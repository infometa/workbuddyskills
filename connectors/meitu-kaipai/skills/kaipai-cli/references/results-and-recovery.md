# 输出与任务恢复

## 读取输出

同时保留 stdout、stderr 和退出码。普通构建的 `chat / reply / tool` 将 SSE 消息正文、交互内容和产物输出为可读文本，标识与进度可能写入 stderr；非流式响应、任务轮询和 CLI 生成的 `session / end` 仍在 stdout 输出 JSON。同一次调用可能混合文本和 JSON，不要对整段 stdout 直接 `JSON.parse`。完整交互结构可通过 `history-detail` 查询。

常见结构如下，字段以实际返回为准；示例 ID 和地址不是可复用结果。

| 输出 | 关键字段与含义 |
|---|---|
| `type=session` | `session_id / room_id / room_url`：会话信息，保存以便续聊与恢复 |
| `type=execution.accepted`（结构化响应时） | `session_id / run_id / task_id / task_ids`：已受理，尚不证明生成完成，任务集合可能为空 |
| `type=execution.result`（结构化响应时） | `task_ids` 是本次执行的权威任务集合；恰好一个 Task 时 `result.task` 为完整任务，否则为 `result.message` |
| `type=task` | `task.id / task.contextId / task.status / task.artifacts / task.metadata`：当前完整任务 |
| `type=history` | `items / session_status / last_event_id / active_task_ids`：历史消息更新、状态、服务端游标和当前活动任务 |
| `type=end` | `reason` 和已知会话、Run/Task 信息；历史观察另有 `last_event_id` |
| `type=execution.error` | 普通执行错误，提炼 `error.code / error.message`；其他上下文字段仅使用实际提供的值 |
| `type=authentication_required` | 鉴权错误，读取 `error_code / error_msg / action_command`；登录时展示新生成的实际授权链接 |

历史消息以 `messageId` 标识，内容在 `parts` 中，可含文本、媒体和结构化交互。按 `messageId` 替换完整消息，不一律追加，也不要把同一消息中的每个 Data Part 当作独立待办。

任务示例（裁剪后的结构）：

```json
{
  "type": "task",
  "session_id": "s_example",
  "task": {
    "id": "task_example",
    "contextId": "s_example",
    "status": { "state": "TASK_STATE_COMPLETED" },
    "artifacts": [
      {
        "artifactId": "artifact_example",
        "name": "处理结果",
        "parts": [
          {
            "url": "https://cdn.example.com/result.mp4",
            "mediaType": "video/mp4",
            "filename": "result.mp4"
          }
        ]
      }
    ]
  }
}
```

## 完成判定

- `TASK_STATE_SUBMITTED / TASK_STATE_WORKING`：等待或执行中，继续观察。
- `TASK_STATE_COMPLETED`：该任务成功结束，可以交付其实际产物。
- `TASK_STATE_FAILED / TASK_STATE_CANCELED`：失败或取消，读取 `task.status.message` 的实际说明，保留已成功结果。
- 进度来自 `task.metadata["viva.progress"]`（如果返回）；不要编造百分比。

`run_id` 是一次执行标识，不是 Task ID；`session_id` 用于续聊，`task.id` 用于任务查询。按 Task ID 保存全部已知任务。`active_task_ids` 只表示当前活动任务，ID 从中消失后仍需查询其终态，不能因此忘记它。

| `end.reason` | 应如何处理 |
|---|---|
| `result` | 本轮返回 Message、未生成 Task；可能是纯文本结果、澄清或批准请求，读取内容再判断 |
| `completed` | 本次观察的任务全部成功，交付实际产物 |
| `failed / cancelled` | 有任务失败或取消；显式取消成功也返回 `cancelled` |
| `snapshot / update` | 完成一次读取或返回实际更新，仍需结合 Task 状态 |
| `idle` | 会话空闲且本次观察到的任务结束；不能证明未观察到的先前执行成功 |
| `detached` | 本地分离退出，继续只读观察 |
| `interrupted` | 本地等待被中断，远端任务未被取消 |
| `error` | 提交或观察出错，不代表远端任务已终止 |

退出码 `0` 包含快照、更新、分离退出等情况，不能单独当作生成成功。任务失败/取消及请求错误通常为 `1`，Ctrl+C 为 `130`；显式 `cancel` 成功为 `0`。

## 连续观察与中断恢复

正常情况下让原 `chat / reply / tool` 命令继续运行，它会观察本次全部任务。断线、超时或使用 `--detach` 后：

1. **已有会话和 Task ID**：用 `task-progress -r '<session_id>' --task-id '<task_1>' '<task_2>' --watch` 观察全部已知任务。
2. **会话已知，但 Task ID 未知或需读取交互**：用 `history-detail -r '<session_id>' --watch --yield-on-update` 获取更新。保存返回的 `last_event_id`，后续串行调用时加 `--last-event-id '<返回游标>'`，同时保留之前发现的 Task ID。
3. **尚未取得会话**：先用 `history --limit 10`，必要时分页，根据实际会话内容定位本次执行；不凭空选择其他会话，也不直接重新提交。无法确定归属时说明未知状态，向用户确认目标会话。
4. **结束当前观察**：Ctrl+C 只停止本地等待。用户明确要求取消时执行 `cancel` 并查询；不要通过杀掉本地进程宣称远端已取消。

