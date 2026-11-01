# SQL 参考速查

> 报错修正、边界情况、已知数据限制。写 SQL 的正确写法以 sql_templates（Q/A/D）为准。

---

## 复购率模式（BITMAP_AND）

sql_templates 未覆盖的特殊模式。用 CTE 分别聚合两个周期，再用 BITMAP_AND 计算交集：

> **当前 Agent 可用性门禁**：当前分析服务白名单不包含 `dwd_base_sales_order_item_df`；以下 D-10/用户明细查询是条件模板，不是已可用能力。必须先通过 table_structure 按精确表名查询且确认实际授权与字段；当前不可用时明确告知无法执行该明细归因/用户聚合，只能使用已授权汇总维度并说明限制。禁止直接执行、扩展白名单、编造字段或将汇总数据冒充用户明细。


```
用户："帮我看看 2026 年 1 月商品的复购率最高的是哪个"
→ 拆分上半月(基准期) + 下半月(目标期)，CTE + BITMAP_AND
```
```sql
WITH base AS (
  SELECT spu_id, spu_name, BITMAP_UNION(pay_uv) AS base_bitmap
  FROM app_commodity_stat_spu_di
  WHERE stat_date BETWEEN '20260101' AND '20260115'
  GROUP BY spu_id, spu_name
),
target AS (
  SELECT spu_id, BITMAP_UNION(pay_uv) AS target_bitmap
  FROM app_commodity_stat_spu_di
  WHERE stat_date BETWEEN '20260116' AND '20260131'
  GROUP BY spu_id
)
SELECT base.spu_id AS 商品ID, base.spu_name AS 商品名称,
       BITMAP_COUNT(BITMAP_AND(base.base_bitmap, target.target_bitmap))
         / NULLIF(BITMAP_COUNT(base.base_bitmap), 0) AS 复购率
FROM base LEFT JOIN target ON base.spu_id = target.spu_id
ORDER BY 复购率 DESC LIMIT 1
```

---

## 复购 vs 非复购客单价对比模式

sql_templates 未覆盖的特殊模式。`app_user_stat_di`/品类表均为天粒度枚举汇总，无用户明细，无法按用户聚合；需改用 `dwd_base_sales_order_item_df`（订单×SKU 明细，D-10 已用此表）按 `uid` 聚合订单数和实付金额：

```
用户："复购用户的客单价跟非复购用户差多少"
→ CTE 按 uid 聚合去重订单数(COUNT DISTINCT order_no)和实付总额(SUM total_pay_amount)，按订单数≥2分组
```
```sql
WITH user_orders AS (
  SELECT uid,
         COUNT(DISTINCT order_no) AS order_cnt,
         SUM(total_pay_amount) / 100.0 AS user_gmv
  FROM dwd_base_sales_order_item_df
  WHERE pay_status = 1
    AND imp_date BETWEEN '{start_date}' AND '{end_date}'
  GROUP BY uid
)
SELECT
    CASE WHEN order_cnt >= 2 THEN '复购用户' ELSE '非复购用户' END AS 用户类型,
    COUNT(DISTINCT uid) AS 用户数,
    ROUND(SUM(user_gmv), 2) AS 总成交金额_元,
    ROUND(SUM(user_gmv) / NULLIF(COUNT(DISTINCT uid), 0), 2) AS 客单价
FROM user_orders
GROUP BY CASE WHEN order_cnt >= 2 THEN '复购用户' ELSE '非复购用户' END;
```

> `total_pay_amount` 单位为分，需 `/100.0` 转元；`pay_status=1` 筛已支付订单；按 `order_no` 去重避免同订单多 SKU 行重复计数。

---

## 复合错误修正示例

一条 SQL 可能同时有多个问题，需要一次性全部修正：

```
原始 SQL：SELECT channel_id, SUM(pay_amt)/BITMAP_COUNT(...) AS ROI, category_name FROM app_market_stat_di WHERE dim_type='channel' ...
报错：Unknown column 'category_name'
→ 诊断：类型B（channel 维度无 category_name）+ 类型D（分母缺 NULLIF）
→ 修正：① 移除 category_name ② 分母加 NULLIF
```

---

## 6 类错误诊断速查

SQL 报错时按此表分类诊断，对症修正：

| 类型 | 报错表现 | 修正方式 |
|------|---------|---------|
| A：语法错误 | `Syntax error` | 修正语法 |
| B：对象不存在 | `Unknown column` | 修正拼写 / 替代字段 / 返回"无法查询" |
| C：聚合函数误用 | BITMAP 相关报错 | 替换为 `BITMAP_COUNT(BITMAP_UNION())` |
| D：除零错误 | `Division by zero` | 添加 `NULLIF(分母, 0)` |
| E：数据膨胀 | 结果量级异常 | 补全 JOIN ON 条件（必须含时间字段） |
| F：执行超时 | `Query timeout` | 添加分区过滤 |

---

## 已知数据限制

| 维度 | 状态 | 处理方式 |
|------|------|---------|
| `activity_type` | MV 已建，有数据 | 正常查询，pay_uv/pay_cnt 用 BITMAP_COUNT |
| `coupon_type` | 券概览表已建，有数据 | acquire_cnt/use_cnt 用 BITMAP_COUNT；券成本跨门店先按天取 MAX 去重 |
| CPS 分销表 | MV 已建，有数据 | click_uv/pay_uv/complate_order_cnt 用 BITMAP_COUNT |
| 品类表无 `order_uv` | 品类漏斗只到 `addcart_uv → pay_uv` | 品类漏斗不含"下单"环节 |
| 分销表无内外部分销员区分 | 只能统计总推广人数 | 不区分内部/外部 |
| 所有表天粒度 | 无小时级数据 | 小时级分析返回"无法计算" |

---

## 方言注意事项

- **字符串类型显式转换**：`VARCHAR(N)` 之间比较/JOIN 时如遇类型不一致报错，用 `CAST(field AS VARCHAR(N))` 显式转换，N 需与目标字段声明宽度一致（如 `CAST(spu_id AS VARCHAR(64))`）
