# Expert Marketplace 项目规范

本规范用于 CodeBuddy 专家包目录审查。专家对标 CodeBuddy CLI 的 plugin 体系，但只使用其中的**专家相关子集**——不包含 hook、command、.lsp.json。

核心概念：**专家 = 精简版 plugin**，**技能 = 专家的子能力模块**。

---

## 一、专家类型

| 类型 | expertType | 说明 |
|------|-----------|------|
| Agent 型 | `"agent"` | 单个 AI 专家，拥有特定领域能力 |
| Team 型 | `"team"` | 多角色协作团队，由主理人编排分工 |
| Plugin 型 | `"plugin"` | 纯技能包，无 agent 定义，只提供 skills |

## 二、目录结构

### Agent 型

```
plugins/{name}/
├── .codebuddy-plugin/
│   └── plugin.json          # 核心配置(必须)
├── avatars/                  # 头像(expertType 为 agent/team 时必须)
│   └── expert.png
├── agents/                   # Agent 定义(必须)
│   └── {agent-name}.md
├── skills/                   # 技能(可选)
│   └── {skill-name}/
│       └── SKILL.md
├── bin/                      # 可执行文件(可选，安装后加入 PATH)
│   └── my-tool
└── README.md                 # 说明(推荐)
```

### Team 型

```
plugins/{name}/
├── .codebuddy-plugin/
│   └── plugin.json
├── avatars/
│   ├── team.png              # 团队头像
│   ├── team-lead.png         # 主理人头像
│   └── {member}.png          # 团队成员头像
├── agents/
│   ├── {team}-team-lead.md   # 主理人(含编排逻辑，文件名须加团队前缀)
│   └── {member}.md           # 团队成员
├── skills/                   # 共享技能(可选)
│   └── {skill-name}/SKILL.md
├── bin/                      # 可执行文件(可选)
├── settings.json             # 指定主理人(必须)
└── README.md
```

### Plugin 型(纯技能包)

```
plugins/{name}/
├── .codebuddy-plugin/
│   └── plugin.json
├── skills/                   # 技能(必须，至少一个)
│   └── {skill-name}/
│       └── SKILL.md
├── bin/                      # 可执行文件(可选)
└── README.md
```

### 关键约束

- `agents/`、`skills/`、`bin/`、`avatars/` 都在插件根目录，不要放进 `.codebuddy-plugin/` 里
- 本项目**不使用** `hooks/`、`commands/`、`.lsp.json`

---

## 三、plugin.json 字段

### 3.1 基础字段(必填)

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 唯一标识，小写字母+连字符，也是技能命名空间前缀 |
| `version` | string | 语义化版本号(MAJOR.MINOR.PATCH) |
| `description` | string | 英文一句话描述 |

### 3.2 可选基础字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `author` | `{name, email}` | 作者信息 |
| `homepage` | string 或 `{url, type}` | 项目主页 |
| `license` | string | 许可证 |
| `keywords` | string[] | 搜索标签 |

### 3.3 类型字段

| 字段 | 说明 |
|------|------|
| `expertType` | `"agent"` / `"team"` / `"plugin"` |
| `agentName` | 主 Agent 名称(对应 agents/ 下 MD 文件名，不含 .md)。**必须有业务语义**，不能使用 `team-lead` 等通用名，避免多插件同时启用时 name 冲突 |
| `teamInfo` | team 时必填：`{leadAgent, memberAgents[]}` |

### 3.4 资源声明

| 字段 | 类型 | 说明 |
|------|------|------|
| `agents` | string[] | Agent 定义文件路径列表(如 `["./agents/team-lead.md", "./agents/member.md"]`) |
| `skills` | string[] | Skill 目录路径列表(如 `["./skills/code-review"]`) |

### 3.5 展示字段(agent/team 上架市场时必填)

| 字段 | 类型 | 说明 |
|------|------|------|
| `displayName` | `{en, zh}` | 展示名称。外部提交包尊重作者已有命名体系，不强制套用谐音花名风格 |
| `profession` | `{en, zh}` | 职业/定位。用于市场展示与身份识别 |
| `displayDescription` | `{en, zh}` | 展示描述。建议中文字数在 40-50 字之间，突出专家或专家团的核心能力 |
| `avatar` | string | 头像相对路径(如 `"avatars/expert.png"`) |
| `categoryId` | string | 行业分类 ID |
| `defaultInitPrompt` | `{en, zh}` | 默认引导语。建议与 `quickPrompts` 的第一条保持一致 |
| `tags` | `{en, zh}[]` | 专家擅长领域标签，建议 3-5 个，用于搜索和市场展示 |
| `quickPrompts` | `{en, zh}[]` | 推荐提示词，建议 3 个，展示在专家卡片上引导用户快速提问 |

