---
name: jy-fund-consistency-analysis
description: 基于聚源金融数据库的基金经理观点与持仓一致性分析工具。分析基金经理在定期报告中表达的投资观点与其管理基金实际持仓的一致性程度，生成标准化分析报告。覆盖观点提取、持仓分析、多维度一致性评分（行业配置、投资风格、选股逻辑、风险控制）、报告生成等核心功能。所有数据来自 MCP API，确保真实可溯源。使用场景：当用户需要分析某基金经理的言行一致性、评估基金经理可信度、查看基金经理观点与持仓匹配度、生成一致性检验报告时触发。英文：Fund Manager Consistency Analysis Tool based on GILData Financial Database. Analyzes the consistency between fund managers' investment views expressed in periodic reports and the actual holdings of funds they manage, generating standardized analysis reports. Covers core functions including viewpoint extraction, holdings analysis, multi-dimensional consistency scoring (industry allocation, investment style, stock selection logic, risk control), and report generation. All data comes from MCP API, ensuring authenticity and traceability. Use case: Triggered when users need to analyze a fund manager's speech-action consistency, evaluate fund manager credibility, check the match between fund manager views and holdings, or generate consistency inspection reports.
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
---

# 基金经理观点持仓一致性分析 (JY Fund Consistency Analysis)

基于聚源金融数据库的专业基金经理"言行一致性"分析工具，通过 MCP 服务获取真实数据，按照标准化模板输出高质量的基金经理观点与持仓一致性检验分析报告。

**核心理念**: 基于真实数据，客观分析，不编造任何信息。

---

## 功能范围

本 Skill 支持以下功能：

- ✅ **观点提取**: 从基金定期报告中提取基金经理核心观点（市场展望、投资策略、重点关注领域）
- ✅ **持仓分析**: 获取基金重仓股及行业配置数据
- ✅ **一致性评分**: 多维度量化分析（行业配置 35%、投资风格 25%、选股逻辑 25%、风险控制 15%）
- ✅ **报告生成**: 生成专业 Markdown 格式分析报告（支持 HTML/PDF 导出）
- ✅ **基金全覆盖**: 对基金经理管理的每一只基金分别进行一致性检验
- ✅ **数据验证**: 确保所有数据来自 MCP API，不编造任何信息
- ✅ **智能日期匹配**: 自动匹配最接近的标准报告期

---

## 查询建议

### 查询需要具备的要素

1. **基金经理姓名**（必需）：完整的基金经理姓名，如"张坤"、"葛兰"
2. **查询日期**（必需）：日期格式为 YYYY-MM-DD，如"2024-12-31"，系统会自动匹配到最接近的标准报告期

### 查询写法

```
分析 [基金经理姓名] 在 [日期] 的观点与持仓一致性
[基金经理姓名] [日期] 一致性检验
查看 [基金经理姓名] 的言行一致性报告
```

---

## 查询示例

```bash
# 示例 1：分析张坤在 2024 年底的一致性
分析张坤在 2024-12-31 的观点与持仓一致性

# 示例 2：分析葛兰在 2023 年中报的一致性
葛兰 2023-06-30 一致性检验

# 示例 3：查看傅鹏博的言行一致性报告
查看傅鹏博的言行一致性报告

# 示例 4：简单查询
张坤 2024 年年报 一致性
```

---

## 环境检查与配置

**每次使用本技能前，必须先检查 mcporter 安装和 MCP 服务配置状态！**

### 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装**，按以下流程安装：

```bash
# 1. 通过 npm 全局安装
npm install -g mcporter

# 2. 验证安装
mcporter --version
```

### 步骤 2：检查 MCP 服务配置

```bash
# 列出所有已配置的 MCP 服务
mcporter list
```

**预期输出**（必须包含以下两个服务）：
- jy-financedata-tool
- jy-financedata-api

**如服务未配置**，需要获取 JY_API_KEY 并配置：

#### 2.1 获取 JY_API_KEY

向恒生聚源申请 JY_API_KEY，通过邮箱申请（首次配置需提供，配置一次即可）

**JY_API_KEY 申请路径**：
向恒生聚源官方邮箱发送邮件申请签发数据地图 JY_API_KEY，用于接口鉴权。申请通过后，恒生聚源将默认发送【工具版和接口版】KEY。

**申请邮箱**：datamap@gildata.com

**邮件标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名

**正文模板**：
- 姓名：
- 手机号：
- 公司/单位全称：
- 所属部门：
- 岗位：
- MCP_KEY 申请用途：
- Skill 申请列表：
- 是否需要 Skill 安装包：（是，邮件提供/否，自行下载）
- 其他补充说明（可选）：

另外，【Skill】包可通过 https://clawhub.ai/ 自行选择下载，若需要我们通过邮件提供【Skill】，亦可在邮件中注明。

#### 2.2 配置 MCP 服务

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

#### 2.3 验证配置

