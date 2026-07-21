# outline-parsing-heuristics.md —— Step 2 材料骨架解析启发式规则

> v0.5.0 ﹒ 适用于 `scripts/parse_outline.py`,**不构建知识树**——只输出扁平 headings 流。
> LLM 在 Step 3/4 据此重组 framework_tree(允许合并 / 重排 / 重命名 / 引入概括节点)。

---

## 1. 总体策略

| 输入类型 | 解析路径 | 字符上限 | 备注 |
|---|---|---:|---|
| `markdown` | ATX `#` + Setext `===` / `---` | 200,000 | 跳过 fenced / indented code block |
| `docx` | zipfile + xml.etree 提取 `pStyle.val == Heading[1-5]` | 5,000 段落 | 零外部依赖,降级处理 |
| `txt` | 多套启发式回退,见 §3 | 100,000 | 短句优先,长句过滤 |
| `pasted_text` | 复用 txt 启发式,内容来自 `content_inline` | 100,000 | 不读文件,直接走内存 |
| `pdf` / `image` / `webpage_url` / `video_url` / `audio_path` | **直接拒绝** | — | OCR 不可靠 + 非主题数据 |

**level 上限 = 5**,超过的标题被压回 level 5 + 加 warning。
**全部 headings 上限 = 1000 条**,超过截断 + warning「建议拆课」。

---

## 2. Markdown 解析(零歧义)

### 2.1 ATX 风格

```regex
^(#{1,6})\s+(.+?)\s*#*\s*$
```

- `# 标题` → level 1
- `## 标题` → level 2
- `### 标题` → level 3
- `#` 数量 = level,**# 数量超过 5 → 压回 level 5 + warning**
- 行尾允许 trailing `#`(GFM 语法,会被剥掉)

### 2.2 Setext 风格

```
线性回归
====

监督学习
----
```

- 上一行 = 标题文本(非空)
- 下一行 = 整行 `=` 或 `-`(至少 2 个)
- `===` → level 1,`---` → level 2

### 2.3 跳过的内容

- **Fenced code block**:` ``` ` 或 `~~~` 包裹的整段
- **Indented code block**:行起头 4 空格 / 1 个 `\t`(简化版,真实 GFM 还需空行触发,这里宽松忽略)

### 2.4 何时识别失败

- 整文 0 个 ATX / Setext → 输出 warning `markdown 未识别到任何标题`,LLM 应改走 txt 启发式或回退 topic_only

---

## 3. txt / pasted_text 启发式(顺序敏感)

> **优先级**:同一行命中多条启发式时,按本节顺序取**第一条命中**——
> 中文章节关键字 > 西文章节关键字 > 数字编号(深→浅) > § 章节符号 > 中文序号 > 字母编号

### 3.1 中文章节关键字(可信度最高)

| 模式 | level | 例 |
|---|---:|---|
| `^第[一二三...\d]+部分` | 1 | 第三部分 |
| `^第[一二三...\d]+[章篇编]` | 1 | 第一章 监督学习 |
| `^第[一二三...\d]+[节回讲课]` | 2 | 第二节 线性回归 |

中文数字字符集:`零一二三四五六七八九十百千万〇○两壹贰叁肆伍陆柒捌玖拾佰仟`

### 3.2 西文章节关键字

| 模式 | level | 例 |
|---|---:|---|
| `^Chapter\s+\d+` | 1 | Chapter 3 Linear Regression |
| `^Section\s+\d+` | 2 | Section 3.1 Loss |

大小写不敏感。

### 3.3 数字编号(深度优先,避免短匹配抢断)

| 模式 | level | 例 |
|---|---:|---|
| `^\d+\.\d+\.\d+\.\d+\s+\S` | 4 | 1.2.3.4 SGD 收敛性 |
| `^\d+\.\d+\.\d+\s+\S` | 3 | 1.2.3 学习率 |
| `^\d+\.\d+\s+\S` 或 `^\d+\.\d+[、.．]\s*\S` | 2 | 1.2 主要范式 / 1.2、主要范式 |
| `^\d+\s*[、.．]\s*\S` | 1 | 1、机器学习 / 1. 机器学习 |

> **注意**:`^\d+\.\s+\S`(level 1)很容易误匹配正文中的「1. 首先...」列表项——`parse_outline.py` 默认仍识别,**LLM 在 Step 3 应据上下文判断是否合并 / 删除疑似误识别的 H1**。

### 3.4 § 章节符号

| 模式 | level | 例 |
|---|---:|---|
| `^§\s*\d+\.\d+\.\d+\s+\S` | 3 | § 3.2.1 |
| `^§\s*\d+\.\d+\s+\S` | 2 | § 3.2 |
| `^§\s*\d+\s+\S` | 1 | § 3 |

### 3.5 中文序号(中等可信度)

| 模式 | level | 例 |
|---|---:|---|
| `^[（(][一二三...]+[）)]\s*\S` | 2 | (一)定义 |
| `^[一二三...]+[、.．]\s*\S`(且整行 ≤ 40 字) | 1 | 一、绪论 |

> 限制为 40 字符的目的:避免误匹配中文正文里的「一、二、」列表项。
> 长句即使匹配模式也忽略,LLM 可在 Step 3 据上下文恢复。

### 3.6 字母编号(最低可信度)

| 模式 | level | 例 |
|---|---:|---|
| `^[A-Z]\.\s+\S` | 2 | A. 监督学习 |

仅大写字母 + `. ` + 文本,避免误匹配「a. b. c.」小写列表。

---

## 4. docx 降级解析(零外部依赖)

不依赖 `python-docx`,直接走标准库 `zipfile + xml.etree`:

1. 用 `zipfile.ZipFile` 打开 docx,读取 `word/document.xml`
2. `ET.fromstring(...)` 解析,namespace `w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`
3. 遍历 `w:body / w:p`,读取 `w:pPr / w:pStyle@w:val`
4. 匹配 `^Heading\s*(\d+)$`(大小写不敏感)→ level
5. 拼接 `.//w:t` 文本节点为标题
6. `char_offset` 在 docx 场景固定 -1(无字符偏移概念,LLM 用 file + line + section 三元组定位)

