---
name: tencentcloud-ocr-questionmarkagent
description: 腾讯云试题批改Agent(SubmitQuestionMarkAgentJob/DescribeQuestionMarkAgentJob)接口调用技能。当用户需要对试卷图片或试题图片中的K12试卷或试题进行自动批改、手写答案识别、知识点分析时,应使用此技能。支持整卷图片批改和单题图片批改,提供题目切题、正误判定、答案对比、错误分析、知识点输出等结构化评估结果。异步接口,先提交任务再轮询查询结果。
version: 1.0.3
display_name: "腾讯云试题批改Agent"
display_name_en: "Tencent Cloud Question Mark Agent"
description_zh: "调用腾讯云试题批改Agent接口，面向K12教育场景，支持整卷/单题端到端批改，包含试卷切题、手写答案识别、正误判定、错误分析和知识点输出。支持深度思考模式和多种图片/PDF格式输入。"
description_en: "Tencent Cloud Question Mark Agent for K12 education. Supports full-paper and single-question grading with handwriting recognition, answer comparison, error analysis, and knowledge point extraction."
visibility: "public"
---

# 腾讯云试题批改Agent (SubmitQuestionMarkAgentJob / DescribeQuestionMarkAgentJob)

## 用途

调用腾讯云OCR试题批改Agent接口，面向K12教育场景的试题批改产品，支持整卷/单题端到端处理（试卷切题+题目批改+手写坐标回显），聚焦试题批改（含手写答案）和试题解析（不含手写答案）。精准输出题目、正误判定、答案对比、错误分析及知识点等结构化评估结果。低年级算式批改效果优于线上数学作业批改。

核心能力：
- **异步双接口模式**：Submit 提交任务获取 JobId → Describe 轮询查询结果（DONE/FAIL 时完成）
- **整卷批改**：自动切题后逐题批改，返回每道题目的批改信息
- **单题批改**：跳过切题环节，直接对单题进行批改，支持传入参考答案
- **深度思考**：可选开启深度思考模式，进行更深层次推理分析（速度更慢）
- **知识点输出**：可配置输出题目关联的知识点信息
- **正确答案输出**：可配置输出题目的正确答案
- **手写答案坐标**：可配置输出手写答案在原图中的坐标位置
- **多格式输入**：支持 PNG、JPG、JPEG、BMP、GIF、WEBP、HEIC、TIFF、HEIF 及 PDF 格式

官方文档：
- 提交任务：https://cloud.tencent.com/document/api/866/128273
- 查询任务：https://cloud.tencent.com/document/api/866/128274

## 使用时机

当用户提出以下需求时触发此技能：
- 需要对试卷图片/PDF进行自动批改
- 需要识别手写答案并判断正误
- 需要对K12试题进行批改分析
- 需要获取试题的知识点信息
- 需要获取试题的正确答案
- 需要对单道题目进行批改（含参考答案）
- 涉及试卷切题、试题解析的任何场景

## 环境要求

- Python 3.6+
- 依赖：`tencentcloud-sdk-python`（通过 `pip install tencentcloud-sdk-python` 安装）
- 环境变量：
  - `TENCENTCLOUD_SECRET_ID`：腾讯云API密钥ID
  - `TENCENTCLOUD_SECRET_KEY`：腾讯云API密钥Key

## 使用方式

运行 `scripts/main.py` 脚本完成试题批改。该接口为**异步接口**，脚本会自动提交任务并轮询查询结果。

### 请求参数

#### 提交任务 (SubmitQuestionMarkAgentJob) 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageBase64 | str | 否(二选一) | 图片/PDF的Base64值，编码后不超过10M，分辨率建议600*800以上，支持PNG/JPG/JPEG/BMP/PDF格式 |
| ImageUrl | str | 否(二选一) | 图片/PDF的URL地址，下载时间不超过3秒。都提供时只使用ImageUrl。建议存储于腾讯云 |
| PdfPageNumber | int | 否 | PDF页码，仅支持单页识别，默认1 |
| BoolSingleQuestion | bool | 否 | 是否单题批改（跳过切题），默认false |
| EnableDeepThink | bool | 否 | 是否开启深度思考（更深层推理，速度更慢），默认false |
| QuestionConfigMap | str | 否 | 题目信息输出配置（JSON字符串），可选key：KnowledgePoints(输出知识点)/TrueAnswer(输出正确答案)/ReturnAnswerPosition(输出手写答案坐标) |
| ReferenceAnswer | str | 否 | 单题批改时的参考答案，仅单题时有效，多题时不生效 |

