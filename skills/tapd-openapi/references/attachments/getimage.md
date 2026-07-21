# GetImage

## 接口描述
获取单个图片下载链接。每次只能请求一张图片的下载链接，下载链接默认有效时间300秒。文件名后缀仅限 png、gif、jpg、jpeg、bmp。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/files/get_image

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只能请求一张图片的下载链接。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| image_path | 是 | string | 图片路径，支持完整url地址，图片所属项目必须和传入的项目ID一致 |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/files/get_image?workspace_id=$TAPD_WORKSPACE_ID&image_path=/tfl/captures/2023-07/tapd_10104801_base64_1689686020_146.png'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Image": {
            "workspace_id": "10104801",
            "filename": "tapd_10104801_base64_1689686020_146.png",
            "type": "png",
            "value": "/tfl/captures/2023-07/tapd_10104801_base64_1689686020_146.png",
            "download_url": "https://file.tapd.cn/attachments/tmp_download/..."
        }
    },
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| workspace_id | 项目ID |
| filename | 图片文件名 |
| type | 文件类型 |
| value | 图片路径 |
| download_url | 单个图片下载地址（有效时间300秒） |
