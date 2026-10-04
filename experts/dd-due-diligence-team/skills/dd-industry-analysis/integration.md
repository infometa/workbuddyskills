# 系统集成（依赖 aidd-saas MCP 工具）

> **本段为系统集成必需步骤**：数据同步（SKILL.md 第 6 步）与行业专项报告生成（SKILL.md 第 7 步）依赖本系统提供的 MCP 工具，在 aidd-saas 系统环境中工具必已注入，**必须执行，不得跳过报告生成**。
> 判断方式：环境中存在 `save_industry_data`、`save_industry_report` 等工具即视为已注入。
> 仅当脱离系统环境独立运行（工具确实不存在）时，完成第 5 步（沙箱文件）后如实说明"数据未入库，需人工上传"。

## 本段依赖的 MCP 工具清单

| 工具                       | 用途                               |
| -------------------------- | ---------------------------------- |
| `get_intake_files`         | 获取进件文件列表                   |
| `get_intake_file_content`  | 获取进件文件解析内容               |
| `save_industry_data`       | 逐 section 同步分析数据到后端      |
| `get_industry_data`        | 确认已同步数据完整性               |
| `search_templates`         | 匹配行业专项报告模板               |
| `get_industry_reports`     | 查询报告已有版本                   |
| `create_report_upload_url` | 获取 DOCX 上传地址                 |
| `save_industry_report`     | 保存行业专项报告（MD + DOCX 关联） |

**动态参数由任务 prompt 传入**：`projectId`、企业名称、贷款品种、申请额度、行业分类等，本段所有工具调用均使用 prompt 中给定的 `projectId`。

## 第 6 步：同步数据到后端

### 6.0 推送前模板核对（每个 section 都必须执行，对不上先改再推送）

**每次调用 `save_industry_data` 之前**，必须先核对生成的 `htmlContent` / `mdContent` 是否与对应 HTML 模板 `templates/{section}.html` 结构一致，**不一致必须先修改再推送，禁止直接推送不匹配的 HTML**。核对项：

1. **占位符全部替换**：对比 `templates/{section}.html` 里的 `{{PLACEHOLDER}}`，生成的 HTML 中不得残留任何未替换的占位符（如 `{{SUMMARY_TEXT}}`、`{{JUDGMENTS}}`、`{{EVIDENCE}}` 等）。
2. **结构骨架一致**：外层必须用 `<div class="ind-section">` 包裹，模板中的 `ind-section__*` 结构块（grid/metrics/insight/evidence/summary/supplement 等）必须保留，只替换占位符内容，**不得增删结构块或发明新 class**。
3. **class 名合法**：只允许使用 SKILL.md「第 5 步 · HTML 片段要求」列出的 class 名；发现 `ind-section__badge` 之类未列出的 class 必须删除并改用合法 class。
4. **表格用 `<table>`**：数据表必须用 `<table>`（宿主已定义 table/th/td 样式），不得用 `<div>` 拼表。
5. **risks 特殊要求**：`section="risks"` 时必须用 `templates/risks.html` 模板（**模板不含 `<style>`，样式由宿主页面统一定义**），用实际风险内容替换占位符，保持表格结构与 class 名不变；且 `risksJson` 必须与 `risks.html` 中的风险条目一一对应。

核对流程：读取模板 → 逐项对照生成的 HTML → 发现不一致立即修改 → 修改后再次核对 → 全部一致后才允许调用 `save_industry_data`。

每完成一个 section 的 MD + HTML 文件后，先执行 6.0 模板核对，再立即调用 MCP 工具同步到后端（不要等全部完成）：

```
save_industry_data(projectId, section, mdContent, htmlContent, e0Fields?, risksJson?)
```

- `section`：e0/e1/e2/e3/e4/e5/e6/e7/e8/risks
- `mdContent`：该 section 的 .md 文件内容
- `htmlContent`：该 section 的 .html 文件内容（**必传**，不得为空或占位文本）
- `e0Fields`：仅 e0 section 传，含 7 字段（representativeProduct, isicClassification, subIndustry, developmentCycle, chainPosition, industryTier, marketShareBasis）
- `risksJson`：仅 risks section 传，结构化风险要点数组，格式：`[{"level": "high|medium|low", "category": "分类", "title": "标题", "detail": "详情", "suggest": "建议"}]`

⚠️ **risks section 必须传 `risksJson`**，传入后系统会自动将风险要点写入「风险总览」页面。

#### save_industry_data 参数说明（逐字段）

**必填 4 项**：

| 字段          | 类型   | 约束 / 值域                                                                                              |
| ------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `projectId`   | string | 项目 ID                                                                                                  |
| `section`     | string | **仅限** `e0` / `e1` / `e2` / `e3` / `e4` / `e5` / `e6` / `e7` / `e8` / `risks`（10 个固定值，不得改名） |
| `mdContent`   | string | 该 section 的 Markdown 正文                                                                              |
| `htmlContent` | string | 该 section 的 HTML 片段（必传，基于模板生成，禁止占位文本）                                              |

