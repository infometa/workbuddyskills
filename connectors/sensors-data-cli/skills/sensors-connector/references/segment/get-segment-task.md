# segment.task-get 分群任务状态

> 工具 `segment.task-get` · 命令 `sensors segment task-get` · 类型 查询

## 用途

查询分群计算任务的状态、基准时间与失败原因。用于确认「任务到底建了没有、算成没算成」，
可配合 `segment.item-list` 核对基准时间；同步等待异常时用于独立查询任务。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user` | `user` |
| `--name` | string | 是 | — | 分群定义机器名 | `active_user_7_days` |
| `--base-time` | string（可重复） | 否 | 今天 00:00（本机时区） | 计算基准时间；服务端按此值**等值匹配**，且落库时按天截断 | `2026-10-26T00:00:00+08:00` |
| `--fetch-all` | flag | 否 | 关 | 返回该基准时间下的全部任务，默认只返回最新一条 | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

```bash
sensors segment task-get --ai-session-id <ai_session_id> --entity-name 'user' \
  --name "<segment_name>" --base-time 2026-10-26T00:00:00+08:00 --format json
```

## 输入 Schema

无 `--input` JSON；查询条件通过 flag 表达。`--dry-run` 打印的请求体字段：

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `entity_name` | string | 实体名称 | `user` |
| `definition_name` | string | 分群定义机器名 | `active_user_7_days` |
| `base_time_list` | string[] | `--base-time` 列表（RFC 3339，服务端按天等值匹配）；缺省为今天 00:00 | `["2026-10-26T00:00:00+08:00"]` |
| `fetch_all` | bool | `--fetch-all` 时传 true，否则省略 | `true` |

以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 构造流程

1. 取分群机器名：`segment.list` 返回的 `name`，作为 `--name`。
2. 定基准时间：默认今天 00:00（本机时区）。查历史批次时显式传 `--base-time`，值必须是
   服务端落库的当天 00:00；不确定时先用 `segment.item-list` 查看已有批次的 `base_time` 再回填。
3. 需要看同一基准时间下的全部任务（含重算历史）时加 `--fetch-all`。
4. 参数拿不准先 `--dry-run` 预览请求体，确认后再真实执行。

```bash
sensors segment task-get --ai-session-id <ai_session_id> --entity-name 'user' \
  --name "<segment_name>" --base-time 2026-10-26T00:00:00+08:00 --format json
```

## 输出

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `tasks[]` | 任务列表，按基准时间倒序 | `—` |
| `tasks[].id` | 任务 ID | `199719` |
| `tasks[].segment_task_status` | `SEGMENT_TASK_PREPARING` / `_WAITING_DATA` / `_COMPUTING` / `_SUCCESS` / `_FAILED` / `_CANCELLED` | `SEGMENT_TASK_SUCCESS` |
| `tasks[].base_time` | 实际基准时间（服务端按天落库后的值） | `2026-10-26T00:00:00+08:00` |
| `tasks[].failure_detail` | 失败任务的错误码与原因（仅失败时出现） | `{"code":"…","error_message":"…"}` |
| `tasks[].failed_times` | 失败重试次数 | `0` |
| `total` | 任务条数 | `1` |
| `base_time_list` | 本次查询使用的基准时间 | `["2026-10-26T00:00:00+08:00"]` |

结构性解读：

- `tasks` 为空表示「这个基准时间下没有任务」，**不代表任务不存在**。服务端按天截断后
  落库，用秒级时间戳查询必然为空；请改试当天 00:00，再试相邻日期。
- 任务报表的 `count` 可能未填充；默认 0 不输出，正数兼容数字与 protobuf int64 字符串；**分群人数请用
  `segment.item-list` 的结果包 `count`**。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：`--base-time` 需要 RFC 3339 格式 | 传入 `2026/10/26` 之类 | 改成 `2026-10-26T00:00:00+08:00` |
| 分群不存在 / 无权限 | 名称无匹配或权限不足 | 核对机器名（先用 `segment.list`） |
| 认证错误 | api_key / 项目无效 | 停止执行，返回修复提示 |

## 使用约束

- 纯只读查询，可反复调用。
- 跨时区场景下先看 `tasks[].base_time` 的实际值，再用该值重新查询，不要靠猜日期。
