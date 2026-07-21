# 双栏对照导出模块

把三步翻译的结果导出为 5 种格式：三档对照 / 双栏 Markdown / 双栏 LaTeX / 双栏 HTML / self-check 报告。

> 输出契约：`english_tex` / `bilingual_tex` / `self_check_summary` 三类产物，Markdown-first 设计，单文件 HTML 报告。

## 输出目录结构

```
translation-output/
└── 20260427-165500-arxiv-2206.04655/
    ├── 01-step1-literal.md          # Step 1 直译
    ├── 02-step2-academic.md         # Step 2 学术规范
    ├── 03-step3-polished.md         # Step 3 信达雅终稿（默认主推荐）
    ├── 04-bilingual.md              # 中英双栏（左原文 / 右终稿）
    ├── 05-bilingual.tex             # LaTeX 双栏（投稿用，含 xeCJK）
    ├── 06-self-check.md             # 自检报告
    ├── 07-bilingual.html            # 双栏 HTML（浏览器打开即用，含交互）
    └── _meta.json                   # 翻译会话元数据
```

> 用户可在 Preflight P2 选择"标准"或"快速"时，部分文件会跳过生成。

## 文件 01-03 — 三档对照

每档都是按章节切分的 Markdown，结构如下：

```markdown
---
paper_id: arxiv:2206.04655
step: step3_polished
language: zh
generated_at: 2026-04-27T16:55:00Z
---

# 论文标题（译文）

> Provenance: arxiv:2206.04655 · 总段数 47 · 已应用术语库: ml-venues + user-cv-2026

## §1 引言

> page 1 · §1 Introduction · 段落 §1-p1

我们提出一种新颖的...

## §2 相关工作
...
```

模板见 [../assets/templates/three-tier-output.md](../assets/templates/three-tier-output.md)。

## 文件 04 — 双栏 Markdown

```markdown
| 原文 | 译文 |
|---|---|
| We propose a novel framework that... | 我们提出一种新颖的框架，... |
| The model achieves 94.3% accuracy on ImageNet. | 该模型在 ImageNet 上达到了 94.3% 的准确率。 |
```

模板见 [../assets/templates/bilingual-markdown.md](../assets/templates/bilingual-markdown.md)。

### 表格在双栏 Markdown 中的渲染（关键 — 防表格丢失）

> 高频踩坑：原文里的真实表格（如 `Table 3: 模型性能对比`）若直接塞进双栏的 `| 原文 | 译文 |` 里，会被 GitHub Markdown 解析器拆掉，**用户打开后看到的就是"表格不见了"**。

**正确做法**：把每张表（占位符 `<MDTABLE_n>`）从双栏对照表中**剥离出来**，单独成一组"原表保留 + caption 双语"块：

```markdown
## §4 Experiments · 实验

> page 5 · §4 Experiments

| 原文 | 译文 |
|---|---|
| We evaluate our model on three benchmarks. | 我们在三个基准上评估了模型。 |
| Results are summarized in <MDTABLE_1>. | 结果汇总于 <MDTABLE_1>。 |

<!-- 表 1 占位符还原区（不进双栏，原表一字不改） -->

**Table 1 · 表 1 — 三个基准上的性能对比**

| Model | ImageNet | COCO | GLUE |
|---|---:|---:|---:|
| BERT | 89.5 | 75.2 | 84.1 |
| Ours | **92.1** | **78.4** | **86.7** |

> caption 译文：表 1 — 我们的方法在三个基准上的性能对比，加粗为最佳。
```

**关键约束**：
- 双栏对照行内的 `<MDTABLE_n>` **占位符不还原**（保留为占位符 token），便于读者跳到下方表格区
- 表格本体在还原区**一字不改**（包括表头英文、数字、加粗 markdown）
- 仅 caption 走三步翻译（caption 段单独成一个 segment，与表格 segment 不混）

### 04 中其他保留 token 的处理

| Token 类 | 双栏内显示 | 还原区显示 |
|---|---|---|
| `<MDTABLE_n>` | 保留占位符 token | 表格本体（一字不改）+ caption 双语 |
| `<CODEBLOCK_n>` | 保留占位符 token | 代码块本体（一字不改） |
| `<FIGURE_n>` / `<TABLE_n>`（LaTeX）| 保留占位符 token | LaTeX 块本体 |
| `<INLINE_MATH_n>` / `<CITE_n>` / `<REF_n>` | **直接还原**（短不影响双栏对齐） | — |

