# 输出契约（Output Schema）

> `result.json` 是本 Skill 的**主产出**；其它 Markdown / HTML 文件均为渲染副产物。
> 子 Skill 调用方（`lit-review-writer` / `academic-coach` 等）只消费 `result.json`。

## Contents

- [一、顶层结构](#一顶层结构)
- [二、summary_card 字段详解](#二summary_card-字段详解)
- [三、connection_points 字段详解](#三connection_points-字段详解)
- [四、deep_dive_answers 字段详解](#四deep_dive_answers-字段详解)
- [五、comparison 字段详解](#五comparison-字段详解)
- [六、provenance-audit.json](#六provenance-auditjson)
- [七、文件目录树](#七文件目录树)
- [八、子 Skill 调用契约](#八子-skill-调用契约)

---

## 一、顶层结构

```json
{
  "meta": { ... },
  "inputs_summary": { ... },
  "papers": [ { /* PaperResult */ } ],
  "comparison": null | { /* ComparisonResult */ },
  "provenance_summary": { ... },
  "warnings": [ ... ],
  "next_step_hint": "..."
}
```

---

## 二、`meta`

```json
{
  "skill_version": "0.1.0",
  "generated_at": "2026-04-23T10:15:00Z",
  "mode": "single | compare",
  "depth_used": ["skim", "guided", "deep"],
  "language": "zh",
  "papers_processed": 1
}
```

- `depth_used` 按实际触发的档位组合填（见 `input-schema.md` §2.4 规则）
- `mode=compare` 时 `depth_used` 至少包含 `"compare"`

---

## 三、`papers[i]`（PaperResult，每篇一个对象）

```json
{
  "label": "PaperA",
  "title": "SelfInstruct: Aligning LMs with Self-Generated Instructions",
  "authors": ["Y. Wang", "..."],
  "year": 2023,
  "venue": "ACL 2023",
  "total_pages": 14,
  "summary_card": { /* 见 §3.1 */ },
  "recommended_questions": [ /* 见 §3.2 */ ],
  "connection_points": [ /* 见 §3.3；非引导模式为 null */ ],
  "deep_dive_answers": [ /* 见 §3.4；非精读模式为 null */ ],
  "references": [ /* 见 §3.5；可空数组（启发式抽取失败时） */ ],
  "references_meta": { /* 见 §3.5；总是有这个键 */ }
}
```

### 3.1 `summary_card`（裸读输出，每篇必出）

```json
{
  "research_question": "能否用 LM 自生成的指令数据做指令微调，且媲美人工标注？",
  "method": "175 条种子指令 bootstrap 扩展到 52K，经分类/过滤后微调",
  "dataset": "52K 自生成指令对；无额外人工标注",
  "key_results": [
    "在 SuperNI 上比 GPT-3 vanilla 提升 33%",
    "与 InstructGPT_001 持平（差距 5% 内）"
  ],
  "contributions": [
    "提出 Self-Instruct 框架",
    "发布 52K 指令数据集",
    "首次证明自生成指令微调的可行性"
  ],
  "limitations": [
    "依赖基座模型 GPT-3 的初始能力",
    "未验证小模型自生成能力",
    "长尾任务覆盖不足"
  ],
  "provenance_map": {
    "research_question": { "page": 1, "section": "Introduction" },
    "method": { "page": 3, "section": "3. Method" },
    "dataset": { "page": 5, "section": "3.2 Dataset Construction" },
    "key_results": [
      { "page": 7, "section": "5.1 Main Results" }
    ],
    "contributions": { "page": 2, "section": "Contributions" },
    "limitations": { "page": 11, "section": "6. Limitations" }
  }
}
```

**硬约束**：`provenance_map` 每个字段**必填**，匹配不到时填 `{"page": null, "section": null, "note": "未在原文显式找到，AI 综合推断"}` 并在 `warnings` 中添加 `LOW_PROVENANCE_CONFIDENCE`。

### 3.2 `recommended_questions`（裸读输出，每篇必出）

```json
[
  {
    "q": "52K 指令的质量过滤标准是什么？",
    "why": "方法的可信度决定了后续复现价值"
  },
  {
    "q": "长尾任务覆盖不足，具体是哪些任务？",
    "why": "直接影响你在幻觉评估方向上的适用范围"
  },
  {
    "q": "自生成的指令与人工标注在多样性上有差距吗？",
    "why": "多样性不足会导致微调模型的幻觉行为放大"
  }
]
```

- 默认 3 条，`preferences.max_recommended_questions` 控制上限（2–5）
- 每条的 `why` **不能**是 "这是个重要问题" 这种空话，必须具体到"对用户 / 研究 / 复现有什么价值"

### 3.3 `connection_points`（引导模式输出，否则 null）

```json
[
  {
    "type": "methodology_reusable",
    "insight": "Self-Instruct 的 bootstrap 机制可用于你方向上『幻觉类型』的数据集自动扩展",
    "evidence_pages": [3, 4],
    "relevance_score": 0.68
  },
  {
    "type": "gap_identified",
    "insight": "本文未做多模态场景 —— 正是你方向的空白",
    "evidence_pages": [11],
    "relevance_score": 0.82
  }
]
```

- `type` 枚举见 [guided-connection-taxonomy.md](guided-connection-taxonomy.md)（6 种）
- `evidence_pages` **非空数组**（否则视为幻觉关联点，不入输出）
- `relevance_score` 0.0–1.0，综合 embedding 相似度 + LLM 打分
- 条数由 `preferences.max_connection_points`（3–7，默认 5）控制

### 3.4 `deep_dive_answers`（精读模式输出，否则 null）

```json
[
  {
    "question": "本文的 52K 指令数据是怎么采样的？",
    "answer": "作者从 175 条人工种子指令出发... 最终筛出 52K 条。",
    "original_excerpts": [
      {
        "page": 5,
        "section": "3.2 Dataset Construction",
        "text": "We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples..."
      },
      {
        "page": 5,
        "section": "3.3 Filtering",
        "text": "We filter out instructions with ROUGE-L > 0.7 similarity to any existing instruction."
      }
    ],
    "critical_analysis": {
      "agree_with": ["采样流程设计合理，bootstrap + 过滤形成闭环"],
      "question": [
        "ROUGE-L 0.7 的阈值没做消融实验",
        "2 条模型生成样本的引入可能加剧自迭代偏差，作者未讨论"
      ],
      "complement": [
        "对你方向：如果直接复用该流程生成『幻觉实例』，需注意 bootstrap 的偏差放大效应"
      ]
    }
  }
]
```

**硬约束**：
- `original_excerpts` **非空数组**（每个元素必含 `page + section + text`）
- 三段 `critical_analysis` **至少填 2 段**（空段填 `[]`）
- `text` 必须是**原文的 ngram**（5-gram 可匹配），否则触发 `HALLUCINATED_EXCERPT`
- 若论文未涉及该问题 → `answer = "原文未涉及该问题"`, `original_excerpts = []`, `critical_analysis = null`

### 3.5 `references` + `references_meta`（v0.4.0 / P0-A 新增）

> **来源**：`scripts/parse_pdf.py::_extract_references()` 启发式抽取的结果，**直接落到 PaperResult**，
> 由下游（文献综述助手 / 学术教练）按需消费。LLM 在 Step 3-7 也可参考，但**不强求**填补。

```json
{
  "references": [
    {
      "idx": 1,
      "raw": "[1] Wang Y., Liu J., et al. Self-Instruct: Aligning LMs ... NeurIPS 2023.",
      "page": 12,
      "year": 2023
    },
    {
      "idx": 2,
      "raw": "[2] Taori R., Gulrajani I., et al. Stanford Alpaca ... 2023.",
      "page": 12,
      "year": 2023
    }
  ],
  "references_meta": {
    "extracted": true,
    "section_title": "References",
    "section_pages": [12, 14],
    "extraction_notes": ["启发式抽取 38 条；非可靠字段（authors/title）请由 LLM 二次解析"],
    "rule_version": "v0.1-heuristic"
  }
}
```

**契约**：
- `references` **总是数组**（即便启发式抽取失败也是 `[]`，不是 `null`）
- `references_meta.extracted: false` 时，`references = []` 且 `extraction_notes` 必含失败原因
- `references[i]` 的**强约束字段**：`idx` (int) + `raw` (str ≥ 10 字符)
- **弱约束字段**：`year` (int | null) + `page` (int | null)
- **不抽取的字段**（留给 LLM）：`authors_parsed` / `title_parsed` / `venue` / `doi` —— 启发式不保证准确，宁缺勿错

**为什么不在 parse_pdf.py 抽 author/title**：
- 引文格式差异巨大（ACL / IEEE / APA / 自创格式...），启发式准确率 < 70% 时不如不抽
- 这些字段由消费方（文献综述助手）决定是否补——可以走 GROBID / refextract 重型方案，也可以走 LLM 解析

---

## 四、`comparison`（多篇对比模式，否则 null）

```json
{
  "papers_labels": ["A", "B", "C"],
  "dimensions": ["research_question", "method", "dataset", "results", "limitations"],
  "table": [
    {
      "dimension": "method",
      "rows": {
        "A": {
          "content": "Self-Instruct bootstrap",
          "provenance": { "page": 3, "section": "3. Method" }
        },
        "B": {
          "content": "Direct human annotation",
          "provenance": { "page": 4, "section": "4.1" }
        },
        "C": {
          "content": "Distillation from GPT-4",
          "provenance": { "page": 5, "section": "3.2" }
        }
      }
    }
  ],
  "differences_narrative": [
    {
      "theme": "数据来源",
      "summary": "A 用自生成，B 靠人工标注，C 靠蒸馏。三者质量与成本呈 C > B > A 递增...",
      "cite": { "A": [3], "B": [4], "C": [5] }
    }
  ],
  "cross_paper_answer": null,
  "key_takeaways_for_user_direction": null,
  "synthesis_block": null
}
```

**条件输出**：
- 若 `context.specific_question` 存在 → 填 `cross_paper_answer`（结构同 §3.4 但跨论文合成）
- 若 `context.my_direction` 存在 → 填 `key_takeaways_for_user_direction`（字符串数组）
- 若 `papers.length >= 2` 且未设置 `preferences.disable_synthesis = true` → 填 `synthesis_block`（结构与契约见 [comparison-dimensions.md § 八](comparison-dimensions.md#八synthesis_blockv040--p1-a-新增对比的画龙点睛)）

**硬约束**：
- `table[i].rows[label].content == "—"` 表示"PaperX 未提及该维度"，允许但必须在 narrative 中说明
- `differences_narrative` **≥ 2 个 theme**（太少说明对比价值低，提示用户）
- 每个 `narrative.cite` 的 key 必须是 `papers_labels` 的子集
- `synthesis_block.method_evolution[*].label` 必须是 `papers_labels` 的子集；length 必须 = papers.length

---

## 五、`provenance_summary`

```json
{
  "total_claims": 23,
  "with_page_citation": 23,
  "hallucination_risk_flags": 0,
  "user_review_required": 0,
  "ngram_match": {
    "high_confidence": 20,
    "medium_confidence": 3,
    "low_confidence": 0,
    "failed": 0
  }
}
```

- `total_claims` = 所有含数字 / 专名 / 方法名的陈述数（由 `scripts/verify_provenance.py` 统计）
- `with_page_citation / total_claims` 应 **= 1.0**（100% 覆盖），否则触发警告
- `hallucination_risk_flags` > 0 时必须在 `next_step_hint` 中提示用户确认

---

## 六、`warnings`（数组）

```json
[
  {
    "level": "info | warning | error",
    "code": "LOW_PROVENANCE_CONFIDENCE",
    "message": "PaperA 的 limitations 字段未在原文显式找到，为 AI 综合推断",
    "paper_label": "A",
    "affected_field": "summary_card.limitations"
  }
]
```

**常见 warning codes**：

| code | level | 触发条件 |
|---|---|---|
| `LOW_PROVENANCE_CONFIDENCE` | warning | ngram 匹配 low 或 provenance_map 某字段 page=null |
| `HALLUCINATED_EXCERPT` | error | `deep_dive.original_excerpts[i].text` ngram 匹配失败 |
| `DIMENSION_NOT_FOUND` | info | 对比模式下某维度在某论文中取不到信息 |
| `PAPER_TOO_LONG` | warning | 超过 50 页，建议用文献综述 Skill |
| `MIXED_LANGUAGES` | info | 多篇论文语言不一致（中英混合）|
| `LOW_RELEVANCE` | info | 某 connection_point 的 relevance_score < 0.3 |
| `TOPIC_DIVERGENCE` | warning | compare 模式多篇主题跨度大，对比价值有限 |

---

## 七、`next_step_hint`（字符串）

Step 8 的主动询问话术，固定模板：

```
是否需要一份可下载/打印的 HTML 一体化报告？
报告包含：每篇摘要卡 + 关联点（若有）+ 精读回答（若有）+ 对比表（若多篇）+ Provenance 审计汇总。
回复「是 / 生成 / 要 / HTML / 好」即生成；回复「否 / 不用 / 跳过」则跳过。
```

若存在 `hallucination_risk_flags > 0` 或 error 级 warning，在询问前**先追加**一段确认请求。

---

## 八、文件产出清单

```
./paper-reader-output/<timestamp>-<mode>/
├── result.json                     # 本 schema 的主产物（子 Skill 消费）
├── summary-cards/
│   ├── paper-a.md                  # 渲染自 papers[0].summary_card
│   └── ...
├── connection-points/              # 若 depth_used 含 guided
│   └── paper-a-connections.md
├── deep-dive/                      # 若 depth_used 含 deep
│   └── paper-a-answer.md
├── comparison/                     # 若 mode == compare
│   ├── comparison-table.md
│   ├── differences-narrative.md
│   └── cross-paper-answer.md       # 若 context.specific_question
├── provenance-audit.json           # scripts/verify_provenance.py 的详细输出
└── report.html                     # Step 8 按需生成
```

**`timestamp`** 格式：`yyyymmdd-hhmmss`（如 `20260423-101500`），时区 UTC。
