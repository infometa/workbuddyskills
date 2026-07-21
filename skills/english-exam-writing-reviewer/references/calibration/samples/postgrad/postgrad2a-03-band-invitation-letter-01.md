---
exam_level: Postgrad2A
band: 3
raw_score: 5
task_subtype: letter
letter_category: invitation
task_type: letter
anchor_tags: [v1.7, new-letter-category-anchor, mid-band, invitation]
reference_source: "基于考研英语二 2016 / 2021 真题邀请信题型风格自构"
prompt: |
  Directions:
  Suppose your university is going to host a lecture by a famous scholar next Friday.
  Write a letter of about 100 words to invite a friend to attend with you. You should
  include the time, place and topic of the lecture. Use "Li Ming" instead of your real
  name. (10 points)
---

# 样例作文原文

```
Dear Zhang Wei,

I am writing to invite you to a lecture which will be held in our
university next Friday. I think you will be interested in it.

The lecture is about artificial intelligence and its future, and it will
be given by Professor John Smith from MIT. The time is 7:00 pm on
December 15, and the place is the main lecture hall in the library
building. I know you are studying computer science, so this topic is
very suitable for you. After the lecture, we can have dinner together
and talk about it.

If you are free on that day, please reply me as soon as possible. I am
looking forward to your reply.

Yours,
Li Ming
```

（正文约 120 词）

---

# 人工阅卷批注（Postgrad2A · letter · invitation · 第三档）

## letter_category = invitation 专属检查项

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头套语 | `writing to invite you to` / `would be delighted if you could join` | `I am writing to invite you to a lecture...` | ✅ |
| 活动三要素（时间/地点/主题）| 全部出现 | time: 7 pm Dec 15 / place: main lecture hall / topic: AI | ✅ |
| 说明为何邀请对方 | 呼应兴趣 | `I know you are studying computer science, so this topic is very suitable for you` | ✅ |
| 后续安排 | 如晚餐/交通 | `After the lecture, we can have dinner together` | ✅ |
| 期待回复 | `look forward to your reply` | `I am looking forward to your reply` | ✅ |

→ **5/5 项达标**，结构完整。

## Directions 照搬检测

- 连续 8 词以上重合：无
- `overall_risk = "none"`

## 5 维诊断

1. **任务完成度**：活动三要素 + 针对性 + 后续安排 + 客套齐全
2. **语法结构与词汇**：较低
   - low-mid tier：`very suitable / very interested / as soon as possible`
   - 无非限定、无定语从句
3. **语言准确性**：有 1 处 grammar 错误（reply me → reply to me）
4. **衔接与连贯**：基本连贯，句间过渡较弱
5. **格式与语域**：称呼/正文/署名齐全；`Dear Zhang Wei` + `Yours` 私信语域

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶3 中 | `please reply me as soon as possible` | `please reply to me at your earliest convenience` | warning | grammar（`reply` 不及物，必须加 `to`）|
| ¶1 末 | `I think you will be interested in it` | `I am certain this would be of great interest to you` | tip | register（`I think` 偏口语）|
| ¶2 中 | `this topic is very suitable for you` | `this topic aligns well with your field of study` | tip | lexical（`very suitable` 中式搭配）|

合计 0 critical + 1 warning + 2 tip — 符合第三档"基本完成；语言错误若干但不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| invitation 五要素齐全 | 5/5 | 3-4 边界 |
| 细节具体度 | 时间/地点/讲座人均具体 | 3-4 |
| 语言层级 | 全文 low-mid tier，无 high-tier | **3**（4 档要求 ≥ 1 处 high-tier）|
| 语法错误 | 1 处 warning（reply me）| 3 |
| 复杂结构 | 0 处（无非限定 / 从句）| 3 |

→ **结构全 + 语言基础 = 第三档（5 分）**。

## 升档路径（Postgrad2A invitation · 3 → 4）

1. 修正 grammar：`reply me` → `get back to me` 或 `let me know`
2. 开头升级：`I am writing to invite you to` → `I am writing to extend a warm invitation to`
3. 加非限定：`The lecture is about artificial intelligence and its future, **delivered by Professor John Smith of MIT**`
4. 替换口语化：`very suitable for you` → `highly relevant to your field`
5. 收尾升级：`I am looking forward to your reply` → `Your earliest confirmation would be most appreciated`

---

# 该样例用途

- **v1.7 letter_category = invitation 中档位锚点**：首篇 invitation 校准
- **典型中式英语示范**：`reply me` / `very suitable for you` 是中国学生邀请信高频错误
- **Step 6 letter_category 识别**：Directions 含 "invite... to attend" → `letter_category = "invitation"`