## 文件 05 — 双栏 LaTeX

`bilingual_tex` 输出契约：

```latex
\documentclass[twocolumn,11pt]{article}
\usepackage{xeCJK}
\setCJKmainfont{STSong}
\usepackage{paracol}

\begin{document}
\begin{paracol}{2}
% 左栏 — 原文
\section{Introduction}
We propose a novel framework that...
\switchcolumn
% 右栏 — 译文
\section{引言}
我们提出一种新颖的框架，...
\end{paracol}
\end{document}
```

详见 [../assets/templates/bilingual-latex.tex](../assets/templates/bilingual-latex.tex)。

> ⚠️ **MUST**：LaTeX 双栏中的所有 `\cite{}` `\ref{}` `$...$` 必须与原文一字不差（用 `scripts/preserve_latex.py --verify` 校验）。

## 文件 07 — 双栏 HTML（浏览器打开即用）

> ⚠️ **必出强约束**：standard / full 模式下 **`07-bilingual.html` 必须生成**。模型常误以为"产出 Markdown 就够了"——这是错误的。HTML 是默认主交付物（公式渲染 + 视图切换 + 段落复制 + **表格原样渲染**）。生成失败时必须在 `06-self-check.md` 顶部明示，不允许沉默。

为了让译稿能直接发给同事审阅、嵌入到知识库网页或团队 Wiki，本模块产出一个**单文件 HTML**——零外部依赖（仅 MathJax 通过 CDN，可离线时切换为本地路径），双击即可在任何现代浏览器中打开。

### 渲染特性

| 特性 | 说明 |
|---|---|
| **响应式双栏** | ≥ 960px 显示左原文 / 右译文；< 960px 自动堆叠为上下双栏，手机也能读 |
| **公式渲染（KaTeX + MathJax 双引擎）** | 行内 `$...$` 与行间 `$$...$$` / `\[...\]` 自动渲染——**KaTeX 首选**（速度快 5-10×，对未配对 `$` 报错醒目），MathJax v3 兜底（CDN 不可达时启用） |
| **占位高亮** | `\cite{xxx}`、`\ref{xxx}`、`\eqref{xxx}` 在双栏中以醒目 token（黄底）展示，便于审阅是否对齐；可一键切换关闭（`.tok` / `.katex` 类已加入引擎 ignore 列表，不会被误吞） |
| **表格原样渲染** | `<MDTABLE_n>` / LaTeX `\begin{table}` 还原后渲染为 HTML `<table>`，**表头/数据一字不改**；caption 在 `<caption>` 中以"原文 / 译文"双语展示 |
| **章节侧栏** | 自动从章节生成左侧目录树 + 滚动联动 active 高亮（IntersectionObserver） |
| **视图切换** | 顶部按钮一键切换「双栏 / 仅原文 / 仅译文」，精读单侧时不被另一栏分散注意力 |
| **段落复制** | 鼠标悬停段落右上角出现"复制译文"按钮，一键 `navigator.clipboard.writeText` |
| **字号档位** | 顶部 小 / 中 / 大 三档切换，长论文阅读不累 |
| **关联跳转** | 页脚提供到 01-06 文件的相对链接，方便在同一目录内来回看 |

### 模板占位符约定

模板文件 [../assets/templates/bilingual-html.html](../assets/templates/bilingual-html.html) 使用两套占位符语法：

1. **简单替换**：`{{KEY}}` 直接 `string.replace`
2. **块循环**：`<!--BEGIN_TOC-->...<!--END_TOC-->` / `<!--BEGIN_CHAPTER-->...<!--END_CHAPTER-->` / `<!--BEGIN_SEG-->...<!--END_SEG-->` 标记的区域按章节 / 段落多次实例化

