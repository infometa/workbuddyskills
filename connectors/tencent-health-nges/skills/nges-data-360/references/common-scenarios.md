# 常用业务场景：对象语义与分析模板

覆盖三大高频分析场景：**拜访**（visit / visit_item）、**会议**（events_meeting）、**用户行为**（user_behavior_details）。下文字段、枚举值、关联关系**均来自 T1 预发环境实测**（GetObjectsByNames），可直接套用。

> ⚠️ **仍以实时元数据为准**：不同租户/环境字段可能有差异，套模板前用 `GetObjectsByNames` 复核一次。所有 `DATETIME` 字段按**秒级** Unix 时间戳过滤。枚举字段（SELECT_ONE/SELECT_ONE_INT）过滤时用**选项的 value**，不是 label。

> **数据范围交给行权限**：下方模板**默认不含 `owner`/`belong_territory` 过滤**——行权限会按当前用户角色自动限定范围（Rep 看自己、DSM/RSM 看团队）。仅当"管理者只看自己"（加 `owner: $_uin`）或"只看某几个特定下属"（`ListSubordinateTerritory` + `belong_territory {_in}`）时才显式收窄。详见 [roles-and-data-scope.md](roles-and-data-scope.md)。

---

## 场景一：拜访分析（visit / visit_item）

**业务语义与两表关系**：`visit`（拜访计划表）是一次拜访的**计划/主单**；`visit_item`（拜访对象表）是该计划下针对**每个医生（HCP）的实际拜访明细**（一次计划可拜访多个医生）。两者通过 `visit_item.visit_id → visit.id`（ONE_TO_ONE 反向为 visit 的 `visit_item` ONE_TO_MANY）关联。

> **口径要点**：「拜访量/拜访了多少医生」通常统计 **visit_item**（实际拜访明细，含 hcp_id）；「拜访计划数」才统计 visit。别混。

### visit 核心字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `actual_date` | DATETIME | 实际拜访日期 |
| `plan_date` | DATETIME | 计划拜访时间 |
| `finish_date` | DATETIME | 完成拜访时间 |
| `status` | SELECT_ONE_INT | 拜访状态：`0`计划中 `1`已执行 `2`已完成 `3`已取消 `4`已过期 |
| `type` | SELECT_ONE_INT | 拜访计划类型：`0`计划拜访 `1`临时拜访 `2`门店拜访 `3`药店总部拜访 |
| `purpose` | SELECT_ONE_INT | 拜访目的：`1`补货与陈列检查 `2`市场活动 `3`店员教育 `4`分销 |
| `hco_id` | TEXT | 机构 id（关联 hco） |
| `staff` | TEXT | 业务人员 |
| `owner` / `belong_territory` | TEXT | 拥有者 / 所属岗位 |

### visit_item 核心字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `actual_date` | DATETIME | 实际拜访日期 |
| `plan_date` / `start_time` / `end_time` | DATETIME | 计划/开始/结束时间 |
| `duration` | FLOAT | 时长 |
| `status` | SELECT_ONE_INT | 医生拜访状态：`0`计划中 `1`待提交 `2`已提交 `3`已取消 `4`已过期 |
| `channel` | SELECT_ONE_INT | 拜访渠道：`1`面对面 `2`电话 `3`邮件 `4`视频 `8`线上拜访 `9`进院拜访 `11`面对面-DA播放 `12`企业微信 …（共 13 项） |
| `type` | SELECT_ONE_INT | 拜访类型：`1`医院拜访 `2`医生拜访 `3`eDA拜访 `4`MSL拜访 |
| `purpose` | SELECT_ONE_INT | 拜访目的：`1`传递产品知识 `2`病理沟通 `3`用药观念沟通 |
| `hcp_id` | TEXT | 医生 id（关联 hcp） |
| `hco_id` / `department` | TEXT | 机构 id / 科室 |
| `summary` / `medical_viewpoint` / `next_plan` | TEXT | 拜访小结 / 医学观点 / 下一步计划 |
| `owner` / `belong_territory` | TEXT | 拥有者 / 所属岗位 |

**常用关联**：`visit_item.hcp`(医生)、`visit_item.visit`(主计划)、`visit_item.participators`(参与医生)、`visit.visit_item`(子明细)、`visit.hco`(机构)。

### 分析模板（占位时间戳替换为目标秒级区间）

**1. 团队本月实际拜访医生次数（已提交）**
```gql
{visit_item(_where: {actual_date: {_gte: 1717171200, _lt: 1719763200}, status: 2}) {
  _aggregate { _count }
}}
```

**2. 各成员拜访量排名（Top 20）**
```gql
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}, _group_by: [owner], _order_by: {cnt: _desc}, _limit: 20) {
  owner
  cnt: _count(id)
}}
```

