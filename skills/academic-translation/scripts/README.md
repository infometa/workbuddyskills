# scripts/ — 工具脚本

本 Skill 内置的辅助脚本，供三步翻译过程调用。**所有脚本都是无副作用的纯函数式工具**（除了写文件输出）。

## 脚本清单

| 脚本 | 用途 | 调用时机 | 依赖 |
|---|---|---|---|
| `extract_pdf.py` | PDF 文本提取 + 章节切片 → segments.json | 输入路由（PDF 输入） | `pdfplumber` |
| `arxiv_fetch.sh` | arXiv 源码下载 + main.tex 定位 | 输入路由（arXiv ID 输入） | `wget`, `tar` |
| `preserve_latex.py` | 公式 / 引用 mask + restore + verify | 三步翻译每段输入 / 还原 / 校验 | （仅标准库） |

## 安装依赖

```bash
pip install pdfplumber
```

> `weasyprint`（PDF 排版输出）目前未在脚本中使用，后续 v0.5 版本将集成。

## 使用示例

### 1. 完整 PDF 翻译流水线

```bash
# 第 1 步：提取 PDF
python scripts/extract_pdf.py --in paper.pdf --out segments.json

# 第 2 步：把每段 raw_text 通过 preserve_latex.py 掩码
python scripts/preserve_latex.py mask --in segment_p1.txt --out segment_p1.masked.json

# 第 3 步：把 masked 文本送翻译模型（在 Skill 内部由 LLM 完成）
# 翻译后填回 JSON 的 translated 字段

# 第 4 步：还原占位符
python scripts/preserve_latex.py restore --in segment_p1.translated.json --out segment_p1.final.txt

# 第 5 步：校验
python scripts/preserve_latex.py verify --original segment_p1.txt --translated segment_p1.final.txt
```

### 2. arXiv 论文翻译

```bash
# 第 1 步：下载源码
bash scripts/arxiv_fetch.sh 2206.04655

# 第 2 步：直接处理 LaTeX（暂未在脚本中实现，由三步翻译模块内联完成）
# 暂用：
cat arxiv-2206.04655/source/main.tex | python scripts/preserve_latex.py mask ...
```

### 3. Preflight P1 检查

```bash
# PDF 可解析性
python scripts/extract_pdf.py check --in paper.pdf

# arxiv ID 合法性（在 arxiv_fetch.sh 内部完成）
bash scripts/arxiv_fetch.sh 2206.04655 /tmp/check
```

## 设计原则

1. **纯函数式**：脚本只读输入、写输出，不依赖 Skill 上下文
2. **可独立调试**：每个脚本都能从命令行直接运行
3. **失败可降级**：依赖缺失时打印清晰的安装提示而不是隐式失败
4. **公式零损伤**：`preserve_latex.py` 是核心护城河，所有翻译流程必经

## 路线图

- [ ] v0.2: `compile_xelatex.sh` — 双栏 LaTeX 编译（含 Docker fallback）
- [ ] v0.3: `md2pdf.py` — Markdown → 高质量 PDF（weasyprint + 中文字体配置）
- [ ] v0.4: `glossary_extractor.py` — 自动从用户已译论文中提取术语库
