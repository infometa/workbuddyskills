# 异常与 Fallback 速查表

> 从 SKILL.md 主文抽出（v0.4.5 瘦身）。**主文保留一句"详见本 ref"指针**；具体降级路径与处理规则在此。

## 设计原则

工作流执行中常见的异常路径与处理动作。**核心**：能降级先降级（保持闭环可用）；无法降级则**主动告知用户**而非静默跳过。

## 异常 → 处理动作映射

| 异常场景 | 触发条件 | 处理动作 | 涉及 Step |
|---|---|---|---|
| **损坏 PDF** | `parse_pdf.py` 抛 PDFSyntaxError / pdfplumber 返回空文本 | 报错退出 + 提示用户"PDF 可能损坏，建议重新下载或粘贴文本" → 用户可改投 `pasted_text` 路径 | Step 2 |
| **加密 PDF** | PDF 含 owner / user 密码 | 报错退出 + 提示"本 Skill 不存储密码，请用户解密后重投"；**不**尝试破解 | Step 2 |
| **图像层 PDF / 扫描件** | `parse_pdf.py` 文本层为空但页数 > 0 | 报错退出 + 提示"建议先用 OCR 工具转文本层"；本 Skill 立场拒绝 OCR（→ NEVER 反范围） | Step 2 |
| **非 UTF-8 编码** | `pasted_text` / docx 解码出乱码 | 自动尝试 GBK / Latin-1 二级 fallback；仍失败则报错退出并展示前 200 字符让用户人工干预 | Step 2 |
| **arxiv 网络超时 / 503** | `fetch_arxiv_tex.py` 任一 HTTP 请求 ≥ 30s 或 5xx | 重试 1 次（指数退避 5s）；二次失败 → 自动降级到 PDF 回退 URL；PDF 也失败 → 提示用户"改投本地 `pdf_path` 或 `pasted_text`" | Step 2 (arxiv 分支) |
| **arxiv ID 不存在 / 404** | API 返回 404 或 abs 页 404 | 立刻报错退出 + 提示用户检查 ID；**不**做 fuzzy match（避免误读邻近论文） | Step 2 (arxiv 分支) |
| **TeX 入口文件不可定位** | tarball 解压后无 `\documentclass` 主文件 | 降级到 PDF 回退 URL；同时记录到 `provenance-audit.json` 的 `meta.fallback_reason` | Step 2 (arxiv 分支) |
| **Provenance ngram 大面积失配** | `verify_provenance.py` 标记 `confidence_degraded == true`（high<60% 或 failed≥3）| HTML / Markdown 顶部出红色 banner；CP-8 询问报告时**默认勾选** md（保留可疑标记），不静默隐藏 | Step 7 |
| **weasyprint 未安装** | 用户选 PDF 但 `weasyprint` import 失败 | 自动降级生成 HTML + 提示"请打开 .html 后用浏览器 ⌘+P 打印为 PDF"；**不**报错退出 | Step 8 |
| **papers > 10** | 用户传入 `papers` 数组长度 > 10 | 立即拒绝 + 建议分批或改用文献综述 Skill；不强制截断（避免静默丢论文）| Step 0 |
| **单篇 > 50 页** | 解析后 `meta.page_count > 50` | 警告"这不是速读场景"+ 询问用户确认继续 / 切到精读单章 | Step 2 |

## 通用原则（任何异常都遵循）

- ❶ 异常先**告知用户原因**（具体到哪一步、哪个文件、哪条规则触发），不静默吞掉
- ❷ 能降级先降级（PDF→pasted_text、TeX→PDF、PDF 报告→HTML），保持闭环可用
- ❸ 不存储敏感信息（密码、token、用户原文非必要副本）
- ❹ 异常处理后续工程问题（如重试次数、超时阈值）可在 `_skill_meta.json` 调，**不**在主流程硬编码

## 何时读本文件

主流程（Step 0-8）正常路径下**无需**读本文件。仅在：
- Step 2 解析报错时（PDF / TeX / 编码异常）
- Step 7 `verify_provenance.py` 输出 `confidence_degraded == true` 时
- Step 8 `weasyprint` import 失败时
- 任何「能降级先降级」决策点

读入后按表格对应行执行处理动作即可。
