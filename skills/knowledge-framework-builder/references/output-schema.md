# output-schema.md —— 知识框架梳理 Skill 输出数据契约

> **文档定位**:`scripts/assemble_result.py` 装配的 `result.json`、子 Skill 调用方读取的主入口的字段契约。
> v1.0 起对外承诺 backward-compatible(只增不减,不改语义)。

---

## 1. 顶层字段一览

```jsonc
{
  "meta":                    "Meta",
  "inputs_summary":          "InputsSummary",
  "warnings":                "Warning[]",
  "framework_tree":          "Node",            // 单顶层 dict + 嵌套 children[]
  "tree_stats":              "TreeStats",
  "node_explanations":       "Explanation[] | null",   // null = 未升档 guided/deep
  "concept_dependencies":    "Dependency[]   | null",  // null = strategy=off
  "recommended_questions":   "Question[]",
  "provenance_summary":      "ProvenanceSummary",
  "outputs":                 "OutputManifest",
  "next_step_hint":          "string"
}
```

---

## 2. `meta`

```jsonc
{
  "skill_name":             "knowledge-framework-builder",
  "skill_version":          "string",                   // 当前 0.5.0
  "generated_at":           "ISO 8601 UTC string",
  "mode":                   "topic_only" | "material_first" | "hybrid",
  "depth_used":             ["skim"] | ["skim","guided"] | ["skim","guided","deep"],
  "language":               "zh" | "en" | "bilingual",
  "course_topic":           "string",                   // material_first 时为 "(from material_files)"
  "material_files_count":   "number",
  "fixture_id":             "string?"                   // 仅 demo 数据
}
```

---

## 3. `framework_tree` —— 单顶层 dict,递归 children[]

```jsonc
{
  "id":                "string",   // n0 / n1 / n1.1 / n1.1.1 命名规则
  "title":             "string",   // ≤ 30 字符建议
  "level":             "number",   // root = 0
  "evidence_source":   "user_material" | "ai_inference" | "curated_syllabus",
  "evidence_locator":  "EvidenceLocator?",   // user_material 时必有
  "is_focus":          "boolean?",           // 该节点是否是 guided 选中的重点
  "ai_inferred_fields":"string[]?",          // 该节点哪些字段是 AI 推断的
  "children":          "Node[]?"
}
```

### 3.1 节点 id 命名规则

| 层级 | 命名 | 例 |
|---|---|---|
| 根 | `n0` | `n0` |
| 大模块(level 1) | `n{1-9}` | `n1` / `n2` |
| 二级(level 2) | `n{大}.{小}` | `n2.1` / `n2.4` |
| 三级叶子(level 3) | `n{大}.{中}.{小}` | `n2.4.1` / `n5.3.2` |
| 四级(罕见,仅 max_levels=5 时) | `n{大}.{中}.{小}.{微}` | `n2.4.1.1` |

### 3.2 `evidence_locator`(`evidence_source = user_material` 时必有)

```jsonc
{
  "file":      "string",      // material_files[].path
  "section":   "string?",     // 可选,如 §3.4 虚拟语气
  "page":      "number?",     // markdown 通常 null
  "excerpt":   "string"       // 30-150 字原文片段,供 ngram 校验
}
```

`scripts/verify_provenance.py` 会用 excerpt 对 material 全文做 3-gram + 5-gram 双粒度匹配,见 `provenance-spec.md` §3。

---

## 4. `tree_stats`

```jsonc
{
  "total_nodes":            "number",       // 含根
  "max_depth":              "number",       // 0-based,即最大 level 值
  "max_depth_semantics":    "string",       // 可读说明,例 "= 3,层数 = 4 层"
  "level_counts":           {"0":1, "1":N, "2":N, "3":N},
  "leaf_count":             "number",
  "branching_factor_avg":   "number"        // (total - 1) / non_leaf,保留 2 位
}
```

**约束**(SKILL.md 核心原则 9):`total_nodes ≤ 100`、`max_depth + 1 ≤ max_levels`(默认 5)。

---

## 5. `node_explanations` —— guided / deep 模式

