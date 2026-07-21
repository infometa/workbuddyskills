#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 阅读顺序检测脚本。

检测 PDF 页面中文本块的正确阅读顺序，
特别适用于多栏排版的文档。

依赖：PyMuPDF (fitz)
"""

import os

COMMAND = "reading_order"
DESCRIPTION = "检测 PDF 页面中文本块的正确阅读顺序，支持多栏排版"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表（从 0 开始），默认全部页"},
]


def _detect_columns(blocks, page_width, threshold=0.15):
    """检测文本块的栏布局。

    通过分析文本块的水平位置分布来判断栏数。
    """
    if not blocks:
        return [[]]

    # 按 center_x 排序
    sorted_blocks = sorted(blocks, key=lambda b: b["center_x"])

    # 使用间隙检测法
    columns = [[sorted_blocks[0]]]
    gap_threshold = page_width * threshold

    for i in range(1, len(sorted_blocks)):
        block = sorted_blocks[i]
        prev_block = sorted_blocks[i - 1]

        # 检查是否有明显的水平间隙
        gap = block["bbox"][0] - prev_block["bbox"][2]
        if gap > gap_threshold:
            columns.append([block])
        else:
            # 判断是否属于同一栏
            current_col_center = sum(b["center_x"] for b in columns[-1]) / len(columns[-1])
            if abs(block["center_x"] - current_col_center) < page_width * 0.3:
                columns[-1].append(block)
            else:
                columns.append([block])

    # 过滤掉只有一个小块的"栏"
    columns = [col for col in columns if len(col) > 1 or
               (len(col) == 1 and col[0]["height"] > 50)]

    return columns if columns else [[]]


def handler(params):
    """检测 PDF 页面的阅读顺序。

    Args:
        params: {
            "input": PDF 文件路径,
            "pages": 页码列表，None 表示全部页
        }
    """
    import fitz

    input_path = params["input"]
    pages = params.get("pages", None)

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    results = []

    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        page_width = page.rect.width
        page_height = page.rect.height

        # 获取文本块
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []

        for block in blocks:
            if block["type"] != 0:  # 非文本块
                continue
            bbox = block["bbox"]
            text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text += span["text"]
                text += "\n"

            text = text.strip()
            if not text:
                continue

            text_blocks.append({
                "bbox": list(bbox),
                "text": text[:200],  # 截取前 200 字符
                "center_x": (bbox[0] + bbox[2]) / 2,
                "center_y": (bbox[1] + bbox[3]) / 2,
                "width": bbox[2] - bbox[0],
                "height": bbox[3] - bbox[1]
            })

        # 检测栏数
        columns = _detect_columns(text_blocks, page_width)
        num_columns = len(columns)

        # 按阅读顺序排序
        ordered_blocks = []
        if num_columns <= 1:
            # 单栏：从上到下
            ordered_blocks = sorted(text_blocks, key=lambda b: b["center_y"])
            layout_type = "single_column"
        else:
            # 多栏：先按栏排序，栏内从上到下
            for col_idx, col_blocks in enumerate(columns):
                col_sorted = sorted(col_blocks, key=lambda b: b["center_y"])
                for b in col_sorted:
                    b["column"] = col_idx
                    ordered_blocks.append(b)
            layout_type = f"{num_columns}_columns"

        # 添加阅读顺序索引
        for i, block in enumerate(ordered_blocks):
            block["reading_order"] = i

        results.append({
            "page": p_idx,
            "layout_type": layout_type,
            "num_columns": num_columns,
            "total_blocks": len(ordered_blocks),
            "blocks": ordered_blocks,
            "page_size": {"width": page_width, "height": page_height}
        })

    doc.close()

    return {
        "success": True,
        "pages_analyzed": len(results),
        "results": results,
        "metadata": {
            "file": os.path.basename(input_path),
            "total_pages": total_pages
        }
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