**降级失败场景**:
- BadZipFile / KeyError(缺 word/document.xml)→ warning + 0 标题
- 用户没用「样式 → 标题 1/2」而是直接加粗大字 → 0 标题 + 提示「请用 Word 内置标题样式」

---

## 5. 标题归一化(所有解析路径共用)

```python
title = unicodedata.normalize("NFC", raw_title)
title = re.sub(r"\s+", " ", title).strip()
```

- 不剥 emoji / 不大小写转换 / 不简繁转换(保留作者风格)
- 长度 > 80 字符 → 截断 `…` + warning(标题不应超 80 字)

---

## 6. 输出 schema(outline.json)

详见 `references/output-schema.md` 末节,核心字段:

```jsonc
{
  "outline_version": "0.5.0",
  "skill_version": "0.5.0",
  "generated_at": "ISO-8601",
  "input_path": "...",
  "files_processed": [
    {
      "file_index": 0,
      "path": "textbook.md",
      "type": "markdown",
      "label": "教材",
      "char_count": 12345,
      "headings_extracted": 23,
      "warnings": []
    }
  ],
  "rejected_files": [
    { "file_index": 1, "path": "scan.pdf", "type": "pdf",
      "reason": "type=pdf 在拒绝列表" }
  ],
  "headings": [
    {
      "file_index": 0,
      "level": 1,
      "title": "机器学习",
      "line": 3,
      "char_offset": 24,
      "method": "markdown_atx",
      "raw": "# 机器学习"
    }
  ],
  "stats": {
    "total_files_accepted": 1,
    "total_files_rejected": 0,
    "total_headings": 23,
    "by_level": {"1": 5, "2": 12, "3": 6},
    "by_method": {"markdown_atx": 23},
    "max_depth": 3,
    "estimated_total_nodes": 24,
    "over_node_limit": false
  },
  "warnings": [],
  "next_step_hint": "..."
}
```

---

## 7. LLM 在 Step 3/4 的使用约定

1. **不必照搬层级**——若解析出 8 层但 SKILL.md 限制 5 层,LLM 应做合并;若解析出 1 层但课程结构应该有 3 层,LLM 应做拆分。
2. **每个最终 framework_tree 节点必须建立 evidence_locator**:
   ```jsonc
   {
     "id": "n2.1",
     "title": "线性回归",
     "evidence_source": "user_material",
     "evidence_locator": {
       "file": "textbook.md",                 // 必须 ∈ files_processed[*].path
       "section": "线性回归",                  // 必须 ∈ headings[*].title 或其前缀
       "excerpt": "线性回归通过最小化均方误差求解最优系数 ..."  // ≥ 8 字符,从原文复制
     }
   }
   ```
3. **excerpt 必须真实出现在原文**——`verify_provenance.py` 会做 3-gram / 5-gram 双层匹配,
   命中率 ≥ 0.85(3-gram)或 ≥ 0.6(5-gram)→ verdict=high。低于 0.3 → failed,LLM 必须重新生成或改 evidence_source = ai_inference。
4. **未在原文出现的"概括节点"**(LLM 自己合并出来的)→ `evidence_source: "ai_inference"`,无需 evidence_locator。

---

## 8. 已知边界 / 已接受的局限

| 局限 | 影响 | 缓解 |
|---|---|---|
| markdown 不识别 HTML `<h1>` 标签 | 极少作者用 inline HTML 标题 | 改用 `#` 重写 |
| txt 启发式可能漏识别(如纯空格缩进结构) | 用户笔记可能识别率低 | 加 # 改用 markdown |
| docx 必须用「样式 → 标题」 | 直接粗体大字会 0 标题 | warning 提示用户 |
| 不支持 reStructuredText / org-mode / asciidoc | 学术写作较少用 | 转 markdown 后再喂 |
| 不识别中英文混排序号(如「1.2 引言 Introduction」第二段语言切换) | 标题正文不冲突 | 已支持 |

不在路线图:
- LaTeX `\section` / `\subsection`(v1.x 视用户呼声)
- HTML 抓取(SKILL.md 已明确不做 OCR / 不抓网页)
- AI 标题识别(违反"零 LLM 调用"的脚本边界)