| 占位符 | 类型 | 含义 | 示例 |
|---|---|---|---|
| `{{PAPER_TITLE}}` | 简单 | 论文标题（取第一档译文的 H1） | "Attention Is All You Need" |
| `{{PAPER_ID}}` | 简单 | 论文 ID（arxiv / DOI / 用户提供） | "arxiv:1706.03762" |
| `{{PAPER_AUTHORS}}` | 简单 | 作者列表 | "Vaswani et al., 2017" |
| `{{DIRECTION}}` | 简单 | 简短方向标签 | "EN→ZH" |
| `{{DIRECTION_FULL}}` | 简单 | 完整方向描述 | "英 → 中" |
| `{{DEPTH}}` | 简单 | 简短深度标签 | "full" |
| `{{DEPTH_FULL}}` | 简单 | 完整深度描述 | "精翻（信达雅终稿）" |
| `{{GENERATED_AT}}` | 简单 | ISO 时间戳 | "2026-04-27T16:55:00Z" |
| `{{SKILL_VERSION}}` | 简单 | 本 skill 版本 | "1.1.0" |
| `{{SEGMENTS_COUNT}}` | 简单 | 总段数 | 47 |
| `{{GLOSSARY_LIST}}` | 简单 | 已应用术语库（逗号连接） | "ml-venues, user-cv-2026" |
| `{{FORMULA_RATE}}` / `{{CITE_RATE}}` / `{{TERMS_HIT_RATE}}` | 简单 | 来自 `_meta.json.stats` | "100% / 100% / 95.8%" |
| `{{CHAPTER_ID}}` / `{{CHAPTER_LABEL}}` | TOC 块 | 侧栏目录条目 | "ch-1" / "§1 Introduction" |
| `{{CHAPTER_TITLE_SRC}}` / `{{CHAPTER_TITLE_TGT}}` | CHAPTER 块 | 章节标题双语 | "Introduction" / "引言" |
| `{{CHAPTER_PAGE}}` / `{{CHAPTER_SECTION}}` | CHAPTER 块 | Provenance：页码 + 章节号 | "1" / "1" |
| `{{SEG_ID}}` | SEG 块 | 段落锚点 ID（与 Provenance 的 segment_id 一致） | "seg-1-p1" |
| `{{SRC_LANG}}` / `{{TGT_LANG}}` | SEG 块 | 语言标签 | "EN" / "ZH" |
| `{{SEG_SRC_HTML}}` / `{{SEG_TGT_HTML}}` | SEG 块 | 段落 HTML 内容（已转义 + 占位 token 化） | 见下文 |

### `{{SEG_SRC_HTML}}` / `{{SEG_TGT_HTML}}` 渲染规则

把 Markdown 段落转为 HTML 时**必须**遵守以下顺序，否则公式 / 引用 / 表格会被破坏：

0. **裸下标 LaTeX 化（关键 — 防 `<sub>` 硬拼丑陋渲染）**：扫描段落中**未被 `$...$` 包裹**的下标变量名 / 上标符号。识别启发式（按命中即转换）：
   - 字符级模式：`y_{it}` / `Post_{h(t)}` / `\beta_1` / `R^2` / `x^{(i)}` —— 凡含 `_{...}` 或 `^{...}` 或下划线后跟单字母/单数字（`y_i`、`x_t`、`H_0`）的，整段表达式自动用 `$...$` 包裹
   - 词级模式：单字母 + 数字下标（`y1`、`X2`）若紧邻数学语境词（β、α、∑、∏、模型/方程/系数），视为变量名转 `$y_1$`
   - 上下文豁免：在 `<table>` 数据单元格里的纯字母+数字组合（如型号 `GPT4`）不转，仅 caption / 行头 / 正文转
   - **底线**：转换后若 `$` 数量奇偶性变化（出现未配对 `$`），整体回退本段不转，并在 06-self-check 标 `inline_math_skipped` 让用户人工确认——KaTeX `throwOnError:false` 模式下未配对 `$` 不会崩页面但会原样显示
1. **抽公式**：先用正则把 `$...$` / `\[...\]` / `$$...$$` / `\begin{equation}...\end{equation}` 抽成占位符 `__FORMULA_{n}__`，原样保留交给 KaTeX/MathJax 渲染
2. **抽引用**：把 `\cite{xxx}` / `\ref{xxx}` / `\eqref{xxx}` / `\autoref{xxx}` 包成 `<span class="tok">\cite{xxx}</span>`（CSS 类 `.tok` 提供高亮，已加入 KaTeX/MathJax ignore 列表）
3. **抽表格**：识别 `<MDTABLE_n>` / `\begin{table}` 占位符，**整体替换为独立的 `<table>` 块**——不放在双栏对照行内，而是作为段落级单元独立渲染（`class="mdtable-block"`），caption 双语展示。**表格行头变量名也走步骤 0 的 LaTeX 化**（如行头 `y_it` → `$y_{it}$`）
4. **HTML 转义**：对剩余文本做 `<` `>` `&` 转义（避免破坏页面结构）。**严禁**在此步骤把变量下标渲染为 `<sub>` / `<sup>` 标签——所有下标必须已在步骤 0 转为 LaTeX
5. **回填公式**：把 `__FORMULA_{n}__` 替换回原始 LaTeX 字符串（KaTeX/MathJax 会负责渲染）
6. **段落换行**：单段内的换行转 `<br>`，跨段则在 CHAPTER 块外层用多个 SEG 实例

