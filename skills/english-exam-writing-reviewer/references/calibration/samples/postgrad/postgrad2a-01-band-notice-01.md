---
exam_level: Postgrad2A
task_subtype: notice
band: 1
raw_score: 2
raw_score_max: 10
reference_source: "2021 考研英语二 A 节风格自构，bottom anchor（第一档）—— 偏题 + 格式崩 + 语法崩 + 字数严重不足"
anchor_tags: [subtype:notice, band:1, bottom-anchor, v1.5-gap-fill, multiple-critical-faults]
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

> Hello everyone,
>
> Summer is comming. My university is going to host a activity. I think it is very good. Many
> people want to join it. Last year I also go to a camp and I enjoy very much. It is really
> fun. You should come. Please tell your friend.
>
> Bye bye,
> Xiao Wang

**字数**：约 58 词（要求 ~100，偏短 42%）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌❌ **严重偏题**：题目明确要求"① brief introduction of camp activities ② call for volunteers"，考生却写成"去年夏令营回忆 + 劝同学来玩"；**活动介绍零信息**（"a activity"/"it is very good"）；**招募零信息**（无资格/无时间/无报名方式）；偏题 > 80% |
| 语法结构与词汇 | ❌❌ **语法崩塌**：SVO + 1 个并列从句；`comming`（拼写）/`a activity`（冠词）/`I also go to a camp and I enjoy`（时态冲突）/`tell your friend`（单复数）/ `Bye bye`（非书面）|
| 语言准确性 | ❌❌ **多处严重错误**：5 处 critical（1 拼写 + 1 冠词 + 2 时态 + 1 单复数）+ 3 tips |
| 衔接与连贯 | ❌ **几乎无衔接**：仅 `Many / Last year / also / really` 散落；段落间无逻辑 |
| 格式与语域 | ❌❌❌ **格式四重违规**：① 无 Notice 标题；② 称呼 `Hello everyone,` 非 notice 规范；③ **签名 Xiao Wang —— 严重违反 Directions "Use Li Ming instead"**；④ 结尾 `Bye bye,` 为极度 casual 用语，不符合 notice 语域 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | format | 末尾 | Xiao Wang | Li Ming | 违反 Directions 签名要求，扣 0.5 分 |
| iss-2 | critical | format | 开头 | Hello everyone, | Notice（标题）| 缺 notice 标题头 |
| iss-3 | critical | format | 结尾 | Bye bye, | — / Li Ming（直接落款即可）| notice 不用 "Bye bye" |
| iss-4 | critical | discourse | ¶1 全段 | 去年夏令营回忆 + 主观感受 | 应写本次活动内容 + 招募信息 | **严重偏题**——未完成任务 |
| iss-5 | critical | mechanical | ¶1 | comming | coming | 拼写错 |
| iss-6 | critical | grammar | ¶1 | a activity | **an** activity | 冠词误用 |
| iss-7 | critical | grammar | ¶1 | Last year I also go to a camp | Last year I **went** to a camp | 时态错 |
| iss-8 | critical | grammar | ¶1 | I enjoy very much | I **enjoyed it** very much | 时态 + 缺宾语 |
| iss-9 | warning | grammar | ¶1 末 | tell your friend | tell your **friends** | 单复数 |
| iss-10 | critical | format | 字数 | 58 词 | ~100 词 | shortfall_ratio=0.42 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [],
  "overall_risk": "none",
  "note": "考生完全偏离 Directions，反而因零引用造成任务完成度 critical"
}
```

## 为什么是第一档（1–2），给 2 分（扣署名后 → 1.5 → 定档 2）

### 档内定档路径

| 步骤 | 计算 | 说明 |
|------|-----|------|
| 1. 5 维画像 | 第一档上限 2 分 | 严重偏题 + 语法崩 + 格式 4 重违规 |
| 2. 署名违规 | 2 − 0.5 = 1.5 | Xiao Wang → 应为 Li Ming |
| 3. 字数不足 shortfall 0.42 | 1.5 − 0 | 已至第一档低位不再叠加 |
| **final_score** | **2**（四舍五入）| |

### 为何不落到 0 分

- 话题（夏令营）**仍与题目有交集**，未完全文不对题；
- 字数 > 0，有段落雏形；
- 仍可辨认为 notice 类尝试（虽格式全错）。

## 为什么不是第二档（3–4）

| 边界判定要素 | 本文表现 | 第二档标准 |
|-------------|---------|------------|
| 任务完成 | 严重偏题（活动零信息 + 招募零信息）| 需要 **基本按要求完成但漏 1-2 点** |
| 格式 | 4 重违规（无标题/称呼错/签名错/结尾错）| 格式基本到位 |
| 语言错误 | 8 处（5 critical + 3 tip）| 错误较多但不完全影响理解 |
| 字数 | 58 词（42% 不足）| ~100 词 |

## 升档路径（→ 第二档 3–4）

1. **完全重写**：丢弃"去年回忆"，回到"本次活动 + 招募"——参考 postgrad2a-02 或 03；
2. **修复格式**：加 `Notice` 标题 + `Li Ming` 正确签名 + 去掉 "Bye bye"；
3. **修复拼写与冠词**：coming / an activity；
4. **修复时态**：went / enjoyed it；
5. **补字数到 100**。

## 金标样例说明

本样例与 postgrad1a-01 配对，形成**考研 A 节两试卷的第一档对称锚点**，共同构成 **多重 critical 故障叠加** 的极端情形：
- 偏题（任务完成度 critical）
- 语法错 × 5（grammar critical 密集）
- 格式 4 重违规（format critical × 4）
- 字数严重不足（42% shortfall）

展示 Skill 在**同时触发 4 类 critical 故障**时仍能做合理定档。

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2A",
  "task_subtype": "notice",
  "band": 1,
  "raw_score": 2,
  "final_score": 2,
  "deductions_total": 0.5,
  "critical_issues_count": 8,
  "expected_key_rationale": [
    "严重偏题（写去年回忆代替本次活动 + 招募）",
    "签名 Xiao Wang 违反 Directions Li Ming 要求，扣 0.5 分",
    "无 Notice 标题 + 非正式开头 Hello everyone + Bye bye 结尾",
    "5 处 critical 语言错误（拼写 + 冠词 + 2 时态 + 单复数）",
    "字数 58 词偏短 42%"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2A", "effective": 58, "requirement_min": 80,
 "requirement_max": null, "within_range": false, "penalty_triggered": true,
 "shortfall_ratio": 0.28, "penalty_level": "warning"}
```
