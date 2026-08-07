# 出海匠连接器配置指引

当出海匠 MCP 工具不可用时，按本文引导用户完成配置。

引导期间用户的原任务保持暂停：不要一边引导一边用其他数据源把任务做掉；配置验证通过后再回来执行原任务。

## 目录

- [选择认证方式](#第一步选择认证方式)
- [配置 MCP](#第二步配置-mcpworkbuddy-由用户操作其他客户端由-ai-代配)
- [验证连接](#第三步验证先自己验不行才让用户排查)
- [故障处理](#故障处理先分清是哪种故障)

## 第一步：选择认证方式

先按当前客户端选择认证方式：

- **WorkBuddy 官方“出海匠”连接器**使用 OAuth：添加连接器后，由 WorkBuddy 打开浏览器完成登录和授权，不需要创建、复制或向 AI 提供 API Key。
- **其他客户端**支持 MCP OAuth 时，同样优先使用原生 OAuth；不支持 OAuth 时再使用 API Key。

只有当前客户端不支持 OAuth，或用户明确选择 API Key 兼容方式时，才继续下面的 API Key 流程。WorkBuddy 官方连接器直接进入第二步。

需要使用 API Key 时，创建页的固定地址是：

`https://developer.chuhaijiang.com/dashboard/apps`

用户选择 API Key 且已在当前对话说明 Key 状态时，不重复询问；否则先问用户：**"你已经有并保存了出海匠 API Key 吗（`sk_live_` 开头）？"**

- **有且已保存** → 直接进入第二步，不打开创建页；任何客户端都不要把 Key 发给 AI，配置只写在用户本机
- **没有、找不到，或创建后没有保存** → 旧 Key 无法再次查看，需要创建新的；不要让用户自己依次登录官网、进入开发者门户、寻找创建入口，由 AI 直接打开下面的创建页

只有需要创建新 Key 时，才用当前客户端的终端/Bash 工具执行与运行环境匹配的一条命令：

| 系统 / Shell | 命令 |
|---|---|
| macOS（Bash / zsh） | `open "https://developer.chuhaijiang.com/dashboard/apps"` |
| Windows（cmd） | `start "" "https://developer.chuhaijiang.com/dashboard/apps"` |
| Windows（PowerShell） | `Start-Process "https://developer.chuhaijiang.com/dashboard/apps"` |
| Linux | `xdg-open "https://developer.chuhaijiang.com/dashboard/apps"` |

只执行当前环境对应的一条命令，不要把命令丢给用户自己运行。该深链会直接进入「应用与密钥」；用户未登录时会先跳转到出海匠统一登录页，登录完成后按原路由返回创建页。

命令执行后，告诉用户下一步：

> 我已经为你打开出海匠「应用与密钥」页面。请按页面提示完成登录；如果还没有应用，先创建一个应用，再点击「创建密钥」。API Key 只在创建成功时完整显示一次，请先复制保存，不要发到对话里；我会写入占位配置，再由你在本机替换。

打开命令不可用、客户端没有终端工具或浏览器未成功启动时，才降级为把 [API Key 创建页](https://developer.chuhaijiang.com/dashboard/apps) 发给用户点击，不要退回旧的三步导航。打开页面不等于密钥已创建；不要替用户操作登录或创建密钥，也不要读取浏览器页面、剪贴板或任何已有 Key。用户保存好 Key 后继续本机配置，不在对话中传递。

## 第二步：配置 MCP（WorkBuddy 由用户操作，其他客户端由 AI 代配）

OAuth 与 API Key 使用同一服务的独立认证入口，不能混用：

- **服务名**：`chuhaijiang`（固定英文小写，不要用中文名，中文名可能导致工具静默加载失败）
- **API Key 端点**：`https://mcp.gateway.chuhaijiang.com/mcp`（streamable HTTP）
- **OAuth 端点**：`https://mcp.gateway.chuhaijiang.com/mcp/oauth`（streamable HTTP）
- **OAuth（优先）**：只使用 OAuth 端点且不配置静态 header；客户端通过 protected-resource metadata 发现 Gateway 授权服务器，使用 Authorization Code + PKCE S256
- **API Key（兼容）**（二选一，服务端优先级 header > query）：
  - HTTP 请求头 `X-API-Key: <sk_live_ 开头的 Key>`
  - URL 查询参数 `?api_key=<Key>`（客户端不支持自定义请求头时用这个）

先识别当前客户端，再按对应方式配置。WorkBuddy 使用官方连接器的 OAuth 流程；其他客户端使用 OAuth 时，由用户在浏览器完成授权。任何客户端都绝不索要 OAuth code、Access Token 或 Refresh Token。其他客户端使用 API Key 时，由 AI 按该客户端的 MCP 配置机制写入占位符版本（配置文件里已有其他 MCP 服务条目时合并，不要覆盖）。

### WorkBuddy

WorkBuddy 官方“出海匠”连接器使用 OAuth。不要引导用户创建或粘贴 API Key，也不要尝试用 Bash、编辑配置文件或手填服务地址替用户连接。

1. 打开「专家·技能·连接器 → 连接器」
2. 搜索「出海匠」，点击连接器卡片右侧的「+」
3. WorkBuddy 会打开浏览器授权页；浏览器没有出海匠登录态时，先按页面提示登录，再确认授权
4. 页面显示“授权已完成，可以关闭窗口”后，关闭该页面并返回 WorkBuddy，确认连接器显示已连接

打开授权页不等于连接成功。请用户完成登录和授权后回复“已连接”，再进入第三步验证；不需要重启或新开会话。

### Claude Code

OAuth 推荐命令：

```bash
claude mcp add --transport http chuhaijiang https://mcp.gateway.chuhaijiang.com/mcp/oauth
```

若 OAuth 不可用，再用 API Key 兼容命令并由用户在本机替换占位符：

```bash
claude mcp add --transport http chuhaijiang https://mcp.gateway.chuhaijiang.com/mcp --header "X-API-Key: <Key>"
```

命令执行后新开会话生效，`/mcp` 可查看连接状态。

### Codex

Codex 直接添加裸 URL，按浏览器提示完成 OAuth：

```bash
codex mcp add chuhaijiang --url "https://mcp.gateway.chuhaijiang.com/mcp/oauth"
```

若当前 Codex 版本不支持该 OAuth 流程，再使用 API Key query 参数兼容方式：

```bash
codex mcp add chuhaijiang --url "https://mcp.gateway.chuhaijiang.com/mcp?api_key=<Key>"
```

或在 `~/.codex/config.toml` 手写 header 方式：

```toml
[mcp_servers.chuhaijiang]
url = "https://mcp.gateway.chuhaijiang.com/mcp"
http_headers = { "X-API-Key" = "<Key>" }
```

改完必须重启 Codex 会话。服务端会在新连接握手时验证 Key 真值；仍需走第三步真调工具，确认当前客户端已正确加载工具。

### 其他客户端

按该客户端官方文档的远程 MCP（streamable HTTP）配置格式写入 OAuth 端点并尝试 OAuth；不支持 OAuth 时改用 API Key 端点，支持自定义请求头就用 `X-API-Key`，否则把 `?api_key=` 拼进 URL。不确定格式就查该客户端的文档，不要凭记忆编。

非 WorkBuddy 客户端使用 API Key 时，只写入占位符版本，让用户自己在本机替换；不要在对话、命令输出或日志里接收、显示完整 Key。

## 第三步：验证（先自己验，不行才让用户排查）

1. **自行验证**：WorkBuddy 等用户完成界面配置并回复“已连接”；其他客户端在配置写好后直接验证。进入验证后，不需要再让用户做其他操作。找工具时注意两点，**别误判成"服务未配置"**：
   - 实际工具名通常带服务名前缀（如 `mcp__chuhaijiang__account_info`），不是裸名 `account_info`
   - 工具可能是延迟加载的：客户端有工具搜索/加载机制时，先按 chuhaijiang 检索并加载 schema，再调用
   用实际全名调 account_info：
   - 返回账户信息和余额 → 配置成功，告诉用户余额情况，回到原任务（不需要用户做任何操作）
   - 返回 401 / 认证失败 → 使用 OAuth 时进入「OAuth 授权失效」；使用 API Key 时进入「密钥失效」
   - 按前缀检索后工具列表里**确实没有**任何 chuhaijiang 工具 → 进入第 2 步
2. **引导用户排查**（确认工具真不存在才走到这步）：核心动作在各客户端一致——查配置、启用/信任、重载连接：
   - 配置没被识别 → WorkBuddy 检查官方“出海匠”连接器是否已添加并显示已连接；其他客户端检查配置文件语法（常见问题：JSON/TOML 逗号引号错误、`disabled` 被设为 true），并确认改的是当前客户端真正读取的那个文件
   - 未启用/未信任 → 打开开关；弹出「信任此服务器」之类的确认时点信任
   - 已启用仍找不到工具 → 重载连接：WorkBuddy 回到「专家·技能·连接器 → 连接器」，搜索「出海匠」后按页面提供的操作重新连接（不需要重启）；Claude Code / Codex 新开会话
   然后回到第 1 步复验。同一个动作不要让用户重复做第二遍——两轮仍失败就停下来，把具体报错信息给用户看

## 故障处理（先分清是哪种故障）

工具调用出错时，按错误类型走不同分支，不要一律让用户换密钥：

### 连接失效（之前能用，现在报连接错误 / 超时 / 工具突然消失）

不是密钥问题。重载 MCP 连接（WorkBuddy：回到「专家·技能·连接器 → 连接器」，搜索「出海匠」后按页面提供的操作重新连接；Claude Code / Codex：新开会话），然后用 `account_info` 复验。仍失败再检查网络，或看配置文件是否被改动。

### OAuth 授权失效（返回 401 / 认证失败，且当前连接使用 OAuth）

不要让用户创建或更换 API Key。回到当前客户端重新连接出海匠，并在浏览器完成登录和授权；WorkBuddy 使用官方“出海匠”连接器提供的重新连接入口。授权完成后用 `account_info` 复验。

### 密钥失效（返回 401 / 认证失败 / invalid key）

本节只适用于 API Key 兼容模式；WorkBuddy 官方连接器使用 OAuth，不走这里。

1. 告诉用户当前 Key 已失效或填错
2. 按第一步由 AI 直接打开 API Key 创建页，让用户重新创建一个 Key
3. 由 AI 更新 MCP 配置里的 `X-API-Key` 请求头或 URL `api_key` 参数
4. 重载连接后用 `account_info` 复验

任一故障都不要反复重试工具调用；两次失败就停下来走上面的分支。
