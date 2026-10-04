#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from brand_conflict_scan import scan  # noqa: E402
from lexicon_hash import compact_digest, digest, tokenize  # noqa: E402


def lexicon_of(*phrases):
    """Build an in-memory lexicon so tests never depend on the shipped export."""
    return {digest(tokenize(p)) for p in phrases}


def compacts_of(*phrases):
    return {compact_digest(tokenize(p)) for p in phrases if compact_digest(tokenize(p))}


def severities(hits):
    return {(h["field"], h["term"]): h["severity"] for h in hits}


class BrandConflictScanTest(unittest.TestCase):
    def test_uppercase_blocks_lowercase_reviews(self):
        """产品决策：大写命中→阻断，小写命中→复核。"""
        lex = lexicon_of("Brother")
        hits = scan(
            {"bullets": ["Fits Brother printers.", "A gift from my brother."]},
            lex, 1, set())
        self.assertEqual(
            [(h["term"], h["severity"]) for h in hits],
            [("Brother", "block"), ("brother", "review")])

    def test_lead_position_capital_is_not_brand_evidence(self):
        """句首/五点开头的大写是语法，不是品牌信号，只能判复核。"""
        lex = lexicon_of("Bounce")
        hits = scan({"bullets": ["Bounce back after every wash."]}, lex, 1, set())
        self.assertEqual(hits[0]["severity"], "review")

    def test_all_caps_run_voids_casing_signal(self):
        """亚马逊五点惯用全大写开头短语，整段大写时大小写不再有区分力。"""
        lex = lexicon_of("Chill")
        hits = scan({"bullets": ["PERFECT CHILL EVERY TIME - keeps drinks cold."]}, lex, 1, set())
        self.assertEqual(hits[0]["severity"], "review")

    def test_title_case_field_voids_the_casing_signal(self):
        """亚马逊标题惯用 Title Case，实词全大写开头，此时大写不是品牌证据。"""
        lex = lexicon_of("Velvet")
        hits = scan(
            {"title": "Soapstone Whiskey Chilling Cubes, Set of 9 with Velvet Pouch"},
            lex, 1, set())
        self.assertEqual(hits[0]["severity"], "review")

    def test_sentence_case_field_still_blocks(self):
        """普通句式里的孤立大写词仍然是品牌证据。"""
        lex = lexicon_of("Velvet")
        hits = scan(
            {"description": "This pouch is soft and keeps Velvet safe from scratches."},
            lex, 1, set())
        self.assertEqual(hits[0]["severity"], "block")

    def test_standalone_capital_mid_sentence_blocks(self):
        lex = lexicon_of("Weber")
        hits = scan({"bullets": ["Fits most Weber grills."]}, lex, 1, set())
        self.assertEqual(hits[0]["severity"], "block")

    def test_backend_fields_block_regardless_of_case(self):
        """后台词天然小写；竞品品牌埋 Search Terms 是零容忍项。"""
        lex = lexicon_of("Yeti")
        hits = scan({"search_terms": "tumbler yeti compatible"}, lex, 1, set())
        self.assertEqual(hits[0]["severity"], "block")
        self.assertIn("后台字段", hits[0]["reason"])

    def test_reproduced_generic_backend_terms_review_instead_of_blocking(self):
        lex = lexicon_of("tummy time", "stimulation", "discovery", "weebles")
        hits = scan({
            "search_terms": "tummy time stimulation discovery weebles",
        }, lex, 2, set())
        by_term = {hit["term"]: hit for hit in hits}

        for term in ("tummy time", "stimulation", "discovery"):
            self.assertEqual(by_term[term]["severity"], "review")
            self.assertIn("通用类目表达", by_term[term]["reason"])
        self.assertEqual(by_term["weebles"]["severity"], "block")

    def test_own_brand_is_never_reported(self):
        lex = lexicon_of("Velmoriq")
        hits = scan({"title": "Velmoriq Whiskey Stones"}, lex, 1, {"velmoriq"})
        self.assertEqual(hits, [])

    def test_multi_token_phrase_wins_over_its_prefix(self):
        """最长匹配优先，且吃掉整个短语，避免同一处报两条。"""
        lex = lexicon_of("The Grinch", "The")
        hits = scan({"description": "Wearing The Grinch sweater to work."}, lex, 2, set())
        self.assertEqual([h["term"] for h in hits], ["The Grinch"])
        self.assertEqual(hits[0]["severity"], "block")

    def test_multi_token_phrase_follows_the_same_casing_rule(self):
        """词库里有 'bpa free'、'food grade' 这类被注册的普通短语，
        「多词即品牌」会把常规材质宣称判死，所以短语同样看大小写。"""
        lex = lexicon_of("the grinch")
        self.assertEqual(
            scan({"description": "a the grinch style sweater"}, lex, 2, set())[0]["severity"],
            "review")
        self.assertEqual(
            scan({"description": "a The Grinch style sweater"}, lex, 2, set())[0]["severity"],
            "block")

    def test_token_boundaries_are_respected(self):
        """'cure' 不得命中 'secure'，'3m' 不得命中 '30ml'。"""
        lex = lexicon_of("Cure", "3M")
        hits = scan({"description": "Secure lid, 30ml capacity."}, lex, 1, set())
        self.assertEqual(hits, [])

    def test_case_variants_normalize_to_one_entry(self):
        """GoPro / gopro / gopro 归一到同一条词目。"""
        lex = lexicon_of("GoPro")
        hits = scan({"title": "Mount for gopro cameras"}, lex, 1, set())
        self.assertEqual(hits[0]["term"], "gopro")

    def test_split_spelling_of_one_word_mark_is_caught_as_review(self):
        """连字符/空格拆写要抓到，但属启发式，只能判复核。"""
        lex, comp = lexicon_of("GoPro"), compacts_of("GoPro")
        hits = scan({"title": "Mount for GO-PRO cameras"}, lex, 2, set(), comp)
        self.assertEqual(hits[0]["term"], "GO-PRO")
        self.assertEqual(hits[0]["severity"], "review")
        self.assertIn("启发式", hits[0]["reason"])

    def test_split_match_never_blocks_even_in_backend_fields(self):
        """启发式命中在后台字段也不升级为阻断，避免 'black berry' 这类误杀。"""
        lex, comp = lexicon_of("BlackBerry"), compacts_of("BlackBerry")
        hits = scan({"search_terms": "black berry jam"}, lex, 2, set(), comp)
        self.assertEqual(hits[0]["severity"], "review")

    def test_short_joins_are_not_compacted(self):
        """少于 5 字符的合并形态噪声太大，不建索引。"""
        self.assertIsNone(compact_digest(tokenize("go go")))

    def test_bullets_list_is_flattened_per_field(self):
        lex = lexicon_of("Yeti")
        hits = scan({"bullets": ["one", "Fits Yeti cups"]}, lex, 1, set())
        self.assertEqual(severities(hits), {("bullets", "Yeti"): "block"})

    def test_clean_listing_produces_no_hits(self):
        lex = lexicon_of("Yeti", "Brother")
        hits = scan({"title": "Soapstone Whiskey Chilling Cubes, Set of 9"}, lex, 1, set())
        self.assertEqual(hits, [])


class LexiconHashTest(unittest.TestCase):
    def test_digest_ignores_case_and_surrounding_punctuation(self):
        self.assertEqual(digest(tokenize("3M")), digest(tokenize("  3m! ")))
        self.assertEqual(digest(tokenize("GoPro")), digest(tokenize("gopro")))

    def test_internal_punctuation_splits_tokens_and_needs_the_compact_path(self):
        """连字符会切词，所以 'go-pro' 不等于 'GoPro' 的精确摘要——那由合并形态兜底。"""
        self.assertNotEqual(digest(tokenize("GoPro")), digest(tokenize("go-pro")))
        self.assertEqual(compact_digest(tokenize("GoPro")), compact_digest(tokenize("go-pro")))

    def test_distinct_phrases_get_distinct_digests(self):
        self.assertNotEqual(digest(tokenize("Weber")), digest(tokenize("Webber")))


if __name__ == "__main__":
    unittest.main()
