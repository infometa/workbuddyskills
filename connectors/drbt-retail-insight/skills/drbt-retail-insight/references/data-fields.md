# 销售明细表查询 · 字段清单

## 入参 filter

| 字段 | 类型 | 说明 |
|---|---|---|
| `begin_create_date_timestamp` | int | 制单开始时间戳（**毫秒**，UTC+8） |
| `end_create_date_timestamp` | int | 制单结束时间戳（**毫秒**，UTC+8） |
| `begin_bill_account_date` | str | 记账开始日期，如 `2026-09-01` |
| `end_bill_account_date` | str | 记账结束日期 |

> 制单时间与记账时间**至少传一个**。默认按制单日期过滤。

其他可选过滤：`bill_type_list`、`institution_id_list`（门店）、`warehouse_id_list`、`warehouse_type`、`product_category_id_list`、`supplier_id_list`、`store_user_id_list`（店员）、`business_account_id_list`（业务员）、`business_partner_id_list`（分销客户）、`sku_name`、`imei1`、`bill_number`、`begin_price`/`end_price`、`customer_info`、`export_column_keys`。

分页：`page_num`（默认 1）、`page_size`（建议 ≤ 100）。

## bill_type

| 值 | 含义 |
|---|---|
| 1 | 零售 |
| 2 | 零售退 |
| 3 | 批发（分销出库） |
| 4 | 批发退（分销退货） |

退货行的 `qty` 与 `sale_money` 均为负数，直接加总即得净额。

## 返回结构

```
data.total       -> 命中明细行数（字符串）
data.pages       -> 总页数
data.rows[]      -> 明细行
data.total_row   -> ★ 整个筛选区间的汇总（不是当前页！）
```

`total_row` 里的 `sale_qty` / `sale_money` / `retail_cost_gross_profit` / `wholesale_cost_gross_profit` 等可直接当作区间口径答案使用 —— `page_size=1` 即可取到。

## 明细行字段

### 标识 / 单据
`id`、`bill_id`、`bill_number`、`bill_type`、`create_date_timestamp`、`create_date`、`bill_account_date`

### 商品
`product69_code`、`sku_code`、`product_name`、`product_category_level1_name`、`product_category_level2_name`、`product_category_level3_name`、`brand_name`、`imei1`、`batch_no`、`in_stock_date`、`in_stock_date_timestamp`

### 金额
| 字段 | 说明 |
|---|---|
| `sale_price` | 单价 |
| `qty` | 数量（退货为负） |
| `sale_money` | **销售额**（不含返利） |
| `sale_rebate_money` | 销售返利 |
| `after_rebate_sale_money` | 含返利销售额 |
| `tax_money` / `sale_tax_money` | 税额 |
| `tax_rate` / `sale_tax_rate` | 税率（常见 0.13） |
| `retail_cost_money` | ★ 零售销售成本 |
| `retail_cost_gross_profit` | ★ 零售成本毛利 |
| `wholesale_cost_money` | ★ 批发销售成本 |
| `wholesale_cost_gross_profit` | ★ 批发成本毛利 |

### 被权限掩码为 `"***"` 的字段（不可用）

`business_cost_money`、`business_cost_gross_profit`、`tax_excluded_cost`、`tax_excluded_cost_gross_profit`、`item_gross_profit`、`gift_cost`、`wholesale_rebate_profit_money`

### 组织 / 人员
| 字段 | 说明 |
|---|---|
| `institution_name` | 出货主体：零售门店 **或** 批发主体（河南强视公司 / 武汉强视公司） |
| `warehouse_name` | 仓库 |
| `store_user_name` | **零售店员**（仅零售 / 零售退有值） |
| `business_account_name` | **分销业务员**（仅批发 / 批发退有值） |
| `create_account_name` | 制单人 |
| `supplier_name` | 供应商 |
| `business_partner_name` | 分销客户 |
| `consumer_phone` | 零售顾客手机号 |
| `cashier_name_list` | 收银方式与金额，如 `["商场收银：2498.00"]` |

## 进销存报表 · 字段

入参：`filter.begin_date` / `filter.end_date`（**整型 `yyyyMMdd`**）、`filter.dimension`（1 商品分类 / 2 供应商 / 3 仓库 / 4 门店）、`show_cost`、`keyword` 等。

数量字段可用：`begin_qty`、`end_qty`、`purchase_in_qty`、`receive_in_qty`、`sale_return_qty`、`distribution_return_qty`、`transfer_return_qty`、`purchase_return_qty`、`send_out_qty`、`sale_out_qty`、`distribution_out_qty`、`write_off_out_qty`、`stock_take_in_qty`、`stock_take_out_qty`。

金额字段**全部被掩码**（`*_money` 一律 `"***"`），只能拿数量。

校验公式：

```
end_qty = begin_qty
        + purchase_in_qty + receive_in_qty + sale_return_qty
        + distribution_return_qty + transfer_return_qty + stock_take_in_qty
        - purchase_return_qty - send_out_qty - sale_out_qty
        - distribution_out_qty - write_off_out_qty - stock_take_out_qty
```

`total_row` 同样是全局汇总。
