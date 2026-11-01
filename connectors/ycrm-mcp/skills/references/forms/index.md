# 目标表单索引

业务名称、已知别名和对象语义用于辅助路由；实际 `deployId` 必须取自本任务适用的 `ycrm_form_deploy_list`，不能直接提交表中匹配键。表中语义不构成字段清单或能力承诺。

本表是固定业务称呼、别名和 Profile 入口的唯一维护位置；Profile 与示例不另建别名清单。新增固定别名须有可复核的产品资料或稳定的 Tool 返回证据；单次返回中的租户名称只用于当次路由，不直接固化为通用别名。

## 解析与加载

1. 用户称呼和本表别名只形成对象候选；根据当前任务的可信 `ycrm_form_deploy_list` 结果，结合可见对象的名称、业务差异和上下文唯一确认目标。别名命中不等于对象已确认，也不能据此直接进入写入。
2. “订单、合同、联系人、发票、回款、付款、退货单、入库单、出库单”等泛称先结合上下文消歧：区分销售与采购、协议与合同订单、开票申请与发票信息及采购发票、计划与实际、采购与销售退货、采购/退货/调拨/其他出入库。仍有多个可见候选时展示名称和差异，请用户选择，不默认取第一个对象。无候选、返回不完整或无法唯一确认时停在发现阶段；对象不可见的结论须有完整发现结果支持。
3. 用户称呼未命中索引时仍用真实对象发现结果路由，不创建临时别名或强行套用对象；唯一确认后，若返回的 `deployId` 匹配本表特有 Profile 的提示键，则读取对应 Profile，其余对象使用本表语义与通用操作规则。新增所需模板歧义不阻塞普通查询。
4. 多实体列仅在[通用批量规则](../multi-entity-rules.md)的“未分组材料拟新增主记录，数量或归属边界待判断”路径按目标加载；判断后可以只有一条。批量更新、已分组新增、查询、已明确的单记录操作和单父记录多行子表均不读该列文件。
5. 跟进记录按特有 Profile 理解事件和字段角色，写入能力以当前 Tool 契约及字段证据为准；拜访签到新增/更新命中服务端限制时停止该写入分支。拜访签到的事件边界文件虽存放于 `multi-entity/`，只由其特有 Profile 在查询或解释时按需加载，不属于下表的新增入口。

## 对象表

