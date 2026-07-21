---
name: tencentcloud-cos
description: '腾讯云对象存储(COS)和数据万象(CI)集成技能。覆盖文件存储管理、AI处理和知识库三大核心场景。 存储场景：上传文件到云端、下载云端文件、批量管理存储桶文件、获取文件签名链接分享、查看文件元信息。 图片处理场景：图片质量评估打分、AI超分辨率放大、AI智能裁剪、二维码/条形码识别、添加文字水印、获取图片EXIF信息、 缩放、裁剪、旋转、格式转换。 文档处理场景：Word/Excel/PPT等办公文档转PDF、文档预览。
  媒体处理场景：视频智能封面提取、视频转码、视频截帧、获取媒体信息。 内容审核场景：图片/视频/音频/文本/文档内容审核，检测违规内容。 智能语音场景：语音识别（音频转文字）、语音合成（文字转语音）、音频降噪、人声分离。 文件处理场景：文件哈希计算、文件压缩打包、文件解压。 内容识别场景：图片标签识别、OCR文字识别。 知识库场景：一键创建知识库、上传文档到知识库、从知识库检索内容片段。 智能检索场景：MetaInsight以图搜图、以文搜图、人脸搜索、元数据检索、多模态文档检索。
  当用户提到以下关键词或口语化表述时应触发此技能： 上传到COS、腾讯云存储、对象存储、云存储、存储桶、Bucket、 图片处理、图片压缩、图片放大、超分辨率、抠图、裁剪、二维码识别、水印、 文档转换、转PDF、视频封面、智能封面、以图搜图、图片搜索、MetaInsight、 COS上传、COS下载、签名URL、腾讯云文件、数据万象、CI处理、 内容审核、图片审核、视频审核、文本审核、语音识别、语音合成、降噪、人声分离、
  OCR、文字识别、图片标签、 创建知识库、建一个知识库、上传到知识库、往知识库里加文件、查询知识库、 从知识库找、搜索知识库、知识库检索、文档检索、文档搜索。 即使用户没有明确提到COS或腾讯云，只要涉及"把文件传到云上"、"生成下载链接"、 "处理云端图片"、"帮我建个知识库"、"把文档放进知识库"、"从知识库里搜一下"、 "加密COS凭证"、"COS密钥不安全"、"加密一下COS密钥"、"保护COS密钥"等意图，也应该触发此技能。

  '
description_zh: 腾讯云 COS 对象存储、数据万象数据智能处理、MetaInsight多模态检索、知识库搭建
description_en: Tencent Cloud COS Object Storage, CI Data Intelligence Processing, MetaInsight Multi-modal Retrieval, Knowledge Base Setup
version: 1.1.5
metadata:
  clawdbot:
    emoji: ☁️
    requires:
      secrets:
      - SecretId
      - SecretKey
      optionalSecrets:
      - Token
      config:
      - Region
      - Bucket
      optionalConfig:
      - DatasetName
      - Domain
      - ServiceDomain
      - Protocol
      envMapping:
        SecretId: TENCENT_COS_SECRET_ID
        SecretKey: TENCENT_COS_SECRET_KEY
        Token: TENCENT_COS_TOKEN
        Region: TENCENT_COS_REGION
        Bucket: TENCENT_COS_BUCKET
        DatasetName: TENCENT_COS_DATASET_NAME
        Domain: TENCENT_COS_DOMAIN
        ServiceDomain: TENCENT_COS_SERVICE_DOMAIN
        Protocol: TENCENT_COS_PROTOCOL
      secretsDescription:
        SecretId:
          label: 腾讯云 API 密钥 ID
          type: cloud-credential
          provider: Tencent Cloud
          sensitivity: critical
          scope: COS object storage and CI data processing APIs
        SecretKey:
          label: 腾讯云 API 密钥 Key
          type: cloud-credential
          provider: Tencent Cloud
          sensitivity: critical
          scope: COS object storage and CI data processing APIs
        Token:
          label: STS 临时安全令牌
          type: session-token
          provider: Tencent Cloud STS
          sensitivity: high
          scope: Time-limited access (default 1800s), auto-expires
    security:
      credentialStorage:
        default: ephemeral
        ephemeral:
          description: Credentials exist only in shell session environment variables; nothing written to disk
          persistsToDisk: false
          recommendation: RECOMMENDED — use with STS temporary credentials
      requirements:
      - MUST use sub-account keys with least-privilege COS-only policy; root account keys are FORBIDDEN
      - STS temporary credentials are recommended; default behavior is ephemeral (no disk persistence)
      - Credentials are NEVER echoed back to the user in chat
    install:
    - id: node-cos-sdk
      kind: node
      package: cos-nodejs-sdk-v5
      label: Install COS Node.js SDK
