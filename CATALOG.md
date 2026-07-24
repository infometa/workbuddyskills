# workbuddyskills 完整清单（中文说明）

每个条目包含：**用来做什么**、**前置条件**（API Key / 登录认证等）。目录与名称**可点击**跳转。

**前置条件 = 无**：一般不需额外密钥或登录即可阅读/使用说明；调用外部服务时平台侧仍可能有限制。

- 技能包：**295** · 连接器：**69** · 专家：**365** · 官方插件：**57** · 团队插件：**30**

> 清单自动同步自 WorkBuddy 公开市场；最近同步：2026-07-25

---
## 目录

1. [技能包 skills/](#1-技能包-skills)
2. [连接器 connectors/](#2-连接器-connectors)
3. [专家包 experts/](#3-专家包-experts)
4. [插件市场 plugins/](#4-插件市场-plugins)

## 1. 技能包 `skills/`

### AI / Agent 工具（159）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`agent-browser-core`](./skills/agent-browser-core/) | [agent-browser-core](./skills/agent-browser-core/SKILL.md) | 用途：OpenClaw skill for the agent-browser CLI (Rust-based with Node.js fallback) enabling A… | 需要登录 / OAuth / 扫码授权 |
| [`agent-mail`](./skills/agent-mail/) | [agentmail](./skills/agent-mail/SKILL.md) | 用途：Email inbox for AI agents. Check messages, send emails, and communicate via your own @… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`AGENTMAIL_API_KEY`、`YOUR_API_KEY` |
| [`agent-mbti`](./skills/agent-mbti/) | [agent-mbti](./skills/agent-mbti/SKILL.md) | 用途：AI Agent personality diagnosis and configuration system based on MBTI framework. Use w… | 无 |
| [`agent-team-orchestration`](./skills/agent-team-orchestration/) | [agent-team-orchestration](./skills/agent-team-orchestration/SKILL.md) | 用途：Orchestrate multi-agent teams with defined roles, task lifecycles, handoff protocols, … | 无 |
| [`ai-shifu-course-creator`](./skills/ai-shifu-course-creator/) | [ai-shifu-course-creator](./skills/ai-shifu-course-creator/SKILL.md) | 用途：Use when the user works with AI-Shifu (AI师傅) courses in any capacity of creating, writ… | 需要登录 / OAuth / 扫码授权；需要环境变量：`SHIFU_TOKEN` |
| [`aihot`](./skills/aihot/) | [aihot](./skills/aihot/SKILL.md) | AI HOT (aihot.virxact.com) 中文 AI 资讯查询 Skill。当用户想知道"今天 AI 圈有什么"、"AI 日报"、"AI HOT"、"AI 资讯"、"… | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`airchina-travel-assistant`](./skills/airchina-travel-assistant/) | [airchina-travel-assistant](./skills/airchina-travel-assistant/SKILL.md) | 帮用户领取中国国航（Air China / 国航 / 国际航空）的优惠券。当用户说"我想领国航的券"、"帮我领张国航机票券"、"国航有活动券吗"、"给我发国航优惠券"、"airc… | 需要环境变量：`SECRET_KEY` |
| [`anti-distill`](./skills/anti-distill/) | [anti-distill](./skills/anti-distill/SKILL.md) | 用途：Anti-distillation defense for employee Skills. Clean your skill files to look complete… | 无 |
| [`api-gateway`](./skills/api-gateway/) | [api-gateway](./skills/api-gateway/SKILL.md) | 用途：Connect to external services through Maton-managed API routes. | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`API_KEY`、`MATON_API_KEY`、`YOUR_API_KEY` |
| [`apple-notes`](./skills/apple-notes/) | [apple-notes](./skills/apple-notes/SKILL.md) | 用途：Manage Apple Notes via the `memo` CLI on macOS (create, view, edit, delete, search, mo… | 无 |
| [`apple-reminders`](./skills/apple-reminders/) | [apple-reminders](./skills/apple-reminders/SKILL.md) | 用途：Manage Apple Reminders via the `remindctl` CLI on macOS (list, add, edit, complete, de… | 无 |
| [`arxiv-reader`](./skills/arxiv-reader/) | [arxiv-reader](./skills/arxiv-reader/SKILL.md) | 利用python，指定某个arxiv_id/url， 基于 LLM Agent 对这篇arxiv论文进行分类与深度阅读，直接print打印阅读笔记 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`LLM_API_KEY` |
| [`arxiv-watcher`](./skills/arxiv-watcher/) | [arxiv-watcher](./skills/arxiv-watcher/SKILL.md) | 用途：Search and summarize papers from ArXiv. Use when the user asks for the latest research… | 无 |
| [`autoresearch`](./skills/autoresearch/) | [autoresearch](./skills/autoresearch/SKILL.md) | 用途：Run Karpathy-style autoresearch optimization on any content. Generates 50+ variants, s… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`ANTHROPIC_API_KEY` |
| [`awesome-design-md`](./skills/awesome-design-md/) | [awesome-design-md](./skills/awesome-design-md/SKILL.md) | 用途：Curated collection of 54 DESIGN.md files extracted from real developer-focused website… | 无 |
| [`baidu-drive`](./skills/baidu-drive/) | [baidu-drive](./skills/baidu-drive/SKILL.md) | 百度网盘(Baidu Drive)文件管理 — 上传、下载、转存、分享、搜索、移动、复制、重命名、创建文件夹。TRIGGER: 用户提及\"百度网盘/bdpan/网盘/云盘/ba… | 需要登录 / OAuth / 扫码授权 |
| [`boss-skills`](./skills/boss-skills/) | [boss-skills](./skills/boss-skills/SKILL.md) | 用途：Distill a real boss into an AI skill, or generate a boss skill from famous entrepreneu… | 无 |
| [`brand-guidelines`](./skills/brand-guidelines/) | [brand-guidelines](./skills/brand-guidelines/SKILL.md) | 用途：Applies Anthropic's official brand colors and typography to any sort of artifact that … | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`browser`](./skills/browser/) | [browser](./skills/browser/SKILL.md) | 用途：Simple headless Puppeteer browser for rendering JavaScript-heavy pages and extracting … | 无 |
| [`browser-cash`](./skills/browser-cash/) | [browser-cash](./skills/browser-cash/SKILL.md) | 用途：Cloud browser sessions via Browser.cash API that bypass anti-bot protections (Cloudfla… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_CASH_API_KEY`、`BROWSER_CASH_KEY` |
| [`browser-use`](./skills/browser-use/) | [browser-use](./skills/browser-use/SKILL.md) | 用途：Automates browser interactions for web testing, form filling, screenshots, and data ex… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`BROWSER_USE_API_KEY` |
| [`cangjie-skill`](./skills/cangjie-skill/) | [cangjie-skill](./skills/cangjie-skill/SKILL.md) | Distill a book into a coherent set of executable skills. Use when the user asks to "拆书" /… | 无 |
| [`capability-evolver`](./skills/capability-evolver/) | [capability-evolver](./skills/capability-evolver/SKILL.md) | 用途：GitHub API token for auto-issue reporting and releases. | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`clawbrowser`](./skills/clawbrowser/) | [clawbrowser](./skills/clawbrowser/SKILL.md) | 用途：Use when the agent needs to drive a browser through the Microsoft Playwright CLI (`pla… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`cli-anything-hub`](./skills/cli-anything-hub/) | [cli-anything-hub](./skills/cli-anything-hub/SKILL.md) | 用途：Discover agent-native CLIs for professional software. Access the live catalog to find … | 无 |
| [`cloudbase`](./skills/cloudbase/) | [cloudbase](./skills/cloudbase/SKILL.md) | CloudBase is a full-stack development and deployment toolkit for building and launching w… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`cloudflare`](./skills/cloudflare/) | [cloudflare](./skills/cloudflare/SKILL.md) | 用途：Comprehensive Cloudflare platform skill covering Workers, Pages, storage (KV, D1, R2),… | 无 |
| [`cloudq`](./skills/cloudq/) | [cloudq](./skills/cloudq/SKILL.md) | 用户咨询腾讯云产品资源、AWS、阿里云等多云资源时，查看智能顾问架构图、架构目录、架构详情、架构评估结果、绘制架构图、开通智能顾问时、AI智能巡检、AI容量监测、AI混沌演练、A… | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY`、`TENCENTCLOUD_TOKEN` |
| [`cn-ecommerce-search`](./skills/cn-ecommerce-search/) | [cn-ecommerce-search](./skills/cn-ecommerce-search/SKILL.md) | > | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`colleague-skill`](./skills/colleague-skill/) | [colleague-skill](./skills/colleague-skill/SKILL.md) | 用途：Distill a colleague into an AI Skill. Auto-collect Feishu/DingTalk/Slack data, generat… | 需要飞书应用凭证或用户登录授权；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`content-factory`](./skills/content-factory/) | [content-factory](./skills/content-factory/SKILL.md) | 用途：Multi-agent content production system. One piece of source content becomes many format… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`content-ops`](./skills/content-ops/) | [content-ops](./skills/content-ops/SKILL.md) | 用途：Score, evaluate, and iteratively improve any content or strategy using an auto-assembl… | 无 |
| [`content-repurposer`](./skills/content-repurposer/) | [content-repurposer](./skills/content-repurposer/SKILL.md) | 用途：Transform long-form content into platform-optimized snippets. Your agent takes one blo… | 无（可选 API/账号以增强能力） |
| [`conversion-ops`](./skills/conversion-ops/) | [conversion-ops](./skills/conversion-ops/SKILL.md) | 用途：conversion-ops | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`crash-expert-skill`](./skills/crash-expert-skill/) | [crash-expert-skill](./skills/crash-expert-skill/SKILL.md) | 用途：Linux kernel vmcore/coredump analysis expert skill. Use when users need to analyze Lin… | 可能需要启用对应 MCP / 连接器 |
| [`darwin-skill`](./skills/darwin-skill/) | [darwin-skill](./skills/darwin-skill/SKILL.md) | Darwin Skill (达尔文.skill): autonomous skill optimizer inspired by Karpathy's autoresearch.… | 无（可选 API/账号以增强能力） |
| [`deck-generator`](./skills/deck-generator/) | [deck-generator](./skills/deck-generator/SKILL.md) | 用途：Generate professional presentations with AI-generated images. Use when asked to create… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`GEMINI_API_KEY` |
| [`deep-research`](./skills/deep-research/) | [deep-research](./skills/deep-research/SKILL.md) | 用途：Structured deep research workflow with human-in-the-loop control. Use /research to gen… | 无 |
| [`diagnose`](./skills/diagnose/) | [diagnose](./skills/diagnose/SKILL.md) | 用途：Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → mini… | 无 |
| [`didi-ride-skill`](./skills/didi-ride-skill/) | [didi-ride-skill](./skills/didi-ride-skill/SKILL.md) | 中国城市出行服务。当用户表达任何交通出行需求时必须使用此技能——包括打车/叫车/网约车、查价格、路线规划（公交/驾车/步行/骑行）、周边搜索、查询订单/司机位置/取消订单。关键词… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`DIDI_MCP_KEY`、`YOUR_KEY` |
| [`earnings-tracker`](./skills/earnings-tracker/) | [earnings-tracker](./skills/earnings-tracker/SKILL.md) | AI 驱动的财报追踪器，自动扫描 A 股/美股财报日历，推送重要财报更新 | 无 |
| [`edgeone`](./skills/edgeone/) | [edgeone](./skills/edgeone/SKILL.md) | 用途：Deploy a single HTML document to Tencent EdgeOne Pages via mcporter with no login or A… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`english-exam-writing-reviewer`](./skills/english-exam-writing-reviewer/) | [english-exam-writing-reviewer](./skills/english-exam-writing-reviewer/SKILL.md) | > | 无（可选 API/账号以增强能力） |
| [`excalidraw-diagram`](./skills/excalidraw-diagram/) | [excalidraw-diagram](./skills/excalidraw-diagram/SKILL.md) | 用途：Create Excalidraw diagrams for workflows, architectures, protocols, concepts, and syst… | 无 |
| [`fadada-document-sign`](./skills/fadada-document-sign/) | [fadada-document-sign](./skills/fadada-document-sign/SKILL.md) | 用途：FaDaDa e-signature tool | 需要环境变量：`FADADA_APP_SECRET` |
| [`fbs-bookwriter`](./skills/fbs-bookwriter/) | [fbs-bookwriter](./skills/fbs-bookwriter/SKILL.md) | 福帮手出品 \| 高质量长文档手稿工具链：书籍、手册、白皮书、行业指南、长篇报道、深度专题；支持联网查证（宿主允许时启用，离线自动降级）、S/P/C/B 分层审校、中文排版与 M… | 可能需要启用对应 MCP / 连接器 |
| [`finance-ops`](./skills/finance-ops/) | [finance-ops](./skills/finance-ops/SKILL.md) | 用途：AI-powered financial analysis suite. Generates executive CFO briefings from QuickBooks… | 无（可选 API/账号以增强能力） |
| [`flyai`](./skills/flyai/) | [flyai](./skills/flyai/SKILL.md) | 用途：Search flights, hotels, attractions, concerts, and travel deals with natural language.… | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要环境变量：`FLYAI_API_KEY` |
| [`frontend-dev`](./skills/frontend-dev/) | [frontend-dev](./skills/frontend-dev/SKILL.md) | \| | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`MINIMAX_API_KEY` |
| [`gif-sticker-maker`](./skills/gif-sticker-maker/) | [gif-sticker-maker](./skills/gif-sticker-maker/SKILL.md) | \| | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`MINIMAX_API_KEY` |
| [`github-ai-trends`](./skills/github-ai-trends/) | [github-ai-trends](./skills/github-ai-trends/SKILL.md) | 用途：Generate GitHub AI trending project reports as formatted text leaderboards. Fetches to… | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`github-trending-cn`](./skills/github-trending-cn/) | [github-trending-cn](./skills/github-trending-cn/SKILL.md) | GitHub Trending Monitor. Fetch GitHub trending repos by daily/weekly/monthly period using… | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`globepilot-ai-agent-2`](./skills/globepilot-ai-agent-2/) | [globepilot-ai-agent-2](./skills/globepilot-ai-agent-2/SKILL.md) | 用途：AI-powered global travel assistant providing visa info, currency conversion, airport s… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`growth-engine`](./skills/growth-engine/) | [growth-engine](./skills/growth-engine/SKILL.md) | 用途：growth-engine | 需要环境变量：`EMAIL_AUTH_TOKEN`、`PIPELINE_AUTH_TOKEN`、`RECRUITING_AUTH_TOKEN` |
| [`handoff`](./skills/handoff/) | [handoff](./skills/handoff/SKILL.md) | 用途：Compact the current conversation into a handoff document for another agent to pick up.… | 无 |
| [`himalaya`](./skills/himalaya/) | [himalaya](./skills/himalaya/SKILL.md) | 用途：CLI to manage emails via IMAP/SMTP. Use `himalaya` to list, read, write, reply, forwar… | 需要登录 / OAuth / 扫码授权 |
| [`html-deploy`](./skills/html-deploy/) | [html-deploy](./skills/html-deploy/SKILL.md) | 用途：Publish a single self-contained HTML page to htmlcode.fun and return live URLs. Use wh… | 无 |
| [`humanizer`](./skills/humanizer/) | [humanizer](./skills/humanizer/SKILL.md) | 用途：Remove signs of AI-generated writing from text. Use when editing or reviewing text to … | 无（可选 API/账号以增强能力） |
| [`impeccable`](./skills/impeccable/) | [impeccable](./skills/impeccable/SKILL.md) | \| | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`infographic-maker`](./skills/infographic-maker/) | [infographic-maker](./skills/infographic-maker/SKILL.md) | 用途：Generate hand-drawn cartoon-style infographics from articles, concepts, reports, or da… | 无 |
| [`jinshuju`](./skills/jinshuju/) | [jinshuju](./skills/jinshuju/SKILL.md) | 用途：Use when the user wants to create or edit forms, collect or query entries, bulk-update… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`YOUR_API_KEY`、`YOUR_API_SECRET` |
| [`kdocs`](./skills/kdocs/) | [kdocs](./skills/kdocs/SKILL.md) | 金山文档（WPS 云文档 / 365.kdocs.cn / www.kdocs.cn）— 在线云文档平台，【金山文档官方 Skill】。 当用户提到金山文档、Kdocs、云文档、… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`khazix-writer`](./skills/khazix-writer/) | [khazix-writer](./skills/khazix-writer/SKILL.md) | \| | 需要微信/企微相关凭证或扫码登录 |
| [`lark-unified`](./skills/lark-unified/) | [lark-unified](./skills/lark-unified/SKILL.md) | 用途：Unified Lark/Feishu CLI suite covering messaging, documents, collaboration, scheduling… | 需要飞书应用凭证或用户登录授权；需要登录 / OAuth / 扫码授权 |
| [`lexiang-knowledge-base`](./skills/lexiang-knowledge-base/) | [lexiang-knowledge-base](./skills/lexiang-knowledge-base/SKILL.md) | 用于访问乐享知识库平台的专用 skill。当用户明确提到「乐享」「lexiang」「知识库」「知识」「文档」等关键词，或用户提供的链接 host 为 lexiangla.com，… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`LEXIANG_TOKEN` |
| [`libtv-skill`](./skills/libtv-skill/) | [libtv-skill](./skills/libtv-skill/SKILL.md) | agent-im 会话技能 - 通过 liblib.tv 的 AI 能力生成和编辑图片/视频。覆盖场景包括：生成（文生图、文生视频、图生视频、做动画、画一个xxx、来段xxx）、… | 需要环境变量：`LIBTV_ACCESS_KEY` |
| [`lingxi-financialsearch-skill`](./skills/lingxi-financialsearch-skill/) | [lingxi-financialsearch-skill](./skills/lingxi-financialsearch-skill/SKILL.md) | 国泰海通金融数据查询Skill，通过自然语言查询A股实时行情、公司基本信息、F10财务数据、个股技术指标等金融数据。遵循沪深交易所行情转发规则，仅提供授权范围内基础行情数据。触发… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`llm-wiki`](./skills/llm-wiki/) | [llm-wiki](./skills/llm-wiki/SKILL.md) | 用途：Build and maintain a personal knowledge base (wiki) using LLMs. Instead of RAG-style r… | 无 |
| [`macro-monitor`](./skills/macro-monitor/) | [macro-monitor](./skills/macro-monitor/SKILL.md) | 每日宏观数据监控和推送。自动浏览免费数据源（Trading Economics、FRED、国家统计局、央行官网、财联社等），整理整合过去24小时发布的宏观数据和政策信息，并推送给… | 无（可选 API/账号以增强能力） |
| [`market-researcher`](./skills/market-researcher/) | [market-researcher](./skills/market-researcher/SKILL.md) | 用途：Market research specialist focused on comprehensive market analysis, consumer behavior… | 无 |
| [`mcdonald-assistant`](./skills/mcdonald-assistant/) | [mcdonald-assistant](./skills/mcdonald-assistant/SKILL.md) | 麦当劳中国点餐与优惠助手。用户提到麦当劳、麦麦、麦当劳外卖、点餐、查菜单、领麦当劳优惠券、查麦当劳积分/订单/活动时使用。依赖 WorkBuddy 已配置并信任的麦当劳 MCP … | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`MCP_TOKEN` |
| [`mcp-builder`](./skills/mcp-builder/) | [mcp-builder](./skills/mcp-builder/SKILL.md) | 用途：Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs … | 可能需要启用对应 MCP / 连接器 |
| [`mcporter`](./skills/mcporter/) | [mcporter](./skills/mcporter/SKILL.md) | 用途：Use the mcporter CLI to list, configure, auth, and call MCP servers/tools directly (HT… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`meituan-coupon-workbuddy`](./skills/meituan-coupon-workbuddy/) | [meituan-coupon-workbuddy](./skills/meituan-coupon-workbuddy/SKILL.md) | 【美团官方】美团生活助手，支持外卖、餐饮团购、酒店住宿、门票度假、休闲娱乐、闪购、医药等多品类优惠券/红包/神券的一键领取与历史领取记录查询。核心能力：1）一键领券，覆盖上述多品… | 需要登录 / OAuth / 扫码授权；需要环境变量：`AUTH_SCRIPT`、`USER_TOKEN` |
| [`meituan-huisheng-coupon`](./skills/meituan-huisheng-coupon/) | [meituan-huisheng-coupon](./skills/meituan-huisheng-coupon/SKILL.md) | > | 需要登录 / OAuth / 扫码授权；需要环境变量：`AUTH_SCRIPT`、`USER_TOKEN` |
| [`migraq`](./skills/migraq/) | [migraq](./skills/migraq/SKILL.md) | 腾讯云迁移平台（CMG/MSP）全流程能力。触发词：资源扫描、扫描阿里云/AWS/华为云/GCP资源、生成云资源清单、选型推荐、对标腾讯云、推荐规格、帮我推荐、给我推荐、ECS对… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`minimax-xlsx`](./skills/minimax-xlsx/) | [minimax-xlsx](./skills/minimax-xlsx/SKILL.md) | 用途：Open, create, read, analyze, edit, or validate Excel/spreadsheet files (.xlsx, .xlsm, … | 无 |
| [`multi-search-engine`](./skills/multi-search-engine/) | [multi-search-engine](./skills/multi-search-engine/SKILL.md) | 用途：Multi search engine integration with 16 engines (7 CN + 9 Global). Supports advanced s… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`my-novel-writer`](./skills/my-novel-writer/) | [my-novel-writer](./skills/my-novel-writer/SKILL.md) | >- | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`NOVEL_API_KEY` |
| [`nano-banana-pro`](./skills/nano-banana-pro/) | [nano-banana-pro](./skills/nano-banana-pro/SKILL.md) | 用途：Generate/edit images with Nano Banana Pro (Gemini 3 Pro Image). Use for image create/m… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`GEMINI_API_KEY` |
| [`neodata-financial-search`](./skills/neodata-financial-search/) | [neodata-financial-search](./skills/neodata-financial-search/SKILL.md) | >- | 无 |
| [`news-summary`](./skills/news-summary/) | [news-summary](./skills/news-summary/SKILL.md) | 用途：This skill should be used when the user asks for news updates, daily briefings, or wha… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`OPENAI_API_KEY` |
| [`note-organizer`](./skills/note-organizer/) | [note-organizer](./skills/note-organizer/SKILL.md) | 用途：Joplin — Note Manager — personal knowledge base. Personal productivity tool. Use when … | 无 |
| [`novel-writer`](./skills/novel-writer/) | [novel-writer](./skills/novel-writer/SKILL.md) | 章节正文生成器 - 根据章节大纲、Voice Profile 和角色档案构建 LLM 提示词，用于生成章节正文。当需要根据大纲创作具体章节时使用。 | 无（可选 API/账号以增强能力） |
| [`nuwa-skill`](./skills/nuwa-skill/) | [nuwa-skill](./skills/nuwa-skill/SKILL.md) | 女娲造人：输入人名/主题/甚至只是模糊需求，自动深度调研→思维框架提炼→生成可运行的人物Skill。 | 需要微信/企微相关凭证或扫码登录 |
| [`obsidian`](./skills/obsidian/) | [obsidian](./skills/obsidian/SKILL.md) | 用途：Work with Obsidian vaults (plain Markdown notes) and automate via obsidian-cli. | 无 |
| [`open-lesson`](./skills/open-lesson/) | [open-lesson](./skills/open-lesson/SKILL.md) | 用途：Interact with openLesson tutoring API for Socratic learning: generate learning plans a… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`OPENLESSON_API_KEY`、`YOUR_API_KEY` |
| [`openai-image-gen`](./skills/openai-image-gen/) | [openai-image-gen](./skills/openai-image-gen/SKILL.md) | 用途：Batch-generate images via OpenAI Images API. Random prompt sampler + `index.html` gall… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`OPENAI_API_KEY` |
| [`openai-whisper`](./skills/openai-whisper/) | [openai-whisper](./skills/openai-whisper/SKILL.md) | 用途：Local speech-to-text with the Whisper CLI (no API key). | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`openai-whisper-api`](./skills/openai-whisper-api/) | [openai-whisper-api](./skills/openai-whisper-api/SKILL.md) | 用途：Transcribe audio via OpenAI Audio Transcriptions API (Whisper). | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`OPENAI_API_KEY` |
| [`openclaw-assets-to-workbuddy`](./skills/openclaw-assets-to-workbuddy/) | [openclaw-assets-to-workbuddy](./skills/openclaw-assets-to-workbuddy/SKILL.md) | 将 OpenClaw 用户的个人资产迁移到 WorkBuddy 对应位置，重点覆盖 SOUL.md、IDENTITY.md、USER.md、memory、skills、MCP 配… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`oracle`](./skills/oracle/) | [oracle](./skills/oracle/SKILL.md) | 用途：Use the @steipete/oracle CLI to bundle a prompt plus the right files and get a second-… | 无 |
| [`outbound-engine`](./skills/outbound-engine/) | [outbound-engine](./skills/outbound-engine/SKILL.md) | 用途：Design, analyze, and optimize cold outbound email campaigns for Instantly. Handles end… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`paper-quick-reader`](./skills/paper-quick-reader/) | [paper-quick-reader](./skills/paper-quick-reader/SKILL.md) | > | 无（可选 API/账号以增强能力） |
| [`perplexity`](./skills/perplexity/) | [perplexity](./skills/perplexity/SKILL.md) | 用途：Search the web with AI-powered answers via Perplexity API. Returns grounded responses … | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`PERPLEXITY_API_KEY` |
| [`plan-tracker`](./skills/plan-tracker/) | [plan-tracker](./skills/plan-tracker/SKILL.md) | 当用户需要目标拆解、每日打卡、连续签到、学习热力图、进度预警时使用。支持 SMART 澄清 + OKR 月周拆解 + ABC 三档每日任务（A 完美 / B 基础 / C ≤15… | 无（可选 API/账号以增强能力） |
| [`playwright-browser-automation`](./skills/playwright-browser-automation/) | [playwright-browser-automation](./skills/playwright-browser-automation/SKILL.md) | 用途：Direct Playwright API for browser automation without MCP complexity. Navigate websites… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`playwright-scraper-skill`](./skills/playwright-scraper-skill/) | [playwright-scraper-skill](./skills/playwright-scraper-skill/SKILL.md) | 用途：Playwright-based web scraping OpenClaw Skill with anti-bot protection. Successfully te… | 需要登录 / OAuth / 扫码授权 |
| [`podcast-ops`](./skills/podcast-ops/) | [podcast-ops](./skills/podcast-ops/SKILL.md) | >- | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`ANTHROPIC_API_KEY`、`OPENAI_API_KEY`、`OPENAI_LLM_KEY` |
| [`porteden-email`](./skills/porteden-email/) | [porteden-email](./skills/porteden-email/SKILL.md) | 用途：Email Management - Secure Gmail, Outlook & Exchange - multi account support. Read, sea… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`PE_API_KEY` |
| [`price-history`](./skills/price-history/) | [price-history](./skills/price-history/SKILL.md) | 封装慢慢买（manmanbuy.com）官方 MCP，按关键词搜索全网商品的参考好价、实时价格与隐藏优惠券，并基于返回数据判断当前价是否为真实低价、识别"先涨后降"的虚假促销。当… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`product-showcase-site`](./skills/product-showcase-site/) | [product-showcase-site](./skills/product-showcase-site/SKILL.md) | 用途：Generate a comprehensive deployable product showcase website for an existing web app. … | 可能需要启用对应 MCP / 连接器；需要环境变量：`YOUR_SITE_KEY` |
| [`promo-creator-skills`](./skills/promo-creator-skills/) | [promo-creator-skills](./skills/promo-creator-skills/SKILL.md) | 产品宣传片制作总控 skill pack。用于从产品说明、官网、应用截图或 GitHub 仓库制作 60-90 秒宣传视频，按阶段完成 brief、storyboard、素材、H… | 无 |
| [`prompt-engineering-expert`](./skills/prompt-engineering-expert/) | [prompt-engineering-expert](./skills/prompt-engineering-expert/SKILL.md) | 用途：Advanced expert in prompt engineering, custom instructions design, and prompt optimiza… | 无 |
| [`qmd`](./skills/qmd/) | [qmd](./skills/qmd/SKILL.md) | 用途：Local hybrid search for markdown notes and docs. Use when searching notes, finding rel… | 可能需要启用对应 MCP / 连接器 |
| [`qqmusic`](./skills/qqmusic/) | [qqmusic](./skills/qqmusic/SKILL.md) | QQ Music — search songs, albums, playlists, music videos, artists; daily recommendations;… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`QQMUSIC_API_KEY` |
| [`remotion-video-toolkit`](./skills/remotion-video-toolkit/) | [remotion-video-toolkit](./skills/remotion-video-toolkit/SKILL.md) | 用途：Complete toolkit for programmatic video creation with Remotion + React. Covers animati… | 无 |
| [`responsiveness-check`](./skills/responsiveness-check/) | [responsiveness-check](./skills/responsiveness-check/SKILL.md) | 用途：Test website responsiveness across viewport widths using browser automation. Resizes a… | 需要 GitHub Token 或 `gh auth login`；可能需要启用对应 MCP / 连接器 |
| [`resume-assistant`](./skills/resume-assistant/) | [resume-assistant](./skills/resume-assistant/SKILL.md) | > | 需要微信/企微相关凭证或扫码登录 |
| [`revenue-intelligence`](./skills/revenue-intelligence/) | [revenue-intelligence](./skills/revenue-intelligence/SKILL.md) | 用途：revenue-intelligence | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`AHREFS_TOKEN`、`GONG_API_KEY`、`HUBSPOT_API_KEY` |
| [`sag`](./skills/sag/) | [sag](./skills/sag/SKILL.md) | 用途：ElevenLabs text-to-speech with mac-style say UX. | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`ELEVENLABS_API_KEY`、`SAG_API_KEY` |
| [`sales-pipeline`](./skills/sales-pipeline/) | [sales-pipeline](./skills/sales-pipeline/SKILL.md) | 用途：sales-pipeline | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`BRAVE_API_KEY`、`HUBSPOT_API_KEY`、`INSTANTLY_API_KEY` |
| [`sales-playbook`](./skills/sales-playbook/) | [sales-playbook](./skills/sales-playbook/SKILL.md) | 用途：sales-playbook | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`AHREFS_API_KEY`、`ANTHROPIC_API_KEY`、`OPENAI_API_KEY`、`SEMRUSH_API_KEY` |
| [`seo-ops`](./skills/seo-ops/) | [seo-ops](./skills/seo-ops/SKILL.md) | 用途：seo-ops | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`AHREFS_TOKEN`、`BRAVE_API_KEY`、`GOOGLE_CLIENT_SECRET` |
| [`shippage`](./skills/shippage/) | [shippage](./skills/shippage/SKILL.md) | 用途：Publish HTML or Markdown to a public URL instantly with ShipPage. Use when a user want… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器；需要环境变量：`API_KEY` |
| [`shopify-admin-api`](./skills/shopify-admin-api/) | [shopify-admin-api](./skills/shopify-admin-api/SKILL.md) | 用途：Full read/write access to Shopify Admin REST API for managing orders, products, custom… | 需要环境变量：`SHOPIFY_ACCESS_TOKEN` |
| [`sino-drug-instructions-search`](./skills/sino-drug-instructions-search/) | [sino-drug-instructions-search](./skills/sino-drug-instructions-search/SKILL.md) | 在用户询问药品说明书、用药信息、适应症、禁忌、用法用量、不良反应、成分、规格、厂家，或根据症状/疾病查找药品时使用此技能。⚠️ 调用前须已通过 use_skill 加载本技能（s… | 可能需要启用对应 MCP / 连接器；需要环境变量：`SKILLS_BIZ_TOKEN` |
| [`skill-creator`](./skills/skill-creator/) | [skill-creator](./skills/skill-creator/SKILL.md) | 用途：Guide for creating effective skills. This skill should be used when users want to crea… | 无（可选 API/账号以增强能力） |
| [`skill-scanner`](./skills/skill-scanner/) | [skill-scanner](./skills/skill-scanner/SKILL.md) | Scan any agent skill for security risks before you install or use it. Powered by Tencent … | 无 |
| [`skill-vetter`](./skills/skill-vetter/) | [skill-vetter](./skills/skill-vetter/SKILL.md) | 用途：Security-first skill vetting for AI agents. Use before installing any skill from commu… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`skills-security-check`](./skills/skills-security-check/) | [skills-security-check](./skills/skills-security-check/SKILL.md) | 腾讯云鼎实验室出品，Skill安全审查工具。对用户指定的skill.md文件及其配套的文档、程序、脚本等进行全面安全审计，确保引用安全 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`OPENAI_API_KEY` |
| [`smart-page`](./skills/smart-page/) | [smart-page](./skills/smart-page/SKILL.md) | 腾讯文档智能页面（Smart Page）是可交互在线汇报网页生成工具，适用于汇报、述职、周报、复盘、数据看板、课件、培训、调研报告、会议纪要和本地 HTML 上云。区别于 PPT… | 可能需要启用对应 MCP / 连接器 |
| [`smooth-browser`](./skills/smooth-browser/) | [smooth-browser](./skills/smooth-browser/SKILL.md) | 用途：PREFERRED BROWSER - Browser for AI agents to carry out any task on the web. Use when y… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`stagehand-browser-cli`](./skills/stagehand-browser-cli/) | [stagehand-browser-cli](./skills/stagehand-browser-cli/SKILL.md) | 用途：Automate web browser interactions using natural language via CLI commands. Use when th… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`BROWSERBASE_API_KEY` |
| [`static-app`](./skills/static-app/) | [static-app](./skills/static-app/SKILL.md) | 用途：Deploy static websites and built frontend apps to Static.app hosting. Use when a user … | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`STATIC_APP_API_KEY` |
| [`summarize`](./skills/summarize/) | [summarize](./skills/summarize/SKILL.md) | 用途：Summarize URLs or files with the summarize CLI (web, PDFs, images, audio, YouTube). | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`ANTHROPIC_API_KEY`、`APIFY_API_TOKEN`、`FIRECRAWL_API_KEY`、`GEMINI_API_KEY`、`GOOGLE_API_KEY`、`GOOGLE_GENERATIVE_AI_API_KEY` |
| [`task-alignment`](./skills/task-alignment/) | [task-alignment](./skills/task-alignment/SKILL.md) | 用途：Alignment conversation starting from a user's rough idea. Co-decides with the user whe… | 需要登录 / OAuth / 扫码授权 |
| [`task-implement`](./skills/task-implement/) | [task-implement](./skills/task-implement/SKILL.md) | 用途：Autonomous task execution driven by documents under `.task/<MMDD_slug>/` (produced by … | 无 |
| [`tavily`](./skills/tavily/) | [tavily](./skills/tavily/SKILL.md) | 用途：AI-optimized web search using Tavily Search API. Use when you need comprehensive web r… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`TAVILY_API_KEY` |
| [`team-ops`](./skills/team-ops/) | [team-ops](./skills/team-ops/SKILL.md) | 用途：Audit team performance using the Elon Algorithm (identify A/B/C players) and extract a… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`ANTHROPIC_API_KEY`、`HUBSPOT_API_KEY`、`OPENAI_API_KEY` |
| [`tencent-campus-recruit`](./skills/tencent-campus-recruit/) | [tencent-campus-recruit](./skills/tencent-campus-recruit/SKILL.md) | 当用户询问腾讯校园招聘相关问题时使用，包括：校招/实习投递流程与时间节点、岗位搜索与推荐、 招聘公告与宣讲会动态、简历诊断与优化、面试准备与模拟陪练、校招防诈骗识别。 通过 jo… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`tencent-docs`](./skills/tencent-docs/) | [tencent-docs](./skills/tencent-docs/SKILL.md) | 腾讯文档（docs.qq.com）-在线云文档平台，是创建、编辑、管理文档的首选 skill。涉及"新建/创建/编辑/读取/查看/搜索文档"、"保存文件"、"云文档"、"腾讯文档… | 可能需要启用对应 MCP / 连接器；需要环境变量：`TENCENT_DOCS_TOKEN` |
| [`tencent-meeting-skill`](./skills/tencent-meeting-skill/) | [tencent-meeting-skill](./skills/tencent-meeting-skill/SKILL.md) | 在用户提及腾讯会议、视频会议、线上会议相关内容与操作时使用此技能。触发关键词包括：预约会议、创建会议、修改会议、取消会议、查询会议、会议详情、会议号、meeting_id、mee… | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器；需要环境变量：`TENCENT_MEETING_TOKEN` |
| [`tencent-music-campus-recruit`](./skills/tencent-music-campus-recruit/) | [tencent-music-campus-recruit](./skills/tencent-music-campus-recruit/SKILL.md) | 当用户询问腾讯校园招聘相关问题时使用，包括：校招/实习投递流程与时间节点、岗位搜索与推荐、 招聘公告与宣讲会动态、组织架构/BG/部门介绍、简历诊断与优化、面试准备与模拟陪练、校… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`tencent-survey`](./skills/tencent-survey/) | [tencent-survey](./skills/tencent-survey/SKILL.md) | 腾讯问卷（wj.qq.com）- 在线问卷调查平台。涉及「问卷」「调查」「表单」「投票」「考试」「测评」「wj.qq.com」等操作时优先使用。支持能力：(1) 获取问卷详情（标… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`TENCENT_SURVEY_TOKEN` |
| [`tencent-yunzhi`](./skills/tencent-yunzhi/) | [tencent-yunzhi](./skills/tencent-yunzhi/SKILL.md) | 腾讯乐享（lexiangla.com / csig.lexiangla.com）知识库专用操作。仅在用户消息包含 lexiangla.com 链接、或明确提及『乐享/云知/Lex… | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`LEXIANG_TOKEN` |
| [`tencentcloud-ocr`](./skills/tencentcloud-ocr/) | [tencentcloud-ocr](./skills/tencentcloud-ocr/SKILL.md) | 腾讯云通用文字识别（高精度版）(GeneralAccurateOCR) 技能包。当用户发送/粘贴图片、提供图片URL、或要求识别图片中的文字时，应自动调用此技能。支持图像整体文字… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tencentcloud-ocr-extractdocagent`](./skills/tencentcloud-ocr-extractdocagent/) | [tencentcloud-ocr-extractdocagent](./skills/tencentcloud-ocr-extractdocagent/SKILL.md) | 腾讯云实时文档抽取Agent(ExtractDocAgent)接口调用技能。当用户需要从图片或PDF中按自定义字段名称进行结构化信息抽取时，应使用此技能。支持自定义字段名称、字段… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tencentcloud-ocr-general`](./skills/tencentcloud-ocr-general/) | [tencentcloud-ocr-general](./skills/tencentcloud-ocr-general/SKILL.md) | 腾讯云广告文字识别(AdvertiseOCR)接口调用技能。当用户需要从图片中识别文字内容时,应使用此技能。支持中英文、横排、竖排及倾斜场景的图片文字识别,支持90度、180度、… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tencentcloud-ocr-questionmarkagent`](./skills/tencentcloud-ocr-questionmarkagent/) | [tencentcloud-ocr-questionmarkagent](./skills/tencentcloud-ocr-questionmarkagent/SKILL.md) | 腾讯云试题批改Agent(SubmitQuestionMarkAgentJob/DescribeQuestionMarkAgentJob)接口调用技能。当用户需要对试卷图片或试题… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tencentcloud-ocr-recognizetableaccurate`](./skills/tencentcloud-ocr-recognizetableaccurate/) | [tencentcloud-ocr-recognizetableaccurate](./skills/tencentcloud-ocr-recognizetableaccurate/SKILL.md) | 腾讯云表格识别v3(RecognizeTableAccurateOCR)接口调用技能。当用户需要从表格图片或PDF中识别常规表格、无线表格、多表格的内容,提取每个单元格的文字信息… | 需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tmux`](./skills/tmux/) | [tmux](./skills/tmux/SKILL.md) | 用途：Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping p… | 无 |
| [`travel-planning`](./skills/travel-planning/) | [travel-planning](./skills/travel-planning/SKILL.md) | 用途：Plan trips with itineraries, multi-city routing, budget optimization, family logistics… | 无 |
| [`university-applications`](./skills/university-applications/) | [university-applications](./skills/university-applications/SKILL.md) | 全体系命理大师 — 八字四柱、紫微斗数、奇门遁甲、六爻、梅花易数、塔罗、星盘、 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`web-access`](./skills/web-access/) | [web-access](./skills/web-access/SKILL.md) | 所有联网操作必须通过此 skill 处理，包括：搜索、网页抓取、登录后操作、网络交互等。 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`web-performance-audit`](./skills/web-performance-audit/) | [web-performance-audit](./skills/web-performance-audit/SKILL.md) | 用途：Analyze deployed websites and web apps for performance quality. Measures Core Web Vita… | 可能需要启用对应 MCP / 连接器 |
| [`web-scraper`](./skills/web-scraper/) | [web-scraper](./skills/web-scraper/SKILL.md) | 用途：Web scraping and content comprehension agent — multi-strategy extraction with cascade … | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`OPENROUTER_API_KEY` |
| [`web-search-exa`](./skills/web-search-exa/) | [web-search-exa](./skills/web-search-exa/SKILL.md) | 用途：Neural web search, content extraction, company and people research, code search, and d… | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要环境变量：`YOUR_EXA_KEY`、`YOUR_KEY` |
| [`wechat-viral-topic`](./skills/wechat-viral-topic/) | [wechat-viral-topic](./skills/wechat-viral-topic/SKILL.md) | 公众号编辑、短视频博主、漫画作者、H5 策划必备的热点爆款策划助手。当用户需要选题灵感、起爆款标题、把热点做成文章/短视频/漫画/H5 等全形态创作方案，或评估某个素材能不能爆时… | 需要微信/企微相关凭证或扫码登录 |
| [`wecom-weisheng-scrm`](./skills/wecom-weisheng-scrm/) | [wecom-weisheng-scrm](./skills/wecom-weisheng-scrm/SKILL.md) | 当用户需要查询或管理微盛企微管家（企业微信） SCRM 中的客户信息、客户标签、客户群、营销素材、活码、群发、跟进记录、聊天记录、联系人、商机、汇报、抽奖、客户日程等相关业务能力… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`weiyun`](./skills/weiyun/) | [weiyun](./skills/weiyun/SKILL.md) | 微云网盘 MCP 接口完整技能。包含 weiyun.list、weiyun.list_by_category、weiyun.download、weiyun.delete、weiy… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`WEIYUN_MCP_TOKEN` |
| [`weread-skills`](./skills/weread-skills/) | [weread-skills](./skills/weread-skills/SKILL.md) | 微信读书助手 — 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要环境变量：`WEREAD_API_KEY` |
| [`workbuddy-asset-migration`](./skills/workbuddy-asset-migration/) | [workbuddy-asset-migration](./skills/workbuddy-asset-migration/SKILL.md) | 在 WorkBuddy 国内版（~/.workbuddy/）和海外版（~/.workbuddy-ai/）之间，或跨机器之间，迁移用户个人资产（skills、memory、conv… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`workrally`](./skills/workrally/) | [workrally](./skills/workrally/SKILL.md) | WorkRally CLI (workrally) — 面向 AI Agent 的 AIGC 漫剧视频创作全流程工具集。 支持 AI 生图、AI 生视频、项目管理、资产库、媒资管… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`WORKRALLY_API_KEY`、`YOUR_API_KEY` |
| [`x-longform-post`](./skills/x-longform-post/) | [x-longform-post](./skills/x-longform-post/SKILL.md) | 用途：Write long-form X (Twitter) posts and threads in a founder/CEO voice. Use when draftin… | 无（可选 API/账号以增强能力） |
| [`xiaobai-coach`](./skills/xiaobai-coach/) | [xiaobai-coach](./skills/xiaobai-coach/SKILL.md) | 给小白讲清理财、基金、股票知识，并配套实操工具与清单的财商陪跑技能。当用户问个人理财、攒钱、基金/ETF/股票/债券入门、定投、资产配置、复利计算、估值、止盈止损、识别投资骗局等… | 无 |
| [`yingmi-skill`](./skills/yingmi-skill/) | [yingmi-skill](./skills/yingmi-skill/SKILL.md) | 当用户需要查询基金、策略、公告、财经资讯，做资产配置、组合诊断、风险回测、现金流分析，或生成图表、PDF 时，优先使用本 Skill 获取真实数据与可执行能力。 | 可能需要启用对应 MCP / 连接器 |
| [`yourself-skill`](./skills/yourself-skill/) | [yourself-skill](./skills/yourself-skill/SKILL.md) | 用途：Distill yourself into an AI Skill. Deconstruct chat history, diaries, social media, an… | 需要微信/企微相关凭证或扫码登录 |
| [`zoom-out`](./skills/zoom-out/) | [zoom-out](./skills/zoom-out/SKILL.md) | 用途：Tell the agent to zoom out and give broader context or a higher-level perspective on u… | 无 |

