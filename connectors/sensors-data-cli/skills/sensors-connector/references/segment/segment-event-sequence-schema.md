# 行为序列输入 Schema（event-sequence-schema）

> 供 `segment.create` / `segment.update` 的 `rule_draft` 中 `event_sequence` 条件引用，描述 step 结构、操作符与时间窗口约束。结构最终事实源：`sensors segment create --schema`。通用字段语义见 [segment-rule-schema.md](segment-rule-schema.md)。

## 条件结构

`event_sequence` 是 `conditions[].type` 的一种，只能用于 `create_type=CUSTOMIZED_RULE`。完整 Draft 示例：

```json
{
  "segment_definition": {"name": "<分群名>", "display_name": "<展示名>", "trigger": {"trigger_type": "MANUAL"}},
  "rule_draft": {
    "create_type": "CUSTOMIZED_RULE",
    "rule": {
      "relation": "AND",
      "conditions": [
        {
          "type": "event_sequence",
          "steps": [
            {"id": "s1", "event_name": "<事件名1>"},
            {"id": "s2", "event_name": "<事件名2>", "filters": [{"field": "<属性名>", "data_type": "NUMBER", "operator": "GTE", "value": 1000}]}
          ],
          "window": {"unit": "DAY", "value": 14}
        }
      ]
    }
  }
}
```

`event_sequence` 含三个字段：`type`（固定 `"event_sequence"`）、`steps`（按顺序排列的事件步骤数组）、`window`（完成整个序列允许的最大时间跨度，同时用作数据查询的回溯窗口）。

## 业务输入到结构的映射

- 业务语言中的顺序描述（先、再、之后、随后、连续完成）→ 有序 `steps`，数组顺序即行为发生顺序，不得重排。
- "N 天内 / N 小时内" 这类窗口 → `window`（`unit` + `value`）；`window` 必填，业务输入未给出窗口时无法组装合法 Draft。
- 某一步事件上的条件（如"支付金额 ≥ 1000 的支付"）→ 该步骤的 `filters`，只作用于该步事件属性。
- 至少两个步骤；只有单个事件的"序列"不是 `event_sequence`，用 `event_occurrence` 等普通条件表达。
- 放入 `EQL` 创建类型的条件树属于结构错误：`event_sequence` 不能渲染为 EQL。

## steps（有序事件步骤）

| 字段 | 类型 | 约束 | 示例值 |
| --- | --- | --- | --- |
| `steps[].id` | string | 步骤唯一标识，非空且不重复；用于明确并保持序列顺序 | `s1` |
| `steps[].event_name` | string | 事件名，使用已确认的真实标识 | `sa_query_analytics` |
| `steps[].filters` | array | 该步骤事件必须满足的属性过滤，可省略；结构见下「step 过滤操作符」 | `[{"field":"v_xunipingmukuandu","operator":"GTE","value":1000}]` |

约束：

- `steps` 至少包含两个步骤（CLI 校验 `event_sequence requires at least two steps`）；数组顺序即行为发生顺序，不得重排。
- 每个 step 的事件名、step `filters` 中的属性与枚举值都必须逐一经元数据查询确认真实存在。
- `filters` 只作用于当前 step 的事件属性，不能承载用户属性条件；已在其他条件表达过的过滤不要再写入 step `filters`（会造成双重过滤）。

## window（时间窗口）

| 字段 | 类型 | 约束 | 示例值 |
| --- | --- | --- | --- |
| `window.unit` | `HOUR` \| `DAY` \| `WEEK` \| `MONTH` \| `YEAR` | 窗口单位 | `DAY` |
| `window.value` | int | 正整数；序列完成的最大时间跨度，同时作为数据查询的回溯窗口 | `14` |

窗口的双重语义（命令层事实）：Builder 用 `window` 生成"从执行时间向前回溯 `value` 个 `unit`"的序列查询范围（起点 `-value`、终点当前），并作为所有步骤完成的最大时间跨度。`{"unit": "DAY", "value": 14}` 表示"在过去 14 天的数据范围内，事件按 step 顺序全部发生"。

- `event_sequence` 条件内没有独立的 `time_range` 字段；"过去 N 天"这类相对窗口只能通过 `window` 表达，写入 `time_range` 属于结构错误。
- step 之间的间隔约束（如"step1 完成后 7 天内完成 step2"）没有对应的 Draft 字段，当前结构无法表达；序列仅有整体 `window`，不得为间隔要求伪造字段。

