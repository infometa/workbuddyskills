---
exam_level: Postgrad1A
band: 3
raw_score: 5
task_subtype: letter
letter_category: apology
task_type: letter
anchor_tags: [v1.7, new-letter-category-anchor, mid-band, apology]
reference_source: "基于考研英语一 2009 真题道歉信题型风格自构"
prompt: |
  Directions:
  You had promised to help a friend move to a new apartment this weekend, but something
  unexpected has come up. Write a letter of about 100 words to apologise and suggest
  another time. Use "Li Ming" instead of your real name. (10 points)
---

# 样例作文原文

```
Dear Andy,

I am writing to say sorry that I cannot help you move to your new
apartment this Saturday as I promised before. I feel really bad about
breaking our arrangement.

The reason is that my grandmother in my hometown suddenly fell ill
yesterday, and my parents asked me to go back immediately to take care
of her. I must take the high-speed train on Friday evening, so I will
not be able to come back in time. I know this is a bad news for you,
because moving alone is very tiring.

To make up for this, I would like to suggest that we move your things
together next Saturday if you have not finished by then. I can also pay
for the truck this time as a small compensation. Sorry again, and
please understand my situation.

Yours,
Li Ming
```

（正文约 155 词）

---

# 人工阅卷批注（Postgrad1A · letter · apology · 第三档）

## letter_category = apology 专属检查项

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头致歉 | `writing to apologise for` / `owe you a sincere apology` | **`I am writing to say sorry that...`** | ⚠️ 偏口语（`say sorry` 为 informal，formal 应为 `apologise for`）|
| 说明原因 | 具体且合理 | `grandmother fell ill / take high-speed train` | ✅ 具体 |
| 提出补救方案 | `would like to make up for it by...` | `we move your things together next Saturday + pay for the truck` | ✅ |
| 再次致歉 | 结尾再表达 | `Sorry again, and please understand my situation` | ⚠️ `Sorry again` 过于口语 |
| 语气诚恳不找借口 | 承担责任 | `I feel really bad about breaking our arrangement` | ✅ |

→ **5/5 项达标**但其中 2 项语气偏口语；apology 在语域上要求略高。

## Directions 照搬检测

- 连续 8 词以上重合：无
- `overall_risk = "none"`

## 5 维诊断

1. **任务完成度**：致歉 + 原因 + 补救 + 再致歉齐全
2. **语法结构与词汇**：较低
   - low-tier 词：`say sorry / feel really bad / bad news / very tiring / a small compensation`
   - 1 处冠词错误（`a bad news`——news 不可数）
3. **语言准确性**：1 处 critical（冠词错误是显性 grammar 错误）
4. **衔接与连贯**：`The reason is that / To make up for this` 清晰
5. **格式与语域**：私信 `Dear Andy / Yours`；但语气过于口语化，接近 casual speech

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 末 | **`this is a bad news for you`** | `this is bad news for you` / `this may come as unwelcome news` | **critical** | grammar（news 不可数，不能加 `a`——考研 A 节显性语法错误）|
| ¶1 首 | `I am writing to say sorry that` | `I am writing to apologise for being unable to` | warning | register（apology 信禁用 `say sorry` 等口语模板）|
| ¶3 末 | `Sorry again, and please understand my situation` | `Once again, I sincerely apologise for the inconvenience` | warning | register |
| ¶1 末 | `I feel really bad` | `I feel genuinely regretful` | tip | register |
| ¶2 中 | `a bad news for you, because moving alone is very tiring` | `(after fixing news) ... given how strenuous moving can be` | tip | lexical |

合计 1 critical + 2 warning + 2 tip — 符合第三档"基本完成；语言错误若干，个别严重"。

## 为什么第三档不是第四档（apology 视角）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| apology 五要素齐全 | 5/5 | 4 |
| 原因具体度 | 家人病情 + 行程，具体 | 4 |
| 补救方案 | 下周 + 付车费，双方案 | 4 |
| 语域一致性 | `say sorry / Sorry again` 口语模板 | **3**（apology 信要求诚恳 formal）|
| 语法错误 | `a bad news` critical | **3** |

→ **结构完整但语域降级 + 1 处 critical = 第三档（5 分）**。

## 升档路径（Postgrad1A apology · 3 → 4）

1. 修正 critical：`a bad news` → `bad news`（news 不可数）
2. 升级致歉套语：
   - 开头：`I am writing to say sorry that` → `I am writing to convey my sincere apologies for being unable to`
   - 结尾：`Sorry again` → `Once again, please accept my heartfelt apology`
3. 升级情感表达：`feel really bad` → `feel genuinely regretful`
4. 补救段加让步：`Admittedly, a postponement is less than ideal; nevertheless, I would very much like to make it up to you by moving your belongings together next Saturday...`
5. 加 high-tier 词：`a small compensation` → `a modest gesture of amends`

---

# 该样例用途

- **v1.7 letter_category = apology 中档位锚点**：首篇 apology 校准
- **语域降级金标**：`say sorry / Sorry again / feel really bad` 是中国学生 apology 信最常见的语域灾区
- **critical grammar 示范**：`a news` / `a news` 类不可数名词冠词错误
- **Step 6 letter_category 识别**：Directions 含 "apologise / make up for" → `letter_category = "apology"`
