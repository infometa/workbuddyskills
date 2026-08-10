# 运维专家 · MCP 协议参考（已启用）

> 本文件是 `skillhub-ops-expert.md` 的协议细节下沉——步骤 0（需求查询）与步骤 5（提交）涉及的 MCP 工具入参/出参/状态机/错误码定义均在此维护，主文档只保留调用步骤和处置逻辑，不重复贴协议全文，避免协议更新时两处漂移。协议来源：《WorkBuddy 专家团 MCP Server》使用文档（测试环境，2026-07 版）+ 实测校验（2026-07-24，直连测试环境 endpoint 逐个工具验证）。**以下字段/取值均为文档原文或实测确认，禁止 Agent 自行编造未写明的具体数值（如频率限制的具体阈值，文档未给出，不得杜撰"每天1次"之类的数字）。**

## 零、⚠️ MCP 工具调用的响应信封结构（红线，所有工具通用，必读）

**下文各工具的"响应字段"表述的都是业务字段本身，不是顶层 JSON 结构**——真实的 `tools/call` 返回是标准 MCP 信封包装，业务数据/错误信息藏在信封内部固定位置，**直接在顶层找 `requirements`/`submission_id`/`status` 等字段是找不到的**：

**成功时**：
```json
{
  "result": {
    "content": [{"type": "text", "text": "list_requirements succeeded"}],
    "structuredContent": { "requirements": [ /* 真实业务数据在这里 */ ] }
  }
}
```
- `content[0].text` **只是一句简短确认文案**（如 `"xxx succeeded"`），**不含**任何可解析的业务数据，**禁止**把这句话当作"查询结果"来判断有没有数据
- **真实业务字段全部在 `result.structuredContent` 里**，下文各工具表格列出的字段（`requirements`/`next_cursor`/`submission_id`/`upload_url`/`status` 等）都是 `structuredContent` 内部的键，取值前必须先取到 `result.structuredContent`，再从里面按字段名取值

**失败时**：
```json
{
  "result": {
    "content": [{"type": "text", "text": "SUBMISSION_NOT_FOUND"}],
    "isError": true
  }
}
```
- `result.isError: true` 时，**没有 `structuredContent`**，此时 `content[0].text` 就是错误码字符串本身（下文 §六 错误码表列出的那些值），直接按该字符串匹配错误码表
- 判断一次调用成功还是失败，**先看 `result.isError` 是否为 `true`**，不要用"有没有拿到某个字段"去猜

⚠️ **红线**：**任何一次工具调用后，必须完整检查 `result.structuredContent` 是否存在业务字段，不能只看 `content[0].text` 的文案就下结论**（事故详情见 `skillhub-incident-log.md` INC-01）。

## 一、连接器基础信息

- 连接器 id：`ssvSkillHub`（对应插件根目录 `.mcp.json` 的 server key，**唯一，不可改名**）
- **鉴权**：MCP 控制面**统一使用固定 Bearer Token 鉴权**，所有 MCP 请求（`initialize`/`tools/list`/`tools/call`）必须携带 `Authorization: Bearer <MCP_AUTH_TOKEN>`——该固定 Token 已直接写入插件根目录 `.mcp.json` 的 `mcpServers.ssvSkillHub.headers.Authorization`，由系统自动带上，**运维专家/主理人无需也不应再手动拼接此 Header 或在对话中提及该 Token**；缺失/格式非法/Token 不正确时服务端返回 `HTTP 401 Unauthorized`——遇到此错误直接回报主理人"MCP 鉴权失败，需核对 `.mcp.json` 中固定 Token 是否正确/环境是否匹配"，不要自行降级为无鉴权重试。
- `upload_token`（`request_upload` 返回的短期 capability）与上述固定 Bearer Token 是**两个完全不同层级的凭证**：固定 Token 用于 MCP 控制面鉴权（`tools/call` 等），`upload_token` 仅用于「上传文件」这一步 HTTP POST 的 `Authorization: Bearer {upload_token}`，**不能互相替代**，也不能拿 `upload_token` 去调用其他 MCP tools。
- **调用方必须以运行时 `tools/list` 返回结果为准**：功能开关关闭时，对应工具或可选参数不会出现在 schema 中，不要假设某工具/参数一定存在；未识别的工具、参数、状态或返回字段应按向前兼容方式处理，**不要推断为成功**
- 当前测试环境实测 `tools/list` 只声明 3 个工具：`list_requirements` / `request_upload` / `get_submission_status`（`get_submission_status` 的 `inputSchema` 里 `submission_id`/`wb_user_id` 均为 `string` 类型，与下文一致）

