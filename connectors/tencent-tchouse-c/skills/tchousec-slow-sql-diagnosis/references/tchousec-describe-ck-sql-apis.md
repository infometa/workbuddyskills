
# tchousec-describe-ck-sql-apis

## 功能说明

连接 TCHouse-C（ClickHouse）集群，对指定 SQL 执行 EXPLAIN 语句，获取查询执行计划。通过分析执行计划可以识别性能瓶颈。

## 接口信息

- **实现方式**：MCP tool（连接 ClickHouse 执行 EXPLAIN）
- **安全限制**：仅允许执行 EXPLAIN 前缀的语句，不执行实际查询
- **性能影响**：EXPLAIN 不实际执行查询，不会对集群产生负载

## 输入参数

| 参数名称    | 必选 | 类型   | 描述                                                                           |
| ----------- | ---- | ------ | ------------------------------------------------------------------------------ |
| InstanceId  | 是   | String | 集群实例 ID，格式如 `cdwch-xxxxxxxx`                                           |
| Region      | 是   | String | 地域，如 `ap-guangzhou`                                                        |
| SQL         | 是   | String | 待分析的 SQL 语句（不需要加 EXPLAIN 前缀，工具会自动添加）                     |
| ExplainType | 否   | String | EXPLAIN 类型，默认 `PLAN`。可选值：`PLAN`/`PIPELINE`/`ESTIMATE`/`AST`/`SYNTAX` |

## ExplainType 说明

| 类型       | 说明                   | 适用场景                          |
| ---------- | ---------------------- | --------------------------------- |
| `PLAN`     | 查询执行计划（默认）   | 分析读取路径、索引使用、JOIN 策略 |
| `PIPELINE` | 查询处理管道           | 分析数据流转和并行度              |
| `ESTIMATE` | 预估读取的行数和字节数 | 快速评估查询代价                  |
| `AST`      | 抽象语法树             | 分析 SQL 解析结果                 |
| `SYNTAX`   | 优化后的 SQL           | 查看 ClickHouse 的 SQL 重写结果   |

## 输出参数

| 参数名称      | 类型    | 描述                 |
| ------------- | ------- | -------------------- |
| ExplainResult | String  | 执行计划文本（多行） |
| Success       | Boolean | 是否执行成功         |
| ErrorMessage  | String  | 错误信息（失败时）   |

## 使用示例

### 请求示例

```json
{
  "InstanceId": "cdwch-xxxxxxxx",
  "Region": "ap-guangzhou",
  "SQL": "SELECT * FROM analytics.events WHERE event_date = '2024-01-05' AND user_id = 12345 ORDER BY timestamp",
  "ExplainType": "PLAN"
}
```

### 响应示例（正常有数据的表）

```
Expression ((Project names + (Projection + Change column names to column identifiers)))
  Sorting (Sorting for ORDER BY)
    Expression (Before ORDER BY)
      ReadFromMergeTree (analytics.events)
        Indexes:
          PrimaryKey
            Keys: event_date, user_id
            Condition: (event_date in ['2024-01-05', '2024-01-05']) AND (user_id in [12345, 12345])
            Parts: 3/150
            Granules: 12/45000
          Skip
            Name: idx_timestamp
            Description: minmax GRANULARITY 3
            Parts: 3/3
            Granules: 10/12
```

### 响应示例（全表扫描 - 性能问题）

```
Expression ((Project names + (Projection + Change column names to column identifiers)))
  Sorting (Sorting for ORDER BY)
    Expression (Before ORDER BY)
      ReadFromMergeTree (analytics.events)
        Indexes:
          PrimaryKey
            Keys: event_date
            Condition: event_date in ['2024-01-05', '2024-01-05']
            Parts: 50/150
            Granules: 40000/45000
```

## 执行计划解读指南

### 关键节点含义

| 节点                                 | 含义                       |
| ------------------------------------ | -------------------------- |
| `ReadFromMergeTree`                  | 从 MergeTree 表读取数据    |
| `ReadNothing (Read from NullSource)` | 表为空或优化器判断无需读取 |
| `Expression`                         | 表达式计算（投影、过滤等） |
| `Sorting`                            | 排序操作                   |
| `Aggregating`                        | 聚合操作                   |
| `Join`                               | JOIN 操作                  |
| `Union`                              | UNION 操作                 |
| `Filter`                             | 过滤操作                   |

### 索引使用分析

在 `ReadFromMergeTree` 节点下的 `Indexes` 部分：

```
Indexes:
  PrimaryKey
    Keys: [使用的主键列]
    Condition: [过滤条件]
    Parts: 使用的Parts数/总Parts数
    Granules: 使用的Granules数/总Granules数
  Skip
    Name: [跳数索引名]
    Description: [索引类型]
    Parts: 过滤后Parts数/输入Parts数
    Granules: 过滤后Granules数/输入Granules数
```

### 性能问题判断标准

| 指标              | 正常         | 异常（需优化）             |
| ----------------- | ------------ | -------------------------- |
| Granules 使用比例 | < 30%        | > 80%（接近全表扫描）      |
| Parts 使用比例    | < 50%        | > 90%（分区裁剪失败）      |
| 是否有 Skip 索引  | 有           | 无（可能需要添加跳数索引） |
| Sorting 节点      | 无或数据量小 | 对大量数据排序             |
| Join 右表大小     | 小表         | 大表（需调整 JOIN 顺序）   |

## 典型使用场景

- **核心诊断工具**：通过执行计划直接定位性能瓶颈
- **索引有效性验证**：确认查询是否命中主键索引和跳数索引
- **分区裁剪验证**：确认分区条件是否生效
- **JOIN 策略分析**：确认 JOIN 算法和表的驱动顺序
- **优化效果验证**：改写 SQL 后重新 EXPLAIN 对比效果
