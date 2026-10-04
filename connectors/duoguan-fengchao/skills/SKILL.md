---
name: duoguan-fengchao
description: 夺冠蜂巢（duoguan-fengchao）AI 自媒体内容生产。当用户需要热点选题、口播/图文文案、配图、配音、播客、视频封装、多账号内容运营或发布准备时使用本连接器。连接后先调用 system.health 和 account.context 确认服务与身份。
version: 1.0.0
author: 夺冠蜂巢
---

# 夺冠蜂巢（Duoguan Fengchao）

夺冠蜂巢是面向自媒体团队和内容创作者的 AI 内容生产平台，通过 MCP 工具覆盖从资料沉淀到发布准备的完整链路。

## 连接与认证

- 本连接器使用 OAuth（OAuth 2.1 + PKCE）认证，由 WorkBuddy 自动完成授权，无需手动配置凭证。
- 兼容历史 `ca_live_` API Key 认证方式。
- 连接后先调用 `system.health` 和 `account.context`，确认服务可用、身份与租户正确，再开始内容生产。
- OAuth 授权过期时 WorkBuddy 会提示重新授权；`ca_live_` Key 过期需在第三方平台重新获取。

## 配套 Skill

连接成功后，引导用户安装 4 个配套 Skill。它们负责内容生产的流程编排与用户引导，与连接器的 MCP 工具配合使用：

| Skill | 职责 |
|---|---|
| `duoguan-fengchao-brain-onboarding` | 内容大脑初始化：从官网/PDF/Word/资料夹提炼业务知识、获取确认并写入大脑档案 |
| `duoguan-fengchao-content-production` | 内容生产：选题、口播/图文文案、配图、反馈修订与定稿 |
| `duoguan-fengchao-media-production` | 音视频生产：播客音频/视频、真人录制、视频封装与交付 |
| `duoguan-fengchao-style-assets` | 风格与资料：开头钩子、文案/图片风格、热点资料的提炼与保存 |

安装渠道与具体安装方式由 Agent 按当前环境处理（如官网下载导入、技能市场安装等）；安装完成后按对应 Skill 的流程编排执行，本连接器只负责提供 MCP 工具。

## 核心工具分组

| 分组 | 工具前缀 | 用途 |
|------|------|------|
| 系统与身份 | `system.*` / `account.*` / `auth.*` | 健康检查、系统配置、身份与租户、短信登录 |
| 内容大脑 | `brain.*` | 品牌画像、业务方向、资料初始化与建议采纳 |
| 品牌画像 | `brand_profile.*` | 品牌资料提取、查询与更新 |
| 内容成员 | `member.*` | 多账号成员入驻与画像草稿 |
| 个人工作区 | `personal_workspace.*` | 个人素材整理、确认与删除 |
| 工作上下文 | `work_context.*` | 当前选题、候选内容、录制素材的选中 |
| 选题 | `topic.*` / `hotspot.*` | 热点研究、选题生成、提案提交与审核 |
| 文案 | `script.*` | 口播/图文文案生成、更新、反馈与定稿 |
| 风格资产 | `opening_hook.*` / `content_style.*` / `visual_style.*` | 钩子、文案风格、视觉风格的创建与管理 |
| 配图 | `image.*` | 小红书/图文配图生成与状态查询 |
| 媒体素材 | `media_asset.*` / `recording.*` | 素材上传、参考图注册、字幕状态、录制 |
| 音视频 | `podcast.*` / `video_packaging.*` | 播客音频、播客视频、视频封装 |
| 生产任务 | `production.*` | 异步任务列表与状态查询 |
| 发布 | `video_publish.*` | 多平台发布投递 |
| 内容诊断与预览 | `content_diagnosis.*` / `content_preview.*` | 内容诊断与发布前预览 |
| 运营资源 | `knowledge.*` / `resource.*` / `style.*` / `team.*` | 周方向沉淀、资源查询、样式管理、团队邀请 |

## 推荐工作流

1. **初始化**：用 `brain.ingest_items` 或 `personal_workspace.organize` 沉淀品牌资料，`brain.confirm_initialization` 完成内容大脑初始化。
2. **选题**：用 `topic.generate` 生成选题，`hotspot.submit_agent_research` 提交热点研究，再用 `work_context.select_topic` 记录当前选题。
3. **文案**：用 `script.generate` 生成文案，确认后用 `script.finalize` 定稿；需要修改时用 `script.update`，不满意可 `script.feedback` 反馈。
4. **产出**：根据内容需要调用 `image.generate_all`（配图）、`podcast.generate_audio`（播客）、`video_packaging.create`（封装）。
5. **发布**：用 `video_publish.create_delivery` 投递前，确认目标平台、账号和用户意图，避免未经确认执行外部发布。

## 调用约定

- 生成类工具（`*_generate` / `*_create`）优先使用 `wait=true`；返回超时表示任务仍在执行，用对应的状态查询工具（`production.task_status` / `image.generation_status` / `podcast.generation_status`）按 `retryAfterMs` 轮询，不要编造进度。
- 每个工具的具体参数以 MCP 返回的 schema 为准。
- 多账号场景：先通过 `account.context` 确认当前租户，所有内容操作都在当前租户隔离范围内进行。

## 常见问题

- **返回无权限**：先调用 `account.context` 确认当前租户和角色，再检查目标资源是否属于当前租户。
- **任务处理中**：使用对应的状态查询工具轮询，避免重复创建任务和重复计费。
- **认证过期**：OAuth 过期会提示重新授权；`ca_live_` Key 过期需重新获取，不要编造新的 Key。
- **发布失败**：检查目标平台账号是否已授权、内容是否符合平台规范，再重新提交。
