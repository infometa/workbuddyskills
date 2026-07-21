# ListTimesheets

## 接口描述
返回符合查询条件的所有花费工时（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/timesheets

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| entity_type | 否 | string | 对象类型，如 story、task、bug 等 | |
| entity_id | 否 | integer | 对象ID | |
| timespent | 否 | string | 花费工时 | |
| spentdate | 否 | date | 花费日期 | 支持时间查询 |
| modified | 否 | date | 最后修改时间 | 支持时间查询 |
| owner | 否 | string | 花费创建人 | |
| include_parent_story_timesheet | 否 | integer | 值=0 不返回父需求的花费 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| memo | 否 | string | 花费描述 | |
| is_delete | 否 | integer | 是否已删除。默认取 0，不返回已删除记录。取 1 返回已删除记录 | |
| limit | 否 | integer | 返回数量限制，默认30，最大200 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/timesheets?workspace_id=$TAPD_WORKSPACE_ID'
```

### 按日期查询

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/timesheets?workspace_id=$TAPD_WORKSPACE_ID&spentdate=2020-05-05'
```

### 按对象类型和对象ID查询

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/timesheets?workspace_id=$TAPD_WORKSPACE_ID&entity_type=story&entity_id=1010158231500709717'
```

### 按花费创建人查询

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/timesheets?workspace_id=$TAPD_WORKSPACE_ID&owner=anyechen&limit=3'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Timesheet": {
                "id": "1010158231001168997",
                "entity_type": "story",
                "entity_id": "1010158231500709717",
                "timespent": "8",
                "spentdate": "2020-05-05",
                "owner": "anyechen",
                "created": "2020-05-06 19:32:35",
                "workspace_id": "10158231",
                "memo": "hey"
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | ID |
| entity_type | 对象类型，如 story、task、bug 等 |
| entity_id | 对象ID |
| timespent | 花费工时 |
| spentdate | 花费日期 |
| owner | 花费创建人 |
| created | 创建时间 |
| workspace_id | 项目ID |
| modified | 最后修改时间 |
| memo | 花费描述 |
| is_delete | 是否已删除 |
