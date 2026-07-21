# input-schema.md —— 知识框架梳理 Skill 输入数据契约

> **文档定位**:`scripts/validate_input.py` 的输入契约规范。
> 子 Skill 调用方(study-coach / paper-quick-reader 等)须按本 schema 构造 `input.json`。
> 任何字段含义 / 取值范围变更须在版本号同步升级,v1.0 起对外承诺 backward-compatible。

---

## 1. 顶层结构

```jsonc
{
  "course_topic":     "string?",          // 与 material_files 至少一个非空
  "material_files":   "MaterialFile[]?",
  "context":          "Context?",
  "preferences":      "Preferences?"
}
```

**约束**:`course_topic` 与 `material_files` **不可同时为空**(SKILL.md Step 0)。

---

## 2. `course_topic` —— 课程主题字符串

| 维度 | 约束 |
|---|---|
| 类型 | `string`(单行,长度建议 ≤ 60) |
| 必填 | 见上(与 `material_files` 二选一) |
| 取值示例 | `"大学英语"` / `"机器学习"` / `"408 计算机统考"` / `"考研政治"` |
| 反例 | `""`(同时 material_files 也空)、`"大学英语 + 高数"`(违反单课程约束) |

**禁止**:同一字符串中跨多门课;若需多门课比较,请分多次调用并由调用方汇总。

---

## 3. `material_files` —— 用户教材 / 笔记 / 大纲

```jsonc
[
  {
    "path":   "string",          // 绝对路径或相对工作区根目录的路径
    "type":   "markdown" | "docx" | "txt" | "pasted_text",
    "label":  "string?",         // 可选,用于报告里的来源名(如「教材」「自己的笔记」)
    "content_inline": "string?"  // 仅当 type=pasted_text 时使用;path 此时可省
  }
]
```

| type | 解析方式(scripts/parse_outline.py) | 上限 |
|---|---|---|
| `markdown` | 按 `#` / `##` / `###` 解析多级标题 | 200,000 字符 |
| `docx` | python-docx + Heading 1/2/3 样式 | 5,000 段落 |
| `txt` | 启发式("第 X 章 / 1.1 / § / 中文数字") | 100,000 字符 |
| `pasted_text` | 同 txt,但内容直接放 `content_inline` | 100,000 字符 |

**被拒绝的输入源**:
- `pdf` / `image` / `webpage_url` / `video_url` / `audio_path` —— 见 `_skill_meta.json.rejected_input_sources`
- 拒绝原因:OCR 不可靠 / 非课程主题数据。请先用 paper-quick-reader 等工具预处理为 markdown 后再喂入。

---

## 4. `context` —— 学习上下文(影响深度档位与讲解语气)

```jsonc
{
  "focus_topics":     "string[]?",     // 最多 5 个,触发 guided 升档
  "learning_goal":    "string?",       // 自然语言,影响 ROI 加权
  "user_level":       "beginner" | "intermediate" | "advanced",
  "deep_explain":     "boolean?"       // true → 升档 deep
}
```

**字段对深度档位的影响**(详见 SKILL.md「核心原则 1」):

| 字段 | 触发档位 |
|---|---|
| 全空 | `[skim]` |
| `focus_topics` 任一 | `[skim, guided]` |
| `learning_goal` 非空 | `[skim, guided]` |
| `user_level` 非空 | `[skim, guided]` |
| `deep_explain: true` | `[skim, guided, deep]` |

**字段对讲解语气的影响**:

| user_level | 节点讲解风格 |
|---|---|
| `beginner` | 类比 + 大白话 + 1 个生活例子,避免术语堆砌 |
| `intermediate`(默认) | 标准定义 + 1 个例子 + 简短易混对比 |
| `advanced` | 假设已知基础 + 边界场景 + 跨知识点关联 |

详见 `prompt-templates.md` §6 user_level 适配表。

---

## 5. `preferences` —— 用户偏好(影响策略与输出)

```jsonc
{
  "language":            "zh" | "en" | "bilingual",      // 默认 zh
  "depth_hint":          "auto" | "force_skim" | "skim_only" | "force_guided" | "force_deep",
  "max_levels":          "1..5",                          // 默认 5
  "concept_dependency_strategy": "off" | "conservative" | "aggressive",  // 默认 off
  "importance_strategy": "frequency" | "centrality" | "mixed",           // 默认 centrality
  "output_formats":      ["markdown" | "markmap" | "mermaid" | "opml"][]
}
```

**`depth_hint` 优先级**:`depth_hint != auto` 时强制覆盖 context 推断。

