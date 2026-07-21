---
exam_level: Postgrad1A
band: 4
raw_score: 8
task_subtype: letter
letter_category: complaint
task_type: letter
anchor_tags: [v1.6, new-letter-category-anchor, complaint-letter]
reference_source: "基于考研英语一 2010 / 2017 真题投诉信题型风格自构"
prompt: |
  Directions:
  Write a letter of about 100 words to the customer service department of an online
  bookstore, making a complaint about a book you recently purchased. You should include
  specific details of the problem and request appropriate compensation.
  Do not sign your own name at the end of the letter. Use "Li Ming" instead.
  Do not write the address. (10 points)
---

# 样例作文原文

```
Dear Customer Service Manager,

I am writing to express my deep dissatisfaction with the condition of a book I
received from your online bookstore last week. The book, "Advanced Data Science"
(Order No. 20240815-AX237), arrived with its cover torn and more than thirty
pages water-damaged, rendering nearly half of the content illegible.

As a loyal customer who has placed over ten orders with your platform this year,
I find this matter particularly regrettable. I would therefore request either a
full refund of 198 yuan or, alternatively, the prompt replacement of the damaged
copy with an undamaged one.

I look forward to a prompt resolution to this matter and to your continued
commitment to quality service.

Yours sincerely,
Li Ming
```

（正文约 108 词，含签名）

---

# 人工阅卷批注（Postgrad1A · letter · complaint · 第四档）

## letter_category = complaint 专属检查项（v1.6 新增）

| 检查项 | 合格要求 | 本文表现 | 判定 |
|-------|---------|---------|------|
| 开头模式 | `express dissatisfaction with` / `dismayed to learn` | `I am writing to express my deep dissatisfaction with...` | ✅ 标准复合模板 |
| 事实陈述（时间+事件+损失）| 三要素齐全 | 时间（last week）+ 事件（封面破损 + 30 页水损）+ 损失（半数内容不可读 + 198 元金额）| ✅ 高质量 |
| 诉求明确 | 有具体补救方案 | `full refund of 198 yuan` 或 `prompt replacement` | ✅ 双方案给出，方便对方选择 |
| 语气坚定但克制 | `dismayed` / `disappointed` / `regrettable`，禁 `angry` / `furious` | `deep dissatisfaction` / `particularly regrettable` | ✅ 语域标准 |
| 结尾期待解决 | `look forward to a prompt resolution` / `your immediate attention` | `I look forward to a prompt resolution to this matter` | ✅ 套话到位 |

→ **5/5 项投诉信专属检查全部达标**，v1.6 `letter-categories.md` §3.7 定义的 complaint 高档位表现。

## Directions 原句照搬检测（Postgrad A 节必跑）

| 检测项 | 结果 |
|-------|------|
| ≥ 8 词连续一致 | 无 |
| 4–7 词短语重合 | `a complaint about a book` → 作文中出现"related to the book I received"，非照搬 |
| 关键词复用（允许）| `customer service` / `book` / `refund` 属合理复用 |

→ `directions_copy_check.applicable = true`, `copied_segments = []`, `overall_risk = "none"`

## 署名合规性检查

- ✅ 使用 `Li Ming`（题目指定）
- ✅ 未使用真实姓名
- ✅ 未填写地址（题目要求"Do not write the address"）

## 考研 A 节 5 维诊断

1. **任务完成度**：所有内容要点齐全（投诉事由 + 具体细节 + 诉求 + 补救方案），无遗漏
2. **语法结构与词汇**：较丰富
   - 非限定：`rendering nearly half of the content illegible` ¶1
   - 同位语：`(Order No. 20240815-AX237)` ¶1
   - 让步补充：`As a loyal customer who has placed over ten orders...` ¶2
   - High-tier 词：`regrettable / prompt resolution / commitment`
