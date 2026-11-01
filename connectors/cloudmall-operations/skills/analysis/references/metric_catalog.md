# 指标清单

> 云MALL 电商数据分析 Skill 当前支持的全部指标。
> 更新日期：2026-06-17（基座 2.0 库表全面迁移）

**口径说明约定**：
- **原子指标**：直接从数据表取值，口径说明列写"统计什么"
- **衍生指标**：由原子指标计算而来，口径说明列写"分子 / 分母"的业务含义
- **去重说明**：标注"去重"表示同一用户/订单在统计周期内只计一次（BITMAP 实现）

**双口径切换规则**：
> 所有比率类指标（转化率/点击率/加购率/核销率）**默认使用 UV（人数）口径**，衡量"有多大比例的人完成了某个行为"。
> 当用户**明确说"次数""PV 口径"**时，切换为 PV（次数）口径，衡量"每次行为的转化效率"。
> 下表中标注 `[默认UV / 备选PV]` 的指标支持双口径切换。
> **例外**：**退款率**统一使用金额口径（退款金额/GMV），不区分 UV/PV。
> **例外**：**商品域转化漏斗**（scene_5 商品分析场景）默认使用**次数（PV）口径**：曝光次数 → 点击次数 → 加购次数 → 成交订单数，不受上方 UV 默认值约束。

---

## 一、交易域（大盘经营）

来源表：`app_sales_stat_overview_di`（天粒度）/ `app_sales_stat_store_di`（天×门店粒度）

