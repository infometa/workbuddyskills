# 分群规则输入 Schema（rule-schema）

> 供 `segment.create` / `segment.update` 的 `--input` 中 `rule_draft` 规则对象引用。结构最终事实源：`sensors segment create --schema`（本地输出，不读取配置、不访问网络）。分工：CLI Schema 负责字段结构、类型、必填项与枚举；本文负责业务语义、字段关系与常见误用。组装顺序：先读本文理解语义，再执行 Schema 命令核对当前版本，最后用下方示例确认嵌套位置。JSON 不支持注释，不能把说明文字写进请求。

## 顶层结构与二选一

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `segment_definition` | object | 定义外壳：`name`（必填机器名）、`display_name`、`trigger`、`storage_settings` 等；不要把筛选条件放在这里。`name` 须匹配正则 `^[a-z][a-z\d_]{0,99}$`，且以按实体名派生的 `<实体名>_segment_` 前缀开头（实体 `user` 即 `user_segment_<名称>`；兼容历史前缀 `user_group_`、`segment_`），详见 [create-segment.md](create-segment.md) | `{"name":"user_segment_agent_dryrun_eql_demo","display_name":"dry-run EQL 示例"}` |
| `rule_draft` | object | 与 `segment_definition.segment_rule_ref.expression` 二选一；由 CLI Builder 转换最终 expression | `{"create_type":"EQL","rule":{…}}` |
| `segment_definition.segment_rule_ref.expression` | object | 二选一的另一侧；调用方已提供完整最终规则时使用 | `—` |

规则来源二选一约束：`rule_draft` 与 `segment_definition.segment_rule_ref.expression` 必须恰好提供一个，同时提供或都不提供都会校验失败。两种模式的差异：

| 模式 | 必填字段 | CLI 行为 |
| --- | --- | --- |
| `rule_draft`（结构化草稿） | `segment_definition.name` | Builder 自动补全默认值（`entity_name=user`、`visible=true`、`managed=true`、`status=ACTIVE`、来源 `source` 类别 `SEGMENT_AGENT` 等）并生成最终 expression；未提供 `trigger` 时默认 `MANUAL` |
| 完整 Definition | `name`、`entity_name`、`create_type`、`segment_rule_ref.expression` 四者缺一不可 | 不重新解释 expression，原样提交，但仍须经过 dry-run 校验 |

通用字段速记：

| 字段 | 业务含义 | 生成约束 | 示例值 |
| --- | --- | --- | --- |
| `rule_draft.create_type` | 规则类型判别字段，决定 `rule_draft.rule` 的结构 | 纯 EQL 条件用 `EQL`；含行为序列必须用 `CUSTOMIZED_RULE` | `EQL` |
| `segment_definition.create_type` | 定义外壳上的创建类型 | 显式提供时必须与 `rule_draft.create_type` 一致 | `EQL` |
| `relation` | 条件组内各条件的逻辑关系 | `AND` 同时满足、`OR` 满足任一、`NOT` 只能包含一个条件 | `AND` |
| `conditions[].type` | 单个条件的类型判别字段 | type 决定该条件允许的字段，不同 type 的字段不能混用 | `user_attribute` |
| `time_range` | 事件统计或判断的数据时间范围 | 联合类型，三种形态见下；`relative` 的数量字段名是 `last` 不是 `value` | `{"type":"relative","unit":"DAY","last":30}` |
| `data_type` | 属性 / 标签值在元数据中的真实类型 | 必须来自元数据查询结果，不按字面值猜测；决定可用 `operator` 与 `value` 类型 | `NUMBER` |
| `operator` | 属性、次数或指标结果与目标值的比较方式 | 必须与 `data_type`（或阈值类型）兼容；分群成员关系用自己的 INCLUDE / EXCLUDE 枚举 | `GTE` |
| `value` | 比较阈值、枚举值或目标值 | 保持业务给定的值，按 `data_type` 输出字符串 / 数字 / 布尔 / 数组；空值操作符必须省略 | `18` |
| `dry_run` | 请求服务端只校验不落库 | 与命令层 `--dry-run` flag 等效且 flag 优先 | `true` |
| `skip_rule_check` | 要求服务端跳过规则校验 | 必须省略或 `false`，禁止设为 `true` | `—` |

