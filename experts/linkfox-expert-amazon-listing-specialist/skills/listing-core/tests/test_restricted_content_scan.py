#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from restricted_content_scan import DEFAULT_LIBRARY, drop_contained, find_spans, scan  # noqa: E402


def library(*rules, level="block"):
    """Minimal in-memory library so scanner tests don't depend on shipped term lists."""
    other = "review" if level == "block" else "block"
    return {"version": "test", "profiles": {level: list(rules), other: []}}


def rule(category, terms, **extra):
    return {"category": category, "terms": terms,
            "reason": f"reason:{category}", "replacement": f"fix:{category}", **extra}


class FindSpansTest(unittest.TestCase):
    def test_matches_whole_words_only(self):
        self.assertEqual(find_spans("Secure lid", "cure"), [])
        self.assertEqual(find_spans("Will cure it", "cure"), [(5, 9)])

    def test_reports_every_occurrence(self):
        self.assertEqual(len(find_spans("best of the best", "best")), 2)

    def test_detects_separated_obfuscation(self):
        self.assertTrue(find_spans("c-u-r-e your skin", "cure"))
        self.assertFalse(find_spans("obscure", "cure"))

    def test_multi_word_terms_skip_the_obfuscation_branch(self):
        """短语本身含空格，不能再套「逐字符拆开」的规则，否则会把整句吞掉。"""
        self.assertEqual(find_spans("bestseller", "best seller"), [])


class DropContainedTest(unittest.TestCase):
    def test_longest_term_at_a_position_wins(self):
        hits = [{"offset": 0, "length": 4, "term": "best"},
                {"offset": 0, "length": 11, "term": "best seller"}]
        self.assertEqual([h["term"] for h in drop_contained(hits)], ["best seller"])

    def test_non_overlapping_hits_all_survive(self):
        hits = [{"offset": 0, "length": 2, "term": "#1"},
                {"offset": 3, "length": 11, "term": "best seller"}]
        self.assertEqual(len(drop_contained(hits)), 2)


class ScanTest(unittest.TestCase):
    def test_hit_carries_field_offset_and_source_text(self):
        hits = scan({"title": "The Best Kettle"}, library(rule("sup", ["best"])))
        self.assertEqual(
            [(h["field"], h["term"], h["offset"], h["severity"]) for h in hits],
            [("title", "Best", 4, "block")])

    def test_escalate_in_promotes_review_to_block_for_named_fields(self):
        lib = library(rule("sup", ["best"], escalate_in=["title"]), level="review")
        self.assertEqual(scan({"title": "Best Kettle"}, lib)[0]["severity"], "block")
        self.assertEqual(scan({"description": "Best kettle"}, lib)[0]["severity"], "review")

    def test_escalate_in_never_downgrades_a_block_rule(self):
        lib = library(rule("banned", ["weed"], escalate_in=["title"]))
        self.assertEqual(scan({"description": "weed bag"}, lib)[0]["severity"], "block")

    def test_bullet_lists_are_scanned(self):
        hits = scan({"bullets": ["clean", "Best value"]}, library(rule("sup", ["best"])))
        self.assertEqual(len(hits), 1)


class ShippedLibrariesTest(unittest.TestCase):
    def test_default_library_still_loads_and_flags_a_known_term(self):
        lib = json.loads(DEFAULT_LIBRARY.read_text(encoding="utf-8"))
        hits = scan({"title": "CBD gummies"}, lib)
        self.assertEqual(hits[0]["severity"], "block")

    def test_default_library_is_quiet_on_clean_copy(self):
        lib = json.loads(DEFAULT_LIBRARY.read_text(encoding="utf-8"))
        self.assertEqual(scan({"title": "Soapstone Chilling Cubes, Set of 9"}, lib), [])


if __name__ == "__main__":
    unittest.main()