### 原子指标

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 1 | GMV（成交金额） | 统计周期内所有已支付订单的成交总金额 | `SUM(gmv)` | 单位：元 |
| 2 | 支付人数 | 统计周期内发生过支付行为的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv))` | Bitmap 去重 |
| 3 | 支付订单数 | 统计周期内已支付的去重订单数 | `BITMAP_COUNT(BITMAP_UNION(pay_cnt))` | Bitmap 去重 |
| 4 | 下单人数 | 统计周期内提交过订单的去重用户数（含未支付） | `BITMAP_COUNT(BITMAP_UNION(order_uv))` | Bitmap 去重 |
| 5 | 下单订单数 | 统计周期内提交的去重订单数（含未支付） | `BITMAP_COUNT(BITMAP_UNION(order_cnt))` | Bitmap 去重 |
| 6 | 下单金额 | 统计周期内所有提交订单的总金额（含未支付） | `SUM(order_amt)` | 单位：元 |
| 7 | 销量（件数） | 统计周期内售出的商品总件数 | `SUM(pay_item_cnt)` | BIGINT 直接 SUM |
| 8 | 退款金额 | 统计周期内已退款的总金额 | `SUM(refund_amt)` | 单位：元 |
| 9 | 退款人数 | 统计周期内发生过退款的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(refund_uv))` | Bitmap 去重 |
| 10 | 退款订单数 | 统计周期内已退款的订单总数 | `BITMAP_COUNT(BITMAP_UNION(refund_order_cnt))` | Bitmap 去重 |
| 11 | 浏览次数（PV） | 统计周期内商城页面被浏览的总次数（同一用户多次访问重复计数） | `SUM(browse_pv)` | SQL 别名：浏览次数 |
| 12 | 访问次数（PV） | 统计周期内商城被访问的总次数（同一用户多次访问重复计数） | `SUM(visit_pv)` | SQL 别名：访问次数 |
| 13 | 浏览人数 | 统计周期内浏览过商城的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(browse_uv))` | Bitmap 去重；SQL 别名：浏览人数（原字段 browse_uv） |
| 14 | 访问人数 | 统计周期内访问过商城的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(visit_uv))` | Bitmap 去重；SQL 别名：访问人数（原字段 visit_uv） |
| 14 | 加购次数 | 统计周期内商品被加入购物车的总次数（不去重） | `SUM(cart_pv)` | BIGINT；⚠️ 概览表已无 `click_pv`，原"点击量"统一以加购替代 |
| 15 | 加购人数 | 统计周期内加入购物车的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(cart_uv))` | Bitmap 去重；⚠️ 概览表已无 `click_uv`，原"点击人数"统一以加购替代 |
| 16 | 注册人数 | 统计周期内首次注册的新用户数 | `BITMAP_COUNT(BITMAP_UNION(register_uv))` | Bitmap 去重 |

### 衍生指标

| # | 指标名 | 口径说明（分子 / 分母） | 计算逻辑 | 备注 |
|---|--------|------------------------|----------|------|
| 17 | 客单价 | 成交总金额 / 支付人数 = 平均每个支付用户花了多少钱 | `GMV / 支付人数` | — |
| 18 | 笔单价 | 成交总金额 / 支付订单数 = 平均每笔订单金额 | `GMV / 支付订单数` | — |
| 19 | 件单价 | 成交总金额 / 销量 = 平均每件商品单价 | `GMV / 销量` | — |
| 20 | 连带率 | 销量 / 支付订单数 = 平均每笔订单买了几件商品 | `SUM(pay_item_cnt) / 支付订单数` | >1 说明有凑单行为 |
| 21 | 退款率 | 退款金额 / GMV = 有多大比例的成交金额被退掉了 | `SUM(refund_amt) / SUM(gmv)` | 统一使用金额口径 |
| 22 | 下单→支付转化率 | [默认UV] 支付人数 / 下单人数 = 提交订单后实际完成支付的用户比例 | `支付人数 / 下单人数` | [备选PV] 支付订单数 / 下单订单数 |
| 23 | 整体转化率 | [默认UV] 支付人数 / 访问人数 = 进入商城的访客中有多大比例完成了购买 | `pay_uv / visit_uv` | [备选PV] 支付订单数 / 访问次数 |
| 24 | 加购转化率 | [默认UV] 支付人数 / 加购人数 = 加购后完成购买的用户比例 | `pay_uv / cart_uv` | [备选PV] 支付订单数 / 加购次数；替代原"点击转化率" |

---

## 二、商品域

### 2.1 品类维度

来源表：`app_commodity_stat_category_di`（天×品类粒度）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 26 | 品类曝光总次数 | 该品类下商品卡在列表页被展示的总次数（不去重） | `BITMAP_COUNT(BITMAP_UNION(expose_pv))` | BITMAP |
| 27 | 品类曝光去重用户数 | 看到过该品类商品卡的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(expose_uv))` | Bitmap 去重 |
| 28 | 品类点击次数 | 该品类商品卡被点击的总次数（不去重） | `BITMAP_COUNT(BITMAP_UNION(click_pv))` | BITMAP |
| 29 | 品类点击人数 | 点击过该品类商品卡的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(click_uv))` | Bitmap 去重 |
| 30 | 品类加购次数 | 该品类商品被加入购物车的总次数（不去重） | `BITMAP_COUNT(BITMAP_UNION(addcart_pv))` | BITMAP |
| 31 | 品类加购人数 | 加购过该品类商品的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(addcart_uv))` | Bitmap 去重 |
| 32 | 品类成交人数 | 购买过该品类商品的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv))` | Bitmap 去重 |
| 33 | 品类成交订单数 | 该品类的成交订单总数 | `SUM(pay_order_cnt)` | BIGINT 直接 SUM |
| 34 | 品类销量 | 该品类售出的商品总件数 | `SUM(pay_quantity)` | BIGINT |
| 35 | 品类 GMV | 该品类的成交总金额 | `SUM(gmv)` | 单位：元 |
| 36 | CTR（点击率） | [默认UV] 点击人数 / 曝光去重用户数 = 看到商品卡后点击进入详情的用户比例 | `点击人数 / 曝光去重用户数` | [备选PV] 点击次数 / 曝光总次数 |
| 37 | 加购率 | [默认UV] 加购人数 / 点击人数 = 点击商品后加入购物车的用户比例 | `加购人数 / 点击人数` | [备选PV] 加购次数 / 点击次数 |
| 38 | CVR（转化率） | [默认UV] 成交人数 / 曝光去重用户数 = 看到商品卡后最终购买的用户比例 | `成交人数 / 曝光去重用户数` | [备选PV] 成交订单数 / 曝光总次数 |
| 39 | 加购转化率 | [默认UV] 加购人数 / 点击人数 = 点击商品后加购的用户比例 | `加购人数 / 点击人数` | [备选PV] 加购次数 / 点击次数 |
| 39a | UV 价值 | 品类 GMV / 品类曝光去重用户数 = 每个曝光用户平均带来多少成交金额 | `SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(expose_uv))` | 分母为曝光UV（非 click_uv） |
| 39b | 用户渗透率 | 品类成交人数 / 全站支付人数 = 该品类在全站买家中的覆盖比例 | `品类 pay_uv / 全站 pay_uv` | 需跨表：分子品类表，分母大盘表 |

> ⚠️ 品类表**无**退款字段，品类退款分析须用 SPU 表按品类聚合。

### 2.2 SPU 维度

来源表：`app_commodity_stat_spu_di`（天×SPU 粒度）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 40 | SPU 曝光次数 | 该 SPU 商品卡在列表页被展示的总次数 | `BITMAP_COUNT(BITMAP_UNION(expose_pv))` | 同品类表 |
| 41 | SPU 曝光人数 | 看到过该 SPU 商品卡的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(expose_uv))` | — |
| 42 | SPU 点击次数 | 该 SPU 商品卡被点击的总次数 | `BITMAP_COUNT(BITMAP_UNION(click_pv))` | — |
| 43 | SPU 点击人数 | 点击过该 SPU 商品卡的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(click_uv))` | — |
| 44 | SPU 加购次数 | 该 SPU 被加入购物车的总次数 | `BITMAP_COUNT(BITMAP_UNION(addcart_pv))` | — |
| 45 | SPU 加购人数 | 加购过该 SPU 的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(addcart_uv))` | — |
| 46 | SPU 成交人数 | 购买过该 SPU 的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv))` | — |
| 47 | SPU 成交订单数 | 该 SPU 的成交订单总数 | `SUM(pay_order_cnt)` | BIGINT |
| 48 | SPU 销量 | 该 SPU 售出的总件数 | `SUM(pay_quantity)` | — |
| 49 | SPU GMV | 该 SPU 的成交总金额 | `SUM(gmv)` | 单位：元 |
| 50 | SPU 退款金额 | 该 SPU 已退款的总金额 | `SUM(refund_amt)` | 单位：元，仅 SPU 表有 |
| 51 | SPU 退款件数 | 该 SPU 已退款的商品件数 | `SUM(refund_quantity)` | — |
| 52 | SPU 退款率 | 退款金额 / GMV = 该 SPU 有多大比例的成交金额被退掉了 | `退款金额 / GMV` | ⚠️ 仅金额口径（SPU 表无 refund_uv，无法计算人数口径） |
| 53 | SPU CTR | [默认UV] 点击人数 / 曝光去重用户数 = 该 SPU 的商品卡点击率 | `点击人数 / 曝光去重用户数` | [备选PV] 点击次数 / 曝光总次数 |
| 54 | SPU CVR | [默认UV] 成交人数 / 曝光去重用户数 = 该 SPU 从曝光到成交的转化率 | `成交人数 / 曝光去重用户数` | [备选PV] 成交订单数 / 曝光总次数 |

> 额外维度字段：`category_name1`（一级品类）。基座 2.0 已移除 `price_tier`、`is_new` 字段。

---

## 三、用户域

### 3.1 用户分群维度

来源表：`app_user_stat_di`（天×tag_type×tag_value）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 55 | 新客支付人数 | 统计周期内首次购买的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv)) WHERE tag_type='user_order_type' AND tag_value='新客'` | — |
| 56 | 老客支付人数 | 统计周期内非首次购买的去重用户数 | 同上，`tag_value='老客'` | — |
| 57 | 新客占比 | 新客支付人数 / 总支付人数 = 新客在成交用户中的比例 | `新客 pay_uv / 总 pay_uv` | — |
| 58 | 分群 GMV | 某用户分群（新老客/生命周期/RFM/来源/会员等级）的成交总金额 | `SUM(total_gmv) WHERE tag_type='xxx'` | 按 user_order_type / lifecycle / rfm / source / member_level 切 |
| 59 | 分群客单价 | 该分群的 GMV / 该分群的支付人数 = 该类用户平均每人花多少 | `分群 GMV / 分群支付人数` | — |
| 60 | 生命周期分布 | 各生命周期阶段的支付人数占比（引入期/成长期/成熟期/流失期） | 各 lifecycle tag_value 的 pay_uv 占比 | tag_type='lifecycle' |
| 61 | RFM 分布 | 各 RFM 等级的支付人数占比（重要价值/一般发展/流失客户等） | 各 rfm tag_value 的 pay_uv 占比 | tag_type='rfm' |
| 61a | 来源渠道分布 | 各注册来源的支付人数占比 | 各 source tag_value 的 pay_uv 占比 | tag_type='source' |
| 61b | 会员等级分布 | 各会员等级的支付人数占比 | 各 member_level tag_value 的 pay_uv 占比 | tag_type='member_level' |

