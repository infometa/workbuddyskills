#!/usr/bin/env python3
"""三库合并与 complianceReport 载荷的契约测试。

单个词库的内容判断在 test_superlative_claims_library.py / test_brand_conflict_scan.py。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import save_compliance_output as sco  # noqa: E402

# output-schema.md 传输层：文件名必须匹配 linkfox-<slug>-<数字>.json
ARTIFACT_NAME_RE = re.compile(r"^linkfox-[a-z0-9-]+-\d+\.json$")

CLEAN = {
    "title": "Soapstone Whiskey Chilling Cubes, Set of 9",
    "bullets": ["Machine-cut from 20mm soapstone, 18g each."],
}
REVIEW_ONLY = {"description": "bpa free material, lab tested for lead"}
DUPLICATE_SPAN = {"description": "bpa free liner"}  # 同时命中品牌库与环保宣称库
BLOCKING = {"description": "our best seller with free shipping"}


def report_for(listing: dict, **overrides):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "listing.json"
        path.write_text(json.dumps(listing), encoding="utf-8")
        args = argparse.Namespace(listing=path, own_brand=[], skip=[], asin=None,
                                  site=None, core_scripts=None)
        for key, value in overrides.items():
            setattr(args, key, value)
        return sco.build_report(args)


class VerdictTest(unittest.TestCase):
    def test_clean_listing_passes(self):
        report = report_for(CLEAN)
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["hits"], [])
        self.assertFalse(report["summary"]["degraded"])

    def test_any_block_hit_makes_the_verdict_block(self):
        self.assertEqual(report_for(BLOCKING)["verdict"], "block")

    def test_review_only_listing_reviews(self):
        report = report_for(REVIEW_ONLY)
        self.assertEqual(report["verdict"], "review")
        self.assertEqual(report["summary"]["block_count"], 0)

    def test_a_failed_library_can_never_report_pass(self):
        """词库跑不起来时说「通过」等于谎报安全，必须降级为复核。"""
        report = report_for(CLEAN, core_scripts=Path("/nonexistent"))
        self.assertEqual(report["verdict"], "review")
        self.assertTrue(report["summary"]["degraded"])
        self.assertIn("不完整", report["summary"]["note"])

    def test_failed_library_is_recorded_not_dropped(self):
        report = report_for(CLEAN, core_scripts=Path("/nonexistent"))
        failed = [lib for lib in report["libraries"] if lib["status"] == "failed"]
        self.assertEqual({lib["key"] for lib in failed}, {"restricted", "claims"})
        self.assertTrue(all(lib["error"] for lib in failed))


class PayloadShapeTest(unittest.TestCase):
    def test_every_library_is_accounted_for(self):
        libraries = report_for(CLEAN)["libraries"]
        self.assertEqual({lib["key"] for lib in libraries},
                         {"restricted", "claims", "claims_zh", "brand"})
        executed = [lib for lib in libraries if lib["status"] == "ok"]
        self.assertEqual({lib["key"] for lib in executed}, {"restricted", "claims", "brand"})
        self.assertTrue(all(lib["version"] for lib in executed))

    def test_every_hit_names_the_library_that_produced_it(self):
        for hit in report_for(BLOCKING)["hits"]:
            self.assertTrue(hit["library"])

    def test_hits_carry_the_full_rendering_contract(self):
        hit = report_for(BLOCKING)["hits"][0]
        for key in ("field", "severity", "category", "term", "offset", "reason",
                    "replacement", "library"):
            self.assertIn(key, hit)

    def test_hits_are_sorted_block_first_then_by_field_order(self):
        report = report_for({
            "description": "lab tested",
            "title": "Best Kettle",
        })
        severities = [h["severity"] for h in report["hits"]]
        self.assertEqual(severities, sorted(severities, key=lambda s: s != "block"))
        self.assertEqual(report["hits"][0]["field"], "title")

    def test_scanned_fields_lists_only_fields_with_content(self):
        report = report_for({"title": "Best Kettle", "description": ""})
        self.assertEqual(report["summary"]["scanned_fields"], ["title"])

    def test_own_brand_is_forwarded_to_the_brand_scanner(self):
        listing = {"description": "Made by Yeti in Ohio."}
        with_own = report_for(listing, own_brand=["Yeti"])
        without = report_for(listing)
        self.assertLess(len(with_own["hits"]), len(without["hits"]))


class ChineseLibraryGatingTest(unittest.TestCase):
    """中文库只在文案真有中文时才跑，纯英文 listing 上它没有可检内容。"""

    def test_english_only_listing_marks_the_chinese_library_not_applicable(self):
        libraries = report_for(CLEAN)["libraries"]
        zh = next(lib for lib in libraries if lib["key"] == "claims_zh")
        self.assertEqual(zh["status"], "not_applicable")
        self.assertIn("未出现中文", zh["reason"])

    def test_not_applicable_does_not_count_as_degraded(self):
        """「没有可检内容」不是「没跑起来」，不能把 verdict 从 pass 拖到 review。"""
        report = report_for(CLEAN)
        self.assertFalse(report["summary"]["degraded"])
        self.assertEqual(report["verdict"], "pass")

    def test_chinese_copy_runs_the_chinese_library(self):
        report = report_for({"title": "全网最低价 限时抢购"})
        zh = next(lib for lib in report["libraries"] if lib["key"] == "claims_zh")
        self.assertEqual(zh["status"], "ok")
        self.assertEqual(report["verdict"], "block")
        self.assertTrue(any(h["library"] == "superlative-claims-zh-v1" for h in report["hits"]))

    def test_chinese_detection_looks_at_every_field(self):
        report = report_for({"title": "Titanium Mug", "bullets": ["国家级工艺"]})
        zh = next(lib for lib in report["libraries"] if lib["key"] == "claims_zh")
        self.assertEqual(zh["status"], "ok")

    def test_mixed_draft_gets_hits_from_both_claim_libraries(self):
        report = report_for({"description": "全网最低价的 best seller"})
        libs = {hit["library"] for hit in report["hits"]}
        self.assertIn("superlative-claims-zh-v1", libs)
        self.assertIn("superlative-claims-v1", libs)


class DeduplicationTest(unittest.TestCase):
    def test_same_span_flagged_by_two_libraries_becomes_one_hit(self):
        hits = [h for h in report_for(DUPLICATE_SPAN)["hits"]
                if h["term"].casefold() == "bpa free"]
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0].get("also_flagged_by"))

    def test_merged_hit_keeps_the_stricter_severity(self):
        hits = [h for h in report_for({"search_terms": "bpa free liner"})["hits"]
                if h["term"].casefold() == "bpa free"]
        # 后台字段里品牌库判阻断，环保库判复核，合并后必须是阻断
        self.assertEqual(hits[0]["severity"], "block")


class ArtifactTransportTest(unittest.TestCase):
    def test_slug_matches_the_bridge_filename_contract(self):
        self.assertTrue(ARTIFACT_NAME_RE.match(f"{sco.SLUG}-20260828120000.json"))

    def test_cli_prints_the_saved_full_response_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "listing.json"
            listing.write_text(json.dumps(CLEAN), encoding="utf-8")
            out = Path(tmp) / f"{sco.SLUG}-20260828120000.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "save_compliance_output.py"),
                 "--listing", str(listing), "--out", str(out)],
                capture_output=True, text=True, check=True)
            self.assertRegex(proc.stdout, r"^Saved full response: .+ \(\d+ bytes\)$")
            self.assertEqual(json.loads(out.read_text())["type"], "complianceReport")


if __name__ == "__main__":
    unittest.main()
