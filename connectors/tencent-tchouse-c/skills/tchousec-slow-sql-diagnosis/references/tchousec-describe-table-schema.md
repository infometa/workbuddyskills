# tchousec-describe-table-schema

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeTableSchema` 云 API，根据表名和节点 IP 获取指定表的完整建表 DDL（CREATE TABLE SQL），用于分析表结构设计是否合理。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeTableSchema`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称 | 必选 | 类型 | 描述 |
|---------|------|------|------|
| Region | 是 | String | 地域，如 `ap-guangzhou` |
| InstanceId | 是 | String | 集群实例 ID，格式如 `cdwch-xxxxxxxx` |
| TableName | 是 | String | 表名（格式为 `database.table`，如 `analytics.events`） |
| NodeIp | 是 | String | 节点 IP 地址（可通过 DescribeInstance 获取集群访问地址中的 IP） |

## 输出参数

| 参数名称 | 类型 | 描述 |
|---------|------|------|
| Exists | Boolean | 表是否存在 |
| CreateTableSql | String | 完整的建表 DDL 语句（CREATE TABLE SQL） |
| RequestId | String | 唯一请求 ID |

## 响应判断逻辑

| 场景 | 判断条件 | 含义 |
|------|---------|------|
| 表存在 | `Exists === true` | `CreateTableSql` 包含完整 DDL |
| 表不存在 | `Exists === false` | 表名或数据库名有误 |
| 接口异常 | 接口调用抛异常 | 网络/鉴权/参数等问题 |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeTableSchema",
  "Version": "2020-09-15",
  "Region": "ap-guangzhou",
  "InstanceId": "cdwch-xxxxxxxx",
  "TableName": "analytics.events",
  "NodeIp": "10.0.0.1"
}
```

### 响应示例（表存在）

```json
{
  "Response": {
    "Exists": true,
    "CreateTableSql": "CREATE TABLE analytics.events\n(\n    `event_date` Date,\n    `user_id` UInt64,\n    `event_type` String,\n    `timestamp` DateTime,\n    `properties` String,\n    `city` LowCardinality(String),\n    INDEX idx_event_type event_type TYPE set(100) GRANULARITY 4,\n    INDEX idx_city city TYPE minmax GRANULARITY 3\n)\nENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/analytics.events', '{replica}')\nPARTITION BY toYYYYMM(event_date)\nORDER BY (event_date, user_id, timestamp)\nSETTINGS index_granularity = 8192",
    "RequestId": "xxx-xxx-xxx"
  }
}
```

### 响应示例（表不存在）

```json
{
  "Response": {
    "Exists": false,
    "CreateTableSql": "",
    "RequestId": "xxx-xxx-xxx"
  }
}
```

## 表结构分析要点

### 排序键（ORDER BY）分析

排序键是 ClickHouse 最重要的索引机制，分析要点：

| 检查项 | 良好设计 | 需要优化 |
|--------|---------|---------|
| 字段顺序 | 基数低→高（如 date → user_id → timestamp） | 基数高的字段在前 |
| 覆盖查询条件 | 高频 WHERE 条件字段在排序键中 | 高频过滤字段不在排序键中 |
| 字段数量 | 3-5 个 | 过多（>8个）影响写入性能 |

### 分区键（PARTITION BY）分析

| 检查项 | 良好设计 | 需要优化 |
|--------|---------|---------|
| 粒度 | 月级（toYYYYMM）或日级（toYYYYMMDD） | 过细（小时级）导致 Parts 过多 |
| 查询覆盖 | 查询条件包含分区字段 | 查询不带分区条件导致全分区扫描 |

### 跳数索引分析

| 索引类型 | 适用场景 | 示例 |
|---------|---------|------|
| `minmax` | 数值/日期范围查询 | `INDEX idx col TYPE minmax GRANULARITY 3` |
| `set(N)` | 低基数字段等值查询 | `INDEX idx col TYPE set(100) GRANULARITY 4` |
| `bloom_filter` | 高基数字段等值查询 | `INDEX idx col TYPE bloom_filter(0.01) GRANULARITY 4` |
| `tokenbf_v1` | 字符串模糊/包含查询 | `INDEX idx col TYPE tokenbf_v1(10240, 3, 0) GRANULARITY 2` |
| `ngrambf_v1` | 字符串 LIKE 查询 | `INDEX idx col TYPE ngrambf_v1(3, 256, 2, 0) GRANULARITY 4` |

## 典型使用场景

- **索引缺失诊断**：对比 SQL 的 WHERE 条件和表的排序键/跳数索引，发现缺失的索引
- **排序键合理性评估**：判断排序键设计是否匹配实际查询模式
- **分区策略评估**：判断分区粒度是否合理，查询是否能有效裁剪分区
- **优化建议生成**：基于表结构生成具体的 ALTER TABLE ADD INDEX 语句
- **引擎类型确认**：确认是否使用了合适的表引擎（MergeTree 系列）
- **建表验证**：建表后调用此接口确认表已成功创建

## 注意事项

1. `TableName` 参数格式为 `database.table`（如 `analytics.events`），包含数据库名
2. `NodeIp` 可通过 `DescribeInstance` 获取集群的访问地址 IP
3. 返回的 `CreateTableSql` 是完整的 DDL，可直接用于分析引擎、分区、排序键等信息
4. 如果 `Exists` 为 `false`，需检查表名和数据库名是否正确
5. 本接口为只读操作，不涉及数据读取，性能开销极小
