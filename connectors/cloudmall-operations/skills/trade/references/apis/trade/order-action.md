# 交易域 — 订单写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-fulfillment.md`
> **先读现值**：全部写入先读 `order-detail.md` 的 detail（现态、商品行、quantityStats、已有包裹、收货字段）；批量发货与 Excel 导入见 `order-ship-batch-action.md`，导出任务取消见 `order-export-action.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 order.ship 🔴 · order.batch-full-ship 🔴 · order.modify-ship 🔴 · order.remark 🟡 · order.receiver-address.update 🔴 · order.confirm-pickup 🔴 · order.complete 🔴 · order.pickup-verify.confirm 🔴 · order.mark.set 🟡 · order.mark.clear 🟡 · order.period-buy.unsubscribe 🔴

---

## 发货对象规则（ship / modify-ship / batch-ship 共用）

`packages[].items[]` 是商品行与数量的绑定。`bizItemId` 取详情 `items[].id`，不是 `skuId` 或 `spuId`。DTO 接受至少一个标识，Agent 统一只用 `bizItemId`；`orderLineNo` 仅新增发货实现会解析，修改发货不能依赖它。不要把详情整个对象原样提交。

| 嵌套字段 | 类型 | 必填/默认/限制与来源 |
|---|---|---|
| packages / newPackages | 对象数组 | 非空；分别表示本次新增 / 修改后的全部包裹 |
| 每包裹.items | 对象数组 | 非空；同一商品跨包裹数量求和后校验 |
| 每商品.bizItemId | 十进制字符串 | Agent 必传；取 detail.items[].id |
| 每商品.orderLineNo | 字符串 | 新增发货兼容标识；Agent 不传；修改发货仅有此字段会失败 |
| 每商品.quantity | 整数 | 必填且 ≥1；新增合计不得超过 detail.items[].quantityStats.shippableQuantity |
| 每包裹.expressCompanyCode | 字符串 | 普通新增、所有修改必传非空；来自用户确认的承运商编码，不能用名称代替；**各租户编码不统一（如测试租户为 `SF`/`YT`/`ZTO`，其他租户可能为小写 `shunfeng` 等），大小写敏感**，一律取 `ops.logistics.express-company.enabled-list` 返回的原值，不凭常识猜测大小写 |
| 每包裹.trackingNumber | 字符串 | 普通新增、所有修改必传非空；同次运单号不得重复；前端 6~50 位字母数字是表单规则，DTO 未声明此正则 |
| 每包裹.deliveryMethod | 字符串 | 仅新增支持；省略为 express；可用 express/city_express/rider_delivery/self_service，大小写敏感 |
| 每包裹.deliveryPerson | 字符串 | self_service 新增必须取得真实配送人；普通新增及修改不传 |
| 每包裹.deliveryPhone | 字符串 | self_service 新增必须取得真实联系电话；普通新增及修改不传 |

门店自配新增不传承运商/运单号，系统生成内部运单。修改发货实现没有自配分支，会忽略配送人字段，故自配修改不能使用本能力。Java `PackageShipItem` 只对 items 声明必填；表中条件字段是执行纪律及下游履约需要，不能误读为都由 DTO 注解保证。来源：`MultiPackageShipRequest`、`PackageShipItem`、`PackageGoodsItem`、`ModifyShipRequest`；运行时 `OrderServiceImpl.ship/handleAdjustPackage`；运营端 `ShipModal`、`ModifyShipModal`。

所有写入先读详情，`dataSource=MIGRATED` 禁止操作。购买主单与履约子单不得混用：存在 `subOrders` 时先定位实际履约对象再读取其详情；不能直接给购买单发货。数量缺失、返回脱敏地址不能复用、物流状态读取失败时，先补齐事实，不能按 0 或空字符串猜测。写调用报错或超时后先回读详情及物流，不自动重发。

---

## ✅ 订单发货 — ops.trade.order.ship

用途：为待发货或部分发货订单新增本次发出的包裹（🔴）。已有包裹不重复提交；调整已有运单应使用 modify-ship。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；详情确认的实际履约订单 |
| packages | 对象数组 | 必填且非空；全部叶子字段见上方“发货对象规则” |

前置 `PENDING_SHIPMENT/PARTIAL_SHIPPED`，非迁移且允许履约。按 detail.items[].quantityStats.shippableQuantity 安排本次数量；禁止 EXCHANGE_IN 行。普通配送与 self_service 分支见对象规则。返回业务数据为空（`OrderController.ship`）；成功后 detail + logistics，核对新增包裹、商品行数量及 `PARTIAL_SHIPPED/SHIPPED`。部分发货保持部分状态是正常结果；异步延迟先报告待核实，不因状态未变再次写入。

```json
{
  "capability": "ops.trade.order.ship",
  "input": {
    "orderNo": "SO20260905000001",
    "packages": [
      {
        "expressCompanyCode": "shunfeng",
        "trackingNumber": "SF1234567890",
        "items": [
          { "bizItemId": "2000000000000000001", "quantity": 1 }
        ]
      }
    ]
  },
  "summary": "发货"
}
```

---

## ✅ 批量整单发货 — ops.trade.order.batch-full-ship

用途：为至多 50 个整单分别登记承运商和运单号（🔴）。`orders` 不能为空且最多 50 项，每项都必须给 `orderNo`、`expressCompanyCode`、`trackingNumber`；不能把多包裹订单塞入本能力。先逐单确认，返回后逐单报告成功/失败。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orders | 对象数组 | 必填；1~50 项，一项代表该单剩余可发商品集中为一个包裹 |
| orders[].orderNo | 字符串 | 必填非空；逐单先读取详情；同一单仅一项 |
| orders[].expressCompanyCode | 字符串 | 必填非空；承运商编码 |
| orders[].trackingNumber | 字符串 | 必填非空；已确认运单 |

来源 `BatchFullShipRequest.FullShipItem`、`ShipImportServiceImpl.batchFullShip`；商品行由执行方计算，禁止添加 items 或自配字段。部分发货单可发剩余数量，并非要求历史上从未发货。返回 `BatchOperationResultVO` 的 `totalCount/successCount/failureCount` 与 `failures[].orderNo/reason`；不能把整体响应成功视为每单成功。逐单回读详情和物流；只对已确认失败、重新核实现态的订单制定重试计划。

```json
{
  "capability": "ops.trade.order.batch-full-ship",
  "input": {
  "orders": [
      {
        "orderNo": "SO20260905000001",
        "expressCompanyCode": "shunfeng",
        "trackingNumber": "SF1234567890"
      }
    ]
  },
  "summary": "批量整单发货"
}
```

---

## ✅ 修改发货方案 — ops.trade.order.modify-ship

用途：替换已发货订单的完整包裹方案（🔴）。`actionType` 固定为 `ADJUST_PACKAGE`，`newPackages` 非空且按发货对象规则填写；这是全量替换，不是添加一个包裹。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；实际履约订单 |
| actionType | 字符串 | 必填，唯一 ADJUST_PACKAGE |
| newPackages | 对象数组 | 必填非空；所有保留及新增包裹；每包裹必传承运商、运单和非空 items，每项必传 bizItemId、quantity；见对象规则 |

前置 `SHIPPED/PARTIAL_SHIPPED` 且没有 `SIGNED` 运单。每商品修改后总数量 ≥ 已发总数，增量 ≤ 当前可发数量。先用 detail.packages 的分配与 logistics 的承运商合成完整方案；不得漏掉未改包裹。`orderLineNo` 不能替代 bizItemId，门店自配不适用。来源 `OrderServiceImpl.handleAdjustPackage`，运营端 `ModifyShipModal` 只构造承运商、运单、商品 id/数量。返回业务数据为空；回读全部运单及商品分配，部分发货全部发完可推进 SHIPPED。

```json
{
  "capability": "ops.trade.order.modify-ship",
  "input": {
    "orderNo": "SO20260905000001",
  "actionType": "ADJUST_PACKAGE",
  "newPackages": [{ "expressCompanyCode": "shunfeng", "trackingNumber": "SF1234567891", "items": [{ "bizItemId": "2000000000000000001", "quantity": 1 }] }]
  },
  "summary": "修改物流"
}
```

---

## ✅ 订单备注覆盖 — ops.trade.order.remark

用途：设置订单运营备注（🟡）。`remark` 是覆盖式单值字段，必须是非 null 文本且不超过 200 字符；先读取原备注，避免无意覆盖；不得写入猜测性结论或敏感信息。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；已确认订单 |
| remark | 字符串 | 必填非 null，最长200；空字符串表示清空，仅明确要求清空时使用 |

来源 `UpdateRemarkRequest` 的 NotNull/Size 与 `OrderServiceImpl.updateRemark`。没有新增一条备注的语义。返回业务数据为空，回读 detail.remark 必须等于提交文本；保存失败先保留原备注，不自动拼接追加。

```json
{
  "capability": "ops.trade.order.remark",
  "input": {
    "orderNo": "SO20260905000001",
    "remark": "已与客户确认周五送达"
  },
  "summary": "添加订单备注"
}
```

---

## ✅ 修改收货地址 — ops.trade.order.receiver-address.update

用途：更正快递订单的完整收货信息（🔴）。运行时逐字段覆盖，省市区遗漏会被置空，旧地址不会自动保留。完整复述新地址并确认后提交。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；PENDING_SHIPMENT 且 deliveryMethod=express |
| receiverName / receiverPhone / receiverDetailAddress | 字符串 | 运行时要求非 null，未校验非空；Agent 必须取得有效完整值，禁止空文本及脱敏号码 |
| receiverProvince / receiverCity / receiverDistrict | 字符串 | Java 可选但遗漏会清空；Agent 必须从旧详情完整保留或取得用户确认的新值，不能仅改一项省略其余 |
| longitude / latitude | 数字 | 可选；两者同时有值才进行坐标范围校验；新地址不能沿用旧坐标 |
| addressId | 十进制字符串 | 共用 DTO 的会员地址模式在本运营实现不读取；禁止用此字段代替完整地址 |

来源 `UpdateReceiverAddressRequest`、`OrderServiceImpl.updateReceiverAddress` 的逐项覆盖和 `EditAddressModal` 构造。缺坐标时尝试地址定位；定位失败可能跳过范围校验，所以“修改成功”不能表述为“配送范围已验证”。业务数据为空；回读全部收货字段和地址变更记录，核对省市区未丢失。不可据输入缺失推断用户想清空地址。

```json
{
  "capability": "ops.trade.order.receiver-address.update",
  "input": {
    "orderNo": "SO20260905000001",
    "receiverName": "张三",
  "receiverPhone": "13800138000",
  "receiverProvince": "浙江省",
  "receiverCity": "杭州市",
  "receiverDistrict": "西湖区",
  "receiverDetailAddress": "文三路 100 号"
  },
  "summary": "修改收货地址"
}
```

---

## ✅ 确认备货 — ops.trade.order.confirm-pickup

用途：把待发货自提订单推进为已备货待客户取货（🔴）。仅输入 `orderNo`；先确认订单是自提履约，不得把配送订单误转为自提。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；PENDING_SHIPMENT 且 SELF_PICKUP；确认实际备货完成 |

来源 `OrderServiceImpl.confirmPickup`。返回业务数据为空；回读 detail.orderStatus=PENDING_PICKUP。备货成功不代表客户已经领取，后续实际交付使用核销预览及确认。

```json
{
  "capability": "ops.trade.order.confirm-pickup",
  "input": {
    "orderNo": "SO20260905000001"
  },
  "summary": "确认备货完成"
}
```

---

## ✅ 人工完成订单 — ops.trade.order.complete

用途：在已签收且没有进行中售后的前提下人工完成订单（🔴）。仅输入 `orderNo`；它不能替代物流签收，也不能用于规避售后。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；RECEIVED，且无进行中售后；确认人工完成意图 |

来源 `TimeoutActionService.manualCompleteOrder`；完成会触发订单完成后的积分处理，不能承诺积分即时到账。返回业务数据为空；回读 detail.orderStatus=COMPLETED。状态或售后条件不满足时停止，不能先关闭售后以绕过校验。

```json
{
  "capability": "ops.trade.order.complete",
  "input": {
    "orderNo": "SO20260905000001"
  },
  "summary": "人工完成订单"
}
```

---

## ✅ 自提核销确认 — ops.trade.order.pickup-verify.confirm

用途：确认客户已实际取走自提商品并留下核销记录（🔴）。`pickupCode` 必须为六位数字，且必须与本轮刚刚预览到的同一订单一致。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| pickupCode | 字符串 | 必填；\d{6}；必须与预览相同 |
| orderNo | 字符串 | DTO 可选；Agent 传预览返回 orderNo 固定目标 |
| verifyChannel | 字符串 | 不传；运营执行固定渠道 |

来源 `PickupVerifyRequest`、`PickupVerifyServiceImpl.confirm`。先预览且确认实际交付。返回 `PickupVerifyResultVO` 的 `orderNo/success/verifyTime/message`；必须检查 success 并核对订单号，再 detail 确认签收状态。预览失效、码不匹配或调用结果未知时先回读，不盲目重复核销。

```json
{
  "capability": "ops.trade.order.pickup-verify.confirm",
  "input": {
    "pickupCode": "123456",
    "orderNo": "SO20260905000001"
  },
  "summary": "确认自提核销"
}
```

---

## ✅ 批量设置标记 — ops.trade.order.mark.set

用途：批量给订单设置颜色标记（🟡）。覆盖既有标记（同单重复标记为替换语义）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNos | 字符串数组 | 是，非空 | 订单号列表 |
| color | 字符串 | 是 | `RED` / `YELLOW` / `GREEN` / `BLUE` / `PURPLE` |
| remark | 字符串 | 否，≤200 字符 | 标记备注 |

来源：`OrderMarkRequest`。设置后用 `mark.get` 抽查核对（逐单回读成本高时可抽查首单并向用户报告设置数量）。

```json
{
  "capability": "ops.trade.order.mark.set",
  "input": { "orderNos": ["SO20260905000001"], "color": "RED", "remark": "重点跟进" },
  "summary": "批量标记订单"
}
```

---

## ✅ 批量清除标记 — ops.trade.order.mark.clear

用途：批量清除订单标记（🟡）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNos | 字符串数组 | 是，非空 | 订单号列表 |

来源：`OrderMarkClearRequest`。清除后标记颜色、备注、标记人全部置空；回读 `mark.get` 确认 `color=null`。

```json
{
  "capability": "ops.trade.order.mark.clear",
  "input": { "orderNos": ["SO20260905000001"] },
  "summary": "批量清除订单标记"
}
```

---

## ✅ 周期购退订 — ops.trade.order.period-buy.unsubscribe

用途：退订周期购计划的后续周期（🔴）。**服务端直接创建退款单并以取消原因关闭订单，不创建售后单**，返回退款金额与受影响订单清单。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNo | 字符串 | 是，路径参数，≤64 字符 | 周期购订单号（履约子单） |
| reason | 字符串 | 是，非空且 ≤256 字符 | 退订原因（记录到操作日志） |

结果来源 `PeriodUnsubscribeResult`：`refundAmount`（退款金额，元）、`affectedOrderNos`（受影响的后续周期履约子单号列表）；`afterSaleNo` **恒为 null**（当前实现不创建售后单，不能据此跟进）。

前置：目标必须是周期购履约子单（购买单聚合态 `PERIOD_FULFILLING` 不直接处置，先定位子单）；向用户复述受影响周期范围与退款金额，确认后执行。执行后逐项报告：退款金额、受影响子单；**退款到账用 `ops.trade.payment.refund.search` 按关联支付单跟进退款单状态**，不走售后流程。

```json
{
  "capability": "ops.trade.order.period-buy.unsubscribe",
  "input": { "orderNo": "SO20260905000001", "reason": "客户要求取消后续周期" },
  "summary": "退订周期购"
}
```
