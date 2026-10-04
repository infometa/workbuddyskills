# tag.get 标签详情

> 工具 `tag.get` · 命令 `sensors tag get` · 类型 查询

## 用途

获取单个标签定义的详情，始终返回规则表达式及完整规则条件（`expression`）。用于解释标签的定义、数据类型、状态、规则内容与规则可用性；进入本工具前应已通过 `tag.list` 等方式确认唯一标签机器名。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--name` | string | 是 | — | 标签定义名称（唯一标识符，非中文显示名） | `user_tag_1` |
| `--entity-name` | string | 是 | — | 实体名称，如 `user` | `user` |
| `--show-deleted` | flag | 否 | 关 | 若标签已删除，也尝试返回其信息 | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例：

```bash
sensors tag get --ai-session-id <ai_session_id> --name "<tag_name>" --entity-name 'user' --format json
sensors tag get --ai-session-id <ai_session_id> --name "<tag_name>" --entity-name 'user' --show-deleted --format json
```

## 输入 Schema

无 `--input` JSON；`--dry-run` 打印的请求体字段：`name`、`entity_name`、`show_deleted`（未开启时省略）。以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 输出

`tag_definition` 对象。输出示例：

```json
{
  "tag_definition": {
    "name": "…",
    "display_name": "…",
    "entity_name": "user",
    "status": "…",
    "create_type": "…",
    "visible": true,
    "data_type": "STRING",
    "current_rule_available": true,
    "create_time": "…",
    "update_time": "…",
    "expression": {
      "tag_type": "SQL_BASED",
      "sql_based_rule": {"sql": "…"}
    }
  }
}
```

`expression` 字段（按 `tag_type` 只出现对应规则主体）：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `tag_type` | 规则类型，如 `SQL_BASED` / `EQL_BASED` / `LOADING_BASED` | `CUSTOM_BASED` |
| `sql_based_rule.sql` | SQL 规则内容 | `—` |
| `eql_based_rule.value_expression` / `filter_expression` | EQL 值表达式 / 过滤表达式 | `user.cname` |
| `loading_based_rule` | 导入规则，含 `matched_field` / `sync_flag` / `loading_type` | `—` |
| `custom_based_rule` | 自定义组件规则，含 `component_name` / `rule` / `rule_str` | `component_name=QE_USER_TAG_RULE_WITH_OLD_META` |
| `basic_measure_based_rule` | 基础指标值规则完整对象 | `bucket_type=PERCENT,buckets=[50]` |
| `rfm_based_rule` | RFM 规则完整对象 | `—` |
| `segment_filter` | 分群筛选规则完整对象 | `—` |
| `segment_based_rule` | 分层规则，完整展开各条件组（含具体筛选条件） | `groups[0].tag=高频` |
| `entity_set_rules` | 实体范围规则，完整数组 | `[]` |
| `virtual` / `version` / `used_fields` | 规则虚拟标识、协议版本和引用字段 | `false` / `1` / `["user.$Events.event_analytics","user.cname"]` |

结构性解读：

- 顶层字段即标签定义本体：`name`（机器名，后续复用）、`display_name`（展示名）、`entity_name`、`status`（定义状态）、`create_type`（创建方式）、`visible`、`data_type`（标签值类型，如 `STRING` / `INT` / `BOOL`）、`current_rule_available`、`create_time` / `update_time`。
- 解读规则的顺序：先说明 `expression.tag_type` 规则类型，再按类型摘取核心内容——SQL 规则给 `sql_based_rule.sql`，EQL 规则给 `value_expression` / `filter_expression`，分层规则给 `segment_based_rule` 各条件组，导入规则给 `loading_based_rule`；不要笼统概括为"规则信息"。
- 本工具完整展开复杂规则（分层规则各条件组、实体范围规则均展开）；`tag.list --verbose` 对同一结构只返回计数摘要（`groups_count` / `entity_set_rules_count`）。
- `current_rule_available` 表示当前规则是否可用，不等于标签已有有效计算结果；两者是不同层面的状态，原样区分传回调用方。
- 输出中保留 `name` 与 `data_type`，供后续 `tag.update`、`tag.evaluate` 或分析链路复用。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| 标签不存在 | `name` / `entity_name` 无匹配定义 | 核对机器名（非显示名）后重查，或先用 `tag.list` 定位 |
| 认证 / 权限错误 | api_key、项目或权限无效 | 停止执行，返回修复提示，不改参数重试 |
| 空结果 | 查无该名称的标签详情 | 不是错误；原样返回"未查到该名称对应的标签"，不扩展为全量列举或换参数重试 |

## 使用约束

- `--name` 必须是机器名 `name`；`display_name` 不能直接作为查询名，先用 `tag.list` 按 `display_name` 匹配到机器名。
- 复杂规则结构在本工具完整展开；`tag.list` 对同一结构仅返回计数摘要。
- `current_rule_available` 表示规则可用性，不等于标签已有有效计算结果；两者区分传回调用方。
- 已删除标签需加 `--show-deleted` 才可能返回；仍查不到时如实返回空结果。
