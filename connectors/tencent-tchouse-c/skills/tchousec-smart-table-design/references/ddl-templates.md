# DDL 模板与设计模式

> **何时使用本文件**：生成 CREATE TABLE DDL 时参考模板；MySQL 迁移时参考类型映射。
> **何时不使用**：选择引擎/分区/排序键（参考 engine-selection-guide.md）；SQL 查询优化。

## 目录

- [§1 通用 DDL 模板](#1-通用-ddl-模板)
- [§2 典型业务场景模板](#2-典型业务场景模板)
- [§3 MySQL 迁移类型映射](#3-mysql-迁移类型映射)
- [§4 分布式表建表模板](#4-分布式表建表模板)
- [§5 TTL 配置模板](#5-ttl-配置模板)
- [§6 ALTER TABLE 优化语句](#6-alter-table-优化语句)

---

## §1 通用 DDL 模板

### 基础 MergeTree 模板

```sql
CREATE TABLE {database}.{table_name}
(
    -- 时间字段（分区键 + 排序键首字段）
    `{date_col}` Date COMMENT '数据日期',
    
    -- 业务主键字段
    `{id_col}` UInt64 COMMENT '主键ID',
    
    -- 维度字段（低基数用 LowCardinality）
    `{dim_col}` LowCardinality(String) COMMENT '维度字段',
    
    -- 指标字段
    `{metric_col}` Float64 COMMENT '指标字段',
    
    -- 时间戳（精确时间）
    `{ts_col}` DateTime COMMENT '事件时间',
    
    -- 跳数索引
    INDEX idx_{dim_col} {dim_col} TYPE set(100) GRANULARITY 4,
    INDEX idx_{id_col} {id_col} TYPE bloom_filter(0.01) GRANULARITY 4
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/{database}.{table_name}', '{replica}')
PARTITION BY toYYYYMM({date_col})
ORDER BY ({date_col}, {dim_col}, {id_col})
TTL {date_col} + INTERVAL {N} DAY DELETE
SETTINGS index_granularity = 8192
COMMENT '表注释说明';
```

### ReplacingMergeTree 模板（去重场景）

```sql
CREATE TABLE {database}.{table_name}
(
    `{date_col}` Date COMMENT '数据日期',
    `{id_col}` UInt64 COMMENT '业务主键（去重键）',
    `{version_col}` UInt64 COMMENT '版本号（保留最大版本）',
    
    -- 业务字段
    `{field1}` String COMMENT '字段1',
    `{field2}` Float64 COMMENT '字段2',
    
    `update_time` DateTime DEFAULT now() COMMENT '更新时间'
)
ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{shard}/{database}.{table_name}', '{replica}', {version_col})
PARTITION BY toYYYYMM({date_col})
ORDER BY ({date_col}, {id_col})
SETTINGS index_granularity = 8192
COMMENT '去重表，按 {id_col} 去重保留 {version_col} 最大的行';
```

### SummingMergeTree 模板（预聚合场景）

```sql
CREATE TABLE {database}.{table_name}
(
    -- 维度字段（排序键）
    `{date_col}` Date COMMENT '统计日期',
    `{dim1}` LowCardinality(String) COMMENT '维度1',
    `{dim2}` LowCardinality(String) COMMENT '维度2',
    
    -- 指标字段（自动求和）
    `{metric1}` UInt64 COMMENT '计数指标',
    `{metric2}` Float64 COMMENT '金额指标'
)
ENGINE = ReplicatedSummingMergeTree('/clickhouse/tables/{shard}/{database}.{table_name}', '{replica}')
PARTITION BY toYYYYMM({date_col})
ORDER BY ({date_col}, {dim1}, {dim2})
SETTINGS index_granularity = 8192
COMMENT '预聚合表，按维度自动求和指标列';
```

## §2 典型业务场景模板

### 电商订单表

```sql
CREATE TABLE analytics.orders
(
    `order_date` Date COMMENT '订单日期',
    `order_id` UInt64 COMMENT '订单ID',
    `user_id` UInt64 COMMENT '用户ID',
    `channel` LowCardinality(String) COMMENT '渠道来源',
    `product_id` UInt64 COMMENT '商品ID',
    `category` LowCardinality(String) COMMENT '商品类目',
    `amount` Decimal(18, 2) COMMENT '订单金额',
    `quantity` UInt32 COMMENT '商品数量',
    `status` LowCardinality(String) COMMENT '订单状态',
    `pay_time` DateTime COMMENT '支付时间',
    `create_time` DateTime COMMENT '创建时间',
    
    INDEX idx_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 4,
    INDEX idx_product_id product_id TYPE bloom_filter(0.01) GRANULARITY 4,
    INDEX idx_status status TYPE set(20) GRANULARITY 4
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/analytics.orders', '{replica}')
PARTITION BY toYYYYMMDD(order_date)
ORDER BY (order_date, channel, user_id, order_id)
TTL order_date + INTERVAL 365 DAY DELETE
SETTINGS index_granularity = 8192
COMMENT '电商订单明细表，日增约5000万条，按天分区';
```

### 用户行为日志表

```sql
CREATE TABLE analytics.user_events
(
    `event_date` Date COMMENT '事件日期',
    `user_id` UInt64 COMMENT '用户ID',
    `event_type` LowCardinality(String) COMMENT '事件类型',
    `page` String COMMENT '页面路径',
    `referrer` String COMMENT '来源页面',
    `device` LowCardinality(String) COMMENT '设备类型',
    `os` LowCardinality(String) COMMENT '操作系统',
    `city` LowCardinality(String) COMMENT '城市',
    `timestamp` DateTime64(3) COMMENT '事件时间（毫秒精度）',
    `properties` String COMMENT '事件属性（JSON）',
    
    INDEX idx_event_type event_type TYPE set(50) GRANULARITY 4,
    INDEX idx_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 4,
    INDEX idx_city city TYPE set(1000) GRANULARITY 3
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/analytics.user_events', '{replica}')
PARTITION BY toYYYYMMDD(event_date)
ORDER BY (event_date, event_type, user_id, timestamp)
TTL event_date + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192
COMMENT '用户行为日志表，保留90天，按天分区';
```

### 用户画像表（去重更新）

```sql
CREATE TABLE analytics.user_profiles
(
    `update_date` Date COMMENT '更新日期',
    `user_id` UInt64 COMMENT '用户ID（去重键）',
    `version` UInt64 COMMENT '版本号',
    `nickname` String COMMENT '昵称',
    `gender` LowCardinality(String) COMMENT '性别',
    `age` UInt8 COMMENT '年龄',
    `city` LowCardinality(String) COMMENT '城市',
    `level` LowCardinality(String) COMMENT '会员等级',
    `total_orders` UInt32 COMMENT '累计订单数',
    `total_amount` Decimal(18, 2) COMMENT '累计消费金额',
    `last_login_time` DateTime COMMENT '最后登录时间',
    `tags` Array(String) COMMENT '用户标签'
)
ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{shard}/analytics.user_profiles', '{replica}', version)
PARTITION BY toYYYYMM(update_date)
ORDER BY (user_id)
SETTINGS index_granularity = 8192
COMMENT '用户画像表，按user_id去重保留最新版本';
```

### 实时统计汇总表（预聚合）

```sql
CREATE TABLE analytics.daily_channel_stats
(
    `stat_date` Date COMMENT '统计日期',
    `channel` LowCardinality(String) COMMENT '渠道',
    `product_category` LowCardinality(String) COMMENT '商品类目',
    
    -- 指标列（自动求和）
    `order_count` UInt64 COMMENT '订单数',
    `user_count` UInt64 COMMENT '用户数（近似）',
    `total_amount` Decimal(18, 2) COMMENT '总金额',
    `refund_count` UInt64 COMMENT '退款数'
)
ENGINE = ReplicatedSummingMergeTree('/clickhouse/tables/{shard}/analytics.daily_channel_stats', '{replica}')
PARTITION BY toYYYYMM(stat_date)
ORDER BY (stat_date, channel, product_category)
SETTINGS index_granularity = 8192
COMMENT '每日渠道统计汇总表，按维度自动聚合';
```

## §3 MySQL 迁移类型映射

### 数据类型映射表

| MySQL 类型 | ClickHouse 类型 | 说明 |
|-----------|----------------|------|
| `TINYINT` | `Int8` / `UInt8` | 有符号/无符号 |
| `SMALLINT` | `Int16` / `UInt16` | |
| `INT` | `Int32` / `UInt32` | |
| `BIGINT` | `Int64` / `UInt64` | |
| `FLOAT` | `Float32` | |
| `DOUBLE` | `Float64` | |
| `DECIMAL(P,S)` | `Decimal(P,S)` | 精度一致 |
| `VARCHAR(N)` / `TEXT` | `String` | ClickHouse 无长度限制 |
| `CHAR(N)` | `FixedString(N)` 或 `String` | 定长用 FixedString |
| `DATE` | `Date` | |
| `DATETIME` | `DateTime` | 秒精度 |
| `DATETIME(3)` | `DateTime64(3)` | 毫秒精度 |
| `TIMESTAMP` | `DateTime` | |
| `BOOLEAN` / `TINYINT(1)` | `UInt8` | 0/1 表示 |
| `ENUM(...)` | `Enum8(...)` 或 `LowCardinality(String)` | 推荐后者更灵活 |
| `JSON` | `String` | 存 JSON 字符串，查询用 JSON 函数 |
| `BLOB` / `BINARY` | `String` | |

### 迁移注意事项

| MySQL 特性 | ClickHouse 处理方式 |
|-----------|-------------------|
| AUTO_INCREMENT | 不支持，需业务侧生成 ID 或用 `generateUUIDv4()` |
| NULL 值 | 建议用默认值替代（`DEFAULT ''`），避免 Nullable 开销 |
| 外键约束 | 不支持，ClickHouse 无外键概念 |
| 唯一索引 | 不支持唯一约束，用 ReplacingMergeTree 实现去重 |
| 事务 | 不支持 ACID 事务 |
| UPDATE/DELETE | 通过 ALTER TABLE UPDATE/DELETE（异步 mutation）或 CollapsingMergeTree |

### MySQL DDL 转换示例

**MySQL 原表**：
```sql
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_status (status)
);
```

**ClickHouse 转换后**：
```sql
CREATE TABLE analytics.orders
(
    `id` UInt64 COMMENT '订单ID',
    `user_id` UInt64 COMMENT '用户ID',
    `amount` Decimal(10, 2) DEFAULT 0 COMMENT '订单金额',
    `status` LowCardinality(String) DEFAULT 'pending' COMMENT '订单状态',
    `created_at` DateTime DEFAULT now() COMMENT '创建时间',
    `updated_at` DateTime DEFAULT now() COMMENT '更新时间',
    `order_date` Date DEFAULT toDate(created_at) COMMENT '订单日期（分区用）',
    
    INDEX idx_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 4,
    INDEX idx_status status TYPE set(20) GRANULARITY 4
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/analytics.orders', '{replica}')
PARTITION BY toYYYYMM(order_date)
ORDER BY (order_date, user_id, id)
SETTINGS index_granularity = 8192;
```

**转换要点**：
1. 添加 `order_date` 列作为分区键（从 `created_at` 派生）
2. `VARCHAR` → `LowCardinality(String)`（低基数字段）
3. `AUTO_INCREMENT` 去掉，ID 由业务侧生成
4. MySQL 索引 → ClickHouse 跳数索引
5. 排序键选择高频查询字段

## §4 分布式表建表模板

TCHouse-C 分布式集群需要建两层表：本地表（存数据）+ Distributed 表（路由查询）。

### 本地表（每个 shard 上）

```sql
CREATE TABLE {database}.{table_name}_local ON CLUSTER '{cluster}'
(
    -- 列定义同上
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/{database}.{table_name}', '{replica}')
PARTITION BY ...
ORDER BY ...;
```

### Distributed 表（路由层）

```sql
CREATE TABLE {database}.{table_name} ON CLUSTER '{cluster}'
AS {database}.{table_name}_local
ENGINE = Distributed('{cluster}', '{database}', '{table_name}_local', {sharding_key});
```

**sharding_key 选择**：
- 按用户分片：`cityHash64(user_id)`
- 随机分片：`rand()`
- 按时间分片：`toYYYYMM(date_col)`

## §5 TTL 配置模板

### 行级 TTL（删除过期数据）

```sql
-- 建表时指定
TTL date_col + INTERVAL 90 DAY DELETE

-- 已有表添加
ALTER TABLE {database}.{table} MODIFY TTL date_col + INTERVAL 90 DAY DELETE;
```

### 列级 TTL（清空过期列）

```sql
CREATE TABLE ...
(
    `date_col` Date,
    `detail_json` String TTL date_col + INTERVAL 30 DAY,  -- 30天后清空该列
    `summary` String  -- 永久保留
)
...
```

### 多级 TTL（冷热分层）

```sql
TTL date_col + INTERVAL 7 DAY TO VOLUME 'warm',
    date_col + INTERVAL 30 DAY TO VOLUME 'cold',
    date_col + INTERVAL 365 DAY DELETE
```

## §6 ALTER TABLE 优化语句

### 添加跳数索引

```sql
ALTER TABLE {database}.{table} ADD INDEX idx_{col} {col} TYPE {type} GRANULARITY {n};
-- 添加后需要对已有数据重建索引
ALTER TABLE {database}.{table} MATERIALIZE INDEX idx_{col};
```

### 添加 TTL

```sql
ALTER TABLE {database}.{table} MODIFY TTL {date_col} + INTERVAL {N} DAY DELETE;
```

### 修改列类型

```sql
ALTER TABLE {database}.{table} MODIFY COLUMN {col} LowCardinality(String);
```

### 添加列

```sql
ALTER TABLE {database}.{table} ADD COLUMN {col} {type} DEFAULT {default} COMMENT '{comment}' AFTER {existing_col};
```
