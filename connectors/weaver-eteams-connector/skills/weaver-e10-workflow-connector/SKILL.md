---
name: weaver-e10-workflow-connector
display_name: 泛微E10流程智能助手
display_name_en: Weaver E10 Workflow Assistant
description: "泛微 E10 流程智能助手：查询待办/已办/我发起/全部流程，查看详情与摘要，处理、批量处理、共享和发起/修改流程。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10/OA 流程智能助手。支持按流程标题/编号/发起时间/完成时间/操作时间/紧急程度/发起人/工作流/表单字段等条件查询待办、已办、我发起和全部流程，支持查看详情、生成摘要、打开流程、同意/提交/批准、退回、转办/委托/转发/抄送/加审、批量提交/置已读/催办/共享/转发/退回，以及发起创建流程和修改已存在流程表单。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10/OA workflow assistant skill. Query pending, done, initiated and all workflows by title/number/time/urgency/initiator/workflow/form fields; view details, generate summaries, open flows, approve/submit, return, transfer/delegate/forward/cc/add review, run batch submit, mark-read, supervise, share, forward and reject operations, and initiate or edit workflow forms. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli workflow --help"
---

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**
认证和登录态只能按共享规则通过 `weaver-work-cli auth ...` 命令判断；禁止直接读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
所有命令通过 `weaver-work-cli --profile eteams --json workflow run <operation>` 执行：**统一用 `--input-json '<json>'` 内联传入**——`planJson`、`filterFields` 这类嵌套结构也一样内联（总量通常只有几百字符，内联完全够用；**不要因为"看着复杂"就去写 JSON 文件**，那会白白多出一次文件写入与一次工具往返）。仅当 JSON 确实很大（几十 KB 级，如超长消息列表）或含难以在 shell 里转义的单引号时，才改写 UTF-8 文件配 `--input <path>`；只有确认当前 shell 能稳定传管道时才用 `--input -`。调用前先按需读取 references 下对应的文件，查参数结构，不要猜字段；**references 是第一信息源**，`weaver-work-cli --profile eteams workflow schema` 是 operation、字段和风险等级的合约来源。
生成或改写的 docs、reference、提示词和命令示例必须同时兼容 Windows 和 macOS/Linux。凡涉及 JSON 输入、用户目录、路径分隔符、文件删除、目录查看或文件比对，必须同时给出 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例；Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 示例不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。
涉及附件、图片、本地文件、远程 URL 文件或文件内容解析的 operation，执行前必须提醒用户：文件内容可能被上传到业务系统、OCR/解析服务，并可能进入当前大模型上下文用于理解和处理；必须等待用户明确确认后才继续。

# 泛微E10流程智能助手

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 适用场景（何时使用本技能）

用户提到待办、已办、我发起的流程、流程详情与摘要、同意/退回/转办/加审等流程操作、批量处理、共享流程、发起创建流程或修改流程表单时，使用本技能。

用户要查组织架构与人员 ID 时转 `weaver-e10-hrm-connector`；查发票、邮件、日程、费控时转对应业务技能。

## 任务入口（每收到用户任务，先按本固定步骤执行）

收到用户任务（查询/查看/操作/批量/共享/发起/修改）后，**不要先推理规划、不要以翻文档代替执行、不要把 references 通读一遍**，按下面两步固定执行：

