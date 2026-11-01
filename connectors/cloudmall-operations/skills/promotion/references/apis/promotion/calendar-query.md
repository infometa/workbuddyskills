# 促销域 — 促销日历与主题查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 日历按毫秒时间戳窗口返回活动与主题快照；主题是活动分组容器，删除主题不删活动。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 calendar.view · theme.detail · theme.eligible-targets · theme.eligible-activities
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 主题维护（创建/编辑/工作副本/删除/归组/移出）见 `calendar-action.md`；写操作的 expectedRevision 从本文件 theme.detail 的 revision 取当前值。

---

## ✅ 查询促销日历 — `ops.promotion.calendar.view`

仅查询正式主表，按 lifecycleStart..endTime 与查询窗口相交取数（有效预热开始 >0 时 lifecycleStart 用预热开始，否则用活动开始）；不包含 pending 草稿。当前不按状态或大类筛选，匹配时间条件的未逻辑删除记录可含已结束/暂停活动，以及 promotionCode=COUPON 的券模板对应活动。计数或列业务活动时按 activities[].promotionCode/promotionStatus 区分，不把券模板混计为用户要求的普通活动。返回范围是当前窗口，不能由空日历断言租户没有活动或主题。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rangeStart | String | ✅ | 时间范围开始（毫秒时间戳，包含端点） |
| rangeEnd | String | ✅ | 时间范围结束（毫秒时间戳，包含端点） |

### 自然日与月份窗口

查询采用闭区间：活动结束时间 ≥ rangeStart 且生命周期开始时间 ≤ rangeEnd。用户按自然日或月份查询时，先按已确认的业务时区计算本期起点与下一期起点，再令 rangeEnd = 下一期起点 − 1 毫秒；不能把下月零点作为排他端点直接提交，否则会包含恰在下月零点开始的活动。显式给出的起止时刻按用户含义保留，不对所有结束时间机械减 1。月份按日历推进，覆盖跨年和闰年，不用固定 30 天或执行环境默认时区。

例如已确认使用 Asia/Shanghai 时，2026 年 11 月为 rangeStart=1793462400000、rangeEnd=1796054399999，即 11 月 1 日 00:00:00 至 11 月 30 日 23:59:59.999。其他时区按用户指定或已确认的业务时区重新计算，未确认时区时先确认再构造自然日区间。

### 出参（原始数据）

- **关键字段来源**：`themes[].themeId`（→ 主题编辑/删除/归组）、`activities[].promotionId`（→ 活动详情）、`unassignedActivities[].promotionId`（未归属活动，归组候选）
- **枚举字段**：`activities[].promotionStatus`（1..7）、`activities[].promotionSubCode`
- **格式敏感字段**：`activities[].startTime`/`endTime`/`preheatStartTime`/`lifecycleStart`（毫秒时间戳）
- `conflicts[]` 为窗口内返回记录的**纯时间重叠对**，当前检测不按状态、大类、层级、商品、门店、人群或 stackableExclusions 筛选（`leftPromotionId` = 两者中较小 ID / `rightPromotionId` = 较大 ID / `overlapStart` = 两者 lifecycleStart 较大者 / `overlapEnd` = 两者 endTime 较小者）。边界相接也算重叠，overlapStart=overlapEnd 可以合法出现；重叠区间按完整生命周期计算，不裁剪到查询窗口，区间超出窗口可以成立。无效生命周期不参与检测。时间重叠不证明优惠互斥、创建失败或实际订单叠加冲突，不能据此自动停用/改期。若用户限定普通活动/进行中记录，只保留符合大类和状态要求的活动及两端均符合条件的冲突对，不能沿用原始conflictCount作筛后数量。
- `summary` 五项**真实字段名**：

| 字段 | 说明 |
|------|------|
| themeCount | 主题数——⚠️ **只统计本次窗口内有活动归属的主题**（无活动归属的空主题不计入，与 theme.detail 能查到空主题不同） |
| assignedActivityCount | 已归属活动数 |
| unassignedActivityCount | 未归属活动数（候选归组） |
| conflictCount | 时间冲突对数 |
| currentActivityCount | 本次窗口内返回活动中 promotionStatus=4 的数量；不是全租户当前进行中总数 |