### 3.6 Team 专用字段

| 字段 | 说明 |
|------|------|
| `members[]` | 每个成员含 `{id, displayName:{en,zh}, profession:{en,zh}, avatar, role}` |

- `role` 取值：`"lead"` 或 `"member"`
- 主理人也必须在 members 中，role 为 `"lead"`

### 3.7 示例

**Agent 型(精简)**：

```json
{
  "name": "llm-wiki",
  "version": "1.0.0",
  "description": "LLM Wiki Knowledge Management Expert",
  "expertType": "agent",
  "agentName": "llm-wiki"
}
```

**Plugin 型(纯技能包)**：

```json
{
  "name": "equity-research",
  "version": "1.0.0",
  "description": "Equity research tools: earnings analysis, initiating coverage reports, and research workflows",
  "author": { "name": "CodeBuddy Teams" },
  "skills": [
    "./skills/earnings-analysis",
    "./skills/morning-note",
    "./skills/sector-overview"
  ],
  "expertType": "plugin"
}
```

**Team 型(完整)**：参见 `plugins/stock-partner-team/.codebuddy-plugin/plugin.json`

---

## 四、Agent 定义文件 (agents/*.md)

### 4.1 Frontmatter

```yaml
---
name: {与文件名一致，必须有业务语义}
description: {英文描述，AI 用来判断何时激活}
displayName:
  en: "{English display name}"
  zh: "{中文显示名称}"
profession:
  en: "{English profession title}"
  zh: "{中文职业头衔}"
maxTurns: {默认50}
---
```

**注意**：
- `displayName` 和 `profession` 为必填字段，用于专家市场展示和成员身份识别
- **禁止在 frontmatter 中声明 `tools` 字段**。工具权限由系统统一分配，手动声明会导致 agent 缺失关键能力（如主理人缺失 AgentTool 导致 create team 失败）

### 4.2 可用工具

- Read, Write, Grep, Glob, Bash — 通用工具
- WebSearch, WebFetch — 联网工具
- AgentTool, SendMessage — 主理人专用(调度团队成员)

### 4.3 提示词结构(推荐)

1. 角色定义
2. 核心能力
3. 工作流程
4. 输出规范
5. 注意事项

### 4.4 主理人特殊要求

主理人 MD 中**必须包含「团队协作机制（铁律）」章节**，内容如下：

#### 协作铁律（4 条正则）

1. **建立团队**：任务开始时由主理人亲自创建团队（TeamCreate），明确协作边界。**团队创建必须且只能由主理人执行，严禁委派任何成员创建团队**
2. **调度成员**：按 SOP 阶段将成员拉入协作、下发独立任务；成员作为独立协作方输出专业产出，不得由主理人代写
3. **消息中转**：成员产出回传给主理人，由主理人汇总、转交下一阶段；所有跨成员信息流必须经主理人中转，不得互相直连
4. **成员结论为准**：任何专业产出必须由对应成员输出后再采信，主理人只做编排与汇编

#### 严禁行为（5 条红线）

- ❌ 禁止跳过 TeamCreate，直接自己模拟成员发言或并行写出多角色内容
- ❌ 禁止自己代写任何团队成员的专业产出
- ❌ 禁止未完成前序阶段就跳到后续阶段
- ❌ 禁止让成员互相直连通信，所有跨成员信息流必须经主理人中转
- ❌ 禁止 spawn 主理人自己（编排、汇总、决策由主理人亲自完成，不得委派给名为主理人的子任务）

#### 协作规则

1. 所有成员调度必须经过"TeamCreate → Agent spawn → SendMessage 回传"正式流程
2. 每阶段结束后，将完整产出原文传递给下一阶段成员
3. 调度成员时，在 Agent 工具的 `name` 参数中传入该成员的 **Agent ID**（即 agents/ 下的 MD 文件名，不含 .md），`subagent_type` 也传入相同值。**禁止**使用中文名或自创名称，确保 UI 层能通过 `members[].id` 精确匹配到 displayName
4. 裁决型角色（如研究主管、风险主管）必须给出明确结论，不得回避决策
5. 每完成一个阶段向用户简要通报进度