---

# 腾讯云 COS 技能

一站式管理腾讯云对象存储(COS)和数据万象(CI)，通过统一的 Node.js SDK 脚本提供以下能力：

- **文件存储**：上传、下载、列出、删除文件，获取签名下载链接，批量操作，复制
- **存储桶管理**：列出/创建存储桶，ACL、跨域、标签、版本控制、生命周期管理
- **图片处理**：缩放、裁剪、旋转、格式转换、文字水印、质量评估、超分辨率、智能裁剪、二维码识别
- **内容识别**：图片标签识别、OCR 文字识别
- **文档处理**：办公文档转 PDF、文档预览（图片/HTML）
- **媒体处理**：视频智能封面、转码、截帧、媒体信息
- **内容审核**：图片/视频/音频/文本/文档违规检测
- **智能语音**：语音识别、语音合成、音频降噪、人声分离
- **文件处理**：哈希计算、压缩、解压
- **智能检索 MetaInsight**：数据集管理、索引管理、以图搜图、文本搜图、人脸搜索、元数据检索、多模态文档检索
- **🚀 知识库**：一键创建知识库（自动创建桶+数据集+绑定），上传文档到知识库，语义检索知识库内容

所有操作通过 `scripts/cos_node.mjs` 单一脚本完成，输出 JSON 格式。

## 首次使用 — 自动设置

当用户首次要求操作 COS 时，按以下流程操作：

### 步骤 1：检查当前状态

```bash
{baseDir}/scripts/setup.sh --check-only
```

如果 Node.js 和 cos-nodejs-sdk-v5 已安装、环境变量已配置，跳到「操作指南」。

### 步骤 2：如果未配置，引导用户提供凭证

告诉用户：
> 我需要你的腾讯云凭证来连接 COS 存储服务。请放心，你的密钥会受到以下保护：
>
> #### 🛡️ 凭证安全保障
> - **默认不落盘**：凭证仅存于当前终端会话内存中，关闭终端即消失
> - **可选持久化**：如需保存，凭证写入项目本地 `.env` 文件（仅当前用户可读，权限 600）
> - **支持 AES-256 加密**：持久化后可一键加密为 `.env.enc`，明文自动删除，密钥绑定本机+本用户，拷贝到其他环境无法解密
> - **自动防误提交**：`.env` / `.env.enc` 自动添加到 `.gitignore`，不会进入版本控制
> - **永远不会在对话中回显你的密钥**
>
> #### 🔒 推荐方案：STS 临时凭证（最安全，自带有效期）
> 1. **SecretId** — TmpSecretId
> 2. **SecretKey** — TmpSecretKey
> 3. **Token** — SecurityToken
> 4. **Region** — 存储桶区域（如 ap-guangzhou）
> 5. **Bucket** — 存储桶名称（格式 name-appid）
>
> #### ⚠️ 降级方案：永久密钥（必须使用子账号最小权限密钥）
> 1. **SecretId** / **SecretKey** / **Region** / **Bucket**
>
> #### 可选配置
> - **DatasetName** — 数据万象数据集名称（仅 MetaInsight 检索需要）
> - **Domain** / **ServiceDomain** / **Protocol** — 自定义域名配置

### 步骤 3：设置环境变量并运行安装

```bash
export TENCENT_COS_SECRET_ID="<SecretId>"
export TENCENT_COS_SECRET_KEY="<SecretKey>"
export TENCENT_COS_TOKEN="<Token>"  # STS 临时凭证才需要
export TENCENT_COS_REGION="<Region>"
export TENCENT_COS_BUCKET="<Bucket>"

# 默认模式：凭证仅存于当前 session，关闭终端后需重新 export
{baseDir}/scripts/setup.sh --from-env

# 持久化模式：凭证写入项目本地 .env 文件，下次自动读取
{baseDir}/scripts/setup.sh --from-env --persist
```

