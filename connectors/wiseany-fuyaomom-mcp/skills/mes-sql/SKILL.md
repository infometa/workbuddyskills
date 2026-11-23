---
name: mes-sql
description: 通过 MCP 工具查询扶摇MOM工厂运营数据（生产工单、设备状态、质量检验、库存等），支持表结构查询与只读SQL分析。
---

# 扶摇MOM 工厂运营数据查询

通过 MCP 工具查询扶摇 MOM 工厂运营数据（SQL Server）的表结构、数据和统计信息，覆盖生产工单与报工、设备运维与报警、质量检验与不良、库存与出入库、基础主数据等业务域。

## 认证与连接

- 首次连接时 WorkBuddy 会弹出浏览器完成 OAuth 授权（使用 MES 网关账号登录）。
- Access Token 由 WorkBuddy 自动携带并续期，无需手动处理。
- 若工具返回 `unauthorized` / 授权失效错误，请引导用户在 WorkBuddy 中重新连接该连接器。

## 可用工具

### 1. list_tables
列出数据库中所有表（含表名、行数、描述、分类）。无参数。
- 返回：`tables`（数组）、`totalCount`、`summary`（文字摘要）
- 建议先调用本工具了解数据范围，再用其他工具深入查询。

### 2. get_table_details
获取指定表的结构详情（列名、类型、是否可空、主键、描述）。
- 参数：
  - `tableName`（必填，字符串）：表名，支持 `dbo.表名` 格式；也支持数组批量查询、对象批量查询
  - `schema`（可选，默认 `dbo`）
- 返回：`data`（列结构数组）、`count`、`errors`

### 3. execute_sql
执行 SQL 查询（仅支持 SELECT，拒绝增删改）。
- 参数：`sql`（必填，字符串）
- 返回：`data`（行数组）、`columns`、`rowCount`、`markdown`（表格）
- 安全限制：非 SELECT 语句直接返回错误；建议先了解表结构再拼接查询，避免全表扫描。

### 4. test_connection
测试数据库连接是否正常。无参数。
- 返回：`success`、`message`

### 5. get_database_info
获取数据库信息（名称、SQL Server 版本、大小、表数量、活动连接数）。无参数。
- 返回：`databaseName`、`serverVersion`、`sizeMB`、`tableCount`、`activeConnections`、`markdown`

### 6. peek_table
快速查看表数据（默认前 10 行，上限 1000 行）。
- 参数：
  - `tableName`（必填）：表名
  - `rows`（可选，默认 10，上限 1000）
  - `schema`（可选，默认 `dbo`）
- 返回：`rows`、`columns`、`rowCount`、`markdown`

## 典型调用示例

1. 用户问「当前生产中的工单有哪些」→ 先 `list_tables` 或 `get_table_details` 了解工单相关表结构，再 `execute_sql` 按状态查询生产中的工单
2. 用户问「哪些设备处于报警或停机状态」→ 查找设备状态表，`execute_sql` 按报警/停机状态过滤
3. 用户问「最近一周质量检验不良率排名前三的不良类型」→ 查询质检表按不良类型分组统计，`execute_sql` 排序取前三
4. 用户问「物料 ZG01001 在各仓库的库存」→ 查询库存表按物料编码与仓库分组汇总
5. 用户问「数据库里有哪些表」→ 调用 `list_tables`
6. 用户问「XX 表有哪些字段」→ 调用 `get_table_details`，tableName 传表名
7. 用户想快速看某表数据 → `peek_table`

## 错误场景与恢复

| 错误 | 含义 | 处理方式 |
| --- | --- | --- |
| `unauthorized` / `invalid_grant` | OAuth 凭证失效 | 引导用户在 WorkBuddy 中重新连接 |
| `no_route` | 用户未配置 Agent 路由 | 联系管理员在网关管理台配置路由映射 |
| `agent_offline` | 内网 MCP Agent 不在线 | 告知用户服务暂不可用，稍后重试 |
| `agent_timeout` | 单次调用超过 30 秒 | 建议缩小查询范围（加 WHERE / TOP）后重试 |
| `只允许执行 SELECT 查询` | SQL 不是 SELECT | 改写为只读查询 |

## 注意事项

- 所有查询为只读操作，不修改生产数据。
- 大表查询请务必带 WHERE 条件或 TOP 限制，避免超时。
- 表名/列名来自生产库，可能使用拼音或缩写命名，必要时用 `list_tables` / `get_table_details` 确认。
