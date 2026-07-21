# MCP 工具参考

nges-data-360 的所有平台交互都通过 MCP 完成，**不使用** python 脚本。认证由 MCP 客户端 自动处理。

## 调用约定

每个工具调用分两步：

1. `mcp_get_tool_description` —— 传入 `[[serverName, toolName]]`，拿到该工具的真实参数 schema（不同环境/版本字段可能有差异，以实际返回为准）。
2. `mcp_call_tool` —— 传入 `serverName`、`toolName` 和 JSON 字符串 `arguments` 执行。

> **serverName 以 `mcp.json` 为准**。

| 用途 | MCP server | 工具（方法名） | 关键参数 |
|------|-----------|---------------|----------|
| 识别当前用户角色/岗位 | `nges` | `NgesServer__NgesStaff__GetStaffUserInfo` | 无参（当前登录用户） |
| 搜索对象（不确定对象名） | `nges` | `DataServer__MetadataService__GetObjectList` | `keyword` / `object_name` / `limit` |
| 获取对象字段与关联 | `nges` | `DataServer__MetadataService__GetObjectsByNames` | `objects: [对象名...]` |
| 获取下属岗位/人员 | `nges` | `NgesServer__NgesStaff__ListSubordinateTerritory` | `territory_code` / `level` / `yearmonth` |
| 执行/校验 GQL 查询 | `nges` | `DataServer__DataService__GraphqlQuery` | `query` / `only_validate` |

---

## 0) GetStaffUserInfo — 识别当前用户角色/岗位

数据洞察的第一步常常是「这个用户是谁、能看多大范围」。当范围模糊、需要按角色推断默认范围时，先调它。

**参数**：无（空对象 `{}`，基于当前登录用户）。

**返回**（关键字段）：

| 字段 | 说明 |
|------|------|
| `identity_tag` | **员工身份/角色** —— 角色判断的依据 |
| `name` / `uin` / `id` | 姓名 / 账号 / 用户 id |
| `current_territory` | 当前岗位 code（可直接用于 `belong_territory` 过滤） |
| `current_territory_name` | 当前岗位名称 |
| `territory_list` | 岗位列表（含 code/name/territory_role） |
| `active_role` | 生效角色列表 |

**identity_tag 取值 → 角色映射**：

| identity_tag | 角色 | 默认数据范围 |
|--------------|------|-------------|
| `representative` | 医药代表 Rep | 仅本人（`owner: $_uin`） |
| `district_manager` | 地区经理 DSM | 本人 + 下属团队（`$_territory_all`） |
| `regional_manager` | 大区经理 RSM | 整条下属链（`$_territory_all`） |

**示例**：

```jsonc
// arguments: {}  → 返回 {"identity_tag": "district_manager", "current_territory": "T_010", ...}
// 据此判定为 DSM：返回数据由行权限自动限定为其团队，直接查即可、无需手写范围；
// 角色信息用于解读口径（"你的团队…"）和决定是否逐人对比
```

---

## 1) GetObjectList — 搜索对象

仅在**不确定准确对象名**时使用，先定位对象再取字段。

**参数**（常见）：

| 参数 | 说明 |
|------|------|
| `keyword` | 模糊搜索关键词（按对象名/中文名） |
| `object_name` | 精确对象名 |
| `limit` / `offset` | 分页 |

**返回**：`{ "count": N, "objects": [ { name, display_name, ... } ] }`

**示例**：

```jsonc
// mcp_call_tool arguments
{ "keyword": "visit", "limit": 10 }
```

---

## 2) GetObjectsByNames — 获取对象字段与关联

编写 GQL 前的**必经步骤**，用来确认字段名、`value_type` 和关联关系。可一次传多个对象。

**参数**：

```jsonc
{ "objects": ["visit", "visit_item"] }
```

**返回**（结构以实际为准，关注以下字段）：

```jsonc
{
  "list": [
    {
      "object": {
        "name": "visit", "display_name": "拜访计划表",
        "relations": [
          { "virtual_field": "hco", "target_object": "hco",
            "relation_type": "ONE_TO_ONE", "real_field": "hco_id", "target_field": "id" },
          { "virtual_field": "visit_item", "target_object": "visit_item",
            "relation_type": "ONE_TO_MANY", "real_field": "id", "target_field": "visit_id" }
        ]
      },
      "fields": [
        { "name": "id",          "display_name": "ID",       "value_type": "TEXT" },
        { "name": "actual_date", "display_name": "实际拜访日期", "value_type": "DATETIME" },
        // SELECT_ONE_INT：选项在 select_one_int_option，value 为整数
        { "name": "status", "display_name": "拜访状态", "value_type": "SELECT_ONE_INT",
          "select_one_int_option": { "options": [
            { "value": 2, "label": "已完成" }, { "value": 3, "label": "已取消" } ] } },
        // SELECT_ONE（字符串选项）：选项在 select_one_option，value 为字符串
        { "name": "record_type", "display_name": "记录类型", "value_type": "SELECT_ONE",
          "select_one_option": { "options": [ { "value": "oldChannel", "label": "拜访渠道" } ] } }
      ]
    }
  ]
}
```

**读这份返回时重点看**：