脚本会自动安装 `cos-nodejs-sdk-v5` 到项目本地 `node_modules/` 并验证连接。

**持久化说明**：`--persist` 会将凭证写入项目目录下的 `.env` 文件（权限 600），并自动添加到 `.gitignore`。
`cos_node.mjs` 启动时会自动读取 `.env`（环境变量优先于 `.env` 文件）。清理凭证：`rm -f .env`。

---

## 操作指南

所有操作通过单一脚本 `scripts/cos_node.mjs` 完成，输出 JSON 格式。

```
node {baseDir}/scripts/cos_node.mjs <action> [--option value ...]
```

**全局可选参数**（所有 action 均支持，用于覆盖环境变量中的默认值）：
- `--bucket <BucketName>` — 指定操作的存储桶（覆盖 `TENCENT_COS_BUCKET`）
- `--region <Region>` — 指定地域（覆盖 `TENCENT_COS_REGION`）
- `--dataset-name <Name>` — 指定数据集名称（覆盖 `TENCENT_COS_DATASET_NAME`）

> 初始配置的 Region、Bucket、DatasetName 只是默认值，每次调用都可以通过参数自由指定。

### COS 存储操作

```bash
# 上传文件
upload --file /path/to/file.jpg --key remote/path/file.jpg

# 上传字符串
put-string --content "文本内容" --key remote/file.txt --content-type "text/plain"

# 下载文件
download --key remote/path/file.jpg --output /path/to/save/file.jpg

# 列出文件
list --prefix "images/" --max-keys 100

# 获取签名 URL
sign-url --key remote/path/file.jpg --expires 3600

# 查看文件信息
head --key remote/path/file.jpg

# 删除文件
delete --key remote/path/file.jpg

# 批量删除
delete-multiple --keys '["file1.txt","file2.txt"]'

# 复制对象
copy-object --source bucket.cos.region.myqcloud.com/source.jpg --key dest.jpg
```

### COS 存储桶管理

> ⚠️ **安全限制**：本技能禁止删除存储桶和清空存储桶操作。

```bash
# 列出所有存储桶
list-buckets

# 创建存储桶
create-bucket --bucket mybucket-1250000000 --region ap-guangzhou

# 检查存储桶是否存在
head-bucket --bucket mybucket-1250000000

# 获取/设置存储桶 ACL
get-bucket-acl
put-bucket-acl --acl private

# 获取/设置跨域配置
get-bucket-cors
put-bucket-cors --origin "*" --methods "GET,POST,PUT"

# 获取/设置标签
get-bucket-tagging
put-bucket-tagging --tags '[{"Key":"env","Value":"prod"}]'

# 查询版本控制/生命周期/地域
get-bucket-versioning
get-bucket-lifecycle
get-bucket-location
```

### CI 图片基础处理

```bash
# 获取图片元信息
image-info --key images/photo.jpg

# 图片缩放
image-thumbnail --key images/photo.jpg --width 200 --height 200

# 图片裁剪
image-crop --key images/photo.jpg --width 300 --height 300 --gravity center

# 图片旋转
image-rotate --key images/photo.jpg --degree 90

# 格式转换（webp/png/jpg/avif/heif/tpg）
image-format --key images/photo.jpg --format webp

# 添加文字水印（支持中文）
watermark-font --key images/photo.jpg --text "版权所有"
```

### CI AI 图片处理

```bash
# 图片质量评估
assess-quality --key images/photo.jpg

# AI 超分辨率
ai-super-resolution --key images/photo.jpg

# AI 智能裁剪
ai-pic-matting --key images/photo.jpg --width 200 --height 200

# 二维码识别
ai-qrcode --key images/qrcode.jpg
```

### CI 内容识别

```bash
# 图片标签识别
recognize-image --key images/photo.jpg

# OCR 文字识别
ocr-general --key images/document.jpg
```

### CI 文档处理

