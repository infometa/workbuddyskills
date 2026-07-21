---
name: layer2-industry-brief
description: "当用户询问某个具体行业的近况、景气、估值或政策影响时——如'白酒最近怎么看''动力煤行业发生了什么''半导体景气如何'。聚焦单一具体行业；跨多行业找方向时先收窄到具体行业、事件或研报证据；个股问题用 stock-brief。"
---

Use when:
- 需要快速理解一个行业最近的变化
- 需要把行业图谱、异动、新闻、研报放在一起看
- 需要给上层 agent 提供行业框架入口
- 需要回答“行业景气度、估值、代表公司、政策变化、当前关注点”这类行业快览问题
- 用户用灵感页口吻问“今天这个板块为什么涨”“这个行业为什么火”“这个概念到底在炒什么”
- 典型场景：
  - 行业简析
  - 行业政策颁布 / 变化
  - 新词条 / 概念 / 现象
  - 近期消息面意义及影响（行业视角）

Not for:
- 不要把它当成完整行业深度报告生成器
- 不要在缺少篮子 / 排名能力时硬做“最优行业推荐”
- 不要在没有最新证据的情况下输出“行业景气明显上行 / 下行”“机构一致看多”等强结论

Depends on:
- `layer1-fin-graph`
- `layer1-doc-search`
- `layer1-fin-data`
- `layer1-same-boat`

Workflow:
0. 调用任何业务工具前，必须先读取对应 Layer 1 契约；不要只凭工具名试参数。行业多空风向标至少读取：
   - `layer1-same-boat/SKILL.md`：行业目录、同舟观点、要闻、`sentiment_score`、`radar`
   - `layer1-fin-data/SKILL.md` 及 `references/entity.md`、`references/market.md`、`references/macro_financial.md`：篮子/指数、行情序列、估值
   - `layer1-doc-search/SKILL.md` 及 `references/news.md`、`references/announcements-events.md`、`references/research.md`：新闻、公告、研报
   - `layer1-fin-graph/SKILL.md`：行业指数代码、图谱、拥挤度、异动
   - 参数错误不是权限错误：只有 gateway 返回 `403 permission_denied` 才能写“当前 key 缺少权限”。Pydantic validation error、unexpected keyword、missing argument、timeout、upstream unavailable 都要按 Layer 1 契约改参数或降级，不要写成权限限制。
   - 统一身份优先：凡 workflow 需要两个以上研究来源，先调用 `resolve_research_identity`，保存 `canonical_id`、`source_ids`、`coverage_gaps` 和候选/警告。后续只复用 resolver 返回的 `same_boat_sector_id`、`fin_data_theme_basket_id`、`fin_data_sw_basket_id`、`market_index_code`、`graph_subject`、`rfg_frame_id` 等目标字段；不要用宽基指数、示例行业或假 ID 替代缺失来源。
   - 行业解析协议必须四路分开，维护内部 resolution ledger，不要把一个工具返回的 ID/名称借给另一个工具当参数：
     - Same Boat `sector_id`：优先使用 `source_ids.same_boat_sector_id`；缺失时再 `search_research_sectors({"query":"<用户给定行业或主题>","limit":5})`，从返回结果中按名称、类别、market_code 选择最匹配行。
     - Fin Data basket：优先使用 `source_ids.fin_data_theme_basket_id` / `source_ids.fin_data_sw_basket_id`；缺失时再 `search_baskets({"keyword":"<用户给定行业或主题>","limit":5})`。当前 gateway wrapper 使用 `keyword`，如果 `tools/list` 明确显示不同 schema，以工具 schema 为准。选定后只把返回的 `basket_id` / `resolved_basket_name` 用于 Fin Data 成分、排行和篮子口径。
     - Fin Graph subject：优先使用 `source_ids.graph_subject`、`source_ids.market_index_code` 或 `source_ids.rfg_frame_id`；缺失时再 `list_supported_subjects(index_type="industry_III_index", limit=500)` 或 `list_industry_indices(limit=500)`，只把返回的 `resolved_subject` / `index_code` 用于图谱、观点、异动和拥挤度。
     - Shenwan valuation：只用 resolver 或 Fin Data/估值工具返回确认的申万行业名调用 `query_sector_valuation({"industry_name":"<returned industry_name>"})`；概念、主题、ETF 篮子不能包装成申万估值。
   - 行业多空风向标稳定模板：先完成上述四路解析；再调用 `list_sector_viewpoints({"sector_id":"<returned sector_id>","time_range":"1m","limit":3})`、`list_market_news({"sector_ids":["<returned sector_id>"],"importance_scores":[4,5],"limit":5})`、`list_constituents({"basket_id":"<returned basket_id>"})`、`query_sector_valuation({"industry_name":"<returned industry_name>"})`、`get_industry_crowding({"industry_name":"<returned or parent industry_name>","industry_level":"industry03"})`。精确层级无结果时才用返回的父行业做 fallback，并在页面标注为父行业口径。
   - 不要说工程上没有解决、后端没做或接口不支持来掩盖解析失败。若某一路 resolver 没返回稳定候选，就把该能力降级为“本轮未形成稳定口径”，或请用户从候选中选择。