### 云 / 存储 / 部署（4）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`cnb-skill`](./skills/cnb-skill/) | [cnb-skill](./skills/cnb-skill/SKILL.md) | Interact with CNB (Cloud Native Build) platform via OpenAPI. Manage organizations, reposi… | 无（可选 API/账号以增强能力） |
| [`netlify-deploy`](./skills/netlify-deploy/) | [netlify-deploy](./skills/netlify-deploy/SKILL.md) | 用途：Deploy and manage Netlify sites with npx netlify. Use for first deploys, preview deplo… | 需要登录 / OAuth / 扫码授权 |
| [`novel-writing`](./skills/novel-writing/) | [novel-writing](./skills/novel-writing/SKILL.md) | AI长篇网文创作技能包。用于解决长篇网络小说创作中的核心痛点：上下文丢失、文风不一致、设定冲突、节奏失控、多线混乱、质量不稳、读者反馈无法内化。触发场景包括：开始新书、规划大纲、… | 无 |
| [`vercel-deploy`](./skills/vercel-deploy/) | [vercel-deploy](./skills/vercel-deploy/SKILL.md) | 用途：Deploy and manage Vercel projects from the terminal. Use for Vercel deployments, previ… | 需要环境变量：`VERCEL_TOKEN` |

### 内容 / 营销 / 媒体（5）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`ecommerce-copywriter`](./skills/ecommerce-copywriter/) | [ecommerce-copywriter](./skills/ecommerce-copywriter/SKILL.md) | 电商爆款文案生成技能。为淘宝/拼多多/抖音/京东卖家生成高转化率的商品标题、详情页文案、卖点提炼和促销文案。使用场景：(1) 商品标题优化，(2) 详情页文案生成，(3) 卖点提… | 无 |
| [`github-pages-auto-deploy`](./skills/github-pages-auto-deploy/) | [github-pages-auto-deploy](./skills/github-pages-auto-deploy/SKILL.md) | 用途：Configure automatic website deployment to GitHub Pages with GitHub Actions and custom … | 无 |
| [`setup-pre-commit`](./skills/setup-pre-commit/) | [setup-pre-commit](./skills/setup-pre-commit/SKILL.md) | 用途：Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in… | 无 |
| [`video-frames`](./skills/video-frames/) | [video-frames](./skills/video-frames/SKILL.md) | 用途：Extract frames or short clips from videos using ffmpeg. | 无 |
| [`web-deploy-github`](./skills/web-deploy-github/) | [web-deploy-github](./skills/web-deploy-github/SKILL.md) | 用途：Create and deploy single-page static websites to GitHub Pages with an autonomous workf… | 需要 GitHub Token 或 `gh auth login` |

### 开发 / 工程（2）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`github`](./skills/github/) | [github](./skills/github/SKILL.md) | 用途：Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh ap… | 需要登录 / OAuth / 扫码授权 |
| [`trello`](./skills/trello/) | [trello](./skills/trello/SKILL.md) | 用途：Manage Trello boards, lists, and cards via the Trello REST API. | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`TRELLO_API_KEY`、`TRELLO_TOKEN` |

### 搜索 / 研究 / 知识（15）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`airbnb`](./skills/airbnb/) | [airbnb](./skills/airbnb/SKILL.md) | 用途：Search Airbnb listings with prices, ratings, and direct links. No API key required. Us… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`aviationstack-flight-tracker`](./skills/aviationstack-flight-tracker/) | [aviationstack-flight-tracker](./skills/aviationstack-flight-tracker/SKILL.md) | 用途：Track flights in real-time with detailed status, gate info, delays, and live position.… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`AVIATIONSTACK_API_KEY` |
| [`browserwing`](./skills/browserwing/) | [browserwing](./skills/browserwing/SKILL.md) | 用途：Control browser automation through HTTP API. Supports page navigation, element interac… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`citation-manager`](./skills/citation-manager/) | [citation-manager](./skills/citation-manager/SKILL.md) | 用途：Add real references and standardize citations for research papers and theses. Supports… | 无 |
| [`cloudflare-worker-builder`](./skills/cloudflare-worker-builder/) | [cloudflare-worker-builder](./skills/cloudflare-worker-builder/SKILL.md) | 用途：Scaffold and deploy Cloudflare Workers with Hono routing, Vite plugin, and Static Asse… | 无 |
| [`ecomseer`](./skills/ecomseer/) | [ecomseer](./skills/ecomseer/SKILL.md) | TikTok Shop e-commerce data assistant. Search products, find trending items, analyze infl… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`ECOMSEER_API_KEY` |
| [`flight-tracker`](./skills/flight-tracker/) | [flight-tracker](./skills/flight-tracker/SKILL.md) | 用途：Flight tracking and scheduling. Track live flights in real-time by region, callsign, o… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`AVIATIONSTACK_API_KEY` |
| [`football-bayes`](./skills/football-bayes/) | [football-bayes](./skills/football-bayes/SKILL.md) | 20年经验的足球竞彩策略官：贝叶斯统计 + 现代战术周期化，输出胜平负概率与风险提示 | 无（可选 API/账号以增强能力） |
| [`gsap-animation-assistant`](./skills/gsap-animation-assistant/) | [gsap-animation-assistant](./skills/gsap-animation-assistant/SKILL.md) | 用途：GSAP assistant for generating and reviewing frontend animation code with timelines, Sc… | 需要登录 / OAuth / 扫码授权 |
| [`healthcheck`](./skills/healthcheck/) | [healthcheck](./skills/healthcheck/SKILL.md) | 用途：Track water and sleep with JSON file storage. | 无 |
| [`novel`](./skills/novel/) | [novel](./skills/novel/SKILL.md) | 用途：Manage novel data — chapters, characters, plots — from the terminal fast. Use when out… | 无 |
| [`stealth-browser`](./skills/stealth-browser/) | [stealth-browser](./skills/stealth-browser/SKILL.md) | 用途：Ultimate stealth browser automation with anti-detection, Cloudflare bypass, CAPTCHA so… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`YOUR_2CAPTCHA_KEY`、`YOUR_ANTICAPTCHA_KEY`、`YOUR_CAPSOLVER_KEY` |
| [`study-planner`](./skills/study-planner/) | [study-planner](./skills/study-planner/SKILL.md) | 当用户需要制定学习计划、备考计划、拆解复习目标时使用。输入目标+截止日+每日时长，输出每天可执行的学习计划，支持雅思/考研/期末复习等场景。 | 无（可选 API/账号以增强能力） |
| [`travel-cn`](./skills/travel-cn/) | [travel-cn](./skills/travel-cn/SKILL.md) | 旅行信息查询 - 去哪儿/携程/飞猪数据查询（Expedia 中国版） | 需要 12306 账号登录 |
| [`vip-skill`](./skills/vip-skill/) | [vip-skill](./skills/vip-skill/SKILL.md) | 唯品会（vip.com）电商服务技能包（vipshop-skills），整合唯品会搜索、商品查询、活动查询、图片搜索等多项购物服务，是一套完整的唯品会购物 AI 助手解决方案。当… | 需要登录 / OAuth / 扫码授权 |

