---
name: image-creator
display_name: 图片模型指南
display_name_en: Image Model Guide
description: "通过指导agent智能调度 Nano-Banana、GPT-image、Seedream 等顶尖图片模型，按\"文字渲染/真实质感/艺术风格\"自动匹配最优模型，完成 PPT 配图、信息图、营销海报、商品主图、详情页长图、电商素材与多画幅视觉，支持 1:1、3:4、9:16 多比例输出。"
description_zh: "通过指导agent智能调度 Nano-Banana、GPT-image、Seedream 等顶尖图片模型，按\"文字渲染/真实质感/艺术风格\"自动匹配最优模型，完成 PPT 配图、信息图、营销海报、商品主图、详情页长图、电商素材与多画幅视觉，支持 1:1、3:4、9:16 多比例输出。"
description_en: "Agent routes Nano-Banana/GPT-image/Seedream for PPT art, infographics, posters, product images, multi-aspect."
category: design
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_image
    与 get_generation_task
triggers:
- 图片生成
- PPT配图
- 营销海报
- 信息图
- 活动海报
- 参考图风格迁移
- 图生图
- 海报配图
- image generation
- product poster
- reference image
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

AI-HIVE 图片生成 Skill 通过 AI-HIVE Connector 完成端到端图片创作。本 Skill 使用 AI-HIVE Connector 提供的以下工具：

- `get_user_info`：查询当前账户与余额；不接收参数。
- `list_models`：按 `image` 列出当前可用模型及价格快照。
- `upload_media_from_path`：上传本地图片（亦可用于视频）并返回 `mediaId`。
- `generate_image`：使用选定模型与可选参考图创建图片生成任务。
- `get_generation_task`：使用 `generate_image` 返回的 `taskId` 查询任务状态与结果。

文本生成或视频生成请分别改用 `text-creator` 或 `video-creator`。

**覆盖场景**：PPT 配图 / 信息图 / 营销海报 / 公众号配图 / 参考图风格迁移 / 多张对比 / 1:1、3:4、9:16 等多画幅。

**典型触发**：当用户说"给我的 PPT 配一张流程图"、"做一张活动营销海报"、"用这张参考做同风格信息图"、"生成 9:16 公众号配图"等需求时使用本 Skill。用户只是询问能力、参数或费用时，直接回答，不创建任务。


## 调用流程

本 Skill 的标准调用顺序如下。每步有明确的输入与输出；上一步失败时不得跳到下一步。

### Step 0：连接检查
- 用户已通过 AI-HIVE Connector 完成 OAuth CLI 流程（如未连接，引导用户连接）。

### Step 1：账户与模型初查
- 调用 `get_user_info` 检查账户与余额。
- 调用 `list_models(kind="image")` 获取可用图片模型与价格快照。

### Step 2：模型推荐与选派
- 对照 `references/model-scenarios.md` 中各图片模型的擅长场景，结合用户需求的画风、细节、分辨率、是否需文字渲染等特点匹配擅长模型。
- 结合 `list_models` 返回的 `pricingSnapshot`（含 COST_FIRST / SPEED_FIRST / SUCCESS_FIRST 三档计费），权衡出图质量与成本，向用户说明推荐理由。
- 若用户未指定偏好，默认推荐效果与成本均衡的选项。
- 用户确认 `publicModelId` 与 `routingMode` 后，进入下一步。

### Step 3：（可选）上传参考图
- 若需要参考图，调用 `upload_media_from_path` 上传，拿到 `mediaId` 备用。
- 不需要参考图时可直接跳到 Step 3。

### Step 4：创建任务
- 把 Step 1 返回的 `model` 对象（含 `pricingSnapshot`）作为 `generate_image.model` 入参。
- 调用 `generate_image`，失败时按 `../references/error-catalog.md` 处理，不重试扣费。

### Step 5：跟踪结果
- 用 Step 3 返回的 `taskId` 调用 `get_generation_task` 轮询。
- `pending` / `processing` → 简要报告真实状态；`completed` → 拿到所有候选 URL；`failed` → 保留错误码。

