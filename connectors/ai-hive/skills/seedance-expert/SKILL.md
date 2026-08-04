---
name: seedance-expert
display_name: Seedance 专家
display_name_en: Seedance Expert
description: "通过指导agent智能调度 Seedance 模型，针对\"电影级运镜、首尾帧过渡、多模态角色引用、时序分镜、角色一致性\"等场景深度优化 prompt 工程，输出具备角色一致性的高质量电影级视频，支持 4-15 秒时长、原生音频生成与多模态参考。"
description_zh: "通过指导agent智能调度 Seedance 模型，针对\"电影级运镜、首尾帧过渡、多模态角色引用、时序分镜、角色一致性\"等场景深度优化 prompt 工程，输出具备角色一致性的高质量电影级视频，支持 4-15 秒时长、原生音频生成与多模态参考。"
description_en: "Agent optimizes Seedance prompts for cinematic camera work, first/last-frame transitions, role consistency."
category: media
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片与视频
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_video 与 get_generation_task
triggers:
- "Seedance"
- "seedance"
- "首尾帧"
- "运镜"
- "电影级"
- "分镜"
- "角色一致性"
- "多模态参考"
- "图生视频"
- "过渡视频"
- "链式续写"
- "cinematic"
- "camera movement"
- "first last frame"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `kind`（可选，string）：资源类型 `video`
- `cursor`（可选，string）：分页游标

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `kind`（可选，string）：资源类型 `video`

### `generate_video`
- `model`（必填，object）：来自 `list_models(kind="video")` 的模型引用
- `prompt`（必填，string）：描述主体、动作、镜头、光线、风格与声音
- `durationSeconds`（可选，integer）：时长 5/10/15
- `count`（可选，integer）：候选数量（默认 1）
- `size`（可选，string）：像素尺寸（仅用支持的枚举值）
- `ratio`（可选，string）：画幅（仅用支持的枚举值）
- `referenceMediaIds`（可选，array）：参考媒体 mediaId 列表
- `firstFrameMediaId`（可选，string）：首帧 mediaId
- `lastFrameMediaId`（可选，string）：尾帧 mediaId

### `get_generation_task`
- `taskId`（必填，string）：`generate_video` 真实返回的 taskId



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

本 Skill 专注 Seedance 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 Seedance 对应的 publicModelId。
- upload_media_from_path：上传本地图片/视频并返回 mediaId，用于首尾帧、参考图与角色锚点。
- generate_video：使用选定模型与 prompt 创建视频任务。
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


## 触发原则

积极触发 -- 有疑虑时就用本 Skill。只要有视频生成意图（即使未明确提到 Seedance），都应考虑使用。信号包括：
- 显式：用户提到 Seedance、首尾帧、运镜、电影级
- 隐含：任何 AI 视频任务、跨镜头角色一致性、多镜头序列、图生视频、视频续写
- 概念：电影级 AI 制作、原生音频生成、多模态参考

## 输入文件格式与大小限制

| 类型 | 限制 | 格式 | 单文件大小 |
|---|---|---|---|
| 图片 | ≤ 9 张 | jpeg / png / webp / bmp / tiff / gif | 各 30MB |
| 视频 | ≤ 3 个 | mp4 / mov | 各 50MB，总时长 2-15s |
| 音频 | ≤ 3 个 | mp3 / wav | 各 15MB，总时长 ≤ 15s |
| 文本 | 自然语言 prompt | — | — |
| 总文件数 | ≤ 12 个 | — | — |

> AI-HIVE MCP 上传工具（upload_media_from_path）实际限制以服务端为准；超出限制时上传失败并返回错误。

## 合规与平台限制

- **真实人脸限制**：上传的图片或视频中不得含真实人脸。Seedance 平台会拦截此类上传，不予生成。
- 合规场景：卡通形象、抽象角色、非特定人物的虚拟人物、产品图、风景、动物、动漫角色等。
- 不合规场景：真人照片、需要保留真实人物外貌的图生图、公众人物肖像。

