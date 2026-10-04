## 1. 接口描述

EDR获取证据列表，私有化调用path为：/capi/EDR/DescribeEvidences，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 滤条件、分页参数<br/><li>IncidentId - int - 是否必填：否 - 操作符: eq - 排序支持：是 - 按事件ID过滤。</li><li>EventId - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按告警ID过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEvidenceData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEvidenceData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEvidences
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
                    "AccountIds": null,
                    "Accounts": [],
                    "CommandLine": "",
                    "DisposalAction": "ignore",
                    "DisposalStatus": 4,
                    "EntityName": "net.exe",
                    "EntityType": "File",
                    "EventNames": [
                        "任意进程告警测试caenxiao"
                    ],
                    "EvidenceId": 12867,
                    "FileMd5": "31890a7de89936f922d44d677f681a7f",
                    "FilePath": "C:\\Windows\\SysWOW64\\net.exe",
                    "FileType": "可执行EXE",
                    "FirstTime": "1716522634",
                    "GraphNodeId": 16028,
                    "HandleDisposalAction": "ignore",
                    "IocContent": "",
                    "IsIocEngine": false,
                    "NodeTag": "",
                    "NodeTagDesc": null,
                    "OccurTime": "1716522634",
                    "RiskLevel": 1,
                    "TerminalIds": [
                        0
                    ],
                    "TerminalNames": []
                }
            ],
            "Page": {
                "PageCount": 1,
                "PageNum": 1,
                "PageSize": 50,
                "Total": 1
            }
        },
        "RequestId": "64a9785f-98e5-45d1-9955-3f67d061f5ca"
    }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