### Step 6：交付
- 把成功候选的 URL 与尺寸呈现给用户；失败候选如实报告错误码，不补写图片内容。

## 适用场景

- 用户希望生成 PPT 配图、信息图、营销海报或风格化插画。
- 用户上传了 1-4 张本地参考图，希望保持构图、配色或风格一致性。
- 用户希望复刻某张图的某个属性（光线/构图/材质），需要参考图作为输入。
- 用户希望快速多版对比，要求任务完成后从 `get_generation_task` 拿到所有候选结果。

## 非适用场景

- 目标是文本或视频；必须切换到 `text-creator` 或 `video-creator`。
- 本地图片未上传到对话，路径不可访问或不在 Skill 可达范围。
- 用户要求绕过积分、版权或安全审核；或请求涉及明显违法、侵权、色情、暴力、仇恨、欺诈等内容。
- 涉及真人、名人、商标或未授权素材；先向用户确认已获得必要授权。
- 用户只是询问能力、参数或费用，并未要求实际创建任务；直接回答问题，不调用付费工具。

## 事实与合规边界

1. 只使用工具真实返回的 `taskId`、状态、错误与结果链接作为事实；不编造任务、进度或成功结果。
2. 不擅自构造或修改 `pricingSnapshot`；最终费用按 AI-HIVE 实际用量与账单计算。
3. 不静默切换用户选定的模型、参考图或关键参数；余额不足或模型下线时返回错误。
4. 不宣称对版权、商标或肖像权作法律判定；如素材包含第三方作品或人物，先提醒用户确认授权。
5. 对未成年人、裸露、暴力、仇恨与违法内容采取保守判断；无法确认合规时停止创建。
6. Token 只在 AI-HIVE Connector 凭证设置中填写，不得在对话中粘贴。

## 输入检查

正式调用前逐项确认：

1. 明确图片用途、尺寸、画幅、数量、风格与是否包含文字。
2. 本地图片必须来自用户主动选择的文件，单次最多 4 张；超过时建议用户选择。
3. 调用 `get_user_info` 检查余额；不足时直接提示充值。
4. 调用 `list_models(kind="image")` 选择合适模型；不支持的尺寸/格式应改用其他模型。
5. 如需参考图，先调用 `upload_media_from_path` 上传并保留返回的 `mediaId`。
6. 涉及真人、商标或公众人物的素材必须先获得用户书面授权，否则不创建任务。

## 调用示例

> 全部示例均基于上文"输入检查"，遵循 `../references/tool-catalog.md` 与 `../references/error-catalog.md` 的口径。
> 用户表达 → AI 的多步行为 → 输出。

### 示例 2：营销海报（无参考图）

**用户表达**：生成 5 张 1:1 活动营销海报。

**AI 行为**：
1. `get_user_info` → 余额检查。
2. `list_models(kind="image")` → 选定支持多张的模型，记录 `pricingSnapshot`。
3. `generate_image(prompt="...", count=5, ratio="1:1", size="1024x1024")` → 拿到 `taskId`。
4. `get_generation_task(taskId)` 轮询到 `completed` → 拿到 5 张 URL。

**输出**：
- `taskId`：xxx
- 候选图：5 张 URL 与尺寸
- 下一步：等待用户确认或重做

### 示例 2：参考图风格迁移

**用户表达**：用这张图片作为构图参考，生成同风格的促销海报。

**AI 行为**：
1. `upload_media_from_path` 上传用户给出的图片 → 拿到 `mediaId_A`。
2. `list_models(kind="image")` 选择支持参考图的模型。
3. `generate_image(prompt="...", referenceMediaIds=["mediaId_A"])` 创建任务。
4. `get_generation_task` 跟踪到 `completed` → 拿到 URL。

**输出**：
- 候选图 + 使用的 `mediaId` 列表
- 下一步：等待用户调整或确认

