## 1. 接口描述

根据操作系统类型，返回租户的顶级终端分组，私有化调用path为：/capi/Assets/Device/DescribeRootGroupId，适用于私有化8.0以后的版本。

## 2. 输入参数


| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| OsType | 否 | Integer | 系统类型（0: win，1：linux，2: mac，4：android，5：ios ）<br/>示例值：0 |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeGroupIdsRspData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeGroupIdsRspData) | 根分组数据|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例1 示例1

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeRootGroupId
<公共请求参数>

{"OsType": 0}
```

#### 输出示例

```json
{
    "Response": {
        "RequestId": "9174ff99-833a-4c07-8f44-ae8b6d454428",
        "Data": {
            "RootGroupId": 42631
        }
    }
}
```

### 示例2 测试

测试

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeRootGroupId
<公共请求参数>

{
	"OsType": 0
}
```

#### 输出示例

```json
{
    "Response": {
        "Data": {
            "RootGroupId": 92
        },
        "RequestId": "77dea8e5-969c-486e-ae61-23b464cdbb67"
    }
}
```











## 5. 错误码


| 错误码 | 描述 |
|---------|---------|
| FailedOperation.QueryData | 查询数据失败。 |
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InternalError.Unknown | 内部未知错误。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
| MissingParameter.CommonParam | 缺少公共参数。 |
| ResourceNotFound.NotFound | 资源不存在。 |
| UnauthorizedOperation.PermissionDenied | 未授权的操作。 |
