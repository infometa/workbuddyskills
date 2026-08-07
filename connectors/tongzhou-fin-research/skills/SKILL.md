---
name: tongzhou-fin-research
description: 连接公开行情、研报检索、行业图谱与同舟投研材料，为股市研究提供可复核证据。
description_zh: 连接公开行情、研报检索、行业图谱与同舟投研材料，为股市研究提供可复核证据。
description_en: Connects market data, research, industry graphs, and Tongzhou evidence for public-equity analysis.
version: 0.21.2
author: LingYue Tech
---

# 同舟金融研究连接器

使用本连接器查询公开市场数据和研究材料。它是四类只读研究来源的统一入口，不用于读取个人持仓、交易历史、私有笔记，也不执行交易。

## 连接与认证

- 仅在连接器显示已连接后调用工具。
- 本连接器使用 MCP 原生 OAuth。首次访问受保护资源时由 WorkBuddy 打开浏览器完成授权；`connector-meta.json` 不设置 `auth_mode`、`mcp.json` 不写静态 `headers` 是有意设计。
- 不要求用户在聊天中粘贴 API Key、Token、验证码或其他凭证。
- 认证失败时提示用户重新连接。不要改用同名全局工具，不要用缓存或模型记忆伪装成实时结果。
- 服务端是无状态 Streamable HTTP；客户端不得把缺少 `mcp-session-id` 当成失败条件。

## 路由

工具名使用固定前缀。先选来源，再选该来源中最窄的工具。

| 用户需求 | 工具前缀 | 首选路径 |
|---|---|---|
| 行情、K 线、估值、财务、宏观、成分 | `fin_data__` | 先解析证券/篮子，再取数据 |
| 新闻、公告、研报、事件、文档正文 | `doc_search__` | 先搜索列表，需要正文时再取详情 |
| 行业身份、行业图谱、产业链、公开因子 | `fin_graph__` | 跨来源研究先统一行业身份 |
| 同舟要闻、分析师解读、行业观点、研究图表 | `same_boat__` | 先查目录/列表，再用返回 ID 取详情 |

## 高频工具

### `fin_data__` 结构化金融数据

| 工具 | 核心参数 | 何时使用 |
|---|---|---|
| `fin_data__search_security` | `keyword`；`market=all/a_stock/etf/hk_stock`；`limit` | 名称、代码或市场不确定时先解析证券 |
| `fin_data__search_security_with_market_data` | `keyword`；`market`；`sort_by=match/amount/volume`；`limit` | 搜索候选并一次附加最新可得可比行情；行情缺失时仍保留身份 |
| `fin_data__rank_etf_candidates` | `keyword`；可选 `tracking_index_id`；`sort_by`；`limit<=30` | 比较跟踪同一指数/主题的ETF候选及公开日频流动性字段，不作为产品推荐 |
| `fin_data__get_security_profile` | `ticker`；`market=a_stock/etf/hk_stock` | 已知代码后核对公司、交易所和行业身份 |
| `fin_data__get_latest_snapshot` | `ticker`；`market=a_stock/index` | 单只 A 股或指数最新可用快照；必须展示返回日期时间、`snapshot_source` 和新鲜度 |
| `fin_data__batch_get_latest_snapshots` | `tickers`；`market=a_stock/index` | 2-50 个同市场标的最新快照；保留逐标的状态，不循环调用单标的工具 |
| `fin_data__get_kline_series` | `ticker`；`market`；`granularity=daily`；`limit`；`moving_average_windows` | A 股、ETF、港股、指数或概念的日 K 与均线证据 |
| `fin_data__batch_query_data` | `tickers`；`market`；`metrics`；`granularity`；日期/`limit` | 2-20 个同市场标的使用相同口径查询历史序列；总请求行数不超过 5000 |
| `fin_data__compute_market_reaction_windows` / `fin_data__compute_batch_reaction_windows` | 单个/多个 `target`；`events`；`windows` | 已取得事件清单后，批量计算单标的或最多 10 个标的的描述性事件窗口收益 |
| `fin_data__query_financial_indicators` / `fin_data__query_sector_valuation` | 证券或行业标识；报告期/估值口径 | A 股财务关键指标或申万行业 PE/PB |

