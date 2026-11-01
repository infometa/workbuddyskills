---
name: trade
display_name: 云MALL交易运营
display_name_en: CloudMall Trade Operations
description: 本域定位：订单交易执行链路（下单→支付→发货→售后），非商品/营销/门店管理。交易与物流运营：订单查询/发货/改址/自提核销/批量发货/Excel导入/导出标记/周期购退订、售后审核/退换货/代客创建/售后配置（自动退款/运费/时效/退库存）与原因库、支付退款/渠道启停/微信发货补报、发票/红冲/销方税收配置、对账差异/节点任务、到店预约、服务订单派单核销、退货地址、交易设置、CPS佣金订单、物流轨迹、快递公司/物流平台/区划配置。防混淆：优惠券/满减/秒杀→促销域；分销员/分销规则/佣金账户与提现/导购→营销域（按订单维度查询 CPS 推广订单与佣金，仍属本域）；商品类目税率/税收映射/开票配置属本域发票配置（勿因"商品"二字路由到商品域）；商品价格库存→商品域；积分兑换订单（积分商城）→用户域；配送方式/运费模板/履约模板→商户域（本域"物流平台"指轨迹查询对接平台如快递100，非配送履约模板）。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths for trade and logistics operations; execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.8.2
author: 云MALL
---

# 云MALL交易运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。本技能包含两个子域：**交易主域（订单/售后/支付/预约/发票对账/退货地址）**、**物流配置与轨迹（logistics）**。写操作的前置条件/状态约束在对应契约锚点内，本表不重复。

## 业务目的定位（本域是什么）

> 本域的业务本质是**管理订单全生命周期流转——从用户下单到支付/发货/收货/退款/售后的交易执行链路**。
> 不是商品管理（商品域）、不是营销拉新（营销域）、不是门店管理（商户域）。
> 简单判断：说"订单/发货/退款/售后/物流/支付/改址/核销"→本域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查订单/售后/支付/退款/发票/对账/预约/服务订单/CPS/物流轨迹/配置现值） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作**（发货/审核/退款/开票/配置保存/核销等） | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应业务族文件（发货履约与订单管理=`trade-fulfillment.md`；售后=`trade-aftersale.md`；售后配置=`trade-aftersale-config.md`；支付发票对账=`trade-finance.md`；预约地址设置=`trade-appointment.md`；服务订单=`trade-service-order.md`；写操作共同闭环=`trade-core.md`；物流配置=`logistics.md`）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值） | `references/domains/trade-enums.md`（主域状态机与枚举字典）/ `references/domains/logistics.md`（物流子域）→ 契约文件锚点 |
| **概念咨询/异常排查**（实体关系/规则语义/退款链路/实现缺口） | `references/domains/trade-concepts.md` → 契约文件锚点 |

## 能力路由表（唯一索引）

> 所有 capability 完整 id = `ops.` + 下表短名（如 `ops.` + `trade.order.search`）；物流子域为 `ops.logistics.` 前缀。契约文件均在 `references/apis/trade/` 下（物流为 `references/apis/logistics/`）。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器）

