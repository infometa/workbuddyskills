#!/usr/bin/env python3
"""Hard-gate validator for final legal due-diligence Word reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency. Install requirements.txt before running this script.") from exc

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W, "r": R, "pr": PKG_REL}
EXTERNAL_SOURCE_CONTENT_KEYS = (
    "report_letter",
    "disclaimer",
    "basic",
    "history",
    "ownership",
    "governance",
    "business",
    "assets_ip",
    "employment",
    "compliance",
    "other_modules",
    "major_issues",
    "pending_items",
    "conclusion",
    "attachments",
)

BODY_HEADINGS = [
    "一、目标公司基本情况",
    "二、历史沿革",
    "三、股权结构、股东及实际控制人",
    "四、公司治理",
    "五、业务、资质及重大合同",
    "六、资产与知识产权",
    "七、劳动用工",
    "八、税务、诉讼、处罚及合规",
    "九、其他实际启用模块",
    "重大问题及风险提示",
    "待核实事项",
    "结论与建议",
    "附件或资料清单",
]
PROHIBITED = ("{{", "}}", "TODO", "示例", "含 AI 生成", "AI 生成", "按 F9", "更新目录")
BRAND_NAME = "同花顺旗下快查企业数据引擎"
BRAND_DISCLOSURE = (
    "本次公开信息核验以同花顺旗下快查企业数据引擎为主要渠道，并对官网、官方公示及可信公开报道"
    "进行有限补充核查；相关结果仅用于一致性复核和线索补充，不替代委托方提供并纳入当前采信范围的资料及原始证明。"
)
INTERNAL_PATTERNS = {
    "MCP": re.compile(r"\bMCP\b", re.IGNORECASE),
    "discover": re.compile(r"\bdiscover\b", re.IGNORECASE),
    "call": re.compile(r"\bcall\b", re.IGNORECASE),
    "tool_id": re.compile(r"\btool_id\b", re.IGNORECASE),
    "查询日志": re.compile(r"查询日志"),
    "分页完整性": re.compile(r"分页完整性"),
    "参数错误": re.compile(r"参数错误"),
    "权限错误": re.compile(r"权限错误"),
    "服务错误": re.compile(r"服务错误"),
    "快查接口": re.compile(r"快查(?:查询|变更记录)?接口"),
    "快查能力": re.compile(r"快查能力"),
    "内部工作材料": re.compile(r"内部工作材料"),
    "内部状态": re.compile(r"\b(?:EMPTY_RESULT|UNSUPPORTED|FAILED|INCOMPLETE)\b"),
    "查询未返回": re.compile(r"(?:快查)?查询未返回|未返回相关记录"),
}
HEADING_FONTS = {
    "Heading1": "黑体",
    "Heading2": "黑体",
    "Heading3": "楷体",
    "Heading4": "仿宋",
}
THEME_FONT_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")
GOTHIC_NAMES = ("MS GOTHIC", "ＭＳ ゴシック", "MS ゴシック")


def text_of(node) -> str:
    return "".join(node.xpath(".//w:t/text()", namespaces=NS)).strip()


def validate_source_control(data_path: Path, errors: list[str]) -> None:
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"无法读取报告数据：{exc}")
        return
    control = data.get("source_control")
    if not isinstance(control, dict):
        errors.append("报告数据缺少 source_control。")
        return
    basis = control.get("primary_basis")
    material_ids = control.get("primary_material_ids")
    if basis not in {"current_accepted_materials", "public_information_pre_dd"}:
        errors.append("source_control.primary_basis 值无效。")
    if not isinstance(material_ids, list):
        errors.append("source_control.primary_material_ids 必须为数组。")
    elif basis == "current_accepted_materials" and not any(str(value).strip() for value in material_ids):
        errors.append("当前采信资料模式缺少 primary_material_ids。")
    elif basis == "public_information_pre_dd" and material_ids:
        errors.append("公开信息 Pre-DD 模式不得填写 primary_material_ids。")
    if control.get("external_verification_role") != "corroboration_only":
        errors.append("external_verification_role 必须为 corroboration_only。")
    if control.get("brand_disclosure_required") is not True:
        errors.append("brand_disclosure_required 必须为 true。")
    if not isinstance(control.get("conflicts"), list):
        errors.append("source_control.conflicts 必须为数组。")


def expected_external_footnotes(value) -> int:
    if isinstance(value, list):
        return sum(expected_external_footnotes(item) for item in value)
    if not isinstance(value, dict):
        return 0
    total = 0
    for key, item in value.items():
        if key == "external_sources":
            if isinstance(item, list):
                total += len(item)
            continue
        total += expected_external_footnotes(item)
    return total


def report_result(path: Path, data_path: Path | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    expected_footnotes = 0
    if data_path is not None:
        validate_source_control(data_path, errors)
        try:
            report_data = json.loads(data_path.read_text(encoding="utf-8"))
            expected_footnotes = sum(
                expected_external_footnotes(report_data.get(key)) for key in EXTERNAL_SOURCE_CONTENT_KEYS
            )
        except (OSError, json.JSONDecodeError):
            pass
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        required_parts = {"word/document.xml", "word/styles.xml", "word/settings.xml"}
        missing_parts = sorted(required_parts - names)
        if missing_parts:
            errors.append("缺少必要 OOXML 部件：" + ", ".join(missing_parts))
            return {"ok": False, "errors": errors, "warnings": warnings}
        document = etree.fromstring(zf.read("word/document.xml"))
        styles = etree.fromstring(zf.read("word/styles.xml"))
        settings = etree.fromstring(zf.read("word/settings.xml"))
        full_text = "\n".join(text_of(p) for p in document.xpath(".//w:p", namespaces=NS))
        footnotes = etree.fromstring(zf.read("word/footnotes.xml")) if "word/footnotes.xml" in names else None
        footnote_text = ""
        if footnotes is not None:
            footnote_text = "\n".join(
                text_of(p)
                for p in footnotes.xpath(".//w:footnote[number(@w:id) >= 1]/w:p", namespaces=NS)
            )
        checked_text = full_text + ("\n" + footnote_text if footnote_text else "")

        for token in PROHIBITED:
            if token in checked_text:
                errors.append(f"残留禁止文本：{token}")
        for label, pattern in INTERNAL_PATTERNS.items():
            if pattern.search(checked_text):
                errors.append(f"残留内部技术信息：{label}")
        brand_count = full_text.count(BRAND_DISCLOSURE)
        if brand_count != 1:
            errors.append(f"快查品牌来源声明数量错误：检测到 {brand_count} 次，应为 1 次。")
        brand_stripped = full_text.replace(BRAND_DISCLOSURE, "")
        if "快查" in brand_stripped or BRAND_NAME in brand_stripped:
            errors.append("报告函来源声明之外仍出现快查品牌或快查作业语言。")
        brand_index = full_text.find(BRAND_DISCLOSURE)
        disclaimer_index = full_text.find("免责声明")
        if brand_index >= 0 and disclaimer_index >= 0 and brand_index > disclaimer_index:
            errors.append("快查品牌来源声明未位于报告函。")
        if "目录" in full_text and not any(x in full_text for x in ("附件或资料清单", "经营范围")):
            warnings.append("检测到“目录”文本，请确认其不是空目录页。")

        footnote_refs = [
            int(value)
            for value in document.xpath(".//w:footnoteReference/@w:id", namespaces=NS)
            if str(value).lstrip("-").isdigit() and int(value) >= 1
        ]
        note_ids = []
        if footnotes is not None:
            note_ids = [
                int(value)
                for value in footnotes.xpath("./w:footnote/@w:id", namespaces=NS)
                if str(value).lstrip("-").isdigit() and int(value) >= 1
            ]
        if expected_footnotes:
            if footnotes is None:
                errors.append("报告数据包含外部来源，但 DOCX 缺少原生脚注部件。")
            if len(footnote_refs) != expected_footnotes:
                errors.append(f"外部来源脚注引用数量错误：检测到 {len(footnote_refs)} 个，应为 {expected_footnotes} 个。")
            if sorted(footnote_refs) != sorted(note_ids):
                errors.append("正文脚注引用与 footnotes.xml 条目不一致。")
            if len(note_ids) != len(set(note_ids)):
                errors.append("footnotes.xml 存在重复脚注编号。")
            if footnote_text.count("来源：") != expected_footnotes:
                errors.append("外部来源脚注缺少标准溯源文本。")
        elif footnote_refs or note_ids:
            warnings.append("DOCX 包含脚注，但报告数据未声明 external_sources。")

        positions = []
        for heading in BODY_HEADINGS:
            index = full_text.find(heading)
            if index < 0:
                errors.append(f"缺少固定标题：{heading}")
            positions.append(index)
        valid_positions = [value for value in positions if value >= 0]
        if valid_positions != sorted(valid_positions):
            errors.append("固定正文和外层标题顺序错误。")
        for required in ("免责声明", "致：", "[本页为签署页，无正文]", "出具主体：", "负责人：", "经办律师："):
            if required not in full_text:
                errors.append(f"缺少必要报告构件：{required}")

        sections = document.xpath(".//w:sectPr", namespaces=NS)
        if len(sections) < 4:
            errors.append(f"分节不足：检测到 {len(sections)} 个，至少需要 4 个。")
        if sections:
            cover_refs = sections[0].xpath("./w:headerReference|./w:footerReference", namespaces=NS)
            if cover_refs:
                errors.append("封面分节仍引用页眉或页脚。")
        if len(sections) >= 2:
            starts = sections[1].xpath("./w:pgNumType/@w:start", namespaces=NS)
            if not starts or starts[0] != "1":
                errors.append("报告函/正文页码未从 1 开始。")

        field_text = " ".join(document.xpath(".//w:instrText/text()", namespaces=NS)).upper()
        for name in [n for n in names if re.fullmatch(r"word/footer\d+\.xml", n)]:
            field_text += " " + " ".join(etree.fromstring(zf.read(name)).xpath(".//w:instrText/text()", namespaces=NS)).upper()
        if "PAGE" not in field_text:
            errors.append("未检测到真实 PAGE 域。")
        if "NUMPAGES" in field_text:
            errors.append("检测到 NUMPAGES 域；本报告禁止 1/N 页码形式。")
        if "TOC" in field_text:
            errors.append("检测到 TOC 域；固定外层结构不包含自动目录。")
        if not settings.xpath(".//w:updateFields[@w:val='true' or @w:val='1']", namespaces=NS):
            errors.append("未设置打开文档时更新域。")

        style_names = {node.get(f"{{{W}}}styleId") for node in styles.xpath(".//w:style", namespaces=NS)}
        for style_id in ("Heading1", "Heading2", "Heading3", "Heading4"):
            if style_id not in style_names:
                errors.append(f"缺少命名样式：{style_id}")
        for style_id, expected_font in HEADING_FONTS.items():
            for candidate in (style_id, f"{style_id}Char"):
                nodes = styles.xpath(f".//w:style[@w:styleId='{candidate}']", namespaces=NS)
                if not nodes:
                    continue
                rfonts = nodes[0].xpath("./w:rPr/w:rFonts", namespaces=NS)
                if not rfonts:
                    errors.append(f"标题样式 {candidate} 缺少显式字体。")
                    continue
                node = rfonts[0]
                if any(node.get(f"{{{W}}}{attr}") for attr in THEME_FONT_ATTRS):
                    errors.append(f"标题样式 {candidate} 仍引用主题字体。")
                east_asia = node.get(f"{{{W}}}eastAsia", "")
                ascii_font = node.get(f"{{{W}}}ascii", "")
                hansi_font = node.get(f"{{{W}}}hAnsi", "")
                if east_asia != expected_font or ascii_font != "Times New Roman" or hansi_font != "Times New Roman":
                    errors.append(f"标题样式 {candidate} 字体不符合规定。")
                upper_fonts = " ".join(node.attrib.values()).upper()
                if any(name.upper() in upper_fonts for name in GOTHIC_NAMES):
                    errors.append(f"标题样式 {candidate} 使用 MS Gothic。")
                langs = nodes[0].xpath("./w:rPr/w:lang/@w:eastAsia", namespaces=NS)
                if not langs or langs[0].lower() != "zh-cn":
                    errors.append(f"标题样式 {candidate} 未设置东亚语言 zh-CN。")
        used_heading_styles = document.xpath(".//w:pStyle[starts-with(@w:val,'Heading')]/@w:val", namespaces=NS)
        if not used_heading_styles:
            errors.append("正文标题未使用 Heading 命名样式。")
        for paragraph in document.xpath(".//w:p[w:pPr/w:pStyle[starts-with(@w:val,'Heading')]]", namespaces=NS):
            style_id = (paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS) or [""])[0]
            expected_font = HEADING_FONTS.get(style_id)
            if expected_font is None:
                continue
            for rfonts in paragraph.xpath("./w:r/w:rPr/w:rFonts", namespaces=NS):
                if any(rfonts.get(f"{{{W}}}{attr}") for attr in THEME_FONT_ATTRS):
                    errors.append(f"标题段落 {text_of(paragraph)[:30]} 仍引用主题字体。")
                    break
                east_asia = rfonts.get(f"{{{W}}}eastAsia")
                if east_asia and east_asia != expected_font:
                    errors.append(f"标题段落 {text_of(paragraph)[:30]} 使用了错误中文字体。")
                    break
                upper_fonts = " ".join(rfonts.attrib.values()).upper()
                if any(name.upper() in upper_fonts for name in GOTHIC_NAMES):
                    errors.append(f"标题段落 {text_of(paragraph)[:30]} 使用 MS Gothic。")
                    break

        used_style_ids = set(
            document.xpath(
                ".//w:pStyle/@w:val | .//w:rStyle/@w:val | .//w:tblStyle/@w:val",
                namespaces=NS,
            )
        )
        style_nodes = []
        pending_style_ids = list(used_style_ids)
        while pending_style_ids:
            style_id = pending_style_ids.pop()
            matches = styles.xpath(f".//w:style[@w:styleId='{style_id}']", namespaces=NS)
            if not matches:
                continue
            style = matches[0]
            if style in style_nodes:
                continue
            style_nodes.append(style)
            pending_style_ids.extend(style.xpath("./w:basedOn/@w:val", namespaces=NS))

        color_nodes = document.xpath(".//w:color[@w:val]", namespaces=NS)
        shading_nodes = document.xpath(".//w:shd[@w:fill]", namespaces=NS)
        if footnotes is not None:
            color_nodes.extend(footnotes.xpath(".//w:color[@w:val]", namespaces=NS))
            shading_nodes.extend(footnotes.xpath(".//w:shd[@w:fill]", namespaces=NS))
        for style in style_nodes:
            color_nodes.extend(style.xpath(".//w:color[@w:val]", namespaces=NS))
            shading_nodes.extend(style.xpath(".//w:shd[@w:fill]", namespaces=NS))

        for node in color_nodes:
            value = node.get(f"{{{W}}}val", "").upper()
            if value not in ("000000", "AUTO"):
                errors.append(f"检测到非黑色文字：{value}")
                break
        for node in shading_nodes:
            value = node.get(f"{{{W}}}fill", "").upper()
            if value not in ("", "AUTO", "FFFFFF"):
                errors.append(f"检测到非白色底纹：{value}")
                break

        tables = document.xpath(".//w:tbl", namespaces=NS)
        for index, table in enumerate(tables, 1):
            tbl_w = table.xpath("./w:tblPr/w:tblW", namespaces=NS)
            if not tbl_w or tbl_w[0].get(f"{{{W}}}type") != "dxa":
                errors.append(f"表格 {index} 未使用显式 DXA 总宽度。")
            grid_cols = table.xpath("./w:tblGrid/w:gridCol", namespaces=NS)
            if not grid_cols:
                errors.append(f"表格 {index} 缺少 tblGrid。")
            if table.xpath(".//w:trHeight[@w:hRule='exact']", namespaces=NS):
                errors.append(f"表格 {index} 使用了固定行高。")
            if not table.xpath("./w:tr[1]/w:trPr/w:tblHeader", namespaces=NS):
                errors.append(f"表格 {index} 未设置重复表头。")

        if "word/comments.xml" in names:
            errors.append("报告仍包含批注。")
        if document.xpath(".//w:ins|.//w:del|.//w:moveFrom|.//w:moveTo", namespaces=NS):
            errors.append("报告仍包含修订记录。")
        if any(name.startswith("word/media/") for name in names):
            warnings.append("报告包含媒体文件，请确认不存在 Logo 或品牌图形。")
        for name in [n for n in names if n.endswith(".rels")]:
            rels = etree.fromstring(zf.read(name))
            if rels.xpath(".//pr:Relationship[@TargetMode='External']", namespaces=NS):
                errors.append(f"检测到外部关系：{name}")

    return {
        "ok": not errors,
        "path": str(path),
        "sections": len(sections),
        "tables": len(tables),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    if not args.docx.exists():
        raise SystemExit(f"DOCX not found: {args.docx}")
    result = report_result(args.docx, args.data)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
