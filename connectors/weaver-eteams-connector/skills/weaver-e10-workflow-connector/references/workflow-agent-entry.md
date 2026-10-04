# Agent 入口与 Schema

## 什么时候读取

使用 `weaver-work-cli workflow` 处理流程查询、查看、打开、取日志或打开 OA 页面之前，或需要选择 operation、确认输入字段结构时，先读取本文件。

本文件只覆盖**只读类** operation（`search` / `todoStat` / `detail` / `summary` / `open` / `requestLog` / `pageOpen` / `memoryPrompt`）。发起、操作、批量、编辑、共享等写操作不在本目录参考文档范围内。

## 准备与探查命令

```text
weaver-work-cli --version
weaver-work-cli doctor --e10
weaver-work-cli --profile eteams workflow schema
```

如未登录，按共享规则读取登录与会话文档后处理。

`weaver-work-cli --profile eteams workflow schema` 是可用 operation、输入字段、固定参数与风险等级的第一信息源。所有 JSON 字段名以 schema 为准（camelCase，如 `pageSize`、`requestId`），不要臆造 schema 中不存在的字段。

## 固定入口

Agent 统一通过 operation 入口调用：

```text
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","pageSize":10}'
```

统一用 `--input-json` **内联**传入，`planJson`、`filterFields` 数组等嵌套结构同样内联（几百字符即可承载，不要写 JSON 文件）；仅当 JSON 很大或含 shell 难转义字符时才用 UTF-8 文件配 `--input <path>`。按环境选择示例：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","pageSize":10}'
```

## Operation 总览（只读）

| Operation | 用途 | 详细文档 |
| --- | --- | --- |
| `workflow.search` | 分页查询待办/已办/我发起/全部流程，支持多维度筛选与 plan 批量编排取数 | [workflow-query.md](./workflow-query.md) |
| `workflow.todoStat` | 按「工作流 × 参与节点 × 参与身份」三元组统计当前用户待办分组计数（智能分组第一步） | [workflow-query.md](./workflow-query.md) |
| `workflow.detail` | 按 requestId 或列表序号查看流程完整详情（基础信息 + 表单数据 + 签字意见） | [workflow-view.md](./workflow-view.md) |
| `workflow.summary` | 按 requestId 或列表序号生成流程业务摘要上下文（不标记已读） | [workflow-view.md](./workflow-view.md) |
| `workflow.open` | 按 requestId 或列表序号生成流程详情打开动作（URL + clientAction） | [workflow-view.md](./workflow-view.md) |
| `workflow.requestLog` | 按页查询流程签字意见/流转日志 | [workflow-view.md](./workflow-view.md) |
| `workflow.pageOpen` | 生成常用 OA 页面（待办/已办/草稿/监控等）或动态页（create/view）的打开地址 | [workflow-view.md](./workflow-view.md) |
| `workflow.memoryPrompt` | 读取用户记忆提示词；顺带返回 OA 版本与当前用户身份，无需再单独查询 | 本文档「记忆与版本定位」 |

## 记忆与版本定位（memoryPrompt）

`workflow.memoryPrompt` 用于读取用户记忆（工作流消歧、摘要字段优先级、展示偏好等）。其返回**顺带附带 OA 版本与当前用户身份**（可能缺失），无需再单独查询：

- `oaContext.version`：OA 系统版本，用于判断待办查询是否走智能分组（≥ `10.0.9909.01`）等版本分支。
- `oaContext.user`：`position`（岗位）、`department`（部门）、`subcompany`（分部，可能为空，为空时忽略分部，不要臆造）。

记忆读取时机：本轮尚未读过记忆，或距上次成功读取超过 6 小时时，先调用 `workflow.memoryPrompt`；之后复用，不重复调用。

`workflow.memoryPrompt` 的输入仅有可选 `workflowId`（工作流维度记忆）。本目录文档不展开记忆保存规则。

## 命令行结构

```text
weaver-work-cli --profile eteams --json workflow run <operation> --input-json '<json>'
```

- `--json`：全局开关，输出结构化 JSON 到 stdout。
- `workflow run <operation>`：资源 `workflow` 下的具体 operation。
- `--input-json '<json>'`：内联 JSON 输入（字段名 camelCase），**默认走这条**。
- `--input <path>`：从 UTF-8 文件读取 JSON 输入，**仅**供确实很大的 JSON 使用。

## 输出处理（大结果）

成功结果在 stdout，失败结果在 stderr。判定规则以共享 JSON 输出约定为准。

列表/详情结果可能很长时，不要把完整信封直接展示给用户。

默认 `pageSize=10` 小页读取；只渲染决策必要的字段（标题、流程编号、发起人、当前节点、停留时长、状态等）。

需要更多结果时按 `current` 分页继续；需要保留完整原始 JSON 时落本地文件并返回路径（见各 operation 的「返回」与「注意」）。

具体渲染形态（顶部统计行/分组标题/卡片两行或三行/摘要兜底等）由 OA 版本与执行模式决定，按各参考文档返回的 `finalMarkdown` 原样呈现，不要改写、压缩或重排。

## 注意

- 只读 operation 无需 confirm；本目录文档不引入写操作确认链。
- 业务输入里**禁止传入** Cookie、ETEAMSID、Token、`header.operator` 等凭据——这些由 CLI 托管。
- 失败/未知返回：CLI 失败时退出码非 0、**stderr** 为 `{ok:false, error:{type, subtype, message, retryable}}`（**没有** `success`/`stopReason`/`userMessage`/`doNotRetry` 字段）。`retryable=true` 时最多重试一次；否则原样转述 `error.message` 并停止，不换接口、不绕过；入参类错误按 `error.message` 补齐后重试一次。
- 未登录/登录失效（`error.type=authentication`）：按共享规则读取 `weaver-e10-shared-connector` 的 `references/e10-auth-and-session.md` 引导处理，认证完成后重放或续跑原请求（读操作可重放，写操作按 `partial/write_uncertain` 处理）。
- 不要把 schema 之外的 operation 当作可直接调用的 CLI 合约；字段名必须与 `weaver-work-cli --profile eteams workflow schema` 完全一致。
