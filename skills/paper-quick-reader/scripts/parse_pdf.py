#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_pdf.py —— 论文 PDF / DOCX / pasted_text 解析器（v0.1 POC）

功能：
  - 从 PDF / DOCX / 粘贴文本抽出结构化 (text, page, section) 三元组
  - 识别章节标题、figure/table caption、过滤 header/footer/footnote
  - 输出 references/pdf-parsing-heuristics.md 定义的 paper_*.json 结构
  - 供后续 summary_card 抽取、ngram provenance 索引消费

用法：
  python scripts/parse_pdf.py --input path/to/paper.pdf --out paper_a.json
  python scripts/parse_pdf.py --input paper.docx --out paper_a.json
  python scripts/parse_pdf.py --text - --out paper_a.json < paper.txt
  python scripts/parse_pdf.py --input paper.pdf --pretty

依赖（可选）：
  pdfplumber >= 0.10    —— PDF 解析主路径
  pymupdf (fitz) >= 1.23 —— PDF 回退路径
  python-docx >= 0.8     —— DOCX 支持

任一 PDF 依赖都没装时：
  提示用户安装；pasted_text 路径不依赖第三方库，可用做 fallback

退出码（对齐 pdf-parsing-heuristics.md 第九节）：
  0  成功
  1  文件不存在 / 参数错误
  2  PDF 加密 / docx 损坏
  3  PDF 无文本层（图像 PDF）—— PDF_IMAGE_LAYER_ONLY
  4  依赖库缺失

说明：
  v0.1 POC 目标：单栏 PDF + 常见 section 编号能识别；双栏 / 复杂布局留 v0.2。
  章节识别采用 heuristic（字号 + 编号前缀 + 关键词），非 ML。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

SCRIPT_VERSION = "0.3.0"

# P1-2：解析中间产物默认 cache 路径，与 fetch_arxiv_tex.py 同根，便于统一管理 / 清理
# 优先级：环境变量 > 默认 ~/.cache/paper-quick-reader/parse
PARSE_CACHE_ROOT = Path(os.environ.get(
    "PAPER_QR_PARSE_CACHE",
    str(Path.home() / ".cache" / "paper-quick-reader" / "parse"),
))


def default_cache_path_for(source_label: str) -> Path:
    """为给定输入（路径 / pasted-text 标记）生成稳定的 cache 文件路径。

    用 source_label 的 stem + 短哈希做文件名，避免：
      (a) 路径不同但 stem 相同造成覆盖
      (b) 重启系统丢失（cache 在 ~/.cache，非 /tmp）
    """
    h = hashlib.sha1(source_label.encode("utf-8")).hexdigest()[:8]
    stem = Path(source_label).stem if source_label else "pasted"
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", stem)[:60] or "paper"
    return PARSE_CACHE_ROOT / f"{safe}-{h}.json"

# ============================================================
# 1. 章节标题识别启发式
# ============================================================

SECTION_KEYWORDS = [
    "Abstract",
    "Introduction",
    "Related Work",
    "Background",
    "Preliminaries",
    "Method",
    "Methods",
    "Approach",
    "Methodology",
    "Experiments",
    "Experimental Setup",
    "Evaluation",
    "Results",
    "Analysis",
    "Discussion",
    "Conclusion",
    "Conclusions",
    "Limitations",
    "Future Work",
    "References",
    "Bibliography",
    "Appendix",
    "Acknowledgments",
    "Acknowledgements",
]

SECTION_KEYWORDS_LC = {k.lower() for k in SECTION_KEYWORDS}

SECTION_NUMBER_RE = re.compile(
    r"^\s*(?:"
    r"(?:\d{1,2}(?:\.\d{1,2}){0,2})"     # 1 / 3.2 / 3.2.1
    r"|(?:[A-Z]\.)"                       # A. / B.
    r"|(?:[一二三四五六七八九十]+[、．.])"  # 中文数字编号
    r")"
    r"\s+(.{2,80})\s*$"
)

