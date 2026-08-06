---
name: shanglv-mcp-gateway-skill
description: 企业级 MCP 授权网关技能 - 聚合财务发票查询与银行账户交易数据（客户/账户/余额/交易/对账单/回单/小时余额），统一走 Keycloak OAuth 2.1 + PKCE 认证与细粒度授权
version: "1.1.0"
author: "shanglv-aicoding-agent team"
---

# MCP Gateway Skill

本 Skill 通过 WorkBuddy Connector 接入企业级 MCP 授权网关（LiteLLM 聚合层），让 AI 能在**统一认证、统一授权、统一审计**的前提下，调用两类企业内部 MCP 工具：财务发票（finance）、银行账户交易数据（yztdata）。

> **关键差异点**：本 Connector 不是直接连到某个 MCP Server，而是连到 LiteLLM 网关。网关在每次 `tools/call` 前执行 PEP（Policy Enforcement Point）四步决策链：JWT 鉴权 → OpenFGA ReBAC（工具调用权 + 行级读取权）→ OPA ABAC（时段/角色/字段脱敏）→ 双写审计。AI 只需要关心工具本身的语义，授权由网关透明处理。

## 认证说明（OAuth 2.1 + PKCE）

- **认证流程**：WorkBuddy 在用户首次连接时，通过第 11 章 MCP 连接器 OAuth 流程自动完成。用户在浏览器中看到 Keycloak 授权页（realm `shanglv`），输入企业账号后点击允许即可。
- **PKCE**：采用 `code_challenge_method: S256`，WorkBuddy 作为公共客户端，无 `client_secret`。
- **Token 有效期**：`access_token` 1 小时，`refresh_token` ≥ 30 天，过期后 WorkBuddy 自动刷新，用户无感。
- **Token 作用域**：Token 中携带 `tenant_id`、`preferred_username` 等声明，网关据此做租户隔离和行级安全（RLS）。
- **重新授权**：如 `refresh_token` 也过期，WorkBuddy 会引导用户重新授权。AI 遇到 401 且无法自动刷新时，提示用户前往 WorkBuddy 设置页重连。
- **授权端点**（由网关 `/.well-known/oauth-protected-resource` + `/.well-known/oauth-authorization-server` 自动发现，无需手填）：
  - 授权：`https://mcp-gateway.yql.net/realms/shanglv/protocol/openid-connect/auth`
  - Token：`https://mcp-gateway.yql.net/realms/shanglv/protocol/openid-connect/token`
  - JWKS：`https://mcp-gateway.yql.net/realms/shanglv/protocol/openid-connect/certs`

## 可用工具

网关将上游两个 MCP Server 的工具聚合成 `<server>-<tool>` 命名格式（如 `finance-query_invoice`、`yztdata-search_customers`）。调用 `tools/list` 可拉取当前用户有权访问的完整工具清单。当前共 **13 个工具**：1 个 finance + 12 个 yztdata。

---

## 一、finance 工具

### finance-query_invoice — 查询发票

查询当前租户下指定发票明细，或列出所有可见发票。受 PostgreSQL 行级安全（RLS）保护，跨租户查询直接被数据库拦截，不返回任何行。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| invoice_id | string | ✅ | 发票号。传 `*` 列出当前租户所有可见发票（最多 100 条） |

**返回**：

- 单条：`{id, tenant_id, amount, description, created_at}`
- 列表：`{invoices: [...]}`
- 无权限：`{error: "not found or not accessible (NO_PERM_ROW_LEVEL)"}`（不区分「不存在」与「无权限」，防探测）

**使用示例**：

- 查单张发票：`finance-query_invoice(invoice_id="INV-001")`
- 列当前租户发票：`finance-query_invoice(invoice_id="*")`

**注意事项**：

- 金额（`amount`）字段：当调用方角色非 `finance_admin` 时，OPA 会下发脱敏义务，网关将 `amount` 替换为 `***`。AI 看到脱敏值应理解为「有权限查存在性，无权限看金额」。
- 跨租户查询（如 alice 查 dept_b 的 INV-002）会被 RLS 静默拦掉，返回 `not found or not accessible`，**不是**报权限错误。
- 全局黑名单工具 `finance:delete_all` / `finance:bulk_export` 不在本 Connector 暴露，任何调用都会被 PEP 拦截。

