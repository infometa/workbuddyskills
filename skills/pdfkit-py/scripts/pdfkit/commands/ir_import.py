#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF IR (Intermediate Representation) 导入 / 重建。

从 JSON IR 文件重建 PDF 文档。使用 PyMuPDF 根据 IR 中的
文本块、图片、链接等信息生成新 PDF。
"""

import json
import os

COMMAND = "ir_import"
DESCRIPTION = "Rebuild PDF from JSON IR"
CATEGORY = "ir"

PARAMS = [
    {"name": "input",  "type": "str", "required": True, "help": "Input IR JSON path"},
    {"name": "output", "type": "str", "required": True, "help": "Output PDF path"},
]


def handler(params):
    """从 IR JSON 重建 PDF。"""
    import fitz
    import base64

    input_path = params["input"]
    output_path = params["output"]

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"IR 文件不存在: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        ir = json.load(f)

    doc = fitz.open()

    pages_created = 0
    for page_ir in ir.get("pages", []):
        width = page_ir.get("width", 595)
        height = page_ir.get("height", 842)
        page = doc.new_page(width=width, height=height)

        if page_ir.get("rotation", 0):
            page.set_rotation(page_ir["rotation"])

        # 重建文本块
        for block in page_ir.get("blocks", []):
            if block.get("type") == "text":
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        bbox = span.get("bbox", [0, 0, 100, 20])
                        font_size = span.get("size", 12)
                        font_name = span.get("font", "helv")
                        color = span.get("color", 0)

                        # 解析颜色
                        if isinstance(color, int):
                            r = ((color >> 16) & 0xFF) / 255.0
                            g = ((color >> 8) & 0xFF) / 255.0
                            b = (color & 0xFF) / 255.0
                            text_color = (r, g, b)
                        elif isinstance(color, (list, tuple)):
                            text_color = tuple(color[:3])
                        else:
                            text_color = (0, 0, 0)

                        point = fitz.Point(bbox[0], bbox[3] - 2)
                        try:
                            # 尝试使用原始字体
                            font = fitz.Font(font_name)
                        except Exception:
                            font = fitz.Font("helv")

                        tw = fitz.TextWriter(page.rect)
                        try:
                            tw.append(point, text, font=font, fontsize=font_size)
                            tw.write_text(page, color=text_color)
                        except Exception:
                            # 回退：直接 insert_text
                            page.insert_text(point, text, fontsize=font_size, color=text_color)

            elif block.get("type") == "image":
                # 如果有 base64 数据，插入图片
                data_b64 = block.get("data_base64")
                if data_b64:
                    img_data = base64.b64decode(data_b64)
                    bbox = block.get("bbox", [0, 0, 100, 100])
                    rect = fitz.Rect(bbox)
                    page.insert_image(rect, stream=img_data)

        # 重建图片（独立 images 列表中带 base64 的）
        for img in page_ir.get("images", []):
            data_b64 = img.get("data_base64")
            if data_b64:
                img_data = base64.b64decode(data_b64)
                # 没有精确位置信息时跳过
                # 这些图片已经在 blocks 中通过 image block 处理了

        # 重建链接
        for link in page_ir.get("links", []):
            link_dict = {
                "kind": link.get("kind", 2),  # LINK_URI
                "from": fitz.Rect(link.get("from", [0, 0, 50, 20])),
            }
            uri = link.get("uri", "")
            if uri:
                link_dict["uri"] = uri
            target_page = link.get("page", -1)
            if target_page >= 0:
                link_dict["kind"] = 1  # LINK_GOTO
                link_dict["page"] = target_page
            try:
                page.insert_link(link_dict)
            except Exception:
                pass

        pages_created += 1

    # 设置元数据
    metadata = ir.get("metadata", {})
    doc.set_metadata({
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "subject": metadata.get("subject", ""),
        "creator": "pdfkit-lite ir_import",
    })

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return {
        "success": True,
        "output": output_path,
        "pages_created": pages_created,
        "file_size": os.path.getsize(output_path),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
