# 表结构速查

## 表 1：`e000.dt_store_view` — 门店主数据（精简视图）

| 属性 | 说明 |
:|------|------|
| **规模** | 268,125 家门店 |
| **主键** | `store_code` |
| **关键字段** | `store_code`, `group_code`, `cy_store_code`, `cy_group_code`（**视图仅含 4 字段**） |

### 字段说明

| 字段名 | 类型 | 中文名 | 用途 | 对应 SQL 占位符 |
|--------|------|--------|------|---------------|
| `store_code` | varchar | 门店 C 号 | **商龙云统一门店编码**（如 C273353），与所有业务表 `store_code` 互通 | `#{omShopCodes}` |
| `group_code` | varchar | 集团 G 号 | **商龙云统一集团编码**（如 G137427），与所有业务表 `group_code` 互通 | `#{SL_UNIFIED_G_ID}` |
| `cy_store_code` | varchar | 餐饮门店编号 | 历史/对账用途 | — |
| `cy_group_code` | varchar | 餐饮集团编号 | 历史/对账用途 | — |

> 💡 **占位符注入机制**：SQL 模板中用 `#{变量名}` 占位符，系统在执行前自动插入真实值。例如 `WHERE group_code = '#{SL_UNIFIED_G_ID}'` → 实际执行时变为 `WHERE group_code = 'G137427'`。AI **不得**在 SQL 模板中硬编码具体值。

> ✅ **关键说明**：`e000.dt_store_view` 是精简视图，**仅 4 字段**。所有 `region` / `province` / `city` / `manage_type` / `brand_name` / `area` / `capacity` / `emp_num` / `is_open` / `is_enable` / `delflg` / `do_id` / `do_name` / `dm_id` / `dm_name` / `shop_label_id` / `shop_label_name` / `close_shop_date` / `open_shop_date` 等维度字段**已不在视图中暴露**。如需这些维度，应通过 JOIN 业务表（`dm.v_pos_corp_sale_analysis_with_sly` / `dm.v_item_sale_analysis_with_sly`）获取。业务表中 `region` / `province` / `city` / `manage_type` 字段可直接使用。

### 关联方式

```sql
-- 7 张表均通过 group_code + store_code 直接 JOIN
FROM e000.dt_store_view s
JOIN dm.v_pos_corp_sale_analysis_with_sly p
  ON p.group_code = s.group_code
 AND p.store_code = s.store_code
WHERE s.group_code = '#{SL_UNIFIED_G_ID}'
  AND s.store_code IN (#{omShopCodes})
```

---

## 表 2：`dm.v_pos_corp_sale_analysis_with_sly` — 营业明细（视图）

| 属性 | 说明 |
:|------|------|
| **规模** | 40亿+ 条 |
| **主键** | `id` |
| **类型** | 视图（VIEW） |

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 门店主数据 | `group_code` + `store_code` | `e000.dt_store_view.group_code` + `store_code` | 获取门店基础信息 |
| 菜品销售 | `group_code` + `store_code` | `dm.v_item_sale_analysis_with_sly.group_code` + `store_code` | 同编码体系直接关联 |
| 会员日汇总 | `group_code` + `store_code` | `dm.dm_crm_card_sum_day_p_store.group_code` + `store_code` | 跨业务关联 |
| SCM 耗用 | `group_code` + `store_code` | `dm.dm_ljc_scm8_..._view.group_code` + `store_code` | 毛利率/采购占销比 |

### 关键字段

