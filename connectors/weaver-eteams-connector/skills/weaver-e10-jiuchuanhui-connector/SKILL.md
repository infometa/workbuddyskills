---
name: weaver-e10-jiuchuanhui-connector
display_name: 泛微九氚汇营销管理
display_name_en: Weaver Jiuchuanhui Marketing Management
description: "泛微 E10 九氚汇营销管理：客户、联系人、商机、线索的创建、查询、搜索、修改、转移、公海、联系计划、联系记录、商机推进、线索转客户等 CRM 操作。用户表达营销/CRM 相关业务意图时使用。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10 九氚汇营销管理。覆盖客户、联系人、商机、线索全生命周期：创建、查询、搜索、修改、转移、公海领取/释放、查重、联系计划、联系记录、商机赢单/输单/无效/暂停/重启、线索转客户，并通过 prepare/apply 确认链处理全部高风险写操作。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Full-lifecycle CRM operations for customers, contacts, opportunities and clues in Weaver E10 Jiuchuanhui marketing management, including confirmed writes for create, update, transfer, pool claim/release, stage changes and clue-to-customer conversion. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli jiuchuanhui --help"
---

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

认证和登录态只能按共享规则通过 `weaver-work-cli auth ...` 命令判断；CLI 会自动携带完整 Cookie、`eteamsid` 与 `User-Agent: AgentType=<agentType>,IsAgent=true`，业务调用方不得覆盖这三条 header，也不得在业务 JSON 中传入这些 key。禁止直接读取、列出、打印或解析用户主目录下的 `.e10-cli`、auth、config 或 Keychain 数据。
所有命令通过 `weaver-work-cli --profile eteams --json jiuchuanhui run <operation>` 执行：简单 JSON 传 `--input-json '<json>'`，复杂或多行 JSON 先写入 UTF-8 文件再传 `--input <path>`，只有确认当前 shell 能稳定传管道时才使用 `--input -`。调用前先按需读取 references 下对应的文件，查参数结构，不要猜字段；**references 是第一信息源**，`weaver-work-cli --profile eteams jiuchuanhui schema` 是 operation、字段和风险等级的合约来源。
命令示例、提示词和临时说明必须同时兼容 Windows 和 macOS/Linux；涉及 JSON 输入、用户目录、路径分隔符、Python 启动器、文件删除、目录查看或文件比对时，同时给 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例。Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 下不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。
涉及附件、图片、本地文件、远程 URL 文件或文件解析的操作，执行前必须提醒用户：文件内容可能被上传到 E10 九氚汇、文件服务或解析服务，并可能进入当前大模型上下文用于理解和处理；必须等待用户明确确认后才继续。

# 泛微九氚汇营销管理

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 启动与缓存（MUST）

**首次使用、缓存缺失、用户要求刷新、或需要版本/配置/选项/objId 时，必须先读取 [`references/cache.md`](references/cache.md) 并按其中规则处理，再继续业务调用。**

- 优先使用 `~/.weaver-e10-jiuchuanhui-connector/{tenantKey}/{userId}/` 下的缓存（主文件 `weaver-e10-jiuchuanhui-connector.json` + `config/{pk}.json`）。
- 缓存缺失或用户要求初始化/刷新时，调用 CLI operation `weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init`（7 步：应用发现 → 13 objId → 版本校验 >= 1.5.11 → cfgId → 配置详情+字段 data_key → ebuilder 关联数据 → 字段选项 → 搜索参数 → 行政区划），支持 `dryRun`/`verbose`；也可在仓库根运行 `node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs`（薄包装，转发同一 operation）。
- 创建/更新接口读 `config/{pk}.json` 的 `detail.mainFields` 与 `detail.detailFields` 的 `data_key`（明细表 `detailFields[].id` 为请求体数组名，如 `detail1`/`detail2`，其 `fields` 定义明细行字段）；搜索接口读 `searchParams`；选项字段优先读字段 `optionList`。缓存已覆盖的配置直接读缓存，不重复走动态配置链路。
- 缓存初始化与刷新**已暴露为 CLI operation `jiuchuanhui.cache.init`**（risk: local-file-write，写本地缓存文件，无需 prepare/apply 确认链），Agent 直接调用即可。
- **版本硬约束（MUST）**：缓存初始化与字段配置预取时，必须确认九氚汇营销管理包版本 `>= 1.5.11`；**版本不达标或无法取得有效版本时，立即停止业务调用并提示用户**，不得继续任何读/写操作。

