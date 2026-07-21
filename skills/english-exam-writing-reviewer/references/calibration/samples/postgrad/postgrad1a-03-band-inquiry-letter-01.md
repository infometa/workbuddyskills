---
exam_level: Postgrad1A
band: 3
raw_score: 6
task_subtype: letter
letter_category: inquiry
task_type: letter
anchor_tags: [v1.7, new-letter-category-anchor, mid-band, inquiry]
reference_source: "基于考研英语一 2011 / 2015 真题咨询信题型风格自构"
prompt: |
  Directions:
  Write a letter of about 100 words to the admissions office of a foreign university,
  enquiring about the master's program in applied linguistics. You should include specific
  questions about application requirements, deadlines and scholarships.
  Do not sign your own name at the end of the letter. Use "Li Ming" instead. (10 points)
---

# 样例作文原文

```
Dear Sir or Madam,

I am writing to enquire about the Master's program in Applied Linguistics
offered by your university. I obtained some basic information from your
website, but several details remain unclear.

First, I would like to know the specific requirements for international
applicants, especially the minimum IELTS score. Second, could you kindly
inform me of the application deadline for the 2026 autumn intake? Third,
I would be grateful if you could tell me whether any scholarships are
available for non-EU students.

Your prompt reply would be greatly appreciated, since I am preparing my
application materials now. Thank you very much for your help.

Yours sincerely,
Li Ming
```

（正文约 112 词）

---

# 人工阅卷批注（Postgrad1A · letter · inquiry · 第三档）

## letter_category = inquiry 专属检查项

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头套语 | `writing to enquire about` / `request information concerning` | `I am writing to enquire about...` | ✅ 标准 |
| 交代已知信息 | 表明已做过功课，避免让对方重复介绍 | `I obtained some basic information from your website, but...` | ✅ |
| 具体问题 ≥ 2 个 | 并列问题列点清晰 | First/Second/Third 三个问题 | ✅ |
| 期待回复客套 | `look forward to your reply` / `prompt reply appreciated` | `Your prompt reply would be greatly appreciated` | ✅ |
| 致谢结尾 | `Thank you for your help` | `Thank you very much for your help` | ✅ |

→ **5/5 项达标**，符合 inquiry 信件的标准结构。

## Directions 照搬检测

- 连续 8 词以上重合：无
- `overall_risk = "none"`，不触发扣分

## 署名合规性

- ✅ 使用 `Li Ming`（题目指定）

## 5 维诊断

1. **任务完成度**：要点齐全（申请要求/截止日期/奖学金三项全覆盖）
2. **语法结构与词汇**：中等
   - mid-tier 词：`enquire / obtain / intake / applicant / appreciated`
   - 无非限定/倒装/强调
3. **语言准确性**：基本准确，无 critical
4. **衔接与连贯**：`First / Second / Third` 机械衔接；收尾自然
5. **格式与语域**：称呼/正文/客套/署名齐全，formal

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 中 | `I would like to know` | `I would be grateful if you could specify` | tip | register（偏日常，可升 formal）|
| ¶2 末 | `could you kindly inform me of` | 保留，标准模板 | tip | stylistic |
| ¶3 首 | `Your prompt reply would be greatly appreciated` | 已达标 | — | — |

合计 0 critical + 0 warning + 2 tip — 第三档"基本完成任务；若干处语言错误，但不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| inquiry 五要素齐全 | 5/5 | 3-4 边界 |
| 问题精确度 | 三个问题有定量（IELTS/2026/non-EU）| 3 |
| 语言丰富度 | mid-tier 为主，无 high-tier + 无复杂结构 | **3**（4 档要求 ≥ 1 处非限定 + 1 处 high-tier）|
| 机械衔接 | First/Second/Third，未升级 | 3 |

→ **结构完整但语言层级卡 3 档（6 分）**。4 档需要语言更丰富。

## 升档路径（Postgrad1A inquiry · 3 → 4）

1. 开头加同位语升级：`I am writing to enquire about the Master's program in Applied Linguistics, **a program widely recognized for its interdisciplinary rigour**, offered by your university.`
2. 衔接升级：`First / Second / Third` → `To begin with / Furthermore / Finally / I would also be grateful if`
3. 加非限定：`I obtained some basic information from your website, **leaving several key details unclear**`
4. 具体问题加复合句：`whether any scholarships are available for non-EU students, **and, if so, the typical amount awarded per academic year**`

---

# 该样例用途

- **v1.7 letter_category = inquiry 中档位锚点**：首篇 inquiry 校准
- **典型中档位示范**：结构完整但语言机械的标准 3 档表现
- **Step 6 letter_category 识别**：Directions 含 "enquiring about" → `letter_category = "inquiry"`
