---
name: h3-expert
display_name: H3 (MiniMax) 专家
display_name_en: H3 (MiniMax) Expert
description: "通过指导agent智能调度 MiniMax H3 模型，针对\"全模态上下文理解、原生立体声音频、首尾帧/参考生视频、视频编辑与动作迁移、产品设计/排版/界面动画\"等场景深度优化 prompt 工程，输出最长 15 秒、最高 2K、带原生立体声的高质量视频。"
description_zh: "通过指导agent智能调度 MiniMax H3 模型，针对\"全模态上下文理解、原生立体声音频、首尾帧/参考生视频、视频编辑与动作迁移、产品设计/排版/界面动画\"等场景深度优化 prompt 工程，输出最长 15 秒、最高 2K、带原生立体声的高质量视频。"
description_en: "Agent optimizes MiniMax H3 prompts for multimodal context, native stereo audio, first/last frame, reference-to-video, video editing, motion transfer; up to 15s / 2K."
category: media
version: 1.1.4
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片、视频与音频
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_video 与 get_generation_task
triggers:
- "H3"
- "MiniMax H3"
- "minimax h3"
- "海螺 H3"
- "H3 视频"
- "全模态视频"
- "立体声视频"
- "动作迁移"
- "参考生视频"
- "minimax video"
- "h3 video"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `modelType`（可选，string）：资源类型枚举 `TEXT` / `IMAGE` / `VIDEO`（本 Skill 用 `VIDEO`）

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `filename`（可选，string）：覆盖上传文件名
- `contentType`（可选，string）：覆盖 MIME 类型；不确定时省略并由客户端识别
- MP3/WAV 音频单文件最大 15 MiB；上传成功后返回 `mediaType=AUDIO`

### `generate_video`
- `publicModelId`（必填，string）：来自 `list_models(modelType="VIDEO")` 的当前模型 ID
- `routingMode`（必填，string）：选中模型实际返回的 `COST_FIRST` / `SPEED_FIRST` / `SUCCESS_FIRST`
- `prompt`（必填，string）：描述主体、动作、镜头、光线、风格与声音
- `imageMediaIds`（可选，array）：参考图片 mediaId 列表
- `videoMediaIds`（可选，array）：参考或待编辑视频 mediaId 列表
- `audioMediaIds`（可选，array）：外部参考音频 mediaId 列表；默认空数组，仅用于当前模型配置明确支持参考音频的组合
- `firstFrameMediaId` / `lastFrameMediaId`（可选，string）：首尾帧 mediaId
- `params`（可选，object）：时长、画幅、分辨率、声音等模型专属参数；键、类型和值以当前模型配置为准
- `pricingSnapshot`（必填，object）：选中模型与路由返回的价格快照，原样传入

### `get_generation_task`
- `taskId`（必填，string）：`generate_video` 真实返回的 taskId


> 所有工具的真实返回值以服务端响应为准；本章节参数表是客户端约束说明。**H3 在 AI-HIVE 中的精确 `publicModelId` 与支持的枚举（时长/分辨率/画幅/参考上限）以 `list_models` 实时返回为准**，不要在客户端臆造。公开资料中的 H3 能力（见下文）仅作场景速查与 prompt 指导，不替代服务端返回值。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token

## 模型事实（交叉验证，2026-08）

> 以下为公开资料交叉验证结论（MiniMax 官方开源报道 2026-08-03、Artificial Analysis 榜单、多家媒体与文档站）。**经 AI-HIVE 实际调用时，一切以 `list_models` 返回为准。**

- **身份**：MiniMax H3，2026-08-03 开源的通用型全模态生成系统（H3-Context-IR / H3-Base / H3-Regenerate-2K 三模块）。
- **模态**：统一理解文本 + 图像 + 视频 + 音频组成的多模态上下文。
- **输出**：最长约 **15 秒**、最高 **2K** 分辨率、带**原生立体声音频**（stereo）的视频。
- **工作模式（公开托管 API）**：文生视频(T2V)、图生视频(I2V，首帧)、首尾帧(FLF2V)、参考生视频(Ref2V)；另有 H3 Turbo 加速变体。
- **模型级参考素材（公开 fal 端点值，AI-HIVE 以 list_models 为准）**：最多约 9 张图 / 3 段视频 / 3 段音频；外部音频上传后按顺序放入 `audioMediaIds`。
- **编辑能力**：视频编辑、文字/品牌元素生成、动作迁移(V2V)、参考视频迁移。
- **榜单**：Artificial Analysis 有声视频编辑榜单 Elo 1130，位列第一（领先 Gemini Omni Flash、HappyHorse-1.0、Wan 2.7）。
- **开放权重**：模型已开源（许可对美/欧/英/韩等地区设限）；经 AI-HIVE 为托管 API 调用，无需本地部署。
- **相对边界**：综合上限、长视频连续性与复杂控制粒度目前弱于 Seedance 2.5；参考素材规模与编辑精细度不及 Seedance 2.5。适合把「理解素材」与「生成镜头」合到同一条链路的产品设计、排版、界面动画、动作迁移、定向编辑类任务。

