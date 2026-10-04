#!/usr/bin/env python3
"""Listing 输入映射契约的回归用例。

真实事故：B00S93EQUK 的线上标题 186 字符，评估者按 `|` 切成 Title 74c +
Item Highlights 109c，`title>75c → 标题维度 cap 59` 的门禁因此没触发，
该维度拿了 92 分、总分 86/B+/pass=true。这些用例锁死那条路径。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_listing_input import normalize  # noqa: E402
from score_quality import DIMENSIONS, score_quality  # noqa: E402

LIVE_TITLE = (
    "Alpha Grillers Instant Read Meat Thermometer Digital, Cooking, Food, Grill | "
    "1-2 Second Ultra-Fast Response Time, Bright Backlit Display, Waterproof (IP67), "
    "Pre-Calibrated & Ready to Use"
)


def product_detail(**overrides):
    product = {
        "asin": "B00S93EQUK",
        "title": LIVE_TITLE,
        "aboutItemFivePoint": ["bullet one", "bullet two"],
        "productDescription": [{"position": 1, "text": "A+ 段落"}, {"position": 2, "image": "https://x/y.jpg"}],
    }
    product.update(overrides)
    return {"errcode": 200, "products": [product]}


def complete_dimensions():
    return {
        key: {"evidence": [f"evidence:{key}"], "deductions": []}
        for key, _name, _weight in DIMENSIONS
    }


class NormalizeListingInputTest(unittest.TestCase):
    def test_title_is_verbatim_and_never_split(self):
        result = normalize(product_detail())
        self.assertEqual(result["listing"]["title"], LIVE_TITLE)
        self.assertEqual(result["field_metrics"]["title_chars"], len(LIVE_TITLE))
        self.assertTrue(result["field_metrics"]["title_over_limit"])
        self.assertEqual(result["field_provenance"]["title"]["source_field"], "products[0].title")

    def test_item_highlights_unavailable_when_source_has_no_such_field(self):
        result = normalize(product_detail())
        self.assertIsNone(result["listing"]["item_highlights"])
        highlights = result["field_provenance"]["item_highlights"]
        self.assertEqual(highlights["state"], "unavailable")
        self.assertIsNone(highlights["source_field"])
        self.assertIn("禁止从标题中拆分", highlights["reason"])

    def test_real_highlights_field_is_accepted(self):
        result = normalize(product_detail(itemHighlights=["Waterproof IP67", "1-2s response"]))
        self.assertEqual(result["listing"]["item_highlights"], ["Waterproof IP67", "1-2s response"])
        self.assertEqual(result["field_provenance"]["item_highlights"]["state"], "verified")

    def test_verified_highlights_may_legitimately_repeat_title_text(self):
        tail = "1-2 Second Ultra-Fast Response Time, Bright Backlit Display, Waterproof (IP67), Pre-Calibrated & Ready to Use"
        result = normalize(product_detail(itemHighlights=[tail]))
        self.assertEqual(result["listing"]["item_highlights"], [tail])
        self.assertEqual(result["field_provenance"]["item_highlights"]["state"], "verified")

    def test_selected_asin_records_the_real_product_index(self):
        payload = product_detail()
        payload["products"].insert(0, {"asin": "B000000000", "title": "Other product"})
        result = normalize(payload, asin="B00S93EQUK")
        self.assertEqual(result["field_provenance"]["title"]["source_field"], "products[1].title")

    def test_bullets_and_description_come_from_the_real_source_fields(self):
        # 日志里第一次提取 bulletPoints / description 全 NOT_FOUND，实际字段是
        # aboutItemFivePoint / productDescription —— 映射固化在脚本里，不靠试错
        result = normalize(product_detail())
        self.assertEqual(result["listing"]["bullets"], ["bullet one", "bullet two"])
        self.assertEqual(result["field_provenance"]["bullets"]["source_field"], "products[0].aboutItemFivePoint")
        self.assertEqual(result["listing"]["description"], "A+ 段落")

    def test_search_terms_are_never_inferred_from_the_front_end(self):
        result = normalize(product_detail())
        self.assertIsNone(result["listing"]["search_terms"])
        self.assertEqual(result["field_provenance"]["search_terms"]["state"], "unavailable")


class ScoreQualityListingContractTest(unittest.TestCase):
    def test_over_limit_title_caps_the_dimension_and_blocks_pass(self):
        normalized = normalize(product_detail())
        result = score_quality({
            "dimensions": complete_dimensions(),
            "compliance_report": {"source": "listing-compliance-scan", "riskTerms": []},
            "listing": normalized["listing"],
            "field_provenance": normalized["field_provenance"],
            "field_metrics": normalized["field_metrics"],
        })
        panel = result["scorePanel"]
        title_item = next(item for item in panel["items"] if item["key"] == "title_first_screen")
        self.assertEqual(title_item["score"], 59)
        gate_keys = {gate["key"] for gate in panel["hardGates"]}
        self.assertIn("title_without_highlights", gate_keys)
        self.assertLessEqual(panel["overall"], 79)
        self.assertFalse(result["pass"])

    def test_score_quality_rejects_unverified_item_highlights(self):
        with self.assertRaises(ValueError):
            score_quality({
                "dimensions": complete_dimensions(),
                "listing": {
                    "title": "Alpha Grillers Instant Read Meat Thermometer Digital, Cooking, Food, Grill",
                    "item_highlights": ["1-2 Second Ultra-Fast Response Time"],
                },
                "field_provenance": {"item_highlights": {"source_field": None, "state": "unavailable"}},
            })

    def test_metrics_are_recomputed_when_the_caller_omits_them(self):
        result = score_quality({
            "dimensions": complete_dimensions(),
            "compliance_report": {"source": "listing-compliance-scan", "riskTerms": []},
            "listing": {"title": LIVE_TITLE, "item_highlights": None, "bullets": []},
        })
        panel = result["scorePanel"]
        self.assertEqual(panel["fieldMetrics"]["title_chars"], len(LIVE_TITLE))
        title_item = next(item for item in panel["items"] if item["key"] == "title_first_screen")
        self.assertEqual(title_item["score"], 59)


if __name__ == "__main__":
    unittest.main()
