# 营销域 — 互动活动奖品履约与库存写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> 实物奖品发货（发货后 SENDED 终态不可撤销）与奖品库存调整（只能调大）——互动活动的奖品履约子模块；编辑配置见 `interactive-activity-action.md`、运行态见 `interactive-activity-lifecycle-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：发货前必读 `interactive-activity-query.md` 的 `prize-records`（筛 CLAIMED 核对收货资料）；库存调整目标值必须用户给出。
> 能力索引（前缀 `ops.marketing.`）：interactive-activity.ship-prize 实物奖品发货 🔴 · interactive-activity.update-stock 更新奖品库存 🔴

---

## ✅ 实物奖品发货 — `ops.marketing.interactive-activity.ship-prize`

- **风险**：🔴 履约动作（发货后 SENDED 终态，不可撤销）
- **前置**：中奖记录为实物（prizeType=physical）且状态 CLAIMED（用户已填写收货资料）。**发货前必须先查中奖记录核对收货人/地址，运单号必须来自用户提供的真实物流信息，禁止编造。** 仅 WAITING_CLAIM→EXPIRED 之外的 CLAIMED 态可发；非 CLAIMED 报状态错误。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| uniqId | String | ✅ | 中奖记录唯一 ID（来自中奖记录查询） |
| logisticsCompany | String | ✅ | 物流公司名称，≤50 字 |
| trackingNo | String | ✅ | 运单号，≤50 字 |

### 出参

- 无 data（成功即已发货，状态 → SENDED）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.ship-prize","input":{"activityId":"1942000000000000001","uniqId":"1943000000000000001","logisticsCompany":"顺丰速运","trackingNo":"SF1234567890101"},"summary":"按用户提供的运单号发货实物奖品"}
```

---

## ✅ 更新奖品库存 — `ops.marketing.interactive-activity.update-stock`

- **风险**：🔴 商业影响（改变可发放量）
- **前置**：活动已发布（存在 formal）且已配置奖品。**库存只能调大、不能调小**（目标值小于当前总量直接报错）；按 `prizeName`（可加 prizeType 辅助定位）匹配奖品；乐观锁冲突时提示刷新重试。
- **请求体形态**：input 传 `{ activityId, items: [...] }`，服务端收到的是 items 数组（顶层 List）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| items | Array | ✅ | 库存调整项，至少 1 项 |
| items[].prizeName | String | ✅ | 奖品名称（定位 key，须与奖品池配置一致） |
| items[].prizeType | String | 否 | 奖品类型（辅助定位） |
| items[].stock | Integer | ✅ | 新的总量（≥当前值，只能增） |

### 出参

- 无 data（成功即已生效；可回读详情核验 totalAmount/usedStock）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.update-stock","input":{"activityId":"1942000000000000001","items":[{"prizeName":"到店礼-10元券","prizeType":"coupon","stock":800}]},"summary":"把该奖品总量从500提到800"}
```

---
