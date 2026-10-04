# segment.list 分群列表

> 工具 `segment.list` · 命令 `sensors segment list` · 类型 查询

## 用途

列出当前项目指定实体下的分群定义，返回身份与状态字段；加 `--verbose` 时附带规则引用摘要。用于列举候选、按已知名称过滤、批量对比摘要等场景。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user`（用户分群） | `user` |
| `--page-size` | int | 否 | 服务端决定 | 每页返回条数 | `100` |
| `--page` | int ≥0 | 否 | 服务端决定 | 页码，从 0 开始 | `0` |
| `--names` | string | 否 | — | 按分群定义名称过滤，多个名称用逗号分隔（精确匹配内部 `name`） | `active_user_7_days,xiaofangdekehu` |
| `--has-valid-segment` | flag | 否 | 关 | 仅返回有效分群包（已完成计算） | `—` |
| `--show-deleted` | flag | 否 | 关 | 包含已删除的分群 | `—` |
| `--only-brief` | flag | 否 | 关 | 仅返回简要信息，不含规则详情（提升查询性能） | `—` |
| `--verbose` | flag | 否 | 关 | 同时返回规则引用摘要（`segment_rule_ref`） | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例：

```bash
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --format json
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --names "<segment_name>" --format json
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --names "seg_a,seg_b" --format json
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --has-valid-segment --format json
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --show-deleted --format json
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --verbose --format json
```

## 输入 Schema

无 `--input` JSON；查询条件全部通过上方 flag 表达。`--dry-run` 打印的请求体字段：

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `entity_name` | string | 实体名称 | `user` |
| `page_size` / `page` | int | 分页参数（未提供时省略） | `100` / `0` |
| `segment_definition_names` | string[] | `--names` 按逗号拆分后的名称列表 | `["active_user_7_days","xiaofangdekehu"]` |
| `has_valid_segment` / `show_deleted` / `only_brief` | bool | 对应 flag（未开启时省略） | `—` |

以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 构造流程

1. 实体定位：目标实体名映射为 `--entity-name`（用户分群即 `user`），必填。
2. 名称过滤：已知分群机器名时映射为 `--names`，多个名称用逗号分隔（CLI 按逗号拆分并去空白后作为 `segment_definition_names` 精确匹配）；只知 `display_name` 时不传 `--names`，改为列出后在 `segment_definitions[]` 上按 `display_name` 匹配候选。
3. 状态与分页口径映射：仅看已有计算结果的分群加 `--has-valid-segment`；包含已删除定义加 `--show-deleted`；遍历用 `--page`（从 0 起）+ `--page-size` 逐页推进，不并发跳页。
4. 需要规则类型摘要时加 `--verbose`；参数拿不准时先 `--dry-run` 预览请求体（未开启的开关在请求体中省略），确认后去掉再真实执行。

```bash
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --names "seg_a,seg_b" --format json
# 预览请求体：--names 拆分为 segment_definition_names，未开启的开关省略
sensors segment list --ai-session-id <ai_session_id> --entity-name 'user' --names "seg_a,seg_b" --dry-run
```

## 输出

`segment_definitions[]` 数组，每项：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `name` | 分群定义唯一名（机器名）；后续查询优先复用的精确名 | `active_user_7_days` |
| `display_name` | 分群显示名；仅用于展示与人工匹配，不一定能作为精确查询名 | `近7日活跃用户` |
| `entity_name` | 所属实体名 | `user` |
| `status` | 分群定义状态 | `ACTIVE` |
| `create_type` | 分群创建方式 | `QUERY_RESULT` |
| `visible` | 是否可见 | `true` |
| `has_valid_segment` | 是否已有可用分群结果（计算成功），不代表规模 | `—` |
| `create_time` / `update_time` | 创建 / 最近更新时间 | `2021-06-05T08:29:57Z` / `2024-07-05T09:33:57.708Z` |
| `trigger_type` | 触发类型，如 `MANUAL` / `PERIODIC` / `CRON` | `MANUAL` |

输出示例（`--verbose`）：

```json
{
  "segment_definitions": [
    {
      "name": "<segment_name>", "display_name": "<展示名>", "entity_name": "user",
      "status": "…", "create_type": "…", "visible": true, "has_valid_segment": true,
      "create_time": "…", "update_time": "…", "trigger_type": "CRON",
      "segment_rule_ref": {"segment_rule_name": "…", "version": "…", "expression": {"type": "EQL_BASED"}}
    }
  ],
  "total": 1, "page": 0, "page_size": 10
}
```

结构性解读：

- `total` 为筛选条件下的总数（服务端返回，缺失时为本页条数）；`page` 从 0 开始，翻页用 `page` / `page_size` 组合推进。
- `has_valid_segment` 是"定义已有可用计算结果"的结构标志：`false` 表示尚无成功计算的分群包，不代表分群不存在，也不代表规模为 0。
- `--verbose` 时每项追加 `segment_rule_ref`：`segment_rule_name`、`version`、`expression` 摘要（`type` 如 `SQL_BASED` / `EQL_BASED` / `LOADING_BASED`；复杂结构只给计数：`group_expression_rule.groups_count`、`event_sequence_rule.sequence_count`、`entity_set_rules_count`）。`expression.type` 只说明规则类型，具体条件内容须用 `segment.get` 展开。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：缺少 `--entity-name` | 未提供实体名 | 补上 `--entity-name user` 等实体参数 |
| UsageError：`--page` 取值越界 | 页码小于 0 | 使用从 0 开始的非负页码 |
| 认证 / 权限 / 项目错误 | api_key、项目或权限无效 | 停止执行，返回修复提示，不改参数重试 |
| 空结果 | 无满足筛选条件的分群 | 不是错误；原样返回空列表与 total，不自动改查其他资产 |

## 使用约束

- `--names` 只匹配内部 `name`（精确匹配）；只知 `display_name` 时先全量列出再按 `display_name` 匹配候选，由调用方确认。
- `--has-valid-segment` 只筛"已有计算结果"的分群，不能用来判断分群定义是否存在。
- 空结果、`has_valid_segment=false` 等结构事实原样传回，业务含义由调用方判断；按名称筛选列表不等于已查看详情，详情用 `segment.get`。
