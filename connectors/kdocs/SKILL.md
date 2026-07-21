---
name: kdocs
description: "操作金山文档（WPS 云文档 / Kdocs / 365.kdocs.cn / www.kdocs.cn）云文档的官方 Skill。核心能力覆盖云端新建、读取、编辑、搜索、分享、整理在线文档（智能文档、Word、Excel、PDF、PPT、演示文稿、智能表格、多维表格）及个人知识库。当用户的任务涉及云文档操作时使用，包括但不限于：写周报/日报/工作汇报、处理合同/发票、创建报名表/登记表、网页剪藏、接龙转表格、信息收集、文档总结与内容生成、改写仿写、翻译、AI PPT生成、PDF拆分导出、标签分类归档、收藏管理、碎片笔记整理、表格美化、回收站还原、知识库管理。"
homepage: https://www.kdocs.cn/latest
version: 1.4.12
metadata: {"openclaw":{"category":"kdocs","tokenUrl":"https://www.kdocs.cn/latest","emoji":"📝"},"keywords":["金山文档","金山表格","金山收藏","WPS","WPS文档","云文档","在线文档","kdocs","WPS云文档","接龙转表格","接龙","群接龙","报名表","信息收集","收集表","登记表","网页剪藏","剪藏","保存网页","网页保存到文档","保存文章","收藏文章","总结","帮我总结","帮我整理","帮我写","帮我翻译","帮我做PPT","翻译文档 - 做PPT - 生成PPT - 培训课件 - 方案展示 - 项目展示","文档总结","内容生成","改写","仿写","翻译","文档翻译","AI PPT","PPT","演示文稿","幻灯片","PDF","拆分PDF","导出PDF","Word","Excel","表格","Markdown","碎片整理","笔记整理","表格优化","文档处理","文件处理","办公助手","文档助手","周报","日报","工作汇报","合同","发票"],"file_types":["pdf","doc","docx","xlsx","xls","pptx","ppt","otl","ksheet","dbt","jpg","jpeg","png","bmp","gif","webp","url","md","txt","html"],"category":"productivity"}
---

# 金山文档 Skill 使用指南

金山文档 Skill 提供了一套完整的在线文档操作工具，支持创建、查询、读取、编辑、分享、移动多种类型的在线文档。

## 严格规则

### 禁止（NEVER）

- 上传写入等接口需传入的 `content_base64` 可能非常大（编码后 >1 MB），禁止在对话中逐 token 生成 Base64 字符串，用脚本完成文件读取、编码和传参

### 必须（MUST）

- 不可逆操作（delete/close 类）执行前必须向用户确认
- 写操作完成后必须用独立读取请求验证实际结果（不信任 `code: 0`）
- 创建文档并验证通过后，必须调用 `get_file_link` 获取链接并展示给用户
- 通过 `--file` 或脚本创建的临时 JSON 文件（如 `payload.json`、`temp.json`），在整个操作流程结束后必须删除，避免残留在用户工作目录

---

## 调用格式

通过 MCP function call 直接构造 JSON，无需处理引号或转义：

```json
{"name": "otl.insert_content", "arguments": {"file_id": "xxx", "content": "hello", "format": "markdown", "mode": "append"}}
{"name": "read_file_content", "arguments": {"drive_id": "xxx", "file_id": "xxx", "format": "markdown", "include_elements": ["all"]}}
```

以下工具不可逆，调用前必须向用户确认（详细约束见各工具参考文档的「操作约束」区）：

`otl.block_delete`、`dbsheet.delete_sheet`、`kwiki.close_knowledge_view`、`sheet.delete_sheets`、`sheet.delete_range`、`dbsheet.delete_view`、`dbsheet.delete_fields`、`cancel_share`、`kwiki.delete_item`、`sheet.delete_protection_ranges`、`dbsheet.delete_records`、`sheet.delete_data_validations`、`sheet.delete_conditional_format_rules`、`sheet.delete_float_images`、`sheet.delete_filters`、`dbsheet.sheet_batch_delete`、`dbsheet.permission_delete_roles_async`

---

## 能力范围

### 操作域路由

Agent 首先判定用户请求的操作域：

| 操作域 | 触发场景 | 路由 |
|--------|---------|------|
| 创建/写入 | 新建文档/编辑内容/上传文件 | **必读** `references/file-writing-guide.md` |
| 读取 | 读取/提取/导出文档内容 | **必读** `references/file-reading-guide.md` |
| 定位文件 | 搜索/按链接找文件/浏览目录 | **必读** `references/file-locating-guide.md` |
| 文件管理 | 移动/重命名/分享/标签/收藏/回收站 | → `references/drive.md` |
| 文档专项功能 | 格式/样式/导出/转换/数据校验等 | 按文档类型查下方表 → 对应 reference |
| AI 生成 | AI 做PPT/生成演示文稿 | → `references/aippt.md` |
| 知识库 | 知识库空间/导入/整理 | → `references/kwiki.md` |

### 支持的文档类型

| 类型 | 别名 | 文件后缀 | 说明 | 详细参考 |
|------|------|----------|------|----------|
| **智能文档** 首选 | ap | .otl | 排版美观，支持丰富组件 | `references/otl.md` — 页面、文本、标题、待办等元素操作 |
| 表格 | et / Excel | .xlsx | 数据表格专用 | `references/sheet.md` — 工作表管理、范围数据获取、批量更新 |
| PDF文档 | pdf | .pdf | PDF 文档专用 | `references/pdf.md` — PDF 创建与内容读取 |
| 文字文档 | wps / Word | .docx | 传统格式 | `references/wps.md` — Word 文档创建与内容操作 |
| 演示文稿 | wpp | .pptx | PPT 文档专用 | `references/wpp.md` — 幻灯片主题字体和配色设置、下载和导出 |
| 智能表格 | as | .ksheet | 结构化表格，支持多视图、字段管理 | `references/sheet.md` — 工作表管理、范围数据获取、批量更新 |
| 多维表格 | db / dbsheet | .dbt | 多数据表、丰富字段类型与视图（表格/看板/甘特等） | `references/dbsheet.md` — 支持数据表/视图/字段/记录的完整增删改查，含表单视图、父子记录、分享协作、高级权限与 Webhook |

