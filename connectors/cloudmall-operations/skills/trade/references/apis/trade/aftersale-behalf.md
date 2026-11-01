# 交易域 — 售后代客创建契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-aftersale.md`
> **先读现值**：创建前读取订单详情、已有售后与 `aftersale-query.md` 的 reasons-detail（真实原因）、refunded-summary（剩余可退余额）、exchangeable-skus（换货目标规格）；由真实订单行取得 `orderItemId/skuId`，不可使用售后行 ID。
> 所有 ID 均为十进制字符串；金额单位为元，输入使用 JSON 数字（如 `99`、`99.5`），最多保留两位小数；金额加总按十进制定点计算，避免浮点累加误差，不把整数分直接当元。前端金额字符串是其内部表示，不能改变开放能力的输入约定。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 aftersale.create-on-behalf 🔴

---

## ✅ 代客创建售后 — ops.trade.aftersale.create-on-behalf

用途：根据客户明确诉求代为新建售后申请（🔴），返回新的售后单号。创建不等于审核同意或退款到账。先读订单与现存售后、选原因、核对每一商品行及申请数量/金额，再确认提交。订单状态仅允许 `PENDING_SHIPMENT`、`PENDING_PICKUP`、`PENDING_DELIVERY`、`PARTIAL_SHIPPED`、`SHIPPED`、`RECEIVED`、`PENDING_FINAL_PAYMENT`；最后一种只允许仅退款。

| 参数 | 类型 | 必填与含义 |
|---|---|---|
| orderNo | 字符串 | 是，订单详情的订单号 |
| afterSaleType | 字符串 | 是，REFUND_ONLY / RETURN_REFUND / EXCHANGE |
| reasonId | ID字符串 | 是，reasons-detail 中与类型对应的原因 id |
| receiveStatus | 整数 | 是，0未收到或1已收到；不能由发货状态推断 |
| shippedStatus | 整数 | 可选，0未发货或1已发货；用户/订单事实，不是状态跳转命令 |
| returnMethod | 字符串 | 仅自提订单且退货退款/换货适用，按下方配送方式规则显式选择；其他场景省略 |
| refundAmount | 金额 | REFUND_ONLY / RETURN_REFUND 条件必填，≥0，等于各 items.refundAmount 之和；EXCHANGE 必须省略 |
| freightRefundAmount / packagingRefundAmount | 金额 | 可选，默认0且≥0，分别为运费/包装费退款；换货省略，不借此发起退款 |
| applyDescription | 字符串 | 可选，最多500字符，客户申请说明 |
| mediaJson | 字符串 | 可选，凭证数组序列化后的字符串，真实结构见下表 |
| items | 对象数组 | 必填且非空；换货只能1个商品行；完整结构如下 |

| items[] 字段 | 类型 | 必填与来源 |
|---|---|---|
| orderItemId | ID字符串 | 是，原订单商品行 id，绝不能取售后 items.id |
| skuId | ID字符串 | 是，该订单商品行的 skuId，必须与 orderItemId 匹配 |
| quantity | 整数 | 是，≥1且≤该行剩余可售后数量 |
| refundAmount | 金额 | 非换货条件必填且≥0；该行商品退款额，不能含运费/包装费；换货省略 |
| exchangeSkuId | ID字符串 | 换货时明确选定的换入规格；实现兼容省略时同规格，但 Agent 应确认目标并显式给值。非换货省略 |

金额约束来自 `AbstractAfterSaleService.validateAmountsAndQuantities`：商品合计+运费+包装费不得超过订单已支付减已退余额；运费/包装费各受对应剩余金额限制，每行还受已退金额和数量限制。存在进行中售后的同 SKU、历史迁移订单、积分商城订单不可新建；待付尾款仅允许仅退款；主品全退可能要求一并处理关联赠品。换入规格由 `AfterSaleExchangeHelper` 校验商品/价格/库存资格，不能凭名称猜 ID。金额上限用 `refunded-summary` 核对剩余可退余额，不凭印象报价；换货目标规格用 `exchangeable-skus` 核对可换性与库存资格，缺少可靠证据时停止，不编造可用值。

`mediaJson` 的外层类型是字符串，内部是凭证数组，不是自由属性对象。来源：前端 `CreateAfterSaleOnBehalfModal` 只序列化已上传成功的文件；`ModifyAfterSaleDrawer` 和 `ReasonInfoCard` 解析/消费；Java `AfterSaleHelper` 保存、`OrderImageSignHelper` 与 `AppAfterSaleDetailConverter` 解析。

| 凭证元素字段 | 类型与构造纪律 |
|---|---|
| url | 必需字符串，实际已上传凭证地址，不伪造上传结果 |
| name | 可选字符串，创建弹窗保存的文件名 |
| type | 可选字符串；创建弹窗保存 MIME 类型如 image/png，编辑页使用 image，视频消费以 video 判断；保留来源实际值，不混造媒体属性 |
| thumbUrl | 可选字符串，已有视频缩略图地址；没有则省略 |

例如字符串值 `"[{\"url\":\"https://example.com/evidence.png\",\"type\":\"image\"}]"` 只演示编码，不可把示例地址作为真实凭证提交。旧返回兼容纯 URL 字符串数组；Agent 新建时使用上述对象数组。不应把 mediaJson 直接传成数组，也不允许附加任意 Map 属性。

创建后拿返回售后号调用 detail，核对类型、状态、商品数量、金额与凭证；创建结果不确定时先查订单已有售后，避免重复申请，不自动连做审核。

```json
{
  "capability": "ops.trade.aftersale.create-on-behalf",
  "input": {
    "orderNo": "SO20260905000001",
    "afterSaleType": "REFUND_ONLY",
  "reasonId": "7100000000000000001",
  "refundAmount": 99,
  "receiveStatus": 0,
  "items": [{ "orderItemId": "2000000000000000001", "skuId": "9000000000000000001", "quantity": 1, "refundAmount": 99 }]
  },
  "summary": "代客创建售后"
}
```

---

## 配送方式规则（returnMethod / receiveStatus）

`receiveStatus` 只使用 `0`（未收到）或 `1`（已收到）；`shippedStatus` 如使用也只使用 `0` 或 `1`。仅自提订单的退货退款或换货适用 `returnMethod`：`SELF_DELIVERY` 为自行退回自提点，`LOGISTICS` 为物流寄回。该条件成立时，Agent 必须先取得用户选择并显式传值，因为省略或错值会静默采用 `SELF_DELIVERY`；其他场景省略，尤其仅退款不需要退货方式。此为 Agent 构造纪律，不是无条件 Java 必填约束。仅退款不强加退货方式。
