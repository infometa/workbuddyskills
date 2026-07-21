# 角色体系与数据范围

数据洞察里最容易出错的一环是**数据范围**：同一个问题，医药代表问的是"我自己的"，经理问的是"我整个团队的"。好消息是——**重楼的行权限已经按角色把范围管好了**，你大多数时候不用操心，但要理解它的运作方式，才能在该收窄时收窄、该解释口径时解释清楚。

## 1) 角色识别与组织层级

**如何识别角色**：调用 MCP `GetStaffUserInfo`（`NgesStaff`，无参，基于当前登录用户）获取 `identity_tag` 字段，对照下表判断。返回里的 `current_territory`（当前岗位 code）、`territory_list`、`active_role` 也可辅助理解其岗位。

医药行业销售团队是层级结构，下级数据自动归集到上级：

| identity_tag | 角色 | 层级 | 行权限自动返回的范围 |
|--------------|------|------|---------------------|
| `representative` | 医药代表 Rep | 最基层，对接 HCP/医生 | 仅本人产生的数据 |
| `district_manager` | 地区经理 DSM | 管若干 Rep | 本人 + 直属 Rep 团队 |
| `regional_manager` | 大区经理 RSM | 管若干 DSM | 整条下属链（DSM + 其下 Rep） |

> 判断逻辑：**基层（representative）看自己，管理者（district_manager/regional_manager）看下属链**。若 `identity_tag` 为空或非上述值（如管理员、其他自定义身份），结合 `active_role`/`territory_list` 判断，或直接按用户问法理解范围。

## 2) 默认：依赖行权限，不手写范围

**重楼按角色配置了行权限，执行 GQL 时会自动注入对应的数据范围过滤。** 所以默认就是：**直接查询，不加 `owner`/`belong_territory`**。Rep 自动只拿到本人数据，DSM/RSM 自动拿到团队/下属链数据。

```gql
# DSM 直接查本月拜访量 —— 行权限自动限定为其团队，无需任何范围条件
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}) {_aggregate{_count}}}
```

> 手动再叠加 `belong_territory`/`owner` 不仅多余，还可能与行权限取交集导致结果偏窄。把范围交给行权限，自己专注**指标和维度**。

**角色识别的真正价值**在于解读与措辞：知道当前是 DSM，就明白返回的是"团队合计"，洞察里应说"你的团队本月…"；知道是 Rep，就说"你本月…"。同一句 GQL，不同角色执行会自动返回不同范围的数据。

## 3) 数据归属字段（显式收窄/分组时才用到）

每条业务数据带这些归属字段，**默认不需要拿它们做过滤**，仅在第 4 节的例外场景里用于显式收窄或分组：

| 字段 | 含义 | 何时用到 |
|------|------|---------|
| `owner` | 数据拥有者 uin | 管理者"只看自己"时 `owner: $_uin`；逐人对比时 `_group_by:[owner]` |
| `belong_territory` | 所属岗位 code | 聚焦特定下属时 `_in [指定code]`；逐岗位对比时 `_group_by` |
| `belong_org` | 所属组织 code | 按组织维度分组时 |
| `create_by` | 创建人 uin | 按创建人统计时 |

## 4) 例外：需要显式收窄范围的场景

### 4.1 管理者只看自己

DSM/RSM 默认看到整个团队；若用户明确"只看**我自己**的"，用 `owner: $_uin` 主动收窄：

```gql
{visit_item(_where: {owner: $_uin, actual_date: {_gte: 1717171200}, status: 2}) {_aggregate{_count}}}
```

### 4.2 按每个成员拆开对比

行权限已把数据限定在可见集合内，直接 `_group_by: [owner]` 就是"逐个可见成员对比"，**无需任何范围条件**：

```gql
# 各成员本月拜访量排名（行权限已限定团队，_group_by 即逐人拆分）
{visit_item(_where: {actual_date: {_gte: 1717171200}, status: 2}, _group_by: [owner], _order_by: {cnt: _desc}) {
  owner
  cnt: _count(id)
}}
```

> `owner` 返回的是 uin（雪花 ID），展示时映射成姓名更可读（关联 `user_info` 或二次查询）。

### 4.3 只看某几个特定下属/某层级

当用户要"只看张三、李四"或"只看某一层级下属"时，才需要显式枚举 territory：

1. 调 `ListSubordinateTerritory`（入参 `territory_code`/`level`/`yearmonth` 均可选）→ 返回下属岗位树。
2. 递归展平 `Subordinate_list`，收集目标的 `territory_code`，并保留 `territory_code → name/job_name` 映射用于展示。
3. 显式 `belong_territory: {_in: [...]}` 收窄：

```gql
# 指定几个下属的本月拜访量
{visit_item(_where: {belong_territory: {_in: ["T_001","T_002"]}, actual_date: {_gte: 1717171200}, status: 2}, _group_by: [belong_territory]) {
  belong_territory
  cnt: _count(id)
}}
```

> 常规"全体下属逐人对比"用 4.2 的 `_group_by` 即可，不必走这一步；只有"点名某几个"才需要显式 `_in`。

## 5) 决策速查

```
默认                      → 不加范围条件，直接查（行权限按角色自动过滤）
管理者要"只看自己"        → 加 owner: $_uin
要"逐个成员对比"          → _group_by: [owner]（无需范围条件）
要"只看某几个特定下属"    → ListSubordinateTerritory 取 code → belong_territory: {_in: [...]}
```

## 6) 注意

- **行权限是默认且权威的范围来源**：即使不写范围条件，也只会返回当前用户有权看的数据；越权数据查不到属正常。不要为"保险"而手动叠加范围，反而可能缩小结果。
- **系统变量按需备用**：GQL 仍内置 `$_uin`、`$_territory`、`$_territory_all`、`$_org_all` 等（按登录态展开）。在行权限自动过滤的前提下通常用不到；个别需要手动表达"本岗及下属"的特殊场景可用 `belong_territory: {_in: $_territory_all}`。
- **口径要在输出里讲清楚**：结果里注明是"本人 / 团队（含下属）/ 指定下属"，避免用户误读——尤其因为范围是行权限隐式决定的，更要主动说明。