#### 4.4.1 成员能力清单

主理人 prompt 中必须列出每个成员的：
- Agent ID
- 擅长领域（3-5 个具体能力点）
- 典型问法（什么问题该调它）

目的：让主理人（和读 prompt 的人）能快速判断每个问题该调谁。

#### 4.4.2 预设 Workflow

针对用户常见的**综合性问题**，主理人 prompt 中设计多个预设 Workflow，每个 Workflow 写明：

- **触发条件**：什么类型的问法匹配此 Workflow
- **Phase 编排**：分 Phase 的串并行调度
  - 并行 Phase：同一条消息中 spawn 多个成员
  - 串行 Phase：等前一 Phase 全部回传后，将结论传入下一 Phase 的成员 prompt
- **输入输出依赖**：每个 Phase 的输入来自哪里、输出传给谁

Workflow 数量根据用户实际高频场景设计，不是越多越好。

**示例**（个股深度研究 Workflow）：
```
Phase 1（并行）：
  stock-researcher → 基本面+财务
  valuation-pricer → 估值判断
  money-tracker   → 资金态度

Phase 2（串行，Phase 1 结论传入）：
  risk-doctor → 综合风险诊断

主理人汇编 → 输出
```

#### 4.4.3 单 agent 直调

简单问题不走 Workflow，直接 spawn 对应成员。主理人 prompt 中附路由表：

| 问法类型 | 直接调谁 |
|---------|---------|
| 单一维度问题 | 对应成员 |
| 综合性问题 | 走预设 Workflow |

### 4.5 团队成员要求

#### 4.5.1 基本要求

- **不要在 frontmatter 中限制 tools 范围**（如果加 tools 就必须加全，否则会缺失必要工具；不加则使用默认全量工具，由运行时自动分配）
- 团队成员由主理人通过 Agent 工具 spawn 为正式 teammate，自行查询数据并通过 SendMessage 回传分析结果

#### 4.5.2 能独立成 agent 的标准

每个成员 agent 必须能独立回答用户的某类问题——如果一个能力只是分析流程的子步骤（如"出海筛选""分红回报"），不适合独立成 agent，应归入相关 agent 内嵌。

判断标准：**有没有用户会直接问它的问题？** 有 → 独立成 agent；没有 → 归入其他 agent。

#### 4.5.3 Prompt 结构

成员 agent 的 prompt 必须包含：

1. **角色定义**：一句话说清"你是谁"
2. **擅长领域**：3-5 个具体能力点（和主理人的成员清单对应）
3. **分析框架**：内嵌的分析能力，写成分步骤流程
4. **数据获取方式**：具体的查询命令或工具调用
5. **结构化输出模板**：表格/分段格式
6. **SendMessage 回传要求**：分析完成后必须通过 SendMessage 将结果回传给主理人。prompt 中需明确写出此要求，确保成员知道自己是被 spawn 的 teammate，结果需要回传

#### 4.5.4 内聚原则

每个 agent 覆盖一个完整的"分析域"，域内多个能力归并进来，但不跨域。跨域协作由主理人通过 Workflow 编排。

---

## 五、Skill 规范

Skill 是专家的子能力模块。每个 skill 是一个目录，包含一个 SKILL.md 文件，可选附带子资源。

### 5.1 目录结构

```
skills/
└── {skill-name}/
    ├── SKILL.md              # 技能定义(必须)
    ├── scripts/              # 可执行脚本(可选)
    └── templates/            # 模板文件(可选)
```

### 5.2 SKILL.md Frontmatter