## 参数与字段处理（MUST）

- **只使用用户明确提供或已确认的字段值**：录入或修改数据时，只使用用户明确提供或已确认的字段值；必填字段缺失时向用户追问，不编造默认值或占位值。
- **写操作必须用户确认**：写操作（新建、修改、删除、转移、释放、领取、状态变更、完成计划等）一律走 `prepare` → 用户确认 → `apply`；查询类操作可直接执行，无需确认。
- **不擅自追加动作**：只完成用户明确要求的业务动作，不自作主张追加查询、修改、创建、验证、推荐或其他操作；只有对应 reference 明确要求的前置步骤才可以执行。
- **参数缺失/不支持立即停止**：操作类请求如果用户提供的参数缺失、不支持、无法映射或不符合接口文档，直接说明具体问题并停止；禁止猜测参数、替换参数或自动重试。
- **选项字段传 ID 不传中文**：`Select`/`RadioBox`/`CheckBox` 优先使用字段 `optionList` 的选项 `value`；`Ebuilder`/关联字段通过对应搜索或查询接口取数据 ID；`RelateBrowser` 使用自定义浏览字段选项查询；均传 ID，不传中文名称。
- **返回的候选选项不猜测内部值**：当接口返回按钮、操作项、阶段、状态、原因或其他候选选项时，**不得猜测其内部 value/ID**，必须展示候选项名称与 ID 让用户选择后再执行写操作。
- **行政区划全路径 ID**：`country`/`province`/`city`/`district` 传逗号分隔的全路径 ID（格式 `country,province,city,district`）；传细粒度自动填充粗粒度。
- **日期与金额**：日期类模糊表达（今天、本周、本月等）转换为明确起止范围；金额统一转换为数字，单位为元。

## 路由优先级（先判断是不是九氚汇 CRM，再选 operation）

九氚汇 CRM 不是通用 E10 对象。**只要用户的核心对象是九氚汇的客户、联系人、商机、线索、联系计划、联系记录、公海客户或相关辅助查询，就优先使用 `weaver-e10-jiuchuanhui-connector`。**

### 明确归 `weaver-e10-jiuchuanhui-connector` 的高优先级语义

出现以下任一语义时，优先走本 Skill：

- 客户 / 新建客户 / 客户详情 / 搜索客户 / 修改客户 / 转移客户 / 客户查重 / 客户公海
- 联系人 / 新建联系人 / 联系人详情 / 修改联系人 / 按客户或商机查联系人
- 商机 / 新建商机 / 商机详情 / 搜索商机 / 修改商机 / 商机阶段 / 商机赢单 / 输单 / 无效 / 暂停 / 重启 / 商机转移 / 关联联系人
- 线索 / 新建线索 / 线索详情 / 搜索线索 / 修改线索 / 线索状态变更 / 线索转客户 / 线索池
- 联系计划 / 完成联系计划 / 联系记录 / 跟进记录 / 批量联系记录
- 公海 / 领取公海客户 / 释放客户到公海 / 公海搜索
- 客户经理 / 按姓名查人员 / 按名称查事项 ID / 事项权限校验 / 企业工商照面 / 字段选项 / 自定义浏览字段
- `customerId` / `saleId` / `clueId` / `contactId` / `planId` / `managerid` 等九氚汇业务 ID

