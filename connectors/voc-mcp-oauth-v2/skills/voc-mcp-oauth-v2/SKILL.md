---
name: voc-mcp-oauth-v2
display_name: 腾讯汽车行业舆情运营连接器
display_name_en: Tencent Automotive VOC Operations Connector
description: 腾讯汽车行业舆情运营 MCP 连接器（OAuth 2.1 授权）。覆盖品牌舆情监测与内容运营全链路「监测 → 分析 → 创作 → 审核 → 分发」：状态字典、监测对象（品牌 / 车型 / 事件）管理、关键词与竞品词典配置、采集触发与全量导出、舆情分析与文章创作流程、高频问排行与舆情收敛结论、正文编辑与人工审核、分发渠道与授权管理。
description_zh: 腾讯汽车行业舆情运营 MCP 连接器 - 通过 OAuth 2.1 授权连接舆情运营平台。覆盖「监测 → 分析 → 创作 → 审核 → 分发」全链路：状态字典、监测对象管理、舆情分析与洞察、内容运营与人工审核、渠道分发与授权。
description_en: 'Tencent Automotive VOC Operations MCP Connector - Connects to the VOC operations platform via OAuth 2.1. Covers the full chain of monitor, analyze, create, review and distribute: status dictionary, monitoring-object management, sentiment analysis and insights, content operations with human review, and channel distribution management.'
category: automotive
version: 1.5.2
author: Tencent Automotive Industry
---
# 腾讯汽车行业舆情运营 MCP

本连接器对接舆情运营平台（服务端标识 `voc-platform`），使用 **MCP Streamable HTTP + OAuth 2.1（PKCE）**鉴权，覆盖品牌舆情监测与内容运营的完整链路。

## 使用流程

1. **首次使用**：在连接器管理页点击「连接」，浏览器跳转到授权页完成账号授权；授权完成后自动回到 WorkBuddy，Token 保存在本机 `~/.workbuddy`。
2. **日常使用**：无需重复授权，直接通过 MCP 工具调用即可。
3. **授权过期**：返回 `401` 时在连接器管理页点击「重新连接」。
4. **Token 安全**：如怀疑泄露，到舆情平台账号设置中撤销授权后重新连接。

## 鉴权说明

- **Connector 类型**：MCP Streamable HTTP + OAuth 2.1（PKCE，公共客户端）
- **MCP 地址**：`https://iautomark.sdm.qq.com/voc/mcp`
- **授权服务器**：`https://iautomark.sdm.qq.com/voc`（`/oauth/authorize`、`/oauth/token`，scope `mcp`）
- **参数发现**：客户端凭服务端暴露的元数据自动获取授权参数（`/.well-known/oauth-protected-resource` 与 `/.well-known/oauth-authorization-server`），连接器包内不含 `client_id` / `client_secret`
- 服务端返回 `401` 时带 `WWW-Authenticate` 头指向元数据地址，由连接器框架自动触发重新授权

## 工具清单

工具名与参数一律以连接建立后 `list_tools` 返回的 `inputSchema` 为准，不要靠记忆编造。

### 一、状态字典

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `voc_query_status_reference` | 查询状态字段的取值含义（状态字典） | 无参数，会话开始时先调一次 |

返回高频问 / 文章 / 机审 / 采集 / 分发 / 渠道 / 智能体任务等状态字段的完整取值含义。能力是否可用不在这份字典里，看各工具自身的返回（如 `capability_enabled`）。

### 二、监测对象（TOPIC）管理

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `voc_query_topics` | 查询监测对象及其采集配置与运行状态 | `enabled`、`limit`、`offset` |
| `voc_manage_topic` | 创建 / 修改 / 启用 / 停用监测对象 | `action`（必填）、`topic_id`、`topic` |
| `voc_trigger_topic_collection` | 立即触发单个 TOPIC 采集，不等调度周期 | `topic_id`（必填）、`platforms` |
| `voc_export_topic` | 导出 TOPIC 全量舆情条目为 JSONL 下载链接 | `topic_id`（必填） |

- 监测对象对应品牌 / 车型 / 事件三类，返回 `platforms[].platform` 为采集平台码，`next_run_at` 为下次调度时间
- 平台绑定只回平台码、采集周期、启停与下次调度时间；取样时间窗、单轮条数、评论抓取、抓取间隔等执行细节不对外下发，要查或要改走控制台
- `keywords` 传数组，每项一个独立关键词；不要把「小米SU7、SU7」写成一项，否则各平台检索不到内容
- `voc_manage_topic` **不支持删除**（删除会影响历史数据）
- `voc_trigger_topic_collection` 是一次性额外采集，不改动自动采集排期
- `voc_export_topic` 已按（TOPIC, 平台, 条目 ID）跨轮次去重，含互动指标与 `raw` 原始字段

