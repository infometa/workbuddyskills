# WorkBuddy Skill 技能大全（120个精选技能速查版）

> 来源：【ima知识库】WorkBuddy实战手册·进阶版 第三部分 · 已固化本地，专家不再调用 IMA
> 说明：SkillHub 已收录 8万+ 技能，本文精选 120 个高频实用技能。整理时间 2026-07-28

## 📌 通用安装方式（5种，适用于所有技能）

| 方式 | 操作步骤 | 适合人群 |
|---|---|---|
| ① 对话安装（最简单） | 在WorkBuddy对话框直接说"帮我安装pptx-generator"→系统自动匹配→确认安装 | 所有人，尤其小白 |
| ② SkillHub浏览安装 | 左侧"技能"菜单→搜索关键词→点击"+"安装，10秒完成 | 想浏览挑选的用户 |
| ③ SkillHub网页版安装 | 访问 skillhub.tencent.com→找到技能→复制安装指令→回WorkBuddy粘贴→自动完成 | 网页浏览习惯用户 |
| ④ CLI命令行安装 | npx clawhub@latest install <技能名> 或 skillhub install <技能名> | 开发者 |
| ⑤ GitHub安装 | npx skills add <作者>/<仓库名> --skill <技能名> 或下载ZIP导入 | 高级用户 |

## 🔧 CLI安装命令速查表

| 命令 | 说明 |
|---|---|
| npx clawhub@latest install <技能名> | 通用CLI安装（推荐，无需预先安装CLI） |
| clawhub install <技能名> | 需先安装ClawHub CLI（npm install -g clawhub） |
| npx skills add <github作者>/<仓库名> --skill <技能名> | 从GitHub仓库安装技能 |
| skillhub install <技能名> | 需先安装SkillHub CLI（npm install -g skillhub） |
| openclaw skills install <技能名> | 通过OpenClaw CLI安装 |

## 🛡️ 安全提醒

- **安装优先级**：WorkBuddy内置市场 > 腾讯SkillHub (skillhub.tencent.com) > ClawHub (clawhub.ai)
- **同类型技能只装一个**：避免冲突（如 pdf 和 nano-pdf 二选一；docx 和 word-docx 二选一）
- **装完即用**：大部分技能装完是"无感调用"——不用记技能名，直接说需求，AI自动判断任务类型并唤醒对应技能

## 📊 模型匹配建议

| 任务类型 | 推荐模型 | 禁忌模型 |
|---|---|---|
| 文档生成、PPT/Excel处理 | GLM-5.0-Turbo | ❌ Kimi系列 |
| PDF解析、深度内容分析 | Kimi-K2-Thinking | ❌ GLM系列 |
| 代码生成与调试 | DeepSeek-V3.2 | — |
| 公众号文章、创意内容 | MiniMax-M2.7 | — |

## 一、地基技能（必装，全岗位通用）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 1 | find-skills | 不知道该装什么技能时 | 技能雷达，推荐最合适的Skill | 帮我安装 find-skills 或 npx clawhub@latest install find-skills |
| 2 | pdf | 合同处理、报表整理、文档归档 | PDF读取、合并、拆分、OCR识别、转Word | 帮我安装 pdf 技能 |
| 3 | docx | 写报告、起草通知、教案生成 | Word文档创建/编辑/排版 | 帮我安装 docx 技能 |
| 4 | xlsx | 报表汇总、数据清洗、成绩统计 | Excel读写、数据分析、公式、图表 | 帮我安装 xlsx 技能 |
| 5 | pptx | 汇报PPT、培训课件、演讲稿 | PPT生成、自动排版、导出可编辑文件 | 帮我安装 pptx 技能 |
| 6 | agent-browser | 网页数据采集、自动填报表 | 浏览器自动化：导航/点击/截图/填表 | 帮我安装 agent-browser 或 npx clawhub@latest install agent-browser |
| 7 | agent-memory | 跨对话记住偏好 | 上下文记忆固化，越用越顺手 | 帮我安装 agent-memory |
| 8 | self-improving-agent | 任务出错时自动纠错 | 自我改进+记忆，自动记录错误 | 帮我安装 self-improving-agent |
| 9 | skill-vetter | 安装新技能前安全扫描 | 安全预审，检测技能风险 | 帮我安装 skill-vetter |
| 10 | skill-creator | 把重复工作流封装成专属技能 | 自建技能，零代码图形化创建 | 帮我安装 skill-creator |

