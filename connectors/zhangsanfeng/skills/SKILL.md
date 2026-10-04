---
name: zhangsanfeng
description: 账三丰 连接器技能 - 财务/进销存/MES 数据查询与文字录入
version: "1.0.0"
author: "神州三丰科技"
---

# 账三丰 Skill

本 Skill 描述账三丰 连接器提供的全部工具。所有工具都以**客户本人身份**访问其授权企业的数据，客户没有权限的模块，其工具不会出现在 tools/list 里，不要向客户承诺这些能力。

## 使用原则

- 先用 `list_account_sets` 了解客户名下账套；多账套时按客户要求 `switch_account_set` 再查，多年度账套用 `switch_fiscal_year`
- 查询类工具不带日期时默认本月；客户说了时间范围就传 `startDate` / `endDate`（yyyy-MM-dd）
- **录入类必须两步**：先调 `*_preview` 生成草稿并把草稿摘要念给客户，客户明确确认后再调 `*_commit`，且 commit 只传 `draft_id`
- 金额、数量、单价一律从客户原话取，不要自行估算或补全；预览返回"没能对上"时把问题转述给客户重说
- 工具返回 `isError` 时把返回文案原样告知客户，不要重试同一调用
- 客户要找人（转人工、客服电话）才调 `contact_human_support`，并只说它返回的联系方式；只问业务数据时不要调

## 工具总览

| 产品线 | 模块 | 工具数 |
|---|---|---:|
| 通用 | 通用 | 4 |
| 财务云 | 录凭证 | 4 |
| 财务云 | 查凭证 | 2 |
| 财务云 | 科目与辅助核算 | 2 |
| 财务云 | 账簿 | 7 |
| 财务云 | 辅助账簿 | 3 |
| 财务云 | 财务报表 | 12 |
| 财务云 | 财税分析 | 1 |
| 财务云 | 出纳 | 7 |
| 财务云 | 智能存货 | 4 |
| 财务云 | 工资 | 3 |
| 财务云 | 固定资产 | 3 |
| 进销存 | 进销存综合 | 14 |
| 进销存 | 采购管理 | 9 |
| 进销存 | 销售管理 | 8 |
| 进销存 | 库存管理 | 24 |
| 进销存 | 资金管理 | 12 |
| 生产与 MES | 生产管理 | 9 |
| 生产与 MES | 委外管理 | 5 |
| 生产与 MES | MES 制造 | 36 |
| 合计 | | 169 |

下文每个工具给出用途与参数（`*` 为必填）；完整说明以 tools/list 返回的 description 与 inputSchema 为准。

## 通用

### 模块：通用

#### contact_human_support

获取账三丰的人工客服联系方式（客服热线、服务时段、客服企业微信二维码）。

无参数。

#### list_account_sets

列出当前企业下我能用的账套（核算主体），标出当前正在使用的那个。

无参数。

#### switch_account_set

切换当前使用的账套（核算主体）。

参数：`name`* (string)

#### switch_fiscal_year

同一账套（核算主体）下切换财务年度，只在客户明确说【去年的账】【2024年的账】这类跨年度查询时用；客户说的是账套名称/切到别的账套，应调用 switch_account_set 而不是本工具。

参数：`index` (integer)、`year` (integer)

## 财务云

### 模块：录凭证

#### finance_account_search

按科目名称或科目编码查询会计科目，返回可用于记账的末级科目候选。

参数：`keyword`* (string)、`limit` (integer)

#### finance_assist_search

按类型（客户、供应商、人员、项目、部门、存货）和关键词查询辅助核算档案。

参数：`assistType`* (string)、`keyword` (string)、`limit` (integer)

#### finance_voucher_commit

客户已经明确回复确认后，提交 finance_voucher_preview 生成的凭证草稿完成记账凭证录入。只接受 draft_id 一个参数，不接受也不采纳任何金额、科目等数值——一律以草稿内容为准。客户没有明确说确认之前，不要调用这个工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| draft_id | string | ✅ | finance_voucher_preview 返回的草稿编号 |

#### finance_voucher_preview

根据客户口述生成一张待确认的记账凭证草稿，不会真实入账。适用问法如“记一笔差旅费200万，现金付的”“帮我记一笔管理费用”。生成草稿后必须等客户明确回复确认，再调用 finance_voucher_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续金额与数量核验，必须原样传入，不要转述或改写 |
| biz_date | string | ✅ | 凭证业务日期，格式 yyyy-MM-dd |
| entries | array<object> | - | 凭证分录，至少两行，且全部借方金额之和必须等于全部贷方金额之和 |
| entries_json | string | - | 与 entries 二选一：把分录数组序列化成 JSON 文本传进来，例如 [{"account_name":"管理费用_业务招待费","debit":"200","credit":"0","summary":"招待费"},{"account_name":"库存现金","debit":"0","credit":"200","summary":"招待费"}]。 |

### 模块：查凭证

#### finance_entry_lookback

查询我(或全账套)这段时间录入了哪些财务凭证/多少钱，并标注每张凭证是小丰对话录入还是手工录入。

参数：`relative_period` (string)、`scope` (string)

#### finance_voucher_detail

按凭证字号精确查询一张凭证的完整信息，返回凭证日期、摘要、每一条分录的科目和借贷金额、借贷合计、附件张数和审核状态。

参数：`year`* (integer)、`month`* (integer)、`voucherNumber`* (string)

### 模块：科目与辅助核算

#### finance_account_tree

