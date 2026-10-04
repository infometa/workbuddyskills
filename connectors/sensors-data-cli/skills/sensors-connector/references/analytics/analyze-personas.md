# 用户群画像分析
> 工具 `analysis.personas` · 命令 `sensors analytics personas-report` · 类型 查询

## 用途

查询人群在画像卡片（标签属性分布 / 属性交叉分布 / 行为指标分布，可含 TGI）上的画像报告。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径；输入字段名须与 `PersonasAnalyseReportRequest` 一致，无 CLI 别名 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 顶层只含 `analysis`（必填对象）与 `use_cache`（bool，可选）。`analysis` 字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `group_configs` | object[] | 是 | 至少 1 项，一次请求只能放 1 项 | 人群配置，见下 | `—` |
| `widget_configs` | object[] | 是 | 至少 1 项，一次请求只能放 1 项 | 画像卡片配置，见下 | `—` |
| `tgi` | bool | 否 | — | 是否查询 TGI；只用布尔值，不写 `"true"` / `"false"` 字符串 | `false` |
| `tgi_base_user_group_config` | object | 否 | 结构见下 | TGI 基准人群配置；`tgi: true` 必须带，`tgi: false` 不传 | `—` |
| `sample_factor` | int | 否 | — | 抽样系数，通常 `64` 表示全量 | `64` |
| `id` / `display_name` / `user_name` / `account_id` / `create_time` / `latest_report` | — | 否 | — | 报告元信息，透传 | `—` |
| `request_id` | string | 否 | — | CLI 自动注入，无需手填 | `—` |

`group_configs[]`：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `group_id` | string | 是 | 人群 ID（已有用户分群或规则人群的唯一标识） | `rule_update_time_set` |
| `group_type` | string | 是 | 人群类型英文枚举（可理解为目标人群 / 对比人群 / TGI 基准人群） | `TARGET_GROUP` |
| `group_name` | string | 否 | 人群展示名 | `更新时间有值人群` |
| `group_component_type` | string | 否 | 人群来源类型英文枚举（已有分群 / 规则设置等） | `EQL_RULE` |
| `user_group_rule` | object | 否 | 规则人群的规则对象，按服务端协议 Struct 原样透传 | `—` |
| `query_request` / `query_type` / `template_data` / `rule_ext` | — | 否 | 上游服务定义的结构，原样透传 | `—` |
| `sql_encode` | bool | 否 | SQL 是否已加密 | `—` |
| `group_missed` | bool | 否 | 人群是否已失效 | `—` |

`widget_configs[]`：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `widget_id` | string | 是 | 画像卡片 ID；已有配置必须保留，临时构造也要稳定，不要每次随机变化 | `widget_tag_user_tag_1` |
| `type` | string | 是 | 卡片类型英文枚举：单属性分布用 `USER_TAG_DISTRIBUTION`，属性交叉分布、行为指标分布等用平台对应枚举 | `USER_TAG_DISTRIBUTION` |
| `request` | object | 否 | 按卡片类型定义的查询对象（如 `{"by_fields": ["user.$update_time"]}`），Struct 透传 | `{"by_fields":["user.user_tag_1"]}` |
| `widget_name` / `chart_type` / `row_index` / `group_ids` | — | 否 | 展示名 / 图类型（无特别要求通常 `column`）/ 行序号 / 关联人群 ID 列表 | `标签user_tag_1分布` / `column` / `—` / `["rule_update_time_set"]` |

`tgi_base_user_group_config`：`type`（必填，基准人群类型，如 `ALL_USER`）、`user_group_rule` / `rule_ext`（可选透传）。

人群规则与卡片查询对象的完整业务结构由上游服务定义，CLI 不做字段级校验、原样透传；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

目标：把「某人群的某画像卡片」业务输入翻译为合法请求。人群与卡片未收敛前不构造请求；多人群 / 多卡片按笛卡尔积拆多次执行。

### 第一步：定人群与卡片范围

明确目标人群、是否需要对比人群、要看的画像卡片类型、是否开启 TGI。人群构建有两种方式：使用已有用户分群（依赖项目内已物化的分群字段，先经 `metadata.fields` 确认字段存在与精确名称，是否存在因项目而异），或按规则临时构建人群（用户属性 / 事件 / 行为序列 / 分群条件组合）。项目内无可用分群字段时，规则人群（EQL_RULE）是表达同等人群的推荐路径。

### 第二步：构造 `group_configs`（先分两大类）

一次请求只放 1 个人群配置。

#### 一类：根据已有用户分群筛选

对应「用某个已有分群做画像」（如「看高价值用户分群的画像」）。构造规则：

