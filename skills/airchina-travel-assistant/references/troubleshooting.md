# 调不通时怎么查

按请求路径从外到内排查，定位到哪一层就去 `status-codes.md` 对错误码。

## 1. 网络到不了

| 现象 | 可能原因 |
|------|---------|
| `Could not resolve host` | DNS 出问题，检查本机解析 |
| `Connection refused` / 超时 | 端口被防火墙挡；测试环境走 9066，生产走 443 |
| TLS 证书错 | 本机时钟漂移，或在中间加了 HTTPS 代理 |

快速验证：
```bash
curl -v --connect-timeout 5 https://m.airchina.com.cn:9066/
```

## 2. 鉴权失败（getAccessToken 返回非 0000）

直接对照错误码表，常见 `0003`（appId 错）/ `0004`（secretKey 不匹配）/ `0001`（channel 错，腾讯侧必须是 `TENCENT`）。

## 3. 业务接口失败

拿到 accessToken 之后，`/api/services/` 返回非 0000：

| 错误码 | 怎么查 |
|-------|--------|
| `1000` 签名失败 | **第一个怀疑对象：MD5 大写没？** 其次再看 body 拼串顺序 |
| `3000` IP 未白 | 联系国航对接人加白（以对端看到的 IP 为准，不要自己用 `ifconfig.me` 查） |
| `3001` 无权限 | 联系国航开通该 adapter/procedure 的权限 |
| `0005` token 失效 | `airchina.sh get-token --force` 强制刷新 |

## 4. 业务层失败（securityCode=0000 但 resp.code 不对）

此时网关已放行，问题在业务系统本身：

- 短信 `50023038`：60 秒频控，等一分钟
- 领券成功码是 `00000000`（8 个 0），非它就看 `resp.msg` 的具体文案

## 调试模式

```bash
AIRCHINA_DEBUG=1 scripts/airchina.sh send_sms_code --phone 13xxxxxxxxx
```

会把每一步中间值（明文、签名、密钥、密文、响应）打到 stderr，方便对账。

## 扩展新接口后如果不通

按下面顺序排查：

1. 新接口的 `adapter` / `procedure` 拼对了吗？
2. req 的 JSON 字段名和值类型与国航约定一致？（字段名区分大小写、值全是字符串）
3. 国航侧对这个 appId 开通了新接口的权限吗？（否则 `3001`）
4. 响应 `resp.code` 的成功码是多少？可能又是新的（文档说"后续补充"）
