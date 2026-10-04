# 七色米 ERP MCP 工具目录

本目录从运行时 `src/main/resources/erp-tools.json` 派生，共 95 个工具。它用于工具发现和风险判断；参数名称、类型、枚举、默认值与完整约束以 WorkBuddy 当前展示的 MCP 工具输入 Schema 为准。

所有业务参数都直接放在工具参数顶层。认证凭据不得作为工具参数传递。

## Account

### `qisemi_account_query_account_list`

- 标题：查询结算账户列表
- 用途：获取结算账户列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_account_query_default_account`

- 标题：查询默认结算账户信息
- 用途：查询默认结算账户信息 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Assembly

### `qisemi_assembly_detail`

- 标题：组装拆卸单详情
- 用途：组装拆卸单详情 只读操作。
- 顶层必填参数：`AssemblyId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_assembly_query_page_list`

- 标题：查询组装拆卸单列表分页
- 用途：查询组装拆卸单列表分页 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## BasicContact

### `qisemi_basic_contact_query_information`

- 标题：查询企业资料信息
- 用途：查询企业资料信息 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## BillNo

### `qisemi_bill_no_query_bill_no_by_type`

- 标题：获取单据编号
- 用途：获取单据编号 只读操作。
- 顶层必填参数：`Type`、`SetType`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_bill_no_query_bill_no_detail`

- 标题：查询单号规则详情
- 用途：查询单号规则详情 只读操作。
- 顶层必填参数：`SetType`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Branch

### `qisemi_branch_query_branch_by_id`

- 标题：按照主键查询门店信息
- 用途：按照主键查询门店信息 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_branch_query_branch_list`

- 标题：获取门店列表
- 用途：获取门店列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Buy

### `qisemi_buy_query_buy_by_id`

- 标题：查询进货单详细
- 用途：查询进货单详细 只读操作。 业务路由（必须遵守）：本工具处理“进货单/采购单”；匹配词：“进货单”、“采购单”；排除词：“进货订单”、“采购订单”、“进货预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`BuyId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_buy_query_buy_list`

- 标题：分页查询进货信息
- 用途：分页查询进货信息 只读操作。 业务路由（必须遵守）：本工具处理“进货单/采购单”；匹配词：“进货单”、“采购单”；排除词：“进货订单”、“采购订单”、“进货预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。用户查询最近/最新一笔或列表且未提供单据 ID 时，优先使用本工具。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## BuyOrder

### `qisemi_buy_order_query_buy_order_by_id`

- 标题：查询进货预订详细
- 用途：查询进货预订详细 只读操作。 业务路由（必须遵守）：本工具处理“进货订单/采购订单/进货预订”；匹配词：“进货订单”、“采购订单”、“进货预订”；排除词：“进货单”、“采购单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`BuyId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_buy_order_query_buy_order_list`

- 标题：查询进货预订列表
- 用途：查询进货预订列表 只读操作。 业务路由（必须遵守）：本工具处理“进货订单/采购订单/进货预订”；匹配词：“进货订单”、“采购订单”、“进货预订”；排除词：“进货单”、“采购单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。用户查询最近/最新一笔或列表且未提供单据 ID 时，优先使用本工具。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## BuyReturn

### `qisemi_buy_return_query_buy_return_by_id`

- 标题：查询进货退货单详细
- 用途：查询进货退货单详细 只读操作。
- 顶层必填参数：`ReturnId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_buy_return_query_buy_return_list`

- 标题：查询进货退货列表
- 用途：查询进货退货列表 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Client

### `qisemi_client_query_client`

- 标题：分页查询客户信息
- 用途：分页查询客户信息 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_client_query_client_by_id`

- 标题：查询商品详情通过ID
- 用途：查询商品详情通过ID 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## ClientRankPrice

### `qisemi_client_rank_price_select_create_product`

- 标题：供客户等级价使用，获取创建商品数量
- 用途：供客户等级价使用，获取创建商品数量 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## DeliveryOrder

### `qisemi_delivery_order_query_delivery_order_by_id`

