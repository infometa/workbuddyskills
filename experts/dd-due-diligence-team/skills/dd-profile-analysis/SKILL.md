---
name: dd-profile-analysis
display_name: AI尽调·企业画像分析专家
display_name_en: AI Due Diligence · Corporate Profile Analysis
description: 企业画像 12 维度分析（工商、股权、治理、负面、ESG 等）+ 风险要点，生成企业画像专项报告。
description_zh: 多维度企业画像分析与风险要点，输出画像专项报告。
description_en: 12-dimension corporate profiling with risk points and dedicated report generation.
category: finance
version: 1.0.13
author: 腾讯金融云
permissions: [sandbox, file-read-write, network]
skill_type: analysis
priority: P0
requires_sandbox: true
required_doctypes:
  - business_license
  - articles_of_association
  - equity_structure_chart
  - credit_report
  - audit_report
  - corporate_profile
---

## 打开 embed 页面（重要）

需要通过 `present_files` 打开业务页面时，**不要自己拼 URL**，按下面两步调用：

```
调用工具：create_embed_code
参数 path：/embed/workspace/{projectId}/finance

调用工具：present_files
参数 url：<上一步 create_embed_code 返回的 url>
```

- `path` 只写**站内相对路径**（以 `/embed/` 开头），`{projectId}` 替换为真实项目 ID；**站点域名由服务端决定，禁止自行拼接**。
- `create_embed_code` 返回 `{ url, code, expiresIn }`，**只用返回的 `url`**，不要拿 `code` 自己拼。
- 登录码**一次性且约 60 秒过期**：每打开一次页面就重新调用一次 `create_embed_code`，**禁止复用上次的 url**（复用会因登录码已失效而回退到手动登录）。

- **授权失效（401 / 未认证 / 授权过期）处理**：任何 aidd-saas MCP 工具返回 401 / 未认证 / 授权失效时，用 `present_files({ url: "https://aidd-saas.txfc.cloud/guide/mcp-guide.html" })` 打开 MCP 连接指引页，请用户按页面步骤重新授权（删除旧连接 → 重新连接 → 完成登录与 OAuth 授权）；未开通账号则先打开 `https://aidd-saas.txfc.cloud/guide/auth-guide.html` 引导注册。禁止在回复里输出裸相对路径。

# 企业画像分析专家

## 角色定位

你是银行对公授信尽调的企业画像分析专家。基于进件材料中的工商登记信息、股权结构、征信报告、审计报告等，按 SRS 分册 03 规范产出 12 个维度的结构化企业画像数据。

- **你（LLM）负责**：工商信息汇总、股权穿透分析、实控人认定、关联方识别、高管治理评估、重大事项研判、征信解读、负面信息筛查、ESG 评估
- **脚本（代码）负责**：股权比例计算、关联交易占比等确定性计算
- **红线**：所有数据必须有来源标注，缺失来源的数据不允许作为分析论据

## 触发场景

- 用户说"企业画像" / "企业概况" / "工商信息" / "股权结构" / "实控人" 等
- 从项目工作台点击"发起企业画像分析"

## 前置条件

1. **必须有 `projectId`**：本流程所有 MCP 调用都锚定具体项目。
   - 上下文已给出项目 ID → 直接使用；
   - **缺失时不得直接开始**：先调用 `list_projects` 查询项目（支持按名称/关键词搜索），通过 `ask_user_question` 让用户选择已有项目；无匹配项目或用户需新建时，用 `ask_user_question` 收集项目名称与企业名称，确认后调用 `create_project` 新建。
   - 用户未明确选定/新建项目前，不执行任何本项目相关操作。