> ⚠️ 查询时**必须** `WHERE tag_type='xxx'`，禁止跨 tag_type SUM。
> tag_type 枚举：`user_order_type` / `lifecycle` / `rfm` / `source` / `member_level`。
> 销量字段为 `total_pay_quantity`（非 sales_qty）。

### 3.2 留存复购维度

来源表：`dws_user_cohort_metrics_di`（Cohort日期×分群）

| # | 指标名 | 口径说明（分子 / 分母） | 计算逻辑 | 备注 |
|---|--------|------------------------|----------|------|
| 62 | Cohort 用户数 | 某天（Cohort日期）首次触达的用户总数 | `SUM(cohort_uv)` | — |
| 63 | D+1 访问留存率 | D+1 天仍有访问的用户数 / Cohort 用户数 = 次日回访比例 | `visit_retain_d1 / cohort_uv` | — |
| 64 | D+7 访问留存率 | D+7 天仍有访问的用户数 / Cohort 用户数 = 7 日回访比例 | `visit_retain_d7 / cohort_uv` | — |
| 65 | D+30 访问留存率 | D+30 天仍有访问的用户数 / Cohort 用户数 = 30 日回访比例 | `visit_retain_d30 / cohort_uv` | — |
| 66 | D+7 复购率 | D+7 天内再次购买的用户数 / Cohort 用户数 = 7 日复购比例 | `repurchase_d7 / cohort_uv` | — |
| 67 | D+30 复购率 | D+30 天内再次购买的用户数 / Cohort 用户数 = 30 日复购比例 | `repurchase_d30 / cohort_uv` | — |
| 68 | 期间复购率 | 购买≥2次的用户数 / 总购买用户数 = 有多大比例的买家是回头客 | `multi_buy_uv / period_buyers` | — |
| 69 | 人均购买次数 | 总购买次数 / 总购买用户数 = 平均每个买家下了几单 | `total_orders / period_buyers` | — |

