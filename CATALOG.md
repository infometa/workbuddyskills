# workbuddyskills 完整清单（中文说明）

每个条目包含：**用来做什么**、**前置条件**（API Key / 登录认证等）。目录与名称**可点击**跳转。

**前置条件 = 无**：一般不需额外密钥或登录即可阅读/使用说明；调用外部服务时平台侧仍可能有限制。

- 技能包：**295** · 连接器：**66** · 专家：**350** · 官方插件：**57** · 团队插件：**30**

> 清单自动同步自 WorkBuddy 公开市场；最近同步：2026-07-22

---
## 目录

1. [技能包 skills/](#1-技能包-skills)
2. [连接器 connectors/](#2-连接器-connectors)
3. [专家包 experts/](#3-专家包-experts)
4. [插件市场 plugins/](#4-插件市场-plugins)

## 1. 技能包 `skills/`

### AI / Agent 工具（51）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`12306`](./skills/12306/) | [12306](./skills/12306/SKILL.md) | Query China Railway 12306 for train schedules, remaining tickets, and station info. Use when user… | 需要 12306 账号登录 |
| [`12306-train-assistant`](./skills/12306-train-assistant/) | [12306-train-assistant](./skills/12306-train-assistant/SKILL.md) | 12306 查询与订票辅助技能，支持余票查询、经停站查询、中转换乘、候补查询与提交/取消、登录状态检查、密码登录与二维码登录、下单与支付链接获取；当用户提到火车票、高铁票、经停站、中转、候补或 … | 需要 12306 账号登录；需要环境变量：`KYFW_PASSWORD` |
| [`agent-mbti`](./skills/agent-mbti/) | [agent-mbti](./skills/agent-mbti/SKILL.md) | 用于：基于 MBTI 框架的 AI Agent 人格诊断系统。 | 无 |
| [`agent-team-orchestration`](./skills/agent-team-orchestration/) | [agent-team-orchestration](./skills/agent-team-orchestration/SKILL.md) | 用途：Orchestrate multi-agent teams with defined roles, task lifecycles, handoff protocols, and review wor。 | 无 |
| [`ai-shifu-course-creator`](./skills/ai-shifu-course-creator/) | [ai-shifu-course-creator](./skills/ai-shifu-course-creator/SKILL.md) | Use when the user works with AI-Shifu (AI师傅) courses in any capacity of creating, writing, editin… | 需要环境变量：`SHIFU_TOKEN` |
| [`aihot`](./skills/aihot/) | [aihot](./skills/aihot/SKILL.md) | AI HOT (aihot.virxact.com) 中文 AI 资讯查询 Skill。 | 无 |
| [`airchina-travel-assistant`](./skills/airchina-travel-assistant/) | [airchina-travel-assistant](./skills/airchina-travel-assistant/SKILL.md) | 用于：帮用户领取中国国航（Air China / 国航 / 国际航空）的优惠券。 | 无（可选 API/账号以增强能力） |
| [`anti-distill`](./skills/anti-distill/) | [anti-distill](./skills/anti-distill/SKILL.md) | > **Language / 语言**: This skill supports both English and Chinese. Detect the user's language fro… | 无 |
| [`arxiv-reader`](./skills/arxiv-reader/) | [arxiv-reader](./skills/arxiv-reader/SKILL.md) | 用于：利用python，指定某个arxiv_id/url， 基于 LLM Agent 对这篇arxiv论文进行分类与深度阅读，直接print打印阅读笔记。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`LLM_API_KEY` |
| [`aviationstack-flight-tracker`](./skills/aviationstack-flight-tracker/) | [aviationstack-flight-tracker](./skills/aviationstack-flight-tracker/SKILL.md) | 用途：Track flights in real-time with detailed status, gate info, delays, and live position。 | 需要环境变量：`AVIATIONSTACK_API_KEY` |
| [`boss-skills`](./skills/boss-skills/) | [boss-skills](./skills/boss-skills/SKILL.md) | 用途：Distill a real boss into an AI skill, or generate a boss skill from famous entrepreneur archetypes (。 | 无 |
| [`cangjie-skill`](./skills/cangjie-skill/) | [cangjie-skill](./skills/cangjie-skill/SKILL.md) | Distill a book into a coherent set of executable skills. Use when the user asks to "拆书" / "蒸馏一本书"… | 无 |
| [`capability-evolver`](./skills/capability-evolver/) | [capability-evolver](./skills/capability-evolver/SKILL.md) | 用途：A self-evolution engine for AI agents。 | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`cli-anything-hub`](./skills/cli-anything-hub/) | [cli-anything-hub](./skills/cli-anything-hub/SKILL.md) | 用途：Discover agent-native CLIs for professional software。 | 无 |
| [`colleague-skill`](./skills/colleague-skill/) | [colleague-skill](./skills/colleague-skill/SKILL.md) | > **Language / 语言**: This skill supports both English and Chinese. Detect the user's language fro… | 需要微信公众号/开放平台 AppID 与 AppSecret；需要飞书应用凭证或用户登录授权；需要环境变量：`FEISHU_APP_SECRET`、`FEISHU_USER_ACCESS_TOKEN` |
| [`conversion-ops`](./skills/conversion-ops/) | [conversion-ops](./skills/conversion-ops/SKILL.md) | 用途：AI Conversion Ops。 | 无（可选 API/账号以增强能力） |
| [`crash-expert-skill`](./skills/crash-expert-skill/) | [crash-expert-skill](./skills/crash-expert-skill/SKILL.md) | 本技能提供 Linux 内核 vmcore 深度分析的完整工作流，结合 AiCrasher MCP 工具实现自动化 crash 调试。 | 无 |
| [`deck-generator`](./skills/deck-generator/) | [deck-generator](./skills/deck-generator/SKILL.md) | 用途：Generate professional presentations with AI-generated images。 | 需要环境变量：`GEMINI_API_KEY` |
| [`didi-ride-skill`](./skills/didi-ride-skill/) | [didi-ride-skill](./skills/didi-ride-skill/SKILL.md) | 用于：中国城市出行服务。 | 无（可选 API/账号以增强能力） |
| [`edgeone`](./skills/edgeone/) | [edgeone](./skills/edgeone/SKILL.md) | MCP 工具相关。 | 无 |
| [`english-exam-writing-reviewer`](./skills/english-exam-writing-reviewer/) | [english-exam-writing-reviewer](./skills/english-exam-writing-reviewer/SKILL.md) | 用于：可追溯的中国主流英语考试作文批改 Skill。 | 无 |
| [`globepilot-ai-agent-2`](./skills/globepilot-ai-agent-2/) | [globepilot-ai-agent-2](./skills/globepilot-ai-agent-2/SKILL.md) | 用途：AI-powered global travel assistant providing visa info, currency conversion, airport status, events,。 | 无 |
| [`goal-tracker`](./skills/goal-tracker/) | [goal-tracker](./skills/goal-tracker/SKILL.md) | 用途：Track long-term goals with milestones, daily logging, and accountability。 | 无 |
| [`guizang-ppt-skill`](./skills/guizang-ppt-skill/) | [guizang-ppt-skill](./skills/guizang-ppt-skill/SKILL.md) | 生成横向翻页网页 PPT（单 HTML 文件），含 WebGL 背景、章节幕封、数据大字报、图片网格等模板。 | 无 |
| [`handoff`](./skills/handoff/) | [handoff](./skills/handoff/SKILL.md) | 用途：Compact the current conversation into a handoff document for another agent to pick up。 | 无 |
| [`humanizer`](./skills/humanizer/) | [humanizer](./skills/humanizer/SKILL.md) | 用途：Remove signs of AI-generated writing from text。 | 无 |
| [`khazix-writer`](./skills/khazix-writer/) | [khazix-writer](./skills/khazix-writer/SKILL.md) | 用于：数字生命卡兹克（Khazix）的公众号长文写作skill。 | 无 |
| [`lexiang-knowledge-base`](./skills/lexiang-knowledge-base/) | [lexiang-knowledge-base](./skills/lexiang-knowledge-base/SKILL.md) | 用于访问乐享知识库平台的专用 skill。 | 需要环境变量：`LEXIANG_TOKEN` |
| [`llm-wiki`](./skills/llm-wiki/) | [llm-wiki](./skills/llm-wiki/SKILL.md) | 用途：Build and maintain a personal knowledge base (wiki) using LLMs。 | 无 |
| [`markitdown-skill`](./skills/markitdown-skill/) | [markitdown-skill](./skills/markitdown-skill/SKILL.md) | 用途：Convert documents to Markdown using Microsoft's MarkItDown CLI (`markitdown`)。 | 无 |
| [`mcp-builder`](./skills/mcp-builder/) | [mcp-builder](./skills/mcp-builder/SKILL.md) | MCP 工具相关。 | 无（可选 API/账号以增强能力） |
| [`mcporter`](./skills/mcporter/) | [mcporter](./skills/mcporter/SKILL.md) | MCP 工具相关。 | 无 |
| [`news-summary`](./skills/news-summary/) | [news-summary](./skills/news-summary/SKILL.md) | 用途：This skill should be used when the user asks for news updates, daily briefings, or what's happening 。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`OPENAI_API_KEY` |
| [`novel-writer`](./skills/novel-writer/) | [novel-writer](./skills/novel-writer/SKILL.md) | 章节正文生成器 - 根据章节大纲、Voice Profile 和角色档案构建 LLM 提示词，用于生成章节正文。 | 无（可选 API/账号以增强能力） |
| [`novel-writing`](./skills/novel-writing/) | [novel-writing](./skills/novel-writing/SKILL.md) | 用于：AI长篇网文创作技能包。 | 无 |
| [`nuwa-skill`](./skills/nuwa-skill/) | [nuwa-skill](./skills/nuwa-skill/SKILL.md) | 女娲造人：输入人名/主题/甚至只是模糊需求，自动深度调研→思维框架提炼→生成可运行的人物Skill。 | 无 |
| [`obsidian`](./skills/obsidian/) | [obsidian](./skills/obsidian/SKILL.md) | 用途：Work with Obsidian vaults (plain Markdown notes) and automate via obsidian-cli。 | 无 |
| [`openclaw-assets-to-workbuddy`](./skills/openclaw-assets-to-workbuddy/) | [openclaw-assets-to-workbuddy](./skills/openclaw-assets-to-workbuddy/SKILL.md) | 将 OpenClaw 用户的个人资产迁移到 WorkBuddy 对应位置，重点覆盖 SOUL.md、IDENTITY.md、USER.md、memory、skills、MCP 配置、bot/ch… | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`oracle`](./skills/oracle/) | [oracle](./skills/oracle/SKILL.md) | 用途：Use the @steipete/oracle CLI to bundle a prompt plus the right files and get a second-model review (。 | 无 |
| [`paper-quick-reader`](./skills/paper-quick-reader/) | [paper-quick-reader](./skills/paper-quick-reader/SKILL.md) | 用于：AI 论文速读 Skill：三档深度（裸读 / 引导 / 精读）+ 页码级 Provenance 防幻觉 + 多篇对比。 | 无（可选 API/账号以增强能力） |
| [`promo-creator-skills`](./skills/promo-creator-skills/) | [promo-creator-skills](./skills/promo-creator-skills/SKILL.md) | 用于：产品宣传片制作总控 skill pack。 | 需要环境变量：`MUREKA_API_KEY` |
| [`resume-assistant`](./skills/resume-assistant/) | [resume-assistant](./skills/resume-assistant/SKILL.md) | 面向中国求职者（应届 / 社招 / 出海）的可追溯 JD 定制简历助手：从 master 简历派生多版本，按 JD 重写并标注三维度防幻觉证据 （不编造数字 / 合法改写 / 防 AI 味），输… | 无 |
| [`revenue-intelligence`](./skills/revenue-intelligence/) | [revenue-intelligence](./skills/revenue-intelligence/SKILL.md) | 用途：AI Revenue Intelligence。 | 需要环境变量：`AHREFS_TOKEN`、`GONG_API_KEY`、`HUBSPOT_API_KEY` |
| [`sales-pipeline`](./skills/sales-pipeline/) | [sales-pipeline](./skills/sales-pipeline/SKILL.md) | 用途：AI Sales Pipeline。 | 需要环境变量：`BRAVE_API_KEY`、`CRM_API_KEY`、`HUBSPOT_API_KEY`、`HUBSPOT_TOKEN`、`INSTANTLY_API_KEY` 等 |
| [`sales-playbook`](./skills/sales-playbook/) | [sales-playbook](./skills/sales-playbook/SKILL.md) | 用途：AI Sales Playbook — Value-Based Pricing & Deal Upselling。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`AHREFS_API_KEY`、`ANTHROPIC_API_KEY`、`OPENAI_API_KEY`、`SEMRUSH_API_KEY` |
| [`seo-ops`](./skills/seo-ops/) | [seo-ops](./skills/seo-ops/SKILL.md) | 用途：AI SEO Ops。 | 需要环境变量：`AHREFS_TOKEN`、`BRAVE_API_KEY`、`CLIENT_SECRET`、`GOOGLE_CLIENT_ID`、`GOOGLE_CLIENT_SECRET` |
| [`skill-creator`](./skills/skill-creator/) | [skill-creator](./skills/skill-creator/SKILL.md) | 用途：Guide for creating effective skills。 | 无 |
| [`skill-vetter`](./skills/skill-vetter/) | [skill-vetter](./skills/skill-vetter/SKILL.md) | 用途：Security-first skill vetting for AI agents。 | 无 |
| [`the-entrepreneurship-handbook`](./skills/the-entrepreneurship-handbook/) | [the-entrepreneurship-handbook](./skills/the-entrepreneurship-handbook/SKILL.md) | Q&A skill for entrepreneurs, managers, and business leaders. Triggers when users ask about entrep… | 无 |
| [`workbuddy-asset-migration`](./skills/workbuddy-asset-migration/) | [workbuddy-asset-migration](./skills/workbuddy-asset-migration/SKILL.md) | 在 WorkBuddy 国内版（~/.workbuddy/）和海外版（~/.workbuddy-ai/）之间，或跨机器之间，迁移用户个人资产（skills、memory、conversation… | 无（可选 API/账号以增强能力） |
| [`yourself-skill`](./skills/yourself-skill/) | [yourself-skill](./skills/yourself-skill/SKILL.md) | > **Language / 语言**: This skill supports both English and Chinese. Detect the user's language fro… | 无 |

### 云 / 存储 / 部署（1）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`healthcheck`](./skills/healthcheck/) | [healthcheck](./skills/healthcheck/SKILL.md) | 用途：Track water and sleep with JSON file storage。 | 无 |

### 其他（56）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`academic-translation`](./skills/academic-translation/) | [academic-translation](./skills/academic-translation/SKILL.md) | 用于：当用户需要学术论文中英互译、润色、Chinglish 修复时使用。 | 无 |
| [`academic-tutor`](./skills/academic-tutor/) | [academic-tutor](./skills/academic-tutor/SKILL.md) | 用于：当大学生问题目、需要苏格拉底式引导讲解、或论文写作指导时使用。 | 无 |
| [`apple-reminders`](./skills/apple-reminders/) | [apple-reminders](./skills/apple-reminders/SKILL.md) | 用途：Manage Apple Reminders via the `remindctl` CLI on macOS (list, add, edit, complete, delete)。 | 无 |
| [`aviation-weather`](./skills/aviation-weather/) | [aviation-weather](./skills/aviation-weather/SKILL.md) | 用途：Fetch aviation weather data (METAR, TAF, PIREPs) from aviationweather。 | 无 |
| [`blogwatcher`](./skills/blogwatcher/) | [blogwatcher](./skills/blogwatcher/SKILL.md) | 用途：Monitor blogs and RSS/Atom feeds for updates using the blogwatcher CLI。 | 无 |
| [`brand-guidelines`](./skills/brand-guidelines/) | [brand-guidelines](./skills/brand-guidelines/SKILL.md) | 用途：Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit fr。 | 无 |
| [`caveman`](./skills/caveman/) | [caveman](./skills/caveman/SKILL.md) | 用途：>-。 | 无 |
| [`charity-writing-assistant`](./skills/charity-writing-assistant/) | [charity-writing-assistant](./skills/charity-writing-assistant/SKILL.md) | 用于：当用户提到公益文书、项目申请、结项报告、传播计划、写文书（公益场景）、写报告（公益项目）、整理材料（公益机构）、捐赠人服务方案、肖像授权书、项目上线、平台申请时使用。 | 无（可选 API/账号以增强能力） |
| [`citation-manager`](./skills/citation-manager/) | [citation-manager](./skills/citation-manager/SKILL.md) | 学术引用管理器是一个专业的科研论文引用管理工具，旨在为科研论文和毕业论文添加真实参考文献并规范引用标注。 | 无 |
| [`ctrip-wendao`](./skills/ctrip-wendao/) | [ctrip-wendao](./skills/ctrip-wendao/SKILL.md) | 当用户发起任意旅行相关问询时，包含但不限于：预订酒店、机票查询、火车票查询、景点推荐、寻找当地特色玩乐、目的地查询、行程规划、美食住宿攻略、签证、查询旅游攻略、获取旅行建议等场景，自动触发此技能。 | 需要环境变量：`WENDAO_API_KEY` |
| [`diagnose`](./skills/diagnose/) | [diagnose](./skills/diagnose/SKILL.md) | 用途：Disciplined diagnosis loop for hard bugs and performance regressions。 | 无 |
| [`ecommerce-copywriter`](./skills/ecommerce-copywriter/) | [ecommerce-copywriter](./skills/ecommerce-copywriter/SKILL.md) | 电商爆款文案生成技能。 | 无 |
| [`education`](./skills/education/) | [education](./skills/education/SKILL.md) | 用途：Generate study plans, quizzes, flashcards, review materials, track learning progress and schedule st。 | 无 |
| [`english-intensive-reader`](./skills/english-intensive-reader/) | [english-intensive-reader](./skills/english-intensive-reader/SKILL.md) | UseWhen: 1. 用户想精读一篇英文文章、拆解长难句、标注生词 2. 用户需要生成英文阅读笔记或双栏精读报告 3. 用户备考四六级 / 考研阅读 / 外刊阅读，需要逐句语法分析 4. 用户… | 无（可选 API/账号以增强能力） |
| [`excalidraw-diagram`](./skills/excalidraw-diagram/) | [excalidraw-diagram](./skills/excalidraw-diagram/SKILL.md) | 用 Excalidraw 生成能够“解释问题”的图，而不是把文字机械摆成卡片。 | 无 |
| [`fintech-engineer`](./skills/fintech-engineer/) | [fintech-engineer](./skills/fintech-engineer/SKILL.md) | 用途：Expert fintech engineer specializing in financial systems, regulatory compliance (PCI DSS, AML, KYC)。 | 无 |
| [`flight-tracker`](./skills/flight-tracker/) | [flight-tracker](./skills/flight-tracker/SKILL.md) | 用途：Flight tracking and scheduling。 | 需要环境变量：`AVIATIONSTACK_API_KEY` |
| [`football-bayes`](./skills/football-bayes/) | [football-bayes](./skills/football-bayes/SKILL.md) | 用于：20年经验的足球竞彩策略官：贝叶斯统计 + 现代战术周期化，输出胜平负概率与风险提示。 | 无 |
| [`gif-sticker-maker`](./skills/gif-sticker-maker/) | [gif-sticker-maker](./skills/gif-sticker-maker/SKILL.md) | 用途：Convert photos (people, pets, objects, logos) into 4 animated GIF stickers with captions。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`growth-engine`](./skills/growth-engine/) | [growth-engine](./skills/growth-engine/SKILL.md) | 用途：Growth Engine。 | 需要环境变量：`EMAIL_AUTH_TOKEN`、`PIPELINE_AUTH_TOKEN`、`RECRUITING_AUTH_TOKEN` |
| [`habit-tracker`](./skills/habit-tracker/) | [habit-tracker](./skills/habit-tracker/SKILL.md) | 用途：Build habits with streaks, reminders, and progress visualization。 | 无 |
| [`idea-validator`](./skills/idea-validator/) | [idea-validator](./skills/idea-validator/SKILL.md) | 用途：Validate startup ideas using Hexa's Opportunity Memo framework and Perceived Created Value (PCV) met。 | 无 |
| [`imsg`](./skills/imsg/) | [imsg](./skills/imsg/SKILL.md) | 用途：iMessage/SMS CLI for listing chats, history, watch, and sending。 | 无 |
| [`infographic-maker`](./skills/infographic-maker/) | [infographic-maker](./skills/infographic-maker/SKILL.md) | 用途：Generate hand-drawn cartoon-style infographics from articles, concepts, reports, or data。 | 无 |
| [`install-futu-opend`](./skills/install-futu-opend/) | [install-futu-opend](./skills/install-futu-opend/SKILL.md) | 用于：Futu OpenD 安装助手。 | 无 |
| [`jinshuju`](./skills/jinshuju/) | [jinshuju](./skills/jinshuju/SKILL.md) | Use when the user wants to create or edit forms, collect or query entries, bulk-update form data,… | 需要环境变量：`YOUR_API_KEY`、`YOUR_API_SECRET` |
| [`knowledge-framework-builder`](./skills/knowledge-framework-builder/) | [knowledge-framework-builder](./skills/knowledge-framework-builder/SKILL.md) | 用于：课程知识框架梳理工具 — 把课程主题或教材资料提炼成结构化知识脉络图，支持三档深度输出与多格式导出。 | 无 |
| [`legal-logic-analysis`](./skills/legal-logic-analysis/) | [legal-logic-analysis](./skills/legal-logic-analysis/SKILL.md) | 用途：Think through any legal situation like a lawyer。 | 无 |
| [`macro-monitor`](./skills/macro-monitor/) | [macro-monitor](./skills/macro-monitor/SKILL.md) | 用于：每日宏观数据监控和推送。 | 无 |
| [`mcdonald-assistant`](./skills/mcdonald-assistant/) | [mcdonald-assistant](./skills/mcdonald-assistant/SKILL.md) | 用于：麦当劳中国点餐与优惠助手。 | 需要环境变量：`MCP_TOKEN` |
| [`meituan-coupon-workbuddy`](./skills/meituan-coupon-workbuddy/) | [meituan-coupon-workbuddy](./skills/meituan-coupon-workbuddy/SKILL.md) | 【美团官方】美团生活助手，支持外卖、餐饮团购、酒店住宿、门票度假、休闲娱乐、闪购、医药等多品类优惠券/红包/神券的一键领取与历史领取记录查询。 | 需要环境变量：`USER_TOKEN` |
| [`meituan-huisheng-coupon`](./skills/meituan-huisheng-coupon/) | [meituan-huisheng-coupon](./skills/meituan-huisheng-coupon/SKILL.md) | 用于：三大核心功能： 1. 一键领取美团生活服务各品类优惠券，覆盖外卖、到店、买菜、酒旅、打车、休娱、医药等全品类，触发即自动领取，领完即用。 | 需要环境变量：`USER_TOKEN` |
| [`nano-banana-pro`](./skills/nano-banana-pro/) | [nano-banana-pro](./skills/nano-banana-pro/SKILL.md) | 用途：Generate/edit images with Nano Banana Pro (Gemini 3 Pro Image)。 | 需要环境变量：`GEMINI_API_KEY` |
| [`note-organizer`](./skills/note-organizer/) | [note-organizer](./skills/note-organizer/SKILL.md) | 用途：Joplin — Note Manager — personal knowledge base。 | 无 |
| [`notebooklm-studio`](./skills/notebooklm-studio/) | [notebooklm-studio](./skills/notebooklm-studio/SKILL.md) | 用途：Import sources (URLs, YouTube, files, text) into Google NotebookLM and generate artifacts: podcasts,。 | 无 |
| [`novel`](./skills/novel/) | [novel](./skills/novel/SKILL.md) | 用途：Manage novel data — chapters, characters, plots — from the terminal fast。 | 无 |
| [`open-novel-writing`](./skills/open-novel-writing/) | [open-novel-writing](./skills/open-novel-writing/SKILL.md) | 用于：中文长篇小说创作助手。 | 无 |
| [`peekaboo`](./skills/peekaboo/) | [peekaboo](./skills/peekaboo/SKILL.md) | 用途：Capture and automate macOS UI with the Peekaboo CLI。 | 无 |
| [`plan-tracker`](./skills/plan-tracker/) | [plan-tracker](./skills/plan-tracker/SKILL.md) | 用于：当用户需要目标拆解、每日打卡、连续签到、学习热力图、进度预警时使用。 | 无 |
| [`podcast-ops`](./skills/podcast-ops/) | [podcast-ops](./skills/podcast-ops/SKILL.md) | 用途：>-。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY`、`OPENAI_API_KEY` |
| [`qcc-company`](./skills/qcc-company/) | [qcc-company](./skills/qcc-company/SKILL.md) | 通过企查查 Connector 查询中国境内企业的工商信息、股权结构、高管人员、财务数据、对外投资、历史变更、上市信息、分支机构、联系方式、开票信息及企业身份核验。 | 无 |
| [`sag`](./skills/sag/) | [sag](./skills/sag/SKILL.md) | 用途：ElevenLabs text-to-speech with mac-style say UX。 | 需要环境变量：`ELEVENLABS_API_KEY`、`SAG_API_KEY` |
| [`setup-pre-commit`](./skills/setup-pre-commit/) | [setup-pre-commit](./skills/setup-pre-commit/SKILL.md) | 用途：Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current r。 | 无 |
| [`shippage`](./skills/shippage/) | [shippage](./skills/shippage/SKILL.md) | 用途：Publish HTML or Markdown to a public URL instantly with ShipPage。 | 无（可选 API/账号以增强能力） |
| [`shopping-price-drop-coupon-scout`](./skills/shopping-price-drop-coupon-scout/) | [shopping-price-drop-coupon-scout](./skills/shopping-price-drop-coupon-scout/SKILL.md) | 用于：监控用户指定商品的价格变动并汇总官方优惠券与促销信息，全程只读、不登录账号、不加购物车、不下单、不处理支付。 | 无（可选 API/账号以增强能力） |
| [`songsee`](./skills/songsee/) | [songsee](./skills/songsee/SKILL.md) | 用途：Generate spectrograms and feature-panel visualizations from audio with the songsee CLI。 | 无 |
| [`study-planner`](./skills/study-planner/) | [study-planner](./skills/study-planner/SKILL.md) | 用于：当用户需要制定学习计划、备考计划、拆解复习目标时使用。 | 无 |
| [`task-alignment`](./skills/task-alignment/) | [task-alignment](./skills/task-alignment/SKILL.md) | 用途：Alignment conversation starting from a user's rough idea。 | 无 |
| [`task-implement`](./skills/task-implement/) | [task-implement](./skills/task-implement/SKILL.md) | 用途：Autonomous task execution driven by documents under `。 | 无 |
| [`teachany`](./skills/teachany/) | [teachany](./skills/teachany/SKILL.md) | 用于：TeachAny 的目标不是把知识堆进页面，而是把一节课做成**有问题锚点、有互动、有讲解、有评估、有发布闭环**的学习体验。 | 需要环境变量：`TEACHANY_DIRECT_TOKEN` |
| [`team-ops`](./skills/team-ops/) | [team-ops](./skills/team-ops/SKILL.md) | 用途：Audit team performance using the Elon Algorithm (identify A/B/C players) and extract action items fr。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY`、`HUBSPOT_API_KEY`、`OPENAI_API_KEY` |
| [`travel-cn`](./skills/travel-cn/) | [travel-cn](./skills/travel-cn/SKILL.md) | 旅行信息查询 - 去哪儿/携程/飞猪数据查询（Expedia 中国版）。 | 无 |
| [`travel-planning`](./skills/travel-planning/) | [travel-planning](./skills/travel-planning/SKILL.md) | 用途：Plan trips with itineraries, multi-city routing, budget optimization, family logistics, packing list。 | 无 |
| [`university-applications`](./skills/university-applications/) | [university-applications](./skills/university-applications/SKILL.md) | 用于：全体系命理大师 — 八字四柱、紫微斗数、奇门遁甲、六爻、梅花易数、塔罗、星盘、。 | 无（可选 API/账号以增强能力） |
| [`x-longform-post`](./skills/x-longform-post/) | [x-longform-post](./skills/x-longform-post/SKILL.md) | 用途：Write long-form X (Twitter) posts and threads in a founder/CEO voice。 | 无 |
| [`yt-competitive-analysis`](./skills/yt-competitive-analysis/) | [yt-competitive-analysis](./skills/yt-competitive-analysis/SKILL.md) | 用途：>-。 | 需要环境变量：`YOUTUBE_API_KEY` |

### 内容 / 营销 / 媒体（14）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`content-factory`](./skills/content-factory/) | [content-factory](./skills/content-factory/SKILL.md) | 用途：Multi-agent content production system。 | 无（可选 API/账号以增强能力） |
| [`content-ops`](./skills/content-ops/) | [content-ops](./skills/content-ops/SKILL.md) | 用途：Score, evaluate, and iteratively improve any content or strategy using an auto-assembled panel of do。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY` |
| [`content-repurposer`](./skills/content-repurposer/) | [content-repurposer](./skills/content-repurposer/SKILL.md) | 用途：Transform long-form content into platform-optimized snippets。 | 无 |
| [`ecomseer`](./skills/ecomseer/) | [ecomseer](./skills/ecomseer/SKILL.md) | TikTok Shop e-commerce data assistant. Search products, find trending items, analyze influencers,… | 需要环境变量：`ECOMSEER_API_KEY`、`YOUR_ECOMSEER_API_KEY` |
| [`email-daily-summary`](./skills/email-daily-summary/) | [email-daily-summary](./skills/email-daily-summary/SKILL.md) | 这个技能帮助你自动登录邮箱，获取邮件内容，并生成每日邮件总结。 | 需要环境变量：`BROWSER_USE_API_KEY` |
| [`jiaozhen-factcheck`](./skills/jiaozhen-factcheck/) | [jiaozhen-factcheck](./skills/jiaozhen-factcheck/SKILL.md) | 用于：事实查证工具，对输入内容的具体说法、资讯、事件或常识进行真实性、准确性、可靠性判断。 | 无 |
| [`libtv-skill`](./skills/libtv-skill/) | [libtv-skill](./skills/libtv-skill/SKILL.md) | agent-im 会话技能 - 通过 liblib.tv 的 AI 能力生成和编辑图片/视频。 | 需要环境变量：`LIBTV_ACCESS_KEY` |
| [`marketing-skills`](./skills/marketing-skills/) | [marketing-skills](./skills/marketing-skills/SKILL.md) | 用途：TL;DR: 23 marketing playbooks (CRO, SEO, copy, analytics, experiments, pricing, launches, ads, socia。 | 无 |
| [`qqmusic`](./skills/qqmusic/) | [qqmusic](./skills/qqmusic/SKILL.md) | QQ Music — search songs, albums, playlists, music videos, artists; daily recommendations; music c… | 需要环境变量：`QQMUSIC_API_KEY` |
| [`remotion-video-toolkit`](./skills/remotion-video-toolkit/) | [remotion-video-toolkit](./skills/remotion-video-toolkit/SKILL.md) | 用途：Complete toolkit for programmatic video creation with Remotion + React。 | 无 |
| [`taobao`](./skills/taobao/) | [maishou](./skills/taobao/SKILL.md) | 商品价格全网对比技能，获取商品在淘宝(Taobao)、天猫(TMall)、京东(JD.com)、拼多多(PinDuoDuo)、抖音(Douyin)、快手(KaiShou)的最优价格、优惠券，当用… | 无 |
| [`video-frames`](./skills/video-frames/) | [video-frames](./skills/video-frames/SKILL.md) | 用途：Extract frames or short clips from videos using ffmpeg。 | 无 |
| [`workrally`](./skills/workrally/) | [workrally](./skills/workrally/SKILL.md) | 用于：WorkRally CLI (workrally) — 面向 AI Agent 的 AIGC 漫剧视频创作全流程工具集。 | 需要环境变量：`WORKRALLY_API_KEY`、`YOUR_API_KEY` |
| [`xiaojia-free-marketing-pack`](./skills/xiaojia-free-marketing-pack/) | [xiaojia-free-marketing-pack](./skills/xiaojia-free-marketing-pack/SKILL.md) | 用于：这是一个轻量免费小加技能包，面向无需登录的营销辅助场景。 | 需要环境变量：`XIAOJIA_FREE_CLIENT_ID` |

### 开发 / 工程（48）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`admapix`](./skills/admapix/) | [admapix](./skills/admapix/SKILL.md) | Ad intelligence and app analytics assistant for searching ad creatives, analyzing apps, rankings,… | 需要环境变量：`ADMAPIX_API_KEY`、`ADMAPIX_DEEP_RESEARCH_TOKEN`、`YOUR_API_KEY` |
| [`android-native-dev`](./skills/android-native-dev/) | [android-native-dev](./skills/android-native-dev/SKILL.md) | 用途：Android native application development and UI design guide。 | 无 |
| [`api-gateway`](./skills/api-gateway/) | [api-gateway](./skills/api-gateway/SKILL.md) | 用途：Connect to external services through Maton-managed API routes。 | 需要环境变量：`MATON_API_KEY`、`YOUR_API_KEY` |
| [`cloudflare`](./skills/cloudflare/) | [cloudflare](./skills/cloudflare/SKILL.md) | 云开发/部署相关。 | 无 |
| [`cloudflare-worker-builder`](./skills/cloudflare-worker-builder/) | [cloudflare-worker-builder](./skills/cloudflare-worker-builder/SKILL.md) | 云开发/部署相关。 | 无 |
| [`cnb-skill`](./skills/cnb-skill/) | [cnb-skill](./skills/cnb-skill/SKILL.md) | Interact with CNB (Cloud Native Build) platform via OpenAPI. Manage organizations, repositories, … | 需要环境变量：`CNB_TOKEN` |
| [`deep-research`](./skills/deep-research/) | [deep-research](./skills/deep-research/SKILL.md) | 基于 [Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) 项目，提供人机协作的结构化调研能力。 | 无 |
| [`edgeone-pages-deploy`](./skills/edgeone-pages-deploy/) | [edgeone-pages-deploy](./skills/edgeone-pages-deploy/SKILL.md) | 6. **Before triggering any browser popup (login / 注册), explain the reason and the benefits to the… | 无 |
| [`fadada-document-sign`](./skills/fadada-document-sign/) | [fadada-document-sign](./skills/fadada-document-sign/SKILL.md) | 基于法大大 FASC API 5.0，提供一键式合同发起签署能力，将合同文件发送给签署方进行电子签署。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`FADADA_APP_SECRET` |
| [`flutter-dev`](./skills/flutter-dev/) | [flutter-dev](./skills/flutter-dev/SKILL.md) | 用途：Flutter cross-platform development guide covering widget patterns, Riverpod/Bloc state management, G。 | 无 |
| [`frontend-dev`](./skills/frontend-dev/) | [frontend-dev](./skills/frontend-dev/SKILL.md) | 用途：Full-stack frontend development combining premium UI design, cinematic animations, AI-generated medi。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`fullstack-dev`](./skills/fullstack-dev/) | [fullstack-dev](./skills/fullstack-dev/SKILL.md) | 用途：Full-stack backend architecture and frontend-backend integration guide。 | 需要环境变量：`JWT_SECRET` |
| [`futuapi`](./skills/futuapi/) | [futuapi](./skills/futuapi/SKILL.md) | 用于：富途 OpenAPI 交易与行情助手。 | 无（可选 API/账号以增强能力） |
| [`github`](./skills/github/) | [github](./skills/github/SKILL.md) | Git/GitHub 开发协作。 | 需要 GitHub Token 或 `gh auth login` |
| [`github-ai-trends`](./skills/github-ai-trends/) | [github-ai-trends](./skills/github-ai-trends/SKILL.md) | Git/GitHub 开发协作。 | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`github-pages-auto-deploy`](./skills/github-pages-auto-deploy/) | [github-pages-auto-deploy](./skills/github-pages-auto-deploy/SKILL.md) | 用于：让你的网站在推送代码时自动部署到 GitHub Pages，实现：。 | 需要 GitHub Token 或 `gh auth login` |
| [`github-trending-cn`](./skills/github-trending-cn/) | [github-trending-cn](./skills/github-trending-cn/SKILL.md) | GitHub Trending Monitor. Fetch GitHub trending repos by daily/weekly/monthly period using real Gi… | 需要 GitHub Token 或 `gh auth login`；需要环境变量：`GITHUB_TOKEN` |
| [`gsap-animation-assistant`](./skills/gsap-animation-assistant/) | [gsap-animation-assistant](./skills/gsap-animation-assistant/SKILL.md) | 用于：GSAP 动画开发助手。 | 无 |
| [`haina-shopping-assistant`](./skills/haina-shopping-assistant/) | [haina-shopping-assistant](./skills/haina-shopping-assistant/SKILL.md) | 值得买开发的海纳购物管家，一款专业为用户提供来自全网与兴趣高度相关的、公允的AI消费决策支持工具。 | 无（可选 API/账号以增强能力） |
| [`html-deploy`](./skills/html-deploy/) | [html-deploy](./skills/html-deploy/SKILL.md) | 云开发/部署相关。 | 无（可选 API/账号以增强能力） |
| [`ima-skills`](./skills/ima-skills/) | [ima-skills](./skills/ima-skills/SKILL.md) | 统一的 IMA OpenAPI 技能，支持笔记管理和知识库操作。 | 需要环境变量：`IMA_OPENAPI_APIKEY` |
| [`ios-application-dev`](./skills/ios-application-dev/) | [ios-application-dev](./skills/ios-application-dev/SKILL.md) | 用途：iOS application development guide covering UIKit, SnapKit, and SwiftUI。 | 无 |
| [`landing-page-generator`](./skills/landing-page-generator/) | [landing-page-generator](./skills/landing-page-generator/SKILL.md) | 云开发/部署相关。 | 无 |
| [`model-usage`](./skills/model-usage/) | [model-usage](./skills/model-usage/SKILL.md) | 用途：Use CodexBar CLI local cost usage to summarize per-model usage for Codex or Claude, including the cu。 | 无 |
| [`my-novel-writer`](./skills/my-novel-writer/) | [my-novel-writer](./skills/my-novel-writer/SKILL.md) | 用于：> ⚠️ **重要**：请通过环境变量配置 API 密钥，不要在配置文件中硬编码。 | 需要环境变量：`NOVEL_API_KEY` |
| [`netlify-deploy`](./skills/netlify-deploy/) | [netlify-deploy](./skills/netlify-deploy/SKILL.md) | 云开发/部署相关。 | 无（可选 API/账号以增强能力） |
| [`open-lesson`](./skills/open-lesson/) | [open-lesson](./skills/open-lesson/SKILL.md) | 用途：Interact with openLesson tutoring API for Socratic learning: generate learning plans as directed gra。 | 需要环境变量：`OPENLESSON_API_KEY`、`YOUR_API_KEY` |
| [`openai-image-gen`](./skills/openai-image-gen/) | [openai-image-gen](./skills/openai-image-gen/SKILL.md) | 用途：Batch-generate images via OpenAI Images API。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`OPENAI_API_KEY` |
| [`openai-whisper`](./skills/openai-whisper/) | [openai-whisper](./skills/openai-whisper/SKILL.md) | 用途：Local speech-to-text with the Whisper CLI (no API key)。 | 无 |
| [`openai-whisper-api`](./skills/openai-whisper-api/) | [openai-whisper-api](./skills/openai-whisper-api/SKILL.md) | 用途：Transcribe audio via OpenAI Audio Transcriptions API (Whisper)。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`OPENAI_API_KEY` |
| [`ozon-1688-uploader`](./skills/ozon-1688-uploader/) | [ozon-1688-uploader](./skills/ozon-1688-uploader/SKILL.md) | 将1688的商品铺货到俄罗斯电商平台Ozon（上架），通过Ozon官方API实现商品信息的上传和状态查询。 | 需要环境变量：`ALPHASHOP_ACCESS_KEY`、`OZON_API_KEY`、`OZON_CLIENT_ID` |
| [`product-showcase-site`](./skills/product-showcase-site/) | [product-showcase-site](./skills/product-showcase-site/SKILL.md) | 云开发/部署相关。 | 无（可选 API/账号以增强能力） |
| [`react-native-dev`](./skills/react-native-dev/) | [react-native-dev](./skills/react-native-dev/SKILL.md) | 用途：React Native and Expo development guide covering components, styling, animations, navigation, state 。 | 无 |
| [`shader-dev`](./skills/shader-dev/) | [shader-dev](./skills/shader-dev/SKILL.md) | 用途：Comprehensive GLSL shader techniques for creating stunning visual effects — ray marching, SDF modeli。 | 无 |
| [`shopify-admin-api`](./skills/shopify-admin-api/) | [shopify-admin-api](./skills/shopify-admin-api/SKILL.md) | 用途：Shopify Admin API。 | 需要环境变量：`SHOPIFY_ACCESS_TOKEN` |
| [`static-app`](./skills/static-app/) | [static-app](./skills/static-app/SKILL.md) | 云开发/部署相关。 | 需要环境变量：`STATIC_APP_API_KEY` |
| [`tapd-openapi`](./skills/tapd-openapi/) | [tapd-openapi](./skills/tapd-openapi/SKILL.md) | TAPD OpenAPI skill，用于需求、缺陷、任务、迭代、Wiki、评论、工时、附件等 TAPD 平台操作。 | 需要环境变量：`TAPD_TOKEN` |
| [`tdd`](./skills/tdd/) | [tdd](./skills/tdd/SKILL.md) | 用途：Test-driven development with red-green-refactor loop。 | 无 |
| [`tmux`](./skills/tmux/) | [tmux](./skills/tmux/SKILL.md) | 用途：Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output。 | 无 |
| [`trello`](./skills/trello/) | [trello](./skills/trello/SKILL.md) | 用途：Manage Trello boards, lists, and cards via the Trello REST API。 | 需要环境变量：`TRELLO_API_KEY`、`TRELLO_TOKEN` |
| [`vercel-deploy`](./skills/vercel-deploy/) | [vercel-deploy](./skills/vercel-deploy/SKILL.md) | 云开发/部署相关。 | 需要环境变量：`VERCEL_TOKEN` |
| [`weather`](./skills/weather/) | [weather](./skills/weather/SKILL.md) | 用途：Get current weather and forecasts (no API key required)。 | 无 |
| [`weather-open-meteo`](./skills/weather-open-meteo/) | [weather-open-meteo](./skills/weather-open-meteo/SKILL.md) | 通过 open-meteo.com 公共 API 查询指定地点的当前天气和未来预报，无需 API key；当 open-meteo 请求失败时可降级使用 wttr.in。 | 无 |
| [`web-deploy`](./skills/web-deploy/) | [web-deploy](./skills/web-deploy/SKILL.md) | Git/GitHub 开发协作。 | 无 |
| [`web-deploy-github`](./skills/web-deploy-github/) | [web-deploy-github](./skills/web-deploy-github/SKILL.md) | Git/GitHub 开发协作。 | 需要 GitHub Token 或 `gh auth login` |
| [`web-performance-audit`](./skills/web-performance-audit/) | [web-performance-audit](./skills/web-performance-audit/SKILL.md) | 云开发/部署相关。 | 无 |
| [`web-scraper`](./skills/web-scraper/) | [web-scraper](./skills/web-scraper/SKILL.md) | 用途：Web scraping and content comprehension agent — multi-strategy extraction with cascade fallback, news。 | 需要环境变量：`OPENROUTER_API_KEY` |
| [`zoom-out`](./skills/zoom-out/) | [zoom-out](./skills/zoom-out/SKILL.md) | 用途：Tell the agent to zoom out and give broader context or a higher-level perspective on unfamiliar code。 | 无 |

### 搜索 / 研究（35）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`agent-browser-core`](./skills/agent-browser-core/) | [agent-browser-core](./skills/agent-browser-core/SKILL.md) | 浏览器自动化。 | 无 |
| [`airbnb`](./skills/airbnb/) | [airbnb](./skills/airbnb/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`apple-notes`](./skills/apple-notes/) | [apple-notes](./skills/apple-notes/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`arxiv-watcher`](./skills/arxiv-watcher/) | [arxiv-watcher](./skills/arxiv-watcher/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`autoresearch`](./skills/autoresearch/) | [autoresearch](./skills/autoresearch/SKILL.md) | 搜索与研究辅助。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY` |
| [`baidu-drive`](./skills/baidu-drive/) | [baidu-drive](./skills/baidu-drive/SKILL.md) | 百度网盘(Baidu Drive)文件管理 — 上传、下载、转存、分享、搜索、移动、复制、重命名、创建文件夹。 | 需要百度网盘 OAuth 授权；需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY` |
| [`browser`](./skills/browser/) | [browser](./skills/browser/SKILL.md) | 浏览器自动化。 | 无 |
| [`browser-cash`](./skills/browser-cash/) | [browser-cash](./skills/browser-cash/SKILL.md) | 浏览器自动化。 | 需要环境变量：`BROWSER_CASH_API_KEY` |
| [`browser-use`](./skills/browser-use/) | [browser-use](./skills/browser-use/SKILL.md) | 浏览器自动化。 | 需要环境变量：`BROWSER_USE_API_KEY` |
| [`browserwing`](./skills/browserwing/) | [browserwing](./skills/browserwing/SKILL.md) | 浏览器自动化。 | 无（可选 API/账号以增强能力） |
| [`clawbrowser`](./skills/clawbrowser/) | [clawbrowser](./skills/clawbrowser/SKILL.md) | 浏览器自动化。 | 无 |
| [`cn-ecommerce-search`](./skills/cn-ecommerce-search/) | [cn-ecommerce-search](./skills/cn-ecommerce-search/SKILL.md) | 搜索与研究辅助。 | 无（可选 API/账号以增强能力） |
| [`darwin-skill`](./skills/darwin-skill/) | [darwin-skill](./skills/darwin-skill/SKILL.md) | Darwin Skill (达尔文.skill): autonomous skill optimizer inspired by Karpathy's autoresearch. Evaluat… | 无 |
| [`flights-search`](./skills/flights-search/) | [flights](./skills/flights-search/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`flyai`](./skills/flyai/) | [flyai](./skills/flyai/SKILL.md) | 搜索与研究辅助。 | 需要环境变量：`FLYAI_API_KEY` |
| [`gifgrep`](./skills/gifgrep/) | [gifgrep](./skills/gifgrep/SKILL.md) | 搜索与研究辅助。 | 需要环境变量：`GIPHY_API_KEY`、`TENOR_API_KEY` |
| [`market-researcher`](./skills/market-researcher/) | [market-researcher](./skills/market-researcher/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`multi-search-engine`](./skills/multi-search-engine/) | [multi-search-engine](./skills/multi-search-engine/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`perplexity`](./skills/perplexity/) | [perplexity](./skills/perplexity/SKILL.md) | 搜索与研究辅助。 | 需要环境变量：`PERPLEXITY_API_KEY` |
| [`playwright-browser-automation`](./skills/playwright-browser-automation/) | [playwright-browser-automation](./skills/playwright-browser-automation/SKILL.md) | 浏览器自动化。 | 无（可选 API/账号以增强能力） |
| [`playwright-scraper-skill`](./skills/playwright-scraper-skill/) | [playwright-scraper-skill](./skills/playwright-scraper-skill/SKILL.md) | 浏览器自动化。 | 无 |
| [`price-history`](./skills/price-history/) | [price-history](./skills/price-history/SKILL.md) | 用于：封装慢慢买（manmanbuy.com）官方 MCP，按关键词搜索全网商品的参考好价、实时价格与隐藏优惠券，并基于返回数据判断当前价是否为真实低价、识别"先涨后降"的虚假促销。 | 无 |
| [`qmd`](./skills/qmd/) | [qmd](./skills/qmd/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`responsiveness-check`](./skills/responsiveness-check/) | [responsiveness-check](./skills/responsiveness-check/SKILL.md) | 浏览器自动化。 | 需要 GitHub Token 或 `gh auth login` |
| [`sino-drug-instructions-search`](./skills/sino-drug-instructions-search/) | [sino-drug-instructions-search](./skills/sino-drug-instructions-search/SKILL.md) | 用于：在用户询问药品说明书、用药信息、适应症、禁忌、用法用量、不良反应、成分、规格、厂家，或根据症状/疾病查找药品时使用此技能。 | 需要环境变量：`SKILLS_BIZ_TOKEN` |
| [`smooth-browser`](./skills/smooth-browser/) | [smooth-browser](./skills/smooth-browser/SKILL.md) | 浏览器自动化。 | 无（可选 API/账号以增强能力） |
| [`stagehand-browser-cli`](./skills/stagehand-browser-cli/) | [stagehand-browser-cli](./skills/stagehand-browser-cli/SKILL.md) | 浏览器自动化。 | 需要环境变量：`BROWSERBASE_API_KEY` |
| [`stealth-browser`](./skills/stealth-browser/) | [stealth-browser](./skills/stealth-browser/SKILL.md) | 长任务使用 `task_runner.py` 管理状态：。 | 无（可选 API/账号以增强能力） |
| [`tavily`](./skills/tavily/) | [tavily](./skills/tavily/SKILL.md) | 搜索与研究辅助。 | 需要环境变量：`TAVILY_API_KEY` |
| [`things-mac`](./skills/things-mac/) | [things-mac](./skills/things-mac/SKILL.md) | 搜索与研究辅助。 | 需要环境变量：`THINGS_AUTH_TOKEN` |
| [`vip-skill`](./skills/vip-skill/) | [vip-skill](./skills/vip-skill/SKILL.md) | 唯品会（vip.com）电商服务技能包（vipshop-skills），整合唯品会搜索、商品查询、活动查询、图片搜索等多项购物服务，是一套完整的唯品会购物 AI 助手解决方案。 | 需要环境变量：`PASSPORT_ACCESS_TOKEN` |
| [`wacli`](./skills/wacli/) | [wacli](./skills/wacli/SKILL.md) | 搜索与研究辅助。 | 无 |
| [`web-access`](./skills/web-access/) | [web-access](./skills/web-access/SKILL.md) | 用于：所有联网操作必须通过此 skill 处理，包括：搜索、网页抓取、登录后操作、网络交互等。 | 无（可选 API/账号以增强能力） |
| [`web-search-exa`](./skills/web-search-exa/) | [web-search-exa](./skills/web-search-exa/SKILL.md) | 搜索与研究辅助。 | 无（可选 API/账号以增强能力） |
| [`xurl`](./skills/xurl/) | [xurl](./skills/xurl/SKILL.md) | 搜索与研究辅助。 | 无 |

### 数据 / 金融 / 股票（10）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`charity-finance-assistant`](./skills/charity-finance-assistant/) | [charity-finance-assistant](./skills/charity-finance-assistant/SKILL.md) | 用于：> ## ⚠️ 使用前请先读这一段（重要）。 | 无 |
| [`finance-ops`](./skills/finance-ops/) | [finance-ops](./skills/finance-ops/SKILL.md) | 金融/股票数据查询或分析。 | 无（可选 API/账号以增强能力） |
| [`lingxi-financialsearch-skill`](./skills/lingxi-financialsearch-skill/) | [lingxi-financialsearch-skill](./skills/lingxi-financialsearch-skill/SKILL.md) | 国泰海通金融数据查询Skill，通过自然语言查询A股实时行情、公司基本信息、F10财务数据、个股技术指标等金融数据。 | 无 |
| [`neodata-financial-search`](./skills/neodata-financial-search/) | [neodata-financial-search](./skills/neodata-financial-search/SKILL.md) | > **一句话概述**：用自然语言查询股票行情、财务报表/财报、基金、指数、板块、宏观经济、外汇、大宗商品等全品类金融数据，即问即答。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`stock-analysis`](./skills/stock-analysis/) | [stock-analysis](./skills/stock-analysis/SKILL.md) | 金融/股票数据查询或分析。 | 需要环境变量：`AUTH_TOKEN` |
| [`stock-analyzer`](./skills/stock-analyzer/) | [stock-analyzer](./skills/stock-analyzer/SKILL.md) | 用于：全球股票综合分析工具。 | 无（可选 API/账号以增强能力） |
| [`us-stock-analysis`](./skills/us-stock-analysis/) | [us-stock-analysis](./skills/us-stock-analysis/SKILL.md) | 金融/股票数据查询或分析。 | 无 |
| [`westock-data`](./skills/westock-data/) | [westockdata](./skills/westock-data/SKILL.md) | 查询A股、港股、美股个股/指数/ETF的详细数据，包括：K线/分时、财务报表（三大报表多期查询，支持跨市场批量对比）、资金流向、技术指标、筹码分析、股东结构、分红除权、业绩预告、公司简况、ETF… | 无 |
| [`westockdata`](./skills/westockdata/) | [westockdata](./skills/westockdata/SKILL.md) | 查询A股、港股、美股个股/指数/ETF的详细数据，包括：K线/分时、财务报表（三大报表多期查询，支持跨市场批量对比）、资金流向、技术指标、筹码分析、股东结构、分红除权、业绩预告、公司简况、ETF… | 无 |
| [`xiaobai-coach`](./skills/xiaobai-coach/) | [xiaobai-coach](./skills/xiaobai-coach/SKILL.md) | 用于：给小白讲清理财、基金、股票知识，并配套实操工具与清单的财商陪跑技能。 | 无 |

### 文档 / 办公（16）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`dingtalk-unified`](./skills/dingtalk-unified/) | [dingtalk-unified](./skills/dingtalk-unified/SKILL.md) | 钉钉 CLI 全能套件，基于官方 DingTalk Workspace CLI（dws）操作钉钉消息、群聊、通讯录、日历、待办、审批、考勤、日志、DING、AI 表格、钉钉文档、钉盘、AI 听记… | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`fbs-bookwriter`](./skills/fbs-bookwriter/) | [fbs-bookwriter](./skills/fbs-bookwriter/SKILL.md) | 用于：福帮手出品 \| 高质量长文档手稿工具链：书籍、手册、白皮书、行业指南、长篇报道、深度专题；支持联网查证（宿主允许时启用，离线自动降级）、S/P/C/B 分层审校、中文排版与 MD/HTML 交付。 | 无（可选 API/账号以增强能力） |
| [`kdocs`](./skills/kdocs/) | [kdocs](./skills/kdocs/SKILL.md) | 用于：金山文档（WPS 云文档 / 365.kdocs.cn / www.kdocs.cn）— 在线云文档平台，【金山文档官方 Skill】。 | 需要环境变量：`EXISTING_TOKEN`、`KINGSOFT_DOCS_TOKEN`、`LEGACY_ENV_TOKEN`、`LEGACY_FILE_TOKEN` |
| [`material-organizer`](./skills/material-organizer/) | [material-organizer](./skills/material-organizer/SKILL.md) | 用于：批量资料整理助手 — 把一堆素材提炼成结构化文档，或对本地目录进行扫描归档。 | 无（可选 API/账号以增强能力） |
| [`md-to-pdf-cjk`](./skills/md-to-pdf-cjk/) | [md-to-pdf-cjk](./skills/md-to-pdf-cjk/SKILL.md) | 办公文档处理。 | 无 |
| [`minimax-docx`](./skills/minimax-docx/) | [minimax-docx](./skills/minimax-docx/SKILL.md) | 用于：signals: "reformat", "apply template", "restyle", "match this format", "套模板", "排版"。 | 无 |
| [`minimax-pdf`](./skills/minimax-pdf/) | [minimax-pdf](./skills/minimax-pdf/SKILL.md) | 办公文档处理。 | 无 |
| [`minimax-xlsx`](./skills/minimax-xlsx/) | [minimax-xlsx](./skills/minimax-xlsx/SKILL.md) | 办公文档处理。 | 无 |
| [`nano-pdf`](./skills/nano-pdf/) | [nano-pdf](./skills/nano-pdf/SKILL.md) | 办公文档处理。 | 无 |
| [`notion`](./skills/notion/) | [notion](./skills/notion/SKILL.md) | 用途：Notion API for creating and managing pages, databases, and blocks。 | 需要 Notion Integration Token |
| [`pdfkit-py`](./skills/pdfkit-py/) | [pdfkit-py](./skills/pdfkit-py/SKILL.md) | Pure-Python PDF toolkit with 50 commands covering reading, editing, conversion, forms, encryption… | 无（可选 API/账号以增强能力） |
| [`pptx-generator`](./skills/pptx-generator/) | [pptx-generator](./skills/pptx-generator/SKILL.md) | 办公文档处理。 | 无 |
| [`summarize`](./skills/summarize/) | [summarize](./skills/summarize/SKILL.md) | 办公文档处理。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY`、`APIFY_API_TOKEN`、`FIRECRAWL_API_KEY`、`GEMINI_API_KEY`、`GOOGLE_API_KEY` 等 |
| [`trip-planner-generator`](./skills/trip-planner-generator/) | [trip-planner-generator](./skills/trip-planner-generator/SKILL.md) | 通过交互式问答帮助用户生成结构化的旅行行程计划，输出包含每日行程、预算明细、行前清单和注意事项的 Markdown 文档。 | 无 |
| [`tutor-skills`](./skills/tutor-skills/) | [tutor-skills](./skills/tutor-skills/SKILL.md) | 办公文档处理。 | 无 |
| [`yingmi-skill`](./skills/yingmi-skill/) | [yingmi-skill](./skills/yingmi-skill/SKILL.md) | 当用户需要查询基金、策略、公告、财经资讯，做资产配置、组合诊断、风险回测、现金流分析，或生成图表、PDF 时，优先使用本 Skill 获取真实数据与可执行能力。 | 无 |

### 腾讯 / 微信 / 企微 / 飞书（48）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`a-stock-data`](./skills/a-stock-data/) | [a-stock-data](./skills/a-stock-data/SKILL.md) | A股全栈数据工具包 — 覆盖行情(mootdx+腾讯+百度K线)、研报(东财+同花顺+iwencai)、信号(同花顺热点+北向+龙虎榜+解禁+行业)、资金面(融资融券+大宗交易+股东户数+分红+… | 需要环境变量：`IWENCAI_API_KEY` |
| [`andonq`](./skills/andonq/) | [andonq](./skills/andonq/SKILL.md) | 用于：AndonQ 腾讯云智能客服"领域虾" — 不切窗口、不排队，即刻获得腾讯云全产品线专业解答。 | 需要环境变量：`AUTHORIZE_APP_ID` |
| [`cloudbase`](./skills/cloudbase/) | [cloudbase](./skills/cloudbase/SKILL.md) | CloudBase is a full-stack development and deployment toolkit for building and launching websites,… | 需要环境变量：`JWT_SECRET` |
| [`cloudq`](./skills/cloudq/) | [cloudq](./skills/cloudq/SKILL.md) | 用户咨询腾讯云产品资源、AWS、阿里云等多云资源时，查看智能顾问架构图、架构目录、架构详情、架构评估结果、绘制架构图、开通智能顾问时、AI智能巡检、AI容量监测、AI混沌演练、AI云诊断、主动预… | 需要飞书应用凭证或用户登录授权；需要环境变量：`TENCENTCLOUD_TOKEN` |
| [`cos-vectors`](./skills/cos-vectors/) | [cos-vectors](./skills/cos-vectors/SKILL.md) | 腾讯云 COS 向量桶全功能管理技能。 | 无（可选 API/账号以增强能力） |
| [`lark-unified`](./skills/lark-unified/) | [lark-unified](./skills/lark-unified/SKILL.md) | Lark (飞书) is a comprehensive collaboration platform combining messaging, documents, spreadsheets,… | 需要微信公众号/开放平台 AppID 与 AppSecret；需要飞书应用凭证或用户登录授权 |
| [`migraq`](./skills/migraq/) | [migraq](./skills/migraq/SKILL.md) | 用于：腾讯云迁移平台（CMG/MSP）全流程能力。 | 无（可选 API/账号以增强能力） |
| [`skill-scanner`](./skills/skill-scanner/) | [skill-scanner](./skills/skill-scanner/SKILL.md) | Scan any agent skill for security risks before you install or use it. Powered by Tencent Zhuque L… | 无 |
| [`skills-security-check`](./skills/skills-security-check/) | [skills-security-check](./skills/skills-security-check/SKILL.md) | 用于：腾讯云鼎实验室出品，Skill安全审查工具。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`OPENAI_API_KEY` |
| [`skyline`](./skills/skyline/) | [skyline](./skills/skyline/SKILL.md) | WeChat Mini Program Skyline rendering engine. Use when developing with Skyline renderer, includin… | 无 |
| [`smart-page`](./skills/smart-page/) | [smart-page](./skills/smart-page/SKILL.md) | 腾讯文档智能页面（Smart Page）是可交互在线汇报网页生成工具，适用于汇报、述职、周报、复盘、数据看板、课件、培训、调研报告、会议纪要和本地 HTML 上云。 | 无（可选 API/账号以增强能力） |
| [`tdesign-miniprogram`](./skills/tdesign-miniprogram/) | [tdesign-miniprogram](./skills/tdesign-miniprogram/SKILL.md) | 微信生态相关能力。 | 无 |
| [`tencent-campus-recruit`](./skills/tencent-campus-recruit/) | [tencent-campus-recruit](./skills/tencent-campus-recruit/SKILL.md) | 用于：当用户询问腾讯校园招聘相关问题时使用，包括：校招/实习投递流程与时间节点、岗位搜索与推荐、 招聘公告与宣讲会动态、简历诊断与优化、面试准备与模拟陪练、校招防诈骗识别。 | 需要环境变量：`TRAG_API_KEY` |
| [`tencent-docs`](./skills/tencent-docs/) | [tencent-docs](./skills/tencent-docs/SKILL.md) | 腾讯文档（docs.qq.com）-在线云文档平台，是创建、编辑、管理文档的首选 skill。 | 需要环境变量：`TENCENT_DOCS_TOKEN` |
| [`tencent-esign-contract`](./skills/tencent-esign-contract/) | [tencent-esign-contract](./skills/tencent-esign-contract/SKILL.md) | 用于：腾讯电子签合同AI助手，支持合同起草、审查、对比、法条法规检索。 | 需要环境变量：`ESIGN_TOKEN` |
| [`tencent-meeting-skill`](./skills/tencent-meeting-skill/) | [tencent-meeting-skill](./skills/tencent-meeting-skill/SKILL.md) | 用于：在用户提及腾讯会议、视频会议、线上会议相关内容与操作时使用此技能。 | 需要环境变量：`TENCENT_MEETING_TOKEN` |
| [`tencent-music-campus-recruit`](./skills/tencent-music-campus-recruit/) | [tencent-music-campus-recruit](./skills/tencent-music-campus-recruit/SKILL.md) | 用于：当用户询问腾讯校园招聘相关问题时使用，包括：校招/实习投递流程与时间节点、岗位搜索与推荐、 招聘公告与宣讲会动态、组织架构/BG/部门介绍、简历诊断与优化、面试准备与模拟陪练、校招防诈骗识别。 | 需要环境变量：`TRAG_API_KEY` |
| [`tencent-musician-skills`](./skills/tencent-musician-skills/) | [tencent-musician-skills](./skills/tencent-musician-skills/SKILL.md) | 用于：腾讯音乐人智能分析助手（数据分析 + 宣推）。 | 需要环境变量：`TME_HEADER_TOKEN` |
| [`tencent-news`](./skills/tencent-news/) | [tencent-news](./skills/tencent-news/SKILL.md) | 用于：7×24 新闻资讯搜索工具，聚焦中国国内信息和国际热点。 | 无 |
| [`tencent-rumor-refuter`](./skills/tencent-rumor-refuter/) | [tencent-rumor-refuter](./skills/tencent-rumor-refuter/SKILL.md) | 嘿！我是小P \U0001F427，腾讯公司谣言辟谣辅助技能 有关腾讯公司的信息真真假假，我来帮你看看！ 可以通过以下方式唤醒我： (1) 直接呼叫\"小P\"或\"小p\"； (2) 提到以下… | 无 |
| [`tencent-ssv-techforgood`](./skills/tencent-ssv-techforgood/) | [tencent-ssv-techforgood](./skills/tencent-ssv-techforgood/SKILL.md) | 专注公益机构数字化赋能的智能助手，围绕腾讯技术公益数字工具箱（techforgood.qq.com）为社会组织匹配免费或低成本数字化产品，支持需求诊断、产品推荐、申领指引、数字化实施参考与必要的… | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`tencent-survey`](./skills/tencent-survey/) | [tencent-survey](./skills/tencent-survey/SKILL.md) | 用于：腾讯问卷（wj.qq.com）- 在线问卷调查平台。 | 需要环境变量：`TENCENT_SURVEY_TOKEN` |
| [`tencent-weather`](./skills/tencent-weather/) | [tencent-weather](./skills/tencent-weather/SKILL.md) | 通过 `tencent-news-cli` 的天气能力完成天气查询。 | 无 |
| [`tencent-yuanbao-gaokao-regional-passing-scores`](./skills/tencent-yuanbao-gaokao-regional-passing-scores/) | [tencent-yuanbao-gaokao-regional-passing-scores](./skills/tencent-yuanbao-gaokao-regional-passing-scores/SKILL.md) | 用于：高考地区分数线信息检索助手。 | 无 |
| [`tencent-yuanbao-gaokao-score-to-rank-lookup`](./skills/tencent-yuanbao-gaokao-score-to-rank-lookup/) | [tencent-yuanbao-gaokao-score-to-rank-lookup](./skills/tencent-yuanbao-gaokao-score-to-rank-lookup/SKILL.md) | 高考一分一段信息检索助手，帮助考生根据分数查询全省排名位次，或根据位次估算对应分数区间，或提供一分一段表。 | 无 |
| [`tencent-yuanbao-standard-search`](./skills/tencent-yuanbao-standard-search/) | [tencent-yuanbao-standard-search](./skills/tencent-yuanbao-standard-search/SKILL.md) | 用于：元宝搜索标准版skill以互联网全网公开资源为基础，叠加腾讯优质内容生态，结合元宝APP联网搜索应用实践，从数据收录到智能检索召回，全链路构建AI友好搜索引擎。 | 需要环境变量：`TENCENTCLOUD_WSA_APIKEY` |
| [`tencent-yunzhi`](./skills/tencent-yunzhi/) | [tencent-yunzhi](./skills/tencent-yunzhi/SKILL.md) | 用于：腾讯乐享（lexiangla.com / csig.lexiangla.com）知识库专用操作。 | 需要飞书应用凭证或用户登录授权；需要环境变量：`LEXIANG_TOKEN` |
| [`tencentcloud-cls`](./skills/tencentcloud-cls/) | [tencentcloud-cls](./skills/tencentcloud-cls/SKILL.md) | 用于：腾讯云日志服务 CLS 技能。 | 无 |
| [`tencentcloud-cos`](./skills/tencentcloud-cos/) | [tencentcloud-cos](./skills/tencentcloud-cos/SKILL.md) | 用于：腾讯云对象存储(COS)和数据万象(CI)集成技能。 | 需要环境变量：`TENCENT_COS_TOKEN` |
| [`tencentcloud-ocr`](./skills/tencentcloud-ocr/) | [tencentcloud-ocr](./skills/tencentcloud-ocr/SKILL.md) | 用于：腾讯云通用文字识别（高精度版）(GeneralAccurateOCR) 技能包。 | 无（可选 API/账号以增强能力） |
| [`tencentcloud-ocr-extractdocagent`](./skills/tencentcloud-ocr-extractdocagent/) | [tencentcloud-ocr-extractdocagent](./skills/tencentcloud-ocr-extractdocagent/SKILL.md) | 用于：腾讯云实时文档抽取Agent(ExtractDocAgent)接口调用技能。 | 无（可选 API/账号以增强能力） |
| [`tencentcloud-ocr-general`](./skills/tencentcloud-ocr-general/) | [tencentcloud-ocr-general](./skills/tencentcloud-ocr-general/SKILL.md) | 用于：腾讯云广告文字识别(AdvertiseOCR)接口调用技能。 | 无（可选 API/账号以增强能力） |
| [`tencentcloud-ocr-questionmarkagent`](./skills/tencentcloud-ocr-questionmarkagent/) | [tencentcloud-ocr-questionmarkagent](./skills/tencentcloud-ocr-questionmarkagent/SKILL.md) | 用于：腾讯云试题批改Agent(SubmitQuestionMarkAgentJob/DescribeQuestionMarkAgentJob)接口调用技能。 | 无（可选 API/账号以增强能力） |
| [`tencentcloud-ocr-recognizetableaccurate`](./skills/tencentcloud-ocr-recognizetableaccurate/) | [tencentcloud-ocr-recognizetableaccurate](./skills/tencentcloud-ocr-recognizetableaccurate/SKILL.md) | 用于：腾讯云表格识别v3(RecognizeTableAccurateOCR)接口调用技能。 | 无（可选 API/账号以增强能力） |
| [`tencentmap-lbs-skill`](./skills/tencentmap-lbs-skill/) | [tencentmap-lbs-skill](./skills/tencentmap-lbs-skill/SKILL.md) | 用于：腾讯地图位置服务，支持POI搜索、路径规划、旅游规划、周边搜索，轨迹数据可视化和地图数据可视化。 | 需要腾讯位置服务 Key（可用体验通道） |
| [`tencentmap-map-assistant`](./skills/tencentmap-map-assistant/) | [tencentmap-map-assistant](./skills/tencentmap-map-assistant/SKILL.md) | 用于：腾讯位置服务·地图助手 Skill，一句自然语言调用腾讯地图全套能力，无需开发者账号、开箱即用。 | 需要腾讯位置服务 Key（可用体验通道） |
| [`tencentos-expert`](./skills/tencentos-expert/) | [tencentos-expert](./skills/tencentos-expert/SKILL.md) | TencentOS Server 全栈运维诊断，根据用户的自然语言描述，自动识别需要的能力接口，查询能力实现，使用具体能力解决客户问题。 | 无（可选 API/账号以增强能力） |
| [`wechat-article-pro`](./skills/wechat-article-pro/) | [wechat-article-pro](./skills/wechat-article-pro/SKILL.md) | 用于：微信公众号文章发布专业版。 | 无 |
| [`wechat-article-search`](./skills/wechat-article-search/) | [wechat-article-search](./skills/wechat-article-search/SKILL.md) | 用于：搜索微信公众号文章技能。 | 无（可选 API/账号以增强能力） |
| [`wechat-miniprogram`](./skills/wechat-miniprogram/) | [wechat-miniprogram](./skills/wechat-miniprogram/SKILL.md) | WeChat Mini Program (微信小程序) development framework. Use when building WeChat mini apps with WXML t… | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`wechat-publisher`](./skills/wechat-publisher/) | [wechat-publisher](./skills/wechat-publisher/SKILL.md) | 用于：一键发布 Markdown 到微信公众号草稿箱。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`WECHAT_APP_SECRET` |
| [`wechat-viral-topic`](./skills/wechat-viral-topic/) | [wechat-viral-topic](./skills/wechat-viral-topic/SKILL.md) | 用于：公众号编辑、短视频博主、漫画作者、H5 策划必备的热点爆款策划助手。 | 无 |
| [`wechatpay-basic-payment`](./skills/wechatpay-basic-payment/) | [wechatpay-basic-payment](./skills/wechatpay-basic-payment/SKILL.md) | 微信支付基础支付解决方案，涵盖支付、退款账单、分账、商户进件、开户意愿确认，提供选型/代码示例/业务速查/质量评估/排障五大能力。 | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`wechatpay-product-coupon`](./skills/wechatpay-product-coupon/) | [wechatpay-product-coupon](./skills/wechatpay-product-coupon/SKILL.md) | 微信支付商品券接入解决方案，覆盖券类型选型、发券/核销/查询/退券/回调全链路，提供选型/示例代码/业务速查/质量评估/排障五大能力。 | 需要微信公众号/开放平台 AppID 与 AppSecret |
| [`wecom-unified`](./skills/wecom-unified/) | [wecom-unified](./skills/wecom-unified/SKILL.md) | 用于：企业微信 CLI 全能套件，覆盖通讯录、消息、文档、日程、会议、待办 6 大业务域。 | 需要企业微信应用凭证（CorpID/Secret 等） |
| [`wecom-weisheng-scrm`](./skills/wecom-weisheng-scrm/) | [wecom-weisheng-scrm](./skills/wecom-weisheng-scrm/SKILL.md) | 当用户需要查询或管理微盛企微管家（企业微信） SCRM 中的客户信息、客户标签、客户群、营销素材、活码、群发、跟进记录、聊天记录、联系人、商机、汇报、抽奖、客户日程等相关业务能力时触发。 | 需要企业微信应用凭证（CorpID/Secret 等）；需要环境变量：`SCRM_APP_KEY` |
| [`weiyun`](./skills/weiyun/) | [weiyun](./skills/weiyun/SKILL.md) | 用于：微云网盘 MCP 接口完整技能。 | 需要百度网盘 OAuth 授权；需要环境变量：`WEIYUN_MCP_TOKEN` |
| [`weread-skills`](./skills/weread-skills/) | [weread-skills](./skills/weread-skills/SKILL.md) | 微信读书助手 — 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书。 | 需要环境变量：`WEREAD_API_KEY` |

### 设计 / UI / 地图（5）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`awesome-design-md`](./skills/awesome-design-md/) | [awesome-design-md](./skills/awesome-design-md/SKILL.md) | When the user asks to build a UI **without mentioning any brand or style preference** (e.g., "帮我做… | 无 |
| [`canvas-design`](./skills/canvas-design/) | [canvas-design](./skills/canvas-design/SKILL.md) | 用途：Create beautiful visual art in 。 | 需要 Canva 授权登录 |
| [`grill-me`](./skills/grill-me/) | [grill-me](./skills/grill-me/SKILL.md) | 用途：Interview the user relentlessly about a plan or design until reaching shared understanding, resolvin。 | 无 |
| [`impeccable`](./skills/impeccable/) | [impeccable](./skills/impeccable/SKILL.md) | 基于 [Impeccable](https://impeccable.style) 项目，帮助生成**独特、生产级**的前端界面设计，避免泛 AI 审美。 | 无 |
| [`prompt-engineering-expert`](./skills/prompt-engineering-expert/) | [prompt-engineering-expert](./skills/prompt-engineering-expert/SKILL.md) | 用途：Advanced expert in prompt engineering, custom instructions design, and prompt optimization for AI ag。 | 无 |

### 通信 / 邮件 / 日历（11）

| 目录 | 名称 | 用来做什么 | 前置条件 |
|------|------|------------|----------|
| [`agent-mail`](./skills/agent-mail/) | [agentmail](./skills/agent-mail/SKILL.md) | 邮件相关能力。 | 需要环境变量：`AGENTMAIL_API_KEY`、`YOUR_API_KEY` |
| [`caldav-calendar`](./skills/caldav-calendar/) | [caldav-calendar](./skills/caldav-calendar/SKILL.md) | 邮件相关能力。 | 无 |
| [`earnings-tracker`](./skills/earnings-tracker/) | [earnings-tracker](./skills/earnings-tracker/SKILL.md) | 用于：AI 驱动的财报追踪器，自动扫描 A 股/美股财报日历，推送重要财报更新。 | 无 |
| [`email-skill`](./skills/email-skill/) | [email-skill](./skills/email-skill/SKILL.md) | 邮件相关能力。 | 需要环境变量：`EMAIL_PASSWORD` |
| [`gmail`](./skills/gmail/) | [gmail](./skills/gmail/SKILL.md) | 邮件相关能力。 | 需要环境变量：`MATON_API_KEY`、`YOUR_API_KEY` |
| [`gog`](./skills/gog/) | [gog](./skills/gog/SKILL.md) | 邮件相关能力。 | 无 |
| [`himalaya`](./skills/himalaya/) | [himalaya](./skills/himalaya/SKILL.md) | 邮件相关能力。 | 无 |
| [`imap-smtp-email`](./skills/imap-smtp-email/) | [imap-smtp-email](./skills/imap-smtp-email/SKILL.md) | 邮件相关能力。 | 无（可选 API/账号以增强能力） |
| [`outbound-engine`](./skills/outbound-engine/) | [outbound-engine](./skills/outbound-engine/SKILL.md) | 邮件相关能力。 | 需要环境变量：`APOLLO_API_KEY`、`INSTANTLY_API_KEY`、`LEADMAGIC_API_KEY`、`SMTP_PASSWORD` |
| [`porteden-email`](./skills/porteden-email/) | [porteden-email](./skills/porteden-email/SKILL.md) | 邮件相关能力。 | 需要环境变量：`PE_API_KEY` |
| [`qq-email`](./skills/qq-email/) | [qq-email](./skills/qq-email/SKILL.md) | QQ邮箱 IMAP receive and SMTP send via Node.js scripts; credentials read from env vars QQ_EMAIL_ACCO… | 需要腾讯位置服务 Key（可用体验通道） |

## 2. 连接器 `connectors/`

连接器对接外部 MCP；**使用前几乎都要在 WorkBuddy 里启用并完成账号授权**。

| 目录 | 名称 | 用来做什么 | 前置条件 | skill 数 |
|------|------|------------|----------|---------|
| [`agentkey`](./connectors/agentkey/) | [AgentKey](./connectors/agentkey/skills/SKILL.md) | AgentKey 是 AI 助手获取可信工具和实时数据的能力市场。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`anydev`](./connectors/anydev/) | [AnyDev云研发](./connectors/anydev/skills/SKILL.md) | 云研发的Skill服务，为大模型赋予AnyDev环境的全生命周期管理能力：支持查询和智能推荐环境模板、一键创建云研发环境，能够远程执行命令、上传文件、自动化部署，也可以按需开启 SSH 连接、调整环境 CPU/内存/磁盘配置、锁定环境… | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`awesun`](./connectors/awesun/) | [向日葵远程控制](./connectors/awesun/skills/SKILL.md) | 通过命令行管理远端设备，实时监测在线状态、秒级发起远程控制、快速传输文件及远程截屏。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`baidu-netdisk`](./connectors/baidu-netdisk/) | [baidu-netdisk](./connectors/baidu-netdisk/skills/SKILL.md) | 连接器「baidu-netdisk」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要百度网盘 OAuth 授权 | 1 |
| [`bugly`](./connectors/bugly/) | [bugly质量概览](./connectors/bugly/skills/SKILL.md) | 查看产品的质量概览 包括崩溃率 anr率 foom（oom）率 启动耗时。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`bugly-token`](./connectors/bugly-token/) | [Bugly 质量概览](./connectors/bugly-token/skills/SKILL.md) | 查看产品的质量概览 包括崩溃率 anr率 foom（oom）率 启动耗时。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`BUGLY_ACCESS_TOKEN` | 1 |
| [`canva`](./connectors/canva/) | [Canva可画](./connectors/canva/skills/SKILL.md) | 无缝调用Canva可画的设计能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要 Canva 授权登录 | 1 |
| [`cloudbase`](./connectors/cloudbase/) | [cloudbase](./connectors/cloudbase/skills/SKILL.md) | 云开发/部署相关。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`CLOUDBASE_API_KEY`、`JWT_SECRET` | 30 |
| [`cnb-api`](./connectors/cnb-api/) | [CNB](./connectors/cnb-api/skills/SKILL.md) | 通过自然语言管理 CNB 平台：仓库、Issue、PR、流水线、制品库等操作。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`cnb-woa`](./connectors/cnb-woa/) | [cnb-woa](./connectors/cnb-woa/skills/SKILL.md) | 连接器「cnb-woa」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`ctrip-wendao`](./connectors/ctrip-wendao/) | [ctrip-wendao](./connectors/ctrip-wendao/skills/SKILL.md) | 连接器「ctrip-wendao」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`WENDAO_API_KEY` | 1 |
| [`dingtalk`](./connectors/dingtalk/) | [dingtalk](./connectors/dingtalk/skills/SKILL.md) | 连接器「dingtalk」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`edgeone-pages`](./connectors/edgeone-pages/) | [edgeone-pages](./connectors/edgeone-pages/skills/SKILL.md) | 连接器「edgeone-pages」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`fbs-connector`](./connectors/fbs-connector/) | [福帮手](./connectors/fbs-connector/skills/SKILL.md) | 福帮手人机协同连接器：面向 WorkBuddy 的身份识别、场景包查询、首值与继续使用记录、乐包状态确认和超级合伙人交接。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`feishu`](./connectors/feishu/) | [feishu](./connectors/feishu/) | 飞书办公协作相关能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 27 |
| [`fyopen-lawsearch`](./connectors/fyopen-lawsearch/) | [法研·法律法规检索](./connectors/fyopen-lawsearch/skills/SKILL.md) | 法研·法律法规检索，支持自然语言获取精准、现行有效的法规条文，将高质量、海量的法规知识库，无缝接入各类AI应用与工作流中。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`gildata`](./connectors/gildata/) | [gildata](./connectors/gildata/) | 连接器「gildata」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`GILDATA_TOKEN` | 3 |
| [`github`](./connectors/github/) | [github](./connectors/github/skill/SKILL.md) | Git/GitHub 开发协作。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要 GitHub Token 或 `gh auth login` | 1 |
| [`github-remote`](./connectors/github-remote/) | [github-remote](./connectors/github-remote/skill/SKILL.md) | Git/GitHub 开发协作。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要 GitHub Token 或 `gh auth login` | 1 |
| [`gmail`](./connectors/gmail/) | [gmail](./connectors/gmail/) | 邮件相关能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`EMAIL_PASSWORD` | 0 |
| [`gongfeng-woa`](./connectors/gongfeng-woa/) | [Gongfeng](./connectors/gongfeng-woa/) | 工蜂 API 的 MCP 服务器，支持仓库管理、文件操作等功能。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`ima-mcp`](./connectors/ima-mcp/) | [ima-mcp](./connectors/ima-mcp/) | MCP 工具相关。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`iwiki-woa`](./connectors/iwiki-woa/) | [iWiki](./connectors/iwiki-woa/) | iWiki的MCP服务，为大模型赋予文档创建、检索等能力：支持创建 iWiki 文档、Markdown 文档，能够通过检索找出相关联的文档，也可以获取空间、文档的基本信息和元数据信息。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`jira`](./connectors/jira/) | [jira](./connectors/jira/) | 连接器「jira」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`ATLASSIAN_API_TOKEN`、`JIRA_API_TOKEN` | 0 |
| [`kdocs`](./connectors/kdocs/) | [kdocs](./connectors/kdocs/SKILL.md) | 连接器「kdocs」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`KINGSOFT_DOCS_TOKEN` | 1 |
| [`km`](./connectors/km/) | [KM](./connectors/km/skills/SKILL.md) | KM官方MCP，发现腾讯精彩。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`lexiang`](./connectors/lexiang/) | [lexiang](./connectors/lexiang/skill/SKILL.md) | 连接器「lexiang」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 8 |
| [`mastergo-vibe-mcp`](./connectors/mastergo-vibe-mcp/) | [mastergo](./connectors/mastergo-vibe-mcp/skills/SKILL.md) | 连接 MasterGo 画布，让 AI 进行设计、修改、同步和获取 D2C 代码。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`neo-crm`](./connectors/neo-crm/) | [销售易CRM](./connectors/neo-crm/skills/SKILL.md) | 用自然语言查客户、推商机、盘线索、领公海、写跟进，一句话打通销售工作闭环。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`netease-mail`](./connectors/netease-mail/) | [netease-mail](./connectors/netease-mail/skills/SKILL.md) | 邮件相关能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`notion`](./connectors/notion/) | [notion](./connectors/notion/) | 连接器「notion」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要 Notion Integration Token | 4 |
| [`patsnap-search`](./connectors/patsnap-search/) | [智慧芽专利&文献融合检索](./connectors/patsnap-search/skills/SKILL.md) | 在智慧芽全球专利数据库和文献库中进行融合检索，支持自然语言、语义搜索、关键词检索和多维过滤，并获取专利或文献信息。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`PATSNAP_API_KEY` | 1 |
| [`pkulaw`](./connectors/pkulaw/) | [北大法宝·法律智能检索](./connectors/pkulaw/skills/SKILL.md) | 语义（自然语言描述） + 关键词（精确/模糊查询）双模式检索法规与案例，结果均带 pkulaw.com 原文链接，可追溯、可复核、可直接引用。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`qcc-company`](./connectors/qcc-company/) | [企查查](./connectors/qcc-company/skills/SKILL.md) | 查询和核实企业工商登记信息。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`qingflow`](./connectors/qingflow/) | [轻流](./connectors/qingflow/skills/SKILL.md) | 轻流无代码平台连接器。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`QINGFLOW_TOKEN` | 1 |
| [`qixinhuiyan-mcp`](./connectors/qixinhuiyan-mcp/) | [启信慧眼](./connectors/qixinhuiyan-mcp/) | 通过启信慧眼 MCP 接入企业全景数据能力，支持用户用自然语言完成企业搜索、工商画像、风险识别、经营动态、知识产权等商业情报分析。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`QIXIN_API_KEY` | 0 |
| [`qq-mail`](./connectors/qq-mail/) | [qq-mail](./connectors/qq-mail/skills/SKILL.md) | 邮件相关能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`region-insight`](./connectors/region-insight/) | [Region Insight](./connectors/region-insight/) | 区域洞察提供 POI 定位、围栏内 POI 查询与聚合能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`REGION_INSIGHT_API_KEY` | 1 |
| [`supabase`](./connectors/supabase/) | [supabase](./connectors/supabase/) | 连接器「supabase」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`tapd`](./connectors/tapd/) | [TAPD](./connectors/tapd/) | 管理需求、缺陷、任务和迭代。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`tapd-woa`](./connectors/tapd-woa/) | [TAPD（司内版）](./connectors/tapd-woa/) | TAPD MCP工具通过MCP协议操作TAPD中的各类资源，包括需求、缺陷、任务、迭代、测试用例、wiki和评论等。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`tc-chengxin`](./connectors/tc-chengxin/) | [同程程心](./connectors/tc-chengxin/skills/SKILL.md) | 同程程心可通过自然语言查询机票、火车票、酒店、景点、度假产品等旅行资源，支持火空联程、智能交通推荐、特价机票搜索、景区门票预订，以及完整行程规划，显著提升出行效率。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tdx-connector`](./connectors/tdx-connector/) | [通达信股票](./connectors/tdx-connector/skills/SKILL.md) | 通过通达信 MCP 查询全球股票行情数据、条件选股、研究报告、公告资讯和宏观信息。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tec-do`](./connectors/tec-do/) | [Tec-Do 2.0 Ad & Growth Intelligence](./connectors/tec-do/skills/SKILL.md) | 面向出海广告投放和增长团队的 AI 能力集合。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tencent-docs`](./connectors/tencent-docs/) | [tencent-docs](./connectors/tencent-docs/) | 连接器「tencent-docs」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`tencent-docs-oa`](./connectors/tencent-docs-oa/) | [tencent-docs-oa](./connectors/tencent-docs-oa/) | 连接器「tencent-docs-oa」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`tencent-health-nges`](./connectors/tencent-health-nges/) | [腾讯健康NGES](./connectors/tencent-health-nges/) | 腾讯健康NGES MCP服务，支持智能问数和合规审核等功能。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tencent-map`](./connectors/tencent-map/) | [腾讯地图](./connectors/tencent-map/) | 接入腾讯地图各类位置服务，包括地点搜索、路线规划（驾车/公交/步行/骑行）、地址正逆解析、沿途搜索和天气查询等。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要腾讯位置服务 Key（可用体验通道） | 0 |
| [`tencent-qidian-cs`](./connectors/tencent-qidian-cs/) | [腾讯企点客服](./connectors/tencent-qidian-cs/skills/SKILL.md) | 腾讯企点客服连接器：用自然语言处理工单（查询/创建/更新/状态变更）、查询坐席在线与实时接待、检索/拉取客户资料、拉取人工/大模型/文本机器人的会话记录和消息、查看客服实时监控、会话监控、客服满意度与响应度报表等数据。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tencent-survey`](./connectors/tencent-survey/) | [tencent-survey](./connectors/tencent-survey/skills/SKILL.md) | 连接器「tencent-survey」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tencent-weiyun`](./connectors/tencent-weiyun/) | [tencent-weiyun](./connectors/tencent-weiyun/skills/SKILL.md) | 连接器「tencent-weiyun」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要百度网盘 OAuth 授权；需要环境变量：`WEIYUN_ACCESS_TOKEN`、`WEIYUN_MCP_TOKEN` | 1 |
| [`tencentads`](./connectors/tencentads/) | [tencentads](./connectors/tencentads/) | 连接器「tencentads」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 7 |
| [`tmeet`](./connectors/tmeet/) | [tmeet](./connectors/tmeet/skills/SKILL.md) | 连接器「tmeet」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tongzhou-fin-research`](./connectors/tongzhou-fin-research/) | [同舟金融研究](./connectors/tongzhou-fin-research/skills/SKILL.md) | 连接公开行情、研报检索、行业图谱与同舟投研材料，为股市研究提供可复核证据。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`tyc-mcp`](./connectors/tyc-mcp/) | [天眼查](./connectors/tyc-mcp/skills/SKILL.md) | 通过天眼查 MCP 查询多维度企业数据。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`TIANYANCHA_API_KEY` | 1 |
| [`wecom`](./connectors/wecom/) | [wecom](./connectors/wecom/) | 企业微信相关能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 9 |
| [`weisheng-scrm`](./connectors/weisheng-scrm/) | [weisheng-scrm](./connectors/weisheng-scrm/skills/SKILL.md) | 连接器「weisheng-scrm」：对接第三方服务。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要企业微信应用凭证（CorpID/Secret 等）；需要环境变量：`SCRM_APP_KEY` | 1 |
| [`westock-mcp`](./connectors/westock-mcp/) | [腾讯自选股](./connectors/westock-mcp/skills/SKILL.md) | 直连腾讯自选股，实时掌握毫秒级行情与资金动态，用自然语言分析自选数据、设置股价提醒、管理模拟交易，轻松搞定盯盘与投资决策。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`wk-workbuddy`](./connectors/wk-workbuddy/) | [威科先行](./connectors/wk-workbuddy/skills/SKILL.md) | 威科先行依托全面、准确、及时更新的法规、案例等法律数据研发的MCP服务，支持语义检索、关键词检索等场景。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`xiaoe-cloud-cli`](./connectors/xiaoe-cloud-cli/) | [小鹅通](./connectors/xiaoe-cloud-cli/skills/SKILL.md) | 用自然语言管理小鹅通店铺：查询课程与学员，创建和编辑课程，查看订单，并查找或上传图片、音频、电子书和文档素材。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`yingmi-mcp`](./connectors/yingmi-mcp/) | [盈米MCP](./connectors/yingmi-mcp/skills/SKILL.md) | 查询基金与市场数据，完成基金研究、组合分析、财富规划及金融内容生成。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`YINGMI_API_KEY` | 1 |
| [`yuandian-mcp`](./connectors/yuandian-mcp/) | [华宇元典法律数据](./connectors/yuandian-mcp/) | 华宇元典法律数据为智能体提供法律法规、案例文书、企业信息 MCP 工具能力。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`yzf-invoice-mcp-server`](./connectors/yzf-invoice-mcp-server/) | [云帐房AI开票](./connectors/yzf-invoice-mcp-server/skills/SKILL.md) | 通过自然语言使用云帐房 AI 开票能力，完成开票信息识别、商品税收分类匹配，并前往电子税局开票。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |
| [`zfs-fssc-ai`](./connectors/zfs-fssc-ai/) | [中兴新云AI智报](./connectors/zfs-fssc-ai/skills/SKILL.md) | 财务云 AI 报销助手：用自然语言完成报销申请、发票查询识别、报销单查询与费用审批等操作。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权；需要环境变量：`ZFS_PASSWORD` | 1 |
| [`zhiyan-cicd`](./connectors/zhiyan-cicd/) | [智研构建部署](./connectors/zhiyan-cicd/) | 智研构建部署官方MCP，操作能力支持TKE容器部署，查询能力包括：流水线执行记录、制品版本、发布评审单、部署历史等。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 0 |
| [`zsxq`](./connectors/zsxq/) | [知识星球](./connectors/zsxq/) | 用自然语言管理知识星球：浏览星球内容、发帖评论、搜索主题、回答问题、管理笔记、查看用户信息。 | 需要在 WorkBuddy 中启用该连接器并完成登录/授权 | 1 |