```yaml
---
name: {skill-name}            # 技能标识，省略则用目录名
description: {描述}            # AI 用来判断何时触发此技能
allowed-tools: Tool1, Tool2   # 工具白名单(可选)
disable-model-invocation: true # 禁止 AI 自动触发(可选)
user-invocable: false          # 隐藏 / 菜单(可选，默认 true)
context: fork                  # 隔离子 Agent 执行(可选)
agent: Explore                 # 子 Agent 类型(仅 context:fork 时有效)
---
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 否 | 技能标识，省略则用目录名 |
| `description` | 推荐 | AI 根据此字段判断何时触发，务必写清用途和触发词 |
| `allowed-tools` | 否 | 逗号分隔的工具白名单，支持模式匹配如 `Bash(git:*)` |
| `disable-model-invocation` | 否 | `true` 则 AI 不会自动触发，只能用户手动 `/skill-name` |
| `disable` | 否 | `true` 则完全禁用(仅作参考资料，其他 skill 可引用) |
| `user-invocable` | 否 | `false` 则隐藏 `/` 菜单，仅供 AI 内部使用 |
| `context` | 否 | `fork` 时在隔离上下文执行 |
| `agent` | 否 | 指定子 Agent 类型(仅 `context: fork` 时有效) |

### 5.3 SKILL.md 正文

正文是 Markdown 格式的技能定义，推荐结构：

1. **功能说明** — 这个技能做什么
2. **工作流** — 分步骤描述执行过程
3. **可用工具/脚本** — 列出调用方式和参数
4. **输出格式** — 期望的输出结构
5. **注意事项** — 边界情况和约束

### 5.4 动态参数

- `$ARGUMENTS` — 用户输入的参数，在 shell 命令执行前替换
- `@file` — 文件引用，在 shell 命令执行后处理

### 5.5 内联 Shell 命令

```markdown
### 当前状态
!`git status --short`

### 最近提交
!`git log --oneline -5`
```

执行管线：`$ARGUMENTS` 替换 → `!`command`` 执行 → `@file` 引用处理

### 5.6 命名空间

安装后技能以 `/plugin-name:skill-name` 格式注册。如 `equity-research` 插件中的 `morning-note` 技能注册为 `/equity-research:morning-note`。

### 5.7 示例

**简单技能**：

```markdown
---
name: morning-note
description: Draft concise morning meeting notes summarizing overnight developments. Triggers on "morning note", "morning meeting", "daily note".
---

# Morning Note

## Workflow
1. Scan for overnight developments across coverage universe
2. Format into 2-minute readable morning note
3. Highlight top call and key events today
```

**带脚本的技能**：

```markdown
---
name: westock
description: |
  股票数据查询与条件选股工具集。
  触发词：查行情、看K线、查财报、资金流向、选股、筛选
---

# WeStock

