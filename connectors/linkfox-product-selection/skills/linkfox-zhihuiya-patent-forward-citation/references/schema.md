# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "patentId": {
      "type": "string",
      "maxLength": 60000,
      "description": "专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条"
    },
    "patentNumber": {
      "type": "string",
      "maxLength": 60000,
      "description": "公开公告号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条"
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
          "citedOthers": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "引用非专利文献"
          },
          "citedPatents": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "引用专利"
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
