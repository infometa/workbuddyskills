# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "imageUrl"
  ],
  "properties": {
    "imageUrl": {
      "type": "string",
      "maxLength": 1000,
      "description": "检测的版权图片URL"
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
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "cosine": {
            "type": "number",
            "description": "检测产品与违规产品相似度"
          },
          "pdTitle": {
            "type": "string",
            "description": "匹配到的违规产品标题"
          },
          "pdImgOssUrl": {
            "type": "string",
            "description": "匹配到的违规产品图片 URL"
          },
          "pdTitleCHNCensored": {
            "type": "string",
            "description": "匹配到的违规产品中文标题"
          }
        }
      },
      "description": "检测出的政策违规产品列表"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "记录数"
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
    "detectId": {
      "type": "string",
      "description": "检测记录 id"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
