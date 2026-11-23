# 免登跳转基建（SSO forward）

> 加载时机：要把查询/选择结果变成「浏览器里已登录的飞鹤前端页」时。
> 本文件只讲编码、`/oauth2/forward`、`forwardCode` / `infoCode`。
> 国际字段表 [`air-intl-sso-forward.md`](air-intl-sso-forward.md)；国内字段表
> [`air-domestic-sso-forward.md`](air-domestic-sso-forward.md)。库：`scripts/sso_forward.py`。

## 目标

一次查询，让用户在系统浏览器打开飞鹤前端时**已经是登录态**。
服务端 `/oauth2/forward`：用 shopping 下发的 **forwardCode**（query `authCode`）换用户 → `logonFromMcp` → cookie → 302。

Python 用 `sso_forward.build_forward_url`。参数 `auth_code` 是当次 `forwardCode`，不要塞 MCP access_token。产品脚本只传入前端 path、hash 和本轮真实字段。

## 链路

```
① 产品脚本拼目标路由（path + hash query）
② 取当次 shopping 最外层 forwardCode
③ GET /oauth2/forward?redirectPage=<①编码后>&authCode=<②>
④ 服务端 getForwardUser → logonFromMcp → cookie → 302 到前端目标页
```

前端只认 URL hash query 里的 `token`（覆盖 `companyCode/userCode/sessionID/userSessionID`），
**不读** `X-Auth-Token` cookie——身份必须由 `/forward` 注入重定向 URL。

唯一输出：HTTPS `/oauth2/forward`（query `authCode`=forwardCode）。国内/国际「去下单」都走它。

## 两个授权码

查询成功时 `domestic_shopping` / `intl_shopping` 最外层同时下发：

- `forwardCode`：只给 `/oauth2/forward?authCode=`
- `infoCode`：只给页内 busi（请求头 `X-Auth-Code`）

两者 30 分钟、整页共用。不要每个舱位发一张，不要把 MCP access_token 写进 HTML/URL。

## forward 请求

```
GET {portal}/api/portal/mcp/oauth2/forward?redirectPage=<路由整体编码一次>&authCode=<forwardCode>
```

`redirectPage` 是**整个路由再编码一次**（`quote(route, safe='')`）；服务端解一次后得到
原始路由，再拼 `Location`。

## 编码规则

1. **中文必须双重编码**：`redirectPage` 里的中文，服务端解码一次后拼进 `Location`，非 ASCII 会被丢弃，表现为没有 Location 的 302。中文值要先 `quote(值)` 再被外层 `quote(整段路由)` 兜一次，最终是 `%25E4...`。
2. **空格必须保持 `%20`**：路由里出现裸空格时 forward 仍可能 302，但会变成 `error_code=login_error`（不注入登录态）。**绝不能解码成裸空格**。
3. **路由不要过长**：完整参数大约 700 字符以上可能被前置网关直接 404。优先只带必要字段。

`sso_forward.encode_value` 按上述规则实现，产品脚本不要再手写一套。JSON 字段若需
`,` `/` 保持裸字符（国际下单 `flightList`），用 `encode_json_param`。

## 无角色授权时

该员工在 portal 没有角色授权记录时，`/forward` 可能变成 `error_code=login_error`，表现为「账号已登出」。
助手在当前对话前台重新打开浏览器：Windows 执行与本说明同目录的 `auth-login.cmd`，macOS / Linux 执行同目录 `sh auth-login.sh`。让用户在网页里重新登录。命令找不到时读 stderr，不要全盘搜索，不要让用户自己去找连接器入口。仍不行再转人工在 portal 补授权。不要声称已经免登成功。

## 页面按钮

- `href` 用产品脚本 + 本基建的输出，**不写死城市/日期/MCP token**。
- 国内/国际页：`authCode` 来自当次 shopping 的 `forwardCode`。国内退改补查、国际「查舱位」用 `infoCode`。
  授权码明文不得写入日志、对话；本机本地 HTML 短时效是允许的例外。
- 查询结果 HTML/JS 字段名只用 `infoCode` / `forwardCode`，不要写 `token`。
- 页面不直调 MCP `tools/call`（认证由 `fh` 附加）。页内只打 busi：国际 `intlShop`、国内 `rule`，头 `X-Auth-Code`。
