# Wordbook Spec — english-intensive-reader

> 单词本数据契约。`wordbook.json` 是本地持久化的生词本，跨 session 累积，支持 Anki CSV 导出。

---

## 一、wordbook.json 数据结构

```json
{
  "version": "1.0",
  "created_at": "2026-05-07T20:00:00+08:00",
  "updated_at": "2026-05-07T20:30:00+08:00",
  "total_words": 42,
  "words": [
    {
      "id": "w001",
      "word": "pressing",
      "pos": "adj.",
      "definition": "紧迫的，迫切的",
      "collocations": ["pressing issue", "pressing need", "pressing concern"],
      "example": "Climate change is one of the most pressing issues facing humanity today.",
      "example_source": "The Economist - Climate Crisis",
      "level_tag": "foreign_press",
      "added_at": "2026-05-07T20:00:00+08:00",
      "review_count": 0,
      "last_reviewed_at": null,
      "mastered": false,
      "tags": ["外刊", "形容词", "考研高频"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 唯一 ID，格式 `w001` / `w002` ... |
| `word` | string | ✅ | 单词或短语 |
| `pos` | string | ✅ | 词性（`n.` / `v.` / `adj.` / `adv.` / `prep.` / `phr.v.`）|
| `definition` | string | ✅ | 中文释义 |
| `collocations` | array | ✅ | 高频搭配（2~4 个）|
| `example` | string | ✅ | 原文例句（必须来自文章，不编造）|
| `example_source` | string | ✅ | 来源说明（文章标题 / 来源）|
| `level_tag` | string | ✅ | 词汇档位（`cet4` / `cet6` / `kaoyan` / `foreign_press`）|
| `added_at` | string | ✅ | 加入时间（ISO 8601）|
| `review_count` | int | ✅ | 复习次数（初始为 0）|
| `last_reviewed_at` | string/null | ✅ | 最近复习时间（未复习为 null）|
| `mastered` | boolean | ✅ | 是否已掌握（用户手动标记）|
| `tags` | array | ❌ | 用户自定义标签 |

---

## 二、操作命令

### 2.1 添加单词

```bash
python scripts/wordbook_manager.py add \
  --word "pressing" \
  --pos "adj." \
  --definition "紧迫的，迫切的" \
  --collocations "pressing issue,pressing need" \
  --example "Climate change is one of the most pressing issues facing humanity today." \
  --source "The Economist - Climate Crisis" \
  --level "foreign_press" \
  --wordbook "./wordbook.json"
```

**口语化触发**：
- "把 pressing 加入单词本" → 自动从当前 session 的 `vocab_notes` 中提取该词信息
- "把这句话里的生词都加入单词本" → 批量添加当前句的所有 `new_words`

### 2.2 查看单词本

```bash
# 查看全部
python scripts/wordbook_manager.py list --wordbook "./wordbook.json"

# 按档位筛选
python scripts/wordbook_manager.py list --level cet6 --wordbook "./wordbook.json"

# 只看未掌握的
python scripts/wordbook_manager.py list --mastered false --wordbook "./wordbook.json"

# 统计
python scripts/wordbook_manager.py stats --wordbook "./wordbook.json"
```

### 2.3 导出 Anki CSV

```bash
python scripts/wordbook_manager.py export \
  --format anki \
  --output "./wordbook-anki.csv" \
  --wordbook "./wordbook.json"
```

**Anki CSV 格式**（制表符分隔）：
```
Front	Back	Tags
pressing	adj. 紧迫的，迫切的\n搭配：pressing issue / pressing need\n例句：Climate change is one of the most pressing issues facing humanity today.	外刊 foreign_press
```

### 2.4 导出 Markdown 表格

```bash
python scripts/wordbook_manager.py export \
  --format md \
  --output "./wordbook.md" \
  --wordbook "./wordbook.json"
```

**Markdown 格式**：
```markdown
| 单词 | 词性 | 释义 | 搭配 | 例句 | 档位 |
|------|------|------|------|------|------|
| pressing | adj. | 紧迫的 | pressing issue | Climate change... | foreign_press |
```

### 2.5 标记已掌握

```bash
python scripts/wordbook_manager.py mark-mastered \
  --word "pressing" \
  --wordbook "./wordbook.json"
```

### 2.6 删除单词

```bash
python scripts/wordbook_manager.py delete \
  --word "pressing" \
  --wordbook "./wordbook.json"
```

---

## 三、文件路径规则

| 场景 | 默认路径 |
|------|---------|
| 用户未指定 | `./wordbook.json`（当前工作目录）|
| 用户指定 | `wordbook_path` 参数值 |
| 文件不存在 | 自动创建空文件（不报错）|
| 文件损坏 | 报错提示，不覆盖原文件 |

---

## 四、重复词处理

- 同一个词（忽略大小写）已存在 → **不重复添加**，提示「pressing 已在单词本中（加入于 2026-05-07）」
- 用户说"更新这个词的例句" → 覆盖 `example` 字段，保留其他字段
- 同一个词有不同词性（如 press n. / press v.）→ 视为不同词条，分别添加

---

## 五、统计输出格式

```
📚 单词本统计
总词数：42
├── CET4：8 词
├── CET6：15 词
├── 考研：12 词
└── 外刊：7 词

已掌握：18 词（43%）
未复习：24 词
最近添加：pressing（2026-05-07）
```
