# Picset Agent Canvas 共享手册

本手册定义 MCP Agent Canvas（万能画布）的标准操作。主 Skill、电商套图 Skill、单图文生图/图生图 Skill、风格复刻 Skill 与 Agent Canvas Skill 共用，不在各处重复实现。充值面板的操作详见 [连接器充值手册](./connector-pricing-playbook.md)。

跨宿主原生画布。调用前用 `tool_search` 取参；只用 live MCP 工具。不得向用户展示 ticket / functionsUrl；`get_agent_canvas_state` 等返回的图片 URL 可展示。

**画布定位**：画布只负责**承接 Agent 生成的图片**和**用户修改后将图片返回给 Agent**。画布不负责图片生成——生成由电商套图（`generate_commerce_images`）、单图文生图/图生图（`generate_agent_canvas_image`）或风格复刻（`generate_style_replicate`）完成。画布也不负责充值——充值由连接器统一充值面板（`open_agent_pricing`）处理，详见 [连接器充值手册](./connector-pricing-playbook.md)。单图文生图/图生图的生成流程详见 [单图共享手册](./single-image-playbook.md)。

命中画布能力时：不要求商品图、不展示套图配置表、不走报价/生成套图链路；直接按下列流程或工具执行。

### 宿主 conversation_id 解析（硬规则）

`conversation_id` / `conversationId` 是宿主（WorkBuddy / CodeBuddy）当前**对话对象**的 ID，由宿主创建；Picset 不生成、不改写。它通常注入在 Agent **进程环境变量**中，**不一定**出现在对话提示词里——因此不得因为“上下文里看不到”就判定缺失。

解析顺序：

1. 若执行上下文已有本场会话保存的真实 ID，原样复用。
2. 否则先运行：
   `python3 __SKILL_DIR__/../../scripts/picset_client.py host-conversation-id`
   （电商子 Skill 目录为 `__SKILL_DIR__`；其他 Skill 用同一相对路径定位该脚本，或直接读环境变量。）
3. 成功时 stdout JSON 的 `conversation_id` 即宿主 ID；原样写入工具参数。
4. 仅当上述步骤仍拿不到时，才说明无法打开画布并跳过画布步骤（本地交付仍有效），**不虚构**。

| 来源 | 是否可用作 conversation_id |
| --- | --- |
| `CODEBUDDY_CONVERSATION_REQUEST_ID`（`host-conversation-id` 读取） | ✅ 对话级，本场稳定 |
| `CODEBUDDY_CONVERSATION_MESSAGE_ID` | ❌ 每条消息变化 |
| `CODEBUDDY_SESSION_ID` / `CLAUDE_SESSION_ID` | ❌ Agent 进程级，非用户对话 |

调用前注入字段名：

| 工具 | 参数名 |
| --- | --- |
| `open_agent_canvas` / `open_agent_pricing` | `conversation_id`（亦接受 `conversationId`） |
| `generate_agent_canvas_image` / `get_agent_canvas_image_status` | `conversationId` |
| `insert_agent_canvas_image` / `replace_agent_canvas_image` / `get_agent_canvas_state` | 优先 `agentCanvasSessionId`；若宿主吞掉了结构化返回、手里没有会话 ID，可改传 `conversation_id` / `conversationId`，服务端按对话复用会话 |

### 保存 open_agent_canvas 返回的会话 ID

`open_agent_canvas` 成功时，`content` 文本是 JSON，至少包含：

- `agentCanvasSessionId`（后续插入/替换/读状态优先用这个）
- `conversationId`

宿主若只把 `content` 文本交给 Agent，仍能从该 JSON 读出会话 ID。`ticket` / `functionsUrl` 只在 `structuredContent`（给面板 UI），不要向用户复述。若文本里也丢了会话 ID，插入/读状态时回退传同一 `conversation_id`。

---

## 一、何时用画布 / 何时用套图 / 何时用单图 / 何时用充值

