# Output Schema — english-intensive-reader

## 顶层结构

```json
{
  "meta": { ... },
  "sentence_units": [ ... ],
  "article_summary": [ ... ],
  "key_patterns": [ ... ]
}
```

---

## meta 对象

```json
{
  "title": "文章标题（无则留空）",
  "source": "来源（如 The Economist）",
  "word_count": 850,
  "sentence_count": 18,
  "level_detected": "cet6",
  "focus": "all",
  "processed_at": "2026-05-07T20:00:00+08:00"
}
```

---

## sentence_unit 对象（核心）

每句话对应一个 `sentence_unit`，是整个 Skill 的最小输出单元。

```json
{
  "id": "s01",
  "raw": "Climate change is one of the most pressing issues facing humanity today.",
  "is_complex": false,
  "highlights": {
    "new_words": ["pressing"],
    "complex_clause_spans": []
  },
  "sentence_analysis": {
    "backbone": "Climate change is one of the most pressing issues",
    "modifiers": [
      {
        "text": "facing humanity today",
        "role": "后置定语",
        "note": "现在分词短语修饰 issues"
      }
    ],
    "grammar_tags": ["现在分词后置定语"],
    "translation": "气候变化是当今人类面临的最紧迫问题之一。"
  },
  "vocab_notes": [
    {
      "word": "pressing",
      "pos": "adj.",
      "definition": "紧迫的，迫切的",
      "collocations": ["pressing issue", "pressing need", "pressing concern"],
      "example": "Climate change is one of the most pressing issues facing humanity today.",
      "example_source_id": "s01",
      "level_tag": "cet6"
    }
  ]
}
```

### sentence_unit 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 句子编号，格式 `s01` / `s02` ... |
| `raw` | string | ✅ | 原句文本，不修改任何字符 |
| `is_complex` | boolean | ✅ | 长难句标记：词数 > 25 或含 ≥ 2 层从句 → `true` |
| `highlights.new_words` | array | ✅ | 按 level 词表标注的生词列表 |
| `highlights.complex_clause_spans` | array | ✅ | 长难句中的从句片段文本（用于下划线渲染）|
| `sentence_analysis.backbone` | string | ✅ | 主干（必须是原句子集，不添加原文没有的成分）|
| `sentence_analysis.modifiers` | array | ✅ | 修饰成分列表（可为空数组）|
| `sentence_analysis.grammar_tags` | array | ✅ | 语法标签（来自 `grammar-tag-taxonomy.md` 枚举）|
| `sentence_analysis.translation` | string | ✅ | 中文翻译 |
| `vocab_notes` | array | ✅ | 生词注释列表（无生词时为空数组）|
| `vocab_notes[i].example` | string | ✅ | **必须从原文取句，附 `example_source_id`，严禁编造** |
| `vocab_notes[i].word_formation` | string | ❌ | 构词法拆解（如 `un- + comfort + -able`），有则填 |
| `vocab_notes[i].context_clues` | object | ❌ | 词义推断线索（见下文），有则填 |

---

## modifier 对象

```json
{
  "text": "修饰成分的原文文本",
  "role": "定语 | 状语 | 同位语 | 插入语 | 表语 | 宾补",
  "note": "可选：补充说明（如「现在分词短语」「由 which 引导的定语从句」）"
}
```

### role 枚举（完整列表）

| 值 | 说明 |
|----|------|
| `"定语"` | 修饰名词（前置或后置）|
| `"状语"` | 修饰动词/形容词/全句 |
| `"同位语"` | 对名词的补充说明 |
| `"插入语"` | 插入句中的补充成分 |
| `"表语"` | 系动词后的成分 |
| `"宾补"` | 宾语补足语 |
| `"主语从句"` | 充当主语的从句 |
| `"宾语从句"` | 充当宾语的从句 |
| `"表语从句"` | 充当表语的从句 |
| `"同位语从句"` | 对名词的从句补充 |

---

## context_clues 对象（词义推断线索）

> 融合自 gaokao-english-tutor 的上下文推断法。当生词可通过上下文线索推断时填写。

```json
{
  "clue_type": "转折 | 因果 | 并列 | 举例 | 解释 | 对比",
  "clue_word": "but",
  "inference": "与前文意思相反，前文说'努力工作'，故此词含义为'不情愿的'"
}
```

| 字段 | 说明 |
|------|------|
| `clue_type` | 线索类型（6 种枚举，来自 `grammar-tag-taxonomy.md` 七类）|
| `clue_word` | 触发推断的标志词（如 but / because / for example）|
| `inference` | 推断过程说明（≤ 30 字）|

---

## rhetoric_tags 数组（修辞标签）

> 融合自 gcse-english-language-tutor 的修辞手法分类体系。
> 仅在 `focus=structure` 或 `level=foreign_press` 时输出；其他情况跳过。

```json
"rhetoric_tags": [
  {
    "tag": "暗喻",
    "span": "the iron curtain of silence",
    "effect": "将沉默比作铁幕，暗示压迫感和不可穿透性"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tag` | string | ✅ | 修辞标签（来自 `grammar-tag-taxonomy.md` 六类枚举）|
| `span` | string | ✅ | 原文中的修辞片段（必须锚定原文）|
| `effect` | string | ✅ | 对读者的效果说明（≤ 30 字，说明 *why*，不只说 *what*）|

---

## upgrade_suggestions 数组（句式升级建议）

> 融合自 gaokao-english-tutor 的句式升级教学法。
> 在 `article_summary` 之后输出，提供 2 条具体的句式升级建议。

