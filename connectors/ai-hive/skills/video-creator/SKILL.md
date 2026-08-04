---
name: video-creator
display_name: 视频模型指南
display_name_en: Video Model Guide
description: "通过指导agent智能调度 Happyhorse、Seedance、Kling 等顶尖视频模型，按\"图生视频/首尾帧/电影级运镜\"自动匹配最优模型，完成产品讲解、培训录屏、宣传短片、模特走秀、多镜头分镜与会议摘要视频，支持 5-15 秒多时长与 9:16、1:1、16:9 多画幅。"
description_zh: "通过指导agent智能调度 Happyhorse、Seedance、Kling 等顶尖视频模型，按\"图生视频/首尾帧/电影级运镜\"自动匹配最优模型，完成产品讲解、培训录屏、宣传短片、模特走秀、多镜头分镜与会议摘要视频，支持 5-15 秒多时长与 9:16、1:1、16:9 多画幅。"
description_en: "Agent routes Happyhorse/Seedance/Kling for product demos, training clips, promo reels, multi-aspect."
category: media
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片与视频
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_video
    与 get_generation_task
triggers:
- 视频生成
- 产品视频
- 产品展示视频
- 产品讲解视频
- 首尾帧
- 多模态参考
- 短片
- video generation
- product video
- first last frame
---

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token


## 能力范围

AI-HIVE 视频生成 Skill 通过 AI-HIVE Connector 完成端到端视频创作。本 Skill 使用 AI-HIVE Connector 提供的以下工具：

- `get_user_info`：查询当前账户与余额；不接收参数。
- `list_models`：按 `video` 列出当前可用模型及价格快照。
- `upload_media_from_path`：上传本地图片或视频并返回 `mediaId`。
- `generate_video`：使用选定模型与可选参考素材创建视频任务。
- `get_generation_task`：使用 `generate_video` 返回的 `taskId` 查询任务状态与结果。

文本生成与图片生成请分别改用 `text-creator` 或 `image-creator`。

**覆盖场景**：产品讲解视频 / 培训录屏 / 宣传短片 / 会议摘要视频 / 首尾帧过渡 / 多模态参考 / 5–15 秒不同时长 / 1:1 / 9:16 等画幅。

**典型触发**：当用户说"生成 10 秒 9:16 产品讲解视频"、"用这两张首尾图生成过渡视频"、"按这组参考图做一段 15 秒培训片段"、"做一个 5 秒宣传开场动画"等需求时使用本 Skill。用户只是咨询能力、参数或费用时，直接回答，不创建任务。


## 调用流程

本 Skill 的标准调用顺序如下。每步有明确的输入与输出；上一步失败时不得跳到下一步。

### Step 0：连接检查
- 用户已通过 AI-HIVE Connector 完成 OAuth CLI 流程（如未连接，引导用户连接）。

### Step 1：账户与模型初查
- 调用 `get_user_info` 检查账户与余额。
- 调用 `list_models(kind="video")` 获取可用视频模型与价格快照。

### Step 2：模型推荐与选派
- 对照 `references/model-scenarios.md` 中各视频模型的擅长场景，结合用户需求的镜头类型、时长、是否有首尾帧、是否需参考素材、是否需音画等特点匹配擅长模型。
- 结合 `list_models` 返回的 `pricingSnapshot`（含 COST_FIRST / SPEED_FIRST / SUCCESS_FIRST 三档计费），权衡成片质量与成本，向用户说明推荐理由。
- 若用户未指定偏好，默认推荐效果与成本均衡的选项。
- 用户确认 `publicModelId` 与 `routingMode` 后，进入下一步。

### Step 3：（可选）上传参考素材
- 首帧、尾帧或多模态参考图/视频：调用 `upload_media_from_path` 上传，拿到 `mediaId` 备用。
- 不需要参考时直接跳到 Step 3。

### Step 4：创建任务
- 把 Step 1 返回的 `model` 对象（含 `pricingSnapshot`）作为 `generate_video.model` 入参。
- 构造 `prompt`、`durationSeconds`、`ratio`、`referenceMediaIds` 等调用 `generate_video`。
- 失败时按 `../references/error-catalog.md` 处理，不重试扣费。

