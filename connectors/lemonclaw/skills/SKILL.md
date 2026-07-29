---
name: lemonclaw-workbuddy
description: "通过 lemonclaw-cli 与内置独立开票工作流查询或操作柠檬云多产品业务数据。覆盖认证和账套、进销存 SCM、业财 ERP、财务 ACC、发票查询及独立开票；适用于客户、供应商、商品、采购、销售、库存、收付款、往来、凭证、账簿、资金与经营报表、进销项发票、立即开票、批量开票和开票反馈等场景。用户提到柠檬云、Lemon Cloud、LemonSCM、LemonERP、进销存、业财、财务或开票时使用。"
version: "1.0.1"
author: "Ningmengyun"
---

# LemonClaw WorkBuddy Skill

## 使用边界

本连接器有两条执行路径：

- 公共认证、账套以及 ACC、SCM、ERP 业务通过 `lemonclaw-cli` 执行。不要直接执行 bundled skill 中的 `action.py`，不要手写 HTTP 请求、URL、headers、认证信息或账套上下文。
- 独立开票 `invoice` 不使用通用 `action search/show/run`；读取当前 runtime 中的 `invoice/SKILL.md`，按其立即开票、批量开票或反馈提交流程执行。

WorkBuddy skill 负责产品路由、账套选择、action 选择、输入输出纪律和最终回复。具体 action 的字段、参数位置、返回结构和展示口径，以 `lemonclaw-cli action show <product> <action>` 返回的 `contract`、`ACTION.md`、`input.md`、`output.md` 为准。

不要把 action 清单、接口路径、字段全集或运行时内部细节写进最终回复。不要向用户展示完整 CLI JSON，除非用户明确要求排查 CLI 协议。

## 认证规则

连接器负责执行 `lemonclaw-cli auth status/login/logout`。ACC、SCM、ERP 业务处理中不要要求用户提供 API Key、access token、Authorization header、cookie 或本地凭据路径，也不要在回复中展示这些信息。

如果认证缺失或过期，按 CLI 返回的认证错误提示用户登录或重新授权；不要自行拼接认证请求。

独立开票是 API Key 规则的唯一例外：是否需要收集 API Key、如何保存和验证，严格按 `invoice/SKILL.md` 及当前开票流程模板执行。即使在开票流程中，也不得要求用户提供 access token、Authorization header、cookie、baseUrl 或本地凭据路径。

## 账套上下文

ACC、SCM、ERP 业务请求前先执行：

```text
lemonclaw-cli account current
```

当前账套满足用户请求时直接继续业务 action。没有当前账套、已根据产品路由确认需要切换产品，或用户明确要求切换账套时，优先执行：

```text
lemonclaw-cli account switch "<产品或账套线索>"
```

按 `account switch` 的结果继续处理：

- 唯一命中并切换成功：执行 `lemonclaw-cli account current` 核验后继续业务 action。
- 返回多个候选：直接展示本次 `switch` 返回的候选并让用户确认；不要再次执行 `account list`，避免刷新候选缓存和序号。用户确认后执行 `account select`，再执行 `account current`。
- 未找到匹配项且没有返回可选候选：执行 `account list` 获取完整候选，等待用户确认后执行 `account select`，再执行 `account current`。
- 认证、网络、权限或服务异常：保持原错误含义处理，不要改用 `account list` 掩盖异常。

候选确认后优先使用最近一次 `switch` 或 `list` 返回的序号：

```text
lemonclaw-cli account select --index <index>
lemonclaw-cli account current
```

名称在最近候选中唯一时，也可以使用：

```text
lemonclaw-cli account select --product <product> --name "<账套名称>"
```

已取得准确 `asid` 时可以使用 `--product <product> --asid <asid>`；专业版同名账套需要同时使用 `--product <product> --serviceid <serviceid> --name "<账套名称>"` 限定。

账套规则：

