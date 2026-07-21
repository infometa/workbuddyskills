#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 布局分析脚本。
基于规则引擎分析 PDF 页面的布局结构，识别标题、段落、表格、图片区域。
"""

COMMAND = "layout_analyze"
DESCRIPTION = "分析 PDF 页面的布局结构，识别标题、段落、表格、图片区域"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表（从 0 开始），默认全部"},
    {"name": "detail", "type": "str", "required": False, "default": "basic", "choices": ["basic", "full"], "help": "详细程度"},
]


def handler(params):
    """分析 PDF 页面的布局结构。

    Args:
        params: {
            "input": PDF 路径,
            "pages": 页码列表（可选，默认全部）,
            "detail": 详细程度（basic/full，默认 basic）
        }
    """
    import fitz

    input_path = params["input"]
    pages = params.get("pages", None)
    detail = params.get("detail", "basic")

    doc = fitz.open(input_path)
    target_pages = pages if pages else list(range(len(doc)))

    results = []

    for page_num in target_pages:
        if page_num >= len(doc):
            continue

        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height

        # 提取所有文本块
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        blocks_info = []

        all_font_sizes = []
        text_blocks = []

        for block in text_dict.get("blocks", []):
            if block["type"] == 0:  # 文本块
                block_text = ""
                block_fonts = []
                block_sizes = []

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span["text"]
                        block_fonts.append(span.get("font", ""))
                        size = span.get("size", 12)
                        block_sizes.append(size)
                        all_font_sizes.append(size)
                    block_text += "\n"

                block_text = block_text.strip()
                if not block_text:
                    continue

                avg_size = sum(block_sizes) / len(block_sizes) if block_sizes else 12
                bbox = block["bbox"]

                text_blocks.append({
                    "text": block_text,
                    "bbox": [round(b, 1) for b in bbox],
                    "font_size": round(avg_size, 1),
                    "fonts": list(set(block_fonts)),
                    "line_count": len(block.get("lines", [])),
                })

            elif block["type"] == 1:  # 图片块
                bbox = block["bbox"]
                blocks_info.append({
                    "type": "image",
                    "bbox": [round(b, 1) for b in bbox],
                    "width": round(bbox[2] - bbox[0], 1),
                    "height": round(bbox[3] - bbox[1], 1),
                    "image_index": block.get("number", -1),
                })

        # 计算平均字号（用于区分标题和正文）
        avg_font_size = sum(all_font_sizes) / len(all_font_sizes) if all_font_sizes else 12
        title_threshold = avg_font_size * 1.2

        # 分类文本块
        for tb in text_blocks:
            block_type = "paragraph"

            # 标题检测：字号大于阈值，且行数较少
            if tb["font_size"] > title_threshold and tb["line_count"] <= 3:
                block_type = "title"
            # 页眉页脚检测：位于页面顶部或底部
            elif tb["bbox"][1] < page_height * 0.08:
                block_type = "header"
            elif tb["bbox"][3] > page_height * 0.92:
                block_type = "footer"
            # 短文本可能是标注
            elif len(tb["text"]) < 20 and tb["line_count"] == 1:
                block_type = "caption"

            block_info = {
                "type": block_type,
                "text": tb["text"] if detail == "full" else (tb["text"][:100] + "..." if len(tb["text"]) > 100 else tb["text"]),
                "bbox": tb["bbox"],
                "font_size": tb["font_size"],
            }

            if detail == "full":
                block_info["fonts"] = tb["fonts"]
                block_info["line_count"] = tb["line_count"]

            blocks_info.append(block_info)

        # 检测表格区域（通过路径对象的网格模式）
        drawings = page.get_drawings()
        if drawings:
            # 简单的表格检测：查找矩形密集区域
            rects = [d["rect"] for d in drawings if d.get("rect")]
            if len(rects) > 4:
                # 聚类矩形，找到表格区域
                min_x = min(r[0] for r in rects)
                min_y = min(r[1] for r in rects)
                max_x = max(r[2] for r in rects)
                max_y = max(r[3] for r in rects)

                # 如果矩形区域足够大，认为是表格
                area = (max_x - min_x) * (max_y - min_y)
                page_area = page_width * page_height
                if area > page_area * 0.05:  # 占页面面积 5% 以上
                    blocks_info.append({
                        "type": "table",
                        "bbox": [round(min_x, 1), round(min_y, 1), round(max_x, 1), round(max_y, 1)],
                        "rect_count": len(rects),
                    })

        # 按 Y 坐标排序
        blocks_info.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

        page_result = {
            "page": page_num,
            "width": round(page_width, 1),
            "height": round(page_height, 1),
            "blocks": blocks_info,
            "block_count": len(blocks_info),
            "stats": {
                "avg_font_size": round(avg_font_size, 1),
                "title_threshold": round(title_threshold, 1),
                "titles": sum(1 for b in blocks_info if b["type"] == "title"),
                "paragraphs": sum(1 for b in blocks_info if b["type"] == "paragraph"),
                "images": sum(1 for b in blocks_info if b["type"] == "image"),
                "tables": sum(1 for b in blocks_info if b["type"] == "table"),
            }
        }
        results.append(page_result)

    doc.close()

    return {
        "pages": results,
        "total_pages": len(results),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
