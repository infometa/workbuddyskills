# DashboardSpec 1.0.0 调用摘要

正式契约源：`contracts/financial-visualization/v2/dashboard-spec.schema.json`。这是内部调用说明，不是另一个 Schema；运行时工具 Schema 与服务端证据校验优先。

顶层为 `specVersion: "1.0.0"`、`title`、`blocks`（1～8 个）。每块都有唯一 `id` 和 `type`，可带 `title`。除 `market-chart` 和 `provider-action` 外必须有 `evidence_refs`（1～12 个去重引用，含本轮审核知识证据）。整张 Dashboard 所有区块、数值绑定与 chart_ref 合计最多 12 个不同证据引用。

| 类型 | 内容字段 |
| --- | --- |
| `comparison` | `items`，2～4 项，以同一维度对比 |
| `scenarios` | `items`，1～4 项，按用户场景解释 |
| `key-points` | `items`，1～6 项，并列要点 |
| `process` | `steps`，2～8 项，审核材料支持的顺序 |
| `formula` | `expression`（审核公式文字或 binding）、可选 `operands`（最多 6 个 metric）、`result`（binding）、`interpretation` |
| `mechanism` | `data_nature:"illustrative"`、`mechanism:"macd-cross"` / `"moving-average-cross"` / `"flow"`，可选 `description`、`nodes`、`edges` |
| `provider-action` | `chart_ref:{evidence_ref,key:"chart"}`，知识 Provider 行动卡且只能为唯一末块 |
| `market-chart` | `chart_ref:{evidence_ref,key:"chart"}`；只引用 `evidenceCharts` 声明过的 chart；可选 `purpose`（本图回答的问题）、`series_ids`（选择并排序 Provider 发布的折线序列 ID） |

`item` 为 `{title,body:string[],metrics?,footnote?}`，body 1～6 条。`metric` 为 `{label?,value:{evidence_ref,key}}`。binding 的 key 必须原样来自相应原子输出的 `evidenceBindings`，不能把说明中的占位名称当实际 key。

`flow` 节点为 `{id,label}`，边为 `{source,target,label}`；节点 2～8 个、边 1～12 条，方向和含义须由审核内容支持。交叉机制是概念示意，不接收模型造出的日期、价格或序列。MACD 使用 DIF/DEA 语义，移动平均线交叉是另一个机制，不能替代。

provider-action 使用 chart_ref 引用知识 Provider 签发的固定行动卡，只能为唯一末块。不构造 URL；没有证据则省略卡片。核心业务链接不使用此类型，统一由 business_links_show 独立交付。

`series_ids` 只适用于折线，必须原样来自该证据的 `presentation.evidenceSeries[].id`，1～50 项且不重复；不能用指标名称代替 ID。未选数据仍保留在原始证据，Widget 会说明未选数量。省略则保留全部序列，过多的现货小图折叠在同一 Dashboard 中。`purpose` 最多 160 字，只描述问题/比较目的，不陈述新事实。无双轴、坐标上下界、单位覆盖、倍率或指数变换参数。
