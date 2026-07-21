# Input Schema — english-intensive-reader

## 顶层字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `article` | object | ✅ | — | 文章输入对象 |
| `level` | string | ❌ | `"auto"` | 词汇分级档位 |
| `focus` | string | ❌ | `"all"` | 精读侧重点 |
| `wordbook_path` | string | ❌ | `"./wordbook.json"` | 单词本文件路径 |
| `mode` | string | ❌ | `"standard"` | 精读模式：`standard`（直接输出）/ `guided`（四步引导）|
| `output_format` | string | ❌ | `"markdown"` | 笔记输出格式 |
| `sentence_range` | array | ❌ | null（全文） | 指定精读的句子范围，如 `[3, 5, 7]` |

---

## article 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | `"text"` / `"url"` / `"pdf_path"` / `"docx_path"` |
| `content` | string | ✅ | 纯文本内容 / URL / 文件绝对路径 |
| `title` | string | ❌ | 文章标题（可选，用于笔记标题） |
| `source` | string | ❌ | 来源说明（如 "The Economist 2024-03"） |

---

## level 枚举

| 值 | 说明 | 词汇范围 |
|----|------|---------|
| `"auto"` | 自动推断（按词汇密度）| — |
| `"cet4"` | 大学英语四级 | CET4 词表（约 4500 词）|
| `"cet6"` | 大学英语六级 | CET6 词表（约 6000 词）|
| `"kaoyan"` | 考研英语 | 考研词表（约 5500 词）|
| `"foreign_press"` | 外刊（经济学人 / 纽约时报等）| 无上限，标注低频词 |

**auto 推断规则**（按文章词汇密度）：
- CET4 词表外词汇占比 < 5% → `cet4`
- 5% ~ 15% → `cet6`
- 15% ~ 25% → `kaoyan`
- > 25% → `foreign_press`

---

## focus 枚举

| 值 | 说明 | 输出内容 |
|----|------|---------|
| `"all"` | 全部（默认）| `sentence_analysis` + `vocab_notes` + `article_summary` + `key_patterns` |
| `"vocab"` | 侧重词汇 | `vocab_notes` + `article_summary`（跳过 `grammar_tags` 详细标注）|
| `"grammar"` | 侧重语法 | `sentence_analysis`（含 `grammar_tags`）+ `key_patterns`（跳过 `vocab_notes`）|
| `"structure"` | 侧重篇章结构 | `article_summary` + 段落功能标注（跳过逐句语法）|

---

## output_format 枚举

| 值 | 说明 |
|----|------|
| `"markdown"` | Markdown 格式（默认，直接在对话中输出）|
| `"html"` | 双栏 HTML 笔记（写入 `./intensive-reader-output/<timestamp>-note.html`）|
| `"both"` | Markdown + HTML 同时输出 |

---

## 输入示例

### 纯文本输入
```json
{
  "article": {
    "type": "text",
    "content": "Climate change is one of the most pressing issues...",
    "title": "Climate Change Overview",
    "source": "The Economist"
  },
  "level": "cet6",
  "focus": "all"
}
```

### URL 输入
```json
{
  "article": {
    "type": "url",
    "content": "https://www.economist.com/leaders/2024/01/01/example"
  },
  "level": "foreign_press",
  "focus": "grammar"
}
```

### PDF 输入
```json
{
  "article": {
    "type": "pdf_path",
    "content": "/Users/student/reading/article.pdf"
  },
  "level": "kaoyan",
  "focus": "vocab",
  "wordbook_path": "/Users/student/my-wordbook.json"
}
```

### 指定句子范围
```json
{
  "article": {
    "type": "text",
    "content": "..."
  },
  "level": "cet4",
  "sentence_range": [3, 5, 7]
}
```

---

## 输入校验规则

1. `article.type = "url"` 时，`content` 必须以 `http://` 或 `https://` 开头
2. `article.type = "pdf_path"` 或 `"docx_path"` 时，`content` 必须是绝对路径
3. `article.type = "text"` 时，`content` 不得为空字符串
4. 图片路径（`.jpg` / `.png` / `.jpeg`）→ 拒绝，提示「本 Skill 不做 OCR」
5. 文章词数 > 3000 → 提示分段，不自动截断

## 口语化触发映射

用户不一定按 JSON 格式输入，以下口语化表达应正确路由：

| 用户说 | 解析为 |
|--------|--------|
| "帮我精读这篇文章，我在备考六级" | `level=cet6, focus=all` |
| "只看词汇，不用讲语法" | `focus=vocab` |
| "这篇经济学人太难了" | `level=foreign_press` |
| "只分析第 3 句和第 5 句" | `sentence_range=[3,5]` |
| "生成 HTML 笔记" | `output_format=html` |
| "引导我理解这篇文章" | `mode=guided` |
| "一步一步来，帮我深度理解" | `mode=guided` |
| "教我怎么读这篇文章" | `mode=guided` |
