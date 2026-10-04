# 智能文档（otl）工具完整参考文档

金山文档智能文档（otl）提供了专属的内容写入接口，支持以 Markdown 格式向文档插入内容（标题、文本、列表等），系统自动转换为富文本格式。

---

## 前置说明（重要）
当终端为 PowerShell 时，为避免转义问题，必须按以下方式传入 JSON 参数。
### JSON 参数传递方式
#### 方式一：`--%` 内联（适合简短参数）
PowerShell 中用 `--%` 停止解析，双引号用 `\"` 转义：

示例
```powershell
mcporter call kdocs-workbuddy otl.block_query --args '{\"file_id\":\"cqTNWO4EMAn9\",\"params\":{\"blockIds\":[\"doc\"]}}'
```
#### 方式二：临时文件（推荐，适合大参数）
先写入 `temp.json`，再读取并转义后传给 `--args`：

示例
```powershell
$json = Get-Content -Raw -Encoding UTF8 .\temp.json
$jsonEscaped = $json -replace '"', '\"'
mcporter call kdocs-workbuddy otl.block_insert --args "$jsonEscaped"
```

## 通用说明

### 智能文档特点

- **推荐度**：⭐⭐⭐ **首选文档格式**
- 排版美观，支持标题、列表、待办、表格、分割线等丰富块组件
- 适合图文混排、报告撰写、知识文档、会议纪要等场景
- 是网页剪藏（`scrape_url`）的默认输出格式

### 新建并写入

新建空白智能文档 → `create_empty_file`：`name` 只写文件名，传 `file_extension=otl`。
新建智能文档并写入 → `create_file_with_content`：`name` 只写文档名，传 `file_extension: "otl"` 与 `content`（Markdown 正文；参数与失败补写见 `drive/create_file_with_content`）。

`.otl` 不支持 `upload_replace_file` 覆盖；新建并写入内容用 `create_file_with_content`，已有文档追加用 `otl.insert_content`。

```json
{
  "name": "项目周报",
  "file_extension": "otl",
  "content": "# 项目周报\n\n## 概述\n\n本季度销售额同比增长 15%。"
}
```

### 读取智能文档

读取内嵌图片（非独立 `.png`/`.jpg` 文件）→ 见本文 **常用工作流 → 读取智能文档内嵌图片**。

#### 首选方式：`otl.block_query`（结构化读取）

使用 `otl.block_query` 查询文档块结构与内容，能完整获取文档的层级信息和全部块类型。传入 `params: { blockIds: ["doc"] }` 可获取全文：

```json
{
  "file_id": "file_otl_001",
  "params": { "blockIds": ["doc"] }
}
```

#### 备选方式：`read_file`（Markdown 导出）

> ⚠️ `read_file` 对智能文档存在**内容遗漏风险**——部分组件类型（如嵌入表格、附件、特殊块）可能在转换过程中丢失。**仅在需要将文档导出为 Markdown 格式时使用**，日常读取和编辑前的内容确认应优先使用 `otl.block_query`。

**图片导出**：默认导出的 Markdown 不含图片链接，仅显示占位符。需要图片时传 `enable_upload_medias: true`（仅 `format=markdown` 或 `kdc` 时生效），图片 URL **有效期约 10 分钟**——导出完成后须立即告知用户链接有时效限制，并询问是否需要下载。

### 写入/更新已有智能文档

已有文档追加/前置/替换正文 → `otl.insert_content`（`mode` 见 `otl/insert_content.md`）。块级编辑 → `otl.block_query` → `otl.block_delete` / `otl.block_insert` / `otl.block_update`。定位目标文件见 `file-locating-guide`。

---

## 一、内容写入与转换

> 整篇 Markdown/HTML 写入与 HTML/Markdown 转块数据

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`otl.insert_content`](otl/insert_content.md) | 向智能文档插入 Markdown/HTML 内容 | `url`\|`link_id`\|`file_id`, `content` |
| [`otl.convert`](otl/convert.md) | 将 HTML/Markdown 转换为智能文档块结构 | `url`\|`link_id`\|`file_id`, `params` |

## 二、块级操作

