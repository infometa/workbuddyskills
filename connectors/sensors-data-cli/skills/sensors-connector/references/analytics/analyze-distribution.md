# 分布分析
> 工具 `analysis.distribution` · 命令 `sensors analytics distribution` · 类型 查询

## 用途

统计数值指标按区间分桶后各桶的人数 / 次数 / 占比分布（活跃度分布）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | JSON 输入；支持内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | — |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

命令只有 `--input` 与 `--dry-run` 两个专属参数，日期等全部输入通过 `--input` JSON 的 `date_range` 传入。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 分布分析的目标事件名 | `$pageview` |
| `measure` | object | 是 | 结构见下 | 分布对象：对哪个数值做分布 | — |
| `date_range` | object | 是 | 见契约 | 公共日期范围，见 [analytics-query-schema.md](analytics-query-schema.md) | `2026-09-20 ~ 2026-09-26` |
| `bucket_boundaries` | number[] | 否 | 默认 `[]`（服务端自动切桶） | 非空时至少 2 个、全数字、严格递增，如 `[1,3,5,10]` 生成 `[1,3)` `[3,5)` `[5,10)` | `[500,700,900]` |
| `by_field` | string | 否 | 非空 | 拆分维度，单数字段（接口无复数形式） | — |
| `filter` | object | 否 | 过滤树 | 事件筛选，作用于分布分析事件本身 | — |
| `user_filter` | object | 否 | 过滤树 | 用户属性筛选，独立于事件筛选 | — |
| `unit` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour` | `day` |
| `measure_type` | enum | 否 | 默认 `times` | `times` 按次数 / `period` 按天或小时数分布 | `times` |

`measure` 对象：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 事件名（允许传字符串简写，CLI 自动包装；通常与顶层 `event` 相同） | `$pageview` |
| `aggregator` | enum | 否 | 默认 `general` | `general` 总次数 / `unique` 去重人数 / `average` 人均次数（均为计数类，不带 `field`）；`sum` / `avg` / `max` / `min` 数值聚合（必须带 `field`）；`distinct_count` 兼容写法，CLI 归一化为 `unique` | `sum` |
| `field` | string | 条件 | 三段式 | 数值类聚合（`sum`/`avg`/`max`/`min`）必填；计数类（`general`/`unique`/`average`）不允许填 | `event.$pageview.$screen_height` |
| `filter` | object | 否 | 过滤树 | 指标级过滤，仅对该 measure 事件生效 | — |

校验速记（构造后必过）：

- `event` 与 `measure.event` 必填非空；`measure` 是 JSON 对象不是字符串。
- `aggregator` 为 `sum`/`avg`/`max`/`min` 时 `measure.field` 必填且必须是三段式；计数类（`general`/`unique`/`average`）不允许带 `field`（注意 `average` 是人均次数、属计数类；数值均值用 `avg`）。
- `bucket_boundaries` 非空时至少 2 个边界点、全数字、严格递增。
- `by_field` 是单数，只支持单维度；写复数 `by_fields` 不生效。
- `measure_type` 只允许 `times` / `period`，不传自动补 `times`。
- 过滤树 `relation` 只接受小写 `and` / `or`。

过滤树与聚合器配套规则见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定事件

确认分布分析的事件名为已确认的精确标识（如 `e2e_add_to_cart`）。

### 第二步：定分布对象（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「每次加购数量的分布」「订单金额区间分布」 | `measure.aggregator: "sum"` + 三段式 `field`（数值属性求和后分桶，最常见） |
| 「按次数看分布」 | `measure.aggregator: "general"`，不填 `field` |
| 「按人数看分布」 | `measure.aggregator: "unique"`，不填 `field` |

`measure.event` 填分布事件名（与顶层 `event` 相同）；数值属性字段须确认为精确三段式路径 `event.<event>.<prop>`。

### 第三步：定分桶（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「分成 3 段：1-3、3-5、5 以上」 | `bucket_boundaries: [1, 3, 5]`，生成 `[1,3)` `[3,5)` `[5,∞)` |
| 「按 1/3/5/10 件分桶」 | `bucket_boundaries: [1, 3, 5, 10]`，生成 `[1,3)` `[3,5)` `[5,10)` `[10,∞)` |
| 无明确区间要求 | 省略该字段，服务端自动切桶 |

边界值是切分点数字数组，须严格递增；区间业务含义应与调用方对齐后再写入。

### 第四步：定拆分

有按维度对比需求（如「iOS vs Android 加购数量分布」）时填 `by_field`（单字段：事件属性 `event.<event>.<prop>` 或用户属性 `user.<prop>`）；无需求不填。

### 第五步：定时间

相对时间（「上周」「最近 7 天」）先换算为绝对日期写入 `date_range`；需要按时间展开分布时配 `unit`（默认 `day`）。

### 第六步：定过滤

用户属性过滤放 `user_filter`，事件属性过滤放 `filter`，二者可同时存在。

### 第七步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 端到端推导示例

业务输入：「2026 年 5 月 27 日至 6 月 8 日，用户『加入购物车』行为中『数量』属性的分布，按 1/3/5/10 件分桶。」

1. 定事件：「加入购物车」确认为 `e2e_add_to_cart`。
2. 定分布对象：「数量」确认为 `e2e_quantity`；按求和口径 → `aggregator: "sum"`，`field: "event.e2e_add_to_cart.e2e_quantity"`。
3. 定分桶：按 1/3/5/10 件 → `bucket_boundaries: [1, 3, 5, 10]`。
4. 定拆分：未要求 → 不填 `by_field`。
5. 定时间：直接填绝对日期 2026-05-27 ~ 2026-06-08。
6. 定过滤：未提 → 不填。

### 调用示例

数值属性分布 + 自定义分桶：

```bash
sensors analytics distribution --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "event": "e2e_add_to_cart",
  "measure": {
    "event": "e2e_add_to_cart",
    "aggregator": "sum",
    "field": "event.e2e_add_to_cart.e2e_quantity"
  },
  "bucket_boundaries": [1, 3, 5, 10],
  "measure_type": "times",
  "date_range": { "from_date": "2026-05-27", "to_date": "2026-06-08" }
}
__SENSORS_QUERY__
```

完整示例（拆分维度 + 用户过滤）：

```bash
sensors analytics distribution --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "event": "order_pay",
  "measure": {
    "event": "order_pay",
    "aggregator": "sum",
    "field": "event.order_pay.amount"
  },
  "bucket_boundaries": [0, 100, 500, 1000, 5000],
  "measure_type": "times",
  "by_field": "user.$province",
  "user_filter": {
    "relation": "and",
    "conditions": [
      { "field": "user.is_vip", "function": "isTrue" }
    ]
  },
  "date_range": { "from_date": "2026-06-01", "to_date": "2026-06-25" },
  "unit": "day"
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。专属动态列（N 为桶序号，从 1 开始，与 `bucket_boundaries` 切分的区间一一对应）：