1. **第一轮就并行发起（关键：不要串行拆成多轮往返）**：在**同一条消息**里同时发出下列调用——
   - Read `../weaver-e10-shared-connector/SKILL.md`（若尚未读过）；
   - `weaver-work-cli --profile eteams --json workflow run workflow.memoryPrompt`——该命令**无入参**，命令形态已给定，**直接执行即可**（仅"非首次对话且距上次成功读取记忆不足 6 小时"时跳过）；
   - **查询类意图**只读 [`workflow-query.md`](references/workflow-query.md) 一份（已覆盖 `workflow.search` 与 `workflow.todoStat`，不要再读其他查询文档）；**但该文件约 105 KB / 820 行、一次读不完**——按它开头的**「分段索引」分次读，单次 `limit` 不超过 150 行**：**首轮并行读契约段两次**（`offset 1 limit 122` 与 `offset 123 limit 122`，已覆盖 Operation、全部输入参数含「大分类判定」、时间条件与「待办时间默认语义」、执行流程），其余章节（`planJson` 编排、汇报式分组骨架、渲染规则与示例）**只在需要的那一刻按索引给出的行区间补读**；查看/操作/批量/共享/发起/修改等意图读对应那一份 reference 即可，不要顺手把查询文档也一起读；
   - **泛化待办查询**（如"今天有哪些待办"）直接 `workflow.search`（category=todo，**不要带 `planJson`/`subCategory`**）——**不要在这一轮先调 `workflow.todoStat`**：模式由 CLI 判定并在返回的 `renderMode` 里给出，未确认前就调 todoStat 在低版本必然失败（报 `todo_stat_requires_smart_mode`）白费一次调用；返回 `renderMode=legacy` 时 CLI 已自带分组统计与卡片，原样渲染即结束，`renderMode=smart` 时才追加 `workflow.todoStat` 做统计规划。
   > 以上调用**互不依赖，必须并行**：串行拆轮会成倍拉长耗时。**实测基准**：一次泛化待办查询全程约 70s，其中**模型轮次占 ~95%**（每轮约 8~25s，主因是模型输出量），CLI 命令本身合计只有 1~2s。**能省一轮就省一轮**——尤其不要为"解析上一轮输出""取流程 ID"另起一轮。
   - **[`workflow-memory.md`](references/workflow-memory.md) 本步不读**——记忆读取的命令形态已在上一行给出（直接执行 `workflow.memoryPrompt` 即可），**记忆保存的规则已在本文件「记忆保存（全局规则）」章节给全**（本轮任务结束时按那一节执行）；只有需要判断"放 `user.md` / `memory.md` / `workflow:{id}` 哪一类"或其它字段细节时，才在需要的那一刻去读它。
   - **读不全就按行段重读源文件，不要去读宿主落盘的临时输出文件**：单次读取过大时宿主会把它落盘并只回一段预览，那段落盘文件（`~/.workbuddy/projects/**/tool-results/**`）**没有读取权限**，去读它必然拿一句 `Permission … has been denied`、白费一轮；正确做法是回到源文件、用 `offset`/`limit` 按行段重读。
2. **执行用户任务**：按下方「选哪个命令」与「处理链」选定 operation 并执行，参数以对应 reference 为准。

> `workflow.memoryPrompt` 返回的 `oaContext` 已含 OA 版本与当前用户身份（岗位/部门/分部），判版本、引用身份直接用它，不要再单独查组织信息。

## 总原则

- **全程中文**；输出时把技术术语翻译成普通用户能看懂的话（命令要求对返回内容原样输出的除外）。
- **列表/详情最终回复 = 原样粘贴命令返回的渲染文本全文，一字不改**：**`workflow.search` 用 `finalMarkdown`**（卡片列表；`smart` 模式无顶部行）、**`workflow.detail` 用 `renderMarkdown`**（该 operation 没有 `finalMarkdown`）——两者不要混用、不要自己拼装；其中禁止出现 `<div>`/`<span>`/`style` 等 HTML 标签。
- 只执行本 skill 列出的 operation，把命令返回的结果、提示、候选**原样呈现**；命令没做的、没返回的、查不到的，反馈用户或停止——**绝不自行发明、探测、绕过**。
- 失败、超时、登录失效、业务错误一律立即停止，不自动重试、不延长等待、不切换地址、不换接口。**例外**：读操作遇登录失效时按 `weaver-e10-shared-connector` 的认证引导处理，认证完成后重放原请求（写操作见「写操作失败处理」）。
- **若决策依据了历史记忆，最终回复要说明；若本轮保存了记忆，要说明会记住什么。**
- **不得写 agent 工具的工作日志/工程日志/对话记录**；**不读取、不处理与本任务无关的工作区引导/身份文件**（如工作区根的引导说明、身份档案等——那是别的流程负责的事，在本轮纠结它只会让任务跑偏并白白多花几秒）；不读取命令源码、不执行调试命令、不使用调试参数。

## 记忆保存（全局规则，每轮任务结束都要执行）

**每轮完整实质任务结束、向用户输出最终回复之前**，必须自行判断本轮是否出现**新的、有价值的语义记忆**（用户**新**澄清/确认了具体工作流、本次**新**表达了字段偏好，或对某字段值有**新**约定；与已有记忆重复的不算）：

