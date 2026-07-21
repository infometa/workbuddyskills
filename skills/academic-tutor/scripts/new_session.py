#!/usr/bin/env python3
"""
academic-tutor · new_session.py

开启一个新对话会话；写入 sessions/<session-id>.json。

Usage:
    python3 new_session.py --topic "高数 - 不定积分"
    python3 new_session.py --topic "论文选题" --intent paper-topic
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime

def _resolve_data_dir() -> pathlib.Path:
    """解析数据目录，优先级：
    1) ACADEMIC_TUTOR_DATA_DIR（用户显式覆盖整段路径）
    2) ACADEMIC_TUTOR_HOME（旧变量，覆盖 home 根，向后兼容）
    3) 平台默认数据目录
    """
    explicit = os.environ.get("ACADEMIC_TUTOR_DATA_DIR")
    if explicit:
        return pathlib.Path(os.path.expandvars(os.path.expanduser(explicit)))
    home_override = os.environ.get("ACADEMIC_TUTOR_HOME")
    base = pathlib.Path(os.path.expandvars(os.path.expanduser(home_override))) if home_override else pathlib.Path.home()
    return base / ".workbuddy" / "data" / "academic-tutor"


DATA_DIR = _resolve_data_dir()
SESSIONS_DIR = DATA_DIR / "sessions"

VALID_INTENTS = {
    "homework", "concept", "proof",
    "paper-topic", "paper-review", "paper-revision",
    "out-of-scope",
}


def slugify(text: str) -> str:
    s = re.sub(r"\s+", "-", text.strip().lower())
    s = re.sub(r"[^\w\-]", "", s, flags=re.UNICODE)
    return s[:40] or "untitled"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True, help="会话主题（中文或英文均可）")
    p.add_argument("--intent", choices=sorted(VALID_INTENTS), default="homework")
    args = p.parse_args()

    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: 无法创建会话目录 {SESSIONS_DIR}：{e}", file=sys.stderr)
        return 1

    now = datetime.now()
    session_id = f"sess-{now.strftime('%Y%m%d-%H%M')}-{slugify(args.topic)}"
    path = SESSIONS_DIR / f"{session_id}.json"

    session = {
        "session_id": session_id,
        "started_at": now.isoformat(timespec="seconds"),
        "topic": args.topic,
        "primary_intent": args.intent,
        "turns": [],
        "attempt_count": 0,
        "stuck_signals": [],
    }
    try:
        path.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        print(f"ERROR: 无法写入会话文件 {path}：{e}", file=sys.stderr)
        return 1
    print(json.dumps({"session_id": session_id, "path": str(path)},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
