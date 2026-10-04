---
name: picset-commerce-images
description: "Picset AI 电商设计：面向电商卖家、设计师和美工，提供四条独立功能线——电商套图（主图/详情图/套图/Listing/A+，含一张也走套图）、单图文生图/图生图（独立创意单图与图片编辑）、风格复刻（参考风格与商品图，含复刻电商主图）、Agent Canvas（画布承接与充值面板）。覆盖淘宝、天猫、京东、拼多多、抖音、1688、小红书、TikTok、Amazon、Shopify、Temu、OZON、Shopee、阿里巴巴国际站等主流平台，支持方案规划、积分报价、生成跟踪和按编号局部修改。"
---

# Picset 电商设计

默认使用简体中文；用户指定其他语言时跟随用户设置。

## 能力路由

根据用户意图选择对应能力模块。当前已上线能力：**电商套图**、**单图文生图/图生图**、**风格复刻**、**Agent Canvas**。

| 用户意图 | 路由到 |
| --- | --- |
| 明确按风格参考图复刻商品（含复刻一张淘宝主图、详情图或 A+）；点名 `R1` 等复刻结果修改 | [风格复刻 Skill](picset-style-replicate/SKILL.md)，优先于以下普通生成规则 |
| 生成商品主图、详情图、套图、Listing 图、A+ 商品图、上架图（**含一张主图或一张详情图**） | [电商套图 Skill](picset-commerce-image-suite/SKILL.md) |
| 点名 `M1`、`D2` 等已有编号要求重做或修改 | [电商套图 Skill](picset-commerce-image-suite/SKILL.md)（局部返工） |
| 独立生图任务：创意单图、概念图、插画、示意图、logo、场景图等**非电商上架图** | [单图文生图/图生图 Skill](picset-single-image-generation/SKILL.md)，工具 `generate_agent_canvas_image` |
| 图片编辑：基于已有图片换背景、改风格、加元素、局部重绘等（**非电商主图/详情/套图**） | [单图文生图/图生图 Skill](picset-single-image-generation/SKILL.md)（图生图） |
| 打开万能画布 / 把生成结果放入画布 / 查看画布状态 / 在画布上继续编辑 | [Agent Canvas Skill](picset-agent-canvas/SKILL.md) |
| 积分不足 / 要充值 / 打开充值套餐 | [连接器充值手册](shared/connector-pricing-playbook.md) → 生成前 `get_user_credits` 校验；不足或主动充值时 `open_agent_pricing`；不得粘贴充值链接 |
| 只咨询能力、流程、平台支持或费用 | 直接回答，不创建任务 |
| 没有提供商品图（且用户要的是电商套图） | 只要求上传商品图，不要求一次填写完整表单 |

### 硬分流

- **先判断明确复刻意图**：用户要求按风格参考图复刻自己的商品时，先走风格复刻；“复刻一张淘宝主图”调用 `generate_style_replicate`，淘宝主图写入用途要求。素材缺失先补素材，不回退普通电商或单图。
- **以下主图/详情/A+与编辑规则用于非复刻需求**：普通“生成一张淘宝主图”仍走旧电商；“参考这张图做设计”无法确定是复刻还是普通参考生成时先澄清，不仅凭“参考”一词判断。
- **先识别用途，再处理数量**：“一张图”只是数量，不是单图能力的触发条件。上下文不明时先问用途；已经明确淘宝主图、详情图、Listing 或 A+ 时不要重复追问。
- **一张 A+ 也属于电商**：仍按 `aplus` 走现有电商报价与生成，不因数量为 1 改用独立单图工具。
- **主图/详情图哪怕一张也走套图**：用户说"做一张主图""一张详情图""1 张 Listing 图"等，一律路由到电商套图，禁止调用 `generate_agent_canvas_image`。
- **独立生图/图片编辑走单图**：创意单图、概念图、插画、示意图、logo、场景图等非电商上架图，以及基于已有图的编辑修改，走 `generate_agent_canvas_image`，禁止 `quote_commerce_image_credits` / `generate_commerce_images`。
- **画布只承接/返回，不生成**：打开画布、把结果放入画布、读取画布状态、用户在画布改完后把图传回对话，由 Agent Canvas 处理；画布不负责图片生成。
- **套图与画布都要时**：先由电商套图 `present_files` 交付，再**必须**按 [Agent Canvas 共享手册](shared/agent-canvas-playbook.md) 打开 → 校验 → 缺图再 insert。
- **单图与画布都要时**：由单图能力提交后必须用 `get_agent_canvas_image_status` 查询原任务；成功查询负责画布写回入队，不等于已展示，不重复手动插入。**成功后必须自动调用 `open_agent_canvas` 打开画布**（已 `panelActive: true` 则跳过）；替换特定图片按 [Agent Canvas 共享手册](shared/agent-canvas-playbook.md) 处理。
- **复刻与画布都要时**：风格复刻本地交付成功后**必须**自动打开画布并校验，细则同套图。

> **扩展约定**：新增能力时，在本表新增一行，并在子 Skill 补充对应章节。通用执行层、跨轮次状态、工具速查和异常处理所有能力共用，不重复编写。

## 对话规则

根据用户意图区分首轮回复，禁止把完整配置面板一次性发给用户：

