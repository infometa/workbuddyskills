# 留存分析
> 工具 `analysis.retention` · 命令 `sensors analytics retention` · 类型 查询

## 用途

统计初始事件与回访事件之间的留存率变化（按周期展开，可按维度分组对比）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | JSON 输入；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 打印转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

执行时自动检测 SA 版本选择 v1 / v2 接口，输入输出结构一致。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `initial_event` | object | 是 | 结构见下 | 初始行为事件（留存起点） | `{"event":"$pageview"}` |
| `return_event` | object | 是 | 结构见下 | 回访行为事件（留存终点） | `{"event":"$WebClick"}` |
| `date_range` | object | 是 | 见契约 | 公共日期范围，见 [analytics-query-schema.md](analytics-query-schema.md) | `{"from_date":"2026-09-20","to_date":"2026-09-26"}` |
| `unit` | enum | 否 | 默认 `day` | 留存周期粒度：`day` / `week` / `month`（不支持 `hour`） | `day` |
| `duration` | int | 否 | 默认 `7` | 观测周期数，上限按 `unit` 分档：`day` ≤ 60、`week` ≤ 45、`month` ≤ 48 | `7` |
| `user_filter` | object | 否 | 过滤树 | 用户属性过滤，字段必须 `user.*` 前缀 | `—` |
| `by_fields` | string[] | 否 | 默认 `[]`，不可重复 | 分组维度，支持 `first.*` / `second.*` / `user.*` 简写前缀 | `[]` |

`initial_event` / `return_event` 每项：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 事件名 | `$pageview` / `$WebClick` |
| `filter` | object | 否 | 过滤树 | 初始事件过滤字段必须 `first.*` 前缀；回访事件过滤字段必须 `second.*` 前缀 | `—` |

字段简写与作用域（核心约定）：

- `first.<property>` → 展开为 `event.<初始事件>.<property>`（初始事件字段）。
- `second.<property>` → 展开为 `event.<回访事件>.<property>`（回访事件字段）。
- `user.<property>` → 原样保留（用户字段）。
- 兼容直接写完整三段式 `event.<event_name>.<property>`，但推荐用简写；输出中各查看维度的取值统一落在 `key_<N>` 列（见「输出」），不会还原显示完整字段名。
- 三类过滤树各有允许前缀，不能跨域混用：`user_filter` 只 `user.*`、`initial_event.filter` 只 `first.*`、`return_event.filter` 只 `second.*`。

`by_fields` 取值规则：

| 规则 | 说明 |
|---|---|
| 自动补初始日期分组 | 结果自动带上初始日期分组维度（按用户初始事件发生日期分批，取值显示在 `key_1` 列）并固定排在第一位；不传 `by_fields` 也会有该维度 |
| 显式传 `first.$time` | 仍排在第一位并去重，不会重复 |
| 前缀限制 | 仅接受 `user.` / `first.` / `second.` / `event.`；`user.`/`first.`/`second.` 简写不允许重复 |

校验速记：`initial_event.event` / `return_event.event` 必填；`duration` 上限按 `unit` 分档（`day` ≤ 60、`week` ≤ 45、`month` ≤ 48）；`unit` 仅 `day`/`week`/`month`（无 `hour`）；事件对象是 JSON 对象不是字符串；过滤树 `relation` 只接受小写 `and` / `or`。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；`first.<attr>` / `second.<attr>` 会被自动展开为 `event.<初始事件>.<attr>` / `event.<回访事件>.<attr>`。以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定起点与回访（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「做了 A 之后是否回来做 B」「A 后留存」 | 起点放 `initial_event.event`，回访放 `return_event.event` |
| 「注册 / 激活 / 首单后的回访」 | 该起始行为对应事件写 `initial_event` |

两个事件名必须是已确认的精确标识；业务上回访事件应确实发生在初始事件之后，否则留存口径失真。仅支持单初始 + 单回访。

### 第二步：定周期（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「次日 / 7 日 / 30 日留存」「按天看」 | `unit: "day"`（默认） |
| 「按周 / 月看留存」 | `unit: "week"` / `"month"` |
| 「看往后 14 个周期」「观察 8 周」 | `duration: 14` / `8`（默认 `7`；上限 `day` 60 / `week` 45 / `month` 48） |

### 第三步：定过滤（三作用域分流）

| 业务表达 | 写入位置 | 字段前缀 |
|---|---|---|
| 「只看某类用户的留存」（用户属性，作用全链路，属性先经 `metadata.fields` 确认） | `user_filter` | 只允许 `user.*` |
| 「只看从中国发起注册的」（初始事件属性） | `initial_event.filter` | 只允许 `first.*` |
| 「只看 iOS 端回访的」（回访事件属性） | `return_event.filter` | 只允许 `second.*` |

### 第四步：定时间

