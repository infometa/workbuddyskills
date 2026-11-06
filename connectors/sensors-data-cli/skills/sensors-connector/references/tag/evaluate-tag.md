# tag.evaluate 触发标签计算

> 工具 `tag.evaluate` · 命令 `sensors tag evaluate` · 类型 写入（触发计算）

## 用途

触发一个或多个标签定义的计算，默认分别等待任务进入终态。304 服务端只接受同一定义的任务，CLI 将输入拆成单项请求，逐项触发并等待；本命令不修改标签定义。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 标签所属实体 | `user` |
| `--input` | string | 是 | — | 内联 JSON 数组/对象、文件路径或 `-`（stdin） | `params.json` |
| `--server-timezone` | string | 否 | 本机时区 | 服务端 JVM 的 IANA 时区；本机与部署不同时必须指定 | `Asia/Shanghai` |
| `--no-wait` | flag | 否 | 关 | 仅触发，不等待终态 | `—` |
| `--poll-timeout` | int ≥1 | 否 | 3600 | 每项轮询等待上限秒数，与 HTTP `--timeout` 独立 | `600` |
| `--dry-run` | flag | 否 | 关 | 打印所有待发送的请求，不访问服务端 | `—` |

全局参数：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填，dry-run 豁免）。

```bash
sensors tag evaluate --ai-session-id <ai_session_id> --entity-name user \
  --server-timezone Asia/Shanghai --input '[{"tag_definition_name":"<tag_name>"}]'
```

## 输入 Schema

支持参数数组或 `{"evaluate_params": [...]}` 对象。

```json
[{"tag_definition_name": "<标签机器名>", "base_time": "2026-10-25T16:00:00Z"}]
```

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `evaluate_params[].tag_definition_name` | string | 是 | 标签定义机器名；由列表查询确认 | `user_tag_1` |
| `evaluate_params[].base_time` | string | 否 | 带时区的 RFC 3339 时间；省略时取服务端今天零点 | `2026-10-26T00:00:00+08:00` |
| `evaluate_params[].tag_task_params` | object | 否 | 服务端支持的任务参数 | `—` |

CLI 先将时间转换到 `--server-timezone`，再按天截断，并以同一值轮询。服务端为 Asia/Shanghai 时，`2026-10-25T16:00:00Z` 与 `2026-10-26T00:00:00+08:00` 是同一批次；不能先把 UTC 时分秒清零。

同一标签、同一归一化基准时间、相同参数只触发一次；同一批次存在不同任务参数时报入参错误。dry-run 单项输出一个请求对象，多项输出请求数组。

## 构造流程

1. 先用 `tag.list` 确认标签机器名与所属实体。
2. 将每个目标写入参数数组；历史批次显式提供带时区的基准时间，并核对服务端时区。
3. 先预览待发送的单项请求；默认逐项等待，确实只需触发时使用 `--no-wait`。

```bash
sensors tag evaluate --entity-name user --server-timezone Asia/Shanghai \
  --input '[{"tag_definition_name":"user_tag_1","base_time":"2026-10-25T16:00:00Z"}]' --dry-run
```

## 输出

默认等待模式返回合并的 `tasks[]`：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `tasks[].status` | 过程态 TAG_PREPARING / TAG_WAITING_DATA / TAG_COMPUTING，终态 TAG_SUCCESS / TAG_FAILED / TAG_TASK_CANCELLED | `TAG_SUCCESS` |
| `tasks[].tag_definition_name` | 标签定义名（查询请求使用 tag_name，任务响应字段为 tag_definition_name） | `user_tag_1` |
| `tasks[].base_time` | 实际基准时间 | `2026-10-25T16:00:00Z` |

每项每 5 秒轮询一次；连续 6 次空任务会提前报错，并提示核对基准时间与服务端时区。所有项均计算成功才正常退出。

`--no-wait` 单项保留服务端触发响应；多项返回 `results[]`，每项含标签名、基准时间及 `response`。触发成功不代表计算完成。

部分失败使用统一工作流错误：`stage=tag.evaluate`、非零退出码，`data` 保留 `tasks[]`、`failed[]`（触发失败）、`poll_errors[]`（查询失败）；`--no-wait` 的已成功提交项保留在 `results[]`。错误体的 `partial_success` 表示是否有已确认成功项。可用的错误码、`request_id` 与 hint 会保留。HTTP 触发超时或传输异常项带 `outcome_unknown=true`，应先确认任务状态，避免重复提交。

网络异常以 `code=network` 记录在 `failed[]` 或 `poll_errors[]`，保留其他项结果并继续处理，不自动重试异常项；查询异常不标记为未知提交。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError | 无参数列表、元素不是对象、时间缺时区/格式错误、时区无效或同批次参数冲突 | 修正输入后重新预览 |
| 连续空任务 | 基准时间与服务端落库时间点不一致等 | 核对服务端 JVM 时区及归一化请求；不要仅延长 HTTP 超时 |
| 轮询超时 | 每项等待超过 `--poll-timeout` | 查询现有任务状态；必要时延长轮询上限 |
| TAG_FAILED / TAG_TASK_CANCELLED | 计算失败或取消 | 命令非零退出，保留各项任务状态；不能报告全部成功 |
| 不存在 / 无权限 | 机器名或权限无效 | 核对目标及权限；保留其他项已完成结果 |

本命令会产生真实计算任务，不能用重复 evaluate 验证已有结果。定义创建/更新成功与计算成功应分别报告。