## 二、办公文档处理类（8个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 11 | PDF-EDITOR (mainpdf) | 编辑扫描版合同、提取关键条款 | 全能PDF编辑：抽正文、抽表格、OCR | 帮我安装 PDF-EDITOR 技能 |
| 12 | nano-pdf | PDF合并拆分、扫描件转文字 | PDF全流程处理（与pdf二选一） | npx clawhub@latest install nano-pdf |
| 13 | markdown-converter | 教材PDF转可编辑文字 | 乱格式一键清洗成干净Markdown | npx skills add steipete/agent-scripts --skill markdown-converter |
| 14 | markdown-to-word | Markdown教研文章转规范Word | Markdown转Word，保留标题层级和表格 | 帮我安装 markdown-to-word |
| 15 | batch-file-processing | 学生作业批量命名、分类归档 | 批量文件处理，按规则重命名/分类 | 帮我安装 batch-file-processing |
| 16 | gongwenformat-pro | 红头文件、通知、请示函排版 | 符合GB/T 9704-2012标准的公文排版 | 帮我安装 gongwenformat-pro |
| 17 | document-formatter | PRD文档排版、制度文件整理 | 文档排版和格式化 | 帮我安装 document-formatter |
| 18 | word-docx | 试卷、教案、学期计划生成 | Word智能排版：补目录、补页码、批注 | 帮我安装 word-docx |

## 三、PPT与演示类（7个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 19 | guizang-ppt-skill | 年度总结、商务汇报PPT | 瑞士风PPT，22种布局+动态切换 | npx skills add https://github.com/op7418/guizang-ppt-skill --skill guizang-ppt-skill |
| 20 | pptx-generator | 方案提案、产品路演PPT | 生成可编辑PPTX文件（11种幻灯片类型） | 帮我安装 pptx-generator |
| 21 | ppt-generator | 科技风演示稿、乔布斯风格PPT | 生成HTML演示稿，渐变背景+极简排版 | 帮我安装 ppt-generator 技能 |
| 22 | ppt-master | 输入主题和要点自动出PPT初稿 | AI驱动PPTX生成，支持原生动画 | npx skills add hugohe3/ppt-master |
| 23 | Frontend Slides | 高级网页设计PPT | 零依赖HTML演示文稿，34种设计模板 | 帮我安装 Frontend Slides |
| 24 | taste | 高级视觉设计PPT | 为AI编码Agent安装设计审美 | npx skills add Leonxlnx/taste-skill |
| 25 | canvas-design | 基于设计哲学创作视觉艺术 | 高质量视觉艺术与海报设计 | 帮我安装 canvas-design |

## 四、数据分析与可视化类（6个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 26 | data-analyst | 销售数据报表、运营指标分析 | 分析CSV/Excel/JSON数据，生成摘要和图表 | 帮我安装 data-analyst |
| 27 | Simple Excel | 重复性数据处理、画图表 | 简单Excel读写创建编辑 | 帮我安装 Simple Excel 技能 |
| 28 | davila7/xlsx | 对账、透视表、批量公式 | Excel数据处理增强版 | npx skills add davila7/claude-code-templates --skill xlsx |
| 29 | summarize | 100页报告30秒出核心观点 | 一键总结网页/PDF/图片/音频/视频 | 帮我安装 summarize |
| 30 | text-structuring | 8000字培训稿整理成要点提纲 | 文本结构化处理 | 帮我安装 text-structuring |
| 31 | dialogue-review | 复盘本周对话提炼备课模板 | 对话复盘与知识沉淀 | 帮我安装 dialogue-review |

## 五、内容创作与自媒体类（15个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 32 | social-content | 小红书文案、朋友圈、视频脚本 | 社交媒体内容创作，按平台调性写文案 | 帮我安装 social-content |
| 33 | copywriting | 广告文案、产品介绍、销售页面 | 营销文案全能选手，经典文案公式 | 帮我安装 copywriting |
| 34 | content-strategy | 选题规划、内容日历 | 内容营销策略规划 | npx skills add coreyhaines31/marketingskills --skill content-strategy |
| 35 | content-factory | 一份教案→公众号文+短视频脚本 | 多代理内容生产流水线，多平台发布 | npx skills add https://github.com/aaaaqwq/agi-super-skills --skill content-factory |
| 36 | wechat-search | 公众号选题搜索 | 搜近期爆款文章按数据评分排序 | npx clawhub@latest install wechat-search |
| 37 | wechat-publisher | 公众号一键发布 | 公众号发布管理 | 帮我安装 wechat-publisher |
| 38 | gzh-design | 公众号排版设计 | Markdown一键转公众号HTML | npx skills add isjiamu/gzh-design-skill |
| 39 | huashu-skills | 封面图、信息图、漫画、排版、翻译 | 花叔内容创作21合1合集 | npx skills add alchaincyf/huashu-skills |
| 40 | khazix-writer | 公众号深度写作 | 四层自检校验长文写作 | npx skills add https://github.com/kkkkhazix/khazix-skills --skill khazix-writer |
| 41 | seo-content-writer | SEO优化文章写作 | 关键词布局、标题优化、内容结构 | 帮我安装 seo-content-writer |
| 42 | seo-optimizer | 搜索排名优化 | 网站SEO分析与优化工具 | 帮我安装 seo-optimizer |
| 43 | humanizer | 去AI味让文章更自然 | 检测AI写作特征+自然重写 | 帮我安装 humanizer |
| 44 | Humanizer-zh | 中文去AI味 | 中文文案人性化优化，24类AI特征检测 | npx skills add https://github.com/op7418/humanizer-zh |
| 45 | video-script-creator | 微课脚本、班级抖音、知识点讲解 | 短视频脚本创作，适配抖音/快手/B站 | 帮我安装 video-script-creator |

