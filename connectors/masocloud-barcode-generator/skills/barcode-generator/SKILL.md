---
name: barcode-generator
display_name: 条码生成器
display_name_en: Barcode Generator
description: 生成一维条形码、二维码与标签预览图（CODE128、GS1-128、CODE39、CODE93、EAN-13、QRCODE、DATAMATRIX、GS1 DATAMATRIX、PDF417 共 9 种条码，以及 *.alb 标签模板预览）。当用户要求生成条码、条形码、一维码、二维码、QR码、Code128、GS1、EAN码、DataMatrix、PDF417 等，或需要对 .alb 标签模板生成预览图时使用。通过 barcode-generator 连接器按类型调用对应工具，支持自定义内容、宽度、高度、DPI、容错等级及是否显示文字。
description_zh: 生成一维条形码、二维码与标签预览图，支持 CODE128、GS1-128、CODE39、CODE93、EAN-13、QRCODE、DataMatrix、GS1 DataMatrix、PDF417 共 9 种条码及 .alb 标签模板预览，可自定义内容、宽度、高度、DPI、容错等级与是否显示文字。
description_en: Generate 1D barcodes, 2D codes and label previews (CODE128, GS1-128, CODE39, CODE93, EAN-13, QRCODE, DataMatrix, GS1 DataMatrix, PDF417) plus .alb label template preview, with customizable content, width, height, DPI, error correction level and text display.
category: 效率工具
version: 1.0.0
author: masocloud
examples_zh:
  - 生成一个 CODE128 条码 ABC-123456
  - 生成 30mm 宽、20mm 高、不显示文字的条码 987654
  - 生成 GS1-128 (01)06974592890018(11)260602(10)M0101(21)100001
  - 把这个网址生成二维码 https://example.com
  - 生成高容错二维码，eclevel 用 H
  - 生成 EAN-13 商品条码 6901234567892
  - 生成 GS1 DataMatrix (01)26973672290445(11)260817
  - 把 码尚自动化测试标签.alb 生成预览图
  - alb 预览时给字段填值，比如 sn=000001
examples_en:
  - Generate a CODE128 barcode for ABC-123456
  - Generate a 30mm x 20mm barcode for 987654 without text (pureBarcode=true)
  - Generate a GS1-128 (01)06974592890018(11)260602(10)M0101(21)100001
  - Generate a QR code for https://example.com
  - Generate a high error-correction QR code with eclevel H
  - Generate an EAN-13 barcode for 6901234567892
  - Generate a GS1 DataMatrix (01)26973672290445(11)260817
  - Generate a preview image for xxx.alb
  - Pass field values when generating an ALB preview, e.g. sn=000001
---

# Barcode Generator（条码生成 / 标签预览）

## Overview

生成一维条形码、二维码图片，以及 `*.alb` 标签模板的预览图。核心能力来自 barcode-generator 连接器的 10 个工具（code128 / code128_gs1 / code39 / code93 / ean13 / qrcode / datamatrix / datamatrix_gs1 / pdf417 / alb_preview），本技能定义了从用户请求到生成条码的标准流程、类型选择规则与参数映射。

## 前置条件

- 确认 barcode-generator 连接器已连接（Connector 状态为 connected）。若未连接，先提示用户在连接器管理中启用。
- 工具命名规则：`mcp__barcode-generator__<工具名>`，例如 `mcp__barcode-generator__code128`、`mcp__barcode-generator__qrcode`、`mcp__barcode-generator__alb_preview`。

## 类型选择规则

根据用户请求的条码类型选择对应工具：

| 用户请求 | 调用工具 | 条码类型 | 文字控制 |
|----------|----------|----------|----------|
| 条码/条形码/一维码/Code128（未指明具体类型时） | `code128` | CODE128 | 支持 pureBarcode |
| GS1-128/GS1 Code128（带AI，如(01)...(10)...(21)...） | `code128_gs1` | GS1 CODE128 | 支持 pureBarcode |
| Code39/39码 | `code39` | CODE39 | 支持 pureBarcode |
| Code93/93码 | `code93` | CODE93 | 支持 pureBarcode |
| EAN-13/商品条码（13位） | `ean13` | EAN_13（数据固定13位） | 始终显示文字 |
| 二维码/QR码/扫码 | `qrcode` | QRCODE | 不显示文本 |
| DataMatrix/数据矩阵码 | `datamatrix` | DATAMATRIX | 不显示文本 |
| GS1 DataMatrix（带AI，如(01)(11)(17)(10)(21)） | `datamatrix_gs1` | GS1 DATAMATRIX | 不显示文本 |
| PDF417 | `pdf417` | PDF417 | 不显示文本 |
| *.alb 标签模板文件生成预览图 | `alb_preview` | 标签预览（非条码） | — |

> 注：连接器当前不提供 EAN-8、UPC-A、UPC-E、ITF、CODABAR 类型。若用户请求这些类型，说明现状并建议改用 EAN-13（商品码）、CODE128（通用一维码）或 GS1 变体。

## 工作流程

