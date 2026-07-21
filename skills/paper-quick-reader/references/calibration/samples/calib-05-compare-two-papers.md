---
paper_id: compare-selfinstruct-vs-lima
title: "Self-Instruct vs LIMA — minimal 2-paper compare"
mode: compare
papers: [self-instruct-2023, lima-2023]
depth_used: [skim, compare]
anchor_tags: [compare-min, 2-papers, orthogonal-approaches]
compare_dimensions: [method, dataset, key_results, limitations]
calibration_status: normal
---

# 论文原文（复用 calib-01 + calib-02）

> 粘贴 `calib-01-self-instruct-skim.md` 与 `calib-02-lima-skim.md` 中的原文段作为 compare 输入的 `papers[0].content` 和 `papers[1].content`。

## 回归测试预期值

```json
{
  "expected_comparison_table_rows": 4,
  "expected_comparison_dimensions": ["method", "dataset", "key_results", "limitations"],
  "expected_narrative_min_chars": 100,
  "expected_narrative_must_mention": [
    "Self-Instruct 或 A",
    "LIMA 或 B",
    "52K 或 52,000 或 52 K",
    "1,000 或 1000"
  ],
  "expected_breakdown": {
    "strong_checked_min": 8
  },
  "expected_match_distribution": {
    "high_min": 2,
    "medium_or_above_min": 6
  },
  "required_anchor_matches": [
    {
      "paper_label": "A",
      "claim_type": "comparison.table.dataset",
      "text": "52K",
      "min_confidence": "medium"
    },
    {
      "paper_label": "B",
      "claim_type": "comparison.table.dataset",
      "text": "1,000",
      "min_confidence": "high"
    }
  ],
  "forbidden_patterns": [
    "narrative 中包含不在任何一篇原文中的数字",
    "cell 中出现 'N/A' 却不给出 provenance"
  ]
}
```

## 本样例用途

- **锚点：最小 compare 场景（2 篇）** —— 用于验证 compare 的边界：2 <= papers_count <= 10
- **边界：正交方法对比** —— A 用数据 bootstrap（52K 自生成），B 用数据精选（1,000 人工）；narrative 必须点出"数据路线正交"
- **回归作用**：验证 narrative 不虚构跨论文的数字关联（常见幻觉场景）
- **扩展**：v0.2 可添加 `cross_paper_answer` 测试（本样例 `specific_question` 留空，不触发）
