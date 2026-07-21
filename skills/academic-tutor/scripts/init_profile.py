#!/usr/bin/env python3
"""
academic-tutor · init_profile.py

初始化用户 profile.json。如果已存在则保留旧字段，仅补缺。
全本地，零网络调用。

Usage:
    python3 init_profile.py [--major <major>] [--grade <grade>] [--tone <tone>]
    python3 init_profile.py --show
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime

def _resolve_data_dir() -> pathlib.Path:
    """解析数据目录，优先级：
    1) ACADEMIC_TUTOR_DATA_DIR（用户显式覆盖整段路径）
    2) ACADEMIC_TUTOR_HOME（旧变量，覆盖 home 根，向后兼容）
    3) 平台默认数据目录
    路径中的 ~ 与 $VAR 会被展开。
    """
    explicit = os.environ.get("ACADEMIC_TUTOR_DATA_DIR")
    if explicit:
        return pathlib.Path(os.path.expandvars(os.path.expanduser(explicit)))
    home_override = os.environ.get("ACADEMIC_TUTOR_HOME")
    base = pathlib.Path(os.path.expandvars(os.path.expanduser(home_override))) if home_override else pathlib.Path.home()
    return base / ".workbuddy" / "data" / "academic-tutor"


DATA_DIR = _resolve_data_dir()
PROFILE_PATH = DATA_DIR / "profile.json"
SESSIONS_DIR = DATA_DIR / "sessions"

DEFAULT_PROFILE = {
    "user_name": None,
    "major": None,
    "grade": None,
    "school_type": None,
    "in_progress_courses": [],
    "thesis": {
        "stage": None,
        "topic_draft": None,
        "advisor_style": None,
        "deadline": None,
    },
    "preferences": {
        "tone": "neutral",
        "language": "zh",
        "max_hints": 3,
        "skip_questions_after_n_attempts": 5,
        "depth_hint": "auto",
    },
    "history_topics": [],
    "created_at": None,
    "updated_at": None,
}

VALID_TONES = {"gentle", "neutral", "strict", "peer"}
VALID_GRADES = {"freshman", "sophomore", "junior", "senior", "grad", "phd"}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_profile(profile: dict) -> None:
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")
    if not profile.get("created_at"):
        profile["created_at"] = profile["updated_at"]
    PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")


def merge(default: dict, current: dict) -> dict:
    """深合并：current 优先，仅补缺。"""
    result = json.loads(json.dumps(default))
    for k, v in current.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge(result[k], v)
        else:
            result[k] = v
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize academic-tutor profile.")
    parser.add_argument("--major", help="主修专业，如：计算机科学与技术")
    parser.add_argument("--grade", choices=sorted(VALID_GRADES), help="年级")
    parser.add_argument("--tone", choices=sorted(VALID_TONES), help="语调档位")
    parser.add_argument("--user-name", help="昵称（可选）")
    parser.add_argument("--show", action="store_true", help="只显示当前 profile")
    args = parser.parse_args()

    ensure_dirs()

    if args.show:
        prof = load_profile()
        if not prof:
            print("(profile 尚未创建)")
            return 0
        print(json.dumps(prof, indent=2, ensure_ascii=False))
        return 0

    current = load_profile()
    profile = merge(DEFAULT_PROFILE, current)

    if args.major:
        profile["major"] = args.major
    if args.grade:
        profile["grade"] = args.grade
    if args.tone:
        profile["preferences"]["tone"] = args.tone
    if args.user_name:
        profile["user_name"] = args.user_name

    save_profile(profile)
    print(f"profile 已写入：{PROFILE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