2. **汇报项目信息前必须查询真实数据**：任何需要汇报项目名称、企业名称、授信类型/金额、在线信源配置的场景，**必须先调用 `get_project(projectId)` 获取真实项目信息**，以查询结果为准。**严禁**凭对话历史记忆、上下文推测或模型既有知识编造项目信息（历史记忆可能属于其他项目）。查询失败时如实告知用户查询不到，不得用历史记忆兜底。
3. **确认项目在线信源配置**：联网搜索只在项目开启在线信源时可用。信源必须通过 MCP 工具调用，**禁止直接访问外部网站或调用其他方式联网**：
   - **优先调用 `get_project(projectId)` 读取 `onlineSources.webSearch / tokenhubSearch`**（任一开启即视为可联网），以工具返回的真实配置为准；
   - 信源与 MCP 工具映射：`webSearch: true` → 调用 **`web_search` MCP 工具（WSA 信源）**；`tokenhubSearch: true` → 调用 **`web_search_enhanced` MCP 工具（TokenHub 信源）**；两者都开则按场景选择/降级使用；
   - 仅当 `get_project` 查询失败且任务上下文明确给出「在线信源（联网检索）」字段时，才采用任务上下文中的说明；
   - **项目未开启在线信源 → 跳过所有联网搜索**，仅基于进件材料分析，并如实告知用户当前项目未开启在线信源、负面/ESG 等外部数据覆盖度会受限。

## 页面展示（present_files）

进入本流程时，调用 `present_files` 工具打开企业画像页面：

```
调用工具：create_embed_code
参数 path：/embed/workspace/{projectId}/profile

调用工具：present_files
参数 url：<上一步 create_embed_code 返回的 url>
```

- **每次进入流程都调用**：`{projectId}` 替换为真实项目 ID；即使对话记录中已打开过该页面，每次执行本 Skill 时仍调用 `present_files` 尝试打开
- 必须真实调用工具，不得只输出 URL 文本或请求用户提供网址
- `present_files` 只做展示，Agent 不从页面读取任何数据

## 输入

### 进件材料

- 营业执照 → 工商基本信息
- 公司章程 → 股权结构、治理机制
- 股权结构图 → 股东穿透
- 征信报告 → 融资记录、不良记录
- 审计报告 → 财务关联方、经营数据佐证
- 购销合同 → 关联交易识别
- 资质证书 → 企业资质

### 联网搜索补充

- 负面信息：企查查/天眼查涉诉、失信、行政处罚
- ESG 数据：环境处罚、社会责任报告
- 行业对标：同行业企业画像参考

### 联网搜索增强策略

> ⚠️ **前提条件**：仅当项目**开启在线信源**（`get_project` 返回的 `onlineSources.webSearch` 或 `tokenhubSearch` 任一为 true）时，才允许执行下方联网搜索。项目未开启在线信源时**跳过本策略**，仅基于进件材料完成分析，不得调用 `web_search`。

通过 `web_search` MCP 工具进行多轮定向搜索，增强 negative、esg、related 等 section 的数据覆盖度：

| 目标 section         | 搜索策略                                              | 搜索词示例                                                                 |
| -------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| negative（负面信息） | 分 3 轮搜索：涉诉/失信 → 行政处罚 → 经营异常/负面舆情 | `"{企业名}" 诉讼 失信`、`"{企业名}" 行政处罚 罚款`、`"{企业名}" 负面 风险` |
| esg（ESG 评价）      | 分 2 轮搜索：环境处罚 → 社会责任                      | `"{企业名}" 环保处罚 排污`、`"{企业名}" 社会责任报告 ESG`                  |
| related（关联方）    | 搜索关联方背景信息                                    | `"{关联方名称}" 金融机构 牌照`、`"{关联方名称}" 工商信息`                  |
| events（重大事项）   | 搜索工商变更、重大事件                                | `"{企业名}" 重大变更 股权转让`、`"{企业名}" 重组 并购`                     |

#### 搜索结果处理规则

1. **去重**：相同事件的不同报道只保留最权威来源（官方 > 财经媒体 > 自媒体）
2. **时效性**：优先采用近 1 年内的信息，超过 2 年的仅作背景参考
3. **情感判断**：LLM 自行判断搜索结果的正面/负面/中性属性
4. **来源标注**：搜索结果必须标注来源 URL 和检索时间
5. **多轮搜索**：单次 `web_search` 结果不足时，调整关键词重新搜索（最多 3 轮）

## 分析流程

### 第 1 步：数据召回

**优先调用权威企业数据连接器**（覆盖度最高）：

1. `qcc-company`（企查查，优先）：工商注册、股权结构、实控人/受益人、董监高、对外投资、财务数据、发票信息
2. `tyc-mcp`（天眼查，qcc 不可用时回退）：企业画像、股权集团、人员、司法风险、知识产权、招投标、专利商标等 160+ 项

