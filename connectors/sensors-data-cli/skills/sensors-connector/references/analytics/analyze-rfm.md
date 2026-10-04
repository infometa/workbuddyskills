# RFM 分析
> 工具 `analysis.rfm` · 命令 `sensors analytics rfm` · 类型 查询

## 用途

按 R（最近一次行为）/ F（频次）/ M（价值）因子做客户价值分层，并查询分层分布。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | RFM 查询输入 JSON；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；必须包含 `group` 与 `rfm_rule`，复杂参数不拆扁平 flag | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅打印转换后的 OpenAPI Request JSON，不发起真实请求；可用于校验默认 `distributions` 补齐结果 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `group` | object | 是 | 结构见下 | RFM 分析的人群范围 | `—` |
| `rfm_rule` | object | 是 | 结构见下 | 因子计算、分层与层级命名规则 | `—` |
| `distributions` | object[] | 否 | 未传或 `[]` 时默认仅查 `RFM` 分布 | 分布查询列表，每项 `{type, show_lines, sort_by, sort_type}` | `—` |
| `sample_factor` | int | 否 | 默认 `64`（全量） | 抽样因子；32 为 1/2、16 为 1/4 采样 | `—` |
| `use_cache` | bool | 否 | 服务端默认 | `false` 强制重新查询 | `—` |
| `time_zone_mode` | string | 否 | 服务端默认 | `CUSTOMER` / `SERVER` | `—` |
| `server_time_zone` | string | 否 | 不传时服务端默认 | 时区偏移，格式 `UTC+HH:MM` | `—` |
| `subject_id` | string | 否 | — | 分析主体 ID，如 `$user_id` / `$device_id` | `—` |

`group`：`group_component_type`（`QUICK_COMPONENT` / `CUSTOMIZED_RULE` / `QUERY_RESULT` / `GROUP_BASED` / `ALL_USER`）+ `rule`（人群规则 Struct，按服务端协议原样透传）。全部用户写 `{"group_component_type": "ALL_USER", "rule": null}`。

`rfm_rule`：

- `rfm_factors[]`：每项 `{factor_type, factor_rule, factor_group_rules}`。
  - `factor_type`：`RECENCY` / `FREQUENCY` / `MONETARY`。**三类因子必须同时提供、缺一不可**——服务端校验任一因子缺失即拒绝（message：`Illegal rfmBasedRule.One of factor is null.`）。
  - `factor_rule.type`：事件指标 `EVENT_MEASURE_BASED`；用户标签 / 用户属性 `PROFILE_BASED`（只填 `rule.field`，不填事件名 / 聚合器 / 时间窗口）。
  - `factor_rule.rule`：事件指标填事件名、过滤、时间范围、聚合字段、聚合器（如 `LAST_TIME_INTERVAL` / `FIRST_TIME_INTERVAL` / `COUNT` / `UNIQUE_COUNT` / `SUM`）。`aggregate_field` 对所有 `EVENT_MEASURE_BASED` 因子必填（含 `FREQUENCY` 的 `COUNT` 聚合），且必须能解析到已注册属性（三段式 `event.<事件>.<属性>`）；为空或未注册报规则不合法错误（message：`Illegal rfmBasedRule...`）。`COUNT` 场景该字段仅参与校验、计数结果不受字段值影响，填该事件任一已注册属性即可。
  - `factor_group_rules[]`：高低分层阈值，每项 `{level, aggregate_function, variable?, value?, unit?}`。`variable: "AVERAGE"` 按均值（不带 `value`）；`variable: "CUSTOM"` 自定义阈值（必须带数值 `value`）；`aggregate_function: "COUNT_RANK_ASC"` / `"COUNT_RANK_DESC"` 按数量升 / 降序 Top 前 N（`value` 为 N，`unit: "COUNT"`）；常用方向为 `LESS_EQUAL` / `GREATER_EQUAL`。
- `layer_params`：RFM 层级编码（如 `"111"`）到展示名的映射。**必须完整覆盖全部 8 个编码键**（`"100"`/`"101"`/`"110"`/`"111"`/`"000"`/`"001"`/`"010"`/`"011"`），缺键或空值会被服务端拒绝（message：`rfmAnalysisRule layerParams is illegal [key=...]`）。

