#!/usr/bin/env python3
"""
normalize.py — 专家包前置规范化（确定性、不修改业务内容）

执行项：
  N01 BOM 移除（plugin.json / settings.json / *.md）
  N02 编码归一（非 UTF-8 → UTF-8）
  N03 换行符统一（CRLF → LF）
  N04 plugin.json 字段顺序按 §三 重排（保留所有未知字段）
  N05 settings.json 字段排序（仅 agent 字段验证）
  N06 Agent MD frontmatter 字段顺序（name → description → displayName → profession → maxTurns → tools）

不做的事：
  - 不修改 plugin.json 业务字段值
  - 不修改 Agent MD 正文内容
  - 不删除任何文件（即使是空目录）—— 删除清理不属于规范化职责

用法：
  python normalize.py <expert_dir> [--output-file <path>]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from review_utils import (  # noqa: E402
    write_output_file, read_text_safe, read_json_safe, ensure_dir,
)


# ── plugin.json 字段顺序（CODEBUDDY.md §三） ──────────

PLUGIN_JSON_FIELD_ORDER = [
    # 基础字段（必填）
    "name",
    "version",
    "description",
    # 可选基础
    "author",
    "homepage",
    "license",
    "keywords",
    # 类型
    "expertType",
    "agentName",
    "teamInfo",
    # 资源
    "agents",
    "skills",
    # 展示字段
    "displayName",
    "profession",
    "displayDescription",
    "avatar",
    "categoryId",
    "defaultInitPrompt",
    "tags",
    "quickPrompts",
    # Team 专用
    "members",
]


# ── Agent MD frontmatter 字段顺序 ─────────────────────

AGENT_FRONTMATTER_ORDER = [
    "name",
    "description",
    "displayName",
    "profession",
    "maxTurns",
    "tools",
]


# ── 二进制/资源文件扩展名（不归一） ────────────────────

BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
                ".zip", ".tar", ".gz", ".woff", ".woff2", ".ttf", ".eot"}


# ── 步骤 1: 文件级编码/换行归一 ───────────────────────

def normalize_text_file(file_path: Path, changes: list) -> None:
    """对单个文本文件执行 BOM 移除、UTF-8 转码、CRLF→LF。"""
    if file_path.suffix.lower() in BINARY_EXTS:
        return
    try:
        raw = file_path.read_bytes()
    except Exception:
        return

    original = raw
    modified = False

    # N01 BOM 移除
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
        modified = True
        changes.append({"file": str(file_path), "change": "BOM removed"})

    # N02 编码归一（尝试 UTF-8 解码，失败则尝试 GBK）
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gbk")
            modified = True
            changes.append({"file": str(file_path), "change": "GBK → UTF-8"})
        except Exception:
            return  # 无法处理，跳过

    # N03 换行符统一
    if "\r\n" in text or "\r" in text:
        new_text = text.replace("\r\n", "\n").replace("\r", "\n")
        if new_text != text:
            text = new_text
            modified = True
            changes.append({"file": str(file_path), "change": "CRLF → LF"})

    # 若 raw 原本是 UTF-8 + LF + 无 BOM，跳过写入
    if modified or raw != original:
        file_path.write_text(text, encoding="utf-8", newline="\n")


def walk_text_files(root: Path) -> list[Path]:
    """遍历专家包内所有文本文件。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过潜在的二进制目录
        if any(skip in dirpath for skip in ["__pycache__", "node_modules", ".git"]):
            continue
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in BINARY_EXTS:
                out.append(p)
    return out


# ── 步骤 2: plugin.json 字段排序 ──────────────────────