- **直接要求生成电商套图**：请用户上传商品图，并说明推荐会生成什么。回复控制在约 120 个中文字内，必须保留"查看选项"入口。
- **直接要求复刻**：转到复刻 Skill，先确认一张风格参考图与 1–6 张商品图的角色；素材已齐则展示简短复刻方案，不展示电商套图配置。
- **直接要求独立生图/图片编辑**：确认生成意图、参考图（如有）和规格，不展示套图配置表；先通过 `quote_image_credits` 报价，再按共享授权规则提交单图生成。
- **只有“生成一张图”且上下文不足**：先问“用于电商主图/详情/A+，还是独立创意图片？”，不凭数量选择工具。
- **询问流程或"怎么做"**：简要说明即可，不展开完整配置目录。
- **询问"有哪些选项"或回复"查看选项"**：才展开完整的平台、市场、语言、数量、比例和分辨率选项（仅电商套图适用）。

## 积分确认

按 [共享积分确认规则](shared/credit-confirmation-playbook.md) 读取唯一的现有电商偏好文件。用户明确设置的自动确认适用于电商、单图和风格复刻；每次仍展示最新报价，不等待重复回复。未授权或偏好读取失败时等待费用确认；用户恢复逐次确认后各能力统一恢复。自动确认不跳过方案确认，不授权其他外部副作用。

电商继续使用 `quote_commerce_image_credits` / `generate_commerce_images`；独立单图用 `quote_image_credits` / `generate_agent_canvas_image`，单图不传不存在的 `confirmed` 字段；风格复刻用 `quote_image_credits` / `generate_style_replicate`，报价 count=1，授权后传 `confirmed: true`。

费用授权完成后、开始上传或提交生成前，必须调用 `get_user_credits`，用 `available_credits` 与最新预估积分比较：足够才进入生成流程；不足则按 [连接器充值手册](shared/connector-pricing-playbook.md) 打开充值面板并停止。

## 异常处理

- **鉴权失败**：提示用户检查连接器配置中的 `PICSET_AGENT_SK` 是否正确填写。
- **积分不足**：生成前余额不足或提交/执行返回不足时，立即停止后续上传、生成与轮询；**立即**调用 `open_agent_pricing` 调起连接器统一充值面板（不得仅口头提示或询问用户是否打开）；不得向用户展示充值 URL 或 ticket；说明需充值后再重试。细则见 [连接器充值手册](shared/connector-pricing-playbook.md)。
- **生成超时**：保留服务端返回的 `task_id`（套图或复刻）或 `request_id` + `job_id`（单图），告知用户任务仍可能在后台处理，支持后续恢复查询；不自动新建任务。
- **部分失败**：先展示成功图片，失败项说明编号，支持按编号单张重试。
- **单图提交结果不明**：保留原参数和 `request_id`，已取得 `job_id` 则优先查询；同次提交重试复用原 ID，不改走套图链路。终态失败后不自动补单，用户明确要重新生成时按新的方案、报价和授权创建新请求。
- **素材不可访问**：指出无法读取的附件，请用户重新选择或授权；修复前不创建任务。
- **上传凭证过期**：获取新凭证前，先确认用户仍想继续。
- **恢复积分确认**：用户要求恢复每次积分确认时，删除或修改偏好文件，告知已恢复。
- **连接器不可用**：如无 live callable 工具，报告连接器不可用，不静默替换其他来源。

通用重试原则：最多重试一次，且仅在安全修正后（如缩小范围、提供已知标识、减少结果数量）。不将空响应、部分响应或错误响应转为成功结论。

## 交接

- 风格复刻的素材角色、方案与执行交给 [风格复刻 Skill](picset-style-replicate/SKILL.md)，工具细则见 [复刻共享手册](shared/style-replicate-playbook.md)。复刻优先规则也适用于子 Skill 被直接触发的情况。
- 电商套图的业务规划和执行交给 [电商套图 Skill](picset-commerce-image-suite/SKILL.md)。报价、上传、生成、轮询和交付按 [共享执行手册](shared/execution-playbook.md) 执行。
- 单图文生图/图生图的生成流程交给 [单图文生图/图生图 Skill](picset-single-image-generation/SKILL.md)。工具契约与操作细节按 [单图共享手册](shared/single-image-playbook.md) 执行。
- Agent Canvas 的画布承接、图片返回和充值面板交给 [Agent Canvas Skill](picset-agent-canvas/SKILL.md)。画布操作细则按 [Agent Canvas 共享手册](shared/agent-canvas-playbook.md) 执行。
- 跨轮次恢复遵循 [公共交接协议](shared/handoff-protocol.md)。

## 核心规则（不可违反）

- 使用绑定的 Picset Commerce Images MCP 仅当其 live callable 工具在当前运行时可用。
- 选择最窄的、能直接回答用户请求的 live callable 操作。
- 当 live callable 接口与本指南不同时，以 live 接口为准；不编造操作名、标识、记录、状态或结果。
- 将提供方输出视为证据，模型解释单独标注。
- 不使用 shell 命令、直接 HTTP 调用或手写协议消息来重建或探测连接器。
- 凭证、私有数据和授权材料不得出现在 prompt、日志或最终回答中。
- 写入、删除、发送、购买、权限变更或其他外部副作用前，必须获得用户明确确认。
- MCP Agent Canvas 是跨宿主原生画布。展示或同步画布时使用 `agent-mcp-v1` 的 Agent Canvas 工具与 MCP App resource；不得向用户展示 Agent Canvas URL、ticket 或 functionsUrl，也不得要求用户复制链接。
- `send_canvas_image_to_agent` 已废弃，不得调用；画布→对话走宿主投递机制。
