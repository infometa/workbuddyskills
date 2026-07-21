# 样例数据索引（v0.4.0 起外迁）

> 本 Skill 的**端到端样例**（含 result.json / provenance-audit.json / HTML demo / 原始 PDF）
> 已从 `references/examples/` 与 `assets/examples/` 迁出到项目根 `demos/paper-quick-reader/`，
> 以**避免 7.7M PDF 污染 LLM 加载 references 的 token 视野**。

## 完整样例位置

| 类型 | 旧位置（已删） | 新位置 |
|---|---|---|
| `result.json` 黄金样本 + 原始 PDF | `references/examples/` | `demos/paper-quick-reader/result-fixtures/` |
| 渲染好的 HTML 报告（3 篇 demo） | `assets/examples/` | `demos/paper-quick-reader/html-demos/` |

## 包含的样例

| 样例 | 模式 | 用途 |
|---|---|---|
| `result-fixtures/single-skim-selfinstruct/` | single + skim | 单篇裸读最小样例 |
| `result-fixtures/single-deep-dive-selfinstruct/` | single + deep | 单篇精读 + provenance 审计样例 |
| `result-fixtures/compare-3papers-alignment/` | compare × 3 篇 | Self-Instruct / Alpaca / LIMA 对比样例（含原 PDF）|

## LLM 使用建议

- **读 schema** → 读 [`output-schema.md`](output-schema.md) 即可，不需要去 demos 拉真实 result.json
- **写 few-shot** → 用 `references/calibration/` 的 5 个锚点，已内置在 skill 中
- **debug 渲染** → 让 `render_report.py` 跑 `demos/paper-quick-reader/result-fixtures/*/result.json` 重新出 HTML/MD/PDF