## 二、list_requirements（查询建设中需求）

分页查询当前处于建设中的 Skill 需求，用于「从需求库领取」入口（`skillhub-ops-expert.md` 步骤 0）。

| 参数 | 必填 | 约束 | 说明 |
|---|---|---|---|
| cursor | 否 | 非空 opaque string | 上一页返回的 `next_cursor`；首请求不传 |
| limit | 否 | 1-100 | 默认 20 |

`structuredContent` 内的业务字段（**注意：要先取 `result.structuredContent`，不是顶层**，见 §零）：

```json
{
  "requirements": [
    {
      "requirement_id": "123456789012345678",
      "problem_description": "需要解决的问题",
      "expected_effect": "期望达到的效果",
      "expected_completion_limit": "7d",
      "created_at": "2026-07-24T01:02:03Z"
    }
  ],
  "next_cursor": "<OPAQUE_CURSOR>"
}
```

- `next_cursor` 缺失表示没有下一页；**调用方不得解析、修改或持久依赖 cursor 内部结构**
- 本团队当前实现：只调用一次、只展示首页（`limit=20`，不传 `cursor`），不做"查看更多"翻页交互；`structuredContent.requirements` 为空数组时才如实告知用户"当前暂无可领取的建设中需求"，并引导转入标准需求描述流程（`skillhub-manager.md` Phase 1）——**判断"是否为空"必须依据 `structuredContent.requirements` 这个数组本身，不能依据 `content[0].text` 的文案**
- 实测已确认该工具真实返回数据示例（测试环境，2026-07-24）：`structuredContent.requirements` 含 2 条记录，字段名与上表完全一致

## 三、request_upload（申请上传地址）

| 参数 | 必填 | 约束 | 说明 |
|---|---|---|---|
| skill_name | 是 | 非空字符串 | 技能名称 |
| skill_md5 | 是 | 32 位小写十六进制 | `skill.zip` 的 MD5（脚本算出，禁止 AI 口算/编造） |
| material_md5 | 是 | 32 位小写十六进制 | `material.zip` 的 MD5 |
| wb_user_id | 是 | 非空字符串 | WorkBuddy 用户声明 |
| idempotency_key | 是 | `[A-Za-z0-9._:-]{1,128}` | 同一次业务申请必须稳定复用，**不得每次重新生成** |
| requirement_id | 否 | 无前导零的正十进制字符串 | 若技能源自「需求库领取」入口，传入用户选定的 `requirement_id`；用户自行描述需求发起的技能**不传此参数** |

**idempotency_key 生成规则**：取 `{wb_user_id}:{skill_md5}` 做 SHA256 后取十六进制前 32 位（天然满足字符集约束、同一技能同一次申请稳定不变）。同一次提交申请全程复用同一个 key；**网络超时或响应丢失时用原参数 + 原 key 重试，不要立即换新 key**——换 key 会被服务端当成新申请，无法基于幂等性识别为重复请求。

成功时 `structuredContent`（同 §零 信封结构，非顶层字段）：

```json
{
  "submission_id": "123456789012345678",
  "status": "upload_pending",
  "upload_url": "<UPLOAD_URL>",
  "upload_token": "<SHORT_LIVED_CAPABILITY>",
  "expires_at": "2026-07-24T01:32:03Z",
  "required_parts": ["skill", "material"]
}
```

## 四、上传文件（非 MCP tool，是对 upload_url 的一次 HTTP POST）

```bash
curl -sf -X POST "{upload_url}" \
  -H "Authorization: Bearer {upload_token}" \
  -F "skill=@{skill-name}-v{version}.zip;type=application/zip;filename=skill.zip" \
  -F "material=@{skill-name}-material-{date}.zip;type=application/zip;filename=material.zip"
```

**硬性大小限制（打包环节必须前置校验，见 `scripts/pack_and_hash.sh`，超限不得尝试上传）**：

