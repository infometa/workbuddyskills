---
exam_level: Postgrad1A
task_subtype: letter
band: 3
raw_score: 6
raw_score_max: 10
reference_source: "2023 考研英语一 A 节风格自构，mid anchor（第三档高位）—— 与 postgrad1a-04/05 同题材，展示'基本完成但语言简单'的档位"
anchor_tags: [subtype:letter, band:3, mid-anchor, v1.5-gap-fill]
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
> Thank you for your letter about the "Aiding Rural Students" project. I am glad to tell you
> something about it.
>
> The project is mainly for children in rural areas. Every weekend, volunteers go to some
> village schools and teach the children English and math. We also play games with them. If
> you want to join, you need to come on Saturday morning and work for about four hours.
>
> We will give you training before you start. You can also get a free bus ticket and a
> certificate at the end. It is very meaningful. I hope you can join us.
>
> Please email me if you have any questions.
>
> Best wishes,
> Li Ming

**字数**：约 112 词（满足 ~100 词要求）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **基本完成**：项目对象（rural children）、活动（teach English/math + games）、时间安排、培训、回报（车票 + 证书）、报名方式全部触达；但**每点都浅描一句**，无任何细节展开 |
| 语法结构与词汇 | ⚠️ **满足任务需求但简单**：全文以 SVO 为主；仅 `If you want to join / before you start` 两处副词从句；词汇 `some / many / very meaningful / free` 均低阶 |
| 语言准确性 | ✅ **基本准确**：2 处 tip（见下），无 grammar 错误 |
| 衔接与连贯 | ⚠️ **简单衔接**：Every weekend / also / If / before / at the end —— 符合第三档"简单衔接手法"描述 |
| 格式与语域 | ✅ **基本合规**：Dear Peter / Best wishes / Li Ming 格式齐；语域 **neutral** 略偏 casual（`I am glad to tell you something / It is very meaningful`），未到 formal |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | discourse | ¶1 | I am glad to tell you something about it | I would be happy to share the details | 口语感偏重，A 节书信应偏 formal |
| iss-2 | tip | lexical | ¶3 | It is very meaningful | It can be a rewarding experience | 空泛评价，缺具体收获 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [
    { "essay_text": "Aiding Rural Students", "matched_directions": "Aiding Rural Students",
      "consecutive_words": 3, "severity": "tip", "deduction_risk": "none",
      "note": "项目名关键词复用" }
  ],
  "overall_risk": "none"
}
```

## 为什么是第三档（5–6），给 6 分

### 档内调节 +1（第三档高位）

- 对齐第三档"**基本按要求完成**试题规定的任务"——所有要点触达但展开浅；
- 对齐"**语法结构基本正确，词汇能满足任务需求**"——无严重语法错；
- 对齐"**使用简单的衔接手段**"——Every weekend / also / If / before；
- 对齐"**有一些错误，但不影响整体理解**"——2 tips；
- 语域偏 casual 但未违规——定**高位 6** 而非低位 5。

## 为什么不是第四档（7–8）

| 边界判定要素 | 本文表现 | 第四档标准 |
|-------------|---------|------------|
| 内容展开 | 每点一句话 | 需要每点**有适当细节**（如 postgrad1a-04 "six hours per fortnight" / "classroom management training"）|
| 语法丰富度 | SVO + 2 简单从句 | 需要 **较丰富**（至少 1 个倒装/非限定/介词短语状语）|
| 词汇 tier | low-mid | 需要 **mid-high**（如 commit/commence/in return）|
| 语域 | neutral 偏 casual | 需要 **basic formal**（I would be happy / please do not hesitate）|

## 为什么不是第二档（3–4）

- **所有要点均触达**，无遗漏，远超第二档"漏掉或未充分讨论某些内容"；
- 错误率低（0 grammar / 2 tips），不符合第二档"错误较多"；
- 格式正确（Dear / 签名 Li Ming），未触发格式扣分。

## 升档路径（→ 第四档 7–8）

1. **每点加 1 条具体信息**：地点（province/district）、学科细化（English 改 conversational English）、时间承诺（four hours/week for a semester）
2. **加 1–2 个高阶句式**：`Volunteers are expected to commit at least X hours per fortnight`
3. **词汇升档**：some → certain; meaningful → rewarding; teach the children → tutor primary-school pupils
4. **语域 formal 化**：开头改 `I am writing in response to your inquiry` 替代 `I am glad to tell you`
5. **结尾标准化**：`Please do not hesitate to contact me` 替代 `email me if you have any questions`

## 跨考试推演

- **投到 Postgrad2A（notice）**：partial，约 5-6/10（语言水平基本可迁移，但 notice 语域应更中性化）
- **投到 CET-4**：partial，约 8-9/15（CET-4 书信体允许，但 CET-4 议论文导向下得分受限）

## 回归测试预期值

```json
{
  "exam_level": "Postgrad1A",
  "task_subtype": "letter",
  "band": 3,
  "raw_score": 6,
  "final_score": 6,
  "expected_key_rationale": [
    "所有要点触达但每点浅描一句，无细节展开",
    "SVO 为主 + 2 个简单副词从句（If/before）",
    "low-mid tier 词汇 some/many/free",
    "语域 neutral 略 casual 但未违规",
    "格式正确 + Li Ming 正确签名"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD1A", "effective": 112, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
