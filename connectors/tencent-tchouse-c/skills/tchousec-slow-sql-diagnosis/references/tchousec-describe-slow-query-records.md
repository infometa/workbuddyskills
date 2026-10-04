
# tchousec-describe-slow-query-records

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeSlowQueryRecords` 云 API，获取指定集群在指定时间范围内的慢查询明细记录。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeSlowQueryRecords`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称          | 必选 | 类型    | 描述                                                                                        |
| ----------------- | ---- | ------- | ------------------------------------------------------------------------------------------- |
| InstanceId        | 是   | String  | 集群实例 ID，格式如 `cdwch-xxxxxxxx`                                                        |
| Region            | 是   | String  | 地域，如 `ap-guangzhou`                                                                     |
| StartTime         | 是   | String  | 查询起始时间，格式 `YYYY-MM-DD HH:MM:SS`                                                    |
| EndTime           | 是   | String  | 查询结束时间，格式 `YYYY-MM-DD HH:MM:SS`                                                    |
| QueryDurationMs   | 否   | Integer | 慢查询阈值（毫秒），只返回执行耗时 ≥ 该值的查询，默认 500                                   |
| PageSize          | 否   | Integer | 每页返回条数，默认 10，最大 200                                                             |
| PageNum           | 否   | Integer | 页码，从 1 开始，默认 1                                                                     |
| SortColumn        | 否   | String  | 排序字段，可选值：`query_duration_ms`（执行耗时）、`query_start_time`（查询开始时间，默认） |
| SortOrder         | 否   | String  | 排序方式：`DESC`（降序，默认）/ `ASC`（升序）                                               |
| SlowQueryUser     | 否   | String  | 按用户过滤                                                                                  |
| SlowQueryDatabase | 否   | String  | 按数据库过滤                                                                                |
| VirtualCluster    | 否   | String  | 虚拟集群名称，如 `default_cluster`，不传则查询所有虚拟集群                                  |

## 输出参数

| 参数名称                           | 类型    | 描述                                                          |
| ---------------------------------- | ------- | ------------------------------------------------------------- |
| TotalCount                         | Integer | 慢查询总条数                                                  |
| SlowQueryRecords                   | Array   | 慢查询记录列表                                                |
| SlowQueryRecords[].Sql             | String  | SQL 文本                                                      |
| SlowQueryRecords[].DurationMs      | Integer | 执行耗时（毫秒）                                              |
| SlowQueryRecords[].QueryStartTime  | String  | 查询开始时间，ISO 8601 格式（如 `2026-06-02T16:32:16+08:00`） |
| SlowQueryRecords[].ReadRows        | Integer | 读取行数                                                      |
| SlowQueryRecords[].ReadBytes       | Integer | 读取字节数                                                    |
| SlowQueryRecords[].ResultBytes     | Integer | 结果字节数                                                    |
| SlowQueryRecords[].MemoryUsage     | Integer | 内存使用量（字节）                                            |
| SlowQueryRecords[].OsUser          | String  | 执行用户                                                      |
| SlowQueryRecords[].CurrentDatabase | String  | 当前数据库名（可能为空）                                      |
| SlowQueryRecords[].InitialAddress  | String  | 客户端 IP 地址                                                |
| SlowQueryRecords[].NodeIp          | String  | 执行该查询的 ClickHouse 节点 IP                               |
| SlowQueryRecords[].InitialQueryId  | String  | 查询唯一标识 ID，可用于关联 query_log                         |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeSlowQueryRecords",
  "Version": "2020-09-15",
  "Region": "ap-guangzhou",
  "InstanceId": "cdwch-xxxxxxxx",
  "StartTime": "2024-01-01 00:00:00",
  "EndTime": "2024-01-07 23:59:59",
  "QueryDurationMs": 500,
  "PageSize": 10,
  "PageNum": 1,
  "SortColumn": "query_duration_ms",
  "SortOrder": "DESC",
  "VirtualCluster": "default_cluster"
}
```

### 响应示例

```json
{
  "Response": {
    "TotalCount": 13,
    "SlowQueryRecords": [
      {
        "NodeIp": "9.0.16.5",
        "OsUser": "gp",
        "InitialAddress": "30.173.162.190",
        "InitialQueryId": "001fe732-95a9-4ca7-bca8-0a238dd34f93",
        "Sql": "SELECT * FROM system.asynchronous_inserts;",
        "QueryStartTime": "2026-06-02T16:32:16+08:00",
        "DurationMs": 3,
        "ReadRows": 0,
        "ReadBytes": 0,
        "ResultBytes": 1915,
        "MemoryUsage": 5673907,
        "CurrentDatabase": ""
      },
      {
        "NodeIp": "9.0.16.5",
        "OsUser": "gp",
        "InitialAddress": "30.50.81.151",
        "InitialQueryId": "b91dc845-e61f-4b66-9fb2-11584eac8d8f",
        "Sql": "EXPLAIN PLAN\nSELECT * FROM repl_db.normal_table;",
        "QueryStartTime": "2026-06-02T15:37:23+08:00",
        "DurationMs": 31,
        "ReadRows": 2,
        "ReadBytes": 139,
        "ResultBytes": 4352,
        "MemoryUsage": 5676403,
        "CurrentDatabase": ""
      }
    ],
    "RequestId": "4370a546-1b14-4034-8a6f-ebd326cbe181"
  }
}
```

## 典型使用场景

- **获取 Top N 慢 SQL**：通过 `SortColumn: query_duration_ms` 按耗时降序排列，获取最慢的 N 条 SQL
- **时间范围过滤**：根据用户描述的时间范围精确检索
- **初步判断瓶颈**：通过 `ReadRows`/`MemoryUsage` 等指标初步判断是 IO 密集还是内存密集
- **关联分析**：通过 `OsUser`/`CurrentDatabase` 字段关联到具体业务
- **节点定位**：通过 `NodeIp` 判断慢查询是否集中在某个节点（数据倾斜/热点）
- **查询追踪**：通过 `InitialQueryId` 可在 `system.query_log` 中追踪更详细的执行信息

## 参数确定策略

| 用户描述     | StartTime     | EndTime       | 说明         |
| ------------ | ------------- | ------------- | ------------ |
| "最近一周"   | 7天前         | 当前时间      |              |
| "昨天"       | 昨天 00:00:00 | 今天 00:00:00 |              |
| "最近一小时" | 1小时前       | 当前时间      |              |
| "上个月"     | 上月1日       | 本月1日       |              |
| 未指定       | 7天前         | 当前时间      | 默认最近一周 |
