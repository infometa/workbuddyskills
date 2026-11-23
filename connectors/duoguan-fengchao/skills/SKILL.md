---
name: duoguan-fengchao
description: 夺冠蜂巢（duoguan-fengchao）AI 自媒体内容生产。当用户需要热点选题、口播/图文文案、情景短剧、配图、配音、播客、视频封装、多账号内容运营或发布准备时使用本连接器。连接后先调用 system.status 确认服务与身份。
version: 1.0.46
author: 夺冠蜂巢
---

# 夺冠蜂巢（Duoguan Fengchao）

夺冠蜂巢是面向自媒体团队和内容创作者的 AI 内容生产平台，通过 MCP 工具覆盖从资料沉淀到发布准备的完整链路。

## 连接与认证

- 本连接器使用 OAuth（OAuth 2.1 + PKCE）认证，由 WorkBuddy 自动完成授权，无需手动配置凭证。
- 兼容历史 `ca_live_` API Key 认证方式。
- 连接后调用 `system.status`，确认服务可用、身份与租户正确，再开始内容生产。
- 首次连接时读取 `account.context.welcomeGuide`，优先展示 `firstAction` 和 `quickExperience.examplePrompts`，用结果导向的短句欢迎用户：直接提供一个行业和冲突即可开始，不要先要求初始化资料、创建角色、创建场景或查询选题池。示例应根据用户已提供的行业或话题动态改写，不能机械照搬财税示例。普通文案未明确形式时默认按短视频口播开始；只有用户意图无法判断时才询问形式。若 `quickExperience.available=true`，主动说明没有现成角色资产也能选择返回的真人或 3D 卡通内置套装做极速体验，无需准备素材，只需确认一次剧本分镜，系统会复用角色、声音、场景和首帧，约 5-10 分钟看到约 15 秒成片；已有资产用户默认仍可复用自己的套装，只有明确选择极速体验时才切换系统套装；具体可用套装仍以 `drama.plan context` 为准。
- 首次欢迎同时展示 `welcomeGuide.quickMediaActions`：用户可以直接提供一句画面描述生成图片，或提供一段 A/B 对话生成双人音频；结果自动进入素材库，可预览、下载和复用，不会自动写入文案中心或角色套装。不要把内部参数名展示给用户，也不要把“直接生成视频”列为当前能力。
- OAuth 授权过期时 WorkBuddy 会提示重新授权；`ca_live_` Key 过期需在第三方平台重新获取。
- 安装清单地址：`https://fc.duoguan.com/agent-kit/manifest.json`；需要安装或更新配套 Skill 时先读取该清单中的版本和下载地址。

## 配套 Skill

连接成功后，引导用户安装以下 5 个配套 Skill。它们负责内容生产的流程编排与用户引导，与连接器的 MCP 工具配合使用：

| Skill | 职责 |
|---|---|
| `duoguan-fengchao-brain-onboarding` | 内容大脑初始化：从官网/PDF/Word/资料夹提炼业务知识、获取确认并写入大脑档案 |
| `duoguan-fengchao-content-production` | 内容生产：选题、口播/图文文案、配图、反馈修订与定稿 |
| `duoguan-fengchao-media-production` | 音视频生产：播客音频/视频、真人录制、视频封装与交付 |
| `duoguan-fengchao-drama-production` | 情景短剧：由端侧 Agent完成研究、剧本改编和全片分镜，再通过蜂巢生成首帧、片段和完整成片 |
| `duoguan-fengchao-style-assets` | 风格与资料：开头钩子、文案/图片风格、热点资料的提炼与保存 |

安装渠道与具体安装方式由 Agent 按当前环境处理（如官网下载导入、技能市场安装等）；安装完成后按对应 Skill 的流程编排执行，本连接器只负责提供 MCP 工具。

## 核心工具分组

| 分组 | 工具前缀 | 用途 |
|------|------|------|
| 系统与身份 | `system.*` / `account.*` | 服务状态、版本、身份与租户上下文 |
| 内容大脑 | `brain.*` | 品牌画像、业务方向、资料初始化与建议采纳 |
| 品牌画像 | `brand_profile.*` | 品牌资料提取、查询与更新 |
| 内容成员 | `member.*` | 多账号成员入驻与画像草稿 |
| 个人工作区 | `personal_workspace.*` | 个人素材整理、确认与删除 |
| 工作上下文 | `work_context.*` | 当前选题、候选内容、录制素材的选中 |
| 选题 | `topic.*` / `hotspot.*` | 热点研究、选题生成、提案提交与审核 |
| 文案 | `script.*` | 口播/图文文案生成、更新、反馈与定稿 |
| 风格资产 | `opening_hook.*` / `style.*` | 钩子、文案风格、视觉风格的创建与管理 |
| 配图 | `image.*` | 小红书/图文配图生成与状态查询 |
| 媒体素材 | `media_asset.*` / `recording.*` | 素材上传、参考图注册、字幕状态、录制 |
| 音视频 | `podcast.*` / `voice.*` / `video_packaging.*` | 双人播客、单人语音、视频封装 |
| 情景短剧 | `drama.*` | 剧本分镜、角色场景资产、首帧按反馈修改、视频片段局部重生成与完整成片合成 |
| 生产任务 | `production.*` | 异步任务列表与状态查询 |
| 发布 | `video_publish.*` | 多平台发布投递 |
| 内容诊断与预览 | `content_diagnosis.*` / `content_preview.*` | 内容诊断与发布前预览 |
| 运营资源 | `resource.*` / `team.*` | 资源查询与团队邀请 |

## 推荐工作流

