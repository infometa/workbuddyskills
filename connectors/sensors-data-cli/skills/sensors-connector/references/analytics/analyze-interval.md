# 间隔分析
> 工具 `analysis.interval` · 命令 `sensors analytics interval` · 类型 查询

## 用途

统计两个事件之间时间间隔的分布：默认输出最大 / 最小 / 平均间隔与次数、人数等基础统计列；需要分位数（如 P50 / P90）时通过 `quantiles` 指定。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | JSON 输入；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | — |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

命令只有 `--input` 与 `--dry-run` 两个专属参数，没有 `--first` / `--days` 等快捷 flag，全部输入通过 `--input` JSON 传入。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `first_event` | object | 是 | 结构见下 | 间隔起始事件（允许字符串简写） | `{"event":"$AppStart"}` |
| `second_event` | object | 是 | 结构见下 | 间隔终止事件（允许字符串简写） | `{"event":"$AppEnd"}` |
| `date_range` | object | 是 | 见契约 | 公共日期范围，见 [analytics-query-schema.md](analytics-query-schema.md) | `2026-09-20 ~ 2026-09-26` |
| `by_fields` | string[] | 否 | 默认 `[]`，元素非空 | 分组维度；当前输入层未透传到接口（平台支持单维度 `by_field`），传了不生效 | — |
| `unit` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour`，控制结果按粒度展开 | `day` |
| `quantiles` | int[] | 否 | 默认 `[]`，元素须为 1~99 整数 | 分位数列表；默认不输出分位列。传入后服务端按请求输出分位列（列名为分位数值字符串），并可能自动补全 `25`/`50`/`75`；是否追加分位列以实际返回 `columns` 为准 | `[10,25,50,75,90]` |

`first_event` / `second_event` 每项：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 事件名 | `$AppStart` |
| `filter` | object | 否 | 过滤树 | 该事件过滤，字段应属于当前事件 | — |

校验速记与业务正确性约定：

- `first_event` / `second_event` 必须是 JSON 对象（至少含 `event` 键），业务上 second 应晚于 first 发生；颠倒顺序会让大量样本间隔为负/无意义，接口直接丢弃。
- 用户属性过滤统一写 `first_event.filter`，避免「起点已发生但终点用户被过滤掉」造成的样本失真。
- 事件 `filter` 内的字段事件名应与该步 `event` 一致；写成其他事件字段时 CLI 不报错但语义不对。
- 过滤树 `relation` 只接受小写 `and` / `or`。

固定注入字段：CLI 构造最终请求体时固定补入 `byValuesSelected: []`、`selected: []`、`measureValues: {"min": true, "max": true, "p10And90": false}` 等平台查询状态字段，不需要也不应在 `--input` 里手工填写。

已知差异（平台 API 支持、CLI 输入层未透传，写了不生效，无需转 SQL 兜底）：分组拆分（`by_field` / `by_event`，仅单维度）、允许终点超出 `to_date`（`extend_over_end_date`）、汇总/明细切换 / 自定义分桶 / 行数上限（`rollup` / `bucket_params` / `limit`）。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定起止（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「A 之后多久 B」「从 A 到 B 耗时」 | 起点放 `first_event.event`，终点放 `second_event.event`（按业务先后） |
| 「注册 → 首单」「下单 → 支付」「加购 → 下单」 | 首行为 `first_event`，后续行为 `second_event` |

两个事件名必须是已确认的精确标识；业务语义上 `second_event` 应晚于 `first_event`，否则结果大量为空。

### 第二步：定过滤（按作用事件分流）

| 业务表达 | 写入位置 |
|---|---|
| 「只看金额 ≥ 100 的订单」（终点事件属性） | `second_event.filter`，字段 `event.<终点事件>.<prop>` |
| 「只看 iOS 用户的下单」（用户属性） | 统一写 `first_event.filter`（保证起点人群即被过滤），字段 `user.*` |

### 第三步：定时间、粒度与分位数

相对时间（「最近 14 天」「上周」）先换算为绝对日期写入 `from_date` / `to_date`；`unit` 仅控制结果按时间维度展开的粒度，不影响间隔本身的计算——问「日内变化」用 `hour`，问「跨月趋势」用 `month`，默认 `day`。需要分位数时传 `quantiles`（1~99 整数列表，如 `[10, 25, 50, 75, 90]`）；不传则不输出分位列。

### 第四步：定拆分

有拆分需求（「按渠道/版本/城市拆分耗时」）时，告知 `by_fields` 当前输入层未透传、写了不生效，暂以结果后处理替代，无需转 SQL。

### 第五步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 端到端推导示例

业务输入：「最近 14 天，注册到首单的间隔时长分布是怎样的？只看 iOS 用户。」

1. 定起止：`注册 → 首单`，确认为 `register`、`order_submit`。
2. 定过滤：「只看 iOS 用户」是用户属性过滤，统一写入 `first_event.filter`，字段 `user.$platform`。
3. 定时间：「最近 14 天」换算为 2026-06-12 ~ 2026-06-25。
4. 定粒度与分位数：未明确，默认 `day`；问的是「分布」→ 传 `quantiles: [10, 25, 50, 75, 90]`。
5. 定拆分：未要求 → 不填 `by_fields`。
6. `--dry-run` → 执行。

### 调用示例

最小可执行（无过滤）：

```bash
sensors analytics interval --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "first_event": { "event": "register" },
  "second_event": { "event": "order_submit" },
  "date_range": { "from_date": "2026-06-12", "to_date": "2026-06-25" }
}
__SENSORS_QUERY__
```

完整示例（起点过滤 + 终点过滤 + 自定义分位数）：

```bash
sensors analytics interval --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "first_event": {
    "event": "register",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "user.$platform", "function": "equal", "params": ["iOS"] }
      ]
    }
  },
  "second_event": {
    "event": "order_submit",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "event.order_submit.amount", "function": "greaterEqual", "params": [100] }
      ]
    }
  },
  "date_range": { "from_date": "2026-06-12", "to_date": "2026-06-25", "timezone": "" },
  "unit": "day",
  "quantiles": [10, 25, 50, 75, 90]
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。专属列构成（基础列固定，按序）：

