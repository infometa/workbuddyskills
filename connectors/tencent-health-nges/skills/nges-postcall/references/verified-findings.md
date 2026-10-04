# NGES 真实环境验证记录（2026-09-07 实测）

> 本文件记录 skill 编写后对 test.nges.qq.com 环境的真实调用验证结果。**以下字段与行为已实测确认**，构造 GQL 时优先以本文件为准；未覆盖的字段仍需运行时 `GetObjectsByNames` 核对。

## 1. 已验证可用的 MCP 调用

| 调用 | 状态 | 备注 |
|---|---|---|
| `NgesStaff__GetStaffUserInfo` | ✅ | 返回 identity_tag / territory_list / active_role |
| `MetadataService__GetObjectList` | ✅ | 729 个对象；含 hcp / visit / visit_item |
| `MetadataService__GetObjectsByNames` | ✅ | 返回 `{"list":[{"object":{...},"fields":[...]}]}` 结构 |
| `DataService__GraphqlQuery`（读） | ✅ | hcp / visit_item 查询均正常返回 |
| `CsaService__CheckStream` | ⚠️ 受限 | 见 §4 已知坑 |
| `DataService__GraphqlQuery`（写） | ✅ **可用** | 语法见下"写入语法（已实测）" |

### 写入语法（2026-09-07 实测通过，含读回验证）

**正确语法是 `mutation insert { 对象(_values: {...}) }`**——不是标准 GraphQL 的 `mutation {insert_对象(...)}`（那样会报 13003「操作暂不支持」）。

```gql
# 写拜访计划（visit_item）——2026-09-08 业务确认：拜访计划与拜访记录统一写 visit_item，不写 visit
mutation insert {
  visit_item(_values: {record_type: "oldChannel", hcp_id: "I~1989257082198589440", plan_date: 1788796800, status: 0, channel: 1, type: 2, summary: "目标摘要"})
}
# 返回: {"visit_item":[{"_insert":true,"id":"I~20xxx"}]}（读回验证用返回的 id）

# 写拜访记录（visit_item）——实测成功；record_type="oldChannel" 必填
mutation insert {
  visit_item(_values: {record_type: "oldChannel", hcp_id: "I~1989257082198589440", actual_date: 1788791355, status: 1, channel: 1, type: 2, summary: "拜访小结", next_plan: "下一步"})
}

# 删除（软删，查询自动过滤）——实测成功
mutation delete { visit(_where: {id: "I~xxx"}) }
```

**实测确认的行为**：
- `only_validate: true` 对 mutation 同样有效（干跑返回 `{"visit":null}` 无报错即通过）——**正式写入前必须先干跑**。
- `owner` / `create_time` / `update_time` / `version` 等平台字段**自动填充，不要传**。
- 写后必须读回验证：`{visit_item(id: "I~xxx") {...}}`，逐字段核对（含 id 反查，如 hcp_id 反查 hcp）。
- **拜访数据（拜访计划 + 拜访记录）一律写 `visit_item`，不写 `visit`**（2026-09-08 业务确认；`visit` 表曾实测写入成功，但不再作为写入目标）。写计划：`status: 0` + `plan_date`；写记录：`status: 1`（草稿）/`2`（提交）+ `actual_date`。
- `visit_item.record_type` 必填且唯一合法值 `"oldChannel"`。

> 历史探测备注：此前用错误语法（`mutation {insert_visit(...)}`、`{add_visit(...)}`）探测得到 13003/13005，曾误判为"端点只读"。正确语法由业务方提供后验证通过。

## 2. 核心对象实测字段（PreCall 用）

### hcp · 医生信息（79 字段）

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | TEXT | 医生姓名 |
| `hco_name` | TEXT | 所在医院名（直接是文本，可用） |
| `department` | TEXT | **存的是 ID 不是科室名**，需关联解析 |
| `major_title` | TEXT | 职称（测试数据里部分存的是枚举 ID 如 "DPT05"） |
| `hcp_grade` | SELECT_ONE | 医生等级（测试数据多为 null） |
| `is_kol` | BOOL | 是否 KOL |
| `belong_territory` | TEXT | 所属岗位，必填 |
| `is_active` | SELECT_ONE_INT | 是否有效，必填 |

实测查询示例（可直接用）：
```gql
# 医生名单——hcp 查询必须带 hcp_territory.id 过滤（只返回已分配辖区的医生），禁止全量查询
{hcp(is_active: 1, hcp_territory.id: {_is_null: false}, _limit: 50, _order_by: {update_time: _desc}) {id name hco_name hcp_grade major_title}}

# 按医生聚合拜访统计（PreCall 推荐逻辑核心查询，已验证 _group_by/_max/_count 可用）
{visit_item(status: 2, _group_by: [hcp_id]) {hcp_id last_visit: _max(actual_date) visit_cnt: _count(id)}}

# 单医生拜访历史（生成手卡时用）
{visit_item(hcp_id: "I~xxx", _order_by: {actual_date: _desc}, _limit: 5) {actual_date summary next_plan purpose channel status}}
```

**注意**：两查询的关联在本地做（hcp_id ↔ hcp.id），不要试图单条 GQL 联查。hcp_id 格式混杂（`I~` / 纯雪花 / `DOC` / `P` 前缀四种），按原值精确匹配。

### visit · 拜访计划表（25 字段）—— ⚠️ 不作为写入目标（拜访数据统一写 visit_item）