### Step 5：跟踪结果
- 用 Step 3 返回的 `taskId` 调用 `get_generation_task` 轮询。
- `pending` / `processing` → 简要报告真实状态；`completed` → 拿到所有视频 URL；`failed` → 保留错误码。

### Step 6：交付
- 把成功视频的 URL、时长与画幅呈现给用户；失败候选如实报告错误码。

## 适用场景

- 用户希望生成 5–15 秒的产品讲解视频、培训录屏或宣传短片。
- 用户上传了首帧或尾帧，希望控制镜头过渡。
- 用户上传多张人物、商品或场景参考图，要求保持参考一致性。
- 用户希望快速多版本对比并跟踪任务状态。

## 非适用场景

- 目标是文本或图片；切换到 `text-creator` 或 `image-creator`。
- 本地参考素材未上传到对话或路径不可访问。
- 用户要求绕过积分、版权或安全审核；或内容明显违法、侵权、色情、暴力、仇恨、欺诈。
- 涉及真人、名人、商标或未授权素材；先向用户确认授权。
- 用户只是咨询能力、参数或费用，并未要求实际创建任务；不调用付费工具。

## 事实与合规边界

1. 只使用工具真实返回的 `taskId`、状态、错误与结果链接作为事实；不编造任务、进度或成功结果。
2. 不擅自构造或修改 `pricingSnapshot`；最终费用按 AI-HIVE 实际用量与账单计算。
3. 不静默切换用户选定的模型、时长、画幅或参考素材。
4. 不宣称对版权、商标或肖像权作法律判定；引用第三方作品或人物前先提示用户确认授权。
5. 对未成年人、裸露、暴力、仇恨与违法内容采取保守判断；无法确认合规时停止创建。
6. Token 只在 AI-HIVE Connector 凭证设置中填写，不在对话中粘贴。

## 输入检查

正式调用前逐项确认：

1. 明确视频时长、画幅、清晰度、数量、是否包含声音与文字。
2. 本地参考素材必须来自用户主动选择的文件；不接受 `localhost`、`file:` URL 或私网地址。
3. 调用 `get_user_info` 检查余额；不足时直接提示充值。
4. 调用 `list_models(kind="video")` 选择模型；时长/画幅仅使用服务端支持的枚举值。
5. 使用参考前先调用 `upload_media_from_path` 上传并保留返回的 `mediaId`。
6. 涉及真人、商标或公众人物时必须先确认用户已获得授权，否则不创建任务。

## 调用示例

> 全部示例均基于上文"输入检查"，遵循 `../references/tool-catalog.md` 与 `../references/error-catalog.md` 的口径。
> 用户表达 → AI 的多步行为 → 输出。

### 示例 1：产品展示视频

**用户表达**：生成一段 10 秒 9:16 的产品讲解视频。

**AI 行为**：
1. `get_user_info` → 余额检查。
2. `list_models(kind="video")` → 选定支持 10 秒 9:16 的模型，记录 `pricingSnapshot`。
3. `generate_video(prompt="...", durationSeconds=10, ratio="9:16")` → 拿到 `taskId`。
4. `get_generation_task(taskId)` 跟踪到 `completed`。

**输出**：
- `taskId`：xxx
- 视频 URL、时长、画幅
- 下一步：等待用户确认或调整

### 示例 2：首尾帧过渡

**用户表达**：用这两张图作为首帧和尾帧，生成一段 6 秒过渡视频。

**AI 行为**：
1. `upload_media_from_path` 上传首图 → `firstMediaId`；上传尾图 → `lastMediaId`。
2. `list_models(kind="video")` 选择支持首尾帧的模型。
3. `generate_video(prompt="...", durationSeconds=6, firstFrameMediaId="firstMediaId", lastFrameMediaId="lastMediaId")`。
4. `get_generation_task` 跟踪到 `completed`。

**输出**：
- `taskId`：xxx
- 视频 URL 与所用 `firstFrameMediaId` / `lastFrameMediaId`
- 下一步：等待用户确认

