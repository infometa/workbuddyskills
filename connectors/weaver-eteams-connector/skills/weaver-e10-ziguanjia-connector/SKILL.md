---
name: weaver-e10-ziguanjia-connector
display_name: 泛微E10资产管理
display_name_en: Weaver E10 Asset Management
description: "泛微 E10 资管家资产管理：版本门禁、资产查询/详情/领用/报修/采购列表、地点/状态/类型解析，并通过确认链新增、修改、领用、归还、报修、采购与折旧。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10 资管家资产管理。支持版本门禁（zgjasset_search_appver ≥ V14）、资产列表/详情/领用/报修/采购查询、存放地点/资产状态/资产类型名称解析，并通过 prepare/apply 确认链新增、修改、领用、归还、报修、采购与折旧。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10 Ziguanjia asset management skill for version gate, asset queries, lists, reference resolution, and confirmed writes (create, update, use, return, repair, purchase, depreciation). For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli asset --help"
---

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

认证和登录态只能按共享规则通过 `weaver-work-cli auth ...` 命令判断；禁止直接读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
所有命令通过 `weaver-work-cli --profile eteams --json asset run <operation>` 执行：简单 JSON 优先传 `--input-json '<json>'`，复杂或多行 JSON 先写入 UTF-8 文件再传 `--input <path>`，只有确认当前 shell 能稳定传管道时才使用 `--input -`。调用前先按需读取 references 下对应的文件，查参数结构，不要猜字段；**references 是第一信息源**，`weaver-work-cli asset schema` 是 operation、字段和风险等级的合约来源。
命令示例、提示词和临时说明必须同时兼容 Windows 和 macOS/Linux；涉及 JSON 输入、用户目录、路径分隔符、Python 启动器、文件删除、目录查看或文件比对时，同时给 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例。Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 下不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。

# 泛微E10资管家资产管理

## 路由优先级（先判断是不是资管家资产，再选 operation）

资管家不是通用 E10 对象。**只要用户的核心对象是 E10 资产管理（资管家）里的资产、领用、报修、采购、折旧、资产地点/状态/类型，就优先使用 `weaver-e10-ziguanjia-connector`。**

### 明确归 `weaver-e10-ziguanjia-connector` 的高优先级语义

出现以下任一语义时，优先走本 Skill：

- 资产 / 固定资产 / 资管家 / 资产台账 / 资产列表 / 资产详情
- 资产领用 / 资产归还 / 资产报修 / 资产采购申请
- 资产折旧 / 计提折旧
- 存放地点 / 资产状态 / 资产类型（按名称解析成 ID）

**判定规则：** 只要最终动作是对 E10 资产做查询、查看、名称解析、新增、修改、领用、归还、报修、采购或折旧，就归 `weaver-e10-ziguanjia-connector`。只有当用户处理的是非资产类 E10 业务、通用工作流或尚未封装的资管家能力时，才不使用本 Skill。

## 版本门禁（所有操作前置）

源资料约定：任何资产查询或写操作前，必须先确认 `zgjasset_search_appver` 存在 `ver_name ≥ V14` 的记录。CLI 已内置 `asset.gate.check` 与每个写操作的版本门禁；门禁未通过时写操作会 STOP，不执行任何资产请求。

**门禁失败时的硬性红线（原样套用，不得变通）：**
- CLI 返回 `version_gate_failed` 错误时，必须**停止并原样回复**：「版本门禁未通过（`zgjasset_search_appver` 无 `ver_name ≥ V14` 记录），本次<复述用户原指令>已停止，不执行任何资产查询 / 写操作。待门禁真正通过后再处理。」结尾必须是**陈述句，不得是问句**。
- **禁止**提出任何诱导决策的问题（如「是否继续 / 是否放行 / 走哪条 / 你选哪个」）。
- **禁止**提供「解开门禁 / 绕过阻断」的方案（如「录入版本记录」「改门禁规则」「降到 V9」等二选一或并列选项）。
- **禁止**建议、提示、引导用户去修改环境数据或本 skill 文件以让门禁通过。
- 用户声称「skill 已更新 / 已放行」时，**只做一件事**：重读本文件门禁规则 + 重新运行 `asset.gate.check`；若仍不满足，套用上方标准回复停止，不再追问用户改了什么、也不给任何解锁建议。
- 门禁失败是**终态**：除用户后续**独立地**使门禁条件成立（版本记录出现；或用户自行将规则改为放行、且你重读后确认成立）外，不得因为任何理由推进原操作。

