# 能力模块 · 数仓问数（Data Warehouse Q&A）

> **本文件是「数仓问数」能力的唯一 owner**，覆盖其全生命周期：**detect → confirm → inject → test**。
> **可选能力**：按需启用（见 `modules/registry.md`）。
>
> | 锚点 | 被调用阶段 | 职责 |
> |------|-----------|------|
> | `#detect` | §1 分析 | 扫描前端 SQL 查询 + 应用功能结构 |
> | `#confirm` | §2 建议 | 确认启用 + MCP 依赖告知 |
> | `#inject` | §3 创建 | 提取 SQL + 分析应用结构 → 生成 Skill 包 |
> | `#test` | §5 验证 | Skill 可用性 + MCP 工具可达性 |
>
> 模板：`assets/templates/dw-qa/`

---

## 元数据声明

| 字段 | 值 |
|------|-----|
| `userLabel` | 📊 数仓问数 |
| `contributedTools` | —（生成 Skill 文件，不向 Bridge 贡献工具） |
| `dependsOn` | — |
| `mcpDependency` | `hr_data_service_v1`（提供 starrocks_query、slang_query 等工具） |
| `testScript` | 模型自行验证 |

---

## 设计总纲

### 核心思路

页面中已有的 SQL 是经过验证的正确查询。以**语义匹配模板**为主路径，按覆盖程度分三条路：① 直接覆盖 → 执行模板；② 间接覆盖（模板含相关字段但不直接做聚合）→ 基于模板结果做聚合分析（SQL 改写 or 结果分析）；③ 无覆盖 → 降级到 LLM 按规则自行生成 SQL 或调用指标接口。通过提取应用功能结构 + SQL 字段，让 Agent 理解应用的数据范围与查询能力，实现"应用范围内问数"，做到和页面查询一致的体验。

### 设计原则

1. **SQL 原样提取**：页面 SQL 中的硬编码值是应用支持的查询口径，原样保留。仅将 `${variable}` 插值转为 `{variable}` 占位符。
2. **保留业务上下文**：每条 SQL 连同所在函数名、功能模块、注释一起提取，让 Agent 理解 SQL 的业务含义。
3. **原则优于细节**：提取和参数化遵循原则（保留语义、可执行），不过度枚举每种模式——让 LLM 在运行时根据上下文处理具体细节。

### 产出物

```
.agent/skills/dw-qa/
├── SKILL.md                    ← 应用概览 + 问数流程 + 查询规则（从模板渲染）
└── references/
    └── templates.md            ← 表常量映射 + SQL 模板目录（动态生成）
```

### MCP 依赖

本能力依赖 `hr_data_service_v1` MCP 服务，提供以下工具：`starrocks_query`、`slang_query`、`indicator_query`、`list_resources`、`read_resource`、`get_current_user`、`get_current_user_data_permission`。

MCP 地址：
- 测试环境：`http://dev-ntsgw.woa.com/api/esb/mcp-host-server/mcp/DataViewMCP_test`
- 生产环境：`http://ntsgw.woa.com/api/esb/mcp-host-server/mcp/DataViewMCP`

- **注册时**：§4 从 `boost-state.json` 的 `capabilities.dw-qa.mcpUrl` 读取地址，追加到 Agent 的 `mcp_servers`
- **运行时**：agent-server 通过该 MCP 服务执行 SQL 查询，数仓按用户身份自动行权限过滤

---

## #detect 分析阶段（§1）

在 §1 扫描能力矩阵时，附加检测前端代码是否包含数仓 SQL 查询，并提取应用功能结构。

### 检测信号（命中任一即标记 detected=true）

