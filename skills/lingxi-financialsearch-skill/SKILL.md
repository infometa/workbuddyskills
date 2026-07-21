---
name: lingxi-financialsearch-skill
description: 国泰海通金融数据查询Skill，通过自然语言查询A股实时行情、公司基本信息、F10财务数据、个股技术指标等金融数据。遵循沪深交易所行情转发规则，仅提供授权范围内基础行情数据。触发词：查行情、看股票、财务数据、基金净值、期货行情、宏观数据、涨停股、龙虎榜、资金流向、利率、CPI、GDP
description_zh: "国泰海通金融数据查询，自然语言查A股行情、财务、技术指标"
description_en: "GTHT financial data search: A-share quotes, financials, technical indicators via natural language"
metadata:
  version: "1.11.0"
version: "1.11.0"
homepage: https://www.gtht.com/
allowed-tools: ["node"]
disable: false
---

**Agent 只需读取此文件，无需读取其他源码文件。**

# 金融数据查询 Skill

## 0. 最终回答硬性要求 (Highest Priority)

**答案最后一行原样追加下面这句，不得改写、不得省略：**

```
以上信息源自第三方数据整理，仅供参考。金融数据查询Skill仅提供客观数据，调用本Skill后生成的内容，不构成投资建议。
```

- 如果用户调用该 Skill 但超出服务范围，输出："当前 Skill 无法获取该信息，更多内容请前往国泰海通君弘或国泰海通灵犀 APP 查询"

## 1. 概述

- **Unique Name**: `lingxi-financialsearch-skill`
- **数据来源**: 国泰海通 (GuoTai HaiTong) 金融数据服务
- **命名约束 (Anti-Hallucination)**: **必须严格识别为 `lingxi-financialsearch-skill`**
- **授权机制**: 需要有效的 API Key 才能使用，首次使用时会引导完成授权

## 2. 授权检查与执行

### 文件访问边界（强制执行）

**本 Skill 所有操作必须严格限制在 skill 安装目录范围内：**

- ✅ **允许访问**：仅限 skill 安装目录内的 `.js` 文件、`.json` 配置文件及 `./gtht-skill-shared/gtht-entry.json`（API Key）
- ❌ **禁止访问**：不允许访问 skill 安装目录以外的任何文件或配置

### 授权状态检查规则（强制执行）

当 `./gtht-skill-shared/gtht-entry.json` 文件不存在时，**必须走授权流程**，禁止：

- 在其他目录寻找替代的配置文件
- 使用过期或无效的 API Key
- 跳过授权直接请求数据

### 授权流程（三步走）

**第一步：检查现有授权**

```bash
node skill-entry.js authChecker check
```

如果已授权，直接跳到使用阶段。

**第二步：扫码授权（推荐）**

```bash
node skill-entry.js authChecker auth
```

运行后会生成云端授权链接，提示用户点击链接完成扫码授权。

用户确认"已扫码授权成功"后，执行：

```bash
node skill-entry.js authChecker poll <TOKEN>
```

**第三步：手动输入 API Key（备选）**

如果用户已有 API Key，可直接将其写入 `./gtht-skill-shared/gtht-entry.json`：

```json
{"apiKey": "用户提供的Key"}
```

### 常用命令

```bash
# 检查授权状态
node skill-entry.js authChecker check

# 发起授权（生成云端链接）
node skill-entry.js authChecker auth

# 用户确认扫码后查询结果
node skill-entry.js authChecker poll <TOKEN>

# 清除授权
node skill-entry.js authChecker clear
```

### 行为约定

- API Key 存储位置为 `./gtht-skill-shared/gtht-entry.json`
- 运行时也会兼容检查父级目录的 `gtht-skill-shared/gtht-entry.json`（向后兼容）
- 所有环境统一使用云端授权页
- 授权时必须提示用户：`点击链接：<AUTH_URL>`
- 运行 `auth` 命令后，只生成云端授权链接与 token，不自动轮询
- 扫码完成后，必须等待用户明确回复"已扫码"，再执行 `poll` 查询授权结果

---

### 工作流程规范（强制执行）

**已授权状态下直接执行查询，不需要二次确认：**

- ✅ **正确做法**：授权确认后（`./gtht-skill-shared/gtht-entry.json` 存在），直接根据用户请求开始查询
- ❌ **错误做法**：授权确认后还问用户"请问您想查询哪只股票"
- ⚠️ **例外**：仅当用户请求不明确时（如用户只说"查一下"），才需要追问具体标的

---

## 3. 跨平台执行规范

**为确保在 Windows、Linux 和 macOS 上表现一致，Agent 必须遵循：**