### 数据 / 金融 / 股票（6）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`fintech-engineer`](./skills/fintech-engineer/) | [fintech-engineer](./skills/fintech-engineer/SKILL.md) | 用途：Expert fintech engineer specializing in financial systems, regulatory compliance (PCI … | 无 |
| [`qcc-company`](./skills/qcc-company/) | [qcc-company](./skills/qcc-company/SKILL.md) | 通过企查查 Connector 查询中国境内企业的工商信息、股权结构、高管人员、财务数据、对外投资、历史变更、上市信息、分支机构、联系方式、开票信息及企业身份核验。当用户的请求涉… | 需要配置/启用 MCP 连接器 |
| [`stock-analysis`](./skills/stock-analysis/) | [stock-analysis](./skills/stock-analysis/SKILL.md) | 用途：Analyze stocks and cryptocurrencies using Yahoo Finance data. Supports portfolio manag… | 需要登录 / OAuth / 扫码授权；需要环境变量：`AUTH_TOKEN` |
| [`us-stock-analysis`](./skills/us-stock-analysis/) | [us-stock-analysis](./skills/us-stock-analysis/SKILL.md) | 用途：Comprehensive US stock analysis including fundamental analysis (financial metrics, bus… | 无 |
| [`westock-data`](./skills/westock-data/) | [westockdata](./skills/westock-data/SKILL.md) | 查询A股、港股、美股个股/指数/ETF的详细数据，包括：K线/分时、财务报表（三大报表多期查询，支持跨市场批量对比）、资金流向、技术指标、筹码分析、股东结构、分红除权、业绩预告、… | 无 |
| [`westockdata`](./skills/westockdata/) | [westockdata](./skills/westockdata/SKILL.md) | 查询A股、港股、美股个股/指数/ETF的详细数据，包括：K线/分时、财务报表（三大报表多期查询，支持跨市场批量对比）、资金流向、技术指标、筹码分析、股东结构、分红除权、业绩预告、… | 无 |

### 文档 / 办公 / 协作（44）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`12306-train-assistant`](./skills/12306-train-assistant/) | [12306-train-assistant](./skills/12306-train-assistant/SKILL.md) | 12306 查询与订票辅助技能，支持余票查询、经停站查询、中转换乘、候补查询与提交/取消、登录状态检查、密码登录与二维码登录、下单与支付链接获取；当用户提到火车票、高铁票、经停站… | 需要微信/企微相关凭证或扫码登录；需要 12306 账号登录；需要登录 / OAuth / 扫码授权；需要环境变量：`KYFW_PASSWORD` |
| [`a-stock-data`](./skills/a-stock-data/) | [a-stock-data](./skills/a-stock-data/SKILL.md) | A股全栈数据工具包 — 覆盖行情(mootdx+腾讯+百度K线)、研报(东财+同花顺+iwencai)、信号(同花顺热点+北向+龙虎榜+解禁+行业)、资金面(融资融券+大宗交易+… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`IWENCAI_API_KEY`、`IWENCAI_KEY` |
| [`academic-translation`](./skills/academic-translation/) | [academic-translation](./skills/academic-translation/SKILL.md) | 当用户需要学术论文中英互译、润色、Chinglish 修复时使用。三步法（直译→反思→雅化），公式/cite 零损伤，顶会术语库，双栏对照，不动原文件。 | 无 |
| [`academic-tutor`](./skills/academic-tutor/) | [academic-tutor](./skills/academic-tutor/SKILL.md) | 当大学生问题目、需要苏格拉底式引导讲解、或论文写作指导时使用。不直接给答案，每轮三段式（引导问题→关键提示→下一步建议），数理化/编程/经管/文史哲全覆盖。 | 无（可选 API/账号以增强能力） |
| [`admapix`](./skills/admapix/) | [admapix](./skills/admapix/SKILL.md) | 用途：Optional bearer token for the AdMapix Deep Research service, if enabled for the accoun… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`ADMAPIX_API_KEY`、`ADMAPIX_DEEP_RESEARCH_TOKEN`、`YOUR_API_KEY` |
| [`android-native-dev`](./skills/android-native-dev/) | [android-native-dev](./skills/android-native-dev/SKILL.md) | 用途：Android native application development and UI design guide. Covers Material Design 3, … | 无 |
| [`caldav-calendar`](./skills/caldav-calendar/) | [caldav-calendar](./skills/caldav-calendar/SKILL.md) | 用途：Sync and query CalDAV calendars (iCloud, Google, Fastmail, Nextcloud, etc.) using vdir… | 无 |
| [`canvas-design`](./skills/canvas-design/) | [canvas-design](./skills/canvas-design/SKILL.md) | 用途：Create beautiful visual art in .png and .pdf documents using design philosophy. You sh… | 无（可选 API/账号以增强能力） |
| [`caveman`](./skills/caveman/) | [caveman](./skills/caveman/SKILL.md) | >- | 无 |
| [`charity-finance-assistant`](./skills/charity-finance-assistant/) | [charity-finance-assistant](./skills/charity-finance-assistant/SKILL.md) | 用途：Nonprofit finance and receipt management assistant. Use when users need to organize do… | 无 |
| [`charity-writing-assistant`](./skills/charity-writing-assistant/) | [charity-writing-assistant](./skills/charity-writing-assistant/SKILL.md) | 当用户提到公益文书、项目申请、结项报告、传播计划、写文书（公益场景）、写报告（公益项目）、整理材料（公益机构）、捐赠人服务方案、肖像授权书、项目上线、平台申请时使用。⚠️ 不适用… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`dingtalk-unified`](./skills/dingtalk-unified/) | [dingtalk-unified](./skills/dingtalk-unified/SKILL.md) | 钉钉 CLI 全能套件，基于官方 DingTalk Workspace CLI（dws）操作钉钉消息、群聊、通讯录、日历、待办、审批、考勤、日志、DING、AI 表格、钉钉文档、… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`email-daily-summary`](./skills/email-daily-summary/) | [email-daily-summary](./skills/email-daily-summary/SKILL.md) | 用途：Automatically logs into email accounts (Gmail, Outlook, QQ Mail, etc.) and generates d… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`english-intensive-reader`](./skills/english-intensive-reader/) | [english-intensive-reader](./skills/english-intensive-reader/SKILL.md) | \| | 无（可选 API/账号以增强能力） |
| [`flights-search`](./skills/flights-search/) | [flights](./skills/flights-search/SKILL.md) | 用途：Search flights via Google Flights. Find nonstop/connecting flights, filter by time and… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`flutter-dev`](./skills/flutter-dev/) | [flutter-dev](./skills/flutter-dev/SKILL.md) | 用途：Flutter cross-platform development guide covering widget patterns, Riverpod/Bloc state… | 无 |
| [`gifgrep`](./skills/gifgrep/) | [gifgrep](./skills/gifgrep/SKILL.md) | 用途：Search GIF providers with CLI/TUI, download results, and extract stills/sheets. | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`GIPHY_API_KEY`、`TENOR_API_KEY` |
| [`gmail`](./skills/gmail/) | [gmail](./skills/gmail/SKILL.md) | 用途：Gmail API integration with managed OAuth. Read, send, and manage emails, threads, labe… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`MATON_API_KEY`、`YOUR_API_KEY` |
| [`gog`](./skills/gog/) | [gog](./skills/gog/SKILL.md) | 用途：Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs. | 需要登录 / OAuth / 扫码授权 |
| [`grill-me`](./skills/grill-me/) | [grill-me](./skills/grill-me/SKILL.md) | 用途：Interview the user relentlessly about a plan or design until reaching shared understan… | 无 |
| [`guizang-ppt-skill`](./skills/guizang-ppt-skill/) | [guizang-ppt-skill](./skills/guizang-ppt-skill/SKILL.md) | 生成横向翻页网页 PPT（单 HTML 文件），含 WebGL 背景、章节幕封、数据大字报、图片网格等模板。提供两种风格：① "电子杂志 × 电子墨水"（衬线 + 流体背景 + … | 无（可选 API/账号以增强能力） |
| [`imap-smtp-email`](./skills/imap-smtp-email/) | [imap-smtp-email](./skills/imap-smtp-email/SKILL.md) | 用途：Read and send email via IMAP/SMTP. Check for new/unread messages, fetch content, searc… | 无（可选 API/账号以增强能力） |
| [`ios-application-dev`](./skills/ios-application-dev/) | [ios-application-dev](./skills/ios-application-dev/SKILL.md) | \| | 无（可选 API/账号以增强能力） |
| [`knowledge-framework-builder`](./skills/knowledge-framework-builder/) | [knowledge-framework-builder](./skills/knowledge-framework-builder/SKILL.md) | \| | 无（可选 API/账号以增强能力） |
| [`landing-page-generator`](./skills/landing-page-generator/) | [landing-page-generator](./skills/landing-page-generator/SKILL.md) | 用途：Generate a complete, deployable landing page from a brief. Produces a single self-cont… | 无（可选 API/账号以增强能力） |
| [`marketing-skills`](./skills/marketing-skills/) | [marketing-skills](./skills/marketing-skills/SKILL.md) | 用途：TL;DR: 23 marketing playbooks (CRO, SEO, copy, analytics, experiments, pricing, launch… | 无 |
| [`material-organizer`](./skills/material-organizer/) | [material-organizer](./skills/material-organizer/SKILL.md) | \| | 需要登录 / OAuth / 扫码授权 |
| [`minimax-docx`](./skills/minimax-docx/) | [minimax-docx](./skills/minimax-docx/SKILL.md) | > | 无（可选 API/账号以增强能力） |
| [`minimax-pdf`](./skills/minimax-pdf/) | [minimax-pdf](./skills/minimax-pdf/SKILL.md) | > | 无 |
| [`nano-pdf`](./skills/nano-pdf/) | [nano-pdf](./skills/nano-pdf/SKILL.md) | 用途：Edit PDFs with natural-language instructions using the nano-pdf CLI. | 无 |
| [`notebooklm-studio`](./skills/notebooklm-studio/) | [notebooklm-studio](./skills/notebooklm-studio/SKILL.md) | 用途：Import sources (URLs, YouTube, files, text) into Google NotebookLM and generate artifa… | 需要登录 / OAuth / 扫码授权 |
| [`notion`](./skills/notion/) | [notion](./skills/notion/SKILL.md) | 用途：Notion API for creating and managing pages, databases, and blocks. | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`NOTION_KEY` |
| [`pptx-generator`](./skills/pptx-generator/) | [pptx-generator](./skills/pptx-generator/SKILL.md) | 用途：Generate, edit, and read PowerPoint presentations. Create from scratch with PptxGenJS … | 无（可选 API/账号以增强能力） |
| [`react-native-dev`](./skills/react-native-dev/) | [react-native-dev](./skills/react-native-dev/SKILL.md) | \| | 需要登录 / OAuth / 扫码授权 |
| [`stock-analyzer`](./skills/stock-analyzer/) | [stock-analyzer](./skills/stock-analyzer/SKILL.md) | 全球股票综合分析工具。支持A股、港股、美股等东方财富覆盖的所有市场。根据用户输入的股票名称或代码，从东方财富网获取股票信息，进行基本面、新闻面、资金面三维分析，给出投资建议、买入… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`taobao`](./skills/taobao/) | [maishou](./skills/taobao/SKILL.md) | 商品价格全网对比技能，获取商品在淘宝(Taobao)、天猫(TMall)、京东(JD.com)、拼多多(PinDuoDuo)、抖音(Douyin)、快手(KaiShou)的最优价… | 无 |
| [`teachany`](./skills/teachany/) | [teachany](./skills/teachany/SKILL.md) | 用途：K-12 interactive courseware creation. Use for school-subject lesson pages, animations,… | 需要环境变量：`GH_TOKEN` |
| [`trip-planner-generator`](./skills/trip-planner-generator/) | [trip-planner-generator](./skills/trip-planner-generator/SKILL.md) | 通过交互式问答帮助用户生成结构化的旅行行程计划，输出包含每日行程、预算明细、行前清单和注意事项的 Markdown 文档。在用户做旅行计划、行程规划、安排出行（travel pl… | 需要 12306 账号登录 |
| [`tutor-skills`](./skills/tutor-skills/) | [tutor-skills](./skills/tutor-skills/SKILL.md) | 用途：Turn PDFs, docs, and codebases into Obsidian StudyVaults with structured notes, then q… | 无 |
| [`wacli`](./skills/wacli/) | [wacli](./skills/wacli/SKILL.md) | 用途：Send WhatsApp messages to other people or search/sync WhatsApp history via the wacli C… | 需要登录 / OAuth / 扫码授权 |
| [`weather-open-meteo`](./skills/weather-open-meteo/) | [weather-open-meteo](./skills/weather-open-meteo/SKILL.md) | 通过 open-meteo.com 公共 API 查询指定地点的当前天气和未来预报，无需 API key；当 open-meteo 请求失败时可降级使用 wttr.in。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`web-deploy`](./skills/web-deploy/) | [web-deploy](./skills/web-deploy/SKILL.md) | 用途：Build, preview, and deploy websites, web apps, and APIs using Vercel, Railway, GitHub … | 需要登录 / OAuth / 扫码授权；需要环境变量：`SECRET_KEY` |
| [`xurl`](./skills/xurl/) | [xurl](./skills/xurl/SKILL.md) | 用途：A Twitter research and content intelligence skill. Use to analyze Twitter profiles, th… | 无 |
| [`yt-competitive-analysis`](./skills/yt-competitive-analysis/) | [yt-competitive-analysis](./skills/yt-competitive-analysis/SKILL.md) | >- | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`YOUTUBE_API_KEY` |

### 腾讯 / 微信 / 企微（47）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`andonq`](./skills/andonq/) | [andonq](./skills/andonq/SKILL.md) | AndonQ 腾讯云智能客服"领域虾" — 不切窗口、不排队，即刻获得腾讯云全产品线专业解答。支持工单查询（列表/详情/流水）、集团/MC 工单与需求单管理、腾讯云全产品线智能问… | 需要登录 / OAuth / 扫码授权 |
| [`aviation-weather`](./skills/aviation-weather/) | [aviation-weather](./skills/aviation-weather/SKILL.md) | 用途：Fetch aviation weather data (METAR, TAF, PIREPs) from aviationweather.gov. Use for fli… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`cos-vectors`](./skills/cos-vectors/) | [cos-vectors](./skills/cos-vectors/SKILL.md) | 腾讯云 COS 向量桶全功能管理技能。覆盖向量桶、索引、向量数据的全生命周期管理，包括创建/删除/查询向量桶、创建/管理索引、插入/查询/搜索/删除向量数据、策略管理等 16 个… | 需要环境变量：`COS_VECTORS_SECRET_KEY` |
| [`ctrip-wendao`](./skills/ctrip-wendao/) | [ctrip-wendao](./skills/ctrip-wendao/SKILL.md) | 当用户发起任意旅行相关问询时，包含但不限于：预订酒店、机票查询、火车票查询、景点推荐、寻找当地特色玩乐、目的地查询、行程规划、美食住宿攻略、签证、查询旅游攻略、获取旅行建议等场景… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`WENDAO_API_KEY` |
| [`edgeone-pages-deploy`](./skills/edgeone-pages-deploy/) | [edgeone-pages-deploy](./skills/edgeone-pages-deploy/SKILL.md) | 用途：Deploy frontend and full-stack projects to Tencent EdgeOne Pages using the EdgeOne CLI… | 需要登录 / OAuth / 扫码授权 |
| [`email-skill`](./skills/email-skill/) | [email-skill](./skills/email-skill/SKILL.md) | 用途：Email management and automation. Send, read, search, and organize emails across multip… | 需要环境变量：`EMAIL_PASSWORD` |
| [`futuapi`](./skills/futuapi/) | [futuapi](./skills/futuapi/SKILL.md) | 富途 OpenAPI 交易与行情助手。查询股票行情、K线、报价、快照、买卖盘、逐笔成交、分时数据；解析期权简写代码、查询期权链、期权到期日；执行买入/卖出/下单/撤单/改单；查询… | 无（可选 API/账号以增强能力） |
| [`haina-shopping-assistant`](./skills/haina-shopping-assistant/) | [haina-shopping-assistant](./skills/haina-shopping-assistant/SKILL.md) | 值得买开发的海纳购物管家，一款专业为用户提供来自全网与兴趣高度相关的、公允的AI消费决策支持工具。它支持四种消费决策模式：商品推荐（根据需求精准匹配合适的商品）、商品总结（对特定… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`idea-validator`](./skills/idea-validator/) | [idea-validator](./skills/idea-validator/SKILL.md) | 用途：Validate startup ideas using Hexa's Opportunity Memo framework and Perceived Created V… | 无 |
| [`ima-skills`](./skills/ima-skills/) | [ima-skills](./skills/ima-skills/SKILL.md) | \| | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`IMA_OPENAPI_APIKEY` |
| [`imsg`](./skills/imsg/) | [imsg](./skills/imsg/SKILL.md) | 用途：iMessage/SMS CLI for listing chats, history, watch, and sending. | 无 |
| [`install-futu-opend`](./skills/install-futu-opend/) | [install-futu-opend](./skills/install-futu-opend/SKILL.md) | Futu OpenD 安装助手。自动下载安装Futu OpenD 并升级 Python SDK。支持 Windows、MacOS、Linux。用户提到安装、下载、启动、运行、配置… | 需要登录 / OAuth / 扫码授权 |
| [`jiaozhen-factcheck`](./skills/jiaozhen-factcheck/) | [jiaozhen-factcheck](./skills/jiaozhen-factcheck/SKILL.md) | 事实查证工具，对输入内容的具体说法、资讯、事件或常识进行真实性、准确性、可靠性判断。当用户需要较真一下，查证问题或判断信息真伪、识别谣言、询问真假，是真的吗，真的假的，能否xxx… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`legal-logic-analysis`](./skills/legal-logic-analysis/) | [legal-logic-analysis](./skills/legal-logic-analysis/SKILL.md) | 用途：Think through any legal situation like a lawyer. Issue spotting, jurisdiction, risk as… | 无 |
| [`markitdown-skill`](./skills/markitdown-skill/) | [markitdown-skill](./skills/markitdown-skill/SKILL.md) | 用途：Convert documents to Markdown using Microsoft's MarkItDown CLI (`markitdown`). Support… | 无 |
| [`md-to-pdf-cjk`](./skills/md-to-pdf-cjk/) | [md-to-pdf-cjk](./skills/md-to-pdf-cjk/SKILL.md) | 用途：Convert Markdown files to professional PDF documents with full CJK (Chinese/Japanese/K… | 无 |
| [`model-usage`](./skills/model-usage/) | [model-usage](./skills/model-usage/SKILL.md) | 用途：Use CodexBar CLI local cost usage to summarize per-model usage for Codex or Claude, in… | 无 |
| [`pdfkit-py`](./skills/pdfkit-py/) | [pdfkit-py](./skills/pdfkit-py/SKILL.md) | Pure-Python PDF toolkit with 50 commands covering reading, editing, conversion, forms, en… | 无（可选 API/账号以增强能力） |
| [`peekaboo`](./skills/peekaboo/) | [peekaboo](./skills/peekaboo/SKILL.md) | 用途：Capture and automate macOS UI with the Peekaboo CLI. | 无 |
| [`qq-email`](./skills/qq-email/) | [qq-email](./skills/qq-email/SKILL.md) | QQ邮箱 IMAP receive and SMTP send via Node.js scripts; credentials read from env vars QQ_EM… | 需要登录 / OAuth / 扫码授权 |
| [`skyline`](./skills/skyline/) | [skyline](./skills/skyline/SKILL.md) | WeChat Mini Program Skyline rendering engine. Use when developing with Skyline renderer, … | 需要微信/企微相关凭证或扫码登录 |
| [`tapd-openapi`](./skills/tapd-openapi/) | [tapd-openapi](./skills/tapd-openapi/SKILL.md) | TAPD OpenAPI skill，用于需求、缺陷、任务、迭代、Wiki、评论、工时、附件等 TAPD 平台操作。当用户提到「TAPD」「需求」「story」「缺陷」「bug」… | 需要环境变量：`TAPD_TOKEN` |
| [`tdd`](./skills/tdd/) | [tdd](./skills/tdd/SKILL.md) | 用途：Test-driven development with red-green-refactor loop. Use when user wants to build fea… | 无 |
| [`tdesign-miniprogram`](./skills/tdesign-miniprogram/) | [tdesign-miniprogram](./skills/tdesign-miniprogram/SKILL.md) | 用途：TDesign WeChat Mini Program UI component library by Tencent. Use when building WeChat … | 需要微信/企微相关凭证或扫码登录 |
| [`tencent-esign-contract`](./skills/tencent-esign-contract/) | [tencent-esign-contract](./skills/tencent-esign-contract/SKILL.md) | 腾讯电子签合同AI助手，支持合同起草、审查、对比、法条法规检索。当用户提到起草合同、写合同、生成合同、审查合同、检查合同风险、合规审核、法务审查、对比合同、合同差异、版本比较、查… | 需要登录 / OAuth / 扫码授权；需要环境变量：`ESIGN_TOKEN` |
| [`tencent-musician-skills`](./skills/tencent-musician-skills/) | [tencent-musician-skills](./skills/tencent-musician-skills/SKILL.md) | 腾讯音乐人智能分析助手（数据分析 + 宣推）。当用户提到以下任一类请求时触发：【数据分析类】分析数据、看播放趋势、歌曲表现、听众画像、数据洞察、粉丝构成、我的数据怎么样、分析这首… | 需要登录 / OAuth / 扫码授权 |
| [`tencent-news`](./skills/tencent-news/) | [tencent-news](./skills/tencent-news/SKILL.md) | 7×24 新闻资讯搜索工具，聚焦中国国内信息和国际热点。支持新闻搜索，包括热点新闻、早报晚报、实时资讯、领域新闻和天气信息查询。当用户需要搜索新闻、新闻热榜、新闻早晚报、订阅新闻… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`tencent-rumor-refuter`](./skills/tencent-rumor-refuter/) | [tencent-rumor-refuter](./skills/tencent-rumor-refuter/SKILL.md) | 嘿！我是小P \U0001F427，腾讯公司谣言辟谣辅助技能 有关腾讯公司的信息真真假假，我来帮你看看！ 可以通过以下方式唤醒我： (1) 直接呼叫\"小P\"或\"小p\"； … | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`tencent-ssv-techforgood`](./skills/tencent-ssv-techforgood/) | [tencent-ssv-techforgood](./skills/tencent-ssv-techforgood/SKILL.md) | 专注公益机构数字化赋能的智能助手，围绕腾讯技术公益数字工具箱（techforgood.qq.com）为社会组织匹配免费或低成本数字化产品，支持需求诊断、产品推荐、申领指引、数字化… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`tencent-weather`](./skills/tencent-weather/) | [tencent-weather](./skills/tencent-weather/SKILL.md) | 用途：Weather lookup tool covering Chinese cities and counties via the tencent-news CLI. Use… | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`tencent-yuanbao-gaokao-regional-passing-scores`](./skills/tencent-yuanbao-gaokao-regional-passing-scores/) | [tencent-yuanbao-gaokao-regional-passing-scores](./skills/tencent-yuanbao-gaokao-regional-passing-scores/SKILL.md) | 高考地区分数线信息检索助手。当用户询问各省份历年高考录取分数线、录取批次或对应排名时使用，支持按地区、年份、选科和批次查询，自动适配新老高考政策差异。 | 无 |
| [`tencent-yuanbao-gaokao-score-to-rank-lookup`](./skills/tencent-yuanbao-gaokao-score-to-rank-lookup/) | [tencent-yuanbao-gaokao-score-to-rank-lookup](./skills/tencent-yuanbao-gaokao-score-to-rank-lookup/SKILL.md) | 高考一分一段信息检索助手，帮助考生根据分数查询全省排名位次，或根据位次估算对应分数区间，或提供一分一段表。 | 无 |
| [`tencent-yuanbao-standard-search`](./skills/tencent-yuanbao-standard-search/) | [tencent-yuanbao-standard-search](./skills/tencent-yuanbao-standard-search/SKILL.md) | 用途：Search the web using TencentCloud Web Search API (WSA). Prioritize using it when you n… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`TENCENTCLOUD_WSA_APIKEY` |
| [`tencentcloud-cls`](./skills/tencentcloud-cls/) | [tencentcloud-cls](./skills/tencentcloud-cls/SKILL.md) | 腾讯云日志服务 CLS 技能。支持 CQL 日志检索、上下文查看、日志主题/日志集查看、机器组与机器状态查看、采集规则查看、日志直方图、指标采集与 PromQL 查询、告警策略与… | 需要环境变量：`TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY` |
| [`tencentcloud-cos`](./skills/tencentcloud-cos/) | [tencentcloud-cos](./skills/tencentcloud-cos/SKILL.md) | 用途：Credentials exist only in shell session environment variables; nothing written to disk | 需要环境变量：`TENCENT_COS_SECRET_KEY`、`TENCENT_COS_TOKEN` |
| [`tencentmap-lbs-skill`](./skills/tencentmap-lbs-skill/) | [tencentmap-lbs-skill](./skills/tencentmap-lbs-skill/SKILL.md) | 腾讯地图位置服务，支持POI搜索、路径规划、旅游规划、周边搜索，轨迹数据可视化和地图数据可视化。⚠️ 强制行为：本 Skill 加载后，第一个动作必须是检查是否存在正式 Key（… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`TMAP_WEBSERVICE_KEY` |
| [`tencentmap-map-assistant`](./skills/tencentmap-map-assistant/) | [tencentmap-map-assistant](./skills/tencentmap-map-assistant/SKILL.md) | 腾讯位置服务·地图助手 Skill，一句自然语言调用腾讯地图全套能力，无需开发者账号、开箱即用。提供 AI 旅游攻略、地点搜索（含评分/人均/营业时间）、关键词提示、路线规划（驾… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`tencentos-expert`](./skills/tencentos-expert/) | [tencentos-expert](./skills/tencentos-expert/SKILL.md) | TencentOS Server 全栈运维诊断，根据用户的自然语言描述，自动识别需要的能力接口，查询能力实现，使用具体能力解决客户问题。覆盖磁盘空间/分区/文件系统/LVM/健康… | 可能需要启用对应 MCP / 连接器 |
| [`things-mac`](./skills/things-mac/) | [things-mac](./skills/things-mac/SKILL.md) | 用途：Manage Things 3 via the `things` CLI on macOS (add/update projects+todos via URL schem… | 需要环境变量：`THINGS_AUTH_TOKEN` |
| [`wechat-article-pro`](./skills/wechat-article-pro/) | [wechat-article-pro](./skills/wechat-article-pro/SKILL.md) | 微信公众号文章发布专业版。功能：1)联网搜索热点信息 2)AI生成微信公众号封面图 3)撰写3000-5000字深度文章 4)使用公众号AI配图功能自动生成并上传封面 5)参考刘… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`wechat-article-search`](./skills/wechat-article-search/) | [wechat-article-search](./skills/wechat-article-search/SKILL.md) | 搜索微信公众号文章技能。通过微信搜索获取文章列表，覆盖科技/AI、社会热点、财经、教育、职场等各类中文资讯；可按关键词检索并返回标题、概要、发布时间、来源公众号与链接。当用户需要… | 需要微信/企微相关凭证或扫码登录 |
| [`wechat-miniprogram`](./skills/wechat-miniprogram/) | [wechat-miniprogram](./skills/wechat-miniprogram/SKILL.md) | WeChat Mini Program (微信小程序) development framework. Use when building WeChat mini apps wit… | 需要微信/企微相关凭证或扫码登录 |
| [`wechat-publisher`](./skills/wechat-publisher/) | [wechat-publisher](./skills/wechat-publisher/SKILL.md) | 一键发布 Markdown 到微信公众号草稿箱。基于 wenyan-cli，支持多主题、代码高亮、图片自动上传。 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`WECHAT_APP_SECRET` |
| [`wechatpay-basic-payment`](./skills/wechatpay-basic-payment/) | [wechatpay-basic-payment](./skills/wechatpay-basic-payment/SKILL.md) | 微信支付基础支付解决方案，涵盖支付、退款账单、分账、商户进件、开户意愿确认，提供选型/代码示例/业务速查/质量评估/排障五大能力。Use when user mentions "… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`wechatpay-product-coupon`](./skills/wechatpay-product-coupon/) | [wechatpay-product-coupon](./skills/wechatpay-product-coupon/SKILL.md) | 微信支付商品券接入解决方案，覆盖券类型选型、发券/核销/查询/退券/回调全链路，提供选型/示例代码/业务速查/质量评估/排障五大能力。Use when user mentions… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`wecom-unified`](./skills/wecom-unified/) | [wecom-unified](./skills/wecom-unified/SKILL.md) | 企业微信 CLI 全能套件，覆盖通讯录、消息、文档、日程、会议、待办 6 大业务域。支持按姓名/别名查找联系人、收发消息（文本/图片/文件/语音/视频）、读取/创建/编辑文档（可… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`xiaojia-free-marketing-pack`](./skills/xiaojia-free-marketing-pack/) | [xiaojia-free-marketing-pack](./skills/xiaojia-free-marketing-pack/SKILL.md) | 用途：Optional local config path. Defaults to ~/.codebuddy/xiaojia-free-marketing-pack.json. | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |

### 设计 / UI / 地图（12）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`12306`](./skills/12306/) | [12306](./skills/12306/SKILL.md) | 用途：Query China Railway 12306 for train schedules, remaining tickets, and station info. Us… | 需要 12306 账号登录 |
| [`blogwatcher`](./skills/blogwatcher/) | [blogwatcher](./skills/blogwatcher/SKILL.md) | 用途：Monitor blogs and RSS/Atom feeds for updates using the blogwatcher CLI. | 无 |
| [`education`](./skills/education/) | [education](./skills/education/SKILL.md) | 用途：Generate study plans, quizzes, flashcards, review materials, track learning progress a… | 无 |
| [`fullstack-dev`](./skills/fullstack-dev/) | [fullstack-dev](./skills/fullstack-dev/SKILL.md) | \| | 需要登录 / OAuth / 扫码授权；需要环境变量：`JWT_SECRET` |
| [`goal-tracker`](./skills/goal-tracker/) | [goal-tracker](./skills/goal-tracker/SKILL.md) | 用途：Track long-term goals with milestones, daily logging, and accountability. Use when use… | 无 |
| [`habit-tracker`](./skills/habit-tracker/) | [habit-tracker](./skills/habit-tracker/SKILL.md) | 用途：Build habits with streaks, reminders, and progress visualization. Use when users want … | 无（可选 API/账号以增强能力） |
| [`ozon-1688-uploader`](./skills/ozon-1688-uploader/) | [ozon-1688-uploader](./skills/ozon-1688-uploader/SKILL.md) | 将1688的商品铺货到俄罗斯电商平台Ozon（上架），通过Ozon官方API实现商品信息的上传和状态查询。适用于需要将单个1688的商品上架到Ozon的场景。触发词：上传到Ozo… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`ALPHASHOP_ACCESS_KEY`、`ALPHASHOP_SECRET_KEY`、`OZON_API_KEY` |
| [`shader-dev`](./skills/shader-dev/) | [shader-dev](./skills/shader-dev/SKILL.md) | 用途：Comprehensive GLSL shader techniques for creating stunning visual effects — ray marchi… | 无 |
| [`shopping-price-drop-coupon-scout`](./skills/shopping-price-drop-coupon-scout/) | [shopping-price-drop-coupon-scout](./skills/shopping-price-drop-coupon-scout/SKILL.md) | 监控用户指定商品的价格变动并汇总官方优惠券与促销信息，全程只读、不登录账号、不加购物车、不下单、不处理支付。当用户希望设置降价提醒、整理可用优惠券清单，或获取某商品/商家的促销汇… | 需要登录 / OAuth / 扫码授权 |
| [`songsee`](./skills/songsee/) | [songsee](./skills/songsee/SKILL.md) | 用途：Generate spectrograms and feature-panel visualizations from audio with the songsee CLI. | 无 |
| [`the-entrepreneurship-handbook`](./skills/the-entrepreneurship-handbook/) | [the-entrepreneurship-handbook](./skills/the-entrepreneurship-handbook/SKILL.md) | Q&A skill for entrepreneurs, managers, and business leaders. Triggers when users ask abou… | 无 |
| [`weather`](./skills/weather/) | [weather](./skills/weather/SKILL.md) | 用途：Get current weather and forecasts (no API key required). | 需要大模型 API Key（OpenAI/Anthropic 等） |

