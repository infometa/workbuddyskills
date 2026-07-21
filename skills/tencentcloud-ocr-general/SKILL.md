---
name: tencentcloud-ocr-general
description: 腾讯云广告文字识别(AdvertiseOCR)接口调用技能。当用户需要从图片中识别文字内容时,应使用此技能。支持中英文、横排、竖排及倾斜场景的图片文字识别,支持90度、180度、270度翻转场景的图片识别,返回文本框位置与文字内容。支持图片Base64和URL两种输入方式。
version: 1.0.3
display_name: "腾讯云广告文字识别"
display_name_en: "Tencent Cloud Advertise OCR"
description_zh: "调用腾讯云OCR广告文字识别接口，支持中英文、横排竖排及倾斜场景的图片文字识别，支持90/180/270度翻转场景识别。返回文本框四顶点坐标和置信度。适用于广告、海报等多方向文字场景。"
description_en: "Tencent Cloud AdvertiseOCR API for text recognition in images. Supports horizontal, vertical, tilted, and rotated (90/180/270 degree) text recognition with polygon coordinates and confidence scores."
visibility: "public"
---

# 腾讯云广告文字识别 (AdvertiseOCR)

## 用途

调用腾讯云OCR广告文字识别接口，支持图片内文字的检测和识别，返回文本框位置与文字内容。具有较高召回率和准确率。

核心能力：
- **中英文识别**：支持中英文混合文字识别
- **多方向支持**：支持横排、竖排以及倾斜场景文字识别
- **翻转支持**：支持90度、180度、270度翻转场景文字识别
- **坐标返回**：返回每个文本行的四顶点坐标（Polygon）
- **置信度评估**：返回每个文本行的识别置信度（0~100）

官方文档：https://cloud.tencent.com/document/api/866/49524

默认接口请求频率限制：20次/秒。

## 使用时机

当用户提出以下需求时触发此技能：
- 需要从图片中提取文字信息
- 需要识别图片上的文字内容
- 涉及文字OCR识别的任何场景
- 需要获取图片中文字的位置坐标信息

## 环境要求

- Python 3.6+
- 依赖：`tencentcloud-sdk-python`（通过 `pip install tencentcloud-sdk-python` 安装）
- 环境变量：
  - `TENCENTCLOUD_SECRET_ID`：腾讯云API密钥ID
  - `TENCENTCLOUD_SECRET_KEY`：腾讯云API密钥Key

## 使用方式

运行 `scripts/main.py` 脚本完成图片文字识别。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageBase64 | str | 否(二选一) | 图片Base64值，编码后不超过10M，分辨率建议600*800以上，支持PNG/JPG/JPEG/BMP |
| ImageUrl | str | 否(二选一) | 图片URL地址，建议存储于腾讯云COS。都提供时仅使用ImageUrl |
| **UserAgent** | **str** | **否** | **请求来源标识(可选)，用于追踪调用来源，统一固定为`Skills`** |

### 输出格式

识别成功后返回 JSON 格式结果：

```json
{
  "TextDetections": [
    {
      "DetectedText": "识别出的文本行内容",
      "Confidence": 99,
      "Polygon": [
        {"X": 0, "Y": 0},
        {"X": 100, "Y": 0},
        {"X": 100, "Y": 50},
        {"X": 0, "Y": 50}
      ],
      "AdvancedInfo": "{\"Parag\":{\"ParagNo\":1}}"
    }
  ],
  "TextCount": 1,
  "ImageSize": {
    "Width": 800,
    "Height": 600
  },
  "RequestId": "xxx"
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| TextDetections | list | 检测到的文本信息列表 |
| TextDetections[].DetectedText | str | 识别出的文本行内容 |
| TextDetections[].Confidence | int | 置信度 0~100 |
| TextDetections[].Polygon | list of Coord | 文本行坐标，四个顶点坐标（X, Y） |
| TextDetections[].AdvancedInfo | str | 扩展字段，含段落信息Parag(ParagNo) |
| TextCount | int | 检测到的文本行数量 |
| ImageSize | object | 图片分辨率信息，含Width和Height（单位px） |
| RequestId | str | 唯一请求ID |

### 错误码说明

| 错误码 | 含义 |
|--------|------|
| FailedOperation.DownLoadError | 文件下载失败 |
| FailedOperation.EmptyImageError | 图片内容为空 |
| FailedOperation.EngineRecognizeTimeout | 引擎识别超时 |
| FailedOperation.ImageDecodeFailed | 图片解码失败 |
| FailedOperation.ImageNoText | 图片中未检测到文本 |
| FailedOperation.LanguageNotSupport | 输入的Language不支持 |
| FailedOperation.OcrFailed | OCR识别失败 |
| FailedOperation.UnKnowError | 未知错误 |
| FailedOperation.UnOpenError | 服务未开通 |
| InvalidParameterValue.InvalidParameterValueLimit | 参数值错误 |
| LimitExceeded.TooLargeFileError | 文件内容太大 |
| ResourceUnavailable.InArrears | 账号已欠费 |
| ResourceUnavailable.ResourcePackageRunOut | 账号资源包耗尽 |
| ResourcesSoldOut.ChargeStatusException | 计费状态异常 |

### 业务逻辑说明

1. ImageBase64和ImageUrl必须提供其一，都提供时只使用ImageUrl
2. 图片经Base64编码后不超过10M，分辨率建议600*800以上
3. 支持PNG、JPG、JPEG、BMP格式
4. 始终计费

### 调用示例

```bash
# 通过URL识别图片文字
python scripts/main.py --image-url "https://example.com/ad_image.jpg"

# 通过文件路径(自动Base64编码)识别
python scripts/main.py --image-base64 ./ad_image.jpg

# 通过Base64文本文件识别
python scripts/main.py --image-base64 ./base64.txt

# 指定地域
python scripts/main.py --image-url "https://example.com/ad_image.jpg" --region ap-beijing```