**判定规则：** 只要最终动作是对九氚汇客户/联系人/商机/线索做查询、搜索、创建、修改、转移、公海、联系计划、联系记录、状态推进或辅助解析，就归 `weaver-e10-jiuchuanhui-connector`。只有当用户处理的是非营销类 E10 业务、通用工作流或尚未封装的九氚汇能力时，才不使用本 Skill。

## 选哪个命令
| 想做什么 | 命令 | 按需读取 reference |
|---|---|---|
| 查看可用 operation、字段和风险等级 | `jiuchuanhui schema` | [`jiuchuanhui-entry.md`](references/jiuchuanhui-entry.md) |
| 初始化/刷新表单配置缓存 | `jiuchuanhui run jiuchuanhui.cache.init`（risk: local-file-write）；或仓库根运行 `node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs` | [`cache.md`](references/cache.md) |
| 客户创建/详情/搜索/修改/转移/公海/查重/联系记录 | `jiuchuanhui run jiuchuanhui.customer.*` | [`customer.md`](references/customer.md) |
| 联系人创建/详情/修改/按事项查询 | `jiuchuanhui run jiuchuanhui.contact.*` | [`contact.md`](references/contact.md) |
| 商机创建/详情/搜索/修改/阶段/赢单/输单/无效/暂停/重启/转移/关联/联系记录 | `jiuchuanhui run jiuchuanhui.sale.*` | [`sale.md`](references/sale.md) |
| 线索创建/详情/搜索/修改/状态变更/转客户/线索池/跟进记录 | `jiuchuanhui run jiuchuanhui.clue.*` | [`clue.md`](references/clue.md) |
| 创建/完成联系计划 | `jiuchuanhui run jiuchuanhui.contact-plan.*` | [`contact-plan.md`](references/contact-plan.md) |
| 按事项或按人员+时间范围查询联系记录 | `jiuchuanhui run jiuchuanhui.entity.contact-records.list` / `jiuchuanhui.contact-records.by-person-time.list` | [`contact-records.md`](references/contact-records.md) |
| 应用/表单/字段/选项/接口配置/文件预览等发现与配置 | `jiuchuanhui run jiuchuanhui.{app,form,ds,field,rest,config,file}.*` | [`discovery-config.md`](references/discovery-config.md)、[`cache.md`](references/cache.md) |
| 按名称查事项/人员 ID、权限、工商照面、字段信息、自定义浏览选项 | `jiuchuanhui run jiuchuanhui.{entity,user,company,field,browser-option}.*` | [`general-helpers.md`](references/general-helpers.md) |
| 商机阶段推进组合、其它 schema 未列出的能力 | 无可用命令 | [`disabled-capabilities.md`](references/disabled-capabilities.md) |

处理链：

- 客户：搜索/查重先于创建。新建客户前先 `jiuchuanhui.customer.duplicate.check`；有疑似重复时表格展示并让用户确认；若客户在公海提醒可领取。确认继续后才 `customer.create.prepare` -> 用户确认 -> `customer.create.apply`。
- 客户修改/转移/释放/领取：先 `customer.search`/`customer.get` 确认唯一 -> `customer.update.prepare`（或 `transfer`/`open-sea.release`/`open-sea.claim`）-> 用户确认 -> `.apply`。
- 联系人：只给姓名未指明所属事项时，先 `contact.by-entity.search` 或搜索候选并让用户选择；创建/修改走 `contact.create/update.prepare -> apply`。联系人随客户创建（`detail2`）时不要重复调用 `contact.create`。
- 商机：赢单/输单/无效/暂停/重启/转移/关联联系人/联系记录，全部先确认商机唯一，再 `sale.*.prepare` -> 用户确认影响与不可逆性 -> `sale.*.apply`。赢单/输单/无效属于高影响状态变更，执行前必须提示不可逆或关键影响；输单必须先确定输单原因，暂停必须有暂停原因，重启需先确认目标商机处于可重启状态（否则不得重启）。
- 线索：状态变更覆盖放弃/分配/转移/有效/无效，先确认线索唯一、目标状态/人员明确 -> `clue.status-change.prepare` -> 用户确认 -> `.apply`。线索转已有客户走 `clue.to-customer`；转新客户走 `customer.create` 且传 `source_module_id=<clueId>`，成功后不要再额外修改线索。
- 联系计划：按客户/商机/线索关联时必须先确定唯一关联事项和 `type`，用户提到联系人时先用 `contact.by-entity.search` 查询候选 -> `contact-plan.create.prepare -> apply`；完成计划走 `contact-plan.complete.prepare -> apply`。
- 通用辅助：先 `user.id.by-name` / `entity.id.by-name` 解析 ID，再进入业务调用；`user.current-profile` 每轮会话优先取一次并复用。

