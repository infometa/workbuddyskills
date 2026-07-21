---
paper_id: {paper_id}
session_id: {session_id}
generated_at: {ISO-time}
based_on: step3_polished
---

# 翻译自检报告

## 1. 整体指标

| 维度 | 数值 | 阈值 | 状态 |
|---|---:|---:|:-:|
| 总段数 | {N} | — | — |
| Step 1 直译成功率 | {n1}/{N} ({pct}%) | ≥ 95% | {✅ \| ⚠️ \| ❌} |
| Step 2 反思成功率 | {n2}/{N} ({pct}%) | ≥ 95% | {✅ \| ⚠️ \| ❌} |
| Step 3 雅化成功率 | {n3}/{N} ({pct}%) | ≥ 90% | {✅ \| ⚠️ \| ❌} |
| 公式保留率 | {f1}/{f0} ({pct}%) | 100% | {✅ \| ❌} |
| 引用保留率 | {c1}/{c0} ({pct}%) | 100% | {✅ \| ❌} |
| 数字保留率 | {n_num1}/{n_num0} ({pct}%) | 100% | {✅ \| ❌} |
| 术语一致性 | {t_unique_consistent}/{t_unique_total} 唯一术语全文统一 | ≥ 95% | {✅ \| ⚠️ \| ❌} |
| Provenance 完整性 | {p1}/{N} 段含三维 Provenance | 100% | {✅ \| ❌} |

> 公式 / 引用 / 数字保留率必须 100%。任一非 100% 都说明 `scripts/preserve_latex.py --verify` 检测失败，需人工复核。

## 2. 应用的术语库

### 2.1 加载情况

| 来源 | 文件 | 术语数 | 命中数 |
|---|---|---:|---:|
| 内置基础 | refs/glossary/general-cs-terms.md | 120 | 47 |
| 内置领域 | refs/glossary/{ml \| nlp \| cv \| ir-data}-venues.md | {N} | {N} |
| 用户上传 | config/user-glossary.yaml | {N} | {N} |

### 2.2 高频命中术语（前 20）

| 术语 | 译法 | 来源 | 命中次数 |
|---|---|---|---:|
| embedding | 嵌入 | glossary/ml-venues.md | 18 |
| backbone | 骨干网络 | glossary/cv-venues.md | 7 |
| ... | ... | ... | ... |

### 2.3 术语库未覆盖（保留原文 + 暂译）

下列术语在内置 / 用户库中均未找到，按"原文（暂译）"格式输出，建议用户加入自定义术语库：

| 原文 | 暂译 | 出现次数 | 段落 |
|---|---|---:|---|
| differentiable rendering | 可微渲染（暂） | 5 | §3.1, §3.2, §4 |
| gauge equivariance | 规范等变性（暂） | 3 | §2, §3 |
| ... | ... | ... | ... |

## 3. 异常段落（需人工复核）

| 段落 | 章节 | 问题 | 建议 |
|---|---|---|---|
| §3.2-p4 | Method | Step 3 触发 `length_reasonable` 失败，已回退到 Step 2 | 人工审核此段，可能是过度雅化 |
| §4.1-p2 | Experiments | 公式 `<EQUATION_3>` 还原后包含罕见命令 `\providecommand` | 复核 LaTeX 编译是否成功 |

## 4. Step 1 → Step 3 修改样例（前 3 个）

### 样例 1（§1-p1，Chinglish 校正 + 删冗）

| Step | 文本 |
|---|---|
| Step 1 | "在最近几年里，深度学习取得了重要的进展" |
| Step 2 | "近年来，深度学习取得了重要进展" |
| Step 3 | "近年来，深度学习取得了显著进展" |

差异：Step 1→2 删除"里"+"的"（Chinglish 校正"in recent years"+"important"过度直译），Step 2→3 词汇升档（"重要" → "显著"）。

### 样例 2（§3.2-p1，公式保留 + 顶会风格）

| Step | 文本（含占位符）| 占位符还原后 |
|---|---|---|
| Step 1 | "我们利用 `<INLINE_MATH_1>` 来证明..." | "我们利用 $\mathbf{x}_t = f(\mathbf{x}_{t-1})$ 来证明..." |
| Step 3 | "我们用 `<INLINE_MATH_1>` 表明..." | "我们用 $\mathbf{x}_t = f(\mathbf{x}_{t-1})$ 表明..." |

差异：utilize → use, demonstrate → show（顶会偏好简洁）；公式占位符在所有 Step 中**完全一致**，仅最终输出还原。

### 样例 3（§4.2-p3，Hedging 校准）

| Step | 文本 |
|---|---|
| Step 1 | "我们的方法表现得相当好" |
| Step 2 | "我们的方法表现良好" |
| Step 3 | "我们的方法在 ImageNet 上达到 94.3% 的准确率，比最强基线高出 2.1 个绝对点" |

差异：Step 1→2 删去"得相当"（口语化），Step 2→3 用具体数字替代主观判断（"用具体数字代替模糊 hedging"原则）。

## 5. 推荐人工复核重点

1. 异常段落（共 {N} 个）— 见第 3 节
2. 术语库未覆盖词（共 {N} 个）— 见第 2.3 节
3. Abstract / Conclusion 两段 — 这两段对投稿影响最大，建议二次精读
4. 含 `<TABLE_n>` `<FIGURE_n>` 占位符的段落 — 表格 / 图的 **caption 翻译**：
   - LaTeX 路径：`scripts/preserve_latex.py` 已在 mask 前预提取 `\caption{...}` 文本送翻译，restore 时自动回填中文 caption；若该段在第 3 节"异常段落"中出现 `caption_unmatched` 警告，需人工核对
   - PDF / Markdown 路径：caption 仅当独立成段并以 `Figure N:` / `Table N:` 开头时被识别翻译，**与图表本体已脱钩**，需人工核对图表与中文 caption 的对应关系
   - 表格内**数值单元格**始终不翻译；表格**表头文字**、图内 **label / 坐标轴文字**均需人工处理

## 6. 输出文件

| 文件 | 用途 | 大小 |
|---|---|---:|
| 01-step1-literal.md | Step 1 直译初稿 | {kB} |
| 02-step2-academic.md | Step 2 学术规范版 | {kB} |
| 03-step3-polished.md | Step 3 信达雅终稿（推荐主用） | {kB} |
| 04-bilingual.md | 双栏对照 Markdown | {kB} |
| 05-bilingual.tex | LaTeX 双栏（投稿用） | {kB} |
| 06-self-check.md | 本报告 | {kB} |
| _meta.json | 会话元数据 | {kB} |

---

> 报告由 `academic-translation` Skill 自动生成。如需深度二次润色，建议人工复核第 3、5 节后调用本 Skill 的 `精翻` 模式重跑。