分布 `type` 可选 `RFM` / `R` / `F` / `M` / `RF` / `RM` / `FM`；默认补齐项为 `{type: "RFM", show_lines: [7], sort_by: "COUNT", sort_type: "DESC"}`。以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

校验速记：`group` + `rfm_rule` 必填；R/F/M 三因子缺一不可；`layer_params` 8 键全覆盖；`EVENT_MEASURE_BASED` 因子 `aggregate_field` 必填且须已注册（`COUNT` 也必填）；R 常用 `LESS_EQUAL`（首次 `FIRST_TIME_INTERVAL` / 末次 `LAST_TIME_INTERVAL` 先确认）、F/M 常用 `GREATER_EQUAL`；动态时间必须保留 `range_text`；`variable: "AVERAGE"` 不带 `value`、`"CUSTOM"` 必须带；`distributions` 不传默认仅 RFM 分布。

## 构造流程

目标：把「按 R/F/M 分层」的业务输入翻译为完整请求。人群、R/F/M 指标（事件名、聚合字段、过滤）、时间模式、分层阈值、分布范围未收敛前不构造请求。按五个子节构造：

### 一、`group`：分析人群

全部用户：

```json
{ "group_component_type": "ALL_USER", "rule": null }
```

已有分群（`group_component_type` 用 `GROUP_BASED`；`rule.operator` 通常 `INTERSECT`；`groups[0].type` 用 `PROFILE_FILTER_BASED`；条件函数 `IS_TRUE`；`field` 必须是已确认的分群用户字段，不能把分群名称或分群 ID 当字段）：

```json
{
  "group_component_type": "GROUP_BASED",
  "rule": {
    "operator": "INTERSECT",
    "groups": [
      {
        "type": "PROFILE_FILTER_BASED",
        "profile_user_group": {
          "condition": {
            "operator": "AND",
            "compound_conditions": [
              {
                "operator": "OR",
                "conditions": [
                  {
                    "function": "IS_TRUE",
                    "params": [
                      { "param_type": "FIELD", "field": "user.user_segment_x" }
                    ]
                  }
                ]
              }
            ]
          }
        }
      }
    ]
  }
}
```

### 二、`rfm_rule.rfm_factors[]`：R/F/M 指标

每个因子包含 `factor_type`、`factor_rule`（指标来源）、`factor_group_rules[]`（分层阈值，见下节）。每个 `EVENT_MEASURE_BASED` 因子必须选定一个该事件的已注册属性作为 `aggregate_field`（三段式 `event.<事件>.<属性>`；`COUNT` 聚合同样必填，计数结果不受字段值影响，填任一已注册属性即可）。事件指标常用映射：

| 因子 | 常用聚合器 | 常用字段 | 常用分层方向 |
|---|---|---|---|
| R / 首次距今天数 | `FIRST_TIME_INTERVAL` | `event.<event>.$day` | `LESS_EQUAL`，越小越新 |
| R / 末次距今天数 | `LAST_TIME_INTERVAL` | `event.<event>.$day` | `LESS_EQUAL`，越小越活跃 |
| F / 频次 | `COUNT` 或 `UNIQUE_COUNT` | `event.<event>.$day` | `GREATER_EQUAL`，越大越活跃 |
| M / 金额或价值 | `SUM` | 数值字段，如 `event.<event>.amount` | `GREATER_EQUAL`，越大价值越高 |

R 指标不能默认只按首次或末次：业务说「最近一次、最后一次、末次活跃、距今未访问天数」用 `LAST_TIME_INTERVAL`；明确说「首次、首访、首次完成、首次距今天数」用 `FIRST_TIME_INTERVAL`；无法判断时先向调用方确认。

标签 / 用户属性指标使用 `PROFILE_BASED`，不填事件名、聚合器或时间窗口；字段格式通常是 `user.<tag_or_profile_field>`，必须先确认存在：