---

## 二、yztdata 工具（银行账户交易数据）

yztdata 上游提供企业银行账户的完整数据能力：从客户档案 → 银行账户 → 实时余额 → 交易明细 → 对账单 → 回单 → 小时级余额监控。工具命名前缀为 `yztdata-`。

### yztdata-search_customers — 搜索客户

按客户名称、统一社会信用代码、联系人、手机号模糊匹配，返回客户列表。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | - | 搜索关键词，留空返回所有客户 |
| limit | integer | - | 返回数量上限，默认 20，最大 100 |

**返回**：客户列表数组，每条含客户编号、名称、统一社会信用代码、联系人、手机号等。

**使用示例**：

- 按名称模糊搜索：`yztdata-search_customers(keyword="科技")`
- 列出所有客户（前 50 条）：`yztdata-search_customers(limit=50)`

**注意事项**：

- 模糊匹配可能返回多条，AI 应让用户确认目标客户后再深入查档案。
- 脱敏：非授权角色看到的手机号、统一社会信用代码可能被脱敏为 `***`。

---

### yztdata-get_customer_profile — 获取客户完整档案

获取客户基本信息 + 关联的所有银行账户 + 每个账户的最新余额快照。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| customer_id | string | ✅ | 客户编号，如 `CUST2024001` |

**返回**：`{basic_info: {...}, bank_accounts: [{account_no, bank_name, balance, ...}]}`

**使用示例**：

- 查客户全档案：`yztdata-get_customer_profile(customer_id="CUST2024001")`

**注意事项**：

- 返回的账户余额是**最新快照**，如需历史时点余额用 `yztdata-get_account_balance` 传 `snapshot_date`。
- 跨主体（集团场景）下，basic_info 里可能含 `entity_id`，后续按子公司过滤交易时需要。

---

### yztdata-list_customer_accounts — 列出客户银行账户

列出客户所有银行账户，可按银行过滤，每个账户附带最新余额快照。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| customer_id | string | ✅ | 客户编号 |
| bank_name | string | - | 银行名称（模糊匹配，可选） |

**返回**：账户数组，每条含账户号、银行名、账户类型、最新余额、更新时间。

**使用示例**：

- 列某客户所有账户：`yztdata-list_customer_accounts(customer_id="CUST2024001")`
- 只看建行账户：`yztdata-list_customer_accounts(customer_id="CUST2024001", bank_name="建设")`

---

### yztdata-get_account_balance — 获取账户余额

获取指定银行账户的余额，支持查询历史时点余额。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号（支持脱敏形式如 `6225****1234`） |
| snapshot_date | string | - | 快照日期 `YYYY-MM-DD` 或 `YYYY-MM`，不传返回最新 |

**返回**：`{account_no, balance, snapshot_date, currency, ...}`

**使用示例**：

- 查最新余额：`yztdata-get_account_balance(account_no="6225****1234")`
- 查上月末余额：`yztdata-get_account_balance(account_no="6225****1234", snapshot_date="2026-06")`

**注意事项**：

- 历史时点余额依赖快照表，若该日期无快照可能返回 `null` 或最近邻快照，AI 应提示用户日期可能无数据。

---

### yztdata-query_transactions — 查询交易明细

查询账户交易明细，支持日期范围、借贷方向、金额区间、对方户名、关键词、业务类型多维筛选，分页返回。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号 |
| start_date | string | - | 起始日期 `YYYY-MM-DD`（包含） |
| end_date | string | - | 结束日期 `YYYY-MM-DD`（包含） |
| txn_type | string | - | `DEBIT`（借/出）或 `CREDIT`（贷/入） |
| min_amount | number | - | 最小金额 |
| max_amount | number | - | 最大金额 |
| counterparty | string | - | 对方户名（模糊匹配） |
| keyword | string | - | 关键词（匹配摘要/对方/渠道） |
| biz_category | string | - | 业务类型，可选值见 `yztdata-list_biz_categories` |
| biz_scenario | string | - | 业务场景（精确匹配，如「外贸TT收汇-跨境汇款」） |
| counterparty_type | string | - | 对方类型（`客户` / `供应商`） |
| entity_id | string | - | 法人主体 ID（集团场景按子公司过滤，先调 `get_customer_profile` 获取） |
| page | integer | - | 页码，默认 1 |
| page_size | integer | - | 每页条数，默认 20，最大 200 |