示例：`fin_data__search_security_with_market_data(keyword="康哲药业", market="hk_stock", limit=5)` 可同时取得身份与最新可得日频行情；需要区间走势时再调用 `fin_data__get_kline_series(ticker="0867.HK", market="hk_stock", limit=30)`。比较多个同市场标的时，改用 `fin_data__batch_query_data`，不得在客户端逐只循环。

### `doc_search__` 公开文档检索

| 工具 | 核心参数 | 何时使用 |
|---|---|---|
| `doc_search__search_hot_news` | `query`；`time_window`；`limit` | 市场热点或行业新闻；查询条件不得为空 |
| `doc_search__search_company_news` | `company` / `ticker`；`time_window`；`limit` | 公司维度新闻，优先结构化公司字段 |
| `doc_search__search_announcements` | `company` / `ticker`；`content_type`；时间窗口 | 上市公司公告列表 |
| `doc_search__search_research_reports` | `company` / `ticker` / `industry`；`content_type`；`time_window`；`limit<=20` | 公司、行业、策略或宏观研报 |
| `doc_search__get_document` | 搜索返回的 `doc_id`；`doc_type`；`max_length` | 用户需要已选文档正文或详情时调用；研报的 `doc_id` 是短期 opaque 引用，必须原样回传且不得展示或持久化 |
| `doc_search__get_document_summaries` | 2-5 个已选结果的 `evidence_ref` + 对应 `doc_type`；`max_length` | 同一证据任务需要核验多篇摘要时有界批量调用；只返回已有摘要和基本来源上下文，不返回原文、原文链接或导出内容 |
| `doc_search__get_document_source_coverage` | 可选 `source_types` | 用户询问文档库样本量、首末日期或来源覆盖缺口时调用；只返回聚合统计 |

示例：`doc_search__search_research_reports(company="贵州茅台", ticker="600519.SH", time_window="1y", limit=5)`。海外公司结果为空时，用可靠公司名去掉 `ticker` 重试一次，不由单一代码格式断言“没有研报”。

### `fin_graph__` 行业与产业链图谱

| 工具 | 核心参数 | 何时使用 |
|---|---|---|
| `fin_graph__resolve_research_identity` | `query`；`query_type=auto/...`；`include_coverage`；`limit` | 行业、主题或来源 ID 跨工具复用前必调 |
| `fin_graph__get_industry_chain_research_map` | `identity` / `lycode` / `frame_id` / `topic`；`focus`；`limit` | 获取产业链或研究框架图谱 |
| `fin_graph__get_public_factor_framework` | `subject`；`graph_type`；`factor_keywords`；`limit` | 获取行业公开因子框架 |
| `fin_graph__get_factor_evidence_panel` | `subject`；`factor_names`；`graph_type` | 获取因子摘要、可用指标和证据边界 |
| `fin_graph__get_factor_metric_values` | `subject`；`factor_names`；`metric_keywords`；`max_points_per_metric` | 因子需要真实公开指标值时补充数据 |

示例：先调用 `fin_graph__resolve_research_identity(query="半导体设备")`，再把返回的 `canonical_id` 或 `graph_subject` 传给后续图谱工具。不要把 `sector_id`、`basket_id`、申万代码或 `frame_id` 相互猜测转换。

### `same_boat__` 同舟投研内容

