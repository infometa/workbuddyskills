#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_case_narrative.py
把检索到的案例渲染成"陪伴式"叙事（M2 / M3 用）

调用：
    python format_case_narrative.py --code CASE-001 --mode m2 --user-context "我做了 3 年还能转吗"
    python format_case_narrative.py --code CASE-004 --mode m3
"""
import argparse, json, sys
from pathlib import Path

CASE_LIB = Path(__file__).resolve().parent.parent / "references" / "case-library.json"


def load_case(code: str) -> dict:
    cases = json.loads(CASE_LIB.read_text(encoding="utf-8"))
    for c in cases:
        if c.get("code") == code:
            return c
    raise ValueError(f"案例 {code} 不存在")


def desensitize_portrait(portrait: str) -> str:
    """画像类型 → 人话角色描述"""
    return {
        "🔍挑剔型": "挑剔型",
        "🌱开放型": "开放型",
        "🚀跃迁型": "跃迁型",
        "🛡稳健型": "稳健型",
    }.get(portrait, portrait or "")


def render_m2(case: dict, user_context: str = "") -> str:
    """M2 完整陪伴模板（1-2 段）"""
    code = case["code"]
    tenure = case.get("tenure", "")
    portrait = desensitize_portrait(case.get("portrait_type", ""))
    span = case.get("span_type", "")
    quotes = case.get("quotes") or []
    quote = quotes[0] if quotes else ""
    advice = case.get("advice") or ""

    # quote 为空时不强行渲染那一段，避免出现空引号
    quote_block = f'\n\n> "{quote}"' if quote else ""

    nudge = f'当时 ta 也在想"{user_context}"，' if user_context else "当时 ta 也走过同样的纠结，"

    return f"""有个像你的同事——{code}（{tenure}, {portrait}），ta {span}。

{nudge}后来有这些复盘：{quote_block}

ta 给后来人的话是这样：

> "{advice[:120]}{'...' if len(advice) > 120 else ''}"

听到这里，你心里浮出什么。"""


def render_m3(case: dict) -> str:
    """M3 教练引子（1 句金句，没金句就用 advice 第一句）"""
    code = case["code"]
    portrait = desensitize_portrait(case.get("portrait_type", ""))
    quotes = case.get("quotes") or []

    if quotes:
        line = quotes[0]
    else:
        # 兜底：用 advice 的第一句
        advice = case.get("advice") or ""
        line = advice.split("。")[0] if advice else ""

    if not line:
        # 都没有 → 用 span_type + scenario_tags 拼一句
        line = f"换岗的关键不在年限，在'{', '.join(case.get('scenario_tags', [])[:2])}'"

    return f"""我有个同事（代号 {code}, {portrait}），ta 给我说过一句话——

> "{line}"

这句话落到你身上，会让你想到什么。"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True, help="案例代号 CASE-001 等")
    ap.add_argument("--mode", choices=["m2", "m3"], default="m2")
    ap.add_argument("--user-context", default="", help="用户当下的核心纠结一句话")
    args = ap.parse_args()

    try:
        case = load_case(args.code)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(2)

    if args.mode == "m2":
        narrative = render_m2(case, args.user_context)
    else:
        narrative = render_m3(case)

    print(json.dumps({
        "ok": True,
        "code": args.code,
        "mode": args.mode,
        "narrative": narrative,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
