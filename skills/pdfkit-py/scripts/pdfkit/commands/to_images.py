#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 页面转图片。"""

import os

COMMAND = "to_images"
DESCRIPTION = "将 PDF 页面渲染为图片（PNG/JPEG）"
CATEGORY = "read"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output_dir", "type": "str", "required": True, "help": "Output directory for images"},
    {"name": "pages",  "type": "json", "required": False, "help": "Page indices (0-based JSON array)"},
    {"name": "dpi",    "type": "int",  "required": False, "default": 150, "help": "Resolution in DPI"},
    {"name": "format", "type": "str",  "required": False, "default": "png",
     "choices": ["png", "jpeg"], "help": "Image format"},
]


def handler(params):
    import fitz

    input_path = params["input"]
    output_dir = params["output_dir"]
    target_pages = params.get("pages")
    dpi = params.get("dpi", 150)
    img_format = params.get("format", "png")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_path)
    total_pages = len(doc)
    page_indices = target_pages if target_pages else list(range(total_pages))

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    images = []

    for i in page_indices:
        if i < 0 or i >= total_pages:
            continue
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)

        ext = img_format
        basename = os.path.splitext(os.path.basename(input_path))[0]
        filename = f"{basename}_page_{i}.{ext}"
        filepath = os.path.join(output_dir, filename)

        if img_format == "jpeg":
            pix.save(filepath, output="jpeg")
        else:
            pix.save(filepath)

        images.append({
            "page": i,
            "path": filepath,
            "width": pix.width,
            "height": pix.height,
            "file_size": os.path.getsize(filepath),
        })
        pix = None

    doc.close()

    return {
        "success": True,
        "images_created": len(images),
        "dpi": dpi,
        "format": img_format,
        "output_dir": output_dir,
        "images": images,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
