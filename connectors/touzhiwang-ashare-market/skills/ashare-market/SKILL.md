---
name: ashare-market
display_name: 吾道 MCP：一级市场资本数据工具服务
display_name_en: Wudao MCP – Primary Market Capital Data Tools
description: 覆盖 A 股一级市场 IPO、再融资、并购重组的审核与发行上市数据，以及市场统计、公司资本运作、券商业务统计、证监会公开监管处罚与资本市场法规信息。通过 MCP 标准协议供 AI 应用与智能体调用，不提供股票行情资讯、行情分析或市场监管政务服务。
description_zh: 覆盖 A 股一级市场 IPO、再融资、并购重组的审核与发行上市数据，以及市场统计、公司资本运作、券商业务统计、证监会公开监管处罚与资本市场法规信息。通过 MCP 标准协议供 AI 应用与智能体调用，不提供股票行情资讯、行情分析或市场监管政务服务。
description_en: Wudao MCP provides primary-market capital data tools covering A-share IPO, refinancing, and M&A/restructuring review and issuance/listing data, together with market statistics, corporate capital operations, brokerage business statistics, publicly available CSRC regulatory penalties, and capital-market regulatory information. It is exposed via the MCP standard for AI applications and agents. It does not provide stock market quotes, market analysis, or market-regulation government services.
version: 1.0.3
author: 吾道
---

# 吾道 MCP：一级市场资本数据工具服务 使用指引

连接本连接器后，通过 MCP Tools 查询资本市场数据。所有写库类操作极少；查询类工具可直接调用。结果受账号订阅与产品口径影响。

## 认证前置

- 本连接器走 **OAuth**：用户在 WorkBuddy 点击连接后浏览器授权，由客户端携带 Bearer Token 调用 MCP。
- 授权失效（`AUTH_ERROR` / HTTP 401）时，提示用户重新连接连接器完成授权。
- 同账号可并行调用；**403** 表示无权限。
- 单次工具调用上限约 **2 分钟**；超时后再重试，勿因偶发偏慢判定不可用。

## 调用总原则

### 1. 先 search，再 detail

| 实体   | 先调用                                     | 取得 ID         | 再调用                                                  |
| ---- | --------------------------------------- | ------------- | ---------------------------------------------------- |
| 公司   | `company_search`                        | `company_id`  | `company_detail_*` / `company_project_*`             |
| 券商   | `firm_search`                           | `firm_id`     | `firm_detail_*` / `firm_person_*` / `firm_analyze_*` |
| 投资者  | `investor_search`                       | `investor_id` | `invest_*` 筛选或明细                                     |
| 项目详情 | `project_list` / `company_project_list` | 项目 id         | `company_project_detail`                             |

勿臆造 ID；详情失败时优先怀疑 ID 无效。

### 2. market vs invest（`primary_category`）

- **市场侧**（`market_*` / `issuance_*` / `audit_*` / `project_list` / `firm_analyze_*`）：常见 IPO / 再融资 / 并购重组（以工具 enum 为准）。
- **投资侧**（`invest_*` / `invest_events` / `ipo_non_investors`）：仅 IPO / 定向增发（勿传「再融资」）。
- 全市场发行/审核统计用 `market_*`；投资者认购与收益用 `invest_*`。
- 投资偏好/概况：`invest_overview` 等已合并 bar/cross，用 `mcp_view=bar|cross` 切换视图。

### 3. 易错必填

- `invest_profit_analysis`：必须传 `profit_scale_range_list`；人数/金额概况用 `invest_overview`。
- `supervise_news_list`：`start_date` / `end_date` 必填（YYYY-MM-DD），`end_date` 不得晚于当天。
- 数组参数传 JSON 数组（如 `["IPO"]`），勿传裸字符串。

### 4. 单位与日期

- 募资/规模区间对外统一**万元**（10 亿元 = `100000`）；`project_list` 由 MCP 换算为上游亿元。
- 日期 YYYY-MM-DD；未说明时开始日常见当年初，结束日常见当天。
- 列表先用较小 `page_size`；账号统计口径用 `get_global_config` / `update_global_config`（勿用已下线的 `*_fields`）。

### 5. 结果解读

- 统计类返回含 `_stat_basis_applied`（账号口径）与 `_criteria_applied`（本次筛选）；解读数字时先看这两项。
- `market_ranking`（`ranking_type=项目`）按**项目**计：同一公司多次资本运作会分行出现，属正常口径，勿按 `company_id` 去重合并后解读。

## 能力地图（按场景选工具）

| 用户意图                | 优先工具                                                                                                                 |
| ------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 公司/券商/投资者是谁         | `company_search` / `firm_search` / `investor_search`                                                                 |
| 市场一览、阶段、趋势、板块、行业、区域 | `market_overview`、`market_status_analysis`、`market_trend_analysis`、`market_*`                                        |
| 券商排名与分析             | `market_ranking`、`firm_analyze_*`、`firm_detail_*`                                                                    |
| 发行价格/费用/首日涨跌        | `issuance_*`                                                                                                         |
| 审核进度、撤回否决、现场检查      | `audit_*`、`audit_events`                                                                                             |
| 投资热度、排名、收益、认购价      | `invest_heats`、`invest_ranking`、`invest_profit_analysis`、`invest_apply_price_analysis`、`invest_overview`（`mcp_view`） |
| 项目列表/详情             | `project_list`、`company_project_list`、`company_project_detail`                                                       |
| 监管处罚、法规、资讯          | `listed_company_punishment*`、`regulatory_punishment*`、`supervise_laws*`、`supervise_news_*`                           |

## 错误码（看 `error_code`）

| 码                  | 含义             | 处理               |
| ------------------ | -------------- | ---------------- |
| `AUTH_ERROR`       | 登录失效（HTTP 401） | 请用户重新连接连接器       |
| `PERMISSION_ERROR` | 无权限（HTTP 403）  | 说明账号无该数据权限       |
| `QUOTA_ERROR`      | 配额/限流          | 稍后重试或缩小查询范围      |
| `PARAM_ERROR`      | 参数错误           | 按工具 schema 修正后重试 |
| `NO_DATA`          | 无结果            | **不是故障**；如实告知无数据 |
| `UPSTREAM_TIMEOUT` | 超时             | 可重试一次；缩小筛选条件     |
| `UPSTREAM_ERROR`   | 上游失败           | 说明暂时不可用，勿伪装成无数据  |

## 典型对话示例

1. 「宁德时代最近资本运作」→ `company_search` → `company_project_list` / `company_project_detail`
2. 「中信证券项目阶段分布」→ `firm_search` → `firm_analyze_progress`（或 `firm_detail_overview`）
3. 「今年科创板 IPO 募资规模」→ `market_fundraising_scale` / `market_listing_board`（`primary_category` 取 IPO，板块取科创板）
4. 「某投资者定增收益」→ `investor_search` → `invest_profit_analysis`（带 `profit_scale_range_list`）或 `invest_overview`
5. 「近一周监管资讯」→ `supervise_news_list`（必填起止日期）→ 需要正文时再 `supervise_news_detail`

## 高风险与确认

- 本连接器以只读查询为主；若调用可写工具（如 `update_global_config`），修改前先向用户确认要改的配置与目标值。
- 勿在回复中回显完整 Access Token / Refresh Token。
