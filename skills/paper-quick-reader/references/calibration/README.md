# 校准集（Calibration Set）· v0.1.0

> 本目录收录 **5 篇锚点论文样例 + 人工标注预期输出**，用于：
>
> 1. **Few-shot 定档**：Skill 在运行时可引用这些锚点作为 skim / deep / compare 的 in-context demo
> 2. **回归测试**：每次 Skill 迭代必须跑 `scripts/calibrate.py --validate` **5/5 全绿**才能发布
> 3. **可追溯差异化**：声明 Skill"用这批样本做过对齐"，可审计可追溯

---

## 总览

| 维度 | 规模 | 说明 |
|---|---|---|
| **锚点样例数** | **5 篇** | 覆盖 single / compare × skim / deep 全部四格 |
| **gold-standard 样例** | **1 篇** | `calib-01` Self-Instruct（核心回归基线）|
| **edge_case 样例** | **1 篇** | `calib-03` survey 论文（无 dataset / 无 key_results 数字）|
| **v0.2 扩展目标** | **10+ 篇** | 每个 anchor_tag 至少覆盖 2 篇（当前多为 1 篇）|

### 按 mode × depth 覆盖

| mode \ depth | skim | skim+deep | skim+compare |
|---|---|---|---|
| single | 3 | 1 | — |
| compare | — | — | 1 |

---

## 目录结构

```
references/calibration/
├── README.md                                       # 本文件
└── samples/                                        # 5 篇锚点样例
    ├── calib-01-self-instruct-skim.md              # gold standard · 经典 · 数字锚点丰富
    ├── calib-02-lima-skim.md                       # 小数据集 · counter-intuitive · 少数字
    ├── calib-03-survey-no-dataset.md               # edge: survey 论文 · 无 dataset / 无数字
    ├── calib-04-deep-dive-specific-q.md            # deep 模式 · 高置信度 excerpt 要求
    └── calib-05-compare-two-papers.md              # 最小 compare · 正交方法对比
```

---

## 每个样例的结构

```markdown
---
paper_id: <稳定 ID，供 expected 互相引用>
title: "<论文标题>"
venue: <会议/期刊>
year: <年份>
mode: single | compare
depth_used: [skim] | [skim, deep] | [skim, compare] | [skim, guided, deep]
anchor_tags: [tag1, tag2, ...]
calibration_status: normal | edge_case | gold-standard
---

# 论文原文
（稳定的 pasted_text，保证 ngram 可复现）

## 回归测试预期值

```json
{
  "expected_breakdown": {...},
  "expected_match_distribution": {...},
  "expected_removed_max": ...,
  "required_anchor_matches": [...],
  "forbidden_patterns": [...]
}
```

## 本样例用途
（说明该样例锚定什么边界 / 什么场景）
```

---

## 运行校准

### 扫描 + 覆盖矩阵

```bash
cd <skill-root>
python3 scripts/calibrate.py                         # Markdown 覆盖报告
python3 scripts/calibrate.py --format json           # 机读 expected JSON
python3 scripts/calibrate.py --coverage-only         # 仅覆盖矩阵
```

### 单样例回归（推荐 CI 脚本用）

```bash
python3 scripts/calibrate.py --validate \
  --sample calib-01-self-instruct-skim.md \
  --result path/to/result.json \
  --audit  path/to/provenance-audit.json
```

返回 `status: pass` 且 exit code = 0 表示通过。

### 批量校准（CI 推荐）

每个样例的 `result.json` 需由 Skill 真实运行产出（此处以 `references/examples/` 下已完成的示例复用）：

```bash
# 示例：把 examples/single-skim-selfinstruct 作为 calib-01 的实跑结果
python3 scripts/calibrate.py --validate \
  --sample calib-01-self-instruct-skim.md \
  --result references/examples/single-skim-selfinstruct/result.json \
  --audit  references/examples/single-skim-selfinstruct/provenance-audit.json

# calib-04 → single-deep-dive-selfinstruct
python3 scripts/calibrate.py --validate \
  --sample calib-04-deep-dive-specific-q.md \
  --result references/examples/single-deep-dive-selfinstruct/result.json \
  --audit  references/examples/single-deep-dive-selfinstruct/provenance-audit.json
```

---

## expected 字段语义

| 字段 | 类型 | 含义 |
|---|---|---|
| `expected_breakdown.X_min` | int | 该类 claim（strong / medium / weak）最少数量 |
| `expected_match_distribution.X_min` | int | 该置信度（high / medium / low / failed）最少数量 |
| `expected_match_distribution.X_max` | int | 该置信度最多数量（用于 `failed_max` 反幻觉上限）|
| `expected_match_distribution.medium_or_above_min` | int | high + medium 之和最小值（常用）|
| `expected_removed_max` | int | 审计剔除条数上限 |
| `required_anchor_matches[].text` | string | 必须出现的锚点文本（子串匹配 `claim_text`）|
| `required_anchor_matches[].min_confidence` | enum | 最小置信度等级（`failed < low < medium < high`）|
| `forbidden_patterns[]` | string[] | 反幻觉黑名单（当前仅作为文档约束，v0.2 引入自动扫描）|

---

## v0.2 扩展方向

1. **补到 10 篇以上** —— 每个 anchor_tag 至少覆盖 2 篇
2. **跨考试/领域锚点** —— 当前集中在 alignment 方向，v0.2 加 RAG / multi-agent / vision-language 各 2 篇
3. **forbidden_patterns 自动扫描** —— v0.1 仅文档层面，v0.2 让 `calibrate.py` 扫 result.json 文本
4. **端到端跑 Skill 的全自动 CI 脚本** —— 当前需人工喂 result.json；v0.2 跑 Skill 本体 → audit → validate 一条龙
