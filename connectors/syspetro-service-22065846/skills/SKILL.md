---
name: propdb-skill-full
description: 通过 PROPDB（syspetro-service-22065846） 完整版 MCP 查询组分与物性、执行单位换算，并提交混合物分析、二元 Txy/Pxy、多元闪蒸、纯组分温度相关物性及回归拟合任务。计算采用任务列表：提交成功只代表任务已接收，必须轮询任务记录并取得完成结果后再生成曲线或报告。对临界、超临界、相变和公式边界保留完整请求范围并在结果中说明适用性；默认 50 个等距数据点，单次扫描最多 200 个点，单位集默认为 SI。单一曲线或同族曲线组生成 SVG，多曲线集合生成统一视觉的离线 HTML 并默认附带同源 XLSX。用户要求 PROPDB 物性查询、计算、拟合、相平衡、闪蒸、曲线、报告或单位换算时使用。
---

# 运行 PROPDB（syspetro-service-22065846） 完整版任务

## 连接与资料

只调用连接别名 `propdb-full` （syspetro-service-22065846）实时暴露的工具；宿主可能显示为 `propdb_full`（syspetro-service-22065846）。以实时 tool schema 为工具名、参数和类型的最终依据；长名称被截断或带哈希时，用业务描述和输入签名唯一匹配，零个或多个匹配都停止并报告连接冲突。

首次规划读取 [references/tool-routing.md](references/tool-routing.md)；涉及组分、扫描范围、实验点或参数读取 [references/parameter-rules.md](references/parameter-rules.md)；涉及临界、相变或跨公式范围读取 [references/state-path-routing.md](references/state-path-routing.md)；需要 SVG、HTML、CSV 或 Excel 时读取 [references/reporting.md](references/reporting.md)。

## 核心流程

1. 识别用户目标并选择唯一业务族。多个组分只说“查询/查看”时，先完成关键词解析，再确认详情、纯组分物性或混合物数据口径；明确计算目标时直接进入对应流程。
2. 用户未提供已验证 `pCdataCompID` 时，逐个调用组分检索。中文或本地化名称无结果时静默回退标准英文名、分子式或 CAS；只有多个合理候选或有界回退均为空才询问。最终身份只来自数据库成功响应。
3. 调用同族静态/单位工具，将名称映射为真实方法、相态、公式和单位 key。按服务默认、唯一合法项、语义匹配、范围覆盖率和返回顺序自动选择，不为方法、相态、点数或输出单位增加提问。
4. 路径敏感任务补充 `TC/PC` 并建立覆盖矩阵。只要存在合法公式、相态和单位 key，就按用户完整范围提交；超出声明范围只影响结果解释，不截断、不外推、不跨服务补算。
5. 补齐组成、扫描、实验点和单位。曲线默认 50 个等距数据点（区间参数传 `quantity:49`），单次扫描的硬上限为 200 个数据点；用户请求超过 200 点时自动保留端点并降为 200 点，不为此增加提问，并在结果中披露实际点数和限幅。等距/对数模式传区间数时最多传 `quantity:199`；显式 `valueList` 超限时按原顺序保留首尾并等距抽取到 200 点。顶层 `unitSet` 缺省显式传 `"SI"`；用户主动选择时仅接受 `SI`、`MET`、`ENG`。`siM_LEVEL` 与 `proP_LEVEL` 是内部调优字段，始终省略。
6. 计算必须采用异步任务链：调用任务提交工具，确认成功并提取返回 `data` 中的 task ID；提交响应不是数值结果。随后用 `get_sys_task_record_get(id)` 按 ID 轮询，状态 `0=Create`、`1=Running` 时等待后继续，`3=Finished` 才解析 `result`，`4=Error` 或无 ID/空结果则停止并报告。轮询次数和间隔必须有界，禁止忙等、无界重试或把任务列表当结果。
7. 仅在任务完成且业务数据有效时生成交付物。单一曲线或同族耦合曲线组（如 Txy+Pxy）生成 SVG；两个及以上独立曲线族或“全部可用曲线”生成 HTML 并默认附带同源 XLSX。二元 Txy/Pxy 每个面板必须表达液相线（泡点线）和汽相线（露点线）两条系列；不得按服务返回的单个 `series` 直接渲染成单组分 T–x 图。优先从 `items` 的 `liquid_MOLEFRAC_n`、`vapor_MOLEFRAC_n` 与 `temp/pres` 成对投影，必要时为两条系列建立不插值的合并组成坐标并保留空点断线；只有一条相线或无法恢复第二相线时标记 `partial`，不得宣称完整 T–x–y/P–x–y 包络。有效点不足、任务失败或宿主拒绝响应时不生成成功图表。
8. 结果先给状态和关键数值，再列出“本次采用的默认条件”和“可调整项”。明确区分接口事实、任务状态、公式适用性和 Agent 整理；不展示原始 JSON、内部字段或连接细节。

