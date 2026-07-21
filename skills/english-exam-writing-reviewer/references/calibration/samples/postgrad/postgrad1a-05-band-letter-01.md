---
exam_level: Postgrad1A
task_subtype: letter
band: 5
raw_score: 10
raw_score_max: 10
reference_source: "2023 考研英语一 A 节（46 题）风格自构，top anchor（第五档满分）—— 与 postgrad1a-04-band-letter-01 同题材同背景，档位差异纯由语言水平驱动"
anchor_tags: [subtype:letter, band:5, top-anchor, v1.5-gap-fill]
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
> Thank you sincerely for the interest you have expressed in the "Aiding Rural Students"
> initiative. Allow me to outline, in some detail, what participation would entail. At its core,
> the programme pairs university volunteers with rural primary schools in neighbouring
> provinces, where weekend tutoring covers English, mathematics and basic science; beyond
> classroom instruction, volunteers also co-organise reading clubs and cultural exchanges.
>
> Should you choose to enrol, training in classroom management will be provided before the
> semester commences, together with reimbursed round-trip transportation and modest meal
> allowances. In return, volunteers will receive a certified record of service, which may
> strengthen subsequent graduate-school or career applications. Registration closes on 15 May;
> please reply to liming@xjtu.edu.cn with your availability.
>
> Should any further clarification be required, do not hesitate to contact me.
>
> Yours sincerely,
> Li Ming

**字数**：约 142 词（约 100 要求，上限宽松，内容充实故可略多）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅✅ **全部内容要点覆盖且充实**：项目性质（学科辅导 + 阅读俱乐部 + 文化交流）、时间承诺与培训、报销与津贴、证书回报、报名方式（邮箱 + 截止日期）；**无遗漏** |
| 语法结构与词汇 | ✅✅ **非常丰富**：`Allow me to outline / Should you choose to enrol / Should any further clarification be required`（两处倒装）+ `which may strengthen subsequent...`（非限定定语）+ academic 词汇 `initiative / entail / co-organise / reimbursed / modest allowances` |
| 语言准确性 | ✅ **几乎零错误**：全文仅 1 处 tip（见下），复杂句自然不勉强 |
| 衔接与连贯 | ✅✅ **多种衔接手法自然交织**：`At its core / beyond classroom instruction / together with / In return / Should...` 跨段呼应 |
| 格式与语域 | ✅✅ **精准 formal**：Dear / Yours sincerely / Li Ming 标准商务邮件；语域一致为 academic-formal，无一处 casual |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | lexical | ¶2 末 | modest meal allowances | **modest** 稍显谦辞偏轻，可改 `basic meal allowances` | 极轻瑕疵，不影响评分 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [
    { "essay_text": "Aiding Rural Students", "matched_directions": "Aiding Rural Students",
      "consecutive_words": 3, "severity": "tip", "deduction_risk": "none",
      "note": "项目专有名词关键词级复用，不扣分" }
  ],
  "overall_risk": "none"
}
```

## 为什么是第五档（9–10），给 10 分

### 档内调节 +1（第五档高位 → 满分 10）

- 对齐第五档"**非常好地完成**试题规定的任务"——5 项要点齐全且每项展开有度；
- 对齐"**使用丰富的语法结构和词汇**"——**2 个倒装 + 1 个非限定定语 + academic tier 高阶词 6 个**；
- 对齐"**语言基本上无错误**"——仅 1 处 tip；
- 对齐"**能很好运用衔接手段**"——跨段呼应 + 多种连接词自然嵌入；
- **格式与语域完美**：标准商务邮件 + formal register + 正确签名 Li Ming；
- 距**真实考场 10 分**仅差"极个别措辞微调"——已达满分水平。

## 为什么不是第四档（7–8）

| 边界判定要素 | 本文表现 | 第四档上限标准 |
|-------------|---------|--------------|
| 语法丰富度 | 2 倒装 + 1 非限定 + 多种结构 | 至多 1 个倒装 / 非限定 |
| 衔接手法 | 跨段呼应 + 6 种连接词 | 段内适当衔接 |
| 词汇 tier | 6 个 academic 词 | 多为 mid-high tier |
| 语域 | 全程 academic-formal | neutral-formal |
| 错误密度 | 0 grammar + 1 tip | 0-1 处 tip |

## 跨考试推演（用 estimate_cross_exam.py 验证）

```bash
python scripts/estimate_cross_exam.py --source Postgrad1A --source-score 10 \
    --source-subtype letter --all
# 预期：Postgrad2A partial 9-10/10；CET4/CET6 partial 12-13/15（书信非 CET 主流）；
#      Postgrad1B/2B incompatible（letter 文体投图画/图表 = refuse）
```

## 升档路径

本文已达满分，**无升档路径**。用作 top anchor few-shot 样例供 Skill 对齐第五档天花板。

## 回归测试预期值

```json
{
  "exam_level": "Postgrad1A",
  "task_subtype": "letter",
  "band": 5,
  "raw_score": 10,
  "final_score": 10,
  "expected_key_rationale": [
    "5 项要点齐全且每项展开（学科+文化+培训+津贴+报名）",
    "2 个倒装 + 1 个非限定定语 + 6 个 academic 词",
    "跨段衔接 At its core / beyond / together with / In return",
    "formal 语域 + 正确 Li Ming 签名",
    "仅 1 处 tip，无 grammar/lexical 错误"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD1A", "effective": 142, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