## 六、运营与营销类（7个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 46 | email-writer | 面试通知、Offer模板、商务邮件 | 专业商务邮件撰写 | 帮我安装 email-writer |
| 47 | competitor-analysis | 竞品调研、市场对比 | 竞品分析出对比报告 | 帮我安装 competitor-analysis |
| 48 | user-research | 用户调研分析 | 用户研究和调研结论输出 | 帮我安装 user-research |
| 49 | growth-hacking | 增长方案策划 | 增长策略规划 | 帮我安装 growth-hacking |
| 50 | marketing-ideas | 营销灵感发散 | 营销方案创意生成 | 帮我安装 marketing-ideas |
| 51 | last30days-skill | 近30天热点数据、选题库 | 选题雷达，海外主流平台热点抓取 | 帮我安装 last30days-skill |
| 52 | Market Research | 项目分析、市场规模评估 | 市场调研分析框架+报告输出 | 帮我安装 Market Research |
| 53 | prompt-optimizer | 大白话需求→标准化指令 | 提示词优化，提升AI执行成功率 | 帮我安装 prompt-optimizer |

## 七、金融投资类（15个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 54 | wb-finance-skill | 查股票、基金、行业数据 | 金融数据查询+行情分析（新手必装） | 帮我安装 wb-finance-skill |
| 55 | NeoData金融 | 金融数据查询 | 东方财富数据库接入 | 帮我安装 NeoData 金融技能 |
| 56 | 平安证券资讯查询 | 平安证券资讯 | 平安证券数据查询 | 帮我安装 平安证券资讯查询技能 |
| 57 | 腾讯自选股 | 实时股票行情 | 腾讯自选股数据 | 帮我安装 腾讯自选股技能 |
| 58 | A股每日复盘 | 每日A股复盘分析 | A股市场每日复盘报告 | 帮我安装 A股每日复盘 |
| 59 | A股涨跌停日报 | 涨跌停数据日报 | A股涨跌停统计 | 帮我安装 A股涨跌停日报 |
| 60 | A股短线交易 | 短线交易策略 | A股短线分析 | npx skills add lijq126/short-term-stock-picker |
| 61 | 每日财经新闻 | 每日财经要闻 | 财经新闻聚合 | 帮我安装 每日财经新闻技能 |
| 62 | 宏观数据日报 | 宏观经济指标 | 宏观经济数据日报 | 帮我安装 宏观数据日报技能 |
| 63 | 大盘走势研判分析 | 大盘走势判断 | 大盘走势技术分析 | 帮我安装 大盘走势研判分析技能 |
| 64 | ETF深度对比 | ETF基金对比 | ETF深度对比分析 | 帮我安装 ETF深度对比技能 |
| 65 | 基金分析 | 基金筛选与分析 | 基金数据查询分析 | 帮我安装 基金分析技能 |
| 66 | 持仓监控告警 | 持仓风险监控 | 持仓异动告警 | 帮我安装 持仓监控告警技能 |
| 67 | 股票分析 | A股/港股/美股行情分析 | 股票行情技术分析 | 帮我安装 股票分析技能 |
| 68 | 足球贝叶斯分析 | 足球赛事概率分析 | 贝叶斯模型赛事预测 | npx clawhub@latest install football-bayes |

