#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 页面裁剪。"""

import os

COMMAND = "crop"
DESCRIPTION = "Crop PDF pages by coordinates"
CATEGORY = "organize"

PARAMS = [
    {"name": "input",  "type": "str",   "required": True,  "help": "Input PDF path"},
    {"name": "output", "type": "str",   "required": True,  "help": "Output PDF path"},
    {"name": "left",   "type": "float", "required": False, "default": 0,   "help": "Left edge x (PyMuPDF coords)"},
    {"name": "top",    "type": "float", "required": False, "default": 0,   "help": "Top edge y (PyMuPDF coords, y=0 at page top)"},
    {"name": "right",  "type": "float", "required": False, "default": 612, "help": "Right edge x (PyMuPDF coords)"},
    {"name": "bottom", "type": "float", "required": False, "default": 792, "help": "Bottom edge y (PyMuPDF coords, y=page_height at page bottom)"},
    {"name": "pages",  "type": "json",  "required": False, "help": "Page indices (0-based JSON array)"},
]


def handler(params):
    """裁剪 PDF 页面。

    坐标系：PyMuPDF 坐标系（原点在页面左上角，y 向下增大）。
    - left, top: 裁剪区域左上角坐标
    - right, bottom: 裁剪区域右下角坐标
    - 例如：保留页面上半部分 → left=0, top=0, right=页宽, bottom=页高/2

    Args:
        params: {
            "input": PDF 路径,
            "output": 输出 PDF 路径,
            "left": 左边界 x（默认 0）,
            "top": 上边界 y（默认 0，即页面顶部）,
            "right": 右边界 x（默认 612）,
            "bottom": 下边界 y（默认 792，即页面底部）,
            "pages": 页码列表（可选，0-based，默认全部）
        }
    """
    from pypdf import PdfReader, PdfWriter

    input_path = params["input"]
    output_path = params["output"]

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    left = float(params.get("left", 0))
    top = float(params.get("top", 0))
    right = float(params.get("right", 612))
    bottom = float(params.get("bottom", 792))
    pages = params.get("pages")

    reader = PdfReader(input_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    if pages is not None:
        if isinstance(pages, str):
            pages = [int(p.strip()) for p in pages.split(",")]
        else:
            pages = [int(p) for p in pages]
    else:
        pages = list(range(total_pages))

    cropped_count = 0
    for i, page in enumerate(reader.pages):
        if i in pages:
            # 坐标转换：PyMuPDF (y=0 顶部) → PDF 原生 (y=0 底部)
            # pypdf mediabox 使用 PDF 原生坐标系
            page_height = float(page.mediabox.height)
            pdf_bottom = page_height - bottom  # PyMuPDF bottom → PDF bottom
            pdf_top = page_height - top        # PyMuPDF top → PDF top

            page.mediabox.left = left
            page.mediabox.bottom = pdf_bottom
            page.mediabox.right = right
            page.mediabox.top = pdf_top
            cropped_count += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "crop",
        "crop_box": {"left": left, "top": top, "right": right, "bottom": bottom},
        "cropped_pages": cropped_count,
        "total_pages": total_pages,
        "output": output_path
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