| 列名 | 含义 | 示例值 |
|---|---|---|
| `date` | 时间点，按 `unit` 粒度每时间点一行 | `2026-06-12` |
| `by_field` | 分组维度值；无分组时为空串（当前输入层未透传分组与汇总配置，不产生 `$ALL` 汇总行） | `iOS` |
| `max_time` | 最大间隔时长 | `<数值>` |
| `min_time` | 最小间隔时长 | `<数值>` |
| `uniqavg_time` | 人均平均间隔时长 | `<数值>` |
| `avg_time` | 平均间隔时长 | `<数值>` |
| `cnt` | 间隔样本次数 | `<数值>` |
| `uniqavg_cnt` | 人均次数 | `<数值>` |
| `people` | 参与计算的人数 | `<数值>` |
| 分位数列（如 `10`、`90`） | 对应分位数的间隔时长；仅请求 `quantiles` 非空时追加，服务端可能自动补全 `25`/`50`/`75`，以实际返回 `columns` 为准 | `"50"`=`<数值>` |

输出示例（请求带 `quantiles: [10, 25, 50, 75, 90]`，数值为占位）：

```json
{
  "truncated": false,
  "columns": [
    {"name": "date", "display_name": "date", "type": "date"},
    {"name": "max_time", "display_name": "max_time", "type": "number"},
    {"name": "min_time", "display_name": "min_time", "type": "number"},
    {"name": "uniqavg_time", "display_name": "uniqavg_time", "type": "number"},
    {"name": "avg_time", "display_name": "avg_time", "type": "number"},
    {"name": "cnt", "display_name": "cnt", "type": "number"},
    {"name": "uniqavg_cnt", "display_name": "uniqavg_cnt", "type": "number"},
    {"name": "people", "display_name": "people", "type": "number"},
    {"name": "10", "display_name": "10", "type": "number"},
    {"name": "25", "display_name": "25", "type": "number"},
    {"name": "50", "display_name": "50", "type": "number"},
    {"name": "75", "display_name": "75", "type": "number"},
    {"name": "90", "display_name": "90", "type": "number"}
  ],
  "rows": [
    ["2026-06-12", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>", "<数值>"]
  ],
  "request_id": "<request_id>"
}
```

结构性读法：不传 `quantiles` 时看 `avg_time` / `uniqavg_time`（平均间隔）与 `people` / `cnt`（样本量，样本量过小时统计值不稳定）；传了 `quantiles` 后先看中位数（如 `50` 列，绝大多数用户多久从 A 走到 B），再看长尾（如 `90` 列），按 `unit` 展开后重点指出中位数 / 长尾在哪些时段明显拉长。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `first_event.event` / `second_event.event` 缺失或为空 | 只传了一边或事件名空白 | 起止事件都必须填 |
| `unit` 校验失败 | 写了 `hourly` / `每天` 等 | 仅支持小写 `day` / `week` / `month` / `hour` |
| `quantiles 元素必须是 1~99 的整数，收到: X` | 分位数元素越界或非整数 | 改为 1~99 的整数列表，如 `[10, 25, 50, 75, 90]` |
| `by_fields[i] 不能为空字符串` | 分组维度元素空白 | 移除或填合法字段名 |
| 写了 `by_fields` 但结果不分组 | CLI 输入层未透传分组（平台支持单维度 `by_field`） | 暂以结果后处理替代，无需转 SQL |
| 终点超出 `to_date` 没生效 | CLI 输入层未透传 `extend_over_end_date` | 按查询区间内完成的终点解读 |
| 分位数大量为空 / 为 0 | `second_event` 早于 `first_event`、时间窗过短、过滤过严 | 口径自检通过即为合法空结果，直接报告；左列成因作为排查建议供用户确认，确认后按建议调整 |
| 中位数耗时异常拉长 | 长尾样本污染、跨自然日切换、起止事件定义不准 | 收口时间窗口、对比 P50 与 P90 差距；业务定义复核由调用方决定 |
| `filter` 用了别的事件的字段 | 把订单字段写到 `register.filter` 里 | 字段事件名必须等于该步 `event` |
| 过滤条件被拒 | `op`/`values` 或非法 `function` | 按 [analytics-query-schema.md](analytics-query-schema.md) 重写 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- `filter` 引用其它事件的字段不报错但语义错误，须保证字段事件名等于所属事件 `event`。
- 空结果很可能是终止事件不在查询区间内，先核对时间窗，不得自动放宽条件重试。
