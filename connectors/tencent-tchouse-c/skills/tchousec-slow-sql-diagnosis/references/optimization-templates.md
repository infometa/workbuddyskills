# SQL 优化方案模板

> **何时使用本文件**：在步骤 4.3（瓶颈识别后生成优化建议）时，根据识别到的问题类型选择对应的优化方案模板。
> **何时不使用**：瓶颈识别规则请参考 `analysis-framework.md §1`；工具调用参数请参考主文件。

---

## 目录

- [§1 SQL 改写方案](#1-sql-改写方案)
- [§2 跳数索引方案](#2-跳数索引方案)
- [§3 排序键调整方案](#3-排序键调整方案)
- [§4 物化视图方案](#4-物化视图方案)
- [§5 配置调优方案](#5-配置调优方案)

---

## §1 SQL 改写方案

### 1.1 添加分区过滤条件

**适用场景**：分区裁剪失败，WHERE 条件未包含分区键字段。

```sql
-- ❌ 原始（扫描所有分区）
SELECT channel, sum(amount) FROM orders WHERE status = 'paid' GROUP BY channel

-- ✅ 改写（添加分区键过滤，假设分区键为 toYYYYMM(order_date)）
SELECT channel, sum(amount) FROM orders 
WHERE order_date >= '2026-05-01' AND status = 'paid' 
GROUP BY channel
```

**改写说明**：添加分区键字段过滤条件，将扫描范围从全量分区收敛至目标时间范围。

### 1.2 使用 PREWHERE 替代 WHERE

**适用场景**：过滤条件过滤率高（>80%），且过滤字段数据量小。

```sql
-- ❌ 原始
SELECT * FROM events WHERE event_type = 'purchase' AND ts >= '2026-05-01'

-- ✅ 改写
SELECT * FROM events PREWHERE event_type = 'purchase' WHERE ts >= '2026-05-01'
```

**改写说明**：PREWHERE 先读取过滤列进行过滤，通过的行再读取其他列，减少 IO。适用于过滤率高的条件。

### 1.3 调整 JOIN 顺序

**适用场景**：大表在 JOIN 右侧被 broadcast 到内存。

```sql
-- ❌ 原始（小表 LEFT JOIN 大表，大表被加载到内存）
SELECT * FROM users u LEFT JOIN orders o ON u.id = o.uid

-- ✅ 改写（大表在左侧，小表在右侧被加载到内存）
SELECT * FROM orders o LEFT JOIN users u ON o.uid = u.id
```

**改写说明**：ClickHouse 默认将右表加载到内存构建 hash table，应将小表放在右侧。

### 1.4 避免 SELECT *

**适用场景**：宽表（列数 > 50）上使用 SELECT *。

```sql
-- ❌ 原始
SELECT * FROM wide_table WHERE id = 123

-- ✅ 改写（只选需要的列）
SELECT id, name, amount, created_at FROM wide_table WHERE id = 123
```

**改写说明**：ClickHouse 列式存储，每列独立文件，SELECT * 读取所有列文件，IO 开销与列数成正比。

### 1.5 子查询改写为 JOIN

**适用场景**：IN (SELECT ...) 子查询可能重复执行。

```sql
-- ❌ 原始
SELECT * FROM order_items WHERE sku_id IN (SELECT sku_id FROM hot_skus WHERE category = 'electronics')

-- ✅ 改写
SELECT oi.* FROM order_items oi 
INNER JOIN hot_skus hs ON oi.sku_id = hs.sku_id 
WHERE hs.category = 'electronics'
```

### 1.6 使用子查询预过滤

**适用场景**：JOIN 前可以先大幅缩小数据量。

```sql
-- ❌ 原始（先 JOIN 再过滤）
SELECT o.*, u.name FROM orders o JOIN users u ON o.uid = u.id 
WHERE o.amount > 1000 AND o.date >= '2026-05-01'

-- ✅ 改写（先过滤再 JOIN）
SELECT o.*, u.name FROM 
  (SELECT * FROM orders WHERE amount > 1000 AND date >= '2026-05-01') o 
JOIN users u ON o.uid = u.id
```

---

## §2 跳数索引方案

### 2.1 minmax 索引

**适用场景**：数值/日期类型字段的范围查询。

```sql
-- 为高频范围过滤字段添加 minmax 索引
ALTER TABLE db.table ADD INDEX idx_amount (amount) TYPE minmax GRANULARITY 3;
```

**说明**：minmax 记录每个 granule 的最大最小值，范围查询时跳过不可能包含目标值的 granule。对高基数数值列效果好。

### 2.2 bloom_filter 索引

**适用场景**：等值查询、IN 查询，字段基数较高。

```sql
-- 为高频等值过滤字段添加 bloom_filter 索引
ALTER TABLE db.table ADD INDEX idx_user_id (user_id) TYPE bloom_filter(0.01) GRANULARITY 1;
```

**说明**：bloom_filter 适合高基数列的等值/IN 查询，假阳性率可调（0.01 = 1%）。

### 2.3 tokenbf_v1 索引

**适用场景**：字符串字段的模糊查询（LIKE '%xxx%'、hasToken）。

```sql
-- 为字符串模糊查询添加 tokenbf_v1 索引
ALTER TABLE db.table ADD INDEX idx_content (content) TYPE tokenbf_v1(10240, 3, 0) GRANULARITY 2;
```

**说明**：tokenbf_v1 对字符串进行分词后建立 bloom filter，适合 LIKE/hasToken 查询。参数含义：(bloom_size, hash_count, seed)。

### 2.4 set 索引

**适用场景**：低基数列的等值/IN 查询。

```sql
-- 为低基数列添加 set 索引
ALTER TABLE db.table ADD INDEX idx_status (status) TYPE set(100) GRANULARITY 1;
```

**说明**：set 索引记录每个 granule 中出现的所有不同值，适合基数 < 100 的列。

### 索引选择决策表

| 查询类型 | 字段特征 | 推荐索引类型 |
|---------|---------|------------|
| 范围查询（>, <, BETWEEN） | 数值/日期，高基数 | minmax |
| 等值查询（=, IN） | 高基数（>1000） | bloom_filter |
| 等值查询（=, IN） | 低基数（<100） | set |
| 模糊查询（LIKE, hasToken） | 字符串 | tokenbf_v1 |
| 多条件组合 | 混合 | 按各条件分别建索引 |

---

## §3 排序键调整方案

**适用场景**：高频查询的 WHERE 条件字段不在当前 ORDER BY 中，且无法通过跳数索引有效解决。

**注意**：调整排序键需要重建表，属于高成本操作，仅在收益明确时建议。

### 排序键设计原则

1. **基数低的字段在前，基数高的在后**（如 `status, user_id, timestamp`）
2. **高频查询的过滤字段优先**
3. **排序键字段数量建议 ≤ 4 个**

### 重建表示例

```sql
-- 1. 创建新表（调整后的排序键）
CREATE TABLE db.table_new AS db.table_old
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (status, user_id, date)  -- 新的排序键
SETTINGS index_granularity = 8192;

-- 2. 迁移数据
INSERT INTO db.table_new SELECT * FROM db.table_old;

-- 3. 原子交换（需要用户确认）
RENAME TABLE db.table_old TO db.table_backup, db.table_new TO db.table_old;
```

---

## §4 物化视图方案

### 4.1 聚合查询预计算

**适用场景**：相同维度的聚合查询频繁执行（如日报/小时报）。

```sql
-- 创建物化视图预计算每小时聚合
CREATE MATERIALIZED VIEW db.mv_hourly_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (channel, hour)
AS SELECT
  toStartOfHour(created_at) AS hour,
  channel,
  sum(amount) AS total_amount,
  count() AS order_count
FROM db.orders
GROUP BY hour, channel;
```

### 4.2 多表 JOIN 宽表

**适用场景**：多表 JOIN 查询频繁，且维度表变化不频繁。

```sql
-- 创建宽表物化视图（适合维度表变化少的场景）
CREATE MATERIALIZED VIEW db.mv_order_detail
ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_date)
ORDER BY (user_id, order_date)
AS SELECT
  o.order_id, o.order_date, o.amount,
  u.user_name, u.region
FROM db.orders o
LEFT JOIN db.users u ON o.user_id = u.id;
```

---

## §5 配置调优方案

| 配置项 | 默认值 | 调优建议 | 适用场景 |
|--------|--------|---------|---------|
| `max_memory_usage` | 10GB | 根据节点内存调整，建议 ≤ 节点内存的 70% | 大查询 OOM |
| `max_threads` | CPU 核数 | 降低可减少单查询资源占用，提高并发 | CPU 争抢严重 |
| `max_execution_time` | 0（无限制） | 建议设置 300-600 秒 | 防止查询无限运行 |
| `max_bytes_before_external_sort` | 0 | 设置为可用内存的 50% | 大数据量排序 OOM |
| `join_algorithm` | hash | 右表过大时改为 partial_merge 或 auto | JOIN OOM |
| `max_rows_to_read` | 0 | 根据业务设置上限 | 防止全表扫描 |
| `prefer_localhost_replica` | 1 | 多副本时设为 0 可分散查询负载 | 单节点负载过高 |

**配置修改注意事项**：
- 配置修改属于写操作，本 Skill 仅给出建议，不直接执行
- 建议在报告中列出具体的配置修改 SQL：`SET max_memory_usage = xxx`（会话级）或通过控制台修改（全局级）
