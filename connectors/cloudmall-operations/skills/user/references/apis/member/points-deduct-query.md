# 会员域 — 积分抵扣查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points.md`；抵扣配置保存（写操作）见 `points-deduct-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。抵扣规则影响下单价格计算，属商业影响写。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.points-deduct.config 积分抵扣配置查询

---

## ✅ 查询积分抵扣配置 — ops.member.points-deduct.config

- 无配置时返回默认值

### 入参

无。

### 出参（原始返回）

配置对象。**关键字段**：`enabled`、`minDeductUnit`（最小抵扣单位，积分）、`exchangeAmount`（兑换金额，元）、`exchangeRate`（积分兑换比率）、`productScope`（ALL/SPECIFIED）、`productIds[]`（商品 ID 列表回显：SPECIFIED 时回填、ALL/无配置时为空数组——与入参兼容字段同名但语义不同，入参侧不落库）、`productList[]`（指定商品清单：id/spuName/spuCode/mainImage/minPrice；⚠️ `status` 字段存在但恒 null）、max/min 抵扣开关+数值、`amountRatioEnabled`/`amountRatioPercent`（1~100）。

### 调用示例

```json
{"capability":"ops.member.points-deduct.config","input":{},"summary":"查询积分抵扣配置"}
```
