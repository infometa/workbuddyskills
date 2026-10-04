#!/usr/bin/env python3
"""Check deterministic heading-format rules for a final legal-opinion DOCX."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
Q = lambda name: f"{{{W}}}{name}"
CHAPTER_RE = re.compile(r"^([一二三四五六七八九十百]+)、")


def w_attr(node, name):
    return None if node is None else node.get(Q(name))


def style_info(styles_root):
    result = {}
    for style in styles_root.xpath("//w:style", namespaces=NS):
        sid = w_attr(style, "styleId")
        result[sid] = {
            "name": w_attr(style.find("w:name", NS), "val") or "",
            "based_on": w_attr(style.find("w:basedOn", NS), "val"),
            "rpr": style.find("w:rPr", NS),
            "ppr": style.find("w:pPr", NS),
        }
    return result


def chain(styles, sid):
    seen = set()
    while sid and sid not in seen and sid in styles:
        seen.add(sid)
        yield styles[sid]
        sid = styles[sid]["based_on"]


def first_property(nodes, path, attr="val"):
    for node in nodes:
        if node is None:
            continue
        found = node.find(path, NS)
        if found is not None:
            return w_attr(found, attr)
    return None


def bool_property(nodes, path):
    value = first_property(nodes, path)
    if value is None:
        for node in nodes:
            if node is not None and node.find(path, NS) is not None:
                return True
        return False
    return value not in {"0", "false", "off"}


def effective_run_signature(run, paragraph, styles, sid, defaults_rpr):
    direct = run.find("w:rPr", NS)
    paragraph_rpr = paragraph.find("w:pPr/w:rPr", NS)
    style_rprs = [item["rpr"] for item in chain(styles, sid)]
    nodes = [direct, paragraph_rpr, *style_rprs, defaults_rpr]
    font_nodes = []
    for node in nodes:
        font_nodes.append(node.find("w:rFonts", NS) if node is not None else None)
    east_asia = first_property(font_nodes, ".", "eastAsia")
    ascii_font = first_property(font_nodes, ".", "ascii")
    size = first_property(nodes, "w:sz")
    color = first_property(nodes, "w:color") or "000000"
    return (east_asia or ascii_font, size, bool_property(nodes, "w:b"), color.upper())


def effective_paragraph_signature(paragraph, styles, sid, defaults_ppr):
    direct = paragraph.find("w:pPr", NS)
    style_pprs = [item["ppr"] for item in chain(styles, sid)]
    nodes = [direct, *style_pprs, defaults_ppr]
    return (
        first_property(nodes, "w:jc") or "left",
        first_property(nodes, "w:spacing", "before") or "0",
        first_property(nodes, "w:spacing", "after") or "0",
        first_property(nodes, "w:spacing", "line"),
        first_property(nodes, "w:spacing", "lineRule"),
        first_property(nodes, "w:ind", "left") or "0",
        first_property(nodes, "w:ind", "firstLine") or "0",
        first_property(nodes, "w:ind", "hanging") or "0",
        bool_property(nodes, "w:keepNext"),
        bool_property(nodes, "w:keepLines"),
        bool_property(nodes, "w:pageBreakBefore"),
    )


def chinese_number(text):
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if text == "十":
        return 10
    if "十" in text:
        left, right = text.split("十", 1)
        return (digits.get(left, 1) * 10) + digits.get(right, 0)
    return digits.get(text)


def check(path: Path):
    issues = []
    try:
        with ZipFile(path) as zf:
            document = etree.fromstring(zf.read("word/document.xml"))
            styles_root = etree.fromstring(zf.read("word/styles.xml"))
    except (BadZipFile, KeyError, etree.XMLSyntaxError) as exc:
        return [f"无法读取 DOCX 结构：{exc}"]

    styles = style_info(styles_root)
    defaults_rpr = styles_root.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
    defaults_ppr = styles_root.find("w:docDefaults/w:pPrDefault/w:pPr", NS)
    chapters = []
    paragraph_signatures = {1: [], 2: []}

    for index, paragraph in enumerate(document.xpath("//w:body//w:p", namespaces=NS), start=1):
        sid = w_attr(paragraph.find("w:pPr/w:pStyle", NS), "val")
        style_name = styles.get(sid, {}).get("name", "").lower()
        if style_name not in {"heading 1", "heading 2", "标题 1", "标题 2"}:
            continue
        level = 1 if style_name in {"heading 1", "标题 1"} else 2
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()
        label = text or f"第 {index} 段"
        expected_size = "32" if level == 1 else "28"
        expected_prefix = CHAPTER_RE if level == 1 else re.compile(r"^（[一二三四五六七八九十百]+）")

        if paragraph.find("w:pPr/w:numPr", NS) is not None:
            issues.append(f"{label}：标题不得保留 Word 自动编号 numPr")
        if not expected_prefix.match(text):
            issues.append(f"{label}：{level} 级标题编号格式不符合统一规范")
        if level == 1:
            match = CHAPTER_RE.match(text)
            if match:
                chapters.append((label, chinese_number(match.group(1))))

        alignment = w_attr(paragraph.find("w:pPr/w:jc", NS), "val")
        if alignment not in {None, "left", "start"}:
            issues.append(f"{label}：标题必须左对齐，当前为 {alignment}")
        paragraph_signatures[level].append(
            (label, effective_paragraph_signature(paragraph, styles, sid, defaults_ppr))
        )

        signatures = []
        for run in paragraph.xpath("./w:r", namespaces=NS):
            if not "".join(run.xpath(".//w:t/text()", namespaces=NS)).strip():
                continue
            rpr = run.find("w:rPr", NS)
            if rpr is not None and any(rpr.find(tag, NS) is not None for tag in ("w:sz", "w:szCs", "w:b", "w:bCs", "w:i", "w:iCs", "w:color")):
                issues.append(f"{label}：标题存在直接字号、粗体、斜体或颜色覆盖，应只使用标题样式")
            signature = effective_run_signature(run, paragraph, styles, sid, defaults_rpr)
            signatures.append(signature)
            font, size, bold, color = signature
            if font != "楷体" or size != expected_size or not bold or color not in {"000000", "AUTO"}:
                issues.append(
                    f"{label}：有效格式应为楷体 {int(expected_size) / 2:g} 磅加粗黑色，"
                    f"当前为 font={font!r}, size={size!r}, bold={bold}, color={color!r}"
                )
        if signatures and len(set(signatures)) != 1:
            issues.append(f"{label}：同一标题内部存在混合字体格式")

    numbers = [number for _, number in chapters]
    if any(number is None for number in numbers):
        issues.append("一级章节包含无法解析的中文编号")
    elif numbers and numbers != list(range(1, len(numbers) + 1)):
        issues.append(f"一级章节编号不连续或顺序错误：{numbers}")
    if not chapters:
        issues.append("未识别到使用 Heading 1 的一级章节标题")
    for level, entries in paragraph_signatures.items():
        if not entries:
            continue
        baseline = entries[0][1]
        for label, signature in entries[1:]:
            if signature != baseline:
                issues.append(f"{label}：与其他 {level} 级标题的段落间距、缩进或分页控制不一致")
    return issues


def main():
    if len(sys.argv) != 2:
        print("用法：check_opinion_format.py <最终法律意见书.docx>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"文件不存在：{path}", file=sys.stderr)
        return 2
    issues = check(path)
    if issues:
        print("FORMAT CHECK FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("FORMAT CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
