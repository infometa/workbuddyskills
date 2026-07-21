---
exam_level: Postgrad1A
task_subtype: letter
band: 2
raw_score: 3
raw_score_max: 10
reference_source: "2023 考研英语一 A 节 风格自构，low anchor，含 Directions 照搬演示"
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
> I am working for the "Aiding Rural Students" project of my university and I am writing
> an email to answer the inquiry from you. I want to tell you something about our project.
>
> Our project is very good. We go to village to teach children. Children in village is
> poor and they need our help. If you come, you can teach English or math. You come one
> day every week. We very welcome you to join us.
>
> We hope you can come.
>
> Your friend,
> Zhang Hua

**字数**：约 90 词。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌ **漏掉主要内容要点**：未说明具体科目（只说 English / math 过于笼统）、无时长承诺、无培训/交通安排、无报名方式 |
| 语法结构与词汇 | ❌ **单调、重复**：`I am... I am... I want... We... We...`，9 个句子中 8 个是 SVO 简单句；词汇停留在 `good / very good / poor / teach / come`，无任何中级词 |
| 语言准确性 | ❌ **较多错误，影响理解**：详见下文 |
| 衔接与连贯 | ❌ **几乎无衔接**：段内无 `however / therefore / for instance`；段间靠重复主题词硬接 |
| 格式与语域 | ❌ **严重违规**：① 署名用 "Zhang Hua" 而非 Directions 指定的 "Li Ming"（扣分）；② 落款 `Your friend,` 过于 casual，不符合志愿者项目回复的 semi-formal 语域 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | **critical** | format | 落款 | Zhang Hua | Li Ming | **违反 Directions 明示要求**，考研 A 节该项单独扣 1–2 分 |
| iss-2 | critical | format | 落款 | Your friend, | Yours sincerely, | 语域严重不符，志愿者回复邮件不能用 `Your friend,` |
| iss-3 | critical | grammar | ¶2 第 2 句 | Children in village is poor | Children in the village **are** poor | 主谓一致 + 缺冠词 |
| iss-4 | warning | grammar | ¶2 第 3 句 | You come one day every week | You may come one day every week / Volunteers come once a week | 缺情态动词，时态/搭配错 |
| iss-5 | warning | grammar | ¶2 末句 | We very welcome you | We warmly welcome you / We sincerely welcome you | `very` 不能直接修饰动词 |
| iss-6 | warning | lexical | ¶2 第 1 句 | Our project is very good | Our project is highly meaningful / Our project has made a significant impact | `very good` 考研 A 节该档必扣（低级评价形容词）|

## directions_copy_check（触发扣分）

```json
{
  "applicable": true,
  "copied_segments": [
    {
      "essay_text": "Aiding Rural Students project of my university and I am writing an email to answer the inquiry from",
      "matched_directions": "Aiding Rural Students project of your university. Write an email to answer the inquiry from",
      "consecutive_words": 15,
      "severity": "critical",
      "deduction_risk": "1-2 分",
      "note": "连续 15 词与 Directions 原句高度重合（仅 my/your 替换），明显属于原句照搬，按考研大纲 A 节规则扣分"
    }
  ],
  "overall_risk": "critical",
  "deduction_amount": 1.5
}
```

## 为什么是第二档（3–4），给 3 分

### 档内调节 -1（在第二档区间 3–4 中取低位）

对照第二档描述"**未能按要求完成试题规定的任务**"：

- ✅ **漏掉/未能有效阐述内容要点**：只笼统提"teach English or math"，无具体安排
- ✅ **语法结构单调、词汇项目有限**：明显表现（见上）
- ✅ **有较多语法/词汇错误，影响对写作内容的理解**：3 处 critical + 3 处 warning
- ✅ **未采用恰当衔接手法**
- ✅ **格式和语域不恰当**：署名错 + 落款错

**选择第二档而非第一档**：虽然问题很多，但**仍然完成了基本回复**（告知项目、邀请加入），有基本段落结构（3 段），**未到"明显遗漏主要内容且有许多不相关内容"的第一档程度**。

### 扣分明细

| 类型 | 金额 | 说明 |
|------|------|------|
| 档次定档（第二档 raw） | 3.0 | 按档内低位 |
| Directions 原句照搬 | -1.5 | 15 词连续一致（见上 copy_check） |
| 署名违规（Li Ming → Zhang Hua） | -0.5 | 题目明示要求 |
| **final_score** | **1.0** | `max(0, 3 - 1.5 - 0.5) = 1` → 实际触发第一档（1–2 分） |

> ⚠️ **边界上浮提示**：由于扣分叠加，最终分数落入第一档区间。按考研评分逻辑，若原始定档第二档 + 扣分后进入第一档区间，需在 `rationale_trace` 显式说明 "档内扣分导致跌档"，避免与"直接定第一档"混淆。

## 升档路径（→ 第三档 5–6）

1. **首要动作**：**改写开头**，不要照搬 Directions；用自己的话复述项目背景（如 `I'm Li Ming from the AS project team and am delighted to respond to your inquiry.`）
2. **补全内容要点**：增加时长（`six hours every other weekend`）、培训（`a one-day training will be provided`）、报名方式
3. **修改基础语法错误**：`is → are` / `You come → You will / may come` / `We very welcome → We warmly welcome`
4. **格式合规**：署名改为 Li Ming，落款改为 `Yours sincerely,`
5. **消除低级评价词**：`very good → meaningful / worthwhile`

## 字数验证

```python
{"exam_level": "POSTGRAD1A", "effective": 90, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```

即使字数达标，**内容+语言+格式三重不足**依然只能定第二档。

---

# 本样例作为 Directions 照搬检测的金标锚点

这是 Skill **考研 A 节独有规则**的示范样例。对此样例运行：

```bash
python scripts/run_review.py --exam-level Postgrad1A --essay-file ... --directions-file ...
```

预期输出 `directions_copy_check.copied_segments[0].consecutive_words = 15` 且 `deduction_risk = "1-2 分"`。若 Skill 漏掉此检测 → **回归测试失败**。
