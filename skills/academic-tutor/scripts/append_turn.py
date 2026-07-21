#!/usr/bin/env python3
"""
academic-tutor · append_turn.py

向会话中追加一轮对话（用户提问 + AI 三段式回复）。

Usage:
    python3 append_turn.py <session-id> --user-msg-file user.txt --reply-file reply.json
    python3 append_turn.py <session-id> --user-msg "..." --reply-json '{...}'
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
SESSIONS_DIR = DATA_DIR / "sessions"


def load_session(session_id: str) -> tuple[pathlib.Path, dict]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        print(f"ERROR: session 不存在：{path}", file=sys.stderr)
        sys.exit(1)
    return path, json.loads(path.read_text(encoding="utf-8"))


def detect_stuck_signals(text: str) -> list[str]:
    signals = []
    triggers = {
        "asking_for_answer": ["直接告诉我", "答案", "把答案", "别废话", "直接给"],
        "emotion_low": ["太菜", "学不会", "不会", "看不懂", "撑不住", "累"],
        "academic_misconduct": ["改重", "降重", "洗稿", "代写", "替我写"],
    }
    for sig, kws in triggers.items():
        if any(k in text for k in kws):
            signals.append(sig)
    return signals


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("session_id")
    p.add_argument("--user-msg")
    p.add_argument("--user-msg-file")
    p.add_argument("--reply-json")
    p.add_argument("--reply-file")
    p.add_argument("--intent")
    args = p.parse_args()

    if not (args.user_msg or args.user_msg_file):
        print("ERROR: --user-msg 或 --user-msg-file 二选一", file=sys.stderr)
        return 2
    if not (args.reply_json or args.reply_file):
        print("ERROR: --reply-json 或 --reply-file 二选一", file=sys.stderr)
        return 2

    try:
        user_msg = (
            pathlib.Path(args.user_msg_file).read_text(encoding="utf-8")
            if args.user_msg_file else args.user_msg
        )
    except FileNotFoundError:
        print(f"ERROR: 用户消息文件不存在：{args.user_msg_file}", file=sys.stderr)
        return 2

    try:
        reply_raw = (
            pathlib.Path(args.reply_file).read_text(encoding="utf-8")
            if args.reply_file else args.reply_json
        )
    except FileNotFoundError:
        print(f"ERROR: 回复文件不存在：{args.reply_file}", file=sys.stderr)
        return 2
    try:
        reply = json.loads(reply_raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: reply JSON 解析失败：{e}", file=sys.stderr)
        return 2

    # 校验 reply 结构
    required = {"questions", "hints", "next_step"}
    missing = required - set(reply.keys())
    if missing:
        print(f"ERROR: reply 缺失必填字段：{missing}", file=sys.stderr)
        return 2

    path, session = load_session(args.session_id)
    new_signals = detect_stuck_signals(user_msg)
    if new_signals:
        existing = set(session.get("stuck_signals", []))
        existing.update(new_signals)
        session["stuck_signals"] = sorted(existing)

    if "asking_for_answer" in new_signals:
        session["attempt_count"] = session.get("attempt_count", 0) + 1

    turn = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "user": user_msg,
        "intent": args.intent or session.get("primary_intent"),
        "ai_response": reply,
        "user_attempt": None,
    }
    session.setdefault("turns", []).append(turn)
    path.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")

    # 读 profile 阈值（默认 5）
    profile_path = DATA_DIR / "profile.json"
    threshold = 5
    if profile_path.exists():
        try:
            prof = json.loads(profile_path.read_text(encoding="utf-8"))
            threshold = int(prof.get("preferences", {}).get("skip_questions_after_n_attempts", 5))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    attempt_count = session.get("attempt_count", 0)
    next_mode = "simplified" if attempt_count >= threshold else "standard"

    print(json.dumps({
        "ok": True,
        "turn_count": len(session["turns"]),
        "attempt_count": attempt_count,
        "stuck_signals": session.get("stuck_signals", []),
        "next_response_mode": next_mode,
        "simplified_mode_threshold": threshold,
        "simplified_mode_hint": (
            "下一轮回复必须切换到简化模式：1 反问 + 1 提示 + 1 句下一步，总字数 ≤ 200。"
            "校验时使用 render_three_segments.py --simplified" if next_mode == "simplified" else None
        ),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
