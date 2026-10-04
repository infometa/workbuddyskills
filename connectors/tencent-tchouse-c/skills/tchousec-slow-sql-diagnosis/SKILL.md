---
name: 腾讯云TCHouse-C 慢 SQL 诊断与自动调优
description: >
  TCHouse-C（ClickHouse）慢 SQL 诊断与自动调优 Skill。AI 自动检索指定集群的慢查询日志，对 Top N 慢 SQL 逐一执行 EXPLAIN 获取执行计划，分析性能瓶颈（全表扫描/JOIN 顺序不优/索引缺失/数据倾斜），生成 SQL 改写方案。
  触发词：慢查询、慢SQL、slow query、SQL优化、查询优化、执行计划、EXPLAIN、查询耗时、查询超时、SQL调优、索引优化、全表扫描、数据倾斜、JOIN优化、查询性能、SQL性能、query performance、查询变慢、报表变慢、ClickHouse优化、TCHouse-C优化、cdwch、查询诊断、SQL诊断。
  本 Skill 包含 3 个子能力：①慢查询 Top N 检索与趋势分析 ②执行计划分析与瓶颈定位 ③SQL 改写与索引优化方案生成。
  何时不触发：集群选型与架构推荐、智能建表与数据建模、NL2SQL、集群健康诊断与故障排查（监控指标/告警/节点故障）、集群扩缩容、权限管理、数据导入导出等非查询性能相关问题不走本 Skill。
allowed-tools:
  - TCHouseCDescribeInstance
  - TCHouseCDescribeInstanceNodes
  - TCHouseCDescribeSlowQueryRecords
  - TCHouseCDescribeSlowQueryTrend
  - TCHouseCDescribeRunningQuery
  - TCHouseCDescribeCkSqlApis
  - TCHouseCDescribeTableSchema
  - TCHouseCDescribeClusterConfigs
  - ask_user # WorkBuddy 中为 AskUserQuestion
---

# 慢 SQL 诊断与自动调优

## 概述

本 Skill 提供 TCHouse-C（ClickHouse）集群的慢 SQL 诊断与自动调优能力，包含三个子能力：

1. **慢查询 Top N 检索与趋势分析**：检索慢查询日志，分析趋势判断是突发还是持续恶化
2. **执行计划分析与瓶颈定位**：对慢 SQL 执行 EXPLAIN，识别全表扫描/JOIN 不优/索引缺失等问题
3. **SQL 改写与索引优化方案生成**：生成 SQL 改写、跳数索引、排序键调整、物化视图等优化建议

## 依赖与运行环境

本 Skill 的所有调用通过 MCP Tool 完成（云 API 类工具由平台封装为 MCP Tool，Agent 直接调用工具名即可）。

**依赖工具清单**：

| #   | Tool 名称                        | 能力定位                                         | 参考文档                                                         |
| --- | -------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------- |
| 1   | TCHouseCDescribeInstance         | 集群信息获取                                     | [参考](references/tchousec-describe-instance.md)           |
| 2   | TCHouseCDescribeSlowQueryRecords | 慢查询明细检索                                   | [参考](references/tchousec-describe-slow-query-records.md) |
| 3   | TCHouseCDescribeSlowQueryTrend   | 慢查询趋势分析                                   | [参考](references/tchousec-describe-slow-query-trend.md)   |
| 4   | TCHouseCDescribeRunningQuery     | 正在运行的查询                                   | [参考](references/tchousec-describe-running-query.md)      |
| 5   | TCHouseCDescribeCkSqlApis        | SQL 执行计划获取                                 | [参考](references/tchousec-describe-ck-sql-apis.md)        |
| 6   | TCHouseCDescribeTableSchema      | 表结构/索引信息                                  | [参考](references/tchousec-describe-table-schema.md)       |
| 7   | TCHouseCDescribeClusterConfigs   | 集群配置参数                                     | [参考](references/tchousec-describe-cluster-configs.md)    |
| 8   | ask_user                         | 向用户询问确认（WorkBuddy 中为 AskUserQuestion） | —                                                                |

## 凭证 / 环境变量

