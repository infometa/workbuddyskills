---
name: tencent-es-data-panel
description: 用于用户要求对腾讯云 ES（Elasticsearch Service）集群执行数据面运维时 —— 查看集群健康 / 节点 / 分片 / 线程池 / 热线程、排查分片未分配与 yellow&red、查看或修改集群 settings（恢复带宽、分片分配开关、磁盘水位）、查看或修改索引 settings（副本数、刷新间隔、translog、解除只读阻塞）、打开或关闭索引、刷新索引、别名切换、索引滚动 rollover、查询与取消 task，以及 tencent-es-diagnose 给出诊断结论后需要在索引 / 分片 / settings 层面落地变更时。不用于集群扩容升配重启等管控面变更，也不用于根因分析。
---

# 腾讯云 ES 数据面运维 Skill

> ⚠️ 本 Skill 直接操作**线上 ES 集群的索引与分片**，写类 MCP tool **一调即下发，无脚本层 dry-run**。根因分析请用 `tencent-es-diagnose`，扩容 / 升配 / 重启请用 `tencent-es-control-panel`。

全部取数与变更通过 **MCP tools** 完成，**零本地脚本、零密钥、零环境变量**。

## ⚠️ 安全铁律

1. **变更前必须二次确认**：展示完整 tool 名 + 全部参数 + 影响，获得用户明确确认。**没有脚本层兜底，Agent 是唯一防线**
2. **变更前必调只读 tool 核对现状**：`CesClusterHealth` 看健康度，改 settings 前先用 `CesGetClusterSettings` / `CesGetIndexInfo(Type=settings)` 读当前值
3. **不做管控面变更**：扩容 / 加节点 / 扩磁盘 / 重启集群或节点 / Kibana 访问 → 全部归 `tencent-es-control-panel`
4. **不做根因分析**：CPU 高 / JVM 高 / 延迟高 / Red 的排查归 `tencent-es-diagnose`（本 Skill 只负责落地变更）
5. **禁止输出密钥**。鉴权由连接器在宿主层完成，Skill 层不存在 SecretId/SecretKey
6. **禁止绕行**：MCP tools 不可用或能力缺失时，**不得**改用 `tccli` / `curl` 云 API / ES 直连 / 自写签名脚本
7. **服务端前置检查被阻断时如实转述**，不重试、不换参数硬闯
8. **不在故障中扩大影响面**：Red / yellow 集群上不做 `State=close`、不做 rollover、不调低副本数

## ⚠️ 强制执行规则

- 执行任何变更前必须 `use_skill("tencent-es-data-panel")` 加载本文档
- 用户回复「确认 / 是 / 执行」等确认词时，**必须重新加载本文档**再执行
- **禁止凭记忆或推测 tool 名与参数** —— 写类 tool 的可改项是**严格枚举**的，必须从 reference 文档核对

## 鉴权模型

鉴权由 MCP 连接器在宿主层完成，本 Skill **不接触任何密钥**，无需环境变量。

**前置检查**：若 MCP tools 不可用（未加载 / 调用报连接错误），提示用户在连接器管理页面配置并连接。

> ℹ️ 所需 CAM 权限：ES 数据面透传相关权限。出现 `AuthFailure` 时让用户联系管理员确认授权。

## MCP Tool 索引

> 🔴 **REQUIRED**：本表**仅为索引，不含完整参数**。调用任何 tool 前，**必须**先读 [`references/ces-tools-reference.md`](references/ces-tools-reference.md) 的对应章节，确认参数枚举、约束与服务端强制前置检查。**禁止**仅凭本表调用。
>
> ⚠️ 所有 tool 均需 `Region` + `InstanceId` 两个必填参数。

### 只读类（诊断取数 / 变更前置核对 / 变更后回读）