- **有** → 组装本轮「用户原始意图 + 澄清过程 + 确认结果」的消息列表，**实际调用** `weaver-work-cli --profile eteams --json workflow run workflow.memoryExtract --input-json '{"msgList":[{"msgRole":"user","msgValue":"…"},{"msgRole":"assistant","msgValue":"…"}],"workflowId":"<已确认的 workflowId，确定时才带>","async":true}'`：
  - **`msgList` 每项的字段名固定是 `msgRole` / `msgValue`**（按对话顺序：user 放用户原话/澄清回复，assistant 放命令返回/你的确认说明），**不要写成 `role` / `content`**；
  - **保存「业务别名 → 工作流」映射时，ID 必须来自本轮命令返回**：`workflow.search` / plan 的 **`cards[].workflowId`**、`workflow.createList` 候选的 `id`、`workflow.todoStat` 的 `countDetails[].workflowId`——拿到就必须把 ID 写进 `msgValue` 的事实句（如「业务别名"问题流程"= 工作流"E10客户问题支持解决流程"，workflowId=1003655203465764898」）**并同时放进入参 `workflowId`**；**不允许只记名称、把 ID 留空**——留空就是「（待确认）」，后续查询只能拿纯名称去试探，多命中还要再澄清一次；
  - `saved:true` → **用自然语言告知用户会记住什么**（如"后续再发起请假流程时会默认按本次偏好（年假）填写"），不展示接口原文；
  - `saved:false` → 按静默失败处理，不告知用户、不重试，直接继续回答用户原本问题。
- **没有** → 不调用 `workflow.memoryExtract`，直接输出最终回复；**不要纠结"一次性原因（如请假事由）是否值得记忆"**。

**硬禁令（违反即为没保存）**：

- **不允许只在思考里写"应该保存记忆"**：判断"有"后必须**真的发出 `workflow.memoryExtract` 命令**，拿到真实 `saved` 结果后再输出最终回复。只在内心说"要保存"而不执行 = 没保存。
- **`workflow.createApply` 成功后不会自动保存记忆**：本次发起的工作流与关键字段偏好，**由你在任务结束时主动调用 `workflow.memoryExtract` 保存**，不要假设命令已代劳。
- 用户澄清后确认的工作流/字段偏好属于典型的"有价值记忆"，**属于要保存的情形**，不要漏。
- **记忆里的别名条目写「（待确认）」时，它是一张待办、不是终态**：本轮只要把该别名唯一解析出了 `workflowId`（**`cards[].workflowId`** 或 `countDetails[].workflowId` 里就有），任务结束时**必须再保存一次把 ID 补上**（口径同上），不要放着不管。

> 本节的规则已足够直接执行；仅当需要判断"放 user.md / memory.md / workflow:{id} 哪一类"或需要其它字段细节时，才去读 [`workflow-memory.md`](references/workflow-memory.md)。

## 路由优先级（先判断是不是流程业务，再选 operation）

流程不是组织、发票或邮件能力。**只要用户的核心对象是待办、已办、我发起的流程、流程详情、流程操作或流程发起，就优先使用 `weaver-e10-workflow-connector`。**

### 明确归 `weaver-e10-workflow-connector` 的高优先级语义

- 待办 / 已办 / 我发起 / 全部流程 / 流程列表 / 我的流程 / 待我处理 / 我审批过的
- 流程详情 / 流程摘要 / 打开流程 / 签字意见 / 流转日志 / 审批记录
- 同意 / 提交 / 批准 / 通过 / 退回 / 驳回 / 转办 / 委托 / 转发 / 抄送 / 加签 / 加审 / 强制收回 / 强制结束 / 意见征询 / 催办 / 删除流程
- 批量处理 / 批量提交 / 批量置已读 / 批量催办 / 批量共享 / 批量转发 / 批量退回
- 共享流程 / 把流程共享给某人或某部门
- 发起流程 / 创建流程 / 提交审批 / 填单 / 起草 / 存草稿
- 修改流程表单 / 改已发起流程的字段

**判定规则：** 用户核心对象是流程实例（request）或流程发起表单时走本 Skill。查询"有哪些流程可以发起"用 `workflow.createList`；查询"我有哪些待办"用 `workflow.search`。涉及"姓名转人员 ID / 组织架构 / 部门岗位"时，人员与组织解析交给 `weaver-e10-hrm-connector`，本 Skill 只在操作流程时消费其返回的人员 ID。

