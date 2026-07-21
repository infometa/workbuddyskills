---
exam_level: Postgrad2A
task_subtype: notice
band: 5
raw_score: 10
raw_score_max: 10
reference_source: "2021 考研英语二 A 节风格自构，top anchor（第五档满分）—— 与 postgrad2a-04/02 同题材同背景"
anchor_tags: [subtype:notice, band:5, top-anchor, v1.5-gap-fill]
prompt: |
  Directions: Suppose your university is to host a summer camp for international students.
  Write a notice to
  1) briefly introduce the camp activities, and
  2) call for volunteers.
  You should write about 100 words on the ANSWER SHEET. Do not sign your own name.
  Use "Li Ming" instead.
directions_text: |
  Suppose your university is to host a summer camp for international students. Write a notice
  to briefly introduce the camp activities, and call for volunteers.
required_signature: "Li Ming"
---

# 样例作文原文

> **NOTICE**
>
> *15 June 2026*
>
> This coming July, our university is delighted to welcome fifty international students to a
> two-week Summer Cultural Immersion Camp. Scheduled highlights include calligraphy and
> tea-art workshops, a guided tour of the Forbidden City, an evening of regional cuisine, and
> weekly panel discussions on contemporary Chinese society — a programme designed to foster
> genuine cross-cultural dialogue.
>
> To ensure a rewarding experience for our guests, we are recruiting twenty student volunteers
> who are enthusiastic about intercultural exchange. Applicants should possess conversational
> proficiency in English (CET-6 or equivalent), be available from 10–23 July, and demonstrate
> prior experience in event assistance. Interested candidates are invited to submit a brief
> letter of intent to volunteer@university.edu.cn by 25 June. A short orientation session
> will follow for successful applicants.
>
> Your enthusiasm and commitment will make this summer truly memorable.
>
> Li Ming
> Student Union

**字数**：约 148 词（虽超出"约 100 词"但信息密度高且语言精练，考场惯例允许 ±30%）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅✅ **两要点深度完成**：① 活动介绍具体（4 类活动 + 设计意图）② 招募信息全维度（人数、资格、英语水平、时间、经验、报名方式、截止日期、后续流程）；**无一点漏** |
| 语法结构与词汇 | ✅✅ **非常丰富**：破折号插入语（`— a programme designed to foster...`）+ 非限定定语（`who are enthusiastic about...`）+ 被动语态（`are invited to submit`）+ 并列结构；academic 词 `delighted / foster / intercultural / proficiency / orientation / commitment` |
| 语言准确性 | ✅ **基本零错**：仅 1 处 tip（break-line punctuation） |
| 衔接与连贯 | ✅✅ **多种衔接自然**：This coming / To ensure / Interested candidates / A short orientation / Your enthusiasm —— 层层递进且无模板感 |
| 格式与语域 | ✅✅ **完美 notice 格式**：标题 NOTICE（居中/加粗）+ 日期 + 正文 + 落款 + 机构；语域 formal-academic；签名 Li Ming 正确；署名附机构"Student Union"合乎规范 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | mechanical | ¶1 破折号 | — a programme designed to foster genuine... | 更规范 `—designed to foster genuine...`（去掉"a programme"重复）| 极轻，不影响评分 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [
    { "essay_text": "summer camp for international students",
      "matched_directions": "summer camp for international students",
      "consecutive_words": 5, "severity": "tip", "deduction_risk": "none",
      "note": "5 词一致但属题目核心名词短语，无法回避，不扣分" }
  ],
  "overall_risk": "none"
}
```

## 为什么是第五档（9–10），给 10 分

### 档内调节 +1（第五档高位 → 满分 10）

- 对齐第五档"**非常好地完成**试题规定的任务"——两要点**双重展开**（活动 4 类 + 招募 8 项）；
- 对齐"**丰富语法结构和词汇**"——破折号插入 + 非限定定语 + academic tier 词 6 个；
- 对齐"**语言基本无错误**"——仅 1 处 tip（标点微调）；
- 对齐"**很好运用衔接手段**"——5 层自然过渡；
- **格式完美**：NOTICE 标题 + 日期 + 机构落款为 A 节最规范形态；
- **签名合规**：Li Ming ✓ + Student Union 机构落款（规范 extra plus）；
- 综合达真实考场满分 10 分水平。

## 为什么不是第四档（7–8）

| 边界判定要素 | 本文表现 | 第四档上限标准 |
|-------------|---------|--------------|
| 要点展开度 | 双重深度展开（4+8 子项） | 要点触达 + 适当展开（2-3 子项）|
| 语法复杂度 | 破折号插入 + 非限定 + 被动并列 | 至多 1-2 个中级句式 |
| 词汇 tier | 6 个 academic | 多为 mid-high |
| 衔接层次 | 5 层自然过渡 | 适当衔接 |
| 格式规范度 | NOTICE + 日期 + 机构落款 | 标准 notice 格式 |

## 跨考试推演

```bash
python scripts/estimate_cross_exam.py --source Postgrad2A --source-score 10 \
    --source-subtype notice --all
# 预期：Postgrad1A partial 9-10（notice 投 letter 稍弱）；CET4/CET6 partial 12-13；
#      考研 B 节 incompatible
```

## 升档路径

本文已达满分，无升档路径。作为 **Postgrad2A 第五档顶点锚点** 供 Skill 对齐。

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2A",
  "task_subtype": "notice",
  "band": 5,
  "raw_score": 10,
  "final_score": 10,
  "expected_key_rationale": [
    "两要点双重展开（活动 4 类 + 招募 8 项）",
    "破折号插入 + 非限定定语 + 被动并列 + academic tier 6 词",
    "NOTICE 标题 + 日期 + 机构落款三重格式合规",
    "签名 Li Ming 正确 + Student Union 机构落款为规范 extra plus",
    "5 层自然衔接无模板感"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2A", "effective": 148, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
