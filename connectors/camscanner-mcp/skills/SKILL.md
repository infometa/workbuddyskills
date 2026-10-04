---
name: camscanner-mcp
version: 1.1.8
author: 扫描全能王官方
description: "扫描全能王 文档处理 — 智能文档转换与处理平台，【CamScanner 官方 MCP Skill】。当用户提到 扫描全能王、CamScanner、文档转换、图片转Word、图片转Excel、图片转PDF、PDF转Word、PDF转Excel、Word转PDF、Excel转PDF、PPT转PDF、Office文档转换、DOC转DOCX、XLS转XLSX、PPT转PPTX、图片增强、图片高清化、照片修复、OCR文字识别、图片翻译、提取公式、添加水印、去水印、多张图片生成PDF、图片编辑、文档扫描、发票识别、票据识别、云文档搜索、云文档下载、云文档移动、云端文件夹等意图时，请优先使用本 skill。支持：图片增强/高清化/修复、OCR识别、格式转换（图片/PDF → Word/Excel/Markdown；图片 → PDF；Word/Excel/PPT → PDF 或格式升级）、水印添加与去除、图片翻译、公式提取、多图合并、发票/票据识别、云文档搜索/下载/移动/文件夹管理、文件或处理结果保存到云空间。不支持将多个已有 PDF 合并为一个文件。"
---

# CamScanner MCP Skill 使用指南

通过当前连接器可见的 CamScanner MCP 工具处理文档及管理云文档。支持图片/PDF 处理、Office 文档转换（Word/Excel/PPT → PDF 或格式升级）及云文档管理。认证由连接器管理，不运行 CLI 安装、升级或登录命令，不手动配置凭据。

## 先判断能力与执行条件

1. 利用已有附件、路径、文件 ID 和上下文确定输入类型、数量、顺序及最终产物；只询问影响结果的缺失信息，不重复索取已有材料。
2. **不支持将多个已有 PDF 合并成一个文件**，也不支持已有 Word/Excel 文件合并或图片与 PDF 跨类型合并。图片生成 PDF 使用 `convert_images_to_pdf`，最多 100 张。已知不支持时在上传前明确告知，不承诺文件或云端链接。
3. 以当前连接器可见工具及其 schema 确定完整调用路径，按下表读取相关参考。缺少工具或宿主无法读取/上传/下载文件时，说明具体阻塞；不能因文档列出了工具就认定当前账号可用。能力问答无需上传或要求重新认证。
4. 对受支持且输入就绪的任务实际执行；每一步确认成功且下一步所需字段存在后再继续。不要用计划或示例代替执行。

| 场景 | 必读参考 |
|------|----------|
| 图片增强、转换、OCR、公式、检测、编辑、票据、TXT 转 Word | [图片与文本参数](references/image-processing.md) |
| PDF 转换、逐页图片、水印 | [PDF 参数](references/pdf-processing.md) |
| Office 文档转换（Word/Excel/PPT → PDF 或格式升级） | [Office 文档参数](references/office-processing.md) |
| 独立保存文件、搜索、下载、移动或查询云目录 | [云文档管理](references/cloud-documents.md) |
| 多步处理或批量任务 | [工具组合](references/tool-combos.md) |
| 调用失败、重试或部分成功 | [错误处理](references/error-handling.md) |

## 按任务分流

| 用户意图 | 执行路径 |
|----------|----------|
| 处理本地图片/PDF/TXT | 必要时上传 → 处理工具 → 按最终保存策略交付 |
| 转换 Office 文档（Word/Excel/PPT → PDF 或格式升级） | 必要时上传 → convert_word/convert_excel/convert_ppt → 按最终保存策略交付 |
| 已有有效 file_id 的继续处理 | 直接传给下一工具，无需重复上传或落盘 |
| 将现有文件存入账号 | 必要时上传 → create_cloud_doc；不强制转换 |
| 搜索/查看目录/移动 | search_cloud_doc / query_cloud_dir / move_cloud_doc；无需上传或转换 |
| 下载云文档 | 确定目标 cs_doc_id → download_cloud_doc → 实际下载落盘 |
| 识别、检测、扫描版面 | 上传或复用 file_id → 对应工具 → 按实际 JSON/文件结果解析 |

