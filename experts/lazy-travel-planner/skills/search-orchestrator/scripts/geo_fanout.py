#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_fanout.py · 把"江西附近游玩"这类模糊地理意图转成候选地点池
v2.0：移除高德 MCP 依赖，改用 meituan-travel 作为主入口。

设计：
  - 本脚本只做"意图解析 + 写一份调用计划"，**实际数据获取由 agent 调美团 skill 完成**
  - agent 拿到候选地点后，再调 fan-in（xhs CLI 深挖）
  - 没有美团连接器 → check_deps 已经在 agent 入口阻塞，到不了这里

为什么这样设计？
  meituan-travel 是 qclaw 内置 skill，agent 直接调用即可（natural-language tool call），
  不需要本脚本去 subprocess 它。本脚本输出的是「意图结构 + 查询计划」给 agent 用。
"""
import argparse, json, sys, re, pathlib

SHARED_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
from check_deps import check_or_block  # noqa


def parse_intent_for_geo(intent: str) -> dict:
    """从 intent 字符串里抽取核心地点 + 半径意图 + 时长"""
    radius_match = re.search(r"(\d+)\s*(km|公里)", intent)
    radius_km = int(radius_match.group(1)) if radius_match else None
    is_around = bool(re.search(r"(附近|周边|周围)", intent)) or radius_km is not None

    duration_match = re.search(r"(\d+)\s*天", intent)
    duration = int(duration_match.group(1)) if duration_match else None

    center_match = re.search(r"^([\u4e00-\u9fff]{2,6})", intent.strip())
    center = center_match.group(1) if center_match else intent.strip().split()[0]

    return {
        "center": center,
        "radius_km": radius_km or (200 if is_around else 0),
        "is_around": is_around,
        "duration_days": duration,
    }


def make_meituan_query_plan(parsed: dict, domain: str) -> list:
    """生成给美团 skill 的查询计划

    每个 query 由 agent 在 runtime 调美团对应 tool。
    """
    plans = []
    center = parsed["center"]
    if domain == "destination":
        if parsed["is_around"]:
            plans.append({
                "tool_hint": "美团 · 行程规划",
                "query": f"{center}附近 {parsed.get('duration_days') or 3} 日游推荐",
                "expects": "一组目的地候选 + 主题路线"
            })
            plans.append({
                "tool_hint": "美团 · 景点推荐",
                "query": f"{center}周边热门景点",
                "expects": "周边 200km 内景点列表"
            })
        else:
            plans.append({
                "tool_hint": "美团 · 行程规划",
                "query": f"{center} {parsed.get('duration_days') or 3} 日游",
                "expects": "标准多日游模板"
            })
            plans.append({
                "tool_hint": "美团 · 景点推荐",
                "query": f"{center} 必去景点",
                "expects": "城市核心景点 Top N"
            })
    elif domain == "poi":
        plans.append({
            "tool_hint": "美团 · 景点推荐",
            "query": f"{center} 景点 Top",
            "expects": "POI 列表（含坐标 + 评分 + 营业 + 票价）"
        })
    elif domain == "accommodation":
        plans.append({
            "tool_hint": "美团 · 酒店推荐",
            "query": f"{center} 酒店",
            "expects": "酒店列表（含一手房态 + 价格 + 评分）"
        })
    elif domain == "risk":
        plans.append({
            "tool_hint": "美团 · 景点推荐",
            "query": f"{center} 景区注意事项",
            "expects": "景区周边官方提示"
        })
    return plans


def geo_fanout(intent: str, domain: str) -> dict:
    """主入口：返回 {parsed, meituan_plan} 给 agent 执行"""
    # 强制依赖体检：美团必须开通
    check_or_block("meituan_travel")
    parsed = parse_intent_for_geo(intent)
    return {
        "parsed_intent": parsed,
        "meituan_query_plan": make_meituan_query_plan(parsed, domain),
        "_doc": "agent 应按 meituan_query_plan 调用美团 skill 拿数据，再喂给 query_expand"
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", required=True)
    ap.add_argument("--domain", default="destination")
    a = ap.parse_args()
    result = geo_fanout(a.intent, a.domain)
    print(json.dumps(result, ensure_ascii=False, indent=2))
