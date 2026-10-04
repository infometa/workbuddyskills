# 腾讯云 ES 数据面运维工作流程指南

> 🔴 **本文档是执行流程、确认话术、流程层异常处理的唯一权威来源（SSOT）**。
>
> **本文档不重复 tool 参数与服务端约束** —— 参数枚举、取值区间、服务端强制前置检查一律以 [`references/ces-tools-reference.md`](references/ces-tools-reference.md)（下称「tool 参考」）为准。文中 §N 指向该文档对应章节，**标注「必读」的必须真正读完再执行**。

## 核心原则

1. **先只读核对** — 任何变更前必须先调只读 tool：`CesClusterHealth` 看健康度，改 settings 前用 `CesGetClusterSettings` / `CesGetIndexInfo(Type=settings)` 读当前值
2. **参数是严格枚举，不是原生 key** — 写类 tool 只认固定参数名，用户提的原生 ES setting 必须先映射；映射不到就如实说不支持。映射表见 [§17 **必读**](references/ces-tools-reference.md#17-cesupdateclustersettings集群-settings-变更-) / [§18 **必读**](references/ces-tools-reference.md#18-cesupdateindexsettings索引-settings-变更-)
3. **根因优先** — `CesClusterReroute` 前必须先 `CesClusterAllocationExplain` 查根因并解决，否则重试必然再失败
4. **逐条单一变更** — 通配表达式先展开为具体索引，**逐个索引单独确认、单独调用**，禁止打包确认
5. **二次确认机制** — 展示完整 tool 名 + 全部参数 + 影响，获得用户明确确认。**无脚本层兜底，Agent 是唯一防线**
6. **能预演就预演** — `CesRolloverIndex` 先 `DryRun=true` 跑一次确认后再实际执行
7. **不在故障中扩大影响面** — Red / yellow 集群上不做 `close`、不做 rollover、不调低副本数
8. **不绕行** — MCP tools 不可用或能力缺失时引导控制台 / Kibana Dev Tools，**绝不用 tccli / curl 云 API / ES 直连绕过**
9. **变更后回读核对** — 变更提交后回读实际状态，基于真实返回汇报，禁止凭空推测
10. **临时配置必须收尾** — `AllocationEnable=none/primaries`、`RefreshInterval=-1` 等临时配置，必须在确认信息中写明"完成后需改回"，并在后续对话主动提醒

---

## 主流程决策树

```mermaid
flowchart TD
    A([用户请求数据面运维]) --> A0{MCP tools<br/>可用？}
    A0 -- 否 --> A1["⛔ 提示用户在连接器管理页面配置并连接<br/>禁止用 tccli / curl / ES 直连绕行"]
    A0 -- 是 --> B{已提供集群 ID + 地域？}
    B -- 否 --> C["引导用户提供集群 ID 与地域<br/>（本 Skill 无集群列表能力）"]
    C --> B
    B -- 是 --> D["CesClusterHealth 核对健康度"]
    D --> E{用户意图分类}

    E -- "只读查询 / 诊断取数" --> F["直接调对应只读 tool<br/>无需确认"]
    E -- "分片未分配 / yellow、red" --> G["CesClusterAllocationExplain<br/>查根因"]
    E -- "settings 变更" --> H["先读当前值：<br/>CesGetClusterSettings /<br/>CesGetIndexInfo(Type=settings)"]
    E -- "索引开关 / 刷新 / 别名 / 滚动" --> I["CesListIndices 确认<br/>索引状态与别名指向"]
    E -- "取消任务" --> J["CesTasks 拿 TaskId<br/>+ 确认 cancellable"]
    E -- "扩容 / 升配 / 重启 / Kibana" --> Z1["⛔ 属管控面<br/>→ tencent-es-control-panel"]
    E -- "根因分析 / 监控趋势" --> Z2["⛔ 属诊断<br/>→ tencent-es-diagnose"]

    G --> G1{根因类型}
    G1 -- "磁盘超水位" --> G2["调水位 或 交管控面扩磁盘"]
    G1 -- "副本数过高" --> G3["CesUpdateIndexSettings<br/>调低 NumberOfReplicas"]
    G1 -- "感知规则冲突" --> G4["⛔ 无 tool 支持<br/>如实告知 + 引导控制台"]
    G2 & G3 --> G5["根因解决后<br/>CesClusterReroute"]

    H --> H1{原生 key 能映射到<br/>tool 参数？}
    H1 -- 否 --> H2["⛔ 如实告知不支持<br/>引导控制台 / Dev Tools"]
    H1 -- 是 --> H3["集群级：读取 persistent / transient / defaults<br/>同名 transient 会被自动清除，须纳入确认"]

    I --> I1{目标操作是否<br/>要求集群正常态？}
    I1 -- "是（rollover / close）" --> I2{集群健康？}
    I2 -- 否 --> I3["⛔ 会被服务端阻断<br/>建议先处理健康问题"]
    I2 -- 是 --> I4["rollover 先 DryRun=true 预演"]
    I1 -- 否 --> K

    G5 & H3 & I4 & J --> K["📋 展示完整 tool 名 + 全部参数<br/>+ 影响 + 回滚方式"]
    K --> L{高风险操作？<br/>close / CancelTask / 副本数=0}
    L -- 是 --> M["🔴 加码风险警告<br/>见「高风险操作确认」"]
    L -- 否 --> N
    M --> N{用户明确确认？}
    N -- 否 --> O([取消，不执行])
    N -- 是 --> P["调用变更 tool"]
    P --> Q{服务端前置检查通过？}
    Q -- 否 --> R["如实转述阻断原因<br/>❌ 不重试、不换参数硬闯"]
    Q -- 是 --> U["只读 tool 回读核对生效<br/>集群 settings 同时核对 transient 已清除"]
    U --> V{有临时配置需收尾？}
    V -- 是 --> W["主动提醒需改回<br/>AllocationEnable=all / RefreshInterval"]
```

---

## 五大典型场景流程图

### 场景 A：分片未分配 / 集群 yellow、red 恢复

> 适用：集群 yellow / red，有 unassigned 分片需要恢复。

```mermaid
flowchart TD
    A([集群 yellow / red]) --> B["CesClusterHealth"]
    B --> C{unassigned_shards > 0？}
    C -- 否 --> D["无未分配分片<br/>问题可能在别处<br/>→ tencent-es-diagnose"]
    C -- 是 --> E["CesClusterAllocationExplain<br/>🔴 查根本原因"]
    E --> F{根因}
    F -- "磁盘超水位" --> G1["CesGetAllocation 看实际使用率"]
    G1 --> G2{能否腾空间 / 调水位？}
    G2 -- 能 --> G3["CesUpdateClusterSettings<br/>(DiskWatermark*)<br/>⚠️ 三档统一单位 low<high<flood"]
    G2 -- 不能 --> G4["→ tencent-es-control-panel 扩磁盘"]
    F -- "节点数不足以满足副本数" --> H1["CesClusterHealth 读<br/>number_of_data_nodes"]
    H1 --> H2["CesUpdateIndexSettings<br/>NumberOfReplicas ≤ 数据节点数-1"]
    F -- "分片感知 / filter 规则冲突" --> I1["⛔ 无 tool 支持该类 setting<br/>如实告知 + 引导控制台"]
    F -- "分配重试达上限 max_retry" --> J1["根因已解决？"]
    J1 -- 否 --> E
    G3 & H2 & J1 --> K["CesClusterReroute<br/>（幂等，无参数）"]
    K --> L["CesClusterHealth / CesGetShards<br/>观察是否开始分配"]
    L --> L1["CesGetRecovery(ActiveOnly=true)<br/>跟踪恢复百分比、速率、剩余量"]
    L1 --> M{分片开始 INITIALIZING？}
    M -- 是 --> N["可选：CesUpdateClusterSettings<br/>RecoveryMaxBytesPerSec / NodeConcurrentRecoveries<br/>⚠️ 占 IO/网络，完成后回退"]
    M -- 否 --> O["再次 CesClusterAllocationExplain<br/>根因可能仍未解决"]
```

### 场景 B：索引 settings 变更（副本数 / 刷新间隔 / translog / 解除只读）

```mermaid
flowchart TD
    A([用户要改索引配置]) --> B{用户给的是<br/>原生 setting key？}
    B -- 是 --> C{能映射到 11 个<br/>tool 参数之一？}
    C -- 否 --> D["⛔ 如实告知不支持<br/>常见：number_of_shards（静态）、<br/>mapping、blocks.write、routing.allocation.require.*"]
    C -- 是 --> E
    B -- 否 --> E["CesListIndices 确认索引存在<br/>（通配则展开为具体列表）"]
    E --> F["CesGetIndexInfo(Type=settings) 读当前值"]
    F --> G{改的是哪一项？}
    G -- NumberOfReplicas --> H1["CesClusterHealth 数数据节点数<br/>🔴 目标值 ≤ 数据节点数-1"]
    H1 --> H2{目标值 = 0？}
    H2 -- 是 --> H3["🔴 警告：失去全部冗余<br/>节点故障即丢数据"]
    H2 -- 否 --> I
    G -- RefreshInterval --> J1{目标值 = -1？}
    J1 -- 是 --> J2["⚠️ 告知：业务将查不到新数据<br/>必须写明「导入完须改回」"]
    J1 -- 否 --> J3["⚠️ 最小 1s，更小会被服务端拒绝"]
    G -- ReadOnlyAllowDelete --> K1["CesGetAllocation<br/>🔴 确认磁盘空间已腾出"]
    K1 --> K2{空间已腾出？}
    K2 -- 否 --> K3["⛔ 不要解除<br/>ES 会立刻重新加上阻塞<br/>先腾空间或扩磁盘"]
    K2 -- 是 --> I
    G -- Translog* --> L1{改为 async？}
    L1 -- 是 --> L2["🔴 告知丢数据窗口<br/>确认业务可接受"]
    L1 -- 否 --> I
    G -- DelayedTimeout --> D1["⚠️ 最大 24h<br/>维护后恢复原值"]
    G -- IndexPriority --> D2["0..1000<br/>仅提高核心索引"]
    G -- MaxResultWindow --> D3["⚠️ 深分页内存风险<br/>>50000 风险高，优先 search_after"]
    G -- MappingTotalFieldsLimit --> D4["⚠️ 字段爆炸救急<br/>根治须优化数据模型"]
    G -- TotalShardsPerNode --> D5["🔴 校验分片容量公式<br/>仅支持放宽"]
    H3 & J2 & J3 & L2 & D1 & D2 & D3 & D4 & D5 & I["📋 展示 diff + 影响"] --> M{用户确认？}
    M -- 否 --> N([取消])
    M -- 是 --> O["CesUpdateIndexSettings<br/>（逐个索引单独调用）"]
    O --> P["CesGetIndexInfo(Type=settings) 回读核对"]
```

### 场景 C：别名切换 / 索引滚动

```mermaid
flowchart TD
    A([别名 / 滚动需求]) --> B["CesListIndices<br/>确认别名当前指向哪个索引"]
    B --> C{需求类型}

    C -- "切到新索引（reindex 后）" --> D["CesUpdateAliases<br/>RemoveIndex=旧 + AddIndex=新<br/>= 原子零停机切换"]
    C -- "新增别名指向" --> E["CesUpdateAliases(AddIndex)"]
    C -- "删除别名指向" --> F["CesUpdateAliases(RemoveIndex)<br/>ℹ️ 唯一能删别名的途径"]
    C -- "日志索引太大要滚动" --> G["CesListIndices 确认别名指向<br/>+ CesCatIndices 看 docs.count / pri.store.size<br/>🔴 人工判断时机（tool 不支持条件触发）"]

    G --> H{别名指向索引名<br/>符合 xxx-000001？}
    H -- 否 --> I["⛔ 本 tool 不支持指定目标索引名<br/>→ 改用 CesUpdateAliases 手工切换"]
    H -- 是 --> J{集群健康正常？}
    J -- 否 --> K["⛔ rollover 要求集群正常态<br/>会被服务端阻断"]
    J -- 是 --> L["CesRolloverIndex(DryRun=true)<br/>🔴 先预演，零副作用"]
    L --> M["核对返回的将要创建的索引名"]
    M --> N["📋 展示确认信息"]

    D & E & F --> N
    N --> O{用户确认？}
    O -- 否 --> P([取消])
    O -- 是 --> Q["调用 tool"]
    Q --> R["CesListIndices 回读<br/>核对别名指向已变更"]
```

### 场景 D：任务失控 / 取消任务

```mermaid
flowchart TD
    A([有任务占资源 / 失控]) --> B["CesTasks<br/>列出正在执行的任务"]
    B --> C["按 running_time 判断哪个异常<br/>action 看任务类型"]
    C --> D{cancellable = true？}
    D -- 否 --> E["⛔ 该任务 ES 标记不可取消<br/>如实告知，无法通过本 Skill 取消"]
    D -- 是 --> F{任务类型}
    F -- "reindex" --> G1["🔴 告知：已写入目标索引的文档保留<br/>目标索引将数据不完整<br/>取消后需人工清理或重跑"]
    F -- "delete_by_query" --> G2["🔴 告知：已删除文档无法恢复"]
    F -- "update_by_query / forcemerge / search" --> G3["告知：已完成部分不回滚"]
    G1 & G2 & G3 --> H["📋 高风险确认<br/>展示 task_id + action + running_time"]
    H --> I{用户确认？}
    I -- 否 --> J([取消])
    I -- 是 --> K["CesCancelTask(TaskId)"]
    K --> L["⚠️ 说明：协作式取消<br/>返回成功仅表示标记已设置<br/>不保证立即结束"]
    L --> M["CesTasks 回读确认任务是否消失"]
    M --> N{仍在？}
    N -- 是 --> O["提示：任务尚未到达可中断点<br/>稍后再回读，不重复调用"]
    N -- 否 --> P["告知已停止<br/>+ 后续清理建议"]
```

### 场景 E：数据写进去了但查不到

```mermaid
flowchart TD
    A([用户：数据写了查不到]) --> B["CesGetIndexInfo(Type=settings)<br/>看 refresh_interval"]
    B --> C{refresh_interval = -1？}
    C -- 是 --> D["找到原因：自动刷新被关闭<br/>🔴 正确顺序："]
    D --> E["① CesUpdateIndexSettings<br/>RefreshInterval 改回 1s / 30s"]
    E --> F["② CesRefreshIndex 刷新一次"]
    C -- 否 --> G{距写入 < 1s？}
    G -- 是 --> H["属正常现象<br/>ES 默认 1s 刷新<br/>可 CesRefreshIndex 立即刷新"]
    G -- 否 --> I["CesGetShards 看分片状态<br/>可能是分片未分配 / 索引被 close"]
    I --> J{索引 status = close？}
    J -- 是 --> K["→ CesUpdateIndexState(State=open)"]
    J -- 否 --> L["→ 转场景 A 排查分片<br/>或交 tencent-es-diagnose"]
    F & H --> M["回读确认数据可查"]
```

---

## 步骤详解

### 步骤 1：只读核对现状（必须执行）

**任何变更前的必要步骤。**

```
# 通用第一步
CesClusterHealth(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")

# 集群 settings 变更前
CesGetClusterSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
  → 🔴 展示 persistent / transient / defaults；同名 transient 会在写入时自动清除，必须纳入确认

# 索引 settings 变更前
CesGetIndexInfo(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                Index="my_index", Type="settings")

# 索引 / 别名类变更前
CesListIndices(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", Index="logs-*")
  → 确认索引存在、status（open/close）、别名当前指向
```

> 🔴 **必读** [§1](references/ces-tools-reference.md#1-cesclusterhealth集群健康-) / [§10](references/ces-tools-reference.md#10-cesgetclustersettings集群-settings-) / [§11](references/ces-tools-reference.md#11-ceslistindices索引与别名列表-)：各返回字段判读、三层优先级机制。**禁止**凭印象判断。

---

### 步骤 2：原生 key → tool 参数映射（settings 变更必做）

用户通常会用 ES 原生 setting key 描述需求，**必须先映射**：

| 用户说的 | 映射到 |
|---------|-------|
| `indices.recovery.max_bytes_per_sec` | `CesUpdateClusterSettings(RecoveryMaxBytesPerSec)` |
| `cluster.routing.allocation.enable` | `CesUpdateClusterSettings(AllocationEnable)` |
| `cluster.routing.allocation.disk.watermark.low/high/flood_stage` | `CesUpdateClusterSettings(DiskWatermarkLow/High/FloodStage)` |
| `cluster.routing.allocation.node_concurrent_recoveries` | `CesUpdateClusterSettings(NodeConcurrentRecoveries)` |
| `cluster.routing.allocation.node_initial_primaries_recoveries` | `CesUpdateClusterSettings(NodeInitialPrimariesRecoveries)` |
| `cluster.routing.rebalance.enable` | `CesUpdateClusterSettings(RebalanceEnable)` |
| `cluster.max_shards_per_node` | `CesUpdateClusterSettings(MaxShardsPerNode)` |
| `index.number_of_replicas` | `CesUpdateIndexSettings(NumberOfReplicas)` |
| `index.refresh_interval` | `CesUpdateIndexSettings(RefreshInterval)` |
| `index.translog.durability / sync_interval / flush_threshold_size` | `CesUpdateIndexSettings(TranslogDurability / TranslogSyncInterval / TranslogFlushThresholdSize)` |
| `index.blocks.read_only_allow_delete` | `CesUpdateIndexSettings(ReadOnlyAllowDelete)`（**只能解除**） |
| `index.unassigned.node_left.delayed_timeout` | `CesUpdateIndexSettings(DelayedTimeout)` |
| `index.priority` | `CesUpdateIndexSettings(IndexPriority)` |
| `index.max_result_window` | `CesUpdateIndexSettings(MaxResultWindow)` |
| `index.mapping.total_fields.limit` | `CesUpdateIndexSettings(MappingTotalFieldsLimit)` |
| `index.routing.allocation.total_shards_per_node` | `CesUpdateIndexSettings(TotalShardsPerNode)` |

**映射不到的一律如实告知不支持**，常见有：`cluster.routing.allocation.cluster_concurrent_rebalance`、`awareness.*`、`allocation.filter.*`、`index.number_of_shards`（静态）、`index.blocks.write`、`index.routing.allocation.require.*`、mapping 变更。

> 🔴 **必读** [§17](references/ces-tools-reference.md#17-cesupdateclustersettings集群-settings-变更-) / [§18](references/ces-tools-reference.md#18-cesupdateindexsettings索引-settings-变更-)：完整映射表、取值格式、服务端校验。

---

### 步骤 3：通配表达式展开（逐条原则）

用户说「把 `logs-*` 的副本数都改成 1」时：

```
① CesListIndices(Index="logs-*")  → 展开为 logs-2026.08.24 / logs-2026.08.25 / logs-2026.08.26
② 告知用户命中 3 个索引，列出清单
③ 🔴 逐个索引单独展示确认信息、单独获得确认、单独调用 tool
```

> 🚫 **禁止打包为一次确认**（"这 3 个都改，确认吗？"）。写类 tool 本身也禁止通配符入参。
> 💡 索引数量很多时（如命中 50 个），先如实告知数量，询问用户是否确实要逐个执行，或建议改用控制台批量操作。

---

### 步骤 4：展示确认信息并获得确认

见下方 [确认交互规范](#确认交互规范-确认话术的唯一权威来源)。

---

### 步骤 5：调用 tool 并处理返回

| 返回情况 | 处理 |
|---------|------|
| 成功 | 进入步骤 6 回读；`CesUpdateClusterSettings` 还须核对目标项的同名 transient 已清除、persistent 为目标值 |
| 返回包含自动清除 transient 的信息 | 属预期行为；如实说明被清除的旧值及当前生效来源，不得省略该副作用 |
| 服务端前置检查阻断 | 如实转述原因，**不重试、不换参数硬闯** |
| 参数校验失败 | 按 [附录 A](references/ces-tools-reference.md#附录-a索引--别名命名约束全局通用) 修正后**重新走一轮确认** |

---

### 步骤 6：回读核对生效

| 刚执行的变更 | 回读 tool |
|------------|----------|
| `CesUpdateClusterSettings` | `CesGetClusterSettings`（核对 persistent 目标值与同名 transient 已清除）；恢复参数变更再用 `CesGetRecovery(ActiveOnly=true)` 看效果 |
| `CesUpdateIndexSettings` | `CesGetIndexInfo(Type=settings)`；调大副本数/恢复优先级时再用 `CesGetRecovery(ActiveOnly=true)` |
| `CesClusterReroute` | `CesClusterHealth` + `CesGetShards` + `CesGetRecovery(ActiveOnly=true)` |
| `CesUpdateIndexState` | `CesListIndices`（看 status）+ `CesClusterHealth`；open 后用 `CesGetRecovery(ActiveOnly=true)` |
| `CesUpdateAliases` | `CesListIndices`（看别名指向） |
| `CesRolloverIndex` | `CesListIndices`（看别名指向）+ `CesCatIndices`（看新旧索引量化信息） |
| `CesCancelTask` | `CesTasks`（任务是否消失） |
| `CesRefreshIndex` | 返回体 `_shards` 即为结果，无需额外回读 |

> 📌 **基于真实返回汇报**，禁止凭空推测"应该已经生效了"。

---

### 步骤 7：临时配置收尾提醒（必做）

以下操作属**临时配置**，执行后必须主动提醒：

| 临时配置 | 提醒内容 |
|---------|---------|
| `AllocationEnable = none` / `primaries` | 🔴 运维窗口结束后**必须改回 `all`**，否则分片长期无法分配、集群持续 yellow / red |
| `RebalanceEnable != all` | 🔴 运维窗口结束后**必须改回 `all`**，否则分片可能长期分布不均 |
| `RefreshInterval = -1` | 🔴 批量导入完成后**必须改回**（`1s` / `30s`），否则业务永久查不到新数据 |
| `RecoveryMaxBytesPerSec` / `NodeConcurrentRecoveries` / `NodeInitialPrimariesRecoveries` 调大 | 恢复完成后建议恢复原值，避免长期占用 IO、CPU 与网络影响在线业务 |
| `DelayedTimeout` 调大 | 滚动维护完成后恢复原值，避免真实节点故障时延迟副本恢复 |
| `TranslogDurability = async` | 存在丢数据窗口，业务对数据安全要求提高时需改回 `request` |

> 💡 在确认信息中就要写明"完成后需改回 X"，并在变更成功的汇报里再提醒一次。

---

## 确认交互规范（🔴 确认话术的唯一权威来源）

> 以下模板是**变更前的唯一防线**，必须完整展示 tool 名 + 全部参数 + diff + 影响，不得简化。
> **只读 tool 无需确认**，可直接调用。

### 标准变更确认（索引 settings）

```
请确认是否执行以下变更：

Tool：CesUpdateIndexSettings
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      Index=my_index, NumberOfReplicas=1

集群健康状态：green ✅（数据节点数 3，上限 NumberOfReplicas ≤ 2）
索引：my_index

变更详情：
  副本数：2 → 1

预期影响：
  - 会触发实际数据变更（删除多余副本分片），期间可能有 IO 开销
  - 单分片冗余从 2 份降为 1 份，仍保留冗余
  - 可回滚：再改回 2 即可（会触发数据复制）

请回复「确认」执行，或回复其他内容取消。
```

新增索引参数的确认信息还必须包含对应风险：

| 参数 | 确认时必须说明 |
|------|---------------|
| `DelayedTimeout` | 延迟真实故障后的副本恢复；滚动维护完成后恢复原值 |
| `IndexPriority` | 只提高核心索引；优先级调整不增加实际恢复资源 |
| `MaxResultWindow` | 深分页增加协调节点内存，超过 50000 有 OOM 风险；优先 `search_after` |
| `MappingTotalFieldsLimit` | 仅字段爆炸救急；上调会增加查询与 master 元数据压力，根治应优化数据模型 |
| `TotalShardsPerNode` | 必须展示容量公式校验结果；放宽可能形成节点热点，不能代替减少分片或扩容 |

### 标准变更确认（集群 settings）

```
请确认是否执行以下变更：

Tool：CesUpdateClusterSettings
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      RecoveryMaxBytesPerSec=100mb

当前值（persistent）：40mb
当前值（transient）：无同名项 ✅

变更详情：
  persistent 分片恢复带宽上限：40mb → 100mb
  transient 同名项：无（如存在，tool 会自动清除为 null）

预期影响：
  - 加快节点故障后的分片恢复速度
  - ⚠️ 会占用更多网络与磁盘 IO，可能影响在线查询延迟
  - 建议在业务低峰期执行
  - 恢复完成后建议调回 40mb

请回复「确认」执行，或回复其他内容取消。
```

> ⚠️ 若 `CesGetClusterSettings` 显示 **transient 层已有同名项**，确认信息中必须写明：
> `transient 层检查：⚠️ 已存在同名项（值 X）；本次 tool 会自动将其清除为 null，并把目标值写入 persistent，使 persistent 值立即生效`
> 这是额外配置变化，必须纳入二次确认，执行后回读三层结果。

新增集群参数的确认信息还必须包含对应风险：

| 参数 | 确认时必须说明 |
|------|---------------|
| `NodeConcurrentRecoveries` | 调大会增加恢复 IO/CPU/网络压力；恢复完成后建议回退原值 |
| `NodeInitialPrimariesRecoveries` | 仅影响本地主分片初始恢复；调大会增加节点磁盘 IO/CPU 压力 |
| `RebalanceEnable` | 与 `AllocationEnable` 语义不同；非 `all` 为临时状态，维护后必须改回 `all` |
| `MaxShardsPerNode` | 仅 ES 7.0+；调大只是分片上限救急，会增加 master 元数据负担，根治应减少分片或扩节点 |

### 别名切换确认

```
请确认是否执行以下变更：

Tool：CesUpdateAliases
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      Alias=my_alias, RemoveIndex=my_index_v1, AddIndex=my_index_v2

别名当前指向：my_index_v1
变更后指向：  my_index_v2

预期影响：
  - 原子切换（remove 先于 add），业务流量无缝切到新索引，零停机
  - 🔴 所有通过 my_alias 读写的业务流量将立即改向 my_index_v2
  - 旧索引 my_index_v1 仍存在且可直接按索引名查询
  - 可回滚：反向再切一次（Alias=my_alias, RemoveIndex=my_index_v2, AddIndex=my_index_v1）

请回复「确认」执行。
```

### 索引滚动确认（先预演）

```
已完成 DryRun 预演（零副作用），结果如下：

Tool：CesRolloverIndex（DryRun=true）
当前别名 my_logs_write 指向：my_logs-000001
  文档数：128,450,000    存储：42.3gb
预演结果：将创建新索引 my_logs-000002

集群健康状态：green ✅（rollover 要求集群正常态）

现在请确认是否实际执行：

Tool：CesRolloverIndex
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx, Alias=my_logs_write

预期影响：
  - 立即创建 my_logs-000002，别名切换到新索引，新数据写入新索引
  - 旧索引 my_logs-000001 仍可查询
  - ⚠️ 本 tool 为无条件立即滚动，不设 max_size / max_age 条件
  - 回滚需用 CesUpdateAliases 手工把别名切回旧索引

请回复「确认」执行。
```

### 高风险操作确认

> 🔴 以下三类操作**必须**用加码模板，显著标注风险后果。

#### ① 关闭索引（制造不可用）

```
🔴 高风险操作警告！

即将关闭索引 my_old_index —— 关闭后该索引【既不可读也不可写】。

Tool：CesUpdateIndexState
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      Index=my_old_index, State=close

风险后果：
  - 🔴 该索引上的所有读写请求都会失败（这是「制造不可用」的操作）
  - 请务必确认业务已完全不再访问该索引
  - ⚠️ ES 6.x / 7.0 / 7.1 在索引关闭期间【不复制副本】，此时若发生节点故障存在丢数据风险
    （当前集群版本：<版本号>）

收益：释放该索引占用的集群堆内存

可回滚：CesUpdateIndexState(State=open) 重新打开（会触发分片恢复，大索引耗时较长）

如确认业务已不再访问该索引，请回复「确认关闭」。
```

#### ② 取消任务（已完成部分不回滚）

```
🔴 高风险操作警告！

即将取消任务：
  task_id：oTUltX4IQMOUUVeiohTt8A:12345
  action：indices:data/write/reindex
  已运行：47 分钟

Tool：CesCancelTask
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      TaskId=oTUltX4IQMOUUVeiohTt8A:12345

风险后果：
  - 🔴 【已完成的部分不会回滚】——已写入目标索引的文档会保留，
    造成目标索引数据不完整，取消后通常需要人工清理或重跑
  - ⚠️ ES 取消是【协作式】的：返回成功仅表示取消标记已设置，
    任务会在到达下一个可中断点时才真正停止，不保证立即结束

收益：释放该任务占用的 CPU / IO / 内存资源，缓解集群压力

不可回滚（任务无法恢复继续，只能重新发起）

如确认要取消，请回复「确认取消」。
```

> 若任务是 `delete_by_query`，风险后果改为：`🔴 已删除的文档【无法恢复】`。

#### ③ 副本数设为 0（失去全部冗余）

```
🔴 高风险操作警告！

即将把索引 my_index 的副本数设为 0 —— 该索引将【失去全部冗余】。

Tool：CesUpdateIndexSettings
参数：Region=ap-guangzhou, InstanceId=es-xxxxxxxx,
      Index=my_index, NumberOfReplicas=0

风险后果：
  - 🔴 任一持有该索引主分片的节点发生故障，该分片数据【直接丢失】且无法恢复
  - 查询吞吐也会下降（无副本分担读请求）

收益：节省约一半存储空间、减少写入时的复制开销

可回滚：改回 1 即可（会触发实际数据复制，有 IO 开销）

如确认可接受无冗余风险，请回复「确认」。
```

### 确认规则细则

1. **逐条确认**：多索引 / 多项变更必须**逐条**展示并确认，不得打包
2. **参数必须完整展开**：所有入参明文列出，不用 `...` 省略
3. **展示内容 = 执行内容**：用户确认后执行的 tool 与参数**必须**与展示完全一致，**禁止**擅自追加或修改。如需调整，**重新走一轮确认**
4. **明确回复才执行**：仅当用户回复 `确认` / `确认执行` / `是` / `执行` / `yes` / `y` 等明确肯定词时执行；含糊回复（"好像可以""看起来 ok"）一律视为**未确认**
5. **重新加载文档**：用户回复确认词时，必须重新 `use_skill("tencent-es-data-panel")` 加载后再执行
6. **只读免确认**：所有 `CesGet*` / `CesList*` / `CesCluster*`（除 `CesClusterReroute`）/ `CesTasks` 可直接调用
7. **变更后必回读**：见 [步骤 6](#步骤-6回读核对生效)

---

## 异常处理指引（流程层）

> tool 层错误码与参数校验失败的处理见 [附录 C](references/ces-tools-reference.md#附录-c通用约定与错误处理)，本表不重复。

| 异常场景 | 处理方式 |
|---------|---------|
| MCP tools 不可用 / 调用报连接错误 | 提示用户在连接器管理页面配置并连接；**禁止**用 `tccli` / `curl` / ES 直连 / 自写签名脚本绕行 |
| 用户未提供集群 ID / 地域 | 引导用户提供（本 Skill 无集群列表能力，`DescribeInstances` 属管控面 Skill） |
| 用户提的 setting 无对应 tool 参数 | 如实告知不支持，说明原因（枚举限制 / 静态 setting / 属 mapping），引导控制台或 Kibana Dev Tools |
| 服务端「要求集群正常状态」阻断（rollover / close） | 如实转述；建议先 `CesClusterHealth` + `CesClusterAllocationExplain` 定位，或交 `tencent-es-diagnose` |
| `CesUpdateClusterSettings` 自动清除了同名 transient 值 | 属预期行为；回读三层并如实说明 transient 已清除、persistent 为目标值及当前生效来源 |
| settings 参数超范围或容量公式不满足被阻断 | 按 §17/§18 的范围与公式重算，展示新参数与影响后**重新走一轮确认**；副本数问题还需核对数据节点数 |
| `RefreshInterval` 小于 `1s` 被拒 | 说明 ES 硬性下限，建议改用 `1s`；若诉求是"立即可查"改用 `CesRefreshIndex` |
| `CesRolloverIndex` 报索引名格式错误 | 说明本 tool 不支持指定目标索引名，改用 `CesUpdateAliases` 手工创建并切换 |
| `CesClusterReroute` 后分片仍未分配 | 根因大概率未真正解决 → 再次 `CesClusterAllocationExplain`，**不要反复刷 reroute** |
| `CesCancelTask` 后任务仍在 | 协作式取消尚未到可中断点，稍后再回读 `CesTasks`，**不要重复调用** |
| `CesCancelTask` 报任务不可取消 | 如实告知 `cancellable: false`，本 Skill 无法取消 |
| 返回体过大 / 上下文截断 | `CesGetNodesStats` 指定 `Module`；只读索引类 tool 用更精确的 `Index` 表达式；`CesGetHotThreads` 减小 `Threads` |
| 用户要求扩容 / 升配 / 重启 / Kibana 相关 | 属管控面 → 引导 `tencent-es-control-panel`，**本 Skill 不执行** |
| 用户要求根因分析 / 监控趋势判读 / 巡检打分 | 属诊断 → 引导 `tencent-es-diagnose` |
| 用户要求 search / bulk / reindex / 改 mapping / 建删索引 | 本 Skill 无对应 tool，如实告知并引导 Kibana Dev Tools |
| 用户取消确认 | 不执行操作，提示可随时重新发起 |
