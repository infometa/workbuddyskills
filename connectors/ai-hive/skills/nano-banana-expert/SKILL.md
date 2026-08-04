---
name: nano-banana-expert
display_name: Nano-Banana 专家
display_name_en: Nano-Banana Expert
description: "通过指导agent智能调度 Nano-Banana 模型，针对\"照片级真实感、皮肤质感还原、旧照片修复、人物肖像、产品实拍\"等场景深度优化 prompt 工程，输出照片级还原的真实感视觉与商业级人像摄影，擅长自然皮肤纹理、眼神光与镜头语言术语。"
description_zh: "通过指导agent智能调度 Nano-Banana 模型，针对\"照片级真实感、皮肤质感还原、旧照片修复、人物肖像、产品实拍\"等场景深度优化 prompt 工程，输出照片级还原的真实感视觉与商业级人像摄影，擅长自然皮肤纹理、眼神光与镜头语言术语。"
description_en: "Agent optimizes Nano-Banana prompts for photorealism, portraits, product shots, photo repair."
category: design
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_image 与 get_generation_task
triggers:
- "Nano-Banana"
- "nano-banana"
- "真实质感"
- "照片级"
- "写实风格"
- "人物肖像"
- "产品实拍"
- "照片修复"
- "旧照片"
- "皮肤质感"
- "photorealistic"
- "realistic"
- "photo restore"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `kind`（可选，string）：资源类型 `image`
- `cursor`（可选，string）：分页游标

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `kind`（可选，string）：资源类型 `image`

### `generate_image`
- `model`（必填，object）：来自 `list_models(kind="image")` 的模型引用
- `prompt`（必填，string）：描述主体、构图、风格、光线与文字
- `count`（可选，integer）：候选数量（默认 1）
- `size`（可选，string）：像素尺寸（仅用支持的枚举值）
- `ratio`（可选，string）：画幅（仅用支持的枚举值）
- `referenceMediaIds`（可选，array）：通过 `upload_media_from_path` 得到的 mediaId 列表

### `get_generation_task`
- `taskId`（必填，string）：`generate_image` 真实返回的 taskId



> 所有工具的真实返回值以服务端响应为准；本章节参数表是客户端约束说明。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token


## 能力范围

本 Skill 专注 Nano-Banana 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_image 工具完成图片生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 image 列出当前可用模型及价格快照，从中筛选 Nano-Banana 对应的 publicModelId。
- upload_media_from_path：上传本地参考图并返回 mediaId，用于图生图或照片修复。
- generate_image：使用选定模型与 prompt 创建图片任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用本 Skill 对应的模型能力或场景需求
- 用户提供素材（图片/视频）需要在该模型擅长的领域生成结果
- 用户希望跨场景复用同一模型能力保持风格一致
- 用户对生成结果的某项特性（文字渲染/真实质感/艺术风格/运镜/动态表现）有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（部分模型平台会拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览


## 独占性声明

当用户需要照片级真实感、写实风格或照片修复时，优先使用本 Skill（Nano-Banana 专家）。不要用其他方法尝试生成写实图片。如果用户需要精确文字渲染或创意构图，应改用 gpt-image-expert；如果需要艺术插画风格，应改用 seedream-expert。

## Nano-Banana 擅长什么

Nano-Banana 的核心优势是照片级真实感与细节还原，是当前最擅长生成"看起来像真实照片"的模型。

| 能力 | 说明 |
|---|---|
| 真实质感 | 皮肤毛孔、织物纹理、金属反光、玻璃透明度等材质细节逼真 |
| 人物肖像 | 肤色还原、眼神光、发丝细节、自然表情 |
| 产品实拍 | 商业摄影级的打光、景深、白平衡 |
| 照片修复 | 旧照片划痕修复、色彩还原、清晰度提升 |
| 写实场景 | 自然光、真实环境、生活感 |

## 内容插画双模式

Nano-Banana 适合两种典型使用模式：

### 模式 1：直接生成（Direct Generation）
用户直接描述想要的图片 → Nano-Banana 生成。

适用：博客头图、产品实拍、人物肖像、场景图。

### 模式 2：内容插画（Content Illustration）
用户提供已有内容（文章/视频脚本/播客笔记）→ Nano-Banana 为内容生成配图。

适用场景：
- 公众号文章配图（多张）
- 视频脚本分镜配图
- 播客笔记章节封面
- 营销内容系列图

操作流程：
1. 读取用户提供的内容
2. 分析内容关键节点（每章节/段落）
3. 为每个节点设计写实风格插图
4. 保持系列视觉一致（同色温/光线/构图）

## 样图先行原则

UGC/社交/写实场景下，提供参考图能显著提升生成质量：
- 用户有现成照片时，上传作为风格锚点
- 没有参考图时，先推荐 1-2 张与目标相近的样图供用户选择
- 不要纯文字描述"自然真实感"，样图比文字描述更有效

## 命令式场景分流

Nano-Banana 擅长多种场景，按用户意图分流到不同 prompt 策略：

