# 端到端诊断场景（Scenarios）

> 本文档为 [SKILL.md](../SKILL.md) 的详细参考。SKILL.md 中的场景索引会指向此处。
>
> **调用方式**：全部使用 MCP tools。下文以 `ToolName(参数...)` 形式表示，实际执行时调用对应 MCP tool。

## 通用约定

**取监控指标**（`Region` 均为必填，示例统一用 `ap-guangzhou`）：

```
GetMonitorData(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"],
               MetricName="<指标名>", Period=300,
               StartTime="<ISO8601>", EndTime="<ISO8601>")
```

- `InstanceIds` 是**数组**，可一次传多个集群批量取同一指标
- 不传时间范围默认最近 1 小时
-时间格式：`2026-08-05T18:00:00+08:00`

> 🔴 **哨兵值**：`DataPoints[].Values` 中的 `-2`/`-1` 是探针失联标记，**不是**真实业务值。统计前必须剔除；全部为哨兵值时视为「无有效数据」并展示 ❓。详见 [scoring-rules.md#哨兵值清洗算法](scoring-rules.md#哨兵值清洗算法必须先做)。怀疑失联时用 `CesClusterHealth` / `CesGetAllocation` 数据面核实。

**日志 LogType**：`1`=主日志，`2`=**搜索慢日志**，`3`=**索引慢日志**，`4`=**GC 日志**。查询慢用 `2`、写入慢用 `3`，GC 用 `4`。

> ✅ **过滤下推**：`LogLevels=["ERROR","WARN"]`（级别）、`SearchKey="message:xxx"`（LUCENE 关键字）、`StartTime`/`EndTime`（格式 `YYYY-MM-DD HH:mm:ss`，**注意与 `GetMonitorData` 的 ISO 8601 不同**）、`Limit`（最大 100）均已支持。**下文示例为节省篇幅省略了这些参数，实际调用时应尽量带上**，不要拉全量再本地过滤。详见 [api/DescribeInstanceLogs.md](api/DescribeInstanceLogs.md#-过滤必须下推到接口不要拉全量再本地过滤)。

---

## 场景 A：集群 Red 根因分析

**Gather（收集）**

```
# Step 1: 取真实健康色（最权威，优先于 DescribeInstances.HealthStatus）
CesClusterHealth(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")

# Step 2: 集群基本信息 + CORE 指标（Status>=1 触发 ShardNumLimitPercen /
#         ClusterNumberOfPendingTasks / IsReadOnly 补查）
DescribeInstances(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"])
GetMonitorData(..., MetricName="DiskUsageMax", ...)      # Red 最常见根因
GetMonitorData(..., MetricName="Status", ...)
GetMonitorData(..., MetricName="IsReadOnly", ...)
GetMonitorData(..., MetricName="ShardNumLimitPercen", ...)

# Step 3: 主日志，定位分片无法分配的报错（下推级别过滤，只取 ERROR/WARN）
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=1,
                     LogLevels=["ERROR","WARN"], StartTime="<起>", EndTime="<止>")

# Step 4: 确认是否有变更操作触发（节点重启/扩缩容）
DescribeInstanceOperations(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                           StartTime="<最近24小时起始>", EndTime="<当前时间>")

# Step 5: 一钉定音——直接问 ES 为什么不分配
CesClusterAllocationExplain(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")

# 配套：节点视角+ 分片视角 + 各节点磁盘水位
CesGetNode(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
CesGetShards(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
CesGetAllocation(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
```

**Diagnose（判断）**

先用 `CesClusterHealth` 确认真实健康色与 `unassigned_shards` 数量，再用指标缩小范围、日志确认。**`CesClusterAllocationExplain` 是最权威的手段** —— ES 会直接说明为什么某分片不能分配（`allocate_explanation` 字段）。

`CesClusterAllocationExplain` 响应关键读法：

| JSON 字段 | 含义 |
|---------|------|
| `index` / `shard` / `primary` | 究竟哪个索引的哪个主分片出了问题 |
| `current_state` | `unassigned` = 没落地；`initializing` = 正在分配 |
| `unassigned_info.reason` | 未分配根因（见下表）|
| `can_allocate` | `no` = 无法分配；配合 `allocate_explanation` 读自然语言解释 |
| `node_allocation_decisions[].deciders[]` | 每个节点被拒绝的具体原因（`disk_threshold`、`shards_limit`、`same_shard`）|

常见 `unassigned_info.reason` 映射：

| reason | 含义 | 对应原因 |
|--------|------|---------|
| `NODE_LEFT` | 节点离线后的分片丢失 | 节点宕机、重启中 |
| `ALLOCATION_FAILED` | 尝试分配失败（结合 `allocate_explanation`）| 磁盘水位、分片锁冲突、未知异常 |
| `CLUSTER_RECOVERED` | 集群刚恢复，分片正在重分配 | 正常过渡状态 |
| `INDEX_CREATED` | 新索引还没分配完 | 正常瞬态 |
| `DANGLING_INDEX_IMPORTED` | 悬空索引导入 | 通常伴随集群重建 |

| 现象组合 | 根因方向 |
|---------|---------|
| Red + `IsReadOnly=1` + `DiskUsageMax` > 95% | **磁盘 flood_stage**：超过 95% 触发强制只读，主分片被锁导致 Red |
| Red + `DiskUsageMax` > 85% + `DiskWatermarkException` 日志 | **磁盘 watermark**：超过 85% 停止分配新分片，持续升高后变 Red |
| Red + `ShardNumLimitPercen` > 90% | **分片数超上限**：无法分配新分片，导致部分主分片 unassigned |
| Red + `ClusterNumberOfPendingTasks` > 50 | **Master 过载**：任务队列积压，分片分配指令无法执行 |
| Red + `master_not_discovered` 日志 | **Master 宕机/脑裂**：Master 节点不可用，整个集群进入 Red |
| Red + `ShardLockObtainFailedException` 日志 + 有节点重启变更记录 | **分片锁冲突**：节点重启后分片锁未释放，通常短暂自愈 |
| Red + `NodeNum` 下降 + 无变更记录 | **节点异常宕机**：非计划内节点丢失，主分片不可用 |

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| 磁盘 flood_stage（只读）| **优先扩容磁盘至 ≤70%**；扩容后解除只读锁：`PUT /_all/_settings {"index.blocks.read_only_allow_delete": null}`；仅紧急且确认有旧数据可删时才清理索引 |
| 磁盘 watermark | 扩容磁盘使使用率降至 85% 以下（推荐 ≤70%）；配置 ILM 策略避免再次触发 |
| 分片数超上限 | 合并或删除小索引；调整 `cluster.max_shards_per_node` 前先评估合理性 |
| Master 过载 | 检查是否有大量索引频繁创建/删除；减少元数据操作频率；用 `CesClusterPendingTasks` 看积压任务类型 |
| Master 宕机/脑裂 | 查变更记录确认是否有计划内重启；持续不恢复联系腾讯云售后 |
| 分片锁冲突 | 等待节点完全重启后自动解决（通常 5-10 分钟）；持续不恢复联系售后 |
| 节点异常宕机 | 查主日志定位宕机原因（OOM/硬件故障）；联系腾讯云售后排查底层问题 |

> ⚠️ 解除只读锁、删除索引等**写操作本Skill 无法执行**，只能输出建议由用户在控制台/Kibana 操作。

---

## 场景 B：CPU 持续高排查

**Gather（收集）**

```
# Step 1: CORE 指标（CpuUsageMax >= 60% 触发 NodeDiskUtilMax / NodeDiskAwaitMax 补查）
GetMonitorData(..., MetricName="CpuUsageMax", StartTime="<最近6小时>", ...)

# Step 2: 交叉验证——判断 CPU 高的根因方向
GetMonitorData(..., MetricName="SearchLatencyAvg", ...)
GetMonitorData(..., MetricName="IndexLatencyAvg", ...)
GetMonitorData(..., MetricName="NodeOldGcDifMax", ...)
GetMonitorData(..., MetricName="NodeDiskUtilMax", ...)
GetMonitorData(..., MetricName="BulkRejectedCompletedPercent", ...)

# Step 3: 按方向查对应日志
DescribeInstanceLogs(..., LogType=2)   # 搜索慢日志（查询压力方向）
DescribeInstanceLogs(..., LogType=3)   # 索引慢日志（写入压力方向）
DescribeInstanceLogs(..., LogType=4)   # GC 日志（GC 压力方向）

# Step 4: 深度诊断——看正在执行的任务，定位 CPU 消耗来源
CesTasks(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
CesGetNode(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")   # 各节点 load_1m
```

**Diagnose（判断）**

先判断 CPU 高的**形态**，再对应查根因：

| CPU 高的形态 | 判断依据 | 下一步 |
|------------|---------|-------|
| 持续高（>80%，无回落）| `CpuUsageMax` 时序无明显波谷 | 排查常驻高负载：大聚合/高写入速率/IO 阻塞 |
| 周期性高（定时出现）| 时序有规律峰值 | 排查定时任务：快照备份/ILM rollover/定时聚合查询 |
| 突发高（短时间急升）| 时序出现尖刺 | 排查突发流量：查询风暴/大批量写入 |

根据交叉指标缩小根因范围：

| 现象组合 | 根因方向 |
|---------|---------|
| CPU 高 + `SearchLatencyAvg` 同步升高 + 搜索慢日志有记录 | **热点查询**：大聚合或复杂 DSL 消耗 CPU |
| CPU 高 + `IndexLatencyAvg` 升高 + `BulkRejectedCompletedPercent` > 0 | **写入压力**：高并发写入导致 CPU 和线程池同时打满 |
| CPU 高 + `NodeOldGcDifMax` 升高 + GC 日志有 Full GC | **GC 压力**：JVM Old 区堆积，GC stop-the-world 期间 CPU 飙升 |
| CPU 高 + `NodeDiskUtilMax` > 90% + `NodeDiskAwaitMax` 高 | **IO 阻塞**：内核 iowait 拉高 CPU，常见于大量 segment merge/flush |
| CPU 高 + 其他指标均正常 + 有快照/ILM 变更记录 | **后台任务**：快照备份或索引滚动触发大量 IO 和 CPU |
| CPU 高 + `SearchLatencyAvg` 正常 + `IndexLatencyAvg` 正常 | **分片 merge 压力**：后台 merge 线程消耗 CPU，不影响前台延迟 |
| CPU 高 + `CesTasks` 显示 reindex / force_merge 运行中 | **运维任务占用**：确认是否为计划内操作 |

**Resolve（建议）**

| 根因 | 建议操作 |
|------|---------|
| 热点查询 | 查搜索慢日志（`LogType=2`）定位高耗时 DSL；避免 `wildcard`/`script_score`/深层 `aggs` 嵌套；考虑对热点索引增加副本分散查询压力 |
| 写入压力 | 降低写入并发；增大 bulk batch size 减少请求次数；评估是否需要扩容数据节点 |
| GC 压力 | 检查 `fielddata` 使用；对 text 字段禁用 fielddata；考虑扩容至更高内存规格 |
| IO 阻塞 | 排查是否有大量 `force_merge`；将 merge 调度到业务低峰期；考虑升级至 SSD 磁盘类型 |
| 后台任务（快照/ILM）| 将快照时间调整到业务低谷（如凌晨）；检查 ILM rollover 频率是否过高 |
| 分片 merge | 适当降低 `index.merge.scheduler.max_thread_count`；减少分片数或合并小分片 |

---

## 场景 C：写入拒绝排查

**Gather（收集）**

```
# Step 1: 确认写入拒绝趋势和写线程队列
GetMonitorData(..., MetricName="BulkRejectedCompletedPercent", ...)
GetMonitorData(..., MetricName="WriteQueueMax", ...)
GetMonitorData(..., MetricName="WriteRejectedDifMax", ...)

# Step 2: 交叉验证根因方向
GetMonitorData(..., MetricName="JvmMemUsageMax", ...)
GetMonitorData(..., MetricName="DiskUsageMax", ...)
GetMonitorData(..., MetricName="CpuUsageMax", ...)
GetMonitorData(..., MetricName="IsReadOnly", ...)
GetMonitorData(..., MetricName="NodeParentBreakerDifMax", ...)

# Step 3: 查日志
DescribeInstanceLogs(..., LogType=4)   # GC 日志（JVM 堆压力方向）
DescribeInstanceLogs(..., LogType=1)   # 主日志，找 CircuitBreaking

# Step 4: 深度诊断
CesGetNode(...)          # 节点负载是否不均衡
CesGetAllocation(...)    # 各节点真实磁盘水位
CesGetClusterSettings(...) # 确认只读锁是否生效
CesGetIndexInfo(..., Index="my_index", Type="cat_segments")  # 写入慢时看段数是否过多/未 merge
```

**Diagnose（判断）**

注意区分"写入排队"和"写入被拒" —— `WriteQueueMax` 积压是拒绝的前驱信号，应更早介入：

| 现象组合 | 根因方向 |
|---------|---------|
| `WriteQueueMax` 积压（> 10）+ `BulkRejected` 刚开始出现 | **写线程池趋近打满**：写入量超过处理速度，需立即降并发 |
| `BulkRejected` 高 + `JvmMemUsageMax` > 85% + Full GC 频繁 | **JVM 堆压力**：GC stop-the-world 期间写入线程池积压，触发拒绝 |
| `BulkRejected` 高 + `DiskUsageMax` > 85% | **磁盘 watermark**：high watermark 触发分片迁移，写入被阻断 |
| `BulkRejected` 高 + `IsReadOnly=1` | **磁盘 flood_stage**：已触发只读锁，所有写入直接拒绝 |
| `BulkRejected` 高 + `CpuUsageMax` > 80% + 其他指标正常 | **写入量超出处理能力**：节点 CPU 打满，需要扩容或降低写入速率 |
| `BulkRejected` 高 + `NodeParentBreakerDifMax` > 0 | **内存熔断**：写入触发熔断保护，查 CircuitBreaking 日志确认 |
| `WriteRejectedDifMax` 高 + 单节点 CPU/JVM 异常 | **节点不均衡**：部分节点过载，分片分布不均导致热点节点写入堆积 |

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| 写线程池积压（预警阶段）| 立即降低写入并发；增大 bulk batch size 减少请求频次 |
| JVM 堆压力 | 检查 `fielddata` 占用；减少 `_source` 字段大小；扩容节点内存 |
| 磁盘 watermark | **优先扩容磁盘**使使用率降至 85% 以下（推荐 ≤70%）；配置 ILM 避免反复触发 |
| 只读锁（flood_stage）| 扩容磁盘后执行 `PUT /_all/_settings {"index.blocks.read_only_allow_delete": null}` |
| 写入量超限 | 增加数据节点；优化 bulk 批次大小（建议单批 5-15MB）|
| 内存熔断 | 减少大聚合并发；检查是否有写入 + 大查询同时进行 |
| 节点热点 | 用 `CesGetShards` 检查分片分布是否均衡；对写入压力大的索引调整 routing 策略 |

---

## 场景 D：定时巡检 + 低分集群自动深度诊断

> 适用于定时任务场景：每小时巡检，对低分集群自动深入分析

**Step 1: 拉取全量集群**

```
DescribeInstances(Region="ap-guangzhou", Limit=100, Offset=0)
# TotalCount > 100 时继续翻页
```

- 跳过 `Status != 1` 的集群（标记 `N/A`，原因「集群状态异常」）
- 返回体可能很大触发落盘，用 Python 解析提取 `InstanceId`/`InstanceName`/`Status`/`HealthStatus`

**Step 2: 批量取 CORE 指标**

```
# 🚀 按指标维度循环：8 个 CORE 指标 = 8 次调用，覆盖全部集群
GetMonitorData(Region="ap-guangzhou",
               InstanceIds=["es-aaa","es-bbb","es-ccc", ...],   # 全部集群
               MetricName="CpuUsageMax", Period=300)
# 重复：JvmMemUsageMax / DiskUsageMax / IndexLatencyAvg / SearchLatencyAvg
#       BulkRejectedCompletedPercent / Status / NodeOldGcDifMax
```

通过 `DataPoints[].Dimensions[].Value` 把时序数据对应回各集群，**不要按下标假定顺序**。

**Step 3: 逐集群打分**

严格按 [scoring-rules.md](scoring-rules.md) 执行：哨兵值清洗 → 健康色三路融合 → 一票否决 → 扣分项。按分数**升序**输出 Dashboard，低于阈值标记 ⚡。

**Step 4: 对低分集群深度诊断**

```
# 常规调用：真实健康色
CesClusterHealth(Region=..., InstanceId="es-abc123")

# 按 issues 方向查日志
DescribeInstanceLogs(..., LogType=4)   # issues 含 JVM/GC → GC 日志
DescribeInstanceLogs(..., LogType=2)   # issues 含查询延迟 → 搜索慢日志
DescribeInstanceLogs(..., LogType=3)   # issues 含写入延迟 → 索引慢日志
DescribeInstanceLogs(..., LogType=1)   # 兜底：主日志 ERROR

# 按症状选数据面 tool（见 SKILL.md 症状路由表）
CesClusterAllocationExplain(...)# Red/Yellow
CesGetAllocation(...)             # 磁盘告警
CesClusterPendingTasks(...)       # Master 过载
CesTasks(...)                     # CPU 高
```

**Step 5: 输出分析报告**

| 集群 | 评分 | 主要问题 | 触发的 EXTENDED 指标 | 建议操作 |
|------|------|---------|-------------------|----------|
| es-abc123 | 45/100 (D) | JVM 92% + Full GC 频繁 | `JvmOldMemUsageMax` 高、`NodeParentBreakerDifMax` > 0 | 扩容节点内存，禁用 fielddata |
| es-def456 | 65/100 (C) | CPU 78% + 慢查询 | `NodeDiskUtilMax` 高 | 优化 DSL，排查 IO 阻塞 |

---

## 场景 E：查询慢排查

**触发条件**：`SearchLatencyAvg` 持续高（> 200ms）、用户反馈查询超时

**Gather（收集）**

```
GetMonitorData(..., MetricName="SearchLatencyAvg", StartTime="<最近6小时>", ...)
GetMonitorData(..., MetricName="SearchQueueMax", ...)
GetMonitorData(..., MetricName="SearchRejectedCompletedPercent", ...)
GetMonitorData(..., MetricName="CpuUsageMax", ...)

DescribeInstanceLogs(..., LogType=2)   # 搜索慢日志，定位具体慢查询 DSL
CesTasks(...)                          # 正在执行的大查询
CesGetIndexInfo(..., Index="my_index", Type="settings")  # 确认 index.search.slowlog.threshold 实际阈值，判断慢日志是否漏采
```

**Diagnose（判断）**

| 现象 | 可能原因 |
|------|---------|
| 查询延迟高 + `SearchQueueMax` 积压（> 10）| 查询线程池打满，请求排队 |
| 查询延迟高 + `SearchRejectedCompletedPercent` > 0 | 查询被直接拒绝，线程池已满 |
| 查询延迟高 + CPU 同步高 | 热点查询消耗大量 CPU，查慢日志定位 DSL |
| 查询延迟高 + CPU 正常 | 可能是单个大查询或深度分页（`from/size` 过大）|
| 查询延迟周期性升高 | 定时任务触发大聚合，查慢日志确认时间规律 |

**慢日志关键字段**：`took_millis`（耗时）、`search_type`（查询类型）、`source`（DSL 内容）
→ 详细字段解读见 [slow-log-guide.md](slow-log-guide.md)

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| 线程池打满 | 降低查询并发；检查是否有异常重试风暴 |
| 热点查询 DSL | 优化查询：避免 `wildcard`/`script`，减少 `aggs` 嵌套层级 |
| 深度分页 | 改用 `search_after` 替代 `from/size` |
| 大聚合 | 启用 `request_cache`；考虑预计算或降低聚合精度 |
| 分片热点 | 用 `CesGetShards` 检查数据分布是否均衡，考虑重新 routing 或增加副本 |

---

## 场景 F：磁盘告警 / IO 打满

**触发条件**：`DiskUsageMax` 超阈值（> 65%）、写入变慢、集群进入只读

**Gather（收集）**

```
GetMonitorData(..., MetricName="DiskUsageMax", StartTime="<最近24小时>", ...)  # 判断增长速度
GetMonitorData(..., MetricName="NodeDiskUtilMax", ...)# IO 是否打满
GetMonitorData(..., MetricName="NodeDiskAwaitMax", ...)
GetMonitorData(..., MetricName="IsReadOnly", ...)         # 是否已触发只读锁

# 🔑 数据面核实各节点真实水位（集群聚合值会掩盖单节点热点）
CesGetAllocation(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
CesGetClusterSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")  # 确认只读锁
CesListIndices(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")         # 列出索引/别名/数据流
CesGetIndexInfo(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                Index="*", Type="stats")   # 索引级 docs.count/store.size，定位可清理的大索引
```

> 💡 `CesGetAllocation` 在此场景价值最高：`DiskUsageMax` 是集群聚合值，可能掩盖「3 节点中 1 个 95%、其余 40%」的单节点热点。同时它不受探针失联影响，是磁盘打满时的权威判据。
>
> 🔍 找大索引：`CesListIndices`（`_resolve/index`）**只返回名称/属性，不含存储量**，因此需用 `CesGetIndexInfo`(`Type=stats`) 看每个索引的 `store.size` / `docs.count`，或 `CesGetShards` 看分片级 `store`，才能定位「哪个索引最占盘」。

**Diagnose（判断）**

| 现象 | 可能原因 |
|------|---------|
| `DiskUsageMax` > 85% + `IsReadOnly = 1` | 磁盘满触发 watermark，ES 自动锁定索引只读 |
| `NodeDiskUtilMax` > 95% + 写入延迟高 | 磁盘 IO 打满，写入被阻塞 |
| `NodeDiskAwaitMax` > 100ms | 磁盘 IO 等待过高，可能是机械盘或大量 merge/flush |
| 磁盘使用率快速增长 | 索引数据量激增，或未配置 ILM/rollover 策略 |
| `DiskUsageMax` > 75% + `BulkRejectedCompletedPercent` > 0 | 接近 high watermark（默认 85%），部分分片已停止分配 |
| `CesGetAllocation` 显示单节点 `disk.percent` 远高于其他 | **分片分布不均**导致局部水位高 |
| 监控指标全为 `-2` 但 `CesGetAllocation` 显示 95%+ | **探针已失联，磁盘确实打满** —— 等价于一票否决 1b |

**腾讯云 ES 默认 watermark 阈值**：
- `low`（85%）：停止向该节点分配新分片
- `high`（90%）：尝试将分片迁移到其他节点
- `flood_stage`（95%）：索引强制设为只读

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| 磁盘使用率高 | **首选扩容磁盘至 ≤70%**（在线扩容，业务无中断）；配置 ILM 自动删除策略 |
| 已触发只读锁 | 扩容磁盘后手动解除：`PUT /_all/_settings {"index.blocks.read_only_allow_delete": null}` |
| IO 打满 | 排查是否有大量 merge；考虑 `force_merge` 调度到业务低峰期；升级磁盘类型 |
| 磁盘增长过快 | 开启索引生命周期管理（ILM）；规划扩容 |
| 分片分布不均 | 检查索引分片数与节点数是否匹配；必要时调整分片策略 |

> ⚠️ **为什么扩容优于清理**：扩容不动业务数据零风险且可持续；清理是一次性缓解且有数据丢失风险。详见 [scoring-rules.md](scoring-rules.md#2d-磁盘95-已被1b-否决此处处理-95-区间)。

---

## 场景 G：JVM OOM / GC 频繁

**触发条件**：`JvmMemUsageMax` 持续高（> 75%）、GC 日志频繁报警、节点响应变慢

**Gather（收集）**

```
GetMonitorData(..., MetricName="JvmMemUsageMax", StartTime="<最近6小时>", ...)
GetMonitorData(..., MetricName="JvmOldMemUsageMax", ...)   # 重点看 Old 区
GetMonitorData(..., MetricName="NodeOldGcDifMax", ...)
GetMonitorData(..., MetricName="NodeParentBreakerDifMax", ...)  # 熔断次数

DescribeInstanceLogs(..., LogType=4)   # 🔴 GC 日志是 LogType=4
DescribeInstanceLogs(..., LogType=1)   # 主日志，找 OutOfMemory / CircuitBreaking

CesGetNode(...)   # 各节点堆内存占用
CesGetNodesStats(..., Module="jvm")   # 节点级 JVM/GC 详细统计（务必带 Module）
CesGetIndexInfo(..., Index="my_index", Type="fielddata")   # 精确到字段的 fielddata 占用，定位内存膨胀字段
```

**Diagnose（判断）**

| 现象 | 可能原因 |
|------|---------|
| `JvmOldMemUsageMax` > 85% + Full GC 频繁 | Old 区堆积无法回收，典型大对象或内存泄漏 |
| `NodeParentBreakerDifMax` > 0 + `CircuitBreaking` 日志 | 内存熔断触发，查询/写入被主动拒绝以保护节点 |
| Full GC 后 Old 区使用率未下降 | 存在内存泄漏，或 `fielddata` / `query cache` 占用过高 |
| GC 频繁 + CPU 同步升高 | GC stop-the-world 导致节点短暂不可用，影响查询延迟 |
| OOM 后节点重启 | 堆内存严重不足，需立即扩容 |

**⚠️ GC 日志注意**：GC 日志无 `level` 字段，找 `Full GC` / `allocation failure` 关键字，不要按 `level:ERROR` 的思路匹配。**LogType 用 4**。

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| Old 区堆积 | 用 `CesGetIndexInfo`(`Type=fielddata`) 定位占用最高的字段；对该 `text` 字段禁用 fielddata（改用 `keyword`）|
| 熔断频繁 | 减少大聚合查询；调整 `indices.breaker.total.limit` 前先排查根因 |
| 内存不足 | 扩容节点至更高内存规格；JVM 堆大小不超过节点内存的 50% |
| Full GC 后不恢复 | 用 `CesGetNode` 确认各节点堆内存实际占用；仍未恢复需扩容节点或联系腾讯云售后 |

---

## 场景 H：节点重启 / 异常变更排查

**触发条件**：集群状态突变（Yellow/Red）、用户反馈集群抖动、怀疑有变更操作

**Gather（收集）**

```
# Step 1: 先查变更记录，确认是否有操作触发（必须传时间窗口！）
DescribeInstanceOperations(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                           StartTime="<最近24小时起始>", EndTime="<当前时间>")

# Step 2: 当前集群状态
CesClusterHealth(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
DescribeInstances(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"])

# Step 3: 对齐时间线——变更时间点前后的监控
GetMonitorData(..., MetricName="Status", StartTime="<最近24小时>", ...)
GetMonitorData(..., MetricName="NodeNum", StartTime="<最近24小时>", ...)

# Step 4: 主日志 + 节点状态核对
DescribeInstanceLogs(..., LogType=1)
CesGetNode(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
CesGetIndexInfo(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                Index="*", Type="recovery")   # 核对各索引分片恢复进度，确认是否全部恢复
```

**Diagnose（判断）**

| 现象 | 可能原因 |
|------|---------|
| 变更记录有「节点重启」+ 集群变 Yellow | 滚动重启期间副本暂时未分配，属正常现象 |
| 变更记录有「扩缩容」+ 集群变 Yellow/Red | 扩缩容过程中分片迁移，通常自动恢复 |
| `NodeNum` 监控出现下降 + 无变更记录 | 节点异常宕机，非计划内重启 |
| 变更记录有失败操作（`Progress=0`）+ 集群状态异常 | 变更中途失败，需确认操作是否回滚 |
| 集群抖动时间与变更时间吻合 | 变更引发，确认变更类型和影响范围 |
| `CesGetNode` 返回节点数 < `DescribeInstances.NodeNum` | 有节点尚未恢复入集群 |

**时间线对齐方法**：
1. 从 `DescribeInstanceOperations` 获取变更的 `StartTime`
2. 用 `GetMonitorData` 的 `StartTime`/`EndTime` 查该时间点前后 30 分钟的监控
3. 确认 `Status`、`NodeNum`、ERROR 日志是否在同一时间点出现异常
4. 用 `CesGetNode` 核对当前节点是否已全部恢复

**Resolve（建议）**

| 原因 | 建议操作 |
|------|---------|
| 计划内滚动重启 | 等待自动恢复（通常 5-15 分钟）；观察 `Status` 是否回 Green |
| 扩缩容分片迁移 | 等待分片迁移完成；用 `CesGetShards` 观察 `relocating` 分片收敛 |
| 节点异常宕机 | 查主日志定位宕机原因（OOM / 硬件故障）；联系腾讯云售后 |
| 变更操作失败 | 查看失败操作 `Detail` 详情；确认集群是否需要人工干预恢复 |
