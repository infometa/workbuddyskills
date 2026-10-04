# LTV 分析
> 工具 `analysis.ltv` · 命令 `sensors analytics ltv` · 类型 查询

## 用途

从指定起点（起点事件或用户时间属性）统计用户在未来 N 个周期的累计价值（LTV）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 输入层 JSON；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；须显式使用 `--input` 或 `--days` 之一 | `-` |
| `--days` | int | 否 | 无 | 最近 N 天的快捷日期范围，与 `--input` 中的 `date_range` 互斥；必须为正整数；CLI 自动转换为 `from_date` / `to_date` | — |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | — |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `start_sign` | object | 是 | 结构见下 | LTV 计算的用户起点定义 | `{"start_event":"$AppStart"}` |
| `measures` | object[] | 是 | 至少 1 项 | 营收事件指标列表，结构见下 | `[{"event":"$AppViewScreen","aggregator":"average","name":"人均浏览次数"}]` |
| `date_range` | object | 是 | 见契约 | 公共日期范围（用 `--days` 时可省略），见 [analytics-query-schema.md](analytics-query-schema.md) | `2026-09-20 ~ 2026-09-26` |
| `time_bucket` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour` | `day` |
| `duration` | int | 否 | 默认 `7` | 观测周期数，正整数 | `7` |
| `by_fields` | string[] | 否 | 默认 `[]`，元素非空 | 分组维度；时间分组 `event.$Anything.$time` 由 CLI 自动注入 | — |
| `filter` | object | 否 | 过滤树 | 顶层事件筛选 | — |
| `subject_id` | string | 否 | 默认 `$user_id` | 分析主体 ID | — |

`start_sign`（`start_event` 与 `start_time_field` 二选一，不能同时提供或同时缺失）：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `start_event` | string | 二选一 | 起点事件名，如 `$AppInstall` | `$AppStart` |
| `start_time_field` | string | 二选一 | 起点时间属性，如 `user.register_time`；数据类型须为 DATE/DATETIME。该字段作为独立起点依赖服务端支持；被服务端拒绝时（message 含 `start_event should not be null`）改用 `start_event` 起点 | — |
| `filter` | object | 否 | 起点事件过滤（过滤树），写 `event.<start_event>.<prop>` 或 `user.<prop>` | — |

`measures[]` 每项：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 营收事件名 | `$AppViewScreen` |
| `aggregator` | enum | 否 | 默认 `average` | `average`=整体人均次数（不许带 `field`）；`LTV_AVG`=按字段累计求和后人均（必须带 `field`）；大小写任意写法会归一化 | `average` |
| `field` | string | 条件 | 三段式 | 仅 `LTV_AVG` 需要且必须填写，如 `event.purchase.revenue` | — |
| `name` | string | 否 | — | 指标展示名 | `人均浏览次数` |
| `filter` | object | 否 | 过滤树 | 营收事件过滤 | — |

`by_fields` 取值规则：

| 规则 | 说明 |
|---|---|
| 用户字段 | 写 `user.<prop>`，原样透传 |
| 事件字段 | 统一写 `event.$Anything.<prop>`；不要把具体事件名拼进分组字段，否则语义会偏到该事件上 |

校验速记（构造后必过）：

- `start_sign` 里 `start_event` 与 `start_time_field` 恰好提供一个。
- `measures` ≥ 1 且每项是 JSON 对象（至少含 `event` 键）；`LTV_AVG` 带三段式 `field`、`average` 不带。
- `duration` 必须是正整数；`time_bucket` 为小写枚举之一。
- 过滤树 `relation` 只接受小写 `and` / `or`。

业务正确性约定（CLI 不强制校验，需自行保证）：

- 起点和价值是两类不同对象，不能混写（典型错误：把价值事件当成起点）；起点和价值事件之间应有合理业务因果关系（先注册后付费）。
- 起点样本范围的条件写 `start_sign.filter`；价值口径限定（如「金额 > 0 的订单」）写 `measures[].filter`；顶层 `filter` 作用于整条查询的事件筛选。

已知差异（写了不生效，统一走平台默认）：自定义观测周期数展示列（如只看 LTV0/1/7/30）、自定义汇总/明细切换、行数上限、多主体。以上差异如实告知用户即可，不做 SQL 兜底。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定起点（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「注册后 30 天累计 GMV」「首购后 N 天累计支付」 | `start_sign.start_event`（起点用事件）+ `start_sign.filter`（如「lib=python 起点」） |
| 「按 `register_time` 起算的累计价值」 | `start_sign.start_time_field`（起点用时间属性，与 `start_event` 互斥） |

`start_time_field` 指向的用户属性数据类型必须是 `DATE` / `DATETIME`（可用元数据命令确认 `data_type`），STRING 类型的日期属性不可用，否则服务端查询引擎报错。

### 第二步：定价值

经确认的 `measures[].event`（价值事件名）与 `measures[].field`（三段式价值字段，如 `event.pay_order.revenue`）；整体人均口径用 `average`（不带 `field`），按字段求和用 `LTV_AVG`（必带 `field`）。

### 第三步：定过滤

限定起点样本写 `start_sign.filter`；限定价值口径写 `measures[].filter`；不要把两类条件都堆到顶层 `filter`。

### 第四步：定时间与粒度

相对时间换算为绝对 `date_range`，或用 `--days N` 快捷参数（二选一，互斥）；`time_bucket` 默认 `day`。

### 第五步：定拆分

`by_fields` 用户字段原样（`user.<prop>`），事件字段统一写 `event.$Anything.<prop>`。

### 第六步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 端到端推导示例

业务输入：「注册（lib=python）后 30 天，按已确认的用户属性拆分，看 `pay_order.revenue` 累计收入。」

1. 定起点：「注册之后」→ `start_sign.start_event: "register"`，附 `filter` 限 `event.register.$lib = python`。
2. 定价值：`measures[].event: "pay_order"`，带 `field` 求和口径 → `aggregator: "LTV_AVG"`，`field: "event.pay_order.revenue"`。
3. 定过滤：起点条件写入 `start_sign.filter`。
4. 定时间：「最近 30 天」用 `--days 30` 或绝对 `date_range`；`time_bucket: "day"`。
5. 定拆分：按已确认的用户属性分组（先经 `metadata.fields` 确认属性存在与取值）→ `by_fields: ["user.<已确认的用户属性>"]`。
6. `--dry-run` → 执行。

### 调用示例

最小可执行（单价值事件 + `--days 30`）：

```bash
sensors analytics ltv --ai-session-id <ai_session_id> --days 30 --dry-run --input - <<'__SENSORS_QUERY__'
{
  "start_sign": { "start_event": "register" },
  "measures": [
    { "event": "pay_order", "aggregator": "LTV_AVG", "field": "event.pay_order.revenue" }
  ]
}
__SENSORS_QUERY__
```

完整示例（起点过滤 + 价值过滤 + 按用户属性拆分 + 自定义时区）：

```bash
sensors analytics ltv --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "start_sign": {
    "start_event": "register",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "event.register.$lib", "function": "equal", "params": ["python"] }
      ]
    }
  },
  "measures": [
    {
      "event": "pay_order",
      "aggregator": "LTV_AVG",
      "field": "event.pay_order.revenue",
      "filter": {
        "relation": "and",
        "conditions": [
          { "field": "event.pay_order.amount", "function": "greater", "params": [0] }
        ]
      }
    }
  ],
  "date_range": { "from_date": "2026-02-01", "to_date": "2026-02-28", "timezone": "UTC+08:00" },
  "time_bucket": "day",
  "by_fields": ["user.<已确认的用户属性>"]
}
__SENSORS_QUERY__
```

`user.<已确认的用户属性>` 为占位形式，实际分组字段须先经 `metadata.fields` 确认存在与取值后替换。

用时间属性作为起点（独立使用依赖服务端支持，被拒时见输入 Schema `start_time_field` 行的处置说明）：

```bash
sensors analytics ltv --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "start_sign": { "start_time_field": "user.register_time" },
  "measures": [
    { "event": "pay_order", "aggregator": "LTV_AVG", "field": "event.pay_order.revenue" }
  ],
  "date_range": { "from_date": "2026-02-01", "to_date": "2026-02-28" }
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。专属列名规律：

