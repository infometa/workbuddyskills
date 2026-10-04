---
name: getnote-auth
description: 连接和诊断得到大脑 MCP 授权，并查看开放平台调用额度。用户说“连接/登录得到大脑”“为什么不能用”“查看额度或限额”时使用。
---

# 得到大脑连接与额度

WorkBuddy 通过连接器内置的 OAuth 2.1 + PKCE 流程管理登录态，不要求用户提供 API Key、Cookie、Authorization 或其他凭证。

## 连接与恢复

- 首次调用需要授权时，引导用户在 WorkBuddy 的连接器界面点击“连接”，然后只在浏览器授权页确认。
- 浏览器授权完成后，继续原请求；不要索要、展示或记录授权码、access token、refresh token、state 或 PKCE verifier。
- 工具返回 `missing_token`、`invalid token`、`token is inactive` 或其他明确认证错误时，说明授权已失效，引导用户重新连接；不要反复重试原请求。
- 网络错误或 `dependency_failure` 不等同于授权失效。仅在结果标记可重试时稍后重试一次，并保留返回的 `request_id`。
- WorkBuddy 自动刷新 access token；不要自行实现 Token 存储、续期或交换。

## 查询额度

用户询问 API/MCP 限额，或工具返回限流错误时调用 `get_quota`。分别展示返回的 `read`、`write`、`write_note` 桶及其日/月 `limit`、`used`、`remaining`、`reset_at`；不要合并或自行换算不同额度桶。

所有 MCP 调用与其他开放平台调用共享服务端日/月额度。空列表是成功结果，不是额度耗尽；只根据明确限流错误或 `get_quota` 返回值判断。
