# 🏅 分类十一：会员分析

## 📌 两张会员表的使用分工

| 场景 | 使用表 | 原因 |
|------|-------|------|
| **用户画像**（性别/年龄/地域/来源/卡类型） | `dm.v_crm_member_with_sly` | 静态属性，全量注册会员，不依赖日期 |
| **生命周期/注册趋势** | `dm.v_crm_member_with_sly` | `mem_create_time` 注册时间更准确 |
| **流失预警** | `dm.v_crm_member_with_sly` | `last_consume_time` 直接取，无需扫行为表 |
| **RFM/价值分层（R）** | `dm.v_crm_member_with_sly` | `last_consume_time` 取最近消费时间 |
| **RFM/价值分层（F/M）** | `dm.dm_crm_card_sum_day_p_store` | 统计指定周期内的消费频次/金额 |
| **消费/储值/积分/用券行为统计** | `dm.dm_crm_card_sum_day_p_store` | 行为记录，必须带日期过滤 |
| **会员排行** | `dm.dm_crm_card_sum_day_p_store` | 统计期间消费金额/次数排名 |
| **复购/留存率** | `dm.dm_crm_card_sum_day_p_store` | 跨期消费行为判断 |
| **卡型分布/持卡结构** | `dm.v_crm_member_with_sly` | `mem_card_type`/`card_num` 静态属性 |
| **跨品牌多卡会员** | `dm.v_crm_member_with_sly` | `mem_card_type` 含 `\|\|` 即多卡会员，`card_num` 持卡数 |
| **余额分布/沉睡资金** | `dm.v_crm_member_with_sly` | `balance_principal`/`balance_gift`/`balance_score` 余额字段 |

> ⚠️ 重要约束：
> 1. **`dm_crm_card_sum_day_p_store` 里的会员不是所有注册会员！** 是**有过消费/储值/积分等行为**的会员
>    - 没有"从未消费过的注册会员"
>    - "会员总量"≠注册会员总数，而是"有行为记录的会员数"
>    - "沉睡会员"=行为间隔超过N天，不是"从未出现过"
>    - ⚠️ 会员类型名词（消费会员/储值会员/积分会员）不加"活跃"前缀；作为统计指标时需加
> 2. `is_new` = "新会员"：日汇总表中**本期新注册的会员**；推荐用维表 `mem_create_time` 更精准
> 3. 日汇总表必须带 `coupon_date` 日期过滤（强制，未指定则询问）
> 4. **统一编码（2026-06-30 实施）**：所有 7 张表均含 `group_code`（集团 G 号）+ `store_code`（门店 C 号），直接 JOIN 即可，无需 `o2o_` 系列字段中转
> 5. 必须带 `LIMIT`
> 6. 会员维度必须 `COUNT(DISTINCT mem_code)` 去重
> 7. **日汇总表默认取交易门店**（`store_code`）数据；如用户需要注册门店或售卡门店维度，需主动询问

---

# 🍽️ 主题一：消费行为分析

## Intent 76: MemberConsumeOverview — 会员消费概况

**触发**：会员消费概况/会员消费统计/消费会员分析/会员贡献

**业务说明**：综合展示有消费行为的会员指标，包括消费会员数、实收金额、人均消费、单均等。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 集团/省份/城市/门店/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN consume_count > 0 THEN mem_code END) AS 消费会员数,
    SUM(consume_count) AS 消费笔数,
    SUM(people_qty) AS 消费人次,
    ROUND(SUM(busi_income), 2) AS 会员实收金额,
    ROUND(SUM(recv_money), 2) AS 营业应收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(consume_count), 0), 2) AS 会员单均消费,
    ROUND(SUM(busi_income) / NULLIF(SUM(people_qty), 0), 2) AS 会员人均消费,
    SUM(dinner_time) AS 用餐时长,
    SUM(star_times) AS 评价次数
FROM dm.dm_crm_card_sum_day_p_store t
LEFT JOIN e000.dt_store_view s
    ON t.group_code = s.group_code
   AND t.store_code = s.store_code
WHERE t.group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND t.store_code IN (#{omShopCodes})
AND t.coupon_date >= :start_date
    AND t.coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 会员实收金额 DESC
LIMIT 50;
```

**输出格式**：表格（维度 / 消费会员数 / 消费笔数 / 消费人次 / 实收金额 / 应收金额 / 单均消费 / 人均消费）

---

## Intent 77: MemberConsumeRanking — 会员消费排行

**触发**：会员消费排行/高价值会员/最消费的会员/会员贡献排名

**业务说明**：按消费金额/消费次数排名，找出高价值消费会员。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `rank_by` | Enum | 实收金额/应收金额/消费笔数/消费天数 | 排行维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    mem_res_name AS 会员姓名,
    mem_store_name AS 入会门店,
    COUNT(DISTINCT coupon_date) AS 消费天数,
    SUM(consume_count) AS 消费笔数,
    SUM(people_qty) AS 消费人次,
    ROUND(SUM(recv_money), 2) AS 营业应收,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(consume_count), 0), 2) AS 单均消费
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
GROUP BY mem_code, mem_res_name, mem_store_name
ORDER BY {{rank_by:实收金额}} DESC
LIMIT {{top_n:20}};
```

**输出格式**：排行榜（会员姓名 / 入会门店 / 消费天数 / 消费笔数 / 消费人次 / 应收金额 / 实收金额 / 单均消费）

---

## Intent 78: MemberConsumeFrequency — 会员消费频次分析

**触发**：会员频次/消费频次/来几次/月均消费次数/消费分布

**业务说明**：分析有消费行为的会员频次分布，识别高频活跃会员和低频沉默会员。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN 消费天数 = 1 THEN mem_code END) AS 来1次,
    COUNT(DISTINCT CASE WHEN 消费天数 BETWEEN 2 AND 3 THEN mem_code END) AS 来2-3次,
    COUNT(DISTINCT CASE WHEN 消费天数 BETWEEN 4 AND 6 THEN mem_code END) AS 来4-6次,
    COUNT(DISTINCT CASE WHEN 消费天数 > 6 THEN mem_code END) AS 来7次以上,
    COUNT(DISTINCT mem_code) AS 消费会员总数,
    ROUND(SUM(消费天数) / NULLIF(COUNT(DISTINCT mem_code), 0), 2) AS 人均消费天数
