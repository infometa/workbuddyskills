# stock-partner-team

**腾讯自选股股票投研专家团** — CodeBuddy Agent Teams Plugin

---

## 简介

腾讯证券产品部 6 位公认的炒股大佬，穿越牛熊十几年，有人做过基金经理，有人当过投顾，有人是资讯信号猎手。我们把他们脑子里的投资框架和决策逻辑掏出来，炼化成了这个专家团插件。

你提问，成员们基于公开信息和真实数据各抒己见，给出多角度分析参考。

**适用场景**：单只个股深度研究 / 多只股票横向对比 / 组合持仓诊断 / 板块行业分析 / 宏观与大盘判断 / 选股点评——主理人按核心矛盾动态编排成员组合。

## 专家团成员

| Emoji | 花名 | 头衔 | 视角 | 擅长领域 |
|-------|------|------|------|----------|
| 🌊 | 星望远 | 产业策略师 | 产业策略 | 产业趋势猎手，15年经验，前公募基金经理。自上而下拆产业链，找核心卡位环节，用估值做硬约束 |
| 📡 | 洲四方 | 信号派首席 | 信号捕捉 | 信号捕捉老炮，20年实战。政策→产业→资讯→资金四层信号体系，四层对齐才动手 |
| 🧮 | 文衡价 | 估值分析师 | 估值定价 | 估值定价学院派，券商策略师出身，12年。Price = EPS x PE，PE Bands / PEG 精确定价 |
| 🏔️ | 坤候底 | 逆向投资人 | 逆向抄底 | 逆向抄底极简派，17年穿越牛熊。只买大市值跌出来的机会，看支撑位分10次买 |
| 🔬 | 钊审财 | 财报研究员 | 基本面研究 | 基本面深耕者，行业研究员型。从生活体感出发，按季度跟踪财报，基本面没变就拿着 |
| ⚡ | 磊追浪 | 短线冲浪手 | 短线交易 | 短线实战派，A股+美股双修，胜率约60%。抓当周主线，集合竞价确认，破均线就走 |

## 使用方式

### 1. 加载插件

在 CodeBuddy Code 中加载本地插件：

```
/plugin
```

在插件管理界面中添加本地目录指向 `stock-partner-team/` 目录。

### 2. 开始提问

加载后，直接向 CodeBuddy 提出股票相关问题即可。主理人会自动调度合适的成员进行分析。

**示例问题（按场景分类）：**

- 单股研究：「帮我分析下比亚迪」「腾讯最近怎么看」
- 多股对比：「宁德 vs 比亚迪 买哪个」「新能源三家对比下」
- 持仓诊断：「帮我看下我的持仓（腾讯/茅台/宁德/招行）」「这几只票怎么样」
- 板块行业：「新能源还能追吗」「白酒板块现在的估值水平？」
- 宏观大盘：「最近大盘怎么看」「美联储加息对 A 股影响」
- 个股事件：「套了 30% 怎么办」「茅台目前估值什么水平？」「最近什么主线？」
- 仓位配置：「50 万怎么配置」「核心+卫星怎么分」
- 选股点评：「高股息低估值标的筛下」「帮我从筛出的这批选几只」

### 3. 点名某位成员

你也可以在问法里点名某位成员，让 TA 担任这场圆桌的主角：

- "估值分析师，帮我看看腾讯的估值"
- "逆向投资人，这个价位能不能抄底？"
- "产业策略师，AI产业链怎么看？"

主理人仍会按核心矛盾再选 2-3 位配角形成圆桌（点名的成员稳坐主角位），不会退化成单成员单线程作答。

## 数据来源

本专家团**强烈依赖** **westock-mcp**（腾讯自选股）连接器获取实时行情、财务、选股等结构化数据（专家包已声明 `dependencies.connectors: ["westock-mcp"]`）。

| 连接器状态 | 取数方式 | 体验 |
|-----------|---------|------|
| **已连接** | 个股详情 → `data_*` Tool（westock-data）；选股筛选 → `tool_*` Tool（westock-tool）。**禁止** WebSearch 替代上述结构化数据 | 完整能力 |
| **未连接** | 降级取数：优先 WebSearch，可使用环境中其他可用 skill/MCP 补充 | **效果明显变差**——行情精度、财务指标、选股筛选等无法保证，分析结论时效性与准确性可能受影响 |

> ⚠️ **建议**：首次使用前完成 westock-mcp 连接器 OAuth 授权。WorkBuddy 首次召唤专家团时会弹出连接器引导卡片。

- 所有数据数字必须来自真实查询，禁止编造

## 报告产物

默认在对话中直接输出报告内容（md + HTML），不写本地文件。用户要求保存时，沉淀在 `{用户当前工作空间根目录}/deliverables/stock-partner/<YYYY-MM-DD>/` 目录下：

- `<主题>-<头衔>.md` — 上场成员各自的个人报告（圆桌模式下每位成员一份，组合/多股场景下一份横跨全部标的的组合视角报告）
- `<主题>-圆桌报告.md` — 主理人融合的圆桌汇总报告
- `<主题>-圆桌报告.html` — **默认产出**的可分享 HTML 版（Anthropic 浅色高级风，头像 base64 内嵌，约 200-300KB），可直接双击打开 / 发微信 / 发邮件

