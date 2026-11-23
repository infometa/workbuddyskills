---
name: hithink-finance-data
description: '通过 hithink-finance CLI 管理本地 DuckDB 数据的初始化、同步、状态、质量校验、迁移、修复、清理和删除，以及只读 SQL 查询和文件导出。'
---

# hithink-finance-data

本地数据生命周期和 SQL 入口。负责让数据可用、可校验、可导出，而不是解释所有研究结论。

## 前置条件表

| 条件                         | 操作                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------- |
| 需要认证、共用输出或维护指引 | 按需读取 [共享规则](../hithink-finance-shared/SKILL.md)，同会话已加载内容可复用 |
| 选定命令或版本变化           | 用目标 `schema <id> --format json` 核对参数；命令未知时再读取 `capabilities`    |
| 需要执行下表某个命令         | 先读取对应 reference 文件，不要只凭命令名猜参数                                 |
| 全市场、分页、多标的或长区间 | 使用命令声明的 `--output <path>` 落盘，只报告摘要                               |

## 快速决策

| 用户意图               | 首选命令 / 路由                         |
| ---------------------- | --------------------------------------- |
| 首次建库或从 dump 导入 | `data init`                             |
| 增量/重新同步本地数据  | `data sync`                             |
| 查看库路径和 schema    | `data status`                           |
| 质量校验               | `data validate`                         |
| 迁移计划或应用         | `data migrate`                          |
| 重建复权等派生数据     | `data repair`                           |
| 清理下载缓存           | `data clean`                            |
| 删除本地库             | `data remove --plan` 先预览             |
| 查看表/视图            | `db describe`                           |
| 只读 SQL 查询          | `db query --sql <sql>`                  |
| 大结果导出             | `db export --sql <sql> --output <file>` |

## Shortcuts

| 命令                                         | 何时使用                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| [data clean](references/data-clean.md)       | 只清理 CLI 管理的下载缓存，不删除数据库。                                                                          |
| [data init](references/data-init.md)         | 远端初始化先通过 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。本地文件导入无需远端认证。 |
| [data migrate](references/data-migrate.md)   | 默认只输出迁移计划；应用迁移前让用户确认。                                                                         |
| [data remove](references/data-remove.md)     | 高风险操作；先运行 `--plan` 报告路径和大小。                                                                       |
| [data repair](references/data-repair.md)     | 用于重建派生复权因子等本地派生数据。                                                                               |
| [data status](references/data-status.md)     | 查看库路径和 schema 版本；该命令可创建缺失数据库，严格只读任务须先用文件系统确认目标存在。                         |
| [data sync](references/data-sync.md)         | 需要当前可用凭据，先按 shared 查看只读 auth status，或提供本次显式 Key。                                           |
| [data validate](references/data-validate.md) | 质量检查会先应用普通迁移。严格只读研究须先确认目标文件存在，并用 data migrate 的默认计划确认 versions 为空。       |
| [db describe](references/db-describe.md)     | 查询表和视图清单，并应用普通迁移；严格只读研究使用 db query 查询 information_schema。                              |
| [db export](references/db-export.md)         | 用于大结果或下游 pandas/notebook 消费。                                                                            |
| [db query](references/db-query.md)           | 只读 SQL；小结果才可直接读取 JSON。                                                                                |

## 原生命令与 schema

```bash
hithink-finance capabilities --format json
hithink-finance schema <capability-id> --format json
hithink-finance data <command> --help
hithink-finance db <command> --help
```

schema 提供当前命令选项；reference 补充业务参数关系和验收方法。全局参数、凭据与输出约定见共享规则。

## 边界声明

- SQL 必须只读；写入、DDL、删除或外部副作用不属于 `db query`。
- 删除数据库或清除数据前先用 plan/状态输出让用户确认，真正删除需要显式 `--yes`。
- `data init` / `data sync` 下载阶段可立即取消；数据库导入提交后会先完成复权、元数据和质量一致性收尾，再报告取消。
- 需要限制本地资源时使用 `HITHINK_FINANCE_DUCKDB_THREADS` / `HITHINK_FINANCE_DUCKDB_MEMORY_LIMIT`；`DATA_LOCK_OPEN_FAILED` 应检查状态目录权限和存储。
- 查询结果很多时用 `db export --output <file>`，不要回显全表。
