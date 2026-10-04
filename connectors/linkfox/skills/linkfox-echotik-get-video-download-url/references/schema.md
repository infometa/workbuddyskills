# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "url"
  ],
  "properties": {
    "url": {
      "type": "string",
      "maxLength": 1000,
      "description": "视频地址, 支持 https://vt.tiktok.com/xxx 短链或 https://www.tiktok.com/@user/video/xxx 两种格式"
    }
  }
}
```

</details>

## 原始 Output Schema

<details>
<summary>展开查看完整 Output Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "columns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "渲染的列"
    },
    "playUrl": {
      "type": "string",
      "description": "视频播放地址"
    },
    "videoId": {
      "type": "string",
      "description": "视频ID"
    },
    "coverUrl": {
      "type": "string",
      "description": "视频封面地址"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "downloadUrl": {
      "type": "string",
      "description": "视频下载地址(含水印)"
    },
    "dynamicCoverUrl": {
      "type": "string",
      "description": "动态封面地址"
    },
    "noWatermarkDownloadUrl": {
      "type": "string",
      "description": "视频下载地址(无水印)"
    }
  }
}
```

</details>