> ⚠️ **绝对禁令**：HTML 输出阶段**不允许**用 `<sub>` / `<sup>` / `<i>` / `<em>` 拼出数学下标或变量名。例如 `y<sub>it</sub> = β·Post<sub>h(t)</sub>` 是**反面教材**——必须写成 `$y_{it} = \beta \cdot Post_{h(t)}$`，由 KaTeX 渲染。理由：① 视觉粗陋（默认下标偏小且字体不匹配）；② 与 Markdown / LaTeX 输出文件不一致（02-step2-academic.md 用 `$...$`，07 用 `<sub>` 会破坏 Markdown ↔ HTML 字符级一致性原则）；③ 不可复制为可粘贴的 LaTeX 源码。

**表格 HTML 模板片段**（`mdtable-block`）：

```html
<figure class="mdtable-block" id="table-{{TABLE_N}}">
  <table>
    <caption>
      <span class="cap-en">Table {{N}}: {{CAPTION_EN}}</span>
      <span class="cap-zh">表 {{N}}：{{CAPTION_ZH}}</span>
    </caption>
    <thead>{{TABLE_HEAD_HTML}}</thead>
    <tbody>{{TABLE_BODY_HTML}}</tbody>
  </table>
</figure>
```

**关键约束**：`{{TABLE_HEAD_HTML}}` / `{{TABLE_BODY_HTML}}` 来自原表的**逐字符 Markdown→HTML 转换**，不经过翻译模型。caption 双语来自专门的 caption segment（已走完三步翻译）。

> ⚠️ **MUST**：HTML 输出前要跑 `scripts/preserve_latex.py --verify --html {output}/07-bilingual.html`，确保公式 / cite token / **表格行数列数**与原文计数一致。任何丢失都视为生成失败，回退到 Step 2。
>
> ⚠️ **ADDITIONAL CHECK**：脚本同时扫描生成的 HTML，若 `<body>` 内出现 `<sub>` / `<sup>` 标签 **且**所在段落不在 `<pre>` / `<code>` / `<table>` 数据单元格内，视为"裸下标硬拼"违规——阻断输出，回退到 SEG_HTML 渲染步骤 0 重做"裸下标 LaTeX 化"。例外：用户原文 Markdown 里就显式写了 `<sub>` HTML 标签（极少见，识别为"作者强意图"）则保留。

### 与 04-bilingual.md 的关系

| 维度 | 04-bilingual.md | 07-bilingual.html |
|---|---|---|
| **数据源** | 同一份 step3_polished + 原文段落对齐 | 同上（同一份 _meta.json 驱动） |
| **公式渲染** | 不渲染（GitHub 端按 Markdown 显示，但 `$...$` / `$$...$$` 在 Typora/VS Code 预览中可正确渲染） | KaTeX 首选 + MathJax 兜底，行内 `$...$` 与行间 `$$...$$` 字符级一致 |
| **交互** | 无 | 视图切换 / 字号 / 复制 / 锚点 |
| **可再编辑** | 是（直接编辑 Markdown） | 否（只读交付物，要改去改 Markdown 重新生成） |
| **适用场景** | 二次编辑 / 同事 PR review / 生成 LaTeX | 在线分享 / 嵌入 Wiki / 离线浏览器读 |

两份文件**互不替代**，任何精翻调用默认都生成。

### 模式裁剪

| 模式 | 是否生成 07-bilingual.html |
|---|---|
| `quick`（仅 Step 1） | ❌ 不生成（直译稿不适合做最终交付） |
| `standard`（Step 1+2） | ✅ **必出**，顶栏 `{{DEPTH_FULL}}` 标为 "学术规范版（未雅化）" |
| `full`（Step 1+2+3） | ✅ **必出**（默认推荐主交付物） |

