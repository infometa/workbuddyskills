# Analytics 公共输入/输出契约

本文件是 `sensors analytics` 标准分析命令共享的纯 Schema 契约：字段路径、过滤树、聚合器、日期范围、结构化调用方式、公共输出结构与完整性标记。各工具专属字段见同目录对应工具文件；业务问题拆解、模型选择与结果解释由调用方决定。

与 CLI 实际行为不一致时，以目标命令的实时 `--help` 与 `--dry-run` 请求预览为最终事实源。

## 字段路径

字段使用完整路径，不使用裸字段名：

- 事件字段：`event.<event_name>.<property>` 三段式，例如 `event.order_pay.amount`。
- 用户字段：`user.<property>`，例如 `user.country`。
- 事件时间：`event.<event_name>.$time`。`$time` 是内置字段，元数据中不出现，需要按事件时间分组或过滤时显式填写。

禁止使用 `$ip`、`event.$ip`、`orderPay.$lib` 等不完整路径。两个模型级变体：

- 事件分析的分组字段归一化为通配形式 `event.$Anything.<property>`（见 [analyze-events.md](analyze-events.md)）。
- 留存分析的事件过滤/分组字段使用 `first.*` / `second.*` 简写前缀，转换时自动展开（见 [analyze-retention.md](analyze-retention.md)）。

标识确认顺序：构造查询对象前逐项核对命名是否精确——事件名 → 聚合 `field` → 过滤条件的 `field` 与 `params` 枚举值 → 分组/拆分字段。单一明确匹配即可继续；多候选不得自行二选一，交还调用方确认；零匹配如实告知「未找到」，不编造。口语描述（「提交订单」「来源」）一律先确认为精确标识再构造查询对象。

## 过滤树

叶子条件统一使用 `field` / `function` / `params` 三段式：

```json
{ "field": "user.country", "function": "equal", "params": ["CN"] }
```

`function` 枚举：

| `function` | 含义 | `params` |
|---|---|---|
| `equal` / `notEqual` | 等于 / 不等于；多值表示集合匹配（IN / NOT IN） | 必填、非空 |
| `contain` / `notContain` | 包含 / 不包含子串 | 必填、非空 |
| `rlike` | 正则匹配 | 必填、非空 |
| `greater` / `greaterEqual` | 大于 / 大于等于 | 必填、非空 |
| `less` / `lessEqual` | 小于 / 小于等于 | 必填、非空 |
| `isSet` | 有值 | 不传（必须为空） |
| `isTrue` / `isFalse` | 布尔为真 / 为假 | 不传（必须为空） |

不使用历史写法 `op`、`values`、`in`、`not_in`；集合匹配用 `equal` / `notEqual` 传多值，例如 `{"function": "equal", "params": ["军工", "机械"]}`。`isSet` / `isTrue` / `isFalse` 带 `params`、其余 `function` 缺空 `params` 都会被 CLI 校验拒绝。

递归过滤树节点使用单数 `filter`：

```json
{
  "relation": "and",
  "conditions": [
    { "field": "event.payOrder.$lib", "function": "equal", "params": ["python"] }
  ],
  "filters": [
    {
      "relation": "or",
      "conditions": [
        { "field": "user.country", "function": "equal", "params": ["CN", "SG"] }
      ]
    }
  ]
}
```

- `relation` 输入层只接受小写 `and` / `or`（大写会被校验拒绝）；CLI 内部按需转换大小写传给接口，调用方无需关心。
- `conditions` 是叶子条件数组；`filters` 是子过滤树数组，用于嵌套。
- 每个节点至少包含非空的 `conditions` 或 `filters` 之一，不允许空节点。
- 模型若区分事件过滤与用户过滤，分别放入 `filter` 与 `user_filter`（如分布、路径）；不要把 `user.*` 混进事件 `filter`。

## 聚合器

