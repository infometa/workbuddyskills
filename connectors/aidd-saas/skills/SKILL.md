---
name: aidd-saas-skill
description: AI尽调助手 — 银行对公授信尽调全流程能力（进件识别、行业分析、企业画像、经营分析、财务分析、报告生成）
version: '1.0.0'
author: 'AIDD Team'
---

# AI尽调助手

本 Skill 提供银行对公授信尽调的完整能力，涵盖从进件材料识别到最终尽调报告生成的全流程。

## 权限要求

使用前需完成 OAuth 授权。授权后 AI 将以当前用户身份调用工具，所有数据操作受用户角色和租户权限控制。

## 工具清单

---

### 一、身份认证

#### whoami

查询当前 access token 绑定的用户与租户信息。

**无需参数**。返回当前用户的 userId、tenantId、username、role 等信息。

**使用场景**：调试时确认当前身份；在多租户场景下验证上下文。

---

### 二、项目管理

#### list_projects

列出当前用户可访问的项目列表。

**参数**：无

**返回**：项目列表，每个项目包含 id、name、companyName 等。

#### search_company

在企业库中模糊搜索企业。

| 参数    | 类型   | 必填 | 说明           |
| ------- | ------ | :--: | -------------- |
| keyword | string |  ✅  | 企业名称关键词 |

#### update_project_company_info

更新项目关联的企业信息。

| 参数        | 类型   | 必填 | 说明             |
| ----------- | ------ | :--: | ---------------- |
| projectId   | string |  ✅  | 项目 ID          |
| companyName | string |  -   | 企业名称         |
| creditCode  | string |  -   | 统一社会信用代码 |

---

### 三、进件文件管理

> 进件文件是尽调的基础材料，支持 PDF/Word/PPT/图片等格式的自动识别。

#### create_intake_file_upload_url

签发 COS 预签名上传 URL。

| 参数     | 类型   | 必填 | 说明               |
| -------- | ------ | :--: | ------------------ |
| fileName | string |  ✅  | 文件名（含扩展名） |

**返回**：`{ uploadUrl, fileKey }` — 用 uploadUrl 做 HTTP PUT 上传文件原始字节。

#### save_intake_file

落库进件文件并触发文档解析。

| 参数      | 类型   | 必填 | 说明                                         |
| --------- | ------ | :--: | -------------------------------------------- |
| fileKey   | string |  ✅  | create_intake_file_upload_url 返回的 fileKey |
| fileName  | string |  ✅  | 原始文件名                                   |
| projectId | string |  ✅  | 所属项目 ID                                  |

#### get_intake_files

获取项目下所有进件文件列表及状态。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

**状态说明**：`uploaded` → `parsing` → `pending_recognition` → `recognizing` → `completed` / `recognition_failed` / `parse_failed`

#### get_intake_file

获取单个进件文件的详细信息（含原始文件 URL 和解析后 Markdown URL）。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |
| fileId    | string |  ✅  | 文件 ID |

#### get_intake_file_content

读取进件文件解析后的 Markdown 内容。

| 参数   | 类型   | 必填 | 说明    |
| ------ | ------ | :--: | ------- |
| fileId | string |  ✅  | 文件 ID |

#### list_intake_tags

获取进件标签字典（用于打标签时约束取值）。

**参数**：无

**返回**：所有可用标签（nameEn、nameZh、description）。

#### update_intake_file_info

回写进件文件的识别结果（摘要、标签、企业主体、文档日期）。

| 参数            | 类型     | 必填 | 说明                                                         |
| --------------- | -------- | :--: | ------------------------------------------------------------ |
| fileId          | string   |  ✅  | 文件 ID                                                      |
| summary         | string   |  -   | 内容简述                                                     |
| tags            | string[] |  -   | 标签列表（取自 list_intake_tags 的 nameEn）                  |
| companySubjects | string[] |  -   | 涉及的企业主体名称                                           |
| docDate         | string   |  -   | 文档日期（yyyy-MM 格式）                                     |
| status          | string   |  -   | 识别状态推进（recognizing / completed / recognition_failed） |

---

### 四、行业分析

#### get_industry_data

获取 E0-E8 维度及风险的行业分析数据。行业码由系统从项目关联企业自动推断。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

**返回**：各 section 的已计算数据（JSON）。

#### save_industry_data

保存行业分析单个 section 的数据。