| 文件 | 最大大小 | 要求 |
|---|---|---|
| `skill.zip` | 10 MiB | 普通可安全解析 ZIP，实际 MD5 必须与申请值一致 |
| `material.zip` | 1 MiB | 普通可安全解析 ZIP，实际 MD5 必须与申请值一致；根目录必须包含 `metadata.md`/`social-value-report.md`/`test-report.md` 三个普通非空文件，**文件名大小写敏感** |

超限直接回报主理人"{skill.zip / material.zip} 大小 {实际值} 超出 {限制值} MiB，需精简后重新打包"，不要尝试上传（必然被拒）。

上传成功响应：`{"status": "review_pending"}`——**只表示制品通过校验、进入待人工审核，不代表审核通过或已在 SkillHub 上架**；此响应体里**没有** `market_url` 字段，**不要凭空脑补一个不存在的字段去回报用户**。此响应是对 `upload_url` 的普通 HTTP POST（非 MCP tools/call），无 `content`/`structuredContent` 信封，按普通 HTTP JSON body 解析即可。

⚠️ **HTTP 429 / `UPLOAD_BUSY` 限频重试**：上传接口返回 `HTTP 429` 或业务错误码 `UPLOAD_BUSY` 时，代表服务端限频繁忙，按指数退避**固定最多自动重试 3 次**（不得无限重试，也不得超过 3 次）；第 3 次重试后仍是 429/`UPLOAD_BUSY` → 视为该通道不可用，直接切换到 `skillhub-ops-expert.md` 步骤 5.5 的问卷兜底通道提交。**重试次数、429 状态本身、以及"已切换问卷通道"这一判断过程，均属内部处置细节，不得出现在任何面向用户的回报文案中**——用户侧只呈现最终结果（提交成功 / 已转由问卷通道处理）。

⚠️ **敏感信息处理红线**：`upload_token` 是短期敏感 capability，**禁止**写入日志、回报文案、`meta.json` 或任何持久化文件；`upload_url` 必须按返回原值使用，**不得**拼接查询参数、替换 host、或跨 submission 复用。

## 五、get_submission_status（查询提交状态）

| 参数 | 必填 | 约束 |
|---|---|---|
| submission_id | 是 | 无前导零的正十进制字符串，最长 20 位 |
| wb_user_id | 是 | 必须与 `request_upload` 时声明值**完全一致** |

**红线：运维专家必须在上传成功返回 `review_pending` 后，主动再调用一次 `get_submission_status` 核实真实状态，才能向主理人回报"提交完成"**——上传接口的成功响应只代表文件已收到并通过初步校验，不是最终结论，直接拿它当"完成"回报属于「禁止假装完成」红线覆盖的行为。

状态机（8 种值，取值位于 `structuredContent.status`，**客户端不得把未知状态自动映射为成功**）：

| status | 含义 | 回报用户的话术方向 |
|---|---|---|
| `upload_pending` | 等待上传两个 ZIP | 需在 `expires_at` 前完成上传，过期需用新 idempotency_key 重新申请 |
| `validating` | 兼容保留的中间状态 | 退避后继续查询，不视为失败 |
| `review_pending` | 自动校验通过，等待运营人工审核 | "已提交，进入平台人工审核流程" |
| `validation_failed` | 文件或每日规则校验失败 | 展示公开失败码，修正后用新 idempotency_key 重新申请 |
| `expired` | 上传 capability 已过期 | 用新 idempotency_key 重新申请 |
| `system_failed` | 系统处理失败 | 稍后重试；反复失败可建议走问卷通道兜底 |
| `review_approved` | 运营审核通过 | "审核通过"，**仍不等于已在 SkillHub 正式上架**，措辞不可越界 |
| `review_rejected` | 运营审核未通过 | 展示允许公开的审核结果，询问用户是否需要整改重新提交 |

⚠️ 实测确认：`submission_id` 不存在时，返回 `result.isError: true` + `content[0].text = "SUBMISSION_NOT_FOUND"`（无 `structuredContent`），按 §六 错误码表处置，不要误判为某种"status"。

## 六、错误码与重试策略