| 对象键 | deployId 匹配提示 | 业务称呼 | 已知别名 | 语义区别 | 特有 Profile | 多实体入口 |
| --- | --- | --- | --- | --- | --- | --- |
| `customer` | `customer` | 客户 | 客户、企业客户、公司客户 | 客户主体；联系人建档与客户子表需区分。 | [客户特有规则](customer.md) | [分组语义](multi-entity/customer.md)（仅未分组新增） |
| `sale-clue` | `sale_clue` | 线索 | 线索、销售线索 | 潜在客户留资与需求，可能以联系人显示。 | [线索特有规则](sale-clue.md) | [分组语义](multi-entity/sale-clue.md)（仅未分组新增） |
| `sale-order` | `sale_order` | 合同订单 | 合同订单、销售订单、订单 | 销售产品/服务订单，与协议、采购单区分。 | [合同订单特有规则](sale-order.md) | [分组语义](multi-entity/sale-order.md)（仅未分组新增） |
| `keep-record` | `keep_record` | 跟进记录 | 跟进记录、客户跟进、线索跟进 | 独立跟进事件，区分发生时间与下次跟进安排。 | [跟进记录特有规则](keep-record.md) | [分组语义](multi-entity/keep-record.md)（仅未分组新增） |
| `visit-record` | `visit_record` | 拜访签到 | 拜访签到、拜访记录 | 实际拜访签到；当前不支持新增/更新。 | [拜访签到特有规则](visit-record.md) | —（当前无新增入口） |
| `visit-plan` | `visit_plan` | 拜访计划 | 拜访计划 | 拜访安排；签到查询中的关联计划不改变目标。 | — | [分组语义](multi-entity/visit-plan.md)（仅未分组新增） |
| `accounting-dimension` | `accounting_dimension` | 核算维度 | 核算维度 | 归集财务数据的维度类型或实例。 | — | [分组语义](multi-entity/accounting-dimension.md)（仅未分组新增） |
| `assembling` | `assembling` | 组装单 | 组装单 | 成品与原材料的组装任务及明细。 | — | [分组语义](multi-entity/assembling.md)（仅未分组新增） |
| `bom` | `bom` | BOM单 | BOM单、BOM | 成品物料组成与版本，不等于组装执行。 | — | [分组语义](multi-entity/bom.md)（仅未分组新增） |
| `check-out` | `check_out` | 结账/反结账 | 结账、反结账 | 会计期间锁定/解锁；记录读写不代替财务动作。 | — | [分组语义](multi-entity/check-out.md)（仅未分组新增） |
| `contactor` | `contactor` | 联系人 | 联系人 | 客户关联人员；结合归属区分供应商联系人。 | — | [分组语义](multi-entity/contactor.md)（仅未分组新增） |
| `contract` | `contract` | 协议 | 协议 | 协议及条款履约；不等同于合同订单。 | — | [分组语义](multi-entity/contract.md)（仅未分组新增） |
| `customer-account` | `customer_account` | 客户账户 | 客户账户、账户设置 | 客户账户配置；官方称账户设置，不是交易流水。 | — | [分组语义](multi-entity/customer-account.md)（仅未分组新增） |
| `invoice` | `invoice` | 开票申请 | 开票申请 | 向客户开票的申请与业务依据。 | — | [分组语义](multi-entity/invoice.md)（仅未分组新增） |
| `invoice-info` | `invoice_info` | 发票信息 | 发票信息 | 开票/收票所用档案，不是发票或开票申请。 | — | [分组语义](multi-entity/invoice-info.md)（仅未分组新增） |
| `main-product` | `main_product` | 产品 | 产品 | 商品或服务主数据，不是单据产品明细。 | — | [分组语义](multi-entity/main-product.md)（仅未分组新增） |
| `opportunity` | `opportunity` | 销售机会 | 销售机会、商机 | 客户的独立销售目标及进展。 | — | [分组语义](multi-entity/opportunity.md)（仅未分组新增） |
| `plan-payment` | `plan_payment` | 计划回款 | 计划回款 | 未来回款安排，结合意图区分实际回款。 | — | [分组语义](multi-entity/plan-payment.md)（仅未分组新增） |
| `real-payment` | `real_payment` | 实际回款 | 实际回款 | 到账记录及核销来源，区别回款计划。 | — | [分组语义](multi-entity/real-payment.md)（仅未分组新增） |
| `project` | `project` | 项目 | 项目 | 独立项目目标与交付范围，区别同项目里程碑。 | — | [分组语义](multi-entity/project.md)（仅未分组新增） |
| `purchase-apply` | `purchase_apply` | 采购申请 | 采购申请 | 物资或服务采购需求，区别采购单。 | — | [分组语义](multi-entity/purchase-apply.md)（仅未分组新增） |
| `purchase-invoice` | `purchase_invoice` | 采购发票 | 采购发票 | 供应商发票及采购/认证/入账关联。 | — | [分组语义](multi-entity/purchase-invoice.md)（仅未分组新增） |
| `purchase-order` | `purchase_order` | 采购单 | 采购单、采购订单 | 向供应商下达的采购单，区别销售订单。 | — | [分组语义](multi-entity/purchase-order.md)（仅未分组新增） |
| `purchase-plan-payment` | `purchase_plan_payment` | 计划付款 | 计划付款 | 未来对外付款安排，区别实际付款。 | — | [分组语义](multi-entity/purchase-plan-payment.md)（仅未分组新增） |
| `purchase-price` | `purchase_price` | 采购价目表 | 采购价目表 | 供应商与物料价目及适用条件。 | — | [分组语义](multi-entity/purchase-price.md)（仅未分组新增） |
| `purchase-real-payment` | `purchase_real_payment` | 实际付款 | 实际付款 | 对外支付记录与核销来源，区别付款计划。 | — | [分组语义](multi-entity/purchase-real-payment.md)（仅未分组新增） |
| `purchase-return-order` | `purchase_return_order` | 采购退货单 | 采购退货单 | 向供应商退货，区别客户销售退货。 | — | [分组语义](multi-entity/purchase-return-order.md)（仅未分组新增） |
| `quotation` | `quotation` | 报价单 | 报价单 | 客户产品/服务报价及明细。 | — | [分组语义](multi-entity/quotation.md)（仅未分组新增） |
| `requisition` | `requisition` | 调拨单 | 调拨单 | 调出与调入安排，区别具体出/入库单。 | — | [分组语义](multi-entity/requisition.md)（仅未分组新增） |
| `sale-return-order` | `sale_return_order` | 销售退货单 | 销售退货单、退货单 | 客户退货单，区别采购退货。 | — | [分组语义](multi-entity/sale-return-order.md)（仅未分组新增） |
| `stock-in-other` | `stock_in_other` | 其他入库单 | 其他入库单 | 其他原因入库，按原因区别采购或调拨。 | — | [分组语义](multi-entity/stock-in-other.md)（仅未分组新增） |
| `stock-in-po` | `stock_in_po` | 采购入库单 | 采购入库单 | 采购收货入库，关联采购来源。 | — | [分组语义](multi-entity/stock-in-po.md)（仅未分组新增） |
| `stock-in-req` | `stock_in_req` | 调拨入库单 | 调拨入库单 | 调拨收货入库，关联调拨来源。 | — | [分组语义](multi-entity/stock-in-req.md)（仅未分组新增） |
| `stock-in-sro` | `stock_in_sro` | 销退入库单 | 销退入库单、销退货入库单 | 客户销售退货入库，关联原退货单。 | — | [分组语义](multi-entity/stock-in-sro.md)（仅未分组新增） |
| `stock-out-other` | `stock_out_other` | 其他出库单 | 其他出库单 | 其他原因出库，按原因区别销售或调拨。 | — | [分组语义](multi-entity/stock-out-other.md)（仅未分组新增） |
| `stock-out-pro` | `stock_out_pro` | 采退出库单 | 采退出库单、采购退货出库单 | 向供应商退货出库，关联采购退货来源。 | — | [分组语义](multi-entity/stock-out-pro.md)（仅未分组新增） |
| `stock-out-req` | `stock_out_req` | 调拨出库单 | 调拨出库单 | 调拨发货出库，关联调拨来源。 | — | [分组语义](multi-entity/stock-out-req.md)（仅未分组新增） |
| `stock-out-so` | `stock_out_so` | 销售出库单 | 销售出库单 | 销售发货出库，关联销售订单。 | — | [分组语义](multi-entity/stock-out-so.md)（仅未分组新增） |
| `supplier` | `supplier` | 供应商 | 供应商 | 供应商主体，区别其人员和账户。 | — | [分组语义](multi-entity/supplier.md)（仅未分组新增） |
| `supplier-account` | `supplier_account` | 供应商账户 | 供应商账户、账号信息 | 供应商账户配置；官方称账号信息。 | — | [分组语义](multi-entity/supplier-account.md)（仅未分组新增） |
| `supplier-contactor` | `supplier_contactor` | 供应商联系人 | 供应商联系人 | 供应商关联人员；结合归属区分客户联系人。 | — | [分组语义](multi-entity/supplier-contactor.md)（仅未分组新增） |
| `warehouse` | `warehouse` | 仓库 | 仓库 | 物理/逻辑仓库，需与内部库位区分。 | — | [分组语义](multi-entity/warehouse.md)（仅未分组新增） |
| `work-daily` | `work_daily` | 日报 | 日报 | 主体某日工作内容及计划。 | — | [分组语义](multi-entity/work-daily.md)（仅未分组新增） |
| `work-monthly` | `work_monthly` | 月报 | 月报 | 个人、团队或部门月度内容。 | — | [分组语义](multi-entity/work-monthly.md)（仅未分组新增） |
| `work-order` | `work_order` | 工单 | 工单 | 服务请求及独立问题处理。 | — | [分组语义](multi-entity/work-order.md)（仅未分组新增） |
| `work-weekly` | `work_weekly` | 周报 | 周报 | 个人、团队或部门周度内容。 | — | [分组语义](multi-entity/work-weekly.md)（仅未分组新增） |
