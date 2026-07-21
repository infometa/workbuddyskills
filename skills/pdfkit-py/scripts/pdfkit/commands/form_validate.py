#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 表单验证工具。
独立的表单字段验证工具，支持边界框交叉检测、高度验证和视觉验证图片生成。

支持边界框交叉检测、高度验证和视觉验证图片生成。
"""

import json
import os

COMMAND = "form_validate"
DESCRIPTION = "验证表单字段的边界框和坐标，可生成视觉验证图片。"
CATEGORY = "security"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "form_fields", "type": "json", "required": True, "help": "表单字段列表 JSON"},
    {"name": "output_image", "type": "str", "required": False, "help": "验证图片输出路径（可选）"},
    {"name": "page", "type": "int", "required": False, "help": "验证的页码（从 1 开始，可选）"},
    {"name": "coordinate_type", "type": "str", "required": False, "default": "pdf", "choices": ["pdf", "image"], "help": "坐标类型"},
]


def validate_bounding_boxes(form_fields, max_errors=20):
    """验证边界框是否有交叉或高度不足。

    检测规则：
    - 检测 label 和 entry 边界框是否交叉（同一字段内 + 不同字段间）
    - 检测 entry 框高度是否小于字号
    - 检测同页不同字段的边界框是否重叠
    - 限制最大错误数量，避免输出过多

    Args:
        form_fields: 表单字段列表
        max_errors: 最大错误数量

    Returns:
        (is_valid, messages) 元组
    """
    messages = []
    messages.append(f"检查 {len(form_fields)} 个字段的边界框")

    def rects_intersect(r1, r2):
        """检测两个矩形是否相交。"""
        disjoint_horizontal = r1[0] >= r2[2] or r1[2] <= r2[0]
        disjoint_vertical = r1[1] >= r2[3] or r1[3] <= r2[1]
        return not (disjoint_horizontal or disjoint_vertical)

    # 收集所有矩形
    rects_and_fields = []
    for f in form_fields:
        if "label_bounding_box" in f:
            rects_and_fields.append({
                "rect": f["label_bounding_box"],
                "rect_type": "label",
                "field": f
            })
        if "entry_bounding_box" in f:
            rects_and_fields.append({
                "rect": f["entry_bounding_box"],
                "rect_type": "entry",
                "field": f
            })

    has_error = False
    error_count = 0

    # 检测矩形交叉
    for i, ri in enumerate(rects_and_fields):
        for j in range(i + 1, len(rects_and_fields)):
            rj = rects_and_fields[j]
            if ri["field"].get("page_number") == rj["field"].get("page_number") and rects_intersect(ri["rect"], rj["rect"]):
                has_error = True
                error_count += 1

                if ri["field"] is rj["field"]:
                    # 同一字段的 label 和 entry 交叉
                    messages.append(
                        f"❌ 字段 \"{ri['field'].get('description', '?')}\" 的 label 和 entry 边界框交叉 "
                        f"({ri['rect']}, {rj['rect']})"
                    )
                else:
                    # 不同字段的边界框交叉
                    messages.append(
                        f"❌ \"{ri['field'].get('description', '?')}\" 的 {ri['rect_type']} 边界框 ({ri['rect']}) "
                        f"与 \"{rj['field'].get('description', '?')}\" 的 {rj['rect_type']} 边界框 ({rj['rect']}) 交叉"
                    )

                if error_count >= max_errors:
                    messages.append("⚠️ 错误过多，中止检查。请先修复以上问题后重试。")
                    return False, messages

        # 检测 entry 框高度是否足够
        if ri["rect_type"] == "entry" and "entry_text" in ri["field"]:
            font_size = ri["field"]["entry_text"].get("font_size", 14)
            entry_height = ri["rect"][3] - ri["rect"][1]
            if entry_height < font_size:
                has_error = True
                error_count += 1
                messages.append(
                    f"❌ 字段 \"{ri['field'].get('description', '?')}\" 的 entry 框高度 ({entry_height:.1f}) "
                    f"小于字号 ({font_size})，文字将溢出。请增大框高度或减小字号。"
                )
                if error_count >= max_errors:
                    messages.append("⚠️ 错误过多，中止检查。请先修复以上问题后重试。")
                    return False, messages

    if not has_error:
        messages.append("✅ 所有边界框验证通过")

    return not has_error, messages


def create_validation_image(pdf_path, form_fields, page_number, output_path, dpi=150):
    """生成视觉验证图片，在 PDF 页面图片上标注边界框。

    标注规则：
    - 红框标注 entry 区域
    - 蓝框标注 label 区域
    - 绿色文字标注字段描述

    Args:
        pdf_path: PDF 文件路径
        form_fields: 表单字段列表
        page_number: 页码（从 1 开始）
        output_path: 输出图片路径
        dpi: 渲染分辨率

    Returns:
        标注的边界框数量
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("需要 PyMuPDF (fitz) 来生成验证图片。请运行: pip install PyMuPDF")

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("需要 Pillow 来生成验证图片。请运行: pip install Pillow")

    # 将 PDF 页面渲染为图片
    doc = fitz.open(pdf_path)
    page_idx = page_number - 1
    if page_idx < 0 or page_idx >= len(doc):
        raise ValueError(f"页码 {page_number} 超出范围（共 {len(doc)} 页）")

    page = doc[page_idx]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # 转为 PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    draw = ImageDraw.Draw(img)

    # 计算坐标缩放比例（PDF 坐标 → 图片像素）
    pdf_width = page.rect.width
    pdf_height = page.rect.height
    x_scale = pix.width / pdf_width
    y_scale = pix.height / pdf_height

    num_boxes = 0
    for field in form_fields:
        if field.get("page_number") != page_number:
            continue

        # 标注 entry 边界框（红色）
        if "entry_bounding_box" in field:
            bbox = field["entry_bounding_box"]
            # PDF 坐标转图片坐标（PDF y 轴向上，图片 y 轴向下）
            img_bbox = [
                bbox[0] * x_scale,
                bbox[1] * y_scale,
                bbox[2] * x_scale,
                bbox[3] * y_scale,
            ]
            draw.rectangle(img_bbox, outline='red', width=2)
            num_boxes += 1

        # 标注 label 边界框（蓝色）
        if "label_bounding_box" in field:
            bbox = field["label_bounding_box"]
            img_bbox = [
                bbox[0] * x_scale,
                bbox[1] * y_scale,
                bbox[2] * x_scale,
                bbox[3] * y_scale,
            ]
            draw.rectangle(img_bbox, outline='blue', width=2)
            num_boxes += 1

        # 标注字段描述（绿色文字）
        desc = field.get("description", "")
        if desc and "entry_bounding_box" in field:
            bbox = field["entry_bounding_box"]
            text_x = bbox[0] * x_scale
            text_y = bbox[1] * y_scale - 12
            try:
                draw.text((text_x, max(0, text_y)), desc, fill='green')
            except Exception:
                pass

    doc.close()

    # 保存验证图片
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    img.save(output_path)

    return num_boxes