1. **初始化**：用 `brain.ingest_items` 或 `personal_workspace.organize` 沉淀品牌资料，`brain.confirm_initialization` 完成内容大脑初始化。
2. **选题**：普通内容与情景短剧都由 Agent 在端侧完成研究和候选规划；用户给出具体话题时可直接按本次输入形成临时选题上下文，不要求先初始化内容大脑或内容成员。需要沉淀到选题池时，拿到候选后必须先展示给用户，等用户明确选中一条，再用 `topic.proposals(action=submit, confirmedByUser=true)` 只保存这一条，随后用 `work_context.select_topic` 记录当前选题。`topic.research_task` 只是读取规划上下文，不能视为入池授权。远程 MCP 不提供云端选题生成工具。
3. **文案**：Agent 在端侧完成文案创作，用 `script.save` 同步保存候选，确认后用 `script.finalize` 定稿；需要修改时由 Agent 重写并用 `script.update` 保存，`script.feedback` 只保存问题过程数据。以上写操作均不调用云端模型或云端反馈分析。
4. **产出**：根据内容需要调用 `image.generate_all`（配图）、`podcast.generate_audio`（双人播客）、`voice.generate`（单人口播语音）、`resource.query(resource=voice)`（查询文案已有音频）、`video_packaging.create`（封装）。需要制作多人情景短剧时，默认由端侧 Agent直接规划选题，不先查询历史选题池；用户确认最终一个选题后，通过 `topic.proposals(action=submit)` 自动沉淀到选题池，再使用返回的 `topicId` 调用 `drama.plan`。只有用户明确要求使用已有选题时才查询选题池第一页，未经要求不得翻页。首次或明确要求极速体验时，用 `drama.plan context` 返回的 `firstExperienceSelection` 输出紧凑套装表格和统一的 `preview.url`，让用户在免登录只读 H5 查看角色图、参考声音和场景后回到 Agent 按编号选择；不要在对话中展开大图或原始媒体 URL。剧本确认时为每句台词填写物理化 `performanceDirection`、每段最多填写一个 `soundCue`；短剧时长由服务端按有效口播内容和默认 6 字/秒统一计算，Agent 不猜测或填写预估秒数，只有不能与对白重叠的明确静默或关键动作才额外计时。遇到多音字、专业术语、数字或英文混排时，保留原 `text`，优先复用 `drama.plan context` 返回的全局已验证读音词条，在 `spokenText` 中使用 `分红(fēn hóng)` 这类简短内联拼音，或换成无歧义同义口语。生成后发现新错音时，先向用户展示原词、朗读写法和验证说明，获得用户明确确认后用 `drama.plan pronunciation_save` 保存为系统级 active 词条；未确认不得保存。短剧角色、声音和场景按完整独立套装复用，禁止跨套装拆借；存在套装时，调用 `drama.asset set_library` 并传入已确认剧本的 `visualMode`，再用「选项｜视觉模式｜角色｜场景｜预览」表格展示候选，末尾加上“新建一套”。最新套装只是推荐，不得默认绑定；即使只有一套也要等用户明确选择。用户单独查询已有角色/场景资产时，`drama.asset set_library` 返回 `assetSets` 和 `preview`，必须同时发送资产表格与 `preview.url` 对应的免登录只读 H5；不要只发送 JSON、原始图片或声音地址。资产套装名称使用系统返回的稳定名称，不得取剧本第一句。生成结果立即保存为项目草稿，用户确认整套画面后系统立刻保存或更新本次套装，不等待完整成片。复用套装后要换单个角色或场景时先用 `drama.asset set_prepare_replace`，整套画面确认后更新原套装，不自动新建重复套装。全部首帧准备后用 `drama.frame review`，按返回的固定表格一次性展示对应剧本、情绪动作、景别运镜、构图描述和内联首帧图片。用户确认整套画面后调用 `drama.advance run` 并传 `visualsConfirmedByUser=true`，后续继续调用 `run` 自动完成片段生成、恢复轮询、片段确认和合成；当第一个片段已提交或完成时就先发送固定 `reviewUrl`，H5 会自动刷新并逐段展示已完成视频，不能等全部片段或成片。不要向用户展示底层任务、报价或 Provider。首帧不满意用 `drama.frame revise`，视频片段存在内容或画面错误时用 `drama.video regenerate`；成片封面不满意时先用 `drama.advance status` 读取当前 `cover.jobId`，再调用 `run` 并传 `retryKind=cover`、`retryCoverJobId` 和可选 `coverFeedback`，只重做封面并自动重合成；如果仅语速偏慢，复用原片并通过 `drama.advance run` 传 `bodyPlaybackRate=1.25` 重新合成，不要重新生成。片尾默认读取租户偏好，也允许本次明确关闭或指定其他租户内 MP4。供应商提交不确定时停止并核对原任务，禁止盲目重提。
5. **发布**：用 `video_publish.create_delivery` 投递前，确认目标平台、账号和用户意图，避免未经确认执行外部发布。

## 调用约定

- 生成类工具（`*_generate` / `*_create`）优先使用 `wait=true`；返回超时表示任务仍在执行，用对应的状态查询工具（`production.task_status` / `image.generation_status` / `podcast.generation_status`）按 `retryAfterMs` 轮询，不要编造进度。
- 每个工具的具体参数以 MCP 返回的 schema 为准。
- 多账号场景：先通过 `system.status` 确认当前租户，所有内容操作都在当前租户隔离范围内进行。

## 常见问题

- **返回无权限**：先调用 `system.status` 确认当前租户和角色，再检查目标资源是否属于当前租户。
- **任务处理中**：使用对应的状态查询工具轮询，避免重复创建任务和重复计费。
- **认证过期**：OAuth 过期会提示重新授权；`ca_live_` Key 过期需重新获取，不要编造新的 Key。
- **发布失败**：检查目标平台账号是否已授权、内容是否符合平台规范，再重新提交。