---

## 四、营促销域

### 4.1 渠道维度

来源表：`app_market_channel_stat_di`（天×渠道ID）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 70 | 渠道浏览量 | 某渠道带来的页面浏览总次数（不去重） | `SUM(browse_pv)` | — |
| 71 | 渠道访客数 | 通过某渠道进入商城的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(browse_uv))` | BITMAP |
| 72 | 渠道成交人数 | 通过某渠道进入并完成购买的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv))` | BITMAP |
| 73 | 渠道成交金额 | 某渠道带来的成交总金额 | `SUM(total_gmv)` | 单位：元 |
| 73a | 渠道退款金额 | 某渠道的退款总金额 | `SUM(refund_amt)` | 单位：元 |
| 74 | 渠道转化率 | [默认UV] 渠道成交人数 / 渠道访客数 | `pay_uv / browse_uv` | [备选PV] 渠道成交订单数 / 渠道浏览量 |

### 4.2 活动维度

来源表：`app_market_stat_promotion_di`（天×活动ID，MV）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 75 | 活动参与人数 | 参与某活动的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(participate_uv))` | BITMAP |
| 76 | 活动成交金额 | 某活动带来的成交总金额（元） | `SUM(promotion_gmv)` | 已转元 |
| 77 | 活动补贴金额 | 平台在某活动中发放的补贴总金额（元） | `SUM(promotion_discount_amt)` | 已转元 |
| 78 | 活动发券量 | 某活动发放的优惠券总张数 | `SUM(coupon_issue_cnt)` | — |
| 78a | 活动用券数 | 某活动中实际被使用的券张数（去重） | `BITMAP_COUNT(BITMAP_UNION(coupon_use_cnt))` | BITMAP |
| 79 | 活动 ROI | 活动成交金额 / 活动补贴金额 = 每补贴 1 元撬动了多少成交 | `SUM(promotion_gmv) / NULLIF(SUM(promotion_discount_amt), 0)` | — |
| 79a | 活动人均消费 | 活动成交金额 / 活动参与人数 | `SUM(promotion_gmv) / NULLIF(BITMAP_COUNT(BITMAP_UNION(participate_uv)), 0)` | — |
| 79b | 活动补贴率 | 补贴金额 / (成交金额+补贴金额) | `SUM(promotion_discount_amt) / NULLIF(SUM(promotion_gmv) + SUM(promotion_discount_amt), 0)` | — |

> 基座 2.0 已下线 `dwm_market_activity_detail_di`（活动×SPU 明细），活动×商品交叉分析直接通过 `app_market_stat_promotion_di` + `app_commodity_stat_spu_di` 关联即可。

### 4.3 优惠券维度

来源表：
- `app_market_stat_coupon_overview_di`（天×门店×券类型）：用于券整体概览、按券类型分析
- `app_market_stat_coupon_di`（天×门店×券批次）：用于券模板列表、券批次漏斗下钻

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 80 | 领取量 | 优惠券被领取的总张数（去重） | `BITMAP_COUNT(BITMAP_UNION(acquire_cnt))` | BITMAP；概览表领取指标跨门店冗余，需用 BITMAP 去重 |
| 81 | 领取人数 | 领取过优惠券的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(acquire_uv))` | BITMAP |
| 82 | 核销量 | 优惠券被使用的总张数（去重） | `BITMAP_COUNT(BITMAP_UNION(use_cnt))` | BITMAP |
| 83 | 核销人数 | 使用过优惠券的去重用户数 | `BITMAP_COUNT(BITMAP_UNION(use_uv))` | BITMAP |
| 84 | 领券核销率 | 核销量 / 领取量 | `BITMAP_COUNT(BITMAP_UNION(use_cnt)) / NULLIF(BITMAP_COUNT(BITMAP_UNION(acquire_cnt)), 0)` | — |
| 86 | 用券成交金额 | 使用优惠券订单带来的成交金额 | `SUM(pay_amt) / 100.0` | 金额字段单位为分，输出转元 |
| 86a | 券优惠成本 | 核销券优惠成本 | 跨门店聚合时先按天×券类型/券批次 `MAX(coupon_cost_amt) / 100.0` 去重，再跨天求和 | 领取/使用/成本映射到门店桶，禁止直接跨门店 SUM |
| 87 | 券基础信息 | 券名称 / 券类型 / 发行总量 | `MAX(template_name)` / `MAX(coupon_type)` / `MAX(issue_cnt)` | 券名称和发行总量仅券批次列表表提供 |