## 选哪个命令

| 想做什么 | 命令 | 按需读取 reference |
| --- | --- | --- |
| 查看可用 operation、字段和风险等级、输出契约 | `workflow schema` | [`workflow-agent-entry.md`](references/workflow-agent-entry.md) |
| 查询待办/已办/我发起/全部流程，按条件筛选，待办智能分组取数 | `workflow run workflow.search` | [`workflow-query.md`](references/workflow-query.md) |
| 待办整体分组计数（智能分组第二步；须先经 `workflow.search` 确认 `renderMode=smart`） | `workflow run workflow.todoStat` | [`workflow-query.md`](references/workflow-query.md) |
| 查看流程完整详情、生成摘要、打开流程、查签字意见/流转日志 | `workflow run workflow.detail` / `workflow.summary` / `workflow.open` / `workflow.requestLog` | [`workflow-view.md`](references/workflow-view.md) |
| 打开 OA 页面（待办/已办/草稿/监控/创建/查看） | `workflow run workflow.pageOpen` | [`workflow-view.md`](references/workflow-view.md) |
| 单条流程操作：同意/提交/退回/转办/委托/转发/抄送/加审/收回/结束/征询/删除/催办 | `workflow run workflow.operatePrepare` / `workflow.operateApply` | [`workflow-operate.md`](references/workflow-operate.md) |
| 批量提交 / 置已读 / 催办 / 共享 / 转发 / 退回（均为单命令，一次调用完成） | `workflow run workflow.batchSubmit` / `workflow.batchRead` / `workflow.batchSupervise` / `workflow.batchShare` / `workflow.batchForward` / `workflow.batchReject` | [`workflow-batch.md`](references/workflow-batch.md) |
| 单条流程共享（人/部门/分部/群组/角色/岗位/所有人） | `workflow run workflow.sharePrepare` / `workflow.shareApply` | [`workflow-share.md`](references/workflow-share.md) |
| 发起/创建流程、填单、存草稿 | `workflow run workflow.createList` / `workflow.createForm` / `workflow.createPrepare` / `workflow.createApply` | [`workflow-create.md`](references/workflow-create.md) |
| 修改已存在流程的表单内容 | `workflow run workflow.editLoad` / `workflow.editPrepare` / `workflow.editApply` | [`workflow-edit.md`](references/workflow-edit.md) |
| 读取用户记忆偏好、OA 版本与当前用户身份；保存本轮语义记忆 | `workflow run workflow.memoryPrompt` / `workflow.memoryExtract` | [`workflow-memory.md`](references/workflow-memory.md) |

处理链：

- 记忆前置：新一轮对话或距上次成功读取记忆超过 6 小时 -> 先执行 `workflow.memoryPrompt`，顺带拿到 `oaContext`（OA 版本 + 当前用户身份），不要单独再查组织信息。
- 查询类意图 -> `workflow.search`。泛化待办查询**先不带 `planJson`/`subCategory` 调一次看 `renderMode`**：`legacy` 直接原样渲染（CLI 自带分组统计，闭环）；`smart` 再 `workflow.todoStat` 统计分组，并**严格按 [`workflow-query.md`](references/workflow-query.md) 的「汇报式分组骨架」+「参与身份 → 分组去向表」划组**，把分组计划打包为一次带 `planJson` 的 `workflow.search`（不要自创分组体系）。
- 查看类意图 -> 优先用列表返回的 `requestId`；只有用户明确指向"第 N 条"时才用 `index`（分组场景加 `group`）定位。
- 单条操作 -> `workflow.operatePrepare` -> 用户确认 -> `workflow.operateApply`。
- 批量处理（提交/置已读/催办/共享/转发/退回）-> **6 个都是单命令**（`workflow.batchSubmit` / `workflow.batchRead` / `workflow.batchSupervise` / `workflow.batchShare` / `workflow.batchForward` / `workflow.batchReject`）：`confirm: true` 与 `requestIds` 在**同一次调用**里传，**不需要先跑 Prepare，也没有 continuation**；目标是范围数据、没有准确 `requestId` 时，先 `workflow.search`（带 `batchType`、`pageSize:100`）取一页，立即用该页 ID 执行，再查再执行、循环到 `total` 归零。
- 单条共享 -> `workflow.sharePrepare` -> 用户确认 -> `workflow.shareApply`。
- 发起流程 -> `workflow.createList` 确认工作流 -> `workflow.createForm` 拿 `context` -> `workflow.createPrepare`（带 `intent`）-> 用户确认 -> `workflow.createApply`（同一 `context`、显式 `intent`、`confirm: true`）。
- 修改表单 -> `workflow.editLoad` 拿 `context` -> `workflow.editPrepare` -> 用户确认 -> `workflow.editApply`。

