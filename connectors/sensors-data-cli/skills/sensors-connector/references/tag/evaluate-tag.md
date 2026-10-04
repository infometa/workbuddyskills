# tag.evaluate 触发标签计算

> 工具 `tag.evaluate` · 命令 `sensors tag evaluate` · 类型 写入（触发计算）

## 用途

触发一个或多个标签定义的计算，并默认同步等待任务进入终态。用于手动触发（`MANUAL`）标签出值，或按指定 `base_time` 复现历史计算口径；只生成新的标签值结果，不修改标签定义。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user`（用户标签）或其他已注册实体 | `user` |
| `--input` | string | 是 | — | JSON 输入；`-` 从 stdin 读，也可传文件路径；格式为 `evaluate_params` 数组或含 `evaluate_params` 键的对象 | `-` |
| `--no-wait` | flag | 否 | 关 | 触发后立即返回，不轮询等待任务完成 | `—` |
| `--poll-timeout` | int ≥1 | 否 | 3600 | 轮询总等待秒数；与单次 HTTP `--timeout` 独立，超时后抛出错误 | `—` |
| `--dry-run` | flag | 否 | 关 | 仅打印请求 JSON，不发起真实请求，用于调试参数 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例：

```bash
sensors tag evaluate --ai-session-id <ai_session_id> --entity-name 'user' --input '[{"tag_definition_name":"<tag_name>"}]' --format json
sensors tag evaluate --ai-session-id <ai_session_id> --entity-name 'user' --input params.json --no-wait --format json
```

## 输入 Schema

`--input` 支持两种等价形状：

```json
[{"tag_definition_name": "<标签机器名>", "base_time": "<RFC 3339 时间，可省略>"}]
```

```json
{"evaluate_params": [{"tag_definition_name": "<标签机器名>"}]}
```

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `evaluate_params[].tag_definition_name` | string | 是 | 目标标签定义机器名 | `user_tag_1` |
| `evaluate_params[].base_time` | string | 否 | 计算基准时间（RFC 3339）；省略时 CLI 自动填充当前时间（带时区、秒级精度） | `2026-09-27T09:54:41+08:00` |

`--entity-name` 作为整次请求的实体名。以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 构造流程

1. 定位目标标签：机器名取自 `tag.list` 返回的 `name`（只知显示名先列出匹配候选），作为 `--input` 每项的 `tag_definition_name`。
2. 组装 `--input`：单定义传 `[{"tag_definition_name":"<机器名>"}]`；多定义批量触发时逐项追加；需复现历史口径时为对应项显式提供 `base_time`（RFC 3339），省略时 CLI 统一填充触发时刻（带时区、秒级精度）。
3. `--entity-name` 传目标实体（如 `user`），作为整次请求实体名；与标签定义所属实体不一致时以 flag 为准。
4. 等待模式选择：默认同步等待终态；不需要等结果时加 `--no-wait`（返回触发响应，结果另行查询）；预计耗时长的任务可调大 `--poll-timeout`。

```bash
sensors tag evaluate --ai-session-id <ai_session_id> --entity-name 'user' \
  --input '[{"tag_definition_name":"user_tag_<名称>"}]' --format json
```

## 输出

同步等待模式（默认），返回任务状态：

```json
{
  "tasks": [
    {
      "status": "COMPLETED",
      "tag_name": "<tag_name>",
      "base_time": "2026-09-24T10:00:00+08:00"
    }
  ]
}
```

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `tasks[]` | 任务列表 | `—` |
| `tasks[].status` | 任务状态：`PENDING` / `RUNNING` / `COMPLETED` / `FAILED` / `CANCELLED` | `—` |
| `tasks[].tag_name` | 标签定义名 | `user_tag_1` |
| `tasks[].base_time` | 计算基准时间（RFC 3339） | `2026-09-27T09:54:41+08:00` |

结构性解读：

- 状态语义：`PENDING` / `RUNNING` 表示任务仍在执行或排队；`COMPLETED` 表示计算完成；`FAILED` / `CANCELLED` 是任务终态失败或取消——后两者是任务结果而非命令错误，原样传回调用方，不改写为命令失败。
- `--no-wait` 模式：原样返回服务端触发响应（通常包含任务 ID 或确认信息），不包含最终任务状态；需要终态时另行查询或改用默认等待模式。

轮询机制（命令层事实）：触发后每 5 秒轮询一次任务接口，直到所有任务进入终态（`COMPLETED` / `FAILED` / `CANCELLED`）或达到 `--poll-timeout` 上限；多定义批量触发时，轮询查询按第一个 `evaluate_params` 项构造（以 `base_time` 为起始区间），批量任务较多时以逐项状态为准。

计算语义（命令层事实）：`trigger_type=MANUAL`（手动更新）的标签不自动计算，需通过本命令触发；`trigger_type=CRON` / `PERIODIC` 的标签由平台按调度自动计算。本命令只生成新的标签值结果，不修改标签定义。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：必须提供 `evaluate_params` 列表 | 输入为空数组或对象中无该键 | 提供至少一项含 `tag_definition_name` 的参数 |
| UsageError：`evaluate_params` 校验失败 | 某项缺少 `tag_definition_name` 或 `base_time` 非 RFC 3339 | 按错误修正对应项 |
| 轮询超时错误 | 超过 `--poll-timeout` 秒仍未全部终态 | 增大 `--poll-timeout`，或改用 `--no-wait` 后另行查询 |
| 任务 `FAILED` / `CANCELLED` | 计算任务本身失败或被取消 | 是任务终态而非命令错误；原样返回状态，不重写为命令失败 |
| 标签不存在 / 无权限 | 名称无匹配或权限不足 | 核对机器名（先用 `tag.list`），权限问题停止并返回修复提示 |

## 使用约束

- 本命令触发真实计算（非 `--dry-run`），不属于只读查询；触发即产生新的计算任务。
- 重复触发同一定义会生成新的计算任务；`base_time` 决定计算基准，需要复现历史口径时显式提供。
- 触发结果中原样保留任务状态与 `request_id`；是否需要触发由调用方决定。
- 计算触发失败不影响定义本身的存在与有效性：创建/更新成功而 evaluate 失败时，如实分别报告两个结果，不把定义状态改写为失败。
- 确认计算结果状态时用 `tag.get` 回读任务状态与结果可用性，不通过再次 evaluate 验证。
