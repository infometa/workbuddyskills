# Anti-Hallucination Rules — english-intensive-reader

> 本文件定义防幻觉规则，是 SKILL.md 中 NEVER 列表的详细展开。
> AI 在每次输出前必须对照本文件进行自检。

---

## 一、核心防幻觉原则

**所有标注必须有原文锚点**。英语精读的幻觉风险主要来自三个来源：
1. 编造例句（最高风险）
2. 在 backbone 中添加原文没有的成分
3. 使用原文没有的语法标签

---

## 二、逐条规则

### R1：vocab_notes.example 必须锚定原文

**规则**：`vocab_notes[i].example` 字段的值必须是原文中的真实句子，且必须附 `example_source_id`（对应 `sentence_unit.id`）。

**违规示例**（❌ 禁止）：
```json
{
  "word": "ubiquitous",
  "example": "Smartphones have become ubiquitous in modern society.",
  "example_source_id": null
}
```
> ❌ 这是编造的例句，不是原文中的句子。

**合规示例**（✅ 正确）：
```json
{
  "word": "ubiquitous",
  "example": "The ubiquitous presence of social media has transformed how people communicate.",
  "example_source_id": "s03"
}
```
> ✅ 原文第 3 句中的真实句子，附 sentence_id。

**特殊情况**：如果原文中该词只出现一次，`example` 就是那句话；如果出现多次，取最能体现词义的那句。

---

### R2：sentence_analysis.backbone 必须是原句子集

**规则**：`backbone` 字段的内容必须是原句的子集（可以省略修饰成分，但不能添加原文没有的词）。

**违规示例**（❌ 禁止）：
```
原句：Climate change is one of the most pressing issues facing humanity today.
backbone：Climate change is a pressing issue that humanity faces.
```
> ❌ "that humanity faces" 是改写，不是原文子集。

**合规示例**（✅ 正确）：
```
backbone：Climate change is one of the most pressing issues
```
> ✅ 直接从原句提取主干，保留原文词汇。

---

### R3：grammar_tags 必须来自枚举

**规则**：`grammar_tags` 数组中的每个值必须来自 `grammar-tag-taxonomy.md` 的枚举列表。

**违规示例**（❌ 禁止）：
```json
"grammar_tags": ["高级句型", "复杂从句结构", "书面语表达"]
```
> ❌ 这些不是 `grammar-tag-taxonomy.md` 中的枚举值。

**合规示例**（✅ 正确）：
```json
"grammar_tags": ["让步状语从句", "虚拟语气-与现在事实相反"]
```

---

### R4：生词标注不得跨档位

**规则**：`new_words` 中的词必须确实超出当前 `level` 词表，不得把低档位词汇标为高档位的"生词"。

**违规示例**（❌ 禁止，level=cet4）：
```json
"new_words": ["important", "challenge", "environment"]
```
> ❌ 这些都是 CET4 核心词，不应标为生词。

**违规示例**（❌ 禁止，level=cet6）：
```json
"new_words": ["ability", "achieve", "affect"]
```
> ❌ 这些是 CET4 词，CET6 档位不应标注。

---

### R5：article_summary 不得推断原文没有的信息

**规则**：`article_summary` 中的每句话必须有原文依据，不得推断作者意图或添加原文没有的信息。

**违规示例**（❌ 禁止）：
```
"作者认为政府应该立即采取行动，否则后果不堪设想。"
```
> ❌ 如果原文没有明确表达这个观点，不得在摘要中出现。

**合规示例**（✅ 正确）：
```
"文章指出，政府在气候政策上的行动速度远落后于科学界的建议。"
```
> ✅ 基于原文内容的客观描述。

---

### R6：URL 抓取失败时不猜测内容

**规则**：当 `article.type = "url"` 且抓取失败时，必须报错退出，不得根据 URL 猜测文章内容。

**违规行为**（❌ 禁止）：
```
URL 抓取失败，但根据 URL 路径推测这是一篇关于气候变化的文章，
以下是可能的分析...
```

**合规行为**（✅ 正确）：
```
❌ 无法抓取该 URL（可能原因：反爬限制 / 需要登录 / 网络问题）。
请复制文章文本后粘贴，我来帮你精读。
```

---

### R7：key_patterns.example 必须来自原文

**规则**：`key_patterns[i].example` 必须是原文中的真实句子，附 `source_id`。

**违规示例**（❌ 禁止）：
```json
{
  "pattern": "让步状语从句",
  "example": "Although it is difficult, we should try our best.",
  "source_id": null
}
```
> ❌ 这是编造的例句。

**合规示例**（✅ 正确）：
```json
{
  "pattern": "让步状语从句",
  "example": "Although the costs are substantial, the long-term benefits justify the investment.",
  "source_id": "s07"
}
```

---

### R8：collocations 必须是真实高频搭配

**规则**：`vocab_notes[i].collocations` 中的搭配必须是真实存在的高频搭配，不得编造。

**违规示例**（❌ 禁止）：
```json
"collocations": ["pressing solution", "pressing answer", "pressing response"]
```
> ❌ 这些不是 pressing 的真实搭配。

**合规示例**（✅ 正确）：
```json
"collocations": ["pressing issue", "pressing need", "pressing concern", "pressing matter"]
```

---

## 三、自检清单（输出前必查）

在输出任何 `sentence_unit` 之前，AI 必须逐项确认：

```
□ vocab_notes[i].example 是否来自原文？是否附 example_source_id？
□ sentence_analysis.backbone 是否是原句的子集？
□ grammar_tags 中的每个值是否在 grammar-tag-taxonomy.md 枚举中？
□ new_words 中的词是否确实超出当前 level 词表？
□ collocations 是否是真实高频搭配？
□ article_summary 中的每句是否有原文依据？
□ key_patterns[i].example 是否来自原文？是否附 source_id？
```

---

## 四、幻觉风险等级

| 字段 | 风险等级 | 说明 |
|------|---------|------|
| `vocab_notes.example` | 🔴 高 | 最容易编造，必须严格锚定 |
| `key_patterns.example` | 🔴 高 | 同上 |
| `sentence_analysis.backbone` | 🟡 中 | 容易添加原文没有的成分 |
| `grammar_tags` | 🟡 中 | 容易使用模糊描述 |
| `article_summary` | 🟡 中 | 容易推断作者意图 |
| `vocab_notes.collocations` | 🟡 中 | 容易编造不存在的搭配 |
| `sentence_analysis.translation` | 🟢 低 | 翻译有一定灵活性，但不得改变原意 |
| `new_words` | 🟢 低 | 按词表标注，风险较低 |