| 契约文件 | capabilities |
|---|---|
| `order-query.md` | trade.order.search 订单分页 · trade.order.tab-count 状态计数 |
| `order-detail.md` | trade.order.detail 订单详情 · trade.order.logistics 运单查询 · trade.order.urge-records 催单记录 · trade.order.pickup-verify.preview 核销预览 · trade.order.mark.get 标记查询 |
| `order-export-query.md` | trade.order.export 订单导出 · trade.order.export.task.detail 导出任务详情 · trade.order.export.task.list 导出任务列表 |
| `order-ship-batch-query.md` | trade.order.import-multi-package-ship.task 导入任务查询 |
| `aftersale-query.md` | trade.aftersale.search 售后分页 · trade.aftersale.tab-count 状态计数 · trade.aftersale.detail 售后详情 · trade.aftersale.reasons-detail 原因详情 · trade.aftersale.reasons.list 原因轻量映射 · trade.aftersale.refunded-summary 已退款汇总 · trade.aftersale.exchangeable-skus 可换规格 · trade.aftersale.remarks.list 备注流水 · trade.aftersale.export 售后导出 |
| `aftersale-config-query.md` | trade.aftersale.auto-refund.get 自动退款配置 · trade.aftersale.freight-rule.list 退运费规则 · trade.aftersale.timeout-config.get 售后时效配置 · trade.aftersale.inventory-config.get 退库存配置 |
| `aftersale-reason-query.md` | trade.aftersale.reason.list 原因库 · trade.aftersale.reason.group-list 原因大类 |
| `payment-query.md` | trade.payment.pay-order.search 支付单分页 · trade.payment.pay-order.detail 支付单详情 · trade.payment.refund.search 退款单查询 · trade.payment.channel-config.list 渠道配置列表 · trade.payment.pay-order.child-orders 支付单子单 |
| `order-cps.md` | trade.order-cps.search CPS推广订单分页 |
| `appointment-query.md` | trade.appointment.search 预约分页 · trade.appointment.tab-count 状态计数 · trade.appointment.calendar 预约日历 · trade.appointment.dashboard.metrics 预约看板 · trade.appointment.config.get 预约全局配置 · trade.appointment.export 预约导出 · trade.appointment.reminder-log.search 提醒记录 · trade.appointment.reminder-log.detail 提醒详情 |
| `invoice-query.md` | trade.invoice.search 发票分页 · trade.invoice.tab-count 状态计数 · trade.invoice.auth-status 认证阻塞状态 · trade.invoice.query-platform 发票平台状态 |
| `invoice-config-query.md` | trade.invoice.platform.list 开票平台列表 · trade.invoice.seller.list 销方列表 · trade.invoice.tax-category.list 税收分类编码 · trade.invoice.goods-tax.list 商品税收映射 · trade.invoice.goods-tax.default-rate.get 默认税率 |
| `reconcile-query.md` | trade.reconcile.diff.search 对账差异分页 · trade.reconcile.diff.detail 差异详情 · trade.reconcile.diff.handle-logs 处理记录 · trade.reconcile.config.list 节点配置 · trade.reconcile.alert-notify.get 告警配置 · trade.reconcile.dashboard.summary 看板汇总 · trade.reconcile.dashboard.risk-banner 风险横幅 · trade.reconcile.dashboard.node-status 节点状态 · trade.reconcile.dashboard.trend 对账趋势 · trade.reconcile.task.search 任务查询 |
| `trade-setting-query.md` | trade.setting.timeout-config 交易超时设置 · trade.setting.gift-warehouse-config.get 赠品仓规则 · trade.operation-log.search 配置操作日志 · trade.operation-log.detail 日志详情 |
| `service-order-query.md` | trade.service-order.search 服务订单分页 · trade.service-order.tab-count 阶段计数 · trade.service-order.export 服务订单导出 · trade.service-order.detail 购买单详情 · trade.service-order.time-slots 可约时段 |
| `return-address-query.md` | trade.return-address.search 退货地址分页 · trade.return-address.detail 地址详情 · trade.return-address.list-all 全量地址 |
| `express-company-query.md`（物流） | logistics.express-company.search 快递公司分页 · logistics.express-company.enabled-list 启用快递公司 |
| `platform-query.md`（物流） | logistics.platform.search 物流平台分页 · logistics.platform.supported-list 支持平台 · logistics.platform.enabled-list 启用平台 |

> **「物流平台」跨域消歧**：本域物流平台 = **轨迹查询对接平台**（快递100、快递鸟等运单轨迹服务的连接配置：平台名/编码/启停/凭据状态）。「配送方式 / 运费模板 / 履约模板」是**商户域**的履约配置概念——运营说"物流配置/配送配置"指向快递运费与履约时走商户域，说"物流平台/轨迹平台/查快递的平台"时留在本域。含"物流平台"字样的指令先在本域 platform.search/enabled-list 查证再回答。
| `region.md`（物流） | logistics.region.provinces 省级区划 · logistics.region.children 子级区划 |
| `track.md`（物流） | logistics.track.query 物流轨迹 |

### 写能力（Capability 写操作执行器）

