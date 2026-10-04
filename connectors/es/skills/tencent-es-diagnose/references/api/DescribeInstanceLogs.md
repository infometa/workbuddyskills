# DescribeInstanceLogs（MCP）

> Tool：`DescribeInstanceLogs` | MCP tool | 只读

## 功能描述

获取指定集群运行日志，用于分析 ERROR/WARN 日志、慢查询与 GC 行为。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Region` | String | ✅ | 地域，如 `ap-guangzhou` |
| `InstanceId` | String | ✅ | 集群 ID，如 `es-xxxxxxxx` |
| `LogType` | Number | ❌ | 日志类型，默认 1。取值见下表 |
| `LogLevels` | String[] | ❌ | **日志级别过滤**，枚举 `DEBUG` / `INFO` / `WARN` / `ERROR`，如 `["WARN","ERROR"]`。不传则不按级别过滤 |
| `SearchKey` | String | ❌ | **搜索词，支持 LUCENE 语法**，如 `level:WARN`、`ip:1.1.1.1`、`message:test-index`、`level:INFO OR level:WARN` |
| `StartTime` | String | ❌ | 日志开始时间，格式 **`YYYY-MM-DD HH:mm:ss`**。不传则不限制起始时间 |
| `EndTime` | String | ❌ | 日志结束时间，格式同上。不传则不限制结束时间 |
| `Limit` | Number | ❌ | 分页大小，默认 100，**最大 100** |
| `Offset` | Number | ❌ | 分页起始位置，默认 0 |
| `OrderByType` | Number | ❌ | 时间排序：`0`=降序（最新日志在前，默认），`1`=升序 |

> ⚠️ **时间格式易错**：本 tool 用 `YYYY-MM-DD HH:mm:ss`（无 `T`、无时区），与 `GetMonitorData` 的 ISO 8601（`2026-08-05T19:00:00+08:00`）**不同**，不要混用。与 `DescribeInstanceOperations` 的格式一致。

### LogType 取值（本表是 LogType 语义的唯一权威来源）

| LogType | 含义 |
|---------|------|
| 1 | 主日志（默认）：集群运行日志，含 ERROR/WARN/INFO |
| 2 | **搜索慢日志**：查询耗时超阈值的日志 |
| 3 | **索引慢日志**：写入耗时超阈值的日志 |
| 4 | **GC 日志**：JVM 垃圾回收日志 |

> 🔴 **查 GC 日志必须用 `LogType=4`。**
>
> 搜索慢日志与索引慢日志是**两个独立类型**（2 和 3），排查"查询慢"用 `2`，排查"写入慢"用 `3`；
> 两者都要看时需分别调用两次，没有"合并慢日志"这个取值。

## 调用示例

```
# 查主日志
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=1)

# 查搜索慢日志（查询慢）
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=2)

# 查索引慢日志（写入慢）
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=3)

# 查 GC 日志
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=4)

# ✅ 推荐：只取近 24h 的 ERROR/WARN（级别 + 时间窗双重下推）
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=1,
                     LogLevels=["ERROR","WARN"],
                     StartTime="2026-08-31 10:00:00", EndTime="2026-09-01 10:00:00",
                     Limit=100)

# ✅ 推荐：直接检索磁盘只读阻塞关键字
DescribeInstanceLogs(Region="ap-guangzhou", InstanceId="es-xxxxxxxx", LogType=1,
                     SearchKey="message:read_only_allow_delete",
                     StartTime="<起>", EndTime="<止>")