**可选 2 项**：

- `e0Fields`（**仅 `section="e0"` 传**）：嵌套对象，含 7 字段（见下）
- `risksJson`（**仅 `section="risks"` 传**）：结构化风险要点数组，`[{level, category?, title, detail?, suggest?}]`，`level` 仅限 high/medium/low/note

**复杂参数：`e0Fields`（嵌套对象，仅 e0）**

```json
{
  "representativeProduct": "单晶硅片、光伏组件",
  "isicClassification": "C 制造业 → C3800 光伏设备及元器件制造",
  "subIndustry": "光伏产业链中游",
  "developmentCycle": "成长期→成熟期过渡",
  "chainPosition": "中游",
  "industryTier": "第一梯队",
  "marketShareBasis": "单晶硅片全球出货量占比"
}
```

7 字段全部为 string，**必填**。同步后后端自动标记 E0 为已确认（`confirmed: true`）。

**易错点（务必注意）**：

1. **`section` 是枚举，不是任意字符串**：只能传 10 个固定值之一，传错后端直接报错。
2. **`e0Fields` 只在 e0 section 传**：其他 section 传了会被忽略或报错。
3. **`risksJson` 只在 risks section 传**：对象数组，`level` 必填（枚举 high/medium/low/note），**不可**传 JSON 字符串或逗号分隔。
4. **`htmlContent` 必传且不能是占位文本**：禁止传"详见 Markdown"/"内容已同步"等。
5. **每完成一个 section 立即推送**：不要等全部完成再一起调用，否则前端无法实时展示。

同步后后端会自动标记 E0 为已确认（confirmed: true）。

## 第 7 步：生成行业专项报告（MD + DOCX）

全部 section 完成并同步后：

1. 调用 `get_industry_data(projectId)` 确认数据完整
2. 调用 `search_templates(intent)` 匹配报告模板，自动选择第一个候选并按章节结构生成（详见 SKILL.md「报告模板匹配」）
3. 生成报告 Markdown 内容（银行送审报告口吻），内容完整详实
4. 生成 DOCX 文件（沙箱内生成，内容与 MD 一致）
5. 调用 `get_industry_reports(projectId)` 查询已有版本，新版本号为已有最大版本号 +1（无版本则从 v1 开始）
6. 调用 `create_report_upload_url(projectId, fileName)` 获取上传地址
7. HTTP PUT DOCX 到 uploadUrl（body 为文件原始字节）
8. 调用 `save_industry_report(projectId, content, versionLabel, docxCosKey)` 保存报告

#### save_industry_report 参数说明

| 字段           | 类型   | 约束 / 说明                                                                                           |
| -------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `projectId`    | string | 项目 ID（必填）                                                                                       |
| `content`      | string | 报告完整 Markdown（必填，非摘要/大纲）                                                                |
| `versionLabel` | string | 版本标签（可选，如 `v3`，不传自动生成）                                                               |
| `docxCosKey`   | string | DOCX 的 COS key（可选，来自 `create_report_upload_url` 返回的 `cosKey`；**不传则前端无法下载 DOCX**） |

**易错点**：

1. **`docxCosKey` 必须传** `create_report_upload_url` 返回的 `cosKey`（不是 `uploadUrl`），否则前端报告列表没有 DOCX 下载。
2. **`content` 必须完整**：传完整报告 Markdown，不要只传摘要或章节大纲。
3. **版本号自增**：用 `get_industry_reports` 返回的最大版本号 +1；首次从 v1 开始。
4. **报告保存只能走 `save_industry_report`**：禁止用其他方式（通用报告生成、直接写文件等）保存，否则报告不会出现在行业分析页面的版本列表中。

⚠️ **报告保存必须使用 MCP 工具 `save_industry_report`**，禁止使用其他任何方式保存报告。

### 报告结构（模板匹配优先）

- 优先通过 `search_templates` 匹配模板，按模板的 `chapterOutline` / `chapterDetails` 生成
- 未匹配到模板时使用默认结构：

1. 行业概述（E0 行业定位）
2. 市场规模与增长（E1 + E2）
3. 发展趋势（E3）
4. 监管政策环境（E4）
5. 竞争格局与企业地位（E5 + E7）
6. 上下游产业链分析（E8）
7. 风险因素与提示（E6 + risks 风险要点）
8. 综合结论与建议

### 章节格式强制约束（影响前端渲染）

- 每个一级章节必须以 `## 章节标题` 开头（注意 ## 后有一个空格）
- 章节标题必须与模板 `chapterOutline` 顶层章节完全一致（不要自行修改/合并/拆分）
- 二级章节用 `### 子章节标题`，与模板子章节保持一致
- 章节之间不要有多余分隔线（---）或空白章节；正文不可为空
- 不要在 `##` 标题前加序号（如"一、""1."）
