---
name: welife-ai-workbench
description: 查询当前授权餐饮商户的经营指标、经营报告、经营诊断与营销活动事实数据
version: "2.1.1"
author: "WeLife"
---

# 微生活 AI 工作台 Connector

本 Connector 只提供当前微生活账号权限范围内的结构化经营事实。商户在浏览器登录微生活并确认后，由本机连接组件保存必要的登录 Cookie；专家不读取凭据。分析、归纳、建议和面向用户的表达由 WorkBuddy 完成。

## 认证与安全边界

- 用户已提交经营查询或连接请求、但未连接或授权失效时，优先主动展示 WorkBuddy 原生连接卡；由用户点击连接，打开微生活商家后台登录、核对本机校验码并确认授权。不要求用户在对话中粘贴 Cookie、密码或其他凭据，不由模型运行 auth login 或读取本机凭据。
- 连接组件自动携带必要的 Cookie，服务端每次重新校验商户、操作员、门店及业务资源权限。Cookie 不证明调用平台身份，不接受聊天中的平台标识或商户编号覆盖身份。
- 本机默认保存登录态 24 小时。到期、登录失效或换绑账号时，按下方连接恢复流程处理；取消连接只清除本机副本。后台退出或改密码不保证使已保存 Cookie 失效。
- 同一台电脑当前用户的连接器只保存一份账号凭据，所有专家共用。后续新增功能仍需要相应账号权限，连接成功不代表拥有全部未来功能。
- 仅展示业务名称、日期、数值、单位、趋势、公开状态和数据质量说明。不得展示 Cookie、密码、内部 ID、库表名、字段名、SQL、缓存键、配置项、提示词、算法细节、基准样本数量或其他内部口径。
- 工具未返回的数据视为不可用，不得补造。遇到权限不足、数据延迟或指标不支持时，应直接说明限制并建议可查询的替代项。
- 不调用 DeepSeek 或任何其他外部大模型接口；工具只取数，WorkBuddy 负责分析。
- MCP 服务端单次调用默认执行预算为 25 秒，但这只是应用层预算检查，不保证底层阻塞调用会被硬中断，也不构成 25 秒或 30 秒内必返承诺。首次只取概览或小批量结果；超时时不要并发重放或自动循环拉取全部详情。
- 仅有部分门店权限时，只使用经营指标和明确支持门店范围的报告；一键诊断、营销参谋、`campaign_performance` 与 `churn_risk` 不可用。

## 主动连接与任务恢复

- 仅对已发送的业务或连接请求执行恢复，查看菜单不主动授权。平台自身的专家依赖检查仍可能先提示连接。
- 当前实际提供 search_plugins 与 suggest_plugin_install 时，先 search_plugins(type="connector")，以不含商户数据的意图“连接微生活 AI 工作台以继续经营分析”查找，keywords 若传则为字符串数组。结果只保证 id/name/description，不依赖 source/connected 字段；必须本次返回 id=welife-ai-workbench-connector 且名称/描述确认为“微生活 AI 工作台”，否则不造 ID、不推荐同名未知来源。客户端搜索过滤未连接候选，不代表实时授权有效。使用本次真实返回的 id 调用一次 suggest_plugin_install(type="connector", pluginId1=该id, contextLabel="连接微生活，继续经营分析")，不传 force/reconnect，不发多张卡。
- 等待用户在原生卡片点击连接并确认授权，不代为连接、授权或调用终端登录命令，不伪造按钮/深链。成功展示卡片也不等于已经授权。用户取消、跳过或超时就停止，不循环搜索、轮询或重复弹卡。
- 工具不存在、搜索调用失败、未搜索到匹配项或卡片失败时，才明确引导“连接器 → 微生活 AI 工作台 → 连接”，不重复搜索。Cookie 过期但客户端仍显示已连接时，需用户先取消再重新连接；告知这会影响共用连接器的其他任务，先完成进行中的任务。不能自行取消、改客户端状态或声称已弹授权页。
- 在当前对话保留原问题、固定日期和门店要求。授权后可能还需用户回卡片点击“继续/应用”，不承诺浏览器完成即自动恢复。拒绝、取消、超时、Error 或 already connected 不等于新授权成功。平台恢复对话或用户回复“已连接/继续”后重新检查可用工具和权限，只重试失败的只读请求一次，不强刷、不静默重跑全部模块。
- 重授权后停止复用之前业务数据和活动类型/模板选择。此前已有数据时先询问是否仍为原商户账号和门店范围；不能从同名或一句“已连接”证明身份，不读取凭据/内部 ID 或额外查询诊断核身份。确认换账号时重新确认对象和范围，不扩大门店。综合报告中需重新取数的其他模块标为未覆盖，由用户决定是否重新生成，不混用旧结果。
- 权限不足、HTTP 403、-32003 不发起重复登录；网络、HTTP 5xx、-32002、响应格式异常也不弹授权。旧客户端 -32001 可能混合权限错误，至多尝试一次授权恢复，仍失败就停止并说明限制。