- `instance_id`：从会话 context 的 X-Context header 自动注入
- `region_id`：从会话 context 的 X-Context header 自动注入（可能是 `RegionId` 数字、`Region` 字符串或中文地域名）
- 若以上参数缺失，通过 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）询问用户

> ⚠️ **地域参数强制规则**：本 Skill 依赖的全部工具（`TCHouseCXxx` 系）都只接受 **`Region` 字符串**（如 `ap-guangzhou`）。**任何工具调用前**都必须先按 [地域映射表](references/region-mapping.md) 将上下文中的地域信息（无论是中文名、英文串还是 `RegionId` 数字）统一转为 `Region` 字符串后再传入，禁止凭记忆填写。详见 [工具传参形式速查](references/region-mapping.md#工具传参形式速查)。

> 💡 **多平台兼容说明**：本文档中所有提到的 `ask_user` 工具，在 WorkBuddy 平台中对应为 `AskUserQuestion`。后文不再重复标注。

## 核心工作流

### 步骤 0：参数确认

**必需参数**：

- `instance_id`（集群 ID）
- `region_id`（地域）

**可选参数**（从用户问题中提取，缺失时使用默认值，不自行假设）：

- 时间范围：未指定 → 默认最近 7 天
- 慢查询阈值：未指定 → 默认 500ms
- Top N 条数：未指定 → 默认 10

**判断逻辑**：

- ✅ 参数齐全 → **强制**按 [地域映射表](references/region-mapping.md) 将地域信息统一转为 `Region` 字符串（任何输入形式都要过这一步：中文名、英文串、数字 ID 都不例外），转换后进入步骤 1
- ❌ `instance_id` 或 `region_id` 缺失 → 调用 `ask_user` 询问
- ❌ 地域信息在映射表中匹配不到（或大区模糊，如"华南地区"）→ 调用 `ask_user` 确认后再转换

### 步骤 1：确认集群信息

调用 `TCHouseCDescribeInstance` 获取集群基本信息。

**判断逻辑**：

- ✅ 集群状态为 `Serving` → 进入步骤 2
- ❌ 集群状态为 `Init`/`Modify` → 告知用户集群当前不可用，建议等待恢复后重试
- ❌ 集群状态为 `Deleted`/`Deleting` → 告知用户集群已下线，终止诊断
- ❌ 调用失败（AuthFailure）→ 报告错误，提示检查权限
- ❌ 调用失败（ResourceNotFound）→ 检查 instance_id 格式（应为 `cdwch-` 前缀），格式错则修正重试，格式对则请用户确认

**记录信息**：ClickHouse 版本号（影响 EXPLAIN 支持）、节点规格和数量。

### 步骤 2：获取慢查询数据

调用 `TCHouseCDescribeSlowQueryRecords` 获取慢 SQL 明细列表。

**参数确定策略**：

- 时间范围：根据用户描述（"最近一周" → 7天，"昨天" → 昨天0点到今天0点）
- 慢查询阈值（QueryDurationMs）：用户指定则按用户要求，未指定默认 500ms
- PageSize：默认 10，用户指定条数则按用户要求
- 排序：`SortColumn: query_duration_ms` + `SortOrder: DESC`（按耗时降序）

**判断逻辑**：

- ✅ 返回有数据 → 进入步骤 3
- ❌ 返回为空 → 告知用户，建议：1) 扩大时间范围 2) 降低阈值（如 500ms → 100ms）
- ❌ 返回错误提示慢查询日志未开启 → 提供开启步骤指引（控制台 → 集群详情 → 参数配置 → 开启 slow_log），告知需等待数据积累
- ❌ 调用超时 → 等 3 秒重试，最多 3 次；仍失败则告知用户服务暂时不可用

**辅助步骤**（可选）：调用 `TCHouseCDescribeSlowQueryTrend` 获取趋势数据，判断慢查询是突发性还是持续恶化。

> ⚠️ **参数命名注意**：`TCHouseCDescribeSlowQueryTrend` 的集群 ID 参数名为 **`InstanceID`（大写 D）**，与其他工具的 `InstanceId`（小写 d）不同，传参时务必注意拼写。

