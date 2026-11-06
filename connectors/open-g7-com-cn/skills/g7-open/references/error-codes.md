# 错误码与排查

## 先看 `error.code`（MCP 层）

| `error.code` | 是否有 `upstream_code` | 含义 | 处理 |
|---|---|---|---|
| `invalid_arguments` | 否 | 请求参数与 `input_schema` 不符 | 按 describe 重建参数，不要重试 |
| `api_not_found` | 否 | `operation_id` 不存在或未授权 | 回 `search_platform_apis` 重检索 |
| `upstream_business_error` | 是 | 平台业务规则拒绝 | 转述 `message`；按 `upstream_code` 决定改参数还是换查询 |
| `internal_error` | 否 | 平台内部异常（也可能是参数未被正确映射） | 重试 1 次；仍失败给 `_source.trace_id` / `error.trace_id` |

`invalid_arguments` 的 message 通常会直接提示原因，例如「参数校验失败：arguments.limit 不是可接受的参数；请先调用 describe_platform_api」——说明该接口是 `POST /_search` 形态，参数要包在 `body` 里。

## 实测到的 `upstream_code`

| code | message 片段 | 触发方式 | 怎么办 |
|---|---|---|---|
| `8800010123` | 车辆不存在或无权访问 | `getVehicle` 传不存在的 id | 换 id，或确认当前租户有没有这辆车 |
| `8800000003` | 参数值非法[…=BADOP]，不是有效的枚举值 | `filter.conditions[].operator` 传了非法枚举 | 按 describe 的 enum 重填 |
| `8800018069` | filter 不能为空 | 事件检索没传 filter | 补 filter |
| `8800018070` | filter 需要包含 start_time / end_time / trigger_time | 事件 filter 只有条件没有时间窗 | 补时间窗（≤31 天） |

## 文档中列出的常见 `upstream_code`

| code | 说明 |
|---|---|
| `8800010121` | 路径参数 id 格式非法（要平台内部 ID 整数或 `key:value` 外部 ID） |
| `8800010122` | 外部 ID 匹配到多条记录，改用平台内部 ID |
| `8800010125` | 系统内部异常 |
| `8800010126` | 标签服务调用失败，稍后重试 |
| `8800018059` | 分页游标无效或已过期，重新从头查 |
| `8800018060` / `8800018061` | 资产 ID / 司机 ID 列表超上限（100） |
| `8800018065` | feed 类接口禁止传 `start_time` / `end_time` / `modified_time` |
| `8800018066` | 游标失效：本次过滤条件与首次查询不一致 |

注意 `8800010121` 有映射缺口：实测 `getVehicle(id="abc/def")` 返回的是 `internal_error` 而不是 `8800010121`。所以遇到 `internal_error` 时，**先怀疑参数格式，再怀疑平台故障**。

## 平台原始 msg（直连 OpenAPI 时常见，MCP 下已封装）

| 原始 msg | 含义 |
|---|---|
| `signature error, the sign string should be: ...` | 签名不通过（MCP 场景不会出现，走 OAuth Bearer） |
| `no permission, api can't access` | 凭证无权调用，或环境与凭证不匹配 |
| `api not exists` | Path 不存在或接口已下线 |
| `QPS已达到上限` | 触发限流，退避重试 |

## 返回成功但没数据

按顺序排查：

1. **时间窗**：事件类必须给 `start_time` / `end_time`，且跨度 ≤31 天。
2. **范围条件**：资产 ID / 组织 ID / 标签是否把数据过滤掉了。
3. **环境**：沙箱是模拟数据，用正式环境的条件查沙箱经常是空数组。
4. **权限**：`scope` 只说明能调这个接口，数据范围还会按企业/组织/标签收窄。

## 报障给用户什么

- `_source.trace_id`（成功响应）或 `error.trace_id`（失败响应）
- `_source.fetched_at` 请求时间
- `_source.api` 或 describe 拿到的 `path` + method
- 脱敏后的关键参数

不要贴完整响应体，不要贴任何密钥。
