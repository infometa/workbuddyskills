---
name: seedance-2-5-expert
display_name: Seedance 2.5 专家
display_name_en: Seedance 2.5 Expert
description: "通过指导agent智能调度 Seedance 2.5 模型，针对\"原生 30 秒长视频、最多 50 个全模态参考、专业级视频编辑与延长、首尾帧、关键帧/分镜、白模渲染、一键成片、无缝转场、多语言叙事\"等场景深度优化 prompt 工程，输出电影级、强角色一致性的高质量视频。"
description_zh: "通过指导agent智能调度 Seedance 2.5 模型，针对\"原生 30 秒长视频、最多 50 个全模态参考、专业级视频编辑与延长、首尾帧、关键帧/分镜、白模渲染、一键成片、无缝转场、多语言叙事\"等场景深度优化 prompt 工程，输出电影级、强角色一致性的高质量视频。"
description_en: "Agent optimizes Seedance 2.5 prompts for 30s long-form, up to 50 multimodal references, video editing, extension, first/last frame, keyframe, storyboard, white-model render, one-click, seamless transition, multilingual narrative."
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
- "Seedance 2.5"
- "seedance 2.5"
- "seedance2.5"
- "SD 2.5"
- "豆包视频"
- "视频编辑"
- "视频延长"
- "关键帧"
- "多宫格分镜"
- "白模渲染"
- "一键成片"
- "无缝转场"
- "30 秒视频"
- "长视频"
- "双 PE"
- "A/B prompt"
- "稳健版和增强版"
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


> 所有工具的真实返回值以服务端响应为准；本章节参数表描述的是模型级能力。部分高级参数（如输出格式、画幅）只有在 `list_models` 的当前模型配置明确暴露时才放入 `params`；否则由模型按任务类型自动处理，不要臆造键名或取值。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token

## 能力范围

本 Skill 专注 Seedance 2.5 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_video 工具完成视频生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 video 列出当前可用模型及价格快照，从中筛选 Seedance 2.5 对应的 publicModelId。
- upload_media_from_path：上传本地图片/视频或 MP3/WAV 音频并返回 mediaId，用于首尾帧与全模态参考；音频单文件最大 15 MiB。
- generate_video：使用选定模型与 prompt 创建视频任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用 Seedance 2.5 或需要长视频、强参考、可编辑的视频生成
- 用户提供图片/视频/音频素材，需要在该模型擅长的领域生成结果
- 用户希望跨场景复用同一模型能力保持风格与角色一致
- 用户需要专业级视频编辑、延长、首尾帧过渡、关键帧/分镜、白模渲染、一键成片或无缝转场
- 用户对生成结果的某项特性（真实质感/艺术风格/运镜/动态表现/多语言叙事）有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（平台会拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览

## 触发原则

积极触发 —— 有疑虑时就用本 Skill。只要有视频生成意图且涉及长视频、强参考、编辑/延长/首尾帧/分镜/白模/多语言任一特征，都应考虑使用。信号包括：
- 显式：用户提到 Seedance 2.5、首尾帧、视频编辑、视频延长、关键帧、分镜、白模、一键成片、无缝转场
- 隐含：任何 AI 长视频任务、跨镜头角色一致性、多镜头序列、图生视频、视频续写、多语言叙事
- 概念：电影级 AI 制作、原生音频生成、多模态参考、工业级视频生产

## 用户常见说法 → 对应能力

| 用户说法 | 触发能力 | 连接器参数倾向 |
|---|---|---|
| 「生成一段 30 秒产品宣传长片」 | 文生视频（无锁定） | 在 `params` 中使用当前模型配置允许的时长与画幅键值 |
| 「用这两张图做过渡」 | 首尾帧 | `firstFrameMediaId` + `lastFrameMediaId`；画幅约束如有则放入 `params` |
| 「把视频里背景换成雪山」 | 视频编辑 | `videoMediaIds` 含源视频，prompt 含编辑关键词 |
| 「这段再延长 5 秒」 | 视频延长 | `videoMediaIds` 含源视频；延长方向放入当前模型配置对应的 `params` 字段，建议 MOV |
| 「做一组分镜短片」 | 多宫格分镜 / 关键帧 | 参考图 + 时间戳分镜 |
| 「多个角色各自动作一致」 | 多主体角色引用 | 图N + 角色名逐一映射 |
| 「接着上一段继续拍」 | 分段尾帧接力 | 上段尾帧 → 下段首帧 |

