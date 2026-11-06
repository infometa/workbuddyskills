# segment.evaluate 触发分群计算

> 工具 `segment.evaluate` · 命令 `sensors segment evaluate` · 类型 写入（触发计算）

## 用途

触发分群定义的计算，并默认同步等待任务进入终态。一次可提交多个定义——服务端只接受
单定义请求，CLI 会自动拆成多次调用并逐项等待。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user`（用户分群）或其他已注册实体 | `user` |
| `--input` | string | 是 | — | JSON 输入；支持**内联 JSON 数组/对象**、文件路径、`-` 从 stdin 读 | `[{"segment_definition_name":"seg_a"}]` |
| `--base-time` | string | 否 | — | 计算基准时间，覆盖输入里每一项的 `base_time`；只支持天粒度，会归一到当天 00:00 | `2026-10-26T00:00:00+08:00` |
| `--server-timezone` | string | 否 | 本机时区 | 服务端 JVM 的 IANA 时区，本机与部署不同时必须指定 | `Asia/Shanghai` |
| `--no-wait` | flag | 否 | 关 | 触发后立即返回，不轮询等待任务完成 | `—` |
| `--poll-timeout` | int ≥1 | 否 | 3600 | 每项轮询等待上限秒数；与单次 HTTP `--timeout` 独立 | `—` |
| `--dry-run` | flag | 否 | 关 | 仅打印将要发出的请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例：

```bash
sensors segment evaluate --ai-session-id <ai_session_id> --entity-name 'user' \
  --input '[{"segment_definition_name": "<segment_name>"}]' --format json
```

## 输入 Schema

`--input` 支持两种等价形状（内联时注意 shell 引号）：

```json
[{"segment_definition_name": "<分群机器名>", "base_time": "<RFC 3339，可省略>"}]
```

```json
{"evaluate_params": [{"segment_definition_name": "<分群机器名>"}]}
```

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `evaluate_params[].segment_definition_name` | string | 是 | 目标分群定义机器名 | `active_user_7_days` |
| `evaluate_params[].base_time` | string | 否 | 计算基准时间（RFC 3339）；省略时取服务端时区当天 00:00 | `2026-10-26T00:00:00+08:00` |

同一 `（分群名, base_time）` 组合和相同参数只触发一次；同一批次参数不同则报入参错误。

## 服务端约束（决定了命令行为）

1. **一次请求只能带一个分群定义**。OpenAPI 层与 gRPC 层各拦一次，传多个会返回
   `Invalid field: evaluate_params must target one segment definition`。
   因此 `--input` 里 N 个定义 = CLI 发出 N 次单定义请求，逐个等待，不并发。
2. **`base_time` 只支持天粒度**。CLI 先转换到 `--server-timezone` 指定的服务端
   JVM 时区，再截断到当天零点，并用同一时间点轮询；默认使用本机时区，须与部署一致。
3. RFC 3339 偏移只表示时间点，不代表服务端时区。服务端为 Asia/Shanghai 时，
   `2026-10-25T16:00:00Z` 等价于 `2026-10-26T00:00:00+08:00`，不能先截成 UTC 零点。

## 构造流程

1. 定位目标分群：机器名取自 `segment.list` 返回的 `name`（只知显示名先列出匹配候选）。
2. 组装 `--input`：单定义传 `[{"segment_definition_name":"<机器名>"}]`；多定义逐项追加；
   需复现历史口径时显式提供 `base_time`。
3. 选择等待模式：默认同步等待终态；不需要等结果时加 `--no-wait`；预计耗时长的任务
   调大 `--poll-timeout`。

```bash
sensors segment evaluate --ai-session-id <ai_session_id> --entity-name 'user' \
  --input '[{"segment_definition_name":"seg_a","base_time":"2026-10-26T00:00:00+08:00"}]' --format json
