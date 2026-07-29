#!/usr/bin/env python3
"""列出可购买的套餐清单。

Usage:
  python list_plans.py

流程：
  1) 解码 JWT 拿 uid（仅记录日志，account 接口自动从 key 识别用户）
  2) GET /account/currentByAPI 拿 isTeamUser
  3) POST /package/getByTypeByAPI body={"packageType":1或7}
  4) 过滤免费版（packagePrice=0），归一化字段后输出
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setup_common  # noqa: E402


def fetch_plans() -> dict:
    """拿用户类型 → 查对应套餐 → 归一化。"""
    # 1) 解 JWT（仅日志，不强制要求成功）
    payload = setup_common.decode_jwt_uid()
    if payload:
        print(f"[real] JWT uid={payload.get('uid')} name={payload.get('name')}", file=sys.stderr)

    # 2) 查用户类型
    user = setup_common.fetch_user_info()
    is_team = bool(user.get("isTeamUser"))
    nick = user.get("nickName", "")
    print(f"[real] 当前用户: {nick} isTeamUser={is_team}", file=sys.stderr)

    # 3) 按类型查套餐
    package_type = 7 if is_team else 1
    type_label = "团队" if is_team else "个人"
    print(f"[real] 查询 {type_label}套餐 packageType={package_type}", file=sys.stderr)
    packages = setup_common.fetch_packages(package_type)

    # 4) 归一化 + 过滤免费版
    plans = []
    for p in packages:
        norm = setup_common.normalize_package(p)
        if norm is not None:
            plans.append(norm)
    print(f"[real] 原始 {len(packages)} 个套餐，过滤免费版后 {len(plans)} 个", file=sys.stderr)
    return {"plans": plans, "user": {"nickName": nick, "isTeamUser": is_team}}


def main() -> int:
    try:
        result = fetch_plans()
    except RuntimeError as e:
        print(json.dumps({"error": True, "message": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