> 判断依据：`result.isError === true` 时，`content[0].text` 即错误码字符串本身（见 §零），按下表匹配。

| 错误码 | 场景 | 处置 |
|---|---|---|
| `INVALID_ARGUMENT` | 字段缺失、格式错误或存在未知字段 | 修正请求，不自动重试 |
| `IDEMPOTENCY_CONFLICT` | 同一幂等键对应不同请求 | 核对调用逻辑，不自动换键 |
| `ACTIVE_SUBMISSION_EXISTS` | 同一用户已有活跃提交 | 等当前提交结束后重试，如实回报主理人 |
| `DAILY_SKILL_LIMIT_EXCEEDED` | 命中同需求或同 Skill 每日限制 | 下一配额日再试（**文档未给出具体数值阈值，不得编造"每天几次"这类数字**，如实告知用户"已达当日限额，请明日再试"） |
| `RATE_LIMITED_DISTINCT_SKILL` | 用户当日总配额已满 | 下一配额日再试（同上，不编造具体额度数字） |
| `REQUIREMENT_NOT_FOUND` | 需求不存在或不可见 | 核对 `requirement_id`，可能需求已被领取/下架 |
| `REQUIREMENT_NOT_BUILDING` | 需求不处于建设中 | 告知用户该需求当前不可申领，建议重新查询列表 |
| `REQUIREMENT_CLOSED` | 需求已关闭 | 不再对该需求重试，建议改走「自行描述需求」标准流程 |
| `SUBMISSION_NOT_FOUND` | 提交不存在或用户声明不匹配（**已实测确认此错误码真实存在**） | 核对 `submission_id` 和 `wb_user_id` |
| `SERVICE_BUSY` / `UPLOAD_BUSY` | 服务并发保护 | 指数退避，复用原请求（原 `idempotency_key`） |
| `DEPENDENCY_UNAVAILABLE` | 依赖暂时不可用 | 指数退避；状态不确定时先调用 `get_submission_status` 查询再决定是否重试 |
| `UPLOAD_EXPIRED` | 上传 capability 已过期 | 用新 `idempotency_key` 重新申请上传 |

**仅对超时、取消、`SERVICE_BUSY`/`UPLOAD_BUSY`、`DEPENDENCY_UNAVAILABLE` 做自动重试（指数退避，且必须确认 upload capability 尚未过期）**；其余错误码属于需要人工/用户介入修正的场景，**不自动重试**。**其中上传文件这一步（§四）命中 429/`UPLOAD_BUSY` 时固定最多重试 3 次**，其余场景（如 `request_upload` 阶段命中 `SERVICE_BUSY`）仍按原退避规则重试 1 次。任一次 MCP 调用失败且不在"可自动重试"范围内，或已达重试上限仍失败 → 直接降级到 `skillhub-ops-expert.md` 步骤 5.5 问卷通道，不做二次尝试；**整个重试与降级判断过程不透出给用户**。

## 七、.mcp.json 配置（项目内已固化于插件根目录，仅供核对，不要重复展开到主文档）

完整字段以插件根目录 `.mcp.json` 实际文件为准（server key 固定为 `ssvSkillHub`，`type: "streamableHttp"`，`url` 为当前环境 endpoint，`headers.Authorization` 固化了当前环境的固定 `MCP_AUTH_TOKEN`，`x-workbuddy.auth.type: "none"` 指的是"用户侧不需要额外走连接授权表单"，与控制面固定 Token 鉴权是两件事）。

连接器随专家包内置声明（插件根目录 `.mcp.json`，属于 WorkBuddy 规范「方式二：兜底读取」，无需在 `plugin.json` 里重复声明 `dependencies.mcpServers`），系统会自动识别并展示连接卡（含上方 `x-workbuddy.displayName`/`description`/`icon`），**用户只需点击连接卡完成授权，无需手动填写地址或连接器名称**——这是相对旧版（无 `.mcp.json` 时代）的重要变化，运维专家不应再引导用户"手动去 MCP 服务管理里添加、名称填 ssvSkillHub"这类操作。

若运维专家发现 `list_requirements`/`request_upload` 等工具在 `tools/list` 中不可见，说明用户尚未点击连接卡完成连接，应回报主理人提示用户先完成连接、再继续对应流程。
