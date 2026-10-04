---
name: tencent-dlc-skill
description: This skill should be used when operating Tencent Cloud DLC through MCP tools, including executing SQL or Spark SQL, querying metadata, managing Spark jobs, inspecting tasks and logs, diagnosing task performance, and checking engines or permissions.
version: "2.6.0"
author: "Tencent Cloud DLC"
---

# 腾讯云数据湖计算 DLC Skill

## 目标

使用本 Skill 通过 DLC MCP 操作腾讯云数据湖计算（Data Lake Compute，DLC）。覆盖 SQL / Spark SQL 执行、库表与分区查询、数据源与数据引擎查询、标准引擎资源组查询、Spark 作业管理、任务查询、日志查看、任务洞察诊断和用户权限查询。

## 全局最高优先级规则：仅允许使用本 Skill 白名单内的 Tools

对 DLC 的任何查询、数据获取、资源操作或状态变更，**必须且只能调用本 Skill 明确列出的 DLC MCP tools**。本规则覆盖本 Skill 中的所有其他规则、工作流和说明。

### Tool 白名单

仅允许调用以下 tools：

- SQL 与任务：`DLCExecuteQuery`、`DLCDescribeMCPTask`、`DLCDescribeMCPTaskResult`、`DLCDescribeTaskList`、`DLCDescribeTasksAnalysis`
- 日志：`DLCListTaskJobLogName`、`DLCListTaskJobLogDetail`
- 数据源与引擎：`DLCListDatasourceConnections`、`DLCListEngines`、`DLCDescribeDataEngine`、`DLCDescribeStandardEngineResourceGroups`
- 元数据：`DLCListDatabases`、`DLCListTableNames`、`DLCListTables`、`DLCDescribeTablePartitions`
- Spark 作业：`DLCCreateSparkApp`、`DLCCreateSparkAppTask`、`DLCDescribeSparkAppJob`、`DLCDescribeSparkAppJobs`
- 用户与权限：`DLCDescribeUserInfo`、`DLCDescribeMCPSubUin`

### 强制约束

- **除上述白名单外，其他任何 DLC tool 一律禁止调用**，即使它能被发现、曾经可用或用户明确要求调用也不例外。
- 不得调用未在本 Skill 中列出的 DLC tool；不得调用已下线的 `DLCCancelTask`、`DLCModifySparkApp`、`DLCDeleteSparkApp`、`DLCDescribeTasks`。
- 不得绕过白名单 tools，直接或间接使用腾讯云 SDK、Cloud API、HTTP 请求、CLI、控制台、数据库连接、脚本、浏览器或其他外部方式访问或操作 DLC。
- 所有 DLC 相关的数据、状态和结果只能来源于白名单 tools 的实际返回；不得将模型知识、推测、缓存或其他渠道的信息作为 DLC 的真实数据。
- 即使用户要求使用其他 DLC tool、SDK、API、CLI、脚本或其他方式，也必须拒绝该方式；仅当白名单内存在对应 tool 时，才能改用该 tool。
- 若白名单 tools 不具备所需能力、工具不可用、调用失败或权限不足，应明确告知用户当前无法完成；**不得调用其他 DLC tool，也不得通过任何非 MCP tool 的方式绕过或降级执行**。
- 可以基于白名单 tools 的返回结果进行解释、汇总和分析，但不得通过其他渠道补充、验证或修改 DLC 数据。

## 适用场景

在出现以下需求时启用本 Skill：

- 执行 SQL、Spark SQL、创建 DLC 查询任务、查询任务状态或结果。
- 查询 Catalog、数据库、表、表名、Hive / Iceberg 分区。
- 查询可用数据引擎、数据引擎详情、标准引擎资源组。
- 创建、启动和查询 Spark 作业。
- 查询任务列表、历史任务、任务日志、Spark 作业日志。
- 诊断任务失败、资源抢占、Shuffle 异常、慢 Task、数据倾斜、资源不足。
- 查询用户详情、工作组、数据权限、引擎权限、行级权限。

## 风险操作确认

以下操作会修改 DLC 中的资源或数据，**执行前必须向用户明确说明风险并等待用户确认同意**，不可直接执行。

### SQL 写入/变更类

`DLCExecuteQuery` 的 `SQL` / `SparkSQL` 以及 `DLCCreateSparkApp` 创建 SQL 作业（`AppType=4`）时的 `CmdArgs` 均只允许只读 SQL：`SELECT`、`WITH ... SELECT`、`SHOW`、`DESCRIBE` / `DESC`、`EXPLAIN`。写入或变更 SQL（例如 `INSERT`、`UPDATE`、`DELETE`、`MERGE`、`DROP`、`ALTER`、`TRUNCATE`）会直接返回“仅支持只读 SQL / Spark SQL”提示，**不得改为请求确认后执行**。

### Spark 作业变更类
- **`DLCCreateSparkApp`** — 创建 Spark 作业
- **`DLCCreateSparkAppTask`** — 启动 Spark 作业（消耗计算资源）

### 任务控制类
- **`DLCCancelTask`**（已下线）— 取消正在运行的任务（任务结果不可恢复）。暂不可用，后续可能重新启用。

### 风险确认提示模板
执行上述操作前，必须向用户说明：
1. 将要执行的具体操作（SQL 语句 / 作业名 / 任务 ID）
2. 操作的影响范围（涉及的表、数据库、引擎）
3. 是否可逆（如 DELETE 不可逆、DROP 不可逆）
4. 明确询问："是否确认执行？"

**只读操作无需确认**（如 `DLCListEngines`、`DLCDescribeMCPTask`、`DLCDescribeUserInfo`、`DLCDescribeMCPSubUin` 等查询类工具）。

## 任务轮询频率限制

`DLCExecuteQuery` 提交任务后需通过 `DLCDescribeMCPTask` 轮询任务状态。为避免对后端造成压力，**严格限制轮询频率**：

