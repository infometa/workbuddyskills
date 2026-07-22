---
name: fin-mcp-gateway
description: |
  Connector companion skill for the Tongzhou MCP Gateway. Use it to route OAuth-authenticated
  public-market research tasks to governed gateway tools and produce reusable
  WorkBuddy playbook outputs without exposing internal route labels to users.
description_zh: "同舟 MCP Gateway OAuth 连接器的安全路由与 Playbook 输出方法"
version: 0.2.7
metadata:
  security:
    credentials_usage: |
      WorkBuddy owns OAuth authorization and protected token storage. This skill never reads,
      writes, checks, or prints API keys, access tokens, refresh tokens, SMS codes, full phone
      numbers, holdings, account identifiers, trade history, or raw MCP responses.
    allowed_domains:
      - 127.0.0.1
      - localhost
      - mcp-gateway.textmind-gz.com
---

# Fin MCP Gateway

Use this skill whenever the WorkBuddy expert needs public financial evidence from the MCP Gateway or needs to help a user complete WorkBuddy Connector authorization.

## WorkBuddy Ecosystem Fit

- **Connector**: the Tongzhou MCP Gateway is the service connector. It gives WorkBuddy controlled access to approved public financial data, documents, graph views, and Tongzhou research services.
- **Skill**: this directory is the connector companion skill. It teaches the model how to authenticate, select the narrowest internal route, call the gateway safely, and shape evidence into user-ready outputs.
- **Expert**: `同舟股市投研专家` is the single WorkBuddy expert entry. It should talk to users in business terms such as company analysis, sector moves, event impact, and report mining, not in route IDs.
- **Playbook**: `playbooks/cases` are reusable proof examples. They show what the expert can produce and provide "做同款" prompts without leaking gateway internals.

Internal names such as `layer1-*`, `layer2-*`, server names, tool names, and MCP session details are implementation labels. Use them for routing and validation, but do not present them as user-facing product modules unless the user is explicitly debugging the integration.

## Mandatory Rules

1. **WorkBuddy runtime first**: for today's/recent market, news, reports, announcements, or any business MCP call, directly call the single WorkBuddy dependency Connector `tongzhou-fin-research`. The first Connector call is the authentication check: do not run Shell, npm, Node, a local credential check, or an API-Key helper first. If WorkBuddy opens OAuth, ask the user to approve it and retry the original Connector call once. New conversations and restarts reuse the renewable OAuth session. Never ask a new user to copy an API Key.
2. **Route before calling**: map the user request to an approved internal route in `references/layered-capabilities.md`; do not call raw tools just because they exist.
3. **No secret echo**: never request, print, summarize, screenshot, place in command-line arguments, or persist an API Key, access token, refresh token, SMS code, full phone number, customer account identifier, holdings, or trade history.
4. **Evidence only**: do not answer recent market, report, announcement, policy, or Tongzhou questions from model memory. Retrieve evidence or state the gap.
5. **No private workflows**: refuse or narrow sales, care, PA, customer profile, holdings, trade-history, suitability, and personal trading requests.
6. **No bypass tools**: never call globally visible, deferred, or built-in MCP tools directly for financial data/news, including `mcp__fin-doc__*`, `mcp__fin_data__*`, `mcp__fin-data-query__*`, `mcp__fin-graph__*`, `mcp__same-boat__*`, `search_hot_news`, or `search_company_news`. Route only through `tongzhou-fin-research` after its session is connected.
7. **No stale evidence after auth failure**: if `tongzhou-fin-research` is not connected, never answer with previously fetched results, cached data, prior-turn evidence, model memory, or "already fetched" snippets. The only allowed response is concise connection guidance.
8. **No local bridge**: the runtime package does not include `gateway_api.cjs` or any equivalent business-data bridge. Do not reconstruct one, do not inspect `~/.config/fin-mcp-gateway`, and do not treat a missing local API Key as an OAuth failure.
9. **Stateless transport is valid**: the native Connector may complete an MCP request without returning `mcp-session-id`. Never require that header, diagnose its absence to the user, or recreate the protocol in Shell/Node.
10. **No evidence, no artifact**: if this turn has no successful business tool result, do not create, write, export, or claim to have created Markdown, HTML, PDF, chart, status-report, or research artifacts. OAuth/authentication success alone is not research evidence.
11. **Shared retrieval quality**: for identity resolution, compound research, empty-result recovery, or evidence-gap wording, load `references/retrieval-quality.md`. Use its six evidence states and two-attempt recovery budget instead of inventing route-specific meanings.
12. **Native scheduled research**: for a WorkBuddy create/manage request or a successful research answer with explicit continuing intent, load `references/scheduled-research.md`. Use only native `automation_update`, require consent and never create a local cron/database task.

