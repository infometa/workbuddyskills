#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
埃及战略顾问 Corpus Manager — 自动化语料整理与状态索引生成器

职责：
1. 扫描下载区/缓存区，将文件按类型归档到标准目录：
   /Reference_Texts, /Databases, /Analysis_Reports
2. 维护 .last_corpus_sync.json 状态记录
3. 生成/更新 Corpus_Index.md 状态清单
4. 支持“每月 1 号全量整理” + “强制补偿”机制

调度逻辑：
- 默认每月 1 号执行全量整理
- 若距上次成功执行 >= 30 天 → 强制补偿
- 若跨越自然月且上月未执行 → 强制补偿
- 使用 --check 仅自检后执行；--force 跳过检查

Usage:
    python scripts/corpus_manager.py                  # 按日期/状态判断是否执行
    python scripts/corpus_manager.py --check        # 仅自检，条件满足才执行（推荐自动化）
    python scripts/corpus_manager.py --force        # 强制立即执行
    python scripts/corpus_manager.py --dry-run      # 模拟执行，不移动/不写入
    python scripts/corpus_manager.py --move         # 归档时移动而非复制（默认复制）
"""

import argparse
import datetime
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Optional PDF support
HAS_PYPDF2 = False
PyPDF2 = None
try:
    import PyPDF2 as _PyPDF2

    PyPDF2 = _PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    pass

# Default root: the plugin directory where this script lives (../.. from scripts/)
DEFAULT_ROOT = Path(__file__).resolve().parent.parent

# Standard corpus directories with Chinese labels
CATEGORY_DIRS: Dict[str, str] = {
    "Reference_Texts": "参考文本",
    "Databases": "本地数据库",
    "Analysis_Reports": "补充分析报告",
}

# Source directories to scan (relative to root). Missing dirs are silently skipped.
DEFAULT_SOURCES = [
    "datasets",
    "reports",
    "references",
    "api_modules",
    "downloads",
    "cache",
    "temp",
]

STATE_FILE = ".last_corpus_sync.json"
INDEX_FILE = "Corpus_Index.md"

# Exclusion patterns
EXCLUDE_NAMES = {
    STATE_FILE,
    INDEX_FILE,
    ".gitkeep",
    ".gitignore",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
}
EXCLUDE_EXTS = {
    ".py",
    ".pyc",
    ".pyo",
    ".exe",
    ".dll",
    ".bat",
    ".ps1",
    ".sh",
    ".codebuddy-plugin",
}


def load_state(root: Path) -> Dict:
    """读取 .last_corpus_sync.json，不存在返回空字典。"""
    state_path = root / STATE_FILE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] 无法读取状态文件 {state_path}: {e}", file=sys.stderr)
    return {}


def save_state(root: Path, state: Dict) -> None:
    """写入 .last_corpus_sync.json。"""
    state_path = root / STATE_FILE
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def should_run(root: Path, force: bool = False) -> Tuple[bool, str]:
    """
    判断是否应该执行整理。
    返回 (should_run, reason)
    """
    if force:
        return True, "强制模式（--force）"

    today = datetime.date.today()
    if today.day == 1:
        return True, "每月 1 号全量整理触发"

    state = load_state(root)
    last_run_str = state.get("last_run_date")
    if not last_run_str:
        return True, "首次运行，状态文件不存在"

    try:
        last_run = datetime.date.fromisoformat(last_run_str)
    except ValueError:
        return True, "状态文件日期格式异常"

    # 补偿条件 1：跨度 >= 30 天
    span = (today - last_run).days
    if span >= 30:
        return True, f"距上次整理已 {span} 天，>= 30 天强制补偿"

    # 补偿条件 2：跨越自然月且当月 1 号未执行
    # 前面已排除 today.day == 1，所以进入这里说明今天不是 1 号
    if (today.year, today.month) != (last_run.year, last_run.month):
        return True, f"跨越自然月（上次 {last_run}，当前 {today}）且未在当月 1 号执行，强制补偿"

    return False, f"无需整理（上次 {last_run}，当前 {today}）"


def categorize_file(path: Path) -> Optional[str]:
    """
    根据文件扩展名和名称判断所属类别。
    返回 CATEGORY_DIRS 的 key 或 None。
    """
    name = path.name
    stem = path.stem.lower()
    ext = path.suffix.lower()

    # 跳过排除项
    if name in EXCLUDE_NAMES or any(part in EXCLUDE_NAMES for part in path.parts):
        return None
    if ext in EXCLUDE_EXTS:
        return None

    # Reference_Texts: 宏观分析、行业指南、年报等
    if ext in {".txt", ".pdf"}:
        return "Reference_Texts"

    # Databases: DuckDB / Parquet / SQLite 等本地数据库
    if ext in {".duckdb", ".parquet", ".db", ".sqlite", ".sqlite3"}:
        return "Databases"

    # 压缩包：按内容或文件名判断
    if ext in {".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z"}:
        if ext == ".zip":
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    inner = [n.lower() for n in zf.namelist()]
                    if any(
                        n.endswith((".duckdb", ".parquet", ".db", ".sqlite", ".sqlite3"))
                        for n in inner
                    ):
                        return "Databases"
                    if any(n.endswith((".csv", ".xlsx", ".xls", ".tsv")) for n in inner):
                        return "Analysis_Reports"
            except Exception:
                pass
        # 文件名启发式
        if any(k in stem for k in ("duckdb", "parquet", "sqlite", "database", "db_backup")):
            return "Databases"
        if any(k in stem for k in ("csv", "dataset", "data", "excel", "xlsx")):
            return "Analysis_Reports"
        # 无法判断的压缩包视为分析报告/归档
        return "Analysis_Reports"

    # 结构化离线表格 → 归入分析报告
    if ext in {".csv", ".xlsx", ".xls", ".tsv"}:
        return "Analysis_Reports"

    # Analysis_Reports: 日志、技术总结、逻辑说明等
    if ext in {".md", ".log", ".json"}:
        return "Analysis_Reports"

    return None


def summarize_text(path: Path, max_lines: int = 50) -> str:
    """提取文本文件前 N 行作为摘要。"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        head = lines[:max_lines]
        summary = " ".join(head)
        if not summary:
            return "文本文件（无有效内容摘要）"
        if len(summary) > 300:
            summary = summary[:300] + "..."
        return summary
    except Exception as e:
        return f"文本摘要失败: {e}"