| 字段分类 | 字段名 | 说明 |
|----------|--------|------|
| **关联字段** | `group_code` | 集团编码（商龙云G号，必填过滤，对应 `SL_UNIFIED_G_ID`） |
| | `store_code` | 门店编码（商龙云C号，对应 `omShopCodes`） |
| | `settle_biz_date` | 营业日期（北京时间） |
| **金额字段** | `recv_money` | 营业应收（账单原价） |
| | `busi_income` | 实收金额（扣除优惠） |
| | `real_income` | 纯收金额（再减杂项） |
| **数量字段** | `bill_count` | 账单数 |
| | `people_qty` | 用餐人数 |
| | `open_table_count` | 开台数（仅堂食） |
| **分类字段** | `sale_type_name` | 销售渠道：堂食/外卖/外带/自提 |
| | `dining_type_name` | 用餐场景：普通就餐/亲友聚餐/商务宴请/婚宴/家庭就餐 |
| | `order_source_name` | 订单来源：自来客/微信/支付宝/美团外卖 |
| | `table_settle_shift_name` | 时段：早市/午市/晚市/宵夜 |
| **优惠字段** | `disc_money_total` | 优惠总金额 |
| | `item_member_money` | 会员价优惠 |
| | `item_promote_money` | 促销优惠 |
| | `item_present_money` | 赠送金额 |
| | `item_disc_money` | 折扣金额 |
| | `asitem_fix_money` | 定额优惠 |
| | `item_wipe_money` | 抹零金额 |
| **费用字段** | `service_free` | 服务费 |
| | `low_consume_polish_free` | 最低消费补齐 |
| **品项字段** | `item_orig_money` | 品项原价（理论销售额） |
| **其他字段** | `region` | 大区 |
| | `province` | 省份 |
| | `city` | 城市 |
| | `manage_type` | 管理类型：直营/加盟/托管/合作 |

---

## 表 3：`dm.dm_crm_card_sum_day_p_store` — 会员每日汇总（新表）

> ⚠️ **默认取数口径**：统计消费、储值、积分、用券等数据时，**默认取交易门店的数据**。
> 如需按"注册门店"或"售卡门店"统计，需主动询问用户并调整查询条件。

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 门店主数据 | `group_code` + `store_code` | `e000.dt_store_view.group_code` + `store_code` | 获取门店基础信息 |
| 营业明细 | `group_code` + `store_code` | `dm.v_pos_corp_sale_analysis_with_sly.group_code` + `store_code` | 跨业务关联 |
| 菜品销售 | `group_code` + `store_code` | `dm.v_item_sale_analysis_with_sly.group_code` + `store_code` | 跨业务关联 |
| 会员维表 | `group_code` + `store_code` + `mem_code` | `dm.v_crm_member_with_sly.group_code` + `store_code` + `mem_code` | 会员身份关联 |
| 会员卡明细 | `group_code` + `store_code` + `mem_card_no` | `dw.dwd_crm_member_card_p_with_sly.group_code` + `store_code` + `card_no` | 卡维度关联 |
| SCM 耗用 | `group_code` + `store_code` | `dm.dm_ljc_scm8_..._view.group_code` + `store_code` | 跨业务关联 |

### 门店字段含义对照

| 字段 | 含义 | 用途 |
|------|------|------|
| `store_code` | **交易门店**的商龙云门店号 | ✅ **默认取此字段** |
| `saled_shop_code` | 会员卡**售卡**云端门店号 | 需用户明确要求时使用 |
| `o2o_store_code` | 交易**云端**门店号 | 需用户明确要求时使用 |
| `mem_store_code` | 会员**注册**门店 | 需用户明确要求时使用 |

### 字段分类

