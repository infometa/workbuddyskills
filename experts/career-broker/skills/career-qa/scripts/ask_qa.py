#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ask_qa.py · 双路由问询入口

流程：
  敏感词过滤 → 路由判断 → 返回上层 agent 应调用的 MCP 工具标记

说明：
  两条问询路径都由 agent 在主对话里直接调用 MCP 工具；本脚本只做
  sensitive filter + route dry-run，避免在脚本里伪造 MCP 环境。

用法：
    python ask_qa.py --query "活水有试用期吗" --user <your-rtx>
    python ask_qa.py --query "VPN 连不上" --user <your-rtx>

输出：
    {"ok": true, "route": "recruit_knowledge"|"xiaoq", "answer": null,
     "tool": "...", "params": {...}}
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensitive_filter import filter_query  # noqa: E402
from route_qa import route                    # noqa: E402

RECRUIT_KNOWLEDGE_API_ID = "recruit.recruit-ai-service.search_knowledge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--conversation-id", default="", help="保留兼容参数；MCP 问询路径不使用")
    ap.add_argument("--timeout", type=int, default=60, help="保留兼容参数；MCP 问询路径不使用")
    args = ap.parse_args()

    # ① 敏感词过滤
    refusal = filter_query(args.query)
    if refusal:
        print(json.dumps({
            "ok": True,
            "route": "blocked",
            "answer": refusal,
            "blocked_by": "sensitive_filter",
        }, ensure_ascii=False))
        return

    # ② 路由判断
    target = route(args.query)

    # ③ 活水/招聘知识库 —— 上层 agent 按 recruit-mcp 的 SearchAPI → CallAPI 流程调用
    if target == "recruit_knowledge":
        print(json.dumps({
            "ok": True,
            "route": "recruit_knowledge",
            "answer": None,
            "should_call_recruit_knowledge": True,
            "search_tool": "mcp__recruit-mcp__SearchAPI",
            "search_params": {"apiId": RECRUIT_KNOWLEDGE_API_ID},
            "call_tool": "mcp__recruit-mcp__CallAPI",
            "call_params": {
                "apiId": RECRUIT_KNOWLEDGE_API_ID,
                "params": {"query": args.query, "topK": 5, "minScore": 0.4},
            },
            "hint": "请 agent 先用 SearchAPI(apiId) 确认 schema，再用 CallAPI 检索知识库；取 hits[0].answer 作为主答案，命中低时再看前 3 条是否有更贴切答案。",
        }, ensure_ascii=False))
        return

    # ④ 其他职场问询 —— 上层 agent 直接调小Q
    print(json.dumps({
        "ok": True,
        "route": "xiaoq",
        "answer": None,
        "should_call_xiaoq": True,
        "tool": "mcp__QLearning__chatWithXiaoQ",
        "params": {"content": args.query},
        "hint": "请 agent 直接调上述 MCP 工具，把返回 text 原样输出给用户（保留链接和温馨提示）",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