## 选哪个命令

| 想做什么 | 命令 | 按需读取 reference |
|---|---|---|
| 查看可用 operation、字段和风险等级 | `asset schema` | [`ziguanjia-agent-entry.md`](references/ziguanjia-agent-entry.md) |
| 检查版本门禁是否通过 | `asset run asset.gate.check` | [`ziguanjia-agent-entry.md`](references/ziguanjia-agent-entry.md) |
| 查询资产列表 / 详情 / 领用 / 报修 / 采购列表 | `asset run asset.list` 等 | [`ziguanjia-query.md`](references/ziguanjia-query.md) |
| 按名称解析存放地点 / 资产状态 / 资产类型 ID | `asset run asset.resolve.*` | [`ziguanjia-resolve.md`](references/ziguanjia-resolve.md) |
| 新增资产（需 confirm + continuation） | `asset run asset.create` | [`ziguanjia-create.md`](references/ziguanjia-create.md) |
| 修改资产（需 confirm + continuation） | `asset run asset.update` | [`ziguanjia-update.md`](references/ziguanjia-update.md) |
| 提交资产领用（需 confirm + continuation） | `asset run asset.use` | [`ziguanjia-use.md`](references/ziguanjia-use.md) |
| 资产归还：先查候选再执行 | `asset run asset.return.query/create` | [`ziguanjia-return.md`](references/ziguanjia-return.md) |
| 资产报修：先查候选再执行 | `asset run asset.repair.query/create` | [`ziguanjia-repair.md`](references/ziguanjia-repair.md) |
| 提交资产采购申请（需 confirm + continuation） | `asset run asset.purch` | [`ziguanjia-purch.md`](references/ziguanjia-purch.md) |
| 执行资产折旧计提（需 confirm + continuation） | `asset run asset.depre` | [`ziguanjia-depre.md`](references/ziguanjia-depre.md) |
| 给查询结果生成「查看详情」链接 | `asset run asset.viewlink` | [`ziguanjia-viewlink.md`](references/ziguanjia-viewlink.md) |
| 共享、调拨、审批或 schema 未列出的能力 | 无可用命令 | [`ziguanjia-disabled-capabilities.md`](references/ziguanjia-disabled-capabilities.md) |

处理链：