```jsonc
[
  {
    "node_id":              "string",       // 必须 ⊂ framework_tree
    "title":                "string",       // 冗余冗校验字段
    "selection_reason":     "string?",      // 仅 guided 必有,deep 可省
    "explanation":          "string",       // 200-500 字(guided)或 200-800 字(deep)
    "user_level_match":     "beginner" | "intermediate" | "advanced",
    "word_count":           "number",       // 中文字符 + 英文 word × 1.6
    "evidence_source":      "string?",      // 默认继承节点
    "drill":                "Drill?",       // 仅 deep 模式
    "cross_ref":            "string[]?"     // 仅 deep 模式,1-3 个关联节点 id
  }
]
```

### 5.1 `drill`(deep 模式扩展)

```jsonc
{
  "confusables":   "string[]",   // 1-3 条易混对比
  "examples":      "string[]"    // 1-2 道例题或正例
}
```

### 5.2 数量与字数约束(`assemble_result.py` 强校验)

| 模式 | 数量 | 单条字数 | 总字数 |
|---|---|---|---|
| guided | 5-10 | 200-500 | — |
| deep | ≤ leaf_count（单批 ≤ 15；超出时截断并写入 warnings[DEEP_BATCH_TRUNCATED]，提示用户继续下一批）| 200-800 | ≤ 30,000（超出 → DEEP_TOTAL_WORD_OVER_LIMIT warning）|

**`explanation` 三段式建议**(rubric 软检查,缺失 → low warning):
```
[定义] 1-2 句 What
[展开] 2-4 句 How / Why,含 ≥ 1 个具体例子
[易错点] 1-2 句 Pitfall(可省,但建议)
```

---

## 6. `concept_dependencies` —— 6 类依赖

```jsonc
[
  {
    "from":              "string",   // node id ⊂ framework_tree
    "to":                "string",   // node id ⊂ framework_tree
    "type":              "prerequisite" | "generalization" | "specialization"
                       | "contrast" | "application" | "tool",
    "weight":            "number?",  // 0-1,用于可视化粗细,默认 1.0
    "confidence":        "high" | "medium" | "low",
    "rationale":         "string",   // ≥ 8 字,禁止套话
    "evidence_source":   "string",
    "evidence_locator":  "EvidenceLocator?"
  }
]
```

### 6.1 全局约束

| 约束 | 限制 |
|---|---|
| 边数预算(conservative) | ≤ total_nodes × 0.15 |
| 边数预算(aggressive) | ≤ total_nodes × 0.30 |
| DAG | prerequisite 关系不可成环(Kahn 拓扑校验) |
| 自环 | from ≠ to |
| 重复 | 同 (from, to, type) 仅一条;contrast 双向去重(min, max) |
| rationale 长度 | ≥ 8 字符 |
| rationale 套话黑名单 | 紧密相关 / 息息相关 / 至关重要 等 → low warning |

详见 `concept-dependency-taxonomy.md` 与 `prompt-templates.md` §3。

---

## 7. `recommended_questions`

```jsonc
[
  {
    "id":                            "q1" | "q2" | "q3",
    "q":                             "string",
    "why":                           "string",
    "expected_depth_after_followup": ["skim"|"guided"|"deep"|"compare(future)"]
  }
]
```

**约定**:**恰好 3 条**,覆盖三类升档诱因——学习路径 / 概念依赖 / 跨课程对比。详见 `prompt-templates.md` §5。

---

## 8. `warnings`

```jsonc
[
  {
    "level":     "high" | "medium" | "low",
    "code":      "TOPIC_ONLY_HALLUCINATION_RISK" | "HYBRID_AI_DOMINANT" | ...,
    "message":   "string",
    "ui_hint":   "string"           // 顶部 ⚠️ banner / 顶部黄色提示 / informational
  }
]
```

### 8.1 已定义的 code