## 执行原则（减少误路由、误重试和无效消耗）

### 1) 先拿最小必要信息，再执行

- 只是搜索时，优先直接用 `customer.search`/`sale.search`/`clue.search`
- 列表默认先取小页，优先 `pageNo=1`、`pageSize=10`；用户没有要求全量时不要自动翻页
- 客户搜索必须显式传 `mine`/`all`/`customerSea` 三个 key（其中一个为 `""`，其余两个为 `-1`），默认 `mine=""&all=-1&customerSea=-1`（我的客户）；本接口没有 `scope` 快捷参数
- 用户已经给出 `customerId`/`saleId`/`clueId` 时，不要先查列表再过滤，直接用对应 get 或 prepare
- 只有需要完整详情、可编辑状态或附件归属时才补 get

### 1.5) 大结果只摘要给用户

- 当前 CLI 会把完整 JSON envelope 写 stdout；Agent 回复时不要原样贴完整 JSON
- 列表最多先展示最相关的前 10 条，包含 ID、名称、负责人、状态/阶段、金额、最近跟进时间和可点击链接
- 需要全量统计时，按 `pageNo` 分页读取并累计必要字段；说明已读取页数、命中数和是否还有更多
- 详情或调试用完整响应过长时，优先落本地文件并向用户提供摘要和文件路径
- 列表、卡片及详情中的关联事项名称必须渲染为可点击链接 `https://{baseUrl}/sp/ebdfpage/card/0/{objId}/{dataId}`；`objId` 优先从缓存 `discovery["objId:{tag}"]` 获取
- 返回类型为对象数组的字段必须展示全部对象及其完整有效值，不得只展示第一项或摘要；数组为空时按空值处理
- 客户列表默认展示客户名称、负责人、客户类型/状态、行业、最近跟进、创建时间；商机列表展示商机名称、客户、负责人、阶段、金额、预计成交/最近跟进；线索列表展示线索名称、客户/公司、处理人、状态、来源、最近跟进/创建时间。缺失字段用 `-`
### 2) 已知对象时直达动作

- 已拿到业务 ID、人员 ID、选项 ID 或完整 `form` 时，优先调用对应 operation
- 同一轮里已有足够的新鲜查询结果时，不要重复查询同一事项
- 不要默认走 `search -> get -> prepare -> apply` 全链路；对象已明确时应压缩步骤

### 3) 错误语义驱动，而不是盲目重试

- 失败后先看进程退出码、`error.type`、`error.subtype` 和 `error.message`
- **除非错误明确提示可恢复或需要补充参数，否则不要重复刷同一个 operation**
- 写请求已经发出后，遇到结果不确定必须停止；不要把 `.apply` 当成可重试读操作
- **错误为 `authentication`（未登录，如 `E10 auth not found`）或 `session_expired`（登录态失效）时：立即停止当前操作，不要用示例占位域名或自行猜域名登录，也不要盲目重试**。先读取共享规则 `../weaver-e10-shared-connector/references/e10-auth-and-session.md`，按其中流程引导用户**断开并重新连接本连接器**完成重新登录，然后再继续原操作

