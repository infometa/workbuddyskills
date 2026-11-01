---
name: caoliao-data-analysis
display_name: 草料二维码数据分析
description: 用草料二维码 MCP 读取并分析组织数据。当用户提到草料、二维码/活码、点检、巡检、检查记录、表单记录、分区、批量模板、完成率、合格率、异常统计、静默点位/停用点位、待办/整改/派单/处理事项、逾期未完成、提交量、扫码量/扫描量/扫码次数/扫码人数/访问量、扫码渠道、扫码地域分布时使用。只读，不改数据。
description_zh: 通过草料二维码 MCP 查指标、看分布、下钻记录、浏览码/表单/模板/分区，统计待办完成与逾期，以及码被扫了多少次、多少人扫、从哪扫的；只读，不改数据。
description_en: Query metrics, distributions, records, to-do completion and QR scan volume (scans, unique visitors, channel and region) from Caoliao QRCode via MCP; browse QR codes, forms, templates and projects. Read-only.
version: 1.6.0
author: 草料二维码
---

# 草料二维码数据分析

草料二维码（cli.im）是企业用二维码管理设备、点位与表单记录的平台。本连接器把**用户所授权组织**的数据只读开放给你：算指标、看分布、追到具体记录，浏览码、表单、批量模板、分区。**任何工具都没有 org 参数**——组织身份由授权决定，你看不到也改不了。

## 前置条件与边界

- 用户需先在 WorkBuddy 完成草料 OAuth 授权。**授权只能由组织管理员完成**——授权页只列出该用户是管理员的组织；普通成员登录后看到的是空列表，这不是故障。遇到这种情况告诉用户"需要用组织管理员账号来连接"，不要让他反复重试。
- 调用返回 401 或"鉴权失败"：告诉用户"草料授权未完成或已失效，请在连接器里重新连接"，**不要反复重试**。用户也可以在草料的「已授权应用」页面里查看与撤销这个连接。
- 授权范围是**整个组织**的数据，不按该用户在草料里的可见范围裁剪——所以它只开放给管理员。用户问"为什么我能看到别的部门的数据"时，如实说明这一点。
- **只读**：不能新增/修改记录、码、表单。用户要写入时如实说明目前不支持，不要伪装成功。
- **个人信息**：记录里常含姓名、工号、手机号、定位。分析时可以用，但写进报表/网页/要分享的内容前，默认去掉手机号与定位，姓名仅在用户明确需要"到人"时保留。

## 术语与 ID（最容易混）

| 用户说的 | 平台对象 | 在工具里怎么指代 |
|---|---|---|
| 分区 / 项目 / 部门 | project | `project_id`（数字串），`scope.project_ids` |
| 码 / 活码 / 点位 / 设备 | qrcode | **两套 id**：`qrcode_id`（数字，用于 `scope.qrcode_ids`、分组）和 `coding`（短码如 `qKtSaXt`，用于 `qrcode_get` / `qrcodes_get_operation`，也接受完整码 URL） |
| 表单 / 检查表 / 点检表 | form | `form_id`（数字串） |
| 字段 / 检查项 / 选项 | field | `field_id`（长数字串，**必须从 `form_get` 取**，不能拿字段名当 id） |
| 批量模板 / 占位码 / 一物一码模板 | template | `tpl_id` + 模板 `coding` |
| 子码 | 模板下的码（qrcode） | 子码 `coding`；工具是 `templates_list_qrcodes` / `templates_get_qrcode` |
| 周期计划 / 定时巡检 | plan | `plan_id` |
| 指标 / 口径 | metric（派生量） | `metric` 名，从 `list_metrics` 取 |

同名表单多份是草料常态（各分区各建一份）——按名字对话，按 id 查询，分组结果里同名多行是不同表单。

## 两种返回外壳