> ⚠️ **调用策略**：该接口按分钟级粒度返回数据点，单次查询时间范围过大会导致返回数据超出 token 上限。请根据步骤 2 中 `TotalCount`（慢查询总条数）和查询天数，计算**日均慢查询数 = TotalCount ÷ 天数**，然后按以下策略调用：
>
> | 日均慢查询数 | 策略                                             | 理由                                                                         |
> | ------------ | ------------------------------------------------ | ---------------------------------------------------------------------------- |
> | ≤ 50 条/天   | **直接查整个时间段**（如 7 天一次性查）          | 数据稀疏，分钟级数据点大部分为 0，返回总量可控                               |
> | 50~500 条/天 | **采样 3 天**：最近 1 天 + 中间 1 天 + 最早 1 天 | 3 个采样点足够判断趋势走向（上升/下降/平稳），避免调用过多                   |
> | > 500 条/天  | **只查最近 1 天**                                | 数据密集，1 天内的分钟级趋势已足够判断模式（突发/持续），超过 1 天必超 token |
>
> **时间范围 ≤ 1 天时**：无论日均数量多少，直接查询即可。
>
> 示例：用户查 7 天，TotalCount=210 → 日均 30 条 → 直接查 7 天整段；TotalCount=2100 → 日均 300 条 → 采样第 1、4、7 天各查 1 次。

### 步骤 3：检查当前运行查询（条件触发）

**触发条件**：用户描述的是"正在发生"的问题（如"现在查询很慢"、"当前有查询卡住"）。

调用 `TCHouseCDescribeRunningQuery` 查看当前长耗时 SQL，辅助判断锁等待、资源争抢、死循环查询。

**判断逻辑**：

- ✅ 有长耗时查询 → 纳入分析范围
- ✅ 无异常 → 继续步骤 3.5
- ❌ 调用失败 → 跳过此步骤，基于历史慢查询数据继续分析

### 步骤 3.5：SQL 模式归一化与去重

对步骤 2 返回的 Top N 慢查询记录进行归一化去重，避免对同一 SQL 模式重复分析。

**归一化规则**（按顺序应用）：

1. 将字符串字面量替换为 `'?'`（如 `WHERE name = 'Alice'` → `WHERE name = '?'`）
2. 将数字字面量替换为 `?`（如 `LIMIT 100` → `LIMIT ?`，`id = 12345` → `id = ?`）
3. 将 `IN (...)` 列表替换为 `IN (?)`（如 `IN (1,2,3)` → `IN (?)`）
4. 去除多余空白、统一为单空格
5. 转为小写后比较

**去重与聚合**：

- 归一化后 SQL 文本相同的记录归为同一**SQL 模式**
- 每个模式记录：出现次数、最大耗时、平均耗时、最近一次执行时间
- 按**最大耗时降序**排列去重后的模式列表

**判断逻辑**：

- ✅ 去重后有 ≥ 3 个不同模式 → 取前 3-5 个模式进入步骤 4
- ⚠️ 去重后只有 1-2 个模式（Top N 几乎全是同一条 SQL）→ 执行以下补充策略：
  1. 记录该高频模式的执行频次（作为独立优化维度：频次高 × 耗时高 = 优先级最高）
  2. 调用 `TCHouseCDescribeSlowQueryRecords` 翻页（PageNum + 1）或降低 QueryDurationMs 阈值，尝试获取更多不同 SQL 模式
  3. 最多补充翻页 2 次（受频率控制约束），将新发现的不同模式纳入分析
- ❌ 翻页后仍只有 1 个模式 → 只分析该模式，但在报告中重点标注其高频特征

**输出**：去重后的 SQL 模式列表（含频次统计），供步骤 4 逐一分析。

### 步骤 4：逐条分析慢 SQL

对步骤 3.5 输出的**去重后 SQL 模式列表**中的每个模式（建议重点分析前 3-5 个）：

> 💡 **并行化提示**：对每个 SQL 模式，4.1（EXPLAIN）和 4.2（表结构）之间**无依赖关系**，可以并行调用以提高效率。同时步骤 5（集群配置获取）也可与步骤 4 并行启动。

**4.1 获取执行计划**：

