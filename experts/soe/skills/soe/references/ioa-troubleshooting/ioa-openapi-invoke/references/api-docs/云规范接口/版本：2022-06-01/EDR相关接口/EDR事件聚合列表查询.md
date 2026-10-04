## 1. 接口描述

EDR事件聚合列表查询，私有化调用path为：/capi/EDR/ListEDRIncidents，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 滤条件、分页参数<br/><li>LastTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按时间过滤。</li><li>RiskLevel - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按风险等级过滤。</li><li>SurveyStatus - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按调查状态过滤。</li><li>JudgStatus - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按研判状态过滤。</li><li>AttckTech - array - 是否必填：否 - 操作符: array_any - 排序支持：否 - 按ATTCK过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [ListEDRIncidentsData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ListEDRIncidentsData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ListEDRIncidents
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
          "Ostype": [
            0
          ],
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "JudgeLevel": 0,
          "RiskLevel": 3,
          "SurveyStatus": 1,
          "JudgStatus": 0,
          "AttckTech": [
            {
              "Key": "TA0009",
              "Tag": "",
              "Description": "",
              "Name": "TA0009 收集",
              "TechType": "Tactic",
              "Url": "https://attack.mitre.org/tactics/TA0009"
            },
            {
              "Key": "TA0011",
              "Tag": "",
              "Description": "",
              "Name": "TA0011 命令与控制",
              "TechType": "Tactic",
              "Url": "https://attack.mitre.org/tactics/TA0011"
            }
          ],
          "LastTime": 1763351564,
          "UpdateTime": 1763364281,
          "IncidentNature": 1,
          "AttckSubTech": [
            {
              "Key": "T1557.002",
              "Tag": "",
              "Description": "",
              "Name": "T1557.002 中间人：ARP 缓存中毒",
              "TechType": "Technique",
              "Url": "https://attack.mitre.org/techniques/T1557/002"
            },
            {
              "Key": "T1557",
              "Tag": "",
              "Description": "",
              "Name": "T1557 中间人",
              "TechType": "Technique",
              "Url": "https://attack.mitre.org/techniques/T1557"
            }
          ],
          "RiskTags": null,
          "CreateBy": "",
          "Id": 26866,
          "CreateTime": 1763350085,
          "FirstTime": 1763349996,
          "EventTotal": 13,
          "TerminalTotal": 2,
          "UserTotal": 0,
          "EvidenceTotal": 18,
          "IsActive": true,
          "UpdateBy": "700001380679",
          "EventPendingTotal": 1,
          "EvidencePendingTotal": 0
        }
      ],
      "Paging": {
        "PageNum": 1,
        "PageSize": 50,
        "Total": 1,
        "PageCount": 1
      }
    },
    "RequestId": "cbff4100-0867-4c20-aa85-561af6988dd5"
  }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
