# 营销域 — 导购业绩（方案 + 明细 + 看板）写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 业绩方案决定订单业绩值的**取值口径**（按实收金额）与**分享/专属导购分成比例**；同一时刻全租户**仅一个方案生效**（启用新方案会自动将当前生效方案置为未生效）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-performance-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-performance-plan.create 创建业绩方案 🟡 · guide-performance-plan.update 更新业绩方案 🟡 · guide-performance-plan.activate 启用业绩方案 🔴 · guide-performance-plan.delete 删除业绩方案 🔴

---

## ✅ 创建业绩方案 — `ops.marketing.guide-performance-plan.create`

- **风险**：🟡 可逆写（新建恒为**未生效**，须 activate 后才参与计算）
- **前置**：分成比例之和必须**精确等于 1**（如 0.4 + 0.6），否则报「分成比例之和必须等于1」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planName | String | ✅ | 方案名称，≤40 字符 |
| valuationRule | Object | ✅ | 取值规则 |
| valuationRule.actualAmount | Boolean | ✅ | 是否按实收金额取值（当前唯一口径，传 true） |
| splitRule | Object | ✅ | 分成规则 |
| splitRule.shareGuideRate | Number | ✅ | 分享导购比例，0..1 **小数形式**（0.4 = 40%） |
| splitRule.exclusiveGuideRate | Number | ✅ | 专属导购比例，0..1 小数形式，与分享比例之和 = 1 |

### 出参（原始数据）

- **关键字段来源**：返回值为新方案 `id`（十进制字符串）→ 后续启用/编辑。

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.create","input":{"planName":"Q4业绩分成方案","valuationRule":{"actualAmount":true},"splitRule":{"shareGuideRate":0.4,"exclusiveGuideRate":0.6}},"summary":"创建四六分成的Q4业绩方案"}
```

---

## ✅ 更新业绩方案 — `ops.marketing.guide-performance-plan.update`

- **风险**：🟡 可逆写
- **前置**：方案存在且**非生效中**（生效中的方案不可编辑，须先启用其他方案切换）；分成比例之和 = 1。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 方案 ID |
| (其余字段) | - | - | 同创建（planName/valuationRule/splitRule） |

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.update","input":{"id":"5500000000000000001","planName":"Q4业绩分成方案","valuationRule":{"actualAmount":true},"splitRule":{"shareGuideRate":0.4,"exclusiveGuideRate":0.6}},"summary":"修改未生效方案的名称与分成比例"}
```

---

## ✅ 启用业绩方案 — `ops.marketing.guide-performance-plan.activate`

- **风险**：🔴 全局即时生效——事务内先把当前生效方案置为未生效，再将目标方案启用；此后所有订单业绩按新方案口径计算。
- **前置**：方案存在；对已生效方案重复调用幂等成功（无副作用）。 **硬门禁：全局互斥即时生效（原生效方案自动停用），提交前必须复述「方案名+分成比例+原方案将停用」取得确认——指令参数齐全不豁免。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 方案 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.activate","input":{"id":"5500000000000000001"},"summary":"启用Q4业绩分成方案（原生效方案自动停用）"}
```

---

## ✅ 删除业绩方案 — `ops.marketing.guide-performance-plan.delete`

- **风险**：🔴 不可逆
- **前置**：方案**非生效中**（生效中不可删）；系统**至少保留一个方案**（仅剩一个时报「至少保留一个方案」）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 方案 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-performance-plan.delete","input":{"id":"5500000000000000001"},"summary":"删除废弃的未生效业绩方案"}
```

---