| 契约文件 | capabilities |
|---|---|
| `order-action.md` | trade.order.ship 发货🔴 · trade.order.batch-full-ship 批量整单发货🔴 · trade.order.modify-ship 修改发货🔴 · trade.order.remark 备注覆盖 · trade.order.receiver-address.update 修改地址🔴 · trade.order.confirm-pickup 确认备货🔴 · trade.order.complete 人工完成🔴 · trade.order.pickup-verify.confirm 核销确认🔴 · trade.order.mark.set 批量标记 · trade.order.mark.clear 清除标记 · trade.order.period-buy.unsubscribe 周期购退订🔴 |
| `order-ship-batch-action.md` | trade.order.batch-ship 批量多包裹发货🔴 · trade.order.merge-ship 合并发货🔴 · trade.order.delivery-plan.update 发货计划更新🔴 · trade.order.import-ship 导入发货🔴 · trade.order.import-multi-package-ship 导入多包裹发货🔴 · trade.order.import-modify-logistics 导入改物流单号🔴 |
| `order-export-action.md` | trade.order.export.task.cancel 取消导出任务 |
| `aftersale-action.md` | trade.aftersale.audit 售后审核🔴 · trade.aftersale.return-logistics.input 退货物流录入🔴 · trade.aftersale.merchant-ship 换货发货🔴 · trade.aftersale.receive.confirm 确认收货🔴 · trade.aftersale.receive.reject 拒收🔴 · trade.aftersale.remark.update 备注覆盖 · trade.aftersale.remark.add 追加备注 · trade.aftersale.complete-offline 线下完结🔴 · trade.aftersale.modify 修改申请🔴 · trade.aftersale.reject-complete-offline 线下拒绝🔴 |
| `aftersale-behalf.md` | trade.aftersale.create-on-behalf 代客创建售后🔴 |
| `aftersale-config-action.md` | trade.aftersale.auto-refund.save 保存自动退款 · trade.aftersale.freight-rule.save 保存运费规则🔴 · trade.aftersale.freight-rule.reset 重置运费规则🔴 · trade.aftersale.timeout-config.save 保存售后时效🔴 · trade.aftersale.inventory-config.save 保存退库存🔴 |
| `aftersale-reason-action.md` | trade.aftersale.reason.create 新增原因 · trade.aftersale.reason.update 编辑原因 · trade.aftersale.reason.toggle 启停原因 · trade.aftersale.reason.delete 删除原因🔴 · trade.aftersale.reason.reorder 原因排序 |
| `payment-action.md` | trade.payment.pay-order.sync 同步支付🔴 · trade.payment.pay-order.close 关闭支付🔴 · trade.payment.refund.retry 退款重试🔴 · trade.payment.channel-config.update-status 渠道启停🔴 · trade.payment.channel-config.wx-shipping-switch 微信发货开关🔴 |
| `wx-shipping.md` | trade.payment.wx-shipping.report 微信发货补报🔴 |
| `appointment-action.md` | trade.appointment.confirm 确认预约🔴 · trade.appointment.reject 拒绝预约🔴 · trade.appointment.confirm-visit 确认到访🔴 · trade.appointment.no-show 标记爽约🔴 · trade.appointment.config.update 保存全局配置🔴 |
| `invoice-action.md` | trade.invoice.trigger 触发开票🔴 · trade.invoice.retry 重试开票🔴 · trade.invoice.red-flush 红冲🔴 · trade.invoice.apply-on-behalf 代客开票🔴 · trade.invoice.auth-clear 清除认证阻塞🔴 · trade.invoice.retry-file-transfer 文件转存补跑 · trade.invoice.red-confirm-operate 红字确认🔴 · trade.invoice.cancel 取消开票🔴 |
| `invoice-config-action.md` | trade.invoice.platform.toggle 平台启停🔴 · trade.invoice.platform.set-default 默认平台🔴 · trade.invoice.seller.save 保存销方 · trade.invoice.seller.delete 删除销方🔴 · trade.invoice.seller.set-default 默认销方 · trade.invoice.tax-category.save 保存税收分类 · trade.invoice.tax-category.delete 删除税收分类🔴 · trade.invoice.goods-tax.save 保存税收映射 · trade.invoice.goods-tax.delete 删除税收映射🔴 · trade.invoice.goods-tax.toggle 启停映射 · trade.invoice.goods-tax.default-rate.save 默认税率🔴 |
| `reconcile-action.md` | trade.reconcile.diff.mark-error 标记差错🔴 · trade.reconcile.diff.escalate 升级差异 · trade.reconcile.diff.confirm 确认处理🔴 · trade.reconcile.diff.remark 差异备注 · trade.reconcile.config.update 节点配置更新🔴 · trade.reconcile.alert-notify.save 保存告警 · trade.reconcile.task.trigger 手动触发对账🔴 |
| `trade-setting-action.md` | trade.setting.timeout-config.save 保存交易超时🔴 · trade.setting.gift-warehouse-config.save 保存赠品仓规则🔴 |
| `service-order-action.md` | trade.service-order.assist-appointment 协助预约🔴 · trade.service-order.reschedule 服务改约🔴 · trade.service-order.dispatch 派单🔴 · trade.service-order.redispatch 改派🔴 · trade.service-order.verify 服务核销🔴 |
| `return-address-action.md` | trade.return-address.create 创建地址 · trade.return-address.update 编辑地址 · trade.return-address.delete 删除地址🔴 |
| `express-company-action.md`（物流） | logistics.express-company.create 新增快递公司🔴 · logistics.express-company.update 更新🔴 · logistics.express-company.update-status 启停🔴 · logistics.express-company.delete 删除🔴 · logistics.express-company.sync-wechat-delivery 微信运力同步🔴 |
| `platform-action.md`（物流） | logistics.platform.update 更新平台🔴 · logistics.platform.update-status 启停🔴 · logistics.platform.test-connection 连接验证 · logistics.platform.delete 删除🔴 |