| 字段分类 | 字段名 | 说明 |
|----------|--------|------|
| **日期字段** | `coupon_date` | 营业日期（按天汇总的维度字段，格式 YYYY-MM-DD）。⚠️ 本表日期字段不叫 `biz_date`/`settle_biz_date`/`stat_date`，必须使用 `coupon_date` |
| **关联字段** | `mem_code` | 会员编码（主键） |
| | `mem_card_no` | 会员卡号 |
| | `group_code` / `store_code` | 商龙云集团/门店编码（**交易门店**，统一 G/C 号） |
| **会员属性** | `mem_sex` | 性别 |
| | `mem_age` | 年龄 |
| | `is_new` | 是否新会员 |
| **消费字段** | `consume_count` | 消费笔数 |
| | `recv_money` | 营业应收 |
| | `busi_income` | 实收金额 |
| | `real_income` | 纯收金额 |
| **储值字段** | `recharge_count` | 储值笔数 |
| | `recharge_amount` | 储值金额 |
| | `recharge_real_amount` | 实收储值金额 |
| | `recharge_donate_amount` | 储值赠送金额 |
| **积分字段** | `score_in_num` | 积分获取金额 |
| | `score_out_num` | 积分消耗金额 |
| | `score_in_count` | 积分获取笔数 |
| | `score_out_count` | 积分消耗笔数 |
| **用券字段** | `use_num` | 用券张数 |
| | `coupon_income` | 优惠券收入 |
| | `coupon_real_income` | 优惠券实收 |
| **券发放字段** | `send_num` | 优惠券发放数 |
| | `used_num` | 已使用数 |
| | `invalid_num` | 已失效数 |
| | `overdue_num` | 已过期数 |
| | `available_num` | 可用数 |

---

## 表 4：`dm.v_crm_member_with_sly` — 会员维表（视图）

> 会员静态信息视图，统一使用 `group_code` + `store_code` 与其他业务表关联。

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 门店主数据 | `group_code` + `store_code` | `e000.dt_store_view.group_code` + `store_code` | 获取门店基础信息 |
| 会员日汇总 | `group_code` + `store_code` + `mem_code` | `dm.dm_crm_card_sum_day_p_store.group_code` + `store_code` + `mem_code` | 会员维度关联 |
| 会员卡明细 | `group_code` + `store_code` + `mem_code` | `dw.dwd_crm_member_card_p_with_sly.group_code` + `store_code` + `member_id` | 通过 member_id 关联 |

| 字段分类 | 字段名 | 说明 |
|----------|--------|------|
| **关联字段** | `mem_code` | 会员编码 |
| | `group_code` / `store_code` | 商龙云集团/门店编码（统一 G/C 号） |
| **会员属性** | `mem_name` | 姓名 |
| | `mem_mobile` | 手机号 |
| | `mem_sex` | 性别 |
| | `mem_birthday` | 生日 |
| | `mem_province` / `mem_city` / `mem_county` | 地区 |
| | `mem_card_type` | 会员卡类型 |
| | `mem_status` | 状态 |
| **行为字段** | `first_consume_time` | 首次消费时间 |
| | `last_consume_time` | 上次消费时间 |
| | `first_recharge_time` | 首次储值时间 |
| | `last_recharge_time` | 上次储值时间 |
| **余额字段** | `balance_principal` | 储值本金余额 |
| | `balance_gift` | 储值赠送余额 |
| | `balance_score` | 积分余额 |

---

## 表 5：`dw.dwd_crm_member_card_p_with_sly` — 会员卡明细表

> 会员卡详细信息，通过以下方式关联其他表：

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 会员日汇总 | `group_code` + `store_code` + `card_no` | `dm.dm_crm_card_sum_day_p_store.group_code` + `store_code` + `mem_card_no` | 卡号维度关联 |
| 会员维表 | `group_code` + `store_code` + `member_id` | `dm.v_crm_member_with_sly.group_code` + `store_code` + `mem_code` | 会员身份关联 |

### 关键字段

| 字段分类 | 字段名 | 说明 |
|----------|--------|------|
| **关联字段** | `member_id` | 会员ID |
| | `card_id` | 卡ID（主键） |
| | `card_no` | 会员卡号 |
| | `group_code` | 商龙云集团编码（G号） |
| **开卡信息** | `open_shop_id` / `open_shop_name` | 开卡门店ID/名称 |
| | `saled_shop_id` / `saled_shop_name` | 售卡门店ID/名称 |
| **卡状态** | `card_status` / `card_status_name` | 卡状态（101=已售卡） |
| | `card_type_name` | 卡类型名称 |
| **余额字段** | `balance_principal` | 本金余额 |
| | `balance_gift` | 赠送余额 |
| | `balance_point` | 积分余额 |
| | `balance_cashback` | 返现余额 |
| **渠道绑定** | `bindings` | 会员渠道绑定 JSON 串。格式：`{mp:gh_xxx|code:openid|type:1}`<br>**type 枚举**：1=微信、2=大众点评、3=支付宝、6=企业微信<br>可解析 `type` 字段分析会员注册渠道分布 |