| 参数        | 类型   | 必填 | 说明          |
| ----------- | ------ | :--: | ------------- |
| projectId   | string |  ✅  | 项目 ID       |
| sectionCode | string |  ✅  | section 编码  |
| contentMd   | string |  -   | Markdown 内容 |
| contentHtml | string |  -   | HTML 内容     |

#### get_industry_reports

获取行业专项报告版本列表。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

#### save_industry_report

保存行业专项报告（多版本管理）。

| 参数         | 类型   | 必填 | 说明                 |
| ------------ | ------ | :--: | -------------------- |
| projectId    | string |  ✅  | 项目 ID              |
| content      | string |  ✅  | 报告内容（Markdown） |
| reportName   | string |  -   | 报告名称             |
| versionLabel | string |  -   | 版本标签             |

---

### 五、企业画像

#### get_profile_data

获取 13 个维度的企业画像数据。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

#### save_profile_data

保存企业画像单个 section 的数据。

| 参数        | 类型   | 必填 | 说明          |
| ----------- | ------ | :--: | ------------- |
| projectId   | string |  ✅  | 项目 ID       |
| sectionCode | string |  ✅  | section 编码  |
| contentMd   | string |  -   | Markdown 内容 |
| contentHtml | string |  -   | HTML 内容     |

#### get_profile_reports

获取企业画像报告版本列表。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

#### save_profile_report

保存企业画像专项报告。

| 参数         | 类型   | 必填 | 说明                 |
| ------------ | ------ | :--: | -------------------- |
| projectId    | string |  ✅  | 项目 ID              |
| content      | string |  ✅  | 报告内容（Markdown） |
| reportName   | string |  -   | 报告名称             |
| versionLabel | string |  -   | 版本标签             |

---

### 六、经营分析

#### get_business_data

获取 8 个维度的经营分析数据。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

#### save_business_data

保存经营分析单个 section 的数据。

| 参数        | 类型   | 必填 | 说明          |
| ----------- | ------ | :--: | ------------- |
| projectId   | string |  ✅  | 项目 ID       |
| sectionCode | string |  ✅  | section 编码  |
| contentMd   | string |  -   | Markdown 内容 |
| contentHtml | string |  -   | HTML 内容     |

#### get_business_reports

获取经营分析报告版本列表。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

#### save_business_report

保存经营分析专项报告。

| 参数         | 类型   | 必填 | 说明                 |
| ------------ | ------ | :--: | -------------------- |
| projectId    | string |  ✅  | 项目 ID              |
| content      | string |  ✅  | 报告内容（Markdown） |
| reportName   | string |  -   | 报告名称             |
| versionLabel | string |  -   | 版本标签             |

---

### 七、财务分析

#### get_finance_data

获取结构化财务分析结果（含财务报表、指标计算等）。

| 参数      | 类型   | 必填 | 说明    |
| --------- | ------ | :--: | ------- |
| projectId | string |  ✅  | 项目 ID |

**返回**：JSON 格式的财务分析数据，包含各类财务指标和报表。

#### save_finance_report

保存财务专项报告。

| 参数         | 类型   | 必填 | 说明                 |
| ------------ | ------ | :--: | -------------------- |
| projectId    | string |  ✅  | 项目 ID              |
| content      | string |  ✅  | 报告内容（Markdown） |
| reportName   | string |  -   | 报告名称             |
| versionLabel | string |  -   | 版本标签             |

---

### 八、报告生成

#### create_report

创建报告占位记录。

| 参数       | 类型   | 必填 | 说明                                                                |
| ---------- | ------ | :--: | ------------------------------------------------------------------- |
| projectId  | string |  ✅  | 项目 ID                                                             |
| reportType | string |  ✅  | 报告类型（due_diligence / industry / profile / business / finance） |
| reportName | string |  -   | 报告名称                                                            |

#### create_report_upload_url

签发报告附件上传 URL。

| 参数     | 类型   | 必填 | 说明       |
| -------- | ------ | :--: | ---------- |
| reportId | string |  ✅  | 报告 ID    |
| fileName | string |  ✅  | 附件文件名 |

#### submit_report

提交通用尽调报告（多章节树结构）。

| 参数     | 类型   | 必填 | 说明                                     |
| -------- | ------ | :--: | ---------------------------------------- |
| reportId | string |  ✅  | 报告 ID                                  |
| chapters | array  |  ✅  | 章节数组 [{ id, title, content, order }] |
| content  | string |  -   | 完整报告内容                             |