- 标题：查询配送单详细
- 用途：查询配送单详细 只读操作。
- 顶层必填参数：`OrderId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_delivery_order_query_delivery_orders`

- 标题：查询配送列表分页
- 用途：查询配送列表分页 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Employee

### `qisemi_employee_query_employee`

- 标题：经手人列表查询
- 用途：经手人列表查询 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_employee_query_user_warehouse_ids`

- 标题：获取员工关联仓库，返回字符串用分号分割
- 用途：获取员工关联仓库，返回字符串用分号分割 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## FundsFlow

### `qisemi_funds_flow_get_has_warehouse_perm`

- 标题：查询当前用户是否拥有仓库权限
- 用途：GetHasWarehousePerm 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_funds_flow_query_funds_flow_list`

- 标题：查询资金流水列表
- 用途：QueryFoundsFlowList 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## IncomeAndPay

### `qisemi_income_and_pay_query_in_come_and_pay_by_id`

- 标题：查询日常收支单详情
- 用途：queryInComeAndPayById 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_income_and_pay_query_income_and_pay`

- 标题：查询日常收支单列表
- 用途：queryIncomeAndPay 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## InstallOrder

### `qisemi_install_order_query_install_order_by_id`

- 标题：查询安装单详细
- 用途：查询安装单详细 只读操作。
- 顶层必填参数：`OrderId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_install_order_query_install_orders`

- 标题：查询销售列表分页
- 用途：查询销售列表分页 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## InventoryReport

### `qisemi_inventory_report_inventory`

- 标题：商品库存
- 用途：商品库存 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_inventory_report_query_cost_detail`

- 标题：查询成本明细分页
- 用途：查询成本明细分页 只读操作。
- 顶层必填参数：`Page`、`Rp`、`ProductId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_inventory_report_query_negative_cost_list`

- 标题：查询成本异常商品列表
- 用途：查询成本异常商品列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## IO

### `qisemi_io_query_ioin_detail`

- 标题：入库单详细
- 用途：入库单详细 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_io_query_ioin_list`

- 标题：入库历史
- 用途：入库历史 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_io_query_ioout_detail`

- 标题：出库单详细
- 用途：出库单详细 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_io_query_ioout_list`

- 标题：出库单历史
- 用途：出库单历史 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Lend

### `qisemi_lend_query_detail_by_id`

- 标题：查询借入借出单详情
- 用途：查询借入借出单详情 只读操作。
- 顶层必填参数：`LendType`、`LendId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_lend_query_lend_list`

- 标题：分页查询借入借出单
- 用途：分页查询借入借出单 只读操作。
- 顶层必填参数：`Page`、`Rp`、`LendType`、`IsShowWriteBack`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_lend_query_turn_buy_or_sale_detail`

- 标题：查询借入借出单转销售/转进货（新增销售单/进货单使用），从借入借出单中查询转进货/转销售
- 用途：查询借入借出单转销售/转进货（新增销售单/进货单使用），从借入借出单中查询转进货/转销售 只读操作。
- 顶层必填参数：`LendId`、`BranchId`、`LendType`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## LendReturn

### `qisemi_lend_return_query_detail_by_id`

- 标题：查询借入借出归还单详情
- 用途：查询借入借出归还单详情 只读操作。
- 顶层必填参数：`ReturnId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_lend_return_query_init_detail`

- 标题：查询新增借入借出单页面数据，从借入借出单中查询未归还数据
- 用途：查询新增借入借出单页面数据，从借入借出单中查询未归还数据 只读操作。
- 顶层必填参数：`LendId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## ProductMainInfo

### `qisemi_product_main_info_detail_main_product_sn_list`

- 标题：查询主商品库存序列号信息
- 用途：查询主商品库存序列号信息 只读操作。
- 顶层必填参数：`ProductId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_detail_product_sn_list`

- 标题：查询商品库存序列号信息(传入的是单品productId返回单品对应的商品的所有序列号信息)
- 用途：查询商品库存序列号信息(传入的是单品productId返回单品对应的商品的所有序列号信息) 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_get_online_product_info`

