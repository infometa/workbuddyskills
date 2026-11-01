# MCP 工具输入与输出约定

本文件覆盖 `ligowin-mcp-service` 的七个查询工具，依据 2026-09-22 后端请求模型、响应模型及服务实现核对。输入 schema 提供结构约束，本文件补充校验器和业务逻辑中的规则；服务升级后需同步复核，不将旧文档作为覆盖实际工具定义的依据。

## 公共结构

直接通过 MCP 工具传入参数对象。下文“必填”指字段是否必须提供；`null` 与省略分别说明。日期使用 `YYYY-MM-DD`，日期时间为 ISO 8601 字符串。数值类型指 JSON number，整数为 integer。

- 成功时 `isError=false`，`structuredContent` 为 `{"message":"查询成功或ok","data":...}`，其中 `message` 为 string，`data` 按各工具定义。`content` 的文本 JSON 表达同一业务结果；客户端仅提供文本时解析文本，不重复计算两份结果。
- 当前 MCP 未声明 `outputSchema`。下表是后端静态响应模型及业务数据的说明，不表示客户端已经获得或强制执行输出 schema。
- 分页工具的记录位于 `data.items`；`data.pagination.total` 是当前筛选和截断规则下的总数，`page` 为当前页，`page_size` 为每页上限。三者均为非空 integer。不能将条目字段误读成 `data` 的直接字段。
- 工具业务失败时 `isError=true`，结构化结果通常含 `detail.code: string`、`detail.message: string`、`status_code: integer`、`request_id: string`；`detail` 也可能是字符串或校验详情，按实际结构读取。未知工具等协议错误可能只有错误文本；OAuth 无效可在协议入口直接返回 HTTP 401，而非上述工具结果。
- 无权限、限流、超时及服务异常不能当作空数据；返回 `null`、缺失字段、空字符串也不能自行补成零。统计服务可能以“该查询条件下统计数据均为零”返回业务错误，与成功的空数组不同。
- 表中嵌套字段的“可为 null”以父对象存在为前提；父对象为 null 时不要求子路径存在。对象表示字典，动态指标和分析要素不保证固定键集合。

## stats_metricsdef

用途：查询当前用户角色可见的指标键、名称和解释，为后续统计选取指标并确认口径。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `metric_keys` | `array<string>/null` | 否 | `null` | 限定指标键；省略/null/空列表时不额外按键筛选 |
| `metric_groups` | `array<string>/null` | 否 | `null` | all（全部）、workforce（人力）、strategy（策略）、community（项目）、rank（排名）；省略/null/空列表时使用当前角色的 all 分组 |

### 约束与口径

- `metric_keys` 与 `metric_groups` 共同限定范围：先取得分组中的指标，再用键列表筛选；不是两者结果求并集。不属于可用分组或指标配置的 key 不返回，结果可能为 `{}`。
- 返回值受用户角色影响；不要将指标键和名称写死为全平台统一清单。此工具拒绝未声明字段。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `object` | 否 | metric_key 到指标定义对象的映射 |
| `data.{metric_key}` | `object` | 否 | 指标信息模型 |
| `data.{metric_key}.name` | `string` | 否 | 指标名称 |
| `data.{metric_key}.explain` | `string` | 否 | 指标说明 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "metric_groups": [
    "community"
  ]
}
```

## stats_operation

用途：查询指定项目一个周期内的运营指标及归因明细。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `period` | `string` | 是 | 无 | daily（日）、weekly（周）、monthly（月）；从 start_date 开始计算一个周期 |
| `community_names` | `array<string>` | 是 | 无 | 项目全名列表；回款查询精确匹配，统计查询解析可访问项目；最少项数 1 |
| `start_date` | `string` | 是 | 无 | YYYY-MM-DD；统计起始日不得晚于服务端当天 |

### 约束与口径

- `community_names` 去除空白、空项和重复项后仍须非空。服务端解析项目并执行当前用户的数据权限检查，不存在或无权访问可能返回业务错误。
- 统计范围为 `[start_date, 周期结束日)`：daily 加1天，weekly 加7天，monthly 加1个日历月；不是自动对齐到本周周一或当月1日。查询自然月时明确使用月初，不传 `end_date`。
- `metrics` 按归因层次组织，叶子可能是格式化字符串，容器可能含 value/children；不能假定每个指标都是可直接求和的数字。按指标定义理解，不把各层重复累计。
- 结果超过服务端 `max_tool_data_count` 时会按实现中的案件量排序保留部分项目；配置默认1000，部署可调整。无分页和截断标志，不能仅凭成功响应宣称全量；应缩小项目范围。此工具拒绝未声明字段。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `array<object>` | 否 | 业务结果，结构见以下字段 |
| `data[].community_name` | `string` | 否 | 项目/小区名称 |
| `data[].metrics` | `object` | 否 | 动态指标及归因结构；值可能是格式化字符串或嵌套对象，不能假设固定数值类型 |
| `data[].metrics.{key}` | `any` | 由实际值决定 | 动态键对应的值，含义按所属对象或指标定义解释 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "period": "monthly",
  "community_names": [
    "示例项目"
  ],
  "start_date": "2026-08-01"
}
```

