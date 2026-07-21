---
name: tencentcloud-ocr-extractdocagent
description: 腾讯云实时文档抽取Agent(ExtractDocAgent)接口调用技能。当用户需要从图片或PDF中按自定义字段名称进行结构化信息抽取时，应使用此技能。支持自定义字段名称、字段类型（KV对或表格字段）和字段提示词，实现灵活的文档信息提取。适用于合同、发票、报告等各类文档的结构化数据抽取场景。
version: 1.0.3
display_name: "腾讯云实时文档抽取Agent"
display_name_en: "Tencent Cloud Extract Doc Agent"
description_zh: "调用腾讯云实时文档抽取Agent接口，支持从图片/PDF中按自定义字段名称进行结构化信息抽取。支持KV对和表格字段两种抽取类型，可通过字段提示词提升准确性。适用于合同、发票、报告等文档的自动信息提取。"
description_en: "Tencent Cloud ExtractDocAgent API for structured information extraction from images/PDFs. Supports custom field names with KV-pair and table field extraction types. Ideal for contracts, invoices, and reports."
visibility: "public"
---

# 腾讯云实时文档抽取Agent (ExtractDocAgent)

## 用途

调用腾讯云OCR实时文档抽取Agent接口，支持从图片/PDF中按用户自定义的字段名称进行结构化信息抽取。模型参数更小，速度更快，适用于对实时性要求高（30秒以内）且输入输出Token在2000以内的场景。

核心能力：
- **自定义字段抽取**：支持用户自定义需要抽取的字段名称
- **KV对抽取**：支持键值对形式的信息抽取（KeyType=0）
- **表格字段抽取**：支持表格形式的信息抽取（KeyType=1）
- **字段提示词**：支持为每个字段提供描述/提示词，提升抽取准确性
- **PDF支持**：支持PDF文件的单页文档抽取
- **多格式输入**：支持PNG、JPG、JPEG、BMP、PDF格式

官方文档：https://cloud.tencent.com/document/api/866/126442

## 使用时机

当用户提出以下需求时触发此技能：
- 需要从文档图片/PDF中抽取指定字段的结构化信息
- 需要从合同、发票、报告等文档中提取特定内容
- 需要按自定义字段名进行文档信息提取
- 涉及文档结构化抽取的任何场景
- 需要同时抽取KV对和表格形式的信息

## 环境要求

- Python 3.6+
- 依赖：`tencentcloud-sdk-python`（通过 `pip install tencentcloud-sdk-python` 安装）
- 环境变量：
  - `TENCENTCLOUD_SECRET_ID`：腾讯云API密钥ID
  - `TENCENTCLOUD_SECRET_KEY`：腾讯云API密钥Key

## 使用方式

运行 `scripts/main.py` 脚本完成文档结构化信息抽取。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageBase64 | str | 否(二选一) | 图片/PDF的Base64值，编码后不超过10M，分辨率建议600*800以上，支持PNG/JPG/JPEG/BMP/PDF，像素需介于20-10000px |
| ImageUrl | str | 否(二选一) | 图片/PDF的URL地址，都提供时只使用ImageUrl |
| ItemNames | list of ItemNames | 是 | 自定义抽取字段列表，至少提供一个 |
| PdfPageNumber | int | 否 | PDF页码，仅支持单页识别 |

**ItemNames 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| KeyName | str | 是 | 要提取的字段名称，不能为空 |
| KeyType | int | 否 | 默认0；0=KV对，1=表格字段 |
| KeyPrompt | str | 否 | 字段描述/提示词，用于提升抄取准确性 |
| **UserAgent** | **str** | **否** | **请求来源标识(可选)，用于追踪调用来源，统一固定为`Skills`** |

### 输出格式

识别成功后返回 JSON 格式结果：

**格式化输出模式（默认）**：
```json
{
  "抽取结果": [
    {
      "组序号": 1,
      "字段列表": [
        {
          "字段名(自动识别)": "合同编号",
          "字段名(配置)": "合同编号",
          "字段值": "HT-2024-001"
        }
      ]
    }
  ],
  "旋转角度": 0.0,
  "RequestId": "xxx"
}
```

