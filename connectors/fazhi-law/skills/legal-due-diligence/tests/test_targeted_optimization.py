from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from lxml import etree


BASE = Path(__file__).resolve().parents[1]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("legal_dd_builder", BASE / "scripts" / "build_legal_dd_report.py")
VALIDATOR = load_module("legal_dd_validator", BASE / "scripts" / "validate_legal_dd_report.py")


def replace_strings(value, old: str, new: str):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_strings(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, old, new) for key, item in value.items()}
    return value


def document_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
    return "\n".join("".join(p.xpath(".//w:t/text()", namespaces=NS)) for p in root.xpath(".//w:p", namespaces=NS))


class TargetedOptimizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp.name)
        raw = json.loads((BASE / "assets" / "report-data.example.json").read_text(encoding="utf-8"))
        self.data = replace_strings(raw, "示例", "测试")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, data: dict, name: str = "report") -> tuple[Path, Path]:
        data_path = self.temp_dir / f"{name}.json"
        output = self.temp_dir / f"{name}.docx"
        data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        BUILDER.build(BASE / "assets" / "法律尽职调查报告模板_正式无品牌版.docx", data_path, output)
        return output, data_path

    def test_material_source_status_mapping_brand_and_api(self) -> None:
        self.data["business"] = ["模型 API 合同属于本次业务材料。", "EMPTY_RESULT"]
        self.data["compliance"] = ["UNSUPPORTED", "FAILED", "INCOMPLETE"]
        output, data_path = self.build(self.data)
        text = document_text(output)
        self.assertEqual(text.count(BUILDER.BRAND_DISCLOSURE), 1)
        self.assertIn("模型 API 合同", text)
        for status in BUILDER.STATUS_WORDING:
            self.assertNotIn(status, text)
        for wording in BUILDER.STATUS_WORDING.values():
            self.assertIn(wording, text)
        result = VALIDATOR.report_result(output, data_path)
        self.assertTrue(result["ok"], result["errors"])

    def test_public_information_pre_dd_adds_scope_limitation(self) -> None:
        self.data["source_control"]["primary_basis"] = "public_information_pre_dd"
        self.data["source_control"]["primary_material_ids"] = []
        output, data_path = self.build(self.data, "public-pre-dd")
        text = document_text(output)
        self.assertIn(BUILDER.PUBLIC_PRE_DD_LIMITATION, text)
        self.assertTrue(VALIDATOR.report_result(output, data_path)["ok"])

    def test_internal_language_is_rejected_but_api_alone_is_allowed(self) -> None:
        self.data["business"] = ["模型 API 合同可以保留。", "快查接口参数错误。"]
        data_path = self.temp_dir / "blocked.json"
        data_path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(SystemExit):
            BUILDER.build(
                BASE / "assets" / "法律尽职调查报告模板_正式无品牌版.docx",
                data_path,
                self.temp_dir / "blocked.docx",
            )

    def test_current_materials_requires_material_ids(self) -> None:
        self.data["source_control"]["primary_material_ids"] = []
        data_path = self.temp_dir / "missing-materials.json"
        data_path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(SystemExit):
            BUILDER.build(
                BASE / "assets" / "法律尽职调查报告模板_正式无品牌版.docx",
                data_path,
                self.temp_dir / "missing-materials.docx",
            )

    def test_heading_styles_are_explicit_and_theme_free(self) -> None:
        output, _ = self.build(self.data, "fonts")
        with zipfile.ZipFile(output) as zf:
            styles = etree.fromstring(zf.read("word/styles.xml"))
        for style_id, expected in VALIDATOR.HEADING_FONTS.items():
            for candidate in (style_id, f"{style_id}Char"):
                nodes = styles.xpath(f".//w:style[@w:styleId='{candidate}']/w:rPr/w:rFonts", namespaces=NS)
                if not nodes:
                    continue
                node = nodes[0]
                self.assertEqual(node.get(f"{{{W}}}eastAsia"), expected)
                self.assertEqual(node.get(f"{{{W}}}ascii"), "Times New Roman")
                for attr in VALIDATOR.THEME_FONT_ATTRS:
                    self.assertIsNone(node.get(f"{{{W}}}{attr}"))

    def test_limited_external_search_policy_is_scoped_and_evidence_safe(self) -> None:
        skill = (BASE / "SKILL.md").read_text(encoding="utf-8")
        policy = (BASE / "references" / "快查外部核查与底稿规则.md").read_text(encoding="utf-8")
        business = (BASE / "references" / "尽调模块-业务资质合同与关联交易.md").read_text(encoding="utf-8")
        people = (BASE / "references" / "尽调模块-主体股权与公司治理.md").read_text(encoding="utf-8")
        ip_data = (BASE / "references" / "尽调模块-知识产权与数据合规.md").read_text(encoding="utf-8")

        self.assertIn("公司、核心人员、产品/业务、商标/品牌四类事项", skill)
        self.assertIn("先审阅当前采信资料、再完成相关快查查询后", policy)
        self.assertIn("搜索结果摘要不得作为证据", policy)
        self.assertIn("不得登录、付费订阅、注册账户或绕过访问限制", policy)
        self.assertIn("没有负面舆情", policy)
        self.assertIn("无近似商标", policy)
        for excluded in ("财务", "税务", "社保", "合同完整性", "资产权属"):
            self.assertIn(excluded, skill)

        self.assertIn("公开职业履历", people)
        self.assertIn("产品是否实际上线运营", business)
        self.assertIn("相同、近似商标线索", ip_data)
        self.assertIn("数据泄露或产品下架线索不能替代", ip_data)

        old_exclusive_rule = "自动外部企业信息核查仅使用共享 MCP 中的" + "快查企业能力"
        old_fallback_rule = "企业外部信息核查不得静默切换到 " + "WebSearch"
        self.assertNotIn(old_exclusive_rule, skill)
        self.assertNotIn(old_fallback_rule, skill)
        self.assertEqual(BUILDER.BRAND_DISCLOSURE, VALIDATOR.BRAND_DISCLOSURE)
        self.assertIn("有限补充核查", BUILDER.BRAND_DISCLOSURE)

    def test_external_sources_render_as_true_page_footnotes(self) -> None:
        self.data["business"] = [
            {
                "type": "paragraph",
                "text": "测试产品已在公司官网公开上线。",
                "external_sources": [
                    {
                        "source_name": "测试公司官网",
                        "title": "测试产品发布页",
                        "published_on": "2026-08-20",
                        "accessed_on": "2026-08-27",
                        "url": "https://example.com/product",
                    }
                ],
            }
        ]
        output, data_path = self.build(self.data, "external-footnote")
        with zipfile.ZipFile(output) as zf:
            self.assertIn("word/footnotes.xml", zf.namelist())
            document = etree.fromstring(zf.read("word/document.xml"))
            footnotes = etree.fromstring(zf.read("word/footnotes.xml"))
            refs = document.xpath(".//w:footnoteReference/@w:id", namespaces=NS)
            note_ids = footnotes.xpath("./w:footnote[number(@w:id) >= 1]/@w:id", namespaces=NS)
            note_text = "".join(footnotes.xpath(".//w:footnote[number(@w:id) >= 1]//w:t/text()", namespaces=NS))
            colors = footnotes.xpath(".//w:footnote[number(@w:id) >= 1]//w:color/@w:val", namespaces=NS)

        self.assertEqual(refs, note_ids)
        self.assertEqual(len(refs), 1)
        self.assertIn("来源：测试公司官网", note_text)
        self.assertIn("《测试产品发布页》", note_text)
        self.assertIn("发布日期：2026-08-20", note_text)
        self.assertIn("https://example.com/product", note_text)
        self.assertIn("访问日期：2026-08-27", note_text)
        self.assertTrue(colors)
        self.assertTrue(all(value == "000000" for value in colors))
        self.assertNotIn("LEGAL_DD_FN", document_text(output))
        result = VALIDATOR.report_result(output, data_path)
        self.assertTrue(result["ok"], result["errors"])


if __name__ == "__main__":
    unittest.main()
