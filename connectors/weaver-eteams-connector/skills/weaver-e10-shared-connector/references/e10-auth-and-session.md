# E10 认证与会话（连接器模式）

## 什么时候读取

需要确认登录态、诊断 E10 连接、遇到登录失效，或任务涉及 profile、base URL、auth 文件时读取本文件。

## 环境是固定的

| 项 | 值 |
| --- | --- |
| 登录域名（base URL） | `https://weapp.eteams.cn` |
| profile 名 | `eteams` |
| 宿主标识（agent_type） | `workbuddy` |

**所有业务命令必须显式带 `--profile eteams`。** CLI 的 `--profile` 是全局参数，必须放在子命令之前：

```text
weaver-work-cli --profile eteams --json <业务域> run <operation> --input-json '{"key":"value"}'
```

不显式指定时，CLI 会使用本机当前活跃 profile —— 用户机器上可能存在其他环境的历史登录态（例如内部 OA 环境），那样会取到**别的环境**的数据或登录态。

## 基本检查

```text
weaver-work-cli --version
weaver-work-cli --profile eteams --json auth status --no-check
```

`--no-check` 只读取本地登录态、不发网络请求。判定已登录：输出中 `loggedIn` 为 `true` 且 `profile` 为 `eteams`。

也可以使用：

```text
weaver-work-cli doctor --e10
weaver-work-cli auth whoami
```

## 登录由连接器完成

Agent **不负责发起登录**。连接器在用户点「连接」时会自行执行：

```text
weaver-work-cli --base-url https://weapp.eteams.cn auth login --agent_type workbuddy
```

（`authWaitForExit` / `authSuppressBrowser` 已由连接器配置为适应该 CLI 的浏览器授权方式；连接器随后轮询 `status` 命令确认登录结果。）

因此 Agent 的职责只有两个：**读登录态**、**失效时引导用户重连**。

### 判定为登录失效的情形

- `--profile eteams --json auth status --no-check` 输出 `loggedIn: false`
- `doctor --e10` 的 `e10AuthFile` 检查为 `ok: false`
- 业务命令失败，stderr JSON 中 `error.type === "authentication"`（如 `E10 auth not found`）
- 业务命令返回 `error.subtype === "session_expired"`（E10 登录态 401/302 失效）

### 失效时的正确处置

1. 停止当前业务流程，**不要自动重试**写入/删除类命令。
2. 告知用户：

> 当前连接器的 E10 登录态已失效，请回到连接器面板断开连接后重新点「连接」，连接器会重新打开浏览器完成授权。

3. 用户重连后再重新执行原业务命令；仍失败则把 `error.type/subtype/message` 原样反馈并停止。

### 禁止事项

- 禁止在 Skill 内执行 `weaver-work-cli auth login` / `auth set` / `auth xiaoe` 等登录命令（登录由连接器调度，Agent 自行登录会与连接器状态不一致）。
- 禁止向用户索要登录域名；域名已由连接器固定。
- 禁止索要或要求用户粘贴 Cookie、ETEAMSID、业务 Token、app key / app secret。
- 禁止使用示例占位域名（如 `https://weapp.xxx.cn`）尝试登录。
- 禁止因为本地存在其他 profile 就切换环境（`auth profile use`），或在不带 `--profile` 的情况下重试业务命令。
- 禁止读取、列出、打印或解析认证目录与认证文件（`~/.weaver-work-cli/e10` 下的 `profiles/*`、`auth`、`config.json`）以及 Keychain 项；登录态判断只能通过 `auth status` / `auth whoami` / `auth profile list` / `doctor --e10` 和业务命令的 JSON 错误完成。

## Profile 与环境（只读使用）

```text
weaver-work-cli auth profile list
weaver-work-cli auth profile current
weaver-work-cli --profile eteams --json auth status --no-check
```

- 连接器使用的 profile 固定为 `eteams`，不需要也不需要切换「活跃 profile」。
- `auth profile current` 显示的可能不是 `eteams`（本机活跃指针由用户其他使用场景决定），这不代表连接器未登录 —— **以 `--profile eteams` 的检查结果为准**。

通过 `weaver-work-cli run` 执行外部命令时，CLI 会按所选 profile 注入 `WEAVER_BASE_URL`、`WEAVER_ETEAMSID`、`WEAVER_COOKIE`、`WEAVER_USER_AGENT` 和 `WEAVER_AGENT_TYPE`。这些值只给子进程使用，不应在回复或日志中明文展示。

## 安全边界

Agent 不要要求用户贴 Cookie、ETEAMSID、业务 Token、app key 或 app secret，也不要直接读取用户机器上的 auth、config 或 Keychain 数据。业务 Skill 只负责调用 CLI；登录态读取、Cookie 拼接、业务 Token 获取和 HTTP header 注入都由 `weaver-work-cli` 内部完成。

