---
exam_level: Postgrad2A
task_subtype: notice
band: 2
raw_score: 4
raw_score_max: 10
reference_source: "2021 考研英语二 A 节风格自构，low anchor（第二档中位）——Directions 照搬 + 署名违规双金标样例"
anchor_tags: [subtype:notice, band:2, gold-standard-directions-copy, gold-standard-signature-violation]
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

> Notice
>
> Our university is to host a summer camp for international students. I write this notice to
> briefly introduce the camp activities and call for volunteers.
>
> The camp will have many activities. We will visit some places. We will also eat food together.
> It will be very fun. If you want to join, please come.
>
> Volunteers are welcome. You need to speak good English. You need to be kind. Please send a
> email to me.
>
> Thank you.
>
> Zhang Wei
> April 22, 2026

**字数**：约 78 词（要求"about 100 words"，明显偏短）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌ **两个要点均被浅描**：活动介绍仅 "visit places / eat food / be fun"（3 条笼统）；志愿者招募仅 "speak English / be kind" 两条。**没有任何具体信息**（地点、时间、报名方式） |
| 语法结构与词汇 | ❌ **语法单一，词汇贫乏**：全文 SVO；`many / good / kind / fun` 均为低阶词；无从句 |
| 语言准确性 | ⚠️ **小错若干**：`a email` (art)、`send a email to me` (偏口语)，但不严重 |
| 衔接与连贯 | ❌ **几乎无衔接词**：句间靠并列罗列，段间无过渡 |
| 格式与语域 | ❌❌ **严重违规 × 2**：① **署名错误**——Directions 明确要求 `Use "Li Ming" instead`，考生签 `Zhang Wei` ② **Directions 原句照搬**——¶1 "Our university is to host a summer camp for international students" 与 Directions 前 10 词完全一致 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | format | 末尾 | Zhang Wei | Li Ming | 违反 Directions 署名要求 |
| iss-2 | critical | discourse | ¶1 全句 | Our university is to host a summer camp for international students | You are welcome to join our summer camp designed for international friends | Directions 原句连续 10 词照搬，触发机械抄袭扣分 |
| iss-3 | critical | discourse | ¶1 第 2 句 | I write this notice to briefly introduce the camp activities and call for volunteers | Hereby we announce the opening of the camp and extend an invitation for volunteers | 继续照搬 Directions 第二句（约 9 词一致） |
| iss-4 | warning | format | 字数 | 78 词 | 约 100 词（±10） | 偏短 22%，触发 shortfall_ratio=0.22 的 warning 级降档 |
| iss-5 | warning | lexical | ¶3 | send a email | send an email / drop me an email | 冠词错用 |
| iss-6 | tip | lexical | 全文 | many / good / kind / fun | various / fluent / enthusiastic / enjoyable | 低阶词升 mid tier |

## directions_copy_check

```json
{
  "applicable": true,
  "overall_risk": "critical",
  "copied_segments": [
    {
      "essay_text": "Our university is to host a summer camp for international students",
      "matched_directions": "Suppose your university is to host a summer camp for international students",
      "consecutive_words": 10,
      "severity": "critical",
      "deduction_risk": "1 分",
      "note": "连续 10 词一致（仅 Suppose/Our 差异），触发第一段机械照搬扣 1 分"
    },
    {
      "essay_text": "I write this notice to briefly introduce the camp activities and call for volunteers",
      "matched_directions": "Write a notice to briefly introduce the camp activities, and call for volunteers",
      "consecutive_words": 9,
      "severity": "warning",
      "deduction_risk": "0.5 分",
      "note": "连续 9 词一致（仅句首主语差异），触发第二句机械照搬扣 0.5 分"
    }
  ],
  "deduction_amount": 1.5
}
```

## 为什么是第二档（3–4），给 4 分（再扣 Directions 后落到 2.5 → 再减署名 0.5 → 最终 2.0）

### 档内定档路径

| 步骤 | 计算 | 说明 |
|------|-----|------|
| 1. 5 维画像 | 第二档上限 4 分 | 两要点浅描 + 语法单一 + 小错若干 |
| 2. Directions 照搬扣分 | 4 − 1.5 = 2.5 | 两段命中（critical 1 分 + warning 0.5 分）|
| 3. 署名违规扣分 | 2.5 − 0.5 = 2.0 | Directions 明确要求却违反 |
| 4. 字数不足 shortfall_ratio | (100 − 78) / 100 = 0.22 | 触发 warning 级（但由于本文已至第二档低位，不再额外扣分，改为 **记录在 intra_band_adjustment = 0**）|
| **final_score** | **2.0** | |

### 为何不落到第一档（1–2）

- 仍有**三段结构**（虽薄），文字**部分可辨**；
- 话题（summer camp）与题目一致，未完全偏题。

## 升档路径（→ 第三档 5–6）

1. **完全重写 ¶1**：`Dear fellow students, this July our campus will welcome 50 international
   participants for a two-week cultural immersion camp.`
2. **具体化活动**：改为 "Scheduled highlights include calligraphy workshops, a tea-art session
   and a tour to the Old Town."
3. **具体化招募**：改为 "We are looking for 20 volunteers, ideally with conversational English
   (CET-6 or above) and availability from July 5 to 18."
4. **正确署名 Li Ming**：必改项。
5. **补 20+ 词凑够 100**：加报名方式 / 联系电话。

## 跨试卷对比（vs postgrad1a-02-band-letter-01）

| 维度 | 本文（英二 A 通知）| postgrad1a-02（英一 A 书信）|
|------|-------------------|--------------------------|
| 同档触发机制 | Directions 照搬（10 词 + 9 词）+ 署名违规 | Directions 照搬（15 词）+ 署名违规 |
| 文体差异 | notice（布告语域）| letter（书信语域）|
| 满分差异 | 10 分满分 | 10 分满分 |
| 扣分合计 | 1.5 + 0.5 = 2 分 | 1.5 + 0.5 = 2 分 |
| **结论** | 英一/英二 A 节 **扣分规则一致**，仅题型语域不同 | 同左 |

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2A",
  "task_subtype": "notice",
  "band": 2,
  "raw_score": 4,
  "final_score": 2,
  "deductions_total": 2.0,
  "directions_copy_check_risk": "critical",
  "expected_key_rationale": [
    "第一段连续 10 词照搬 Directions（扣 1 分）",
    "第二句连续 9 词照搬 Directions（扣 0.5 分）",
    "署名 Zhang Wei 违反 Directions 要求（扣 0.5 分）",
    "字数 78 词偏短 22% 但已至低位，不再重复扣分"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2A", "effective": 78, "requirement_min": 80,
 "requirement_max": null, "within_range": false, "penalty_triggered": true,
 "shortfall_ratio": 0.22, "penalty_level": "warning"}
```
