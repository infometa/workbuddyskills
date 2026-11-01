---
name: scnet-omni-ocr
description: 一站式文档智能处理 MCP，集成 OCR 文字识别与信息提取、高精度文档解析和文档格式转换三大能力。需要识别图片/文档文字、抽取票据证照字段、解析论文/合同/标书版式为结构化 Markdown、或将 PDF/图片转换为 Word/PPT 时使用。
metadata:
  version: "3.0.7"
  author: "SCNet"
---

# SCNet 一站式文档智能处理 MCP

本 Skill 描述项目注册的 `scnet-omni-ocr` MCP 服务。该服务通过 Streamable HTTP 统一提供三大核心能力：

- **OCR 文字识别与信息提取**：支持通用文字、印章、表格识别，以及个人证照、行业资质、财务票据和金融单据的结构化字段抽取。同步返回结果。
- **高精度文档解析**：自研模型驱动，还原整页版式——从目录、段落、表格到公式、化学分子式、图片、印章，拆解为带层级的结构化 Markdown 数据。异步执行，需提交任务后轮询结果。
- **文档格式转换**：支持 PDF 转 Word、图片转 Word、图片转 PPT 等多类型互转，高保真还原排版。异步执行，需提交任务后轮询结果。

## 服务注册

- 服务名称：`scnet-omni-ocr`
- 传输类型：`streamableHttp`
- MCP 地址：`https://scnet-omni-ocr.ksai.scnet.cn:58043/mcp`
- 请求超时：`30000` 毫秒
- MCP 工具：`fileUploadPresign`、`ocrRecognition`、`documentParsing`、`fileConversion`、`getTaskResult`

客户端配置在 `mcp.json` 中，认证信息应通过 HTTP 请求 Header 传递：

```http
Authorization: Bearer ${ACCESS_TOKEN}
```

`${ACCESS_TOKEN}` 是调用方配置的平台 access token，不要把真实 token 写入提示词、日志、文件内容或普通业务参数中。

---

## 本地文件上传流程

三种能力共用同一套本地文件上传机制。用户选择本地文件时，每次都必须完整执行以下流程：

1. 从本地文件路径取得文件名（必须包含扩展名），例如从 `D:\images\aaa.jpg` 取得 `aaa.jpg`。
2. 调用 `fileUploadPresign`，传入文件名，获取本次上传专用的临时凭证。
3. 执行 `skills/scripts/file_upload.py` 中的 `upload_and_get_web_file_path(presign_data, local_file_path)`。`presign_data` 使用凭证工具成功响应中的 `data`，`local_file_path` 使用用户选择的原始本地路径。（脚本为 python 脚本，python 环境 3.8+，无需额外库，可直接运行）
4. 脚本上传成功后返回文件网络 URL，再将 URL 传入后续识别/解析/转换工具。

脚本调用示例：

```python
from file_upload import upload_and_get_web_file_path

file_url = upload_and_get_web_file_path(presign_response, local_file_path)
```

不得跳过上传脚本而把本地路径直接传给后续工具。每次本地文件操作都重新获取上传凭证并执行脚本，不要复用旧凭证。API Key 只由 MCP 服务端使用，不要向用户索取、输出或传给脚本。如果用户提供的本身就是服务端可访问的 `http://` 或 `https://` URL，可以直接传入后续工具，不执行本地上传流程。

---

## 可用工具

本服务共注册 5 个 MCP 工具，以下是各工具的详细说明。

### `fileUploadPresign`

为本地文件获取一次性上传凭证。该工具必须在执行本地上传脚本前调用。

| 参数         | 类型     | 必填 | 说明                                        |
|------------|--------|----|-------------------------------------------|
| `fileName` | string | 是  | 本地文件名，必须包含扩展名，例如 `invoice.jpg`。不要传完整本地路径。 |

成功响应中的 `data` 应直接传给 `upload_and_get_web_file_path`，不要修改凭证字段，也不要将凭证展示给用户。获取凭证失败或脚本上传失败时停止流程，不要继续调用后续工具。

### `ocrRecognition`

对图片或文档执行 OCR 文字识别与信息提取。调用前先根据文件内容选择准确的 `sceneType`，不要使用中文场景名称代替枚举值。