## Seedance 2.5 模型规格

| 维度 | 规格 |
|---|---|
| 原生时长 | 最长 30 秒直出（API 通常 4-30 秒，以 list_models 枚举为准） |
| 模型级输入能力 | 文本 + 最多 50 个全模态参考素材（图片最多 30 张 4K；视频最多 10 段、总时长 ≤30s；音频最多 10 段、总时长 ≤30s）；具体数量、时长与组合以当前模型配置为准 |
| 输出 | MP4 / MOV（编辑、延长类建议 MOV 以保色亮度与声画一致）；API 常见 480p / 720p |
| 自由宽高比 | 支持 [0.4, 2.5] 之间任意宽高比（经输入素材控制） |
| 语言 | 原生支持 10 余种语言叙事 |
| 任务类型 | 参考生视频(R2V) / 首尾帧 / 视频编辑 / 视频延长 / 一键成片 / 无缝转场 / 组合能力 |

> 单次参考素材总上限 50 个；超出会被服务端拒绝。具体每张/每段的大小与格式限制以 `upload_media_from_path` 实际返回为准。

## OpenAPI 交叉验证：模型 ID 与参数（SDK models-reference.md，2026-08）

> 以下 `publicModelId` 与参数来自 AI-HIVE OpenAPI `models-reference.md`（经 SDK 交叉验证）。
> 在 AI-HIVE Connector 中**运行时一切以 `list_models` 实际返回为准**；下表用于预校验与 prompt 指引用，不臆造未返回字段。

### 已验证 publicModelId（Seedance 2.5）

| 任务类型 | publicModelId |
|---|---|
| 文生视频 T2V | `public_model_seedance_2_5_t2v` |
| 图生视频 I2V | `public_model_seedance_2_5_i2v` |
| 参考生视频 R2V | `public_model_seedance_2_5_r2v` |
| 视频编辑 | `public_model_seedance_2_5_video_edit` |
| 视频延长 | `public_model_seedance_2_5_video_extend` |

### 已验证参数（Seedance 2.5）

| 参数 | 取值 / 默认 | 说明 |
|---|---|---|
| `resolution` | 480p / 720p，默认 720p | 像素分辨率 |
| `duration` | -1（自动）或 4-30s，默认 -1 | 时长；-1 由模型自定 |
| 画幅参数（置于 `params`） | adaptive / 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 | 具体键名、默认值与模式限制以当前模型配置为准 |
| `generateAudio` | 默认 true | 原生音频 |
| `outputFormat` | mp4 / mov，默认 mp4 | 编辑/延长建议 mov 保色亮度与声画一致 |
| `watermark` | 默认 false | 水印 |
| `extendDirection` | forward / backward | 仅视频延长；向前/向后延长 |

> 连接器映射：I2V 的首帧使用 `firstFrameMediaId`；编辑与延长所需的画幅、时长约束放入 `params`，但具体键名和值必须来自当前模型配置。

**可复现性（可选）**：若 `list_models` 返回该模型支持 `seed` 参数，可固定种子复现结果（调试或抽卡对齐时使用）；不固定则由模型随机生成。参考社区 Seedance CLI 支持 `-1` 到 `2147483647` 的种子范围。

### 价格参考（¥/秒，以服务端 `pricingSnapshot` 为准）

| 分辨率 | 无参考 | 有参考 |
|---|---|---|
| 480p | 0.672 | 0.4032 |
| 720p | 1.512 | 0.9072 |

## 任务分类：有锁定 vs 无锁定

Seedance 2.5 根据传入素材是否锁定输出属性，把任务分为两类（Seedance 2.0 无此区分）：