## 创建类型与输入形状

| `rule_draft.create_type` | `rule_draft.rule` 形状 |
| --- | --- |
| `EQL` | `EqlLogicGroupDraft`：仅含可转 EQL 条件的条件树，不支持 `event_sequence` |
| `CUSTOMIZED_RULE` | `LogicGroupDraft`：可扩展条件树，支持普通条件与 `event_sequence`（结构见 [segment-event-sequence-schema.md](segment-event-sequence-schema.md)） |

类型判定规则：

- 普通用户属性、事件、标签或分群条件（无行为先后顺序）→ `EQL`。
- 多组规则、复杂组合、行为先后顺序（先 A 再 B）→ `CUSTOMIZED_RULE`；行为序列必须作为其中的 `event_sequence` 条件表达。
- 不因规则校验失败自动切换 create_type；规则形态有歧义时先按业务差异确认再定。
- 当前 CLI 仅支持以上两种创建类型；SQL 分群、导入分群（`GROUP_BASED` / `QUERY_RESULT` / `IMPORT` / `SQL`）不支持通过本命令创建。

## 条件树（分组结构）

```json
{"relation": "AND", "conditions": ["<条件对象或嵌套条件组>"]}
```

| 字段 | 约束 | 示例值 |
| --- | --- | --- |
| `relation` | `AND`（同时满足）/ `OR`（满足任一）/ `NOT`（只能包含一个条件） | `AND` |
| `conditions[]` | 条件对象或嵌套条件组，可递归组合；`AND` / `OR` 组至少一个成员 | `[{"type":"user_attribute",…},{"type":"segment_filter",…}]` |

`event_sequence` 只能出现在 `CUSTOMIZED_RULE` 条件树的顶层 `conditions`；放入嵌套条件组会被 CLI 拒绝（`nested event_sequence groups are not supported`）。含 `event_sequence` 的混合规则不支持 `NOT` 关系；同层多条件按 `AND` 生成 `"$1" * "$2"`、按 `OR` 生成 `"$1" + "$2"` 的人群组表达式。

## 条件类型（`conditions[].type` 判别联合）

| `type` | 语义 | 关键字段 | 示例值 |
| --- | --- | --- | --- |
| `user_attribute` | 比较用户属性 | `field`、`data_type`、`operator`、`value` | `Age / NUMBER / GTE / 18` |
| `event_occurrence` | 时间范围内至少发生过一次事件 | `event_name`、`time_range`、可选 `filters`；无次数阈值 | `sa_query_analytics / 近30天` |
| `event_absence` | 时间范围内没有发生事件 | `event_name`、`time_range`、可选 `filters`；语义是"未发生"，不能改写为次数 ≤ 0 | `trading_day_management / 近1周` |
| `event_count` | 比较事件发生次数 | `event_name`、`time_range`、`operator`、`value`（比较对象是次数）、可选 `filters` | `sa_query_analytics / 近7天 / GTE / 3` |
| `event_metric` | 聚合事件属性后比较结果 | `event_name`、`field`、`data_type`、`aggregation`、`time_range`、`operator`、`value` | `sa_query_analytics / time_consuming SUM / GTE / 1000` |
| `event_day_distribution` | 比较事件发生的去重天数 | 同 `event_count`；统计活跃天数而非次数；`relative` + `DAY` 时 `last` ≥ 1 | `sa_query_analytics / 近30天 / GTE / 5` |
| `tag_filter` | 按已有标签值筛选 | `tag`（准确标签名）、`data_type`、`operator`、`value` | `user_tag_biaoqian3 / NUMBER / GTE / 1` |
| `segment_filter` | 按已有分群成员关系筛选 | `segment`（分群内部 `name`，非 `display_name`，从 `segment list` 获取）、`operator`：`INCLUDE`（属于该分群）/ `EXCLUDE`（不属于） | `user_segment_<名称> / INCLUDE` |
| `event_sequence` | 多个事件按顺序发生 | `steps`、`window`；见 [segment-event-sequence-schema.md](segment-event-sequence-schema.md) | `s1 sa_query_analytics → s2 trading_day_management / 14天` |

各类型示例（占位符须替换为已确认的真实标识）：

