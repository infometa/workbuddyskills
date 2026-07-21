#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 页眉/页脚自动清除脚本。

智能识别并清除 PDF 中的页眉、页脚和脚注内容，
提取纯净的正文文本。

依赖：PyMuPDF (fitz)
"""

import os

COMMAND = "remove_headers_footers"
DESCRIPTION = "智能识别并清除 PDF 中的页眉、页脚和脚注内容。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": False, "help": "输出 PDF 路径（清除模式下必填）"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表，不指定表示全部页"},
    {"name": "header_ratio", "type": "float", "required": False, "default": 0.08, "help": "页眉区域占页面高度的比例"},
    {"name": "footer_ratio", "type": "float", "required": False, "default": 0.08, "help": "页脚区域占页面高度的比例"},
    {"name": "extract_only", "type": "bool", "required": False, "default": False, "help": "仅识别不清除，返回识别结果"},
]


def remove_headers_footers(input_path, output_path=None, pages=None,
                           header_ratio=0.08, footer_ratio=0.08,
                           extract_only=False):
    """识别并清除页眉页脚。

    Args:
        input_path: PDF 文件路径
        output_path: 输出 PDF 路径（extract_only=False 时必填）
        pages: 页码列表，None 表示全部页
        header_ratio: 页眉区域占页面高度的比例
        footer_ratio: 页脚区域占页面高度的比例
        extract_only: 仅识别不清除，返回识别结果
    """
    import fitz  # PyMuPDF

    doc = fitz.open(input_path)
    total_pages = len(doc)
    if pages is None:
        pages = list(range(total_pages))

    # 第一遍：收集每页的页眉页脚候选文本
    page_headers = {}
    page_footers = {}

    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        h = page.rect.height
        header_y = h * header_ratio
        footer_y = h * (1 - footer_ratio)

        blocks = page.get_text("dict")["blocks"]
        headers = []
        footers = []
        for block in blocks:
            if block["type"] != 0:
                continue
            bbox = block["bbox"]
            text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text += span["text"]
            text = text.strip()
            if not text:
                continue
            if bbox[3] < header_y:
                headers.append({"text": text, "bbox": list(bbox)})
            elif bbox[1] > footer_y:
                footers.append({"text": text, "bbox": list(bbox)})

        page_headers[p_idx] = headers
        page_footers[p_idx] = footers

    # 第二遍：识别重复出现的页眉页脚（跨页重复 = 高置信度）
    from collections import Counter
    header_texts = Counter()
    footer_texts = Counter()
    for h_list in page_headers.values():
        for h in h_list:
            header_texts[h["text"]] += 1
    for f_list in page_footers.values():
        for f in f_list:
            footer_texts[f["text"]] += 1

    threshold = max(2, len(pages) * 0.3)
    repeated_headers = {t for t, c in header_texts.items() if c >= threshold}
    repeated_footers = {t for t, c in footer_texts.items() if c >= threshold}

    results = []
    removed_count = 0

    if extract_only:
        for p_idx in pages:
            page_result = {"page": p_idx, "headers": [], "footers": []}
            for h in page_headers.get(p_idx, []):
                is_repeated = h["text"] in repeated_headers
                page_result["headers"].append({**h, "repeated": is_repeated, "confidence": 0.9 if is_repeated else 0.5})
            for f in page_footers.get(p_idx, []):
                is_repeated = f["text"] in repeated_footers
                page_result["footers"].append({**f, "repeated": is_repeated, "confidence": 0.9 if is_repeated else 0.5})
            results.append(page_result)
        doc.close()
        return {"success": True, "mode": "extract_only", "pages": results,
                "repeated_headers": list(repeated_headers), "repeated_footers": list(repeated_footers)}

    # 清除模式
    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        for h in page_headers.get(p_idx, []):
            if h["text"] in repeated_headers:
                rect = fitz.Rect(h["bbox"])
                page.add_redact_annot(rect, fill=(1, 1, 1))
                removed_count += 1
        for f in page_footers.get(p_idx, []):
            if f["text"] in repeated_footers:
                rect = fitz.Rect(f["bbox"])
                page.add_redact_annot(rect, fill=(1, 1, 1))
                removed_count += 1
        page.apply_redactions()

    doc.save(output_path)
    file_size = os.path.getsize(output_path)
    doc.close()

    return {"success": True, "mode": "remove", "removed_count": removed_count,
            "repeated_headers": list(repeated_headers), "repeated_footers": list(repeated_footers),
            "output": output_path, "file_size": file_size}


def handler(params):
    """处理 PDF 页眉页脚清除请求。"""
    input_path = params.get("input", "")
    output_path = params.get("output", "")
    pages = params.get("pages")
    extract_only = params.get("extract_only", False)
    header_ratio = params.get("header_ratio", 0.08)
    footer_ratio = params.get("footer_ratio", 0.08)

    if not input_path:
        raise ValueError("'input' 参数必填")
    if not extract_only and not output_path:
        raise ValueError("清除模式下 'output' 参数必填")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    return remove_headers_footers(input_path, output_path, pages, header_ratio, footer_ratio, extract_only)


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
