---
name: tencentcloud-ocr-recognizetableaccurate
description: 腾讯云表格识别v3(RecognizeTableAccurateOCR)接口调用技能。当用户需要从表格图片或PDF中识别常规表格、无线表格、多表格的内容,提取每个单元格的文字信息,或将表格图片识别结果导出为Excel文件时,应使用此技能。支持中英文表格图片、旋转表格图片、嵌套表格图片等复杂场景,识别效果优于表格识别V2。
version: 1.0.3
display_name: "腾讯云表格识别v3"
display_name_en: "Tencent Cloud Table OCR v3"
description_zh: "调用腾讯云表格识别v3接口，支持常规表格、无线表格、多表格、嵌套表格和旋转表格的识别。返回每个单元格的文字内容，支持导出为Excel文件。适用于各类复杂表格图片/PDF的结构化提取。"
description_en: "Tencent Cloud RecognizeTableAccurateOCR API for table recognition. Supports bordered, borderless, nested, multi-table, and rotated table images/PDFs with Excel export capability."
visibility: "public"
---

# 腾讯云表格识别v3 (RecognizeTableAccurateOCR)

## 用途

调用腾讯云OCR表格识别v3接口，支持中英文图片/PDF内常规表格、无线表格、多表格的检测和识别，返回每个单元格的文字内容，支持旋转的表格图片识别，且支持将识别结果保存为Excel格式。

核心能力：
- **常规表格识别**：支持有线表格的精准识别
- **无线表格识别**：支持无边框表格的检测与识别
- **多表格识别**：单张图片/PDF中包含多个表格时均可检测
- **嵌套表格识别**：有线表格中包含无线表格的复杂场景
- **旋转表格识别**：支持旋转角度的表格图片
- **Excel导出**：识别结果可直接导出为Excel文件（Base64编码）
- **PDF支持**：支持PDF文件的单页表格识别

官方文档：https://cloud.tencent.com/document/api/866/86721

## 使用时机

当用户提出以下需求时触发此技能：
- 需要从图片中提取表格内容
- 需要从PDF中识别表格数据
- 需要将图片/PDF中的表格转换为Excel文件
- 涉及表格OCR识别的任何场景
- 需要识别无线表格、嵌套表格等复杂表格

## 环境要求

- Python 3.6+
- 依赖：`tencentcloud-sdk-python`（通过 `pip install tencentcloud-sdk-python` 安装）
- 环境变量：
  - `TENCENTCLOUD_SECRET_ID`：腾讯云API密钥ID
  - `TENCENTCLOUD_SECRET_KEY`：腾讯云API密钥Key

## 使用方式

运行 `scripts/main.py` 脚本完成表格识别。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageBase64 | str | 否(二选一) | 图片/PDF的Base64值，编码后不超过10M，分辨率建议600*800以上且长宽比小于3，支持PNG/JPG/JPEG/BMP/PDF |
| ImageUrl | str | 否(二选一) | 图片/PDF的URL地址，都提供时只使用ImageUrl |
| PdfPageNumber | int | 否 | PDF页码，仅支持单页识别，默认1，必须>=1 |
| **UserAgent** | **str** | **否** | **请求来源标识(可选)，用于追踪调用来源，统一固定为`Skills`** |

### 输出格式

识别成功后返回 JSON 格式结果：

**格式化输出模式（默认）**：
```json
{
  "表格数量": 1,
  "表格详情": [
    {
      "表格序号": 1,
      "表格类型": "有线表格",
      "单元格数量": 12,
      "单元格详情": [
        {
          "行范围": "0 - 1",
          "列范围": "0 - 1",
          "文本": "本报告期末",
          "置信度": 99.0,
          "单元格类型": "body"
        }
      ],
      "表格坐标": [
        {"X": 50, "Y": 100},
        {"X": 800, "Y": 100},
        {"X": 800, "Y": 600},
        {"X": 50, "Y": 600}
      ]
    }
  ],
  "Excel数据": "已返回(Base64编码)",
  "旋转角度": 0.0,
  "RequestId": "xxx"
}
```