**复刻优先**：明确按风格参考图复刻自己的商品时，含“复刻一张淘宝主图”，先交给 [风格复刻 Skill](../picset-style-replicate/SKILL.md)。缺素材先补素材，不回退电商或单图。仅“参考图片”或“改风格”不足以判定商品复刻，无法区分时先澄清；以下电商与编辑规则仅用于普通非复刻需求。此规则也适用于画布入口被直接触发。

| 用户意图 | 正确路径 | 禁止 |
| --- | --- | --- |
| 明确商品风格复刻（含一张电商主图） | 风格复刻 Skill / [复刻共享手册](./style-replicate-playbook.md) | 不得因用途是主图而切回普通电商生成 |
| 普通已有商品图的主图/详情/套图/Listing/A+（**含一张主图或一张详情图**） | 电商套图 Skill / [共享执行手册](./execution-playbook.md) | 不得用单图工具或 Canvas 冒充上架套图；**哪怕只有一张也必须走套图** |
| 独立创意单图/概念图/插画/示意图/logo/场景图等非电商上架图 | 单图文生图/图生图 Skill / [单图共享手册](./single-image-playbook.md) | 不得调用 `generate_commerce_images`；不得先走套图报价 |
| 基于已有图做编辑（换背景/改风格/加元素等，非电商上架图） | 单图文生图/图生图 Skill（图生图） | 不得走套图链路；不得用 Canvas 代替编辑 |
| 打开画布 / 把生成结果放入画布 / 查看画布状态 | Agent Canvas Skill / 本手册 | 不得编造 session / conversation id |
| 积分不足 / 用户要充值 | [连接器充值手册](./connector-pricing-playbook.md) → 生成前用 `get_user_credits` 校验；不足或主动充值时 `open_agent_pricing` | 不得向用户展示充值 URL / ticket；不得编造套餐价目 |
| 把已有 URL 图放入画布 | `insert_agent_canvas_image` / `replace_agent_canvas_image` | 不得把 ticket 当图片 URL |
| 用户在画布改完后把图传回对话 | 画布→对话（宿主投递，不经过 MCP） | 不得调用 `send_canvas_image_to_agent`（已废弃） |

---

## 二、画布承接流程

先确认结果来源及是否已经写回。

- **单图**：成功查询已由服务端将插图命令入队，不重复插入；成功后只打开画布。
- **电商套图 / 风格复刻**：`present_files` 交付成功后必须自动打开画布，再**校验**画布是否已有本批图；宿主推送是首选写入路径，但**不是唯一路径**——推送未到位时必须兜底 `insert`。
- 用户明确要求替换特定图片、或把**未**经本场交付的已有 URL 放入画布时，走插入/替换。

### 防重复写入（硬规则）

| 场景 | 允许 | 禁止 |
| --- | --- | --- |
| 电商 / 复刻刚完成 `present_files`，且 `get_agent_canvas_state` 已含本批稳定编号 | 只保证面板打开；不再 `insert` / 不带 `initial_images` | `initial_images` 带上本批 M/D/R；对本批已存在的图再 `insert` |
| 已 `present_files`，但 `get_agent_canvas_state` 显示画布无本批图（`imageCount=0` 或 `imageIds` 缺本批编号） | 对每张**缺失**的成功图 `insert_agent_canvas_image`（每张新 UUID v4 `request_id`） | 反复空开 `open_agent_canvas` 指望宿主推送再来一次；用 `initial_images` 塞本批图 |
| 单图成功查询后 | 只调 `open_agent_canvas`；写回已由服务端入队 | 再手动 `insert` 同一张结果图（除非校验确认画布仍无该图且用户要补） |
| 用户要「把这张 URL 放进画布」且本场未交付推送 | `insert_agent_canvas_image` | 同时再用 `initial_images` 塞同一 URL |
| 用户要替换画布里某一张 | `replace_agent_canvas_image`（需真实 `targetImageId`） | 虚构 id；用 `open`+`initial_images` 冒充替换 |

**已出现重复时**：MCP **无 delete 工具**。若面板能提供重复图的 `targetImageId`，用 `replace_agent_canvas_image` 换成另一张有效图；拿不到 id 则向用户说明无法按工具精准去重。不得为「重建干净会话」擅自改写宿主 `conversation_id`。

