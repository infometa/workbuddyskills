#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
PIPELINE = CORE / "scripts" / "run_pipeline.py"
sys.path.insert(0, str(CORE / "scripts"))

from build_spec import assemble_spec  # noqa: E402
from run_pipeline import _compile_backend_fields, _fact_constraints  # noqa: E402


def product(asin: str, brand: str) -> dict:
    return {
        "asin": asin,
        "title": f"{brand} Reusable Drink Chilling Stones",
        "brand": brand,
        "aboutItemFivePoint": [
            "Reusable stones chill drinks without adding water",
            "Smooth storage tray keeps the set organized",
        ],
        "itemSpecifications": {"Material": "Stone"},
        "authorsReviews": [
            {"title": "Useful", "text": "Keeps drinks cool without dilution", "rating": 5},
            {"title": "Needs care", "text": "Rinse and dry after use", "rating": 3},
        ],
    }


class PipelineContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_dir = self.root / "run"
        self.env = dict(os.environ)
        self.env["LISTING_WORKSPACE"] = str(self.root / "workspace")
        self.product_response = self.root / "product-detail-response.json"
        self.product_response.write_text(json.dumps({"products": [
            product("B000000001", "Velmoriq"),
            product("B000000002", "CompetitorCo"),
        ]}), encoding="utf-8")
        self.matrix = self.root / "keyword-matrix.json"
        self.matrix.write_text(json.dumps({"scored_table": [
            {"keyword": "whiskey stones", "source": "SIF", "weekly_search_volume": 1000},
            {"keyword": "home bar gift", "source": "SIF", "weekly_search_volume": 500},
            {"keyword": "no dilution", "source": "SIF", "weekly_search_volume": 300},
            {"keyword": "reusable stone", "source": "SIF", "weekly_search_volume": 200},
        ]}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PIPELINE), *args],
            capture_output=True, text=True, env=self.env,
        )

    def plan(self) -> subprocess.CompletedProcess:
        return self.execute(
            "plan", "--run-dir", str(self.run_dir), "--mode", "benchmark",
            "--target-asin", "B000000001", "--competitor-asin", "B000000002",
            "--marketplace", "US", "--output-language", "en_US",
        )

    def ingest(self) -> subprocess.CompletedProcess:
        return self.execute(
            "ingest", "--run-dir", str(self.run_dir),
            "--product-detail", str(self.product_response),
            "--keyword-matrix", str(self.matrix),
        )

    def test_four_commands_preserve_artifacts_and_contracts(self):
        planned = self.plan()
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(planned.stdout.count("Saved full response:"), 1)
        fetch_plan = json.loads((self.run_dir / "fetch-plan.json").read_text("utf-8"))
        self.assertEqual(fetch_plan["product_detail"]["request_asins"], [
            "B000000001", "B000000002",
        ])

        ingested = self.ingest()
        self.assertEqual(ingested.returncode, 0, ingested.stderr)
        self.assertTrue((self.run_dir / "01-facts" / "product-facts.md").is_file())
        self.assertTrue((self.run_dir / "01-facts" / "product-detail.json").is_file())
        insight_input_path = self.run_dir / "02-insight" / "insight-input.json"
        insight_input = json.loads(insight_input_path.read_text("utf-8"))
        self.assertEqual(insight_input["kind"], "listingInsightInput")
        self.assertEqual(len(insight_input["keyword_candidates"]), 4)
        self.assertEqual(len(insight_input_path.read_text("utf-8").splitlines()), 1)

        insight_bundle = self.root / "insight-bundle.json"
        insight_bundle.write_text(json.dumps({
            "kind": "listingInsightBundle",
            "schema_version": 1,
            "insight_markdown": "# 洞察\n\n- 核心关注：不稀释饮品。",
            "buyer_questions": [{
                "question": "Will the stones dilute a drink?",
                "source": "product_detail_summary",
                "strength": "strong",
                "target_fields": ["bullets"],
            }],
            "keywords": {
                "core": ["whiskey stones"],
                "scene": ["home bar gift"],
                "pain": ["no dilution"],
                "attribute": ["reusable stone"],
                "locked": [], "banned": [],
            },
        }), encoding="utf-8")
        prepared = self.execute(
            "prepare-write", "--run-dir", str(self.run_dir),
            "--insight-bundle", str(insight_bundle),
            "--brands-owned", "Velmoriq", "--brands-competitor", "CompetitorCo",
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        for relative in (
            "02-insight/insight.md", "02-insight/buyer-questions.json",
            "02-insight/keywords.json", "03-write/spec.json", "03-write/writer-input.json",
        ):
            self.assertTrue((self.run_dir / relative).is_file(), relative)
        writer_input_path = self.run_dir / "03-write" / "writer-input.json"
        writer_input = json.loads(writer_input_path.read_text("utf-8"))
        self.assertEqual(writer_input["kind"], "listingWriterInput")
        self.assertEqual(len(writer_input_path.read_text("utf-8").splitlines()), 1)
        self.assertIn("verified_product_facts", writer_input)
        self.assertNotIn("authorsReviews", writer_input["verified_product_facts"])
        self.assertNotIn("product_evidence", writer_input)
        self.assertNotIn("keywords", writer_input)
        self.assertNotIn("buyer_questions", writer_input["insight"])
        self.assertNotIn("spec", writer_input)
        model_spec = writer_input["model_spec"]
        self.assertEqual(model_spec["kind"], "listingWriterModelSpec")
        self.assertEqual(len(model_spec["buyer_questions"]), 1)
        self.assertIn("generation_targets", model_spec)
        self.assertIn("claim_policy", model_spec)
        self.assertIn("required_four_pillars", model_spec)
        self.assertNotIn("keyword_evidence", model_spec)
        self.assertNotIn("discovery_contract", model_spec)
        self.assertNotIn("performance_contract", model_spec)
        self.assertNotIn("search_terms_contract", model_spec)
        full_spec = json.loads(
            (self.run_dir / "03-write" / "spec.json").read_text("utf-8")
        )
        self.assertLess(
            len(json.dumps(model_spec, ensure_ascii=False)),
            len(json.dumps(full_spec, ensure_ascii=False)),
        )
        self.assertIn("at least 60%", writer_input["instruction"])
        self.assertIn("Do not generate search_terms", writer_input["instruction"])
        self.assertNotIn("search_terms", writer_input["draft_contract"])
        self.assertNotIn("subject_matter", writer_input["draft_contract"])
        self.assertEqual(
            writer_input["model_spec"]["backend_fields"]["generated_by"],
            "pipeline_finish",
        )

        draft = {
            "title": "Velmoriq Whiskey Stones for Chilled Drinks",
            "item_highlights": ["Reusable stone set for a tidy home bar"],
            "bullets": [
                "CHILL WITHOUT WATER: Reusable stones cool drinks without adding melting ice",
                "HOME BAR USE: Keep the set ready for relaxed drinks and thoughtful gifting",
                "SIMPLE ROUTINE: Rinse the stones and dry them after each use",
                "ORGANIZED STORAGE: The included tray keeps every piece together",
                "USE WITH CARE: Follow the supplied cleaning guidance before storing",
            ],
            "description": "A reusable chilling stone set for serving drinks at home without melting ice.",
            "search_terms": "this model supplied value must be replaced",
            "subject_matter": ["this model supplied value must be replaced"],
            "structured_attributes": {"material": "Stone"},
            "question_coverage": [{
                "question": "Will the stones dilute a drink?",
                "answered_by": ["bullet_1"], "strength": "explicit",
            }],
            "four_pillars": {
                "what": "pass", "who_scene": "pass",
                "pain_solution": "pass", "trust_boundary": "pass",
            },
        }
        (self.run_dir / "03-write" / "listing-draft.json").write_text(
            json.dumps(draft), encoding="utf-8",
        )
        finished = self.execute(
            "finish", "--run-dir", str(self.run_dir),
        )
        self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)
        self.assertEqual(finished.stdout.count("Saved full response:"), 1)
        self.assertIn("Pipeline total:", finished.stdout)
        compiled_draft = json.loads(
            (self.run_dir / "03-write" / "listing-draft.json").read_text("utf-8")
        )
        self.assertEqual(compiled_draft["search_terms"], "gift no dilution stone")
        self.assertEqual(compiled_draft["subject_matter"], [
            "home bar gift", "no dilution", "reusable stone",
        ])
        for relative in (
            "03-write/check-report.json", "03-write/listing-final.json",
            "03-write/listing-final.md", "03-write/ai-readiness.json",
            "03-write/amazon-detail-preview.json",
        ):
            self.assertTrue((self.run_dir / relative).is_file(), relative)
        manifest = json.loads((self.run_dir / "run-manifest.json").read_text("utf-8"))
        self.assertTrue(all(stage["status"] == "complete" for stage in manifest["stages"]))
        self.assertIn("total_duration_ms", manifest["timing"])
        self.assertEqual(set(manifest["timing"]["steps"]), {
            "evidence_plan", "external_evidence", "evidence_ingest",
            "insight_semantic", "prepare_write", "writer_semantic", "finalize_pipeline",
        })

    def test_ingest_populates_cache_for_next_plan(self):
        self.assertEqual(self.plan().returncode, 0)
        self.assertEqual(self.ingest().returncode, 0)
        second = self.execute(
            "plan", "--run-dir", str(self.root / "second-run"), "--mode", "benchmark",
            "--target-asin", "B000000001", "--competitor-asin", "B000000002",
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        plan = json.loads((self.root / "second-run" / "fetch-plan.json").read_text("utf-8"))
        self.assertEqual(plan["product_detail"]["request_asins"], [])
        self.assertIsNone(plan["keyword_matrix"]["request"])

    def test_plan_can_allocate_run_dir_from_portable_session_root(self):
        result = self.execute(
            "plan", "--mode", "benchmark", "--target-asin", "B000000001",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest_line = next(
            line for line in result.stdout.splitlines()
            if line.startswith("Saved full response: ")
        )
        manifest = Path(manifest_line.split(": ", 1)[1])
        self.assertTrue(manifest.is_file())
        self.assertIn("listing-core/benchmark-B000000001", str(manifest.parent))

    def test_rewrite_audit_handoff_reaches_writer_spec(self):
        handoff = self.root / "audit-handoff.json"
        handoff.write_text(json.dumps({
            "kind": "listingAuditHandoff",
            "schema_version": 1,
            "target": {"asin": "B000000001", "marketplace": "US"},
            "field_actions": [{
                "field": "title", "priority": "high",
                "problem": "weak first screen", "objective": "front-load product identity",
            }],
            "locked_fields": ["description"],
        }), encoding="utf-8")
        planned = self.execute(
            "plan", "--run-dir", str(self.run_dir), "--mode", "rewrite",
            "--target-asin", "B000000001", "--audit-handoff", str(handoff),
        )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(self.ingest().returncode, 0)
        insight_bundle = self.root / "insight-bundle.json"
        insight_bundle.write_text(json.dumps({
            "kind": "listingInsightBundle", "schema_version": 1,
            "insight_markdown": "# 洞察\n\n保留审计约束。",
            "buyer_questions": [{
                "question": "What should the title explain first?",
                "source": "audit_handoff", "strength": "strong",
                "target_fields": ["title"],
            }],
            "keywords": {
                "core": ["whiskey stones"], "scene": [], "pain": [],
                "attribute": [], "locked": [], "banned": [],
            },
        }), encoding="utf-8")
        prepared = self.execute(
            "prepare-write", "--run-dir", str(self.run_dir),
            "--insight-bundle", str(insight_bundle),
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        spec = json.loads((self.run_dir / "03-write" / "spec.json").read_text("utf-8"))
        self.assertEqual(spec["rewrite_contract"]["locked_fields"], ["description"])
        self.assertEqual(spec["rewrite_contract"]["field_actions"][0]["field"], "title")

    def test_keyword_failure_is_explicit_facts_only_downgrade(self):
        self.assertEqual(self.plan().returncode, 0)
        ingested = self.execute(
            "ingest", "--run-dir", str(self.run_dir),
            "--product-detail", str(self.product_response),
            "--keyword-unavailable", "SIF and SellerSprite returned no rows",
        )
        self.assertEqual(ingested.returncode, 0, ingested.stderr)
        insight_input = json.loads(
            (self.run_dir / "02-insight" / "insight-input.json").read_text("utf-8")
        )
        self.assertEqual(insight_input["execution_mode"], "facts_only")
        self.assertEqual(insight_input["keyword_candidates"], [])

        insight_bundle = self.root / "facts-only-insight.json"
        insight_bundle.write_text(json.dumps({
            "kind": "listingInsightBundle", "schema_version": 1,
            "insight_markdown": "# 洞察\n\n关键词市场数据不可用。",
            "buyer_questions": [{
                "question": "Will the stones dilute a drink?",
                "source": "product_detail_summary", "strength": "strong",
                "target_fields": ["bullets"],
            }],
            "keywords": {
                "core": [{
                    "word": "whiskey stones", "source": "inferred", "search_volume": None,
                }],
                "scene": [], "pain": [], "attribute": [], "locked": [], "banned": [],
            },
        }), encoding="utf-8")
        prepared = self.execute(
            "prepare-write", "--run-dir", str(self.run_dir),
            "--insight-bundle", str(insight_bundle),
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        writer_input = json.loads(
            (self.run_dir / "03-write" / "writer-input.json").read_text("utf-8")
        )
        self.assertEqual(writer_input["execution_mode"], "facts_only")
        self.assertEqual(writer_input["model_spec"]["evidence_mode"], "facts_only")
        self.assertNotIn("keywords", writer_input)
        self.assertNotIn("keyword_evidence", writer_input["model_spec"])

    def test_backend_compiler_filters_and_bounds_keyword_evidence(self):
        spec = assemble_spec(
            mode="benchmark",
            brands_owned=["Velmoriq"],
            brands_competitor=["CompetitorCo"],
            keywords={
                "core": ["whiskey stones"],
                "scene": ["home bar gift"],
                "pain": ["no dilution"],
                "attribute": [
                    "CompetitorCo keepsake", "miracle cure", "ultra portable",
                    "bluetooth 5.4 earbuds",
                ],
            },
            category_flags=[],
            banned_terms=["miracle"],
        )
        spec["generation_targets"]["search_terms_bytes_max"] = 18
        draft = {
            "title": "Velmoriq Whiskey Stones",
            "bullets": ["A tidy home bar setup"],
            "search_terms": "model output is ignored",
            "subject_matter": ["model output is ignored"],
        }
        metrics = _compile_backend_fields(draft, spec)
        self.assertEqual(draft["search_terms"], "gift no dilution")
        self.assertLessEqual(len(draft["search_terms"].encode("utf-8")), 18)
        self.assertNotIn("competitorco", json.dumps(draft).casefold())
        self.assertNotIn("miracle", json.dumps(draft).casefold())
        self.assertNotRegex(json.dumps(draft), r"\d")
        self.assertEqual(metrics["search_terms_tokens"], 3)
        self.assertIn("ultra portable", draft["subject_matter"])

    def test_backend_compiler_fails_instead_of_inventing_keywords(self):
        spec = assemble_spec(
            mode="benchmark",
            brands_owned=[],
            brands_competitor=[],
            keywords={"core": ["whiskey stones"]},
            category_flags=[],
        )
        with self.assertRaisesRegex(ValueError, "no safe non-front keyword"):
            _compile_backend_fields({
                "title": "Whiskey Stones",
                "bullets": ["Simple set"],
            }, spec)

    def test_backend_compiler_quarantines_opaque_singletons_and_age_conflicts(self):
        facts = {
            "title": "JoySpark Musical Crawling Crab Baby Toy, 6-18 Months",
            "aboutItemFivePoint": [
                "Soft plush toy for sensory floor play activity",
            ],
        }
        spec = assemble_spec(
            mode="benchmark",
            brands_owned=["JoySpark"],
            brands_competitor=[],
            keywords={
                "core": [{"word": "crawling crab toy", "source": "sif"}],
                "scene": [
                    {"word": "peekimo", "source": "sif"},
                    {"word": "newborn sensory", "source": "sif"},
                    {"word": "floor play activity", "source": "sif"},
                ],
            },
            category_flags=[],
        )
        spec["fact_constraints"] = _fact_constraints(facts)
        draft = {
            "title": "JoySpark Musical Crawling Crab Baby Toy",
            "bullets": ["Interactive movement encourages active play"],
        }

        _compile_backend_fields(draft, spec)

        backend = json.dumps({
            "search_terms": draft["search_terms"],
            "subject_matter": draft["subject_matter"],
        }).casefold()
        self.assertNotIn("peekimo", backend)
        self.assertNotIn("newborn", backend)
        self.assertIn("floor play activity", draft["subject_matter"])


if __name__ == "__main__":
    unittest.main()
