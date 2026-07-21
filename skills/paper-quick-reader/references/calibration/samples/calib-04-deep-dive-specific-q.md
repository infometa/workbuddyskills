---
paper_id: self-instruct-2023-deep
title: "Self-Instruct — deep mode with specific question"
venue: ACL 2023
year: 2023
mode: single
depth_used: [skim, deep]
anchor_tags: [deep-dive, specific-question, excerpt-required, high-confidence-expected]
calibration_status: normal
specific_question: "本文 52K 指令数据是怎么采样和过滤的？"
---

# 论文原文（同 calib-01，精读模式）

```
SelfInstruct: Aligning LMs with Self-Generated Instructions (ACL 2023)

3.2 Dataset Construction
We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples for each iteration. The final dataset contains 52K diverse instructions.

3.3 Filtering
We filter out instructions with ROUGE-L > 0.7 similarity to any existing instruction.
```

## 回归测试预期值

```json
{
  "expected_deep_dive_answers_count": 1,
  "expected_original_excerpts_count_min": 2,
  "expected_critical_analysis_sections_min": 2,
  "expected_breakdown": {
    "strong_checked_min": 2
  },
  "expected_match_distribution": {
    "high_min": 2
  },
  "required_anchor_matches": [
    {
      "claim_type": "deep_dive.original_excerpts",
      "text": "We start with 175 seed instructions and use 8 human-written",
      "min_confidence": "high"
    },
    {
      "claim_type": "deep_dive.original_excerpts",
      "text": "We filter out instructions with ROUGE-L > 0.7",
      "min_confidence": "high"
    }
  ],
  "forbidden_patterns": [
    "deep_dive.original_excerpts 含有不在原文中的句子",
    "critical_analysis 全部三段都留空"
  ]
}
```

## 本样例用途

- **锚点：精读模式的 gold standard** —— `original_excerpts` 必须 100% 来自原文且 5-gram=1.0
- **边界：multi-section 引用** —— 回答跨越 3.2 和 3.3 两个 section，Skill 应分别引用不同 page/section
- **反幻觉核心验证**：Skill 绝不能把中文答案写成"原文摘录"塞进 `original_excerpts[].text`
- **critical_analysis 三段式**：agree_with / question / complement 至少 2 段非空（输出 schema 硬约束）
