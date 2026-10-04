## 1. 接口描述

EDR响应中心查询任务详情，私有化调用path为：/capi/EDR/DescribeEDRRespondTask，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| TaskId | 否 | Integer | 任务ID |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEDRRespondTaskData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEDRRespondTaskData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEDRRespondTask
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "181af615-067c-486a-8f48-a1994891b207",
    "Data": {
      "Task": {
        "Id": 132612,
        "RespondRuleName": "test",
        "Action": "scan_kill_virus",
        "EventId": 0,
        "EventName": "",
        "IncidentId": 0,
        "IncidentName": "",
        "DoneTime": 1765369660,
        "CreateBy": "700001380679",
        "TaskSeq": 209652,
        "Ostype": 0,
        "Type": 0,
        "Status": 3,
        "DomainInstanceId": 1,
        "Description": "from rule(71094): 可疑的进程父进程",
        "CreateTime": 1765369658,
        "ActionDistName": [
          "ship"
        ],
        "RespondRuleId": 1087,
        "ScopeObjName": [
          "ship"
        ],
        "RecordTotal": 1,
        "RecordDoneTotal": 0
      },
      "ActionItems": [
        {
          "Id": 133481,
          "DistMd5": "",
          "DistPid": 0,
          "TaskId": 132612,
          "DistExtra": "{\"subid\":11,\"data\":{\"ScanType\":1,\"Details\":{\"FixType\":1,\"isTrustMacroAndInfectClean\":0,\"ScanVirusType\":0,\"subid\":11}}}",
          "RespondFileUrl": "",
          "RespondFileMd5": "",
          "IsRoot": false,
          "ScriptParameter": "",
          "DistNetworkPort": "",
          "DisposalAction": "scan_kill_virus",
          "DistType": "Term",
          "DistValue": "ship",
          "DistName": ""
        }
      ]
    }
  }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