FROM (
    SELECT
        mem_code,
        store_code,
        COUNT(DISTINCT coupon_date) AS 消费天数
    FROM dm.dm_crm_card_sum_day_p_store
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
        AND store_code IN (#{omShopCodes})
        AND coupon_date >= :start_date
        AND coupon_date < :end_date_plus_1
    GROUP BY mem_code, store_code
) t
LEFT JOIN e000.dt_store_view s
    ON t.store_code = s.store_code
   AND s.group_code = '#{SL_UNIFIED_G_ID}'
    AND store_code IN (#{omShopCodes})
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
LIMIT 50;
```

**输出格式**：分布表格（维度 / 来1次 / 来2-3次 / 来4-6次 / 来7次以上 / 会员数 / 人均消费天数）

---

## Intent 79: MemberConsumePerTransaction — 会员单均消费分析

**触发**：会员单均/会员人均/单次消费/平均消费金额

**业务说明**：计算有消费行为会员的单次消费和人均消费水平，分析消费深度。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN consume_count > 0 THEN mem_code END) AS 消费会员数,
    SUM(consume_count) AS 总消费笔数,
    SUM(people_qty) AS 消费人次,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(consume_count), 0), 2) AS 会员单均消费,
    ROUND(SUM(busi_income) / NULLIF(SUM(people_qty), 0), 2) AS 会员人均消费,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT store_code), 0), 2) AS 店均会员实收
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 会员单均消费 DESC
LIMIT {{top_n:20}};
```

**输出格式**：表格（维度 / 消费会员数 / 总笔数 / 人次 / 实收金额 / 单均消费 / 人均消费 / 店均实收）

---

## Intent 80: MemberConsumeMoM — 会员消费趋势与环比

**触发**：会员消费趋势/月度会员营收/会员消费环比/会员增长情况

**业务说明**：分析有消费行为会员的营收趋势，并对比上一周期的变化。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 月/周/日 | 时间粒度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 当前周期（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板**：
```sql
WITH cur AS (
    SELECT
        SUBSTR(coupon_date, 1, {{group_by:7}}) AS 周期,
        COUNT(DISTINCT CASE WHEN consume_count > 0 THEN mem_code END) AS 消费会员数,
        SUM(consume_count) AS 消费笔数,
        SUM(busi_income) AS 实收金额
    FROM dm.dm_crm_card_sum_day_p_store
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
        AND coupon_date < :end_date_plus_1
        {{#if region}} AND province = :region
GROUP BY SUBSTR(coupon_date, 1, {{group_by:7}})
),
prev AS (
    SELECT
        SUBSTR(coupon_date, 1, {{group_by:7}}) AS 周期,
        COUNT(DISTINCT CASE WHEN consume_count > 0 THEN mem_code END) AS 上期会员数,
        SUM(busi_income) AS 上期实收
    FROM dm.dm_crm_card_sum_day_p_store
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND coupon_date >= DATE_SUB(:start_date, INTERVAL 1 {{group_by:1}})
        AND coupon_date < :start_date
        {{#if region}} AND province = :region
GROUP BY SUBSTR(coupon_date, 1, {{group_by:7}})
)
SELECT
    cur.周期 AS 周期,
    cur.消费会员数 AS 本期会员数,
    prev.上期会员数 AS 上期会员数,
    ROUND((cur.消费会员数 - prev.上期会员数) * 100.0 / NULLIF(prev.上期会员数, 0), 2) AS 会员环比%,
    cur.实收金额 AS 本期实收,
    prev.上期实收 AS 上期实收,
    ROUND((cur.实收金额 - prev.上期实收) * 100.0 / NULLIF(prev.上期实收, 0), 2) AS 营收环比%,
    ROUND(cur.实收金额 / NULLIF(cur.消费会员数, 0), 2) AS 本期人均
FROM cur
LEFT JOIN prev ON cur.周期 = prev.周期
ORDER BY cur.周期;
```

**输出格式**：对比表格（周期 / 本期会员 / 上期会员 / 会员环比% / 本期实收 / 上期实收 / 营收环比% / 本期人均）

---

# 💰 主题二：储值行为分析

## Intent 81: MemberRechargeOverview — 会员储值概况

**触发**：会员储值概况/充值统计/储值会员分析

**业务说明**：综合展示有储值行为的会员指标，包括储值会员数、实充金额、赠送金额、人均实充等。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END) AS 储值会员数,
    SUM(recharge_count) AS 充值笔数,
    ROUND(SUM(recharge_amount), 2) AS 充值总金额,
    ROUND(SUM(recharge_real_amount), 2) AS 实充金额,
    ROUND(SUM(recharge_donate_amount), 2) AS 储值赠送金额,
    ROUND(SUM(recharge_real_amount) / NULLIF(SUM(recharge_count), 0), 2) AS 单次实充金额,
    ROUND(SUM(recharge_real_amount) / NULLIF(COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END), 0), 2) AS 人均实充金额
