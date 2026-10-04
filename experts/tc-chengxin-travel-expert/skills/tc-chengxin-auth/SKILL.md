---
name: tc-chengxin-auth
description: 仅在同程领券或查询脚本返回未登录、授权失效或401后使用。脚本自动区分本机桌面与移动端/云端；不得提前授权，浏览器只由脚本唤起。
---

# 同程程心授权

只在业务返回未登录/401后使用。CLI 管理 Token，不接收 API Key、手机号、验证码或密码。

## 授权流程

1. 使用真实 Base directory 前台执行一次：

   ```bash
   node "<Base directory for this skill>/scripts/ensure-auth.js" --start
   ```

   业务接口的 401 是最终判据。`--start` 先使旧授权失效，再创建新会话；不得因本地 status 为 `READY` 跳过授权。

2. 端类型只由 `--start` 判断，不得自行选路径或调用通用浏览器/电脑控制/截图工具：
   - `DESKTOP_BROWSER_POLL`：本机 macOS、Windows 或有图形 Linux。脚本打开默认浏览器并在当前命令内轮询；用户无需回复“已登录”，不另起进程或调用 `--poll`。
   - `LOGIN_LINK`：手机、小程序、真正无图形的云端或打开失败。把 `AUTH_URL` 写成 `[登录同程旅行](url)`，提示登录后回复“已登录”并结束本轮；不得代操作页面。
3. 桌面端 `READY` 后自动重试原操作一次。手机/云端收到“已登录”后只执行一次 `node "<Base directory for this skill>/scripts/ensure-auth.js" --check`；`READY` 时自动重试，其他状态如实说明并结束。仅用户明确要新链接时重新 `--start`。

## 安全

只使用已验证 URL，不展示授权 JSON、session ID、secret、Token 或凭证路径。未成功不继续。严禁自建中继、改网关/CLI、注入凭证或要求 Connector。

若宿主/用户明确要求指定目录交付 Markdown，阻塞时直接执行：

```bash
node "<Base directory for this skill>/scripts/write-blocked-result.js" --output-dir "<绝对目录>" --status "待授权" --reason "同程旅行账号尚未完成授权" --login-url "<脚本验证后的 HTTPS 授权链接>"
```

脚本固定生成含“状态/已完成/未完成/原因/登录入口/下一步”的键值 Markdown；不只留中间证据，不现场自建模板。
