# 智在记录 · 消息与录音卡

发送站内消息，查询录音卡用量。可跳过动态模版管线。

## 统一结果判定

先看 HTTP：`400`/`401`/`406` → 无权限（检查 `ZHIZAI_REC_API_KEY`）。再看 JSON：`resultCode == "0"` 为成功。

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {},
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

对用户：可用 `resultMsg` 短句；禁止展示完整 Key、`stack`、未脱敏 `errorInfos`。限流 ≤2 次/秒。

`ZHIZAI_BASE_URL` = `https://openapi.zzjilu.com/api/v1`。Header：`Authorization: ${ZHIZAI_REC_API_KEY}`（无 Bearer）。


## 意图路由

| 意图 | 接口 |
|---|---|
| 发送消息 | `POST /msg/sendMessage` |
| 单卡用量 | `GET /recordingCard/queryUsage?deviceSn=` |
| 批量用量 | `POST /recordingCard/batchQueryUsage` |

## 使用注意

- 发消息前确认手机号与内容；`phoneNum`/`title`/`message` 必填。
- 批量 SN 单次最多 100 个；关注 `notFoundSnList`。
- `deviceStatus`：`CONNECTED` / `DISCONNECTED`；向用户用中文说明电量、存储、文件数等。

## 接口协议

### POST `/msg/sendMessage`  发送消息

**接口说明**：发送消息  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phoneNum | string | 是 | 手机号（必填） |
| title | string | 是 | 消息标题（必填） |
| message | string | 是 | 消息内容（必填） |
| url | string | 否 | 跳转地址 |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/msg/sendMessage\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "phoneNum": "",
  "title": "",
  "message": "",
  "url": ""
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | null | 是 | 返回数据对象（为null） |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": null,
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/recordingCard/queryUsage`  查询录音卡使用情况

**接口说明**：按SN码查询录音卡使用情况：设备信息、归属用户、连接状态（CONNECTED-连接/DISCONNECTED-断开）、电量、存储、最近心跳/上报时间及录音文件列表  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| deviceSn | string | 是 | 录音卡SN码，唯一标识一张录音卡 |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/recordingCard/queryUsage?deviceSn=SN20260826001' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功，-1表示失败 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.id | Long | 是 | 录音卡记录ID |
| resultObject.userId | Long | 是 | 归属用户ID（最近一次上报的用户） |
| resultObject.deviceVendor | string | 否 | 设备厂家 |
| resultObject.deviceName | string | 否 | 设备名称 |
| resultObject.firmwareVersion | string | 否 | 固件版本 |
| resultObject.deviceSn | string | 是 | 录音卡SN码 |
| resultObject.latitude | string | 否 | 设备当前所在位置纬度 |
| resultObject.longitude | string | 否 | 设备当前所在位置经度 |
| resultObject.batteryLevel | integer | 否 | 剩余电量（百分比，0-100） |
| resultObject.remainStorage | Long | 否 | 剩余存储容量（字节） |
| resultObject.deviceStatus | string | 否 | 设备状态（CONNECTED-连接，DISCONNECTED-断开） |
| resultObject.lastHeartbeatTime | Long | 否 | 最近一次心跳上报时间（毫秒时间戳） |
| resultObject.reportTime | Long | 否 | 最近一次上报时间（毫秒时间戳） |
| resultObject.creatorId | Long | 否 | 建档用户ID（服务端冗余字段） |
| resultObject.createTime | Long | 否 | 建档时间（毫秒时间戳，服务端冗余字段） |
| resultObject.updatorId | Long | 否 | 最近修改用户ID（服务端冗余字段） |
| resultObject.updateTime | Long | 否 | 最近修改时间（毫秒时间戳，服务端冗余字段） |
| resultObject.status | string | 否 | 数据状态（00A-有效，00X-无效，服务端冗余字段） |
| resultObject.fileCount | integer | 是 | 当前录音文件总数 |
| resultObject.fileList | array | 是 | 当前录音文件列表 |
| resultObject.fileList[].fileName | string | 是 | 录音文件名称 |
| resultObject.fileList[].duration | Long | 否 | 录音时长（秒） |
| resultObject.fileList[].fileSize | Long | 否 | 录音文件大小（字节） |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "id": 1409833657651040300,
    "userId": 1234567890,
    "deviceVendor": "华为",
    "deviceName": "录音卡Pro",
    "firmwareVersion": "v1.2.3",
    "deviceSn": "SN20260826001",
    "latitude": "31.2304",
    "longitude": "121.4737",
    "batteryLevel": 88,
    "remainStorage": 34359738368,
    "deviceStatus": "CONNECTED",
    "lastHeartbeatTime": 1759200000000,
    "reportTime": 1759199700000,
    "creatorId": 1234567890,
    "createTime": 1759199700000,
    "updatorId": 1234567890,
    "updateTime": 1759199700000,
    "status": "00A",
    "fileCount": 2,
    "fileList": [
      {
        "fileName": "REC_001.wav",
        "duration": 60,
        "fileSize": 1024
      },
      {
        "fileName": "REC_002.wav",
        "duration": 120,
        "fileSize": 2048
      }
    ]
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/recordingCard/batchQueryUsage`  批量查询录音卡使用情况