```json
"upgrade_suggestions": [
  {
    "original": "The weather was good. We went to the park.",
    "source_id": "s03",
    "upgraded": "The weather being good, we went to the park.",
    "technique": "独立主格结构",
    "note": "用独立主格替代两个简单句，更简洁高级"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `original` | string | ✅ | 原文中相对简单的句子（来自文章，附 `source_id`）|
| `source_id` | string | ✅ | 对应 `sentence_unit.id` |
| `upgraded` | string | ✅ | 升级后的句子（AI 改写，需保持原意）|
| `technique` | string | ✅ | 使用的句式技巧（≤ 15 字）|
| `note` | string | ✅ | 升级说明（≤ 25 字）|

---

## PEAL 段落分析（focus=structure 时输出）

> 融合自 gcse-english-language-tutor 的 PEAL/PETAL 框架。
> 在 `focus=structure` 时，对每个段落额外输出 PEAL 分析。

```json
"paragraph_analysis": [
  {
    "paragraph_id": "p01",
    "sentences": ["s01", "s02", "s03"],
    "function": "引入 | 论证 | 转折 | 举例 | 结论",
    "peal": {
      "point": "段落的核心论点（一句话）",
      "evidence": "支撑论点的关键句（原文引用，附 sentence_id）",
      "analysis": "作者如何通过语言/结构实现这一效果",
      "link": "与全文主旨或上下段的关联"
    }
  }
]
```

---

## article_summary 数组

3~5 个字符串，描述全文脉络：

```json
[
  "文章以气候变化为切入点，指出其已成为全球最紧迫的议题。",
  "作者援引 IPCC 数据，说明全球气温上升的速度超出预期。",
  "文章进一步分析了化石燃料依赖与政策滞后两大核心原因。",
  "转折处提出可再生能源转型的可行路径与成本估算。",
  "结论呼吁各国政府在 2030 年前采取实质性减排行动。"
]
```

**规则**：
- 每句 ≤ 40 字
- 必须基于原文，不推断作者意图（N10）
- 无明显结论时，最后一句描述文章收尾方式

---

## key_patterns 数组

3 个值得背诵的句型：

```json
[
  {
    "pattern": "让步状语从句 + 主句（Although ... , S + V）",
    "example": "Although the costs are high, the long-term benefits outweigh them.",
    "source_id": "s07",
    "why_worth_learning": "议论文让步转折，四六级高频"
  },
  {
    "pattern": "It is ... that 强调句",
    "example": "It is the lack of political will that hinders progress.",
    "source_id": "s12",
    "why_worth_learning": "强调主语，考研写作常用"
  },
  {
    "pattern": "Not only ... but also 并列递进",
    "example": "Not only does this affect the economy, but it also threatens biodiversity.",
    "source_id": "s15",
    "why_worth_learning": "倒装 + 递进，外刊高频结构"
  }
]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pattern` | string | ✅ | 句型名称（≤ 30 字）|
| `example` | string | ✅ | 原文例句（必须来自文章，附 `source_id`）|
| `source_id` | string | ✅ | 对应 `sentence_unit.id`，如 `"s07"` |
| `why_worth_learning` | string | ✅ | 使用场景说明（≤ 20 字）|

---

## Markdown 输出模板

```markdown
# 📖 英语精读笔记
**文章**：{title} | **来源**：{source} | **级别**：{level} | **词数**：{word_count}

---

## 逐句精读

### [s01] {raw}
> 🔑 **主干**：{backbone}
> 📎 **修饰**：{modifiers[0].text}（{modifiers[0].role}）
> 🏷 **语法**：{grammar_tags}
> 🌐 **译文**：{translation}

📚 **生词**：
- **{word}** *{pos}* — {definition}
  - 搭配：{collocations}
  - 例句：_{example}_ `[+单词本]`

---

## 📋 全文脉络
1. {summary[0]}
2. {summary[1]}
...

## ✨ 值得背诵的句型
1. **{pattern}**
   > {example}（来自 {source_id}）
   > 💡 {why_worth_learning}
```

---

## 完整输出示例（单句）

```json
{
  "meta": {
    "title": "The Climate Crisis",
    "source": "The Economist",
    "word_count": 320,
    "sentence_count": 8,
    "level_detected": "foreign_press",
    "focus": "all",
    "processed_at": "2026-05-07T20:00:00+08:00"
  },
  "sentence_units": [
    {
      "id": "s01",
      "raw": "Climate change is one of the most pressing issues facing humanity today.",
      "is_complex": false,
      "highlights": {
        "new_words": ["pressing"],
        "complex_clause_spans": []
      },
      "sentence_analysis": {
        "backbone": "Climate change is one of the most pressing issues",
        "modifiers": [
          {
            "text": "facing humanity today",
            "role": "定语",
            "note": "现在分词短语后置修饰 issues"
          }
        ],
        "grammar_tags": ["现在分词后置定语"],
        "translation": "气候变化是当今人类面临的最紧迫问题之一。"
      },
      "vocab_notes": [
        {
          "word": "pressing",
          "pos": "adj.",
          "definition": "紧迫的，迫切的",
          "collocations": ["pressing issue", "pressing need", "pressing concern"],
          "example": "Climate change is one of the most pressing issues facing humanity today.",
          "example_source_id": "s01",
          "level_tag": "foreign_press"
        }
      ]
    }
  ],
  "article_summary": [
    "文章以气候变化为核心议题，指出其紧迫性已超越以往任何时期。"
  ],
  "key_patterns": [
    {
      "pattern": "现在分词短语后置定语",
      "example": "Climate change is one of the most pressing issues facing humanity today.",
      "source_id": "s01",
      "why_worth_learning": "替代定语从句，简洁高级"
    }
  ]
}
```
