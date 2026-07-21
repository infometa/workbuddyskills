#!/usr/bin/env python3
"""
extract_pdf.py — PDF 文本提取 + 章节切片

输出统一 segments JSON schema（见 modules/input-router.md），供三步翻译消费。

用法：
  python extract_pdf.py --in paper.pdf --out segments.json
  python extract_pdf.py --check paper.pdf

依赖：
  pip install pdfplumber
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

SECTION_HEAD_PATTERNS = [
    (r'^(Abstract)\s*$', 'abstract', 1),
    (r'^(\d+)\s+(Introduction|Related Work|Background|Method|Methods|Methodology|'
     r'Approach|Experiments?|Results?|Discussion|Conclusion|References)\s*$', 'section', 1),
    (r'^(\d+\.\d+)\s+(.+?)\s*$', 'subsection', 2),
    (r'^(\d+\.\d+\.\d+)\s+(.+?)\s*$', 'subsubsection', 3),
]


def extract_pdf(path: Path) -> Dict[str, Any]:
    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber 未安装；请先 `pip install pdfplumber`", file=sys.stderr)
        sys.exit(2)

    paper_id = "pdf-" + hashlib.md5(path.read_bytes()).hexdigest()[:8]
    paper_meta: Dict[str, Any] = {
        "source_type": "pdf",
        "source_path": str(path.resolve()),
        "paper_id": paper_id,
        "language_detected": None,
        "pdf_pages": 0,
        "has_latex": False,
    }
    segments: List[Dict[str, Any]] = []
    char_offset = 0
    section_path: List[str] = []
    seg_idx = 0

    with pdfplumber.open(path) as pdf:
        paper_meta["pdf_pages"] = len(pdf.pages)
        all_text = []

        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            all_text.append(text)
            for raw_para in re.split(r"\n\s*\n", text):
                para = raw_para.strip()
                if len(para) < 30:
                    continue
                for pattern, kind, level in SECTION_HEAD_PATTERNS:
                    if re.match(pattern, para, re.MULTILINE):
                        match = re.match(pattern, para, re.MULTILINE)
                        title = match.group(level) if level <= len(match.groups()) else para[:50]
                        if kind == "abstract":
                            section_path = ["§abs", title]
                        elif kind == "section":
                            section_path = [f"§{match.group(1)}", match.group(2)]
                        elif kind == "subsection":
                            section_path = section_path[:2] + [f"§{match.group(1)}", match.group(2)]
                        elif kind == "subsubsection":
                            section_path = section_path[:4] + [f"§{match.group(1)}", match.group(2)]
                        break

                seg_idx += 1
                seg_id = f"{section_path[0] if section_path else '§p'}-p{seg_idx}"
                paragraph_kind = classify_paragraph(para)

                segments.append({
                    "segment_id": seg_id,
                    "section_path": section_path.copy(),
                    "page_range": [page_num, page_num],
                    "char_range": [char_offset, char_offset + len(para)],
                    "paragraph_kind": paragraph_kind,
                    "raw_text": para,
                })
                char_offset += len(para) + 2

    full_text = "\n\n".join(all_text)
    paper_meta["language_detected"] = detect_language(full_text)
    paper_meta["has_latex"] = bool(re.search(r'\\(cite|ref|begin\{equation)', full_text))
    paper_meta["total_segments"] = len(segments)

    return {"paper_meta": paper_meta, "segments": segments}


def classify_paragraph(text: str) -> str:
    if re.match(r'^Abstract\b', text, re.IGNORECASE):
        return "abstract"
    if re.match(r'^(Figure|Fig\.|Table)\s*\d', text, re.IGNORECASE):
        return "caption"
    if re.match(r'^Algorithm\s*\d', text, re.IGNORECASE):
        return "algorithm"
    if re.match(r'^[-•*]\s', text) or re.match(r'^\d+[.)]\s', text):
        return "list_item"
    if "=" in text and len(re.findall(r'[a-zA-Z]\s*=\s*', text)) >= 2:
        return "equation"
    return "narrative"


def detect_language(text: str) -> str:
    sample = text[:5000]
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', sample))
    en_words = len(re.findall(r'\b[a-zA-Z]{2,}\b', sample))
    if cn_chars > en_words * 0.3 and cn_chars > 100:
        return "mixed" if en_words > cn_chars * 0.3 else "zh"
    return "en"


def cmd_extract(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.exists():
        print(f"❌ 文件不存在: {path}", file=sys.stderr)
        return 1
    result = extract_pdf(path)
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pm = result["paper_meta"]
    print(f"✅ 已提取 → {args.output}")
    print(f"   paper_id: {pm['paper_id']}")
    print(f"   pages: {pm['pdf_pages']}")
    print(f"   total_segments: {pm['total_segments']}")
    print(f"   language: {pm['language_detected']}")
    print(f"   has_latex: {pm['has_latex']}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        return 1
    try:
        import pdfplumber
    except ImportError:
        print("⚠️  pdfplumber 未安装；请先 `pip install pdfplumber`")
        return 2
    with pdfplumber.open(path) as pdf:
        text = (pdf.pages[0].extract_text() or "").strip()
        if len(text) < 100:
            print(f"⚠️  PDF 第一页文本仅 {len(text)} 字符，疑似扫描件，建议先 OCR")
            return 3
        print(f"✅ PDF 可解析（共 {len(pdf.pages)} 页）")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF 文本提取 + 章节切片")
    sub = parser.add_subparsers(dest="cmd", required=False)

    pe = sub.add_parser("extract", help="提取 PDF 为 segments.json")
    pe.add_argument("--in", dest="input", required=True)
    pe.add_argument("--out", dest="output", required=True)
    pe.set_defaults(func=cmd_extract)

    pc = sub.add_parser("check", help="快速检查 PDF 可解析性")
    pc.add_argument("--in", dest="input", required=True)
    pc.set_defaults(func=cmd_check)

    parser.set_defaults(cmd="extract")
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
