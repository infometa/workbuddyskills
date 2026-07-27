#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_self_assessments.py
拉取员工**全部历史自评**：
  - 列表 listMyAssessments
  - 近 3 期完整 getSelfAssess
  - 更早期仅保留标题，等 build_profile 时让 LLM 汇总

调用：
    python fetch_self_assessments.py --staff-id 12345678 [--out-dir raw/]
    python fetch_self_assessments.py --staff-id 12345678 --mock

依赖：
    - connector:自评MCP（无需 token）
    - 实际调用通过 MCP 网关，本脚本提供契约 + mock，真正调用由 agent 在对话中触发
      （或后续接入 mcp-py-client 直接 stdio 调）

输出：
    raw/self_assess_index.json    # 列表（全量）
    raw/self_assess_<asId>.json   # 近 3 期每期一个文件
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Mock：v2 阶段 LLM agent 直接通过 MCP 工具调用，本脚本主要承担"序列化产物"职责
# 真实调用由 agent 在对话中通过 mcp__自评MCP__listMyAssessments / getSelfAssess 完成


def call_list_my_assessments(skip: int = 0, limit: int = 50) -> dict:
    """
    契约：
    {
      "data": {
        "assessments": [
          { "_id": "...", "periodId": "...", "periodName": "2025下半年人才评估",
            "staffId": "", "staffName": "", "statusKey": "AssessFinish" }
        ],
        "count": 1
      }
    }
    """
    raise NotImplementedError(
        "首版未直连 MCP 网关。建议由 agent 在对话中调用 mcp__自评MCP__listMyAssessments，"
        "把返回 JSON 通过 stdin 喂给本脚本：cat list.json | fetch_self_assessments.py --from-stdin"
    )


def call_get_self_assess(as_id: str) -> dict:
    """
    契约：
    {
      "data": {
        "dimensions": [
          {
            "typeId": "Achievement",
            "typeName": "业务",
            "objectives": [
              { "index": 0, "oName": "...", "keyResults": "KR1: ...",
                "outcome": "...", "highPriority": false }
            ]
          }
        ]
      }
    }
    """
    raise NotImplementedError(
        "首版未直连 MCP 网关。同上，由 agent 调用 mcp__自评MCP__getSelfAssess(asId=...) 后喂给本脚本。"
    )


def load_mock_index() -> dict:
    return {
        "data": {
            "assessments": [
                {"_id": "ass-2025h2", "periodId": "p2025h2", "periodName": "2025下半年人才评估",
                 "staffId": "", "staffName": "", "statusKey": "AssessFinish"},
                {"_id": "ass-2025h1", "periodId": "p2025h1", "periodName": "2025上半年人才评估",
                 "staffId": "", "staffName": "", "statusKey": "AssessFinish"},
                {"_id": "ass-2024h2", "periodId": "p2024h2", "periodName": "2024下半年人才评估",
                 "staffId": "", "staffName": "", "statusKey": "AssessFinish"},
                {"_id": "ass-2024h1", "periodId": "p2024h1", "periodName": "2024上半年人才评估",
                 "staffId": "", "staffName": "", "statusKey": "AssessFinish"},
                {"_id": "ass-2023h2", "periodId": "p2023h2", "periodName": "2023下半年人才评估",
                 "staffId": "", "staffName": "", "statusKey": "AssessFinish"},
            ],
            "count": 5,
        }
    }