## 3. 专家包 `experts/`

目录总表：[`expert_center.json`](./experts/expert_center.json)

### 产品设计（18）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`adort-design-expert`](./experts/adort-design-expert/) | [林觉初](./experts/adort-design-expert/) | 单人专家 | 精通 Ardot 设计软件，既能在画布上构建精准 UI，也能将设计稿直接生成前端代码。 | 无 |
| [`ai-image-prompt-engineer`](./experts/ai-image-prompt-engineer/) | [画令令](./experts/ai-image-prompt-engineer/) | 单人专家 | 精通AI图像生成的语言密码，将抽象视觉概念转化为精准提示词。 | 无 |
| [`behavioral-nudge-engine`](./experts/behavioral-nudge-engine/) | [助推推](./experts/behavioral-nudge-engine/README.md) | 单人专家 | 运用行为经济学设计产品助推机制，引导用户做出更好的决策。 | 无（可选 API/账号以增强能力） |
| [`delightful-experience-designer`](./experts/delightful-experience-designer/) | [惊喜喜](./experts/delightful-experience-designer/) | 单人专家 | 专注于在品牌体验中注入意想不到的愉悦时刻。 | 无 |
| [`design-engine`](./experts/design-engine/) | [设计原型专家团](./experts/design-engine/README.md) | 专家团 | 6 角色 AI 设计团队，覆盖从需求发现到品牌级原型交付的完整工作流，内置 71 套设计系统。 | 无 |
| [`design-md-architect`](./experts/design-md-architect/) | [规范范](./experts/design-md-architect/) | 单人专家 | 基于58个品牌参考库，生成设计系统规范文档并直接输出高质量HTML/CSS页面与UI组件代码。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`design-prototype-expert`](./experts/design-prototype-expert/) | [小花创意](./experts/design-prototype-expert/README.md) | 单人专家 | 设计系统驱动的高保真原型专家。 | 无 |
| [`design-to-code`](./experts/design-to-code/) | [图变码](./experts/design-to-code/README.md) | 单人专家 | 将 Figma 设计稿和截图转换为可直接使用的代码组件，内置无障碍性支持。 | 无（可选 API/账号以增强能力） |
| [`diversity-visual-expert`](./experts/diversity-visual-expert/) | [多元元](./experts/diversity-visual-expert/) | 单人专家 | 致力于消除AI图像中的系统性偏见，确保视觉内容文化准确和包容。 | 无 |
| [`feedback-synthesis-analyst`](./experts/feedback-synthesis-analyst/) | [听声声](./experts/feedback-synthesis-analyst/README.md) | 单人专家 | 从海量用户反馈中提炼有价值洞察，将用户声音转化为改进方向。 | 无（可选 API/账号以增强能力） |
| [`mermaid-diagram-expert`](./experts/mermaid-diagram-expert/) | [绘灵](./experts/mermaid-diagram-expert/README.md) | 单人专家 | 将自然语言转化为专业级Mermaid图表，支持6种图表类型、15种主题配色，秒级渲染出版级SVG与ASCII可视化。 | 无（可选 API/账号以增强能力） |
| [`product-management`](./experts/product-management/) | [产品通](./experts/product-management/README.md) | 单人专家 | 产品管理工具集：功能规格编写、路线图规划、利益相关者沟通、用户研究综合、竞品分析和指标追踪。 | 无（可选 API/账号以增强能力） |
| [`product-strategy-team`](./experts/product-strategy-team/) | [产品战略团队](./experts/product-strategy-team/) | 专家团 | 由产品总监领导的 5 人产品专家团队：需求分析师（PRD/功能规格书）、用户研究员（调研综合分析）、竞品分析师（竞争情报）、数据分析师（指标追踪）和路线图规划师（路线图管理/迭代规划）。 | 无 |
| [`sprint-priority-manager`](./experts/sprint-priority-manager/) | [排序序](./experts/sprint-priority-manager/README.md) | 单人专家 | 在有限迭代周期内做出最优优先级决策，确保Sprint交付最大价值。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`ui-designer`](./experts/ui-designer/) | [像素君](./experts/ui-designer/) | 单人专家 | 精通设计系统和组件库，追求像素级完美，打造无障碍用户界面。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`user-experience-architect`](./experts/user-experience-architect/) | [体验达](./experts/user-experience-architect/) | 单人专家 | 为开发者提供坚实的技术基础和CSS系统，是设计与开发之间的桥梁。 | 无 |
| [`user-experience-researcher`](./experts/user-experience-researcher/) | [探真真](./experts/user-experience-researcher/) | 单人专家 | 用真实数据而非假设验证设计决策，专精用户行为分析和可用性测试。 | 无 |
| [`visual-storytelling-expert`](./experts/visual-storytelling-expert/) | [图说说](./experts/visual-storytelling-expert/) | 单人专家 | 擅长将复杂信息转化为引人入胜的视觉故事。 | 无 |