---

## 表 6：`dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view` — SCM8 原物料耗用视图

> 供应链进销存日粒度视图，覆盖采购入库、实际耗用、理论耗用、库存、盘点差异等全链条。

| 属性 | 说明 |
|------|------|
| **规模** | 2.7亿+ 行 |
| **粒度** | 日 × 集团 × 门店 × 原料 |
| **关键字段** | `group_code`, `store_code`, `biz_date`, `rm_item_id` |

### ✅ SCM8 统一编码（与其他 6 张表一致）

> SCM8 视图已统一 `group_code`（集团 G 号）+ `store_code`（门店 C 号），**与其他 6 张业务表完全互通**，`#{变量名}` 占位符直接使用：

| `#{变量名}` 占位符 | 本表字段 | 说明 | 示例值 |
|-----------|---------|------|--------|
| `#{SL_UNIFIED_G_ID}` | `group_code` | 商龙云集团编码（G号） | `G137427` |
| `#{omShopCodes}` | `store_code` | 商龙云门店编码（C号） | `'C273353','C273354',...` |

```sql
-- SCM8 WHERE 过滤示例
WHERE group_code = '#{SL_UNIFIED_G_ID}'
  AND store_code IN (#{omShopCodes})
```

### ⚠️ 取数约定

| 字段类型 | 取数方式 | 说明 |
|---------|---------|------|
| **期初/期末库存** | **点取**（单日 biz_date） | 禁止 SUM。期初取月初第一天，期末取月最后一天 |
| **流量字段**（采购/耗用/报损等） | 可 SUM | 日粒度加总 |

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 营业明细 | `group_code` + `store_code` | `dm.v_pos_corp_sale_analysis_with_sly.group_code` + `store_code` | 毛利率/采购占销比 |
| 菜品销售 | `group_code` + `store_code` | `dm.v_item_sale_analysis_with_sly.group_code` + `store_code` | 跨业务关联 |
| 会员日汇总 | `group_code` + `store_code` | `dm.dm_crm_card_sum_day_p_store.group_code` + `store_code` | 跨业务关联 |
| 门店主数据 | `group_code` + `store_code` | `e000.dt_store_view.group_code` + `store_code` | 直接 JOIN 获取门店信息 |

### 字段分类

#### 关联字段

| 字段名 | 说明 |
|--------|------|
| `group_code` | 商龙云集团编码（G号，对应 `SL_UNIFIED_G_ID`，**WHERE 过滤用此字段**） |
| `store_code` | 商龙云门店编码（C号，对应 `omShopCodes`，**WHERE 过滤用此字段**） |
| `organ_id` / `store_id` | 组织/门店 ID |
| `rm_item_id` | 原料 ID（行级粒度） |
| `biz_date` | 业务日期 |
| `ap_year` / `ap_month` | 会计年/月 |
| `etl_time` | ETL 更新时间 |

#### 门店/组织信息

| 字段名 | 说明 |
|--------|------|
| `organ_code` / `organ_name` | 组织编码/名称 |
| `region_id` / `region_name` | 大区 |
| `organ_type` | 组织类型（集团/门店等） |
| `scm8_group_name` / `scm8_store_name` | SCM8 集团/门店名称 |
| `pos_store_code` | POS 门店编码 |
| `province` / `city` / `county` | 省市区 |

#### 原料信息

| 字段名 | 说明 |
|--------|------|
| `rm_item_code` | 原料编码 |
| `rm_item_name` | 原料名称 |
| `rm_item_small_type_code` / `rm_item_small_type_name` | 原料小类编码/名称 |
| `rm_item_parent_type_code` / `rm_item_parent_type_name` | 原料大类编码/名称 |
| `main_unit_name` | 主单位 |
| `report_unit_name` | 报表单位 |
| `report_unit_ratio` | 报表单位换算比 |

