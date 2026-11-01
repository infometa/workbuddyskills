# 营销域 — 导购推广任务写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 面向运营端创建/下发/跟进导购推广任务（新品推广、活动推广、日常任务）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-task-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-task.create 创建推广任务 🟡 · guide-task.update 更新推广任务 🟡 · guide-task.dispatch 下发推广任务 🔴 · guide-task.urge 催办导购 🟡 · guide-task.end 结束推广任务 🔴

---

## ✅ 创建推广任务 — `ops.marketing.guide-task.create`

- **风险**：🟡 可逆写（草稿）／🔴 商业影响（isDraft=false 直接下发）
- **前置**：`isDraft=true` 仅 taskTitle/taskType 必填；`isDraft=false` 时 targetCustomer/relatedContent/dispatch 三段必填，且派发结束时间不得早于开始时间，创建后**直接进入 active 并异步生成执行记录**（无需再调下发）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskTitle | String | ✅ | 任务标题，≤100 字 |
| taskType | String | ✅ | new_product/activity/daily |
| remark | String | 否 | 备注，≤500 字 |
| referenceSpeech | String | 否 | 参考话术，≤500 字 |
| targetCustomer | Object | isDraft=false ✅ | 目标人群范围（见「范围模型」） |
| relatedContent | Object | isDraft=false ✅ | 关联内容（见下方展开） |
| dispatch | Object | isDraft=false ✅ | 派发配置（见下方展开） |
| isDraft | Boolean | 否 | 默认 false；true=仅存草稿 |

**关联内容（relatedContent）展开**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contentType | String | ✅ | product/promotion/coupon/content/page（任务类型决定可选项：新品→product；活动→promotion/coupon；日常→content/page） |
| businessContent.product.scope | String | 否 | all=全部商品 / specified=指定商品 |
| businessContent.product.goodsList | Array | 否 | specified 时的商品列表，见下方展开 |
| businessContent.coupon/promotion/page/contentMaterial | Object | 否 | 各为 `{scope: all\|specified, ids: String[]}`，ids 为对应业务对象 ID 列表 |

**goodsList 商品引用展开**（注意：SKU 引用字段是 `skuList[].skuId`，**不是** skuIds）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | 商品 SPU ID |
| skuList[].skuId | String | 否 | 指定 SKU 时传；SPU 级选择不传 skuList（后端自动圈全部 SKU） |

**dispatch 派发配置展开**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scope | Object | ✅ | 执行范围（guide 指定导购 > store 指定门店 > 全部在职导购，优先级依次兜底） |
| goalBehavior | String | 否 | 目标行为：share/share_after/share_order |
| goalQuantity | Integer | 否 | 目标数量 |
| goalUnit | String | 否 | 目标单位 |
| frequencyType | String | 否 | once（单次）/periodic（周期） |
| periodicConfig | Object | 否 | frequencyType=periodic 时传：`frequency`（daily/weekly/monthly）、`dayOfWeek`（weekly 用 1..7）、`dayOfMonth`（monthly 用 1..31）、`timeOfDay`（HH:mm） |
| dispatchTimeType | String | ✅ | unlimited（不限时间）/specified（指定时间段） |
| startTime / endTime | String | 否 | specified 时传，yyyy-MM-dd HH:mm:ss；endTime 不得早于 startTime |

**范围模型（targetCustomer / dispatch.scope 通用）**：

| 字段 | 说明 |
|------|------|
| userTag | 人群标签范围 `{type: all\|specified, ids: 标签值 ID 列表}` |
| user | 目标用户范围 |
| store | 门店范围（ids 为门店 ID） |
| guide | 导购范围（ids 为导购 ID） |

### 出参（原始数据）

新建任务 ID（String，十进制）。

### 调用示例

```json
{"capability":"ops.marketing.guide-task.create","input":{"taskTitle":"秋季新品推广","taskType":"new_product","remark":"秋装上新季","referenceSpeech":"新品到店，欢迎体验","isDraft":false,"targetCustomer":{"userTag":{"type":"all","ids":[]}},"relatedContent":{"contentType":"product","businessContent":{"product":{"scope":"all"}}},"dispatch":{"scope":{"guide":{"type":"all","ids":[]}},"goalBehavior":"share","goalQuantity":10,"goalUnit":"次","frequencyType":"once","dispatchTimeType":"unlimited"}},"summary":"创建并下发秋季新品推广任务给全部导购"}
```

---

## ✅ 更新推广任务 — `ops.marketing.guide-task.update`

- **风险**：🟡 可逆写
- **前置**：任务状态为 draft 或 active（**已结束不可编辑**）；仅传非空字段做部分更新，嵌套结构整体替换。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |
| taskTitle | String | 否 | ≤100 字 |
| taskType | String | 否 | new_product/activity/daily |
| remark / referenceSpeech | String | 否 | ≤500 字 |
| targetCustomer / relatedContent / dispatch | Object | 否 | 结构与创建接口相同 |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-task.update","input":{"id":"5100000000000000001","taskTitle":"秋季新品推广（修订）","remark":"调整派发备注"},"summary":"修订任务标题与备注"}
```

---

## ✅ 下发推广任务 — `ops.marketing.guide-task.dispatch`

- **风险**：🔴 商业影响（触发向导购批量派发）
- **前置**：任务存在且**未结束**（draft/active 均可下发）；执行记录异步生成，接口返回不代表记录已落库，稍后用执行列表查询确认。active 状态重复下发会按当前派发范围再次生成执行记录（可能产生重复记录），下发前先确认任务当前状态。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |

### 出参（原始数据）

无业务数据（成功即受理）。

### 调用示例

```json
{"capability":"ops.marketing.guide-task.dispatch","input":{"id":"5100000000000000001"},"summary":"下发草稿任务给目标导购"}
```

---

## ✅ 催办导购 — `ops.marketing.guide-task.urge`

- **风险**：🟡 通知类写（更新执行记录催办计数）
- **前置**：任务必须处于 active（进行中）。
- **行为**：指定 executionIds 且 ≤10 条 → 同步催办；未指定或 >10 条 → 异步催办该任务下所有 pending/received 记录。仅 pending/received 状态的记录会被实际催办。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |
| message | String | 否 | 催办消息内容 |
| executionIds | String[] | 否 | 目标执行记录 ID 列表（来自执行列表出参 records[].id）；缺省=催办全部未执行记录 |

### 出参（原始数据）

无业务数据（成功即受理）。

### 调用示例

```json
{"capability":"ops.marketing.guide-task.urge","input":{"id":"5100000000000000001","message":"请尽快完成本周期推广任务"},"summary":"催办该任务下全部未执行导购"}
```

---

## ✅ 结束推广任务 — `ops.marketing.guide-task.end`

- **风险**：🔴 不可逆（终态，不可恢复）
- **前置**：任务存在且未结束；结束后所有 pending/received 执行记录被批量置为 expired，任务不可再编辑/下发/催办。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 任务 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-task.end","input":{"id":"5100000000000000001"},"summary":"结束推广任务"}
```

---
