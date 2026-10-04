## 1. 接口描述

EDR响应中心查询任务动作统计，私有化调用path为：/capi/EDR/DescribeEDRRespondTaskActionStatistics，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 过滤条件、分页参数<br/><li>CreateTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按发生时间过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | Array of [ReportGeneralCountItem](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ReportGeneralCountItem) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEDRRespondTaskActionStatistics
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "538af04e-84dd-4f99-ac88-5994bb1f0e64",
    "Data": [
      {
        "Total": 1,
        "Key": "auto_file_isolate",
        "Text": "自动隔离文件"
      },
      {
        "Total": 8,
        "Key": "cancel_isolate",
        "Text": "取消隔离"
      },
      {
        "Total": 1,
        "Key": "cancel_isolate_block",
        "Text": "恢复网络连接"
      },
      {
        "Total": 1275,
        "Key": "collect_file",
        "Text": "捕获文件"
      },
      {
        "Total": 236,
        "Key": "complete_delete_file",
        "Text": "删除文件"
      },
      {
        "Total": 7,
        "Key": "delete_file",
        "Text": "隔离文件"
      },
      {
        "Total": 90,
        "Key": "delete_file&kill_proc",
        "Text": "终止进程并删除文件"
      },
      {
        "Total": 1531,
        "Key": "exec_script",
        "Text": "执行脚本"
      },
      {
        "Total": 24,
        "Key": "fix_vul",
        "Text": "漏洞修复"
      },
      {
        "Total": 19,
        "Key": "isolate",
        "Text": "隔离"
      },
      {
        "Total": 342,
        "Key": "isolate_block",
        "Text": "阻断网络连接"
      },
      {
        "Total": 2,
        "Key": "recover_file",
        "Text": "恢复文件"
      },
      {
        "Total": 1710,
        "Key": "scan_kill_virus",
        "Text": "病毒查杀"
      }
    ]
  }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