### 有锁定：编辑 / 首尾帧 / 延长

这类任务会根据输入素材自动锁定部分生成参数，通常不支持自定义宽高比：

| 任务类型 | 锁定说明 | 连接器参数提示 |
|---|---|---|
| 视频编辑 | 锁定宽高比（严格对齐待编辑视频）；画幅字段使用当前模型配置允许的自适应值，时长通常对齐输入 | `videoMediaIds` 含源视频；prompt 含编辑关键词（编辑/增加/删除/修改/替换） |
| 首帧/首尾帧 | 锁定宽高比（严格对齐首帧图）；时长可自定义 | `firstFrameMediaId`（+`lastFrameMediaId`）；建议首尾帧画幅一致 |
| 视频延长 | 锁定宽高比（严格对齐待延长视频）；画幅与时长使用当前模型配置允许的 `params` | `videoMediaIds` 含源视频；prompt 含延长关键词（向前/向后延长/续写）；建议 MOV |

### 无锁定：参考任务 / 多宫格分镜 / 关键帧

参考类任务（含多宫格分镜、关键帧）不锁定输出宽高比与时长，用户可自定义：

- 多宫格分镜：生成画面不严格对齐分镜图细节，分镜图主要提供剧情参考；推荐简约线稿分镜，prompt 补齐动作/运镜/风格。
- 关键帧：多张独立分镜图作为关键帧输入，生成画面相对严格对齐输入图；时长可自定义。

## 模式 → 连接器参数矩阵（避免非法媒体组合）

> 借鉴 SDK 示例技能的 `validate_mode_inputs()`。映射到 `generate_video` 的五类媒体入参：`imageMediaIds` / `videoMediaIds` / `audioMediaIds` / `firstFrameMediaId` / `lastFrameMediaId`。
> 提交前按下表自检，**不要把所有媒体字段同时填上**；非法组合会被服务端拒绝（400）。

| 模式 | 首尾帧字段 | `imageMediaIds` | `videoMediaIds` | `audioMediaIds` | 参数锁定 |
|---|---|---|---|---|---|
| 文生视频 T2V | ✗ 禁止 | 空 | 空 | 空 | 画幅/时长在 `params` 中按当前配置填写 |
| 图生视频 I2V（首尾帧） | `firstFrameMediaId` 必填；尾帧可选 | 空 | 空 | 仅当前配置允许该组合时填写 | 自适应画幅值以当前配置为准 |
| 参考生视频 R2V | ✗ 禁止 | 按需填写参考图片 | 按需填写参考视频 | 按需填写参考音频 | 画幅/时长在 `params` 中按当前配置填写 |
| 视频编辑 edit | ✗ 禁止 | 可选参考图片 | **首个视频=待编辑**；后续可为参考视频 | 仅当前配置支持音频编辑/参考时填写 | 自适应画幅、原时长等值以当前配置为准 |
| 视频延长 extend | ✗ 禁止 | 可选参考图片 | **首个视频=待延长** | 仅当前配置支持声音连续参考时填写 | 延长方向、画幅、时长均按当前配置填写 |

> 关键规则：首尾帧字段只用于 I2V；普通参考素材按图片、视频、音频类型分开放入三个数组；T2V 不带媒体。编辑/延长的源视频放在 `videoMediaIds` 首位。外部参考音频只有在当前模型配置明确支持该模式与组合时才进入 `audioMediaIds`，否则保持空数组。

## Seedance 2.5 全模态能力清单

> 模型层面支持文本、图片、视频、音频的灵活组合。Connector 可上传 MP3/WAV 并提交 `audioMediaIds`，但模型是否接受仍以当前模型配置及合法组合为准。

