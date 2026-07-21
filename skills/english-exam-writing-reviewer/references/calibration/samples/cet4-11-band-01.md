---
exam_level: CET4
band: 11
raw_score: 11
reference_source: "DURUII/english-learning-skills @ references/writing.md"
prompt: |
  Commenting on the saying "If you cannot do great things, do small things in a great way."
---

# 样例作文原文

"If you cannot do great things, do small things in a great way" is the greatest saying I've ever heard. I admire many people. Some of them are heroes who do great things, but some of them are ordinary people. They do small things which seems simple and boring.

To illustrate it, I show an example first. My Chinese teacher, Miss Chen, is an ordinary senior high school teacher. She teaches everyday. However, in my eyes, she's a great teacher. She really loves her students and her courses are wonderful. She will spend her spare time to prepare a good class. She's always willing to help students. As a result, she's a very popular teacher in our school.

Miss Chen doesn't do great things, but she tries to make her job great. When you do things wholeheartedly, you are great person. Obviously, not everyone has the chance to be a hero, but when we do our small things in great way, we succeed.

This is an amazing quality. So we shouldn't complain that we can't do great things. Let's do small things in a great way to be our own hero.

---

# 人工阅卷批注

## 隐含维度诊断

- **切题度**：切题。主题清晰、立场一致
- **表达清晰度**：思想清楚。有主题句 + 例证（Miss Chen）+ 收束
- **连贯性**：文字连贯，但衔接略机械（`obviously` / `as a result` / `so` 等显性连词堆砌）
- **语言准确度**：有少量错误（3-4 处），均不影响理解

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶1 末 | `small things which seems simple and boring` | `small things that seem simple and boring` | warning | grammar（主谓一致）|
| ¶2 第 6 句 | `She will spend her spare time to prepare a good class` | `She spends her spare time preparing a good class` | warning | grammar（spend time doing + 时态）|
| ¶3 第 3 句 | `you are great person` | `you are a great person` | warning | grammar（冠词）|
| ¶4 末 | `Let's do small things in a great way to be our own hero` | `By doing small things in a great way, we can become our own heroes` | tip | lexical（语气偏口语 + 单复数）|

合计 3 处 warning + 1 处 tip，0 处 critical，符合 11 档"有少量语言错误"。

## 为什么 11 分不是 14 分（边界判定）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| 错误数量 | 3 处 warning + 1 tip | 11（14 档允许 ≤2 处小错）|
| 严重错误 | 0 | 14 |
| 行文流畅度 | 衔接略机械，高级词少 | 11 |
| 用词地道度 | `greatest saying` / `amazing quality` 等略泛泛 | 11 |

→ 3 项指向 11，1 项指向 14，定 11 档。

## 为什么 11 分不是 8 分（边界判定）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| 切题 | 切题（非"基本切题"） | 11 |
| 表达清晰 | 清楚（非"不够清楚"）| 11 |
| 错误严重度 | 无 critical | 11 |

→ 4 项全部指向 11 或以上，明显优于 8 档。

## 升档路径（11 → 14）

1. 消除 iss-1 / iss-2 语法错误至"个别小错"（≤2 处）
2. 用词升级：`great` → `remarkable`；`amazing` → `inspiring`；`popular` → `well-respected`
3. ¶2 Miss Chen 例证扩展（加入具体细节）
4. ¶4 加入 1 处复杂句式（非谓语 / 倒装）
5. 替换机械衔接（obviously / so）为隐性衔接（In this regard / Consequently）

---

# 该样例用途

- **Step 3 定档**：CET-4 11 档中位 few-shot
- **Step 4 档内调节**：`delta=0`（相当）基准
- **边界判定**：11 vs 14 / 11 vs 8 两个边界的典型