FIGURE_CAPTION_RE = re.compile(r"^\s*(?:Figure|Fig\.?|图)\s+\d+[:：.]?\s*(.{0,200})", re.IGNORECASE)
TABLE_CAPTION_RE = re.compile(r"^\s*(?:Table|表)\s+\d+[:：.]?\s*(.{0,200})", re.IGNORECASE)

# Header/footer 的候选：纯数字、"Page N of M"、邮箱
HEADER_FOOTER_RE = re.compile(
    r"^(?:\s*\d+\s*|\s*Page\s+\d+\s+of\s+\d+\s*|\S+@\S+\.\S+)\s*$",
    re.IGNORECASE,
)


def is_section_title(line: str) -> Optional[str]:
    """若 line 像章节标题，返回标题本身；否则返回 None。"""
    stripped = line.strip()
    if not stripped or len(stripped) > 100:
        return None

    # 编号开头
    m = SECTION_NUMBER_RE.match(stripped)
    if m:
        return stripped

    # 关键词独立成行
    lc = stripped.lower()
    if lc in SECTION_KEYWORDS_LC:
        return stripped

    # 如 "3 Method" 无点号但首字符数字 + 单词关键词
    parts = stripped.split(None, 1)
    if len(parts) == 2 and parts[0].rstrip(".").isdigit():
        if parts[1].lower() in SECTION_KEYWORDS_LC:
            return stripped

    return None


def is_header_footer(line: str, page_width_chars: int = 120) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if HEADER_FOOTER_RE.match(stripped):
        return True
    return False


# ============================================================
# 2. PDF 解析（优先 pdfplumber；回退 pymupdf）
# ============================================================


