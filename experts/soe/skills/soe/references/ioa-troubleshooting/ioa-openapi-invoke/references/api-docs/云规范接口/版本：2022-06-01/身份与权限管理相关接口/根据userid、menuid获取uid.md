## 1. 接口描述




根据userid、menuid获取uid，私有化调用path为：/mapi/DescribeUid

## 2. 输入参数


| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Data.N | 否 | Array of [DescribeUidReqData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeUidReqData) | <strong><font color="blue"></font></strong>要获取的账号目录参数列表，注意：为了提升接口响应数据、减少查询时间和资源消耗，接口限制了此参数长度不超过5000组，超过5000组接口会返回参数错误 |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Items | Array of [DescribeUidRspData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeUidRspData) | <strong><font color="blue"></font></strong>获取账号列表响应的分页对象<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例











## 5. 错误码


| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InternalError.Unknown | 内部未知错误。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
