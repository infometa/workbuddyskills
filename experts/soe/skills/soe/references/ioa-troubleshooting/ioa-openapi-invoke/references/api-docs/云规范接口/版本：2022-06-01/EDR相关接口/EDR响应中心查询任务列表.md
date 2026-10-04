## 1. 接口描述

EDR响应中心查询任务列表，私有化调用path为：/capi/EDR/ListEDRRespondTasks，从8.6P1版本开始支持

## 2. 输入参数


| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) |  过滤条件、分页参数<br/><li>CreateTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按发生时间过滤。</li> <li>Status - string - 是否必填：否 - 操作符: eq - 排序支持：是 - 按状态过滤。</li> <li>Type - string - 是否必填：否 - 操作符: eq - 排序支持：是 - 按响应类型过滤。</li> <li>Action - string - 是否必填：否 - 操作符: eq - 排序支持：是 - 按处置动作过滤。</li> <li>Ostype - string - 是否必填：否 - 操作符: eq - 排序支持：是 - 按系统平台过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [ListEDRRespondTasksData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ListEDRRespondTasksData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ListEDRRespondTasks
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "Data": {
      "Items": [
        {
          "RecordTotal": 1,
          "RecordDoneTotal": 0,
          "RespondRuleId": 1087,
          "RespondRuleName": "test",
          "Action": "scan_kill_virus",
          "EventName": "",
          "IncidentId": 0,
          "IncidentName": "",
          "DoneTime": 1765369660,
          "CreateBy": "700001380679",
          "Status": 3,
          "Ostype": 0,
          "DomainInstanceId": 1,
          "Type": 0,
          "Description": "from rule(71094): 可疑的进程父进程",
          "CreateTime": 1765369658,
          "TaskSeq": 209652,
          "Id": 132612,
          "EventId": 0,
          "ScopeObjName": [
            "ship"
          ],
          "ActionDistName": [
            "ship"
          ]
        }
      ],
      "Paging": {
        "PageNum": 1,
        "PageSize": 50,
        "Total": 1,
        "PageCount": 1
      }
    },
    "RequestId": "7cf9595a-271b-4ee9-8611-c515bceb1bf0"
  }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
