# DownloadAttachment

## 接口描述
获取单个附件下载链接。每次只能请求一个附件的下载链接，下载链接默认有效时间300秒。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/attachments/down

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只能请求一个附件的下载链接。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| id | 是 | integer | 附件ID |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/attachments/down?workspace_id=$TAPD_WORKSPACE_ID&id=1210104801000028203'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Attachment": {
            "id": "1210104801000028203",
            "type": "wiki_description",
            "entry_id": "6100014242115511668",
            "filename": "OneDrive.mp4",
            "description": null,
            "content_type": "video/mp4",
            "created": "2021-04-08 15:51:27",
            "workspace_id": "10104801",
            "owner": "anyechen",
            "download_url": "https://..."
        }
    },
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 附件ID |
| type | 业务对象类型 |
| entry_id | 业务对象的ID |
| filename | 文件名 |
| description | 附件描述 |
| content_type | 文件类型 |
| created | 创建时间 |
| workspace_id | 项目ID |
| owner | 附件上传人 |
| download_url | 下载链接（有效时间300秒） |