```bash
# 文档转 PDF（自动轮询等待结果）
create-doc-to-pdf-job --key docs/report.docx

# 查询文档处理任务
describe-doc-job --job-id <jobId>

# 文档预览（转图片）
doc-preview --key docs/report.docx --page 1 --format jpg

# 获取文档在线预览 HTML 链接
doc-preview-html-url --key docs/report.docx
```

### CI 媒体处理

```bash
# 视频智能封面（自动轮询等待结果）
create-media-smart-cover-job --key videos/demo.mp4

# 查询媒体处理任务
describe-media-job --job-id <jobId>

# 视频转码
media-transcode-job --key videos/demo.mp4 --format mp4

# 视频截帧
media-snapshot --key videos/demo.mp4 --time 5 --format jpg

# 获取媒体文件信息
media-info --key videos/demo.mp4
```

### CI 内容审核

```bash
# 图片同步审核
audit-image --key images/photo.jpg

# 图片异步审核任务
audit-image-job --key images/photo.jpg

# 视频审核任务
audit-video-job --key videos/demo.mp4

# 音频审核任务
audit-audio-job --key audio/song.mp3

# 文本审核任务
audit-text-job --content "待审核的文本内容"

# 文档审核任务
audit-document-job --key docs/report.docx

# 查询审核任务结果（--type 可选 image/video/audio/text/document）
describe-audit-job --job-id <jobId> --type image
```

### CI 智能语音

```bash
# 语音识别
speech-recognition-job --key audio/meeting.mp3 --engine 16k_zh_video

# 语音合成（文字转语音）
tts-job --text "你好，欢迎使用腾讯云"

# 音频降噪
noise-reduction-job --key audio/noisy.mp3

# 人声分离
voice-separate-job --key audio/song.mp3
```

### CI 文件处理

```bash
# 文件哈希计算（md5/sha1/sha256）
file-hash --key docs/report.docx --type md5

# 文件压缩
file-compress-job --prefix "images/" --format zip

# 文件解压
file-uncompress-job --key archive.zip --prefix "output/"

# 查询文件处理任务
describe-file-job --job-id <jobId>
```

### CI MetaInsight

#### 数据集管理

```bash
# 列出所有数据集
list-datasets

# 创建数据集（模板：Official:COSBasicMeta / Official:ImageSearch / Official:FaceSearch）
create-dataset --name my-dataset --template "Official:ImageSearch" --description "图片搜索"

# 查询数据集详情
describe-dataset --name my-dataset

# 绑定存储桶到数据集（默认 Mode=1 存量索引，自动索引桶内已有文件）
create-dataset-binding --name my-dataset
create-dataset-binding --name my-dataset --uri "cos://other-bucket-1250000000"

# 仅增量索引（Mode=0，只索引绑定后新上传的文件）
create-dataset-binding --name my-dataset --mode 0

# 查询数据集的绑定关系
describe-dataset-bindings --name my-dataset
```

#### 索引管理

```bash
# 创建文件元数据索引
create-file-meta-index --name my-dataset --uri "cos://bucket/images/photo.jpg" --media-type image

# 查询文件元数据索引
describe-file-meta-index --name my-dataset --uri "cos://bucket/images/photo.jpg"

# 删除文件元数据索引
delete-file-meta-index --name my-dataset --uri "cos://bucket/images/photo.jpg"
```

#### 检索（需预建数据集）

三种检索需要**不同模板**的数据集，通过环境变量或 `--dataset` 参数分别指定：

| 检索类型 | 所需数据集模板 | 环境变量 |
|---------|---------------|----------|
| 图片检索（以图搜图/文本搜图） | `Official:ImageSearch` | `TENCENT_COS_DATASET_IMAGE_SEARCH` |
| 人脸搜索 | `Official:FaceSearch` | `TENCENT_COS_DATASET_FACE_SEARCH` |
| 元数据检索 | `Official:COSBasicMeta` | `TENCENT_COS_DATASET_META` |

> `TENCENT_COS_DATASET_NAME` 作为图片检索的兜底值。所有 action 都支持 `--dataset` 参数覆盖。