#### 入库（可 SUM）

| 字段名 | 说明 |
|--------|------|
| `instore_qty` / `instore_non_tax_cost_amount` / `instore_non_tax_amount` / `instore_amount` | **总入库**数量/不含税成本/不含税金额/含税金额 |
| `purchase_instore_qty` / `purchase_instore_non_tax_cost_amount` | **采购入库**数量/不含税成本 |
| `other_instore_qty` / `other_instore_non_tax_cost_amount` | **其他入库** |
| `inventory_profit_instore_qty` / `inventory_profit_instore_non_tax_cost_amount` | **盘盈入库** |
| `transfer_instore_qty` / `transfer_instore_non_tax_cost_amount` | **调拨入库** |
| `sales_return_instore_qty` / `sales_return_instore_non_tax_cost_amount` | **销售退货入库** |
| `write_off_return_instore_qty` / `write_off_return_instore_non_tax_cost_amount` | **核销退货入库** |
| `compose_process_instore_qty` / `compose_process_instore_non_tax_cost_amount` | **加工组装入库** |
| `split_net_material_instore_qty` / `split_net_material_instore_non_tax_cost_amount` | **分割净料入库** |
| `difference_instore_qty` / `difference_instore_non_tax_cost_amount` | **差异入库** |

#### 出库（可 SUM）

| 字段名 | 说明 |
|--------|------|
| `outstore_qty` / `outstore_amount` / `outstore_non_tax_amount` | **总出库**数量/含税金额/不含税金额 |
| `sales_outstore_qty` / `sales_outstore_non_tax_cost_amount` | **销售出库** |
| `other_outstore_qty` / `other_outstore_non_tax_cost_amount` | **其他出库** |
| `loss_report_qty` / `loss_report_non_tax_amount` / `loss_report_amount` | **报损**数量/不含税金额/含税金额 |
| `inventory_loss_outstore_qty` / `inventory_loss_outstore_non_tax_cost_amount` | **盘亏出库** |
| `transfer_outstore_qty` / `transfer_outstore_non_tax_cost_amount` | **调拨出库** |
| `purchase_return_qty` / `purchase_return_non_tax_cost_amount` | **采购退货** |
| `write_off_outstore_qty` / `write_off_outstore_non_tax_cost_amount` | **核销出库** |
| `compose_process_outstore_qty` / `compose_process_outstore_non_tax_cost_amount` | **加工组装出库** |
| `split_net_material_parent_outstore_qty` / `split_net_material_parent_outstore_non_tax_cost_amount` | **分割净料（父级）出库** |
| `department_outstore_qty` / `department_outstore_non_tax_cost_amount` | **部门出库** |
| `difference_outstore_qty` / `difference_outstore_non_tax_cost_amount` | **差异出库** |

#### 耗用（可 SUM）

| 字段名 | 说明 |
|--------|------|
| `actual_consume_qty` | **实际耗用数量** |
| `actual_non_tax_consume_amount` | 实际耗用不含税金额 |
| `actual_consume_amount` | 实际耗用含税金额 |
| `theory_consume_qty` | **理论耗用数量**（基于配方计算） |
| `non_tax_theory_cost_amount` | 理论耗用不含税成本 |
| `tax_theory_cost_amount` | **理论耗用含税成本**（值为 0 表示未接入配方系统） |

#### 库存（点取，禁止 SUM）

| 字段名 | 说明 |
|--------|------|
| `begin_inventory_qty` / `begin_non_tax_inventory_amount` / `begin_inventory_amount` | **实际期初**库存数量/不含税金额/含税金额 |
| `end_inventory_qty` / `end_non_tax_inventory_amount` / `end_inventory_amount` | **实际期末**库存数量/不含税金额/含税金额 |
| `theory_begin_inventory_qty` / `theory_begin_non_tax_inventory_amount` / `theory_begin_inventory_amount` | **理论期初**库存数量/不含税金额/含税金额 |
| `theory_end_inventory_qty` / `theory_end_non_tax_inventory_amount` / `theory_end_inventory_amount` | **理论期末**库存数量/不含税金额/含税金额 |

