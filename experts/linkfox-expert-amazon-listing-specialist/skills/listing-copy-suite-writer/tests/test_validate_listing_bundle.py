from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_listing_bundle.py"


def valid_payload() -> dict:
    return {
        "title": "Reusable Pet Hair Remover for Furniture and Car Seats",
        "item_highlights": "Quick lint pickup for sofas, bedding, clothing, and travel",
        "bullets": [
            "LIFTS EMBEDDED HAIR — Textured surface collects loose pet hair from upholstery without disposable sheets.",
            "REUSABLE DAILY TOOL — Empty the collection chamber and keep the roller ready for routine cleanup.",
            "MULTI-SURFACE CLEANING — Use on sofas, bedding, car seats, and clothing after checking fabric care guidance.",
            "COMFORTABLE HANDLING — Contoured grip supports controlled passes across cushions and other fabric surfaces.",
            "COMPACT STORAGE — Lightweight form fits cleaning cabinets, vehicle organizers, and travel bags.",
        ],
        "description": (
            "Keep fabric surfaces tidy with a reusable remover designed for everyday pet hair pickup. "
            "The textured cleaning surface gathers loose fibers into an easy-empty chamber. "
            "Use it across sofas, bedding, clothing, and vehicle upholstery after checking the care guidance for each fabric."
        ),
        "search_terms": "dander shedding kitty canine grooming accessory",
        "competitor_brands": ["AcmeCo"],
        "banned_terms": ["miracle clean"],
        "brand": "Northwind",
        "product_name": "Reusable Pet Hair Remover",
        "category": "Pet Supplies",
        "market": "Amazon US",
    }


class ValidateListingBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        # 产物落在 cwd 下的 linkfox/<date>/<session>/data/，断言要读它，所以目录须活到用例结束
        self._workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._workdir.cleanup)

    def run_validator(self, payload: dict) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._workdir.name,
            check=False,
        )

    def last_json(self, stdout: str) -> dict:
        for line in reversed(stdout.splitlines()):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise AssertionError(f"no result JSON in stdout:\n{stdout}")

    # --- 正常路径 --------------------------------------------------------

    def test_valid_bundle_passes_and_reports_zero_mutation(self) -> None:
        proc = self.run_validator(valid_payload())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Compliance artifact:", proc.stdout)
        self.assertIn("Saved full response:", proc.stdout)
        result = self.last_json(proc.stdout)
        self.assertEqual(result["status"], "success")
        self.assertIs(result["content_mutated_by_script"], False)

    def test_compliance_artifact_shape_matches_exporter_contract(self) -> None:
        """export_listing_copy_xlsx.py 会读 compliance_path 并要求 status=passed。"""
        proc = self.run_validator(valid_payload())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.last_json(proc.stdout)
        doc = json.loads(Path(result["compliance_path"]).read_text(encoding="utf-8"))
        report = doc["compliance_report"]
        self.assertEqual(report["status"], "passed")
        self.assertIs(report["passed"], True)
        self.assertIn("raw_check", doc)

    def test_single_process_no_subprocess_fanout(self) -> None:
        """回归护栏：不得再退回按字段拉起多个 writer 子进程。

        只查真实调用手段（subprocess / os.exec / 四个 save_*_output），不查文字——
        文档说明实现策略时不该被护栏误伤。
        """
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.execv", "os.execvp",
                          "save_title_output", "save_bullets_output",
                          "save_description_output", "save_search_terms_output"):
            self.assertNotIn(forbidden, source, f"不得重新引入 {forbidden}")

    # --- 门禁：逐条对齐原 keyword_checker -------------------------------

    def test_competitor_brand_blocks(self) -> None:
        payload = valid_payload()
        payload["description"] = payload["description"] + " Better than AcmeCo."
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("competitor_brand", proc.stderr)

    def test_user_banned_term_blocks(self) -> None:
        """调用方 banned_terms 走 spec.user_banned_terms，判 fail → exit 2。"""
        payload = valid_payload()
        payload["title"] = "Miracle Clean Pet Hair Remover"
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("miracle clean", proc.stderr)
        self.assertIn("user_banned", proc.stderr)

    def test_restricted_block_term_exits_2_not_3(self) -> None:
        """受限词库的 block 级命中必须阻断（2），不能降级成人工复核（3）。

        block 级受限内容必须停止交付。
        """
        payload = valid_payload()
        payload["description"] += " Intended for cannabis storage."
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("cannabis", proc.stderr)

    def test_restricted_review_term_exits_3(self) -> None:
        """review 级命中只要人工复核（3），不能升级成阻断。

        review 级受限内容必须进入人工复核。
        """
        payload = valid_payload()
        payload["description"] += " Includes an antibacterial surface claim."
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 3, proc.stdout)
        self.assertIn("antibacterial", proc.stderr)

    def test_secure_does_not_false_match_cure(self) -> None:
        """"secure" 不得被 "cure" 误命中。"""
        payload = valid_payload()
        payload["description"] += " A secure closure helps keep the case shut during travel."
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_block_and_review_together_block_wins(self) -> None:
        """同时命中 block 与 review 时，整体判 blocked。"""
        payload = valid_payload()
        payload["description"] += " Intended for cannabis storage with an antibacterial surface."
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)

    def test_over_limit_title_blocks(self) -> None:
        payload = valid_payload()
        payload["title"] = "Pet Hair Remover " * 20
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("over_limit", proc.stderr)

    def test_front_dup_is_zero_tolerance(self) -> None:
        """原 keyword_checker 的 search_terms_dedup 是零容忍，迁移后必须保持。"""
        payload = valid_payload()
        payload["search_terms"] = "reusable dander shedding"  # reusable 已在五点出现
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("front_dup", proc.stderr)

    # --- 输入门禁 --------------------------------------------------------

    def test_missing_required_field(self) -> None:
        payload = valid_payload()
        payload["description"] = ""
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("缺少必填字段", proc.stderr)

    def test_bullets_must_be_exactly_five(self) -> None:
        payload = valid_payload()
        payload["bullets"] = payload["bullets"][:4]
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("bullets 必须是恰好 5 条", proc.stderr)

    def test_benchmark_without_competitor_brands_is_rejected(self) -> None:
        payload = valid_payload()
        payload["competitor_brands"] = []
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("竞品品牌零容忍检查", proc.stderr)

    def test_is_media_makes_item_highlights_optional(self) -> None:
        payload = valid_payload()
        payload["item_highlights"] = ""
        payload["is_media"] = True
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bad_json_input(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input="not json",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                check=False,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("不是合法 JSON", proc.stderr)

    def test_script_never_mutates_content(self) -> None:
        payload = valid_payload()
        original = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        proc = self.run_validator(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.last_json(proc.stdout)
        doc = json.loads(Path(result["compliance_path"]).read_text(encoding="utf-8"))
        # 产物里不得出现被改写过的正文
        self.assertEqual(original, json.dumps(payload, ensure_ascii=False, sort_keys=True))
        self.assertIs(doc["compliance_report"]["passed"], True)


if __name__ == "__main__":
    unittest.main()