- 轮询 QPS：**严格限制为 1**（即每秒最多 1 次调用），建议间隔 3~5 秒。
- 总轮询次数：**最多 60 次**（约 3~5 分钟）。超过后告知用户任务仍在执行中，提供 TaskId 供稍后手动查询。
- `DLCDescribeMCPTask` 已包含结果预览（`DataSet` 字段），大多数场景无需再调用 `DLCDescribeMCPTaskResult`。只有在结果被截断（`IsSQLCutOff=true`）或需要完整结果集时，才调用 `DLCDescribeMCPTaskResult`。
- `DLCDescribeMCPTaskResult` 单次最多返回 **1000 行**。当前 tool 不接受 `NextToken` 入参，不能继续获取后续页；结果被截断时应明确告知用户。
- 如果用户短时间内（如 1 分钟内）连续提交多个 SQL，应提示用户等待前一个任务完成后再提交下一个。

## 通用约定

### 必填参数

- **Region**：所有工具的第一个必填参数，跨地域 per-user 模型，每次调用均需传入（如 `ap-guangzhou`、`ap-shanghai`）。

### 默认值

- 使用 `DataLakeCatalog` 作为默认 `DatasourceConnectionName` / `Catalog`。
- 不假设全局分页默认值；每个 tool 的默认值以其详细说明为准。
- 常规列表单次查询建议 `Limit<=100`；日志详情建议 `Limit<=1000`。
- 时间范围使用 `yyyy-MM-dd HH:mm:ss`，日志详情使用 Unix 毫秒时间戳。
- `Sorting` 使用 `desc` 或 `asc`；`Asc` 使用 `true`/`false`。

### 任务状态

前端任务状态（用于状态过滤）：

| 值 | 含义 |
|---:|---|
| `0` | 初始化 |
| `1` | 运行中 |
| `2` | 成功 |
| `3` | 数据写入中 |
| `4` | 排队中 |
| `-1` | 失败 |
| `-2` | 删除中 |
| `-3` | 已删除 |
| `-5` | 已过期 |
| `-6` | 运行超时 |
| `-10` | 未初始化 |

后端任务状态（`DLCDescribeMCPTask` 返回的 `State`）：

| 值 | 状态 |
|---:|---|
| `1` | `TaskInit` |
| `3` | `TaskSubmited` |
| `4` | `ResourceApplying` |
| `5` | `Computing` |
| `8` | `Blocking` |
| `9` | `Queued` |
| `0` | `TaskFinished` |
| `-1` | `TaskFailed` |
| `-2` | `TaskDeleting` |
| `-3` | `TaskDeleted` |
| `-4` | `TaskExpiration` |
| `-5` | `TaskExpired` |
| `-6` | `TaskRunTimeout` |
| `-8` | `TaskCanceled` |
| `-9` | `TaskDeleteFailed` |

### 任务类型（TaskType）

DLC 任务的 `TaskType` 取值如下：

| 值 | 含义 |
|---|---|
| `SQLTask` | 交互式 SQL 任务 |
| `SparkSQLTask` | Spark SQL 任务 |
| `BatchSQLTask` | 批 SQL 任务（Session） |
| `SparkTask` | Spark 任务 |
| `ImportTask` | 数据导入任务 |
| `ExportTask` | 数据导出任务 |
| `GuldanScheduleTask` | 周期调度任务 |
| `StandardSparkSQLTask` | 标准引擎（253 通用引擎）Spark Session SQL |
| `StandardPrestoSQLTask` | 标准引擎（253 通用引擎）Presto SQL |
| `SparkBatchTask` | Spark 批任务 |
| `SparkBatchSQL` | Spark 批 SQL |
| `SparkStreamingTask` | Spark 流任务 |
| `SparkNotebookTask` | Spark Notebook 任务 |
| `SparkPythonTask` | Spark Python 任务 |
| `InvalidTask` | 无效任务 |

> 注：`GovernSparkTask` / `GovernSparkSQLTask` / `GovernSparkBatchTask` / `StandardGovernSparkSQLTask` 为数据治理任务类型（仅前端查询使用，任务列表中不出现）。

### 作业类型（Spark 作业子渠道）

Spark 作业按作业类型分为三类，对应关系如下（在 `DLCDescribeTaskList` / `DLCDescribeMCPTask` 返回的 `SourceExtra` 中体现）：

| 作业类型 | 对应任务类型 | 说明 |
|---|---|---|
| `批处理`（Batch Processing） | `SparkBatchTask` | 批作业 |
| `流处理`（Stream Processing） | `SparkStreamingTask` | 流作业 |
| `SQL作业`（SQL Job） | `SparkBatchSQL` | SQL 作业 |

### 引擎类型（EngineType）

**执行引擎类型**（任务/引擎过滤中的 `ExecEngine` 或 `EngineType`）：

| 值 | 含义 |
|---|---|
| `SPARK` | Spark 引擎 |
| `PRESTO` | Presto 引擎 |
| `HIVE` | Hive 引擎 |
| `EOS` | EOS 引擎 |
| `STANDARD_SPARK` | 标准引擎 - Spark |
| `STANDARD_PRESTO` | 标准引擎 - Presto |
| `INVALID` | 无效类型 |

**数据引擎类型**（`DLCListEngines` / `DLCDescribeDataEngine` 返回的引擎类型）：

| 值 | 含义 |
|---|---|
| `SparkSQL` | Spark SQL 引擎 |
| `PrestoSQL` | Presto SQL 引擎 |
| `SparkBatch` | Spark 批处理引擎 |
| `StandardSpark` | 标准引擎 - Spark |
| `StandardPresto` | 标准引擎 - Presto |
| `Kyuubi` | Kyuubi 引擎 |
| `StarRocks` | StarRocks 引擎 |

**标准引擎（Standard Engine）**：指 Native（原生/新一代，253 通用引擎）代际的引擎，属于标准引擎的引擎类型只有两种：

