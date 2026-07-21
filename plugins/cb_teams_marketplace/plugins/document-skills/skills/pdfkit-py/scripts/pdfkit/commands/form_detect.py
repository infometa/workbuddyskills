#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 表单检测工具。
检测 PDF 中的可填写表单字段和结构化表单元素。
"""

import os

COMMAND = "form_detect"
DESCRIPTION = "检测 PDF 中的可填写表单字段和结构化表单元素。"
CATEGORY = "security"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "extract_structure", "type": "bool", "required": False, "default": True, "help": "是否提取表单结构"},
]


def _get_full_annotation_field_id(annotation):
    """从注释对象中获取完整的字段 ID（含父级路径）。"""
    components = []
    a = annotation
    while a:
        field_name = a.get('/T')
        if field_name:
            components.append(field_name)
        a = a.get('/Parent')
    return ".".join(reversed(components)) if components else None


def _make_field_dict(field, field_id):
    """根据字段类型构建字段信息字典。"""
    field_dict = {"field_id": field_id}
    ft = field.get('/FT')

    if ft == "/Tx":
        field_dict["type"] = "text"
    elif ft == "/Btn":
        # 先标记为 checkbox，后续如果检测到 /Kids + /AP 会升级为 radio_group
        field_dict["type"] = "checkbox"
        states = field.get("/_States_", [])
        if len(states) == 2:
            if "/Off" in states:
                field_dict["checked_value"] = states[0] if states[0] != "/Off" else states[1]
                field_dict["unchecked_value"] = "/Off"
            else:
                field_dict["checked_value"] = states[0]
                field_dict["unchecked_value"] = states[1]
    elif ft == "/Ch":
        field_dict["type"] = "choice"
        states = field.get("/_States_", [])
        field_dict["choice_options"] = [
            {"value": s[0], "text": s[1]} if isinstance(s, (list, tuple)) and len(s) == 2
            else {"value": s, "text": s}
            for s in states
        ] if states else []
    else:
        field_dict["type"] = f"unknown ({ft})"

    return field_dict


def detect_fillable_fields(pdf_path):
    """检测 PDF 中的可填写表单字段。

    功能特性：
    - 正确区分 checkbox 和 radio_group（通过 /Kids + /AP/N 检测）
    - 提取 radio_options（每个选项的 value 和 rect）
    - 完善 choice_options 提取
    - 字段按页码和位置排序
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    if not fields:
        return False, []

    # 第一遍：构建字段信息，识别可能的 radio_group 父节点
    field_info_by_id = {}
    possible_radio_names = set()

    for field_id, field in fields.items():
        if field.get("/Kids"):
            # 有子节点的 /Btn 类型字段可能是 radio_group
            if field.get("/FT") == "/Btn":
                possible_radio_names.add(field_id)
            continue
        field_info_by_id[field_id] = _make_field_dict(field, field_id)

    # 第二遍：遍历页面注释，获取字段位置 + 识别 radio_group
    radio_fields_by_id = {}

    for page_index, page in enumerate(reader.pages):
        annotations = page.get('/Annots', [])
        for ann in annotations:
            field_id = _get_full_annotation_field_id(ann)

            if field_id in field_info_by_id:
                # 普通字段：记录页码和位置
                field_info_by_id[field_id]["page"] = page_index + 1
                rect = ann.get('/Rect')
                if rect:
                    field_info_by_id[field_id]["rect"] = [float(r) for r in rect]

            elif field_id in possible_radio_names:
                # Radio Group：从 /AP/N 中提取选项值
                try:
                    on_values = [v for v in ann["/AP"]["/N"] if v != "/Off"]
                except (KeyError, TypeError):
                    continue

                if len(on_values) == 1:
                    rect = ann.get("/Rect")
                    rect_floats = [float(r) for r in rect] if rect else None

                    if field_id not in radio_fields_by_id:
                        radio_fields_by_id[field_id] = {
                            "field_id": field_id,
                            "type": "radio_group",
                            "page": page_index + 1,
                            "radio_options": [],
                        }
                    radio_fields_by_id[field_id]["radio_options"].append({
                        "value": on_values[0],
                        "rect": rect_floats,
                    })

    # 合并结果：过滤无位置信息的字段
    fields_with_location = []
    for field_info in field_info_by_id.values():
        if "page" in field_info:
            fields_with_location.append(field_info)

    # 合并 radio_group 字段
    all_fields = fields_with_location + list(radio_fields_by_id.values())

    # 按页码和位置排序（从上到下、从左到右）
    def sort_key(f):
        if "radio_options" in f and f["radio_options"]:
            rect = f["radio_options"][0].get("rect") or [0, 0, 0, 0]
        else:
            rect = f.get("rect") or [0, 0, 0, 0]
        # 按页码、y 坐标降序（PDF 坐标系 y 轴向上）、x 坐标升序
        return [f.get("page", 0), -rect[1], rect[0]]

    all_fields.sort(key=sort_key)

    return True, all_fields