### 全球发展（21）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`brazil-company-query`](./experts/brazil-company-query/) | [巴西商务拓展专家](./experts/brazil-company-query/README.md) | 单人专家 | 排查巴西企业工商与信用风险，尽调专利商标知识产权，分析市场拓展路径，降低商务拓展风险。 | 无 |
| [`brazil-legal`](./experts/brazil-legal/) | [Brazil Legal Expert](./experts/brazil-legal/README.md) | 单人专家 | 巴西公司注册、合同审查、知识产权、产品准入、劳动用工、数据合规及争议解决，助力企业合规出海巴西。 | 无 |
| [`brazil-rfb-expert`](./experts/brazil-rfb-expert/) | [Brazil Finance & Tax Expert](./experts/brazil-rfb-expert/README.md) | 单人专家 | 服务企业出海巴西的财税全周期：本地补贴、税制设计、跨境资金规划与日常合规，内置完整财税政策。 | 无 |
| [`egypt-marketing`](./experts/egypt-marketing/) | [埃及市场营销专家](./experts/egypt-marketing/README.md) | 单人专家 | 中国企业出海埃及的CMO级营销引擎，覆盖数字生态、斋月营销、品牌本地化、消费者洞察与ROI预估全链路。 | 无 |
| [`egypt-public-affairs`](./experts/egypt-public-affairs/) | [Egypt Public Affairs](./experts/egypt-public-affairs/README.md) | 单人专家 | 精通埃及政府关系、政策解读、监管沟通、行业协会、危机公关和舆情管理，服务企业一站式公共事务咨询。 | 无 |
| [`egypt-strategic-advisory`](./experts/egypt-strategic-advisory/) | [Egypt Strategic Advisory](./experts/egypt-strategic-advisory/) | 单人专家 | 精通埃及宏观环境、产业趋势、竞争格局和风险管控，提供投资选址、进入模式和长期布局决策建议。 | 无 |
| [`indonesia-bd-expert`](./experts/indonesia-bd-expert/) | [印尼商务拓展专家](./experts/indonesia-bd-expert/README.md) | 单人专家 | 整合全链路客供与渠道资源，洞察园区展会招商契机，锚定市场进入路径，打造产业合作生态与合规风控护航。 | 无 |
| [`indonesia-digital-law-expert`](./experts/indonesia-digital-law-expert/) | [印尼法务合规专家](./experts/indonesia-digital-law-expert/README.md) | 单人专家 | 聚焦外商投资、数据合规与商业交易，打通营商审批、金融监管与知识产权保护链路，赋能跨境SaaS与AI等新兴赛道全流程印尼法务保障。 | 无 |
| [`indonesia-pa-expert`](./experts/indonesia-pa-expert/) | [Indo Pub Affair](./experts/indonesia-pa-expert/README.md) | 单人专家 | 剖析印尼政商生态与合规风险，整合政策解读危机公关，融合本土宗教文化，输出落地GR策略。 | 无（可选 API/账号以增强能力） |
| [`malaysia-finance-tax`](./experts/malaysia-finance-tax/) | [马来西亚财税金融专家](./experts/malaysia-finance-tax/README.md) | 单人专家 | 精通马来西亚税务、银行、外汇、审计、补贴、保险、伊斯兰金融及财政分析的财税金融全栈专家。 | 无 |
| [`malaysia-hr-admin`](./experts/malaysia-hr-admin/) | [Malaysia HR & Administration](./experts/malaysia-hr-admin/README.md) | 单人专家 | 精通马来西亚招聘、劳动合同、薪酬福利、签证工签与社保，服务企业跨境人力行政咨询。 | 无 |
| [`malaysia-legal`](./experts/malaysia-legal/) | [Malaysia Legal & Compliance](./experts/malaysia-legal/README.md) | 单人专家 | 精通马来西亚公司注册、合同、知识产权、行业准入与数据合规，服务跨境法务合规咨询。 | 无 |
| [`malaysia-marketing`](./experts/malaysia-marketing/) | [大马营销通](./experts/malaysia-marketing/README.md) | 单人专家 | 深谙马来西亚文化与宗教，覆盖消费者画像、品牌本地化、社媒投放与用户增长，生成营销海报与短视频。 | 无 |
| [`sg-biz-dev`](./experts/sg-biz-dev/) | [Sg Business](./experts/sg-biz-dev/README.md) | 单人专家 | 帮助企业在新加坡发现客户、伙伴、渠道、供应商与代理商，对接园区、展会、招商及确认市场进入路径。 | 无 |
| [`sg-finance-tax`](./experts/sg-finance-tax/) | [Sg Finance & Tax](./experts/sg-finance-tax/README.md) | 单人专家 | 精通企业在新加坡经营中的税务、会计、银行、融资、外汇、支付、审计、补贴、保险和财务规划等内容。 | 无 |
| [`sg-hr-admin-expert`](./experts/sg-hr-admin-expert/) | [Sg HR & Admin](./experts/sg-hr-admin-expert/README.md) | 单人专家 | 精通新加坡当地招聘、劳动合同、薪酬福利、签证工签、社保、办公场地、行政流程和员工管理等内容。 | 无 |
| [`thai-marketing-creative`](./experts/thai-marketing-creative/) | [泰国市场营销专家](./experts/thai-marketing-creative/README.md) | 单人专家 | 整合全链路用户洞察与行为决策，锚定本土松弛悦己情绪切口，打通泰语市场转化路径，输出泰国市场营销方案。 | 无 |
| [`thailand-hr-admin`](./experts/thailand-hr-admin/) | [Thai HR&Admin](./experts/thailand-hr-admin/README.md) | 单人专家 | 精通泰国劳动法(LPA)、外籍员工工签合规、薪酬福利设计与本土职场文化适配，护航中资企业出海泰国全周期人力行政。 | 无 |
| [`uae-marketing-advisor`](./experts/uae-marketing-advisor/) | [UAE Marketing Expert](./experts/uae-marketing-advisor/README.md) | 单人专家 | 覆盖阿联酋不同地区差异化营销。 | 无 |
| [`uae-public-affairs`](./experts/uae-public-affairs/) | [阿联酋公共事务专家](./experts/uae-public-affairs/README.md) | 单人专家 | 专注阿联酋政府关系、政策解读与监管沟通，为中企及投资机构提供专业公共事务咨询与风险评估服务。 | 无 |
| [`uae-strategic-advisor`](./experts/uae-strategic-advisor/) | [阿联酋战略顾问专家](./experts/uae-strategic-advisor/README.md) | 单人专家 | 研判阿联酋七酋长国宏观环境与产业趋势，对比竞合格局与投资选址，评估进入模式与风险，输出出海战略建议。 | 无 |

