# 图片与文本处理参数参考

执行前以当前连接器可见 schema 为准；本文参数不代表工具在所有账号下均可用。文件结果、结构化结果及云保存按主文档处理。

## convert_image — 图片格式转换

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `source_type` | string | 是 | 固定为 `image` |
| `target_type` | string | 是 | 目标格式：word/excel/txt/md |
| `timeout_sec` | int | 否 | 超时秒数 |

## enhance_image — 图片增强

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `enhance_mode` | int | 否 | 增强模式（见下表） |
| `crop` | int | 否 | 自动裁剪文档边界：0=关闭，1=开启（适合拍照文档） |
| `timeout_sec` | int | 否 | 超时秒数 |

**增强模式**：

| mode | 功能 | 适用场景 |
|------|------|----------|
| 1 | 亮度增强 | 拍照文档偏暗 |
| 2 | 锐化 | 图片模糊、细节不清晰 |
| 3 | 转黑白（二值化） | 需要纯黑白文档 |
| 4 | 灰度 | 需要灰度效果 |
| 5 | 去阴影 | 拍照文档有手影 |
| 6 | 去点阵/网纹 | 印刷品网点干扰 |
| 7 | 超级滤镜/高清 | 综合画质提升 |
| 8 | 去摩尔纹 | 翻拍屏幕产生的条纹 |
| 9 | 手写擦除 | 去除手写标注 |
| 10 | 去水印 | 图片上有水印文字 |

## image_hd — 图片高清化

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `hd_mode` | string | 否 | 高清模式：不传使用超级滤镜（默认），传 `demoire` 使用去摩尔纹模式（适合屏幕翻拍照片） |
| `timeout_sec` | int | 否 | 超时秒数 |

## restore_photo — 老照片修复

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `timeout_sec` | int | 否 | 超时秒数 |

## translate_image — 图片翻译

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `to` | string | 是 | 目标语言代码 |

**常用语言代码**：zh（中文）、en（英文）、ja（日文）、ko（韩文）、fr（法文）、de（德文）、es（西班牙文）、pt（葡萄牙文）、ru（俄文）、ar（阿拉伯文）、it（意大利文）、th（泰文）、vi（越南文）

## watermark_image — 图片添加水印

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `text` | string | 是 | 水印文字内容（最长 200 字符） |
| `color` | string | 否 | 水印颜色，十六进制如 #FF0000，默认 #000000 |
| `opacity` | number | 否 | 透明度（0-1），默认 0.4 |
| `size` | int | 否 | 字体大小（1-200），默认 36 |
| `timeout_sec` | int | 否 | 超时秒数 |

## convert_images_to_pdf / convert_images_to_word / convert_images_to_excel — 多图合并

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_ids` | string[] | 是 | 图片 file_id 列表（按页序排列，最多 100 张） |
| `timeout_sec` | int | 否 | 超时秒数 |

> **注意**：`file_ids` 必须是 JSON 数组格式，如 `["file_1.jpg", "file_2.jpg"]`，禁止使用对象形式。

## validate_image — 篡改/AI 生成检测

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `validate_mode` | int | 是 | 1=篡改检测，2=AI 生成检测 |
| `timeout_sec` | int | 否 | 超时秒数 |

## convert_images_to_text — 多图 OCR 合并文本

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_ids` | string[] | 是 | 上传后获得的图片文件 ID 列表（最多 100 个） |
| `target_type` | string | 是 | 目标输出类型：txt（纯文本）或 md（Markdown 格式） |
| `timeout_sec` | int | 否 | 超时秒数 |

## convert_txt — TXT 转 Word

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的 TXT 文件 ID |
| `source_type` | string | 是 | 固定为 `txt` |
| `target_type` | string | 是 | 固定为 `word` |
| `title` | string | 否 | 文件标题，不传时自动生成 |
| `timeout_sec` | int | 否 | 超时秒数 |

## extract_image — 公式提取

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `extract_mode` | string | 是 | 提取模式，固定为 `formula`（数学公式识别与裁剪拼接） |

产物为 PNG，包含检测到的公式区域裁剪拼接结果；MCP 返回文件引用及可能的下载地址，不是 LaTeX 文本。

