# barcode-generator 连接器 API 参考

工具命名：`mcp__barcode-generator__<工具名>`，当前共 **10 个工具**（2026-09-03 tools/list 实测）。

> 变更记录：
> - EAN-8、UPC-A、UPC-E、ITF、CODABAR 不提供。
> - 新增 GS1 变体（code128_gs1 / datamatrix_gs1）与标签预览（alb_preview）。

---

## 族1：一维码（含 pureBarcode 参数）

适用工具：`code128` / `code128_gs1` / `code39` / `code93`

### 公共参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| data | string | ✅ | - | 条形码数据（要编码的内容） |
| pureBarcode | boolean | ❌ | false | 是否只显示条形码（不显示下方文字） |
| dpi | number | ❌ | 300 | 输出分辨率（DPI） |
| height | number | ❌ | 15 | 条形码高度（mm） |
| width | number | ❌ | 60 | 条形码宽度（mm） |

### 各工具说明

| 工具名 | 类型 | 说明 |
|--------|------|------|
| `code128` | CODE128 | 支持完整 ASCII，通用性最强，未指明类型时的默认选择 |
| `code128_gs1` | GS1 CODE128 | GS1 应用标识符码，data 用带小括号 AI，如 `(01)06974592890018(11)260602(10)M0101(21)100001` |
| `code39` | CODE39 | 经典一维码，通常用于工业/资产管理 |
| `code93` | CODE93 | Code39 的增强版，密度更高 |

---

## 族2：商品码（无 pureBarcode，始终显示文字）

适用工具：`ean13`

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| data | string | ✅ | - | 条形码数据，固定 13 位数字 |
| dpi | number | ❌ | 300 | 输出分辨率（DPI） |
| height | number | ❌ | 15 | 条形码高度（mm） |
| width | number | ❌ | 60 | 条形码宽度（mm） |

---

## 族3：二维码（无 pureBarcode，始终不显示文本）

适用工具：`qrcode` / `datamatrix` / `datamatrix_gs1` / `pdf417`

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| data | string | ✅ | - | 条码数据（GS1 变体用带小括号 AI） |
| dpi | number | ❌ | 300 | 输出分辨率（DPI） |
| height | number | ❌ | 见下表 | 条码高度（mm） |
| width | number | ❌ | 见下表 | 条码宽度（mm） |
| eclevel | string | ❌ | L | **仅 qrcode**：L/M/Q/H，对应 7%/15%/25%/30% 容错 |

### 各工具默认尺寸

| 工具名 | 类型 | width 默认 | height 默认 | 备注 |
|--------|------|-----------|-------------|------|
| `qrcode` | QRCODE | 40 | 40 | 支持 eclevel |
| `datamatrix` | DATAMATRIX | 40 | 40 | - |
| `datamatrix_gs1` | GS1 DATAMATRIX | 40 | 40 | data 用带小括号 AI，如 `(01)26973672290445(11)260817(17)290817(10)20260817` |
| `pdf417` | PDF417 | 60 | 20 | - |

---

## 族4：alb 标签预览（alb_preview，非条码）

为码尚标签格式文件（`*.alb`）生成带条码的预览图。

### 参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| fileName | string | 建议 | .alb 模板文件名，如 `专用三合一标签.alb`，用于服务端保存/识别模板 |
| fileBase64 | string | 建议 | .alb 模板文件内容，Base64 编码（不含 `data:` 前缀） |
| dataJson | string | ❌ | .alb 模板文件里 fields 结构对应的动态参数 JSON 对象：键=字段 id，值=参数值，如 `{"batch":"B20260903","规格":"三合一"}`；可让用户输入，不输入则用 fields 里的默认值 |

> fileName 与 fileBase64 至少提供其一（提供 fileBase64 时 fileName 一并给出最佳）。

### 调用说明

通过常规 MCP 工具通道调用 `mcp__barcode-generator__alb_preview`，传入 `fileName` 与 `fileBase64`（或 `fileName` + `dataJson`）即可。服务端渲染完成后返回图片 URL。

---

## 调用示例

CODE128 一维码（含文字、标准尺寸）：

```json
{
  "data": "ABC-123456",
  "width": 60,
  "height": 15,
  "dpi": 300,
  "pureBarcode": false
}
```

仅条码图形、高分辨率：

```json
{
  "data": "987654",
  "pureBarcode": true,
  "dpi": 600
}
```

GS1 CODE128：

```json
{
  "data": "(01)06974592890018(11)260602(10)M0101(21)100001"
}
```

二维码（默认 40×40mm、容错 L）：

```json
{
  "data": "https://example.com"
}
```

高容错二维码：

```json
{
  "data": "https://example.com",
  "eclevel": "H"
}
```

GS1 DataMatrix（医药/医疗器械标签常用）：

```json
{
  "data": "(01)26973672290445(11)260817(17)290817(10)20260817"
}
```

EAN-13 商品条码（固定13位数字）：

```json
{
  "data": "6901234567892"
}
```

---

## 返回值

生成后返回条码图片 URL，形如：

```
https://ai.masocloud.net/DoYsSV/resTemp/barcode1d/barcode_xxxxx.png
https://ai.masocloud.net/DoYsSV/resTemp/alb/2026090311/alb_12.png
```

使用返回的完整 URL 下载图片到本地 outputs 目录，再用 present_files 展示给用户。

## 错误处理

- 若连接器未连接，调用会失败：先提示用户在连接器管理页启用 barcode-generator，再重试。
- 若 data 缺失，会因参数校验失败：先向用户确认条码内容再调用。
- EAN-13 数据必须为 13 位数字，格式不符会生成失败：向用户说明限制并请其确认数据。
- 若用户请求 EAN-8 / UPC-A / UPC-E / ITF / CODABAR：说明这些类型不提供，建议改用 EAN-13、CODE128 或 GS1 变体。

