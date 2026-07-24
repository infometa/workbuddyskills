# starrocks-business-analysis-sly 演示方案

> 用于 AI 问数效果演示，**不暴露任何真实集团/品牌信息**。
> 所有示例中的集团、门店、品牌名称均为虚构占位符。

---

## 演示概述

| 项目 | 说明 |
|-----|------|
| 演示目标 | 展示 AI 自然语言查数能力，覆盖多业务场景 |
| 数据范围 | 使用虚构占位符（`某川菜品牌`、`某火锅连锁`等） |
| 查询逻辑 | 演示不同 Intent 的触发与 SQL 生成，**不实际执行** |
| 适用场景 | 客户 POC、产品演示、内部评审 |

> ⚠️ **重要**：演示文档中的所有数据均为虚构占位，AI 在实际查询时会根据用户 token 注入真实 `group_code`，数据结果为用户权限范围内的真实数据。

---

## 一、🏪 门店画像（Intent 1-5）

### Q1：我们集团现在有多少家门店？
**Intent**：Intent 01 — 门店基础信息

**触发词识别**：
- 「有多少家门店」「门店总数」「几个店」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `group_code` | 用户 token 注入 |
| `store_code` | 未指定（全量） |

**生成 SQL**：
```sql
SELECT
    COUNT(DISTINCT store_code) AS 门店总数,
    COUNT(DISTINCT CASE WHEN is_enable = '1' THEN store_code END) AS 营业门店数,
    COUNT(DISTINCT CASE WHEN is_enable = '0' THEN store_code END) AS 停业门店数
FROM e000.dt_store
WHERE group_code = :group_code
LIMIT 1;
```

**回答示例**：
> 集团共有 **48 家**门店，其中 **45 家**正常营业，**3 家**已停业。

---

### Q2：门店都分布在哪些城市？
**Intent**：Intent 03 — 门店地理分布

**触发词识别**：
- 「哪些城市」「门店分布在哪」「在哪些城市有店」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    province AS 省份,
    city AS 城市,
    COUNT(DISTINCT store_code) AS 门店数
FROM e000.dt_store
WHERE group_code = :group_code
    AND is_enable = '1'
GROUP BY province, city
ORDER BY 门店数 DESC
LIMIT 50;
```

**回答示例**：
> 门店主要分布在 **6 个省份、12 个城市**，其中 **成都** 最多（12家），其次是 **重庆**（8家）和 **西安**（6家）。

---

### Q3：各品牌的门店数量是多少？
**Intent**：Intent 04 — 品牌排名分析

**触发词识别**：
- 「品牌门店数」「各品牌有多少店」「品牌分布」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    brand_name AS 品牌名称,
    COUNT(DISTINCT store_code) AS 门店数
FROM e000.dt_store
WHERE group_code = :group_code
    AND is_enable = '1'
GROUP BY brand_name
ORDER BY 门店数 DESC
LIMIT 20;
```

**回答示例**：
> 集团下共有 **4 个品牌**，其中「川菜旗舰店」品牌门店最多（18家），其次是「川菜轻食档」（12家）。

---

## 二、💰 营收分析（Intent 6-9）

### Q4：2月份整体营收是多少？同比去年怎么样？
**Intent**：Intent 09 — 营收同比分析

**触发词识别**：
- 「2月营收」「同比」「比去年增长多少」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `compare_type` | YoY（同比） |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    '2026年2月' AS 本期,
    SUM(recv_money) AS 本期营收,
    SUM(busi_income) AS 本期实收,
    SUM(real_income) AS 本期纯收,
    COUNT(DISTINCT bill_id) AS 账单数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
UNION ALL
SELECT
    '2025年2月' AS 本期,
    SUM(recv_money),
    SUM(busi_income),
    SUM(real_income),
    COUNT(DISTINCT bill_id)
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2025-02-01'
    AND settle_biz_date < '2025-03-01';
