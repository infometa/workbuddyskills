#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_outline.py —— 知识框架梳理 Skill · Step 2 材料骨架解析(v0.5.0)

定位:
  本脚本仅做"标题级"骨架抽取——把 markdown / txt / pasted_text(以及降级处理的 docx)
  解析成扁平的 headings 数组,**不构建知识树**(树由 LLM 在 Step 3 据此重组,
  允许合并 / 重排 / 重命名 / 引入未在原文出现的概括节点)。

输入(--input input.json,与 SKILL.md / input-schema.md 对齐):
  - 顶层 material_files: MaterialFile[]
  - 每条 {path, type, label?, content_inline?}

输出(--out outline.json):
  - files_processed[]:成功解析的文件清单 + 每文件的 heading 数
  - headings[]:扁平 heading 流(file_index, level, title, line, char_offset, method, raw)
  - rejected_files[]:type ∈ {pdf, image, webpage_url, video_url, audio_path} 直接拒绝
  - stats:by_level / by_method / max_depth / estimated_total_nodes / over_node_limit
  - warnings[]:启发式不确定 / docx 降级 / 文件超过字符上限等

退出码:
  0  正常解析(不管是否有 rejected_files / 启发式 warnings)
  1  参数 / 文件读取错误
  2  input.json 缺 material_files 或全部文件被拒
  3  解析后 0 个 heading(LLM 应改走 topic_only 模式)

CLI:
  python3 scripts/parse_outline.py --input input.json --out outline.json --pretty
  python3 scripts/parse_outline.py --input input.json --out outline.json --quiet

设计原则:
  1. 零外部依赖:即使 docx 也降级用 zip + xml.etree(标准库)解析 Heading 样式
  2. 解析方法用 method 字段标注(markdown_atx / markdown_setext / heuristic_chapter /
     heuristic_numeric / heuristic_chinese_序号 / heuristic_section_sign / docx_heading_style),
     便于 LLM / 用户审计
  3. 同一行可能匹配多种启发式 → 取最可信(优先级 markdown > 章节关键字 > 数字编号 > 中文序号 > §)
  4. 识别上限:单文件 200,000 字符 / 全部 headings 上限 1000 → 超过截断 + warning

详细启发式规则见 references/outline-parsing-heuristics.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "0.5.0"
SKILL_VERSION = "0.5.0"

LIMITS = {
    "markdown_max_chars": 200_000,
    "txt_max_chars": 100_000,
    "pasted_text_max_chars": 100_000,
    "docx_max_paragraphs": 5_000,
    "max_total_headings": 1_000,
    "max_depth": 5,
}

REJECTED_TYPES = {"pdf", "image", "webpage_url", "video_url", "audio_path"}
ACCEPTED_TYPES = {"markdown", "txt", "pasted_text", "docx"}

# ---------- markdown 解析 ---------- #

# ATX-style: ^#{1,6} title (允许尾部 #)
ATX_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")

# Setext-style: 上一行是标题,下一行整行都是 = 或 -
SETEXT_H1_RE = re.compile(r"^=+\s*$")
SETEXT_H2_RE = re.compile(r"^-+\s*$")