```bash
# 以图搜图（ImageSearch 数据集）
image-search-pic --uri "https://example.com/query.jpg"

# 文本搜图（ImageSearch 数据集）
image-search-text --text "蓝天白云"

# 人脸搜索（FaceSearch 数据集）
face-search --uri "cos://bucket/photo.jpg" --max-face-num 1 --limit 10 --threshold 80

# 元数据检索 — 简单查询（任意数据集）
dataset-simple-query --dataset my-dataset --sort CustomId --order desc --max-results 50
dataset-simple-query --dataset my-dataset --query '{"Operation":"eq","Field":"ContentType","Value":"image/jpeg"}'

# 多模态检索 — 文档检索（DocSearch 数据集）
hybrid-search --text "包含一颗大树的文档" --dataset docsearch --templates DocSearch --limit 10
hybrid-search --text "关键词" --dataset docsearch --filter '{"$and":[{"MediaType":{"$in":["image","document"]}},{"Size":{"$gt":123}}]}'
```

### 🚀 知识库（快捷功能）

> **重要**：这是一组面向用户口语化描述的快捷流程。用户不需要知道底层命令，只需用自然语言描述意图。

#### 用户意图识别

| 用户可能的说法 | 对应操作 |
|---------------|----------|
| "帮我创建一个知识库" "建一个知识库" "我想做个文档库" | → 执行 `create-knowledge-base` |
| "上传到知识库" "把文件放进知识库" "往知识库里加文档" | → 执行 `upload`（指向知识库对应的桶） |
| "查询知识库" "从知识库找" "搜索知识库" "知识库里有没有关于XX的内容" | → 执行 `hybrid-search`（指向知识库对应的数据集） |

#### 流程 1：创建知识库

当用户说"创建知识库"/"建一个知识库"/"我想做个文档库"时：

1. 如果用户没指定名称 → 询问用户想给知识库起什么名字
2. 执行创建：

```bash
create-knowledge-base --name <用户指定的名称>
```

3. 自动完成三步：创建存储桶 → 创建 DocSearch 数据集 → 绑定
4. **记住本次创建的知识库信息**（桶名、地域、数据集名），后续上传/查询时直接使用
5. 告诉用户：

> ✅ 知识库「<名称>」已创建！
> - 你可以把文档（PDF、Word、Excel、PPT、TXT 等）上传到这个知识库
> - 上传后系统会自动建立索引（需要几秒到几分钟）
> - 之后你可以直接说"从知识库里搜一下XXX"来查询内容

#### 流程 2：上传到知识库

当用户说"上传到知识库"/"把文件放进知识库"/"往知识库里加文档"时：

**判断使用哪个知识库：**

1. 如果本次对话中已创建/使用过知识库 → 直接使用该知识库的桶和地域
2. 如果不确定 → 执行 `list-datasets` 列出所有数据集，筛选 TemplateId 为 `Official:DocSearch` 的数据集：
   - 只有 1 个 DocSearch 数据集 → 直接使用它，通过数据集绑定关系推断对应的桶
   - 有多个 DocSearch 数据集 → 列出让用户选择
   - 没有 DocSearch 数据集 → 告诉用户"你还没有知识库，要帮你创建一个吗？"
3. 确定知识库后，执行上传：

```bash
upload --file <用户的文件路径> --key <文件名> --bucket <知识库桶名> --region <知识库地域>
```

4. 告诉用户：

> ✅ 文件已上传到知识库「<名称>」，索引建立中，稍后即可检索。

#### 流程 3：查询知识库

当用户说"查询知识库"/"从知识库找XX"/"搜索知识库"/"知识库里有没有关于XX的"/"从知识库里搜一下"时：

**判断使用哪个知识库：**

1. 如果本次对话中已创建/使用过知识库 → 直接使用该知识库的数据集
2. 如果不确定 → 执行 `list-datasets` 列出所有数据集，筛选 TemplateId 为 `Official:DocSearch` 的数据集：
   - 只有 1 个 DocSearch 数据集 → 直接使用它
   - 有多个 DocSearch 数据集 → 列出让用户选择（展示名称和文件数）
   - 没有 DocSearch 数据集 → 告诉用户"你还没有知识库，要帮你创建一个吗？"
3. 确定知识库后，执行检索：

