# Step 9 · 多轮追问闭环协议（v0.4.0 / P1-B）

> 从 SKILL.md 主文抽出（v0.4.5 瘦身），减少首次触发时的上下文负担。仅在判定为「同 session 追问已读论文」时按需读入。

## 触发判定

任一为真即进入 Step 9（**不重启 Step 1-7**）：

- 同一 chat session 已交付 `result.json`，且本轮**无新 papers**
- 用户表述含「再问 / 继续 / 那个 / 它的 / 上面这篇 / 刚才那篇」等指代

典型用户表述（按相似度排序）：

| 表述 | 是否走 Step 9 |
|---|:---:|
| "那个 52K 怎么过滤的？" | ✅ |
| "再看下 limitations" | ✅ |
| "继续问它的 baseline" | ✅ |
| "上面这篇的 dataset 来源是？" | ✅ |
| "刚才那篇的复现难度大吗？" | ✅ |
| "重新读一下这篇 PDF"（用户主动重启）| ❌（回 Step 1 重启）|
| "换一篇 paper：./xxx.pdf"（papers 变了）| ❌（回 Step 1 重启）|

## 五项动作

### ① 复用 parse cache

`scripts/parse_pdf.py` 已支持 `~/.cache/paper-quick-reader/parse/<hash>.json`：
- cache hit 直接读 JSON，**不再调 pdfplumber**
- cache 命中后日志输出 `[cache hit] /path/to/<hash>.json`
- cache miss → 仍走 pdfplumber 全流程 + 写入 cache

### ② 复用上一轮 result.json

本轮**只追加** `deep_dive_answers[i]`，**不重写**：
- summary_card（已稳定，无需复算）
- connection_points（除非用户显式说「重新挖关联」）

### ③ 新问题视作 specific_question

自动走 Step 5 增量分支：
- 解析新问题 → 填入 `context.specific_question`
- 走标准精读协议（excerpt + 三段 critical_analysis）
- 追加到 `result.json` 的 `deep_dive_answers` 数组末尾，不覆盖已有条目

### ④ Provenance 增量校验

- 仅对**新 excerpts** 跑 `verify_provenance.py`
- 整篇 `confidence_degraded` 状态保持上一轮值（不回滚也不重判）
- 新 claim 单独标 ngram 置信度

### ⑤ 报告默认不刷新

- 用户若主动说「重生成报告 / 刷新 HTML / 给我新版 PDF」才按 Step 8 询问格式
- 此时 `result.json` 已含追问的新答案，渲染器直接读取即可

## NEVER（实操禁令）

- **NEVER** 重新调 `parse_pdf.py`（除非 cache miss）
- **NEVER** 重出 `summary_card` 浪费 token
- **NEVER** 切换论文却仍走 Step 9（papers 变了 → 必须回 Step 1 重启）
- **NEVER** 在 Step 9 内重置 `confidence_degraded`（上一轮的整篇可信度判定不该被新问题污染）

## 与 Step 8 的协同

Step 9 默认**不**触发 Step 8 的报告询问（追问场景下用户多半在 chat 内消费答案）。
仅当用户主动要求「重生成 / 刷新 / 出 PDF」才走 Step 8 的 4 选格式追问。
