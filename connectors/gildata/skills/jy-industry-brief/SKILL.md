---
name: jy-industry-brief
description: 基于恒生聚源 MCP 聚源金融数据库生成指定行业的 24 小时速报（默认 Markdown 格式，支持 HTML 输出）。覆盖备选简读素材、重要新闻信息、行业企业动态、投融资事件四大核心模块，所有信息可溯源、带原始发布时间戳。⚠️ 本技能仅提供资讯信息展示，不构成任何投资建议或投资参考。使用场景：当用户有以下意图时触发——生成指定行业的速报，快速了解某行业最新动态，如"生成新能源汽车行业速报"、"人工智能行业今天有什么新闻"、"帮我看看半导体行业的最新动态"、"医药行业 24 小时速报"等。示例问题："生成半导体行业速报"、"新能源行业最新动态"
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
version: 1.0.0
---

# 行业速报（jy-industry-brief）

基于恒生聚源金融数据库 (MCP) 为指定行业生成 24 小时速报，覆盖备选简读素材、重要新闻信息、行业企业动态、投融资事件四大核心模块。

**声明**：本 Skill 仅提供客观信息整理，不构成任何投资建议。市场有风险，决策需谨慎。

---

## ⚠️ 执行前必读（强制执行）

**执行本技能前，必须完整读取以下所有文件，缺一不可：**

### 1. 主技能文档（必须读取）
- [x] `SKILL.md` — 本技能主文档（你正在阅读的文件）

### 2. 参考文档（全部必须读取）
- [x] `references/news-validation.md` — 新闻核验清单与时效性验证
- [x] `references/investment-validation.md` — 投融资事件核验规则
- [x] `references/report-template.md` — 完整报告模板（格式要求、数量要求、数据源说明）
- [x] `references/html-template.md` — HTML 输出模板（如用户要求 HTML 输出）
- [x] `references/setup-guide.md` — MCP 配置指南

### 3. 执行检查清单（每次执行必须逐项核对）

#### 阶段一：准备阶段（数据收集前）
- [ ] 已读取主技能文档 SKILL.md
- [ ] 已读取 `references/news-validation.md`
- [ ] 已读取 `references/investment-validation.md`
- [ ] 已读取 `references/report-template.md`
- [ ] 已读取 `references/html-template.md`（如需要 HTML 输出）
- [ ] 已读取 `references/setup-guide.md`（如 MCP 配置有问题）
- [ ] 已确认 MCP 服务已配置（`mcporter list` 显示 2 healthy）
- [ ] 已理解四大模块的数据源分配（见 report-template.md）

#### 阶段二：数据收集阶段
- [ ] 已调用 `IndustryNewsFlash` 获取行业快讯（核心数据源，**必需**）
- [ ] 数据不足时已调用 `NewsPublicOpinionList` 补充（聚合多家公司）
- [ ] 已调用 `FinancialResearchReport` 获取备选简读素材
- [ ] 已调用 `CorporateResearchViewpoints` 获取研报观点（⚠️ 在 jy-financedata-api 中）

#### 阶段三：数据核验阶段
- [ ] 重要新闻信息均为 24 小时内发布
- [ ] 行业企业动态均为 24 小时内发布
- [ ] 投融资事件均为 24 小时内发布（或明确标注时间范围）
- [ ] 备选简读素材在 7 天内（可放宽）
- [ ] 重要新闻信息≥3 条
- [ ] 行业企业动态≥5 条
- [ ] 投融资事件已按规则核验（排除奖励、购买产品、减持等无效情况）
- [ ] 无重复新闻（同一事件只保留最权威来源）
- [ ] 各模块按发布日期降序排序（最新在前）

#### 阶段四：报告生成阶段
- [ ] 标题格式正确（`## YYYY 年 MM 月 DD 日{行业名称} 行业速报`）
- [ ] 备选简读素材使用表格格式
- [ ] 重要新闻信息使用序号列表（①②③...）
- [ ] 行业企业动态使用序号列表（①②③...）
- [ ] 投融资事件使用表格格式（无事件写"无"）
- [ ] 每条信息都标注了来源和原始发布日期
- [ ] 来源格式正确（单条来源后不加逗号）
- [ ] 已包含免责声明（必备）
- [ ] 已包含溯源信息表格（必备）