**原始输出模式（--raw）**：
```json
{
  "TableDetections": [
    {
      "Cells": [
        {
          "ColTl": 0,
          "RowTl": 0,
          "ColBr": 1,
          "RowBr": 1,
          "Text": "本报告期末",
          "Type": "body",
          "Confidence": 99.0,
          "Polygon": [{"X": 50, "Y": 100}, {"X": 200, "Y": 100}, {"X": 200, "Y": 150}, {"X": 50, "Y": 150}]
        }
      ],
      "Type": 1,
      "TableCoordPoint": [{"X": 50, "Y": 100}, {"X": 800, "Y": 100}, {"X": 800, "Y": 600}, {"X": 50, "Y": 600}]
    }
  ],
  "Data": "UEsDBBQACAgIAIFzWFY...",
  "PdfPageSize": 0,
  "Angle": 0.0,
  "RequestId": "xxx"
}
```

### 响应数据结构说明

**TableInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| Cells | list of TableCellInfo | 单元格内容（可能返回null） |
| Type | int | 文本块类型：0非表格文本、1有线表格、2无线表格（可能返回null） |
| TableCoordPoint | list of Coord | 表格主体四个顶点坐标，左上→右上→右下→左下（可能返回null） |

**TableCellInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| ColTl | int | 单元格左上角的列索引 |
| RowTl | int | 单元格左上角的行索引 |
| ColBr | int | 单元格右下角的列索引 |
| RowBr | int | 单元格右下角的行索引 |
| Text | str | 单元格内识别出的字符串文本，多行以换行符\n隔开 |
| Type | str | 单元格类型 |
| Confidence | float | 单元格置信度 |
| Polygon | list of Coord | 单元格在图像中的四点坐标 |

### 错误码说明

| 错误码 | 含义 |
|--------|------|
| FailedOperation.DownLoadError | 文件下载失败 |
| FailedOperation.EmptyImageError | 图片内容为空 |
| FailedOperation.ImageDecodeFailed | 图片解码失败 |
| FailedOperation.ImageSizeTooLarge | 图片尺寸过大 |
| FailedOperation.OcrFailed | OCR识别失败 |
| FailedOperation.PDFParseFailed | PDF解析失败 |
| FailedOperation.UnKnowError | 未知错误 |
| FailedOperation.UnKnowFileTypeError | 未知的文件类型 |
| FailedOperation.UnOpenError | 服务未开通 |
| InvalidParameterValue.InvalidParameterValueLimit | 参数值错误 |
| LimitExceeded.TooLargeFileError | 文件内容太大 |
| ResourceUnavailable.InArrears | 账号已欠费 |
| ResourceUnavailable.ResourcePackageRunOut | 账号资源包耗尽 |
| ResourcesSoldOut.ChargeStatusException | 计费状态异常 |

### 重要业务逻辑

1. **ImageBase64和ImageUrl必须提供其一**，都提供时只使用ImageUrl
2. 图片/PDF编码后不超过10M，分辨率建议600*800以上且长宽比小于3（短边分辨率>600，长边<=短边*3）
3. 支持格式：PNG、JPG、JPEG、BMP、PDF
4. **PdfPageNumber必须>=1**，仅支持PDF单页识别，默认值为1
5. PDF转图有白名单机制，需白名单用户才支持
6. 若引擎返回ImageSizeTooLargeError，会映射为ImageSizeInvalidError
7. 支持将识别结果导出为Excel（Data字段为Base64编码的Excel数据）
8. **默认接口请求频率限制：2次/秒**
9. 建议图片存储于腾讯云COS以获得更高的下载速度和稳定性

### 调用示例

```bash
# 通过URL识别表格
python scripts/main.py --image-url "https://example.com/table.jpg"

# 通过文件路径(自动Base64编码)识别
python scripts/main.py --image-base64 ./table.png

# 识别PDF中的表格(指定页码)
python scripts/main.py --image-base64 ./document.pdf --pdf-page-number 2

# 识别并保存Excel文件
python scripts/main.py --image-url "https://example.com/table.jpg" --save-excel ./result.xlsx

# 输出原始JSON响应
python scripts/main.py --image-url "https://example.com/table.jpg" --raw

# 指定地域
python scripts/main.py --image-url "https://example.com/table.jpg" --region ap-beijing```