## stats_workforce

用途：按员工或部门查询当前权限范围内的人力效能指标。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `period` | `string` | 是 | 无 | daily（日）、weekly（周）、monthly（月）；从 start_date 开始计算一个周期 |
| `start_date` | `string` | 是 | 无 | YYYY-MM-DD；统计起始日不得晚于服务端当天 |
| `aggregation` | `string` | 是 | 无 | by_user（按员工）或 by_department（按部门）；实际可用聚合和数据范围受用户角色限制 |

### 约束与口径

- 周期区间与 stats_operation 相同，`start_date` 是窗口起点，不自动对齐自然周/月；不传 `end_date`。
- 不接受任意员工、部门或公司筛选字段。查询范围由当前用户角色及机构、部门、运营单元等权限确定；schema 允许的 aggregation 也可能被具体角色权限拒绝。
- `name`、`department_name` 可为 null；按 aggregation 理解对象，不假定员工和部门查询都会填齐二者。`metrics` 为动态归因结构，解释方式同项目统计。
- 超过服务端 `max_tool_data_count` 时按实现中的案件量排序保留部分记录；配置默认1000，可调整。没有分页或截断标志，结果可能不完整。此工具拒绝未声明字段。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `array<object>` | 否 | 业务结果，结构见以下字段 |
| `data[].name` | `string/null` | 是 | 用户姓名或部门名称 |
| `data[].department_name` | `string/null` | 是 | 部门名称 |
| `data[].metrics` | `object` | 否 | 动态指标及归因结构；值可能是格式化字符串或嵌套对象，不能假设固定数值类型 |
| `data[].metrics.{key}` | `any` | 由实际值决定 | 动态键对应的值，含义按所属对象或指标定义解释 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "period": "weekly",
  "start_date": "2026-08-03",
  "aggregation": "by_department"
}
```

## stats_pivot_table

用途：按指定维度、指标和时间区间查询透视统计。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `dimension` | `string` | 是 | 无 | employee（员工）、department（部门）、community（项目）、time_day（日）、time_week（周）、time_month（月） |
| `metrics` | `array<string>` | 是 | 无 | 指标 key 数组，先查询指标定义；非空，最多20项；服务端去重并验证指标与维度的兼容性；最少项数 1，最多项数 20 |
| `start_date` | `string` | 是 | 无 | YYYY-MM-DD；统计起始日不得晚于服务端当天 |
| `end_date` | `string` | 是 | 无 | YYYY-MM-DD；统计结束日，不含当天，必须严格晚于 start_date |
| `account_names` | `null` | 禁止 | 必须省略 | 禁止传入，包含 null 也会拒绝；此字段虽出现在 inputSchema，实际校验要求省略 |
| `community_names` | `array<string>/null` | 否 | `null` | 项目全名列表；回款查询精确匹配，统计查询解析可访问项目 |
| `company_names` | `array<string>/null` | 否 | `null` | 公司全名列表；回款查询精确匹配，透视查询解析为权限范围内的公司 |
| `area_names` | `array<string>/null` | 否 | `null` | 片区名称列表，透视查询解析其下公司 |
| `group_names` | `array<string>/null` | 否 | `null` | 物业集团名称列表，透视查询解析其下公司 |
| `user_names` | `array<string>/null` | 否 | `null` | 员工名称列表，解析为可访问员工 |
| `department_names` | `array<string>/null` | 否 | `null` | 部门名称列表，解析为可访问部门 |

### 约束与口径

- 日期范围为 `[start_date, end_date)`；`start_date` 不晚于当天，`end_date` 严格晚于起始日。`time_day` 最多查询60天。指标列表先校验1至20项，再去重；不保证按输入指标顺序返回。
- schema 中的 `account_names: null` 不是可用参数，必须省略。当前工具也不支持 account 维度。
- 指标须存在于统计配置；cover、rotate、interval 类型指标仅能用于 community 维度，其他不匹配组合会被拒绝。
- 名称过滤先转换为权限范围内的内部对象；未找到对应项目、公司或人员等会返回业务错误。company_names、area_names、group_names 都映射到公司筛选：当前实现依次赋值，后者覆盖前者，不表示三者交集；同次查询优先只选其中一种。部门/员工等组合结果以服务端规则为准，不推断额外的并集或交集行为。
- 返回行只有 dimension_name 是固定声明字段，其余指标列及附加信息动态展开；没有固定的 metrics 包裹层。列名和值类型以实际返回及指标定义为准。
- 行数上限为 `floor(max_tool_data_count × 30 / 去重后指标数)`，超出后仅保留前部行；配置默认 max_tool_data_count=1000，可调整。没有分页或截断标志，不保证全量。除受禁止字段特殊处理外，此工具拒绝未声明字段。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `array<object>` | 否 | 业务结果，结构见以下字段 |
| `data[].dimension_name` | `string` | 否 | 维度展示名称，其余列动态展开 |
| `data[].{动态列}` | `any` | 由实际值决定 | 请求指标及附加信息展开后的列；不是固定 schema 字段 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "dimension": "department",
  "metrics": [
    "num_calls"
  ],
  "start_date": "2026-08-01",
  "end_date": "2026-09-01"
}
```

