#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SAVE = SCRIPTS / "save_buyer_questions.py"
sys.path.insert(0, str(SCRIPTS))
from build_spec import assemble_spec  # noqa: E402


class SaveBuyerQuestionsTest(unittest.TestCase):
    def test_canonical_output_feeds_build_spec_without_losing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "buyer-questions.json"
            payload = {"questions": [{
                "question": "Will it fit in a backpack?",
                "source": "product_detail_summary",
                "strength": "strong",
                "target_fields": ["bullets", "item_highlights"],
            }]}
            result = subprocess.run(
                [sys.executable, str(SAVE), "--out", str(out)],
                input=json.dumps(payload), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads(out.read_text(encoding="utf-8"))
            spec = assemble_spec("create", [], [], {}, [], buyer_questions=saved)
            self.assertEqual(spec["buyer_questions"], payload["questions"])
            self.assertIn(f"JSON artifact: {out}", result.stdout)

    def test_legacy_string_array_stays_compatible(self) -> None:
        spec = assemble_spec(
            "create", [], [], {}, [], buyer_questions=["Will it fit?"],
        )
        self.assertEqual(spec["buyer_questions"], ["Will it fit?"])

    def test_rejects_missing_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SAVE), "--out", str(Path(tmp) / "questions.json")],
                input=json.dumps({"questions": [{"source": "insight"}]}),
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("缺少 question", result.stderr)


if __name__ == "__main__":
    unittest.main()
