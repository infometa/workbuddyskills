---
exam_level: Postgrad1B
task_subtype: cartoon_standard
band: 1
raw_score: 2
raw_score_max: 20
reference_source: "2022 考研英语一 B 节 风格自构，low anchor（第一档），含字数不足扣分"
prompt: |
  Directions: Write an essay of 160-200 words based on the picture below.
  [Picture: Same as postgrad1b-05-band-cartoon-01.md —— 信息的海洋 vs 思想的深度]
---

# 样例作文原文

> In the picture, a man is walking. He has phone and book. Phone have many message and
> video. Book is open. The picture mean information is many but think is few.
>
> I think this is truth problem. People always use phone, not read book. Phone is fast
> but book is slow. Information on phone is not good. Book is good for think.
>
> So I think we read more book. Don't only use phone. This is better for our future.

**字数**：约 78 词（**远低于 160 词下限，严重不足**）。

---

# 人工阅卷批注（考研 5 维）

| 观察点 | 定性诊断 |
|--------|---------|
| 任务完成度 | ❌ **明显遗漏主要内容**：描述部分过于笼统（未提 *Deep Thinking* 书名、caption），寓意解读只有一句，评论只有一句；三个任务要求虽都提到但严重阐述不足 |
| 语法结构与词汇 | ❌ **单调、重复**：全篇无一复合句/非谓语结构；核心动词只有 `is / have / use / think / read`；无任何衔接词 except `So` |
| 语言准确性 | ❌ **错误多，有碍读者对内容的理解，语言运用能力差**：详见下文（7 处严重错误）|
| 衔接与连贯 | ❌ **完全无衔接**：段间无过渡，段内无逻辑连接词 |
| 格式与语域 | ❌ **无格式与语域概念**：三段看似有段落划分，但每段都只有 2–3 句极短句，缺乏段落内的逻辑展开；整体语域完全 casual |

## 标注错误（issues）

| id | severity | type | location | original | suggestion | reason |
|----|----------|------|----------|----------|-----------|--------|
| iss-1 | critical | grammar | ¶1 第 2 句 | He has phone and book | He has **a phone and a book** | 缺冠词 |
| iss-2 | critical | grammar | ¶1 第 3 句 | Phone have many message | **The phone shows** many **messages** | 主谓一致 + 名词复数 + 动词选择错 |
| iss-3 | critical | grammar | ¶1 末句 | The picture mean information is many but think is few | The picture **means that** information is **abundant** but **thinking is scarce** | 多处错：主谓一致、连接词缺失、`think` 作名词误用、用 `many/few` 修饰不可数名词 |
| iss-4 | critical | grammar | ¶2 第 1 句 | truth problem | **a real problem** / **an authentic issue** | `truth` 为名词误作形容词 |
| iss-5 | critical | grammar | ¶3 第 1 句 | we read more book | we **should read more books** | 缺情态动词 + 名词复数 |
| iss-6 | warning | lexical | 全文 | phone / book / think | fragmented information / digital content / contemplation | 无任何中级词汇 |
| iss-7 | warning | discourse | 全文 | — | — | 完全无衔接词，无段落内展开逻辑 |

## 扣分项

| 扣分类型 | 金额 | 依据 |
|---------|------|------|
| 字数不足（78 词 vs 160 下限，shortfall_ratio = 0.51）| -2 | `deduction-rules.md` "≥ 50% 短缺 → 可能触发降档" |
| 书写差（假设）| 0 | AI 无法判断 |

## 为什么是第一档（1–4），给 2 分

### 档内调节 -1（第一档区间 1–4，低位 2）

对照第一档："**未完成试题规定的任务**"：

- ✅ "**明显遗漏主要内容**" → 三要点都只浅层提及
- ✅ "**语法项目和词汇的使用单调、重复**" → 动词只有 5 个
- ✅ "**语言错误多，有碍读者对内容的理解**" → 5 处 critical grammar
- ✅ "**未使用任何衔接手法，内容不连贯**" → 完全无
- ✅ "**无格式与语域概念**" → casual 断句

**选择第一档低位 2 分而非高位 4 分**：

- 字数严重不足（仅完成规定的 48%）
- critical 错误密度过高（78 词中 5 处）
- 但**未达 0 分线**（仍有可识别的三段式和部分任务涉及）

### 初始定档 4 分 → 字数扣 2 分 → 最终 2 分

```json
{
  "band": 1,
  "raw_score": 4,
  "deductions": [
    { "type": "word_count", "amount": 2, "reason": "78 词 / 160 词下限 = 49% 短缺，按酌情 2-3 分扣" }
  ],
  "final_score": 2
}
```

## 为什么不是 0 分

对照 0 档条件："所传达的信息或所用语言太少，无法评价；内容与要求无关或无法辨认。"

本文**虽错误多但能读懂大意**（漫画批评"用手机过多、读书过少"），仍然完成了**最低限度的任务对应**（描述/寓意/评论三段都出现）——因此不判 0 分，而是**第一档低位**。

## 为什么不是第二档（5–8）

| 边界要素 | 本文档 | 第二档标准 |
|----------|--------|-----------|
| 任务完成 | 浅层提及三要点 | "漏掉或未能**有效阐述**一些内容要点" |
| 错误数量 | 5 critical + 2 warning (78 词) | "**较多**错误" |
| 连贯 | 完全无 | "**缺少**连贯性"（"缺少" vs 第一档"不连贯")|
| 格式 | 无段内展开 | "不恰当" |

**判定要点**：第二档允许"一些错误 + 一些连贯性缺失"，但本文**连最基本的谓语动词一致都错**，且**全篇无任何衔接词**——达到第一档的"语言运用能力差"标准。

## 升档路径（→ 第二档 5–8）

1. **先解决字数**：必须达到 120+ 词（虽未到 160 但至少摆脱"严重不足"扣分）
2. **补基础语法**：iss-1 ~ iss-5 全部修正——这是跨到第二档的**最低门槛**
3. **加基础衔接词**：每段至少 1 个 However / Therefore / For example
4. **展开段内内容**：每段从 2 句扩到 4 句，说清楚"是什么/为什么/如何"
5. **词汇替换**：`phone → smartphone / digital device`、`think → reflection / contemplation`、`truth → real`

---

# 本样例作为"字数扣分 + 档内边界"的金标锚点

这是 Skill **字数不足触发降档** + **第一/第二档边界判定**的综合示范。对此样例运行：

```bash
python scripts/word_count.py --essay-file ... --exam-level Postgrad1B
# 预期：effective=78, within_range=false, shortfall=82, shortfall_ratio=0.51,
#       penalty_triggered=true, penalty_hint="≥3 分，可能触发降档"
```

字数扣分逻辑错误 → **回归测试失败**。