def detect_form_structure(pdf_path):
    """检测 PDF 中的表单结构（文字标签、线条、复选框）。"""
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber 未安装，无法提取表单结构", "labels": [], "lines": [], "checkboxes": []}

    structure = {
        "pages": [],
        "labels": [],
        "lines": [],
        "checkboxes": [],
        "row_boundaries": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            structure["pages"].append({
                "page_number": page_num,
                "width": float(page.width),
                "height": float(page.height)
            })

            # 提取文字标签
            words = page.extract_words()
            for word in words:
                structure["labels"].append({
                    "page": page_num,
                    "text": word["text"],
                    "x0": round(float(word["x0"]), 1),
                    "top": round(float(word["top"]), 1),
                    "x1": round(float(word["x1"]), 1),
                    "bottom": round(float(word["bottom"]), 1)
                })

            # 提取水平线
            for line in page.lines:
                if abs(float(line["x1"]) - float(line["x0"])) > page.width * 0.5:
                    structure["lines"].append({
                        "page": page_num,
                        "y": round(float(line["top"]), 1),
                        "x0": round(float(line["x0"]), 1),
                        "x1": round(float(line["x1"]), 1)
                    })

            # 检测复选框（小方形矩形）
            for rect in page.rects:
                width = float(rect["x1"]) - float(rect["x0"])
                height = float(rect["bottom"]) - float(rect["top"])
                if 5 <= width <= 15 and 5 <= height <= 15 and abs(width - height) < 2:
                    structure["checkboxes"].append({
                        "page": page_num,
                        "x0": round(float(rect["x0"]), 1),
                        "top": round(float(rect["top"]), 1),
                        "x1": round(float(rect["x1"]), 1),
                        "bottom": round(float(rect["bottom"]), 1),
                        "center_x": round((float(rect["x0"]) + float(rect["x1"])) / 2, 1),
                        "center_y": round((float(rect["top"]) + float(rect["bottom"])) / 2, 1)
                    })

    # 计算行边界
    lines_by_page = {}
    for line in structure["lines"]:
        page = line["page"]
        if page not in lines_by_page:
            lines_by_page[page] = []
        lines_by_page[page].append(line["y"])

    for page, y_coords in lines_by_page.items():
        y_coords = sorted(set(y_coords))
        for i in range(len(y_coords) - 1):
            structure["row_boundaries"].append({
                "page": page,
                "row_top": y_coords[i],
                "row_bottom": y_coords[i + 1],
                "row_height": round(y_coords[i + 1] - y_coords[i], 1)
            })

    return structure


def handler(params):
    """处理表单检测请求。

    Args:
        params: {
            "input": PDF 路径,
            "extract_structure": 是否提取表单结构（可选，默认 True）
        }
    """
    pdf_path = params["input"]
    extract_structure = params.get("extract_structure", True)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    # 检测可填写字段
    has_fillable, fillable_fields = detect_fillable_fields(pdf_path)

    # 检测表单结构
    form_structure = detect_form_structure(pdf_path) if extract_structure else {}

    result = {
        "has_fillable_fields": has_fillable,
        "fillable_field_count": len(fillable_fields),
        "fillable_fields": fillable_fields,
        "form_structure": {
            "page_count": len(form_structure.get("pages", [])),
            "label_count": len(form_structure.get("labels", [])),
            "line_count": len(form_structure.get("lines", [])),
            "checkbox_count": len(form_structure.get("checkboxes", [])),
        },
        "form_structure_detail": form_structure,
        "summary": ""
    }

    # 生成摘要
    if has_fillable:
        types = {}
        for f in fillable_fields:
            t = f.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        type_str = ", ".join(f"{v}个{k}" for k, v in types.items())
        result["summary"] = f"该 PDF 包含 {len(fillable_fields)} 个可填写表单字段（{type_str}）。"
        # 根据字段类型给出更精确的建议
        hints = []
        if "radio_group" in types:
            hints.append("radio_group 字段需使用 radio_options 中的 value 值填写")
        if "choice" in types:
            hints.append("choice 字段需使用 choice_options 中的 value 值填写")
        if "checkbox" in types:
            hints.append("checkbox 字段需使用 checked_value/unchecked_value 填写")
        if hints:
            result["summary"] += " 注意：" + "；".join(hints) + "。"
        result["summary"] += " 可使用 pdf_form_fill 工具填写。"
    else:
        label_count = len(form_structure.get("labels", []))
        checkbox_count = len(form_structure.get("checkboxes", []))
        if label_count > 0:
            result["summary"] = f"该 PDF 没有可填写字段，但检测到 {label_count} 个文字标签和 {checkbox_count} 个复选框。可使用 pdf_form_fill_annotation 工具通过注释方式填写。"
        else:
            result["summary"] = "该 PDF 没有可填写字段，也没有检测到表单结构。可能是扫描件，建议先用 pdf_to_images 转图片后视觉分析。"

    return result


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
