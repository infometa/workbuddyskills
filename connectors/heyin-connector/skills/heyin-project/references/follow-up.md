# 随访管理使用说明

随访管理按当前环境和角色可见中心提供研究参与者视图与日期范围内的计划视图。写操作只修改已存在的随访计划，不创建计划，也不改变访视窗定义。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 查询随访日程 | 按自然日范围和可选中心获取随访计划 | 否 |
| 查询随访研究参与者 | 按中心、编号关键词和状态分页获取研究参与者及其计划 | 否 |
| 调整计划时间 | 在原访视窗内修改一条计划的 `plan_date` | 是 |
| 更新访视状态 | 按平台允许的状态转换更新状态和必要的实际访视时间 | 是 |

## 调用平台

按 [项目使用指南](../SKILL.md) 选择目标项目和角色凭证，通过 `heyincli req` 调用以下接口。参数直接放入表中指定的 `--query` 或 `--body` JSON 对象，项目由凭证确定，不传 `project_id`；请求环境由 `--test-env` 选择。

- 查询随访计划和研究参与者需要项目级 `PRJ_FOLLOW_UP_ACCESS` 权限或目标中心级 `SITE_FOLLOW_UP_ACCESS` 权限。
- 调整计划时间和更新访视状态需要项目级 `PRJ_FOLLOW_UP_EDIT` 权限或目标中心级 `SITE_FOLLOW_UP_EDIT` 权限。

## 查询随访数据（只读）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 获取随访计划列表 | `GET` | `/api/project/follow_up/list_follow_up_schedule/` | `--query`：`start_date`、`end_date` = `YYYY-MM-DD`（必填）；`site_id` = 当前项目可见中心 ID（可选，非负整数） |
| 获取随访研究参与者列表 | `GET` | `/api/project/follow_up/list_patient/` | `--query`：`limit` = 10–100（必填）；`offset` = 非负分页偏移（可选）；`site_id` = 可见中心 ID（可选，非负整数）；`keyword` = 研究参与者编号关键词（可选，最长 64）；`patient_status` = 有效状态（可选） |

`patient_status` 可选值为 `SCREENING`、`SCREENING_SUCCESS`、`SCREENING_FAILED`、`ENROLLMENT`、`DONE`、`QUIT` 或 `ABANDON`。不筛选时省略该字段。

### 返回内容

| 接口 | 业务返回内容 | 定义 |
| --- | --- | --- |
| 随访计划列表 | `list`（`FollowUpScheduleItem[]`） | 计划时间落在起止日期所覆盖完整自然日内的计划；不返回 `total`。 |
| 随访研究参与者列表 | `list`（`PatientFollowUpItem[]`）和 `total` | 应用中心、编号和状态筛选后的研究参与者；按研究参与者 ID 升序分页。 |

`FollowUpScheduleItem` 的核心属性如下：

| 属性 | 定义 |
| --- | --- |
| `id` | 随访计划 ID，也是写操作的 `schedule_id`。 |
| `site_id`、`patient_id`、`patient_sn` | 所属中心与研究参与者标识。 |
| `patient_is_mdv_upgrading` | 研究参与者是否正在进行方案版本升级；为 `true` 时写操作会被拒绝。 |
| `event_def_id`、`event_name` | 对应随访事件定义。 |
| `plan_date` | 当前计划时间。 |
| `window_start_date`、`window_end_date` | 访视窗起止时间。 |
| `visit_date` | 实际访视时间，可能为空。 |
| `time_unit` | `DAY`、`HOUR` 或 `MINUTE`，决定写入时间格式和访视窗比较粒度。 |
| `status` | `NOT_STARTED`、`IN_PROGRESS`、`COMPLETED`、`OUT_OF_WINDOW_COMPLETED` 或 `OUT_OF_WINDOW_MISSED`。 |

`PatientFollowUpItem` 包含研究参与者 ID、编号、状态、方案升级标志、`current_follow_up_schedule`、`next_follow_up_schedule` 和 `follow_up_schedules`。完整计划按计划时间与 ID 升序组织；“当前”是第一条 `IN_PROGRESS`，“下一条”是第一条 `NOT_STARTED`。`QUIT` 或 `ABANDON` 的研究参与者仍可出现在列表中，但当前和下一计划均为空，不能据此判断其历史计划不存在。

## 查询范围与分页

- 两个接口都要求项目已启用随访，并按当前生产或测试环境过滤。指定 `site_id` 时，中心必须属于当前环境且当前角色对该中心具有对应权限。
- 省略 `site_id` 不一定代表整个项目：项目级角色可见当前环境全部中心，中心级角色只返回其获授权的中心集合；中心级角色在当前环境没有可见中心时应得到空结果，不能把空范围解释为全项目范围。
- 日程查询的起止值按 CST 自然日处理，包含起始日和结束日的完整一天。它排除状态为 `QUIT` 或 `ABANDON` 的研究参与者所对应计划，且无分页；日期范围过窄时不能推断范围外没有计划。
- 研究参与者列表使用 `limit`、`offset` 和 `total`。从 `offset=0` 开始按实际返回条数推进，直到累计数量达到 `total`；空页或未读完全部页不能解释为没有其他结果。
- 写操作必须从最新读取结果按计划 ID、研究参与者编号、事件、计划时间和中心唯一定位。名称或编号歧义、计划不在当前读取范围或上下文不足时继续只读查询或向用户澄清，不得猜测 ID。

## 调整随访计划时间（写）

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 调整随访计划时间 | `POST` | `/api/project/follow_up/update_follow_up_schedule_plan_date/` | `--body`：`schedule_id` = 最新读取唯一定位的计划 ID（必填）；`plan_date` = 新计划时间（必填） | 无 |