def parse_markdown(text: str, file_index: int) -> tuple[list[dict], list[str]]:
    """解析 markdown 文件,返回 (headings, warnings)。
    - 同时支持 ATX (#) 与 Setext (===)
    - 跳过 fenced code block(``` 包裹)与 indented code block(4 空格起头)
    - level 上限 6,level=1 对应 #
    """
    headings: list[dict] = []
    warnings: list[str] = []
    lines = text.split("\n")

    in_fenced = False
    fenced_marker = ""
    char_offset = 0

    for idx, raw_line in enumerate(lines):
        line = raw_line
        line_len = len(raw_line) + 1  # +1 是换行符

        stripped = line.lstrip()
        # fenced code block 切换
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fenced:
                in_fenced = True
                fenced_marker = marker
            elif stripped.startswith(fenced_marker):
                in_fenced = False
                fenced_marker = ""
            char_offset += line_len
            continue
        if in_fenced:
            char_offset += line_len
            continue

        # indented code block(4 空格 / 1 个 \t 开头),不在引用 / 列表内时整行跳过
        # (此处简化:对空行后的第一行,若以 4 空格开头,视为代码块)
        if line.startswith("    ") or line.startswith("\t"):
            char_offset += line_len
            continue

        # ATX
        m = ATX_RE.match(line.rstrip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if title and 1 <= level <= LIMITS["max_depth"] + 1:
                headings.append({
                    "file_index": file_index,
                    "level": min(level, LIMITS["max_depth"]),
                    "title": title,
                    "line": idx + 1,
                    "char_offset": char_offset,
                    "method": "markdown_atx",
                    "raw": line.rstrip(),
                })
            char_offset += line_len
            continue

        # Setext: 当前行是 ==/--, 上一行是非空文本 → 上一行 = 标题
        if idx > 0 and line.rstrip():
            prev = lines[idx - 1].rstrip()
            if prev and not ATX_RE.match(prev):
                if SETEXT_H1_RE.match(line.rstrip()):
                    headings.append({
                        "file_index": file_index,
                        "level": 1,
                        "title": prev.strip(),
                        "line": idx,
                        "char_offset": char_offset - len(lines[idx - 1]) - 1,
                        "method": "markdown_setext",
                        "raw": prev + "\n" + line.rstrip(),
                    })
                elif SETEXT_H2_RE.match(line.rstrip()) and len(line.rstrip()) >= 2:
                    headings.append({
                        "file_index": file_index,
                        "level": 2,
                        "title": prev.strip(),
                        "line": idx,
                        "char_offset": char_offset - len(lines[idx - 1]) - 1,
                        "method": "markdown_setext",
                        "raw": prev + "\n" + line.rstrip(),
                    })

        char_offset += line_len

    if not headings:
        warnings.append("markdown 未识别到任何标题(无 # / 无 ===)→ 建议改用 txt heuristic 或 topic_only")
    return headings, warnings


# ---------- txt / pasted_text 启发式 ---------- #

CHINESE_NUM_CHARS = "零一二三四五六七八九十百千万〇○两壹贰叁肆伍陆柒捌玖拾佰仟"

CHAPTER_RE = re.compile(rf"^第[{CHINESE_NUM_CHARS}\d]+[章篇编]\s*")
SECTION_RE = re.compile(rf"^第[{CHINESE_NUM_CHARS}\d]+[节回讲课]\s*")
NUMERIC_L1_RE = re.compile(r"^(\d{1,2})\s*[、\.．]\s*\S")
NUMERIC_L2_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s+\S")
NUMERIC_L2B_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s*[、\.．]\s*\S")
NUMERIC_L3_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{1,2})\s+\S")
NUMERIC_L4_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{1,2})\.(\d{1,2})\s+\S")
CHINESE_SEQ_L1_RE = re.compile(rf"^[{CHINESE_NUM_CHARS}]+[、\.．]\s*\S")
CHINESE_SEQ_L2_RE = re.compile(rf"^[（(][{CHINESE_NUM_CHARS}]+[）)]\s*\S")
SECTION_SIGN_L1_RE = re.compile(r"^§\s*\d+\s+\S")
SECTION_SIGN_L2_RE = re.compile(r"^§\s*\d+\.\d+\s+\S")
SECTION_SIGN_L3_RE = re.compile(r"^§\s*\d+\.\d+\.\d+\s+\S")
LATIN_L1_RE = re.compile(r"^Chapter\s+\d+", re.IGNORECASE)
LATIN_L2_RE = re.compile(r"^Section\s+\d+", re.IGNORECASE)
LETTER_L2_RE = re.compile(r"^[A-Z]\.\s+\S")

PART_RE = re.compile(rf"^第[{CHINESE_NUM_CHARS}\d]+部分\s*")


