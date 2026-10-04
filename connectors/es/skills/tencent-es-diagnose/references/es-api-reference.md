# 腾讯云 ES API 参考文档（索引与横向知识）

官方文档：https://cloud.tencent.com/document/product/845

> 本文档只保留**跨接口的横向知识**（地域列表、监控指标目录、错误码总表、ES 常见错误日志分析）。
> 单接口的完整请求参数/响应字段/调用示例统一维护在 [references/api/](api/) 目录下的独立文档中，
> 本文档不再重复这些表格，避免同一份参数信息出现两处、改一处漏一处。

## 目录

1. [地域列表](#地域列表)
2. [接口文档索引](#接口文档索引)
3. [监控指标列表（QCE/CES）](#监控指标列表)
4. [错误码说明](#错误码说明)
5. [ES 常见错误日志分析](#es-常见错误日志分析)

---

## 地域列表

| 地域标识              | 地域名称   |
|---------------------|----------|
| `ap-guangzhou`      | 广州       |
| `ap-shanghai`       | 上海       |
| `ap-beijing`        | 北京       |
| `ap-chengdu`        | 成都       |
| `ap-chongqing`      | 重庆       |
| `ap-nanjing`        | 南京       |
| `ap-hongkong`       | 香港       |
| `ap-singapore`      | 新加坡     |
| `ap-bangkok`        | 曼谷       |
| `ap-tokyo`          | 东京       |
| `ap-seoul`          | 首尔       |
| `ap-mumbai`         | 孟买       |
| `na-siliconvalley`  | 硅谷       |
| `na-ashburn`        | 弗吉尼亚   |
| `eu-frankfurt`      | 法兰克福   |

---

## 接口文档索引

各tool 的完整参数、响应字段、调用示例、常见陷阱、错误码，见对应独立文档：

| MCP Tool | 类型 | 完整文档 |
|----------|------|---------|
| `DescribeInstances` | 管控面 | [api/DescribeInstances.md](api/DescribeInstances.md) |
| `DescribeInstanceLogs` | 管控面 | [api/DescribeInstanceLogs.md](api/DescribeInstanceLogs.md) |
| `DescribeInstanceOperations` | 管控面 | [api/DescribeInstanceOperations.md](api/DescribeInstanceOperations.md) |
| `GetMonitorData` | 云监控 | [api/GetMonitorData.md](api/GetMonitorData.md) |
| `CesClusterHealth`、`CesGetAllocation`、`CesClusterAllocationExplain`、`CesGetShards`、`CesClusterPendingTasks`、`CesGetNode`、`CesTasks`、`CesGetClusterSettings`、`CesListIndices` 等 | **ES 数据面（只读）** | [api/data-plane-tools.md](api/data-plane-tools.md) |

> 全部通过 MCP tools 调用，鉴权在宿主层完成，本Skill 不接触密钥。

---

## 监控指标列表

**命名空间**：`QCE/CES`
**接口**：`GetMonitorData`（云监控）
**文档**：https://cloud.tencent.com/document/product/248/45115

### 集群级别指标

| 指标名                          | 单位  | 说明                    |
|-------------------------------|-----|------------------------|
| `CpuUsageAvg`                 | %   | 平均 CPU 使用率           |
| `CpuUsageMax`                 | %   | 最大 CPU 使用率           |
| `MemUsageAvg`                 | %   | 平均内存使用率             |
| `MemUsageMax`                 | %   | 最大内存使用率             |
| `JvmMemUsageAvg`              | %   | 平均 JVM 内存使用率        |
| `JvmMemUsageMax`              | %   | 最大 JVM 内存使用率        |
| `DiskUsageAvg`                | %   | 平均磁盘使用率             |
| `DiskUsageMax`                | %   | 最大磁盘使用率             |
| `IndexLatencyAvg`             | ms  | 平均写入延迟               |
| `IndexLatencyMax`             | ms  | 最大写入延迟               |
| `SearchLatencyAvg`            | ms  | 平均查询延迟               |
| `SearchLatencyMax`            | ms  | 最大查询延迟               |
| `IndexSpeed`                  | 次/s | 写入速度                  |
| `SearchCompletedSpeed`        | 次/s | 查询速度                  |
| `BulkRejectedCompletedPercent`| %   | Bulk 拒绝率               |
| `SearchRejectedCompletedPercent`| % | 查询拒绝率                |
| `Status`                      | -   | 集群健康状态（0=Green，1=Yellow，2=Red）|
| `ActiveShardsPercent`         | %   | 活跃分片百分比             |
| `NodeNum`                     | 个  | 节点数量                  |
| `NodeOldGcDifMax`             | 次  | 节点单周期 Old GC 次数_最大值 |
| `NodeOldGcTimeDifMax`         | ms  | 节点单周期 Old GC 时间_最大值 |

> EXTENDED 深度指标（`ShardNumLimitPercen`、`ClusterNumberOfPendingTasks`、`IsReadOnly` 等 11 个）及触发规则见 [metrics-design.md](metrics-design.md)；调用格式见 [api/GetMonitorData.md](api/GetMonitorData.md)。

### 统计粒度

| Period（秒） | 说明                    |
|------------|------------------------|
| 60         | 1 分钟（最细粒度）        |
| 300        | 5 分钟                  |
| 3600       | 1 小时                  |
| 86400      | 1 天                    |

---

## 错误码说明

| 错误码                              | 说明                                    |
|-----------------------------------|----------------------------------------|
| `AuthFailure`                     | 认证失败，检查 SecretId/SecretKey        |
| `AuthFailure.SignatureExpire`     | 签名过期，检查系统时间是否准确            |
| `ResourceNotFound.InstanceNotExist`| 集群不存在，检查集群 ID 和地域           |
| `InvalidParameter`                | 参数错误，检查请求参数格式               |
| `RequestLimitExceeded`            | 接口限频（20次/秒），稍后重试            |
| `InternalError`                   | 内部错误，稍后重试或联系腾讯云支持       |
| `UnauthorizedOperation`           | 无权限，检查 CAM 策略是否包含 ES 权限    |

---

## ES 常见错误日志分析

### 1. CircuitBreakingException（内存熔断）

```
CircuitBreakingException: [parent] Data too large, data for [<http_request>] would be [xxx/xxxmb], which is larger than the limit of [xxx/xxxmb]
```

**原因**：JVM 堆内存使用率过高，触发熔断保护
**关联指标**：`JvmMemUsageMax` > 85%
**建议**：
- 升级节点规格（增加内存）
- 优化查询语句，减少聚合深度
- 调整熔断阈值（不推荐，治标不治本）
- 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/circuit-breaker.html

### 2. rejected execution（线程池拒绝）

```
EsRejectedExecutionException: rejected execution of org.elasticsearch.transport.TransportService$7@xxx on EsThreadPoolExecutor[name = xxx/write, queue capacity = 200, ...]
```

**原因**：写入/查询线程池队列已满，新请求被拒绝
**关联指标**：`BulkRejectedCompletedPercent` > 1%
**建议**：
- 降低写入并发，增加批量写入大小
- 升级节点规格
- 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-threadpool.html

### 3. DiskWatermarkException（磁盘水位线）

```
flood stage disk watermark [95%] exceeded on [xxx][xxx][xxx] free: xxx[xxx], all indices on this node will be marked read-only
```

**原因**：磁盘使用率超过 95%，集群进入只读模式
**关联指标**：`DiskUsageMax` > 85%
**建议**：
- 立即扩容磁盘或删除不必要的索引
- 执行 `PUT /_cluster/settings` 解除只读模式（需先扩容）
- 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/disk-usage-exceeded.html

### 4. master_not_discovered（Master 未发现）

```
master_not_discovered exception; existing master [null]
```

**原因**：Master 节点不可用，可能是 Master 宕机或网络分区
**建议**：
- 检查 Master 节点状态和日志
- 查看变更记录是否有节点重启操作
- 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/discovery-troubleshooting.html

### 5. OutOfMemoryError（JVM OOM）

```
java.lang.OutOfMemoryError: Java heap space
```

**原因**：JVM 堆内存耗尽
**关联指标**：`JvmMemUsageMax` 持续 > 90%，`NodeOldGcDifMax` 频繁
**建议**：
- 立即升级节点规格
- 检查是否有大查询（深度分页、大聚合）
- 参考：https://www.elastic.co/guide/en/elasticsearch/reference/current/heap-size.html

### 6. NodeDisconnectedException（节点断连）

```
NodeDisconnectedException: [xxx][xxx:9300] Node disconnected
```

**原因**：节点间通信中断，可能是网络问题或节点 OOM 重启
**建议**：
- 查看对应节点的 GC 日志
- 检查节点 CPU/内存监控
- 查看变更记录是否有节点重启
