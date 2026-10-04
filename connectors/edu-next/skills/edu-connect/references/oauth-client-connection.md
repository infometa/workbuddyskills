# OAuth 客户端连接与恢复

仅在首次配置 Edu Next MCP、完成 OAuth 授权、刷新凭证、处理 `401 invalid_token` 或重新授权时读取本参考。

## 发现授权服务器

通过 MCP 服务器的 protected-resource metadata 发现 Ory Hydra OAuth 2.1 授权服务器。使用动态注册或预注册客户端以及 Authorization Code + PKCE（`S256`）完成授权。

授权请求明确包含 `openid email profile offline_access`。Metadata 和动态客户端注册中的 scope 只声明客户端可以请求的范围，本次 authorization request 仍需包含 `offline_access`。让用户在浏览器中看到客户端身份和请求范围，并明确允许或拒绝授权。

## 保存与刷新凭证

确认 token response 同时包含 access token 和 refresh token，再将它们保存到 MCP 客户端的安全凭证存储中。

在 access token 到期前使用 refresh token 自动续期。服务端返回轮换后的 refresh token 时，原子替换旧值，并让并发请求共用同一次刷新。

## 恢复授权

收到 `401 invalid_token` 时，刷新 access token 并重试原请求一次。refresh grant 已失效或授权已撤销时，重新发起浏览器授权。

密码、PAT、secret key、长期 token 和 service-role 凭证只进入安全凭证存储，不进入对话、Tool 参数、任务包或项目文件。