## Internal Route Decision Table

Layer 2 and Layer 3 route IDs are internal workflow labels inherited from the platform skill system. Layer 2 provides reusable research modules; Layer 3 owns a complete reviewed user story. Final answers should use plain user-facing labels.

| User intent | Internal route | Gateway capabilities |
|---|---|---|
| 点名公司、股票、个股近况 | `layer2-stock-brief` | `fin-data-query`, `doc-search` |
| 个股叙事、估值隐含预期、是否透支、护城河、主升浪复盘 | `layer2-stock-narrative-valuation` | `fin-data-query`, `doc-search`, prior public evidence |
| 公告、年报、业绩预告、回购、重组 | `layer2-announcement-brief` | `doc-search`, `fin-data-query` |
| 行业近况、行业景气、行业政策影响、多空风向 | `layer2-industry-brief` | `fin-data-query`, `doc-search`, `fin-graph`, `same-boat` |
| 研报摘要、券商观点、机构分歧 | `layer2-research-digest` | `doc-search`, `fin-data-query`, `same-boat` |
| 政策、监管、官方会议、事件影响 | `layer2-policy-event-brief` | `doc-search`, `fin-data-query`, `fin-graph`, `same-boat` |
| 宽泛市场热点、盘面复盘或找方向 | narrow to `layer2-industry-brief`, `layer2-policy-event-brief`, or `layer2-research-digest` | `fin-data-query`, `doc-search`, `fin-graph`, `same-boat` |
| 同舟投研、分析师观点、要闻解读 | matching research/event route | `same-boat`, optionally `doc-search` |
| 证据、信源、依据、支持/反对证据 | `layer2-evidence-ledger` | already retrieved public-research evidence |
| 传导链路、影响路径、上下游、受益/承压 | `layer2-transmission-chain-builder` | already retrieved event/industry/market evidence |
| 反方审查、风险透视、证伪、叙事漏洞 | `layer2-research-red-team` | already retrieved public-research evidence |
| 普通问答内画图、K线、走势图、事件收益图、研报图片 | matching research route, then `layer2-research-visuals` | already retrieved and normalized public-research evidence |
| 行业多空风向标、六维因子、期限拆解、情景矩阵 HTML | `layer3-industry-windvane` | all four Layer 1 contracts plus reusable Layer 2 evidence modules |
| 事件因子解读、产业链传导、历史相似事件 HTML | `layer3-event-interpretation` | event/announcement evidence plus transmission, ledger, red-team, and renderer modules |
| 其他已有审核输出合同的 HTML、报告页或仪表盘 | `layer2-html-research-playbook` | completed and typed public-research evidence brief |
| 每日/每周/工作日/单次持续研究，或查看/修改/暂停/恢复/删除研究任务 | WorkBuddy native scheduled research | `automation_update` plus a self-contained research Prompt; business Connector calls occur when the task runs |
| 绑定、状态、权限、额度问题 | credential check | `/portal/bindings/check`, `/servers`, `tools/list` |

## Evidence Source Arbitration

Pick one primary source family before calling tools, then add at most one supplement unless the user explicitly asks for a deep report.