| 字段 | 类型 | 说明 |
|---|---|---|
| `plan_date` | DATETIME | 计划拜访时间（秒级时间戳） |
| `actual_date` | DATETIME | 实际拜访日期 |
| `status` | SELECT_ONE_INT | 拜访状态（枚举值需运行时查选项） |
| `purpose` | SELECT_ONE_INT | 拜访目的（枚举） |
| `type` | SELECT_ONE_INT | 拜访计划类型（枚举） |
| `visit_period` | SELECT_ONE_INT | 拜访时间段（枚举） |
| `todo` | TEXT | 待办事项（**可写入手卡摘要**） |
| `staff` | TEXT | 业务人员 |
| `hco_id` | TEXT | 机构 id |
| `record_type` | SELECT_ONE | **必填**，枚举值需运行时查 |

## 3. 核心对象实测字段（PostCall 用）

### visit_item · 拜访对象表（57 字段）—— PostCall 写入目标

| 字段 | 类型 | 说明 |
|---|---|---|
| `hcp_id` | TEXT | 医生 id（关联 hcp.id） |
| `hco_id` / `hco_name` | TEXT | 机构 |
| `actual_date` | DATETIME | 实际拜访日期（秒级） |
| `plan_date` | DATETIME | 计划拜访时间 |
| `summary` | TEXT | **拜访小结 —— 报告主体落这里** |
| `medical_viewpoint` | TEXT | **医学观点记录 —— 医生反馈/原话落这里** |
| `next_plan` | TEXT | **下一步计划 —— 承诺/遗留落这里** |
| `discuss_intent` | SELECT_ONE_INT | 讨论意图（枚举） |
| `purpose` | SELECT_ONE_INT | 拜访目的（枚举） |
| `channel` | SELECT_ONE_INT | 拜访渠道（枚举） |
| `duration` | FLOAT | 拜访时长 |
| `status` | SELECT_ONE_INT | 医生拜访状态（实测见过 2=已提交、4） |
| `record_type` | SELECT_ONE | **必填**，枚举值需运行时查 |
| `ai_msg_record_id` | TEXT | 可关联 ai_message_record 表（AI 会话留痕） |

## 4. 已知坑（实测踩出）

| # | 坑 | 规避方式 |
|---|---|---|
| 1 | **ID 带 `I~` 前缀**（如 `I~2095447301330456576`） | 写入外键时保留完整前缀，不要截断 |
| 2 | **CheckStream 是流式接口，MCP 代理只回传 `start` 事件**，拿不到最终 passed/violations 判定 | 见下"合规检测降级策略" |
| 3 | `enable_ae_detection` 参数声明是对象 `{value: bool}`，但 Go 后端要纯 bool，**两种传法都报错** | **直接不传此参数**，系统默认启用 AE 检测 |
| 4 | `hcp.department` / `major_title` 测试环境里存枚举 ID 而非文本 | 展示时如值像 ID 则标注"未解析"，不要硬显示 |
| 5 | SELECT_ONE_INT 枚举的具体含义（如 status=2/4 各是什么）元数据里有 options，需查 `select_one_int_option.options` | 展示状态/目的时先做枚举→中文映射。**实测枚举**：visit_item.status 0=计划中/1=待提交/2=已提交/3=已取消/4=已过期；purpose 1=传递产品知识/2=病理沟通/3=用药观念沟通；type 1=医院拜访/2=医生拜访/3=eDA拜访；channel 1=面对面/2=电话/8=线上拜访 等；visit.status 0=计划中/1=已执行/2=已完成 |
| 6 | **写入语法非标准**：必须是 `mutation insert { 对象(_values: {...}) }`，用标准 GraphQL 写法（`mutation {insert_对象(...)}`）会报 13003 | 按 §1"写入语法"模板构造；先 `only_validate: true` 干跑再正式写入 |

## 5. 合规检测降级策略（CheckStream 受限时）

CheckStream 经 MCP 代理只能拿到 start 事件（request_id 已生成、检测任务已入队列），拿不到终态判定。落库前的合规兜底改为：

1. **本地预检**：生成文本先过一遍关键词自检（超说明书表述、绝对化用语、患者姓名/病案号），命中即改。
2. **仍调 CheckStream**：拿到 request_id 即视为"已提交合规检测"，在报告中记录该 id 供审计追溯。
3. **AE 人工确认**：代表确认落库前，明确询问一句"本次拜访是否涉及患者用药后不良反应？"——代表答"是"则中止落库转 AE 上报流程。

> 该降级策略是过渡方案；待 MCP 代理支持流式终态回传后，恢复以 CheckStream 判定为准。

## 6. 写入操作规范（已可用）

写入已实测可用，按以下纪律执行（对标 ADP 写库纪律）：

1. **先干跑**：`only_validate: true` 校验 mutation 语法与字段，失败则把字段错误转述给用户修正。
2. **代表确认**：用 markdown 呈现待写入内容，等代表明确说"确认/保存/提交"后再正式写入。
3. **正式写入**：`mutation insert { 对象(_values: {...}) }`；平台字段（owner/create_time/update_time/version）不传，自动填充。
4. **读回验证**：用返回的 id 查回记录，逐字段核对（日期时间、id 反查），核对无误后向代表返回结果（计划/记录编号、日期、对象），不展示验证过程。
