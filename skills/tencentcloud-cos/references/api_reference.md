# COS Node.js SDK 操作参考

本文档记录 `scripts/cos_node.mjs` 所有操作的详细参数。

**环境设置**：首次使用请运行 `scripts/setup.sh`，详见 `SKILL.md` 首次使用章节。

**官方文档链接：**
- COS Node.js SDK: https://cloud.tencent.com/document/product/436/8629
- 数据万象(CI): https://cloud.tencent.com/document/product/460
- cos-nodejs-sdk-v5 GitHub: https://github.com/tencentyun/cos-nodejs-sdk-v5

---

## 通用说明

所有命令格式：`node scripts/cos_node.mjs <action> [--option value ...]`

- 输出统一为 JSON 格式
- `success: true` 表示成功，退出码 0
- `success: false` 表示失败，退出码 1
- 所有 `--key` 参数为存储桶内的相对路径，如 `images/photo.jpg`

---

## COS 存储操作

### upload — 上传本地文件
- `--file` (string, **必需**): 本地文件路径
- `--key` (string, 可选): 存储桶中的对象键，默认使用文件名

### put-string — 上传字符串内容
- `--content` (string, **必需**): 要上传的字符串内容
- `--key` (string, **必需**): 存储桶中的对象键
- `--content-type` (string, 可选): MIME 类型，默认 `text/plain`

### download — 下载文件
- `--key` (string, **必需**): 存储桶中的对象键
- `--output` (string, 可选): 本地保存路径，默认使用文件名

### list — 列出文件
- `--prefix` (string, 可选): 路径前缀过滤
- `--max-keys` (number, 可选): 最大返回数量，默认 100

### sign-url — 获取签名下载链接
- `--key` (string, **必需**): 存储桶中的对象键
- `--expires` (number, 可选): 签名有效期（秒），默认 3600

### head — 查看文件元信息
- `--key` (string, **必需**): 存储桶中的对象键

### delete — 删除文件
- `--key` (string, **必需**): 存储桶中的对象键

---

## CI 图片基础处理

### image-info — 获取图片元数据
- `--key` (string, **必需**): 图片在存储桶中的路径

### watermark-font — 添加文字水印
- `--key` (string, **必需**): 图片在存储桶中的路径
- `--text` (string, **必需**): 水印文字内容（支持中文）

处理后的图片存储到同一存储桶，文件名格式 `{date}_{原名}_{随机码}`。

---

## CI AI 图片处理

### assess-quality — 图片质量评估
- `--key` (string, **必需**): 图片在存储桶中的路径

返回图片质量评分。

### ai-super-resolution — AI 超分辨率
- `--key` (string, **必需**): 图片在存储桶中的路径

处理后的高分辨率图片存储到同一存储桶。

### ai-pic-matting — AI 智能裁剪
- `--key` (string, **必需**): 图片在存储桶中的路径
- `--width` (string, 可选): 输出宽度
- `--height` (string, 可选): 输出高度

### ai-qrcode — 二维码识别
- `--key` (string, **必需**): 含二维码的图片路径

返回识别到的二维码内容。

---

## CI 文档处理

### create-doc-to-pdf-job — 文档转 PDF
- `--key` (string, **必需**): 文档在存储桶中的路径（支持 docx/xlsx/pptx 等）

提交异步任务，脚本自动轮询（最多 10 次，间隔 2 秒）等待结果。转换后的 PDF 存储到同一存储桶。

### describe-doc-job — 查询文档处理任务
- `--job-id` (string, **必需**): 任务 ID

---

## CI 媒体处理

### create-media-smart-cover-job — 视频智能封面
- `--key` (string, **必需**): 视频在存储桶中的路径

提交异步任务，脚本自动轮询（最多 10 次，间隔 4 秒）等待结果。

### describe-media-job — 查询媒体处理任务
- `--job-id` (string, **必需**): 任务 ID

---

## CI MetaInsight（以图搜图/文本搜图）

需要设置 `TENCENT_COS_DATASET_NAME` 环境变量。

### image-search-pic — 以图搜图
- `--uri` (string, **必需**): 查询图片地址

### image-search-text — 文本搜图
- `--text` (string, **必需**): 检索文本

---

## CI 通用请求（扩展入口）

### ci-request — 通用 CI API 请求

用于调用尚未封装为独立 action 的 CI 能力（如内容审核、文件处理等）。

- `--method` (string, 可选): HTTP 方法，默认 `GET`
- `--path` (string, **必需**): CI API 路径，如 `image/auditing`、`file_jobs`、`jobs`
- `--body` (string, 可选): 请求体内容
- `--content-type` (string, 可选): 请求体类型，默认 `application/xml`
- `--query` (string, 可选): 查询参数，JSON 字符串格式

请求自动发送到 `https://{Bucket}.ci.{Region}.myqcloud.com/{path}`。

**扩展示例：**

```bash
# 内容审核 — 提交图片审核任务
ci-request --method POST --path "image/auditing" --body '<Request><Input><Object>images/test.jpg</Object></Input><Conf><BizType></BizType></Conf></Request>'

# 文件处理 — 提交文件哈希计算
ci-request --method GET --path "test.docx" --query '{"ci-process":"filehash","type":"md5"}'

# 查询任务结果
ci-request --method GET --path "file_jobs/<jobId>"
```
