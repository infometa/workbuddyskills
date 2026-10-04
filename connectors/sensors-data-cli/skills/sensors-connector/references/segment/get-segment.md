# segment.get 分群详情

> 工具 `segment.get` · 命令 `sensors segment get` · 类型 查询

## 用途

获取单个分群定义的详情，始终返回规则引用及完整规则条件（`segment_rule_ref`）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--name` | string | 是 | — | 分群定义名称（唯一标识符，非中文显示名） | `active_user_7_days` |
| `--entity-name` | string | 是 | — | 实体名称，如 `user` | `user` |
| `--show-deleted` | flag | 否 | 关 | 若分群已删除，也尝试返回其信息 | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例：

```bash
sensors segment get --ai-session-id <ai_session_id> --name "<segment_name>" --entity-name 'user' --format json
```

## 输入 Schema

无 `--input` JSON；`--dry-run` 打印的请求体字段：`name`、`entity_name`、`show_deleted`（未开启时省略）。以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 输出

`segment_definition` 对象：`name`、`display_name`、`entity_name`、`status`、`create_type`、`visible`、`has_valid_segment`（是否已有可用计算结果）、`create_time`、`update_time`、`trigger_type`（如 `MANUAL` / `PERIODIC` / `CRON`）。

输出示例：

```json
{
  "segment_definition": {
    "name": "…", "display_name": "…", "entity_name": "user",
    "trigger_type": "CRON", "has_valid_segment": true,
    "segment_rule_ref": {
      "segment_rule_name": "…", "version": "…",
      "expression": {"type": "SQL_BASED", "sql_segment_rule": {"sql": "…"}}
    }
  }
}
```

`segment_rule_ref`：`segment_rule_name`（规则名）、`version`（规则版本）、`expression`（完整规则条件）。`expression` 字段：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `type` | 规则类型，如 `SQL_BASED` / `EQL_BASED` / `LOADING_BASED` / `GROUP_EXPRESSION_BASED` / `EVENT_SEQUENCE_BASED` | `SQL_BASED` |
| `sql_segment_rule.sql` | SQL 规则内容 | `—` |
| `eql_segment_rule.eql` | EQL 规则内容 | `user.Age >= 18` |
| `loading_segment_rule` | 导入规则，含 `matched_field` / `sync_flag` / `loading_type` | `—` |
| `group_expression_rule` | 条件组规则，完整展开各条件组（含具体筛选条件） | `group_expression: "$1"` |
| `event_sequence_rule` | 行为序列规则，完整展开各序列 | 2 个 `event_steps` + `time_range` |
| `entity_set_rules` | 实体范围规则，完整数组 | `[]` |

经 CLI Rule Draft 创建的分群，回读时 `expression` 的典型形态：

```json
{"type": "EQL_BASED", "eql_segment_rule": {"eql": "<单个 EQL 条件组>"}}
```

```json
{"type": "GROUP_EXPRESSION_BASED", "group_expression_rule": {"groups": ["<…多个规则组…>"], "group_expression": "\"$1\" * \"$2\""}}
```

```json
{"type": "EVENT_SEQUENCE_BASED", "event_sequence_rule": {"simple_event_sequences": [{"event_steps": ["<…>"], "time_range": "<…>"}]}}
```

混合规则的 `group_expression` 用 `*`（交集 / AND）与 `+`（并集 / OR）连接 `"$1"`、`"$2"` 等规则组引用。

结构性解读：

- 先区分"定义存在"与"有可用计算结果"：`has_valid_segment` 只表示后者，两者是不同字段层的概念，不混合解释。
- 解释规则时先给 `expression.type` 规则类型，再按需摘取核心 SQL / EQL / 导入规则 / 条件组具体条件；规则内容与定义状态字段分开说明。
- 输出中保留 `name`（机器名），供后续查询、分析或更新链路复用。

规则补水机制（命令层事实）：部分环境的 definition 接口只返回规则名和版本；此时命令自动解析当前项目数字 ID 并补查对应版本的分群规则，将 `expression` 合并进 `segment_rule_ref`；补查失败时明确报错，不会把失败静默解释为空规则。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| 分群不存在 | `name` / `entity_name` 无匹配定义 | 核对机器名（非显示名）后重查，或先用 `segment.list` 定位；未查到时如实说明，不扩展成重新列举全量分群 |
| ClickException：无法解析项目数字 ID | 规则补水时项目接口未返回整数 ID | 检查 `--project` / 配置中的项目英文名 |
| ClickException：未配置项目英文名 | 规则补水需要项目名而当前为空 | 通过 `--project` 或配置指定项目 |
| ClickException：规则未返回 `expression` | 规则接口成功响应中缺少 expression | 返回错误原文，不伪造规则内容 |
| 认证 / 权限错误 | api_key、项目或权限无效 | 停止执行，返回修复提示 |

## 使用约束

- `--name` 必须是机器名 `name`；`display_name` 不能直接作为查询名。
- 复杂规则结构在本工具完整展开；`segment.list` 对同一结构仅返回计数摘要。
- 用于更新前的现状读取：`create_type`、规则形态（`expression.type`）与 `trigger` 是 `segment.update` 同类型校验与调度边界的输入。