def handler(params):
    """处理表单验证请求。

    Args:
        params: {
            "input": PDF 路径,
            "form_fields": 表单字段列表,
            "output_image": 验证图片输出路径（可选）,
            "page": 验证的页码（可选）,
            "coordinate_type": 坐标类型（可选）
        }
    """
    pdf_path = params["input"]
    form_fields = params.get("form_fields", [])

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    if not form_fields:
        raise ValueError("'form_fields' 不能为空")

    # 如果 form_fields 是字符串（JSON 文件路径），读取它
    if isinstance(form_fields, str):
        with open(form_fields, "r", encoding="utf-8") as f:
            form_fields = json.load(f)
            if isinstance(form_fields, dict) and "form_fields" in form_fields:
                form_fields = form_fields["form_fields"]

    # 1. 边界框验证
    is_valid, messages = validate_bounding_boxes(form_fields)

    result = {
        "is_valid": is_valid,
        "messages": messages,
        "field_count": len(form_fields),
    }

    # 2. 生成视觉验证图片（如果指定了输出路径）
    output_image = params.get("output_image")
    if output_image:
        page = params.get("page")
        if page is None:
            # 自动取第一个字段的页码
            pages = set(f.get("page_number", 1) for f in form_fields)
            page = min(pages) if pages else 1

        try:
            num_boxes = create_validation_image(pdf_path, form_fields, page, output_image)
            result["validation_image"] = output_image
            result["validation_image_boxes"] = num_boxes
            result["messages"].append(f"📷 已生成验证图片: {output_image}（标注了 {num_boxes} 个边界框）")
        except Exception as e:
            result["validation_image_error"] = str(e)
            result["messages"].append(f"⚠️ 生成验证图片失败: {e}")

    return result


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