- `StandardSpark`：引擎类型 `spark` + 代际 Native
- `StandardPresto`：引擎类型 `presto` + 代际 Native

对应执行引擎类型为 `STANDARD_SPARK` / `STANDARD_PRESTO`。其余类型（`SparkSQL`、`PrestoSQL`、`SparkBatch`、`Kyuubi`、`StarRocks` 等）不属于标准引擎。

### 返回结果枚举

各接口返回结果中的固定枚举值速查。

**任务结果**（`DLCDescribeMCPTaskResult` / `DLCDescribeMCPTask` 返回的 `SQLType`、`State`、`DisplayFormat`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `SQLType` | `DDL` / `DML` / `DQL` | SQL 类型（部分接口细分为 `SELECT` / `INSERT` / `UPDATE` / `DELETE` / `Other`） |
| `State` | `0` | 初始化 |
| | `1` | 任务运行中 |
| | `2` | 执行成功 |
| | `3` | 数据写入中 |
| | `4` | 排队中 |
| | `-1` | 执行失败 |
| | `-3` | 用户手动终止 / 已取消 |
| `DisplayFormat` | `table` / `text` | 控制台展示格式：表格 / 文本 |

**引擎**（`DLCListEngines` / `DLCDescribeDataEngine` 返回 `DataEngineInfo`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `EngineType` | `spark` / `presto` | 引擎类型 |
| `ClusterType` | `spark_private` / `presto_private` / `presto_cu` / `spark_cu` | 集群资源类型 |
| `State` | `-2` | 已删除 |
| | `-1` | 失败 |
| | `0` | 初始化中 |
| | `1` | 挂起 |
| | `2` | 运行中 |
| | `3` | 准备删除 |
| | `4` | 删除中 |
| `Mode` | `0` / `1` / `2` | 计费模式：共享模式 / 按量计费 / 包年包月 |
| `EngineExecType` | `SQL` / `BATCH` | 引擎执行任务类型 |
| `EngineTypeDetail` | `SparkSQL` / `PrestoSQL` / `SparkBatch` / `StandardSpark` / `StandardPresto` | 引擎详细类型 |
| `CrontabResumeSuspend` | `0` / `1` | 定时启停策略：关闭 / 开启 |
| `RenewFlag` | `0` / `1` / `2` | 自动续费：初始状态 / 自动续费 / 明确不自动续费 |

**Spark 作业**（`DLCDescribeSparkAppJob(s)` 返回 `SparkJobInfo`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `JobType` | `1` / `2` | 作业类型：`1`=batch 批作业，`2`=streaming 流作业 |
| `JobStatus` | `0` | 初始化 |
| | `1` | 运行中 |
| | `2` | 成功 |
| | `3` | 数据写入中 |
| | `4` | 排队中 |
| | `-1` | 失败 |
| | `-3` | 已删除 |
| | `-5` | 已过期 |
| `DataEngineStatus` | `-100` | 默认未知状态 |
| | `-2` ~ `11` | 引擎正常状态 |
| `IsLocal` / `IsLocalJars` / `IsLocalFiles` | `cos` / `lakefs` | 依赖上传方式 |
| `IsLocalPythonFiles` / `IsLocalArchives` | `1` / `2` | 依赖上传方式：`1`=cos，`2`=lakefs |
| `IsInherit` | `0` / `1` | 是否继承集群模板：不继承 / 继承 |

**数据源**（`DLCListDatasourceConnections` 返回 `DatasourceConnectionInfo`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `DatasourceConnectionType` | `DataLakeCatalog` / `IcebergCatalog` / `Result` / `Mysql` / `HiveCos` / `HiveHdfs` | 数据源类型 |
| `State` | `0` | 初始化 |
| | `1` | 成功 |
| | `-1` | 已删除 |
| | `-2` | 失败 |
| | `-3` | 删除中 |
| `ConnectivityState` | `0` / `1` / `2` | 连通性：未测试 / 正常 / 失败 |

**元数据**（`DLCListTables` 返回 `TableInfo`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `Type` | `TABLE` / `VIEW` | 表类型：表 / 视图 |
| `TableFormat` | `hive` / `iceberg` 等 | 数据格式类型 |
| `DataFormat` | `TextFile` / `CSV` / `Json` / `Parquet` / `ORC` / `AVRD` | 数据表文件格式 |

**用户信息**（`DLCDescribeUserInfo` 返回 `UserDetailInfo`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `Type` | `Group` / `DataAuth` / `EngineAuth` / `RowFilter` | 返回的信息类型：工作组 / 数据权限 / 引擎权限 / 行过滤 |
| `UserType` | `ADMIN` / `COMMON` | 用户类型：管理员 / 一般用户 |

**洞察分析**（`DLCDescribeTasksAnalysis` 返回 `AnalysisTaskResults`）：

| 字段 | 取值 | 说明 |
|---|---|---|
| `State` | `0` / `1` / `2` / `3` / `4` / `-1` / `-3` | 任务状态：初始化 / 执行中 / 执行成功 / 数据写入中 / 排队中 / 执行失败 / 已取消 |
| `AnalysisStatus` | `SPARK-StageScheduleDelay` | 资源抢占 |
| | `SPARK-ShuffleFailure` | Shuffle 异常 |
| | `SPARK-SlowTask` | 慢 task |
| | `SPARK-DataSkew` | 数据倾斜 |
| | `SPARK-InsufficientResource` | 磁盘或内存不足 |

> 注：`AnalysisStatus` 为 JSON 数组字符串，一次可能包含多种类型；`DLCDescribeTasksAnalysis` 的 `Filter.Key` 支持 `task-id`、`task-state`（`0` 初始化、`1` 执行中、`2` 执行成功、`-1` 执行失败）、`rule-id`（洞察类型）。

### Filter 格式

使用以下结构传递过滤条件：

```json
{
  "Key": "task-id",
  "Values": ["task-xxx"]
}
```

常见 `Filter.Key`：

