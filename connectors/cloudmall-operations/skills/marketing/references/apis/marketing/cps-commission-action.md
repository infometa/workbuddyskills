# 营销域 — CPS 佣金率写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 佣金率是**小数比例**：`0.1213` 表示 12.13%，取值范围 `[0.0000, 1.0000]`（最大即 100%）——**不是**百分比数字。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-commission-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-commission.set-global-rate 设置全局默认佣金率 🔴🔴 · cps-commission.batch-reset-goods-rate 批量重置商品定向佣金率 🔴 · cps-commission.batch-reset-group-rate 批量重置商品分组佣金率 🔴 · cps-commission.cancel-directed 批量取消定向佣金 🔴 · cps.order.trigger-replay 订单佣金补偿重放（客诉补算） 🔴

---

## ✅ 设置全局佣金率 — `ops.marketing.cps-commission.set-global-rate`

- **风险**：🔴🔴 佣金率变更影响全量结算（未定向、未分组命中的所有商品兜底率随之变化）
- **前置**：`rate` 为小数比例 `[0.0000, 1.0000]`（0.1 = 10%），**禁止 AI 编造数值**——必须用户明确给出目标费率后才能执行；执行前向用户复述「当前值 → 目标值」并确认。
- **后果**：立即生效，影响后续所有分佣计算；也是配置商品×分组佣金的前置条件。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rate | Number | ✅ | 佣金率，小数比例 [0, 1]，如 0.1 表示 10% |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.set-global-rate","input":{"rate":0.1},"summary":"将全局默认佣金率设置为10%"}
```

---

## ✅ 批量重置商品定向佣金率 — `ops.marketing.cps-commission.batch-reset-goods-rate`

- **风险**：🔴 佣金率变更影响对应商品结算（覆盖式：已有定向率的商品会被改为新值）
- **前置**：items 1..500 条；`rate` 为小数比例 `[0, 1]`，数值必须用户给出；SPU 必须存在且已有有效推广关系（无推广关系的商品设置后不参与分佣）。
- **后果**：逐条 upsert（成功条目立即生效）并将商品标记为定向佣金；**部分失败不回滚**——返回失败明细，需按 failItems 逐条处理。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | Array | ✅ | 定向佣金项列表，1..500 条 |
| items[].spuId | String | ✅ | 商品 SPU ID |
| items[].rate | Number | ✅ | 佣金率，小数比例 [0, 1] |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| data | 整体是否成功（存在失败项即为 false） |
| successCount | 成功数量 |
| failCount | 失败数量 |
| failItems | 失败项列表：`spuId` + `reason`（失败原因） |

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.batch-reset-goods-rate","input":{"items":[{"spuId":"2058365707555589633","rate":0.15}]},"summary":"将该商品定向佣金率设置为15%"}
```

---

## ✅ 批量重置商品分组佣金率 — `ops.marketing.cps-commission.batch-reset-group-rate`

- **风险**：🔴 佣金率变更影响对应商品×分组结算（最高优先级命中层）
- **前置**：**必须先设置全局佣金率**，否则报业务错误；`spuIds` 与 `commissionList` 均不允许为空；`rate` 为小数比例 `[0, 1]`，数值必须用户给出。
- **后果**：为每个 `spuId × groupId` 组合 upsert 佣金记录（存在则更新，不存在则插入）。总组合数为 spuIds × commissionList 条数，注意批量规模。
- **两种用法（由 spuIds 区分）**：
  - **商品×分组专属率**：`spuIds` 填具体商品 SPU ID——只影响这些商品对该分组的佣金。
  - **分组默认率（全部商品）**：`spuIds` 固定传 `["0"]`（`"0"` 为全局商品占位，运营端「全局佣金设置→分销员组佣金」即此写法）——设置该分组推广**任意商品**的默认率，对应查询能力 `cps-commission.global-group-rates`。用户说「某分组所有商品/默认佣金 X%」时用此写法，不要逐个枚举商品。
- **groupId 红线**：必须是真实分组 ID（来自 `cps-group.options`），**不得传 `-1`**——`spuIds=["0"]` + `groupId=-1` 等于改写全局默认佣金率（应走 set-global-rate 并按 🔴🔴 确认）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuIds | String[] | ✅ | 商品 SPU ID 列表，不允许为空；传 `["0"]` 表示设置分组默认率（全部商品） |
| commissionList | Array | ✅ | 分组佣金项列表，不允许为空 |
| commissionList[].groupId | String | ✅ | 分组 ID（必填，服务端校验非空；来自 `cps-group.options`） |
| commissionList[].rate | Number | ✅ | 佣金率，小数比例 [0, 1] |

### 出参（原始数据）

- 无业务数据（成功即生效；前置不满足时报业务错误）。执行后用 `cps-commission.goods-group-rates`（商品维度）或 `cps-commission.global-group-rates`（分组默认）回读核验。

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.batch-reset-group-rate","input":{"spuIds":["2058365707555589633"],"commissionList":[{"groupId":"5300000000000000001","rate":0.2}]},"summary":"设置该商品对高佣金分组的专属佣金率20%"}
```

```json
{"capability":"ops.marketing.cps-commission.batch-reset-group-rate","input":{"spuIds":["0"],"commissionList":[{"groupId":"5300000000000000001","rate":0.08}]},"summary":"设置高佣金分组推广全部商品的默认佣金率8%"}
```

---

## ✅ 批量取消定向佣金 — `ops.marketing.cps-commission.cancel-directed`

- **风险**：🔴 佣金回退（商品定向率与该商品全部分组率一并删除，回退全局默认）
- **前置**：`spuIds` 为商品 SPU ID 列表；执行前向用户确认受影响商品清单。
- **后果**：删除每个商品的定向佣金记录与全部分组佣金记录，并将商品佣金类型回退为「全局佣金」；**部分失败不回滚**——按 failItems 逐条处理。对本来就没有定向佣金的商品操作是安全的（幂等，成功计数）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuIds | String[] | ✅ | 商品 SPU ID 列表 |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| data | 整体是否成功（存在失败项即为 false） |
| successCount | 成功数量 |
| failCount | 失败数量 |
| failItems | 失败项列表：`spuId` + `reason`（失败原因） |

### 调用示例

```json
{"capability":"ops.marketing.cps-commission.cancel-directed","input":{"spuIds":["2058365707555589633"]},"summary":"取消该商品的定向佣金，回退全局默认"}
```

---

## ✅ 订单佣金补偿重放 — `ops.marketing.cps.order.trigger-replay`

- **风险**：🔴 资金面补偿写——按订单**当前状态**触发分佣计算/结算确认（幂等补偿语义：已处理完成的订单重放会返回相应结果，不重复入账）
- **说明**：「分销员反馈订单没算佣金」类客诉的**补算入口**。以订单状态机为依据决定执行动作（补算分佣 / 确认结算等），结果以返回 VO 为准；执行前向用户确认订单号。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderNo | String | ✅ | 订单号（query 参数） |
| track | Boolean | 否 | 是否返回执行轨迹明细，默认 false |

### 出参（原始数据）

- **展示字段**：重放结果 VO（`CpsOrderReplayResultVO`）：订单状态、执行动作、是否成功
- ⚠️ 结果务必逐字段向用户解读；执行动作以响应为准，不预设。

### 调用示例

```json
{"capability":"ops.marketing.cps.order.trigger-replay","input":{"orderNo":"SO202609180001","track":false},"summary":"对该订单触发佣金补偿重放"}
```

---
