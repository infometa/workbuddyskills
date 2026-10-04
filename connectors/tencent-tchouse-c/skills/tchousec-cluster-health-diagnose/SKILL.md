---
name: 腾讯云TCHouse-C 集群健康诊断与故障排查
description: >
  TCHouse-C（ClickHouse）集群健康诊断与故障排查 Skill。AI 拉取集群监控指标（CPU/内存/磁盘/IOPS/连接数/副本延迟）、告警历史及节点状态，输出集群健康评分，定位异常根因，并给出修复建议（参数调整/分区清理/节点重启等）。
  触发词：集群健康、健康检查、巡检、节点故障、磁盘告警、CPU告警、内存告警、OOM、磁盘满、磁盘空间不足、节点异常、副本延迟、查询堆积、连接数满、集群状态、cluster health、node failure、disk alert、replica lag、集群诊断、故障排查、监控异常、告警处理、节点状态、资源告警、性能瓶颈、IO高、网络异常、ZooKeeper异常、parts过多、merge压力、cdwch、TCHouse-C、ClickHouse集群。
  本 Skill 包含 3 个子能力：①集群全面健康巡检 ②告警事件排查与根因定位 ③节点故障诊断与修复建议。
  何时不触发：慢 SQL 诊断与自动调优（单条 SQL 性能分析）、集群选型与架构推荐、智能建表与数据建模、NL2SQL、AI Function 智能编排、集群扩缩容操作、权限管理、数据导入导出等非集群健康/故障相关问题不走本 Skill。
allowed-tools:
  - TCHouseCDescribeInstance
  - TCHouseCDescribeInstanceNodes
  - TCHouseCDescribeEventTasks
  - TCHouseCDescribeClusterConfigs
  - TCHouseCDescribeInstanceShards
  - MonitorDescribeDashboardMetricData
  - TCHouseCDescribeRunningQuery
  - ask_user # WorkBuddy 中为 AskUserQuestion
---

# 集群健康诊断与故障排查

## 概述

本 Skill 提供 TCHouse-C（ClickHouse）集群的健康诊断与故障排查能力，包含三个子能力：

1. **集群全面健康巡检**：拉取监控指标、节点状态、告警事件，输出健康评分和全面诊断报告
2. **告警事件排查与根因定位**：针对具体告警事件（磁盘/CPU/内存/副本延迟），定位根因并给出修复建议
3. **节点故障诊断与修复建议**：针对节点异常（宕机/不可达/资源耗尽），分析原因并给出恢复方案

## 依赖与运行环境

本 Skill 的所有调用通过 MCP Tool 完成（云 API 类工具由平台封装为 MCP Tool，Agent 直接调用工具名即可）。

**依赖工具清单**：

| #   | Tool 名称                          | 能力定位                                                 | 参考文档                                                           |
| --- | ---------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------ |
| 1   | TCHouseCDescribeInstance           | 集群基本信息获取（含状态与流程进度 `InstanceStateInfo`） | [参考](references/tchousec-describe-instance.md)             |
| 2   | TCHouseCDescribeInstanceNodes      | 节点列表与状态                                           | [参考](references/tchousec-describe-instance-nodes.md)       |
| 3   | TCHouseCDescribeEventTasks         | 告警/事件历史查询                                        | [参考](references/tchousec-describe-event-tasks.md)          |
| 4   | TCHouseCDescribeClusterConfigs     | 集群配置参数获取                                         | [参考](references/tchousec-describe-cluster-configs.md)      |
| 5   | TCHouseCDescribeInstanceShards     | 分片拓扑信息                                             | [参考](references/tchousec-describe-instance-shards.md)      |
| 6   | MonitorDescribeDashboardMetricData | 集群监控指标查询（Monitor 产品）                         | [参考](references/monitor-describe-dashboard-metric-data.md) |
| 7   | TCHouseCDescribeRunningQuery       | 当前运行中的查询                                         | [参考](references/tchousec-describe-running-query.md)        |
| 8   | ask_user                           | 向用户询问确认信息（WorkBuddy 中为 AskUserQuestion）     | —                                                                  |