**返回**：`{transactions: [...], total: N, page: P, page_size: S}`

**使用示例**：

- 查最近一个月贷方入账且金额 > 10000：`yztdata-query_transactions(account_no="6225****1234", start_date="2026-06-15", end_date="2026-07-15", txn_type="CREDIT", min_amount=10000)`
- 按对方户名查：`yztdata-query_transactions(account_no="6225****1234", counterparty="某供应商")`

**注意事项**：

- 大结果集自动分页，AI 拉到第一页后应看 `total` 判断是否还有更多。
- `biz_category` 建议先调 `yztdata-list_biz_categories` 拿可选值再传，避免无效筛选。

---

### yztdata-list_biz_categories — 列出业务类型

列出当前数据中出现的所有业务类型（biz_category），例如：融资类、票据类、扣款类、利息类、税务类、电商及三方支付、日常经营。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | - | 账户号（可选，默认全量统计） |

**返回**：`{categories: ["融资类", "票据类", ...]}`

**使用示例**：

- 列全量业务类型：`yztdata-list_biz_categories()`
- 只看某账户出现的类型：`yztdata-list_biz_categories(account_no="6225****1234")`

---

### yztdata-list_statements — 列出对账单

列出账户的对账单（按月），可按年份过滤。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号 |
| year | string | - | 年份，如 `2025`（可选） |

**返回**：`{statements: [{period: "2025-06", ...}]}`

**使用示例**：

- 列 2026 年所有对账单：`yztdata-list_statements(account_no="6225****1234", year="2026")`

---

### yztdata-get_statement_detail — 获取对账单详情

获取指定期间对账单的完整内容，含借贷汇总、期初/期末余额、生成时间。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号 |
| period | string | ✅ | 期间 `YYYY-MM` |

**返回**：`{period, debit_total, credit_total, opening_balance, closing_balance, generated_at, ...}`

**使用示例**：

- 查 2026 年 6 月对账单：`yztdata-get_statement_detail(account_no="6225****1234", period="2026-06")`

---

### yztdata-list_receipts — 列出回单

列出账户的电子回单，每个回单附 `download_url`，可通过 HTTP GET 下载真实 PDF/图片文件。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | - | 账户号（与 `customer_id` 二选一） |
| customer_id | string | - | 客户编号（查该客户所有账户的回单） |
| txn_id | string | - | 交易 ID（精确匹配） |
| start_date | string | - | 起始日期 `YYYY-MM-DD` |
| end_date | string | - | 结束日期 `YYYY-MM-DD` |
| limit | integer | - | 返回上限，默认 50，最大 500 |

**返回**：`{receipts: [{txn_id, date, amount, download_url, ...}]}`

**使用示例**：

- 查某账户最近 100 条回单：`yztdata-list_receipts(account_no="6225****1234", limit=100)`
- 按客户查所有回单：`yztdata-list_receipts(customer_id="CUST2024001")`

**注意事项**：

- `download_url` 可能是带签名的临时链接，有时效性，AI 应提示用户尽快下载。
- 非授权用户可能拿到回单列表但 `download_url` 被脱敏为 `***`（仅能看存在性，不能下载）。

---

### yztdata-get_hourly_balance — 获取某月小时余额

获取某账户某月所有小时余额快照（每天 24 小时，一个月约 720-744 条）。可用于观察日内余额波动、监控大额进出、识别异常时段。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号（脱敏形式如 `6216****2782`） |
| period | string | ✅ | 月份 `YYYY-MM`，如 `2026-07` |

**返回**：`{snapshots: [{timestamp: "2026-07-01T00:00:00", balance: ...}], count: N}`

**使用示例**：

- 查 2026 年 7 月小时余额：`yztdata-get_hourly_balance(account_no="6216****2782", period="2026-07")`

**注意事项**：

