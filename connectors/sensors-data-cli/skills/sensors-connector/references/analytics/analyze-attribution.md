# 归因分析
> 工具 `analysis.attribution` · 命令 `sensors analytics attribution` · 类型 查询

## 用途

按选定归因模型计算各归因触点事件对目标转化事件的贡献度。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

执行时自动检测 SA 版本选择 v1 / v2 接口，输入输出结构一致。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `target_event` | object | 是 | 结构见下 | 目标转化事件（允许字符串简写） | `{"event":"$AppEnd"}` |
| `attribution_events` | object[] | 是 | 至少 1 项 | 归因触点事件列表（元素允许字符串简写） | `[{"event":"$AppStart"},{"event":"$AppViewScreen"}]` |
| `date_range` | object | 是 | 见契约 | 公共日期范围，见 [analytics-query-schema.md](analytics-query-schema.md) | `2026-09-20 ~ 2026-09-26` |
| `model` | enum | 否 | 默认 `last_touch` | `first_touch` / `last_touch` / `linear` / `time_decay` | `last_touch` |
| `lookback_window` | object | 否 | 默认 `{value: 90, unit: "day"}` | 回溯窗口，结构见下；`value: 0` 为空回溯窗口（触点不计入归因），服务端无「不限制」语义，勿显式传 0 | — |

`target_event` 每项：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 目标转化事件名 | `$AppEnd` |
| `aggregator` | enum | 否 | 默认 `general` | `field` 配套规则见 [analytics-query-schema.md](analytics-query-schema.md) | `general` |
| `field` | string | 条件 | 三段式 | 数值类聚合必填；计数类不允许填 | — |
| `filter` | object | 否 | 过滤树 | 目标事件过滤 | — |

`attribution_events[]` 每项：`event`（必填，触点事件名）、`filter`（可选，触点过滤，字段应属于该触点事件）。

`lookback_window`：`value`（int，≥ 0，**0 为空回溯窗口，触点不计入归因，勿显式传 0**）、`unit`（`day` / `week` / `month` / `hour`，默认 `day`）。回溯窗口粒度只在 `lookback_window.unit` 设置，请求外层无 `unit` 字段。默认 90 天回溯；归因结果触点全为 0 时优先检查是否把窗口设成了 0。

校验速记与业务正确性约定：

- `target_event` / `attribution_events[]` 每项是 JSON 对象（至少含 `event` 键）；字符串简写（`"target_event": "arrival"`）兼容但不推荐。
- 过滤只有事件级入口：用户级/顶层过滤当前不在输入层暴露，目标条件写 `target_event.filter`，触点条件写对应 `attribution_events[].filter`；字段事件名必须等于所属事件。
- 触点应是业务上真实发生在目标转化之前的行为，否则贡献分配口径失真。
- 关联事件、直接转化参与归因、使用缓存、汇总/明细切换、行数上限、触点维度拆分等高级项走平台默认，不可配。
- 过滤树 `relation` 只接受小写 `and` / `or`。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定目标（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「看 X 转化是谁带来的」「X 之前哪些行为起作用」 | `target_event.event`（被归因的目标转化事件） |
| 「按转化次数算贡献」（默认） | `target_event.aggregator: "general"`，不带 `field` |
| 「按转化人数算贡献」 | `target_event.aggregator: "unique"`，不带 `field` |
| 「目标看转化金额 / 时长」 | `target_event.aggregator: "sum"` + 三段式 `target_event.field` |

### 第二步：定触点

把所有待归因触点逐个列入 `attribution_events`（每个一项，至少 1 个），逐个确认事件名；未确认的口语词先解决，多候选不自行二选一。

### 第三步：定模型（值映射）

| 业务表达 | `model` |
|---|---|
| 「首次接触」「首触」 | `first_touch` |
| 「末次接触」「末触」（默认） | `last_touch` |
| 「线性」 | `linear` |
| 「时间衰减」 | `time_decay` |

### 第四步：定时间与回溯窗口

相对时间（「上周」「最近 7 天」）先换算为绝对日期写入 `date_range`。需要限定窗口期时传 `lookback_window`（如 `{value: 30, unit: "day"}` 表示 30 天回溯窗口；默认 90 天，`value: 0` 为空回溯窗口，勿显式传 0）。

### 第五步：定过滤（按归属分流）

| 业务表达 | 写入位置 |
|---|---|
| 「只看金额 ≥ 100 的转化」（目标事件属性） | `target_event.filter` |
| 「只看某来源的触点」（某触点属性） | 该触点的 `attribution_events[].filter` |

### 第六步：自检并执行

对照校验速记过（目标聚合器与 field 配套、触点至少 1 个、model 取值合法）→ `--dry-run` → 执行。比较不同模型须分别以不同 `model` 各执行一次。

### 端到端推导示例

业务输入：「看上周『到达』转化的渠道贡献，把『App 启动』『App 点击』两个触点拿来按末次接触归因，只看金额 ≥ 100 的到达。」

