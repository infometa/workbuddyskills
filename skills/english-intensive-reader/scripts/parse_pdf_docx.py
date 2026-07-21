#!/usr/bin/env python3
"""
parse_pdf_docx.py — english-intensive-reader
Extract plain text from PDF or Word (.docx) files.

Usage:
    python parse_pdf_docx.py --file article.pdf [--output article.txt]
    python parse_pdf_docx.py --file article.docx [--output article.txt]
"""

import sys
import os
import argparse
import json
from typing import Optional


def parse_pdf(file_path: str) -> dict:
    """Extract text from PDF using pdfplumber."""
    result = {
        "success": False,
        "text": "",
        "word_count": 0,
        "page_count": 0,
        "error": "",
    }
    try:
        import pdfplumber

        pages_text = []
        with pdfplumber.open(file_path) as pdf:
            result["page_count"] = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text)
        if not full_text.strip():
            result["error"] = "PDF 内容为空或为扫描件（图像层 PDF），本 Skill 不做 OCR。请先转换为文本层 PDF。"
            return result

        result["success"] = True
        result["text"] = full_text
        result["word_count"] = _count_words(full_text)
        return result

    except ImportError:
        result["error"] = "缺少依赖：请运行 pip install pdfplumber"
        return result
    except Exception as e:
        result["error"] = f"PDF 解析失败：{str(e)}"
        return result


def parse_docx(file_path: str) -> dict:
    """Extract text from Word .docx file using python-docx."""
    result = {
        "success": False,
        "text": "",
        "word_count": 0,
        "paragraph_count": 0,
        "error": "",
    }
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        result["paragraph_count"] = len(paragraphs)
        full_text = "\n\n".join(paragraphs)

        if not full_text.strip():
            result["error"] = "Word 文档内容为空。"
            return result

        result["success"] = True
        result["text"] = full_text
        result["word_count"] = _count_words(full_text)
        return result

    except ImportError:
        result["error"] = "缺少依赖：请运行 pip install python-docx"
        return result
    except Exception as e:
        result["error"] = f"Word 文档解析失败：{str(e)}"
        return result


def _count_words(text: str) -> int:
    """Count English words in text."""
    import re
    return len(re.findall(r"\b[a-zA-Z]+\b", text))


def parse_file(file_path: str) -> dict:
    """
    Auto-detect file type and parse accordingly.
    Returns result dict with success/text/word_count/error.
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "text": "",
            "word_count": 0,
            "error": f"文件不存在：{file_path}",
        }

    ext = os.path.splitext(file_path)[1].lower()

    # Reject image files (NEVER N9)
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    if ext in image_exts:
        return {
            "success": False,
            "text": "",
            "word_count": 0,
            "error": "本 Skill 不支持图片输入，不做 OCR。请先将图片转为文本后粘贴。",
        }

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        if ext == ".doc":
            return {
                "success": False,
                "text": "",
                "word_count": 0,
                "error": "不支持旧版 .doc 格式，请另存为 .docx 后重试。",
            }
        return parse_docx(file_path)
    else:
        # Try reading as plain text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return {
                "success": True,
                "text": text,
                "word_count": _count_words(text),
                "error": "",
            }
        except UnicodeDecodeError:
            return {
                "success": False,
                "text": "",
                "word_count": 0,
                "error": f"不支持的文件格式：{ext}。支持：.pdf / .docx / .txt",
            }


def check_word_limit(word_count: int, limit: int = 3000) -> dict:
    """
    Check if article exceeds word limit (NEVER N6).
    Returns warning info if exceeded.
    """
    if word_count > limit:
        return {
            "exceeded": True,
            "word_count": word_count,
            "limit": limit,
            "message": (
                f"⚠️ 文章共 {word_count} 词，超过单次处理上限（{limit} 词）。\n"
                f"建议分段精读，每次处理约 {limit} 词。\n"
                f"请告诉我从第几段开始，或直接粘贴你想精读的段落。"
            ),
        }
    return {"exceeded": False, "word_count": word_count, "limit": limit}


def main():
    parser = argparse.ArgumentParser(
        description="Parse PDF or Word file for english-intensive-reader"
    )
    parser.add_argument("--file", required=True, help="Path to PDF or Word file")
    parser.add_argument("--output", help="Output text file path (optional)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--word-limit", type=int, default=3000, help="Word count limit (default: 3000)"
    )
    args = parser.parse_args()

    result = parse_file(args.file)

    # Check word limit
    if result["success"]:
        limit_check = check_word_limit(result["word_count"], args.word_limit)
        result["limit_check"] = limit_check
        if limit_check["exceeded"]:
            print(limit_check["message"], file=sys.stderr)

    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
        print(output)
    else:
        if result["success"]:
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result["text"])
                print(
                    f"✅ 文本已提取到 {args.output}（{result['word_count']} 词）",
                    file=sys.stderr,
                )
            else:
                print(result["text"])
        else:
            print(f"❌ {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
