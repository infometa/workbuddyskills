---
name: wan3-video-expert
display_name: Wan 3.0 视频专家
display_name_en: Wan 3.0 Video Expert
description: "通过指导agent智能调度 Wan 3.0 模型，针对电影短剧、对白口播、品牌 TVC、电商展示、材质微距、开箱试穿等场景深度优化 prompt 工程，支持 T2V/I2V/R2V 三模态、首尾帧控制、多镜头时间戳编排与图片/视频/音频混合参考，输出电影感、高一致性的视频。"
description_zh: "通过指导agent智能调度 Wan 3.0 模型，针对电影短剧、对白口播、品牌 TVC、电商展示、材质微距、开箱试穿等场景深度优化 prompt 工程，支持 T2V/I2V/R2V 三模态、首尾帧控制、多镜头时间戳编排与图片/视频/音频混合参考，输出电影感、高一致性的视频。"
description_en: "Agent optimizes Wan 3.0 prompts for cinematic shorts, dialogue, brand TVC and e-commerce videos across T2V/I2V/R2V, with first/last-frame control, multi-shot timelines and mixed media references."
category: media
version: 1.2.1
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片、视频与音频
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、get_model、upload_media_from_path、generate_video 与 get_generation_task
triggers:
- "Wan 3.0"
- "Wan3"
- "wan3"
- "通义万相"
- "电影短剧"
- "品牌TVC"
- "口播视频"
- "电商展示视频"
- "材质微距"
- "开箱视频"
---

## 能力范围

本 Skill 专注 Wan 3.0 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成，覆盖新写、改写与 badcase 诊断三类任务。默认只交付提示词、素材职责、参数建议和风险提示，不上传素材、不调用付费生成；只有用户明确说「生成」「开始跑」「提交任务」等执行指令，才进入付费流程。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 Wan 3.0 对应的 publicModelId。
- get_model：查询单个模型的当前调用契约（paramsSchema、媒体要求、计费因素与 pricingSnapshot）。
- upload_media_from_path：上传本地图片/视频或 MP3/WAV 音频并返回 mediaId；音频单文件最大 15 MiB。
- generate_video：使用选定模型与 prompt 创建视频任务；支持 dryRun 只读预检。
- get_generation_task：使用 taskId 查询任务状态与结果。

普通文本聊天、图片生成或非 Wan 视频任务不在本 Skill 范围，分别回到 text-creator、image-creator、video-creator skill。

## 适用场景

- 用户明确提到 Wan 3.0 / Wan3，或需求匹配其擅长场景（电影短剧、对白、品牌 TVC、电商展示、口播、材质微距、开箱、试穿、多卖点视频）
- 用户希望新写、改写或诊断 Wan 3.0 提示词
- 用户提供素材（图片/视频，以及当前路线明确兼容的音频）并明确发起 Wan 3.0 视频生成
- 用户对运镜、多镜头叙事、音画同生或商品一致性有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 用户要求直接编辑已有视频——AI-HIVE 当前不提供 Wan 3.0 V2V 编辑入口，不得宣称可直接编辑旧视频
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览

## Wan 3.0 擅长什么

| 能力 | 说明 |
|---|---|
| 电影短剧与对白 | 多镜头时间戳叙事；对白逐句带说话者、情绪、语调、语速、音色与口音；支持音画同生 |
| 三模态覆盖 | T2V 文生视频、I2V 首帧/首尾帧图生视频、R2V 图片/视频/音频混合参考生视频 |
| 长视频与多镜头 | duration 2–30 秒整数，多镜头按连续时间段编排，总体设定锁定一致性 |
| 电商与品牌 | 商品一致性锁、材质微距/ASMR、开箱、试穿走秀、多卖点分镜、品牌 TVC 创意结构 |

上述音频能力包含 prompt / `params.audio` 的原生声音能力与 R2V 参考音频；只有 `list_models` 的当前模型配置明确支持参考音频及当前组合时才提交外部音频，否则保持 `audioMediaIds=[]`。

## 模型规格

| 维度 | 规格 |
|---|---|
| 版本 | 标准版 / Pro（prime），模式互斥，由用户选择，不静默升级 |
| 模态 | T2V / I2V / R2V |
| 单次时长 | 2–30 秒整数；不支持 -1 或自动时长 |
| 分辨率 | 480P / 720P / 1080P |
| 宽高比 | adaptive / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 |
| 声音 | `params.audio` 布尔；未明确需要声音时也要向用户展示其值 |
| 其他参数 | `params.seed`（0–2147483647，可选）、`params.watermark`（可选布尔） |

R2V 当前素材上限：参考图片最多 10 张；参考视频最多 5 段，每段 1–15 秒且总时长不超过 15 秒；参考音频最多 5 段，每段 1–15 秒且总时长不超过 15 秒；参考视频总时长与输出 duration 之和不超过 30 秒。执行前以当次模型详情中的 `videoConfig` 为准。

