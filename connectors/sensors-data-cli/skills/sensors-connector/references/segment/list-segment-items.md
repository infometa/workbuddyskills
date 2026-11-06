# segment.item-list 分群结果包列表

> 工具 `segment.item-list` · 命令 `sensors segment item-list` · 类型 查询

## 用途

列出分群的历史计算结果包，返回每批的 `base_time` / `segment_ready` / `count`。
这是**不依赖 SQL** 获取分群人数的官方途径：既不用猜分群视图表名，也不受历史批次累积
影响（同一视图里多天批次并存时 `count(*)` 会翻倍）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user` | `user` |
| `--name` | string | 是 | — | 分群定义机器名 | `active_user_7_days` |
| `--limit` | int ≥1 | 否 | 20 | 返回条数上限；CLI 按 base_time 的实际时间倒序排列后截断 | `5` |
| `--base-time` | string（可重复） | 否 | — | 只取指定基准时间的结果包，服务端按天等值匹配 | `2026-10-26T00:00:00+08:00` |
| `--ready-only` | flag | 否 | 关 | 只返回已生成完成的结果包 | `—` |
| `--not-ready` | flag | 否 | 关 | 只返回尚未生成完成的结果包；与 `--ready-only` 互斥 | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

```bash
sensors segment item-list --ai-session-id <ai_session_id> --entity-name 'user' \
  --name "<segment_name>" --ready-only --limit 5 --format json
```

## 输入 Schema

无 `--input` JSON；查询条件通过 flag 表达。`--dry-run` 打印的请求体字段：

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `entity_name` | string | 实体名称 | `user` |
| `definition_name` | string | 分群定义机器名 | `active_user_7_days` |
| `limit` | int | 返回条数上限（服务端必填） | `20` |
| `base_time_list` | string[] | `--base-time` 列表（未提供时省略） | `["2026-10-26T00:00:00+08:00"]` |
| `segment_ready` | bool | `--ready-only` 传 true、`--not-ready` 传 false，都不给则省略 | `true` |

以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 构造流程

1. 取分群机器名：`segment.list` 返回的 `name`，作为 `--name`。
2. 定范围：默认倒序取最新 `--limit` 条；只看某个批次时加 `--base-time`（服务端按天等值匹配）。
3. 定过滤：只关心已产出的结果包加 `--ready-only`；排查「算了但没结果」加 `--not-ready`。
4. 取人数直接读 `items[0].count`，不再查库。

```bash
sensors segment item-list --ai-session-id <ai_session_id> --entity-name 'user' \
  --name "<segment_name>" --ready-only --limit 5 --format json
```

## 输出

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `items[]` | 结果包列表，按基准时间倒序 | `—` |
| `items[].base_time` | 批次基准时间（服务端按天落库值） | `2026-10-26T00:00:00+08:00` |
| `items[].segment_ready` | 结果包是否生成完成 | `true` |
| `items[].count` | 该批次分群人数 | `337` |
| `items[].create_time` | 批次创建时间 | `2026-10-26T10:27:01Z` |
| `items[].segment_ready_time` | 结果包就绪时间 | `2026-10-26T10:27:51Z` |
| `items[].segment_name` | 结果包名称 | `user_seg_1_1792944000000` |
| `total` | 返回条数 | `2` |

结构性解读：

- `items[0]` 是最新批次；`items[0].count` 就是当前分群规模。
- 多个 `items` 里 `count` 相同而 `base_time` 不同，说明不同批次算出同样的人（正常）；
  SQL 侧对同一视图做 `count(*)` 会把这些批次加总。查询单批次人数应限定目标基准时间，
  或直接用本命令；跨批次去重不能替代单批次口径。
- `segment_ready=false` 表示该批次还没产出结果包，`count` 不可信。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：`--ready-only` 与 `--not-ready` 不能同时使用 | 两个 flag 同时给 | 只保留一个 |
| 分群不存在 / 无权限 | 名称无匹配或权限不足 | 核对机器名（先用 `segment.list`） |
| 认证错误 | api_key / 项目无效 | 停止执行，返回修复提示 |

## 使用约束

- 纯只读查询。
- 人数口径以本命令为准；不要再用 `SELECT count(*) FROM user_group_<分群名>` 佐证，
  那个值会被历史批次放大。