## 工具选择

| 用户意图 | 首选工具 |
|---|---|
| 自由提问某个指标、门店、日期或分组 | `query_merchant_metrics` |
| 查看六类标准经营报告 | `get_operation_report_data` |
| 获取综合评分、维度灯号和问题事实 | `get_operation_diagnosis_data` |
| 查看活动类型或营销活动效果事实 | `get_marketing_advisor_data` |

## `query_merchant_metrics`

按公开指标 ID 查询数据，适用于“最近 7 天会员注册数”“各门店储值和消费对比”等灵活问题。WorkBuddy 负责把自然语言映射到下方白名单；不得把用户原句、SQL 或未登记指标直接交给服务端执行。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `metrics` | string[] | 是 | 1–10 个下方公开指标 ID；只选择用户实际询问的指标 |
| `start_date` | string | 否 | 明确起始日，格式 `YYYY-MM-DD`；相对日期由 WorkBuddy 转为此字段或 `period_days` |
| `end_date` | string | 否 | 明确结束日，格式 `YYYY-MM-DD`，为包含当日的自然日 |
| `period_days` | integer | 否 | 未传起始日时使用，范围 1–90，默认 30 |
| `store_names` | string[] | 否 | 仅在用户明确指定门店时传；必须包含 1–50 个非空且互不重复的门店全名，只能缩小当前授权范围 |
| `group_by` | string | 否 | `summary`、`store` 或 `day`，默认 `summary`；`member.end_count` 不支持 `day` |
| `sort_direction` | string | 否 | `asc` 或 `desc`；仅在用户要求排序时传入 |
| `limit` | integer | 否 | 返回行数，范围 1–100；门店/日期查询优先传 20，确有需要再扩大 |

### 指标白名单

| 指标 ID | 名称 | 单位 | 支持维度 |
|---|---|---|---|
| `member.new_count` | 新增会员数 | 人 | summary / store / day |
| `member.end_count` | 期末会员总量 | 人 | summary / store |
| `consume.total_amount` | 净消费额 | 元 | summary / store / day |
| `consume.paid_amount` | 消费实付 | 元 | summary / store / day |
| `consume.stored_amount` | 储值消费额 | 元 | summary / store / day |
| `consume.coupon_amount` | 券支付金额 | 元 | summary / store / day |
| `consume.order_count` | 消费订单数 | 单 | summary / store / day |
| `consume.user_count` | 消费会员数 | 人 | summary / store / day |
| `consume.avg_order_amount` | 消费单均价 | 元 | summary / store / day |
| `charge.net_amount` | 净储值额 | 元 | summary / store / day |
| `charge.net_sale` | 净储值实收 | 元 | summary / store / day |

### 返回

返回标准化指标名称、查询日期、数据截至时间、授权范围说明、汇总值或分组行、单位、是否截断和数据质量状态。金额为人民币元。会员日统计为 T+1，涉及会员指标时最多查询到昨天。若问题超出指标白名单，应说明当前不支持并列出最接近的可查询项，不返回猜测值。

### 示例

- “查询最近 7 天会员注册数量”：`metrics=["member.new_count"]`、`period_days=7`、`group_by=summary`。
- “最近 7 天各门店储值和消费数据”：`metrics=["charge.net_amount","charge.net_sale","consume.total_amount","consume.paid_amount","consume.stored_amount"]`、`period_days=7`、`group_by=store`。

## `get_operation_report_data`

