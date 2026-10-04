# MCP Tool 详细参考（MCP Tools Reference）

> 🔴 **本文档是 tool 参数、服务端前置检查、错误码的唯一权威来源（SSOT）**。SKILL.md 只有索引，`workflow.md` 只有流程与话术 —— 参数语义以本文档为准，两者冲突时以本文档为准。
>
> **调用任何 tool 前必须读完对应章节**，禁止凭索引或记忆调用。
>
> 鉴权在宿主层由 MCP 连接器完成，本 Skill 不接触密钥。
>
> ⚠️ 所有 tool 均需 `Region` 参数（如 `ap-guangzhou`）。以下表格中 `Region` 不再重复列出。

## 目录

**只读类**
1. [DescribeInstances（集群概览）](#1-describeinstances集群概览-)
2. [GetMonitorData（监控取数）](#2-getmonitordata监控取数-)

**变更类**

3. [UpdateInstanceNodeNum（节点数量扩容）](#3-updateinstancenodenum节点数量扩容-)
4. [UpdateInstanceDiskSize（磁盘扩容）](#4-updateinstancedisksize磁盘扩容-)
5. [RestartInstance（集群滚动重启）](#5-restartinstance集群滚动重启-)
6. [RestartNodes（节点重启）](#6-restartnodes节点重启-)
7. [RestartKibana（Kibana 重启）](#7-restartkibanakibana-重启-)
8. [UpdateEsAcl（Kibana 访问白/黑名单）](#8-updateesaclkibana-访问白黑名单-)
9. [UpdateKibanaPublicAccess（Kibana 公网访问开关）](#9-updatekibanapublicaccesskibana-公网访问开关-)
10. [UpdateKibanaPrivateAccess（Kibana 内网访问开关）](#10-updatekibanaprivateaccesskibana-内网访问开关-)

**辅助只读类**

11. [DescribeInstanceOperations（变更进度）](#11-describeinstanceoperations变更进度-)
12. [DescribeClusterDiskRange（磁盘上下限）](#12-describeclusterdiskrange磁盘上下限-)
13. [DescribeUpgrade（可升级版本）](#13-describeupgrade可升级版本-)
14. [DescribeViews（集群视图）](#14-describeviews集群视图-)
15. [DescribeInstancePluginList（插件列表）](#15-describeinstancepluginlist插件列表-)
16. [DescribeClusterSnapshot（快照备份）](#16-describeclustersnapshot快照备份-)
17. [事件中心三件套](#17-事件中心三件套-)

**本地脚本（2 个，均零云 API 调用）**

18. [detect_my_ip.py（本机公网 IP 探测）](#18-detect_my_ippy本机公网-ip-探测-)
19. [forecast_calc.py（容量预测计算）](#19-forecast_calcpy容量预测计算-)

**附录**

- [通用约定与错误码](#附录通用约定与错误码)

---

## 1. DescribeInstances（集群概览）📊

- **类型**：只读
- **功能**：查询账号下 ES 集群实例列表与详情
- **定位**：**每次变更前的必调 tool**，用于读取 `Status`（可操作性）、`HealthStatus`、`NodeInfoList`（算扩容目标值）、`DiskType`、`EsAcl`

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceIds` | ❌ | 集群 ID 列表（字符串数组），按 ID 精确查询 |
| `InstanceNames` | ❌ | 集群名称列表，按名称查询 |
| `Fields` | ❌ | **返回字段投影白名单**，用于裁剪响应体、规避上下文截断。字段名精确匹配（大小写不敏感），未命中时退化为关键词子串匹配（如 `Disk` 命中 `DiskType`/`DiskSize`/`DiskEncrypt`）。传 `["*"]` 返回全量 |
| `Limit` | ❌ | 分页大小，默认 20，最大 100 |
| `Offset` | ❌ | 分页起始位置，默认 0 |
| `OrderByKey` | ❌ | 排序字段：1 实例 ID，2 实例名称，3 可用区，4 创建时间。不传按创建时间降序 |
| `OrderByType` | ❌ | 0 升序，1 降序 |

### ⚠️ 关键陷阱：默认返回精简字段集

**默认响应不含 `NodeInfoList` 和 `EsAcl`**，只有实例 ID/名称/状态/健康度/版本/规格/地域/创建时间等。做扩容或 ACL 变更时**必须显式传 `Fields`**，否则拿不到算目标值所需的数据。

```
# 变更前置查询（扩容场景）——务必带 Fields
DescribeInstances(
  Region="ap-guangzhou",
  InstanceIds=["es-xxxxxxxx"],
  Fields=["InstanceId","InstanceName","Status","HealthStatus","NodeInfoList",
          "NodeType","NodeNum","DiskType","DiskSize"]
)

# ACL 变更前置查询
DescribeInstances(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"],
                  Fields=["InstanceId","InstanceName","Status","EsAcl","KibanaUrl"])

# 集群列表（用精简字段集即可，不传 Fields）
DescribeInstances(Region="ap-guangzhou", Limit=100)
```

> 💡 不要动辄传 `Fields=["*"]`。大集群全量字段可能撑爆上下文，按需列举字段名。

### 关键检查项（🔴 状态码判读的唯一权威来源）

| 字段 | 正常值 | 异常处理 |
|------|-------|---------|
| `Status` | `1`（正常）| `0`=处理中（等待完成）；`-1`=停止；`-2`=删除中；`-3`=已隔离；`-4`=已过期（需续费）。**非 1 时全部变更 tool 都会被服务端阻断** |
| `HealthStatus` | **仅 `0`(Green) 可执行变更** | `1`=Yellow、`2`=Red。`RestartInstance` / `RestartNodes` / `UpdateInstanceNodeNum` **强制要求 green —— yellow 同样被阻断**，不要误以为 yellow 可以放行 |
| `NodeInfoList[].Type` | 节点类型 | 用于定位目标节点组，注意空值视为 `hotData` |
| `NodeInfoList[].NodeNum` | 该类型当前节点数 | **算扩容目标值的基准** |
| `NodeInfoList[].DiskSize` | 该类型单节点磁盘 GB | **算磁盘扩容目标值的基准** |
| `DiskType` | 磁盘类型 | `LOCAL_SSD`=本地盘（**不可扩磁盘**，只能加节点）；`CLOUD_*`=云盘（可扩磁盘）|
| `EsAcl.WhiteIpList` / `BlackIpList` | 白/黑名单 | 字段缺失 = 未开通公网访问 |

---

## 2. GetMonitorData（监控取数）📈

- **类型**：只读（云监控 `QCE/CES` 命名空间）
- **功能**：查询集群监控指标时序数据，支持批量多实例、可选节点级维度
- **定位**：**容量预测的唯一取数来源**（判读规则见 [capacity-forecast-rules.md](capacity-forecast-rules.md)）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceIds` | ✅ | 集群 ID 列表（**支持批量**），如 `["es-xxxxxxxx","es-yyyyyyyy"]` |
| `MetricName` | ✅ | 监控指标名，见下方指标表 |
| `StartTime` | ❌ | 起始时间，**ISO 8601 / RFC3339**，如 `2026-08-11T00:00:00+08:00`。默认当前时间往前 1 小时 |
| `EndTime` | ❌ | 结束时间，同上格式。默认当前时间 |
| `Period` | ❌ | 统计粒度（秒），常用 60/300/3600，默认 300 |
| `NodeId` | ❌ | 节点 ID。传入则查节点级指标；不传查集群聚合值 |

> ⚠️ 时间格式与 `DescribeInstanceOperations` **不同**：本 tool 用 ISO 8601（带时区），`DescribeInstanceOperations` 用 `YYYY-MM-DD HH:mm:ss`。别混用。

### 容量预测常用指标

| 指标名 | 单位 | 预警 | 危险 | 用途 |
|-------|------|-----|------|------|
| `DiskUsageMax` | % | 65 | 80 | 磁盘趋势 → 扩磁盘 / 加节点 |
| `CpuUsageMax` | % | 70 | 85 | CPU 趋势 → 升配（暂无 tool，只读推荐）|
| `JvmMemUsageMax` | % | 75 | 85 | JVM 趋势 → 升配（暂无 tool，只读推荐）|
| `IndexSpeed` | 次/s | — | — | 写入 QPS 增长趋势 → 加节点 |
| `SearchCompletedSpeed` | 次/s | — | — | 查询 QPS 增长趋势 → 加节点 |
| `SearchLatencyAvg` | ms | 200 | 500 | 延迟趋势（仅参考，根因归 diagnose skill）|

> 其他可用指标：`JvmOldMemUsageMax`、`IndexLatencyAvg`、`BulkRejectedCompletedPercent`、`Status`、`ShardNumLimitPercen`、`ClusterNumberOfPendingTasks`、`IsReadOnly`、`SearchQueueMax`/`WriteQueueMax`、`NodeOldGcDifMax`、`NodeParentBreakerDifMax`。

### ⚠️ 哨兵值必须剔除

云监控探针采集失败时返回 **`-2`（偶见 `-1`）** 而非 `null`。**判读前必须先剔除负值**，否则会把 `-2` 当成"磁盘使用率下降"，得出完全反向的趋势结论。

> ✅ 把本 tool 的返回**原样交给 [`forecast_calc.py`](#19-forecast_calcpy容量预测计算-)**，脚本内部已完成哨兵值剔除，无需 Agent 手工处理。

### 返回结构

```json
{"Response":{"MetricName":"DiskUsageMax","Period":3600,
  "DataPoints":[{"Dimensions":[{"Name":"uInstanceId","Value":"es-xxxxxxxx"}],
                 "Timestamps":[1786935600, ...],"Values":[15.074, ...]}]}}
```

> ⚠️ `Timestamps` 与 `Values` 是**两个平行数组**（非 (ts,value) 元组列表），按下标一一对应。批量多实例时 `DataPoints` 为多项，靠 `Dimensions.uInstanceId` 区分。

---

## 3. UpdateInstanceNodeNum（节点数量扩容）🔧

- **类型**：🔴 **写操作 / 变配**
- **功能**：对指定 ES 集群的某一类节点做**节点数量扩容（横向扩容）**，底层调用云 API `UpdateInstance`
- **变更方式**：蓝绿变更（`ScaleType=0`），**集群不重启**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `NodeNum` | ✅ | **扩容后的目标节点数量**（不是增量！）。必须严格大于该类型当前节点数 |
| `Type` | ❌ | 待扩容节点类型，默认 `hotData`。可选 `hotData` / `warmData` / `dedicatedMaster` / `dedicatedCoordinating` / `dedicatedMl` |

### 🚨 `NodeNum` 是目标总数，不是增量（🔴 换算步骤的唯一权威来源）

这是本 Skill 最高频的错误点：用户口头表达通常是**增量**（「扩 2 个节点」），而本 tool 必须传**目标总数**。

```
用户：「给 es-xxxxxxxx 扩容 2 个热节点」

① DescribeInstances(Region=..., InstanceIds=["es-xxxxxxxx"], Fields=["NodeInfoList","Status","HealthStatus","InstanceName"])
② 在 NodeInfoList 中找 Type=="hotData"（或 Type 为空）的项 → current_num = 3
③ target_num = 3 + 2 = 5
④ 校验 5 落在 hotData 的 2~50 区间内 ✅
⑤ 展示「热数据节点：3 → 5（增加 2 个）」+ 数据搬迁与计费提示 → 等用户确认
⑥ UpdateInstanceNodeNum(Region=..., InstanceId="es-xxxxxxxx", Type="hotData", NodeNum=5)
```

### 节点数量允许区间（🔴 区间约束的唯一权威来源）

| 节点类型 | 允许区间 | 备注 |
|---------|---------|------|
| `dedicatedMaster` | **仅 3 或 5** | 扩容只能由 3 调整为 5 |
| `dedicatedMl` | 3 ~ 5 | |
| `hotData` / `warmData` / `dedicatedCoordinating` | 2 ~ 50 | |

### 能力边界（服务端硬约束）

1. 仅支持扩容节点数量，**不支持缩容**
2. **不支持**修改节点规格（`NodeType`）
3. **不支持**修改磁盘（类型/大小/块数）—— 磁盘扩容请用 `UpdateInstanceDiskSize`
4. **不支持**新增集群中原本不存在的节点类型
5. 采用蓝绿变更（`ScaleType=0`），集群不重启

> 💡 **`NodeInfoList` 由 tool 内部自动查询并原样回填**，调用方无需（也无法）传入 —— 因此不存在「漏传某个节点类型导致误缩容甚至删除节点」的风险。

### 服务端强制前置检查（8 项，任一不通过直接阻断）

1. 实例运行状态必须正常（`Status == 1`）
2. 目标节点类型必须在集群中已存在
3. 目标节点数量必须**严格大于**当前数量（缩容或相等均阻断）
4. 目标节点数量必须落在该类型允许区间
5. 单节点集群不支持变配，直接阻断
6. 集群健康状态必须为 **green**，且不存在未分配分片
7. 集群不存在 **close 状态的索引**，也不存在**无副本（0 副本）的索引**
8. 官方变配检查接口 `CheckUpdateInstance` 必须返回 `AllowUpdate=true`

> ℹ️ 检查 7 常见阻断场景：用户有单副本测试索引（`number_of_replicas: 0`）。此时应告知用户「需先给该索引加副本或删除该索引」，**不要**试图绕过。

### 变更影响提示（必须向用户说明）

- 蓝绿变更，集群不重启
- 扩容完成后集群会把分片 **rebalance 到新节点，属真实数据搬迁**，可能影响业务读写延迟
- 新增节点**产生计费变化**
- 预计耗时：约 15~30 分钟（视数据量而定）

---

## 4. UpdateInstanceDiskSize（磁盘扩容）💾

- **类型**：🔴 **写操作 / 变配**
- **功能**：对指定 ES 集群的数据节点做**磁盘扩容**，底层调用云 API `UpdateInstance`
- **变更方式**：蓝绿变更（`ScaleType=0`），**集群不重启**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `DiskSize` | ✅ | **扩容后的目标单节点磁盘大小（GB）**。必须严格大于当前值，且落在该节点类型磁盘上下限区间内 |
| `Type` | ❌ | 待扩容节点类型，默认 `hotData`。可选 `hotData` / `warmData` / `dedicatedCoordinating` / `dedicatedMl`。**不支持 `dedicatedMaster`** |

### ⚠️ `DiskSize` 语义

`DiskSize` 是**目标单节点磁盘容量**，不是增量，也不是集群总容量。

```
用户：「把 es-xxxxxxxx 磁盘扩到 500G」

① DescribeInstances(..., Fields=["NodeInfoList","DiskType","Status"])
   → hotData 当前 DiskSize = 300（单节点），NodeNum = 3
② DescribeClusterDiskRange(Region=..., InstanceId="es-xxxxxxxx")
   → 确认 hotData 的 Min/Max 区间包含 500
③ 展示「单节点磁盘：300GB → 500GB；集群总容量 900GB → 1500GB」→ 确认
④ UpdateInstanceDiskSize(Region=..., InstanceId="es-xxxxxxxx", Type="hotData", DiskSize=500)
```

> ⚠️ 若用户说的是「总容量扩到 1500G」，需换算：`1500 / NodeNum(3) = 500` 再传。**换算过程必须在确认信息中展示给用户核对。**

### 能力边界（服务端硬约束）

1. 仅支持扩容，**不支持缩容**（且**云盘扩容不可逆**）
2. **不支持**修改磁盘类型、节点规格、节点数量
3. **不支持**修改 `dedicatedMaster` 磁盘（容量由系统固定）
4. 采用蓝绿变更（`ScaleType=0`），集群不重启

### 服务端强制前置检查（3 项）

1. 实例运行状态必须正常（`Status == 1`）
2. 目标磁盘大小必须**严格大于**当前磁盘大小
3. 目标磁盘大小必须落在该节点类型的磁盘上下限区间（`DescribeClusterDiskRange` 的 Min/Max）

### 本地盘集群无法扩磁盘

若 `DiskType == "LOCAL_SSD"`（本地 SSD 盘），**磁盘容量与机型绑定，无法单独扩容**。此时唯一扩容路径是 `UpdateInstanceNodeNum` 加节点。判读时先看 `DiskType` 再给建议。

---

## 5. RestartInstance（集群滚动重启）🔄

- **类型**：🔴 **写操作**
- **功能**：重启指定 ES 集群实例（常用于重启并升级内核 patch 版本）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `UpgradeKernel` | ❌ | 重启时是否升级内核 patch 版本，默认 `false` |

### ⚠️ 服务端硬编码约束（不对外暴露、不可更改）

| 约束 | 说明 |
|------|------|
| `ForceRestart` 恒为 `false` | **不提供强制重启** |
| `RestartMode` 恒为滚动重启 | **不提供全量重启**，避免整个集群同时重启造成服务中断 |

> 📌 因此**不要询问用户「滚动还是全量」**，也不要承诺强制重启。全量 / 强制重启只能走腾讯云控制台。

### 服务端强制前置检查（2 项）

1. 实例运行状态必须正常（`Status == 1`）
2. 集群健康状态必须为 **green**（**yellow / red 均阻断**）

### 标准应答话术（🔴 重启场景话术的唯一权威来源）

```
集群重启仅支持「滚动重启」（逐节点依次重启，服务不中断），且要求集群健康状态为 green。
当前集群 es-xxxxxxxx 健康状态：<green|yellow|red>

[green]  → 展示确认信息，等用户确认后调用 RestartInstance
[yellow/red] → 不执行。建议：
   ① 先用 tencent-es-diagnose skill 定位未分配分片原因，恢复 green 后再重启；
   ② 若为紧急抢救场景需强制/全量重启，请在腾讯云控制台操作。
```

### 变更影响提示

- 逐节点依次重启，服务不中断
- 耗时 ≈ 节点数 × 单节点重启时间
- 建议在维护时间窗口或业务低峰期执行
- `UpgradeKernel=true` 时会同时升级内核 patch 版本，需向用户明确说明

---

## 6. RestartNodes（节点重启）🖥️

- **类型**：🔴 **写操作**
- **功能**：重启指定 ES 集群的一个或多个节点

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `NodeNames` | ✅ | 待重启节点名称列表（**字符串数组**），如 `["1785402856003287032"]` |
| `RestartMode` | ❌ | `in-place`（原地重启，默认）或 `blue-green`（蓝绿重启）|
| `ForceRestart` | ❌ | 是否强制重启，默认 `false`。🚫 **本 Skill 恒不传此参数**，见下方规定 |

### 🚫 `ForceRestart` 使用规定（不得含糊处理）

**Agent 在任何情况下都不得传 `ForceRestart=true`**，包括用户主动要求时。原因：该参数会跳过「无 close 索引 / 无 0 副本索引」的保护语义，在无副本索引场景下会造成数据直接不可访问。

用户坚持要强制重启时，正确回应是：说明风险、引导腾讯云控制台操作，**不要为了满足请求而传 true**。

### 节点名称说明

节点名称**直接传入用户提供的值**即可，无需查询转换。格式因集群而异：

- 长数字串：`1785402856003287032`（**这就是节点名称**，直接使用）
- IP 地址：`10.0.0.1`

> 📌 用户说「重启节点 1774524330008786732」时，直接 `NodeNames=["1774524330008786732"]`，无需任何转换。
> 💡 若用户不知道节点名，可用 `DescribeViews` 或 `DescribeInstances(Fields=["NodeInfoList"])` 查询后让用户选择。

### `in-place` vs `blue-green`

| 维度 | `in-place`（原地重启） | `blue-green`（蓝绿重启） |
|------|---------------------|----------------------|
| 原理 | 直接重启现有节点 | 新建替换节点后迁移分片，再下线旧节点 |
| 业务影响 | ⚠️ 该节点分片暂时不可用，集群自动重路由 | ✅ 影响极小 |
| 耗时 | ✅ 快 | ❌ 慢（需数据迁移）|
| 适用 | 有副本、可接受短暂抖动 | 生产环境、高可用要求 |

> 询问用户选择时给出上表；无明确偏好时按 tool 默认 `in-place`，但**必须在确认信息中明示所用模式**。

### 服务端强制前置检查（4 项）

1. 实例运行状态必须正常（`Status == 1`）
2. 集群健康状态必须为 **green**（yellow / red 均阻断）
3. 集群**不存在 close 状态的索引**
4. 集群**不存在无副本（0 副本）的索引**

> ℹ️ 检查 3/4 的原因：节点重启期间该节点分片不可用，若索引无副本则数据直接不可访问。被阻断时告知用户需先给索引加副本或删除该索引，**不要试图用 `ForceRestart` 绕过**。

---

## 7. RestartKibana（Kibana 重启）🖼️

- **类型**：🔴 **写操作**
- **功能**：重启指定 ES 集群的 Kibana 服务
- **典型场景**：Kibana 无法访问、卡死、白屏等异常时的运维自愈

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |

### 服务端强制前置检查（1 项）

1. 实例运行状态必须正常（`Status == 1`）

### 变更影响提示

- 重启期间 **Kibana 短暂不可用**
- **不影响 ES 集群本身的读写**（Kibana 是独立的可视化组件）

### ⚠️ 与 ACL 问题的区分（高频误判）

| 用户描述 | 真实原因 | 正确处理 |
|---------|---------|---------|
| 「很抱歉，你没有权限访问」/ 403 | 本机公网 IP 不在白名单 | → [§8 UpdateEsAcl](#8-updateesaclkibana-访问白黑名单-)，**不是重启** |
| 页面打不开 / 白屏 / 一直转圈 / 卡死 | Kibana 进程异常 | → `RestartKibana` |
| 完全无法连接 / 域名解析失败 | 公网访问未开启 | → [§9 UpdateKibanaPublicAccess](#9-updatekibanapublicaccesskibana-公网访问开关-) |

> 🚫 **不要把 403「没有权限访问」当成 Kibana 故障去重启** —— 重启解决不了白名单问题，还白白让 Kibana 不可用一段时间。

---

## 8. UpdateEsAcl（Kibana 访问白/黑名单）🛡️

- **类型**：🔴 **写操作**
- **功能**：修改 ES 集群可视化组件（Kibana）的公网访问策略（IP 白名单 / 黑名单），底层调用云 API `UpdateInstance` 下发 `EsAcl`
- **典型场景**：Kibana 报「很抱歉，你没有权限访问」→ 本机公网 IP 不在白名单

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `WhiteIpList` | ❌* | 访问白名单 IP 列表（字符串数组），支持通配符，如 `["129.226.177.54","127.*.*.*"]` |
| `BlackIpList` | ❌* | 访问黑名单 IP 列表（字符串数组），支持通配符，如 `["10.*.*.*"]` |

> *白名单与黑名单**至少需要传入一个非空列表**。

### 🚨 必须同时回传白名单和黑名单

`UpdateEsAcl` 是**全量覆盖语义**，不是增量。只传 `WhiteIpList` 会导致 `BlackIpList` 被视为清空（反之亦然）。

```
正确流程（增量修改）：
① DescribeInstances(Region=..., InstanceIds=[id], Fields=["EsAcl","Status","InstanceName","KibanaUrl"])
   → 读出 EsAcl.WhiteIpList = ["1.2.3.4"], EsAcl.BlackIpList = ["9.9.9.9"]
② 在内存中做增量运算：
   追加 → target_white = 原列表 + 新IP（去重，保持原顺序）
   移除 → target_white = 原列表 - 指定IP（精确匹配）
③ 安全校验所有待追加 IP（见下方硬性约束）
④ 展示 diff（保留哪些 / 新增哪些 / 移除哪些 / 目标列表）+ Kibana 入口 → 等用户确认
⑤ UpdateEsAcl(Region=..., InstanceId=id,
              WhiteIpList=target_white,   ← 全量目标列表
              BlackIpList=target_black)   ← 即使没改也必须原样回传
```

### 🛡️ 硬性安全约束（🔴 唯一权威来源，**由 Agent 在 Skill 层强制拦截**）

服务端不保证拦截「全部放开」类输入，因此**本 Skill 层必须硬性拒绝**：

| 禁止的输入 | 拒绝原因 |
|-----------|---------|
| `0.0.0.0` / `0.0.0.0/0` / `::` / `::/0` / `*` / `any` / `all` | 等同于关闭白名单限制，存在严重安全风险 |
| 任何掩码为 `/0` 的 CIDR（如 `1.2.3.4/0`）| 等同于全部放开 |
| 操作执行后**白名单变为空** | 清空白名单 = 关闭限制，需走控制台显式确认 |
| 非法 IP / CIDR 格式 | 参数错误，先与用户核对 |

> ⚠️ 以上约束**没有任何绕过方式**。如用户确需完全开放，请引导其在腾讯云控制台操作并自行承担风险。

### 服务端强制前置检查（1 项）

1. 实例运行状态必须正常（`Status == 1`）

### 前置条件

集群必须**已开通公网访问**（`EsAcl` 字段非空）。若 `EsAcl` 缺失，说明未开通，应先用 [`UpdateKibanaPublicAccess`](#9-updatekibanapublicaccesskibana-公网访问开关-) 开启（需用户确认公网暴露风险），或引导用户在控制台开启。

### 📌 Kibana 403 快速修复路径（完整两步）

```
① 探测本机公网 IP（本地脚本，零云 API 调用）
   $PYTHON_CMD scripts/detect_my_ip.py --region ap-guangzhou
   → 输出：{"ip": "182.x.x.x", "source": "集群地域 ap-guangzhou 识别为国内地域..."}

② 读现有 ACL → 增量追加 → 确认 → 提交
   DescribeInstances(..., Fields=["EsAcl","Status","KibanaUrl"])
   UpdateEsAcl(Region=..., InstanceId=..., WhiteIpList=[...原有..., "182.x.x.x"], BlackIpList=[...原有...])

③ 提示用户约 1~2 分钟生效后重试访问 Kibana
```

> 🚫 **禁止跳过步骤 ①，由 Agent 自行 curl 探测 IP**。原因见 [§18 设计原理](#18-detect_my_ippy本机公网-ip-探测-)。

### 异常处理（🔴 ACL 场景异常处理的唯一权威来源）

| 场景 | 处理 |
|------|------|
| `EsAcl` 字段为空/缺失 | 集群未开通公网访问 → 引导用 `UpdateKibanaPublicAccess` 开启或走控制台 |
| 无法获取本机公网 IP（探测服务全部不可达）| 按 [§18 探测全部失败时](#18-detect_my_ippy本机公网-ip-探测-) 的话术让用户自查后手动提供 |
| 待追加 IP 已在白名单 | 友好提示「已存在，无需添加」，**不调用 tool** |
| 待移除 IP 不在白名单 | 友好提示「不存在」，**不调用 tool** |
| 加完 IP 仍然 403 | 大概率是探测到的 IP 与浏览器实际出口不一致（代理 / 多出口）→ 让用户在浏览器访问 IP 查询站点自报 IP 后重试 |

---

## 9. UpdateKibanaPublicAccess（Kibana 公网访问开关）🌐

- **类型**：🔴 **写操作**
- **功能**：开启或关闭指定 ES 集群的 Kibana **公网**访问地址，底层调用云 API `UpdateInstance` 仅下发 `KibanaPublicAccess`

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `Access` | ✅ | `OPEN`（开启）/ `CLOSE`（关闭）|

### 服务端强制前置检查（1 项）

1. 实例运行状态必须正常（`Status == 1`）

### ⚠️ 安全提示（`Access=OPEN` 时必须向用户说明）

开启后 **Kibana 将对公网暴露访问入口**。必须在确认信息中提示：

```
⚠️ 开启 Kibana 公网访问后，Kibana 入口将暴露在公网上。
强烈建议开启后立即通过 UpdateEsAcl 配置精确的 IP 白名单，避免任意来源访问。
是否继续？
```

> 📌 **推荐组合动作**：`UpdateKibanaPublicAccess(Access="OPEN")` 成功后，主动询问用户是否立刻配置白名单，并引导走 [§8](#8-updateesaclkibana-访问白黑名单-)。

### `Access=CLOSE` 场景

关闭公网访问后，用户将**无法从公网访问 Kibana**（内网访问不受影响）。确认信息中需明示这一点，避免用户误操作后失去访问能力。

---

## 10. UpdateKibanaPrivateAccess（Kibana 内网访问开关）🏠

- **类型**：🔴 **写操作**
- **功能**：开启或关闭指定 ES 集群的 Kibana **内网**访问地址，底层调用云 API `UpdateInstance` 仅下发 `KibanaPrivateAccess`

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `Access` | ✅ | `OPEN`（开启）/ `CLOSE`（关闭）|

### 服务端强制前置检查（1 项）

1. 实例运行状态必须正常（`Status == 1`）

### 说明

- 内网访问仅 VPC 内可达，**安全风险远低于公网访问**
- 典型用途：用户希望只保留内网访问、关闭公网入口时，先 `UpdateKibanaPrivateAccess(OPEN)` 再 `UpdateKibanaPublicAccess(CLOSE)`
- ⚠️ 关闭内网访问前，先确认用户不是**仅**依赖内网入口，否则会失去全部访问能力

---

## 11. DescribeInstanceOperations（变更进度）📋

- **类型**：只读
- **功能**：查询集群在某时间范围内的操作记录，**变更提交后的进度跟踪入口**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `StartTime` | ❌ | 起始时间，格式 **`YYYY-MM-DD HH:mm:ss`**，默认 `2017-01-01 00:00:00` |
| `EndTime` | ❌ | 结束时间，同上格式，默认当前时间 |
| `Limit` | ❌ | 分页大小，默认 20，最大 100 |
| `Offset` | ❌ | 分页起始位置，默认 0 |

> ⚠️ 时间格式是 `YYYY-MM-DD HH:mm:ss`（**无时区、无 T**），与 `GetMonitorData` 的 ISO 8601 不同。
> ⚠️ **不传时间范围会拉取自 2017 年的全部记录**，输出量可能极大。跟踪刚提交的变更时务必显式限定近 1~2 小时。

```
# 跟踪刚提交的变更（Agent 自行计算近 1~2 小时的时间范围）
DescribeInstanceOperations(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                          StartTime="2026-08-18 09:00:00", EndTime="2026-08-18 10:00:00", Limit=20)
```

### 进度解读（🔴 唯一权威来源）

| `Progress` | 状态 | 说明 |
|-----------|------|------|
| `-1` | 🔄 进行中 | 操作正在执行，请等待 |
| `1` | ✅ 成功 | 操作已完成 |
| `0` | ❌ 失败 | 操作失败，查看 `Detail` 字段了解原因 |

> 📌 变更提交后**不要立即查进度**（可能还没生成记录）。建议提示用户「约 1 分钟后可查询进度」，或由用户主动要求时再查。
> 📌 进度长时间为 `-1`（远超预计耗时）→ 提示用户联系腾讯云支持并提供操作 ID，**不要**重复提交变更。

---

## 12. DescribeClusterDiskRange（磁盘上下限）📏

- **类型**：只读
- **功能**：获取指定集群各节点类型的磁盘大小上下限
- **定位**：**磁盘扩容前的可行性校验**

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |

返回各节点类型（`hotData` / `warmData` 等）的磁盘 `Min` / `Med` / `Max`、磁盘数量上下限等约束。

**使用时机**：调用 `UpdateInstanceDiskSize` 前先调本 tool，确认目标 `DiskSize` 落在区间内。虽然服务端也会校验并阻断，但**提前校验能在确认环节就给用户准确的可选范围**，避免"确认完才发现超限"的糟糕体验。

```
用户：「磁盘能扩到多大？」
→ DescribeClusterDiskRange(Region=..., InstanceId=...) → 直接回答区间，不需要试错
```

---

## 13. DescribeUpgrade（可升级版本）⬆️

- **类型**：只读
- **功能**：获取指定 ES 实例可升级的大版本、商业特性与子产品列表

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |

**使用时机**：用户询问版本升级时。**注意版本升级本身暂无 MCP 写 tool**，本 tool 只能做**只读可行性校验**：

```
用户：「帮我把集群升到 7.14.2」
① DescribeUpgrade(Region=..., InstanceId=...)        → 列出可升级的目标版本
② DescribeInstancePluginList(Region=..., InstanceId=...) → 核对已装插件兼容性
③ DescribeClusterSnapshot(Region=..., InstanceId=...)    → 确认有可用备份
④ 明确告知：版本升级暂无 MCP tool 支持，请在腾讯云控制台执行；
   并附上以上三项校验结论作为升级前检查清单
```

> 详见 [unsupported-operations.md](unsupported-operations.md)。

---

## 14. DescribeViews（集群视图）👁️

- **类型**：只读
- **功能**：查询集群视图（集群视图、节点视图、Kibana 视图等）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |

**本 Skill 中的定位**：

- 变更前后的**节点资源快照对比**（扩容后确认新节点已就位）
- 用户不知道节点名时，**查询节点列表供选择**（`RestartNodes` 前置）
- 查看节点级资源使用情况

> ⚠️ **不要用本 tool 做健康诊断与根因分析** —— 那是 `tencent-es-diagnose` 的职责。本 Skill 只用它做变更前后的状态核对。

---

## 15. DescribeInstancePluginList（插件列表）🧩

- **类型**：只读
- **功能**：获取指定集群已安装的插件列表（名称、版本、描述、是否可用、是否可移除）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `PluginType` | ❌ | `0`=系统插件，`1`=用户安装插件。不传返回全部 |
| `Limit` | ❌ | 分页大小，默认 20，最大 100 |
| `Offset` | ❌ | 分页起始位置，默认 0 |
| `OrderBy` | ❌ | 当前支持 `pluginName` |
| `OrderByType` | ❌ | `asc` / `desc` |

**本 Skill 中的定位**：版本升级前的**插件兼容性核对**（用户自装插件常常是版本升级失败的元凶），配合 `DescribeUpgrade` 使用。

---

## 16. DescribeClusterSnapshot（快照备份）💾

- **类型**：只读
- **功能**：获取集群快照备份列表（快照名称、状态、耗时、分片成功/失败数）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `RepositoryName` | ❌ | 快照仓库名，如 `BACKUP`。不填返回全部仓库 |
| `SnapshotName` | ❌ | 快照名称。不填返回全部 |

**本 Skill 中的定位**：**高风险变更前确认存在可用备份**。建议在以下场景主动调用并在确认信息中告知用户最近一次成功快照时间：

- `RestartInstance`（尤其 `UpgradeKernel=true`）
- `UpdateInstanceNodeNum`（涉及分片 rebalance 数据搬迁）
- 引导用户走控制台做版本升级前

```
✅ 最近成功快照：snapshot-20260817（2026-08-17 02:15，分片全部成功）
⚠️ 最近 7 天无成功快照 → 建议先在控制台创建快照再执行本次变更
```

---

## 17. 事件中心三件套 🔔

**类型**：只读。用于变更前确认集群**无进行中的硬件异常 / 智能运维事件**，避免与平台侧操作冲突。

### 17.1 DescribeEsInstanceEventLists（事件列表）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceIds` | ❌ | 集群 ID 列表，查指定集群相关事件 |
| `EventTypes` | ❌ | 事件类型列表：`1` 硬件异常、`2` 用户变更、`3` 智能运维。默认全部 |
| `EventStatus` | ❌ | 事件状态列表，如 `[0,1,2]` |
| `StartTime` | ❌ | `YYYY-MM-DD HH:mm:ss`，默认 `2018-01-01 00:00:00` |
| `EndTime` | ❌ | `YYYY-MM-DD HH:mm:ss`，默认当前时间 |
| `Limit` / `Offset` | ❌ | 分页，默认 20 / 0，Limit 最大 100 |

> ⚠️ 注意 `InstanceIds` 是**可选**的，且本 tool **只要求 `Region`**。不传 `InstanceIds` + 不传时间范围会拉取整个地域自 2018 年的全部事件，输出量极大 —— **务必同时限定 `InstanceIds` 和时间范围**。

### 17.2 DescribeEventDataDetail（事件详情）

| 参数 | 必需 | 说明 |
|------|-----|------|
| `InstanceId` | ✅ | 集群 ID |
| `EventType` | ✅ | `1` 硬件异常 / `2` 用户变更 / `3` 智能运维 |
| `EventTaskId` | ✅ | 异常事件任务 ID（数字），从 17.1 的列表中获取 |

返回事件名称、重要程度、内容、节点、状态、隔离/修复信息等。

### 17.3 DescribeEventInfoList（事件类型字典）

仅需 `Region`。返回事件类型枚举与名称映射，作为 `EventTypes` 取值参考。

### 变更前检查建议

```
DescribeEsInstanceEventLists(Region=..., InstanceIds=["es-xxxxxxxx"],
                            EventTypes=[1,3],
                            StartTime="2026-08-11 00:00:00", EndTime="2026-08-18 10:00:00", Limit=20)
→ 若存在进行中的硬件异常/智能运维事件：
  提示用户「平台侧正在处理 <事件名>，建议等其完成后再发起本次变更，避免冲突」
```

---

## 18. detect_my_ip.py（本机公网 IP 探测）🌍

- **类型**：**本地脚本，零云 API 调用**
- **功能**：按集群地域智能选择探测服务，获取**本机公网出口 IP**，并做安全校验
- **为什么必须保留**：MCP 服务端运行在云侧，**无法感知用户本机的公网出口 IP**。而 Kibana 403 的修复恰恰需要这个 IP

| 参数 | 必需 | 说明 |
|------|-----|------|
| `--region` | ✅ | 集群地域，如 `ap-guangzhou`。**决定使用国内还是海外探测服务** |
| `--output` | ❌ | `json`（默认）/ `text` |
| `--timeout` | ❌ | 单个探测服务超时秒数，默认 5 |

### 设计原理（为什么要按地域选路）

用户访问 Kibana 的浏览器出口 IP 取决于路由策略：

| 集群地域 | 用户典型访问方式 | 应使用的探测服务 |
|---------|---------------|---------------|
| 国内（`ap-guangzhou` / `ap-shanghai` / `ap-beijing` / `ap-chengdu` 等）| 浏览器**直连** | 国内服务（`myip.ipip.net` / `4.ipw.cn` / `ddns.oray.com`）→ 拿到真实国内 ISP 出口 IP |
| 海外（`ap-hongkong` / `ap-singapore` / `ap-tokyo` / `na-*` / `eu-*` / `sa-*` 等）| 通常**走代理** | 境外服务（`ifconfig.me` / `api.ipify.org` / `icanhazip.com`）→ 拿到代理出口 IP |

> 🚨 **如果 Agent 自己 curl 境外服务探测国内集群场景**：本机走代理时会拿到**代理出口 IP**（典型如腾讯云海外段 `43.x.x.x`），而用户浏览器是直连（真实 IP 如电信宽带 `182.x.x.x`）。加进白名单后 tool 返回"成功"，但**Kibana 依旧 403**，且问题极难排查。这就是必须用本脚本的原因。

### 使用示例

```bash
$PYTHON_CMD scripts/detect_my_ip.py --region ap-guangzhou
# → {"ip": "182.x.x.x", "region": "ap-guangzhou", "region_kind": "国内",
#    "source": "集群地域 ap-guangzhou 识别为国内地域，使用国内直连出口（via https://myip.ipip.net）"}

$PYTHON_CMD scripts/detect_my_ip.py --region ap-singapore --output text
# → 182.x.x.x
```

### 内置安全校验

脚本会拒绝返回「全部放开」类地址（`0.0.0.0` / `/0` 掩码 CIDR 等），作为极端情况的兜底。校验规则与 [§8 硬性安全约束](#8-updateesaclkibana-访问白黑名单-) 一致。

### 探测全部失败时（🔴 兜底话术的唯一权威来源）

脚本以非零退出码退出并输出错误 JSON。此时**不要**改用其他方式硬探，而是提示用户：

```
自动探测本机公网 IP 失败（探测服务不可达，可能是网络受限）。
请在浏览器访问 https://myip.ipip.net 或 https://ip138.com 查看你的公网 IP，
然后告诉我，我再帮你加进白名单。
```

---

## 19. forecast_calc.py（容量预测计算）📐

- **类型**：**本地脚本，零云 API 调用**（不读凭证、不做签名、不发起任何网络请求）
- **功能**：把 `GetMonitorData` 的返回做确定性数值计算 —— 哨兵值剔除、线性回归、P50/P95、阈值外推、目标值推荐
- **为什么必须保留**：线性回归需对上百数据点求 Σxy/Σx²，交给 LLM 心算不可靠，且**算错不会报错**，只会给出看似合理的错误天数

| 参数 | 必需 | 说明 |
|------|-----|------|
| stdin | ✅ | `GetMonitorData` 返回的 JSON。支持①单个响应 ②多响应组成的数组 ③已剥掉 `Response` 外层的对象 |
| `--node-num` | ❌ | 目标节点类型的**当前节点数**（取自 `DescribeInstances` 的 `NodeInfoList`）|
| `--disk-size` | ❌ | 目标节点类型的**当前单节点磁盘 GB**（同上）|
| `--disk-type` | ❌ | `LOCAL_SSD` / `CLOUD_PREMIUM` / `CLOUD_SSD` / `CLOUD_HSSD`，决定扩容路径分流 |
| `--node-type` | ❌ | 当前规格，如 `ES.S1.LARGE16`，用于升配推荐 |
| `--node-role` | ❌ | 目标节点类型，默认 `hotData` |
| `--instance-id` | ❌ | 批量返回时只分析该实例 |
| `--output` | ❌ | `json`（默认）/ `text` |

### 使用示例

```bash
# 单指标
<GetMonitorData 返回> | $PYTHON_CMD scripts/forecast_calc.py \
  --node-num 3 --disk-size 300 --disk-type CLOUD_SSD

# 多指标一次算完（把多个响应放进一个 JSON 数组）
cat metrics.json | $PYTHON_CMD scripts/forecast_calc.py \
  --node-num 3 --disk-size 300 --disk-type CLOUD_SSD \
  --node-type ES.S1.LARGE16 --node-role hotData --output text
```

### 输出结构

```json
{
  "cluster_context": { "node_num":3, "disk_size_per_node_gb":300,
                       "total_storage_gb":900, "can_expand_disk":true, ... },
  "metrics": { "DiskUsageMax": { "current":71.67, "p50":..., "p95":...,
      "slope_per_day":0.24, "trend":"上升",
      "days_to_critical":{"days":34.7,"note":""},
      "valid_points":168, "raw_points":168, "sentinel_dropped":0,
      "confidence":"normal", "status":"warn" } },
  "recommendations": [ { "priority":1, "type":"expand_disk", "urgency":"🟠 建议",
      "tool":"UpdateInstanceDiskSize",
      "tool_args":{"Type":"hotData","DiskSize":400},
      "calc":"300 × 71.67% / 0.6 = 358.4 → 向上取整百位 → 400",
      "must_verify":"调用前用 DescribeClusterDiskRange 确认落在 Min/Max 区间" } ]
}
```

### 🔑 关键：`tool_args` 已是目标值

`recommendations[].tool_args` 可**直接**用作 MCP tool 入参，无需再做增量换算 —— 这也顺带消除了「增量当目标值传」这个最高频错误。

```
脚本输出 tool_args={"Type":"hotData","DiskSize":400}
  → 展示确认信息 → 用户确认
  → UpdateInstanceDiskSize(Region=..., InstanceId=..., Type="hotData", DiskSize=400)
```

### 关键行为

| 行为 | 说明 |
|------|------|
| 哨兵值剔除 | 自动丢弃 `value < 0` 的点，并在 `sentinel_dropped` 中报告数量 |
| 外推基准 | 用**最后一个有效数据点时间**而非 `now()`，避免历史区间外推失真 |
| 无法外推 | `slope<=0` / 点数<2 / 外推超 10 年时返回 `days:null` + `note` 说明原因 |
| 置信度 | 有效点 < 总点数 50%、或有效点 < 10 时标记 `confidence:"low"` |
| 本地盘保护 | `LOCAL_SSD` 时**不会**推荐扩磁盘，只推荐加节点 |
| 区间封顶 | 目标节点数超上限时封顶并在 `capped_note` 说明 |
| 单次单一变更 | 多条可执行建议时，为第 2 条起注入 `serial_note` 提醒串行执行 |
| 异常输入 | 非法 JSON / 空输入 / 无 `DataPoints` 时**非零退出码报错**，不静默返回错误结果 |

> ⚠️ 脚本只做计算与建议，**不执行任何变更**。变更仍须 Agent 展示详情、用户确认后调用 MCP tool。

---

## 附录：通用约定与错误码

### 通用约定

- 所有 tool 均需 `Region` 参数
- 所有变更类 tool **一调即真实下发，无 dry-run**。二次确认**完全由 Agent 在对话中负责**，无任何脚本层兜底
- 服务端前置检查失败时返回明确阻断原因 → **如实转述给用户，不要重试、不要换参数硬闯**
- 变更类 tool 的 `NodeInfoList` 由服务端自动查询回填，调用方无法传入
- 鉴权在宿主层完成，Skill 层不存在任何密钥

### 时间格式对照（易错）

| Tool | 格式 | 示例 |
|------|------|------|
| `GetMonitorData` | ISO 8601 / RFC3339（带时区）| `2026-08-18T10:00:00+08:00` |
| `DescribeInstanceOperations` | `YYYY-MM-DD HH:mm:ss` | `2026-08-18 10:00:00` |
| `DescribeEsInstanceEventLists` | `YYYY-MM-DD HH:mm:ss` | `2026-08-18 10:00:00` |

### 错误码

| 错误码 | 含义 | 处理 |
|-------|------|------|
| `AuthFailure` / `AuthFailure.*` | CAM 权限不足或凭证问题 | 提示用户确认连接器所用账号具备 `es:*` / `monitor:GetMonitorData` 权限；必要时重连连接器 |
| `UnauthorizedOperation` | 无权限 | 同上，检查 CAM 策略 |
| `ResourceNotFound.InstanceNotExist` | 集群不存在 | 确认集群 ID 与地域是否匹配 |
| `InvalidParameter` / `InvalidParameterValue` | 参数错误 | 核对参数格式（尤其时间格式、数组类型、枚举值）|
| `RequestLimitExceeded` | 接口限频 | 稍后重试，避免高频轮询进度 |
| `FailedOperation` | 操作失败 | 集群当前状态可能不允许，查看返回消息 |
| `InternalError` | 内部错误 | 稍后重试或联系腾讯云支持 |
| MCP tool 不可用 / 调用报连接错误 | 连接器未配置/未连接 | 提示用户在连接器管理页面配置并连接；**禁止用 tccli 等方式绕行** |