```json
{"type": "user_attribute", "field": "<用户属性名>", "data_type": "STRING", "operator": "EQ", "value": "<属性值>"}
```

```json
{"type": "event_occurrence", "event_name": "<事件名>", "time_range": {"type": "relative", "unit": "DAY", "last": 30}, "filters": [{"field": "<属性名>", "data_type": "STRING", "operator": "IS_NOT_NULL"}]}
```

```json
{"type": "event_absence", "event_name": "<事件名>", "time_range": {"type": "relative", "unit": "WEEK", "last": 1}}
```

```json
{"type": "event_count", "event_name": "<事件名>", "time_range": {"type": "relative", "unit": "DAY", "last": 7}, "operator": "GTE", "value": 3}
```

```json
{"type": "event_metric", "event_name": "<事件名>", "field": "<数值属性名>", "data_type": "NUMBER", "aggregation": "SUM", "time_range": {"type": "relative", "unit": "DAY", "last": 30}, "operator": "GTE", "value": 1000}
```

```json
{"type": "event_day_distribution", "event_name": "<事件名>", "time_range": {"type": "relative", "unit": "DAY", "last": 30}, "operator": "GTE", "value": 5}
```

```json
{"type": "tag_filter", "tag": "<标签名>", "data_type": "STRING", "operator": "EQ", "value": "<标签值>"}
```

```json
{"type": "segment_filter", "segment": "<分群内部name>", "operator": "INCLUDE"}
```

`event_sequence` 示例见 [segment-event-sequence-schema.md](segment-event-sequence-schema.md)。

`event_metric.aggregation` 取值：`COUNT` / `COUNT_DISTINCT` / `SUM` / `AVG` / `MIN` / `MAX`；约束：`COUNT_DISTINCT` 不支持用于 `event_metric`；`SUM` / `AVG` 要求 `data_type=NUMBER`；`MIN` / `MAX` 要求 `NUMBER` / `DATE` / `DATETIME`；`field` 对所有聚合必填（含 `COUNT`），`data_type` 在非 `COUNT` 聚合下必须绑定。`tag_filter` 未提供 `data_type` 时只允许 `IS_NULL` / `IS_NOT_NULL`。

## 过滤条件（`filters[]`，含 `event_sequence.steps[].filters`）

| 字段 | 类型 | 约束 | 示例值 |
| --- | --- | --- | --- |
| `field` | string | 事件属性名，使用已确认的真实标识 | `analysis_type` |
| `data_type` | `STRING` \| `NUMBER` \| `BOOL` \| `DATE` \| `DATETIME` | 来自元数据查询结果，不按字面值猜测 | `STRING` |
| `operator` | 枚举 | 见下表；须与 `data_type` 兼容 | `IS_NOT_NULL` |
| `value` | 与 `data_type` 匹配 | `operator` 为 `IS_NULL` / `IS_NOT_NULL` 时必须省略（不可传 `null` 或空值） | `1000` |

同一 `filters` 列表内多个条件按 AND 组合。`value` 类型必须与 `data_type` 一致：`NUMBER` 用数字字面量、`STRING` 用字符串、`BOOL` 用布尔值、`DATE` / `DATETIME` 用字符串。

### 操作符矩阵（18 个）

| `operator` | 语义 | `value` 要求 | 适用 `data_type` |
| --- | --- | --- | --- |
| `EQ` / `NEQ` | 等于 / 不等于 | 单个与 `data_type` 匹配的值 | 全部 |
| `IN` / `NOT_IN` | 在 / 不在枚举列表内 | 非空数组，元素类型与 `data_type` 一致 | `STRING` / `NUMBER` / `DATE` / `DATETIME` |
| `GT` / `GTE` / `LT` / `LTE` | 大于 / 大于等于 / 小于 / 小于等于 | 单值 | `NUMBER` / `DATE` / `DATETIME` |
| `BETWEEN` | 区间，≥ 下界且 ≤ 上界（含边界） | 恰好两个元素的数组 | `NUMBER` / `DATE` / `DATETIME` |
| `IS_NULL` / `IS_NOT_NULL` | 属性为空 / 属性有值 | 必须省略 | 全部 |
| `CONTAINS` / `NOT_CONTAINS` | 包含 / 不包含子串 | 单个字符串 | `STRING` |
| `LIKE` / `NOT_LIKE` | 通配符匹配 / 反向 | 单个字符串 | `STRING` |
| `RLIKE` / `NOT_RLIKE` | 正则匹配 / 反向 | 单个字符串 | `STRING` |
| `STARTS_WITH` | 前缀匹配 | 单个字符串 | `STRING` |