| Tool | 能力 | 参数 |
|------|------|------|
| `CesClusterHealth` | 集群健康度、分片分配概览 | [§1](references/ces-tools-reference.md#1-cesclusterhealth集群健康-) |
| `CesGetNode` | 节点列表、角色、负载、内存 / 磁盘 | [§2](references/ces-tools-reference.md#2-cesgetnode节点列表-) |
| `CesGetShards` | 分片分布与状态（含 UNASSIGNED） | [§3](references/ces-tools-reference.md#3-cesgetshards分片分布-) |
| `CesGetAllocation` | 各节点分片数与磁盘水位 | [§4](references/ces-tools-reference.md#4-cesgetallocation节点分片与磁盘-) |
| `CesGetNodesStats` | JVM / GC / 磁盘 / 线程池详细统计 | [§5](references/ces-tools-reference.md#5-cesgetnodesstats节点详细统计-) |
| `CesGetThreadPool` | 线程池 active / queue / **rejected** | [§6](references/ces-tools-reference.md#6-cesgetthreadpool线程池统计-) |
| `CesGetHotThreads` | 热线程（CPU 飙高定位） | [§7](references/ces-tools-reference.md#7-cesgethotthreads热线程-) |
| `CesClusterPendingTasks` | master 待执行队列（变更缓慢排查） | [§8](references/ces-tools-reference.md#8-cesclusterpendingtasksmaster-待执行队列-) |
| `CesClusterAllocationExplain` | **未分配分片根因**（reroute 前必调） | [§9](references/ces-tools-reference.md#9-cesclusterallocationexplain未分配分片根因-) |
| `CesGetClusterSettings` | 集群 settings（含默认值与 transient） | [§10](references/ces-tools-reference.md#10-cesgetclustersettings集群-settings-) |
| `CesListIndices` | index / alias / data_stream 名称与属性 | [§11](references/ces-tools-reference.md#11-ceslistindices索引与别名列表-) |
| `CesCatIndices` | 索引文档数、存储、主副本、健康状态 | [§11A](references/ces-tools-reference.md#11a-cescatindices索引量化明细-) |
| `CesGetRecovery` | 分片恢复进度、速率与剩余量 | [§11B](references/ces-tools-reference.md#11b-cesgetrecovery分片恢复进度-) |
| `CesGetIndexInfo` | 索引 settings / mapping / alias / stats / segments / recovery / count / fielddata | [§12](references/ces-tools-reference.md#12-cesgetindexinfo索引维度信息-) |
| `CesTasks` | 正在执行的 task（取消前必调） | [§14](references/ces-tools-reference.md#14-cestasks正在执行的任务-) |

### 变更类（写操作，必须二次确认）

| Tool | 能力 | 风险 | 参数与前置检查 |
|------|------|------|--------------|
| `CesRefreshIndex` | 强制刷新索引使新数据可搜索 | 低（幂等） | [§15](references/ces-tools-reference.md#15-cesrefreshindex强制刷新索引-) |
| `CesClusterReroute` | 重试被放弃分配的失败分片 | 低（幂等） | [§16](references/ces-tools-reference.md#16-cesclusterreroute重试失败分片-) |
| `CesUpdateClusterSettings` | 集群 settings（**仅 9 项**） | 中 | [§17](references/ces-tools-reference.md#17-cesupdateclustersettings集群-settings-变更-) |
| `CesUpdateIndexSettings` | 索引 settings（**仅 11 项**） | 中 | [§18](references/ces-tools-reference.md#18-cesupdateindexsettings索引-settings-变更-) |
| `CesUpdateAliases` | 别名原子切换 / 新增 / 解除 | 中高（切流量） | [§19](references/ces-tools-reference.md#19-cesupdatealiases别名变更-) |
| `CesRolloverIndex` | 别名滚动（**无条件立即**，支持 DryRun） | 中高 | [§20](references/ces-tools-reference.md#20-cesrolloverindex索引滚动-) |
| `CesUpdateIndexState` | 打开 / **关闭**索引 | open 低 / **close 高** | [§21](references/ces-tools-reference.md#21-cesupdateindexstate索引开关-) |
| `CesCancelTask` | 取消正在执行的 task | **高（不可回滚）** | [§22](references/ces-tools-reference.md#22-cescanceltask取消任务-) |

## 执行顺序（MANDATORY，禁止跳步骤）

```
只读 tool 核对现状（健康度 / 当前值） → 判断是否允许变更 → 展示完整 tool 调用与影响
  → 用户明确确认 → 调用变更 tool → 只读 tool 回读核对生效
```

> 🔴 **REQUIRED**：完整流程图、分场景步骤详解、确认话术模板、异常处理，**执行变更前必读** [`workflow.md`](workflow.md)。

## 六条最高频陷阱

**① 写类 tool 的可改项是严格枚举，不是任意 ES setting。** `CesUpdateClusterSettings` 只认 9 个参数、`CesUpdateIndexSettings` 只认 11 个参数，**不接受原生 setting key**（如 `index.number_of_shards`、`index.blocks.write`、`awareness.*` 等仍无法通过本 Skill 修改）。用户提原生 key 时先映射到 tool 参数，映射不到的如实告知不支持。
→ 完整映射表见 [ces-tools-reference §17](references/ces-tools-reference.md#17-cesupdateclustersettings集群-settings-变更-) / [§18](references/ces-tools-reference.md#18-cesupdateindexsettings索引-settings-变更-)，**必读**。

**② `CesUpdateClusterSettings` 会清除同名 transient 值。** ES 优先级是 transient > persistent；最新 tool 写入 persistent 时会把目标 setting 的同名 transient 项设为 `null`，确保新值立即生效。变更前必须用 `CesGetClusterSettings` 展示 persistent / transient / defaults 三层，并在确认信息中明确告知会清除哪些 transient 覆盖值。

**③ `CesClusterReroute` 不解决根因，直接调用往往无效。** 必须先 `CesClusterHealth` 确认有 unassigned → `CesClusterAllocationExplain` 查明根因 → **先解决根因**（扩磁盘 / 调低副本数 / 调整水位）→ 最后才 reroute。根因未解决时重试仍会失败。
→ 标准四步流程见 [ces-tools-reference §16](references/ces-tools-reference.md#16-cesclusterreroute重试失败分片-)。

**④ 三类操作不可回滚 / 制造不可用，确认话术需加码。** `CesUpdateIndexState(State=close)` 使索引完全不可读写；`CesCancelTask` 已完成部分不回滚（reindex 会留下不完整目标索引）；`NumberOfReplicas=0` 失去全部冗余。这三类必须在确认信息中显著标注风险并要求用户明确确认。
→ 加码话术模板见 [workflow.md 高风险操作确认](workflow.md#高风险操作确认)。

**⑤ 恢复与再均衡参数通常是临时调优。** 调大 `NodeConcurrentRecoveries` / `NodeInitialPrimariesRecoveries` 会放大磁盘 IO、CPU 与网络压力；`RebalanceEnable=none` 会让分片长期不均。确认信息必须写明恢复/维护完成后的回退值，并在变更后主动提醒。

**⑥ 放宽索引与分片限制只是救急，不是根治。** 调大 `MaxShardsPerNode`、`TotalShardsPerNode`、`MappingTotalFieldsLimit`、`MaxResultWindow` 会分别增加 master 元数据、节点热点、字段爆炸或协调节点 OOM 风险；必须先核对现状、采用最小增量，并给出减少分片、优化数据模型或改用 `search_after` 的根治建议。

## 用户意图路由表

| 用户描述 | Tool | 关键提示 |
|---------|------|----------|
| 集群健康状况 / 是不是 yellow、red | `CesClusterHealth` | 看 `unassigned_shards` 决定是否继续排查 |
| 分片为什么没分配 / 为什么 yellow | `CesClusterHealth` → `CesClusterAllocationExplain` | **先看根因再动手** |
| 分片分配失败了、根因已解决但没恢复 | `CesClusterAllocationExplain` → 解决根因 → `CesClusterReroute` → `CesGetRecovery` | 直接 reroute 往往无效；恢复后跟踪进度 |
| 查看分片分布 / 有没有 UNASSIGNED / 分布不均 | `CesGetShards` | 看分片级状态与节点分布 |
| 查看索引大小 / 文档数 / 主副本数 / 是否该 rollover | `CesCatIndices` | 按存储从大到小；真实数据量看 `pri.store.size` |
| 节点磁盘用了多少 / 谁快满了 | `CesGetAllocation` | 配合磁盘水位判断是否触发只读阻塞 |
| 节点列表 / 节点负载 / 有几个数据节点 | `CesGetNode` | 改副本数前用它数数据节点数 |
| JVM 内存高 / GC 频繁 / 磁盘明细 | `CesGetNodesStats` | `Module=jvm` 或 `fs` 减少返回量 |
| 有没有请求被拒 / bulk reject | `CesGetThreadPool` 或 `CesGetNodesStats(Module=thread_pool)` | `rejected > 0` 即队列打满 |
| CPU 飙高在干什么 | `CesGetHotThreads` | 返回纯文本；`Threads` 1~100 |
| 集群变更慢 / master 卡住 | `CesClusterPendingTasks` | 看排队时间与优先级 |
| 查看集群配置 / 恢复带宽是多少 | `CesGetClusterSettings` | 含 persistent / transient / defaults 三层 |
| 有哪些索引 / 别名指向哪个索引 | `CesListIndices` | 支持 `my_index*` / `*my_index` / `*` |
| 查看索引副本数 / 刷新间隔 / 分片数 | `CesGetIndexInfo(Type=settings)` | `Index` 与 `Type` 必填，支持通配 |
| 查看字段类型 / 分词器 | `CesGetIndexInfo(Type=mapping)` | 支持通配；字段多时尽量精确索引名 |
| 查看索引大小 / 文档数 / 段 / 恢复 / fielddata | `CesGetIndexInfo(Type=stats/segments/recovery/fielddata)` | 按目的选择单个 `Type`，大返回值避免 `Index="*"` |
| 有什么任务在跑 / reindex 到哪了 | `CesTasks` | 取消任务前必调，用于拿 `TaskId` |
| **加快 / 减慢分片恢复速度** | `CesUpdateClusterSettings(RecoveryMaxBytesPerSec / NodeConcurrentRecoveries)` | 调大占 IO/网络，恢复完成后建议回退 |
| **调整节点重启后的本地主分片恢复并发** | `CesUpdateClusterSettings(NodeInitialPrimariesRecoveries)` | 1..30；调大增加节点磁盘 IO/CPU 压力 |
| **暂停 / 放开分片分配**（滚动运维窗口） | `CesUpdateClusterSettings(AllocationEnable)` | ⚠️ 设 `none`/`primaries` 后**必须改回 `all`** |
| **暂停 / 放开分片再均衡** | `CesUpdateClusterSettings(RebalanceEnable)` | `none` 仅停再均衡，不阻止新分片分配；完成后改回 `all` |
| **调整磁盘水位** | `CesUpdateClusterSettings(DiskWatermark*)` | 三档必须统一单位且 `low < high < flood` |
| **放宽集群总分片上限** | `CesUpdateClusterSettings(MaxShardsPerNode)` | 1..10000；仅救急，根治应减少分片或扩节点 |
| **改副本数** | `CesUpdateIndexSettings(NumberOfReplicas)` | 0..5，且 ≤「数据节点数-1」；`0` 需警告失去冗余 |
| **改刷新间隔 / 导入期关闭刷新** | `CesUpdateIndexSettings(RefreshInterval)` | 最小 `1s`；`-1` 关闭，**导入完须改回** |
| **索引变只读了 / 写不进去 / 磁盘满导致阻塞** | 先腾空间 → `CesUpdateIndexSettings(ReadOnlyAllowDelete)` | 只支持**解除**（`false` / `null`）；不腾空间会被 ES 重新加上 |
| **提升写入吞吐 / translog 调优** | `CesUpdateIndexSettings(TranslogDurability / SyncInterval / FlushThresholdSize)` | `async` 有丢数据窗口，须明确告知 |
| **节点短暂离线时延迟重分配** | `CesUpdateIndexSettings(DelayedTimeout)` | 最大 24h；滚动维护后应恢复原值，避免故障时延迟恢复 |
| **提高核心索引恢复优先级** | `CesUpdateIndexSettings(IndexPriority)` | 0..1000；避免所有索引都设高优先级 |
| **放宽深分页上限** | `CesUpdateIndexSettings(MaxResultWindow)` | 1000..100000；超过 5 万 OOM 风险高，优先 `search_after` |
| **放宽 mapping 字段上限** | `CesUpdateIndexSettings(MappingTotalFieldsLimit)` | 300..3000；仅字段爆炸救急，根治应优化数据模型 |
| **放宽单节点该索引分片上限** | `CesUpdateIndexSettings(TotalShardsPerNode)` | 500..10000；需满足容量公式，防止分片持续未分配 |
| **数据写进去了但查不到** | `CesRefreshIndex` | 先确认不是 `RefreshInterval=-1` 导致 |
| **别名切到新索引 / 零停机切流量** | `CesUpdateAliases(AddIndex + RemoveIndex)` | 同传即原子切换（remove 先于 add） |
| **删除别名对某索引的指向** | `CesUpdateAliases(RemoveIndex)` | 这是**唯一能删别名的途径** |
| **日志索引太大了，滚动一下** | `CesRolloverIndex(DryRun=true)` → 确认 → 实际执行 | 无条件立即滚动；索引名须形如 `xxx-000001` |
| **打开被关闭的索引** | `CesUpdateIndexState(State=open)` | 低风险；会触发分片恢复 |
| **关闭索引释放内存 / 归档历史索引** | `CesUpdateIndexState(State=close)` | 🔴 高风险，索引完全不可读写；要求集群正常态 |
| **有个任务失控了，杀掉它** | `CesTasks` → `CesCancelTask(TaskId)` | 🔴 协作式取消，**已完成部分不回滚** |

## 能力边界

- ❌ 不做管控面变更（扩容 / 加节点 / 扩磁盘 / 重启集群或节点 / 重启 Kibana / Kibana 访问与白名单）→ `tencent-es-control-panel`
- ❌ 不做根因分析、监控趋势判读、批量巡检打分 → `tencent-es-diagnose`
- ❌ 不做数据读写（search / bulk / reindex / delete_by_query）与 mapping 变更
- ❌ 不做索引创建与删除、`number_of_shards` 变更（静态 setting，需 shrink / split / reindex）
- ❌ 不支持手工指定分片移动（`move` / `allocate_replica`）；`allocate_stale_primary` / `allocate_empty_primary` 等数据丢失类操作**永久禁止**
- ⚠️ 写类 tool 的可改项为**严格枚举**，超出范围的 setting 一律如实告知不支持并引导控制台 / Kibana Dev Tools
- ⚠️ 部分 tool 有服务端强制前置检查（`CesRolloverIndex`、`CesUpdateIndexState(close)` 要求集群正常态），被阻断时不绕行

### Skill 协作关系

```
tencent-es-diagnose（诊断 / 根因分析 / 监控巡检）
    │ 结论：索引 / 分片 / settings 级问题
    ▼
tencent-es-data-panel（数据面运维 / 索引与分片变更）  ← 本 Skill
    │ 结论：节点 / 集群资源不足
    ▼
tencent-es-control-panel（管控面：扩容 / 升配 / 重启）
```

> 三个 Skill 共用同一套 MCP tools。本 Skill 只做「数据面只读核对 + 索引与分片层变更 + 变更后回读」。

## Anti-Patterns

❌ **用原生 ES setting key 当 tool 参数传** → 写类 tool 只认枚举参数名，必须先映射；映射不到就如实说不支持
❌ **未获得用户确认就调用写类 tool** → 无脚本层兜底、无 dry-run，一调即真，Agent 是唯一防线
❌ **MCP tools 不可用时改用 `tccli` / `curl` 云 API / ES 直连绕行** → 绕过了服务端强制安全前置检查，等于放弃全部保护
❌ **不看 `CesClusterAllocationExplain` 就直接 `CesClusterReroute`** → 根因未解决，重试必然再失败，白白刷一轮
❌ **忽略 `CesUpdateClusterSettings` 会清除同名 transient 值** → 这会改变实际生效配置来源；必须在确认信息中展示将被清除的 transient 覆盖值，并在变更后回读三层结果
❌ **`AllocationEnable` 设为 `none` / `primaries` 后忘记改回 `all`** → 分片长期无法分配，集群持续 yellow / red
❌ **`RefreshInterval=-1` 导入完忘记改回** → 业务永久查不到新数据
❌ **在批量写入循环中反复 `CesRefreshIndex`** → 小 segment 暴增，merge 压力拖慢集群
❌ **不数数据节点数就设 `NumberOfReplicas`** → 超过「数据节点数-1」会有副本分片永远无法分配，集群变 yellow
❌ **`CesRolloverIndex` 不先 `DryRun=true` 预演** → 索引名不符合数字后缀格式时才发现报错，且无法指定目标索引名
❌ **把 `State=close` 当成"减负优化"随手执行** → 这是制造不可用，必须确认业务已不再访问该索引
❌ **`CesCancelTask` 后不做后续清理提示** → reindex 被取消会留下数据不完整的目标索引，需人工清理或重跑
❌ **对未实际看到的 tool 返回做猜测性描述** → 结果必须基于真实返回，禁止凭空推测

## References

**🔴 以下文档为强制阅读项，不是「延伸阅读」：**

| 文档 | 何时**必读** |
|------|------------|
| [`references/ces-tools-reference.md`](references/ces-tools-reference.md) | **调用任何 tool 前** —— 完整参数枚举、取值约束、服务端前置检查、返回判读。本 Skill 中 tool 参数的**唯一权威来源** |
| [`workflow.md`](workflow.md) | **执行任何变更前** —— 流程图、分场景步骤、确认话术模板、异常处理 |