def parse_pdf_via_pdfplumber(path: Path) -> dict[str, Any]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        raise ImportError("pdfplumber 未安装，请运行 `pip install pdfplumber`")

    pages_text: list[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            # pdfplumber 0.7–0.10 有 is_encrypted 属性，0.11+ 移除；
            # 都用 getattr 兼容。真加密时下面 extract_text 会抛异常再捕获。
            if getattr(pdf, "is_encrypted", False):
                raise PermissionError("PDF_ENCRYPTED")
            for page in pdf.pages:
                # x_tolerance=1.5 修复 LaTeX / pdfTeX 生成 PDF 的"无空格拼接"问题
                # （常见于 arxiv / ACL / NeurIPS 等会议 PDF）
                text = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
                pages_text.append(text)
    except PermissionError:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypt" in msg:
            raise PermissionError("PDF_ENCRYPTED") from e
        raise

    return _build_result_from_pages(pages_text, source_type="pdf_path", original_path=str(path))


def parse_pdf_via_pymupdf(path: Path) -> dict[str, Any]:
    try:
        import fitz  # type: ignore  # pymupdf
    except ImportError:
        raise ImportError("pymupdf 未安装，请运行 `pip install pymupdf`")

    doc = fitz.open(str(path))
    if getattr(doc, "is_encrypted", False) or getattr(doc, "needs_pass", False):
        raise PermissionError("PDF_ENCRYPTED")
    pages_text = [page.get_text("text") or "" for page in doc]
    doc.close()

    return _build_result_from_pages(pages_text, source_type="pdf_path", original_path=str(path))


def parse_pdf(path: Path) -> dict[str, Any]:
    last_err: Optional[Exception] = None
    for fn in (parse_pdf_via_pdfplumber, parse_pdf_via_pymupdf):
        try:
            return fn(path)
        except ImportError as e:
            last_err = e
            continue
        except PermissionError:
            raise
    raise ImportError(
        "未找到 PDF 解析依赖。请安装 pdfplumber 或 pymupdf：\n"
        "  pip install pdfplumber   # 推荐\n"
        "  pip install pymupdf       # 或备选"
    )


# ============================================================
# 3. DOCX 解析
# ============================================================


def parse_docx(path: Path) -> dict[str, Any]:
    try:
        from docx import Document  # type: ignore
    except ImportError:
        raise ImportError("python-docx 未安装，请运行 `pip install python-docx`")

    doc = Document(str(path))
    # 按段落切；docx 无原生页码 → 以段落编号近似
    paragraphs: list[str] = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    # 每 ~40 段虚拟一页（近似打印 A4 密度）
    page_size = 40
    pages_text: list[str] = []
    for i in range(0, len(paragraphs), page_size):
        pages_text.append("\n".join(paragraphs[i : i + page_size]))
    if not pages_text:
        pages_text = [""]

    return _build_result_from_pages(pages_text, source_type="docx_path", original_path=str(path))


# ============================================================
# 4. Pasted text 解析
# ============================================================


def parse_pasted_text(text: str) -> dict[str, Any]:
    if len(text) < 50:
        raise ValueError("粘贴文本过短（< 50 字）。请提供 ≥ 200 字的论文片段，并尽量附上章节信息。")
    # 粘贴文本无法可靠分页 → 整体视为 1 页（page 会置为 None）
    return _build_result_from_pages(
        [text],
        source_type="pasted_text",
        original_path="",
        page_is_null=True,
    )


# ============================================================
# 5. 通用构建：pages_text → 结构化 JSON
# ============================================================


def _extract_meta(pages_text: list[str]) -> dict[str, Any]:
    """从前两页启发式抽取标题 / 作者 / 年份 / 摘要。"""
    head = "\n".join(pages_text[:2])
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]

    title = lines[0] if lines else ""
    # 去除过长首行（可能是 header）
    if len(title) > 200:
        for ln in lines[1:6]:
            if 10 <= len(ln) <= 200:
                title = ln
                break

    year_match = re.search(r"\b(19|20)\d{2}\b", head)
    year = int(year_match.group(0)) if year_match else None

    abstract = ""
    head_lc = head.lower()
    if "abstract" in head_lc:
        idx = head_lc.index("abstract")
        tail = head[idx + len("abstract") :].lstrip(" :：.\n\r")
        # 截到下一个章节标题或 500 字
        stop = len(tail)
        for kw in ["introduction", "1. introduction", "1 introduction"]:
            i2 = tail.lower().find(kw)
            if 0 < i2 < stop:
                stop = i2
        abstract = tail[: min(stop, 1500)].strip()

    # 作者（启发：摘要前的一行短列表）
    authors: list[str] = []
    for ln in lines[1:5]:
        if "@" in ln or len(ln) > 200:
            continue
        if re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", ln):
            parts = re.split(r"[,，;；]|\sand\s", ln)
            authors = [p.strip(" *†‡1234567890.") for p in parts if 2 < len(p.strip()) < 60]
            authors = [a for a in authors if a]
            if authors:
                break

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": None,
        "abstract": abstract,
    }