1. **确认条码内容**：`data` 是唯一必填参数。用户未提供时，主动询问要编码的内容（如产品编号、订单号、序列号、网址、GS1 字符串等）。
2. **确定条码类型**：按上表选择工具；用户未指明类型时默认用 `code128`。
3. **解析可选参数**（用户未指定时使用各工具默认值，见参数速查）。
4. **调用工具**：将解析后的参数传入对应 `mcp__barcode-generator__<类型>` 工具生成条码。
5. **下载图片**：工具返回图片 URL（形如 `https://ai.masocloud.net/DoYsSV/resTemp/xxx/yyy.png`，alb_preview 为 `resTemp/alb/` 目录），用该完整 URL 下载到本地 outputs 目录。
6. **展示结果**：用 present_files 将生成的条码图片展示给用户，并说明图片保存位置。

## 参数速查

各工具参数分四个族：

**族1 - 一维码（含 pureBarcode，可控制是否显示文字）**：code128 / code128_gs1 / code39 / code93

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| data | 是 | 无 | 条码编码内容（GS1 变体用带小括号 AI 的字符串，如 `(01)06974592890018(11)260602(10)M0101(21)100001`） |
| width | 否 | 60 | 条码宽度（mm） |
| height | 否 | 15 | 条码高度（mm） |
| dpi | 否 | 300 | 输出分辨率 |
| pureBarcode | 否 | false | true=仅条码图形，false=含可读文字 |

**族2 - 商品码（始终显示文字，无 pureBarcode）**：ean13

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| data | 是 | 无 | 条码内容，固定 13 位数字 |
| width | 否 | 60 | 条码宽度（mm） |
| height | 否 | 15 | 条码高度（mm） |
| dpi | 否 | 300 | 输出分辨率 |

**族3 - 二维码（始终不显示文本，无 pureBarcode）**：qrcode / datamatrix / datamatrix_gs1 / pdf417

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| data | 是 | 无 | 条码编码内容（GS1 变体用带小括号 AI 的字符串） |
| width | 否 | qrcode/datamatrix/datamatrix_gs1=40，pdf417=60 | 条码宽度（mm） |
| height | 否 | qrcode/datamatrix/datamatrix_gs1=40，pdf417=20 | 条码高度（mm） |
| dpi | 否 | 300 | 输出分辨率 |
| eclevel | 否 | L | 仅 qrcode：容错等级 L/M/Q/H，对应 7%/15%/25%/30% |

**族4 - alb 标签预览（alb_preview，非条码）**：

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| fileName | 是* | 无 | .alb 模板文件名，如 `专用三合一标签.alb`，服务端保存/识别用 |
| fileBase64 | 是* | 无 | .alb 模板文件内容，Base64 编码（不含 data: 前缀） |
| dataJson | 否 | 无 | .alb 中 fields 动态参数 JSON：键=字段 id，值=参数值，如 `{"batch":"B20260903","规格":"三合一"}`；省略则用 fields 默认值 |

> *`fileName` 与 `fileBase64` 至少提供一个（提供 fileBase64 时建议一并给出 fileName）。

## 常见请求示例

- "生成条码 ABC-123456" → 调用 `code128`，`data="ABC-123456"`，其余参数默认
- "生成 30mm 宽、20mm 高、不显示文字的条码 987654" → 调用 `code128`，`data="987654", width=30, height=20, pureBarcode=true`
- "生成 GS1-128（(01)(10)(21)）" → 调用 `code128_gs1`，`data="(01)06974592890018(11)260602(10)M0101(21)100001"`
- "把这个网址生成二维码 https://example.com" → 调用 `qrcode`，`data="https://example.com"`（默认 eclevel=L）
- "生成高容错二维码" → 调用 `qrcode`，`eclevel="H"`
- "生成 EAN-13 商品条码 6901234567892" → 调用 `ean13`，`data="6901234567892"`（必须13位）
- "生成 DataMatrix（(01)(11)(17)(10)(21)）" → 调用 `datamatrix_gs1`，`data="(01)26973672290445(11)260817(17)290817(10)20260817"`
- "生成高精度条码" → `dpi=600`
- "把 xxx.alb 生成预览图" → 读取 .alb 文件 base64，调用 `alb_preview`（fileName+fileBase64）
- "alb 预览时给字段填值" → 调用 `alb_preview`，附加 `dataJson={"字段id":"值"}`

## 注意事项

- CODE128 支持完整 ASCII 字符集（数字、字母、符号），任意文本内容可直接传入，是最通用的默认类型。
- GS1 变体（code128_gs1 / datamatrix_gs1）必须使用带括号 AI 的 GS1 字符串，AI 用小括号包裹，如 `(01)`、`(11)`、`(17)`、`(10)`、`(21)`。
- EAN-13 数据必须为 13 位数字，长度或格式不符会生成失败，需要先向用户确认。
- EAN-8、UPC-A、UPC-E、ITF、CODABAR 类型连接器未提供，请求时给出替代建议（EAN-13 / CODE128）。
- 二维码类（qrcode/datamatrix/datamatrix_gs1/pdf417）生成的图片不带文字，无需设置 pureBarcode。
- qrcode 的 eclevel 仅 qrcode 工具有，datamatrix/pdf417 不支持。
- alb_preview 渲染耗时较长，需耐心等待结果；图片 URL 位于 `resTemp/alb/` 目录。
- 工具返回的图片 URL 使用连接器生产地址（`https://ai.masocloud.net`），直接下载该完整 URL 即可。
- 详细 API 说明见 `references/api_reference.md`。