**主题关键词**由主理人根据用户问题概括成 3-10 字短词，按场景取：个股简称（腾讯）／多股对比（腾讯vs美团）／板块名（新能源）／宏观关键词（A股大盘）／组合标签（我的持仓、选股点评）。

> **HTML 渲染细节**：
> - 默认走 `skills/md-to-html` 渲染圆桌报告 HTML
> - HTML 渲染依赖 Python 3.8+ 与 Pillow；未安装时会保留相对路径版 HTML，稍后可重跑 `skills/md-to-html/scripts/embed_avatars.py` 补内嵌

## 环境要求

- **Python 3.8+**（用于 `skills/md-to-html/scripts/render.py` 与 `embed_avatars.py`）
- **Pillow**（用于 HTML 头像 base64 内嵌）：`pip install pillow`
- **验证安装**：`python3 -c "import PIL; print(PIL.__version__)"`

## 使用数据说明

本插件会在圆桌启动与报告交付成功时，采集**匿名任务级使用埋点**（用于渠道数据看板统计使用情况）：

- **采集内容**：随机生成的设备标识 `dev_id`（首次运行本地生成的 UUID）、事件时间戳、事件类型（start/complete）、任务耗时等常量字段。
- **不采集**：任何个人身份信息、股票查询内容、对话内容、账户信息。
- **上报方式**：由 `bin/init_task`（跨平台启动器，内部调 `init_task.py`）通过 HTTPS 上报，全程 fail-safe，网络异常不影响任何功能。
- **会话隔离**：多会话/多项目并发时，任务标记按会话隔离（默认按项目根 `.git` 或工作目录分桶）；`dev_id` 跨会话复用。可选环境变量 `WESTOCK_SESSION_KEY` 可显式指定会话隔离键，**普通用户无需配置**（未设置时自动回退，功能不受影响）。
- **关闭方式**：如需关闭，删除或清空 `bin/init_task.py` 即可（不影响专家团分析能力）。

## 目录结构

```
stock-partner-team/
├── .codebuddy-plugin/           # CodeBuddy 插件配置
│   └── plugin.json              # 含 dependencies.connectors: westock-mcp
├── avatars/                     # 头像目录
│   ├── team.png                 # 团队头像
│   ├── stock-partner-lead.png   # 主理人头像
│   ├── industry-strategist.png  # 产业策略师头像
│   ├── signal-chief.png         # 信号派首席头像
│   ├── valuation-analyst.png    # 估值分析师头像
│   ├── contrarian-investor.png  # 逆向投资人头像
│   ├── fundamental-researcher.png # 财报研究员头像
│   └── shortterm-surfer.png     # 短线冲浪手头像
├── agents/
│   ├── stock-partner-lead.md    # 主理人（编排核心）
│   ├── industry-strategist.md   # 产业策略师（产业视角）
│   ├── signal-chief.md          # 信号派首席（信号视角）
│   ├── valuation-analyst.md     # 估值分析师（估值视角）
│   ├── contrarian-investor.md   # 逆向投资人（逆向视角）
│   ├── fundamental-researcher.md # 财报研究员（基本面视角）
│   └── shortterm-surfer.md      # 短线冲浪手（短线视角）
├── skills/                      # 技能
│   ├── westock-data/            # 个股/指数详情查询（通过 westock-mcp data_* Tool）
│   │   ├── SKILL.md
│   │   └── references/          # MCP 映射、场景指南、字段说明
│   ├── westock-tool/            # 条件选股 / 高级筛选（通过 westock-mcp tool_* Tool）
│   │   ├── SKILL.md
│   │   └── references/
│   └── md-to-html/              # 圆桌报告 body 片段 → 可分享 HTML
│       ├── SKILL.md             # 薄入口：调用 render.py 的工作流
│       ├── components.md        # 组件接口手册：4 模块 + nav/hero 的 class 与 HTML 模板
│       ├── avatar-mapping.md    # 头衔 ↔ avatars/<kebab>.png 唯一映射
│       ├── shell.html           # 外壳模板（含全部 CSS + {{TITLE}}/{{BODY}}/{{DATE}} 占位符）
│       └── scripts/
│           ├── render.py        # 注入器：body 片段 → 完整 HTML（自动调 embed_avatars）
│           └── embed_avatars.py # 就地把 <img src="avatars/*.png"> 内嵌为 base64
├── bin/                         # 跨技能通用可执行文件（安装后加入 PATH）
│   ├── init_task                # 跨平台启动器（macOS/Linux，sh）——调用入口
│   ├── init_task.cmd            # 跨平台启动器（Windows，cmd）
│   └── init_task.py             # 实际逻辑：任务级 InLong 上报（start/complete）+ dev_id 持久化
├── settings.json                # 主理人设置
└── README.md
```

---

> ⚠️ **免责声明**：本插件所有输出内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。