| 参数          | 类型     | 必填 | 说明                                                          |
|-------------|--------|----|-------------------------------------------------------------|
| `sceneType` | string | 是  | 识别场景枚举，必须使用下表中的英文值。大小写不敏感，但建议使用大写原值。                        |
| `file`      | string | 是  | 传递文件网络URL地址。对于本地文件，使用上传脚本返回的网络 URL。                         |
| `filename`  | string | 是  | 原始文件名，必须包含扩展名，例如 `invoice.jpg`、`id-card.png` 或 `table.pdf`。 |

调用示例：

```json
{
  "sceneType": "VAT_INVOICE",
  "file": "https://example.com/invoice.jpg",
  "filename": "invoice.jpg"
}
```

如果用户没有提供文件，先向用户索取文件。网络文件必须能被服务端访问；本地文件必须先按"本地文件上传流程"上传成功。

### `documentParsing`

提交高精度文档解析任务。自研模型驱动，将 PDF、Office 文档等复杂文档还原为结构化 Markdown 数据。**这是一个异步接口**，返回 `taskId` 后需要用 `getTaskResult` 轮询获取最终结果。

| 参数               | 类型      | 必填 | 说明                                                         |
|------------------|---------|----|------------------------------------------------------------|
| `fileUrl`        | string  | 是  | 文件的 `http://`/`https://` 网络地址。本地文件需先上传。                       |
| `ocrType`        | enum    | 否  | 处理类型。文档解析时固定为 `DOC_PARING`，也可不传（默认值即为 `DOC_PARING`）。             |
| `pageIndex`      | string  | 否  | 页码范围，如 `1` 或 `1-5`；不传则解析全部页面。                                  |
| `isTableCls`     | boolean | 否  | 是否开启表格细分处理，默认 `false`。                                       |
| `isDocOri`       | boolean | 否  | 是否开启文档方向矫正，扫描件或旋转页面时设为 `true`，默认 `false`。                       |
| `enforceSeal`    | boolean | 否  | 是否开启强制二次印章检测，默认 `false`。                                     |
| `isInlineFormula` | boolean | 否  | 是否开启行内公式检测，数学或科技文档时设为 `true`，默认 `false`。                        |

调用示例：

```json
{
  "fileUrl": "https://example.com/paper.pdf",
  "isTableCls": true,
  "isInlineFormula": true
}
```

返回的 `data.output.task_id` 是后续轮询所需的任务 ID；返回成功只表示任务已受理，不表示解析完成。

### `fileConversion`

提交文档格式转换任务。支持 PDF 转 Word、图片转 Word、图片转 PPT。**这是一个异步接口**，返回 `taskId` 后需要用 `getTaskResult` 轮询获取最终结果。

| 参数               | 类型      | 必填 | 说明                                                         |
|------------------|---------|----|------------------------------------------------------------|
| `fileUrl`        | string  | 是  | 文件的 `http://`/`https://` 网络地址。本地文件需先上传。                       |
| `ocrType`        | enum    | 是  | 转换类型，必填。可选：`PDF_TO_WORD`（PDF 转 Word）、`IMAGE_TO_WORD`（图片转 Word）、`IMAGE_TO_PPT`（图片转 PPT）。 |
| `pageIndex`      | string  | 否  | 页码范围，如 `1` 或 `1-5`；不传则转换全部页面。                                  |
| `isTableCls`     | boolean | 否  | 是否开启表格细分处理，默认 `false`。                                       |
| `isDocOri`       | boolean | 否  | 是否开启文档方向矫正，扫描件或旋转页面时设为 `true`，默认 `false`。                       |
| `enforceSeal`    | boolean | 否  | 是否开启强制二次印章检测，默认 `false`。                                     |
| `isInlineFormula` | boolean | 否  | 是否开启行内公式检测，数学或科技文档时设为 `true`，默认 `false`。                        |

调用示例：

```json
{
  "fileUrl": "https://example.com/report.pdf",
  "ocrType": "PDF_TO_WORD",
  "isTableCls": true
}
```

返回的 `data.output.task_id` 是后续轮询所需的任务 ID；返回成功只表示任务已受理，不表示转换完成。

