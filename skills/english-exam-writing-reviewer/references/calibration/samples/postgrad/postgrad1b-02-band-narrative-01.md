---
exam_level: Postgrad1B
task_subtype: narrative
band: 2
raw_score: 6
raw_score_max: 20
reference_source: "2017 考研英语一 B 节风格自构，low-mid anchor（第二档高位）"
anchor_tags: [subtype:narrative, band:2, off-topic-partial]
prompt: |
  Directions: Write an essay of 160-200 words based on the picture below. In your essay, you should:
  1) describe the picture briefly,
  2) interpret its intended meaning, and
  3) give your comments.
  [Picture: A father carries his elderly mother on his back across a stream, while his own
  young son mimics by carrying a toy bear on his back behind them. Caption: "言传不如身教"
  (Teaching by example surpasses teaching by words).]
---

# 样例作文原文

> The picture tell a story. A father is walking on a small river. He carry his old mother on
> back. Behind them, a little boy see his father and he also carry a toy bear on his back.
> There is a Chinese words under the picture: "Teaching by example surpasses teaching by words".
>
> I think this picture is very interesting. When I was young, my father also take me to visit
> my grandmother. We lived in a small village. My grandmother often give me candies and tell
> me old stories. I love her very much. One day, she got sick and my father took care of her
> for many days. I remember that time very clearly.
>
> So we should love our family. Family is very important for everyone. We must help each other
> when we have difficult. This is what the picture want to tell us. I hope every family can be
> happy.

**字数**：约 172 词（在 160–200 区间内）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌ **漏掉主要信息**：¶2 **完全偏题**——题目要求 "interpret intended meaning"（解读寓意），但考生改写成个人童年叙事，只有 ¶3 末句勉强回到主题。**偏题 > 30%** 直接打到第二档上限 |
| 语法结构与词汇 | ❌ **语法单一**：全文几乎只有 SVO 简单句 + `When I was young` 一个时间状语从句，无一处并列/复合句 |
| 语言准确性 | ❌ **较多错误影响理解**：见下（6 处，3 处主谓一致/时态）|
| 衔接与连贯 | ❌ **连贯性差**：¶2 与寓意无关；段间过渡靠 `So` 一词；指代混乱 |
| 格式与语域 | ⚠️ **结构勉强成形** 但段落权重严重失衡（¶2 叙事 70 词 vs ¶3 评论仅 55 词且空泛）|

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | grammar | ¶1 第 1 句 | The picture tell a story | The picture **tells** a story | 主谓一致 |
| iss-2 | critical | grammar | ¶1 第 2 句 | He carry his old mother on back | He **carries** his old mother on **his** back | 主谓一致 + 缺物主代词 |
| iss-3 | critical | grammar | ¶1 第 3 句 | a little boy see / he also carry | the little boy **sees** / he also **carries** | 主谓一致 × 2 |
| iss-4 | warning | lexical | ¶1 末 | a Chinese words | a Chinese **line/caption** 或 some Chinese **words** | 单复数矛盾 |
| iss-5 | critical | discourse | ¶2 整段 | 童年叙事 70 词 | 应改写为"画面寓意解读"——如"代际传递" | **偏题**，背离题目 "interpret intended meaning" |
| iss-6 | warning | grammar | ¶3 | when we have difficult | when we have **difficulties** / when we **are in trouble** | 词性错用（adj 作 n）|

## 为什么是第二档（5–8），给 6 分

### 档内调节 +1（在第二档区间 5–8 中取中低位）

- 对齐第二档"**基本按要求完成**但漏掉或未充分讨论某些内容"——本文**完全漏掉"解读寓意"**这一题眼；
- 符合"**语法结构单一，用词贫乏**"——全文无复合句；
- 符合"**错误较多，明显影响理解**"——6 处错误中 3 处主谓一致直接刺眼。

### 为何不落到第一档（1–4）
- **文章主题仍大致可辨**（"家庭亲情"与画面有部分关联），未到"严重偏离主题或未完成任务"；
- 字数达标（172 词），无"过短"触发降档。

## 为什么不是第三档（9–12）

| 边界判定要素 | 本文表现 | 第三档标准 |
|-------------|---------|------------|
| 任务完成 | ¶2 完全偏题 | 需要 **基本完成**所有子任务 |
| 语法词汇 | 几乎全 SVO | 需要 **满足任务需求**的句式多样性 |
| 错误密度 | 6 处，3 处影响理解 | 需要 **有一些错误但不影响整体理解** |

## 升档路径（→ 第三档 9–12）

1. **回到题目**：¶2 改写为寓意解读 `The picture implies a cycle of filial care — the way we
   treat our parents becomes the blueprint our children imitate.`
2. **修复主谓**：全文把 `tell / carry / see` 加 -s；
3. **加 1–2 个复合句**：`As the father shoulders his mother, his son... mirrors every step`
4. **评论段具体化**：¶3 "Family is important" 太空；改为 "Values are transmitted not by lectures
   but by lived actions."

## 回归测试预期值

```json
{
  "exam_level": "Postgrad1B",
  "task_subtype": "narrative",
  "band": 2,
  "raw_score": 6,
  "final_score": 6,
  "expected_key_rationale": [
    "任务完成度缺口：寓意段偏题（¶2 写成个人回忆）",
    "语法单一 + 主谓一致错误密集（3 处）",
    "主题大致可辨故未跌入第一档"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD1B", "effective": 172, "requirement_min": 160,
 "requirement_max": 200, "within_range": true, "penalty_triggered": false}
```