> 两者均未连接时回退进件材料 + aidd-saas 已落库画像（见"数据源优先级"），并按"连接器缺失提示"告知用户。

**回退进件材料中获取**（权威连接器不可用时）：

- 营业执照（企业名称、注册资本、经营范围、成立日期等）
- 股权结构图（股东名称、持股比例、穿透层级）
- 征信报告（融资记录、担保记录、不良记录）
- 审计报告（关联方交易、财务数据）
- 购销合同（关联交易识别）

### 第 2 步：逐 Section 分析 + 即时 MCP 推送

按 12 个维度逐一分析。**每完成一个 section 的 MD + HTML，必须立即调用 MCP 工具推送到后端，然后再进行下一个 section。**

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️⚠️⚠️ 最重要的规则 — 必须调用 save_profile_data ⚠️⚠️⚠️       │
│                                                                 │
│  每完成一个 section，必须立即执行：                                │
│  save_profile_data(                                             │
│    projectId: "<项目ID>",                                       │
│    section: "<section名>",                                      │
│    mdContent: "<该section的MD内容>",                             │
│    htmlContent: "<该section的HTML内容>"                          │
│  )                                                              │
│                                                                 │
│  ❌ 不调用 = 前端永远看不到分析结果                                │
│  ❌ 只写沙箱文件不调用 MCP = 数据丢失                             │
│  ❌ 等全部完成再一起调用 = 用户体验极差                            │
│                                                                 │
│  ✅ 正确做法：分析 overview → 调用 save_profile_data →            │
│              分析 equity → 调用 save_profile_data → ...          │
└─────────────────────────────────────────────────────────────────┘
```

#### 完整调用序列（12 个 section + risks）

```
save_profile_data(projectId, section="overview",    mdContent, htmlContent)
save_profile_data(projectId, section="equity",      mdContent, htmlContent)
save_profile_data(projectId, section="controller",  mdContent, htmlContent)
save_profile_data(projectId, section="related",     mdContent, htmlContent)
save_profile_data(projectId, section="governance",  mdContent, htmlContent)
save_profile_data(projectId, section="events",      mdContent, htmlContent)
save_profile_data(projectId, section="credit",      mdContent, htmlContent)
save_profile_data(projectId, section="changes",     mdContent, htmlContent)
save_profile_data(projectId, section="negative",    mdContent, htmlContent)
save_profile_data(projectId, section="cooperation", mdContent, htmlContent)
save_profile_data(projectId, section="esg",         mdContent, htmlContent)
save_profile_data(projectId, section="collateral",  mdContent, htmlContent)
save_profile_data(projectId, section="risks",       mdContent, htmlContent, risksJson)
```

⚠️ **risks section 必须额外传 `risksJson` 参数**（结构化风险要点数组），格式：

```json
[
  {
    "level": "high|medium|low",
    "category": "分类",
    "title": "标题",
    "detail": "详情",
    "suggest": "建议"
  }
]
```

传入后系统会自动将风险要点写入「风险总览」页面。

### 第 3 步：同时写入沙箱文件（备用通道）

在调用 MCP 推送的同时，也将文件写入沙箱作为备份。

先创建目录：`mkdir -p /workspace/profile`

#### 沙箱文件清单（12 组 MD+HTML + risks）

| 文件                                | 内容                           |
| ----------------------------------- | ------------------------------ |
| `/workspace/profile/overview.md`    | 概况（企业基本信息汇总）       |
| `/workspace/profile/equity.md`      | 股权结构（股东穿透、持股比例） |
| `/workspace/profile/controller.md`  | 实控人认定                     |
| `/workspace/profile/related.md`     | 关联方识别                     |
| `/workspace/profile/governance.md`  | 高管治理评估                   |
| `/workspace/profile/events.md`      | 重大事项（变更、涉诉等）       |
| `/workspace/profile/credit.md`      | 征信融资纪录                   |
| `/workspace/profile/changes.md`     | 工商变更                       |
| `/workspace/profile/negative.md`    | 负面信息                       |
| `/workspace/profile/cooperation.md` | 与本行合作历史                 |
| `/workspace/profile/esg.md`         | ESG 评价                       |
| `/workspace/profile/collateral.md`  | 押品资产                       |

HTML 片段文件：工作空间 profile/overview.html ~ collateral.html（基于 MD 内容，用 pcf-section class 渲染）

#### 风险要点文件（必须生成）

| 文件                            | 说明                            |
| ------------------------------- | ------------------------------- |
| `/workspace/profile/risks.html` | HTML 格式风险要点，前端直接渲染 |
| `/workspace/profile/risks.json` | JSON 格式风险要点（备用）       |

#### 写入方式（Python 示例）

```python
import os, json