## OpenAPI 交叉验证：模型 ID（SDK models-reference.md，2026-08）

> 以下 `publicModelId` 来自 AI-HIVE OpenAPI `models-reference.md`（经 SDK 交叉验证）。
> 在 AI-HIVE Connector 中**运行时一切以 `list_models` 实际返回为准**；下表用于预校验，不臆造未返回字段。

| 任务类型 | publicModelId |
|---|---|
| 文生视频 T2V | `public_model_minimax_h3_t2v` |
| 图生视频 I2V | `public_model_minimax_h3_i2v` |
| 参考生视频 R2V | `public_model_minimax_h3_r2v` |

> H3 的公开托管 API 另有 H3 Turbo 加速变体；经 AI-HIVE 实际可用的变体以 `list_models` 为准。

## 能力范围

本 Skill 专注 MiniMax H3 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 H3（MiniMax）对应的 publicModelId。
- upload_media_from_path：上传本地图片/视频或 MP3/WAV 音频并返回 mediaId，用于首帧与全模态参考；音频单文件最大 15 MiB。
- generate_video：使用选定模型与 prompt 创建视频任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用 H3 / MiniMax H3，或需要全模态上下文理解、原生立体声、首尾帧、参考生视频、视频编辑、动作迁移
- 产品设计演示、排版/界面动画、品牌内容、参考视频迁移、动作/运镜迁移类任务
- 用户希望把图片/视频/音频素材与生成镜头合到同一条链路

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（平台可能拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览
- 需要 30 秒级长叙事或 50 规模参考集时，建议改用 Seedance 2.5（见 model-scenarios.md 选派逻辑）

## 触发原则

积极触发 —— 有疑虑时就用本 Skill。信号包括：
- 显式：用户提到 H3、MiniMax H3、海螺 H3、全模态视频、立体声视频、动作迁移
- 隐含：全模态参考视频生成、产品设计/排版/界面动画视频、带原生立体声的视频、参考视频迁移
- 概念：理解素材并生成镜头、V2V 动作迁移、定向视频编辑

## H3 擅长什么

| 能力 | 说明 |
|---|---|
| 全模态上下文 | 同一上下文内融合文本 + 图像 + 视频 + 音频，生成贴合素材的视频 |
| 原生立体声 | 输出带原生立体声音频，音画同步，无需后期配音 |
| 首尾帧 | 首帧(I2V) / 首尾帧(FLF2V) 控制开头与结尾画面 |
| 参考生视频 | Ref2V：用参考图/视频锚定主体、风格、动作 |
| 视频编辑 | 定向编辑画面、生成文字/品牌元素、参考视频迁移 |
| 动作迁移 | V2V 将参考视频的动作/运镜迁移到生成结果 |

## 三种常用模式

| 用户意图 | 模式 | 参数 | 说明 |
|---|---|---|---|
| 从零构建场景 | T2V | 无图片/视频素材、无首尾帧 | 从 prompt 生成 |
| 让静态画面动起来 | I2V | firstFrameMediaId | 从指定图片开始，自然延续 |
| 首尾帧过渡 | FLF2V | firstFrameMediaId + lastFrameMediaId | 生成两帧之间过渡 |
| 编排多角色/参考 | Ref2V | 图片用 `imageMediaIds`，视频用 `videoMediaIds`，音频用 `audioMediaIds` | 用素材锚定主体、风格、动作与声音参考 |
| 编辑/迁移 | 编辑/Ref2V | `videoMediaIds`（源视频）+ 编辑 prompt | 定向修改、动作迁移、文字生成 |

## Prompt 公式（通用多模态结构）

H3 暂无像 Seedance 2.5 那样公开的详细官方 prompt 模板；以下基于其公开能力与通用多模态视频实践：

**1. 素材指代**：明确每个图、视频和音频的编号（各自按上传顺序）与用途（谁是形象、风格、动作、场景、节拍或音色）。音频按音频1、音频2……映射到 `audioMediaIds`；只有当前模型配置明确支持参考音频和当前组合时才提交。

**2. 一句话概述**：主体 + 地点 + 事件 + 题材/风格 + 特殊运镜。

**3. 具体情节描述**：用时间戳或「镜头 N」切分，逐段描述画面内容、运镜、动作、台词、音效，尽量用正向描述。

**4. 结尾**：补充贯穿始终的画面细节，如机位/运镜、环境/场景、声音、氛围。

**参考类（多素材映射）**：多主体逐一列清映射关系，避免混淆（如「图1是主角，图2是场景，视频1提供运镜」）。分工具体到「参考什么」，部分参考写明「参考哪一部分」。

