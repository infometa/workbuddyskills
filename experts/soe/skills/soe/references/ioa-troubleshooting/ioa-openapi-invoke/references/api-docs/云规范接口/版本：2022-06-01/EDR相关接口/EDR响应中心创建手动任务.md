## 1. 接口描述

EDR响应中心创建手动任务，私有化调用path为：/capi/EDR/CreateEDRRespondTask，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| DisposalAction | 否 | String | 任务动作 |
| Ostype | 否 | Integer | 系统平台(只支持32位) |
| Description | 否 | String | 任务描述 |
| ActionItems.N | 否 | Array of [EDRRespondTaskActionInfo](/开放API/云规范接口/版本：2022-06-01/数据结构.md#EDRRespondTaskActionInfo) | 动作子项 |
| IncludeScopes.N | 否 | Array of [EDRRespondTaskScopeInfo](/开放API/云规范接口/版本：2022-06-01/数据结构.md#EDRRespondTaskScopeInfo) | 执行范围 |
| ExcludeScopes.N | 否 | Array of [EDRRespondTaskScopeInfo](/开放API/云规范接口/版本：2022-06-01/数据结构.md#EDRRespondTaskScopeInfo) | 例外范围 |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeEDRRespondTaskData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeEDRRespondTaskData) | 任务详情数据 |
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: CreateEDRRespondTask
<公共请求参数>

{
    "DisposalAction": "delete_file",
    "Ostype": 0,
    "ActionItems": [
        {
            "DisposalAction": "delete_file",
            "DistType": "File",
            "DistName": "test1.exe",
            "DistValue": "C:\\hello\\test1.exe"
        }
    ],
    "IncludeScopes": [
        {
            "ForAll": true
        }
    ]
}
```

#### 输出示例

```json
{
    "Response": {
        "RequestId": "6bdde92f-09d5-4216-9117-d8a52e740cd7"
    }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
