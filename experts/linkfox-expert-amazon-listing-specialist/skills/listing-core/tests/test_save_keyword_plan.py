#!/usr/bin/env python3
"""save_keyword_plan 回归测试。

keywords.json 是词表工作台和 `[fieldAdjust:keywords]` 的唯一数据入口，
此前没有生产者。这里守三件事：
1. 落盘的 kind/schema_version 必须是 UI 认得的 listingKeywordPlan；
2. 用户手输词不许带搜索量（编造 volume 是硬错）；
3. 走 `JSON artifact:` 行，不抢一次 Bash 唯一的 `Saved full response:`。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SAVE_PLAN = SCRIPTS / "save_keyword_plan.py"


def run(payload: dict, out: Path, matrix: Path | None = None) -> subprocess.CompletedProcess:
    out.parent.mkdir(parents=True, exist_ok=True)
    source = out.parent / "grouped-keywords.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    command = [
        sys.executable, str(SAVE_PLAN), "--out", str(out), "--source", str(source),
    ]
    if matrix:
        command += ["--matrix", str(matrix)]
    return subprocess.run(
        command, capture_output=True, text=True,
    )


BASE = {
    "core": [{"word": "dog water bottle", "source": "SIF", "search_volume": 40321}],
    "scene": ["hiking"],
    "pain": [],
    "attribute": [],
    "locked": ["dog water bottle"],
    "banned": ["LEAKPROOF"],
}


class SaveKeywordPlanTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "02-insight" / "keywords.json"

    def test_writes_ui_contract_and_json_artifact_line(self):
        result = run(BASE, self.out)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(plan["kind"], "listingKeywordPlan")
        self.assertEqual(plan["schema_version"], 1)
        # 裸字符串词要补齐成对象，缺的数据是 null 而不是编造
        self.assertEqual(
            plan["scene"][0], {"word": "hiking", "source": "unknown", "search_volume": None}
        )
        self.assertEqual(plan["locked"], ["dog water bottle"])
        self.assertIn(f"JSON artifact: {self.out}", result.stdout)
        self.assertNotIn("Saved full response:", result.stdout)

    def test_missing_source_fails_immediately(self):
        result = subprocess.run(
            [sys.executable, str(SAVE_PLAN), "--out", str(self.out)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=2,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--source", result.stderr)

    def test_missing_source_file_has_actionable_error(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SAVE_PLAN),
                "--out",
                str(self.out),
                "--source",
                str(Path(self.temp.name) / "missing.json"),
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("无法读取 --source", result.stderr)

    def test_user_typed_word_cannot_carry_search_volume(self):
        payload = {
            **BASE,
            "scene": [{"word": "camping", "source": "user", "search_volume": 1234}],
        }
        result = run(payload, self.out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("search_volume 必须为 null", result.stderr)

    def test_locked_word_must_exist_in_groups(self):
        result = run({**BASE, "locked": ["not in the plan"]}, self.out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("locked", result.stderr)

    def test_normalizes_object_shaped_locked_and_banned_entries(self):
        payload = {
            **BASE,
            "locked": [{"word": "dog water bottle", "source": "SIF"}],
            "banned": [{"word": "BrandX", "source": "policy"}],
        }
        result = run(payload, self.out)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(plan["locked"], ["dog water bottle"])
        self.assertEqual(plan["banned"], ["BrandX"])

    def test_rejects_object_without_word_in_string_lists(self):
        result = run({**BASE, "locked": [{"source": "SIF"}]}, self.out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("带 word 的对象", result.stderr)

    def test_matrix_enriches_grouped_words_without_reclassifying(self):
        matrix = Path(self.temp.name) / "matrix.json"
        matrix.write_text(json.dumps({"scored_table": [
            {
                "keyword": "dog water bottle", "source": "SIF",
                "weekly_search_volume": 40321, "field": "Title",
            },
            {
                "keyword": "hiking", "source": "SIF",
                "weekly_search_volume": 812, "field": "Bullet 2",
            },
        ]}), encoding="utf-8")
        payload = {
            "core": ["dog water bottle"], "scene": ["hiking"],
            "pain": [], "attribute": [], "locked": [], "banned": [],
        }
        result = run(payload, self.out, matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(plan["core"][0]["source"], "SIF")
        self.assertEqual(plan["core"][0]["search_volume"], 40321)
        self.assertEqual(plan["scene"][0]["search_volume"], 812)

    def test_matrix_does_not_overwrite_explicit_local_provenance(self):
        matrix = Path(self.temp.name) / "matrix.json"
        matrix.write_text(json.dumps({"scored_table": [{
            "keyword": "hiking", "source": "SIF", "weekly_search_volume": 812,
        }]}), encoding="utf-8")
        payload = {
            **BASE,
            "scene": [{"word": "hiking", "source": "local", "search_volume": None}],
        }
        result = run(payload, self.out, matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(plan["scene"][0]["source"], "local")
        self.assertIsNone(plan["scene"][0]["search_volume"])

    def test_empty_plan_is_rejected(self):
        result = run(
            {"core": [], "scene": [], "pain": [], "attribute": [], "locked": [], "banned": []},
            self.out,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("keyword_data_unavailable", result.stderr)


if __name__ == "__main__":
    unittest.main()
