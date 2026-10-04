#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "thesis_preflight.py"
spec = importlib.util.spec_from_file_location("thesis_preflight", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ThesisPreflightTests(unittest.TestCase):
    def test_clean_text_passes(self):
        result = module.audit("# 引言\n\n本文分析某一明确问题，并说明适用边界。\n")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["summary"], {"P0": 0, "P1": 0, "P2": 0})

    def test_placeholder_is_p0(self):
        result = module.audit("# 结果\n\nAUTHOR_INPUT_NEEDED\n")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["summary"]["P0"], 1)

    def test_missing_numbered_reference_is_p0(self):
        text = "# 正文\n结论已有研究支持[1]。\n# 参考文献\n[2] 示例文献\n"
        result = module.audit(text)
        codes = {item["code"] for item in result["issues"]}
        self.assertIn("MISSING_REFERENCE", codes)
        self.assertIn("UNCITED_REFERENCE", codes)

    def test_heading_jump_is_p2(self):
        result = module.audit("# 一级\n### 三级\n")
        self.assertEqual(result["status"], "WARN")
        self.assertEqual(result["summary"]["P2"], 1)

    def test_overclaim_is_p1(self):
        result = module.audit("本研究首次证明该方法普遍适用。")
        self.assertEqual(result["status"], "WARN")
        self.assertGreaterEqual(result["summary"]["P1"], 2)

    def test_inline_figure_references_are_not_duplicate_captions(self):
        text = "如图1所示，图1中的趋势与结果一致。\n\n图1：主要结果\n"
        result = module.audit(text)
        codes = {item["code"] for item in result["issues"]}
        self.assertNotIn("DUPLICATE_CAPTION", codes)

    def test_duplicate_caption_is_p2(self):
        result = module.audit("图1：结果A\n\n图1：结果B\n")
        codes = {item["code"] for item in result["issues"]}
        self.assertIn("DUPLICATE_CAPTION", codes)

    def test_cli_json_and_strict_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text("本文具有重要意义。", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--json", "--strict"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "WARN")

    def test_cli_missing_file_returns_two(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "/definitely/not/found.md"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