相对时间（「上周」「最近 7 天」）先换算为绝对日期写入 `date_range.from_date` / `to_date`；区间应覆盖初始事件及其后续观察周期。

### 第五步：定拆分

`by_fields` 按归属用简写写入：用户维度 `user.*`（属性先经 `metadata.fields` 确认）、初始事件维度 `first.*`、回访事件维度 `second.*`。无需手写初始日期分组字段，结果自动带初始日期分组维度（取值显示在首位 `key_1` 列）。

### 第六步：自检并执行

对照校验速记过（过滤作用域、`duration` 范围、`by_fields` 前缀与去重）→ `--dry-run` → 执行。

### 端到端推导示例

业务输入：「看上周 AppInstall 的用户，往后 14 天里 AppOpen 的留存，只看满足某用户属性条件的用户，按平台拆分。」

1. 定起点/回访：`AppInstall → AppOpen` → `initial_event.event: "AppInstall"`、`return_event.event: "AppOpen"`。
2. 定周期：「往后 14 天」→ `unit: "day"`、`duration: 14`。
3. 定过滤：「某用户属性条件」→ `user_filter`，字段写 `user.<已确认的用户属性>`（先经 `metadata.fields` 确认属性存在与取值）。
4. 定时间：「上周」换算为 2026-06-15 ~ 2026-06-21。
5. 定拆分：「按平台」是回访端属性 → `by_fields: ["second.$platform"]`（结果自动先带初始日期分组维度，取值显示在 `key_1` 列）。
6. `--dry-run` → 执行。

### 调用示例

最小可执行（默认 7 个周期、无过滤）：

```bash
sensors analytics retention --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "initial_event": { "event": "register" },
  "return_event": { "event": "login" },
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-30" }
}
__SENSORS_QUERY__
```

不写 `by_fields` 时，结果仍会自动带上初始日期分组维度（取值显示在首位 `key_1` 列）。

完整示例（初始过滤 + 回访过滤 + 用户过滤 + 多维拆分 + 周留存）：

```bash
sensors analytics retention --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "initial_event": {
    "event": "AppInstall",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "first.$country", "function": "equal", "params": ["中国"] }
      ]
    }
  },
  "return_event": {
    "event": "AppOpen",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "second.$platform", "function": "equal", "params": ["iOS", "Android"] }
      ]
    }
  },
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-30", "timezone": "" },
  "unit": "week",
  "duration": 8,
  "user_filter": {
    "relation": "and",
    "conditions": [
      { "field": "user.<已确认的用户属性>", "function": "equal", "params": ["<取值>"] }
    ]
  },
  "by_fields": ["user.<已确认的用户属性>", "first.$country", "second.$platform"]
}
__SENSORS_QUERY__
```

`return_event.filter` 里用 `equal` 传多值 `["iOS", "Android"]` 表达「属于集合」（IN 语义）；没有 `in` 这个 function。示例中 `user.<已确认的用户属性>` / `<取值>` 为占位形式，实际属性与取值须先经 `metadata.fields` / `metadata.values` 确认后替换。

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。留存专属列名由服务端固定拼接：

| 列名 | 类型 | 含义 | 示例值 |
|---|---|---|---|
| `key_<N>` | string / number | 第 N 个查看维度的取值，类型随维度数据类型（日期 / 枚举维度为 string，数值型维度为 number）；查看维度 = 自动注入首位的初始日期分组 + `by_fields` 各维度（无 `by_fields` 时 `key_1` 即初始日期） | `"2026-06-15 00:00:00.0"` / `1.0` |
| `key_key_rt_init` | number | 初始（留存起始）人数，即该分组批次的起点样本 total | `132.0` |
| `key_key_rt_<N>_rate` | string | 第 N 个留存窗口的留存率，**服务端拼好的字符串**（两位小数 + `%`，如 `"40.00%"`），列类型 STRING | `"40.00%"` |
| `key_key_rt_<N>_entity` | number | 第 N 个留存窗口的留存人数 | `53.0` |
| `key_key_measure_<N>_<M>` | number | 同时显示指标列；仅请求配置留存指标时输出，本 CLI 未暴露留存指标输入，经本命令不会出现 | `—` |

`rate` / `entity` 的 `<N>` 从 1 展开到 `duration` 个留存窗口。`key_1`（初始日期）实际格式带时间部分（如 `"2026-06-15 00:00:00.0"`），做字符串匹配时注意不要按纯日期比对。输出示例（查看维度 2 个、留存窗口 2 个，实际列数按请求展开；`init` / `entity` 为数值，仅 `rate` 是字符串）：

