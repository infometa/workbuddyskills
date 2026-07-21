# 多篇对比维度定义（Comparison Dimensions）

> `mode = compare` 时用户从 12 + N 个维度中**多选**（`compare_dimensions`），Skill 按维度产出对比表 + 差异叙述。

## Contents

- [一、12 个内置维度总览](#一12-个内置维度总览)
- [二、每个维度的抽取启发式](#二每个维度的抽取启发式)
- [三、synthesis_block（综合块）](#三synthesis_block综合块)
- [四、自定义维度（custom）](#四自定义维度custom)
- [五、对比表格格式约束](#五对比表格格式约束)

---

## 一、12 个内置维度总览

| 维度 key | 中文名 | 抽取难度 | 典型来源 |
|---|---|:---:|---|
| `research_question` | 研究问题 | 低 | Abstract / Introduction |
| `method` | 方法 | 中 | Method / Approach |
| `dataset` | 数据集 | 低 | Dataset / Experiment Setup |
| `baseline` | 对比 baseline | 中 | Experiments |
| `metric` | 评估指标 | 低 | Evaluation |
| `results` | 关键结果 | 中 | Results / Tables |
| `novelty` | 宣称创新点 | 中 | Introduction / Contributions |
| `limitations` | 局限 | 中 | Limitations / Discussion / Conclusion |
| `dataset_size` | 数据规模 | 低 | Dataset |
| `compute_cost` | 算力成本 | 高 | Implementation Details / Appendix |
| `future_work` | 未来方向 | 低 | Conclusion |
| `reproducibility` | 可复现性 | 中 | Footer / Appendix / GitHub 链接 |

---

## 二、各维度详细定义与抽取启发式

### 2.1 `research_question`

- **格式**：1 句中文疑问句或陈述claim
- **长度**：20–40 字
- **取源启发式**：
  - 优先 Abstract 末句
  - 次选 Introduction "In this paper, we address..."
- **对比时**：重点看是否**同一个问题的不同切面**

### 2.2 `method`

- **格式**：1–2 句中文 + 保留核心技术名词英文
- **长度**：30–80 字
- **取源启发式**：Method 章节首段 + Figure 1 caption
- **对比时**：关键看**技术路线**（监督 / 自监督 / 对比 / 蒸馏 / bootstrap …）
- **填"—"条件**：本文是纯综述 / 理论分析，无具体方法

### 2.3 `dataset`

- **格式**：`<名称> · <规模> · <语言> · <领域>` 4 元组
- **示例**：`"Self-Instruct · 52K · en · 通用指令"`
- **对比时**：重点看语言 / 领域 / 规模三维是否 comparable

### 2.4 `baseline`

- **格式**：baseline 名称列表，关键 baseline 限 3 个以内
- **示例**：`"GPT-3 vanilla, InstructGPT_001, T0++"`
- **取源启发式**：Experiments Table 的列名
- **对比时**：重点看是否有**共同 baseline**（便于横向比较数字）

### 2.5 `metric`

- **格式**：主要指标名称（英文）+ 使用场景
- **示例**：`"ROUGE-L (SuperNI), Accuracy (MMLU)"`
- **对比时**：指标不同则结果不直接可比，narrative 要说明

### 2.6 `results`

- **格式**：1 条**最具代表性**的数字结果（含相对 baseline 的 delta）
- **长度**：30–60 字
- **示例**：`"SuperNI ROUGE-L 46.2（相对 GPT-3 +33%）"`
- **对比时**：转换为统一尺度（如均按 "+% 相对 baseline"）
- **警告**：若多篇 baseline 不同，narrative 中必须警示"数字不直接可比"

### 2.7 `novelty`

- **格式**：作者**宣称**的创新点（原文"we are the first to..."）
- **长度**：20–50 字
- **对比时**：看 novelty 是否**对立**（一家说 A 好，另一家说 A 不必要）

### 2.8 `limitations`

- **格式**：2–3 条（作者承认的 + AI 隐含推断分开）
- **对比时**：找**共同局限**（对用户方向特别有价值）

### 2.9 `dataset_size`

- **格式**：数字 + 单位
- **示例**：`"52K pairs"` / `"2.1M tokens"` / `"14K images"`
- **取不到填"—"，不要估算**

### 2.10 `compute_cost`

- **格式**：`<GPU 数 × 型号> × <训练时长>` 或 `<FLOPs>` 或 `"未披露"`
- **示例**：`"8 × V100 × 36h"` / `"5e22 FLOPs"` / `"未披露"`
- **常见坑**：大部分论文不披露，取不到时填 `"—"`

### 2.11 `future_work`

- **格式**：1–3 条作者展望方向
- **取源**：Conclusion 末段
- **对比时**：看是否**指向共同趋势**

### 2.12 `reproducibility`

- **格式**：`<代码/权重/数据的开放程度>` 分级
- **分级**：
  - `"full"`：代码 + 权重 + 数据全开源
  - `"code_only"`：仅代码
  - `"paper_only"`：仅论文，未见开源
  - `"closed"`：明确不开源
- **取源**：Footer 的 GitHub 链接 / Code Availability 声明

---

## 三、自定义维度（`custom:<字段名>`）

用户可传入 `custom:中文数据占比` / `custom:是否支持流式输出` 等自定义维度。

**处理规则**：
- 把字段名提交给 LLM 作为抽取目标
- LLM **必须**从每篇论文的原文中找证据（允许返回"未提及"）
- 填入 `table[i].rows[label].content` + `provenance`
- 若超过 3 篇论文均为"未提及" → 在 `warnings` 加 `CUSTOM_DIMENSION_LOW_COVERAGE`

---

## 四、`differences_narrative` 生成规则

对比表产出后，Skill **必须**额外生成 **≥ 2 个 theme** 的差异叙述。

### 4.1 theme 候选

按以下优先级挑 theme：

1. **技术路线差异** —— 不同方法路径（如 supervised vs self-supervised）
2. **数据集差异** —— 语言 / 规模 / 领域差距
3. **结果量级差异** —— 谁显著领先，差距多大
4. **共同局限** —— 多篇都承认的短板（对用户方向最有价值）
5. **算力门槛差异** —— 哪些是"低成本可复现"哪些不是
6. **可复现性差异** —— 谁开源谁不开源

### 4.2 theme 结构

```json
{
  "theme": "数据来源",
  "summary": "A 用自生成，B 靠人工标注，C 靠蒸馏。三者质量与成本呈 C > B > A 递增，但 A 的可扩展性最强。",
  "cite": {
    "A": [3],
    "B": [4],
    "C": [5]
  }
}
```

- `summary`：1–3 句中文叙述，**必须含对比陈述**（"A > B" / "A 比 B 多 X" / "只有 C 做了 Y"）
- `cite`：每个提到的 label 都要有 `[pages]` 证据

### 4.3 数量

- 至少 2 个 theme（太少说明对比价值低 → warning `TOPIC_DIVERGENCE` 或 `LOW_COMPARE_VALUE`）
- 最多 6 个 theme（太多信息过载）

---

## 五、`cross_paper_answer`（条件性）

当 `context.specific_question` 存在且 `mode = compare` 时，额外产出**跨论文合成回答**。

**结构**：同单篇精读的 `deep_dive_answers[i]`，但 `original_excerpts` 要标注来源 label：

```json
{
  "question": "哪种方法最适合低资源中文指令微调？",
  "answer": "综合看 A（Self-Instruct）最可行...",
  "per_paper_evidence": {
    "A": [
      {"page": 3, "excerpt": "bootstrap mechanism is model-agnostic..."}
    ],
    "B": [
      {"page": 9, "excerpt": "requires >40k hours of annotation..."}
    ],
    "C": [
      {"page": 13, "excerpt": "dependent on access to GPT-4 API..."}
    ]
  },
  "critical_analysis": {
    "agree_with": ["..."],
    "question": ["..."],
    "complement": ["..."]
  }
}
```

---

## 六、`key_takeaways_for_user_direction`（条件性）

当 `context.my_direction` 存在且 `mode = compare` 时，额外产出**面向用户方向的 key takeaways**。

**结构**：字符串数组，3–5 条，每条 1 句中文。

**示例**：

```json
"key_takeaways_for_user_direction": [
  "若方向是『中文多模态幻觉』，应优先借鉴 A 的 bootstrap + B 的高质量人工过滤，避开 C 的合规问题",
  "三篇都在 en-only 上评估 —— 你的中文场景工作天然有差异化",
  "A 的 ROUGE-L 0.7 阈值未做消融，你若复用要补这个实验来加强论证"
]
```

---

## 七、常见错误（NEVER）

- **NEVER** 在 `table[i].rows[X].content` 里写"本文未提及" —— 统一用 `"—"`（em dash）表示
- **NEVER** 让 `differences_narrative` 只有 1 个 theme（至少 2 个）
- **NEVER** `cite` 里的 label 不在 `papers_labels` 中
- **NEVER** 对无共同 baseline 的论文直接比较数字（必须 narrative 警告 "数字不直接可比"）
- **NEVER** `compute_cost` 基于"推测"填入 —— 取不到就 `"—"`
- **NEVER** 超过 8 个 `compare_dimensions`（表格会过宽难读）
- **NEVER** 对维度差异过大的论文（如一篇理论、一篇实证）硬凑对比 —— 在 warnings 加 `TOPIC_DIVERGENCE`

---

## 八、`synthesis_block`（v0.4.0 / P1-A 新增）—— 对比的"画龙点睛"

> 对比表 + `differences_narrative` 是**横向一行行**展示，本节是**纵向脉络化**总结：
> 帮用户从"三篇有什么不一样"升级到"这条研究线在往哪走"。
>
> 触发：`mode = compare` 且 `papers.length >= 2` 时**默认产出**；
> 关闭：用户在 `preferences.disable_synthesis = true` 时可跳过。
>
> 与 `differences_narrative` 的边界：
> - `differences_narrative` 是**主题切片**（每个 theme 一段），围绕**单一对比维度**展开
> - `synthesis_block` 是**全局视角**，回答"这条研究线在往哪走 / 共识在哪 / 还缺什么"

### 8.1 字段结构

```json
"synthesis_block": {
  "research_lineage": "Self-Instruct (2022) → Alpaca (2023) → LIMA (2023)：从『靠 LM 自动放大』到『精挑细选 1K 高质量样本』的方法论逆转",
  "method_evolution": [
    {
      "label": "A",
      "stage": "Self-Instruct",
      "year": 2022,
      "key_move": "175 seed → 52K LM 自生成 + 启发式过滤",
      "rationale": "突破人工标注瓶颈，假设规模 + 多样性 = 质量"
    },
    {
      "label": "B",
      "stage": "Alpaca",
      "year": 2023,
      "key_move": "全用 GPT-3.5 生成的 52K 跟 LLaMA 7B 微调",
      "rationale": "复现 + 工程化，证明小模型也能蒸馏 LLM 能力"
    },
    {
      "label": "C",
      "stage": "LIMA",
      "year": 2023,
      "key_move": "1K 人工精选样本 + LLaMA 65B 微调",
      "rationale": "反向论证：质量远比规模重要"
    }
  ],
  "key_disagreements": [
    {
      "topic": "数据规模 vs 数据质量",
      "positions": {
        "A": "52K 多样化（自动过滤）",
        "B": "52K 全自动（不过滤）",
        "C": "1K 人工精选（极简主义）"
      },
      "evidence_pages": { "A": 5, "B": 3, "C": 2 }
    },
    {
      "topic": "微调样本是否需要多样化指令类型",
      "positions": {
        "A": "需要（依赖 175 seed 的类别覆盖）",
        "C": "不需要（反例：1K 同质样本足够）"
      },
      "evidence_pages": { "A": 6, "C": 4 }
    }
  ],
  "consensus": [
    "对齐效果不取决于基座模型规模（7B 即可见效）",
    "评估必须包含开放式生成质量（仅 BLEU / ROUGE 不够）"
  ],
  "open_questions": [
    "1K 高质量 vs 52K 自动过滤——在跨语言场景哪个更鲁棒？",
    "LIMA 论文未做消融：1K 中哪些维度（领域 / 长度 / 难度）更关键？",
    "本批论文都没碰多模态——指令对齐如何迁移到 VLM？"
  ]
}
```

### 8.2 字段约束

| 字段 | 必填 | 类型 | 长度约束 | 说明 |
|---|:---:|---|---|---|
| `research_lineage` | ✅ | 1 句中文 | 30–120 字 | 一句话脉络，**带时间序**（年份）+ **方向词**（演进 / 逆转 / 分化）|
| `method_evolution` | ✅ | 数组 | 长度 = papers.length | 每个 entry 含 5 字段；按论文出版年份递增排序 |
| `method_evolution[i].rationale` | ✅ | 1 句 | 20–60 字 | 不是说**做了什么**（key_move 已说），而是**为什么这么做**|
| `key_disagreements` | ✅ | 数组 | 长度 ≥ 1 | 每条至少含 2 个 positions（< 2 不构成"分歧"）|
| `key_disagreements[i].evidence_pages[label]` | ✅ | int | — | 每个引用论文都要有页码，否则触发 `WEAK_SYNTHESIS_PROVENANCE` |
| `consensus` | ⚠️ | 数组 | 长度 0–5 | 全部 papers 都支持的结论才能进；找不到时填 `[]` |
| `open_questions` | ⚠️ | 数组 | 长度 0–5 | 应该是**这批论文都没回答的**问题（不是某一篇的 limitation）|

### 8.3 抽取启发式

| 字段 | 来源 | 兜底 |
|---|---|---|
| `research_lineage` | papers 按年份排序 + summary_card 的 method 关键变化点 | 找不到时序关系：填 `"三篇方向各异，未形成清晰演进线"`+ `consensus = []` |
| `method_evolution` | papers[i].summary_card.method + 出版年份 | label 不可省，至少取 papers 自带 label |
| `key_disagreements` | 找出 table[i].rows 内容差异 ≥ 70% 的维度 | 没找到时给 `"未发现实质性方法分歧（可能这批论文方向同质化）"` |
| `consensus` | 跨 papers 的 contributions / key_results 重叠提炼 | — |
| `open_questions` | 各篇 limitations 的并集 + 用户 my_direction 视角 | — |

### 8.4 与 `key_takeaways_for_user_direction` 的关系

- `synthesis_block` 是**论文之间**的关系
- `key_takeaways_for_user_direction` 是**论文 → 用户研究方向**的关系
- 两者**并存不冲突**，用户可同时拿到"研究线视角" + "我能用什么"两个角度

### 8.5 NEVER

- **NEVER** 在 papers.length < 2 时硬产出 `synthesis_block`（无法构成对比）
- **NEVER** 在 `method_evolution` 漏掉某篇 paper（即便它"和这条线无关"，也要标 `stage: "outlier"` + `rationale` 说明为何离群）
- **NEVER** 在 `consensus` 写"都很重要"这种空话（必须是**可证伪的具体结论**）
- **NEVER** 在 `key_disagreements[i].positions` 里只列 1 个 paper（< 2 不是分歧）
