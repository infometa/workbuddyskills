# Gateway OAuth Binding

## Preferred WorkBuddy Native OAuth

1. Call the single `tongzhou-fin-research` Connector for the original research request. The business call itself is the connection check.
2. If it is disconnected, WorkBuddy opens the gateway browser authorization page through native OAuth with PKCE.
3. The user signs in if needed and approves the public-research scope. WorkBuddy receives the native callback and stores a renewable session.
4. Retry the original Connector call once. Do not run Shell, npm, Node, a local credential check, or an API-Key helper first.
5. New conversations and WorkBuddy restarts reuse the protected renewable session. Reauthorization is required only after revoke, refresh-family failure, or session expiry.

```text
同舟研究能力尚未连接。请在 WorkBuddy 点击“连接”，并在自动打开的浏览器页面确认授权；完成后我会重试刚才的查询。无需复制 API Key，也不要把任何凭证发到聊天中。
```

Community handoff is optional and independent. A missing community configuration, QR, or enterprise-WeChat link must not turn an approved OAuth connection into a failure.

## Codex Registered MCP OAuth

Codex uses the single configured MCP server `tongzhou-fin-research`, normally installed as the npm stdio OAuth proxy. Call its namespaced tools directly. Do not run a preflight shell command before normal research. If the registered MCP server reports that authorization is required, complete Device Flow and retry the original tool call once.

The public namespaces are:

- `fin_data__<tool>`
- `doc_search__<tool>`
- `fin_graph__<tool>`
- `same_boat__<tool>`

## No Local Credential Path

The current expert and Codex plugin do not ship `gateway_api.cjs`. They do not read `~/.config/fin-mcp-gateway`, `FIN_MCP_GATEWAY_API_KEY`, or any equivalent local API-Key source. Do not recreate a bridge script or turn a missing local key into an OAuth error.

If a user pastes an API Key, access token, refresh token, authorization code, or SMS code into chat, do not echo, save, or use it. Ask the user to remove the message and authorize from the client connection UI.

## Service And Feedback Entry

OAuth authorization success already exposes the mobile community handoff. For group access, product feedback, usage questions, or reopening the entry after installation:

- WorkBuddy: reopen the `tongzhou-fin-research` Connector authorization page from settings, or use `https://mcp-gateway.textmind-gz.com/login`.
- Codex and other npm-installed clients: run `npx --yes tongzhou-fin-research-expert@latest support`; it uses the renewable OAuth session and returns a short-lived same-origin service URL.

This route does not require reinstalling the expert or sharing credentials in chat.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| Connector not connected in WorkBuddy | Browser authorization was not approved, expired, or the session was revoked | Click `连接`, approve the browser page, then retry the same request once |
| Registered Codex MCP is unavailable | OAuth proxy was not installed, authorization is incomplete, or the client has not reloaded config | Run the npm setup/auth flow outside the research turn, restart Codex if config changed, then retry the original MCP tool |
| Prior-turn or cached data exists after auth failure | The conversation contains old evidence | Do not summarize or reuse it; authorize and rerun the query |
| Expert sees unrelated global/deferred MCP tools | Runtime exposes tools outside the governed connection | Do not call them; use only `tongzhou-fin-research` |
| 401 | OAuth session is no longer accepted | Reauthorize the Connector; do not request tokens |
| 403 | Tool/server is not in the account grant | Explain the capability boundary |
| 429 | Minute/day quota reached | Follow `Retry-After` |
| 503/504 | Gateway or upstream is temporarily unavailable | Stop retries after the documented limit and state the temporary gap |

## Security

- WorkBuddy and the npm proxy own OAuth token storage and refresh.
- Do not print or inspect access tokens, refresh tokens, API Keys, authorization codes, SMS codes, full phone numbers, holdings, or trade history.
- Do not use cached evidence after authorization failure.
