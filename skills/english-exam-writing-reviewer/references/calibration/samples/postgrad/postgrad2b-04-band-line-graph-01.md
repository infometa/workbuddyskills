---
exam_level: Postgrad2B
band: 4
raw_score: 11
task_subtype: line_graph
chart_subtype: line_graph
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, line_graph]
reference_source: "基于考研英语二 2025 折线图真题首考风格自构（中国家庭恩格尔系数走势）"
prompt: |
  Write an essay of about 150 words based on the line graph below, in which you should:
  1) describe the chart, and
  2) give your comments.
  The graph traces the Engel coefficient of Chinese urban households from 2004 to 2024,
  declining from 38% in 2004, falling steadily to 30% by 2014, and then dropping more
  gently to 26% by 2024, with a brief plateau between 2018 and 2020.
---

# 样例作文原文

```
The line graph charts the trajectory of the Engel coefficient among
Chinese urban households from 2004 to 2024, revealing a clear long-term
decline punctuated by a brief period of stagnation.

During the first decade, the coefficient fell markedly from 38% in 2004
to 30% in 2014, averaging a decrease of roughly 0.8 percentage points
per year. Thereafter, the downward trend slowed considerably, with the
figure easing to 26% by 2024. Worth noting is the plateau between 2018
and 2020, during which the coefficient hovered around 28%, coinciding
with the onset of the pandemic.

Two interrelated factors largely account for this trend. On the one
hand, rising disposable incomes have diversified household spending
beyond subsistence needs. On the other hand, the pandemic-era plateau
reflects a temporary tightening of consumer budgets, after which
recovery gradually resumed.

Overall, the downward trajectory is expected to persist, albeit at a
more modest pace.
```

（正文约 155 词）

---

# 人工阅卷批注（Postgrad2B · line_graph · 第四档）

## line_graph 专属检查项（v1.6 `chart-verbs.md` §2.4）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 时间跨度 + 总趋势 | 开场概述趋势 | `clear long-term decline punctuated by a brief period of stagnation` | ✅ 高质量开场 |
| 分阶段描述（至少 2 阶段）| 折线图核心能力 | 第一个十年 + 之后 + 2018-2020 平台 = 3 阶段 | ✅ |
| 变化率/速率 | `by X points / percentage points per year` | `averaging a decrease of roughly 0.8 percentage points per year` | ✅ 折线图专属 |
| 拐点/平台识别 | `plateau / peak / trough / level off` | `plateau between 2018 and 2020 / hovered around 28%` | ✅ |
| 归因 + 展望 | 解释 + 预测 | 收入 + 疫情双因素 + `expected to persist, albeit at a more modest pace` | ✅ |

→ **5/5 项达标** + 速率表达 + 平台识别（line_graph 专属加分项）。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| 2004: 38% | ✅ |
| 2014: 30% | ✅ |
| 2024: 26% | ✅ |
| 2018-2020 plateau: ~28% | ✅（`hovered around 28%`）|
| avg rate ~0.8 pp/year | ✅ 自行计算精确 |

→ 5/5 精确 + 自行推算速率（加分）。

## 5 维诊断

1. **任务完成度**：分阶段描述 + 速率 + 拐点 + 归因 + 展望齐全
2. **语法结构与词汇**：较丰富
   - 非限定：`punctuated by a brief period of stagnation / coinciding with the onset of the pandemic`
   - 倒装：`Worth noting is the plateau between 2018 and 2020` ✅
   - high-tier：`trajectory / punctuated / stagnation / disposable incomes / subsistence / albeit`
3. **语言准确性**：准确
4. **衔接与连贯**：`During the first decade / Thereafter / Worth noting is / On the one hand / On the other hand / Overall` 推进严谨
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| 全文 | 无明显错误 | — | — | — |

合计 0 critical + 0 warning + 0 tip — 语言水准稳定在第四档上界。

## 为什么第四档不是第五档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| line_graph 五要素齐全 + 速率 + 平台 | 5/5+ | 5 |
| 数据精准度 + 自推算速率 | 5/5+ | 5 |
| 复杂结构 | 非限定 ×2 + 倒装 ×1 | 5 |
| high-tier 词汇 | 6 处 | 5 |
| academic tier | 0 处（如 `secular decline / macroeconomic headwind`）| **4** |
| 辩证 / 多因素 | 双因素但未深度辩证 | 4 |

→ **接近第五档但缺 academic tier = 第四档上界（11 分）**。

## 升档路径（Postgrad2B line_graph · 4 → 5）

1. 加 academic tier：`rising disposable incomes have diversified household spending beyond subsistence needs` → `rising disposable incomes have restructured consumption beyond mere subsistence, accompanied by the Engel curve's secular decline`
2. 加辩证：`Admittedly, the Engel coefficient alone cannot capture welfare nuances; nevertheless, its long-run decline remains a robust indicator of livelihood improvement.`
3. 展望加政策维度：`the downward trajectory is expected to persist, albeit at a more modest pace` → `the downward trajectory is expected to persist, albeit moderated by demographic headwinds and post-pandemic consumption caution`

---

# 该样例用途

- **v1.7 chart_subtype = line_graph 中档位锚点**：首篇 line_graph 校准（**折线图为 2025 年首考题型**）
- **速率 + 平台识别金标**：`0.8 percentage points per year` + `plateau between 2018 and 2020` 是 line_graph 的专属高阶能力
- **倒装 + 非限定示范**：`Worth noting is the plateau...` 为 line_graph 第四档的标志性句式
- **Step 2 chart_subtype 识别**：Directions 含 "line graph / traces... from X to Y" → `chart_subtype = "line_graph"`