```

## 返回字段（关键）

| 字段 | 说明 |
|------|------|
| `TotalCount` | 匹配日志总数 |
| `InstanceLogList[].Time` | 日志时间（**UTC+8**）|
| `InstanceLogList[].Ip` | 产生日志的节点 IP |
| `InstanceLogList[].Message` | 日志内容 |
| `InstanceLogList[].Level` | 日志级别（主日志有，GC 日志无）|

## 常见 ERROR 关键词及含义

| 关键词 | 可能原因 |
|--------|---------|
| `OutOfMemoryError` | JVM 堆内存不足 |
| `CircuitBreakingException` | 内存熔断，查询/写入被拒绝 |
| `read_only_allow_delete` / `DiskWatermarkException` | 磁盘水位触发只读 |
| `flood_stage` | 磁盘 flood watermark，已强制只读 |
| `DiskThresholdMonitor` | 磁盘水位监视器告警 |
| `FORBIDDEN` | 磁盘/只读类阻塞错误 |
| `ShardLockObtainFailedException` | 分片锁获取失败，可能有节点重启 |
| `ClusterBlockException` | 集群被阻塞（磁盘满/只读模式）|
| `master_not_discovered` | Master 节点未发现 |
| `rejected execution` | 线程池队列满 |

> 📌 打分规则 1f 使用的磁盘阻塞关键字集合：`read_only_allow_delete`、`FORBIDDEN`、`DiskThresholdMonitor`、`flood_stage`（单 token 匹配，≥5 条触发 ≤30 分一票否决）。

## ✅ 过滤必须下推到接口（不要拉全量再本地过滤）

日志量可能极大。`LogLevels` / `SearchKey` / `StartTime` / `EndTime` / `Limit` 均已支持，**能下推的过滤条件一律下推**，减少返回体积与上下文占用：

| 需求 | ✅ 正确做法（下推） | ❌ 错误做法 |
|------|------------------|-----------|
| 统计 ERROR/WARN 数量 | `LogLevels=["ERROR","WARN"]` + 时间窗，取返回的 `TotalCount` | 拉 `LogType=1` 全量后按 `Level` 字段本地计数 |
| 检索磁盘只读关键字 | `SearchKey="message:read_only_allow_delete"`（其余关键字同理逐个查）| 拉全量后在 `Message` 里做子串匹配 |
| 限定时间窗口 | `StartTime` / `EndTime`（`YYYY-MM-DD HH:mm:ss`）| 拉全量后按 `Time` 字段本地过滤 |
| 定位某节点的日志 | `SearchKey="ip:10.0.0.1"` | 拉全量后按 `Ip` 字段筛 |

> 📌 `TotalCount` 是**匹配条数**而非返回条数。带 `LogLevels` / `SearchKey` 过滤后，直接读 `TotalCount` 即可得到计数，**无需翻页取全量**。
> ⚠️ `LogLevels` 与 `SearchKey` 可同时使用；`SearchKey` 走 LUCENE 语法，也可用 `level:ERROR` 表达级别过滤，但**优先用 `LogLevels`**（枚举校验更明确）。
> ⚠️ **GC 日志（`LogType=4`）无 `Level` 字段**，对其传 `LogLevels` 无意义 —— 应改用 `SearchKey`（如 `message:Full GC`）。

> 💡 判定磁盘打满时，**仍优先用 `CesGetAllocation` + `CesClusterHealth` 数据面直连核实**（不受探针失联影响），日志关键字作为辅助证据。

## 其他注意事项

- 返回时间为 **UTC+8**
- GC 日志无 `level` 字段，不要按 `level:ERROR` 的思路去匹配，应找 `Full GC` / `allocation failure`
- 只查主日志（`LogType=1`）就下结论是典型错误 —— GC 与慢查询在其他类型里
- 「查询慢」查 `LogType=2`、「写入慢」查 `LogType=3`，**不要用一次调用代替两者**
- `Limit` 最大 100；匹配条数超 100 时优先**收窄过滤条件**（级别 / 关键字 / 时间窗），而非用 `Offset` 反复翻页

## 错误码

| 错误码 | 含义 |
|------|------|
| `AuthFailure.*` | CAM 权限不足，需授予 `es:DescribeInstanceLogs` |
| `ResourceNotFound.InstanceNotExist` | 集群 ID 不存在或地域不匹配 |
| `InvalidParameter.*` | `LogType` 不在 [1,4] 范围；`LogLevels` 含非枚举值；时间格式不是 `YYYY-MM-DD HH:mm:ss`；`Limit` > 100 |