#### 查询任务 (DescribeQuestionMarkAgentJob) 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| JobId | str | 是 | 任务唯一ID，由Submit接口返回，长度不超过32字符 |
| **UserAgent** | **str** | **否** | **请求来源标识(可选)，用于追踪调用来源，统一固定为`Skills`** |

### 输出格式

识别成功后返回 JSON 格式结果：

**格式化输出模式（默认）**：
```json
{
  "任务ID": "1410885500986064896",
  "任务状态": "DONE",
  "切题数量": "2",
  "旋转角度": 0.0,
  "批改结果": [
    {
      "题号": 1,
      "题干": "1. 小琪在做作业时发现有一道题的一部分被墨水遮住了...",
      "子题": [
        {
          "题号": "1-1",
          "题干": "(1)小琪猜测,墨水遮住的内容是"2a",请你根据小琪的猜测完成计算;",
          "答案列表": [
            {
              "手写答案": "\\frac{2}{a-1}...",
              "是否正确": false,
              "答案分析": "首先将除法转化为乘法，对分子分母因式分解后约分...",
              "正确答案": "...",
              "知识点": ["分式运算", "因式分解"],
              "答案坐标": [113, 648, 558, 648, 558, 698, 113, 698]
            }
          ]
        }
      ]
    }
  ],
  "RequestId": "xxx"
}
```

**原始输出模式（--raw）**：
```json
{
  "JobId": "1410885500986064896",
  "JobStatus": "DONE",
  "ErrorCode": "",
  "ErrorMessage": "",
  "Angle": 0.0,
  "MarkInfos": [
    {
      "MarkItemTitle": "1. 小琪在做作业时...",
      "AnswerInfos": [],
      "MarkInfos": [
        {
          "MarkItemTitle": "(1)小琪猜测...",
          "AnswerInfos": [
            {
              "HandwriteInfo": "\\frac{2}{a-1}...",
              "IsCorrect": false,
              "AnswerAnalysis": "首先将除法转化为乘法...",
              "RightAnswer": "",
              "KnowledgePoints": [],
              "HandwriteInfoPositions": [113, 648, 558, 648, 558, 698, 113, 698]
            }
          ],
          "MarkInfos": []
        }
      ]
    }
  ],
  "RequestId": "xxx"
}
```

### 响应数据结构说明

#### SubmitQuestionMarkAgentJob 响应

| 参数 | 类型 | 说明 |
|------|------|------|
| JobId | str | 任务唯一ID，用于查询结果 |
| QuestionInfo | list of QuestionInfo | 切题题目边框坐标列表（BoolSingleQuestion=true时为空） |
| QuestionCount | str | 切题数量，作为计费题目数总量 |
| RequestId | str | 唯一请求ID |

#### DescribeQuestionMarkAgentJob 响应

| 参数 | 类型 | 说明 |
|------|------|------|
| JobStatus | str | 任务状态：WAIT(等待中)/RUN(执行中)/FAIL(失败)/DONE(成功) |
| ErrorCode | str | 任务执行错误码（非FAIL时为空） |
| ErrorMessage | str | 任务执行错误信息（非FAIL时为空） |
| Angle | float | 图片旋转角度（角度制），水平方向为0，顺时针为正 |
| MarkInfos | list of MarkInfo | 试题批改信息 |
| RequestId | str | 唯一请求ID |

**MarkInfo 结构（嵌套递归）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| MarkItemTitle | str | 题目的题干信息 |
| AnswerInfos | list of AnswerInfo | 批改答案列表（按从左到右、从上到下排列） |
| MarkInfos | list of MarkInfo | 嵌套子题信息（无子题则为空） |

**AnswerInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| HandwriteInfo | str | 手写答案内容（如选择题的手写选项、填空题的手写内容） |
| IsCorrect | bool | 答案是否正确 |
| AnswerAnalysis | str | 答案分析结果 |
| HandwriteInfoPositions | list of int | 答案区域4角点坐标（长度8数组：左上/右上/右下/左下），需配置ReturnAnswerPosition。可能返回null |
| RightAnswer | str | 正确答案内容，需配置 QuestionConfigMap 的 TrueAnswer 为 true |
| KnowledgePoints | list of str | 知识点内容，需配置 QuestionConfigMap 的 KnowledgePoints 为 true。可能返回null |

**QuestionInfo 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| Angle | float | 旋转角度 |
| Height | int | 预处理后图片高度 |
| Width | int | 预处理后图片宽度 |
| ResultList | list of ResultList | 文档元素（可能返回null） |
| OrgHeight | int | 输入图片高度 |
| OrgWidth | int | 输入图片宽度 |
| ImageBase64 | str | 预处理后的图片base64编码 |

### 错误码说明

| 错误码 | 含义 |
|--------|------|
| FailedOperation.DownLoadError | 文件下载失败 |
| FailedOperation.ImageDecodeFailed | 图片解码失败 |
| FailedOperation.ImageSizeTooLarge | 图片尺寸过大，请确保编码后不超过10M |
| FailedOperation.OcrFailed | OCR识别失败 |
| FailedOperation.PDFParseFailed | PDF解析失败 |
| FailedOperation.UnKnowError | 未知错误 |
| FailedOperation.UnKnowFileTypeError | 未知的文件类型 |
| FailedOperation.UnOpenError | 服务未开通，请先在腾讯云控制台开通试题批改Agent服务 |
| InvalidParameterValue.InvalidParameterValueLimit | 参数值错误 |
| LimitExceeded.TooLargeFileError | 文件内容太大 |
| ResourceUnavailable.InArrears | 账号已欠费 |
| ResourceUnavailable.ResourcePackageRunOut | 账号资源包耗尽 |
| ResourcesSoldOut.ChargeStatusException | 计费状态异常 |

### 重要业务逻辑

1. **异步双接口模式**：Submit 提交任务 → Describe 轮询，JobStatus 为 DONE/FAIL 时完成
2. **Submit 计费，Describe 不计费**
3. **ImageBase64 和 ImageUrl 必须提供其一**，都提供时只使用 ImageUrl
4. 支持格式：PNG/JPG/JPEG/BMP/GIF/WEBP/HEIC/TIFF/HEIF 及 PDF
5. PdfPageNumber 必须为正整数，仅支持单页识别
6. BoolSingleQuestion=true 时跳过切题，直接单题批改
7. QuestionConfigMap 示例：`{"KnowledgePoints":true,"TrueAnswer":true,"ReturnAnswerPosition":false}`
8. ReferenceAnswer 仅单题时有效，多题时不生效
9. JobId 长度不超过32字符
10. **默认接口请求并发限制：10题/分钟**
11. 建议图片存储于腾讯云COS以获得更高的下载速度和稳定性
12. MarkInfo 为递归嵌套结构，可能存在多层子题

### 调用示例

```bash
# 通过URL进行整卷批改（输出知识点和正确答案）
python scripts/main.py --image-url "https://example.com/exam_paper.jpg" \
  --question-config '{"KnowledgePoints":true,"TrueAnswer":true}'

# 通过URL进行单题批改（带参考答案）
python scripts/main.py --image-url "https://example.com/single_question.jpg" \
  --single-question --reference-answer "x=2"

# 开启深度思考模式
python scripts/main.py --image-url "https://example.com/exam.jpg" --enable-deep-think

# 通过文件路径进行批改（自动Base64编码）
python scripts/main.py --image-base64 ./exam_paper.png

# 批改PDF试卷（指定页码）
python scripts/main.py --image-base64 ./exam.pdf --pdf-page-number 2

# 输出原始JSON响应
python scripts/main.py --image-url "https://example.com/exam.jpg" --raw

# 指定地域和自定义轮询参数
python scripts/main.py --image-url "https://example.com/exam.jpg" \
  --region ap-beijing --poll-interval 3 --poll-timeout 300```