**未按上述要求执行 = 技能执行失败！**

---

---

## 功能范围

1. **生成行业速报**：为指定行业生成 24 小时速报（默认 Markdown）
2. **HTML/PDF 输出**：用户明确要求时可输出 HTML 或 PDF 格式
3. **数据溯源**：所有信息标注数据来源和原始发布时间
4. **多行业覆盖**：支持各行业领域速报生成

**触发场景**：
- "生成新能源汽车行业速报"
- "人工智能行业今天有什么新闻"
- "帮我看看半导体行业的最新动态"
- "医药行业 24 小时速报"

---

## 查询建议

**查询要素**：行业名称、时间范围（默认 24 小时）、输出格式（默认 Markdown）

**标准写法**：
```
生成 {行业名称} 行业速报
生成 {行业名称} 行业速报，渲染成 HTML
生成 {行业名称} 行业速报，返回 PDF
```

---

## 环境检查与配置

**每次使用前必须检查 mcporter 安装和 MCP 服务配置！**

### 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装**：
```bash
npm install -g mcporter
mcporter --version
```

### 步骤 2：检查 MCP 服务配置

```bash
mcporter list
```

**预期输出**（必须包含）：
- jy-financedata-tool
- jy-financedata-api

**如未配置**，需获取 JY_API_KEY 并配置：

#### 获取 JY_API_KEY

向恒生聚源申请（首次配置需提供，配置一次即可）。

**申请邮箱**：datamap@gildata.com

**邮件标题**：数据地图 KEY 申请 -XX 公司 - 申请人姓名

**正文模板**：
- 姓名、手机号、公司/单位全称、所属部门、岗位
- MCP_KEY 申请用途、Skill 申请列表
- 是否需要 Skill 安装包：（是，邮件提供/否，自行下载）

#### 配置 MCP 服务

```json
{
    "mcpServers": {
        "jy-financedata-tool": {
            "type": "streamableHttp",
            "url": "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=${GILDATA_TOKEN}",
            "timeout": 180000
        },
        "jy-financedata-api": {
            "type": "streamableHttp",
            "url": "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=${GILDATA_TOKEN}",
            "timeout": 180000
        }
    }
}
```

#### 使用方式

```bash
# 所有服务工具的入参均为 query
mcporter call jy-financedata-api.StockBelongIndustry query="电子行业 代表性上市公司"
```

### 步骤 3：在 OpenClaw 中启用 mcporter

**编辑 openclaw.json**（`C:\Users\你的用户名\.openclaw\openclaw.json`）：

```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": {
          "MCPORTER_CONFIG": "C:\\Users\\你的用户名\\config\\mcporter.json"
        }
      }
    }
  }
}
```

**重启 OpenClaw**：
```bash
openclaw gateway restart
```

---

## 核心工作流程（执行清单）

### ✅ 步骤 0：读取全部参考文档（强制执行）

**在开始任何操作前，必须完整读取：**
- [ ] `references/news-validation.md` — 理解新闻核验规则和时效性要求
- [ ] `references/investment-validation.md` — 理解投融资事件判定规则
- [ ] `references/report-template.md` — 掌握报告格式、数量要求、数据源分配
- [ ] `references/html-template.md` — 如用户要求 HTML 输出则参考
- [ ] `references/setup-guide.md` — 如 MCP 配置有问题则参考

**未读取全部参考文档 = 禁止执行后续步骤！**

### ✅ 步骤 1：识别行业名称

从用户输入提取行业名称（如"新能源汽车"、"人工智能"、"半导体"等）。

**如行业名称模糊**：向用户确认具体行业或使用标准行业分类名称（参考申万行业分类）。

### ✅ 步骤 2：MCP 连接检查

```bash
mcporter list
```

