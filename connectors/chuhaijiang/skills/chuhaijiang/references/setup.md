# 出海匠连接器配置指引

当出海匠 MCP 工具不可用时，按本文引导用户完成配置。

引导期间用户的原任务保持暂停：不要一边引导一边用其他数据源把任务做掉；配置验证通过后再回来执行原任务。

## 第一步：确认用户有没有 API Key

先问用户：**"你有出海匠的 API Key 吗（`sk_live_` 开头）？"**

- **有** → 直接进入第二步
- **没有** → 把下面三步原样告诉用户（一次性给全）：
  1. 登录出海匠：https://www.chuhaijiang.com
  2. 进入出海匠开发者门户：https://developer.chuhaijiang.com
  3. 在开发者门户创建 API 密钥，得到一个 `sk_live_` 开头的 Key
  提醒用户：Key 只在创建时完整显示一次，先复制保存好。

## 第二步：写入 MCP 配置（你直接帮用户写，不要让用户手动改文件）

连接契约在所有客户端一致：

- **服务名**：`chuhaijiang`（固定英文小写，不要用中文名，中文名可能导致工具静默加载失败）
- **端点**：`https://mcp.gateway.chuhaijiang.com/mcp`（streamable HTTP）
- **认证**（二选一，服务端优先级 header > query）：
  - HTTP 请求头 `X-API-Key: <sk_live_ 开头的 Key>`
  - URL 查询参数 `?api_key=<Key>`（客户端不支持自定义请求头时用这个）

⚠️ 该端点带一个为 Claude.ai Connector 准备的形式化 OAuth：支持 OAuth 自动发现的客户端（如 Codex）会提示"登录成功"，但那个登录**不是有效认证**，调用照样 401——必须显式配置 Key，OAuth 流程走没走无所谓。

你运行在哪个客户端里你自己最清楚——把这份契约按所在客户端的 MCP 配置机制写入（配置文件里已有其他 MCP 服务条目时合并，不要覆盖）。已验证的写法：

### WorkBuddy

配置文件在**用户主目录下的 `.workbuddy/mcp.json`**（macOS/Linux 为 `~/.workbuddy/mcp.json`，Windows 为 `%USERPROFILE%\.workbuddy\mcp.json`）。确切路径以 WorkBuddy「MCP 服务管理 → 配置 MCP」界面顶部显示的「配置文件路径」为准，不确定时先探测该文件是否存在。

```json
{
  "mcpServers": {
    "chuhaijiang": {
      "type": "http",
      "url": "https://mcp.gateway.chuhaijiang.com/mcp",
      "headers": {
        "X-API-Key": "在这里粘贴你的API密钥（sk_live_开头）"
      },
      "disabled": false
    }
  }
}
```

写入即生效，不需要重启或新开会话。

### Claude Code

一条命令：

```bash
claude mcp add --transport http chuhaijiang https://mcp.gateway.chuhaijiang.com/mcp --header "X-API-Key: <Key>"
```

或把 WorkBuddy 同款 JSON 写进项目根目录 `.mcp.json`（团队共享时用这种）。新开会话生效；项目级 `.mcp.json` 首次使用会弹信任确认，`/mcp` 可查看连接状态。

### Codex

Codex 的 `mcp add` 不支持自定义请求头，用 query 参数一条命令搞定（过程中提示 OAuth 登录成功，无视它，见上面的警告）：

```bash
codex mcp add chuhaijiang --url "https://mcp.gateway.chuhaijiang.com/mcp?api_key=<Key>"
```

或在 `~/.codex/config.toml` 手写 header 方式：

```toml
[mcp_servers.chuhaijiang]
url = "https://mcp.gateway.chuhaijiang.com/mcp"
http_headers = { "X-API-Key" = "<Key>" }
```

改完必须重启 Codex 会话。注意：连接建立成功不校验 Key，必须走第三步真调工具才算验证通过。

### 其他客户端

按该客户端官方文档的远程 MCP（streamable HTTP）配置格式写入同一份契约：支持自定义请求头就用 `X-API-Key` 头，不支持就把 `?api_key=` 拼进 URL。不确定格式就查该客户端的文档，不要凭记忆编。

Key 的处理，按用户意愿二选一：

- 用户直接把 Key 发给你 → 完整写入配置，用户零手动操作；顺口提醒一句：Key 已进入对话记录，建议之后在开发者门户轮换
- 用户不想在对话里发 Key → 写入占位符版本，让用户自己把占位符替换成真实 Key（WorkBuddy 用户走「专家·技能·连接器 → 连接器 → MCP 服务管理 → 配置 MCP」界面；其他客户端直接改配置文件）

## 第三步：验证（先自己验，不行才让用户排查）

1. **自行验证**：配置写好后直接验证，不需要先让用户做任何操作。找工具时注意两点，**别误判成"服务未配置"**：
   - 实际工具名通常带服务名前缀（如 `mcp__chuhaijiang__account_info`），不是裸名 `account_info`
   - 工具可能是延迟加载的：客户端有工具搜索/加载机制时，先按 chuhaijiang 检索并加载 schema，再调用
   用实际全名调 account_info：
   - 返回账户信息和余额 → 配置成功，告诉用户余额情况，回到原任务（不需要用户做任何操作）
   - 返回 401 / 认证失败 → Key 填错或已失效，见「密钥失效处理」
   - 按前缀检索后工具列表里**确实没有**任何 chuhaijiang 工具 → 进入第 2 步
2. **引导用户排查**（确认工具真不存在才走到这步）：核心动作在各客户端一致——查配置、启用/信任、重载连接：
   - 配置没被识别 → 检查配置文件语法（常见问题：JSON/TOML 逗号引号错误、`disabled` 被设为 true），并确认改的是当前客户端真正读取的那个文件
   - 未启用/未信任 → 打开开关；弹出「信任此服务器」之类的确认时点信任
   - 已启用仍找不到工具 → 重载连接：WorkBuddy 在「专家·技能·连接器 → 连接器 → MCP 服务管理」把开关**关一次再开一次**（不需要重启）；Claude Code / Codex 新开会话
   然后回到第 1 步复验。同一个动作不要让用户重复做第二遍——两轮仍失败就停下来，把具体报错信息给用户看

## 故障处理（先分清是哪种故障）

工具调用出错时，按错误类型走不同分支，不要一律让用户换密钥：

### 连接失效（之前能用，现在报连接错误 / 超时 / 工具突然消失）

不是密钥问题。重载 MCP 连接（WorkBuddy：「MCP 服务管理」把 chuhaijiang 开关**关一次再开一次**；Claude Code / Codex：新开会话），然后用 `account_info` 复验。仍失败再检查网络，或看配置文件是否被改动。

### 密钥失效（返回 401 / 认证失败 / invalid key）

先排除一个 Codex 特例：如果配置里是**裸 URL**（没带 `api_key` 参数、也没配请求头），401 的根因是 OAuth 假 token，换多少新 Key 都没用——按第二步 Codex 写法把 Key 显式配上即可。其余情况：

1. 告诉用户当前 Key 已失效或填错
2. 引导用户去开发者门户重新创建一个 Key（同第一步）
3. 更新 MCP 配置里的 Key（`X-API-Key` 头或 URL 的 `api_key` 参数，同第二步，你直接帮改）
4. 重载连接后用 `account_info` 复验

任一故障都不要反复重试工具调用；两次失败就停下来走上面的分支。
