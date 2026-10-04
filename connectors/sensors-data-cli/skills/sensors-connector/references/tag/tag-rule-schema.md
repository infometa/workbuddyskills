# 标签规则输入 Schema（rule-schema）

> 供 `tag.create` / `tag.update` 的 `--input` 中 `rule_draft` 规则对象引用。结构最终事实源：`sensors tag create --schema`（本地输出，不读取配置、不访问网络）。

## 如何使用本文件

- CLI Schema（`--schema` 输出）负责字段结构、类型、必填项、枚举值和互斥约束，是唯一结构真相；本文负责业务语义、字段之间的关系和常见误用。
- 下方 JSON 示例展示可直接组装的完整形状；JSON 不支持注释，说明文字不得写进请求。
- 组装顺序：先理解本文语义 → 执行 `--schema` 核对当前版本 → 用示例确认嵌套位置。
- 调用方生成 `rule_draft`，CLI Builder 负责转换最终 Horizon expression；不要手写最终 expression。

## 顶层结构与二选一

| 字段 | 类型 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `definition` | object | 定义外壳：`name`（必填机器名）、`display_name`、`data_type`、`trigger`、`storage_settings` 等；至少提供稳定的 `name`，规则条件不放这里。`name` 须匹配正则 `^[a-z][a-z\d_]{0,99}$`，且以按实体名派生的 `<实体名>_tag_` 前缀开头（实体 `user` 即 `user_tag_<名称>`；兼容历史前缀 `user_tag_`、`tag_`），详见 [create-tag.md](create-tag.md) | `{"name":"user_tag_agent_demo_eql","display_name":"Agent演示EQL标签"}` |
| `rule_draft` | object | 结构化规则草稿；优先用于自然语言创建，与 `definition.expression` 二选一 | `{"create_type":"TAG_EQL","value_expression":{"expression":"user.cname"}}` |
| `definition.expression` | object | 已完成转换的 Horizon 最终规则；仅在调用方明确提供完整 Definition 时使用，二选一的另一侧 | `{"tag_type":"EQL_BASED","eql_based_rule":{"value_expression":"user.cname"}}` |

同时提供或都不提供会校验失败。完整 Definition 模式必须提供 `name`、`entity_name`、`create_type`、`expression` 四个必填字段；CLI 不重新解释 expression，但仍要经过 dry-run。

采用 `rule_draft` 时 CLI 自动补全默认值（`entity_name=user`、`data_type=STRING`、`visible=true`、`status=TAG_ACTIVE`、来源类别 `TAG_AGENT` 等）。

## 创建类型与输入形状

`rule_draft.create_type` 是判别字段，决定其余字段的结构；必须按业务意图选择，不能只因某个字段容易填写而改变类型。当前 CLI 仅支持四种创建类型，导入标签等不支持：

| `rule_draft.create_type` | 形状 | 生成的规则类型 |
| --- | --- | --- |
| `TAG_EQL` | `value_expression` 或 `rule` 二选一，可选 `filter_expression` | `EQL_BASED` |
| `TAG_CUSTOMIZED_RULE` | `layers[]`（唯一可组装形状，兼容字段 `rule` 会被 Builder 拒绝） | `SEGMENT_BASED`（分层） |
| `TAG_GENERAL_RULE_DISTRIBUTION` | `rule` 为指标分布分桶 | `BASIC_MEASURE_BASED` |
| `TAG_SQL` | `rule.sql` 为完整 SQL | `SQL_BASED` |

`definition.create_type` 若显式提供，必须与 `rule_draft.create_type` 一致，不一致会校验失败。

## 通用字段语义

适用于条件树与过滤条件的字段级规则：

