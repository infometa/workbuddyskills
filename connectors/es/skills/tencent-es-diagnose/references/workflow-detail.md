# 腾讯云 ES AIOps 分析工作流程指南（步骤详解）

> 本文档是 [SKILL.md「Workflow」](../SKILL.md#workflow) 的详细展开。**症状 → 首选工具/下一步** 的路由决策
> 唯一权威来源是 SKILL.md 的「症状路由表」和「强制调查顺序」表，本文档不重复该路由逻辑，只按其步骤编号
>（3A-3F）补充每一步的具体命令、判断依据、陷阱提醒与异常处理。

## 核心原则

1. **先定位集群** — 若用户未提供集群 ID，先调用 `DescribeInstances` 列出集群，让用户确认目标集群
2. **只读操作** — 严禁调用任何变更类 tool（`RestartInstance`、`RestartKibana`、`RestartNodes`、`UpdateEsAcl`、`UpdateKibanaPrivateAccess`、`UpdateKibanaPublicAccess`），只允许 `Describe*`/`Get*`/`Ces*` 只读 tool
3. **事实与推断分离** — 输出时明确区分"事实（Fact）"与"推断（Inference）"，推断需标注置信度
4. **结合官方文档** — 发现 ERROR 日志时，结合 Elasticsearch 官方文档、GitHub Issues 分析根因
5. **时间范围合理** — 问题排查默认查问题发生前后各 30 分钟；趋势分析查最近 24 小时

---

## 步骤详解

### 步骤1：健康检查获取集群全貌

**首选入口**，按 [SKILL.md「健康检查工作流」](../SKILL.md#健康检查工作流单集群) 依次聚合：基本信息 + CORE 指标 + 真实健康色 + 自动触发的 EXTENDED 指标 + 日志统计 + 变更记录。

```
# 1. 基本信息
DescribeInstances(Region="<地域>", InstanceIds=["<集群ID>"])

# 2. CORE 指标（8 个，Period=300，逐个取并做哨兵值清洗）
GetMonitorData(Region="<地域>", InstanceIds=["<集群ID>"], MetricName="CpuUsageMax", Period=300, ...)
# ... JvmMemUsageMax / DiskUsageMax / IndexLatencyAvg / SearchLatencyAvg
#     BulkRejectedCompletedPercent / Status / NodeOldGcDifMax

# 3. 真实健康色（第三路信号，建议常规调用）
CesClusterHealth(Region="<地域>", InstanceId="<集群ID>")

# 4. 按触发规则补查 EXTENDED 指标（见 SKILL.md触发规则表）
# 5. 日志统计（下推级别过滤 + 时间窗，取 TotalCount 即为计数）
DescribeInstanceLogs(Region="<地域>", InstanceId="<集群ID>", LogType=1,
                     LogLevels=["ERROR","WARN"], StartTime="<起>", EndTime="<止>")
# 6. 变更记录
DescribeInstanceOperations(Region="<地域>", InstanceId="<集群ID>",
                           StartTime="<起>", EndTime="<止>")
```

**分析产出应包含的关键内容：**

| 内容 | 用途 |
|------|------|
| `issues` | 发现的问题列表，直接指向症状方向 |
| `suggestions` | 处置建议 |
| 触发的 EXTENDED 指标及原因 | 说明为何补查这些指标 |
| CORE / EXTENDED 指标清洗后的 max/avg | 判断依据（**必须已剔除 `-2`/`-1` 哨兵值**）|
| 健康色判定依据 | 三路信号来源与取值，不一致时需注明 |

> CORE/EXTENDED 指标分层与触发规则完整设计（含排查方向、参考阈值）详见 [metrics-design.md](metrics-design.md)；打分规则见 [scoring-rules.md](scoring-rules.md)。
> 若用户仅询问集群基本信息（版本、节点数），只调用 `DescribeInstances` 即可。

#### 单集群健康检查 8 步清单

| # | 动作 | 要点 |
|---|------|------|
| 1 | `DescribeInstances` + `InstanceIds=[目标集群]` | 取 `Status`、`HealthStatus`、`EsVersion`、`NodeNum`、`TotalStorage` |
| 2 | `GetMonitorData` 取 8 个 CORE 指标（`Period=300`）| **每个指标都要做哨兵值清洗**；保留原始时序数组以支持「连续 15min」判断 |
| 3 | `CesClusterHealth` | 第三路健康信号，用于修正 `HealthStatus=-1(Unknown)` |
| 4 | 按触发规则补查 EXTENDED 指标 | 规则表见 [metrics-design.md](metrics-design.md#触发规则)；正常集群不补查，零额外开销 |
| 5 | `DescribeInstanceLogs`（`LogType=1`）| **下推过滤**：`LogLevels=["ERROR","WARN"]` + 时间窗统计数量（读 `TotalCount`）；磁盘只读关键字用 `SearchKey` 逐个查（`read_only_allow_delete`、`FORBIDDEN`、`DiskThresholdMonitor`、`flood_stage`）|
| 6 | `DescribeInstanceOperations` + 显式时间窗 | 统计总变更数与 `Progress=0` 的失败操作数 |
| 7 | 按 [scoring-rules.md](scoring-rules.md) 打分 | 严格执行**一票否决项 → 扣分项**两层规则，禁止凭感觉估分 |
| 8 | 低分（`score < 85`）时深度诊断 | 按 [SKILL.md 症状路由表](../SKILL.md#症状路由表) 调用数据面 tool 定位根因 |

---

## 批量巡检工作流（多集群）

| # | 动作 | 要点 |
|---|------|------|
| 1 | `DescribeInstances`（`Limit=100` + 分页）| 拉全量集群；`TotalCount` > 已取条数时 `Offset += Limit` |
| 2 | **跳过** `Status != 1` 的集群 | 标记 `❓ N/A`，原因记为「集群状态异常」，不参与打分 |
| 3 | `GetMonitorData` **按指标维度**批量取数 | `InstanceIds` 传入全部集群 ID，**8 次调用覆盖所有集群**，而非按集群循环（N×8 次）|
| 4 | 逐集群按 [scoring-rules.md](scoring-rules.md) 打分 | 按分数**升序**排列（最差排最前）|
| 5 | `score < 85` 的集群标记 ⚡ | 对其执行上文「单集群健康检查 8 步清单」定位根因 |
| 6 | 输出 Dashboard | 四档口径见 [scoring-rules.md](scoring-rules.md#评分等级与触发动作)，每行显示分数 + 等级字母 |

**批量取数的两个实操约束：**

- **回填靠 Dimensions，不靠下标**：通过 `DataPoints[].Dimensions[].Value` 把时序对应回各集群，**不要假定返回顺序与传入顺序一致**
- **批量条数上限**：云监控对 `InstanceIds` 数组长度有限制，集群数较多时需**拆批调用**；若返回条数少于传入集群数，说明已被截断，必须拆批重试
- **EXTENDED 指标不在批量阶段补查**：批量阶段只取 8 个 CORE 指标；`SearchRejectedCompletedPercent`、`ClusterNumberOfPendingTasks` 等 EXTENDED 指标在第 5 步的单集群深度诊断中按触发规则补查

---

### 步骤2：解读检查结果，确定症状方向

根据 `issues` 中出现的指标关键词（如 `Status`/`CpuUsageMax`/`BulkRejectedCompletedPercent` 等），
对照 [SKILL.md「症状路由表」](../SKILL.md#症状路由表) 定位到对应症状方向，即可确定下一步该看本文档的哪个步骤（3A-3F）。

> 各指标的正常/告警/严重阈值判定，唯一权威来源见 [scoring-rules.md](scoring-rules.md)（评分规则）与 [metrics-design.md](metrics-design.md)（指标分层设计）。各症状的端到端诊断步骤见 [scenarios.md](scenarios.md)。

---

### 步骤3A：日志分析（集群 Red/Yellow 场景）

```
# 主日志（下推 ERROR 级别过滤；也可用 SearchKey="message:shard" 直接命中分片相关报错）
DescribeInstanceLogs(Region="<地域>", InstanceId="<集群ID>", LogType=1,
                     LogLevels=["ERROR","WARN"], StartTime="<起>", EndTime="<止>")

# 权威手段：直接问 ES 为什么分片不能分配
CesClusterAllocationExplain(Region="<地域>", InstanceId="<集群ID>")
CesGetShards(Region="<地域>", InstanceId="<集群ID>")
```

**常见 ERROR 关键词及含义（含报告置信度标注）：**

| 关键词 | 可能原因 | 置信度 |
|--------|---------|--------|
| `OutOfMemoryError` | JVM 堆内存不足，GC 无法回收 | 高 |
| `CircuitBreakingException` | 内存熔断，查询/写入被拒绝 | 高 |
| `DiskWatermarkException` | 磁盘使用率超过水位线，写入被阻断 | 高 |
| `ShardLockObtainFailedException` | 分片锁获取失败，可能有节点重启 | 中 |
| `ClusterBlockException` | 集群被阻塞，通常因磁盘满或只读模式 | 高 |
| `NodeDisconnectedException` | 节点断连，可能是网络或 OOM 导致 | 中 |
| `master_not_discovered` | Master 节点未发现，集群脑裂或 Master 宕机 | 高 |
| `rejected execution` | 线程池队列满，写入/查询被拒绝 | 高 |

→ 完整根因分析流程（含交叉指标验证、`_cluster/allocation/explain` 判读）见 [scenarios.md 场景A](scenarios.md#场景-a集群-red-根因分析)

---

### 步骤3B：日志分析（CPU 高场景）

先判断 CPU 高的**形态**（持续/周期性/突发），再按方向查日志（GC 日志用 `LogType=4`，找 `"Full GC"` 关键字，GC 日志无 level 字段）。

→ 完整取数命令、交叉指标验证、现象→根因映射表见 [scenarios.md 场景B](scenarios.md#场景-bcpu-持续高排查)

---

### 步骤3C：日志分析（写入拒绝场景）

注意区分"写入排队"（`WriteQueueMax` 积压，前驱信号）和"写入被拒"（`BulkRejected` > 0，已发生数据丢失风险）。

→ 完整取数命令、现象→根因映射表见 [scenarios.md 场景C](scenarios.md#场景-c写入拒绝排查)

---

### 步骤3D：日志分析（查询慢场景）

**慢日志关键字段**：`took_millis`（耗时）、`search_type`（查询类型）、`source`（DSL 内容）
**LogType**：查询慢用 `2`（搜索慢日志），写入慢用 `3`（索引慢日志）

→ 详细字段解读见 [slow-log-guide.md](slow-log-guide.md)
→ 完整取数命令、根因判断见 [scenarios.md 场景E](scenarios.md#场景-e查询慢排查)

---

### 步骤3E：日志分析（磁盘/JVM/GC 场景）

腾讯云 ES 默认 watermark 阈值：`low`（85%，停止分配新分片）→ `high`（90%，迁移分片）→ `flood_stage`（95%，强制只读）。

→ 磁盘场景完整排查流程见 [scenarios.md 场景F](scenarios.md#场景-f磁盘告警--io-打满)
→ JVM/GC 场景完整排查流程见 [scenarios.md 场景G](scenarios.md#场景-gjvm-oom--gc-频繁)

---

### 步骤3F：变更记录分析（异常变更/节点重启场景）

```
DescribeInstanceOperations(Region="<地域>", InstanceId="<集群ID>",
                           StartTime="<最近24小时起始>", EndTime="<当前时间>")

# 核对节点是否已全部恢复
CesGetNode(Region="<地域>", InstanceId="<集群ID>")
```

**关注点：**
- 变更时间是否与异常时间吻合（时间线对齐）
- 是否有节点重启、扩缩容、配置变更操作
- 变更状态是否为失败（`Progress=0`）
- **必须显式传时间窗口** —— 否则默认拉2017 年至今全量记录

→ 完整根因分析流程见 [scenarios.md 场景H](scenarios.md#场景-h节点重启--异常变更排查)

---

### 步骤4：输出分析报告

#### 输出规范

严格区分事实与推断：

- **事实（Fact）**：API 返回的客观数据
  > 示例：集群 es-xxxxxxxx 在 2024-01-01 10:15:00 出现 `CircuitBreakingException`，共 127 条 ERROR 日志，同时段 JVM 内存使用率达到 92%。

- **推断（Inference）**：基于数据的分析，需标注置信度（高/中/低）
  > 示例：**[推断-高置信度]** JVM 内存持续超过 90% 触发内存熔断，导致查询请求被拒绝，这是集群 Yellow 状态的直接原因。建议：升级节点规格或优化查询语句减少内存占用。

#### 报告结构

```
## 集群分析报告：<集群ID>

### 基本信息
- 集群状态：<状态>
- 健康状态：<Green/Yellow/Red>
- 节点数：<N>
- ES 版本：<版本>

### 问题摘要
<1-3 句话描述核心问题>

### 事实（Fact）
- <基于 API 数据的客观描述>

### 根因分析（Inference）
- **[高置信度]** <主要根因>
- **[中置信度]** <次要可能原因>

### 处置建议
1. <具体可操作的建议>
2. <参考文档链接>
```

---

## 异常处理指引

| 异常场景 | 处理方式 |
|---------|---------|
| 用户未提供集群 ID | 调用 `DescribeInstances` 列出集群，让用户选择 |
| 用户未提供地域 | 询问用户地域，或列出常用地域供选择 |
| MCP tools 不可用 / 调用报连接错误 | 提示用户在连接器管理页面完成配置并连接；**不要**尝试用 tccli 等方式绕行 |
| API 返回 AuthFailure | 提示用户确认连接器所用账号具备 `es:Describe*`/`monitor:GetMonitorData` 权限 |
| API 返回 ResourceNotFound | 集群 ID 不存在或地域不匹配，提示用户确认 |
| 日志为空 | 说明该时间段无日志，建议换日志类型（`LogType` 1/2/3/4）确认 |
| **监控数据全为 `-2` / `-1`** | **哨兵值，表示探针失联，不是"指标很低"**。立即用 `CesClusterHealth` + `CesGetAllocation` 数据面核实真实状态，并按一票否决规则 1e 压分 |
| 监控数据全为 0 | 可能是集群停止或监控未上报，建议检查集群 `Status` |
| 数据面 tool 超时/不可达 | 集群可能已不可用（磁盘打满、节点全挂）——**这本身是重要诊断信号** |
| 返回结果过大被截断落盘 | 用 Python（`json.load`）解析落盘文件提取字段，环境可能无 `jq` |
| 接口限频（RequestLimitExceeded）| 降低调用频率，稍后重试 |