## 凭证 / 环境变量

- `instance_id`：从会话 context 的 X-Context header 自动注入
- `region_id`：从会话 context 的 X-Context header 自动注入（可能是 `RegionId` 数字，也可能是 `Region` 字符串，也可能是中文地域名）
- 若以上参数缺失，通过 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）询问用户

> ⚠️ **地域参数强制规则**：**任何工具调用前**都必须先按 [地域映射表](references/region-mapping.md) 把上下文中的地域信息补齐为 **`Region`（字符串）+ `RegionId`（数字）** 两种形式，禁止凭记忆填写。不同工具对参数形式的要求见 [工具传参形式速查](references/region-mapping.md#工具传参形式速查)：
>
> - `TCHouseCXxx` 系工具：**只传 `Region` 字符串**
> - `MonitorDescribeDashboardMetricData`：**同时传 `Region` 字符串 和 `RegionId` 数字**

> 💡 **多平台兼容说明**：本文档中所有提到的 `ask_user` 工具，在 WorkBuddy 平台中对应为 `AskUserQuestion`。后文不再重复标注。

## 核心工作流

### 步骤 0：参数确认

**必需参数**：

- `instance_id`（集群 ID）
- `region_id`（地域）

**可选参数**（从用户问题中提取，缺失时使用默认值，不自行假设）：

- 时间范围：未指定 → 默认最近 24 小时
- 具体告警事件或节点 IP：从用户问题中提取

**判断逻辑**：

- ✅ 参数齐全 → **强制**按 [地域映射表](references/region-mapping.md) 把地域补齐为 `Region`（字符串）+ `RegionId`（数字）两种形式（任何输入形式都要过这一步：中文名、英文串、数字 ID 都不例外），补齐后进入步骤 1
- ❌ `instance_id` 或 `region_id` 缺失 → 调用 `ask_user` 询问
- ❌ 地域信息在映射表中匹配不到（或大区模糊，如"华南地区"）→ 调用 `ask_user` 确认后再补齐

### 步骤 1：确认集群信息与状态

调用一次 `TCHouseCDescribeInstance` 同时获取集群基本信息和当前状态。状态与流程进度从 `InstanceInfo.InstanceStateInfo` 子对象读取（含 `InstanceState`/`InstanceStateDesc`/`FlowName`/`FlowProgress`/`FlowMsg`），无需额外调用 `DescribeInstanceState`。

**判断逻辑**：

- ✅ 集群状态 `InstanceInfo.InstanceStateInfo.InstanceState`（或外层 `InstanceInfo.Status`）为 `Serving` → 进入步骤 2
- ❌ 状态为 `Init`/`Modify` → 告知用户集群当前状态，说明可能的影响；若有正在进行的流程（`FlowName` + `FlowProgress`），建议等待完成后再诊断
- ❌ 状态为 `Deleted`/`Deleting` → 告知用户集群已下线，无法执行诊断，建议通过控制台检查或提工单
- ❌ 调用失败（AuthFailure）→ 报告鉴权失败，提示检查权限
- ❌ 调用失败（ResourceNotFound）→ 检查 instance_id 格式（应为 `cdwch-` 前缀），格式错则修正重试，格式对则请用户确认
- ❌ 调用超时/网络错误 → 等 3 秒重试，最多 3 次；仍失败 → 告知用户服务暂时不可用

**记录信息**：ClickHouse 版本号、节点规格和数量、是否为 HA 集群。

### 步骤 2：获取节点状态矩阵

调用 `TCHouseCDescribeInstanceNodes` 获取所有节点详细信息：

- 分别传 `NodeRole=DATA` 和 `NodeRole=COMMON` 获取数据节点和 ZK 节点
- 使用 `ForceAll=true` 获取全量节点

**判断逻辑**：

- ✅ 所有节点状态为 `Running` → 继续步骤 3
- ❌ 存在非 `Running` 状态的节点 → 标记为异常节点，记录 IP 和状态，作为后续重点关注对象
- ❌ 调用失败 → 跳过节点级分析，基于集群级数据（事件、配置）给出有限诊断建议

**记录信息**：节点 IP 列表、规格（Core/Memory/Disk）、磁盘类型（DiskType）。

### 步骤 3：检查告警/事件历史

调用 `TCHouseCDescribeEventTasks` 获取集群的告警和事件历史。

**参数策略**：

- 时间范围：根据用户描述确定，未指定则默认最近 7 天
- 时间格式：`YYYY-MM-DD HH:MM:SS`（如 `2026-06-11 20:00:00`）
- 状态过滤：优先查看待处理（Status=1）和处理中（Status=3）的事件
- 排序：按 `create_time` 降序，最新事件优先

**判断逻辑**：

- ✅ 存在未处理的高严重度事件 → 优先分析该事件，作为诊断重点，进入步骤 4
- ✅ 无告警事件 → 继续全面巡检流程（步骤 4）
- ❌ 调用失败 → 告知用户指定时间范围内事件查询失败，继续基于监控指标进行主动巡检
- ❌ 返回为空 → 告知用户无告警事件，继续基于监控指标巡检

**告警严重度分级**详见 [诊断分析框架](references/diagnosis-framework.md#告警事件分级)。

### 步骤 4：拉取监控指标

调用 `MonitorDescribeDashboardMetricData` 获取集群核心监控指标。

> ⚠️ 该接口属于 Monitor 产品（非 cdwch），MetricName 需使用**驼峰格式**（如 `cpu_usage` → `CpuUsage`）。
> 节点级指标需先通过步骤 2 获取节点 IP 列表，传入 `NodeIps` 参数；集群聚合指标需传入 `NodeCount` 参数。
> 时间格式：**ISO 8601**（如 `2026-06-11T20:00:00+08:00`），与 `TCHouseCDescribeEventTasks` 的 `YYYY-MM-DD HH:MM:SS` 格式不同，注意区分。

**时间范围策略**：

- 用户指定了时间 → 按用户要求
- 用户说"刚才"/"刚刚" → 最近 1 小时
- 用户说"今天" → 当天 0 点到当前
- 未指定 → 默认最近 1 小时（Period=60）

**推荐查询策略**：

> ⚠️ **前置条件**：步骤 2 已通过 `TCHouseCDescribeInstanceNodes` 获取节点列表（CK 节点数和各节点 IP）。
>
> - **集群聚合指标**（Sum/Ck 开头）：传 `NodeCount` 参数（= CK 节点数），不传 `NodeIps`
> - **CK 节点级指标**：传 `NodeIps` 参数（CK 节点 IP，逗号分隔），不传 `NodeCount`
> - **ZK/Keeper 节点指标**：传 `NodeIps` 参数（ZK/Keeper 节点 IP，通过 NodeRole=COMMON 获取，逗号分隔），不传 `NodeCount`

1. **第一步：查集群聚合指标**（传 `NodeCount` = CK 节点数）：
   - `SumCpuUsage`、`SumMemUsage`、`SumDiskUsage`、`SumQuery`、`SumFailedselectquery`
2. **第二步：发现异常后下钻到 CK 节点级**（传 `NodeIps` = CK 节点 IP 列表）：
   - CPU 异常 → 查 `CpuUsage`、`CpuUsageAvg`、`NodeLoad1`
   - 内存异常 → 查 `MemUsage`
   - 磁盘异常 → 查 `DiskUsage`、`NodeDiskIoUtil`、`NodeDiskIoWait`
   - 网络异常 → 查 `NodeNetworkReceiveBytesTotal`、`NodeNetworkTransmitBytesTotal`
3. **第三步：检查 Keeper/ZK 节点健康**（传 `NodeIps` = Keeper/ZK 节点 IP 列表，通过 NodeRole=COMMON 获取）：
   - 存活检查 → 查 `KeeperUp` / `ZkUp`
   - Leader 状态 → 查 `KeeperIsLeader` / `ZkIsLeader`
   - 节点资源 → 查 `CpuUsage`、`MemUsage`、`DiskUsage`（⚠️ 同名指标，但需用 Keeper/ZK 节点 IP 查询，采集的是 Keeper/ZK 节点资源）

**指标分组查询**：按 [诊断分析框架](references/diagnosis-framework.md#监控指标阈值) 中的指标列表和阈值进行判断。

**判断逻辑**：

- ✅ 所有指标正常 → 进入步骤 7（综合分析）
- ❌ 发现 CPU 高或查询堆积 → 进入步骤 5（检查运行查询）
- ❌ 发现配置相关问题（内存不足/并发过高）→ 进入步骤 6（检查配置）
- ❌ 监控数据缺失（采集中断）→ 标注数据缺失时段，基于可用数据做分析，报告中注明
- ❌ 调用失败 → 等 3 秒重试，最多 3 次；仍失败 → 跳过监控分析，基于节点状态和事件数据给出有限诊断

### 步骤 5：检查当前运行查询（条件触发）

**触发条件**（满足任一即触发）：

- 步骤 4 发现 CPU 高或查询堆积
- 步骤 4 调用失败（监控数据不可用时，作为补充信息源）

调用 `TCHouseCDescribeRunningQuery` 查看当前正在执行的查询。

**判断逻辑**：

- ✅ 发现长时间运行的查询（> 60 秒）→ 纳入根因分析
- ✅ 发现大量并发查询导致资源争抢 → 纳入根因分析
- ✅ 无异常 → 继续步骤 7
- ❌ 调用失败 → 跳过此步骤，基于已有数据给出建议

### 步骤 6：检查集群配置（条件触发）

**触发条件**（满足任一即触发）：

- 步骤 4 发现可能与配置相关的问题（内存不足/并发过高）
- 步骤 4 调用失败（监控数据不可用时，配置信息可提供间接诊断线索）

调用 `TCHouseCDescribeClusterConfigs` 获取关键性能配置，重点关注：

- `max_connections` — 最大连接数上限
- `max_concurrent_queries` — 最大并发查询数
- `max_memory_usage` — 单查询内存上限
- `max_thread_pool_size` — 线程池大小
- `merge_tree.parts_to_throw_insert` / `parts_to_delay_insert` — parts 阈值

**判断逻辑**：

- ✅ 成功 → 纳入综合分析
- ❌ 获取失败 → 跳过配置分析，基于已有数据给出建议，报告中注明

### 步骤 6.5：检查分片拓扑（条件触发）

**触发条件**（满足任一即触发）：

- HA 集群或多分片集群，且怀疑副本/分片相关问题
- 步骤 4 调用失败（监控数据不可用时，分片拓扑信息可辅助诊断）

调用 `TCHouseCDescribeInstanceShards` 获取分片信息：确认分片数量和副本配置、ZooKeeper 连接状态、分片间数据均衡情况。

**判断逻辑**：

- ✅ 成功 → 纳入综合分析
- ❌ 获取失败 → 跳过分片分析，基于已有数据给出建议

### 步骤 7：综合分析与生成报告

基于收集到的所有信息，按 [诊断分析框架](references/diagnosis-framework.md#常见故障模式) 进行根因分析，按 [输出报告格式](references/report-template.md) 生成诊断报告。

**报告必须包含**：

1. 集群概况（ID/名称/版本/状态/节点数/HA 模式）
2. 健康评分（🟢/🟡/🔴 + 一句话总结）
3. 节点状态矩阵
4. 告警事件列表（如有）
5. 异常项详情与根因分析
6. 修复建议（按优先级排序：P0 防数据丢失 → P1 性能恢复 → P2 长期优化）

**多异常并发时的优先级排序**：

1. 先解磁盘（防数据丢失）
2. 再处理查询堆积（恢复服务）
3. 再优化 CPU/内存（性能调优）

## 频率控制

| 限制                                    | 阈值          | 说明                                 |
| --------------------------------------- | ------------- | ------------------------------------ |
| 工具总调用频率                          | ≤ 15 次/分钟  | 避免触发平台限流                     |
| MonitorDescribeDashboardMetricData 调用 | ≤ 5 次/轮诊断 | 每次可批量查询多个指标（Query 数组） |
| TCHouseCDescribeEventTasks 翻页         | ≤ 3 次/轮     | 避免拉取过多历史事件                 |

**超限处理**：连续收到 `RequestLimitExceeded` → 等 5 秒重试，连续 3 次仍失败 → 降低调用频率，告知用户被限流。

## 错误码与处理策略

| 错误码/场景            | Agent 行为                                                                                                                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AuthFailure.*`        | 报告鉴权失败，提示用户检查集群访问权限                                                                                                                                                                |
| `ResourceNotFound`     | 检查 ID 格式（`cdwch-` 前缀）；格式错 → 修正重试；格式对 → 请用户确认                                                                                                                                 |
| `InvalidParameter.*`   | 检查参数格式（时间范围、节点角色），尝试修正后重试 1 次；无法修正 → 报告具体问题                                                                                                                      |
| `UnsupportedRegion`    | 该地域未开通 TCHouseC 产品。**不重试、不自动切换地域**，必须调用 `ask_user` 让用户确认地域。详见 [error-handling.md §1](references/error-handling.md#1-unsupportedregion该接口不支持此地域访问) |
| `InternalError`        | 等 3 秒重试，最多 3 次；仍失败 → 报告错误码 + RequestId                                                                                                                                               |
| `RequestLimitExceeded` | 等 5 秒重试；连续 3 次 → 降低频率，告知被限流                                                                                                                                                         |
| 监控数据缺失           | 标注缺失时段，基于可用数据分析，报告中注明                                                                                                                                                            |
| 节点信息获取失败       | 跳过节点级分析，基于集群级数据给出有限诊断                                                                                                                                                            |
| 网络超时               | 等 3 秒重试，最多 3 次；仍失败 → 告知用户服务暂时不可用                                                                                                                                               |
| 兜底（未列出错误码）   | 报告完整错误信息 + RequestId                                                                                                                                                                          |

## 安全规则

1. **本 Skill 为纯只读诊断**：所有操作均为查询类（Describe），不涉及写操作，无需用户确认即可执行
2. **修复建议仅为建议**：涉及重启、配置变更等操作时，仅输出建议和步骤，不直接执行；需明确告知影响范围和建议执行时间（低峰期）
3. **凭据安全**：不在输出中展示任何凭据信息
4. **敏感信息控制**：节点 IP、配置内容等仅在诊断报告中展示，不在非必要场景暴露
5. **数据量控制**：监控指标查询时间范围不超过 7 天，避免 token 消耗过大
6. **关联诊断边界**：如果发现问题根因是慢 SQL 导致的资源耗尽，建议用户使用"慢 SQL 诊断与自动调优" Skill 进一步分析，不越界处理

## 经验沉淀库

| 经验                                            | 置信度 | 说明                                                                       |
| ----------------------------------------------- | ------ | -------------------------------------------------------------------------- |
| 磁盘告警最常见原因是 TTL 未生效或过期分区未清理 | ⭐⭐⭐ | 检查 TTL 策略和分区保留策略，`OPTIMIZE TABLE xxx FINAL` 可强制触发清理     |
| CPU 持续高负载通常伴随慢查询堆积                | ⭐⭐⭐ | 先检查 running_queries，Kill 异常长时间查询后 CPU 通常立即下降             |
| 副本延迟高优先检查 ZooKeeper 状态               | ⭐⭐   | ZK 连接异常是副本延迟的最常见根因，其次是网络和写入压力                    |
| parts 过多通常是高频小批量写入导致              | ⭐⭐⭐ | 合并小批量写入为大批量（建议单批 ≥ 10000 行），或调高 background_pool_size |
| 内存 OOM 多因单查询无内存限制                   | ⭐⭐   | 设置 `max_memory_usage` 限制单查询内存，建议 ≤ 节点内存的 70%              |
| 连接数耗尽多因客户端连接池配置不当              | ⭐⭐   | 检查客户端是否正确释放连接，建议连接池 max_idle_time ≤ 300s                |
