---
paper_id: lima-2023
title: "LIMA: Less Is More for Alignment"
venue: NeurIPS 2023
year: 2023
mode: single
depth_used: [skim]
anchor_tags: [small-dataset-edge-case, counterintuitive-result, few-numeric-anchors]
calibration_status: normal
---

# 论文原文

```
LIMA: Less Is More for Alignment

Chunting Zhou, Pengfei Liu, Puxin Xu, Srini Iyer et al. (Meta AI, 2023)

Abstract
Large language models are trained in two stages: (1) unsupervised pretraining from raw text, and (2) alignment via supervised fine-tuning and reinforcement learning from human feedback (RLHF). We measure the relative importance of these two stages by training LIMA, a 65B parameter LLaMA language model fine-tuned with the standard supervised loss on only 1,000 carefully curated prompts and responses, without any reinforcement learning or human preference modeling.

3. Training LIMA
We train LIMA using a 65B parameter LLaMA model, fine-tuning on just 1,000 carefully curated prompts and responses.

4. Human Evaluation
LIMA's responses are preferred over GPT-4 in 43% of cases.

7. Discussion
The Superficial Alignment Hypothesis: a model's knowledge and capabilities are learnt almost entirely during pretraining, while alignment teaches it which subdistribution of formats should be used. Future work requires scaling further data and investigating multi-turn dialogue.
```

## 回归测试预期值

```json
{
  "expected_breakdown": {
    "strong_checked_min": 5
  },
  "expected_match_distribution": {
    "high_min": 1,
    "medium_or_above_min": 3,
    "failed_max": 3
  },
  "required_anchor_matches": [
    { "text": "1,000 carefully curated prompts", "min_confidence": "high" },
    { "text": "65B parameter LLaMA", "min_confidence": "high" },
    { "text": "43%", "min_confidence": "medium" }
  ]
}
```

## 本样例用途

- **边界：小数据集场景** —— dataset 字段只有 1,000 条（vs 常见几万到几十万）
- **边界：反直觉结论** —— "Less Is More" 是 counter-intuitive finding；Skill 应完整保留作者原话
- **边界：少数字样本** —— 全文关键数字仅 1,000 / 65B / 43%，任一错匹配即失败（严格锚点）
- **回归作用**：验证小样本论文摘要不会被 Skill 过度扩写（应保持克制）