| 任务类型 | 支持的能力 | 能力细化 |
|---|---|---|
| 参考生视频 | 主体参考 / 运动参考 / 白模参考 / 风格参考 / 音频参考 / 宫格分镜参考 / 关键帧参考 | 主体图/音视频/图+音色；动作/表情/运镜/特效运动；粗/细粒度白模渲染；风格图/视频；音乐/台词/音色；多宫格分镜；单/多图关键帧、首尾帧 |
| 首尾帧生视频 | 首帧 / 首尾帧 | 严格通过 `firstFrameMediaId` / `lastFrameMediaId` 控制 |
| 编辑视频 | 视频指令编辑 / 视频参考图编辑 / 视频音频编辑 | 增/改/删主体、服饰、运镜、特效、背景、字幕、水印；支持时间戳指定生效时段；人声/音乐/音效增删改 |
| 视频延长 | 向前/向后延长 | 可要求画面/音频无缝衔接；建议 MOV |
| 其他 | 一键成片 / 视频无缝转场 / 组合能力 | 多图/视频生成短片；两段视频补全间隙转场；上述能力自由组合 |

## 素材输入建议

| 场景 | 输入建议 |
|---|---|
| 模型级输入素材上限 | 图片最多 30 张 4K；视频最多 10 段（总时长 ≤30s）；音频最多 10 段（总时长 ≤30s、MP3/WAV 单文件 ≤15 MiB）；合计 ≤50。最终以当前模型配置为准 |
| 主体音视频（建议几个主体） | 1-5 主体效果较好；6-10 可尝试但稳定性下降、可能需抽卡 |
| 主体音视频（建议时长） | 5-10s 效果较好；更长稳定性下降 |
| 主体图（建议几个主体） | 1-8 主体效果较好；9-12 可尝试但稳定性下降 |
| 多视角主体图 | 1-5 主体「单视图」「多视图」均可；超 5 主体建议拆分为多张不同视图分别输入 |
| 宫格图分镜 | 更适用于 15 个以下分镜；推荐火柴人/线稿，不在分镜图上写过多文字 |
| 白模参考 | 简单建模（粗粒度）参考效果较好，建议仅用简单几何体拼接 |
| 视频编辑 | 20s 以内效果较好；更长稳定性下降 |
| 视频参考图编辑 | 1-5 张参考图较好；6-8 可尝试但稳定性下降 |
| 视频延长 | 为最佳声画衔接，输入与输出均采用 MOV |

## 超长视频：分段 + 尾帧接力

Seedance 2.5 原生最长 30 秒（H3 仅 15 秒）。要生成超过该上限的连贯长片，用「分段生成 + 尾帧接力」：

1. 生成第一段，时长取模型上限内（2.5 用 30s / H3 用 15s）。
2. 获取尾帧：只有当 `get_generation_task` 明确返回可用的尾帧素材链接时才使用；否则请用户提供已截取的本地尾帧，或使用当前环境中确实可用的取帧能力，再经 `upload_media_from_path` 上传。
3. 以该尾帧作为下一段的 `firstFrameMediaId`，prompt 写明「紧接上一段结尾，运镜 / 主体 / 服装连续不跳变」，继续生成。
4. 重复直到完片；每段保持相同角色锚点与画幅，保证一致性。

> 借鉴自社区 Seedance CLI 的 `returnLastFrame` + 多段连续生成模式；在 AI-HIVE Connector 中一切以 `get_generation_task` 实际返回为准，不臆造尾帧字段。

## 角色引用系统（核心语法）

Seedance 2.5 可把参考图、视频和音频分配为不同素材职责。三类素材分别按各自上传顺序编号为图1、图2…… / 视频1、视频2…… / 音频1、音频2……：

- 图1 作为首帧 / 图2 作为尾帧
- 图1 的角色作为主体（身份锚定）
- 场景参考图3
- 参考视频1 的运镜
- 穿着图2 中的服装
- BGM 节拍与音色参考音频1（仅在当前模型配置明确支持参考音频和当前模式组合时绑定）

多主体逐一列清映射关系，人数多时用清单罗列（如「img1-2 是人物1；img3-4 是人物2」），避免角色混淆或重复。外部参考音频、Prompt 中的声音描述、`params` 中的原生声音开关分别记录，不得混用或互相替代。

### 音频素材职责

