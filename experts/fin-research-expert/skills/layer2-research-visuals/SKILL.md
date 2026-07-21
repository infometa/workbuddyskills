---
name: layer2-research-visuals
description: "当用户明确要求K线、走势图、事件收益图、数据对比图、研报图片，或已取证数据用图形更易理解时使用。负责普通问答中的可复核可视化、WorkBuddy内联显示和跨客户端表格降级；不新增数据权限、不生成预测、不替代HTML Playbook。"
---

# Research Visuals Router

Use this skill only after the matching research workflow has completed authentication, subject resolution and evidence retrieval.

## Use When

- 用户明确要求“画图、走势图、K线、收益对比、事件表现、图表、研报图片”。
- 已取得的时间序列、方向对比或事件窗口数据用图形能明显降低理解成本。
- 用户需要普通问答中的图表，而不是完整 HTML 报告、仪表盘或 Playbook 页面。

## Do Not Use When

- 只有一个数值或几行短表，图表只会重复信息。
- 本轮认证未成功、主体未解析、时间窗口不清楚或证据不足。
- 用户要求个人持仓收益、仓位建议、价格预测、策略回测、买卖指令或收益承诺。
- 用户明确要求行业多空风向标或事件因子解读 HTML；分别使用 `layer3-industry-windvane` 或 `layer3-event-interpretation`，并由它们调用 `layer2-html-research-playbook` 共享渲染。

## Progressive References

Load only the references needed for the request:

- `references/common.md`: WorkBuddy inline visual gate, Fallback first, rendering safety, color, accessibility and failure behavior.
- `references/market-charts.md`: daily candlestick/volume, close or metric trend, and event-window return charts.
- `references/widget-svg-runtime.md`: chart-family template router and shared payload boundary.
- `references/widget-kline-runtime.md`: dedicated K-line, moving-average, volume and hover-detail runtime.
- `references/widget-trend-runtime.md`: dedicated one/two-series trend runtime.
- `references/widget-event-runtime.md`: dedicated signed event-window runtime.
- `references/report-images.md`: stable report-image eligibility, source verification, MCP image boundaries and no-fake-link fallback.

## Workflow

1. Finish the original Layer 2 route and its required Layer 1 contract preflight. This skill does not call a business data source by itself.
2. Identify the smallest useful visual: candlestick/volume, line trend, event-return bars, relationship diagram or eligible report image.
3. Normalize the evidence once and prepare the compact text/table representation first.
4. Load `references/common.md`, the chart-specific reference, `references/widget-svg-runtime.md`, and exactly one selected family template for numeric charts.
5. If the WorkBuddy inline visual gate passes, copy only the validated JSON payload into that family-specific JS-to-SVG template and call `show_widget` directly.
6. If the visual gate does not pass or rendering fails, return the prepared table and text. Never expose raw widget markup or tool errors.
7. Add the evidence window, source type, missing-data boundary and four-part financial disclaimer.

## Hard Boundaries

- The visual is a presentation layer, not a new source. It must not add, interpolate, repair or predict data.
- Source data must come from the current authenticated turn. Do not reuse prior-turn evidence after an authentication failure.
- A chart cannot be the only user-visible result; include a short interpretation and a readable fallback.
- Every user-visible financial visual remains AI-generated public-information research. 用户可见内容必须明确：AI 生成、仅基于公开信息整理、不构成投资建议、不构成个股推荐。
- Do not show API keys, raw MCP JSON, physical database names, internal document IDs, model scores, holdings or trade history.
- Report images follow `references/report-images.md`; normal chart data follows `references/market-charts.md`.
- WorkBuddy-only rendering instructions remain internal. Other clients receive the same evidence as a compact table and text.
- Normal-answer rendering must not create or execute Python/Node scripts, CLI pipelines, temporary JSON, SVG, PNG or HTML files. The selected packaged Widget family template is the renderer; do not merge all chart scripts into a generic runtime.
