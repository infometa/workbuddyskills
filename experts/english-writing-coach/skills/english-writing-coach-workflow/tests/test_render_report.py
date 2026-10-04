from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "render_report.py"
SPEC = importlib.util.spec_from_file_location("render_report", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_data() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "report_type": "exam_review",
        "title": "CET-4 作文批改报告",
        "meta": {"task": "CET-4", "source": "CET-2016"},
        "score": {"raw": 11, "deduction": 1, "final": 10, "maximum": 15, "band": "11档"},
        "summary": "整体判断",
        "evidence": [{"claim": "支持当前档", "quote": "Original sentence.", "reason": "Reason"}],
        "issues": [{
            "priority": "P1",
            "location": "P2",
            "original": "Original sentence.",
            "suggestion": "Suggested sentence.",
            "reason": "Reason",
        }],
        "actions": ["Rewrite the second paragraph."],
    }


class RenderReportTests(unittest.TestCase):
    def test_valid_contract(self) -> None:
        MODULE.validate_data(valid_data())

    def test_evidence_field_is_required(self) -> None:
        data = valid_data()
        data["evidence"][0]["quote"] = ""
        with self.assertRaisesRegex(ValueError, "evidence\\[0\\]\\.quote"):
            MODULE.validate_data(data)

    def test_issue_field_is_required_when_issue_exists(self) -> None:
        data = valid_data()
        del data["issues"][0]["location"]
        with self.assertRaisesRegex(ValueError, "issues\\[0\\]\\.location"):
            MODULE.validate_data(data)

    def test_actions_must_be_non_empty_strings(self) -> None:
        data = valid_data()
        data["actions"] = [""]
        with self.assertRaisesRegex(ValueError, "actions\\[0\\]"):
            MODULE.validate_data(data)

    def test_score_band_is_required(self) -> None:
        data = valid_data()
        data["score"]["band"] = ""
        with self.assertRaisesRegex(ValueError, "score.band"):
            MODULE.validate_data(data)

    def test_user_content_is_escaped(self) -> None:
        data = valid_data()
        data["summary"] = "<script>alert('x')</script>"
        MODULE.validate_data(data)
        rendered = MODULE.render(data)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
