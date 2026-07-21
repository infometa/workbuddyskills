# CountWikis

## 接口描述
计算符合查询条件的 Wiki 数量并返回。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/tapd_wikis/count

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| name | 否 | string | 标题 | 支持模糊匹配 |
| modifier | 否 | string | 修改人 | |
| creator | 否 | string | 创建人 | |
| note | 否 | string | 备注 | |
| view_count | 否 | string | 浏览量 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/tapd_wikis/count?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 23
    },
    "info": "success"
}
```