FROM dm.dm_crm_card_sum_day_p_store t
LEFT JOIN e000.dt_store_view s
    ON t.group_code = s.group_code
   AND t.store_code = s.store_code
WHERE t.group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND t.store_code IN (#{omShopCodes})
    AND t.coupon_date >= :start_date
    AND t.coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 实充金额 DESC
LIMIT 50;
```

**输出格式**：表格（维度 / 储值会员数 / 充值笔数 / 充值总金额 / 实充金额 / 赠送金额 / 单次实充 / 人均实充）

---

## Intent 82: MemberRechargeRanking — 会员储值排行

**触发**：会员充值排行/充值最多/充值排名/储值金额排名

**业务说明**：按充值金额/充值次数排名，找出高储值会员。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `rank_by` | Enum | 实充金额/充值总金额/充值次数 | 排行维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    mem_res_name AS 会员姓名,
    mem_store_name AS 入会门店,
    SUM(recharge_count) AS 充值次数,
    ROUND(SUM(recharge_amount), 2) AS 充值总金额,
    ROUND(SUM(recharge_real_amount), 2) AS 实充金额,
    ROUND(SUM(recharge_donate_amount), 2) AS 赠送金额,
    ROUND(SUM(recharge_real_amount) / NULLIF(SUM(recharge_count), 0), 2) AS 单次实充
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
GROUP BY mem_code, mem_res_name, mem_store_name
HAVING SUM(recharge_count) > 0
ORDER BY {{rank_by:实充金额}} DESC
LIMIT {{top_n:20}};
```

**输出格式**：排行榜（会员姓名 / 入会门店 / 充值次数 / 充值总金额 / 实充金额 / 赠送金额 / 单次实充）

---

## Intent 83: MemberRechargeTrend — 会员储值趋势

**触发**：会员储值趋势/月度充值/充值变化/充值增长

**业务说明**：分析有储值行为会员的充值时间趋势，评估充值活动效果。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 月/周/日 | 时间粒度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板**：
```sql
SELECT
    SUBSTR(coupon_date, 1, {{group_by:7}}) AS 时间,
    COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END) AS 储值会员数,
    SUM(recharge_count) AS 充值笔数,
    ROUND(SUM(recharge_amount), 2) AS 充值总金额,
    ROUND(SUM(recharge_real_amount), 2) AS 实充金额,
    ROUND(SUM(recharge_donate_amount), 2) AS 赠送金额,
    ROUND(SUM(recharge_real_amount) / NULLIF(SUM(recharge_count), 0), 2) AS 单次实充金额
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
    {{#if region}} AND province = :region
GROUP BY SUBSTR(coupon_date, 1, {{group_by:7}})
ORDER BY 时间;
```

**输出格式**：趋势表格（时间 / 储值会员数 / 充值笔数 / 充值总金额 / 实充金额 / 赠送金额 / 单次实充）

---

## Intent 84: MemberRechargeRate — 会员充值渗透率

**触发**：会员充值率/充值转化/充值占比/有多少会员充值了

**业务说明**：分析有消费行为的会员中有多少同时进行了储值，衡量充值渗透率。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT mem_code) AS 消费会员数,
    COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END) AS 储值会员数,
    ROUND(COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END) * 100.0 /
        NULLIF(COUNT(DISTINCT mem_code), 0), 2) AS 充值渗透率%,
    ROUND(SUM(recharge_real_amount), 2) AS 实充总金额,
    ROUND(SUM(recharge_real_amount) / NULLIF(COUNT(DISTINCT CASE WHEN recharge_count > 0 THEN mem_code END), 0), 2) AS 人均实充
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 充值渗透率% DESC
LIMIT {{top_n:20}};
```

**输出格式**：表格（维度 / 消费会员数 / 储值会员数 / 充值渗透率% / 实充总金额 / 人均实充）

---

# 🎁 主题三：积分行为分析

## Intent 85: MemberScoreOverview — 会员积分概况

**触发**：会员积分概况/积分统计/积分会员分析

**业务说明**：综合展示有积分变动行为的会员指标，包括积分变动会员数、积分收支、积分存量等。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN score_in_num > 0 OR score_out_num > 0 THEN mem_code END) AS 积分变动会员数,
    ROUND(SUM(score_total_num), 2) AS 积分总量,
    ROUND(SUM(score_total_num) / NULLIF(COUNT(DISTINCT CASE WHEN score_in_num > 0 OR score_out_num > 0 THEN mem_code END), 0), 2) AS 人均积分,
    ROUND(SUM(score_in_num), 2) AS 积分收入总量,
    ROUND(SUM(score_out_num), 2) AS 积分支出总量,
    ROUND(SUM(score_in_num) - SUM(score_out_num), 2) AS 积分净增总量
FROM dm.dm_crm_card_sum_day_p_store t
LEFT JOIN e000.dt_store_view s
    ON t.group_code = s.group_code
   AND t.store_code = s.store_code
WHERE t.group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND t.store_code IN (#{omShopCodes})
    AND t.coupon_date >= :start_date
    AND t.coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 积分变动会员数 DESC
LIMIT 50;
```

**输出格式**：表格（维度 / 积分变动会员数 / 积分总量 / 人均积分 / 积分收入 / 积分支出 / 积分净增）

---

## Intent 86: MemberScoreFlow — 会员积分流转趋势

**触发**：积分流转/积分收支/月度积分/积分变化/积分趋势

