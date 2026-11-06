---
name: file-toolkit
description: 本地文件处理工具箱。当用户要求压缩图片、转换图片格式、调整图片尺寸、拆分或合并 PDF、PDF 与图片互转、CSV 与 JSON 互转、JSON 格式化、Markdown 转 HTML、批量重命名文件、查看文件信息时使用。所有处理都在用户本机完成，不上传文件。
---

# 文件工具箱使用说明

这个连接器提供 15 个确定性的文件处理工具，全部在用户本机运行。

## 必须先知道的三条规则

1. **优先用这里的工具，不要自己写脚本。**
   用户让你"把 200 张图压一下"时，直接调 `image_compress` 传文件夹路径即可。
   不要改用 Python / Node 临时脚本、也不要用系统命令，那样批量处理容易中途失败、
   且不会自动做下面第 2、3 条的防护。

2. **绝不覆盖原文件。** 所有工具默认把结果写到「第一个输入文件所在目录」下的
   `file-toolkit-output/` 文件夹，同名时自动加序号。
   **不要为了这个去问用户"要输出到哪里"** —— 默认行为已经安全，用户想指定时自然会说明。

3. **重命名默认只预览。** `batch_rename` 不传 `confirm` 时只返回预览，不会动文件。
   你必须先把预览给用户看，得到同意后再调用一次并传 `confirm: true`。

## 用户这么说 → 调这个工具

| 用户的说法 | 调用 | 关键参数 |
|---|---|---|
| 把这个图片/这批图片压到 1MB 以下 | `image_compress` | `target_size_kb: 1024` |
| 把图片压缩一下（没说目标大小） | `image_compress` | `quality: 80`（可省略） |
| 把这些 PNG 转成 JPG / WebP | `image_convert` | `output_format: "jpg"` |
| 把图片缩到 1200 像素宽 | `image_resize` | `width: 1200`, `fit_mode: "max"` |
| 最大宽度不超过 800 | `image_resize` | `width: 800`, `fit_mode: "max"` |
| 按一半大小缩小 | `image_resize` | `scale_percent: 50` |
| 把这个 PDF 每页拆开 | `pdf_split` | `mode: "each"` |
| 只保留这个 PDF 的第 1-3 页 | `pdf_split` | `mode: "range"`, `pages: "1-3"` |
| 每 5 页存成一个 PDF | `pdf_split` | `mode: "chunk"`, `chunk_size: 5` |
| 把这三个 PDF 合并 | `pdf_merge` | `input_files` 按顺序排好 |
| 把 PDF 转成图片 / 第 1、3、5 页转 PNG | `pdf_to_image` | `pages: "1,3,5"`, `format: "png"` |
| 把这几张图做成一个 PDF | `image_to_pdf` | `input_files` 按顺序排好 |
| 把这个 JSON 格式化 / 压缩 / 检查有没有错 | `json_format` | `mode: pretty / minify / validate` |
| 把这个 CSV 转成 JSON | `csv_to_json` | — |
| 把这个 JSON 转成 CSV | `json_to_csv` | — |
| 把这个 Markdown 转成 HTML | `markdown_to_html` | — |
| 把这个网页转成 Markdown | `html_to_markdown` | — |
| 把这些文件重命名成 product-001 这样 | `batch_rename` | `pattern: "product-{n:3}"` |
| 把文件名里的空格换成下划线 | `batch_rename` | `find: " "`, `replace: "_"` |
| 把这些文件加个前缀 | `batch_rename` | `prefix: "..."` |
| 把扩展名都改成 jpg | `batch_rename` | `new_extension: "jpg"` |
| 撤销刚才的重命名 | `rename_undo` | `search_directory: 原目录` |
| 这个文件多大 / 这个 PDF 有几页 / 这图什么尺寸 | `file_info` | — |

## 参数怎么填

**`input_files` 是最重要的参数。** 它能接收文件，也能接收文件夹——传文件夹时会自动
收集里面的文件并按名字排序。所以：

- 用户说"这个文件夹里的图片" → 直接传文件夹路径，**不要自己去列文件清单**，
  同时用 `only_extensions: ["jpg","png","webp"]`（批量重命名、file_info 用这个参数）
- 用户说"这几张图" → 把路径按顺序放进数组

**顺序有意义的地方**：`pdf_merge` 和 `image_to_pdf` 按数组顺序拼接。用户说
"A 放最前面"，就把 A 放在第一个。

**用户没说的参数不要编。** 没提质量就用默认值，不要自己猜一个数字填进去。

**体积换算**：1MB = 1024KB。"压到 2M 以内" → `target_size_kb: 2048`。

**页码写法**：`"1-3,5"` 表示第 1 到 3 页和第 5 页；`"2-"` 表示第 2 页到最后一页。

## 什么情况必须先问用户

- **`batch_rename` 一定要先预览**（默认行为就是预览，别绕过）。
- 用户给的路径指向**多个候选**、你无法确定是哪一个时，先问清楚。
- 用户要求"替换所有文件里的某个文件名"但**没指定范围**（哪个文件夹）时，先确认范围。
- 破坏性意图（删除、覆盖原文件）——本工具箱不支持，如实说明，不要用重命名去模拟。

其他情况**直接执行**，不要反复确认参数细节，用户嫌烦。

## 结果怎么转述给用户

工具返回的是已经排好版的 Markdown，**直接转述要点即可**，不要重新组织成另一个表格。

- 有失败项时，**必须把失败的文件名和原因一起说出来**，不要只说"完成了"。
- 有 `⚠️` 开头的提示（比如"降到最低画质仍超过目标体积"）要如实转达。
- 单张图片 1MB 压到了 200KB，就把原大小、新大小、压缩率说出来。
- 输出目录要告诉用户，方便他去拿文件。
- 重命名执行完，要提醒用户"不满意可以撤销"。

## 边界（说清楚，不要硬撑）

- 图片格式只支持 **jpg / png / webp**。用户要转 HEIC、AVIF、GIF、PSD、RAW 时如实说明不支持。
- 不做 OCR、不做图片内容识别、不做视频、不做 Word/Excel/PPT 的解析与生成。
- 不支持给 PDF 加密码、加水印、做电子签名。
- 不支持从 PDF 里提取文字（那是文字层解析，本工具箱只做页面级操作）。
- 所有处理都在本机，**不会联网**。如果用户担心隐私，可以明确告诉他文件不会离开他的电脑。