summary 五项均为本次返回的未筛原始计数，匹配窗口的 COUPON 记录和全部状态按各字段定义参与计数；用户指定普通活动/某状态时，基于实际记录重新筛选计数，不能沿用原始 summary。空日历时五项全为 0。

### 调用示例

```json
{"capability":"ops.promotion.calendar.view","input":{"rangeStart":"1790784000000","rangeEnd":"1793462399999"},"summary":"查看2026年十月的促销日历（Asia/Shanghai）"}
```

---

## ✅ 主题详情 — `ops.promotion.theme.detail`

- **语义**：读取**完整主题**——包含时间窗口外成员及空主题。编辑回填/取乐观锁 revision 以此接口为准（calendar 视图仅含窗口内活动）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| themeId | String | ✅ | 主题 ID |

### 出参（原始数据）

- **出参仅 7 个字段**：`themeId` / `revision` / `name` / `startTime` / `endTime` / `promotionIds[]` / `activityCount`——**没有归组明细**，成员只有 ID 列表。查成员名称/状态按 promotionIds 用 activity.search 或逐项 activity.detail；theme.eligible-activities 可提供候选标题，但不返回 promotionStatus 且有周期筛选，不能代替完整成员状态查询。
- **关键字段来源**：`themeId`、`revision`（主题乐观锁——**所有主题写操作的 expectedRevision 必须取此字段当前值**（创建传 0 除外）；整数，经专用序列化器保持 JSON 数字）、`promotionIds[]`（完整成员列表，含窗口外成员）、`activityCount`（= `promotionIds.length`）
- **格式敏感字段**：`startTime`/`endTime`（毫秒时间戳）

### 调用示例

```json
{"capability":"ops.promotion.theme.detail","input":{"themeId":"5100000000000000001"},"summary":"查看主题完整成员与当前版本号"}
```

---

## ✅ 活动可放置主题查询 — `ops.promotion.theme.eligible-targets`

- 归组前预检：eligible 仅表示主题时间覆盖活动完整生命周期（含预热），不证明当前账号具备写权限或最新 revision 仍可提交；实际写入仍遵循 calendar-action 的版本与业务前置。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 活动 ID |

### 出参（数组，原始数据）

- 每项：`themeId`/`name`/`startTime`/`endTime`（毫秒时间戳）、`eligible`（是否可放置）、`reasonCode`（不可放原因码：THEME_PERIOD_NOT_COVER_ACTIVITY 主题周期未覆盖活动 等）、`current`（当前所在主题）。

### 调用示例

```json
{"capability":"ops.promotion.theme.eligible-targets","input":{"promotionId":"4100000000000000001"},"summary":"查询该活动可放入哪些主题"}
```

---

## ✅ 主题候选活动查询 — `ops.promotion.theme.eligible-activities`

- 按主题周期分页查完整生命周期被覆盖的正式主表记录（含预热，起止边界可相等）；与日历“窗口相交”口径不同。此查询没有状态或大类筛选，候选可能含已结束/暂停的活动及COUPON券模板对应记录，按候选promotionCode区分。不能将候选数称为普通活动数/进行中活动数或将其用于活动编辑权限判断。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startTime | String | ✅ | 主题周期开始（毫秒时间戳） |
| endTime | String | ✅ | 主题周期结束（毫秒时间戳） |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].promotionId`、`currentThemeId`（当前归属，null=未归属）
- `currentThemeRevision` 为当前归属主题版本；候选行没有 promotionStatus，需要状态时按 promotionId 查正式活动，不按标题或时间猜状态。
- **枚举字段**：`promotionSubCode`；**格式敏感字段**：`lifecycleStart`/`endTime`（毫秒时间戳）

### 调用示例

```json
{"capability":"ops.promotion.theme.eligible-activities","input":{"startTime":"1788192000000","endTime":"1790783999999","pageNum":1,"pageSize":20},"summary":"查询2026年九月主题排期内可纳入的候选活动（Asia/Shanghai，示例起止时刻已确认）"}
```

---