新计划时间必须位于该计划的现有访视窗内。`time_unit=DAY` 时使用 `YYYY-MM-DD`；`HOUR` 或 `MINUTE` 时使用 `YYYY-MM-DD HH:mm` 或 `YYYY-MM-DDTHH:mm`。按天的访视窗使用 CST 自然日比较，按小时或分钟的访视窗按时间比较。

更新会把该计划标记为人工计划时间，但不会在此写操作中重算状态或改变访视窗。项目同时启用 ePRO 时，平台还会把新计划时间同步到同一研究参与者、同一事件设计下除 `FILLED`、`OVERDUE_FILLED` 外的 ePRO 问卷数据，包括 `OVERDUE_MISSED`；同步只改计划时间，不改问卷的访视窗或状态。执行前必须说明这一副作用，写后不能只核对输入参数；已填写终态记录保留旧计划时间是预期行为。

平台未在此接口限制计划当前状态，但仍要求目标研究参与者未处于方案升级中、项目和中心的研究参与者数据可写、项目允许当前环境执行写入。不得通过改变日期绕过状态或数据写入限制。

## 更新随访计划状态（写）

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 更新随访计划状态 | `POST` | `/api/project/follow_up/update_follow_up_schedule_status/` | `--body`：`schedule_id` = 最新读取唯一定位的计划 ID（必填）；`status` = 允许的目标状态（必填）；`visit_date` = 目标状态需要的实际访视时间（按需） | 无 |

平台允许的手动状态转换如下：

| 当前状态 | 允许目标状态 | `visit_date` 规则 |
| --- | --- | --- |
| `NOT_STARTED` | 无 | 未开始计划不能手动设置状态。 |
| `IN_PROGRESS` | `COMPLETED` | 必填并按 `time_unit` 格式化。 |
| `COMPLETED` | `IN_PROGRESS`、`OUT_OF_WINDOW_COMPLETED`、`OUT_OF_WINDOW_MISSED` | 转为完成类状态时必填；转回进行中会清空实际访视时间。 |
| `OUT_OF_WINDOW_MISSED` | `COMPLETED`、`OUT_OF_WINDOW_COMPLETED` | 完成类状态均须提供实际访视时间。 |
| `OUT_OF_WINDOW_COMPLETED` | `OUT_OF_WINDOW_MISSED`、`COMPLETED` | 转为 `COMPLETED` 时须提供实际访视时间。 |

`OUT_OF_WINDOW_COMPLETED` 的 `visit_date` 必须位于访视窗外。平台只校验 `COMPLETED` 的访视时间格式，不校验它是否位于窗内；提交前仍须对照访视窗展示实际关系，不得把窗外时间静默描述为窗内完成。转为 `IN_PROGRESS` 时当前时间必须位于访视窗内，并清空 `visit_date`。转为 `OUT_OF_WINDOW_MISSED` 时接口不会要求新的访视时间，也不会明确清除已有值，因此写后必须按实际返回报告 `visit_date`，不得自行宣称为空。

超窗完成和超窗缺失通常构成方案偏离，状态调整后提醒用户按项目流程记录偏离及原因；平台状态不替代偏离记录。

手动调整的目标状态只能使用 `IN_PROGRESS`、`COMPLETED`、`OUT_OF_WINDOW_COMPLETED` 或 `OUT_OF_WINDOW_MISSED`，且必须满足上表，最终由平台校验。更新会把状态标记为人工设置。目标研究参与者、项目、环境、功能开关和数据可写要求与调整计划时间相同。

## 操作前置与失败处理

每次写入前必须重新读取包含该计划的数据，固定 `schedule_id`、中心、研究参与者编号、事件、当前状态、计划时间、访视窗、时间粒度和现有实际访视时间。核对变更前后值及日期同步或状态影响是否在用户授权范围内；已覆盖完整关键参数时继续，不重复确认。用户只要求查询、比较或建议时不得写入。

每个获确认计划只执行一次写请求。权限不足、随访未开启、对象不属于当前项目或环境、研究参与者正在方案升级、项目或中心数据不可写、访视窗不匹配、状态转换非法、结果不明或平台失败时，保留实际错误并停止。不得更换计划、中心、目标状态或时间，也不得盲目重试。

## 敏感数据与输出边界

- 研究参与者 ID 与编号属于敏感研究数据，只展示完成当前随访任务所需的最小集合；不得扩展查询或输出无关研究参与者。
- 不得输出认证材料、内部路径、通知联系方式、未请求的临床数据或无关上游字段。缺失的计划、事件名称、访视时间或状态保持“未知”。
- 当前或下一计划为空只表示平台未返回对应状态的计划；不得补造计划，也不得推断随访已完成、未执行或研究参与者无风险。
- 平台返回的数据是业务记录，不代替临床判断；不能根据超窗、未完成或退出状态推断医学原因或责任归属。

## 结果核验

调整时间或状态后，必须重新读取覆盖该计划的日期范围，或在研究参与者视图中回读其完整计划，并按 `schedule_id` 核验最终 `plan_date`、`status` 和 `visit_date`。计划时间改变后，旧日期范围可能不再包含目标，应使用同时覆盖新旧计划时间的范围回读。

用写前和写后的实际结果反馈，不得只复述请求参数。单个计划可使用“属性 / 变更前 / 变更后 / 结果”表格；多个计划逐项列出。回读失败、目标未出现或字段与预期不符时报告“变更未确认生效”，不得仅根据空成功响应宣称完成。