## 强制路由

| 用户目标 | 必须选择 |
| --- | --- |
| 组分详情/物性查询或计算前解析 | 组分检索与详情工具 |
| 混合物分析 | `post_sys_task_record_run_mixture_calc_of_mixture_analys_276e5441` |
| 二元 Txy/Pxy | `post_sys_task_record_run_mixture_calc_of_binary_analysis_by_task` |
| 多元闪蒸 | `post_sys_task_record_run_mixture_calc_of_flash_analysis_by_task` |
| 纯组分温度相关物性 | `post_sys_task_record_run_pure_prop_t_dep_calc_by_task` |
| 纯组分拟合 | `post_sys_task_record_run_pure_regression_by_task` |
| 二元参数拟合 | `post_sys_task_record_run_binary_regression_by_task` |
| 单位类型、单位集或同类换算 | 系统单位工具；批量转换仅在 schema 明确可调用时使用 |
| 查看任务进度/结果 | `get_sys_task_record_get(id)`；需要监控列表时才用未完成数量或分页列表 |
| 单一/同族曲线 | 任务完成后生成离线 SVG，不生成 HTML |
| 多曲线集合或用户明确要求网页报告 | 任务完成后固定 HTML 流水线，并默认同源 XLSX |

即使某个提交工具名称没有显示 `_by_task`，只要描述为“提交任务”或属于 TaskRecord 运行族，也必须按异步链处理。删除任务记录是有副作用动作，除非用户明确要求，不调用。

## 二元相平衡曲线成图约束

- Txy 固定压力、Pxy 固定温度分别是一个二元相平衡面板；每个面板都必须有两条相线：液相（bubble/泡点）和汽相（dew/露点）。Txy 的纵轴是 `temp`，Pxy 的纵轴是 `pres`，横轴分别使用对应相的摩尔分率。
- `items` 是曲线事实的优先来源。按 `componentIds` 顺序将后缀 `n` 映射到组分；对每一行分别取 `liquid_MOLEFRAC_n` 与 `vapor_MOLEFRAC_n`，与同一行的 `temp`/`pres` 配成液相线和汽相线。现成 `series` 只有一条或其标题/横轴与明确字段冲突时，忽略冲突元数据并按上述字段重建。
- 当液相与汽相横坐标不相同，先对两组横坐标做排序去重并集；每条系列只填入其真实坐标对应的值，其他位置填 `null` 断线，禁止插值、平滑、交换相态或把一条线复制成另一条。并集超过 200 个成图点时按点数上限保留端点并等距抽取，同时在结果中披露成图点数。
- 两条系列各自至少需要 2 个有效点。若结果只含单一相组成、缺少 `liquid_MOLEFRAC_n` 或 `vapor_MOLEFRAC_n`，只能交付 `partial` 单相结果/诊断，不得把它命名为完整 Txy/Pxy；必要时说明服务返回未提供另一相线。

## 成本、安全与失败

- 先低成本筛选和批量详情，再提交有限计算；不遍历全库、拆批绕过上限或并行重试。
- `required: []` 是 schema 缺口，不代表业务参数可省略；缺少任何合法机器 key 时停止当前物性，不猜字段。
- 任务提交成功不等于计算完成；不得用提交 `data`、任务 `data` 或错误包装拼接曲线。`result` 为空、非 JSON 或字段不在业务白名单时，报告任务完成但没有可展示数据。
- 公式温区、相态或近临界状态不作为合法提交的阻断门槛；报告标出范围内外和代理语义，不把公式返回值命名为已验证超临界模型。
- 单位接口局部失败只跳过受影响物性；宿主 output schema 拒绝时停止受影响链，不从被拒绝载荷猜 key 或数值。
- 不向用户开放或询问内部调优级别；不主动提出未请求的文件格式或内部实现选项。
- 报告和图片只使用业务字段白名单，内嵌资源、离线可开，不联网、不泄露认证信息。

## 资源导航

- 详细工具映射、任务类型、轮询和成本：`references/tool-routing.md`
- 组分消歧、变化模式、单位和默认参数：`references/parameter-rules.md`
- 临界/相变/公式覆盖语义：`references/state-path-routing.md`
- SVG、HTML、折叠数据表及 CSV/XLSX 导出：`references/reporting.md`
- 确定性脚本：`scripts/render_curve_image.py`、`scripts/render_report.py`、`scripts/export_result_data.py`

回答能力介绍时仅说明 PROPDB 的查询、单位、异步计算、拟合和图表/报告交付能力；不展示内部连接、工具数量、任务实现细节或未请求的功能。