**业务说明**：分析有积分变动行为会员的积分收支时间趋势，评估积分运营健康度。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 月/周/日 | 时间粒度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板**：
```sql
SELECT
    SUBSTR(coupon_date, 1, {{group_by:7}}) AS 时间,
    COUNT(DISTINCT CASE WHEN score_in_num > 0 THEN mem_code END) AS 积分获取会员数,
    COUNT(DISTINCT CASE WHEN score_out_num > 0 THEN mem_code END) AS 积分兑换会员数,
    ROUND(SUM(score_in_num), 2) AS 积分收入,
    ROUND(SUM(score_out_num), 2) AS 积分支出,
    ROUND(SUM(score_in_num) - SUM(score_out_num), 2) AS 积分净增,
    ROUND(SUM(score_in_count), 2) AS 积分获取笔数,
    ROUND(SUM(score_out_count), 2) AS 积分兑换笔数
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
    {{#if region}} AND province = :region
GROUP BY SUBSTR(coupon_date, 1, {{group_by:7}})
ORDER BY 时间;
```

**输出格式**：趋势表格（时间 / 积分获取会员数 / 积分消耗会员数 / 积分收入 / 积分支出 / 积分净增 / 获取笔数 / 消耗笔数）

---

## Intent 87: MemberScoreBalance — 会员积分余额分布

**触发**：积分余额/积分存量/积分分布/人均积分

