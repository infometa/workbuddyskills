# WorkBuddy 连接器故障恢复

先确认当前工具来自本连接器，且 profile 为 `workbuddy`、API 为 `https://freenote.patch-x.cn`。旧测试 MCP 或另一个本地 profile 的登录状态不能替代当前连接。

## 状态与动作

| 状态/错误 | 动作 |
| --- | --- |
| 安装下载失败、命令找不到 | 检查 WorkBuddy 运行时和 `cli.json` 安装步骤，确认 native CLI 已准备好 |
| `no_credential` / `refresh_expired` | 发起浏览器授权，完成后继续原任务 |
| `invalid_credential` | 同 profile 使用 `mcp login --force` 重新取得凭据 |
| `server_or_client_mismatch` | 核对同一 profile、API 和 CLI 默认 client_id；不要沿用另一环境的凭据 |
| `credential_unavailable` | 提示原生凭据存储不可读，先解决存储问题，不连续发起短信登录 |
| `authenticated=true` 但工具 `auth_required` | 一次 `mcp status --verify` 确认；服务端明确失效时强制重新授权 |
| `token_refresh_failed` / `transport_error` | 暂时无法刷新或连接，保留凭据；网络恢复后重试原工具 |
| `permission_denied` | 说明当前操作权限不足，检查所选账号/平台，不冒充未登录 |
| `rate_limited` | 按服务返回提示稍后重试，不重新登录 |
| `invalid_params` | 读取实时工具 schema 修正参数，不重新登录 |
| 记录为空 | 说明当前平台暂无记录，不判断为授权失败或其他平台也无记录 |

状态命令：

```sh
npx --yes patchxnote-agent@0.2.16 mcp status --output json --profile workbuddy --server-base-url https://freenote.patch-x.cn
```

仅需要核实服务端是否接受凭据时加 `--verify`；不要把它放入 WorkBuddy 的周期状态轮询。

## 浏览器与回调

- 正常连接时：WorkBuddy 读取 `--no-browser` 输出的链接；必须保留 `authWaitForExit=true`，否则 CLI 回调进程可能提前结束。
- 对话恢复时：执行不带 `--no-browser` 的 `mcp login --force`，由 CLI 打开浏览器。
- 浏览器没有打开时说明这一阶段；不要宣称已经完成重新授权。
- 用户取消、关闭网页或等待超时后停止等待。需要重试时使用新的登录流程，不复用过期回调链接。
- 重新授权成功后，先调用当前连接器的账户工具。仍失败时重连当前连接器，再恢复原任务。
- 不因一次网络错误先执行 logout；不要从 `auth_required` 单独推断用户“从未登录”。

## 内容和草稿

该 stdio 服务代理远程 MCP。`patchxnote_get_memory` 可能只提供元数据；完整的可读笔记可通过 `patchxnote_render_webhook_message` 的 Markdown 返回值取得。

远程草稿调用不要传 `save_draft=true`、`out` 或本地 `draft_dir`。在聊天中展示返回内容，不能把元数据当成完整笔记。

## 升级或重复入口

新包保留 source `patchxfreenote`。发现旧 `note-test` 配置时指出其地址和来源；处理本连接器时始终使用 `https://freenote.patch-x.cn`，不默认删除其他入口。低于最低 WorkBuddy 版本时提示升级，不反复登录。

排查只报告失败阶段、版本、状态和错误码，不输出令牌、验证码或完整用户记录。
