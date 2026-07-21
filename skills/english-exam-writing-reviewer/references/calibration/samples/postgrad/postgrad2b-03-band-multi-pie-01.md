---
exam_level: Postgrad2B
band: 3
raw_score: 9
task_subtype: multi_pie
chart_subtype: multi_pie
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, multi_pie]
reference_source: "基于考研英语二 2022 双饼图真题风格自构（城乡购物渠道对比）"
prompt: |
  Write an essay of about 150 words based on the two pie charts below, in which you should:
  1) describe the charts, and
  2) give your comments.
  The charts compare the shopping channel preferences of urban and rural residents in
  China in 2024. Urban: online 55% / supermarket 30% / convenience store 10% / others
  5%. Rural: online 30% / supermarket 25% / convenience store 35% / others 10%.
---

# 样例作文原文

```
The two pie charts present the shopping channel preferences of urban
and rural residents in China in 2024. Clearly, the two groups differ
remarkably in their channel distribution.

Among urban residents, online shopping dominates at 55%, with
supermarkets taking 30% and convenience stores only 10%. The rural
picture is very different: convenience stores lead at 35%, while online
shopping ranks second at 30% and supermarkets at 25%. The "others"
category is 5% for urban and 10% for rural.

Two reasons can be given for the difference. First, urban residents
have faster internet and more logistics options, which makes online
shopping convenient. Second, rural areas have fewer large supermarkets,
so convenience stores become the main offline choice.

In my view, as rural logistics infrastructure improves, online shopping
in rural areas will keep rising and may eventually approach the urban
level in the coming decade.
```

（正文约 155 词）

---

# 人工阅卷批注（Postgrad2B · multi_pie · 第三档）

## multi_pie 专属检查项（v1.6 `chart-verbs.md` §2.6）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 两组并列开头 | 明确点明两组 | `shopping channel preferences of urban and rural residents` + `differ remarkably` | ✅ |
| 差异点 ≥ 2 处带定量 | 数据对比 | 在线 55 vs 30 / 便利店 10 vs 35 / 超市 30 vs 25 | ✅ 3 处 |
| 相似点 ≥ 1 处 | 两组共性 | 未点出（如 "online 与 supermarket 都是高频"）| ❌ warning |
| 不可只描述一组 | 两组均覆盖 | ✅ 每类都双数据 |
| 归因段 | 差异归因 | 网速+物流 / 超市稀少 两条 | ✅ |

→ **4/5 达标**，缺相似点对比（multi_pie 硬门槛）。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| 城 online 55 | ✅ |
| 城 超市 30 | ✅ |
| 城 便利店 10 | ✅ |
| 城 others 5 | ✅ |
| 乡 online 30 | ✅ |
| 乡 超市 25 | ✅ |
| 乡 便利店 35 | ✅ |
| 乡 others 10 | ✅ |

→ 8/8 全精确。

## 5 维诊断

1. **任务完成度**：差异 + 归因 + 展望齐全；缺相似点
2. **语法结构与词汇**：中等
   - 对比：`while / very different / at 30%`
   - 定语从句：`which makes online shopping convenient`
   - mid-tier：`differ remarkably / infrastructure / dominates / approach`
3. **语言准确性**：基本准确
4. **衔接与连贯**：`Among urban / The rural picture / First / Second / In my view` 层次清晰
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 中 | `The rural picture is very different` | `The rural picture diverges markedly` | tip | lexical（`very different` 偏口语）|
| ¶3 末 | `so convenience stores become the main offline choice` | `rendering convenience stores the predominant offline option` | tip | stylistic |
| ¶4 首 | `In my view` | `Looking ahead` / `From a forward-looking perspective` | tip | register |
| 全文 | 无相似点描述 | 加 `In both settings, online shopping and supermarkets together claim over half of spending, underscoring the broader penetration of mainstream retail channels.` | warning | discourse（multi_pie 应同时指相似和差异）|

合计 0 critical + 1 warning + 3 tip — 符合第三档"基本完成；语言错误若干不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| multi_pie 五要素 | 4/5（缺相似点）| **3** |
| 数据精准度 | 8/8 | 4 |
| 复杂结构 | 定语从句 ×1，无非限定 / 倒装 | 3 |
| high-tier 词汇 | `differ remarkably / infrastructure` 2 处；无 academic | 3 |
| 归因深度 | 双因素，直接 | 3-4 边界 |

→ **数据全 + 缺相似点 + 语言中等 = 第三档（9 分）**。

## 升档路径（Postgrad2B multi_pie · 3 → 4）

1. **补相似点**（multi_pie 硬门槛）：加一句 `Notably, online shopping occupies a substantial share in both settings, suggesting that e-commerce penetration now reaches well beyond urban frontiers.`
2. 加非限定：`convenience stores lead at 35%, **reflecting the limited presence of larger retail formats in rural areas**`
3. 加倒装：`Striking as the differences are, one common thread unites both groups: online commerce has become indispensable.`
4. high-tier：`differ remarkably` → `diverge sharply`；`approach the urban level` → `converge toward urban parity`

---

# 该样例用途

- **v1.7 chart_subtype = multi_pie 中档位锚点**：首篇 multi_pie 校准
- **"缺相似点扣档"金标**：multi_pie 数据 8/8 全精确但仅描述差异，忽略相似 → 降至 3 档
- **Step 2 chart_subtype 识别**：Directions 含 "two pie charts / compare" → `chart_subtype = "multi_pie"`
