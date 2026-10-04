# PDF 处理参数参考

当前不支持将多个已有 PDF 合并为一个文件。逐页渲染再组装属于有损图像重建，不能用来承诺原 PDF 合并或保留文本层、书签、表单和签名。

参数以当前连接器 schema 为准。MCP 文件结果是引用及可能的下载地址；`output_mode=raw` 不保证返回二进制。

## convert_pdf — PDF 格式转换

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 PDF 文件 ID |
| `source_type` | string | 是 | 固定为 `pdf` |
| `target_type` | string | 是 | 目标格式：word/excel/txt/md |
| `timeout_sec` | int | 否 | 超时秒数 |

## watermark_file — PDF 添加水印

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | PDF 文件 ID |
| `file_type` | string | 是 | 固定为 `pdf` |
| `text` | string | 是 | 水印文字内容（最长 200 字符） |
| `color` | string | 否 | 水印颜色，十六进制如 #FF0000，默认 #000000 |
| `opacity` | number | 否 | 透明度（0-1），默认 0.4 |
| `size` | int | 否 | 字体大小（1-200），默认 36 |
| `timeout_sec` | int | 否 | 超时秒数 |

## convert_pdf_to_images — PDF 逐页转图片

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 PDF 文件 ID |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

输出：`{"file_ids": [...], "sizes": [...], "page_count": N}`

## convert_pdf_to_images_zip — PDF 转图片 ZIP

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 PDF 文件 ID |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

产物为 ZIP 文件，包含逐页图片；MCP 返回文件引用，需实际下载后才是本地 ZIP。

## remove_watermark_pdf — PDF 去水印

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 PDF 文件 ID |
| `output_mode` | string | 否 | MCP 普通文件结果按 file_id 处理，不依赖 raw 获取二进制 |
| `dpi` | int | 否 | PDF 渲染 DPI（最小 72，默认 144） |
| `timeout_sec` | int | 否 | 超时秒数 |

限制：最多支持 100 页 PDF。

## 格式与保存

- Word/Excel/Markdown 产物可保存云端，分别使用 `file_type=word/excel/md`；TXT 和 ZIP 不支持云保存。
- 用户要各自处理多个 PDF 时逐个执行；用户要单个合并 PDF 时明确不支持，不能静默返回多个文件。
- `convert_pdf_to_images` 的 `file_ids` 按页序排列。逐页处理保留此顺序；保存为多页图片云文档时使用 `file_type=image`，这不是原 PDF 文件。