### 4.4 分销（CPS）维度

来源表：`app_market_stat_cps_di`（天×推广人粒度，MV）

| # | 指标名 | 口径说明 | 计算逻辑 | 备注 |
|---|--------|----------|----------|------|
| 88 | 分销订单数 | CPS 推广产生的订单数（去重） | `BITMAP_COUNT(BITMAP_UNION(order_cnt))` | BITMAP |
| 89 | 分销支付人数 | 通过 CPS 推广完成支付的用户数 | `BITMAP_COUNT(BITMAP_UNION(order_uv))` | BITMAP |
| 90 | 分销 GMV | 通过 CPS 推广产生的成交金额 | `SUM(cps_gmv)` | 单位：元 |
| 91 | 结算单数 | 已结算的 CPS 订单数 | `BITMAP_COUNT(BITMAP_UNION(settle_cnt))` | BITMAP |
| 92 | 结算佣金 | 已结算的佣金总额 | `SUM(settle_commission)` | 单位：元 |
| 93 | 佣金总额 | 平台支付给推广人的佣金总和（含未结算） | `SUM(total_commission)` | 单位：元 |
| 94 | 分销 ROI | 分销 GMV / 佣金总额 = 每支出 1 元佣金撬动了多少成交 | `SUM(cps_gmv) / NULLIF(SUM(total_commission), 0)` | — |
| 96 | 人均佣金 | 佣金总额 / 推广人数 = 平均每个推广人赚了多少佣金 | `SUM(total_commission) / COUNT(DISTINCT promoter_uid)` | — |
| 97 | 推广人数 | 统计周期内有推广记录的去重推广人数 | `COUNT(DISTINCT promoter_uid)` | — |