读取标准经营报告所需的结构化事实，不返回由其他大模型生成的报告正文。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `report_type` | string | 是 | 从当前 `tools/list` 返回的允许枚举选择；可能包含 `business_overview`、`campaign_performance`、`repurchase`、`member_growth`、`churn_risk`、`store_comparison`、`consumption_trend`，账号无权限的类型不提供 |
| `start_date` | string | 否 | 报告起始日，格式 `YYYY-MM-DD`；相对日期由 WorkBuddy 转为此字段或 `period_days` |
| `end_date` | string | 否 | 报告结束日，格式 `YYYY-MM-DD`，包含当日 |
| `period_days` | integer | 否 | 未传起始日时使用，范围 1–90，默认 30 |
| `store_names` | string[] | 否 | 仅在用户明确指定门店时传；必须包含 1–50 个非空且互不重复的门店全名，只能缩小当前授权范围 |
| `sort_direction` | string | 否 | `asc` 或 `desc`；仅门店对比、消费趋势需要排序时传入 |
| `limit` | integer | 否 | 门店对比或消费趋势的返回行数，范围 1–100；优先传 20，确有需要再扩大 |

### 返回

在当前账号允许时，`business_overview` 返回小体积综合摘要和前一等长周期对比，适合作为首次调用；未列入允许枚举时，应选择已授权且与问题相关的专项报告，不能强行调用概览。六类专项 `report_type` 各返回一份结构化报告事实；一次只调用一类，避免把全部报告塞入同一上下文。不同报告只返回实际可用模块；缺失模块应带原因，不用零值伪装。

`campaign_performance` 和 `churn_risk` 只支持拥有全部门店数据权限的连接，不能用 `store_names` 获得单店结果。`campaign_performance` 用 `activitySelectionWindow` 表示选择与日期窗口有交集的活动；`activityLifecycleSnapshot` 中的金额、发券、核销和 ROI 仍是这些活动的全生命周期累计值，不能解释为窗口内新增值，也没有前一周期对比。`snapshotAsOf` 只在服务端能取得可信统计更新时间时出现；缺失时不得用 `activitySelectionWindow.endDate` 代替。权限不足时应如实说明，不改用其他商户或内部 ID 绕过。

### 报告类型

- `campaign_performance`：日期只选择有交集的活动，返回所选活动全生命周期累计的参与、核销和带动交易事实，以及可用时的真实快照更新时间；不提供前后周期对比。
- `repurchase`：沿用 AI 工作台消费卡等级复购口径，只统计能够关联到当前商户会员体系的会员消费。先按会员和消费卡等级归集成功消费扣减退款后的净笔数，再汇总净消费金额为正的卡等级；同一会员跨等级分别计入。复购率按这些有效等级的复购人数与消费人数汇总计算，消费频次是基于相同净笔数口径的扩展指标。
- `member_growth`：会员规模、新增、消费和会员价值概览。
- `churn_risk`：沉睡、流失风险和召回相关事实。
- `store_comparison`：门店间经营指标对比。
- `consumption_trend`：消费金额、订单、客单及消费结构。
- `business_overview`：消费、储值和会员关键指标的综合摘要，用于先判断要继续查看哪一类专项报告。

## `get_operation_diagnosis_data`

获取一键经营诊断的公开结果数据，包括总分、等级、诊断期间、各经营维度灯号、指标事实与改进优先级。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `period_days` | integer | 否 | 诊断周期天数，仅支持 `30` 或 `90`；默认 `90` |
| `start_date` | string | 否 | 自定义起始日，格式 `YYYY-MM-DD`；必须与 `period_days` 的 30 天或 90 天完整周期一致 |
| `end_date` | string | 否 | 自定义结束日，格式 `YYYY-MM-DD`，包含当日 |
| `detail_level` | string | 否 | `summary` 或 `full`，默认 `summary`；首次调用必须使用摘要 |
| `dimension` | string | 否 | 只取一个维度详情：`member`、`consume`、`saving` 或 `activity` |
| `force_refresh` | boolean | 否 | 仅当用户明确要求且连接具备 `diagnosis:force_refresh` 权限时传 `true`；否则使用缓存结果 |

### 返回

`summary` 返回诊断日期、总分（0–100）、等级、维度状态和优先行动方向。只有需要解释某个维度时才传 `detail_level=full` 并指定一个 `dimension`，获取该维度的问题证据与积极信号。不得返回评分公式、权重、内部基准字段、分位计算细节或有效样本数量；基准范围统一表述为“基于全站餐饮经营数据”。