- Generate：音频可负责 BGM 节拍、台词/音色或声音风格参考，不替代生成画面所需的主体、场景与动作描述。
- Edit：`videoMediaIds` 首个视频仍是待编辑母版；音频只负责当前配置允许的声音替换、增删改或参考，不得改变非目标画面职责。
- Extend：`videoMediaIds` 首个视频仍是延长源；音频只负责当前配置允许的声音氛围、节奏或声画连续参考。
- 三种模式都必须保持音频 mediaId 与“音频N”映射一致；不兼容时不提交 `audioMediaIds`，只保留 Prompt / `params` 中当前模型原生声音能力。

## Prompt 公式（导演思维）

把 Seedance 2.5 当作视觉内容生产者，用导演思维书写结构化 Prompt：

**1. 素材指代**：明确每个图、视频与音频的编号（各自按上传顺序）及用途（谁是形象、动作、场景、节拍或音色）。仅当前模型配置明确支持参考音频时绑定 `audioMediaIds`。

**2. 一句话概述**：主体 + 地点 + 事件 + 题材/风格 + 特殊运镜。

**3. 具体情节描述**：逐段描述画面内容、运镜、动作、台词、音效，尽量用正向描述。只有用户明确给出分镜/节拍，或卡点、对白对齐、关键事件边界确实需要时，才使用连续整数秒时间戳；其他任务用自然事件顺序或「镜头 N」，不因总时长较长就自动切时间片。支持负向控制：如「不要字幕」「无 bgm，只生成环境音」。

**4. 结尾**：补充贯穿始终的画面细节，如机位/运镜、环境/场景、声音、氛围。

需要时间对齐的视频可按时间片分段，例如：
`0-3秒女孩推门走进咖啡馆镜头向前推；3-6秒她坐下点单镜头平移到吧台；6-10秒咖啡上桌特写镜头固定。`

### 时间戳写法

- 整数秒时间区间（注意连续，避免 `0-3秒...5-6秒` 这种跳变）：`0-3秒……3-7秒……7-15秒` 或 `[1s-4s]…[4s-8s]`
- 时间点：`第5s快速向左横移转场`
- 相对时间：`张三呆滞站立，3秒后周围人纷纷摇头`
- 不建议用时间戳控制频率（如「一秒摇头3次」）

### 进阶：镜头语言

- 通识可直接写：景别（大全景/全景/中景/近景/特写）、运镜（推/拉/摇/移/跟/环绕/俯冲/后拉/上摇/手持晃动）、机位（低角度/俯视/第一人称）
- 热门运镜可直接写：一镜到底、希区柯克变焦、航拍、FPV、子弹时间、手持、回弹变速
- 小众专业名词转为「名词+描述性解释」
- 转场写清触发点与方式、时间

### 进阶：动作/表情

- 动作：优先概括性描述（「连续高抬腿和空翻」），只在记忆点写具体细节
- 表情：写描述性语句（「脸上带着满足的笑容，大口吃饭」），减少成语

### 进阶：白模参考/渲染

- 写明希望参考白模视频的什么元素（运镜/动作/光影）
- 叠加参考图时，写明参考图与白模的对应关系
- 建议在 Prompt 中详细描述希望生成的视频内容，文本需与白模吻合

### 进阶：多宫格分镜/关键帧

- 多宫格分镜：≤15 分镜；推荐线稿；prompt 避免前后矛盾；宫格图不严格对齐，需严格对齐时用多关键帧
- 关键帧：第一句写「以图片1至图片N的顺序作为关键帧」，按序传入

## 与 Seedance 2.0 的差异

1. 响应时间戳：2.0 只响应镜头序号，2.5 响应整数秒时间戳。
2. 多视图：2.0 不建议多视图主体参考，2.5 支持。
3. 自由宽高比：2.0 仅 6 档固定，2.5 支持 [0.4, 2.5] 任意宽高比。
4. V2V 画质：2.5 支持 MOV，编辑/延长中更好保持颜色亮度与声画一致。

