---
description: Show ChainGuard plugin status, mode, server connectivity, and supported ecosystems
---

Run the ChainGuard status diagnostic and show the user the result.

Execute this command:

```
node ${CODEBUDDY_PLUGIN_ROOT}/dist/security-guard.cjs --status
```

The command outputs JSON with the plugin's current status including:
- `enabled`: whether the plugin is active
- `plugin_version` / `client_version`: version info
- `mode`: current product mode (smooth/audit/strict)
- `server`: server connectivity and auth status
- `supported_ecosystems`: which package ecosystems are covered

Show the user a brief, readable summary of the status card. If the server is not reachable, suggest checking the `CODEBUDDY_SERVICE_PROXY_URL` environment variable. If auth failed (401), suggest re-authenticating with CodeBuddy. Always show:
- Support / 反馈支持: @selinasong (如遇异常可执行 `/chainguard-debug` 开启调试并导出日志)
Do NOT dump the raw JSON — format it as a short status card.
