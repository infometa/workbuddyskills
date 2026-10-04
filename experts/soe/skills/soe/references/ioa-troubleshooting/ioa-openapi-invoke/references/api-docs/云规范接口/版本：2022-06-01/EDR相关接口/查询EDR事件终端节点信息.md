## 1. 接口描述

查询EDR事件终端节点信息，私有化调用path为：/capi/EDR/DescribeEventAttackGraphTermNode，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| EventId | 否 | Integer | 事件ID |
| NodeId | 否 | Integer | 节点ID（优先） |
| TerminalId | 否 | Integer | 终端ID（可选） |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEventAttackGraphTermNodeData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEventAttackGraphTermNodeData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEventAttackGraphTermNode
<公共请求参数>

{
	"EventId": 1,
	"NodeId": 1
}
```

#### 输出示例

```json
{
    "Response": {
        "Data": {
            "Node": {
                "DisposalStatus": 0,
                "Id": 1,
                "IocContent": null,
                "LogContent": [
                    {
                        "GroupTag": "进程信息",
                        "InputType": "input",
                        "Key": "ProcPid",
                        "Name": "进程Pid",
                        "Text": "1972",
                        "Value": "1972",
                        "ValueType": "int"
                    },
                    {
                        "GroupTag": "进程信息",
                        "InputType": "input",
                        "Key": "ProcCmdline",
                        "Name": "进程命令行",
                        "Text": "C:\\WINDOWS\\system32\\svchost.exe -k netsvcs -p -s Schedule",
                        "Value": "C:\\WINDOWS\\system32\\svchost.exe -k netsvcs -p -s Schedule",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "input",
                        "Key": "FileName",
                        "Name": "文件名",
                        "Text": "svchost.exe",
                        "Value": "svchost.exe",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "input",
                        "Key": "FilePath",
                        "Name": "文件路径",
                        "Text": "C:\\WINDOWS\\system32\\svchost.exe",
                        "Value": "C:\\WINDOWS\\system32\\svchost.exe",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "input",
                        "Key": "FileMd5",
                        "Name": "文件md5",
                        "Text": "b7f884c1b74a263f746ee12a5f7c9f6a",
                        "Value": "b7f884c1b74a263f746ee12a5f7c9f6a",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "鉴定信息",
                        "InputType": "select",
                        "Key": "CloudAttr",
                        "Name": "云查属性",
                        "Text": "安全(White)",
                        "Value": "White",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "input",
                        "Key": "FileSign",
                        "Name": "文件签名",
                        "Text": "Microsoft Windows Publisher",
                        "Value": "Microsoft Windows Publisher",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "select",
                        "Key": "FileSignStatus",
                        "Name": "文件签名状态",
                        "Text": "验证通过",
                        "Value": "Valid",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "鉴定信息",
                        "InputType": "select",
                        "Key": "FileSignWhite",
                        "Name": "是否白签名",
                        "Text": "是",
                        "Value": "1",
                        "ValueType": "int"
                    },
                    {
                        "GroupTag": "",
                        "InputType": "select",
                        "Key": "Type",
                        "Name": "节点类型",
                        "Text": "进程",
                        "Value": "Proc",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "进程信息",
                        "InputType": "input",
                        "Key": "ThreadId",
                        "Name": "线程ID",
                        "Text": "10524",
                        "Value": "10524",
                        "ValueType": "int"
                    },
                    {
                        "GroupTag": "进程信息",
                        "InputType": "input",
                        "Key": "ProcGuid",
                        "Name": "进程唯一ID",
                        "Text": "13851412440389519284",
                        "Value": "13851412440389519284",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "鉴定信息",
                        "InputType": "select",
                        "Key": "ProcTrust",
                        "Name": "进程可信",
                        "Text": "可信",
                        "Value": "Trust",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "select",
                        "Key": "FileFormat",
                        "Name": "文件类型",
                        "Text": "可执行EXE",
                        "Value": "EXE",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "文件信息",
                        "InputType": "select",
                        "Key": "FileMd5Type",
                        "Name": "文件md5类型",
                        "Text": "全文",
                        "Value": "FullMd5",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "鉴定信息",
                        "InputType": "select",
                        "Key": "FileTags",
                        "Name": "文件标签",
                        "Text": "",
                        "Value": "",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "鉴定信息",
                        "InputType": "select",
                        "Key": "ScanAttr",
                        "Name": "威胁鉴定",
                        "Text": "安全",
                        "Value": "White",
                        "ValueType": "string"
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "NodeId",
                        "Name": "NodeId",
                        "Text": "c:\\windows\\system32\\svchost.exe_13851412440389519284",
                        "Value": "c:\\windows\\system32\\svchost.exe_13851412440389519284",
                        "ValueType": ""
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "NodeName",
                        "Name": "NodeName",
                        "Text": "svchost.exe(1972)",
                        "Value": "svchost.exe(1972)",
                        "ValueType": ""
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "TraceColorRule",
                        "Name": "TraceColorRule",
                        "Text": "白进程创建红色节点",
                        "Value": "白进程创建红色节点",
                        "ValueType": ""
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "NodeMergeId",
                        "Name": "NodeMergeId",
                        "Text": "c:\\windows\\system32\\svchost.exe_b7f884c1b74a263f746ee12a5f7c9f6a",
                        "Value": "c:\\windows\\system32\\svchost.exe_b7f884c1b74a263f746ee12a5f7c9f6a",
                        "ValueType": ""
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "NodeEvidence",
                        "Name": "NodeEvidence",
                        "Text": "true",
                        "Value": "true",
                        "ValueType": ""
                    },
                    {
                        "GroupTag": "",
                        "InputType": "",
                        "Key": "TraceColor",
                        "Name": "TraceColor",
                        "Text": "Yellow",
                        "Value": "Yellow",
                        "ValueType": ""
                    }
                ],
                "Name": "svchost.exe(1972)",
                "NodeTagDesc": null,
                "NodeTags": "",
                "OccurTime": 0,
                "RiskLevel": 1,
                "Type": "Proc"
            },
            "Terminal": null
        },
        "RequestId": "e15d4131-6800-4cdf-a672-78943b858176"
    }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