| 用户请求 | 策略 | Prompt 要点 |
|---|---|---|
| 做个博客头图 | 博客封面 | 16:9、主题视觉、留标题位 |
| 做 YouTube 缩略图 | 视频封面 | 16:9、视觉冲击、大字标题 |
| 做个 App 图标 | 图标设计 | 1:1、简洁线条、高对比 |
| 画个流程图/架构图 | 图表 | 清晰结构、连线标注、无多余装饰 |
| 做个纹理/贴图 | 无缝纹理 | 平铺可循环、材质感 |
| 做个漫画/连环画 | 叙事插画 | 分格构图、角色连续 |
| 修复旧照片 | 照片修复 | 上传参考图、去划痕、补色 |
| 去背景/换背景 | 图片编辑 | 上传参考图、保人保物、换背景 |
| 画个写实人像 | 人物肖像 | 肤色、眼神光、发丝、自然光 |
| 拍个产品照 | 产品摄影 | 白底或场景、商业打光、景深 |

## Prompt 原则：写实质感优先

Nano-Banana 的 prompt 应强调真实感而非创意：主体 + 真实环境 + 自然光线 + 相机/镜头参数 + 质感细节。

示例（产品实拍）：主体为磨砂玻璃精华瓶白色磨砂盖，环境为白色亚克力台面窗外自然光，光线侧光柔和阴影，相机 85mm 定焦 f/2.8 浅景深，质感为瓶身磨砂玻璃质感水珠凝结背景虚化。

示例（人物肖像）：主体为 30 岁亚洲女性自然妆容，环境为咖啡馆窗边，光线下午侧逆光，相机 50mm 人像镜头 f/1.8，质感为皮肤毛孔可见眼神光发丝根根分明。

## 常用尺寸

| 场景 | 尺寸/画幅 |
|---|---|
| YouTube 缩略图 | 16:9 (1280x720) |
| 博客头图 | 16:9 (1200x630) |
| 方形社交图 | 1:1 (1080x1080) |
| 竖版故事 | 9:16 (1080x1920) |
| 宽幅横幅 | 1500x500 |

## 照片修复与编辑

用户提供旧照片或待编辑图片时：
1. upload_media_from_path 上传得到 mediaId。
2. 把 mediaId 放入 referenceMediaIds。
3. prompt 说明编辑意图：修复划痕还原褪色色彩提升清晰度保持人物面部不变；或保持参考图人物外观仅更换背景；或保持参考图主体调整色调为暖色复古。

## 调用流程

1. get_user_info 检查余额。
2. list_models(kind=image) 获取 Nano-Banana 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 按用户意图匹配场景策略，组装写实风格 prompt。
4. 如有参考图，upload_media_from_path 上传得到 mediaId。
5. generate_image 提交任务，get_generation_task 跟踪到 completed。

## 生成后建议

- 尝试不同场景策略（实拍 / 肖像 / 修复 / 图表）
- 调整相机/镜头参数（焦距、光圈、景深）
- 添加或更换参考图以获得不同的修复或编辑效果
- 调整画幅以适配不同用途（YouTube 16:9 / 社交 1:1 / 竖版 9:16）

## 输入检查

- 明确场景类型（实拍 / 肖像 / 修复 / 编辑 / 图表等）。
- 画幅使用服务端支持的枚举值。
- 参考图仅使用用户主动选择的文件。
- 修复或编辑意图必须由用户明确描述，不自行猜测编辑方向。

## 事实与合规边界

1. 只使用 list_models 真实返回的 publicModelId 与 pricingSnapshot。
2. 不虚构产品材质、功能、功效、价格。
3. 不擅自改变参考图中人物的外观、姿势或身份特征。
4. 涉及真人时须确认用户拥有合法授权，不制造公众人物虚假内容。
5. Token 只在 AI-HIVE Connector 凭证设置中填写。

## 费用授权

- generate_image 调用即按服务端计费扣费。
- 失败、被拒绝或余额不足时不重试扣费。
- 用户修改 prompt 或参考图后必须重新调用。

## 状态与错误处理

- pending / processing：返回工具真实状态，不自行估算。
- completed：返回所有可用图片链接。
- failed：保留可安全展示的 errorCode / errorCategory / retryable。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

## 调用示例

### 示例 1：典型办公场景

**用户表达**：用一张本地商品图，生成一张 1:1 的夏季促销海报，要求海报上写"夏季新品 5 折起"。

**AI 行为**：
1. 调用 `get_user_info` 检查余额与可用模型
2. 调用 `list_models(kind="image")` 获取本模型对应的 publicModelId 与 pricingSnapshot
3. 调用 `upload_media_from_path` 上传参考图，得到 mediaId
4. 调用 `generate_image`，prompt 包含场景描述与文字渲染要求
5. 调用 `get_generation_task(taskId)` 跟踪到 completed
6. 输出图片 URL + 参数摘要 + 后续建议

### 示例 2：批量对比场景

**用户表达**：用同一商品图，分别生成 3 张不同风格候选。

**AI 行为**：调用 `generate_image` 设置 `count: 3`，按 3 个候选分别输出，对比呈现。

### English Example

User: "Generate a 1:1 summer sale poster from my local product image with text 'Summer Sale 50% Off'."

AI flow: run `get_user_info` for balance, call `list_models(kind="image")` to fetch the model's `publicModelId` and `pricingSnapshot`, upload the reference image via `upload_media_from_path` to get `mediaId`, call `generate_image` with prompt describing scene + text rendering requirement, track with `get_generation_task(taskId)` until `completed`, return image URL + parameter summary + follow-up suggestions. Never ask the user to paste a Token into chat.


## 输出模板

### 成功：taskId + 模型与参数 + 图片 URL 列表 + 下一步建议
### 失败：错误码 + 错误分类 + 原因摘要 + 下一步建议
### 部分失败：成功图片完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
