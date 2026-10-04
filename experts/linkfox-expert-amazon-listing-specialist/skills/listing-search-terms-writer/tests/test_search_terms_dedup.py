#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from save_search_terms_output import dedup_against_front  # noqa: E402


class TestSearchTermsDedup(unittest.TestCase):
    def test_keeps_unicode_words_intact(self) -> None:
        terms = "kühlwürfel zubehör whisky geschenkidee"
        front = ["Kühlsteine für Whisky – ideale Geschenkidee"]
        deduped, removed = dedup_against_front(terms, front)
        self.assertEqual(removed, ["whisky", "geschenkidee"])
        self.assertEqual(deduped, "kühlwürfel zubehör")

    def test_matches_accents_across_all_supplied_front_texts(self) -> None:
        deduped, removed = dedup_against_front(
            "glacière dégustation bourbon",
            ["Coffret DÉGUSTATION", "Une glacière compacte"],
        )
        self.assertEqual(removed, ["glacière", "dégustation"])
        self.assertEqual(deduped, "bourbon")

    def test_does_not_apply_english_stemming_to_other_locales(self) -> None:
        deduped, removed = dedup_against_front("pierre", ["pierres naturelles"])
        self.assertEqual(removed, [])
        self.assertEqual(deduped, "pierre")


if __name__ == "__main__":
    unittest.main()