def _build_result_from_pages(
    pages_text: list[str],
    *,
    source_type: str,
    original_path: str,
    page_is_null: bool = False,
) -> dict[str, Any]:
    # 图像 PDF 判定
    non_empty = [t for t in pages_text if t.strip()]
    if not non_empty and source_type == "pdf_path":
        raise RuntimeError("PDF_IMAGE_LAYER_ONLY")

    meta = _extract_meta(pages_text)
    meta.update(
        {
            "total_pages": len(pages_text),
            "source_type": source_type,
            "original_path": original_path,
            # P2-1：标记是否真有页码体系。pasted_text 永远 false
            # —— 下游 render_report.py 据此把 page=null 渲染为「（粘贴段·未分页）」
            # 而不是空白；同时 SKILL Step 2 也据此追问用户补章节。
            "paginated": not page_is_null,
        }
    )

    # 构建 blocks + sections
    sections: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    figures_and_tables: list[dict[str, Any]] = []

    current_section_id: Optional[str] = None
    current_section_title: Optional[str] = None
    block_counter = 0
    fig_counter = 0
    tab_counter = 0

    for page_idx, page_text in enumerate(pages_text, start=1):
        page_num: Optional[int] = None if page_is_null else page_idx

        # 先收集 figure/table caption（整行扫描）
        for line in page_text.splitlines():
            fm = FIGURE_CAPTION_RE.match(line)
            if fm:
                fig_counter += 1
                figures_and_tables.append(
                    {
                        "type": "figure",
                        "id": f"fig-{fig_counter}",
                        "page": page_num,
                        "caption": line.strip(),
                    }
                )
                continue
            tm = TABLE_CAPTION_RE.match(line)
            if tm:
                tab_counter += 1
                figures_and_tables.append(
                    {
                        "type": "table",
                        "id": f"tab-{tab_counter}",
                        "page": page_num,
                        "caption": line.strip(),
                    }
                )

        # 切 block：按空行分段，跳过 header/footer
        paragraphs = _split_into_paragraphs(page_text)
        for para in paragraphs:
            first_line = para.splitlines()[0] if para else ""

            # 是否是 section title
            title = is_section_title(first_line)
            if title:
                section_id = f"s-{len(sections)}"
                sections.append(
                    {
                        "id": section_id,
                        "title": title,
                        "first_page": page_num if page_num is not None else 1,
                        "last_page": page_num if page_num is not None else 1,
                    }
                )
                current_section_id = section_id
                current_section_title = title
                # section title 本身不作为 block（除非有后续同段内容）
                remain = "\n".join(para.splitlines()[1:]).strip()
                if not remain:
                    continue
                para_text = remain
            else:
                para_text = para

            if not para_text.strip():
                continue

            block_counter += 1
            blocks.append(
                {
                    "block_id": f"b-{block_counter:04d}",
                    "page": page_num,
                    "section_id": current_section_id or "s-unknown",
                    "section_title": current_section_title or "Unknown",
                    "text": para_text.strip(),
                }
            )
            # 更新当前 section 的 last_page
            if sections and current_section_id == sections[-1]["id"] and page_num is not None:
                sections[-1]["last_page"] = page_num

    # 若完全没识别到 section，兜底整段归 "Document"
    if not sections:
        sections.append(
            {
                "id": "s-0",
                "title": "Document",
                "first_page": 1,
                "last_page": len(pages_text),
            }
        )
        for b in blocks:
            b["section_id"] = "s-0"
            b["section_title"] = "Document"

    references, references_meta = _extract_references(sections, blocks)

    return {
        "parse_version": SCRIPT_VERSION,
        "meta": meta,
        "sections": sections,
        "blocks": blocks,
        "figures_and_tables": figures_and_tables,
        "references": references,
        "references_meta": references_meta,
    }


# ============================================================
# 5.5 References / Bibliography 启发式抽取（v0.3.0 / P0-A）
# ============================================================
#
# 设计目标：
#   - **零依赖** —— 不引入 GROBID（Java 重量级）/ refextract / anystyle
#   - **best-effort** —— 抽不全比抽错强；抽到的字段只填充能确定的 (idx/raw/year/page)，
#                         作者/标题/会议留 None 让 LLM 后续补
#   - 支持的 reference 格式（覆盖 ACL / ICML / NeurIPS / arXiv 多种）：
#       [1]  Smith, J. and Doe, A. (2023). Foo bar baz. NeurIPS.
#       1.   Smith, J. ...
#       (1)  Smith, J. ...
#       Smith, J., Doe, A., 2023. Foo bar. JMLR 24(1), pp.1-10.   ← author-year 风格

REFERENCES_SECTION_RE = re.compile(
    r"^\s*(?:\d+\s*[.\)]\s*)?(references|bibliography|works\s+cited|参考文献)\s*$",
    re.IGNORECASE,
)
REF_NUMBERED_RE = re.compile(r"^\s*(?:\[(\d+)\]|\((\d+)\)|(\d+)\s*[.\)])\s+")
REF_YEAR_RE = re.compile(r"\((\d{4}[a-z]?)\)|(?<![\d-])(\d{4})(?![\d-])")


def _is_references_section(section: dict[str, Any]) -> bool:
    title = (section.get("title") or "").strip()
    return bool(REFERENCES_SECTION_RE.match(title))