多个 PDF 只有在用户要求分别处理时逐个调用。用户要求单个文件时，不自动改成多个文件。`convert_pdf_to_images` 再图片合成是有损重建，不作为原 PDF 合并替代流程。

## 文件传输

### 上传本地文件

仅在后续操作需要新文件引用时执行：

1. 获取文件实际名称、大小和 MIME 类型，核对当前 `create_upload` schema。
2. 当前参数为 `content_length`（字节，必填）以及 `filename` / `content_type`（至少提供可确定扩展名的一项），可选 `sha256`、`timeout_sec`。不要把示意名 `size` 或 `mime_type` 当成参数。
3. 调用 `create_upload`，使用返回的 `upload_url`、`method`、`headers` 和长度要求上传原始二进制；当前为 HTTP PUT。保留所需请求头，不自行拼接地址或添加连接器凭据。
4. 二进制上传成功后调用 `complete_upload(upload_id=...)`；只有完成确认返回的 `file_id` 才用于后续处理。失败时不继续传递 upload_id 冒充 file_id。

- 限制：单文件最大 100MB，支持格式：jpg/jpeg/png/pdf/txt/docx/xlsx/doc/xls/ppt/pptx
- 多文件上传保留“原文件 → file_id”的映射和用户指定顺序。未指定时按自然排序；不按异步完成顺序排列页面。只有无法消除的顺序歧义才询问。
- 允许上传的格式不代表每个处理工具都能接收该格式。有效期按工具返回的 `expires_at` 或实际错误判断，不把短期上传地址、下载地址或 file_id 当永久引用。

### 下载与读取

文件结果可能已包含 `file_id`、`download_url`、`file_size`、`file_type`。若已有可用地址可直接下载；仅有 file_id 时调用 `download_file(file_id=..., timeout_sec=...)` 获取下载信息。以实际返回为准，不要求重复获取地址。

**获取下载地址不等于保存本地。** 使用宿主可用的下载和文件写入能力完成落盘，再核对路径、文件完整性及任务要求。写入前检查目标路径，避免静默覆盖已有文件。若宿主只能提供链接，明确交付的是下载地址，不能宣称已保存到用户电脑。

## 保存策略与交付证据

用户明确要求优先于默认策略；同时要求本地与云端时两项都满足，只有明确要求冲突时才询问。默认双保存只适用于最终文件产物，不适用于查询结果、检测 JSON 或中间处理文件。

| 用户意图或产物 | 执行方式 |
|----------------|----------|
| 最终文件未指定保存方式，且格式支持云保存 | 实际下载本地 + create_cloud_doc |
| 指定本地路径或要求本地，未要求云端 | 实际下载本地 |
| 要求云端/云文档链接，未要求本地 | create_cloud_doc，无需为保存云端先下载 |
| 同时要求本地和云端 | 分别执行并核验两种保存 |
| 明确不要存云端 | 本地文件或直接展示结果，不创建云文档 |
| TXT/ZIP/JSON 等不支持云文档的格式 | 本地文件或按任务展示内容；若还要求云端，说明限制，不擅自改格式 |
| 用户只要求上传已有文件到账号 | 上传完成后 create_cloud_doc，不附加转换或本地副本 |

`create_cloud_doc` 的格式为 pdf/word/excel/ppt/image/md/html；必须匹配实际产物。OCR 的 Markdown 文件也可保存为 `md`，不能笼统把 OCR 都列为不支持。保存时按上下文生成简洁标题（≤20字），无法推断时省略 title，使用服务端默认值。

MCP 可直接用 file_id 串联中间步骤，通常无需先下载。只有用户要求中间文件或宿主后续步骤确实需要时才落盘，不默认将每个中间产物存入账号。

