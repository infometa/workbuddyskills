---
exam_level: Postgrad2B
band: 3
raw_score: 9
task_subtype: pie_chart
chart_subtype: pie_chart
task_type: chart
anchor_tags: [v1.7, new-chart-subtype-anchor, mid-band, pie_chart]
reference_source: "基于考研英语二 2018 饼图真题（居民体育消费结构）风格自构"
prompt: |
  Write an essay of about 150 words based on the pie chart below, in which you should:
  1) describe the chart, and
  2) give your comments.
  The chart shows the composition of Chinese residents' sports-related spending in 2024:
  fitness equipment (35%), sportswear (28%), gym membership (20%), sports events
  (10%), and others (7%).
---

# 样例作文原文

```
As can be seen from the pie chart, the composition of Chinese residents'
sports-related spending in 2024 is divided into five categories. Fitness
equipment claimed the largest slice, accounting for 35% of total
expenditure, while sportswear took up 28%. Gym membership made up 20%,
with sports events accounting for 10% and "others" for the remaining 7%.

This distribution reflects two recent trends. On the one hand, the
popularity of home-based workouts has boosted demand for fitness
equipment like treadmills and yoga mats. On the other hand, the fashion
attribute of sportswear is being reinforced by leading brands, so
consumers are willing to invest more in it.

Personally, I think this pattern will continue. As more urban residents
become health-conscious, fitness equipment and gym membership will keep
rising, whereas sports events might stay relatively stable.
```

（正文约 143 词）

---

# 人工阅卷批注（Postgrad2B · pie_chart · 第三档）

## pie_chart 专属检查项（v1.6 `chart-verbs.md` §2.2）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 用饼图专属动词 | `slice / share / account for / comprise / make up` | `claimed the largest slice / accounting for 35% / took up 28% / made up 20%` | ✅ 4 种变体 |
| "整体=100%" 暗示 | `of total expenditure` / `out of 100%` | `of total expenditure` | ✅ |
| 数据覆盖全部类别 | 5/5 | 健器 35 / 运动服 28 / 健身房 20 / 赛事 10 / 其他 7 | ✅ |
| 归因段 | 解释原因 | 家庭健身热 / 运动服时尚属性 两条 | ✅ |
| 结论 | 给评论 + 展望 | `this pattern will continue` | ✅ |

→ **5/5 项达标**。

## 数据精准度检查

| 数据点 | 图中 | 作文 | 判定 |
|-------|-----|-----|------|
| fitness equipment 35% | ✅ |
| sportswear 28% | ✅ |
| gym membership 20% | ✅ |
| sports events 10% | ✅ |
| others 7% | ✅ |

→ 5/5 全精确。

## 5 维诊断

1. **任务完成度**：描述 + 归因 + 展望齐全
2. **语法结构与词汇**：中等
   - 对比：`On the one hand / On the other hand / whereas`
   - mid-tier：`composition / expenditure / boost / attribute / health-conscious`
   - 无非限定、无倒装
3. **语言准确性**：基本准确
4. **衔接与连贯**：`On the one hand / On the other hand` 对比清晰
5. **格式与语域**：学术 formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶3 首 | `Personally, I think` | `It is my belief that` / `In all likelihood` | tip | register（`Personally, I think` 偏口语，pie_chart 评论段应更客观）|
| ¶2 中 | `the fashion attribute of sportswear is being reinforced by leading brands, so consumers are willing to invest` | `the marketing of sportswear as a fashion statement... has driven consumer willingness to invest` | tip | stylistic（`so consumers are willing` 因果链条机械）|

合计 0 critical + 0 warning + 2 tip — 符合第三档上界（9 分，接近 4 档）。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| pie_chart 五要素齐全 | 5/5 | 4 |
| 数据精准度 | 5/5 | 4 |
| 饼图专属动词多样性 | 4 种变体 | 4 加分 |
| 复杂结构 | 对比 ×2 + 介词短语，**无非限定 / 倒装 / 虚拟语气** | 3 |
| high-tier 词汇 | 0 处（`boost / health-conscious` 均 mid）| 3 |
| 评论客观度 | `Personally, I think` 偏主观 | 3 |

→ **数据全 + 描述丰富 + 语言中等 = 第三档上界（9 分）**。

## 升档路径（Postgrad2B pie_chart · 3 → 4）

1. 加非限定：`Fitness equipment claimed the largest slice, accounting for 35% of total expenditure, **underscoring the rising prominence of home fitness culture**`
2. 加倒装：`No less striking is the 28% allocated to sportswear, which signals a clear shift toward athleisure lifestyles.`
3. 替换 `Personally, I think` → `Looking ahead, it seems reasonable to anticipate that`
4. high-tier：`boost` → `fuel / galvanize`；`health-conscious` → `wellness-oriented`

---

# 该样例用途

- **v1.7 chart_subtype = pie_chart 中档位锚点**：首篇 pie_chart 校准
- **饼图专属动词 4 种变体示范**：`claimed the largest slice / accounting for / took up / made up`
- **"主观评论扣档"**：`Personally, I think` 在正式图表评论中被评卷老师视为口语化
- **Step 2 chart_subtype 识别**：单饼图 → `chart_subtype = "pie_chart"`
