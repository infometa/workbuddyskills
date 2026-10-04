## 1. 接口描述

EDR响应中心查询任务执行记录，私有化调用path为：/capi/EDR/ListEDRRespondTaskRecords，从8.6P1版本开始支持

## 2. 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | 过滤条件、分页参数<br/><li>TaskSeq - string - 是否必填：是 - 操作符: eq - 排序支持：否 - 按任务Seq过滤。</li> <li>DeviceName - string - 是否必填：是 - 操作符: eq,ilike - 排序支持：否 - 按设备名称过滤。</li> <li>DeviceLoginUser - string - 是否必填：是 - 操作符: eq,ilike - 排序支持：否 - 按设备用户名称过滤。</li> <li>Status - string - 是否必填：是 - 操作符: eq - 排序支持：否 - 按任务状态过滤。</li> |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [ListEDRRespondTaskRecordsData](/开放API/云规范接口/版本：2022-06-01/数据结构.md#ListEDRRespondTaskRecordsData) | 数据<br/>注意：此字段可能返回 null，表示取不到有效值。|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: ListEDRRespondTaskRecords
<公共请求参数>

{}
```

#### 输出示例

```json
{
    "Response": {
        "Data": {
            "Items": [
                {
                    "DeviceGroupId": 101028,
                    "DeviceGroupName": "未分组终端",
                    "DeviceId": 116,
                    "DeviceLoginUser": "",
                    "DeviceMid": "6E27B4133DA1B7CAA88C038BB67D8BF9663E08C8",
                    "DeviceName": "seedsnie-PC3",
                    "DeviceUsername": "seedsnie",
                    "DoneTime": 0,
                    "Id": 4759,
                    "Result": "",
                    "Status": 0
                },
                {
                    "DeviceGroupId": 101028,
                    "DeviceGroupName": "未分组终端",
                    "DeviceId": 116,
                    "DeviceLoginUser": "",
                    "DeviceMid": "6E27B4133DA1B7CAA88C038BB67D8BF9663E08C8",
                    "DeviceName": "seedsnie-PC3",
                    "DeviceUsername": "seedsnie",
                    "DoneTime": 0,
                    "Id": 4412,
                    "Result": "",
                    "Status": 9
                },
                {
                    "DeviceGroupId": 101028,
                    "DeviceGroupName": "未分组终端",
                    "DeviceId": 116,
                    "DeviceLoginUser": "",
                    "DeviceMid": "6E27B4133DA1B7CAA88C038BB67D8BF9663E08C8",
                    "DeviceName": "seedsnie-PC3",
                    "DeviceUsername": "seedsnie",
                    "DoneTime": 0,
                    "Id": 4383,
                    "Result": "",
                    "Status": 9
                },
                {
                    "DeviceGroupId": 101028,
                    "DeviceGroupName": "未分组终端",
                    "DeviceId": 116,
                    "DeviceLoginUser": "",
                    "DeviceMid": "6E27B4133DA1B7CAA88C038BB67D8BF9663E08C8",
                    "DeviceName": "seedsnie-PC3",
                    "DeviceUsername": "seedsnie",
                    "DoneTime": 0,
                    "Id": 4389,
                    "Result": "",
                    "Status": 9
                }
            ],
            "Paging": {
                "PageCount": 1,
                "PageNum": 1,
                "PageSize": 50,
                "Total": 4
            }
        },
        "RequestId": "d4c08622-9b2b-4167-94fd-c55fb274c72e"
    }
}
```

## 5. 错误码

| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
| InvalidParameter.RequestParam | 请求参数错误。 |