按 `data_type` 速查：

- `STRING`：`EQ`、`NEQ`、`IN`、`NOT_IN`、`IS_NULL`、`IS_NOT_NULL`、`CONTAINS`、`NOT_CONTAINS`、`LIKE`、`NOT_LIKE`、`RLIKE`、`NOT_RLIKE`、`STARTS_WITH`
- `NUMBER` / `DATE` / `DATETIME`：`EQ`、`NEQ`、`IN`、`NOT_IN`、`GT`、`GTE`、`LT`、`LTE`、`BETWEEN`、`IS_NULL`、`IS_NOT_NULL`
- `BOOL`：`EQ`、`NEQ`、`IS_NULL`、`IS_NOT_NULL`

阈值比较（`event_count` / `event_day_distribution`，以及 `event_metric` 的 `COUNT` / `SUM` / `AVG` 和数值 `MIN` / `MAX`）：比较对象是数值，仅支持 `EQ`、`NEQ`、`GT`、`GTE`、`LT`、`LTE`、`BETWEEN`；`IN` / `NOT_IN` / `IS_NULL` / `IS_NOT_NULL` 会被拒绝。`event_metric` 的 `MIN` / `MAX` 且 `data_type=DATE` / `DATETIME` 时按类型化比较，支持日期比较操作符。

### 空值判断（IS_NULL / IS_NOT_NULL）

- `value` 必须省略：不可传 `null`、空字符串或任意值，误传会校验失败。
- 直接判断属性是否为空 / 有值，不与任何具体值比较；适用于 `event_occurrence` / `event_absence` / `event_count` / `event_metric` / `event_day_distribution` 的 `filters` 与 `event_sequence.steps[].filters`，各 `data_type` 均可用。
- 禁止用 `!= ""` 等兜底写法或手写 EQL 替代；`IS_NULL` / `IS_NOT_NULL` 是语义精确的表达，Builder 会正确转换。
- `data_type` 仍必须提供，来自元数据查询结果。

## time_range 联合类型

事件类条件（`event_occurrence` / `event_absence` / `event_count` / `event_metric` / `event_day_distribution`）必填 `time_range`；`event_sequence` 使用 `window` 代替，不接受 `time_range`。三种形态：

```json
{"type": "all_time"}
```

```json
{"type": "relative", "unit": "DAY", "last": 30}
```

```json
{"type": "static", "start": "2025-01-01", "end": "2025-01-31"}
```

| 形状 | 结构 | 说明 |
| --- | --- | --- |
| `all_time` | `{"type": "all_time"}` | 全部可用历史数据，无额外字段 |
| `relative` | `{"type": "relative", "unit": …, "last": …}` | 从执行时间向前回溯；`unit`：`HOUR` / `DAY` / `WEEK` / `MONTH` / `YEAR`；`last` 为正有限数（字段名是 `last` 不是 `value`） |
| `static` | `{"type": "static", "start": …, "end": …}` | 固定区间；`start` / `end` 为 ISO 日期或日期时间，含边界（示例日期仅为格式演示） |

## 调度字段（`segment_definition.trigger` / `storage_settings`）

| 字段 | 结构 | 约束 | 示例值 |
| --- | --- | --- | --- |
| `trigger.trigger_type` | `MANUAL` \| `CRON` | 未提供时默认 `MANUAL` | `MANUAL` |
| `trigger.cron_trigger.crontab_exp` | string | 七字段 Quartz CRON 表达式，由服务端校验（dry-run 反馈格式错误）；更新侧另有 CLI 形态校验，见 [update-segment.md](update-segment.md) | `—` |
| `storage_settings.version_count` | int | `MANUAL` 固定为 `1`（CLI 自动补全，不可指定其他值）；`CRON` 默认 `5`，可指定 `1..100` | `1` |

两种触发的写法：

```json
{"trigger": {"trigger_type": "MANUAL"}}
```

