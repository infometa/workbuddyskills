# 营销域 — 导购业绩（方案 + 明细 + 看板）查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 业绩方案决定订单业绩值的**取值口径**（按实收金额）与**分享/专属导购分成比例**；同一时刻全租户**仅一个方案生效**（启用新方案会自动将当前生效方案置为未生效）。
> 方案状态：`active` 生效中 / `inactive` 未生效（新建恒为 inactive，须显式启用）。
> 业绩明细由订单完成事件按当前生效方案自动计算落账（一单一条：分享导购/专属导购各自业绩）；运营侧仅查询与统计。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-performance-plan.list 业绩方案列表（含未生效） · guide-performance-plan.active 当前生效业绩方案（无则 null） · guide-performance-detail.search 业绩明细分页（五种分成场景） · guide-performance-detail.stats 业绩统计（分享/专属导购分布） · guide.dashboard.stats 导购看板统计（timeRange：today/week/month/quarter） · guide.dashboard.ranking-top 导购头部排名（rankBy：performance/customers） · guide.dashboard.ranking-bottom 导购尾部排名（识别低绩效；单对象返回） · guide.dashboard.performance-trend 业绩趋势序列（granularity：day/week/month） · guide.dashboard.customer-trend 客户趋势序列 · guide.dashboard.active-plan 看板当前生效方案 ID（Long，非方案对象）
> 写操作见 `guide-performance-action.md`。

---

---

> 明细由订单完成事件按当前生效方案自动计算落账（一单一条：分享导购/专属导购各自业绩）；运营侧仅查询与统计。

---

## ⛔ 未开放端点

无（该模块全部查询、看板与方案管理端点均已开放；业绩明细无写端点）。

---

## ✅ 方案列表 — `ops.marketing.guide-performance-plan.list`

- **说明**：返回全部方案（含未生效），按创建时间倒序。

### 入参

- 无。

### 出参（数组，原始数据）

- **关键字段来源**：`id`（→ 更新/启用/删除）
- **枚举字段**：`status`（active/inactive）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- 其余展示字段：`planName`、`statusDesc`、`valuationRuleSummary`（取值规则摘要）、`splitRuleSummary`（分成规则摘要）。

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.list","input":{},"summary":"列出全部业绩方案及生效状态"}
```

---

## ✅ 当前生效方案 — `ops.marketing.guide-performance-plan.active`

### 入参

- 无。

### 出参（原始数据）

- 结构同方案列表项；**无生效方案时 data 为 null**（此时订单不产生导购分成业绩）。

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.active","input":{},"summary":"查看当前生效的业绩方案"}
```

---

## ✅ 业绩明细分页 — `ops.marketing.guide-performance-detail.search`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| orderNo | String | 否 | 订单号（精确） |
| guideId | String | 否 | 导购 ID（**同时匹配**分享导购或专属导购） |
| splitScene | String | 否 | 分成场景：`cross_guide_cooperation` 跨导购协作 / `same_guide` 同一导购 / `exclusive_only` 仅专属导购 / `share_only` 仅分享导购 / `no_guide` 无导购 |
| startTime | String | 否 | 按**订单时间**过滤，yyyy-MM-dd HH:mm:ss |
| endTime | String | 否 | 同上 |

### 出参（分页，原始数据）

- **枚举字段**：`splitScene`（五种分成场景，见入参）
- **格式敏感字段**：`performanceValue`（订单业绩值，**元**）、`shareGuidePerformance`/`exclusiveGuidePerformance`（分享/专属导购业绩，元）、`orderTime`/（yyyy-MM-dd HH:mm:ss）
- 其余展示字段：`orderNo`、`planName`（计算时方案名快照）、`shareGuideName`/`exclusiveGuideName`、`uid`（买家）。

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-detail.search","input":{"pageNum":1,"pageSize":20,"splitScene":"cross_guide_cooperation"},"summary":"查看跨导购协作的业绩明细"}
```

---

## ✅ 业绩统计卡片 — `ops.marketing.guide-performance-detail.stats`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | String | 否 | 按**订单时间**过滤，yyyy-MM-dd HH:mm:ss |
| endTime | String | 否 | 同上 |

### 出参（原始数据）

- **格式敏感字段**：`totalPerformance`（总业绩值）/`shareGuideTotal`（分享导购合计）/`exclusiveGuideTotal`（专属导购合计）——均为**元**。

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-detail.stats","input":{"startTime":"2026-09-01 00:00:00","endTime":"2026-09-30 23:59:59"},"summary":"统计9月业绩总额及分享/专属导购分布"}
```

