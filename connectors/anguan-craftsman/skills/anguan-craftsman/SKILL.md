---
name: anguan-craftsman
display_name: 安管工匠
description: 安管工匠连接器使用说明。接入交通运输企业安全管理平台后，通过自然语言完成培训下发、公告与风险通知、车辆/驾驶员台账、证照到期提醒与检查任务，并支持更换（解绑重连）连接码。所有写入操作不可撤回，推送前必须经用户明确许可。
description_zh: 安管工匠连接器使用说明。接入交通运输企业安全管理平台后，通过自然语言完成培训下发、公告与风险通知、车辆/驾驶员台账、证照到期提醒与检查任务，并支持更换（解绑重连）连接码。所有写入操作不可撤回，推送前必须经用户明确许可。
description_en: Usage guide for the Anguan Craftsman connector. After connecting the transport enterprise safety platform, handle training dispatch, announcements and risk notices, vehicle/driver records, document expiry reminders and inspection tasks in natural language; the connection code can be replaced (unbind and rebind) at any time. All write operations are irreversible and require explicit user approval.
version: 1.0.3
author: 安管工匠
---

# 安管工匠（连接器技能）

接入企业安全管理平台后的能力使用说明。工具清单以 `tools/list` 实时返回为准（随平台版本动态更新），本文件只讲**怎么用对**。

## 前提

- 连接器已连接：用户在连接表单里只填了一项 **连接码**（固定前缀 7 位 + 48 位，共 55 字符）；
- 未连接或报鉴权失败时，提示用户到「连接器管理 → 安管工匠 → 设置」重新粘贴连接码，**不要索要、不要复述连接码**（掩码规则：前 6 后 4）；
- 本连接器是**远程 MCP**（`https://apsc.top/mcp`），没有本地进程，也没有本地文件访问能力。

## 更换连接码 / 解绑重连（支持，按此引导）

**触发**：用户说「换个连接码」「重新配置连接码」「密钥过期了」「解绑」「重新绑定」「重置接入」「我那个码不能用了」。

**事实**：连接码是**一人一码、可随时吊销重发**的凭据；连接器不缓存它，改动后下一个请求就用新码。所以更换 = **改表单字段并保存**，不需要卸载连接器、不需要重新添加、也不需要换连接器。

**引导步骤**（逐句给用户，不要让用户把码发给你）：

1. 打开 WorkBuddy 的**连接器管理**，找到「安管工匠」；
2. 点**设置/编辑**（若当前版本提供**断开连接**入口，先断开再连接，效果相同）；
3. 把「连接码」字段**清空**，粘贴**新的**连接码，保存；
4. **新建一个会话**（工具目录与连接状态在会话里缓存），然后我用 `get_dashboard` 验一次；若返回业务数据即完成。

**你绝不能做的事**：

- 不要在对话里向用户索要连接码，也不要让用户把码贴在聊天正文里（会进聊天记录）；用户主动贴了，提醒他撤回并改用连接器设置填写；
- 不要说「我帮你解绑/我帮你改密钥」——本连接器**无权读写用户本机凭证**，工具目录里也没有改凭据的接口；
- 不要建议删除连接器重装、不要建议改 `source` 或换别的连接器（在本平台这两个不是同一个产品，换过去等于换了账号体系）。

**更换后仍报错怎么办**（按 message 精确处置）：

| message 关键词 | 含义 | 动作 |
|---|---|---|
| 「无效或已失效」（无附加原因） | 新码也无效：可能抄错、或又被重新生成顶替 | 让用户在「企业详情 → AI 接入」重新取一次，注意前 7 位是固定前缀、共 55 字符、无空格 |
| 「该企业已关闭 AI 接入服务」 | 企业总开关被关 | 管理员在 Web 端重新打开，**即时生效** |
| 「IP x.x.x.x 不在白名单内」 | 企业开了 IP 白名单 | 把报错里的 IP 报给服务方登记，即时生效 |
| 更换后**旧**会话短时间内仍能读到数据 | 网关对受管码有约 **5 分钟**缓存（提前 1 分钟刷新） | 属预期残留窗口，最迟约 5 分钟消失；要**立刻**掐断，让管理员关「AI 接入」总开关或轮换凭据，别只重新生成连接码 |

## 能力速查（以 `tools/list` 实时返回为准）

