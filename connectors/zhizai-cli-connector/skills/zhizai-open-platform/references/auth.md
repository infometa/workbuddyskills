# 智在记录 · 鉴权

负责把“用户想用智在记录”推进到可调业务接口的状态。不要只说“已配置”：Key 非空且至少一次业务调用 `resultCode=0` 才算连接成功。

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


## 首次连接闭环

1. 检查智能体/环境中的 `ZHIZAI_REC_API_KEY` 是否已配置且非空。
2. 未配置：只提示前往 [智在记录开发者](https://www.zzjilu.com/pc/developer) 获取并配置；不调业务接口。
3. 无写入验收：`POST /note/queryNoteList`，`pageNum=1`、`pageSize=1`。成功才可宣布已连接。
4. 用户明确要求用口令换 Key 时，才调用 `getApiKeyByPassword`；**禁止**在对话中完整输出口令或返回的 `API-KEY`。

## 意图路由

| 意图 | 接口 |
|---|---|
| 口令换 API Key | `POST /auth/getApiKeyByPassword` |
| 解析 token | `GET /auth/analysisToken?token=` |

## 安全与恢复

- 不展示或记录完整 `Authorization` / API Key；调试仅掩码。
- 鉴权失败引导检查环境变量，不回显 Header。
- `analysisToken` 身份字段按最小必要展示，不回显完整 token。

## 接口协议

### POST `/auth/getApiKeyByPassword`  通过口令获取API-KEY

**接口说明**：通过口令获取个人的API-KEY  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phoneNum | String | 是 | 手机号 |
| password | String | 是 | 口令（管理员提供） |
| teamId | Long | 是 | 根团队ID |

#### 请求示例

```bash
curl --request POST \
  --url 'https://openapi.zzjilu.com/api/v1/auth/getApiKeyByPassword' \
  --header 'content-type: application/json' \
  --data '{
    "phoneNum": "13900001111",
    "password": "{cipher}{aes}TestPassword1234567890ABCDEF",
    "teamId": 1234567890123456789
  }'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.API-KEY | string | 是 | 个人API-KEY |
| resultObject.tokenExpDate | string | 是 | API-KEY失效时间 |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表 |
| guidance | null | 是 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "API-KEY": "DemoApiKey1234567890==",
    "tokenExpDate": "2027-12-31 23:59:59"
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/auth/analysisToken`  解析token

**接口说明**：解析token  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| token | string | 是 | 用户鉴权令牌 |

#### 请求示例

```bash
curl --request GET \
  --url https://openapi.zzjilu.com/api/v1/auth/analysisToken?token= \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | object | 是 | 用户登录信息对象 |
| stack | string | 是 | 异常堆栈信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "token": null,
    "userId": 8912493637529600,
    "userName": "张三",
    "phoneNo": "13900001111",
    "realName": null,
    "tenantId": null,
    "attributes": null
  },
  "stack": ""
}
```
