#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 表单注释填写工具（不可填写字段）。
通过 FreeText 注释方式填写没有可填写字段的 PDF 表单。

增强功能：
- 集成 form_validate 进行填写前验证
- 支持裁剪区域辅助定位（crop_region 参数）
- 填写后自动生成验证图片（validate_output 参数）
- 自动推断页面尺寸（无需手动提供 pages 参数）
"""

import os

COMMAND = "form_fill_annotation"
DESCRIPTION = "通过 FreeText 注释方式填写没有可填写字段的 PDF 表单。"
CATEGORY = "security"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "coordinate_type", "type": "str", "required": False, "default": "pdf", "choices": ["pdf", "image"], "help": "坐标类型：pdf=PDF原生坐标(y=0在底部)，image=图片坐标(y=0在顶部)。注意：此命令的 pdf 坐标与其他命令不同，其他命令统一使用 PyMuPDF 坐标系(y=0在顶部)"},
    {"name": "pages", "type": "json", "required": False, "help": "页面信息列表"},
    {"name": "form_fields", "type": "json", "required": False, "help": "表单字段列表（填写模式必填，crop_region 模式可省略）"},
    {"name": "validate_output", "type": "str", "required": False, "help": "填写后验证图片输出路径（可选）"},
    {"name": "crop_region", "type": "json", "required": False, "help": "裁剪区域辅助定位 {page, bbox, output, dpi}（可选，bbox 使用 PyMuPDF 坐标系）"},
    {"name": "skip_validation", "type": "bool", "required": False, "default": False, "help": "跳过边界框验证"},
]


def transform_from_image_coords(bbox, image_width, image_height, pdf_width, pdf_height):
    """将图片坐标转换为 PDF 坐标。"""
    x_scale = pdf_width / image_width
    y_scale = pdf_height / image_height
    left = bbox[0] * x_scale
    right = bbox[2] * x_scale
    top = pdf_height - (bbox[1] * y_scale)
    bottom = pdf_height - (bbox[3] * y_scale)
    return left, bottom, right, top


def transform_from_pdf_coords(bbox, pdf_height):
    """将 PDF 坐标转换为 pypdf 注释坐标。"""
    left = bbox[0]
    right = bbox[2]
    pypdf_top = pdf_height - bbox[1]
    pypdf_bottom = pdf_height - bbox[3]
    return left, pypdf_bottom, right, pypdf_top


def _get_pdf_dimensions(pdf_path):
    """获取 PDF 每页的尺寸信息。"""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    dimensions = {}
    for i, page in enumerate(reader.pages):
        mediabox = page.mediabox
        dimensions[i + 1] = [float(mediabox.width), float(mediabox.height)]
    return dimensions


def _crop_region_to_image(pdf_path, page, bbox, output, dpi=300):
    """裁剪 PDF 局部区域为高清图片，辅助精确定位坐标。

    Args:
        pdf_path: PDF 文件路径
        page: 页码（从 1 开始）
        bbox: 裁剪区域 [left, top, right, bottom]（PDF 坐标）
        output: 输出图片路径
        dpi: 渲染分辨率（默认 300，高清）

    Returns:
        裁剪信息字典
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("需要 PyMuPDF (fitz) 来裁剪区域。请运行: pip install PyMuPDF")

    doc = fitz.open(pdf_path)
    page_obj = doc[page - 1]

    # 裁剪区域（PDF 坐标）
    clip = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page_obj.get_pixmap(matrix=mat, clip=clip)

    output_dir = os.path.dirname(output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    pix.save(output)
    doc.close()

    return {
        "output": output,
        "page": page,
        "crop_bbox": bbox,
        "image_width": pix.width,
        "image_height": pix.height,
        "dpi": dpi,
        "hint": (
            f"裁剪图片已保存到 {output}。"
            f"在裁剪图中定位坐标后，换算回全页坐标："
            f"full_x = crop_x * {(bbox[2]-bbox[0])/pix.width:.4f} + {bbox[0]}, "
            f"full_y = crop_y * {(bbox[3]-bbox[1])/pix.height:.4f} + {bbox[1]}"
        )
    }


def fill_pdf_form_annotation(input_pdf_path, fields_data, output_pdf_path, skip_validation=False):
    """通过 FreeText 注释方式填写 PDF 表单。

    增强功能：
    - 集成 form_validate 进行填写前验证
    - 自动推断页面尺寸
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import FreeText

    # 使用 form_validate 进行验证（如果未跳过）
    if not skip_validation:
        from pdfkit.commands.form_validate import validate_bounding_boxes
        is_valid, messages = validate_bounding_boxes(fields_data.get("form_fields", []))
        if not is_valid:
            return {"success": False, "errors": messages}

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    # 获取 PDF 页面尺寸
    pdf_dimensions = {}
    for i, page in enumerate(reader.pages):
        mediabox = page.mediabox
        pdf_dimensions[i + 1] = [float(mediabox.width), float(mediabox.height)]

    # 构建页面信息索引
    pages_info = {}
    for p in fields_data.get("pages", []):
        pages_info[p["page_number"]] = p

    annotation_count = 0
    for field in fields_data["form_fields"]:
        page_num = field["page_number"]
        pdf_width, pdf_height = pdf_dimensions.get(page_num, [612, 792])

        # 获取页面信息（如果提供了）
        page_info = pages_info.get(page_num, {})

        # 坐标转换
        if "pdf_width" in page_info:
            transformed = transform_from_pdf_coords(field["entry_bounding_box"], pdf_height)
        elif "image_width" in page_info:
            transformed = transform_from_image_coords(
                field["entry_bounding_box"],
                page_info["image_width"], page_info["image_height"],
                pdf_width, pdf_height
            )
        else:
            # 默认使用 PDF 坐标
            transformed = transform_from_pdf_coords(field["entry_bounding_box"], pdf_height)

        if "entry_text" not in field or "text" not in field["entry_text"]:
            continue

        entry_text = field["entry_text"]
        text = entry_text["text"]
        if not text:
            continue

        font_name = entry_text.get("font", "Arial")
        font_size = str(entry_text.get("font_size", 14)) + "pt"
        font_color = entry_text.get("font_color", "000000")

        annotation = FreeText(
            text=text,
            rect=transformed,
            font=font_name,
            font_size=font_size,
            font_color=font_color,
            border_color=None,
            background_color=None,
        )
        writer.add_annotation(page_number=page_num - 1, annotation=annotation)
        annotation_count += 1

    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "annotation_count": annotation_count,
        "output": output_pdf_path
    }


def handler(params):
    """处理注释方式填写表单请求。

    Args:
        params: {
            "input": PDF 路径,
            "output": 输出 PDF 路径,
            "coordinate_type": 坐标类型（可选，"pdf" 或 "image"）,
            "pages": 页面信息列表,
            "form_fields": 表单字段列表,
            "validate_output": 填写后验证图片输出路径（可选）,
            "crop_region": 裁剪区域辅助定位（可选）,
            "skip_validation": 跳过边界框验证（可选）
        }
    """
    input_path = params["input"]
    output_path = params["output"]

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 裁剪区域辅助定位（如果指定了 crop_region，只做裁剪不做填写）
    crop_region = params.get("crop_region")
    if crop_region:
        return _crop_region_to_image(
            input_path,
            crop_region["page"],
            crop_region["bbox"],
            crop_region["output"],
            crop_region.get("dpi", 300)
        )

    if "form_fields" not in params:
        raise ValueError("'form_fields' 不能为空")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 构建 fields_data 结构
    fields_data = {
        "pages": params.get("pages", []),
        "form_fields": params["form_fields"],
    }

    skip_validation = params.get("skip_validation", False)
    result = fill_pdf_form_annotation(input_path, fields_data, output_path, skip_validation)

    # 填写后生成验证图片（如果指定了 validate_output）
    validate_output = params.get("validate_output")
    if validate_output and result.get("success"):
        try:
            from pdfkit.commands.form_validate import create_validation_image
            pages = set(f.get("page_number", 1) for f in params["form_fields"])
            page = min(pages) if pages else 1
            num_boxes = create_validation_image(output_path, params["form_fields"], page, validate_output)
            result["validation_image"] = validate_output
            result["validation_image_boxes"] = num_boxes
        except Exception as e:
            result["validation_image_error"] = str(e)

    return result


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