| 类别 | 工具 | 说明 |
|---|---|---|
| 概览与待办 | get_dashboard / get_pending_summary / get_pending_receipts / get_weekly_report / get_assistant_guidance | 首页概览、待办、签收情况、周报、智能建议 |
| 培训 | create_training / list_trainings / list_training_categories / get_training_overview / get_training_detail / get_training_progress | 下发学习任务、查完成率与签字 |
| 培训 AI 提交 | plan_training_ai_submit / execute_training_ai_submit / cancel_training_ai_submit / get_training_ai_submit_status | 批量生成并提交培训内容，**plan → execute 顺序不可颠倒** |
| 公告 | create_announcement / list_announcements | 公告查询；**发布广播全员、不可撤回** |
| 风险 | list_risk_notices / create_risk_notice / get_risk_detail / get_risk_receipts | 按车推送隐患通知（不可撤回）、查签收 |
| 车辆 | query_vehicles / create_vehicle / batch_create_vehicles / get_vehicle_documents / create_vehicle_document | 台账建档、批量建档、证件查询与新增 |
| 驾驶员 | query_drivers / batch_create_drivers / find_driver_by_license / export_driver_roster / get_driver_documents / create_driver_document | 台账、按证件号精确定位、花名册导出、证件管理 |
| 人车关联 | bind_driver_vehicle / unbind_driver_vehicle | 绑定/解绑须先确认车牌与驾驶员姓名 |
| 车辆编组与人员 | list_fleets / list_personnel / list_custom_roles | 编组、人员与角色清单 |
| 检查任务 | create_inspection_task / list_inspection_tasks / list_inspection_items / list_inspection_combos / get_inspection_detail | 安全检查任务下发与跟踪 |
| 入企审批 | list_pending_applications / approve_join_application / reject_join_application / get_invite_link | 入企申请审批与邀请链接 |
| 证照与体系 | get_safety_assessment / get_document_reminders / get_document_reminder_details / get_credit_hours_ranking | 安全评分、证照到期提醒、学时排名 |
| 网页与手册 | get_web_login_url / open_web_page / get_web_manual_index / get_web_manual_section | 免登录网页入口与操作手册 |

> **身份与权限分流**：能力目录由平台按凭据权限下发——读写连接码 **54** 个工具，只读连接码 **36** 个（被过滤的 18 个全是写工具，含 `get_web_login_url`）。工具数变少先确认是不是只读码，属预期。调用返回 403 或「无权限」时，如实说明当前身份不具备该能力，**不要换接口、改参数或反复重试绕行**。

## 参数与返回格式

**参数**以每个工具返回的 `inputSchema` 为唯一权威（含 `required`、类型、`default`、`enum`、上限），本文件不复述全量字段。

**校验分工（决定你要不要自己兜底）**：网关只硬校验**顶层 `required`** 与**数组 `minItems`**（缺字段/空串/纯空白/必填数组给空都会被拦，并在报错里点名）；**类型、`enum`、`anyOf`/`allOf` 二选一、业务规则由后端校验或根本不校验**——不要指望网关兜底，参数写错可能直接落库。

三条通用规则：

1. **清单类取值必须先查**：分类名 → `list_training_categories`；车队名 → `list_fleets`；身份名 → `list_custom_roles`；驾驶员的 `userId` → `query_drivers`。拼错不报错、只会落空（培训/通知已创建但无人可收，且不可撤回）。
2. **分页上限**：`page` 从 1 开始；`pageSize` 各工具上限不同（车辆/统计 20、培训列表 10），超上限会被拒，**不要为了取全量硬抬 pageSize**，改用翻页。
3. **数组参数**可传数组，也可传逗号分隔字符串（网关会归一化）；**必填数组不能传空数组**（等于没给）；非必填数组传 `[]` 视为「本次不用这一路」被放过。

**返回格式**：MCP 标准结果 —— `content[0].text` 是格式化后的 JSON（老客户端只读文本也能用），对象型结果同时给 `structuredContent`。业务失败**不是** HTTP 错误，而是 `result.isError = true`，原因在 `content[0].text` 里（中文）。单个结果文本超过约 90KB 会截断，末尾追加「[输出已截断…]」并带 `_meta.truncated = true`。

**典型调用（只读，可直接执行）**：

| 用户说法 | 调用 | 返回要点 |
|---|---|---|
| 「看看首页概览 / 这周有什么待办」 | `get_dashboard`（无必填） | 各类计数与待办摘要 |
| 「查下张三的证件和培训」 | `query_drivers` 拿 `userId` → `get_driver_documents` / `get_training_progress` | 档案、证件到期、完成率与签字 |
| 「这个驾照号是谁」 | `find_driver_by_license`{"licenseNumber":"…"} | 命中返回驾驶员档案，未命中返回空（如实说查不到） |
| 「有没有证件快过期」 | `get_document_reminders` | 到期/临期清单，**只汇报不推送** |

**典型调用（写入，必须先经用户确认）**：