---

## 表 7：`dm.v_item_sale_analysis_with_sly` — 菜品销售分析（视图）

| 属性 | 说明 |
:|------|------|
| **规模** | 2.7亿+ 行 |
| **粒度** | 账单 × 菜品 |
| **类型** | 视图（VIEW） |

### 关联关系

| 关联方向 | 本表字段 | 目标表.字段 | 说明 |
|---------|---------|-----------|------|
| 营业明细 | `group_code` + `store_code` | `dm.v_pos_corp_sale_analysis_with_sly.group_code` + `store_code` | 同编码体系直接关联 |
| 门店主数据 | `group_code` + `store_code` | `e000.dt_store_view.group_code` + `store_code` | 获取门店基础信息 |

### 关键字段

| 字段分类 | 字段名 | 说明 |
|----------|--------|------|
| **关联字段** | `group_code` | 商龙云集团编码（G号，对应 `SL_UNIFIED_G_ID`） |
| | `store_code` | 商龙云门店编码（C号，对应 `omShopCodes`） |
| | `settle_biz_date` | 营业日期 |
| **菜品信息** | `item_id` | 菜品 ID |
| | `item_code` | 菜品编码 |
| | `item_name` | 菜品名称 |
| | `item_sub_class_id` / `item_sub_class_name` | 菜品小类 ID / 名称 |
| | `item_class_id` / `item_class_name` | 菜品大类 ID / 名称 |
| | `unit_name` | 计量单位 |
| **销售字段** | `sale_qty` | 销售数量 |
| | `recv_money` | 营业应收（原价） |
| | `busi_income` | 实收金额（扣优惠） |
| | `real_income` | 纯收金额 |
| | `item_orig_money` | 品项原价 |
| **优惠字段** | `disc_money_total` | 优惠总金额 |
| | `item_member_money` | 会员价优惠 |
| | `item_promote_money` | 促销优惠 |
| | `item_present_money` | 赠送金额 |
| **分类字段** | `sale_type_name` | 销售渠道：堂食/外卖/外带/自提 |
| | `dining_type_name` | 用餐场景 |
| | `order_source_name` | 订单来源 |
| | `table_settle_shift_name` | 时段：早市/午市/晚市/宵夜 |
| | `manage_type` | 管理类型（直营/加盟等） |
| | `region` / `province` / `city` | 大区/省份/城市 |

---

## 枚举值速查

| 字段 | 表 | 枚举值 |
|------|-----|--------|
| `manage_type` | 两表 | 直营 / 加盟 / 托管 / 合作 |
| `region` | 两表 | 华北 / 华东 / 华南 / 华中 / 西北 / 西南 / 东北 |
| ~~`is_open`~~ | ~~dt_store~~ | ⚠️ `e000.dt_store_view` 已不暴露该字段，如需查询请从 POS/菜品视图获取 |
| `sale_type_name` | dm_pos | 堂食 / 外卖 / 外带 / 自提 |
| `dining_type_name` | dm_pos | 普通就餐 / 亲友聚餐 / 商务宴请 / 婚宴 / 家庭就餐 |
| `order_source_name` | dm_pos | 自来客 / 微信 / 支付宝 / 美团外卖 |
| `table_settle_shift_name` | dm_pos | 早市 / 午市 / 晚市 / 宵夜 |

---

## 三个金额指标的关系

```
recv_money (营业应收) ≥ busi_income (实收金额) ≥ real_income (纯收金额)

recv_money - busi_income = disc_money_total（优惠总金额）
busi_income - real_income ≈ service_free + low_consume + asitem_fix + item_wipe（杂项费用合计）
recv_money - real_income = 优惠合计 + 杂费合计
```

---

## 金额单位

所有金额字段（`real_income`, `busi_income`, `recv_money` 等）：**元**，decimal(18,4) 精度
