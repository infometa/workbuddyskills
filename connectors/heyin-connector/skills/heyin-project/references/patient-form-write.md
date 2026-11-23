# 研究参与者事件与表单写入说明

请求参数、凭证、环境、授权及响应读取遵循[项目使用指南](../SKILL.md)。

## 功能总览

| 功能 | 说明 | 预检 |
| --- | --- | --- |
| 事件实例维护 | 创建、变更日期、排序和删除事件数据 | 仅删除事件有 dry-run |
| 表单实例维护 | 创建、排序和批量删除表单数据 | 无 |
| 重复字段组维护 | 创建、排序和批量删除重复字段组数据行 | 无 |
| 字段实时保存 | 逐字段保存并报告冲突，可在明确授权覆盖冲突字段后强制覆盖 | 无 |
| 表单提交 | 使用全量 `subs` 快照保存或提交；已提交不能退回未提交 | 无 |

## 共同对象与状态边界

所有写入都必须基于[事件与表单读取说明](patient-form-read.md)形成的最新层级快照。定义 ID 决定创建哪类对象，数据 ID 决定更新、排序或删除哪条实例；二者不得互换。

事件、表单和字段组的可重复性、受控重复、提交、锁定、冻结及审核状态由平台最终校验。只在实时定义明确允许、父子关系一致且目标可写时提交；不得为完成请求自动取消提交、解除锁定或冻结、删减失败目标，也不得调用本说明之外的状态标记接口。

## 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 创建事件数据 | `POST` | `/api/project/patient/detail/create_event_data/` | `--body`：`patient_id`、`event_def_id`（必填）；`start_date`、`finish_date`（可选） |
| 变更事件数据 | `POST` | `/api/project/patient/detail/update_event_data/` | `--body`：事件数据 `id`（必填）；`start_date`、`finish_date`（可选）；`reason`（string，可选，最多 120 字符） |
| 排序事件数据 | `POST` | `/api/project/patient/detail/rank_event_data/` | `--body`：事件数据 `id`、目标 `ranking`（必填） |
| 删除事件数据演练 | `POST` | `/api/project/patient/detail/delete_event_data_dry_run/` | `--body`：事件数据 `id`（必填） |
| 删除事件数据 | `POST` | `/api/project/patient/detail/delete_event_data/` | `--body`：与有效演练相同的事件数据 `id`（必填）；`reason`（string，可选，最多 120 字符） |
| 创建表单数据 | `POST` | `/api/project/patient/detail/create_form_data/` | `--body`：`event_data_id`、`form_def_id`（必填） |
| 排序表单数据 | `POST` | `/api/project/patient/detail/rank_form_data/` | `--body`：表单数据 `id`、目标 `ranking`（必填）；`message`（可选） |
| 删除表单数据 | `POST` | `/api/project/patient/detail/delete_form_data/` | `--body`：同一事件数据、同一表单定义下的非空表单数据 `ids`（必填）；`message` 最长 120 字符（可选） |
| 创建字段组数据 | `POST` | `/api/project/patient/detail/create_section_data/` | `--body`：`section_def_id`（必填）；表单与父字段组上下文（按目标提供）；`event_data_id`（integer，可选）；`form_data_id`（integer，可选）；`form_def_id`（integer，可选）；`parent_section_data_id`（integer，可选） |
| 排序字段组数据 | `POST` | `/api/project/patient/detail/rank_section_data/` | `--body`：字段组数据 `id`、目标 `ranking`（必填） |
| 删除字段组数据 | `POST` | `/api/project/patient/detail/delete_section_data/` | `--body`：同一表单数据实例下的非空重复字段组数据 `ids`（必填）；`message` 最长 120 字符（表单已提交且定义 `has_change_info=true` 时必填，其余可选） |
| 实时保存表单字段数据 | `POST` | `/api/project/patient/detail/sync_form_data/` | `--body`：非空 `fields`（必填）；`is_force`（boolean，可选）；表单上下文（按目标提供）；`event_data_id`（integer，可选）；`form_data_id`（integer，可选）；`form_def_id`（integer，可选） |
| 提交表单数据 | `POST` | `/api/project/patient/detail/commit_form_data/` | `--body`：全量 JSON 字符串 `subs`（必填）；`is_committed`（boolean，可选）、`message`（string，可选，最长 120 字符）、`opened_at`（string，可选，表单打开时间）；表单上下文（按目标提供）；`event_data_id`（integer，可选）；`form_data_id`（integer，可选）；`form_def_id`（integer，可选） |

