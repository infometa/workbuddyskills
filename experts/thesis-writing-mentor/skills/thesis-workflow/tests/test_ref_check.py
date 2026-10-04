#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "ref_check.py"
spec = importlib.util.spec_from_file_location("ref_check", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ReferenceCheckTests(unittest.TestCase):
    def test_missing_fields_are_reported(self):
        result = module.audit("张三. 缺少来源和年份的题名[J].\n")
        item = result["field_completeness"]["items"][0]
        self.assertFalse(item["complete"])
        self.assertIn("year", item["missing"])
        self.assertIn("source", item["missing"])
        self.assertIn("pages", item["missing"])

    def test_duplicate_doi_has_priority(self):
        text = (
            "张三. 甲题名[J]. 教育研究, 2023, 12(3): 45-52. doi:10.1234/SAME.\n"
            "李四. 乙题名[J]. 高教研究, 2024, 13(2): 10-18. https://doi.org/10.1234/same.\n"
        )
        groups = module.audit(text)["duplicates"]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["method"], "doi")
        self.assertEqual(groups[0]["entries"], [1, 2])

    def test_normalized_title_duplicate_without_doi(self):
        text = (
            "张三. 学术写作：结构与证据[J]. 教育研究, 2023, 12(3): 45-52.\n"
            "李四. 学术写作: 结构与证据[J]. 高教研究, 2024, 13(2): 10-18.\n"
        )
        groups = module.audit(text)["duplicates"]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["method"], "normalized_title")

    def test_common_punctuation_errors_are_reported(self):
        result = module.audit("张三. 示例题名[J] 教育研究，2023，12(3)：45-52\n")
        codes = {item["code"] for item in result["punctuation"]["issues"]}
        self.assertIn("PUNCT_AFTER_TYPE", codes)
        self.assertIn("FULLWIDTH_SEPARATOR", codes)
        self.assertIn("MISSING_TERMINAL_PERIOD", codes)

    def test_normal_sample_passes(self):
        text = "张三. 规范著录示例[J]. 教育研究, 2023, 12(3): 45-52. doi:10.1234/example.1.\n"
        result = module.audit(text)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["field_completeness"]["incomplete_count"], 0)
        self.assertEqual(result["punctuation"]["issue_count"], 0)
        self.assertEqual(result["duplicates"]["group_count"], 0)

    def test_missing_doi_is_hint_not_error(self):
        text = "张三. 无 DOI 的有效条目[J]. 教育研究, 2023, 12(3): 45-52.\n"
        result = module.audit(text)
        self.assertEqual(result["status"], "PASS")
        item = result["field_completeness"]["items"][0]
        self.assertTrue(item["complete"])
        self.assertTrue(item["hints"])

    def test_human_readable_report_has_three_sections(self):
        result = module.audit("张三. 规范著录示例[J]. 教育研究, 2023, 12(3): 45-52.\n")
        rendered = module.render_text(result)
        self.assertIn("[字段完整性]", rendered)
        self.assertIn("[GB/T 7714 常见标点]", rendered)
        self.assertIn("[重复条目]", rendered)

    def test_cli_json_reads_utf8_bom_without_writing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "references.txt"
            original = "\ufeff张三. 规范著录示例[J]. 教育研究, 2023, 12(3): 45-52. doi:10.1234/example.1.\n".encode("utf-8")
            path.write_bytes(original)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["entry_count"], 1)
            self.assertEqual(path.read_bytes(), original)

    def test_cli_missing_file_returns_two(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "/definitely/not/found-references.txt"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("不存在", completed.stderr)


if __name__ == "__main__":
    unittest.main()
