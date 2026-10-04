# Picset 单图文生图/图生图共享手册

本手册定义单图文生图、图生图和图片编辑的工具契约与操作细节。[单图文生图/图生图 Skill](../picset-single-image-generation/SKILL.md) 统一遵循本手册，不重复实现工具调用逻辑。

业务用途优先于数量：普通电商主图、详情图、Listing、A+ 即使只要一张，也走现有电商链路；明确按风格参考图复刻自己的商品时，优先走 [复刻手册](./style-replicate-playbook.md)。仅“参考图片”或“改风格”不足以认定商品复刻，用途不明先澄清。

调用 MCP 工具前，必须使用 `tool_search` 按工具名获取完整参数定义，再按取回的定义发起调用。实际参数与工具名以运行时定义为准；工具不可用时停止，不用 shell 或直接 HTTP 重建连接器。

---

## 一、工具总览

| 工具 | 用途 | 调用阶段 |
| --- | --- | --- |
| `quote_image_credits` | 按物理规格查询 1 张图片的预估积分，只读、不扣费 | 报价 |
| `get_user_credits` | 查询当前用户可用积分余额，只读 | 生成前余额校验 |
| `generate_agent_canvas_image` | 单图生成（文生图/图生图/图片编辑），outputCount 固定 1 | 生成提交 |
| `get_agent_canvas_image_status` | 查询单图任务状态；成功时由服务端将画布写回命令入队 | 轮询 |
| `open_agent_canvas` | 生成成功后打开/复用画布 Panel，展示写回结果 | 结果交付 |
| `open_agent_pricing` | 打开连接器统一充值面板 | 积分不足 |

执行顺序：确认意图与规格 → 报价与积分确认 → **生成前余额校验** → 准备已授权参考图（如需）→ 提交生成 → 专用状态查询 → **成功后自动打开画布** → 结果交付。

不调用 `quote_commerce_image_credits` / `generate_commerce_images` / `get_generation_task_status` 来替代单图流程。公共素材上传登记不改变业务路由。

> 注：`generate_agent_canvas_image` 工具名中虽含 "canvas"，但其定位是独立单图生成工具。无需先打开画布；服务端按 `conversationId` 自动开/复用画布会话，成功查询负责写回入队。**生成成功后必须自动调用 `open_agent_canvas`**，让用户看到结果；替换与图片返回细则见 [Agent Canvas 共享手册](./agent-canvas-playbook.md)，不重复插图。

---

## 二、报价与积分确认

确认用户的生成意图、提示词、参考素材及实际规格后，调用 `quote_image_credits`。缺少真实宿主会话 ID 或没有可行素材准备路径时先解决阻塞，不报价后盲目提交。

### 入参

默认推荐 `nova-2.0 / 2K / 1:1 / fast`；用户指定且接口支持时优先采用。单组规格示例：

```json
{
  "model": "nova-2.0",
  "resolution": "2K",
  "aspect_ratio": "1:1",
  "speed_mode": "fast",
  "count": 1
}
```

- `count` 固定为 1，不同时传兼容别名 `image_count`；不传电商类型、提示词、参考图、会话 ID、请求 ID 或确认状态。
- 模型公开名按 schema：`nova-pro`、`nova-2.0`、`nova-2.0-lite`、`nova-img-2`、`nova-img-2-vip`。不向用户推荐内部模型名。
- 分辨率、速度、比例须符合模型约束：`nova-2.0-lite` 固定 `1K`；极端比例 `1:8 / 1:4 / 4:1 / 8:1` 仅 `nova-2.0 / nova-2.0-lite` 支持；`0.5K` 不用于 `normal`，`nova-img-2` 不支持 `turbo`。不支持时说明并确认可用替代，不静默修改。
- 本能力不单独开放 `quality` 选择：生成工具没有对应字段，不传只改变报价而无法用于生成的画质选项。
- 报价与生成显式传同一组模型、分辨率、比例、速度，不依赖两端缺省值恰好相同。

### 返回与授权

- 根据 `items` 中的 `credit_cost_per_image`、`subtotal_credits` 及顶层 `estimated_credits` 展示“1 张、模型、分辨率、比例、速度、预估积分”。字段变化按实际返回读取；缺少可靠费用时停止，不把缺失当成 0。
- 说明最终按提交时实时积分扣除，可能与预估不同；不编造实际扣费或退款。
- 按 [共享积分确认规则](./credit-confirmation-playbook.md) 读取唯一电商偏好文件。有效自动确认授权下，展示最新报价后继续；否则结束当前回复，等待用户针对最新费用的新确认。用户恢复确认后单图也须等待，不另建单图偏好文件。
- 方案确认不等于费用确认；用户修改方案或规格后重新报价，旧的本次费用确认失效。
- 费用授权完成后、准备素材或提交生成前，必须按 [连接器充值手册](./connector-pricing-playbook.md) 调用 `get_user_credits`，将 `available_credits` 与本次 `estimated_credits` 比较；余额不足则打开充值面板并停止，不上传、不生成。

