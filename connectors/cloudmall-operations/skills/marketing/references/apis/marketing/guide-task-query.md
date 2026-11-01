# 营销域 — 导购推广任务查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 面向运营端创建/下发/跟进导购推广任务（新品推广、活动推广、日常任务）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-task.search 推广任务分页（含执行统计） · guide-task.status-counts 各状态任务计数 · guide-task.detail 推广任务详情（范围富化） · guide-task.executions 任务执行记录分页（催办目标来源）
> 写操作见 `guide-task-action.md`。

---

## 任务状态机（写操作前置判定）

```
draft（草稿）── dispatch / create(isDraft=false) ──▶ active（进行中）── end ──▶ ended（已结束，终态）
```

- `draft`：仅 taskTitle/taskType 必填即可保存；可编辑、可下发。
- `active`：执行记录由系统异步批量生成（按派发范围圈选在职导购）；可编辑、可催办、可结束、可再次下发（再次下发会重新按当前范围生成执行记录）。
- `ended`：终态——不可编辑、不可下发、不可催办；结束后所有 pending/received 执行记录被批量置为 expired。

执行记录状态机：`pending（待接收）→ received（已接收）→ executed（已执行）`；任务结束时 `pending/received → expired（已过期）`。

---

## ⛔ 未开放端点

本控制器全部端点均已开放，无未开放项。

---

## ✅ 推广任务分页 — `ops.marketing.guide-task.search`

- **说明**：按任务类型/状态/标题关键词分页查询，按创建时间倒序；每行带执行统计（已下发数/已执行数/执行率）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| taskType | String | 否 | 任务类型：`new_product`（新品推广）/`activity`（活动推广）/`daily`（日常任务） |
| status | String | 否 | 任务状态：`draft`/`active`/`ended` |
| keyword | String | 否 | 任务标题模糊匹配 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 任务详情/执行列表/下发/催办/结束 的路径 ID）
- **枚举字段**：`status`（见上方状态机）、`taskType`（new_product/activity/daily）、`dispatchTimeType`（unlimited-不限/specified-指定时间段）、`relatedContents[].contentType`（product/promotion/coupon/content/page）
- **格式敏感字段**：`createdTime`/`dispatchStartTime`/`dispatchEndTime`（yyyy-MM-dd HH:mm:ss）、`executionRate`（百分比数值，如 66.7 = 66.7%）

### 调用示例

```json
{"capability":"ops.marketing.guide-task.search","input":{"pageNum":1,"pageSize":20,"taskType":"new_product","status":"draft","keyword":"秋季新品"},"summary":"查询新品推广的草稿任务"}
```

---

## ✅ 各状态任务计数 — `ops.marketing.guide-task.status-counts`

- **说明**：一次查询返回各状态任务数量，用于列表页 Tab 徽标，避免多次分页查询。

### 入参

无（空对象）。

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| all | 全部任务数（= active + draft + ended） |
| active | 进行中数量 |
| draft | 草稿数量 |
| ended | 已结束数量 |

### 调用示例

```json
{"capability":"ops.marketing.guide-task.status-counts","input":{},"summary":"查询推广任务各状态数量"}
```

---

## ✅ 推广任务详情 — `ops.marketing.guide-task.detail`

- **说明**：返回任务完整配置；目标人群与派发范围中的 ID 列表已富化为名称（门店名、导购名「导购名（门店名）」、人群标签名），关联内容已富化（商品/优惠券/促销活动/页面/内容素材名称）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |

### 出参（原始数据）

- **关键字段**：`targetCustomer`/`dispatchScope`（范围对象，见下方「范围模型」）、`relatedContent`（关联内容，含富化名称）、`dispatch`（派发配置，见创建接口展开）
- **枚举字段**：`status`（draft/active/ended）、`taskType`、`dispatch.goalBehavior`（share/share_after/share_order）、`dispatch.frequencyType`（once/periodic）、`dispatch.dispatchTimeType`（unlimited/specified）
- **格式敏感字段**：`createdTime`/`dispatch.startTime`/`dispatch.endTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.marketing.guide-task.detail","input":{"id":"5100000000000000001"},"summary":"查看推广任务详情"}
```

---

## ✅ 任务执行记录分页 — `ops.marketing.guide-task.executions`

- **说明**：查某任务下每位导购的执行记录（下发后系统异步生成，量大时略有延迟）；按创建时间倒序。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| executionStatus | String | 否 | 执行状态：`pending`（待接收）/`received`（已接收）/`executed`（已执行）/`expired`（已过期） |
| keyword | String | 否 | 导购姓名模糊匹配 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 催办接口的 executionIds 指定催办目标）
- **枚举字段**：`executionStatus`（pending/received/executed/expired）
- **格式敏感字段**：`receivedAt`/`executedAt`/`lastUrgedAt`（yyyy-MM-dd HH:mm:ss，可能为 null）、`urgeCount`（催办次数整数）
- **关键字段**：`goalAchievement.targetValue`/`actualValue`/`achievementRate`（目标达成，achievementRate 为百分比数值）

### 调用示例

```json
{"capability":"ops.marketing.guide-task.executions","input":{"id":"5100000000000000001","pageNum":1,"pageSize":20,"executionStatus":"pending","keyword":"陈"},"summary":"查询任务中待接收的陈姓导购执行记录"}
```

---