```json
{
  "factor_type": "RECENCY",
  "factor_rule": {
    "type": "PROFILE_BASED",
    "rule": { "field": "user.user_tag_chyts" }
  },
  "factor_group_rules": [
    { "level": 1, "aggregate_function": "COUNT_RANK_ASC", "value": 1, "unit": "COUNT" }
  ]
}
```

事件指标的时间模式（`factor_rule.rule.time_range`，与公共 `date_range` 不同：相对时间必须保留 `range_text`，否则丢失「过去 90 天」「截至昨天」的动态滚动语义）：

| 时间模式 | `time_function` | `range_text` | `start_date` / `end_date` |
|---|---|---|---|
| 静态时间 / 固定日期 | `absolute_time` | `""` | 使用指定的固定日期 |
| 动态时间 / 相对日期 | `relative_time` | 保留相对表达，如 `"90 day"`、`"-1 day"` | 按当前查询日解析出的起止日期填写，供服务端校验和展示 |

业务未指定时间模式时，默认建议动态「过去 7 天」：`time_function: "relative_time"`，`range_text: "7 day"`，并按当前查询日解析出对应 `start_date` / `end_date`。

### 三、`factor_group_rules[]`：分层阈值

按平均值分层（业务未指定时的默认建议：R 用 `LESS_EQUAL` + `AVERAGE`，F/M 用 `GREATER_EQUAL` + `AVERAGE`）：

```json
{ "level": 1, "aggregate_function": "GREATER_EQUAL", "variable": "AVERAGE" }
```

自定义阈值分层：

```json
{ "level": 1, "aggregate_function": "LESS_EQUAL", "variable": "CUSTOM", "value": 1 }
```

按排名 Top 前 N 名分层（桌面文案「升序 TOP 前 N 名」）：

```json
{ "level": 1, "aggregate_function": "COUNT_RANK_ASC", "value": 1, "unit": "COUNT" }
```

按排名 Top 前 N 名分层（桌面文案「降序 TOP 前 N 名」）：

```json
{ "level": 1, "aggregate_function": "COUNT_RANK_DESC", "value": 1, "unit": "COUNT" }
```

配套规则：`variable: "AVERAGE"` 不带 `value`；`variable: "CUSTOM"` 必须带数值 `value`；`COUNT_RANK_ASC` / `COUNT_RANK_DESC` 的 `value` 是 N，`unit: "COUNT"` 表示单位为「名」。

### 四、`layer_params`：分层名称

必须完整覆盖 8 个编码键（缺键被服务端拒绝，message：`rfmAnalysisRule layerParams is illegal`）。业务未提供名称时的默认八层映射（编码为 R/F/M 高低标志，`1` 为高）：

```json
{
  "100": "一般发展客户",
  "101": "重点发展客户",
  "110": "一般价值客户",
  "111": "高价值客户",
  "000": "一般挽留客户",
  "001": "重点挽留客户",
  "010": "一般保持客户",
  "011": "重点保持客户"
}
```

### 五、`distributions`：分布查询

不传或传 `[]` 均视为未传，CLI 补默认分布（仅查 RFM）：

```json
[ { "type": "RFM", "show_lines": [7], "sort_by": "COUNT", "sort_type": "DESC" } ]
```

业务未指定时不默认全量展示七类，只建议 `RFM`；明确要看 R / F / M / RF / RM / FM 时才把对应类型写入。构造完成后先 `--dry-run`，确认默认 `distributions` 已补齐再正式执行。

### 调用示例

全部用户 + 动态时间截至昨天（三因子完整请求。事件名与属性名 `activityview` / `$day` / `$receive_time` 均为占位示例，构造真实请求时须替换为已确认的真实事件与已注册属性）：