**预期输出**：
```
jy-financedata-tool (5 tools)
jy-financedata-api (252+ tools)
2 healthy
```

- ✅ 显示两个服务已配置 → 继续
- ❌ 服务未配置 → 提示用户先完成配置（见环境检查与配置）

### ✅ 步骤 3：四大模块数据收集

**核心数据源优先级**：
1. `IndustryNewsFlash` (jy-financedata-api) - 覆盖重要新闻、企业动态、投融资事件
2. `NewsPublicOpinionList` (jy-financedata-api) - 补充公司层面信息
3. `FinancialResearchReport` (jy-financedata-tool) - 备选简读素材
4. `CorporateResearchViewpoints` (jy-financedata-api) - 研报观点

| 模块 | 核心内容 | MCP 工具 | 所属服务 |
|------|----------|----------|----------|
| 备选简读素材 | 技术分析、科普知识、深度报告 | `FinancialResearchReport`、`CorporateResearchViewpoints` | jy-financedata-tool、jy-financedata-api |
| 重要新闻信息 | 宏观政策、行业整体动态 | `IndustryNewsFlash` | jy-financedata-api |
| 行业企业动态 | 产品发布、战略合作、技术进展 | `IndustryNewsFlash`、`NewsPublicOpinionList` | jy-financedata-api |
| 投融资事件 | 投资、融资、收购、入股 | `IndustryNewsFlash`、`NewsInfoList` | jy-financedata-api |

**并发调用**（可提速）：
```bash
mcporter call jy-financedata-api.IndustryNewsFlash query="行业名称" &
mcporter call jy-financedata-tool.FinancialResearchReport query="行业名称 行业分析" &
mcporter call jy-financedata-api.CorporateResearchViewpoints query="行业名称" &
wait
```

**数据源优先级**：优先 MCP，仅当 MCP 完全无数据时启用 web_search 兜底。

### ✅ 步骤 4：数据整理与核验

#### 时效性核验
| 模块 | 时间要求 |
|------|----------|
| 重要新闻信息 | 24 小时内 |
| 行业企业动态 | 24 小时内 |
| 投融资事件 | 24 小时内 |
| 备选简读素材 | 可放宽至 7 天 |

- 标注原始发布时间（非技能调用时间）
- 按发布日期降序排序（最新在前）

#### 投融资事件核验
**有效关键词**：获投、融资、收购、入股、投资、加投、参投、股权、增资等

**无效情况**（排除）：
- 奖励、补贴、奖金
- 购买产品、设备、服务
- 减持股权、出售股权
- 银行贷款、债权融资（除非明确为股权融资）
- 单纯业务合作、战略合作（无股权/资金注入）
- 慈善捐赠、公益捐赠

**投资方与被投资方判定**：
- "A 受让 B 持有的 C 的股权" → 被投资方=C，投资方=A
- "A、B 共同投资 C" → 被投资方=C，投资方=A、B
- "A 领投，B、C 跟投 D 公司" → 被投资方=D，投资方=A(领投)、B、C

### ✅ 步骤 5：生成行业速报

**默认输出**：Markdown 格式

**报告结构**：
1. 报告标题（日期 + 行业名称）
2. 备选简读素材（表格，带发布时间，降序）
3. 重要新闻信息（序号列表，≥3 条，带发布时间，降序）
4. 行业企业动态（序号列表，≥5 条，带发布时间，降序）
5. 投融资事件（表格或"无"，带发布时间，降序）
6. 免责声明（必备）
7. 溯源信息（必备）

---

## 快速开始

### 工具调用命令

**注意**：所有服务工具的入参均为 `query`。

```bash
# 行业快讯（核心）
mcporter call jy-financedata-api.IndustryNewsFlash query="太空光伏"

# 新闻舆情
mcporter call jy-financedata-api.NewsPublicOpinionList query="688000"

# 研究报告
mcporter call jy-financedata-tool.FinancialResearchReport query="太空光伏 行业分析"

# 自然语言查询
mcporter call jy-financedata-tool.FinQuery query="太空光伏行业 最新政策 市场规模"

# 新闻资讯
mcporter call jy-financedata-api.NewsInfoList query="融资 投资"

# 研报观点
mcporter call jy-financedata-api.CorporateResearchViewpoints query="太空光伏"
```

