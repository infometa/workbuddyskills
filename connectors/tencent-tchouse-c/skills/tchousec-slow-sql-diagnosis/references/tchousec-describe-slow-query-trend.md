
# tchousec-describe-slow-query-trend

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeSlowQueryTrend` 云 API，获取指定集群在指定时间范围内的慢查询趋势统计数据。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeSlowQueryTrend`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称        | 必选 | 类型    | 描述                                                       |
| --------------- | ---- | ------- | ---------------------------------------------------------- |
| InstanceID      | 是   | String  | 集群实例 ID，格式如 `cdwch-xxxxxxxx`                       |
| Region          | 是   | String  | 地域，如 `ap-guangzhou`                                    |
| StartTime       | 是   | String  | 查询起始时间，格式 `YYYY-MM-DD HH:MM:SS`                   |
| EndTime         | 是   | String  | 查询结束时间，格式 `YYYY-MM-DD HH:MM:SS`                   |
| QueryDurationMs | 否   | Integer | 慢查询阈值（毫秒），只返回执行耗时 ≥ 该值的查询，默认 500  |
| VirtualCluster  | 否   | String  | 虚拟集群名称，如 `default_cluster`，不传则查询所有虚拟集群 |

## 输出参数

| 参数名称                      | 类型    | 描述                                                    |
| ----------------------------- | ------- | ------------------------------------------------------- |
| SlowQueryTrends               | Array   | 慢查询趋势数据列表                                      |
| SlowQueryTrends[].TimeSpan    | String  | 时间点，ISO 8601 格式（如 `2026-06-02T15:34:00+08:00`） |
| SlowQueryTrends[].Count       | Integer | 该时间段内慢查询数量                                    |
| SlowQueryTrends[].AvgDuration | Integer | 该时间段内平均执行耗时（毫秒）                          |
| SlowQueryTrends[].MaxDuration | Integer | 该时间段内最大执行耗时（毫秒）                          |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeSlowQueryTrend",
  "Version": "2020-09-15",
  "Region": "ap-chongqing",
  "InstanceID": "cdwch-xxxxxxxx",
  "StartTime": "2026-06-02 16:45:34",
  "EndTime": "2026-06-02 17:45:34",
  "QueryDurationMs": 500,
  "VirtualCluster": "default_cluster"
}
```

### 响应示例

```json
{
  "Response": {
    "RequestId": "01a7ede8-cc6e-44e9-82d3-7f209b34c041",
    "SlowQueryTrends": [
      {
        "TimeSpan": "2026-06-02T15:34:00+08:00",
        "Count": 5,
        "AvgDuration": 81,
        "MaxDuration": 154
      },
      {
        "TimeSpan": "2026-06-02T15:37:00+08:00",
        "Count": 2,
        "AvgDuration": 100,
        "MaxDuration": 170
      },
      {
        "TimeSpan": "2026-06-02T16:32:00+08:00",
        "Count": 2,
        "AvgDuration": 2,
        "MaxDuration": 3
      }
    ]
  }
}
```

## 典型使用场景

- **趋势判断**：判断慢查询是突发性（某个时间点突然增多）还是持续恶化（逐渐增多）
- **关联变更**：如果某个时间点慢查询突增，可能与代码发布、数据导入、配置变更相关
- **基线对比**：对比正常时段和异常时段的慢查询数量，量化问题严重程度
- **辅助报告**：在诊断报告中展示趋势图，帮助用户直观理解问题

## 分析策略

| 趋势特征     | 可能原因                   | 建议动作                    |
| ------------ | -------------------------- | --------------------------- |
| 某时间点突增 | 代码发布/数据导入/配置变更 | 排查该时间点前后的变更      |
| 持续增长     | 数据量增长/索引退化        | 检查表数据量和索引有效性    |
| 周期性波动   | 定时任务/报表查询          | 优化定时任务 SQL 或错峰执行 |
| 平稳但数量多 | SQL 本身效率低             | 重点优化 Top N 慢 SQL       |