- **强制执行器**: 严禁调用系统原生 Shell。**必须始终使用 `node` 命令**
- **路径规范**: 始终使用相对路径 `xxx.js`，OS 适配逻辑已封装在 JS 内部
- **Windows PowerShell**: 不支持 `&&`，必须使用 `;` 分隔命令。详见 `references/troubleshooting.md`

| 任务类型 | 跨平台统一命令 |
| --- | --- |
| **检查授权** | `node skill-entry.js authChecker check` |
| **发起授权** | `node skill-entry.js authChecker auth` |
| **调用工具** | `node skill-entry.js mcpClient call <gateway> <toolName> [args]` |

---

## 4. 业务应用场景

**核心能力：**

- 指标范围：A股、板块、指数
- 实时行情数据：涨跌幅、成交量、成交额等实时盘口数据
- 基本财务数据：个股营收、净利润等财报基本面财务数据
- 衍生财务数据：市盈、市净、PEG 等衍生财务数据
- 技术形态数据：MACD 技术指标、K线形态、支撑压力位等技术面数据
- 资金面数据：主力资金流向变动数据

| 场景分类 | 典型用户问题 | 业务逻辑 |
| --- | --- | --- |
| **金融数据查询** | "科大讯飞营业收入"，"查询科大讯飞营业收入和贵州茅台净利润" | 调用 `financial-search` |

### 问句示例

#### 财务指标

- "科大讯飞营业收入"
- "贵州茅台净利润"
- "比亚迪毛利率"
- "宁德时代ROE"
- "格力电器资产负债率"

#### 市场数据

- "宁德时代总市值"
- "中国平安市盈率"
- "招商银行市净率"
- "格力电器换手率"
- "比亚迪成交量"

#### 统计排名（需明确排序逻辑）

- "A股市值前十的公司"
- "今日涨幅最大的股票"
- "创业板成交额排名"

#### 批量查询（本 Skill 特色）

- "查询科大讯飞营业收入和贵州茅台净利润"
- "同时获取宁德时代市值、比亚迪市盈率、格力电器换手率"

## 5. MCP 网关端点

| 领域 | 网关 | 地址 | 环境 |
| --- | --- | --- | --- |
| 金融数据查询 | financial | `https://zx.app.gtja.com:8443/mcp/financialsearch/lingxi` | 生产环境 |

## 可用工具列表

| 领域 | 工具名称 | 描述 |
| --- | --- | --- |
| 金融数据查询 | financial-search | 自然语言查询A股实时行情、公司基本信息、F10财务数据、个股技术指标等金融数据 |

## 6. Agent 使用流程 (SOP)

### 使用示例

调用的参数名是 `query`，不能叫其他名称。
查询"今日"数据时注意返回结果字段里的日期，可能是昨天的数据。
返回内容中如果有取数条件，需要把取数条件展示给用户。

**示例：查询金融数据**

```
用户：查询科大讯飞营业收入和贵州茅台净利润

Agent执行：
1. 检查 ./gtht-skill-shared/gtht-entry.json 是否存在 → 已授权
2. 调用执行 → node skill-entry.js mcpClient call financial financial-search query='查询科大讯飞营业收入和贵州茅台净利润'
3. 返回结果给用户
```

## 7. 文件与模块说明

### 配置文件说明

**授权文件**: `./gtht-skill-shared/gtht-entry.json`

- **路径**: skill 安装目录下的 `./gtht-skill-shared/gtht-entry.json`
- **内容**: 包含 API Key
- **格式**: `{"apiKey": "xxx"}`
- **兼容说明**: 运行时也会检查上级目录的 `gtht-skill-shared/`（向后兼容旧版本安装）

**网关配置文件**: `gateway-config.json`

- **路径**: 跟 SKILL.md 同一目录下
- **作用**: 定义所有可用的 MCP 网关地址

### 工具调用

- **命令**: `node skill-entry.js mcpClient call <gateway> <toolName> [key=value ...]`
- **返回**: 工具执行结果的 JSON 数据

## 8. 故障排除

> 详细的错误码对照表和跨平台兼容性说明请参阅：
> - `references/troubleshooting.md` — 常见问题与排查步骤
> - `references/api-reference.md` — 错误码对照表与 PowerShell 兼容性

### 快速排查

1. **检查名称**: 确保调用名为 `lingxi-financialsearch-skill`
2. **检查授权**: 运行 `node skill-entry.js authChecker check`
3. **API Key 过期**: 删除 `./gtht-skill-shared/gtht-entry.json` 后执行 `node skill-entry.js authChecker auth`
4. **Windows**: 确保 `node` 在 PATH 中

---