- **语义七工具**（下表前 7 个）：成功 `{data, notes?, next_actions?}`——`notes` 是口径说明与截断提醒，**必须读**；`next_actions` 是建议的下一步及可直接复用的参数模板。失败以错误返回 `{code, message}`，`message` 已写明怎么办。
- **对象浏览八工具**：REST 风格 `{code: 0, message, data: {...}}`，分页字段在 `data` 里。

## 时间窗

- `time.from` / `time.to` 用 **epoch 秒**（如 `1788883200`），或**带时区**的 ISO 8601（`"2026-09-09T00:00:00+08:00"`）。**不带时区的 ISO 字符串会被拒绝**，防止静默偏 8 小时。
- 用户说"本月""最近 30 天""上周"时，你按 **GMT+8** 自然日换算成秒；`to` 超过当前时间会自动截到现在。
- `query_metrics` 时间窗**必填**；`record_list` 可不填（但不填会撞上限）。

## 工具速查

### 语义七工具（分析主力）

| 工具 | 何时用 | 关键参数 | 返回要点 / 坑 |
|---|---|---|---|
| `list_metrics` | **永远第一步**。用户问"我们有哪些…" | `limit`（每类对象上限，默认 30，最多 100） | `data.catalog.{forms,plans,qrcodes,projects}` 带名字；`catalog.totals` 是各块总数（`null` = 没数出来，不是 0），`catalog.truncated` 列出**只返回了前 N 条**的块，`catalog.degraded` 列出**查失败**的块——三者都表示"目录里没有 ≠ 组织没有"。`plans[].time_slots[]` 是 `{time_uuid, label, execute_status_label}`，`label` 是排班人话（如「每周 周一 00:00 → 周日 23:59」），`time_uuid` 对应 `group_by:"time_slot"` 的 `group_key`。`data.metrics[]` 每个含 `dimensions`（可分组维度）、`applicability`（`has_records` / `has_cycle_plans` / `has_todos`——组织没有周期计划或没启用待办，对应指标就不会列出）、`limitations`、`source`（`registry` = 平台口径，`org_metric` = 组织自定义）；`saved_definitions` 是组织自定义口径（可能为空）。用户点名的表单不在目录里时，先看 `truncated`，再用 `forms_list`（`search_key` 按名搜）找 |
| `get_metric` | 出数前看口径，比例类必看 | `metric` | 分母是什么、可用 `dimensions`、`limitations`（转述给用户） |
| `query_metrics` | 多少 / 占比 / 趋势 / 分布 | `metric`、`time`（必填）、`group_by`、`scope`、`limit`、`field_id` | 见下方「配方」。`limit` 默认 30；单维上限 200、双维上限 500，超限报 `invalid_argument`。比例类的数值点还带 `numerator`/`denominator`；计划类另带 `components{planned,completed,pending,overdue}`、待办类另带 `breakdown` 五桶——**这两个是回答"应做/已做/未做各多少"的正解**，见配方④⑤ |
| `record_list` | "这个数字是哪几条"——**取证不是遍历** | `filters`（同 scope 结构）、`time`（可选）、`limit`（默认 50，最多 200） | `data.{rows, total, truncated, limit}`。`total` 是符合条件的总数（权威），`rows` 只是前 N 条；**没有翻页**，不够就收窄时间窗或加过滤 |
| `record_get` | 一条记录的完整内容、审核链、附件 | `record_id` 或 `record_url`（二选一）；`format`=`json`(默认)/`markdown` | 读权威源，无同步延迟 |
| `form_get` | 读懂字段、拿 `field_id` | `form_id`，或 `form_ids`（批量，最多 20，返回 `{forms:[...]}`，单个失败只标该项 `error`） | `data.fields[]`：`field_id`、`field_name`、`field_type`（radio/checkbox/text/image/name/time…）、`options[].value` |
| `qrcode_get` | 单个码的标题、字段、内容、操作区 | `qrcode`（coding 或码 URL） | |

