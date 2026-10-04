# Office 文档转换参数参考

将 Word、Excel、PPT 文档转换为 PDF，或将旧格式（DOC/XLS/PPT）升级为新格式（DOCX/XLSX/PPTX）。三个工具共享相同的参数结构，区别在于 `source_type` 和 `target_type` 的可选值。

参数以当前连接器 schema 为准。MCP bridge 自动注入 `file_id` 参数。

## convert_word — Word 文档转换

将 Word 文档（DOC 或 DOCX）转换为 PDF，或将 DOC 升级为 DOCX。具体 DOC/DOCX 格式由文件内容自动检测。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 Word 文件 ID |
| `source_type` | string | 是 | 固定为 `word` |
| `target_type` | string | 是 | 目标格式：`pdf` 或 `docx` |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

**转换规则**：
- DOC 文件：可转为 PDF 或升级为 DOCX
- DOCX 文件：只能转为 PDF（已是新格式，无需升级）

## convert_excel — Excel 文档转换

将 Excel 文档（XLS 或 XLSX）转换为 PDF，或将 XLS 升级为 XLSX。具体 XLS/XLSX 格式由文件内容自动检测。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 Excel 文件 ID |
| `source_type` | string | 是 | 固定为 `excel` |
| `target_type` | string | 是 | 目标格式：`pdf` 或 `xlsx` |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

**转换规则**：
- XLS 文件：可转为 PDF 或升级为 XLSX
- XLSX 文件：只能转为 PDF（已是新格式，无需升级）

## convert_ppt — PPT 文档转换

将 PowerPoint 文档（PPT 或 PPTX）转换为 PDF，或将 PPT 升级为 PPTX。具体 PPT/PPTX 格式由文件内容自动检测。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 PPT 文件 ID |
| `source_type` | string | 是 | 固定为 `ppt` |
| `target_type` | string | 是 | 目标格式：`pdf` 或 `pptx` |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

**转换规则**：
- PPT 文件：可转为 PDF 或升级为 PPTX
- PPTX 文件：只能转为 PDF（已是新格式，无需升级）

## 输出

三个工具的输出结构一致：

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 转换结果文件 ID |
| `download_url` | string | 文件下载地址 |
| `file_size` | int | 输出文件大小（字节） |
| `target_type` | string | 实际输出格式 |

## 保存与交付

- PDF 产物可保存云端，使用 `create_cloud_doc(file_type="pdf")`
- DOCX/XLSX/PPTX 产物可保存云端，使用 `create_cloud_doc(file_type="word"/"excel"/"ppt")`
- 默认双保存策略与主文档一致

## Agent 行为规范

- 根据输入文件扩展名或上下文判断使用哪个工具：DOC/DOCX → `convert_word`，XLS/XLSX → `convert_excel`，PPT/PPTX → `convert_ppt`
- 用户说"转PDF"时，`target_type` 使用 `pdf`；用户说"升级格式"、"转DOCX"等时使用对应的新格式
- 新格式文件（DOCX/XLSX/PPTX）请求升级时，告知已是最新格式，只能转 PDF
- 不要与 `convert_image` 或 `convert_pdf` 混淆：Office 文档转换使用专用工具
