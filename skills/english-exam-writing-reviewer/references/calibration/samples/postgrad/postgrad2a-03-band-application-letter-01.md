---
exam_level: Postgrad2A
band: 3
raw_score: 6
task_subtype: letter
letter_category: application
task_type: letter
anchor_tags: [v1.7, new-letter-category-anchor, mid-band, application]
reference_source: "基于考研英语二 2013 / 2020 真题申请信题型风格自构"
prompt: |
  Directions:
  Suppose you are applying for a summer internship program at a multinational company.
  Write a letter of about 100 words to introduce yourself, state your qualifications and
  express your interest. Use "Li Ming" instead of your real name. (10 points)
---

# 样例作文原文

```
Dear Hiring Manager,

I am writing to apply for the summer internship program advertised on your
company's official website last week. As a third-year student majoring in
International Business at Peking University, I believe I am a suitable
candidate for this position.

During my studies, I have acquired solid knowledge of marketing and
finance. Last summer I also worked as a part-time assistant in a trading
company, where I learned how to handle clients and daily office tasks.
Moreover, I have a good command of English and Chinese, and I can use
Excel and PowerPoint skillfully.

I am available from July 1 to August 31 and can start work immediately.
I am looking forward to your positive reply at your convenience. Thank
you for considering my application.

Yours sincerely,
Li Ming
```

（正文约 136 词）

---

# 人工阅卷批注（Postgrad2A · letter · application · 第三档）

## letter_category = application 专属检查项

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头套语 | `writing to apply for` / `to express my interest in` | `I am writing to apply for...` | ✅ |
| 自我定位（身份/学校/年级）| 一句话自述 | `a third-year student majoring in International Business at Peking University` | ✅ |
| 资质匹配 ≥ 2 点 | 学术 + 实践 + 技能 | 学术（marketing/finance）+ 实习（trading company）+ 技能（English/Excel）三点 | ✅ |
| 时间/可用性说明 | 何时可到岗 | `available from July 1 to August 31` | ✅ |
| 致谢结尾 | `Thank you for considering` | `Thank you for considering my application` | ✅ |

→ **5/5 项达标**，结构标准。

## Directions 照搬检测

- 连续 8 词以上重合：无
- `overall_risk = "none"`

## 5 维诊断

1. **任务完成度**：要点齐全（身份 + 资质 + 时间 + 客套）
2. **语法结构与词汇**：中等
   - mid-tier 词：`acquired / solid / command / skillfully`
   - `skillfully` 为副词搭配略生硬
3. **语言准确性**：基本准确
4. **衔接与连贯**：`During / Moreover / I am` 推进清晰
5. **格式与语域**：formal，称呼/署名齐全

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 末 | `I can use Excel and PowerPoint skillfully` | `I am proficient in Excel and PowerPoint` | warning | lexical（`use...skillfully` 中式英语搭配，proficient 为标准表达）|
| ¶2 中 | `handle clients and daily office tasks` | `liaise with clients and manage daily administrative tasks` | tip | lexical（handle 偏口语）|
| ¶3 首 | `I am available from July 1 to August 31` | 保留 | — | — |

合计 0 critical + 1 warning + 1 tip — 符合第三档"基本完成任务；若干语言错误但不影响理解"。

## 为什么第三档不是第四档

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| application 五要素齐全 | 5/5 | 3-4 边界 |
| 资质具体度 | 学校+专业+实习公司均具体 | 3-4 |
| 复杂结构 | 无非限定/倒装；`where I learned how to` 从句 ×1 | 3（4 档要求 ≥ 2 处复杂结构）|
| high-tier 词汇 | 0 处（`proficient / liaise / commit` 均缺失）| 3 |
| 1 处 warning 级搭配错误 | `use...skillfully` | 3 |

→ **结构完整但语言水平卡 3 档**。

## 升档路径（Postgrad2A application · 3 → 4）

1. 开头加同位语：`I am writing to apply for the summer internship program, **a highly competitive role I came across on your website last week**.`
2. 资质段加非限定：`Last summer I worked as a part-time assistant in a trading company, **honing my client-handling and administrative skills**.`
3. 替换搭配：`use Excel and PowerPoint skillfully` → `am proficient in both Excel and PowerPoint`
4. high-tier 词：`handle` → `liaise with`；`good command` → `strong proficiency`
5. 加让步强化：`Although I am still pursuing my undergraduate degree, my academic training and hands-on experience have equipped me with...`

---

# 该样例用途

- **v1.7 letter_category = application 中档位锚点**：首篇 application 校准
- **典型语言错误示范**：`use...skillfully` 为中国学生常见中式英语搭配
- **Step 6 letter_category 识别**：Directions 含 "applying for" → `letter_category = "application"`
