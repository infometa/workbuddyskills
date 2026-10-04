## 1. 接口描述

查询EDR事件列表，支持分页和按参数筛选，私有化调用path为：/capi/EDR/ListEvents，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 滤条件、分页参数<br/><li>OccurTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按告警发生时间过滤。</li><li>RiskLevel - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按风险等级过滤。</li><li>RiskTags - array - 是否必填：否 - 操作符: array_any - 排序支持：否 - 按风险标签过滤。</li><li>DisposalStatus - int - 是否必填：否 - 操作符: eq - 排序支持：否 - 按处置状态过滤。</li><li>ActionName - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按事件动作过滤。</li><li>EventName - string - 是否必填：否 - 操作符: eq,like - 排序支持：否 - 按告警名称过滤。</li><li>SrcIp - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源IP过滤。</li><li>DistIp - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标IP过滤。</li><li>SrcFileName - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源文件名过滤。</li><li>SrcFileMd5 - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按源文件MD5过滤。</li><li>DistFileName - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标文件名过滤。</li><li>DistFileMd5 - string - 是否必填：否 - 操作符: eq - 排序支持：否 - 按目标文件MD5过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [ListEventsData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ListEventsData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ListEvents
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "170fa1b3-53cc-47c9-8201-a5b4fe2b11ca",
    "Data": {
      "Paging": {
        "PageSize": 50,
        "PageNum": 1,
        "PageCount": 1,
        "Total": 13
      },
      "Items": [
        {
          "Id": 567890,
          "ParentDesc": "vmnat.exe(7224)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763351564,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "19C354965851573BED9B6EE31FCB764C670C9228",
          "FirstOccurTime": 1763349997,
          "DuplicateTimes": 3,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 128366,
          "RiskLevel": 3,
          "TerminalGroupId": 85160,
          "TerminalName": "cugnansu-NB1",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "vmnat.exe(7224) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763351585,
          "IsSys": 1,
          "SrcFileName": "vmnat.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567891,
          "ParentDesc": "cmd.exe(6504)",
          "RiskTags": [],
          "ChildDesc": "ARP.EXE(5196)",
          "ActionTypeDesc": "进程",
          "OccurTime": 1763350736,
          "ActionNameDesc": "进程创建",
          "ActionType": "Proc",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763349996,
          "DuplicateTimes": 3,
          "IncidentOstype": [
            0
          ],
          "EventName": "ARP命令执行",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 1,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "cmd.exe(6504) ProcessCreate ARP.EXE(5196)",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 0,
          "DisposalResult": "",
          "IncidentId": 26866,
          "RuleId": 71384,
          "RuleName": "ARP命令执行",
          "EngineName": "GraphEngine",
          "RuleScore": 0,
          "AlertDescription": "1、检测到ARP命令执行，攻击者常利用此方式收集终端信息。",
          "ActionName": "ProcessCreate",
          "UpdateTime": 1763350745,
          "IsSys": 1,
          "SrcFileName": "cmd.exe",
          "ViciousNode": "",
          "DistType": "Proc",
          "SrcType": "Proc",
          "DistFileName": "ARP.EXE",
          "AttackTech": [
            {
              "TechType": "Technique",
              "Name": "T1557.002 中间人：ARP 缓存中毒",
              "Url": "https://attack.mitre.org/techniques/T1557/002",
              "Tag": "",
              "Description": "",
              "Key": "T1557.002"
            },
            {
              "TechType": "Tactic",
              "Name": "TA0009 收集",
              "Url": "https://attack.mitre.org/tactics/TA0009",
              "Tag": "",
              "Description": "",
              "Key": "TA0009"
            },
            {
              "TechType": "Technique",
              "Name": "T1557 中间人",
              "Url": "https://attack.mitre.org/techniques/T1557",
              "Tag": "",
              "Description": "",
              "Key": "T1557"
            }
          ]
        },
        {
          "Id": 567901,
          "ParentDesc": "query1.exe(4036)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350711,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350711,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "query1.exe(4036) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350807,
          "IsSys": 1,
          "SrcFileName": "query1.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567894,
          "ParentDesc": "query.exe(10312)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350466,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350023,
          "DuplicateTimes": 4,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "query.exe(10312) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350505,
          "IsSys": 1,
          "SrcFileName": "query.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567899,
          "ParentDesc": "deny.exe(2276)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350425,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350425,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(2276) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350506,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567900,
          "ParentDesc": "deny.exe(2276)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350425,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350425,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(2276) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350506,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567898,
          "ParentDesc": "deny.exe(2276)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350416,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350416,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(2276) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350506,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567897,
          "ParentDesc": "deny.exe(2276)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350416,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350416,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(2276) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350506,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567895,
          "ParentDesc": "deny.exe(3832)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350288,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350288,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(3832) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350386,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567896,
          "ParentDesc": "deny.exe(3832)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350288,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350288,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "deny.exe(3832) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350386,
          "IsSys": 1,
          "SrcFileName": "deny.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567892,
          "ParentDesc": "query.exe(10312)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350023,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350023,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "query.exe(10312) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350078,
          "IsSys": 1,
          "SrcFileName": "query.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567893,
          "ParentDesc": "query.exe(10312)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763350023,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "6F104B7668515D1B1FCCAB9806BF92DF691A95B6",
          "FirstOccurTime": 1763350023,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 1379918,
          "RiskLevel": 3,
          "TerminalGroupId": 71832,
          "TerminalName": "DESKTOP-3D3F1JR",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "query.exe(10312) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350078,
          "IsSys": 1,
          "SrcFileName": "query.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
        },
        {
          "Id": 567889,
          "ParentDesc": "vmnat.exe(7224)",
          "RiskTags": [],
          "ChildDesc": "23.133.4.25:27978",
          "ActionTypeDesc": "网络",
          "OccurTime": 1763349997,
          "ActionNameDesc": "Socket请求",
          "ActionType": "Network",
          "Mid": "19C354965851573BED9B6EE31FCB764C670C9228",
          "FirstOccurTime": 1763349997,
          "DuplicateTimes": 1,
          "IncidentOstype": [
            0
          ],
          "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
          "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
          "TerminalId": 128366,
          "RiskLevel": 3,
          "TerminalGroupId": 85160,
          "TerminalName": "cugnansu-NB1",
          "Ostype": 0,
          "TerminalOnlineStatus": 1,
          "AccountId": 0,
          "IOAAccount": "",
          "AttackSummary": "vmnat.exe(7224) SocketRequest 23.133.4.25:27978",
          "UpdateBy": "",
          "AttackResult": 0,
          "TerminalStatus": 0,
          "DisposalStatus": 5,
          "DisposalResult": "Success",
          "IncidentId": 26866,
          "RuleId": 70198,
          "RuleName": "威胁联网自动处置",
          "EngineName": "IocEngine",
          "RuleScore": 0,
          "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
          "ActionName": "SocketRequest",
          "UpdateTime": 1763350074,
          "IsSys": 1,
          "SrcFileName": "vmnat.exe",
          "ViciousNode": "Parent,Child",
          "DistType": "Network",
          "SrcType": "Proc",
          "DistFileName": "",
          "AttackTech": [
            {
              "TechType": "Tactic",
              "Name": "TA0011 命令与控制",
              "Url": "https://attack.mitre.org/tactics/TA0011",
              "Tag": "",
              "Description": "",
              "Key": "TA0011"
            }
          ]
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