1. 先调用 `search_baskets` 确认行业或主题是否已有稳定篮子定义；如能匹配成功，再调用 `list_constituents` 获取代表性成分，优先取前 `8-15` 个观察标的。
2. 如果用户问“最近怎么看 / 最近发生了什么 / 景气度如何”，优先调用 `search_documents(doc_type="news", industry=...)` 获取近 `7-30` 天行业新闻。
3. 如果用户问政策变化、消息影响、行业催化，优先再调用 `search_documents(doc_type="event", industry=...)` 或其他可用事件检索工具获取近期行业事件。
4. 如果用户问研究观点、行业逻辑、景气验证，调用 `search_research_reports(industry=..., content_type="行业研究")`；如果研报链路不可用，要明确降级，不要编造券商观点。
5. 如果用户问估值，调用 `query_sector_valuation` 查询对应申万行业估值；没有估值数据时不要自己估。
6. 如果用户问“行业多空风向标”“行业分数”“看多看空理由”“同舟怎么看这个行业”“分析师观点偏多还是偏空”，必须使用 Same Boat 行业观点链路：
   - 先调用 `search_research_sectors(query=...)` 获取稳定 `sector_id`，不要直接把行业名传给 `list_sector_viewpoints`。
   - 再调用 `list_sector_viewpoints(sector_id=..., time_range="1w" 或 "1m", limit=...)` 获取不同分析师/同舟观点。
   - 输出必须引用返回的 `sentiment`、`sentiment_score`、`radar`、`summary` / `content`、`analyst_count` 与 `publish_time`；如果这些字段缺失，要说明该项未返回，不要自己补分。
   - `sentiment_score` 只能作为 Same Boat 返回的观点分数或情绪分，不能写成模型独立预测分、投资评级或目标价。
7. 如果用户问“金融资讯影响力评级”“重要新闻”“最值得关注的行业要闻”，可复用 Same Boat 解析出的 `sector_id` 调用 `list_market_news(importance_scores=[4, 5], sector_ids=[...], limit=...)`，并按 `importance_score`、`popularity_score`、`publish_time` 分层；不要承诺完整全市场评级模型。
8. 图谱能力是可选增强，而不是默认起点。只有在需要行业框架、公开节点摘要、异动视角时，才调用 `get_graph_overview`、`query_graph_nodes`、`get_graph_node_brief`、`list_industry_anomalies` 或 `get_industry_views`；调用 `get_industry_views` 前必须先用 `list_industry_indices` / `list_supported_subjects` 解析 `index_code`，再传 `index_codes=[...]`，不要把行业名直接塞进 `index_codes`。
9. 对 MLCC、AI 算力、半导体、新能源车、机器人这类产业链主题，必须补一层“传导链路”：
   - 触发事件 / 新闻 / 政策 / 研报观点
   - 影响机制：需求、供给、价格、库存、产能、成本、替代、政策约束中的哪一项
   - 上游 / 中游 / 下游分别可能受到什么影响
   - 哪些代表公司或板块只是相关，哪些有更直接证据
   - 后续验证变量：价格、订单、库存、产能利用率、客户需求、公告或研报覆盖变化
