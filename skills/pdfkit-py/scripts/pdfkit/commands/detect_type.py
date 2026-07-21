#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 页面类型检测原子工具。
返回每页的类型 + 详细特征，让 AI 可以看到类型判断结果并决定编辑策略。
"""

import os
import sys

# smart_edit 辅助函数从 lite 包导入
from pdfkit.commands.smart_edit import _detect_page_types

COMMAND = "detect_type"
DESCRIPTION = "检测 PDF 每页的类型（文字/扫描/混合）和详细特征"
CATEGORY = "meta"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "pages", "type": "json", "required": False, "help": "目标页码列表（从 0 开始），默认全部页"},
]


def _get_edit_recommendation(page_type):
    """根据页面类型给出编辑策略建议。"""
    recommendations = {
        "text": "文字层 PDF，推荐使用 pdf_smart_edit 或 pdf_edit_text（search_for + redact 方案）",
        "scanned": "纯扫描件，推荐使用 pdf_smart_edit（OCR + 图片处理方案）",
        "scanned_with_ocr": "带 OCR 层的扫描件，推荐使用 pdf_overlay_text（overlay 方案），"
                           "或 pdf_search_text(engine=pdfplumber) 定位后用 pdf_overlay_text 替换",
        "mixed": "混合型 PDF，推荐使用 pdf_smart_edit（自动分页处理）",
        "empty": "空白页，无需编辑",
    }
    return recommendations.get(page_type, "未知类型，建议先用 pdf_inspect 查看结构")


def handler(params):
    """检测 PDF 每页的类型和详细特征。

    Args:
        params: {
            "input": PDF 文件路径,
            "pages": 目标页码列表（可选，默认全部页）,
        }
    """
    import fitz

    input_path = params["input"]
    pages = params.get("pages", None)

    doc = fitz.open(input_path)
    total_pages = len(doc)

    # 使用改进后的类型检测
    page_types = _detect_page_types(doc)

    if pages is None:
        target_pages = list(range(total_pages))
    else:
        target_pages = [p for p in pages if p < total_pages]

    results = []
    for pg in target_pages:
        page = doc[pg]
        text = page.get_text("text").strip()
        images = page.get_images()

        # 计算图片覆盖率
        max_coverage = 0.0
        for img_info in images:
            xref = img_info[0]
            try:
                img_rects = page.get_image_rects(xref)
                if img_rects:
                    for img_rect in img_rects:
                        img_area = abs(img_rect.width * img_rect.height)
                        page_area = abs(page.rect.width * page.rect.height)
                        if page_area > 0:
                            coverage = img_area / page_area
                            max_coverage = max(max_coverage, coverage)
            except Exception:
                pass

        results.append({
            "page": pg,
            "type": page_types.get(pg, "unknown"),
            "text_chars": len(text),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "image_count": len(images),
            "max_image_coverage": round(max_coverage, 3),
            "page_width": round(page.rect.width, 2),
            "page_height": round(page.rect.height, 2),
            "recommendation": _get_edit_recommendation(page_types.get(pg, "unknown")),
        })

    doc.close()

    return {
        "success": True,
        "total_pages": total_pages,
        "pages": results,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
