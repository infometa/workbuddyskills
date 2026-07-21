# UpdateTimesheet

## 接口描述
更新花费工时，返回花费工时更新后的数据。每次只允许更新一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/timesheets

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| id | 是 | integer | ID |
| workspace_id | 是 | integer | 项目ID |
| timespent | 否 | string | 花费工时 |
| timeremain | 否 | string | 剩余工时 |
| memo | 否 | string | 花费描述 |

## 请求示例

```bash
curl -s -X POST -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/timesheets" \
  -d '{"id":"1010158231001169003","workspace_id":"'"${TAPD_WORKSPACE_ID}"'","timespent":"3"}'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Timesheet": {
            "id": "1010158231001169003",
            "entity_type": "story",
            "entity_id": "1010158231500709717",
            "timespent": "3",
            "spentdate": "2020-05-05",
            "owner": "anyechen",
            "created": "2020-05-06 22:08:35",
            "workspace_id": "10158231",
            "memo": "hey"
        }
    },
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
| timeremain | 剩余工时 |
| spentdate | 花费日期 |
| owner | 花费创建人 |
| created | 创建时间 |
| workspace_id | 项目ID |
| memo | 花费描述 |
