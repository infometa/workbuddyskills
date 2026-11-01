# 营销域 — 导购客户/公共池/绑定关系写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖客户归属列表、客户 360 画像、行为轨迹、归属转移、公共客户池与绑定关系查询/释放。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-customer-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-customer.transfer 客户归属转移 🔴 · guide-public-pool.assign 公共池客户分配 🔴 · guide-relation.release 手动释放绑定关系 🔴

---

## ✅ 客户归属转移 — `ops.marketing.guide-customer.transfer`

- **风险**：🔴 商业影响——**客户归属变更**，执行前向用户复述客户与目标导购
- **前置**：`toGuideId` 必填且不得等于 `fromGuideId`；目标导购应在职。
- **语义**：
  - `fromGuideId` 传值：仅失效该客户与原导购的关系（共享/专属均失效）；
  - `fromGuideId` 省略：**失效该客户全部活跃关系**（可能同时释放共享导购与专属导购）；
  - 新关系保留原有关系类型；客户原本无任何关系时新建专属导购关系；到期时间按绑定设置中的专属导购有效期重新计算。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customerUid | String | ✅ | 客户 UID |
| toGuideId | String | ✅ | 目标导购 ID |
| fromGuideId | String | 否 | 原导购 ID；省略时自动处理该客户全部活跃关系 |
| reason | String | 否 | 转移原因（备注） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| data | 成功恒为 true |

### 调用示例

```json
{"capability":"ops.marketing.guide-customer.transfer","input":{"customerUid":"900000000000000001","fromGuideId":"5100000000000000001","toGuideId":"5100000000000000002","reason":"客户申请更换服务导购"},"summary":"把客户从导购A转移给导购B"}
```

---

## ✅ 公共池客户分配 — `ops.marketing.guide-public-pool.assign`

- **风险**：🔴 商业影响——**客户归属变更**
- **前置**：`poolId` 必须是池中待分配记录（已分配或不存在时报错）。
- **重要口径**：无论 `assignMethod` 取何值，**目标导购一律取 `targetGuideId`**——`assignMethod` 仅作为绑定方式记录在关系上，`nearest_store`/`store_round_robin` 并不会自动选址或轮询。因此 `targetGuideId` 实际必填。
- 分配成功后新建专属导购关系（到期时间按绑定设置计算），公共池记录标记已分配。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| poolId | String | ✅ | 公共池记录 ID |
| assignMethod | String | ✅ | `admin_assign`-运营指定/`nearest_store`-就近门店/`store_round_robin`-门店轮流（仅记录绑定方式） |
| targetGuideId | String | 实际必填 | 目标导购 ID（分配结果的归属导购） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide-public-pool.assign","input":{"poolId":"5300000000000000001","assignMethod":"admin_assign","targetGuideId":"5100000000000000002"},"summary":"将公共池客户分配给指定导购"}
```

---

## ✅ 手动释放绑定关系 — `ops.marketing.guide-relation.release`

- **风险**：🔴 商业影响——**解绑客户归属**，执行前向用户复述导购与客户
- **前置**：建议先经绑定关系查询拿到生效中的关系 ID。
- **语义**：失效该条绑定关系；若客户无其他活跃绑定关系，自动进入公共客户池。幂等——关系不存在或已失效时**静默成功**（不报错）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 绑定关系记录 ID（路径参数） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide-relation.release","input":{"id":"5400000000000000001"},"summary":"手动释放该条导购客户绑定"}
```

---