### `getTaskResult`

查询异步任务的状态和结果。用于 `documentParsing` 和 `fileConversion` 提交的任务的后续轮询。

| 参数       | 类型     | 必填 | 说明                                                         |
|----------|--------|----|------------------------------------------------------------|
| `taskId` | string | 是  | 由 `documentParsing` 或 `fileConversion` 返回的任务 ID。             |
| `ocrType` | enum   | 是  | 任务类型。查询文档解析结果时填 `DOC_PARING`；查询格式转换结果时填 `PDF_TO_WORD`、`IMAGE_TO_WORD` 或 `IMAGE_TO_PPT`（与提交时的 `ocrType` 保持一致）。 |

**文档解析结果**（`ocrType=DOC_PARING`）返回结构：

```json
{
  "code": 200,
  "message": "SUCCESS",
  "data": {
    "taskId": "任务ID",
    "taskStatus": "pending | succeeded | failed",
    "submitTime": "提交时间",
    "endTime": "结束时间",
    "errorCode": "错误码（失败时）",
    "errorMessage": "失败原因（失败时）",
    "resultJsonFile": "结果JSON文件URL（成功时）",
    "markdowns": [
      {
        "documentId": "文档ID",
        "markdownContent": "# 文档标题\n\n正文内容（图片已内嵌为base64）"
      }
    ]
  }
}
```

**格式转换结果**（`ocrType` 为 `PDF_TO_WORD`/`IMAGE_TO_WORD`/`IMAGE_TO_PPT`）返回结构：

```json
{
  "code": 200,
  "message": "SUCCESS",
  "data": {
    "task_id": "任务ID",
    "task_status": "succeeded | failed",
    "submit_time": "提交时间",
    "end_time": "结束时间",
    "results": ["结果文件URL1", "结果文件URL2"],
    "error_code": "错误码",
    "error_message": "错误信息"
  }
}
```

**轮询规则**：
- `taskStatus` / `task_status` 为 `pending`：任务仍在处理，等待后继续查询。
- `taskStatus` / `task_status` 为 `succeeded`：停止轮询，展示结果。
- `taskStatus` / `task_status` 为 `failed`：停止轮询，展示错误信息。
- 查询请求本身返回 `code: 500` 时，可在确认任务 ID 后重试；不要把请求错误误判为任务失败。

---

# 能力一：OCR 文字识别与信息提取

同步接口，对图片或文档进行通用文字、印章、表格和证照/票据结构化识别。

## OCR 识别场景

### 通用识别

- 文字识别：`GENERAL`
- 印章文字识别：`SEAL_CHARACTER_RECOGNITION`
- 表格识别：`TABLE_RECOGNITION`

### 个人证照

- 居民身份证：`ID_CARD`
- 中国香港身份证：`HONG_KONG_IDENTITY_CARD`
- 外国人永久居留身份证：`PERMANENT_RESIDENCE_ID_CARD_FOR`
- 银行卡：`BANK_CARD`
- 社保卡：`SOCIAL_SECURITY_CARD`
- 户口本：`HOUSEHOLD_REGISTER`
- 出生医学证明：`BIRTH_CERTIFICATE`
- 往来港澳通行证：`HK_MACAU_PASS`
- 往来台湾通行证：`TAIWAN_PASS`
- 台湾居民来往大陆通行证：`TAIWAN_MAINLAND_PASS`
- 港澳居民来往内地通行证：`HK_MAINLAND_PASS`
- 结婚证：`MARRIAGE_CERTIFICATE`
- 不动产权证书：`REAL_ESTATE_OWNERSHIP_CERTIFICAT`
- 机动车行驶证正页：`FRONT_PAGE_OF_MOTOR_VEHICLE_DRIV`
- 机动车行驶证副页：`SECOND_SHEET_OF_MOTOR_VEHICLE_DR`
- 机动车驾驶证正页：`MOTOR_VEHICLE_DRIVING_LICENSE`
- 机动车驾驶证副页：`MOTOR_VEHICLE_DRIVING_LICENSE_SU`
- 中国护照：`CHINESE_PASSPORT`
- 学历证书：`ACADEMIC_CERTIFICATE`
- 学历证书电子注册备案表：`ONLINE_VERIFICATION_REPORT_OF_HE`
- 学位证书：`DIPLOMA`