## report_collection_insights

用途：分页查询案件、回款及动作统计，取得动作查询所需的案件公开 ID。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `company_names` | `array<string>/null` | 否 | `null` | 公司全名列表；回款查询精确匹配，透视查询解析为权限范围内的公司 |
| `community_names` | `array<string>/null` | 否 | `null` | 项目全名列表；回款查询精确匹配，统计查询解析可访问项目 |
| `statuses` | `array<string>/null` | 否 | `null` | 案件状态代码列表，有效值及省略行为见下文；不是中文展示状态 |
| `action_date_from` | `string(date)/null` | 否 | `null` | 动作窗口开始日，包含当天；未传则无下界 |
| `action_date_to` | `string(date)/null` | 否 | `null` | 动作窗口结束日，包含当天；未传则无上界。回款查询另用此字段作为对账累计截止日期 |
| `page` | `integer` | 否 | `1` | 页码，从1开始；最小值 1 |
| `page_size` | `integer` | 否 | `200` | 每页记录上限，1至200；最小值 1，最大值 200 |

### 约束与口径

- company_names、community_names、statuses 清理空白、空项和重复项后至少一项非空。即使 schema 将三者都标成可选，也不能全部省略。
- 有效状态：UNASSIGNED（未分配）、FOLLOWING（在催中）、TRANSFERING（流转中）、PENDING（挂起）、LEGAL（送诉）、COMPLETED（已完成催管）、SUSPENDED（已终止）、CLOSED（已对账）。固定排除 ARCHIVED、UPDATED、LAWYER。非空指定状态列表经过有效状态过滤后为空时，结果为空；混合状态只保留有效项，不保证报参数错误。
- 省略/null/清理后为空的 statuses 使用上述全部有效状态，不默认 FOLLOWING。输出 status 是中文展示名称，不能原样当作输入代码。
- action_date_from/to 影响动作计数、标签汇总以及窗口内首末动作/通话时间，不是案件创建日期或欠费日期过滤。结束日期包含整日。应提供有序日期，当前请求模型未声明两者先后关系校验。
- 对账金额按关联对账动作时间累计至 action_date_to（含当天）；不使用 action_date_from。未指定截止日期时累计全部相关时间。金额按当前对账状态分组，不是还原截止日的历史状态快照。
- total_recon_amount 仅为当前状态 PENDING 的金额；total_paid_amount 仅为当前状态 APPROVED 的金额。两者不是“所有提交金额”和“其中已完成金额”的包含关系。驳回等其他状态不计入这两项。
- 返回字段中的案件资料和状态是当前数据；日期窗口不能使它们变成历史快照。权限过滤后分页，空结果仍为合法分页响应。
- 当前请求模型忽略未声明字段，而非拒绝；调用仍只传文档列出的字段，不能依赖额外字段产生过滤效果。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `object` | 否 | 业务结果，结构见以下字段 |
| `data.items` | `array<object>` | 否 | 本页记录列表 |
| `data.items[].account_public_id` | `string` | 否 | 案件公开ID；用于后续动作查询，不解码猜测内部ID |
| `data.items[].family_public_id` | `string/null` | 是 | 案件分组公开 ID；同组案件的分组 ID 相同，不存在同组案件时为空 |
| `data.items[].user_public_id` | `string/null` | 是 | 案件经办人公开 ID，未分配时为空 |
| `data.items[].company_name` | `string` | 否 | 物业公司名称 |
| `data.items[].district_name` | `string` | 否 | 片区名称 |
| `data.items[].community_name` | `string` | 否 | 项目/小区名称 |
| `data.items[].building` | `string` | 否 | 楼栋 |
| `data.items[].room_num` | `string` | 否 | 房号 |
| `data.items[].created_at` | `string(date-time)/null` | 是 | 案件创建时间 |
| `data.items[].updated_at` | `string(date-time)/null` | 是 | 案件更新时间 |
| `data.items[].owe_start_date` | `string(date)/null` | 是 | 欠费起始日期 |
| `data.items[].owe_end_date` | `string(date)/null` | 是 | 欠费截止日期 |
| `data.items[].owe_amount` | `number/null` | 是 | 欠费金额（元） |
| `data.items[].penalty_amount` | `number/null` | 是 | 违约金金额（元） |
| `data.items[].score_level` | `string` | 否 | 案件评分等级 |
| `data.items[].status` | `string` | 否 | 当前案件中文展示状态，不是输入所需代码 |
| `data.items[].debt_reasons` | `array<string>` | 否 | 窗口内欠费原因标签展示值集合 |
| `data.items[].interaction_results` | `array<string>` | 否 | 窗口内交互结果标签展示值集合 |
| `data.items[].core_motivation` | `string` | 否 | 欠费核心动机展示值 |
| `data.items[].is_property_withdrawal` | `boolean` | 否 | 是否物业退场项目 |
| `data.items[].is_important` | `boolean` | 否 | 是否重点关注 |
| `data.items[].is_valid_debt` | `boolean` | 否 | 是否有效债务 |
| `data.items[].first_call_at` | `string(date-time)/null` | 是 | 所选动作窗口内首次电话时间 |
| `data.items[].last_call_at` | `string(date-time)/null` | 是 | 所选动作窗口内最后电话时间 |
| `data.items[].first_action_at` | `string(date-time)/null` | 是 | 所选动作窗口内首次动作时间 |
| `data.items[].last_action_at` | `string(date-time)/null` | 是 | 所选动作窗口内最后动作时间 |
| `data.items[].total_recon_amount` | `number` | 否 | 截至 action_date_to、当前状态为 PENDING 的对账金额（元） |
| `data.items[].total_paid_amount` | `number` | 否 | 截至 action_date_to、当前状态为 APPROVED 的对账金额（元） |
| `data.items[].call_count` | `integer` | 否 | 所选动作窗口内电话次数 |
| `data.items[].connected_count` | `integer` | 否 | 所选动作窗口内已接通电话次数 |
| `data.pagination` | `object` | 否 | 当前分页信息 |
| `data.pagination.total` | `integer` | 否 | 当前查询规则下的记录总数 |
| `data.pagination.page` | `integer` | 否 | 当前页码 |
| `data.pagination.page_size` | `integer` | 否 | 每页记录上限 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "community_names": [
    "示例项目"
  ],
  "action_date_from": "2026-08-01",
  "action_date_to": "2026-08-31",
  "page": 1,
  "page_size": 50
}
```

## action_list

用途：分页查询可读案件的动作及关联明细。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `account_public_ids` | `array<string>` | 是 | 无 | 非空案件公开ID数组，从回款查询 data.items[].account_public_id 获取；不得猜测或跨应用复用 |
| `action_types` | `array<string>/null` | 否 | `null` | call（电话）、property（物业跟进）、reminder（法催函件）、sms（短信）、label_change（标签变更）、accountrecon（对账）；省略/null/空列表使用全部六类 |
| `action_date_from` | `string(date)/null` | 否 | `null` | 动作窗口开始日，包含当天；未传则无下界 |
| `action_date_to` | `string(date)/null` | 否 | `null` | 动作窗口结束日，包含当天；未传则无上界。回款查询另用此字段作为对账累计截止日期 |
| `max_actions` | `integer` | 否 | `6` | 默认模式每案件最多返回的最近动作数；1至50，最近记录模式不使用此上限；最小值 1，最大值 50 |
| `only_last_connected_call` | `boolean` | 否 | `false` | 仅取各案件在指定日期窗口内最近一次已接通电话；还受 action_types 限制 |
| `only_last_property_service` | `boolean` | 否 | `false` | 仅取各案件在指定日期窗口内最近一次物业跟进；可与电话最近记录组合 |
| `with_call_analysis` | `boolean` | 否 | `false` | 是否附带话术质检结果；开启也不保证每条通话有结果 |
| `page` | `integer` | 否 | `1` | 页码，从1开始；最小值 1 |
| `page_size` | `integer` | 否 | `200` | 每页记录上限，1至200；最小值 1，最大值 200 |

### 约束与口径

- account_public_ids 清理空白、空项和重复项后不能为空；ID 属于特定应用，应使用当前连接返回的公开 ID。服务端解码后按当前用户可读案件筛选，不保证所有提交的 ID 都有记录。
- action_types 只允许表中六个值；非法值会拒绝。动作结束日期包含整日；日期参数应有序，当前请求模型未声明起止先后关系校验。
- 默认模式在案件、日期及类型过滤后，对每个案件按动作ID倒序取最多 max_actions 条，再进行全局分页；total 是截断后的合并条数。所有页取完也不代表全部历史动作。
- 任一 only_last_* 为 true 时进入最近记录模式，按案件和相应类型选窗口内最大动作ID；两者开启取两类记录并集，max_actions 不参与截断。action_types 仍生效：排除了 call 就不会返回最近电话，排除了 property 就不会返回最近物业跟进；不返回其他类型。
- 对账动作必须有关联对账记录且未驳回才返回。call、property_service、label_change、accountrecon 按动作类型和实际关联记录填充，否则可为 null。
- call_analysis 仅在 with_call_analysis=true 且有分析结果或配置摘要时填充。features/completion_rate 来自相关分析配置的累计摘要，不等于本次通话独立得分；extracted_fields 来自本次通话最新分析结果，不是累计值。动态要素中文名读取 data.call_analysis_labels，部分要素可能没有标签。
- call 中的 damage_amount、has_damage_evidence、blame、domain 来自通话分析提取字段，缺失或无法解析时按对应字段返回 null 或 N/A；不要臆测事实。has_dialogue 只是是否存在转写的标志，不包含转写全文。
- 当前业务控制器有异常记录后返回空结果的路径，因此空结果也不能单独证明历史上没有动作；存在疑问时保留查询范围和错误上下文供排查。此工具拒绝未声明字段。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `object` | 否 | 业务结果，结构见以下字段 |
| `data.items` | `array<object>` | 否 | 本页记录列表 |
| `data.items[].account_public_id` | `string` | 否 | 案件公开ID；用于后续动作查询，不解码猜测内部ID |
| `data.items[].datetime` | `string(date-time)` | 否 | 动作发生日期时间 |
| `data.items[].type` | `string` | 否 | 动作类型代码 |
| `data.items[].comment` | `string/null` | 是 | 动作备注 |
| `data.items[].result` | `string` | 否 | 动作结果展示名称 |
| `data.items[].is_radical` | `boolean/null` | 是 | 是否存在过激沟通 |
| `data.items[].is_discontented` | `boolean/null` | 是 | 是否对催收不满 |
| `data.items[].motivations` | `array<string>` | 否 | 本次动作的欠费动机 |
| `data.items[].interaction_result` | `string` | 否 | 交互结果标签展示值 |
| `data.items[].debt_reason` | `string` | 否 | 欠费原因标签展示值 |
| `data.items[].call` | `object/null` | 是 | 电话明细，无对应通话时可为null |
| `data.items[].call.phone_public_id` | `string/null` | 是 | 通话关联电话公开 ID |
| `data.items[].call.out_number` | `string/null` | 是 | 脱敏外呼号码，不是完整号码 |
| `data.items[].call.is_commited` | `boolean/null` | 是 | 是否承诺还款 |
| `data.items[].call.commit_time` | `string(date)/null` | 是 | 承诺还款日期 |
| `data.items[].call.reply` | `string/null` | 是 | 债务人主要诉求和主张 |
| `data.items[].call.commit_condition` | `string/null` | 是 | 承诺还款条件 |
| `data.items[].call.is_valid_call` | `boolean/null` | 是 | 是否为有效通话 |
| `data.items[].call.has_dialogue` | `boolean` | 否 | 是否存在通话转写；不返回全文 |
| `data.items[].call.revealed_self` | `boolean/null` | 是 | 是否表明身份和机构 |
| `data.items[].call.purpose` | `string/null` | 是 | 催收人员通话目的和诉求 |
| `data.items[].call.consequence` | `string/null` | 是 | 告知债务人的未履约后果 |
| `data.items[].call.follow_up` | `string/null` | 是 | 催收人员计划的后续行动 |
| `data.items[].call.duration_seconds` | `integer/null` | 是 | 通话时长（秒） |
| `data.items[].call.debt_reason_text` | `string/null` | 是 | 欠费原因文字总结 |
| `data.items[].call.damage_amount` | `number/null` | 是 | 分析提取的受损金额（元），缺失或无法解析为数字时null |
| `data.items[].call.has_damage_evidence` | `boolean/null` | 是 | 是否能提供受损凭证 |
| `data.items[].call.blame` | `string` | 否 | 分析提取的责任划分；如物业主责/非物业主责，缺失时N/A |
| `data.items[].call.domain` | `string` | 否 | 分析提取的受损类型；如私域/公域，缺失时N/A |
| `data.items[].property_service` | `object/null` | 是 | 物业跟进明细 |
| `data.items[].property_service.follow_up_date` | `string(date)/null` | 是 | 物业跟进日期 |
| `data.items[].property_service.issue_category` | `string/null` | 是 | 跟进事项分类 |
| `data.items[].property_service.issue` | `string/null` | 是 | 跟进事项 |
| `data.items[].property_service.reply` | `string/null` | 是 | 催收机构填写的物业回复 |
| `data.items[].property_service.comment` | `string/null` | 是 | 物业跟进批注 |
| `data.items[].property_service.reply_date` | `string(date)/null` | 是 | 物业回复日期 |
| `data.items[].call_analysis` | `object/null` | 是 | 话术质检结果，须请求且有数据 |
| `data.items[].call_analysis.features` | `object` | 否 | 相关配置累计摘要中的要素达成值，动态字段 |
| `data.items[].call_analysis.features.{key}` | `any` | 由实际值决定 | 动态分析要素的累计达成值，类型由实际要素决定 |
| `data.items[].call_analysis.completion_rate` | `integer/null` | 是 | 相关配置累计摘要的要素达成率，可缺失 |
| `data.items[].call_analysis.extracted_fields` | `object/null` | 是 | 本次通话最新分析提取的要素实际值，动态字段 |
| `data.items[].call_analysis.extracted_fields.{key}` | `any` | 由实际值决定 | 动态键对应的值，含义按所属对象或指标定义解释 |
| `data.items[].label_change` | `object/null` | 是 | 标签变更明细 |
| `data.items[].label_change.from_state` | `object` | 否 | 标签变更前状态 |
| `data.items[].label_change.from_state.{key}` | `any` | 由实际值决定 | 动态键对应的值，含义按所属对象或指标定义解释 |
| `data.items[].label_change.to_state` | `object` | 否 | 标签变更后状态 |
| `data.items[].label_change.to_state.{key}` | `any` | 由实际值决定 | 动态键对应的值，含义按所属对象或指标定义解释 |
| `data.items[].accountrecon` | `object/null` | 是 | 对账明细 |
| `data.items[].accountrecon.status` | `string` | 否 | 对账状态中文名 |
| `data.items[].accountrecon.date` | `string(date)/null` | 是 | 发起对账日期 |
| `data.items[].accountrecon.amount` | `number/null` | 是 | 发起对账金额 |
| `data.pagination` | `object` | 否 | 当前分页信息 |
| `data.pagination.total` | `integer` | 否 | 当前查询规则下的记录总数 |
| `data.pagination.page` | `integer` | 否 | 当前页码 |
| `data.pagination.page_size` | `integer` | 否 | 每页记录上限 |
| `data.call_analysis_labels` | `object` | 否 | 本页话术分析要素中文标签 |
| `data.call_analysis_labels.{key}` | `string` | 否 | 动态要素对应的中文标签 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。 `account.example` 仅为占位符，必须替换为当前应用返回的真实公开ID；模型验证不代表该ID能通过解码和权限检查。

```json
{
  "account_public_ids": [
    "account.example"
  ],
  "action_types": [
    "call",
    "property"
  ],
  "max_actions": 6,
  "page": 1,
  "page_size": 50
}
```

## legal_kb_originals_query

用途：按物业问题概要检索法规原文。

### 输入

| 字段 | 类型 | 必填 | 默认值 | 含义与限制 |
| --- | --- | --- | --- | --- |
| `scenario` | `string` | 否 | `"property"` | 查询场景；当前业务仅支持 property |
| `question_summary` | `string` | 是 | 无 | 物业问题概要，保留地区及关键事实；原始字符串最多100字符，去除首尾空白后非空；最长字符数 100 |

### 约束与口径

- scenario 默认 property；当前服务仅支持 property，其他非空值虽然可通过字符串 schema，业务层仍拒绝。两项字符串去除首尾空白后均不得为空。
- question_summary 的100字符上限先按原始字符串校验，再清理空白；不要用前后空白填充。地区写入概要，不额外传 region 查询参数。
- 返回 originals 最多100条；无匹配返回空列表，不表示不存在相关法规。超时或上游故障按错误处理，不能当作无匹配。
- OpenAPI 响应模型仅声明 `list[dict[str, Any]]`；下列原文字段来自当前知识库对象结构，不表示外层逐条强制验证了必填、类型或非空。使用前核对实际记录，不用缺失原文推断法律结论。
- 当前请求模型忽略未声明字段，而非拒绝；仍只传列出的参数，忽略不等于支持。

### 输出

以下路径相对于 `structuredContent`。

| 字段路径 | 类型 | 可为 null | 含义 |
| --- | --- | --- | --- |
| `message` | `string` | 否 | 业务提示字符串；不据此代替 isError 判断 |
| `data` | `object` | 否 | 业务结果，结构见以下字段 |
| `data.originals` | `array<object>` | 否 | 法规原文对象列表，最多100条；具体字段另见说明 |

当前原文对象字段（不是外层强校验承诺）：

| 字段路径 | 当前结构类型 | 缺失或 null 处理 | 含义 |
| --- | --- | --- | --- |
| `data.originals[].region` | `string` | 核对记录，缺失则不推断适用地区 | 适用地区，如全国、成都市 |
| `data.originals[].source_name` | `string` | 缺失则不能补造来源名称 | 原文来源文件名 |
| `data.originals[].source_level` | `string` | 缺失则不能推断效力层级 | 法律、行政法规、地方性法规等 |
| `data.originals[].raw_lines` | `string` | 缺失则无可引用原文，不自行补写 | 检索到的原文内容 |

### 调用示例

参数示意，项目、时间和查询条件须替换为实际请求。

```json
{
  "scenario": "property",
  "question_summary": "成都市物业服务收费项目和标准应如何公示？"
}
```