### 交付后打开 + 校验 + 兜底插入（电商 / 复刻必做）

`present_files` 完成后、最终文字总结前（至少一张成功图时）：

1. 按「宿主 conversation_id 解析」取得真实 ID。
2. 调用 `open_agent_canvas`（**`initial_images` 省略或 `[]`**），从返回文本 JSON 保存 `agentCanvasSessionId`。
3. 调用 `get_agent_canvas_state`（传 `agentCanvasSessionId` 或同一 `conversation_id`）。从返回文本/`structuredContent` 读取 `imageIds` / `imageCount` / `images`。
4. 对照本批成功稳定编号（如 `M1`、`D1`、`R1`）：
   - **已全部出现在 `imageIds` 中**：跳过插入，只确保面板已打开。
   - **缺失任一张**：视为宿主推送未到位；对每张**缺失**图调用 `insert_agent_canvas_image`：
     - `agentCanvasSessionId` = 上一步会话 ID
     - `image.url` = 服务端 `image_url`
     - `image.id` = 稳定编号
     - `request_id` = **新生成**的 UUID v4（每张一个，绝不复用生成任务 `request_id`）
   - 插入后可再调一次 `get_agent_canvas_state` 确认。
5. 仍无法取得 `conversation_id` 时跳过画布步骤并说明；本地交付仍有效。

说明：`get_agent_canvas_state` 汇总 MCP 插入命令与已绑定项目快照中的图片 id；纯宿主内存推送若未落库可能仍显示为空——此时按第 4 步兜底插入，优先保证画布有图。重新打开画布时，launch 会带 `restoreCanvasSnapshot: true` 并从已绑定 `sourceProjectId` 恢复 DB 快照，避免空面板把已落库内容盖掉。

手动插入/替换前须有真实 `agentCanvasSessionId`；未知时，按上文「宿主 conversation_id 解析」取得真实 `conversation_id` 后打开/复用画布并保存返回值。缺少真实标识时停止画布步骤（本地交付仍有效），不虚构。随后按以下规则调用：

- **画布命令幂等键**：每个新的手动插入或替换操作保存一个新的 UUID v4 作为 `request_id`，不复用生成任务的 ID。每张图片分别生成命令 ID；不同图片、目标、操作或会话不得共用同一命令 ID。
- **精确重放**：同一命令提交中断/结果不明时，恢复原命令 ID 与全部原参数（会话、操作、image 的 id/url/prompt、targetImageId），最多原样重放一次，不换 ID 补插；无法恢复原参数时先核对，不能猜测。保存字段的省略状态，重放时也不擅自补字段。
- **生成与查询标识不变**：新的画布命令 ID 只用于 `insert_agent_canvas_image` / `replace_agent_canvas_image`，不替换生成或状态查询的 `request_id`，不重新生成收费图片。
- **冲突处理**：`COMMAND_IDEMPOTENCY_CONFLICT` 时停止并核对已有命令与用户意图，不自动换 ID 绕过冲突或重复插入；确认是新的用户操作后，才按新命令处理。
- 单图专用状态查询使用原生成 ID 自动入队属于服务端行为；不要为了这次自动写回自行改 ID。后续用户要求替换时才创建新的手动画布命令。

### 2.1 插入新图

调用 `insert_agent_canvas_image`，传入：
- `agentCanvasSessionId`：当前画布会话 ID
- `request_id`：本次插入命令保存的 UUID v4；每张图片使用不同的新命令 ID，同一插入重放保持不变
- `image`：对象，含 `url`（必填），`id` 和 `prompt` 可选

### 2.2 替换已有图

调用 `replace_agent_canvas_image`，传入：
- `agentCanvasSessionId`：真实目标画布会话
- `request_id`：本次替换的新命令 ID，不复用之前插入或生成的 ID；同一替换重放保持原 ID 与原参数
- `targetImageId`：画布中待替换的目标图片 ID
- `image`：新图片对象，含 `url`

### 2.3 打开画布