### 行业资质

- 营业执照：`BUSINESS_LICENSE`
- 社会团体法人登记证书：`SOCIAL_ORG_REG`
- 工会法人资格证书：`TRADE_UNION_REG`
- 民办非企业单位登记证书：`PRIVATE_NON_ENTERPRISE_REG`
- 事业单位法人证书：`INSTITUTION_LEGAL_REG`
- 统一社会信用代码证书：`UNIFIED_SOCIAL_CREDIT_REG`
- 食品经营许可证：`FOOD_BUSINESS_LICENSE`
- 食品生产许可证：`FOOD_PRODUCTION_LICENSE`
- 卫生许可证：`HYGIENE_LICENSE`
- 金融许可证：`FINANCIAL_LICENSE`
- 金融机构代码证：`FINANCIAL_INSTITUTION_CODE_CERT`
- 支付业务许可证：`PAYMENT_BUSINESS_LICENSE`
- 开户许可证：`ACCOUNT_OPENING_LICENSE`
- 商标注册证：`TRADEMARK_REGISTRATION_CERT`
- 税务登记证：`TAX_REGISTRATION_CERT`
- 组织机构代码证：`ORGANIZATION_CODE_CERT`

### 财务票据

- 增值税发票：`VAT_INVOICE`
- 增值税通行费发票：`VAT_TOLL_INVOICE`
- 增值税卷票：`VAT_ROLL_INVOICE`
- 出租车发票：`TAXI_INVOICE`
- 火车票：`TRAIN_TICKET`
- 航空运输电子客票行程单：`AIRPORT_TICKET`
- 机动车销售统一发票：`VEHICLE_SALE_INVOICE`
- 定额发票：`QUOTA_INVOICE`
- 过路过桥费发票：`TOLL_INVOICE`
- 通用机打发票：`GENERAL_MACHINE_INVOICE`
- 非税票据：`NON_TAX_BILL`
- 汽车票：`BUS_TICKET`
- 船票：`SHIP_TICKET`
- 网约车行程单：`RIDE_HAILING_ITINERARY`
- 银联 POS 签购单：`UNIONPAY_POS_RECEIPT`
- 税收完税证明：`TAX_CERTIFICATE`

### 医疗票据

- 医疗门诊发票：`MEDICAL_INVOICE`
- 医疗住院发票：`MEDICAL_INPATIENT_INVOICE`
- 医疗费用结算单：`MEDICAL_EXPENSE_SETTLEMENT`

### 金融单据

- 银行汇票：`BANK_DRAFT`
- 银行承兑汇票：`BANK_ACCEPTANCE_BILL`
- 电子银行承兑汇票：`ELECTRONIC_BANK_ACCEPTANCE_BILL`
- 商业承兑汇票：`COMMERCIAL_ACCEPTANCE_BILL`
- 电子商业承兑汇票：`ELECTRONIC_COMMERCIAL_ACCEPTANCE`
- 银行支票：`BANK_CHECK`
- 银行回单：`BANK_RECEIPT`
- 进账单：`DEPOSIT_SLIP`
- 电汇凭证：`TELEGRAPHIC_TRANSFER_VOUCHER`
- 支款凭证：`WITHDRAWAL_VOUCHER`
- 移动支付账单：`MOBILE_PAYMENT_BILL`
- 财政授权支付凭证：`FISCAL_AUTH_PAYMENT_VOUCHER`
- 海关专用缴款书：`CUSTOMS_PAYMENT_RECEIPT`
- 海关进/出口货物报关单：`CUSTOMS_DECLARATION`
- 国际汇票：`INTERNATIONAL_BILL`
- 商业发票：`COMMERCIAL_INVOICE`
- 原产地证明：`CERTIFICATE_OF_ORIGIN`
- 货物运输保险单：`CARGO_TRANSPORT_INSURANCE`
- 装箱单：`PACKING_LIST`
- 提单：`BILL_OF_LADING`

## OCR 返回结果

工具返回统一结构：

```json
{
  "code": 200,
  "message": "SUCCESS",
  "data": []
}
```