## 执行原则（减少误路由、误重试和无效消耗）

### 1) 先拿最小必要信息，再执行

- 只是查待办时，直接 `workflow.search`，不要先做全量探查
- 用户已给出流程标题、编号或 `requestId` 时，不要先拉全量列表再本地过滤
- 批量操作的目标已有明确 `requestId` 时，直接把 `requestIds` 传给对应的 `workflow.batch*` 单命令（连同 `confirm: true`），**不要为了"看看哪些能批量提交"先做一次 `--batchType` 查询**（批量门禁按本机查询索引放行，那一次查询不参与放行）；**不要先跑任何 `Prepare`**——6 个批量命令都是一次调用完成，不存在两阶段。
- 查询条件里的名称解析不出唯一对象时，**按 CLI 返回的形态分两种处理**（对齐 V11.3，不要混为一谈）：① **澄清信封**（`ok:true` + `status=NEEDS_CLARIFICATION` + `data.candidates`）——工作流多/零命中、工作流类型/发起人/部门/分部/紧急程度**多命中**、表单字段名或选项值不唯一、字段元数据不可用；**用 `data.candidates` 与用户确认，拿到确认后用 `名称(ID)` 重发同一条命令**，**不要**为了拿候选去调 `workflow.createList`，更不要用 `workflow.createForm`（它会**创建出草稿**）；**不要把它转述成"没有匹配的流程"或"查询结果为 0 条"**。② **`ok:false` + `error.subtype=*_not_found`**——工作流类型/发起人/部门/分部/紧急程度**0 命中**（V11.3 即硬失败，因为放行会静默丢掉该条件返回全量数据）；按 `error.message` 的提示（紧急程度会列出全部可选等级）与用户核对后改用 `名称(ID)` 重发
- 缺少的关键信息（目标流程、接收人、发起工作流）只问一次；能从记忆 `oaContext` 或上下文推断的不要反问
- **查询范围的缺省口径不要反问**：时间词 + 动作词（"本周接收的""今天有哪些待办"等）的默认含义已由 `references/workflow-query.md`「待办时间默认语义」定死，**照表直接执行**；`category` 按该文「大分类判定」定（句中出现"我/我的"或"提交/发起/创建"**不等于** `mine`）；不要因为用户没说"待办/已办"、或没说是发起时间还是接收时间就停下来反问——只有该文所列的三种真歧义才问

### 1.5) 大结果只摘要给用户

- 当前 CLI 的 `--json` 会把完整 JSON envelope 写 stdout；Agent 回复时不要原样粘贴完整 JSON
- 列表默认先取小页，优先 `pageSize=10`；若记忆里的展示偏好另有条数（如"每页 5 条"），以记忆为准；用户没有要求全量时不要自动扫完整数据集
- 需要全量统计时，按 `current` 分页分批读取，只累计任务所需字段和去重键，并报告已读取页数、命中数和是否还有更多
- 超长文本、大数组、详情原始响应或调试 JSON 需要保留时，优先落本地文件并向用户提供摘要和路径

### 2) 已知对象时直达动作

- 已知 `requestId` 或已从列表定位到目标时，直接对目标 operation 执行，不要重复查询
- 单条操作不要用批量能力替代；批量能力只用于用户明确要求处理多条

### 3) 错误语义驱动，而不是盲目重试

- 失败后先看进程退出码、`error.type`、`error.subtype` 和 `error.message`
- **除非错误明确提示可恢复或需要补充参数，否则不要重复刷同一个 operation**
- 写请求已经发出后，遇到结果不确定必须停止；不要把 `.apply` 当成可重试读操作
- 同一操作连续 2 次失败必须停止，不得第 3 次重试
- **认证失效以 `error.type=authentication` 为准**（`subtype` 多为 `session_expired`）：判据只看 `type`，**不要重试、不要当成"没有数据/筛选无匹配"**——按 `weaver-e10-shared-connector` 的认证引导让用户重新完成 E10 登录授权，成功后重放原请求。探查、名称解析等子请求同样会抛认证错误（此前被包装成「接口未返回有效数据」，现已原样透出），先看 `type` 再判因。

