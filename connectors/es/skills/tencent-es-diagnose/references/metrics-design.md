# 健康检查指标分层设计

> **文档目的**：说明健康检查的指标分层策略，指导后续指标扩展。
> **唯一权威来源**：本文档的阈值必须与 [scoring-rules.md](scoring-rules.md) 中的判定表逐项对齐；改动阈值请同时改两处。

---

## 设计原则

日常巡检只查最关键的 CORE 指标，避免对正常集群产生不必要的 API 调用开销。
当 CORE 指标发现异常时，**自动**按触发规则补查对应的 EXTENDED 深度指标，精准定位根因。

```
正常集群：CORE 指标（8个）→ 快速评分 → 结束
异常集群：CORE 指标 → 触发规则 → 自动补查 EXTENDED 指标 → 深度评分
```

---

## 第一层：CORE 指标（日常巡检必查）

每次健康检查都会查，用于基础评分和触发判断。

| 指标名 | 说明 | 告警阈值 | 严重阈值 |
|--------|------|---------|---------|
| `CpuUsageMax` | 最大 CPU 使用率 | 60% | 90% |
| `JvmMemUsageMax` | 最大 JVM 内存使用率 | 80% | 90% |
| `DiskUsageMax` | 最大磁盘使用率 | 75% | 90%（另有 95% 一票否决档，见 [scoring-rules.md](scoring-rules.md)） |
| `IndexLatencyAvg` | 平均写入延迟 | 100ms | 500ms |
| `SearchLatencyAvg` | 平均查询延迟 | 100ms | 500ms |
| `BulkRejectedCompletedPercent` | Bulk 写入拒绝率 | > 0%（无分级，只要 >0 即扣分） | > 0% |
| `Status` | 集群健康状态（0=Green/1=Yellow/2=Red） | Yellow | Red |
| `NodeOldGcDifMax` | 节点单周期 Old GC 次数_最大值 | ≥1次（一票否决 ≤40分） | ≥1次 |

---

## 第二层：EXTENDED 指标（按触发条件补查）

### 触发规则

| 触发条件 | 补查指标 | 排查方向 |
|---------|---------|---------|
| `Status >= 1`（Yellow/Red） | `ShardNumLimitPercen`<br>`ClusterNumberOfPendingTasks`<br>`IsReadOnly` | 分片数打满 / Master 任务积压 / 磁盘触发只读锁 |
| `SearchLatencyAvg` ≥ 告警阈值 | `SearchQueueMax`<br>`SearchRejectedCompletedPercent` | 查询线程池积压 / 查询被拒绝 |
| `BulkRejectedCompletedPercent` > 0 | `WriteQueueMax`<br>`WriteRejectedDifMax` | 写线程池积压 / 单周期写拒绝次数 |
| `DiskUsageMax` ≥ 告警阈值 | `NodeDiskUtilMax`<br>`NodeDiskAwaitMax`<br>`IsReadOnly` | 磁盘 IO 打满 / IO 延迟高 / 是否已触发只读 |
| `JvmMemUsageMax` ≥ 告警阈值 | `JvmOldMemUsageMax`<br>`NodeParentBreakerDifMax` | Old 区堆压力 / 熔断触发次数 |
| `CpuUsageMax` ≥ 告警阈值 | `NodeDiskUtilMax`<br>`NodeDiskAwaitMax` | 排查 CPU 高是否由 IO 阻塞引起 |

### 补查指标说明

| 指标名 | 说明 | 参考阈值 |
|--------|------|---------|
| `ShardNumLimitPercen` | 集群分片使用率 | > 80% 告警，> 90% 严重 |
| `ClusterNumberOfPendingTasks` | Master 任务队列等待数 | > 100 告警，> 500 严重（500-1000/>1000 更细分级见 [scoring-rules.md](scoring-rules.md)） |
| `IsReadOnly` | 集群是否只读（1=只读） | = 1 立即告警 |
| `SearchQueueMax` | 集群节点最大查询线程队列排队数 | > 10 告警，> 50 严重 |
| `SearchRejectedCompletedPercent` | 查询拒绝率 | > 0%（无分级，只要 >0 即扣分） |
| `WriteQueueMax` | 集群节点最大写线程队列排队数 | > 10 告警，> 50 严重 |
| `WriteRejectedDifMax` | 单周期集群节点最大写线程队列拒绝数 | > 0 告警，> 10 严重 |
| `NodeDiskUtilMax` | 节点磁盘 IO 使用率_最大值 | > 80% 告警，> 95% 严重 |
| `NodeDiskAwaitMax` | 节点磁盘 IO 操作等待时间_最大值 | > 20ms 告警，> 100ms 严重 |
| `JvmOldMemUsageMax` | 最大 JVM Old 区内存使用率 | > 80% 告警，> 90% 严重 |
| `NodeParentBreakerDifMax` | 节点单周期熔断次数_最大值 | > 0 告警，> 5 严重 |

---

## 全量补查模式（人工兜底）

用户明确要求"深度体检 / 全面检查"，或集群已被判定为低分（`score < 85`）需深度诊断时，
可**忽略触发规则，直接补查全部 EXTENDED 指标**。默认行为仍是按触发规则按需补查。

---

## 分层决策流程

```
健康检查工作流启动
        │
        ▼
  查 CORE 指标（8个，GetMonitorData）
        │
        ▼
  哨兵值清洗（剔除 -2/-1）
        │
        ├─ 无异常 ──→ 评分 → 输出报告（结束）
        │
        └─ 有异常 ──→ 匹配触发规则
                            │
                            ▼
                    补查对应 EXTENDED 指标
                            │
                            ▼
                    深度评分 → 输出报告（含根因提示）
```

---

## 扩展说明

- **为什么 Old GC 用 Max 不用 Avg**：Max 能发现热点节点的 GC 压力，Avg 会被正常节点稀释。
- **为什么 DiskUsageMax 触发 IO 指标**：磁盘使用率高时写性能下降，IO await 升高是写入延迟的常见根因，需交叉验证。
- **IsReadOnly 在两处触发**：磁盘满（`DiskUsageMax`）和集群异常（`Status`）都可能触发只读锁，需优先确认。
