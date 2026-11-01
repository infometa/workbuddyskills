# 营销域 — 运营流程：CPS 结算明细与商品推广

> 概念知识见 `references/domains/cps-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`cps-settle-query.md` / `cps-settle-action.md`（结算明细/手动结算）、`cps-goods-promotion-query.md` / `cps-goods-promotion-action.md`（商品推广）。

---

## CPS 结算明细

**场景**：查询分销员×活动维度的预估结算汇总；结算数据异常时手动修复。

1. 活动维度：`cps-settle.search`（activityId 必填路径参数；按 cpsUid/cpsType/settleStatus/结算时间筛选）。
2. 全局维度：`cps-settle.global-search`（activityId 可选；activityName/phone/groupName 先反查再过滤，反查无命中返回空页）。
3. 手动结算：`cps-settle.manual-settle`（🔴 资金面运维动作，仅用于结算数据异常修复，**不得作为常规结算入口**；订单不存在时静默成功）——执行后用活动结算明细分页复查。

### 异常处置
- 明细出参 `phone` 为未脱敏明文——展示给用户时自行打码。
- 两套结算状态不可混用：活动侧字符串（'0'/unsettled/settled）vs 明细侧整数（0/1）。
- 订单维度明细后端无端点，订单数据走交易域。

---

## CPS 商品推广

**场景**：管理商品的分销可推广性与查询佣金率范围。

1. 查询：分页 `cps-goods-promotion.search`（spuName/externalSpuId 模糊、commissionType/promotionStatus/品类筛选；默认推广中在前、已停止沉底）；详情 `cps-goods-promotion.detail`（不含佣金率范围，看分页的 commissionRateRange）；选品 `cps-goods-promotion.selector`（供活动奖励范围/活动推广编排选品）。
2. 批量启停：`cps-goods-promotion.toggle-status`（spuIds + status 0 启用/1 禁用）——逐条执行、失败仅记日志无回执，**操作后回查分页确认 promotionStatus**。

### 参数来源

| 参数 | 来源 |
|------|------|
| spuId | 商品推广分页/选择器/商品域查询 |
| categoryCodes | 商品域类目编码（末级，服务端递归展开子孙类目） |

---
