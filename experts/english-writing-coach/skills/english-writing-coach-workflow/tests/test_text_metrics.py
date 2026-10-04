from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "text_metrics.py"
SPEC = importlib.util.spec_from_file_location("text_metrics", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TextMetricsTests(unittest.TestCase):
    def test_basic_sentence_count(self) -> None:
        result = MODULE.analyze("This is one sentence. This is another! Is this the third?")
        self.assertEqual(result["sentence_count"], 3)
        self.assertEqual(result["total_word_count"], 11)
        self.assertEqual(result["effective_word_count"], 11)

    def test_common_abbreviation_does_not_split_sentence(self) -> None:
        result = MODULE.analyze("Dr. Smith wrote one sentence.\nNext paragraph here.")
        self.assertEqual(result["sentence_count"], 2)
        self.assertEqual(result["paragraph_count"], 2)
        self.assertEqual(result["paragraph_mode_used"], "line")

    def test_initials_and_decimal_do_not_split_sentence(self) -> None:
        result = MODULE.analyze("J. Smith reported 3.5 points. The U.S. sample was small.")
        self.assertEqual(result["sentence_count"], 2)

    def test_blank_line_mode_preserves_wrapped_lines(self) -> None:
        text = "First wrapped line\ncontinues here.\n\nSecond paragraph ends here."
        result = MODULE.analyze(text)
        self.assertEqual(result["paragraph_count"], 2)
        self.assertEqual(result["paragraph_mode_used"], "blank-line")

    def test_exact_exclusion_changes_effective_count(self) -> None:
        text = "Write about honesty. Honesty helps people build trust."
        result = MODULE.analyze(text, exclusions=["Write about honesty."])
        self.assertEqual(result["total_word_count"], 8)
        self.assertEqual(result["excluded_word_count"], 3)
        self.assertEqual(result["effective_word_count"], 5)
        self.assertEqual(result["exclusions"][0]["occurrence_count"], 1)

    def test_missing_exclusion_is_reported_without_subtraction(self) -> None:
        result = MODULE.analyze("A complete sentence.", exclusions=["Not present."])
        self.assertEqual(result["excluded_word_count"], 0)
        self.assertEqual(len(result["warnings"]), 1)

    def test_empty_text(self) -> None:
        result = MODULE.analyze("")
        self.assertEqual(result["sentence_count"], 0)
        self.assertEqual(result["paragraph_count"], 0)
        self.assertEqual(result["effective_word_count"], 0)


if __name__ == "__main__":
    unittest.main()