```bash
mcporter list
```

预期输出应包含：
```
- jy-financedata-tool — 聚源 - 多智能体模式（X 工具）
- jy-financedata-api — 聚源 - 全量接口模式（X 工具）
```

#### 2.4 测试调用

```bash
# 测试调用（注意：所有服务工具的入参均为 query）
mcporter call jy-financedata-api.FundManagerViewPointReport query="张坤 2024-12-31"
```

### 步骤 3：在 OpenClaw 中启用 mcporter（如未配置）

**mcporter 配置文件路径**：
- Windows: `C:\Users\你的用户名\.mcporter\mcporter.json`

**OpenClaw 配置文件路径**：
- Windows: `C:\Users\你的用户名\.openclaw\openclaw.json`

**编辑 openclaw.json**，在 skills 部分添加 mcporter 配置：

```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": {
          "MCPORTER_CONFIG": "C:\\Users\\你的用户名\\.mcporter\\mcporter.json"
        }
      }
    }
  }
}
```

**重启 OpenClaw 使配置生效**：

```bash
openclaw gateway restart
```

---

## 核心工作流程

流程中的工具调用能够并发调用尽量并发调用提速。

### 步骤 1：获取基金经理观点

1. **调用 API**: `FundManagerViewPointReport`
2. **输入参数**:
   - 查询参数：`{基金经理姓名} {查询日期}`
3. **获取并记录以下信息**：
   对于在查询日期对应报告期内，该基金经理管理下的**每一只基金**:
   - 管理基金代码
   - 管理基金简称
   - 观点报告期 (API 返回的实际报告期)
   - 投资策略和运作分析内容
   - 基金市场展望内容
4. **注意**:
   - 如果用户输入的日期不是标准的报告期末，请选择与该日期最接近的已披露报告期的观点
   - 记录下所有由该基金经理管理的、在指定报告期有观点数据的基金列表

**调用示例**：
```bash
mcporter call jy-financedata-api.FundManagerViewPointReport query="张坤 2024-12-31"
```

### 步骤 2：获取基金持股明细

1. **确定持仓报告期**:
   对于步骤 1 中获取的**每一只基金**及其对应的**观点报告期**，计算其**后一个季度**的日期作为"持仓报告期"。
   
   **规则**:
   - 观点报告期为 2023 年年报 (2023-12-31) → 持仓报告期为 2024 年一季报 (2024-03-31)
   - 观点报告期为 2023 年一季报 (2023-03-31) → 持仓报告期为 2023 年二季报 (2023-06-30)
   - 观点报告期为 2023 年中报 (2023-06-30) → 持仓报告期为 2023 年三季报 (2023-09-30)
   - 观点报告期为 2023 年三季报 (2023-09-30) → 持仓报告期为 2023 年年报 (2023-12-31)

2. **调用 API**: `ShareholdingDetailReport`
3. **输入参数**（对步骤 1 中获取的每一只基金分别调用）:
   - 查询参数：`{基金代码/基金简称} {持仓报告期}`
   - 持仓类型：重仓股票
4. **获取并记录以下信息**：
   对于每只基金，在其对应的"持仓报告期"，记录其**重仓股票**，至少包括:
   - 股票代码
   - 股票简称
   - 持仓市值
   - 占基金净值比
   - 所属行业（例如申万一级行业）

**调用示例**：
```bash
mcporter call jy-financedata-api.ShareholdingDetailReport query="000001 2024-03-31"
```

### 步骤 3：数据验证与处理

1. **验证基金代码匹配**: 确保观点数据与持仓数据来自同一只基金
2. **处理 A/C 类合并**: 同一基金的 A/C 类份额合并分析
3. **数据去重**: 去除重复的股票记录
4. **行业分类统一**: 确保行业分类标准一致

### 步骤 4：一致性分析

对每一只基金，从以下维度进行分析：

1. **行业配置匹配度** (35%):
   - 观点中提到的行业是否在持仓中体现？
   - 重点配置的行业是否与观点一致？

2. **投资风格一致性** (25%):
   - 持仓组合风格是否与观点中阐述的风格一致？
   - 成长/价值/均衡风格是否匹配？

3. **选股逻辑一致性** (25%):
   - 重仓股是否符合观点中提及的选股标准？
   - 是否买入/加仓了明确看好的标的？

4. **风险控制一致性** (15%):
   - 观点中提示的风险，在持仓中是否有规避？
   - 仓位水平是否与市场判断匹配？

### 步骤 5：生成报告

严格按照模板格式生成 Markdown 报告，确保：
- 所有数据来自 API，不编造
- 表格清晰易读
- 分析客观严谨
- 结论基于数据

---

## 快速开始

### 基础调用

**主服务（jy-financedata-api）- 推荐：**
```bash
# FundManagerViewPointReport 和 ShareholdingDetailReport 都在 jy-financedata-api 中
mcporter call jy-financedata-api.FundManagerViewPointReport query="张坤 2024-12-31"
mcporter call jy-financedata-api.ShareholdingDetailReport query="易方达蓝筹精选 2024-03-31"
```