---

## 三、generate_agent_canvas_image

### 用途

根据提示词和可选参考图生成单张图片。文生图时不传参考图；图生图/图片编辑时传入符合第七节授权条件的参考图。

### 前置条件

- 用户意图已确认为独立生图任务或普通图片编辑，非电商上架图或商品风格复刻
- `conversationId` 已按 [Agent Canvas 共享手册](./agent-canvas-playbook.md)「宿主 conversation_id 解析」取得；解析失败时要求宿主提供，生成前停止
- 方案、实际规格、最新报价与费用授权已完成；生成前余额校验已通过；参考图已准备就绪
- 首次正式提交前已生成并保存 UUID v4 `request_id`

### 入参

```json
{
  "conversationId": "<宿主当前会话 ID>",
  "request_id": "<UUID v4，本次生图的稳定幂等键>",
  "prompt": "<本次图片生成提示词，1-4000 字符>",
  "referenceImages": [
    { "url": "<已授权的 HTTPS 参考图 URL>", "id": "<可选，图片标识>", "mimeType": "<可选，MIME 类型>" }
  ],
  "outputCount": 1,
  "model": "nova-2.0",
  "resolution": "2K",
  "aspect_ratio": "1:1",
  "speed_mode": "fast"
}
```

- `conversationId`：必填，宿主提供的真实当前对话 ID（见第六节解析规则）。原样使用，不自行生成、改写或用 `request_id` 代替。
- `request_id`：必填，UUID v4；同一次提交、查询和重放不变，详见第五节。
- `prompt`：必填，1–4000 字符；超长时先精简并让用户确认，不静默截断关键需求。
- `referenceImages`：可选，最多 5 项，每项必须含 `url`；`id` 和 `mimeType` 可选。文生图时为空或不传；编辑意图写入 `prompt`。
- `outputCount`：固定为 1，不得传其他值。
- `model`、`resolution`、`aspect_ratio`、`speed_mode`：与最新报价一致。
- `agentCanvasSessionId`：可选，已知画布会话 ID；不虚构，不传时服务端按 `conversationId` 自动开/复用。
- 无 `confirmed` 字段，不得传入；费用授权在调用前按共享规则执行。

### 返回

提交成功后返回 `job_id` 和 `status: processing`。保存原请求参数、`request_id`、`job_id`、返回的 `agentCanvasSessionId` 与可确认的费用记录，把任务标记为 `submitted`。提交响应不保证提供实际扣费字段，缺失保持未知，不把预估当实扣。

### 约束

- 不得先调用生成工具试探参数或校验 `request_id`
- 提交成功不等于图片生成成功；空响应、错误响应或缺少 `job_id` 的响应不能宣称成功
- 提交中断保留原参数与 `request_id`，已取得 `job_id` 时优先查询，不自动创建第二个收费任务
- 积分不足按第八节立即停止并调起充值面板，不改走电商生图

---

## 四、get_agent_canvas_image_status

### 用途

查询单张图片生成结果，并在成功后由服务端将画布插图命令入队。提交后必须调用 `get_agent_canvas_image_status`，即使生成很快也不能跳过；不使用 `get_generation_task_status` 查询单图任务。

### 前置条件

- 已调用 `generate_agent_canvas_image` 并取得 `job_id`
- 保存了原 `conversationId` 和 `request_id`

### 入参

```json
{
  "conversationId": "<与生成时相同的宿主对话 ID>",
  "request_id": "<与生成时相同的 UUID v4>",
  "job_id": "<generate_agent_canvas_image 返回的任务 ID>"
}
```

- 三个标识均必填，不换用新的请求标识查询旧任务
- `agentCanvasSessionId` 可选；生成时显式指定的查询也须使用同一值，可使用生成响应返回的会话 ID

### 返回与状态处理

- `processing`：继续轮询
- `success`：记录 `image_url` 和真实生成结果；`writeback.status: enqueued` 表示写回命令已入队，不代表画布已显示。成功后必须按第八节自动打开画布，再简要告知结果
- `failed`：记录失败原因，停止轮询；未知或缺失状态不当成功；失败不打开画布
- 成功查询已负责写回入队，不再手动调用插入工具；打开画布与其他承接操作见第八节

### 节奏

- 固定 30 秒间隔调用一次，不向用户输出逐次进度消息
- 轮询期间不读写本地文件

### 超时处理

- 累计等待达到合理上限或宿主执行时限时停止轮询
- 保留原 `conversationId`、`request_id`、`job_id` 和已知画布会话 ID，告知任务仍可能在后台处理
- 不自动新建任务或重新提交；用户后续继续时恢复原任务查询，成功查询后才有写回入队证据

---

## 五、request_id 规则

