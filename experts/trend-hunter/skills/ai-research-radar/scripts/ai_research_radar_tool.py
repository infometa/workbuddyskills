#!/usr/bin/env python3
"""
定时任务：每日研究简报 — 工具脚本
漏掉重要论文和行业报告？每天帮你盯着，关键信息一条不漏

目标用户: 研究人员、AI 从业者
输出产物: 每日简报（Markdown）
"""

import sys, json, os, argparse
from datetime import datetime
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


import json
from datetime import datetime

def cmd_generate(args):
    """生成每日简报框架"""
    date = args.date if args.date != "today" else datetime.now().strftime("%Y-%m-%d")
    output = args.output or f"ai_brief_{date}.md"
    
    md = f"""# 🤖 AI 每日研究简报

**日期**: {date}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📰 今日AI头条

### 1. [标题]
- **来源**: [链接]
- **摘要**: [一段话总结]
- **影响**: 🔴高 / 🟡中 / 🟢低

### 2. [标题]
- **来源**: [链接]  
- **摘要**: [一段话总结]
- **影响**: 🔴高 / 🟡中 / 🟢低

### 3. [标题]
- **来源**: [链接]
- **摘要**: [一段话总结]
- **影响**: 🔴高 / 🟡中 / 🟢低

## 📄 论文速递

| 论文标题 | 作者 | arXiv链接 | 一句话摘要 |
|---------|------|----------|-----------|
| [标题1] | [作者] | [链接] | [摘要] |
| [标题2] | [作者] | [链接] | [摘要] |

## 🔧 开源项目推荐

| 项目名 | Stars | GitHub链接 | 说明 |
|--------|-------|----------|------|
| [项目1] | ⭐XXX | [链接] | [说明] |
| [项目2] | ⭐XXX | [链接] | [说明] |

## ⭐ 值得深读

> 💡 今日最值得深入阅读的内容：
> 
> **[标题]** — [推荐理由]
> 链接: [URL]

---
*本简报由AI自动生成，内容基于公开信息检索*
"""
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(json.dumps({"status": "success", "output_file": output, "date": date}, ensure_ascii=False, indent=2))
    return 0

def cmd_archive(args):
    """归档历史简报"""
    import os, glob
    dir_path = args.dir or "."
    files = glob.glob(os.path.join(dir_path, "ai_brief_*.md"))
    print(json.dumps({"status": "success", "archived_files": len(files), "files": sorted(files)}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args):
    """查看当前状态"""
    data_files = []
    if os.path.exists(DATA_DIR):
        data_files = [f for f in os.listdir(DATA_DIR) if not f.startswith(".")]
    result = {
        "skill": "ai-research-radar",
        "scene": "定时任务：每日研究简报",
        "data_dir": DATA_DIR,
        "data_files": data_files,
        "file_count": len(data_files),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_export(args):
    """导出结果"""
    fmt = getattr(args, "format", "json") or "json"
    data_files = []
    if os.path.exists(DATA_DIR):
        data_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if not f.startswith(".")]
    
    if fmt == "json":
        output = json.dumps({"files": data_files, "count": len(data_files)}, ensure_ascii=False, indent=2)
    else:
        output = "\n".join(data_files)
    
    print(output)
    return 0


def main():
    parser = argparse.ArgumentParser(description="定时任务：每日研究简报")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    p_generate = subparsers.add_parser("generate", help="生成今日简报框架")
    p_generate.add_argument("--date", help="DATE")
    p_generate.add_argument("--output", help="PATH")

    p_archive = subparsers.add_parser("archive", help="归档历史简报")
    p_archive.add_argument("--dir", help="PATH")

    subparsers.add_parser("status", help="查看状态")
    p_export = subparsers.add_parser("export", help="导出结果")
    p_export.add_argument("format", nargs="?", default="json", help="导出格式")

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "archive":
        return cmd_archive(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "export":
        return cmd_export(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
