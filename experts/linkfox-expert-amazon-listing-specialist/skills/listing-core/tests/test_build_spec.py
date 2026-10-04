#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT / "scripts"))
from build_spec import assemble_spec  # noqa: E402

KW = {"core": ["drawer organizer"], "scene": ["kitchen"], "pain": ["messy drawer"]}

class TestBuildSpec(unittest.TestCase):
    def test_defaults_and_shape(self):
        s = assemble_spec("benchmark", ["Rocktone"], ["BrandX"], KW, [])
        self.assertEqual(s["kind"], "listingWritingSpec")
        self.assertEqual(s["limits"]["title_max"], 75)          # listing_spec DEFAULTS
        self.assertEqual(s["limits"]["search_terms_bytes_max"], 250)
        self.assertEqual(s["generation_targets"]["title_max"], 70)
        self.assertEqual(s["generation_targets"]["item_highlights_max"], 115)
        self.assertEqual(s["generation_targets"]["bullet_each_max"], 190)
        self.assertEqual(s["limits"]["bullet_each_max"], 255)
        self.assertEqual(s["limits"]["bullet_total_max"], 1275)
        self.assertEqual(s["authoring_recommendations"]["bullet_each_max"], 200)
        self.assertEqual(s["generation_targets"]["description_max"], 950)
        self.assertEqual(s["generation_targets"]["search_terms_bytes_max"], 230)
        self.assertEqual(s["writer_contract_version"], 2)
        self.assertEqual(
            s["search_terms_contract"]["reserved_front_tokens"],
            ["drawer", "organizer", "kitchen", "messy"],
        )
        self.assertIn("护理方式", s["claim_policy"]["forbidden_without_explicit_fact"])
        self.assertEqual(s["keywords"]["core_to_title"], ["drawer organizer"])
        self.assertEqual(len(s["bullet_plan"]), 5)
        self.assertIn("最强卖点", s["bullet_plan"][0])
        self.assertIn("质保", s["bullet_plan"][4])
        self.assertEqual(s["marketplace"], "US")
        self.assertEqual(s["output_language"], "en_US")
        self.assertEqual(s["profile"], "standard")
        self.assertTrue(s["performance_contract"]["provided_evidence_only"])
        self.assertEqual(s["performance_contract"]["detailed_reviews_source"], "user_or_host_provided")
        self.assertEqual(s["performance_contract"]["keyword_top_n"], 50)
        self.assertEqual(
            s["discovery_contract"]["shopping_assistant"]["four_pillars"],
            ["what", "who_scene", "pain_solution", "trust_boundary"],
        )

    def test_brand_overlap_raises(self):
        with self.assertRaises(ValueError):
            assemble_spec("create", ["Rocktone"], ["rocktone"], KW, [])

    def test_category_flags_shape_bullets(self):
        s = assemble_spec("create", [], [], KW, ["diy", "dimension"])
        self.assertTrue(any("使用方法" in b or "操作步骤" in b for b in s["bullet_plan"]))
        self.assertTrue(any("使用收益" in b for b in s["bullet_plan"]))

    def test_attribute_dimension_and_buyer_questions(self):
        kw = dict(KW)
        kw["attribute"] = ["BPA-free", "19oz"]
        s = assemble_spec(
            "create", [], [], kw, [],
            buyer_questions=["can I put it in backpack?"],
        )
        self.assertEqual(s["keywords"]["attribute_to_highlights"], ["BPA-free", "19oz"])
        self.assertEqual(s["buyer_questions"], ["can I put it in backpack?"])
        # 未提供时保持空列表而非缺键（下游按键读取）
        s2 = assemble_spec("create", [], [], KW, [])
        self.assertEqual(s2["keywords"]["attribute_to_highlights"], [])
        self.assertEqual(s2["buyer_questions"], [])

    def test_bullet_plan_four_questions_mapping(self):
        s = assemble_spec("benchmark", [], [], KW, [])
        self.assertIn("边界", s["bullet_plan"][4])
        self.assertIn("场景", s["bullet_plan"][1])
        self.assertIn("痛点", s["bullet_plan"][2])
        self.assertIn("前50字符", s["style"]["title_formula"])

    def test_user_spec_overrides_layer_b(self):
        s = assemble_spec("benchmark", [], [], KW, [], user_spec={"title": {"max": 150}})
        self.assertEqual(s["limits"]["title_max"], 150)
        self.assertEqual(s["generation_targets"]["title_max"], 145)

    def test_user_bullet_spec_overrides_default_recommendation(self):
        s = assemble_spec(
            "benchmark", [], [], KW, [],
            user_spec={"bullets": {"each_max": 400}},
        )
        self.assertEqual(s["limits"]["bullet_each_max"], 400)
        self.assertEqual(s["generation_targets"]["bullet_each_max"], 390)
        self.assertEqual(s["authoring_recommendations"]["bullet_each_max"], 400)

    def test_marketplace_derives_locale_and_keeps_product_context(self):
        s = assemble_spec(
            "create", [], [], KW, [], marketplace="DE", category="Home", product_type="Bottle"
        )
        self.assertEqual(s["output_language"], "de_DE")
        self.assertEqual(s["style"]["locale"], "de_DE")
        self.assertEqual(s["category"], "Home")
        self.assertEqual(s["product_type"], "Bottle")

    def test_legacy_fast_profile_resolves_to_standard_and_ui_keyword_objects(self):
        # fast 档已 deprecate：旧调用方传 fast 也必须按 standard 展开
        keywords = {
            "core": [{"word": "dog water bottle", "source": "sif", "search_volume": 1200}],
            "scene": [{"keyword": "hiking with dog", "source": "sif"}],
            "pain": [],
            "attribute": [],
        }
        s = assemble_spec("create", [], [], keywords, [], profile="fast")
        self.assertEqual(s["keywords"]["core_to_title"], ["dog water bottle"])
        self.assertEqual(s["keyword_evidence"][0]["volume"], 1200)
        self.assertEqual(s["profile"], "standard")
        self.assertEqual(s["performance_contract"]["keyword_top_n"], 50)
        self.assertEqual(s["performance_contract"]["max_semantic_calls"], 2)
        self.assertEqual(s["performance_contract"]["detailed_reviews_source"], "user_or_host_provided")

    def test_rewrite_handoff_is_normalized(self):
        handoff = {
            "kind": "listingAuditHandoff",
            "schema_version": 1,
            "target": {"asin": "B012345678", "marketplace": "US"},
            "field_actions": [{
                "field": "title",
                "priority": "high",
                "problem": "weak first screen",
                "objective": "front-load product identity",
            }],
            "locked_fields": ["description"],
        }
        s = assemble_spec("rewrite", [], [], KW, [], rewrite_handoff=handoff)
        self.assertEqual(s["rewrite_contract"]["field_actions"][0]["field"], "title")
        self.assertEqual(s["rewrite_contract"]["locked_fields"], ["description"])
        self.assertTrue(s["performance_contract"]["reuse_audit_evidence"])

    def test_rewrite_handoff_with_s3_bundle_reduces_semantic_budget(self):
        handoff = {
            "kind": "listingAuditHandoff", "schema_version": 1,
            "target": {"asin": "B012345678", "marketplace": "US"},
            "evidence_paths": {
                "keywords": "/abs/keywords.json",
                "buyer_questions": "/abs/buyer-questions.json",
                "insight": "/abs/insight.md",
            },
            "field_actions": [], "locked_fields": [],
        }
        spec = assemble_spec("rewrite", [], [], KW, [], rewrite_handoff=handoff)
        self.assertTrue(spec["performance_contract"]["reuse_audit_insight"])
        self.assertEqual(spec["performance_contract"]["max_semantic_calls"], 1)

    def test_rewrite_accepts_full_audit_report_without_manual_extraction(self):
        report = {
            "kind": "listingAuditReport",
            "schema_version": 2,
            "auditHandoff": {
                "kind": "listingAuditHandoff",
                "schema_version": 1,
                "field_actions": [{"field": "title"}],
                "locked_fields": ["description"],
            },
        }
        spec = assemble_spec("rewrite", [], [], KW, [], rewrite_handoff=report)
        self.assertEqual(spec["rewrite_contract"]["field_actions"][0]["field"], "title")
        self.assertEqual(spec["rewrite_contract"]["locked_fields"], ["description"])

    def test_rewrite_handoff_rejects_conflicts_and_wrong_mode(self):
        handoff = {
            "kind": "listingAuditHandoff",
            "schema_version": 1,
            "field_actions": [{"field": "title"}],
            "locked_fields": ["title"],
        }
        with self.assertRaisesRegex(ValueError, "both locked and targeted"):
            assemble_spec("rewrite", [], [], KW, [], rewrite_handoff=handoff)
        with self.assertRaisesRegex(ValueError, "only valid"):
            assemble_spec("create", [], [], KW, [], rewrite_handoff={**handoff, "locked_fields": []})

    def test_facts_only_disables_external_evidence_contract(self):
        spec = assemble_spec(
            "rewrite", ["Velmoriq"], [], {}, [], evidence_mode="facts_only"
        )
        self.assertEqual(spec["evidence_mode"], "facts_only")
        self.assertFalse(spec["keywords"]["integrity"])
        self.assertTrue(spec["performance_contract"]["provided_evidence_only"])
        self.assertTrue(spec["performance_contract"]["keyword_evidence_optional"])

    def test_locked_and_banned_from_keyword_plan_reach_the_spec(self):
        """词表工作台的 locked/banned 必须进入写作契约。"""
        kw = {**KW, "locked": ["whiskey stones"], "banned": ["leakproof", "WIRELESS"]}
        spec = assemble_spec(
            "create", [], [], kw, [], banned_terms=["wireless", "EGG"]
        )
        self.assertEqual(spec["keywords"]["locked"], ["whiskey stones"])
        self.assertEqual(spec["user_banned_terms"], ["wireless", "EGG", "leakproof"])

    def test_user_banned_terms_defaults_to_empty(self):
        spec = assemble_spec("create", [], [], KW, [])
        self.assertEqual(spec["user_banned_terms"], [])
        self.assertEqual(spec["keywords"]["locked"], [])

if __name__ == "__main__":
    unittest.main()