### 其他（1）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`open-novel-writing`](./skills/open-novel-writing/) | [open-novel-writing](./skills/open-novel-writing/SKILL.md) | \| | 无（可选 API/账号以增强能力） |

## 2. 连接器 `connectors/`

| 目录 | 用来做什么 | 前置条件 |
|------|------------|----------|
| [`agentkey`](./connectors/agentkey/) | AgentKey 是 AI 助手获取可信工具和实时数据的能力市场。支持网页搜索、URL抓取、新闻、社交媒体、股票市场价格、电商产品数据、企业/公司数据、天气、地图和地理位置、旅行… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`anydev`](./connectors/anydev/) | 云研发的Skill服务，为大模型赋予AnyDev环境的全生命周期管理能力：支持查询和智能推荐环境模板、一键创建云研发环境，能够远程执行命令、上传文件、自动化部署，也可以按需开启 … | 需要登录 / OAuth / 扫码授权 |
| [`awesun`](./connectors/awesun/) | 通过命令行管理远端设备，实时监测在线状态、秒级发起远程控制、快速传输文件及远程截屏。零部署、免更新，轻松实现智能批量运维。 | 需要登录 / OAuth / 扫码授权 |
| [`baidu-netdisk`](./connectors/baidu-netdisk/) | 百度网盘文件管理与智能检索。支持浏览、关键词和语义搜索、文件整理、分享链接、容量查询，以及保存文本内容或通过 URL 转存文件。触发关键词：百度网盘、网盘、baidu、netdi… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`bugly`](./connectors/bugly/) | 用途：View the product quality overview | 可能需要启用对应 MCP / 连接器 |
| [`bugly-token`](./connectors/bugly-token/) | 查看产品的质量概览 包括崩溃率 anr率 foom（oom）率 启动耗时 | 可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`BUGLY_ACCESS_TOKEN` |
| [`canva`](./connectors/canva/) | 无缝调用Canva可画的设计能力。一句话生成海报、演示文稿、小红书封面等设计，通过文字描述调整尺寸、填充品牌模板及检索已有内容 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`cloudbase`](./connectors/cloudbase/) | Use this skill when you develop, design, build, deploy, debug, migrate, or troubleshoot C… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`cnb-api`](./connectors/cnb-api/) | 用途：Manage CNB platform via CLI. | 无（可选 API/账号以增强能力） |
| [`cnb-woa`](./connectors/cnb-woa/) | CNB 平台交互命令，支持代码仓库、Issue、PR、CI、制品库读写等操作。 | 无（可选 API/账号以增强能力） |
| [`ctrip-wendao`](./connectors/ctrip-wendao/) | Trigger when user asks travel-related questions: hotel search, flight query, attraction r… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要按 token-schema 配置凭证；需要环境变量：`WENDAO_API_KEY` |
| [`dingtalk`](./connectors/dingtalk/) | 管理钉钉产品能力(AI表格/AI搜问/日历/通讯录/群聊与机器人/待办/审批/考勤/日志/DING消息/开放平台文档/钉钉文档/钉钉云盘/AI听记/邮箱/在线电子表格/知识库等)… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`edgeone-pages`](./connectors/edgeone-pages/) | 用途：edgeone-makers | 可能需要启用对应 MCP / 连接器 |
| [`fbs-connector`](./connectors/fbs-connector/) | 福帮手人机协同连接器：面向 WorkBuddy 的身份识别、场景包查询、首值与继续使用记录、乐包状态确认和超级合伙人交接。 | 可能需要启用对应 MCP / 连接器 |
| [`feishu`](./connectors/feishu/) | 连接器配置与技能 | 需要在 App 内完成 OAuth / 扫码或配置 Token |
| [`fyopen-lawsearch`](./connectors/fyopen-lawsearch/) | 用途：Support natural language to obtain accurate and currently effective regulatory provisi… | 可能需要启用对应 MCP / 连接器 |
| [`gildata`](./connectors/gildata/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`GILDATA_TOKEN` |
| [`github`](./connectors/github/) | 用途：Use github connector to access github MCP capabilities via github mcp server. | 可能需要启用对应 MCP / 连接器 |
| [`github-remote`](./connectors/github-remote/) | 用途：Use github-remote connector to access github-remote MCP capabilities via github-remote… | 可能需要启用对应 MCP / 连接器 |
| [`gmail`](./connectors/gmail/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器；需要环境变量：`EMAIL_PASSWORD` |
| [`gongfeng-woa`](./connectors/gongfeng-woa/) | 用途：MCP server for Gongfeng API, supporting repository management, file operations, and mo… | 可能需要启用对应 MCP / 连接器 |
| [`ima-mcp`](./connectors/ima-mcp/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器 |
| [`iwiki-woa`](./connectors/iwiki-woa/) | 用途：iWiki MCP service empowers LLMs with document creation and retrieval capabilities. Sup… | 可能需要启用对应 MCP / 连接器 |
| [`jinshuju`](./connectors/jinshuju/) | 金数据（Jinshuju，jinshuju.net）操作技能 —— 创建/复制/编辑表单与主题，增删改查与批量修改表单数据，上传图片附件，查询账户套餐与团队成员。触发词：金数据、… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`jira`](./connectors/jira/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器；需要环境变量：`ATLASSIAN_API_TOKEN`、`JIRA_API_TOKEN` |
| [`kdocs`](./connectors/kdocs/) | 操作金山文档（WPS 云文档 / Kdocs / 365.kdocs.cn / www.kdocs.cn）云文档的官方 Skill。核心能力覆盖云端新建、读取、编辑、搜索、分享、… | 可能需要启用对应 MCP / 连接器 |
| [`km`](./connectors/km/) | 用途：KM official MCP - discover the best of Tencent knowledge. | 可能需要启用对应 MCP / 连接器 |
| [`lexiang`](./connectors/lexiang/) | 乐享知识库 MCP 全功能 Skill。当用户提到「乐享」「知识库」「lexiang」，或提供 lexiangla.com 链接，或涉及知识库的搜索/写入/编辑/文件/配置等操作… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`lovrabet-cli`](./connectors/lovrabet-cli/) | 通过 Lovrabet Runtime CLI 访问已发布应用的数据集、运行态 API、SQL、BFF、文件、OCR、Artifact 和知识库能力。 | 需要登录 / OAuth / 扫码授权 |
| [`mastergo-vibe-mcp`](./connectors/mastergo-vibe-mcp/) | 用途：Connect to the MasterGo canvas to allow AI to design, modify, synchronize, and retriev… | 可能需要启用对应 MCP / 连接器 |
| [`neo-crm`](./connectors/neo-crm/) | 用自然语言查客户、推商机、盘线索、领公海、写跟进，一句话打通销售工作闭环。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`netease-mail`](./connectors/netease-mail/) | 通过 IMAP/SMTP 连接邮箱，支持收发邮件、搜索、附件下载。支持 163、126、yeah.net 等网易邮箱及其他标准 IMAP/SMTP 邮箱。触发关键词：邮件、邮箱、… | 需要登录 / OAuth / 扫码授权；需要按 token-schema 配置凭证 |
| [`notion`](./connectors/notion/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器 |
| [`patsnap-search`](./connectors/patsnap-search/) | 用途：Search Patsnap's global patent and literature databases with natural-language, semanti… | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`PATSNAP_API_KEY` |
| [`pkulaw`](./connectors/pkulaw/) | 用途：PKULaw — Semantic (natural language) + keyword (exact / fuzzy) dual-mode retrieval ove… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`qcc-company`](./connectors/qcc-company/) | 用途：Query and verify corporate registration information. Supports shareholder structure, a… | 可能需要启用对应 MCP / 连接器 |
| [`qingflow`](./connectors/qingflow/) | 用途：QingFlow no-code platform connector for building apps, managing records, and automatin… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`QINGFLOW_TOKEN` |
| [`qixinhuiyan-mcp`](./connectors/qixinhuiyan-mcp/) | 启信慧眼企业信息查询工具 | 可能需要启用对应 MCP / 连接器 |
| [`qq-mail`](./connectors/qq-mail/) | QQ邮箱(QQ Mail)全功能操作技能。触发场景：看邮箱、查邮件、收件箱、看看邮件、有没有新邮件、未读邮件、帮我看看邮箱、打开邮箱、最近的邮件、邮件列表、发邮件、写邮件、发一封… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`region-insight`](./connectors/region-insight/) | 用途：Search POIs and analyze fenced-area distributions in specified areas. | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`REGION_INSIGHT_API_KEY` |
| [`shanlong-claw`](./connectors/shanlong-claw/) | 商龙餐饮经营数据分析连接器，通过 StarRocks 数据仓库查询门店画像、营收客流、优惠结算、菜品套餐、渠道来源、员工绩效、运营效率、会员分析、供应链等多维经营数据 | 需要在 App 内完成 OAuth / 扫码或配置 Token |
| [`supabase`](./connectors/supabase/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器 |
| [`tapd`](./connectors/tapd/) | 管理需求、缺陷、任务和迭代。查询项目进度、拆分需求、流转状态、填写工时，覆盖研发全生命周期。 | 可能需要启用对应 MCP / 连接器 |
| [`tapd-woa`](./connectors/tapd-woa/) | 用途：TAPD MCP tool operates various resources in TAPD via MCP protocol, including stories, … | 可能需要启用对应 MCP / 连接器 |
| [`tc-chengxin`](./connectors/tc-chengxin/) | 同程程心可通过自然语言查询机票、火车票、酒店、景点、度假产品等旅行资源，支持火空联程、智能交通推荐、特价机票搜索、景区门票预订，以及完整行程规划，显著提升出行效率。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`CHENGXIN_API_KEY` |
| [`tdx-connector`](./connectors/tdx-connector/) | 用途：Query global stock data via Tongdaxin MCP, with screening and research support. | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要环境变量：`TDX_API_KEY` |
| [`tec-do`](./connectors/tec-do/) | 面向出海广告投放和增长团队的 AI 能力集合。 | 可能需要启用对应 MCP / 连接器 |
| [`tencent-docs`](./connectors/tencent-docs/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器 |
| [`tencent-docs-oa`](./connectors/tencent-docs-oa/) | 连接器配置与技能 | 可能需要启用对应 MCP / 连接器 |
| [`tencent-health-nges`](./connectors/tencent-health-nges/) | 腾讯健康NGES MCP服务，支持智能问数和合规审核等功能 | 可能需要启用对应 MCP / 连接器 |
| [`tencent-map`](./connectors/tencent-map/) | 用途：Access Tencent Map location services via MCP | 可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`TENCENT_MAP_KEY` |
| [`tencent-qidian-cs`](./connectors/tencent-qidian-cs/) | 腾讯企点客服连接器：用自然语言处理工单（查询/创建/更新/状态变更）、查询坐席在线与实时接待、检索/拉取客户资料、拉取人工/大模型/文本机器人的会话记录和消息、查看客服实时监控、… | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`tencent-survey`](./connectors/tencent-survey/) | 腾讯问卷（wj.qq.com）MCP Skill。涉及「问卷」「调查」「表单」「投票」「考试」「测评」「wj.qq.com」等操作时使用。支持能力：(1) 获取问卷详情（标题、设… | 可能需要启用对应 MCP / 连接器 |
| [`tencent-weiyun`](./connectors/tencent-weiyun/) | 微云网盘 MCP 接口完整技能。包含 weiyun.list、weiyun.list_by_category、weiyun.download、weiyun.delete、weiy… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`WEIYUN_MCP_TOKEN` |
| [`tencentads`](./connectors/tencentads/) | 连接器配置与技能 | 需要在 App 内完成 OAuth / 扫码或配置 Token |
| [`tmeet`](./connectors/tmeet/) | 腾讯会议 CLI（tmeet）：OAuth 授权登录/登出/状态查询、会议管理（创建/更新/取消/查询/受邀者）、录制管理（列表/下载地址/智能纪要/转写/录制权限申请）、会议报… | 需要登录 / OAuth / 扫码授权 |
| [`tongzhou-fin-research`](./connectors/tongzhou-fin-research/) | 连接公开行情、研报检索、行业图谱与同舟投研材料，支持批量查询与事件窗口分析，为股市研究提供可复核证据。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`tyc-mcp`](./connectors/tyc-mcp/) | 用途：Query comprehensive enterprise data via Tianyancha MCP. Supports company registration … | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`TIANYANCHA_API_KEY` |
| [`wecom`](./connectors/wecom/) | 连接器配置与技能 | 需要在 App 内完成 OAuth / 扫码或配置 Token |
| [`weisheng-scrm`](./connectors/weisheng-scrm/) | 当用户需要查询或管理微盛企微管家（企业微信） SCRM 中的客户信息、客户标签、客户群、营销素材、活码、群发、跟进记录、聊天记录、会话存档、联系人、商机、汇报、抽奖、客户日程、客… | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`SCRM_APP_KEY` |
| [`westock-mcp`](./connectors/westock-mcp/) | 提供实时行情，支持条件选股、自选管理、股价提醒与模拟交易。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`wk-workbuddy`](./connectors/wk-workbuddy/) | 用途：Built on Wolters Kluwer China's authoritative and real-time legal database, MCP servic… | 可能需要启用对应 MCP / 连接器 |
| [`xiaoe-cloud-cli`](./connectors/xiaoe-cloud-cli/) | 用途：Manage your Xiaoe shop with natural language: query courses and students, create or up… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`yingmi-mcp`](./connectors/yingmi-mcp/) | 查询基金与市场数据，完成基金研究、组合分析、财富规划及金融内容生成。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`YINGMI_API_KEY` |
| [`yuandian-mcp`](./connectors/yuandian-mcp/) | 用途：Huayu Yuandian Legal Data provides agents with MCP tool capabilities for laws and regu… | 可能需要启用对应 MCP / 连接器 |
| [`yzf-invoice-mcp-server`](./connectors/yzf-invoice-mcp-server/) | 用途：Use Yunzhangfang AI invoicing services to extract billing information, match tax class… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`zfs-fssc-ai`](./connectors/zfs-fssc-ai/) | 用途：AI reimbursement assistant for ZTE FSSC: reimburse, query invoices and expense bills v… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要按 token-schema 配置凭证；需要环境变量：`ZFS_LOGIN_KEY`、`ZFS_PASSWORD` |
| [`zhiyan-cicd`](./connectors/zhiyan-cicd/) | 用途：ZhiYan CI/CD official MCP, supporting TKE container deployment, pipeline execution rec… | 可能需要启用对应 MCP / 连接器 |
| [`zsxq`](./connectors/zsxq/) | Zsxq (知识星球) knowledge community CLI — browse, post, comment, search, and manage notes. | 需要在 App 内完成 OAuth / 扫码或配置 Token |

## 3. 专家包 `experts/`

### 产品设计（18）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`adort-design-expert`](./experts/adort-design-expert/) | [Ardot 设计专家](./experts/adort-design-expert/) | 精通 Ardot 设计软件，既能在画布上构建精准 UI，也能将设计稿直接生成前端代码 | 可能需要启用对应 MCP / 连接器 |
| [`ai-image-prompt-engineer`](./experts/ai-image-prompt-engineer/) | [AI图像提示词工程师](./experts/ai-image-prompt-engineer/) | 精通AI图像生成的语言密码，将抽象视觉概念转化为精准提示词 | 无（可选 API/账号以增强能力） |
| [`behavioral-nudge-engine`](./experts/behavioral-nudge-engine/) | [行为助推引擎](./experts/behavioral-nudge-engine/) | 运用行为经济学设计产品助推机制，引导用户做出更好的决策 | 需要微信/企微相关凭证或扫码登录 |
| [`delightful-experience-designer`](./experts/delightful-experience-designer/) | [趣味体验设计师](./experts/delightful-experience-designer/) | 专注于在品牌体验中注入意想不到的愉悦时刻 | 无（可选 API/账号以增强能力） |
| [`design-engine`](./experts/design-engine/) | [设计原型专家团](./experts/design-engine/) | 6 角色 AI 设计团队，覆盖从需求发现到品牌级原型交付的完整工作流，内置 71 套设计系统 | 无（可选 API/账号以增强能力） |
| [`design-md-architect`](./experts/design-md-architect/) | [设计系统架构师](./experts/design-md-architect/) | 基于58个品牌参考库，生成设计系统规范文档并直接输出高质量HTML/CSS页面与UI组件代码 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`design-prototype-expert`](./experts/design-prototype-expert/) | [设计工作室主理人](./experts/design-prototype-expert/) | 设计系统驱动的高保真原型专家。先建规范再出页面，提供多方向选择，交付前做AI味检测。 | 无（可选 API/账号以增强能力） |
| [`design-to-code`](./experts/design-to-code/) | [设计转代码专家](./experts/design-to-code/) | 将 Figma 设计稿和截图转换为可直接使用的代码组件，内置无障碍性支持 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`diversity-visual-expert`](./experts/diversity-visual-expert/) | [多元视觉专家](./experts/diversity-visual-expert/) | 致力于消除AI图像中的系统性偏见，确保视觉内容文化准确和包容 | 无 |
| [`feedback-synthesis-analyst`](./experts/feedback-synthesis-analyst/) | [反馈综合分析师](./experts/feedback-synthesis-analyst/) | 从海量用户反馈中提炼有价值洞察，将用户声音转化为改进方向 | 需要微信/企微相关凭证或扫码登录 |
| [`mermaid-diagram-expert`](./experts/mermaid-diagram-expert/) | [图表设计与渲染专家](./experts/mermaid-diagram-expert/) | 将自然语言转化为专业级Mermaid图表，支持6种图表类型、15种主题配色，秒级渲染出版级SVG与ASCII可视化 | 需要登录 / OAuth / 扫码授权 |
| [`product-management`](./experts/product-management/) | [产品管理专家](./experts/product-management/) | 产品管理工具集：功能规格编写、路线图规划、利益相关者沟通、用户研究综合、竞品分析和指标追踪 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`product-strategy-team`](./experts/product-strategy-team/) | [产品战略团队](./experts/product-strategy-team/) | 由产品总监领导的 5 人产品专家团队：需求分析师（PRD/功能规格书）、用户研究员（调研综合分析）、竞品分析师（竞争情报）、数据分析师（指标追踪）和路线图规划师（路线图管理/迭代… | 无 |
| [`sprint-priority-manager`](./experts/sprint-priority-manager/) | [迭代优先级管理者](./experts/sprint-priority-manager/) | 在有限迭代周期内做出最优优先级决策，确保Sprint交付最大价值 | 无（可选 API/账号以增强能力） |
| [`ui-designer`](./experts/ui-designer/) | [UI设计师](./experts/ui-designer/) | 精通设计系统和组件库，追求像素级完美，打造无障碍用户界面 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`user-experience-architect`](./experts/user-experience-architect/) | [用户体验架构师](./experts/user-experience-architect/) | 为开发者提供坚实的技术基础和CSS系统，是设计与开发之间的桥梁 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`user-experience-researcher`](./experts/user-experience-researcher/) | [用户体验研究员](./experts/user-experience-researcher/) | 用真实数据而非假设验证设计决策，专精用户行为分析和可用性测试 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`visual-storytelling-expert`](./experts/visual-storytelling-expert/) | [视觉叙事专家](./experts/visual-storytelling-expert/) | 擅长将复杂信息转化为引人入胜的视觉故事 | 需要大模型 API Key（OpenAI/Anthropic 等） |

### 全球发展（21）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`brazil-company-query`](./experts/brazil-company-query/) | [巴西商务拓展专家](./experts/brazil-company-query/) | 排查巴西企业工商与信用风险，尽调专利商标知识产权，分析市场拓展路径，降低商务拓展风险。 | 无（可选 API/账号以增强能力） |
| [`brazil-legal`](./experts/brazil-legal/) | [巴西法务合规专家](./experts/brazil-legal/) | 巴西公司注册、合同审查、知识产权、产品准入、劳动用工、数据合规及争议解决，助力企业合规出海巴西。 | 无 |
| [`brazil-rfb-expert`](./experts/brazil-rfb-expert/) | [巴西财税金融专家](./experts/brazil-rfb-expert/) | 服务企业出海巴西的财税全周期：本地补贴、税制设计、跨境资金规划与日常合规，内置完整财税政策。 | 无 |
| [`egypt-marketing`](./experts/egypt-marketing/) | [埃及市场营销专家](./experts/egypt-marketing/) | 中国企业出海埃及的CMO级营销引擎，覆盖数字生态、斋月营销、品牌本地化、消费者洞察与ROI预估全链路 | 需要微信/企微相关凭证或扫码登录 |
| [`egypt-public-affairs`](./experts/egypt-public-affairs/) | [埃及公共事务专家](./experts/egypt-public-affairs/) | 精通埃及政府关系、政策解读、监管沟通、行业协会、危机公关和舆情管理，服务企业一站式公共事务咨询。 | 需要登录 / OAuth / 扫码授权 |
| [`egypt-strategic-advisory`](./experts/egypt-strategic-advisory/) | [埃及战略顾问](./experts/egypt-strategic-advisory/) | 精通埃及宏观环境、产业趋势、竞争格局和风险管控，提供投资选址、进入模式和长期布局决策建议。 | 无 |
| [`indonesia-bd-expert`](./experts/indonesia-bd-expert/) | [印尼商务拓展专家](./experts/indonesia-bd-expert/) | 整合全链路客供与渠道资源，洞察园区展会招商契机，锚定市场进入路径，打造产业合作生态与合规风控护航。 | 无 |
| [`indonesia-digital-law-expert`](./experts/indonesia-digital-law-expert/) | [印尼法务合规专家](./experts/indonesia-digital-law-expert/) | 聚焦外商投资、数据合规与商业交易，打通营商审批、金融监管与知识产权保护链路，赋能跨境SaaS与AI等新兴赛道全流程印尼法务保障。 | 可能需要启用对应 MCP / 连接器 |
| [`indonesia-pa-expert`](./experts/indonesia-pa-expert/) | [印尼公共事务专家](./experts/indonesia-pa-expert/) | 剖析印尼政商生态与合规风险，整合政策解读危机公关，融合本土宗教文化，输出落地GR策略。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`malaysia-finance-tax`](./experts/malaysia-finance-tax/) | [马来西亚财税金融专家](./experts/malaysia-finance-tax/) | 精通马来西亚税务、银行、外汇、审计、补贴、保险、伊斯兰金融及财政分析的财税金融全栈专家。 | 无（可选 API/账号以增强能力） |
| [`malaysia-hr-admin`](./experts/malaysia-hr-admin/) | [马来西亚人力行政专家](./experts/malaysia-hr-admin/) | 精通马来西亚招聘、劳动合同、薪酬福利、签证工签与社保，服务企业跨境人力行政咨询。 | 无 |
| [`malaysia-legal`](./experts/malaysia-legal/) | [马来西亚法务合规专家](./experts/malaysia-legal/) | 精通马来西亚公司注册、合同、知识产权、行业准入与数据合规，服务跨境法务合规咨询。 | 无（可选 API/账号以增强能力） |
| [`malaysia-marketing`](./experts/malaysia-marketing/) | [马来西亚市场营销专家](./experts/malaysia-marketing/) | 深谙马来西亚文化与宗教，覆盖消费者画像、品牌本地化、社媒投放与用户增长，生成营销海报与短视频。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`sg-biz-dev`](./experts/sg-biz-dev/) | [新加坡商务拓展专家](./experts/sg-biz-dev/) | 帮助企业在新加坡发现客户、伙伴、渠道、供应商与代理商，对接园区、展会、招商及确认市场进入路径 | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`sg-finance-tax`](./experts/sg-finance-tax/) | [新加坡财税金融专家](./experts/sg-finance-tax/) | 精通企业在新加坡经营中的税务、会计、银行、融资、外汇、支付、审计、补贴、保险和财务规划等内容 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`sg-hr-admin-expert`](./experts/sg-hr-admin-expert/) | [新加坡人力行政专家](./experts/sg-hr-admin-expert/) | 精通新加坡当地招聘、劳动合同、薪酬福利、签证工签、社保、办公场地、行政流程和员工管理等内容。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`thai-marketing-creative`](./experts/thai-marketing-creative/) | [泰国市场营销专家](./experts/thai-marketing-creative/) | 整合全链路用户洞察与行为决策，锚定本土松弛悦己情绪切口，打通泰语市场转化路径，输出泰国市场营销方案。 | 需要登录 / OAuth / 扫码授权 |
| [`thailand-hr-admin`](./experts/thailand-hr-admin/) | [泰国人力行政专家](./experts/thailand-hr-admin/) | 精通泰国劳动法(LPA)、外籍员工工签合规、薪酬福利设计与本土职场文化适配，护航中资企业出海泰国全周期人力行政 | 需要微信/企微相关凭证或扫码登录 |
| [`uae-marketing-advisor`](./experts/uae-marketing-advisor/) | [阿联酋市场营销专家](./experts/uae-marketing-advisor/) | 覆盖阿联酋不同地区差异化营销。覆盖消费者画像、品牌本土化、渠道策略与用户增长，生成营销海报视频。 | 需要环境变量：`COS_SECRET_KEY` |
| [`uae-public-affairs`](./experts/uae-public-affairs/) | [公共事务顾问](./experts/uae-public-affairs/) | 专注阿联酋政府关系、政策解读与监管沟通，为中企及投资机构提供专业公共事务咨询与风险评估服务。 | 无（可选 API/账号以增强能力） |
| [`uae-strategic-advisor`](./experts/uae-strategic-advisor/) | [阿联酋战略顾问](./experts/uae-strategic-advisor/) | 研判阿联酋七酋长国宏观环境与产业趋势，对比竞合格局与投资选址，评估进入模式与风险，输出出海战略建议 | 无 |

