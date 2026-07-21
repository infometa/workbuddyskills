# PDF 解析启发式

> `scripts/parse_pdf.py` 的实现规范。目标：从 PDF / DOCX / pasted_text 抽出**结构化 `(text, page, section)` 三元组**，
> 支持后续的摘要卡抽取 + 页码级 provenance。

## Contents

- [一、支持的输入源](#一支持的输入源)
- [二、PDF 解析策略](#二pdf-解析策略)
- [三、双栏布局处理](#三双栏布局处理)
- [四、章节切分启发式](#四章节切分启发式)
- [五、arXiv TeX 解析（§11）](#五arxiv-tex-解析11)
- [六、异常处理](#六异常处理)

---

## 一、支持的输入源

| source | 解析路径 | 依赖库 |
|---|---|---|
| `arxiv_url` / `arxiv_id` | **首选 TeX Source**（scripts/fetch_arxiv_tex.py）+ 并行 PDF 做页码映射 | `tarfile` / `urllib`（标准库）|
| `pdf_path` | pdfplumber → text + bbox + page；回退 pymupdf | pdfplumber / pymupdf |
| `docx_path` | python-docx 读段落；页码降级为段落编号 | python-docx |
| `pasted_text` | 按段落切分；页码 = null；追问用户页码上下文 | 无 |
| `image_path` | **拒绝** | — |

> **arXiv TeX 优先**（v0.2.0 新增）：用户输入 arxiv URL / ID 时，**首选** TeX tarball 路径（保留公式、结构、章节名精确）；PDF 并行下载仅用于 `page` 字段映射。完整协议见 [arxiv-fetch-protocol.md](arxiv-fetch-protocol.md)。

**拒绝图像 PDF** 的判定：
```
if page.extract_text() == "" for all pages:
    raise PDF_IMAGE_LAYER_ONLY
```

---

## 二、解析后的核心数据结构

```json
{
  "meta": {
    "title": "Self-Instruct: Aligning LMs with Self-Generated Instructions",
    "authors": ["Y. Wang", "..."],
    "year": 2023,
    "venue": "ACL 2023",
    "total_pages": 14,
    "abstract": "...",
    "source_type": "pdf_path",
    "original_path": "./papers/self-instruct.pdf"
  },
  "sections": [
    { "id": "s-0",  "title": "Abstract",                    "first_page": 1, "last_page": 1 },
    { "id": "s-1",  "title": "1. Introduction",             "first_page": 1, "last_page": 2 },
    { "id": "s-2",  "title": "2. Related Work",             "first_page": 2, "last_page": 3 },
    { "id": "s-3",  "title": "3. Method",                   "first_page": 3, "last_page": 6 },
    { "id": "s-4",  "title": "3.2 Dataset Construction",    "first_page": 5, "last_page": 5 },
    { "id": "s-5",  "title": "3.3 Filtering",               "first_page": 5, "last_page": 5 },
    { "id": "s-6",  "title": "5. Results",                  "first_page": 7, "last_page": 10 },
    { "id": "s-7",  "title": "6. Limitations",              "first_page": 11, "last_page": 11 },
    { "id": "s-8",  "title": "Conclusion",                  "first_page": 11, "last_page": 11 },
    { "id": "s-9",  "title": "References",                  "first_page": 12, "last_page": 14 }
  ],
  "blocks": [
    {
      "block_id": "b-0001",
      "page": 1,
      "section_id": "s-0",
      "section_title": "Abstract",
      "text": "Large \"instruction-tuned\" language models..."
    },
    {
      "block_id": "b-0002",
      "page": 5,
      "section_id": "s-4",
      "section_title": "3.2 Dataset Construction",
      "text": "We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples..."
    }
  ],
  "figures_and_tables": [
    { "type": "figure", "id": "fig-1", "page": 2, "caption": "Overview of Self-Instruct..." },
    { "type": "table",  "id": "tab-2", "page": 8, "caption": "Main Results on SuperNI..." }
  ]
}
```

---

## 三、章节识别启发式

### 3.1 双栏 vs 单栏

- **v0.1 POC 当前实现**：统一按页提取（`page.extract_text(x_tolerance=1.5, y_tolerance=3)`）
  - `x_tolerance=1.5` 修复 LaTeX / pdfTeX 生成 PDF 的"词间距为 0"问题（ACL / NeurIPS / arxiv 常见）
  - **已知局限**：双栏布局下左右列会交错（行级 y 坐标接近时 pdfplumber 按 x 升序读）
    - 影响：长句跨列时 ngram 匹配率下降
    - 表现：某些 claim 会被标为 `hallucination_risk: medium/high` 即使实际在原文中存在
- **v0.2 规划**：按 bbox 列聚类 → 左列全读完再读右列（pdfplumber 的 `.within_bbox` 可实现）

### 3.2 章节标题识别（优先级）

1. **字号差异**：section title 通常比正文大 1–3pt（字号排序前 10%）
2. **编号前缀**：`"^\d+\.\s"` / `"^\d+\.\d+\s"` / `"^[A-Z]+\.\s"`
3. **关键词**：`Abstract / Introduction / Related Work / Method / Experiments / Results / Discussion / Conclusion / Limitations / References / Appendix`
4. **单行独立**：整行文字 + 下文空行 → 可能是标题

### 3.3 特殊处理

| 情况 | 处理 |
|---|---|
| 无明显章节（如 ArXiv preprint 单栏）| 按页回退：section_title = `"Page N"` |
| LaTeX workshop paper 无编号 | 按关键词匹配（Abstract / Intro / Method …）|
| 非英文论文（中文 / 日文） | 按中日文节号（`一、/ 二、/ 第 1 章`）|

---

## 四、footnote / header / footer 过滤

### 4.1 Header 识别

- 每页**首 2 行**若在多页重复出现（> 3 页相同） → 视为 header，过滤
- 常见 header：论文标题 / 会议信息 / 页眉

### 4.2 Footer 识别

- 每页**末 2 行**：
  - 纯数字 / "Page N of M" → 页码，过滤
  - 作者邮箱 / 会议年份 → 过滤

### 4.3 Footnote 识别

- 以上标数字 `^\d{1,2}` 开头 + 字号比正文小 1–2pt
- 标记为独立 block，`section_id = "footnote"`

---

## 五、References / Bibliography 特殊处理

- References 章节**不拆 block**，整段保留
- 不参与 ngram 索引（摘要卡不需要引用 References 原文）
- 仅用于后续的"引文关联"（v0.3 规划）

---

## 六、Figures / Tables 处理

### 6.1 Caption 抽取

- "^Figure\s+\d+" / "^Fig\.\s+\d+" / "^Table\s+\d+" 开头的段落
- 取到下一个空行或下一个大字号段为止
- 存入 `figures_and_tables` 数组

### 6.2 不做的事

- **不做**图表内容提取（图像解析）
- **不做**表格数据重构（后续 v0.3 可能做 Camelot 集成）
- Caption **参与** ngram 索引（用户问"Figure 1 显示了什么"时需要）

---

## 七、语言检测

```python
# 简单启发：前 500 字中 CJK 字符占比 > 50% → zh
cjk_count = sum(1 for c in sample_text if '\u4e00' <= c <= '\u9fff')
lang = "zh" if cjk_count / len(sample_text) > 0.5 else "en"
```

- 用于 `warnings` 中判断 `MIXED_LANGUAGES`
- 多篇对比时，若语言不一致 → warning（不阻断）

---

## 八、`pasted_text` 模式特殊规则

### 8.1 输入要求

用户粘贴的文本：
- 必须 ≥ 200 字
- 建议用户提供论文元数据（title / authors / year）

### 8.2 处理流程

1. 按空行分段 → 每段一个 block
2. `page = null`（无法追溯）
3. `section_id` 按 "段落 N" 编号
4. **追问用户**：
   - "这段文字来自论文的哪一部分？（Abstract / Method / Results / …）"
   - "论文标题是什么？有完整 PDF 路径吗？"
5. 精读模式下，`original_excerpts[*].page` 设为 `null`，但 `text` 仍做 ngram 校验

---

## 九、错误处理与退出码

| 错误 | 退出码 | 处理 |
|---|:---:|---|
| 文件不存在 | 1 | 错误消息 → stderr |
| PDF 加密 | 2 | 提示用户解密后重试 |
| PDF 无文本层（图像）| 3 | 返回 `PDF_IMAGE_LAYER_ONLY` |
| 超过 50 页 | 0 | 正常解析但加 `PAPER_TOO_LONG` warning |
| 超过 100 页 | 0 | 解析但仅保留 Abstract / Intro / Method / Conclusion / Limitations |
| docx 损坏 | 2 | 提示用户另存为或转 PDF |

---

## 十、性能目标（v0.1 POC）

| 论文规模 | 目标时间（本地 macOS）|
|---|---|
| 10 页以内 | < 3s |
| 10–30 页 | < 10s |
| 30–50 页 | < 30s |
| > 50 页 | 警告用户并截断 |

---

## 十一、arXiv TeX 路径细节（v0.2.0 吸收）

当 `source.kind in {arxiv_url, arxiv_id}` 时走本节流程，**替代**单纯的 PDF 解析：

### 11.1 双轨并行

```
fetch_arxiv_tex.py {input}
  ├─ 下载 src.tar.gz → 解压 → 定位 main.tex → 递归 \input/\include
  └─ 并行下载 source.pdf → parse_pdf.py 得到每 block 的页码
```

### 11.2 TeX → blocks 映射

| LaTeX 结构 | 对应 `sections[*].title` |
|---|---|
| `\section{Introduction}` | `"1. Introduction"`（序号按出现次序自动递增）|
| `\subsection{Dataset Construction}` | `"3.2 Dataset Construction"` |
| `\begin{abstract} ... \end{abstract}` | `"Abstract"` |
| `\section*{References}` | `"References"`（标记不参与 ngram 索引）|

### 11.3 公式处理

- 行内公式 `$...$` → 保留原 LaTeX 文本（不渲染）
- 行间公式 `\begin{equation} ... \end{equation}` / `\[...\]` → 作为独立 block，`section_id` 同上下文
- **这些公式参与 ngram 校验**（防止 provenance 丢失数学表达）

### 11.4 页码回填策略

对 TeX 抽出的每个 block：
1. 取其前 80 字符（去除 LaTeX 命令后）作为 ngram 种子
2. 在 PDF blocks 中做 ngram 匹配（3-gram + 5-gram 双粒度，见 `provenance-rules.md`）
3. `confidence ≥ 0.7` → 填 `page`；否则 `page = null` 并在 warnings 添加 `TEX_PDF_MAP_LOW_CONFIDENCE`

### 11.5 降级

| 情况 | 处理 |
|---|---|
| `fetch_arxiv_tex.py` 失败 | 完全回退到 `parse_pdf.py`，警告 `ARXIV_TEX_FETCH_FAILED` |
| TeX 成功但 PDF 失败 | 继续 TeX 路径，所有 `page = null`，warning `PDF_MAP_UNAVAILABLE` |
| 入口文件找不到（`ARXIV_TEX_ENTRY_NOT_FOUND`）| 回退 PDF 路径 |

---

## 十二、常见错误（NEVER）

- **NEVER** 对图像 PDF 调 OCR（本 Skill 明确拒绝，强制用户转文本层）
- **NEVER** 忽略双栏布局导致左右列串行（产生错乱段落）
- **NEVER** 把 References / Acknowledgments 混入摘要卡抽取的语料
- **NEVER** 把 footnote 当作正文（会污染 section 识别）
- **NEVER** 对超过 100 页的文档做全量解析（速度慢且价值低，截断核心章节）
- **NEVER** 让 `page` 字段超出 `total_pages` 范围
- **NEVER** 对 arxiv 输入直接走 `parse_pdf.py`（会丢失公式 + 双栏错乱；应走 `fetch_arxiv_tex.py`）
- **NEVER** 把 TeX 路径下的 `page = null` 当作错误报 —— 这是 PDF 映射失败的正常降级，只警告不阻断
