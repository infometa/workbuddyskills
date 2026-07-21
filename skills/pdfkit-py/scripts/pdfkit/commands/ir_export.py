#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF IR (Intermediate Representation) 导出。

使用 PyMuPDF 将 PDF 文档结构导出为 JSON 格式的中间表示，
包含页面、文本块、图片、字体、元数据等结构化信息。
"""

import json
import os

COMMAND = "ir_export"
DESCRIPTION = "Export PDF structure as JSON IR (Intermediate Representation)"
CATEGORY = "ir"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output", "type": "str",  "required": True,  "help": "Output JSON path"},
    {"name": "pages",  "type": "json", "required": False, "help": "Page indices (0-based JSON array), default all"},
    {"name": "include_images", "type": "bool", "required": False, "default": False, "help": "Include base64 image data"},
    {"name": "include_fonts",  "type": "bool", "required": False, "default": False, "help": "Include embedded font info"},
]


def handler(params):
    """导出 PDF 为 IR JSON。"""
    import fitz
    import base64

    input_path = params["input"]
    output_path = params["output"]
    target_pages = params.get("pages")
    include_images = params.get("include_images", False)
    include_fonts = params.get("include_fonts", False)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    doc = fitz.open(input_path)

    ir = {
        "version": "1.0",
        "generator": "pdfkit-lite",
        "source": os.path.basename(input_path),
        "metadata": {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "page_count": len(doc),
        },
        "pages": [],
    }

    page_indices = target_pages if target_pages else list(range(len(doc)))

    for i in page_indices:
        if i < 0 or i >= len(doc):
            continue
        page = doc[i]
        rect = page.rect

        page_ir = {
            "index": i,
            "width": rect.width,
            "height": rect.height,
            "rotation": page.rotation,
            "blocks": [],
            "images": [],
            "links": [],
        }

        # 提取文本块
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                block_ir = {
                    "type": "text",
                    "bbox": list(block["bbox"]),
                    "lines": [],
                }
                for line in block.get("lines", []):
                    line_ir = {
                        "bbox": list(line["bbox"]),
                        "dir": list(line.get("dir", (1, 0))),
                        "spans": [],
                    }
                    for span in line.get("spans", []):
                        span_ir = {
                            "text": span["text"],
                            "bbox": list(span["bbox"]),
                            "font": span.get("font", ""),
                            "size": span.get("size", 12),
                            "flags": span.get("flags", 0),
                            "color": span.get("color", 0),
                        }
                        line_ir["spans"].append(span_ir)
                    block_ir["lines"].append(line_ir)
                page_ir["blocks"].append(block_ir)
            elif block.get("type") == 1:  # 图片块
                img_ir = {
                    "type": "image",
                    "bbox": list(block["bbox"]),
                    "width": block.get("width", 0),
                    "height": block.get("height", 0),
                }
                page_ir["blocks"].append(img_ir)

        # 提取图片信息
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            img_entry = {
                "xref": xref,
                "width": img_info[2],
                "height": img_info[3],
                "bpc": img_info[4],
                "colorspace": img_info[5],
            }
            if include_images:
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:  # CMYK / CMYK+Alpha → RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    img_entry["data_base64"] = base64.b64encode(pix.tobytes("png")).decode()
                    pix = None
                except Exception:
                    img_entry["data_base64"] = None
            page_ir["images"].append(img_entry)

        # 提取链接
        for link in page.get_links():
            link_ir = {
                "kind": link.get("kind", 0),
                "from": list(link.get("from", fitz.Rect()).irect),
                "uri": link.get("uri", ""),
                "page": link.get("page", -1),
            }
            page_ir["links"].append(link_ir)

        ir["pages"].append(page_ir)

    # 字体信息
    if include_fonts:
        fonts = []
        for i in page_indices:
            if i < 0 or i >= len(doc):
                continue
            for font_info in doc.get_page_fonts(i, full=True):
                fonts.append({
                    "xref": font_info[0],
                    "ext": font_info[1],
                    "type": font_info[2],
                    "name": font_info[3],
                    "encoding": font_info[4] if len(font_info) > 4 else "",
                })
        # 去重
        seen = set()
        unique_fonts = []
        for f in fonts:
            key = f["xref"]
            if key not in seen:
                seen.add(key)
                unique_fonts.append(f)
        ir["fonts"] = unique_fonts

    doc.close()

    # 写入输出
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "output": output_path,
        "pages_exported": len(ir["pages"]),
        "total_blocks": sum(len(p["blocks"]) for p in ir["pages"]),
        "total_images": sum(len(p["images"]) for p in ir["pages"]),
        "file_size": os.path.getsize(output_path),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
