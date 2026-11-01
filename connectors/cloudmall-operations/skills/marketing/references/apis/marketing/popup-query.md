# 营销域 — 首页弹窗查询契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/popup-review-flow.md`
> 弹窗带完整审核链（草稿 → 提审 → 审核 → 投放/驳回）；创建/编辑/审核是三种不同角色动作，AI 不得代替用户做审核结论。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：popup.search 弹窗分页查询 · popup.detail 弹窗详情（编辑回显基线） · popup.logs 弹窗操作日志（含驳回原因全文） · popup.status-count 弹窗各状态数量 · popup.conflict 弹窗冲突检测（无副作用只读） · popup.global-strategy 全局弹窗频控策略查询 · popup-stats.global-summary 全租户曝光/点击率汇总 · popup-stats.summary 单弹窗效果汇总（日期/门店筛选） · popup-stats.trend 弹窗效果趋势（DAY/HOUR 粒度） · popup-stats.store 弹窗门店维度统计
> 写操作见 `popup-action.md`。

---

## 弹窗状态机（7 态，取值全大写字符串）

| 状态 | 含义 | 可执行动作 |
|------|------|-----------|
| DRAFT | 草稿 | 编辑、提审、删除 |
| PENDING_REVIEW | 待审核 | 审核（通过/驳回） |
| APPROVED | 待投放（审核通过且开始时间未到） | 下线（等待到点自动转投放中） |
| REJECTED | 已驳回 | 编辑、提审、删除 |
| ACTIVE | 投放中 | 暂停、下线（不可删除、不可编辑） |
| PAUSED | 已暂停 | 恢复、下线 |
| ENDED | 已结束（终态） | 删除 |

流转规则（服务端强校验，违反报业务错误）：
- 创建后恒为 DRAFT（无论是否草稿模式）；
- 编辑仅限 DRAFT / REJECTED；
- 提审仅限 DRAFT / REJECTED，且服务端校验完整性（名称/模板类型/开始时间/优先级/投放规则四要素齐全，开始时间无需未来但创建非草稿时必须未来）；
- 审核仅限 PENDING_REVIEW：APPROVE / EDIT_APPROVE 通过后——开始时间已过 → 直接 ACTIVE，未到 → APPROVED（待投放，到点自动上线）；REJECT → REJECTED；
- 暂停仅限 ACTIVE；恢复仅限 PAUSED 且投放结束时间未过期；下线限 ACTIVE / PAUSED / APPROVED → ENDED；
- 删除：投放中（ACTIVE）不可删，需先下线；
- 批量下线/删除为逐条执行、失败跳过（部分成功，无逐项回执），执行后应回读列表核验。

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 弹窗统计导出（Excel 文件流） | 服务端导出实现仍为 TODO（返回空文件），不可用 |
| 选项类接口（优惠券/活动页/标签/门店选项） | 前端 mock 或复用其它域既有接口，无独立运营端点 |

---

## ✅ 弹窗分页查询 — `ops.marketing.popup.search`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| status | String | 否 | 状态筛选（7 态之一，全大写；不传=全部） |
| name | String | 否 | 弹窗名称模糊搜索，≤50 字 |
| templateType | String | 否 | 模板类型：CENTER_IMAGE/FULLSCREEN/CAROUSEL/CAROUSEL_FULLSCREEN/VIDEO/COUPON |
| updatedBy | String | 否 | 最后更新人，≤64 字 |
| startTimeBegin | String | 否 | 投放开始时间下界（yyyy-MM-dd HH:mm:ss） |
| startTimeEnd | String | 否 | 投放开始时间上界（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 详情/编辑/提审/审核/暂停/恢复/下线/删除/日志/统计各能力的弹窗 ID）
- **枚举字段**：`status`（见上方状态机）、`templateType`
- **格式敏感字段**：`startTime`/`endTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `impressionCount`（总曝光）/`clickRate`（点击率，百分数如 12.34 表示 12.34%，不要再乘 100）

### 调用示例

```json
{"capability":"ops.marketing.popup.search","input":{"pageNum":1,"pageSize":20,"status":"PENDING_REVIEW","name":"会员日"},"summary":"查看待审核的弹窗列表"}
```

---

## ✅ 弹窗详情 — `ops.marketing.popup.detail`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID（十进制字符串；本文各能力的 id 均为此义） |

### 出参（原始数据）

- **关键字段来源**：`id`（→ 全部状态操作）、`status`/`checkReason`（驳回原因，编辑前必读）、`templateConfig`/`ruleConfig`（编辑回显基线，保留未改动字段）
- **枚举字段**：`status`（状态机）、`templateType`、`endOfOperation`（MANUAL 手动下线 / AUTO_EXPIRED 自动过期）
- **格式敏感字段**：`startTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`priority`（1..100 整数）
- `ruleConfig.store` / `ruleConfig.audience` 为富化结构（含门店名/标签名），编辑提交时请用详情回显的原始值。

### 调用示例

```json
{"capability":"ops.marketing.popup.detail","input":{"id":"5100000000000000001"},"summary":"读取弹窗详情用于编辑回显"}
```

---

## ✅ 弹窗操作日志 — `ops.marketing.popup.logs`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **枚举字段**：`records[].operationType`（CREATE/EDIT/SUBMIT/APPROVE/EDIT_APPROVE/REJECT/ONLINE/PAUSE/RESUME/OFFLINE/DELETE）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）
- `detail` 为操作说明（驳回记录含驳回原因全文）。

### 调用示例

```json
{"capability":"ops.marketing.popup.logs","input":{"id":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"查看弹窗的审核与操作记录"}
```