### 行业识别

```bash
# 查询代表性公司
mcporter call jy-financedata-tool.FinQuery query="{行业名称} 代表性上市公司 龙头股"
```

### 多公司数据聚合

```bash
# 示例：光子芯片行业
mcporter call jy-financedata-api.NewsPublicOpinionList query="688000"
mcporter call jy-financedata-api.NewsPublicOpinionList query="688001"
mcporter call jy-financedata-api.NewsPublicOpinionList query="688002"
```

合并去重后按时间排序。

### Web Search 兜底

**启用条件**：MCP 连接正常但完全无相关行业数据（行业太新）。

```bash
web_search "{行业名称} 最新动态 2026"
web_search "{行业名称} 融资 投资 收购 2026"
```

标注来源为"网络公开信息"。

---

## 输出格式要求

### ⚠️ 格式合规性检查（生成报告前必须逐项核对）

**严格遵循 `references/report-template.md` 中的模板要求：**

| 检查项 | 要求 | 示例 |
|--------|------|------|
| 标题格式 | `## YYYY 年 MM 月 DD 日{行业名称} 行业速报` | `## 2026 年 03 月 30 日新能源汽车行业速报` |
| 序号格式 | 重要新闻和企业动态使用 ①②③... | ① ② ③ ④ ⑤ |
| 表格格式 | 备选简读素材和投融资事件必须用表格 | `\| 序号 \| 资讯标题 \|...` |
| 来源标注 | 单条来源后**不加逗号** | `（新华社，2026-03-30）` |
| 多条来源 | 用顿号分隔 | `（新华社、人民日报，2026-03-30）` |
| 排序要求 | 各模块按发布日期**降序**排序 | 最新在前 |
| 数量要求 | 重要新闻≥3 条，企业动态≥5 条 | - |
| 免责声明 | **必须包含**，放在报告末尾 | `**免责声明**：...` |
| 溯源信息 | **必须包含**，放在免责声明之后 | 表格形式 |

**不符合上述要求 = 输出无效！**

### 报告标题
```
## 2026 年 03 月 30 日新能源汽车行业速报
```

### 1. 备选简读素材（表格，降序）
```
### 1. 备选简读素材：
| 序号 | 资讯标题 | 数据来源 | 发布时间 |
| 1 | 标题 1 | 来源 1 | 2026-03-30 |
| 2 | 标题 2 | 来源 2 | 2026-03-29 |
```

### 2. 重要新闻信息（序号列表，≥3 条，降序）
```
### 2. 重要新闻信息：
① 宏观政策新闻 1（来源，2026-03-30）
② 行业动态新闻 2（来源，2026-03-30）
③ 其他新闻 3（来源，2026-03-29）
```

### 3. 行业企业动态（序号列表，≥5 条，降序）
```
### 3. 行业企业动态：
① 公司产品发布 1（来源，2026-03-30）
② 战略合作 2（来源，2026-03-29）
...
```

### 4. 投融资事件

**有事件时**（表格，降序）：
```
### 4. 投融资事件：
| 被投资方 | 投资方 | 投融资事件 | 发布时间 |
| 公司 A | 机构 B | C 轮融资 | 2026-03-30 |
```

**无事件时**：
```
### 4. 投融资事件：
无
```

### 5. 免责声明（必备）
```
---
**免责声明**：本速报仅提供信息整理，不构成任何投资建议。市场有风险，决策需谨慎。
```

### 6. 溯源信息（必备）
```
---
## 溯源信息

| 数据类型 | 数据来源 | 原始发布日期 |
|---------|---------|-------------|
| 行业快讯 | jy-financedata-api.IndustryNewsFlash | 2026-03-30 |
| 新闻舆情 | jy-financedata-api.NewsPublicOpinionList | 2026-03-30 |
| 研究报告 | jy-financedata-tool.FinancialResearchReport | 2026-03-29 |
| 研报观点 | jy-financedata-api.CorporateResearchViewpoints | 2026-03-30 |

**数据核查**：已通过内部一致性核查
```