- `code=200`：识别成功。
- `code=500`：识别失败，`message` 包含原因，`data` 通常为 `null`。
- `data`：识别结果数组。一份多页文件或包含多个凭证时可能有多个元素。

每个 `data` 元素包含：

- `fileIndex`：文件页索引。
- `cutIndex`：页面中被切分出的凭证索引。
- `coordinate`：凭证或识别区域坐标数组。
- `confidence`：整体识别置信度。

结果主体根据 `sceneType` 变化：

- `GENERAL` 返回 `ocrText`，即识别出的连续文字。
- `SEAL_CHARACTER_RECOGNITION` 返回 `stamps` 数组。每个印章包含 `stampPosition`、`stampConfidence`、`stampShape`、`stampColor`、`stampType` 和 `stampTextList`。
- `TABLE_RECOGNITION` 返回 `tables` 数组。每个表格包含 `type`（`wired_table` 有线表格 / `wireless_table` 无线表格）、`bbox` 和 HTML 格式的 `html`。
- 其他证照、票据和单据场景返回 `fields` 数组。字段包含英文 `key`、中文 `name` 和单值 `value`；明细类字段使用二维数组 `listValue`。

## OCR 调用决策

1. 先判断用户要识别的文件类型，再选择最具体的 `sceneType`。例如，增值税发票使用 `VAT_INVOICE`，不要使用泛化的 `GENERAL`，除非用户上传的文件类型没有具体的 `sceneType` 对应，或用户只需要原始文字。
2. 仅需要原文时使用 `GENERAL`；需要表格单元格结构时使用 `TABLE_RECOGNITION`；需要印章位置和印章文字时使用 `SEAL_CHARACTER_RECOGNITION`。
3. 成功后根据返回主体读取结果：票据/证照优先解析 `fields`，通用识别读取 `ocrText`，表格读取 `tables[*].html`，印章读取 `stamps`。
4. 识别失败时保留 `message` 的错误语义并向用户说明，不要把失败响应当作空的成功结果。

## OCR 如何展示

1. 将 API 返回结果转化为 markdown 形式进行可视化展示，最好以表格形式展示。若识别结果中有细项数据部分，细项数据可另起表格展示；
2. 将 API 返回结果 json 数据存入临时文件，用户可点击 `查看原始结果JSON` 查看该 json 数据内容；
3. API 返回结果为用户上传文件识别信息，展示环境也是用户本地环境，不涉及隐私泄露，不要进行脱敏，请将所有内容全部展示，否则用户会认为识别有误。

---

# 能力二：高精度文档解析

异步接口。自研高精度模型驱动，将 PDF、Office 文档、表格和图片等复杂文档还原为带层级结构的 Markdown 数据。

调用流程：`fileUploadPresign`（本地文件）→ 上传脚本 → `documentParsing` → `getTaskResult` 轮询（`ocrType=DOC_PARING`）。

## 文档解析适用场景

- 解析学术论文、技术报告、合同、招投标文件、政务材料等多页文档。
- 提取表格、目录、段落、公式、化学分子式、图片和印章等版面元素。
- 对扫描件或方向不确定的文档进行方向矫正。
- 需要保留 Markdown 结构，或需要把解析结果继续入库、摘要、问答的场景。

## 文档解析调用决策

- 复杂表格：将 `isTableCls` 设为 `true`。
- 扫描件、旋转页面：将 `isDocOri` 设为 `true`。
- 需要印章识别：将 `enforceSeal` 设为 `true`。
- 数学或科技文档：将 `isInlineFormula` 设为 `true`。
- 只解析指定页面：使用 `pageIndex`，例如 `1` 或 `1-5`；不传则解析全部页面。

轮询 `getTaskResult` 时，`ocrType` 填 `DOC_PARING`。根据 `taskStatus` 分支处理。查询请求本身返回 `code: 500` 时，可在确认任务 ID 后重试；不要把请求错误误判为解析任务失败。

## 文档解析如何展示

1. 解析成功后优先展示 `markdowns[].markdownContent`，该字段是完整的 Markdown 内容（图片已内嵌为 base64），可以直接展示。
2. `resultJsonFile` 表示文档解析结果 JSON 文件链接，用户可点击 `查看原始结果JSON` 下载该文件；
3. 处理中时明确告知用户任务仍在处理，并继续轮询；失败时展示 `errorMessage` 和 `errorCode`，同时说明任务未成功完成。对于超长文档，可先向用户报告状态，完成后再分段展示结果。