查询财务科目列表/科目树：不传关键词返回一级科目全集，传编号定位该科目及其直接子科目，传中文名模糊匹配，传"现金"/"库存现金"按现金标志位精确定位。

参数：`keyword` (string)、`level` (integer)、`is_last_level` (boolean)、`category` (string)

#### finance_assist_archive

查询财务辅助核算档案（客户/供应商/仓库/存货/项目/部门/账户/支出类别/收入类别等），支持按名称/编号模糊匹配、按真实档案类型确定性归类过滤。

参数：`name` (string)、`archive_type` (string)

### 模块：账簿

#### finance_account_balance

查询科目余额表：按会计科目列出期初余额、本期借方发生额、本期贷方发生额、期末余额和本年累计发生额。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`account` (string)、`accountLevel` (integer)、`includeZeroBalance` (boolean)、`page` (integer)、`size` (integer)

#### finance_book_details

查询某一个会计科目的明细账（该科目的逐笔流水）：按时间顺序列出每一笔分录的日期、凭证字号、摘要、借方金额、贷方金额和余额，开头一行是期初余额，每个月末带本期合计和本年累计。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`account`* (string)、`summary` (string)、`page` (integer)、`size` (integer)

#### finance_chronology_account

查询某个会计期间开过哪些凭证（序时账），返回每张凭证的日期、凭证字号、借贷合计、审核状态和分录明细。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`summary` (string)、`status` (integer)、`page` (integer)、`size` (integer)

#### finance_current_period

查询当前财务账套的记账进度和记账范围。

无参数。

#### finance_general_ledger

查询某一个会计科目的总账：逐月列出这个科目的期初余额、本期借贷发生额、期末余额和本年累计发生额，每个月三行（期初余额、本期合计、本年累计）。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`account`* (string)、`includeZeroPeriod` (boolean)

#### finance_multi_column_journal

查询某一个会计科目的多栏账：在明细账的基础上，把这个科目的下级科目横向铺成一栏一栏，一眼看出每笔业务分别落在哪个明细项上。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`account`* (string)、`onlyLastLevelColumns` (boolean)、`includeZeroColumnAccount` (boolean)、`page` (integer)、`size` (integer)

#### finance_voucher_summary

查询凭证汇总表：把一段会计期间内所有凭证按科目汇总，给出每个科目的借方合计、贷方合计，以及这段期间的凭证总张数和附件总张数。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`accountLevel` (integer)

### 模块：辅助账簿

#### finance_assist_balance

查询辅助核算余额表：按辅助核算类别（客户、供应商、人员、项目、部门、存货等）列出每个核算项目的期初余额、本期借贷发生额、期末余额和本年累计。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`assistCategoryName`* (string)、`includeZeroBalance` (boolean)、`page` (integer)、`size` (integer)

#### finance_currency_balance

