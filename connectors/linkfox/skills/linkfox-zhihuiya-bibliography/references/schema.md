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
            "description": "公开公告号"
          },
          "exdt": {
            "type": "integer",
            "description": "智慧芽专利预估到期日"
          },
          "agency": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "申请代理机构"
          },
          "agents": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "专利申请人"
          },
          "patentId": {
            "type": "string",
            "description": "专利ID"
          },
          "abstracts": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "专利摘要"
          },
          "assignees": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "当前申请(专利权)人"
          },
          "examiners": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "审查员信息"
          },
          "inventors": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "发明人"
          },
          "applicants": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "原始申请人"
          },
          "patentType": {
            "type": "string",
            "description": "专利类型，其中APPLICATION：发明申请，PATENT：授权发明，UTILITY：实用新型，DESIGN：外观设计"
          },
          "inventionTitle": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "专利标题语言和名称"
          },
          "priorityClaims": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "优先权声明"
          },
          "classificationFi": {
            "type": "array",
            "items": {},
            "description": "FI分类号"
          },
          "relatedDocuments": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "分案继续申请信息"
          },
          "classificationCpc": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "classificationGbc": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "classificationLoc": {
            "type": "array",
            "items": {},
            "description": "LOC分类号"
          },
          "classificationUpc": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "classificationIpcr": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "classificationFterm": {
            "type": "array",
            "items": {},
            "description": "F_term分类号"
          },
          "applicationReference": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "publicationReference": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "referenceCitedOthers": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "引用非专利文献"
          },
          "referenceCitedPatents": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "引用专利文献"
          },
          "pctOrRegionalFilingData": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "datesOfPublicAvailability": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "pctOrRegionalPublishingData": {
            "type": "object",
            "required": [],
            "properties": {}
          }
        }
      },
      "description": "著录项目数据列表"
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
