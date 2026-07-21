---
exam_level: Postgrad2A
task_subtype: notice
band: 4
raw_score: 8
raw_score_max: 10
reference_source: "2021 考研英语二 A 节 风格自构，high anchor；题型为【通知】以区分英一 A 书信样例"
prompt: |
  Directions: Suppose you are the chair of the Student Union. Write a notice of no less than 100 words
  to recruit volunteers for an international conference on campus. Your notice should include
  the brief introduction of the conference, qualifications required, and how to contact the organizers.
  Do not use your own name. Use "Li Ming" instead.
directions_text: |
  Suppose you are the chair of the Student Union. Write a notice of no less than 100 words to
  recruit volunteers for an international conference on campus.
required_signature: "Li Ming"
---

# 样例作文原文

> **NOTICE**
>
> **November 5, 2026**
>
> The Student Union is delighted to announce that the **2026 International Conference on
> Green Technology** will be hosted on our campus from December 10 to 12. To ensure the
> smooth running of this high-profile event, we are now recruiting 30 volunteers.
>
> Volunteers will assist with guest reception, simultaneous-interpretation support, and
> session coordination. Candidates are expected to have a solid command of spoken English
> (CET-6 or above preferred), a strong sense of responsibility, and prior volunteering
> experience will be considered a plus. Prior to the conference, a two-day training covering
> etiquette and logistics will be provided free of charge.
>
> Interested students are welcome to submit a brief application, together with a recent
> resume, to su@example.edu.cn by November 20. For further information, please contact
> Li Ming at 138-xxxx-xxxx.
>
> **The Student Union**

**字数**：约 140 词（不含标题/日期）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **三要点齐全**：会议简介（Green Technology / Dec 10–12）+ 资格要求（CET-6、责任心、经验）+ 联系方式（邮箱 + 电话）|
| 语法结构与词汇 | ✅ **较丰富**：`to ensure... running of`（不定式目的）、`together with...`、`prior to...`、被动 `will be provided`；词汇 `high-profile / a solid command of / considered a plus` 属 mid+high tier |
| 语言准确性 | ✅ **基本准确**，仅 1 处 tip（见下）|
| 衔接与连贯 | ✅ **适当衔接**：段落间逻辑清晰（announce → 具体要求 → 报名方式）|
| 格式与语域 | ✅ **通知格式标准**：标题 NOTICE + 日期 + 正文 + 落款机构；语域 formal-ish，无 casual 用词 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | discourse | ¶2 | Candidates are expected to have a solid command ... and prior volunteering experience will be considered a plus | 拆分或改为并列结构 | 当前句将 3 项要求混合为 1 长句，第 3 项（experience）用独立主句打破并列，读起来略突兀，建议拆成 2 句 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [],
  "overall_risk": "none",
  "note": "全文未出现与 Directions 连续 8 词以上的重合；'recruiting volunteers' 类 2-3 词短语属关键词级复用，不扣分"
}
```

## 为什么是第四档（7–8），给 8 分

### 档内调节 +1（第四档 7–8 取高位 8）

- 对照第四档："**较好地完成试题规定的任务**" ✅
- "**包含所有内容要点，允许漏 1–2 次重点**" ✅（三要点齐）
- "**较丰富的语法结构和词汇**" ✅
- "**语言基本准确**" ✅
- "**适当的衔接手法**" ✅
- "**格式与语域较恰当**" ✅

**为什么 8 而非 7**：通知格式极为标准（标题/日期/正文/落款机构），格式加分明显；全文无 grammar 错误，1 处仅 discourse tip。

## 为什么不是第五档（9–10）

| 边界判定要素 | 本文档表现 | 第五档标准 |
|-------------|-----------|------------|
| 语法/词汇"丰富" | mid+high tier，但缺 academic | "**丰富**"应含 academic 词 + 多样复杂句 |
| 衔接手法 | 3 种（to ensure / prior to / For further information）| "**有效地采用了多种衔接手法**，文字连贯，层次清晰" |
| 错误密度 | 0 grammar + 1 tip | "**极少错误**"（0 tip 更佳）|
| 语域"贴切" | formal-ish | "**恰当贴切**"（如 `delighted` 换成 `pleased to announce`，更 formal） |

## 升档路径（→ 第五档 9–10）

1. **加 1 处复杂句式**：`Drawing on our campus's strength in international exchanges, the Student Union is pleased to announce that ...`（分词状语）
2. **词汇升档**：`candidates are expected to → candidates shall possess` / `a plus → a distinct advantage`
3. **去掉 iss-1 的 discourse tip**：拆句
4. **加段内衔接**：第二段加 `Specifically,...` 开头，凸显"资格说明"层次

## 英二 A vs 英一 A 的题型对比（本样例的锚点价值）

本样例与 `postgrad1a-04-band-letter-01.md` 形成**跨试卷同档位对比**：

| 维度 | 英一 A（书信） | 英二 A（通知） |
|------|---------------|---------------|
| 读者定位 | **特定个人**（Peter）| **全体学生**（匿名群体）|
| 语域 | semi-formal（个人邮件）| formal（官方公告）|
| 开头 | `Dear Peter, / I am delighted to learn...` | `The Student Union is delighted to announce...` |
| 落款 | `Yours sincerely, / Li Ming` | 机构落款 `The Student Union` |
| Directions 照搬风险 | 高（容易照抄项目名）| 中（关键词级复用为主）|

**Skill 实现要点**：`task_subtype` 必须区分 `letter / notice / announcement / memorandum`，对应不同的格式检查规则。

## 字数验证

```python
{"exam_level": "POSTGRAD2A", "effective": 140, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