| 字段 | 业务含义 | 生成约束 | 示例值 |
| --- | --- | --- | --- |
| `relation` | 当前条件组中各条件的逻辑关系 | `AND` 同时满足；`OR` 满足任一；`NOT` 必须且只能包含一个条件 | `AND` |
| `conditions[].type` | 单个条件的类型判别字段 | type 决定该条件允许的字段；不同 type 的字段不能混用 | `user_attribute` |
| `time_range` | 事件统计或判断使用的数据时间范围 | `relative.last` 表示从执行时间向前回溯的数量（不是固定日期），单位放在 `unit`；形态见下方「过滤条件与 time_range」 | `{"type":"relative","unit":"DAY","last":30}` |
| `data_type` | 元数据中属性或标签值的真实类型 | 必须来自元数据查询，不能根据字面值猜测；它决定可用的 `operator` 和 `value` 类型 | `STRING` |
| `operator` | 属性、次数或指标结果与目标值的比较方式 | 必须与 `data_type` 和条件类型兼容；空值操作符不应再携带普通比较值 | `EQ` |
| `value` | 比较阈值、枚举值或属性目标值 | 保持业务给定值，并按元数据类型输出字符串、数字、布尔值或数组 | `神策分析 Demo` |
| `dry_run` | 请求服务端只校验、不持久化标签 | 与命令层 `--dry-run` flag 等效且 flag 优先 | `true` |
| `skip_rule_check` | 要求服务端跳过规则校验 | 必须省略或设为 `false`，禁止设为 `true` | `—` |

## TAG_EQL

使用一个可转换为 EQL 的规则计算标签值。`value_expression` 与 `rule` 必须二选一；`filter_expression` 仅用于限制参与计算的用户。

| 字段 | 约束 | 示例值 |
| --- | --- | --- |
| `value_expression.expression` | 完整 EQL 值表达式，资源已完成元数据绑定（取用户属性形如 `user.<属性名>`）；与 `rule` 二选一 | `user.cname` |
| `rule` | `EqlLogicGroupDraft` 条件树（结构见下方「条件树与条件类型」）；与 `value_expression` 二选一 | `{"relation":"AND","conditions":[…]}` |
| `filter_expression` | 可选完整 EQL 过滤表达式，限制参与计算的用户 | `—` |

`value_expression` 形态（标签值直接取用户属性或简单表达式）：

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "VIP 等级标签",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_EQL",
    "value_expression": {
      "expression": "user.<属性名>"
    }
  }
}
```

`rule` 条件树形态（由条件树推导标签值，CLI Builder 转换最终 EQL）：

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "VIP 等级标签",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_EQL",
    "rule": {
      "relation": "AND",
      "conditions": [
        {
          "type": "user_attribute",
          "field": "vip_level",
          "data_type": "NUMBER",
          "operator": "GTE",
          "value": 3
        }
      ]
    }
  }
}
```

BOOL 标签形态（字段层规则）：

- `definition.data_type` 必须显式声明 `"BOOL"`，不可遗漏，否则标签值被解释为数值/字符串而非布尔值。
- 规则使用 `rule`（`EqlLogicGroupDraft`）而非 `value_expression`；可用全部 EQL 条件类型（`user_attribute`、`event_occurrence`、`event_count`、`event_metric` 等）。
- 标签值不是属性或表达式的值，而是条件成立与否的布尔判断：条件全部成立 → `true`，任一不成立 → `false`；多条件用 `relation`（`AND` / `OR`）组合。
- `value_expression` 与 BOOL 形态不兼容；需要直接返回布尔表达式值时用 `value_expression`，此时 `data_type` 省略、由表达式类型推断。

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "<展示名>",
    "data_type": "BOOL",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_EQL",
    "rule": {
      "relation": "AND",
      "conditions": [
        {
          "type": "event_metric",
          "event_name": "<事件名>",
          "field": "<数值属性名>",
          "data_type": "NUMBER",
          "aggregation": "SUM",
          "time_range": {"type": "relative", "unit": "DAY", "last": 30},
          "operator": "GT",
          "value": 10000
        }
      ]
    }
  }
}
```

## TAG_CUSTOMIZED_RULE

按明确的标签值分层创建；`layers` 必填且至少一层。Schema 中保留的兼容字段 `rule` 仅用于旧输入兼容校验，Builder 一律要求 `layers`（仅提供 `rule` 会报 `TAG_CUSTOMIZED_RULE layers are required`），组装时不要使用。

| 字段 | 约束 | 示例值 |
| --- | --- | --- |
| `layers[].tag` | 命中该层得到的标签值；同一规则内必须唯一、非空；顺序保持确认过的分层顺序 | `高频` |
| `layers[].segment` | 该层人群条件：`EqlLogicGroupDraft` 条件树，或 `group_expression` 人群组表达式；每层独立表达，不把不同标签值的条件合并 | `{"relation":"AND","conditions":[…]}` |

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "年龄阶段标签",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_CUSTOMIZED_RULE",
    "layers": [
      {
        "tag": "adult",
        "segment": {
          "relation": "AND",
          "conditions": [
            {
              "type": "user_attribute",
              "field": "age",
              "data_type": "NUMBER",
              "operator": "GTE",
              "value": 18
            }
          ]
        }
      }
    ]
  }
}
```