`scope` / `filters` 可用字段（不填=不限定，可组合）：`form_ids`、`project_ids`、`qrcode_ids`、`member_ids`（提交人）、`process_status_text`（如「待处理」）/ `process_status`、`result_value_texts` / `result_values`（如「合格」）、`field_equals: [{field_id, value}]`（字段精确匹配）、`audit_stage_ids`、`auditor_user_ids`、`state_ids`。数组字段也接受 JSON 字符串形态。

### 平台派生量清单（`list_metrics` 会按组织适用性裁剪，实际以返回为准）

| 派生量 | 是什么 | 适用条件 |
|---|---|---|
| `record_submission_count` | 记录提交量 | `has_records` |
| `active_submitter_count` | 提交人数（去重） | `has_records` |
| `active_qrcode_count` | 有记录产生的码数（去重） | `has_records` |
| `active_form_count` | 有记录产生的表单数（去重） | `has_records` |
| `inactive_qrcode_count` | 静默码数（配方⑤） | `has_records` |
| `plan_task_completion_ratio` | 周期任务按期完成占比（配方④） | `has_cycle_plans` |
| `plan_task_gap_count` | 周期任务已逾期未完成数 | `has_cycle_plans` |
| `todo_open_count` | 待办未完成数（配方⑥） | `has_todos` |
| `todo_overdue_open_count` | 待办已逾期未完成数 | `has_todos` |
| `todo_on_time_completion_ratio` | 待办按期完成占比 | `has_todos` |
| `scan_count` | 扫码次数（配方⑦） | `has_scans` |
| `scan_visitor_count` | 扫码人数（去重，配方⑦） | `has_scans` |

记录类五个量共享同一套维度：`form` / `qrcode` / `project` / `process_status_text` / `result_value_text` / `day` / `month` / `field_value`。计划类与待办类的维度见各自配方。

### 对象浏览八工具（枚举，不算数、不分组）

| 工具 | 参数 | 返回 |
|---|---|---|
| `forms_list` | `page`(默认 1)、`page_size`(默认 10，最多 20)、`search_key`（模糊匹配标题/备注/编号）、`number`（编号精确，如 `D32`） | `data.list[]{id,name,type_text,number,project{id,name}}`，`data.page{current_page,last_page,per_page,total}` |
| `projects_list` | `page_size`(默认 100，最多 100) | `project_id,name,parent_id` |
| `qrcodes_list` | `page_size`(默认 20，最多 100)、`page_token`（上一页的 `next_page_token`）、`start_time`/`end_time`(ISO 8601) | `data.list[]{name,id,coding,tpl_id}`、`next_page_token`、`total` |
| `qrcodes_get_operation` | `qrcode`（coding 或 URL） | 该码关联的操作项：`operation_name`、`operation_description`、`element_type` + `element_type_title`（中文类型名，展示用这个）、`element_value` |
| `templates_list` | 同 `qrcodes_list` 的分页/时间 | `tpl_id,name,coding` |
| `templates_get` | `template`（模板 coding 或 URL） | 模板 meta + 字段结构 |
| `templates_list_qrcodes` | `template`(必填) + 分页/时间 | 模板下子码 `name,id,coding` |
| `templates_get_qrcode` | `template`、**`subcode`**（均 coding 或 URL）——注意参数名仍是 `subcode`，不是 `qrcode` | 子码 meta + fields |

浏览工具翻页：`qrcodes_list`/`templates_*` 用 `page_token`，`forms_list` 用 `page`。这些能翻页；`record_list` 不能。

## 标准链路

`list_metrics` → `get_metric` → `query_metrics` → `record_list`（传 drill_down） → `record_get` / `form_get`

## 七条验证过的配方