### 内容创作（41）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`ai-content-creator-team`](./experts/ai-content-creator-team/) | [内容创作专家团](./experts/ai-content-creator-team/README.md) | 专家团 | AI驱动的多模态内容生产团队，从创意策划到成品交付全覆盖，涵盖品牌定位、情绪板、广告方向、文案创作、视频生成、图片设计、精修合成和素材改编。 | 无 |
| [`ai-humanizer`](./experts/ai-humanizer/) | [鹏城信息AI专家](./experts/ai-humanizer/README.md) | 单人专家 | 识别24种AI写作模式与500+词汇，统计突发性与多样性，重写为自然真实的人类表达，彻底消除机器味。 | 无 |
| [`ai-shifu`](./experts/ai-shifu/) | [AI师傅](./experts/ai-shifu/README.md) | 单人专家 | 基于你的教学需求和原始内容(PPT、Word、PDF、txt等)，帮你快速做门AI一对一互动课。 | 无（可选 API/账号以增强能力） |
| [`ai-shifu-expert`](./experts/ai-shifu-expert/) | [AI师傅](./experts/ai-shifu-expert/README.md) | 单人专家 | 基于你的教学需求和原始内容(PPT、Word、PDF、txt等)，帮你快速做门AI一对一互动课。 | 无 |
| [`ai-video-script`](./experts/ai-video-script/) | [鹏城信息AI专家](./experts/ai-video-script/README.md) | 单人专家 | 依据主题或关键词生成完整视频脚本，涵盖分镜表、画面提示词、配音文案与字幕，适配主流AI生成工具及抖音、B站平台。 | 无 |
| [`bilibili-content-strategist`](./experts/bilibili-content-strategist/) | [弹幕幕](./experts/bilibili-content-strategist/README.md) | 单人专家 | 精通B站平台生态和年轻用户偏好，打造高播放量视频策略。 | 无 |
| [`book-co-creator`](./experts/book-co-creator/) | [著书书](./experts/book-co-creator/README.md) | 单人专家 | 与作者深度协作，帮助规划书籍结构和内容，达到出版级品质。 | 无（可选 API/账号以增强能力） |
| [`chatcut-video-editor`](./experts/chatcut-video-editor/) | [一站式视频创作专家](./experts/chatcut-video-editor/README.md) | 单人专家 | AI 视频剪辑与素材生成：剪辑、字幕、转场、特效，并生成视频/图片/音乐/配音，保持可手动编辑的多轨时间线，支持导出 Pr / DaVinci 工程文件。 | 无 |
| [`content-creation-expert-prod`](./experts/content-creation-expert-prod/) | [汽车行业内容创作专家团](./experts/content-creation-expert-prod/README.md) | 专家团 | 汽车行业垂类图文创作团队，5 人协作完成选题、撰写、智能配图与质检，一键交付懂车帝、小红书等风格图文。 | 无 |
| [`content-creator`](./experts/content-creator/) | [文博凯](./experts/content-creator/README.md) | 单人专家 | 擅长创作引人入胜的多平台内容，让品牌故事触达目标受众。 | 无 |
| [`content-distribution-team`](./experts/content-distribution-team/) | [全域内容分发专家团](./experts/content-distribution-team/README.md) | 专家团 | 一站式多平台内容分发方案，覆盖13+全球社交媒体平台（含微信视频号），提供发布规则适配、排期管理、批量发布编排、跨平台数据分析和小红书自动化发布能力。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`LIBTV_ACCESS_KEY`、`WECHAT_APPID`、`WECHAT_SECRET` |
| [`content-writer`](./experts/content-writer/) | [鹏城信息AI专家](./experts/content-writer/README.md) | 单人专家 | 专注为小红书、知乎、公众号、抖音生成平台原生的可发布内容，含标题钩子、正文结构与转化引导，匹配各平台字数规范。 | 无 |
| [`douyin-strategist`](./experts/douyin-strategist/) | [斗音音](./experts/douyin-strategist/README.md) | 单人专家 | 精通抖音算法和内容生态，打造短视频爆款并实现商业化变现。 | 无 |
| [`frontend-slides`](./experts/frontend-slides/) | [鹏城信息AI专家](./experts/frontend-slides/README.md) | 单人专家 | 零依赖打造动画丰富的网页演示文稿，支持从零创建、PPTX转换与幻灯片增强，提供风格预览、在线部署与PDF导出。 | 无 |
| [`humanize-ppt-team`](./experts/humanize-ppt-team/) | [PPT大纲、生成、视频、演示与交付专家团](./experts/humanize-ppt-team/README.md) | 专家团 | 把原始资料梳理成人感PPT大纲，调度HTML生成、演讲模式、视频动效与交付质检，形成可演示成果。 | 无（可选 API/账号以增强能力） |
| [`instagram-operations-expert`](./experts/instagram-operations-expert/) | [晒图图](./experts/instagram-operations-expert/README.md) | 单人专家 | 精通Instagram视觉美学和内容策略，打造令人向往的品牌形象。 | 无 |
| [`kdocs-doc-butler`](./experts/kdocs-doc-butler/) | [金山文档文档管家助手](./experts/kdocs-doc-butler/README.md) | 单人专家 | 金山文档出品一站式管理金山文档全生命周期：新建各类在线文档、按关键词快速搜索定位、AI 按主题自动分类整理文件夹、批量移动重命名、生成分享链接与权限管理、读取文档内容输出为 Markdown。 | 需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`kdocs-knowledge-collector`](./experts/kdocs-knowledge-collector/) | [金山文档知识收藏助手](./experts/kdocs-knowledge-collector/README.md) | 单人专家 | 金山文档出品把网页、消息、笔记等碎片内容沉淀为结构化知识资产：一键剪藏公众号与网页为云文档，AI 按主题聚合零散笔记生成整理稿，多份文档自动提炼摘要与要点，一键归档到个人知识库并智能整理已有内容。 | 需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`kdocs-pdf-toolbox`](./experts/kdocs-pdf-toolbox/) | [金山文档PDF处理助手](./experts/kdocs-pdf-toolbox/README.md) | 单人专家 | 金山文档出品PDF 文档处理一站式：按页拆分、多文件合并、提取指定页、转换为 Word/Excel/PPT、全文翻译导出（双语/指定语言）、内容读取与页数查询。 | 需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`kdocs-ppt-creator`](./experts/kdocs-ppt-creator/) | [WPS AIPPT创作助手](./experts/kdocs-ppt-creator/README.md) | 单人专家 | WPS官方出品一句话主题或一份参考文档，AI 自动设计大纲并生成包含标题页、内容页、总结页的完整 PPT，并按场景统一配色与排版。 | 无（可选 API/账号以增强能力） |
| [`kidd-content-expert`](./experts/kidd-content-expert/) | [吟游诗人基德创作专家](./experts/kidd-content-expert/) | 单人专家 | 基于深度研究报告，用基德风格创作口语化、反常识的知识视频脚本，覆盖时政财经、宇宙科普与科技前沿。 | 无 |
| [`kuaishou-strategist`](./experts/kuaishou-strategist/) | [老铁铁](./experts/kuaishou-strategist/README.md) | 单人专家 | 深谙快手下沉市场特性和老铁文化，打造接地气的内容策略。 | 无 |
| [`long-manuscript-expert`](./experts/long-manuscript-expert/) | [福帮手](./experts/long-manuscript-expert/README.md) | 单人专家 | 擅长把提纲、访谈、旧稿和零散素材整理成长文档手稿，独立完成结构规划、章节扩写与交付前质检。 | 无 |
| [`news-buddy`](./experts/news-buddy/) | [懂秘](./experts/news-buddy/) | 单人专家 | 懂你的资讯顾问。 | 无 |
| [`novel-generator`](./experts/novel-generator/) | [鹏城信息AI专家](./experts/novel-generator/README.md) | 单人专家 | 把一句话灵感扩写成完整提示词与大纲，逐章生成连贯爽文，维护角色、地点、情节一致，支持修仙、重生、都市等题材。 | 无 |
| [`podcast-strategist`](./experts/podcast-strategist/) | [声浪浪](./experts/podcast-strategist/README.md) | 单人专家 | 精通播客内容策划和增长策略，通过音频建立深度用户连接。 | 无 |
| [`ppt-implement`](./experts/ppt-implement/) | [幻灯灯](./experts/ppt-implement/) | 单人专家 | 智能 PPT 生成助手，一键将想法转化为精美演示文稿。 | 无 |
| [`promo-creator-team`](./experts/promo-creator-team/) | [袋鼠帝宣传片创作团队](./experts/promo-creator-team/README.md) | 专家团 | 6位专业角色分6阶段协作完成产品宣传片全流程制作：创意简报、逐镜头分镜、素材生产、HyperFrames剪辑合成、BGM设计与交付，从产品URL到可发布的60-90秒宣传片MP4。 | 需要环境变量：`MUREKA_API_KEY` |
| [`remotion-video-generator`](./experts/remotion-video-generator/) | [动画画](./experts/remotion-video-generator/README.md) | 单人专家 | 基于 Remotion 的视频生成专家，创建产品演示、解说视频、社交媒体内容和演示文稿。 | 无 |
| [`short-video-editing-coach`](./experts/short-video-editing-coach/) | [剪神神](./experts/short-video-editing-coach/README.md) | 单人专家 | 精通短视频剪辑技巧和节奏把控，让每条视频具有专业冲击力。 | 无 |
| [`tik-tok-strategist`](./experts/tik-tok-strategist/) | [拓刻刻](./experts/tik-tok-strategist/README.md) | 单人专家 | 精通TikTok算法和海外短视频生态，帮助品牌在全球平台爆发。 | 需要环境变量：`LIBTV_ACCESS_KEY` |
| [`topic-evaluator`](./experts/topic-evaluator/) | [科技侠来了](./experts/topic-evaluator/README.md) | 单人专家 | 双层级4维评分与5方向对比，全部评分详情、硬源清单、风险提示在对话中完整展示，报告可下载存档。 | 无 |
| [`twitter-operations-expert`](./experts/twitter-operations-expert/) | [推文文](./experts/twitter-operations-expert/README.md) | 单人专家 | 精通Twitter/X平台互动策略和话题运营，让品牌占据全球对话。 | 无 |
| [`vibeknow-handdraw`](./experts/vibeknow-handdraw/) | [vibeknow](./experts/vibeknow-handdraw/README.md) | 单人专家 | 老师讲历史、家长讲绘本、医生讲康复、理财博主讲避坑，专业内容边画边讲成手绘科普视频，51种风格随选。 | 无（可选 API/账号以增强能力） |
| [`video-dissection`](./experts/video-dissection/) | [苍何视频解剖](./experts/video-dissection/README.md) | 专家团 | 专业拆解火爆抖音视频拍摄手法的专家团。 | 需要环境变量：`ARK_API_KEY`、`DOUYIN_API_KEY`、`SILICONFLOW_API_KEY` |
| [`video-gen-team`](./experts/video-gen-team/) | [苍何视频生成团队](./experts/video-gen-team/README.md) | 专家团 | 三位一体的AI视频创作团队：灵阅负责采集AI/科技热点，灵枢负责策划选题与脚本，灵映负责渲染MP4视频成品（配音+字幕）。 | 无 |
| [`viral-topic-master`](./experts/viral-topic-master/) | [爆款炼金师](./experts/viral-topic-master/README.md) | 单人专家 | 投热点出爆款。 | 无 |
| [`wechat-official-account-expert`](./experts/wechat-official-account-expert/) | [郝文昌](./experts/wechat-official-account-expert/README.md) | 单人专家 | 精通公众号内容策略和粉丝增长，打造10万+品牌自媒体矩阵。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`WECHAT_APPID`、`WECHAT_SECRET` |
| [`weibo-strategist`](./experts/weibo-strategist/) | [热搜搜](./experts/weibo-strategist/README.md) | 单人专家 | 精通微博话题营销和舆论传播规律，让品牌在热搜持续出圈。 | 无 |
| [`xiaohongshu-operations-expert`](./experts/xiaohongshu-operations-expert/) | [薛红笙](./experts/xiaohongshu-operations-expert/README.md) | 单人专家 | 深谙小红书种草生态和推荐机制，打造高互动率种草内容。 | 无 |
| [`zhihu-strategist`](./experts/zhihu-strategist/) | [答有道](./experts/zhihu-strategist/README.md) | 单人专家 | 精通知乎推荐机制和知识营销策略，通过高质量回答建立权威。 | 无 |

