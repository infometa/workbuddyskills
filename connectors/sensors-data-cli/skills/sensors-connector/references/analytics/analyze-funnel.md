# 漏斗分析
> 工具 `analysis.funnel` · 命令 `sensors analytics funnel` · 类型 查询

## 用途

按步骤顺序统计用户在多步事件序列上的转化率与每步流失。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；分析参数须一次性传入 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 打印转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

执行时自动检测 SA 版本选择 v1 / v2 接口，输入输出结构一致。注意 `--dry-run` 预览固定输出 v1 形态（`funnel` 字段）；v2 环境实际请求为 `funnel_define` 结构，两者 `max_convert_time` 均以分钟计。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `steps` | object[] | 是 | 至少 2 项 | 按业务先后排列的步骤，结构见下 | `[{"event":"$AppStart"},{"event":"$AppEnd"}]` |
| `date_range` | object | 是 | 见契约 | 公共日期范围，另支持 `steps_must_be_within_date_range`（bool，默认 `false`，是否要求每步都在统计区间内），见 [analytics-query-schema.md](analytics-query-schema.md) | `{"from_date":"2026-09-20","to_date":"2026-09-26"}` |
| `filter` | object | 否 | 过滤树 | 全局筛选，作用于整个漏斗；事件字段必须引用步骤内事件 | `—` |
| `subject` | string | 否 | 默认 `$user_id` | 漏斗主体 ID | `$user_id` |
| `count_mode` | enum | 否 | 默认 `users` | `users` 按人数 / `times` 按次数；CLI 分别映射为平台 `uniq` / `count` | `users` |
| `conversion_window` | string | 否 | 默认 `7day` | `natural_day` 或 `<N>m\|h\|d\|day\|days`（如 `20m`、`2h`、`10day`），数值须 ≥ 1 | `7day` |
| `time_bucket` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour` | `day` |
| `by_fields` | object[] | 否 | 无条件注入时间分组 | 每项 `{field, step}`，`field` 支持 `event.<event>.<prop>` 或 `user.<prop>`，`step` 为作用步骤（0 起）；无论是否显式传入，CLI 总会在最前注入第一步事件的 `$time` 分组（显式传同名字段时不重复注入） | `[{"field":"event.$AppStart.$time","step":0}]` |

`steps[]` 每项：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `event` | string | 是 | 步骤事件名，非空 | `$AppStart` |
| `name` | string | 否 | 步骤展示名 | `启动` |
| `filter` | object | 否 | 步骤级过滤，字段应属于当前步骤事件 | `—` |

字段约束细则：

- `conversion_window` 特例 `natural_day` 表示自然日当天；其余必须匹配 `<number><unit>`，`unit` ∈ `m` / `h` / `d` / `day` / `days`。非法示例：`7天`、`1week`、`3小时`（中文或非约定单位会被校验拒绝）。`date_range.timezone` 为空时不注入时区字段，与页面空值语义一致。
- 全局 `filter` 的事件字段用 `event.<event>.<prop>` 时，`<event>` 必须是漏斗某一步骤的事件名；CLI 据此自动生成接口所需的 `filter_field_steps`（事件字段→该事件步骤索引，用户字段→`-1`）。这是漏斗独有约束：全局 filter 引用步骤外事件无法确定作用步骤。
- `$time` 是内置字段，元数据中不出现，按事件时间分组时显式填写 `event.<event_name>.$time`，且只能配置在第 1 步（`step: 0`）。
- 输入层不接受对比时间、汇总配置、同时显示指标、关联属性等高级能力字段。

校验速记：`steps` ≥ 2；全局 `filter` 事件字段必须在 `steps` 中；`$time` 拆分只能 `step: 0`；`steps[]` 每项是 JSON 对象（至少含 `event` 键）；过滤树 `relation` 只接受小写 `and` / `or`。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：拆步骤

识别行为链，按业务先后排出 `steps`（至少 2 步）。每个事件名必须是已确认的精确标识；多候选事件禁止自行二选一。

### 第二步：定统计口径

| 业务表达 | 映射结果 |
|---|---|
| 「多少人转化」「转化率」（默认） | `count_mode: "users"`（按人去重） |
| 「多少次」、明确提到次数口径 | `count_mode: "times"`（按次数） |
| 漏斗主体不是用户（如按设备） | `subject`（默认 `$user_id`，特殊主体才改） |

### 第三步：定转化窗口（值映射）

| 业务表达 | `conversion_window` |
|---|---|
| 「当天完成」 | `natural_day` |
| 「3 天内完成」 | `3day` |
| 「2 小时内完成」 | `2h` |
| 「20 分钟内完成」 | `20m` |
| 未明确说明 | 默认 `7day` |

### 第四步：定时间

相对时间（「上周」「最近 7 天」）先换算为绝对日期写入 `date_range`；仅当显式要求「所有步骤必须落在统计区间内完成」时才设 `steps_must_be_within_date_range: true`。

### 第五步：定过滤（两级分流）

- 全局过滤（顶层 `filter`）：放用户属性（`user.*`）或贯穿全链路的条件；事件字段的事件名必须是某一步骤的事件。
- 步骤过滤（`steps[].filter`）：放某一步的事件属性条件（如「下单金额 > 100」），字段事件名必须等于该步 `event`。

### 第六步：定拆分

每个拆分维度写 `{field, step}`：先确认字段，再定它作用在哪一步（`step` 从 0 起且 ≤ 步数-1）；按事件时间分组用 `event.<event>.$time` 且只能放 `step: 0`。

### 第七步：自检并执行

对照校验速记逐项过（步骤数、窗口格式、step 范围、`$time` 位置、步骤 filter 事件名）→ `--dry-run` → 执行。

### 端到端推导示例

业务输入：「看上周注册的用户里，3 天内完成首次下单的转化率，按注册渠道拆分。」

1. 拆步骤：`注册 → 下单`，确认为 `register`、`order_submit` → `steps: [register, order_submit]`。
2. 定口径：问「转化率」「多少用户」→ `count_mode: "users"`。
3. 定窗口：「3 天内完成」→ `conversion_window: "3day"`。
4. 定时间：「上周」换算为 2026-06-15 ~ 2026-06-21；未要求全步骤落在区间内 → `steps_must_be_within_date_range: false`。
5. 定过滤：无额外条件 → 不填 `filter`。
6. 定拆分：注册渠道确认为 `event.register.$utm_source`，作用在注册步 → `by_fields: [{field: "event.register.$utm_source", step: 0}]`。
7. `--dry-run` → 执行。

### 调用示例

最小可执行（2 步无过滤）：

```bash
sensors analytics funnel --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "steps": [{ "event": "register" }, { "event": "order_submit" }],
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-07" }
}
__SENSORS_QUERY__
```

完整示例（全局过滤 + 步骤过滤 + 多维拆分 + 自定义窗口）：

```bash
sensors analytics funnel --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "subject": "$user_id",
  "count_mode": "users",
  "conversion_window": "10day",
  "time_bucket": "day",
  "date_range": {
    "from_date": "2026-06-01",
    "to_date": "2026-06-07",
    "timezone": "",
    "steps_must_be_within_date_range": false
  },
  "filter": {
    "relation": "and",
    "conditions": [
      { "field": "user.user_segment_t3", "function": "isTrue", "params": [] }
    ]
  },
  "steps": [
    { "event": "$AppClick", "name": "App 点击" },
    {
      "event": "payOrder",
      "name": "支付订单",
      "filter": {
        "relation": "and",
        "conditions": [
          { "field": "event.payOrder.amount", "function": "greaterEqual", "params": [100] }
        ]
      }
    }
  ],
  "by_fields": [
    { "field": "event.$AppClick.$time", "step": 0 },
    { "field": "event.payOrder.$lib", "step": 1 }
  ]
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。专属列名规律：

