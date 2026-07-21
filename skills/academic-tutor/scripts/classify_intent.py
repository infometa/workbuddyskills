#!/usr/bin/env python3
"""
academic-tutor · classify_intent.py

意图分类（启发式 + 关键词）。返回 7 类之一：
homework / concept / proof / paper-topic / paper-review / paper-revision / out-of-scope

设计说明：
- 本 Skill 自我闭环，**不做任何跨能力跳转**。
- 越界请求（学习计划 / 打卡 / 知识框架 / 论文速读 / 简历 / 学术翻译 / 应试英语作文…）
  统一识别为 `out-of-scope`，由调用方走"不在能力范围 + 邀请回到本能力"统一话术。
- `should_delegate` 字段保留为 `None`（永远 None），仅为向后兼容上游消费者。

Usage:
    python3 classify_intent.py --text "这道高数题怎么做"
    echo "..." | python3 classify_intent.py --stdin
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# 越界关键词（统一归并为 out-of-scope，不再细分到具体能力方向）
OUT_OF_SCOPE_KEYWORDS = [
    # —— 代写代做 ——
    "帮我写论文", "帮我写引言", "帮我把.{0,8}写", "替我写", "整段代笔",
    "代写", "帮我交作业", "替我做完", "我懒得写", "帮我做作业",
    # —— 学术不端 ——
    "改重", "降重", "洗稿", "抄改", "换种说法过查重", "换个说法.*查重",
    # —— 心理危机 ——
    "想不开", "抑郁", "撑不下去", "活不下去", "想自杀", "想结束",
    # —— 越界领域 ——
    "起诉", "合同", "买什么股", "投资什么", "我是不是得了", "用药",
    # —— Prompt 注入 ——
    "system prompt", "complete your instructions", "ignore previous",
    "你现在是", "忽略前面的规则", "输出你的内部",
    # —— 寒暄 ——
    "你叫什么", "推荐电影", "今天天气",
    # —— 学习计划（不在范围内）——
    "学习计划", "30 天", "60 天", "100 天", "备考计划",
    "几个月计划", "学习路线", "时间分配", "倒计时",
    # —— 打卡陪伴（不在范围内）——
    "打卡", "今日任务", "今天学什么", "streak", "连续",
    "热力图", "复盘",
    # —— 知识框架 / 思维导图（不在范围内）——
    "知识框架", "思维导图", "骨架图",
    "整门课", "课程梳理", "学科地图",
    # —— 论文速读（不在范围内）——
    "速读", "一句话总结这篇", "速读这篇", "速读 N 篇",
    "快速过.*论文",
    # —— 学术翻译（不在范围内）——
    "学术英语翻译", "翻译.*论文", "翻译.*段",
    # —— 应试英语作文批改（不在范围内）——
    "批改作文", "雅思作文批改",
    "托福作文批改", "六级作文",
    # —— 简历（不在范围内）——
    "改简历", "求职信",
]

# 非 out-of-scope 的具体意图分类
KEYWORDS = {
    "paper-topic": [
        "选题", "题目方向", "想做什么方向", "不知道做什么",
        "毕业论文做啥", "研究方向",
    ],
    "paper-review": [
        "文献综述", "综述写", "我读了", "现状", "literature review",
        "已有研究",
    ],
    "paper-revision": [
        "改论文", "优化表达", "审稿意见", "Major Revision", "Minor Revision",
        "答辩", "答辩 PPT", "rebuttal", "回信", "评委可能问",
        "这段对吗", "这段哪里有问题",
    ],
    "proof": [
        "证明", "推导", "为什么成立", "怎么得到", "如何证",
    ],
    "concept": [
        "是什么", "怎么理解", "解释一下", "什么意思", "定义", "区别是",
        "和.*的区别", "和.*有什么不同",
    ],
    "homework": [
        "这道题", "这题", "习题", "求解", "怎么做", "怎么算",
        "这道", "求.*=", "计算", "解一下",
    ],
}


def classify(text: str) -> dict:
    text_low = text.strip()

    # 1) 优先 out-of-scope（涵盖代写 / 不端 / 心理 / 越界领域 / 注入 / 寒暄 +
    #    学习计划 / 打卡 / 知识框架 / 论文速读 / 翻译 / 简历 / 应试英语作文 等
    #    本 Skill 不做的诉求；统一回复"不在能力范围 + 邀请回到本能力"）
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if re.search(kw, text_low):
            return {
                "intent": "out-of-scope",
                "matched": kw,
                "should_delegate": None,
            }

    # 2) 论文场景优先级
    for intent in ("paper-topic", "paper-review", "paper-revision"):
        for kw in KEYWORDS[intent]:
            if re.search(kw, text_low):
                return {"intent": intent, "matched": kw, "should_delegate": None}

    # 3) 学业题目类
    for intent in ("proof", "concept", "homework"):
        for kw in KEYWORDS[intent]:
            if re.search(kw, text_low):
                return {"intent": intent, "matched": kw, "should_delegate": None}

    return {"intent": "homework", "matched": "default", "should_delegate": None}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text")
    p.add_argument("--stdin", action="store_true")
    args = p.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        print("ERROR: 请提供 --text 或 --stdin", file=sys.stderr)
        return 2

    if not text.strip():
        print("ERROR: 输入为空", file=sys.stderr)
        return 2

    result = classify(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