## 双 PE 对照模式（仅用户明确请求时）

当用户明确要求“双 PE”“A/B prompt”“稳健版和增强版”“两版提示词对照”或“组内盲测”时，读取 [Seedance 2.5 双 PE 对照规范](../references/seedance-2-5-dual-pe.md)。普通生成、编辑或延长请求继续只产出一个最佳 Prompt，不自动扩展为两版。

- 版本 A 命名为**稳健基线版**，完整、清晰、低风险，不为突出另一版而故意写弱。
- 版本 B 命名为**优化增强版**，只增强镜头、节奏、场景 knowhow、素材调度与可观察细节，不增加未经用户提供的事实。
- 两版共享同一任务类型、事实边界、素材职责和接口参数；不得用不同模型、路由、媒体或参数制造差异。
- 默认采用 **Prompt-only**：只交付两版 Prompt 与差异说明，不调用 `generate_video`。
- 只有用户明确要求实际运行两版时，先说明会产生**两次独立计费调用**并取得确认；确认后才分别创建两个任务并跟踪真实结果。
- 版本名称固定为“稳健基线版 / 优化增强版”；当前交付物没有足以证明某内部 PE 包为官方发布物的来源链。

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

组装顺序：用途 → 主体 → 镜头脚本 → 运镜 → 视觉风格 → 光线色彩 → 音频 → 保留项。仅保留有值的字段。

**输出参数（不写入 Prompt）**：时长、画幅、分辨率、输出格式、原生声音开关等属于接口参数。只有 `list_models` 的当前模型配置明确暴露对应键和值时，才放入 `generate_video.params`；不要把这些接口参数混入 Prompt 正文。

## 调用流程

1. get_user_info 检查余额。
2. list_models(modelType=VIDEO) 获取 Seedance 2.5 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 分析用户需求：文生 / 图生 / 首尾帧 / 多图角色 / 编辑 / 延长 / 分镜 / 白模 / 一键成片 / 转场，并判断用户是否明确要求双 PE 对照。
4. 如需图片、视频或音频参考素材，upload_media_from_path 逐个上传得到 mediaId；MP3/WAV 音频单文件最大 15 MiB（模型级总上限仅作参考，实际以当前配置为准）。
5. 按类型与上传顺序建立图N、视频N、音频N映射；普通模式组装一个最佳 Prompt；双 PE 模式按参考规范先交付两版 Prompt，保持同源、同素材、同参数（包括相同 `audioMediaIds` 值与顺序）。
6. 仅在用户要求实际生成时调用 generate_video；双 PE 实际运行须先确认两次独立计费调用，再分别提交并用 get_generation_task 跟踪到终态。

## 输入检查

- 明确生成模式（文生 / 图生 / 首尾帧 / 多图角色 / 编辑 / 延长 / 分镜 / 白模 / 一键成片 / 转场）。
- 参考素材仅使用用户主动选择的文件，且总数 ≤50；音频限 MP3/WAV 且单文件 ≤15 MiB。
- 只有当前模型配置明确支持参考音频和当前模式组合时才提交 `audioMediaIds`；否则保持空数组。
- 时长仅使用服务端支持的枚举值（通常 4-30 秒）。
- 画幅仅使用服务端支持的枚举值；编辑/延长/首尾帧类任务优先 `adaptive`。
- 多图角色引用时，必须用图N + 角色名明确每张图用途。
- 编辑/延长任务通过 prompt 关键词触发，并将源视频放入 `videoMediaIds`。
- 首尾帧通过 `firstFrameMediaId` / `lastFrameMediaId` 控制。
- 编辑/延长建议输出 MOV 以保声画一致。

## 生成后建议

