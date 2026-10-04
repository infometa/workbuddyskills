# 事件分析
> 工具 `analysis.events` · 命令 `sensors analytics segmentation` · 类型 查询

## 用途

多指标查询事件在时间与分组维度上的聚合结果：一次请求可混合多个普通指标（不同事件 × 不同聚合，各自独立的属性与过滤）与公式指标（基于聚合函数四则运算的转化率、客单价、占比等派生指标）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

命令只有 `--input` 与 `--dry-run` 两个专属参数，没有 `--event` / `--days` 等快捷 flag，所有分析参数均通过 `--input` JSON 传入。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `measures` | object[] | 是 | 至少 1 项，`name` 全局唯一 | 指标列表，普通指标与公式指标可混排，结构见下 | `[{"event":"$pageview","aggregator":"general","name":"浏览次数"}]` |
| `date_range` | object | 是 | 见契约 | 公共日期范围（`from_date` / `to_date` / `timezone`），见 [analytics-query-schema.md](analytics-query-schema.md) | `{"from_date":"2026-09-20","to_date":"2026-09-26"}` |
| `unit` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour`（小写） | `day` |
| `by_fields` | string[] | 否 | 默认 `[]`，最多 2 个，元素非空 | 分组维度，作用于全部指标；事件字段输出列名会归一化为 `event.$Anything.<prop>` | `["event.$pageview.$os"]` |
| `filter` | object | 否 | 过滤树 | 顶层全局过滤，对**所有指标**生效；单个指标的过滤写 `measures[].filter` | `{"relation":"and","conditions":[{"field":"event.$pageview.$os","function":"equal","params":["Windows","iOS"]}]}` |

`measures[]` 普通指标（二选一形态之一）：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 事件名 | `$pageview` |
| `aggregator` | enum | 是 | 见聚合器表 | 聚合方式，与 `field` 配套规则见下 | `general` |
| `field` | string | 条件 | 三段式/四段式 | 数值类聚合必填，`event.<event>.<prop>[.<sub>]`；计数类禁止填 | `event.$pageview.$viewport_width` |
| `filter` | object | 否 | 过滤树 | 指标级过滤，只作用于本指标 | `—` |
| `name` | string | 否 | 全局唯一 | 结果列名；缺省自动生成 `{event}.{aggregator}[.{prop末段}]` | `浏览次数` |

`measures[]` 公式指标（提供 `expression` 即为公式指标，两种形态互斥）：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `expression` | string | 是 | ``公式\|format`` | 表达式语法见下节，如 `count(event.purchase)/count(event.$MPShow)\|%2p` | `count(event.$WebClick)/count(event.$pageview)\|%2p` |
| `name` | string | 是 | 全局唯一 | 结果列名（公式指标必填） | `点击率` |
| `filter` | object | 否 | 过滤树 | 作用于表达式内**全部**原子指标 | `—` |
| `expression_filters` | (object\|null)[] | 否 | 数量 ≤ 原子指标数 | 按原子指标出现顺序下标对齐；`null` 表示该原子不过滤 | `—` |
| `events` | string[] | 否 | — | 表达式涉及事件名；缺省由 CLI 自动派生（去重） | `—` |
| `expression_denominator_without_group` | boolean | 否 | — | `true` 时除法分母上的原子指标不按分组计算（占比场景必用） | `—` |
| `atom_measure_without_group` | boolean | 否 | — | `true` 时全部原子指标不分组，用整体合计值代入公式 | `—` |

### 公式表达式语法

表达式 = `<算术公式>|<format 后缀>`，两部分都必须提供：

- **原子指标**写成聚合函数调用 `聚合函数(字段引用)`，与普通指标同口径；
- **运算符**仅支持 `+ - * /`、括号、一元正负号与数字字面量（不支持取模和 abs/round 等数学函数）；
- **format 后缀**控制结果显示：`%2f` 两位小数 / `%d` 整数（输出为浮点值，如 `3070.0`）/ `%n` 千分位格式（**返回 JSON 字符串**，如 `"3070"`）/ `%2p` 百分比口径，通式 `%<位数><f|p|d|n>`。注意 `%2p` 的 API 返回值仍是**原始比率**（0~1 区间小数，如 `0.2074`），不含 `%` 符号，展示时需 ×100 并自行补 `%`。

字段引用形态（决定「统计什么」）：

| 引用 | 写法示例 | 语义 |
|---|---|---|
| 事件次数/人数 | `count(event.$AppClick)`、`unique(event.purchase)` | 不带属性：总次数 / 去重人数 |
| 事件属性聚合 | `sum(event.purchase.amount)`、`avg(event.Click.$duration)` | 带属性：数值属性求和 / 均值 |
| 属性去重/人均 | `unique(event.purchase.order_id)`、`average(event.purchase.amount)` | 带属性的 unique=去重数、average=人均值；不带属性时分别是人数/人均次数 |
| 用户维度 | `count(user)`、`max(user.age)` | 裸 `user` 仅限 count 类函数=用户总数；`user.<prop>` 为用户属性 |
| Session 维度 | `count(session_<名称>.$Anything)`、`bounce_rate(session_<名称>.$Anything)` | Session 引用；`bounce_rate`/`exit_rate`/`session_count` 仅限此形态 |

常用函数：`count` / `general`（总次数）、`unique` / `uniqcount`（人数/去重数）、`average` / `uniqavg`（人均次数/人均值）、`sum` / `avg` / `max` / `min`（数值属性）、`quantile25` / `quantile50` / `quantile75` / `quantile90`（分位数）、`rollup_count` / `rollup_uniq`（合计次数/人数）及滚动窗口类（`count_last_day_7` 等）。函数名大小写不敏感；完整可用函数清单以校验错误提示中的「可用函数」列表为准。

配对规则（CLI 强制校验）：`sum`/`avg`/`max`/`min`/`quantile*` 等数值函数必须带属性；`count`/`general` 与滚动窗口类不允许带属性；`ltv*` 为留存专用（不支持）；泛型 `quantile` 需改用 `quantile25/50/75/90`。

### 聚合器表（普通指标 `aggregator`）

| 类别 | 取值 | `field` |
|---|---|---|
| 计数类 | `general`（总次数/PV）、`unique`（去重人数/UV）、`average`（人均次数）、`rollup_count` / `rollup_uniq`（合计次数/人数）、`count_last_day_7` / `count_last_day_30`（过去 N 天总次数）、`uniq_last_day_7` / `uniq_last_day_30`（过去 N 天用户数）、`count_cur_month` / `uniq_cur_month`（当月次数/人数） | 禁止填 |
| 数值类 | `sum`（求和）、`avg`（均值）、`max` / `min`（最值）、`uniqavg`（人均值）、`uniqcount`（去重数）、`quantile25` / `quantile50` / `quantile75` / `quantile90`（分位数） | 必填 `event.<event>.<prop>` |

注意口径区分：`average`=人均次数（不带属性），`avg`=数值属性均值（必带属性）；公式内 `average(event.X.amount)` 则是人均值。

`by_fields` 取值规则：用户字段写 `user.<prop>` 原样透传；事件字段写 `event.<event>.<prop>`，输出列名归一化为 `event.$Anything.<prop>`；时间类字段（`$time` / `register_time` 等）CLI 按 `unit` 自动补 `bucket_params`，无需手写。

校验速记（构造后必过）：

- `measures` 至少 1 项；普通指标 `event`+`aggregator` 必填，公式指标 `expression`+`name` 必填，两种形态字段不可混用。
- 所有 `name` 全局唯一（含自动生成的默认名）；过滤树 `relation` 只接受小写 `and` / `or`。
- 表达式必须带 `|format` 后缀；`expression_filters` 数量不能超过表达式原子指标个数。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：拆指标

把业务问题拆成若干指标（同事件多聚合、多事件对比、派生比率），每项决定普通指标（事件+聚合）还是公式指标（表达式）。

### 第二步：定事件与聚合（值映射）

| 业务口径 | 映射结果 | 规则 |
|---|---|---|
| 「次数」「PV」「触发了多少次」 | `aggregator: "general"` | 计数类，不填 `field` |
| 「多少人」「UV」「DAU」「独立用户」 | `aggregator: "unique"` | 计数类，不填 `field`；DAU 通常配 `unit: "day"` |
| 「人均次数」「平均每人触发几次」 | `aggregator: "average"` | 计数类，不填 `field` |
| 「金额总和」「时长总和」 | `aggregator: "sum"` + `field` | `field` 写三段式 `event.<event>.<prop>` |
| 「平均金额」「平均时长」 | `aggregator: "avg"` + `field` | 同上 |
| 「最大 / 最小金额」 | `aggregator: "max"` / `"min"` + `field` | 同上 |
| 「转化率」「点击率」「完成率」 | 公式指标 `count(...)/count(...)\|%2p` | 分子分母分别确认事件与口径 |
| 「客单价」「人均金额」 | 公式指标 `sum(...)/unique(...)\|%2f` | 金额求和除以人数 |
| 「各分组占比」 | 公式指标 + `expression_denominator_without_group: true` | 分母不分组，用整体合计 |

事件名必须是已确认的精确标识，口语词（「提交订单」「小程序显示」）未确认前不得猜测。

### 第三步：定过滤

只作用于单个指标的条件写 `measures[].filter`（公式指标的 `filter` 作用于全部原子指标；需要只过滤某一个原子时用 `expression_filters` 按出现顺序对齐，不过滤的原子填 `null`）；对所有指标都生效的公共条件写顶层 `filter`。多值集合匹配用 `equal` 传多值（无 `in`）。

### 第四步：定时间与粒度

相对时间（「最近 7 天」「上周」）先换算为绝对日期再写入 `date_range`；`unit` 默认 `day`，DAU 类问题必须 `day`。

### 第五步：定拆分与命名

最多 2 个 `by_fields`（时间类分组字段由 CLI 自动补 `bucket_params`）；多指标场景建议显式写 `name`，结果列名与解读都更清晰。

### 第六步：自检并执行

对照「输入 Schema」校验速记过一遍 → `--dry-run` 确认转换后的请求（指标顺序、聚合器、过滤位置、分组字段、`bucket_params`、公式 `events` 派生）→ 去掉 `--dry-run` 执行。

### 端到端推导示例

业务输入：「最近 7 天支付金额总和与支付人数，算客单价；只看 lib_version 是 1.6.34 或 1.6.39 的支付。」

1. 拆指标：金额总和（普通 `sum`）、支付人数（普通 `unique`）、客单价（公式 `sum/unique`）。
2. 定聚合与属性：`field: "event.purchase.amount"`；公式 `sum(event.purchase.amount)/unique(event.purchase)|%2f`。
3. 定过滤：`lib_version` 条件只作用于支付相关指标 → 写进各 `measures[].filter`（或顶层 `filter`，因三个指标都涉及 purchase）。
4. 定时间：「最近 7 天」换算为绝对 `date_range`；`unit: "day"`。
5. 定命名：显式 `name`「支付金额」「支付人数」「客单价」。
6. `--dry-run` → 执行。

### 调用示例

最小可执行（单指标次数）：

```bash
sensors analytics segmentation --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "measures": [{ "event": "$MPShow", "aggregator": "general" }],
  "date_range": { "from_date": "2026-06-19", "to_date": "2026-06-25" }
}
__SENSORS_QUERY__
```

多指标 + 指标级过滤 + 分组拆分：

```bash
sensors analytics segmentation --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "measures": [
    {
      "event": "$MPShow",
      "aggregator": "general",
      "name": "小程序显示总次数",
      "filter": {
        "relation": "and",
        "conditions": [
          { "field": "event.$MPShow.$lib_version", "function": "equal", "params": ["1.6.34", "1.6.39"] },
          { "field": "user.prefer_concept", "function": "equal", "params": ["军工", "机械"] }
        ]
      }
    },
    { "event": "$MPShow", "aggregator": "unique", "name": "小程序显示人数" }
  ],
  "date_range": { "from_date": "2026-06-19", "to_date": "2026-06-25", "timezone": "" },
  "unit": "day",
  "by_fields": ["event.$MPShow.$referrer"]
}
__SENSORS_QUERY__
```

公式指标（客单价 + 转化率 + 占比）：

```bash
sensors analytics segmentation --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "measures": [
    {
      "name": "客单价",
      "expression": "sum(event.order_pay.amount)/unique(event.order_pay)|%2f",
      "filter": {
        "relation": "and",
        "conditions": [
          { "field": "event.order_pay.$lib_version", "function": "equal", "params": ["1.6.34"] }
        ]
      }
    },
    {
      "name": "支付转化率",
      "expression": "count(event.order_pay)/count(event.$MPShow)|%2p"
    },
    {
      "name": "渠道占比",
      "expression": "count(event.order_pay)/count(event.$Anything)|%2p",
      "expression_denominator_without_group": true
    }
  ],
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-07" },
  "unit": "day",
  "by_fields": ["user.<已确认的用户属性>"]
}
__SENSORS_QUERY__
```

`user.<已确认的用户属性>` 为占位形式，实际分组字段须先经 `metadata.fields` 确认存在与取值后替换。

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。专属列名规律：

| 列类型 | 识别方式 | 说明 | 示例值 |
|---|---|---|---|
| 维度列 | 来自 `by_fields` | 事件分组字段显示为 `event.$Anything.<prop>`；无分组时无维度列 | `event.$Anything.$os`=`iOS` |
| 指标列 | 与 `measures` 顺序对应 | 列名即指标 `name`（含自动生成的默认名） | `浏览次数`=`5902.0` |
| 时间点列 | `columns` 固定含 `name` 为 `date` 的列 | 每个时间点**一行**（`columns` 各列 `name` 形如 `date, <指标名>...`），`date` 值标识该行所属时间点，按 `unit` 步进 | `date`=`2026-09-20 00:00:00` |
| 总计行 | 维度值为 `$layer_total_reserved_word` | 跨分组合计保留字；仅汇总（rollup）场景返回，默认请求（如本命令默认不开启汇总）通常无总计行 | `—` |

分组场景读法：

- 无分组：没有分组维度列，每个时间点一行，按 `date` 顺序解读整体趋势（峰谷、走势）。
- 普通枚举分组：维度列是单值字符串（如 `美国`），按主指标排序对比。
- 时间型桶分组：维度列是区间字符串（如 `2026-06-01~2026-06-08`），按区间解读，不要当作单一日期。
- 总计行的 `$layer_total_reserved_word` 解释为「总计 / 全部分组合计」，不要原样返回保留字。
- 公式指标列读数按 `format` 后缀口径：`%2f` / `%d` 为数值（`%d` 输出浮点）、`%n` 为字符串；`%2p` 列读数 = **原始比率**（0~1 小数，如 `0.2074`），需 ×100 并补 `%` 后展示——与留存分析 `key_key_rt_<N>_rate`（服务端已拼好 `"40.00%"` 字符串）口径不同，不要混淆。占比类公式默认分母按分组计算，写了 `expression_denominator_without_group: true` 时分母是整体合计。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `measures 至少需要 1 个指标` / `Field required: measures` | 指标列表缺失或为空（含旧格式 `event`/`metrics`/`measure` 输入） | 按「输入 Schema」用 `measures` 列表重写 |
| `aggregator '...' 不是合法的聚合方式` | 聚合名拼错或用了旧简写（`total`/`per_day`） | 按错误信息列出的合法值改写：`total→general`、人均次数用 `average` |
| `数值类聚合必须提供 field` / `field 格式非法` | 数值聚合缺属性或路径不是 `event.<事件>.<属性>` | 补三段式/四段式 `field` |
| `计数类聚合不允许提供 field` | `general`/`unique`/`average` 等填了 `field` | 删除 `field`；属性聚合改用 `sum`/`avg` 等 |
| `指标 name 重复` | 显式或默认名冲突 | 为同名指标显式指定不同 `name` |
| `缺少 format 后缀` / `format 后缀非法` | 公式没写 `\|format` 或后缀不合法 | 补 `%2f`/`%d`/`%2p`/`%n` 后缀 |
| `聚合函数 '...' 不存在` | 表达式函数名拼错 | 按错误信息列出的可用函数改写 |
| `缺少聚合属性` / `不支持属性引用` | `sum(event.purchase)` 缺属性、`general(event.x.amount)` 带属性 | 按错误信息中的示例改写引用形态 |
| `仅支持 Session 引用` | `bounce_rate` 等用在普通事件引用上 | 改为 `session_<名称>.$Anything` 或换函数 |
| `expression_filters 数量不能超过原子指标个数` | 过滤列表比表达式原子指标多 | 按出现顺序对齐，多余项删除、不过滤的原子填 `null` |
| `by_fields 最多支持 2 个字段` | 分组维度超过 2 | 降到 ≤ 2；更多维度需求如实告知当前上限，由用户决定是否分多次查询 |
| 过滤条件被拒 | 用了 `op`/`values` 或非法 `function` | 按 [analytics-query-schema.md](analytics-query-schema.md) 三段式与 `function` 枚举重写 |
| 分组列名变成 `event.$Anything.<prop>` | 事件分组字段的正常归一化 | 正常行为；解读结果时按属性名识别该列 |
| 未写 `bucket_params` 但返回区间桶 | CLI 识别时间类字段后自动补齐 | 正常行为；按区间分组解读 |
| 结果截断 / 采样 | 拆分维度多、时间跨度大 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释；降维、缩短时间后重查由调用方决定 |
| 空结果 | 条件过严、命名错、区间无数据 | 只说明当前条件下无结果；复核 `has_data` 与是否放宽由调用方决定，不自动重试 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- 进入请求的属性（含 `user.*` 过滤/分组字段）必须先经 `metadata.fields` 确认属性存在、类型与取值，未确认属性不得进入请求。
- `%2p` 公式指标列读数为原始比率（0~1），解读时 ×100 并补 `%` 后再呈现，不得把读数直接当百分数。
- `truncated=true` 原样传回调用方，不得宣称完整排名。
- 空结果不代表业务上不存在，不得自动放宽条件重试。
- 输出列名中的 `event.$Anything.<prop>` 是分组字段通配形式，解读时按属性名识别。
- 公式指标的分母口径（是否按分组）必须在回答占比类问题时显式确认，默认与 `expression_denominator_without_group` 的取值一致。
