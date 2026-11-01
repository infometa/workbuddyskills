# execute-ai-chat — 神策 AI 对话（SDAF OpenAPI）

> 工具 `ai.chat` · 命令 `sensors ai chat` · 会话作用域能力需要 sensors-cli ≥ 2.0.1；SSE 流式（`--stream` / `--progress` / `--progress-file`）需要 ≥ 2.0.3。
> AI 域鉴权要求 `api-key` + `sensorsdata-project` +
> `X-Organization-Id` 三个请求头，**org_id 必填**（缺省时 CLI 会报带恢复提示的配置错误）。

## 用途

客群发现与运营增长白名单场景。精确数字、明细、可复算结果走 CLI 链路。

## 参数

```bash
sensors ai chat "<用户原始请求文本>" [--session-id <id>] [--new-session] [--conversation-key <key>]
              [--execution-mode review|autonomous] [--thinking-mode standard|deep]
              [--skills <name>]... [--sub-agent-name <name>]
              [--stream] [--progress] [--progress-file <path>]
              [--timeout 1800] [--format json|pretty] [--include-raw] [--include-http]

sensors ai sessions list [--all-conversations] [--format json|pretty]

sensors ai resources [--resource all|skills|subagents] [--language zh-CN] [--timeout 30]
```

## 输入 Schema

请求体由 CLI 生成，且**每次请求都携带 `session_id`**。请求体里的 `stream` 默认 `false`（一次性返回整轮结果），加 `--stream` 后为 `true`（SSE 长连接增量接收）。会话 ID 的取值按以下优先级确定：

1. `--session-id <id>` 显式指定（跨对话续聊、切回旧任务线）；
2. `--new-session` 强制新开一条任务线（CLI 生成新 ID，旧线保留在台账可切回）；
3. `--resume-last` 从台账兜底找回；
4. 都不传：**同一对话作用域内自动续聊**——CLI 自动识别宿主注入的对话 ID（WorkBuddy 内即当前对话、整条对话稳定），该对话最近 12 小时内用过的会话自动续用（`session_source=conversation_session`）；12 小时未活动或无法确定作用域（终端裸用）时新开对话。

对话作用域键默认自动获取，一般无需显式传 `--conversation-key`；台账按「平台+项目+对话作用域」分组保存每条对话用过的会话线（LRU 最多 20 条），**不同 WorkBuddy 对话天然隔离，不会串会话**。

## 会话纪律（强制）

**默认动作是不传任何会话参数**——同一条 WorkBuddy 对话里，CLI 自动续用该对话最近用过的会话，调用方不需要（也不应该）手工管理会话 ID。只在下表的特定场景才传参数：

| 场景 | 动作 |
|---|---|
| 同一对话内继续当前任务（追问、下钻、补口径、**超时后重试**） | **什么都不传**，自动续聊 |
| 同一对话内换话题 / 开新任务线 | `--new-session`（旧任务线保留，可随时切回） |
| 切回本对话的旧任务线 | 先 `sensors ai sessions list` 拿 ID，再 `--session-id <id>` |
| 跨对话续聊（另一条 WorkBuddy 对话接手旧任务） | 在旧对话输出或 `sensors ai sessions list --all-conversations` 拿 ID，再 `--session-id <id>` |
| 台账兜底（对话上下文丢失） | `--resume-last`（取回后转为自动续聊） |

补充规则：

- **重试必须落在同一条会话线上**：`403` / `timeout` 后重发时不传参数（同对话自动续聊命中同一条线）；如果中间发生过 `--new-session` 导致自动续聊命中的不是目标线，则显式带原 `--session-id`。**永远不要把「换 ID 再试」当排障手段**。
- **禁止自造 ID**（如自己 `uuid4()`）：服务端不认识它，会把排障带偏。只会用 CLI 回传或 `ai sessions list` 列出的值。
- **核对分叉**：每一轮输出都带 `data.session_id` 与 `data.session_source`。发现本该续聊的轮次出现 `new_session`，说明会话分叉了（常见原因：换了宿主对话、超过 12 小时窗口），按上表重新认领或新开。
- 拿不到可用会话时的标准动作是**停下来向用户报告**，而不是反复重试或凭空换 ID。

## 长任务与进度可见性（--stream）

默认非流式：服务端把整轮跑完才回包，**客户端在进程退出前拿不到任何中间信息**。预测、归因、大盘生成这类任务可能要跑几分钟，期间表现为「长时间无返回」——上层若靠「再发一轮问进度」来获取信息，那一轮的答复是独立的一段新文本，与原答复天然接不上。

加 `--stream` 后走 SSE 长连接，解决的是「等待不可观测」与「总时长被掐断」两件事：

