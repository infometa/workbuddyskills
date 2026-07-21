# PDF 文档（pdf）工具完整参考文档

金山文档 PDF 工具适合处理"最终交付版"文档，包括查询页数、抽取指定页和格式转换。

---

## 通用说明

### PDF 文档特点

- **推荐度**：⭐⭐ 适合作为最终输出格式，不适合作为过程编辑格式
- PDF 适合作为最终分发、归档和打印格式，不适合高频在线编辑
- 如果目标是"持续编辑内容"，优先使用 `otl`、`docx`、`sheet`、`pptx`
- 如果目标是"输出最终版"、"归档"、"打印"或"扫描件整理"，优先考虑 PDF
- 常规创建或覆盖上传 PDF 时，使用通用工具 `upload_file`
- 当需求是"处理 PDF 本身"时，再使用 `pdf.*` 专属工具

### 读取 PDF 内容

通过 `read_file_content` 读取，系统会自动提取文本并转为 Markdown：

```json
{
  "file_id": "file_pdf_001"
}
```

返回内容更适合"阅读理解、摘要、信息提取"，不适合依赖版式精确保真的任务。

### 创建或写入 PDF 内容

通过 `upload_file` 上传 PDF 文件；若传入已有 `file_id`，则执行覆盖更新：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_id": "string",
  "size": 1024,
  "hashes": [
    { "sum": "string", "type": "sha256" }
  ]
}
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 合同签署 | 用于分发和归档最终版文件 |
| 财务报表 | 保持固定版式，便于打印 |
| 资料归档 | 长期保存、减少误编辑 |
| 最终交付 | 将 Word/Excel/PPT 或 Markdown 输出为 PDF |

### 注意事项

- 写入 PDF 为全量覆盖，不支持像文档类文件那样的局部编辑
- 若需要频繁编辑正文，建议先使用 `otl`、`docx`、`sheet` 或 `pptx`，完成后再导出为 PDF
- `pdf.extract_pdf_pages` 的页码为 1-based，即第一页是 `1`

### 工具选择建议

| 目标 | 推荐工具 |
|------|------|
| 只想读取 PDF 文本内容 | `read_file_content` |
| 想知道 PDF 一共有多少页 | `pdf.get_pdf_page_count` |
| 想从 PDF 中抽取部分页面生成新 PDF | `pdf.extract_pdf_pages` |
| 想把 PDF 转成可编辑文档（docx/xlsx/pptx） | `pdf.convert`（默认付费额度，VIP 不足时降级 `is_free_convert=true` 重试） + `pdf.convert_query` |
| 想做 PDF 全文翻译并导出（单语/双语） | `pdf.translate_full_file`（必要时 `pdf.get_translate_progress` / `pdf.cancel_translate`） |

---

## 一、读取 PDF 内容

### 1. read_file_content

#### 功能说明

读取指定文件的内容，系统会自动提取文本并转为 Markdown 格式。

**适用于**：阅读理解、摘要、信息提取。

#### 调用示例

```json
{
  "file_id": "file_pdf_001"
}
```

#### 参数说明

- `file_id` (string, 必填): 文件 ID

#### 模型使用建议

- 当用户说"帮我读一下这个 PDF 讲了什么"时，优先使用这个工具
- 返回内容更适合"阅读理解、摘要、信息提取"，不适合依赖版式精确保真的任务

---

## 一、页面查询

> PDF 基本信息与页数

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`pdf.get_pdf_page_count`](pdf/inspect.md) | 查询 PDF 总页数 | `file_id` |

## 二、拆分与合并

> 抽取、拆分、合并 PDF 页面

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`pdf.extract_pdf_pages`](pdf/split_and_merge.md) | 提取指定页并生成新 PDF | `file_id`, `ranges` |
| [`pdf.split`](pdf/split_and_merge.md) | 将 PDF 按固定页数间隔拆分为多个文件 | `file_id`, `dc_interval` |
| [`pdf.split_query`](pdf/split_and_merge.md) | 查询 PDF 拆分任务进度 | `jobid` |
| [`pdf.merge`](pdf/split_and_merge.md) | 将多个 PDF 文件合并为一个 | `files` |
| [`pdf.merge_query`](pdf/split_and_merge.md) | 查询 PDF 合并任务进度 | `jobid` |

## 三、格式转换

> PDF 与其他格式之间的异步转换与状态轮询

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`pdf.convert`](pdf/convert.md) | 发起 PDF 转 Office 转换任务 | `file_id`, `to_format` |
| [`pdf.convert_query`](pdf/convert.md) | 查询 PDF 转换任务进度与结果 | `jobid`, `file_id` |

## 四、全文翻译

