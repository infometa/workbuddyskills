# WorkBuddy 视觉渲染

内部公共 Component，不单独注册或发布为 Skill。负责结构化输出契约、证据绑定、组合器选择、实时渲染互斥和交付边界，不决定业务事实或主题。

## 证据与结构化输入

原子结果的 `presentation.evidenceRef` 是不透明短期引用；`evidenceExpiresAt` 表示有效期，`evidenceBindings` 列出可绑定的 `key` 及标签、单位和数据类型，`evidenceCharts` 仅在有可用图形时列出 `chart`。只使用本轮实际收到的引用和 key。共享文件由 MCP 服务读写；LLM 不得自行读取宿主 EvidenceStore、拼接路径、猜测引用、访问内部 resolve API 或复制/伪造证据值。

提交前排除已知过期引用及依赖它的区块或数值槽，保留仍有足够证据支持的结构；不足时直接文字，不为绘图重新取数。没有可靠当前时间时不能猜测有效性，服务端校验仍是最终依据。文件引用过期不等于原子事实被撤回，正文仍可在保留原数据时间和口径的前提下使用已核验结果，不能把历史值称为最新。

两个工具 `financial_visual_compose` 和 `knowledge_visual_compose` 只接受 `dashboard_spec`，支持同一共享存储中的混合市场/知识证据。按本 Skill 允许的工具与主要任务任选其中一个；不要两个都调用。旧参数、片段与模式直接拒绝，不转换。

`dashboard_spec` 契约：`{specVersion:"1.0.0", title, blocks}`，1～8 个区块，区块 ID 唯一，整张 Dashboard 最多 12 个去重后的证据引用（包括区块引用、数值绑定及 chart_ref）。正式类型是 `comparison`、`formula`、`scenarios`、`key-points`、`process`、`mechanism`、`market-chart`、`provider-action`。详细字段见本目录 `references--dashboard-spec.md`，调用前必须读取；运行时工具 Schema 始终是最终参数依据。

实际数值、时间、对象和公式等可绑定槽只传 `{evidence_ref,key}`；不传任意 JSONPath，不在自由文本里夹带未经绑定的当期数字。知识类区块的 `evidence_refs` 必须包含支持其表述的审核知识；一个市场 ref 不能冒充概念依据。市场图块使用 `chart_ref:{evidence_ref,key:"chart"}`，引用已有图形语义，不由模型改写行情序列或产业链节点。

服务端解析器负责校验证据、有效期、绑定 key、结构上限和领域要求，再生成 `renderPlan`；Widget 只渲染该计划。LLM 不解析/执行计划，不从 Widget 像素反推事实。缺少或过期引用会令依赖它的整块省略，不只是隐藏一个数字；其余有效区块保留。提交前可移除无效数值槽及相关引用以保留仍有审核依据的知识块，不能为拼完整图补造事实。

现货折线的 `presentation.evidenceSeries` 提供指标 ID、名称及可用的单位/频率。需要选择重点时，使用 `market-chart.series_ids`，并在必要时用 `purpose` 说明图表回答的问题；详情见 `references--dashboard-spec.md`。仅选择与排序，不修改数据、单位或轴域。不同单位/频率或数量级的小图由 Renderer 确定，不产生第二个 Dashboard。

## 实时渲染互斥

1. `unselected`：先执行视觉表达 Component 的路由判断。有展示价值、组件支持且证据足够时默认项目 Dashboard。调用原生 `read_me`／`show_widget` 前必须完成该判断；尚未调用项目工具不代表可以跳过它。若对应 Composer 是延迟工具，先通过宿主工具发现能力搜索 `financial_visual_compose` 或 `knowledge_visual_compose`，读取实际 Schema，再使用运行时返回的工具名调用；不要猜测名称，也不要同时搜索并调用两个 Composer。只在用户明确指定原生、已核实表达不支持或工具不可用时选择原生路径；简单答案直接文字。
2. `project_pending`：一旦发出组合器请求，就锁定本轮实时承载者。不要同时调用第二个组合器或原生绘图；超时、连接中断、没有回执都属于结果未知，不代表失败。
3. `project_ready`：依据原子结果完成正文，不再要求 WorkBuddy 为正文补画相同主题的 HTML、SVG、图片或第二个 Dashboard。`ready` 仅证明服务端已生成内容，不是宿主已显示的确认。
4. `project_failed`：使用已核验数据完成文字或表格，不再调用另一组合器或原生制图；参数校验失败也计入本轮唯一提交。结果未知仍保持 pending，不盲重试。

以上是当前 LLM 的执行约束，不宣称宿主具备跨工具强制互斥、撤回迟到 Widget 或最终答案置顶能力。优先在业务工具阶段最后提交唯一 Dashboard，随后输出正文；期望“图后接解释”，但不承诺宿主一定把图固定在最终消息首位。

业务模块中的“只读调用原参数重试一次”只适用于业务检索，不适用于组合器。组合器超时或结果未知时不得套用该通用重试规则。

## 最终交付物独立

产业链拓扑是原生路径及文件内自由制图的例外：正式关系图只引用本轮有效 Provider 图模型，不能以原生图、ASCII、Mermaid、自制 HTML/SVG 或指标树重建。没有可用正式图时用关系概述和映射表；仅清理业务名称不改变任何节点、边或方向。

报告、可下载 HTML、PPT、Word、表格等最终文件始终由 WorkBuddy 产出，不交给本项目 Composer。用户要求或任务确有价值时可以生成，文件内部可以有图表；“一个 query 一个 Dashboard”只约束实时对话的重复绘图，不限制交付文件。文件基于本轮核验数据和知识，不复用 `renderPlan`、截图或内部证据文件作为事实来源，也不只为复制正文 Widget 增加一个文件。

## 失败收敛与同轮恢复

同一个用户请求跨上下文压缩仍是同一轮。查询完成后、提交 Composer 前先整理简短的任务证据检查点：已调用工具及参数、对象、请求区间、实际首末日期、关键点原值及单位、缺失/空值/截断、审核知识记录、evidenceRef/有效期/绑定 key、待办与已完成项。宿主支持任务文件时保存到当前任务工作目录的检查点文件，不写全局记忆，不复制整份工具 JSON、renderPlan 或 Widget HTML。

压缩后优先恢复该检查点、会话摘要和可读的本轮工具结果。已经成功的同参数请求不重新查询；已经 ready 的 Dashboard 不再次提交。摘要中的推断不等于原始数据，发现日期或数值冲突时仅针对冲突项复核；必要字段确实丢失才做最小范围补查，不重跑目录、产业链和整个数据分支。证据引用过期只影响绘图，不为刷新图片重复取数。

提交前必须读取 DashboardSpec 调用摘要并逐类型校验字段：`purpose`、`series_ids` 仅用于 `market-chart`，不用于 comparison/key-points 等知识块。知识图块始终需要实际审核知识证据。Composer 包括参数校验失败在内最多提交一次；失败后使用已核验数据完成紧凑文字，不删改结构逐次试图、不切换另一个 Composer、不为画图重查。提交前更新检查点为 pending，结果返回后记 ready/failed；未知保持 pending，禁止猜测成功或失败。