| 业务口径 | `aggregator` | `field` |
|---|---|---|
| 次数 / PV | `general` | 不允许填 |
| 人数 / UV | `unique` | 不允许填 |
| 人均次数 | `average` | 不允许填 |
| 求和 | `sum` | 必填三段式字段路径 |
| 均值 | `avg` | 必填三段式字段路径 |
| 最大值 / 最小值 | `max` / `min` | 必填三段式字段路径 |

- `distinct_count` 仅用于兼容旧输入，转换时归一化为 `unique`；新查询直接用 `unique`，不要拼 `uniqCount` 等变体。
- LTV 的价值事件使用专属口径 `average` / `LTV_AVG`，不在本表范围（见 [analyze-ltv.md](analyze-ltv.md)）。

## 日期范围

公共 `date_range` 对象：

```json
{ "from_date": "2026-06-01", "to_date": "2026-06-07", "timezone": "" }
```

| 字段 | 必填 | 约束 | 示例值 |
|---|---|---|---|
| `from_date` | 是 | `yyyy-MM-dd`，须为合法日历日期 | `2026-09-20` |
| `to_date` | 是 | `yyyy-MM-dd`，不得早于 `from_date` | `2026-09-26` |
| `timezone` | 否 | 空=项目默认时区；`CUSTOMER`=客户端时区；`UTC±HH:MM` 偏移或合法 IANA 时区名（如 `Asia/Shanghai`） | `""` |

相对时间（"最近 7 天"）必须先换算为绝对日期再写入。时间粒度字段按模型区分：事件分析 / Session / 间隔 / 分布 用 `unit`，漏斗 / LTV 用 `time_bucket`，归因回溯窗口用 `lookback_window.unit`；取值统一为小写 `hour` / `day` / `week` / `month`（留存不支持 `hour`）。漏斗专属字段 `steps_must_be_within_date_range` 只出现在漏斗 `date_range` 中。

## 结构化调用约定

分析模型统一通过 `--input` 传 JSON 查询对象，典型调用：

```bash
sensors analytics <subcommand> --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{ ... }
__SENSORS_QUERY__
```

- `--input` 支持内联 JSON、文件路径、`-`（stdin）；heredoc 标记使用单引号，避免 shell 展开 JSON。
- `--dry-run` 仅输出转换后的 OpenAPI Request JSON，不发起真实请求；通过后去掉 `--dry-run` 执行同一份输入，输入变化后重新预览。dry-run 用于确认：事件名、聚合器、过滤条件位置、分组/拆分字段、`bucket_params` 是否符合预期。
- 对某个子命令的 `--input` 字段定义不确定时，运行 `sensors analytics <subcommand> --help` 查看完整 Schema。
- 模型选择、维度收口、时间粒度调整等业务决策由调用方决定；结构事实（采样、截断、空结果）原样传回。

## 公共输出结构

多数分析命令把结果归一化为：

| 字段 | 类型 | 含义 | 示例值 |
|---|---|---|---|
| `truncated` | bool | 结果是否被截断 | `false` |
| `columns` | object[] | 列对象数组，每列 `{name, display_name, type}`，按列顺序排列 | `[{"name":"date","display_name":"date","type":"date"},{"name":"浏览次数","display_name":"浏览次数","type":"number"}]` |
| `rows` | any[][] | 二维行数据，每行与 `columns` 顺序一一对应 | `[["2026-09-20 00:00:00",5902.0]]` |
| `request_id` | string | 请求追踪 ID | `7fbf3ef387344b3893101be1b0815d2a` |

`columns` 列对象三字段恒存在：

| 字段 | 含义 |
|---|---|
| `name` | 列名，与 `rows` 位置对齐的唯一键 |
| `display_name` | 最佳可读列名；来源无显示名时回退为 `name`（v2 漏斗/归因携带服务端显示名） |
| `type` | 归一化数据类型：`string` / `number` / `boolean` / `date` / `unknown`；服务端未提供类型时为 `unknown`，SQL 输出恒为 `unknown` |