### 内容创作（43）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`ai-content-creator-team`](./experts/ai-content-creator-team/) | [内容创作专家团](./experts/ai-content-creator-team/) | AI驱动的多模态内容生产团队，从创意策划到成品交付全覆盖，涵盖品牌定位、情绪板、广告方向、文案创作、视频生成、图片设计、精修合成和素材改编。 | 需要微信/企微相关凭证或扫码登录 |
| [`ai-humanizer`](./experts/ai-humanizer/) | [AI痕迹消除专家](./experts/ai-humanizer/) | 识别24种AI写作模式与500+词汇，统计突发性与多样性，重写为自然真实的人类表达，彻底消除机器味。 | 无 |
| [`ai-shifu`](./experts/ai-shifu/) | [AI师傅课程制作专家](./experts/ai-shifu/) | 基于你的教学需求和原始内容(PPT、Word、PDF、txt等)，帮你快速做门AI一对一互动课 | 需要登录 / OAuth / 扫码授权 |
| [`ai-shifu-expert`](./experts/ai-shifu-expert/) | [AI师傅课程制作专家](./experts/ai-shifu-expert/) | 基于你的教学需求和原始内容(PPT、Word、PDF、txt等)，帮你快速做门AI一对一互动课 | 需要登录 / OAuth / 扫码授权 |
| [`ai-video-script`](./experts/ai-video-script/) | [AI视频脚本创作专家](./experts/ai-video-script/) | 依据主题或关键词生成完整视频脚本，涵盖分镜表、画面提示词、配音文案与字幕，适配主流AI生成工具及抖音、B站平台。 | 需要微信/企微相关凭证或扫码登录 |
| [`bilibili-content-strategist`](./experts/bilibili-content-strategist/) | [B站内容策略师](./experts/bilibili-content-strategist/) | 精通B站平台生态和年轻用户偏好，打造高播放量视频策略 | 需要微信/企微相关凭证或扫码登录 |
| [`book-co-creator`](./experts/book-co-creator/) | [图书联合创作者](./experts/book-co-creator/) | 与作者深度协作，帮助规划书籍结构和内容，达到出版级品质 | 需要微信/企微相关凭证或扫码登录 |
| [`chatcut-video-editor`](./experts/chatcut-video-editor/) | [ChatCut 视频剪辑师](./experts/chatcut-video-editor/) | AI 视频剪辑与素材生成：剪辑、字幕、转场、特效，并生成视频/图片/音乐/配音，保持可手动编辑的多轨时间线，支持导出 Pr / DaVinci 工程文件。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`content-creation-expert-prod`](./experts/content-creation-expert-prod/) | [汽车行业内容创作专家团](./experts/content-creation-expert-prod/) | 汽车行业垂类图文创作团队，5 人协作完成选题、撰写、智能配图与质检，一键交付懂车帝、小红书等风格图文 | 可能需要启用对应 MCP / 连接器；需要环境变量：`COS_SECRET_KEY` |
| [`content-creator`](./experts/content-creator/) | [内容创作专家](./experts/content-creator/) | 擅长创作引人入胜的多平台内容，让品牌故事触达目标受众 | 无（可选 API/账号以增强能力） |
| [`content-distribution-team`](./experts/content-distribution-team/) | [全域内容分发专家团](./experts/content-distribution-team/) | 一站式多平台内容分发方案，覆盖13+全球社交媒体平台（含微信视频号），提供发布规则适配、排期管理、批量发布编排、跨平台数据分析和小红书自动化发布能力 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`LIBTV_ACCESS_KEY`、`TOKEN`、`WECHAT_AUTHOR`、`WECHAT_SECRET` |
| [`content-writer`](./experts/content-writer/) | [自媒体内容写作专家](./experts/content-writer/) | 专注为小红书、知乎、公众号、抖音生成平台原生的可发布内容，含标题钩子、正文结构与转化引导，匹配各平台字数规范。 | 需要微信/企微相关凭证或扫码登录 |
| [`douyin-strategist`](./experts/douyin-strategist/) | [抖音策略师](./experts/douyin-strategist/) | 精通抖音算法和内容生态，打造短视频爆款并实现商业化变现 | 无（可选 API/账号以增强能力） |
| [`frontend-slides`](./experts/frontend-slides/) | [HTML幻灯片制作专家](./experts/frontend-slides/) | 零依赖打造动画丰富的网页演示文稿，支持从零创建、PPTX转换与幻灯片增强，提供风格预览、在线部署与PDF导出。 | 无（可选 API/账号以增强能力） |
| [`humanize-ppt-team`](./experts/humanize-ppt-team/) | [卡尔的人感PPT专家团](./experts/humanize-ppt-team/) | 把原始资料梳理成人感PPT大纲，调度HTML生成、演讲模式、视频动效与交付质检，形成可演示成果。 | 需要登录 / OAuth / 扫码授权 |
| [`instagram-operations-expert`](./experts/instagram-operations-expert/) | [Instagram运营专家](./experts/instagram-operations-expert/) | 精通Instagram视觉美学和内容策略，打造令人向往的品牌形象 | 需要 GitHub Token 或 `gh auth login` |
| [`kdocs-doc-butler`](./experts/kdocs-doc-butler/) | [文档管家](./experts/kdocs-doc-butler/) | 金山文档出品一站式管理金山文档全生命周期：新建各类在线文档、按关键词快速搜索定位、AI 按主题自动分类整理文件夹、批量移动重命名、生成分享链接与权限管理、读取文档内容输出为 Ma… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`kdocs-knowledge-collector`](./experts/kdocs-knowledge-collector/) | [知识收藏专家](./experts/kdocs-knowledge-collector/) | 金山文档出品把网页、消息、笔记等碎片内容沉淀为结构化知识资产：一键剪藏公众号与网页为云文档，AI 按主题聚合零散笔记生成整理稿，多份文档自动提炼摘要与要点，一键归档到个人知识库并… | 无 |
| [`kdocs-pdf-toolbox`](./experts/kdocs-pdf-toolbox/) | [PDF 处理专家](./experts/kdocs-pdf-toolbox/) | 金山文档出品PDF 文档处理一站式：按页拆分、多文件合并、提取指定页、转换为 Word/Excel/PPT、全文翻译导出（双语/指定语言）、内容读取与页数查询。适用于合同拆分、报… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`kdocs-ppt-creator`](./experts/kdocs-ppt-creator/) | [AIPPT专家](./experts/kdocs-ppt-creator/) | WPS官方出品一句话主题或一份参考文档，AI 自动设计大纲并生成包含标题页、内容页、总结页的完整 PPT，并按场景统一配色与排版。覆盖工作汇报、项目展示、培训课件、方案演示等高频… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`kidd-content-expert`](./experts/kidd-content-expert/) | [知识视频创作专家](./experts/kidd-content-expert/) | 基于深度研究报告，用基德风格创作口语化、反常识的知识视频脚本，覆盖时政财经、宇宙科普与科技前沿。 | 无 |
| [`kuaishou-strategist`](./experts/kuaishou-strategist/) | [快手策略师](./experts/kuaishou-strategist/) | 深谙快手下沉市场特性和老铁文化，打造接地气的内容策略 | 无 |
| [`long-manuscript-expert`](./experts/long-manuscript-expert/) | [长文档写作与改稿专家](./experts/long-manuscript-expert/) | 把提纲、访谈、旧稿和零散素材整理成结构清晰的长文档，支持章节续写、限定范围改稿与成稿交付前检查。 | 需要登录 / OAuth / 扫码授权 |
| [`news-buddy`](./experts/news-buddy/) | [资讯顾问](./experts/news-buddy/) | 懂你的资讯顾问。基于隐式画像精选新闻，告诉你每条跟你有什么关系、你能做什么，让信息真正为你所用。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`novel-generator`](./experts/novel-generator/) | [爽文小说生成专家](./experts/novel-generator/) | 把一句话灵感扩写成完整提示词与大纲，逐章生成连贯爽文，维护角色、地点、情节一致，支持修仙、重生、都市等题材。 | 无 |
| [`podcast-strategist`](./experts/podcast-strategist/) | [播客策略师](./experts/podcast-strategist/) | 精通播客内容策划和增长策略，通过音频建立深度用户连接 | 需要微信/企微相关凭证或扫码登录 |
| [`ppt-implement`](./experts/ppt-implement/) | [PPT制作专家](./experts/ppt-implement/) | 智能 PPT 生成助手，一键将想法转化为精美演示文稿 | 无 |
| [`promo-creator-team`](./experts/promo-creator-team/) | [宣传片创作团队](./experts/promo-creator-team/) | 6位专业角色分6阶段协作完成产品宣传片全流程制作：创意简报、逐镜头分镜、素材生产、HyperFrames剪辑合成、BGM设计与交付，从产品URL到可发布的60-90秒宣传片MP4 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`MUREKA_API_KEY` |
| [`remotion-video-generator`](./experts/remotion-video-generator/) | [视频生成专家](./experts/remotion-video-generator/) | 基于 Remotion 的视频生成专家，创建产品演示、解说视频、社交媒体内容和演示文稿 | 可能需要启用对应 MCP / 连接器 |
| [`short-video-editing-coach`](./experts/short-video-editing-coach/) | [短视频剪辑教练](./experts/short-video-editing-coach/) | 精通短视频剪辑技巧和节奏把控，让每条视频具有专业冲击力 | 无（可选 API/账号以增强能力） |
| [`tik-tok-strategist`](./experts/tik-tok-strategist/) | [TikTok策略师](./experts/tik-tok-strategist/) | 精通TikTok算法和海外短视频生态，帮助品牌在全球平台爆发 | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`LIBTV_ACCESS_KEY` |
| [`topic-evaluator`](./experts/topic-evaluator/) | [科技频道选题评估师](./experts/topic-evaluator/) | 双层级4维评分与5方向对比，全部评分详情、硬源清单、风险提示在对话中完整展示，报告可下载存档。 | 无 |
| [`twitter-operations-expert`](./experts/twitter-operations-expert/) | [Twitter运营专家](./experts/twitter-operations-expert/) | 精通Twitter/X平台互动策略和话题运营，让品牌占据全球对话 | 需要 GitHub Token 或 `gh auth login` |
| [`vibeknow-design-video`](./experts/vibeknow-design-video/) | [VibeKnow 视频专家](./experts/vibeknow-design-video/) | 给个文件或一篇文章，自动排版式、配图、配音，编排成一条动效流畅、有设计感的图文短视频。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`vibeknow-handdraw`](./experts/vibeknow-handdraw/) | [VibeKnow 手绘视频专家](./experts/vibeknow-handdraw/) | 老师讲历史、家长讲绘本、医生讲康复、理财博主讲避坑，专业内容边画边讲成手绘科普视频，51种风格随选。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`WB_TOKEN` |
| [`vibeknow-ppt-explain`](./experts/vibeknow-ppt-explain/) | [VibeKnow PPT/PDF讲解大师](./experts/vibeknow-ppt-explain/) | 讲师做培训、医生讲科普、分析师讲研报、企业讲方案，PPT/PDF 逐页配音，一键成讲解视频。 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`video-dissection`](./experts/video-dissection/) | [视频解剖专家团](./experts/video-dissection/) | 专业拆解火爆抖音视频拍摄手法的专家团。输入抖音链接，自动提取视频、转录文案、分析景别运镜、剪辑节奏、色调风格，生成完整拍摄脚本拆解文档，并提供可落地的仿拍建议。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`API_KEY`、`ARK_API_KEY`、`DOUYIN_API_KEY`、`SILICONFLOW_API_KEY` |
| [`video-gen-team`](./experts/video-gen-team/) | [AI视频创作团队](./experts/video-gen-team/) | 三位一体的AI视频创作团队：灵阅负责采集AI/科技热点，灵枢负责策划选题与脚本，灵映负责渲染MP4视频成品（配音+字幕）。全流程自动化，60秒短视频一键生成。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要环境变量：`AZURE_TTS_KEY` |
| [`viral-topic-master`](./experts/viral-topic-master/) | [爆款选题策划专家](./experts/viral-topic-master/) | 投热点出爆款。12 心法预筛+8 维打分+6 大形态产出，公众号视频号小红书 H5 通吃。 | 需要微信/企微相关凭证或扫码登录 |
| [`wechat-official-account-expert`](./experts/wechat-official-account-expert/) | [微信公众号运营专家](./experts/wechat-official-account-expert/) | 精通公众号内容策略和粉丝增长，打造10万+品牌自媒体矩阵 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TOKEN`、`WECHAT_AUTHOR`、`WECHAT_SECRET` |
| [`weibo-strategist`](./experts/weibo-strategist/) | [微博策略师](./experts/weibo-strategist/) | 精通微博话题营销和舆论传播规律，让品牌在热搜持续出圈 | 无 |
| [`xiaohongshu-operations-expert`](./experts/xiaohongshu-operations-expert/) | [小红书运营专家](./experts/xiaohongshu-operations-expert/) | 深谙小红书种草生态和推荐机制，打造高互动率种草内容 | 需要 GitHub Token 或 `gh auth login`；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`zhihu-strategist`](./experts/zhihu-strategist/) | [知乎策略师](./experts/zhihu-strategist/) | 精通知乎推荐机制和知识营销策略，通过高质量回答建立权威 | 需要 GitHub Token 或 `gh auth login` |

### 技术工程（39）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`api-dev`](./experts/api-dev/) | [API开发专家](./experts/api-dev/) | 专注接口全生命周期开发，涵盖端点搭建、自动化测试、OpenAPI文档生成、Mock服务搭建与HTTP请求问题调试，提升开发效率。 | 无 |
| [`backend-architect`](./experts/backend-architect/) | [后端架构师](./experts/backend-architect/) | 深耕分布式系统和高并发架构，擅长将复杂业务转化为优雅技术方案 | 需要登录 / OAuth / 扫码授权 |
| [`code`](./experts/code/) | [代码开发流程专家](./experts/code/) | 提供规划执行验证测试全流程编码指导，将复杂需求拆解为可独立验证步骤，支持多任务跟踪与偏好记忆。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`code-review-expert`](./experts/code-review-expert/) | [代码审查专家](./experts/code-review-expert/) | 以鹰眼标准检查每行代码，在缺陷到达生产环境之前将其拦截 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 GitHub Token 或 `gh auth login`；需要登录 / OAuth / 扫码授权；需要环境变量：`GH_TOKEN`、`GITHUB_TOKEN` |
| [`database-operations`](./experts/database-operations/) | [数据库设计调优专家](./experts/database-operations/) | 精通表结构设计、迁移与性能调优。先用执行计划分析慢查询，再构建复合索引、修复N+1问题、实施分区与缓存优化。 | 无 |
| [`dev-ops-automation-engineer`](./experts/dev-ops-automation-engineer/) | [DevOps自动化工程师](./experts/dev-ops-automation-engineer/) | 将一切手动运维自动化，从CI/CD到基础设施即代码，部署一键搞定 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`IMA_OPENAPI_APIKEY` |
| [`dev-pipeline-orchestrator`](./experts/dev-pipeline-orchestrator/) | [开发流水线编排专家](./experts/dev-pipeline-orchestrator/) | 编排开发流水线：澄清需求意图，拆解为测试驱动的细粒度任务，子代理逐任务实现并双重评审，最终集成分支。 | 无 |
| [`dockerfile-gen`](./experts/dockerfile-gen/) | [Dockerfile生成专家](./experts/dockerfile-gen/) | Dockerfile 自动生成专家，遵循容器化最佳实践 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`embedded-firmware-engineer`](./experts/embedded-firmware-engineer/) | [嵌入式固件工程师](./experts/embedded-firmware-engineer/) | 精通微控制器编程，在资源受限的硬件上编写高效可靠的固件代码 | 无 |
| [`engineering-assurance-team`](./experts/engineering-assurance-team/) | [工程保障团队](./experts/engineering-assurance-team/) | 由工程总监领导的 5 人工程专家团队：代码审查师（安全/性能/正确性）、架构师（系统设计/ADR）、SRE 工程师（事故响应/部署）、测试专家（测试策略/覆盖率）和技术文档师（文… | 无（可选 API/账号以增强能力） |
| [`engineering-workflow-skills`](./experts/engineering-workflow-skills/) | [工程实践专家](./experts/engineering-workflow-skills/) | 基于Google 工程师的《Agent Skills》打造的资深工程全流程教练：规约驱动、测试驱动、代码评审、CI/CD发布 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`eno`](./experts/eno/) | [前端架构分析专家](./experts/eno/) | 深度分析前端项目架构、技术栈选型、组件设计与构建配置，输出含评分等级、优势短板和重构优先级的结构化评审报告。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`frontend`](./experts/frontend/) | [前端界面开发专家](./experts/frontend/) | 精通响应式界面开发，遵循移动优先与可访问性，以鲜明排版与色彩构建落地页、仪表盘、表单等高保真界面。 | 无（可选 API/账号以增强能力） |
| [`frontend-developer`](./experts/frontend-developer/) | [前端开发工程师](./experts/frontend-developer/) | 精通现代Web技术和主流框架，以像素级精度构建响应式高性能Web应用 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`git-workflow-expert`](./experts/git-workflow-expert/) | [Git工作流专家](./experts/git-workflow-expert/) | 精通Git高级工作流和分支策略，让团队协作像行云流水般顺畅 | 需要 GitHub Token 或 `gh auth login`；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`GH_TOKEN`、`GITHUB_TOKEN` |
| [`gstack`](./experts/gstack/) | [软件工坊](./experts/gstack/) | 6位工程专业角色：产品评审、代码审查、安全审计、QA测试、设计系统、调试运维，覆盖从想法到生产的完整软件生命周期 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`hsk-devops-expert`](./experts/hsk-devops-expert/) | [网页发布与前端调试专家](./experts/hsk-devops-expert/) | 基于 HSK CLI 的 DevOps 专家，提供零配置公网预览、内网穿透、文件托管和项目部署能力 | 无 |
| [`incident-response-commander`](./experts/incident-response-commander/) | [事故响应指挥官](./experts/incident-response-commander/) | 系统故障时冷静指挥团队快速定位处理和恢复，是终极救火队长 | 无（可选 API/账号以增强能力） |
| [`infrastructure-operations-expert`](./experts/infrastructure-operations-expert/) | [基础设施运维专家](./experts/infrastructure-operations-expert/) | 确保IT基础设施的持续稳定运行，一切尽在掌控 | 无 |
| [`lsp-index-engineer`](./experts/lsp-index-engineer/) | [LSP索引工程师](./experts/lsp-index-engineer/) | 精通语言服务器协议和代码索引技术 | 无 |
| [`mcp-build-expert`](./experts/mcp-build-expert/) | [MCP构建专家](./experts/mcp-build-expert/) | 精通Model Context Protocol设计实现 | 可能需要启用对应 MCP / 连接器 |
| [`mobile-application-developer`](./experts/mobile-application-developer/) | [移动应用开发工程师](./experts/mobile-application-developer/) | 精通iOS和Android原生及跨平台开发，打造流畅美观的移动应用 | 无（可选 API/账号以增强能力） |
| [`modern-webapp`](./experts/modern-webapp/) | [现代Web开发专家](./experts/modern-webapp/) | 现代 Web 应用开发专家，基于 React + TypeScript + Vite + Tailwind CSS + shadcn/ui 技术栈，含浏览器自动化能力 | 需要登录 / OAuth / 扫码授权 |
| [`mvp-dev-expert-team`](./experts/mvp-dev-expert-team/) | [MVP开发专家团](./experts/mvp-dev-expert-team/) | 说出你的想法，8位专家从调研、设计、编码、测试到部署全流程协作，帮你快速开发MVP产品 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`COS_SECRET_KEY`、`JWT_SECRET`、`MOCK_JWT_TOKEN`、`RESEND_API_KEY`、`SESSION_SECRET`、`STRIPE_SECRET_KEY` |
| [`ncre-expert`](./experts/ncre-expert/) | [计算机等级考试专家团](./experts/ncre-expert/) | NCRE一至四级专家团，覆盖Office、编程、数据库与网络安全，分工协作，量身定制备考方案。 | 无 |
| [`omics-hpc-expert`](./experts/omics-hpc-expert/) | [腾讯组学HPC集群运维与作业管理专家](./experts/omics-hpc-expert/) | 组学HPC一站式运维，管控节点、队列与存储全生命周期，适配SLURM/SGE调度，自然语言降低门槛 | 需要登录 / OAuth / 扫码授权 |
| [`rapid-prototyping-engineer`](./experts/rapid-prototyping-engineer/) | [快速原型工程师](./experts/rapid-prototyping-engineer/) | 以极快速度将创意转化为可工作的原型，让团队快速验证想法 | 需要登录 / OAuth / 扫码授权 |
| [`rum-fullstack-team`](./experts/rum-fullstack-team/) | [腾讯云 RUM 全链路专家团](./experts/rum-fullstack-team/) | 腾讯云 RUM 全链路服务：10 大平台 aegis SDK 接入 + WebVitals/异常/接口/资源分析，支持 RUM-APM 联动 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`RUM_TOKEN` |
| [`security-engineer`](./experts/security-engineer/) | [安全工程师](./experts/security-engineer/) | 全方位保障系统安全，在黑客之前发现并修复安全漏洞 | 需要 GitHub Token 或 `gh auth login`；需要登录 / OAuth / 扫码授权；需要环境变量：`GITHUB_TOKEN` |
| [`senior-developer`](./experts/senior-developer/) | [高级开发工程师](./experts/senior-developer/) | 10年以上全栈经验，精通多种语言和框架，是团队的技术中坚 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 GitHub Token 或 `gh auth login`；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY`、`GH_TOKEN`、`GITHUB_TOKEN` |
| [`site-reliability-engineer`](./experts/site-reliability-engineer/) | [站点可靠性工程师](./experts/site-reliability-engineer/) | 用软件工程方法论解决运维问题，确保99.99%可用性 | 无 |
| [`software-architect`](./experts/software-architect/) | [软件架构师](./experts/software-architect/) | 站在全局高度设计可扩展高可用的软件架构，为技术团队指明方向 | 需要登录 / OAuth / 扫码授权 |
| [`software-company`](./experts/software-company/) | [软件开发团队](./experts/software-company/) | 高效软件研发团队，产品经理定需求、架构师设计+拆任务、工程师批量实现代码、QA验证质量，小需求支持快速模式 | 无（可选 API/账号以增强能力） |
| [`solidity-smart-contract-engineer`](./experts/solidity-smart-contract-engineer/) | [Solidity智能合约工程师](./experts/solidity-smart-contract-engineer/) | 精通Solidity和EVM生态，编写安全高效的智能合约 | 无 |
| [`superpowers-zh`](./experts/superpowers-zh/) | [AI编程方法论与中文开发规范专家](./experts/superpowers-zh/) | 二十项AI编程方法论，覆盖头脑风暴、测试驱动开发、系统化调试、代码审查，适配中文文档与国内平台规范。 | 可能需要启用对应 MCP / 连接器 |
| [`tencentcloud-api`](./experts/tencentcloud-api/) | [腾讯云API专家](./experts/tencentcloud-api/) | 自然语言管理腾讯云200+产品资源，智能检索API并构造CLI命令，内置安全管控与异常处理 | 需要登录 / OAuth / 扫码授权 |
| [`terminal-integration-expert`](./experts/terminal-integration-expert/) | [终端集成专家](./experts/terminal-integration-expert/) | 精通终端应用与空间计算环境的集成 | 无 |
| [`threat-detection-engineer`](./experts/threat-detection-engineer/) | [威胁检测工程师](./experts/threat-detection-engineer/) | 专精构建威胁检测系统，在攻击者造成损害前发现拦截威胁 | 无 |
| [`we-chat-mini-program-developer`](./experts/we-chat-mini-program-developer/) | [微信小程序开发者](./experts/we-chat-mini-program-developer/) | 精通微信小程序开发框架和生态，打造流畅微信原生体验应用 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |

### 数据智能（34）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`academic-journal-selector`](./experts/academic-journal-selector/) | [学术选刊顾问团 v3.1](./experts/academic-journal-selector/) | 万方数据旗下学术选刊专家团，中英双管道并行检索，覆盖中英文核心期刊，输出冲-稳-保分层投稿方案。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`ai-data-copilot`](./experts/ai-data-copilot/) | [智数分析专家团](./experts/ai-data-copilot/) | 6人AI数据分析团队，擅长自然语言转SQL、Python建模、RAG知识问答、仪表盘可视化与报告生成 | 无（可选 API/账号以增强能力） |
| [`ai-engineer`](./experts/ai-engineer/) | [AI工程师](./experts/ai-engineer/) | 精通ML模型开发部署优化的全栈AI工程师，将AI从论文带到生产环境 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`aihot`](./experts/aihot/) | [资讯速递专家](./experts/aihot/) | 一句话查到每天精选的 AI 模型/产品/行业/论文动态，自动整理成中文简报，免配置免登录。 | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`arxiv-watcher`](./experts/arxiv-watcher/) | [ArXiv论文追踪专家](./experts/arxiv-watcher/) | 检索ArXiv最新论文，支持按关键词、作者、学科精准搜索，自动提炼摘要要点并归档至研究日志，助您持续追踪前沿学术动态。 | 无 |
| [`autonomous-optimization-architect`](./experts/autonomous-optimization-architect/) | [自主优化架构师](./experts/autonomous-optimization-architect/) | 专精于设计能自主优化和进化的智能系统架构，让系统越用越聪明 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 GitHub Token 或 `gh auth login`；需要环境变量：`GH_TOKEN`、`GITHUB_TOKEN` |
| [`data`](./experts/data/) | [数据探索专家](./experts/data/) | 数据探索专家，支持 SQL 查询、数据探索、可视化、仪表板构建、数据验证和洞察生成 | 可能需要启用对应 MCP / 连接器；需要环境变量：`DISTKEY`、`SORTKEY` |
| [`data-analysis`](./experts/data-analysis/) | [数据分析专家](./experts/data-analysis/) | 数据分析专家，支持 Excel 电子表格的创建、编辑、分析、公式计算、格式化和数据可视化 | 需要微信/企微相关凭证或扫码登录 |
| [`data-analytics-reporter`](./experts/data-analytics-reporter/) | [数据分析报告师](./experts/data-analytics-reporter/) | 将复杂数据转化为战略洞察，提供指标诊断、KPI框架设计、数据质量评估与决策报告 | 无 |
| [`data-engineer`](./experts/data-engineer/) | [数据工程师](./experts/data-engineer/) | 构建高效可靠的数据管道和ETL流程，让数据从源头到洞察畅通无阻 | 无 |
| [`data-integration-agent`](./experts/data-integration-agent/) | [数据整合代理](./experts/data-integration-agent/) | 将分散数据清洗整合统一，构建企业统一数据视图 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`database-optimization-expert`](./experts/database-optimization-expert/) | [数据库优化专家](./experts/database-optimization-expert/) | 专精数据库性能调优和查询优化，让慢查询变快让瓶颈消失 | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GH_TOKEN`、`GITHUB_TOKEN`、`SUPABASE_ANON_KEY` |
| [`databrain-opinion-expert`](./experts/databrain-opinion-expert/) | [DataBrain舆情分析专家](./experts/databrain-opinion-expert/) | 玩家口碑与舆情侦察兵，覆盖评分告警、内容趋势、竞品对比与热点挖掘，实时感知玩家声音，辅助运营决策 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`DATABRAIN_TOKEN`、`TAI_IT_TOKEN` |
| [`deep-research`](./experts/deep-research/) | [深度研究专家](./experts/deep-research/) | 综合性深度研究专家，支持多源信息检索、事实验证、知识发现和结构化报告生成，含微信公众号文章搜索能力 | 需要微信/企微相关凭证或扫码登录 |
| [`finance-data`](./experts/finance-data/) | [金融数据检索专家](./experts/finance-data/) | 金融数据检索专家，通过自然语言查询 209 个金融数据 API，涵盖股票、指数、期货、债券、基金和宏观经济等 15 大类 | 无（可选 API/账号以增强能力） |
| [`fundus-disease-analysis`](./experts/fundus-disease-analysis/) | [眼科AI诊断专家](./experts/fundus-disease-analysis/) | 基于普角与超广角眼底彩照的AI多病种分析，覆盖青光眼、糖网、AMD等数十种疾病的诊断与报告解读。 | 需要环境变量：`FUNDUS_TOKEN` |
| [`gpt-researcher-team`](./experts/gpt-researcher-team/) | [深度研究团队](./experts/gpt-researcher-team/) | 深度研究报告输出，7角色5阶段聚合多源信息，经审稿修订循环输出带引用的专业报告 | 无（可选 API/账号以增强能力） |
| [`huashu-data-pro`](./experts/huashu-data-pro/) | [花叔数据分析专家团](./experts/huashu-data-pro/) | 「一人公司」本地数据分析专家团。一份 Excel 进，趋势 / 结构 / 异常三专家并行分析，交付网页、Excel、PPT 三格式报告，数据不出本地。 | 无 |
| [`jinshuju-expert`](./experts/jinshuju-expert/) | [金数据表单与数据管理专家](./experts/jinshuju-expert/) | 通过金数据 MCP 用自然语言搭建表单、增删改查与批量维护数据、查询套餐额度，替代登录后台手动操作 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`YOUR_API_KEY`、`YOUR_API_SECRET` |
| [`kdocs-data-table`](./experts/kdocs-data-table/) | [数据建表专家](./experts/kdocs-data-table/) | 金山文档出品将群聊接龙一键转为结构化表格，一句话生成可分享的信息收集表，智能美化表格并固化规则（条件格式高亮异常值、数据校验下拉约束、区域保护锁定表头）。擅长接龙识别、字段推断、… | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`llm-wiki`](./experts/llm-wiki/) | [知识管理专家](./experts/llm-wiki/) | 基于 Andrej Karpathy 的 LLM Wiki 模式，帮助用户构建、维护和查询持久化的个人知识库。擅长将原始资料（论文、文章、笔记等）编译为结构化 Markdown … | 无 |
| [`model-quality-assurance-expert`](./experts/model-quality-assurance-expert/) | [模型质量保障专家](./experts/model-quality-assurance-expert/) | 系统化评估保障AI模型质量，确保输出准确公平安全 | 无 |
| [`omics-bioinfo-expert`](./experts/omics-bioinfo-expert/) | [腾讯组学生信分析专家](./experts/omics-bioinfo-expert/) | 专攻生信分析，支持任务投递、进度追踪、日志解析、智能排错。内置自研模型库，加速生信研发与生产分析 | 需要登录 / OAuth / 扫码授权 |
| [`omics-cdgpt-expert`](./experts/omics-cdgpt-expert/) | [腾讯CD-GPT生物序列建模专家](./experts/omics-cdgpt-expert/) | 基于腾讯CD-GPT多模态大模型，覆盖DNA、RNA、蛋白质序列，支持翻译、反向翻译、生成与功能注释 | 需要登录 / OAuth / 扫码授权 |
| [`omics-diagnosis-expert`](./experts/omics-diagnosis-expert/) | [腾讯组学任务分析智能诊断专家](./experts/omics-diagnosis-expert/) | 生物信息分析智能诊断，解析任务日志、拆解错误堆栈、快速定位OOM、磁盘满载等故障根源，提升分析效率 | 需要登录 / OAuth / 扫码授权 |
| [`omics-iggm-expert`](./experts/omics-iggm-expert/) | [腾讯IgGM抗体药物研发专家](./experts/omics-iggm-expert/) | 精通腾讯IgGM生成式模型。覆盖CDR重设计、全链生成与人源化亲和力优化，输出可验证的抗体候选序列 | 需要登录 / OAuth / 扫码授权 |
| [`omics-ori-expert`](./experts/omics-ori-expert/) | [腾讯ORI蛋白设计专家](./experts/omics-ori-expert/) | 覆盖序列从头设计、USMFold结构预测及溶解性等评估，打通从设计到可生产蛋白的关键决策 | 需要登录 / OAuth / 扫码授权 |
| [`omics-scbert-expert`](./experts/omics-scbert-expert/) | [腾讯scBert单细胞预训练专家](./experts/omics-scbert-expert/) | 基于scBERT模型，实现细胞精细注释、新亚群挖掘及Marker筛选，助力肿瘤细胞研究 | 需要登录 / OAuth / 扫码授权 |
| [`omics-scprotein-expert`](./experts/omics-scprotein-expert/) | [腾讯scPROTEIN单细胞蛋白组建模专家](./experts/omics-scprotein-expert/) | scPROTEIN图神经网络模型，适配CITE-seq稀疏蛋白数据，实现降噪补全与不确定性预估 | 需要登录 / OAuth / 扫码授权 |
| [`omics-tfold-expert`](./experts/omics-tfold-expert/) | [腾讯tFold抗体结构预测专家](./experts/omics-tfold-expert/) | tFold模型，专注单克隆/纳米抗体与抗原复合物的高精度结合界面建模，辅助表位预测与亲和力改造 | 需要登录 / OAuth / 扫码授权 |
| [`prompt-engineering-expert`](./experts/prompt-engineering-expert/) | [AI提示词工程专家](./experts/prompt-engineering-expert/) | 精通提示词工程，提供提示词撰写、系统提示设计、自定义指令、优化迭代与评估测试，打造高效稳定的智能体。 | 无 |
| [`sales-data-extraction-agent`](./experts/sales-data-extraction-agent/) | [销售数据提取代理](./experts/sales-data-extraction-agent/) | 从各类数据源中自动提取整理销售数据 | 无 |
| [`trend-researcher`](./experts/trend-researcher/) | [行业趋势专家](./experts/trend-researcher/) | 持续追踪行业和技术趋势，为产品战略提供前瞻性洞察 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY`、`IMA_OPENAPI_APIKEY` |
| [`vocab-craft-expert`](./experts/vocab-craft-expert/) | [智能词汇教练](./experts/vocab-craft-expert/) | 融合间隔重复记忆科学与键盘输入训练的AI英语词汇教练，支持每日定时推送、错词强化、三种练习模式，让背单词更科学高效 | 无 |

