# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "lang": {
      "type": "string",
      "default": "en",
      "examples": [
        {
          "value": "en",
          "summary": "英文"
        },
        {
          "value": "cn",
          "summary": "中文"
        },
        {
          "value": "jp",
          "summary": "日语"
        }
      ],
      "maxLength": 1000,
      "description": "翻译语言，支持cn、en、jp"
    },
    "patentId": {
      "type": "string",
      "maxLength": 60000,
      "description": "专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开"
    },
    "patentNumber": {
      "type": "string",
      "maxLength": 60000,
      "description": "公开(公告)号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开"
    },
    "replaceByRelated": {
      "type": "integer",
      "default": 0,
      "examples": [
        {
          "value": "1",
          "summary": "是"
        },
        {
          "value": "0",
          "summary": "否"
        }
      ],
      "description": "摘要无法获取时是否用同族专利摘要替代：1是 0否"
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
          "title": {
            "type": "string",
            "description": "标题翻译"
          },
          "patentId": {
            "type": "string",
            "description": "专利Id"
          },
          "pnRelated": {
            "type": "string",
            "description": "替代专利的公开号（仅当使用同族专利替代时提供）"
          },
          "abstractText": {
            "type": "string",
            "description": "摘要翻译"
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
