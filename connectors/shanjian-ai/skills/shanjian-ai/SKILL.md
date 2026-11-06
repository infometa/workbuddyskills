---
name: "shanjian-ai"
description: "使用闪剪AI连接器按游标逐页浏览素材标签并核对总数，浏览笔记与作品，查询剩余算力、个人和当前系统云空间、有效会员及到期时间，容量由连接器自动以 MB/GB 展示。支持创作报价、确认生成和作品管理；仅在对话内交互，禁止生成网页。用户提到闪剪创作、算力、云空间、会员、我的素材、笔记或作品时使用。"
description_zh: "通过闪剪账号授权，按服务端游标逐页浏览素材标签并核对总数，浏览笔记与作品，查询剩余算力、个人和当前系统云空间、有效会员及到期时间；容量自动以 MB/GB 展示，创作先报价、在对话内确认费用后生成，不创建交互网页。"
description_en: "Use Shanjian AI to browse material tag pages with server cursors and verify tag totals; view notes and works; check compute credits, personal and system cloud storage in MB/GB, and active membership expiry; quote and confirm content generation in chat; never create interaction web pages."
version: "0.2.8"
author: "Shanjian"
---

# 闪剪AI连接器使用说明

通过已授权的闪剪账号调用 `shanjian-ai` MCP 工具。支持的内容类型包括短视频、AI短剧、文章、图文、朋友圈、播客、音乐和图片；实际可用类型、模板及模型以工具返回为准。

## 交互边界：禁止生成页面

- **闪剪 MCP 交互只在当前对话内完成，禁止生成、保存或托管 HTML／网页。** 不使用其他工具创建本地页面、临时链接、演示站点、报价确认页、登录／验证码表单、作品展示页或仪表盘；用户要求页面展示时也遵守此限制。
- 报价、进度、权益和作品信息用普通文字、Markdown 表格及工具返回的媒体展示。保留正常的视频、图片、音频、文章等内容创作能力。
- 需要登录、授权或前往作品页面时，仅使用当前环境服务实际返回的官方前端链接；不拼接、猜测 URL，不把测试／灰度链接改成正式地址。成品媒体直链可原样交付，但不作为业务操作页面。
- **费用在对话内确认。** 展示本次最新报价，用户明确同意并选择 `wait`／`async` 后调用 `confirm_generation`；不创建按钮或网页代替确认，不提供自建网页兜底。
- 页面入口缺失、报价过期或接口失败时，说明原因并按工具指引在对话中处理；不能通过编写页面、索取验证码或模拟成功绕过问题。没有官方前端入口时明确告知暂不可用。

English: Never generate, save, or host web pages, HTML artifacts, login forms, quote confirmation pages, or dashboards for Shanjian MCP flows, including through other tools. Keep interaction and fee consent in chat; use only official frontend links actually returned by the current environment. Missing links or API failures must not be replaced with fabricated pages.

## 认证前置条件：服务端自带 OAuth

本连接器采用 WorkBuddy 官方文档中的「MCP Server 自带 OAuth」方式：**省略 `auth_mode`，无需 `token-schema.json`，无需用户手填 Token/API Key，也不在 `mcp.json` 中预置认证请求头。**

- MCP 地址：`https://mcp-connector.shanjian.tv/mcp`。
- `mcp.json` 中 `timeout: 180000` 的单位是**毫秒**，即 3 分钟；视频生成任务的整体进度通过 `get_operation` 分次查询。
- 用户在 WorkBuddy 连接器界面点击「连接／授权」。未携带凭证的请求返回 HTTP 401，通过 `WWW-Authenticate` 的 `resource_metadata` 发现授权服务。
- WorkBuddy 自动完成元数据发现、动态客户端注册、浏览器授权、授权码与 PKCE S256 交换，随后携带 Bearer Token 调用工具。
- 用户在闪剪授权页登录并批准权限，账号身份来自服务端校验后的 Token 和有效授权记录。「我的笔记」「我的作品」指当前授权账号可访问的数据。
- 登录、验证码及授权操作在闪剪授权页完成；不要要求用户在聊天里提供密码、验证码或 Token，不输出凭证内容。
- 授权失效时由 WorkBuddy 尝试刷新；仍失败时引导用户重新连接并授权。重新授权后若旧对话仍无工具，打开新对话再试。HTTP 503 表示依赖暂不可用，应稍后重试，不反复要求重新授权。

