# SQL 生成规范与模板

> **何时使用本文件**：在步骤 3（理解需求与生成 SQL）时参考，确保生成的 SQL 符合 ClickHouse 最佳实践。
> **何时不使用**：图表可视化和结论生成请参考 `visualization-guide.md`；工具调用参数请参考各工具的 reference 文档。

---

## 目录

- [§1 生成规范](#1-生成规范)
- [§2 时间处理函数](#2-时间处理函数)
- [§3 常见分析模式模板](#3-常见分析模式模板)
- [§4 性能优化要点](#4-性能优化要点)
- [§5 常见错误与修正](#5-常见错误与修正)

---

## §1 生成规范

### 基本原则

1. **只生成 SELECT 语句**：严禁生成任何 DDL/DML（INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE）
2. **必须使用分区键过滤**：WHERE 条件中必须包含分区键字段，避免全表扫描
3. **只选需要的列**：禁止 `SELECT *`，明确列出需要的字段
4. **结果集控制**：非聚合查询必须添加 `LIMIT`（默认 1000）
5. **使用 ClickHouse 原生函数**：时间处理、字符串处理等使用 ClickHouse 内置函数

### SQL 格式规范

```sql
-- 标准格式
SELECT
    维度列,
    聚合函数(指标列) AS 指标别名
FROM 数据库.表名
WHERE 分区键过滤条件
  AND 其他过滤条件
GROUP BY 维度列
ORDER BY 排序列 DESC
LIMIT N
```

### 别名规范

- 聚合结果必须有中文别名（方便业务人员理解）
- 别名使用反引号包裹：`` AS `支付金额` ``
- 时间维度别名统一为：`日期`、`月份`、`小时` 等

---

## §2 时间处理函数

### 常用时间函数映射

| 用户表述 | ClickHouse 函数 | 示例 |
|---------|----------------|------|
| 按天 | `toDate(时间列)` | `toDate(create_time) AS `日期`` |
| 按周 | `toStartOfWeek(时间列)` | `toStartOfWeek(create_time) AS `周起始日`` |
| 按月 | `toStartOfMonth(时间列)` | `toStartOfMonth(create_time) AS `月份`` |
| 按小时 | `toStartOfHour(时间列)` | `toStartOfHour(create_time) AS `小时`` |
| 按年 | `toYear(时间列)` | `toYear(create_time) AS `年份`` |

### 时间范围过滤

| 用户表述 | SQL 条件 | 优先级 |
|---------|---------|--------|
| 过去 7 天 | `WHERE date >= today() - 7 AND date < today()` | ⭐⭐⭐（优先） |
| 过去 30 天 | `WHERE date >= today() - 30 AND date < today()` | ⭐⭐⭐（优先） |
| 本月 | `WHERE date >= toStartOfMonth(today()) AND date < today() + 1` | ⭐⭐⭐（优先） |
| 上个月 | `WHERE date >= toStartOfMonth(today()) - INTERVAL 1 MONTH AND date < toStartOfMonth(today())` | ⭐⭐⭐（优先） |
| 今天 | `WHERE date = today()` | ⭐⭐⭐（优先） |
| 昨天 | `WHERE date = today() - 1` | ⭐⭐⭐（优先） |
| 本周 | `WHERE date >= toStartOfWeek(today()) AND date < today() + 1` | ⭐⭐⭐（优先） |
| 今年 | `WHERE date >= toStartOfYear(today()) AND date < today() + 1` | ⭐⭐⭐（优先） |
| 2026-06-09 至 2026-06-16 | `WHERE date BETWEEN toDate('2026-06-09') AND toDate('2026-06-16')` | ⭐（仅用户指定精确日期时） |

### 日期处理规则

#### 1. 动态函数优先原则

**核心规则**：优先使用 ClickHouse 动态时间函数，避免硬编码日期

- ✅ **推荐**：使用 `today()`、`now()`、`toStartOfMonth(today())` 等动态函数
- ❌ **避免**：硬编码日期字符串如 `'2026-06-09'`，除非用户明确指定

#### 2. 时间范围推断规则

| 用户表述 | 推断规则 | SQL 实现 |
|---------|---------|---------|
| "最近"、"近期" | 默认 7 天 | `today() - 7` |
| "这个月"、"本月" | 当月 1 号至今 | `toStartOfMonth(today())` |
| "上个月" | 上月完整月 | `toStartOfMonth(today()) - INTERVAL 1 MONTH` |
| "本周" | 本周一至今 | `toStartOfWeek(today())` |
| "上周" | 上周完整周 | `toStartOfWeek(today()) - INTERVAL 1 WEEK` |

#### 3. 精确日期处理

**仅当用户明确指定精确日期时**才使用硬编码：

```sql
-- 用户明确说："查询2026年6月9日到6月16日的数据"
WHERE date BETWEEN toDate('2026-06-09') AND toDate('2026-06-16')

-- 用户明确说："查看6月10号的数据"  
WHERE date = toDate('2026-06-10')
```

#### 4. 日期格式规范

- 使用 `toDate()` 函数包装日期字符串
- 日期格式：`'YYYY-MM-DD'`
- 时间格式：`'YYYY-MM-DD HH:MM:SS'`

### 注意事项

- 如果分区键是 `toYYYYMM(date)` 格式，过滤条件也要用对应格式
- 时间比较使用 `>=` 和 `<`（左闭右开），避免边界问题
- 当前时间使用 `now()`，当前日期使用 `today()`

---

## §3 常见分析模式模板

### 3.1 趋势分析（按时间维度汇总）

```sql
-- 用户需求："统计过去7天每天的订单量和支付金额"
SELECT
    toDate(pay_time) AS `日期`,
    count() AS `订单量`,
    sum(pay_amount) AS `支付金额`
FROM db.orders
WHERE pay_time >= today() - 7
  AND pay_time < today()
GROUP BY `日期`
ORDER BY `日期` ASC
```

### 3.2 分组对比（按分类维度汇总）

```sql
-- 用户需求："各渠道的用户数和支付金额对比"
SELECT
    channel AS `渠道`,
    uniqExact(user_id) AS `用户数`,
    sum(pay_amount) AS `支付金额`
FROM db.orders
WHERE date >= today() - 30
  AND date < today()
GROUP BY `渠道`
ORDER BY `支付金额` DESC
```

### 3.3 TOP N 排名

```sql
-- 用户需求："支付金额最高的前10个商品"
SELECT
    product_name AS `商品名称`,
    sum(pay_amount) AS `支付金额`,
    count() AS `订单量`
FROM db.orders
WHERE date >= today() - 30
  AND date < today()
GROUP BY `商品名称`
ORDER BY `支付金额` DESC
LIMIT 10
```

### 3.4 占比分析

```sql
-- 用户需求："各支付方式的订单占比"
SELECT
    pay_method AS `支付方式`,
    count() AS `订单量`,
    round(count() * 100.0 / sum(count()) OVER (), 2) AS `占比(%)`
FROM db.orders
WHERE date >= today() - 7
  AND date < today()
GROUP BY `支付方式`
ORDER BY `订单量` DESC
```

### 3.5 同比/环比分析

```sql
-- 用户需求："本月与上月的GMV对比（环比）"
SELECT
    '本月' AS `时间段`,
    sum(pay_amount) AS `GMV`
FROM db.orders
WHERE date >= toStartOfMonth(today())
  AND date < today() + 1

UNION ALL

SELECT
    '上月' AS `时间段`,
    sum(pay_amount) AS `GMV`
FROM db.orders
WHERE date >= toStartOfMonth(today()) - INTERVAL 1 MONTH
  AND date < toStartOfMonth(today())
```

### 3.6 多维交叉分析

```sql
-- 用户需求："过去7天各渠道每天的支付金额趋势"
SELECT
    toDate(pay_time) AS `日期`,
    channel AS `渠道`,
    sum(pay_amount) AS `支付金额`
FROM db.orders
WHERE pay_time >= today() - 7
  AND pay_time < today()
GROUP BY `日期`, `渠道`
ORDER BY `日期` ASC, `支付金额` DESC
```

### 3.7 漏斗分析（简化版）

```sql
-- 用户需求："注册-下单-支付的转化漏斗"
SELECT
    '注册' AS `步骤`,
    uniqExact(user_id) AS `用户数`
FROM db.user_events
WHERE event = 'register' AND date >= today() - 7

UNION ALL

SELECT
    '下单' AS `步骤`,
    uniqExact(user_id) AS `用户数`
FROM db.user_events
WHERE event = 'create_order' AND date >= today() - 7

UNION ALL

SELECT
    '支付' AS `步骤`,
    uniqExact(user_id) AS `用户数`
FROM db.user_events
WHERE event = 'pay_success' AND date >= today() - 7
```

---

## §4 性能优化要点

| 优化项 | 说明 | 示例 |
|--------|------|------|
| 分区裁剪 | WHERE 必须包含分区键 | `WHERE toYYYYMM(date) = 202601` |
| 避免 SELECT * | 只选需要的列 | `SELECT user_id, amount` |
| PREWHERE 优化 | 高过滤率条件放 PREWHERE | `PREWHERE status = 'paid'` |
| 小表放右侧 | JOIN 时小表做右表 | `big_table LEFT JOIN small_table` |
| 使用近似函数 | 大数据量用近似去重 | `uniq(user_id)` 替代 `uniqExact(user_id)` |
| LIMIT 控制 | 非聚合查询加 LIMIT | `LIMIT 1000` |
| 避免 ORDER BY 大结果集 | 先聚合再排序 | 聚合后通常行数少，排序开销小 |

---

## §5 常见错误与修正

| 错误场景 | 错误写法 | 正确写法 | 说明 |
|---------|---------|---------|------|
| 中文列名未转义 | `SELECT 支付金额` | `` SELECT `支付金额` `` | 中文列名必须用反引号 |
| 日期比较类型不匹配 | `WHERE date = '2026-01-01'` | `WHERE date = toDate('2026-01-01')` | 确保类型一致 |
| GROUP BY 缺少维度 | `SELECT a, b, sum(c)` | `SELECT a, b, sum(c) GROUP BY a, b` | 非聚合列必须在 GROUP BY 中 |
| LIMIT 位置错误 | `SELECT ... LIMIT 10 ORDER BY ...` | `SELECT ... ORDER BY ... LIMIT 10` | LIMIT 在 ORDER BY 之后 |
| 除零错误 | `a / b` | `a / nullIf(b, 0)` | 使用 nullIf 避免除零 |
| 时间格式错误 | `DATE_FORMAT(...)` | `formatDateTime(...)` | ClickHouse 使用自己的时间函数 |
| 字符串拼接 | `CONCAT(a, b)` | `concat(a, b)` | ClickHouse 函数名小写 |