- 标题：网店商品详情（多属性）
- 用途：网店商品详情（多属性） 只读操作。
- 顶层必填参数：`ProductId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_get_product_price_list`

- 标题：获取商品价格列表
- 用途：获取商品价格列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_is_property_ref_with_business`

- 标题：校验商品有无被业务单据、特价、套餐、商品模板、客户可见商品、业绩提成方案引用
- 用途：校验商品有无被业务单据、特价、套餐、商品模板、客户可见商品、业绩提成方案引用 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_is_ref_with_product`

- 标题：校验商品有无被业务单据、特价、套餐、商品模板、客户可见商品、业绩提成方案引用
- 用途：校验商品有无被业务单据、特价、套餐、商品模板、客户可见商品、业绩提成方案引用 只读操作。
- 顶层必填参数：`ProductId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_online_product_list`

- 标题：查询网店主商品列表
- 用途：查询网店主商品列表 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_product`

- 标题：商品列表
- 用途：商品列表 只读操作。
- 顶层必填参数：`Rp`、`Page`、`QueryListType`、`IsShowZeroStock`、`CustomFieldList`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_product_by_code`

- 标题：扫码录入查询商品（无优先级）
- 用途：扫码录入查询商品（无优先级） 只读操作。
- 顶层必填参数：`SearchKey`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_product_by_id`

- 标题：获取商品详细
- 用途：获取商品详细 只读操作。
- 顶层必填参数：`ProductId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_product_by_serial_no`

- 标题：维修单开单扫码序列号选择商品
- 用途：维修单开单扫码序列号选择商品 只读操作。
- 顶层必填参数：`SearchKey`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_product_pt_detail_records`

- 标题：获取商品套餐，模板id集合
- 用途：获取商品套餐，模板id集合 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_update_price_by_id`

- 标题：查询快捷改价商品详情
- 用途：查询快捷改价商品详情 只读操作。
- 顶层必填参数：`ProductId`、`UnitId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_main_info_query_update_price_list`

- 标题：查询快捷改价数据列表
- 用途：查询快捷改价数据列表 只读操作。
- 顶层必填参数：`Page`、`Rp`、`CustomFieldList`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## ProductProperty

### `qisemi_product_property_query_all_property`

- 标题：查询所有商品属性[property1-property5]（带分组及属性值）
- 用途：查询所有商品属性[property1-property5]（带分组及属性值） 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_property_query_common_property`

- 标题：获取所有属性
- 用途：获取所有属性 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_property_query_property_by_name`

- 标题：查询商品属性（带分组及属性值）不分页
- 用途：查询商品属性（带分组及属性值）不分页 只读操作。
- 顶层必填参数：`PropertyName`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_product_property_query_property_text_by_property_name`

- 标题：查询指定属性下的所有属性值分组和属性值分组下面的属性值(支持属性值分组下的属性值分组) 支持分页
- 用途：查询指定属性下的所有属性值分组和属性值分组下面的属性值(支持属性值分组下的属性值分组) 支持分页 只读操作。
- 顶层必填参数：`PropertyName`、`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Project

### `qisemi_project_query_project`

- 标题：查询收支项目列表
- 用途：查询收支项目列表 只读操作。
- 顶层必填参数：`Rp`、`Page`、`SearchProjectType`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## ReceiveAndPay

### `qisemi_receive_and_pay_add_pay`

- 标题：新增付款单
- 用途：新增一张单账户付款单。MCP 服务端固定为供应商付款类型，不支持多账户、核销和图片附件；付款单号由 ERP 后端自动生成。 高风险操作，调用时必须显式传入 confirm=true。
- 顶层必填参数：`BranchId`、`BusiDate`、`BusiUser`、`CSId`、`CSName`、`AccountId`、`AccountName`、`amtpayment`、`amtcurpayment`
- 访问等级：写入（高风险）
- 确认规则：调用前取得用户明确确认，并在工具参数顶层传入 `confirm: true`。

### `qisemi_receive_and_pay_add_receive`

- 标题：新增收款单
- 用途：新增一张单账户收款单。MCP 服务端固定为客户收款类型，不支持多账户、核销和图片附件；收款单号由 ERP 后端自动生成。 高风险操作，调用时必须显式传入 confirm=true。
- 顶层必填参数：`BranchId`、`BusiDate`、`BusiUser`、`CSId`、`CSName`、`AccountId`、`AccountName`、`amtpayment`、`amtcurpayment`
- 访问等级：写入（高风险）
- 确认规则：调用前取得用户明确确认，并在工具参数顶层传入 `confirm: true`。

## RepairOrder

### `qisemi_repair_order_get_last_service_type`

- 标题：查询上一单服务方式
- 用途：查询上一单服务方式 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_repair_order_query_last_order_by_ps`

