---
name: text-creator
display_name: 文本模型指南
display_name_en: Text Model Guide
description: 通过指导agent智能调度 Deepseek、Kimi、Claude 等顶尖文本模型，按办公任务类型自动匹配最优模型与调用策略，完成周报纪要、合同要点、邮件拟稿、多语言稿件、长报告总结、汇报大纲、多步推理与结构化改写，支持流式输出与超长文档处理。
description_zh: 通过指导agent智能调度 Deepseek、Kimi、Claude 等顶尖文本模型，按办公任务类型自动匹配最优模型与调用策略，完成周报纪要、合同要点、邮件拟稿、多语言稿件、长报告总结、汇报大纲、多步推理与结构化改写，支持流式输出与超长文档处理。
description_en: "Agent routes Deepseek/Kimi/Claude for reports, contracts, emails, multilingual drafts, summaries, structured rewriting."
category: writing
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地文档
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models 与 chat_text
triggers:
- 文本生成
- 写文案
- 文案润色
- 总结
- 改写
- 推理
- 问答
- 分类
- 摘要
- polish
- summarize
- rewrite
---

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token


## 能力范围

AI-HIVE 文本生成 Skill 通过 AI-HIVE Connector 完成端到端文本任务。本 Skill 使用 AI-HIVE Connector 提供的以下工具：

- `get_user_info`：查询当前账户与余额；不接收参数。
- `list_models`：按 `text` 列出当前可用模型及价格快照，返回 `publicModelId` 与 `pricingSnapshot`。
- `chat_text`：使用服务端选定的模型与价格快照调用文本生成；扣费由服务端自动结算。

需要生图、生视频或上传大文件，请分别改用 `image-creator` 或 `video-creator`。

**覆盖场景**：周报纪要润色 / 长报告总结 / 合同要点提炼 / 邮件拟稿 / 评论分类 / 多语言翻译 / 多步推理 / 长文多段生成 / 流式输出。

**典型触发**：当用户说"润色这段周报"、"总结这份报告"、"提炼这份合同的要点"、"帮我拟一封邮件"、"把这条评论分类"、"写一段 200 字会议纪要"、"中翻英/英翻中"、"分三步推理这道题"等任意办公文本生成需求时使用本 Skill。用户只是询问 AI-HIVE 能力、参数、积分或价格时，直接回答，不调用付费工具。


## 调用流程

本 Skill 的标准调用顺序如下。每步有明确的输入与输出；上一步失败时不得跳到下一步。

### Step 0：连接检查
- 用户已通过 AI-HIVE Connector 完成 OAuth CLI 流程（如未连接，引导用户连接）。

### Step 1：账户与模型初查
- 调用 `get_user_info` 检查账户与余额。
- 调用 `list_models(kind="text")` 获取可用模型清单与价格快照。

### Step 2：模型推荐与选派
- 对照 `references/model-scenarios.md` 中各文本模型的擅长场景，结合用户任务的难度、篇幅、语言等特点匹配擅长模型。
- 结合 `list_models` 返回的 `pricingSnapshot`（含 COST_FIRST / SPEED_FIRST / SUCCESS_FIRST 三档计费），权衡效果与成本，向用户说明推荐理由。
- 若用户未指定偏好，默认推荐效果与成本均衡的选项。
- 用户确认 `publicModelId` 与 `routingMode` 后，进入下一步。

### Step 3：构造请求
- 把用户在 `messages` 中表达的内容整理为对话历史。
- 把 Step 1 返回的 `model` 对象（含 `publicModelId` 与 `pricingSnapshot`）作为 `chat_text.model` 入参。

### Step 4：执行
- 调用 `chat_text`，按 `temperature` / `maxTokens` 等参数生成。
- 失败时按 `../references/error-catalog.md` 处理，不重试扣费。

### Step 5：交付
- 把 `content` 完整呈现给用户。
- 若仅是查询类需求（账户余额、可用模型），完成 Step 1 后可直接交付，不需要执行 Step 2-3。

## 适用场景

- 用户希望生成结构化文本，例如问答、摘要、改写、分类、推理或多步规划。
- 用户提供素材只是上下文背景，最终输出仍是文字。
- 用户希望确认账户余额或筛选适合当前任务的文本模型。
- 用户需要多语言生成（中文、英文、小语种）。

## 非适用场景

- 目标是图片或视频；必须切换到 `image-creator` 或 `video-creator`。
- 本地文件路径不可访问、未上传到对话或不在 Skill 可达范围。
- 用户要求绕过积分、版权或安全审核。
- 涉及明显违法、侵权、色情、暴力、仇恨、欺诈或其他敏感内容。
- 用户只是询问"AI-HIVE 能做什么"，并不要求真正生成；直接回答问题，不调用付费工具。

## 事实与合规边界

1. 只使用工具真实返回的 `publicModelId`、`pricingSnapshot`、生成结果与错误代码；不编造积分、模型或任务状态。
2. 不擅自构造或修改 `pricingSnapshot`；最终费用按 AI-HIVE 实际用量与账单计算。
3. 不静默切换用户选定的模型或参数；余额不足或模型下线时返回错误并给出下一步。
4. 不宣称对版权、商标或肖像权作法律判定；不索要、记录或写入用户 Token。
5. 对未成年人、裸露、暴力、仇恨与违法内容采取保守判断；无法确认合规时停止创建并说明原因。
6. Token 只在 AI-HIVE Connector 凭证设置中填写，不得在对话中粘贴。