| Key | 说明 |
|---|---|
| `task-id` | 任务 ID |
| `task-sql-keyword` | SQL 关键字 |
| `task-state` | 任务状态 |
| `batch-id` | 批次 ID |
| `data-engine-name` | 数据引擎名称 |
| `data-engine-name-unique` | 精确数据引擎名称 |
| `engine-id` | 引擎 ID |
| `state` | 状态 |
| `engine-type` | 引擎类型 |
| `engine-exec-type` | 引擎执行类型 |
| `engine-generation` | 引擎代际 |
| `rule-id` | 洞察规则 ID |
| `keyword` | 通用关键字 |
| `task-name` | 任务名 |
| `task-source` | 任务来源 |
| `task-source-extra` | 任务子来源 |
| `spark-job-name` / `job-name` | Spark 作业名 |
| `spark-job-id` | Spark 作业 ID |
| `key-word` | Spark 作业名或 ID 关键字 |

## 核心工作流（工具调用顺序）

### 工作流 A：创建异步 SQL 任务并获取结果

```
DLCListEngines（若未指定引擎）
  → DLCExecuteQuery（异步创建任务，仅返回 TaskId）
  → DLCDescribeMCPTask（使用 TaskId 轮询任务状态）
  → [State=0，任务完成] DLCDescribeMCPTask（读取 DataSet 结果预览）
  → [需要完整结果] DLCDescribeMCPTaskResult（查询完整结果集）
  → [SQL 失败] DLCDescribeMCPTask（读取 OutputMessage）
  → [Spark 类任务失败] DLCListTaskJobLogName → DLCListTaskJobLogDetail（查日志）
  → [Spark 性能异常] DLCDescribeTasksAnalysis（诊断分析）
```

**注意事项**：
- `DLCExecuteQuery` 创建任务是**异步**操作：调用后只返回 `TaskId`，不等待任务执行完成，也不返回查询结果。
- 拿到 `TaskId` 后，必须调用 `DLCDescribeMCPTask` 查询并轮询任务状态：后端状态 `0`（`TaskFinished`）表示任务已完成；`-1`（`TaskFailed`）、`-6`（`TaskRunTimeout`）等表示任务失败或异常终止。
- 仅在任务完成（`State=0`）后，使用 `DLCDescribeMCPTask` 返回的 `DataSet` 预览结果；任务尚未完成时应继续按频率限制轮询，不应调用结果查询接口。
- 需要完整结果集、结果预览被截断（`IsSQLCutOff=true`）或用户明确要求结果 Schema 时，在任务完成后调用 `DLCDescribeMCPTaskResult`。
- `DLCDescribeMCPTaskResult` 单次最多返回 1000 行；当前 tool 不支持传入 `NextToken` 获取后续页。
- **轮询 QPS 严格限制为 1**（每秒最多 1 次），详见「任务轮询频率限制」章节。
- 根据 SQL 类型选择引擎：Presto / SQL 引擎用于普通 SQL，Spark 引擎用于 Spark SQL。

### 工作流 B：元数据发现

```
DLCListDatasourceConnections（若未指定数据源，获取可用数据源列表）
  → DLCListDatabases（获取数据库列表）
  → DLCListTableNames（获取表名列表）
  → DLCListTables（传入非空 TableNames 数组，批量获取表详情）
  → DLCDescribeTablePartitions（获取分区列表）
```

**注意事项**：
- 如果用户未提供 `DatabaseName` 或表名，按上述顺序通过 tools 获取；如果用户已明确提供，可直接调用对应查询 tool。
- `DLCListDatabases` 的 `DatasourceConnectionName` 未传时默认为 `DataLakeCatalog`。
- `DLCListTableNames` 用于浏览表名；将所需表名组成非空 `TableNames` 数组传给 `DLCListTables`，可批量查询表结构。
- `DLCDescribeTablePartitions` 的 `Limit+Offset` 超过 10000 时可能报结果过大错误；Iceberg 非托管表可能返回空分区。
- 分区数量极大时，建议改用 SQL（`SELECT DISTINCT partition_col FROM table`）而非分区接口。

### 工作流 C：Spark 作业全生命周期

```
DLCListEngines（确认可用 Spark 引擎）
  → DLCCreateSparkApp（创建作业，返回 SparkAppId）
  → DLCCreateSparkAppTask（启动作业，返回 TaskId / BatchId）
  → DLCDescribeMCPTask（查询任务状态）
  → [仅需完整结果或 Schema] DLCDescribeMCPTaskResult（单次最多获取 1000 行）
  → [失败] DLCListTaskJobLogName → DLCListTaskJobLogDetail（查日志）
  → [诊断] DLCDescribeTasksAnalysis
```

**注意事项**：
- `DLCCreateSparkApp` 的 `AppType`：`1` = 批处理、`2` = 流处理、`3` = Python、`4` = SQL 作业。
- 创建 SQL 作业时，必须在 `CmdArgs` 中传入 SQL 原文；仅允许只读查询，Tool 校验通过后会自动进行 Base64 编码。
- `DLCCreateSparkAppTask` 需要 `JobName`（作业名），后端按名称查询唯一 Spark 作业。
- `DLCModifySparkApp` 和 `DLCDeleteSparkApp` 不在 Tool 白名单内，禁止调用。
- Spark 作业日志使用 `DLCListTaskJobLogName` + `DLCListTaskJobLogDetail`；SQL 任务失败优先查看 `DLCDescribeMCPTask` 的 `OutputMessage`。

### 工作流 D：任务排查与诊断

```
DLCDescribeMCPTask（查任务详情：状态、SQL、引擎、耗时、输出消息及结果预览）
  → [仅需完整结果或 Schema] DLCDescribeMCPTaskResult（单次最多获取 1000 行）
  → [失败时] DLCListTaskJobLogName（获取日志文件名）
  → DLCListTaskJobLogDetail（分页读取日志内容）
  → DLCDescribeTasksAnalysis（Spark 任务性能诊断）
```