| depth_hint | 含义 |
|---|---|
| `auto` | 按 context 字段自动判定(默认) |
| `force_skim` / `skim_only` | 强制单档 skim,忽略 context 触发 |
| `force_guided` | 强制 `[skim, guided]`,自动选 5-10 个高价值节点 |
| `force_deep` | 强制 `[skim, guided, deep]`,全叶子节点深度讲解 |

**`concept_dependency_strategy`**:

| 策略 | 边数预算 | 类型范围 | 适用 |
|---|---|---|---|
| `off`(默认) | 0 | — | 仅骨架 |
| `conservative` | ≤ total_nodes × 0.15 | prerequisite + contrast(只输出 confidence=high) | 想看核心依赖,信噪比优先 |
| `aggressive` | ≤ total_nodes × 0.30 | 6 类全开,confidence ≥ medium | 全面挖掘,牺牲信噪比 |

**`importance_strategy`**:guided 模式下选 5-10 个重点节点的依据。

| 策略 | 选节点依据 |
|---|---|
| `centrality`(默认) | 在依赖图中入度 + 出度排名前 N |
| `frequency` | 在用户材料中被提及次数 ≥ 阈值(仅 material_first / hybrid) |
| `mixed` | 两种各取一半 |

---

## 6. 完整示例

### 6.1 `topic_only` × `skim`(最简)

```json
{
  "course_topic": "大学英语",
  "material_files": [],
  "context": {},
  "preferences": {}
}
```

→ build_plan: mode=topic_only,depth=[skim]

### 6.2 `topic_only` × `skim + guided`(对应 fixture topic-with-focus-cet)

```json
{
  "course_topic": "大学英语",
  "material_files": [],
  "context": {
    "focus_topics": ["语法", "写作"],
    "learning_goal": "6 个月内通过 CET-4",
    "user_level": "intermediate"
  },
  "preferences": {
    "language": "zh",
    "depth_hint": "auto",
    "concept_dependency_strategy": "off",
    "importance_strategy": "centrality"
  }
}
```

→ build_plan: mode=topic_only,depth=[skim, guided],guided 选 5-10 个节点

### 6.3 `topic_only` × `skim + guided + deep + 概念依赖`(对应 fixture topic-deep-with-deps-cet)

```json
{
  "course_topic": "大学英语",
  "material_files": [],
  "context": {
    "focus_topics": ["语法"],
    "user_level": "intermediate",
    "deep_explain": true
  },
  "preferences": {
    "depth_hint": "auto",
    "concept_dependency_strategy": "conservative"
  }
}
```

→ build_plan: mode=topic_only,depth=[skim, guided, deep],dep_strategy=conservative

### 6.4 `material_first` × `skim + guided`(对应 fixture material-markdown-ml)

```json
{
  "course_topic": "",
  "material_files": [
    {"path": "/Users/me/notes/ml-notes.md", "type": "markdown", "label": "我的机器学习笔记"}
  ],
  "context": {
    "user_level": "intermediate"
  },
  "preferences": {
    "concept_dependency_strategy": "conservative"
  }
}
```

→ build_plan: mode=material_first,depth=[skim, guided],ngram 校验启用

---

## 7. 错误码(validate_input.py 退出码 2)

| 错误 | 提示 | 修复 |
|---|---|---|
| `course_topic 与 material_files 不可同时为空` | E_INPUT_EMPTY | 至少提供其一 |
| `preferences.depth_hint 非法` | E_INVALID_DEPTH_HINT | 见 §5 取值范围 |
| `preferences.concept_dependency_strategy 非法` | E_INVALID_DEP_STRATEGY | 见 §5 取值范围 |
| `preferences.language 非法` | E_INVALID_LANG | 见 §5(zh/en/bilingual) |
| `context.user_level 非法` | E_INVALID_USER_LEVEL | beginner/intermediate/advanced |
| `context.focus_topics 上限 5,当前 N` | E_FOCUS_OVER_LIMIT | 缩短列表或拆多次调用 |
| `preferences.output_formats 含非法值` | E_INVALID_OUTPUT_FORMAT | 见 §5 |
| `preferences.max_levels 必须是 1-5 整数` | E_INVALID_MAX_LEVELS | 1 ≤ N ≤ 5 |

---

## 8. 与 SKILL.md / `_skill_meta.json` 的对应关系

- 输入 schema 字段 ↔ SKILL.md「输入契约」表(主入口给用户读)
- 取值约束 ↔ `_skill_meta.json.constraints`(机器可读)
- 校验逻辑 ↔ `scripts/validate_input.py`(执行体)
- 错误码 ↔ build_plan.json.errors(下游 LLM 的反馈源)