### 法务安全（23）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`agent-identity-trust-expert`](./experts/agent-identity-trust-expert/) | [智能体身份信任专家](./experts/agent-identity-trust-expert/) | 构建AI智能体间的身份认证和信任机制 | 可能需要启用对应 MCP / 连接器 |
| [`blockchain-security-auditor`](./experts/blockchain-security-auditor/) | [区块链安全审计师](./experts/blockchain-security-auditor/) | 专精区块链智能合约和DeFi协议安全审计 | 无 |
| [`chatlaw-team`](./experts/chatlaw-team/) | [中文法律咨询团](./experts/chatlaw-team/) | 案情采集、法条研究、判例分析、建议撰写，为民事、婚姻、合同、劳动等高频场景出具专业法律咨询报告。 | 需要微信/企微相关凭证或扫码登录 |
| [`compliance-auditor`](./experts/compliance-auditor/) | [合规审计师](./experts/compliance-auditor/) | 全面审计企业运营合规性，确保符合行业标准 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`contract-expert`](./experts/contract-expert/) | [合同风控顾问](./experts/contract-expert/) | 覆盖合同起草、审查、谈判、背景评估与全生命周期管理；专业审查模式一键产出风险清单、审查报告与批注稿。 | 可能需要启用对应 MCP / 连接器 |
| [`enterprise-legal-team`](./experts/enterprise-legal-team/) | [企业法务专家团](./experts/enterprise-legal-team/) | 面向企业法务的多角色专家团，覆盖合同、交易、隐私、产品、监管、AI 治理、雇佣与知识产权分诊。 | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`fbsir-board-secretary-assistant`](./experts/fbsir-board-secretary-assistant/) | [董秘助手](./experts/fbsir-board-secretary-assistant/) | 面向公告、路演、投资者问答、互动回复和沟通稿，在对外使用前做合规红队审查并给出审批下一步。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`healthcare-marketing-compliance-expert`](./experts/healthcare-marketing-compliance-expert/) | [医疗营销合规专家](./experts/healthcare-marketing-compliance-expert/) | 确保医疗营销内容符合法规要求，守护信息准确性 | 无 |
| [`huashu-doc-reviewer`](./experts/huashu-doc-reviewer/) | [合同与公文审稿](./experts/huashu-doc-reviewer/) | 为「一人公司」打造的 AI 审稿专家。直接在 .docx 原文里加批注气泡和追踪修订，不返回新文档、不破坏原格式。 | 无 |
| [`invoice-verify-workbuddy`](./experts/invoice-verify-workbuddy/) | [智能发票专家团](./experts/invoice-verify-workbuddy/) | 五位AI专家接力协作，通过上传文件、表格或文件夹，完成识别、税局验真、信用核查与归档 | 可能需要启用对应 MCP / 连接器；需要环境变量：`KEY_NAME`、`OSS_ACCESS_KEY`、`OSS_SECRET_KEY` |
| [`ip-expert`](./experts/ip-expert/) | [知识产权专家](./experts/ip-expert/) | 覆盖著作权、专利、商标、商业秘密与域名，指引专业库检索，做侵权/FTO/确权分析并输出可落地策略。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`law-student-coach`](./experts/law-student-coach/) | [法学学习教练](./experts/law-student-coach/) | 面向法学生的学习陪练，训练苏格拉底问答、案例摘要、IRAC、课程大纲和律考复习。 | 无（可选 API/账号以增强能力） |
| [`legal-builder-hub`](./experts/legal-builder-hub/) | [法律技能治理专家](./experts/legal-builder-hub/) | 面向法律运营和技能开发者的治理助手，评估技能来源、工具权限、新鲜度、许可证和信任边界。 | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`legal-clinic-supervisor`](./experts/legal-clinic-supervisor/) | [法律诊所督导顾问](./experts/legal-clinic-supervisor/) | 面向法学院诊所导师的监督助手，支持客户接待、研究启动、期限追踪、学生入职和学期交接。 | 可能需要启用对应 MCP / 连接器 |
| [`legal-compliance-reviewer`](./experts/legal-compliance-reviewer/) | [法律合规审查员](./experts/legal-compliance-reviewer/) | 确保业务运营和产品功能符合法律法规要求，防范合规风险 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`IMA_OPENAPI_APIKEY`、`TENCENT_DOCS_TOKEN` |
| [`legal-search-pro`](./experts/legal-search-pro/) | [法律检索专家](./experts/legal-search-pro/) | 识别检索意图与场景，按法源位阶检索法规与类案，验证效力评估相似度，适配14种输出可溯源报告。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`litigation-legal`](./experts/litigation-legal/) | [诉讼支持顾问](./experts/litigation-legal/) | 面向诉讼律师的案件支持专家，梳理案件、证据、时间线、质证准备、索赔图表和文书草稿。 | 需要微信/企微相关凭证或扫码登录 |
| [`marketing-reviewer`](./experts/marketing-reviewer/) | [营销文案审查官](./experts/marketing-reviewer/) | 9维度34条规则扫描营销文案，定位广告法与隐私合规风险，输出分级Excel与HTML审查报告。 | 无（可选 API/账号以增强能力） |
| [`smb-compliance`](./experts/smb-compliance/) | [客户与合规官](./experts/smb-compliance/) | 小企业客户与合规官，处理客户反馈、客诉工单、CRM清理和合同风险审查 | 需要微信/企微相关凭证或扫码登录 |
| [`soe`](./experts/soe/) | [腾讯云安全运营专家](./experts/soe/) | 分析WAF/主机安全/云防火墙/SOC/御界/天幕的告警/事件等离线数据，含漏洞、攻击、溯源分析。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`tax-compliance-team`](./experts/tax-compliance-team/) | [财税合规专家团](./experts/tax-compliance-team/) | 覆盖票据处理、记账核算、报表编制、税务申报、合规审计五大环节的企业财税合规全链路管理专家团 | 无 |
| [`xiaofa-litigation-assistant`](./experts/xiaofa-litigation-assistant/) | [诉讼助手](./experts/xiaofa-litigation-assistant/) | 诉讼助手：起草起诉状、要素式转换、证据整理、流程指引、强制执行、利息计算。输出 DOCX 格式，Word/WPS 直接编辑。7大法律技能，一站式自助办案。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器；需要环境变量：`YOUR_API_KEY` |
| [`zero-knowledge-proof-admin`](./experts/zero-knowledge-proof-admin/) | [零知识证明管理员](./experts/zero-knowledge-proof-admin/) | 精通零知识证明技术的应用和管理 | 无（可选 API/账号以增强能力） |

### 游戏空间（25）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`game-audio-engineer`](./experts/game-audio-engineer/) | [游戏音频工程师](./experts/game-audio-engineer/) | 精通FMOD/Wwise集成和空间音频，让游戏声音栩栩如生 | 无 |
| [`game-designer`](./experts/game-designer/) | [游戏设计师](./experts/game-designer/) | 精通游戏系统和机制设计，用循环杠杆和心理构建玩法 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录 |
| [`game-development-studio`](./experts/game-development-studio/) | [游戏开发工作室](./experts/game-development-studio/) | 统筹策划、技术、美术、音频、质量、运营六大专业成员，以七阶段工作流驱动游戏从概念到上线流程协同开发。 | 无（可选 API/账号以增强能力） |
| [`godot-game-script-engineer`](./experts/godot-game-script-engineer/) | [Godot游戏脚本工程师](./experts/godot-game-script-engineer/) | 精通GDScript 2.0和Godot 4节点架构 | 无 |
| [`godot-multiplayer-engineer`](./experts/godot-multiplayer-engineer/) | [Godot多人联机工程师](./experts/godot-multiplayer-engineer/) | 精通Godot 4 MultiplayerAPI和网络复制 | 无 |
| [`godot-shader-developer`](./experts/godot-shader-developer/) | [Godot着色器开发者](./experts/godot-shader-developer/) | 精通Godot着色语言和VisualShader | 无 |
| [`level-designer`](./experts/level-designer/) | [关卡设计师](./experts/level-designer/) | 将每个关卡视为精心编排的体验，用空间讲述故事 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`mac-os-spatial-metal-engineer`](./experts/mac-os-spatial-metal-engineer/) | [macOS空间Metal工程师](./experts/mac-os-spatial-metal-engineer/) | 精通Apple Metal图形API和macOS空间计算开发 | 无 |
| [`narrative-designer`](./experts/narrative-designer/) | [叙事设计师](./experts/narrative-designer/) | 将叙事和游戏玩法无缝融合，让故事与互动不可分割 | 无（可选 API/账号以增强能力） |
| [`roblox-avatar-creator`](./experts/roblox-avatar-creator/) | [Roblox虚拟形象创作者](./experts/roblox-avatar-creator/) | 精通Roblox UGC和虚拟形象管线 | 无 |
| [`roblox-experience-designer`](./experts/roblox-experience-designer/) | [Roblox体验设计师](./experts/roblox-experience-designer/) | 精通Roblox平台UX和商业化设计 | 无 |
| [`roblox-system-script-engineer`](./experts/roblox-system-script-engineer/) | [Roblox系统脚本工程师](./experts/roblox-system-script-engineer/) | 精通Luau和Roblox客户端-服务器安全模型 | 无 |
| [`technical-artist`](./experts/technical-artist/) | [技术美术](./experts/technical-artist/) | 在美术愿景与引擎实现之间架起桥梁，精通着色器和VFX | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`GEMINI_API_KEY` |
| [`unity-architect`](./experts/unity-architect/) | [Unity架构师](./experts/unity-architect/) | 精通ScriptableObjects和解耦系统设计 | 无 |
| [`unity-editor-tool-developer`](./experts/unity-editor-tool-developer/) | [Unity编辑器工具开发者](./experts/unity-editor-tool-developer/) | 精通Unity自定义EditorWindow和管线自动化 | 需要登录 / OAuth / 扫码授权 |
| [`unity-multiplayer-engineer`](./experts/unity-multiplayer-engineer/) | [Unity多人联机工程师](./experts/unity-multiplayer-engineer/) | 精通Netcode for GameObjects和网络预测 | 无 |
| [`unity-shader-graph-artist`](./experts/unity-shader-graph-artist/) | [Unity着色器图表艺术家](./experts/unity-shader-graph-artist/) | 精通Unity Shader Graph和HLSL | 无 |
| [`unreal-multiplayer-architect`](./experts/unreal-multiplayer-architect/) | [Unreal多人架构师](./experts/unreal-multiplayer-architect/) | 精通Unreal Actor复制和服务器权威架构 | 需要登录 / OAuth / 扫码授权 |
| [`unreal-system-engineer`](./experts/unreal-system-engineer/) | [Unreal系统工程师](./experts/unreal-system-engineer/) | 精通C++/Blueprint和Nanite/Lumen | 无 |
| [`unreal-technical-artist`](./experts/unreal-technical-artist/) | [Unreal技术美术](./experts/unreal-technical-artist/) | 精通UE5材质编辑器和Niagara VFX | 无 |
| [`unreal-world-builder`](./experts/unreal-world-builder/) | [Unreal世界构建师](./experts/unreal-world-builder/) | 精通UE5 World Partition和大世界流式加载 | 无 |
| [`vision-os-spatial-engineer`](./experts/vision-os-spatial-engineer/) | [visionOS空间工程师](./experts/vision-os-spatial-engineer/) | 精通visionOS平台开发，打造Apple Vision Pro空间应用 | 无（可选 API/账号以增强能力） |
| [`xr-cockpit-interaction-expert`](./experts/xr-cockpit-interaction-expert/) | [XR座舱交互专家](./experts/xr-cockpit-interaction-expert/) | 专精XR环境下的座舱式交互设计 | 无 |
| [`xr-immersive-developer`](./experts/xr-immersive-developer/) | [XR沉浸式开发者](./experts/xr-immersive-developer/) | 精通XR沉浸式体验开发，创造身临其境的VR/MR应用 | 无（可选 API/账号以增强能力） |
| [`xr-interface-architect`](./experts/xr-interface-architect/) | [XR界面架构师](./experts/xr-interface-architect/) | 设计XR环境中的用户界面架构，让3D空间交互直观自然 | 无 |

### 腾讯专区（29）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`andon-q-expert`](./experts/andon-q-expert/) | [腾讯云智能客服](./experts/andon-q-expert/) | 精通腾讯云全线产品，提供产品咨询、故障排查、服务报告等多维度服务的技术专家。 | 需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY`、`TENCENTCLOUD_TOKEN` |
| [`anti-scam-agent`](./experts/anti-scam-agent/) | [腾讯云天御反诈专家](./experts/anti-scam-agent/) | 金融黑灰产情报驱动的反诈智能体，覆盖电诈、职业背债、贷款包装、反催收，能分析、能查证、能出研判报告。 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`apm-performance-expert`](./experts/apm-performance-expert/) | [应用性能专家](./experts/apm-performance-expert/) | 精通腾讯云 APM 性能诊断与调优，快速定位应用瓶颈并给出优化方案 | 可能需要启用对应 MCP / 连接器；需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`capacity-expert`](./experts/capacity-expert/) | [腾讯云容量规划专家](./experts/capacity-expert/) | 容量规划专家。擅长水位监控、容量预测与弹性伸缩策略制定，防止资源瓶颈与浪费。 | 可能需要启用对应 MCP / 连接器 |
| [`cat-network-quality-analyst`](./experts/cat-network-quality-analyst/) | [网络质量分析专家](./experts/cat-network-quality-analyst/) | 精通多维性能分析、异常定位、抓包诊断、问题定界，快速定位网络与服务异常根因 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`CAT_SECRET_ID`、`CAT_SECRET_KEY`、`TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY` |
| [`chaos-expert`](./experts/chaos-expert/) | [腾讯云混沌演练专家](./experts/chaos-expert/) | 混沌演练专家。擅长故障注入演练、韧性验证与熔断策略评估，提升系统抗脆弱能力。 | 可能需要启用对应 MCP / 连接器 |
| [`charity-doc-finance-expert`](./experts/charity-doc-finance-expert/) | [公益文书与财务专家](./experts/charity-doc-finance-expert/) | 公益机构文书与财务一站式专家，覆盖项目申请书、结项报告、票据管理、审计准备与合规咨询，帮助公益人从繁琐行政中解放。 | 需要微信/企微相关凭证或扫码登录 |
| [`cloud-ops-team`](./experts/cloud-ops-team/) | [腾讯云技术支持](./experts/cloud-ops-team/) | 三位专家组成的运维团队 — CloudQ 负责多云统一治理与架构可视化，AndonQ 负责工单管理与智能问答，MigraQ 负责跨云迁移规划与 TCO 分析。从迁移上云到日常运维… | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY`、`TENCENTCLOUD_TOKEN` |
| [`contract-legal-expert`](./experts/contract-legal-expert/) | [资深合同法务专家](./experts/contract-legal-expert/) | 腾讯电子签合同法务专家擅长合同起草、审查、对比、法规检索，能在线发起签署，劳动/租赁/买卖全场景覆盖 | 需要登录 / OAuth / 扫码授权；需要环境变量：`ESIGN_TOKEN`、`NEW_TOKEN`、`YOUR_TOKEN` |
| [`databrain-agent-v2`](./experts/databrain-agent-v2/) | [DataBrain数据专家2.0](./experts/databrain-agent-v2/) | 覆盖经分取数、三方市场情报、舆情情感分析、归因下钻及跨游戏竞品对比，提供有数据支撑的专业洞察与建议。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器；需要环境变量：`DATABRAIN_TOKEN` |
| [`edgeone-makers-experts`](./experts/edgeone-makers-experts/) | [Makers 开发专家团](./experts/edgeone-makers-experts/) | 在 EdgeOne Makers 上构建并部署 Web 应用 —— 涵盖前端页面、Serverless 后端（边缘函数/云函数）、AI Agent 开发（DeepAgents、L… | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`AI_GATEWAY_API_KEY`、`EDGEONE_PAGES_API_TOKEN`、`SUPABASE_ANON_KEY`、`WSA_API_KEY` |
| [`finops-expert`](./experts/finops-expert/) | [腾讯云FinOps专家](./experts/finops-expert/) | 云成本治理专家。擅长账单分析、闲置资源识别、计费模式优化与成本分摊，驱动降本增效决策。 | 可能需要启用对应 MCP / 连接器 |
| [`industry-sre-team`](./experts/industry-sre-team/) | [腾讯云行业SRE](./experts/industry-sre-team/) | 12 位行业 SRE 覆盖游戏、金融、电商等场景，做五维巡检，输出可对照可执行的架构治理建议。 | 无 |
| [`inspection-expert`](./experts/inspection-expert/) | [腾讯云风险巡检专家](./experts/inspection-expert/) | 云资源巡检专家。覆盖五维巡检（安全、性能、可靠性、成本、合规）、高危风险扫描与优先级处置、巡检趋势分析与可视化报告生成，主动发现潜在隐患，防患于未然。 | 可能需要启用对应 MCP / 连接器 |
| [`migraq-team`](./experts/migraq-team/) | [腾讯云上云迁移专家团](./experts/migraq-team/) | 7位专家协作完成上云迁移：产品选型、Landing Zone、架构设计、交付实施、运维与FDE部署 | 无（可选 API/账号以增强能力） |
| [`multi-cloud-expert`](./experts/multi-cloud-expert/) | [多云AIOps专家](./experts/multi-cloud-expert/) | 统一管理腾讯云、阿里云、AWS、Azure、GCP 等多云平台，一个智能体即可管多云。 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`multi-cloud-management-expert`](./experts/multi-cloud-management-expert/) | [腾讯云DevOps专家](./experts/multi-cloud-management-expert/) | 精通腾讯云、阿里云、AWS等多云架构治理、架构可视化、智能巡检、云成本优化和风险评估，一个专家管理所有云。 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`nges-healthcare-marketing-team`](./experts/nges-healthcare-marketing-team/) | [腾讯健康NGES医药营销专家团](./experts/nges-healthcare-marketing-team/) | 由医药营销智能协调官统一调度的医药营销专家团，整合HCP客户洞察、互动病例生成、学术物料生成、合规审核四大能力，覆盖从客户情报分析到内容生产到合规检测的全流程。企业版提供完整功能… | 需要微信/企微相关凭证或扫码登录 |
| [`patient-education-content-review-word-assistant`](./experts/patient-education-content-review-word-assistant/) | [腾讯健康药箱-私域患教内容审核助手](./experts/patient-education-content-review-word-assistant/) | 六维度审核患教内容并核对数据文献一致性，审核意见以 Word 批注+高亮直接标注在原文上输出。 | 需要微信/企微相关凭证或扫码登录 |
| [`sdk-log-expert`](./experts/sdk-log-expert/) | [SDK 日志分析专家](./experts/sdk-log-expert/) | 解码客户端日志，还原 TRTC/IM/TUI 时间线，定位音视频与 IM 相关根因 | 需要微信/企微相关凭证或扫码登录 |
| [`sre-expert`](./experts/sre-expert/) | [腾讯云SRE专家](./experts/sre-expert/) | 站点可靠性专家。擅长故障根因推理、告警关联分析、业务进程诊断与 SLO 治理，通过系统化诊断方法论保障服务持续稳定运行。 | 可能需要启用对应 MCP / 连接器 |
| [`tc-sec`](./experts/tc-sec/) | [腾讯云安全专家](./experts/tc-sec/) | 联动CWP/KMS/BH/CDS/CFW/SSM/TCSS/WAF/CSIP产品接口生成安全运营报告 | 需要登录 / OAuth / 扫码授权 |
| [`tencent-charity-expert`](./experts/tencent-charity-expert/) | [腾讯技术公益智能化专家](./experts/tencent-charity-expert/) | 精通公益行业产品和技术解决方案的腾讯技术公益智能化专家 | 无 |
| [`tencent-rtc-expert`](./experts/tencent-rtc-expert/) | [腾讯云实时音视频专家](./experts/tencent-rtc-expert/) | TRTC 技术支持专家：通话用量与质量查询、单次通话诊断、云端巡检解读、故障排查与友商代码迁移。 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY` |
| [`tencent-security-expert`](./experts/tencent-security-expert/) | [腾讯安全专家](./experts/tencent-security-expert/) | 深耕安全领域多年，提供威胁建模、漏洞评估、安全代码审查、架构设计、事件响应、安全咨询等服务 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`tianyu-account-guardian`](./experts/tianyu-account-guardian/) | [腾讯云天御账号保护专家](./experts/tianyu-account-guardian/) | 替您盯住注册、登录、裂变全链路账号异常，实时调优策略拦截恶意账号，并生成客诉原因分析报告。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`tianyu-marketing-guardian`](./experts/tianyu-marketing-guardian/) | [腾讯云天御营销保护专家](./experts/tianyu-marketing-guardian/) | 替您守护每一场营销活动，在文旅、零售、Token、医疗挂号等场景自动盯活动、查漏召、调策略护预算。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权 |
| [`well-arch-expert`](./experts/well-arch-expert/) | [腾讯云卓越架构专家](./experts/well-arch-expert/) | 卓越架构专家。擅长架构可视化评估、资源拓扑梳理、Well-Architected 六支柱评估与架构风险识别，确保架构符合最佳实践。 | 可能需要启用对应 MCP / 连接器 |
| [`yunzhi-qa-assistant`](./experts/yunzhi-qa-assistant/) | [腾讯云知识问答专家](./experts/yunzhi-qa-assistant/) | 基于腾讯云知（乐享）平台的检索增强问答专家。调用乐享 MCP 的语义向量检索多路并行召回；基于检索结果生成结构化回答； | 可能需要启用对应 MCP / 连接器；需要环境变量：`LEXIANG_TOKEN` |