**编辑/迁移类**：明确修改范围与内容，可配合时间戳做部分编辑（如「仅编辑视频1中男人的台词改为…」「将视频1的动作迁移到图1角色」）。

**负向控制**：可用「不要字幕」「无 bgm，只生成环境音」等约束，以服务端实际支持为准。

### 外部参考音频工作流

1. 只读取用户主动选择的 MP3/WAV，单文件最大 15 MiB，并逐个调用 `upload_media_from_path`。
2. 按上传顺序建立音频1、音频2……与 `audioMediaIds` 的一一映射，Prompt 中的引用不得重排。
3. H3 的参考音频数量、时长和组合限制以当前模型配置为准；同时核对图片、视频、首尾帧字段是否可与音频组合。
4. 模型不兼容时不发送 `audioMediaIds`；Prompt 的声音描述与 `params` 原生声音开关仍按当前配置独立使用。

## 原声音频写法

原生立体声音频默认启用（公开资料未提及开关，以服务端为准）。在 prompt 中用以下方式描述：

- 对话用双引号做口型同步：她低声说"你在吗？"
- SFX：撞击时低频轰鸣、水下气泡声
- 音乐：命名风格（如 synthwave 145 BPM），不写"史诗音乐"这种模糊词

## Prompt 骨架（通用模板）

逐场景组装时，按以下字段结构化；缺省字段留空，不强行填充：

| 字段 | 含义 | 示例 |
|---|---|---|
| 用途 | 视频用在哪（产品讲解 / 宣传片 / 分镜） | 产品宣传短片 |
| 主体 | 核心对象 / 人物 | 产品 + 模特 |
| 镜头脚本 | 分镜与时长（0-4s / 4-8s …） | 0-4s 推进特写 |
| 运镜 | 相机运动 | 环绕 / 横移 |
| 视觉风格 | 电影级 / 动画 / 实拍 | 电影级调色 |
| 光线色彩 | 光向与色调 | 暖光、霓虹 |
| 音频 | 原生音 / 配乐 / BGM | Synthwave 124BPM |
| 保留项 | 图生视频须保留要素 | 人物不变形 |
| 输出规格 | 时长 / 画幅 / 分辨率 | 12s / 9:16 / 480P |

组装顺序：用途 → 主体 → 镜头脚本 → 运镜 → 视觉风格 → 光线色彩 → 音频 → 保留项 → 输出规格。仅保留有值的字段。

## 调用流程

1. get_user_info 检查余额。
2. list_models(modelType=VIDEO) 获取 H3（MiniMax）模型对象（含 publicModelId 与 pricingSnapshot）。若列表中无 H3，提示该模型当前在 AI-HIVE 不可用，推荐 Seedance 2.5 / Happyhorse 等替代。
3. 分析用户需求：T2V / I2V / FLF2V / Ref2V / 编辑迁移。
4. 如需图片、视频或音频参考素材，upload_media_from_path 逐个上传得到 mediaId；音频限 MP3/WAV、单文件最大 15 MiB。
5. 分别映射 `imageMediaIds`、`videoMediaIds`、`audioMediaIds`；只有当前模型配置明确支持参考音频和当前组合时才提交音频数组。
6. 按模式组装 prompt（参见上方对应模式指南）。
7. generate_video 提交任务，get_generation_task 跟踪到 `COMPLETED`。

## 输入检查

- 明确模式（T2V / I2V / FLF2V / Ref2V / 编辑迁移）。
- 参考素材仅使用用户主动选择的文件，且遵循 list_models 返回的参考上限；MP3/WAV 音频单文件 ≤15 MiB。
- 参考音频数量、时长和组合限制以当前模型配置为准；不兼容时保持 `audioMediaIds=[]`。
- 时长仅使用服务端支持的枚举值（公开值最长约 15 秒）。
- 画幅/分辨率仅使用服务端支持的枚举值（公开值最高 2K）。
- 多素材引用时必须用素材编号 + 用途明确每张素材。
- 编辑/迁移任务将源视频放入 `videoMediaIds` 并在 prompt 中写清修改范围。

## 生成后建议

- 尝试不同模式（I2V 不理想可改 T2V 或 Ref2V）。
- 调整景别（特写/近景/中景/全景/远景）。
- 增减参考图数量或改用首尾帧控制。
- 调整时长、分辨率（公开值 2K 上限）。
- 编辑不满意可调整源素材或换用 Seedance 2.5（更长/更强编辑场景）。

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

### 余额不足 / 任务被拒

**AI-HIVE 官网**：https://ai-hive.iclip.cn

**充值路径**（账户已存在）：
1. 访问 https://ai-hive.iclip.cn → 登录 AI-HIVE 账户
2. 进入「账户中心」/「钱包」/「充值」页面
3. 选择充值套餐或自定义金额 → 完成支付
4. 充值成功后回到 WorkBuddy，无需重新连接 Connector，直接重试任务