### 高频流程指引

#### 创建并写入文档

执行顺序：
1) 先按 `references/file-locating-guide.md` 获取目标目录 `drive_id`(可选)、`parent_id`(可选)。
2) 再按 `references/file-writing-guide.md` 选择文档类型与写入路径。
字段传递：步骤 1 获取 `drive_id`(可选)、`parent_id`(可选)，作为步骤 2 的输入，执行"新建写入"流程。

#### 上传本地文件到云盘

执行顺序：
1) 先按 `references/file-locating-guide.md` 获取目标目录 `drive_id`(可选)、`parent_id`(可选)、`file_id`(可选)。
2) 再按 `references/file-writing-guide.md` 的"本地文件上传（upload_file）"路径调用上传能力（新建上传或覆盖更新）。
字段传递：新建上传使用步骤 1 的 `drive_id`(可选)、`parent_id`(可选) + `name`；覆盖更新使用步骤 1 的 `file_id` 。

#### 搜索定位文档

工具说明：`search_files(keyword="关键词", type="all", page_size=20)`，获取 `file_id`、`drive_id` 供后续链路使用。
详细参数与返回结构见 `references/drive/search.md`。

### 更多操作流程

| 流程 | 说明 | 详细参考 |
|------|------|---------|
| AI 生成演示文稿（全文） | aippt.execute 单接口全文生成链路：两次调用完成需求澄清与生成，支持主题/文档两种来源，固定使用 html 模式 | `references/workflows/aippt-whole.md` |
| 网页剪藏 | 抓取网页内容并自动保存为智能文档 | `references/workflows/web-scrape.md` |
| 搜索-读取-汇报撰写 | 搜索多份文档、提取信息、汇总撰写新报告 | `references/workflows/search-read-report.md` |
| 定期读取与播报 | 定期读取指定文档，提取关键信息生成摘要 | `references/workflows/periodic-read-summary.md` |
| 智能分类整理 | 列出目录，按内容或指定维度分类创建文件夹并归档 | `references/workflows/smart-classify.md` |
| 精准搜索与风险排查 | 在特定目录批量搜索文档，逐一读取分析，汇总到新文档 | `references/workflows/precise-search-analysis.md` |
| 云文档导入幻灯片 | 将外部 PPTX 文件中的指定幻灯片导入到已有演示文稿中 | `references/workflows/import-slides.md` |
| 接龙转表格 | 识别接龙文本内容，自动提取并转为在线表格 | `references/workflows/jielong-to-table.md` |
| 信息收集表单生成 | 根据用户需求自动设计并创建信息收集表格 | `references/workflows/form-generator.md` |
| 知识智能整理 | 对知识库中的零散内容进行智能化整理和结构化重组 | `references/workflows/knowledge-format.md` |
| 知识一键存入 | 将各类内容（网页、文件、文本）一键保存到知识库 | `references/workflows/knowledge-save.md` |
| 表格美化与数据规范 | 读取表格数据，进行格式美化、数据规范化和样式调整，并通过条件格式、数据校验、区域权限固化规则 | `references/workflows/table-beautify.md` |

---

## 错误速查

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `400006` / 鉴权失败 | Token 过期或连接器授权失效 | 告知用户在连接器管理中断开金山文档连接器，重新连接以刷新授权 |
| `429001` / 限频 | 请求过于频繁，响应含**限频恢复时间** | 立即停止命令调用，直到达到恢复时间；禁止立即重试、换参、换子命令连续请求 |
| `429002` / 熔断 | 多因短时间内连续触发 `429001` ，响应含**熔断持续时间** | 熔断时长内零请求，期满再试；重新规划任务避免请求过频 |
| 搜索无结果 | 关键词过精确 / 索引延迟 | 缩短关键词 / 等待 3-5 秒重试 |
| 读取内容为空 | 文件无内容或格式不支持 | 确认文件非空且后缀正确 |
| `read_file_content` 对 .csv 长时间 `running` | CSV 格式不支持 | 勿对 .csv 调用 `read_file_content`，建议用户转为 .xlsx 后用 `sheet.*` 读取 |
| 创建文件失败 | 文件名后缀不正确 | 检查后缀：`.otl` / `.docx` / `.xlsx` / `.ksheet` / `.dbt` / `.pdf` / `.pptx` |
| 移动文件失败 | 目标文件夹不存在 | 先搜索确认或创建文件夹 |
| HTTP 5xx / 超时 | 服务端故障 | 等 3 秒重试 1 次 |
| 验证不通过（回读值与预期不符） | 写入未生效或延迟 | 等 2 秒重新验证，仍不通过则报告用户 |
| 工具调用失败需判断是否可重试 | 不同工具幂等性不同 | 查看该工具参考文档「操作约束」区的幂等性说明，幂等工具可安全重试，非幂等工具须先确认状态 |

---

## 安全约束

- 凭据由连接器管理，Skill 自身不存储、不记录，禁止在对话中暴露 Token
- 无状态代理，不缓存任何文档内容或业务数据
- 仅在用户主动发起操作时调用对应 API
