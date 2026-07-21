---
exam_level: Postgrad1A
task_subtype: letter
band: 4
raw_score: 8
raw_score_max: 10
reference_source: "2023 考研英语一 A 节（46 题）风格自构，用作 high anchor"
prompt: |
  Directions: Suppose you are working for the "Aiding Rural Students" project of your
  university. Write an email to answer the inquiry from an international student volunteer,
  specifying the details of the project. You should write about 100 words on the
  ANSWER SHEET. Do not use your own name. Use "Li Ming" instead.
directions_text: |
  Suppose you are working for the "Aiding Rural Students" project of your university.
  Write an email to answer the inquiry from an international student volunteer,
  specifying the details of the project.
required_signature: "Li Ming"
---

# 样例作文原文

> Dear Peter,
>
> I am delighted to learn of your interest in our "Aiding Rural Students" project and am
> writing to provide further details. The project primarily involves tutoring children in
> rural areas on weekends, covering subjects such as English, mathematics, and basic science.
>
> Volunteers are expected to commit a minimum of six hours per fortnight over one semester.
> We will offer free training on classroom management before the project commences, together
> with round-trip transportation to the partner schools. In return, participants will gain
> valuable teaching experience and a volunteering certificate upon completion.
>
> Should you require any further information, please feel free to contact me at
> liming@example.edu.cn. I look forward to working with you.
>
> Yours sincerely,
> Li Ming

**字数**：约 128 词（不含称呼/落款）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **包含所有内容要点**：项目内容（tutoring subjects）、时间承诺（six hours per fortnight）、培训与交通安排、志愿者收获。**允许漏 1–2 次重点**的标准达到（漏"报名方式"但用邮箱替代） |
| 语法结构与词汇 | ✅ **较丰富**：用了 `commit a minimum of`、`commences`、`in return`、`upon completion`、`should you require` 倒装句 |
| 语言准确性 | ✅ **基本准确**，仅 1 处复杂句搭配略显生硬（见下） |
| 衔接与连贯 | ✅ **适当衔接手法**：together with / In return / Should you... 多样化，不堆砌 |
| 格式与语域 | ✅ **较恰当**：标准商务邮件格式（Dear + 落款 Sincerely + 署名 Li Ming），语域 formal-ish，符合"志愿者回复"场景 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | lexical | ¶1 第 2 句 | tutoring children in rural areas on weekends | providing weekend tutoring for children in rural areas | 轻微语序瑕疵，当前结构把状语 `on weekends` 放末尾尚可，但 `weekend tutoring` 作前置修饰更地道 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [
    {
      "essay_text": "Aiding Rural Students",
      "matched_directions": "Aiding Rural Students",
      "consecutive_words": 3,
      "severity": "tip",
      "deduction_risk": "none",
      "note": "项目专有名词，关键词级复用，不扣分"
    }
  ],
  "overall_risk": "none"
}
```

## 为什么是第四档（7–8），给 8 分

### 档内调节 +1（在第四档区间 7–8 中取高位）

- 与第四档描述"**较好地完成**试题规定的任务"对齐；
- 用了 `should you require` 倒装 + `upon completion` 介词短语——超出"**较**丰富语法结构"的底线；
- 但未达第五档"**非常流畅、有效采用多种衔接手法**"——衔接基本都在句间，未见跨段过渡；
- 语言**基本准确**，仅 1 处 tip——符合"**只有复杂结构时有个别错误**"。

## 为什么不是第五档（9–10）

| 边界判定要素 | 本文档表现 | 第五档标准 |
|-------------|-----------|------------|
| 语法结构丰富度 | 有 1 个倒装 + 2 个中级句式 | 需要 **多个复合/非谓语/倒装** 的自然组合 |
| 衔接手法多样 | 句间衔接 | 需要 **段落级+句间级** 双层衔接 |
| 语言错误密度 | 0 grammar + 1 tip | 应为 **极少错误**，建议 0 处 |
| 语域"恰当贴切" | 基本 formal | 需要每句都精准 formal（如 `I am delighted` vs `I feel happy`）|

升到第五档需要：增加 1 处独立主格或分词状语 + 1 处跨段衔接（如 `As outlined above, ...`）。

## 升档路径（→ 第五档 9–10）

1. **段落级衔接**：在第二段开头加 `Beyond the content itself`（把"内容"和"要求"过渡得更显性）
2. **高阶句式**：把 "Volunteers are expected to commit a minimum of six hours..." 改成 "Volunteers are required to dedicate no fewer than six hours per fortnight, with training in classroom management to be provided prior to the commencement of the project."
3. **词汇升档**：`gain valuable teaching experience` → `cultivate pedagogical competence`（Academic tier）
4. **语域统一**：`feel free to contact me` → `do not hesitate to contact me`（Formal tier）

## 字数验证

```python
# scripts/word_count.py --essay-file ... --exam-level Postgrad1A
{"exam_level": "POSTGRAD1A", "effective": 128, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
