# 集群健康诊断分析框架

> **何时使用本文件**：在步骤 3（告警事件分级判断）、步骤 4（监控指标阈值判断）、步骤 7（综合分析与根因定位）时参考。
> **何时不使用**：工具调用参数请参考各工具的 reference 文档；输出报告格式请参考 `report-template.md`。

---

## 目录

- [§1 告警事件分级](#1-告警事件分级)
- [§2 监控指标阈值](#2-监控指标阈值)
- [§3 健康评分规则](#3-健康评分规则)
- [§4 常见故障模式与根因分析](#4-常见故障模式与根因分析)

---

## §1 告警事件分级

| EventCode | 含义 | 严重程度 | Agent 优先级 |
|-----------|------|---------|-------------|
| `DiskHigh` | 磁盘使用率过高 | 🔴 高 | 立即分析，防数据丢失 |
| `AbnormalInstanceDisk` | 实例硬盘异常 | 🔴 高 | 立即分析，可能影响数据完整性 |
| `InstanceDiskAlter` | 实例硬盘预警 | 🟡 中 | 纳入诊断，给出预防建议 |
| `InstanceRisk` | 实例运行隐患 | 🟡 中 | 纳入诊断，分析具体风险 |
| `EmptyPassword` | 空密码安全隐患 | 🟡 中 | 纳入诊断，建议设置密码 |
| `InstanceMaintenance` | 实例维护升级 | 🟢 低 | 告知用户，通常无需处理 |

### 事件状态说明

| Status 值 | 含义 | Agent 行为 |
|-----------|------|-----------|
| 1 | 待处理 | 重点关注，纳入诊断 |
| 2 | 已处理 | 仅作为历史参考 |
| 3 | 处理中 | 关注进度，告知用户 |
| 4 | 已忽略 | 跳过 |

---

## §2 监控指标阈值

> **接口说明**：监控指标通过 `MonitorDescribeDashboardMetricData` 接口查询（Monitor 产品），MetricName 使用驼峰格式。
> **参数规则**：
> - 集群聚合指标：传 `NodeCount` 参数（= CK 节点数），通过 `TCHouseCDescribeInstanceNodes` 获取
> - 节点级指标：传 `NodeIps` 参数（节点 IP 逗号分隔），通过 `TCHouseCDescribeInstanceNodes` 获取对应类型节点 IP

### 集群聚合指标（传 NodeCount = CK 节点数）

| 指标类别 | MetricName（驼峰） | 含义 | 正常范围 | 警告阈值 | 严重阈值 |
|---------|-------------------|------|---------|---------|----------|
| CPU | SumCpuUsage | CPU使用率（集群聚合） | < 60% | > 80% 持续 5 分钟 | > 95% 持续 5 分钟 |
| 内存 | SumMemUsage | 内存使用率（集群聚合） | < 70% | > 85% | > 95% |
| 磁盘 | SumDiskUsage | 数据盘使用率（集群聚合） | < 70% | > 85% | > 90% |
| 查询 | SumQuery | 总查询数 | 基线水平 | 突增 3 倍以上 | 突增 5 倍以上 |
| 写入失败 | SumFailedinsertquery | 插入失败数 | 0 | > 0 持续出现 | 持续增长 |
| 查询失败 | SumFailedselectquery | 查询失败数 | 0 | > 0 持续出现 | 持续增长 |
| CK CPU | CkCpuUsage | CK节点CPU使用率 | < 60% | > 80% | > 95% |
| CK 内存 | CkMemUsage | CK节点内存使用率 | < 70% | > 85% | > 95% |
| CK 磁盘 | CkDiskUsage | CK节点磁盘使用率 | < 70% | > 85% | > 90% |

### CK 节点资源指标（传 NodeIps = CK 节点 IP 列表）

| 指标类别 | MetricName（驼峰） | 含义 | 正常范围 | 警告阈值 | 严重阈值 |
|---------|-------------------|------|---------|---------|----------|
| 存活 | CkUp | 节点存活 | 1 | — | 0（失活） |
| CPU | CpuUsage | CPU峰值使用率 | < 60% | > 80% 持续 5 分钟 | > 95% 持续 5 分钟 |
| CPU 均值 | CpuUsageAvg | CPU平均使用率 | < 50% | > 70% | > 90% |
| CPU 负载比 | CpuLoadRate | CPU负载比率 | < 100% | > 150% | > 200% |
| 负载 | NodeLoad1 | 1分钟负载 | < CPU核数 | > CPU核数×1.5 | > CPU核数×2 |
| 内存 | MemUsage | 内存使用率 | < 70% | > 85% | > 95% |
| 磁盘 | DiskUsage | 数据盘使用率 | < 70% | > 85% | > 90% |
| 磁盘 IO | NodeDiskIoUtil | 硬盘IO使用率 | < 60% | > 80% | > 95% |
| IO 等待 | NodeDiskIoWait | 硬盘IO等待时间 | < 50ms | > 100ms | > 500ms |
| IO 队列 | NodeIoQueueSize | IO队列长度 | < 10 | > 32 | > 64 |
| 读 IOPS | NodeDiskReadIops | 硬盘读IOPS | 视磁盘类型 | 接近规格上限 | 达到规格上限 |
| 写 IOPS | NodeDiskWriteIops | 硬盘写IOPS | 视磁盘类型 | 接近规格上限 | 达到规格上限 |
| 网络入 | NodeNetworkReceiveBytesTotal | 节点接收流量 | 基线水平 | 突增 3 倍 | 突增 5 倍 |
| 网络出 | NodeNetworkTransmitBytesTotal | 节点流出流量 | 基线水平 | 突增 3 倍 | 突增 5 倍 |

### CK 服务指标（传 NodeIps = CK 节点 IP 列表）

| 指标类别 | MetricName（驼峰） | 含义 | 正常范围 | 警告阈值 | 严重阈值 |
|---------|-------------------|------|---------|---------|----------|
| 连接数 | Httpconnection / Tcpconnection | HTTP/TCP连接数 | < 50% max | > 80% max_connections | > 95% max_connections |
| 查询线程 | Querythread | 查询线程数 | < 50% max | > 80% max_concurrent_queries | > 95% max_concurrent_queries |
| 合并数 | Merge | 合并数 | < background_pool_size | 接近 pool_size | 达到 pool_size |
| 合并耗时 | Mergestimemilliseconds | Merge消耗时间 | < 1000ms | > 5000ms | > 30000ms |
| 副本只读 | ReadonlyReplica | readonlyReplica数量 | 0 | > 0 | 持续 > 0 |
| Mutation | PartMutation | mutation数量 | < 10 | > 50 | > 100 |
| 分布式写入 | Distributedfilestoinsert | 分布式表等待写入文件数 | < 100 | > 500 | > 1000 |
| ZK 请求 | Zookeeperrequest | ZK请求数 | 基线水平 | 突增 3 倍 | 突增 5 倍 |
| 上下文锁 | Contextlockwait | 上下文锁等待 | 0 | > 0 持续出现 | 持续增长 |

### Keeper/ZK 节点指标（传 NodeIps = Keeper/ZK 节点 IP 列表，NodeRole=COMMON）

> ⚠️ **重要**：Keeper/ZK 节点也有通用系统指标（`CpuUsage`、`MemUsage`、`DiskUsage` 等），这些指标名称与 CK 节点相同，但采集的是 Keeper/ZK 节点的资源。查询时必须使用 **Keeper/ZK 节点的 IP**（通过 `TCHouseCDescribeInstanceNodes` 的 NodeRole=COMMON 获取），而非 CK 节点 IP。

**Keeper/ZK 专有指标**：

| 指标类别 | MetricName（驼峰） | 含义 | 正常范围 | 警告阈值 | 严重阈值 |
|---------|-------------------|------|---------|---------|----------|
| 存活 | KeeperUp / ZkUp | 进程存活 | 1 | — | 0（失活） |
| Leader | KeeperIsLeader / ZkIsLeader | 是否为Leader | 集群中有且仅有1个 | — | 0个或多个Leader |
| 事务版本 | KeeperZxid / Zxid | 事务版本 | 各节点一致 | 节点间差异 > 1000 | 节点间差异 > 10000 |
| Watch | KeeperWatchCount / WatchCount | Watch数量 | < 10000 | > 50000 | > 100000 |
| 队列 | KeeperRequestCommitQueued / RequestCommitQueued | 请求提交队列 | < 10 | > 100 | > 1000 |
| DDL | KeeperActiveDistributedDdl / ActiveDistributedDdl | 运行中分布式DDL | < 5 | > 10 | > 50 |

**Keeper/ZK 节点系统资源指标**（与 CK 节点同名，但采集的是 Keeper/ZK 节点资源，需用 Keeper/ZK 节点 IP 查询）：

| 指标类别 | MetricName（驼峰） | 含义 | 正常范围 | 警告阈值 | 严重阈值 |
|---------|-------------------|------|---------|---------|----------|
| CPU | CpuUsage | CPU使用率 | < 60% | > 80% | > 95% |
| 内存 | MemUsage | 内存使用率 | < 70% | > 85% | > 95% |
| 磁盘 | DiskUsage | 数据盘使用率 | < 70% | > 85% | > 90% |
| 负载 | NodeLoad1 | 1分钟负载 | < CPU核数 | > CPU核数×1.5 | > CPU核数×2 |
| 磁盘 IO | NodeDiskIoUtil | 硬盘IO使用率 | < 60% | > 80% | > 95% |
| IO 等待 | NodeDiskIoWait | 硬盘IO等待时间 | < 50ms | > 100ms | > 500ms |
| 网络入 | NodeNetworkReceiveBytesTotal | 节点接收流量 | 基线水平 | 突增 3 倍 | 突增 5 倍 |
| 网络出 | NodeNetworkTransmitBytesTotal | 节点流出流量 | 基线水平 | 突增 3 倍 | 突增 5 倍 |
### 磁盘类型与 IO 性能预期

| 磁盘类型 | 预期 IOPS | 预期吞吐 | 说明 |
|---------|----------|---------|------|
| CLOUD_SSD | 26000 | 260 MB/s | 标准 SSD |
| CLOUD_PREMIUM | 6000 | 150 MB/s | 高性能云硬盘 |
| CLOUD_HSSD | 100000+ | 350 MB/s | 增强型 SSD |

### MetricName 转换规则

告警配置中的 `metricName` 使用下划线格式（如 `cpu_usage`），调用 `MonitorDescribeDashboardMetricData` 时需转换为驼峰格式（如 `CpuUsage`）。

**转换方法**：去掉下划线 `_`，每个单词首字母大写。例如：
- `node_disk_io_util` → `NodeDiskIoUtil`
- `ck_up` → `CkUp`
- `sum_cpu_usage` → `SumCpuUsage`

---

## §3 健康评分规则

> **原则**：评分必须可追溯，报告里给出的分数必须能对应到下方的扣分项，禁止拍脑袋给分。

### 评分方法：100 分制扣分

起始分 **100 分**，按下列规则逐项扣分，扣完为止（最低 0 分）。所有扣分必须在报告的"扣分明细"表中列出，让用户可以复核。

#### 扣分项 A：节点异常

| 现象 | 扣分 |
|------|------|
| 每个非 `Running` 状态的 DATA 节点 | **-20 分** |
| 每个非 `Running` 状态的 COMMON(ZK/Keeper) 节点 | **-15 分** |
| 每个 `CkUp = 0` / `KeeperUp = 0` / `ZkUp = 0`（存活指标失活） | **-20 分** |
| ZK/Keeper Leader 缺失（0 个 Leader 或多 Leader） | **-15 分** |

#### 扣分项 B：告警事件（仅统计 Status=1 待处理 与 Status=3 处理中）

| 严重程度 | 扣分（每条） | 单项封顶 |
|---------|-------------|----------|
| 🔴 高（`DiskHigh` / `AbnormalInstanceDisk`） | **-15 分** | -45 分 |
| 🟡 中（`InstanceDiskAlter` / `InstanceRisk` / `EmptyPassword`） | **-8 分** | -24 分 |
| 🟢 低（`InstanceMaintenance` 等） | **-2 分** | -6 分 |

> 已处理（Status=2）/已忽略（Status=4）的事件**不扣分**。

#### 扣分项 C：监控指标（按 §2 表格中的阈值判定）

| 指标类别 | 达到"严重阈值" | 达到"警告阈值" | 单类别封顶 |
|---------|:-------------:|:-------------:|:---------:|
| CPU（`SumCpuUsage` / `CpuUsage` / `NodeLoad1`） | **-10 分** | **-5 分** | -15 分 |
| 内存（`SumMemUsage` / `MemUsage`） | **-10 分** | **-5 分** | -15 分 |
| 磁盘容量（`SumDiskUsage` / `DiskUsage`） | **-15 分** | **-8 分** | -23 分 |
| 磁盘 IO（`NodeDiskIoUtil` / `NodeDiskIoWait` / `NodeIoQueueSize`） | **-8 分** | **-4 分** | -12 分 |
| 查询相关（`SumQuery` 突增 / `Querythread` / `SumFailedselectquery`） | **-8 分** | **-4 分** | -12 分 |
| 写入相关（`SumFailedinsertquery` / `Distributedfilestoinsert` / `PartMutation`） | **-8 分** | **-4 分** | -12 分 |
| 连接数（`Httpconnection` / `Tcpconnection`） | **-8 分** | **-4 分** | -12 分 |
| 副本/合并（`ReadonlyReplica` / `Merge` / `Mergestimemilliseconds`） | **-8 分** | **-4 分** | -12 分 |
| ZK/Keeper 专有（`Zxid` 差异 / `WatchCount` / `RequestCommitQueued`） | **-10 分** | **-5 分** | -15 分 |

**同一指标的判定规则**：
- 同一指标在多个节点触发同一档阈值 → 按"节点数"计入，但受"单类别封顶"约束（例如 5 个节点 CPU 都爆到严重阈值，也只扣 15 分）
- 同一指标既触发警告又触发严重 → 按严重阈值扣分，不叠加

### 评分等级映射

| 分数区间 | 等级 |
|---------|------|
| 90 – 100 | 🟢 **健康** |
| 70 – 89  | 🟡 **警告** |
| 0  – 69  | 🔴 **异常** |

> 若最终得分与"最严重单项"表现不一致（例如所有扣分累加后仍 ≥ 90 分，但存在节点宕机），**强制降级**为 🔴 异常。规则：出现任一节点非 Running、`CkUp=0`、🔴 高严重度未处理告警时，评分等级最高为 🔴，与总分独立。

### 数据不充分时的评分调整

当部分诊断数据不可用（如监控指标拉取失败）时，评分需要降级处理：

| 缺失数据 | 评分调整策略 |
|---------|------------|
| 监控指标完全不可用 | 不给出具体分数，仅基于节点状态和事件数据给出定性等级（🟢/🟡/🔴），并在报告中注明"因监控数据不可用，评分仅基于节点状态和告警事件" |
| 部分节点指标缺失 | 可给出评分，但标注"部分节点数据缺失（-N 分未计入），评分可能偏乐观" |
| 事件历史不可用 | 可给出评分，但标注"告警事件数据不可用，可能遗漏历史问题" |
| 仅节点状态可用 | 仅给出节点存活性评估，不给出综合健康评分 |

> **原则**：宁可标注"数据不充分，无法给出准确评分"，也不要基于不完整数据给出过于乐观的评分。

---

## §4 常见故障模式与根因分析

### 4.1 磁盘空间不足

**信号**：`DiskHigh` 告警、disk_usage_percent > 90%

**排查路径**：
1. 确认哪些节点磁盘使用率高
2. 检查是否有大量 parts 未合并（parts_count 异常高）
3. 检查 TTL 策略是否生效
4. 检查是否有异常大量写入

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | 清理过期分区：`ALTER TABLE xxx DROP PARTITION 'yyyymm'` | 立即释放空间 | 数据不可恢复，需确认分区确实过期 |
| P0 | 强制触发 TTL 清理：`OPTIMIZE TABLE xxx FINAL` | 清理 TTL 过期数据 | 消耗 IO 和 CPU，建议低峰期 |
| P1 | 检查并修复 TTL 策略 | 防止再次堆积 | 无 |
| P2 | 扩容磁盘 | 根本解决空间不足 | 需要控制台操作 |

### 4.2 CPU 持续高负载

**信号**：cpu_usage_percent > 80% 持续 5 分钟以上

**排查路径**：
1. 检查 running_queries 是否异常高
2. 检查是否有复杂查询占用大量 CPU
3. 检查后台 merge 是否过于频繁
4. 检查 max_threads 配置是否过高

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | Kill 异常长时间运行的查询 | CPU 立即下降 | 查询中断，需通知业务方 |
| P1 | 调整 `max_threads` 降低单查询并行度 | 减少单查询 CPU 占用 | 单查询变慢 |
| P1 | 优化高频慢查询（转到慢 SQL 诊断 Skill） | 根本降低 CPU 消耗 | 需要 SQL 改写 |
| P2 | 错峰调度批量任务 | 避免高峰期资源争抢 | 需业务方配合 |

### 4.3 内存使用率过高

**信号**：memory_usage_percent > 85%、OOM Kill 事件

**排查路径**：
1. 检查 memory_tracking 指标
2. 检查是否有大查询占用过多内存
3. 检查 `max_memory_usage` 配置
4. 检查 mark_cache_size 和 uncompressed_cache_size 是否过大

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | Kill 内存占用过大的查询 | 立即释放内存 | 查询中断 |
| P1 | 降低 `max_memory_usage` 限制单查询内存 | 防止单查询耗尽内存 | 大查询可能报错 |
| P1 | 调整缓存大小配置 | 释放缓存占用的内存 | 查询缓存命中率下降 |
| P2 | 考虑扩容内存 | 根本解决内存不足 | 需要控制台操作 |

### 4.4 副本延迟过高

**信号**：replica_delay_seconds > 300 秒

**排查路径**：
1. 检查 ZooKeeper 连接状态
2. 检查网络延迟
3. 检查是否有大量写入导致副本同步跟不上
4. 检查副本节点资源是否充足

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | 检查 ZooKeeper 健康状态 | 定位 ZK 问题 | 无 |
| P1 | 检查网络连通性 | 排除网络因素 | 无 |
| P1 | 降低写入速率或错峰写入 | 减轻副本同步压力 | 需业务方配合 |
| P2 | 增加副本节点资源 | 提升同步能力 | 需要控制台操作 |

### 4.5 连接数/查询数耗尽

**信号**：current_connections 接近 max_connections、running_queries 接近 max_concurrent_queries

**排查路径**：
1. 检查是否有连接泄漏（大量空闲连接）
2. 检查是否有慢查询堆积
3. 检查客户端连接池配置

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | Kill 空闲连接 | 立即释放连接数 | 可能影响正在等待的客户端 |
| P1 | 调高 `max_connections` / `max_concurrent_queries` | 提高上限 | 可能增加资源压力 |
| P1 | 优化慢查询减少查询堆积 | 根本减少并发占用 | 需要 SQL 改写 |
| P2 | 优化客户端连接池配置 | 减少无效连接 | 需业务方配合 |

### 4.6 Parts 过多（MergeTree 合并压力）

**信号**：parts_count 接近 parts_to_delay_insert、写入变慢或被拒绝

**排查路径**：
1. 检查写入频率是否过高（高频小批量写入）
2. 检查后台 merge 线程是否充足
3. 检查磁盘 IO 是否成为 merge 瓶颈

**修复建议**（按优先级）：
| 优先级 | 操作 | 预期效果 | 风险 |
|--------|------|---------|------|
| P0 | 手动触发合并：`OPTIMIZE TABLE xxx` | 加速 parts 合并 | 消耗 IO 和 CPU |
| P1 | 合并小批量写入为大批量（建议单批 ≥ 10000 行） | 减少 parts 产生速度 | 需业务方改造 |
| P1 | 调高 `background_pool_size` 增加合并线程 | 加速后台合并 | 增加 CPU 消耗 |
| P2 | 调整 `parts_to_delay_insert` / `parts_to_throw_insert` 阈值 | 提高容忍度 | 可能导致查询变慢 |