**3. 拜访量按天趋势**
```gql
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}, _group_by: [day], _order_by: {day: _asc}) {
  day: _func("to_char", _func("to_timestamp", actual_date), "YYYY-MM-DD")
  cnt: _count(id)
}}
```

**4. 拜访渠道分布**
```gql
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}, _group_by: [channel]) {
  channel
  cnt: _count(id)
}}
```
> 返回的 `channel` 是整数 value，输出时按上表映射成中文（如 `1`→面对面）。

**5. 覆盖的医生去重数（拜访覆盖率分子）**
```gql
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}) {
  covered_hcp: _distinct_count(hcp_id)
}}
```

**6. 拜访计划完成情况（visit 维度）**
```gql
{visit(_where: {plan_date: {_gte: 1717171200}}, _group_by: [status]) {
  status
  cnt: _count(id)
}}
```

---

## 场景二：会议分析（events_meeting）

**业务语义**：`events_meeting`（会议信息）是学术会议/科室会/城市会等，含状态、类型、规模、费用、参会人数等，是合规与费效分析重点。

> **费用单位是分（×100）**：`plan_cost`、`real_cost` 为「金额×100」的整数（即以分存储）。汇总后**除以 100** 得到元。`total_cost` 为会议总花费金额。

### 核心字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `meeting_name` | TEXT | 会议名称 |
| `meeting_status` | SELECT_ONE | 会议状态：`1`待提交 `2`审批中 `3`已拒绝 `4`待开始 `5`进行中 `7`已取消 `8`已完成 `10`已结束 …（共 11 项） |
| `meeting_type_id` | SELECT_ONE | 会议类型：`1`科室会 `2`城市会 `3`区域会 `4`其他会议 |
| `type` | SELECT_ONE_INT | 形式：`0`线上会 `2`线下会 `3`网络研讨会 `4`线上线下会 |
| `scale` | SELECT_ONE_INT | 规模：`1`小型 `2`中型 `3`大型学术会 |
| `is_violate` | SELECT_ONE | 是否合规：`1`不合规 `2`合规 |
| `meeting_stime` / `meeting_etime` | DATETIME | 计划开始 / 结束时间 |
| `plan_cost` / `real_cost` | INT | 计划 / 实际花费（**分，×100**） |
| `total_cost` | INT | 会议总花费金额 |
| `expected_attendance` | INT | 计划参会人数 |
| `join_num` / `confirm_num` | INT | 实际 / 确认参会人数 |
| `hcp_join_num` / `user_join_num` | INT | 外部(医生) / 内部参会人数 |
| `main_product_id` / `speaker_name` | TEXT | 主产品 / 讲者 |
| `owner` / `belong_territory` | TEXT | 拥有者 / 所属岗位 |

**常用关联**：`meeting_type`(会议类型对象)、`attender_id`(参会人 events_meeting_attender)、`meeting_cost`(费用明细)、`owner`(主办人)。

### 分析模板

**1. 团队会议状态分布**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}}, _group_by: [meeting_status]) {
  meeting_status
  cnt: _count(id)
}}
```

**2. 已完成会议的费用合计与均值（结果 ÷100 得元）**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}, meeting_status: "8"}) {
  cnt: _count(id)
  total_real_fen: _sum(real_cost)
  avg_real_fen: _avg(real_cost)
}}
```

**3. 各会议类型的数量与实际费用**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}}, _group_by: [meeting_type_id], _order_by: {total: _desc}) {
  meeting_type_id
  cnt: _count(id)
  total: _sum(real_cost)
}}
```

**4. 费用最高的会议 Top 10（明细）**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}}, _order_by: {real_cost: _desc}, _limit: 10) {
  id meeting_name meeting_type_id real_cost join_num
}}
```