def detect_heuristic(line: str) -> tuple[int, str] | None:
    """返回 (level, method) 或 None。优先级从可信度高到低。"""
    s = line.strip()
    if not s:
        return None

    if PART_RE.match(s):
        return (1, "heuristic_part")
    if CHAPTER_RE.match(s):
        return (1, "heuristic_chapter")
    if SECTION_RE.match(s):
        return (2, "heuristic_section")

    if LATIN_L1_RE.match(s):
        return (1, "heuristic_latin_chapter")
    if LATIN_L2_RE.match(s):
        return (2, "heuristic_latin_section")

    if NUMERIC_L4_RE.match(s):
        return (4, "heuristic_numeric")
    if NUMERIC_L3_RE.match(s):
        return (3, "heuristic_numeric")
    if NUMERIC_L2_RE.match(s) or NUMERIC_L2B_RE.match(s):
        return (2, "heuristic_numeric")
    if NUMERIC_L1_RE.match(s):
        # 限制:仅当后接较短文本或已存在 L2 时,1. / 2. 才视为 H1;
        # 这里宽松接受,LLM 在 Step 3 会再判
        return (1, "heuristic_numeric")

    if SECTION_SIGN_L3_RE.match(s):
        return (3, "heuristic_section_sign")
    if SECTION_SIGN_L2_RE.match(s):
        return (2, "heuristic_section_sign")
    if SECTION_SIGN_L1_RE.match(s):
        return (1, "heuristic_section_sign")

    if CHINESE_SEQ_L2_RE.match(s):
        return (2, "heuristic_chinese_seq")
    if CHINESE_SEQ_L1_RE.match(s):
        # 中文序号"一、二、"作为 L1,但短句优先(避免误识别正文)
        if len(s) <= 40:
            return (1, "heuristic_chinese_seq")

    if LETTER_L2_RE.match(s):
        return (2, "heuristic_letter")

    return None


def parse_txt(text: str, file_index: int) -> tuple[list[dict], list[str]]:
    headings: list[dict] = []
    warnings: list[str] = []
    lines = text.split("\n")
    char_offset = 0
    for idx, line in enumerate(lines):
        line_len = len(line) + 1
        # 仅扫描前 200 字符内的疑似标题(避免行内模式爆炸)
        scan = line[:200]
        result = detect_heuristic(scan)
        if result is not None:
            level, method = result
            title = line.strip()
            # 过长行强制截断(标题不应超过 80 字符,超过则 warning + 截断)
            if len(title) > 80:
                warnings.append(
                    f"file_index={file_index} line={idx+1} 标题超 80 字符,已截断(method={method})"
                )
                title = title[:80] + "…"
            headings.append({
                "file_index": file_index,
                "level": min(level, LIMITS["max_depth"]),
                "title": title,
                "line": idx + 1,
                "char_offset": char_offset,
                "method": method,
                "raw": line.rstrip(),
            })
        char_offset += line_len

    if not headings:
        warnings.append(
            "txt 未识别到任何启发式标题(无第 X 章 / 1.1 / § / 中文序号)→ "
            "建议改用 markdown 加 # 前缀,或回退 topic_only 模式"
        )
    return headings, warnings


# ---------- docx 降级解析 ---------- #

DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

DOCX_HEADING_STYLE_RE = re.compile(r"^Heading\s*(\d+)$", re.IGNORECASE)


def parse_docx(path: Path, file_index: int) -> tuple[list[dict], list[str], int]:
    """标准库 zip + xml.etree 解析 docx 的 Heading 1/2/3 段落样式。
    返回 (headings, warnings, paragraph_count)
    """
    headings: list[dict] = []
    warnings: list[str] = []
    paragraph_count = 0

    try:
        with zipfile.ZipFile(path) as zf:
            with zf.open("word/document.xml") as f:
                data = f.read()
    except (zipfile.BadZipFile, KeyError) as e:
        warnings.append(f"file_index={file_index} docx 解析失败({e}),按 0 标题处理")
        return [], warnings, 0

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        warnings.append(f"file_index={file_index} docx XML 解析失败({e})")
        return [], warnings, 0

    body = root.find("w:body", DOCX_NS)
    if body is None:
        return [], warnings, 0

    for p_idx, p in enumerate(body.findall("w:p", DOCX_NS)):
        paragraph_count += 1
        if paragraph_count > LIMITS["docx_max_paragraphs"]:
            warnings.append(
                f"file_index={file_index} docx 段落超 {LIMITS['docx_max_paragraphs']},已截断"
            )
            break
        # 段落样式
        pPr = p.find("w:pPr", DOCX_NS)
        if pPr is None:
            continue
        pStyle = pPr.find("w:pStyle", DOCX_NS)
        if pStyle is None:
            continue
        style_val = pStyle.get(f"{{{DOCX_NS['w']}}}val", "")
        m = DOCX_HEADING_STYLE_RE.match(style_val)
        if not m:
            continue
        level = int(m.group(1))
        if level < 1 or level > LIMITS["max_depth"]:
            continue
        # 文本
        text_parts = [t.text or "" for t in p.findall(".//w:t", DOCX_NS)]
        title = "".join(text_parts).strip()
        if not title:
            continue
        headings.append({
            "file_index": file_index,
            "level": level,
            "title": title,
            "line": p_idx + 1,
            "char_offset": -1,  # docx 无字符偏移概念
            "method": "docx_heading_style",
            "raw": f"<Heading{level}> {title}",
        })

    if not headings:
        warnings.append(
            f"file_index={file_index} docx 未识别到 Heading 1/2/3 样式段落 → "
            "请确认作者使用 Word 内置「标题」样式而非粗体大字"
        )
    return headings, warnings, paragraph_count


