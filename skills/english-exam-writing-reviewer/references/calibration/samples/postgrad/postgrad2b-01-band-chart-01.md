---
exam_level: Postgrad2B
task_subtype: chart
band: 1
raw_score: 3
raw_score_max: 15
reference_source: "2018 考研英语二 B 节风格自构，low anchor（第一档高位）——数据错位 + 字数不足双扣分金标样例"
anchor_tags: [subtype:chart, band:1, gold-standard-data-error, gold-standard-shortfall]
prompt: |
  Directions: Write an essay of about 150 words based on the pie chart below. In your essay,
  you should:
  1) describe the main information of the chart, and
  2) analyse possible reasons and give your conclusion.
  [Pie chart: "Sources of household income in a Chinese city (2023)"
   Wages 55% | Investments 20% | Pensions 15% | Others 10%]
---

# 样例作文原文

> The chart show household income in a city. Wages is 45%. Investments is 25%. Pensions is 10%.
> Others is 20%. We can see wages is biggest.
>
> There are many reasons. People need to work to get money. So wages is very important. People
> also want to invest money. So investments is second. I think this chart is good.
>
> We should work hard and save money.

**字数**：约 72 词（要求 "about 150 words"，严重偏短 52%）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌❌ **数据全部错误**：Wages 55% 写成 45%，Investments 20% 写成 25%，Pensions 15% 写成 10%，Others 10% 写成 20%——**4 个关键数据全错位**，严重偏离图表；原因段仅 1 个笼统理由（"人要工作"），无第二层分析；结论段仅一句口号 |
| 语法结构与词汇 | ❌ **语法错误密集**：全文 `wages is / investments is / pensions is` 主谓一致全错（复数主语 + is）；无任何从句/分词；词汇全部低阶 `many / good / important / hard` |
| 语言准确性 | ❌ **多处严重错误**：5 处主谓一致 + 1 处时态 + 1 处搭配，累计 7 处影响理解 |
| 衔接与连贯 | ❌ **几乎无衔接**：仅 `So / also` 两个简单连接词；段间无过渡 |
| 格式与语域 | ❌ **结构几乎崩塌**：¶3 仅一句（14 词），段落权重严重失衡；口号式语域 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | lexical | ¶1 各句 | Wages is 45% / Investments is 25% / Pensions is 10% / Others is 20% | Wages account for 55%; investments make up 20%; pensions contribute 15%; other sources constitute 10% | **数据错位 × 4**：全部与图表不符，且动词 `is` 用错 |
| iss-2 | critical | grammar | ¶1/¶2 | wages is / investments is | wages **are** / investments **are** | 主谓一致 × 3（复数主语）|
| iss-3 | critical | grammar | ¶1 首句 | The chart show | The chart **shows** | 主谓一致（单数 chart + s）|
| iss-4 | warning | discourse | ¶2 | 仅"人要工作"1 个原因 | 需要 ≥ 2 个结构性原因（如工资主导型经济 + 投资门槛较高）| 任务完成度不足 |
| iss-5 | warning | discourse | ¶3 整段 | We should work hard and save money | 应回扣图表数据，如"多元化收入结构有利于家庭抗风险" | 结论与图表脱钩 |
| iss-6 | critical | format | 字数 | 72 词 | 约 150 词（±15） | 偏短 52%，shortfall_ratio=0.52，触发 critical 级降档 |

## 为什么是第一档（1–4），给 3 分（再扣字数后 → final 2）

### 档内定档路径

| 步骤 | 计算 | 说明 |
|------|-----|------|
| 1. 5 维画像（无数据错位假设）| 第二档下限 5 分 | 任务薄 + 语法错密集 + 无衔接 |
| 2. 数据错位扣分 | 5 − 2 = 3 | 4 个关键数全错，触发"数据精准度 critical"——英二 B 独有扣分 |
| 3. raw_score 锚定 | **3** | 已跌入第一档（1–4）|
| 4. 字数不足降档 | 3 − 1 = 2 | shortfall_ratio 0.52 > 0.50 触发 critical 级再降 1 分 |
| **final_score** | **2** | 第一档低位 |

### 为何仍在第一档（1–4）而非 0 分

- 话题（收入构成）与图表主题**大致一致**，未完全偏离；
- 仍有三段结构雏形；
- 字数 72 词 > 0，未构成"未完成"。

## 为什么不是第二档（5–8）

| 边界判定要素 | 本文表现 | 第二档标准 |
|-------------|---------|------------|
| 任务完成度 | 数据全错位 | 需要 **基本按要求完成**，数据大致正确 |
| 语法错误密度 | 5 处主谓一致 | 需要 **错误较多但不完全影响理解** |
| 字数 | 72 词（52% 不足）| 需要至少达"约 150 词"的 70% 即 105 词 |

## 升档路径（→ 第二档 5–8 下限）

1. **修正所有数据**：¶1 改为 `Wages account for 55% of household income, constituting the
   largest share. Investments follow at 20%, while pensions contribute 15% and other sources
   make up the remaining 10%.`
2. **修复主谓一致**：`wages are / investments are / pensions are / the chart shows`
3. **补字数到 150**：扩展原因段（`First, wage income remains the pillar of urban households
   because... Second, investment returns have been rising but require capital and financial
   literacy.`）
4. **结论回扣**：`The chart reveals a relatively diversified but still wage-dependent income
   structure, suggesting that young families should gradually build passive income streams.`

## 金标样例说明

本样例用于回归测试两个**关键扣分机制**：

1. **数据精准度（英二 B 独有）**——4 个关键数全部错位，直接从第二档下限 5 降到 3（扣 2 分）
2. **字数不足级联降档**——shortfall_ratio=0.52 > 0.50 触发 critical 级降档（再扣 1 分）

两者叠加使 final_score 从 5 一路掉到 2（跨两档），展示"多重扣分机制叠加"的评分路径。

## 跨试卷对比（vs postgrad1b-01-band-cartoon-01）

| 维度 | 本文（英二 B 图表）| postgrad1b-01（英一 B 图画）|
|------|------------------|--------------------------|
| 触发扣分机制 | 数据错位 + 字数不足 | 字数不足（78/160，shortfall 0.51）|
| 满分 | 15 | 20 |
| raw → final 路径 | 5 → 3 → 2 | 4 → 2 |
| 跨跌档数 | 跨 2 档（二档 → 一档）| 跨 2 档（二档 → 一档）|
| **结论** | 两个试卷 **低档扣分叠加规则同构**——均能从中档跌至低档 | 同左 |

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2B",
  "task_subtype": "chart",
  "band": 1,
  "raw_score": 3,
  "final_score": 2,
  "deductions_total": 3.0,
  "data_accuracy_score": "critical",
  "expected_key_rationale": [
    "4 个关键数全部错位（45/25/10/20 vs 55/20/15/10）——数据精准度 critical 扣 2 分",
    "字数 72 词不足 150，shortfall_ratio=0.52 > 0.50 触发 critical 级降档扣 1 分",
    "主谓一致错误密集（5 处）",
    "结论段仅 14 词与图表脱钩"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2B", "effective": 72, "requirement_min": 120,
 "requirement_max": null, "within_range": false, "penalty_triggered": true,
 "shortfall_ratio": 0.52, "penalty_level": "critical"}
```