| 列名模式 | 含义 | 示例值 |
|---|---|---|
| `by_value` | 恒输出：无 `by_field` 时承载 `unit` 时间点，有 `by_field` 时承载拆分维度取值 | `2026-09-20` / `网页` |
| `total_user` | 总用户数（去重） | `4989.0` |
| `unique_average` | 人均值（总次数 ÷ 总人数） | `1.0` |
| `bucket_region_N` | 第 N 桶区间范围字符串，如 `[1, 3)` | `[500.0, 700.0)` |
| `addiction_user_bucket_N` | 第 N 桶用户数（去重） | `87.0` |
| `addiction_rate_bucket_N` | 第 N 桶占比，0~1 小数（`1.0` = 100%） | `0.0174` |
| `addiction_measure_bucket_N` | 第 N 桶 measure 值；仅服务端请求携带附加指标时输出，本 CLI 未暴露附加指标输入，经本命令不会出现 | — |
| `total_measure` | measure 汇总值；同上仅附加指标场景输出，经本命令不会出现 | — |

结构性读法：

- 主结论：找最大 `addiction_rate_bucket_N` 的桶，即「最集中的区间是 X，占 Y%」。
- 长尾识别：最后一个桶（含 ∞ 区间）占比高时，说明存在高值长尾，可建议细化该区间的分桶边界。
- 拆分对比：有 `by_field` 时按 `by_value` 分行，比较不同分组的分布形态差异。
- 空桶：`addiction_user_bucket_N = 0` 正常，说明该区间无数据，不代表数据缺失。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `属性聚合必须提供 field` | `aggregator` 为数值类但缺 `field` | 补三段式 `event.<event>.<prop>` |
| `计数类聚合不允许提供 field` | 计数类聚合填了 `field` | 删除 `field` |
| `bucket_boundaries 至少需要 2 个边界点` | 边界少于 2 个 | 至少 2 个，或省略该字段走自动切桶 |
| `bucket_boundaries[i] 必须为数字` | 元素含字符串等非数字 | 全部改为数字 |
| `bucket_boundaries 必须严格递增` | 等值或乱序 | 按升序排列（如 `[1, 3, 5, 10]`） |
| `by_field 不能为空字符串` | 拆分维度为空白 | 省略该字段或传合法字段 |
| 拆分不生效 | 写了复数 `by_fields` | 接口只支持单数 `by_field` |
| 桶区间不合理（太宽 / 太窄） | `bucket_boundaries` 设置不当 | 与调用方确认业务合理的切分点，或先不传让服务端自动切桶 |
| 所有桶数据为 0 | 事件名或属性名有误、时间范围无数据 | 先确认事件 / 属性存在且有数据（`has_data`），是否重查由调用方决定 |
| 结果截断 / 采样 | 时间跨度大、拆分维度基数高 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释；缩短时间或不拆分由调用方决定 |
| 空结果 | 日期范围无匹配数据、过滤过严 | 先去掉过滤验证（由调用方决定），不自动放宽重试 |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- `addiction_user_bucket_N = 0` 表示该区间无数据，不代表数据缺失。
- `truncated=true` 原样传回；空结果不得自动放宽条件重试。
