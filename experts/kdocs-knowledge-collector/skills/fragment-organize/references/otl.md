# 智能文档（otl）工具完整参考文档

金山文档智能文档（otl）提供了专属的内容写入接口，支持以 Markdown 格式向文档插入内容（标题、文本、列表等），系统自动转换为富文本格式。

---

## 前置说明（重要）
PowerShell 下复杂 JSON（含中文、数组、大对象）优先用 `--file`；完整规则见 SKILL.md「调用格式」。otl 示例：`kdocs-cli otl block-query --file params.json`。

## 通用说明

### 智能文档特点

- **推荐度**：⭐⭐⭐ **首选文档格式**
- 排版美观，支持标题、列表、待办、表格、分割线等丰富块组件
- 适合图文混排、报告撰写、知识文档、会议纪要等场景
- 是网页剪藏（`scrape_url`）的默认输出格式

### 新建并写入

新建空白智能文档 → `create_empty_file`：后缀 `.otl`。
新建智能文档并写入 → `create_file_with_content`：`name` 后缀 `.otl`，传 `content`（Markdown 正文；参数与失败补写见 `drive/create_file_with_content`）。

`.otl` 不支持 `upload_replace_file` 覆盖；新建并写入内容用 `create_file_with_content`，已有文档追加用 `otl.insert_content`。

```json
{
  "name": "项目周报.otl",
  "content": "# 项目周报\n\n## 概述\n\n本季度销售额同比增长 15%。"
}
```

### 读取智能文档

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

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 新建文档并写入内容 | 见上文「新建并写入」 |
| 向已有文档追加/前置正文 | `otl.insert_content`（`mode=prepend` / `append`；全文替换用 `mode=replace`，见 `otl/insert_content.md`） |
| 读取现有文档内容 | `otl.block_query`（`params: { blockIds: ["doc"] }` 获取全文） |
| 导出文档为 Markdown | `read_file`（可能遗漏部分组件内容；需要图片时传 `enable_upload_medias: true`，URL 有效期约 10 分钟） |
| 精确修改文档块 | `otl.block_query` → `otl.block_delete` / `otl.block_insert` |
| 修改文档标题 | `otl.block_query`（`blockIds: ["doc"]`）获取 title 块 ID → `otl.block_update`（`update_content`，`content` 传 text 节点） |
| 向文档插入图片 | `upload_attachment`（获取 `object_id`）→ `otl.block_insert`（`type: "picture"`，`sourceKey` 设为 `object_id`，其余属性见 otl/node.md） |
| 下载文档中的图片/附件 | `otl.block_query` → 找到目标块的 `sourceKey` → `download_attachment`（`attachment_id` 为 `sourceKey`） |
| 获取文档封面图 | `otl.block_query`（`params: { blockIds: ["doc"] }`）→ 查看返回的 `cover.sourceKey`；可通过 `download_attachment` 下载封面图资源 |
| 设置文档封面图 | `upload_attachment`（获取 `object_id`）→ `otl.block_update`（`update_attrs`，`blockId: "doc"`，`attrs.cover.sourceKey` 设为 `object_id`） |
| 清除文档封面图 | `otl.block_update`（`update_attrs`，`blockId: "doc"`，`attrs: { cover: {} }`） |
| 外部内容转块后插入 | `otl.convert` → `otl.block_insert` |
