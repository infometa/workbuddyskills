---
exam_level: Postgrad1A
band: 4
raw_score: 7
task_subtype: letter
letter_category: recommendation
task_type: letter
anchor_tags: [v1.7, new-letter-category-anchor, mid-band, recommendation]
reference_source: "基于考研英语一 2013 真题推荐信题型风格自构"
prompt: |
  Directions:
  Write a letter of about 100 words to a friend, recommending a TV program or film you
  have recently enjoyed. You should include reasons for your recommendation.
  Use "Li Ming" instead of your real name. (10 points)
---

# 样例作文原文

```
Dear Chris,

I am writing to recommend a documentary series that I have recently
watched and immensely enjoyed—"Planet Earth III", produced by the BBC.
Knowing your passion for nature and photography, I am confident that this
programme will resonate with you as well.

There are three principal reasons why I recommend it so warmly. First,
the cinematography is nothing short of breathtaking, capturing rarely
seen animal behaviour with remarkable clarity. Second, each episode is
narrated by Sir David Attenborough, whose measured voice lends the series
a rare sense of gravitas. Last but not least, the programme touches on
climate change in an accessible yet deeply thought-provoking manner.

Do take the time to watch it when your schedule permits. I would love
to hear your thoughts afterwards.

Yours,
Li Ming
```

（正文约 135 词）

---

# 人工阅卷批注（Postgrad1A · letter · recommendation · 第四档）

## letter_category = recommendation 专属检查项

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头套语 | `writing to recommend` / `highly recommend` | `I am writing to recommend a documentary series...` | ✅ |
| 推荐对象精确命名 | 具体名称 + 作者/出品方 | `"Planet Earth III", produced by the BBC` | ✅ 含作品名 + 出品方 |
| 推荐理由 ≥ 2 条 | 并列理由 | First/Second/Last but not least 三条 | ✅ |
| 针对收件人兴趣 | 呼应对方偏好 | `Knowing your passion for nature and photography` | ✅ 个性化 |
| 期待回应 | `hear your thoughts` / `let me know` | `I would love to hear your thoughts afterwards` | ✅ |

→ **5/5 项达标** + 呼应收件人兴趣（第四档加分）。

## Directions 照搬检测

- 连续 8 词以上重合：无
- `overall_risk = "none"`

## 5 维诊断

1. **任务完成度**：推荐对象 + 三条理由 + 呼应收件人 + 期待回应，齐全
2. **语法结构与词汇**：较丰富
   - 非限定：`capturing rarely seen animal behaviour` / `produced by the BBC`
   - 定语从句：`whose measured voice lends the series...`
   - high-tier 词：`resonate / gravitas / thought-provoking / cinematography / breathtaking`
3. **语言准确性**：准确
4. **衔接与连贯**：`First / Second / Last but not least` + 收尾礼貌邀请
5. **格式与语域**：`Dear Chris` 私人信件语域（而非 formal）；`Yours` 简短签名与私信风格一致

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 中 | `so warmly` | 保留，已高阶 | — | — |
| 全文 | 无明显错误 | — | — | — |

合计 0 critical + 0 warning + 0 tip — 符合第四档"较好完成；仅在试图复杂/高阶时才有个别错误"。

## 为什么第四档不是第五档（recommendation 视角）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| recommendation 五要素齐全 | 5/5 | 5 |
| 理由具体度 | 三条理由均带形容+例证 | 4-5 边界 |
| 复杂结构 | 非限定 ×2 + 定语从句 ×1 = 3 处 | 5（已达门槛）|
| high-tier 词汇 | `resonate / gravitas / thought-provoking / cinematography` 4 处 | 4-5 边界 |
| academic tier | 0 处（如 `epitomize / paradigm` 等）| **4**（第五档期望 ≥ 1 处 academic）|
| 倒装强调 | 0 处 | 4 |

→ **结构完整 + 语言丰富 = 第四档（7 分）**，未达第五档缺 academic tier + 倒装。

## 升档路径（Postgrad1A recommendation · 4 → 5）

1. 加 academic tier：`the programme touches on climate change in an accessible yet deeply thought-provoking manner` → `the programme epitomizes how ecological discourse can be rendered both accessible and intellectually profound`
2. 加倒装强调：`Last but not least, the programme...` → `Rarely have I encountered a nature documentary that engages with climate change so deftly.`
3. 收尾加强：`I would love to hear your thoughts` → `I should be delighted to compare impressions once you have watched it`

---

# 该样例用途

- **v1.7 letter_category = recommendation 中档位锚点**：首篇 recommendation 校准
- **私人信件语域示范**：`Dear Chris` + `Yours` 与正式 `Dear Sir or Madam` + `Yours sincerely` 的区别
- **Step 6 letter_category 识别**：Directions 含 "recommending" → `letter_category = "recommendation"`
