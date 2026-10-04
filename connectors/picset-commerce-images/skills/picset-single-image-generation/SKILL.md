---
name: picset-single-image-generation
description: "Picset 单图文生图/图生图：面向独立生图任务和图片编辑场景，根据提示词或参考图生成单张图片。适用于创意单图、概念图、插画、示意图、logo、场景图等非电商上架图，以及基于已有图片的换背景、改风格、加元素等编辑操作。电商主图、详情图、Listing 和 A+ 即使只生成一张，也不属于独立单图能力；明确商品风格复刻交给复刻能力。不走电商套图报价与 generate_commerce_images 链路；画布仅作为结果承接容器，无需提前打开画布，生成成功后必须自动打开画布。"
---

# Picset 单图文生图/图生图

独立单张图片生成与图片编辑能力。默认使用简体中文。

## 职责与边界

负责**独立生图任务**和**图片编辑**：根据用户提示词生成单张创意图片，或基于用户提供的参考图进行图生图/编辑修改。

**不负责**：
- 明确按风格参考图复刻自己的商品（含复刻一张淘宝主图）——优先交给 [风格复刻 Skill](../picset-style-replicate/SKILL.md)。缺素材先补素材，不回退普通电商或单图；仅“参考图片”或“改风格”不足以认定商品复刻，无法区分时先澄清。
- 普通电商主图、详情图、套图、Listing 图、A+ 商品图的方案规划与 `generate_commerce_images` 链路——交给 [电商套图 Skill](../picset-commerce-image-suite/SKILL.md)，**哪怕用户只要一张主图或一张详情图，也必须走套图**。
- 画布的手动插入/替换、画布状态读取与图片返回——交给 [Agent Canvas Skill](../picset-agent-canvas/SKILL.md)。单图任务查询仍由本能力负责，成功查询由服务端写回入队；**生成成功后由本能力调用 `open_agent_canvas` 自动打开画布**，不必提前打开。
- 充值套餐面板——由连接器统一充值面板处理，详见 [连接器充值手册](../shared/connector-pricing-playbook.md)，工具为 `open_agent_pricing`。

细则与工具契约一律按 [单图共享手册](../shared/single-image-playbook.md) 执行，本 Skill 不重复展开。费用授权按 [共享积分确认规则](../shared/credit-confirmation-playbook.md)，不另建单图偏好文件。

## 调用时机

仅在以下两种场景调用本能力：

1. **独立生图任务**：用户要的是创意单图、概念图、插画、示意图、logo、场景图、氛围图等**非电商上架图**，且没有要求生成主图/详情图/套图/Listing/A+。
2. **图片编辑**：用户上传或引用一张已有图片，要求对其进行修改（换背景、改风格、加元素、局部重绘、扩图等），且修改目标**不是**电商主图/详情图/套图。

只说“生成一张图”且上下文不足时，先问“用于电商主图/详情/A+，还是独立创意图片？”；能确定时不重复问。确认主体、用途与关键风格即可，不展示电商套图配置表，不一次性要求填写全部参数。

## 硬边界

- **复刻优先**：以下普通电商与编辑规则不覆盖明确商品风格复刻。
- **主图/详情图哪怕一张也走套图**：普通“做一张主图”“一张详情图”“1 张 Listing 图”或“一张 A+ 图”路由到电商套图，禁止用单图工具冒充上架图；点名 M/D 编号修改回到电商局部返工。
- **单图不走套图报价**：独立生图和图片编辑使用 `quote_image_credits`，不调用 `quote_commerce_image_credits` / `generate_commerce_images`，不采用电商批量编号。公共素材上传登记不改变生成路由。
- **画布不负责生成**：本 Skill 不调用 `insert_agent_canvas_image` / `replace_agent_canvas_image`；但提交后必须调用 `get_agent_canvas_image_status` 查询任务，成功后必须调用 `open_agent_canvas` 打开画布，不改走 `get_generation_task_status`。

## 单图文生图流程

用户没有提供参考图、要求根据提示词生成单张图片时：

1. `conversationId` 必须按 [Agent Canvas 共享手册](../shared/agent-canvas-playbook.md)「宿主 conversation_id 解析」取得（优先 `picset_client.py host-conversation-id` / `CODEBUDDY_CONVERSATION_REQUEST_ID`），原样使用，不得自行生成或改写；解析失败时停止，请宿主提供。
2. 确认生成意图、提示词与实际规格；未指定时推荐 `nova-2.0 / 2K / 1:1 / fast`。调用 `quote_image_credits`（count=1），展示最新预估与实时扣费说明；按共享规则判断费用授权，未授权自动确认时等待本次费用确认。
3. 费用授权后调用 `get_user_credits`，将 `available_credits` 与本次 `estimated_credits` 比较；不足则打开充值面板并停止，足够才继续。见 [连接器充值手册](../shared/connector-pricing-playbook.md)。
4. 首次正式提交前生成并保存 UUID v4 `request_id`；同一次提交、查询和结果不明时的重放复用原 ID 与全部原参数。终态失败后主动重新生成按手册作为新请求，不自动补单。
5. 调用 `generate_agent_canvas_image`，传入 `conversationId`、`request_id`、`prompt` 和与报价一致的物理规格，`outputCount` 固定为 1，`referenceImages` 为空或不传；无 `confirmed` 字段，不得传入。未传 `agentCanvasSessionId` 时服务端按 `conversationId` 自动开/复用画布会话。
6. 保存返回的 `job_id` 和会话 ID，必须用 `get_agent_canvas_image_status` 查询，携带原 `conversationId`、`request_id` 和 `job_id`；按手册静默轮询，不能凭提交成功宣称图片已生成。
7. 成功查询后：若尚未 `panelActive: true`，用原 `conversationId` 调用 `open_agent_canvas` **自动打开画布**；再简要告知生成结果。勿输出 ticket / functionsUrl。成功查询负责画布写回入队，入队不等于已展示，不重复插图；替换等其他画布操作交给 Agent Canvas。