## 八、编程与开发类（10个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 69 | code-1 | 写Python脚本、搭网页、处理数据 | 代码开发全能，多语言支持 | 帮我安装 code-1 技能 |
| 70 | git-essentials | 提交代码、切分支、合并冲突 | Git版本控制操作 | 帮我安装 git-essentials |
| 71 | git-master | 原子提交、合并、历史搜索 | Git工作流专家 | 帮我安装 git-master |
| 72 | code-review | 找代码潜在问题和优化点 | 代码审查 | 帮我安装 code-review |
| 73 | refactor | 优化现有代码结构 | 代码重构 | 帮我安装 refactor |
| 74 | testing-expert | 写单元测试、集成测试 | 测试开发 | 帮我安装 testing-expert |
| 75 | security-audit | 找代码安全漏洞 | 代码安全审计 | 帮我安装 security-audit |
| 76 | superpowers-zh | 海外爆款技能中文增强版 | 中文方法论Skills合集 | git clone https://github.com/jnMetaCode/superpowers-zh.git → 复制到 ~/.workbuddy/skills/ |
| 77 | github-trending-cn | 看GitHub热门项目 | GitHub趋势监控 | 帮我安装 github-trending-cn |
| 78 | wechat-miniprogram | 微信小程序开发 | 微信小程序开发框架 | 帮我安装 wechat-miniprogram |

## 九、设计、图像与多媒体类（10个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 79 | image-generator | AI生图、封面图、配图 | 多风格AI生图 | 帮我安装 image-generator |
| 80 | image-generation | 多模型图片生成 | 多模型图片生成 | 帮我安装 image-generation |
| 81 | gptimage-2 | GPT高质量图片生成 | GPT Image 2模型生图 | 帮我安装 gptimage-2 |
| 82 | nano-banana-pro | 4K高清AI画图+改图 | AI画图（教学情境图、封面图） | 帮我安装 nano-banana-pro |
| 83 | sketch-illustration | 教学插画、知识海报、板书图 | 5种风格手绘插画 | 帮我安装 sketch-illustration |
| 84 | openai-image-gen | 课件配图、班会海报、教学素材 | AI图像生成（卡通风格等） | 帮我安装 openai-image-gen |
| 85 | tencentcloud-ocr | 图片文字高精度识别 | 腾讯云OCR识别 | 帮我安装 tencentcloud-ocr |
| 86 | Video Generator (Remotion) | 从需求到MP4视频 | Remotion视频生成 | 帮我安装 Video Generator 技能 |
| 87 | ffmpeg-video-editor | 视频裁剪、合并、加字幕、转格式 | FFmpeg视频剪辑 | 帮我安装 ffmpeg-video-editor |
| 88 | openai-whisper | 公开课录像转文字、口语测评 | 音视频转文字 | 帮我安装 openai-whisper |

## 十、办公协同与通讯类（9个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 89 | lark-unified | 飞书消息/文档/日程管理 | 飞书全能套件 | 帮我安装 lark-unified |
| 90 | dingtalk-unified | 钉钉消息/审批/日程 | 钉钉CLI套件 | 帮我安装 dingtalk-unified |
| 91 | kdocs | 金山文档在线协作 | 金山文档（WPS）读写 | npx clawhub@latest install kdocs |
| 92 | IMAP/SMTP邮件 | 多账户邮件收发+附件 | 邮件收发处理（内置连接器） | 「连接器」页面配置，无需安装技能包 |
| 93 | 企业微信套件 | 企业微信消息/文档/日程 | 企微全功能套件（官方MCP） | npx -y @wecom/wecom-openclaw-cli install --force |
| 94 | 腾讯文档 PDFKit | 腾讯文档PDF处理 | 腾讯文档PDF生成 | 帮我安装 PDFKit 技能 |
| 95 | QQ邮箱连接器 | QQ邮箱收发邮件 | QQ邮箱MCP连接（内置连接器） | 「连接器」页面QQ邮箱卡片→扫码授权 |
| 96 | meeting-notes | 会议录音转文字、提取决策待办 | 会议纪要自动整理 | 帮我安装 会议纪要技能 |
| 97 | 1password | API密钥、密码自动管理 | 密钥管理 | npx clawhub@latest install steipete/1password |

## 十一、知识管理与信息类（6个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 98 | ima-skills | IMA知识库笔记读写检索 | IMA知识库管理 | 下载ZIP→技能中心导入 或 SkillHub搜索"ima-skills" |
| 99 | WPS知识库 | WPS文档知识库 | WPS知识库接入 | 同kdocs安装方式 |
| 100 | tavily-search | 搜索最新政策、学科前沿 | 联网实时搜索 | 帮我安装 tavily-search |
| 101 | Web Access | 网页信息获取 | 网页访问能力（WorkBuddy内置） | 无需安装，WorkBuddy内置支持 |
| 102 | QQ浏览器自动化 | 浏览器自动操作 | QQBrowserUse自动化 | 帮我安装 QQ浏览器自动化 |
| 103 | Playwright Browser | 高级网页自动化 | Playwright浏览器自动化 | npx clawhub@latest install playwright-mcp |