```bash
sensors analytics rfm --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "group": { "group_component_type": "ALL_USER", "rule": null },
  "rfm_rule": {
    "layer_params": {
      "100": "一般发展客户", "101": "重点发展客户", "110": "一般价值客户", "111": "高价值客户",
      "000": "一般挽留客户", "001": "重点挽留客户", "010": "一般保持客户", "011": "重点保持客户"
    },
    "rfm_factors": [
      {
        "factor_type": "RECENCY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "relative_time",
              "start_date": "2026-05-05",
              "end_date": "2026-08-03",
              "range_text": "90 day"
            },
            "aggregate_field": "event.activityview.$day",
            "aggregator": "FIRST_TIME_INTERVAL"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "LESS_EQUAL", "variable": "AVERAGE" }
        ]
      },
      {
        "factor_type": "FREQUENCY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "relative_time",
              "start_date": "2026-05-05",
              "end_date": "2026-08-03",
              "range_text": "90 day"
            },
            "aggregate_field": "event.activityview.$day",
            "aggregator": "COUNT"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "GREATER_EQUAL", "variable": "AVERAGE" }
        ]
      },
      {
        "factor_type": "MONETARY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "relative_time",
              "start_date": "2026-05-05",
              "end_date": "2026-08-03",
              "range_text": "90 day"
            },
            "aggregate_field": "event.activityview.$receive_time",
            "aggregator": "SUM"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "GREATER_EQUAL", "variable": "AVERAGE" }
        ]
      }
    ]
  },
  "sample_factor": 64
}
__SENSORS_QUERY__
```

已有分群 + 静态时间 + R 自定义阈值（事件与属性名同为占位示例，须替换为已确认的真实事件与已注册属性）：

```json
{
  "group": {
    "group_component_type": "GROUP_BASED",
    "rule": {
      "operator": "INTERSECT",
      "groups": [
        {
          "type": "PROFILE_FILTER_BASED",
          "profile_user_group": {
            "condition": {
              "operator": "AND",
              "compound_conditions": [
                {
                  "operator": "OR",
                  "conditions": [
                    {
                      "function": "IS_TRUE",
                      "params": [
                        { "param_type": "FIELD", "field": "user.user_segment_x" }
                      ]
                    }
                  ]
                }
              ]
            }
          }
        }
      ]
    }
  },
  "rfm_rule": {
    "layer_params": {
      "100": "一般发展客户", "101": "重点发展客户", "110": "一般价值客户", "111": "高价值客户",
      "000": "一般挽留客户", "001": "重点挽留客户", "010": "一般保持客户", "011": "重点保持客户"
    },
    "rfm_factors": [
      {
        "factor_type": "RECENCY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "absolute_time",
              "start_date": "2026-07-01",
              "end_date": "2026-07-07",
              "range_text": ""
            },
            "aggregate_field": "event.activityview.$day",
            "aggregator": "FIRST_TIME_INTERVAL"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "LESS_EQUAL", "variable": "CUSTOM", "value": 1 }
        ]
      },
      {
        "factor_type": "FREQUENCY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "absolute_time",
              "start_date": "2026-07-01",
              "end_date": "2026-07-07",
              "range_text": ""
            },
            "aggregate_field": "event.activityview.$day",
            "aggregator": "COUNT"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "GREATER_EQUAL", "variable": "AVERAGE" }
        ]
      },
      {
        "factor_type": "MONETARY",
        "factor_rule": {
          "type": "EVENT_MEASURE_BASED",
          "rule": {
            "event_name": "activityview",
            "filter": {},
            "time_range": {
              "time_function": "absolute_time",
              "start_date": "2026-07-01",
              "end_date": "2026-07-07",
              "range_text": ""
            },
            "aggregate_field": "event.activityview.$receive_time",
            "aggregator": "SUM"
          }
        },
        "factor_group_rules": [
          { "level": 1, "aggregate_function": "GREATER_EQUAL", "variable": "AVERAGE" }
        ]
      }
    ]
  },
  "sample_factor": 64
}
```

## 输出

不走公共 `columns` / `rows` 结构（见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节），保留专属结构：

| 字段 | 含义 | 示例值 |
|---|---|---|
| `report.total_count` / `rfm_count` / `unknown_count` | 总人数 / 可归入分层人数 / 未归类人数 | `—` |
| `report.total_sum` / `average` 及更新时间字段 | 价值汇总、均值与计算时间 | `—` |
| `distributions[]` | 分布结果列表，每项含 `type` 与 `result.rows`（分层人数 / 占比行） | `—` |
| `request_id` | 请求追踪 ID | `—` |