| 列名模式 | 含义 | 示例值 |
|---|---|---|
| `event.<event>.$time` 等维度列 | 分组维度值（默认按第一步时间分组） | `event.$AppStart.$time`=`2026-09-20` |
| `step_fold.user_count` / `step_fold.conversion_rate` | 整体转化人数（= 最后一步人数）/ 整体转化率（末步人数 ÷ 首步人数 ×100） | `126.0` / `95.45` |
| `step_<N>.user_count` | 第 N 步人数（`step_1` 为首步） | `step_1.user_count`=`132.0` |
| `step_<N>.wastage_user` | 第 N 步流失人数 | `step_1.wastage_user`=`6.0` |
| `step_<N>.medium_converted_time` | 第 N 步转化时长中位数，数值输出（整数或浮点均可能出现，按数值解读）；OpenAPI 链路下非最后一步恒输出，无关闭参数 | `step_1.medium_converted_time`=`34.0` |
| `step_<N>.conversion_rate` | 到第 N 步的转化率 | `step_1.conversion_rate`=`95.45` |

`count_mode: "times"` 时统计口径变为次数，但列名保持 `*.user_count` 系列不变，解读时按次数口径。

行读取示例（`rows` 一行按 `columns` 各列 `name` 对齐）：

| 列名 | 值 |
|---|---|
| `event.$AppStart.$time` | `2026-09-20` |
| `step_fold.user_count` | `126.0` |
| `step_fold.conversion_rate` | `95.45` |
| `step_1.user_count` | `132.0` |
| `step_1.wastage_user` | `6.0` |
| `step_1.medium_converted_time` | `34.0` |
| `step_1.conversion_rate` | `95.45` |
| `step_2.user_count` | `126.0` |