```

## 输出

同步等待模式（默认）：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `results[]` | 每个分群一行汇总 | `—` |
| `results[].segment_definition_name` | 分群定义名 | `active_user_7_days` |
| `results[].base_time` | 实际基准时间（服务端按天落库后的值） | `2026-10-26T00:00:00+08:00` |
| `results[].segment_task_status` | 终态：`SEGMENT_TASK_SUCCESS` / `_FAILED` / `_CANCELLED` | `SEGMENT_TASK_SUCCESS` |
| `results[].success` | 是否计算成功 | `true` |
| `results[].count` | 分群人数（取自结果包，结果包未产出时缺省） | `337` |
| `results[].segment_ready` | 结果包是否生成完成 | `true` |
| `results[].task_id` | 任务 ID | `199719` |
| `results[].failure_detail` | 失败任务的错误码与原因 | `{"code":"…","error_message":"…"}` |
| `tasks[]` | 合并后的原始任务列表 | `—` |
| `partial_success` | 是否全部成功 | `true` |

`--no-wait` 模式：`results[]` 为各定义的触发结果（含服务端响应），不含任务状态。

结构性解读：

- 任务状态取值来自服务端枚举 `SEGMENT_TASK_*`，`SEGMENT_TASK_PREPARING` /
  `_WAITING_DATA` / `_COMPUTING` 是过程态；`_SUCCESS` / `_FAILED` / `_CANCELLED` 是终态。
- HTTP 触发超时或传输异常项带 `outcome_unknown=true`；先查询已有任务，避免直接重试产生重复计算。
- 网络异常以 `code=network` 记录在 `failed[]`（提交）或 `poll_errors[]`（查询），保留其他项结果并继续处理；不自动重试异常项。可选人数查询失败时保留成功任务，省略未知人数。
- 任一任务失败、或任一触发请求失败，命令以非零退出码结束，错误体里带 `partial_success`
  与 `results[]` / `failed[]` / `poll_errors[]`，可据此区分「全失败」与「部分成功」。
- 人数以结果包为准：任务报表的 `count` 可能未填充，不能把默认 0 当作真实人数。
- 轮询每 5 秒一次；连续 6 次拿到空任务列表即判定为查询口径不匹配并立即报错，不会静默
  等到 `--poll-timeout`。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：必须提供 `evaluate_params` 列表 | 输入为空数组或对象中无该键 | 提供至少一项含 `segment_definition_name` 的参数 |
| UsageError：`evaluate_params` 校验失败 | 某项缺少 `segment_definition_name`，或 `base_time` 非 RFC 3339 | 按错误修正对应项 |
| `连续 N 次返回空结果` | 轮询查不到任务：几乎总是 `base_time` 日期/精度与服务端落库值不一致 | 用 `segment task-get --base-time <值>` 核对落库日期；跨时区时显式给服务端当天 00:00 |
| 轮询超时 | 超过 `--poll-timeout` 秒仍未终态 | 增大 `--poll-timeout`，或改用 `--no-wait` 后用 `segment task-get` 查询 |
| 任务 `SEGMENT_TASK_FAILED` / `_CANCELLED` | 计算本身失败或被取消 | 读 `failure_detail`；这是任务终态，命令以非零退出码表达 |
| 分群不存在 / 无权限 | 名称无匹配或权限不足 | 核对机器名（先用 `segment.list`），权限问题停止并返回修复提示 |

## 使用约束

- 本命令触发真实计算（非 `--dry-run`），触发即产生新的计算任务与新的结果包。
- **手动重算不清理历史分区**：通过 OpenAPI 触发的重算会在分群结果视图里按 `base_time`
  累积批次（平台 UI 手动重算会先清掉其他分区，OpenAPI 不会）。因此
  跨批次直接统计视图行数可能重复计算。取人数请用 `sensors segment item-list` 的
  `count`；SQL 需先确认实际库表列，并限定目标批次，不能跨批次去重来替代单批次口径。
- 确认结果状态优先用 `segment task-get`（任务）与 `segment item-list`（结果包人数），
  而不是再触发一次 evaluate。
- 计算语义：`trigger_type=MANUAL` 的分群不自动计算，需本命令触发；`CRON` / `PERIODIC`
  由平台按调度自动计算。本命令只产生新结果，不修改分群定义。
