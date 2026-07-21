# 引导关联点分类体系（Guided Connection Taxonomy）

> 引导模式下，Skill 对"用户研究方向 × 本文"做**反向挖掘**，产出 3–7 条 `connection_points`。
> 每条必须属于以下 **6 种类型**之一，且必须带 `evidence_pages` + `relevance_score`。

## Contents

- [一、6 种类型总览](#一6-种类型总览)
- [二、各类型填写规范](#二各类型填写规范)
- [三、user_notes_placeholder 槽位](#三user_notes_placeholder-槽位)
- [四、反例（禁止写法）](#四反例禁止写法)
- [五、JSON 示例](#五json-示例)

---

## 一、6 种类型总览

| 类型 | 语义 | 典型触发词 | 对用户的价值 |
|---|---|---|---|
| `methodology_reusable` | 本文方法可迁移到用户方向 | "bootstrap" / "self-supervised" / "contrastive" | 直接复用 / 改造方法 |
| `baseline_reference` | 本文可作为用户研究的 baseline | "HaluEval" / "SuperNI" / "benchmark" | 证明新方法优越性的对照 |
| `gap_identified` | 本文未覆盖的空白正是用户方向 | "we do not evaluate..." / "left for future work" | 论证用户选题创新性 |
| `data_overlap` | 数据集 / 语料可复用 | "publicly released dataset" / "GitHub repo" | 降低数据收集成本 |
| `novelty_related` | 本文的 novelty 与用户 novelty 相关 | "first to..." / "a new perspective" | 为用户 novelty 找参照 |
| `theory_extension` | 理论 / 洞察可扩展到用户场景 | "generalizes to..." / "theoretical analysis" | 借用理论框架支撑用户工作 |

---

## 二、各类型详细定义

### 2.1 `methodology_reusable`（方法可迁移）

**触发条件**：本文某个具体的**技术步骤** / **算法模块** / **训练流程**可以**直接或改造后**用到用户方向。

**insight 格式要求**：
- 必须具体到"**本文的 X 可用于你的 Y**"
- 指明迁移路径（直接复用 vs 需改造）
- **不允许**空泛如"方法有借鉴意义"

**正面示例**：

```json
{
  "type": "methodology_reusable",
  "insight": "Self-Instruct 的 bootstrap 机制（p.3 Figure 1）可用于你方向『幻觉类型数据集』的自动扩展：
    种子换成 100 条人工标注的幻觉实例，LLM 迭代生成新幻觉即可",
  "evidence_pages": [3, 4],
  "relevance_score": 0.68
}
```

**反面示例** ❌：

```json
{
  "type": "methodology_reusable",
  "insight": "本文的方法对你的研究很有启发",
  "evidence_pages": [],
  "relevance_score": 0.5
}
```

### 2.2 `baseline_reference`（可作 baseline）

**触发条件**：本文发布的**评估基准** / **benchmark** / **标准方法**可以作为用户新方法的对比对象。

**insight 格式**：
- 说明**哪个基准**可被复用
- 说明**在用户场景下需要什么改造**（如补中文子集、扩展评估维度）

**正面示例**：

```json
{
  "type": "baseline_reference",
  "insight": "本文的 HaluEval 基准（p.7 Table 2）覆盖了问答/对话/摘要三类幻觉，
    可直接作为你方法的对比 baseline。注意：需要为中文场景补充对应子集，
    本文仅 en-only",
  "evidence_pages": [7],
  "relevance_score": 0.75
}
```

### 2.3 `gap_identified`（空白发现）★ 最高价值

**触发条件**：本文**未覆盖**的某个角度，正是用户研究方向的**核心切入点**或**创新点**。

**insight 格式**：
- 明确点出**具体的空白**（不能笼统说"本文研究不够深入"）
- 说明这个空白如何支撑用户选题的**创新性论证**

**正面示例**：

```json
{
  "type": "gap_identified",
  "insight": "本文只在英文场景评估（p.11 § Limitations 明确承认），
    未涉及中文多模态 —— 正是你方向的创新切入点，
    可用本文方法论 + 中文数据论证你的必要性",
  "evidence_pages": [11],
  "relevance_score": 0.82
}
```

### 2.4 `data_overlap`（数据集可复用）

**触发条件**：本文**开源**的数据 / 代码 / 模型权重可以直接拿来用。

**insight 格式**：
- 说明数据的**规模 / 字段 / 获取方式**
- 说明在用户场景下**如何使用**（直接用 / 需过滤 / 需扩展）

**正面示例**：

```json
{
  "type": "data_overlap",
  "insight": "本文开源了 52K Self-Instruct 数据集（GitHub 链接 p.13），
    可作为你幻觉评估的『干净对照组』—— 筛出其中 3K 条数学任务，
    验证你的幻觉检测器在 clean data 上的 false positive 率",
  "evidence_pages": [13],
  "relevance_score": 0.55
}
```

### 2.5 `novelty_related`（novelty 相关）

**触发条件**：本文宣称的 novelty 与用户的 novelty **相似 / 对立 / 互补**。

**insight 格式**：
- 说明 novelty 的**对应关系**（"本文 first to X，你 first to X-in-Chinese" / "本文做 A，你做 A 的反面"）

**正面示例**：

```json
{
  "type": "novelty_related",
  "insight": "本文 novelty 是『LM 自生成指令替代人工』（Abstract），
    你的 novelty 可定位为『LM 自检测幻觉替代人工标注』—— 
    两者都是『用 LLM 替代人工』系列，写 related work 时可作为主要参照",
  "evidence_pages": [1, 2],
  "relevance_score": 0.60
}
```

### 2.6 `theory_extension`（理论扩展）

**触发条件**：本文的**理论分析** / **定理** / **结论**可以**泛化**或**延伸**到用户场景。

**insight 格式**：
- 说明**哪条理论**（最好引用原文定理号 / 命题号）
- 说明**如何扩展**到用户问题

**正面示例**：

```json
{
  "type": "theory_extension",
  "insight": "本文 § 4.2 Proposition 1 证明了『bootstrap 生成数据的熵下界』，
    这个结论可延伸到你的场景：你的幻觉数据生成的多样性也受此下界约束，
    引用时可支撑你的『数据多样性设计』章节",
  "evidence_pages": [6],
  "relevance_score": 0.45
}
```

---

## 三、`relevance_score` 评分标准

`relevance_score` ∈ [0.0, 1.0]，综合 embedding 相似度 + LLM 主观打分：

| 分数区间 | 语义 | 示例场景 |
|---|---|---|
| 0.8–1.0 | **高度相关** —— 几乎直接可用 | `gap_identified` 正好覆盖用户选题 |
| 0.6–0.8 | **中度相关** —— 需部分改造 | 方法可迁移但需改数据集 |
| 0.4–0.6 | **弱相关** —— 启发作用 | 同一领域但不同子方向 |
| 0.2–0.4 | **边缘相关** —— 可能有用 | 理论层面相似但应用差距大 |
| < 0.2 | **不相关** —— **不应出现**在输出中 | 应被过滤掉 |

**硬约束**：
- 任何 `relevance_score < 0.3` 的 connection_point **不入 `papers[i].connection_points`**
- 若所有关联点都 < 0.5 → 在 `warnings` 加 `LOW_RELEVANCE` + 提示用户"本文与你方向的关联较弱"

---

## 四、数量控制与排序

### 4.1 数量

- 由 `preferences.max_connection_points`（3–7，默认 5）控制
- 找不到 3 条高相关点时：
  - 返回实际找到的（即使只有 1 条）
  - 在 warnings 加 `LOW_RELEVANCE` 说明

### 4.2 排序

按 **类型优先级 → relevance_score 降序** 双层排序：

```
类型优先级（从高到低）：
  gap_identified > methodology_reusable > baseline_reference
  > novelty_related > data_overlap > theory_extension
```

理由：`gap_identified` 对用户选题论证价值最高（创新性），`theory_extension` 价值最弱（偏抽象）。

---

## 五、质量检查清单（AI 自检）

生成 `connection_points` 后，AI **自检**以下 5 条：

- [ ] 每条 `type` 是否属于 6 种枚举？
- [ ] 每条 `evidence_pages` 是否**非空数组**？
- [ ] 每条 `insight` 是否含"**本文 X → 你的 Y**"的显式连接语？
- [ ] 每条 `insight` 是否**具体**而非空话（避免"启发" / "借鉴" / "类似"这种虚词）？
- [ ] `relevance_score` 分布是否合理（不全是 0.5，不全是 0.9）？

任一条不过 → 重写该条或删除。

---

## 五点五、`user_notes_placeholder`（用户补充槽，v0.2.0 新增）

> **吸收来源**：SkillHub `paper-reader-deep` 的"与用户研究的关联"模板——预留用户亲手补充的空间，避免 AI 把"用户视角"全部替用户想完。

### 5.5.1 为什么要留槽？

`connection_points[i].insight` 已经是 AI 主观判断的产物。但：
- AI 可能**猜错**用户真实意图（尤其当 `my_direction` 只有一句话时）
- 用户读完这条关联后，可能**立刻想到**一个更贴切的应用场景
- 若不留槽，用户要么在脑中想想就忘，要么去别处记笔记，导致**关联上下文丢失**

### 5.5.2 字段结构

每个 `connection_points[i]` 在 **`insight` / `evidence_pages` / `relevance_score` 之外**追加：

```json
{
  "type": "methodology_reusable",
  "insight": "Self-Instruct 的 bootstrap 机制可用于你的 ...",
  "evidence_pages": [3, 4],
  "relevance_score": 0.68,
  "user_notes_placeholder": {
    "relevance_override": null,          // 用户自评相关度: "high" | "medium" | "low" | null（未填）
    "applicability_note": "",            // 用户补充："在我的场景下这个机制需要…"
    "next_action": ""                    // 用户打算做什么："明天试一下" | "先存着" | "不适用"
  }
}
```

### 5.5.3 AI 行为约束

- AI **生成时**：`user_notes_placeholder` 的三个子字段**必须全部是空值**（`null` / `""`）—— 这是预留给用户填的槽
- AI **绝不**预先填入 `applicability_note` 或 `next_action`（那是用户视角，AI 越俎代庖）
- 若用户后续 run 复用本次输出，AI 可读取 `user_notes_placeholder` 中**用户已填**的内容作为上下文，但**不覆盖**

### 5.5.4 在 HTML 报告中的呈现

`scripts/render_report.py` 渲染时将 `user_notes_placeholder` 渲染为：
- `<input type="radio">` 三选一的相关度（high / medium / low）
- `<textarea>` 两个文本框（applicability_note + next_action）
- 附一个「导出为 Markdown 笔记」按钮 —— 生成独立的 `connection-notes-{paper}.md`

---

---

## 六、常见错误（NEVER）

- **NEVER** 产出 `evidence_pages = []` 的关联点（视为幻觉，必须指向具体页码）
- **NEVER** 用"本文对你的研究很有启发 / 很有借鉴意义"这种空话
- **NEVER** 用 > 7 条关联点（噪声多，用户无法消化）
- **NEVER** 把同一个关联分成多条（如"方法有用"+"数据有用"应合成一条）
- **NEVER** `type` 乱用（如把 baseline_reference 填成 methodology_reusable）
- **NEVER** `relevance_score` 全给高分（打分要有梯度，真实反映相关性）
- **NEVER** 预先填 `user_notes_placeholder` 的三个子字段（那是用户的槽位，AI 必须留空）
