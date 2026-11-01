# 交易域 — 批量发货与物流导入契约（写操作）

> 运营流程：`references/flows/trade-fulfillment.md`；概念知识：`references/domains/trade-concepts.md`
> **先读现值**：逐单发货前用 `order-detail.md` 的 order.detail 核实现态与商品行；异步任务结果查询用 `order-ship-batch-query.md` 的 import-multi-package-ship.task；单包裹发货对象规则见 `order-action.md` 的“发货对象规则”。
> 全部为履约高风险操作（🔴）：批量改变多个订单的发货事实，必须逐单核实后执行。所有 ID 为十进制字符串。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 order.batch-ship 🔴 · order.merge-ship 🔴 · order.delivery-plan.update 🔴 · order.import-ship 🔴 · order.import-multi-package-ship 🔴 · order.import-modify-logistics 🔴

---

## ✅ 批量多包裹发货 — ops.trade.order.batch-ship

用途：批量多包裹发货（🔴）。与 `batch-full-ship` 的区别：本能力逐包裹逐商品行指定发货内容（一单多包裹、多运单）；`batch-full-ship` 是后端自动计算整单发货。需要精确控制包裹内容时用本能力。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orders | 对象数组 | 是，非空，≤50 单 | 订单发货详情列表 |

| orders[] 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| orderNo | 字符串 | 是 | 订单号 |
| packages | 对象数组 | 是，非空 | 该单包裹列表（结构同 ship 能力的 packages） |

`packages[]` 含 `expressCompanyCode` / `trackingNumber`（非门店自配必填）、`items[]`（`bizItemId` + `quantity`，来自订单详情商品行）以及门店自配分支字段（`deliveryMethod=self_service` 时的 `deliveryPerson` / `deliveryPhone`）。来源：`BatchMultiPackageShipRequest`（≤50 单）。

结果来源 `BatchOperationResultVO`：`totalCount` / `successCount` / `failureCount` 与 `failures[]`（逐单失败原因）。**逐单分别报告成功、失败与原因，不把总体受理说成全部成功**；失败单不自动重试。

```json
{
  "capability": "ops.trade.order.batch-ship",
  "input": {
    "orders": [
      {
        "orderNo": "SO20260905000001",
        "packages": [
          { "expressCompanyCode": "shunfeng", "trackingNumber": "SF1234567890", "items": [{ "bizItemId": "2000000000000000001", "quantity": 1 }] }
        ]
      }
    ]
  },
  "summary": "批量多包裹发货"
}
```

---

## ✅ 合并发货 — ops.trade.order.merge-ship

用途：多订单合并发货（🔴）——多个订单的商品合并进同一个包裹，共用同一运单号。仅合并场景使用，系统不校验运单号与订单的一对一关系。

前置（服务端校验）：各订单须**同收货人、同一下单账号、同一发货门店**，订单创建时间在 **3 天窗口内**，且均处**待发货/部分发货**状态。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNos | 字符串数组 | 是，2~3 个订单号 | 待合并订单列表 |
| expressCompanyCode | 字符串 | 是，非空 | 快递公司编码 |
| trackingNumber | 字符串 | 是，非空 | 共用运单号 |

来源：`MergeShipRequest`（`@Size(min=2, max=3)`）。前置：各订单均已核实可发（同收货人/地址）；合并后各订单共享物流记录。结果来源 `BatchOperationResultVO`，逐单报告。

```json
{
  "capability": "ops.trade.order.merge-ship",
  "input": {
    "orderNos": ["SO20260905000001", "SO20260905000002"],
    "expressCompanyCode": "shunfeng",
    "trackingNumber": "SF1234567890"
  },
  "summary": "合并发货"
}
```

---

## ✅ 周期购发货计划更新 — ops.trade.order.delivery-plan.update