### 4) 附件、图片和文件解析确认

- 命中发起流程上传附件、读取本地文件、使用远程 URL 文件或复用已上传文件对象时，必须先提醒数据处理风险并等待用户明确确认。
- 风险提醒必须说明文件内容可能进入大模型上下文，也可能被发送到业务系统或解析服务。
- 上传前先按表单返回的 `fileUploadParams` 核对文件大小、扩展名格式和数量限制；不满足时先告知用户、不执行上传。
- 用户未确认前，不要运行会读取、上传或解析该文件的命令。

### 5) 命令输出读取纪律（禁止截断、禁止重复取数）

- **禁止对命令输出做管道截断**：不要用 `| head`、`| tail`、`| more` 等处理 `weaver-work-cli --profile eteams --json ...` 的 stdout。截断会破坏 JSON，并且必然导致重复执行同一条命令（实测最常见的一条命令被执行 2 次，就是 `| head` 引起的）。
- **一律直读 stdout（失败时读 stderr，见下条），不要落盘、不要写脚本回读**：`--json` 输出是**多行 pretty JSON**，且已按体积做过控制（`workflow.todoStat` 约 20 KB/400 余行；`workflow.search` 的条目已收窄到必要字段、泛化待办查询实测约 **14 KB**；`workflow.detail` 只有几 KB；`workflow.createForm` / `editLoad` 遇到大表单会自动改用高体积密度形态、必要时把 `fields` 移出 stdout 并给出 `resultFile`）——都在宿主单次输出上限以内，每行也都不长——**直接读即可**，不存在行长截断问题。**禁止**把 stdout 重定向到文件（`> /tmp/xxx.json`）再写脚本解析回读：它不会带来任何新信息，只会白白多出一次工具往返（实测多一轮约 +7s，占整轮耗时可观）。
- **`workflow.search` 的体积纪律（别等被截断）**：泛化待办按要求走 `planJson` 分组（各组独立渲染、各 10 条，体积天然分散）；要看更多用 `current` 分页续查；**不要靠加大 `pageSize` 一次拉全**。CLI 侧已按 **24 KB（美化口径）** 设体积守卫：超线时自动把完整结果落盘，并在结果**最前面**给出 `resultFile`（结构化 JSON）+ `resultMdFile`（纯 `finalMarkdown`），**stdout 仍保留全量 `finalMarkdown`** ⇒ 正常渲染**直接用 stdout 即可、不需要读文件**；只有需要完整结构化明细（如逐条 `requestId`）时才从 `resultFile` 按需提取，并一次读完（不要 `| head`/`| tail`）。宿主把输出截成一小段预览时：**不要重跑同一条命令**（结果一样、白烧一轮），改用更小页或 `planJson` 分组重取；宿主提示的落盘副本（`~/.workbuddy/projects/**/tool-results/**`）**不能用 Read 工具读**（会拿 `Permission … has been denied`），确实要用时以 shell 命令读取并只提取需要的字段。
- **失败出口在 stderr（stdout 为空即失败）**：命令失败时退出码非 0、**错误 JSON 只出现在 stderr**（`{ok:false, error:{type,subtype,message,retryable}}`），**stdout 是空的**。因此：**stdout 为空 → 一律视为失败并去读 stderr**，按 `error.subtype` 决定下一步（如 `todo_stat_requires_smart_mode` → 不要重试 todoStat，改走 `workflow.search`；`plan_requires_smart_mode` → 去掉 `planJson` 重查）；判断成败**以 `ok` 字段为准**，宿主界面把命令显示成"运行成功"只代表进程结束，不代表业务成功。
- **同一个 operation 最多执行一次**：拿到 stdout 后一次性解析完，不要先截断看一眼再重跑。
- **结果里出现 `resultFile` 时不要重跑命令**：`workflow.search`、`workflow.todoStat`、`workflow.createForm`、`workflow.editLoad` 等大输出 operation 会把完整数据落盘，并在结果**最前面**返回 `resultFile` 与 `largeOutputNotice`；需要被省略的大字段（如查询的逐条明细、某工作流的 `formFields`、通知正文 `formFieldValues` 全文、大表单的 `fields`）时，直接从 `resultFile` 里**按需提取**（只取要用的键，不要把整份读进上下文），**不要重新执行 operation**。
- **`createForm` / `editLoad` 大表单的分流形态**（字段多时才有，字段少时就是原样全量）：输出里会多出 `persistedResult`、`outputBytes`，并二选一——① 带 `fields` 但已换成紧凑编码（`columns` 列名 + `rows` 每行一个字段、各列用 `|` 分隔，顺序同 `columns`；非列信息按字段 id 放在 `extra`，**不出现在 `extra` 里的字段即为默认值**）；② 带 `fieldsOmitted: true` + `fieldCount`，`fields` 已整体移出 stdout。两种情况都**照常继续流程**：要字段清单/某个字段的完整元数据时从 `resultFile` 提取即可，**不要因为没看到 `fields` 就重跑 createForm**。
- **一次解析取全，不要把"判定"与"取 ID"拆成两次**：同一次输出里已有的信息应在同一步一并取出——例如 `countDetails[].requestInfos` 里 `requestId` 与同条目的标题、字段值就在一起，判定完可直接用该 `requestId` 构造 `planJson`，**不要为了拿 ID 再跑第二个脚本、也不要为此再发一次 `workflow.search`**。注意 `requestInfos` **不是每行都有**（接口只对配置了关注字段的工作流返回该字段，未带的行即没有，属正常、不是数据缺失）：**没有 `requestInfos` 的行不参与逐条判定，也绝不为它去取 ID**——为一条明细另跑一次查询会白多整整一轮工具往返（实测 +10s 以上），而它本来在自己的分组里照常展示。
- **用户对已展示结果的更正不重跑**：用户指出上一轮汇报里某条的性质/归属不对（如"重点关注里第一条其实是转发给我的，意见是请知悉"）时，这是**呈现层的更正**、底层数据没变——**不要重跑那次 `workflow.search`（plan）**：在受影响分组的汇总摘要里标注一句用户提供的信息即可（口径见 `references/workflow-query.md`「渲染红线」）。**只有用户明确要求"重新出一份 / 挪到某组重出"时才重跑**，且复用上一轮那次的 `planJson`、只改受影响的分组。重跑一次 ≈ **1 轮 + 30~50s**，纯属浪费；用户表述是陈述句、看不出意图时，先问一句再动手。