- **输出契约不变**：stdout 仍只有一份完整 JSON（`reply` / `sections` 思考过程 / `cards` 与非流式完全一致），只是数据是增量收全的；`data.stream=true`、`data.frames`（收到的帧数）、`data.elapsed_s`（本轮耗时）为流式专属字段。
- **超时语义变为「空闲超时」**：`--timeout`不再是整轮总时长上限，而是**相邻两帧的最大间隔**。只要服务端还在出帧（含工具调用、思考过程），任务就不会被判超时。仍建议保持默认 1800，不要调小——单次工具调用内部可能静默 20 秒以上（实测知识检索静默 24 秒）。
- **进度可见性靠显式开关**：`--progress` 把进度行写 stderr，`--progress-file <path>` 追加写文件（逐行 flush，**宿主可在命令运行期间 tail 读取**）。两个都不开则不产生任何额外输出，stdout/stderr 保持干净契约。
- **进度行的粒度是工具边界级**：`会话已建立` → `SKILL <加载的技能>` → `TOOL_CALL <命令摘要>` → `开始输出答案` → `任务结束`。REPLY 帧是逐词到达的（一轮可几十帧），只报告首帧，避免刷屏。
- **不含连续心跳**：单次工具调用内部无帧可报，那段静默仍然存在，只是被两侧的工具帧框住了。
- 服务端若未按流式返回（Content-Type 不是 event-stream），CLI 自动回退到非流式解析，输出照旧，`data.frames` 为 0——调用方无需分支处理。
- `--stream` 下 `data.http.raw_body` 恒为 null（长连接不缓冲原始响应体），响应头级诊断仍然可用。

进度只走 stderr 或进度文件，**绝不进 stdout**；未显式开开关时不要假设有进度输出。

## 输出

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `CONTENT` | positional | yes | — | **用户原始请求文本**：不改写、不翻译、不摘要 |
| `--session-id` | string | no | 自动 | 显式指定要使用的会话 ID（跨对话续聊、切回旧任务线时用），同时带请求体字段与 `X-Sai-Session-Id` 请求头。与 `--new-session` / `--resume-last` 互斥 |
| `--new-session` | flag | no | false | 强制新开一条任务线；旧线保留在台账，可 `sessions list` 找回后 `--session-id` 切回。与 `--session-id` / `--resume-last` 互斥 |
| `--conversation-key` | string | no | 宿主对话 ID | 对话作用域键；缺省自动取宿主注入的对话 ID，**一般无需显式传入** |
| `--resume-last` | flag | no | false | 仅兜底：从台账取当前作用域最近一次会话续用。与 `--session-id` / `--new-session` 互斥 |
| `--stream` | flag | no | false | 走 SSE 长连接增量接收（仅本接口支持）。stdout 契约不变；`--timeout` 变为相邻帧空闲上限；进度需另开 `--progress` / `--progress-file` |
| `--progress` | flag | no | false | 流式下把进度行（`[progress]` 前缀）写 stderr；stdout 仍只有一份最终 JSON。未开 `--stream` 时无效 |
| `--progress-file` | string | no | — | 流式下把进度行追加写入该文件（逐行 flush，便于宿主运行期间 tail）。与 `--progress` 可同时用 |
| `--execution-mode` | enum | no | `review` | `review` 等待人工确认；`autonomous` 自主执行（**仅用户明确要求时**） |
| `--thinking-mode` | enum | no | `standard` | Plan 思考模式：`standard` / `deep`（深度思考，更慢） |
| `--skills` | string[] | no | — | 优先参考的 skill 名，可重复；先 `sensors ai resources` 确认 |
| `--sub-agent-name` | string | no | — | 优先使用的 subagent；同上 |
| `--message-id` | string | no | 服务端生成 | 消息 ID |
| `--session-hidden` | flag | no | false | 创建隐藏会话 |
| `--cron-task` | flag | no | false | 按定时任务对话模式执行 |
| `--do-not-remember` | flag | no | false | 本轮不写入长期记忆 |
| `--include-raw` | flag | no | false | 在 `data.raw` 保留服务端原始响应（已解包的 data 部分） |
| `--include-http` | flag | no | false | 在 `data.http` 输出 HTTP 级诊断（状态码 / 响应头 / 服务端原始响应体），用于核对会话 ID 的实际位置；**复用同一次请求，不额外调用** |
| `--timeout` | int | no | 1800 | 秒；AI 对话非流式同步等待整个任务跑完，复杂分析常需数分钟，默认 30 分钟。**不要为省时间调小**——超时只说明客户端不再等待，服务端任务仍在执行 |
| `--format` | enum | no | `json` | `json` / `pretty`（无 text 渲染模式） |

## 输出字段（data）