### HTML 输出

用户要求"渲染成 HTML"时，参考 [references/html-template.md](references/html-template.md)。

---

## 资源清单

```
skills/jy-industry-brief-V1.0/
├── SKILL.md                          # 本技能主文档
├── references/
│   ├── news-validation.md            # 新闻核验清单
│   ├── investment-validation.md      # 投融资核验规则
│   ├── report-template.md            # 完整报告模板
│   ├── setup-guide.md                # MCP 配置指南
│   └── html-template.md              # HTML 输出模板
└── scripts/
    └── md2pdf.py                     # Markdown 转 PDF 脚本
```

---

## 限制

### 执行限制（强制要求）
- **执行前必须完整读取主技能和全部 5 个 reference 文件**
- **必须按执行检查清单逐项核对**
- **必须严格遵循 report-template.md 中的格式要求**

### 数据源限制
- 必须连接 MCP 聚源金融数据库
- PDF 输出需安装 Python + reportlab
- web_search 仅作兜底，不优先使用

### 内容要求
- 新闻 24 小时内（备选简读素材可 7 天）
- 备选简读素材、投融资事件用表格（无事件写"无"）
- 重要新闻、企业动态用序号列表（①②③...）
- 所有信息标注来源和原始发布日期
- 严格按用户指定行业检索
- 单条来源后不加逗号
- 各模块按发布日期降序排序

### 工具调用规范
- 所有服务工具入参均为 `query`
- 使用 `mcporter call` 命令调用
- 确保 jy-financedata-tool 和 jy-financedata-api 已配置

### 常见问题与解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| mcporter list 显示服务未配置 | MCP 服务未正确配置 | 按步骤 2 重新配置服务，检查 JY_API_KEY 是否有效 |
| 调用工具返回空数据 | 行业 24 小时内新闻较少或 MCP 未覆盖 | 聚合多家相关公司数据，使用龙头股票代码查询，或放宽时间范围 |
| 投融资事件不足 | 该行业 24 小时内投融资事件较少 | 24 小时内无事件直接写"无"，不要编造 |
| JY_API_KEY 失效 | KEY 过期或被撤销 | 重新向恒生聚源申请（datamap@gildata.com） |
| CorporateResearchViewpoints 调用失败 | 错误调用 jy-financedata-tool.CorporateResearchViewpoints | 改用 jy-financedata-api.CorporateResearchViewpoints |
| 行业名称无法识别 | 行业名称太宽泛或太具体 | 使用标准行业分类名称（申万行业分类），或提供行业龙头公司名称 |
| PDF 输出失败 | 未安装 Python + reportlab | 安装依赖：`pip install reportlab`，或改用 HTML 输出 |

---

## 版本更新说明 (V1.0)

### V1.0 优化内容

**修正内容**：
- `CorporateResearchViewpoints` 从 `jy-financedata-tool` 修正为 `jy-financedata-api`
- 优化工作流程为可执行清单格式（✅ 步骤 0-5）
- 强化 MCP 服务工具分配的说明（添加醒目提示和常见错误）
- 完善常见问题表格（添加更多场景和解决方案）
- 优化格式合规性检查表格（添加示例列）

**依据**：
- 根据 MEMORY.md 记录，jy-financedata-tool 仅包含 5 个工具（FinQuery、MacroIndustryData、FinancialResearchReport、FundMultipleFactorFilter、StockMultipleFactorFilter），其他所有工具均在 jy-financedata-api 中。
- 根据用户要求：调用该技能时必须完整读取主 skill 和相关的 reference 文档，严格按照要求产出。

---

**版本**：v1.0 | **创建**：2026-03-31 | **修正**：CorporateResearchViewpoints 服务分配 | **优化**：执行清单化、服务分配强化、错误处理完善
