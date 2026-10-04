---
name: gaia-cli
description: WorkBuddy 中使用已连接的 Gaia CLI External SaaS 能力。包含 WorkBuddy 专属认证流程、Gaia CLI 业务发现、权限检查、动态命令调用和错误恢复规则。
---

# Gaia CLI for WorkBuddy

本 Skill 面向 WorkBuddy 连接器，完整覆盖 Gaia CLI 的 External SaaS 使用规则。WorkBuddy 使用本 Skill 了解连接器认证、业务发现、权限检查、动态命令、安全确认和错误恢复，不需要额外加载其他基础 Skill。只使用连接器安装并管理的 `gaia` 命令，不切换隐藏的 Profile、channel、环境、云或服务端点。

## 连接器边界

- 当前连接器只支持 Gaia CLI External SaaS 模式，不提供员工账号、WFM、Work 租户选择或内部模式命令。
- WorkBuddy 负责调用 `init`、`auth`、`status` 和 `unAuth`。普通业务对话不要主动执行登录、登出、更新、卸载或修改本地凭据。
- 不要读取或修改 `config.json`、Token 文件、Client Secret、Cookie 或其他本地凭据，也不要要求用户把 Token、密码或 Secret 粘贴到对话中。
- 不要使用 `curl`、`wget`、自建 HTTP 客户端或猜测的业务 URL 绕过 Gaia CLI。

## WorkBuddy 认证

连接器认证配置执行 `gaia login --browser`。首次连接、解绑后重新连接或本地没有租户配置时：

1. CLI 打开本地回环地址的租户 Code 页面；
2. 用户提交租户 Code 后，当前页面重定向到该租户的 SSO 授权页；
3. 用户完成授权后，CLI 接收本机回调并保存登录状态。

提交租户 Code 后不应再打开第二个授权 Tab。如果用户看到重复 Tab、授权页没有打开或回调失败，让用户在 WorkBuddy 中重新连接，并报告 CLI 的原始错误；不要索取凭据。

已保存租户 Code 时，`gaia login --browser` 会复用该租户，不会再次询问。需要切换租户时：

- 优先让用户在 WorkBuddy 中解绑并重新连接；连接器的 `unAuth` 执行 `gaia logout --all`，会清理 Token、登录状态和缓存的租户 Code；
- 用户明确要求在已有 CLI 进程中切换时，可以执行 `gaia login --browser --config`，提交并完成新租户授权后才替换当前活动租户。

不要在普通业务对话中执行 `gaia logout` 修复业务错误；连接和断开由 WorkBuddy 连接器流程负责。

## 开始前检查

需要执行 Gaia CLI 前，使用：

```bash
gaia version
gaia status --json
```

`status --json` 中：

- `logged_in=true`、`login_status="Logged in"`、`token_status="Valid"`：可以继续；
- `token_status="Expiring soon"`：只允许继续当前只读操作；任何写操作前先让用户重新连接；
- `logged_in=false`、`Not logged in`、`Token expired` 或 `Unavailable`：停止业务调用，让用户在 WorkBuddy 中重新连接。

该状态只反映本地 Token 是否存在及是否过期，不代表服务端仍接受该 Token；输出中的租户、环境和云只用于展示当前上下文，不要据此切换隐藏配置。需要诊断时可执行 `gaia doctor --json`，但不要要求用户打开配置或凭据文件。

## 发现业务能力

用户没有给出精确命令时先发现，不要猜测模块、资源、方法或参数：

```bash
gaia api list --json
gaia api show <module> [resource] [--version <version>] --json
gaia commands list --json
gaia commands list --module <module> --json
gaia <module> <resource> <method> --help
```

已知模块时优先使用 `gaia commands list --module <module> --json`。需要非默认 Discovery 文档时使用 `--version <version>`；未指定时默认使用 `v1`。执行前用精确命令的 `--help` 核对 path/query 参数、请求体字段、必填声明和示例。`--help` 只读取 Discovery，不执行权限校验或业务接口。`unspecified` 代表 Discovery 未声明必填性，不能自行推断。

