# segment.valid-check 分群结果包有效性判定

> 工具 `segment.valid-check` · 命令 `sensors segment valid-check` · 类型 查询

## 用途

批量判断若干分群定义「是否已有可用的计算结果包」。响应体里没有 `has_valid_segment`
字段（它只是 list 请求侧的过滤器），因此命令用两次查询做差集：一次按名称全量取回，
一次加上有效过滤，出现在后者里的就是已有可用结果包的分群。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user` | `user` |
| `--names` | string | 是 | — | 待检查的分群机器名，逗号分隔 | `seg_a,seg_b` |
| `--dry-run` | flag | 否 | 关 | 打印两次请求的 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

```bash
sensors segment valid-check --ai-session-id <ai_session_id> --entity-name 'user' \
  --names 'seg_a,seg_b' --format json
```

## 输入 Schema

无 `--input` JSON；`--names` 按逗号拆分、去除空白和重复名称后作为 list 请求的 `segment_definition_names`。
`--dry-run` 会先后打印两次请求体：

| 请求 | 关键字段 | 说明 |
| --- | --- | --- |
| 第一次（存在性） | `segment_definition_names` / `only_brief` / `page_size` | 取回全部指定名称的定义 |
| 第二次（有效性） | 上述字段 + `has_valid_segment: true` | 只返回已有可用结果包的定义 |

两次请求均设置 `show_invisible=true`，包含当前账号有权限访问的不可见定义；不绕过权限过滤。

两次结果的差集即「定义了但还没算出结果包」。以 `--dry-run` 输出为最终事实源。

## 构造流程

1. 收集待判定的分群机器名（`segment.list` 的 `name`），逗号分隔传给 `--names`。
2. 命令自动发两次 list 请求（全量 + 有效过滤）并做差集，无需手工比对。
3. 结果里 `exists=false` 的去核对机器名拼写；`exists=true` 且 `has_valid_segment=false`
   的先 `segment.evaluate` 触发计算，再回看。

```bash
sensors segment valid-check --ai-session-id <ai_session_id> --entity-name 'user' \
  --names "seg_a,seg_b" --format json
```

## 输出

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `results[]` | 每个分群的判定结果 | `—` |
| `results[].name` | 分群定义名 | `seg_a` |
| `results[].exists` | 当前账号是否能查到未删除的定义（无权限、已删除或拼错可为 false） | `true` |
| `results[].has_valid_segment` | 是否已有可用结果包 | `true` |
| `valid_count` | 有可用结果包的数量 | `1` |
| `invalid_count` | 存在定义但无可用结果包的数量 | `1` |
| `missing[]` | 不存在的分群名 | `["seg_x"]` |

结构性解读：

- `exists=false` 与 `has_valid_segment=false` 是两件事，不要合并解释：前者是当前账号未查询到定义，
  后者是定义存在但还没算出结果（`MANUAL` 分群需要先 `segment.evaluate`）。
- 需要人数时用 `segment.item-list`；本命令只回答「有没有可用的结果包」。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：`--names` 不能为空 | 传入空串或只有逗号 | 给出至少一个机器名 |
| 认证 / 权限错误 | api_key、项目或权限无效 | 停止执行，返回修复提示 |

## 使用约束

- 纯只读查询；单次调用会发出两次 list 请求（按名称一次、带有效过滤一次）。
- 一次检查的分群数量受 list 分页限制影响，本命令按传入数量设置页大小；数量很大时
  建议分批调用。