```bash
hybrid-search --text "<用户的查询内容>" --dataset <知识库数据集名> --templates DocSearch
```

4. **结果呈现**（不要直接输出 JSON，用友好格式）：
   - 按相关度排序展示检索结果
   - 每条结果展示：**相关度分数** + **来源文件名** + **匹配内容摘要**
   - 如果没有匹配结果 → 告诉用户"知识库中没有找到相关内容，你可以上传更多文档试试"

### CI 通用请求（扩展入口）

用于调用尚未封装为独立 action 的 CI 能力：

```bash
ci-request --method POST --path "image/auditing" --body '<xml>...</xml>'
ci-request --method GET --path "jobs/<jobId>"
```

---

## 功能对照表

| 分类 | action | 说明 |
|------|--------|------|
| **存储** | `upload` | 上传文件 |
| | `put-string` | 上传字符串 |
| | `download` | 下载文件 |
| | `list` | 列出文件 |
| | `sign-url` | 获取签名链接 |
| | `delete` | 删除文件 |
| | `delete-multiple` | 批量删除 |
| | `head` | 文件元信息 |
| | `copy-object` | 复制对象 |
| **存储桶管理** | `list-buckets` | 列出所有存储桶 |
| | `create-bucket` | 创建存储桶 |
| | `head-bucket` | 检查存储桶是否存在 |
| | `get-bucket-acl` / `put-bucket-acl` | ACL 权限管理 |
| | `get-bucket-cors` / `put-bucket-cors` | 跨域配置 |
| | `get-bucket-tagging` / `put-bucket-tagging` | 标签管理 |
| | `get-bucket-versioning` | 查询版本控制 |
| | `get-bucket-lifecycle` | 查询生命周期 |
| | `get-bucket-location` | 查询存储桶地域 |
| **图片基础** | `image-info` | 图片元信息 |
| | `image-thumbnail` | 缩放 |
| | `image-crop` | 裁剪 |
| | `image-rotate` | 旋转 |
| | `image-format` | 格式转换 |
| | `watermark-font` | 文字水印 |
| **AI图片** | `assess-quality` | 质量评估 |
| | `ai-super-resolution` | 超分辨率 |
| | `ai-pic-matting` | 智能裁剪 |
| | `ai-qrcode` | 二维码识别 |
| **内容识别** | `recognize-image` | 图片标签识别 |
| | `ocr-general` | OCR 文字识别 |
| **文档处理** | `create-doc-to-pdf-job` | 文档转 PDF |
| | `describe-doc-job` | 查询文档任务 |
| | `doc-preview` | 文档预览（转图片） |
| | `doc-preview-html-url` | 文档在线预览链接 |
| **媒体处理** | `create-media-smart-cover-job` | 智能封面 |
| | `describe-media-job` | 查询媒体任务 |
| | `media-transcode-job` | 视频转码 |
| | `media-snapshot` | 视频截帧 |
| | `media-info` | 媒体文件信息 |
| **内容审核** | `audit-image` | 图片同步审核 |
| | `audit-image-job` | 图片异步审核 |
| | `audit-video-job` | 视频审核 |
| | `audit-audio-job` | 音频审核 |
| | `audit-text-job` | 文本审核 |
| | `audit-document-job` | 文档审核 |
| | `describe-audit-job` | 查询审核结果 |
| **智能语音** | `speech-recognition-job` | 语音识别 |
| | `tts-job` | 语音合成 |
| | `noise-reduction-job` | 音频降噪 |
| | `voice-separate-job` | 人声分离 |
| **文件处理** | `file-hash` | 哈希计算 |
| | `file-compress-job` | 文件压缩 |
| | `file-uncompress-job` | 文件解压 |
| | `describe-file-job` | 查询文件任务 |
| **MetaInsight 管理** | `list-datasets` | 列出数据集 |
| | `create-dataset` | 创建数据集 |
| | `describe-dataset` | 查询数据集详情 |
| | `create-dataset-binding` | 绑定存储桶 |
| | `describe-dataset-bindings` | 查询绑定关系 |
| **MetaInsight 索引** | `create-file-meta-index` | 创建文件索引 |
| | `describe-file-meta-index` | 查询文件索引 |
| | `delete-file-meta-index` | 删除文件索引 |
| **MetaInsight 检索** | `image-search-pic` | 以图搜图 |
| | `image-search-text` | 文本搜图 |
| | `face-search` | 人脸搜索 |
| | `dataset-simple-query` | 元数据检索 |
| | `hybrid-search` | 多模态检索（文档检索） |
| **通用** | `ci-request` | 调用任意 CI API |
| **🚀 知识库** | `create-knowledge-base` | "创建知识库" → 一键创建桶+数据集+绑定 |
| | `upload` → 指向知识库桶 | "上传到知识库" → 上传文档 |
| | `hybrid-search` → 指向知识库数据集 | "查询知识库" → 语义检索文档内容 |
| **🚫 禁止** | ~~deleteBucket~~ | **不允许删除/清空存储桶** |
| **🔐 凭证管理** | `encrypt-env` | 加密 .env → .env.enc 并删除明文 |
| | `decrypt-env` | 解密 .env.enc → .env 还原明文 |

