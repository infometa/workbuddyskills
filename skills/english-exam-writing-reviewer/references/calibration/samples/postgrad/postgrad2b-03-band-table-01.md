---
exam_level: Postgrad2B
band: 3
raw_score: 8
task_subtype: table
chart_subtype: table
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, table]
reference_source: "基于考研英语二 2024 表格真题（大学生阅读习惯）首考风格自构"
prompt: |
  Write an essay of about 150 words based on the table below, in which you should:
  1) describe the table, and
  2) give your comments.
  The table lists the average weekly reading time of Chinese university students by
  category in 2020 and 2024 (hours): textbooks 2020→2024 (8 → 6); e-books (2 → 5);
  social media (5 → 9); paper novels (3 → 2).
---

# 样例作文原文

```
The table records the average weekly reading time that Chinese
university students devoted to four reading categories in 2020 and
2024. During this five-year interval, significant changes took place.

Specifically, the time spent on textbooks dropped from 8 hours to 6
hours, and paper novels also declined slightly, from 3 to 2 hours.
Meanwhile, e-books enjoyed a steady rise, from 2 to 5 hours, and
social media saw the most dramatic growth, jumping from 5 to 9 hours a
week.

Two factors may account for this shift. First, the convenience of
digital reading devices has enabled students to consume content
anywhere. Second, the rich entertainment value of short-form content
on social media appeals to young readers, at the expense of longer
traditional formats.

Overall, the table shows a clear migration from printed materials to
digital, which is likely to continue in the coming years.
```

（正文约 145 词）

---

# 人工阅卷批注（Postgrad2B · table · 第三档）

## table 专属检查项（v1.6 `chart-verbs.md` §2.3）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 时间跨度点明 | `between X and Y / during this N-year interval` | `during this five-year interval` | ✅ |
| 变化方向+幅度 | `rose / dropped / by X%` 齐全 | `dropped from 8 to 6 / declined slightly / enjoyed a steady rise / jumping from 5 to 9` | ✅ 4 类动词变体 |
| 全部行/列覆盖 | 4 行全出现 | 4/4 | ✅ |
| 对比 / 反向趋势 | `meanwhile / in contrast / whereas` | `Meanwhile` ×1，对比单一 | ⚠️ |
| 归因段 | 解释原因 | 数字化设备便利 / 短视频娱乐 两条 | ✅ |

→ **4/5 完整 + 1 项单薄**。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| textbooks 8→6 | ✅ |
| e-books 2→5 | ✅ |
| social media 5→9 | ✅ |
| paper novels 3→2 | ✅ |

→ 4/4 全精确。

## 5 维诊断

1. **任务完成度**：时间 + 四项数据 + 归因 + 展望齐全
2. **语法结构与词汇**：中等
   - 动词变体：`dropped / declined slightly / enjoyed a steady rise / jumping`
   - 无非限定、无倒装
   - mid-tier：`interval / dramatic / migration / appeal to / consume`
3. **语言准确性**：基本准确
4. **衔接与连贯**：`Specifically / Meanwhile / First / Second / Overall` 层次清晰
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 中 | `jumping from 5 to 9 hours a week` | `surging from 5 to 9 hours per week` | tip | lexical（jumping 偏口语）|
| ¶3 末 | `at the expense of longer traditional formats` | 可保留，已高阶 | — | — |
| ¶4 末 | `which is likely to continue in the coming years` | `a trajectory likely to persist in the foreseeable future` | tip | stylistic |

合计 0 critical + 0 warning + 2 tip — 符合第三档"基本完成；语言错误若干不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| table 五要素 | 4/5（对比单一）| 3-4 边界 |
| 数据精准度 | 4/4 | 4 |
| 动词变体多样性 | 4 种（dropped/declined/enjoyed a rise/jumping）| 4 加分 |
| 复杂结构 | 0 处非限定 / 倒装 / 定语从句 | **3** |
| high-tier 词汇 | `interval / dramatic / migration` 均属 mid，0 high | 3 |
| 反向对比 | `Meanwhile` ×1，对比表达较弱 | 3-4 |

→ **数据全 + 动词变体丰富 + 结构单薄 = 第三档上界（8 分）**。

## 升档路径（Postgrad2B table · 3 → 4）

1. 加非限定：`social media saw the most dramatic growth, jumping from 5 to 9 hours a week, **now consuming nearly half of weekly reading time**`
2. 加对比：`e-books enjoyed a steady rise, from 2 to 5 hours, **whereas their printed counterparts continued to lose ground**`
3. 加 high-tier：`migration` → `paradigm shift`；`consume content` → `assimilate content`
4. 加倒装（可选 5 档冲击）：`Nowhere is this shift more evident than in the near-doubling of social-media reading time.`

---

# 该样例用途

- **v1.7 chart_subtype = table 中档位锚点**：首篇 table 校准（**表格为 2024 年首考题型**）
- **四动词变体金标**：`dropped / declined / enjoyed a rise / jumping` 覆盖了涨跌两方向的 4 种 tier
- **"对比单薄扣档"**：表格本应比柱状图有更多对比机会，本文仅 1 处 `Meanwhile` → 卡 3 档上界
- **Step 2 chart_subtype 识别**：Directions 含 "the table lists / records" → `chart_subtype = "table"`
