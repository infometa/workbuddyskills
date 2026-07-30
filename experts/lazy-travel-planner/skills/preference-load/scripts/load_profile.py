#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
load_profile.py · 加载 user_profile.json，输出给上游 skill。
不存在则返回 {} + exit code 4（提示走 BOOTSTRAP）。
"""
import json, sys, pathlib, argparse, datetime

DEFAULT_PROFILE = (pathlib.Path(__file__).parent.parent.parent.parent
                   / "data" / "user_profile.json")


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ profile 损坏: {e}", file=sys.stderr)
        return {"_corrupted": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=str(DEFAULT_PROFILE))
    ap.add_argument("--touch", action="store_true",
                    help="顺便把 _last_active 更新成现在时间")
    a = ap.parse_args()
    p = pathlib.Path(a.profile)
    data = load(p)
    if not data:
        print(json.dumps({"ok": False, "needs_bootstrap": True}, ensure_ascii=False))
        sys.exit(4)
    if data.get("_corrupted"):
        print(json.dumps({"ok": False, "corrupted": True}, ensure_ascii=False))
        sys.exit(3)

    if a.touch:
        data["_last_active"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "profile": data}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
