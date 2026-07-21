#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转长图（所有页面拼接为一张图片）。"""

import os

COMMAND = "long_image"
DESCRIPTION = "将 PDF 所有页面拼接为一张长图"
CATEGORY = "read"

PARAMS = [
    {"name": "input",  "type": "str", "required": True,  "help": "Input PDF path"},
    {"name": "output", "type": "str", "required": True,  "help": "Output image path"},
    {"name": "pages",  "type": "json", "required": False, "help": "Page indices (0-based JSON array)"},
    {"name": "dpi",    "type": "int", "required": False, "default": 150, "help": "Resolution in DPI"},
    {"name": "gap",    "type": "int", "required": False, "default": 0,   "help": "Gap between pages in pixels"},
]


def handler(params):
    import fitz
    from PIL import Image
    import io

    input_path = params["input"]
    output_path = params["output"]
    target_pages = params.get("pages")
    dpi = params.get("dpi", 150)
    gap = params.get("gap", 0)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    doc = fitz.open(input_path)
    total_pages = len(doc)
    page_indices = target_pages if target_pages else list(range(total_pages))

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    # 渲染所有页面
    page_images = []
    for i in page_indices:
        if i < 0 or i >= total_pages:
            continue
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        page_images.append(img)
        pix = None

    doc.close()

    if not page_images:
        raise ValueError("没有可渲染的页面")

    # 计算总尺寸
    max_width = max(img.width for img in page_images)
    total_height = sum(img.height for img in page_images) + gap * (len(page_images) - 1)

    # 拼接
    long_img = Image.new("RGB", (max_width, total_height), (255, 255, 255))
    y_offset = 0
    for img in page_images:
        # 水平居中
        x_offset = (max_width - img.width) // 2
        long_img.paste(img, (x_offset, y_offset))
        y_offset += img.height + gap

    # 保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
        long_img.save(output_path, "JPEG", quality=90)
    else:
        long_img.save(output_path, "PNG")

    return {
        "success": True,
        "output": output_path,
        "pages_rendered": len(page_images),
        "width": max_width,
        "height": total_height,
        "dpi": dpi,
        "file_size": os.path.getsize(output_path),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
