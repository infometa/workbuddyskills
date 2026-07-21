---
paper_id: self-instruct-2023
title: "Self-Instruct: Aligning Language Models with Self-Generated Instructions"
venue: ACL 2023
year: 2023
mode: single
depth_used: [skim]
anchor_tags: [classic, instruction-tuning, rich-numeric-anchors, gold-standard]
min_required_ngram_high: 0
min_required_ngram_medium_or_above: 5
calibration_status: normal
---

# 论文原文（pasted_text，稳定可复现）

```
SelfInstruct: Aligning LMs with Self-Generated Instructions

Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A. Smith, Daniel Khashabi, Hannaneh Hajishirzi (ACL 2023)

Abstract
Large instruction-tuned language models demonstrate strong zero-shot generalization. We introduce Self-Instruct, a framework that improves instruction-following by bootstrapping off the model's own generations. Starting from 175 seed instructions, we generate 52K examples and show substantial gains over GPT-3 baseline.

3. Method
Our approach starts with 175 seed instructions and uses 8 human-written and 2 model-generated examples as in-context demonstrations at each iteration.

3.2 Dataset Construction
We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples for each iteration. The final dataset contains 52K diverse instructions.

3.3 Filtering
We filter out instructions with ROUGE-L > 0.7 similarity to any existing instruction.

5. Results
On SuperNI benchmark, Self-Instruct improves GPT-3 vanilla ROUGE-L from 34.6 to 46.2, a 33% relative gain. Performance approaches InstructGPT_001 within 5%.

6. Limitations
Our method depends on the base model's initial ability. We do not evaluate on smaller models. Long-tail tasks remain under-covered.
```

## 回归测试预期值

回归测试时，Skill 输出的 `provenance-audit.json` 应满足：

```json
{
  "expected_breakdown": {
    "strong_checked_min": 2,
    "medium_checked_min": 4
  },
  "expected_match_distribution": {
    "medium_or_above_min": 5,
    "failed_max": 2
  },
  "expected_removed_max": 1,
  "required_anchor_matches": [
    { "text": "175", "min_confidence": "medium" },
    { "text": "52K", "min_confidence": "medium" },
    { "text": "34.6", "min_confidence": "medium" },
    { "text": "46.2", "min_confidence": "medium" }
  ]
}
```

> 注：skim 模式下 claim_text 为中文改写，锚点应选会出现在**改写后中文文本**里的数字。
> 对精读 / deep 模式，用英文 ngram 原文锚点（见 `calib-04`）。

## 本样例用途

- **锚点：最经典的 instruction-tuning 论文**，数字 / 专名锚点极丰富
- **边界：skim 模式 baseline** —— 其它 skim 样例分差不超过本例 ±2
- **容错：中文改写的 cross-language paraphrase 放宽**（method / dataset 全为 CJK 改写但数字全中 → medium）
- **Gold standard**：任何 Skill 迭代都必须使本样例的 required_anchor_matches **5/5 通过**
