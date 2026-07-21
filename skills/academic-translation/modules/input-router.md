# 输入路由模块

将用户输入分流到对应的解析路径，统一产出**章节切片 + Provenance 元数据**给三步翻译消费。

## 路由表

| 输入类型 | 识别信号 | 解析路径 | 关键脚本 |
|---|---|---|---|
| **PDF** | 路径以 `.pdf` 结尾 / 用户上传 PDF 文件 | PDF → 文本提取 → 章节切片 | `scripts/extract_pdf.py` |
| **arXiv ID** | 形如 `2206.04655` 或 `2401.12345` 或 `cs.LG/9901001` | 下载 e-print → 解压 → 定位 main.tex | `scripts/arxiv_fetch.sh` |
| **arXiv URL** | `arxiv.org/abs/XXXX.NNNNN` 或 `arxiv.org/pdf/XXXX.NNNNN` | 提取 ID → 走 arXiv 路径 | 同上 |
| **LaTeX 源** | `.tex` 文件 / 含 `\documentclass` 的文本 | 直接解析 → 段落切片（保留命令） | `scripts/preserve_latex.py --parse` |
| **Markdown 文件** | `.md` 文件 | 解析标题 → 段落切片 | （内置） |
| **粘贴文本** | 字符串，无文件路径 | 段落切片 + 启发式段落级 Provenance | （内置） |

## 输出统一 schema（章节切片）

无论输入类型，输入路由器**必须**产出以下统一结构供三步翻译消费：

```yaml
paper_meta:
  source_type: "pdf" | "arxiv" | "latex" | "markdown" | "text"
  source_path: "/abs/path/to/source"  # 或 arxiv ID / 粘贴文本的 hash
  paper_id: "arxiv:2206.04655" | "pdf:lecun-2015"  # slug，用于输出目录命名
  language_detected: "en" | "zh" | "mixed"
  total_segments: 47
  pdf_pages: 12  # 仅 PDF
  has_latex: true | false  # 是否含 LaTeX 源（决定公式保留策略严格度）

segments:
  - segment_id: "§1-p1"
    section_path: ["1", "Introduction"]
    page_range: [1, 1]  # PDF 页码；非 PDF 则为 null
    char_range: [0, 487]  # 在原文中的字符偏移
    paragraph_kind: "narrative" | "abstract" | "caption" | "algorithm" | "table" | "equation" | "list_item"
    raw_text: "We propose a novel..."
    preserved_tokens:
      formulas: ["$\\mathbf{x}_t = f(\\mathbf{x}_{t-1})$"]
      citations: ["\\cite{vaswani2017attention}", "\\cite{he2016deep}"]
      cross_refs: ["\\ref{fig:overview}", "\\eqref{eq:loss}"]
      datasets: ["ImageNet", "COCO"]
      proper_nouns: ["BERT", "Transformer"]
      numbers: ["94.3%", "2.1 points"]
    masked_text: "We propose a novel <FORMULA_1>... see <CITE_1>..."  # 用于送翻译
```

> `masked_text` 是关键设计：发给翻译模型的版本是把所有需要保留的 token 替换为 `<FORMULA_1>` `<CITE_1>` 等占位符。Step 3 完成后再用 `scripts/preserve_latex.py --restore` 把占位符还原回真实内容，**保证一字不改**。

## PDF 解析路径

```python
import pdfplumber
import re

def parse_pdf(path):
    with pdfplumber.open(path) as pdf:
        segments = []
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for para in re.split(r'\n\s*\n', text):
                if len(para.strip()) < 30:
                    continue
                segments.append({
                    "raw_text": para.strip(),
                    "page_range": [page_num, page_num],
                    "section_path": detect_section(para),
                    "paragraph_kind": classify(para),
                })
        return segments
```

**章节检测启发式**：
- 行首匹配 `^(Abstract|Introduction|Related Work|Method|Experiments|Conclusion)\b` → section heading
- 行首匹配 `^\d+(\.\d+)*\s+[A-Z]` → 编号 section（`3.2 Method`）
- 全大写短行 → 可能是 caption / heading

**标题层级映射约定**：PDF 内的视觉标题层级（字号 / bold / 居中）映射到 Markdown 的 `#` / `##` / `###`，规则与主流学术 PDF→Markdown 工具一致。

## arXiv 解析路径

```bash
ARXIV_ID="$1"
mkdir -p arXiv_${ARXIV_ID}
wget -q "https://arxiv.org/e-print/${ARXIV_ID}" -O arXiv_${ARXIV_ID}/source.tar.gz
tar -xzf arXiv_${ARXIV_ID}/source.tar.gz -C arXiv_${ARXIV_ID}/source/
MAIN_TEX=$(grep -lE '\\documentclass' arXiv_${ARXIV_ID}/source/*.tex | head -1)
echo "main_tex=${MAIN_TEX}"
```

定位到 `main.tex` 后，走 LaTeX 解析路径。

**完整 arXiv 翻译工作流**：下载 → 翻译 → REVIEW → CJK → 编译 → Report 六步走。
> ⚠️ 本 Skill **只做翻译产出**，不自动执行 xelatex 编译；编译由用户按需触发 `scripts/compile_xelatex.sh`。

## LaTeX 解析路径（关键 — 公式零损伤的核心）

```python
import re

LATEX_PRESERVE_PATTERNS = [
    (r'\$[^$]+\$', 'INLINE_MATH'),
    (r'\$\$[^$]+\$\$', 'DISPLAY_MATH'),
    (r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}', 'EQUATION'),
    (r'\\begin\{align\*?\}.*?\\end\{align\*?\}', 'ALIGN'),
    (r'\\begin\{algorithm\*?\}.*?\\end\{algorithm\*?\}', 'ALGORITHM'),
    (r'\\cite[tp]?\{[^}]+\}', 'CITE'),
    (r'\\ref\{[^}]+\}', 'REF'),
    (r'\\eqref\{[^}]+\}', 'EQREF'),
    (r'\\autoref\{[^}]+\}', 'AUTOREF'),
    (r'\\label\{[^}]+\}', 'LABEL'),
]

def mask_latex(text):
    counter = {}
    masked = text
    preserved = {}
    for pattern, kind in LATEX_PRESERVE_PATTERNS:
        def repl(m):
            counter[kind] = counter.get(kind, 0) + 1
            tag = f'<{kind}_{counter[kind]}>'
            preserved[tag] = m.group(0)
            return tag
        masked = re.sub(pattern, repl, masked, flags=re.DOTALL)
    return masked, preserved
```

**送翻译模型的就是 `masked` 文本**，模型完全看不到公式和引用 → 不可能改动它们。Step 3 完成后用 `preserved` 字典还原。

详细规则见 [../refs/formula-preservation.md](../refs/formula-preservation.md)。

## Markdown 解析路径

按 ATX 标题切分（`#` `##` `###`），每个段落作为一个 segment。代码块（` ``` ` 围栏）整体保留不翻译，仅翻译 caption。

## 粘贴文本路径

按双换行分段，每段一个 segment。Provenance 简化为段落序号（`§p3`）。

> **MUST**：粘贴文本无页码，但**不能**省略 Provenance；必须用段落 hash 做完整性校验，确保 Step 1 → Step 3 的段落 ID 不变。

## 输入路由完成后的下一步

把统一 schema 交给 [three-step-translation.md](three-step-translation.md) 的 Step 1 直译入口。