- 标题：查询商品序列号历史最近维修记录
- 用途：查询商品序列号历史最近维修记录 只读操作。
- 顶层必填参数：`ProductId`、`SerialNo`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_repair_order_query_repair_order_by_id`

- 标题：查询维修单详细
- 用途：查询维修单详细 只读操作。
- 顶层必填参数：`OrderId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_repair_order_query_repair_orders`

- 标题：查询维修列表分页
- 用途：查询维修列表分页 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Sale

### `qisemi_sale_query_sale_by_id`

- 标题：查询销售单详细
- 用途：查询销售单详细 只读操作。 业务路由（必须遵守）：本工具处理“销售单”；匹配词：“销售单”；排除词：“销售订单”、“销售预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`SaleId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_query_sale_details`

- 标题：定制用户查询销售明细列表分页
- 用途：定制用户查询销售明细列表分页 只读操作。 业务路由（必须遵守）：本工具处理“销售单”；匹配词：“销售单”；排除词：“销售订单”、“销售预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`Page`、`Rp`、`DeductX`、`DeductY`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_query_sales`

- 标题：查询销售列表分页
- 用途：查询销售列表分页 只读操作。 业务路由（必须遵守）：本工具处理“销售单”；匹配词：“销售单”；排除词：“销售订单”、“销售预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。用户查询最近/最新一笔或列表且未提供单据 ID 时，优先使用本工具。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_save_sale`

- 标题：新增销售单
- 用途：新增销售单 高风险操作，调用时必须显式传入 confirm=true。 业务路由（必须遵守）：本工具处理“销售单”；匹配词：“销售单”；排除词：“销售订单”、“销售预订”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`AccountId`、`BranchId`、`BillType`、`ClientName`、`DeliveryType`、`DiscountType`、`DisCountAmt`、`IsGenDeliveryOrder`、`InvoiceState`、`IsOpenTaxRate`、`IsMultiWarehouse`、`IsMultiAccount`、`FAReceAmt`、`PayType`、`ReceAmt`、`SaleNo`、`SaleDate`、`SaleAmt`、`SaleUser`、`TaxAmt`、`WarehouseId`、`WarehouseIdStr`
- 访问等级：写入（高风险）
- 确认规则：调用前取得用户明确确认，并在工具参数顶层传入 `confirm: true`。

## SaleExchange

### `qisemi_sale_exchange_query_sale_exchange_by_id`

- 标题：查询销售换货单详细
- 用途：查询销售换货单详细 只读操作。
- 顶层必填参数：`ExchangeId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_exchange_query_sale_exchange_list`

- 标题：销售换货单列表分页查询
- 用途：销售换货单列表分页查询 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## SaleOrder

### `qisemi_sale_order_query_order_detail_by_order_no`

- 标题：查询商户应用市场订单
- 用途：查询商户应用市场订单 只读操作。 业务路由（必须遵守）：本工具处理“销售订单/销售预订”；匹配词：“销售订单”、“销售预订”；排除词：“销售单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`OrderNo`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_order_query_page_by_product_name`

- 标题：查询商户应用市场订单
- 用途：查询商户应用市场订单 只读操作。 业务路由（必须遵守）：本工具处理“销售订单/销售预订”；匹配词：“销售订单”、“销售预订”；排除词：“销售单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_order_query_sale_order_by_id`

- 标题：查询销售预订详情
- 用途：查询销售预订详情 只读操作。 业务路由（必须遵守）：本工具处理“销售订单/销售预订”；匹配词：“销售订单”、“销售预订”；排除词：“销售单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_order_query_sale_order_list`