| 列名模式 | 含义 | 示例值 |
|---|---|---|
| `event.$Anything.<prop>` / `user.<prop>` | 分组字段 | `event.$Anything.$time` |
| `measure_name` | 价值指标名；单价值事件时可能为空字符串 | `人均浏览次数` |
| `date` | 起点日期（按起点事件/时间属性发生日期分批） | `2026-09-20` |
| `initial_user` | 该起点日期的起点用户数 | `132.0` |
| `amount_ltv_<N>` | 第 N 周期累计价值（如 `amount_ltv_0`、`amount_ltv_7`） | `8.33` |
| `rate_ltv_<N>` | 第 N 周期累计价值率 | `0.0` |

值为 `null` 表示该周期未到达或当前起点人群无对应数据。LTV 展示列（`<N>` 取值集合）由服务端按 `time_bucket` 决定并按数据可计算性截断（如 `初始日期+N` 超出查询窗口即止），以实际返回 `columns` 为准；`duration` 是计算窗口参数，不直接决定展示列数，输入层不可自定义展示列。

结构性读法：先看哪个分组累计价值最高、在哪个周期开始放缓；LTV0 为起始值，LTV7 / LTV30 等为关键节点；`null` 多时在报告中提示可能成因（起点人群与价值事件时间窗错位），是否排查由用户决定。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `start_sign 只能配置 start_event 或 start_time_field 其中一个，不能同时提供` | 两者都填 | 二选一 |
| `start_sign 必须配置 start_event 或 start_time_field 其中一个` | 两者都缺 | 补其一 |
| `field 必须是三段式字段名` | 价值字段非三段式 | 改为 `event.<event>.<prop>` |
| `aggregator 仅支持 average/LTV_AVG` | 其它聚合名 | 按整体人均 / 按字段求和二选一 |
| `aggregator 为 average 时，不能填写 field` / `为 LTV_AVG 时，field 不能为空` | `field` 与聚合口径不匹配 | 按配套规则补删 `field` |
| `measures 至少需要 1 项` | `measures` 为空数组 | 至少 1 项；多价值事件加权当前不支持，如实告知 |
| `duration 必须是正整数` | `duration <= 0` | 传正整数 |
| `--days 必须是正整数` / `--days 与 --input 中的 date_range 互斥` | 快捷参数冲突 | 只保留一种日期传法 |
| 服务端查询引擎错误 | `start_time_field` 指向非 DATE/DATETIME 属性（message 含 `data type must be date / datetime`）；其余多为引擎内部异常，通常与参数无关 | 属性类型问题改用 DATE/DATETIME 字段或改 `start_event` 起点；其余附 `request_id` 联系技术支持，勿反复重试 |
| 起点用了非业务起点的事件 | 起点选错（如把「支付」当起点） | 与调用方确认业务真实起点 |
| 累计价值异常低 / 大量 `null` | 起点人群与价值事件时间窗错位 | 检查 `date_range` 是否覆盖起点之后的足够周期 |
| `by_fields` 写具体事件名不生效 | 事件分组字段应统一写 `event.$Anything.<prop>` | 改写 `$Anything` 形式或转 `user.<prop>` |
| 时区写 `DAY` / `WEEK` 等大写 | 输入层只接受小写 | 用 `day` / `week` / `month` / `hour` |
| 结果截断 / 采样 | 时间跨度大、起点日期分组多 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释；缩短跨度由调用方决定 |
| 空结果 | 起点过严 / 时间窗短 / 命名错 | 只说明当前条件下无结果；是否复核 `has_data` 由调用方决定 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- 进入请求的属性必须先经元数据确认（用户属性用 `metadata.fields`；`start_time_field` 还须确认数据类型为 DATE / DATETIME），未确认属性不得进入请求。
- 分组字段统一写 `event.$Anything.<prop>` 或 `user.<prop>`，写具体事件名的分组不生效。
- 空结果不得自动放宽条件重试；`truncated=true` 原样传回。