**接口说明**：按SN码列表批量查询录音卡使用情况：空白条目自动过滤、重复SN自动去重，单次最多100个；已注册的SN返回使用情况，未注册的SN回传notFoundSnList便于对账  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| deviceSnList | array | 是 | 录音卡SN码列表，单次最多100个；空白条目自动过滤，重复SN自动去重（保持首次出现顺序） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/recordingCard/batchQueryUsage \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
	"deviceSnList": ["SN20260826001", "SN20260826002", "SN_NOT_EXIST"]
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功，-1表示失败 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.cardList | array | 是 | 查询到的录音卡使用情况列表，顺序与去重后的请求SN列表一致 |
| resultObject.cardList[].id | Long | 是 | 录音卡记录ID |
| resultObject.cardList[].userId | Long | 是 | 归属用户ID（最近一次上报的用户） |
| resultObject.cardList[].deviceVendor | string | 否 | 设备厂家 |
| resultObject.cardList[].deviceName | string | 否 | 设备名称 |
| resultObject.cardList[].firmwareVersion | string | 否 | 固件版本 |
| resultObject.cardList[].deviceSn | string | 是 | 录音卡SN码 |
| resultObject.cardList[].latitude | string | 否 | 设备当前所在位置纬度 |
| resultObject.cardList[].longitude | string | 否 | 设备当前所在位置经度 |
| resultObject.cardList[].batteryLevel | integer | 否 | 剩余电量（百分比，0-100） |
| resultObject.cardList[].remainStorage | Long | 否 | 剩余存储容量（字节） |
| resultObject.cardList[].deviceStatus | string | 否 | 设备状态（CONNECTED-连接，DISCONNECTED-断开） |
| resultObject.cardList[].lastHeartbeatTime | Long | 否 | 最近一次心跳上报时间（毫秒时间戳） |
| resultObject.cardList[].reportTime | Long | 否 | 最近一次上报时间（毫秒时间戳） |
| resultObject.cardList[].creatorId | Long | 否 | 建档用户ID（服务端冗余字段） |
| resultObject.cardList[].createTime | Long | 否 | 建档时间（毫秒时间戳，服务端冗余字段） |
| resultObject.cardList[].updatorId | Long | 否 | 最近修改用户ID（服务端冗余字段） |
| resultObject.cardList[].updateTime | Long | 否 | 最近修改时间（毫秒时间戳，服务端冗余字段） |
| resultObject.cardList[].status | string | 否 | 数据状态（00A-有效，00X-无效，服务端冗余字段） |
| resultObject.cardList[].fileCount | integer | 是 | 当前录音文件总数 |
| resultObject.cardList[].fileList | array | 是 | 当前录音文件列表 |
| resultObject.cardList[].fileList[].fileName | string | 是 | 录音文件名称 |
| resultObject.cardList[].fileList[].duration | Long | 否 | 录音时长（秒） |
| resultObject.cardList[].fileList[].fileSize | Long | 否 | 录音文件大小（字节） |
| resultObject.notFoundSnList | array | 是 | 未注册的SN码列表（未通过全量上报建档），便于接入方对账 |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "cardList": [
      {
        "id": 1409833657651040300,
        "userId": 1234567890,
        "deviceVendor": "华为",
        "deviceName": "录音卡Pro",
        "firmwareVersion": "v1.2.3",
        "deviceSn": "SN20260826001",
        "latitude": "31.2304",
        "longitude": "121.4737",
        "batteryLevel": 88,
        "remainStorage": 34359738368,
        "deviceStatus": "CONNECTED",
        "lastHeartbeatTime": 1759200000000,
        "reportTime": 1759199700000,
        "creatorId": 1234567890,
        "createTime": 1759199700000,
        "updatorId": 1234567890,
        "updateTime": 1759199700000,
        "status": "00A",
        "fileCount": 2,
        "fileList": [
          {
            "fileName": "REC_001.wav",
            "duration": 60,
            "fileSize": 1024
          },
          {
            "fileName": "REC_002.wav",
            "duration": 120,
            "fileSize": 2048
          }
        ]
      },
      {
        "id": 1409833657651040500,
        "userId": 9876543210,
        "deviceVendor": "小米",
        "deviceName": "录音卡Lite",
        "firmwareVersion": "v1.0.5",
        "deviceSn": "SN20260826002",
        "latitude": null,
        "longitude": null,
        "batteryLevel": null,
        "remainStorage": null,
        "deviceStatus": "DISCONNECTED",
        "lastHeartbeatTime": 1759100000000,
        "reportTime": 1759100000000,
        "creatorId": 9876543210,
        "createTime": 1759100000000,
        "updatorId": 9876543210,
        "updateTime": 1759100000000,
        "status": "00A",
        "fileCount": 0,
        "fileList": []
      }
    ],
    "notFoundSnList": [
      "SN_NOT_EXIST"
    ]
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

## 安全约束（强制）

- `sendMessage`：发送前确认手机号与内容。
- 录音卡批量最多 100 个 SN；关注 `notFoundSnList`。
