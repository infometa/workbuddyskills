# TAPD OPENAPI SKILL

## 功能特性

- **需求管理** — 查询、统计 TAPD 需求（Stories）
- **缺陷管理** — 查询、统计 TAPD 缺陷（Bugs）
- **任务管理** — 查询 TAPD 任务（Tasks）
- **迭代管理** — 查询 TAPD 迭代（Iterations）信息
- **Wiki 管理** — 查询、统计 TAPD Wiki 文档
- **问题解答** — 综合 TAPD 数据回答用户问题

## 使用前配置

使用前至少需要配置以下环境变量：

- `TAPD_TOKEN`：必填，TAPD OpenAPI 的认证 Token
- `TAPD_WORKSPACE_IDS`：建议配置，TAPD 项目 ID 列表，多个项目用英文逗号分隔

可选环境变量：

- `TAPD_API_ENDPOINT`：TAPD API 地址
- `TAPD_WORKSPACE_ID`：单个 TAPD 项目 ID，兼容旧配置

说明：

- `TAPD_WORKSPACE_IDS` 优先级高于 `TAPD_WORKSPACE_ID`