- 尝试不同模态（文生不理想可改图生、首尾帧或参考）。
- 调整运镜（推/拉/摇/移/跟/升/降/固定）。
- 增减参考图数量或改用线稿分镜/关键帧。
- 调整时长（短视频连贯叙事，长视频用时间戳分镜）。
- 编辑/延长不满意可换 MOV 或调整源素材。

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
- 双 PE 的 Prompt-only 模式不调用付费工具；实际运行 A/B 会创建两个独立计费任务，必须先向用户说明并取得确认。

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
- `COMPLETED`：返回所有可用视频链接、缩略图与工具明确给出的部分失败信息。注意 `COMPLETED` 状态不保证有视频 URL，必须检查返回体。
- `FAILED`：展示 `failure.code`、`failure.summary` 与 `failure.suggestion`（若返回），不暴露内部诊断。
- 超时或网络不明：拿到 taskId 时只查询原任务，不重复创建。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

### 常见错误指引

| 错误类型 | 可能原因 | 处理建议 |
|---|---|---|
| 上传失败 413 | 文件超过大小限制 | 图片/视频按服务端限制压缩或拆分；音频压缩至 15 MiB 以内 |
| 上传失败 415 | 文件格式不支持 | 图片转 jpeg/png/webp，视频转 mp4/mov/webm，音频转 MP3/WAV |
| 音频组合被拒 | 当前模型、模式或媒体组合不兼容 | 移除 `audioMediaIds`，保留 Prompt / `params` 中当前模型支持的原生声音需求，或改选兼容模型 |
| 生成失败（realistic human faces） | 上传内容含真实人脸 | 改用卡通/虚拟人物 |
| 生成失败（参数不支持） | `params` 中的时长/画幅或开关类型不符合配置 | 调用 `list_models` 查询该模型支持的键、类型和值 |
| 参考素材超限 | 超过 50 个或单类超上限 | 精简素材至 50 以内，遵循素材输入建议 |
| 余额不足 | 工具可读消息或 `failure.code`（若有） | 引导用户充值后重试 |
| 任务超时 | 服务端压力 | 等几分钟后用 taskId 重查询，不重复创建 |

## 调用示例

### 示例 1：参考生视频（多主体）

**用户表达**：用角色图1-2 和场景图3，生成一个 10 秒电影级短片，角色在雪夜房间对话。

**AI 行为**：
1. get_user_info 检查余额
2. list_models(modelType=VIDEO) 筛选 Seedance 2.5 的 publicModelId
3. upload_media_from_path 上传图1-3 得到 mediaId
4. 组装 prompt：素材指代（图1-2=人物，图3=场景）+ 时序分镜（0-5s…5-10s…）+ 运镜/光影/音频
5. `generate_video(imageMediaIds=[图1,图2,图3], ...)` 提交
6. get_generation_task 跟踪到 `COMPLETED`，返回视频 URL + 参数摘要

### 示例 2：视频编辑

**用户表达**：把视频1里男人的台词改成「你不要过来啊」，口音改东北口音。

**AI 行为**：upload 视频1 → `generate_video(videoMediaIds=[视频1], ...)`，prompt 含「仅编辑视频1中男人的台词…」，再用 `get_generation_task` 跟踪。

### 示例 3：首尾帧

**用户表达**：用这张首帧图和这张尾帧图，生成 6 秒过渡视频。

**AI 行为**：upload 两张图 → `generate_video(firstFrameMediaId=图1, lastFrameMediaId=图2, params={duration: 6}, ...)`；参数键和值以当前模型配置为准，然后跟踪结果。

### English Example

User: "Generate a 10-second cinematic clip from character images 1-2 and scene image 3, with the characters talking in a snowy night room."

AI flow: get_user_info for balance, list_models(modelType=VIDEO) to fetch Seedance 2.5 publicModelId, routingMode, and pricingSnapshot, upload images 1-3 via upload_media_from_path, assemble a structured prompt (asset mapping + timestamped storyboard + camera/light/audio), call generate_video with imageMediaIds and runtime-validated params, track with get_generation_task until COMPLETED, return video URL + parameter summary. Never ask the user to paste a Token into chat.

## 输出模板

### 成功：taskId + 模型与参数 + 视频 URL 列表 + 下一步建议
### 失败：failure.code + failure.summary + 原因摘要 + 下一步建议
### 部分失败：成功视频完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