## 输入检查

正式调用前逐项确认：

1. 明确文本目标类型、目标语言、长度范围、输出格式（Markdown/JSON/纯文本）。
2. 本地素材必须来自用户主动选择的文件，不读取非授权文件。
3. 调用 `get_user_info` 检查余额；不足时直接提示充值。
4. 调用 `list_models` 选定模型并保留服务端返回值，不在客户端改写。
5. 用户对措辞、语气、规避词或受众有要求时合并到 `messages`，不得静默丢弃。
6. 用户未给定格式时，先询问结构化输出要求，不自行选择。

## 调用示例

> 全部示例均基于上文"输入检查"，遵循 `../references/tool-catalog.md` 与 `../references/error-catalog.md` 的口径。
> 用户表达 → AI 的多步行为 → 输出。

### 示例 1：周报总结

**用户表达**：把这份周报总结成 3 条要点。

**AI 行为**：
1. 用户已把周报内容作为对话上下文。调用 `get_user_info` 检查余额。
2. 调用 `list_models(kind="text")` 获取可用文本模型与价格快照。
3. 对照 `references/model-scenarios.md`，长文摘要推荐 kimi-k2.6（长程）或 deepseek-v3.1-fast（快速），结合 `pricingSnapshot` 权衡后向用户说明推荐理由；用户确认 `publicModelId` 与 `routingMode`。
4. 构造 `messages`，包含周报原文 + "请总结为 3 条要点"。
5. 调用 `chat_text` 拿到总结。

**输出**：
- 模型与参数：服务端实际采用值
- 摘要：完整的 3 条要点
- 下一步：等待用户确认、改写或保存

### 示例 2：余额查询（只读）

**用户表达**：看下我的 AI-HIVE 账户余额。

**AI 行为**：
1. 直接调用 `get_user_info`。
2. 按 `../references/error-catalog.md` 的脱敏规则遮盖余额以外的无关字段。

**输出**：
- 账户：xxxx
- 余额：x.xx 元
- 下一步：等待用户确认

### 示例 3：余额不足

**用户表达**：帮我写一段产品文案。

**AI 行为**：
1. `get_user_info` 显示余额不足 → 收到 `INSUFFICIENT_BALANCE`。
2. 不重试扣费，也不调用 `chat_text`。
3. 引导用户在 AI-HIVE 完成充值，充值后再调用。

**输出**：
- 错误码：`INSUFFICIENT_BALANCE`
- 下一步：充值后重试

## 工具参数

### `get_user_info`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| — | — | — | 不接收任何参数；返回账户与余额信息 |

### `list_models`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `kind` | string | 可选 | `"text"` | 资源类型；本 Skill 仅关心 `"text"` |
| `cursor` | string | 可选 | 空 | 分页游标 |

### `chat_text`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models` 的模型引用，含 `publicModelId` 与 `pricingSnapshot` |
| `messages` | array | ✅ | — | 对话历史与本轮输入；不允许伪造系统或用户消息 |
| `stream` | boolean | 可选 | `false` | 是否走流式响应 |
| `temperature` | number | 可选 | 服务端默认 | 越高越发散 |
| `maxTokens` | integer | 可选 | 服务端默认 | 单次输出最大 token 数 |

## 费用授权

- `chat_text` 调用即按服务端计费，无需额外授权步骤。
- 失败、被拒绝或余额不足时不重试扣费，只返回错误并询问用户下一步。
- 用户修改模型、消息、`temperature` 或 `maxTokens` 后必须重新调用，不复用旧扣费配额。
- 模型暂时下线时返回 `MODEL_UNAVAILABLE`，建议用户改用其他模型。

## 状态与错误处理

- 成功：返回 `content` 字段或流式片段；流式时按 SSE 拼装后呈现给用户。
- 服务端 5xx：返回 `errorCode` 与 `errorCategory`；可建议用户稍后重试，不在客户端自动重试扣费。
- **鉴权失败 / 连接过期**：WorkBuddy → Connector 设置 → 找到 AI-HIVE → 点击"重新连接" → 完成浏览器 OAuth 流程；如仍失败，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token → 重新发起授权
- **AI-HIVE 账户无余额**：返回 INSUFFICIENT_BALANCE，引导用户在 ai-hive.iclip.cn 完成充值后再试
- **AI-HIVE 服务端错误**：按 `error-catalog.md` 处理，不自行重试扣费

- 模型不存在或下线：返回 `MODEL_UNAVAILABLE`，不自动改用其他模型替代。
- 超时或网络不明：保留工具原始错误，不声称已部分完成。
- 流式中断：只返回已接收的片段，不得臆测后续内容。

## 输出模板

### 成功

- 模型与参数：服务端实际采用值
- 价格（如有）：仅服务端回写时显示
- 内容：完整文本或分段引用
- 下一步：等待用户确认、改写或保存

### 失败

- 错误码：`errorCode`（安全展示）
- 错误分类：`errorCategory`
- 原因摘要：工具给出的可读描述
- 下一步建议：充值、改连 Connector、切换模型或稍后重试

### 部分失败

- 已成功片段：完整呈现
- 失败段：错误码与时间戳
- 不得为失败段落猜测内容