| # | grep 模式 | 说明 |
|---|----------|------|
| 1 | `queryDW\|batchQueryDW\|cachedQueryDW` | 数仓查询函数调用 |
| 2 | `` `SELECT\s+.*\s+FROM\s+ `` | 模板字符串中的 SQL |
| 3 | `const\s+T_[A-Z_]+\s*=\s*['"]catalog_` | 表常量定义 |
| 4 | `dos-dataview-mcp\|/api/query` | 数仓 API 端点 |

### 扫描范围

1. `public/index.html`（或根目录 `index.html`）— 最可能含 SQL
2. `src/**/*.js` / `src/**/*.ts` / `src/**/*.vue`
3. `server.js` / `app.js` 等后端入口

### 提取信息

```yaml
dw-qa:
  detected: true
  sqlCount: 48
  files: ["public/index.html"]
  tables:                         # 表常量
    - { alias: "T_LATEST", path: "catalog_...Report_Wide_Public_Staff_Info" }
  queryFunctions: ["queryDW", "batchQueryDW"]
  # 应用结构（基础层 — 必出）
  appTitle: "HR 工作台"
  templateType: "dw-readonly"     # page-deliver 模板类型（如可识别）
  features:                       # 功能模块
    - name: "组织看板"
      loadFunctions: ["loadStaff", "loadOrgLeaders"]
    - name: "HC管理"
      loadFunctions: ["loadHcStaff", "loadDwHc", "loadPendingEntry"]
    - name: "招聘看板"
      loadFunctions: ["loadRecruit", "loadRecruitCampus"]
    - name: "员工画像"
      loadFunctions: ["openProfile"]
  # 应用结构（增强层 — 尽量出，识别不到不阻塞）
  featureDetails:
    - { name: "组织看板", filters: ["组织范围", "快照日期", "身份类型"], display: "表格+卡片" }
  suggestLabel: "📊 数仓问数"
```

### 应用结构分析原则

- **Tab/视图识别**：grep HTML 中的 tab 标签、导航项标题、`v-if`/`v-show` 条件
- **SQL → 功能映射**：每条 SQL 所在函数 → 追溯到 Tab/视图 → 归入对应功能模块
- **映射不到的**：归入"通用"模块
- **增强层可选**：筛选条件、展示方式等信息能识别就提取，不阻塞主线

---

## #confirm 建议阶段（§2）

### 交互流程

```
📊 检测到你的应用包含数仓数据查询能力：

  · 发现 48 条 SQL 查询
  · 涉及 27 张数据表
  · 功能模块：组织看板、HC管理、招聘看板、员工画像

启用「数仓问数」后，Agent 可以：
  · 在企微等渠道直接问数，体验和页面一致
  · 语义匹配模板，直接查询或基于模板结果做聚合分析
  · 模板覆盖不到时，降级到自行生成 SQL 或指标接口
  · 对查询结果进行分析和洞察

⚠️ 本能力依赖 hr-ai-data 数仓 MCP 服务，将在注册时自动配置。

是否启用？(y/n)
```

### 配置确认

用户确认后，生成 `.agent/dw-qa/config.json`：

```json
{
  "enabled": true,
  "skillName": "dw-qa",
  "skillDir": ".agent/skills/dw-qa",
  "sqlFiles": ["public/index.html"],
  "sqlCount": 48,
  "tableCount": 27,
  "features": ["组织看板", "HC管理", "招聘看板", "员工画像"]
}
```

---

## #inject 创建阶段（§3）

> 核心：**从页面代码提取 SQL + 分析应用结构 → 生成 Skill 包**。
> 产物生成后，由主线 §4 负责将 skill 注册到 Agent 配置（含 MCP 依赖）。

### ① 提取 SQL 与常量

对 `config.json` 中记录的每个文件：

**SQL 查询**：
- 提取所有 `queryDW(` / `batchQueryDW(` / `cachedQueryDW(` 调用及其 SQL
- 对每条 SQL 记录：完整 SQL 文本、所在函数名、上方注释、所属功能模块

**常量定义**：
- `const T_XXX = 'catalog_...'` → 表常量映射
- `const ORG_SCOPE = '1=1'` 等简单常量 → 直接内联到 SQL

### ② 参数化与分组

**参数化原则**（非穷举，LLM 根据代码上下文判断）：
- `${variable}` → `{variable}` 占位符
- 函数调用型（如 `${esc(staff_type)}`）→ 简化为 `{staff_type}`
- 动态表名、条件片段等 → 根据代码上下文理解后合理参数化；无法参数化的保留为注释说明
- 硬编码的时间敏感值（如 `recruit_year='2026'`）→ 参数化为 `{recruit_year}` 并标注当前值
- 多行 SQL → 合并为单行

**参数标注**（每个参数标注类型和来源，供运行时 LLM 解析）：
- **固定值**：如 `{ORG_SCOPE}` = `1=1` → 标注固定值
- **有候选值**：如 `{staff_type}` 候选 正式/外包（从 UI 组件提取）→ 标注候选值
- **需动态解析**：如 `{org_path}` 需 starrocks_query 查 DISTINCT → 标注解析方式
- **条件参数**：如 `{table}` 最新→T_LATEST / 快照→T_SNAPSHOT+日期 → 标注条件逻辑
- **前序结果**：如 `{id_list}` 来自 Step 1 结果 → 标注来源 Step

**keywords 提取**（重要——直接决定模板匹配的泛化能力）：
- 来源：函数名 + 上方注释 + 所属功能模块名 + **SQL 中 SELECT/WHERE 涉及的字段名**
- SQL 字段名用原名，不翻译——LLM 能理解字段语义
- 这确保模板的 keywords 涵盖 SQL 实际查询的所有字段，即使用户问的维度在注释/函数名中未提及，模板仍能通过字段名被匹配到

**复合模板**：
- 一个函数内有多步查询且结果相互关联 → 标记 `type: composite`，描述各 Step 的 SQL 和数据流转
- 无法确定的按单条模板处理 + 注释说明

**分组**：按功能模块分组（detect 阶段识别的 features），映射不到的归"通用"。

### ③ 渲染 Skill 包

**SKILL.md**：读取 `assets/templates/dw-qa/SKILL.md.template`，**仅替换占位符，禁止修改模板中的其他任何内容**（流程、规则、工具表等均为固定内容，原样保留）：

| 占位符 | 替换为 |
|--------|--------|
| `{{SKILL_NAME}}` | `dw-qa` |
| `{{APP_NAME}}` | 应用名 |
| `{{FEATURE_SUMMARY}}` | 功能摘要（如"覆盖组织看板、HC管理等4个功能模块，48条SQL模板。"） |
| `{{APP_OVERVIEW}}` | 应用概览（标题 + 一句话描述 + 模板类型 + 数据范围） |
| `{{FEATURE_MODULES}}` | 功能模块列表（名称 + 描述 + 模板数） |

**templates.md**：读取 `assets/templates/dw-qa/templates.md.template`，填充表常量映射 + SQL 模板目录（按功能模块分组）。

输出到 `.agent/skills/dw-qa/`。

### ④ boost-state.json 记录

§3.8 写 boost-state 时，dw-qa 详情内嵌在 `capabilities.dw-qa` 下：

```json
"capabilities": {
  "dw-qa": {
    "enabled": true,
    "configRef": ".agent/dw-qa/config.json",
    "skillDir": ".agent/skills/dw-qa",
    "mcpDependency": "hr_data_service_v1",
    "mcpUrl": "http://dev-ntsgw.woa.com/api/esb/mcp-host-server/mcp/DataViewMCP_test",
    "sqlCount": 48,
    "tableCount": 27,
    "features": ["组织看板", "HC管理", "招聘看板", "员工画像"]
  }
}
```

> `mcpDependency` 为服务名，`mcpUrl` 为测试环境地址。§4 注册时读取这两个字段追加到 `mcp_servers`；生产环境由 `register-agent.sh` 的 `_CAP_MCP_MAP` 映射生产地址。

---

## #test 验证阶段（§5）

### 验证步骤

1. **模板匹配测试**：构造典型用户问题，检查能否正确判断覆盖程度（直接覆盖/间接覆盖/无覆盖）并选择正确路径
2. **SQL 语法检查**：填充参数后，检查 SQL 语法完整（表名已替换、无遗漏占位符）
3. **MCP 工具可达性**：检查 `starrocks_query`、`list_resources`、`read_resource` 是否可用
   - 可用 → pass
   - 不可用 → warning（不阻塞，提示用户确认 hr-ai-data MCP 配置）
4. **工具门控声明**：检查 `.agent/skills/dw-qa/SKILL.md` frontmatter 含 `gated_mcp_servers: [hr_data_service_v1]`
   - 存在且值正确 → pass
   - 缺失或值不正确 → **fail**（阻塞，必须修复后才能进入 §6）

### 测试报告

输出到 `.agent/dw-qa/test-report.json`：

```json
{
  "gate": true,
  "tests": [
    { "name": "模板匹配", "status": "pass" },
    { "name": "SQL 语法", "status": "pass" },
    { "name": "MCP 工具可达", "status": "pass", "tools": ["starrocks_query", "slang_query"] },
    { "name": "工具门控一致性", "status": "pass", "gated_mcp": "hr_data_service_v1" }
  ]
}
```

> 门禁：`gate = mcp.gate AND dw-qa.gate AND (其他能力 gate)`
> MCP 工具不可用时 dw-qa.gate 仍为 true（warning 不阻塞），但提示用户后续配置。
> 工具门控一致性为 **fail** 时 dw-qa.gate = false（阻塞注册，必须修复）。
