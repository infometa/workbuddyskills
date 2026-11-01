# 营销域 — CPS 结算明细写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-settle-flow.md`
> **结算状态（明细维度，整数，与活动维度的字符串结算状态是两套体系）**：`settleStatus` 0=待结算 / 1=已结算；`awardStatus` 0=未发奖 / 1=已发奖。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-settle-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-settle.manual-settle 手动结算（单订单预结算刷新） 🔴

---

## ✅ 手动结算（🔴 资金面运维） — `ops.marketing.cps-settle.manual-settle`

- **风险**：🔴 资金面
- **说明**：对指定活动的单笔订单手动触发预结算刷新（重算该订单的预估结算数据）。属于资金相关运维动作，仅用于结算数据异常时的修复，**不得作为常规结算入口**。
- **行为细节**：订单不存在时静默返回成功（不报错）；存在则重新计算并落库该订单的预估结算结果。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID（16 位数字串，路径参数） |
| orderNo | String | ✅ | 订单号（查询参数） |

### 出参（原始数据）

成功无业务数据（空 data）。结算结果需通过「活动结算明细分页」复查确认。

### 调用示例

```json
{"capability":"ops.marketing.cps-settle.manual-settle","input":{"activityId":"7017890752010234","orderNo":"202609180930123001"},"summary":"手动刷新该订单的预估结算数据"}
```

---