## 场景模式分类

按用户需求场景选择不同的 prompt 模式与侧重：

### 电商广告（E-commerce Ads）
- 目标：突出产品卖点，促成点击/转化
- 重点：产品特写、动态展示、品牌色、CTA 视觉
- Prompt 强化：突出材质细节、使用场景、品牌元素
- 时长建议：5-8 秒紧凑节奏

### 短剧（Short Drama）
- 目标：情节推进、情绪表达
- 重点：人物动作、表情变化、镜头叙事
- Prompt 强化：景别+运镜前置、对话驱动、情绪标注
- 时长建议：10-15 秒分段叙事
- 必备约束：禁止字幕、禁止 BGM（避免剧透）/ 或 BGM 标注

### 教育内容（Educational）
- 目标：知识清晰传达
- 重点：演示过程、图表动画、步骤分解
- Prompt 强化：分步骤、特写关键节点、配音解说
- 时长建议：根据内容长度灵活

## 模型规格

| 维度 | 规格 |
|---|---|
| 输入模态 | 文本 + 最多 9 张图 + 最多 3 个视频 + 最多 3 个音频（共最多 12 个文件） |
| 输出 | MP4，480p 或 720p |
| 时长 | 4-15 秒 |
| 原生音频 | 自动生成 SFX、音乐、lip-sync 对话 |
| 画幅 | 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 / auto |
| 端点 | text-to-video / image-to-video（支持首帧+尾帧）/ reference-to-video |

## Seedance 擅长什么

Seedance 的核心优势是电影级运镜与多模态角色引用，是把多张参考图当作角色而非单纯视觉锚点的模型。

| 能力 | 说明 |
|---|---|
| 首尾帧过渡 | 提供 firstFrameMediaId + lastFrameMediaId，生成两帧之间的平滑过渡视频 |
| 运镜控制 | 推、拉、摇、移、跟、升、降--单一镜头内一种运镜 |
| 多图角色引用 | 把参考图标记为角色，在 prompt 中锚定身份 |
| 多模态输入 | 文本 + 最多 9 张图 + 视频参考，融合多源素材 |
| 时序分镜 | 大于 8 秒视频按时间片拆分 |
| 角色一致性 | 4 图法（正面 + 纯侧脸 + 3/4 动态 + 换背景正面）跨镜头保人 |
| 原生音频 | 自动生成 SFX、音乐、lip-sync 对话 |

## 角色引用系统（核心语法）

Seedance 把参考图当角色而非视觉锚点。上传多张参考图后，按上传顺序编号（图1、图2...），在 prompt 中声明每张图的用途：

- 图1 作为首帧 / 图2 作为尾帧
- 图1 的角色作为主体（身份锚定）
- 场景参考图3
- 参考视频1 的运镜
- 穿着图2 中的服装
- BGM 参考音频1

## Prompt 公式

主体/角色设定 + 场景环境 + 动作/运动 + 运镜 + 时序分段 + 转场/特效 + 音效/声音 + 风格/氛围

大于 8 秒视频按时间片分段：0-3秒女孩推门走进咖啡馆镜头向前推；3-6秒她坐下点单镜头平移到吧台；6-10秒咖啡上桌特写镜头固定。

## 角色一致性 4 图法

需要跨镜头保持真实人物或宠物一致性时，提供 4 张互补角度的图：

1. 正面英雄镜头--看镜头，全脸，均匀光线
2. 纯侧脸特写--展示脸型与特征（眼镜框侧面、耳形等）
3. 3/4 动态--过肩或运动中，增加变化
4. 换背景正面--与图1不同背景/姿势，防止背景渗透

### 多角色技巧（重要）

当同时出现人物+宠物（或两个角色）时，不要 4+4 平均分配参考图。正确做法：
- 主角色 3 张 + 次角色 2 张（非 4+4）
- 平均分配会导致 identity bleed（脸混淆），模型无法区分两张脸
- 不对称分配给主角色足够锚定，同时保留次角色的品种/毛色/特征