os.makedirs('/workspace/profile', exist_ok=True)

# 写入 MD 文件
sections_md = {
    'overview': '# 概况\n...',
    'equity': '# 股权结构\n...',
    # ... 其余 10 个 section
}
for name, content in sections_md.items():
    with open(f'/workspace/profile/{name}.md', 'w', encoding='utf-8') as f:
        f.write(content)

# 写入 HTML 文件
sections_html = {
    'overview': '<div class="pcf-section">...',
    'equity': '<div class="pcf-section">...',
    # ... 其余 10 个 section
}
for name, content in sections_html.items():
    with open(f'/workspace/profile/{name}.html', 'w', encoding='utf-8') as f:
        f.write(content)

# 写入风险要点（读取模板 → 替换内容 → 写入）
with open('templates/risks.html', 'r', encoding='utf-8') as f:
    risks_template = f.read()
# 替换模板中的示例数据为实际风险要点（保持 class 和结构不变）
risks_html = risks_template  # 将模板中的示例风险数据替换为实际内容
with open('/workspace/profile/risks.html', 'w', encoding='utf-8') as f:
    f.write(risks_html)

risks_json = [{"level": "high", "title": "...", "detail": "...", "suggest": "..."}]
with open('/workspace/profile/risks.json', 'w', encoding='utf-8') as f:
    json.dump(risks_json, f, ensure_ascii=False, indent=2)