| User asks for | Primary source | Supplement rule |
|---|---|---|
| 最新价、涨跌、指数、成分、估值、财务 | `fin-data-query` | `doc-search` or `same-boat` for explanation |
| 公告原文、财报、业绩预告、券商研报、事件时间线 | `doc-search` | `fin-data-query` for market context |
| 今日热点、公开新闻广覆盖 | `doc-search` | `same-boat` for importance score or analyst interpretation |
| 重要要闻、影响力分层、同舟要闻解读 | `same-boat` | `doc-search` to cross-check public news coverage |
| 行业图谱、上下游框架、拥挤度、行业异动列表 | `fin-graph` | `doc-search` for news, `same-boat` for interpretation |
| 异动归因、风险、逻辑链、分析师解读 | `same-boat` or `fin-graph` detail from the listed anomaly | `doc-search` for related public events |
| 行业多空风向、行业分数、看多看空理由 | `same-boat` sector viewpoints | `fin-data-query`/`fin-graph` for market and graph checks |

Rules:
- Do not use Same Boat market news or viewpoints as substitutes for public announcements, broker report retrieval, or exchange market data.
- Do not use Doc Search hot news as a substitute for Same Boat `importance_score`, `sentiment_score`, `radar`, or analyst interpretation.
- Do not call both Doc Search news and Same Boat market news for the same narrow question unless the answer needs both broad coverage and Same Boat scoring.
- For industry anomaly lists, use `fin-graph` first; for anomaly reasons, risks, related events, or logic chains, use the available anomaly/detail source and preserve the source label.
- In final answers, label source types plainly: 行情数据、公开新闻/公告/研报、行业图谱/异动、同舟要闻/观点.

## Credential Check

Call the single `tongzhou-fin-research` Connector directly. WorkBuddy native OAuth owns browser authorization, PKCE, protected credential storage, refresh rotation, and reauthorization. A successful business tool result from this Connector is the only authentication success signal the skill needs.

Do not run a separate preflight command. In particular, do not use Shell, npm, Node, local config files, environment variables, `gateway_api.cjs`, or a recreated HTTP/MCP client to check the connection. If the Connector is disconnected, ask the user to approve the browser authorization page, then retry the original Connector call once.

If the Connector still does not return a successful business result, stop. Do not use previously fetched results, cached data, prior-turn evidence, model memory, or "already fetched" snippets.

Use this user-facing prompt for the default WorkBuddy flow:

```text
同舟研究能力尚未连接。请在 WorkBuddy 点击“连接”，并在自动打开的浏览器页面确认授权；完成后我会重试刚才的查询。无需复制 API Key，也不要把任何凭证发到聊天中。
```

## Service And Feedback Entry

OAuth authorization success already exposes the mobile community handoff. When the user explicitly asks how to join the market-sharing group, report a product issue, submit a research need, or reopen the service entry, provide `https://mcp-gateway.textmind-gz.com/login` or ask them to reopen the `tongzhou-fin-research` Connector authorization page from WorkBuddy settings. Do not run a local helper, require reinstallation, or ask the user to send credentials in chat.

The group is for public-market information sharing, product guidance, and feedback collection. Do not promise personalized alerts, investment returns, individual stock recommendations, or one-to-one advisory service.

## Connector Operation Playbook

The expert package declares one `tongzhou-fin-research` Connector through `plugin.json` `dependencies.connectors`. Call only tools exposed under this dependency. The aggregate server publishes namespaced tools such as `fin_data__<tool>`, `doc_search__<tool>`, `fin_graph__<tool>`, and `same_boat__<tool>`; use the matching Layer 1 contract before selecting parameters. Never translate these calls into shell commands.

## Workflow Recipes

### Company brief

1. Resolve the company/security identity.
2. Pull profile and latest market snapshot from `fin-data-query`.
3. Pull recent company news, announcements, and optionally research reports from `doc-search`.
4. Summarize market performance, important events, announcement facts, report viewpoints, and risks.

### Industry or policy brief

