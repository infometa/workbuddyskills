---
paper_id: survey-rlhf-2023
title: "A Survey of Reinforcement Learning from Human Feedback"
venue: arxiv preprint
year: 2023
mode: single
depth_used: [skim]
anchor_tags: [survey, no-dataset-field, no-key-results-numbers, theory-paper]
calibration_status: edge_case
---

# 论文原文（合成 survey 节选 —— 用于测试 null dataset 字段）

```
A Survey of Reinforcement Learning from Human Feedback

Christian Wirth et al. (2023)

Abstract
This survey provides a comprehensive review of reinforcement learning from human feedback (RLHF). We categorize existing methods into three families: preference-based learning, direct policy optimization, and reward model distillation. Unlike empirical papers, this survey does not introduce new datasets or report benchmark numbers; instead, it synthesizes findings across 147 prior works.

1. Introduction
The alignment problem has motivated three decades of research. This survey aims to unify disparate threads into a coherent taxonomy.

3. Taxonomy
We organize methods along two axes: (a) feedback granularity (scalar / comparative / demonstrative), and (b) optimization target (reward model / policy / preference distribution).

8. Open Challenges
We identify five unresolved questions: reward hacking, preference inconsistency, sample inefficiency, distributional shift, and interpretability.
```

## 回归测试预期值

```json
{
  "expected_summary_card_fields_nullable": ["dataset", "key_results"],
  "required_summary_card_notes": [
    "dataset 字段应为 null 或 '不适用（综述类论文，未引入新数据集）'",
    "key_results 应聚焦概念性贡献而非数字"
  ],
  "expected_breakdown": {
    "strong_checked_min": 4
  },
  "expected_match_distribution": {
    "high_min": 0,
    "medium_or_above_min": 2,
    "failed_max": 4
  },
  "required_anchor_matches": [
    { "text": "three families", "min_confidence": "medium" },
    { "text": "147 prior works", "min_confidence": "medium" }
  ],
  "forbidden_patterns": [
    "编造任何未出现在原文中的 benchmark 数字（如 X%、Y 分）"
  ]
}
```

## 本样例用途

- **边界：综述类论文** —— 无 dataset / 无 key_results 数字
- **边界：非实证论文** —— Skill 应自动判定并给出 null 或"不适用"的规范回应，而非**虚构数字**
- **反幻觉核心验证**：Skill 绝不能为 survey 论文"造出"一个 benchmark 表格
- **未来扩展**：本样例可扩展测试 `key_results: null` 的前端渲染是否正确处理
