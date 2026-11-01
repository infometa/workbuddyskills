# 营销域 — CPS 商品推广写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-settle-flow.md`
> **核心枚举**：`commissionType` 佣金类型 0=全局佣金 / 1=定向佣金；`promotionStatus` 推广状态 0=推广中（有效）/ 1=已停止（无效）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-goods-promotion-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-goods-promotion.toggle-status 批量启停商品推广 🟡

---

## ✅ 批量启停推广 — `ops.marketing.cps-goods-promotion.toggle-status`

- **风险**：🟡 影响商品 C 端可推广性（禁用后分销侧不可推）
- **说明**：批量切换商品推广状态（0=启用/推广中，1=禁用/已停止）。逐条执行、单条失败不影响其余（失败仅记日志无回执），操作后应回查分页确认目标状态。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuIds | Array&lt;Long&gt; | ✅ | 商品 SPU ID 列表（十进制字符串），不允许为空 |
| status | Integer | ✅ | 目标状态：0 启用 / 1 禁用 |

### 出参（原始数据）

成功无业务数据（空 data）。结果需通过「推广商品分页」复查 promotionStatus 确认。

### 调用示例

```json
{"capability":"ops.marketing.cps-goods-promotion.toggle-status","input":{"spuIds":["2058365707555589633","2058365707555589634"],"status":1},"summary":"停止这两个商品的分销推广"}
```

---