- `account switch` 可以按产品、账套名、asid、serviceid、版本等线索匹配；账套名、产品或版本存在歧义时先让用户确认。
- `account select` 只从最近一次 `account switch` 或 `account list` 缓存的候选中选择；没有候选缓存时不要直接按名称选择。
- `account select --index` 的序号必须来自最近一次候选结果，不要固定传 `1`；名称重复时不得自行选择。
- 展示候选时使用 `index`、`productName`、`editionName`、`accountSetName`、`asid`；专业版同名账套需要区分时可附加 `serviceid`。
- 不展示或要求用户提供 `candidateId`、`appasid`、`appAsId`、`accAppId`。
- 每个产品独立保存自己的账套上下文。切换当前产品或账套不应删除其他产品的上下文。
- `account clear` 只清理账套上下文，不清理认证。
- 独立开票所需的销方、购方、认证和公司选择以 `invoice/SKILL.md` 为准；除非开票流程明确要求，否则不要把本节的普通业务账套流程强行套用到 invoice。

## 产品路由

同一时间只有一个 `activeProduct`。如果 `activeProduct` 存在，默认只在当前产品中搜索和执行 action。除非用户明确点名另一个产品、明确要求切换产品、明确要求跨产品汇总，或明确进入独立开票流程，否则不要切换产品。

如果没有 `activeProduct`，且用户没有说明产品，先确认用户要使用财务 ACC、进销存 SCM、业财 ERP，还是独立开票 invoice；确认前不要默认切到 SCM 或跨产品试探。

产品边界：

- `acc`：独立财务账套，包括凭证、账簿、资金、基础资料、财务发票查询、财务报表等。
- `scm`：进销存账套，包括商品、客户、供应商、采购、销售、库存、收付款、经营报表等。
- `erp`：业财账套，包括进销存业务和 ERP 财务侧能力。ERP 财务侧的凭证、账簿、资金、基础资料和财务发票能力应在 ERP 产品内处理，不要为了这些词切到 ACC。
- `invoice`：独立开票流程。仅当用户明确提出独立开票、立即开票、批量开票、确认开票、发票预览、提交开票等开票操作时使用。

容易误判的业务词：客户、供应商、商品、库存、采购、销售、收款、付款、往来、资金、报表、明细、汇总、对账、欠款、利润、发票等在多个产品中都可能存在。不能仅凭这些词切换产品；先在当前 `activeProduct` 范围内搜索候选。

发票业务也必须遵循上述产品路由规则。普通发票查询、发票详情、进项发票、销项发票、发票导出和发票统计，在已确认的当前 ACC、SCM 或 ERP 产品范围内选择 action；没有当前产品且用户未指定产品或账套时，先请用户确认，不得默认选择 ACC。

只有用户明确提出独立开票、立即开票、批量开票、确认开票、提交开票、发票预览或税票平台操作时，才进入 `invoice` 流程。

其他产品已经保存账套上下文，不构成切换产品的依据。当前产品没有匹配能力时，只能说明当前产品暂未找到对应能力并询问用户是否切换；不得静默使用其他产品的 action 或数据代替。

## 独立开票工作流

命中独立开票、立即开票、批量开票、确认开票、开票预览、提交开票或开票问题反馈时：

1. 执行 `lemonclaw-cli skill-root --check`，获取当前 runtime 的 bundled skill 根目录。
2. 完整读取 `<skill-root>/invoice/SKILL.md`，并以 `<skill-root>/invoice/` 作为所有相对路径的基准。
3. 立即开票只按 `references/immediate/flow.md` 执行；批量开票只按 `references/batch/flow.md` 执行；反馈提交只按 `invoice/SKILL.md` 指定的 shared 文档执行。
4. 按开票 Skill 和当前阶段文档调用随 runtime 分发的脚本、references、config 与 assets；不要自行改写开票门禁、固定提示、预览、确认、额度检查、payload、提交或反馈流程。
5. 独立开票不使用通用 `action search/show/run`，也不要用 ACC 或 ERP 的发票查询 action 代替开票流程。普通进项、销项发票查询仍按当前 ACC 或 ERP 产品执行。
6. `invoice/SKILL.md`、当前流程文档和共享输出协议是独立开票的执行依据；与下文通用 CLI action 规则不同时，以开票工作流为准。