调用 `open_agent_canvas`，传入按「宿主 conversation_id 解析」得到的 `conversation_id`（当前对话 ID）。未传 `agentCanvasSessionId` 时服务端按 `conversation_id` 自动开/复用会话。成功后从返回文本 JSON 保存 `agentCanvasSessionId`（见上文）；不要只依赖宿主是否转发 `structuredContent`。

**交付后打开时**：`initial_images` 必须省略或传空数组；不得把本批 `present_files` / 单图结果塞进 `initial_images`。

触发时机（生成成功后均为必做，不等待用户再说“打开画布”）：
- **单图**：`get_agent_canvas_image_status` 返回 `success` 后立即打开（无 `initial_images`）。
- **电商套图 / 风格复刻**：`present_files` 交付至少一张成功图后，按上文「交付后打开 + 校验 + 兜底插入」执行；若已 `panelActive: true` 且本批图已在 `imageIds` 中，不重复打开、不重复插入。
- **用户主动要求**：用户要求打开画布查看或继续编辑时同样调用（无必要不带 `initial_images`）。

### 2.4 panelActive 判断

- `writeback.status: enqueued` 只表示命令已入队，不代表已展示；`panelActive` 也不是图片已显示或命令已消费的证明。
- 任一生成能力成功后：若已返回或已知 `panelActive: true`，跳过重复调用 `open_agent_canvas`；否则必须调用一次打开画布。**不以 `initial_images`「确保显示」。**
- 纯查看/兜底场景：`panelActive: false` 且宿主没有打开工具结果返回的 UI 时，才可使用同一个 `conversation_id` 调用 `open_agent_canvas` 兜底。

---

## 三、套图与单图结果写回画布

- **电商套图**：`present_files` 交付成功图后**必须**按第二节「交付后打开 + 校验 + 兜底插入」执行。禁止交付时用 `initial_images` 批量塞图；仅当 `get_agent_canvas_state` 确认本批图缺失时才 `insert`。全部失败或无成功图时不打开。解析失败时跳过画布步骤并说明；本地交付仍有效。
- **单图**：成功查询负责自动写回入队，不重复插入；**成功后必须按 2.3 自动打开画布**（无 `initial_images`）。还没有成功查询证据时回到单图能力查询原任务，不用插入代替查询。
- 用户明确要求把单图结果替换到画布特定旧图时，保存新的替换命令 ID 和真实 `targetImageId`；同一替换重放保持原参数。生成与查询继续使用原请求标识。
- **风格复刻**：本地 `present_files` 交付成功后规则同电商套图（打开 → 校验 → 缺图再 insert）。用户要求把新结果替换画布旧图时，用真实 `targetImageId` 做替换；保留原生成任务与 R 编号。
- 仅报告真实生成与可确认的展示状态，不把 `enqueued` 或面板活跃说成图片已展示。

---

## 四、画布 → 对话

用户在画布上点击「加入当前对话」时，面板把选中图投到宿主输入框（下一条消息附件），**不经过任何 MCP 工具**。

- Agent 不必触发；收到带图消息即作修改上下文，勿再调工具或索要地址。
- `send_canvas_image_to_agent` 已废弃，不得调用。该工具只回显入参，不会向对话推送任何内容，仅为兼容旧客户端保留。

---

## 五、画布工具速查

| 工具 | 用途 |
| --- | --- |
| `open_agent_canvas` | 打开/复用画布 Panel |
| `get_agent_canvas_state` | 读取会话摘要与 `imageIds`（交付后校验） |
| `insert_agent_canvas_image` | 插入图片到画布 |
| `replace_agent_canvas_image` | 替换画布中目标图片 |

> 注 1：`generate_agent_canvas_image` 和 `get_agent_canvas_image_status` 属于单图文生图/图生图能力，详见 [单图共享手册](./single-image-playbook.md)，不在本画布手册范围内。
> 注 2：`open_agent_pricing` 属于连接器统一充值面板，详见 [连接器充值手册](./connector-pricing-playbook.md)，不在本画布手册范围内。