读法一致：`columns` 是列 schema，用 `columns[i].name` 把 `rows` 里的值映射回列含义、用 `columns[i].type` 判断值的处理方式；各模型的列名规律见对应工具文件的「输出」一节。

保留专属结构、不走 `columns` / `rows` 的模型：路径分析（`nodes` / `links`，见 [analyze-user-path.md](analyze-user-path.md)）、用户群画像（`group_id` / `widget_id` / `data`，见 [analyze-personas.md](analyze-personas.md)）、RFM（`report` / `distributions`，见 [analyze-rfm.md](analyze-rfm.md)）、用户列表（`users` / `page`，见 [analyze-user-list.md](analyze-user-list.md)）、各分析模型用户明细（`users` / `page`，见 [list-funnel-users.md](list-funnel-users.md) 等 `list-*-users` 工具）。专属结构必须原样保留，不强行转换。

## 完整性标记

- `truncated = true`：结果不完整，原样传回调用方；不得据此推断「Top」「唯一」或完整排名。
- `sampling_factor` / `sample_factor = 64`：表示全量计算、结果精确；其它值表示采样状态，原样传回，绝对量级按估算口径理解。归一化输出不单列采样字段，按结果合理性结合上下文判断；采样状态下排序、占比类结论可保留，但须提示「基于采样估算，绝对量级可能有偏差」。
- `$ALL`：汇总行或汇总时间点。
- `$layer_total_reserved_word`：跨分组合计（如事件分析分组结果中的总计行）。
- 空结果只表示当前条件没有返回数据，不代表业务上不存在；不得自动放宽条件重试，是否复核及如何复核由最终使用者（用户）决定，工具不自动发起排查性查询。

## 结果排查与收口

构造或解读查询时遇到以下情况的处理手段（执行与否由调用方决定）：

- 大结果 / 截断（`truncated = true`）：成因通常是分组维度取值过多、时间跨度过长或 `limit` 不足。收口手段：减少 `by_fields`（优先降到 1 个维度）、缩短 `date_range`、用 `filter` 聚焦关注的分组值；归因等支持 `limit` 的模型可在确认必要时调大 `limit`（权衡结果体量与可读性）。
- 分组 / 拆分维度爆炸：高基数字段（如 `$ip`、`user_id`、原始 URL）不适合直接做分组维度，先确认是否真有必要，或改用 `filter` 聚焦；事件分析 `by_fields` 最多 2 个，维度取值过多时优先单维度再按需下钻。
- 长时间跨度 × 小时间粒度：如一年 × `hour` 会产生超大时间轴；趋势类问题优先 `day` / `week`，需要细看某段再缩小范围加粒度。
- 空结果：不编造「没有数据」「没有贡献」；口径自检通过（参数与用户意图一致、事件/字段已经元数据解析——解析时已顺带确认有上报、时间范围与过滤如实转写）后，0/空即为合法结果，直接报告。报告可附排查建议（日期范围是否覆盖数据、过滤是否过严）供用户选择。禁止为「凑出结果」换事件名、放宽条件后自行重试，也禁止自动发起交叉验证、换模型复算或 SQL 复算等排查性查询。
- 服务端错误（HTTP 5xx 等）：同参数重试至多 1 次；仍失败则如实上报服务端返回的错误信息与 request_id 后停止，不自动换工具、换口径或转 SQL 硬闯。
- 慢查询 / 超时：大跨度、多维度、复杂 `filter` 易超时；先 `--dry-run` 确认查询对象无误，再收口范围（缩短日期、减少维度）后执行；不通过反复重试硬刷。

## 结果解读顺序

返回给调用方的结果统一按以下顺序组织：

1. 结论：整体趋势 / 主分组对比 / 关键峰谷 / 主要贡献或漏损。
2. 查询口径：事件、聚合方式、时间范围、过滤条件、分组字段（及 Session 模型的 `session_name` 口径）。
3. 命名发现 / 消歧说明（如有）。
4. 采样 / 截断 / 桶口径提示（如有，按上文完整性标记口径解释）。
