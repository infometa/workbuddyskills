<!-- 由 scripts/sync-skill-reference.mjs 自动生成，请勿手工编辑。 -->
<!-- 唯一内容来源：src/mcp/tools/*.tool.ts（由 loadToolDefinitions 汇总） -->
<!-- 重新生成：npm run sync:skill -->

# MCP Tool 参考

本文件列出连接器当前注册的全部 77 个 Tool 及其参数，用于在对话中确认该调哪个 Tool、怎么传参。

> **诊断类请求除外。** 生成 GEO 诊断报告前必须先调用 `geo_brand_diagnosis_report` 取回服务端维护的最新交付规范（章节结构、逐章取数口径、合规红线），不要凭本文件或记忆自行组织章节。

有副作用的 Tool（新增、修改、删除、启停、发布）执行前必须先向用户说明影响并取得确认；
标记为必须 `confirm: true` 的删除类动作，缺少该参数会被服务端拒绝。

## 工具索引

| Tool | 用途 |
| --- | --- |
| `account_balance` | 查询算力余额与明细 |
| `article_library_category_get` | 获取文章库分类详情 |
| `article_library_category_list` | 查询文章库分类 |
| `article_library_list` | 查询文章库列表 |
| `brand_diagnosis_get` | 获取品牌诊断结果 |
| `brand_mention_competitor` | 查询品牌竞品指标 |
| `brand_mention_source_list` | 查询品牌引用信源明细 |
| `brand_mention_sources` | 查询品牌引用信源统计 |
| `brand_mention_statistics` | 查询品牌提及统计 |
| `brand_monitor_list` | 查询品牌监控列表 |
| `brand_monitor_manage` | 管理品牌监控与诊断 |
| `brand_monitor_statistics` | 查询品牌监控统计 |
| `client_pair` | 绑定发布助手客户端 |
| `content_manage` | 管理 GEO 内容资产 |
| `creation_manage` | 管理 GEO 创作任务 |
| `creation_task_get` | 获取创作任务详情 |
| `creation_task_list` | 查询创作任务 |
| `external_hub_catalog` | 读取客户端能力目录 |
| `external_hub_execute` | 调用客户端能力 |
| `geo_brand_diagnosis_report` | GEO 诊断报告交付规范 |
| `geo_content_get` | 获取 GEO 文章详情 |
| `geo_content_search` | 搜索 GEO 文章 |
| `geo_overview_get` | 查询 GEO 监控总览 |
| `geo_reference_list` | 分页查询引用信源 |
| `geo_reference_overview` | 查询引用信源概览 |
| `graphic_douyin_schema` | 生成抖音投稿 Schema |
| `graphic_layout_confirm` | 确认长文排版 |
| `graphic_layout_get` | 读取公开长文排版 |
| `graphic_library_category_list` | 查询图文库分类 |
| `graphic_library_list` | 查询图文库列表 |
| `graphic_reference_upload` | 上传临时参考图 |
| `graphic_task_get` | 获取生图任务详情 |
| `graphic_task_list` | 查询生图任务 |
| `image_library_upload` | 上传图片到图片库 |
| `instruction_all` | 查询全部指令 |
| `instruction_get` | 获取指令详情 |
| `instruction_list` | 查询指令库 |
| `instruction_manage` | 管理 GEO 指令 |
| `instruction_market_list` | 查询指令市场 |
| `keyword_main_get` | 获取 GEO 主词详情 |
| `keyword_main_list` | 查询 GEO 主词 |
| `keyword_manage` | 管理 GEO 蒸馏词 |
| `keyword_target_get` | 获取 GEO 问题词详情 |
| `keyword_target_list` | 查询 GEO 问题词 |
| `material_category_all` | 获取全部素材分类 |
| `material_category_get` | 获取素材分类详情 |
| `material_category_list` | 查询素材库分类 |
| `material_library_list` | 查询素材库列表 |
| `oral_audio_get` | 获取口播音频详情 |
| `oral_list` | 查询口播任务与内容 |
| `oral_script_get` | 获取口播文案详情 |
| `oral_script_task_get` | 获取口播文案任务 |
| `oral_video_get` | 获取口播视频详情 |
| `publication_article_list` | 查询待发布文章 |
| `publication_manage` | 管理 GEO 发布任务 |
| `publication_media_list` | 查询媒体列表 |
| `publication_pending_scheduled` | 查询待执行定时批次 |
| `publication_record_list` | 查询发布记录 |
| `publication_task_cache` | 查询最近发布任务配置 |
| `publication_task_get` | 获取发布任务详情 |
| `publication_task_list` | 查询发布任务 |
| `site_agreement_get` | 获取网站协议 |
| `site_copyright_get` | 获取网站备案信息 |
| `site_footer_get` | 获取底部导航详情 |
| `site_footer_list` | 查询底部导航 |
| `site_manage` | 管理网站与模板 |
| `site_page_list` | 查询网站页面 |
| `site_project_list` | 查询网站项目 |
| `site_system_config_get` | 获取网站公共配置 |
| `site_template_common_pages` | 查询模板公共页面 |
| `site_template_get` | 获取模板详情 |
| `site_template_list` | 查询模板列表 |
| `site_template_pages` | 查询模板页面 |
| `site_website_get` | 获取网站信息 |
| `tenant_account_balance` | 查询账户余额（非算力） |
| `tenant_config_get` | 获取租户配置 |
| `tenant_profile_get` | 获取当前租户信息 |

## 参数详情

### `account_balance` — 查询算力余额与明细

查询当前租户的算力余额或消耗明细。明细支持分页、类型和渠道筛选。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `balance` \| `list` | 是 |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `type` | string | 否 |
| `channel` | string | 否 |

### `article_library_category_get` — 获取文章库分类详情

按分类 ID 获取文章库或图文库分类详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `article_library_category_list` — 查询文章库分类

分页查询文章库分类及文章数量。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `isShow` | `0` \| `1` | 否 |

### `article_library_list` — 查询文章库列表

按标题、分类、显示状态和发布状态分页查询文章库内容。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `title` | string | 否 |
| `categoryId` | integer | 否 |
| `isShow` | `0` \| `1` | 否 |
| `publishStatus` | string | 否 |
| `sourceArticleId` | integer | 否 |

### `brand_diagnosis_get` — 获取品牌诊断结果

按诊断任务标识查询品牌诊断结果。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `taskId` | string \| integer | 是 |

### `brand_mention_competitor` — 查询品牌竞品指标

按监控批次查询品牌与竞品指标。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `batchNo` | string | 是 |

### `brand_mention_source_list` — 查询品牌引用信源明细

按监控批次分页查询引用信源明细。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `batchNo` | string | 是 |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `brand_mention_sources` — 查询品牌引用信源统计

按监控批次查询品牌引用信源统计。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `batchNo` | string | 是 |

### `brand_mention_statistics` — 查询品牌提及统计

按监控批次查询品牌提及率和引用佐证统计。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `batchNo` | string | 是 |

### `brand_monitor_list` — 查询品牌监控列表

分页查询 GEO 数据监控结果。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `mainWordId` | string \| integer | 否 |

### `brand_monitor_manage` — 管理品牌监控与诊断

维护问题词监控、提交品牌诊断和管理品牌公司。删除品牌或问题词必须提供 confirm: true；诊断接口返回异步任务结果。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `question_add` \| `question_edit` \| `question_delete` \| `diagnosis_create` \| `diagnosis_submit` \| `company_create` \| `company_delete` | 是 |
| `id` | string \| integer | 否 |
| `companyId` | string \| integer | 否 |
| `mainWordId` | string \| integer | 否 |
| `question` | string | 否 |
| `questions` | array<string> | 否 |
| `brandName` | string | 否 |
| `platforms` | array<string> | 否 |
| `companyName` | string | 否 |
| `address` | string | 否 |
| `industry` | string | 否 |
| `mainBusiness` | string | 否 |
| `companyIntro` | string | 否 |
| `status` | string | 否 |
| `confirm` | `true` | 否 |

### `brand_monitor_statistics` — 查询品牌监控统计

查询 GEO 数据监控统计结果。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `companyId` | integer | 否 |
| `batchNo` | string | 否 |
| `startDate` | string | 否 |
| `endDate` | string | 否 |

### `client_pair` — 绑定发布助手客户端

输入发布助手客户端显示的配对码，将当前 WorkBuddy 授权租户的 API Key 安全下发并保存到该客户端。切换到新租户时可再次调用。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pairingCode` | string | 是 |

### `content_manage` — 管理 GEO 内容资产

新增、编辑、启停或删除 GEO 文章栏目、文章和图片库记录。删除动作必须提供 confirm: true；请求字段仅映射到固定上游接口。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `article_category_add` \| `article_category_edit` \| `article_category_status` \| `article_category_delete` \| `article_add` \| `article_edit` \| `article_status` \| `article_delete` \| `article_publish` \| `image_category_add` \| `image_category_edit` \| `image_category_delete` \| `image_delete` | 是 |
| `id` | string \| integer | 否 |
| `categoryId` | string \| integer | 否 |
| `contentType` | `article` \| `graphic` | 否 |
| `type` | `10` \| `20` \| `30` \| `40` | 否 |
| `imageUrls` | array<string> | 否 |
| `uri` | string | 否 |
| `ids` | array<string \| integer> | 否 |
| `name` | string | 否 |
| `title` | string | 否 |
| `abstract` | string | 否 |
| `content` | string | 否 |
| `sort` | integer | 否 |
| `isShow` | `0` \| `1` | 否 |
| `status` | string \| integer | 否 |
| `publishUrl` | string | 否 |
| `publishPlatform` | string | 否 |
| `publishAccount` | string | 否 |
| `confirm` | `true` | 否 |

### `creation_manage` — 管理 GEO 创作任务

创建、编辑、取消和删除创作任务，并提交口播文案、音频、视频和生图任务。生成任务可能扣除算力；删除、取消和重试动作必须提供 confirm: true。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `task_add` \| `task_edit` \| `task_delete` \| `task_cancel` \| `oral_generate` \| `oral_add` \| `oral_edit` \| `oral_delete` \| `audio_generate` \| `audio_delete` \| `audio_retry` \| `video_generate` \| `video_delete` \| `video_retry` \| `graphic_add` \| `graphic_delete` | 是 |
| `id` | string \| integer | 否 |
| `taskId` | string \| integer | 否 |
| `libraryId` | string \| integer | 否 |
| `librarySource` | `tenant` \| `public` | 否 |
| `cateId` | integer | 否 |
| `imgCateId` | integer | 否 |
| `imageMode` | `library` \| `ai` | 否 |
| `imageNumber` | integer | 否 |
| `imageSize` | string | 否 |
| `imageModelVersion` | `v1` \| `v2` | 否 |
| `number` | integer | 否 |
| `executeMode` | `immediate` \| `scheduled` | 否 |
| `scheduleTimes` | array<string> | 否 |
| `scheduleIds` | array<integer> | 否 |
| `articleIds` | array<string \| integer> | 否 |
| `name` | string | 否 |
| `title` | string | 否 |
| `content` | string | 否 |
| `generateCount` | integer | 否 |
| `oralId` | integer | 否 |
| `voiceId` | integer | 否 |
| `audioId` | string \| integer | 否 |
| `styleId` | string | 否 |
| `styleSnapshot` | object \| array<unknown> | 否 |
| `profile` | `3:4` \| `4:3` \| `1:1` \| `9:16` \| `16:9` | 否 |
| `width` | integer | 否 |
| `height` | integer | 否 |
| `prompt` | string | 否 |
| `cid` | integer | 否 |
| `articleId` | integer | 否 |
| `images` | array<unknown> | 否 |
| `modelVersion` | `v1` \| `v2` | 否 |
| `size` | string | 否 |
| `confirm` | `true` | 否 |

### `creation_task_get` — 获取创作任务详情

按任务 ID 查询创作任务详情和结果摘要。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `creation_task_list` — 查询创作任务

分页查询当前租户的 GEO 创作任务。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `external_hub_catalog` — 读取客户端能力目录

读取本机「AI智能发布助手」客户端当前发布的实时能力目录。当用户提出客户端侧操作时，先调用本工具获取语义工具名与对应 command，再立即调用 external_hub_execute 执行；不要凭记忆猜测 command。

典型说法（用户口语，不限于此）：
- 账号：绑定了哪些账号 / 账号列表 / 哪个号掉线了 / 登录状态 / 重新登录 / 账号授权 / 授权到哪一步了 / 这个号还能不能发
- 检索账号：绑定了哪些检索账号 / 豆包账号 / deepseek 账号 / 检索账号掉线了
- AI 检索：执行一次检索 / 帮我搜一下某个词 / 用某个平台查这个关键词 / 批量检索 / 检索任务跑完没 / 停止检索 / 检索记录
- 发布：发布模式 / 静默发布 / 发布任务列表 / 任务跑到哪了 / 发布日志 / 取消计划发布 / 暂停发布 / 执行远程发布任务

无入参。

### `external_hub_execute` — 调用客户端能力

按 external_hub_catalog 返回的定义执行本机「AI智能发布助手」客户端能力。command 必须直接取自目录项的 hub.command，业务字段放在 params，租户认证上下文放在 auth。若尚未获取目录，先调用 external_hub_catalog；不要自行编造 command。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `command` | string | 是 | 从 external_hub_catalog 对应语义工具项读取的 command |
| `params` | object | 是 | 目标能力的业务参数 |
| `auth` | object | 否 | 租户认证上下文，例如 ownerUserId、ownerAccountName、apiKey、apiBaseUrl |

### `geo_brand_diagnosis_report` — GEO 诊断报告交付规范

生成 GEO 诊断报告 / AI 搜索表现分析 / AI 可见性排查 / AI 推荐情况分析 / 品牌 AI 搜索诊断 / 整改方案之前，必须先调用本工具获取服务端维护的最新交付规范（报告章节结构、执行顺序、逐章取数口径、合规红线），再严格按该规范生成，不得自行设计章节。用户说“帮我生成一个 XXX 的 GEO 诊断报告”“XXX 在 AI 里的表现怎么样”“分析下 XXX 在豆包、DeepSeek 里的曝光和推荐情况”时即调用。返回内容与 MCP Prompt `geo_brand_diagnosis` 同源，始终为服务端当前最新版本。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `brand_name` | string | 否 | 需要诊断的对外品牌名；已在对话中明确时可省略 |
| `additional_context` | string | 否 | 可选补充资料，例如行业、城市、工商主体、竞品、关键词或上期报告摘要 |

### `geo_content_get` — 获取 GEO 文章详情

按文章 ID 获取 GEO 文章完整详情，包括正文、封面和发布状态。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `geo_content_search` — 搜索 GEO 文章

按标题、栏目和显示状态分页查询当前租户的 GEO 文章。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `title` | string | 否 |
| `categoryId` | integer | 否 |
| `isShow` | `0` \| `1` | 否 |

### `geo_overview_get` — 查询 GEO 监控总览

查询当前租户的 GEO 综合评分、优化机会、平台表现或竞品对比。只读操作；需要指定批次时请提供 batchNo。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `companyId` | integer | 否 |
| `batchNo` | string | 否 |
| `startDate` | string | 否 |
| `endDate` | string | 否 |
| `action` | `score` \| `opportunities` \| `platforms` \| `competitor` | 是 |

### `geo_reference_list` — 分页查询引用信源

分页查询 GEO 引用信源域名明细，可按引用文章标题筛选。默认返回第一页，单页最多 50 条。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `companyId` | integer | 否 |
| `startDate` | string | 否 |
| `endDate` | string | 否 |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `title` | string | 否 |

### `geo_reference_overview` — 查询引用信源概览

查询 GEO 引用信源数量、引用趋势、TOP 信源和信源类型分布。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `companyId` | integer | 否 |
| `startDate` | string | 否 |
| `endDate` | string | 否 |

### `graphic_douyin_schema` — 生成抖音投稿 Schema

根据长文排版短码生成抖音投稿 Schema，成功回调后可能扣除发布任务算力。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `shareToken` | string | 是 |
| `confirm` | `true` | 是 |

### `graphic_layout_confirm` — 确认长文排版

确认文章长文排版并获取固定短链；可能保存素材并扣除算力，必须提供 confirm: true 和幂等 requestId。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `articleId` | integer | 是 |
| `categoryId` | integer | 是 |
| `title` | string | 是 |
| `abstract` | string | 否 |
| `fileIds` | array<integer> | 是 |
| `requestId` | string | 是 |
| `confirm` | `true` | 是 |

### `graphic_layout_get` — 读取公开长文排版

根据十位短码读取公开长文排版数据。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `shareToken` | string | 是 |

### `graphic_library_category_list` — 查询图文库分类

分页查询图文库分类及作品数量。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `isShow` | `0` \| `1` | 否 |

### `graphic_library_list` — 查询图文库列表

按标题、分类、显示状态和发布状态分页查询图文库作品。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `title` | string | 否 |
| `categoryId` | integer | 否 |
| `isShow` | `0` \| `1` | 否 |
| `publishStatus` | string | 否 |
| `sourceArticleId` | integer | 否 |

### `graphic_reference_upload` — 上传临时参考图

上传 AI 生图任务的临时参考图，不写入正式图片库。最大 20 MiB。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `fileBase64` | string | 是 |
| `fileName` | string | 是 |
| `mimeType` | `image/jpeg` \| `image/png` \| `image/webp` \| `image/gif` | 是 |

### `graphic_task_get` — 获取生图任务详情

按任务 ID 查询生图状态和生成素材。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `graphic_task_list` — 查询生图任务

分页查询当前租户的 AI 生图任务。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `image_library_upload` — 上传图片到图片库

将图片上传到指定 GEO 图片库。文件以 Base64 传入，支持 JPEG、PNG、WebP、GIF，最大 20 MiB。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `fileBase64` | string | 是 |
| `fileName` | string | 是 |
| `mimeType` | `image/jpeg` \| `image/png` \| `image/webp` \| `image/gif` | 是 |
| `categoryId` | string \| integer | 是 |

### `instruction_all` — 查询全部指令

查询当前租户全部可用指令。

无入参。

### `instruction_get` — 获取指令详情

按指令 ID 查询指令详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `instruction_list` — 查询指令库

分页查询当前租户的 GEO 指令，可按名称筛选。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `name` | string | 否 |

### `instruction_manage` — 管理 GEO 指令

创建、编辑、启停、删除、预览和复用 GEO 指令。删除或复用市场指令等改变数据的动作需要 confirm: true。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `add` \| `edit` \| `status` \| `delete` \| `chat` \| `use_market` \| `ai_generate` | 是 |
| `id` | string \| integer | 否 |
| `name` | string | 否 |
| `systemPrompt` | string | 否 |
| `modelName` | string | 否 |
| `model` | string | 否 |
| `isShow` | `0` \| `1` | 否 |
| `sort` | integer | 否 |
| `categoryId` | string \| integer | 否 |
| `publicLibraryId` | string \| integer | 否 |
| `companyIntro` | string | 否 |
| `description` | string | 否 |
| `articleWordsNumber` | string | 否 |
| `rivalDesc` | string | 否 |
| `mainWordId` | integer | 否 |
| `knowledgeId` | string \| integer | 否 |
| `knowledgeIds` | array<string \| integer> | 否 |
| `targetWords` | array<string> | 否 |
| `questionIds` | array<integer> | 否 |
| `instructionName` | string | 否 |
| `finalPrompt` | string | 否 |
| `type` | string | 否 |
| `libraryId` | string \| integer | 否 |
| `confirm` | `true` | 否 |

### `instruction_market_list` — 查询指令市场

分页查询系统指令市场，可按名称和行业分类筛选。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `name` | string | 否 |
| `categoryId` | string \| integer | 否 |

### `keyword_main_get` — 获取 GEO 主词详情

按主词 ID 查询 GEO 蒸馏主词详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `keyword_main_list` — 查询 GEO 主词

查询当前租户全部 GEO 蒸馏主词。

无入参。

### `keyword_manage` — 管理 GEO 蒸馏词

创建、编辑、启停、导入和异步生成 GEO 主词与问题词。删除动作必须提供 confirm: true；异步生成成功仅表示任务已提交。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `main_edit` \| `main_status` \| `main_delete` \| `main_ai_add` \| `target_add` \| `target_edit` \| `target_status` \| `target_delete` \| `target_import` \| `target_continue_ai` \| `target_toggle_open` | 是 |
| `id` | string \| integer | 否 |
| `mainId` | string \| integer | 否 |
| `ids` | array<string \| integer> | 否 |
| `isAll` | `0` \| `1` \| boolean | 否 |
| `name` | string | 否 |
| `words` | string | 否 |
| `number` | integer | 是 |
| `targetName` | string | 否 |
| `weight` | integer | 否 |
| `is_show` | `0` \| `1` | 是 |
| `useAdjPfx` | `0` \| `1` \| boolean | 否 |
| `useSynSfx` | `0` \| `1` \| boolean | 否 |
| `useRecSfx` | `0` \| `1` \| boolean | 否 |
| `useQrySfx` | `0` \| `1` \| boolean | 否 |
| `useRegPfx` | `0` \| `1` \| boolean | 否 |
| `status` | string \| integer | 否 |
| `keywords` | array<string> | 否 |
| `confirm` | `true` | 否 |

### `keyword_target_get` — 获取 GEO 问题词详情

按问题词 ID 查询问题词详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `keyword_target_list` — 查询 GEO 问题词

分页查询当前租户的问题词，可按名称和主词筛选。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `name` | string | 否 |
| `mainId` | string \| integer | 否 |

### `material_category_all` — 获取全部素材分类

按素材类型获取全部素材分类，不分页。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `type` | `10` \| `20` \| `30` \| `40` | 是 |

### `material_category_get` — 获取素材分类详情

按分类 ID 获取素材分类详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `material_category_list` — 查询素材库分类

分页查询素材库分类，默认查询图片分类 type=10。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `type` | `10` | 是 |
| `name` | string | 否 |

### `material_library_list` — 查询素材库列表

按素材分类、类型和名称分页查询当前租户可见素材。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `categoryId` | integer | 否 |
| `type` | `10` \| `20` \| `30` \| `40` | 否 |
| `name` | string | 否 |

### `oral_audio_get` — 获取口播音频详情

按音频记录 ID 查询生成状态和地址。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `oral_list` — 查询口播任务与内容

按 type 查询口播文案任务、文案、音频或视频列表。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `type` | `script_task` \| `script` \| `audio` \| `video` | 是 |

### `oral_script_get` — 获取口播文案详情

按文案 ID 查询口播文案正文和媒体统计。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `oral_script_task_get` — 获取口播文案任务

按任务 ID 查询口播文案生成结果。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `oral_video_get` — 获取口播视频详情

按视频记录 ID 查询合成状态和视频地址。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `publication_article_list` — 查询待发布文章

查询指定发布任务或发布批次的待发布文章。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `taskId` | string \| integer | 否 |
| `batchId` | string \| integer | 否 |

### `publication_manage` — 管理 GEO 发布任务

创建、编辑、暂停、启动和重试发布任务，并同步发布记录。真实发布、删除和重试动作必须提供 confirm: true。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `media_export` \| `task_add` \| `task_edit` \| `task_delete` \| `task_start` \| `task_pause` \| `client_start` \| `client_pause` \| `record_retry` \| `record_status` \| `record_add` \| `record_delete` | 是 |
| `id` | string \| integer | 否 |
| `taskId` | string \| integer | 否 |
| `recordId` | string \| integer | 否 |
| `platform` | string | 否 |
| `name` | string | 否 |
| `categoryId` | integer | 否 |
| `accounts` | array<unknown> | 否 |
| `articleType` | `default` \| `fixed` | 否 |
| `articleNumber` | integer | 否 |
| `articleIds` | array<string \| integer> | 否 |
| `delay` | integer | 否 |
| `publishMode` | `immediate` \| `scheduled` | 否 |
| `scheduleType` | `once` \| `day` \| `weekly` \| `workday` \| `customize` | 否 |
| `scheduleDatetimes` | array<string> | 否 |
| `batchId` | string \| integer | 否 |
| `articleId` | string \| integer | 否 |
| `screenImg` | string | 否 |
| `errMsg` | string | 否 |
| `options` | object | 否 |
| `status` | `waiting` \| `processing` \| `success` \| `failed` | 否 |
| `mediaType` | `news` \| `wemedia` | 否 |
| `filters` | object | 否 |
| `sort` | string | 否 |
| `fileName` | string | 否 |
| `selectIds` | array<string \| integer> | 否 |
| `error` | string | 否 |
| `screenshot` | string | 否 |
| `confirm` | `true` | 否 |

### `publication_media_list` — 查询媒体列表

按媒体类型、筛选条件和分页查询可发布媒体；媒体列表最多每页 100 条。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `mediaType` | `news` \| `wemedia` | 是 |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `sort` | string | 否 |
| `filters` | object | 否 |

### `publication_pending_scheduled` — 查询待执行定时批次

查询 Self 平台待执行的定时发布批次。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `publication_record_list` — 查询发布记录

分页查询文章发布结果、目标平台和失败原因。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `publication_task_cache` — 查询最近发布任务配置

按平台查询最近一条发布任务配置。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `platform` | string | 否 |

### `publication_task_get` — 获取发布任务详情

按发布任务 ID 查询任务配置、平台和调度信息。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `publication_task_list` — 查询发布任务

分页查询发布主任务及成功失败统计。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_agreement_get` — 获取网站协议

查询当前租户的网站政策与协议信息。

无入参。

### `site_copyright_get` — 获取网站备案信息

查询当前租户的网站备案信息。

无入参。

### `site_footer_get` — 获取底部导航详情

按导航 ID 查询底部导航详情。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string \| integer | 是 |

### `site_footer_list` — 查询底部导航

分页查询网站底部导航。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_manage` — 管理网站与模板

修改网站设置、页面、模板和底部导航。重置、删除和启用模板等动作必须提供 confirm: true。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `action` | `website_apply` \| `website_set` \| `copyright_set` \| `agreement_set` \| `project_create` \| `project_page_edit` \| `template_config_edit` \| `template_page_edit` \| `template_page_enabled` \| `template_reset_all` \| `template_page_reset` \| `template_create` \| `template_enabled` \| `template_delete` \| `template_custom_page_add` \| `footer_add` \| `footer_edit` \| `footer_status` \| `footer_delete` | 是 |
| `id` | string \| integer | 否 |
| `projectId` | string \| integer | 否 |
| `pageId` | string \| integer | 否 |
| `templateId` | string \| integer | 否 |
| `name` | string | 否 |
| `title` | string | 否 |
| `url` | string | 否 |
| `pageData` | object | 否 |
| `config` | object | 否 |
| `enabled` | `0` \| `1` | 否 |
| `content` | string | 否 |
| `confirm` | `true` | 否 |

### `site_page_list` — 查询网站页面

按项目查询网站页面列表。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |
| `projectId` | string \| integer | 否 |

### `site_project_list` — 查询网站项目

分页查询当前租户的网站模板项目。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_system_config_get` — 获取网站公共配置

查询网站模板编辑使用的公共配置。

无入参。

### `site_template_common_pages` — 查询模板公共页面

查询模板可用的公共页面。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_template_get` — 获取模板详情

查询当前启用模板的详细配置。

无入参。

### `site_template_list` — 查询模板列表

分页查询可用的网站模板。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_template_pages` — 查询模板页面

查询当前模板的页面配置列表。

| 参数 | 类型 | 必填 |
| --- | --- | --- |
| `pageNo` | integer | 是 |
| `pageSize` | integer | 是 |

### `site_website_get` — 获取网站信息

查询当前租户的网站基础信息。

无入参。

### `tenant_account_balance` — 查询账户余额（非算力）

查询当前租户通用账户余额，以及累计充值和累计消费金额；金额单位为元。

无入参。

### `tenant_config_get` — 获取租户配置

查询当前租户的公开业务配置。不会返回租户 API Key。

无入参。

### `tenant_profile_get` — 获取当前租户信息

查询当前 Bearer API Key 所属租户的信息。该操作只读，不会修改租户数据。

无入参。