## 十二、腾讯生态服务类（6个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 104 | 腾讯新闻 | 实时新闻资讯 | 腾讯新闻数据 | 帮我安装 腾讯新闻技能 |
| 105 | 腾讯地图 | 地理位置查询、商圈分析 | 腾讯地图服务 | 帮我安装 腾讯地图技能 |
| 106 | 腾讯电子签 | 电子合同签署 | 腾讯电子签 | 通过MCP连接器接入（非独立Skill包） |
| 107 | QQ音乐助手 | 音乐信息查询 | QQ音乐数据 | 帮我安装 QQ音乐助手 |
| 108 | 微信直播skill | 创建直播、上架商品、查询数据 | 微信直播全链路运营 | 帮我安装 微信直播技能 |
| 109 | 商业选址 | 零售/餐饮商圈分析选址 | 基于高德地图商圈分析 | 帮我安装 商业选址技能 |

## 十三、深度研究类（3个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 110 | Deep Research | 复杂研究项目、多来源深度调研 | 多来源深度调研与报告生成 | 帮我安装 Deep Research |
| 111 | research-paper-writer | 学术论文写作 | IEEE/ACM标准格式学术论文 | 帮我安装 research-paper-writer |
| 112 | automation-workflows | 重复性工作自动化 | Zapier/Make/n8n自动化工作流 | 帮我安装 automation-workflows |

## 十四、专业领域类（8个）

| # | 技能名称 | 使用场景 | 核心功能 | 安装指令 |
|---|---|---|---|---|
| 113 | 案件分析报告 | 法律案件分析 | 法律关系分析法Plus，检索法条类案 | 帮我安装 案件分析报告技能 |
| 114 | 专利交底书 | 专利申请撰写 | 专利交底书生成 | 帮我安装 专利交底书技能 |
| 115 | 法律文书 | 合同审查、法律意见书 | 法律文书模板管理 | 从法律元力网站下载 |
| 116 | 需求分析 | 产品需求文档 | 需求分析文档撰写 | 帮我安装 需求分析技能 |
| 117 | 财报分析Skill | 10家公司财报一键分析 | Excel公式驱动7Sheet12指标分析 | 帮我安装 财报分析技能 |
| 118 | 财报附注生成 | 财报附注自动生成 | 找数汇总归类回填自动化 | 帮我安装 财报附注生成技能 |
| 119 | grill-me | 问答式学习考核 | 自我考核技能 | npx skills add mattpocock/skills/grill-me |
| 120 | geography-teaching | 中学地理教案/知识整合/教学案例 | 地理学科专属技能包 | 帮我安装 geography-teaching |

## 📎 补充：常用自建技能模板（5个参考方向）

| 方向 | 自建技能名称 | 使用场景 | 创建方式 |
|---|---|---|---|
| 邮件管理 | 邮件自动分类回复 | 批量邮件自动分类+智能回复 | 对话中说"帮我创建一个邮件自动分类回复的技能" |
| 数据处理 | 一键数据清洗分析 | Excel/CSV数据清洗+分析+可视化 | 对话中说"帮我创建一个一键数据清洗分析的技能" |
| 公众号运营 | 公众号一人编辑部 | 选题→写作→排版→发布全链路 | 对话中说"帮我创建一个公众号一人编辑部的技能" |
| 竞品监控 | 竞品监控简报 | 定时抓取竞品动态生成简报 | 对话中说"帮我创建一个竞品监控简报的技能" |
| 热点追踪 | 热点选题追踪 | 实时热点自动追踪+选题推荐 | 对话中说"帮我创建一个热点选题追踪的技能" |

## 🔗 主要来源参考

| 来源 | 地址 |
|---|---|
| SkillHub官方市场 | https://skillhub.tencent.com / https://skillhub.cn |
| ClawHub社区市场 | https://clawhub.ai |
| 语雀WorkBuddy常用Skills文档 | https://www.yuque.com/sdutzhou/durg6g/ht2pfhfiutlq2b43 |
| 法律元力技能目录 | https://yuanli.ailaw.cn/skills/ |
| 腾讯云开发者社区 | 多篇WorkBuddy系列教程 |

> 建议：先装地基10个，再按岗位选装，试一周确认适配性后再扩展。
> 本文件由【ima知识库】Skill技能大全固化整理，供 WorkBuddy 全能导师专家本地调用。