```json
{"trigger": {"trigger_type": "CRON", "cron_trigger": {"crontab_exp": "<七字段 Quartz CRON>"}}, "storage_settings": {"version_count": 10}}
```

语义映射：

- "每天上午 10 点例行调度 + 保留 10 份" → `trigger_type: CRON` + 对应 `crontab_exp` + `version_count: 10`
- "手动更新"或未提及调度 → 省略 `trigger`（默认 `MANUAL`），`version_count` 自动为 `1`
- `MANUAL` 分群不自动计算，需通过 `sensors segment evaluate` 触发

编辑存储规则（修改 `version_count`）需要单独的功能权限；没有该权限的用户创建分群时只能使用默认设置。

## 完整示例（四种规则形态）

`EQL`（单一条件组合）：

```json
{
  "segment_definition": {"name": "user_segment_<名称>", "display_name": "<展示名>", "trigger": {"trigger_type": "MANUAL"}},
  "rule_draft": {
    "create_type": "EQL",
    "rule": {"relation": "AND", "conditions": [
      {"type": "user_attribute", "field": "<用户属性名>", "data_type": "STRING", "operator": "EQ", "value": "<属性值>"}
    ]}
  }
}
```

`CUSTOMIZED_RULE`（普通条件树，无行为顺序；Builder 生成由 EQL 规则组组成的人群组表达式）：

```json
{
  "segment_definition": {"name": "user_segment_<名称>", "display_name": "<展示名>"},
  "rule_draft": {
    "create_type": "CUSTOMIZED_RULE",
    "rule": {"relation": "AND", "conditions": [
      {"type": "user_attribute", "field": "<用户属性名>", "data_type": "NUMBER", "operator": "GTE", "value": 5}
    ]}
  }
}
```

`CUSTOMIZED_RULE`（事件序列）：

```json
{
  "segment_definition": {"name": "user_segment_<名称>", "display_name": "<展示名>"},
  "rule_draft": {
    "create_type": "CUSTOMIZED_RULE",
    "rule": {"relation": "AND", "conditions": [
      {"type": "event_sequence",
       "steps": [{"id": "s1", "event_name": "<事件名1>"}, {"id": "s2", "event_name": "<事件名2>"}],
       "window": {"unit": "DAY", "value": 7}}
    ]}
  }
}
```

`CUSTOMIZED_RULE`（同层混合：EQL 条件 + 事件序列，AND 关系生成 `"$1" * "$2"`）：

```json
{
  "segment_definition": {"name": "user_segment_<名称>", "display_name": "<展示名>"},
  "rule_draft": {
    "create_type": "CUSTOMIZED_RULE",
    "rule": {"relation": "AND", "conditions": [
      {"type": "user_attribute", "field": "<用户属性名>", "data_type": "NUMBER", "operator": "GTE", "value": 2},
      {"type": "event_sequence",
       "steps": [{"id": "s1", "event_name": "<事件名1>"}, {"id": "s2", "event_name": "<事件名2>"}],
       "window": {"unit": "DAY", "value": 30}}
    ]}
  }
}
```

## 占位符与标识约定

- 示例中 `<名称>`、`<事件名>`、`<属性名>`、`<标签名>`、`<CRON 表达式>` 等尖括号内容为占位符，必须替换为已确认的真实标识；机器名占位形态 `user_segment_<名称>` 为派生前缀加占位名称；不得沿用示例名称。
- 事件、属性、标签、分群引用一律使用元数据或对应查询命令确认过的准确名称与 `data_type`；多候选或无法唯一确定时交由调用方消解，不猜测、不套用近似名称。
- `$time`、`$day` 等契约明确的平台内置字段无需单独查询元数据，但其所属事件必须真实存在并已确认。
- 已在其他条件表达过的过滤不要重复写入（如 `event_sequence.steps[].filters`），避免双重过滤。

## 构造边界

- 不手写最终 Horizon expression；Rule Draft 交给 CLI Builder 转换。
- 不设置 `skip_rule_check` 为 `true`；不设置或引用旧的规则名称字段；不自动改名。
- 先按本文与 `--schema` 组装，再执行 `sensors segment create --dry-run` 做服务端校验；完整 Definition 模式不重新解释 expression，但仍要经过 dry-run。
