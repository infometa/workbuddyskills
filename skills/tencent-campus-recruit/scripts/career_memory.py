#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯校招求职记忆管理脚本（本地工作空间版）

用途：
- 在当前工作空间中维护候选人的长期求职画像，便于持续对话时给出更个性化建议
- 默认写入 ./career-memory/campus-recruit-memory.md
- 只保存用户明确提供、与求职建议直接相关的信息；不保存身份证、手机号、住址、账号密钥等敏感信息

用法：
    python scripts/career_memory.py init
    python scripts/career_memory.py show
    python scripts/career_memory.py append --text "目标：技术后台开发；城市：深圳/北京"
    python scripts/career_memory.py forget
"""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from pathlib import Path

DEFAULT_MEMORY_PATH = Path("career-memory") / "campus-recruit-memory.md"
MAX_APPEND_CHARS = 2000

SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{11}\b"),
    re.compile(r"\b\d{17}[0-9Xx]\b"),
    re.compile(r"(?i)api[_-]?key|secret|token|password|authorization|bearer|sk-[A-Za-z0-9]"),
    re.compile(r"(?i)身份证|手机号|住址|银行卡|密码|密钥|验证码|cookie"),
]

TEMPLATE = """# 腾讯校招求职记忆

> 本文件由腾讯校园招聘助手在用户允许的工作空间内维护。
> 仅记录用户明确提供、会影响求职建议的长期信息；不要写入身份证、手机号、住址、账号密钥、完整联系方式等敏感信息。

## 用户画像
- 学历/年级/毕业时间：待补充
- 专业/研究方向：待补充
- 目标岗位方向：待补充
- 目标城市/可接受工作地：待补充
- 当前招聘阶段：待补充

## 能力与经历
- 核心技能：待补充
- 项目/实习亮点：待补充
- 作品集/论文/竞赛：待补充

## 偏好与约束
- 可实习时间/到岗时间：待补充
- 不考虑方向/城市：待补充
- 沟通风格偏好：待补充

## 辅导记录
- 暂无
"""


def get_memory_path() -> Path:
    override = os.getenv("CAREER_MEMORY_FILE")
    return Path(override) if override else DEFAULT_MEMORY_PATH


def ensure_memory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(TEMPLATE, encoding="utf-8")


def sanitize(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("记忆内容不能为空")
    if len(text) > MAX_APPEND_CHARS:
        text = text[:MAX_APPEND_CHARS] + "…"
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise ValueError("检测到疑似敏感信息，已拒绝写入记忆")
    return text


def cmd_init(path: Path) -> None:
    ensure_memory(path)
    print(f"memory_file={path}")


def cmd_show(path: Path) -> None:
    ensure_memory(path)
    print(path.read_text(encoding="utf-8"))


def cmd_append(path: Path, text: str) -> None:
    ensure_memory(path)
    safe_text = sanitize(text)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n- {now}：{safe_text}\n")
    print(f"appended_to={path}")


def cmd_forget(path: Path) -> None:
    if path.exists():
        path.unlink()
    print(f"forgot={path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="腾讯校招求职记忆管理脚本")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="初始化记忆文件")
    sub.add_parser("show", help="查看记忆文件")
    append_parser = sub.add_parser("append", help="追加一条求职记忆")
    append_parser.add_argument("--text", required=True, help="待追加的记忆内容")
    sub.add_parser("forget", help="删除记忆文件")

    args = parser.parse_args()
    path = get_memory_path()

    try:
        if args.cmd == "init":
            cmd_init(path)
        elif args.cmd == "show":
            cmd_show(path)
        elif args.cmd == "append":
            cmd_append(path, args.text)
        elif args.cmd == "forget":
            cmd_forget(path)
    except ValueError as e:
        print(f"error={e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