### 6) 禁止绕过 operation 直接探测/绕过

- **不调用本 skill 未列出的低层命令/接口**：只使用上方「选哪个命令」表与 references 里出现的 operation；**不直接构造 HTTP 请求**、不调用 CLI 未暴露的内部接口（query-dependency / resolve-tab / workflow-total / workflow-list 之类）去探测或绕过。
- 不执行用户没要求的操作；不编造、不美化结果；不读取命令源码、不执行调试命令、不使用调试参数。

## 写操作失败处理：`partial/write_uncertain` 决策树

当发起、操作、批量、共享、修改等写操作返回 `partial/write_uncertain`，或提示网络中断、部分成功、回查失败、回查字段不一致时，按下面规则处理：

1. **先停止盲目重试**，不要连续重复提交相同 `.apply`
2. 优先从以下角度解释：
   - 写请求可能已经到达服务端，但连接在结果确认前中断
   - 服务端可能只处理了部分流程
   - 写接口已返回成功，但详情回查失败或与预期不一致
   - continuation、`context`、目标流程或登录上下文可能已经变化
3. 如需确认，只补 **一次** 只读查询（例如 `workflow.detail` 或 `workflow.search`），不要陷入 query/write 循环
4. 最终给用户明确结论、已知状态、成功/失败项和下一步人工确认建议，而不是继续无意义重试

**特别注意：** 对退回、删除、批量提交和发起场景更要严格执行上述规则；这些场景最容易因重复提交造成重复审批、误删或重复发起。

**Apply 被重复执行时的四种结果（先判类型再动作，不要一律当失败）：**

