# 查询创意组件库 (components/get)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| filtering | struct[] | 过滤条件，支持按 `component_type`、`component_id`、`created_time` 等字段过滤 |
| fields | string[] | 指定返回字段，如 `component_id`、`component_name`、`component_value`、`component_type` |
| page | integer | 页码，默认 1 |
| page_size | integer | 每页条数，默认 10，最大 100 |

> **脚本层说明**：`get-components.mjs` 已封装该接口，传入 `account_id` 和 `component_type` 即可。

## 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| list[].component_id | int64 | 组件唯一标识，填入 `creative_components` 使用 |
| list[].component_type | enum | 组件类型 |
| list[].component_name | string | 组件名称 |
| list[].component_value | struct | 组件内容详情 |
| list[].similarity_status | enum | 相似度检测状态 |
| page_info.total_number | integer | 组件总数 |
