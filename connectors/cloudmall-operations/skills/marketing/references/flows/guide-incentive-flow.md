# 营销域 — 运营流程：导购目标/提成/业绩

> 概念知识见 `references/domains/guide-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`guide-target-plan-query.md` / `guide-target-plan-action.md`、`guide-commission-query.md` / `guide-commission-action.md`、`guide-performance-query.md` / `guide-performance-action.md`。

---

## 导购目标

**场景**：按月度/季度周期给导购设定销售额与客户数目标。

```
创建计划（guide-target-plan.create，仅周期信息；同周期唯一）→ 批量添加目标行（batch-add-targets，空白行；已存在导购自动跳过）
  → 填值：单条（update-target，整体覆盖语义）或 按上期 N%（fill-by-last-period，🔴 覆盖式——全部目标行被重算，无上期数据者置 0）
  → 查询/汇总（targets / store-groups / target-summary）
  → [可选] 清空全部目标值（clear-targets，🔴 目标行保留、值置空）/ 删除计划（delete，🔴 仅未开始，级联删除全部目标行）
```

- 周期选项：`guide-target-plan.periods`（全部计划周期倒序，"上期"参照）。
- **目标值（销售额元/客户数）禁止 AI 编造**，必须用户明确给出；填充百分比同样由用户给出。
- 批量添加中不存在的导购 ID 会被静默跳过——执行后回查 targets 列表核验。

---

## 导购提成

**场景**：提成规则配置与明细结算。

```
查现有规则（guide-commission-rule.search / status-counts）
  → 冲突检测（guide-commission-rule.conflict-check：同优先级= same_priority，仅范围重叠= overlap）
  → 创建（guide-commission-rule.create，建议先 conflict-check；status 可 draft/直接 active）
  → [可选] 更新（update，scopes/items 全量替换——先读详情带上完整数据；已停用规则不可编辑）
  → [可选] 停用（disable，🔴 无重新启用通道，停用即永久退出匹配）/ 删除（delete，🔴 仅草稿可删）
明细：guide-commission-detail.search（按导购/订单号/结算状态/落账时间）→ stats（总额/待结算/已结算）
  → 批量标记结算（guide-commission-detail.batch-settle，🔴🔴 资金面：pending → settled，1..500 条；已结算的静默跳过；执行后回查核验）
```

- 提成比例（commissionRate）为小数比例（0.05=5%），fixed 规则为元金额，阶梯门槛以万元数值录入——均由用户给出。
- 明细由订单完成事件自动落账，不可手工创建/修改金额。

---

## 导购业绩

**场景**：业绩方案管理（全租户互斥生效）与业绩明细查询。

1. 方案：`guide-performance-plan.list` / `active`（无生效方案时 data 为 null，订单不产生导购分成业绩）。
2. 创建 `create`（新建恒为 inactive；**分成比例之和必须精确等于 1**）→ 更新 `update`（仅非生效中可改）→ 启用 `activate`（🔴 全局即时生效，自动停用原生效方案；重复启用幂等）→ 删除 `delete`（🔴 非生效中才可删；系统至少保留一个方案）。
3. 明细：`guide-performance-detail.search`（splitScene 五种分成场景；guideId 同时匹配分享/专属导购）/ `stats`（按订单时间过滤）。

---