- 数据量大（720+ 条/月），AI 调用前应向用户确认是否真的需要小时粒度，通常 `get_hourly_balance_stats` 摘要更够用。
- 异常时段（如凌晨 3 点大额进出）可能是资金异常信号，AI 看到应主动提示用户关注。

---

### yztdata-get_hourly_balance_range — 查询时间区间小时余额

查询指定时间区间内的小时余额快照（自动覆盖涉及的月份），可用于拉取连续时段数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号 |
| start_time | string | ✅ | 起始时间 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS` |
| end_time | string | ✅ | 结束时间 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS` |

**返回**：`{snapshots: [...], count: N}`

**使用示例**：

- 拉最近一周小时余额：`yztdata-get_hourly_balance_range(account_no="6216****2782", start_time="2026-07-08", end_time="2026-07-15")`

---

### yztdata-get_hourly_balance_stats — 小时余额统计摘要

获取某月小时余额的统计摘要：峰值/谷值/平均值/最大单小时变动额/有交易的小时数。适合做监控指标。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| account_no | string | ✅ | 账户号 |
| period | string | ✅ | 月份 `YYYY-MM` |

**返回**：`{peak, trough, average, max_hourly_delta, active_hours, period}`

**使用示例**：

- 查 2026-07 余额统计摘要：`yztdata-get_hourly_balance_stats(account_no="6216****2782", period="2026-07")`

**注意事项**：

- 优先调本工具做快速诊断，发现异常（如 `max_hourly_delta` 异常大）再调 `get_hourly_balance` 拉明细排查。

---

## 错误处理

PEP 拒绝时返回标准 MCP `isError: true` 响应（HTTP 仍为 200），AI **必须检查 `result.isError` 而非 HTTP status**。常见错误细分：

| 错误码 | 含义 | AI 应对 |
|--------|------|---------|
| `UNAUTHENTICATED` | JWT 缺失/过期且刷新失败 | 提示用户前往 WorkBuddy 设置页重新授权 |
| `NO_TOOL_PERMISSION` | 用户无该工具的 `caller` 关系 | 告知用户无此工具权限，建议联系管理员申请 |
| `NO_READER_PERMISSION` | 有工具调用权但无行级读取权 | 告知用户对该数据行无读取权限，结果不可见 |
| `BLOCKED_TOOL` | 工具在全局黑名单 | 不应尝试调用，说明该操作被策略禁止 |
| `OFF_BUSINESS_HOURS` | 非工作时间调用敏感工具 | 告知用户当前时段不可用，建议工作时间重试 |
| `OPA_UNAVAILABLE` | OPA 熔断（连续 5 次失败） | 网关自动降级为 FGA-only 模式，AI 应提示「授权降级中，部分策略可能不生效」 |

## 注意事项

1. **租户隔离是硬约束**：所有工具调用都带 `X-Tenant-Id`，由网关从 JWT 注入，AI 无法绕过。AI 不应在参数里手填租户字段。
2. **审计全覆盖**：每次 `tools/call`（含 ALLOW 和 DENY）都双写 PostgreSQL + ClickHouse。AI 应告知用户操作会被审计。
3. **降级语义**：OPA 熔断时网关降级为「FGA-only + 标记 DEGRADED」，AI 看到此标记应提示用户当前为降级授权模式。
4. **缓存失效**：权限变更后可由运维调 `POST /pep/cache/invalidate-user` 立即生效；AI 无需关心，但可提示用户「权限变更后可能需要几分钟生效或联系运维立即刷新」。
5. **优先调 tools/list**：上游工具集会随版本演进，AI 拿到可用工具清单后再决定调用，不要假设工具固定不变。
6. **账户号脱敏形式**：yztdata 工具的 `account_no` 参数普遍支持脱敏形式（如 `6225****1234`），AI 不应尝试还原完整卡号，直接用脱敏形式调用即可。
7. **业务类型枚举**：调用 `yztdata-query_transactions` 传 `biz_category` 前，建议先调 `yztdata-list_biz_categories` 拿可选值，避免无效筛选。
8. **集团多主体**：`yztdata-query_transactions` 的 `entity_id` 用于集团场景按子公司过滤，需先调 `yztdata-get_customer_profile` 获取 `entity_id` 再传。