```

**回答示例**：
> | 期间 | 营收 | 实收 | 纯收 | 账单数 |
> |------|-----:|-----:|-----:|-------:|
> | 2026年2月 | 4,820万 | 4,560万 | 4,230万 | 62,400 |
> | 2025年2月 | 4,150万 | 3,920万 | 3,640万 | 54,200 |
> | **同比** | **+16.1%** | **+16.3%** | **+16.2%** | **+15.1%** |
>
> 2月营收同比增长约 **16%**，整体增势良好。

---

### Q5：营收最高的10家门店是哪些？
**Intent**：Intent 07 — 营收门店排名

**触发词识别**：
- 「营收最高」「最赚钱的店」「门店营收排行」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 用户指定（未指定则询问） |
| `rank_by` | busi_income（实收，默认） |
| `top_n` | 10 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    store_name AS 门店名称,
    COUNT(DISTINCT bill_id) AS 账单数,
    ROUND(SUM(recv_money), 2) AS 营收,
    ROUND(SUM(busi_income), 2) AS 实收,
    ROUND(SUM(real_income), 2) AS 纯收,
    ROUND(SUM(busi_income) / COUNT(DISTINCT bill_id), 2) AS 客单价
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY store_name, store_code
ORDER BY SUM(busi_income) DESC
LIMIT 10;
```

**回答示例**：
> | 排名 | 门店名称 | 账单数 | 营收 | 实收 | 纯收 | 客单价 |
> |---:|---------|------:|-----:|-----:|-----:|-----:|
> | 1 | 成都春熙路旗舰店 | 3,240 | 482万 | 456万 | 423万 | 1,407 |
> | 2 | 成都锦里店 | 2,890 | 421万 | 398万 | 369万 | 1,377 |
> | 3 | 重庆解放碑店 | 2,560 | 368万 | 348万 | 323万 | 1,359 |
> | … | … | … | … | … | … | … |

---

## 三、👥 客流与客群（Intent 10-14）

### Q6：2月份一共接待了多少客人？客单价是多少？
**Intent**：Intent 10 — 客流分析

**触发词识别**：
- 「接待多少客人」「客流」「客单价」「多少人就餐」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    COUNT(DISTINCT bill_id) AS 账单数,
    SUM(person_num) AS 用餐人数,
    ROUND(SUM(person_num) / COUNT(DISTINCT bill_id), 2) AS 人均,
    ROUND(SUM(busi_income) / SUM(person_num), 2) AS 客单价
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01';
```

**回答示例**：
> 2月份共接待 **62,400 人次**（账单数），累计用餐人数 **86,640 人**，人均 **1.39 人/桌**，客单价约 **¥526**。

---

### Q7：小程序下单占比是多少？比上个月提升了还是下降了？
**Intent**：Intent 23 — 小程序渠道分析

**触发词识别**：
- 「小程序占比」「小程序提升了吗」「小程序下单率」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `compare_type` | MoM（环比） |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    '本期' AS 期间,
    COUNT(DISTINCT CASE WHEN is_applet_bill = '1' THEN bill_id END) AS 小程序账单数,
    COUNT(DISTINCT bill_id) AS 总账单数,
    ROUND(COUNT(DISTINCT CASE WHEN is_applet_bill = '1' THEN bill_id END) * 100.0 / COUNT(DISTINCT bill_id), 2) AS 小程序占比_pct
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
UNION ALL
SELECT
    '上期' AS 期间,
    COUNT(DISTINCT CASE WHEN is_applet_bill = '1' THEN bill_id END),
    COUNT(DISTINCT bill_id),
    ROUND(COUNT(DISTINCT CASE WHEN is_applet_bill = '1' THEN bill_id END) * 100.0 / COUNT(DISTINCT bill_id), 2)
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-01-01'
    AND settle_biz_date < '2026-02-01';
```

**回答示例**：
> | 期间 | 小程序账单数 | 总账单数 | 小程序占比 |
> |------|----------:|-------:|--------:|
> | 本期（2月） | 23,208 | 62,400 | **37.2%** |
> | 上期（1月） | 22,440 | 61,200 | **36.7%** |
> | 变化 | +768 | +1,200 | **+0.5pp** |
>
> 小程序下单占比小幅提升 **0.5 个百分点**，渗透率稳定在 **37%** 左右。

---

## 四、🎁 优惠与结算（Intent 15-19）

### Q8：2月份一共优惠了多少钱？折扣率是多少？
**Intent**：Intent 15 — 优惠折扣分析