### 示例 3：超时或长任务

**用户表达**：生成一个 15 秒视频。

**AI 行为**：
1. `generate_video` 创建任务成功，连续 `get_generation_task` 收到 `processing` 但无进度数字。
2. 不自行估算完成时间；保留工具原始状态与时间戳。
3. 必要时提示用户稍后继续查询；如决定"取消重做"则需重新扣费，必须重新走 Step 3 拿新 `taskId`。

**输出**：
- 工具真实状态与时间戳
- 下一步：等待 / 取消重做

## 工具参数

### `get_user_info`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| — | — | — | 不接收参数 |

### `list_models`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `kind` | string | 可选 | `"video"` | 资源类型 |
| `cursor` | string | 可选 | 空 | 分页游标 |

### `upload_media_from_path`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `path` | string | ✅ | — | 用户授权的本地文件绝对路径 |
| `kind` | string | 可选 | 服务端推断 | 资源类型；图片或视频 |

返回 `mediaId`，必须在后续 `generate_video` 中引用。

### `generate_video`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models` 的模型引用 |
| `prompt` | string | ✅ | — | 描述主体、动作、镜头、光线、风格与声音 |
| `durationSeconds` | integer | 可选 | 服务端默认 | 单次视频时长（如 5/10/15） |
| `count` | integer | 可选 | `1` | 候选数量；增加会按比例增扣费用 |
| `size` | string | 可选 | 服务端默认 | 像素尺寸，仅使用支持的枚举值 |
| `ratio` | string | 可选 | 服务端默认 | 画幅；与服务端支持的尺寸组合 |
| `referenceMediaIds` | array | 可选 | — | 通过 `upload_media_from_path` 得到的 `mediaId` 列表 |
| `firstFrameMediaId` | string | 可选 | — | 首帧对应的 `mediaId` |
| `lastFrameMediaId` | string | 可选 | — | 尾帧对应的 `mediaId`，与 `firstFrameMediaId` 配合做首尾帧过渡 |

### `get_generation_task`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `taskId` | string | ✅ | 仅使用 `generate_video` 真实返回的 `taskId`；不得用其他 ID 查询 |

## 费用授权

- `generate_video` 调用即按服务端计费并扣费。
- 失败、被拒绝或余额不足时不重试扣费，只返回错误并询问用户下一步。
- 用户修改模型、提示词、时长、画幅或参考素材后必须重新调用，不复用旧扣费配额。

## 状态与错误处理

- `pending` / `processing`：返回工具真实状态或进度；没有进度数字时不要自行估算。
- `completed`：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。
- `failed`：保留可安全展示的 `errorCode`、`errorCategory`、`retryable`，不暴露内部凭证或堆栈。
- 超时或网络不明：拿到 `taskId` 时只查询原任务；不知道是否创建成功时不要再次创建。
- **鉴权失败 / 连接过期**：WorkBuddy → Connector 设置 → 找到 AI-HIVE → 点击"重新连接" → 完成浏览器 OAuth 流程；如仍失败，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token → 重新发起授权
- **AI-HIVE 账户无余额**：返回 INSUFFICIENT_BALANCE，引导用户在 ai-hive.iclip.cn 完成充值后再试
- **AI-HIVE 服务端错误**：按 `error-catalog.md` 处理，不自行重试扣费

- 单个视频或子任务失败：仅返回成功的视频与失败子任务的明确错误，不补写视频内容。

## 输出模板

### 成功

- `taskId`：工具真实返回的值
- 模型与参数：服务端实际采用值
- 视频：逐项列出可用 URL、缩略图、时长与画幅
- 下一步：等待用户确认、调整或保存

### 失败

- 错误码：`errorCode`（安全展示）
- 错误分类：`errorCategory`
- 原因摘要：工具给出的可读描述
- 下一步建议：充值、改连 Connector、调整提示词或切换模型

### 部分失败

- 成功视频：完整呈现 URL、时长与画幅
- 失败子任务：错误码与对应的 `prompt` 概要
- 不补写：不得为失败任务猜测视频内容