### 技术工程（37）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`api-dev`](./experts/api-dev/) | [鹏城信息AI专家](./experts/api-dev/README.md) | 单人专家 | 专注接口全生命周期开发，涵盖端点搭建、自动化测试、OpenAPI文档生成、Mock服务搭建与HTTP请求问题调试，提升开发效率。 | 无 |
| [`backend-architect`](./experts/backend-architect/) | [磐石石](./experts/backend-architect/README.md) | 单人专家 | 深耕分布式系统和高并发架构，擅长将复杂业务转化为优雅技术方案。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`code`](./experts/code/) | [鹏城信息AI专家](./experts/code/README.md) | 单人专家 | 提供规划执行验证测试全流程编码指导，将复杂需求拆解为可独立验证步骤，支持多任务跟踪与偏好记忆。 | 无（可选 API/账号以增强能力） |
| [`code-review-expert`](./experts/code-review-expert/) | [火眼眼](./experts/code-review-expert/README.md) | 单人专家 | 以鹰眼标准检查每行代码，在缺陷到达生产环境之前将其拦截。 | 无 |
| [`database-operations`](./experts/database-operations/) | [鹏城信息AI专家](./experts/database-operations/README.md) | 单人专家 | 精通表结构设计、迁移与性能调优。 | 无 |
| [`dev-ops-automation-engineer`](./experts/dev-ops-automation-engineer/) | [一键达](./experts/dev-ops-automation-engineer/README.md) | 单人专家 | 将一切手动运维自动化，从CI/CD到基础设施即代码，部署一键搞定。 | 无 |
| [`dev-pipeline-orchestrator`](./experts/dev-pipeline-orchestrator/) | [鹏城信息AI专家](./experts/dev-pipeline-orchestrator/README.md) | 单人专家 | 编排开发流水线：澄清需求意图，拆解为测试驱动的细粒度任务，子代理逐任务实现并双重评审，最终集成分支。 | 无 |
| [`dockerfile-gen`](./experts/dockerfile-gen/) | [容器器](./experts/dockerfile-gen/) | 单人专家 | Dockerfile 自动生成专家，遵循容器化最佳实践。 | 无 |
| [`embedded-firmware-engineer`](./experts/embedded-firmware-engineer/) | [固件通](./experts/embedded-firmware-engineer/README.md) | 单人专家 | 精通微控制器编程，在资源受限的硬件上编写高效可靠的固件代码。 | 无 |
| [`engineering-assurance-team`](./experts/engineering-assurance-team/) | [工程保障团队](./experts/engineering-assurance-team/) | 专家团 | 由工程总监领导的 5 人工程专家团队：代码审查师（安全/性能/正确性）、架构师（系统设计/ADR）、SRE 工程师（事故响应/部署）、测试专家（测试策略/覆盖率）和技术文档师（文档/Runbook）。 | 无 |
| [`engineering-workflow-skills`](./experts/engineering-workflow-skills/) | [工序达](./experts/engineering-workflow-skills/README.md) | 单人专家 | 基于Google 工程师的《Agent Skills》打造的资深工程全流程教练：规约驱动、测试驱动、代码评审、CI/CD发布。 | 无 |
| [`eno`](./experts/eno/) | [鹏城信息AI专家](./experts/eno/README.md) | 单人专家 | 深度分析前端项目架构、技术栈选型、组件设计与构建配置，输出含评分等级、优势短板和重构优先级的结构化评审报告。 | 无 |
| [`frontend`](./experts/frontend/) | [鹏城信息AI专家](./experts/frontend/README.md) | 单人专家 | 精通响应式界面开发，遵循移动优先与可访问性，以鲜明排版与色彩构建落地页、仪表盘、表单等高保真界面。 | 无 |
| [`frontend-developer`](./experts/frontend-developer/) | [像素匠](./experts/frontend-developer/README.md) | 单人专家 | 精通现代Web技术和主流框架，以像素级精度构建响应式高性能Web应用。 | 需要环境变量：`MINIMAX_API_KEY` |
| [`git-workflow-expert`](./experts/git-workflow-expert/) | [分支通](./experts/git-workflow-expert/README.md) | 单人专家 | 精通Git高级工作流和分支策略，让团队协作像行云流水般顺畅。 | 无 |
| [`gstack`](./experts/gstack/) | [软件工坊](./experts/gstack/) | 专家团 | 6位工程专业角色：产品评审、代码审查、安全审计、QA测试、设计系统、调试运维，覆盖从想法到生产的完整软件生命周期。 | 无 |
| [`hsk-devops-expert`](./experts/hsk-devops-expert/) | [贝锐花生壳](./experts/hsk-devops-expert/README.md) | 单人专家 | 基于 HSK CLI 的 DevOps 专家，提供零配置公网预览、内网穿透、文件托管和项目部署能力。 | 无 |
| [`incident-response-commander`](./experts/incident-response-commander/) | [救火队](./experts/incident-response-commander/README.md) | 单人专家 | 系统故障时冷静指挥团队快速定位处理和恢复，是终极救火队长。 | 无 |
| [`infrastructure-operations-expert`](./experts/infrastructure-operations-expert/) | [运维通](./experts/infrastructure-operations-expert/README.md) | 单人专家 | 确保IT基础设施的持续稳定运行，一切尽在掌控。 | 无 |
| [`lsp-index-engineer`](./experts/lsp-index-engineer/) | [索引引](./experts/lsp-index-engineer/README.md) | 单人专家 | 精通语言服务器协议和代码索引技术。 | 无 |
| [`mcp-build-expert`](./experts/mcp-build-expert/) | [协议通](./experts/mcp-build-expert/README.md) | 单人专家 | 精通Model Context Protocol设计实现。 | 无 |
| [`mobile-application-developer`](./experts/mobile-application-developer/) | [掌中灵](./experts/mobile-application-developer/README.md) | 单人专家 | 精通iOS和Android原生及跨平台开发，打造流畅美观的移动应用。 | 无 |
| [`modern-webapp`](./experts/modern-webapp/) | [速构构](./experts/modern-webapp/) | 单人专家 | 现代 Web 应用开发专家，基于 React + TypeScript + Vite + Tailwind CSS + shadcn/ui 技术栈，含浏览器自动化能力。 | 需要环境变量：`APP_PASSWORD` |
| [`mvp-dev-expert-team`](./experts/mvp-dev-expert-team/) | [MVP开发专家团](./experts/mvp-dev-expert-team/README.md) | 专家团 | 说出你的想法，8位专家从调研、设计、编码、测试到部署全流程协作，帮你快速开发MVP产品。 | 需要环境变量：`JWT_SECRET`、`RESEND_API_KEY`、`SESSION_SECRET` |
| [`ncre-expert`](./experts/ncre-expert/) | [计算机等级考试专家团](./experts/ncre-expert/README.md) | 专家团 | NCRE一至四级专家团，覆盖Office、编程、数据库与网络安全，分工协作，量身定制备考方案。 | 无 |
| [`rapid-prototyping-engineer`](./experts/rapid-prototyping-engineer/) | [闪造造](./experts/rapid-prototyping-engineer/README.md) | 单人专家 | 以极快速度将创意转化为可工作的原型，让团队快速验证想法。 | 无 |
| [`rum-fullstack-team`](./experts/rum-fullstack-team/) | [腾讯云 RUM 全链路专家团](./experts/rum-fullstack-team/README.md) | 专家团 | 腾讯云 RUM 全链路服务：10 大平台 aegis SDK 接入 + WebVitals/异常/接口/资源分析，支持 RUM-APM 联动。 | 需要环境变量：`RUM_TOKEN` |
| [`security-engineer`](./experts/security-engineer/) | [盾甲甲](./experts/security-engineer/README.md) | 单人专家 | 全方位保障系统安全，在黑客之前发现并修复安全漏洞。 | 无 |
| [`senior-developer`](./experts/senior-developer/) | [吴八哥](./experts/senior-developer/README.md) | 单人专家 | 10年以上全栈经验，精通多种语言和框架，是团队的技术中坚。 | 无 |
| [`site-reliability-engineer`](./experts/site-reliability-engineer/) | [稳如山](./experts/site-reliability-engineer/README.md) | 单人专家 | 用软件工程方法论解决运维问题，确保99.99%可用性。 | 无 |
| [`software-architect`](./experts/software-architect/) | [架构通](./experts/software-architect/README.md) | 单人专家 | 站在全局高度设计可扩展高可用的软件架构，为技术团队指明方向。 | 无 |
| [`software-company`](./experts/software-company/) | [软件开发团队](./experts/software-company/) | 专家团 | 高效软件研发团队，产品经理定需求、架构师设计+拆任务、工程师批量实现代码、QA验证质量，小需求支持快速模式。 | 无 |
| [`solidity-smart-contract-engineer`](./experts/solidity-smart-contract-engineer/) | [链合约](./experts/solidity-smart-contract-engineer/README.md) | 单人专家 | 精通Solidity和EVM生态，编写安全高效的智能合约。 | 无 |
| [`superpowers-zh`](./experts/superpowers-zh/) | [AI编程方法论专家](./experts/superpowers-zh/README.md) | 单人专家 | 二十项AI编程方法论，覆盖头脑风暴、测试驱动开发、系统化调试、代码审查，适配中文文档与国内平台规范。 | 无 |
| [`terminal-integration-expert`](./experts/terminal-integration-expert/) | [终端通](./experts/terminal-integration-expert/README.md) | 单人专家 | 精通终端应用与空间计算环境的集成。 | 无 |
| [`threat-detection-engineer`](./experts/threat-detection-engineer/) | [猎威威](./experts/threat-detection-engineer/README.md) | 单人专家 | 专精构建威胁检测系统，在攻击者造成损害前发现拦截威胁。 | 无 |
| [`we-chat-mini-program-developer`](./experts/we-chat-mini-program-developer/) | [小程达](./experts/we-chat-mini-program-developer/README.md) | 单人专家 | 精通微信小程序开发框架和生态，打造流畅微信原生体验应用。 | 无 |

### 数据智能（25）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`academic-journal-selector`](./experts/academic-journal-selector/) | [万方数据](./experts/academic-journal-selector/README.md) | 专家团 | 万方数据旗下学术选刊专家团，中英双管道并行检索，覆盖中英文核心期刊，输出冲-稳-保分层投稿方案。 | 无（可选 API/账号以增强能力） |
| [`ai-data-copilot`](./experts/ai-data-copilot/) | [智数分析专家团](./experts/ai-data-copilot/README.md) | 专家团 | 6人AI数据分析团队，擅长自然语言转SQL、Python建模、RAG知识问答、仪表盘可视化与报告生成。 | 无 |
| [`ai-engineer`](./experts/ai-engineer/) | [深网网](./experts/ai-engineer/README.md) | 单人专家 | 精通ML模型开发部署优化的全栈AI工程师，将AI从论文带到生产环境。 | 无（可选 API/账号以增强能力） |
| [`aihot`](./experts/aihot/) | [数字生命卡兹克](./experts/aihot/README.md) | 单人专家 | 一句话查到每天精选的 AI 模型/产品/行业/论文动态，自动整理成中文简报，免配置免登录。 | 无 |
| [`arxiv-watcher`](./experts/arxiv-watcher/) | [鹏城信息AI专家](./experts/arxiv-watcher/README.md) | 单人专家 | 检索ArXiv最新论文，支持按关键词、作者、学科精准搜索，自动提炼摘要要点并归档至研究日志，助您持续追踪前沿学术动态。 | 无 |
| [`autonomous-optimization-architect`](./experts/autonomous-optimization-architect/) | [自进化](./experts/autonomous-optimization-architect/README.md) | 单人专家 | 专精于设计能自主优化和进化的智能系统架构，让系统越用越聪明。 | 无 |
| [`data`](./experts/data/) | [探数数](./experts/data/README.md) | 单人专家 | 数据探索专家，支持 SQL 查询、数据探索、可视化、仪表板构建、数据验证和洞察生成。 | 无 |
| [`data-analysis`](./experts/data-analysis/) | [析数数](./experts/data-analysis/) | 单人专家 | 数据分析专家，支持 Excel 电子表格的创建、编辑、分析、公式计算、格式化和数据可视化。 | 无 |
| [`data-analytics-reporter`](./experts/data-analytics-reporter/) | [舒明析](./experts/data-analytics-reporter/README.md) | 单人专家 | 将复杂数据转化为战略洞察，提供指标诊断、KPI框架设计、数据质量评估与决策报告。 | 无 |
| [`data-engineer`](./experts/data-engineer/) | [管道通](./experts/data-engineer/README.md) | 单人专家 | 构建高效可靠的数据管道和ETL流程，让数据从源头到洞察畅通无阻。 | 无 |
| [`data-integration-agent`](./experts/data-integration-agent/) | [聚数数](./experts/data-integration-agent/README.md) | 单人专家 | 将分散数据清洗整合统一，构建企业统一数据视图。 | 无 |
| [`database-optimization-expert`](./experts/database-optimization-expert/) | [索引灵](./experts/database-optimization-expert/README.md) | 单人专家 | 专精数据库性能调优和查询优化，让慢查询变快让瓶颈消失。 | 无 |
| [`deep-research`](./experts/deep-research/) | [深研研](./experts/deep-research/) | 单人专家 | 综合性深度研究专家，支持多源信息检索、事实验证、知识发现和结构化报告生成，含微信公众号文章搜索能力。 | 无 |
| [`finance-data`](./experts/finance-data/) | [财数数](./experts/finance-data/) | 单人专家 | 金融数据检索专家，通过自然语言查询 209 个金融数据 API，涵盖股票、指数、期货、债券、基金和宏观经济等 15 大类。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`fundus-disease-analysis`](./experts/fundus-disease-analysis/) | [甄瞳](./experts/fundus-disease-analysis/README.md) | 单人专家 | 基于普角与超广角眼底彩照的AI多病种分析，覆盖青光眼、糖网、AMD等数十种疾病的诊断与报告解读。 | 需要环境变量：`FUNDUS_APPID`、`FUNDUS_TOKEN` |
| [`gpt-researcher-team`](./experts/gpt-researcher-team/) | [深度研究团队](./experts/gpt-researcher-team/) | 专家团 | 深度研究报告输出，7角色5阶段聚合多源信息，经审稿修订循环输出带引用的专业报告。 | 无 |
| [`huashu-data-pro`](./experts/huashu-data-pro/) | [花叔数据分析专家团](./experts/huashu-data-pro/README.md) | 专家团 | 「一人公司」本地数据分析专家团。 | 无 |
| [`jinshuju-expert`](./experts/jinshuju-expert/) | [金数据](./experts/jinshuju-expert/README.md) | 单人专家 | 通过金数据 MCP 用自然语言搭建表单、增删改查与批量维护数据、查询套餐额度，替代登录后台手动操作。 | 需要环境变量：`ENV_SECRET`、`JINSHUJU_API_KEY`、`JINSHUJU_API_SECRET`、`YOUR_API_KEY`、`YOUR_API_SECRET` |
| [`kdocs-data-table`](./experts/kdocs-data-table/) | [金山文档智能建表助手](./experts/kdocs-data-table/README.md) | 单人专家 | 金山文档出品将群聊接龙一键转为结构化表格，一句话生成可分享的信息收集表，智能美化表格并固化规则（条件格式高亮异常值、数据校验下拉约束、区域保护锁定表头）。 | 需要环境变量：`KINGSOFT_DOCS_TOKEN` |
| [`llm-wiki`](./experts/llm-wiki/) | [知库库](./experts/llm-wiki/) | 单人专家 | 基于 Andrej Karpathy 的 LLM Wiki 模式，帮助用户构建、维护和查询持久化的个人知识库。 | 无 |
| [`model-quality-assurance-expert`](./experts/model-quality-assurance-expert/) | [模检检](./experts/model-quality-assurance-expert/README.md) | 单人专家 | 系统化评估保障AI模型质量，确保输出准确公平安全。 | 无 |
| [`prompt-engineering-expert`](./experts/prompt-engineering-expert/) | [鹏城信息AI专家](./experts/prompt-engineering-expert/README.md) | 单人专家 | 精通提示词工程，提供提示词撰写、系统提示设计、自定义指令、优化迭代与评估测试，打造高效稳定的智能体。 | 无 |
| [`sales-data-extraction-agent`](./experts/sales-data-extraction-agent/) | [拉数数](./experts/sales-data-extraction-agent/README.md) | 单人专家 | 从各类数据源中自动提取整理销售数据。 | 无 |
| [`trend-researcher`](./experts/trend-researcher/) | [风向标](./experts/trend-researcher/README.md) | 单人专家 | 持续追踪行业和技术趋势，为产品战略提供前瞻性洞察。 | 无 |
| [`vocab-craft-expert`](./experts/vocab-craft-expert/) | [词力](./experts/vocab-craft-expert/README.md) | 单人专家 | 融合间隔重复记忆科学与键盘输入训练的AI英语词汇教练，支持每日定时推送、错词强化、三种练习模式，让背单词更科学高效。 | 无 |

### 法务安全（23）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`agent-identity-trust-expert`](./experts/agent-identity-trust-expert/) | [信链链](./experts/agent-identity-trust-expert/README.md) | 单人专家 | 构建AI智能体间的身份认证和信任机制。 | 无 |
| [`blockchain-security-auditor`](./experts/blockchain-security-auditor/) | [链审审](./experts/blockchain-security-auditor/README.md) | 单人专家 | 专精区块链智能合约和DeFi协议安全审计。 | 无 |
| [`chatlaw-team`](./experts/chatlaw-team/) | [中文法律咨询团](./experts/chatlaw-team/README.md) | 专家团 | 案情采集、法条研究、判例分析、建议撰写，为民事、婚姻、合同、劳动等高频场景出具专业法律咨询报告。 | 无 |
| [`compliance-auditor`](./experts/compliance-auditor/) | [合规规](./experts/compliance-auditor/README.md) | 单人专家 | 全面审计企业运营合规性，确保符合行业标准。 | 无 |
| [`contract-expert`](./experts/contract-expert/) | [何同守](./experts/contract-expert/README.md) | 单人专家 | 覆盖合同起草、审查、谈判、背景评估与全生命周期管理；专业审查模式一键产出风险清单、审查报告与批注稿。 | 无 |
| [`enterprise-legal-team`](./experts/enterprise-legal-team/) | [企业法务专家团](./experts/enterprise-legal-team/) | 专家团 | 面向企业法务的多角色专家团，覆盖合同、交易、隐私、产品、监管、AI 治理、雇佣与知识产权分诊。 | 需要环境变量：`YD_API_KEY` |
| [`fbsir-board-secretary-assistant`](./experts/fbsir-board-secretary-assistant/) | [福帮手](./experts/fbsir-board-secretary-assistant/README.md) | 单人专家 | 面向公告、路演、投资者问答、互动回复和沟通稿，在对外使用前做合规红队审查并给出审批下一步。 | 无 |
| [`healthcare-marketing-compliance-expert`](./experts/healthcare-marketing-compliance-expert/) | [医合合](./experts/healthcare-marketing-compliance-expert/README.md) | 单人专家 | 确保医疗营销内容符合法规要求，守护信息准确性。 | 无 |
| [`huashu-doc-reviewer`](./experts/huashu-doc-reviewer/) | [花叔文档审稿专家](./experts/huashu-doc-reviewer/README.md) | 单人专家 | 为「一人公司」打造的 AI 审稿专家。 | 无 |
| [`invoice-verify-workbuddy`](./experts/invoice-verify-workbuddy/) | [智能发票专家团](./experts/invoice-verify-workbuddy/README.md) | 专家团 | 五位AI专家接力协作，通过上传文件、表格或文件夹，完成识别、税局验真、信用核查与归档。 | 需要环境变量：`OSS_ACCESS_KEY` |
| [`ip-expert`](./experts/ip-expert/) | [权知明](./experts/ip-expert/README.md) | 单人专家 | 覆盖著作权、专利、商标、商业秘密与域名，指引专业库检索，做侵权/FTO/确权分析并输出可落地策略。 | 无（可选 API/账号以增强能力） |
| [`law-student-coach`](./experts/law-student-coach/) | [法学生陪练](./experts/law-student-coach/) | 单人专家 | 面向法学生的学习陪练，训练苏格拉底问答、案例摘要、IRAC、课程大纲和律考复习。 | 无 |
| [`legal-builder-hub`](./experts/legal-builder-hub/) | [法律技能运营官](./experts/legal-builder-hub/) | 单人专家 | 面向法律运营和技能开发者的治理助手，评估技能来源、工具权限、新鲜度、许可证和信任边界。 | 无 |
| [`legal-clinic-supervisor`](./experts/legal-clinic-supervisor/) | [法律诊所督导](./experts/legal-clinic-supervisor/) | 单人专家 | 面向法学院诊所导师的监督助手，支持客户接待、研究启动、期限追踪、学生入职和学期交接。 | 无 |
| [`legal-compliance-reviewer`](./experts/legal-compliance-reviewer/) | [律守正](./experts/legal-compliance-reviewer/README.md) | 单人专家 | 确保业务运营和产品功能符合法律法规要求，防范合规风险。 | 无 |
| [`legal-search-pro`](./experts/legal-search-pro/) | [法检 Pro](./experts/legal-search-pro/README.md) | 单人专家 | 识别检索意图与场景，按法源位阶检索法规与类案，验证效力评估相似度，适配14种输出可溯源报告。 | 无 |
| [`litigation-legal`](./experts/litigation-legal/) | [诉讼法务专家](./experts/litigation-legal/) | 单人专家 | 面向诉讼律师的案件支持专家，梳理案件、证据、时间线、质证准备、索赔图表和文书草稿。 | 无 |
| [`marketing-reviewer`](./experts/marketing-reviewer/) | [营文稳](./experts/marketing-reviewer/README.md) | 单人专家 | 9维度34条规则扫描营销文案，定位广告法与隐私合规风险，输出分级Excel与HTML审查报告。 | 无 |
| [`smb-compliance`](./experts/smb-compliance/) | [严守约](./experts/smb-compliance/) | 单人专家 | 小企业客户与合规官，处理客户反馈、客诉工单、CRM清理和合同风险审查。 | 无 |
| [`soe`](./experts/soe/) | [腾讯云安全运营专家](./experts/soe/README.md) | 单人专家 | 分析腾讯云安全产品告警与离线数据，覆盖漏洞验证、入侵溯源、攻击分析，输出报告与处置建议。 | 无 |
| [`tax-compliance-team`](./experts/tax-compliance-team/) | [财税合规专家团](./experts/tax-compliance-team/README.md) | 专家团 | 覆盖票据处理、记账核算、报表编制、税务申报、合规审计五大环节的企业财税合规全链路管理专家团。 | 无 |
| [`xiaofa-litigation-assistant`](./experts/xiaofa-litigation-assistant/) | [小法同学](./experts/xiaofa-litigation-assistant/README.md) | 单人专家 | 诉讼助手：起草起诉状、要素式转换、证据整理、流程指引、强制执行、利息计算。 | 需要环境变量：`YOUR_API_KEY` |
| [`zero-knowledge-proof-admin`](./experts/zero-knowledge-proof-admin/) | [零知知](./experts/zero-knowledge-proof-admin/README.md) | 单人专家 | 精通零知识证明技术的应用和管理。 | 无 |