def load_mock_assess(as_id: str) -> dict:
    seed = {
        "ass-2025h2": {
            "dimensions": [{
                "typeId": "Achievement", "typeName": "业务", "objectives": [
                    {"index": 0, "oName": "校招核心业务诉求挖掘与落地",
                     "keyResults": "KR1: 推进官网简历游戏经历改造\nKR2: 用工类型改造\nKR3: 特殊青云录用流程",
                     "outcome": "游戏经历模块 8/28 上线 26,681 份；用工类型 2026/1/1 上线；青云 11/6 上线。",
                     "highPriority": False},
                    {"index": 1, "oName": "内部工具体验优化",
                     "keyResults": "KR1: 匿名池链路优化\nKR2: 内部挂号方案\nKR3: 19 个日常需求",
                     "outcome": "匿名池活跃 5,100+，沟通发起 3,786 次（消息量 +1000%）。",
                     "highPriority": False},
                    {"index": 2, "oName": "AI+行业 专业能力提升",
                     "keyResults": "KR1: 集体面试报告\nKR2: 对外智能问询\nKR3: 招聘 AI 运营\nKR4: HR STAR",
                     "outcome": "集体面试报告 412 份 / 207 面试官 / 84.9% 准确率。",
                     "highPriority": False},
                ]
            }]
        },
        "ass-2025h1": {
            "dimensions": [{
                "typeId": "Achievement", "typeName": "业务", "objectives": [
                    {"index": 0, "oName": "招聘 AI 第一阶段产品建设",
                     "keyResults": "KR1: 集体面试报告 0-1\nKR2: AI 搜索接入",
                     "outcome": "集体面试报告功能 5 月上线，AI 搜索 6 月小流量灰度。",
                     "highPriority": True},
                    {"index": 1, "oName": "内部匿名池 0-1",
                     "keyResults": "KR1: 匿名池产品方案\nKR2: 匿名沟通能力",
                     "outcome": "匿名池 4 月上线，首批入池 500+。",
                     "highPriority": False},
                ]
            }]
        },
        "ass-2024h2": {
            "dimensions": [{
                "typeId": "Achievement", "typeName": "业务", "objectives": [
                    {"index": 0, "oName": "校招简历搜推优化",
                     "keyResults": "KR1: 简历搜索召回率\nKR2: 推荐策略",
                     "outcome": "搜索召回率提升 30%。",
                     "highPriority": False},
                ]
            }]
        },
        "ass-2024h1": {
            "dimensions": [{
                "typeId": "Achievement", "typeName": "业务", "objectives": [
                    {"index": 0, "oName": "校招系统重构基础能力",
                     "keyResults": "KR1: ...", "outcome": "...", "highPriority": False},
                ]
            }]
        },
        "ass-2023h2": {
            "dimensions": [{
                "typeId": "Achievement", "typeName": "业务", "objectives": [
                    {"index": 0, "oName": "校招招聘流程数字化",
                     "keyResults": "KR1: ...", "outcome": "...", "highPriority": False},
                ]
            }]
        },
    }
    return {"data": seed.get(as_id, {"dimensions": []})}


def main():
    ap = argparse.ArgumentParser(description="Fetch all self-assessments (list + recent 3 detailed)")
    ap.add_argument("--staff-id", required=True)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--recent-n", type=int, default=3, help="完整解析最近 N 期")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--from-stdin", action="store_true",
                    help="预留：从 stdin 读 list/detail JSON（agent 喂数据用）")
    args = ap.parse_args()

    if not args.out_dir:
        args.out_dir = str(Path.home() / ".workbuddy" / "career-broker" / args.staff_id / "raw")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 列表
    if args.mock:
        list_data = load_mock_index()
    else:
        try:
            list_data = call_list_my_assessments()
        except NotImplementedError as e:
            print(f"[WARN] {e}", file=sys.stderr)
            sys.exit(2)

    (out_dir / "self_assess_index.json").write_text(
        json.dumps(list_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    assessments = list_data["data"].get("assessments", [])
    count_total = list_data["data"].get("count", len(assessments))

    # 按 periodId 倒序（mock 数据已倒序，这里防御性 sort）
    assessments_sorted = sorted(assessments, key=lambda x: x.get("periodId", ""), reverse=True)
    recent = assessments_sorted[: args.recent_n]
    earlier = assessments_sorted[args.recent_n :]

    # 2. 近 N 期完整
    expanded_files = []
    for a in recent:
        as_id = a["_id"]
        if args.mock:
            detail = load_mock_assess(as_id)
        else:
            try:
                detail = call_get_self_assess(as_id)
            except NotImplementedError as e:
                print(f"[WARN] {as_id} {e}", file=sys.stderr)
                continue
        path = out_dir / f"self_assess_{as_id}.json"
        path.write_text(json.dumps({**a, "detail": detail["data"]}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        expanded_files.append({"asId": as_id, "period": a["periodName"], "path": str(path), "expanded": True})

    earlier_meta = [
        {"asId": a["_id"], "period": a["periodName"], "path": None, "expanded": False}
        for a in earlier
    ]

    # 3. 元数据汇总
    summary = {
        "n_total": count_total,
        "n_expanded": len(expanded_files),
        "expanded_files": expanded_files,
        "earlier_meta": earlier_meta,
    }
    (out_dir / "self_assess_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"ok": True, "out_dir": str(out_dir), **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