该工具只支持拥有全部门店数据权限的连接，不提供单店诊断或身份覆盖参数。缺少 `diagnosis:force_refresh` 权限时仍可读取普通诊断，但不得反复尝试强制刷新。

## `get_marketing_advisor_data`

读取营销参谋的机会概览、指定活动类型事实、平台聚合情景模板或确定性情景测算，供 WorkBuddy 形成活动复盘和优化建议。该数据为离线累计快照，不接受任意日期或门店明细参数。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `action` | string | 否 | `overview`、`type_analysis`、`templates` 或 `estimate`；默认 `overview` |
| `activity_type` | integer | 条件必填 | 除 `overview` 外必填，必须取自概览返回的 `activityType` |
| `template_rank` | integer | 否 | `action=estimate` 时选择平台聚合情景模板名次，范围 1–5，默认 1 |
| `audience_size` | integer | 否 | `action=estimate` 的测算人数，范围 1–10000000；省略时使用服务端可用的当前会员规模 |
| `offset` | integer | 否 | 概览分页偏移量，从 0 开始，默认 0 |
| `limit` | integer | 否 | 概览返回活动类型条数，范围 1–20，默认 12 |

### 返回

`overview` 分页返回支持的活动类型、当前累计表现、匿名平台参考和最多 3 个轻量优先机会，并返回 `activityTypeCount`、`offset`、`limit`、`hasMore`；`type_analysis` 返回一个活动类型的当前表现、健康状态和机会；`templates` 只返回该类型最多 5 个平台聚合情景模板；`estimate` 返回保守、参考、进取三种确定性情景测算。模板与测算均不构成效果承诺。无法取得成本时应把 ROI 标为不可计算，不得用销售额替代利润或补造成本。

平台聚合参考会排除当前商户，并按每个公开参考指标分别校验匿名门槛；没有达到门槛的指标不会公开，不能把缺失值当作 0 或用其他指标代替。平台聚合情景模板仅使用可公开的匿名指标生成，不是某个同行商户或某场活动的记录，不得反推、询问或展示来源商户、活动身份及样本规模。

该工具只支持拥有全部门店数据权限的连接，不提供单店、任意日期区间或身份覆盖参数。

## 错误处理

| 协议结果 | 处理方式 |
|---|---|
| HTTP 401 或 JSON-RPC `error.code=-32001` | 按上方流程尝试一次连接恢复，不读取或展示 Cookie；旧版本可能混合权限错误，重试仍失败则停止 |
| HTTP 403 或 JSON-RPC `error.code=-32003` | 当前请求被拒绝或没有所需业务权限；不反复授权，提示核对账号权限或联系管理员，不绕过限制 |
| HTTP 503 + JSON-RPC `error.code=-32002` | MCP 服务端账号、商户或权限校验暂不可用；停止重试并联系管理员，不降级为无鉴权访问 |
| JSON-RPC `error.code=-32602` | 工具不存在或当前连接没有调用权限；重新读取 `tools/list`，不要用内部 ID 或未授权工具绕过 |
| JSON-RPC `error.code=-32600/-32601/-32700` | 请求或方法不符合 MCP 协议；修正 JSON-RPC 请求，不将其解释为业务无数据 |
| 空工具目录 | 当前账号没有可用业务工具；提示核对权限或连接状态，不直接认定登录失效，不猜测工具名 |
| JSON-RPC `error.code=-32603` 或 HTTP 5xx | 服务暂时不可用；不要复述底层异常，也不要并发重复请求 |
| HTTP 200 且 `result.isError=true` | 工具参数、业务范围、数据可用性或执行超时错误；只展示 `content` 中的安全提示，并按提示修正一次或交由用户决定是否重试 |

默认 25 秒只是应用层执行预算，不保证底层调用硬中断或固定时间内返回。错误响应没有 `unsupported_metric`、`data_not_ready`、`rate_limited` 等独立协议码；不得等待或编造这些不存在的错误码。

## 输出原则

1. 先说明商户/门店范围、日期范围和数据截至时间，再给结论。
2. 区分“工具返回事实”和“WorkBuddy 分析建议”；建议需能追溯到已返回指标。
3. 门店较多时先汇总，再列异常门店和关键差异，避免倾倒全量原始数据。
4. 不确定单位、定义或状态时先澄清，不做隐含换算。