### 游戏空间（25）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`game-audio-engineer`](./experts/game-audio-engineer/) | [音效效](./experts/game-audio-engineer/README.md) | 单人专家 | 精通FMOD/Wwise集成和空间音频，让游戏声音栩栩如生。 | 无 |
| [`game-designer`](./experts/game-designer/) | [玩法师](./experts/game-designer/README.md) | 单人专家 | 精通游戏系统和机制设计，用循环杠杆和心理构建玩法。 | 无 |
| [`game-development-studio`](./experts/game-development-studio/) | [鹏城信息AI专家](./experts/game-development-studio/README.md) | 专家团 | 统筹策划、技术、美术、音频、质量、运营六大专业成员，以七阶段工作流驱动游戏从概念到上线流程协同开发。 | 无 |
| [`godot-game-script-engineer`](./experts/godot-game-script-engineer/) | [节点通](./experts/godot-game-script-engineer/README.md) | 单人专家 | 精通GDScript 2.0和Godot 4节点架构。 | 无 |
| [`godot-multiplayer-engineer`](./experts/godot-multiplayer-engineer/) | [联网达](./experts/godot-multiplayer-engineer/README.md) | 单人专家 | 精通Godot 4 MultiplayerAPI和网络复制。 | 无 |
| [`godot-shader-developer`](./experts/godot-shader-developer/) | [渲染达](./experts/godot-shader-developer/README.md) | 单人专家 | 精通Godot着色语言和VisualShader。 | 无 |
| [`level-designer`](./experts/level-designer/) | [关卡卡](./experts/level-designer/README.md) | 单人专家 | 将每个关卡视为精心编排的体验，用空间讲述故事。 | 无 |
| [`mac-os-spatial-metal-engineer`](./experts/mac-os-spatial-metal-engineer/) | [渲染师](./experts/mac-os-spatial-metal-engineer/README.md) | 单人专家 | 精通Apple Metal图形API和macOS空间计算开发。 | 无 |
| [`narrative-designer`](./experts/narrative-designer/) | [剧本本](./experts/narrative-designer/README.md) | 单人专家 | 将叙事和游戏玩法无缝融合，让故事与互动不可分割。 | 无 |
| [`roblox-avatar-creator`](./experts/roblox-avatar-creator/) | [捏脸达](./experts/roblox-avatar-creator/README.md) | 单人专家 | 精通Roblox UGC和虚拟形象管线。 | 无 |
| [`roblox-experience-designer`](./experts/roblox-experience-designer/) | [乐体验](./experts/roblox-experience-designer/README.md) | 单人专家 | 精通Roblox平台UX和商业化设计。 | 无 |
| [`roblox-system-script-engineer`](./experts/roblox-system-script-engineer/) | [脚本通](./experts/roblox-system-script-engineer/README.md) | 单人专家 | 精通Luau和Roblox客户端-服务器安全模型。 | 无 |
| [`technical-artist`](./experts/technical-artist/) | [技美美](./experts/technical-artist/README.md) | 单人专家 | 在美术愿景与引擎实现之间架起桥梁，精通着色器和VFX。 | 需要环境变量：`GEMINI_API_KEY` |
| [`unity-architect`](./experts/unity-architect/) | [解耦达](./experts/unity-architect/README.md) | 单人专家 | 精通ScriptableObjects和解耦系统设计。 | 无 |
| [`unity-editor-tool-developer`](./experts/unity-editor-tool-developer/) | [插件达](./experts/unity-editor-tool-developer/README.md) | 单人专家 | 精通Unity自定义EditorWindow和管线自动化。 | 无（可选 API/账号以增强能力） |
| [`unity-multiplayer-engineer`](./experts/unity-multiplayer-engineer/) | [同步达](./experts/unity-multiplayer-engineer/README.md) | 单人专家 | 精通Netcode for GameObjects和网络预测。 | 无 |
| [`unity-shader-graph-artist`](./experts/unity-shader-graph-artist/) | [着色师](./experts/unity-shader-graph-artist/README.md) | 单人专家 | 精通Unity Shader Graph和HLSL。 | 无 |
| [`unreal-multiplayer-architect`](./experts/unreal-multiplayer-architect/) | [联机达](./experts/unreal-multiplayer-architect/README.md) | 单人专家 | 精通Unreal Actor复制和服务器权威架构。 | 无 |
| [`unreal-system-engineer`](./experts/unreal-system-engineer/) | [虚幻通](./experts/unreal-system-engineer/README.md) | 单人专家 | 精通C++/Blueprint和Nanite/Lumen。 | 无 |
| [`unreal-technical-artist`](./experts/unreal-technical-artist/) | [材质通](./experts/unreal-technical-artist/README.md) | 单人专家 | 精通UE5材质编辑器和Niagara VFX。 | 无 |
| [`unreal-world-builder`](./experts/unreal-world-builder/) | [造世界](./experts/unreal-world-builder/README.md) | 单人专家 | 精通UE5 World Partition和大世界流式加载。 | 无 |
| [`vision-os-spatial-engineer`](./experts/vision-os-spatial-engineer/) | [空间通](./experts/vision-os-spatial-engineer/README.md) | 单人专家 | 精通visionOS平台开发，打造Apple Vision Pro空间应用。 | 无 |
| [`xr-cockpit-interaction-expert`](./experts/xr-cockpit-interaction-expert/) | [座舱师](./experts/xr-cockpit-interaction-expert/README.md) | 单人专家 | 专精XR环境下的座舱式交互设计。 | 无 |
| [`xr-immersive-developer`](./experts/xr-immersive-developer/) | [沉浸达](./experts/xr-immersive-developer/README.md) | 单人专家 | 精通XR沉浸式体验开发，创造身临其境的VR/MR应用。 | 无 |
| [`xr-interface-architect`](./experts/xr-interface-architect/) | [空间界](./experts/xr-interface-architect/README.md) | 单人专家 | 设计XR环境中的用户界面架构，让3D空间交互直观自然。 | 无 |

### 腾讯专区（29）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`andon-q-expert`](./experts/andon-q-expert/) | [AndonQ](./experts/andon-q-expert/README.md) | 单人专家 | 精通腾讯云全线产品，提供产品咨询、故障排查、服务报告等多维度服务的技术专家。 | 需要环境变量：`AUTHORIZE_APP_ID` |
| [`anti-scam-agent`](./experts/anti-scam-agent/) | [天御金融反诈](./experts/anti-scam-agent/README.md) | 单人专家 | 这是一款由金融黑灰产情报驱动的反诈智能体，覆盖电信网络诈骗、职业背债人、贷款包装、反催收等常见金融黑灰产，能分析、能干活、能告警。 | 无 |
| [`apm-performance-expert`](./experts/apm-performance-expert/) | [安迪](./experts/apm-performance-expert/README.md) | 单人专家 | 精通腾讯云 APM 性能诊断与调优，快速定位应用瓶颈并给出优化方案。 | 无 |
| [`capacity-expert`](./experts/capacity-expert/) | [CloudQ](./experts/capacity-expert/README.md) | 单人专家 | 容量规划专家。 | 无 |
| [`cat-network-quality-analyst`](./experts/cat-network-quality-analyst/) | [亚伦](./experts/cat-network-quality-analyst/README.md) | 单人专家 | 精通多维性能分析、异常定位、抓包诊断、问题定界，快速定位网络与服务异常根因。 | 无 |
| [`chaos-expert`](./experts/chaos-expert/) | [CloudQ](./experts/chaos-expert/README.md) | 单人专家 | 混沌演练专家。 | 无 |
| [`charity-doc-finance-expert`](./experts/charity-doc-finance-expert/) | [小益](./experts/charity-doc-finance-expert/README.md) | 单人专家 | 公益机构文书与财务一站式专家，覆盖项目申请书、结项报告、票据管理、审计准备与合规咨询，帮助公益人从繁琐行政中解放。 | 无 |
| [`cloud-ops-team`](./experts/cloud-ops-team/) | [腾讯云技术支持](./experts/cloud-ops-team/README.md) | 专家团 | 三位专家组成的运维团队 — CloudQ 负责多云统一治理与架构可视化，AndonQ 负责工单管理与智能问答，MigraQ 负责跨云迁移规划与 TCO 分析。 | 需要环境变量：`AUTHORIZE_APP_ID`、`TENCENTCLOUD_TOKEN` |
| [`contract-legal-expert`](./experts/contract-legal-expert/) | [腾讯电子签合同法务专家](./experts/contract-legal-expert/README.md) | 单人专家 | 腾讯电子签合同法务专家擅长合同起草、审查、对比、法规检索，能在线发起签署，劳动/租赁/买卖全场景覆盖。 | 需要环境变量：`ESIGN_TOKEN` |
| [`databrain-agent-v2`](./experts/databrain-agent-v2/) | [DataBrain](./experts/databrain-agent-v2/README.md) | 单人专家 | 覆盖经分取数、三方市场情报、舆情情感分析、归因下钻及跨游戏竞品对比，提供有数据支撑的专业洞察与建议。 | 需要环境变量：`DATABRAIN_TOKEN` |
| [`edgeone-makers-experts`](./experts/edgeone-makers-experts/) | [Makers 开发专家团](./experts/edgeone-makers-experts/README.md) | 专家团 | 在 EdgeOne Makers 上构建并部署 Web 应用 —— 涵盖前端页面、Serverless 后端（边缘函数/云函数）、AI Agent 开发（DeepAgents、LangGraph、Claude SDK、OpenAI Agents、CrewAI）及快速部署到全球加速网络。 | 需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`AI_GATEWAY_API_KEY`、`ANTHROPIC_API_KEY`、`EDGEONE_PAGES_API_TOKEN`、`WSA_API_KEY` |
| [`finops-expert`](./experts/finops-expert/) | [CloudQ](./experts/finops-expert/README.md) | 单人专家 | 云成本治理专家。 | 无 |
| [`industry-sre-team`](./experts/industry-sre-team/) | [腾讯云行业 SRE](./experts/industry-sre-team/README.md) | 专家团 | 12 位行业 SRE 覆盖游戏、金融、电商等场景，做五维巡检，输出可对照可执行的架构治理建议。 | 需要环境变量：`TENCENTCLOUD_TOKEN` |
| [`inspection-expert`](./experts/inspection-expert/) | [CloudQ](./experts/inspection-expert/README.md) | 单人专家 | 云资源巡检专家。 | 无 |
| [`migraq-team`](./experts/migraq-team/) | [腾讯云上云迁移专家团](./experts/migraq-team/README.md) | 专家团 | 7位专家协作完成上云迁移：产品选型、Landing Zone、架构设计、交付实施、运维与FDE部署。 | 无（可选 API/账号以增强能力） |
| [`multi-cloud-expert`](./experts/multi-cloud-expert/) | [CloudQ](./experts/multi-cloud-expert/README.md) | 单人专家 | 统一管理腾讯云、阿里云、AWS、Azure、GCP 等多云平台，一个智能体即可管多云。 | 无 |
| [`multi-cloud-management-expert`](./experts/multi-cloud-management-expert/) | [CloudQ](./experts/multi-cloud-management-expert/README.md) | 单人专家 | 精通腾讯云、阿里云、AWS等多云架构治理、架构可视化、智能巡检、云成本优化和风险评估，一个专家管理所有云。 | 需要飞书应用凭证或用户登录授权；需要环境变量：`TENCENTCLOUD_TOKEN` |
| [`nges-healthcare-marketing-team`](./experts/nges-healthcare-marketing-team/) | [腾讯健康NGES医药营销专家团](./experts/nges-healthcare-marketing-team/README.md) | 专家团 | 由医药营销智能协调官统一调度的医药营销专家团，整合HCP客户洞察、互动病例生成、学术物料生成、合规审核四大能力，覆盖从客户情报分析到内容生产到合规检测的全流程。 | 无 |
| [`patient-education-content-review-word-assistant`](./experts/patient-education-content-review-word-assistant/) | [腾讯健康药箱-私域患教内容审核助手](./experts/patient-education-content-review-word-assistant/README.md) | 单人专家 | 六维度审核患教内容并核对数据文献一致性，审核意见以 Word 批注+高亮直接标注在原文上输出。 | 无 |
| [`sre-expert`](./experts/sre-expert/) | [CloudQ](./experts/sre-expert/README.md) | 单人专家 | 站点可靠性专家。 | 无 |
| [`tc-sec`](./experts/tc-sec/) | [腾讯云安全专家](./experts/tc-sec/README.md) | 单人专家 | 联动CWP/KMS/BH/CDS/CFW/SSM/TCSS/WAF/CSIP产品接口生成安全运营报告。 | 无 |
| [`tencent-charity-expert`](./experts/tencent-charity-expert/) | [小益](./experts/tencent-charity-expert/) | 单人专家 | 精通公益行业产品和技术解决方案的腾讯技术公益智能化专家。 | 无 |
| [`tencent-rtc-expert`](./experts/tencent-rtc-expert/) | [CloudQ](./experts/tencent-rtc-expert/README.md) | 单人专家 | TRTC 技术支持专家：通话用量与质量查询、单次通话诊断、云端巡检解读、故障排查与友商代码迁移。 | 需要环境变量：`TENCENTCLOUD_TOKEN` |
| [`tencent-security-expert`](./experts/tencent-security-expert/) | [云鼎安全专家](./experts/tencent-security-expert/) | 单人专家 | 深耕安全领域多年，提供威胁建模、漏洞评估、安全代码审查、架构设计、事件响应、安全咨询等服务。 | 无 |
| [`tencentcloud-api`](./experts/tencentcloud-api/) | [腾讯云API专家](./experts/tencentcloud-api/README.md) | 单人专家 | 自然语言管理腾讯云200+产品资源，智能检索API并构造CLI命令，内置安全管控与异常处理。 | 无 |
| [`tianyu-account-guardian`](./experts/tianyu-account-guardian/) | [天御账号保护](./experts/tianyu-account-guardian/README.md) | 单人专家 | 替您盯住注册、登录、裂变全链路账号异常，实时调优策略拦截恶意账号，并生成客诉原因分析报告。 | 无 |
| [`tianyu-marketing-guardian`](./experts/tianyu-marketing-guardian/) | [天御营销保护](./experts/tianyu-marketing-guardian/README.md) | 单人专家 | 替您守护每一场营销活动，在文旅、零售、Token、医疗挂号等场景自动盯活动、查漏召、调策略护预算。 | 无 |
| [`well-arch-expert`](./experts/well-arch-expert/) | [CloudQ](./experts/well-arch-expert/README.md) | 单人专家 | 卓越架构专家。 | 无 |
| [`yunzhi-qa-assistant`](./experts/yunzhi-qa-assistant/) | [腾讯云知（乐享）](./experts/yunzhi-qa-assistant/README.md) | 单人专家 | 基于腾讯云知（乐享）平台的检索增强问答专家。 | 需要环境变量：`LEXIANG_TOKEN` |

### 营销增长（33）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`ad-creative-strategist`](./experts/ad-creative-strategist/) | [点睛睛](./experts/ad-creative-strategist/README.md) | 单人专家 | 精通广告创意设计和效果预判，创作高转化广告素材。 | 无 |
| [`ad-tracking-expert`](./experts/ad-tracking-expert/) | [追踪踪](./experts/ad-tracking-expert/README.md) | 单人专家 | 精通广告追踪代码和转化归因技术，确保投放效果可追踪。 | 无 |
| [`app-store-optimization-expert`](./experts/app-store-optimization-expert/) | [榜上上](./experts/app-store-optimization-expert/README.md) | 单人专家 | 精通App Store和Google Play搜索排名算法，让应用脱颖而出。 | 无 |
| [`auto-consultant`](./experts/auto-consultant/) | [车赢赢](./experts/auto-consultant/README.md) | 单人专家 | 精通用户选车购车决策，深谙汽车营销增长，覆盖品牌营销、用户增长、车型分析、购车咨询等全链路汽车服务。 | 无 |
| [`baidu-seo-expert`](./experts/baidu-seo-expert/) | [度优优](./experts/baidu-seo-expert/README.md) | 单人专家 | 深谙百度搜索算法和中国搜索生态，让品牌获得最大曝光。 | 无 |
| [`brand-guardian`](./experts/brand-guardian/) | [盾卫卫](./experts/brand-guardian/) | 单人专家 | 15年品牌战略经验，守护品牌一致性的终极捍卫者。 | 无 |
| [`carousel-content-growth-expert`](./experts/carousel-content-growth-expert/) | [翻页页](./experts/carousel-content-growth-expert/README.md) | 单人专家 | 专精设计高互动率轮播图内容，驱动社交平台用户参与和增长。 | 无 |
| [`china-ecommerce-operations-expert`](./experts/china-ecommerce-operations-expert/) | [卖得好](./experts/china-ecommerce-operations-expert/README.md) | 单人专家 | 精通天猫京东拼多多等平台运营，从选品到爆款一站式操盘。 | 无 |
| [`content-monetization-team`](./experts/content-monetization-team/) | [内容变现商业化专家团](./experts/content-monetization-team/README.md) | 专家团 | 5人专家团覆盖CPS带货分佣、CPE/CPM效果广告、创作者-品牌交易撮合与收益分析，助力内容创作者和品牌方实现商业化闭环。 | 无 |
| [`cross-border-ecommerce-expert`](./experts/cross-border-ecommerce-expert/) | [海跨洋](./experts/cross-border-ecommerce-expert/README.md) | 单人专家 | 精通亚马逊Shopify等国际电商平台，助力品牌出海全球。 | 无 |
| [`cultural-intelligence-strategist`](./experts/cultural-intelligence-strategist/) | [知文文](./experts/cultural-intelligence-strategist/README.md) | 单人专家 | 帮助品牌建立全球化过程中的文化敏感度。 | 无 |
| [`developer-evangelist`](./experts/developer-evangelist/) | [布道道](./experts/developer-evangelist/README.md) | 单人专家 | 构建发展开发者社区，推动产品在开发者群体中的采用。 | 无 |
| [`executing-marketing-campaigns`](./experts/executing-marketing-campaigns/) | [策动动](./experts/executing-marketing-campaigns/README.md) | 单人专家 | 策划、创建和优化全渠道营销活动，包括内容策略、社交媒体、邮件营销和广告投放。 | 无 |
| [`geo-diagnosis-expert`](./experts/geo-diagnosis-expert/) | [苍何](./experts/geo-diagnosis-expert/) | 单人专家 | 品牌 GEO 可见度诊断专家，覆盖基建评估、AI 平台收录、竞品对标、舆情分析，输出 AIVO 评分报告。 | 无 |
| [`growth-hacker`](./experts/growth-hacker/) | [裂变变](./experts/growth-hacker/README.md) | 单人专家 | 用数据驱动的实验方法论找到未开发的增长渠道，实现指数级增长。 | 无 |
| [`identity-graph-operator`](./experts/identity-graph-operator/) | [识图图](./experts/identity-graph-operator/README.md) | 单人专家 | 构建维护用户身份图谱系统，实现跨平台身份识别。 | 无 |
| [`jiayi-ads-analytics-expert`](./experts/jiayi-ads-analytics-expert/) | [爆量君](./experts/jiayi-ads-analytics-expert/README.md) | 单人专家 | 不止分析，更能直接操盘——通过API调价、暂停词、加否词、改预算、上下创意，五大广告平台一句话搞定。 | 需要环境变量：`BAIDU_ADS_ACCESS_TOKEN`、`BAIDU_ADS_REFRESH_TOKEN`、`GOOGLE_ADS_CLIENT_ID`、`GOOGLE_ADS_DEVELOPER_TOKEN`、`MICROSOFT_ADS_CLIENT_ID` 等 |
| [`linked-in-content-creator`](./experts/linked-in-content-creator/) | [领英达](./experts/linked-in-content-creator/README.md) | 单人专家 | 精通LinkedIn专业社交平台内容策略，帮助建立思想领袖地位。 | 无 |
| [`livestream-ecommerce-coach`](./experts/livestream-ecommerce-coach/) | [播旺旺](./experts/livestream-ecommerce-coach/README.md) | 单人专家 | 精通直播带货全链路运营，从话术到投流帮助实现GMV突破。 | 无 |
| [`market-analysis-cn`](./experts/market-analysis-cn/) | [鹏城信息AI专家](./experts/market-analysis-cn/README.md) | 单人专家 | 聚焦市场趋势、竞品对标与用户行为洞察，输出SWOT分析与战略建议，助力企业做出明智商业决策。 | 无 |
| [`marketing-campaign-team`](./experts/marketing-campaign-team/) | [营销战役团队](./experts/marketing-campaign-team/) | 专家团 | 由营销总监领导的 4 人营销专家团队：内容创作者（博客/邮件/社媒/品牌声音）、活动策划师（战役策略/受众/渠道/预算）、SEO 专家（技术审计/内容优化/效果分析）和品牌分析师（竞品定位/品牌审核）。 | 无 |
| [`paid-media-auditor`](./experts/paid-media-auditor/) | [查账账](./experts/paid-media-auditor/README.md) | 单人专家 | 深度审计广告投放数据和预算分配，找出被浪费的广告费。 | 无 |
| [`ppc-bidding-strategist`](./experts/ppc-bidding-strategist/) | [竞高高](./experts/ppc-bidding-strategist/README.md) | 单人专家 | 精通Google Ads和百度竞价，以最低点击成本获取高质量流量。 | 无 |
| [`private-domain-marketing-expert`](./experts/private-domain-marketing-expert/) | [司玉琦](./experts/private-domain-marketing-expert/README.md) | 单人专家 | 深谙私域运营增长，盘活现有数据资源、洞察营销机会、实现业绩增长。 | 无 |
| [`private-domain-operations-expert`](./experts/private-domain-operations-expert/) | [留客客](./experts/private-domain-operations-expert/README.md) | 单人专家 | 精通微信私域流量池搭建运营，将公域流量沉淀为私域资产。 | 无 |
| [`programmatic-ad-buyer`](./experts/programmatic-ad-buyer/) | [算法投](./experts/programmatic-ad-buyer/README.md) | 单人专家 | 精通程序化广告购买和DSP平台，通过算法实现大规模精准投放。 | 无 |
| [`reddit-community-builder`](./experts/reddit-community-builder/) | [红迪迪](./experts/reddit-community-builder/README.md) | 单人专家 | 深谙Reddit社区文化，在全球最大论坛上建立真实社区影响力。 | 无 |
| [`search-term-analyst`](./experts/search-term-analyst/) | [词探探](./experts/search-term-analyst/README.md) | 单人专家 | 深度分析搜索词数据，挖掘用户真实搜索意图。 | 无 |
| [`seo-content-team`](./experts/seo-content-team/) | [SEO 内容营销团队](./experts/seo-content-team/README.md) | 专家团 | 7位专业角色分5阶段协作：关键词研究、SEO长文创作、技术优化、内容编辑、链接策略、转化率分析，全流程自动化产出高质量SEO内容。 | 无 |
| [`seo-expert`](./experts/seo-expert/) | [搜霸霸](./experts/seo-expert/README.md) | 单人专家 | 精通Google搜索算法和技术SEO，让网站在搜索结果中稳居前列。 | 无（可选 API/账号以增强能力） |
| [`social-ad-strategist`](./experts/social-ad-strategist/) | [精投投](./experts/social-ad-strategist/README.md) | 单人专家 | 精通社交平台广告投放，以精准定向实现最优获客成本。 | 无 |
| [`social-engagement-team`](./experts/social-engagement-team/) | [社媒互动增长专家团](./experts/social-engagement-team/README.md) | 专家团 | 通过智能化互动自动化、AI评论运营、高转化信号挖掘和品牌舆情监控，安全高效提升社交媒体互动效果，覆盖14+全球主流平台。 | 无 |
| [`social-media-strategist`](./experts/social-media-strategist/) | [传声声](./experts/social-media-strategist/README.md) | 单人专家 | 全面统筹多平台社交媒体策略，让品牌在每个平台发出最强音。 | 无 |