10. 默认不要只看 `1-2` 天新闻就下结论。除非用户明确只要“今日快讯”，行业归因至少需要近 `7-30` 天证据；若传导链路依赖更早背景，可补 `3-6` 个月内的关键政策、价格、库存或研报线索，但要标注时间窗口。
11. 如果用户要求 HTML、灵感样张或“做同款”，把结果整理成 WorkBuddy 证据包：
   - 行业/板块定义：本次匹配到的篮子、主题或行业口径；没匹配到就说明口径偏事件解释
   - 身份证据：展示用户可理解的 `canonical_id`、已使用的 `source_ids` 摘要和 `coverage_gaps`，不要展示工具日志或 raw JSON。
   - 证据窗口：新闻、事件、研报、同舟观点、图谱/行情的时间范围
   - 一句话解释：普通用户能听懂的“为什么涨/为什么受关注”
   - 短/中/长期三张卡：每张必须有方向、核心理由、失败条件和颜色标签；短期看新闻/资金，中期看动销/价格/订单/库存，长期看估值/竞争格局/现金流或政策约束。
   - 综合分或证据强度：优先引用 Same Boat `sentiment_score` / `radar`；如要用 50 分基准加减分，必须把每个加减分绑定到已返回证据，不能把它写成收益预测。
   - 触发事件：3-5 条关键新闻/事件/研报/同舟观点，保留来源、发布时间和可点击链接字段；没有 URL 的数据不要做源头卡。
   - 核心信号：拆成“支撑短期 / 需要验证 / 支撑长期 / 反向约束”，每条只讲一个用户能听懂的变量。
   - 六维因子：景气与盈利、资金确认、政策催化、估值位置、供需位置、舆情与风险；每维必须写客观数据或明确来源类型。能从图谱拿到 `get_factor_metric_values` 时优先展示指标值或短历史变化，再用规则评分兜底。
   - 源头复核入口：只保留返回的 `source_url`、`document_url`、`report_url`、`original_url` 或小程序页面链接；没有链接的数据进入数据口径，不要写成“未返回链接”卡片。
   - 数据口径与限制：用用户可读话术写清楚“本轮未纳入某类证据，因为没有形成可复核结果”；不要暴露接口失败、超时、参数名、服务名或取数日志。
12. 输出时优先回答：
   - 这个行业最近在发生什么
   - 当前市场关注的核心变量是什么
   - 事件如何沿产业链或价值链传导
   - 如果有估值数据，估值在什么位置
   - 如果有稳定成分篮子，哪些公司更有代表性
13. 如果新闻、研报、估值、成分数据里只拿到其中一部分，要明确结论边界；不要把缺失部分用常识补齐成完整行业报告。

