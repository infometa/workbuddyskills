#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取 PDF 中的内嵌图片。"""

import os

COMMAND = "extract_images"
DESCRIPTION = "提取 PDF 中的内嵌图片并保存到指定目录"
CATEGORY = "read"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output_dir", "type": "str", "required": True, "help": "Output directory for images"},
    {"name": "pages",  "type": "json", "required": False, "help": "Page indices (0-based JSON array)"},
    {"name": "min_size", "type": "int", "required": False, "default": 100,
     "help": "Minimum image dimension (skip tiny images)"},
]


def handler(params):
    import fitz

    input_path = params["input"]
    output_dir = params["output_dir"]
    target_pages = params.get("pages")
    min_size = params.get("min_size", 100)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_path)
    total_pages = len(doc)
    page_indices = target_pages if target_pages else list(range(total_pages))

    extracted = []
    seen_xrefs = set()

    for i in page_indices:
        if i < 0 or i >= total_pages:
            continue
        page = doc[i]

        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            width = img_info[2]
            height = img_info[3]

            # 跳过太小的图片
            if width < min_size and height < min_size:
                continue

            try:
                pix = fitz.Pixmap(doc, xref)
                # CMYK / CMYK+Alpha → RGB
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                ext = "png"
                filename = f"image_p{i}_x{xref}.{ext}"
                filepath = os.path.join(output_dir, filename)
                pix.save(filepath)

                extracted.append({
                    "page": i,
                    "xref": xref,
                    "width": pix.width,
                    "height": pix.height,
                    "path": filepath,
                    "file_size": os.path.getsize(filepath),
                })
                pix = None
            except Exception as e:
                extracted.append({
                    "page": i,
                    "xref": xref,
                    "width": width,
                    "height": height,
                    "error": str(e),
                })

    doc.close()

    success_count = sum(1 for e in extracted if "path" in e)

    return {
        "success": True,
        "images_found": len(extracted),
        "images_extracted": success_count,
        "output_dir": output_dir,
        "images": extracted,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