**沉默跳过 07 = 输出失败**：哪怕模型自认为"用户没明说要 HTML"，只要在 standard / full 模式下，07 必须存在。除非用户在 P2 后**显式追问"只要 Markdown，不要 HTML"**——此时记入 `_meta.json.config.skip_html=true` 后才允许跳过。

### 离线 / 内网部署

默认 KaTeX + MathJax 双引擎走 jsDelivr CDN。当用户在内网或离线场景使用时，把 `<script src="...">` 与 `<link href="...">` 路径改为本地相对路径即可：

```html
<!-- KaTeX 离线版（推荐，体积小） -->
<link rel="stylesheet" href="./assets/katex/katex.min.css" />
<script defer src="./assets/katex/katex.min.js"></script>
<script defer src="./assets/katex/auto-render.min.js" onload="renderMathInElement(document.body)"></script>

<!-- MathJax 离线版（兜底） -->
<script id="MathJax-script" async src="./assets/mathjax/tex-mml-chtml.js"></script>
```

> 当用户在 Preflight P2 后追问"能不能离线"时，按需在 `output_dir/assets/mathjax/` 下放一份 MathJax 静态文件并改 src。这是按需扩展，不是默认行为。

## 文件 06 — Self-Check 报告

`self_check_summary` 契约，扩展为 8 维度：

```markdown
# 翻译自检报告

## 整体指标

| 维度 | 数值 | 阈值 | 状态 |
|---|---:|---:|:-:|
| 总段数 | 47 | — | — |
| Step 1 成功率 | 47/47 (100%) | ≥ 95% | ✅ |
| Step 2 成功率 | 47/47 (100%) | ≥ 95% | ✅ |
| Step 3 成功率 | 46/47 (97.9%) | ≥ 90% | ✅ |
| 公式保留率 | 113/113 (100%) | 100% | ✅ |
| 引用保留率 | 89/89 (100%) | 100% | ✅ |
| 数字保留率 | 41/41 (100%) | 100% | ✅ |
| 术语一致性 | 23/24 唯一术语 全文统一 | ≥ 95% | ✅ |
| Provenance 完整性 | 47/47 段含三维 Provenance | 100% | ✅ |

## 应用的术语库

| 术语 | 译法 | 来源 | 命中次数 |
|---|---|---|---:|
| embedding | 嵌入 | glossary/ml-venues.md | 18 |
| backbone | 骨干网络 | glossary/cv-venues.md | 7 |
| ... | ... | ... | ... |

## 异常段落（需人工复核）

| 段落 | 章节 | 问题 | 建议 |
|---|---|---|---|
| §3.2-p4 | Method | Step 3 触发"length_reasonable"失败，已回退到 Step 2 | 人工审核此段，可能是过度雅化 |

## Step 1 → Step 3 修改样例（前 3 个）

### 样例 1（§1-p1，Chinglish 校正）

| Step | 文本 |
|---|---|
| Step 1 | "在最近几年里，深度学习取得了重要的进展" |
| Step 2 | "近年来，深度学习取得了重要进展" |
| Step 3 | "近年来，深度学习取得了显著进展" |

差异：Step 1→2 删冗，Step 2→3 词汇升档（重要 → 显著）。

## 推荐人工复核重点

1. §3.2-p4（length_reasonable 失败段落）
2. 全文 6 处术语库未覆盖的概念，已用"原文（暂译）"格式标注
3. Abstract / Conclusion 两段建议二次精读，因这两段对投稿影响最大
```

详见 [../assets/templates/self-check-report.md](../assets/templates/self-check-report.md)（按需创建）。

## _meta.json — 会话元数据

```json
{
  "session_id": "20260427-165500-arxiv-2206.04655",
  "skill_version": "0.1.0",
  "input": {
    "type": "arxiv",
    "id": "2206.04655",
    "language_detected": "en"
  },
  "config": {
    "direction": "en2zh",
    "depth": "polished",
    "glossary": ["builtin:ml-venues", "user:cv-2026.yaml"]
  },
  "stats": {
    "total_segments": 47,
    "step1_success": 47,
    "step2_success": 47,
    "step3_success": 46,
    "preservation": {
      "formulas": [113, 113],
      "citations": [89, 89],
      "numbers": [41, 41]
    }
  },
  "outputs": [
    "01-step1-literal.md",
    "02-step2-academic.md",
    "03-step3-polished.md",
    "04-bilingual.md",
    "05-bilingual.tex",
    "06-self-check.md",
    "07-bilingual.html"
  ]
}
```