| 字段 | 说明 |
|---|---|
| `session_id` | 本轮实际使用的会话 ID |
| `session_source` | 会话来源：`conversation_session`（同对话自动续用，**默认路径**）/ `reused_session`（调用方显式传入）/ `resumed_session`（`--resume-last` 读台账兜底）/ `new_session`（新开会话线）。**发现本该续聊的轮次出现 `new_session`，说明会话分叉** |
| `requested_session_id` | 仅当 `session_id` 与本次请求发送的 ID 不一致时出现：本次请求实际发送的 ID，用于核对续聊是否命中同一会话 |
| `hint` | 下一步会话动作提示（自然语言），指导调用方下一轮该传什么参数；**按 hint 执行即可，无需自行推导** |
| `stream` | 仅 `--stream` 时出现：`true`（本轮走了长连接） |
| `frames` | 仅 `--stream` 时出现：收到的 SSE 帧数；服务端回退非流式时为 `0` |
| `elapsed_s` | 仅 `--stream` 时出现：本轮耗时秒数 |
| `message_id` | 本轮消息 ID |
| `reply` | **最终答复正文，向用户汇报以此为准** |
| `sections` | dict[str, list]：按 chunk 类型分组的过程信息（执行计划、思考过程等），仅作进展说明 |
| `cards` | 结构化卡片内容 |
| `http` | 仅 `--include-http` 时出现：`status_code` / `response_headers` / `session_id`（响应头或信封中的 ID）/ `envelope_session_id` / `raw_body`（超长时截断并附 `raw_body_truncated`） |

`sensors ai sessions list` 输出当前对话作用域内用过的会话线（按最近使用倒序，最多 20 条，含 `session_id` / `snippet` / `updated_at`）；`--all-conversations` 跨对话列出（每条另带 `project_key` / `conversation_key`），用于跨对话认领旧任务线。

## 示例

```bash
# 首轮 & 同对话内追问/超时重试：什么都不传，自动续聊
sensors ai chat "分析最近 7 天新用户激活率下降的可能原因"
sensors ai chat "按渠道拆开看看"
sensors ai chat "请同步当前进展"

# 同一对话内换话题：--new-session 开新任务线（旧线保留）
sensors ai chat --new-session "换个问题：看看本月留存"

# 切回本对话的旧任务线：先列出，再认领
sensors ai sessions list
sensors ai chat --session-id 3f9c1a7b2d40 "回到激活率那个任务，再深挖一层"

# 跨对话续聊：在旧对话输出或全量列表里拿 ID
sensors ai sessions list --all-conversations

# 长任务（预测/归因/大盘生成）：流式 + 进度落盘，宿主可 tail 进度文件看进展
sensors ai chat --stream --progress-file /tmp/sensors-ai-progress.log "预测下月各渠道转化率"

# 查看可用 skills / subagents（传 --skills 前必做）
sensors ai resources --resource all

# 深度思考 + 指定 skill（同对话内自动续聊，无需会话参数）
sensors ai chat --thinking-mode deep --skills funnel-analysis "……"
```

## 错误

| 现象 | 含义 | 恢复 |
|---|---|---|
| `SensorsConfigError`（org_id） | AI OpenAPI 缺组织 ID | `sensors config init --org-id <ORG>` 或 `--org-id` 覆盖 |
| HTTP 401 | 认证失败 | 核对 API Key / Project / Org ID，重新 `sensors connector auth` |
| HTTP 403 | 无 AI 权限，也可能是服务端瞬时限流/容量波动 | **先按瞬时故障处理**：不传参数重发（同对话自动续聊命中同一条线）；持续失败再找管理员核查权限 |
| HTTP 404 / 405 | 服务端未开放或版本不兼容（瞬时不可用也会出现） | 确认 base_url 与 ai-server 版本，必要时稍后重试 |
| `[TIMEOUT]` | 非流式：整轮等待超过 `--timeout`；流式：**相邻两帧间隔**超过 `--timeout`（空闲超时） | 报错信息里带本次 `session_id`；**不传参数发「请同步当前进展」自动续聊同一条线，不要重新提交需求**；若该对话中间已开过别的任务线，则显式带原 `--session-id`。长任务优先改用 `--stream`，避免总时长判定 |
| 同一会话反复失败（403/404 持续、重试无效） | 该会话可能已在服务端失效 | `--new-session` 另开一条会话线继续任务，并在汇报里说明发生了新会话 |

## 边界

- AI 对话可能创建神策侧资产（分群/标签/报告）：汇报时提醒用户到平台确认，不要宣称"已创建成功"。
- 内部业务能力标识（如 `analytic_agent`、`horizon_segment_agent`）会被拒绝，不要尝试。
- 链路 A 不能替代写操作的确认流程。
- 自动续聊的 12 小时窗口与对话作用域都依赖 sensors-cli ≥ 2.0.1；SSE 流式依赖 ≥ 2.0.3（未传 `--stream` 时行为与旧版一致）。