查询外币核算余额表：对开了外币核算的会计科目，同时给出原币金额和折算成人民币的本位币金额，含期初余额、本期借贷发生额、期末余额和本年累计。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth` (integer)、`account` (string)、`includeZeroBalance` (boolean)、`page` (integer)、`size` (integer)

#### finance_dc_checklist

查询往来核算勾稽表：给出某个会计期间末，每个客户的应收账款余额和预收账款余额，或者每个供应商的应付账款余额和预付账款余额。

参数：`year`* (integer)、`month`* (integer)、`dcType`* (integer)

### 模块：财务报表

#### finance_assets_liabilities

查询资产负债表。

参数：`year` (integer)、`period` (integer)

#### finance_boss_business_status

查询经营状况表（老板报表之一）。

参数：`year` (integer)

#### finance_boss_cost_statistics

查询费用统计表（老板报表之一）。

参数：`year` (integer)

#### finance_budget_check_change

查询预算结转结余变动表。

参数：`year` (integer)、`period` (integer)

#### finance_budget_income_expense

查询预算收入支出表、收入费用表或者盈余及盈余分配表，三选一，用 reportKind 指定。

参数：`year` (integer)、`period` (integer)、`season` (integer)、`reportKind`* (integer)

#### finance_cash_flow

查询现金流量表。

参数：`year` (integer)、`period` (integer)、`season` (integer)

#### finance_dept_profit

查询部门利润表。

参数：`year` (integer)、`period` (integer)、`season` (integer)

#### finance_owner_equity_change

查询所有者权益变动表。

参数：`year` (integer)、`period` (integer)

#### finance_profit_distribution

查询收益及收益分配表。

参数：`year` (integer)、`period` (integer)

#### finance_profits

查询利润表（也叫损益表）。

参数：`year` (integer)、`period` (integer)、`season` (integer)

#### finance_project_profit

查询项目利润表。

参数：`year` (integer)、`period` (integer)、`season` (integer)

#### finance_receivable_payable_statistics

查询应收统计表或应付统计表，用 receivableOrPayable 指定查哪一张。

参数：`year` (integer)、`period` (integer)、`receivableOrPayable`* (integer)

### 模块：财税分析

#### finance_boss_tax_statistics

查询纳税明细统计表。

参数：`year` (integer)

### 模块：出纳

#### finance_account_check

核对出纳账和总账。

参数：`year`* (integer)、`period`* (integer)、`includeSealed` (boolean)

#### finance_account_statistics

查询出纳账户统计。

参数：`year`* (integer)、`period`* (integer)

#### finance_account_statistics_chart

查询某个现金或银行账户最近 12 个月的收支走势。

参数：`accountKeyword`* (string)、`year`* (integer)、`period`* (integer)

#### finance_cash_or_bank_charges

查询某个现金或银行账户的日记账流水。

参数：`accountKeyword`* (string)、`startYear`* (integer)、`startPeriod`* (integer)、`endYear`* (integer)、`endPeriod`* (integer)、`limit` (integer)

#### finance_cash_statement

查询某个现金或银行账户某一天的资金日报表。

参数：`accountKeyword`* (string)、`year`* (integer)、`period`* (integer)、`day`* (integer)、`limit` (integer)

#### finance_charge_balance

查询资金日报余额表。

参数：`year`* (integer)、`period`* (integer)、`limit` (integer)

#### finance_income_detail

查询收支明细表，按收支类别汇总。

参数：`accountKeyword` (string)、`startYear`* (integer)、`startPeriod`* (integer)、`endYear`* (integer)、`endPeriod`* (integer)、`includeZeroRows` (boolean)、`limit` (integer)

### 模块：智能存货

#### finance_inventory_ledger

查询某个存货（商品、材料）的明细账，也叫出入库明细表。

参数：`inventoryKeyword`* (string)、`startYear`* (integer)、`startPeriod`* (integer)、`endYear`* (integer)、`endPeriod`* (integer)、`limit` (integer)

#### finance_inventory_summary

查询存货汇总表，也叫出入库汇总表、存货结存表。

参数：`year`* (integer)、`period`* (integer)、`categoryKeyword` (string)、`inventoryKeyword` (string)、`includeYtd` (boolean)、`limit` (integer)

#### finance_invoice_statistics

查询发票统计。

参数：`startYear`* (integer)、`startPeriod`* (integer)、`endYear`* (integer)、`endPeriod`* (integer)、`invoiceType` (integer)、`payee` (string)、`payer` (string)、`invoiceNumber` (string)、`limit` (integer)

#### finance_product_gross_profit

查询商品毛利表。

参数：`year`* (integer)、`period`* (integer)、`keyword` (string)、`limit` (integer)

### 模块：工资

#### finance_wages_company_summary

查询账套某月工资/个税公司级聚合：纳税人数、应发工资总额、应纳税额、实发工资总额、单位承担社保合计、单位承担公积金，按工资类型（正常工资薪金/外籍人员工资薪金/全年一次性奖金收入/劳务报酬）逐行返回，不跨类型相加。

参数：`target_year` (integer)、`target_period` (integer)、`relative_period` (string)

#### finance_wages_department_summary

按部门查询工资聚合：应发工资合计、实发工资合计、个税合计、在职人数。

参数：`target_year` (integer)、`target_period` (integer)、`relative_period` (string)、`dept_name` (string)

#### finance_wages_employee_detail

查询员工个人工资明细：本期收入/年收入、社保四项个人承担、专项附加六项、个税、实发工资。

参数：`target_year` (integer)、`target_period` (integer)、`relative_period` (string)、`employee_name` (string)、`sort` (string)

### 模块：固定资产

#### finance_asset_card_list

查询资产卡片列表（固定资产 / 无形资产 / 长期待摊费用）。

参数：`propertyType`* (integer)、`keyword` (string)、`page` (integer)、`size` (integer)

#### finance_depreciation_detail

查询折旧（摊销）明细表：逐张资产卡片列出选定年度内每个月计提了多少折旧或摊销，并给出期末累计折旧和期末净值，还带类别小计和合计行。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth`* (integer)、`propertyType` (integer)、`groupByDept` (boolean)

#### finance_depreciation_summary

查询折旧（摊销）汇总表：按资产类别（可再按使用部门）汇总选定年度内每个月的折旧或摊销额，并给出原值、减值准备、期末累计折旧、期末净值和本年累计折旧。

参数：`year`* (integer)、`startMonth`* (integer)、`endMonth`* (integer)、`propertyType` (integer)、`groupByDept` (boolean)

## 进销存

### 模块：进销存综合

#### anomaly_alert_scan

扫描生产异常预警：良品率低于阈值的工人、产量环比下降超过阈值的工人，两类结果合并返回并用 AlertType 字段区分(rate=良品率异常/drop=产量环比降异常)。

参数：`startDate` (string)、`endDate` (string)、`prevStartDate` (string)、`prevEndDate` (string)、`good_rate_threshold` (number)、`output_drop_threshold` (number)

#### completion_forecast

预测工单还需要多少天能完工：按该工单近14天的良品产出节奏估算日均产量，推算预计完工日并与计划完工日比较。

参数：`order_no` (string)

#### doc_detail_list

按 doc_type 逐条列出报工单/产成品入库检验单/工单的明细字段(不是只回数量，想看总数用 document_count)，固定按时间倒序最多返回50条。

参数：`doc_type`* (string)、`startDate` (string)、`endDate` (string)、`worker_name` (string)

#### document_count

只统计报工单/产成品入库检验单/工单的数量，或判断某类单据是否存在，不返回任何逐条明细。

参数：`doc_type`* (string)、`startDate` (string)、`endDate` (string)、`product_name` (string)、`process_name` (string)、`workshop_name` (string)

#### kpi_compare

环比对比：产量/良品率/不良率/合格率/完成率(五选一，通过 metric 指定)本期与上期的对比。

参数：`metric`* (string)、`startDate` (string)、`endDate` (string)、`group_by` (string)

#### overview_detail