# ---------- 主流程 ---------- #

def truncate_text(text: str, limit: int, type_name: str) -> tuple[str, str | None]:
    if len(text) <= limit:
        return text, None
    return (
        text[:limit],
        f"{type_name} 字符数 {len(text)} 超过上限 {limit},已截断",
    )


def normalize_title(title: str) -> str:
    """NFC 归一化 + 去多余空格,便于后续 LLM 排重。"""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", title)).strip()


def parse_one(mf: dict, file_index: int, input_dir: Path) -> dict:
    """处理单个 material_file,返回结构化结果。"""
    path_str = mf.get("path", "")
    mtype = mf.get("type", "")
    label = mf.get("label", "")
    content_inline = mf.get("content_inline", "")

    out: dict[str, Any] = {
        "file_index": file_index,
        "path": path_str,
        "type": mtype,
        "label": label,
        "headings_extracted": 0,
        "char_count": 0,
        "warnings": [],
    }

    if mtype in REJECTED_TYPES:
        return {**out, "rejected": True, "reject_reason": f"type={mtype} 在拒绝列表"}

    if mtype not in ACCEPTED_TYPES:
        return {**out, "rejected": True, "reject_reason": f"未知 type: {mtype}"}

    text = ""
    src_path: Path | None = None

    if mtype == "pasted_text":
        if not content_inline:
            return {**out, "rejected": True, "reject_reason": "pasted_text 缺 content_inline"}
        text = content_inline
    else:
        if not path_str:
            return {**out, "rejected": True, "reject_reason": f"{mtype} 缺 path"}
        src_path = Path(path_str)
        if not src_path.is_absolute():
            src_path = (input_dir / path_str).resolve()
        if not src_path.exists():
            return {**out, "rejected": True, "reject_reason": f"路径不存在: {src_path}"}
        if mtype == "docx":
            heads, warns, pcount = parse_docx(src_path, file_index)
            out["headings"] = [{**h, "title": normalize_title(h["title"])} for h in heads]
            out["warnings"].extend(warns)
            out["headings_extracted"] = len(out["headings"])
            out["paragraph_count"] = pcount
            return out
        try:
            text = src_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return {**out, "rejected": True, "reject_reason": f"读取失败: {e}"}

    out["char_count"] = len(text)

    if mtype == "markdown":
        text, t_warn = truncate_text(text, LIMITS["markdown_max_chars"], "markdown")
        if t_warn:
            out["warnings"].append(t_warn)
        heads, warns = parse_markdown(text, file_index)
    elif mtype == "txt":
        text, t_warn = truncate_text(text, LIMITS["txt_max_chars"], "txt")
        if t_warn:
            out["warnings"].append(t_warn)
        heads, warns = parse_txt(text, file_index)
    else:  # pasted_text
        text, t_warn = truncate_text(text, LIMITS["pasted_text_max_chars"], "pasted_text")
        if t_warn:
            out["warnings"].append(t_warn)
        heads, warns = parse_txt(text, file_index)

    out["headings"] = [{**h, "title": normalize_title(h["title"])} for h in heads]
    out["headings_extracted"] = len(out["headings"])
    out["warnings"].extend(warns)
    return out