## 模型 ID（以 list_models 实际返回为准）

> 以下 `publicModelId` 用于预校验；运行时一切以 `list_models` / `get_model` 实际返回为准，不臆造未返回字段。

| 版本 | 模态 | publicModelId | 媒体字段 |
|---|---|---|---|
| 标准 | T2V | `public_model_wan_3_0_video` | 无 |
| 标准 | I2V | `public_model_wan_3_0_video_i2v` | `firstFrameMediaId` 必填，`lastFrameMediaId` 可选 |
| 标准 | R2V | `public_model_wan_3_0_video_r2v` | `imageMediaIds` / `videoMediaIds` / `audioMediaIds` 至少一类非空 |
| Pro | T2V | `public_model_wan_3_0_video_prime` | 无 |
| Pro | I2V | `public_model_wan_3_0_video_prime_i2v` | `firstFrameMediaId` 必填，`lastFrameMediaId` 可选 |
| Pro | R2V | `public_model_wan_3_0_video_prime_r2v` | `imageMediaIds` / `videoMediaIds` / `audioMediaIds` 至少一类非空 |

模式互斥。首尾帧不能放进 `imageMediaIds`；普通参考图不能冒充 `firstFrameMediaId`。

## 工作流

1. 识别任务：新写、改写、badcase 诊断，或明确生成。
2. 确认模式与素材职责：无参考用 T2V；首帧/首尾帧用 I2V；图片、视频或音频参考用 R2V。标准版与 Pro 由用户选择；未指定时给出差异并询问，不静默升级。
3. 按需读取参考：
   - 模型、字段、价格与付费流程：[`references/ai-hive-contract.md`](references/ai-hive-contract.md)
   - Wan 公式、素材指代、多镜头：[`references/prompt-formulas.md`](references/prompt-formulas.md)
   - 电影、短剧、光影、材质与运动：[`references/scene-craft.md`](references/scene-craft.md)
   - 电商、口播、TVC、品类风险：[`references/ecommerce.md`](references/ecommerce.md)
   - badcase、对白、声音与验收：[`references/diagnosis-and-audio.md`](references/diagnosis-and-audio.md)
4. 输出可直接复制的最终提示词；多素材时先列「编号 → 职责 → 全片/局部生效范围」。
5. 若明确生成，进入下方「调用流程」。

## 写作硬规则

- R2V 参考必须写 `@图片1`、`@视频1`、`@音频1`；各类型按上传顺序分别编号。禁止用 `图1`、`@图1` 或自创别名替代。
- I2V 首帧或首尾帧已经承载主体、场景与风格，提示词主要写运动过程、状态变化、运镜和声音，不重复素材外观。
- 多镜头给出连续时间段，首尾相接且总时长等于目标 duration；需单镜头时明确写「生成单镜头」或「一镜到底」。
- 对白逐句写说话者、带引号原文、情绪、语调、语速、音色和口音；声音效果只描述期望，不承诺精准口型或逐帧时长必然实现。
- 把抽象形容词改成可见结果：几何、尺度、材质、光线作用、运动轨迹、速度与停止条件。关键约束优先使用正向描述。
- 品牌、商品结构、人物和服装要写一致性锁；复杂开合、液体、手部交互先提示风险，优先拆段或改为动作前后状态。
- `audio=false` 时不要在提示词里要求对白、旁白、BGM 或音效。

## 输出格式

### 新写/改写

1. **模式与素材职责**：T2V / I2V / R2V；列素材映射。
2. **最终提示词**：一段可复制文本；需要多镜头时使用连续时间戳。
3. **参数建议**：duration、resolution、ratio、audio；只写 AI-HIVE 当前支持的值。
4. **风险与备选**：仅列会影响成片的 1–3 项。

### Badcase

1. **已观察现象**：只写用户提供的事实。
2. **可能归因**：明确标成推测。
3. **最小补丁**：用「删 / 改 / 加」给出局部 diff；没有原提示词时说明无法逐字 diff，不整篇重写。
4. **A/B 复测**：每轮只改变一个变量，其余素材、seed 和参数保持一致。

## 调用流程

1. `get_user_info` 获取余额。
2. `list_models({modelType:"VIDEO", detail:"full"})` 获取当前 Wan 3.0 模型、routingMode、参数配置与 `pricingSnapshot`；需要单模型契约时用 `get_model` 查询。
3. 选择与素材模式和版本完全匹配的 publicModelId。
4. 如需素材，`upload_media_from_path` 逐个上传，保持各类型上传顺序与提示词 `@图片N` / `@视频N` / `@音频N` 一致。
5. 先用 `dryRun=true` 预检参数与媒体并获取预估费用（不创建任务、不扣费，此时省略 `pricingSnapshot` 与 `clientRequestId`）。
6. 展示 publicModelId、routingMode、duration、resolution、ratio、audio、计费维度、预计费用和余额，等待用户确认。
7. 用稳定 UUID 作为 `clientRequestId`、原样回传 `pricingSnapshot` 调用 `generate_video`。
8. 返回 pending 时只用 `get_generation_task({taskId})` 查询；不得为同一逻辑请求重复创建任务。