### 行业顾问（19）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`ask-liuxiaopai`](./experts/ask-liuxiaopai/) | [AI 刘小排](./experts/ask-liuxiaopai/) | 单人专家 | Raphael AI 创始人刘小排的数字分身，office-hours 风格陪你拆 idea：钉死具体的人、真痛点、第一笔钱、第一批用户在哪，再给一件今晚就能做的事。 | 无 |
| [`chaogeek-kongming`](./experts/chaogeek-kongming/) | [ChaoGeek 0x孔明](./experts/chaogeek-kongming/README.md) | 单人专家 | 一人公司认知反缴械思维搭子：少问但问到根，补上下文、对齐意图，帮你驾驭智能体不外包判断力。 | 无 |
| [`chuangye-manor`](./experts/chuangye-manor/) | [林正刚](./experts/chuangye-manor/README.md) | 单人专家 | 林老师分身+读书伙伴。 | 无 |
| [`family-education-ma`](./experts/family-education-ma/) | [马滢老师](./experts/family-education-ma/) | 单人专家 | 腾讯未保营地8年一线实践，融合三大循证体系，为家长提供亲子沟通、沉迷干预、家庭成长咨询。 | 无 |
| [`fbsir-eight-seat-board`](./experts/fbsir-eight-seat-board/) | [福帮手](./experts/fbsir-eight-seat-board/README.md) | 专家团 | 福帮手经营决策独立审议专家团｜按案组建必要席位，独立判断、交叉质询、保留异议，交付可追溯行动备忘录。 | 无 |
| [`fbsir-industry-scene-researcher`](./experts/fbsir-industry-scene-researcher/) | [行业场景研究员](./experts/fbsir-industry-scene-researcher/README.md) | 单人专家 | 围绕一个行业场景定位关键工作流缺口，并交付补位卡、3天行动计划、项目动作执行包和下一步建议。 | 无 |
| [`fbsir-super-partner`](./experts/fbsir-super-partner/) | [超级合伙人\|魔镜行动](./experts/fbsir-super-partner/README.md) | 单人专家 | 带上目标或真实材料，立即得到可使用成品；宿主能力可用且获授权时执行并回执，再做72小时裁决。 | 无 |
| [`fbsir-super-partner-group`](./experts/fbsir-super-partner-group/) | [超级合伙人](./experts/fbsir-super-partner-group/README.md) | 专家团 | 以AI+OPC智能化运营为底座，统筹战略、运营、增长与AI试点，输出诊断卡和下一步。 | 无 |
| [`fortune-consultant`](./experts/fortune-consultant/) | [运势分析师](./experts/fortune-consultant/README.md) | 单人专家 | 传统命理参考工具——八字紫微排盘、塔罗梅花起卦、农历黄历查询，多体系交叉参考，仅供娱乐。 | 无（可选 API/账号以增强能力） |
| [`gaokao-advisor`](./experts/gaokao-advisor/) | [专业高考顾问](./experts/gaokao-advisor/README.md) | 单人专家 | 辅助检索高考知识库并调用分数线、一分一段能力，整理带来源的真题、高校专业和志愿参考；同时提供全流程志愿填报引导，产出可转发的腾讯文档志愿报告。 | 无（可选 API/账号以增强能力） |
| [`indie-founder-coach`](./experts/indie-founder-coach/) | [创迪](./experts/indie-founder-coach/README.md) | 单人专家 | 信奉精益创业与自力更生理念，帮助独立创业者用最少资源从0到1构建可持续盈利事业，覆盖创业全旅程关键决策。 | 无 |
| [`ket-prep-team`](./experts/ket-prep-team/) | [KET备考专家团](./experts/ket-prep-team/README.md) | 专家团 | 剑桥认证考官领衔，为小学生提供KET全流程备考：学情测评、词汇语法地基、听说读写专项提分、考前冲刺模考，助力Merit（优秀）/Distinction（卓越）达标。 | 无 |
| [`liuxue-yanxue-expert`](./experts/liuxue-yanxue-expert/) | [福帮手](./experts/liuxue-yanxue-expert/README.md) | 单人专家 | 面向家庭生成留学研学首轮规划，兼顾高考窗口、预算风险、路径备选与后续承接行动建议。 | 无 |
| [`metamorphosis-practitioner`](./experts/metamorphosis-practitioner/) | [蜕变践行者](./experts/metamorphosis-practitioner/README.md) | 单人专家 | 不是导师，是走过你想走的路的人。 | 无 |
| [`opc-team`](./experts/opc-team/) | [一人公司专家团](./experts/opc-team/README.md) | 专家团 | 基于由Easy创作的《一人企业方法论》，9位专家陪你走完从资源盘点、利基定位到MVP、转化、复盘的一人公司全流程共创。 | 无 |
| [`paper-topic-selection`](./experts/paper-topic-selection/) | [选题专家团队（WANFANG TOPIC）](./experts/paper-topic-selection/README.md) | 专家团 | 帮你做论文选题：检索文献、推荐方向、评估新颖性、生成标题、出领域报告。 | 无 |
| [`smb-team`](./experts/smb-team/) | [小企业经营团队](./experts/smb-team/) | 专家团 | 经营总管调度四位领域专家，覆盖财务、营收、客户合规和运营，小企业管理一站搞定。 | 无 |
| [`terminal-veteran`](./experts/terminal-veteran/) | [终端老兵专家（陈丰伟）](./experts/terminal-veteran/README.md) | 单人专家 | 近三十年终端老兵，11条铁律+三层方法论，厂商策略/渠道选品/投资分析+行业报告。 | 无 |
| [`tripstar-agent`](./experts/tripstar-agent/) | [路小鲜](./experts/tripstar-agent/README.md) | 单人专家 | 生活服务管家，一站式搞定行程规划、景点/酒店/天气/预算与美团红包领取。 | 需要环境变量：`AVIATIONSTACK_API_KEY`、`USER_TOKEN` |

### 运营人力（10）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`corporate-training-designer`](./experts/corporate-training-designer/) | [育才才](./experts/corporate-training-designer/README.md) | 单人专家 | 设计系统化企业培训课程和学习路径，让员工技能快速提升。 | 无 |
| [`customer-support-expert`](./experts/customer-support-expert/) | [暖心心](./experts/customer-support-expert/README.md) | 单人专家 | 将每次沮丧的用户互动转化为忠实拥护者，用卓越服务创口碑。 | 无 |
| [`hr-operations-team`](./experts/hr-operations-team/) | [HR 运营团队](./experts/hr-operations-team/) | 专家团 | 人力资源管理流程化，招聘筛选、薪酬体系设计、组织发展与HR运营流程化管理，助力企业人才战略落地。 | 无 |
| [`ihr-conference`](./experts/ihr-conference/) | [利唐智语AI面谈官](./experts/ihr-conference/) | 单人专家 | 提供九大智能面谈大纲与线上实时指引，基于云录制自动生成结构化纪要与待办，全周期辅助管理者高效沟通。 | 无 |
| [`interview-simulator`](./experts/interview-simulator/) | [鹏城信息AI专家](./experts/interview-simulator/README.md) | 单人专家 | 模拟任意职位的真实面试官，覆盖技术产品销售人事等全岗位，提供逐题评分详细反馈与录用建议，助你高效备战面试。 | 无 |
| [`recruitment-expert`](./experts/recruitment-expert/) | [伯乐乐](./experts/recruitment-expert/README.md) | 单人专家 | 精通人才招聘全流程，为团队找到最佳人才。 | 无 |
| [`resume-assistant`](./experts/resume-assistant/) | [鹏城信息AI专家](./experts/resume-assistant/README.md) | 单人专家 | 提供百分制专业评分、四十项深度清单润色、岗位匹配定制与多格式导出，全面打造高竞争力求职简历。 | 无 |
| [`smb-operations`](./experts/smb-operations/) | [毕运营](./experts/smb-operations/) | 单人专家 | 小企业组织运营师，负责招聘入职、工具初始化和业务快照，让运营不掉链子。 | 无 |
| [`study-abroad-consultant`](./experts/study-abroad-consultant/) | [留洋洋](./experts/study-abroad-consultant/README.md) | 单人专家 | 精通各国留学申请流程和院校信息。 | 无 |
| [`supply-chain-strategist`](./experts/supply-chain-strategist/) | [链优优](./experts/supply-chain-strategist/README.md) | 单人专家 | 优化供应链每个环节，实现成本效率韧性的最佳平衡。 | 无 |

### 金融投资（32）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`a-share-analysis`](./experts/a-share-analysis/) | [A股研究团队](./experts/a-share-analysis/README.md) | 专家团 | 8位研究专家支持6个预设工作流编排，覆盖宏观策略、盘面解读、个股深度、估值定价、产业链映射、资金追踪、风险诊断。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`accounts-payable-agent`](./experts/accounts-payable-agent/) | [付清清](./experts/accounts-payable-agent/README.md) | 单人专家 | 自动化处理应付账款流程，确保付款准确及时。 | 无 |
| [`citongshuopro`](./experts/citongshuopro/) | [刺桐说Pro-投资社群嘉宾团](./experts/citongshuopro/README.md) | 专家团 | 模拟真实投资社群运作模式的多智能体投研系统，已接入社群嘉宾数字分身，可7*24为您提供投资咨询服务。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`earnings-reviewer`](./experts/earnings-reviewer/) | [季明辨](./experts/earnings-reviewer/) | 单人专家 | 资深季报复核分析师,读财报电话会和公告更新覆盖模型,产出季报后记、方差表与估值调整,供研究部门沿用。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`equity-research`](./experts/equity-research/) | [严估深](./experts/equity-research/) | 单人专家 | 全面的股票研究工具集：财报分析、首次覆盖报告、DCF与可比估值、多空推介、投资备忘录、事件情景分析、组合风险管理，覆盖完整买方卖方研究工作流。 | 无 |
| [`fin-research-expert`](./experts/fin-research-expert/) | [同舟股市投研专家](./experts/fin-research-expert/README.md) | 单人专家 | 连接同舟公开投研能力，稳定生成个股、行业、事件与研报的证据化简报和可复核投研案例页面。 | 需要环境变量：`GITEA_TOKEN`、`NPM_TOKEN`、`OSS_ACCESS_KEY_SECRET` |
| [`finance`](./experts/finance/) | [记账账](./experts/finance/README.md) | 单人专家 | 财务会计工具集：月末结账、日记账分录、账户核对、财务报表生成、差异分析和 SOX 审计支持。 | 无 |
| [`financial-analysis`](./experts/financial-analysis/) | [建模模](./experts/financial-analysis/) | 单人专家 | 核心金融建模工具：DCF 估值、可比公司分析、LBO 模型、三张表模型、竞争格局分析和 PPT 质检。 | 无 |
| [`financial-tracker`](./experts/financial-tracker/) | [账清清](./experts/financial-tracker/README.md) | 单人专家 | 精准追踪项目和业务的财务数据，确保每笔收支清晰透明。 | 无（可选 API/账号以增强能力） |
| [`gl-reconciler`](./experts/gl-reconciler/) | [钱对齐](./experts/gl-reconciler/) | 单人专家 | 基金后台日终与月末对账专员,在总账与子账之间找出差异、追溯到源交易、归类 timing/reclass/FX 等原因并出具可签核清单。 | 无 |
| [`investment-banking`](./experts/investment-banking/) | [银拓远](./experts/investment-banking/README.md) | 单人专家 | 全能投资银行专家：交易材料制作、估值建模（Comps/DCF/LBO/三表）、资本市场融资、买方尽调分析、重组与回收瀑布、交易全流程执行。 | 无 |
| [`investment-masters-team`](./experts/investment-masters-team/) | [投资大师专家团](./experts/investment-masters-team/) | 专家团 | 13位传奇投资哲学家 + 6位专业分析师并行分析，风险管理师评估约束，投资组合经理信号聚合投票，多角度投资分析参考。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`kyc-screener`](./experts/kyc-screener/) | [查本源](./experts/kyc-screener/) | 单人专家 | 客户准入合规分析师,解析 KYC 材料、跑规则引擎、比对制裁与 PEP 名单,并按风险等级形成可交合规签核的升级包。 | 无 |
| [`mai-deal-advisor`](./experts/mai-deal-advisor/) | [MAI Lab并购专家包](./experts/mai-deal-advisor/README.md) | 单人专家 | MAI Lab出品的免费并购专家包：提供报告模板、数据校验闸门、港股公告监控与复杂问题分诊留资，协助投行专业人士推进并购流程。 | 无 |
| [`market-researcher`](./experts/market-researcher/) | [严研行](./experts/market-researcher/) | 单人专家 | 面向分析师与基金经理的行业研究分析师,产出行业全景、竞争格局、可比公司估值表与主题选股清单等研究交付物。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`meeting-prep-agent`](./experts/meeting-prep-agent/) | [周备全](./experts/meeting-prep-agent/) | 单人专家 | 理财顾问的会议准备搭档,在每次客户见面前汇总关系历史、持仓近况、市场要闻与议题清单,让顾问 5 分钟进入状态。 | 无 |
| [`model-builder`](./experts/model-builder/) | [莫百炼](./experts/model-builder/) | 单人专家 | 专业财务建模师,在 Excel 中从零搭建 DCF、LBO、三张表模型与可比公司估值,公式全链接、可追溯、机构级品控。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`month-end-closer`](./experts/month-end-closer/) | [关月结](./experts/month-end-closer/) | 单人专家 | 财务负责人的月末关账搭档,按清单跑应计、滚动表、差异说明,把关账包整理好交给 controller 签核。 | 无 |
| [`pitch-agent`](./experts/pitch-agent/) | [白必得](./experts/pitch-agent/) | 单人专家 | 资深投行关联人,从零搭建 pitch 初稿——可比公司、先例交易、DCF、足球场估值图,并生成绑在模型上的品牌化 PPT。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`private-equity`](./experts/private-equity/) | [募资资](./experts/private-equity/) | 单人专家 | 私募股权工具集：Deal Sourcing、项目筛选、尽调清单、IC Memo、单位经济学分析、回报分析、投后管理和价值创造方案。 | 无 |
| [`smart-stock-analyst`](./experts/smart-stock-analyst/) | [星辰](./experts/smart-stock-analyst/README.md) | 单人专家 | AI驱动多市场股票分析专家，内置缠论、波浪等15+策略，默认输出精美交互式HTML决策仪表盘报告。 | 无 |
| [`smb-finance`](./experts/smb-finance/) | [钱守通](./experts/smb-finance/) | 单人专家 | 小企业财务管家，一站式搞定现金流预测、逾期追款、毛利分析、月结对账和税务准备。 | 无 |
| [`statement-auditor`](./experts/statement-auditor/) | [审细明](./experts/statement-auditor/) | 单人专家 | LP 资本账户报表最后把关人,按基金 NAV 反算每条项目、对齐分配与管理费,发差前形成签核建议与异常清单。 | 无 |
| [`stock-partner-team`](./experts/stock-partner-team/) | [腾讯自选股股票投研专家团](./experts/stock-partner-team/README.md) | 专家团 | 六位投研专家团，兼擅产业策略、信号捕捉、估值定价、逆向布局、基本面与短线，基于实时行情多视角研判。 | 无 |
| [`strategy-backtest-expert`](./experts/strategy-backtest-expert/) | [回测明算](./experts/strategy-backtest-expert/README.md) | 单人专家 | 把自然语言描述的交易策略转成可运行的 Python 回测脚本，输出标准指标、可视化图表、HTML 仪表盘，并给出实现细节、已知偏差和结果解读。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`tdx-stock-diagnostician`](./experts/tdx-stock-diagnostician/) | [通达信诊断师](./experts/tdx-stock-diagnostician/README.md) | 单人专家 | 像经验丰富的分析师，对任意A股进行六大模块360度全方位诊断，涵盖基本面、技术面、资金面、事件催化、同业对标，输出专业诊断报告。 | 无 |
| [`tdx-stock-hunter`](./experts/tdx-stock-hunter/) | [通达信选股猎手](./experts/tdx-stock-hunter/README.md) | 单人专家 | 基于通达信MCP数据，将自然语言转为多维筛选条件，从5000+A股中按基本面/技术面/资金面/估值做横向分析与综合评分，供用户参考。 | 无 |
| [`tdx-value-assessor`](./experts/tdx-value-assessor/) | [通达信评估师](./experts/tdx-value-assessor/README.md) | 单人专家 | 秉承格雷厄姆-巴菲特价值体系，运用15+估值模型，通过护城河评估与多维估值分析，评估企业内在价值与安全边际水平。 | 无 |
| [`trading-agent`](./experts/trading-agent/) | [交易分析团队](./experts/trading-agent/) | 专家团 | 13位专业角色分5阶段协作完成投资分析：技术面、基本面、新闻面、情绪面数据采集 → 多空辩论 → 交易决策 → 三方风险评估 → 最终报告，输出 BUY/SELL/HOLD 建议及完整操作方案。 | 无 |
| [`valuation-reviewer`](./experts/valuation-reviewer/) | [顾估衡](./experts/valuation-reviewer/) | 单人专家 | PE/VC 基金组合估值主管,收 GP 估值包、跑标准估值模板、算基金 NAV 与 LP 分配、出 LP 报告草稿交投资者关系签核。 | 需要环境变量：`CLI_TOKEN`、`SAVE_TOKEN` |
| [`wealth-management`](./experts/wealth-management/) | [理财财](./experts/wealth-management/) | 单人专家 | 财富管理工具集：客户回顾、财务规划、投资组合再平衡、税损收割、投资提案和客户报告生成。 | 无 |
| [`yahoo-finance-cli`](./experts/yahoo-finance-cli/) | [鹏城信息AI专家](./experts/yahoo-finance-cli/README.md) | 单人专家 | 查询全球股票实时行情、基本面、财报预期、评级、历史走势与估值洞察，发现热门趋势标的，支持模糊检索与并排对比。 | 无 |

### 销售商务（14）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`cordys-crm`](./experts/cordys-crm/) | [Cordys CRM 助手](./experts/cordys-crm/README.md) | 单人专家 | 角色感知型CRM助手，覆盖线索到现金全链路。 | 需要环境变量：`CORDYS_ACCESS_KEY` |
| [`deal-strategist`](./experts/deal-strategist/) | [赢单单](./experts/deal-strategist/README.md) | 单人专家 | 精通复杂交易策略制定和推进，帮助销售团队赢得大单。 | 无 |
| [`discovery-coach`](./experts/discovery-coach/) | [掘需需](./experts/discovery-coach/README.md) | 单人专家 | 训练销售掌握深度需求挖掘技巧，发现真正的业务痛点。 | 无 |
| [`enterprise-account-strategist`](./experts/enterprise-account-strategist/) | [拓客客](./experts/enterprise-account-strategist/README.md) | 单人专家 | 精通大客户经营和账户扩展策略，将客户发展为长期战略伙伴。 | 无 |
| [`government-digital-presales-consultant`](./experts/government-digital-presales-consultant/) | [政通通](./experts/government-digital-presales-consultant/README.md) | 单人专家 | 精通政府数字化转型需求和采购流程。 | 无 |
| [`meituan-living-assistant`](./experts/meituan-living-assistant/) | [40-20 外卖券](./experts/meituan-living-assistant/) | 单人专家 | 帮您一键领取美团优惠券，搜索附近团购美食并下单，探索今日活动，覆盖餐饮饮品等生活服务，省钱省心。 | 无（可选 API/账号以增强能力） |
| [`outbound-strategist`](./experts/outbound-strategist/) | [拨必通](./experts/outbound-strategist/README.md) | 单人专家 | 精通外呼和冷启动销售策略，让陌生人30秒内愿意继续倾听。 | 无 |
| [`presales-technical-consultant`](./experts/presales-technical-consultant/) | [方案通](./experts/presales-technical-consultant/README.md) | 单人专家 | 架起技术与商业的桥梁，帮助客户理解解决方案的价值。 | 无 |
| [`proposal-strategist`](./experts/proposal-strategist/) | [策必中](./experts/proposal-strategist/README.md) | 单人专家 | 精通销售提案和方案设计，将价值转化为无法拒绝的商业论证。 | 无 |
| [`sales-battle-team`](./experts/sales-battle-team/) | [销售作战团队](./experts/sales-battle-team/) | 专家团 | 销售攻坚体系，客户研究锁定目标、外联策略提升触达、竞品情报预警风险、销售预测优化资源分配。 | 无 |
| [`sales-coach`](./experts/sales-coach/) | [单必成](./experts/sales-coach/README.md) | 单人专家 | 全栈销售教练：从能力培养到实战执行——会议准备、交易策略、商业案例、竞品分析、通话复盘，用苏格拉底式提问驱动。 | 无 |
| [`sales-pipeline-analyst`](./experts/sales-pipeline-analyst/) | [漏斗通](./experts/sales-pipeline-analyst/README.md) | 单人专家 | 用数据驱动方法分析销售管道健康度，让预测从猜测变科学。 | 无 |
| [`smb-revenue`](./experts/smb-revenue/) | [甄客来](./experts/smb-revenue/) | 单人专家 | 小企业营收增长师，从线索打分到内容策略再到营销活动，一条龙驱动营收增长。 | 无 |
| [`uupt-delivery`](./experts/uupt-delivery/) | [UU跑腿](./experts/uupt-delivery/README.md) | 单人专家 | 提供UU跑腿同城即时配送与现场帮忙服务，支持订单询价、发单下单、订单查询取消及跑男实时追踪。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`UUPT_APP_SECRET` |

### 项目质量（23）

| 插件目录 | 显示名 | 类型 | 用来做什么 | 前置条件 |
|----------|--------|------|------------|----------|
| [`accessibility-auditor`](./experts/accessibility-auditor/) | [无碍碍](./experts/accessibility-auditor/README.md) | 单人专家 | 按WCAG标准审计界面可访问性，确保每个用户都能使用产品。 | 无 |
| [`agent-orchestrator`](./experts/agent-orchestrator/) | [调度达](./experts/agent-orchestrator/README.md) | 单人专家 | 精通多智能体系统的编排和协调，让AI团队高效协作。 | 无 |
| [`ai-meeting-notes`](./experts/ai-meeting-notes/) | [鹏城信息AI专家](./experts/ai-meeting-notes/README.md) | 单人专家 | 粘贴会议笔记或转写文本，自动提炼摘要、负责人、截止日期与行动项，归档可检索并联动待办清单跟踪执行。 | 无 |
| [`api-testing-expert`](./experts/api-testing-expert/) | [接口探](./experts/api-testing-expert/README.md) | 单人专家 | 在用户之前发现API的每一个缺陷，确保接口稳定性和正确性。 | 无 |
| [`document-generation-expert`](./experts/document-generation-expert/) | [文档达](./experts/document-generation-expert/README.md) | 单人专家 | 自动化生成各类业务文档，大幅提升文档创建效率。 | 无 |
| [`document-skills`](./experts/document-skills/) | [理文文](./experts/document-skills/) | 单人专家 | 文档处理套件：Excel 电子表格、Word 文档、PowerPoint 演示文稿和 PDF 文件的创建、编辑与转换。 | 无 |
| [`evidence-collector`](./experts/evidence-collector/) | [截图图](./experts/evidence-collector/README.md) | 单人专家 | 不放过任何没有截图证据的问题，用视觉证据确保缺陷无处遁形。 | 无 |
| [`executive-summary-generator`](./experts/executive-summary-generator/) | [简明明](./experts/executive-summary-generator/README.md) | 单人专家 | 将冗长报告浓缩为高管可快速消化的精华摘要，节省每分钟。 | 无 |
| [`experiment-tracking-manager`](./experts/experiment-tracking-manager/) | [实验通](./experts/experiment-tracking-manager/README.md) | 单人专家 | 系统化管理实验全生命周期，确保每个实验有假设有执行有结论。 | 无 |
| [`internal-comms`](./experts/internal-comms/) | [传令令](./experts/internal-comms/) | 单人专家 | 内部沟通模板专家：状态报告、领导汇报、公司简报、FAQ、事故报告和项目更新。 | 无 |
| [`jira-workflow-admin`](./experts/jira-workflow-admin/) | [看板达](./experts/jira-workflow-admin/README.md) | 单人专家 | 精通Jira配置和敏捷工作流设计，让工具真正服务于团队效率。 | 需要环境变量：`TENCENTCLOUD_TOKEN` |
| [`openspec-doc-team`](./experts/openspec-doc-team/) | [专业文档生成团队](./experts/openspec-doc-team/) | 专家团 | 企业级长文档生成，4角色协作完成深度调研、大纲规划、内容撰写与合规审核全流程。 | 无 |
| [`performance-testing-expert`](./experts/performance-testing-expert/) | [压测测](./experts/performance-testing-expert/README.md) | 单人专家 | 精通性能测试和基准评估，用数据证明性能改进而非凭感觉。 | 无 |
| [`project-shepherd`](./experts/project-shepherd/) | [牧羊羊](./experts/project-shepherd/README.md) | 单人专家 | 温和但坚定地引导项目按计划推进，确保里程碑准时交付。 | 无 |
| [`reality-checker`](./experts/reality-checker/) | [验真真](./experts/reality-checker/README.md) | 单人专家 | 默认认为一切需要更多证据，需要压倒性证据才批准生产就绪。 | 无 |
| [`senior-project-manager`](./experts/senior-project-manager/) | [关德豪](./experts/senior-project-manager/README.md) | 单人专家 | 10年以上项目管理经验，精通瀑布和敏捷，是复杂项目定海神针。 | 无 |
| [`studio-operations-manager`](./experts/studio-operations-manager/) | [统筹筹](./experts/studio-operations-manager/README.md) | 单人专家 | 全面管理工作室日常运营，从资源调配到流程优化。 | 无 |
| [`studio-producer`](./experts/studio-producer/) | [制片达](./experts/studio-producer/README.md) | 单人专家 | 统筹项目从立项到交付的全过程，平衡创意预算和时间。 | 无 |
| [`technical-documentation-engineer`](./experts/technical-documentation-engineer/) | [文通通](./experts/technical-documentation-engineer/README.md) | 单人专家 | 将复杂技术概念转化为清晰准确的文档，让技术知识可传播。 | 无 |
| [`test-results-analyst`](./experts/test-results-analyst/) | [析测测](./experts/test-results-analyst/README.md) | 单人专家 | 像侦探解读证据一样分析测试结果，发现隐藏的质量问题。 | 无 |
| [`tool-evaluation-expert`](./experts/tool-evaluation-expert/) | [选品品](./experts/tool-evaluation-expert/README.md) | 单人专家 | 系统化评估推荐最适合团队的工具，避免浪费时间在错误工具上。 | 无 |
| [`webapp-testing`](./experts/webapp-testing/) | [端测测](./experts/webapp-testing/README.md) | 单人专家 | Web 应用测试助手，引导用户完成 Web 应用的启动、配置和测试流程。 | 无（可选 API/账号以增强能力） |
| [`workflow-optimization-expert`](./experts/workflow-optimization-expert/) | [流畅畅](./experts/workflow-optimization-expert/README.md) | 单人专家 | 找到瓶颈修复流程自动化一切，让团队效率最大化。 | 无 |

## 4. 插件市场 `plugins/`

### 4.1 codebuddy-plugins-official（57）

