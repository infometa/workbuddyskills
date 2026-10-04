---
name: weaver-e10-qiyecheng-connector
display_name: 泛微齐业成费控
display_name_en: Weaver Qiyecheng FNA
description: 泛微齐业成费控中心（预算查询/费用中心/借款管理/发票核销）的 E10 查询与提醒写操作能力，通过 weaver-work-cli fna 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_zh: 泛微齐业成费控中心助手：事前申请单预算详情、预算执行报表、报销/借款/预付核销金额、全公司借款汇总与列表、提醒还款、发票核销金额与列表、催票。所有能力通过 weaver-work-cli fna 命令执行，提醒还款与催票为写操作，必须先 prepare 预览并经用户明确确认后 apply。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Expense, budget and loan assistant for Weaver Qiyecheng FNA. Queries pre-application budget details, budget execution reports, reimbursed/loan/prepay amounts, company-wide loan summary and list, invoice write-off summary and list. Sends repayment reminders and invoice call-tickets through the weaver-work-cli fna command with a prepare/apply confirmation chain. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli fna --help"
---

# weaver-work-cli 齐业成费控（FNA）Skill

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

所有调用统一走 `weaver-work-cli fna ...`，禁止绕过 CLI 直接 curl/fetch E10 接口，禁止读取、复制、打印或解析 Cookie、ETEAMSID、Token 或 `~/.e10-cli` 等认证目录；登录诊断只允许 `weaver-work-cli auth root/status/profile list/profile current`、`weaver-work-cli doctor --e10` 和业务命令 JSON 错误。

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 适用场景（何时使用本技能）

用户提到事前申请单预算、预算执行报表、报销/借款/预付核销金额、全公司借款汇总与列表、提醒还款、发票核销金额与列表或催票时，使用本技能。

发票票夹与 OCR 走 `weaver-e10-yepiaotong-connector`，人员与流程 ID 解析不属于本技能范围。

## 能力范围

| 能力 | 说明 | 身份 |
|---|---|---|
| 预算查询 | 事前申请单预算详情、预算执行报表（只读） | 登录即可（接口公开） |
| 费用中心 | 报销金额合计、借款金额分段、预付核销金额（只读） | 登录即可（默认当前登录人） |
| 借款管理 | 全公司待还/还款中汇总、全员借款单列表（只读）；提醒还款（写） | 管理员 |
| 发票核销财务 | 金额 tab 汇总、核销列表（只读）；催票（写） | 财务/管理员 |

## 路由优先级

先判断用户意图归属哪个模块，再选择 operation；一个意图只选最匹配的一个接口，目标不明确先提问收窄，不自动切换近义接口。**只有借款/发票核销模块涉及提醒类写操作，先 `prepare` 出预览并请用户明确确认，再 `apply`；禁止未确认自动执行。**

- 「这个事前申请单预算还剩多少」「某 requestId 的预算情况」→ `fna.budget.application.detail`
- 「预算执行报表」「某模板/部门/期间预算执行情况」→ `fna.budget.execute.list`
- 「我/某人某段时间报销了多少」→ `fna.expense.reimbursed.sum`
- 「还有多少借款没还」「各状态借款金额/笔数」→ `fna.expense.loan.sum`
- 「预付核销进度」「未到账多少」→ `fna.expense.prepay.writeoff.sum`
- 「全公司待还款/还款中多少钱」→ `fna.loan.main.page`
- 「列出借款单」「谁还欠多少」→ `fna.loan.main.list`
- 「提醒某人/批量提醒还款」→ `fna.loan.remind.repay.prepare` → 确认 → `fna.loan.remind.repay.apply`
- 「发票核销未核销/核销中多少」→ `fna.invoice.writeoff.summary`
- 「列出发票核销单」→ `fna.invoice.writeoff.list`
- 「催票/批量催票」→ `fna.invoice.writeoff.callticket.prepare` → 确认 → `fna.invoice.writeoff.callticket.apply`

## Operation 表（以 `weaver-work-cli fna schema` 为准）

| 操作 | 风险 | 说明 |
|---|---|---|
| `fna.budget.application.detail` | read | GET 事前申请单预算详情（requestId 必填） |
| `fna.budget.execute.list` | read | POST 预算执行报表（current/pageSize 必填） |
| `fna.expense.reimbursed.sum` | read | 报销金额合计（body 可为空） |
| `fna.expense.loan.sum` | read | 借款金额分段汇总（已知缺陷：仅统计首条借款记录；瞬时空响应自动重试） |
| `fna.expense.prepay.writeoff.sum` | read | 预付核销金额汇总 |
| `fna.loan.main.page` | read | 借款首页汇总（dhk/hkz） |
| `fna.loan.main.list` | read | 借款首页列表（menuCode/permissionSetCode 必填） |
| `fna.loan.remind.repay.prepare` | write | 提醒还款预览（不发送） |
| `fna.loan.remind.repay.apply` | write | 提醒还款（confirm+continuation） |
| `fna.invoice.writeoff.summary` | read | 发票核销金额 tab |
| `fna.invoice.writeoff.list` | read | 发票核销列表 |
| `fna.invoice.writeoff.callticket.prepare` | write | 催票预览（不发送） |
| `fna.invoice.writeoff.callticket.apply` | write | 催票（confirm+continuation） |