**触发词识别**：
- 「优惠了多少钱」「折扣率」「优惠总额」「折扣多少」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    COUNT(DISTINCT bill_id) AS 账单数,
    ROUND(SUM(recv_money), 2) AS 应收总额,
    ROUND(SUM(busi_income), 2) AS 实收总额,
    ROUND(SUM(recv_money) - SUM(busi_income), 2) AS 优惠总额,
    ROUND((SUM(recv_money) - SUM(busi_income)) * 100.0 / SUM(recv_money), 2) AS 折扣率_pct
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01';
```

**回答示例**：
> 2月份优惠总额 **¥260万**，整体折扣率约 **5.4%**（优惠前营收4,820万 → 实收4,560万）。折扣率处于合理水平。

---

## 五、🍽️ 菜品与套餐（Intent 20-22）

### Q9：套餐卖得好不好？套餐营收占比多少？
**Intent**：Intent 20 — 套餐分析

**触发词识别**：
- 「套餐营收」「套餐占比」「套餐卖了多少」「套餐受欢迎吗」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 用户指定（未指定则询问） |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    COUNT(DISTINCT bill_id) AS 含套餐账单数,
    COUNT(DISTINCT CASE WHEN setmeal_count > 0 THEN bill_id END) AS 含套餐账单,
    ROUND(COUNT(DISTINCT CASE WHEN setmeal_count > 0 THEN bill_id END) * 100.0 / COUNT(DISTINCT bill_id), 2) AS 套餐渗透率_pct,
    ROUND(SUM(setmeal_money), 2) AS 套餐营收,
    ROUND(SUM(setmeal_money) * 100.0 / SUM(busi_income), 2) AS 套餐营收占比_pct
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1;
```

**回答示例**：
> 含套餐的账单占比约 **28.6%**，套餐营收 **¥1,305万**，占总营收的 **28.6%**，说明套餐产品对营收有较强拉动作用。

---

## 六、🥩 菜品明细分析（Intent 42-50）

### Q10：2月份卖得最好的20道菜是什么？
**Intent**：Intent 42 — 菜品销售排行

**触发词识别**：
- 「卖得最好的菜」「最畅销的菜」「菜品排行」「TOP菜」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `group_by` | 品项 |
| `rank_by` | 营收（或数量） |
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `top_n` | 20 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    item_name AS 菜品名称,
    small_class_name AS 小类,
    big_class_name AS 大类,
    COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(pre_discount_price), 2) AS 应收金额,
    ROUND(SUM(actual_money), 2) AS 实收金额,
    ROUND(SUM(income_money), 2) AS 纯收金额
FROM dm.v_item_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
    AND last_qty > 0
GROUP BY item_name, small_class_name, big_class_name
ORDER BY SUM(income_money) DESC
LIMIT 20;
```

**回答示例**：
> | 排名 | 菜品名称 | 小类 | 大类 | 销售数量 | 纯收金额 |
> |---:|---------|-----|-----|-------:|-------:|
> | 1 | 招牌毛血旺 | 特色菜 | 川菜 | 2,840 | ¥28.6万 |
> | 2 | 夫妻肺片 | 凉菜 | 川菜 | 2,120 | ¥21.2万 |
> | 3 | 回锅肉 | 经典菜 | 川菜 | 1,980 | ¥19.8万 |
> | … | … | … | … | … | … |

---

### Q11：哪些菜毛利率最高？给我看毛利率最高的10道菜
**Intent**：Intent 46 — 菜品毛利分析

**触发词识别**：
- 「毛利率最高」「哪道菜利润高」「毛利排行」「盈利能力」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `group_by` | 品项 |
| `rank_by` | 折后毛利率 |
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `top_n` | 10 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    item_name AS 菜品名称,
    small_class_name AS 小类,
    big_class_name AS 大类,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(pre_discount_price), 2) AS 应收金额,
    ROUND(SUM(cost_money), 2) AS 理论成本,
    ROUND(SUM(pre_discount_price) - SUM(cost_money), 2) AS 折前理论毛利,
    ROUND((SUM(pre_discount_price) - SUM(cost_money)) / NULLIF(SUM(pre_discount_price), 0) * 100, 2) AS 折前毛利率_pct,
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(income_money) - SUM(cost_money), 2) AS 折后理论毛利,
    ROUND((SUM(income_money) - SUM(cost_money)) / NULLIF(SUM(income_money), 0) * 100, 2) AS 折后毛利率_pct
FROM dm.v_item_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
    AND last_qty > 0
    AND cost_money > 0
GROUP BY item_name, small_class_name, big_class_name
ORDER BY (SUM(income_money) - SUM(cost_money)) / NULLIF(SUM(income_money), 0) DESC
LIMIT 10;
```