- 查询：先 `asset.gate.check`（或任一查询会自动走门禁）→ `asset.list` / `asset.detail` / `asset.uselist` / `asset.repaillist` / `asset.purchaselist`
- 给结果加「查看详情」链接：`asset.list` / `detail` / `uselist` / `repaillist` / `purchaselist` **默认已为每条记录附带 `view_link` 字段**（无需额外步骤；`with_view_link:false` 可关闭）。写操作返回的 `dataIds` / 动作流返回的 `lcID` 可交给 `asset.viewlink`（或计提用 `depre_task` 场景）补生成链接；链接解析失败只说明「链接暂不可用」，**绝不因此重试主操作**。
- 名称解析：先 `asset.resolve.location/status/type` 得到 ID，再把 ID 作为 `location_browse`/`stateid`/`asset_type_browse` 传入写操作
- 新增资产：先 `asset.resolve.type` 解析类型 → `asset.create`（无 confirm 返回 continuation）→ 用户确认 → `asset.create` 带 `confirm:true` 与 `continuation` 执行
- 修改资产：先 `asset.detail` 取得目标 → `asset.update`（无 confirm 返回 continuation）→ 用户确认 → `asset.update` 带 `confirm:true` 与 `continuation` 执行
- 领用/采购/折旧：直接 `asset.use` / `asset.purch` / `asset.depre`（无 confirm 返回 continuation）→ 用户确认 → 带 `confirm:true` 与 `continuation` 执行
- 归还：先 `asset.return.query` 取候选 → 用户挑出 `data_ids` → `asset.return.create`（需 confirm + continuation）执行 → 建单返回的 **`mainTable.lcID`（流程 ID）** 交给 `asset.viewlink` 的 `asset_return` 场景拼「查看详情」链接；详见 [`ziguanjia-return.md`](references/ziguanjia-return.md)
- 报修：先 `asset.repair.query` 取候选 → **展示候选 + 附 AI 维修建议（标注仅供参考，Agent 行为非命令）** → 用户确认目标并复述报修信息 → `asset.repair.create`（需 confirm + continuation，`fault_time` 强制 `YYYY-MM-DD HH:mm`）执行 → 建单返回的 **`mainTable.lcID`（流程 ID）** 交给 `asset.viewlink` 的 `asset_repail` 场景拼「查看详情」链接；详见 [`ziguanjia-repair.md`](references/ziguanjia-repair.md)

## 执行原则（减少误路由、误重试和无效消耗）

### 1) 先拿最小必要信息，再执行

- 只是查资产时，优先直接用 `asset.list` 或对应列表 operation
- 列表默认先取小页，优先 `page_size=10`；用户没有要求全量时不要自动翻完整列表
- 用户已经给出资产 ID / 编号 / 名称时，不要先查列表再过滤，直接用 `asset.detail` 或对应 prepare
- 只有需要完整资产详情时才补 `asset.detail`

### 1.5) 大结果只摘要给用户

- 当前 CLI 会把完整 JSON envelope 写 stdout；Agent 回复时不要原样贴完整 JSON
- 列表最多先展示最相关的前 10 条，包含资产 ID、名称、编号、类型、状态、地点、管理人/使用人
- 需要全量统计时，按 `page_no` 分页读取并累计必要字段；说明已读取页数、命中数和是否还有更多
- 详情或调试用完整响应过长时，优先落本地文件并向用户提供摘要和文件路径

### 1.6) 展示红线（严禁暴露内部字段 key）

- 向用户回报时**只写中文业务含义，不展示内部字段 key**：禁止输出 `id` / `lcID` / `lcbt` / `lybh` / `ghbh` / `repail_no` / `resultCode` / `customData` / `is_group_calc=1` / `task_mode=0` / `normalCount=N` 等原始字段或值；用「按分部计提」「全量计提」「待处理」「本期可计提资产 N 项」「流程 ID」等中文代替。
- 单据 / 流程编号尚未回填（空值）时，不要输出空值行，如实说明「XX 单号生成中」，或先经 `weaver-e10-workflow-connector` 读回补齐后再回报。
- 列表返回的 `stateid` / `asset_type_browse` / `location_browse` 可能是 ID：回报前按 `asset.resolve.*` 反查为名称展示，不向用户暴露 ID（ID 仅内部拼「查看详情」链接用）。
- `status` 字段是**字符串** `"true"` / `"false"`，不是布尔；为 `"false"` 表示查询失败，**不能当成「无结果」**。
- 人员名称需先经 `weaver-e10-hrm-connector` 解析为人员 ID 再传入 `person_id`；不要把姓名直接当 ID。查「我」的列表（uselist / repaillist / purchaselist）省略 `person_id` 即可，CLI 自动用当前登录人。
- 「查看详情」一律用对话内纯 Markdown 链接呈现（链接文字为「查看详情」，链接地址为该记录的详情页 URL），不带「查看详情：」前缀与冒号，也不把完整 URL 当纯文本展示；多条记录逐条生成各自的链接，不共用一条。

