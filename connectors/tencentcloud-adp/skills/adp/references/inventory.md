# 应用盘点

默认范围来自 `adp.jsonc` 的 `space_id`，也可显式 `--space-id`。
只有用户要求跨空间盘点时才用 `--all-spaces`；无配置不等于授权扫描所有空间。

没有 `adp.jsonc` 时，先列一个空间，再列该空间的应用，然后对单个应用列会话。失败信封里的 `adp init` 会写项目文件，不要执行。

```bash
adp schema --command "app list" --format json
adp space list --format json
adp app list --space-id <id> --fields appId,name,status,updateTime,spaceId --limit 50 --format json
adp conversation list --app-id <appId> --format json
```

读取 `truncated/total`；截断时提高 `--limit`，保留原来的空间、profile、env 和 fields。
未知 total 时逐步提高 limit 并设置调用次数上限；仍截断就明确报告不完整，不无限重试。
CLI 内部跟随 API 的 PageNumber/PageSize，不手签 Cloud API 分页。
`--page` 对每个列表命令都是 0 起始（首页是 `--page 0`），CLI 会换算成各 API 自己的起始页；
带 `--page` 时结果含 `page/pageSize`，截断时用 `--page <n+1>` 续取。
空列表表示当前范围无可见结果，不是权限完整性证明。

应用 `status`：1 未发布、2 运行中、3 已停用。`status` 与 `updateTime` 只能作为活跃代理指标。
`conversation list` 返回的会话属于当前凭据可见范围。结果字段 `scope` 的值是 `owner`，没有 `--scope` 参数。这不是应用所有 C 端请求量。
先 list，再用返回的 `conversationId` 和该行的 `type` 读消息：

```bash
adp conversation messages --conversation-id <id> --type <type-from-list> --format json
```

`messages` 同样是当前 CAM 可见范围。结果没有 `total`，也不走 `PageNumber`。`truncated=true` 且 `hasMoreBefore=true` 时，用返回的 `firstRecordId` 向更早翻页，并保留原来的 `--type`：

```bash
adp conversation messages --conversation-id <id> --type <type-from-list> --record-id <firstRecordId> --direction backward --format json
```

`truncated=true` 且 `hasMoreAfter=true`、方向是 forward 或 both 时，用 `lastRecordId` 和 `--direction forward`，同样保留 `--type`。

字段到正文、引用、角标、任务状态、MCP `toolResult`、token 摘要，以及消息上的 `type`（含 `tool_call`）、`trace.toolName` 和 `trace.traceId`。工具调用的入参在 `title`，结果在对应 content 的 `text`。`reasoningTokens` 只是计数，没有单独的思考正文。消息接口不接受 `--type 0`，把 list 行上的 `type` 传进去；省略时默认 1。
`adp usage` 返回该应用近 7 天的模型用量 KPI（`total_calls`、`total_tokens` 等），需要 `--app-id` 或 `adp.jsonc`。返回 450002 时是权限失败；不要把失败、空值或 owner 会话数当真实调用量。