- 标题：查询销售预订列表
- 用途：查询销售预订列表 只读操作。 业务路由（必须遵守）：本工具处理“销售订单/销售预订”；匹配词：“销售订单”、“销售预订”；排除词：“销售单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。用户查询最近/最新一笔或列表且未提供单据 ID 时，优先使用本工具。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_order_query_un_turn_sale_detail_list`

- 标题：查询销售预订缺货表
- 用途：查询销售预订缺货表 只读操作。 业务路由（必须遵守）：本工具处理“销售订单/销售预订”；匹配词：“销售订单”、“销售预订”；排除词：“销售单”。用户使用排除词时禁止调用本工具。用户只说“订单”且未明确业务类型时，禁止调用并先询问。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## SaleReturn

### `qisemi_sale_return_query_sale_return_by_id`

- 标题：查询销售退货详情
- 用途：根据销售退货单ID查询主单、附件、商品明细、单位、序列号及套餐组成等完整信息。 只读操作。
- 顶层必填参数：`ReturnId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sale_return_query_sale_return_list`

- 标题：查询销售退货列表
- 用途：分页查询销售退货单，支持模糊搜索、高级筛选、分页合计，以及上一单/下一单场景的单据ID查询。 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## SalesMan

### `qisemi_sales_man_get_sales_man_by_user_name`

- 标题：根据导购员名称判断导购员是否存在
- 用途：根据导购员名称判断导购员是否存在 只读操作。
- 顶层必填参数：`UserName`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_sales_man_query_page_list`

- 标题：查询导购员列表分页
- 用途：查询导购员列表分页 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## SaleType

### `qisemi_sale_type_query_sale_type_list`

- 标题：查询销售类型列表
- 用途：查询销售类型列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Supplier

### `qisemi_supplier_query_supplier`

- 标题：分页查询供应商信息
- 用途：分页查询供应商信息 只读操作。
- 顶层必填参数：`Page`、`Rp`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_supplier_query_supplier_by_id`

- 标题：根据ID查询供应商
- 用途：querySupplierById 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_supplier_query_supplier_by_name`

- 标题：根据供应商名称查询供应商是否存在
- 用途：根据供应商名称查询供应商是否存在 只读操作。
- 顶层必填参数：`SupplierName`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Transfer

### `qisemi_transfer_query_transfer_by_id`

- 标题：调拨详细
- 用途：调拨详细 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_transfer_query_transfer_list`

- 标题：调拨列表
- 用途：调拨列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Warehouse

### `qisemi_warehouse_query_relation_warehouse_by_user`

- 标题：获取当前登录用户关联仓库
- 用途：获取当前登录用户关联仓库 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warehouse_query_warehouse_by_id`

- 标题：获取仓库/车仓详细信息
- 用途：获取仓库/车仓详细信息 只读操作。
- 顶层必填参数：`WarehouseId`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warehouse_query_warehouse_list`

- 标题：查询仓库列表
- 用途：queryWarehouseList 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warehouse_query_warehouse_lock_state`

- 标题：查询仓库锁定状态
- 用途：查询仓库锁定状态 只读操作。
- 顶层必填参数：`WarehouseList`
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

## Warning

### `qisemi_warning_get_warning_info`

- 标题：查询预警信息
- 用途：autoCompleteSaleReceAmt 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warning_has_warning_info`

- 标题：商户是否有预警信息
- 用途：商户是否有预警信息 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warning_query_low_sale_list`

- 标题：获取低价销售列表
- 用途：获取低价销售列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warning_query_product_warehouse`

- 标题：查询商品仓库异常列表
- 用途：查询商品仓库异常列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

### `qisemi_warning_query_stock_warning_list`

- 标题：获取预警商品列表
- 用途：获取预警商品列表 只读操作。
- 顶层必填参数：无
- 访问等级：只读
- 确认规则：只读调用，无需写入确认。