- `fields[].name` —— GQL 里要用的真实字段名。
- `fields[].value_type` —— 决定过滤/聚合时值的写法（见 gql-syntax.md 类型对照）。`DATETIME` 是**秒级**时间戳。
- **枚举选项**：`SELECT_ONE_INT` 选项在 `select_one_int_option.options`（value 为**整数**，过滤不加引号）；`SELECT_ONE`/`SELECT_MANY` 选项在 `select_one_option`/`select_many_option`（value 为**字符串**，过滤加引号）。过滤值一律用选项的 `value` 而非 `label`，展示时再用 label 翻译。
- `object.relations` —— 关联字段：`virtual_field`(查询用的虚拟字段名) + `target_object`(目标对象) + `relation_type`(如 ONE_TO_ONE/ONE_TO_MANY/ONE_TO_MANY_BY_IDS) + `real_field`/`target_field`。
- `AUTO_NUMBER`/`FORMULA`/`ROLLUP_SUMMARY` 类型是虚拟字段，`_all` 不返回，需要时显式列出。

---

## 3) ListSubordinateTerritory — 获取下属岗位/人员

「根据当前登录用户岗位获取所有下属岗位及岗位对应的用户（允许空岗）」。当需要按"每个下属"拆开分析、或只看某一层级下属时使用。拿到下属的 `territory_code` 列表后，放进 GQL 的 `belong_territory: {_in: [...]}`。

> 若只是"我和我所有下属合起来看"，**不必调用此接口**，也无需手写范围——行权限会自动按角色覆盖团队数据，直接查即可（见 roles-and-data-scope.md）。

**参数**（均可选）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `yearmonth` | string | 岗位架构的年月（如 `"202606"`），不传取当前最新 |
| `territory_code` | string | 起始岗位 code，不传使用当前登录用户的岗位 |
| `level` | int | 最大展示下属层级：`0` 不限制、`n` 展示 n 级，不传默认不限制 |

**返回**：`{ "data": [ TerritorySubordinateInfo ] }`，是一棵**岗位树**（按层级递归）。每个节点：

| 字段 | 说明 |
|------|------|
| `territory_code` | 岗位 code —— **代入 GQL `belong_territory` 的就是它** |
| `name` / `account` | 该岗位负责人姓名 / 账号 |
| `job_id` / `job_name` | 岗位/职务 id 与名称 |
| `job_role_codes` | 岗位角色列表（可据此识别 Rep/DSM/RSM 等角色） |
| `Subordinate_list` | **下级节点数组**（递归，需自行展平收集所有层级的 code） |

> 当前登录用户若无岗位上下文（如纯 admin 账号），`data` 为空数组属正常。
> 另有 `SearchSubordinateTerritory`（按 `user_name`/`job_name` 模糊搜下属，返回扁平 `UserTerritoryInfo` 列表）可按需使用。

**用法示例**：

```jsonc
// 1. 取下属岗位树（不限层级）
//    arguments: {"level": 0}
//    → 展平 Subordinate_list，收集所有 territory_code，如 ["T_001","T_002","T_003"]
// 2. 代入 GQL，逐岗位对比拜访量
{
  "query": "{visit_item(_where:{belong_territory:{_in:[\"T_001\",\"T_002\",\"T_003\"]}, status:2}, _group_by:[belong_territory], _order_by:{cnt:_desc}){belong_territory cnt:_count(id)}}"
}
// 3. 用步骤1返回里的 name/job_name 把 territory_code 映射成可读姓名再展示
```

---

## 4) GraphqlQuery — 执行/校验查询

执行重楼 GQL，返回业务数据。

**参数**：

| 参数 | 说明 |
|------|------|
| `query` | GQL 语句字符串 |
| `only_validate` | 可选，`true` 时只做解析+元数据校验的 dry-run，不实际取数 |

**返回**（实测结构）：

```jsonc
{
  "affect_rows": "0",                 // 字符串
  "data": {                            // 对象，键为查询的对象名
    "visit_item": [                    // 普通/分组查询：值为记录数组
      { "cnt": 1844, "channel": 1 },
      { "cnt": 1573, "channel": 2 }
    ]
  }
}
```

- `data` 是**已结构化的对象**（不是 JSON 字符串），按 `data.<对象名>` 取结果数组。
- 聚合字段名**不带下划线**：GQL 写 `_count`/`_sum`，返回是 `count`/`sum`（建议用别名 `cnt: _count(id)` 规避）。
- 用了 `_aggregate` 时该对象的值为 `{ "_aggregate": {"count": N}, "_data": [...] }`。
- 枚举字段原样返回 value：`SELECT_ONE_INT` 返回整数（如 `channel:1`）、`SELECT_ONE` 返回字符串（如 `meeting_status:"8"`）；未填值为 `null`。展示时按 common-scenarios.md 的枚举表翻译。

**示例**：

```jsonc
{ "query": "{events_meeting(_group_by:[meeting_status],_order_by:{cnt:_desc}){meeting_status cnt:_count(id)}}" }
```

**dry-run 校验**：

```jsonc
{ "query": "{visit(...){...}}", "only_validate": true }
```

校验成功返回 `affect_rows:"0"` 且 data 为 null；失败返回业务错误码与原因，据此修正 GQL。

---

## 常见错误处理

| 现象 | 原因 | 处理 |
|------|------|------|
| `xxx not found`(13005) | 对象名不存在 | 用 `GetObjectList` 搜正确对象名 |
| `field xxx not found` | 字段名错或无列权限 | 重新 `GetObjectsByNames` 核对字段 |
| 聚合值始终为 0 / 缺字段 | 读了带下划线的返回键 | 返回键用 `count`/`sum`（无下划线） |
| 结果比预期少 | 行/列权限自动过滤 | 正常；确认当前用户数据范围 |
| `invalid input syntax` | 过滤值类型不匹配 | 对照 `value_type` 修正值写法 |
| `Authentication required` | 未登录 / token 失效 | 重新登录后重试 |
