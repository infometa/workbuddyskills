# 内容生成规范（Step 3–6 输出质量约束）

> 本文件是 Step 3–6 的**结构化输出护栏**，LLM 执行时必须严格按以下模板填充字段，
> 不得省略、不得空泛、不得跨字段混写。
> 从 SKILL.md v0.4.9 起下沉到此处，减少 body 体积。

## Contents

- [① 裸读摘要卡（Step 3）字段质量标准](#-裸读摘要卡step-3字段质量标准)
- [② 引导模式关联点（Step 4）填写规范](#-引导模式关联点step-4填写规范)
- [③ 精读回答（Step 5）三段结构约束](#-精读回答step-5三段结构约束)
- [④ 对比模式（Step 6）表格格式约束](#-对比模式step-6表格格式约束)

---

## ① 裸读摘要卡（Step 3）字段质量标准

| 字段 | 质量要求 | 反例（禁止） |
|---|---|---|
| `research_question` | 一句话，具体到「用什么方法解决什么问题」 | "本文研究了一个有趣的问题" |
| `method` | 包含：训练范式 / 核心模块 / 关键改进点（≥2 项） | "用了深度学习" |
| `dataset` | 名称 + 规模 + 来源（若已知） | "公开数据集" |
| `key_results` | 数字化指标 + Baseline 对比（≥1 个数字） | "效果很好" |
| `contributions` | 编号的具体贡献点（≥2 条），避免套话 | "提出了新方法，取得了更好效果" |
| `limitations` | 具体局限（数据、场景、计算成本等），不得写"作者未提及" | "仍有改进空间" |
| `method_formula` | 伪代数式（如 `Input → Module A → Loss → Output`），≤5 步 | "复杂流程" |
| `one_line_plain` | ≤40 字，零技术术语，小学生能看懂；不含 LaTeX 公式或深度技术缩写（ROUGE-L / BLEU / EM），常见英文词汇（AI / LLM）可接受 | "提出了一种基于 Transformer 的方法" |

**每个基础字段必须附 `provenance_map`，格式：`{page: N, section: "§X.X Name"}`**。
若 `pasted_text` 输入无页码，`page` 填 `null`，`section` 必须填段落标识。

---

## ② 引导模式关联点（Step 4）填写规范

每条 `connection_points` 条目必须**同时**满足以下 4 项：

| 字段 | 约束 |
|---|---|
| `type` | 只能是 6 种枚举之一：`methodology_reusable` / `baseline_reference` / `gap_identified` / `data_overlap` / `novelty_related` / `theory_extension` |
| `insight` | 格式：「本文的 **X** 可以直接用于你的 **Y**，因为 **Z**」——必须具体到方法名 / 数据集名 / 实验设置名 |
| `evidence_pages` | 必须填实际页码（不允许空数组 `[]`） |
| `relevance_score` | 范围 0.0–1.0，必须附判据（不能无理由给 1.0） |

**禁止写法**：

| 禁止 | 原因 |
|---|---|
| 「本文与你的研究方向高度相关」 | 无具体细节，对用户无价值 |
| 「可以参考借鉴」 | 空泛，缺乏 insight 具体内容 |
| 「作为 baseline 参考」（无后续说明） | 缺少"哪个实验 / 哪个指标"作参照 |

**`user_notes_placeholder` 槽位**（三子字段）：
- `relevance_override`：用户可覆盖 AI 的相关度判断
- `applicability_note`：用户填写可应用性备注
- `next_action`：用户填写下一步行动
- **严禁 AI 预填这三个字段**，必须留空供用户手动填写

---

## ③ 精读回答（Step 5）三段结构约束

```
answer:
  [直接回答，≥3 句，引用原文关键术语；
   开头模板：描述性→"根据原文，XX 是..."，比较性→"本文 XX 与 YY 的差异在于..."]

original_excerpts:
  - text: [原文引用，英文原文不强翻译]
    page: N
    section: "§X.X Name"
  （≥1 条，必含 page + section）

critical_analysis:
  agree_with:  [认可的点，需说明为何认可——不能只写"方法有创意"]
  question:    [存疑点：假设是否成立？实验设置是否公平？数据集是否有选择偏差？]
  complement:  [对用户研究方向的具体补充价值，需提及具体方法名或指标]
```

**原文未涉及时的强制模板**：

```
answer: 「原文未直接提及 XXX，以下基于相关段落推断：...（推断内容）」
```

> **NEVER** 编造数据或结论——宁可写"原文未提及"也不编造。

---

## ④ 对比模式（Step 6）表格格式约束

### 强制格式：dimension-major（禁止 paper-major）

✅ **正确（dimension-major）**：
```json
{
  "table": [
    {
      "dimension": "method",
      "rows": {
        "paper-a": { "content": "DPR + BART seq2seq", "provenance": {"page": 4, "section": "3.2"} },
        "paper-b": { "content": "SELF-RAG with reflection tokens", "provenance": {"page": 3, "section": "3.1"} }
      }
    }
  ]
}
```

❌ **禁止（paper-major）**：
```json
{
  "table": [
    { "paper": "paper-a", "method": "...", "dataset": "..." },
    { "paper": "paper-b", "method": "...", "dataset": "..." }
  ]
}
```

### 其他约束

| 约束 | 规则 |
|---|---|
| 每格 `content` 长度 | ≤80 字，超出截断并附 `provenance` 指向完整章节 |
| 取不到数据时 | `content = "—"`，`provenance.note = "原文未明确说明"` |
| `differences_narrative` | 必须包含 ≥2 个**实质性**差异主题，每个主题有具体数据或方法名佐证 |
| 带 `specific_question` 时 | 追加 `cross_paper_answer`（跨论文综合回答） |
| 带 `my_direction` 时 | 追加 `key_takeaways_for_user_direction` |