- 每次独立生图任务生成一个新的 UUID v4 `request_id`，首次正式提交前保存
- 同一次提交、查询、结果不明时的重放必须复用同一个值及全部原参数；重放返回的费用不能重复累计
- 终态失败后同 ID 命中已有任务，不代表会重新生成；不得自动换 ID 补单收费
- 用户明确要求重新生成或修改提示词、参考图、规格时，作为新的独立请求，重新确认方案、报价与授权后使用新 ID
- 不同生图任务使用不同的 `request_id`；只保留在执行上下文，不发送给报价工具

---

## 六、conversationId 规则

- 必须原样使用宿主当前会话 ID（亦可能写作 `conversation_id`）
- 不得自行生成、改写或拼接，不得使用图片生成 `request_id` 代替
- 对话提示词里未必带有该 ID：按 [Agent Canvas 共享手册](./agent-canvas-playbook.md)「宿主 conversation_id 解析」，先跑 `python3 __SKILL_DIR__/../../scripts/picset_client.py host-conversation-id`（或读取 `CODEBUDDY_CONVERSATION_REQUEST_ID`），再写入 `conversationId`
- 不得使用 `CODEBUDDY_CONVERSATION_MESSAGE_ID`、`CODEBUDDY_SESSION_ID`、`CLAUDE_SESSION_ID`
- 解析仍失败时停止生成并说明，不盲目提交
- 同一会话内多次生图使用同一个 `conversationId`；恢复旧任务时保留生成时的真实会话 ID

---

## 七、参考图规则

- `referenceImages` 最多 5 张，每项必须含 HTTPS `url`；本地路径不是 URL，不直接传 OSS 相对路径。6 张及以上请用户选择，不静默丢弃或自行分批。
- 文生图为空或不传；图生图/编辑传已确认的素材，不能静默增加用户未要求的修改。
- **可访问不等于已授权**：后端要求 URL 属于配置允许的 OSS/CDN 域名；对应 OSS 路径存在于 `user_uploaded_images`，归属当前用户，且 `audit_status` 为 `approved`。不得访问数据库或编造审核结果来绕过鉴权。
- 已有可靠登记和审核成功记录的素材可复用。普通宿主附件、外域 URL、历史生成图片不能仅凭可访问就认定已授权；无法确认时先准备素材，不用收费生成工具试探。
- 未登记素材：方案和报价授权完成后，取得用户已授权使用的本地附件，通过 `get_reference_image_upload_token` → `picset_client.py upload` → `register_reference_image` 准备素材。仅复用 [上传登记手册](./execution-playbook.md#三上传登记) 的凭证、公共上传器与登记操作，不继承电商的 9 张上限、报价、生成或批量编号；单图始终最多 5 张。
- 登记返回 `success: true` 且 `audit_status: approved` 后，使用 `reference_image_urls` 中对应的 HTTPS URL；失败或审核未确认完成时停止，不伪造 `approved`。只有远程附件且宿主无法提供本地素材、工具或公共上传器不可用时，报告具体阻塞，请用户提供可准备的素材；不自建上传服务，不用 shell 或直接 HTTP 替代 MCP。
- 上传凭证按公共上传器规范通过标准输入传递，不写日志或临时文件、不展示密钥；上传登记不改变独立单图生成路由。
- `REFERENCE_IMAGE_NOT_AUTHORIZED` 或参考图失效时停止，恢复授权素材；不静默降级成无参考图文生图，也不自动换 ID 收费重试。

---

## 八、结果与失败处理

- **成功**：成功查询确认后，**必须**用原 `conversationId`（或宿主 `conversation_id`）调用 `open_agent_canvas` 自动打开画布，再简要告知生成/编辑完成与可确认费用。不输出 ticket、functionsUrl 或内部会话 ID，不编造扣费/退款。
- **失败**：区分提交结果不明与终态失败，按第五节和第九节处理，不改走电商链路，不编造结果；终态失败不打开画布。
- **积分不足**：生成前余额不足或提交/执行返回积分不足时，立即停止后续上传、生成与轮询；**立即**调用 `open_agent_pricing` 调起连接器统一充值面板（不得仅口头提示或询问用户是否打开），不得向用户展示充值 URL 或 ticket；说明需充值后再重试。细则见 [连接器充值手册](./connector-pricing-playbook.md)。
- **画布承接**：成功查询由服务端写回入队；不重复插图，不把入队说成已展示。**单图成功后自动打开画布是本能力必做步骤**，不等待用户再说“打开画布”。若状态查询已返回 `panelActive: true`，则不再重复调用 `open_agent_canvas`。替换特定图片或返回对话交给 [Agent Canvas 共享手册](./agent-canvas-playbook.md)。
- **工具缺失/鉴权失败**：如实报告，不替换成电商或其他服务；错误或部分响应不转换成成功结论。

---

## 九、通用重试原则

同一次请求提交中断/结果不明时，保留全部原参数和 `request_id`，最多重放一次；已取得 `job_id` 时优先查询。超时不重提。修改内容或终态失败后主动重新生成按第五节作为新请求，不把修正后的参数混入旧请求。不将空响应、部分响应或错误响应转为成功结论。
