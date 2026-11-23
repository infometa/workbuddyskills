# WorkBuddy 安装、登录与重连

## 连接方式

本包要求 WorkBuddy 5.0.0 或以上：`mcp.json` 顶层 `preAuth: "cli"` 调度同目录 `cli.json`，随后启动本地 stdio MCP。连接器仍为 MCP 类型，账号和记录读取由远程服务处理。

- CLI：`patchxnote-agent@0.2.16`
- 配置档案：`workbuddy`
- 环境：`production`
- API：`https://freenote.patch-x.cn`
- 后端 MCP：`https://freenote.patch-x.cn/mcp`
- 代理模式：`PATCHXNOTE_MCP_MODE=remote`

连接器 `source=patchxfreenote` 是市场身份；CLI 登录和 MCP 继续共用 CLI 默认 OAuth client_id，不用 source 替换它。

## 首次连接

1. WorkBuddy 按 `cli.json` 准备 Node、npm wrapper 和原生 CLI。首次下载发生在安装阶段。
2. 执行 `mcp status --output json`，读取当前配置档案。轮询不执行 `--verify`，不刷新凭据。
3. 未登录时执行 `mcp login --no-browser --force`。CLI 输出完整授权链接，WorkBuddy 打开浏览器。
4. `authWaitForExit=true` 保留 CLI 的本机回调监听；用户在网页完成手机号验证码授权。
5. CLI 保存凭据后退出；WorkBuddy 再启动同版本、同 profile 和同服务地址的 `mcp serve`。
6. 调用 `patchxnote_get_current_user` 及 `patchxnote_list_memories`（`{"platform":"mobile","limit":5}`），然后继续原来的请求。

Windows 的 CLI 调度使用 `npx.cmd`；MCP 使用 WorkBuddy 托管 Node 环境中的 `npx`。不要从 WSL 登录后假定 Windows WorkBuddy 能读取那份凭据。若安装或命令解析失败，先处理对应阶段，不把它归因于账号授权。

## 对话中恢复授权

在同一运行环境执行以下命令会由 CLI 直接打开浏览器：

```sh
npx --yes patchxnote-agent@0.2.16 mcp login --force --profile workbuddy --server-base-url https://freenote.patch-x.cn
```

`--force` 用于已有凭据失效或用户要求切换账号；新授权成功前不替换旧凭据。先检查状态，避免每次查询都调用登录。

登录后仍通过当前连接器工具确认可用；必要时只重连当前连接器。不要另建一个默认 profile 的 MCP 来充当恢复成功证据。

## 保持登录、退出和升级

- `access_expires_at`：访问令牌到期时间；自动刷新由 CLI 处理。
- `refresh_expires_at`：刷新凭据到期时间，刷新后以新值为准。
- 默认时长为 15 分钟和 30 天，不表示用户每 15 分钟重新登录，也不是永久登录保证。
- WorkBuddy 重启时先读取持久化状态，不应重新弹出授权窗口。
- 退出/切换账号使用同参数的 `mcp logout`，再登录并核对当前账户；只处理 `workbuddy` 配置档案。
- 从旧远程连接器升级到此包需要首次完成 CLI 授权；以前由 WorkBuddy 保存的远程 OAuth 凭据不会自动迁移到 CLI。
- “解绑连接器”与“退出账号”不是同一动作；是否执行了 unAuth 以实际结果为准。

凭据保存在既有原生凭据存储中。用户只在浏览器输入验证码，不把任何验证码或令牌粘贴到聊天。
