# GetMonitorData（MCP）

> Tool：`GetMonitorData` | MCP tool | 只读

## 功能描述

查询ES 集群监控指标时序数据（云监控 `QCE/CES` 命名空间），支持 CPU、JVM、磁盘、写入/查询性能等，**支持批量多实例**与可选的节点级维度。

> 📌 相比历史 tccli 方式，MCP tool 已封装 `Namespace`、`Instances[].Dimensions[]` 等嵌套结构，**只需传 `InstanceIds` 数组即可**，无需再手工构造 skeleton JSON。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Region` | String | ✅ | 地域，如 `ap-guangzhou` |
| `InstanceIds` | String[] | ✅ | 集群 ID **数组**，支持批量，如 `["es-aaa","es-bbb"]` |
| `MetricName` | String | ✅ | 指标名，见下方列表 |
| `StartTime` | String | ❌ | ISO 8601 (RFC3339)，如 `2026-08-05T19:00:00+08:00`，默认当前时间往前 1 小时 |
| `EndTime` | String | ❌ | ISO 8601 (RFC3339)，默认当前时间 |
| `Period` | Number | ❌ | 统计粒度（秒），常用 60/300/3600，默认 **300** |
| `NodeId` | String | ❌ | 节点 ID；传入则查节点级指标，不传则查集群聚合值 |

## 调用示例

```
# 单集群 CPU（最近 1 小时，默认）
GetMonitorData(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"], MetricName="CpuUsageMax")

# 指定时间窗口 + 粒度
GetMonitorData(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"],
               MetricName="DiskUsageMax", Period=300,
               StartTime="2026-08-05T09:00:00+08:00",
               EndTime="2026-08-05T10:00:00+08:00")

# 🚀 批量：一次取多个集群的同一指标（巡检场景强烈推荐）
GetMonitorData(Region="ap-guangzhou",
               InstanceIds=["es-aaa","es-bbb","es-ccc"],
               MetricName="CpuUsageMax", Period=300)
```

> 🚀 **巡检性能要点**：批量巡检时应**按指标维度循环**（8 个 CORE 指标 = 8 次调用，覆盖全部集群），而**不是**按集群循环（N 个集群 × 8 = N×8 次调用）。25 个集群场景下可从 200 次降至 8 次。

## 返回结构

```
{
  "DataPoints": [
    {
      "Dimensions": [{"Name": "uInstanceId", "Value": "es-xxxxxxxx"}],
      "Timestamps": [...],
      "Values": [...]
    },
    ...  // 批量查询时每个实例一项，通过 Dimensions 区分归属
  ],
  "StartTime": "...", "EndTime": "...", "Period": 300, "MetricName": "..."
}
```

> ⚠️ 批量查询时 `DataPoints` 有多项，**必须通过 `Dimensions[].Value` 把时序数据对应回具体集群**，不要按数组下标假定顺序。

## 指标列表

### CORE 指标（每次必查，8 个）

| 指标名 | 说明 | warn | critical |
|--------|------|------|----------|
| `CpuUsageMax` | 最大 CPU 使用率（%）| 60 | 90 |
| `JvmMemUsageMax` | 最大 JVM 内存使用率（%）| 80 | 90 |
| `DiskUsageMax` | 最大磁盘使用率（%）| 75 | 90 |
| `IndexLatencyAvg` | 平均写入延迟（ms）| 100 | 500 |
| `SearchLatencyAvg` | 平均查询延迟（ms）| 100 | 500 |
| `BulkRejectedCompletedPercent` | Bulk 拒绝率（%）| 0 | 0 |
| `Status` | 集群健康状态（0=Green，1=Yellow，2=Red）| — | — |
| `NodeOldGcDifMax` | 节点单周期 Old GC 次数最大值 | 1 | 1 |

### EXTENDED 指标（按触发规则补查，11 个）

| 指标名 | 说明 | warn | critical |
|--------|------|------|----------|
| `ShardNumLimitPercen` | 集群分片使用率（%）| 80 | 90 |
| `ClusterNumberOfPendingTasks` | Master 任务队列等待数 | 100 | 500 |
| `IsReadOnly` | 集群是否只读（1=只读）| 1 | 1 |
| `SearchQueueMax` | 最大查询线程队列排队数 | 10 | 50 |
| `SearchRejectedCompletedPercent` | 查询拒绝率（%）| 0 | 0 |
| `WriteQueueMax` | 最大写线程队列排队数 | 10 | 50 |
| `WriteRejectedDifMax` | 单周期最大写线程队列拒绝数 | 0 | 10 |
| `NodeDiskUtilMax` | 节点磁盘 IO 利用率最大值（%）| 80 | 95 |
| `NodeDiskAwaitMax` | 节点磁盘 IO 等待时间最大值（ms）| 20 | 100 |
| `JvmOldMemUsageMax` | 最大 JVM Old 区内存使用率（%）| 80 | 90 |
| `NodeParentBreakerDifMax` | 节点单周期熔断次数最大值 | 0 | 5 |

### 其他可用指标

`CpuUsageAvg`、`MemUsageAvg/Max`、`JvmMemUsageAvg`、`DiskUsageAvg`、`IndexLatencyMax`、`SearchLatencyMax`、`NodeNum`、`ActiveShardsPercent`、`IndexSpeed`（写入速度 次/s）、`SearchCompletedSpeed`（查询速度 次/s）、`NodeOldGcTimeDifMax`（Old GC 时间 ms）

### 常见指标名误用纠正

| 错误写法 | 正确指标名 |
|---------|-----------|
| `IndexingRate` / `IndexRate` / `WriteSpeed` | `IndexSpeed` |
| `SearchSpeed` / `SearchRate` | `SearchCompletedSpeed` |
| `CpuUsage` | `CpuUsageMax` |
| `JvmMemUsage` | `JvmMemUsageMax` |
| `DiskUsage` | `DiskUsageMax` |
| `IndexLatency` | `IndexLatencyAvg` |
| `SearchLatency` | `SearchLatencyAvg` |
| `BulkRejected` | `BulkRejectedCompletedPercent` |
| `OldGc` / `GcCount` | `NodeOldGcDifMax` |

## ⚠️ 哨兵值注意事项（最关键）

腾讯云云监控探针采集失败时（集群不可用、磁盘满导致探针失联、节点网络不通等）**不返回 null，而是返回 `-2`（偶见 `-1`）**。

**若直接读取 `Values` 原始值做判断，极易把 `-2` 误判为真实业务值** —— 例如把「磁盘使用率 -2%」误读成「磁盘只用了 2%，很健康」，从而完全反转结论。

**统计前必须先剔除 `-2` / `-1`**，全部为哨兵值时标记 `data_missing` 并展示 ❓。完整清洗算法见 [scoring-rules.md#哨兵值清洗算法](../scoring-rules.md#哨兵值清洗算法必须先做)。

**交叉验证建议**：怀疑探针失联时，用数据面 tool 核实真实状态 —— `CesClusterHealth`（真实健康色）、`CesGetAllocation`（各节点真实磁盘水位）。数据面直连不受探针影响。

## 错误码

| 错误码 | 含义 |
|------|------|
| `AuthFailure.*` | CAM 权限不足，需授予 `monitor:GetMonitorData` |
| `InvalidParameter.*` | MetricName 拼写错误或时间格式非 ISO 8601 |