**注意事项**：
- 日志查询时间范围（`StartTime` / `EndTime`）用 Unix 毫秒时间戳，建议围绕任务创建时间设窗口。
- 日志详情支持 `Context` 游标翻页，`ListOver=true` 表示已全部返回。
- 当前日志 tools 不支持 `LogScene` 入参，不得传入该参数。
- `DLCDescribeTasksAnalysis` 按 RuleId 诊断：`SPARK-StageScheduleDelay`（资源抢占）、`SPARK-ShuffleFailure`（Shuffle 异常）、`SPARK-SlowTask`（慢 Task）、`SPARK-DataSkew`（数据倾斜）、`SPARK-InsufficientResource`（资源不足）。

### 工作流 E：权限与引擎查询

```
DLCListEngines（获取引擎列表）
  → DLCDescribeDataEngine（查引擎详情：状态、规格、VPC 等）
  → DLCDescribeStandardEngineResourceGroups（查资源组）
  → DLCDescribeUserInfo（查用户权限）
```

**注意事项**：
- `DLCDescribeUserInfo` 的 `Type` 使用 tool 明确描述的值：`Group`（工作组）、`DataAuth`（数据权限）、`EngineAuth`（引擎权限）、`RowFilter`（行级过滤）。
- `DLCDescribeStandardEngineResourceGroups` 的 `DataEngineName` 为可选过滤条件；未指定时可查询资源组列表。

---

## 各工具详细说明

### SQL 执行

#### `DLCExecuteQuery`

异步提交**只读 SQL 或 Spark SQL** 任务，仅返回 `TaskId`，不等待执行结果。`SQL` 与 `SparkSQL` 至少提供一个；实际提供哪个字段就校验哪个字段。支持 `SELECT`、`WITH ... SELECT`、`SHOW`、`DESCRIBE` / `DESC`、`EXPLAIN`；不支持写入、变更或多语句 SQL。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `SQL` | string | 否 | 只读 SQL 明文；与 `SparkSQL` 至少提供一个 |
| `SparkSQL` | string | 否 | 只读 Spark SQL 明文；与 `SQL` 至少提供一个 |
| `DataEngineName` | string | 是 | 数据引擎名称 |
| `DatabaseName` | string | 否 | 默认数据库 |
| `DatasourceConnectionName` | string | 否 | 默认 `DataLakeCatalog` |

返回：`TaskId`、`RequestId`。

**注意事项**：
- 后端 SQL 使用 base64 编码传输；MCP 工具接收明文 SQL，自动编码。
- 分别对实际提供的 `SQL` 和 `SparkSQL` 做单条只读校验。写入或变更 SQL 会返回“仅支持只读 SQL / Spark SQL”提示；多语句 SQL 会被拒绝。
- 校验器会保守扫描未引用 token；若字段名或别名与写入/变更关键字同名，也可能被拒绝，应改用不冲突的别名后再查询。
- 任务创建后返回 `TaskId`。使用 `DLCDescribeMCPTask` 查询任务状态，任务完成（`State=0`）后可预览 `DataSet`；需要完整结果时再调用 `DLCDescribeMCPTaskResult`。
- 后端会做引擎存在性校验、引擎类型与任务类型匹配校验、CAM 权限校验。

### 任务状态与结果

#### `DLCDescribeMCPTask`

使用 `DLCExecuteQuery` 等创建任务返回的 `TaskId` 查询单个任务完整详情及任务状态。**适用所有任务类型**（SQL 任务、Spark 任务、Spark 作业等）。任务状态完成（`State=0`）后，本接口可通过 `DataSet` 返回结果预览。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `TaskId` | string | 是 | 任务 ID |

返回（`TaskInfo` 字段）：`Id`、`BatchId`、`State`（后端状态值）、**`TaskType`**（任务类型，如 `SQLTask`、`SparkSQLTask`、`SparkBatchTask` 等）、**`TaskKind`**（任务种类）、`SQLType`、`SQL`、`DatabaseName`、`DataEngineId`、`ResourceGroupName`、`SparkJobId`、`SparkJobName`、`OperateUin`、`CreateTime`、`StartTime`、`EndTime`、`UpdateTime`、`UsedTime`（引擎耗时毫秒）、`TotalTime`（总耗时毫秒）、`Progress`、`OutputMessage`、`DataSet`（结果预览）、`IsSQLCutOff`（结果是否被截断）。

**注意事项**：
- `State` 为后端任务状态（0=成功、-1=失败等），不是前端状态。
- **此接口已包含结果预览**（`DataSet` 字段），大多数场景直接使用本接口即可，无需再调用 `DLCDescribeMCPTaskResult`。
- 仅在以下情况调用 `DLCDescribeMCPTaskResult`：① `IsSQLCutOff=true`（结果被截断，需要完整数据）；② 用户明确要求完整结果集；③ 需要查看结果 Schema（`ResultSchema`）。
- 轮询 QPS 严格限制为 1（每秒最多 1 次），建议间隔 3~5 秒，直到 `State` 变为终态（0 / -1 / -6 等）。

#### `DLCDescribeMCPTaskResult`

任务完成（`DLCDescribeMCPTask` 返回 `State=0`）后，使用同一个 `TaskId` 查询执行结果详情（含 Schema 和单次最多 1000 行数据）。**非必要不调用**，优先使用 `DLCDescribeMCPTask` 的结果预览。**适用所有任务类型**。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `TaskId` | string | 是 | 任务 ID |

返回（`TaskResult` 字段）：`TaskId`、`State`、`ResultSchema`（列 Schema）、`ResultSet`（结果集数据，最多 1000 行）、`NextToken`（仅作为响应字段）、`RowAffectInfo`（影响行数）、`OutputMessage`、`DisplayFormat`、`CanDownload`、`QueryResultTime`（结果查询耗时毫秒）、`IsResultOversize`（是否超大）。

