#!/usr/bin/env python3
"""
academic-tutor · update_profile.py

更新用户 profile（专业/年级/在修课程/论文进度/语调）。
所有字段都可选，仅更新提供的部分。

Usage:
    python3 update_profile.py --add-course "操作系统:第5章 内存管理"
    python3 update_profile.py --thesis-stage proposal --thesis-topic "小样本图像分类"
    python3 update_profile.py --tone strict
    python3 update_profile.py --remove-course "操作系统"
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
    """
    explicit = os.environ.get("ACADEMIC_TUTOR_DATA_DIR")
    if explicit:
        return pathlib.Path(os.path.expandvars(os.path.expanduser(explicit)))
    home_override = os.environ.get("ACADEMIC_TUTOR_HOME")
    base = pathlib.Path(os.path.expandvars(os.path.expanduser(home_override))) if home_override else pathlib.Path.home()
    return base / ".workbuddy" / "data" / "academic-tutor"


DATA_DIR = _resolve_data_dir()
PROFILE_PATH = DATA_DIR / "profile.json"

VALID_TONES = {"gentle", "neutral", "strict", "peer"}
VALID_THESIS_STAGES = {
    "topic-selection",
    "literature-review",
    "proposal",
    "framework",
    "drafting",
    "argument-review",
    "revision",
    "defense",
}


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        print("ERROR: profile 不存在，请先运行 init_profile.py", file=sys.stderr)
        sys.exit(1)
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def save_profile(profile: dict) -> None:
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")
    PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")


def add_course(profile: dict, spec: str) -> None:
    """格式：'课程名:进度描述' 或 '课程名'。"""
    if ":" in spec:
        name, progress = spec.split(":", 1)
    else:
        name, progress = spec, ""
    name = name.strip()
    progress = progress.strip()

    courses = profile.setdefault("in_progress_courses", [])
    for c in courses:
        if c.get("name") == name:
            c["progress"] = progress
            return
    courses.append({"name": name, "progress": progress})


def remove_course(profile: dict, name: str) -> None:
    courses = profile.setdefault("in_progress_courses", [])
    profile["in_progress_courses"] = [c for c in courses if c.get("name") != name]


def update_thesis(profile: dict, stage: str | None, topic: str | None,
                  advisor_style: str | None, deadline: str | None) -> None:
    thesis = profile.setdefault("thesis", {})
    if stage is not None:
        thesis["stage"] = stage
    if topic is not None:
        thesis["topic_draft"] = topic
    if advisor_style is not None:
        thesis["advisor_style"] = advisor_style
    if deadline is not None:
        thesis["deadline"] = deadline


def main() -> int:
    p = argparse.ArgumentParser(description="Update academic-tutor profile fields.")
    p.add_argument("--major")
    p.add_argument("--grade")
    p.add_argument("--add-course", action="append", default=[],
                   help='追加课程，格式 "课程名:进度"。可重复。')
    p.add_argument("--remove-course", action="append", default=[],
                   help="按名删除课程。可重复。")
    p.add_argument("--thesis-stage", choices=sorted(VALID_THESIS_STAGES))
    p.add_argument("--thesis-topic")
    p.add_argument("--thesis-advisor-style")
    p.add_argument("--thesis-deadline")
    p.add_argument("--tone", choices=sorted(VALID_TONES))
    p.add_argument("--language", choices=["zh", "en", "bilingual"])
    p.add_argument("--max-hints", type=int)
    p.add_argument("--skip-after", type=int, dest="skip_after",
                   help="重复几次后简化引导（默认 5）")
    args = p.parse_args()

    profile = load_profile()

    if args.major:
        profile["major"] = args.major
    if args.grade:
        profile["grade"] = args.grade
    for c in args.add_course:
        add_course(profile, c)
    for c in args.remove_course:
        remove_course(profile, c)

    if any([args.thesis_stage, args.thesis_topic, args.thesis_advisor_style, args.thesis_deadline]):
        update_thesis(profile, args.thesis_stage, args.thesis_topic,
                      args.thesis_advisor_style, args.thesis_deadline)

    prefs = profile.setdefault("preferences", {})
    if args.tone:
        prefs["tone"] = args.tone
    if args.language:
        prefs["language"] = args.language
    if args.max_hints is not None:
        if args.max_hints < 1 or args.max_hints > 3:
            print("ERROR: max-hints 必须在 1-3", file=sys.stderr)
            return 2
        prefs["max_hints"] = args.max_hints
    if args.skip_after is not None:
        if args.skip_after < 2:
            print("ERROR: skip-after 必须 >= 2", file=sys.stderr)
            return 2
        prefs["skip_questions_after_n_attempts"] = args.skip_after

    save_profile(profile)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