简报详情下钻：在 production_overview 简报基础上追加与上期(上月/上一周期)的环比对比，返回 11 行纵表——5 个可比指标(产量/不良数/良品率/质检合格率/工单完成率，均含本期值/上期值/环比变化)…

参数：`startDate` (string)、`endDate` (string)

#### psi_batch_search

按存货查可用批次列表（批次号/生产日期/可用数量），批次管理的存货开单填批次号前用它。

参数：`goodsId`* (string)、`warehouseId` (string)

#### psi_entity_compare

同一指标(metric四选一，同psi_period_compare)下、同一时间段内两个具体对象的数字对比。

参数：`metric` (string)、`dimension` (string)、`entity_a_name`* (string)、`entity_b_name`* (string)、`startDate` (string)、`endDate` (string)、`side` (string)

#### psi_entry_lookback

查询我(或全账套)这段时间录入了哪些进销存单据/多少钱，含出入库单据与采购/销售订单，并标注每张单是小丰对话录入还是手工录入。

参数：`relative_period` (string)、`scope` (string)

#### psi_goods_price

按账套配置的取价规则取存货单价。

参数：`billType`* (integer)、`partnerAid` (string)、`date` (string)、`items`* (array)

#### psi_goods_search

按存货编码或名称模糊查存货档案，返回 AID、编码、名称、三个单位（采购/销售/库存）、单位换算率、参考进价、是否批次管理。

参数：`keyword`* (string)、`limit` (integer)

#### psi_partner_search

按名称或编码模糊查往来单位档案（供应商或客户），返回 AID、编码、名称。

参数：`partnerType`* (string)、`keyword`* (string)、`limit` (integer)

#### psi_period_compare

同一指标(metric四选一: sales=销售/purchase=采购/stock_movement=出入库/receipt_payment=资金)在两个时间段之间的对比，…

参数：`metric` (string)、`compare_type` (string)、`startDate` (string)、`endDate` (string)、`prev_start` (string)、`prev_end` (string)、`side` (string)

#### psi_warehouse_search

按名称或编码模糊查仓库档案，返回 AID、编码、名称。

参数：`keyword`* (string)、`limit` (integer)

### 模块：采购管理

#### psi_bill_commit

客户已经明确回复确认后，提交进销存开单预览工具（如 purchase_in_bill_preview）生成的单据草稿完成开单。只接受 draft_id 一个参数，不接受也不采纳任何数量、单价等数值——一律以草稿内容为准。客户没有明确说确认之前，不要调用这个工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| draft_id | string | ✅ | 开单预览工具返回的草稿编号 |

#### psi_purchase_summary

查询指定时段内按存货或供应商汇总的采购总数(口径=Σ采购入库−Σ采购退货，以入库/退货单为准，非订单)。

参数：`startDate` (string)、`endDate` (string)、`dimension` (string)、`order_by` (string)、`counterparty_name` (string)、`min_amount` (number)、`max_amount` (number)、`min_count` (number)、`max_count` (number)、`limit` (integer)

#### psi_purchase_trend

按月统计采购入库/采购退货/净采购额(=入库-退货)价税合计走势，口径对齐 PSI 首页采购折线图(只算已审核已记账且未收票的采购入库/采购退货单据)。

参数：`startDate` (string)、`endDate` (string)

#### purchase_in_bill_list

查询采购入库单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### purchase_in_bill_preview

根据客户口述生成一张待确认的采购入库单草稿，不会真实变动库存。适用问法如“昨天从鑫源采购黄桃30个，单价20，入1号仓”“开一张采购入库单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 供应商名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

#### purchase_order_list

查询采购订单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### purchase_order_preview

根据客户口述生成一张待确认的采购订单草稿，不会真实下单。适用问法如“帮我下一个采购订单，跟鑫源订黄桃100个”“开一张采购订单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 供应商名称 |
| warehouse_name | string | - | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |
| delivery_date | string | - | 交货日期，格式2026-09-01，不填默认等于单据日期 |

#### purchase_return_bill_list

查询采购退货单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### purchase_return_bill_preview

根据客户口述生成一张待确认的采购退货单草稿，不会真实变动库存。适用问法如“退给供应商鑫源黄桃5个，从1号仓出”“开一张采购退货单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 供应商名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

### 模块：销售管理

#### psi_sales_rank

查询指定时段内按存货/客户/业务员/仓库统计的销售排行。

参数：`startDate` (string)、`endDate` (string)、`dimension` (string)、`order_by` (string)、`counterparty_name` (string)、`min_amount` (number)、`max_amount` (number)、`min_count` (number)、`max_count` (number)、`limit` (integer)

#### psi_sales_trend

按月统计销售出库/销售退货/净销售额(=出库-退货)价税合计走势，口径对齐 PSI 首页销售折线图(只算已审核已记账的销售出库/销售退货单据)。

参数：`startDate` (string)、`endDate` (string)

#### sale_order_list

查询销售订单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### sale_order_preview

根据客户口述生成一张待确认的销售订单草稿，不会真实下单。适用问法如“给客户张三下一张销售订单，黄桃50个”“开一张销售订单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 客户名称 |
| warehouse_name | string | - | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |
| delivery_date | string | - | 交货日期，格式2026-09-01，不填默认等于单据日期 |

#### sale_out_bill_list

查询销售出库单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### sale_out_bill_preview

根据客户口述生成一张待确认的销售出库单草稿，不会真实变动库存。适用问法如“卖给张三黄桃20个，单价30，从1号仓出”“开一张销售出库单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 客户名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