**注意事项**：
- 只有在任务成功后（`DLCDescribeMCPTask` 返回 `State=0`）调用才有意义。
- **单次最多返回 1000 行**。当前 tool 仅接受 `Region` 和 `TaskId`，不接受 `NextToken`，因此不能通过该 tool 获取后续页。
- `NextToken` 非空或 `IsResultOversize=true` 时，应明确告知用户结果可能不完整；不得调用白名单外的其他 tool 或外部方式获取剩余数据。

#### `DLCCancelTask`（已下线）

> **当前已下线，暂不可调用**。以下为后续重新启用时的使用说明（保留供参考）。

取消正在运行的任务。**适用所有任务类型**（SQL 任务、Spark 任务、Spark 作业、导入导出任务等）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `TaskId` | string | 是 | 任务 ID |

返回：`RequestId`。

**注意事项**：
- 后端根据任务类型走不同取消逻辑（SQL/Spark 任务、导入导出任务、Spark 作业任务各有独立取消流程）。
- 后端先按 TaskId 查询任务，再校验引擎 CAM 权限，最后执行取消。
- 已结束的任务无法取消。

### 任务运维

#### `DLCDescribeTaskList`

查询历史任务列表。**适用所有任务类型**（SQL 任务、Spark 任务、Spark 作业、导入导出等）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0` |
| `SortBy` | string | 否 | 排序字段，仅支持 `create-time`（默认）、`update-time` |
| `Sorting` | string | 否 | `desc` / `asc`，默认 `asc` |
| `StartTime` / `EndTime` | string | 否 | 时间范围，格式 `yyyy-MM-dd HH:mm:ss`，默认最近约 45 天 |
| `DataEngineName` | string | 否 | 引擎名称过滤 |
| `TaskId` | string | 否 | 任务 ID 精确过滤 |
| `KeyWord` | string | 否 | SQL 关键字模糊过滤 |
| `State` | string | 否 | 前端状态过滤（0/1/2/-1 等） |

**注意事项**：
- `SortBy` 建议仅传 `create-time` 或 `update-time`；tool 会将其他非空值原样透传，可能被后端拒绝。
- `State` 使用前端状态值（0=初始化、1=运行中、2=成功、-1=失败），非后端状态。
- `TaskId`/`KeyWord`/`State` 通过后端 Filters 传递（Key 分别为 `task-id`、`task-sql-keyword`、`task-state`）。

#### `DLCDescribeTasksAnalysis`

Spark 任务性能诊断分析。**仅适用于 Spark 引擎任务**（后端仅查询 Spark 引擎 `GetAllSparkHousesByAppId`），SQL/Presto 任务无诊断数据。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0`，`Limit` 最大为 `100` |
| `SortBy` / `Sorting` | string | 否 | 排序字段与方向 |
| `StartTime` / `EndTime` | string | 否 | 时间范围，格式 `yyyy-MM-dd HH:mm:ss` |
| `TaskId` | string | 否 | 任务 ID 精确过滤 |
| `State` | string | 否 | 任务状态过滤（前端状态值） |
| `RuleId` | string | 否 | 诊断规则（每次只能传 1 个） |
| `DataEngineName` | string | 否 | 引擎名称过滤（仅 Spark 引擎） |

推荐 `RuleId`（每次只能选 1 个）：

| RuleId | 说明 |
|---|---|
| `SPARK-StageScheduleDelay` | 资源抢占 / Stage 调度等待 |
| `SPARK-ShuffleFailure` | Shuffle 异常 |
| `SPARK-SlowTask` | 慢 Task |
| `SPARK-DataSkew` | 数据倾斜 |
| `SPARK-InsufficientResource` | 资源不足 |

**注意事项**：
- **仅适用于 Spark 引擎任务**，SQL/Presto 任务调用本接口会返回空结果。可通过 `DLCDescribeMCPTask` 的 `TaskType` 判断任务类型。
- `RuleId`、`TaskId`、`State` 均通过 Filters 传递（Key 分别为 `rule-id`、`task-id`、`task-state`）。
- **`RuleId` 每次只能传 1 个值**，后端严格校验。

### 日志查询

#### `DLCListTaskJobLogName`

获取日志文件名列表。**主要用于 Spark 类任务**（SparkSQL、SparkBatchSQL、Spark 作业等），SQL 任务日志需通过 `DLCDescribeMCPTask` 的 `OutputMessage` 查看。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `TaskId` | string | 是 | 任务 ID |
| `BatchId` | string | 否 | Spark SQL 批任务 ID |

**注意事项**：
- 主要用于 Spark 类任务；当前 tool 不支持 `LogScene` 参数。
- 非 Spark 任务可能返回空日志列表。

#### `DLCListTaskJobLogDetail`

分页读取日志内容。**主要用于 Spark 类任务**。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `StartTime` | number | 是 | Unix 毫秒时间戳 |
| `EndTime` | number | 是 | Unix 毫秒时间戳 |
| `Limit` | number | 否 | 建议最大 `1000`，默认 `1000` |
| `Context` | string | 否 | 翻页游标（上次返回的 Context），首次查询不传 |
| `TaskId` | string | 否 | 任务 ID |
| `BatchId` | string | 否 | 批任务 ID |
| `Asc` | boolean | 否 | 是否升序，默认 `false` |

返回：`ListOver`（`true` 表示已全部返回）、`Context`（翻页游标）、`Results`、`LogUrl`。

**注意事项**：
- `StartTime` / `EndTime` 为 **Unix 毫秒时间戳**（非秒），建议围绕任务创建时间设置窗口。
- 通过 `Context` 游标翻页：首次查询不传 `Context`；后续将上次返回的 `Context` 传入继续获取；`ListOver=true` 表示已全部返回。

#### `DLCListDatasourceConnections`

