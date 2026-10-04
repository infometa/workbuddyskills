## 1. 接口描述

EDR响应中心查询任务执行记录状态统计，私有化调用path为：/capi/EDR/DescribeEDRRespondTaskRecordStatusStatistics，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| TaskId | 否 | Integer | 任务ID（与TaskSeq参数二选一） |
| TaskSeq.N | 否 | Array of Integer | 任务中心序号（与TaskId参数二选一） |

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
X-TC-Action: DescribeEDRRespondTaskRecordStatusStatistics
<公共请求参数>

{
    "TaskId": 1
}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "ef8389c3-7a49-4d3f-9b05-5e68a96b207f",
    "Data": [
      {
        "Total": 1,
        "Text": "",
        "Key": "3"
      },
      {
        "Total": 1,
        "Text": "",
        "Key": "4"
      },
      {
        "Total": 31,
        "Text": "",
        "Key": "5"
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
