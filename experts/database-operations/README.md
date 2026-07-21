# database-operations

数据库设计调优专家 —— 面向 PostgreSQL 的表结构设计、查询性能调优、零停机迁移、EF Core 工作流、索引策略与缓存/分区优化的专家包。

## 能力概览

加载本专家后，可直接用自然语言发起数据库相关任务，专家会遵循"先测量、后优化"的原则输出 SQL、迁移脚本与配置：

- **表结构设计**：用户表、审计日志、软删除视图、全文检索（`tsvector` + GIN），含枚举类型、约束与策略性索引
- **查询调优**：用 `EXPLAIN (ANALYZE, BUFFERS)` 解读执行计划；通过 `pg_stat_statements` / `pg_stat_user_indexes` 定位慢查询、未用索引与 N+1 模式
- **索引策略**：单列、复合（列顺序）、部分、覆盖（`INCLUDE`）、GIN(JSONB)、表达式索引；生产环境一律 `CREATE INDEX CONCURRENTLY`
- **迁移工程**：安全加列、零停机重命名、范围分区 + 自动建分区函数；EF Core 的 `migrations add/update/script --idempotent` 与回滚
- **缓存与会话**：Redis 查询缓存（TTL + 失效）、物化视图（`REFRESH ... CONCURRENTLY`）、连接池配置与健康监控
- **运行时监控**：活跃连接、长事务、表/索引体积、表膨胀（dead tuple 比例）等诊断查询

## 使用方式

在 WorkBuddy 中加载本专家后，直接用自然语言提问即可，例如：

- 分析这条慢查询并给出索引优化方案
- 为用户订单系统设计 PostgreSQL 表结构
- 生成零停机的字段重命名迁移脚本

## 工作原则

- **先测量后优化**：任何调优前先跑 `EXPLAIN ANALYZE`，没有证据不下结论。
- **零停机迁移**：先加后删，新增列/索引在前，破坏性变更在后；生产索引用 `CONCURRENTLY`。
- **务必规划回滚**：每个迁移配套反向脚本，先在非生产环境验证。
- **金额用 `DECIMAL`**：金额字段使用 `DECIMAL(10,2)` 或整数分，禁用浮点。

## 安全须知

- 生成的 SQL/迁移在被执行前必须由用户在非生产环境验证，回滚流程必须先演练。
- 审计触发器可能将敏感字段写入审计表，落地前需过滤或脱敏。
- 缓存与物化视图存在数据陈旧风险，需同时给出失效规则与刷新节奏。

## 来源

改编自 buildwithclaude 的 database-operations（Dave Poon，MIT），由 jgarrison929 发布于 ClawHub。