---

## ✅ 导购看板统计 — `ops.marketing.guide.dashboard.stats`

- **说明**：导购运营看板的核心指标统计（导购/客户/业绩总量类指标），按时间范围聚合。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | 时间范围：`today` / `week` / `month` / `quarter` |

### 出参（原始数据）

- **展示字段**：看板统计指标（`DashboardStatsVO`）；金额类字段遵循本域约定**单位元**（两位小数）

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.stats","input":{"timeRange":"week"},"summary":"看板本周核心指标"}
```

---

## ✅ 导购排名（Top） — `ops.marketing.guide.dashboard.ranking-top`

- **说明**：指定时间范围内的导购**头部**排名（默认按业绩）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | `today` / `week` / `month` / `quarter` |
| rankBy | String | 否 | 排名维度：`performance`（业绩，默认）/ `customers`（客户） |
| storeId | String | 否 | 限定门店 ID |
| limit | Integer | 否 | 取前 N 名，默认 10 |

### 出参（原始数据）

- 排名列表（`List<RankingItemVO>`）：导购、指标值、名次

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.ranking-top","input":{"timeRange":"week","rankBy":"performance","limit":10},"summary":"本周业绩前十的导购"}
```

---

## ✅ 导购排名（Bottom） — `ops.marketing.guide.dashboard.ranking-bottom`

- **说明**：指定时间范围内的导购**尾部**排名（用于识别低绩效导购）。返回结构为**单个汇总对象**（含尾部名单），与 Top 的列表结构不同。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | `today` / `week` / `month` / `quarter` |
| rankBy | String | 否 | `performance`（默认）/ `customers` |
| storeId | String | 否 | 限定门店 ID |
| limit | Integer | 否 | 取后 N 名，默认 10 |

### 出参（原始数据）

- **格式敏感字段**：`RankingBottomVO`（单对象，含尾部排名明细）

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.ranking-bottom","input":{"timeRange":"week","rankBy":"performance","limit":10},"summary":"本周业绩垫底的导购"}
```

---

## ✅ 业绩趋势 — `ops.marketing.guide.dashboard.performance-trend`

- **说明**：导购业绩随时间的走势序列（看板图表数据源）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | `today` / `week` / `month` / `quarter` |
| granularity | String | 否 | 聚合粒度：`day`（默认）/ `week` / `month` |

### 出参（原始数据）

- 趋势序列（`List<TrendItemVO>`）：时间点 + 指标值

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.performance-trend","input":{"timeRange":"month","granularity":"day"},"summary":"本月按天的业绩走势"}
```

---

## ✅ 客户趋势 — `ops.marketing.guide.dashboard.customer-trend`

- **说明**：导购客户新增/归属随时间的走势序列。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timeRange | String | ✅ | `today` / `week` / `month` / `quarter` |
| granularity | String | 否 | `day`（默认）/ `week` / `month` |

### 出参（原始数据）

- 趋势序列（`List<TrendItemVO>`）

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.customer-trend","input":{"timeRange":"month","granularity":"day"},"summary":"本月按天的客户增长走势"}
```

---

## ✅ 当前生效方案 — `ops.marketing.guide.dashboard.active-plan`

- **说明**：看板当前生效的**业绩方案 ID**。返回的是 `Long` 型方案 ID，不是方案对象；方案详情用 `ops.marketing.guide-performance-plan.list`（或 active 查询）回查。

### 入参

无。

### 出参（原始数据）

- **格式敏感字段**：`Long`——当前生效方案 ID（→ 业绩方案查询的 `planId`）

### 调用示例

```json
{"capability":"ops.marketing.guide.dashboard.active-plan","input":{},"summary":"看板当前生效的业绩方案"}
```

---