def _extract_references(
    sections: list[dict[str, Any]],
    blocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """从已切好的 sections + blocks 中找出 References 段并启发式拆条目。

    返回:
        (references_list, references_meta)
    references_list 即便为空也返回 []（不返回 None），
    references_meta 总是有 extracted/section_pages/extraction_notes 三个键。
    """
    notes: list[str] = []
    ref_section = next((s for s in sections if _is_references_section(s)), None)
    meta: dict[str, Any] = {
        "extracted": False,
        "section_title": None,
        "section_pages": None,
        "extraction_notes": notes,
        "rule_version": "v0.1-heuristic",
    }
    if ref_section is None:
        notes.append("未发现 References / Bibliography 段；常见原因：综述/扫描件/抽取启发式未命中标题")
        return [], meta

    sec_id = ref_section["id"]
    ref_blocks = [b for b in blocks if b.get("section_id") == sec_id]
    if not ref_blocks:
        notes.append("References 段定位到了，但 blocks 里没有内容（可能是 PDF 末尾解析丢失）")
        return [], meta

    # 把 References 段所有 block.text 拼接成一篇，按行扫描，遇到 [N] / N. / (N) 开新条目
    full_text_with_pages: list[tuple[str, Optional[int]]] = []
    for b in ref_blocks:
        for ln in (b.get("text") or "").splitlines():
            full_text_with_pages.append((ln, b.get("page")))

    references: list[dict[str, Any]] = []
    current: Optional[dict[str, Any]] = None

    for line, page in full_text_with_pages:
        stripped = line.strip()
        if not stripped:
            continue
        m = REF_NUMBERED_RE.match(stripped)
        if m:
            if current is not None:
                references.append(_finalize_reference(current))
            idx_str = next((g for g in m.groups() if g is not None), None)
            try:
                idx = int(idx_str) if idx_str else len(references) + 1
            except (TypeError, ValueError):
                idx = len(references) + 1
            current = {
                "idx": idx,
                "raw_lines": [REF_NUMBERED_RE.sub("", stripped, count=1)],
                "page": page,
            }
        else:
            if current is None:
                # 没有编号前缀的 author-year 风格：第一行也算一条
                if not references and _looks_like_reference_line(stripped):
                    current = {
                        "idx": 1,
                        "raw_lines": [stripped],
                        "page": page,
                    }
            else:
                current["raw_lines"].append(stripped)

    if current is not None:
        references.append(_finalize_reference(current))

    meta["extracted"] = bool(references)
    meta["section_title"] = ref_section.get("title")
    meta["section_pages"] = [ref_section.get("first_page"), ref_section.get("last_page")]
    if not references:
        notes.append("References 段定位到了，但启发式未能切分出具体条目（可能格式特殊：脚注式 / 行内式）")
    else:
        notes.append(f"启发式抽取 {len(references)} 条；非可靠字段（authors/title）请由 LLM 二次解析")
    return references, meta


def _finalize_reference(item: dict[str, Any]) -> dict[str, Any]:
    """把累积的 raw_lines 合并成 raw 字符串，并尽力提取 year。"""
    raw = " ".join(item["raw_lines"]).strip()
    raw = re.sub(r"\s+", " ", raw)
    year_match = REF_YEAR_RE.search(raw)
    year: Optional[int] = None
    if year_match:
        token = next((g for g in year_match.groups() if g is not None), None)
        if token:
            digits = re.sub(r"[^\d]", "", token)
            if digits:
                try:
                    y = int(digits[:4])
                    if 1900 <= y <= 2100:
                        year = y
                except ValueError:
                    pass
    return {
        "idx": item["idx"],
        "raw": raw,
        "page": item.get("page"),
        "year": year,
    }


def _looks_like_reference_line(line: str) -> bool:
    """author-year 风格首行判定：含年份 + 大写姓氏 + 句号。"""
    if not REF_YEAR_RE.search(line):
        return False
    if not re.search(r"\b[A-Z][a-zA-Z]+\b", line):
        return False
    return "." in line or "," in line


def _split_into_paragraphs(page_text: str) -> list[str]:
    if not page_text:
        return []
    # 按连续空行切分
    raw = re.split(r"\n\s*\n", page_text)
    paragraphs: list[str] = []
    for chunk in raw:
        # 过滤明显的 header/footer 整段
        lines = [ln for ln in chunk.splitlines() if not is_header_footer(ln)]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


# ============================================================
# 6. CLI
# ============================================================


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse paper PDF/DOCX/pasted text into structured (text, page, section) JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i", type=str, help="Path to .pdf or .docx")
    group.add_argument(
        "--text",
        "-t",
        type=str,
        help="Paste text directly; use '-' to read from stdin.",
    )
    parser.add_argument("--out", "-o", type=str, default="-", help="Output file path; '-' for stdout (default)")
    parser.add_argument(
        "--cache",
        action="store_true",
        help=(
            "Write to default cache location instead of stdout/--out. "
            f"Default: {PARSE_CACHE_ROOT}/<input-stem>-<hash>.json "
            "(override via $PAPER_QR_PARSE_CACHE)"
        ),
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indent=2")
    parser.add_argument("--label", type=str, default=None, help="Optional paper label for meta")
    parser.add_argument(
        "--read-cache",
        action="store_true",
        help=(
            "P1-B (v0.4.0): Cache-read mode for follow-up Q&A. "
            "Check cache hit first; on hit, print cached JSON and exit 0 "
            "without re-parsing PDF/DOCX. On miss, fall back to fresh parse "
            "(combine with --cache to write the fresh result)."
        ),
    )

    args = parser.parse_args(argv)

    if args.read_cache and args.input:
        cache_hit_path = default_cache_path_for(args.input)
        if cache_hit_path.exists():
            try:
                cached = cache_hit_path.read_text(encoding="utf-8")
                if args.out == "-" and not args.cache:
                    sys.stdout.write(cached + ("\n" if not cached.endswith("\n") else ""))
                else:
                    out_path = (
                        cache_hit_path
                        if args.cache
                        else Path(args.out).expanduser().resolve()
                    )
                    if out_path != cache_hit_path:
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        out_path.write_text(cached, encoding="utf-8")
                _err(f"cache hit: {cache_hit_path}（跳过重新解析）")
                return 0
            except OSError as e:
                _err(f"cache 读取失败 ({e})，回退到重新解析")

    try:
        if args.input:
            path = Path(args.input).expanduser().resolve()
            if not path.exists():
                _err(f"文件不存在: {path}")
                return 1
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                try:
                    result = parse_pdf(path)
                except PermissionError:
                    _err("PDF 已加密，无法解析。请先解密后重试。")
                    return 2
                except RuntimeError as e:
                    if str(e) == "PDF_IMAGE_LAYER_ONLY":
                        _err("PDF 无文本层（扫描件或纯图像 PDF）。本 Skill 拒绝 OCR，请转为文本层 PDF 后重试。")
                        return 3
                    raise
                except ImportError as e:
                    _err(str(e))
                    return 4
            elif suffix == ".docx":
                try:
                    result = parse_docx(path)
                except ImportError as e:
                    _err(str(e))
                    return 4
            else:
                _err(f"不支持的文件后缀: {suffix}（仅支持 .pdf / .docx）")
                return 1
        else:
            if args.text == "-":
                text = sys.stdin.read()
            else:
                text = args.text or ""
            try:
                result = parse_pasted_text(text)
            except ValueError as e:
                _err(str(e))
                return 1
    except Exception as e:  # noqa: BLE001
        _err(f"解析异常: {type(e).__name__}: {e}")
        return 1

    if args.label:
        result["meta"]["label"] = args.label

    output = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.cache:
        # P1-2：cache 优先级最高，覆盖 --out
        source_label = args.input or "pasted-text"
        out_path = default_cache_path_for(source_label)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        _err(f"已写入 cache: {out_path}")
    elif args.out == "-":
        sys.stdout.write(output + "\n")
    else:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        _err(f"已写入: {out_path}")

    return 0


def _err(msg: str) -> None:
    sys.stderr.write(f"[parse_pdf] {msg}\n")


if __name__ == "__main__":
    sys.exit(main())