**① 出数 + 下钻**
`query_metrics{metric:"record_submission_count", time, group_by:"form"}` → 每组返回 `{group_key:"2693999", group_label:"动火作业检查", value:734, drill_down:{filters:{form_ids:["2693999"]}, time}}`。把某组的 `drill_down` **原样**作为 `record_list` 的 `filters` + `time` 传入，就得到构成这个数字的记录。不分组时 `result.value` 是总量，分组时 `result.value` 为 null、看 `groups`。

**② 按字段取值分布 / 合格率（两步精确查询，禁止抽样）**
1. `form_get{form_id}` 找到目标字段的 `field_id`（如「检查结果」）。
2. `query_metrics{metric:"record_submission_count", time, group_by:"field_value", field_id, scope:{form_ids:[仅一个]}}` → 组为 `{group_key:"正常", value:733}`、`{group_key:"异常", value:1}`；取值就是展示文本。合格率 = 合格组 / 各组之和（或除以应做数）。
3. 要看异常明细：`record_list{filters:{form_ids:[…], field_equals:[{field_id, value:"异常"}]}, time}`。
约束：`field_value` 必须配 `field_id` 且 `scope.form_ids` **恰好一个表单**；只有记录统计类指标支持它，计划类（`plan_task_*`）不支持。

**③ 双维交叉（区域×班次、表单×月份）**
`group_by:["form","month"]`（或 `"form,month"`，最多两维，不能相同）→ `group_key` 与 `group_label` 变成**按维度名做键的对象**：`{form:"2693999", month:"2026-08"}`，用维度名取值，别假设键序。每组的 `drill_down` 已按该组切好时间。组数上限 500，触顶时 `notes` 会提醒被截断——此时不要把看到的组当全部，收窄范围或改单维。

**④ 周期计划：应做 / 已做 / 未做 / 逾期（别只报 value）**
`query_metrics{metric:"plan_task_completion_ratio", time}` 的数值点除了 `value`，还带
`components:{planned, completed, pending, overdue}` 与 `breakdown:{planned, done, missed, pending, skipped}`。
**报"完成情况"时要用这四个分量，不要只报 value**：`value` 的分母含 `pending`（还没到期的任务），时间窗越靠近当下 pending 越多、value 被无端拉低。
返回的 `notes` 里会直接给出这次的换算结果（如「completed=45、pending=5、overdue=234：评估执行纪律建议看 completed/(completed+overdue)=16.1%，而不是直接用 value」）——**读它，按它报**。
- 可用维度：`plan_target_form` / `cycle_type` / `day` / `month` / `plan` / `qrcode` / `time_slot` / `project`。
- 每日趋势：`group_by:"day"`；按点位/班次拆：`group_by:["qrcode","time_slot"]`（即「区域 × 班次」矩阵）。
- **「哪些没做」的明细**：用 `plan_task_gap_count` + `group_by:"qrcode"`，得到的是**点位清单**（每组一个码，`group_label` 是码名）。计划类**不给记录级下钻**——未完成的任务本来就没有记录，`record_list` 查不到它们；`drill_down` 为 null 是正确行为，不是缺陷。
- 计划类**不支持** `field_value` 维度：未完成的任务没有记录、没有字段值。

**⑤ 静默点位：哪些码这段时间一条记录都没有**
`query_metrics{metric:"inactive_qrcode_count", time, group_by:"qrcode"}`。三个反直觉之处必须记住：
1. **分组后每组的 `value` 是"静默天数"，不是记录条数**——是距今多久没动（如 `152` 表示 152 天没有新记录）。
2. universe 是"历史上至少提交过一条记录、且当前未删除"的码；**建了从没用过的新码不计入**（它的"没记录"是还没启用，不是停了）。
3. **不分组时不给 `drill_down`**（静默是"没发生"，顶层没有可下钻的记录集）；分组后每组的 `drill_down` 时间窗是按该码最后一次提交单独算的，不是你传的观察窗——原样传给 `record_list` 就能看到它最后那条记录。

