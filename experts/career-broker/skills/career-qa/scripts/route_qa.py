#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_qa.py · 问询路由判断器
仅做关键词匹配，不调任何外部服务。

用法：
    python route_qa.py --query "活水有试用期吗？"   # → recruit_knowledge
    python route_qa.py --query "VPN 连不上"        # → xiaoq
    python route_qa.py --query "你好"              # → xiaoq（默认）
"""
import argparse
import json
import sys

RECRUIT_KNOWLEDGE_KEYWORDS = [
    "活水", "入池", "冷却", "匿名池",
    "内推", "调岗", "转岗", "跨BG",
    "校招", "社招", "招聘流程",
    "Offer鹅", "Offer 鹅", "智能问询",
]

XIAOQ_KEYWORDS = [
    # HR
    "年假", "病假", "产假", "陪产假", "婚假", "丧假", "工龄", "司龄",
    "离职流程", "转正",
    "公积金", "社保", "五险一金", "商业保险", "体检", "绩效流程",
    # IT/行政
    "VPN", "内网", "蓝鲸", "工位", "会议室", "班车", "门禁", "卡证",
    "设备申请", "电脑申请", "报修",
    # 财经
    "报销", "差旅", "出差", "机票", "采购", "合同", "付款", "固定资产",
    # 新人
    "新人", "入职", "导师", "带教", "师傅", "徒弟",
    # 学习
    "课程", "学习积分", "学习记录", "QLearning", "学堂", "行家",
]


def route(query: str) -> str:
    """
    返回 'recruit_knowledge' 或 'xiaoq'。
    判断顺序：招聘问询知识库关键词 → 小Q 关键词 → 默认小Q。
    """
    if not query:
        return "xiaoq"
    q = query
    for kw in RECRUIT_KNOWLEDGE_KEYWORDS:
        if kw in q:
            return "recruit_knowledge"
    for kw in XIAOQ_KEYWORDS:
        if kw in q:
            return "xiaoq"
    return "xiaoq"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    args = ap.parse_args()
    target = route(args.query)
    print(json.dumps({"route": target, "query": args.query}, ensure_ascii=False))


if __name__ == "__main__":
    # 自测用例
    if len(sys.argv) == 1:
        cases = [
            ("活水有试用期吗", "recruit_knowledge"),
            ("VPN 连不上", "xiaoq"),
            ("年假怎么算", "xiaoq"),
            ("怎么报销出差机票", "xiaoq"),
            ("内部活水冷却期是多久", "recruit_knowledge"),
            ("校招简历筛选规则", "recruit_knowledge"),
            ("新人入职第一天做什么", "xiaoq"),
            ("课程推荐", "xiaoq"),
            ("你好", "xiaoq"),
        ]
        ok = sum(1 for q, expected in cases if route(q) == expected)
        for q, expected in cases:
            actual = route(q)
            mark = "✅" if actual == expected else "❌"
            print(f"{mark} [{actual:17}] {q}  (expected {expected})")
        print(f"\n{ok}/{len(cases)} 通过")
    else:
        main()