查询结束仍有已知任务未终结时继续查询；需要用户输入或请求持续失败时保存恢复信息并说明下一步。不要同时为同一任务开启多个观察命令。只读查询的网络退避由 CLI 处理；退出后按实际错误恢复，避免无界循环。

HTTP 200、响应头中的会话 ID、SSE EOF 或历史 idle 都不能证明一次未知提交已完成。Chat POST 不自动重试，也不保证重复请求幂等。

## 澄清与批准

- 普通文本追问用同一会话的 `chat -p` 回复。
- 结构化问询从当前消息读取字段、选项和约束，使用 `reply --answer '<JSON 对象>'`。有图片/视频候选时，先在 WorkBuddy 展示真实预览和文案，再收集用户选择；不代选。
- 批准或拒绝前先读取当前交互，核对用户授权范围，分别使用 `reply --approve` 或 `reply --reject [--reason '<理由>']`。这会恢复会话当前待处理动作，不能指定旧卡片；不盲批历史消息。
- `--answer / --approve / --reject` 三选一。当前交互已变更时重新核对，不能用新的工具提交来代替交互回复。

## 错误恢复

| 情形 | 处理方式 |
|---|---|
| 未登录或授权失效 | 读取 `authentication_required` 或 stderr 的鉴权说明，重新连接/登录后远端复检。明确未受理的请求最多在恢复后重试一次；受理未知时先查任务 |
| 参数、类型、大小或时长不符 | 按实际 `error.code / error.message` 修正；缺少用户输入时询问，不丢弃素材或换成虚构输入 |
| 缺少 `ffprobe`、本地媒体无法读取 | 报告实际依赖或文件问题，修复后再提交；不跳过校验 |
| 内容审核或服务能力拒绝 | 展示实际原因，按用户意图调整合法输入或停止；不改变协议绕过拒绝 |
| 工具不支持、404 或协议解析失败 | 保留实际命令与错误，核对版本和连接状态；不回退旧 A2UI、内部 API 或任意 action |
| 网络、超时、未知提交结果 | 保留会话、全部任务和原始输入，先按上述流程查询；不自动重发生成请求 |
| 已确认 Task 失败 | 交付其他成功产物；仅在用户授权重试后，以原始输入在同一会话发起一次新尝试并记录新 Task ID |
| 权益不足 | 由 Agent 根据真实返回内容判断，执行 `purchase --open` 或 `purchase` 展示 `action_url`；等待用户确认购买完成并授权重试，再核对明确失败的任务 |
| 下载失败或 URL 过期 | 查 `downloaded[].error`，必要时查询 `task-progress` 获取新 URL，仅重新下载失败文件 |

权益购买后的固定工具重试必须保留原工具名和原始源文件/URL，或使用真实、可用且属于原会话的源媒体 ID。不能改用失败结果媒体 ID。普通创作按用户授权在原会话发起新的 `chat`；已有成功结果继续保留。打开购买页不等于购买成功，CLI 不检测付款、不自动续做。

购买页打开失败时，`purchase --open` 已输出的 `action_url` 仍可展示给用户；浏览器错误还可能在 `error.data.action_url` 保留入口，无需反复打开。

普通错误优先读取 `type=execution.error` 的 `error.code / error.message`。鉴权和 `auth` 命令保留原有错误格式；任务失败本身保留在 Task 状态中。下载汇总也需检查 `failed` 和每项 `error`，不要只查事件类型。保留实际错误码，不假定存在某个专用的“权益不足”或“内容审核”码。

## 产物交付与保存

1. 产物入口取自本次 `task.artifacts[].parts[].url`，名称用 Artifact 的 `name` 或 Part 的 `filename`，类型用 `mediaType`。文本输出里实际提供的产物 URL 也及时展示，不把输入素材或旧历史结果当作新产物。
2. 以 `task.id + artifactId` 维护结果，记录已展示的 Part 与 URL；新增 Part 补交，URL 刷新时更新原产物入口，不重复交付同一结果。
3. 优先使用 WorkBuddy 的原生附件、预览或播放器；不可用时提供可点击完整 URL。保留查询参数和所有成功产物入口，不用缩略图或封面代替实际视频，不承诺未返回的格式。
4. 用户要求本地保存时执行 `download --url '<实际产物 URL>' -o '<目标目录>'`，按 `succeeded / failed / downloaded` 核对并提供成功文件。下载不会自动搜集全部历史产物；只传本次需交付的实际 URL。
5. 有成功产物的任务可先交付，其他任务继续观察。最终说明成功与失败部分；返回实际 `room_url` 时再提供开拍会话入口。