**回答示例**：
> | 排名 | 菜品名称 | 销售数量 | 纯收金额 | 理论成本 | 折后理论毛利 | **折后毛利率** |
> |---:|---------|-------:|-------:|-------:|----------:|------------:|
> | 1 | 酸辣土豆丝 | 3,200 | ¥9.6万 | ¥0.3万 | ¥9.3万 | **96.9%** |
> | 2 | 麻婆豆腐 | 2,800 | ¥8.4万 | ¥0.3万 | ¥8.1万 | **96.4%** |
> | 3 | 拍黄瓜 | 2,100 | ¥4.2万 | ¥0.2万 | ¥4.0万 | **95.2%** |
> | … | … | … | … | … | … | … |
>
> 高毛利菜品以**家常凉菜/素菜**为主，适合作为引流品拉动客流。

---

### Q12：哪些菜退得最多？有没有需要重点关注的？
**Intent**：Intent 45 — 菜品退菜明细分析

**触发词识别**：
- 「退菜最多」「退货」「退菜率」「哪些菜被退回」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `rank_by` | 退菜金额（默认） |
| `date_range` | 用户指定 |
| `top_n` | 10 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    item_name AS 菜品名称,
    big_class_name AS 大类,
    ROUND(SUM(last_qty), 2) AS 实售数量,
    ROUND(SUM(return_qty), 2) AS 退菜数量,
    ROUND(SUM(return_subtotal), 2) AS 退菜金额,
    ROUND(SUM(return_qty) * 100.0 / NULLIF(SUM(last_qty) + SUM(return_qty), 0), 2) AS 退菜率_pct
FROM dm.v_item_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND return_qty > 0
GROUP BY item_name, big_class_name
HAVING SUM(return_qty) > 0
ORDER BY SUM(return_subtotal) DESC
LIMIT 10;
```

**回答示例**：
> | 菜品名称 | 大类 | 实售数量 | 退菜数量 | 退菜金额 | 退菜率 |
> |---------|-----|--------:|--------:|--------:|------:|
> | 水煮鱼（大份） | 特色菜 | 1,240 | 86 | ¥6,480 | 6.5% |
> | 毛血旺（大份） | 特色菜 | 1,860 | 62 | ¥4,340 | 3.2% |
> | … | … | … | … | … | … |
>
> 「水煮鱼（大份）」退菜率偏高（6.5%），建议关注出品质量或口味是否符合本地偏好。

---

### Q13：2月份赠送最多的菜是什么？赠送成本高不高？
**Intent**：Intent 48 — 赠送品项分析

**触发词识别**：
- 「赠送最多」「免费送」「赠送菜品」「赠送成本」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `rank_by` | 赠送金额（默认） |
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `top_n` | 10 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    item_name AS 菜品名称,
    small_class_name AS 小类,
    ROUND(SUM(present_qty), 2) AS 赠送数量,
    ROUND(SUM(present_money), 2) AS 赠送金额,
    ROUND(SUM(cost_money), 2) AS 赠送成本,
    ROUND(SUM(present_money) * 100.0 / SUM(SUM(present_money)) OVER(), 2) AS 赠送金额占比_pct
FROM dm.v_item_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
    AND present_qty > 0
    AND present_money > 0
GROUP BY item_name, small_class_name
ORDER BY SUM(present_money) DESC
LIMIT 10;
```

**回答示例**：
> | 菜品名称 | 小类 | 赠送数量 | 赠送金额 | 赠送成本 |
> |---------|-----|--------:|--------:|-------:|
> | 招牌开胃小菜 | 凉菜 | 3,420 | ¥6.8万 | ¥1.2万 |
> | 手工酸奶 | 甜品 | 2,860 | ¥4.3万 | ¥0.8万 |
> | 餐后水果 | 果盘 | 1,920 | ¥2.9万 | ¥0.6万 |
>
> 赠送成本约占赠送金额的 **17%**，属于合理的促销成本区间。

---

## 七、⏱️ 运营效率（Intent 28-32）

### Q14：中午和晚上翻台率分别是多少？
**Intent**：Intent 28 — 时段分析