3. **语言准确性**：语言基本准确，仅有 1 处 tip 级用词
4. **衔接与连贯**：`I find this matter... / I would therefore request... / I look forward to...` 形成自然推进链条
5. **格式与语域**：
   - 格式：称呼 + 正文 3 段 + 客套结尾 + 署名，齐全
   - 语域：formal，零口语成分
   - 署名合规 ✅

## 标注错误

| 位置 | 原文 | 建议 | 分级 | 类型 |
|-----|-----|-----|-----|-----|
| ¶2 中 | `I find this matter particularly regrettable` | 可保留；升级版：`I find the state of affairs particularly disappointing` | tip | stylistic（`particularly regrettable` 已是高阶表达，升级空间小）|

合计 0 critical + 0 warning + 1 tip — 符合考研英一 A 节第四档"只有在试图使用较复杂结构或较高级词汇时才有个别错误"。

## 为什么第四档不是第五档（complaint 专属视角）

| 判定点 | 本文表现 | 档次指向 |
|-------|---------|---------|
| 投诉信格式合规 | 全部合规 | 5 |
| 事实精确度 | 订单号 + 具体损坏范围 + 金额（全定量）| 5 |
| 复杂结构 | 非限定 ×1 + 同位语 ×1 + 让步结构 ×1 = 3 处 | 4-5 边界 |
| 辩证性 / 层次递进 | 仅单向抱怨 → 诉求，**缺少与品牌关系的张力（如"尽管是忠实客户"）的更深层次铺垫** | 4 |
| High-tier 多样性 | `regrettable / prompt resolution` 两处 high-tier；但未触及 academic（如 `egregious / inexcusable oversight`）| 4 |
| 字数 | 108 词，稍超 100 词目标 | 不扣分（无上限惩罚）|

→ 结构完整 + 证据充分 + 高阶表达 = **第四档（8 分）**，未达第五档是因：
① 未触及 academic tier 词汇
② 缺 1 处复杂结构变体（如倒装强调：`Seldom have I encountered such a lapse in quality control...`）
③ 辩证张力不足

## 为什么第四档不是第三档

- ✅ 格式全合规（第三档常缺 signature 或结尾客套）
- ✅ 语域 formal 一致（第三档常出现 `I am really angry` 等口语化）
- ✅ 诉求明确且双方案（第三档常仅说 `please solve it`）
- ✅ 证据定量（订单号+金额+页数）

→ 明显优于第三档。

## 升档路径（Postgrad1A complaint · 4 → 5）

1. **语气强化不失克制**（加 1 处 academic tier）：
   - `I am writing to express my deep dissatisfaction` → `I am writing to register a formal complaint concerning an egregious lapse in quality control`
2. **加 1 处倒装强调**：
   - `I find this matter particularly regrettable.` → `Seldom, in my ten years as a reader, have I received a book in such a state.`
3. **加入让步+转折强化辩证**：
   - `Admittedly, minor blemishes are occasionally unavoidable in long-distance shipping; nevertheless, the damage sustained here falls far beyond any reasonable tolerance.`
4. **诉求段加时间期限**（加强 task_completion）：
   - `a full refund of 198 yuan` → `a full refund of 198 yuan **to be processed within seven working days**`
5. **结尾加呼应品牌价值**：
   - `your continued commitment to quality service` → `your otherwise exemplary commitment to quality service, which I trust will be upheld on this occasion as well`

---

# 该样例用途

- **v1.6 新 letter_category = complaint 锚点样例**：第一篇投诉信校准
- **complaint 高档位金标**：展示"语气坚定但克制 + 证据定量 + 双方案诉求"三要素齐全的考研 A 节投诉信典范
- **Step 6 letter_category 识别**：本文 Directions 含 `complaint` 关键词，Skill 应自动识别为 `letter_category = "complaint"` 并启用专属检查
- **教学价值**：中国考生写投诉信最大雷区是"语气失控"（`I am so angry that...`），本文通过 `regrettable / dissatisfaction` 示范了正确语域；另一雷区是"诉求泛泛"（`please solve it`），本文给出了定量双方案
