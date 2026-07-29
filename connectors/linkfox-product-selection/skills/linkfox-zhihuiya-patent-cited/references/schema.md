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
          "citedBy3y": {
            "type": "integer",
            "description": "3年内被引用次数"
          },
          "citedBy5y": {
            "type": "integer",
            "description": "5年内被引用次数"
          },
          "citedByPatents": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "被引用专利"
          },
          "citedBySimpleFamily": {
            "type": "integer",
            "description": "简单同族被引专利数量"
          },
          "citedByInpadocFamily": {
            "type": "integer",
            "description": "INPADOC同族被引专利数量"
          },
          "citedByPatsnapFamily": {
            "type": "integer",
            "description": "PatSnap同族被引专利数量"
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