### 4) 文件处理确认

- 执行文件预览（`file.preview`）或任何会读取本地文件、上传远程 URL 文件、解析图片/PDF/XML 的步骤前，必须先提醒用户文件内容可能进入大模型上下文，也可能发送到 E10 九氚汇或文件解析服务
- 用户未明确确认前，不要运行文件预览或解析命令

## 写操作失败处理：`partial/write_uncertain` 决策树

当创建、修改、转移、释放、领取、状态变更、赢单/输单等写操作返回 `partial/write_uncertain`，或提示网络中断、部分成功、回查失败、回查字段不一致时，按下面规则处理：

1. **先停止盲目重试**，不要连续重复提交相同 `.apply`
2. 优先从以下角度解释：
   - 写请求可能已经到达服务端，但连接在结果确认前中断
   - 服务端可能只处理了部分事项（例如批量联系记录）
   - 写接口已返回成功，但详情回查失败或与预期不一致
   - continuation、目标事项或登录上下文可能已经变化
3. 如需确认，只补 **一次** 只读查询（例如 `customer.get`/`sale.get`/`clue.get` 或列表查询），不要陷入 query/write 循环
4. 最终给用户明确结论、已知 `status`/`resultCode`、成功/失败项和下一步人工确认建议，而不是继续无意义重试

**特别注意：** 对转移、释放公海、赢单/输单/无效、状态变更场景更要严格执行上述规则；这些场景最容易因重复提交造成误转、误释放或覆盖用户刚确认的状态。

**搜索约束：** 查询/搜索无结果时，直接原样说明查询条件并告知无结果，**不得修改条件（扩大范围/降低阈值/去除非核心条件）重试**——参数不支持的错误应反馈给用户后停止，而不是悄悄调整客户本意。

## 快速命令示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams jiuchuanhui schema
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.duplicate.check --input-json '{"mainTable":{"name":"示例科技有限公司","simpleName":"示例科技"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.search --input-json '{"customer_name":"小康","mine":"","all":"-1","customerSea":"-1","pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.get --input-json '{"id":"100001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input-json '{"form":{"mainTable":{"manager":"USER_ID","customer_name":"示例科技有限公司"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.prepare --input-json '{"mainTable":{"saleId":"200001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.id.by-name --input-json '{"mainTable":{"employeeName":"魏思雨"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams jiuchuanhui schema
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.duplicate.check --input-json '{"mainTable":{"name":"示例科技有限公司","simpleName":"示例科技"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.search --input-json '{"customer_name":"小康","mine":"","all":"-1","customerSea":"-1","pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.get --input-json '{"id":"100001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input-json '{"form":{"mainTable":{"manager":"USER_ID","customer_name":"示例科技有限公司"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.prepare --input-json '{"mainTable":{"saleId":"200001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.id.by-name --input-json '{"mainTable":{"employeeName":"魏思雨"}}'
```

## 不在本 skill 范围

- 禁止加载原始 `weaver-e10-jiuchuanhui-connector` 源 Skill 代替 CLI。
- 禁止 curl、fetch、浏览器自动化或直接访问 E10 原始接口路径。
- 禁止读取或复制 CLI runtime 内部 Token、Cookie、ETEAMSID。
- 禁止读取、列出、打印或解析用户主目录下的 `.e10-cli`、auth、config 或 Keychain 数据。
- `jiuchuanhui.sale.stage-advance` 未暴露为 CLI operation：商机阶段推进依赖缓存中的阶段配置做映射与前置校验，属于 Skill 编排层职责，CLI 的 `sale.update` 与 `sale.stage.search` 已覆盖基础能力。
- 非九氚汇营销类 E10 能力、通用流程编排、非 CRM 表单/审批/组织等业务不由本 Skill 承载。
