---
exam_level: Postgrad1A
task_subtype: letter
band: 1
raw_score: 2
raw_score_max: 10
reference_source: "2023 考研英语一 A 节风格自构，bottom anchor（第一档）—— 字数严重不足 + 格式崩坏 + 语言错误密集 + 偏题"
anchor_tags: [subtype:letter, band:1, bottom-anchor, v1.5-gap-fill, multiple-critical-faults]
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

> Hi,
>
> I get your letter. The project are for help student. We go to village and teach them. It
> are very important for poor children. I like this project very much because I was a poor
> student when I am young. Every people should help other.
>
> You can come. Thanks.
>
> Peter

**字数**：约 56 词（要求 ~100，偏短 44%）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌❌ **严重偏题 + 遗漏多数要点**：题目要求"specify the details of the project"，考生却改写成个人情感表达（"我小时候是贫困生"），**未覆盖**项目安排（时间/地点/培训/报销/报名方式）；核心任务未完成 |
| 语法结构与词汇 | ❌❌ **语法崩塌**：全文 SVO；`The project are / It are / Every people should` 主谓一致 × 3；`I was a poor student when I am young`（时态冲突）；词汇全部 low tier |
| 语言准确性 | ❌❌ **多处严重错误影响理解**：6 处——3 处主谓一致 + 1 处时态 + 1 处名词单复数 + 1 处冠词 |
| 衔接与连贯 | ❌ **几乎无衔接**：只有 `because / every` 两个简单连接词；段间无过渡 |
| 格式与语域 | ❌❌❌ **格式三重违规**：① 称呼 `Hi,` 不是 `Dear Peter,`；② **签名 `Peter`——严重违反 Directions "Use Li Ming instead"**；③ 缺 Yours sincerely / Best wishes 等结尾礼辞；语域全程 casual |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | format | 末尾 | Peter | Li Ming | 违反 Directions 签名要求（扣 0.5 分）|
| iss-2 | critical | format | 开头 | Hi, | Dear Peter, | 非 A 节标准称呼格式 |
| iss-3 | critical | format | 结尾 | Thanks. | Yours sincerely,\nLi Ming | 缺正式结尾礼辞 |
| iss-4 | critical | discourse | ¶1 全段 | 个人回忆 + 空泛评价 | 应写项目细节（时间/地点/培训/报销/报名方式）| **严重偏题**——未完成任务 |
| iss-5 | critical | grammar | ¶1 多处 | The project are / It are / Every people should | The project **is** / It **is** / **Everyone** should | 主谓一致 × 3 |
| iss-6 | critical | grammar | ¶1 | I was a poor student when I am young | when I **was** young | 时态冲突 |
| iss-7 | warning | lexical | ¶1 | I get your letter | I **received** your letter | 时态用错（应完成或过去）|
| iss-8 | critical | format | 字数 | 56 词 | ~100 词（±20）| 偏短 44%，shortfall_ratio=0.44 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [],
  "overall_risk": "none",
  "note": "考生完全没引用 Directions，反而因偏题造成更大失分"
}
```

## 为什么是第一档（1–2），给 2 分（再扣署名后 → final 1.5 → 取整 2）

### 档内定档路径

| 步骤 | 计算 | 说明 |
|------|-----|------|
| 1. 5 维画像 | 第一档上限 2 分 | 偏题 + 语法崩 + 格式崩 |
| 2. 署名违规 | 2 − 0.5 = 1.5 | Peter → 应为 Li Ming |
| 3. 字数不足（shortfall 0.44）| 1.5 − 0 | 已至第一档低位不再叠加扣分 |
| **final_score** | **2**（向上取整）| 考研允许 0.5 增量，可记 1.5 但档次仍为第一档 |

### 为何不落到 0 分

- 话题（项目、志愿）**仍与项目主题有交集**，未完全文不对题；
- 仍有段落雏形（虽只有 2 段）；
- 字数 > 0，不构成"未完成"。

## 为什么不是第二档（3–4）

| 边界判定要素 | 本文表现 | 第二档标准 |
|-------------|---------|------------|
| 任务完成 | 偏题（写个人回忆而非项目细节）| 需要 **基本按要求完成但漏 1-2 点** |
| 格式 | 3 处 critical（开头/结尾/签名）| 格式基本到位 |
| 语言错误 | 6 处严重错 | 错误较多但不完全影响 |
| 字数 | 56 词（44% 不足）| 约 100 词（±20）|

## 升档路径（→ 第二档 3–4）

1. **完全重写**：回到题目"项目细节"而非个人回忆——参考 postgrad1a-02 或 03；
2. **修复格式**：`Dear Peter,` 开头 + `Yours sincerely,\nLi Ming` 签名；
3. **修复主谓一致**：project is / it is / everyone should；
4. **修复时态**：when I was young；
5. **补字数到 100**。

## 金标样例说明

本样例用于回归测试**多重 critical 故障叠加**的极端情形：
1. 偏题（任务完成度 critical）
2. 主谓一致 × 3（grammar critical）
3. 格式三重违规（format critical × 3，含署名违规触发额外扣分）
4. 字数严重不足（44% shortfall）

展示 Skill 在**同时触发 4 类 critical 故障**时仍能做合理定档（第一档低位 = 2 分）。

## 回归测试预期值

```json
{
  "exam_level": "Postgrad1A",
  "task_subtype": "letter",
  "band": 1,
  "raw_score": 2,
  "final_score": 2,
  "deductions_total": 0.5,
  "critical_issues_count": 6,
  "expected_key_rationale": [
    "严重偏题（写个人回忆代替项目细节）",
    "签名 Peter 违反 Directions Li Ming 要求，扣 0.5 分",
    "缺正式称呼与结尾礼辞",
    "6 处严重语言错误（3 主谓一致 + 1 时态 + 1 冠词 + 1 名词单复数）",
    "字数 56 词偏短 44%"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD1A", "effective": 56, "requirement_min": 80,
 "requirement_max": null, "within_range": false, "penalty_triggered": true,
 "shortfall_ratio": 0.30, "penalty_level": "warning"}
```