**业务说明**：按门店/区域统计有积分行为会员的积分总量和人均积分分布。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填，取截止日余额） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN score_total_num > 0 THEN mem_code END) AS 积分余额会员数,
    ROUND(SUM(score_total_num), 2) AS 积分总量,
    ROUND(SUM(score_total_num) / NULLIF(COUNT(DISTINCT CASE WHEN score_total_num > 0 THEN mem_code END), 0), 2) AS 人均积分
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 积分总量 DESC
LIMIT {{top_n:20}};
```

**输出格式**：表格（维度 / 积分余额会员数 / 积分总量 / 人均积分）

---

# 👤 主题四：用户画像分析

> ⚠️ **表说明**：画像分析使用 `dm.v_crm_member_with_sly`（会员维表），统计**全量注册会员**的静态属性分布，不依赖行为日期过滤。与日汇总表的区别：
> - 维表：反映**注册会员**的年龄/性别/地域/来源/卡类型等静态属性
> - 日汇总表：反映**有交易行为**的会员的消费行为

## Intent 88: MemberPortrait — 会员画像分析

**触发**：会员画像/年龄分布/性别分布/地域分布/来源分布/会员结构/注册会员分析

**业务说明**：基于**全量注册会员**展示年龄、性别、地域、来源渠道、卡类型等静态画像分布，用于精准营销人群定位。数据来源为会员维表，不受日期过滤影响。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 年龄段/性别/省份/城市/来源渠道/卡类型/会员状态 | 画像维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（年龄分布）**：
```sql
SELECT
    CASE
        WHEN mem_age >= 0 AND mem_age < 18 THEN '17岁及以下'
        WHEN mem_age >= 18 AND mem_age < 25 THEN '18-24岁'
        WHEN mem_age >= 25 AND mem_age < 35 THEN '25-34岁'
        WHEN mem_age >= 35 AND mem_age < 45 THEN '35-44岁'
        WHEN mem_age >= 45 AND mem_age < 55 THEN '45-54岁'
        WHEN mem_age >= 55 AND mem_age < 65 THEN '55-64岁'
        WHEN mem_age >= 65 THEN '65岁及以上'
        ELSE '年龄未知'
    END AS 年龄段,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码，维表.group_code = 统一码）
 AND store_code IN (#{omShopCodes})
AND (mem_status IS NULL OR mem_status = '正常')
GROUP BY 年龄段
ORDER BY 会员数 DESC;
```

**SQL 模板（性别/省份/城市/来源渠道/卡类型/会员状态）**：
```sql
SELECT
    {{group_by:mem_sex}} AS 维度,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码，维表.group_code = 统一码）
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY {{group_by:mem_sex}}
ORDER BY 会员数 DESC
LIMIT {{top_n:20}};
```

**group_by 枚举对照**：

| 用户说的 | 对应字段 |
|---------|---------|
| 性别 | `mem_sex` |
| 省份/地域 | `mem_province` |
| 城市 | `mem_city` |
| 来源渠道 | `mem_res_name` |
| 卡类型 | `mem_card_type` |
| 会员状态 | `mem_status` |

**输出格式**：画像表格（维度 / 会员数 / 占比%）

---

# 🔄 主题五：用户生命周期分析

> ⚠️ **表说明**：
> - **注册趋势/生命周期阶段分析**：使用 `dm.v_crm_member_with_sly`（会员维表），基于 `mem_create_time` 注册时间，反映**全量注册会员**的生命阶段
> - **留存/复购/流失预警**：使用 `dm.dm_crm_card_sum_day_p_store`（日汇总表），基于 `last_consume_time` 最后消费时间

## Intent 89: MemberLifecycle — 会员生命周期分析

**触发**：会员生命周期/新增会员趋势/会员注册增长/新注册会员数/会员增长情况

**业务说明**：基于**全量注册会员**分析注册趋势与生命周期阶段分布。使用会员维表的 `mem_create_time` 注册时间，比日汇总表的 `is_new` 字段更准确。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 月/周/日 | 时间粒度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 注册日期范围（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板（注册趋势）**：
```sql
SELECT
    SUBSTR(mem_create_time, 1, {{group_by:7}}) AS 时间,
    COUNT(DISTINCT mem_code) AS 新注册会员数,
    COUNT(DISTINCT CASE WHEN mem_card_type LIKE '%储值%' THEN mem_code END) AS 储值卡会员数,
    COUNT(DISTINCT CASE WHEN mem_card_type LIKE '%积分%' OR mem_card_type LIKE '%普通%' THEN mem_code END) AS 积分卡会员数
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND mem_create_time >= :start_date
    AND mem_create_time < :end_date_plus_1
    {{#if region}} AND (mem_province = :region OR mem_city = :region)
AND (mem_status IS NULL OR mem_status = '正常')
GROUP BY SUBSTR(mem_create_time, 1, {{group_by:7}})
ORDER BY 时间;
```

**SQL 模板（生命周期阶段分布，截至某日）**：
```sql
SELECT
    CASE
        WHEN first_consume_time IS NULL THEN '从未消费'
        WHEN DATEDIFF(:end_date, last_consume_time) <= 30 THEN '活跃（30天内消费）'
        WHEN DATEDIFF(:end_date, last_consume_time) <= 90 THEN '沉默（31-90天）'
        WHEN DATEDIFF(:end_date, last_consume_time) <= 180 THEN '睡眠（91-180天）'
        ELSE '流失（180天以上）'
    END AS 生命周期阶段,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY 生命周期阶段
ORDER BY 会员数 DESC;
```

**输出格式**：
- 注册趋势：趋势表格（时间 / 新注册会员数 / 储值卡会员数 / 积分卡会员数）
- 阶段分布：分层表格（生命周期阶段 / 会员数 / 占比%）

---

## Intent 90: MemberRetention — 会员留存率分析

**触发**：会员留存/复购率/留存率/月留存

**业务说明**：计算指定周期内新注册会员在后续周期是否继续有消费行为（即是否"留存"）。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 分析周期（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板**：
```sql
WITH 新会员 AS (
    SELECT
        mem_code,
        store_code,
        MIN(coupon_date) AS 首次消费日
    FROM dm.dm_crm_card_sum_day_p_store
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
        AND store_code IN (#{omShopCodes})
        AND coupon_date >= :start_date
        AND coupon_date < :end_date_plus_1
        AND is_new = '新会员'
        {{#if region}} AND province = :region
GROUP BY mem_code, store_code
),
周期 AS (
    SELECT
        t.mem_code,
        t.store_code,
        COUNT(DISTINCT SUBSTR(p.coupon_date, 1, 7)) AS 消费月数
    FROM 新会员 t
    JOIN dm.dm_crm_card_sum_day_p_store p
        ON t.mem_code = p.mem_code
        AND t.store_code = p.store_code
        AND p.group_code = '#{SL_UNIFIED_G_ID}'
         AND store_code IN (#{omShopCodes})
AND p.coupon_date >= :start_date
        AND p.coupon_date < :end_date_plus_1
    GROUP BY t.mem_code, t.store_code
)
SELECT
    '新注册会员' AS 群体,
    COUNT(*) AS 新会员总数,
    COUNT(CASE WHEN 消费月数 >= 1 THEN 1 END) AS 次月留存数,
    ROUND(COUNT(CASE WHEN 消费月数 >= 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS 次月留存率%
FROM 周期;
```

**输出格式**：留存表格（群体 / 新会员总数 / 次月留存数 / 次月留存率%）

---

## Intent 91: MemberRepurchase — 会员复购分析

**触发**：复购会员/多次消费/回头客/月复购/高复购会员

**业务说明**：统计有消费行为的会员中，消费2次及以上的会员数量及贡献，衡量会员粘性。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT mem_code) AS 消费会员总数,
    COUNT(DISTINCT CASE WHEN 消费次数 >= 2 THEN mem_code END) AS 复购会员数,
    ROUND(COUNT(DISTINCT CASE WHEN 消费次数 >= 2 THEN mem_code END) * 100.0 /
        NULLIF(COUNT(DISTINCT mem_code), 0), 2) AS 复购率%,
    ROUND(SUM(busi_income), 2) AS 总实收,
    ROUND(SUM(CASE WHEN 消费次数 >= 2 THEN busi_income ELSE 0 END), 2) AS 复购实收,
    ROUND(SUM(CASE WHEN 消费次数 >= 2 THEN busi_income ELSE 0 END) * 100.0 /
        NULLIF(SUM(busi_income), 0), 2) AS 复购营收占比%
FROM (
    SELECT
        mem_code,
        store_code,
        SUM(consume_count) AS 消费次数,
        SUM(busi_income) AS busi_income
    FROM dm.dm_crm_card_sum_day_p_store
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
        AND coupon_date < :end_date_plus_1
    GROUP BY mem_code, store_code
) t
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 复购率% DESC
LIMIT {{top_n:20}};
```

**输出格式**：复购表格（维度 / 消费会员总数 / 复购会员数 / 复购率% / 总实收 / 复购实收 / 复购营收占比%）

---

## Intent 92: MemberDormant — 会员流失预警

**触发**：沉睡会员/会员流失/很久没来/不活跃会员/流失预警/多久没消费

**业务说明**：识别距今天数超过阈值（如90天）未消费的会员，帮助运营做流失挽回触达。使用会员维表的 `last_consume_time` 直接计算，效率更高。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `days` | Integer | 默认90 | 流失天数阈值 |
| `group_by` | Enum | 门店/省份/城市 | 聚合维度 |
| `as_of_date` | Date | YYYY-MM-DD | 基准日期（默认取今日） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（汇总统计）**：
```sql
SELECT
    {{group_by:store_code}} AS 维度编码,
    {{group_by:store_code}} AS 维度,
    COUNT(DISTINCT mem_code) AS 流失会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 流失占比%,
    ROUND(AVG(DATEDIFF(:as_of_date, last_consume_time)), 0) AS 平均流失天数,
    MAX(DATEDIFF(:as_of_date, last_consume_time)) AS 最长流失天数
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND last_consume_time IS NOT NULL
    AND DATEDIFF(:as_of_date, last_consume_time) >= :days
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY {{group_by:store_code}}
ORDER BY 流失会员数 DESC
LIMIT {{top_n:20}};
```

**SQL 模板（流失会员明细，用于触达名单）**：
```sql
SELECT
    mem_code AS 会员编码,
    mem_name AS 会员姓名,
    CONCAT(LEFT(mem_mobile, 3), '****', RIGHT(mem_mobile, 4)) AS 手机号,
    store_code AS 注册门店编码,
    mem_card_type AS 卡类型,
    last_consume_time AS 最后消费时间,
    DATEDIFF(:as_of_date, last_consume_time) AS 距今天数,
    balance_principal AS 储值本金余额,
    balance_score AS 积分余额
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND last_consume_time IS NOT NULL
    AND DATEDIFF(:as_of_date, last_consume_time) >= :days
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
ORDER BY 距今天数 DESC
LIMIT {{top_n:50}};
```

**输出格式**：
- 汇总：流失预警表格（维度 / 流失会员数 / 流失占比% / 平均流失天数 / 最长流失天数）
- 明细：名单表格（会员编码 / 会员姓名 / 手机号 / 注册门店 / 卡类型 / 最后消费时间 / 距今天数 / 储值余额 / 积分余额）

---

## Intent 93: MemberValueSegmentation — 会员价值分层（RFM）

**触发**：会员分层/会员价值/高价值会员/RFM/价值分层/重要价值/一般价值

**业务说明**：基于 RFM 模型将会员分层。**R 使用维表 `last_consume_time`**（全量会员，含近期无行为的），**F/M 使用日汇总表**聚合指定周期内的消费频次和金额，两表通过 `mem_code` 关联，覆盖更完整。

**RFM模型**：
- **R（Recency）**：最近消费距今天数（来自维表 `last_consume_time`），越小越高价值
- **F（Frequency）**：指定周期内消费频次（来自日汇总表 `consume_count`），越高越高价值
- **M（Monetary）**：指定周期内消费金额（来自日汇总表 `busi_income`），越高越高价值

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/省份/城市/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | F/M 统计周期（必填） |
| `as_of_date` | Date | YYYY-MM-DD | R 计算基准日（默认取 end_date） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:m.store_code}} AS 维度编码,
    {{group_by:m.store_code}} AS 维度,
    COUNT(DISTINCT CASE WHEN rfm.价值分层 = '重要价值' THEN m.mem_code END) AS 重要价值会员,
    COUNT(DISTINCT CASE WHEN rfm.价值分层 = '一般价值' THEN m.mem_code END) AS 一般价值会员,
    COUNT(DISTINCT CASE WHEN rfm.价值分层 = '低价值' THEN m.mem_code END) AS 低价值会员,
    COUNT(DISTINCT CASE WHEN rfm.价值分层 = '流失风险' THEN m.mem_code END) AS 流失风险会员,
    COUNT(DISTINCT m.mem_code) AS 会员总数,
    ROUND(COUNT(DISTINCT CASE WHEN rfm.价值分层 = '重要价值' THEN m.mem_code END) * 100.0 /
        NULLIF(COUNT(DISTINCT m.mem_code), 0), 2) AS 重要价值占比%
FROM dm.v_crm_member_with_sly m
LEFT JOIN (
    SELECT
        mem_code,
        SUM(consume_count) AS 消费频次,
        SUM(busi_income) AS 消费金额,
        CASE
            WHEN DATEDIFF(:as_of_date, MAX(last_consume_time_inner)) <= 30
             AND SUM(consume_count) >= 3
             AND SUM(busi_income) >= 500
            THEN '重要价值'
            WHEN DATEDIFF(:as_of_date, MAX(last_consume_time_inner)) <= 60
             AND SUM(consume_count) >= 2
             AND SUM(busi_income) >= 200
            THEN '一般价值'
            WHEN DATEDIFF(:as_of_date, MAX(last_consume_time_inner)) <= 90
            THEN '低价值'
            ELSE '流失风险'
        END AS 价值分层
    FROM (
        SELECT mem_code, SUM(consume_count) AS consume_count,
            SUM(busi_income) AS busi_income,
            MAX(coupon_date) AS last_consume_time_inner
        FROM dm.dm_crm_card_sum_day_p_store
        WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
         AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
            AND coupon_date < :end_date_plus_1
        GROUP BY mem_code
    ) t
    GROUP BY mem_code
) rfm ON m.mem_code = rfm.mem_code
WHERE m.group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND (m.mem_status IS NULL OR m.mem_status = '正常')
GROUP BY {{group_by:m.store_code}}
ORDER BY 重要价值占比% DESC
LIMIT {{top_n:20}};
```

**输出格式**：分层表格（维度 / 重要价值会员 / 一般价值会员 / 低价值会员 / 流失风险会员 / 会员总数 / 重要价值占比%）

> 💡 分层阈值（R≤30天/F≥3次/M≥500元）为默认值，可根据集团实际消费水平调整。

---

---

# 💳 主题六：会员卡型分析

> ⚠️ **表说明**：卡型分析使用 `dm.v_crm_member_with_sly`（会员维表），统计**全量注册会员**的卡型结构、余额分布、多卡情况，不依赖行为日期过滤。
>
> **卡型字段说明**：
> - `mem_card_type`：卡类型名称，一个会员若持有多张不同类型卡，用 `||` 分隔拼接（如 `才湾人普通会员卡||南鸭榜会员卡`）
> - `card_num`：该会员持有的会员卡数量
> - `balance_principal`：储值本金余额
> - `balance_gift`：储值赠送余额
> - `balance_cashback`：返现余额
> - `balance_recharge`：可用充值余额
> - `balance_score`：积分余额
> - `effective_coupon_num`：当前有效券数量

## Intent 95: MemberCardTypeDistribution — 会员卡型分布

**触发**：会员卡型分布/什么卡/卡类型统计/各卡型会员数/持卡结构

**业务说明**：统计各卡型的会员数和占比，支持按门店/集团聚合，帮助了解不同卡种的会员规模和余额沉淀。基于 `mem_card_type` 字段，展示单卡和多卡拼接情况。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 集团/门店/省份/城市 | 聚合维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（按卡型统计会员数）**：
```sql
SELECT
    mem_card_type AS 卡类型,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%,
    COUNT(DISTINCT CASE WHEN balance_principal > 0 THEN mem_code END) AS 有储值余额会员数,
    ROUND(SUM(balance_principal), 2) AS 储值本金余额总计,
    ROUND(AVG(balance_principal), 2) AS 人均储值本金,
    ROUND(SUM(balance_score), 2) AS 积分余额总计
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY mem_card_type
ORDER BY 会员数 DESC
LIMIT {{top_n:20}};
```

**SQL 模板（按门店/省份/城市聚合各卡型人数）**：
```sql
SELECT
    {{group_by:store_code}} AS 维度,
    COUNT(DISTINCT mem_code) AS 总会员数,
    COUNT(DISTINCT CASE WHEN mem_card_type LIKE '%储值%' OR balance_principal > 0 THEN mem_code END) AS 储值卡会员数,
    COUNT(DISTINCT CASE WHEN mem_card_type LIKE '%积分%' OR mem_card_type LIKE '%普通%' OR mem_card_type LIKE '%电子%' THEN mem_code END) AS 积分/普通卡会员数,
    ROUND(SUM(balance_principal), 2) AS 储值本金余额,
    ROUND(SUM(balance_gift), 2) AS 储值赠送余额,
    ROUND(SUM(balance_score), 2) AS 积分余额
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND (mem_status IS NULL OR mem_status = '正常')
GROUP BY {{group_by:store_code}}
ORDER BY 总会员数 DESC
LIMIT {{top_n:20}};
```

**输出格式**：
- 卡型分布：表格（卡类型 / 会员数 / 占比% / 有储值余额会员数 / 储值本金余额总计 / 人均储值本金 / 积分余额总计）
- 门店聚合：表格（维度 / 总会员数 / 储值卡会员数 / 积分/普通卡会员数 / 储值本金余额 / 储值赠送余额 / 积分余额）

---

## Intent 96: MemberMultiCard — 跨品牌/多卡会员分析

**触发**：多卡会员/跨品牌会员/同时持有多张卡/持多品牌卡/持卡数量

**业务说明**：分析同时持有多张不同品牌卡的会员群体，用于识别跨品牌高粘性会员，辅助集团整体会员运营决策。`mem_card_type` 中含 `||` 的即为多卡会员，`card_num` 字段直接反映持卡数。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（多卡会员分布）**：
```sql
SELECT
    card_num AS 持卡数量,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%,
    ROUND(SUM(balance_principal), 2) AS 储值本金余额合计,
    ROUND(AVG(balance_principal), 2) AS 人均储值本金
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND (mem_status IS NULL OR mem_status = '正常')
GROUP BY card_num
ORDER BY card_num DESC;
```

**SQL 模板（多卡会员卡型组合分布，按 mem_card_type 聚合）**：
```sql
SELECT
    mem_card_type AS 持卡组合,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%,
    ROUND(SUM(balance_principal), 2) AS 储值本金余额合计,
    ROUND(SUM(balance_score), 2) AS 积分余额合计
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND card_num >= 2
    AND (mem_status IS NULL OR mem_status = '正常')
GROUP BY mem_card_type
ORDER BY 会员数 DESC
LIMIT {{top_n:20}};
```

**SQL 模板（多卡会员明细，用于营销触达）**：
```sql
SELECT
    mem_code AS 会员编码,
    mem_name AS 姓名,
    CONCAT(LEFT(mem_mobile, 3), '****', RIGHT(mem_mobile, 4)) AS 手机号,
    mem_card_type AS 持卡组合,
    card_num AS 持卡数,
    store_code AS 注册门店,
    balance_principal AS 储值本金余额,
    balance_score AS 积分余额,
    last_consume_time AS 最后消费时间
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND card_num >= 2
    AND (mem_status IS NULL OR mem_status = '正常')
ORDER BY card_num DESC, balance_principal DESC
LIMIT {{top_n:50}};
```

**输出格式**：
- 分布：表格（持卡数量 / 会员数 / 占比% / 储值本金余额合计 / 人均储值本金）
- 卡型组合：表格（持卡组合 / 会员数 / 占比% / 储值余额 / 积分余额）
- 明细：名单表格（会员编码 / 姓名 / 手机号 / 持卡组合 / 持卡数 / 注册门店 / 储值余额 / 积分余额 / 最后消费时间）

---

## Intent 97: MemberBalanceDistribution — 会员余额分布与沉睡资金分析

**触发**：会员余额/储值余额分布/沉睡资金/积分沉淀/余额风险/有余额没消费/余额分层

**业务说明**：分析全量注册会员的储值/积分余额分布，识别有余额但长期未消费的"沉睡资金"会员，辅助运营盘活资产。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `as_of_date` | Date | YYYY-MM-DD | 基准日期（默认今日） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（余额分层分布）**：
```sql
SELECT
    CASE
        WHEN balance_principal <= 0 THEN '无储值余额'
        WHEN balance_principal > 0 AND balance_principal < 100 THEN '余额1-99元'
        WHEN balance_principal >= 100 AND balance_principal < 500 THEN '余额100-499元'
        WHEN balance_principal >= 500 AND balance_principal < 1000 THEN '余额500-999元'
        WHEN balance_principal >= 1000 AND balance_principal < 5000 THEN '余额1000-4999元'
        ELSE '余额5000元以上'
    END AS 余额分层,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(COUNT(DISTINCT mem_code) * 100.0 /
        SUM(COUNT(DISTINCT mem_code)) OVER(), 2) AS 占比%,
    ROUND(SUM(balance_principal), 2) AS 储值本金总额,
    ROUND(SUM(balance_gift), 2) AS 储值赠送总额,
    ROUND(AVG(balance_principal), 2) AS 人均余额
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY 余额分层
ORDER BY SUM(balance_principal) DESC;
```

**SQL 模板（沉睡资金会员，有余额但超N天未消费）**：
```sql
SELECT
    CASE
        WHEN DATEDIFF(:as_of_date, last_consume_time) <= 90 THEN '90天内有消费'
        WHEN DATEDIFF(:as_of_date, last_consume_time) <= 180 THEN '91-180天未消费'
        WHEN DATEDIFF(:as_of_date, last_consume_time) <= 365 THEN '181-365天未消费'
        WHEN DATEDIFF(:as_of_date, last_consume_time) > 365 THEN '超1年未消费'
        ELSE '从未消费'
    END AS 消费状态,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(SUM(balance_principal), 2) AS 储值本金余额,
    ROUND(SUM(balance_gift), 2) AS 储值赠送余额,
    ROUND(SUM(balance_principal + balance_gift), 2) AS 储值总余额,
    ROUND(SUM(balance_score), 2) AS 积分余额,
    ROUND(AVG(balance_principal), 2) AS 人均储值本金
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND balance_principal > 0
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
GROUP BY 消费状态
ORDER BY 储值本金余额 DESC;
```

**SQL 模板（沉睡资金会员明细，用于唤醒触达）**：
```sql
SELECT
    mem_code AS 会员编码,
    mem_name AS 姓名,
    CONCAT(LEFT(mem_mobile, 3), '****', RIGHT(mem_mobile, 4)) AS 手机号,
    mem_card_type AS 卡类型,
    store_code AS 注册门店,
    ROUND(balance_principal, 2) AS 储值本金余额,
    ROUND(balance_gift, 2) AS 储值赠送余额,
    balance_score AS 积分余额,
    last_consume_time AS 最后消费时间,
    DATEDIFF(:as_of_date, last_consume_time) AS 距今天数
FROM dm.v_crm_member_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
    AND balance_principal > 0
    AND (last_consume_time IS NULL OR DATEDIFF(:as_of_date, last_consume_time) > :days)
    AND (mem_status IS NULL OR mem_status = '正常')
        AND store_code IN (#{omShopCodes})
ORDER BY balance_principal DESC
LIMIT {{top_n:50}};
```

**输出格式**：
- 余额分层：表格（余额分层 / 会员数 / 占比% / 储值本金总额 / 储值赠送总额 / 人均余额）
- 沉睡资金：表格（消费状态 / 会员数 / 储值本金余额 / 储值赠送余额 / 储值总余额 / 积分余额 / 人均储值本金）
- 触达明细：名单（会员编码 / 姓名 / 手机号 / 卡类型 / 注册门店 / 余额明细 / 最后消费时间 / 距今天数）

> 💡 "沉睡资金"默认条件：储值本金余额 > 0 且超90天未消费。可根据运营需求调整天数阈值。

---

## Intent 94: MemberCouponEffectiveness — 优惠券促活效果

**触发**：优惠券效果/优惠券促活/优惠券ROI/用券会员消费

**业务说明**：对比有用券行为和无券消费的会员群体，评估优惠券的促活效果。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 分析周期（必填） |
| `region` | String | 省份/城市 | 区域过滤 |

**SQL 模板**：
```sql
SELECT
    CASE WHEN coupon_consume_times > 0 THEN '用券会员' ELSE '非用券会员' END AS 群体,
    COUNT(DISTINCT mem_code) AS 会员数,
    ROUND(SUM(coupon_consume_times), 2) AS 总用券次数,
    ROUND(SUM(coupon_consume_times) / NULLIF(COUNT(DISTINCT CASE WHEN coupon_consume_times > 0 THEN mem_code END), 0), 2) AS 人均用券次数,
    ROUND(SUM(coupon_consume_amount), 2) AS 券消费金额,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT mem_code), 0), 2) AS 人均实收,
    ROUND(SUM(coupon_consume_amount) * 100.0 / NULLIF(SUM(busi_income), 0), 2) AS 券消费占比%
FROM dm.dm_crm_card_sum_day_p_store
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND coupon_date >= :start_date
    AND coupon_date < :end_date_plus_1
    {{#if region}} AND province = :region
GROUP BY CASE WHEN coupon_consume_times > 0 THEN '用券会员' ELSE '非用券会员' END;
```

**输出格式**：对比表格（群体 / 会员数 / 总用券次数 / 人均用券次数 / 券消费金额 / 实收金额 / 人均实收 / 券消费占比%）

---