**⑥ 待办 / 整改派单**
待办是"记录满足规则条件后自动派单、或人工指派"的处理事项，三条量共用同一时间窗（按待办**创建时间**筛选），可直接互相印证：
- `todo_open_count` 未完成数 —— 含已逾期、未到期、以及**根本没设期限**的。
- `todo_overdue_open_count` 已逾期未完成数 —— **没设期限的待办永远不算逾期**，所以它只是未完成数的一个子集，不能当"未完成里有多少没办好"的全貌。
- `todo_on_time_completion_ratio` 按期完成占比 —— **分母只含"设了期限的已完成待办"**，没设期限的分子分母都不进。实际使用中相当比例的待办不设期限，所以这个比例回答的是"有期限要求的事项里按时办结的占多少"，不是"所有待办完成了多少"；分母很小时要结合 `todo_open_count` 的绝对量一起说。

维度：`form` / `project` / `qrcode` / `operator_source`（派单方式）/ `priority` / `trigger_type` / `month` / `day`。
`priority` 分组的组名是数值，含义：**100 紧急 / 50 普通 / 20 低 / 0 未设置**。
`operator_source` 取值：`rule_assigned` 规则自动派、`assigned` 人工指派、`claimed` 认领、`pending_dispatch` 待派单、空串未定。
组织没启用待办时，`list_metrics` 不会列出这三条量，`notes` 会说明"这个组织还没有待办数据"——这时如实告诉用户，不要拿别的量凑。

**⑦ 扫码量：码被扫了多少次、多少人扫、从哪扫的**
`query_metrics{metric:"scan_count", time}` 给扫码次数，`scan_visitor_count` 给去重人数。维度另有一套，共 12 个：
- 时间：`day` / `week` / `month` / `quarter` / `year`
- 地域：`province`（已归一到 34 省 + 海外 + 未知）/ `city`（`group_key` 是「省份/城市」复合键如 `黑龙江省/齐齐哈尔市`，`group_label` 是人话——城市重名跨省真实存在，只用市名会把两地并成一行）
- 终端与来源：`scan_source`（扫码渠道）/ `os` / `brand`
- 其他：`hour`（**一天中的哪个小时**，0-23 的分布，不是窗口内逐小时趋势）/ `qrcode`
**分区不能当分组维度**——底层看板不按分区拆扫码量。要比较分区就分别用 `scope:{project_ids:[…]}` 查几次。
**最有价值的用法是与记录提交量对照**：同一时间窗再拉一次 `record_submission_count`，两者的差就是「扫了没填」。实测某组织近 30 天：消防安全培训扫 10411 次交 4450 条（42.7%），消防安全考试扫 6227 次交 3564 条（57.2%）——差距本身就是结论。

⚠️ **两族按码分组的 `group_key` 不是同一套**，对照时必须先对齐：扫码族给的是 **coding**（如 `q2P8dlH`），记录族给的是 **qrcode_id**（如 `400369812`）。
- **不要靠 `group_label`（码名）配对**——同名码多份是草料常态，靠名字会配错。
- 正确做法：用 `list_metrics` 返回的 `catalog.qrcodes[]`（每项同时有 `qrcode_id` 与 `coding`）或 `qrcodes_list`（返回 `{name,id,coding}`）建立映射，再按 id 对上。
- 码多时先各自取 TOP N，只对交集里的码算转化率，并说明这是 TOP N 而非全量。
四个必须记住的差异：
1. **扫码 ≠ 提交**。同一个人反复扫算多次，扫了没填也算。回答「多少人做了检查」要用记录侧的量，不要拿扫码人数顶替。
2. **没有 `drill_down`**。一次扫码可能什么都没提交，没有对应的记录集可下钻——为 null 是正确行为。
3. **不支持双维交叉**，`scope` 只认 `project_ids`。传表单/字段/处理进度这些**记录的属性**会明确报错，不会被静默忽略。
4. **人数不可加**。各天/各省的扫码人数相加得不到总人数（同一个人会被重复计），总数要单独查一次不带 `group_by` 的。按 `hour` 分组时底层没有按小时的人数，`scan_visitor_count` 会全部返回 0——看小时分布用 `scan_count`。
其他口径：`scan_source` 是微信场景值收敛的八个业务桶（扫一扫 / 长按识别 / 相册识别 / 好友分享 / 群聊分享 / 微信收藏 / H5扫描 / 其他），其中「H5扫描」是浏览器直接打开、没有微信场景值的那部分，这部分没有 open_id，**计入次数但不计入人数**。`province` 已归一到 34 省 + 海外 + 未知。时间窗按**北京整日**对齐，半天的窗口会被撑成整天。
组织没有扫码数据、或本次部署没接扫码统计服务时，`list_metrics` 不列出这两条量，`notes` 会说清是「没接」「确实没有」还是「探针查失败」——**这三者含义完全不同，不要把后两种当成「这个组织没扫过码」下结论**。

