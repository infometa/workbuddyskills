#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 问答（Chat with PDF）脚本。

提取 PDF 文本内容，按页分块，返回结构化的上下文信息，
供 AI 进行自然语言问答。

依赖：PyMuPDF (fitz)
"""

import os

COMMAND = "chat_pdf"
DESCRIPTION = "从 PDF 中提取与问题相关的上下文，供 AI 问答"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "question", "type": "str", "required": False, "default": "", "help": "用户问题"},
    {"name": "pages", "type": "json", "required": False, "help": "指定页码列表（从 0 开始），默认全部页"},
    {"name": "max_context_chars", "type": "int", "required": False, "default": 8000, "help": "最大上下文字符数"},
]


def handler(params):
    """从 PDF 中提取与问题相关的上下文。

    Args:
        params: {
            "input": PDF 文件路径,
            "question": 用户问题,
            "pages": 指定页码列表（从 0 开始），None 表示全部页,
            "max_context_chars": 最大上下文字符数
        }
    """
    import fitz

    input_path = params["input"]
    question = params.get("question", "")
    pages = params.get("pages", None)
    max_context_chars = params.get("max_context_chars", 8000)

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    # 提取每页文本
    page_texts = []
    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        text = page.get_text("text").strip()
        if text:
            page_texts.append({
                "page": p_idx,
                "text": text,
                "char_count": len(text)
            })

    # 如果有问题关键词，按相关性排序
    if question:
        keywords = question.lower().split()
        for pt in page_texts:
            score = 0
            text_lower = pt["text"].lower()
            for kw in keywords:
                score += text_lower.count(kw)
            pt["relevance_score"] = score

        # 按相关性排序
        page_texts.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # 截取上下文
    context_parts = []
    total_chars = 0
    for pt in page_texts:
        if total_chars + pt["char_count"] > max_context_chars:
            # 截取部分文本
            remaining = max_context_chars - total_chars
            if remaining > 100:
                context_parts.append({
                    "page": pt["page"],
                    "text": pt["text"][:remaining] + "...(截断)",
                    "truncated": True
                })
            break
        context_parts.append({
            "page": pt["page"],
            "text": pt["text"],
            "truncated": False
        })
        total_chars += pt["char_count"]

    # 按页码重新排序
    context_parts.sort(key=lambda x: x["page"])

    doc.close()

    return {
        "success": True,
        "total_pages": total_pages,
        "pages_extracted": len(context_parts),
        "total_chars": total_chars,
        "question": question,
        "context": context_parts,
        "metadata": {
            "file": os.path.basename(input_path),
            "file_size": os.path.getsize(input_path)
        }
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