列出数据源 / Catalog 连接。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=20, Offset=0`，`Limit` 最大为 `100` |
| `DatasourceConnectionName` | string | 否 | 数据源连接名称过滤 |

返回：连接 ID、名称、描述、类型、状态、创建时间等。

**注意事项**：
- `DatasourceConnectionName` 会作为云 API `Filters` 中 `Name=DatasourceConnectionName` 的过滤条件透传。

### 数据引擎与资源组

#### `DLCListEngines`

列出数据引擎。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |

返回：`DataEngines`、`TotalCount`。

**注意事项**：
- 当前 tool 不接受分页、排序或过滤参数，内部固定以 `Limit=100` 查询。

#### `DLCDescribeDataEngine`

查询单个数据引擎详情。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `DataEngineName` | string | 是 | 引擎名称 |

返回：引擎状态、类型、规格（CU）、VPC 信息、标签、自动挂起/恢复配置、JDBC 信息、资源组信息等。

#### `DLCDescribeStandardEngineResourceGroups`

查询标准引擎资源组。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `DataEngineName` | string | 否 | 引擎名称过滤 |
| `ResourceGroupName` | string | 否 | 资源组名称过滤 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0` |
| `SortBy` / `Sorting` | string | 否 | 排序字段与方向 |

### 元数据查询

#### `DLCListDatabases`

列出数据库。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `DatasourceConnectionName` | string | 否 | 默认 `DataLakeCatalog` |
| `KeyWord` | string | 否 | 库名模糊匹配 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0`，`Limit` 最大为 `100` |

**注意事项**：
- 当前 tool 不支持排序参数。
- 未传 `DatasourceConnectionName` 时默认使用 `DataLakeCatalog`。

#### `DLCListTableNames`

列出表名。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `DatabaseName` | string | 是 | 数据库名；未知时先调用 `DLCListDatabases` 获取 |
| `DatasourceConnectionName` | string | 否 | 默认 `DataLakeCatalog` |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0` |

**注意事项**：
- 用户未提供 `DatabaseName` 时，先调用 `DLCListDatabases` 获取；已明确提供时可直接使用。
- 当前 tool 不支持排序或时间范围过滤参数。

#### `DLCListTables`

按表名数组批量查询完整表元数据。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `DatabaseName` | string | 是 | 数据库名 |
| `TableNames` | array | 是 | 非空表名字符串数组；表名未知时先调用 `DLCListTableNames` 获取 |
| `DatasourceConnectionName` | string | 否 | 默认 `DataLakeCatalog` |

**注意事项**：
- `TableNames` 必须是非空字符串数组；缺失或为空时 tool 会返回错误。
- tool 会逐个查询表；单个表查询失败时继续处理其他表，因此可能返回部分成功结果。
- 返回列定义（名称/类型/注释）、分区信息、存储位置、表属性，并自动附加数据脱敏策略。

#### `DLCDescribeTablePartitions`

查询 Hive / Iceberg 表分区。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `Database` | string | 是 | 数据库名 |
| `Table` | string | 是 | 表名 |
| `Catalog` | string | 否 | 默认 `DataLakeCatalog` |
| `FuzzyPartition` | string | 否 | 分区模糊匹配 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=10, Offset=0` |

**注意事项**：
- 当前 tool 不支持 `Cursor` 或 `Sorts` 参数。
- Iceberg 表 `Offset + Limit > 10000` 可能报错。
- 非托管 Iceberg 表或非 `DataLakeCatalog` 的 Iceberg 表可能返回空分区。
- 分区数量极大时建议用 SQL 查询分区。

### Spark 作业管理

#### `DLCCreateSparkApp`

创建 Spark 作业。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `AppName` | string | 是 | 作业名 |
| `AppType` | number | 是 | `1`=批处理，`2`=流处理，`3`=Python，`4`=SQL 作业 |
| `DataEngine` | string | 是 | 数据引擎名称 |
| `AppFile` | string | 条件必填 | 批处理、流处理和 Python 作业必须提供程序包路径；SQL 作业无需提供 |
| `RoleArn` | number | 是 | 用户提供的 CAM Role ARN 标识 |
| `AppDriverSize` | string | 否 | Driver 规格，默认 `small` |
| `AppExecutorSize` | string | 否 | Executor 规格，默认 `small` |
| `AppExecutorNums` | number | 否 | Executor 数量，默认 `1` |
| `IsLocal` | string | 否 | 程序包来源，默认 `cos` |
| `MainClass` | string | 否 | 主类 |
| `AppConf` | string | 否 | Spark 配置，以换行符分隔 |
| `CmdArgs` | string | 条件必填 | 普通作业为程序参数；SQL 作业必须传入 SQL 原文 |
| `DataSource` | string | 否 | 数据源名称 |
| `AppExecutorMaxNumbers` | number | 否 | 开启动态分配时的最大 Executor 数量 |

返回：`SparkAppId`。

**限制**：
- `AppType=4` 时，`CmdArgs` 仅允许 `SELECT`、`WITH ... SELECT`、`SHOW`、`DESCRIBE` / `DESC`、`EXPLAIN`；禁止 DDL、DML 和多语句。Tool 会在校验通过后自动将 SQL 原文 Base64 编码到 Cloud API 的 `CmdArgs`，调用方不得自行编码。
- `DLCModifySparkApp` 和 `DLCDeleteSparkApp` 已下线且不在 Tool 白名单中，禁止调用。

#### `DLCCreateSparkAppTask`

启动 Spark 作业。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `JobName` | string | 是 | Spark 作业名 |
| `CmdArgs` | string | 否 | 运行参数，以空格分隔 |

返回：`BatchId` / `TaskId`。

**注意事项**：
- 后端按 `JobName` 查询唯一 Spark 作业，要求作业名唯一。
- 返回的 `TaskId` 可用于后续 `DLCDescribeMCPTask` 查询状态。

#### `DLCDescribeSparkAppJobs`

查询 Spark 作业列表。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `Limit` / `Offset` | number | 否 | 分页，默认 `Limit=100, Offset=0` |
| `SortBy` | string | 否 | 排序字段，仅支持 `create-time`、`update-time`、`user-name`、`data-engine-name` |
| `Sorting` | string | 否 | `desc` / `asc`，默认 `asc` |
| `KeyWord` | string | 否 | 关键词搜索（作业名或 ID） |
| `StartTime` / `EndTime` | string | 否 | 时间范围，格式 `yyyy-MM-dd HH:mm:ss` |

**注意事项**：
- `SortBy` 仅支持上述 4 个枚举值。
- `KeyWord` 通过 Filters（Key=`key-word`）传递。

#### `DLCDescribeSparkAppJob`

查询单个 Spark 作业详情。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `JobId` | string | 否 | 作业 ID（优先） |
| `JobName` | string | 否 | 作业名 |

**注意事项**：
- `JobId` 与 `JobName` **至少提供一个**；同时存在时优先按 `JobId`。

### 用户与权限

#### `DLCDescribeUserInfo`

查询用户详情与权限。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域 |
| `UserId` | string | 否 | 用户 ID；查询当前调用方时可先通过 `DLCDescribeMCPSubUin` 获取 |
| `Type` | string | 否 | `Group` / `DataAuth` / `EngineAuth` / `RowFilter` |
| `Limit` / `Offset` | number | 否 | 分页 |
| `SortBy` / `Sorting` | string | 否 | 排序 |

**注意事项**：
- `Type=Group` 查询工作组归属；`DataAuth` 查询数据权限；`EngineAuth` 查询引擎权限；`RowFilter` 查询行级过滤。

#### `DLCDescribeMCPSubUin`

获取当前调用方（MCP 客户端）的子账号 Uin（SubUin）。该 Uin 通常作为 `DLCDescribeUserInfo` 的 `UserId` 入参，用于查询当前账号自身的权限信息。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Region` | string | 是 | 地域信息，例如 ap-guangzhou、ap-shanghai、ap-beijing 等 |