**5. 预算执行率（实际/计划，取出后在输出层算比率并 ÷100 展示）**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}}) {
  total_plan_fen: _sum(plan_cost)
  total_real_fen: _sum(real_cost)
}}
```

**6. 参会规模分析**
```gql
{events_meeting(_where: {meeting_stime: {_gte: 1717171200}, meeting_status: "8"}) {
  total_join: _sum(join_num)
  avg_join: _avg(join_num)
  total_hcp: _sum(hcp_join_num)
}}
```

---

## 场景三：用户行为分析（user_behavior_details）

**业务语义**：`user_behavior_details`（用户行为详情表）是用户在小程序/H5/企微等的行为埋点明细（登录、阅读、分享、参会、观看视频、咨询AI 等）。数据量大，**务必带时间范围 + limit**。

> **重要差异**：本表**没有独立的行为时间字段**，用 `create_time`（DATETIME，秒级）作为行为发生时间；行为对象用 `target_content_id`/`target_content_name`；没有 page/duration 字段，页面来源用 `source`。

### 核心字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `create_time` | DATETIME | 行为时间（秒级） |
| `behavior_type` | SELECT_ONE | 行为类型（**字符串 value**）：`1`登录 `3`阅读 `4`分享 `8`参加会议 `11`点赞 `17`阅读时长和阅读率 `18`观看视频 `22`页面访问 `37`咨询AI …（共 38 项） |
| `behavior_value` | TEXT | 行为值 |
| `source` | SELECT_ONE | 来源：`1`小程序 `2`h5 `4`会议详情页 `7`文章详情页 `9`媒体播放器 `11`AI …（共 13 项） |
| `target_content_type` | SELECT_ONE | 对象类型：`1`文章 `2`会议 `4`音视频 `14`播客 … |
| `target_content_id` / `target_content_name` | TEXT | 对象 id / 名称 |
| `user_id` | TEXT | 行为用户 id |
| `hcp_id` | TEXT | 医生 id |
| `user_identity` | SELECT_ONE | 用户身份：`1`员工 `2`参会人 `3`讲者 `4`临时参会人 |
| `user_type` | SELECT_ONE | 用户类型：`1`医生 `2`代表 `3`员工 |
| `owner` / `belong_territory` | TEXT | 拥有者 / 所属岗位 |

**常用关联**：`meeting`(events_meeting via source_id)、`hcp`、`article`(mcm_article)、`material`(mcm_material)、`user_info`。

### 分析模板

**1. 日活（按天去重用户）**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}}, _group_by: [day], _order_by: {day: _asc}) {
  day: _func("to_char", _func("to_timestamp", create_time), "YYYY-MM-DD")
  dau: _distinct_count(user_id)
}}
```

**2. 行为类型分布**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}}, _group_by: [behavior_type], _order_by: {cnt: _desc}) {
  behavior_type
  cnt: _count(id)
}}
```
> `behavior_type` 是字符串 value，按上表映射成中文（如 `"3"`→阅读）。

**3. 热门内容 Top 20（阅读行为的 PV/UV）**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}, behavior_type: "3"}, _group_by: [target_content_id], _order_by: {pv: _desc}, _limit: 20) {
  target_content_id
  pv: _count(id)
  uv: _distinct_count(user_id)
}}
```

**4. 各来源渠道的活跃度**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}}, _group_by: [source], _order_by: {pv: _desc}) {
  source
  pv: _count(id)
  uv: _distinct_count(user_id)
}}
```

**5. 视频观看次数（behavior_type=18）**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}, behavior_type: "18"}) {
  play_cnt: _count(id)
  viewer: _distinct_count(user_id)
}}
```

**6. 某会议的参与行为（按内容关联）**
```gql
{user_behavior_details(_where: {create_time: {_gte: 1717171200}, target_content_type: "2", target_content_id: "<会议id>"}, _group_by: [behavior_type]) {
  behavior_type
  cnt: _count(id)
}}
```

---

## 跨场景小贴士

- **枚举映射**：visit/visit_item 的 `status`/`type`/`channel` 是 **INT** 选项；events_meeting 的 `meeting_status`/`meeting_type_id`、user_behavior_details 的 `behavior_type`/`source` 是 **字符串** 选项。过滤值要匹配类型（INT 不加引号、字符串加引号），输出时按本文枚举表翻译成中文。
- **金额还原**：events_meeting 的 `plan_cost`/`real_cost` 是分（×100），sum/avg 后 ÷100 展示为元。
- **时间字段各异**：visit/visit_item 用 `actual_date`，events_meeting 用 `meeting_stime`，user_behavior_details 用 `create_time`。别用错。
- **大表防爆**：`user_behavior_details` 必须带时间范围；明细查询务必 `_limit`，统计走 `_group_by`。
- **比率类指标**（完成率、执行率、覆盖率）：GQL 取分子分母，比值在输出层算。
- **下属逐人对比**：把模板里的 `_group_by:[owner]` 配合 `ListSubordinateTerritory` 的 `territory_code`→姓名映射，结论更可读（见 roles-and-data-scope.md）。`owner` 返回的是 uin（雪花 ID），展示时应映射成姓名（关联 `user_info` 或二次查询）。
- **脏数据/枚举兜底**（实测经验）：真实数据里枚举字段可能出现**未在元数据选项内的脏值**（如 `null`、`NaN`、历史或测试残留值）。按枚举字段 `_group_by` 时这些值会一并冒出来；展示时按本文枚举表归类，未知值统一归「其他/未填」，避免污染结论。必要时在 `_where` 用 `_in [合法value列表]` 过滤掉脏值。