创建和更新事件的业务返回均含 `event_def`、`event_data`，事件实例 ID 读取 `event_data.id`；创建表单和创建字段组均返回 `def`、`data`，表单实例 ID 读取内层 `data.id`。排序和正式删除接口输出 `null`，不返回目标 ID。

`update_event_data` 与 `delete_event_data` 的 `reason` 是可选字符串，最长 120 字符；省略时按平台预设首选原因处理。需要特定修改或删除原因时显式传入用户已确认的内容，不能自行编造。

创建字段组、实时保存和提交可用 `form_data_id` 指向现有表单实例，或使用 `event_data_id`、`form_def_id` 提供待实例化表单的上下文；必须依据最新读取确认关系，不能混用冲突的上下文。

## 事件实例维护

创建前从研究参与者事件列表核对定义的 `is_repeating`、日期类型和已有实例。`start_date` 在 `DAY_TIME` 时使用 `YYYY-MM-DD HH:mm`，其他日期类型使用 `YYYY-MM-DD`；更新时空字符串具有清除语义，不能用省略字段替代明确清除。

排序只调整同一研究参与者、同一事件定义下重复实例的 `ranking`。创建、更新或排序成功后重新读取事件列表，用返回的数据 ID、日期和顺序核验。

### 删除事件闭环

1. 实时读取目标事件、下属表单和状态，展示将删除的整个事件实例范围。
2. 按用户已授权的目标执行一次 dry-run，参数为该事件数据 `id`。
3. 展示 `patient_is_locked`、`event_data_is_locked`、`has_frozen_or_locked_data_or_sd` 及已提交、审核、编码、SDV、签名和 SD 文件计数；缺失字段不补成零。
4. 只有演练通过、目标和影响未漂移且已有授权覆盖实际影响时，使用相同 `id` 正式删除。
5. 回读事件列表确认目标不存在。超时或结果未知时不重试。

## 表单与重复字段组维护

创建表单数据前核对目标定义是否允许重复及当前实例；排序只在同一事件数据、同一表单定义的实例间进行。批量删除表单时，全部 ID 必须属于同一事件数据和同一表单定义；批量删除字段组时，全部 ID 必须属于同一表单数据实例。每个 ID 都要核验归属，数组非空、为正整数且不重复；同一参与者内跨事件或跨表单的目标也不能随意合批。没有 dry-run 时必须在批准前直接说明全部目标和下级数据影响。

创建字段组数据只适用于重复字段组。`parent_section_data_id` 在祖先链含重复字段组时必传，且必须指向直接父级字段组数据；其余情况不传，不能把所有嵌套字段组都视为必须提供该参数。平台会补齐该行下字段和非重复子字段组，但不会自动创建嵌套的重复字段组；表单数据尚未创建时可能一并创建；创建响应的业务数据包含 `def` 和 `data`，表单数据 ID 读取内层 `data.id`，不是顶层 `form_data_id`。

字段组创建和排序只对未提交表单执行。排序只能发生在同一父实例下、同一 `section_def_id` 的数据行之间；不得跨父实例或字段组移动。删除重复字段组可用于已提交表单，但表单须未锁定、未冻结，待删行及其下级也不能包含冻结字段；表单已提交且定义 `has_change_info=true` 时必须填写 `message`。成功后用表单数据详情核验结构和顺序。

删除表单或重复字段组会级联删除对应下级字段、字段修改轨迹及 SD 字段映射，自动关闭相关质疑，并重新计算该参与者跨事件的自动计算与逻辑核查，可能改变其他字段值及系统质疑。删除字段组还会使所在表单当前有效的签名失效。操作前将这些影响纳入范围说明，操作后除核对目标消失，还要在可读取范围核对相关质疑、映射、签名和受影响的计算结果；无法完整回读的副作用明确标为未核验。

## 字段实时保存与冲突

`fields` 至少一项，每项必须含 `field_def_id`，可携带字符串 `data_value`、`null_flavor`、`unit_label`、`old_data_value`、`old_null_flavor`、`old_unit_label`。祖先链存在重复字段组时必须提供所属 `section_data_id`；其他字段可由服务端定位。提交前按[表单字段值与全量提交协议](form-data-values.md)核对选项编码、日期时间、数字精度、空值及单位；旧值三元组必须取自本次完整回读，不能把可选字段一律省略当成未知旧值。