| 用户说法 | 调用 | 必填要点 |
|---|---|---|
| 「发一份雨季行车安全培训」 | `create_training` | `title` / `content`（富文本 HTML，非纯文本）/ `category`（先查清单）；`targetType` 默认 `all`，选 `driver`/`fleet`/`member` 必须同时给 `targetValue`（driver 传 `userId` **字符串**数组）；`requireSignature` 默认 `true` |
| 「建一个安全检查任务」 | `create_inspection_task` | `title` 必填；`comboKeys` 与 `checklistItems` **二选一**、`vehicleIds` 与 `plateNumbers` **二选一**（工具说明的业务要求，**网关不强校验**，两组都必须人工补齐），否则可能建出无人无项的空任务 |
| 「给全员发个通知」 | `create_announcement` | `title` 必填、广播全员、**不可撤回** |
| 「给这辆车下一条隐患通知」 | `create_risk_notice` | 先 `query_vehicles` 确认车牌与车辆 ID，**不可撤回** |

## 铁律（违者即停）

1. **不可撤回的写入操作**（create_announcement / create_risk_notice / create_training / create_vehicle / bind_driver_vehicle / approve_join_application 等）：先把内容与对象**完整呈现给用户确认**，拿到明确许可再调用；
2. **只查不推**：查到名单（如证件到期、未完成培训）**只如实汇报**，不诱导、不主动问「要不要推送给他们」；
3. **数据边界**：一家企业的数据不出这家企业；跨企业对比类请求拒绝；
4. **不伪造**：查不到就说查不到，禁止用估算或示例数据填充；
5. **报错翻译**：把接口报错翻译成人话，不把原始报错、URL、工具名直接抛给用户；
6. **培训 AI 提交按序执行**：`plan_training_ai_submit` 仅生成方案（无副作用），须把方案完整呈现给用户并取得许可后，方可调用 `execute_training_ai_submit`；
7. **权限失败不绕行**：遇 403 /「无权限」如实说明并停手，禁止换接口、改参数或反复重试绕过校验；
8. **凭据不进对话**：连接码只在连接器设置里填写与更换，不在会话中索要、复述或回显（需要提到时只给前 6 后 4 掩码）。

## 远程形态的已知限制

| 限制 | 正确处理 |
|---|---|
| 读不到用户本机文件（如批量导入的 Excel） | 先让用户把文件上传到平台取得 URL，再传 URL 参数；**不要伪造本地路径** |
| 服务端不能打开用户浏览器 | `get_web_login_url` / `open_web_page` 只把链接原样返回，由对话侧展示给用户点击 |
| 单次结果超过约 90KB 会被截断（`_meta.truncated`） | 缩小查询范围或分页，不要假装拿到全量 |
| 单次请求 30 秒超时 | 超时重试一次仍失败则如实告知并建议稍后再试 |

## 参数闸门与写操作安全

- 必填项缺失、空字符串、纯空白、必填数组为空都会在触达后端前被拒并点名缺哪个字段——补齐后重试是安全的，不算重复下发；
- **参数名拼错不会报错**（未知字段被静默剔除），下发前自行逐项核对字段名；
- 非必填的数组参数留空（传 `[]`）等于「本次不用这一路」，**不要为了凑一项猜一个 ID 填进去**；
- `dryRun` 预检只有 `create_training` 支持；其余工具返回「不支持 dryRun」只是拒做预检，**严禁去掉 dryRun 重试**（会真落库）；
- 写操作返回「执行状态未知」时**严禁直接重发**：先用对应查询工具核实是否已落库，确认未生效才重试一次。

## 常见报错处置

| 报错 | 含义与动作 |
|---|---|
| `-32001` 鉴权失败（连接码无效或已失效） | 连接码被重新生成或吊销 → 请用户在平台「企业详情 → AI 接入」重新获取并粘贴；企业内部关闭了 AI 接入则需管理员重新打开 |
| `-32001` 含「不在白名单内」 | 企业开启了 IP 白名单，把报错里的 IP 报给服务方登记 |
| `-32002` / HTTP 429 | 调用限流，等 60 秒再试，并降低频率 |
| HTTP 413 / `-32600` | 请求体超 256KB，附件先上传取 URL，勿内联 base64 |
| 「当前 AI 连接码为只读权限…」 | 只读码调用了写工具，属正常保护。确需写入 → 让用户在 Web 端「AI 接入」签发读写连接码，不要改参数绕行 |
| 「入参未通过必填校验：…」 | 本次未触达后端、未写入，按点名补齐字段后重试是安全的 |
| `Unknown tool` / JSON-RPC `-32601`、`-32602` | 工具名写错，或当前凭据权限下没有该工具：以 `tools/list` 为准，不要猜别的名字 |