### 营销增长（33）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`ad-creative-strategist`](./experts/ad-creative-strategist/) | [广告创意策略师](./experts/ad-creative-strategist/) | 精通广告创意设计和效果预判，创作高转化广告素材 | 需要大模型 API Key（OpenAI/Anthropic 等）；可能需要启用对应 MCP / 连接器 |
| [`ad-tracking-expert`](./experts/ad-tracking-expert/) | [广告追踪技术专家](./experts/ad-tracking-expert/) | 精通广告追踪代码和转化归因技术，确保投放效果可追踪 | 需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`app-store-optimization-expert`](./experts/app-store-optimization-expert/) | [应用商店优化专家](./experts/app-store-optimization-expert/) | 精通App Store和Google Play搜索排名算法，让应用脱颖而出 | 无 |
| [`auto-consultant`](./experts/auto-consultant/) | [汽车营销专家](./experts/auto-consultant/) | 精通用户选车购车决策，深谙汽车营销增长，覆盖品牌营销、用户增长、车型分析、购车咨询等全链路汽车服务。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`baidu-seo-expert`](./experts/baidu-seo-expert/) | [百度SEO专家](./experts/baidu-seo-expert/) | 深谙百度搜索算法和中国搜索生态，让品牌获得最大曝光 | 无 |
| [`brand-guardian`](./experts/brand-guardian/) | [品牌策略师](./experts/brand-guardian/) | 15年品牌战略经验，守护品牌一致性的终极捍卫者 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`carousel-content-growth-expert`](./experts/carousel-content-growth-expert/) | [轮播内容增长专家](./experts/carousel-content-growth-expert/) | 专精设计高互动率轮播图内容，驱动社交平台用户参与和增长 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`GEMINI_API_KEY`、`UPLOADPOST_TOKEN` |
| [`china-ecommerce-operations-expert`](./experts/china-ecommerce-operations-expert/) | [中国电商运营专家](./experts/china-ecommerce-operations-expert/) | 精通天猫京东拼多多等平台运营，从选品到爆款一站式操盘 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`content-monetization-team`](./experts/content-monetization-team/) | [内容变现商业化专家团](./experts/content-monetization-team/) | 5人专家团覆盖CPS带货分佣、CPE/CPM效果广告、创作者-品牌交易撮合与收益分析，助力内容创作者和品牌方实现商业化闭环 | 无（可选 API/账号以增强能力） |
| [`cross-border-ecommerce-expert`](./experts/cross-border-ecommerce-expert/) | [跨境电商专家](./experts/cross-border-ecommerce-expert/) | 精通亚马逊Shopify等国际电商平台，助力品牌出海全球 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`cultural-intelligence-strategist`](./experts/cultural-intelligence-strategist/) | [文化智能策略师](./experts/cultural-intelligence-strategist/) | 帮助品牌建立全球化过程中的文化敏感度 | 无 |
| [`developer-evangelist`](./experts/developer-evangelist/) | [开发者布道师](./experts/developer-evangelist/) | 构建发展开发者社区，推动产品在开发者群体中的采用 | 需要 GitHub Token 或 `gh auth login` |
| [`executing-marketing-campaigns`](./experts/executing-marketing-campaigns/) | [营销活动策划专家](./experts/executing-marketing-campaigns/) | 策划、创建和优化全渠道营销活动，包括内容策略、社交媒体、邮件营销和广告投放 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`geo-diagnosis-expert`](./experts/geo-diagnosis-expert/) | [品牌 GEO 可见度诊断师](./experts/geo-diagnosis-expert/) | 品牌 GEO 可见度诊断专家，覆盖基建评估、AI 平台收录、竞品对标、舆情分析，输出 AIVO 评分报告。 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`growth-hacker`](./experts/growth-hacker/) | [增长黑客](./experts/growth-hacker/) | 用数据驱动的实验方法论找到未开发的增长渠道，实现指数级增长 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要环境变量：`IMA_OPENAPI_APIKEY` |
| [`identity-graph-operator`](./experts/identity-graph-operator/) | [身份图谱运营师](./experts/identity-graph-operator/) | 构建维护用户身份图谱系统，实现跨平台身份识别 | 无 |
| [`jiayi-ads-analytics-expert`](./experts/jiayi-ads-analytics-expert/) | [广告投放操盘专家](./experts/jiayi-ads-analytics-expert/) | 不止分析，更能直接操盘——通过API调价、暂停词、加否词、改预算、上下创意，五大广告平台一句话搞定 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`GOOGLE_ADS_CLIENT_SECRET`、`GOOGLE_ADS_DEVELOPER_TOKEN`、`GOOGLE_ADS_REFRESH_TOKEN`、`MICROSOFT_ADS_DEVELOPER_TOKEN`、`TENCENT_AD_ACCESS_TOKEN`、`TENCENT_AD_CLIENT_SECRET` |
| [`linked-in-content-creator`](./experts/linked-in-content-creator/) | [LinkedIn内容创作者](./experts/linked-in-content-creator/) | 精通LinkedIn专业社交平台内容策略，帮助建立思想领袖地位 | 无 |
| [`livestream-ecommerce-coach`](./experts/livestream-ecommerce-coach/) | [直播电商教练](./experts/livestream-ecommerce-coach/) | 精通直播带货全链路运营，从话术到投流帮助实现GMV突破 | 需要微信/企微相关凭证或扫码登录 |
| [`market-analysis-cn`](./experts/market-analysis-cn/) | [市场分析专家](./experts/market-analysis-cn/) | 聚焦市场趋势、竞品对标与用户行为洞察，输出SWOT分析与战略建议，助力企业做出明智商业决策。 | 无 |
| [`marketing-campaign-team`](./experts/marketing-campaign-team/) | [营销战役团队](./experts/marketing-campaign-team/) | 由营销总监领导的 4 人营销专家团队：内容创作者（博客/邮件/社媒/品牌声音）、活动策划师（战役策略/受众/渠道/预算）、SEO 专家（技术审计/内容优化/效果分析）和品牌分析师… | 需要微信/企微相关凭证或扫码登录 |
| [`paid-media-auditor`](./experts/paid-media-auditor/) | [付费媒体审计师](./experts/paid-media-auditor/) | 深度审计广告投放数据和预算分配，找出被浪费的广告费 | 可能需要启用对应 MCP / 连接器 |
| [`ppc-bidding-strategist`](./experts/ppc-bidding-strategist/) | [PPC竞价广告策略师](./experts/ppc-bidding-strategist/) | 精通Google Ads和百度竞价，以最低点击成本获取高质量流量 | 可能需要启用对应 MCP / 连接器 |
| [`private-domain-marketing-expert`](./experts/private-domain-marketing-expert/) | [私域营销专家](./experts/private-domain-marketing-expert/) | 深谙私域运营增长，盘活现有数据资源、洞察营销机会、实现业绩增长 | 需要微信/企微相关凭证或扫码登录 |
| [`private-domain-operations-expert`](./experts/private-domain-operations-expert/) | [私域运营专家](./experts/private-domain-operations-expert/) | 精通微信私域流量池搭建运营，将公域流量沉淀为私域资产 | 需要微信/企微相关凭证或扫码登录 |
| [`programmatic-ad-buyer`](./experts/programmatic-ad-buyer/) | [程序化广告买手](./experts/programmatic-ad-buyer/) | 精通程序化广告购买和DSP平台，通过算法实现大规模精准投放 | 可能需要启用对应 MCP / 连接器 |
| [`reddit-community-builder`](./experts/reddit-community-builder/) | [Reddit社区建设者](./experts/reddit-community-builder/) | 深谙Reddit社区文化，在全球最大论坛上建立真实社区影响力 | 需要 GitHub Token 或 `gh auth login` |
| [`search-term-analyst`](./experts/search-term-analyst/) | [搜索词分析师](./experts/search-term-analyst/) | 深度分析搜索词数据，挖掘用户真实搜索意图 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 GitHub Token 或 `gh auth login`；可能需要启用对应 MCP / 连接器；需要环境变量：`GH_TOKEN`、`GITHUB_TOKEN`、`TAVILY_API_KEY` |
| [`seo-content-team`](./experts/seo-content-team/) | [SEO 内容营销团队](./experts/seo-content-team/) | 7位专业角色分5阶段协作：关键词研究、SEO长文创作、技术优化、内容编辑、链接策略、转化率分析，全流程自动化产出高质量SEO内容 | 无 |
| [`seo-expert`](./experts/seo-expert/) | [SEO专家](./experts/seo-expert/) | 精通Google搜索算法和技术SEO，让网站在搜索结果中稳居前列 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`social-ad-strategist`](./experts/social-ad-strategist/) | [社交广告策略师](./experts/social-ad-strategist/) | 精通社交平台广告投放，以精准定向实现最优获客成本 | 可能需要启用对应 MCP / 连接器 |
| [`social-engagement-team`](./experts/social-engagement-team/) | [社媒互动增长专家团](./experts/social-engagement-team/) | 通过智能化互动自动化、AI评论运营、高转化信号挖掘和品牌舆情监控，安全高效提升社交媒体互动效果，覆盖14+全球主流平台 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`social-media-strategist`](./experts/social-media-strategist/) | [社交媒体策略师](./experts/social-media-strategist/) | 全面统筹多平台社交媒体策略，让品牌在每个平台发出最强音 | 无 |

### 行业顾问（20）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`ask-liuxiaopai`](./experts/ask-liuxiaopai/) | [产品顾问](./experts/ask-liuxiaopai/) | Raphael AI 创始人刘小排的数字分身，office-hours 风格陪你拆 idea：钉死具体的人、真痛点、第一笔钱、第一批用户在哪，再给一件今晚就能做的事。 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录 |
| [`chaogeek-kongming`](./experts/chaogeek-kongming/) | [苏格拉底式AI思维搭子](./experts/chaogeek-kongming/) | 一人公司认知反缴械思维搭子：少问但问到根，补上下文、对齐意图，帮你驾驭智能体不外包判断力。 | 无（可选 API/账号以增强能力） |
| [`chuangye-manor`](./experts/chuangye-manor/) | [创业伙伴](./experts/chuangye-manor/) | 林老师分身+读书伙伴。送《创业可以学》，陪创业者读书，从读书中听痛点，痛点匹配时自然引出课程咨询。擅长GTM落地、敢见客户情绪层突破、顺序判断。 | 需要微信/企微相关凭证或扫码登录 |
| [`family-education-ma`](./experts/family-education-ma/) | [家庭教育专家](./experts/family-education-ma/) | 腾讯未保营地8年一线实践，融合三大循证体系，为家长提供亲子沟通、沉迷干预、家庭成长咨询 | 无 |
| [`fbsir-eight-seat-board`](./experts/fbsir-eight-seat-board/) | [独董会](./experts/fbsir-eight-seat-board/) | 福帮手经营决策独立审议专家团｜按案组建必要席位，独立判断、交叉质询、保留异议，交付可追溯行动备忘录 | 无（可选 API/账号以增强能力） |
| [`fbsir-industry-scene-researcher`](./experts/fbsir-industry-scene-researcher/) | [行业场景研究员](./experts/fbsir-industry-scene-researcher/) | 围绕一个行业场景定位关键工作流缺口，并交付补位卡、3天行动计划、项目动作执行包和下一步建议。 | 可能需要启用对应 MCP / 连接器 |
| [`fbsir-super-partner`](./experts/fbsir-super-partner/) | [超级合伙人|魔镜行动](./experts/fbsir-super-partner/) | 带上目标或真实材料，立即得到可使用成品；宿主能力可用且获授权时执行并回执，再做72小时裁决。 | 需要登录 / OAuth / 扫码授权 |
| [`fbsir-super-partner-group`](./experts/fbsir-super-partner-group/) | [超级合伙人](./experts/fbsir-super-partner-group/) | 以AI+OPC智能化运营为底座，统筹战略、运营、增长与AI试点，输出诊断卡和下一步。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`fortune-consultant`](./experts/fortune-consultant/) | [赛博神算子](./experts/fortune-consultant/) | 传统命理参考工具——八字紫微排盘、塔罗梅花起卦、农历黄历查询，多体系交叉参考，仅供娱乐。 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`gaokao-advisor`](./experts/gaokao-advisor/) | [高考我帮你](./experts/gaokao-advisor/) | 辅助检索高考知识库并调用分数线、一分一段能力，整理带来源的真题、高校专业和志愿参考；同时提供全流程志愿填报引导，产出可转发的腾讯文档志愿报告 | 需要大模型 API Key（OpenAI/Anthropic 等） |
| [`indie-founder-coach`](./experts/indie-founder-coach/) | [独立创业教练](./experts/indie-founder-coach/) | 信奉精益创业与自力更生理念，帮助独立创业者用最少资源从0到1构建可持续盈利事业，覆盖创业全旅程关键决策 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录 |
| [`ket-prep-team`](./experts/ket-prep-team/) | [KET备考专家团](./experts/ket-prep-team/) | 剑桥认证考官领衔，为小学生提供KET全流程备考：学情测评、词汇语法地基、听说读写专项提分、考前冲刺模考，助力Merit（优秀）/Distinction（卓越）达标。 | 无 |
| [`liuxue-yanxue-expert`](./experts/liuxue-yanxue-expert/) | [留学研学专家](./experts/liuxue-yanxue-expert/) | 面向家庭生成留学研学首轮规划，兼顾高考窗口、预算风险、路径备选与后续承接行动建议。 | 无（可选 API/账号以增强能力） |
| [`metamorphosis-practitioner`](./experts/metamorphosis-practitioner/) | [创业心态陪伴者](./experts/metamorphosis-practitioner/) | 不是导师，是走过你想走的路的人。通过分享创业经历帮创业者觉醒心态问题，不说教只分享，让用户自己感悟。 | 无（可选 API/账号以增强能力） |
| [`opc-team`](./experts/opc-team/) | [一人公司专家团](./experts/opc-team/) | 基于由Easy创作的《一人企业方法论》，9位专家陪你走完从资源盘点、利基定位到MVP、转化、复盘的一人公司全流程共创 | 无（可选 API/账号以增强能力） |
| [`paper-topic-selection`](./experts/paper-topic-selection/) | [选题专家团队（WANFANG TOPIC）](./experts/paper-topic-selection/) | 帮你做论文选题：检索文献、推荐方向、评估新颖性、生成标题、出领域报告。说学科方向即可。 | 需要环境变量：`APP_KEY` |
| [`skillhub-charity-expert-team`](./experts/skillhub-charity-expert-team/) | [技术公益专家团](./experts/skillhub-charity-expert-team/) | 首席协调官星星带领六位专家，覆盖公益技能从需求分析、编写、测试、社会价值评审、版权确认和打包交付的全流程。 | 可能需要启用对应 MCP / 连接器 |
| [`smb-team`](./experts/smb-team/) | [经营总管](./experts/smb-team/) | 经营总管调度四位领域专家，覆盖财务、营收、客户合规和运营，小企业管理一站搞定 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录 |
| [`terminal-veteran`](./experts/terminal-veteran/) | [终端产业分析师](./experts/terminal-veteran/) | 近三十年终端老兵，11条铁律+三层方法论，厂商策略/渠道选品/投资分析+行业报告 | 无 |
| [`tripstar-agent`](./experts/tripstar-agent/) | [旅游攻略管家](./experts/tripstar-agent/) | 生活服务管家，一站式搞定行程规划、景点/酒店/天气/预算与美团红包领取 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 12306 账号登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`AUTH_SCRIPT`、`USER_TOKEN` |