## 前置依赖与口径约定

- **ID 解析不在本 Skill**：姓名→`employeeId`、流程名→`workflowId` 依赖人员/流程解析接口，源资料未提供；用户只给姓名/流程名时先索要数字 ID，禁止编造 ID 或接口。
- `menuCode`/`permissionSetCode` 环境相关（借款 `fesx_fna_borrowingManagement(.default)`、核销 `inv_write_off_financial(.default)`），不确定时先与用户核对实际值。
- 金额双套口径：`data` 原始精度字符串（计算）、`displayData` 格式化（展示/回传）；金额单位为元。
- 费用中心日期口径不同：报销按明细费用日期、借款按流程创建时间、预付核销按核销记录创建时间。
- 借款费用中心接口 requestId/employeeId/workflowId 只认**数字**（字符串会静默返回空）；超 2^53 的巨型 ID 保留字符串并提示人工核验。

## 执行原则

1. 业务输入只描述业务对象与意图；认证与接口地址全部由 CLI 托管。
2. 列表/详情可能返回大响应：只保留回答所需字段，给摘要与总数，不原样粘贴超长 JSON。
3. 金额/比率为字符串时转数值使用（比率需去 `%`）。
4. 借款金额查询已知实现缺陷：对外汇报注明「可能仅反映首条记录口径」。
5. 写操作（remindRepay/callTicket）失败决策树：`partial` / `write_uncertain` / 登录失效 / 网络中断 → **立即停止，禁止自动重试**，做一次只读回查（`fna.loan.main.list` / `fna.invoice.writeoff.list`）后向用户汇报；若返回 `confirmation.required`，说明缺少明确确认，先 prepare 再确认后 apply。
6. 金额结论口径存疑时（如借款缺陷、瞬时空响应）先说明不确定性；`total=0` 或空列表提示「暂无记录」，不得伪造成功。

## References

| 需要 | 读取 |
|---|---|
| 接口目录与按模块路由 | [references/catalog.md](references/catalog.md) |
| 预算：事前申请单预算详情 / 预算执行报表 | [references/budget.md](references/budget.md) |
| 费用中心：报销 / 借款 / 预付核销 | [references/expense-center.md](references/expense-center.md) |
| 借款管理：汇总 / 列表 / 提醒还款（prepare→apply） | [references/loan-management.md](references/loan-management.md) |
| 发票核销：金额 tab / 列表 / 催票（prepare→apply） | [references/invoice-writeoff.md](references/invoice-writeoff.md) |
| 源资料指纹与更新检测 | [references/source-manifest.json](references/source-manifest.json) |

## 命令示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.budget.application.detail --input-json '{"requestId":"1001"}'
weaver-work-cli --profile eteams --json fna run fna.expense.loan.sum --input-json '{"employeeId":12345,"startDate":"2026-01-01","endDate":"2026-08-31"}'
weaver-work-cli --profile eteams --json fna run fna.loan.main.list --input-json '{"current":1,"pageSize":20,"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.budget.application.detail --input-json '{"requestId":"1001"}'
weaver-work-cli --profile eteams --json fna run fna.expense.loan.sum --input-json '{"employeeId":12345,"startDate":"2026-01-01","endDate":"2026-08-31"}'
weaver-work-cli --profile eteams --json fna run fna.loan.main.list --input-json '{"current":1,"pageSize":20,"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
```

## 附件与文件安全

本 Skill 的 11 个接口均为查询/提醒类，**不涉及附件、图片或文件上传解析**。若后续扩展接口涉及附件或文件内容解析，必须先向用户说明「附件内容可能会发送到当前大模型服务处理，可能进入大模型上下文」，并在用户明确确认后才能处理；不得把用户仅提供路径或文件名视为同意解析或上传。

## 不在本 Skill 范围

- 借款「确认已还 confirmRepay」、核销明细等页面按钮能力（源资料未提供接口）→ 见 `weaver-work-cli fna schema` 的 `withheldOperations`，不得编造 operation 或直连接口。
- 姓名/流程名 → ID 的解析、创建借款单/预付单/事前申请单等需联动工作流的写流程（未提供接口依据）。
- 其它模块（发票票夹、人事、流程待办）请路由到对应 Skill，不在此重复实现。