**注意事项**：
- 该接口无业务参数，仅需 `Region`。
- 返回字段 `Subuin` 即为当前调用方的子账号 Uin，可作为 `DLCDescribeUserInfo` 的 `UserId` 使用。
- 当不确定 `DLCDescribeUserInfo` 应传入的 `UserId` 时，可先调用本工具获取。

---

## 错误处理

### 权限错误

遇到 `UnauthorizedOperation.NoEngineCamPermissions` 时按以下顺序排查：

1. 检查 `Uin`、`Region`、`CamContext` 是否匹配。
2. 检查用户是否有目标数据引擎权限。
3. 对任务接口，检查任务所属 `HouseId` / `DataEngineId`。
4. 对标准 Spark 引擎，检查资源组权限。
5. `CheckResource` 失败时优先定位 CAM token / CAM 策略。
6. `CheckResource` 成功但 `HasPermission` 失败时优先定位目标引擎资源权限或标签权限。

### 参数错误

- 缺少 `DataEngineName`：先调用 `DLCListEngines`。
- 元数据 tools 缺少 `DatabaseName`：先调用 `DLCListDatabases` 获取或询问用户；`DLCExecuteQuery` 的 `DatabaseName` 可选。
- 缺少 `TaskId`：取消任务、查询任务或获取日志文件名时必须补齐；`DLCListTaskJobLogDetail` 的 `TaskId` 可选，但 `StartTime`、`EndTime` 必填。
- 时间格式错误：任务列表类 tools 使用 `yyyy-MM-dd HH:mm:ss`；`DLCListTaskJobLogDetail` 使用 Unix 毫秒时间戳。
- SQL base64 decode 失败：MCP tool 接收明文 SQL，不要传入已编码内容。

### 任务失败排查顺序

1. 调用 `DLCDescribeMCPTask` 根据 `TaskId` 查询状态和 `OutputMessage`。
2. SQL 任务优先依据 `OutputMessage` 排查，不调用 Spark 日志 tools。
3. Spark 类任务失败时，调用 `DLCListTaskJobLogName` 获取日志名，再调用 `DLCListTaskJobLogDetail` 分页读取日志。
4. Spark 任务可继续调用 `DLCDescribeTasksAnalysis`，根据 `RuleId` 判断异常类型。

---

## 使用原则

- **所有工具调用必须传 Region**，这是跨地域 per-user 模型的硬性要求。
- 未指定数据引擎时，先调用 `DLCListEngines`，不要猜测引擎名。
- 未指定 Catalog 时，使用 `DataLakeCatalog`。
- **风险操作必须先确认**：Spark 作业创建、启动及取消任务等白名单操作（见「风险操作确认」章节），必须先向用户说明风险并等待明确确认，不可直接执行；修改、删除 Spark 作业不在白名单内，禁止调用相关 tools。
- `DLCExecuteQuery` 允许单条只读 `SQL` 或 `SparkSQL`；实际提供哪个字段就校验哪个字段。对写入、变更或多语句 SQL，直接返回“仅支持只读 SQL / Spark SQL”提示，不请求确认也不执行。
- 用户只想查询元数据时，优先使用元数据接口（`DLCListDatabases` → `DLCListTableNames` → `DLCListTables`），不要执行 SQL。
- 查询列表时默认分页，避免一次拉取过多数据。
- 查日志时优先围绕任务创建时间或更新时间设置时间窗口。
- `DLCExecuteQuery` 是异步的，必须用 `DLCDescribeMCPTask` 轮询状态。`DLCDescribeMCPTask` 已包含结果预览（`DataSet`），**非必要不调用 `DLCDescribeMCPTaskResult`**。仅在结果被截断（`IsSQLCutOff=true`）或需要完整结果集时才调用。
- **任务轮询 QPS 严格限制为 1**（每秒最多 1 次），详见「任务轮询频率限制」章节。
- 不要输出访问密钥、token、`CamContext`、临时凭证。
- 返回结果时先总结关键信息，再给出必要 JSON 字段。