```json
{
  "truncated": false,
  "columns": [
    {"name": "key_1", "display_name": "key_1", "type": "string"},
    {"name": "key_2", "display_name": "key_2", "type": "string"},
    {"name": "key_key_rt_init", "display_name": "key_key_rt_init", "type": "number"},
    {"name": "key_key_rt_1_rate", "display_name": "key_key_rt_1_rate", "type": "string"},
    {"name": "key_key_rt_1_entity", "display_name": "key_key_rt_1_entity", "type": "number"},
    {"name": "key_key_rt_2_rate", "display_name": "key_key_rt_2_rate", "type": "string"},
    {"name": "key_key_rt_2_entity", "display_name": "key_key_rt_2_entity", "type": "number"}
  ],
  "rows": [
    ["2026-06-15 00:00:00.0", "iOS", 200.0, "40.00%", 80.0, "27.50%", 55.0],
    ["2026-06-15 00:00:00.0", "Android", 100.0, "30.00%", 30.0, "20.00%", 20.0]
  ],
  "request_id": "<request_id>"
}
```

`rows` 每行对应一个「初始日期 × 分组」组合（某天发生初始事件的那批用户，叠加 `by_fields` 分组），按 `columns` 顺序取值。**传 `by_fields` 时服务端会额外生成 rollup 汇总行**：每个初始日期下的分组小计行 + 末行全量汇总（`key_key_rt_init` = 各分组之和）。CLI 输出不携带汇总标识（`rollup_columns` 在归一化时被丢弃），汇总行表现为：与某明细行同初始日期、维度值重复出现的行，或末尾维度值为 `null` / 重复分组值的行；识别方式是 `key_key_rt_init` 恰等于同日期各分组之和。汇总行属于汇总层，不要当成单日明细。结构性读法：

- `key_key_rt_<N>_rate` 是服务端格式化好的 STRING（`"40.00%"`），不能当数值做二次计算；需要数值口径时用 `key_key_rt_<N>_entity / key_key_rt_init` 自行计算。
- 关键周期：次日、7 日、30 日或主要观察周期的留存率 / 留存人数。
- 留存拐点：留存明显下滑的周期。
- 分组差异（如有 `by_fields`）：哪个分组留存更高、哪个下滑更快。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `initial_event.event` / `return_event.event` 缺失 | 只给了一边 | 初始与回访事件都必须填 |
| `duration 必须在 0 到 60 之间` / `duration 超出 unit=d 的上限 N` | duration 越界（上限按 `unit` 分档：day 60 / week 45 / month 48） | 调整到对应上限内 |
| `user_filter 仅允许 user.* 字段` | 用户过滤里写了 `first.*`/`second.*` | 用户条件只写 `user.*`，事件条件移到对应事件 `filter` |
| `initial_event.filter 仅允许 first.* 字段` | 初始过滤里写了 `second.*`/`user.*` | 初始事件条件只写 `first.*` |
| `return_event.filter 仅允许 second.* 字段` | 回访过滤里写了 `first.*`/`user.*` | 回访事件条件只写 `second.*` |
| `by_fields 不支持字段: ...` | 非 `user.`/`first.`/`second.`/`event.` 前缀 | 改用允许的前缀之一 |
| `by_fields 不允许重复` | 同一简写字段写了两次 | 去重 |
| `unit` 校验失败 | 写了 `hour` | 留存仅支持 `day` / `week` / `month` |
| 结果里多了一列时间维度 | 结果自动带初始日期分组维度（取值显示在 `key_1` 列） | 正常行为；该维度固定在首位 |
| 集合匹配不知道怎么写 | 想表达「属于多个值」 | 用 `equal` 传多值（`params: ["a","b"]`），无 `in` |
| 过滤条件被拒 | `op`/`values`、非法 `function` 或 `relation` 大写 | 按 [analytics-query-schema.md](analytics-query-schema.md) 重写，`relation` 用小写 |
| 留存大量为 0 / 空 | 回访事件早于初始事件、时间窗太短、过滤过严 | 口径自检通过即为合法空结果，直接报告；左列成因作为排查建议供用户确认，确认后按建议调整 |
| 结果截断 / 采样 | 分组维度多、时间跨度大 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释；降维 / 缩短跨度由调用方决定 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- 进入请求的属性（含 `user.*` 过滤/分组字段）必须先经 `metadata.fields` 确认属性存在、类型与取值，未确认属性不得进入请求。
- 结果固定带初始日期分组维度（取值显示在首位 `key_1` 列），属正常行为。
- `key_key_rt_<N>_rate` 为服务端拼好的百分比字符串，不得当作数值参与计算；数值口径用 `key_key_rt_<N>_entity / key_key_rt_init` 自行计算。
- 留存大量为 0 / 空时先核对初始与回访事件业务先后及 `date_range` 覆盖，不得自动放宽条件重试。
- 回访事件应在业务上确实发生在初始事件之后；多初始 / 多回访联合留存当前不支持。
