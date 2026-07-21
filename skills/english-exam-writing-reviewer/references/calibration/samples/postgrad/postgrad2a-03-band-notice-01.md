---
exam_level: Postgrad2A
task_subtype: notice
band: 3
raw_score: 6
raw_score_max: 10
reference_source: "2021 考研英语二 A 节风格自构，mid anchor（第三档高位）"
anchor_tags: [subtype:notice, band:3, mid-anchor, v1.5-gap-fill]
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
> Our university will host a summer camp for international students in July. The camp will
> last two weeks. During this time, we will have some activities such as visiting the Great
> Wall, learning Chinese painting, and trying Chinese food together.
>
> We now need some volunteers to help the international students. If you can speak English
> and you are free in July, please join us. You will help them in activities and also help
> them with daily life. You can get some experience and make new friends.
>
> If you are interested, please send an email to me before June 30th. Thank you.
>
> Li Ming

**字数**：约 108 词（满足 ~100 词要求）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **基本完成**：活动介绍有 3 项（长城 / 国画 / 美食）+ 招募含英语要求 + 时间 + 报名方式；但每项都**一句带过**无具体细节 |
| 语法结构与词汇 | ⚠️ **满足任务但简单**：SVO 为主；只有 `such as visiting / If... you / before June 30th` 3 处次级结构；词汇 `some / free / experience / new friends` low-mid tier |
| 语言准确性 | ✅ **基本准确**：2 处 tip（见下），无 grammar 错误 |
| 衔接与连贯 | ⚠️ **简单衔接**：during this time / also / If / now —— 第三档典型特征 |
| 格式与语域 | ✅ **基本合规**：Notice 标题 + 正文 + 签名 Li Ming；语域 **neutral**（如 `send an email to me / Thank you` 略偏 casual） |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | tip | discourse | ¶1 | some activities | `a series of cultural activities` 或直接列"4 cultural workshops" | "some" 空泛，notice 应精确 |
| iss-2 | tip | discourse | ¶2 | some experience | `valuable intercultural experience` | 评价空泛，缺具体收获 |

## directions_copy_check

```json
{
  "applicable": true,
  "copied_segments": [
    { "essay_text": "summer camp for international students",
      "matched_directions": "summer camp for international students",
      "consecutive_words": 5, "severity": "tip", "deduction_risk": "none",
      "note": "题目核心名词短语，关键词级复用" }
  ],
  "overall_risk": "none"
}
```

## 为什么是第三档（5–6），给 6 分

### 档内调节 +1（第三档高位）

- 对齐第三档"**基本按要求完成**试题规定的任务"——两要点触达；
- 对齐"**语法结构基本正确，词汇能满足任务需求**"；
- 对齐"**使用简单的衔接手段**"——during this time / also / If；
- 对齐"**有一些错误，但不影响整体理解**"——2 tips，零 critical；
- **格式规范 + 签名正确**——定**高位 6** 而非低位 5。

## 为什么不是第四档（7–8）

| 边界判定要素 | 本文表现 | 第四档标准 |
|-------------|---------|------------|
| 要点展开 | 每点一句 | 需要每点 **适当展开**（2-3 子项）|
| 语法复杂度 | 3 个次级结构 | 需要 **较丰富**（含至少 1 个中级句式）|
| 词汇 tier | low-mid | 需要 **mid-high** |
| 语域 | neutral 略 casual | 需要 **basic formal** |

## 为什么不是第二档（3–4）

- 两要点**均触达**，无遗漏——远超第二档"漏掉"；
- 错误率低（0 grammar / 2 tips），不符合"较多错误"；
- 格式正确 + Li Ming 正确签名，未触发格式扣分。

## 升档路径（→ 第四档 7–8）

1. **每点加具体**：活动改为"calligraphy, tea-art, forbidden-city tour"（4 类，非"some activities"）
2. **招募具体化**：`We are looking for 20 volunteers with CET-6 level English, available from July 10-23`
3. **语法升档**：`Interested candidates are invited to submit a letter of intent`
4. **语域 formal 化**：`Please do not hesitate to contact me at...` 替代 `send an email to me`
5. **加 1 句展望**：`Your support will make this cultural exchange truly memorable.`

## 跨考试推演

- **Postgrad1A（letter）**：partial ~6/10（notice 转 letter 需加称呼和结尾礼辞）
- **CET4**：partial ~9/15（CET-4 不主考 notice 但可接受）

## 回归测试预期值

```json
{
  "exam_level": "Postgrad2A",
  "task_subtype": "notice",
  "band": 3,
  "raw_score": 6,
  "final_score": 6,
  "expected_key_rationale": [
    "两要点触达但每点仅一句带过，无细节",
    "SVO 为主 + 3 个次级结构（such as / If / 时间状语）",
    "low-mid tier 词汇 some / free / experience",
    "格式规范 + Li Ming 签名正确",
    "语域 neutral 偏 casual（send an email to me / Thank you）"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD2A", "effective": 108, "requirement_min": 80,
 "requirement_max": null, "within_range": true, "penalty_triggered": false}
```