### 三、分析与洞察

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `voc_trigger_pipeline` | 触发智能体流程 | `pipeline`（必填）、`entity_id`（必填） |
| `voc_query_hot_questions` | 查询高频问排行，统计分析主数据源 | `topic_id`、`status`、`source`、`include_closed`、`include_examples`、`include_merge_sources`、`limit`、`offset` |
| `voc_query_convergence` | 查询 TOPIC 在 AI 搜索中的舆情收敛判定 | `topic_id`、`limit`、`offset` |
| `voc_query_topic_report` | 查询 TOPIC 当前舆情分析报告 | `topic_id`（必填）、`include_html` |

- `voc_trigger_pipeline` 的 `pipeline` 取 `analysis`（对指定采集批次做舆情分析并更新高频问）或 `article_creation`（对指定高频问发起文章创作）；`entity_id` 按流程传不同实体：`analysis` 传 `crawl_batch_id`，`article_creation` 传 `hot_question_id`。**同一实体在同一时间窗内幂等**，重复调用返回同一任务，返回 `agent_task_id` 与 `status`
- 高频问每条已聚合 `mention_count`（提及数）、`total_likes`（累计赞）、`negative_hits`（负面信号数）、`priority_score`（优先级分），可直接用于分桶、求和、排序
- 每条高频问只带精简的对象摘要（`id` / `name` / `topic_type`）：判断归属不必再查对象清单，但话题桶、关键词等分桶维度不在里面，分桶要另查 `voc_query_topics`
- 传 `topic_id` 会附带本轮采集概览：`failed_platforms` 非空说明本轮有采集缺口、统计会偏少；衡量热度看跨轮去重后的 `new_item_count`，不看累计 `item_count`
- 平台写的现状速览（`insight`）超过 200 字会截断并以「…」结尾，引用时不要当成完整原文
- `voc_query_convergence` 返回置信度与归因说明，以及被点名需重写回应的问题（`redraft`）；**默认只返回最近 5 条**（一次判定即一轮评测），看更长走势用 `offset` 翻页；归因说明 `reasoning` 超过 300 字会截断并以「…」结尾；收敛智能体未接入时返回 `capability_enabled=false`
- `voc_query_topic_report` 只读，每个 TOPIC 只有一份当前报告，重新生成成功即覆盖；报告在控制台「舆情报告」页生成

### 四、内容运营

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `voc_query_article` | 查询文章内容与审核 / 发布状态 | `article_id`、`status`、`include_html`、`editable_wrapper`、`limit`、`offset` |
| `voc_update_article` | 回写正文，生成新版本并自动重跑机审 | `article_id`、`html`（均必填）、`title`、`note`、`citations` |
| `voc_review_article` | 人工审核：通过或驳回 | `article_id`、`decision`（均必填）、`opinion` |
| `voc_create_hot_question` | 运营手动录入高频问 | `topic_id`、`question`（均必填）、`insight`、`subject_brand`、`subject_series`、`subject_model` |

- `voc_query_article` 传 `article_id` 返回单篇详情（HTML 正文 + 分发记录 + 佐证清单 `citations` + 配图 + 机审意见）；不传则返回列表，**列表只给定位与状态**（标题、状态、机审风险、审核记录、版本轮次），不含正文、佐证清单、配图与审核意见——审核与在线修改一律先取单篇。文章状态与高频问状态**相互独立**
- 正文以 `mimeType=text/html` 的 resource 返回（`uri` 形如 `voc://article/{id}/v{version}.html`），落盘后用 `present_files` 展示，不要贴源码或用 Markdown 转写
- `voc_update_article` 回写后 `edit_version +1`，旧版本留档，并自动重跑机审；改动正文角标时用 `citations`（`index` / `claim` / `url` / `source_name`，`url` 为空表示该角标没有材料）一并回写佐证清单，不回写则清单保持原样、下次读取会提示「佐证可能已失效」
- `voc_review_article` 的 `decision` 取 `approve`（进入 APPROVED，可发起分发）或 `reject`（驳回意见作为输入自动重写，直至轮次上限）；`opinion` 在 `reject` 时**必填**（作为重写输入），`approve` 时可选
- `voc_create_hot_question` 创建后 `source=MANUAL`、状态 `OPEN`，从下一轮起纳入所属 TOPIC 的 GEO 评测

### 五、分发与渠道

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `voc_query_channels` | 查询分发渠道与账号授权状态 | `code` |
| `voc_distribution` | 把文章分发到指定渠道 | `article_id`、`channels`（均必填）、`cover_url` |

