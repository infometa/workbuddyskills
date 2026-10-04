#!/usr/bin/env python3
"""双层规格模型（listing_spec + 各 saver --spec）回归测试。

覆盖三类行为：
1. 不传 spec：使用平台单条硬限制与默认 1000 字符合计限制；
2. 传用户 spec：Layer B 上限按用户值执行，错误带 [用户规格] 前缀；
3. 平台底线：任何 spec 都不能放宽 Layer A，越线在加载期即被拒绝。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
# 开发态里共享 skill 住 linkfoxagent-v2/，部署后才和自有 skill 一起平铺到 skills/。
# 两处都找，找不到就 skip——不要因为某个 saver 是共享 skill 就让整组回归变红。
SHARED_POOL = SKILLS.parents[2] / "linkfoxagent-v2"


def _saver(rel: str) -> Path:
    for base in (SKILLS, SHARED_POOL):
        candidate = base / rel
        if candidate.is_file():
            return candidate
    return SKILLS / rel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from listing_spec import (  # noqa: E402
    check_range,
    field_enabled,
    resolve_limit,
    validate_spec,
)

BULLETS_SAVER = _saver("listing-bullet-writer/scripts/save_bullets_output.py")
DESC_SAVER = _saver("listing-description-writer/scripts/save_description_output.py")
SEARCH_SAVER = _saver("listing-search-terms-writer/scripts/save_search_terms_output.py")


def run_saver(script: Path, payload: dict, spec: dict | None = None) -> subprocess.CompletedProcess:
    if not script.is_file():
        raise unittest.SkipTest(f"saver 不在本工作区（自有 skills/ 与共享池均未找到）：{script.name}")
    args = [sys.executable, str(script)]
    tmp = None
    if spec is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(spec, tmp)
        tmp.close()
        args += ["--spec", tmp.name]
    env = dict(os.environ)
    env.pop("LISTING_SPEC_PATH", None)
    proc = subprocess.run(
        args,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
    )
    if tmp:
        os.unlink(tmp.name)
    return proc


USER_SPEC = {
    # 用户示例 prompt 的规格：标题 ~190、五点 200-400、描述 1000-2000、无 highlights
    "title": {"max": 190},
    "item_highlights": {"enabled": False},
    "bullets": {"count": 5, "each_max": 400, "each_min": 200, "total_max": 2000},
    "description": {"max": 2000, "min": 1000},
    "search_terms": {"bytes_max": 250},
}


class TestModule(unittest.TestCase):
    def test_resolve_limit_default(self):
        self.assertEqual(resolve_limit(None, "title", "max", 75), (75, "default"))

    def test_resolve_limit_user(self):
        self.assertEqual(resolve_limit(USER_SPEC, "title", "max", 75), (190, "user_spec"))

    def test_field_enabled(self):
        self.assertTrue(field_enabled(None, "item_highlights"))
        self.assertFalse(field_enabled(USER_SPEC, "item_highlights"))
        self.assertFalse(field_enabled({"item_highlights": {"max": 0}}, "item_highlights"))

    def test_platform_floor_rejects_spec(self):
        errors = validate_spec({"description": {"max": 2500}})
        self.assertTrue(any("平台硬限制" in e for e in errors))
        errors = validate_spec({"title": {"max": 250}})
        self.assertTrue(any("平台硬限制" in e for e in errors))
        errors = validate_spec({"search_terms": {"bytes_max": 500}})
        self.assertTrue(any("平台硬限制" in e for e in errors))
        self.assertEqual(validate_spec(USER_SPEC), [])

    def test_check_range_layers(self):
        errs = check_range(450, field="bullets", label="第 1 条五点", spec=USER_SPEC,
                           max_key="each_max", min_key="each_min", default_max=200, default_min=0)
        self.assertTrue(any("[用户规格]" in e for e in errs))
        errs = check_range(150, field="bullets", label="第 1 条五点", spec=USER_SPEC,
                           max_key="each_max", min_key="each_min", default_max=200, default_min=0)
        self.assertTrue(any("低于下限" in e for e in errs))
        errs = check_range(600, field="bullets", label="第 1 条五点", spec=USER_SPEC,
                           max_key="each_max", min_key="each_min", default_max=200, default_min=0)
        self.assertTrue(any("[平台硬限制]" in e for e in errs))


class TestBulletsSaver(unittest.TestCase):
    def test_no_spec_regression_pass(self):
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 180] * 5})
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_no_spec_allows_over_200_when_total_is_valid(self):
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 204, "a", "b", "c", "d"]})
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_no_spec_fails_over_255(self):
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 256, "a", "b", "c", "d"]})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("超长", proc.stderr)

    def test_user_spec_allows_400(self):
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 390] * 5}, spec=USER_SPEC)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_user_spec_min_enforced(self):
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 100] * 5}, spec=USER_SPEC)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("[用户规格]", proc.stderr)

    def test_user_spec_count(self):
        spec = {"bullets": {"count": 3, "total_max": 2500}}
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 150] * 3}, spec=spec)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        proc = run_saver(BULLETS_SAVER, {"bullets": ["x" * 150] * 5}, spec=spec)
        self.assertEqual(proc.returncode, 2)

    def test_platform_floor_wins_over_default_misuse(self):
        # spec 合法（each_max=500 恰在平台上限）但内容 501 → 平台错误
        proc = run_saver(
            BULLETS_SAVER,
            {"bullets": ["x" * 501] * 5},
            spec={"bullets": {"each_max": 500, "total_max": 2500}},
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("[平台硬限制]", proc.stderr)


class TestDescriptionSaver(unittest.TestCase):
    def test_no_spec_regression(self):
        self.assertEqual(run_saver(DESC_SAVER, {"description": "x" * 900}).returncode, 0)
        proc = run_saver(DESC_SAVER, {"description": "x" * 1200})
        self.assertEqual(proc.returncode, 2)

    def test_user_spec_allows_1800(self):
        proc = run_saver(DESC_SAVER, {"description": "x" * 1800}, spec=USER_SPEC)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_user_spec_min(self):
        proc = run_saver(DESC_SAVER, {"description": "x" * 500}, spec=USER_SPEC)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("低于下限", proc.stderr)

    def test_spec_beyond_platform_rejected_at_load(self):
        proc = run_saver(DESC_SAVER, {"description": "x" * 100}, spec={"description": {"max": 2500}})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("平台硬限制", proc.stderr)


class TestSearchTermsSaver(unittest.TestCase):
    def test_no_spec_regression(self):
        self.assertEqual(run_saver(SEARCH_SAVER, {"search_terms": "alpha beta gamma"}).returncode, 0)
        proc = run_saver(SEARCH_SAVER, {"search_terms": "x" * 260})
        self.assertEqual(proc.returncode, 2)

    def test_user_spec_tighten(self):
        proc = run_saver(SEARCH_SAVER, {"search_terms": "x" * 200}, spec={"search_terms": {"bytes_max": 150}})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("[用户规格]", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
