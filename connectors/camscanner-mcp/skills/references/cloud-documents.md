# 云文档管理参考

本组工具不需要统一执行“上传→转换”。使用用户已明确的文档 ID 或当前搜索结果；只在目标或目录存在歧义时询问，已明确的选择不重复确认。

## create_cloud_doc — 保存到云端

将上传的文件或处理结果保存到用户的扫描全能王账号，可指定保存到特定文件夹。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_ids` | string[] | 是 | 文件 ID 列表（来自上传完成或处理结果） |
| `file_type` | string | 是 | 文件类型：pdf/word/excel/ppt/image/md/html |
| `title` | string | 否 | 文档标题，不传则自动生成 |
| `dir_id` | string | 否 | 目标文件夹 ID（通过 `query_cloud_dir` 获取，优先级高于 dir_name） |
| `dir_name` | string | 否 | 目标文件夹名称（按名称匹配，匹配失败时降级到根目录） |
| `root` | boolean | 否 | 保存到根目录（显式传入时跳过目录查询） |

> **注意**：`file_ids` 必须是 **JSON 数组**格式，例如 `["file_abc.jpg"]` 或 `["file_1.jpg", "file_2.jpg"]`。**禁止**使用对象形式如 `{"item": "..."}` 或其他非数组结构。

**智能命名规则**：保存到云端时，Agent 应根据用户意图和文件内容生成简洁标题（≤20字）。
- 示例：用户说"把这张发票转成 Excel" → `title: "发票转Excel"`
- 示例：多张扫描图片生成 PDF → `title: "扫描文档合并"`
- 无法推断时不传 title，由服务端自动生成


**产物数量与返回结构**：

- `file_type=image`：多个图片 ID 可创建一个多页图片文档。
- PDF/Word/Excel/PPT/Markdown/HTML：一个文件创建一个云文档；传多个文件会分别创建多个文档，不会合并内容。
- 单文档返回 `doc_id`（Web 承接页 URL）、`title`、可能的 `dir_id`、`dir_title`、`warning`；多个 Office/PDF 文档可能返回 `results[]`，逐项读取，不能寻找虚构的 `cloud_doc_id`。
- 展示实际链接、标题和位置，转述 warning。缺少目录字段时按返回契约判断根目录，字段缺失或原因未知不能自行推断为“文件夹不存在”。
- 保存超时或失败时可能已创建部分文档，按错误参考先核查，不能盲目重复创建。


## search_cloud_doc — 搜索云文档

搜索用户云端的 CamScanner 文档。支持关键词搜索、时间范围过滤、文档类型过滤，可组合使用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | 否 | 搜索关键词（多个词用空格分隔，OR 语义） |
| `search_scope` | string | 否 | 搜索范围：`title`（默认，标题+页标题+备注）或 `full`（含 OCR 全文） |
| `doc_type` | string | 否 | 文档类型过滤：pdf/word/excel/ppt/image/markdown/html |
| `start_time` | int | 否 | 起始时间（Unix 时间戳，秒） |
| `end_time` | int | 否 | 截止时间（Unix 时间戳，秒） |
| `limit` | int | 否 | 返回数量上限（默认 5，最大 50） |

**返回数据结构**：

```json
{
  "docs": [
    {
      "doc_id": "https://www.camscanner.com/file/pdfDetail?id=abcdef123456789012345678_pdfx0",
      "cs_doc_id": "abcdef123456789012345678_pdfx0",
      "title": "合同扫描件",
      "create_time": 1724500000,
      "modify_time": 1724600000,
      "dir_id": "folder_abc",
      "dir_title": "工作文档"
    }
  ],
  "total": 3
}
```

**Agent 行为规范**：
- 用户说"找/搜/查我的文档"时，走 `search_cloud_doc`，**不走** convert/enhance 等文件处理流程
- 多关键词用空格分隔，采用 OR 语义
- 未传 keyword 时返回最近文档列表
- 默认返回 5 条，用户需要更多时增加 `limit`
- 时间意图应转换为 Unix 时间戳传入 `start_time`/`end_time`，而非作为关键词
- 用户未指定搜索范围时，先 `search_scope=title`，无结果再用 `search_scope=full` 查询一次；用户明确指定范围时遵守其要求。无匹配只说明本次未找到，不能证明文档不存在或保存未发生。

**Agent 展示规范（强制）**：向用户呈现搜索结果时，**必须**至少包含以下四列信息：

| 列名 | 来源 | 说明 |
|------|------|------|
| 标题 | `title` 字段 | 文档标题 |
| 类型 | 从 `doc_id`（URL）路径推断 | `/pdfDetail` → PDF，`/markdownDetail` → Markdown，`/detail` → 扫描件/图片 |
| 所在目录 | `dir_title` 字段 | 文档所在文件夹（空值展示为"根目录"） |
| 链接 | `doc_id` 字段 | 可点击的 Web 承接页地址 |

> Agent 禁止省略类型列或仅展示标题和链接。

## download_cloud_doc — 下载云端文档

按 `doc_id` 下载云端文档。Office 类文档直接下载原始文件，图片类文档默认导出为 PDF。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | string | 是 | 云端文档 ID（来自 `search_cloud_doc` 返回的 `cs_doc_id`，或从 doc_id URL 中提取） |
| `format` | string | 否 | 图片类文档的导出格式：`pdf`（默认）或 `zip`（导出原始 JPG 打包） |

输出：`{file_id, download_url, file_size, file_type}`。

**Agent 行为规范**：
- 用户说"下载"、"导出"、"保存到本地"某个云文档时使用
- `doc_id` 使用 `search_cloud_doc` 结果中的 `cs_doc_id` 字段
- Office/PDF 文档保留原格式；图片类文档默认导出 PDF，用户明确要原图时使用 `format=zip`。
- 获得 `download_url` 后还需实际下载并核验本地文件；没有宿主文件写入能力时只交付链接。

## query_cloud_dir — 查询云端文件夹

查询用户云端文件夹目录树，返回精简的目录结构。

无必填参数。

输出：
```json
{
  "dirs": [
    {
      "dir_id": "B7F4FCBC...",
      "title": "工作文档",
      "create_time": 1787303650027,
      "doc_count": 5,
      "dirs": [...]
    }
  ],
  "total": 3
}
```

**Agent 行为规范**：
- 用户说"我的文件夹"、"列出目录"、"文件夹列表"时使用
- 需要解析文件夹名称或缺少目标 ID 时查询。已有明确有效 ID、使用 `create_cloud_doc(dir_name=...)` 或明确操作根目录时，不强制重复查询。
- 以树形结构向用户展示结果

## move_cloud_doc — 移动文档到文件夹

将一个或多个文档移动到指定文件夹。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `doc_ids` | string[] | 是 | 要移动的文档 ID 列表 |
| `dir_id` | string | 否 | 目标文件夹 ID（与 root 二选一，通过 `query_cloud_dir` 获取） |
| `root` | boolean | 否 | 移动到根目录（与 dir_id 互斥） |

**Agent 行为规范**：
- 用户说"移动文档"、"整理到文件夹"、"归类"时使用
- 仅在需要解析目标文件夹时查询 `query_cloud_dir`；移到根目录使用 `root=true`，不传 `dir_id`。
- `doc_ids` 使用 `search_cloud_doc` 结果中的 `cs_doc_id` 字段
- 移动完成后向用户报告目标文件夹名称（而非 dir_id）

## 目标与权限

- 搜索命中多个合同或多个同名目录时，不默认选择第一项执行移动。结合上下文确定；仍有歧义时询问具体目标。
- 移动只覆盖用户要求的文档和目录，不扩大到全部搜索结果。结果成功后报告实际目标目录名称。
- 文档 Web 链接、临时下载地址和原始 `cs_doc_id` 用途不同；不要用其中一个替代另一个，也不保证 Web 链接免登录公开访问。
