---
name: tencentcloud-ocr
description: 腾讯云通用文字识别（高精度版）(GeneralAccurateOCR) 技能包。当用户发送/粘贴图片、提供图片URL、或要求识别图片中的文字时，应自动调用此技能。支持图像整体文字的检测和识别，支持中文、英文、中英文、数字和特殊字符号的识别，并返回文字框位置和文字内容。适用于文字较多、版式复杂、对识别准召率要求较高的场景，如网络图片、街景店招牌、法律卷宗、多语种简历等场景。支持图片Base64和URL两种输入方式，同时支持PDF文件识别和单字信息返回。对于简历识别场景，提供专门的结构化解析指引（详见 references/resume-parsing.md）。
version: 1.0.4
display_name: "腾讯云通用文字识别（高精度版）"
display_name_en: "Tencent Cloud General OCR (High Accuracy)"
description_zh: "调用腾讯云OCR通用文字识别（高精度版）接口，对图片中的文字进行高精度识别。支持中英文、数字和特殊字符识别，适用于文字较多、版式复杂的场景。支持图片URL、Base64、PDF输入，可返回单字信息和文字框位置。内含简历结构化解析指引。"
description_en: "High-accuracy OCR powered by Tencent Cloud GeneralAccurateOCR API. Recognizes Chinese, English, numbers and special characters from images. Supports image URL, Base64, and PDF input with optional per-character positioning."
visibility: "public"
---

# 腾讯云通用文字识别（高精度版）(GeneralAccurateOCR)

## 用途

调用腾讯云OCR通用文字识别（高精度版）接口，对图片中的文字进行精准提取。

核心能力：
- **文字识别**：高精度识别图片中的文字内容，返回完整识别文本
- **图片URL直接识别**：支持直接传入图片URL进行识别，无需下载图片
- **PDF支持**：支持对PDF文件进行文字识别（单页）
- **单字信息**：可选返回每个单字的位置和置信度信息
- **多语种简历结构化识别**：基于 OCR 结果，对简历进行结构化提取与格式化输出（详见 `references/resume-parsing.md`）

官方文档：https://cloud.tencent.com/document/api/866/37831

## 📚 可用资源

### References（场景化指引）
- `references/resume-parsing.md` - 多语种简历结构化识别指引（处理流程、Prompt模板、输出格式化模板、格式化规则）

## 使用时机

当用户提出以下需求时触发此技能：
- **用户发送了图片**（包括粘贴图片、上传图片、截图等），需要识别其中的文字内容
- **用户提供了图片URL**（如 `https://xxx.com/image.jpg`、`https://xxx.cos.xxx/xxx.png` 等），需要识别其中的文字
- 用户说"识别这张图"、"看看图片里写了什么"、"提取图片文字"、"OCR"等表达
- 需要从图片或PDF中提取文字内容
- 需要对各类文档、图片等进行文字识别
- 涉及通用文字OCR识别的任何场景
- 需要从简历图片/PDF中识别并结构化提取简历信息（请参考 `references/resume-parsing.md` 指引）
- 需要对多语种简历进行识别和格式化输出（请参考 `references/resume-parsing.md` 指引）

### 🤖 自动触发指引（面向大模型）

当检测到以下信号时，应**自动调用**此技能，无需用户显式要求"OCR"：

1. **用户消息中包含图片URL**：检测到 `http(s)://` 开头且以图片扩展名（`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.webp`, `.tiff`）结尾的URL，或包含已知图片托管域名（如 `cos.`、`cdn.`、`oss.`、`imgur.com` 等）的URL
2. **用户上传/粘贴了图片**：对话中出现了图片附件或图片Base64数据
3. **用户意图关键词**：消息中包含"识别"、"文字"、"OCR"、"提取"、"读取"、"看看写了什么"等与文字识别相关的表达

**调用方式**：
- 如果用户提供了图片URL，直接使用 `--image-url` 参数传入
- 如果用户上传了图片文件，使用 `--image-base64` 参数传入文件路径或Base64内容

## 环境要求

- Python 3.6+
- 依赖：`tencentcloud-sdk-python`（通过 `pip install tencentcloud-sdk-python` 安装）
- 环境变量：
  - `TENCENTCLOUD_SECRET_ID`：腾讯云API密钥ID
  - `TENCENTCLOUD_SECRET_KEY`：腾讯云API密钥Key

## 使用方式

运行 `scripts/main.py` 脚本完成文字识别。脚本使用 SDK 高层接口 `client.GeneralAccurateOCR(req)` 进行调用，具有类型安全和自动反序列化的优势。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageBase64 | str | 否(二选一) | 图片Base64值，不超过10MB |
| ImageUrl | str | 否(二选一) | 图片URL地址，优先使用 |
| IsPdf | bool | 否 | 是否开启PDF识别，默认false |
| PdfPageNumber | int | 否 | 需要识别的PDF页码，IsPdf为true时有效，默认1 |
| IsWords | bool | 否 | 是否返回单字信息，默认false |
| **UserAgent** | **str** | **否** | **请求来源标识(可选)，用于追踪调用来源，统一固定为`Skills`** |

### ⚠️ UserAgent参数使用指南

**`--user-agent`参数是可选参数**，统一固定为`Skills`，无需手动传递。用于标识API调用来源，便于追踪和统计：

| 调用框架 | --user-agent 参数值 | 说明 |
|---------|--------------|------|
| 所有框架 | `Skills` | 统一固定值，不传递时也默认为此值 |

**实现说明**：
- 通过`--user-agent`命令行参数传递，SDK 会将其拼接为 `SDK_PYTHON_x.x.x; Skills` 注入到请求中
- 统一固定为`Skills`，未传递时也默认为此值
- 该标识会记录在ES日志的 `ReqBody.RequestClient` 字段中，可用于追踪来源

### 输出格式

识别成功后返回 JSON 格式结果：

```json
{
  "raw_text": "识别到的完整文字内容\n第二行文字\n第三行文字",
  "RequestId": "xxx"
}
```

无文字时返回：

```json
{
  "raw_text": "",
  "message": "No text detected in the image.",
  "RequestId": "xxx"
}
```

### 调用示例

```bash
# 用户提供了图片URL，直接传入识别（最常用场景）
python scripts/main.py --image-url "https://example.com/document.jpg"

# 用户上传了图片文件，使用 Base64 方式调用
python scripts/main.py --image-base64 "/path/to/document.jpg"

# 识别 PDF 文件中的文字
python scripts/main.py --image-url "https://example.com/doc.pdf" \
  --is-pdf true --pdf-page-number 1

# 返回单字信息
python scripts/main.py --image-url "https://example.com/document.jpg" --is-words true
```

## 密钥配置

### Step 1: 获取 API 密钥

🔗 **[腾讯云 API 密钥管理](https://console.cloud.tencent.com/cam/capi)**

### Step 2: 获取/购买 OCR 服务

🔗 **[腾讯云文字识别 OCR 购买页](https://buy.cloud.tencent.com/iai_ocr)**

在购买页面中选择 **通用文字识别（高精度版）** 完成购买。

### Step 3: 设置环境变量

**Linux / macOS：**
```bash
export TENCENTCLOUD_SECRET_ID="你的SecretId"
export TENCENTCLOUD_SECRET_KEY="你的SecretKey"
```

**Windows (PowerShell)：**
```powershell
$env:TENCENTCLOUD_SECRET_ID = "你的SecretId"
$env:TENCENTCLOUD_SECRET_KEY = "你的SecretKey"
```