> PDF 全文翻译导出与状态轮询

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`pdf.translate_full_file`](pdf/translate.md) | 提交 PDF 全文翻译导出任务 | `file_id`, `file_source`, `header`, `body`, `from_lang`, `to_lang`, `engine_type`, `pages`, `output_file_mode`, `output_file_two_lang` |
| [`pdf.get_translate_progress`](pdf/translate.md) | 查询全文翻译任务进度 | `file_id`, `task_id` |
| [`pdf.cancel_translate`](pdf/translate.md) | 取消全文翻译任务 | `file_id` |

## 常用工作流

#### PDF 文档操作

按用户需求选择对应操作：

**读取 PDF 内容**：
1. `search_files` 或 `get_share_info` 定位文档 → 获取 `file_id`、`drive_id`
2. `read_file_content(file_id=..., format="markdown")` → 返回 Markdown 文本
> 适合摘要、信息提取等场景；复杂排版可能有精度损失

**查询 PDF 页数**：
1. `search_files` 定位 PDF → 获取 `file_id`
2. `pdf.get_pdf_page_count(file_id=...)` → 返回总页数

**提取指定页面**：
1. `search_files` 定位 PDF → 获取 `file_id`
2. `pdf.get_pdf_page_count` 确认总页数，校验用户请求的页码是否越界
3. `pdf.extract_pdf_pages(file_id=..., ranges=[{from:1,to:1},{from:5,to:8}])` → 生成新 PDF
> 页码 1-based；`ranges` 为 `{from, to}` 对象数组，多段按顺序合并；提取结果为临时下载链接

**按固定页数拆分**：
1. `search_files` 定位 PDF → 获取 `file_id`
2. `pdf.get_pdf_page_count` 确认总页数
3. `pdf.split(file_id=..., dc_interval=N, file_name="章节")` 发起拆分，返回 `jobid`
4. `pdf.split_query(jobid=...)` 轮询进度，直到 `progress=100`
5. 从 `result_files` 读取各子文件（file_id、name、download_url）
> `dc_interval` 为每 N 页拆分一次；结果存入金山文档 `我的云文档/应用/PDF拆分`

**合并多个 PDF**：
1. `search_files` 定位所有待合并 PDF → 获取各 `file_id`
2. `pdf.merge(files=[{file_id:"..."}, {file_id:"..."}], file_name="完整报告")` 发起合并，返回 `jobid`
3. `pdf.merge_query(jobid=...)` 轮询进度，直到 `progress=100`
4. 从 `result_files` 读取合并结果（file_id、name、download_url）
> `files` 数组按顺序合并，至少 2 个；结果存入金山文档 `我的云文档/应用/PDF合并`

**转换为可编辑文档（Word/Excel/PPT）**：
1. `search_files` 定位 PDF → 获取 `file_id`
2. `pdf.convert(file_id=..., to_format="docx|xlsx|pptx", ...)` 发起转换任务（默认 `is_free_convert=false`）
3. 若步骤 2 返回 `code=400100` 或含 `VipLevelNotEnough` 等会员不足提示，使用相同参数、仅将 `is_free_convert=true` 重新调用 `pdf.convert`（免费额度最多处理前 5 页）
4. `pdf.convert_query(jobid=..., file_id=..., fname=...)` 轮询进度，直到 `progress=100`
5. 从 `result_files` 读取转换结果（类型、大小、下载 URL）

**全文翻译导出（双语/指定语言）**：
1. `search_files` 定位 PDF → 获取 `file_id`
2. `pdf.translate_full_file(file_id=..., from_lang=..., to_lang=..., output_file_mode=..., output_file_two_lang=...)`
3. 若 `pdf.translate_full_file` 返回任务态，再用 `pdf.get_translate_progress(file_id=..., task_id=...)` 轮询
4. 任务需中止时调用 `pdf.cancel_translate(file_id=...)`

**创建/上传 PDF**：
- `upload_file(drive_id=..., parent_id=..., name="xxx.pdf", content_base64=...)` 直接上传
- 更新已有 PDF：`upload_file(file_id=..., content_base64=...)` 全量覆盖

## 常见决策示例

- 用户说"帮我读一下这个 PDF 讲了什么"：用 `read_file_content`
- 用户说"这个 PDF 有多少页"：用 `pdf.get_pdf_page_count`
- 用户说"把第 2 到 6 页单独导出来"：用 `pdf.extract_pdf_pages`
- 用户说"把这个 PDF 转成 Word/Excel/PPT"：先用 `pdf.convert`（默认 `is_free_convert=false`），若返回会员不足错误（`code=400100` / `VipLevelNotEnough`）则将 `is_free_convert` 改为 `true` 重试，再用 `pdf.convert_query` 轮询结果
- 用户说"把这个 PDF 全文翻译成英文并导出双语版"：先用 `pdf.translate_full_file`，如返回任务态再用 `pdf.get_translate_progress` 轮询