## 链式 clip 续写（长视频）

Seedance 单次最长 15 秒。需要更长叙事时，用链式续写：

1. 生成 Clip N，拿到视频
2. 提取 Clip N 的最后一帧（截图）
3. 把最后一帧作为 Clip N+1 的 firstFrameMediaId
4. 重复，直到叙事完成

注意：image-to-video 模式不支持额外参考图。角色身份仅锚定在首帧中。续写+一致性场景可考虑：把每个 clip 控制在 10 秒内，或接受一定的角色漂移。

## 音频与对话写法

原生音频默认启用。在 prompt 中用以下方式描述：

- 对话用双引号做 lip-sync：她低声说"你在吗？"
- SFX：撞击时低频轰鸣、水下气泡声
- 音乐：命名风格（John Williams 式管弦、145 BPM synthwave），不写"史诗音乐"这种模糊词

## 运镜规则

- 单一时间片只允许一种运镜，禁止同时推拉摇移。
- 常用运镜：向前推 / 后拉 / 左右平移 / 上升 / 下降 / 跟随 / 固定。

## 模式选择

| 用户意图 | 参数 | 说明 |
|---|---|---|
| 纯文生视频 | 无 referenceMediaIds / 无首尾帧 | 从 prompt 生成 |
| 首帧续写 | firstFrameMediaId | 从指定帧开始，自然延续 |
| 首尾帧过渡 | firstFrameMediaId + lastFrameMediaId | 生成两帧之间过渡 |
| 多图角色融合 | referenceMediaIds（多图）| 用图N 引用角色 |
| 链式续写 | 上一个 clip 最后一帧作为 firstFrameMediaId | 长视频分段 |

## 调用流程

1. get_user_info 检查余额。
2. list_models(kind=video) 获取 Seedance 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 分析用户需求：纯文生 / 图生 / 首尾帧 / 多图角色 / 链式续写。
4. 如需参考图，upload_media_from_path 逐张上传得到 mediaId。
5. 组装 prompt：角色设定、场景、动作、运镜、时序、音频、风格。
6. generate_video 提交任务，get_generation_task 跟踪到 completed。

## 输入检查

- 明确生成模式（文生 / 图生 / 首尾帧 / 多图角色 / 链式续写）。
- 参考图仅使用用户主动选择的文件。
- 时长仅使用服务端支持的枚举值（4-15 秒）。
- 画幅仅使用服务端支持的枚举值。
- 多图角色引用时，必须用图N + 角色名明确每张图的用途。
- 多角色场景用 3+2 不对称分配，不用 4+4 平均分配。

## 生成后建议

- 尝试不同模态（文生不理想可改图生或首尾帧）。
- 调整运镜方式（推/拉/摇/移/跟/升/降/固定）。
- 增减参考图数量。
- 调整时长（短视频用连贯叙事，长视频用时间戳分镜）。
- 链式续写分段时，注意角色漂移风险。

## 事实与合规边界

1. 只使用 list_models 真实返回的 publicModelId 与 pricingSnapshot。
2. 不虚构商品信息、不制造虚假代言。
3. 不擅自改变参考图中人物的外观或身份特征。
4. 涉及真人时须确认用户拥有合法授权，不制造公众人物虚假内容。
5. 对未成年人、裸露、暴力内容采取保守判断。
6. Token 只在 AI-HIVE Connector 凭证设置中填写。

## 费用授权

- generate_video 调用即按服务端计费扣费。
- 失败、被拒绝或余额不足时不重试扣费。
- 用户修改模型、prompt、时长、画幅或参考素材后必须重新调用。

## 状态与错误处理

- pending / processing：返回工具真实状态或进度，无进度数字时不自行估算。
- completed：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。注意 COMPLETED 状态不保证有视频 URL，必须检查返回体。
- failed：保留可安全展示的 errorCode / errorCategory / retryable。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
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

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：错误码 + 错误分类 + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