def summarize_pdf(path: Path) -> str:
    """尝试提取 PDF 文本摘要。"""
    if not HAS_PYPDF2:
        size_mb = path.stat().st_size / (1024 * 1024)
        return f"PDF 文档（未安装 PyPDF2，无法提取文本），大小 {size_mb:.2f} MB"
    try:
        reader = PyPDF2.PdfReader(str(path))
        pages = reader.pages[:3]
        text = ""
        for page in pages:
            extracted = page.extract_text() or ""
            text += extracted + "\n"
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summary = " ".join(lines[:50])
        if not summary:
            return f"PDF 文档（共 {len(reader.pages)} 页），无可读文本摘要"
        if len(summary) > 300:
            summary = summary[:300] + "..."
        return summary
    except Exception as e:
        return f"PDF 摘要失败: {e}"


def summarize_file(path: Path) -> str:
    """根据文件类型生成简短摘要。"""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return summarize_pdf(path)
    if ext in {".txt", ".md"}:
        return summarize_text(path)
    if ext == ".csv":
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]
            preview = " | ".join(lines[:3])
            if len(lines) > 3:
                preview += " ..."
            return f"CSV 预览: {preview}"
        except Exception as e:
            return f"CSV 预览失败: {e}"
    if ext in {".xlsx", ".xls"}:
        return "Excel 表格文件（结构化数据）"
    if ext in {".duckdb", ".db", ".sqlite", ".sqlite3"}:
        size_mb = path.stat().st_size / (1024 * 1024)
        return f"本地数据库文件 ({size_mb:.2f} MB)"
    if ext == ".parquet":
        size_mb = path.stat().st_size / (1024 * 1024)
        return f"Parquet 列式数据文件 ({size_mb:.2f} MB)"
    if ext == ".json":
        return "JSON 格式日志/元数据文件"
    if ext == ".log":
        return "运行日志文件"
    return "—"