| code | level | 触发 |
|---|---|---|
| `TOPIC_ONLY_HALLUCINATION_RISK` | high | mode = topic_only |
| `HYBRID_AI_DOMINANT` | medium | mode=hybrid 且 AI 推断节点占比 > 50% |
| `DEEP_BATCH_TRUNCATED` | medium | deep explanations < leaf_count |
| `DEEP_TOTAL_WORD_OVER_LIMIT` | medium | deep 总字数 > 30,000 |
| `DEEP_NON_LEAF_EXPLANATION` | low | deep 模式下 explanation 写在非叶子节点 |
| `DEP_OVER_BUDGET` | medium | concept_dependencies 边数 > 预算 |
| `DEP_RATIONALE_CLICHE` | low | 含套话 |
| `DEP_LOW_CONFIDENCE_IN_CONSERVATIVE` | low | conservative 策略下含 ≠ high 的边 |
| `EXPLANATION_STRUCTURE_INCOMPLETE` | low | 缺 [定义] / [展开] 段 |

UI 渲染规则:
- `level=high` → markdown / HTML 顶部 ⚠️ 红色 banner
- `level=medium` → markdown / HTML 顶部 ℹ️ 黄色提示
- `level=low` → 仅 result.json 内,不显示在 banner

---

## 9. `provenance_summary`

```jsonc
{
  "total_nodes":                "number",
  "evidence_source_breakdown":  {"user_material": N, "ai_inference": N, "curated_syllabus": N},
  "ai_inferred_fields":         "string[]",       // 整体哪些字段是 AI 推断的
  "ngram_match_attempted":      "boolean",        // mode != topic_only 时为 true
  "ngram_match_attempted_reason":"string?",       // 仅 topic_only 时给出
  "hallucination_risk_overall": "high" | "medium" | "low",
  "user_review_required":       "boolean",
  "banner_message":             "string?"         // 仅 topic_only 时给出
}
```

`scripts/verify_provenance.py` 输出的独立 `provenance-audit.json` 是它的**详尽版**(每节点级)。

---

## 10. `outputs`(产物清单)

```jsonc
{
  "framework_md":              "framework.md",
  "framework_markmap_html":    "framework.markmap.html",
  "framework_mermaid_md":      "framework.mermaid.md",
  "framework_opml":            "framework.opml",
  "concept_dependencies_md":   "concept-dependencies.md?",   // 仅 deps 非空时
  "provenance_audit_json":     "provenance-audit.json"
}
```

**渲染规则总览**(详见 `scripts/render_outputs.py`):

| 格式 | banner | explanation 渲染 | dependencies 渲染 |
|---|---|---|---|
| `framework.md` | blockquote ⚠️ | `<details>` 折叠块,含 word_count + level | 文末按类型分组 + Mermaid flowchart |
| `framework.markmap.html` | 顶部彩色条 | 节点旁加 📖 emoji(讲解在 framework.md) | — |
| `framework.mermaid.md` | blockquote | — | flowchart TD 内嵌依赖箭头 |
| `framework.opml` | root `_note` | 节点 `_note` 字段写前 300 字 | — |
| `concept-dependencies.md` | — | — | 完整 Mermaid flowchart LR + 表格 |

---

## 11. `next_step_hint`

字符串,自动生成,引导用户尝试更高档位(由 `assemble_result._next_hint()` 计算)。例:

> 下一步可:提供 context.deep_explain=true 升档 deep;提供 concept_dependency_strategy=conservative 启用依赖图;提供 material_files 启用节点级 ngram 校验。

---

## 12. 子 Skill 调用方读取约定

```python
import json
result = json.loads(Path("result.json").read_text(encoding="utf-8"))

# 1. 检查警告等级
if any(w["level"] == "high" for w in result["warnings"]):
    # 必须向终端用户展示 banner
    ...

# 2. 拿骨架
tree = result["framework_tree"]

# 3. 拿讲解(可能为 null)
exps = result.get("node_explanations") or []

# 4. 拿依赖(可能为 null)
deps = result.get("concept_dependencies") or []
```

`schema_version` 字段(预留 v1.0+):一旦字段语义变更,在 `meta.schema_version: "1.0"` / `"2.0"` 通过版本号通知调用方。
