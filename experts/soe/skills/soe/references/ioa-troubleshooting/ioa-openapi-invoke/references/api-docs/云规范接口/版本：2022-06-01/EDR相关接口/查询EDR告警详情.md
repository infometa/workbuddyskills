## 1. 接口描述

查询EDR事件详情，需要传入ID，私有化调用path为：/capi/EDR/DescribeEvent，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| EventId | 否 | Integer | 事件ID |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEventData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEventData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEvent
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "df0806a4-3935-44be-93e9-b5397b947835",
    "Data": {
      "User": null,
      "Evidence": null,
      "Incident": {
        "Id": 26866,
        "SurveyStatus": 1,
        "JudgStatus": 0,
        "FirstTime": 1763349996,
        "LastTime": 1763351564,
        "EventTotal": 13,
        "TerminalTotal": 2,
        "UserTotal": 0,
        "EvidenceTotal": 18,
        "Ostype": [
          0
        ],
        "RiskLevel": 3,
        "Uuid": "f79580b6-c8da-4095-9517-fafc7f2c0aab",
        "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击"
      },
      "LogContent": "{\"@collection\":\"2025-11-17T11:26:37.76+08:00\",\"@table\":\"NetworkEvents\",\"@timestamp\":\"2025-11-17T11:26:41.798345184+08:00\",\"Action\":{\"EdgeShowName\":\"vmnat.exe(7224)_SocketRequest_23.133.4.25:27978\",\"EdgeType\":\"Report\",\"EventId\":398086,\"EventMode\":\"ModeAsync\",\"EventUUId\":\"f54c180e-f515-4097-bc45-2840d5e287d9\",\"Name\":\"SocketRequest\",\"NodeId\":\"c:\\\\windows\\\\syswow64\\\\vmnat.exe_3708630519874067512_socketrequest_tcp_23.133.4.25_27978\",\"NodeMergeId\":\"c:\\\\windows\\\\syswow64\\\\vmnat.exe_6ee023f00cd791995a88ec3fac5c7dee_socketrequest_tcp_23.133.4.25_27978\",\"NodeName\":\"SocketRequest\",\"StoreAlert\":{\"AlertSource\":\"HIPS\",\"BlockType\":\"Deny\",\"CloudEngineName\":\"Unknown\",\"CloudRuleId\":0,\"CloudTitle\":\"已检测到进程连接可疑网络\",\"EngineName\":\"IocEngine\",\"ExplainTags\":\"Winos4.0恶意软件\",\"FixResult\":\"Success\",\"IOCInfo\":\"\"}\"},\"Child\":{\"Direct\":1,\"DstIp\":\"23.133.4.25\",\"DstPort\":27978,\"Host\":\"\",\"IpIoc\":\"BLACK\",\"NodeEvidence\":true,\"NodeId\":\"tcp_23.133.4.25_27978\",\"NodeMergeId\":\"tcp_23.133.4.25_27978\",\"NodeName\":\"23.133.4.25:27978\",\"Protocol\":\"tcp\",\"SessionId\":5,\"SrcIp\":\"192.168.255.10\",\"SrcPort\":59868,\"Type\":\"Network\"},\"Cmd\":7520,\"Common\":{\"AgentMode\":0,\"AuthId\":251272654,\"ClientVer\":\"210.10.29092.62001\",\"DeviceGroup\":\"全网终端.supp\",\"EdrSdkVer\":\"'210.10.29092.62001'\",\"EventId\":398086,\"EventTime\":1763349997760,\"EventUUId\":\"f54c180e-f515-4097-bc45-2840d5e287d9\",\"Guid\":\"19C354965851573BED9B6EE31FCB764C\",\"LoginStatus\":2,\"Mid\":\"19C354965851573BED9B6EE31FCB764C670C9228\",\"MonitorGroupId\":40305,\"MonitorId\":60006,\"ReportId\":3756,\"SessionId\":5,\"Source\":\"KernelMon\",\"Uid\":0,\"UserName\":\"\"},\"DomainId\":862,\"Environment\":{\"DomainName\":\"TENCENT\",\"ExportIp\":\"113.108.77.61\",\"HostName\":\"cugnansu-NB1\",\"MacAddr\":\"F0:B6:1E:57:1A:66\",\"OsBit\":\"64\",\"OsBuild\":19045,\"OsProduectDesc\":\"Windows 10 Enterprise 22H2\",\"OsType\":\"Windows\",\"OsUserName\":\"cugnansu\",\"OsVersion\":\"Win10\",\"SysStartTimes\":1763344847500},\"OS\":0,\"PParent\":{\"CloudAttr\":\"White\",\"FileMd5\":\"852ee5587d6cb0b8b17e981fe84a31d4\",\"FileMd5Type\":\"FullMd5\",\"FilePath\":\"C:\\\\WINDOWS\\\\system32\\\\services.exe\",\"FileSign\":\"Microsoft Windows Publisher\",\"FileSignStatus\":\"Valid\",\"FileSignWhite\":1,\"FileSourceUrl\":\"\",\"FileTags\":\"\",\"ProcCmdline\":\"C:\\\\WINDOWS\\\\system32\\\\services.exe\",\"ProcGuid\":\"3529058023100384324\",\"ProcPid\":1092},\"Parent\":{\"CloudAttr\":\"Unknown\",\"FileAccessTime\":1693221165,\"FileCompany\":\"VMware, Inc.\",\"FileCopyright\":\"Copyright © 1998-2022 VMware, Inc.\",\"FileCreateTime\":1763016161,\"FileDesc\":\"VMware NAT Service\",\"FileDriverType\":\"Fixed\",\"FileFormat\":\"EXE\",\"FileIssuer\":\"DigiCert Assured ID Code Signing CA-1\",\"FileLegalMark\":\"\",\"FileMd5\":\"6ee023f00cd791995a88ec3fac5c7dee\",\"FileMd5Type\":\"FullMd5\",\"FileModifyTime\":1668532542,\"FileName\":\"vmnat.exe\",\"FileOriginalName\":\"vmnat.exe\",\"FilePath\":\"C:\\\\Windows\\\\SysWOW64\\\\vmnat.exe\",\"FileProductName\":\"VMware Workstation\",\"FileProductVer\":\"17.0.0 build-20800274\",\"FileSha\":\"12f40ecc06613efd43f84e50f18a7b32a7776127a8c1596bc79f391de7059c7f\",\"FileShaType\":3,\"FileSign\":\"VMware, Inc.\",\"FileSignStatus\":\"Valid\",\"FileSignWhite\":1,\"FileSize\":428184,\"FileSourceUrl\":\"\",\"FileVersion\":\"17.0.0 build-20800274\",\"NodeEvidence\":true,\"NodeId\":\"c:\\\\windows\\\\syswow64\\\\vmnat.exe_3708630519874067512\",\"NodeMergeId\":\"c:\\\\windows\\\\syswow64\\\\vmnat.exe_6ee023f00cd791995a88ec3fac5c7dee\",\"NodeName\":\"vmnat.exe(7224)\",\"ProcArch\":\"x86\",\"ProcChainGuid\":\"3529058023100384324,3527041312618709668,3172493372940878532,3146994774834414188,3146994774834151428,3146994774834151424\",\"ProcChainInfo\":\"\",\"ProcChainTrust\":\"Trust\",\"ProcCmdline\":\"C:\\\\Windows\\\\SysWOW64\\\\vmnat.exe\",\"ProcCreateTime\":1763344872321,\"ProcDomainName\":\"NT AUTHORITY\"
























,\"ProcElevationType\":1,\"ProcExited\":false,\"ProcGuid\":\"3708630519874067512\",\"ProcIntegrity\":6,\"ProcPid\":7224,\"ProcTrust\":\"Trust\",\"ProcUserName\":\"SYSTEM\",\"SessionId\":5,\"TavSign\":\"\",\"TrojanName\":\"\",\"Type\":\"Proc\"},\"TenantId\":\"251272654\",\"Uuid\":\"ad3429f7d18e51fd89b6c9a5bce7407b\",\"Version\":1,\"_id\":\"FdnZj5oBPbqRdzwpuLqN\"}",
      "Rule": {
        "Id": 70198,
        "Name": "威胁联网自动处置",
        "RiskLevel": 3,
        "RiskTags": [],
        "Description": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
        "IsSys": true,
        "Score": 0,
        "AttackTech": [
          {
            "Description": "",
            "Name": "TA0011 命令与控制",
            "Url": "https://attack.mitre.org/tactics/TA0011",
            "TechType": "Tactic",
            "Tag": "",
            "Key": "TA0011"
          }
        ],
        "Nature": 1
      },
      "Info": {
        "Id": 567890,
        "RuleId": 70198,
        "RuleName": "威胁联网自动处置",
        "RuleScore": 0,
        "RiskLevel": 3,
        "AlertDescription": "终端基于威胁情报引擎，发现联网的域名或IP指向威胁情报，会自动处置拦截，并产生告警",
        "RiskTags": [],
        "SrcType": "Proc",
        "SrcFileName": "vmnat.exe",
        "ActionType": "Network",
        "DistType": "Network",
        "Mid": "19C354965851573BED9B6EE31FCB764C670C9228",
        "DistFileName": "",
        "AttackTech": [
          {
            "Description": "",
            "Name": "TA0011 命令与控制",
            "Url": "https://attack.mitre.org/tactics/TA0011",
            "TechType": "Tactic",
            "Tag": "",
            "Key": "TA0011"
          }
        ],
        "IncidentId": 26866,
        "ViciousNode": "Parent,Child",
        "ParentDesc": "vmnat.exe(7224)",
        "ChildDesc": "23.133.4.25:27978",
        "ActionTypeDesc": "网络",
        "ActionName": "SocketRequest",
        "ActionNameDesc": "Socket请求",
        "EngineName": "IocEngine",
        "IncidentName": "DESKTOP-3D3F1JR,cugnansu-NB1等2个终端 'Winos4.0恶意软件' 攻击",
        "FirstOccurTime": 1763349997,
        "DuplicateTimes": 3,
        "IsSys": 1,
        "Ostype": 0,
        "IncidentOstype": [
          0
        ],
        "EventName": "威胁联网自动处置 (Winos4.0恶意软件)",
        "TerminalId": 128366,
        "TerminalGroupId": 85160,
        "TerminalName": "cugnansu-NB1",
        "TerminalOnlineStatus": 1,
        "AccountId": 0,
        "IOAAccount": "",
        "UpdateTime": 1763351585,
        "UpdateBy": "",
        "AttackResult": 0,
        "TerminalStatus": 0,
        "DisposalStatus": 5,
        "DisposalResult": "Success",
        "AttackSummary": "vmnat.exe(7224) SocketRequest 23.133.4.25:27978",
        "OccurTime": 1763351564
      },
      "Terminal": {
        "Id": 128366,
        "TerminalName": "cugnansu-NB1",
        "GroupName": "supp",
        "IOAAccount": "",
        "OnlineStatus": 1,
        "ActiveStatus": 0,
        "Ostype": 0,
        "TerminalStatus": 0,
        "OsVersion": "10.0.19045",
        "ClassAsset": 0,
        "Mid": "19C354965851573BED9B6EE31FCB764C670C9228",
        "Os": "Microsoft Windows 10 专业版"
      }
    }
  }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
