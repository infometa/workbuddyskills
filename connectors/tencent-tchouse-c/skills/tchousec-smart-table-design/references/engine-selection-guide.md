# 表引擎选择与诊断指南

> **何时使用本文件**：设计新表需要选择引擎时；诊断现有表结构是否合理时。
> **何时不使用**：SQL 性能优化（参考 tchousec-slow-sql-diagnosis）；数据查询分析（参考 tchousec-nl2sql-analysis）。

## 目录

- [§1 引擎选择决策树](#1-引擎选择决策树)
- [§2 各引擎详解与适用场景](#2-各引擎详解与适用场景)
- [§3 分区策略设计指南](#3-分区策略设计指南)
- [§4 排序键设计指南](#4-排序键设计指南)
- [§5 跳数索引设计指南](#5-跳数索引设计指南)
- [§6 诊断检查清单](#6-诊断检查清单)

---

## §1 引擎选择决策树

```
用户需求分析
    │
    ├─ 数据是否需要更新/去重？
    │   ├─ 否（纯追加写入）
    │   │   ├─ 是否需要预聚合？
    │   │   │   ├─ 否 → MergeTree / ReplicatedMergeTree
    │   │   │   ├─ 需要 SUM 聚合 → SummingMergeTree
    │   │   │   └─ 需要复杂聚合（avg/uniq）→ AggregatingMergeTree
    │   │   └─ 是否为分布式集群？
    │   │       ├─ 是 → Replicated* + Distributed 表
    │   │       └─ 否 → 对应非 Replicated 版本
    │   │
    │   └─ 是（需要更新/去重）
    │       ├─ 只需要按主键保留最新一条？
    │       │   └─ 是 → ReplacingMergeTree
    │       ├─ 需要实时更新任意字段？
    │       │   ├─ 有版本号字段 → VersionedCollapsingMergeTree
    │       │   └─ 无版本号 → CollapsingMergeTree
    │       └─ 需要删除操作？
    │           └─ CollapsingMergeTree（sign=-1 标记删除）
    │
    └─ 特殊场景
        ├─ 日志/事件流（只追加，按时间查询）→ MergeTree
        ├─ 维度表/字典表（小表，全量更新）→ ReplacingMergeTree 或 Dictionary
        └─ 实时数仓（Kafka 消费）→ MergeTree + Materialized View
```

## §2 各引擎详解与适用场景

### MergeTree（基础引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 日志、事件流、订单明细等纯追加写入场景 |
| 数据特点 | 只追加，不更新，不去重 |
| 查询模式 | 按时间范围 + 维度过滤 |
| 优势 | 写入性能最高，查询最快，功能最完整 |
| 劣势 | 不支持去重和更新 |

### ReplicatedMergeTree（高可用版本）

| 属性 | 说明 |
|------|------|
| 适用场景 | 生产环境必选，提供数据副本和高可用 |
| 与 MergeTree 区别 | 多副本同步，ZooKeeper/Keeper 协调 |
| 建表语法 | `ReplicatedMergeTree('/clickhouse/tables/{shard}/{database}.{table}', '{replica}')` |
| 注意事项 | TCHouse-C 集群默认使用 Replicated 版本 |

### ReplacingMergeTree（去重引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 需要按主键去重，保留最新版本 |
| 去重时机 | 后台 merge 时去重，**非实时** |
| 查询注意 | 需加 `FINAL` 或用 `argMax` 确保最新值 |
| 版本字段 | 可选，指定后保留版本号最大的行 |
| 典型用例 | 用户画像表、维度表、CDC 同步 |

### SummingMergeTree（求和引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 只需要聚合后的汇总值，不需要明细 |
| 聚合方式 | 按排序键分组，对数值列自动求和 |
| 聚合时机 | 后台 merge 时聚合 |
| 典型用例 | PV/UV 统计表、金额汇总表 |
| 注意事项 | 查询时仍需 GROUP BY 确保准确性 |

### AggregatingMergeTree（聚合引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 需要复杂聚合（avg、uniq、quantile 等） |
| 数据类型 | 使用 AggregateFunction 类型存储中间状态 |
| 写入方式 | 通常配合 Materialized View 使用 |
| 典型用例 | 实时数仓的预聚合层 |
| 注意事项 | 查询时需用 -Merge 后缀函数（如 `uniqMerge`） |

### CollapsingMergeTree（折叠引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 需要更新/删除操作的场景 |
| 工作原理 | 通过 sign 列（1=插入，-1=删除）标记状态 |
| 更新方式 | 先写 sign=-1 的旧行，再写 sign=1 的新行 |
| 典型用例 | 实时更新的统计表、状态变更表 |
| 注意事项 | 写入顺序必须严格保证（先删后插） |

### VersionedCollapsingMergeTree（版本化折叠引擎）

| 属性 | 说明 |
|------|------|
| 适用场景 | 需要更新且无法保证写入顺序 |
| 与 Collapsing 区别 | 额外有 version 列，不依赖写入顺序 |
| 典型用例 | 多线程/分布式写入的更新场景 |
| 注意事项 | 需要业务侧维护递增的版本号 |

## §3 分区策略设计指南

### 分区粒度选择

| 日增数据量 | 推荐分区粒度 | 分区表达式 | 预估 Parts 数 |
|-----------|-------------|-----------|--------------|
| < 10 万行 | 按月 | `toYYYYMM(date_col)` | ~12/年 |
| 10 万 ~ 100 万行 | 按月 | `toYYYYMM(date_col)` | ~12/年 |
| 100 万 ~ 1 亿行 | 按天 | `toYYYYMMDD(date_col)` | ~365/年 |
| 1 亿 ~ 10 亿行 | 按天 | `toYYYYMMDD(date_col)` | ~365/年 |
| > 10 亿行 | 按天 + 业务维度 | `(toYYYYMMDD(date_col), cityHash64(user_id) % 16)` | ~5840/年 |

### 分区设计原则

1. **单个分区数据量**：建议 100 万 ~ 1 亿行（过少浪费，过多查询慢）
2. **分区总数**：建议 < 1000 个活跃分区（过多影响元数据管理）
3. **查询必须命中分区键**：WHERE 条件必须包含分区字段，否则全分区扫描
4. **TTL 与分区对齐**：TTL 删除以分区为单位，分区粒度应与保留周期匹配

### 常见错误

| 错误 | 后果 | 修正 |
|------|------|------|
| 按小时分区 | Parts 过多，merge 压力大 | 改为按天分区 |
| 不分区 | 无法利用分区裁剪，全表扫描 | 添加时间分区 |
| 分区键不在 WHERE 中 | 查询扫描所有分区 | 调整查询或分区策略 |

## §4 排序键设计指南

### 排序键选择原则

1. **高频过滤字段优先**：WHERE 中最常出现的字段放入排序键
2. **基数从低到高**：低基数字段在前（如 date → status → user_id）
3. **分区键字段放首位**：分区键字段作为排序键第一个字段
4. **数量控制在 3-5 个**：过多增加写入排序开销
5. **不要放高基数唯一字段在前面**：如 UUID 放首位会导致索引失效

### 排序键设计示例

| 业务场景 | 高频查询 | 推荐排序键 |
|---------|---------|-----------|
| 订单表 | 按时间+用户查询 | `(order_date, user_id, order_id)` |
| 日志表 | 按时间+服务名查询 | `(log_date, service_name, timestamp)` |
| 用户行为 | 按用户+时间查询 | `(event_date, user_id, event_type)` |
| 商品表 | 按类目+品牌查询 | `(category_id, brand_id, product_id)` |

### 排序键 vs 主键

- ClickHouse 中 `PRIMARY KEY` 默认等于 `ORDER BY`
- 可以单独指定 `PRIMARY KEY` 为 `ORDER BY` 的前缀（减少主键索引大小）
- 大多数场景不需要单独指定 PRIMARY KEY

## §5 跳数索引设计指南

### 索引类型选择

| 索引类型 | 适用场景 | 参数说明 | 示例 |
|---------|---------|---------|------|
| `minmax` | 数值/日期范围查询 | GRANULARITY = 跳过的 granule 数 | `INDEX idx_amount amount TYPE minmax GRANULARITY 3` |
| `set(N)` | 低基数字段等值查询 | N = 集合最大元素数 | `INDEX idx_status status TYPE set(100) GRANULARITY 4` |
| `bloom_filter(p)` | 高基数字段等值查询 | p = 误判率 | `INDEX idx_uid user_id TYPE bloom_filter(0.01) GRANULARITY 4` |
| `tokenbf_v1` | 字符串 token 查询（hasToken） | (size, hashes, seed) | `INDEX idx_url url TYPE tokenbf_v1(10240, 3, 0) GRANULARITY 2` |
| `ngrambf_v1` | 字符串 LIKE 查询 | (n, size, hashes, seed) | `INDEX idx_msg message TYPE ngrambf_v1(3, 256, 2, 0) GRANULARITY 4` |

### GRANULARITY 选择

- GRANULARITY 表示索引覆盖多少个 granule（默认 granule = 8192 行）
- GRANULARITY = 4 表示每 4×8192 = 32768 行建一个索引条目
- 值越小索引越精确但占用空间越大，建议 3-5

### 何时不需要跳数索引

- 字段已在排序键中（排序键本身就是最高效的索引）
- 查询频率极低的字段
- 数据分布极均匀的字段（索引无法有效跳过）

## §6 诊断检查清单

对现有表结构进行诊断时，按以下清单逐项检查：

| # | 检查项 | 良好设计 | 需要优化 | 优化建议 |
|---|--------|---------|---------|---------|
| 1 | 引擎选择 | 匹配业务需求（追加/去重/聚合） | 引擎与业务不匹配 | 重建表使用正确引擎 |
| 2 | 分区粒度 | 单分区 100万~1亿行 | 过细（小时级）或不分区 | 调整分区表达式 |
| 3 | 排序键覆盖 | 高频 WHERE 字段在排序键中 | 高频过滤字段不在排序键 | 重建表调整排序键 |
| 4 | 排序键顺序 | 基数低→高 | 高基数字段在前 | 重建表调整顺序 |
| 5 | 排序键数量 | 3-5 个 | > 8 个 | 精简排序键 |
| 6 | 跳数索引 | 非排序键的高频过滤字段有索引 | 缺少必要索引 | ALTER TABLE ADD INDEX |
| 7 | TTL 配置 | 有保留周期的表配置了 TTL | 数据无限增长 | ALTER TABLE MODIFY TTL |
| 8 | 数据类型 | LowCardinality 用于低基数字段 | 低基数字段用普通 String | 重建表优化类型 |
| 9 | Nullable | 尽量避免 Nullable | 大量 Nullable 列 | 用默认值替代 |
| 10 | 分布式表 | 有本地表 + Distributed 表 | 只有本地表或只有 Distributed | 补建对应表 |

### 诊断输出格式

```markdown
## 表结构诊断报告

### 基本信息
- 表名：{database}.{table}
- 引擎：{engine}
- 分区：{partition_expr}
- 排序键：{order_by}

### 诊断结果

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | 引擎选择 | ✅/⚠️/❌ | {说明} |
| ... |

### 优化建议（按优先级排序）

1. **[高]** {建议1}
   ```sql
   ALTER TABLE ...
   ```
2. **[中]** {建议2}
   ...
```
