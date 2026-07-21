# 状态码对照

## 网关层 securityCode（顶层字段）

| 编码 | 描述 |
|------|------|
| 0000 | 成功 |
| 0001 | channel 为空或不存在 |
| 0002 | subChannel 为空或不存在 |
| 0003 | appId 为空或不存在 |
| 0004 | appId & secretKey 验证不匹配 |
| 0005 | accessToken 为空或已失效 |
| 1000 | 签名验证失败 |
| 3000 | IP 地址不在白名单 |
| 3001 | 无权访问该服务 |

## 业务层错误码（resp.code）

| 编码 | 描述 |
|------|------|
| 0 | 成功（短信接口 sendSMSVeriCodeActivity） |
| 00000000 | 成功（领券接口 tencentClaimCoupon） |
| 50023038 | 60 秒内短信验证码只能获取一次（短信接口频控） |
| 其他 | 后续补充 |

## 响应结构

网关响应在 `securityCode`/`resp`/`msg` 外还有一个规范没写的字段 `RiskCode`（风控预留，通常空字符串）。skill 只读 `securityCode` 和 `resp`，`RiskCode` 可忽略。

```json
{
  "RiskCode": "",
  "resp": "<AES 密文，需解密后再 URL-decode>",
  "securityCode": "0000"
}
```

## 排障速查

| 现象 | 原因 | 怎么办 |
|------|------|--------|
| `securityCode=0005` | accessToken 过期 | `get-token --force` 刷新；skill 内置 110 分钟缓存自动续 |
| `securityCode=1000` | 签名不对 | 确认 MD5 结果是**大写 hex**（skill 已内置，改实现时别踩回去） |
| `securityCode=3000` / 生产环境 HTTP 500 | 出口 IP 不在白名单 | 联系国航对接人，以对端实际看到的 TCP 源 IP 为准 |
| `securityCode=3001` | appId 无权访问此 adapter/procedure | 联系国航侧开通权限 |
| 响应解密成功但 JSON 解析失败 | 解密后没做 URL-decode | Bash/Python 版都已内置，自定义扩展时别忘 |
| 短信 `code=50023038` | 60 秒内重发 | 让用户等 1 分钟；正常用户体感无感 |
| 领券 `code` 非 `00000000` | 业务层拒绝（如验证码错、活动已结束） | 看 `resp.msg` 文案 |