Rules:
- 成分股、估值、近期新闻、近期事件、近期研报这五类信息里，拿到什么就写什么；没拿到的不要靠模型补。
- Same Boat `sector_id`、Fin Data basket、Fin Graph subject、Shenwan valuation 是四套不同口径。不要互相复用 ID 或把用户原词直接塞进下游参数；每条链路必须有自己的 resolver 证据。
- 跨来源 workflow 必须先用 `resolve_research_identity` 固定统一身份，再把 resolver 返回的目标字段分发给各来源；如果某个目标字段缺失，保留缺口并降级该证据族，不要用宽基指数、示例行业或假 ID 替代。
- 如果只有 Same Boat 行业目录解析成功，而 Fin Data basket 没有稳定候选，就输出行业观点和要闻，成分股/申万篮子口径留空；不要硬写申万篮子或龙头名单。
- 如果 Fin Graph subject 没有稳定候选，跳过图谱增强；不要因此放弃新闻、研报、行情或同舟观点，也不要写成工程能力未完成。
- 行业新闻与行业研报各取 `3-5` 条即可，避免为了凑材料反复调用直到撞上 `tool_calls_limit`。
- 如果 `search_baskets` 能匹配到稳定篮子，优先引用 `list_constituents` 的结果给出代表性公司；不要凭经验硬写成分股。
- 如果用户问“最近怎么看”，默认优先近 `7-30` 天的信息，不要只给长期常识。
- 如果用户问“多空风向”“行业分数”“看多看空”，必须明确列出 Same Boat 返回的观点分数、看多/看空倾向、主要理由和分数边界；不能只给行情或新闻摘要。
- 如果 `list_sector_viewpoints` 未返回有效 `sentiment_score` / `radar` / 理由，只能说本次同舟观点字段不足，不能自行生成行业分数。
- 如果用户要求生成灵感 HTML 且主要证据家族少于 3 类，不要硬生成完整风向标；先提示需要补充可复核证据。证据家族可包括：行情/估值、新闻/公告、同舟观点、资金/拥挤度、研报、行业图谱。
- 工具调用失败不是用户结果。允许内部改用替代工具或降级口径，但最终页面不要出现“接口失败”“超时”“外部数据源暂不可用”“未返回可用数据”等技术字样。
- 如果 `list_market_news` 返回 `url`，必须进入源头复核卡；不要写“没有文章级链接”。如果只有无链接数据，源头复核区可以少放或不放，不能创建“无链接来源标注”卡片区。
- 如果使用 `list_market_news(importance_scores=[4, 5])` 筛要闻，要说明这是按 Same Boat 返回的重要度字段筛选，不是专家自行计算的影响力评级。
- 如果用户问“为什么异动”“影响哪些环节”“看不懂传导”，输出里必须有“事件 -> 机制 -> 上游/中游/下游 -> 代表标的/板块 -> 验证变量”的链路；没有链路证据时要写“当前只能给事件线索，传导链路证据不足”。
- 如果用户问“今天这个板块为什么涨”，默认先给一句人话答案，再列证据；不要先写行业定义长篇背景。
- 如果本次检索结果主要集中在 `1-2` 天，不能把它包装成完整行业判断；必须额外说明“短窗口证据偏新闻催化”，并补充需要验证的中期变量。
- 如果用户问“景气度”“政策变化”“近期变化”“当前关注点”，至少要有新闻、事件或研报中的一类证据；否则要明确说“当前检索到的最新公开信息有限”。
- 如果用户问估值，必须先调用 `query_sector_valuation` 或明确说明当前没有估值数据；不要自己口头判断“估值高 / 低”。
- 图谱能力只作为行业框架增强，不要默认把图谱放在所有行业问题的第一步，也不要因为图谱失败就放弃整个回答。
- 如果 `get_industry_views` 返回“当前未返回已生成观点”，只能说明该 `index_code` 本次没有已生成观点；不要扩写成行业没有观点、没有研报或没有新闻。
- `list_industry_anomalies` 为空时，只能说明当前日期/行业过滤下未返回异动；不要扩写成行业近期没有事件或价格波动。
- 如果图谱、新闻、研报结论不一致，要保留来源边界，不要揉成单一确定事实。
- 不要输出图谱节点 `id`、`path`、完整 `outline` 原始结构、内部节点筛选策略或未公开节点名。
- 如果缺少成分股 / 篮子数据，要明确当前结论更偏”行业框架和事件层”，不是”标的池推荐层”。
- 如果缺少新闻 / 事件 / 研报中的大部分证据，不要写”近期亮点””市场一致预期””主要催化已明确”这类强表述。
- 不要写”市场观点认为””预计下半年””有望企稳回升”这类卖方腔总结，除非用户明确要看研报观点。
- 如果要提估值，最多保留一个关键数字，马上解释”现在大概算便宜还是不便宜”，不要展开历史分位。
- 如果要提代表公司，默认只提 `1-2` 家，不要列龙头名单。少用研究腔（”景气度上修、估值切换、催化验证”），尽量换成客户一听就懂的话。

Suggested output template:
1. 行业框架与关键维度
2. 近期异动与证据窗口
3. 产业链传导链路
4. 多空风向与同舟观点分数（仅在 Same Boat 返回 `sentiment_score` / `radar` 时展示）
5. 代表性成分或观察标的
6. 最近新闻与研报
7. 当前市场关注焦点和验证变量
8. 证据缺口与一句话行业状态总结

WorkBuddy HTML handoff:
1. 页面标题建议用“{行业/主题}行业多空风向标”，不要改成深度报告标题。
2. 首屏固定为：一句话答案、证据窗口、短/中/长期三卡、`接下来最该盯的三条线`、右侧综合分或证据强度。
3. 中段固定展示“六维因子雷达或六维因子条 / 原文索引 / 期限拆解 / 核心信号 / 情景与验证矩阵”，其中因子图要做成封面级大图，不要做成小缩略图或细表格；不要使用保证预测口吻。
4. 文末必须有数据口径、限制和非投资建议；不要把技术失败放在首屏或源头卡片里。

Examples:
- `白酒最近怎么看`
- `动力煤行业最近发生了什么`
- `帮我快速看一下纯碱行业`
- `今天机器人板块为什么涨`