**注册路径**（首次用户）：
1. 直接访问 https://ai-hive.iclip.cn/login，进入注册页面
2. 使用手机号完成注册
3. 登录 → 回到 WorkBuddy 重新连接 AI-HIVE Connector 即可

**价格透明**：
- 每次调用前可调 `get_user_info` 查看当前余额
- 调用后实际扣费以服务端 `pricingSnapshot` 为准
- 若工具明确提示余额不足，停止创建任务；任务进入 `FAILED` 时按 `failure` 安全字段展示
- 详细价格参考：https://ai-hive.iclip.cn/pricing

**常见扣费场景参考**（具体以服务端为准）：
- 文本生成：按 token 数计费
- 图片生成：按张数 + 分辨率计费
- 视频生成：按秒数 + 分辨率计费

**其他被拒原因**：
- 账户被风控：联系 AI-HIVE 客服（https://ai-hive.iclip.cn → 登录 → 设置 → 联系客服）
- 模型临时不可用：稍后重试或换模型
- 内容违规审核：调整 prompt 后重试（避免敏感内容）
- list_models 无 H3：提示该模型当前在 AI-HIVE 不可用，推荐替代模型

- `PENDING` / `PROCESSING`：返回工具真实状态或进度，无进度数字时不自行估算。
- `COMPLETED`：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。注意 `COMPLETED` 状态不保证有视频 URL，必须检查返回体。
- `FAILED`：展示 `failure.code`、`failure.summary` 与 `failure.suggestion`（若返回），不暴露内部诊断。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

### 常见错误指引

| 错误类型 | 可能原因 | 处理建议 |
|---|---|---|
| 上传失败 413 | 文件超过大小限制 | 压缩视频或拆分素材；音频压缩至 15 MiB 以内 |
| 上传失败 415 | 文件格式不支持 | 转 mp4/mov/webm 视频、jpeg/png/webp 图片或 MP3/WAV 音频 |
| 音频组合被拒 | H3 当前配置不支持该参考音频数量、时长或媒体组合 | 移除或精简 `audioMediaIds`，保留原生声音描述，或改用兼容模型 |
| 生成失败（realistic human faces） | 上传内容含真实人脸 | 改用卡通/虚拟人物 |
| 生成失败（参数不支持） | `params` 中的时长/画幅超出枚举 | 调用 `list_models` 查询该模型支持的键、类型和值 |
| 参考素材超限 | 超过服务端参考上限 | 精简素材，遵循 list_models 返回的上限 |
| 余额不足 | 工具可读消息或 `failure.code`（若有） | 引导用户充值后重试 |
| 任务超时 | 服务端压力 | 等几分钟后用 taskId 重查询，不重复创建 |

## 调用示例

### 示例 1：参考生视频（产品设计）

**用户表达**：用产品图1 和场景图2，生成一个 8 秒的产品展示视频，带原生立体声。

**AI 行为**：
1. get_user_info 检查余额
2. list_models(modelType=VIDEO) 筛选 H3（MiniMax）的 publicModelId
3. upload_media_from_path 上传图1-2 得到 mediaId
4. 组装 prompt：素材指代（图1=产品，图2=场景）+ 时序分镜 + 运镜/光影/音效
5. `generate_video(imageMediaIds=[图1,图2], ...)` 提交
6. get_generation_task 跟踪到 `COMPLETED`，返回视频 URL + 参数摘要

### 示例 2：首尾帧

**用户表达**：用这张首帧图和尾帧图，生成 6 秒过渡视频。

**AI 行为**：upload 两张图 → `generate_video(firstFrameMediaId=图1, lastFrameMediaId=图2, params={duration: 6}, ...)`，参数以当前模型配置为准，然后跟踪结果。

### 示例 3：动作迁移（V2V）

**用户表达**：把视频1里人物的动作迁移到图1的角色上。

**AI 行为**：upload 视频1 + 图1 → `generate_video(videoMediaIds=[视频1], imageMediaIds=[图1], ...)`，prompt 含「将视频1的动作迁移到图1角色」，然后跟踪结果。

### English Example

User: "Generate an 8-second product showcase from product image 1 and scene image 2, with native stereo audio."

AI flow: get_user_info for balance, list_models(modelType=VIDEO) to fetch H3 (MiniMax) publicModelId, routingMode, and pricingSnapshot, upload images 1-2 via upload_media_from_path, assemble a structured prompt (asset mapping + timestamped storyboard + camera/light/audio), call generate_video with imageMediaIds, track with get_generation_task until COMPLETED, return video URL + parameter summary. Never ask the user to paste a Token into chat.

## 输出模板

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：failure.code + failure.summary + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