def compute_sha256(path: Path) -> str:
    """计算文件 SHA256 前 16 位。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def organize_corpus(
    root: Path, sources: List[str], move: bool = False, dry_run: bool = False
) -> List[Dict]:
    """
    扫描源目录，将文件归类到标准目录。
    返回索引条目列表。
    """
    entries = []
    target_dirs = {key: root / key for key in CATEGORY_DIRS}

    # 确保目标目录存在
    if not dry_run:
        for target in target_dirs.values():
            target.mkdir(exist_ok=True)

    # 收集有效源目录
    source_paths = []
    for src_name in sources:
        src = root / src_name
        if src.exists() and src.is_dir():
            source_paths.append(src)
        else:
            print(f"[INFO] 源目录不存在或不是目录，跳过: {src}")

    # 扫描并归档
    for src in source_paths:
        for file_path in src.rglob("*"):
            if not file_path.is_file():
                continue

            # 跳过排除项
            if any(part in EXCLUDE_NAMES for part in file_path.parts):
                continue
            if file_path.suffix.lower() in EXCLUDE_EXTS:
                continue

            category = categorize_file(file_path)
            if not category:
                continue

            # 保持源目录相对层级
            rel = file_path.relative_to(src)
            target_dir = target_dirs[category]
            target_path = target_dir / rel
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 重复检测：通过 SHA256 比对
            file_hash = compute_sha256(file_path)
            if target_path.exists():
                target_hash = compute_sha256(target_path)
                if target_hash == file_hash:
                    # Dedup hit — still include in index so Corpus_Index.md is complete
                    print(f"[SKIP] 重复文件已在目标目录: {target_path}")
                    entries.append(
                        {
                            "name": target_path.name,
                            "relative_path": str(target_path.relative_to(root)),
                            "category": category,
                            "type": CATEGORY_DIRS[category],
                            "size": target_path.stat().st_size,
                            "sha256": file_hash,
                            "summary": summarize_file(target_path),
                            "source": str(file_path.relative_to(root)),
                        }
                    )
                    continue
                else:
                    # 同名不同内容：追加哈希后缀
                    new_name = f"{target_path.stem}_{file_hash}{target_path.suffix}"
                    target_path = target_path.with_name(new_name)

            action = "移动" if move else "复制"
            if dry_run:
                print(f"[DRY-RUN] {action}: {file_path} -> {target_path}")
            else:
                if move:
                    shutil.move(str(file_path), str(target_path))
                else:
                    shutil.copy2(str(file_path), str(target_path))
                print(f"[DONE] {action}: {file_path} -> {target_path}")

            entries.append(
                {
                    "name": target_path.name,
                    "relative_path": str(target_path.relative_to(root)),
                    "category": category,
                    "type": CATEGORY_DIRS[category],
                    "size": target_path.stat().st_size if not dry_run else file_path.stat().st_size,
                    "sha256": file_hash,
                    "summary": (
                        summarize_file(target_path)
                        if not dry_run and target_path.exists()
                        else summarize_file(file_path)
                    ),
                    "source": str(file_path.relative_to(root)),
                }
            )

    return sorted(entries, key=lambda x: x["relative_path"])


def scan_target_dirs(root: Path) -> List[Dict]:
    """扫描已归档的目标目录，为其中尚未被 entries 覆盖的文件生成索引条目。"""
    target_entries = []
    existing_paths = set()

    for category, label in CATEGORY_DIRS.items():
        target_dir = root / category
        if not target_dir.exists():
            continue
        for file_path in target_dir.rglob("*"):
            if not file_path.is_file():
                continue
            rel_path = str(file_path.relative_to(root))
            if rel_path in existing_paths:
                continue
            existing_paths.add(rel_path)

            # 跳过语料库报告本身
            if file_path.name in (INDEX_FILE, STATE_FILE):
                continue

            target_entries.append(
                {
                    "name": file_path.name,
                    "relative_path": rel_path,
                    "category": category,
                    "type": label,
                    "size": file_path.stat().st_size,
                    "sha256": compute_sha256(file_path),
                    "summary": summarize_file(file_path),
                    "source": rel_path,
                }
            )
    return target_entries


def generate_index(root: Path, entries: List[Dict]) -> None:
    """生成/更新 Corpus_Index.md。同时扫描目标目录，确保 Reference_Texts 等已归档文件也被索引。"""
    # 合并 organize 产生的 entries 与目标目录扫描结果
    target_entries = scan_target_dirs(root)
    all_entries = {e["relative_path"]: e for e in entries}
    for te in target_entries:
        all_entries.setdefault(te["relative_path"], te)
    merged_entries = sorted(all_entries.values(), key=lambda x: x["relative_path"])

    lines = []
    lines.append("# 埃及战略顾问 语料库状态清单 (Corpus Index)")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"**条目总数**: {len(merged_entries)}")
    lines.append("")
    lines.append("## 目录结构")
    lines.append("")
    for key, label in CATEGORY_DIRS.items():
        lines.append(f"- **{key}/** — {label}")
    lines.append("")
    lines.append("## 文件清单")
    lines.append("")
    lines.append("| 文件/目录名称 | 类型 | 用途说明 |")
    lines.append("|-------------|------|---------|")

    for entry in merged_entries:
        name = entry["name"]
        rel_path = entry["relative_path"]
        type_label = entry["type"]
        summary = entry["summary"].replace("|", "\\|").replace("\n", " ").strip()
        if len(summary) > 200:
            summary = summary[:200] + "..."
        lines.append(f"| {name}<br>`{rel_path}` | {type_label} | {summary} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本文件由 `corpus_manager.py` 自动生成，请勿手动修改。*")

    index_path = root / INDEX_FILE
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[INDEX] 已生成/更新: {index_path}")


def main() -> None:
    # Guard against Windows GBK stdout / stderr encoding issues
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

    parser = argparse.ArgumentParser(
        description="埃及市场营销 语料库自动整理与索引生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(DEFAULT_ROOT),
        help="语料库根目录（默认：脚本所在目录的上一级）",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=None,
        help="扫描源目录（可多次指定，默认：datasets reports references api_modules downloads cache temp）",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="归档时移动文件而非复制（默认复制，保留源文件）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅当满足触发条件时才执行（推荐用于自动化调度）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制立即执行，跳过日期/补偿检查",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟执行，不移动/复制文件，不写入状态文件",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] 根目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    sources = args.source if args.source else DEFAULT_SOURCES

    # 默认模式和 --check 都走条件检查；--force 跳过检查
    if not args.force:
        should, reason = should_run(root, force=False)
        print(f"[CHECK] {reason}")
        if not should:
            print("[INFO] 无需执行全量整理。")
            sys.exit(0)
        print(f"[TRIGGER] {reason}，开始执行...")
    else:
        print("[TRIGGER] 强制模式（--force），跳过条件检查，开始执行...")

    print(f"[INFO] 根目录: {root}")
    print(f"[INFO] 扫描源: {sources}")
    print(f"[INFO] 操作模式: {'移动' if args.move else '复制'}")
    print(f"[INFO] 模拟运行: {args.dry_run}")

    entries = organize_corpus(root, sources, move=args.move, dry_run=args.dry_run)

    if not args.dry_run:
        generate_index(root, entries)
        state = load_state(root)
        state["last_run_date"] = datetime.date.today().isoformat()
        state["last_run_datetime"] = datetime.datetime.now().isoformat(timespec="seconds")
        state["files_indexed"] = len(entries)
        state["version"] = "1.0.0"
        save_state(root, state)
        print(f"[STATE] 已更新: {root / STATE_FILE}")
    else:
        print(f"[DRY-RUN] 将生成 {len(entries)} 条索引，不写入文件")

    print("[DONE] 语料整理完成。")


if __name__ == "__main__":
    main()
