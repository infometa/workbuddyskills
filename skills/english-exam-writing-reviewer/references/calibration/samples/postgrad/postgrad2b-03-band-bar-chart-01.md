---
exam_level: Postgrad2B
band: 3
raw_score: 8
task_subtype: bar_chart
chart_subtype: bar_chart
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, bar_chart]
reference_source: "基于考研英语二 2015 柱状图真题（大学生消费构成）风格自构"
prompt: |
  Write an essay of about 150 words based on the bar chart below, in which you should:
  1) describe the chart, and
  2) give your comments.
  The chart presents the spending distribution of university students in China across
  five categories in 2024: food (40%), study materials (22%), clothing (14%),
  entertainment (16%), and others (8%).
---

# 样例作文原文

```
The bar chart illustrates how university students in China spent their
money across five categories in 2024. Clearly, food took the largest
share of 40%, followed by study materials (22%), entertainment (16%),
and clothing (14%). The "others" category ranked last, at only 8%.

Several reasons can explain this distribution. First, as most students
live on campus and eat in canteens three times a day, daily meals
naturally consume most of their budget. Second, the rising price of
textbooks and online courses has pushed study materials to the second
position. Third, entertainment such as movies and games has gradually
become a regular part of student life, which is why it overtook
clothing.

In my opinion, this structure is basically reasonable, though students
should probably allocate more to reading materials if they want to
invest in their future development.
```

（正文约 148 词）

---

# 人工阅卷批注（Postgrad2B · bar_chart · 第三档）

## bar_chart 专属检查项（v1.6 `chart-verbs.md` §2.1）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 排序描述 | 用 `followed by / ranked last / the largest share` | `took the largest share / followed by / ranked last` | ✅ |
| 全部 5 项数据出现 | 5/5 | 食 40 / 学 22 / 娱 16 / 衣 14 / 他 8 | ✅ 5/5 |
| 对比表达 | 至少 1 处 `whereas / compared to / in contrast` | 0 处（仅顺序列举）| ❌ warning |
| 归因段 | 解释为什么这样分布 | First/Second/Third 三条理由 | ✅ |
| 结论 | 给出评论 | `basically reasonable + 建议多投 reading materials` | ✅ |

→ **4/5 项达标**，缺 1 项对比表达（扣一档次）。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| food 40% | 40% ✅ |
| study materials 22% | 22% ✅ |
| clothing 14% | 14% ✅ |
| entertainment 16% | 16% ✅ |
| others 8% | 8% ✅ |

→ 5/5 数据全精确，无错位。

## 5 维诊断

1. **任务完成度**：描述 + 归因 + 评论齐全
2. **语法结构与词汇**：中等
   - 定语从句：`which is why it overtook clothing`
   - mid-tier：`allocate / distribution / consume / overtake`
   - **缺对比/转折结构**
3. **语言准确性**：基本准确
4. **衔接与连贯**：`First / Second / Third` 机械
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶1 全段 | 纯顺序列举，无对比 | 加 `whereas entertainment at 16% marginally outstripped clothing at 14%` | warning | discourse（bar_chart 缺对比表达）|
| ¶3 中 | `this structure is basically reasonable` | `this pattern is largely in line with the realities of campus life` | tip | lexical |
| ¶3 末 | `if they want to invest in their future development` | `if they aspire to invest more substantively in long-term self-development` | tip | lexical |

合计 0 critical + 1 warning + 2 tip — 符合第三档"基本完成；语言错误若干不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| bar_chart 五要素 | 4/5（缺对比）| **3** |
| 数据精准度 | 5/5 | 4 |
| 归因段 | 3 条理由 | 4 |
| 复杂结构 | 定语从句 ×1，无非限定 / 倒装 / 对比 | 3 |
| high-tier 词汇 | 0 处 | 3 |
| 机械衔接 | First/Second/Third | 3 |

→ **数据精准但缺对比 + 语言机械 = 第三档（8 分）**。

## 升档路径（Postgrad2B bar_chart · 3 → 4）

1. **补对比**（bar_chart 硬门槛）：`food took the largest share of 40%, **twice as much as the combined share of clothing and others**`
2. 加非限定：`Clearly, food took the largest share of 40%, **commanding nearly half of the monthly budget**`
3. high-tier：`allocate` → `earmark`；`consume most of their budget` → `absorb the lion's share`
4. 替换机械衔接：`First / Second / Third` → `To begin with / Moreover / More tellingly`

---

# 该样例用途

- **v1.7 chart_subtype = bar_chart 中档位锚点**：首篇 bar_chart 校准
- **"缺对比"扣档金标**：数据 5/5 全精确但无 1 处 `whereas / compared to` → 降至 3 档的典型示范
- **Step 2 chart_subtype 识别**：单一柱状图 → `chart_subtype = "bar_chart"`
