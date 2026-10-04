## 1. 接口描述

EDR响应中心查询任务状态统计，私有化调用path为：/capi/EDR/DescribeEDRRespondTaskStatusStatistics，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 过滤条件、分页参数<br/><li>CreateTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按发生时间过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEDRRespondTaskStatusStatisticsData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEDRRespondTaskStatusStatisticsData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEDRRespondTaskStatusStatistics
<公共请求参数>

{}
```

#### 输出示例

```json
{
  "Response": {
    "RequestId": "c4a22248-7d5a-4ac4-a5a2-a9affe5d8ea3",
    "Data": {
      "AllItems": [
        {
          "Total": 5100,
          "Key": "0",
          "Text": "自动响应"
        },
        {
          "Total": 146,
          "Key": "1",
          "Text": "人工响应"
        }
      ],
      "RunningItems": [
        {
          "Total": 3,
          "Key": "0",
          "Text": "自动响应"
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