### 示例 3：模型暂时不可用

**用户表达**：用某模型生成一张图。

**AI 行为**：
1. `list_models(kind="image")` 返回中**没有**该模型。
2. 不自动改用其他模型替代；返回 `MODEL_UNAVAILABLE`。
3. 提示用户改用列表中的可用模型。

**输出**：
- 错误码：`MODEL_UNAVAILABLE`
- 下一步：选择其他模型或稍后再试

## 工具参数

### `get_user_info`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| — | — | — | 不接收参数 |

### `list_models`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `kind` | string | 可选 | `"image"` | 资源类型；本 Skill 仅关心 `"image"` |
| `cursor` | string | 可选 | 空 | 分页游标 |

### `upload_media_from_path`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `path` | string | ✅ | — | 用户授权的本地文件绝对路径；不读取非授权路径 |
| `kind` | string | 可选 | 服务端推断 | 资源类型；图片填 `image`，视频填 `video` |

返回 `mediaId`，必须在后续 `generate_image` 中引用。

### `generate_image`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models` 的模型引用 |
| `prompt` | string | ✅ | — | 描述主体、构图、风格、光线与文字；不擅自加入用户没有要求的人物、品牌或事实 |
| `count` | integer | 可选 | `1` | 单次候选数量；增加会按比例增扣费用 |
| `size` | string | 可选 | 服务端默认 | 像素尺寸，仅使用服务端支持的枚举值 |
| `ratio` | string | 可选 | 服务端默认 | 画幅，仅使用服务端支持的枚举值 |
| `referenceMediaIds` | array | 可选 | — | 通过 `upload_media_from_path` 得到的 `mediaId` 列表 |

### `get_generation_task`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `taskId` | string | ✅ | 仅使用 `generate_image` 真实返回的 `taskId`；不得用预检结果或其他用户的任务 ID 查询 |

## 费用授权

- `generate_image` 调用即按服务端计费并扣费；不需要单独的预检步骤。
- 同一参数集失败时，不在客户端自动重试扣费；只返回错误并询问用户下一步。
- 余额不足时返回 `INSUFFICIENT_BALANCE`，提示用户在 AI-HIVE 完成充值后再试。
- 用户修改模型、提示词、尺寸、画幅或参考图后必须重新调用，不复用旧扣费配额。

## 状态与错误处理

- `pending` / `processing`：返回工具真实状态或进度；没有进度数字时不要自行估算。
- `completed`：返回所有可用图片链接、缩略图与工具明确给出的部分失败信息。
- `failed`：保留可安全展示的 `errorCode`、`errorCategory`、`retryable`，不暴露内部凭证或堆栈。
- 超时或网络不明：拿到 `taskId` 时只查询原任务；不知道是否创建成功时不要再次创建。
- **鉴权失败 / 连接过期**：WorkBuddy → Connector 设置 → 找到 AI-HIVE → 点击"重新连接" → 完成浏览器 OAuth 流程；如仍失败，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token → 重新发起授权
- **AI-HIVE 账户无余额**：返回 INSUFFICIENT_BALANCE，引导用户在 ai-hive.iclip.cn 完成充值后再试
- **AI-HIVE 服务端错误**：按 `error-catalog.md` 处理，不自行重试扣费

- 流式中断或单张候选失败：仅返回成功的候选与失败子任务的明确错误，不补写图片内容。

## 输出模板

### 成功

- `taskId`：工具真实返回的值
- 模型与参数：服务端实际采用值
- 候选图：逐项列出可用 URL、缩略图与尺寸
- 下一步：等待用户确认、调整或保存

### 失败

- 错误码：`errorCode`（安全展示）
- 错误分类：`errorCategory`
- 原因摘要：工具给出的可读描述
- 下一步建议：充值、改连 Connector、调整提示词或切换模型

### 部分失败

- 成功候选：完整呈现 URL 与尺寸
- 失败子任务：错误码与对应的 `prompt` 概要
- 不补写：不得为失败候选猜测内容