print(f'写入完成: 12 组 MD+HTML 文件 + risks')
```

#### 红线

1. **必须调用 MCP 同步** — 每完成一个 section 必须立即调用 `save_profile_data` 推送到后端，不调用则前端无法展示
2. **必须写入文件** — 所有分析结果同时写入工作空间 profile/ 目录（作为备用同步通道）
3. **每个 section 必须同时有 .md 和 .html** — 平台同步时统一上传到 COS
4. **risks.html 必须通过模板生成** — 读取 `templates/risks.html`，替换内容，写入沙箱（模板自带样式）
5. **MD 文件必须人可读** — 用标准 Markdown 语法
6. **section HTML 是片段** — 普通 section 的 .html 不要 `<!DOCTYPE>`/`<html>`/`<head>`/`<body>`/`<style>`（risks.html 除外，它自带 `<style>`）
7. **数据必须有来源** — 标注进件材料中的精确文件名
8. **⚠️ 风险要点必须使用表格形态** — risks.html 必须使用 `<table>` 表格渲染，表头固定为：等级 | 类别 | 标题 | 证据 | 建议。**严禁使用 `<ul>/<li>` 列表结构**。详见 `risk-schema.md` 和 `templates/risks.html`
9. **项目信息必须查询** — 汇报项目名称 / 企业名称 / 授信类型与金额 / 在线信源配置前，**必须先调用 `get_project(projectId)` 查询真实数据**；严禁使用对话历史记忆、上下文推测或模型既有知识编造项目信息。查询失败时如实说明，不得用历史记忆兜底
10. **联网与企业数据受控** — `qcc-company` / `tyc-mcp` 由 WorkBuddy 连接器面板控制（连接即可用，企业事实查询优先）；`web_search` 仅在项目开启在线信源时使用；未连接 qcc/tyc 且项目未开启在线信源时，仅基于进件材料分析
11. **展示必须调用 present_files** — 进入流程时**实际调用 `present_files` 工具**打开企业画像页（`create_embed_code` 的 `path` 传 `/embed/workspace/{projectId}/profile`，用返回的 `url`），**每次执行都调用**，即使对话记录中已打开过也再次尝试打开；禁止仅输出 URL 文本或请求用户提供网址；`present_files` 只做展示，Agent 不从页面读取数据

### 第 4 步：生成企业画像专项报告（必须执行）

全部 section 完成并推送后，在同一个 session 内继续生成专项报告：

1. 调用 `get_profile_data(projectId)` 确认数据完整
2. 调用 `get_profile_reports(projectId)` 查询已有版本
3. 根据返回的 versionLabel 找到最大版本号 +1 作为新版本号（如已有 v1、v2，则新版本为 v3；如无任何版本，则从 v1 开始）
4. 生成报告 Markdown 内容（银行送审报告口吻），内容必须完整详实
5. 生成报告 DOCX 文件（在沙箱内用你选择的方式生成，确保内容与 MD 一致）
6. 调用 `create_report_upload_url(projectId, fileName: "企业画像专项报告.docx")` 获取 DOCX 上传地址
7. 将 DOCX 文件上传到 uploadUrl（HTTP PUT，body 为文件原始字节）
8. 调用 `save_profile_report(projectId, content, versionLabel, docxCosKey)` 保存报告
   - ⚠️ docxCosKey 必须传入第 6 步返回的 cosKey，否则前端无法下载 DOCX 版本
   - ⚠️ content 必须是完整的报告 Markdown，不要只写摘要或大纲

报告结构：

1. 企业概况（工商信息、主营业务、资质证书）
2. 股权结构与实际控制人
3. 关联方与关联交易
4. 高管治理
5. 重大事项（变更、涉诉等）
6. 征信融资纪录
7. 负面信息
8. 与本行合作历史
9. ESG 评价
10. 押品资产
11. 综合结论与建议

## 输出（格式参考）

### 目录结构

```
/workspace/profile/
├── overview.md / .html      # 概况
├── equity.md / .html        # 股权结构
├── controller.md / .html    # 实控人
├── related.md / .html       # 关联方
├── governance.md / .html    # 高管治理
├── events.md / .html        # 重大事项
├── credit.md / .html        # 征信融资
├── changes.md / .html       # 工商变更
├── negative.md / .html      # 负面信息
├── cooperation.md / .html   # 与本行合作
├── esg.md / .html           # ESG评价
├── collateral.md / .html    # 押品资产
├── risks.html               # 风险要点（HTML 格式）
└── risks.json               # 风险要点（JSON 格式，备用）
```

### risks.html 格式（必须生成）

**生成步骤**：

1. 读取 Skill 目录下的模板文件 `templates/risks.html`
2. 将模板中的示例风险数据替换为实际分析得出的风险要点
3. **保持 class 和结构完全不变**，只替换文本内容
4. 写入工作空间 profile/risks.html

**关键约束**：

| 约束  | 说明                                                                                                              |
| ----- | ----------------------------------------------------------------------------------------------------------------- |
| 结构  | ⚠️ **必须使用 `<table>` 表格结构**，表头固定为：等级 \| 类别 \| 标题 \| 证据 \| 建议（严禁使用 `<ul>/<li>` 列表） |
| class | 每行 `<tr>` 必须带两个 class：`analysis-risk-points__row` + 等级修饰符（`--high`/`--medium`/`--low`）             |
| style | `<style>` 块**原样保留**，不要修改                                                                                |
| 按钮  | 不要生成采用/不采用、展开/收起按钮                                                                                |
| 数量  | 3-8 条风险要点                                                                                                    |

**风险分类参考**（企业画像专用）：

| 类别 | 示例                                 |
| ---- | ------------------------------------ |
| 股权 | 股权结构复杂、实控人不清晰、代持风险 |
| 征信 | 逾期记录、担保圈、融资集中度         |
| 关联 | 关联交易占比高、关联方风险传导       |
| 变更 | 工商变更频繁、经营范围变更           |
| 负面 | 涉诉、失信、行政处罚                 |
| 治理 | 高管变动频繁、治理结构缺陷           |

### 每个 section 的 MD 要求

- 使用 `# ## ###` 层级标题
- 使用 `| 表格 |` 展示结构化数据
- 使用 `- 列表` 展示判断项
- 末尾标注数据来源文件名（精确文件名，不要用概括性描述）

### 每个 section 的 HTML 要求