## Action 选择流程

处理 ACC、ERP、SCM 业务请求时严格按顺序执行：

```text
1. lemonclaw-cli account current
2. lemonclaw-cli action search "用户需求"
3. lemonclaw-cli action show <product> <action>
4. lemonclaw-cli action run <product> <action> --json-stdin
```

选择规则：

- `search` 只用于找候选，不生成参数、不执行业务请求。
- `search` 结果不是最终 action。候选接近、名称相似或业务边界不清时，必须 `show` 多个候选，对比用途、输入和输出后再决定；仍不确定时向用户澄清。
- 第一次 `search` 没有候选时，不得直接判断当前产品不支持。先拆解用户请求中的业务对象、操作类型、结果粒度、筛选条件和期望输出，在当前 `activeProduct` 内改写搜索词重新搜索并核对候选；完成语义核对后仍未找到，才说明当前产品暂未找到对应能力。
- `show` 返回当前 action 的 `contract`、`ACTION.md`、`input.md`、`output.md`。只能根据这些内容构造请求。
- 不要根据 action 名称、响应字段、页面列名、旧记忆或相邻 action 臆造入参。
- 不要为了找到更像的 action 自动跨产品搜索。跨产品前必须满足产品路由规则。
- `invoice` 产品是独立编排流程，不能通过通用 `action search/show/run` 执行；遇到对应错误时不要改用 ACC 发票查询 action 代替开票流程。

## Action 输入规则

本节只适用于 ACC、SCM、ERP 的 CLI action。`action run` 的 stdin 必须保持嵌套结构：

```json
{
  "query": {},
  "body": {},
  "_outputMode": "full"
}
```

硬规则：

- 顶层只允许 `query`、`body`、`_outputMode`。
- 不要拍平 `query/body`，也不要让 CLI 根据字段名重新分流。
- 不传 `context`、`_context`、headers、token、cookie、appasid、appAsId、accAppId 等运行时字段；CLI 从已选择账套加载上下文。
- `bodyMode:none` 的 action 可省略 `body` 或传 `{}`，业务字段按 `show` 文档放入 `query`。
- `bodyMode:list` 的 action，`body` 必须是数组；其他公开 action 的 `body` 必须是对象。
- 参数是否必填、字段类型、枚举值、日期格式、ID 串格式，以 `action show` 返回的 `input.md` 和 `contract.requestParamSchema` 为准。
- 普通查看省略 `_outputMode`；也可显式传 `basic`。
- 只有统计、分析、二次筛选、Top、核对、下游交接或需要完整结构化数据时才传 `_outputMode:"full"`。
- `internal`、`raw-internal`、`system` 是内部编排模式，禁止从 WorkBuddy 传入。
- ACC、SCM、ERP 写操作只有在用户明确确认后才能追加 CLI 参数 `--user-confirmed`；该标志不写入 JSON。

调用时把 JSON 作为命令 stdin 直接提交，不使用 shell `echo` 拼接 JSON。

## 输出展示规则

本节只适用于 ACC、SCM、ERP 的 CLI action。CLI stdout 是 action 完成取数、展示塑形后的最终 JSON，不是原始业务接口响应。不要再次按接口 `rows/raw/data` 自行拼接展示。

普通查看：

