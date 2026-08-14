# 游戏创作、质量与复用
## 新游戏

先调用 `salesnail_get_product_context`，以 `content[0].text` 中完整产品说明的“复杂 B2B 大客户战略沙盘、信息不对称、团队销售、三轮资源取舍”为设计边界。工具不可用时才读取 `salesnail://product/overview/zh-cn`。不要把游戏生成成话术问答、CRM 流程或通知工具。

依次调用：模板列表 → 设计 Schema → 设计校验 → 启动生成 → 轮询任务 → 读取游戏 → 质量审计。

常规商务游戏默认 `decisionMakerCounts=[5,3,3,3,3]`，预期五个商机和 22 个 NPC。只有用户明确要求其他结构时才调整。

生成失败或取消后使用 `salesnail_retry_job`，不要用新的随机参数重复启动同一意图。

## 游戏修改

先调用 `salesnail_get_game`。

### 创意卡牌

先调用 `salesnail_get_product_context` 取得完整产品说明；工具不可用时才读取 `salesnail://product/overview/zh-cn`。确认卡牌是沙盘中的销售动作和资源取舍机制，而不是任意自动化脚本或外部通信能力。

WorkBuddy 里的大模型只负责把用户的人话整理为 `CardIntent`，不得直接推断或填写 `isNpc`、`textType`、`useTarget`、通用规则组等遗留字段。固定流程：

```text
salesnail_get_product_context
salesnail_get_card_authoring_capabilities
salesnail_get_game
只根据本轮用户原话整理 CardIntent；有关键歧义时向用户确认，不调用 preview
salesnail_preview_card_change
向用户说明 summary、assumptions、willNotDo、warnings 和 simulations
用户明确确认
salesnail_apply_card_change
salesnail_get_card_change_operation
salesnail_get_game
```

当前 `CardIntent 1.1` 一次新增一张卡牌，支持四类经过验证的行为：

- `offline_action`：线下纯消耗动作。例如“寻找顾问支持”。系统只扣行动点、记录使用并展示线下说明；不联系讲师、不选 NPC、不产生 IM 对话。
- `internal_action`：团队内部纯消耗动作。例如“召开内部销售会议”或“复盘”。不改变客户、商机或方案状态。
- `customer_relationship`：选择客户并在线下完成关系活动。例如“邀请客户唱卡拉 OK”。必须明确目标人数、行动点、使用次数/轮次、好感度变化和审批方式；不能自行猜测活动一定增加好感度。
- `npc_dialogue`：使用现有 NPC 文本体系的系统对话。只有用户明确需要系统返回 NPC 信息且游戏已有匹配文本时使用。

#### 讲师通信绝对边界

`notify_instructor` 和 `generate_instructor_reply` 当前明确不支持。用户要求系统通知讲师、替讲师生成回复或保证讲师实时看到卡牌时，必须 fail closed，并说明唯一可实现的替代是 `offline_action` / `offline_cost_only`：系统只扣行动点、记录使用并展示“学员在线下联系讲师”的说明。

- 不得把 `npc_dialogue` 或 NPC 预置文本描述成讲师回复；NPC 是游戏中的客户角色，不是讲师。
- 不得把课堂指挥中心、行动日志、审批、广播或“讲师可能看到”描述成通知通道或实时提醒保证。
- 不得暗示 SalesNail 会生成讲师回复，或讲师一定会看到/回答；除非用户另行安排了明确的线下人工流程。
- 只有用户接受“无系统通信、纯线下完成”的边界并补齐点数、次数、轮次等字段后，才能为线下卡牌生成 preview。

#### 本轮原话证据门禁

调用 preview 前，必须按 capabilities 的 `requiredExplicitFields` 逐项检查。本轮用户消息没有明确写出的参数，一律视为未知：

- `provenance.currentUserRequest` 必须逐字保留当前这一轮用户提出卡牌需求的原话，不能改写、扩写，也不能混入之前任务、现有卡牌、范例或模型生成内容。
- `provenance.explicitFieldEvidence` 的每个值必须是从 `currentUserRequest` 逐字复制的短句，并且确实支持对应字段和值。
- 相似卡牌只能用于发现重复风险，不能作为目标人数、点数、次数、轮次、好感度或审批方式的默认值。
- 用户只说“请客户唱歌”时，必须先询问目标人数、行动点、计次范围与次数、可用轮次、好感度变化和审批方式；不得先生成 preview 再让用户整体确认。
- 缺少任一关键字段时，直接向用户一次性列出全部问题并停止。不得用 assumptions、空 evidence、整句模糊需求或“常见配置”代替明确原文。

服务端会验证 evidence 是否逐字存在并能支持对应参数；不满足时返回 `CARD_INTENT_AMBIGUOUS`，必须把 `details.questions` 原样转成业务问题，请用户补充后重新读取游戏并 preview。

以下情况必须提问或拒绝，不得用底层 patch 绕过：

- 用户没有说明客户活动是否影响好感度、选几位客户、是否审批或消耗多少点。
- 用户要求通知现场讲师、生成讲师回复、自动修改商机/方案、执行任意脚本或数据库操作。
- 用户要求编辑/删除现有卡牌、创建任意规则组；当前语义能力只支持新增，需明确说明边界。
- preview 返回 `CARD_INTENT_AMBIGUOUS`、`CARD_BEHAVIOR_UNSUPPORTED` 或模拟失败。

提交超时或返回 `CARD_CHANGE_STATUS_UNKNOWN` 后，先用原 `clientRequestId` 调用 `salesnail_get_card_change_operation` 查询；也可用完全相同的 `confirmationId + clientRequestId` 重试 apply。不得换 ID 重复创建。

### 其他游戏结构修改

`salesnail_preview_game_patch` 只支持严格字段的：

- update_game
- add_round / update_round
- add_npc / update_npc
- add_chance / update_chance

不支持卡牌、卡牌规则或删除操作。优先一次确认一个聚焦变更；跨实体操作不是数据库事务。

## 质量和上架

上架前调用 `salesnail_audit_game_readiness`。阻断项包括结构缺失、NPC/卡牌/商机字段不完整、语言泄漏、不安全材料、名称/简介/封面缺失。警告也应向用户说明。

首次上架可能收费人民币 9.90 元，必须展示 preview 返回的实际金额。下架通过 game reuse 的 unpublish 操作完成，不删除已有课程。

## 复用和授权

使用 `salesnail_list_game_library` 查看 owned、authorized_by_me、shared_with_me、template 和 copied 游戏。

复制后 MCP 会识别新游戏并尽量修复缺失 NPC 头像。分享、授权、修改期限、撤销授权和下架均先调用 `salesnail_preview_game_reuse`。
