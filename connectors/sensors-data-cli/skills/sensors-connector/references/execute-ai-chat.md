# execute-ai-chat — 神策 AI 对话（SDAF OpenAPI）

> 工具 `ai.chat` · 命令 `sensors ai chat` · 需要 sensors-cli ≥ 1.1.0。
> AI 域鉴权要求 `api-key` + `sensorsdata-project` +
> `X-Organization-Id` 三个请求头，**org_id 必填**（缺省时 CLI 会报带恢复提示的配置错误）。

## 用途

客群发现与运营增长白名单场景。精确数字、明细、可复算结果走 CLI 链路。

## 参数

```bash
sensors ai chat "<用户原始请求文本>" [--session-id <id>] [--execution-mode review|autonomous]
              [--thinking-mode standard|deep] [--skills <name>]... [--sub-agent-name <name>]
              [--timeout 120] [--format json|pretty] [--include-raw]

sensors ai resources [--resource all|skills|subagents] [--language zh-CN] [--timeout 30]
```

## 输入 Schema

请求体由 CLI 生成，首轮不传 `session_id`；后续传 `--session-id` 时同时发送 body 字段和 `X-Sai-Session-Id` header。

## 输出

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `CONTENT` | positional | yes | — | **用户原始请求文本**：不改写、不翻译、不摘要 |
| `--session-id` | string | no | 新会话 | 复用会话 ID（首轮不传）；复用时同时带请求体字段与 `X-Sai-Session-Id` 请求头 |
| `--execution-mode` | enum | no | `review` | `review` 等待人工确认；`autonomous` 自主执行（**仅用户明确要求时**） |
| `--thinking-mode` | enum | no | `standard` | Plan 思考模式：`standard` / `deep`（深度思考，更慢） |
| `--skills` | string[] | no | — | 优先参考的 skill 名，可重复；先 `sensors ai resources` 确认 |
| `--sub-agent-name` | string | no | — | 优先使用的 subagent；同上 |
| `--message-id` | string | no | 服务端生成 | 消息 ID |
| `--session-hidden` | flag | no | false | 创建隐藏会话 |
| `--cron-task` | flag | no | false | 按定时任务对话模式执行 |
| `--do-not-remember` | flag | no | false | 本轮不写入长期记忆 |
| `--include-raw` | flag | no | false | 在 `data.raw` 保留服务端原始响应 |
| `--timeout` | int | no | 120 | 秒；复杂分析可能超时，属正常 |
| `--format` | enum | no | `json` | `json` / `pretty`（无 text 渲染模式） |

## 输出字段（data）

| 字段 | 说明 |
|---|---|
| `session_id` | 会话 ID；多轮对话必须复用它（服务端可能在 `data` / `message.session` / chunk 内返回，CLI 已统一提取） |
| `message_id` | 本轮消息 ID |
| `reply` | **最终答复正文，向用户汇报以此为准** |
| `sections` | dict[str, list]：按 chunk 类型分组的过程信息（执行计划、思考过程等），仅作进展说明 |
| `cards` | 结构化卡片内容 |

## 示例

```bash
# 首轮
sensors ai chat "分析最近 7 天新用户激活率下降的可能原因"
# -> 记下输出 data.session_id，如 sess-abc123

# 多轮追问（复用会话）
sensors ai chat --session-id sess-abc123 "按渠道拆开看看"

# 超时恢复（任务可能仍在服务端执行，复用同一 session，不要重新提交）
sensors ai chat --session-id sess-abc123 "请同步当前进展"

# 查看可用 skills / subagents（传 --skills 前必做）
sensors ai resources --resource all

# 深度思考 + 指定 skill
sensors ai chat --thinking-mode deep --skills funnel-analysis "……"
```

## 错误

| 现象 | 含义 | 恢复 |
|---|---|---|
| `SensorsConfigError`（org_id） | AI OpenAPI 缺组织 ID | `sensors config init --org-id <ORG>` 或 `--org-id` 覆盖 |
| HTTP 401 | 认证失败 | 核对 API Key / Project / Org ID，重新 `sensors connector auth` |
| HTTP 403 | 无 AI 权限 | 联系管理员开通 AI 能力 |
| HTTP 404 / 405 | 服务端未开放或版本不兼容 | 确认 base_url 与 ai-server 版本 |
| `[TIMEOUT]` | 服务端执行中超时 | **复用 session_id 发「请同步当前进展」，不要重新提交** |

## 边界

- AI 对话可能创建神策侧资产（分群/标签/报告）：汇报时提醒用户到平台确认，不要宣称"已创建成功"。
- 内部业务能力标识（如 `analytic_agent`、`horizon_segment_agent`）会被拒绝，不要尝试。
- 链路 A 不能替代写操作的确认流程。
