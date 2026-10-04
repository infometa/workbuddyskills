#!/usr/bin/env python3
"""极限词库的内容测试：库本身的分级是否符合政策，以及与受限内容库是否重叠。

扫描器的机制测试在 listing-core/tests/test_restricted_content_scan.py。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SCRIPTS = ROOT.parent / "listing-core" / "scripts"
PRIVATE_DATA = ROOT.parent / "_listing-private-assets" / "data"
sys.path.insert(0, str(CORE_SCRIPTS))

from restricted_content_scan import scan  # noqa: E402

LIBRARY = json.loads((PRIVATE_DATA / "superlative-claims-v1.json").read_text(encoding="utf-8"))
RESTRICTED = json.loads((CORE_SCRIPTS / "restricted-content-v1.json").read_text(encoding="utf-8"))


def severity_of(field, text, category=None):
    hits = scan({field: text}, LIBRARY)
    if category:
        hits = [h for h in hits if h["category"] == category]
    return hits[0]["severity"] if hits else None


def all_terms(library):
    return {t for level in library["profiles"].values() for r in level for t in r["terms"]}


class LibraryShapeTest(unittest.TestCase):
    def test_every_rule_carries_reason_and_replacement(self):
        for level in ("block", "review"):
            for rule in LIBRARY["profiles"][level]:
                self.assertTrue(rule["reason"], rule["category"])
                self.assertTrue(rule["replacement"], rule["category"])
                self.assertTrue(rule["terms"], rule["category"])

    def test_terms_are_lowercase_and_unique_within_the_library(self):
        seen = set()
        for level in ("block", "review"):
            for rule in LIBRARY["profiles"][level]:
                for term in rule["terms"]:
                    self.assertEqual(term, term.lower(), term)
                    self.assertNotIn(term, seen, f"{term} 重复收录")
                    seen.add(term)

    def test_does_not_duplicate_the_restricted_content_library(self):
        """两个库各管一摊：受限品类归 restricted-content，绝对化用语归本库。"""
        overlap = all_terms(LIBRARY) & all_terms(RESTRICTED)
        self.assertEqual(overlap, set(), f"与受限内容库重复收录：{sorted(overlap)}")


class SeverityPolicyTest(unittest.TestCase):
    def test_platform_prohibited_claims_block(self):
        """排名、促销、绝对安全：属实也不许写，一律阻断。"""
        self.assertEqual(severity_of("description", "our best seller"), "block")
        self.assertEqual(severity_of("description", "with free shipping"), "block")
        self.assertEqual(severity_of("description", "100% safe for kids"), "block")

    def test_evidence_backed_claims_only_review(self):
        """有证据即可保留的，判复核而不是阻断。"""
        self.assertEqual(severity_of("description", "lab tested for lead"), "review")
        self.assertEqual(severity_of("description", "lifetime warranty included"), "review")
        self.assertEqual(severity_of("description", "bpa free material"), "review")

    def test_subjective_superlative_escalates_in_title_only(self):
        """亚马逊对标题的主观宣称限制严于正文。"""
        self.assertEqual(severity_of("title", "Ultimate Whiskey Set"), "block")
        self.assertEqual(severity_of("description", "the ultimate whiskey set"), "review")

    def test_longest_claim_wins_over_its_prefix(self):
        """'best seller' 命中时不再另报一条 'best'。"""
        hits = scan({"description": "our best seller"}, LIBRARY)
        self.assertEqual([h["term"] for h in hits], ["best seller"])


class FalsePositiveGuardTest(unittest.TestCase):
    def test_clean_factual_copy_produces_no_hits(self):
        listing = {
            "title": "Soapstone Whiskey Chilling Cubes, Set of 9 with Storage Pouch",
            "bullets": ["Machine-cut from 20mm soapstone, 18g each.",
                        "Chills a 60ml pour by 8°C after 5 minutes in the freezer.",
                        "Dishwasher safe; rinse and refreeze between uses."],
            "search_terms": "soapstone chilling cubes reusable whiskey",
        }
        self.assertEqual(scan(listing, LIBRARY), [])

    def test_substrings_of_ordinary_words_do_not_match(self):
        self.assertIsNone(severity_of("description", "Bestow this on a friend"))
        self.assertIsNone(severity_of("description", "An organically shaped handle"))


class ChipExampleTest(unittest.TestCase):
    """chip comply:banned 的 guidedExample 在建库前零命中，这里锁死它必须被抓到。"""

    LISTING = {
        "title": "Velmoriq Best Whiskey Stones, 100% Safe Soapstone Ice Cubes",
        "bullets": ["PERFECT CHILL - Instantly keeps every drink cold for hours.",
                    "ODORLESS & FOOD GRADE - Completely safe with zero taste transfer.",
                    "GUARANTEED RESULTS - The ultimate gift every whiskey lover will love."],
    }

    def test_every_planted_claim_is_flagged(self):
        found = {h["term"].lower() for h in scan(self.LISTING, LIBRARY)}
        for expected in ("best", "100% safe", "perfect", "completely safe",
                         "guaranteed", "ultimate", "food grade", "odorless"):
            self.assertIn(expected, found, f"漏检 {expected}")

    def test_absolute_safety_claims_block(self):
        blocked = {h["term"].lower() for h in scan(self.LISTING, LIBRARY)
                   if h["severity"] == "block"}
        self.assertIn("100% safe", blocked)
        self.assertIn("completely safe", blocked)


if __name__ == "__main__":
    unittest.main()
