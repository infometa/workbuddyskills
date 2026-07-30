#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_mcp_json.py
扫 ~/.workbuddy/mcp.json，检测已有的 MCP 配置 + 太湖 PAT（用于 QLearning / km 复用判断）。
被各个 setup 引导话术调用——agent 引导用户装 QLearning / km 前先跑一次，
判断"是否已有可复用 PAT" / "已经装了哪几个 MCP"。

⚠️ 安全：绝不输出真实 PAT 明文，只返回 has_tai_pat + 掩码。
⚠️ 招活MCP（recruit-mcp）走一键授权、不靠太湖 PAT，故不在本脚本的 PAT 复用判断范围内。

输出 JSON：
{
  "mcp_json_exists": true/false,
  "installed": ["QLearning", "recruit-mcp", "km", ...],
  "missing": ["QLearning", "km"],                 // 相对于本专家需 PAT 的 MCP
  "has_tai_pat": true/false,                       // 是否已有可复用 PAT
  "tai_pat_masked": "tai_pat_clbb***OXOA" | null,  // 仅掩码，绝不明文
  "tai_pat_source": "QLearning" | "km" | ...,      // 哪个 MCP 用的
  "needs_pat_apply": false,                        // 不需要再申 PAT
  "advice": "<给 agent 的一句话建议>"
}
"""
import json
import re
import sys
from pathlib import Path


MCP_JSON_PATH = Path.home() / ".workbuddy" / "mcp.json"

# 本专家关心、且靠太湖 PAT 鉴权的 MCP（按 mcp.json 里的 key 名）。
# recruit-mcp（招活MCP）走一键授权、不用 PAT，故不在此列。
CAREER_BROKER_PAT_MCPS = ["QLearning", "km"]


def mask_pat(pat: str) -> str:
    """脱敏：只保留前 8 位 + 后 4 位，中间用 *** 替代。绝不输出完整 PAT。"""
    if not pat:
        return ""
    if len(pat) <= 14:
        return "***"
    return f"{pat[:8]}***{pat[-4:]}"


def find_tai_pat(mcp_servers: dict) -> tuple[str | None, str | None]:
    """从任何一个 mcp 的 Authorization: Bearer 里抠太湖 PAT。返回 (token, source_mcp_name)"""
    for name, cfg in mcp_servers.items():
        headers = (cfg or {}).get("headers", {}) or {}
        auth = headers.get("Authorization") or headers.get("authorization") or ""
        m = re.search(r"Bearer\s+(tai_pat_[A-Za-z0-9._-]+)", auth)
        if m:
            return m.group(1), name
    return None, None


def main():
    result = {
        "mcp_json_exists": MCP_JSON_PATH.exists(),
        "installed": [],
        "missing": [],
        "has_tai_pat": False,
        "tai_pat_masked": None,
        "tai_pat_source": None,
        "needs_pat_apply": True,
        "advice": "",
    }

    if not MCP_JSON_PATH.exists():
        result["missing"] = list(CAREER_BROKER_PAT_MCPS)
        result["advice"] = (
            "你还没有 ~/.workbuddy/mcp.json 文件。QLearning / km 看 skills/career-broker-core/references/setup/00-mcp-bundle.md 一次装齐；"
            "招活MCP 走一键授权（召唤专家时弹连接提示），不用写这里。"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    try:
        data = json.loads(MCP_JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result["advice"] = f"~/.workbuddy/mcp.json JSON 语法错误：{e}。先修一下再装新 MCP。"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    mcp_servers = data.get("mcpServers", {}) or {}
    result["installed"] = sorted(mcp_servers.keys())

    # 缺哪些（本专家用到、且靠 PAT 的）
    result["missing"] = [m for m in CAREER_BROKER_PAT_MCPS if m not in mcp_servers]

    # 找 PAT（只输出掩码，绝不明文）
    pat, source = find_tai_pat(mcp_servers)
    if pat:
        result["has_tai_pat"] = True
        result["tai_pat_masked"] = mask_pat(pat)
        result["tai_pat_source"] = source
        result["needs_pat_apply"] = False

    # 拼建议
    advice_parts = []
    if not result["missing"]:
        advice_parts.append(
            f"本专家需要太湖 PAT 的 MCP（{' + '.join(CAREER_BROKER_PAT_MCPS)}）你这边都装了，直接用。"
        )
    else:
        if result["has_tai_pat"]:
            advice_parts.append(
                f"你之前为 {result['tai_pat_source']} 配过太湖 PAT，"
                f"装 {' + '.join(result['missing'])} 时直接复用这同一份 PAT 即可（无需再申请）。"
            )
        else:
            advice_parts.append("还没装过任何用太湖 PAT 的 MCP，建议直接看 skills/career-broker-core/references/setup/00-mcp-bundle.md 一次装齐。")
    advice_parts.append("招活MCP 走一键授权，不在这里配，也不用 PAT。")

    result["advice"] = " ".join(advice_parts)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
