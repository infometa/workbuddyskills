# tag.list 标签列表

> 工具 `tag.list` · 命令 `sensors tag list` · 类型 查询

## 用途

列出当前项目指定实体下的标签定义，返回身份与状态字段；加 `--verbose` 时附带规则表达式摘要。支持按名称精确过滤、包含已删除标签与分页遍历；只知道 `display_name` 或口语名称时，先用本命令列出候选再匹配，是定位标签对象的第一步。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--entity-name` | string | 是 | — | 实体名称，如 `user`（用户标签） | `user` |
| `--page-size` | int ≥1 | 否 | 100 | 每页返回条数，必须大于 0 | `100` |
| `--page` | int ≥0 | 否 | 0 | 页码，从 0 开始 | `0` |
| `--names` | string | 否 | — | 按标签定义名称过滤，多个名称用逗号分隔（精确匹配内部 `name`） | `"user_tag_1,user_tag_9"` |
| `--show-deleted` | flag | 否 | 关 | 包含已删除的标签 | `—` |
| `--only-brief` | flag | 否 | 关 | 仅返回简要信息，不含规则详情（提升查询性能） | `—` |
| `--verbose` | flag | 否 | 关 | 同时返回规则表达式摘要（`expression`） | `—` |
| `--dry-run` | flag | 否 | 关 | 打印请求 JSON，不发起真实请求 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` 豁免）。

调用示例（常用筛选变体）：

```bash
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --format json
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --names "<tag_name>" --format json
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --names "tag_a,tag_b" --format json
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --show-deleted --format json
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --verbose --format json
```

## 输入 Schema

无 `--input` JSON；查询条件全部通过上方 flag 表达。`--dry-run` 打印的请求体字段：

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `entity_name` | string | 实体名称 | `user` |
| `page_size` / `page` | int | 分页参数 | `100` / `0` |
| `tag_names` | string[] | `--names` 按逗号拆分后的名称列表 | `["user_tag_1","user_tag_9"]` |
| `show_deleted` / `only_brief` | bool | 对应 flag（未开启时省略）；未加 `--verbose` 时 CLI 自动以 `only_brief=true` 请求 | `true` |

以 `--help` 与 `--dry-run` 请求 JSON 为最终事实源。

## 构造流程

1. 实体定位：目标实体名映射为 `--entity-name`（用户标签即 `user`），必填。
2. 名称过滤：已知标签机器名时映射为 `--names`，多个名称用逗号分隔（CLI 按逗号拆分并去空白后作为 `tag_names` 精确匹配）；只知 `display_name` 时不传 `--names`，改为列出后在 `tag_definitions[]` 上按 `display_name` 匹配候选。
3. 其余口径映射：包含已删除标签加 `--show-deleted`；遍历用 `--page`（默认 0）+ `--page-size`（默认 100，≥1）逐页推进，不并发跳页。
4. 需要规则表达式摘要时加 `--verbose`（不加时 CLI 自动以 `only_brief=true` 请求）；参数拿不准时先 `--dry-run` 预览请求体，确认后去掉再真实执行。

```bash
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --names "tag_a,tag_b" --format json
# 只知显示名时先列第 0 页，再在 tag_definitions[] 上按 display_name 匹配候选
sensors tag list --ai-session-id <ai_session_id> --entity-name 'user' --page 0 --format json
```

## 输出

输出示例：

```json
{
  "tag_definitions": [
    {
      "name": "user_tag_<名称>",
      "display_name": "VIP 等级标签",
      "entity_name": "user",
      "status": "TAG_ACTIVE",
      "create_type": "TAG_EQL",
      "visible": true,
      "data_type": "STRING",
      "current_rule_available": false,
      "create_time": "…",
      "update_time": "…",
      "expression": {"tag_type": "EQL_BASED"}
    }
  ],
  "total": 1,
  "page": 0,
  "page_size": 100
}
```

`tag_definitions[]` 数组每项字段：

| 字段 | 说明 | 示例值 |
| --- | --- | --- |
| `name` | 标签定义唯一名（机器名），后续查询与写命令引用时优先复用 | `user_tag_1` |
| `display_name` | 标签显示名，仅用于展示，不一定能作为精确查询名 | `事件分析使用` |
| `entity_name` | 所属实体名 | `user` |
| `status` | 标签定义状态 | `TAG_ACTIVE` |
| `create_type` | 标签创建方式（如 `TAG_EQL` / `TAG_CUSTOMIZED_RULE` / `TAG_GENERAL_RULE_DISTRIBUTION` / `TAG_SQL`） | `TAG_CUSTOMIZED_RULE` |
| `visible` | 是否可见 | `true` |
| `data_type` | 标签值类型，如 `STRING` / `INT` / `BOOL` | `STRING` |
| `current_rule_available` | 当前规则是否可用（不等于已有有效标签结果） | `true` |
| `create_time` / `update_time` | 创建 / 最近更新时间 | `2019-08-30T14:04:36Z` / `2026-09-26T17:01:56.346Z` |

结构性解读：

- `name` 是机器名，`tag.get`、`tag.update`、`tag.evaluate` 都以它为精确标识；`display_name` 不能直接用于 `--names` 过滤。
- `current_rule_available` 只表示当前规则可用性；"规则可用"与"已有有效标签结果"是两回事，不得混同。
- `expression.tag_type` 只区分规则类型（如 `EQL_BASED` / `SQL_BASED`）；具体规则内容在 `tag.get` 中才完整展开，本工具不做规则级解读。
- 分页语义：默认只返回第 0 页、每页最多 100 条；遍历全部标签时递增 `--page`，不要并发跳页猜测。
- `total` 语义（命令层事实）：服务端返回总数时直接使用；缺失时 CLI 以相同筛选条件、每页 100 条的 brief 请求分页统计（安全上限 10000 页），`--names` / `--show-deleted` 同时作用于展示页与 total 统计。
- `--verbose` 时每项追加 `expression` 摘要：`tag_type`（如 `SQL_BASED` / `EQL_BASED` / `LOADING_BASED`）与规则主体核心字段；复杂结构只给计数（`segment_based_rule.groups_count`、`entity_set_rules_count`）。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：缺少 `--entity-name` | 未提供实体名 | 补上 `--entity-name user` 等实体参数 |
| UsageError：`--page-size` / `--page` 越界 | 页大小 < 1 或页码 < 0 | 使用合法分页值 |
| ClickException：响应字段不是数组 | 服务端列表字段结构异常 | 返回错误原文，不猜测解析 |
| ClickException：总数统计重复分页 / 超安全上限 | 服务端分页异常或标签超上限 | 缩小筛选范围（如 `--names`）后重试 |
| 认证 / 权限 / 项目错误 | api_key、项目或权限无效 | 停止执行，返回修复提示 |
| 空结果 | 无满足筛选条件的标签 | 不是错误；原样返回空列表与 total，不自动改查其它资产 |

## 使用约束

- `--names` 只匹配内部 `name`；只知 `display_name` 时先全量列出再按 `display_name` 匹配候选，由调用方确认。
- 带筛选条件的 `total` 不等于项目全部标签数量；空结果与 `current_rule_available` 等结构事实原样传回，业务含义由调用方判断。
- 本工具是"列出候选"，不等于"查看详情"；规则详情用 `tag.get`。
