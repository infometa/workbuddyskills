# 渠道云能力目录参考

> ⚠️ 以下为一次快照（共 41 项，其中可用 26 项、关闭 15 项）。**能力可用性会随服务端状态变化**，执行时务必以 `search_abilities` 的实时返回为准，**不要凭记忆推导 ability_code**。可用性统计以 `whoami` 的 `available_ability_count` 为权威值。

## base — 基础资料（8 项，全部可用）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.base.ai.item.find | 商品查询 | 关键词/分类/状态筛选 + 分页 |
| chaoyue.base.ai.item.read | 商品详情 | 按商品编码查询，返回字段经白名单 |
| chaoyue.base.ai.item.category.find | 商品分类查询 | 支持层级；单次最多 500 个分类 |
| chaoyue.base.ai.client.find | 客户门店档案查询 | 含等级、归属渠道商；customer_id 精确查询与 name/code 分页不能混用 |
| chaoyue.base.ai.supplier.find | 供应商查询 | 含供货关系 |
| chaoyue.base.ai.store.find | 门店档案查询 | 含生命周期阶段；不接受参数 |
| chaoyue.base.ai.warehouse.find | 仓库档案查询 | 按名称或编号分页 |
| chaoyue.base.ai.employee.find | 员工目录查询 | 仅启用员工、仅非敏感字段，不含手机号/登录账号 |

## inv — 库存（5 项，全部可用）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.inv.ai.inventory.find | 库存查询 | 按门店/仓库/商品，校验仓库权限 |
| chaoyue.inv.ai.inventory.movement.find | 库存进出明细 | 最长 31 天、默认近 30 天；不返回库存成本和库存金额 |
| chaoyue.inv.ai.transferorder.find | 转仓单查询 | 按单号和日期分页 |
| chaoyue.inv.ai.stockloss.find | 报损单查询 | 按单号和日期分页 |
| chaoyue.inv.ai.stocksurplus.find | 报溢单查询 | 按单号和日期分页 |

## sal — 销售（4 项可用 + 1 项写入关闭）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.sal.ai.saleorder.find | 销售单查询 | 支持金额/数量/折扣/退货筛选；order_type 202 出仓为常用值 |
| chaoyue.sal.ai.saleorder.read | 销售单详情 | 单据头 + 明细；由分页结果与商品明细两次受控查询组合 |
| chaoyue.sal.ai.saleorder.detail.find | 销售明细查询 | 商品级销售明细 |
| chaoyue.sal.ai.returnorder.find | 退货单查询 | 含退货原因、遵循字段白名单；当前复用退款单类型 203 |
| chaoyue.sal.ai.priceadjustment.apply | 应用调价单 | ❌ 写入能力，默认关闭，稳定返回 ability_disabled |

## pur — 采购（4 项，全部可用）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.pur.ai.purchaseorder.find | 采购订单查询 | 含供应商；不返回采购成本 |
| chaoyue.pur.ai.receiveorder.find | 收货单查询 | 含入库状态 |
| chaoyue.pur.ai.returnorder.find | 采购退货单查询 | 按采购退货类型 103 查询 |
| chaoyue.pur.ai.purchasedetail.find | 采购商品明细查询 | 按商品名称和日期分页 |

## fin — 财务（2 项可用 + 3 项关闭）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.fin.ai.receivable.find | 客户应收查询 | 含账期、逾期天数；最长 366 天，默认近 30 天 |
| chaoyue.fin.ai.payable.find | 供应商应付查询 | 含往来账合计；最长 366 天 |
| chaoyue.fin.ai.settlement.find | 客户结算单查询 | ❌ 无可信生产执行器 |
| chaoyue.fin.ai.collection.find | 收款单查询 | ❌ 无可信生产执行器 |
| chaoyue.fin.ai.clientprice.find | 客户价格查询 | ❌ 需独立价格权限 |

## rpt — 报表（3 项可用 + 4 项关闭）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.rpt.ai.itemsales.find | 商品销售分析 | summary_types 支持 branch/item/bizday，**当前执行器仅实现 item** |
| chaoyue.rpt.ai.itempurchase.find | 商品采购分析 | 统一采购口径 |
| chaoyue.rpt.ai.salecategory.find | 商品分类销售分析 | 按商品分类统计 |
| chaoyue.rpt.ai.branchindicator.find | 门店指标分析 | ❌ 无可信生产执行器 |
| chaoyue.rpt.ai.iteminventory.find | 商品库存分析 | ❌ 无可信生产执行器 |
| chaoyue.rpt.ai.clientpurchase.find | 客户采购分析 | ❌ 无可信生产执行器 |
| chaoyue.rpt.ai.itemlossprofit.find | 商品损益分析 | ❌ 含毛利，需独立利润权限 |

## life — 门店生命周期（7 项，全部关闭）

| ability_code | 能力 | 说明 |
|---|---|---|
| chaoyue.life.ai.store.profile.find | 门店全生命周期档案 | ❌ 无可信生产执行器 |
| chaoyue.life.ai.visit.record.find | 拜访记录查询 | ❌ 无可信生产执行器 |
| chaoyue.life.ai.visit.record.apply | 创建拜访记录 | ❌ 写入能力，默认关闭 |
| chaoyue.life.ai.store.salesrate.find | 门店动销率 | ❌ 无可信生产执行器 |
| chaoyue.life.ai.store.churnscore.find | 门店流失评分 | ❌ 无可信生产执行器 |
| chaoyue.life.ai.store.recall.find | 召回任务查询 | ❌ 无可信生产执行器 |
| chaoyue.life.ai.store.summary | 生命周期阶段分布 | ❌ 无可信生产执行器 |

## 错误码清单

| 错误码 | 含义 | 处理方式 |
|---|---|---|
| invalid_args | 参数不符合 input_schema | 重新读文档修正后重试一次 |
| unauthorized | 会话/授权失效 | 用户重新授权连接器 |
| forbidden_store | 对象不在授权门店/仓库范围 | 说明范围限制，不要重试 |
| ability_disabled | 能力未开放 | 如实告知，给替代能力 |
| upstream_unavailable | 下游业务系统不可用 | 重试 ≤2 次，仍失败则反馈 |
| sale_unavailable | 销售执行器不可用（非标准码） | 同上，反馈时注明该码 |
| session_not_found | MCP 会话失效 | 用户重连连接器 |
