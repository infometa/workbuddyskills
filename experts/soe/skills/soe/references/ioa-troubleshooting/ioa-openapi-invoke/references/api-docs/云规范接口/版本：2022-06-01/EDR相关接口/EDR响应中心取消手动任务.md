## 1. 接口描述

EDR响应中心取消手动任务，私有化调用path为：/capi/EDR/ModifyCancelEDRRespondTask，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| TaskId | 否 | Integer | 任务ID |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ModifyCancelEDRRespondTask
<公共请求参数>

{
    "DomainInstanceId": "1",
    "TaskId": 1
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
