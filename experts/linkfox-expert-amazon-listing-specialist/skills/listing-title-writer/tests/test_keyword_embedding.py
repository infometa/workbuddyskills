from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from plan_keywords import _contains_term, classify, plan  # noqa: E402

FIXTURE = json.loads((ROOT / "tests/fixtures/keyword-matrix-sample.json").read_text())


class KeywordPlanTest(unittest.TestCase):
    def test_matching_respects_word_boundaries(self):
        self.assertTrue(_contains_term("Go travel bottle", "go"))
        self.assertFalse(_contains_term("dog travel bottle", "go"))

    def test_classifies_keyword_intent(self):
        self.assertEqual(classify("dog water bottle", {})[0], "core")
        self.assertEqual(classify("dog water bottle for hiking", {})[0], "scenario")
        self.assertEqual(classify("leakproof dog bottle", {})[0], "pain")

    def test_plans_only_from_provided_matrix(self):
        result = plan(FIXTURE, top=4, banned=["best"], exclude_brand=["HYDAWAY"])
        self.assertEqual(result["primary_keyword"], "dog water bottle")
        self.assertNotIn("leakproof dog water bottle", result["title_pool"])
        self.assertEqual(result["stats"]["dropped"]["competitor_brand"], 1)


if __name__ == "__main__":
    unittest.main()
