#!/usr/bin/env python3
"""Validate the structural safety of an editable MAI transaction SVG.

Usage: svg_validate.py <diagram.svg> [more.svg]
Exit codes: 0=all valid, 1=one or more invalid SVG files, 2=input error.
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


URL_REF = re.compile(r"url\(\s*#([^)\s]+)\s*\)")
URL_VALUE = re.compile(r"url\(\s*['\"]?([^)'\"\s]+)", re.I)
HREF_KEYS = {"href", "{http://www.w3.org/1999/xlink}href"}
ACTIVE_TAGS = {"script", "foreignObject", "iframe", "object", "embed"}
GEOMETRY_TAGS = {"rect", "ellipse", "circle", "line", "path", "polyline", "polygon"}


class InputError(Exception):
    """The SVG input was not available for validation."""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_svg(path: Path) -> list[str]:
    if not path.is_file():
        raise InputError(f"文件不存在或不是普通文件: {path}")
    try:
        root = ET.parse(path).getroot()
    except OSError as exc:
        raise InputError(f"无法读取文件: {exc}") from exc
    except ET.ParseError as exc:
        return [f"XML 无法解析: {exc}"]

    issues = []
    if local_name(root.tag) != "svg":
        issues.append("根元素必须是 svg")

    raw_view_box = root.attrib.get("viewBox", "")
    try:
        view_box = [float(value) for value in raw_view_box.replace(",", " ").split()]
    except ValueError:
        view_box = []
    if len(view_box) != 4 or view_box[2] <= 0 or view_box[3] <= 0:
        issues.append("viewBox 必须包含四个数字，且宽度和高度大于零")

    elements = list(root.iter())
    names = [local_name(element.tag) for element in elements]
    ids = [element.attrib["id"] for element in elements if element.attrib.get("id")]
    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        issues.append(f"存在重复 id: {', '.join(duplicates)}")

    if any(local_name(element.tag) == "style" for element in elements):
        issues.append("样式必须使用 inline 属性，不能使用 style 区块")
    if any("class" in element.attrib for element in elements):
        issues.append("样式必须使用 inline 属性，不能依赖 class")
    if any(name in ACTIVE_TAGS for name in names):
        issues.append("不允许 script、foreignObject 等活动内容")
    if not any(name in GEOMETRY_TAGS for name in names):
        issues.append("交易结构图至少需要一个图形元素")
    if not any(name == "text" and "".join(element.itertext()).strip() for name, element in zip(names, elements)):
        issues.append("交易结构图至少需要一个非空文字标签")

    for element in elements:
        name = local_name(element.tag)
        if name == "image":
            issues.append("不允许 image 外部资源；图必须保持纯 SVG 元素")
        for key, value in element.attrib.items():
            if local_name(key).lower().startswith("on"):
                issues.append(f"不允许事件属性: {local_name(key)}")
            if key in HREF_KEYS and value and not value.startswith("#"):
                issues.append(f"不允许外部资源: {value}")
            for target in URL_VALUE.findall(value):
                if not target.startswith("#"):
                    issues.append(f"不允许外部资源: {target}")

    id_set = set(ids)
    references = []
    for element in elements:
        for value in element.attrib.values():
            references.extend(URL_REF.findall(value))
    missing = sorted(set(references) - id_set)
    if missing:
        issues.append(f"引用了不存在的 id: {', '.join(missing)}")

    return issues


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        print(__doc__)
        return 2

    invalid = 0
    unverified = 0
    for raw_path in args:
        path = Path(raw_path)
        try:
            issues = validate_svg(path)
        except InputError as exc:
            unverified += 1
            print(f"[UNVERIFIED] {path.name}: 未完成校验: {exc}")
            continue
        if issues:
            invalid += 1
            print(f"[FAIL] {path.name}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[OK] {path.name}: SVG 结构校验通过")
    if unverified:
        return 2
    return 1 if invalid else 0


if __name__ == "__main__":
    sys.exit(main())