| 目录 | 名称 | 用来做什么 | 前置条件 | skill 数 |
|------|------|------------|----------|---------|
| [`agent-browser`](./plugins/codebuddy-plugins-official/plugins/agent-browser/) | [agent-browser](./plugins/codebuddy-plugins-official/plugins/agent-browser/) | 基于 Vercel agent-browser CLI 的浏览器自动化插件。 | 无（可选 API/账号以增强能力） | 1 |
| [`agent-sdk-dev`](./plugins/codebuddy-plugins-official/plugins/agent-sdk-dev/) | [agent-sdk-dev](./plugins/codebuddy-plugins-official/plugins/agent-sdk-dev/) | 插件「agent-sdk-dev」（含 0 个 skill）。 | 需要环境变量：`CODEBUDDY_API_KEY`、`CODEBUDDY_AUTH_TOKEN`、`MY_API_KEY` | 0 |
| [`agent-team-agile-workflow`](./plugins/codebuddy-plugins-official/plugins/agent-team-agile-workflow/) | [agent-team-agile-workflow](./plugins/codebuddy-plugins-official/plugins/agent-team-agile-workflow/) | 完整的 BMAD 敏捷工作流插件，包含角色化代理（PO、架构师、SM、开发、QA）和交互式审批流程。 | 无 | 0 |
| [`algorithmic-art`](./plugins/codebuddy-plugins-official/plugins/algorithmic-art/) | [algorithmic-art](./plugins/codebuddy-plugins-official/plugins/algorithmic-art/) | 使用 p5.js 创建算法艺术，支持种子随机性和交互式参数探索。 | 无 | 1 |
| [`atuin`](./plugins/codebuddy-plugins-official/plugins/atuin/) | [atuin](./plugins/codebuddy-plugins-official/plugins/atuin/) | 自动拦截 AI 的高危操作，自动阻止 AI 使用有漏洞的组件。 | 无 | 0 |
| [`chainguard`](./plugins/codebuddy-plugins-official/plugins/chainguard/) | [chainguard](./plugins/codebuddy-plugins-official/plugins/chainguard/) | AI 编程供应链安全防护，自动拦截依赖安装操作进行安全审计，检测漏洞组件、License 合规及 SBOM 白名单。 | 无 | 0 |
| [`clangd-lsp`](./plugins/codebuddy-plugins-official/plugins/clangd-lsp/) | [clangd-lsp](./plugins/codebuddy-plugins-official/plugins/clangd-lsp/) | C/C++ 语言服务器(clangd)，提供代码智能提示。 | 无 | 0 |
| [`cloudbase`](./plugins/codebuddy-plugins-official/plugins/cloudbase/) | [cloudbase](./plugins/codebuddy-plugins-official/plugins/cloudbase/) | CloudBase AI 开发插件，提供 Web、小程序、云函数、CloudRun、数据库（NoSQL/MySQL）、云存储、AI 模型、UI 设计等全栈开发能力。 | 无 | 23 |
| [`code-simplifier`](./plugins/codebuddy-plugins-official/plugins/code-simplifier/) | [code-simplifier](./plugins/codebuddy-plugins-official/plugins/code-simplifier/) | 专注于简化代码以提升清晰度、一致性和可维护性的智能代理,在保留完整功能的前提下优化代码结构。 | 无 | 0 |
| [`codebuddy-md-management`](./plugins/codebuddy-plugins-official/plugins/codebuddy-md-management/) | [codebuddy-md-management](./plugins/codebuddy-plugins-official/plugins/codebuddy-md-management/) | 用于维护和改进 CODEBUDDY.md 文件的工具 - 审核质量、捕获会话学习内容，并保持项目记忆最新。 | 无 | 1 |
| [`commit-commands`](./plugins/codebuddy-plugins-official/plugins/commit-commands/) | [commit-commands](./plugins/codebuddy-plugins-official/plugins/commit-commands/) | Git 提交工作流命令，包括提交、推送和创建拉取请求。 | 需要 GitHub Token 或 `gh auth login` | 0 |
| [`context7`](./plugins/codebuddy-plugins-official/plugins/context7/) | [context7](./plugins/codebuddy-plugins-official/plugins/context7/) | Upstash Context7 MCP 服务器，用于查找最新文档。 | 无 | 0 |
| [`csharp-lsp`](./plugins/codebuddy-plugins-official/plugins/csharp-lsp/) | [csharp-lsp](./plugins/codebuddy-plugins-official/plugins/csharp-lsp/) | C# 语言服务器，提供代码智能提示和诊断。 | 无 | 0 |
| [`development-essentials`](./plugins/codebuddy-plugins-official/plugins/development-essentials/) | [development-essentials](./plugins/codebuddy-plugins-official/plugins/development-essentials/) | 核心开发命令集，包含编码、调试、测试、优化和文档生成等常用开发工作流。 | 无 | 0 |
| [`doc-coauthoring`](./plugins/codebuddy-plugins-official/plugins/doc-coauthoring/) | [doc-coauthoring](./plugins/codebuddy-plugins-official/plugins/doc-coauthoring/) | 引导用户通过结构化工作流协作撰写文档。 | 无 | 1 |
| [`docx`](./plugins/codebuddy-plugins-official/plugins/docx/) | [docx](./plugins/codebuddy-plugins-official/plugins/docx/) | 全面的 Word 文档创建、编辑和分析工具，支持修订跟踪、评论、格式保留和文本提取。 | 无 | 1 |
| [`feature-dev`](./plugins/codebuddy-plugins-official/plugins/feature-dev/) | [feature-dev](./plugins/codebuddy-plugins-official/plugins/feature-dev/) | 全面的功能开发工作流，配备专门的智能体用于代码库探索、架构设计和质量审查。 | 无 | 0 |
| [`find-skills`](./plugins/codebuddy-plugins-official/plugins/find-skills/) | [find-skills](./plugins/codebuddy-plugins-official/plugins/find-skills/) | 帮助用户发现和安装 AI Agent 技能，支持从 Vercel Skills 和 ClawHub 两个技能仓库搜索和安装。 | 无 | 1 |
| [`firebase`](./plugins/codebuddy-plugins-official/plugins/firebase/) | [firebase](./plugins/codebuddy-plugins-official/plugins/firebase/) | Google Firebase MCP 集成。 | 无 | 0 |
| [`frontend-design`](./plugins/codebuddy-plugins-official/plugins/frontend-design/) | [frontend-design](./plugins/codebuddy-plugins-official/plugins/frontend-design/) | 创建独特的生产级前端界面,具有高设计质量。 | 无 | 1 |
| [`github`](./plugins/codebuddy-plugins-official/plugins/github/) | [github](./plugins/codebuddy-plugins-official/plugins/github/) | 官方 GitHub MCP 服务器，用于仓库管理。 | 无 | 0 |
| [`gitlab`](./plugins/codebuddy-plugins-official/plugins/gitlab/) | [gitlab](./plugins/codebuddy-plugins-official/plugins/gitlab/) | GitLab DevOps 平台集成。 | 无 | 0 |
| [`godot-mcp`](./plugins/codebuddy-plugins-official/plugins/godot-mcp/) | [godot-mcp](./plugins/codebuddy-plugins-official/plugins/godot-mcp/) | Godot 4 MCP 集成插件，通过 AI 对话直接操作 Godot Editor。 | 无（可选 API/账号以增强能力） | 25 |
| [`gopls-lsp`](./plugins/codebuddy-plugins-official/plugins/gopls-lsp/) | [gopls-lsp](./plugins/codebuddy-plugins-official/plugins/gopls-lsp/) | Go 语言服务器，提供代码智能提示和重构功能。 | 无 | 0 |
| [`hookify`](./plugins/codebuddy-plugins-official/plugins/hookify/) | [hookify](./plugins/codebuddy-plugins-official/plugins/hookify/) | 通过分析对话模式或显式指令轻松创建自定义钩子，防止不希望的行为。 | 无（可选 API/账号以增强能力） | 1 |
| [`hot-skills`](./plugins/codebuddy-plugins-official/plugins/hot-skills/) | [hot-skills](./plugins/codebuddy-plugins-official/plugins/hot-skills/) | 精选热门 AI Agent 技能合集，汇集社区高下载量技能于一处。 | 无（可选 API/账号以增强能力） | 34 |
| [`jdtls-lsp`](./plugins/codebuddy-plugins-official/plugins/jdtls-lsp/) | [jdtls-lsp](./plugins/codebuddy-plugins-official/plugins/jdtls-lsp/) | Java 语言服务器（Eclipse JDT.LS），提供代码智能和重构功能。 | 无 | 0 |
| [`lexiang-knowledge-plugins`](./plugins/codebuddy-plugins-official/plugins/lexiang-knowledge-plugins/) | [lexiang-knowledge](./plugins/codebuddy-plugins-official/plugins/lexiang-knowledge-plugins/) | 乐享知识库, 企业协同知识库，提供获取文档内容与元数据、搜索文档内容、查询知识库与目录结构、创建/编辑/移动文档、管理标签与评论、上传文件及维护附件等知识库操作能力。 | 需要环境变量：`ACCESS_TOKEN` | 1 |
| [`lua-lsp`](./plugins/codebuddy-plugins-official/plugins/lua-lsp/) | [lua-lsp](./plugins/codebuddy-plugins-official/plugins/lua-lsp/) | 为 Lua 语言提供代码智能和诊断的语言服务器。 | 无 | 0 |
| [`lucide-icons`](./plugins/codebuddy-plugins-official/plugins/lucide-icons/) | [lucide-icons](./plugins/codebuddy-plugins-official/plugins/lucide-icons/) | 搜索、下载和自定义 Lucide 图标（1000+ 精美 SVG 图标），支持生成 React 组件。 | 无 | 1 |
| [`magicai-hub`](./plugins/codebuddy-plugins-official/plugins/magicai-hub/) | [magicai-hub](./plugins/codebuddy-plugins-official/plugins/magicai-hub/) | Godot 4.x 游戏开发 AI 技能工具包。 | 无 | 8 |
| [`oh-my-codebuddy`](./plugins/codebuddy-plugins-official/plugins/oh-my-codebuddy/) | [oh-my-codebuddy](./plugins/codebuddy-plugins-official/plugins/oh-my-codebuddy/) | 完整的 OMC (Oh My CodeBuddy) 插件，包含 agents、commands、skills、hooks、tools 和 MCP servers。 | 无 | 10 |
| [`pdf`](./plugins/codebuddy-plugins-official/plugins/pdf/) | [pdf](./plugins/codebuddy-plugins-official/plugins/pdf/) | 全面的 PDF 处理工具包，支持提取文本和表格、创建新 PDF、合并/拆分文档、表单填写、加密解密、OCR 扫描等功能。 | 无 | 1 |
| [`php-lsp`](./plugins/codebuddy-plugins-official/plugins/php-lsp/) | [php-lsp](./plugins/codebuddy-plugins-official/plugins/php-lsp/) | PHP 语言服务器（Intelephense），提供代码智能和诊断。 | 无 | 0 |
| [`playwright-cli`](./plugins/codebuddy-plugins-official/plugins/playwright-cli/) | [playwright-cli](./plugins/codebuddy-plugins-official/plugins/playwright-cli/) | 浏览器自动化。 | 无（可选 API/账号以增强能力） | 1 |
| [`plugin-dev`](./plugins/codebuddy-plugins-official/plugins/plugin-dev/) | [plugin-dev](./plugins/codebuddy-plugins-official/plugins/plugin-dev/) | 用于开发 CodeBuddy Code 插件的综合工具包。 | 需要环境变量：`API_SECRET`、`API_TOKEN`、`AUTH_TOKEN` | 7 |
| [`plugin-finder`](./plugins/codebuddy-plugins-official/plugins/plugin-finder/) | [plugin-finder](./plugins/codebuddy-plugins-official/plugins/plugin-finder/) | 智能插件发现和管理助手 - 支持智能搜索、多插件并行对比、多插件协同工作流（sequence-run）、插件信息详解、许愿新插件等功能。 | 无 | 1 |
| [`ppt-writer`](./plugins/codebuddy-plugins-official/plugins/ppt-writer/) | [ppt-writer](./plugins/codebuddy-plugins-official/plugins/ppt-writer/) | AI驱动的PPT创作助手，支持智能内容生成、多格式导出和专业模板。 | 无 | 2 |
| [`pptx`](./plugins/codebuddy-plugins-official/plugins/pptx/) | [pptx](./plugins/codebuddy-plugins-official/plugins/pptx/) | PowerPoint 演示文稿创建、编辑和分析技能。 | 无 | 1 |
| [`pr-review-toolkit`](./plugins/codebuddy-plugins-official/plugins/pr-review-toolkit/) | [pr-review-toolkit](./plugins/codebuddy-plugins-official/plugins/pr-review-toolkit/) | 全面的 PR 审查代理工具集,专注于代码注释、测试覆盖、错误处理、类型设计、代码质量和代码简化。 | 无 | 0 |
| [`pyright-lsp`](./plugins/codebuddy-plugins-official/plugins/pyright-lsp/) | [pyright-lsp](./plugins/codebuddy-plugins-official/plugins/pyright-lsp/) | Python 语言服务器（Pyright），提供类型检查和代码智能提示。 | 无 | 0 |
| [`ralph-loop`](./plugins/codebuddy-plugins-official/plugins/ralph-loop/) | [ralph-loop](./plugins/codebuddy-plugins-official/plugins/ralph-loop/) | 用于迭代开发的交互式自引用AI循环，实现Ralph Wiggum技术。 | 无 | 0 |
| [`requirements-driven-workflow`](./plugins/codebuddy-plugins-official/plugins/requirements-driven-workflow/) | [requirements-driven-workflow](./plugins/codebuddy-plugins-official/plugins/requirements-driven-workflow/) | 需求驱动开发工作流，包含 90% 质量门控的实用功能实现流程。 | 无 | 0 |
| [`rust-analyzer-lsp`](./plugins/codebuddy-plugins-official/plugins/rust-analyzer-lsp/) | [rust-analyzer-lsp](./plugins/codebuddy-plugins-official/plugins/rust-analyzer-lsp/) | Rust 语言服务器，提供代码智能和分析功能。 | 无 | 0 |
| [`security-guidance`](./plugins/codebuddy-plugins-official/plugins/security-guidance/) | [security-guidance](./plugins/codebuddy-plugins-official/plugins/security-guidance/) | 安全提醒钩子，在编辑文件时警告潜在的安全问题，包括命令注入、XSS 和不安全的代码模式。 | 无 | 0 |
| [`security-rules`](./plugins/codebuddy-plugins-official/plugins/security-rules/) | [security-rules](./plugins/codebuddy-plugins-official/plugins/security-rules/) | 腾讯云鼎实验室出品，将安全专家经验融入代码生成过程，实时对常见漏洞的防护规则和安全函数约束，让 AI 直接生成安全代码，从源头保障代码安全质量。 | 无 | 0 |
| [`security-scan`](./plugins/codebuddy-plugins-official/plugins/security-scan/) | [security-scan](./plugins/codebuddy-plugins-official/plugins/security-scan/) | 插件「security-scan」（含 0 个 skill）。 | 需要企业微信应用凭证（CorpID/Secret 等）；需要大模型 API Key（OpenAI/Anthropic/Groq 等）；需要环境变量：`ANTHROPIC_API_KEY`、`GEMINI_API_KEY`、`GOOGLE_API_KEY`、`OPENAI_API_KEY`、`OPEN… | 0 |
| [`serena`](./plugins/codebuddy-plugins-official/plugins/serena/) | [serena](./plugins/codebuddy-plugins-official/plugins/serena/) | 语义代码分析 MCP 服务器，通过语言服务器协议集成提供智能代码理解、重构建议和代码库导航功能。 | 无 | 0 |
| [`skills-security-check`](./plugins/codebuddy-plugins-official/plugins/skills-security-check/) | [skills-security-check](./plugins/codebuddy-plugins-official/plugins/skills-security-check/) | 腾讯云鼎实验室出品，Skill安全审查工具。 | 无 | 1 |
| [`supabase`](./plugins/codebuddy-plugins-official/plugins/supabase/) | [supabase](./plugins/codebuddy-plugins-official/plugins/supabase/) | Supabase MCP 集成，用于数据库操作、身份验证、存储和实时订阅。 | 无 | 0 |
| [`swift-lsp`](./plugins/codebuddy-plugins-official/plugins/swift-lsp/) | [swift-lsp](./plugins/codebuddy-plugins-official/plugins/swift-lsp/) | Swift 语言服务器（SourceKit-LSP），提供代码智能支持。 | 无 | 0 |
| [`testbuddy`](./plugins/codebuddy-plugins-official/plugins/testbuddy/) | [testbuddy](./plugins/codebuddy-plugins-official/plugins/testbuddy/) | 文本测试用例生成插件。 | 需要环境变量：`TESTBUDDY_TOKEN` | 3 |
| [`tmap-lbs-plugin`](./plugins/codebuddy-plugins-official/plugins/tmap-lbs-plugin/) | [tmap-lbs-plugin](./plugins/codebuddy-plugins-official/plugins/tmap-lbs-plugin/) | 腾讯地图位置服务开发插件，提供 JavaScript GL 地图开发指南和 Web 服务 API（POI搜索、路径规划、旅游规划、轨迹可视化等）能力。 | 需要腾讯位置服务 Key（可用体验通道） | 2 |
| [`typescript-lsp`](./plugins/codebuddy-plugins-official/plugins/typescript-lsp/) | [typescript-lsp](./plugins/codebuddy-plugins-official/plugins/typescript-lsp/) | TypeScript/JavaScript 语言服务器，提供增强的代码智能功能。 | 无 | 0 |
| [`web-artifacts-builder`](./plugins/codebuddy-plugins-official/plugins/web-artifacts-builder/) | [web-artifacts-builder](./plugins/codebuddy-plugins-official/plugins/web-artifacts-builder/) | 使用现代前端技术（React、Tailwind CSS、shadcn/ui）创建复杂多组件 HTML 工件的工具套件。 | 无 | 1 |
| [`weixin-minigame-helper`](./plugins/codebuddy-plugins-official/plugins/weixin-minigame-helper/) | [weixin-minigame-helper](./plugins/codebuddy-plugins-official/plugins/weixin-minigame-helper/) | 微信小游戏AI调试、预览、运行、真机测试上传发布微信小游戏。 | 需要微信公众号/开放平台 AppID 与 AppSecret；需要环境变量：`WECHAT_APPID` | 1 |
| [`xlsx`](./plugins/codebuddy-plugins-official/plugins/xlsx/) | [xlsx](./plugins/codebuddy-plugins-official/plugins/xlsx/) | 全面的电子表格创建、编辑和分析工具，支持公式、格式化、数据分析和可视化。 | 无 | 1 |

### 4.2 cb_teams_marketplace（30）

| 目录 | 名称 | 用来做什么 | 前置条件 | skill 数 |
|------|------|------------|----------|---------|
| [`a-share-analysis`](./plugins/cb_teams_marketplace/plugins/a-share-analysis/) | [a-share-analysis](./plugins/cb_teams_marketplace/plugins/a-share-analysis/) | A股投资分析技能集，覆盖宏观研究、市场结构、个股深度、行业比较、资金行为、风险管理等 21 个专业分析 skill 和 6 个编排 agent。 | 无 | 20 |
| [`agent-sdk-dev`](./plugins/cb_teams_marketplace/plugins/agent-sdk-dev/) | [agent-sdk-dev](./plugins/cb_teams_marketplace/plugins/agent-sdk-dev/) | 插件「agent-sdk-dev」（含 0 个 skill）。 | 需要环境变量：`CODEBUDDY_API_KEY` | 0 |
| [`ai-hedge-fund`](./plugins/cb_teams_marketplace/plugins/ai-hedge-fund/) | [ai-hedge-fund](./plugins/cb_teams_marketplace/plugins/ai-hedge-fund/) | AI 对冲基金投资分析系统：19位投资大师并行分析 + 风险管理 + 投资组合决策的全流程投资分析。 | 无 | 0 |
| [`ardot-design-generator`](./plugins/cb_teams_marketplace/plugins/ardot-design-generator/) | [ardot-design-generator](./plugins/cb_teams_marketplace/plugins/ardot-design-generator/) | Ardot设计工具：在Ardot中生成高质量设计稿，移动端UI，网站页面，web应用，幻灯片等设计稿。 | 无 | 3 |
| [`codebuddy-chat-web`](./plugins/cb_teams_marketplace/plugins/codebuddy-chat-web/) | [codebuddy-chat-web](./plugins/cb_teams_marketplace/plugins/codebuddy-chat-web/) | 插件「codebuddy-chat-web」（含 1 个 skill）。 | 需要环境变量：`CODEBUDDY_API_KEY`、`CODEBUDDY_AUTH_TOKEN` | 1 |
| [`data`](./plugins/cb_teams_marketplace/plugins/data/) | [data](./plugins/cb_teams_marketplace/plugins/data/) | 数据分析插件，支持 SQL 查询、数据探索、可视化、仪表板构建和洞察生成。 | 无 | 8 |
| [`data-analysis`](./plugins/cb_teams_marketplace/plugins/data-analysis/) | [data-analysis](./plugins/cb_teams_marketplace/plugins/data-analysis/) | 插件「data-analysis」（含 2 个 skill）。 | 无 | 2 |
| [`deep-research`](./plugins/cb_teams_marketplace/plugins/deep-research/) | [deep-research](./plugins/cb_teams_marketplace/plugins/deep-research/) | 搜索与研究辅助。 | 无 | 1 |
| [`design-to-code`](./plugins/cb_teams_marketplace/plugins/design-to-code/) | [design-to-code](./plugins/cb_teams_marketplace/plugins/design-to-code/) | 设计工具套件：Figma 设计转代码、无障碍审查、设计评审、设计交付、设计系统管理、用户研究、UX 文案。 | 无（可选 API/账号以增强能力） | 8 |
| [`dockerfile-gen`](./plugins/cb_teams_marketplace/plugins/dockerfile-gen/) | [dockerfile-gen](./plugins/cb_teams_marketplace/plugins/dockerfile-gen/) | 插件「dockerfile-gen」（含 0 个 skill）。 | 无 | 0 |
| [`document-skills`](./plugins/cb_teams_marketplace/plugins/document-skills/) | [document-skills](./plugins/cb_teams_marketplace/plugins/document-skills/) | 插件「document-skills」（含 5 个 skill）。 | 无 | 5 |
| [`equity-research`](./plugins/cb_teams_marketplace/plugins/equity-research/) | [equity-research](./plugins/cb_teams_marketplace/plugins/equity-research/) | 搜索与研究辅助。 | 无 | 9 |
| [`executing-marketing-campaigns`](./plugins/cb_teams_marketplace/plugins/executing-marketing-campaigns/) | [executing-marketing-campaigns](./plugins/cb_teams_marketplace/plugins/executing-marketing-campaigns/) | 插件「executing-marketing-campaigns」（含 1 个 skill）。 | 无 | 1 |
| [`finance`](./plugins/cb_teams_marketplace/plugins/finance/) | [finance](./plugins/cb_teams_marketplace/plugins/finance/) | 财务与会计插件，支持月末结账、日记账分录、账户核对、财务报表生成、差异分析和 SOX 审计支持。 | 无 | 9 |
| [`financial-analysis`](./plugins/cb_teams_marketplace/plugins/financial-analysis/) | [financial-analysis](./plugins/cb_teams_marketplace/plugins/financial-analysis/) | 插件「financial-analysis」（含 9 个 skill）。 | 无 | 9 |
| [`gaokao-advisor`](./plugins/cb_teams_marketplace/plugins/gaokao-advisor/) | [gaokao-advisor](./plugins/cb_teams_marketplace/plugins/gaokao-advisor/) | 插件「gaokao-advisor」（含 4 个 skill）。 | 无（可选 API/账号以增强能力） | 4 |
| [`general-skills`](./plugins/cb_teams_marketplace/plugins/general-skills/) | [general-skills](./plugins/cb_teams_marketplace/plugins/general-skills/) | 插件「general-skills」（含 4 个 skill）。 | 需要环境变量：`OPENROUTER_API_KEY` | 4 |
| [`internal-comms`](./plugins/cb_teams_marketplace/plugins/internal-comms/) | [internal-comms](./plugins/cb_teams_marketplace/plugins/internal-comms/) | 插件「internal-comms」（含 1 个 skill）。 | 无 | 1 |
| [`investment-banking`](./plugins/cb_teams_marketplace/plugins/investment-banking/) | [investment-banking](./plugins/cb_teams_marketplace/plugins/investment-banking/) | 插件「investment-banking」（含 9 个 skill）。 | 无 | 9 |
| [`lseg`](./plugins/cb_teams_marketplace/plugins/lseg/) | [lseg](./plugins/cb_teams_marketplace/plugins/lseg/) | 插件「lseg」（含 8 个 skill）。 | 无 | 8 |
| [`modern-webapp`](./plugins/cb_teams_marketplace/plugins/modern-webapp/) | [modern-webapp](./plugins/cb_teams_marketplace/plugins/modern-webapp/) | 插件「modern-webapp」（含 4 个 skill）。 | 需要环境变量：`APP_PASSWORD` | 4 |
| [`ppt-implement`](./plugins/cb_teams_marketplace/plugins/ppt-implement/) | [ppt-implement](./plugins/cb_teams_marketplace/plugins/ppt-implement/) | 智能 PPT 生成助手，一键将您的想法转化为精美演示文稿。 | 无 | 1 |
| [`private-equity`](./plugins/cb_teams_marketplace/plugins/private-equity/) | [private-equity](./plugins/cb_teams_marketplace/plugins/private-equity/) | 插件「private-equity」（含 9 个 skill）。 | 无 | 9 |
| [`product-management`](./plugins/cb_teams_marketplace/plugins/product-management/) | [product-management](./plugins/cb_teams_marketplace/plugins/product-management/) | 产品管理插件，支持功能规格编写、路线图规划、利益相关者沟通、用户研究综合、竞品分析、指标审查、产品头脑风暴和冲刺规划。 | 无（可选 API/账号以增强能力） | 9 |
| [`remotion-video-generator`](./plugins/cb_teams_marketplace/plugins/remotion-video-generator/) | [remotion-video-generator](./plugins/cb_teams_marketplace/plugins/remotion-video-generator/) | 插件「remotion-video-generator」（含 6 个 skill）。 | 无 | 6 |
| [`skill-creator`](./plugins/cb_teams_marketplace/plugins/skill-creator/) | [skill-creator](./plugins/cb_teams_marketplace/plugins/skill-creator/) | 提供创建高效 Claude 技能的指南,通过专业知识、工作流程和工具集成来扩展 AI 助手的能力。 | 无 | 1 |
| [`spglobal`](./plugins/cb_teams_marketplace/plugins/spglobal/) | [spglobal](./plugins/cb_teams_marketplace/plugins/spglobal/) | 插件「spglobal」（含 3 个 skill）。 | 无 | 3 |
| [`trading-agent`](./plugins/cb_teams_marketplace/plugins/trading-agent/) | [trading-agent](./plugins/cb_teams_marketplace/plugins/trading-agent/) | 交易智能体插件：基于多角色辩论方法论的系统性投资分析，涵盖市场技术分析、基本面分析、新闻与情绪分析、多空辩论、交易决策与三方风险评估全流程，输出 BUY/SELL/HOLD 建议。 | 无 | 1 |
| [`wealth-management`](./plugins/cb_teams_marketplace/plugins/wealth-management/) | [wealth-management](./plugins/cb_teams_marketplace/plugins/wealth-management/) | 插件「wealth-management」（含 6 个 skill）。 | 无 | 6 |
| [`webapp-testing`](./plugins/cb_teams_marketplace/plugins/webapp-testing/) | [webapp-testing](./plugins/cb_teams_marketplace/plugins/webapp-testing/) | Web 应用测试助手，引导用户启动、配置和测试 Web 应用。 | 无（可选 API/账号以增强能力） | 0 |