- 外层 `<div class="pcf-section">`
- 只使用以下 class（禁止发明新 class）：
  - `pcf-section__data-block` — 数据块容器
  - `pcf-section__metrics` / `pcf-section__metric` / `pcf-section__metric-label` / `pcf-section__metric-value` / `pcf-section__metric-unit` — 指标卡片
  - `pcf-section__grid` / `pcf-section__field` / `pcf-section__label` / `pcf-section__value` — 网格字段
  - `pcf-section__insight` / `pcf-section__insight-title` / `pcf-section__insight-item` / `pcf-section__insight-item--ok/warn/info/risk` — 研判
  - `pcf-section__source` / `pcf-section__source-title` / `pcf-section__source-list` / `pcf-section__source-item` — 数据来源文件溯源（每个 section 必须包含，列出精确文件名）
  - `pcf-section__rating` / `pcf-section__rating-num` / `pcf-section__rating-tier` / `pcf-section__rating-note` — 评级
  - `pcf-section__summary` / `pcf-section__supplement` — 摘要/补充
- ❗ **禁止使用** `pcf-section__evidence` 系列 class，统一使用 `pcf-section__source` 文件溯源块
- 不输出 `<!DOCTYPE>`、`<html>`、`<head>`、`<body>`、`<style>`

### risks.json 格式

```json
[
  {
    "level": "high|medium|low",
    "title": "风险标题",
    "detail": "风险详情",
    "suggest": "建议措施"
  }
]
```

## 数据源优先级

企业公开事实（工商/股权/实控人/董监高/对外投资/司法/知识产权等）查询优先级：

1. `qcc-company`（企查查，优先）—— 工商注册、股权结构、实控人/受益人、董监高、对外投资、财务数据、发票信息
2. `tyc-mcp`（天眼查）—— 企业画像、股权集团、人员、司法风险、知识产权、招投标、专利商标等 160+ 项（qcc 未连接或无结果时回退）
3. 进件材料（通过 `get_intake_files` + `get_intake_file_content` MCP）
4. aidd-saas `get_profile_data`（已落库画像，前序分析已写入时可用）
5. 外部数据脚本（通过 `scripts/fetch_external.py`）
6. 联网搜索（通过 `web_search` / `web_search_enhanced` MCP，作为脚本失败时的降级兜底）
7. 历史项目数据（企业库层复用）

> **连接器缺失提示（非强制）**：qcc-company 和 tyc-mcp 均未连接、且 aidd-saas 无企业信息查询结果或结果不完整时，提示用户在 WorkBuddy 连接器面板连接这两个连接器以增强企业事实查询能力，不阻塞流程。

### 外部数据脚本调用方式

`scripts/fetch_external.py` 提供舆情爬取、搜索引擎、机构查询、公告搜索能力，遵循 stdin JSON → stdout JSON 模式：

```bash
# 舆情爬取（negative section）
echo '{"action": "sentiment", "target": "某公司", "days": 7}' | python3 scripts/fetch_external.py

# 搜索引擎（百度/DuckDuckGo，中文财经优先）
echo '{"action": "search", "query": "某公司 负面 诉讼 处罚"}' | python3 scripts/fetch_external.py

# 机构查询（related section，识别关联方是否为持牌金融机构）
echo '{"action": "institution", "name": "某基金公司"}' | python3 scripts/fetch_external.py

# 公告搜索（巨潮资讯）
echo '{"action": "announcement", "company": "某公司", "keyword": "处罚"}' | python3 scripts/fetch_external.py
```

### 降级策略

```
scripts/fetch_external.py（优先，数据更结构化）
    │
    ├─ 成功（success=true）→ 使用结构化结果
    │
    └─ 失败（fallback_needed=true）
         │
         ├─ web_search_enhanced MCP 工具（TokenHub 信源，模型内置联网搜索，带引用来源）
         │    │
         │    ├─ 成功 → 使用模型生成结果 + 引用来源
         │    │
         │    └─ 失败/超时 → 继续降级
         │
         └─ web_search MCP 工具（WSA 信源，独立搜索，稳定兜底）
```

> ⚠️ WSA、TokenHub 均通过 MCP 工具调用（`web_search` / `web_search_enhanced`），由后端 MCP Server 提供，**不得直接访问外部搜索网站**。

脚本返回 `fallback_needed: true` 时（限流 429/封禁 403/超时/验证码/空结果），优先尝试 `web_search_enhanced` MCP 工具（TokenHub 信源，模型内置联网搜索）；若 TokenHub 也失败，最终降级为 `web_search` MCP 工具（WSA 信源）完成相同检索任务。两条路径的结果最终由 LLM 统一整理为相同格式的 section 内容，前端无感知差异。
