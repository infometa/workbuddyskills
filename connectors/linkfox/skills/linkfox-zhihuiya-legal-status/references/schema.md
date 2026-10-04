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
      "description": "公开(公告)号（专利id和公开号两个参数必须要有一个，如果两个都存在，会优先使用专利id），多个用英文逗号隔开，上限100条"
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
          "legalDate": {
            "type": "integer",
            "description": "法律状态更新日期"
          },
          "eventStatus": {
            "type": "array",
            "items": {},
            "description": "法律事件，如：权利转移-Transfer，许可-License，质押/担保-Pledge，信托-Trust，异议-Opposition，复审-Re-examination，海关备案-Customs，诉讼-Litigation，保全-Preservation，无效程序-Invalid-procedure，口头审理-Oral-procedure，国防解密-Declassification，一案双申-Double application"
          },
          "legalStatus": {
            "type": "array",
            "items": {},
            "description": "法律状态，如：公开-Published，实质审查-Examining，授权-Granted，避重授权-Double，放弃-未指定类型-Abandoned-Undetermined，放弃-主动放弃-Abandoned-Voluntarily，放弃-视为放弃-Abandoned-Deemed，撤回-未指定类型-Withdrawn-Undetermined，撤回-主动撤回-Withdrawn-Voluntarily，撤回-视为撤回-Withdrawn-Deemed，驳回-Rejected，全部撤销-Revoked，期限届满-Expired，未缴年费-Non-Payment，权利恢复-Restoration，权利终止-Ceased，部分无效-P-Revoked，申请终止-Discontinuation，PCT国际公布-PCT published，PCT进入指定国（指定期内）-PCT entering(designated period)，PCT进入指定国（指定期满）-PCT entering(designated expiration)，PCT未进指定国-PCT unentered"
          },
          "simpleLegalStatus": {
            "type": "array",
            "items": {},
            "description": "简单法律状态，如：失效-Inactive，有效-Active，审中-Pending，未确认-Undetermined，PCT指定期内-PCT designated period，PCT指定期满-PCT designated expiration"
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