- 调用 `TCHouseCDescribeCkSqlApis`，使用 `PLAN` 类型
- ✅ 成功 → 进入 4.3
- ❌ 版本不支持（< 20.6）→ 标记“版本不支持 EXPLAIN”，基于 SQL 文本和表结构给出有限建议
- ❌ SQL 语法错误/表已删除 → 跳过该条，继续下一条
- ❌ 执行超时 → 标记“执行计划获取超时”，跳过继续，报告中注明建议用户简化后重试
  **4.2 获取表结构**：

- 从 SQL 中提取涉及的表名，调用 `TCHouseCDescribeTableSchema` 获取建表 DDL
- ✅ 成功 → 进入 4.3
- ❌ 表已删除/权限不足 → 跳过表结构分析，基于执行计划给出有限建议

**4.3 瓶颈识别**：

- 按 [分析框架](references/analysis-framework.md#性能瓶颈识别) 识别问题类型
- 生成对应优化建议，详见 [优化方案模板](references/optimization-templates.md)

### 步骤 5：检查集群配置（默认执行）

> 💡 **执行策略**：本步骤为**默认执行**，与步骤 4 并行启动。理由：配置获取零依赖、成本低（单次 API 调用）、可在 EXPLAIN/表结构获取失败时提供间接诊断线索。

调用 `TCHouseCDescribeClusterConfigs` 获取集群配置文件列表。

> ⚠️ **返回格式说明**：该接口返回的是 `ClusterConfList` 数组，每个元素包含 `FileName`（文件名）和 `FileConf`（XML 格式的配置文件全文）。**不是结构化键值对**，需要从 XML 文本中提取目标配置项。

**XML 解析步骤**：

1. **定位目标文件**：
   - 查询级配置（内存/超时/并发）→ 从 `FileName = "users.xml"` 的 `FileConf` 中提取
   - 服务端配置（连接数/缓存/MergeTree）→ 从 `FileName = "config.xml"` 的 `FileConf` 中提取
   - 集群拓扑（分片/副本）→ 从 `FileName = "metrika.xml"` 的 `FileConf` 中提取

2. **从 XML 文本中提取关键配置项**（使用正则或 XML 标签匹配）：

   **users.xml（`<profiles><default>` 节点下）**：
   - `<max_memory_usage>` — 单次查询内存上限（字节）
   - `<max_threads>` — 查询并发线程数
   - `<max_execution_time>` — 查询超时时间（秒）
   - `<join_algorithm>` — JOIN 算法（hash/partial_merge/auto）
   - `<max_bytes_before_external_sort>` — 外部排序阈值
   - `<max_bytes_before_external_group_by>` — 外部 GROUP BY 阈值

   **config.xml（`<yandex>` 根节点下）**：
   - `<max_concurrent_queries>` — 最大并发查询数
   - `<max_connections>` — 最大连接数
   - `<uncompressed_cache_size>` — 未压缩数据缓存
   - `<mark_cache_size>` — Mark 缓存大小
   - `<merge_tree><parts_to_throw_insert>` — parts 过多阈值

3. **提取方式**：对 `FileConf` 字符串，按 XML 标签名匹配提取值，例如匹配 `<max_memory_usage>(\d+)</max_memory_usage>` 获取数值。若标签不存在则表示使用 ClickHouse 默认值。

**判断逻辑**：

- ✅ 成功获取并解析出配置值 → 纳入综合分析，与步骤 4 的瓶颈对照判断是否为配置瓶颈
- ⚠️ 目标配置项在 XML 中不存在 → 标注"使用默认值"，参考 ClickHouse 官方默认值进行分析
- ❌ 接口调用失败 → 跳过配置分析，基于已有数据给出建议，报告中注明未能获取配置信息

### 步骤 6：综合分析与生成报告

基于收集到的所有信息，按 [输出报告格式](references/analysis-framework.md#输出报告格式) 生成诊断报告。

**报告必须包含**：

1. 集群概况（ID/版本/状态）
2. 慢查询概览（时间范围/总数/平均耗时）
3. 趋势分析（突发 vs 持续）
4. 逐条诊断（SQL文本/耗时/瓶颈/优化建议）
5. 综合优化建议（按优先级排序）

## 频率控制

| 限制                                  | 阈值          | 说明                           |
| ------------------------------------- | ------------- | ------------------------------ |
| 工具总调用频率                        | ≤ 10 次/分钟  | 避免触发平台限流               |
| TCHouseCDescribeCkSqlApis 调用        | ≤ 5 次/轮诊断 | EXPLAIN 不执行查询但有解析开销 |
| TCHouseCDescribeSlowQueryRecords 翻页 | ≤ 3 次/轮     | 避免拉取过多数据               |

**超限处理**：连续收到 `RequestLimitExceeded` → 等 5 秒重试，连续 3 次仍失败 → 降低调用频率，告知用户被限流。

## 错误码与处理策略

| 错误码/场景            | Agent 行为                                                                                                                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AuthFailure.*`        | 报告鉴权失败，提示用户检查集群访问权限                                                                                                                                                                |
| `ResourceNotFound`     | 检查 ID 格式（`cdwch-` 前缀）；格式错 → 修正重试；格式对 → 请用户确认                                                                                                                                 |
| `InvalidParameter.*`   | 检查参数格式（时间范围、阈值），尝试修正后重试 1 次；无法修正 → 报告具体问题                                                                                                                          |
| `UnsupportedRegion`    | 该地域未开通 TCHouseC 产品。**不重试、不自动切换地域**，必须调用 `ask_user` 让用户确认地域。详见 [error-handling.md §1](references/error-handling.md#1-unsupportedregion该接口不支持此地域访问) |
| `InternalError`        | 等 3 秒重试，最多 3 次；仍失败 → 报告错误码 + RequestId                                                                                                                                               |
| `RequestLimitExceeded` | 等 5 秒重试；连续 3 次 → 降低频率，告知被限流                                                                                                                                                         |
| EXPLAIN 超时           | 标记该 SQL 为"执行计划获取超时"，跳过继续处理其余 SQL                                                                                                                                                 |
| 表结构获取失败         | 跳过表结构分析，基于执行计划和 SQL 文本给出有限建议                                                                                                                                                   |
| 集群配置获取失败       | 跳过配置分析，基于已有数据给出建议                                                                                                                                                                    |
| 网络超时               | 查询类操作等 3 秒重试，最多 3 次；仍失败 → 告知用户服务暂时不可用                                                                                                                                     |
| 兜底（未列出错误码）   | 报告完整错误信息 + RequestId                                                                                                                                                                          |

## 安全规则

1. **本 Skill 为纯只读诊断**：所有操作均为查询类（Describe/Explain），不涉及写操作，无需用户确认即可执行
2. **SQL 脱敏**：输出报告中的 SQL 文本可能包含敏感数据（表名、字段值），如实展示但不额外暴露
3. **凭据安全**：不在输出中展示任何凭据信息
4. **数据量控制**：Top N 不超过 10 条，重点分析前 3-5 条，避免 token 消耗过大
5. **EXPLAIN 安全**：EXPLAIN 本身不执行查询，不会对集群产生负载影响

## 经验沉淀库

| 经验                             | 置信度 | 说明                                                                                                                  |
| -------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------- |
| 分区键未命中是最常见的慢查询原因 | ⭐⭐⭐ | WHERE 条件未包含分区键字段（如 toYYYYMM(date)），导致全分区扫描                                                       |
| SELECT \* 在宽表上性能极差       | ⭐⭐⭐ | ClickHouse 列式存储，SELECT \* 读取所有列文件，应只选需要的列                                                         |
| 大表 JOIN 小表时应将小表放右侧   | ⭐⭐   | ClickHouse 默认将右表加载到内存做 hash join                                                                           |
| PREWHERE 比 WHERE 更高效         | ⭐⭐   | PREWHERE 先过滤再读取其他列，减少 IO；适用于过滤率高的条件                                                            |
| 跳数索引对低基数列效果有限       | ⭐⭐   | minmax 索引对基数低的列（如 status）裁剪效果差，考虑 bloom_filter                                                     |
| IN 子查询应改写为 JOIN           | ⭐⭐   | IN (SELECT ...) 可能重复执行子查询，改写为 JOIN 性能更优                                                              |
| \_local 表只含当前分片数据       | ⭐⭐   | 表名以 `_local` 结尾表示本地表，SELECT 结果仅为单分片数据而非全集群数据；需确认是否应查分布式表（去掉 `_local` 后缀） |