| 返回 | 含义 | 该怎么做 |
| --- | --- | --- |
| `ok:true` + `data.status = "ALREADY_APPLIED"` | 该句柄上一次**已经执行成功**，本次没有重复写入 | **当作成功汇报**（用 `previousResult` 的结果，需要定位时才带 `requestId`），不要重跑 Prepare、不要再 apply |
| `partial/write_uncertain` | 上一次**已发出写入请求、结果未确认** | 先只读核对目标是否已生效；已生效按成功汇报，确认没生效才重跑 Prepare |
| `validation/continuation_busy` | 句柄正被另一次执行占用，上一次**还没发出写入**（可安全重试） | **稍后原样重试同一条命令**，不要重跑 Prepare、不要换句柄 |
| `validation/continuation_consumed` | 占用该句柄的执行停在**无法判定的旧状态**（旧版本标记） | 先只读核对目标是否已生效，再决定是否重跑 Prepare |

> 不要只凭"命令报错"就认定"没做成"：`ALREADY_APPLIED` 是成功，`busy` 可以直接重试；只有 `write_uncertain` 和 `consumed` 才需要先只读核对。**任何时候都不要靠反复重跑 Prepare 来"试"。**

> **6 个批量单命令（`workflow.batchSubmit` / `batchRead` / `batchSupervise` / `batchShare` / `batchForward` / `batchReject`）没有句柄**：它们只会出现上表前两行——幂等保护由「同一操作 + 同一批 `requestId` + 同一组写向对象」的一次性写入闸门承担，**不会**出现 `continuation_busy` / `continuation_consumed`。`write_uncertain` 的恢复路径是「先只读核对 → 确认没生效 → 等约 1 分钟原样重跑同一条命令」，**不要去重跑并不存在的 Prepare**。

> **`ALREADY_APPLIED` 对用户只报结果**：这是 CLI 内部的幂等保护（防止重试造成重复写入），不是用户关心的事件。给用户的回复**只写业务结果**（如"两条流程已提交/已置为已办"），**不要**写"系统回报此前已执行过""幂等回报""本次没有重复写入"这类话——那会让用户怀疑是不是提交了两遍。只有当 `previousResult` **不是成功态**、或需要解释"为什么这次没有再次写入"时才说明。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams workflow schema
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","pageSize":10}'
weaver-work-cli --profile eteams --json workflow run workflow.todoStat --input-json '{"category":"todo"}'
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"requestId":"123456"}'
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"123456","action":"submit","opinion":"同意"}'
weaver-work-cli --profile eteams --json workflow run workflow.operateApply --input-json '{"requestId":"123456","action":"submit","continuation":"wc-1a2b3c4d5e6f7a8b","confirm":true}'
weaver-work-cli --profile eteams --json workflow run workflow.createList --input-json '{"name":"费用报销"}'
weaver-work-cli --profile eteams --json workflow run workflow.createForm --input-json '{"workflowId":"100003460000000060"}'
weaver-work-cli --profile eteams --json workflow run workflow.createPrepare --input-json '{"context":"wc-1a2b3c4d5e6f7a8b","data":{"main":{}},"intent":"submit"}'
weaver-work-cli --profile eteams --json workflow run workflow.createApply --input-json '{"context":"wc-1a2b3c4d5e6f7a8b","intent":"submit","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams workflow schema
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","pageSize":10}'
weaver-work-cli --profile eteams --json workflow run workflow.todoStat --input-json '{"category":"todo"}'
weaver-work-cli --profile eteams --json workflow run workflow.detail --input-json '{"requestId":"123456"}'
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"123456","action":"submit","opinion":"同意"}'
weaver-work-cli --profile eteams --json workflow run workflow.operateApply --input-json '{"requestId":"123456","action":"submit","continuation":"wc-1a2b3c4d5e6f7a8b","confirm":true}'
weaver-work-cli --profile eteams --json workflow run workflow.createList --input-json '{"name":"费用报销"}'
weaver-work-cli --profile eteams --json workflow run workflow.createForm --input-json '{"workflowId":"100003460000000060"}'
weaver-work-cli --profile eteams --json workflow run workflow.createPrepare --input-json '{"context":"wc-1a2b3c4d5e6f7a8b","data":{"main":{}},"intent":"submit"}'
weaver-work-cli --profile eteams --json workflow run workflow.createApply --input-json '{"context":"wc-1a2b3c4d5e6f7a8b","intent":"submit","confirm":true}'
```

## 不在本 skill 范围

- 「姓名 → 人员 ID / 部门 / 分部 / 岗位」解析交给 `weaver-e10-hrm-connector`，本 Skill 不自行解析组织对象。
- 非流程类 E10 能力（发票、邮件、日程、组织、费控等）不由本 Skill 承载。