1. 定目标：「到达」确认为 `arrival` → `target_event.event: "arrival"`；按次数 → `aggregator: "general"`。
2. 定触点：确认为 `$AppStart`、`$AppClick` → `attribution_events: [{event: "$AppStart"}, {event: "$AppClick"}]`。
3. 定模型：「末次接触」→ `model: "last_touch"`。
4. 定时间：「上周」换算为 2026-06-15 ~ 2026-06-21。
5. 定过滤：「金额 ≥ 100」是目标事件属性 → `target_event.filter`，字段 `event.arrival.amount`。
6. `--dry-run` → 执行。

### 调用示例

最小可执行（单触点、默认末次接触模型）：

```bash
sensors analytics attribution --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "target_event": { "event": "arrival" },
  "attribution_events": [
    { "event": "$AppStart" }
  ],
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-07" }
}
__SENSORS_QUERY__
```

完整示例（属性聚合目标 + 目标过滤 + 触点过滤 + 线性模型）：

```bash
sensors analytics attribution --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "target_event": {
    "event": "payOrder",
    "aggregator": "sum",
    "field": "event.payOrder.amount",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "event.payOrder.amount", "function": "greaterEqual", "params": [100] }
      ]
    }
  },
  "attribution_events": [
    { "event": "$AppStart" },
    {
      "event": "$AppClick",
      "filter": {
        "relation": "and",
        "conditions": [
          { "field": "event.$AppClick.$lib", "function": "equal", "params": ["python"] }
        ]
      }
    }
  ],
  "model": "linear",
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-07", "timezone": "" }
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。无查看维度时 `columns` 固定 12 列（1 维度 + 11 指标），以实际返回为准：

| 列名 | 含义 |
|---|---|
| `ATTRIBUTION_EVENT` | 触点事件名；`null` 行为「直接转化」（无触点、直接完成转化），末行为目标事件全量汇总 |
| `total_attribution_event_number` / `total_attribution_event_user_number` | 触点事件总次数 / 总人数 |
| `attribution_event_number` / `attribution_event_user_number` | 参与归因的触点次数 / 人数 |
| `converted_attribution_event_number` / `converted_attribution_event_user_number` | 归因到转化的触点次数 / 人数 |
| `converted_attribution_event_number_rate` | 归因转化次数占比 |
| `target_event_value` / `target_event_user_number` | 目标事件价值（`sum` 聚合时）/ 目标人数 |
| `conversion_rate` | 转化率 |
| `contribution_value` | **贡献占比**（该触点分摊的目标贡献占总贡献的比例，各触点之和约 100）；核心结论列 |

带 `by_fields` 分组时另加分组维度列，组内仍有直接转化行与末行汇总（`rollup_columns` 层级）。比较不同归因模型须分别以不同 `model` 各执行一次，解读时须结合请求里的 `model`。通常为单表返回（分组维度在表内表达）；个别环境多触点分组返回多张表，CLI 取第一张。

结构性读法：先识别贡献指标列，按贡献从高到低排序指出贡献最高的触点；给结论（哪个触点贡献最高）→ 数字支撑 → 有采样/截断则提示前提。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `target_event.event` 缺失 | 没给目标转化事件 | 补 `target_event.event` |
| `attribution_events 至少需要 1 个归因触点事件` | 触点列表为空 | 至少 1 个触点 |
| `model` 校验失败 | 写了 `position` / `first` / 中文名 / 大写 | 改用四个枚举值之一 |
| `属性聚合必须提供 field` / `计数类聚合不允许提供 field` | 目标事件聚合与 `field` 不匹配 | 按 [analytics-query-schema.md](analytics-query-schema.md) 配套规则修正 |
| `lookback_window.value 必须 >= 0` | 窗口值为负 | 正整数（默认 90）；0 为空回溯窗口，勿显式传 |
| 写了 `user_filter` / 顶层 `filter` 没生效 | 输入层未暴露这些字段 | 目标条件写 `target_event.filter`，触点条件写对应 `attribution_events[].filter` |
| 想自定义 `limit` / 触点拆分没生效 | CLI 输入层当前未暴露 | 走平台默认，如实告知当前不支持自定义 |
| 触点过滤用了别的事件的字段 | 把目标字段写到触点 `filter` 里 | 字段事件名必须等于所属事件 `event` |
| 过滤条件被拒 | `op`/`values` 或非法 `function` | 按 [analytics-query-schema.md](analytics-query-schema.md) 重写；集合匹配用 `equal` 传多值 |
| 结果截断 / 采样 | 触点多、时间跨度大 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释，不下「Top / 唯一贡献」结论 |
| 空结果 | 条件过严、命名错、区间无数据 | 只说明当前条件下无结果；是否复核 `has_data` 由调用方决定 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- 触点 `filter` 引用其它事件的字段不报错但语义错误，须保证字段事件名等于所属触点 `event`。
- `truncated=true` 时不得宣称「Top / 唯一贡献」；空结果不得自动放宽条件重试。
