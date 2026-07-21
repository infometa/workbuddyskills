# 裸读摘要卡 Rubric（6 基础字段 + 2 扩展字段）

> 每篇论文无论什么 mode / 档位，都必须生成一张摘要卡。
> **6 基础字段**：`research_question` / `method` / `dataset` / `key_results` / `contributions` / `limitations`
> **2 扩展字段**（v0.2.0 吸收自 SkillHub `paper-parse` Part B）：`method_formula` / `one_line_plain`
> 每字段**必附** `provenance_map` 指向原文 page + section（`method_formula` / `one_line_plain` 为综合推断，附 `provenance_map.aggregate_pages`）。

## Contents

- [一、6 基础字段质量标准](#一6-基础字段质量标准)
- [二、2 扩展字段规范](#二2-扩展字段规范)
- [三、provenance_map 填写规则](#三provenance_map-填写规则)
- [四、recommended_questions 生成规则](#四recommended_questions-生成规则)
- [五、完整 JSON 示例](#五完整-json-示例)

---

## 一、6 字段的语义与取源优先级

### 1.1 `research_question`（研究问题 / 核心 claim）

| 优先级 | 取源位置 |
|:---:|---|
| 1 | Abstract 末句（通常陈述 claim）|
| 2 | Introduction 的 "In this paper, we..." 句 |
| 3 | Introduction 末段总结 |
| 4 | 标题（次选，因为标题常压缩）|

**格式要求**：
- 1 句中文，30–60 字
- 以"能否 / 如何 / 是否 / 本文探究"开头
- **不直译**英文 claim，要转中文表述

**反面示例** ❌：

```
research_question: "Self-Instruct: Aligning LMs with Self-Generated Instructions"
```

（这只是标题，不是研究问题）

**正面示例** ✅：

```
research_question: "能否用 LM 自生成的指令数据做指令微调，且媲美人工标注数据？"
```

### 1.2 `method`（方法 / 模型架构 / 算法）

| 优先级 | 取源位置 |
|:---:|---|
| 1 | Method / Approach / Proposed Method 章节开头段 |
| 2 | Figure 1 / Overview Figure 的 caption |
| 3 | Abstract 中方法描述句 |

**格式要求**：
- 2–3 句中文，50–120 字
- 必须包含**核心机制**的技术名词（英文保留）
- 描述**流程骨架**而非细节

**正面示例** ✅：

```
method: "用 175 条种子指令启动，通过 bootstrap 迭代让 GPT-3 生成新指令；用 ROUGE-L 做去重过滤，
分类器区分分类任务/生成任务后分别采样实例，最终产出 52K 指令对用于 instruction tuning。"
```

### 1.3 `dataset`（数据集）

**必提取的子项**：

- **名称**（若有专门命名，如 HaluEval / SuperNI）
- **规模**（样本数 / 词数 / 图片数）
- **语言**（en / zh / multilingual）
- **领域**（通用 / 医疗 / 法律 / 代码 / ...）
- **来源**（人工 / 自生成 / 蒸馏 / 开源汇集）

**格式要求**：1–2 句中文，信息密度优先。

**正面示例** ✅：

```
dataset: "52K 自生成英文指令对（instruction + input + output 三元组），
来自 175 人工种子 × GPT-3 bootstrap；无人工标注成本。"
```

### 1.4 `key_results`（关键实验结果）

**必提取**：
- **最具代表性的 2–4 个数字结果**（性能提升 / 准确率 / 相对 baseline 的 delta）
- 每条必须可追溯到 Results / Experiments 章节

**格式要求**：
- 数组，每条 1 句中文
- **必须含数字**
- 保留英文 metric 名称（ROUGE-L / Accuracy / F1 / BLEU 等）

**正面示例** ✅：

```json
"key_results": [
  "在 SuperNI 上相对 GPT-3 vanilla 提升 33%（Zero-shot ROUGE-L 从 34.6 → 46.2）",
  "与 InstructGPT_001 在 252 个用户指令上打平（差距 < 5%）",
  "自生成数据仅 3000 条即可达到 10000 条人工数据的效果"
]
```

**反面示例** ❌：

```json
"key_results": ["方法效果显著", "超越了 baseline"]  // 无数字，违反 ngram provenance 检查
```

### 1.5 `contributions`（贡献）

**取源**：
- 优先 Introduction 末段的 "Our contributions are:" 列表
- 次选：Abstract 中"We propose / We introduce"句
- 兜底：综合 method + key_results 提炼

**格式要求**：
- 数组，**3–5 条**（少于 3 条太薄，超过 5 条太散）
- 每条 1 句中文
- **按重要性排序**

**正面示例** ✅：

```json
"contributions": [
  "提出 Self-Instruct 框架，首次证明 LM 可以用自生成数据做指令微调",
  "发布 52K 公开数据集，推动社区研究",
  "在 GPT-3 base 上验证有效性，可规模化到更大模型"
]
```

### 1.6 `limitations`（局限）

**取源优先级**：
1. Limitations / Discussion 专章（最可靠）
2. Conclusion 末段"however / yet / one concern..."
3. Related Work 中对比时承认的短板
4. AI 补充：**原文未显式提及但隐含的局限**（需标注 `note: "AI 隐含推断"`）

**格式要求**：
- 数组，2–4 条
- 作者显式承认的 vs AI 补充的要**分开**（若混在一起要在 provenance_map 中标注）

**正面示例** ✅：

```json
"limitations": [
  "依赖基座模型 GPT-3 的初始生成能力（作者承认，p.11）",
  "未验证小模型的自生成能力（作者承认，p.11）",
  "长尾/罕见任务覆盖不足（作者承认，p.11）"
]
```

**若含 AI 补充**：

```json
"limitations": [
  "依赖基座模型的初始能力（作者承认，p.11）",
  "【AI 隐含推断】自生成数据有 bootstrap 偏差放大风险，作者未讨论"
]
```

---

### 1.7 `method_formula`（方法公式化，扩展字段）

> **吸收来源**：SkillHub `paper-parse` Part B —— 把论文方法抽象成一个极简"文字公式"，揭示内在逻辑或演算过程。

**目的**：让读者看完这一行就知道「这篇论文的方法在做什么运算」，不用看完整个 Method 章节。

**格式要求**：
- 1 行 Markdown 公式（不是真 LaTeX，是"文字公式"）
- 使用 `=` / `+` / `×` / `/` 等常见符号
- **必须包含** 2–4 个核心元素（不能只有 1 个，也不能塞 10 个）
- 不含数字结果（那是 `key_results` 的职责）

**正面示例** ✅：

```json
"method_formula": "Self-Instruct = (175 条 seed 指令 + ICL 提示) × GPT-3 迭代 / ROUGE-L 去重"
```

```json
"method_formula": "RAG = Retriever(Query → Top-K) + Reader(Query + Top-K → Answer)"
```

```json
"method_formula": "可靠工业 AI = (多智能体分工 + 结构化思维链) × 实时知识库"
```

**反面示例** ❌：

```json
"method_formula": "本文提出的方法结合了多种技术"  // 无公式结构
"method_formula": "A"                          // 只一个元素
"method_formula": "X = (a+b)*c / (d*e) + log(f) - σ(g)"  // 堆符号反而失焦
```

**何时降级为 `null`**：纯综述 / 调研类论文（`research_question` 为"总结过去 5 年的 X 研究现状"）、纯理论证明类论文 —— 填 `null` + `method_formula_note: "本文为综述/理论证明，方法不可公式化"`。

### 1.8 `one_line_plain`（大白话一句话总结，扩展字段）

> **吸收来源**：SkillHub `paper-parse` Part B —— 用一个 10 岁小孩都能听懂的比喻或说法，概括论文最核心观点。

**目的**：配合 `research_question`（学术表述）形成双重定义，**降低认知门槛**。

**格式要求**：
- **1 句话**（≤ 40 字）
- **禁用术语**（任何英文技术词 / 专名都要换成日常词）
- **用动作 / 比喻 / 具体场景**
- **不重复** `research_question`（避免同义重复）

**正面示例** ✅：

| research_question（学术版） | one_line_plain（大白话版） |
|---|---|
| 「能否用 LM 自生成指令数据做微调，媲美人工标注？」 | 「让 AI 自己出题自己答，练出来居然能跟人出的题打平。」 |
| 「RAG 能否在长尾知识问答上超越参数化记忆？」 | 「模型不用记住所有知识，问的时候翻书比死记硬背更准。」 |
| 「DPO 能否不用 reward model 对齐人类偏好？」 | 「以前要先教一个『打分员』再调主模型；DPO 说不用打分员直接调。」 |

**反面示例** ❌：

```json
"one_line_plain": "本文提出了一种新的 Self-Instruct 方法用于 instruction tuning"
// ❌ 有术语、无比喻、和 research_question 重复
```

```json
"one_line_plain": "这个方法很厉害"
// ❌ 空话无信息
```

**硬约束**：
- 扫描以下词表，命中即**自动回改**：`本文 | 方法 | 模型 | 框架 | 算法 | 机制 | 提出了`
- 命中 ≥ 1 个英文技术专名（如 RAG / LSTM / Transformer） → 回改（除非该词已是大众化）

### 1.9 扩展字段 vs `writing_style` 交叉

`method_formula` 和 `one_line_plain` 是**独立字段**，与 `preferences.writing_style` 正交：
- `analytical` + 扩展字段：公式偏结构化，大白话偏"说人话"
- `feynman` + 扩展字段：公式也要体现"变形替代定义"（见 `feynman-style-rubric.md` 原则 3）；大白话贯穿全 card

---

## 二、`provenance_map` 填写规则

### 2.1 结构

```json
"provenance_map": {
  "research_question": { "page": 1, "section": "Introduction" },
  "method":            { "page": 3, "section": "3. Method" },
  "dataset":           { "page": 5, "section": "3.2 Dataset Construction" },
  "key_results": [
    { "page": 7, "section": "5.1 Main Results" },
    { "page": 7, "section": "5.1 Main Results" },
    { "page": 8, "section": "5.2 Scaling Analysis" }
  ],
  "contributions":     { "page": 2, "section": "Contributions" },
  "limitations":       { "page": 11, "section": "6. Limitations" },
  "method_formula":    { "aggregate_pages": [3, 5], "section": "3. Method, 3.2 Dataset Construction" },
  "one_line_plain":    { "aggregate_pages": [1, 2], "section": "Abstract + Introduction" }
}
```

- **5 个标量字段**（research_question / method / dataset / contributions / limitations）→ 对象
- `key_results` 是数组 → `provenance_map.key_results` 也是数组（一一对应）

### 2.2 取不到原文时的降级

| 情况 | `provenance_map` 填法 | 附加动作 |
|---|---|---|
| 原文确有章节但页码模糊 | `{"page": null, "section": "Discussion"}` | 在 `warnings` 加 `LOW_PROVENANCE_CONFIDENCE` |
| AI 综合推断（如隐含 limitation）| `{"page": null, "section": null, "note": "AI 综合推断"}` | warning 必出 |
| `pasted_text` 模式无页码 | `{"page": null, "section": "粘贴段落"}` | 提示用户用 pdf_path 获得完整页码 |

### 2.3 `section` 命名规范

- 优先使用**原文章节标题**（保留英文，如 `"3.2 Dataset Construction"`）
- Abstract / Introduction / Conclusion 常用简称
- 特殊区块：`"Figure 1 caption"` / `"Table 2"` / `"Footnote 3"`

---

## 三、`recommended_questions` 生成规则

### 3.1 三条默认问题的类型配比

| 类型 | 占比 | 说明 |
|---|---|---|
| **方法细节型** | 1 条 | 针对 method / dataset 的"怎么做的"（利于复现）|
| **局限拓展型** | 1 条 | 针对 limitations 的"为什么没做 / 能否扩展" |
| **应用启发型** | 1 条 | "这个方法能用到 X 场景吗" |

### 3.2 `why` 字段要求

`why` **不能**是：
- ❌ "这是个重要问题"
- ❌ "值得深入思考"
- ❌ "对研究有帮助"

`why` **应该**是：
- ✅ "方法的可信度决定了后续复现价值"
- ✅ "直接影响你在 X 方向上的适用范围"
- ✅ "若无消融实验，这个设计选择就是黑盒"

### 3.3 问题数量控制

- `preferences.max_recommended_questions`：默认 3，范围 2–5
- 超过 3 条时，按"方法细节 → 局限拓展 → 应用启发 → 实验设计 → 批判性质疑"顺序追加

---

## 四、常见错误（NEVER）

- **NEVER** 把 `research_question` 写成标题（标题是陈述，问题是疑问 / 探究）
- **NEVER** 在 `key_results` 里省略数字（"效果显著" ≠ 结果）
- **NEVER** 混用作者承认的 limitation 与 AI 推断的（要分开标注）
- **NEVER** 把 `contributions` 压缩到 1 条或膨胀到 10 条（保持 3–5 条）
- **NEVER** 让 `provenance_map` 有字段缺失（取不到至少填 `{page: null, section: null, note: "..."}`）
- **NEVER** 让 `recommended_questions[i].why` 是空话（必须具体到对用户 / 复现 / 应用的价值）
- **NEVER** 让 `method_formula` 只有 1 个元素或堆 10 个符号（保持 2–4 个核心元素的"文字公式"）
- **NEVER** 让 `one_line_plain` 含英文技术术语或和 `research_question` 同义重复（前者是大白话翻译，后者是学术化陈述）
