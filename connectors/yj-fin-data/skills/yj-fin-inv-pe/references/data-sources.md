# 数据来源、缺失处理与出处标注（yj-fin-data MCP 版）

本技能的全部外部数据都来自 **yj-fin-data MCP 工具集**（云极数据服务）。跑分析前，先加载 `yj-fin-data` 技能查看各工具参数；本文件规定"什么维度调用哪个工具、以及必须真的去取数"。

## 一、铁律：先取数，再下笔（取代"视可得性 / 不探活"）

- **必须实取**：凡涉及行业规模、可比公司财务/行情/估值、研报观点、纪要、公告、宏观指标等维度，**必须调用 yj-fin-data MCP 工具实取**，不得凭记忆撰写。记忆里的"大概数字"一律以工具取数为准。
- **授权失败要停下来**：若工具返回 `UNAUTHORIZED` / `SCOPE_MISSING`，立刻停止后续取数，明确告诉用户"需在连接器里完成云极账号授权后再跑"——**不要**用记忆内容填空。
- **空结果/无数据要如实写**：返回 `ENTITY_NOT_FOUND` 或空列表时，写"该维度暂无数据"，不要编造或倒推。
- **只有 truly 不可达维度**（工商/司法/一级融资，yj-fin-data 不提供）才用"受数据可得性限制，XX 待补充核验"带过，且绝不假设、绝不编造比例/轮次/投资方。

## 二、维度 → 工具映射（全部为 yj-fin-data MCP 工具，调用名即下方所列）

| # | 维度 | 工具（yj-fin-data MCP） | 关键入参要点 |
|---|---|---|---|
| D1 | 券商研报 / 纪要 / 观点 / 公告 / 公众号（行业·公司·可比线索） | `securities_search`（先解析代码）→ `knowledge_search`（研报/纪要/观点片段）→ `fetch_document`（取原文：broker_report / announcement / announcement_hk / announcement_us）→ `meeting_summary_list`+`fetch_meeting_summary`（纪要）→ `domestic_chief_opinion_list`（首席观点） | keyword 用全称；`start_date`/`end_date` 用真实当前日期；多轮替换关键词 |
| D2 | 上市可比公司财务 / 行情 / 乘数 | `financial_income`/`financial_balance`/`financial_cashflow`（三表，market: a/hk/us）→ `quote_daily`(A)/`quote_daily_hk`(港)/`quote_daily_us`(美) → `valuation_analysis`（pe_ttm/ps_ttm/pb_mrq…）→ `earnings_consensus`（一致预期）→ `management_discussion`（管理层讨论-年报/半年报/业绩会）→ `qa_list`（投资者问答） | 先 `securities_search` 拿带后缀代码；`period`/`fiscal_year` 闭集；`field_list` 显式传 |
| D3 | 工商登记 / 股权穿透 / 实控人 / 股东名册 | 本技能无专职工商库 | **不可达**（除非用户上传）→ 写"股权结构受数据可得性限制待补充核验"；不假设、不编造比例 |
| D4 | 司法 / 股权冻结 / 被执行人 / 失信 | 无 | **不可达** → 风险处一句"司法维度待核验补充"；绝不假设无诉讼无冻结 |
| D5 | 知识产权（专利/软著/资质） | 无独立库；研报/公告可旁证 | 能引研报/公告则标来源；否则"IP 清单待补充" |
| D6 | 一级市场融资事件 / 轮次 / 金额 / 估值 / 投资方 | 无专门一级库；研报/纪要/观点/公告可交叉 | 落到可比财务乘数与区间；事件本身无可靠来源则"待补充"，不按金额倒推、不臆造轮次/投资方 |
| D7 | 非上市公司财务 | 用户上传报表 + 研报/纪要旁证 | 给报表→走 CAS 标准化；只给口头规模→标"[项目方/线索口径，未经审计]" |
| D8 | 宏观 / 行业指标（TAM/增速/渗透率） | `macro_indicator_search`（先拿 indicator_id）→ `macro_indicator_series`（取数）；或 `indicator_*` | 单次批量上限 10 个指标；中国宏观指标名不含"中国" |
| D9 | 通用公网检索（WebSearch/WebFetch） | 本环境一般未注入且网关受限 | **通常不可达** → 需公网资料时先试；不可达→明示该检索维度为空 |

**铁律（续）**：D3–D9 任一不可达 → 不阻塞出报告，但必须在对应模块与结尾以自然措辞写明局限。用户明确补传材料后再补实。

## 三、标准取数流程（每个模块开跑前照做）

1. **解析代码**：对每个标的与可比公司先 `securities_search({keyword, top})` 拿带交易所后缀的代码（如 曦智科技→`01879.HK`），一次任务内每标的只解析一次。
2. **行业/公司第一层**：用 `knowledge_search({query, start_date, end_date, resource_types:[research_report,conference_minutes,chief_analyst_view]})` 检索研报/纪要/观点，挑候选；要原文用 `fetch_document`；要纪要用 `meeting_summary_list`+`fetch_meeting_summary`；观点用 `domestic_chief_opinion_list`。
3. **可比公司（已上市）**：`financial_*` 取三表、`quote_*` 取行情、`valuation_analysis` 取估值分位、`earnings_consensus` 取一致预期、`management_discussion`/`qa_list` 取经营信息。
4. **宏观/行业规模**：先 `macro_indicator_search` 拿 indicator_id，再 `macro_indicator_series` 取数。关键 TAM/增速至少 2 个独立来源交叉。
5. **就近标注来源**：每条关键数据用 yj-fin-data 信封里的 `sources` 字段，或就近标签 `[研报]`/`[纪要]`/`[观点]`/`[公告]`/`[行情/财务]`/`[项目方-BP]`/`[用户提供]`。

## 四、出处标注（全局强制）

- 每条关键数据附来源标签（就近）：`[研报]` / `[纪要]` / `[观点]` / `[公告]` / `[行情/财务]` / `[项目方-BP]` / `[用户提供]`。
- 独立源偏好：公司披露(公告/官方) > 券商研报 > 纪要/观点 > 项目方 BP > 二手传闻。
- TAM/增速/市场规模核心口径**至少 2 个独立来源交叉**；冲突以更权威为准。
- **禁止**：整段行业只写 BP 内容、无凭据数字、把项目方叙事当客观事实。

## 五、缺失处理（默认约束）

- 工商/司法/一级融资（D3/D4/D6）yj-fin-data 不提供 → "受数据可得性限制，XX 待补充核验"，不假设、不编造。
- 交付物是分析成品：局限用自然措辞带过，不写"故障/未连通/兜底"。
