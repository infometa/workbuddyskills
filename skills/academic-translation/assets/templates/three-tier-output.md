---
paper_id: {paper_id}
step: {step1_literal | step2_academic | step3_polished}
language: {zh | en}
generated_at: {ISO-time}
total_segments: {N}
---

# {论文标题（按 step 语言渲染）}

> **Provenance**: {source_type}:{source_id} · 总段数 {N} · 已应用术语库: {glossary_list}
>
> **本档说明**：
> - **直译版（step1）** = Step 1 输出，**保留所有术语 + 占位符**，逐句对应原文，不追求流畅
> - **学术规范版（step2）** = Step 2 输出，**已应用 Chinglish 校正 + 术语一致性 + 学术惯例**
> - **信达雅终稿（step3）** = Step 3 输出，**已应用顶会风格 + 段落级流动 + 去 AI 味**
>
> 所有版本中的公式、`\cite{}`、`\ref{}`、数字、数据集名、算法名 **完全一致** — 雅化只改语言层，不改技术内容。

---

## §1 引言（Introduction）

> page 1 · §1 Introduction · 段落 §1-p1
>
> 原文片段（excerpt）：
> > Deep learning has achieved remarkable success in...

我们提出一种新颖的框架...

> page 1 · §1 Introduction · 段落 §1-p2

具体来说，本文做了三方面贡献：

- 我们 \cite{vaswani2017attention}（占位符已还原）...
- 在 ImageNet 上，我们的方法达到 94.3% 的准确率，比最强基线高 2.1 个绝对点...
- ...

---

## §2 相关工作（Related Work）

> page 2 · §2 Related Work · 段落 §2-p1

...

---

（以下省略，按章节继续）

---

## 自检摘要（嵌入式 mini summary）

| 维度 | 值 | 状态 |
|---|---:|:-:|
| 段落数 | {N} | — |
| 公式保留 | {M}/{M} | ✅ |
| 引用保留 | {C}/{C} | ✅ |
| 术语一致性 | {x}/{y} 唯一术语已对齐 | {✅ \| ⚠️} |

> 详细自检报告见 `06-self-check.md`。

---

## 修订日志（仅在 step2 / step3 显示）

### 与上一档（step{N-1}）的关键差异

- §1-p1: "在最近几年里" → "近年来"（删冗 "里"，符合学术中文）
- §1-p3: "实验显示了..." → "实验表明..."（顶会偏好简洁）
- ...

（前 5 条 + "更多差异见 06-self-check.md"）