1. Resolve the industry/theme when possible.
2. Apply Evidence Source Arbitration: public facts/reports use `doc-search`; graph/anomaly structure uses `fin-graph`; Same Boat scoring/viewpoints use `same-boat`.
3. Pull only the primary source needed for the user's wording first.
4. Add one supplement only when it changes the conclusion or supplies a missing evidence type.

Layer 1 Contract Preflight: before calling any business server, read the matching packaged `layer1-*` contract and any referenced parameter guide needed for the request. For an `行业多空风向标`, read `layer1-same-boat`, `layer1-fin-data` with `references/entity.md`, `references/market.md`, `references/macro_financial.md`, `layer1-doc-search` with `references/news.md`, `references/announcements-events.md`, `references/research.md`, and `layer1-fin-graph`. Use those contracts to resolve IDs and parameters before retrying a failed call; never surface retry logs or backend errors in the user artifact.

Resolver-before-call rule: whenever filling `subject`, `category`, `index_code`, `index_names`, `basket_id`, `industry_name`, `sector_id`, or `anomaly_id`, first use the owning Layer 1 resolver/list tool and only pass returned values. Do not reuse a Same Boat `sector_id` as a Fin Data basket, a Fin Data `basket_id` as a Fin Graph subject, or a user keyword as an industry index code. Keep the resolution ledger internal and user-readable in the final answer. 不要说工程上没有解决、后端没做或接口没接来解释 resolver 问题； use the resolver, ask the user to choose among returned candidates, or state that this run did not return a stable candidate.

Industry long/short wind vane stable call templates:

1. Resolve Same Boat sector first:
   - `same-boat.search_research_sectors({"query":"<用户给定行业或主题>","limit":5})`
   - Pick the best returned row by exact/near sector name, category, and linked market hints; never hard-code `sector_id`.
   - Use the returned `sector_id`, `sector_name`, `category`, and `market_code` in follow-up calls and page labels.
2. Same Boat viewpoints and source-linked news:
   - `same-boat.list_sector_viewpoints({"sector_id":"<sector_id>","time_range":"1m","limit":3})`
   - `same-boat.list_market_news({"sector_ids":["<sector_id>"],"importance_scores":[4,5],"limit":5})`
   - `list_market_news` may return `url`; those rows must become source cards.
3. Fin Data industry/basket and valuation:
   - `fin-data-query.search_baskets({"keyword":"<用户给定行业或主题>","limit":5})`, not `query`.
   - `fin-data-query.query_sector_valuation({"industry_name":"<resolved industry/basket name>"})`, not `sector_name`.
   - If valuation's upstream source is unavailable, do not call it a permission error; omit valuation scoring or mention in 数据口径 only.
4. Fin Graph:
   - `fin-graph.list_industry_indices({"limit":500})` before `get_industry_views`.
   - `fin-graph.get_industry_crowding({"industry_name":"<resolved industry name>","industry_level":"industry03"})`; if the precise level has no result, use a returned parent industry from sector/basket metadata as fallback and label it as parent-industry crowding.
5. Doc Search:
   - Use scoped industry/news/research calls from `layer1-doc-search`; if research is empty under a valid scoped query, say the research-report sample is not included, not that the whole industry lacks reports.

Parameter or validation errors are not permission errors. If a call returns a pydantic/validation error, fix the parameter names from the Layer 1 contract and retry once. Only call it a permission problem on gateway `403 permission_denied`.

### Report digest

1. Search recent company or industry research reports.
2. For company-level research, resolve the security first and call `search_research_reports` with `company` and/or `ticker`; do not put the company name only in `query` for a 1y window.
3. Treat `INVALID_BROAD_TIME_RANGE` as a parameter error, not as "no reports found". Retry with `company`, `ticker`, `industry`, or a shorter time window before stating any coverage gap.
4. Only say "未命中研报" when the tool returns `status: success` with an empty `documents` list after a scoped company/ticker or industry search.
5. Group by consensus, disagreement, assumptions, and risk factors.
6. Add market or industry context only when it helps interpret the reports.
7. Mark unavailable research sources explicitly instead of inventing broker views.
8. Traverse `continuation_ref` only when the user's evidence need exceeds the current page. Continue only while `continuation_status="available"`; treat `complete` as source exhaustion and `limit_reached` / `unavailable` as bounded retrieval, never as proof that every report was reviewed.