> 按 block id 定位进行查询、插入、更新、删除

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`otl.block_insert`](otl/block_insert.md) | 向智能文档插入一个或多个块 | `url`\|`link_id`\|`file_id`, `params` |
| [`otl.block_delete`](otl/block_delete.md) | 删除智能文档中一个或多个块区间 | `url`\|`link_id`\|`file_id`, `params` |
| [`otl.block_query`](otl/block_query.md) | 查询智能文档指定块的结构与内容 | `url`\|`link_id`\|`file_id`, `params` |
| [`otl.block_update`](otl/block_update.md) | 更新智能文档指定块的内容或属性 | `url`\|`link_id`\|`file_id`, `params` |

## 常用工作流

#### 读取智能文档内嵌图片

> 🎯 **读取智能文档内嵌图片时，禁止仅用默认 `read_file`（会得到 `![image]()` 空占位）。**

**触发识别**：用户要求读取/查看/下载 **智能文档（.otl）内的图片** 时走此流程（含表格单元格内 picture、文档封面等）。

**路径 A（首选，Markdown 中带图）**：

```json
{"name": "read_file", "arguments": {
  "url": "https://www.kdocs.cn/l/xxx",
  "enable_upload_medias": true
}}
```

- 成功：`content` 中 `![image](https://...)` 含临时 URL（**约 10 分钟有效**），须告知用户时效并询问是否下载。
- 若仍为 `![image]()`：检查是否遗漏 `enable_upload_medias=true`，或改走路径 B。

**路径 B（按块下载原图）**：`otl.block_query`（`params: { blockIds: ["doc"] }`）→ 找目标 `type: "picture"` 节点的 `attrs.sourceKey` → `download_attachment`（`attachment_id` 填该值，文档标识沿用块查询时的值）。

**禁止**：仅调用默认 `read_file` 后告知「无法读取图片」；收到 warnings 建议 `otl.block_query` 时必须继续尝试路径 A 或 B。

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 新建文档并写入内容 | 见上文「新建并写入」 |
| 向已有文档追加/前置正文 | `otl.insert_content`（`mode=prepend` / `append`；全文替换用 `mode=replace`，见 `otl/insert_content.md`） |
| 向已有文档追加/插入表格 | 末尾追加 → `otl.insert_content`（`format=markdown` + 管道表，**禁止 html**）；指定块位置 → `otl.block_query` → `otl.convert`（markdown）→ `otl.block_insert`（约束见 `otl/insert_content.md`、`otl/convert.md`） |
| 读取现有文档内容 | `otl.block_query`（`params: { blockIds: ["doc"] }` 获取全文） |
| **读取/下载文档内图片** | 见本文「常用工作流 → 读取智能文档内嵌图片」 |
| 导出文档为 Markdown | `read_file`（可能遗漏部分组件内容；需要图片时传 `enable_upload_medias: true`，URL 有效期约 10 分钟） |
| 精确修改文档块 | `otl.block_query` → `otl.block_delete` / `otl.block_insert` |
| 修改文档标题 | `otl.block_query`（`params: { blockIds: ["doc"] }`）获取 title 块 ID → `otl.block_update`（`update_content`，`content` 传 text 节点） |
| 向文档插入图片 | `upload_attachment`（获取 `object_id`）→ `otl.block_insert`（`type: "picture"`，`sourceKey` 设为 `object_id`，其余属性见 otl/node.md） |
| 下载文档中的图片/附件 | `otl.block_query` → 找到目标块的 `sourceKey` → `download_attachment`（`attachment_id` 为 `sourceKey`） |
| 获取文档封面图 | `otl.block_query`（`params: { blockIds: ["doc"] }`）→ 查看返回的 `cover.sourceKey`；可通过 `download_attachment` 下载封面图资源 |
| 设置文档封面图 | `upload_attachment`（获取 `object_id`）→ `otl.block_update`（`update_attrs`，`blockId: "doc"`，`attrs.cover.sourceKey` 设为 `object_id`） |
| 清除文档封面图 | `otl.block_update`（`update_attrs`，`blockId: "doc"`，`attrs: { cover: {} }`） |
| 外部富文本段落转块后插入（非表格） | `otl.convert`（html/markdown）→ `otl.block_insert` |