授权发现地址为 `/.well-known/oauth-protected-resource` 与 `/.well-known/oauth-authorization-server`；客户端按元数据访问 `/oauth/register`、`/oauth/authorize`、`/oauth/token`。这些流程由 WorkBuddy 管理，AI 不自行注册客户端、索取用户凭证或拼接 Token。

依据：[WorkBuddy 认证与凭证](https://open.workbuddy.cn/docs/connector#认证与凭证)、[MCP OAuth 流程](https://open.workbuddy.cn/docs/connector#mcp-oauth-流程)。

## 从需求到作品

1. 调用 `list_systems`，优先使用返回的 `selectedMtvSpaceId`，否则使用 `defaultMtvSpaceId`。若服务端自动初始化默认系统，告知用户实际选中的系统；没有默认值时展示可选系统，由用户选择后调用 `set_default_system`。用户要求切换时再更改默认系统。
2. 调用 `search_workflows(mtvSpaceId)` 获取工作流、智能体及首批模板。`workflowId`、`agentId`、`templateId` 等都从实际返回取值，展示可选项供用户挑选；需要更多选项时调用模板／模型工具。不要承诺未启用的工作流可用。
3. 补齐创作要求和参数后调用 `prepare_generation`；重做已有作品用 `recreate_work`。这两步返回报价，不执行付费生成。记录 `operationId`、所属 `mtvSpaceId`、`quote.version`、`quote.expiresAt`、费用说明及 `clientRequestId`。
4. 原样展示服务端报价和内容摘要，并询问用户是「等待结果」还是「提交后结束」。**只有用户在看到本次最新报价后明确同意，才能调用 `confirm_generation`**。最初提出生成需求、提前说「自动确认」或同意旧报价，都不能替代本次报价后的确认。
5. 确认时传 `operationId`、最新 `quoteVersion`、`confirm: true`、用户选择的 `waitMode`：`wait` 表示等待交付；`async` 表示提交后结束。用户未选择结果获取方式时先询问；未同意费用时不要提交。
6. `wait` 模式根据工具给出的 `retryAfterSeconds`／轮询指引查询 `get_operation`；`async` 模式告知已提交并保留操作编号，不主动继续轮询，用户之后询问时再查。成功后交付返回的成品链接或闪剪网页端作品入口，失败时说明原因与费用状态，不自行重新付费生成。

## 参数与 ID 规则

- 业务 ID 使用对应工具返回的完整 24 位十六进制字符串；不能用标题、序号或尾号代替。`operationId` 是生成操作 ID，`messageId` 是作品 ID，二者不可互换。
- `mtvSpaceId` 是闪剪系统空间；知识库的 `kbaseSpaceId`／`spaceId` 不是同一字段。查询旧操作时始终使用创建时所属的 `mtvSpaceId`。
- 可选 `mtvSpaceId` 不传时使用默认系统；工具声明必填时仍须显式传入。`agentId` 必须来自当前系统的 `search_workflows`，查作品时不可省略。
- `sid` 是服务端游标，只能原样使用上页返回的 `nextSid`；首页省略。支持 `pageSize` 的列表默认为 10，范围 1～10。
- 新生成需求创建唯一 `clientRequestId`，例如 `gen-` 加当前毫秒时间戳；重做使用 `re-` 前缀，长度 6～64 个字符。同一次未提交需求的重试复用该值。

### 创作输入

| 输入 | 类型／条件 | 使用方式 |
|---|---|---|
| `workflowId` | 字符串，显式填写 | 从 `search_workflows` 的可用目录选择；虽然服务端默认 article，不依赖默认值猜用户需求 |
| `input.text` | 必填字符串，1～5000 字符 | 创作主题／要求；固定时长短视频保留用户原意，由平台扩写，不擅自改成完整口播台词 |
| `input.duration` | 整数秒，3～1800；按工作流条件填写 | AI短剧需要；短视频／播客固定时长模式需要；模型具体时长档位以返回值为准 |
| `input.oralScriptMode` | 可选布尔，默认关闭 | 用户明确选择短视频／播客的台词模式时设 true，传完整台词并省略 duration，由平台换算时长 |
| `input.audioUrl` | 可选音频直链，仅短视频 | 同时传 duration=真实音频秒数；不得与 oralScriptMode 同用 |
| `input.templateId` | 可选 ID | 从 `list_templates` 取；省略使用默认模板／配音。播客也可使用 `list_public_voices` 返回的 `items[].id` |
| `input.modelId`、`input.percent` | 可选字符串 | 仅适用支持它们的工作流，取 `list_models` 的模型与比例选项，不编造 |
| `input.imageUrls` | 可选 HTTPS 直链数组，最多 9 张 | 短视频作为素材图，图片／AI短剧作为参考图；模型可能有更小的数量上限。其他工作流不传 |
| `input.contentTextId` | 可选笔记 ID | 用户选定 `list_notes` 的笔记后传入；`input.text` 仍填写创作要求 |
| `input.linkUrl` | 可选 HTTP/HTTPS URL | 短视频／图文／播客／文章／朋友圈支持；与 contentTextId、oralScriptMode 互斥 |
| `input.materialMatchV2` | 可选对象 | 短视频／音乐可用；素材范围来自 `list_materials`。网络素材／笔记素材开关沿用用户已存配置，只有用户明确要求并确认时才更改 |

可选标题、语速、音乐模式等参数按实时 MCP 工具 schema 使用。公共数字人浏览结果不能直接作为 `templateId`；需要先在闪剪 App 配置到模板，再选择实际模板。

## 工具目录

下表 `?` 表示可选；ID、游标和分页约束见上文。所有调用均使用当前授权身份。

| 工具 | 参数 | 返回／用途 |
|---|---|---|
| `list_systems` | 无 | `systems` 与默认／选中系统 |
| `get_account_rights` | `mtvSpaceId?` | 剩余算力、个人与当前系统云空间（自动 MB/GB）、当前会员类型与到期时间；需要 account:read |
| `set_default_system` | `mtvSpaceId` | 设置用户指定的默认系统 |
| `search_workflows` | `mtvSpaceId, query?` | 可用 `workflows`、`agents` 及首批模板 |
| `list_templates` | `workflowId, mtvSpaceId?, agentId?, sid?` | `templates[].templateId`、模板／配音与 `nextSid` |
| `list_models` | `workflowId`，限 aiShortFlim/picture/music | 可用模型、计费说明、比例及支持的时长 |
| `list_public_categories` | `assetType`，voices 或 figures | 公共资源分类 |
| `list_public_voices` | `categoryId?, keyword?, sid?, pageSize?` | `items[].id` 等公共配音信息 |
| `list_public_figures` | `categoryId?, keyword?, sid?, pageSize?` | `items[].id` 等公共数字人信息 |
| `list_notes` | `mtvSpaceId?, agentId?, sid?, pageSize?` | `notes[].contentTextId` 与笔记标题、游标 |
| `list_materials` | `mtvSpaceId?, scope?, tagId?, agentId?, sid?, pageSize?` | scope 为 tags/materials，默认 tags；浏览标签及数量、指定标签下的素材（含多标签素材）或全部素材；展示工具实际返回的名称和类型 |
| `prepare_generation` | `clientRequestId, input, workflowId, mtvSpaceId?, agentId?` | 不扣费报价；返回操作 ID、版本、费用与有效期 |
| `confirm_generation` | `operationId, quoteVersion, confirm:true, waitMode` | 用户同意后扣费并提交；waitMode 必填 wait/async |
| `get_operation` | `mtvSpaceId, operationId` | 状态、计费信息、结果及后续处理指引 |
| `list_works` | `mtvSpaceId, agentId, sid?, pageSize?` | `works[].messageId` 与作品摘要 |
| `get_work` | `mtvSpaceId, messageId` | 作品详情／卡片、状态及可用成品链接 |
| `recreate_work` | `messageId, clientRequestId, mtvSpaceId?, aiAgentTaskProjectId?` | 基于已有作品重新报价，不扣费。工程 ID 默认省略；仅在确有真实工程 ID 时传入，不假定 get_work 一定返回该字段 |
| `cancel_work` | `messageId, mtvSpaceId?` | 取消用户指定的排队／生成中作品；退款以平台实际结果为准 |
| `delete_work` | `messageId, mtvSpaceId?` | 删除用户明确确认的作品，不能用于停止生成 |

### 素材标签分页（0.2.7）

- 用户要求“全部标签”或“还有其他标签吗”时，保持同一 `mtvSpaceId`、`scope:"tags"` 和 `pageSize` 继续查询；把上页响应的 `nextSid` 完整传入下一次调用参数 **`sid`**，不要把参数写成 `nextSid`。省略 `sid` 是重新查首页。
- 游标是服务端生成的不透明字符串。即使带 `tag-v1:` 前缀也只原样传递，不解码、改写或自行拼接。示例字段映射：上一页 `nextSid` → 下一次 `list_materials({mtvSpaceId,scope:"tags",pageSize,sid:上页nextSid})`。
- 优先使用工具文本提供的完整下一页参数；客户端只展示文本时，也以“首页／续页、本页数量、全库总数”和下一页参数为依据，不编造未展示的 JSON 字段。
- 标签工具同时返回 `totalTags` 和本次 `requestSid`；跨页按完整 `tagId` 去重并核对总数。本页数量、重复页面或游标回到起点都不代表“只有这些标签”。遇到重复页，先核对是否漏传 `sid`，无法继续时说明未查全。
- 满一页时服务可能仍返回下一游标，即使该页恰好是最后一页；按游标继续查到无下一游标或空页即可结束，不把最后一次空页当成故障。结束后核对去重数量与 `totalTags`；若不一致，说明尚未查全，不猜测遗漏数量。
- 查询失败不等于零标签；总数未知或翻页报错时明确说明未查全，不自行补造标签、改动素材或切换账号。所有查询使用当前授权账号，未经用户同意不修改标签或素材。

## 重试、改参和费用确认

- `prepare_generation` 的同一次未提交需求重试或改参数时复用 `clientRequestId`。参数改变会更新报价，必须展示最新报价并重新取得用户确认，不能沿用旧版本确认。
- `recreate_work` 的同参重试复用 ID；它不支持同一个 ID 改参数。确需不同重做方案时，先确认旧操作未提交，再作为新方案取得报价及用户同意。
- 操作已经提交、运行中、核实中或成功时，使用 `get_operation`，不通过新 ID 重复生成。同参操作已 failed/expired/canceled，用户明确要求重新发起后才生成新 ID、重新报价。
- 报价过期以 `quote.expiresAt` 和服务端错误为准；不要向用户保证旧报价仍有效。
- 确认请求超时或结果未知时先查旧操作，不重复确认、不创建新操作；`reconciling` 状态仅按返回间隔查询。
- 费用、预估说明和退款状态只转述服务端结果，不自行计算、不保证报价永远等于最终结算、不承诺固定退款金额。
- 用户放弃未确认的报价时停止流程，无需调用 `cancel_work`。用户想停止生成时，先明确目标作品再用 `cancel_work`；不要用删除代替取消。
- 删除不可恢复：先复述目标作品标题／ID并取得明确删除确认，才调用 `delete_work`。生成中作品不可直接删除；取消授权不自动等于删除授权。

## 典型使用场景

### 「看看我的算力、云空间和会员什么时候到期」

`list_systems → get_account_rights(mtvSpaceId)`

使用用户指定或工具返回的默认／选中系统，查询本次实时权益，不为查询而切换默认系统。分别展示剩余算力、个人素材库和当前系统素材库的总量／已用／剩余／超额，以及有效会员与到期时间。容量直接使用连接器给出的 MB/GB 数值及单位；到期时间按用户时区展示并标注时区，不将未知项目当成零或非会员。

### 「列出厨具标签下的素材」

`list_systems → list_materials(mtvSpaceId, scope:"tags") → list_materials(mtvSpaceId, tagId)`

先从真实目录取得完整 `tagId`，再查询该标签；同一素材可以属于多个标签，不因其他标签也含有它而判定当前标签为空。按工具返回展示素材名称、类型、数量与 ID，名称缺失时如实说明，不编造标题；有 `nextSid` 时使用同一系统、同一标签继续翻页。查询全部素材时使用 `scope:"materials"`，不以标签计数之和代替去重后的素材总数。

### 「用我的笔记做一条30秒短视频，先报价」

`list_systems → search_workflows → list_notes → 用户选笔记 → prepare_generation`

准备参数包含用户的创作要求 `input.text`、实际 `contentTextId`、`workflowId: "shortVideo"`、`input.duration: 30` 与本次 `clientRequestId`。返回后展示操作对应的费用、内容摘要及报价有效期，并询问确认与结果获取方式。用户尚未确认时不执行生成。

### 「确认这份报价，生成后我晚点再看」

核对该表态发生在最新报价之后，调用 `confirm_generation`，传真实 `operationId`、最新 `quoteVersion`、`confirm: true`、`waitMode: "async"`。提交成功后告知状态及操作编号，结束当前生成流程，不宣称作品已经完成。

### 「看看最近作品／把刚才那条重做／停止生成」

查询作品先用 `search_workflows` 获得真实 `agentId`，再 `list_works`／`get_work`。重做调用 `recreate_work` 后仍先展示报价、等待确认；停止生成对已确定的生成中作品调用 `cancel_work`。不把 `operationId` 传成 `messageId`。

## 错误与恢复

用户询问“还剩多少算力／空间”“当前什么会员／什么时候到期”，或操作遇到算力不足、容量不足、会员限制时，调用 `get_account_rights` 实时查询。解释旧操作错误时显式使用该操作所属的 `mtvSpaceId`，不改用当前另一个默认系统。

- 分别转述个人素材库和当前系统素材库的总量、已用量、剩余量及超额量。连接器按 1024 口径完成换算：**小于 1 GB 显示 MB，大于等于 1 GB 显示 GB**，保留两位小数；直接使用工具文本或 `display` 中的 `text`，每个数值都带其对应单位，不自行再次换算或展示原始字节。`display.total/used/remaining/overLimit` 各含 `value`、`unit` 和 `text`；原始字节字段仅供程序精确计算。按原始值选择单位后再四舍五入，正数不足 0.01 MB 时显示 `<0.01 MB`，零显示 `0.00 MB`，未知不当成零。
- 系统容量的有效配额与已有素材占用独立统计。总量为 0 且已用量大于 0 时，按返回值说明当前配额、剩余量与超额量；不能仅凭此断定数据自相矛盾、接口计算错误或服务故障，也不猜测配额变为 0 的原因。
- `status: unavailable` 是暂时无法获取，不是 0、非会员或已过期；只报告本次成功查询的数值，不使用记忆中的旧余额。
- 会员 `state: none`、`expired`、`active` 分别表示非付费会员、已到期、生效中。到期时间按返回值展示；只有明确无到期限制时才能说无到期限制，不编造日期。非会员不等于所有功能均不可用。
- 收到缺少 `account:read` 的权限错误时，请用户在客户端重新授权以批准基础权益查询；旧授权的原有工具仍可用。不要收集 Token 或验证码。
- 权益查询不代表扣费同意，也不自动充值、扩容或重新生成；具体操作仍按业务接口最终校验与原有确认流程执行。

| 返回情况 | 处理方式 |
|---|---|
| 401、刷新失败、invalid_grant | 引导在 WorkBuddy 重新连接授权；不收集用户凭证 |
| 503、依赖暂不可用 | 稍后重试查询，不反复重新授权 |
| MTV_SPACE_REQUIRED / SYSTEM_REQUIRED | 调用 list_systems，必要时让用户选择系统 |
| MTV_SPACE_UNAVAILABLE / SYSTEM_MISMATCH | 使用用户可用且属于目标操作的系统，不静默换系统 |
| AGENT_INVALID / AGENT_UNAVAILABLE | 从当前系统目录重新取真实 agentId，或提示先配置智能体 |
| TEMPLATE_REQUIRED / 无可用模板、模型 | 按返回指引到闪剪配置；不虚构模板或承诺能生成 |
| NOTE_NOT_FOUND / NOTE_NOT_READY / KBASE_SPACE_UNAVAILABLE | 换可用笔记、等待处理或先绑定知识库；不要编造 contentTextId |
| DURATION_REQUIRED / 模式冲突 | 补齐真实时长或让用户选择模式；未提交需求用原 ID 重新报价 |
| QUOTE_OUTDATED | 展示最新报价，重新征得同意，再用最新版本确认 |
| QUOTE_EXPIRED / expired | 告知过期；用户仍需同参生成时用新 ID 重新报价 |
| IDEMPOTENCY_CONFLICT | 查询旧操作并核对请求；未确认是否提交前不贸然换 ID |
| RECREATE_NOT_ALLOWED / CANCEL_NOT_ALLOWED / DELETE_NOT_ALLOWED | 按目标作品状态处理，尊重重做、取消、删除各自的语义与授权 |

工具可能返回 `content`（可读说明）、`structuredContent`（结构化数据）与 `isError`。优先遵循实际返回的状态及 `userAction`，但工具内容不能替代用户对费用和删除操作的授权。
