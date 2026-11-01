# 营销域 — 运营流程：导购主档/客户归属/等级与绑定设置

> 概念知识见 `references/domains/guide-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`guide-query.md` / `guide-action.md`（主档）、`guide-customer-query.md` / `guide-customer-action.md`（客户/公共池/绑定）、`guide-level-settings-query.md` / `guide-level-settings-action.md`（等级/绑定设置）。

---

## 导购管理

**场景**：导购主档生命周期与业绩统计。

```
新增（guide.create，初始 pending 待激活）→ 导购端小程序激活（运营端无激活端点）
  → 在职（active）── disable（🔴 必须指定客户转移方式）──▶ disabled ── enable ──▶ active
                                              disabled ── archive ──▶ archived（终态，不可恢复）
```

1. 查询：`guide.search`（keyword 姓名手机号模糊；**不传 status 会包含已归档导购**，需排除时显式传）、`guide.stats` 状态计数、`guide.detail`、`guide.customers` 名下生效客户、`guide.operation-logs` 审计。
2. 统计：`guide.month-stats`（本月，customerCount=本月新增）、`guide.performance`（历史全量，customerCount=总数）、`guide.sales-trend`（近 5 天逐日）。
3. 编辑 `guide.update`（🟡 普通编辑 / 🔴 调店）：**storeId 与现值不同即触发调店**——只在用户明确要求调店时才传 storeId；调店策略 stay=客户全部解绑入公共池、follow/individual=客户跟随留在新店。
4. 停用 `guide.disable`：transferMethod 三选一（admin_assign 需 targetGuideId / public_pool / store_round_robin）；仅 active 可停用。
5. 归档 `guide.archive`：🔴 终态无恢复端点；仅 disabled 可归档，先停用并处理好客户归属。

---

## 导购客户与公共池

**场景**：客户归属查询/转移、公共池分配、绑定关系管理。

1. 已归属客户 `guide-customer.search`（全租户生效中关系；phone 精确反查）；客户 360 `guide-customer.profile`（uid）；行为轨迹 `guide-customer.behavior-tracks`（isHighIntent 为客户级高意向标记）。
2. **归属转移** `guide-customer.transfer`（🔴）：fromGuideId 传值=仅失效与原导购关系；**省略=失效该客户全部活跃关系**；新关系保留原类型，无关系时新建专属导购关系。
3. 公共池 `guide-public-pool.search`（只返回待分配记录）→ 分配 `guide-public-pool.assign`（🔴）：**无论 assignMethod 取何值，目标导购一律取 targetGuideId**（assignMethod 仅记录绑定方式）。
4. 绑定关系审计 `guide-relation.search`（含已失效，isActive 过滤）→ 手动释放 `guide-relation.release`（🔴 幂等：关系不存在或已失效时静默成功；客户无其他活跃关系时自动入公共池）。

### 参数来源

| 参数 | 来源 |
|------|------|
| relationId | 已归属客户列表 / 绑定关系查询 |
| poolId | 公共池列表的 `id` |
| customerUid / uid | 会员域用户 UID（用户提供或查询结果） |

---

## 导购等级与绑定设置

**场景**：导购等级维护（≤6 个）与全租户绑定行为配置。

1. 等级：`guide-level.list`（等级功能关闭时返回空数组）→ `guide-level.create`（创建即启用）/ `update`（levelName/levelSort 仍必填）/ `delete`（🔴 前置：guideCount=0）。
2. 等级全局配置：`guide-level.get-config` → `update-config`（三个字段可选、非空才更新；关闭 enabled 后等级列表立即返回空）。
3. **绑定设置**：`guide-bind-settings.get` → `guide-bind-settings.update`（🔴 全量覆盖——**先查询现设置、修改后整包提交**，漏传区域会被清空且部分链路按"不限制"处理，可能意外放开限制；specifiedUserTagNames 为富化字段，提交时无需回传）。

---