- **调用 `voc_distribution` 前必须先调 `voc_query_channels`**，据此确定 `channels` 与是否需要 `cover_url`；`channels` 只能从返回的 `distributable_codes` 中取，其余会被服务端拒绝
- 渠道条目给出能不能发、为什么不能发，以及 `account_count`（可用账号数）；**平台不下发账号明细**，具体哪个账号过期、哪个可用看不到，分发时也由服务端自动选账号。`authorized=false` 且 `account_count>0` 是登录态失效，去控制台「渠道授权」处理，不是没绑账号
- 渠道查询返回 `degraded=true` 时是平台凭证查询失败，`authorized` 不可信，稍后重试即可，不要引导用户重新授权
- `cover_required=true` 时 `cover_url` 必传且要公网可达，尺寸不低于渠道声明的下限，否则前置校验会失败
- `voc_distribution` 按文章是否已分发过自动选路径：未分发且已 `APPROVED` 的文章创建新分发（`mode=create`）；已分发的在**最近一次分发**上处理 `channels`（`mode=append`）——没发过的渠道追加、上次失败终态的重发、已成功 / 待扫码 / 在途的跳过。回执里的 `appended` / `retried` / `skipped` 要逐项转述，`skipped` 表示该渠道这次**没有**被重新发布

## 关键链路约束

以下为服务端强校验的硬规则，违反会被拒绝：

1. **会话开始先调 `voc_query_status_reference`**，取准状态字段口径
2. **机审 HIGH 风险的文章不能直接人审通过**——必须先用 `voc_update_article` 改出新版本，才能 `voc_review_article` 通过
3. **`voc_update_article` 与 `voc_review_article` 都要求文章处于 `PENDING_HUMAN_REVIEW`**（待人审）状态
4. **驳回必须带意见**：`voc_review_article` 的 `decision=reject` 时 `opinion` 必填，缺了会被拒绝
5. **分发前必须先查渠道**，`channels` 取自 `voc_query_channels` 的 `distributable_codes`
6. **`voc_manage_topic` 不支持删除**，停用请用 `action` 切换启停

典型链路：`voc_query_topics` 取对象 → `voc_query_hot_questions` 取待处理问题 → `voc_trigger_pipeline(article_creation)` 发起创作 → `voc_query_article` 取正文 → `voc_update_article` 修订 → `voc_review_article` 人审 → `voc_query_channels` → `voc_distribution` 分发。

## 参数口径约定

- 工具名、参数名、枚举值严格按 `inputSchema` 传递，禁止自行推测或改写
- 涉及汽车行业业务字段（品牌、车型、车系、竞品、平台、渠道）时，严格遵循舆情平台口径，不用模型常识补齐
- 分页参数按服务端声明传递；返回为空时先核对参数口径，不要编造数据
- 状态字段取值含义以 `voc_query_status_reference` 的返回为准

## 错误与边界

| 场景 | 处理建议 |
| --- | --- |
| 调用返回 401 | 授权失效或过期，引导用户在连接器管理页重新连接 |
| 工具调用 403 | 当前账号在该对象或渠道上没有权限，提示联系平台管理员，不要重试 |
| 工具调用 5xx | 舆情平台服务异常，稍后重试；连续失败则如实告知服务端不可用 |
| 状态校验被拒 | 核对文章 / 高频问当前状态是否满足前提（如是否在 `PENDING_HUMAN_REVIEW`） |
| 渠道不可分发 | 看 `authorized` 与 `account_count`：有账号但仍不可分发是登录态失效，去控制台「渠道授权」；账号明细平台不下发，不要承诺查出是哪个账号 |
| 渠道查询 `degraded=true` | 平台凭证查询失败，渠道状态不可信，稍后重试；不要让用户重新授权 |
| 分发前置失败（`PRECHECK_FAILED`） | 多为封面缺失或尺寸不达标，按渠道声明的下限换图后重发 |
| 授权页打不开 | 确认可访问 `iautomark.sdm.qq.com`，该地址走域名 + HTTPS |
| 返回空结果 | 核对 TOPIC ID、时间范围、状态筛选口径，不要编造数据 |
| `capability_enabled=false` | 对应智能体能力未接入，如实告知用户该能力当前不可用 |
| `isError: true` | 把错误原文贴给用户，并说明可能原因（参数缺失、状态前提不满足、服务端异常） |

## 注意事项

- **分发有业务副作用**：`voc_distribution` 会把文章真实推送到外部渠道，调用前必须与用户确认渠道和文章范围
- **审核结论影响分发**：`voc_review_article` 的结论决定内容是否进入分发，代审场景需向用户复述审核依据
- **编辑会生成新版本**：`voc_update_article` 回写后产生新版本并重跑机审，改动前说明影响范围
- **长流程不要盲目重试**：`voc_trigger_topic_collection` 与 `voc_trigger_pipeline` 属长流程，超时以任务状态查询结果为准
- 连接器包内不含任何真实凭证，OAuth 参数由平台侧下发