读法：`step_fold.*` 是整体结果，`step_<N>.*` 是各步结果（`medium_converted_time` 为转化时长中位数，仅非最后一步输出），`event.*.$time` 是分组维度；时间维度值为 `null` 的行是汇总层（各维度小计），不要当成单日明细。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `steps 至少需要 2 个步骤` | 步骤数 < 2 | 补足至少 2 步 |
| `conversion_window 必须是 natural_day 或 <number>m\|h\|d\|day\|days` | 窗口格式非法（如 `7天`、`1week`） | 改用 `natural_day` / `10day` / `2h` / `20m` |
| `by_fields.step 必须在 0 到 N 之间` | 拆分步骤越界 | step 对齐 0 ~ 步数-1 |
| `事件时间分组字段 $time 只能配置在第 1 步（step=0）` | `$time` 放在非首步 | 移到 `step: 0` |
| `全局 filter 条件引用的事件 X 不在漏斗步骤中` | 全局 filter 引用了步骤外事件 | 改用步骤内事件字段，或把该事件加入 `steps` |
| `全局 filter 字段必须以 event. 或 user. 开头` | 裸字段名 | 改三段式或 `user.*` 前缀 |
| 步骤过滤结果不符合预期 | 步骤 `filter` 用了别的步骤的事件字段（CLI 不报错但语义错） | 字段事件名应等于当前步 `event` |
| 过滤条件被拒 | `op`/`values` 或非法 `function` | 按 [analytics-query-schema.md](analytics-query-schema.md) 重写；集合匹配用 `equal` 传多值 |
| 转化率异常低或为 0 | 转化窗口过短、步骤业务顺序排错 | 口径自检通过即为合法结果，直接报告；左列成因作为排查建议供用户确认，确认后核对 `conversion_window` 与 `steps` 的业务先后 |
| 结果截断 / 采样 | 拆分维度多、时间跨度大 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释；降维/缩短跨度由用户决定 |
| 空结果 | 条件过严、命名错、区间无数据 | 只说明当前条件下无结果；是否复核由用户决定，不自动放宽重试 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- 步骤 `filter` 引用其他步骤事件的字段不会报错但语义错误，须保证字段事件名等于当前步骤 `event`。
- `truncated=true` 原样传回，不得宣称完整漏损排名；空结果不得自动放宽条件重试。