**原始输出模式（--raw）**：
```json
{
  "Angle": 0.0,
  "StructuralList": [
    {
      "Groups": [
        {
          "Lines": [
            {
              "Key": {
                "AutoName": "合同编号",
                "ConfigName": "合同编号"
              },
              "Value": {
                "AutoContent": "HT-2024-001",
                "Coord": { ... },
                "PageIndex": "0"
              }
            }
          ]
        }
      ]
    }
  ],
  "ErrorCode": "",
  "ErrorMessage": "",
  "RequestId": "xxx"
}
```

### 响应数据结构说明

**GroupInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| Groups | list of LineInfo | 每一行的元素 |

**LineInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| Lines | list of ItemInfo | 每行的一个元素 |

**ItemInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| Key | Key | key信息组（可能返回null） |
| Value | Value | Value信息组（可能返回null） |

**Key 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| AutoName | str | 自动识别的字段名称 |
| ConfigName | str | 定义的字段名称（传key的名称，可能返回null） |

**Value 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| AutoContent | str | 自动识别的字段内容 |
| Coord | Polygon | 四点坐标（可能返回null） |
| PageIndex | str | 页数（可能返回null） |

### 错误码说明

| 错误码 | 含义 |
|--------|------|
| FailedOperation.DownLoadError | 文件下载失败 |
| FailedOperation.ImageDecodeFailed | 图片解码失败 |
| FailedOperation.ImageSizeTooLarge | 图片尺寸过大，请确保编码后不超过10M，像素介于20-10000px |
| FailedOperation.OcrFailed | OCR识别失败 |
| FailedOperation.PDFParseFailed | PDF解析失败 |
| FailedOperation.ResponseParseFailed | 结果解析失败 |
| FailedOperation.UnKnowError | 未知错误 |
| FailedOperation.UnKnowFileTypeError | 未知的文件类型 |
| FailedOperation.UnOpenError | 服务未开通，请先在腾讯云控制台开通文档抽取Agent服务 |
| InvalidParameterValue.InvalidParameterValueLimit | 参数值错误 |
| LimitExceeded.TooLargeFileError | 文件内容太大 |
| ResourceUnavailable.InArrears | 账号已欠费 |
| ResourceUnavailable.ResourcePackageRunOut | 账号资源包耗尽 |
| ResourcesSoldOut.ChargeStatusException | 计费状态异常 |

### 重要业务逻辑

1. **ImageBase64和ImageUrl必须提供其一**，都提供时只使用ImageUrl
2. 图片/PDF编码后不超过10M，分辨率建议600*800以上，像素需介于20-10000px
3. 支持格式：PNG、JPG、JPEG、BMP、PDF
4. **ItemNames不能为空**，KeyName不能为空
5. **KeyType仅支持0(KV对)和1(表格字段)两种类型**
6. KV类型和表格类型分别有数量上限
7. KeyName和KeyPrompt有长度限制
8. PdfPageNumber>=1，仅支持PDF单页识别
9. **计费策略**：固定价格，不限抽取字段数；自适应价格下抽取字段>10个记两次费用，≤10个记一次费用
10. **默认接口请求频率限制：20次/秒**
11. 建议图片存储于腾讯云COS以获得更高的下载速度和稳定性
12. 响应中ErrorCode非空时表示业务处理失败，需检查ErrorMessage获取错误详情

### 调用示例

```bash
# 通过URL抽取文档中的KV字段
python scripts/main.py --image-url "https://example.com/contract.jpg" \
  --item-names '[{"KeyName":"合同编号","KeyType":0,"KeyPrompt":"文档中的合同编号"}]'

# 同时抽取KV字段和表格字段
python scripts/main.py --image-url "https://example.com/invoice.jpg" \
  --item-names '[{"KeyName":"发票号码","KeyType":0},{"KeyName":"明细","KeyType":1,"KeyPrompt":"明细条目表格"}]'

# 通过文件路径(自动Base64编码)抽取
python scripts/main.py --image-base64 ./document.png \
  --item-names '[{"KeyName":"姓名","KeyType":0},{"KeyName":"金额","KeyType":0}]'

# 识别PDF中的文档(指定页码)
python scripts/main.py --image-base64 ./document.pdf --pdf-page-number 2 \
  --item-names '[{"KeyName":"总金额","KeyType":0}]'

# 输出原始JSON响应
python scripts/main.py --image-url "https://example.com/doc.jpg" \
  --item-names '[{"KeyName":"标题","KeyType":0}]' --raw

# 指定地域
python scripts/main.py --image-url "https://example.com/doc.jpg" \
  --item-names '[{"KeyName":"签署日期","KeyType":0}]' --region ap-beijing```
