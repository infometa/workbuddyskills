# 公式 / 引用 / 表格 / 数字零损伤规则

> **核心不变量**：从 Step 1 直译到 Step 3 雅化的全过程，公式、引用、`\cite{}`、`\ref{}`、数字、算法块、**表格结构与单元格内容**、数据集名 **一字不改**。

## 必须保留的 Token 清单

下列 Token 在送翻译模型前**必须**用占位符替换，翻译完成后再用 `scripts/preserve_latex.py --restore` 还原：

| # | Token 类 | 正则 | 占位符 | 例 |
|:-:|---|---|---|---|
| 1 | 行内公式 | `\$[^\$]+\$` | `<INLINE_MATH_n>` | `$\mathbf{x}_t = f(\mathbf{x}_{t-1})$` |
| 2 | 显示公式 | `\$\$[^\$]+\$\$` | `<DISPLAY_MATH_n>` | `$$\sum_{i=1}^{n} x_i$$` |
| 3 | equation 块 | `\\begin\{equation\*?\}.*?\\end\{equation\*?\}` | `<EQUATION_n>` | `\begin{equation}...\end{equation}` |
| 4 | align 块 | `\\begin\{align\*?\}.*?\\end\{align\*?\}` | `<ALIGN_n>` | `\begin{align}...\end{align}` |
| 5 | 算法块 | `\\begin\{algorithm\*?\}.*?\\end\{algorithm\*?\}` | `<ALGORITHM_n>` | — |
| 6 | LaTeX 表格块 | `\\begin\{table\*?\}.*?\\end\{table\*?\}` | `<TABLE_n>` | 表格内容不翻译，仅 caption 翻译 |
| 6b | LaTeX `tabular` 块 | `\\begin\{tabular\*?\}.*?\\end\{tabular\*?\}` | `<TABULAR_n>` | 仅本体；caption 与 label 在 `<TABLE_n>` 外 |
| 6c | **Markdown 管道符表格** | 见下文「Markdown 表格识别」 | `<MDTABLE_n>` | **整张表占位，仅 caption 翻译** |
| 7 | LaTeX 图块 | `\\begin\{figure\*?\}.*?\\end\{figure\*?\}` | `<FIGURE_n>` | 同上 |
| 8 | `\cite{}` | `\\cite[tp]?\{[^}]+\}` | `<CITE_n>` | `\cite{vaswani2017attention}` |
| 9 | `\ref{}` | `\\ref\{[^}]+\}` | `<REF_n>` | `\ref{fig:overview}` |
| 10 | `\eqref{}` | `\\eqref\{[^}]+\}` | `<EQREF_n>` | `\eqref{eq:loss}` |
| 11 | `\autoref{}` | `\\autoref\{[^}]+\}` | `<AUTOREF_n>` | — |
| 12 | `\label{}` | `\\label\{[^}]+\}` | `<LABEL_n>` | — |
| 13 | URL | `https?://\S+` | `<URL_n>` | `https://arxiv.org/abs/...` |
| 14 | 代码块 | ` ```[\s\S]*?``` ` | `<CODEBLOCK_n>` | Markdown 代码 |

## Markdown 表格识别（`<MDTABLE_n>` 详细规则）

**识别正则**（多行匹配）：

```python
# 一张 Markdown 管道符表格 = 表头行 + 分隔符行（含 :--- / ---: / :---:） + ≥0 数据行
MD_TABLE_PATTERN = re.compile(
    r'(^\|.+\|\s*\n'           # header row：以 | 开头、| 结尾
    r'\|[\s\-:|]+\|\s*\n'      # separator row：仅 - : | 与空白
    r'(?:\|.+\|\s*\n?)*)',     # 0+ data rows
    re.MULTILINE,
)
```

**整段表格**视为 1 个 `<MDTABLE_n>` 占位符送翻译模型。模型只看到占位符，不可能动表格内的任何字符。

**caption 处理**：表格的 caption 通常出现在表格紧前一行（如 `**Table 3.** Comparison of ...`）或紧后一行（`Table 3: ...`）。识别后**单独切出 segment** 走三步翻译，不进占位符。识别启发式：

```python
CAPTION_BEFORE = re.compile(r'^\*?\*?(Table|表)\s*\d+[.：:]\s*.+$', re.MULTILINE)
CAPTION_AFTER  = CAPTION_BEFORE  # 同样规则
```

**输出阶段还原**：
- 在 `01-step1-literal.md` / `02-step2-academic.md` / `03-step3-polished.md` 中，`<MDTABLE_n>` 替换回**原表格字符串**（一字不改）
- 在 `04-bilingual.md` 中，**单独占用一行**（不放进双栏 `| 原文 | 译文 |` 里），以"折叠 details + 表格"或"上下双栏"形式呈现：
  ```markdown
  <details><summary>Table 3 · 表 3 — 模型性能对比（原表保留）</summary>

  | Model | Acc | F1 |
  |---|---|---|
  | BERT | 89.5 | 88.2 |
  | Ours | 92.1 | 91.4 |

  </details>
  ```
