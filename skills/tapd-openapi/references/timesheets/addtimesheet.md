# AddTimesheet

## 接口描述
新建花费工时，返回新建花费工时的数据。一次插入一条数据。注意同一 entity_type、entity_id、spentdate、owner 只能有一条工时记录。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/timesheets

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| entity_type | 是 | string | 对象类型，如 story、task、bug 等 |
| entity_id | 是 | integer | 对象ID |
| timespent | 是 | string | 花费工时 |
| owner | 是 | string | 花费创建人 |
| timeremain | 否 | string | 剩余工时 |
| spentdate | 否 | date | 花费日期 |
| memo | 否 | string | 花费描述 |

## 请求示例

```bash
curl -s -X POST -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/timesheets" \
  -d '{"workspace_id":"'"${TAPD_WORKSPACE_ID}"'","entity_type":"story","entity_id":"1010158231500709717","owner":"anyechen","timespent":"2","spentdate":"2020-05-05"}'
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
            "timespent": "2",
            "spentdate": "2020-05-05",
            "owner": "anyechen",
            "created": "2020-05-06 22:08:35",
            "workspace_id": "10158231",
            "memo": null
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