---

# 能力三：文档格式转换

异步接口。支持 PDF、图片等文档格式之间的互转，高保真还原原始排版。

调用流程：`fileUploadPresign`（本地文件）→ 上传脚本 → `fileConversion` → `getTaskResult` 轮询（`ocrType` 与提交时一致）。

## 格式转换适用场景

- 将 PDF 文档转换为可编辑的 Word 文件，保留原始排版和格式。
- 将扫描件或图片中的文字内容转换为 Word 文档。
- 将图片内容转换为 PPT 演示文稿。
- 科研文献、合同标书、财报报表、课件及政务公文等多场景文档格式互转。
- 对扫描件或方向不确定的文档进行方向矫正。
- 需要高保真保留表格、公式、印章等复杂元素的文档转换。

## 格式转换调用决策

- PDF 文件转 Word：将 `ocrType` 设为 `PDF_TO_WORD`。
- 图片转 Word：将 `ocrType` 设为 `IMAGE_TO_WORD`。
- 图片转 PPT：将 `ocrType` 设为 `IMAGE_TO_PPT`。
- 复杂表格：将 `isTableCls` 设为 `true`。
- 扫描件、旋转页面：将 `isDocOri` 设为 `true`。
- 需要印章识别：将 `enforceSeal` 设为 `true`。
- 数学或科技文档：将 `isInlineFormula` 设为 `true`。
- 只转换指定页面：使用 `pageIndex`，例如 `1` 或 `1-5`；不传则转换全部页面。

轮询 `getTaskResult` 时，`ocrType` 必须与提交 `fileConversion` 时一致。根据 `task_status` 分支处理。查询请求本身返回 `code: 500` 时，可在确认任务 ID 后重试；不要把请求错误误判为转换任务失败。

## 格式转换如何展示

1. 转换成功后优先展示 `results` 列表中的文件 URL，这些是转换完成后的文件下载地址，可以点击下载或直接提供给用户。
2. 多个结果文件按顺序逐一展示，并说明每个文件的用途（如果能够区分）。
3. 处理中时明确告知用户任务仍在处理，并继续轮询；失败时展示 `error_message` 和 `error_code`，同时说明任务未成功完成。对于大批量或长文档的转换，可先向用户报告状态，完成后再展示结果。

---

# 能力选择总结

根据用户意图选择对应的能力：

| 用户意图                             | 使用能力     | 核心工具链                                                                                      | 执行方式 |
|----------------------------------|----------|--------------------------------------------------------------------------------------------|------|
| 识别图片/文档中的文字、印章、表格              | OCR 文字识别 | `fileUploadPresign`（本地）→ 上传脚本 → `ocrRecognition`                                           | 同步   |
| 抽取票据、证照、资质、单据的结构化字段            | OCR 文字识别 | 同上                                                                                         | 同步   |
| 解析论文、合同、标书等文档的完整版式，输出 Markdown | 高精度文档解析  | `fileUploadPresign`（本地）→ 上传脚本 → `documentParsing` → `getTaskResult(ocrType=DOC_PARING)` 轮询    | 异步   |
| 将 PDF 转为可编辑的 Word                | 文档格式转换   | `fileUploadPresign`（本地）→ 上传脚本 → `fileConversion(ocrType=PDF_TO_WORD)` → `getTaskResult` 轮询  | 异步   |
| 将图片转为 Word                      | 文档格式转换   | `fileUploadPresign`（本地）→ 上传脚本 → `fileConversion(ocrType=IMAGE_TO_WORD)` → `getTaskResult` 轮询 | 异步   |
| 将图片转为 PPT                       | 文档格式转换   | `fileUploadPresign`（本地）→ 上传脚本 → `fileConversion(ocrType=IMAGE_TO_PPT)` → `getTaskResult` 轮询  | 异步   |

如果用户提供的文件本身是网络 URL，则跳过 `fileUploadPresign` 和上传脚本步骤，直接调用后续工具。