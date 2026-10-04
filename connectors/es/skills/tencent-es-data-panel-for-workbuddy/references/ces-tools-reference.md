# CES 数据面 MCP Tool 详细参考（Ces Tools Reference）

> 🔴 **本文档是 tool 参数、取值约束、服务端前置检查、返回判读的唯一权威来源（SSOT）**。SKILL.md 只有索引，`workflow.md` 只有流程与话术 —— 参数语义以本文档为准，冲突时以本文档为准。
>
> **调用任何 tool 前必须读完对应章节**，禁止凭索引或记忆调用。
>
> 鉴权在宿主层由 MCP 连接器完成，本 Skill 不接触密钥。
>
> ⚠️ **所有 tool 均需 `Region`（如 `ap-guangzhou`）+ `InstanceId`（如 `es-xxxxxxxx`）两个必填参数**，以下各节表格中不再重复列出。

## 目录

**只读类**

1. [CesClusterHealth（集群健康）](#1-cesclusterhealth集群健康-)
2. [CesGetNode（节点列表）](#2-cesgetnode节点列表-)
3. [CesGetShards（分片分布）](#3-cesgetshards分片分布-)
4. [CesGetAllocation（节点分片与磁盘）](#4-cesgetallocation节点分片与磁盘-)
5. [CesGetNodesStats（节点详细统计）](#5-cesgetnodesstats节点详细统计-)
6. [CesGetThreadPool（线程池统计）](#6-cesgetthreadpool线程池统计-)
7. [CesGetHotThreads（热线程）](#7-cesgethotthreads热线程-)
8. [CesClusterPendingTasks（master 待执行队列）](#8-cesclusterpendingtasksmaster-待执行队列-)
9. [CesClusterAllocationExplain（未分配分片根因）](#9-cesclusterallocationexplain未分配分片根因-)
10. [CesGetClusterSettings（集群 settings）](#10-cesgetclustersettings集群-settings-)
11. [CesListIndices（索引与别名列表）](#11-ceslistindices索引与别名列表-)
11A. [CesCatIndices（索引量化明细）](#11a-cescatindices索引量化明细-)
11B. [CesGetRecovery（分片恢复进度）](#11b-cesgetrecovery分片恢复进度-)
12. [CesGetIndexInfo（索引维度信息）](#12-cesgetindexinfo索引维度信息-)
13. [淘汰工具迁移说明](#13-淘汰工具迁移说明)
14. [CesTasks（正在执行的任务）](#14-cestasks正在执行的任务-)

**变更类**

15. [CesRefreshIndex（强制刷新索引）](#15-cesrefreshindex强制刷新索引-)
16. [CesClusterReroute（重试失败分片）](#16-cesclusterreroute重试失败分片-)
17. [CesUpdateClusterSettings（集群 settings 变更）](#17-cesupdateclustersettings集群-settings-变更-)
18. [CesUpdateIndexSettings（索引 settings 变更）](#18-cesupdateindexsettings索引-settings-变更-)
19. [CesUpdateAliases（别名变更）](#19-cesupdatealiases别名变更-)
20. [CesRolloverIndex（索引滚动）](#20-cesrolloverindex索引滚动-)
21. [CesUpdateIndexState（索引开关）](#21-cesupdateindexstate索引开关-)
22. [CesCancelTask（取消任务）](#22-cescanceltask取消任务-)

**附录**

- [索引 / 别名命名约束（全局通用）](#附录-a索引--别名命名约束全局通用)
- [服务端前置检查一览](#附录-b服务端前置检查一览)
- [通用约定与错误处理](#附录-c通用约定与错误处理)

---

## 1. CesClusterHealth（集群健康）🩺

- **类型**：只读
- **底层**：`_cluster/health`
- **定位**：**排查与变更的第一个 tool**，判断集群能否安全变更

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

```
CesClusterHealth(Region="ap-guangzhou", InstanceId="es-xxxxxxxx")
```

### 关键返回字段判读

| 字段 | 判读 |
|------|------|
| `status` | `green` 全部分片正常；`yellow` 有副本分片未分配；`red` **有主分片未分配，已丢失可用性** |
| `unassigned_shards` | `> 0` 时进入 [§9 `CesClusterAllocationExplain`](#9-cesclusterallocationexplain未分配分片根因-) 查根因 |
| `initializing_shards` / `relocating_shards` | `> 0` 表示正在恢复 / 搬迁中，此时**不要**叠加 rollover、close 等操作 |
| `number_of_data_nodes` | **设 `NumberOfReplicas` 的上限依据**（见 [§18](#18-cesupdateindexsettings索引-settings-变更-)） |
| `number_of_pending_tasks` | 偏大时进入 [§8](#8-cesclusterpendingtasksmaster-待执行队列-) 看 master 队列 |

> 📌 **变更后回读**：`CesClusterReroute`、`CesUpdateIndexState(open)`、改副本数后都应回读本 tool 观察分片是否开始分配。

---

## 2. CesGetNode（节点列表）🖥️

- **类型**：只读
- **底层**：`_cat/nodes`
- **用途**：查看节点列表、角色、负载、内存 / 磁盘使用

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

> 💡 用于确认数据节点数量与角色分布；改副本数的上限也可从这里核对（与 `CesClusterHealth.number_of_data_nodes` 交叉验证）。

---

## 3. CesGetShards（分片分布）🧩

- **类型**：只读
- **底层**：`_cat/shards`
- **用途**：查看各索引分片在节点上的分布、主 / 副本、状态、文档数与大小

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数，**不支持按索引过滤**（返回全量分片，大集群注意上下文体积） |

### 典型用途

| 场景 | 看什么 |
|------|-------|
| 排查未分配分片 | `state` 列中的 `UNASSIGNED`，配合 `prirep`（`p` 主 / `r` 副）判断严重程度 |
| 分布不均 | 各 `node` 上的分片数量差异 |
| 辅助查看分片级大小 | `docs` / `store` 列；判断索引整体大小与 rollover 时机优先用 [§11A `CesCatIndices`](#11a-cescatindices索引量化明细-) |
| 变更后回读 | `UNASSIGNED` 是否减少、是否转为 `INITIALIZING` |

---

## 4. CesGetAllocation（节点分片与磁盘）💾

- **类型**：只读
- **底层**：`_cat/allocation`
- **用途**：查看每个节点的分片数、磁盘已用 / 可用 / 总量、磁盘使用百分比

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

> 🔴 **调整磁盘水位前必调**（[§17](#17-cesupdateclustersettings集群-settings-变更-)）：需要知道当前实际使用率才能判断新水位是否合理。
> 🔴 **解除只读阻塞前必调**（[§18](#18-cesupdateindexsettings索引-settings-变更-) `ReadOnlyAllowDelete`）：确认磁盘空间**已经腾出**，否则 ES 会立刻重新加上阻塞。

---

## 5. CesGetNodesStats（节点详细统计）📊

- **类型**：只读
- **底层**：`_nodes/stats`
- **用途**：JVM 堆内存 / GC、文件系统磁盘、线程池等详细运行指标

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Module` | ❌ | 统计子模块：`all`（默认，**量最大**）/ `jvm` / `fs` / `thread_pool` |

> ⚠️ **不传 `Module` 会返回全量统计**，大集群极易撑爆上下文。**按需指定子模块**：
> - JVM 内存高 / GC 频繁 → `Module="jvm"`
> - 磁盘明细 → `Module="fs"`
> - 线程池 → `Module="thread_pool"`（或用更精简的 [§6](#6-cesgetthreadpool线程池统计-)）

---

## 6. CesGetThreadPool（线程池统计）🧵

- **类型**：只读
- **底层**：`_cat/thread_pool?v&format=json`
- **用途**：查看 `bulk` / `search` / `write` / `get` 等线程池的 `active` / `queue` / `rejected`

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

### 判读

| 现象 | 含义 |
|------|------|
| `rejected > 0` | **队列已满，有请求被拒绝** —— 写入 / 查询侧会报错，是最直接的过载证据 |
| `queue` 持续接近上限 | 处理能力不足，即将开始 reject |
| `active` 长期打满 | 线程池饱和 |

> 📌 `rejected` 是**累计值**（自节点启动），需两次采样对比增量才能判断"当前是否还在 reject"。

---

## 7. CesGetHotThreads（热线程）🔥

- **类型**：只读
- **底层**：`_nodes/hot_threads`
- **用途**：CPU 飙高时定位具体耗时操作
- **返回**：⚠️ **纯文本（非 JSON）**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Threads` | ❌ | 抓取的线程数量，**取值 1~100**，不传取 ES 默认值 |
| `Interval` | ❌ | 采样间隔，如 `2s` / `500ms` / `1m`，不传取 ES 默认值 |

```
CesGetHotThreads(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", Threads=3, Interval="2s")
```

> 💡 输出较长，建议 `Threads` 取 3~5 控制体积。判读时关注栈顶方法（`search`、`merge`、`bulk`、`GC` 等）。
> ℹ️ 本 tool 属定位类，深度根因分析归 `tencent-es-diagnose`。

---

## 8. CesClusterPendingTasks（master 待执行队列）⏳

- **类型**：只读
- **底层**：`_cluster/pending_tasks`
- **用途**：查看 master 尚未处理的任务（mapping 更新、分片分配等）及排队时间与优先级

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

> 💡 **集群变更缓慢 / settings 改完迟迟不生效**时用它排查：队列长、`time_in_queue` 大说明 master 繁忙。
> ⚠️ master 繁忙时**不要**叠加更多变更操作（rollover、批量改 settings），会进一步排长队列。

---

## 9. CesClusterAllocationExplain（未分配分片根因）🔍

- **类型**：只读
- **底层**：`_cluster/allocation/explain`
- **定位**：🔴 **`CesClusterReroute` 前的强制前置步骤**

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数（**不支持指定索引 / 分片**，由 ES 自动挑一个未分配分片解释） |

### 常见根因与对应处置

| 根因 | 处置 |
|------|------|
| 磁盘超过水位（`disk watermark`） | 腾空间 / `CesUpdateClusterSettings` 调水位 / 交给 `tencent-es-control-panel` 扩磁盘 |
| 节点数不足以满足副本数 | `CesUpdateIndexSettings(NumberOfReplicas)` 调低，或加节点（管控面） |
| 分片感知规则冲突（awareness / filter） | 本 Skill 无法修改该类 setting，如实告知并引导控制台 / Dev Tools |
| 分配重试次数达上限（`max_retry`） | 根因解决后调 [§16 `CesClusterReroute`](#16-cesclusterreroute重试失败分片-) |

> ℹ️ 集群健康（无未分配分片）时，ES 返回类似 `unable to find any unassigned shards to explain` —— **属正常情况**，不是错误，如实告知用户"当前无未分配分片"即可。

---

## 10. CesGetClusterSettings（集群 settings）⚙️

- **类型**：只读
- **底层**：`_cluster/settings?include_defaults=true`
- **定位**：🔴 **`CesUpdateClusterSettings` 前的强制前置步骤**

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数 |

### 🔴 关键：三层优先级

返回含 `persistent` / `transient` / `defaults` 三层，**ES 生效优先级：`transient` > `persistent` > `defaults`**。

> ⚠️ [§17](#17-cesupdateclustersettings集群-settings-变更-) 将新值写入 `persistent` 层，并会把本次目标 setting 的**同名 transient 项自动清除为 `null`**，确保新值立即生效。因此改前必须检查并展示三层当前值：
> - `transient` 有同名值 → 确认信息必须明确告知该覆盖值将被清除，不能把它当作无副作用的普通 persistent 写入
> - `transient` 无同名值 → 正常写入 persistent

> 💡 磁盘水位只传部分档位时，服务端会读当前生效值一起做 `low < high < flood_stage` 校验 —— 先看清当前三档值再决定要传几个。

---

## 11. CesListIndices（索引与别名列表）📇

- **类型**：只读
- **底层**：`_resolve/index/<Index>`
- **用途**：列出匹配的 **index / alias / data_stream**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ❌ | 索引表达式，**不传默认 `*`（全部）**。支持精确名 `my_index`、后缀通配 `my_index*`、前缀通配 `*my_index`、全部 `*`。命名约束见 [附录 A](#附录-a索引--别名命名约束全局通用) |

```
CesListIndices(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", Index="logs-*")
```

### 变更前必调场景

| 即将执行 | 用本 tool 确认什么 |
|---------|------------------|
| `CesUpdateIndexState` | 索引当前 `status` 是 `open` 还是 `close`（避免无意义调用） |
| `CesUpdateAliases` | 别名**当前指向哪个索引**（算 `RemoveIndex` 的依据） |
| `CesRolloverIndex` | 别名是否**恰好指向一个**索引、索引名是否符合 `xxx-000001` 数字后缀格式 |
| `CesUpdateIndexSettings` / `CesRefreshIndex` | 索引完整名称是否存在（写类 tool 禁止通配） |

> ⚠️ 不传 `Index` 时返回全部索引，索引数量多的集群注意上下文体积，尽量带上通配前缀。
> ⚠️ 本 tool **不含**文档数、存储量、主/副本数等量化列；要判断索引大小或 rollover 时机，必须用下方 `CesCatIndices`。

---

## 11A. CesCatIndices（索引量化明细）📊

- **类型**：只读
- **底层**：`_cat/indices`
- **用途**：按存储占用从大到小查看索引文档数、存储、主/副本分片数、健康状态和开关状态

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ❌ | 索引表达式；不传返回全部索引，支持精确名与通配 |

- `store.size`：包含副本放大的总占用
- `pri.store.size`：仅主分片占用，估算真实数据量应看此列
- `pri` / `rep`：主分片数 / 副本数；`docs.count`：文档数

> 🔴 与 `CesListIndices` 分工：看 index / alias / data_stream 名称与关系用 `CesListIndices`；看索引大小、文档数、主副本和健康状态用 `CesCatIndices`。

---

## 11B. CesGetRecovery（分片恢复进度）⏱️

- **类型**：只读
- **底层**：`_cat/recovery`
- **用途**：观察恢复是否推进、单个分片恢复百分比、速率、源/目标节点和剩余量

| 参数 | 必需 | 说明 |
|------|-----|------|
| `ActiveOnly` | ❌ | 默认 `true`，仅返回进行中恢复；`false` 返回全部历史，⚠️ 大集群可能产生数万行 |

> `ActiveOnly=true` 返回空数组 `[]` 是正常结果，表示当前没有进行中的恢复。以下操作后应调用本 tool：`CesUpdateIndexState(State=open)`、`CesClusterReroute`、调大 `NumberOfReplicas`、节点重启/故障恢复。
> 恢复过慢时，可在确认风险后调整 `RecoveryMaxBytesPerSec` / `NodeConcurrentRecoveries`，或用 `IndexPriority` 提高核心索引优先级。

---

## 12. CesGetIndexInfo（索引维度信息）📄

- **类型**：只读
- **底层**：由 `Type` 决定（`<Index>/_mapping`、`_settings`、`_stats` 等）
- **定位**：索引维度只读信息的统一入口；🔴 **`CesUpdateIndexSettings` 前必须用 `Type="settings"` 读当前值**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ✅ | 索引表达式，支持 `my_index` / `my_index*` / `*my_index` / `*`。命名约束见 [附录 A](#附录-a索引--别名命名约束全局通用) |
| `Type` | ✅ | 仅允许 `mapping` / `settings` / `alias` / `stats` / `segments` / `recovery` / `count` / `fielddata` / `cat_segments` |

| `Type` | 底层接口 | 典型用途与判读 |
|--------|---------|---------------|
| `settings` | `<Index>/_settings?include_defaults=true` | 变更前后读 `number_of_replicas`、`refresh_interval`、`blocks.read_only_allow_delete`、`translog.*`、本节新增 5 项 setting 的当前值 |
| `mapping` | `<Index>/_mapping?include_defaults=true` | 字段定义、类型、分词器；mapping 变更仍不受本 Skill 支持，通常需 reindex |
| `alias` | `<Index>/_alias` | 查看该索引绑定的别名 |
| `stats` | `<Index>/_stats` | 文档数、存储、段、refresh / merge 等索引级统计 |
| `segments` | `<Index>/_segments` | Lucene 段原始信息 |
| `recovery` | `<Index>/_recovery` | 节点重启、打开索引、调副本数后查看目标索引分片恢复进度 |
| `count` | `<Index>/_count` | 索引全量文档数；不支持附带查询条件 |
| `fielddata` | `<Index>/_stats/fielddata?fields=*` | 定位具体字段的 fielddata 内存膨胀 |
| `cat_segments` | `_cat/segments/<Index>` | 判断段数过多、未 merge，辅助 refresh / merge 调优 |

```
# 索引 settings 变更前读取当前值
CesGetIndexInfo(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                Index="my_index", Type="settings")
```

> ⚠️ `mapping` / `stats` / `segments` / `fielddata` 可能返回大量内容，字段或索引很多时应尽量指定精确 `Index`，避免 `*` 全量查询。

---

## 13. 淘汰工具迁移说明

- `CesGetIndexSetting` 已淘汰 → 改用 `CesGetIndexInfo(Type="settings")`
- `CesGetIndexMapping` 已淘汰 → 改用 `CesGetIndexInfo(Type="mapping")`
- 新工具的 `Index` 与 `Type` 都是必填参数；禁止继续调用旧工具名

---

## 14. CesTasks（正在执行的任务）📋

- **类型**：只读
- **底层**：`_tasks`
- **定位**：🔴 **`CesCancelTask` 前的强制前置步骤**（用于获取 `TaskId`）

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | 无额外参数（**不支持按 action 过滤**，返回全部任务） |

### 判读

| 字段 | 用途 |
|------|------|
| `task_id`（形如 `oTUltX4IQMOUUVeiohTt8A:12345`） | **`CesCancelTask` 的 `TaskId` 入参来源** |
| `action` | 任务类型：`indices:data/write/reindex`、`delete_by_query`、`update_by_query`、`forcemerge`、`search` 等 |
| `running_time` / `running_time_in_nanos` | **判断是否异常**（远超预期即候选取消对象） |
| `cancellable` | `false` 表示**不可取消**，对其调用 `CesCancelTask` 会报错 |

> 📌 **取消后回读**：再调本 tool 确认任务是否已消失（ES 取消是协作式的，不会立即生效）。

---

## 15. CesRefreshIndex（强制刷新索引）🔄

- **类型**：**写**（风险低：幂等、可自愈）
- **底层**：`POST <Index>/_refresh`
- **用途**：使刚写入的数据立即可被搜索

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ✅ | **单个索引的完整名称**。🚫 禁止通配符 `*`、禁止 `_all`、禁止以 `.` `_` `-` `+` 开头（保护系统索引） |

```
CesRefreshIndex(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", Index="my_index")
```

### 典型场景

1. **"数据写进去了但查不到"** —— ES 默认每 1s 才自动刷新，刷新前新文档对搜索不可见，这是最常见的"误判为写入失败"
2. **批量导入完成后立即可查** —— 若导入期把 `RefreshInterval` 设成了 `-1`，**正确顺序**是：先用 [§18](#18-cesupdateindexsettings索引-settings-变更-) 把 `RefreshInterval` 改回正常值，**再**调本 tool 刷新一次

### 返回判读

`_shards`：`total` / `successful` / `failed` —— 表示多少分片完成刷新。

> ⚠️ **不要在批量写入循环中反复调用**：每次刷新生成新 segment，频繁刷新造成小 segment 暴增、加重后台 merge 压力并拖慢集群。
> ✅ **不要求集群处于正常状态** —— 排查数据可见性问题时往往正需要它。

---

## 16. CesClusterReroute（重试失败分片）♻️

- **类型**：**写**（风险低：幂等）
- **底层**：`POST _cluster/reroute?retry_failed=true`
- **用途**：分片分配连续失败达上限（ES 默认 5 次）后 ES 会放弃自动重试，**即使根因已解决分片也不会自动恢复**，必须手动触发

| 参数 | 必需 | 说明 |
|------|-----|------|
| （仅 `Region` / `InstanceId`） | ✅ | **无任何额外参数**，URI 固定 |

### 🔴 正确使用顺序（直接调用往往无效）

```
① CesClusterHealth              → 确认确实 yellow/red 且 unassigned_shards > 0
② CesClusterAllocationExplain   → 查明无法分配的【根本原因】
③ 先解决根本原因：
     磁盘超水位   → CesUpdateClusterSettings 调水位 / 交管控面扩磁盘
     副本数过高   → CesUpdateIndexSettings(NumberOfReplicas) 调低
     感知规则冲突 → 本 Skill 不支持，如实告知
④ CesClusterReroute                → 触发重试
⑤ CesClusterHealth / CesGetShards  → 观察分片是否开始分配
⑥ CesGetRecovery(ActiveOnly=true)  → 跟踪恢复百分比、速率与剩余量
```

> 🚫 **根因未解决就调用，重试仍会失败** —— 不要跳过 ②③ 直接刷 ④。

### 安全限制（服务端硬性）

- 🚫 **不支持手工指定分片移动**：ES 原生 reroute 的 `move` / `cancel` / `allocate_replica` 等 commands **均未开放**（这类操作需精确节点与分片编号，填错会造成分片错位）
- 🚫 `allocate_stale_primary` / `allocate_empty_primary`（数据丢失类）**永久禁止**

> ✅ **幂等**：当前无失败分片时调用同样返回成功（`acknowledged: true`），无副作用。
> ✅ **不要求集群处于正常状态** —— 本 tool 专用于 yellow / red 异常场景。

---

## 17. CesUpdateClusterSettings（集群 settings 变更）⚙️✍️

- **类型**：**写**（风险中）
- **底层**：`PUT _cluster/settings`
- **定位**：**ES 集群级别的 settings 变更都用这个 tool**

### 🔴 仅支持下列 9 项，不在列表中的设置无法通过本 tool 修改

| tool 参数 | 映射的 ES setting | 取值格式 | 风险提示 |
|-----------|------------------|---------|---------|
| `RecoveryMaxBytesPerSec` | `indices.recovery.max_bytes_per_sec` | 数字+单位（`b`/`kb`/`mb`/`gb`），如 `40mb`、`100mb` | 调大会占用更多网络与磁盘 IO，恢复完成后建议回退 |
| `AllocationEnable` | `cluster.routing.allocation.enable` | `all` / `primaries` / `new_primaries` / `none` | `none`/`primaries` 为临时值，完成后必须改回 `all` |
| `DiskWatermarkLow` | `cluster.routing.allocation.disk.watermark.low` | 百分比 `85%`（已用占比）或绝对容量 `100gb`（剩余可用） | 调高水位可能让磁盘逼近写满，只能短期救急 |
| `DiskWatermarkHigh` | `cluster.routing.allocation.disk.watermark.high` | 同上 | 同上 |
| `DiskWatermarkFloodStage` | `cluster.routing.allocation.disk.watermark.flood_stage` | 同上 | 同上 |
| `NodeConcurrentRecoveries` | `cluster.routing.allocation.node_concurrent_recoveries` | 整数 **1..20**（ES 默认 2） | 调大会同时增加恢复 IO、CPU 与网络压力；恢复完成后建议改回 2 |
| `NodeInitialPrimariesRecoveries` | `cluster.routing.allocation.node_initial_primaries_recoveries` | 整数 **1..30**（ES 默认 4） | 仅影响节点重启后的本地主分片初始恢复；调大会增加节点磁盘 IO/CPU 压力 |
| `RebalanceEnable` | `cluster.routing.rebalance.enable` | `all` / `primaries` / `replicas` / `none` | `none` 只停止已分配分片的再均衡，不阻止新分片分配；完成后必须改回 `all` |
| `MaxShardsPerNode` | `cluster.max_shards_per_node` | 整数 **1..10000**，要求 ES 7.0+ | 调大仅为分片上限救急，会增加 master 元数据与集群状态开销；根治应减少分片或扩节点 |

> ⚠️ **用户提到的原生 key 若不在上表，一律如实告知不支持**。常见不支持项：`cluster.routing.allocation.cluster_concurrent_rebalance`、`awareness.*`、各类 `allocation.filter.*`。

### 🔴 关键陷阱一：会清除同名 transient 覆盖值

本 tool 把新值写入 `persistent` 层。由于 ES 优先级为 `transient > persistent > defaults`，服务端会把本次目标 setting 的**同名 transient 项自动设为 `null`**，确保新值立即生效：

- 改前必须用 [§10 `CesGetClusterSettings`](#10-cesgetclustersettings集群-settings-) 读取三层当前值
- 若 transient 有同名值，确认信息必须展示「旧 transient 值 → 清除」及「persistent 当前值 → 目标值」
- 变更后回读三层，确认 transient 已清除且 persistent 为目标值

### 🔴 关键陷阱二：磁盘水位三档必须统一单位且有序

- 用**百分比**时：`low < high < flood_stage`（如 `85% < 90% < 95%`）
- 用**绝对容量**（剩余可用空间）时：**反向** `low > high > flood_stage`（如 `100gb > 50gb > 20gb`）
- **三档必须统一单位**，不可混用百分比与绝对容量
- 只传部分档位时，服务端会**读取当前生效值一起校验** → 必须先看清当前三档值

### 🔴 关键陷阱三：临时开关与恢复参数必须收尾

- `AllocationEnable=none/primaries`：运维完成后必须改回 `all`，否则分片长期无法分配
- `RebalanceEnable=none/primaries/replicas`：临时操作完成后必须改回 `all`，否则分片可能长期分布不均
- 调大的 `RecoveryMaxBytesPerSec` / `NodeConcurrentRecoveries` / `NodeInitialPrimariesRecoveries`：恢复完成后建议回退原值，避免长期资源争抢

### 其他约束

- 上述参数**至少要传 1 个**，未传的参数不会被改动
- `MaxShardsPerNode` 仅支持 ES 7.0+，低版本会被服务端阻断
- ✅ **不要求集群处于正常状态** —— 集群异常或变更卡住时同样可调用

```
# 同时提高恢复带宽和并发（⚠️ 恢复完成后建议回退）
CesUpdateClusterSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                         RecoveryMaxBytesPerSec="100mb", NodeConcurrentRecoveries=4)

# 运维窗口停止再均衡（⚠️ 完成后必须改回 all）
CesUpdateClusterSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                         RebalanceEnable="none")

# 调整三档水位（统一百分比，low < high < flood）
CesUpdateClusterSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                         DiskWatermarkLow="85%", DiskWatermarkHigh="90%",
                         DiskWatermarkFloodStage="95%")
```

---

## 18. CesUpdateIndexSettings（索引 settings 变更）📄✍️

- **类型**：**写**（风险中）
- **底层**：`PUT <Index>/_settings`
- **定位**：**ES 索引级别的 settings 变更都用这个 tool**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ✅ | **单个索引的完整名称**。🚫 禁止通配符 `*`、禁止 `_all`、禁止以 `.` `_` `-` `+` 开头 |

### 🔴 仅支持下列 11 项动态 setting

| tool 参数 | 映射的 ES setting | 取值 | 风险提示 |
|-----------|------------------|------|---------|
| `NumberOfReplicas` | `index.number_of_replicas` | 数字 **0..5** | `0` **失去冗余（节点故障即丢数据）**；不得超过「数据节点数-1」；**变更会触发实际数据复制** |
| `RefreshInterval` | `index.refresh_interval` | 数字+单位（`ms`/`s`/`m`/`h`），如 `1s`/`30s`/`5m`；特殊值 `-1` 关闭自动刷新 | **最小允许 `1s`**；`-1` **导入完必须改回**，否则业务长期查不到新数据 |
| `TranslogDurability` | `index.translog.durability` | `request` / `async` | `async` **节点异常宕机时会丢失最后一个周期内的数据**，改前必须确认业务可接受该窗口 |
| `TranslogSyncInterval` | `index.translog.sync_interval` | 数字+单位（`ms`/`s`/`m`），如 `5s` | **仅在 `TranslogDurability=async` 时生效**；不得小于 **100ms** |
| `TranslogFlushThresholdSize` | `index.translog.flush_threshold_size` | 数字+单位（`b`/`kb`/`mb`/`gb`），如 `512mb` | 调大可减少 flush，但会**拉长节点重启后的恢复时间** |
| `ReadOnlyAllowDelete` | `index.blocks.read_only_allow_delete` | 只支持解除：`false` / `null` | 🚫 不支持 `true`；必须**先腾出磁盘空间再解除**，否则 ES 会重新加上 |
| `DelayedTimeout` | `index.unassigned.node_left.delayed_timeout` | 数字+单位（`ms`/`s`/`m`/`h`），最大 **24h** | 滚动重启前调大可避免无谓搬迁；维护后应恢复原值，否则真实故障时会延迟副本恢复 |
| `IndexPriority` | `index.priority` | 整数 **0..1000** | 值越大恢复越优先；只应提高核心索引，全部设高会失去优先级意义 |
| `MaxResultWindow` | `index.max_result_window` | 整数 **1000..100000** | 调大会增加协调节点内存；**超过 50000 有 OOM 风险**，深分页优先用 `search_after` |
| `MappingTotalFieldsLimit` | `index.mapping.total_fields.limit` | 整数 **300..3000** | 上调仅为字段爆炸救急；字段过多拖慢查询与 master 元数据同步，根治应优化数据模型 |
| `TotalShardsPerNode` | `index.routing.allocation.total_shards_per_node` | 整数 **500..10000** | 仅支持放宽；需满足「值 × 数据节点数 ≥ 主分片数 × (1+副本数)」，否则仍会有未分配分片 |

### 未列出的常见诉求

| 用户诉求 | 说明 |
|---------|------|
| 改分片数 `index.number_of_shards` | **静态 setting，索引创建后不可修改**，只能通过 shrink / split / reindex 实现（本 Skill 均不支持） |
| 改 mapping / 字段类型 | **不属于 settings，本 tool 不支持**，通常需要 reindex |
| `index.blocks.write` 写保护 | 不在支持列表；需要"关闭写入"时改用 [§21 `CesUpdateIndexState(State=close)`](#21-cesupdateindexstate索引开关-)（注意 close 是读写全禁） |
| 冷热路由 `index.routing.allocation.require.box_type` | 不在支持列表，如实告知不支持 |

### 服务端前置检查

- 上述参数**至少要传 1 个**，未传的不会被改动
- 传 `NumberOfReplicas` 时会校验其**不超过「数据节点数-1」**，超出则阻断 → 改前先用 [§1](#1-cesclusterhealth集群健康-) 或 [§2](#2-cesgetnode节点列表-) 数数据节点数
- `DelayedTimeout` 最大 24h；`IndexPriority` 为 0..1000；`MaxResultWindow` 为 1000..100000；`MappingTotalFieldsLimit` 为 300..3000；`TotalShardsPerNode` 为 500..10000
- 传 `TotalShardsPerNode` 前必须结合索引主分片数、副本数和数据节点数校验容量公式；它不支持设为 ES 默认的 `-1`
- 改前与改后统一用 [§12 `CesGetIndexInfo(Type="settings")`](#12-cesgetindexinfo索引维度信息-) 读取实际值
- ✅ **不要求集群处于正常状态** —— 集群卡住或异常时同样可调用（解除只读阻塞、调低副本数等正是抢救手段）

```
# 调低副本数（先确认数据节点数 ≥ 2）
CesUpdateIndexSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                       Index="my_index", NumberOfReplicas=1)

# 批量导入期关闭刷新（⚠️ 导入完必须改回 1s / 30s）
CesUpdateIndexSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                       Index="my_index", RefreshInterval="-1")

# 磁盘腾出空间后解除只读阻塞
CesUpdateIndexSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                       Index="my_index", ReadOnlyAllowDelete="null")

# 滚动维护前延迟节点离线后的分片重分配（⚠️ 维护后恢复原值）
CesUpdateIndexSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                       Index="my_index", DelayedTimeout="10m")

# 字段爆炸临时救急（⚠️ 根治应优化数据模型）
CesUpdateIndexSettings(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                       Index="my_index", MappingTotalFieldsLimit=1500)
```

---

## 19. CesUpdateAliases（别名变更）🔀

- **类型**：**写**（风险中高：**直接切换业务读写流量**）
- **底层**：`POST _aliases`

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Alias` | ✅ | 要变更的**别名完整名称**。🚫 禁止通配 `*` / `_all` / 以 `.` `_` `-` `+` 开头。**不能与已存在的索引同名**（否则 ES 报 `invalid_alias_name_exception`） |
| `AddIndex` | ❌ | 要让该别名指向的**索引完整名称** |
| `RemoveIndex` | ❌ | 要解除该别名指向的**索引完整名称** |

> ⚠️ `AddIndex` 与 `RemoveIndex` **至少提供一个**。

### 三种用法

| 用法 | 参数 | 语义 |
|------|------|------|
| **零停机切换**（主要用途） | 同时传 `AddIndex` + `RemoveIndex` | remove 与 add 在**同一原子请求**中完成（remove 先于 add），保证任一时刻别名恰好指向一个索引，业务流量**无缝**从旧索引切到新索引。典型用于 reindex 后的切换 |
| 新增指向 | 只传 `AddIndex` | 让别名额外指向某索引 |
| **解除指向** | 只传 `RemoveIndex` | ⚠️ **这是本 MCP 唯一能删除别名的途径**（底层云 API 不支持 DELETE 方法，ES 原生 `DELETE <index>/_alias/<name>` 无法使用） |

```
# 零停机切换：my_alias 从 v1 切到 v2
CesUpdateAliases(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                 Alias="my_alias", RemoveIndex="my_index_v1", AddIndex="my_index_v2")
```

### 约束

- 一次调用**只能操作一个别名**（`Alias` 单值），但可同时对该别名做一次 remove + 一次 add
- `Alias` / `AddIndex` / `RemoveIndex` 均须**完整名称**，禁止通配与 `_all`，不支持系统索引与系统别名（以 `.` 开头）
- 🔴 **变更前必调 [§11 `CesListIndices`](#11-ceslistindices索引与别名列表-)** 确认别名当前指向哪个索引（算 `RemoveIndex` 的依据）
- ✅ **不要求集群处于正常状态** —— 集群异常时往往正需要把别名切到健康索引上

> 🔴 **确认信息中必须写明**：切换后哪些业务流量会流向新索引、旧索引是否仍可查询、回滚方式（反向再切一次）。

---

## 20. CesRolloverIndex（索引滚动）🎯

- **类型**：**写**（风险中高：创建新索引 + 切换别名）
- **底层**：`POST <Alias>/_rollover`
- **用途**：时序数据（日志、监控、订单流水）按大小或时间分割索引

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Alias` | ✅ | 要执行滚动的**别名完整名称**。🚫 禁止通配 `*` / `_all` / 以 `.` `_` `-` `+` 开头 |
| `DryRun` | ❌ | 默认 `false`。`true` = **只预演不实际执行（零副作用）**，返回将要创建的索引名与条件判定结果 |

### 🔴 重要限制（调用前必读）

1. **本 tool 执行的是「无条件立即滚动」** —— **不支持** `max_age` / `max_docs` / `max_size` 等触发条件，调用即立刻滚动。
   → 先用 [§11 `CesListIndices`](#11-ceslistindices索引与别名列表-) 确认别名指向，再用 [§11A `CesCatIndices`](#11a-cescatindices索引量化明细-) 查看当前索引 `docs.count` / `pri.store.size`，**人工判断是否达到滚动时机**
2. **别名当前指向的索引名必须符合「名称 + 数字后缀」格式**（如 `my-index-000001`）。不符合时 ES 会报错要求显式指定新索引名，而**本 tool 不支持指定目标索引名** → 这种情况改用 [§19 `CesUpdateAliases`](#19-cesupdatealiases别名变更-) 手工创建并切换别名
3. 别名必须**恰好指向一个索引**，且该索引是**可写索引（write index）**，否则 ES 拒绝
4. 滚动后的新索引名由 ES **自动递增生成**（`my-index-000001` → `my-index-000002`）

### 🔴 强烈建议：先 DryRun 预演

```
# ① 预演（零副作用）
CesRolloverIndex(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                 Alias="my_logs_write", DryRun=true)
# → 返回将要创建的索引名，确认无误

# ② 实际执行
CesRolloverIndex(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                 Alias="my_logs_write")
```

> ⚠️ **要求集群处于正常状态** —— 滚动会创建新索引并切换别名，集群异常时执行会加剧风险，**会被服务端阻断**。被阻断时如实转述，建议先处理集群健康问题。

---

## 21. CesUpdateIndexState（索引开关）🚪

- **类型**：**写**（`open` 风险低 / **`close` 风险高**）
- **底层**：`POST <Index>/_open` 或 `POST <Index>/_close`

| 参数 | 必需 | 说明 |
|------|-----|------|
| `Index` | ✅ | **单个索引的完整名称**。🚫 禁止通配 `*` / `_all` / 以 `.` `_` `-` `+` 开头 |
| `State` | ✅ | `open` / `close` —— **两者语义与风险差异极大** |

### `State=open`（恢复类，风险低）

- 打开已关闭的索引，恢复可读写
- 典型场景：恢复被关闭的索引、修改静态 setting 后重新打开
- 会**触发分片恢复**，大索引可能耗时较长 → 用 [§1 `CesClusterHealth`](#1-cesclusterhealth集群健康-) 看聚合状态，并用 [§11B `CesGetRecovery`](#11b-cesgetrecovery分片恢复进度-) 跟踪每个分片的百分比、速率与剩余量
- ✅ **不要求集群处于正常状态** —— 集群异常或变更卡住时正需要尽快恢复索引可读写

### `State=close`（🔴 高风险，制造不可用）

- 关闭索引后**既不可读也不可写**，但不再占用集群堆内存
- 典型场景：归档不再查询的历史索引以释放内存
- 🔴 **风险**：
  - 该索引上的**所有读写请求都会失败** —— 属于「制造不可用」的操作，**必须确认业务已不再访问该索引**
  - ES **6.x 与 7.0 / 7.1** 版本在索引关闭期间**不复制副本**，此时若发生节点故障**存在丢数据风险**（7.2+ 关闭索引仍复制副本）→ 需先确认集群版本
- ⚠️ **要求集群处于正常状态** —— 集群异常时调用会被**服务端阻断**，避免在故障中扩大影响面

### 通用说明

- 🔴 调用前先用 [§11 `CesListIndices`](#11-ceslistindices索引与别名列表-) 看索引的 `status` 列确认当前是 `open` 还是 `close`
- ✅ **幂等**：对已 `open` 的索引再 `open`（或已 `close` 的再 `close`）同样返回成功

```
CesUpdateIndexState(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                    Index="my_index", State="open")
```

> ⚠️ 需要"禁止写入但保留查询"时，`close` **不合适**（读写全禁）；而 `index.blocks.write` 不在 [§18](#18-cesupdateindexsettings索引-settings-变更-) 支持列表内 —— 如实告知该诉求当前无 tool 可满足。

---

## 22. CesCancelTask（取消任务）🛑

- **类型**：**写**（🔴 **风险高：不可回滚**）
- **底层**：`POST _tasks/<TaskId>/_cancel`
- **用途**：终止长时间运行、占用大量资源或已失控的任务，缓解集群压力。常见对象：`reindex`、`delete_by_query`、`update_by_query`、`forcemerge`、超大范围搜索

| 参数 | 必需 | 说明 |
|------|-----|------|
| `TaskId` | ✅ | 完整的「节点ID:任务编号」形态，如 `oTUltX4IQMOUUVeiohTt8A:12345`。🚫 **禁止通配符 `*`，不支持批量取消**（避免误中断集群全部工作） |

### 🔴 使用顺序

```
① CesTasks           → 查当前任务列表，拿到目标 task_id
② 结合 running_time  → 判断哪个任务异常（运行时间远超预期）
③ 确认 cancellable   → false 的任务无法取消
④ CesCancelTask      → 取消
⑤ CesTasks           → 回读确认任务是否已消失
```

### 🔴 重要语义（务必理解后再调用）

1. **协作式取消**：请求返回成功**只表示「取消标记已设置」**，任务会在到达下一个可中断点时才真正停止，**不保证立即结束** → 取消后需回读 `CesTasks` 确认
2. **已完成的部分不会回滚**：
   - `reindex` 被取消 → 已写入目标索引的文档**保留**，造成**目标索引数据不完整**
   - `delete_by_query` 已删除的文档**无法恢复**
   - 🔴 取消这类任务后通常需要**人工清理或重跑** —— 必须在确认信息中明确告知用户这一后果
3. **部分任务不可取消**：ES 标记 `cancellable: false` 的任务调用会返回错误

> ✅ **不要求集群处于正常状态** —— 取消失控任务本身就是解除集群异常的常用手段。

---

## 附录 A：索引 / 别名命名约束（全局通用）

### 只读 tool（支持通配）

`CesListIndices` / `CesCatIndices` / `CesGetIndexInfo` 的 `Index`：

- 支持：精确名 `my_index`、后缀通配 `my_index*`、前缀通配 `*my_index`、全部 `*`
- 字符限制：**仅允许字母数字及 `.` `_` `-` `+` `*`，不能包含 `/`**
- `CesListIndices` / `CesCatIndices` 的 `Index` 可不传（默认 `*`）；`CesGetIndexInfo` 的 `Index` 与 `Type` 均必传

### 写类 tool（禁止通配）

`CesRefreshIndex` / `CesUpdateIndexSettings` / `CesUpdateIndexState` 的 `Index`，以及 `CesUpdateAliases` / `CesRolloverIndex` 的 `Alias` / `AddIndex` / `RemoveIndex`：

- 必须是**单个对象的完整名称**
- 🚫 禁止通配符 `*`
- 🚫 禁止 `_all`
- 🚫 禁止以 `.` `_` `-` `+` 开头（**保护系统索引 / 系统别名**）

> 💡 用户给出通配表达式（如"把 `logs-*` 的副本数改成 1"）时：先用 `CesListIndices` 展开为具体索引列表 → **逐个索引单独确认、单独调用**，禁止打包为一次确认。

---

## 附录 B：服务端前置检查一览

| Tool | 要求集群正常状态？ | 其他服务端校验 |
|------|:---:|--------------|
| 全部只读 tool | 否 | — |
| `CesRefreshIndex` | 否 | 索引名合法性 |
| `CesClusterReroute` | **否**（专用于异常场景） | — |
| `CesUpdateClusterSettings` | **否**（异常时正需要它抢救） | 至少传 1 参数；水位单位统一且 `low<high<flood`；范围校验；写 persistent 并自动清除目标项的同名 transient 值；`MaxShardsPerNode` 要求 ES 7.0+ |
| `CesUpdateIndexSettings` | **否**（异常时正需要它抢救） | 至少传 1 参数；副本数/刷新间隔/translog/新增 5 项均做范围校验；`ReadOnlyAllowDelete` 不支持 `true`；`TotalShardsPerNode` 需满足容量公式 |
| `CesUpdateAliases` | 否 | `AddIndex`/`RemoveIndex` 至少一个；别名不得与已存在索引同名 |
| `CesRolloverIndex` | 🔴 **是（会被阻断）** | 别名恰好指向一个可写索引；索引名须符合数字后缀格式 |
| `CesUpdateIndexState(open)` | 否 | 索引名合法性 |
| `CesUpdateIndexState(close)` | 🔴 **是（会被阻断）** | 索引名合法性 |
| `CesCancelTask` | 否 | `TaskId` 须完整形态、禁止通配；任务须 `cancellable` |

> 🔴 **被服务端前置检查阻断时**：如实转述阻断原因，**不重试、不换参数硬闯、不绕行**。集群状态类阻断建议先用 `tencent-es-diagnose` 定位、必要时走 `tencent-es-control-panel` 处理资源问题。

---

## 附录 C：通用约定与错误处理

### 参数约定

- **所有 tool** 必填 `Region`（如 `ap-guangzhou` / `ap-shanghai` / `ap-beijing`）+ `InstanceId`（如 `es-xxxxxxxx`）
- 用户未提供集群 ID 时，本 Skill **不提供集群列表能力**（`DescribeInstances` 属管控面）→ 引导用户提供集群 ID 与地域

### 常见错误处理

| 错误现象 | 处理 |
|---------|------|
| MCP tool 不可用 / 连接错误 | 提示用户在连接器管理页面配置并连接；🚫 **禁止**用 `tccli` / `curl` / ES 直连绕行 |
| `AuthFailure` | 让用户联系管理员确认 CAM 授权，不重试 |
| 参数校验失败（不合法索引名 / 通配符 / 系统索引） | 按 [附录 A](#附录-a索引--别名命名约束全局通用) 修正后**重新走一轮确认**，不擅自改名 |
| 服务端「要求集群正常状态」阻断 | 如实转述；建议先 `CesClusterHealth` + `CesClusterAllocationExplain` 定位，或交 `tencent-es-diagnose` |
| `CesUpdateClusterSettings` 清除了同名 transient 值 | 属最新 tool 的预期行为；必须回读 `CesGetClusterSettings`，确认 transient 已清除且 persistent 为目标值，并如实说明实际生效来源已改变 |
| `CesUpdateIndexSettings` 参数范围或副本数超限被阻断 | 按 §18 的范围/容量约束重算；涉及副本数时用 `CesClusterHealth` / `CesGetNode` 数数据节点，调整后重新确认 |
| `CesRolloverIndex` 报索引名格式错误 | 说明本 tool 不支持指定目标索引名，改用 `CesUpdateAliases` 手工切换 |
| `CesCancelTask` 报任务不可取消 | 如实告知该任务 `cancellable: false`，无法通过本 Skill 取消 |
| 返回体过大 / 上下文截断风险 | `CesGetNodesStats` 指定 `Module`；`CesListIndices` / `CesCatIndices` / `CesGetIndexInfo` 带更精确的 `Index`；`CesGetRecovery` 保持默认 `ActiveOnly=true`；避免大索引非必要的 `mapping`/`stats`/`segments`/`fielddata` 全量查询 |
| 用户请求的能力无对应 tool | 如实告知不支持，引导控制台 / Kibana Dev Tools；🚫 **不绕行、不臆造 tool** |
