# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "limit": {
      "type": "string",
      "default": "100",
      "maxLength": 1000,
      "description": "返回图片总量，最大100"
    },
    "offset": {
      "type": "string",
      "maxLength": 1000,
      "description": "偏移量"
    },
    "patentId": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利ID"
    },
    "patentNumber": {
      "type": "string",
      "maxLength": 1000,
      "description": "公开(公告)号"
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
          "pn": {
            "type": "string",
            "description": "公开(公告)号"
          },
          "patentId": {
            "type": "string",
            "description": "专利Id"
          },
          "imageType": {
            "type": "string",
            "description": "图片类型"
          },
          "fulltextImagePath": {
            "type": "string",
            "description": "图片路径"
          }
        }
      },
      "description": "专利列表"
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
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
