#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 文档分块（Chunking）脚本。

将 PDF 文档按语义分块，适用于 RAG 知识库构建。
支持多种分块策略：按页、按段落、按固定大小、按语义。

依赖：PyMuPDF (fitz)
"""

import os
import re

COMMAND = "chunk_pdf"
DESCRIPTION = "将 PDF 文档按语义分块，适用于 RAG 知识库构建"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "strategy", "type": "str", "required": False, "default": "paragraph", "choices": ["page", "paragraph", "fixed", "semantic"], "help": "分块策略"},
    {"name": "chunk_size", "type": "int", "required": False, "default": 1000, "help": "每块最大字符数（fixed/semantic 策略使用）"},
    {"name": "overlap", "type": "int", "required": False, "default": 200, "help": "块间重叠字符数（fixed 策略使用）"},
    {"name": "pages", "type": "json", "required": False, "help": "指定页码列表（从 0 开始），默认全部页"},
]


def handler(params):
    """将 PDF 文档按指定策略分块。

    Args:
        params: {
            "input": PDF 文件路径,
            "strategy": 分块策略 - "page"(按页), "paragraph"(按段落), "fixed"(固定大小), "semantic"(语义),
            "chunk_size": 每块最大字符数,
            "overlap": 块间重叠字符数,
            "pages": 指定页码列表，None 表示全部页
        }
    """
    import fitz

    input_path = params["input"]
    strategy = params.get("strategy", "paragraph")
    chunk_size = params.get("chunk_size", 1000)
    overlap = params.get("overlap", 200)
    pages = params.get("pages", None)

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    chunks = []

    if strategy == "page":
        # 按页分块
        for p_idx in pages:
            if p_idx < 0 or p_idx >= total_pages:
                continue
            page = doc[p_idx]
            text = page.get_text("text").strip()
            if text:
                chunks.append({
                    "id": f"page_{p_idx}",
                    "text": text,
                    "metadata": {
                        "page": p_idx,
                        "char_count": len(text),
                        "strategy": "page"
                    }
                })

    elif strategy == "paragraph":
        # 按段落分块（基于空行分割）
        chunk_id = 0
        for p_idx in pages:
            if p_idx < 0 or p_idx >= total_pages:
                continue
            page = doc[p_idx]
            text = page.get_text("text").strip()
            if not text:
                continue

            # 按空行分割段落
            paragraphs = re.split(r'\n\s*\n', text)
            current_chunk = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # 如果当前块加上新段落不超过限制，合并
                if len(current_chunk) + len(para) + 1 <= chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + para
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append({
                            "id": f"chunk_{chunk_id}",
                            "text": current_chunk,
                            "metadata": {
                                "page": p_idx,
                                "char_count": len(current_chunk),
                                "strategy": "paragraph"
                            }
                        })
                        chunk_id += 1
                    current_chunk = para

            # 保存最后一个块
            if current_chunk:
                chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": current_chunk,
                    "metadata": {
                        "page": p_idx,
                        "char_count": len(current_chunk),
                        "strategy": "paragraph"
                    }
                })
                chunk_id += 1

    elif strategy == "fixed":
        # 固定大小分块（带重叠）
        all_text = ""
        page_boundaries = []
        for p_idx in pages:
            if p_idx < 0 or p_idx >= total_pages:
                continue
            page = doc[p_idx]
            text = page.get_text("text").strip()
            if text:
                start = len(all_text)
                all_text += text + "\n\n"
                page_boundaries.append((p_idx, start, len(all_text)))

        # 按固定大小切分
        chunk_id = 0
        start = 0
        while start < len(all_text):
            end = min(start + chunk_size, len(all_text))

            # 尝试在句子边界切分
            if end < len(all_text):
                # 向后查找句号/换行
                for sep in ['\n\n', '。', '.\n', '. ', '\n']:
                    pos = all_text.rfind(sep, start + chunk_size // 2, end)
                    if pos > start:
                        end = pos + len(sep)
                        break

            chunk_text = all_text[start:end].strip()
            if chunk_text:
                # 确定所在页码
                page_num = 0
                for p_idx, p_start, p_end in page_boundaries:
                    if p_start <= start < p_end:
                        page_num = p_idx
                        break

                chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": chunk_text,
                    "metadata": {
                        "page": page_num,
                        "char_count": len(chunk_text),
                        "start_offset": start,
                        "end_offset": end,
                        "strategy": "fixed"
                    }
                })
                chunk_id += 1

            start = end - overlap if overlap > 0 else end

    elif strategy == "semantic":
        # 语义分块（基于标题/段落结构）
        chunk_id = 0
        for p_idx in pages:
            if p_idx < 0 or p_idx >= total_pages:
                continue
            page = doc[p_idx]

            # 获取文本块及其字体信息
            blocks = page.get_text("dict")["blocks"]
            current_section = ""
            current_title = ""

            for block in blocks:
                if block["type"] != 0:  # 非文本块
                    continue

                for line in block.get("lines", []):
                    line_text = ""
                    max_font_size = 0
                    for span in line.get("spans", []):
                        line_text += span["text"]
                        max_font_size = max(max_font_size, span["size"])

                    line_text = line_text.strip()
                    if not line_text:
                        continue

                    # 判断是否为标题（字号较大）
                    is_title = max_font_size > 14

                    if is_title and current_section:
                        # 遇到新标题，保存当前段落
                        chunks.append({
                            "id": f"chunk_{chunk_id}",
                            "text": current_section.strip(),
                            "metadata": {
                                "page": p_idx,
                                "title": current_title,
                                "char_count": len(current_section),
                                "strategy": "semantic"
                            }
                        })
                        chunk_id += 1
                        current_section = ""

                    if is_title:
                        current_title = line_text

                    current_section += line_text + "\n"

            # 保存最后一段
            if current_section.strip():
                chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": current_section.strip(),
                    "metadata": {
                        "page": p_idx,
                        "title": current_title,
                        "char_count": len(current_section),
                        "strategy": "semantic"
                    }
                })
                chunk_id += 1

    doc.close()

    total_chars = sum(c["metadata"]["char_count"] for c in chunks)

    return {
        "success": True,
        "total_chunks": len(chunks),
        "total_chars": total_chars,
        "strategy": strategy,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks": chunks,
        "metadata": {
            "file": os.path.basename(input_path),
            "total_pages": total_pages,
            "pages_processed": len(pages)
        }
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