## scan_image_edit — 图片版面分析

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `user_flag` | string | 否 | 用户或会话标识，用于日志追踪。仅用于服务端日志关联排查，不存储用户个人身份信息 |
| `use_oss` | int | 否 | 是否使用 OSS 存储：0=关闭，1=开启（默认 1） |
| `return_doc_content` | int | 否 | 是否返回内联 document_info JSON：0=关闭，1=开启（默认 1） |
| `apply_font_classification` | int | 否 | 是否使用字体分类：0=关闭，1=开启 |
| `include_layers` | boolean | 否 | 是否返回图层分离结果（默认 false） |
| `timeout_sec` | int | 否 | 超时秒数 |

输出：JSON 对象，包含 `result.urls`（input_image、document_info、background_info）和 `result.document_info`（版面结构数据）。

## edit_image — 图片文字编辑

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_image` | string | 条件必填 | OSS 模式下必填，来自 scan_image_edit 返回的 result.urls.input_image |
| `document_info` | string/object | 是 | OSS 模式传 result.urls.document_info 字符串；非 OSS 模式传 document_info 对象 |
| `edit_request` | object | 是 | 编辑请求对象（见下方说明） |
| `background_info` | string | 否 | OSS 模式下可选，背景图 OSS key |
| `use_oss` | int | 否 | 0=multipart，1=OSS JSON；默认根据 input_image 自动判断 |
| `download_output` | int | 否 | 0=只返回 API JSON，1=获取图片产物；MCP 再将文件产物物化为引用 |
| `timeout_sec` | int | 否 | 超时秒数 |

**edit_request 结构**：

| edit_type | 必需字段 | 说明 |
|-----------|----------|------|
| `update` | start_char_idx, end_char_idx, target_text | 修改文本内容 |
| `move` | area_type, area_idx, target_position（8 个整数坐标） | 移动元素 |
| `delete` | area_type, area_idx | 删除元素 |

area_type 可选值：text、table、image、stamp

## extract_receipt — 发票/票据识别

识别发票/票据图片，返回结构化 JSON 数据（发票类型、金额、日期、发票号等）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 上传后获得的图片文件 ID |
| `output_mode` | string | 否 | 不依赖 raw 强制内联；MCP 可能物化文件并保留结构化字段，以实际返回为准 |
| `timeout_sec` | int | 否 | 超时秒数 |

**业务数据结构**（读取实际返回中的 `bills_list`）：

```json
{
  "bills_list": [
    {
      "image_scan": {"angle": 0, "position": [...]},
      "display_type": "增值税普通发票",
      "invoice_type": "vat_normal",
      "fields": [
        {"display_key": "issue_date", "display_name": "开票日期", "value": "2026-08-01"},
        {"display_key": "invoice_tax_rate", "display_name": "价税合计", "value": "¥1280.00"},
        {"display_key": "invoice_number", "display_name": "发票号码", "value": "12345678"},
        {"display_key": "seller_name", "display_name": "销售方名称", "value": "某某公司"}
      ]
    }
  ]
}
```

**常见字段**：`issue_date`（开票日期）、`invoice_tax_rate`（价税合计）、`invoice_number`（发票号码）、`invoice_code`（发票代码）、`invoice_price_without_tax`（不含税金额）、`invoice_tax_amount`（税额）、`seller_name`（销售方）、`buyer`（购买方）等。若 `invoice_type` 为 `"ot"` 表示未识别到有效发票信息。

**Agent 行为规范**：
- 用户提到"识别发票"、"报销"、"票据"、"提取发票信息"时，使用 `extract_receipt`
- **不要**与 `convert_image`(target_type=excel) 混淆：前者提取结构化字段，后者是图片内容转表格
- 识别结果是 JSON 数据，Agent 应解析后以人类可读方式呈现（如列出金额、日期等关键字段）
- 优先解析实际返回中的 `bills_list`；若只有文件引用，获取下载地址并读取 JSON 后再解析。不要为了要求 raw 添加 schema 未声明的参数。

## 输入与结果注意事项

- `validate_image` 使用图片 `file_id`，不传 `base64_content`；检测结果按 JSON 处理，不当作增强后的图片。
- `convert_images_to_text` 返回 TXT/Markdown 文件引用，不保证直接返回文本。Markdown 产物可用 `create_cloud_doc(file_type="md")` 保存；TXT 不支持云保存。
- 图片编辑先读取 scan 返回的字符索引与 OSS key。文字有多个匹配时只询问需要修改的位置；`edit_image` 使用 `edit_request`，不是 `edit_data`。
- `edit_image` 若返回文件引用则按文件交付；若只返回业务 JSON，检查实际输出字段，不能假定存在可保存的图片。