**备用服务（jy-financedata-tool）- 部分功能：**
```bash
# jy-financedata-tool 只有 5 个工具，不支持 FundManagerViewPointReport 和 ShareholdingDetailReport
# 但可以用 FinQuery 查询部分金融数据作为备用
mcporter call jy-financedata-tool.FinQuery query="张坤 管理基金 2024 年年报"
mcporter call jy-financedata-tool.FinQuery query="基金代码 000001 重仓股 2024 年一季报"
mcporter call jy-financedata-tool.MacroIndustryData query="中国最新 GDP 增速 CPI 数据"
mcporter call jy-financedata-tool.FinancialResearchReport query="基金经理观点分析 研报"
```

### 数据获取策略

1. **优先使用 jy-financedata-api**：接口最全，支持 FundManagerViewPointReport 和 ShareholdingDetailReport
2. **备用 jy-financedata-tool**：当 api 服务不可用时，可用 FinQuery 查询部分数据
3. **所有入参统一为 query**：不要使用其他参数名

### 错误处理

```bash
# 如遇到认证错误，检查 JY_API_KEY 是否有效
mcporter list

# 如遇到超时，增加超时时间（默认 150 秒）
# 在 skill 配置中调整 timeout 参数
```

---

## 资源清单

```
jy-fund-consistency-analysis/
├── SKILL.md                          # 技能文档（本文件）
├── README.md                         # 使用说明
├── skill.config.json                 # 配置文件
├── requirements.txt                  # Python 依赖
├── analyzer_v2.py                    # 主分析程序（v2 版本）
├── generate_pdf_v2.py                # PDF 生成工具
└── consistency_reports/              # 输出目录
    ├── *.md                          # 生成的 Markdown 报告
    └── *.html                        # 生成的 HTML 文件
```

### 核心文件说明

| 文件 | 用途 |
|------|------|
| `analyzer_v2.py` | 主分析程序，执行完整的 CoT 思维链步骤 |
| `generate_pdf_v2.py` | PDF 生成工具，通过 HTML 中转避免中文乱码 |
| `skill.config.json` | 技能配置文件，包含 MCP 服务、分析维度等配置 |
| `consistency_reports/` | 输出目录，存放生成的报告文件 |

---

## 限制

### 数据源限制

1. **仅支持 MCP API 数据源**：所有数据必须来自 jy-financedata-api 或 jy-financedata-tool，严禁编造数据
2. **API 响应时间**：每次调用约 60-150 秒（网络延迟），请设置合理的超时时间
3. **数据披露延迟**：季报披露有延迟，可能需尝试多个日期

### 输出格式限制

1. **报告格式**：默认 Markdown，支持 HTML 导出，PDF 需手动打印
2. **基金数量限制**：单次分析最多处理 20 只基金
3. **重仓股数量**：每只基金分析前十大重仓股

### 注意事项

1. **报告期匹配**：自动匹配最接近的标准报告期（3/6/9/12 月末）
2. **基金代码验证**：确保观点与持仓数据来自同一只基金
3. **A/C 类合并**：同一基金的 A/C 类份额合并分析
4. **JY_API_KEY 安全**：妥善保管 API KEY，不要公开分享

---

## 一致性等级标准

| 综合评分 | 等级 | 信号灯 | 说明 |
|----------|------|--------|------|
| ≥85 | 高度一致 | 🟢 | 观点与持仓完全匹配，言行高度一致 |
| ≥70 | 基本一致 | 🟢 | 观点与持仓基本匹配，整体可信 |
| ≥50 | 部分一致 | 🟡 | 观点与持仓存在一定偏差 |
| ≥30 | 存在偏差 | 🟠 | 观点与持仓存在明显不一致 |
| <30 | 明显不一致 | 🔴 | 观点与持仓严重不符 |

---

## 报告模板结构

生成的报告包含以下四个核心部分：

### 一、报告摘要
- 基金经理姓名
- 观点分析区间
- 持仓分析区间
- 分析基金数量
- 核心结论
- 综合评分

### 二、基金经理核心观点概述
- 市场展望
- 投资策略与运作分析
- 重点关注领域/行业
- 风险提示

### 三、逐只基金观点与持仓一致性检验
- 基金名称与代码
- 观点报告期与持仓报告期
- 基金定位与核心观点
- 主要持仓（前 5-10 大重仓股）
- 一致性分析（四维度评分）
- 结论（高度一致/基本一致/部分一致/不一致）

### 四、整体结论与评价
- 综合评价
- 一致性亮点
- 潜在不一致/关注点
- 投资启示

---

*最后更新：2026-03-30*
*Skill 版本：v1.0*
*数据源：恒生聚源金融数据 (jy-financedata-api / jy-financedata-tool)*