## 未开放（不调用，只整理需求）

文件流型导出与导入模板下载（走管理后台；URL 型导出与 Excel 导入已开放）、支付渠道创建与密钥配置（敏感凭据面，渠道启停与微信发货开关已开放）、开票平台凭据配置（appKey/appSecret，走管理后台；平台启停/默认切换已开放）、物流平台创建与凭据变更（无法形成确定性验证闭环）、预约规则维护、其他交易设置写入及内部维护。它们缺少开放能力契约或完整执行依赖；不推测能力标识。遇到需要这些能力才能确定的数据，说明具体缺口并停止相应写入，已完成的查询仍可报告。

## 通用约定（护栏）

- 只调用契约中明确登记的能力；查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`，输入为 `{capability,input,summary}`。
- 身份、授权和数据范围由连接自动绑定。不得索取或传递租户、账号、连接凭证、内部实现或技术定位信息。
- 全部雪花 ID 以十进制字符串传递和处理，绝不能转换为 JSON Number。金额是元的 JSON 数字；日期格式以对应参数表为准。
- 本域的相对时间（今天、最近 N 天、上个月、本月）按北京时间（UTC+8）计算（带偏移的时间字段写 `+08:00`）。运行时取当前时间的命令可能在加载本技能之前就已执行、默认输出 UTC（比北京时间晚 8 小时，北京时间 8 点前日期仍是前一天，跨月会错月）：已拿到 UTC 时间时，先加 8 小时再推算日期和月份；需要重新取时间时用 `TZ=Asia/Shanghai date`。
- 写操作只在用户明确要求执行后发生；工具从不自动重试。超时或网络失败先回读状态，不能因失败信息不完整而再次提交。
- `PERMISSION_DENIED`、`AUTH_REQUIRED`、`SCOPE_INSUFFICIENT` 立即停止；`INPUT_INVALID` 回到契约纠正；`UPSTREAM_*` 不是“无数据”或“未执行”。

## 嵌套对象与非结构化数据边界

嵌套输入按目标能力的全部叶子字段构造：发货 `packages[].items[]`、批量整单发货 `orders[]`、修改发货 `newPackages[].items[]`、代客售后 `items[]`。商品行 ID、SKU ID、订单号各有归属，不能互换。商品行和可选地址可从读取结果取得；用户负责确认操作意图、数量、金额及真实履约事实，无须手工提供系统中已经核实的 ID。

`Object`、映射和序列化文本不是自由填值的授权。售后凭证 `mediaJson` 与换货信息 `exchangeItemInfo` 按售后契约解释；前端预留映射不能扩展退货地址查询的分页字段。未知返回字段可忽略，但不得将整段返回对象原样当成写入对象。

## 写操作风险档位

| 档位 | 适用能力 | 必须纪律 |
|---|---|---|
| 🔴 资金、履约或不可逆 | 发货/改物流、批量多包裹/合并发货、Excel 导入发货/改物流单号、改地址、确认备货、完成订单、自提核销、服务订单协助预约/改约/派单/改派/核销、售后审核、退货/换货物流、收货确认、拒收、代客创建、线下完结/线下拒绝、修改售后申请、周期购退订/改发货计划、关闭或同步支付、退款重试、支付渠道启停/微信发货开关、微信发货补报、预约确认/拒绝/到访/爽约、预约全局配置保存、发票开具/重试/红冲/红字确认/取消/代客开票/清除认证阻塞、发票平台启停/默认切换/删除销方/删除税收分类/删除类目映射/默认税率、对账标记或确认、对账节点配置更新/手动触发、订单超时配置与赠品仓规则保存、删除地址、删除售后原因、退运费规则保存/重置、售后时效与退库存配置保存、售后导出 | 先读当前对象、复述对象和金额/物流/状态影响，取得明确确认；提交后按流程回读并逐项报告 |
| 🟡 有运营影响但可追溯 | 订单/售后备注、对账备注/升级/告警通知保存、创建或编辑退货地址、售后原因创建/编辑/启停/排序、自动退款配置保存、订单标记设置/清除、取消导出任务、发票文件转存补跑、销方保存/默认切换、税收分类与类目映射保存/启停 | 用户明确指令后执行；覆盖编辑须先读原值；提交后回读或报告返回结果 |
| 🟢 只读 | 所有 search/detail/count/logistics/calendar/dashboard 能力，售后原因/大类/轻量原因/备注流水/已退款汇总/可换规格查询，四组售后配置读取，发票认证状态/平台状态查询/平台销方税率清单读取，对账配置/看板/任务查询，交易设置与操作日志读取，服务订单全部查询能力 | 可直接调用 |

风险等级在本表统一定义；能力文档解释具体前置条件，不得自行降档。用户已明确确认同一对象、同一数值和同一影响时不重复索要确认；读取到状态或金额变化后须重新说明。

## 意图分流与执行边界

| 用户诉求 | 选择依据 |
|---|---|
| 发货 / 改运单 / 批量发货 | 新发商品使用发货；调整已有包裹使用修改发货；批量整单仅适用每单一套整单物流的已核实订单清单；逐包裹指定商品内容用批量多包裹发货；多订单合并包裹用合并发货；Excel 批量场景走导入链路（用户提供文件） |
| 拒绝售后 | 待审核走审核拒绝；待商家收货走拒收；自行退回自提点且待买家退回走线下拒绝；其他阶段不得套用这三项 |
| 改备注 / 追加跟进记录 | 覆盖已有备注与追加运营流水分别使用对应能力，不能根据名称相近替换；追加后可用备注流水查询核对 |
| 退款是否到账 | 读取退款状态，退款中与退款成功分别报告；售后审核通过不等于到账 |
| 确认自提 / 确认到店 | 实物自提走核销预览与确认；服务预约到店走预约处置，核销码与预约 ID 不通用 |
| 改售后申请 / 改售后规则 | 待审核申请的内容更正走售后修改；售后规则（自动退款/运费/时效/退库存/原因库）走对应配置与原因库能力，全量覆盖先读现值 |
| 修改设置 / 发票平台配置 | 交易侧超时与赠品仓、售后侧设置（自动退款/运费规则/售后时效/退库存）、预约全局配置均已开放读写（先读现值全量提交）；发票平台启停与销方/税收配置已开放，平台凭据配置走管理后台 |
| 预约服务 / 服务订单履约 | 到店预约台账走预约契约；服务类商品（上门/取送）履约走服务订单契约（购买单/履约子单/次数序号三层标识），4 位服务核销码与 6 位实物自提核销码不通用 |

## 物流子域（logistics）特有纪律

- 查询使用 `当前运行时的 Capability 查询执行器`，写入使用 `当前运行时的 Capability 写操作执行器`，输入为 `{capability,input,summary}`；写操作单次提交且不自动重试。
- 快递公司与物流平台均为**共享配置**：先查询现态，向用户确认对象和影响，再执行，最后回读；超时后先查现态，不盲目重试。
- 删除为逻辑删除且当前开放能力集不含恢复操作；停用会影响发货选项或轨迹查询，执行前必须确认。
- 平台凭据属于敏感信息，列表不会返回。当前连接验证存在误判，普通轨迹也无法证明目标平台凭据有效，因此**平台创建和凭据变更暂不开放**；平台启用只在用户已有外部验证证据并明确要求时执行。
- 物流子域已开放能力——查询：`ops.logistics.express-company.search`、`ops.logistics.express-company.enabled-list`、`ops.logistics.platform.search`、`ops.logistics.platform.supported-list`、`ops.logistics.platform.enabled-list`、`ops.logistics.region.provinces`、`ops.logistics.region.children`、`ops.logistics.track.query`；写入：`ops.logistics.express-company.create`、`ops.logistics.express-company.update`、`ops.logistics.express-company.update-status`、`ops.logistics.express-company.delete`、`ops.logistics.express-company.sync-wechat-delivery`、`ops.logistics.platform.update`、`ops.logistics.platform.update-status`、`ops.logistics.platform.delete`、`ops.logistics.platform.test-connection`。
- 物流子域未开放：平台创建与凭据变更（无法形成确定性验证闭环）、内部服务调用、平台回调、文件导入导出、包裹项与运单底层维护、订阅重试、配送区块、配送方式。用户命中时只说明当前不可执行并整理需求。

## 结果与未知状态

成功工具结果包含 `capability`、`data`、`traceId`；`data` 的业务结构以相应契约为准。空数据、动作受理、批量部分成功和最终完成必须区分。写入没有业务返回字段时，只说明提交成功，按流程读取目标对象验证；读取失败则报告“已提交，结果待核验”。

列表可能延迟反映状态，零命中不能证明写入失败。敏感字段只用于本次授权操作所需的对象核对；不能把脱敏文本或密文回写成手机号、地址，也不能假设开放能力提供解密功能。