- 在返回结果对象中读取 `mustDisplayVerbatim` 和 `primaryDisplayField`。
- 当 `mustDisplayVerbatim=true` 时，按 `primaryDisplayField` 指定的字段原样展示；常见字段是 `displayMarkdown`、`reportMarkdown`、`markdown` 或 `content`。
- 原样展示时不要改写 Markdown 表头、章节顺序、表格列、排序、金额格式、提示语或文件路径。
- `primaryDisplayField` 不存在时，再依据该 action 的 `output.md` 解释结构化结果。
- 面向用户优先输出中文业务结果和必要结论，不要直接贴完整 JSON、字段名清单、错误码堆栈或 CLI 调试过程。

结构化读取：

- 常见结构为 `data.数据`、`data.数据列表`、`data.总数`；具体以 `output.md` 为准。
- 字段含义优先以 `action show` 返回的 `output.md` 为准；只有 CLI 明确返回了可读取的字段映射内容时才继续使用，不要根据 `fieldMap` 路径直接访问 runtime 内部文件。不要把内部 ID 当作普通展示列输出。
- 如果结果包含文件路径、下载路径或导出信息，只在 action 成功且字段真实存在时告知用户。

`basic` 返回的表格只代表默认展示列，不代表 action 的全部返回字段。用户点名查看、筛选、排序、统计或交接默认表格未展示的字段时，先检查 `output.md`；字段已经定义则使用 `_outputMode:"full"` 重新取数，确认未定义后才能说明当前 action 不支持该字段。

## full 模式规则

本节只适用于 ACC、SCM、ERP 的 CLI action。`full` 用于统计分析、二次筛选、Top、核对、下游交接和完整结构化读取；`full` 不等于自动导出 Excel，也不代表可以把全量结构化行直接贴给用户。

使用 `full` 后必须检查数据完整性：

- 比较 `数据列表` 实际长度与 `总数`。
- 如果长度小于总数、存在 `complete=false`、存在分页/截断提示，或 `output.md` 明确说明可能不是全量，不得声称分析覆盖全部数据。
- 数据不完整时，说明当前结果范围和限制，并建议缩小筛选条件、补充期间/账户/类别等条件，或使用系统导出能力。
- 统计金额、数量、Top、占比、异常分析时，如果数据不完整，结论必须标注“基于当前返回数据”。

## 报表规则

本节只适用于 ACC、SCM、ERP 的 CLI action。模板报表和已塑形报表必须优先使用 action 返回的最终正文。只要返回包含 `displayPolicy=verbatim_markdown`、`mustDisplayVerbatim=true` 或明确指定 `primaryDisplayField`，最终回复必须原样展示指定字段。

报表规则：

- 资金日报、资金周报、资金月报等模板报表，最终正文必须来自对应 action 的 `displayMarkdown` 或文档指定字段。
- 不得手写、摘要化、删章节、改标题、改顺序、改表格列、合并表格或只展示局部指标。
- 展示前确认正文包含模板要求的固定章节；如果 action 返回显示正文不完整，应按错误或不完整结果处理。
- 对应模板或 `output.md` 明确要求包含 `报告结束` 时，展示前必须核验；ACC/ERP 财务侧 statement query 不强制追加该标记，仍按其 `primaryDisplayField` 和输出契约原样展示。
- ACC 的 `cashier-daily-report`、`cashier-weekly-report`、`cashier-monthly-report` 是 ACC 资金报表入口。
- ERP 中同名资金报表是 ERP 财务侧入口。不要跨产品混用报表入口。
- SCM/ERP 销售经营报表和 ACC/ERP 资金报表都应通过正式报表 action 生成，不要只查底层列表后自行拼报表。

## 写操作规则

ACC、SCM、ERP 的写操作、状态变更、提交、删除、清理和有业务影响的动作，必须先获得用户明确业务确认。确认后在 CLI 命令上追加 `--user-confirmed`，不要把确认标志写入 JSON。

如果用户只是询问、预览、查询、核对或分析，不要执行写操作。支持 dry-run 的命令可先用 `--dry-run` 查看计划，但 dry-run 结果不能当作真实业务结果。