组织自定义口径（`source=org_metric`）不支持双维交叉，且比例的分子/分母字段暂缺——这是平台已知分期，不是数据错。

## 必须遵守

1. **数据能拿到就不许估算。** 每个数字来自工具精确返回。`record_list` 的 `truncated=true` 时 `rows` 只是样本，**禁止**用样本比例外推整体（"200 条里 30% 异常，估计全量 900 条"这类一律不做）；要占比用 `query_metrics`，它没有截断。
2. **用名字不用编号。** 表单名、字段名、选项值是用户写的，直接用它们和用户对话；查询时才换成 id。
3. **口径先说清。** 比例类回答带分子、分母、时间范围；`get_metric.limitations` 里的陷阱要转述（如"还没到期的任务计在分母里，时间窗越靠近当下比例越低"）。
4. **读 `notes`。** 截断、口径、名字解析失败（label 回落为 id，表单可能已删除）都在里面。
5. **拿不到精确统计就说不知道。** 某维度不支持时如实说"暂不支持精确分布"，不编数。

## 错误码

| `code` | 含义 | 怎么办 |
|---|---|---|
| `metric_not_found` | 指标名不对 | 回 `list_metrics` 看可用清单 |
| `invalid_argument` | 参数不合法（超 limit、缺时区、field_value 缺 form_ids 等） | 按 `message` 修正参数 |
| `query_timeout` / `query_busy` | 时间窗或分组太大 / 查询通道繁忙 | 收窄时间窗、减少维度或 scope 后重试一次，不要无限重试 |
| `upstream_unavailable` / `upstream_rejected` / `not_configured` | 上游暂不可用或拒绝 | 稍后重试一次，仍失败则告诉用户稍后再试 |
| `form_schema_unavailable` | 表单结构取不到（可能已删除） | 用 id 继续，向用户说明字段名无法还原 |
| `not_implemented` | 是这个组织沉淀的命名口径，当前版本还不能直接按它出数 | 按 `message` 的指引，用 `get_metric` 看定义，再用对应的结构派生量 + scope 自己算 |
| `internal` | 服务端内部错误 | 重试一次；仍失败如实告诉用户，不要伪造数据 |

**注意两种失败外壳不一样**：上表这些是**工具级**失败，形如 `{code, message}`。而**参数 schema 级**校验失败（时间缺时区、类型不对等）由 MCP 框架直接返回校验文本，**没有 `code`/`message` 字段**，形如 `2 validation errors for call[query_metrics] time.from Value error, ISO 时间字符串缺时区…`——同样已写明怎么改，照着修参数重试即可。

## 输出习惯

- 先给结论和关键数字，再给分组表；每张表注明时间范围与口径。
- 报表/网页里所有数字都来自本次查询，标注"数据截至 <查询时间>"；默认不放手机号与定位。
- 需要持续更新的报表，提示用户在 WorkBuddy 设置定时任务，每次执行都会重新取最新数据。
