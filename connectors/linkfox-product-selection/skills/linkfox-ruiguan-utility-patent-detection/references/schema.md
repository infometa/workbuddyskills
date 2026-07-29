# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "productTitle",
    "productDescription",
    "region",
    "topNumber"
  ],
  "properties": {
    "region": {
      "type": "string",
      "default": "US",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        }
      ],
      "maxLength": 1000,
      "description": "商品想要售卖的国家/地区代码，多个用逗号分隔，当前支持 US"
    },
    "topNumber": {
      "type": "integer",
      "default": 100,
      "maximum": 200,
      "minimum": 10,
      "description": "召回数量，最大200"
    },
    "productTitle": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品标题"
    },
    "productDescription": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品描述"
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
          "title": {
            "type": "string",
            "description": "发明专利标题"
          },
          "claims": {
            "type": "string",
            "description": "权利要求"
          },
          "images": {
            "type": "array",
            "items": {},
            "description": "专利附图"
          },
          "region": {
            "type": "string",
            "description": "受理局"
          },
          "titleCn": {
            "type": "string",
            "description": "发明专利标题(中文)"
          },
          "troCase": {
            "type": "boolean",
            "description": "是否有TRO维权史"
          },
          "claimsCn": {
            "type": "string",
            "description": "权利要求(中文)"
          },
          "inventors": {
            "type": "array",
            "items": {},
            "description": "发明家 和 国家拼接 数组格式"
          },
          "troHolder": {
            "type": "boolean",
            "description": "是否是TRO权利人的专利"
          },
          "applicants": {
            "type": "array",
            "items": {},
            "description": "申请人 和 国家 拼接 数组格式"
          },
          "cpcKindRaw": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "cpc分类（原始 JSONArray）"
          },
          "similarity": {
            "type": "number",
            "description": "相似度"
          },
          "classNumList": {
            "type": "array",
            "items": {},
            "description": "类别号路径列表，格式 classNum1 > classNum2 > classNum3，由 cpcKind 结构生成"
          },
          "specification": {
            "type": "string",
            "description": "说明书"
          },
          "patentAbstract": {
            "type": "string",
            "description": "摘要"
          },
          "patentImageUrl": {
            "type": "string",
            "description": "专利封面图"
          },
          "patentValidity": {
            "type": "string",
            "description": "专利有效性 Active/Invalid"
          },
          "priorityNumber": {
            "type": "array",
            "items": {},
            "description": "优先权号 数组"
          },
          "applicationDate": {
            "type": "string",
            "description": "申请日 yyyy-MM-dd"
          },
          "globalUtilityId": {
            "type": "string",
            "description": "专利id"
          },
          "publicationDate": {
            "type": "string",
            "description": "公开日 yyyy-MM-dd"
          },
          "specificationCn": {
            "type": "string",
            "description": "说明书(中文)"
          },
          "estimatedDueDate": {
            "type": "string",
            "description": "预估到期日 yyyy-MM-dd"
          },
          "patentAbstractCn": {
            "type": "string",
            "description": "摘要（中文）"
          },
          "applicationNumber": {
            "type": "string",
            "description": "申请号"
          },
          "inventorAddresses": {
            "type": "array",
            "items": {},
            "description": "发明人地址 数组格式"
          },
          "publicationNumber": {
            "type": "string",
            "description": "公开号"
          },
          "applicantAddresses": {
            "type": "array",
            "items": {},
            "description": "权利人地址 数组格式"
          },
          "relatedPublicationDate": {
            "type": "array",
            "items": {},
            "description": "首次公开日 数组 yyyy-MM-dd"
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
    "detectId": {
      "type": "string",
      "description": "检测id"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