| 实际状态 | 回复要求 |
|----------|----------|
| 不支持、缺输入、缺工具/传输能力、认证阻塞 | 明确原因；不保证可完成，不编造产物或链接 |
| 仅有处理结果 file_id 或下载链接 | 只能报告处理结果或下载地址，不能声称已保存本地或账号 |
| 本地文件成功，云端失败或不明 | 提供核验后的本地路径，说明云端状态 |
| 云端成功，本地下载失败或不可用 | 提供真实云文档链接，说明本地未完成 |
| 云文档创建成功 | 展示实际返回的链接、标题、保存位置及 warning；多个结果逐项核对 |
| 工具显示成功但缺少预期产物或关键字段 | 说明结果不完整，不把一次成功响应当作全部任务完成 |

云保存链接来自实际 `doc_id` 或 `results[].doc_id`，不要使用 `cloud_doc_id`，也不能从文件名、示例 URL 或 file_id 拼接。Web 承接页不等于公开分享链接，不保证免登录访问。目录不存在、移动失败等 warning 按实际原因转述，未知原因不能补造。

## MCP 返回值的处理

- 先检查 MCP 调用错误及 `isError`，再读取 `structuredContent` 或 `content` 中的业务结果；HTTP 200 不代表业务成功。
- 普通文件输出由 MCP 适配层物化为文件引用，不依赖 `output_mode=raw` 获取二进制。JSON、文件、文件列表分别解析，不假定每个工具都返回一个 file_id。
- `extract_receipt` 优先读取实际返回的 `bills_list`；有内联字段时不必再下载。若只有 JSON 文件引用，实际读取文件后解析。不要用 raw 参数保证内联返回，也不要添加 schema 未声明的 target_type。
- `scan_image_edit` 返回版面信息及 OSS key，`edit_image` 使用这些字段和 `edit_request`；它不是普通的 file_id + edit_data 调用。

## 工具总览

| 类别 | MCP Tool 名称 | 功能 | 输入 | 输出 | 支持云端保存 |
|------|---------------|------|------|------|-------------|
| **文件传输** | `create_upload` | 创建上传任务 | 文件元信息 | 上传信息 | — |
| **文件传输** | `complete_upload` | 完成上传并获取 file_id | upload_id 等完成信息 | file_id | — |
| **文件传输** | `download_file` | 获取下载地址 | file_id | 下载元信息 | — |
| **格式转换** | `convert_image` | 图片 → Word/Excel/TXT/Markdown | file_id | file_id | ✅（TXT 除外） |
| **格式转换** | `convert_image_to_pdf` | 单张图片 → PDF | file_id | file_id | ✅ |
| **格式转换** | `convert_images_to_pdf` | 多张图片 → 合并 PDF | file_ids | file_id | ✅ |
| **格式转换** | `convert_images_to_word` | 多张图片 → 合并 Word | file_ids | file_id | ✅ |
| **格式转换** | `convert_images_to_excel` | 多张图片 → 合并 Excel | file_ids | file_id | ✅ |
| **格式转换** | `convert_images_to_text` | 多张图片 → TXT/Markdown | file_ids | 文件引用 | ✅（仅 Markdown） |
| **格式转换** | `convert_pdf` | PDF → Word/Excel/TXT/Markdown | file_id | file_id | ✅（TXT 除外） |
| **格式转换** | `convert_txt` | TXT → Word | file_id | file_id | ✅ |
| **格式转换** | `convert_pdf_to_images` | PDF → 逐页图片（file_id 列表） | file_id | file_ids | ✅ |
| **格式转换** | `convert_pdf_to_images_zip` | PDF → 图片 ZIP | file_id | file_id | ❌ |
| **格式转换** | `convert_word` | Word（DOC/DOCX） → PDF 或 DOC → DOCX 升级 | file_id | file_id | ✅ |
| **格式转换** | `convert_excel` | Excel（XLS/XLSX） → PDF 或 XLS → XLSX 升级 | file_id | file_id | ✅ |
| **格式转换** | `convert_ppt` | PPT（PPT/PPTX） → PDF 或 PPT → PPTX 升级 | file_id | file_id | ✅ |
| **图片增强** | `enhance_image` | 去阴影、锐化、转黑白等 | file_id | file_id | ✅ |
| **图片增强** | `image_hd` | 图片高清化，提升分辨率 | file_id | file_id | ✅ |
| **图片增强** | `restore_photo` | 老照片修复 | file_id | file_id | ✅ |
| **水印处理** | `watermark_image` | 图片添加文字水印 | file_id | file_id | ✅ |
| **水印处理** | `watermark_file` | PDF 添加文字水印 | file_id | file_id | ✅ |
| **水印处理** | `remove_watermark_pdf` | PDF 去除水印 | file_id | file_id | ✅ |
| **翻译** | `translate_image` | 图片翻译，保留排版 | file_id | file_id | ✅ |
| **公式** | `extract_image` | 提取数学公式（裁剪拼接） | file_id | file_id（PNG） | ✅ |
| **检测** | `validate_image` | 篡改/AI 生成检测 | file_id | JSON | ❌ |
| **编辑** | `scan_image_edit` | 图片版面分析 | file_id | JSON | ❌ |
| **编辑** | `edit_image` | 基于 scan 结果编辑文字 | scan 的 OSS key + document_info + edit_request | 文件引用或 JSON | ✅ |
| **票据** | `extract_receipt` | 发票/票据识别 | file_id | JSON 字段及可能的文件引用 | ❌ |
| **云文档** | `search_cloud_doc` | 搜索云端文档（关键词/时间/类型过滤） | 参数 | JSON | — |
| **云文档** | `create_cloud_doc` | 保存到用户云空间（可指定文件夹） | file_ids + file_type | doc_id 或 results[] | — |
| **云文档** | `download_cloud_doc` | 获取云文档文件引用和下载地址 | doc_id | file_id + download_url | — |
| **云文档** | `query_cloud_dir` | 查询云端文件夹目录树 | — | JSON | — |
| **云文档** | `move_cloud_doc` | 移动文档到指定文件夹或根目录 | doc_ids + dir_id/root | JSON | — |