- 在 `07-bilingual.html` 中，把表格直接渲染为 `<table>`，**caption 中英对照**展示在 `<caption>` 中

**底线断言**：`scripts/preserve_latex.py --verify` 必须额外校验：

```python
def verify_tables(original_md, translated_md):
    """表格行数列数严格一致"""
    orig_tables = MD_TABLE_PATTERN.findall(original_md)
    trans_tables = MD_TABLE_PATTERN.findall(translated_md)
    if len(orig_tables) != len(trans_tables):
        return [f"表格数量变更: 原文 {len(orig_tables)} → 译文 {len(trans_tables)}"]
    for i, (o, t) in enumerate(zip(orig_tables, trans_tables)):
        o_rows = o.count("\n")
        t_rows = t.count("\n")
        if o_rows != t_rows:
            return [f"表 {i+1} 行数变更: {o_rows} → {t_rows}"]
        if o.strip() != t.strip():
            return [f"表 {i+1} 内容被翻译/篡改（除 caption 外应一字不改）"]
    return []
```

## 不必保留但需注意一致性的 Token

下列 Token **不掩码**，但翻译时应**与术语库强一致**：

| 类 | 例 | 处理 |
|---|---|---|
| 数字（含 % 和单位） | `94.3%`, `2.1 points`, `1024-dim` | 不变 |
| 数据集名 | ImageNet, COCO, GLUE, MS-MARCO | 不翻译，原样 |
| 模型名 | BERT, ResNet, Transformer | 不翻译，原样 |
| 算法名 | Adam, SGD, AdamW | 不翻译，原样 |
| 化学式 | H₂O, CO₂, NaCl | 不变 |
| 单位符号 | °C, mg/L, m/s², ms, GB | 不变 |
| 缩写（首次出现含全称时） | "long short-term memory (LSTM)" | 中译时保留缩写：长短期记忆（LSTM） |

## 还原校验（每段必跑）

`scripts/preserve_latex.py --verify` 自动校验：

```python
def verify_preservation(original, translated, preserved_map):
    issues = []

    # 1. 所有占位符已被替换为真实内容
    leftover_placeholders = re.findall(r'<\w+_\d+>', translated)
    if leftover_placeholders:
        issues.append(f"占位符未还原: {leftover_placeholders}")

    # 2. 所有 preserved tokens 在 translated 中出现
    for tag, content in preserved_map.items():
        if content not in translated:
            issues.append(f"原始 token 丢失: {content[:50]}")

    # 3. 数字一致性
    orig_nums = set(re.findall(r'\b\d+\.?\d*%?\b', original))
    trans_nums = set(re.findall(r'\b\d+\.?\d*%?\b', translated))
    if orig_nums != trans_nums:
        diff = orig_nums.symmetric_difference(trans_nums)
        issues.append(f"数字变更: {diff}")

    # 4. 数据集 / 模型名常用词检查
    KNOWN_PROPER = {"ImageNet", "COCO", "BERT", "GPT", "Transformer", "ResNet", "Adam"}
    for word in KNOWN_PROPER:
        if word in original and word not in translated:
            issues.append(f"专有名词可能被翻译: {word}")

    return issues
```

校验失败时的处理：

| 严重度 | 触发条件 | 处理 |
|---|---|---|
| 🚨 阻断 | 占位符未还原 | 阻断输出此段，回退 Step 2，重试一次 |
| 🚨 阻断 | 原始 token 丢失 | 同上 |
| ⚠️ 警告 | 数字变更 | 标注此段，输出但提示用户复核 |
| ⚠️ 警告 | 专有名词被翻译 | 自动用术语库还原，提示用户 |

## 占位符设计的关键

为什么用 `<FORMULA_n>` 而不是 `[FORMULA_n]` 或 `{FORMULA_n}`？

- `< >` 不太可能在学术文本中出现（不像 `[]` 在引用中常见、`{}` 在 LaTeX 中是命令参数）
- LLM 对 `<XXX_n>` 这种 HTML/XML-style tag 的"不要修改"指令配合度最高
- 数字下标 `_n` 比字母下标更不易被模型当作"normal token"处理

## NEVER

- **NEVER** 在掩码后又取消掩码（让模型看到原始公式）
- **NEVER** 用同一占位符代替不同 token（每个 token 必须有唯一 ID）
- **NEVER** 在 Step 3 还原后再做任何改写（破坏校验）
- **NEVER** 假设模型会"理解"公式的语义并修复——它会幻觉
- **NEVER** 跳过 verify 阶段直接输出
