# ES 数据面只读 Tools（MCP）

> MCP tools | **本文档只收录本 Skill 允许调用的只读 tool**。数据面写类 tool 见 [SKILL.md 安全边界](../../SKILL.md#-安全边界最高优先级覆盖本文档其它所有表述)（本 Skill 一律拒绝）。

## 概述

历史版本通过 `RequestInstancesByGet` 手工拼接 Uri 字符串（如 `_cluster/allocation/explain?pretty`）来透传 ES 原生接口，需要维护白名单正则、处理 URL 编码与响应格式差异。

**MCP 版本已改为一批语义化的专用 tool**，每个 tool 对应一个 ES 只读接口，无需拼 Uri、无需关心白名单：

| Tool | 底层 ES 接口 | 参数 |
|------|-------------|------|
| `CesClusterHealth` | `_cluster/health` | `Region`, `InstanceId` |
| `CesGetAllocation` | `_cat/allocation` | `Region`, `InstanceId` |
| `CesClusterAllocationExplain` | `_cluster/allocation/explain` | `Region`, `InstanceId` |
| `CesGetShards` | `_cat/shards` | `Region`, `InstanceId` |
| `CesClusterPendingTasks` | `_cluster/pending_tasks` | `Region`, `InstanceId` |
| `CesGetNode` | `_cat/nodes` | `Region`, `InstanceId` |
| `CesTasks` | `_tasks` | `Region`, `InstanceId` |
| `CesGetClusterSettings` | `_cluster/settings?include_defaults=true` | `Region`, `InstanceId` |
| `CesGetThreadPool` | `_cat/thread_pool?v&format=json` | `Region`, `InstanceId` |
| `CesGetNodesStats` | `_nodes/stats` | `Region`, `InstanceId`, **`Module`**（可选）|
| `CesGetHotThreads` | `_nodes/hot_threads` | `Region`, `InstanceId`, **`Threads`** / **`Interval`**（可选）|
| `CesListIndices` | `_resolve/index/<Index>` | `Region`, `InstanceId`, `Index`（可选，默认 `*`）|
| `CesGetIndexInfo` | `<Index>/_mapping`、`_settings`、`_alias`、`_stats`、`_segments`、`_recovery`、`_count`、fielddata、`_cat/segments`（由 `Type` 决定）| `Region`, `InstanceId`, **`Index`（必填）**, **`Type`（必填）**|

> 多数 tool 只需 `Region` + `InstanceId`，**无嵌套结构、无需构造 JSON**。但下列 3 个有额外参数，调用前需注意：
>
> | Tool | 额外参数 | 要点 |
> |------|---------|------|
> | `CesGetNodesStats` | `Module` | 取值 `all`（默认，**量最大**）/ `jvm` / `fs` / `thread_pool`。🔴 **不传会返回全量统计，大集群极易撑爆上下文** —— JVM/GC 用 `jvm`、磁盘明细用 `fs`、线程池用 `thread_pool` |
> | `CesGetHotThreads` | `Threads` / `Interval` | `Threads` 取值 **1~100**（建议 3~5 控制体积）；`Interval` 如 `2s` / `500ms`。⚠️ **返回纯文本（非 JSON）** |
> | `CesGetIndexInfo` | `Index`（**必填**）+ `Type`（**必填**）| `Index` 支持通配 `my_index*` / `*my_index` / `*`；仅允许字母数字及 `.` `_` `-` `+` `*`，**不能含 `/`**。`Type` 决定查询类别（见下表），字段多的索引 `mapping`/`stats` 返回极大，尽量给精确索引名 |
>
> 🔀 **`CesGetIndexInfo` 的 `Type` 枚举**（原 `CesGetIndexMapping`/`CesGetIndexSetting` 已合并进此 tool）：
>
> | `Type` | 底层接口 | 用途 |
> |--------|---------|------|
> | `mapping` | `<Index>/_mapping`（含默认值）| 字段定义、类型、分词器（原 `CesGetIndexMapping`）|
> | `settings` | `<Index>/_settings`（含默认值）| 分片/副本数、刷新间隔、**慢日志实际生效阈值 `index.search.slowlog.threshold`**（原 `CesGetIndexSetting`）|
> | `alias` | `<Index>/_alias` | 该索引绑定的别名 |
> | `stats` | `<Index>/_stats` | 文档数、存储、段、refresh/merge 索引级统计（**判断索引是否过大**）|
> | `segments` | `<Index>/_segments` | Lucene 段原始信息 |
> | `recovery` | `<Index>/_recovery` | 该索引分片恢复进度（节点重启/扩缩容后核对）|
> | `count` | `<Index>/_count` | 全量文档数（**不支持带查询条件**）|
> | `fielddata` | `<Index>/_stats/fielddata?fields=*` | 精确到字段的 fielddata 内存占用（**定位 text 字段被聚合导致的内存膨胀**）|
> | `cat_segments` | `_cat/segments/<Index>` | 段表格视图（**段数过多/未 merge 判定、refresh_interval 建议**）|
>
> ⚠️ `CesListIndices` 的 `Index` **可不传**（默认 `*` 全量），但索引多的集群建议带通配前缀收窄。
>
> 🔴 **`CesListIndices` 底层是 `_resolve/index/<Index>`，不是 `_cat/indices`** —— 返回的是 **index / alias / data_stream 的名称与属性**（含 `attributes` 里的 `open`/`closed`），**不含 `docs.count` / `store.size` / `pri` / `rep` 等统计列**。
> 因此「分片数接近上限找可清理索引」「判断索引是否过大」这类需求，需配合 `CesGetShards` 看每个分片的 `docs` / `store` 与分片总数，或用 `CesGetIndexInfo`(`Type=stats`) 看索引级存储与文档数。

## 核心价值：不受监控探针影响

数据面 tool **直连集群**，返回集群当下的真实状态：

- ✅ **无哨兵值问题** —— 不存在 `-2` / `-1` 污染
- ✅ **无管控面延迟** —— 比 `DescribeInstances.HealthStatus` 快照更实时
- ✅ **是监控失联时的权威兜底** —— 磁盘打满导致探针失联时，监控全是 `-2`，但数据面仍能返回真实水位

因此在打分规则中：
- `CesClusterHealth` 作为**健康色判定的第三路信号**（建议常规调用）
- `CesGetAllocation` 作为**磁盘打满的权威判据**（某节点 `disk.percent >= 95` 等价于一票否决1b 命中）

## 调用时机

| Tool | 建议时机 |
|------|---------|
| `CesClusterHealth` | **常规调用**（每次健康检查都调，用于交叉验证健康色）|
| `CesGetThreadPool` | 写入/查询被拒（`BulkRejected > 0`）时 —— 注意 `rejected` 是累计值，需两次采样比增量 |
| `CesGetNodesStats` | JVM/GC 或磁盘明细排查时，**必须带 `Module`** |
| `CesGetHotThreads` | CPU 飙高且 `CesTasks` 无法定性时（返回纯文本，体积大）|
| 其余 | **按需调用** —— 仅在打分识别出需深度诊断后，按症状路由表选择对应 tool |

> ⚠️ 日常批量巡检**不要**对每个集群调用全部数据面 tool，否则调用量和输出噪音都会失控。原则：**监控定位现象 → 数据面定位根因**。

## 高价值使用场景

### 1. 集群 Red / Yellow → 定位未分配分片

```
CesClusterHealth(Region=..., InstanceId=...)              # 确认真实健康色、未分配分片数
CesClusterAllocationExplain(Region=..., InstanceId=...)   # 未分配的具体原因
CesGetShards(Region=..., InstanceId=...)                  # 哪些索引/分片处于 UNASSIGNED
```

`CesClusterHealth` 关键返回字段：

| 字段 | 含义 |
|------|------|
| `status` | `green` / `yellow` / `red` |
| `number_of_nodes` / `number_of_data_nodes` | 节点数（与 `DescribeInstances.NodeNum` 对比可发现掉节点）|
| `unassigned_shards` | 未分配分片数（> 0 是 Yellow/Red 的直接原因）|
| `active_shards_percent_as_number` | 活跃分片百分比 |
| `initializing_shards` / `relocating_shards` | 正在初始化/迁移的分片 |

> ℹ️ `CesClusterAllocationExplain` 在集群健康时返回 `unable to find any unassigned shards to explain`，**这是正常响应**，不是错误，说明确实没有未分配分片。

### 2. 磁盘告警 → 核实各节点真实水位

```
CesGetAllocation(Region=..., InstanceId=...)
```

返回每个节点的 `shards`、`disk.indices`、`disk.used`、`disk.avail`、`disk.total`、`disk.percent`。

**用途**：
- 监控 `DiskUsageMax` 是集群聚合值，可能掩盖**单节点热点**（如3 节点中 1 个 95%、其余 40%）
- 探针失联时的权威兜底
- 判断是否分片分布不均导致的局部水位高

### 3. Master 过载 / 变更缓慢

```
CesClusterPendingTasks(Region=..., InstanceId=...)
```

返回待处理任务及其 `time_in_queue`、`priority`、`source`。若大量 `put-mapping` 排队，说明业务在高频变更 mapping。

### 4. CPU 高 / 查询热点

```
CesTasks(Region=..., InstanceId=...)
```

查看正在执行的任务（reindex、force merge、大查询、分片迁移），定位 CPU 消耗来源。

### 5. 节点重启后核对状态

```
CesGetNode(Region=..., InstanceId=...)
```

返回节点列表、角色、`load_1m`、堆内存占用、磁盘占用。与 `DescribeInstanceOperations` 的重启记录配合，确认节点是否已全部恢复。

### 6. 确认只读锁与水位配置

```
CesGetClusterSettings(Region=..., InstanceId=...)
```

检查 `index.blocks.read_only_allow_delete`、`cluster.routing.allocation.disk.watermark.*` 等配置，确认只读锁是否仍在生效。

> 💡 返回含 `persistent` / `transient` / `defaults` 三层（本 tool 带 `include_defaults=true`）。**ES 生效优先级：`transient` > `persistent` > `defaults`** —— 判读某项配置是否生效时必须看清它来自哪一层。

### 7. CPU 飙高 → 抓热线程定位具体耗时操作

```
CesGetHotThreads(Region=..., InstanceId=..., Threads=3, Interval="2s")
```

⚠️ **返回纯文本（非 JSON）**，输出较长，`Threads` 建议取 3~5。判读时关注栈顶方法（`search` / `merge` / `bulk` / `GC` 等）。

> 📌 与 `CesTasks` 配合：`CesTasks` 看"有哪些任务在跑"，`CesGetHotThreads` 看"CPU 实际耗在哪段代码"。

### 8. 写入/查询被拒 → 线程池 reject 判定

```
CesGetThreadPool(Region=..., InstanceId=...)
```

返回 `bulk` / `search` / `write` / `get` 等线程池的 `active` / `queue` / `rejected`。

| 现象 | 含义 |
|------|------|
| `rejected > 0` | **队列已满，有请求被拒绝** —— 最直接的过载证据 |
| `queue` 持续接近上限 | 处理能力不足，即将开始 reject |
| `active` 长期打满 | 线程池饱和 |

> 🔴 **`rejected` 是累计值**（自节点启动累计），**需两次采样对比增量**才能判断"当前是否还在 reject"。仅看一次的非零值可能是很久以前的历史遗留，据此判定"正在被拒绝"是典型误判。

### 9. JVM / GC / 磁盘明细 → 节点级详细统计

```
CesGetNodesStats(Region=..., InstanceId=..., Module="jvm")
```

| 排查方向 | `Module` 取值 |
|---------|-------------|
| JVM 堆内存高 / GC 频繁 | `jvm` |
| 磁盘使用明细 | `fs` |
| 线程池（比 `CesGetThreadPool` 更详细）| `thread_pool` |
| 全部（**量最大，谨慎**）| `all` 或不传 |

> 🔴 **务必指定 `Module`** —— 不传会返回全量统计，大集群极易撑爆上下文。

### 10. 索引维度信息 → mapping / settings / stats / fielddata / segments

```
CesGetIndexInfo(Region=..., InstanceId=..., Index="my_index", Type="fielddata")
```

`CesGetIndexInfo` 通过 `Type` 一站式覆盖索引维度的多种只读信息（`Type` 枚举见上文参数表）。诊断高频用法：

| 排查场景 | `Type` | 判读要点 |
|---------|--------|---------|
| **JVM 堆高 / fielddata 内存膨胀**（场景 G）| `fielddata` | 精确到字段的 fielddata 占用，定位是哪个 `text` 字段被聚合/排序导致堆内存膨胀，据此建议禁用该字段 fielddata 或改用 `keyword` |
| **磁盘告警 / 分片数上限找大索引**（场景 F）| `stats` | 看索引级 `docs.count`、`store.size`，判断哪些索引过大可清理（`CesListIndices` 不含统计列，需靠这个）|
| **写入慢 / 段数过多**（场景 C）| `cat_segments` | 段数过多、未及时 merge 会拖慢写入与查询；据此建议调整 `refresh_interval` 或触发 merge（写操作由用户执行）|
| **查询慢确认慢日志阈值**（场景 E）| `settings` | 确认 `index.search.slowlog.threshold.*` 实际生效阈值，判断慢日志是否漏采 |
| **节点重启后核对分片恢复**（场景 H）| `recovery` | 看该索引各分片 recovery 进度，确认是否已全部恢复 |
| 字段定义 / 别名 / 文档数 | `mapping` / `alias` / `count` | 常规元信息查询 |

> ⚠️ `mapping`、`stats`、`fielddata` 在字段多/索引大的集群返回量大，**尽量给精确索引名**，避免用 `*` 全量拉取。

## ⚠️ 关键约束

- **本 Skill 只用只读 tool**：上表 tool 全部是 GET 类查询。
  🔴 **写类数据面 tool（`CesClusterReroute`、`CesUpdate*`、`CesRefreshIndex`、`CesRolloverIndex`、`CesCancelTask`）连接器虽然提供，但本 Skill 越权，一律拒绝** —— 判断依据见 [SKILL.md 安全边界](../../SKILL.md#-安全边界最高优先级覆盖本文档其它所有表述) 的显式清单，**不允许用 `Ces*` 前缀推断只读**。
- **需要执行写操作时**：输出诊断结论与建议动作，并说明由 **`tencent-es-data-panel` Skill**（数据面：`_reroute` / 索引开关 / settings 变更 / 解除只读锁）或 **`tencent-es-control-panel` Skill**（管控面：扩容 / 升配 / 重启）落地执行；用户也可自行在控制台 / Kibana Dev Tools 操作。
- **不主动批量调用**：由打分结果触发，遵循「监控看现象、数据面找根因」的分工
- **返回可能较大**：`CesGetShards`、`CesListIndices` 在大集群上返回量大，必要时落盘用 Python 解析；`CesGetNodesStats` 必须指定 `Module`；`CesGetIndexInfo` 的 `mapping`/`stats`/`fielddata` 尽量给精确索引名，避免 `*` 全量

## 错误码

| 错误码 | 含义 |
|------|------|
| `AuthFailure.*` | CAM 权限不足 |
| `ResourceNotFound.InstanceNotExist` | 集群 ID 不存在或地域不匹配 |
| 集群不可达 / 超时 | 集群可能已不可用（磁盘打满、节点全挂）—— **这本身就是重要诊断信号**，应与监控失联现象合并判断 |
