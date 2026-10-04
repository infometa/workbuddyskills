#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from score_quality import DIMENSIONS, score_quality  # noqa: E402


def complete_dimensions():
    return {
        key: {"evidence": [f"evidence:{key}"], "deductions": []}
        for key, _name, _weight in DIMENSIONS
    }


def compliance_report():
    """机检产物占位：合规分只有在存在这类产物时才允许按 20% 权重计入 overall。"""
    return {"source": "listing-compliance-scan", "riskTerms": [], "violations": []}


def check_report():
    return {
        "kind": "listingCheckReport",
        "schema_version": 1,
        "fields": {
            field: {"status": "pass", "issues": []}
            for field in ("title", "bullets", "description", "search_terms", "item_highlights")
        },
    }


class ScoreQualityTest(unittest.TestCase):
    def test_perfect_score_and_ai_readiness(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "compliance_report": compliance_report(),
        })
        self.assertEqual(result["scorePanel"]["overall"], 100)
        self.assertEqual(result["scorePanel"]["grade"], "A")
        self.assertTrue(result["pass"])
        self.assertEqual(result["aiReadiness"]["discoverability"], "pass")
        self.assertEqual(result["aiReadiness"]["answerability"], "pass")
        self.assertEqual(result["aiReadiness"]["recommendation_readiness"], "pass")
        self.assertFalse(result["aiReadiness"]["external_probe"]["probed"])

    def test_deductions_and_na_are_deterministic(self):
        dimensions = complete_dimensions()
        dimensions["localization"] = {"state": "na"}
        dimensions["ai_answerability"]["deductions"] = [{"points": 25, "reason": "questions missing"}]
        result = score_quality({"dimensions": dimensions})
        answer = next(
            item for item in result["scorePanel"]["items"] if item["key"] == "ai_answerability"
        )
        self.assertEqual(answer["score"], 75)
        self.assertEqual(answer["state"], "warn")
        self.assertTrue(result["scorePanel"]["insufficientData"])
        self.assertEqual(result["aiReadiness"]["answerability"], "weak")
        self.assertEqual(result["aiReadiness"]["recommendation_readiness"], "weak")

    def test_hard_gate_caps_and_blocks_pass(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "hard_gates": [{
                "key": "competitor_brand_trademark",
                "triggered": True,
                "evidence": ["BrandX in title"],
            }],
        })
        self.assertEqual(result["scorePanel"]["overall"], 59)
        self.assertFalse(result["pass"])
        self.assertTrue(result["requiresHumanReview"])
        self.assertEqual(result["aiReadiness"]["recommendation_readiness"], "miss")

    def test_dimension_cap_is_applied(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "dimension_caps": {"title_first_screen": 59},
        })
        title = next(
            item for item in result["scorePanel"]["items"] if item["key"] == "title_first_screen"
        )
        self.assertEqual(title["score"], 59)

    def test_unknown_gate_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown hard gate"):
            score_quality({
                "dimensions": complete_dimensions(),
                "hard_gates": [{"key": "invented_gate", "triggered": True}],
            })

    def test_missing_compliance_and_facts_auto_cap_and_block_pass(self):
        dimensions = complete_dimensions()
        dimensions["compliance_risk"] = {"state": "na"}
        dimensions["fact_trust"] = {"state": "na"}
        result = score_quality({"dimensions": dimensions})
        self.assertEqual(result["scorePanel"]["overall"], 79)
        self.assertFalse(result["pass"])
        failed_keys = {
            gate["key"] for gate in result["scorePanel"]["hardGates"]
            if gate["status"] == "fail"
        }
        self.assertEqual(
            failed_keys, {"compliance_unavailable", "product_facts_unavailable"}
        )

    def test_unknown_dimension_rejected(self):
        dimensions = complete_dimensions()
        dimensions["ai_friendliness"] = {"deductions": []}
        with self.assertRaisesRegex(ValueError, "unknown dimensions"):
            score_quality({"dimensions": dimensions})



class ComplianceProvenanceTest(unittest.TestCase):
    """机检没跑时，合规分不允许按 20% 权重进 overall。"""

    def test_unverified_compliance_triggers_gate_and_cap(self):
        result = score_quality({"dimensions": complete_dimensions()})
        panel = result["scorePanel"]
        compliance = next(item for item in panel["items"] if item["key"] == "compliance_risk")
        self.assertEqual(compliance["score"], 79)
        self.assertIn("合规待终检", compliance["note"])
        gate = next(g for g in panel["hardGates"] if g["key"] == "compliance_unavailable")
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(panel["overall"], 79)
        self.assertFalse(result["pass"])

    def test_check_report_alone_counts_as_compliance_evidence(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "check_report": check_report(),
        })
        panel = result["scorePanel"]
        self.assertEqual(panel["overall"], 100)
        self.assertNotIn(
            "compliance_unavailable", {gate["key"] for gate in panel["hardGates"]}
        )

    def test_malformed_or_partial_report_does_not_count_as_compliance_evidence(self):
        for report in (
            {"foo": "bar"},
            {"kind": "listingCheckReport", "schema_version": 1, "fields": {}},
            {"fields": {"title": {"status": "pass", "issues": []}}},
        ):
            with self.subTest(report=report):
                result = score_quality({
                    "dimensions": complete_dimensions(),
                    "check_report": report,
                })
                self.assertEqual(result["scorePanel"]["overall"], 79)
                self.assertFalse(result["pass"])
                self.assertIn(
                    "compliance_unavailable",
                    {gate["key"] for gate in result["scorePanel"]["hardGates"]},
                )

    def test_evaluator_cannot_self_declare_compliance_evidence(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "data_confidence": {"overall": "verified", "compliance": "verified"},
        })
        panel = result["scorePanel"]
        self.assertEqual(panel["overall"], 79)
        self.assertIn(
            "compliance_unavailable", {gate["key"] for gate in panel["hardGates"]}
        )

    def test_check_report_merge_accepts_list_evidence_in_existing_deduction(self):
        dimensions = complete_dimensions()
        dimensions["semantic_discoverability"]["deductions"] = [{
            "points": 1,
            "reason": "现有语义扣分",
            "evidence": ["keyword coverage", {"field": "title"}],
        }]
        report = check_report()
        report["coverage"] = {"bullets_scene_pain_pct": 0}

        result = score_quality({
            "dimensions": dimensions,
            "check_report": report,
        })

        semantic = next(
            item for item in result["scorePanel"]["items"]
            if item["key"] == "semantic_discoverability"
        )
        self.assertEqual(semantic["score"], 93)


if __name__ == "__main__":
    unittest.main()