- `group_component_type` 用 `GROUP_BASED`；`user_group_rule` 与 `user_group_rule.groups` 必传。
- `groups[0].type` 用 `PROFILE_FILTER_BASED`；条件函数用 `IS_TRUE`。
- `field` 依赖项目把分群物化为用户属性（虚拟字段，形如 `user_segment_` 前缀、每个分群一个，是否存在因项目而异）：先经 `metadata.fields`（schema `users`）确认项目内是否存在可用分群字段，存在则用确认到的精确字段名；分群内部名先经 `segment.list` / `segment.get` 确认。不能把 `segment_id` 或分群展示名当 `field`；项目无可用分群字段时本路径不可用，改用「二类」规则人群（EQL_RULE）表达同等人群，或用 `segment.get` 展开分群规则自行构造。
- 未显式指定分群版本时默认按最新版本字段处理；指定固定历史版本时字段带 `@YYYY-MM-DD HH:mm:ss`。

```json
{
  "group_id": "seg_xxx",
  "group_name": "高价值用户",
  "group_type": "TARGET_GROUP",
  "group_component_type": "GROUP_BASED",
  "user_group_rule": {
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
                          { "param_type": "FIELD", "field": "<已确认的分群字段>" }
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

#### 二类：根据规则设置的人群

对应「按规则现拼一个画像人群」（如「最近 7 天下单过但未退款」）。构造规则：

- 常用 `group_component_type` 为 `EQL_RULE`；上游已有稳定旧规则对象时也可能是 `CUSTOMIZED_RULE`。
- `user_group_rule.groups[]` 中每条规则落为一个 `EQL_BASED`；多条规则之间通过 `group_expression` 组合（如 `"\"$1\"+\"$2\""`）。

```json
{
  "group_id": "rule_xxx",
  "group_name": "规则人群",
  "group_type": "TARGET_GROUP",
  "group_component_type": "EQL_RULE",
  "user_group_rule": {
    "type": "GROUP_EXPRESSION_BASED",
    "group_expression_rule": {
      "groups": [
        {
          "type": "EQL_BASED",
          "eql_segment_rule": { "eql": "(user.device_type in ['desktop'])" }
        }
      ],
      "group_expression": "\"$1\""
    }
  }
}
```

规则人群按条件类型细分四类，EQL 常见映射：

| 规则类型 | 常见 EQL 写法 |
|---|---|
| 属性规则 | 等于：`user.city == 'Shanghai'`、`user.device_type in ['desktop']`；不属于：`not(user.$first_utm_source in ['8'])`；有值 / 无值：`user.$update_time.is_not_null()` / `user.$first_utm_term.is_null()`；字符串空 / 非空：`user.$first_utm_content == ''`；数值区间：`user.$update_time >= 1 and user.$update_time <= 2`；正则：`user.$latest_utm_content.rlike('*')` |
| 事件规则 | 发生过：`user.$Events.$AppInstall.filter_event(start, end).count() >= 1`；未发生：`...count() <= 0 or ...count().is_null()`；次数区间：`count() >= 1 and count() <= 2`；带事件属性过滤：`user.$Events.$AppInstall.filter_event(start, end, (user.$Events.$AppInstall.$idmap_reason.is_not_null())).count() > 0` |
| 行为序列规则 | 用 `EVENT_SEQUENCE_BASED` 结构（见下）；事件步骤 `event_name` 必须用实体事件路径（如 `user.$Events.$AppClick`）；相对时间必须展开成确定表达式（如 `datetime_add(${var:base_time}, -1, 'DAY')`），不把口语直接写成字符串 |
| 分群规则 | 属于某分群：`user.$SegmentMembership.<已确认的分群字段名> == true`；分群字段名先经 `metadata.fields` 确认（形如 `user_segment_` 前缀，是否存在因项目而异），不直接写 `seg_xxx` |

行为序列规则完整示例（`$update_time` 有值，且最近 1 天内连续两次 App 元素点击）：

```json
{
  "group_id": "rule_update_time_set_appclick_sequence",
  "group_name": "更新时间有值且发生 App 元素点击序列人群",
  "group_type": "CONTROL_GROUP",
  "group_component_type": "EQL_RULE",
  "user_group_rule": {
    "type": "GROUP_EXPRESSION_BASED",
    "group_expression_rule": {
      "groups": [
        { "type": "EQL_BASED", "eql_segment_rule": { "eql": "user.$update_time.is_not_null()" } },
        {
          "type": "EVENT_SEQUENCE_BASED",
          "event_sequence_rule": {
            "operator": "INTERSECT",
            "simple_event_sequences": [
              {
                "time_range": {
                  "start_time": {
                    "type": "RELATIVE",
                    "trunc_unit": "TRUNC_DAY",
                    "relative_time": { "time_interval": { "size": -1, "unit": "DAY" } }
                  },
                  "end_time": {
                    "type": "RELATIVE",
                    "trunc_unit": "TRUNC_DAY",
                    "relative_time": { "time_interval": { "size": 0, "unit": "DAY" } }
                  }
                },
                "event_steps": [
                  { "event_name": "user.$Events.$AppClick", "condition": { "operator": "AND", "conditions": [] } },
                  { "event_name": "user.$Events.$AppClick", "condition": { "operator": "AND", "conditions": [] } }
                ]
              }
            ]
          }
        }
      ],
      "group_expression": "\"$1\"+\"$2\""
    }
  },
  "rule_ext": { "ext_type": "EQL_RULE_V1", "schema_version": 1, "editor": "segment-rule" }
}
```

行为序列静态时间片段（`static_time` 使用 RFC 3339 UTC 时间，仅 `time_range` 部分）：

```json
{
  "time_range": {
    "start_time": { "type": "STATIC", "static_time": "2026-06-30T16:00:00.000Z" },
    "end_time": { "type": "STATIC", "static_time": "2026-07-07T16:00:00.000Z" }
  }
}
```

同时包含属性规则与行为序列规则时，把属性规则放进独立的 `EQL_BASED` 规则组，再用 `group_expression` 与行为序列规则组做交集。

### 第三步：构造 `widget_configs`（按卡片类型分三类）

一次请求只放 1 个卡片配置。通用规则：`widget_name` 直接表达卡片含义；`chart_type` 无特别要求用 `column`；`request` 内的 `by_fields`、`measures[].field`、事件名和过滤条件必须来自已确认元数据；默认不传 `row_index`、`widget_time_range`、`show_line_num`、`sort_by`、`sort_type`、`use_cache`。

| 业务意图 | `type` | 关键 `request` 字段 |
|---|---|---|
| 标签属性分布（城市、会员等级、首次来源等单字段） | `USER_TAG_DISTRIBUTION` | `by_fields` / `measures` / `filter` |
| 两个用户属性交叉分布（省份 X 城市） | `USER_PROPERTY_DISTRIBUTION` | `by_fields` 必须传两个字段 |
| 用户行为指标分布（时间范围内支付次数 / 金额分布） | `MEASURES_DISTRIBUTION` | `event_name` / `measure_type` / 时间相关字段 |

人数统计卡片 `request.measures[]` 固定使用 `{"aggregator": "count", "field": ""}`，`field` 必须是空字符串，不要拿 `user.$id` 或别的字段凑数。

`USER_TAG_DISTRIBUTION` 最小模板：

```json
{
  "widget_id": "widget_tag_xxx",
  "widget_name": "首次广告系列名称的分布",
  "type": "USER_TAG_DISTRIBUTION",
  "chart_type": "column",
  "request": {
    "bucket_params": {},
    "by_fields": ["user.$first_utm_campaign"],
    "filter": {},
    "measures": [{ "aggregator": "count", "field": "" }]
  }
}
```

`USER_PROPERTY_DISTRIBUTION` 最小模板（`by_fields` 传两个字段；单属性分布不用本类型，改 `USER_TAG_DISTRIBUTION`）：

```json
{
  "widget_id": "widget_prop_cross_xxx",
  "widget_name": "首次广告系列名称 X 首次搜索关键词的交叉分布",
  "type": "USER_PROPERTY_DISTRIBUTION",
  "chart_type": "column",
  "request": {
    "bucket_params": {},
    "by_fields": ["user.$first_utm_campaign", "user.$first_utm_term"],
    "filter": {},
    "measures": [{ "aggregator": "count", "field": "" }]
  }
}
```

`MEASURES_DISTRIBUTION` 最小模板（必须能明确对应到真实事件和行为口径，不能只凭展示名猜）：

卡片 `request` 的时间写法只有两种合法枚举：动态相对时间 `time_function: "relative_time"` + `time_params: ["1 day"]`；固定日期区间 `time_function: "absolute_time"` + `time_params: ["<yyyy-MM-dd>", "<yyyy-MM-dd>"]`（起止两个日期，同一天则两项相同）。不存在 `custom_time` 等其它枚举，写错会被服务端以 `FILTER_FUNCTION_INVALID` 拒绝。用户给出明确日期范围时必须用 `absolute_time`。

```json
{
  "widget_id": "widget_measure_xxx",
  "widget_name": "完成到店总次数的行为分布",
  "type": "MEASURES_DISTRIBUTION",
  "chart_type": "column",
  "request": {
    "event_name": "arrival",
    "filter": {},
    "measure_type": "times",
    "result_bucket_param": null,
    "rollup_date": true,
    "sampling_factor": 64,
    "time_function": "absolute_time",
    "time_params": ["2026-06-01", "2026-06-09"],
    "unit": "day"
  }
}
```

### 第四步：定 TGI（只在明确要差异 / 偏好强弱时开启）

- `analysis.tgi = true` 推荐显式提供 `tgi_base_user_group_config`；未提供时服务端按全体用户（`ALL_USER`）作为隐式基准，为避免歧义建议始终显式声明；`tgi = false` 不传基准。
- 只看普通画像分布、人群本身占比或人数时不开启 TGI；不要把目标人群本身同时当作基准人群。
- 基准人群四类：全体用户 `{ "type": "ALL_USER" }`（默认基准，`type = "ALL_USER"` 时不传 `user_group_rule`）；已有分群基准 `{ "type": "GROUP_BASED", ... }`（复用「根据已有分群筛选」同一模板，`field` 仍是经 `metadata.fields` 确认的实际分群字段）；规则筛选基准 `{ "type": "EQL_RULE", ... }` / `{ "type": "CUSTOMIZED_RULE", ... }`（与规则人群构造一致）。

### 第五步：按笛卡尔积拆请求

多人群 `[A, B]` × 多卡片 `[a, b]` 必须拆成 4 次独立请求（`A+a`、`A+b`、`B+a`、`B+b`），不能合并进同一次 request；各次结果返回后再合并解释，不只依据某一次结果下总判断。

### 第六步：自检并执行

每个拆分后的请求先 `--dry-run` 确认请求体，再正式执行。

### 调用示例

最小可用请求（`user_group_rule.groups` 必传且不能为空列表，`field` 用经 `metadata.fields` 确认的分群字段占位）：

```bash
sensors analytics personas-report --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "analysis": {
    "sample_factor": 64,
    "tgi": false,
    "group_configs": [
      {
        "group_id": "seg_target",
        "group_name": "目标人群",
        "group_type": "TARGET_GROUP",
        "group_component_type": "GROUP_BASED",
        "user_group_rule": {
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
                            { "param_type": "FIELD", "field": "user.<已确认的分群字段>" }
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
    ],
    "widget_configs": [
      {
        "widget_id": "widget_city",
        "widget_name": "更新时间分布",
        "type": "USER_TAG_DISTRIBUTION",
        "request": { "by_fields": ["user.$update_time"] },
        "group_ids": ["seg_target"]
      }
    ]
  },
  "use_cache": true
}
__SENSORS_QUERY__
```

带 TGI 的请求（全体用户基准）：

```bash
sensors analytics personas-report --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "analysis": {
    "sample_factor": 64,
    "tgi": true,
    "group_configs": [
      {
        "group_id": "seg_target",
        "group_name": "目标人群",
        "group_type": "TARGET_GROUP",
        "group_component_type": "GROUP_BASED",
        "user_group_rule": {
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
                            { "param_type": "FIELD", "field": "user.<已确认的分群字段>" }
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
    ],
    "widget_configs": [
      {
        "widget_id": "widget_city",
        "widget_name": "更新时间分布",
        "type": "USER_TAG_DISTRIBUTION",
        "request": { "by_fields": ["user.$update_time"] },
        "group_ids": ["seg_target"]
      }
    ],
    "tgi_base_user_group_config": { "type": "ALL_USER" }
  }
}
__SENSORS_QUERY__
```

## 输出

不走公共 `columns` / `rows` 结构（见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节），保留专属结构：

| 字段 | 含义 | 示例值 |
|---|---|---|
| `group_id` / `widget_id` | 本次结果对应的人群 ID / 卡片 ID | `rule_update_time_set` / `widget_tag_user_tag_1` |
| `widget_time_ranges` | 卡片时间范围列表 | `[]` |
| `data.report_update_time` / `data_sufficient_update_time` / `data_update_time` | 报告更新 / 数据充足 / 数据更新时间（固定返回） | `2026-09-27 13:09:46` |
| `data.count` | 当前卡片结果总量 | `1.0` |
| `data.detail_result.sampling_factor` | 抽样系数（64=全量） | `64` |
| `data.detail_result.total_people` | 行为分布场景总人数 | `0` |
| `data.detail_result.rows` | 图表明细行列表 | `[{"sort_id":2,"by_values":["一般"],"values":[[1.0]]}]` |
| `request_id` | 请求追踪 ID | `4d2d6e05ceca414ca5546e29460830da` |

`rows` 普通行字段按卡片类型返回：`sort_id`、`by_values` / `encrypted_by_values`（维度值数组）、`values`（表格值数组）、`by_value` / `encrypted_by_value`（行为分布单维度值）、`user_tag_event_total`（恒返回；非目标场景未计算时为默认值 `0.0`）；`people` / `percent` 仅 `MEASURES_DISTRIBUTION` 且非 TGI 的行为分布行返回。**TGI 模式下 `values` 每项为 4 元素数组**（目标组人数、目标组总人数、基准组人数、基准组总人数两组口径），非 TGI 为 1 元素。「行为分布（`MEASURES_DISTRIBUTION`）+ TGI」行还会额外返回 `user_tag_event_user_cnt` / `profile_event_user_cnt`（目标组 / 基准组命中人数）与 `user_tag_user_cnt` / `profile_user_cnt`（目标组 / 基准组总人数）；属性分布等其他场景不返回这 4 个字段。

结构性读法：

- `USER_TAG_DISTRIBUTION` / `USER_PROPERTY_DISTRIBUTION`：重点看 `by_values` 与 `values`。
- `MEASURES_DISTRIBUTION`：重点看 `by_value`、`people`、`percent`。
- TGI 行：先说明目标组与基准组分别是谁，再解释差异；`user_tag_user_cnt` / `profile_user_cnt` 不要当作普通画像人数输出；行里只有目标组人数、没有基准组字段时不硬下 TGI 结论。
- 行内只有加密字段（`encrypted_by_values` 等）时，不要自行猜测维度值含义。
- `rows` 为空时不编造画像结论；`sampling_factor != 64` 时绝对量级按采样估算口径解释。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `group_configs 不能为空列表` | 没给人群配置 | 至少 1 项（一次 1 项） |
| `widget_configs 不能为空列表` | 没给卡片配置 | 至少 1 项（一次 1 项） |
| `group_id` / `group_type` / `widget_id` / `type 不能为空字符串` | 关键字段空白 | 填已确认的精确标识 |
| 分群字段错误 / 属性不存在或失效 | 把 `segment_id` 或分群展示名直接当用户字段，或项目未把分群物化为用户属性、字段名未经确认 | 先 `metadata.fields`（schema `users`）确认可用分群字段，用确认到的精确字段名重构；无可用字段时改用规则人群（EQL_RULE）路径 |
| 规则类型混淆 | 把已有分群筛选误写成 EQL，或把规则中的分群条件误写成 `PROFILE_FILTER_BASED` | 先判断是「已有分群筛选」还是「规则筛选中的分群条件」 |
| 人数统计卡片结果异常 | `request.measures[].field` 传了非空字段 | 改成 `{"aggregator": "count", "field": ""}` |
| 交叉分布只用了一个属性 | `USER_PROPERTY_DISTRIBUTION` 的 `by_fields` 不足两个字段 | 补两个字段，或单属性改用 `USER_TAG_DISTRIBUTION` |
| 服务端校验失败（人群 / 卡片结构） | `user_group_rule`、`request` 结构不符合服务端协议 | 按错误提示修正透传结构 |
| TGI 基准为隐式全体用户 | `tgi: true` 未带 `tgi_base_user_group_config` | 服务端默认全体用户基准（不报错）；为避免歧义建议显式补齐基准人群配置 |
| 服务端参数校验异常（error_cause「参数为空」） | `user_group_rule.groups` 传空列表 | `groups` 必传且至少 1 项完整规则条目 |
| SA 版本不满足 | 组件 ≤ 3.0.4.573 | 升级神策组件 |
| 返回为空 | 人群规则或卡片条件无匹配数据 | 检查人群规则和卡片 `request` 是否精确；是否调整由调用方决定 |

## 使用约束

- 一次请求 `group_configs` 与 `widget_configs` 各只能放 1 项；多人群 / 多卡片须拆成多次请求，由调用方合并。
- 人群 ID、分群字段、卡片 ID 等标识必须已确认，不得猜测；行内只有加密字段时不得猜测维度值含义。
- 分群字段的存在性因项目而异（取决于项目是否把分群物化为用户属性），未经 `metadata` 确认不得引用；无可用分群字段时用规则人群（EQL_RULE）表达同等人群。
- `sampling_factor != 64` 时绝对量级为采样估算；`rows` 为空时不产出画像结论。
- 本命令服务画像语义；普通属性分组统计转 `user-property`，数值区间分布转 `distribution`，由调用方决定。
