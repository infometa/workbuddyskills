# ListAttachments

## 接口描述
返回符合查询条件的所有附件（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/attachments

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | |
| type | 否 | string | 类型 | |
| entry_id | 否 | integer | 依赖对象ID | |
| filename | 否 | string | 附件名称 | |
| owner | 否 | string | 上传人 | |
| limit | 否 | integer | 返回数量限制，默认30 | |
| page | 否 | integer | 页码，默认1 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/attachments?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Attachment": {
                "id": "1210104801000028203",
                "type": "wiki_description",
                "entry_id": "6100014242115511668",
                "filename": "OneDrive.mp4",
                "content_type": "video/mp4",
                "created": "2020-08-25 11:24:44",
                "workspace_id": "10104801",
                "owner": "anyechen"
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 附件ID |
| type | 类型 |
| entry_id | 依赖对象ID |
| filename | 附件名称 |
| content_type | 内容类型 |
| created | 创建时间 |
| workspace_id | 项目ID |
| owner | 上传人 |