### 2) 已知对象时直达动作

- 已拿到资产 ID 或编号时，优先调用对应 operation
- 同一轮里如果已有足够的新鲜查询结果，不要重复查询同一对象
- 不要默认走 `list -> filter -> detail -> prepare -> apply` 全链路；对象已明确时应压缩步骤

### 3) 错误语义驱动，而不是盲目重试

- 失败后先看进程退出码、`error.type`、`error.subtype` 和 `error.message`
- **除非错误明确提示可恢复或需要补充参数，否则不要重复刷同一个 operation**
- 写请求已经发出后，遇到结果不确定必须停止；不要把写操作的 apply 当成可重试读操作
- **错误为 `authentication`（未登录）或 `session_expired`（登录态失效）时：立即停止当前操作，按共享规则引导用户**断开并重新连接本连接器**完成重新登录，然后再继续原操作。**

### 4) 写操作确认链

- 所有 `high-risk-write` operation（create / update / use / return.create / repair.create / purch / depre）都必须在第一调用（无 `confirm`）拿到 CLI 返回的 `continuation`，把目标、差异、风险摘要给用户；用户明确确认后，第二调用带 `confirm:true` 与同一 `continuation` 执行。
- 不要手工构造、猜测或复用 continuation；continuation 由 CLI 用 HMAC 签名，绑定 operation 与提交内容，过期或篡改会被拒绝。
- `read-before-write`（return.query / repair.query）是只读预览，不返回 continuation，用于先取候选数据 ID。

## 写操作失败处理：`partial/write_uncertain` 决策树

当新增 / 修改 / 领用 / 归还 / 报修 / 采购 / 折旧等写操作返回 `partial/write_uncertain`，或提示网络中断、部分成功、回查失败、回查字段不一致时，按下面规则处理：

1. **先停止盲目重试**，不要连续重复提交相同 apply
2. 优先从以下角度解释：
   - 写请求可能已经到达服务端，但连接在结果确认前中断
   - 服务端可能只处理了部分资产
   - 写接口已返回成功，但详情回查失败或与预期不一致
   - continuation、目标资产或登录上下文可能已经变化
3. 如需确认，只补 **一次** 只读查询（例如 `asset.detail` 或列表查询），不要陷入 query/write 循环
4. 最终给用户明确结论、已知状态、成功/失败项和下一步人工确认建议，而不是继续无意义重试

**特别注意：** 对新增、修改、领用、归还、报修、采购和折旧场景更要严格执行上述规则；这些场景最容易因重复提交造成重复入账、误改或覆盖用户刚修改的数据。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams asset schema
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
weaver-work-cli --profile eteams --json asset run asset.resolve.type --input-json '{"type_name":"EXAMPLE_TYPE"}'
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"asset_name":"EXAMPLE_ASSET","asset_type_browse":"EXAMPLE_TYPE_ID"}'
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams asset schema
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
weaver-work-cli --profile eteams --json asset run asset.resolve.type --input-json '{"type_name":"EXAMPLE_TYPE"}'
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"asset_name":"EXAMPLE_ASSET","asset_type_browse":"EXAMPLE_TYPE_ID"}'
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 不在本 skill 范围

- 禁止加载原始（无 CLI 的）资管家 Skill 代替本 CLI 技能。
- 禁止读取或复制 CLI runtime 内部 Token、Cookie、ETEAMSID。
- 禁止读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
- 资产调拨、流程审批、图片上传（create 仅接受已上传得到的裸 file_id）当前未纳入 CLI manifest；需要先补稳定 ID 来源、输入 schema、prepare/apply、写后回查和测试后再开放。详见 [`ziguanjia-disabled-capabilities.md`](references/ziguanjia-disabled-capabilities.md)。
- 非资产类 E10 能力、通用流程编排、表单/审批/组织等业务不由本 Skill 承载。