### clientRequestId 重试规则

- 传输中断、`REQUEST_IN_PROGRESS`：参数完全相同时复用原 ID。
- 价格快照过期：刷新 `list_models`，保持业务参数并复用原 ID 重试 1 次。
- 余额、参数、媒体或已缓存模型调用失败：修正后使用新 ID；原 ID 只会重放旧失败。
- `REQUEST_OUTCOME_UNKNOWN`：停止自动重试，不自动生成新 ID，提示人工核查。
- 任何业务参数变化都代表新逻辑请求，使用新 ID。

## 输入检查

- 明确模态（T2V / I2V / R2V）与版本（标准 / Pro），素材字段与模式匹配。
- 参考图片、视频与音频仅使用用户主动选择的文件；MP3/WAV 音频单文件 ≤15 MiB。
- 时长仅使用 2–30 的整数；不使用 -1 或自动时长。
- 画幅与分辨率仅使用服务端支持的枚举值。
- 不把本地路径或公开 URL 直接写成媒体输入；先上传再引用 mediaId。
- I2V 时 prompt 聚焦变化与动态，不重复静态信息；R2V 时必须写清每个素材职责。

## 价格与确认门槛

- 价格只能来自本次 `list_models({modelType:"VIDEO", detail:"full"})` / `get_model` 或 dry-run 返回，不得引用文档、历史记忆或示例价格。
- 付费生成前必须先展示 publicModelId、routingMode、duration、resolution、ratio、audio、计费维度、预计费用和余额，再等待用户确认。
- pending 任务只调用 `get_generation_task`；不得为同一逻辑请求重复创建任务。

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `modelType`（可选，string）：资源类型枚举 `TEXT` / `IMAGE` / `VIDEO`（本 Skill 用 `VIDEO`）
- `detail`（可选，string）：`lite` 只返回各路由售价摘要用于选型；`full`（默认）返回完整公开详情（含 `pricingSnapshot`）

### `get_model`
- `publicModelId`（必填，string）：来自 `list_models` 的当前模型 ID
- `routingMode`（可选，string）：获取指定线路的专属契约
- 返回该模型当前唯一调用契约：`paramsSchema`、媒体要求、计费因素、示例与 `pricingSnapshot`

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
- `dryRun`（可选，boolean）：`true` 时只校验参数与媒体并返回预估费用，不创建任务、不扣费，此时省略 `pricingSnapshot` 与 `clientRequestId`
- `clientRequestId`（付费调用必传，string）：稳定 UUID 幂等键；传输中断或刷新过期快照后用原值同参重试，修正业务参数后必须换新
- `pricingSnapshot`（付费调用必传，object）：`list_models(detail="full")`、`get_model` 或 dry-run 返回的价格快照，原样回传，不自行构造或修改

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

## 事实与合规边界

1. 只使用 list_models 与 get_model 真实返回的 publicModelId、参数契约与 pricingSnapshot。
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

- `PENDING` / `PROCESSING`：返回工具真实状态或进度，无进度数字时不自行估算。
- `COMPLETED`：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。
- `FAILED`：展示 `failure.code`、`failure.summary` 与 `failure.suggestion`（若返回），不暴露内部诊断。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

### 常见错误指引

| 错误类型 | 可能原因 | 处理建议 |
|---|---|---|
| 上传失败 413 | 文件超过服务端大小限制 | 压缩视频或拆分素材；音频压缩至 15 MiB 以内（其他上限见 references/material-prep.md） |
| 上传失败 415 | 文件格式不支持 | 转 mp4/mov/webm 视频、jpeg/png/webp 图片或 MP3/WAV 音频 |
| 外部音频不兼容 | 当前 Wan 3.0 路线或媒体组合不支持 `audioMediaIds` | 移除音频数组，保留 Prompt / `params` 的原生声音能力，或改选兼容模型 |
| 生成失败（realistic human faces） | 上传内容含真实人脸 | 改用卡通/虚拟人物，或换 Seedance 工具 |
| 生成失败（参数不支持） | `params` 中的时长/画幅超出枚举 | 调用 `list_models` 查询该模型支持的键、类型和值 |
| 余额不足 | 工具可读消息或 `failure.code`（若有） | 引导用户充值后重试 |
| 任务超时 | 服务端压力 | 等几分钟后用 taskId 重查询，不重复创建 |

## 输出模板

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：failure.code + failure.summary + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