## 确认 API 注册

需要确认某个模块、资源和方法是否已注册到当前 Discovery 时，使用：

```bash
gaia api check <module> <resource> <method> [--version <version>] --json
```

该命令只检查 API 注册信息，不代表当前账号拥有调用权限，也不会替代 Permission 检查。

## 权限检查

需要判断当前账号是否可以调用接口时，使用 Discovery 提供的 resource code 或接口契约中的权限元数据：

```bash
gaia permission check <resource-code> --json
gaia permission list --filter <text> --json
gaia permission has <code> [code...] --json
```

`permission check` 检查资源访问权限；`permission list` 和 `permission has` 查询当前 SaaS 上下文的 action/权限 code。不要猜 resource code，不要把 action code 缺失直接解释为资源权限拒绝，也不要自动申请权限或切换账号。

动态业务命令的权限校验返回 `allowed=false` 时，优先按 CLI 返回的结构化信息解释：`missing_scopes` 只表示 Discovery scopes 与当前租户 action code 的差集；`permission_diagnosis_failed` 表示诊断本身失败，不能臆测缺失权限；如果提示租户已拥有全部 scopes，应说明拒绝不能归因于缺少 action code。权限服务自身返回 401、非 200、网络错误或无效响应时，保留原始错误，不自行补推权限结论。

## 执行动态命令

动态命令格式为：

```bash
gaia <module> <resource> <method> \
  --params '<JSON object>' \
  --body '<JSON object>' \
  --header '<JSON object>'
```

- `--params` 只放契约声明的 path/query 参数；
- `--body` 只放契约声明的 JSON 请求体；
- `--header` 只放必要的业务 Header，值必须来自契约且保持字符串类型，不能覆盖 `Authorization`；
- Authorization Token 由 CLI 自动注入，不能手工传入；
- 不要添加当前 CLI、Discovery 或精确命令 `--help` 未声明的请求体字段；
- `--debug` 可能输出完整 Authorization Token，只在用户明确要求排障且不会把结果回传或写入公开内容时使用。

查询、列表和状态类操作在参数明确后可以直接执行。创建、提交、修改、删除、撤回、审批、授权、权限变更或其他会改变外部状态的操作，执行前必须展示准确对象、关键参数和影响范围，并获得用户明确确认。

## 输出与安全

Agent 需要稳定字段时优先使用 `--json`，但除非用户明确要求原始 JSON，不要整段转发 CLI JSON：单个对象整理为字段和值，多条记录整理为表格或列表，布尔结果直接说明是/否。不得输出 Token、刷新 Token、密码、Client Secret、Cookie、完整 Authorization Header 或本地凭据内容。

## 错误恢复

- 命令或参数不存在：只重新运行对应命令的 `--help`，按实际契约修正一次；
- 本地未登录或 Token 过期：提示用户在 WorkBuddy 中重新连接，完成后只重试原命令一次；
- 业务请求返回 401：即使本地 Token 未过期，也提示用户在 WorkBuddy 中先解绑再重新连接；解绑会执行 `gaia logout --all` 清理旧 Token 和租户配置，完成新授权后只重试原命令一次；不要只执行普通 `gaia login --browser` 后盲目重试；
- 返回 403 或权限不足：报告 CLI 返回的缺失权限或拒绝原因，不自动申请、切换账号或绕过权限；
- 返回 404：先核对模块、资源、方法和标识符，不猜测替代值；
- 网络错误、超时或 5xx：保留原参数，说明原始错误；只有操作可安全重试且不会造成重复写入时才重试一次；
- 认证失败、连接器未连接或需要清理本地登录：让用户使用 WorkBuddy 的解绑/重新连接流程处理。

认证恢复完成后只重试原命令一次；仍然失败时停止重试并报告原始错误和恢复结果。