def reorder_plugin_json(plugin_json_path: Path, changes: list) -> None:
    """按 §三 字段顺序重排 plugin.json（保留所有未知字段在末尾）。"""
    data = read_json_safe(plugin_json_path)
    if not isinstance(data, dict):
        return

    ordered = {}
    for k in PLUGIN_JSON_FIELD_ORDER:
        if k in data:
            ordered[k] = data[k]
    # 保留未知字段（按原顺序）
    for k, v in data.items():
        if k not in ordered:
            ordered[k] = v

    if list(ordered.keys()) != list(data.keys()):
        plugin_json_path.write_text(
            json.dumps(ordered, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        changes.append({
            "file": str(plugin_json_path),
            "change": "plugin.json fields reordered",
            "old_order": list(data.keys()),
            "new_order": list(ordered.keys()),
        })


# ── 步骤 3: Agent MD frontmatter 字段顺序 ─────────────

def reorder_agent_frontmatter(md_path: Path, changes: list) -> None:
    """重排 agents/*.md frontmatter 字段顺序，保留正文不变。

    仅处理键值对在同一行的简单 frontmatter；不处理多行嵌套对象（如 displayName: {en, zh}）
    的字段重排（这类字段会原样保留）。
    """
    text = read_text_safe(md_path)
    if not text.startswith("---\n"):
        return

    end = text.find("\n---\n", 4)
    if end == -1:
        return

    fm_block = text[4:end]
    body = text[end + 5:]

    # 解析 frontmatter 为有序列表（保留多行块）
    blocks: list[tuple[str, str]] = []  # (key, full_block_text_including_newline)
    current_key: str | None = None
    current_lines: list[str] = []

    def flush():
        if current_key is not None:
            blocks.append((current_key, "\n".join(current_lines) + "\n"))

    for line in fm_block.split("\n"):
        if line and line[0] not in (" ", "\t", "-"):
            # 新键
            m = line.split(":", 1)
            if len(m) == 2 and m[0].strip() and not m[0].startswith("#"):
                # flush 上一块
                flush()
                current_key = m[0].strip()
                current_lines = [line]
                continue
        current_lines.append(line)
    flush()

    # 按 AGENT_FRONTMATTER_ORDER 重排
    ordered_blocks: list[tuple[str, str]] = []
    seen = set()
    for k in AGENT_FRONTMATTER_ORDER:
        for bk, bv in blocks:
            if bk == k and bk not in seen:
                ordered_blocks.append((bk, bv))
                seen.add(bk)
    # 未知字段保留
    for bk, bv in blocks:
        if bk not in seen:
            ordered_blocks.append((bk, bv))
            seen.add(bk)

    new_fm = "".join(b for _, b in ordered_blocks).rstrip("\n")
    new_text = f"---\n{new_fm}\n---\n{body}"

    if new_text != text and [k for k, _ in ordered_blocks] != [k for k, _ in blocks]:
        md_path.write_text(new_text, encoding="utf-8", newline="\n")
        changes.append({
            "file": str(md_path),
            "change": "agent frontmatter reordered",
            "new_order": [k for k, _ in ordered_blocks],
        })


# ── 主入口 ────────────────────────────────────────────

def normalize_expert_dir(expert_dir: Path) -> dict:
    """对一个专家包目录执行全部 N01-N06 归一。"""
    changes: list = []
    warnings: list = []

    if not expert_dir.is_dir():
        return {"ok": False, "error": f"目录不存在: {expert_dir}", "changes": []}

    # Step 1: 文本文件 BOM/编码/换行
    for fp in walk_text_files(expert_dir):
        try:
            normalize_text_file(fp, changes)
        except Exception as e:
            warnings.append({"file": str(fp), "warning": str(e)})

    # Step 2: plugin.json 字段排序
    plugin_json = None
    for cand in [".codebuddy-plugin/plugin.json", ".workbuddy-plugin/plugin.json"]:
        p = expert_dir / cand
        if p.exists():
            plugin_json = p
            break
    if plugin_json:
        try:
            reorder_plugin_json(plugin_json, changes)
        except Exception as e:
            warnings.append({"file": str(plugin_json), "warning": str(e)})
    else:
        warnings.append({"warning": "plugin.json 未找到（.codebuddy-plugin/ 或 .workbuddy-plugin/）"})

    # Step 3: agents/*.md frontmatter 字段排序
    agents_dir = expert_dir / "agents"
    if agents_dir.is_dir():
        for md in agents_dir.glob("*.md"):
            try:
                reorder_agent_frontmatter(md, changes)
            except Exception as e:
                warnings.append({"file": str(md), "warning": str(e)})

    return {
        "ok": True,
        "expert_dir": str(expert_dir),
        "changes": changes,
        "warnings": warnings,
        "summary": {
            "files_modified": len({c["file"] for c in changes if "file" in c}),
            "warnings_count": len(warnings),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="专家包前置规范化")
    parser.add_argument("expert_dir", help="专家包目录路径")
    parser.add_argument("--output-file", help="输出 JSON 路径（推荐，避免 PowerShell 编码截断）")
    args = parser.parse_args()

    expert_dir = Path(args.expert_dir).resolve()
    result = normalize_expert_dir(expert_dir)

    plugin_name = expert_dir.name
    summary = (
        f"normalize 完成：修改 {result['summary']['files_modified']} 个文件，"
        f"{result['summary']['warnings_count']} 个警告"
    )

    write_output_file(args.output_file, result, stdout_summary=summary)
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