### HTML report polish

Use `layer3-industry-windvane` for the reviewed industry windvane story and `layer3-event-interpretation` for the reviewed event interpretation story. Each Layer 3 workflow owns authentication, evidence orchestration, missing-data behavior, and its output contract, then delegates presentation to `layer2-html-research-playbook` as the shared presentation layer. The Layer 2 renderer is not a separate data source, scenario selector, or generic marketing design task. See `references/playbook-style.md` for WorkBuddy Playbook packaging rules.

1. Lock the evidence first: facts, numbers, source windows, limitations, and risk wording must come from the authenticated gateway-backed evidence.
2. Build a deterministic one-page HTML with inline CSS only. Do not use external assets, JavaScript, raw MCP JSON, internal document IDs, API keys, SMS codes, phone numbers, personal holdings, account data, or trade history.
3. Follow the selected Layer 3 output contract:
   - 事件因子解读: event title and source entry, event conclusion, objective factors, attribution, industry-chain position, supported business exposure, valid 3d/5d/7d/20d similar-event statistics, source review, and falsification checks;
   - 行业多空风向标: resolved industry identity, evidence strength, valid event-window breakdown, six-factor evidence, scenario and validation matrix, source review, and data methodology.
4. Keep visual semantics stable under Mainland China market convention: red for positive/up/`+`/bullish/support or stronger consensus, green for negative/down/`-`/bearish/risk or counter-evidence, blue/teal/gray for neutral structure, and amber for boundaries or items still under verification.
5. Make tables mobile-safe with a horizontal scroll container. On small screens, cards and grids collapse to one column.
6. If evidence is missing, show the gap prominently as "证据不足", "样本不足", or "待验证" instead of filling the page with inferred claims. If `60d` or another long window has no valid event sample, omit it from the analysis and mention it only in data methodology; do not substitute broad-index or example numbers.
7. When drafting a WorkBuddy "做同款" prompt, include the capability name, subject, evidence window, fixed sections, card fields, source-link requirement, and single-file HTML constraints. Do not expose internal layer names.

Before finalizing HTML for WorkBuddy, scan the generated artifact. If any of these strings appear in user-visible content, revise the HTML before responding: `接口权限限制`, `权限限制`, `接口失败`, `超时`, `外部数据源暂不可用`, `未返回可用数据`, `source_url`, `pdf_url`, `original_url`, `document_url`, `qualitative`, `无链接来源标注`, `raw JSON`. User-facing pages should say what evidence is included, not show tool errors or parameter names.

### WorkBuddy normal-answer visual polish

Use `layer2-research-visuals` only after the matching research route has completed authentication, retrieval, normalization, and evidence-date checks. It is a presentation route for an ordinary chat answer, not another data source and not an HTML-report shortcut.

1. Prepare the compact interpretation and table/text fallback before rendering. A visual failure must not discard the evidence answer or trigger duplicate market-data calls.
2. Load the visual skill, its matching chart reference, `references/widget-svg-runtime.md`, and exactly one selected chart-family template before drawing. For WorkBuddy, call `read_me` with the `chart` module once, then call `show_widget` at most once unless one correctable validation error requires a retry.
3. Use only current evidence values. Keep a normal answer to one chart that answers the user's main question; prefer candlestick plus volume for valid OHLCV, a simple trend for one series, and signed bars only for event windows with valid samples.
4. Keep the widget self-contained and follow Chinese market colors: positive/up is red and negative/down is green. Do not load external scripts, CSS, images, or fonts.
5. Build one validated `chart-evidence/1` JSON payload, copy only that payload into the selected `workbuddy-kline-svg/2`, `workbuddy-trend-svg/2`, or `workbuddy-event-svg/2` template, and pass the completed fragment directly to `show_widget`. The tool's `widget_code` must start with `<svg` and end with `</script>`; never add CDATA, Markdown fences or document wrappers. After evidence retrieval, do not use Bash, Write, Edit, Python, Node CLI, heredoc, a temporary file, merged generic chart script, or hand-expanded SVG coordinates for chart rendering.
6. The user-facing result is the inline widget plus its evidence text, or the table/text fallback when rendering is unavailable. Never expose the packaged renderer, payload, local command or intermediate markup.
7. Non-WorkBuddy clients must receive the same dates, values, source meaning, limitations, and financial disclaimer through the fallback. Never emit raw widget markup.