用途：更新周期购单期发货计划的预计发货时间（🔴）。运营端仅发货日期 + 操作原因（地址簿是 C 端概念，`addressId` 恒不传）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| orderNo | 字符串 | 是，路径参数，≤64 字符 | 周期购履约子单号 |
| expectedShipTime | 字符串 | 条件必填（与 addressId 至少一项；运营端即本字段） | ISO-8601 OffsetDateTime（如 `2026-09-25T10:00:00+08:00`），不传则不修改 |
| operationReason | 字符串 | 是（运营端必填），≤256 字符 | 操作原因，记录到操作日志 |

来源：`UpdatePeriodDeliveryPlanRequest` 与 `PeriodBuyOrderService.updateDeliveryPlan`。回读订单详情核对发货计划；周期购购买单（`PERIOD_FULFILLING` 聚合态）须先定位具体履约子单。

```json
{
  "capability": "ops.trade.order.delivery-plan.update",
  "input": {
    "orderNo": "SO20260905000001",
    "expectedShipTime": "2026-09-25T10:00:00+08:00",
    "operationReason": "客户要求延后一期发货"
  },
  "summary": "更新周期购发货计划"
}
```

---

## ✅ Excel 导入发货 — ops.trade.order.import-ship

用途：上传 Excel 批量发货（🔴）。系统按 Excel 中的订单号自动补全可发商品明细后逐单发货。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | 文件 | 是 | Excel 文件（列：订单编号/快递公司编码/运单号），≤5MB |

来源：`ShipImportService.importShip`（同步执行）。结果来源 `ShipImportResultVO`：`totalCount` / `successCount` / `failureCount`；`hasFailureDetail=true` 时 `failureDetailUrl` 是失败明细 Excel 的 COS 预签名下载链接（转告用户下载）；`errorMessage` 为任务级失败原因（正常完成为空）。部分失败不阻塞成功行；失败行修正后需重新导入。

```json
{
  "capability": "ops.trade.order.import-ship",
  "input": { "fileType": "excel" },
  "summary": "导入批量发货（文件由用户提供）"
}
```

---

## ✅ Excel 导入多包裹发货 — ops.trade.order.import-multi-package-ship

用途：上传 Excel 导入多包裹发货（🔴）。同一订单可多行（不同运单号=不同包裹），通过 SKU 标识指定包裹内商品。异步执行：返回 `data` 为任务 ID 字符串。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | 文件 | 是 | Excel 文件（列：订单编号/快递公司编码/运单号/SKU ID/商家SKU编码/数量），≤5MB |

提交后立即返回 taskId；用 `ops.trade.order.import-multi-package-ship.task` 轮询结果（结果结构与 import-ship 的 `ShipImportResultVO` 相同）。不重复提交同一文件（无幂等保证）。

```json
{
  "capability": "ops.trade.order.import-multi-package-ship",
  "input": { "fileType": "excel" },
  "summary": "导入多包裹发货（异步）"
}
```

---

## ✅ Excel 导入改物流单号 — ops.trade.order.import-modify-logistics

用途：上传 Excel 批量修改物流单号（🔴）。按订单号替换原承运商/运单号，调用物流中心修改运单信息。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | 文件 | 是 | Excel 文件（列：订单编号/原快递公司/原快递单号/新快递公司/新快递运单号），≤5MB |

状态约束（服务端校验）：未发货/已发货订单可改；已收货/已完成/已关闭不可改。结果 `ShipImportResultVO` 同 import-ship（含失败明细 URL）。

```json
{
  "capability": "ops.trade.order.import-modify-logistics",
  "input": { "fileType": "excel" },
  "summary": "导入批量修改物流单号"
}
```

---

## 导入链路纪律

三条导入链路都是「用户提供真实文件 → Agent 转交 → 报告结果」：Agent 不生成、修改 Excel 内容；文件格式与模板从管理后台获取。发货事实（承运商、运单号、包裹内容）必须来自用户与订单详情核实，导入文件内容由用户负责。所有批量操作逐单报告，不笼统宣称成功。
