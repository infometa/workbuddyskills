---
name: picset-agent-canvas
description: "Picset Agent Canvas（万能画布）：跨宿主原生画布，负责承接 Agent 生成的图片、用户在画布上修改后将图片返回给 Agent。画布不负责图片生成（生成由电商套图、单图文生图/图生图或风格复刻完成），也不负责充值（充值由连接器统一充值面板 open_agent_pricing 处理）。"
---

# Picset Agent Canvas

跨宿主原生画布能力入口。默认使用简体中文。

## 职责与边界

负责：
- **承接 Agent 生成的图片**：供用户查看和编辑电商、独立单图或复刻结果；单图由服务端自动入队，电商与复刻在交付后自动插入；替换特定图片仍按用户要求执行。
- **用户修改后返回图片到 Agent**：用户在画布上点击「加入当前对话」时，画布把选中图投递到宿主输入框，成为下一条消息的图片附件，Agent 收到后可继续编辑。

**复刻优先**：明确按风格参考图复刻自己的商品时，包括“复刻一张淘宝主图”，交给 [风格复刻 Skill](../picset-style-replicate/SKILL.md)。缺素材先补素材，不回退电商或单图。仅“参考图片”或“改风格”不足以认定商品复刻，无法区分先澄清。即使本画布入口被直接触发，也先执行该规则。

**不负责**：
- 图片生成——普通非复刻的电商主图/详情/套图/Listing/A+ 由 [电商套图 Skill](../picset-commerce-image-suite/SKILL.md) 完成；独立创意单图/图片编辑由 [单图文生图/图生图 Skill](../picset-single-image-generation/SKILL.md) 完成。
- 单图文生图/图生图的生成流程——详见 [单图共享手册](../shared/single-image-playbook.md)。
- 充值套餐面板——积分不足或用户要充值时，由连接器统一充值面板处理，详见 [连接器充值手册](../shared/connector-pricing-playbook.md)，工具为 `open_agent_pricing`。

细则与工具契约一律按 [Agent Canvas 共享手册](../shared/agent-canvas-playbook.md) 执行，本 Skill 不重复展开。

## 画布承接流程

先确认结果来源：单图成功查询已自动入队，不重复插入；**电商或复刻在 `present_files` 交付成功后必须打开画布，再 `get_agent_canvas_state` 校验；缺本批图时兜底 `insert`（禁止交付时用 `initial_images`）**。替换特定图片、或放入本场未交付的 URL 才走手动画布操作。手动操作前没有已知画布会话时，先按 [Agent Canvas 共享手册](../shared/agent-canvas-playbook.md)「宿主 conversation_id 解析」取得真实 ID 并打开/复用，保存会话 ID；解析失败则停止画布步骤，不虚构。

- **画布命令 ID**：每个新的手动插入/替换操作保存新的 UUID v4，每张图片分别使用独立命令 ID，不复用生成 ID。生成与查询的原请求标识保持不变，不触发重新生图。
- **重放**：同一命令结果不明时，恢复原命令 ID 与全部原参数，最多原样重放一次；不同图片、目标、操作或会话不能共用命令 ID。参数丢失先核对，不猜测、不自动换 ID 补插。
- **冲突**：`COMMAND_IDEMPOTENCY_CONFLICT` 时停止并核对原命令和用户意图，不自动换 ID 绕过；新用户操作确认后才建立新命令。详细字段保存规则按共享手册执行。

1. **新图插入**（校验缺图兜底，或手动 / 非本场交付场景）：调用 `insert_agent_canvas_image`，传入真实 `agentCanvasSessionId`、本次命令的 `request_id` 和 `image`（含 `url`）。
2. **替换已有图**：调用 `replace_agent_canvas_image`，传入 `agentCanvasSessionId`、本次替换的新命令 ID（`request_id`）、真实 `targetImageId` 和新 `image`；不复用此前插入的命令 ID。`targetImageId` 须从面板或用户提供取得（`get_agent_canvas_state` 的 `imageIds` 可辅助核对是否已有图，但不保证返回可替换目标的面板内部 id）。
3. **打开画布**：调用 `open_agent_canvas`，传入真实 `conversation_id`，从返回文本 JSON 保存 `agentCanvasSessionId`；交付后打开时 `initial_images` 必须为空。单图 / 电商 / 复刻生成成功后由各生成能力自动打开；用户主动要求打开时同样调用。若会话 ID 丢失，插入/读状态可回退传同一 `conversation_id`。
4. **校验**：交付后必须 `get_agent_canvas_state`；`imageIds` 已含本批稳定编号则不再 insert。
5. **panelActive 判断**：
   - `writeback.status: enqueued` 只表示已入队，不代表已展示；`panelActive` 也不证明图片已显示或命令已消费。
   - 生成成功后：已 `panelActive: true` 则跳过重复打开，否则必须打开一次。

## 画布 → 对话

用户在画布上点击「加入当前对话」时，面板把选中图投到宿主输入框（下一条消息附件），**不经过任何 MCP 工具**。

- Agent 不必触发任何工具；收到带图消息即作为修改上下文。
- 勿再调用工具或索要图片地址。
- `send_canvas_image_to_agent` 已废弃，不得调用。

## 套图与单图结果写回画布

- 电商套图经 `present_files` 交付后**必须**按 [Agent Canvas 共享手册](../shared/agent-canvas-playbook.md) 打开 → 校验 → 缺图再 insert。
- 单图成功查询负责自动写回入队，不重复插入；**成功后必须自动打开画布**。无成功查询证据时回到单图能力查询原任务。用户要求替换特定旧图时，才创建独立替换命令，生成与查询 ID 不变。
- 风格复刻交付后规则同套图。用户要求替换画布旧图时，用真实 `targetImageId` 替换，不改变 R 编号或原生成任务。
- 不把入队或面板活跃说成已展示；无 delete 工具，已出现的重复图按共享手册「已出现重复时」处理。

## MCP 工具速查

| 工具 | 用途 | 调用阶段 |
| --- | --- | --- |
| `open_agent_canvas` | 打开/复用画布 Panel | 打开画布 |
| `get_agent_canvas_state` | 读取画布状态摘要 | 画布状态 |
| `insert_agent_canvas_image` | 插入图片到画布 | 结果承接 |
| `replace_agent_canvas_image` | 替换画布中目标图片 | 结果承接 |

调用 MCP 工具前，必须使用 `tool_search` 按工具名获取完整参数定义，再按取回的定义发起调用。运行时工具名可能带有后缀，以 `tool_search` 返回的实际名称为准。

> 注 1：`generate_agent_canvas_image` 和 `get_agent_canvas_image_status` 属于单图文生图/图生图能力，由 [单图文生图/图生图 Skill](../picset-single-image-generation/SKILL.md) 调用，不在本画布能力的工具范围内。
> 注 2：`open_agent_pricing` 属于连接器统一充值面板，详见 [连接器充值手册](../shared/connector-pricing-playbook.md)，不在本画布能力的工具范围内。