---

## ✅ 状态计数 — `ops.marketing.popup.status-count`

- **说明**：当前租户各状态弹窗数量，用于列表 Tab 计数；无入参。

### 出参（原始数据）

- 数组，每项 `{status, statusDesc, count}`；status 见状态机。

### 调用示例

```json
{"capability":"ops.marketing.popup.status-count","input":{},"summary":"查看各状态弹窗数量"}
```

---

## ✅ 冲突检测 — `ops.marketing.popup.conflict`

- **说明**：只读无副作用，允许瞬态单次重试。检测指定弹窗与同投放页面/门店/时间段的其它弹窗的冲突。提审后建议执行一次并向用户转述冲突项。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 出参（原始数据）

- `hasConflict`（布尔）；`conflictItems[]`：每项含 `popupId`/`popupName`/`priority`（冲突弹窗信息）、`overlapPages[]`/`overlapStores[]`（重叠页面/门店）、`overlapTimeRange`（重叠时间段描述）。

### 调用示例

```json
{"capability":"ops.marketing.popup.conflict","input":{"id":"5100000000000000001"},"summary":"检测该弹窗与其它在投弹窗的冲突"}
```

---

## ✅ 全局弹窗策略查询 — `ops.marketing.popup.global-strategy`

- **说明**：当前租户的全局弹窗频控策略；无入参。

### 出参（原始数据）

- **枚举字段**：`sameWeightSort`（CREATED_DESC 创建时间倒序 / CREATED_ASC 创建时间正序 / RANDOM 随机）
- `maxPopupsPerVisit`（单次访问最多弹出数）/`maxPopupsPerDay`（每日最多弹出数）/`intervalSeconds`（两次弹窗最小间隔秒数）。

### 调用示例

```json
{"capability":"ops.marketing.popup.global-strategy","input":{},"summary":"查看全局弹窗频控策略"}
```

---

## ✅ 全局曝光汇总 — `ops.marketing.popup-stats.global-summary`

- **说明**：当前租户整体汇总（列表页统计卡片）；无入参。

### 出参（原始数据）

- 当前实现仅稳定聚合 `impressionCount`/`clickCount`/`clickRate`（百分数，不要再乘 100），其余字段可能为空，不要向用户声称有值。

### 调用示例

```json
{"capability":"ops.marketing.popup-stats.global-summary","input":{},"summary":"查看弹窗总曝光与平均点击率"}
```

---

## ✅ 单弹窗效果汇总 — `ops.marketing.popup-stats.summary`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |
| startDate | String | 否 | 统计起始日（yyyy-MM-dd） |
| endDate | String | 否 | 统计截止日（yyyy-MM-dd） |
| storeId | String | 否 | 门店 ID（只看单店） |

### 出参（原始数据）

- **格式敏感字段**：`avgReadDuration`（平均阅读时长，单位秒）、`clickRate`/`closeRate`（百分数，服务端已 ×100）
- `impressionCount`/`impressionUv`/`clickCount`/`clickUv`/`closeCount`/`couponClaimCount`/`orderCount`/`orderGmv` 为计数/金额；`conversionRate` 当前实现未赋值，不要引用。
- 多日查询时 `impressionUv`/`clickUv` 为每日 UV 相加，不是跨日去重人数。

### 调用示例

```json
{"capability":"ops.marketing.popup-stats.summary","input":{"id":"5100000000000000001","startDate":"2026-09-01","endDate":"2026-09-07"},"summary":"查看该弹窗近一周的效果汇总"}
```

---

## ✅ 效果趋势 — `ops.marketing.popup-stats.trend`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |
| startDate | String | 否 | yyyy-MM-dd |
| endDate | String | 否 | yyyy-MM-dd |
| granularity | String | 否 | DAY（默认）/ HOUR；HOUR 且日期跨度超过 7 天时服务端把截止日截到开始日+7 天 |

### 出参（List，原始数据）

- **枚举字段**：`granularity`（DAY/HOUR）
- **格式敏感字段**：`statsDate`（yyyy-MM-dd，DAY 粒度）、`statsHour`（0-23，HOUR 粒度）
- 每点含 `impressionCount`/`impressionUv`/`clickCount`/`closeCount`/`clickRate`（百分数）/`couponClaimCount`/`orderCount`/`orderGmv`。`timePoint` 字段当前实现未赋值，请用 `statsDate`/`statsHour` 展示。

### 调用示例

```json
{"capability":"ops.marketing.popup-stats.trend","input":{"id":"5100000000000000001","startDate":"2026-09-01","endDate":"2026-09-07","granularity":"DAY"},"summary":"查看该弹窗按天的效果趋势"}
```

---

## ✅ 门店维度统计 — `ops.marketing.popup-stats.store`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |
| startDate | String | 否 | yyyy-MM-dd |
| endDate | String | 否 | yyyy-MM-dd |
| pageNum | Integer | 否 | 默认 1，传正整数 |
| pageSize | Integer | 否 | 默认 20，建议 ≤100 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].storeId`
- **格式敏感字段**：`clickRate`（百分数）
- 每行含 `storeName`（门店名富化失败时可能为空）/`impressionCount`/`clickCount`/`closeCount`/`couponClaimCount`/`orderCount`/`orderGmv`。注意：服务端为内存分页，翻页请用正分页值。

### 调用示例

```json
{"capability":"ops.marketing.popup-stats.store","input":{"id":"5100000000000000001","startDate":"2026-09-01","endDate":"2026-09-07","pageNum":1,"pageSize":20},"summary":"查看该弹窗各门店的效果统计"}
```

---
