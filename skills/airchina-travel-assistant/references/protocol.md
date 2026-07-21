# 国航 B2C 网关协议细则（摘自规范 v1.0.0）

## 网关地址

- 授权：`POST {gateway}/airchina/gateway/ota/v2.0/auth/getAccessToken`
- 业务：`POST {gateway}/airchina/gateway/ota/v2.0/api/services/`

| 环境 | Gateway |
|------|---------|
| 测试 | `https://m.airchina.com.cn:9066` |
| 生产 | `https://m.airchina.com.cn` |

## 鉴权

- 入参（URL query）：`appId`、`secretKey`、`channel`、`subChannel`
- 成功响应：`{ "securityCode": "0000", "accessToken": "..." }`
- accessToken 有效期 **2 小时**

## Header（9 项全必填）

| 参数 | 说明 |
|------|------|
| channel | 渠道名称（腾讯 WorkBuddy 为 `TENCENT`） |
| subChannel | 子渠道（固定 `OTA`） |
| appId | 应用 Id |
| accessToken | 鉴权接口换来的 token |
| signString | 请求 body 的 MD5 签名（**大写 hex**）|
| adapter | 业务接口标识，决定路由到哪个适配器 |
| procedure | 业务接口标识，决定适配器内具体方法 |
| serviceVersion | 接口版本，默认 10000，当前 10100 |
| Content-Type | `application/x-www-form-urlencoded` |

## 请求 Body（通用 3 字段）

| 参数 | 说明 |
|------|------|
| lang | 语言码：`zh_CN` / `en_US` / `jn_JP` / `ko_KR` |
| timestamp | 毫秒时间戳 |
| req | 业务请求 JSON 字符串（各业务接口自定义字段） |

## 签名算法（MD5）

1. 取出 queryString 和 body 的所有键值对
2. URL-decode 后按 key 升序排序
3. 拼成 `k1=v1&k2=v2&...&kn=vn`（末尾无 `&`）
4. 对拼接后的字符串做 MD5，得到 `signString`

## 加密算法（AES）

- 算法：`AES/ECB/PKCS5Padding`
- 密钥：**accessToken 的第 8~24 位**（16 字节，AES-128）
- 请求体：整串明文 body（排好序的 `k=v&k=v...`）整体加密，Base64 后作为 HTTP body 发出
- 响应体：网关响应的 `resp` 字段是密文，需用同一密钥解密

## 响应公共参数

| 参数 | 类型 | 说明 |
|------|------|------|
| securityCode | String | 网关层状态码，`0000` 表示通过 |
| msg | String | 错误文言 |
| resp | String | 业务响应报文（密文，需解密） |
| RiskCode | String | **文档未写**，实测存在，目前为空字符串；推测是国航风控链路预留字段，skill 忽略即可 |

## 业务层成功码

业务层的成功码**不统一**，按接口而定：
- `sendSMSVeriCodeActivity`：`resp.code == "0"`
- `tencentClaimCoupon`：`resp.code == "00000000"`
