# DownloadDocument

## 接口描述
获取单个文档下载链接。每次只能获取一个文档下载链接。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/documents/down

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只能获取一个文档下载链接。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| id | 是 | integer | 文档ID |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/documents/down?workspace_id=$TAPD_WORKSPACE_ID&id=1010104801001648871'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Document": {
            "id": "1010104801001648871",
            "workspace_id": "10104801",
            "name": "报告标题.docx",
            "type": "",
            "folder_id": "1010104801000035293",
            "creator": "anyechen",
            "modifier": "anyechen",
            "status": null,
            "created": "2021-12-24 16:40:36",
            "modified": "2021-12-24 16:40:36",
            "download_url": "https://..."
        }
    },
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 文档ID |
| workspace_id | 项目ID |
| name | 标题 |
| type | 文档类型 |
| folder_id | 文件夹ID |
| creator | 创建人 |
| modifier | 最后修改人 |
| created | 创建时间 |
| modified | 最后修改时间 |
| download_url | 下载链接 |
