import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from mck_fusion import FusionDeck
from mckinsey_pptx.base import add_line, blank_slide, init_presentation
from mckinsey_pptx.theme import DEFAULT_THEME
from scripts.build_fusion_deck import build_deck
from scripts.gate_check import run_gate_check
from scripts.gate_check_s3 import run_gate_check_s3
from scripts.render_preview import render_preview


def valid_spec():
    return {
        "meta": {
            "title": "增长战略",
            "audience": "管理委员会",
            "governing_thought": "资源应集中投入高潜场景",
            "total_slides": 2,
            "language": "zh-CN",
        },
        "slides": [
            {
                "idx": 1,
                "layout": "cover",
                "engine": "main",
                "title": "增长战略",
                "role": "Transition",
                "rhythm": "Transition",
                "visual_role": "Cover",
                "anti_pattern": "不使用受保护品牌标识",
                "density": "low",
                "objective": "建立决策主题",
                "one_message": "资源应聚焦高潜场景",
                "evidence": [],
                "source": [],
                "data": {"subtitle": "管理委员会讨论稿", "date": "2026-07"},
            },
            {
                "idx": 2,
                "layout": "three_trends_numbered",
                "engine": "supplemental",
                "title": "三个结构性趋势正在提高聚焦高潜场景的必要性",
                "role": "Hero",
                "rhythm": "Peak",
                "visual_role": "Evidence structure",
                "anti_pattern": "不使用无差异等宽卡片",
                "density": "medium",
                "objective": "证明资源聚焦的必要性",
                "one_message": "结构性变化要求聚焦投入",
                "evidence": [{"claim_id": "C-01", "grade": "[F]"}],
                "source": [{"label": "内部经营分析", "url": ""}],
                "data": {
                    "subtitle": "",
                    "section_marker": "",
                    "trends": [
                        {"label": "需求", "bullets": ["高价值需求向专业场景集中"]},
                        {"label": "供给", "bullets": ["优质供给仍然稀缺"]},
                        {"label": "效率", "bullets": ["复用机制决定规模效率"]},
                    ],
                },
            },
        ],
    }


class DeckPipelineTests(unittest.TestCase):
    def write_spec(self, directory, spec):
        path = Path(directory) / "deck_spec.json"
        path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        return path

    def test_s3_rejects_empty_slides(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_spec(tmp, {"meta": {"total_slides": 0}, "slides": []})
            result = run_gate_check_s3(str(path), tmp)
            self.assertFalse(result["passed"])
            self.assertTrue(any(item["check"] == "slides_empty" for item in result["fail_items"]))

    def test_s3_rejects_placeholders(self):
        spec = valid_spec()
        spec["slides"][1]["data"]["subtitle"] = "[Insert subtitle]"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_spec(tmp, spec)
            result = run_gate_check_s3(str(path), tmp)
            self.assertFalse(result["passed"])
            self.assertTrue(any(item["check"] == "placeholder" for item in result["fail_items"]))

    def test_add_line_is_connector_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            prs = init_presentation(DEFAULT_THEME)
            slide = blank_slide(prs)
            add_line(slide, 1.0, 1.0, 5.0, 1.0, color=DEFAULT_THEME.palette.rule_gray)
            path = Path(tmp) / "line.pptx"
            prs.save(path)
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            self.assertNotIn("<p:cxnSp", xml)

    def test_mixed_engine_build_and_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = self.write_spec(tmp, valid_spec())
            output = Path(tmp) / "mixed.pptx"
            result_path = Path(tmp) / "build_result.json"
            result = build_deck(str(spec_path), str(output), str(result_path))
            self.assertTrue(result["passed"], result)
            self.assertEqual(result["actual_slides"], 2)
            self.assertTrue(output.exists())
            with zipfile.ZipFile(output) as archive:
                slide_xml = "".join(
                    archive.read(name).decode("utf-8")
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
            self.assertNotIn("<p:cxnSp", slide_xml)
            self.assertIn("2/2", slide_xml)
            gate = run_gate_check(str(output), tmp)
            self.assertIn("checklist", gate)
            self.assertFalse(any(
                item.get("category") == "guard_rail" and "connector" in item.get("message", "").lower()
                for item in gate.get("user_code_error_detail", [])
            ))

    def test_render_preview_has_honest_degradation(self):
        with tempfile.TemporaryDirectory() as tmp:
            prs = init_presentation(DEFAULT_THEME)
            blank_slide(prs)
            path = Path(tmp) / "preview.pptx"
            prs.save(path)
            result = render_preview(str(path), tmp)
            self.assertTrue(result["passed"], result)
            self.assertIn(result["mode"], {"full", "quicklook_first_screen", "structure_only"})
            self.assertTrue((Path(tmp) / "preview" / "structure_preview.json").exists())
            if result["mode"] != "full":
                self.assertFalse(result["full_render"])
                self.assertIn("degraded", result["note"].lower())

    def test_unknown_layout_fails_fast(self):
        spec = valid_spec()
        spec["slides"][1]["layout"] = "not_a_real_layout"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_spec(tmp, spec)
            result = run_gate_check_s3(str(path), tmp)
            self.assertFalse(result["passed"])
            self.assertTrue(any(item["check"] == "layout_unknown" for item in result["fail_items"]))
            deck = FusionDeck(total_slides=1)
            with self.assertRaises(RuntimeError):
                deck.build_specs([{
                    "idx": 1,
                    "layout": "not_a_real_layout",
                    "engine": "main",
                    "data": {},
                    "source": [],
                }])


if __name__ == "__main__":
    unittest.main()