解读顺序：先看 `report.total_count` / `rfm_count` / `unknown_count` 说明总量与可分层人数；再看 `distributions[type=RFM].result.rows` 解释八类客户分层人数和占比；问单因子看 `R` / `F` / `M` 分布，问组合关系看 `RF` / `RM` / `FM`。

`sample_factor` 非 64 时绝对量级为采样估算，原样传回。

## 错误

| 错误 / 现象 | 后果 | 修正 |
|---|---|---|
| `group` / `rfm_rule` 缺失或校验失败 | 必填对象缺失或结构不符 | 按上述五个子节的结构补齐 |
| 动态时间只写绝对日期，不写 `range_text` | 丢失动态滚动语义 | `time_function: "relative_time"` 时保留 `range_text` |
| R 使用 `GREATER_EQUAL` | 活跃度方向反了 | R 距离越小越高，用 `LESS_EQUAL` |
| R 默认写成首次 | 与业务「末次」选择不一致 | 先确认首次 / 末次；末次用 `LAST_TIME_INTERVAL`，首次用 `FIRST_TIME_INTERVAL` |
| 标签指标仍按事件指标构造 | 多出事件时间和聚合器，参数不匹配 | 标签 / 用户属性用 `PROFILE_BASED`，只填 `rule.field` |
| 服务端规则不合法错误 | 服务端拒绝 RFM 规则；常见触发：R/F/M 任一因子缺失（`Illegal rfmBasedRule.One of factor is null.`）或 `EVENT_MEASURE_BASED` 因子 `aggregate_field` 为空 / 未注册 | 三因子补齐；为每个因子填该事件的已注册属性（三段式 `event.<事件>.<属性>`；`COUNT` 聚合也必填，填任一已注册属性即可） |
| 服务端参数校验失败（message：`rfmAnalysisRule layerParams is illegal [key=...]`，附 `[layerParams=...]` 回显） | `layer_params` 缺编码键或值为空 | 补全全部 8 个编码键 |
| 升序 / 降序 Top 前 N 名写成平均值或自定义阈值 | 分层口径错误 | 升序用 `COUNT_RANK_ASC`，降序用 `COUNT_RANK_DESC`，并带 `value` + `unit: "COUNT"` |
| 服务端报错（因子字段类型不符） | F/M 用非数值字段做 `SUM`，结果失真 | 先确认字段数据类型再构造 |
| `distributions` 传空数组后当作无数据 | 误解 CLI 行为 | 空数组等同未传，CLI 会补默认 `RFM` 分布，按输出解读 |
| `HTTP 504` / 请求超时截断 | `distributions` 多、数据量大，同步链路耗时超过网关 / 超时上限（该查询不走查询缓存） | 减少本次 `distributions` 数量（只留必要项）、传 `sample_factor` 采样（如 32=1/2、16=1/4）、拆成多次调用 |
| SA 版本不满足 | 组件 ≤ 3.0.4.573 | 升级神策组件 |
| 结果为空 | 人群、指标或时间条件无匹配 | 只说明当前查询条件下无结果，不擅自换事件、放宽时间或改阈值重试 |

## 使用约束

- 人群字段、标签字段、事件名必须已确认，不得猜测；分层阈值与层级命名等业务口径由调用方给定。
- 阈值规则按 `variable` / `aggregate_function` 的配套约束构造（`AVERAGE` 不带 `value`、`CUSTOM` 必带、排名分层带 `value` + `unit: "COUNT"`）。
- 空结果只说明当前查询条件下无结果，不得擅自换事件、放宽时间或改阈值重试。
- RFM 查询为同步链路且不走查询缓存，一次调用串行执行主分析与每个分布各一条查询，耗时随 `distributions` 数量和数据量增加；构造时只保留必要分布项，数据量大时传 `sample_factor` 采样或拆成多次调用，避免单次请求被超时截断。