| 工具 | 核心参数 | 何时使用 |
|---|---|---|
| `same_boat__search_research_sectors` | `query`；`limit` | 解析行业、板块或概念目录 ID |
| `same_boat__list_market_news` | `sector_ids` / `analyst_ids`；`filter_mode`；`scroll_id`；`limit<=50` | 获取市场要闻列表 |
| `same_boat__get_market_news` | 列表返回的 `news_id` | 获取单条要闻摘要 |
| `same_boat__list_sector_viewpoints` | `sector_id`；`time_range`；`scroll_id`；`limit<=50` | 获取某行业下不同分析师观点 |
| `same_boat__get_research_visual_evidence` / `same_boat__generate_content_url_link` | 已返回的内容 ID、`content_type`，必要时 `analyst_id` | 入选内容确需图表或源头复核时调用 |

示例：`same_boat__search_research_sectors(query="半导体设备", limit=5)`，再把返回的 `sector_id` 传给 `same_boat__list_sector_viewpoints`。只有列表或详情没有文章级链接且用户明确需要复核时，才生成内容链接；不得猜 ID 或制造替代链接。

## 调用优先级

1. 先解析证券、行业或主题身份，不猜代码和来源 ID。
2. 两个及以上同市场标的使用对应批量工具；混合市场先按市场分组，每组至多一次批量调用。
3. 用列表/搜索工具取得少量候选，通常 `limit=5-10`。
4. 仅对用户选中或最终入选的候选调用详情、正文、图表或链接工具。
5. 需要综合判断时至少交叉核对两类独立证据，并对齐实体、日期和口径。
6. 工具返回空结果时只说明当前筛选未召回；工具报错时说明来源暂不可用，不把报错写成“没有数据”。

## 覆盖边界

- 最新快照当前以 A 股和指数为主；A 股返回 `realtime_current_table` 时才可描述为交易时段实时源，返回 `latest_trading_day_archive` 时必须写明最新交易日归档；指数按返回时间和新鲜度描述。港股可使用证券解析和日 K，不能把历史末值或快照缺口写成实时价、停牌或无行情。
- `cache_status=stale` 表示实时查询失败时复用的有时限最近结果，必须展示实际数据日期；ETF候选不含AUM、买卖价差、盘口或实时申赎数据。
- 事件窗口收益只是在实际收盘价上的描述性统计，不是因果证明、策略回测、预测或收益承诺；样本不足时保留工具返回的不足状态。
- 公告源当前以巨潮资讯为主，不含港交所披露易原生公告；港股公告空结果是覆盖缺口。
- 公司研报身份支持 A 股、港股、美股和英国市场，但海外代码可能存在供应商格式差异，应按上文重试。
- 行业图谱、产业链图谱和同舟研究目录是不同来源；必须使用解析器返回的映射，不按名称强行等同。
- 视觉结果只消费返回的语义数据、公开 HTTPS 图片和回退表格，不从截图重建精确数值。

## 排错

| 现象 | 处理 |
|---|---|
| 弹出登录或 `401` | 完成浏览器 OAuth 后重试原调用一次；不要索要 API Key |
| `Gateway did not return MCP session ID` | 客户端不应强制会话头；按无状态 Streamable HTTP 继续初始化和调用 |
| 参数无效或实体不明确 | 先用 `search_security` 或 `resolve_research_identity`，复用返回 ID |
| 空结果 | 缩小或修正实体、时间、内容类型；海外研报按名称回退一次；保留覆盖缺口 |
| 超时 | 单次上限为 3 分钟；缩短时间窗口、降低 `limit`、拆分来源后重试，不无限等待 |
| 原文链接不可用 | 只保留工具真实返回的文章级 URL；未返回则标注来源类型，不链接登录页或控制台 |

## 输出与合规

- 输出标题/名称、稳定代码或 ID、数据日期/发布时间、来源类型、关键数值与单位。
- 区分事实、观点、推断和数据缺口；不暴露物理表名、SQL、内部索引、原始日志或鉴权信息。
- 中国市场视觉遵循红涨绿跌；文字含义和数值符号优先于颜色。
- 输出只基于公开信息和实际返回的数据。AI 生成内容可能存在误差，不构成投资建议，也不构成个股推荐。
