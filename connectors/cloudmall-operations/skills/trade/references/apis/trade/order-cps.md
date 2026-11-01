# 交易域 — CPS 订单查询契约

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-fulfillment.md`
> CPS（按成交计费推广）订单视图：从推广分佣视角查询订单，含佣金与导购归属信息。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 order-cps.search

---

## ✅ CPS 订单搜索 — ops.trade.order-cps.search

用途：从 CPS 推广分佣视角分页查询订单（🟢）。与 `order.search` 的区别：返回佣金总额、导购/门店/员工归属标记等推广维度字段。收货人信息脱敏敏感面，只用于核对归属，不向用户复述明文。

入参：`OrderPageQuery`（与 `ops.trade.order.search` 完全相同的筛选字段：`pageNum`/`pageSize`、`orderNo`、`status`、时间范围、关键词等，详见 `order-query.md` 的 search 参数表）。**请求是 POST + JSON body。**

结果来源 `PageResult<CpsOrderVO>`，每条关键字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| orderNo / parentOrderNo | 字符串 | 订单号 / 父订单号（后续订单详情定位） |
| uid | ID字符串 | 客户标识 |
| orderStatus / orderStatusDesc | 字符串 | 状态枚举与中文描述 |
| needPayAmount / paidAmount / discountAmount | 金额（元） | 应付 / 实付 / 优惠金额 |
| pointsAmount | 整数 | 积分抵扣 |
| totalCommission | 金额（元） | 佣金总额（CPS 核心指标） |
| selfFlag / staffFlag / storeFlag | 整数 | 自购 / 员工 / 门店归属标记 |
| storeId / storeName / salesGuideName | ID字符串 / 字符串 | 门店与导购归属 |
| settleStatus / settleTime | 整数 / 时间字符串 | 分佣结算状态与结算时间。**CpsSettleStatus（本域）：`1` 未结算 / `2` 结算中 / `3` 结算失败 / `4` 结算成功**。⚠ 营销域结算明细的 settleStatus 是另一套枚举（`0` 待结算 / `1` 已结算），不得混用；以本表解释 CPS 订单的结算状态，`settleStatus=1` 表示未结算 |
| activityId / promotionId | 字符串 | 命中的 CPS 活动 / 促销标识 |
| cpsInfo | 对象 | 推广者信息快照（见下表） |
| commissionInfo[] | 对象数组 | 多级佣金分摊明细（见下表） |
| extData | 对象 | 分佣金额基数快照（见下表） |
| items[] | 对象数组 | 商品行（同订单域商品行结构，另平铺佣金字段：`commissionType` 佣金类型、`commissionRate` 佣金率（四位小数，0.1213=12.13%）、`returnQuantity` 退款数量、`originCommissionAmount` 原始佣金、`actualCommissionAmount` 扣退款后实际佣金） |
| receiverName / receiverPhone / receiverAddress | 字符串 | **脱敏敏感面**：收货人信息，只用于核对归属，不向用户复述明文 |
| createTime / payTime / finishTime | 时间字符串 | `yyyy-MM-dd HH:mm:ss` |

`cpsInfo`（`CpsInfoDTO`）结构：`items[]` 推广员列表（每项含 `cpsType` 类型、`groupId`/`groupName` 分组、`uid`/`name`/`phone` 推广者标识、`level` 等级、`commissionRatio` 佣金比例（四位小数，1.0000=100%）、`status` 0 正常/1 冻结——`phone` 为敏感面不复述）+ 四个布尔标记：`selfOrderFlag` 自推自买、`selfOrderCommissionFlag` 自购参与分佣、`staffOrderCommissionFlag` 员工参与分佣、`internalOrderFlag` 内部分销订单。

`commissionInfo[]`（`CpsCommissionItemDTO`）每项：`cpsType`（分销者类型如 DEFAULT_CPS）、`uid`（分销者 UID）、`actualCommissionAmount`（实付佣金，元）、`originCommissionAmount`（未扣退款前原始佣金，元）——佣金争议核对以本明细为准。

`extData`（`CpsExtDataDTO`）：`paidAmount` 下单时实付快照（**售后退款后不回减**）、`validPaidAmount` 有效实付（已扣完成售后退款，与佣金计算基数公式一致）——解释「为什么佣金比」时用 `validPaidAmount`，不用 `paidAmount`。

来源：`OrderCpsController.page`（`@SensitiveApi` 敏感接口，收货人字段由统一脱敏链路处理）。佣金统计以 `totalCommission` 为准，不按商品行自行估算。

```json
{
  "capability": "ops.trade.order-cps.search",
  "input": { "pageNum": 1, "pageSize": 20 },
  "summary": "查询 CPS 推广订单"
}
```

---

## 边界

CPS 视图是订单的另一个只读投影：不能通过它执行订单写操作（发货/改址等仍走订单契约并先读取订单详情）。收货人联系方式是脱敏敏感数据，仅用于本次授权查询的对象核对。
