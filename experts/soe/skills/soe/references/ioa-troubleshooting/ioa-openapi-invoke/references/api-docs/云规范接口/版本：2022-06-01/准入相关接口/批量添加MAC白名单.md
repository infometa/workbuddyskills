## 1. 接口描述




添加多个准入MAC白名单，私有化调用path为：capi/inac/CreateBatchMacWhite

## 2. 输入参数


| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| MacWhites.N | 否 | Array of [MacWhites](/开放API/云规范接口/版本：2022-06-01/数据结构.md#MacWhites) | <strong><font color="blue"></font></strong>白名单列表 |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例1 批量添加Mac白名单

批量添加Mac白名单

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: CreateBatchMacWhite
<公共请求参数>

{
  "MacWhites": [
    {
      "Mac": "AD:AD:AD:AD:AD:AD",
      "UserName": "终端用户名",
      "Remark": "备注:永久有效"
    },
    {
      "Mac": "AD:AD:AD:AD:AD:AD",
      "UserName": "终端用户名2",
      "IsValidTime": 1,
      "ValidTime": "2025-01-01 00:00:00",
      "Remark": "备注:指定有效期"
    }
  ]
}
```

#### 输出示例

```json
{
    "Response": {
        "RequestId": "3c140219-cfe9-470e-b241-907877d6fb03"
    }
}
```

### 示例2 批量添加Mac白名单--失败

批量添加Mac白名单--失败

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: CreateBatchMacWhite
<公共请求参数>

{
    "MacWhites": [
        {
            "Mac": "AD:AD:AD:AD:AD:ddDdddd",
            "UserName": "终端用户名",
            "Remark": "备注:永久有效"
        }
    ]
}
```

#### 输出示例

```json
{
    "Response": {
        "Error": {
            "Message": "无效的MAC地址。",
            "Code": "InvalidParameter.InvalidMacAddress"
        },
        "RequestId": "3c140219-cfe9-470e-b241-907877d6fb03"
    }
}
```











## 5. 错误码


| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.CantEmptyList | 交换机列表不能为空 |
| InvalidParameter.InvalidDateFormat | 日期格式无效。 |
| InvalidParameter.InvalidMacAddress | 无效的MAC地址。 |
| InvalidParameter.OutOfRangeVlan | VLAN不能大于4096 |
| InvalidParameter.RequestParam | 请求参数错误。 |