## 单图图生图流程

用户提供了参考图、要求基于参考图生成单张图片时：

1. 确认素材与修改意图，最多 5 张；超过时请用户选择，不静默丢弃、不自行分批。参考图必须是当前用户已授权且审核通过的 HTTPS URL，普通宿主附件或历史生成图片仅可访问不够，本地路径不能直接当 URL。
2. `conversationId`、方案确认、报价与费用授权规则同文生图。费用授权后须先通过余额校验再准备未登记素材；无可行素材准备路径时明确阻塞，不编造上传服务、不降级成无参考图生成。
3. 调用 `generate_agent_canvas_image`，参数同文生图，另传 `referenceImages`（每项含已授权 `url`）；`prompt` 描述生成/编辑意图，不添加用户未要求的修改。
4. 必须查询原任务；轮询、**成功后自动打开画布**与结果处理同文生图。

## 图片编辑流程

用户要求对已有图片进行修改（换背景、改风格、加元素等）时：

1. 先排除明确商品复刻；确认编辑目标不是电商主图/详情图/套图——如果是，路由到电商套图的局部返工。
2. 将待编辑图片按手册准备为已授权参考图后传入 `referenceImages`，`prompt` 描述编辑意图（如“把背景换成厨房场景”）。
3. 其余流程同图生图（含成功后自动打开画布）。
4. 编辑并打开画布后，若用户继续在画布上微调，交给 Agent Canvas 承接；若用户要求把编辑后的图传回对话，按 Agent Canvas 手册由宿主支持的返回机制处理。

## 结果处理

- **成功**：成功查询后立即自动打开画布，再简要告知生成/编辑完成，说明真实结果与可确认费用。不输出 ticket、functionsUrl 或内部会话 ID，不编造扣费/退款。
- **提交中断/结果不明**：保留原参数和 `request_id`，同次请求最多重放一次，已取得 `job_id` 时优先查询，不自动创建第二个收费任务。
- **生成超时**：保留原 `conversationId`、`request_id`、`job_id` 与已知画布会话 ID，后续恢复查询，不重新提交。
- **终态失败**：如实报告；同 ID 重放不保证重新生成。用户明确要求重做或修改内容时，按新请求重新确认方案、报价与授权，再使用新 ID，不自动补单。失败不打开画布。
- **画布承接**：成功查询由服务端写回入队；不重复插图，不宣称入队即已展示。**成功后自动打开画布是本流程必做步骤**，不等待用户要求；若已 `panelActive: true` 则跳过重复打开。替换特定图片交给 Agent Canvas。
- **积分不足**：生成前余额不足或提交/执行返回不足时，立即停止后续上传、生成与轮询；**立即**调用 `open_agent_pricing` 调起连接器统一充值面板（不得仅口头提示或询问用户是否打开），不得向用户展示充值 URL 或 ticket；说明需充值后再重试。
- **工具缺失/素材未授权**：按手册报告阻塞并准备可用素材，不静默切换电商或其他服务。

## MCP 工具速查

| 工具 | 用途 | 调用阶段 |
| --- | --- | --- |
| `quote_image_credits` | 按实际物理规格查询 1 张图片预估积分，只读、不扣费 | 报价 |
| `get_user_credits` | 查询可用积分余额 | 生成前余额校验 |
| `generate_agent_canvas_image` | 单图生成（文生图/图生图/图片编辑），outputCount 固定 1 | 生成提交 |
| `get_agent_canvas_image_status` | 查询单图任务状态与结果，成功时写回画布命令入队 | 轮询 |
| `open_agent_canvas` | 生成成功后打开/复用画布 Panel | 结果交付 |
| `open_agent_pricing` | 打开连接器统一充值面板 | 积分不足 |

调用 MCP 工具前，必须使用 `tool_search` 按工具名获取完整参数定义，再按取回的定义发起调用。运行时工具名可能带有后缀，以 `tool_search` 返回的实际名称为准。

> 注：`generate_agent_canvas_image` 工具名中虽含 "canvas"，但其定位是**独立单图生成工具**；画布承接是服务端的联动行为，不改变本能力的独立生图定位。生成成功后自动打开画布属于结果交付，不属于“用画布生成”。