`segment` 也可用 `group_expression` 显式组合多个 EQL 规则组：

```json
{
  "type": "group_expression",
  "groups": [{"id": "g1", "rule": {"relation": "AND", "conditions": ["…"]}}],
  "expression": "\"$1\"",
  "time_zone": "<可选项目时区>"
}
```

`groups[].id` 省略时按顺序生成；`expression` 引用组标识，`*` 表示交集、`+` 表示并集，可用括号，默认 `"\"$1\""`。

## TAG_GENERAL_RULE_DISTRIBUTION

按事件指标聚合结果分桶生成标签值。`rule`（指标分布）字段：

| 字段 | 约束 | 示例值 |
| --- | --- | --- |
| `event_name` | 事件名，使用已确认的真实标识 | `sa_query_analytics` |
| `field` | 参与聚合的事件属性；非 `COUNT` 聚合必须提供，使用元数据中的准确名称 | `—` |
| `aggregation` | `COUNT` / `COUNT_DISTINCT` / `SUM` / `AVG` / `MIN` / `MAX` | `COUNT` |
| `bucket_type` | 指标切分方式：`NUMBER` 按数值边界、`PERCENT` 按百分位边界、`DISCRETE` 按离散指标值 | `PERCENT` |
| `values` | 按分桶顺序分配的标签值；顺序必须与分桶结果一致；`NUMBER` / `PERCENT` 必须非空，`DISCRETE` 必须为空 | `["高频","低频"]` |
| `buckets` | 有序数值或百分位边界；`NUMBER` / `PERCENT` 必须非空，`DISCRETE` 必须为空 | `[50]` |
| `time_range` | 统计时间范围，默认 `all_time`；结构见下方「过滤条件与 time_range」 | `{"type":"relative","unit":"DAY","last":30}` |
| `filters` / `segment_filter` | 聚合前的事件属性过滤 / 参与计算的人群范围，均可省略 | `—` |

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "下单次数等级",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_GENERAL_RULE_DISTRIBUTION",
    "rule": {
      "event_name": "Order",
      "aggregation": "COUNT",
      "bucket_type": "PERCENT",
      "values": ["top", "tail"],
      "buckets": [50],
      "time_range": {"type": "relative", "unit": "DAY", "last": 30}
    }
  }
}
```

## TAG_SQL

`rule.sql`：返回实体标识列和标签值列的完整 SQL。只接受用户显式提供的完整 SQL，不得根据自然语言猜测或生成，也不改写；最终由 Schema 和服务端 dry-run 校验。

```json
{
  "definition": {
    "name": "user_tag_<名称>",
    "display_name": "显式 SQL 标签",
    "trigger": {"trigger_type": "MANUAL"}
  },
  "rule_draft": {
    "create_type": "TAG_SQL",
    "rule": {
      "sql": "select id, value from confirmed_user_tag_source"
    }
  }
}
```

## 条件树与条件类型

`EqlLogicGroupDraft` 条件树：`relation`（`AND` / `OR` / `NOT`，`NOT` 只能包含一个条件）+ `conditions[]`（条件对象或嵌套条件组，可递归）。标签条件树仅包含可转换为 EQL 的条件，不含 `event_sequence` 事件序列条件。

| `conditions[].type` | 语义 | 关键字段与区别 | 示例值 |
| --- | --- | --- | --- |
| `user_attribute` | 比较用户属性 | `field`、`data_type`、`operator`、`value` | `user_attribute` |
| `event_occurrence` | 时间范围内至少发生过一次事件 | `event_name`、`time_range`、可选 `filters`；不填写次数阈值 | `event_occurrence` |
| `event_absence` | 时间范围内没有发生事件 | 同上；语义是"未发生"，不能改写成 `event_count` 次数 ≤ 0 | `event_absence` |
| `event_count` | 比较事件发生次数 | `event_name`、`time_range`、`operator`、`value`；比较对象是次数，不是事件属性 | `event_count` |
| `event_metric` | 聚合事件属性后比较结果 | `event_name`、`field`、`data_type`、`aggregation`、`time_range`、`operator`、`value`；`COUNT_DISTINCT` 不支持，`SUM` / `AVG` 要求 `NUMBER` 数值属性 | `event_metric` |
| `event_day_distribution` | 比较事件发生的去重天数 | 同 `event_count`；统计的是活跃天数，不是次数 | `event_day_distribution` |
| `tag_filter` | 按已有标签值筛选 | `tag`（必须已绑定的准确标签名）、`data_type`、`operator`、`value` | `tag_filter` |
| `segment_filter` | 按已有分群成员关系筛选 | `segment`（分群内部 `name`，如 `user_segment_vip_high_level`，不能填 `display_name`，`name` 从 `segment list` 返回获取）、`operator`：`INCLUDE`（属于该分群）/ `EXCLUDE`（不属于） | `segment_filter` |

## 过滤条件与 time_range

`filters[]`：`field`（属性名）+ `data_type`（`STRING` / `NUMBER` / `BOOL` / `DATE` / `DATETIME`，来自元数据查询）+ `operator` + 可选 `value`。`operator` 枚举：`EQ`、`NEQ`、`IN`、`NOT_IN`、`GT`、`GTE`、`LT`、`LTE`、`IS_NULL`、`IS_NOT_NULL`、`CONTAINS`、`NOT_CONTAINS`、`LIKE`、`NOT_LIKE`、`RLIKE`、`NOT_RLIKE`、`STARTS_WITH`、`BETWEEN`。`IS_NULL` / `IS_NOT_NULL` 必须省略 `value`；其余操作符的 `value` 类型必须与 `data_type` 一致；同一列表内多条件按 AND 组合。

`time_range` 联合类型：`{"type": "all_time"}`；`{"type": "relative", "unit": "HOUR|DAY|WEEK|MONTH|YEAR", "last": <正数>}`（从执行时间向前回溯 `last` 个 `unit`）；`{"type": "static", "start": "…", "end": "…"}`（ISO 日期或日期时间，含边界）。

## 调度字段（`definition.trigger` / `storage_settings`）

| 字段 | 结构 | 约束 | 示例值 |
| --- | --- | --- | --- |
| `trigger.trigger_type` | `MANUAL` \| `CRON` | 未提供时默认 `MANUAL` | `MANUAL` |
| `trigger.cron_trigger.crontab_exp` | string | 七字段 Quartz CRON 表达式，由服务端校验 | `0 0 8 * * ? *` |
| `storage_settings.version_count` | int | `MANUAL` 固定为 `1`（CLI 自动补全）；`CRON` 默认 `5`，可指定 `1..100` | `1` |

更新侧调度边界（`tag.update`，CLI 校验事实）：`CRON → CRON` 仅允许改秒/分/时，日、月、周、年必须与当前一致；支持 `CRON → MANUAL`（联动 `version_count=1`）；不支持 `MANUAL → CRON`。详见 [update-tag.md](update-tag.md)。

## 元数据绑定

- 规则引用的事件、属性、枚举值、已有标签和分群，先绑定到元数据或对应资产查询返回的准确名称与 `data_type`，不从自然语言猜测资源名称或数据类型。
- 多候选时停止并交由调用方确认；无候选禁止猜测近似名称或套用示例名称。
- `$time`、`$day` 等契约明确的平台内置字段无需单独查询，但其所属事件必须真实存在并已确认。
- 完整 EQL / SQL 只接受用户明确提供或已有可信契约中的内容。

## 占位符与标识约定

- 示例中 `<名称>`、`<标签名>`、`<属性名>`、`<事件名>`、`<分群名>`、`<项目时区>` 等尖括号内容为占位符，必须替换为已确认的真实标识；机器名占位形态 `user_tag_<名称>` 为派生前缀加占位名称；示例中的具体名称（如 `Order`）仅展示结构，不得沿用。
- 事件、属性、标签、分群引用一律使用元数据或对应查询命令确认过的准确名称与 `data_type`；无法唯一确定时交由调用方消解，不猜测。

## 重要边界

- 不手写最终 Horizon expression；`rule_draft` 交给 CLI Builder 转换。
- 不设置 `skip_rule_check=true`；不自动改名。
- 先按 `--schema` 组装，再用 `sensors tag create --dry-run` 执行服务端业务校验。
- 完整 Definition 模式不重新解释 expression，但仍要经过 dry-run。
