# 短信验证码接口 sendSMSVeriCodeActivity

- **adapter**：`ACOTADigitalProducts`
- **procedure**：`sendSMSVeriCodeActivity`
- **调用方**：外部服务商
- **原始内网地址（仅文档留痕）**：`http://10.211.144.113:9080/airchina/inner/sendSMSVeriCodeActivity.do`

## 请求参数（放在 req 字段里）

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| areaCode | String | 是 | 手机号国家码 | `86` |
| phone | String | 是 | 接收短信手机号 | `188xxxxx63` |

请求示例：

```json
{
  "phone": "188xxxxx63",
  "areaCode": "86"
}
```

## 响应参数（resp 解密后）

| 参数 | 类型 | 说明 |
|------|------|------|
| code | string | 状态代码，`"0"` 成功 |
| msg | string | 状态文言 |

响应示例：

```json
{
  "resp": {
    "code": "0",
    "msg": "ok"
  }
}
```
