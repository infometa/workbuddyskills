#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 文档结构摘要 / 检查。

快速输出 PDF 的结构摘要：页数、页面尺寸、文本量、图片数、
字体使用情况、加密状态等。不需要导出完整 IR。
"""

import os

COMMAND = "ir_inspect"
DESCRIPTION = "Inspect PDF structure summary (pages, fonts, images, metadata)"
CATEGORY = "ir"

PARAMS = [
    {"name": "input", "type": "str",  "required": True, "help": "Input PDF path"},
    {"name": "pages", "type": "json", "required": False, "help": "Page indices to inspect (default all)"},
]


def handler(params):
    """检查 PDF 结构摘要。"""
    import fitz

    input_path = params["input"]
    target_pages = params.get("pages")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    doc = fitz.open(input_path)
    total_pages = len(doc)
    page_indices = target_pages if target_pages else list(range(total_pages))

    summary = {
        "file": os.path.basename(input_path),
        "file_size": os.path.getsize(input_path),
        "page_count": total_pages,
        "metadata": dict(doc.metadata) if doc.metadata else {},
        "is_encrypted": doc.is_encrypted,
        "is_pdf": doc.is_pdf,
        "pages": [],
        "fonts_summary": [],
        "totals": {
            "text_chars": 0,
            "images": 0,
            "links": 0,
        },
    }

    all_fonts = {}

    for i in page_indices:
        if i < 0 or i >= total_pages:
            continue
        page = doc[i]
        text = page.get_text("text")
        images = page.get_images()
        links = page.get_links()
        rect = page.rect

        page_info = {
            "index": i,
            "width": round(rect.width, 2),
            "height": round(rect.height, 2),
            "rotation": page.rotation,
            "text_chars": len(text),
            "text_preview": text[:200].strip() if text else "",
            "image_count": len(images),
            "link_count": len(links),
        }

        # 检测页面类型
        has_text = len(text.strip()) > 10
        has_full_page_img = False
        for img_info in images:
            xref = img_info[0]
            try:
                rects = page.get_image_rects(xref)
                for img_rect in rects:
                    coverage = (img_rect.width * img_rect.height) / (rect.width * rect.height)
                    if coverage > 0.85:
                        has_full_page_img = True
                        break
            except Exception:
                pass

        if has_text and not has_full_page_img:
            page_info["type"] = "text"
        elif not has_text and images:
            page_info["type"] = "scanned"
        elif has_text and has_full_page_img:
            page_info["type"] = "scanned_with_ocr"
        elif has_text and images:
            page_info["type"] = "mixed"
        else:
            page_info["type"] = "empty"

        summary["pages"].append(page_info)
        summary["totals"]["text_chars"] += len(text)
        summary["totals"]["images"] += len(images)
        summary["totals"]["links"] += len(links)

        # 收集字体
        for font_info in doc.get_page_fonts(i, full=True):
            name = font_info[3] if len(font_info) > 3 else f"xref-{font_info[0]}"
            if name not in all_fonts:
                all_fonts[name] = {
                    "name": name,
                    "xref": font_info[0],
                    "ext": font_info[1],
                    "type": font_info[2],
                    "pages": [],
                }
            all_fonts[name]["pages"].append(i)

    summary["fonts_summary"] = list(all_fonts.values())

    doc.close()

    return summary


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
