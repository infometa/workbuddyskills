# agent

运行画布 Agent 任务。当前稳定入口是 `agent session create`，其它 session/SSE 操作是否可用以后续版本为准。

## 用法

```text
reelmate agent session create NAME [--canvas CANVAS_ID]
reelmate agent session list [--canvas CANVAS_ID]
reelmate agent session delete SESSION_ID [--canvas CANVAS_ID]
reelmate agent enter SESSION_ID
reelmate agent exit SESSION_ID
reelmate agent run SESSION_ID [--follow]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate agent session create NAME` | 创建 Agent task/session |
| `reelmate agent session list` | 查询 session 列表 |
| `reelmate agent session delete SESSION_ID` | 删除 session |
| `reelmate agent enter SESSION_ID` | 进入 session |
| `reelmate agent exit SESSION_ID` | 退出 session |
| `reelmate agent run SESSION_ID` | 执行 session 并可持续消费事件 |

## `reelmate agent session create NAME`

### 作用

创建 Agent task/session。

### 参数

- `NAME`（必填）：任务名称。
- `--canvas CANVAS_ID`：画布上下文。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--json`：输出 JSON。

### 输出

返回创建的 task/session 标识和摘要。

### 示例

```bash
reelmate agent session create planning --canvas CANVAS_ID --json
```

## `reelmate agent session list`

### 作用

查询 session 列表。

### 参数

- `--canvas CANVAS_ID`、`--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--json`：输出 JSON。

### 输出

成功时返回 session/task 数据；当前部署不支持的操作会返回明确的不可用错误，不会伪造成功。

### 示例

```bash
reelmate agent session list --canvas CANVAS_ID --json
```

## `reelmate agent session delete`

### 作用

删除 session。

### 参数

- `SESSION_ID`：session 标识，来自创建或查询结果。
- `--canvas CANVAS_ID`、`--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--json`：输出 JSON。

### 输出

成功时返回删除结果；当前部署不支持的操作会返回明确的不可用错误，不会伪造成功。

### 示例

```bash
reelmate agent session delete SESSION_ID --canvas CANVAS_ID --json
```

## `reelmate agent enter`

### 作用

进入 session。

### 参数

- `SESSION_ID`：session 标识，来自创建或查询结果。
- `--json`：输出 JSON。

### 输出

成功时返回 session 数据；当前部署不支持的操作会返回明确的不可用错误，不会伪造成功。

### 示例

```bash
reelmate agent enter SESSION_ID --json
```

## `reelmate agent exit`

### 作用

退出 session。

### 参数

- `SESSION_ID`：session 标识，来自创建或查询结果。
- `--json`：输出 JSON。

### 输出

成功时返回退出结果；当前部署不支持的操作会返回明确的不可用错误，不会伪造成功。

### 示例

```bash
reelmate agent exit SESSION_ID --json
```

## `reelmate agent run`

### 作用

执行 session 并可持续消费事件。

### 参数

- `SESSION_ID`：session 标识，来自创建或查询结果。
- `--follow`、`--timeout DURATION`、`--ndjson`：运行时持续消费、超时和输出格式。

### 输出

成功时返回 session/task 数据或 SSE 终态；当前部署不支持的操作会返回明确的不可用错误，不会伪造成功。

### 示例

```bash
reelmate agent run SESSION_ID --follow --ndjson
```

## 注意事项

- `NAME` 不是系统 ID；后续操作使用返回的 session/task ID。
- Agent 命令需要有效的空间作用域；已绑定工作区时可省略 `--workspace`。
