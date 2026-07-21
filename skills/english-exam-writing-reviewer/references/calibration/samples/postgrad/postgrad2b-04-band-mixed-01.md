---
exam_level: Postgrad2B
band: 4
raw_score: 11
task_subtype: mixed
chart_subtype: mixed
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, mixed]
reference_source: "基于考研英语二 2023 年混合图风格自构（饼图+柱状图组合，新能源车）"
prompt: |
  Write an essay of about 150 words based on the two charts below, in which you should:
  1) describe the charts, and
  2) give your comments.
  Chart 1 (pie): China's 2024 new-energy-vehicle market share by powertrain — BEV 62% /
  PHEV 28% / HEV 8% / FCV 2%.
  Chart 2 (bar): Annual NEV sales volume in China, 2020-2024 (million units):
  1.4 → 2.9 → 5.7 → 9.5 → 13.2.
---

# 样例作文原文

```
The two charts together present a panoramic view of China's new-energy-
vehicle market. Chart 1 breaks down the 2024 market by powertrain
technology, while Chart 2 traces sales volume over the past five years.

From the pie chart, battery electric vehicles overwhelmingly dominate
the mix, commanding 62% of the share, followed by plug-in hybrids at
28%, hybrids at 8%, and fuel-cell vehicles trailing at only 2%. Chart 2
reveals an even more striking story: annual sales have surged from 1.4
million units in 2020 to 13.2 million in 2024, representing a nearly
ten-fold increase over the five-year window.

Two complementary trends stand out. First, the technological
concentration on pure battery systems signals manufacturers' bet on
charging infrastructure. Second, the parabolic growth in volume
reflects both policy incentives and maturing consumer acceptance.

Looking ahead, provided that battery costs continue to fall, the
current trajectory appears set to persist well into the latter half of
this decade.
```

（正文约 165 词）

---

# 人工阅卷批注（Postgrad2B · mixed · 第四档）

## mixed 专属检查项（v1.6 `chart-verbs.md` §2.7）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 两图关系点明 | 开头说明两图互补 | `panoramic view / Chart 1 breaks down... while Chart 2 traces...` | ✅ 明确互补关系 |
| 分别描述两图 | 各一段 | ¶2 饼图 + ¶2 后半柱状图 | ✅ |
| 专属动词按图类型区分 | 饼图用 `claim/slice`；柱状用 `surge/rise` | 饼：`dominate / commanding / trailing`；柱：`surged / ten-fold increase` | ✅ 正确区分 |
| 串联两图的宏观趋势 | 点出共同含义 | `Two complementary trends stand out` + 技术集中 + 体量爆发 | ✅ |
| 归因 + 展望 | 双维度 | 充电基础设施 + 政策 + 消费者接受 + 预测 | ✅ |

→ **5/5 项达标** + 明确图类型区分（mixed 核心能力）。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| BEV 62 / PHEV 28 / HEV 8 / FCV 2 | ✅ 4/4 |
| 2020: 1.4M | ✅ |
| 2024: 13.2M | ✅ |
| "nearly ten-fold" | 13.2/1.4 ≈ 9.4 ≈ 10 | ✅ 正确推算 |

→ 6/6 全精确 + 正确推算比率（加分）。

## 5 维诊断

1. **任务完成度**：两图描述 + 专属动词 + 串联趋势 + 归因 + 展望齐全
2. **语法结构与词汇**：较丰富
   - 非限定：`followed by plug-in hybrids at 28% / trailing at only 2% / representing a nearly ten-fold increase`
   - 条件状语：`provided that battery costs continue to fall`
   - high-tier：`panoramic / powertrain / overwhelmingly / parabolic / trajectory / complementary / maturing`
3. **语言准确性**：准确
4. **衔接与连贯**：`From the pie chart / Chart 2 reveals / Two complementary trends / Looking ahead` 图内→图外→总结
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶3 中 | `manufacturers' bet on` | `manufacturers' strategic commitment to` | tip | register（`bet` 偏口语）|
| 其余 | 无 | — | — | — |

合计 0 critical + 0 warning + 1 tip — 符合第四档上界。

## 为什么第四档不是第五档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| mixed 五要素齐全 + 图类区分 | 5/5+ | 5 |
| 数据精准 + 自推算比率 | 6/6+ | 5 |
| 复杂结构 | 非限定 ×3 + 条件状语 ×1 | 5 |
| high-tier 词汇 | 7 处 | 5 |
| academic tier | 0 处（如 `electrification paradigm / market coalescence`）| **4** |
| 倒装 | 0 处 | 4 |

→ **结构完整 + 高密度 high-tier = 第四档上界（11 分）**，缺 academic tier + 倒装未跨入第五档。

## 升档路径（Postgrad2B mixed · 4 → 5）

1. 加 academic tier：`technological concentration on pure battery systems` → `the crystallization of an electrification paradigm around pure battery architectures`
2. 加倒装：`Parabolic growth in volume reflects...` → `Not only has volume expanded parabolically, but the composition of demand has simultaneously coalesced around battery-only vehicles.`
3. 展望加政策维度：`provided that battery costs continue to fall` → `provided that battery costs continue their downward trajectory and charging infrastructure scales apace`

---

# 该样例用途

- **v1.7 chart_subtype = mixed 中档位锚点**：首篇 mixed 校准（**混合图是真题低频但大纲覆盖的难点**）
- **图类型动词区分金标**：饼图用 `dominate / commanding / trailing`；柱状用 `surged / ten-fold increase`——mixed 的核心能力
- **自推算比率示范**：13.2/1.4 ≈ 10 → `nearly ten-fold increase` 展现数据理解深度
- **Step 2 chart_subtype 识别**：Directions 含"两图"且图种不同 → `chart_subtype = "mixed"`
