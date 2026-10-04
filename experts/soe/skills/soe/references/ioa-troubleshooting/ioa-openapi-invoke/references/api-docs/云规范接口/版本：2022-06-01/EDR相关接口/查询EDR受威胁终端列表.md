## 1. 接口描述

查询EDR受威胁终端列表，支持分页和参数筛选，私有化调用path为：/capi/EDR/ListThreatenedTerminals，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 滤条件、分页参数<br/><li>TerminalGroupId - int - 是否必填：否 - 操作符: eq  - 排序支持：否- 按终端组过滤。</li><li>LastEventTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按最后告警时间过滤。</li><li>Mid - string - 是否必填：否 - 操作符: eq  - 排序支持：否 - 按终端Mid过滤。</li><li>OccurTime - string - 是否必填：否 - 操作符: egt,gt,elt,lt - 排序支持：否 - 按告警发生时间过滤。</li><li>RiskLevel - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按风险等级过滤。</li><li>RiskTags - array - 是否必填：否 - 操作符: array_any - 排序支持：否 - 按风险标签过滤。</li><li>TerminalStatus - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按终端状态过滤。</li><li>AttackResult - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按终端攻击结果过滤。</li><li>EventName - string - 是否必填：否 - 操作符: eq,like - 排序支持：否 - 按告警名称过滤。</li><li>SrcIp - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源IP过滤。</li><li>DistIp - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标IP过滤。</li><li>SrcFileName - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源文件名过滤。</li><li>SrcFileMd5 - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源文件MD5过滤。</li><li>DistFileName - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标文件名过滤。</li><li>DistFileMd5 - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标文件MD5过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [ListThreatenedTerminalsData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ListThreatenedTerminalsData) | 响应数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ListThreatenedTerminals
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "9c2b06a7-ad0e-4cb1-ac58-bde580be28ff",
    "Data": {
      "Paging": {
        "PageSize": 50,
        "PageNum": 1,
        "PageCount": 1,
        "Total": 2
      },
      "Items": [
        {
          "Id": 128366,
          "AttackTech": [
            {
              "Description": "",
              "Name": "命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "TechType": "Tactic",
              "Key": "TA0011"
            }
          ],
          "UpdateTime": 1763351585,
          "UpdateBy": "",
          "TerminalName": "cugnansu-NB1",
          "RiskTags": null,
          "IOAAccount": "",
          "PendingEventCount": 0,
          "EventCount": 2,
          "OnlineStatus": 1,
          "TerminalStatus": 0,
          "AttackResult": 0,
          "Mid": "19C354965851573BED9B6EE31FCB764C670C9228",
          "Ostype": 0
        },
        {
          "Id": 1379918,
          "AttackTech": [
            {
              "Description": "",
              "Name": "命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "TechType": "Tactic",
              "Key": "TA0011"
            },
            {
              "Description": "",
              "Name": "中间人：ARP 缓存中毒",
              "Url": "https://attack.mitre.org/techniques/T1557/002",
              "Tag": "",
              "TechType": "Technique",
              "Key": "T1557.002"
            },
            {
              "Description": "",
              "Name": "收集",
              "Url": "https://attack.mitre.org/tactics/TA0009",
              "Tag": "",
              "TechType": "Tactic",
              "Key": "TA0009"
            },
            {
              "Description": "",
              "Name": "中间人",
              "Url": "https://attack.mitre.org/techniques/T1557",
              "Tag": "",
              "TechType": "Technique",
              "Key": "T1557"
            }
          ],
          "UpdateTime": 1763350807,
          "UpdateBy": "",
          "TerminalName": "DESKTOP-3D3F1JR",
          "RiskTags": null,
          "IOAAccount": "",
          "PendingEventCount": 1,
          "EventCount": 11,
          "OnlineStatus": 1,
          "TerminalStatus": 0,
          "AttackResult": 0,
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "Ostype": 0
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