#### mark_report_generating

标记报告状态为「生成中」。

| 参数     | 类型   | 必填 | 说明    |
| -------- | ------ | :--: | ------- |
| reportId | string |  ✅  | 报告 ID |

#### mark_report_failed

标记报告状态为「生成失败」。

| 参数     | 类型   | 必填 | 说明     |
| -------- | ------ | :--: | -------- |
| reportId | string |  ✅  | 报告 ID  |
| reason   | string |  -   | 失败原因 |

#### get_report_status

查询报告当前状态。

| 参数     | 类型   | 必填 | 说明    |
| -------- | ------ | :--: | ------- |
| reportId | string |  ✅  | 报告 ID |

---

### 九、报告模板

#### search_templates

AI 智能模板匹配搜索。

| 参数    | 类型   | 必填 | 说明       |
| ------- | ------ | :--: | ---------- |
| keyword | string |  ✅  | 搜索关键词 |

#### list_report_templates

按条件筛选模板列表。

| 参数    | 类型   | 必填 | 说明                          |
| ------- | ------ | :--: | ----------------------------- |
| status  | string |  -   | 状态筛选（active / inactive） |
| keyword | string |  -   | 名称关键词                    |

#### get_report_template

获取模板详情（含完整章节大纲）。

| 参数       | 类型   | 必填 | 说明    |
| ---------- | ------ | :--: | ------- |
| templateId | string |  ✅  | 模板 ID |

#### get_enabled_templates

获取当前启用的模板列表。

**参数**：无

#### create_report_template

创建新模板。

| 参数        | 类型   | 必填 | 说明     |
| ----------- | ------ | :--: | -------- |
| name        | string |  ✅  | 模板名称 |
| description | string |  -   | 模板描述 |
| chapters    | array  |  -   | 章节大纲 |

#### toggle_template_status

启用/停用模板。

| 参数       | 类型   | 必填 | 说明    |
| ---------- | ------ | :--: | ------- |
| templateId | string |  ✅  | 模板 ID |

---

### 十、联网搜索

#### web_search

腾讯云 WSA 实时联网搜索。

| 参数      | 类型   | 必填 | 说明                  |
| --------- | ------ | :--: | --------------------- |
| query     | string |  ✅  | 搜索查询              |
| site      | string |  -   | 限定站点（如 gov.cn） |
| dateRange | string |  -   | 时间范围              |

#### web_search_enhanced

TokenHub 模型内置联网搜索。模型自主判断是否需要搜索、搜索什么关键词，基于搜索结果直接生成综合回答，响应中附带引用来源。适合需要深度分析的场景（行业调研、政策解读、企业舆情等）。

| 参数         | 类型   | 必填 | 说明                                                                 |
| ------------ | ------ | :--: | -------------------------------------------------------------------- |
| query        | string |  ✅  | 搜索问题（自然语言，模型自动提取关键词）                             |
| systemPrompt | string |  -   | 系统提示词，引导模型如何组织搜索结果                                 |
| searchSource | string |  -   | 搜索版本：lite（轻量版，更快）或 standard（标准版，更全），默认 lite |

---

## 典型工作流

### 进件 → 分析 → 报告全流程

1. **选项目**：`list_projects` 确认当前工作项目
2. **收材料**：`create_intake_file_upload_url` → HTTP PUT 上传 → `save_intake_file` 入库
3. **识材料**：轮询 `get_intake_files` 等解析完成 → `list_intake_tags` 取标签 → `update_intake_file_info` 回写识别结果
4. **做分析**：根据需要调用 `get_industry_data` / `get_profile_data` / `get_business_data` / `get_finance_data`
5. **出报告**：`create_report` → 填充内容 → `submit_report`

### 快速查询

- "查一下蓝雪科技的财务状况" → `get_finance_data`
- "蓝雪科技在什么行业" → `get_industry_data`
- "蓝雪科技的企业基本信息" → `get_profile_data`

## 注意事项

- 所有数据操作（save_*）受用户角色和租户权限控制
- 进件文件识别需等待后端解析完成（状态到 `pending_recognition`）才可操作
- 报告提交后不可修改，如需调整请创建新版本
- Token 过期后 WorkBuddy 会自动使用 refresh_token 续期
- 联网搜索适用于需要外部信息补充的场景（行业资讯、政策法规等）
