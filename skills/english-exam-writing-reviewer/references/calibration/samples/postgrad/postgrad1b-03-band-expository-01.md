---
exam_level: Postgrad1B
task_subtype: expository
band: 3
raw_score: 10
raw_score_max: 20
reference_source: "2019 考研英语一 B 节风格自构，mid anchor（第三档中位），与 postgrad1b-03-band-cartoon-01.md 形成同档位文体对比"
anchor_tags: [subtype:expository, band:3, parallel-to-cartoon-03]
prompt: |
  Directions: Write an essay of 160-200 words based on the picture below. In your essay, you should:
  1) describe the picture briefly,
  2) explain its implied meaning, and
  3) give your comments.
  [Picture: A pie chart split into three slices labelled "Paper Books 25%", "E-books 35%",
  "Audio Books 40%", captioned "Reading habits of Chinese university students (2024)".
  Beside it, a student wearing earphones strolls with a smartphone — no physical book in sight.]
---

# 样例作文原文

> The picture shows a pie chart about reading habits of Chinese university students in 2024.
> According to the chart, audio books take 40%, which is the largest part. E-books follow with
> 35%. Paper books only have 25%, which is the smallest one. Next to the chart, a student is
> walking with earphones and a smartphone, and no paper book can be seen.
>
> The picture tells us that digital reading has become more popular than paper reading. There
> are several reasons for this. First, audio books are convenient because students can listen
> while they walk or take the subway. Second, e-books are easy to carry and are often cheaper
> than paper ones. Third, smartphones are already in every student's hand, so digital formats
> fit their life.
>
> In my view, digital reading and paper reading both have value. Digital reading is fast and
> convenient. Paper reading is good for deep thinking. We should use both of them.

**字数**：约 170 词（在 160–200 区间内）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ✅ **基本完成**：描述段（数据）+ 原因段（三点）+ 评论段三要素齐全；但"implied meaning"（寓意）被简化为一句 "digital reading has become more popular than paper reading"，未深入讨论**深度阅读 vs 碎片化**的对立 |
| 语法结构与词汇 | ⚠️ **满足任务需求但简单**：大量 SVO 并列；仅 `so digital formats fit their life`（结果状语）是次级复杂；词汇 `convenient / easy / cheaper / good` 均低阶 |
| 语言准确性 | ✅ **基本准确**，1 处搭配瑕疵（见下） |
| 衔接与连贯 | ⚠️ **简单衔接**：`First / Second / Third / In my view` 程式化，符合第三档"简单衔接"描述 |
| 格式与语域 | ✅ **合规**：三段结构，语域 neutral，无 casual 口语 |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | warning | lexical | ¶1 | audio books take 40% | audio books **account for / make up** 40% | `take` 不用于百分比描述；图表文体要求准确动词 |
| iss-2 | tip | discourse | ¶2 | three reasons | 原因平铺无主次 | 考研图表要求"原因需有主次/层次" |
| iss-3 | tip | lexical | ¶3 | Digital reading is fast and convenient | Digital reading affords immediacy; print reading invites contemplation | 评论段过于低阶，应升至 mid-high tier |

## 为什么是第三档（9–12），给 10 分

### 档内调节 +0（第三档中位）

- 对齐第三档"**基本完成试题规定的任务**"——三要点齐全但浅；
- 对齐"**语法结构基本正确，词汇能满足任务需求**"——无严重语法错误；
- 对齐"**简单的衔接手法**"——First/Second/Third；
- 对齐"**有一些错误但不影响理解**"——1 warning + 2 tips，未到"较多错误"程度。

## 为什么不是第四档（13–16）

| 边界判定要素 | 本文表现 | 第四档标准 |
|-------------|---------|------------|
| 内容深度 | 寓意一句带过 | 需要 **主要信息完整 + 观点有展开** |
| 语法丰富度 | SVO + 1 状语从句 | 需要 **较丰富的语法结构** |
| 衔接手法 | First/Second/Third 程式化 | 需要 **适当衔接手法** |
| 词汇层级 | low-mid tier | 需要 **较丰富词汇** |

## 为什么不是第二档（5–8）

- 文章**完成了所有子任务**，无偏题；
- 错误密度低（1 warning），不符合第二档"错误较多明显影响理解"；
- 结构清晰三段，不符合第二档"语法结构单一，用词贫乏"到失衡程度。

## 升档路径（→ 第四档 13–16）

1. **深化寓意**：¶2 首句改为 `The pie chart reveals not merely a shift in medium but a deeper
   tension between fast consumption and slow reflection.`
2. **句式多样**：把 "audio books are convenient because students can listen" 改成 "What makes
   audio books appealing is the ability to multitask — listening while commuting."
3. **词汇升档**：`convenient` → `accessible`；`easy to carry` → `portable`；`fit their life`
   → `dovetail with their routines`（Academic tier）
4. **原因有主次**：¶2 结构改为"技术推动（首要）→ 成本优势（次要）→ 场景契合（辅助）"
5. **评论辩证**：¶3 补一句 `Yet the convenience of audio may come at the cost of sustained
   attention — a capacity that paper reading uniquely cultivates.`

## 跨文体对比（vs postgrad1b-03-band-cartoon-01）

| 观察维度 | 本文（说明文/图表）| postgrad1b-03-band-cartoon |
|---------|-------------------|--------------------------|
| 共同特征 | 三要点齐全、简单衔接、低-中阶词汇、基本准确 | ✅ 同 |
| 文体特有问题 | 图表动词用错（`take` → `account for`）| 寓意与评论边界模糊 |
| 都属第三档的判据 | 均为"任务完成但浅 + 简单衔接 + 少量错误" | ✅ 同 |

## 回归测试预期值

```json
{
  "exam_level": "Postgrad1B",
  "task_subtype": "expository",
  "band": 3,
  "raw_score": 10,
  "final_score": 10,
  "expected_key_rationale": [
    "三要点齐全但寓意浅",
    "简单衔接 First/Second/Third",
    "图表动词 take 40% 不准确",
    "词汇 low-mid tier"
  ]
}
```

## 字数验证

```python
{"exam_level": "POSTGRAD1B", "effective": 170, "requirement_min": 160,
 "requirement_max": 200, "within_range": true, "penalty_triggered": false}
```