def build_outline(input_data: dict, input_path: Path) -> dict:
    materials = input_data.get("material_files") or []
    input_dir = input_path.parent.resolve()

    files_processed: list[dict] = []
    rejected_files: list[dict] = []
    all_headings: list[dict] = []
    global_warnings: list[str] = []

    for i, mf in enumerate(materials):
        result = parse_one(mf, i, input_dir)
        if result.get("rejected"):
            rejected_files.append({
                "file_index": i,
                "path": result.get("path"),
                "type": result.get("type"),
                "reason": result.get("reject_reason"),
            })
            continue

        heads = result.pop("headings", [])
        all_headings.extend(heads)
        files_processed.append({
            k: v for k, v in result.items()
            if k not in {"rejected", "reject_reason"}
        })

    if len(all_headings) > LIMITS["max_total_headings"]:
        global_warnings.append(
            f"全部 headings {len(all_headings)} 超过上限 {LIMITS['max_total_headings']},"
            f"已截断;建议拆分为多门课分别梳理"
        )
        all_headings = all_headings[: LIMITS["max_total_headings"]]

    by_level: dict[str, int] = {}
    by_method: dict[str, int] = {}
    for h in all_headings:
        by_level[str(h["level"])] = by_level.get(str(h["level"]), 0) + 1
        by_method[h["method"]] = by_method.get(h["method"], 0) + 1
    max_depth = max((h["level"] for h in all_headings), default=0)

    estimated_total_nodes = 1 + len(all_headings)  # +1 是根节点
    over_node_limit = estimated_total_nodes > 100

    if over_node_limit:
        global_warnings.append(
            f"预估总节点 {estimated_total_nodes} > 100(SKILL.md 核心原则 9),"
            f"建议 LLM 在 Step 3 合并到 ≤ 100"
        )

    return {
        "outline_version": SCRIPT_VERSION,
        "skill_version": SKILL_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_path": str(input_path.resolve()),
        "files_processed": files_processed,
        "rejected_files": rejected_files,
        "headings": all_headings,
        "stats": {
            "total_files_accepted": len(files_processed),
            "total_files_rejected": len(rejected_files),
            "total_headings": len(all_headings),
            "by_level": by_level,
            "by_method": by_method,
            "max_depth": max_depth,
            "estimated_total_nodes": estimated_total_nodes,
            "over_node_limit": over_node_limit,
        },
        "warnings": global_warnings,
        "next_step_hint": (
            "LLM 在 Step 3/4 据此 outline 重组 framework_tree(允许合并 / 重排 / 重命名 / "
            "引入未在原文出现的概括节点);每个节点 evidence_source = user_material 时,"
            "evidence_locator 必须填 {file: files_processed[i].path, section: title, "
            "excerpt: 原文 ≥ 8 字符片段},供 verify_provenance.py 做 ngram 校验。"
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="知识框架材料骨架解析")
    p.add_argument("--input", required=True, help="input.json 路径")
    p.add_argument("--out", required=True, help="outline.json 输出路径")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--quiet", action="store_true", help="不打印 stderr 进度")
    args = p.parse_args()

    ipath = Path(args.input)
    if not ipath.exists():
        print(f"[parse_outline] 错误: --input 不存在 {ipath}", file=sys.stderr)
        return 1

    try:
        input_data = json.loads(ipath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[parse_outline] 错误: input.json 解析失败: {e}", file=sys.stderr)
        return 1

    materials = input_data.get("material_files") or []
    if not materials:
        print(
            "[parse_outline] 错误: input.json.material_files 为空 → "
            "应走 topic_only 模式,无需 parse_outline",
            file=sys.stderr,
        )
        return 2

    outline = build_outline(input_data, ipath)

    if outline["stats"]["total_files_accepted"] == 0:
        print(
            f"[parse_outline] 错误: 全部 {len(materials)} 个文件被拒"
            f"({[r['reason'] for r in outline['rejected_files']]})",
            file=sys.stderr,
        )
        return 2

    out_text = json.dumps(outline, ensure_ascii=False, indent=2 if args.pretty else None)
    Path(args.out).write_text(out_text + "\n", encoding="utf-8")

    if not args.quiet:
        s = outline["stats"]
        print(
            f"[parse_outline] ✓ 文件 {s['total_files_accepted']}(拒 {s['total_files_rejected']})"
            f" · 标题 {s['total_headings']}(深度 {s['max_depth']})"
            f" · 预估节点 {s['estimated_total_nodes']}"
            f"{'  ⚠️ 超 100' if s['over_node_limit'] else ''}"
            f" → {args.out}",
            file=sys.stderr,
        )

    if outline["stats"]["total_headings"] == 0:
        print(
            "[parse_outline] 警告: 0 个标题被识别 → "
            "LLM 应改走 topic_only 模式或手工补 # 前缀重跑",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