该接口用于实时保存未提交表单。自动计算字段的提交值会被忽略，仍由平台计算填写；即使请求成功且冲突列表为空，也不能宣称这些值已按提交内容覆盖。

默认 `is_force=false` 或省略，让平台根据旧值、新值和平台当前值判定冲突：旧值或新值任一与平台当前值一致时不冲突。响应 `list` 中的字段均未保存，其中同时包含本次值与平台当前值；未进入冲突列表的字段可能已经保存，所以必须区分“已保存”“冲突未保存”和“未核验”。`form_data_id` 是本次定位或创建的表单数据 ID。`system_query_count` 只表示回填已提交表单所新增的系统质疑数量，不证明全部字段保存成功。

需要覆盖时，先展示冲突字段、平台当前值和拟覆盖值，再核对用户是否已明确授权以 `is_force=true` 覆盖这些冲突字段；未覆盖时补充确认。覆盖请求只能包含用户明确选择的字段；不得把原请求所有字段自动强制重放。

## 表单全量提交

`subs` 是合法 JSON 数组字符串形式的全量表单数据，不是增量补丁：遗漏的普通可写字段会被清空，遗漏的非重复字段组会坍缩为一行，遗漏的重复字段组现有行会被全部删除。自动计算及随机结果只读字段由平台保留或计算，不能利用此接口覆盖。字段组提交项的 `id` 缺省时，非重复字段组复用现有行，重复字段组新增一行。按[表单字段值与全量提交协议](form-data-values.md)的节点定义及平铺、嵌套重复组示例，从最新完整定义与数据形成最终快照，保留所有不在变更范围内的字段和重复行。授权已覆盖完整目标与影响时继续；不能从局部字段、缓存或冲突响应猜补整表，缺少完整现状时先补读。

`is_committed` 必须按当前状态和用户目标显式传入：未提交表单用 `false` 保存、用 `true` 提交；已提交表单编辑时仍须传 `true`。已提交不能退回未提交，此时省略该字段也会按 `false` 处理并被拒绝。`message` 最长 120 字符。成功响应的 `system_query_count` 表示本次产生的系统质疑数。提交后重新读取表单数据，核对 `is_committed`、完整结构和值；只收到成功响应或计数不能证明提交结果完整。

已提交表单的实际字段变更会留下轨迹，并可能取消对应审核、SDV 等标记和使签名失效；自动计算、逻辑控制、逻辑核查还可能改变同一参与者的其他字段或系统质疑。表单定义 `has_change_info=true` 时，修改已提交字段或新增非空字段需要字段级 `message` 或表单级 `message`；省略重复行形成删除时需要表单级原因。原因必须来自用户已确认内容。写后回读相关状态；未核验的连带影响保持未知。

### ePRO 代填同步

`commit_form_data` 在 `is_committed=true` 时还会查找该参与者、事件定义与表单定义匹配的有效非终态 ePRO 问卷，按当前时间与访视窗同步填写状态，记录 `opened_at`、`submitted_at`、耗时、当前操作人及角色快照，并将 `is_self_filled` 设为 `false`。没有匹配问卷或已有终态记录时不会因此新建或改写该记录；不从表单提交成功推断问卷一定改变。

`is_overdue_fillable` 仅限制参与者自填，不阻止研究者 EDC 补录；逾期未填写的匹配记录仍会变为逾期已填写。`opened_at` 若提供须为带时区的 RFC3339 字符串，不提供时使用请求时刻，不能编造打开时间或耗时。提交前把问卷代填影响纳入已授权范围，提交后按[问卷读取说明](epro.md)或参与者问卷列表核验状态与 `is_self_filled`；无读取权限时明确这部分未核验，不宣称由参与者本人填写。

## 共同写入与敏感边界

- 每项写操作都须核对完整参数与实际影响是否已获授权；已有明确授权覆盖时继续，不重复确认。
- 写前或批准后对象、环境、提交、锁定、冻结、结构或值发生变化时，旧批准失效。
- 字段值、空值原因、修改说明、冲突前后值和系统质疑只做任务所需的最小展示。
- 平台拒绝、部分保存、回读失败或结果未知时保留实际语义，不自动重试或改参。
