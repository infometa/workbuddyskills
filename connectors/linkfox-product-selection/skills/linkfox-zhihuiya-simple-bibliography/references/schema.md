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
      "description": "专利ID（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个专利ID相互之间用英文[,]隔开，最大支持100个"
    },
    "patentNumber": {
      "type": "string",
      "maxLength": 60000,
      "description": "公开公告号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个公开公告号相互之间用英文[,]隔开，最大支持100个"
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
          "gbc": {
            "type": "array",
            "items": {},
            "description": "GBC分类号列表"
          },
          "loc": {
            "type": "array",
            "items": {},
            "description": "LOC分类号列表"
          },
          "kind": {
            "type": "string",
            "description": "专利类型代码"
          },
          "title": {
            "type": "string",
            "description": "专利标题"
          },
          "country": {
            "type": "string",
            "description": "国家代码"
          },
          "cpcMain": {
            "type": "string",
            "description": "CPC主分类号"
          },
          "ipcMain": {
            "type": "string",
            "description": "IPC主分类号"
          },
          "patentId": {
            "type": "string",
            "description": "专利ID"
          },
          "assignees": {
            "type": "array",
            "items": {},
            "description": "专利权人列表"
          },
          "inventors": {
            "type": "array",
            "items": {},
            "description": "发明人列表"
          },
          "applicants": {
            "type": "array",
            "items": {},
            "description": "申请人列表"
          },
          "cpcFurther": {
            "type": "array",
            "items": {},
            "description": "CPC副分类号列表"
          },
          "ipcFurther": {
            "type": "array",
            "items": {},
            "description": "IPC副分类号列表"
          },
          "patentType": {
            "type": "string",
            "description": "专利类型"
          },
          "citedPatents": {
            "type": "array",
            "items": {},
            "description": "引用专利列表"
          },
          "pctEntryDate": {
            "type": "string",
            "description": "PCT进入日期"
          },
          "applicationNo": {
            "type": "string",
            "description": "申请号"
          },
          "pctFilingDate": {
            "type": "string",
            "description": "PCT申请日期"
          },
          "priorityClaims": {
            "type": "array",
            "items": {},
            "description": "优先权声明列表"
          },
          "abstractContent": {
            "type": "string",
            "description": "专利摘要"
          },
          "applicationDate": {
            "type": "string",
            "description": "申请日期"
          },
          "citedNonPatents": {
            "type": "array",
            "items": {},
            "description": "引用非专利文献列表"
          },
          "publicationDate": {
            "type": "string",
            "description": "公开日期"
          },
          "publicationKind": {
            "type": "string",
            "description": "公开类型代码"
          },
          "pctApplicationNo": {
            "type": "string",
            "description": "PCT申请号"
          },
          "assigneeAddresses": {
            "type": "array",
            "items": {},
            "description": "专利权人地址列表"
          },
          "publicationNumber": {
            "type": "string",
            "description": "公开号"
          },
          "publicationCountry": {
            "type": "string",
            "description": "公开国家"
          }
        }
      },
      "description": "著录项列表"
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
    },
    "allRecordsCount": {
      "type": "integer",
      "description": "总记录数"
    }
  }
}
```

</details>