## 安全注意事项

### 凭证处理

凭证存储有三种模式，安全性递增：

| 模式 | 存储位置 | 安全性 | 用法 |
|------|---------|--------|------|
| **默认模式** | shell session 环境变量 | ⭐⭐⭐ 最安全（关闭终端即消失） | `setup.sh --from-env` |
| **持久化模式** | 项目 `.env` 文件（权限 600） | ⭐⭐ 便捷但明文 | `setup.sh --from-env --persist` |
| **加密持久化** | 项目 `.env.enc`（AES-256-GCM） | ⭐⭐⭐ 推荐 | 先 `--persist`，再 `encrypt-env` |

#### 加密存储（推荐）

持久化后执行 `encrypt-env` 即可加密凭证：

```bash
# 1. 先持久化
setup.sh --from-env --persist

# 2. 加密（自动删除明文 .env，生成 .env.enc）
node scripts/cos_node.mjs encrypt-env

# 3. 之后脚本自动从 .env.enc 解密读取，所有功能正常使用
node scripts/cos_node.mjs list
```

**加密原理**：
- 算法：AES-256-GCM（认证加密，防篡改）
- 密钥派生：`SHA-256(hostname + username + 项目绝对路径)`
- **加密文件绑定当前机器和用户**，拷贝到其他机器/用户无法解密
- 如需还原明文：`node scripts/cos_node.mjs decrypt-env`
- 清理凭证：`rm -f .env .env.enc`

**其他安全要求**：
- **永远不要在对话中回显** SecretId/SecretKey
- 推荐使用 **STS 临时凭证**（自带有效期，过期自动失效）

### 最小权限与子账号密钥

> ⚠️ **永远不要使用主账号密钥**。

推荐创建专用子账号并授予最小权限策略：
- `QcloudCOSDataReadOnlyAccess` — 仅读取
- `QcloudCOSDataFullControl` — COS 数据读写
- 如需数据万象功能，额外添加 `QcloudCIFullAccess`

可进一步限制到具体存储桶：
```json
{
  "statement": [{
    "effect": "allow",
    "action": ["cos:*"],
    "resource": ["qcs::cos:<Region>::uid/<APPID>:<BucketName>/*"]
  }]
}
```

### 安装包说明

本技能通过 npm 安装 `cos-nodejs-sdk-v5`（腾讯云 COS 官方 Node.js SDK），安装到项目本地 `node_modules/`，不执行全局安装。

## 使用规范

1. **首次使用先运行** `{baseDir}/scripts/setup.sh --check-only` 检查环境
2. **所有文件路径**（`--key`）为存储桶内的相对路径，如 `images/photo.jpg`
3. **异步任务**（文档转换、视频封面）脚本会自动轮询结果，也可通过 `--job-id` 手动查询
4. **上传后主动获取链接**：上传完成后调用 `sign-url` 返回访问链接
5. **错误处理**：调用失败时先用 `setup.sh --check-only` 诊断环境问题
6. **扩展 CI 能力**：通过 `ci-request` action 可调用任意 CI API（内容审核、文件处理等）
7. **脚本源码**见 `scripts/cos_node.mjs`
8. **命令参考**见 `references/api_reference.md`