## 调用方式
- westock-data: `node scripts/data-index.js <命令> <参数>`
- westock-tool: `node scripts/tool-index.js <命令> <参数>`
```

### 5.8 Skills 数量与归并

单个 plugin 的 skills 数量过多会增加模型路由负担、降低触发精度。建议控制在 **5 个以内**。

- 超过 5 个 skills 时，必须向用户提示风险，并主动询问是否归并
- 归并方式：功能相近或调用方式相同的 skills 合并为一个（如 westock-data 和 westock-tool 归并为 westock）
- 归并后的 skill 通过子工具/子命令区分功能，在一个 SKILL.md 中统一描述

---

## 六、bin 目录

`bin/` 放可执行文件（脚本、编译后的二进制等）。插件启用后，`bin/` 目录下的文件会被加入 Bash 工具的 PATH，可在 Agent 和 Skill 中直接调用。

适用场景：CLI 工具、数据处理脚本、编译后的二进制工具等。

与 skill 内 `scripts/` 的区别：`bin/` 是全局可用的可执行文件；`scripts/` 是某个 skill 内部的辅助脚本，通常由该 skill 的 SKILL.md 指定调用方式。

---

## 七、.mcp.json

仅在需要外部 MCP 服务集成时使用。放在插件根目录，格式为 JSON 配置文件。大多数专家不需要。

---

## 八、settings.json

仅 Team 型必须。指定主理人 Agent：

```json
{"agent": "{主理人 agent name}"}
```

值必须与 plugin.json 的 `agentName` 和主理人定义文件的 `name` 一致。

---

## 九、命名规范（花名）

本章花名规范适用于：
- **Agent 型（单专家）** 的 `displayName.zh` 字段
- **Team 型（专家团）** 成员的 `displayName.zh` 字段

即：所有面向用户展示的中文名字，统一使用谐音花名风格。

### 9.1 谐音花名风格

花名读起来是正常中文姓名，谐音或拆字暗含职能相关的巧思。

| 规则 | 说明 |
|------|------|
| 建议三个字 | 姓+名，建议三个字，两个字也可接受 |
| 先是正常人名 | 姓+名结构，不解释也能当名字用 |
| 暗含职能巧思 | 谐音、拆字、典故均可，但不刻意 |
| 不与 profession 重复 | displayName 是"谁"，profession 是"做什么"，两者互补 |
| 中英文都自然 | 中文用花名，英文用拼音姓氏 |

**示例**（软件开发团队）：

| profession | displayName(zh) | 巧思 | displayName(en) |
|-----------|----------|------|----------|
| 交付总监 | 齐活林 | 齐活了(交付完成) | Qi |
| 产品经理 | 许清楚 | 需求要说清楚 | Xu |
| 架构师 | 高见远 | 高见(架构视野) | Gao |
| 项目经理 | 毕达成 | 必达(交付必达) | Bi |
| 工程师 | 寇豆码 | code(代码) | Kou |
| QA工程师 | 严过关 | 严格过关 | Yan |

**禁止**：
- 叠字谐音（领码码、需求求、蓝图图）
- 一个字的 displayName 或纯职能词（策略、组织、入职）
- 和 profession 重复（架构师叫"架构师"）
- 无意义随机名（张三、John Doe）
- 英文 displayName 用 Agent ID（industry-strategist）
- 读起来是短语而非人名（裁定方、成交易、严控险）

### 9.2 主理人(lead)的 profession

主理人的 `profession` 不能用通用 title（团长、主理人、Team Lead），应体现该团队的调度风格和业务定位。

| 原则 | 说明 |
|------|------|
| 体现团队业务 | profession 一眼看出这个团队做什么 |
| 不用通用 title | "团长""主理人"是系统概念(role=lead)，不该占 profession |
| 不与 displayName 重复 | displayName 是"谁"，profession 是"做什么" |

**示例**：

| 专家团 | 主理人 displayName | profession(zh) | profession(en) |
|--------|-----------|---------------|----------------|
| 软件开发团队 | 齐活林 | 交付总监 | Delivery Director |
| 交易分析团队 | 何执舟 | 首席策略官 | Chief Strategist |
| 营销战役团队 | 营销总监 | 增长操盘手 | Growth Operator |
| 销售作战团队 | 销售总监 | 赢单顾问 | Win Advisor |
| 深度研究团队 | 顾全之 | 研究主编 | Research Editor |
| 产品战略团队 | 方向明 | 产品舵手 | Product Helmsman |

---

## 十、头像规范

| 项目 | 要求 |
|------|------|
| 格式 | PNG 或 JPG |
| 尺寸 | 512×512 px |
| 大小 | 单张不超过 500KB |
| 风格 | 统一漫画/插画风格 |
| 路径 | 包内本地文件，不支持 URL |

### plugin 内部路径（plugin.json 引用）

- agent 型：`avatars/expert.png`
- team 型：`avatars/team.png` + `avatars/{member}.png`
- plugin 型(纯技能包)：头像可选

### 审查范围

本章节只检查 `plugin.json` 的 `avatar` 字段及 `members[].avatar` 是否指向专家包内实际存在的头像文件。


---

## 十一、行业分类 (categoryId)

专家包 `plugin.json` 的 `categoryId` 统一使用下列 **13 个** 分类之一。

| ID | 分类（中文 / 英文） | 典型范围 |
|----|---------------------|----------|
| `01-ProductDesign` | 产品设计 / Product Design | 产品经理、UI/UX 设计师、交互设计师、用户研究员、产品战略 |
| `02-Engineering` | 技术工程 / Engineering | 前端、后端、全栈、移动端、DevOps、安全、云计算、工程保障 |
| `03-GameSpatial` | 游戏空间 / Game & Spatial | 游戏设计、Unity/Unreal/Godot/Roblox、XR、空间计算 |
| `04-DataAI` | 数据智能 / Data & AI | 数据分析、数据工程、AI/ML 工程师、BI、LLM、深度研究 |
| `05-MarketingGrowth` | 营销增长 / Marketing Growth | SEO/SEM、付费媒体、电商、社媒、私域、营销战役 |
| `06-ContentCreative` | 内容创作 / Content Creative | 文案策划、短视频、自媒体、播客、PPT、视频生成 |
| `07-SalesCommerce` | 销售商务 / Sales Commerce | 销售策略、商务拓展、方案撰写、客户管理、销售作战 |
| `08-FinanceInvestment` | 金融投资 / Finance Investment | 股票分析、股权研究、投行、私募、财富管理、交易策略 |
| `09-OperationsHR` | 运营人力 / Operations HR | 产品运营、客户成功、社区运营、招聘、HR 运营、组织发展 |
| `10-ProjectQuality` | 项目质量 / Project Quality | 项目管理、敏捷教练、QA、测试、文档、流程优化 |
| `11-SecurityCompliance` | 法务安全 / Security Compliance | 法律合规、合同审查、信息安全、隐私保护、区块链安全 |
| `12-IndustryConsultant` | 行业顾问 / Industry Consultant | 创业辅导、医疗健康、公共事业、公益、垂直领域咨询 |
| `13-TencentZone` | 腾讯专区 / Tencent Zone | 腾讯云、微信小程序、企业微信、腾讯游戏等腾讯技术栈专家 |

> **规则**：
> - 任何专家/插件的 `categoryId` / `category` 必须使用上表中的 13 个值之一
> - **不使用 `00-ExpertTeam`**：团队型专家按其业务领域归类（如 trading-agent → `08-FinanceInvestment`、engineering-assurance-team → `02-Engineering`）


---

## 十二、专家包审查范围

本规范副本只覆盖专家包目录本体，审查对象包括 `plugin.json`、`agents/`、`skills/`、`avatars/`、`settings.json`、`README.md`、`bin/`、`.mcp.json` 等包内文件。

审查报告不得要求修改专家包目录之外的文件。


---

## 十三、一致性约束(检查清单)

1. plugin.json `agentName` = Agent 定义文件 `name` = 文件名(不含 .md)，**必须有业务语义**，不能使用 `team-lead` 等通用名
2. plugin.json `teamInfo.memberAgents[]` 中的 ID = 对应 `members[].id` = 对应定义文件名
3. plugin.json `avatar` 路径必须指向实际存在的文件
4. settings.json `agent` = plugin.json `agentName`
5. plugin.json `skills[]` 路径下必须存在对应的 `SKILL.md`
6. **禁止在 Agent frontmatter 中声明 `tools` 字段**，工具权限由系统统一分配
7. 任何专家包内容更新（agents/skills/plugin.json/头像等）必须保持包内引用路径和字段一致

---

## 十四、不使用的 Plugin 能力

以下是 CodeBuddy CLI plugin 体系支持但本项目专家包**不使用**的能力：

| 能力 | 位置 | 不使用原因 |
|------|------|-----------|
| Slash Commands | `commands/*.md` | 专家通过对话交互，不需要斜杠命令 |
| Hooks | `hooks/hooks.json` | 专家不需要事件驱动自动化 |
| LSP Server | `.lsp.json` | 专家不提供语言服务 |

---

## 十五、专家类型判断(转化参考)

| 源项目特征 | 推荐 expertType |
|-----------|----------------|
| 多角色协作 + SOP 工作流 | `team` |
| 单角色 + agent prompt | `agent` |
| 仅有 skills/工具集、无角色定义 | `plugin` |
| 框架/SDK（无业务场景） | 不适合转化 |

---

## 十六、外部提交的专家包审查原则

当审查的专家包是**外部提交**的（已经是专家风格的包，而非从非专家项目转化而来），只需关注**结构性和功能性问题**（目录结构、plugin.json 字段、工具调用语法等），**不要改动**作者自己的命名风格、角色设定、人设设计等内容创意层面的东西。

具体来说：
- 第九章的命名规范（谐音花名等）仅适用于**我们自己从零构建或从非专家项目转化**的场景
- 外部提交者已有自己的命名体系（如历史人物名、行业术语名等），尊重原作者设计，不强制套用谐音花名
- 如果不确定一个包是"外部提交"还是"需要转化"，先询问用户

---

## 十七、交付前 Checklist

每个专家包提交前，按此清单逐项检查。

### 一致性（硬性，不通过则不可交付）

- [ ] plugin.json `agentName` = Agent 定义文件 `name` = 文件名(不含 .md)，且有业务语义（非 `team-lead` 等通用名）
- [ ] plugin.json `teamInfo.memberAgents[]` 中的 ID = 对应 `members[].id` = 对应定义文件名
- [ ] plugin.json `avatar` 路径指向实际存在的文件
- [ ] settings.json `agent` = plugin.json `agentName`
- [ ] plugin.json `skills[]` 路径下存在对应的 `SKILL.md`
- [ ] Agent frontmatter 中**不包含 `tools` 字段**（工具权限由系统统一分配）
- [ ] agents/、skills/、avatars/ 在插件根目录，不在 `.codebuddy-plugin/` 里
- [ ] `agents/` 下只有 agent 定义文件（带 frontmatter 的 .md），策略文档、规则文档、模板文档等应放在 `references/`
- [ ] `.codebuddy-plugin/` 下只有 `plugin.json`，没有 agents、skills、avatars、hooks、commands、`.lsp.json`

- [ ] 所有 JSON 文件可正常解析，无语法错误

### Team 型专项

- [ ] 主理人 prompt 中有明确的 TeamCreate + Agent(name=成员名, team_name=...) 调用流程和示例
- [ ] 主理人 prompt 中明确必须先 TeamCreate 创建团队，再 spawn 成员
- [ ] 主理人 prompt 中有"禁止跳过 TeamCreate 直接 fork sub-agent"的约束
- [ ] 主理人 prompt 中有"禁止自行模拟或代写成员发言"的铁律

- [ ] 所有 agent（含主理人和团队成员）frontmatter 中**不包含 `tools` 字段**
- [ ] 每个成员 agent 能独立回答某类用户问题（见 4.5.2）
- [ ] 成员 prompt 中有擅长领域、分析框架、输出模板（见 4.5.3）
- [ ] 成员 prompt 中明确要求通过 SendMessage 将分析结果回传给主理人
- [ ] 术语统一：使用"主理人"/"团队成员"，不使用"团长"/"团员"/"高手"


### 术语与规范

- [ ] 目录名使用 `.codebuddy-plugin/`（非 `.workbuddy-plugin/`）
- [ ] 无已废弃字段（如 `expertCount`）
- [ ] Agent name 有业务语义，多插件同时启用时不会 name 冲突
- [ ] 头像格式 PNG/JPG，尺寸 512×512px，单张 <500KB

### 运行时验效（建议上线前实测）

- [ ] 主理人收到问题后，先 TeamCreate 创建团队，再通过 Agent(name=成员名, team_name=...) spawn 正式 teammate
- [ ] 团队成员各自独立查询数据并通过 SendMessage 回传分析，非主理人代查代写
- [ ] 讨论结束后主理人通过 SendMessage shutdown_request 关闭团队成员
- [ ] Skill 中引用的工具/脚本可正常调用（如 westock 的 `node scripts/data-index.js`）
- [ ] 不使用 `find /projects` 等硬编码路径探测，而是通过 skill 上下文引用

---

## 十八、金融类专家团合规要求

适用范围：涉及股票/基金/投资分析的 Team 型专家团(当前为 stock-partner-team、trading-agent)。equity-research、financial-analysis 等纯工具集不在此范围。

### 17.1 外露文案规范

| 字段 | 要求 |
|------|------|
| `defaultInitPrompt` | 不含"能不能买""该买吗""推荐"等决策类措辞，改为信息梳理/分析类表述 |
| `displayDescription` | 不暗示提供投资建议/买卖信号/操作路线图，改为"多角度分析参考" |
| `description` | 不含"投资建议""BUY/SELL/HOLD 建议"等措辞 |

### 17.2 免责声明

每次输出末尾必须包含统一免责声明，措辞需涵盖以下要素：

1. **AI 生成**：明确标注内容由 AI 生成
2. **基于公开信息**：标注信息来源为公开信息
3. **不构成投资建议**：明确不构成投资建议
4. **不构成个股推荐**：明确不构成个股推荐

统一模板：

> ⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。

### 17.3 数据来源披露

引用行情、财务、资金等数据时，标注数据来源(如 westock-data quote、neodata-financial-search、WebSearch 搜索词等)，让用户可自行验证。

### 17.4 用户协议弹窗(产品端)

用户首次调取金融类专家团时，需通过弹窗提示 AI 生成声明，用户勾选同意后方可使用。此项由产品端实现，专家包无需改动。

### 17.5 交付 Checklist 补充

金融类专家团在十六 Checklist 基础上，额外检查：

- [ ] `defaultInitPrompt` 无决策类措辞("能不能买""该买吗""推荐"等)
- [ ] `displayDescription`、`description` 无投资建议暗示
- [ ] 所有 agent prompt 末尾免责声明已更新为统一模板(含 AI 生成、公开信息、不构成投资建议、不构成个股推荐四要素)
- [ ] 主理人 prompt 铁律中包含数据来源披露要求
