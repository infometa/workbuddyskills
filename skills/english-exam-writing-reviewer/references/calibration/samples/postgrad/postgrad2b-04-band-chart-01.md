---
exam_level: Postgrad2B
task_subtype: chart
band: 4
raw_score: 12
raw_score_max: 15
reference_source: "2020 考研英语二 B 节风格自构，mid-high anchor（第四档中位）"
anchor_tags: [subtype:chart, band:4, partial-analysis]
prompt: |
  Directions: Write an essay of about 150 words based on the bar chart below. In your essay,
  you should:
  1) describe the main information of the chart, and
  2) analyse possible reasons and draw your own conclusion.
  [Bar chart: "Online shopping expenditure of Chinese consumers aged 18-25 (2020-2024)"
   2020 — ¥3 800 / 2021 — ¥4 600 / 2022 — ¥5 900 / 2023 — ¥7 400 / 2024 — ¥8 900]
---

# 样例作文原文

> The bar chart clearly illustrates the annual online shopping expenditure of Chinese consumers
> aged 18 to 25 over the past five years. From 2020 to 2024, the figure has witnessed a steady
> upward trend, rising from around 3,800 yuan to nearly 8,900 yuan — more than doubling within
> half a decade. The growth has been particularly pronounced since 2022, when spending surpassed
> 5,900 yuan.
>
> Several factors may account for this phenomenon. For one thing, the rapid expansion of
> e-commerce platforms and the widespread use of mobile payment have made online purchasing
> remarkably convenient. For another, aggressive promotional campaigns such as Double 11 and
> livestreamed sales have effectively stimulated the consumption desire of young buyers.
>
> To sum up, the chart reflects both the digital transformation of consumption and the rising
> purchasing power of Chinese youth. Rational spending habits are therefore worth cultivating.

**字数**：约 152 词（达标）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **主要信息完整**：5 年数据走势（¶1）+ 2 个原因（¶2）+ 结论（¶3）；**数据精准**（`3,800` / `8,900` / `5,900` 三个关键数与图表一致）|
| 语法结构与词汇 | ✅ **较丰富**：`has witnessed a steady upward trend`、`more than doubling within half a decade`（独立主格/分词）、`For one thing / For another`；词汇 `pronounced / stimulated / consumption desire / rational spending` 在 mid-high tier |
| 语言准确性 | ✅ **基本准确**，1 处 tip（见下） |
| 衔接与连贯 | ⚠️ **衔接较好但不够多样**：过渡靠 `For one thing / For another / To sum up` 模板；段间无跨段呼应 |
| 格式与语域 | ✅ **合规**：图表文体三段结构，neutral-formal 语域 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | lexical | ¶2 | consumption desire | purchasing appetite / consumer enthusiasm | `consumption desire` 中式搭配，建议替换 |
| iss-2 | tip | discourse | ¶3 | Rational spending habits are therefore worth cultivating | ¶3 建议加 1 句回扣图表趋势（如 `As the figure continues to climb, young consumers should...`）| 结论段与图表数据脱钩 |

## 为什么是第四档（10–12），给 12 分

### 档内调节 +2（第四档高位）

- 对齐第四档"**切题，表达基本清楚**"——数据描述、原因、结论三要素齐全且精准；
- 对齐"**较好运用衔接手段**"——`particularly pronounced / for one thing / to sum up` 层次分明；
- **数据精准度** 这一英二 B 独有维度表现突出（3 个关键数点全对）——**档内取高位 12**；
- 距第五档仅差"**观点有深度 + 语言地道自然**"——¶3 结论停留于陈词滥调，未做深层解读。

## 为什么不是第五档（13–15）

| 边界判定要素 | 本文表现 | 第五档标准 |
|-------------|---------|------------|
| 观点深度 | ¶3 "rational spending" 陈词滥调 | 需要 **原创性评论**（如"消费金融化/代际财富转移"）|
| 语言地道度 | `consumption desire` 中式 | 需要 **母语者表达 + academic 词汇** |
| 衔接多样性 | For one thing / For another | 需要 **跨段呼应 + 多种连接手法** |

## 为什么不是第三档（7–9）

- **数据精准**——远超第三档"要点齐全但描述粗糙"；
- **语法词汇明显高于第三档**（现在完成时 + 独立主格 + mid-high tier）；
- 错误仅 2 tips，错误密度极低。

## 升档路径（→ 第五档 13–15）

1. **结论深化**：¶3 改为 `The steepening curve since 2022 likely mirrors both the maturation
   of livestream commerce and a generational shift toward experiential consumption. Yet beneath
   this growth lies a subtler concern: the normalization of debt-driven purchases among
   financially inexperienced youth.`
2. **去中式搭配**：`consumption desire` → `purchasing appetite` / `propensity to spend`
3. **跨段衔接**：¶2 首句改 `Behind these numbers, two structural forces stand out.`
4. **收尾回扣**：加 `A chart of rising figures, therefore, is also a chart of new habits in need
   of guidance.`

## 跨文体对比（vs postgrad2b-05-band-chart-01）

| 维度 | 本文（第四档）| postgrad2b-05（第五档）|
|------|-------------|----------------------|
| 数据精准度 | 3 点精准 | 全精准 + 增长率换算 |
| 原因分析深度 | 2 个表层原因 | 3 个结构性原因 + 反面风险 |
| 结论 | 陈词滥调 | 原创性评论 + 图表回扣 |
| 语言地道度 | mid-high + 1 处中式 | academic + 零中式 |

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2B",
  "task_subtype": "chart",
  "band": 4,
  "raw_score": 12,
  "final_score": 12,
  "data_accuracy_score": "high",
  "expected_key_rationale": [
    "5 年趋势 + 2 个原因 + 结论三要素齐全",
    "3 个关键数点全精准（数据精准度维度高）",
    "结论段陈词滥调故未至第五档",
    "1 处中式搭配 consumption desire"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2B", "effective": 152, "requirement_min": 120,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