独立开票不得套用 `--user-confirmed`。其预览、用户确认、认证、额度检查和提交门禁严格按 `invoice/SKILL.md` 及当前流程文档执行。

## 错误处理

ACC、SCM、ERP 的 CLI 与账套错误按错误类型处理，不要把所有错误都改写成“CLI 执行失败”。独立开票错误按本节最后一条执行。

- `source:"cli"`：CLI 参数、索引、进程或协议错误。按错误码修正命令、产品、action 或输入信封。
- `active_product_mismatch`：当前产品与请求产品不一致。先确认用户是否要切换产品或账套。
- 缺少账套上下文：执行 `account switch`；唯一命中后执行 `account current` 核验。
- 候选账套歧义：直接展示 `account switch` 返回的候选，用户确认后执行 `account select`；不要在二者之间重新执行 `account list`。
- `account switch` 未找到匹配项且没有返回候选：执行 `account list`，用户确认候选后再执行 `account select`。
- 账套命令返回认证、网络、权限或服务异常：按原错误处理，不要通过刷新候选规避错误。
- action 未找到：在当前产品重新 `action search`。不要直接跨产品乱搜。
- payload 或 request 参数校验失败：重新执行 `action show`，按 `input.md` 和 `contract` 修正 `query/body`。
- 权限、业务规则、数据不存在、期间未启用等结构化业务错误：保持原业务含义，用中文说明下一步可操作建议。
- 文件导出失败或返回错误文件：不要把错误文件当成 Excel 成果。
- 不得因为接口报错、空数据、无权限、认证失效或服务不可用而自动切换产品、账套、服务或接口域名。先按当前上下文说明问题，只有用户明确要求后才能切换。
- 独立开票的错误、失败反馈和最终措辞按 `invoice/SKILL.md`、当前流程模板和共享输出协议处理，不要改写成通用 CLI 错误。

## 最终回复规则

最终回复使用中文业务语言，优先回答用户问题本身。不要输出 action.py 路径、HTTP 路径、headers、token、appasid、candidateId、完整 CLI JSON、调试日志或不必要的字段名。除账套候选确认确有必要展示的 `asid`、`serviceid` 外，不要向用户展示业务单据 ID、客户 ID、供应商 ID、商品 ID 或其他系统内部 ID。

如果 ACC、SCM、ERP 请求发起或依赖了真实业务数据查询，回复末尾说明本次使用的账套名称和 `serviceid`；如果当前上下文没有账套名称，不要猜测，写“账套名称：未获取”。未发起真实业务请求时，不需要账套尾注。

独立开票最终回复必须按当前开票流程的固定模板和共享输出协议收口；当开票文档要求只输出固定成功或失败文案时，不追加通用账套尾注或其他说明。

当数据为空、被截断、权限不足或筛选条件不完整时，要明确说明范围和限制。不要为了让结果看起来完整而补造数据、猜测金额、猜测期间或猜测业务对象。

用户反馈数据异常、结果不对、不会操作，或明确要求人工、客服、官方帮助时，提示可以前往柠檬云官网联系在线客服。官网地址：https://www.ningmengyun.com/ 。独立开票客服入口和二维码优先使用开票流程规定的 `customer_service_link` 与固定模板。

## CLI 快速参考

```text
lemonclaw-cli auth status
lemonclaw-cli skill-root --check
lemonclaw-cli account current
lemonclaw-cli account switch "<产品或账套线索>"
lemonclaw-cli account list
lemonclaw-cli account select --index <index>
lemonclaw-cli account select --product <product> --name "<账套名称>"
lemonclaw-cli account select --product <product> --asid <asid>
lemonclaw-cli account select --product <product> --serviceid <serviceid> --name "<账套名称>"
lemonclaw-cli action search "用户需求"
lemonclaw-cli action show <product> <action>
lemonclaw-cli action run <product> <action> --json-stdin
```
