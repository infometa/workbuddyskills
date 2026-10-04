## 1. 接口描述

EDR响应中心查询任务趋势统计，私有化调用path为：/capi/EDR/DescribeEDRRespondTaskTrending，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 过滤条件、分页参数<br/><li>CreateTime - string - 是否必填：是 - 操作符: egt,gt,elt,lt - 排序支持：是 - 按发生时间过滤。</li> |
| TimeUnit | 否 | String | 统计时间单位（hour.小时 day.天） |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | Array of [ReportGeneralTimeCountItem](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ReportGeneralTimeCountItem) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeEDRRespondTaskTrending
<公共请求参数>

{}
```

#### 输出示例

```json
{
    "Response": {
        "Data": [
            {
                "TimeFmt": "YYYY-MM-DD",
                "TimePoint": "2024-05-14",
                "Values": [
                    {
                        "Key": "1",
                        "Text": "人工响应",
                        "Total": 1
                    }
                ]
            },
            {
                "TimeFmt": "YYYY-MM-DD",
                "TimePoint": "2024-05-15",
                "Values": [
                    {
                        "Key": "1",
                        "Text": "人工响应",
                        "Total": 1
                    }
                ]
            },
            {
                "TimeFmt": "YYYY-MM-DD",
                "TimePoint": "2024-05-16",
                "Values": [
                    {
                        "Key": "1",
                        "Text": "人工响应",
                        "Total": 1
                    }
                ]
            },
            {
                "TimeFmt": "YYYY-MM-DD",
                "TimePoint": "2024-05-30",
                "Values": [
                    {
                        "Key": "1",
                        "Text": "人工响应",
                        "Total": 1
                    }
                ]
            }
        ],
        "RequestId": "cd3f1ec5-d051-4c38-a445-eade2c436090"
    }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