## step 过滤操作符

`steps[].filters[]` 使用 `field` / `data_type` / `operator` / `value` 契约，但**只支持以下 8 个操作符**，不能臆造其他操作符：

| operator | 语义 | value 要求 | 常用 data_type |
| --- | --- | --- | --- |
| `EQ` | 等于 | 必填，与 `data_type` 匹配 | STRING / NUMBER |
| `NEQ` | 不等于 | 必填 | STRING / NUMBER |
| `GT` / `GTE` / `LT` / `LTE` | 大于 / 大于等于 / 小于 / 小于等于 | 必填，数字字面量 | NUMBER |
| `IS_NULL` / `IS_NOT_NULL` | 属性为空 / 有值 | 必须省略 | 全部 data_type |

要点：

- 通用过滤的其余操作符（`IN`、`NOT_IN`、`BETWEEN`、`CONTAINS`、`LIKE`、`RLIKE`、`STARTS_WITH` 等）用于 step 过滤会被 CLI 拒绝（`unsupported event_sequence step filter operator`）；需要这些操作符的属性条件应放到普通事件条件的 `filters`，而不是 step 内。
- `value` 类型必须与 `data_type` 一致：`NUMBER` 用数字字面量（如 `1000`），`STRING` 用字符串（如 `"product_detail"`），`BOOL` 用布尔值，`DATE` / `DATETIME` 用字符串；不能用字符串代替数字，反之亦然。
- `IS_NULL` / `IS_NOT_NULL` 适用于 STRING、NUMBER、BOOL、DATE、DATETIME 各类 `data_type`，不仅限字符串；其 `value` 必须省略的完整规则见 [segment-rule-schema.md](segment-rule-schema.md)「空值判断」。
- `data_type` 必须来自元数据查询的真实类型，不能根据字面值猜测；判断"订单金额 ≥ 1000"时金额属性属于事件属性，不要误当用户属性。

```json
[
  {"field": "<金额属性名>", "data_type": "NUMBER", "operator": "GTE", "value": 1000},
  {"field": "<来源属性名>", "data_type": "STRING", "operator": "EQ", "value": "<枚举值>"},
  {"field": "<名称属性名>", "data_type": "STRING", "operator": "IS_NOT_NULL"}
]
```

## 组合约束

- `event_sequence` 只能出现在 `CUSTOMIZED_RULE` 条件树的顶层 `conditions`；放入嵌套条件组会被 CLI 拒绝（`nested event_sequence groups are not supported`）。如需多层条件嵌套，把所有条件提升到顶层 `conditions`，用 `AND` / `OR` 组合。
- 同层混合：顶层 `conditions` 可同时放置 EQL 条件（`user_attribute`、`event_occurrence` 等）与 `event_sequence`，CLI 按顶层 `relation` 生成 `"$1" * "$2"`（AND）或 `"$1" + "$2"`（OR）的人群组表达式；含 `event_sequence` 的混合规则不支持 `NOT` 关系。
- 不要在 step `filters` 中重复表达已在其他条件中表达的用户属性过滤（如 VIP 等级阈值），这会导致双重过滤。
- 不把行为序列手写为最终 `EVENT_SEQUENCE_BASED` expression；交给 Builder 生成。
- 不省略用户明确给出的顺序和时间窗口；时间约束用 `window` 相对表达，Draft 中没有写死具体日期的位置。

同层混合示例（"<用户属性> ≥ 2 且 过去 30 天内先 <事件1> 后 <事件2>"）：

```json
{
  "rule": {
    "relation": "AND",
    "conditions": [
      {"type": "user_attribute", "field": "<用户属性名>", "data_type": "NUMBER", "operator": "GTE", "value": 2},
      {"type": "event_sequence",
       "steps": [{"id": "s1", "event_name": "<事件名1>"}, {"id": "s2", "event_name": "<事件名2>"}],
       "window": {"unit": "DAY", "value": 30}}
    ]
  }
}
```

## 占位符与标识约定

- 示例中 `<事件名1>`、`<事件名2>`、`<属性名>` 等尖括号内容为占位符，必须替换为已确认的真实标识；不得沿用示例名称。
- 序列中每个事件、step 过滤属性及枚举值都必须逐一确认真实存在；无法唯一确定时交由调用方消解，不猜测。