#### sale_return_bill_list

查询销售退货单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### sale_return_bill_preview

根据客户口述生成一张待确认的销售退货单草稿，不会真实变动库存。适用问法如“客户张三退回黄桃3个，入1号仓”“开一张销售退货单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | ✅ | 客户名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

### 模块：库存管理

#### allocation_bill_list

查询调拨单列表（仓库之间调货的单据）。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### combine_bill_detail

按单号查询单个组装单或拆卸单的完整详情，含子件明细。

参数：`number`* (string)

#### combine_bill_list

查询组装单/拆卸单列表。

参数：`billKind` (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### cost_adjust_bill_detail

按单号查询单个成本调整单的完整详情，含各存货调整明细。

参数：`number`* (string)

#### cost_adjust_bill_list

查询成本调整单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### cost_share_bill_detail

按单号查询单个费用分摊单的完整详情，含分摊明细。

参数：`number`* (string)

#### cost_share_bill_list

查询费用分摊单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### inventory_check_bill_list

查询盘点单列表（每张盘点单的仓库/日期/盘点状态）。

参数：`startDate` (string)、`endDate` (string)、`limit` (integer)

#### other_in_bill_list

查询其他入库单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### other_in_bill_preview

根据客户口述生成一张待确认的其他入库单草稿，不会真实变动库存。适用问法如“其他入库，1号仓入办公用品10个”“开一张其他入库单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | - | 供应商名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

#### other_out_bill_list

查询其他出库单列表。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`companyName` (string)、`limit` (integer)

#### other_out_bill_preview

根据客户口述生成一张待确认的其他出库单草稿，不会真实变动库存。适用问法如“其他出库，1号仓出办公用品5个”“开一张其他出库单”。生成草稿后必须等客户明确回复确认，再调用 psi_bill_commit 提交，客户确认前不要调用提交工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| raw_text | string | ✅ | 客户这句话的原文，用于后续数量与单价核验，必须原样传入，不要转述或改写 |
| partner_name | string | - | 客户名称 |
| warehouse_name | string | ✅ | 仓库名称 |
| biz_date | string | - | 单据日期，格式2026-09-01，不填默认今天 |
| remark | string | - | 备注 |
| items | array<object> | ✅ | 明细，至少一行 |

#### psi_available_inventory

查询可用库存：实际库存加上各类在途/待入、减去各类占用/待出后的可用数量，按存货+仓库维度展示。

参数：`endDate` (string)、`product_name` (string)、`warehouse_name` (string)、`limit` (integer)

#### psi_batch_inventory

按批次(批次号+生产日期+保质期)查询存货当前库存数量、成本与有效期至，只覆盖开通了批次/保质期管理的存货。

参数：`end` (string)、`product_name` (string)、`warehouse_name` (string)、`pc_num` (string)、`hide_zero` (boolean)、`show_all` (boolean)

#### psi_dead_stock

按用户给定的"无出库天数"标准，从当前库存快照里筛出候选呆滞料清单(距最近一次出库已超过/不到指定天数的存货，含从未出库过的存货)。

参数：`product_name` (string)、`warehouse_name` (string)、`min_no_outbound_days` (number)、`max_no_outbound_days` (number)、`show_all` (boolean)

#### psi_dead_stock_forecast

按存货近90天的消耗速度(日均出库量)，预测现有库存还能用多少天/多久后会滞销，适合回答【这批货多久会滞销】【现有库存还能撑多久】【哪些存货未来可能卖不动】【预计多久用不完的存货有哪些】等面向未来的预测问题。

参数：`product_name` (string)、`warehouse_name` (string)、`min_forecast_days` (number)、`max_forecast_days` (number)、`show_all` (boolean)

#### psi_dead_stock_report

呆滞料复合报告：一次问答整合呆滞判定明细+库龄结构分布两段快照，适合回答【给我一份呆滞料复合报告】【呆滞情况总体怎么样】【呆滞料整体分析】这类希望一次性看到呆滞料概貌的问题。

参数：`product_name` (string)、`warehouse_name` (string)、`dormant_days` (number)、`show_all` (boolean)

#### psi_expiry_warning

查询已进入保质期预警范围(含已过期)的批次清单，预警天数按存货自身配置(不是账套统一参数)，剩余天数为负代表已过期。

参数：`product_name` (string)、`warehouse_name` (string)、`pc_num` (string)、`min_remaining_days` (number)、`max_remaining_days` (number)、`show_all` (boolean)

#### psi_in_transit_overdue

在途超龄预警：从已下单未入库的采购订单里，按超过交货日期多久还没到货筛出候选超龄清单，适合回答【在途超龄预警】【哪些采购订单一直没到货】【在途超期的货有哪些】【有没有供应商一直拖着不发货】等问题。

参数：`product_name` (string)、`warehouse_name` (string)、`counterparty_name` (string)、`min_overdue_days` (number)、`max_overdue_days` (number)、`show_all` (boolean)

#### psi_inventory_aging

查询存货库龄分析：截止指定日期各存货/仓库的在库时长分档统计。

参数：`end` (string)、`show_all` (boolean)、`product_name` (string)、`warehouse_name` (string)、`min_age_days` (number)、`max_age_days` (number)

#### psi_inventory_status

查询库存状况：截止指定日期各仓库/存货的库存数量、单位成本均价、库存成本。

参数：`end` (string)、`show_all` (boolean)、`product_name` (string)、`warehouse_name` (string)、`order_by` (string)、`group_by` (string)、`min_cost` (number)、`max_cost` (number)、`min_qty` (number)、`max_qty` (number)

#### psi_inventory_warning

查询库存预警：截止当前日期哪些存货库存低于最低预警或高于最高预警。

参数：`end` (string)、`show_all` (boolean)、`product_name` (string)、`warehouse_name` (string)

#### psi_stock_movement

查询进销存出入库汇总/明细：mode=summary（默认）按存货+仓库统计期初结存、本期入库、本期出库、期末结存；mode=detail 输出某段时间逐笔出入库记录（数量/金额）。

参数：`startDate` (string)、`endDate` (string)、`mode` (string)、`product_name` (string)、`warehouse_name` (string)、`limit` (integer)、`order_by` (string)、`min_amount` (number)、`max_amount` (number)、`min_qty` (number)、`max_qty` (number)

#### psi_stock_movement_trend

按月统计存货出入库数量、金额走势，口径复刻出入库汇总表的本期入库/本期出库流量部分(不含期初/期末结存快照)。

参数：`startDate` (string)、`endDate` (string)

### 模块：资金管理

#### advance_receipt_payment_bill_list

查询预收款单/预付款单列表。

参数：`direction`* (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### cancel_bill_detail

按单号查询单个核销单的完整详情，含核销明细。

参数：`number`* (string)

#### cancel_bill_list

查询核销单列表，覆盖预收冲应收/预付冲应付/应收冲应付/应收转应收/应付转应付。

参数：`billKind` (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### expenditure_bill_list

查询其他支出单/其他收入单列表（一张张具体单据，含审批状态/记账状态）。

参数：`billKind` (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### psi_account_balance

查询账户余额表：资金模块收付款单对应的账户收支合计与余额（期初+净流水）。

参数：`startDate` (string)、`endDate` (string)、`limit` (integer)

#### psi_other_income_expense

查询其他支出单、其他收入单的往来明细，按单据日期倒序。

参数：`startDate` (string)、`endDate` (string)、`name` (string)、`limit` (integer)

#### psi_payable_summary

查询应付账款汇总（按供应商维度）：期初余额+本期发生额+本期已付金额+期末应付余额，含暂估调整/支出暂估调整等进销存核算口径（委外加工费用单口径暂已停用，恒不计入，同小丰现网行为）。

参数：`name` (string)、`start` (string)、`end` (string)、`limit` (integer)

#### psi_receipt_payment_overview

查询收付款一览，side 二选一：sale=销售收款一览表(销售出库单据的收款跟踪，含委托代销结算单)，purchase=采购付款一览表(采购入库单据的付款跟踪)。

参数：`startDate` (string)、`endDate` (string)、`side` (string)、`name` (string)、`limit` (integer)

#### psi_receipt_payment_trend

side="sale"(默认)对应销售收款趋势，side="purchase"对应采购付款趋势，按月统计价税合计、实际收/付款、退款走势，口径复刻现有收付款一览表(含委托代销结算单)。

参数：`startDate` (string)、`endDate` (string)、`side` (string)

#### psi_receivable_overdue_warning

查询超过指定天数仍未收清欠款的销售单据(应收超期预警)，超期天数由用户自定(默认30天)。

参数：`overdue_days` (integer)、`counterparty_name` (string)、`order_by` (string)、`min_amount` (number)、`max_amount` (number)、`show_all` (boolean)

#### psi_receivable_summary

查询应收账款汇总（按客户维度）：期初余额+本期发生额+本期已收金额+期末应收余额，含暂估调整/核销单转移等进销存核算口径。

参数：`name` (string)、`start` (string)、`end` (string)、`limit` (integer)

#### receipt_payment_bill_list

查询收款单/付款单列表（一张张具体单据，含单号/金额/审批状态）。

参数：`direction`* (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

## 生产与 MES

### 模块：生产管理

#### bom_list

查询 BOM（物料清单）列表，支持按编号/名称/关联产品的统一关键字模糊过滤（不支持组合过滤）。

参数：`keyword` (string)、`limit` (integer)

#### finished_bill_detail

按单号查询产成品入库单、产成品退库单、委外产成品入库单或委外产成品退货单的完整详情，含存货明细行。

参数：`number`* (string)

#### finished_bill_list

查询产成品出入库单据表（分页列表），必须指定单据类型四选一：生产产成品入库/生产产成品退库/委外产成品入库/委外产成品退货。

参数：`billKind`* (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### material_bill_detail

按单号查询生产领料单、生产退料单、委外发料单或委外退料单的完整详情，含存货明细行。

参数：`number`* (string)

#### material_bill_list

查询领退料单据表（分页列表），必须指定单据类型四选一：生产领料/生产退料/委外发料/委外退料。

参数：`billKind`* (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### mrp_plan_order_list

查询 MRP 运算产出的计划订单列表，支持按计划订单编号/状态（1已生成/2未生成）/时间范围过滤。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`status` (integer)、`limit` (integer)

#### process_bill_detail

按单号查询生产加工单或委外加工单的表头详情（单号/日期/车间/计划员/领料入库状态等）。

参数：`number`* (string)

#### process_bill_list

查询生产加工单/委外加工单单据表（分页列表），必须指定类型二选一：自制/委外。

参数：`billKind`* (string)、`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

#### production_process_track

查询生产加工单跟踪表：按单号/时间范围列出生产加工单的计划数、已领料数、已入库数等跟踪事实。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

### 模块：委外管理

#### outsource_cost_bill_detail

按单号查询委外加工费用单或委外加工退费单的完整详情（含加工费单价/加工费/税额/单据金额/已付未付金额）。

参数：`number`* (string)

#### outsource_cost_bill_list

查询委外加工费用/委外加工退费单据表（分页列表），必须指定单据类型二选一：加工费用/加工退费。

参数：`billKind`* (string)、`startDate` (string)、`endDate` (string)、`limit` (integer)

#### outsource_execution_detail

查询委外加工执行明细表：按加工单行项目（存货）粒度列出每个委外加工单的入库数量/材料成本/加工费/费用核销明细。

参数：`startDate` (string)、`endDate` (string)、`billNumber` (string)、`completeStatus` (integer)、`limit` (integer)

#### outsource_execution_summary

查询委外加工执行汇总表：按存货维度跨单据汇总委外加工的入库数量/材料成本/加工费/费用核销数据（不按单据展示）。

参数：`startDate` (string)、`endDate` (string)、`billNumber` (string)、`completeStatus` (integer)、`limit` (integer)

#### outsource_process_track

查询委外加工单跟踪表：按单号/时间范围列出委外加工单的计划数、已发料数、已入库数等跟踪事实。

参数：`startDate` (string)、`endDate` (string)、`number` (string)、`limit` (integer)

### 模块：MES 制造

#### delivery_risk

查询未来 7 天内将到期或已逾期的未完工工单，按计划完工日升序排列（最紧急在前）。

参数：`delivery_risk_days` (integer)

#### employee_performance

按工人维度统计综合绩效：报工产量/不良数/良品率联合工资总额并列展示（首期不加权，只并列不出综合分）。

参数：`startDate` (string)、`endDate` (string)、`good_rate_below` (number)、`good_rate_above` (number)

#### inspection_conclusion_summary

统计已结束检验单按检验结论（合格/不合格/让步接收/未判定）分组的数量分布，只统计已结束（Status=3）的检验单。

参数：`startDate` (string)、`endDate` (string)、`inspection_type` (integer)、`conclusion` (string)

#### inspection_item_fail_rank

按检验项统计不合格率排名，只统计已判定的检验记录（合格/不合格两种明确结论，未判定的文本/拍照类记录不计入分母）。

参数：`startDate` (string)、`endDate` (string)、`item_name` (string)

#### inspection_order_progress

按检验状态（未开始/进行中/已结束）分组统计检验单数量与完成率，完成率=已结束单数/本期全部检验单总数（不随下面的状态/类型筛选收窄）。

参数：`startDate` (string)、`endDate` (string)、`status` (string)、`inspection_type` (string)

#### inspection_pass_rate

按产品维度统计质检合格率（本月/指定时段），只统计已结束（Status=3）的检验单，合格率超过100%时按100%显示。

参数：`startDate` (string)、`endDate` (string)、`inspection_type` (string)、`pass_rate_below` (number)、`pass_rate_above` (number)

#### mes_defect_item_list

查询 MES 不良品项基础数据列表，支持按名称/编号模糊过滤。

参数：`name` (string)、`code` (string)、`limit` (integer)

#### mes_dispatch_list

查询 MES 派工记录列表，支持按工单号/工序名称/状态过滤。

参数：`orderNo` (string)、`processName` (string)、`status` (integer)、`limit` (integer)

#### mes_drawing_list

查询 MES 图纸列表，支持按编号/名称模糊关键字过滤。

参数：`keyword` (string)、`limit` (integer)

#### mes_inspection_detail

按检验单号查询单个检验单的完整详情，含各批次检验结果和检验项判定。

参数：`code`* (string)

#### mes_inspection_item_list

查询 MES 检验项基础数据列表，支持按名称/编号过滤。

参数：`name` (string)、`code` (string)、`limit` (integer)

#### mes_inspection_list

查询 MES 检验单列表，支持按单号/产品名称/检验时机（1首检/2巡检/3末检）/状态（1未开始/2进行中/3已结束）过滤。

参数：`code` (string)、`productName` (string)、`inspectionTiming` (integer)、`status` (integer)、`limit` (integer)

#### mes_inspection_spec_detail

按编号或名称查询单个检验规范的完整详情，含引用的检验项和标准值。

参数：`code`* (string)

#### mes_inspection_spec_list

查询 MES 检验规范列表，支持按名称/编号过滤。

参数：`name` (string)、`code` (string)、`limit` (integer)

#### mes_material_by_order

按工单号查询该工单的历次领料关联记录（领料单号/申请数量/时间）。

参数：`orderNo`* (string)、`processName` (string)

#### mes_order_detail

按工单号查询单个工单的完整详情，含工序进度明细。

参数：`code`* (string)

#### mes_order_list

查询 MES 工单列表（逐条列出），支持按工单号/产品名称/状态（0待排产/1已排产/2生产中/3已完工/4已关闭）/优先级（1普通/2紧急/3加急）过滤。

参数：`orderNo` (string)、`productName` (string)、`status` (integer)、`priority` (integer)、`limit` (integer)

#### mes_process_list

查询 MES 工序基础数据列表，支持按名称/编码过滤。

参数：`name` (string)、`code` (string)、`limit` (integer)

#### mes_report_detail

按工单号查询报工详情，可选按工序名称进一步定位到具体一条报工记录。

参数：`orderNo`* (string)、`processName` (string)

#### mes_report_list

查询 MES 报工记录列表，支持按工单号/工序名称/产品名称/时间范围过滤。

参数：`orderNo` (string)、`processName` (string)、`productName` (string)、`startDate` (string)、`endDate` (string)、`limit` (integer)

#### mes_route_detail

按编号或名称查询单条工艺路线的完整工序步骤详情。

参数：`code`* (string)

#### mes_route_list

查询 MES 工艺路线列表，支持按编号/名称过滤。

参数：`name` (string)、`code` (string)、`limit` (integer)

#### output_trend

查询产量趋势（按天/周/月粒度，良品产量或不良数），与产品产量排名(product_output_rank)同口径(均不做末道工序门禁)，两工具数字应互相对得上。

参数：`startDate` (string)、`endDate` (string)、`granularity` (string)、`metric` (string)、`group_by` (string)

#### piece_wage

按工人维度统计计件工资（默认本月，可指定时段）。

参数：`startDate` (string)、`endDate` (string)、`worker_name` (string)、`wage_above` (number)、`wage_below` (number)、`include_total` (boolean)

#### process_bottleneck

按工序维度分析产量/不良/工时，不良率降序、同不良率按产量升序（把高不良低产出的工序顶到最前，便于定位瓶颈工序）。

参数：`startDate` (string)、`endDate` (string)、`product_name` (string)、`workshop_name` (string)、`worker_name` (string)、`defect_rate_above` (number)、`defect_rate_below` (number)

#### product_defect_rate_rank

按产品维度统计不良率排名（本月/指定时段），分母为良品数+不良数(不含报废)，与工人不良率口径一致，HAVING 过滤零产出产品防小样本失真。

参数：`startDate` (string)、`endDate` (string)、`process_name` (string)、`workshop_name` (string)、`worker_name` (string)、`product_name` (string)、`defect_rate_above` (number)、`defect_rate_below` (number)

#### product_output_rank

按产品维度统计产量(良品数)排名（本月/指定时段），按报工合格数直排，不做末道工序门禁——与产量趋势(output_trend)同口径，两个工具的数字应互相对得上。

参数：`startDate` (string)、`endDate` (string)、`process_name` (string)、`workshop_name` (string)、`worker_name` (string)、`product_name` (string)、`output_above` (number)、`output_below` (number)

#### production_overview

生成生产经营简报：本期产量(良品/不良)+整体良品率、工单状态分布（实时快照）、交期风险工单数（未来7天内到期或已逾期的未完工工单，实时快照）。

参数：`startDate` (string)、`endDate` (string)

#### work_order_completion_rate

查询工单完成率明细，按完成率从低到高排列（最滞后的排在前面，方便发现进度落后的工单），同完成率再按计划完工日排序。

参数：`startDate` (string)、`endDate` (string)、`order_no` (string)、`status` (string)、`completion_rate_below` (number)、`completion_rate_above` (number)

#### work_order_on_time_rate

查询指定时段内已完工工单的准时交付率（实际完工日不晚于计划完工日视为准时）。

参数：`startDate` (string)、`endDate` (string)

#### work_order_status_count

查询各状态（待排产/已排产/生产中/已完工/已关闭）工单的数量分布。

参数：`startDate` (string)、`endDate` (string)、`workshop_name` (string)

#### work_order_stock_status

查询工单实时入库状态（未入库/部分入库/已全部入库），已入库数按关联入库单实时现算，不信工单快照字段。

参数：`startDate` (string)、`endDate` (string)、`stock_status` (string)、`stocked_qty_above` (number)、`stocked_qty_below` (number)

#### worker_defect_rate

按工人维度统计不良率排名（本月/指定时段），分母为良品数+不良数(不含报废)，不良率降序（问题最大的工人排最前）。

参数：`startDate` (string)、`endDate` (string)、`product_name` (string)、`process_name` (string)、`workshop_name` (string)、`worker_name` (string)、`defect_rate_above` (number)、`defect_rate_below` (number)

#### worker_good_rate_rank

按工人维度统计良品率排名（本月/指定时段），分母为良品数+不良数(不含报废)。

参数：`startDate` (string)、`endDate` (string)、`product_name` (string)、`process_name` (string)、`workshop_name` (string)、`worker_name` (string)、`good_rate_above` (number)、`good_rate_below` (number)、`include_total` (boolean)

#### worker_output_rank

按工人维度统计产量(良品数)排名（本月/指定时段）。

参数：`startDate` (string)、`endDate` (string)、`product_name` (string)、`process_name` (string)、`workshop_name` (string)、`worker_name` (string)、`output_above` (number)、`output_below` (number)、`include_total` (boolean)

#### workshop_output_rank

按车间维度统计产量(良品数)排名（本月/指定时段）。

参数：`startDate` (string)、`endDate` (string)、`product_name` (string)、`process_name` (string)、`worker_name` (string)、`workshop_name` (string)、`output_above` (number)、`output_below` (number)

## 注意事项

- 首次使用需在浏览器完成账三丰登录（微信扫码或账号密码）并选择企业；授权失效时 WorkBuddy 会重新打开授权页
- 首版仅支持账三丰 ERP 线客户；代账版客户登录后会看到提示，暂不可用
- 客户要切换账号时，请在 WorkBuddy 中删除本连接器后重新添加（"断开重连"清不掉客户端本地授权状态）
- 如需取消授权，在 WorkBuddy 中移除连接器即可
