#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 页面旋转。"""

import os

COMMAND = "rotate"
DESCRIPTION = "Rotate PDF pages by angle"
CATEGORY = "organize"

PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "Input PDF path"},
    {"name": "output", "type": "str", "required": True, "help": "Output PDF path"},
    {"name": "angle", "type": "int", "required": False, "default": 90, "choices": [90, 180, 270, -90, -180, -270], "help": "Rotation angle"},
    {"name": "pages", "type": "json", "required": False, "help": "Page indices (0-based JSON array)"},
]


def handler(params):
    """旋转 PDF 页面。"""
    from pypdf import PdfReader, PdfWriter

    input_path = params["input"]
    output_path = params["output"]
    angle = int(params.get("angle", 90))
    pages = params.get("pages")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if angle not in [90, 180, 270, -90, -180, -270]:
        raise ValueError(f"不支持的旋转角度: {angle}，支持 90/180/270/-90/-180/-270")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

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

    rotated_count = 0
    for i, page in enumerate(reader.pages):
        if i in pages:
            page.rotate(angle)
            rotated_count += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "rotate",
        "angle": angle,
        "rotated_pages": rotated_count,
        "total_pages": total_pages,
        "output": output_path
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