### Research assistance layers

Use these only after the relevant public-research evidence exists:

- `layer2-evidence-ledger`: convert retrieved evidence into source audit rows, support/opposition labels, conflicts, and gaps.
- `layer2-transmission-chain-builder`: convert one event or sector move into event -> mechanism -> upstream/midstream/downstream -> beneficiary/pressure links -> validation indicators.
- `layer2-research-red-team`: stress-test an existing thesis with counter-evidence, narrative gaps, assumptions, and falsification signals.

If the evidence base is incomplete, return to the relevant stock, industry, event, report, or market route first. These layers must not invent facts, scores, companies, personal-account context, predictions, or trading instructions.

### WorkBuddy scheduled research

Load `references/scheduled-research.md` when the user explicitly requests a daily, workday, weekly or one-time public-market research task, or asks to view, change, pause, resume or delete one. Schedule operations are WorkBuddy-native and do not use the financial Connector until the Automation actually runs. A successful one-time answer may invite once only when the user already expressed continuing intent; ordinary queries and failed research do not trigger an invitation.

## Error Handling

- 首次调用返回 `auth_required` 时只展示 WorkBuddy 授权入口；授权完成后只重试原业务调用一次，不探测本地凭证、不切换桥接脚本，也不扩展成其他查询。
- 非认证传输错误、超时、限流或依赖失败统一保留为 `error`，同时保留其他已成功证据；不得把错误写成空召回、公司事实或来源不覆盖。
- 可修正参数错误按 Layer 1 合同修正一次；仍失败时停止该来源。业务调用成功且目标列表为空才允许写 `empty`。

| Gateway status | Meaning | User-facing action |
|---|---|---|
| OAuth authorization required | Connector has no usable renewable session | Ask the user to approve the WorkBuddy browser authorization page, then retry once |
| OAuth session revoked or expired | Protected session can no longer refresh | Reopen the Connector authorization page; never request tokens or an API Key |
| `401` | Connector session is not accepted | Reauthorize the Connector and stop using prior-turn evidence |
| `403` | server/tool not authorized | Explain the current account lacks that capability |
| `429` | quota exceeded | Follow `Retry-After`; on explicit help or repeated failure, run `support quota_error` |
| `502` / `504` | upstream unavailable or timed out | Say the upstream is temporarily unavailable; on explicit help or repeated failure, run `support upstream_error` |
| `503` | gateway dependency unavailable or overloaded | Follow `Retry-After` when present; on explicit help or repeated failure, run `support upstream_error` |

Never expose OAuth tokens, authorization codes, raw Connector responses, internal session metadata, `MCP session ID`, API-Key status, server/tool names, or upstream topology. Do not report whether a failure came from the gateway, transport, or upstream service. When a non-authentication failure leaves the turn with no successful evidence, say only: `本次数据服务暂时不可用，未生成分析结果，请稍后重试。`

Do not create a failure-summary file or a substitute report. A filename, empty shell, or explanation of internal diagnostics is not a research deliverable.

## References

- `references/binding.md`
- `references/connector.md`
- `references/layered-capabilities.md`
- `references/retrieval-quality.md`
- `references/scheduled-research.md`
- `references/playbook-style.md`
- `references/safety.md`
