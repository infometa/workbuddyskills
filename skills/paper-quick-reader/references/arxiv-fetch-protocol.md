# arXiv 抓取协议（TeX Source 优先）

> **吸收来源**：
> - skills.sh `karpathy/nanochat@read-arxiv-paper` —— TeX Source 优先策略
> - Knot `arXiv 论文搜索器`（DL=2769）—— Python arxiv 库的多维搜索能力
>
> **适用场景**：用户输入是 **arXiv URL / arXiv ID** 时（而非本地 PDF 路径），优先走 TeX tarball 路径而非 PDF 解析。

## Contents

- [一、为什么优先 TeX Source？](#一为什么优先-tex-source)
- [二、ID 规范化](#二id-规范化)
- [三、下载流程](#三下载流程)
- [四、页码映射（TeX→PDF）](#四页码映射texpdff)
- [五、速率合规与缓存策略](#五速率合规与缓存策略)
- [六、降级路径](#六降级路径)

---

## 一、为什么优先 TeX Source？

| 维度 | PDF 路径（`scripts/parse_pdf.py`） | TeX Source 路径（`scripts/fetch_arxiv_tex.py`） |
|---|---|---|
| **文本提取** | pdfplumber + 启发式重组，双栏易串行 | LaTeX 源码天然线性 |
| **公式** | PDF 公式是向量图 / 光栅化图形 —— 无法提取原文 | LaTeX `$...$` / `\begin{equation}` 原样保留 |
| **章节结构** | 靠字号 + 关键词启发式识别 | `\section{...}` / `\subsection{...}` 直接解析 |
| **参考文献** | 文本块提取后启发式拆分 | `\bibitem{...}` / `.bib` 文件结构化 |
| **图表 caption** | 靠正则匹配"Figure N" 开头 | `\caption{...}` 原样 |
| **页码** | 天然有页码 | **缺失** —— 需映射回 PDF 页码（见 §4 降级） |

**结论**：arXiv 输入优先 TeX，**但 `page` 字段必须从 PDF 补齐**（provenance 不能丢页码）。

---

## 二、输入识别与分支路由

### 2.1 arXiv 输入判定

| 输入形式 | 正则/规则 | arXiv ID 提取 |
|---|---|---|
| `https://arxiv.org/abs/2601.07372` | `arxiv.org/abs/` | 取路径末段 |
| `https://arxiv.org/pdf/2601.07372.pdf` | `arxiv.org/pdf/` | 去 `.pdf` 后缀 |
| `https://arxiv.org/pdf/2601.07372v2` | 含版本号 | 保留或去除 `vN`（保留更精确）|
| `2601.07372` | `^\d{4}\.\d{4,5}(v\d+)?$` | 直接是 ID |
| `arXiv:2601.07372` | `^arXiv:` 前缀 | 去前缀 |
| 老版 ID `cs.CL/0610050` | 含 `/` 的 6 位数字 | 保留原格式 |

### 2.2 路由决策

```
if source.kind == "arxiv_url" or source.kind == "arxiv_id":
    1) 调 scripts/fetch_arxiv_tex.py 下载 TeX tarball
    2) 并行：调 scripts/parse_pdf.py（PDF 版本，用于页码映射）
    3) 合并：TeX 给结构 + 公式 + 章节精确名称；PDF 给页码 + bbox
elif source.kind == "pdf_path":
    仅走 scripts/parse_pdf.py
```

---

## 三、`fetch_arxiv_tex.py` 协议

### 3.1 URL 规范化

```python
# 输入：任意 arXiv 形式
# 输出：arxiv_id（不含 v 后缀）, 源 URL
abs_url = f"https://arxiv.org/abs/{arxiv_id}"
src_url = f"https://arxiv.org/src/{arxiv_id}"      # TeX tarball
pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"  # PDF 回退
```

**关键**：`arxiv.org/src/{id}` 是 arXiv 官方的 **TeX tarball 下载接口**（不是 HTML 抓取，是 tar.gz 二进制）。

### 3.2 缓存策略

```
~/.cache/paper-quick-reader/arxiv/{arxiv_id}/
├── src.tar.gz              # 原始 tarball
├── unpacked/               # 解压后的 LaTeX 源树
│   ├── main.tex            # 入口（或 paper.tex / {id}.tex）
│   ├── sections/...
│   └── refs.bib
├── source.pdf              # 并行下载的 PDF（用于页码映射）
└── manifest.json           # 记录入口文件位置 + 解析元数据
```

- 已存在 `src.tar.gz` → 跳过下载
- **避免重复下载**是性能关键（arXiv 有速率限制）

### 3.3 入口文件定位启发式

TeX 源码没有统一的入口命名，按优先级查找：

| 优先级 | 文件名模式 | 内容判定 |
|:-:|---|---|
| 1 | `main.tex` / `paper.tex` / `article.tex` | 含 `\documentclass` |
| 2 | `{arxiv_id}.tex` | 含 `\documentclass` |
| 3 | `ms.tex` / `manuscript.tex` | 含 `\documentclass` |
| 4 | 目录下唯一一个 `\documentclass` 的 .tex | — |
| 5 | 多个都含 `\documentclass` | 取 `\begin{document}` 之前内容最少的（通常是入口而非 template）|

找不到 → 报错 `ARXIV_TEX_ENTRY_NOT_FOUND`，降级到 PDF 路径。

### 3.4 `\input` / `\include` 递归处理

```
读 main.tex：
  逐行扫描 \input{xxx} / \include{xxx} / \subfile{xxx}
  对每个 xxx.tex 递归读取 + 内联展开
  最多递归深度 5（防循环）
  忽略 \input{preamble.tex} 这类非内容文件
```

---

## 四、页码映射（Provenance 补齐）

### 4.1 为什么需要映射？

TeX 源码**没有页码**概念。但 paper-quick-reader 的所有 provenance 都要求 `page` 字段 —— 否则无法追溯。

### 4.2 映射策略

1. **同步下载 PDF**：`fetch_arxiv_tex.py` 在下载 tarball 的同时拉 PDF
2. **双轨解析**：TeX 给章节结构 + 精确文本；PDF 给每个 block 的页码
3. **文本对齐**：对 TeX 提取的每个 block，做 ngram 匹配找到 PDF 中的位置 → 取页码

```python
# 伪代码
tex_blocks = parse_tex(main_tex_path)           # [{text, section_title, tex_line}]
pdf_blocks = parse_pdf(pdf_path)                # [{text, page, section_title}]
for tb in tex_blocks:
    matched = find_best_ngram_match(tb.text, pdf_blocks)
    tb.page = matched.page if matched.confidence >= 0.7 else None
```

### 4.3 降级（PDF 不可用时）

| 情况 | 处理 |
|---|---|
| PDF 下载失败但 TeX 成功 | provenance_map 中 `page = null`，附 `note: "仅 TeX 源，页码缺失"` |
| TeX tarball 下载失败 | 完全回退到 `scripts/parse_pdf.py` |
| 两者都失败 | 返回错误 `ARXIV_FETCH_FAILED`，提示用户手动提供 PDF |

---

## 五、合规与速率限制

### 5.1 arXiv 使用条款要点

- 允许个人/机构的合理批量访问（≤ 1 req/3s）
- 不得分发非作者许可的全文
- 必须尊重 `robots.txt`

### 5.2 本 Skill 的自我约束

| 约束 | 实施 |
|---|---|
| **速率** | 默认 1 req / 3s（可通过 `PAPER_QR_ARXIV_QPS` 环境变量放开）|
| **缓存优先** | 同 `arxiv_id` 24 小时内不重复下载 |
| **批量拒绝** | 单次 run 内 `papers` 数组里 arXiv 来源不超过 10 个（与 compare 模式上限一致）|
| **User-Agent** | 明确标识 `paper-quick-reader/{version}` + contact（从 `_skill_meta.json` 读）|
| **不做** | 不做"订阅全领域" / "每日自动拉取"（那是 arxiv-watcher 的职责，见 `SKILL.md` § 与其它 Skill 的关系）|

### 5.3 禁用场景

- **NEVER** 用本协议做 arXiv 批量爬取（违反速率与合规）
- **NEVER** 缓存 tarball 到公共目录让其他用户访问
- **NEVER** 分发下载的全文（仅限用户当前 session 使用）

---

## 六、（已删除）arxiv-search 辅助工具

> v0.4.0 起，原 `scripts/search_arxiv.py`（arxiv 关键词检索 helper）已**整体移除**。
> 理由：与 SKILL.md 反范围条款"不做论文检索/获取"冲突——getter 阶段交由 IDE / LLM / curl 等通用工具，本 Skill 只负责"读"。
> 用户若需要"先搜再读"流程：先用通用搜索工具（Semantic Scholar / 秘塔 / Google Scholar）拿到 arXiv ID，再以 `arxiv_id` / `arxiv_url` / `pdf_path` 喂入本 Skill。

---

## 七、常见错误（NEVER）

- **NEVER** 对 arXiv URL 输入仍然走 `parse_pdf.py`（会丢失公式、双栏错乱；该走 `fetch_arxiv_tex.py`）
- **NEVER** 跳过 PDF 并行下载（TeX 无页码，provenance 会全部 null）
- **NEVER** 无限递归 `\input`（会被攻击者构造的循环引用卡死）
- **NEVER** 在缓存中保留非当前用户下载的 tarball 并提供给新 session（破坏合规）
- **NEVER** 在本 Skill 内做关键词检索 / 论文发现（v0.4.0 已移除相关脚本，超出本 Skill 边界）
- **NEVER** 忽略 arXiv 的速率限制（会被 IP 封禁）
- **NEVER** 对老格式 ID（`cs.CL/0610050`）按新格式处理（会 404）
