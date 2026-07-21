# CountTimesheets

## 接口描述
计算符合查询条件的花费工时数量并返回。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/timesheets/count

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 只返回花费工时数量。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| entity_type | 否 | string | 对象类型，如 story、task、bug 等 | |
| entity_id | 否 | integer | 对象ID | |
| timespent | 否 | string | 花费工时 | |
| spentdate | 否 | date | 花费日期 | 支持时间查询 |
| owner | 否 | string | 花费创建人 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| memo | 否 | string | 花费描述 | |
| is_delete | 否 | integer | 是否已删除。默认取 0，不返回已删除记录。取 1 返回已删除记录 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/timesheets/count?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 14
    },
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| count | 符合条件的花费工时数量 |