**触发词识别**：
- 「中午翻台率」「晚市翻台率」「时段效率」「翻台率」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 用户指定 |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    CASE
        WHEN settle_biz_date BETWEEN :start_date AND :end_date_plus_1 THEN '全日'
    END AS 时段,
    ROUND(SUM(open_table_count) / SUM(table_count * shift_count), 4) * 100 AS 开台率_pct,
    GREATEST(ROUND((SUM(open_table_count) / SUM(table_count * shift_count) - 1) * 100, 2), 0) AS 翻台率_pct
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY CASE WHEN settle_biz_date BETWEEN :start_date AND :end_date_plus_1 THEN '全日' END;
```

**回答示例**：
> | 时段 | 开台率 | 翻台率 |
> |------|------:|------:|
> | 全日 | 142.6% | **42.6%** |
> | 午市（模拟估算） | 98.2% | — |
> | 晚市（模拟估算） | 168.4% | — |
>
> 整体翻台率约 **42.6%**，晚市压力较大，建议优化等位管理。

---

## 八、📊 多维对比（Intent 33-41）

### Q15：2月份营收环比1月份增长了多少？趋势如何？
**Intent**：Intent 33 — 环比分析

**触发词识别**：
- 「环比」「比上个月」「增长了多少」「趋势」

**Slots 提取**：
| Slot | 值 |
|------|-----|
| `date_range` | 2026-02-01 ~ 2026-02-28 |
| `compare_type` | MoM（环比） |
| `group_code` | 用户 token 注入 |

**生成 SQL**：
```sql
SELECT
    '本期(2月)' AS 期间,
    COUNT(DISTINCT bill_id) AS 账单数,
    ROUND(SUM(person_num), 2) AS 用餐人数,
    ROUND(SUM(recv_money), 2) AS 营收,
    ROUND(SUM(busi_income), 2) AS 实收,
    ROUND(SUM(busi_income) / SUM(person_num), 2) AS 客单价
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-02-01'
    AND settle_biz_date < '2026-03-01'
UNION ALL
SELECT
    '上期(1月)' AS 期间,
    COUNT(DISTINCT bill_id),
    ROUND(SUM(person_num), 2),
    ROUND(SUM(recv_money), 2),
    ROUND(SUM(busi_income), 2),
    ROUND(SUM(busi_income) / SUM(person_num), 2)
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE cy7_group_code = :group_code
    AND settle_biz_date >= '2026-01-01'
    AND settle_biz_date < '2026-02-01';
```

**回答示例**：
> | 期间 | 账单数 | 用餐人数 | 营收 | 实收 | 客单价 |
> |------|------:|--------:|-----:|-----:|-----:|
> | 本期（2月） | 62,400 | 86,640 | 4,820万 | 4,560万 | ¥526 |
> | 上期（1月） | 61,200 | 84,580 | 4,680万 | 4,420万 | ¥523 |
> | **环比** | +1,200 | +2,060 | **+3.0%** | **+3.2%** | **+0.6%** |
>
> 2月营收环比增长约 **3%**，客单价基本持平，增量主要来自客流提升。

---

## 演示流程建议

| 顺序 | 问题类型 | 建议时长 | 目的 |
|----:|---------|-------:|------|
| 1 | 门店画像 | 2 min | 建立「我能查你有什么」的基础感知 |
| 2 | 营收分析 | 3 min | 展示「我能查你做得多好」的核心价值 |
| 3 | 客流与客群 | 2 min | 体现多维度分析能力 |
| 4 | 优惠与菜品 | 3 min | 深入业务细节 |
| 5 | 菜品明细 | 4 min | **重点**——展示品项粒度的精细分析 |
| 6 | 运营效率 | 2 min | 拓展分析广度 |
| 7 | 多维对比 | 2 min | 收尾，体现同比/环比能力 |

**总时长建议：18-20 分钟**（含互动问答）

---

## 演示注意事项

1. **用户数据隔离**：演示时 AI 根据用户 token 自动注入 `group_code`，结果天然隔离，无需额外处理
2. **日期默认策略**：用户未指定日期时，AI 会主动询问，避免全量查询
3. **LIMIT 安全兜底**：所有营业表查询强制带 LIMIT，防止全表扫描
4. **敏感信息不暴露**：SQL 中不出现 `group_code`、门店ID等敏感参数，仅展示业务含义
5. **数据均为虚构**：演示文档中的所有示例数据（金额、门店名、人数等）均为占位符
