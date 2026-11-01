# 会员域 — 积分兑换订单写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；订单检索与现值读取（分页/详情）先读 `points-exchange-order-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.points-exchange-order.ship 兑换订单发货

---

## ✅ 兑换订单发货 — ops.member.points-exchange-order.ship

- 仅**待发货（status=1）**可发货，发货后不可撤销；物流单号必须由用户提供，禁止编造

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 订单 ID |
| logisticsNo | String | ✅ | 物流单号 |
| logisticsCompany | String | — | 物流公司名称（建议提供） |

### 出参（原始返回）

`data` 为 `null`；非待发货状态返回业务错误。回读 `points-exchange-order.detail` 核验（status=2 + 物流信息）。

### 调用示例

```json
{"capability":"ops.member.points-exchange-order.ship","input":{"id":"1200012345678901234","logisticsCompany":"顺丰速运","logisticsNo":"SF1234567890123"},"summary":"为兑换订单发货"}
```