---
## 五、跨域同名指标消歧

多域共有的指标名，口径或粒度不同，路由时必须区分：

| 用户说 | 交易域 | 商品域 | 营促销域 | 判定规则 |
|--------|--------|--------|---------|---------|
| "转化率" | pay_uv / visit_uv（访问→支付） | pay_uv / expose_uv（曝光→支付） | pay_uv / browse_uv（按渠道切） | 无修饰→交易域；含商品/品类→商品域；含渠道→营促销域 |
| "PV"/"页面浏览次数" | 商城整体页面浏览次数 | 商品卡曝光次数（expose_pv） | 各渠道页面浏览次数 | 同上 |
| "UV"/"页面浏览人数" | 商城整体页面浏览人数 | 商品卡曝光人数（expose_uv） | 各渠道页面浏览人数 | 同上 |
| "点击" | ⚠️ 概览表已无 click_pv/click_uv，建议改用"加购"（cart_pv/cart_uv） | SPU 级 click_pv | — | 用户提到大盘"点击"时主动澄清 |
| "退款率" | refund_amt / gmv（金额口径） | refund_amt / gmv（SPU 级金额口径） | — | 无修饰→交易域；含商品→商品域 |
| "注册人数" | 大盘当天新注册 | — | 各渠道注册 | 无修饰→交易域；含渠道→营促销域 |

**转化率消歧决策树**（用户说"转化率"时）：

```
├─ 含"商品/品类/SPU/CTR/CVR" → 商品域 CVR
├─ 含"渠道/各渠道" → 营促销域 渠道转化率
├─ 含"分销/推广" → 营促销域 分销转化率
├─ 含"下单/支付率" → 交易域 下单→支付转化率
├─ 含"加购转化率" → 交易域 加购转化率（pay_uv / cart_uv）
└─ 无修饰词 → 交易域 整体转化率（pay_uv / visit_uv）
```

---

## 六、常见说法→指标别名映射（交易域内部，避免口径混淆）

> 供指标字典查询（`当前运行时的 Capability 分析执行器` 的 `metric_search` action）精确匹配使用：用户口语化说法需先在此对上标准指标名，否则会被误判为"查不到"。

| 用户说法 | 映射到 | 判定依据 |
|---------|--------|---------|
| 平均一单多少钱 / 客单价（口语误用） | 笔单价（#18） | "一单"对应订单维度，分母应是支付订单数，不是支付人数 |
| 人均消费 / 花了多少钱 / 平均每人花多少 | 客单价（#17） | "人均"对应用户维度，分母应是支付人数 |
