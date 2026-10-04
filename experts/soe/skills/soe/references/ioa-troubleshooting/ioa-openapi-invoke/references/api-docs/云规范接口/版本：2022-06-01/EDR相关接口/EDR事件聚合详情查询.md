## 1. 接口描述

EDR事件聚合详情查询，私有化调用path为：/capi/EDR/DescribeEDRIncident，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Id | 否 | Integer | 主键ID |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEDRIncidentData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEDRIncidentData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEDRIncident
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "93dba44b-9dae-4f45-bb8a-12f249529a63",
    "Data": {
      "CommentTotal": 0,
      "JudgData": null,
      "IncidentInfo": {
        "Id": 26866,
        "CreateBy": "",
        "UpdateBy": "700001380679",
        "EventPendingTotal": 1,
        "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
        "Ostype": [
          0
        ],
        "RiskLevel": 3,
        "SurveyStatus": 1,
        "JudgStatus": 0,
        "IsActive": true,
        "JudgeLevel": 0,
        "AttckSubTech": [
          {
            "Description": "",
            "Name": "T1557.002 中间人：ARP 缓存中毒",
            "Url": "https://attack.mitre.org/techniques/T1557/002",
            "Tag": "",
            "TechType": "Technique",
            "Key": "T1557.002"
          },
          {
            "Description": "",
            "Name": "T1557 中间人",
            "Url": "https://attack.mitre.org/techniques/T1557",
            "Tag": "",
            "TechType": "Technique",
            "Key": "T1557"
          }
        ],
        "IncidentNature": 1,
        "RiskTags": null,
        "EvidencePendingTotal": 0,
        "CreateTime": 1763350085,
        "UpdateTime": 1763364281,
        "AttckTech": [
          {
            "Description": "",
            "Name": "TA0009 收集",
            "Url": "https://attack.mitre.org/tactics/TA0009",
            "Tag": "",
            "TechType": "Tactic",
            "Key": "TA0009"
          },
          {
            "Description": "",
            "Name": "TA0011 命令与控制",
            "Url": "https://attack.mitre.org/tactics/TA0011",
            "Tag": "",
            "TechType": "Tactic",
            "Key": "TA0011"
          }
        ],
        "EvidenceTotal": 18,
        "FirstTime": 1763349996,
        "LastTime": 1763351564,
        "EventTotal": 13,
        "TerminalTotal": 2,
        "UserTotal": 0
      }
    }
  }
}
```

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