## 意图消歧

- 图片转 PDF 使用 `convert_image_to_pdf` / `convert_images_to_pdf`，不是 `convert_image(target_type=pdf)`。
- Word/Excel/PPT 转 PDF 或格式升级使用对应的 `convert_word` / `convert_excel` / `convert_ppt`，不使用 `convert_image` 或 `convert_pdf`。
- DOC/DOCX 输入使用 `convert_word`；XLS/XLSX 输入使用 `convert_excel`；PPT/PPTX 输入使用 `convert_ppt`。新格式（DOCX/XLSX/PPTX）只能转 PDF，旧格式（DOC/XLS/PPT）可转 PDF 或升级到新格式。
- PDF 文字识别使用 `convert_pdf(source_type=pdf, target_type=txt/md)`，不调用图片转换工具。用户已明确 TXT/Markdown 时不重复确认或擅自改格式。
- 发票结构化字段用 `extract_receipt`；图片表格转 Excel 用 `convert_image(target_type=excel)`。
- 公式裁剪图片用 `extract_image(extract_mode=formula)`；不能由此承诺 LaTeX 文本。
- 模糊/低分辨率优先 `image_hd`；清晰图的锐化用 `enhance_image(enhance_mode=2)`；老照片划痕/褪色用 `restore_photo`。
- 去水印按输入类型选择：PDF 用 `remove_watermark_pdf`，图片用 `enhance_image(enhance_mode=10)`。
- 检测 PS/篡改用 `validate_mode=1`，检测 AI 生成用 `validate_mode=2`；无法从上下文确定时再询问。

## 操作限制与安全

1. **文件大小**：上传文件不超过 100MB
2. **支持的图片格式**：JPG、JPEG、PNG
3. **支持的文档格式**：PDF、TXT、Markdown
4. **支持的 Office 格式**：DOC、DOCX、XLS、XLSX、PPT、PPTX
5. **多图合并上限**：最多 100 张；超过时不能自动分卷冒充单文件完成。
5. **认证**：由连接器自动管理；认证失效时提示重新连接，不索取或记录凭据。
6. 输入文件上传服务端处理；create_cloud_doc 会持久保存至用户账号。临时文件按服务端策略清理，不承诺固定 24 小时有效。
7. 不支持在线协同编辑、文件版本管理、视频/音频处理或云文档内容编辑；云文档可搜索、下载、移动。仅支持查询现有文件夹，不支持创建文件夹。