### 运营人力（11）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`corporate-training-designer`](./experts/corporate-training-designer/) | [企业培训设计师](./experts/corporate-training-designer/) | 设计系统化企业培训课程和学习路径，让员工技能快速提升 | 需要微信/企微相关凭证或扫码登录 |
| [`customer-support-expert`](./experts/customer-support-expert/) | [客户支持专家](./experts/customer-support-expert/) | 将每次沮丧的用户互动转化为忠实拥护者，用卓越服务创口碑 | 无 |
| [`hr-operations-team`](./experts/hr-operations-team/) | [HR 运营团队](./experts/hr-operations-team/) | 人力资源管理流程化，招聘筛选、薪酬体系设计、组织发展与HR运营流程化管理，助力企业人才战略落地 | 无 |
| [`ihr-ai-interviewer`](./experts/ihr-ai-interviewer/) | [数字人招聘面试专家](./experts/ihr-ai-interviewer/) | 围绕岗位画像设计面试维度与题库，管理数字人面试模板，校验候选人信息并发起面试，回查面试记录与纪要。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`IHR360_API_TOKEN` |
| [`ihr-conference`](./experts/ihr-conference/) | [AI面谈官](./experts/ihr-conference/) | 提供九大智能面谈大纲与线上实时指引，基于云录制自动生成结构化纪要与待办，全周期辅助管理者高效沟通。 | 需要登录 / OAuth / 扫码授权；需要环境变量：`IHR360_API_TOKEN` |
| [`interview-simulator`](./experts/interview-simulator/) | [面试模拟专家](./experts/interview-simulator/) | 模拟任意职位的真实面试官，覆盖技术产品销售人事等全岗位，提供逐题评分详细反馈与录用建议，助你高效备战面试。 | 无（可选 API/账号以增强能力） |
| [`recruitment-expert`](./experts/recruitment-expert/) | [招聘专家](./experts/recruitment-expert/) | 精通人才招聘全流程，为团队找到最佳人才 | 需要飞书应用凭证或用户登录授权 |
| [`resume-assistant`](./experts/resume-assistant/) | [简历优化专家](./experts/resume-assistant/) | 提供百分制专业评分、四十项深度清单润色、岗位匹配定制与多格式导出，全面打造高竞争力求职简历。 | 无（可选 API/账号以增强能力） |
| [`smb-operations`](./experts/smb-operations/) | [组织运营师](./experts/smb-operations/) | 小企业组织运营师，负责招聘入职、工具初始化和业务快照，让运营不掉链子 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录 |
| [`study-abroad-consultant`](./experts/study-abroad-consultant/) | [留学顾问](./experts/study-abroad-consultant/) | 精通各国留学申请流程和院校信息 | 无（可选 API/账号以增强能力） |
| [`supply-chain-strategist`](./experts/supply-chain-strategist/) | [供应链策略师](./experts/supply-chain-strategist/) | 优化供应链每个环节，实现成本效率韧性的最佳平衡 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY`、`TMAP_WEBSERVICE_KEY` |

### 金融投资（32）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`a-share-analysis`](./experts/a-share-analysis/) | [A股研究团队](./experts/a-share-analysis/) | 8位研究专家支持6个预设工作流编排，覆盖宏观策略、盘面解读、个股深度、估值定价、产业链映射、资金追踪、风险诊断 | 无（可选 API/账号以增强能力） |
| [`accounts-payable-agent`](./experts/accounts-payable-agent/) | [应付账款代理](./experts/accounts-payable-agent/) | 自动化处理应付账款流程，确保付款准确及时 | 无 |
| [`citongshuopro`](./experts/citongshuopro/) | [刺桐说Pro-投资社群嘉宾团](./experts/citongshuopro/) | 模拟真实投资社群运作模式的多智能体投研系统，已接入社群嘉宾数字分身，可7*24为您提供投资咨询服务。 | 可能需要启用对应 MCP / 连接器 |
| [`earnings-reviewer`](./experts/earnings-reviewer/) | [财报研究员](./experts/earnings-reviewer/) | 资深季报复核分析师,读财报电话会和公告更新覆盖模型,产出季报后记、方差表与估值调整,供研究部门沿用。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`equity-research`](./experts/equity-research/) | [股票研究专家](./experts/equity-research/) | 全面的股票研究工具集：财报分析、首次覆盖报告、DCF与可比估值、多空推介、投资备忘录、事件情景分析、组合风险管理，覆盖完整买方卖方研究工作流 | 无 |
| [`fin-research-expert`](./experts/fin-research-expert/) | [股市投研分析师](./experts/fin-research-expert/) | 连接同舟公开投研能力，稳定生成个股、行业、事件与研报的证据化简报和可复核投研案例页面 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要 GitHub Token 或 `gh auth login`；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器 |
| [`finance`](./experts/finance/) | [财务会计专家](./experts/finance/) | 财务会计工具集：月末结账、日记账分录、账户核对、财务报表生成、差异分析和 SOX 审计支持 | 无（可选 API/账号以增强能力） |
| [`financial-analysis`](./experts/financial-analysis/) | [金融建模专家](./experts/financial-analysis/) | 核心金融建模工具：DCF 估值、可比公司分析、LBO 模型、三张表模型、竞争格局分析和 PPT 质检 | 可能需要启用对应 MCP / 连接器 |
| [`financial-tracker`](./experts/financial-tracker/) | [财务追踪师](./experts/financial-tracker/) | 精准追踪项目和业务的财务数据，确保每笔收支清晰透明 | 无（可选 API/账号以增强能力） |
| [`gl-reconciler`](./experts/gl-reconciler/) | [总账对账师](./experts/gl-reconciler/) | 基金后台日终与月末对账专员,在总账与子账之间找出差异、追溯到源交易、归类 timing/reclass/FX 等原因并出具可签核清单。 | 可能需要启用对应 MCP / 连接器 |
| [`investment-banking`](./experts/investment-banking/) | [投资银行专家](./experts/investment-banking/) | 全能投资银行专家：交易材料制作、估值建模（Comps/DCF/LBO/三表）、资本市场融资、买方尽调分析、重组与回收瀑布、交易全流程执行 | 可能需要启用对应 MCP / 连接器 |
| [`investment-masters-team`](./experts/investment-masters-team/) | [投资大师专家团](./experts/investment-masters-team/) | 13位传奇投资哲学家 + 6位专业分析师并行分析，风险管理师评估约束，投资组合经理信号聚合投票，多角度投资分析参考 | 无 |
| [`kyc-screener`](./experts/kyc-screener/) | [客户合规官](./experts/kyc-screener/) | 客户准入合规分析师,解析 KYC 材料、跑规则引擎、比对制裁与 PEP 名单,并按风险等级形成可交合规签核的升级包。 | 可能需要启用对应 MCP / 连接器 |
| [`mai-deal-advisor`](./experts/mai-deal-advisor/) | [并购买卖，先问 MAI](./experts/mai-deal-advisor/) | MAI帮你理清并购方向、搭建报告、核验数字与股权表、监控港股公告，复杂判断再转交专业团队 | 无 |
| [`market-researcher`](./experts/market-researcher/) | [行业研究员](./experts/market-researcher/) | 面向分析师与基金经理的行业研究分析师,产出行业全景、竞争格局、可比公司估值表与主题选股清单等研究交付物。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`meeting-prep-agent`](./experts/meeting-prep-agent/) | [会前准备助理](./experts/meeting-prep-agent/) | 理财顾问的会议准备搭档,在每次客户见面前汇总关系历史、持仓近况、市场要闻与议题清单,让顾问 5 分钟进入状态。 | 可能需要启用对应 MCP / 连接器 |
| [`model-builder`](./experts/model-builder/) | [财务建模师](./experts/model-builder/) | 专业财务建模师,在 Excel 中从零搭建 DCF、LBO、三张表模型与可比公司估值,公式全链接、可追溯、机构级品控。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`month-end-closer`](./experts/month-end-closer/) | [月末结账会计](./experts/month-end-closer/) | 财务负责人的月末关账搭档,按清单跑应计、滚动表、差异说明,把关账包整理好交给 controller 签核。 | 可能需要启用对应 MCP / 连接器 |
| [`pitch-agent`](./experts/pitch-agent/) | [投行交易助理](./experts/pitch-agent/) | 资深投行关联人,从零搭建 pitch 初稿——可比公司、先例交易、DCF、足球场估值图,并生成绑在模型上的品牌化 PPT。 | 可能需要启用对应 MCP / 连接器 |
| [`private-equity`](./experts/private-equity/) | [私募股权专家](./experts/private-equity/) | 私募股权工具集：Deal Sourcing、项目筛选、尽调清单、IC Memo、单位经济学分析、回报分析、投后管理和价值创造方案 | 可能需要启用对应 MCP / 连接器 |
| [`smart-stock-analyst`](./experts/smart-stock-analyst/) | [多市场智能股票分析师](./experts/smart-stock-analyst/) | AI驱动多市场股票分析专家，内置缠论、波浪等15+策略，默认输出精美交互式HTML决策仪表盘报告 | 无（可选 API/账号以增强能力） |
| [`smb-finance`](./experts/smb-finance/) | [财务管家](./experts/smb-finance/) | 小企业财务管家，一站式搞定现金流预测、逾期追款、毛利分析、月结对账和税务准备 | 需要登录 / OAuth / 扫码授权 |
| [`statement-auditor`](./experts/statement-auditor/) | [LP 报表审核师](./experts/statement-auditor/) | LP 资本账户报表最后把关人,按基金 NAV 反算每条项目、对齐分配与管理费,发差前形成签核建议与异常清单。 | 可能需要启用对应 MCP / 连接器 |
| [`stock-partner-team`](./experts/stock-partner-team/) | [腾讯自选股股票投研专家团](./experts/stock-partner-team/) | 六位投研专家团，兼擅产业策略、信号捕捉、估值定价、逆向布局、基本面与短线，基于实时行情多视角研判。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；可能需要启用对应 MCP / 连接器；需要环境变量：`WESTOCK_SESSION_KEY` |
| [`strategy-backtest-expert`](./experts/strategy-backtest-expert/) | [量化策略回测师](./experts/strategy-backtest-expert/) | 把自然语言描述的交易策略转成可运行的 Python 回测脚本，输出标准指标、可视化图表、HTML 仪表盘，并给出实现细节、已知偏差和结果解读。 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要环境变量：`APIKEY` |
| [`tdx-stock-diagnostician`](./experts/tdx-stock-diagnostician/) | [个股深度诊断师](./experts/tdx-stock-diagnostician/) | 像经验丰富的分析师，对任意A股进行六大模块360度全方位诊断，涵盖基本面、技术面、资金面、事件催化、同业对标，输出专业诊断报告。 | 可能需要启用对应 MCP / 连接器 |
| [`tdx-stock-hunter`](./experts/tdx-stock-hunter/) | [智能选股猎手](./experts/tdx-stock-hunter/) | 基于通达信MCP数据，将自然语言转为多维筛选条件，从5000+A股中按基本面/技术面/资金面/估值做横向分析与综合评分，供用户参考。 | 可能需要启用对应 MCP / 连接器 |
| [`tdx-value-assessor`](./experts/tdx-value-assessor/) | [价值评估师](./experts/tdx-value-assessor/) | 秉承格雷厄姆-巴菲特价值体系，运用15+估值模型，通过护城河评估与多维估值分析，评估企业内在价值与安全边际水平。 | 可能需要启用对应 MCP / 连接器 |
| [`trading-agent`](./experts/trading-agent/) | [交易分析团队](./experts/trading-agent/) | 13位专业角色分5阶段协作完成投资分析：技术面、基本面、新闻面、情绪面数据采集 → 多空辩论 → 交易决策 → 三方风险评估 → 最终报告，输出 BUY/SELL/HOLD 建议… | 无 |
| [`valuation-reviewer`](./experts/valuation-reviewer/) | [组合估值主管](./experts/valuation-reviewer/) | PE/VC 基金组合估值主管,收 GP 估值包、跑标准估值模板、算基金 NAV 与 LP 分配、出 LP 报告草稿交投资者关系签核。 | 需要微信/企微相关凭证或扫码登录；可能需要启用对应 MCP / 连接器 |
| [`wealth-management`](./experts/wealth-management/) | [财富管理专家](./experts/wealth-management/) | 财富管理工具集：客户回顾、财务规划、投资组合再平衡、税损收割、投资提案和客户报告生成 | 可能需要启用对应 MCP / 连接器 |
| [`yahoo-finance-cli`](./experts/yahoo-finance-cli/) | [行情洞察与趋势发现专家](./experts/yahoo-finance-cli/) | 查询全球股票实时行情、基本面、财报预期、评级、历史走势与估值洞察，发现热门趋势标的，支持模糊检索与并排对比。 | 无 |

### 销售商务（14）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`cordys-crm`](./experts/cordys-crm/) | [Cordys CRM L2C 管道专家](./experts/cordys-crm/) | 角色感知型CRM助手，覆盖线索到现金全链路。自动识别角色，提供查询、风险预警与漏斗分析。 | 需要环境变量：`CORDYS_ACCESS_KEY`、`CORDYS_SECRET_KEY` |
| [`deal-strategist`](./experts/deal-strategist/) | [交易策略师](./experts/deal-strategist/) | 精通复杂交易策略制定和推进，帮助销售团队赢得大单 | 需要登录 / OAuth / 扫码授权；需要环境变量：`AUTH_TOKEN` |
| [`discovery-coach`](./experts/discovery-coach/) | [需求发现教练](./experts/discovery-coach/) | 训练销售掌握深度需求挖掘技巧，发现真正的业务痛点 | 无（可选 API/账号以增强能力） |
| [`enterprise-account-strategist`](./experts/enterprise-account-strategist/) | [大客户策略师](./experts/enterprise-account-strategist/) | 精通大客户经营和账户扩展策略，将客户发展为长期战略伙伴 | 无（可选 API/账号以增强能力） |
| [`government-digital-presales-consultant`](./experts/government-digital-presales-consultant/) | [政府数字化售前顾问](./experts/government-digital-presales-consultant/) | 精通政府数字化转型需求和采购流程 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要环境变量：`IMA_OPENAPI_APIKEY` |
| [`meituan-living-assistant`](./experts/meituan-living-assistant/) | [美团生活助手](./experts/meituan-living-assistant/) | 帮您一键领取美团优惠券，搜索附近团购美食并下单，探索今日活动，覆盖餐饮饮品等生活服务，省钱省心。 | 需要登录 / OAuth / 扫码授权；需要环境变量：`DEVICE_TOKEN`、`USER_TOKEN` |
| [`outbound-strategist`](./experts/outbound-strategist/) | [外呼策略师](./experts/outbound-strategist/) | 精通外呼和冷启动销售策略，让陌生人30秒内愿意继续倾听 | 无（可选 API/账号以增强能力） |
| [`presales-technical-consultant`](./experts/presales-technical-consultant/) | [售前技术顾问](./experts/presales-technical-consultant/) | 架起技术与商业的桥梁，帮助客户理解解决方案的价值 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录 |
| [`proposal-strategist`](./experts/proposal-strategist/) | [方案策划师](./experts/proposal-strategist/) | 精通销售提案和方案设计，将价值转化为无法拒绝的商业论证 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要登录 / OAuth / 扫码授权；需要环境变量：`BROWSER_USE_API_KEY` |
| [`sales-battle-team`](./experts/sales-battle-team/) | [销售作战团队](./experts/sales-battle-team/) | 销售攻坚体系，客户研究锁定目标、外联策略提升触达、竞品情报预警风险、销售预测优化资源分配 | 需要微信/企微相关凭证或扫码登录 |
| [`sales-coach`](./experts/sales-coach/) | [销售教练](./experts/sales-coach/) | 全栈销售教练：从能力培养到实战执行——会议准备、交易策略、商业案例、竞品分析、通话复盘，用苏格拉底式提问驱动 | 无（可选 API/账号以增强能力） |
| [`sales-pipeline-analyst`](./experts/sales-pipeline-analyst/) | [销售管道分析师](./experts/sales-pipeline-analyst/) | 用数据驱动方法分析销售管道健康度，让预测从猜测变科学 | 无 |
| [`smb-revenue`](./experts/smb-revenue/) | [营收增长师](./experts/smb-revenue/) | 小企业营收增长师，从线索打分到内容策略再到营销活动，一条龙驱动营收增长 | 需要微信/企微相关凭证或扫码登录 |
| [`uupt-delivery`](./experts/uupt-delivery/) | [同城配送助手](./experts/uupt-delivery/) | 提供UU跑腿同城即时配送与现场帮忙服务，支持订单询价、发单下单、订单查询取消及跑男实时追踪。 | 需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`UUPT_APP_SECRET` |

### 项目质量（23）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`accessibility-auditor`](./experts/accessibility-auditor/) | [无障碍审计师](./experts/accessibility-auditor/) | 按WCAG标准审计界面可访问性，确保每个用户都能使用产品 | 无 |
| [`agent-orchestrator`](./experts/agent-orchestrator/) | [智能体编排师](./experts/agent-orchestrator/) | 精通多智能体系统的编排和协调，让AI团队高效协作 | 需要登录 / OAuth / 扫码授权 |
| [`ai-meeting-notes`](./experts/ai-meeting-notes/) | [会议纪要提取专家](./experts/ai-meeting-notes/) | 粘贴会议笔记或转写文本，自动提炼摘要、负责人、截止日期与行动项，归档可检索并联动待办清单跟踪执行。 | 无 |
| [`api-testing-expert`](./experts/api-testing-expert/) | [API测试专家](./experts/api-testing-expert/) | 在用户之前发现API的每一个缺陷，确保接口稳定性和正确性 | 需要登录 / OAuth / 扫码授权 |
| [`document-generation-expert`](./experts/document-generation-expert/) | [文档生成专家](./experts/document-generation-expert/) | 自动化生成各类业务文档，大幅提升文档创建效率 | 无（可选 API/账号以增强能力） |
| [`document-skills`](./experts/document-skills/) | [文档处理专家](./experts/document-skills/) | 文档处理套件：Excel 电子表格、Word 文档、PowerPoint 演示文稿和 PDF 文件的创建、编辑与转换 | 无 |
| [`evidence-collector`](./experts/evidence-collector/) | [证据收集员](./experts/evidence-collector/) | 不放过任何没有截图证据的问题，用视觉证据确保缺陷无处遁形 | 无 |
| [`executive-summary-generator`](./experts/executive-summary-generator/) | [战略报告顾问](./experts/executive-summary-generator/) | 将冗长报告浓缩为高管可快速消化的精华摘要，节省每分钟 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`experiment-tracking-manager`](./experts/experiment-tracking-manager/) | [实验追踪管理者](./experts/experiment-tracking-manager/) | 系统化管理实验全生命周期，确保每个实验有假设有执行有结论 | 无 |
| [`internal-comms`](./experts/internal-comms/) | [内部沟通专家](./experts/internal-comms/) | 内部沟通模板专家：状态报告、领导汇报、公司简报、FAQ、事故报告和项目更新 | 无 |
| [`jira-workflow-admin`](./experts/jira-workflow-admin/) | [Jira工作流管理员](./experts/jira-workflow-admin/) | 精通Jira配置和敏捷工作流设计，让工具真正服务于团队效率 | 需要飞书应用凭证或用户登录授权；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权；需要环境变量：`TENCENTCLOUD_SECRET_KEY`、`TENCENTCLOUD_TOKEN` |
| [`openspec-doc-team`](./experts/openspec-doc-team/) | [专业文档生成团队](./experts/openspec-doc-team/) | 企业级长文档生成，4角色协作完成深度调研、大纲规划、内容撰写与合规审核全流程 | 无（可选 API/账号以增强能力） |
| [`performance-testing-expert`](./experts/performance-testing-expert/) | [性能测试专家](./experts/performance-testing-expert/) | 精通性能测试和基准评估，用数据证明性能改进而非凭感觉 | 需要登录 / OAuth / 扫码授权 |
| [`project-shepherd`](./experts/project-shepherd/) | [项目牧羊人](./experts/project-shepherd/) | 温和但坚定地引导项目按计划推进，确保里程碑准时交付 | 无 |
| [`reality-checker`](./experts/reality-checker/) | [现实检查员](./experts/reality-checker/) | 默认认为一切需要更多证据，需要压倒性证据才批准生产就绪 | 无 |
| [`senior-project-manager`](./experts/senior-project-manager/) | [高级项目经理](./experts/senior-project-manager/) | 10年以上项目管理经验，精通瀑布和敏捷，是复杂项目定海神针 | 无（可选 API/账号以增强能力） |
| [`studio-operations-manager`](./experts/studio-operations-manager/) | [工作室运营管理者](./experts/studio-operations-manager/) | 全面管理工作室日常运营，从资源调配到流程优化 | 无（可选 API/账号以增强能力） |
| [`studio-producer`](./experts/studio-producer/) | [工作室制片人](./experts/studio-producer/) | 统筹项目从立项到交付的全过程，平衡创意预算和时间 | 无 |
| [`technical-documentation-engineer`](./experts/technical-documentation-engineer/) | [技术文档工程师](./experts/technical-documentation-engineer/) | 将复杂技术概念转化为清晰准确的文档，让技术知识可传播 | 需要大模型 API Key（OpenAI/Anthropic 等）；需要微信/企微相关凭证或扫码登录；需要登录 / OAuth / 扫码授权 |
| [`test-results-analyst`](./experts/test-results-analyst/) | [测试结果分析师](./experts/test-results-analyst/) | 像侦探解读证据一样分析测试结果，发现隐藏的质量问题 | 需要登录 / OAuth / 扫码授权 |
| [`tool-evaluation-expert`](./experts/tool-evaluation-expert/) | [工具评估专家](./experts/tool-evaluation-expert/) | 系统化评估推荐最适合团队的工具，避免浪费时间在错误工具上 | 无（可选 API/账号以增强能力） |
| [`webapp-testing`](./experts/webapp-testing/) | [Web应用测试专家](./experts/webapp-testing/) | Web 应用测试助手，引导用户完成 Web 应用的启动、配置和测试流程 | 需要登录 / OAuth / 扫码授权 |
| [`workflow-optimization-expert`](./experts/workflow-optimization-expert/) | [工作流优化专家](./experts/workflow-optimization-expert/) | 找到瓶颈修复流程自动化一切，让团队效率最大化 | 无（可选 API/账号以增强能力） |

## 4. 插件市场 `plugins/`

- 官方插件 `plugins/codebuddy-plugins-official/plugins/`：**57**
- 团队插件 `plugins/cb_teams_marketplace/plugins/`：**30**

### 官方插件

| 目录 | 说明 |
|------|------|
| [`agent-browser`](./plugins/codebuddy-plugins-official/plugins/agent-browser/) | 用途：Browser automation plugin for CodeBuddy using `vercel-labs/agent-browser` CLI, with fi… |
| [`agent-sdk-dev`](./plugins/codebuddy-plugins-official/plugins/agent-sdk-dev/) | 用于创建和验证 CodeBuddy Agent SDK 应用的综合开发插件。 |
| [`agent-team-agile-workflow`](./plugins/codebuddy-plugins-official/plugins/agent-team-agile-workflow/) | 完整的 BMAD 敏捷工作流插件，包含角色化代理（PO、架构师、SM、开发、QA）和交互式审批流程 |
| [`algorithmic-art`](./plugins/codebuddy-plugins-official/plugins/algorithmic-art/) | 使用 p5.js 创建算法艺术，支持种子随机性和交互式参数探索。适用于生成艺术、流场、粒子系统等代码艺术创作。 |
| [`atuin`](./plugins/codebuddy-plugins-official/plugins/atuin/) | 自动拦截 AI 的高危操作，自动阻止 AI 使用有漏洞的组件。腾讯玄武实验室出品。 |
| [`chainguard`](./plugins/codebuddy-plugins-official/plugins/chainguard/) | 自动拦截 AI 依赖安装操作，进行供应链安全审计。 |
| [`clangd-lsp`](./plugins/codebuddy-plugins-official/plugins/clangd-lsp/) | C/C++ Language Server (clangd)，为 CodeBuddy 提供代码智能、诊断和格式化功能。 |
| [`cloudbase`](./plugins/codebuddy-plugins-official/plugins/cloudbase/) | CloudBase AI 开发插件，提供 Web、小程序、云函数、CloudRun、数据库（NoSQL/MySQL）、云存储、AI 模型、UI 设计等全栈开发能力。 |
| [`code-simplifier`](./plugins/codebuddy-plugins-official/plugins/code-simplifier/) | 专注于简化代码以提升清晰度、一致性和可维护性的智能代理,在保留完整功能的前提下优化代码结构。主要关注最近修改的代码。 |
| [`codebuddy-md-management`](./plugins/codebuddy-plugins-official/plugins/codebuddy-md-management/) | 用途：Tools to maintain and improve CODEBUDDY.md files - audit quality, capture session lear… |
| [`commit-commands`](./plugins/codebuddy-plugins-official/plugins/commit-commands/) | 用途：Streamline your git workflow with simple commands for committing, pushing, and creatin… |
| [`context7`](./plugins/codebuddy-plugins-official/plugins/context7/) | Upstash Context7 MCP 服务器，用于查找最新文档。可直接从源代码仓库拉取特定版本的文档和代码示例到 LLM 上下文中。 |
| [`csharp-lsp`](./plugins/codebuddy-plugins-official/plugins/csharp-lsp/) | C# Language Server，为 CodeBuddy 提供代码智能和诊断功能。 |
| [`development-essentials`](./plugins/codebuddy-plugins-official/plugins/development-essentials/) | 核心开发命令套件，提供日常开发所需的所有基础命令。无需工作流开销，直接执行开发任务。 |
| [`doc-coauthoring`](./plugins/codebuddy-plugins-official/plugins/doc-coauthoring/) | 引导用户通过结构化工作流协作撰写文档。适用于编写文档、提案、技术规格、决策文档等结构化内容，帮助高效传递上下文、迭代优化内容并验证文档的可读性。 |
| [`docx`](./plugins/codebuddy-plugins-official/plugins/docx/) | 全面的 Word 文档创建、编辑和分析工具，支持修订跟踪、评论、格式保留和文本提取。用于处理专业 Word 文档(.docx) |
| [`feature-dev`](./plugins/codebuddy-plugins-official/plugins/feature-dev/) | 用途：A comprehensive, structured workflow for feature development with specialized agents f… |
| [`find-skills`](./plugins/codebuddy-plugins-official/plugins/find-skills/) | 帮助用户发现和安装 AI Agent 技能，支持从 Vercel Skills 和 ClawHub 两个技能仓库搜索和安装 |
| [`firebase`](./plugins/codebuddy-plugins-official/plugins/firebase/) | Google Firebase MCP 集成。管理 Firestore 数据库、身份验证、云函数、托管服务和存储。直接从开发工作流中构建和管理 Firebase 后端。 |
| [`frontend-design`](./plugins/codebuddy-plugins-official/plugins/frontend-design/) | 创建独特的生产级前端界面,具有高设计质量。生成富有创意、精致的代码,避免千篇一律的AI审美。 |
| [`github`](./plugins/codebuddy-plugins-official/plugins/github/) | 官方 GitHub MCP 服务器，用于仓库管理。可直接在 Claude Code 中创建议题、管理拉取请求、审查代码、搜索仓库以及调用 GitHub 完整 API。 |
| [`gitlab`](./plugins/codebuddy-plugins-official/plugins/gitlab/) | GitLab DevOps 平台集成。管理代码仓库、合并请求、CI/CD 流水线、问题和 Wiki。全面访问 GitLab 的 DevOps 生命周期工具。 |
| [`godot-mcp`](./plugins/codebuddy-plugins-official/plugins/godot-mcp/) | 用途：A comprehensive integration between Godot Engine and AI assistants using the Model Con… |
| [`gopls-lsp`](./plugins/codebuddy-plugins-official/plugins/gopls-lsp/) | Go Language Server，为 CodeBuddy 提供代码智能、重构和分析功能。 |
| [`hookify`](./plugins/codebuddy-plugins-official/plugins/hookify/) | 用途：Easily create custom hooks to prevent unwanted behaviors by analyzing conversation pat… |
| [`hot-skills`](./plugins/codebuddy-plugins-official/plugins/hot-skills/) | 用途：A curated collection of 7 top-downloaded AI agent skills, bundled into a single plugin… |
| [`jdtls-lsp`](./plugins/codebuddy-plugins-official/plugins/jdtls-lsp/) | Java Language Server (Eclipse JDT.LS)，为 CodeBuddy 提供代码智能和重构功能。 |
| [`lexiang-knowledge-plugins`](./plugins/codebuddy-plugins-official/plugins/lexiang-knowledge-plugins/) | 乐享知识库, 企业协同知识库，提供获取文档内容与元数据、搜索文档内容、查询知识库与目录结构、创建/编辑/移动文档、管理标签与评论、上传文件及维护附件等知识库操作能力。 |
| [`lua-lsp`](./plugins/codebuddy-plugins-official/plugins/lua-lsp/) | Lua Language Server，为 CodeBuddy 提供代码智能和诊断功能。 |
| [`lucide-icons`](./plugins/codebuddy-plugins-official/plugins/lucide-icons/) | 用途：A CodeBuddy skill for searching, downloading, and customizing [Lucide icons](https://l… |
| [`magicai-hub`](./plugins/codebuddy-plugins-official/plugins/magicai-hub/) | Godot 4.x 游戏开发 AI 技能工具包。为 CodeBuddy 提供一组专业技能，帮助 AI 更高效地协助 Godot 项目开发。 |
| [`oh-my-codebuddy`](./plugins/codebuddy-plugins-official/plugins/oh-my-codebuddy/) | 完整的 OMC (Oh My CodeBuddy) 插件，包含 agents、commands、skills、hooks、tools 和 MCP servers。提供多代理编排、… |
| [`pdf`](./plugins/codebuddy-plugins-official/plugins/pdf/) | 全面的 PDF 处理工具包，支持提取文本和表格、创建新 PDF、合并/拆分文档、表单填写、加密解密、OCR 扫描等功能 |
| [`php-lsp`](./plugins/codebuddy-plugins-official/plugins/php-lsp/) | PHP Language Server (Intelephense)，为 CodeBuddy 提供代码智能和诊断功能。 |
| [`playwright-cli`](./plugins/codebuddy-plugins-official/plugins/playwright-cli/) | 用途：Playwright CLI with SKILLS |
| [`plugin-dev`](./plugins/codebuddy-plugins-official/plugins/plugin-dev/) | 用途：A comprehensive toolkit for developing CodeBuddy Code plugins with expert guidance on … |
| [`plugin-finder`](./plugins/codebuddy-plugins-official/plugins/plugin-finder/) | 智能插件发现和管理助手，帮助用户从众多插件市场中轻松发现、安装和比较插件。 |
| [`ppt-writer`](./plugins/codebuddy-plugins-official/plugins/ppt-writer/) | 一个功能强大的CodeBuddy Code插件，帮助你快速创建专业、美观、有说服力的PPT演示文稿。 |
| [`pptx`](./plugins/codebuddy-plugins-official/plugins/pptx/) | PowerPoint 演示文稿创建、编辑和分析技能。支持创建新演示文稿、修改内容、处理布局、添加注释或演讲者备注等操作 |
| [`pr-review-toolkit`](./plugins/codebuddy-plugins-official/plugins/pr-review-toolkit/) | 用途：A comprehensive collection of specialized agents for thorough pull request review, cov… |
| [`pyright-lsp`](./plugins/codebuddy-plugins-official/plugins/pyright-lsp/) | Python Language Server (Pyright)，为 CodeBuddy 提供静态类型检查和代码智能功能。 |
| [`ralph-loop`](./plugins/codebuddy-plugins-official/plugins/ralph-loop/) | 用途：Implementation of the Ralph Wiggum technique for iterative, self-referential AI develo… |
| [`requirements-driven-workflow`](./plugins/codebuddy-plugins-official/plugins/requirements-driven-workflow/) | 需求驱动开发工作流，包含 90% 质量门控的实用功能实现流程 |
| [`rust-analyzer-lsp`](./plugins/codebuddy-plugins-official/plugins/rust-analyzer-lsp/) | Rust Language Server，为 CodeBuddy 提供代码智能和分析功能。 |
| [`security-guidance`](./plugins/codebuddy-plugins-official/plugins/security-guidance/) | 安全提醒钩子，在编辑文件时警告潜在的安全问题，包括命令注入、XSS 和不安全的代码模式 |
| [`security-rules`](./plugins/codebuddy-plugins-official/plugins/security-rules/) | 安全三部安全 rules 插件 |
| [`security-scan`](./plugins/codebuddy-plugins-official/plugins/security-scan/) | 一款智能代码安全审计工具，通过 **语义索引 + 多 Agent 并行扫描 + 对抗验证** 实现专业级漏洞发现。支持 **全链路 --auto 无人值守模式 + 安全门禁 + … |
| [`serena`](./plugins/codebuddy-plugins-official/plugins/serena/) | 语义代码分析 MCP 服务器，通过语言服务器协议集成提供智能代码理解、重构建议和代码库导航功能。 |
| [`skills-security-check`](./plugins/codebuddy-plugins-official/plugins/skills-security-check/) | 腾讯云鼎实验室出品，Skill安全审查工具。本skill用于对用户指定的skill.md文件、及其配套的文档、程序、脚本等做安全审查，确保引用安全 |
| [`supabase`](./plugins/codebuddy-plugins-official/plugins/supabase/) | Supabase MCP 集成，用于数据库操作、身份验证、存储和实时订阅。管理您的 Supabase 项目，运行 SQL 查询，并直接与后端交互。 |
| [`swift-lsp`](./plugins/codebuddy-plugins-official/plugins/swift-lsp/) | Swift Language Server (SourceKit-LSP)，为 CodeBuddy 提供 Swift 项目的代码智能功能。 |
| [`testbuddy`](./plugins/codebuddy-plugins-official/plugins/testbuddy/) | 文本测试用例生成插件。主要用于文本测试用例生成、文本测试用例框架生成、脑图用例生成、召回、需求分析等文本测试用例生成 |
| [`tmap-lbs-plugin`](./plugins/codebuddy-plugins-official/plugins/tmap-lbs-plugin/) | 腾讯地图位置服务开发插件，提供 JavaScript GL 地图开发指南和 Web 服务 API（POI搜索、路径规划、旅游规划、轨迹可视化等）能力。 |
| [`typescript-lsp`](./plugins/codebuddy-plugins-official/plugins/typescript-lsp/) | TypeScript/JavaScript Language Server，为 CodeBuddy 提供跳转定义、查找引用、错误检查等代码智能功能。 |
| [`web-artifacts-builder`](./plugins/codebuddy-plugins-official/plugins/web-artifacts-builder/) | 使用现代前端技术（React、Tailwind CSS、shadcn/ui）创建复杂多组件 HTML 工件的工具套件。适用于需要状态管理、路由或 shadcn/ui 组件的复杂工… |
| [`weixin-minigame-helper`](./plugins/codebuddy-plugins-official/plugins/weixin-minigame-helper/) | 微信小游戏 AI 开发助手 —— 预览、调试、真机测试、发布一站式解决。 |
| [`xlsx`](./plugins/codebuddy-plugins-official/plugins/xlsx/) | 全面的电子表格创建、编辑和分析工具，支持公式、格式化、数据分析和可视化。适用于 .xlsx、.xlsm、.csv、.tsv 等表格文件的处理 |

### 团队插件

| 目录 | 说明 |
|------|------|
| [`a-share-analysis`](./plugins/cb_teams_marketplace/plugins/a-share-analysis/) | A股投资分析技能集，覆盖宏观研究、市场结构、个股深度、行业比较、资金行为、风险管理等 21 个专业分析 skill 和 6 个编排 agent。 |
| [`agent-sdk-dev`](./plugins/cb_teams_marketplace/plugins/agent-sdk-dev/) | 用于创建和验证 CodeBuddy Agent SDK 应用的综合开发插件。 |
| [`ai-hedge-fund`](./plugins/cb_teams_marketplace/plugins/ai-hedge-fund/) | AI 对冲基金投资分析系统：19位投资大师并行分析 + 风险管理 + 投资组合决策的全流程投资分析。涵盖巴菲特、芒格、林奇、伯里、塔勒布、伍德、格雷厄姆等13位传奇投资哲学家 +… |
| [`ardot-design-generator`](./plugins/cb_teams_marketplace/plugins/ardot-design-generator/) | `ardot-design-generator` 是一个面向 Ardot 画布的 CodeBuddy 插件，通过 MCP（Model Context Protocol）对接 Ar… |
| [`codebuddy-chat-web`](./plugins/cb_teams_marketplace/plugins/codebuddy-chat-web/) | 用途：Initialize a complete web-based chat application powered by CodeBuddy Agent SDK. |
| [`data`](./plugins/cb_teams_marketplace/plugins/data/) | 数据分析插件，支持 SQL 查询、数据探索、可视化、仪表板构建和洞察生成。包含完整的数据分析工作流程和最佳实践。 |
| [`data-analysis`](./plugins/cb_teams_marketplace/plugins/data-analysis/) | 用途：Data analysis plugin with Excel spreadsheet creation, editing, and analysis capabiliti… |
| [`deep-research`](./plugins/cb_teams_marketplace/plugins/deep-research/) | 用途：Deep research plugin that enables comprehensive web research, information synthesis, a… |
| [`design-to-code`](./plugins/cb_teams_marketplace/plugins/design-to-code/) | 将 Figma 设计文件和 UI 截图转换为生产就绪的代码组件，内置无障碍性支持。 |
| [`dockerfile-gen`](./plugins/cb_teams_marketplace/plugins/dockerfile-gen/) | 用途：Dockerfile Generator - Automated Dockerfile generation with best practices for contain… |
| [`document-skills`](./plugins/cb_teams_marketplace/plugins/document-skills/) | 用途：Collection of document processing suite including Excel, Word, PowerPoint, and PDF cap… |
| [`equity-research`](./plugins/cb_teams_marketplace/plugins/equity-research/) | 用途：Equity research tools: earnings analysis, initiating coverage reports, and research wo… |
| [`executing-marketing-campaigns`](./plugins/cb_teams_marketplace/plugins/executing-marketing-campaigns/) | 用途：A comprehensive Claude skill designed to help marketing teams plan, execute, and measu… |
| [`finance`](./plugins/cb_teams_marketplace/plugins/finance/) | 财务与会计插件，支持月末结账、日记账分录、账户核对、财务报表生成、差异分析和 SOX 审计支持。 |
| [`financial-analysis`](./plugins/cb_teams_marketplace/plugins/financial-analysis/) | 用途：Core financial modeling and analysis tools: DCF, comps, LBO, 3-statement models, compe… |
| [`gaokao-advisor`](./plugins/cb_teams_marketplace/plugins/gaokao-advisor/) | 面向高考真题/作文、全国高校与专业信息检索、地区批次线查询、一分一段/位次查询和志愿填报参考。 |
| [`general-skills`](./plugins/cb_teams_marketplace/plugins/general-skills/) | 用途：A collection of general-purpose skills for CodeBuddy Code. |
| [`internal-comms`](./plugins/cb_teams_marketplace/plugins/internal-comms/) | 用途：A set of resources to help write internal communications using company-preferred forma… |
| [`investment-banking`](./plugins/cb_teams_marketplace/plugins/investment-banking/) | 用途：Investment banking productivity tools for equity research, valuation, presentations, a… |
| [`lseg`](./plugins/cb_teams_marketplace/plugins/lseg/) | 用途：Price bonds, analyze yield curves, evaluate FX carry trades, value options, and build … |
| [`modern-webapp`](./plugins/cb_teams_marketplace/plugins/modern-webapp/) | 用途：Modern web application development plugin with React, TypeScript, Vite, Tailwind CSS, … |
| [`ppt-implement`](./plugins/cb_teams_marketplace/plugins/ppt-implement/) | 智能 PPT 生成助手，一键将您的想法转化为精美演示文稿 |
| [`private-equity`](./plugins/cb_teams_marketplace/plugins/private-equity/) | 用途：Private equity deal sourcing and workflow tools: company discovery, CRM integration, a… |
| [`product-management`](./plugins/cb_teams_marketplace/plugins/product-management/) | 产品管理插件覆盖完整的 PM 工作流程：编写功能规格、管理产品路线图、与利益相关者沟通、综合用户研究、分析竞品和审查产品指标。 |
| [`remotion-video-generator`](./plugins/cb_teams_marketplace/plugins/remotion-video-generator/) | 用途：Automatically generate beautiful, production-quality videos using Remotion with minima… |
| [`skill-creator`](./plugins/cb_teams_marketplace/plugins/skill-creator/) | 提供创建高效 Claude 技能的指南,通过专业知识、工作流程和工具集成来扩展 AI 助手的能力 |
| [`spglobal`](./plugins/cb_teams_marketplace/plugins/spglobal/) | 用途：S&P Global - Financial data and analytics skills including company tearsheets, earning… |
| [`trading-agent`](./plugins/cb_teams_marketplace/plugins/trading-agent/) | 交易智能体插件：基于多角色辩论方法论的系统性投资分析，涵盖市场技术分析、基本面分析、新闻与情绪分析、多空辩论、交易决策与三方风险评估全流程，输出 BUY/SELL/HOLD 建议… |
| [`wealth-management`](./plugins/cb_teams_marketplace/plugins/wealth-management/) | 用途：Wealth management and financial advisory tools: client reviews, financial planning, po… |
| [`webapp-testing`](./plugins/cb_teams_marketplace/plugins/webapp-testing/) | 智能引导式 Web 应用测试助手，帮助你快速启动、配置和测试 Web 应用。自动分析项目结构，检测运行环境，配合 `agent-browser` 进行浏览器自动化测试。 |

