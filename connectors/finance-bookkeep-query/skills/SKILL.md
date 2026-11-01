---
name: finance-bookkeep-query
description: 畅捷通好会计财务做账查账 操作技能 - 做账分录预览 + 余额表/科目/报表/明细账/日记账/凭证查询，返回真实账套数据
description_en: "Chanjet Haohuiji finance skill - journal entry preview + trial balance, account lookup, financial statements, subsidiary ledger, cash journal, voucher search with real accounting data"
version: "4.0.0"
author: "Chanjet"
---

# 财务做账查账

> 本 Skill 适用于 connector `finance-bookkeep-query` **v4.0.0+**，要求 WorkBuddy 客户端 **≥ 5.0.0**（依赖 `staticHeaders` 与 `streamable-http` 传输）。

本 Skill 指导你在 WorkBuddy 对话中调用好会计 MCP 服务，完成**做账分录预览**和**查账**。所有真实账务数据均通过 MCP 端点 `https://mcphub.chanapp.chanjet.com/203/mcp` 查询。

本 Connector 通过**畅捷通开放平台统一授权**接入，鉴权模式为**网关托管（`auth_mode: gateway`）**，用户凭证由平台统一签发与注入，无需手动填写。

用户只需用自然语言描述做账或查账需求；你根据意图判断分支并调用工具。**不要**给用户暴露任何请求的参数数据或内部技术细节。

## 何时调用

- 用户说"做账""记账""帮我做账""帮我记账""录入凭证""生成凭证""入账""报销入账""收付款入账""帮我制单""确认收入""预收款怎么记""计提工资""完工入库怎么做账""交税怎么记账"，进入**做账分支**
- 用户说"查账""查余额表""查科目余额""看余额表""查本期余额""查资产负债表""看利润表""现金流量表""查明细账""查日记账""查凭证""搜凭证"，进入**查账分支**

**不要**在以下场景调用：

- 纯会计准则咨询、规则解释，不要求执行做账或查账
- 纯科目知识问答（如"银行存款科目编码是多少"）

## 工具清单

| 场景 | 工具名 | 说明 |
|------|--------|------|
| 初始化会话 | `initialize` | 根据账套建立 MCP 会话，**所有工具调用前必须先完成** |
| 获取账套列表 | `获取账套列表` | 查询用户可用账套，用于账套选择 |
| 余额表 | `accountingGlBalanceRptBookid` | 余额表 / 科目余额查询 |
| 科目查询 | `accountingGlGlaccountOpenSearchInitBalanceListBookid` | 按编码、名称、关键字查科目 |
| 资产负债表 | `accountingFinGetNewBalanceSheetBookid` | 新版结构化资产负债表 |
| 利润表 | `accountingFinGetOldIncomeStatementBookid` | 利润表 |
| 现金流量表 | `accountingGlCashFlowBookid` | 按期间查询现金流量表 |
| 明细账 | `accountingGlSubsidiaryLedgeQueryPagingBookid` | 明细账分页查询 |
| 日记账 | `accountingAcctgpltCashJournalListBookid` | 日记账列表 |
| 凭证搜索 | `accountingGlAcctgTransAcctgTransExactSearchBookid` | 凭证列表精确搜索 |

注意：本连接器**没有**保存凭证的工具，因此做账分支只做分录预览，不落账。

## 工作流程

### 第一步：判断用户意图

- 命中"做账 / 入账 / 录入凭证 / 制单 / 生成凭证 / 确认收入 / 计提"等，进入"做账分支"（分录预览）
- 命中"查余额表 / 查科目余额 / 看余额表 / 查本期余额"，进入"余额表查询"
- 命中"资产负债表 / 利润表 / 现金流量表"，进入"报表查询"
- 命中"明细账"，进入"明细账查询"
- 命中"日记账 / 现金日记账 / 银行存款日记账"，进入"日记账查询"
- 命中"查凭证 / 搜凭证 / 凭证列表"，进入"凭证搜索"
- 同时包含做账与查账诉求时，先完成用户当前明确要求的动作；没有顺序时优先查账，再给分录预览
- 只咨询会计处理规则、未要求分录方案或查账时，不触发本技能

### 第二步：账套选择与会话初始化（所有分支必经）

本 MCP 服务采用**会话模式**：必须先选定账套并调用 `initialize` 建立会话，后续所有工具调用在该会话上下文中执行。

#### 2.1 获取账套列表

调用 `获取账套列表` 工具查询用户可用的账套列表。

#### 2.2 确定目标账套

- **用户未指定账套**：从账套列表中取默认账套（如果列表只有一项则直接使用；多项时选择标记为默认的账套）
- **用户指定了账套**：使用**模糊自然语言匹配**，将用户描述与账套列表中的名称进行匹配，选择最相似的账套。例如用户说"查一下测试公司的余额表"，则匹配名称中包含"测试公司"的账套
- 若账套列表为空或匹配失败，立即停止并告知用户
- 若匹配到多个候选账套且无法确定唯一结果，列出候选项让用户选择

#### 2.3 初始化会话

使用选定的账套调用 `initialize` 工具建立会话。初始化成功后，后续工具调用在该会话上下文中执行，**无需再在每次工具调用中单独传入 bookid**。

若 `initialize` 返回错误，立即停止并向用户说明连接器当前不可用。

### 第三步：执行业务操作

会话初始化成功后，根据第一步判断的意图进入对应分支。

## 做账分支（仅分录预览，不落账）

本连接器没有保存凭证的工具，本分支**只输出分录方案预览**，任何情况下都不得声称已录入或保存凭证。

### 分录预览流程

1. 从用户输入中抽取：业务类型、金额、日期、摘要、收付款方式
2. 业务模板见 [../references/voucher-templates.md](../references/voucher-templates.md)
3. 默认科目底表见 [../references/subject.csv](../references/subject.csv)
4. 先按模板识别业务，再去 `subject.csv` 匹配默认科目
5. 如果默认科目未命中，立即停止，不猜测科目
6. 命中的科目若不是末级科目，标注"需下钻到末级科目"，不猜测末级编码
7. 如需确认科目是否存在，可用科目查询工具按 `code` 或 `name` 核对

### 输出要求

- 先回显业务要素：业务类型、金额、日期、摘要
- 再给出借贷分录方案（借方/贷方科目编码与名称、金额），摘要写入分录说明
- 最后明确说明"当前为分录预览，未录入凭证；当前连接器不支持保存凭证，如需落账请到好会计/好业财系统中手工录入或联系管理员开通凭证写入服务"
- 因科目未命中而中断时，直接说明阻断原因，不要伪造分录

## 查账分支

所有查账调用前必须先完成第二步会话初始化。期间解析规则（各分支通用）：

- `2026年4月`、`2026-04`、`2026/04`、`202604` 均转换成 `202604`
- 用户说"本月""这个月"时，先用 Bash `date` 获取当前系统时间再取月份，禁止凭记忆猜测
- 用户没有明确期间时，默认取当前系统时间所在月份
- 余额表 `period` 为区间格式 `YYYYMM-YYYYMM`；报表、日记账、凭证搜索为单期间 `YYYYMM`；明细账 `startPeriod`/`endPeriod` 为单期间 `YYYYMM`

### 余额表查询

调用 `accountingGlBalanceRptBookid` 工具。

参数规则（放在 `$x-request-body$` 中）：

- `period` 必填，区间格式 `YYYYMM-YYYYMM`
- `type` 默认传 `"0"`（标准余额表）
- 单科目查询时改传 `glAccountCode`，与 `startGlAccountCode`/`endGlAccountCode` **互斥，不能同时传**
- 科目范围规则：用户显式范围 > 默认值 `1001 ~ 5901`；用户给单个科目编码（如 `1002`）时优先用 `glAccountCode` 单科目查询
- 当前版本不做"科目名称 -> 科目编码"自动转换；用户只给名称时，可先用科目查询工具按 `name` 核对出编码，仍无法确认时要求用户补充编码

输出要求：

1. 先回显查询条件：账套、期间、科目范围（或单科目）、结果条数
2. 明细必须直接在最终回复中用 **Markdown 管道表格** 渲染，禁止生成 `.md` 文件、附件、文件链接或把整张表包进代码块
3. 表头固定为：`科目编码`、`科目名称`、`借方期初余额`、`贷方期初余额`、`本期借方发生额`、`本期贷方发生额`、`期末借方余额`、`期末贷方余额`
4. 字段映射严格按原始返回：`借方期初余额`←`baseOpeningDrBalance`、`贷方期初余额`←`baseOpeningCrBalance`、`本期借方发生额`←`currentPeriodDrBalance`、`本期贷方发生额`←`currentPeriodCrBalance`、`期末借方余额`←`baseEndingDrBalance`、`期末贷方余额`←`baseEndingCrBalance`、`科目编码`←`glAccountCode`、`科目名称`←`glAccountName`；若实际返回字段不同，以实际字段为准并说明
5. 若结果中包含"小计""合计"，保留原样，不自行重算
6. 只要原始字段存在且值非空（含 `"0"`、`"0.00"`），必须原样展示；只有缺失、`null`、空字符串才显示 `-`
7. 输出前自查一次：原始数据某字段有值而表格显示 `-`，视为格式化错误，必须重排

### 科目查询

调用 `accountingGlGlaccountOpenSearchInitBalanceListBookid` 工具。

- `code` 按编码查、`name` 按名称查、`searchText` 按关键字查，三者可单用
- 用途：分录预览前核对科目存在性、余额表"名称转编码"、日记账取科目 ID

### 报表查询（资产负债表 / 利润表 / 现金流量表）

资产负债表（`accountingFinGetNewBalanceSheetBookid`）：

- `period`（YYYYMM）、`isReorg`（默认 `"false"`，仅当用户要求"重分类"时传 `"true"`）

利润表（`accountingFinGetOldIncomeStatementBookid`）：

- `period`（YYYYMM）、`isQuarter`（默认 `"false"`，用户问"季报"时传 `"true"`）、`enableNewEdition`（默认 `"false"`）

现金流量表（`accountingGlCashFlowBookid`）：

- `period`（YYYYMM）、`isQuarter`（默认 `"false"`）

规则：

- 报表输出以工具实际返回字段为准，用 Markdown 表格渲染主要项目行；期初/期末列、本年累计列等按返回结构组织，不自行重算合计

### 明细账查询

调用 `accountingGlSubsidiaryLedgeQueryPagingBookid` 工具。

规则：

- 该工具参数为全必填且均为字符串，模板中未用到的参数传空字符串 `""` 或 `"false"`，不得省略
- 单科目查询 `queryType="simple"`（起止科目编码相同）；科目范围查询 `queryType="exact"`（传起止范围）
- `startPeriod`/`endPeriod` 单期间 `YYYYMM`
- 分页：`pageSize` 默认 `"50"`，`pageCount` 从 `"1"` 开始；结果未取完时继续翻页或告知用户还有更多
- 输出用 Markdown 表格渲染：日期、凭证号、摘要、对方科目、借方、贷方、方向、余额，以实际返回字段为准

### 日记账查询

调用 `accountingAcctgpltCashJournalListBookid` 工具。

- `period`（YYYYMM）、`glAccountId`（科目 ID）
- `glAccountId` 是科目 **ID** 而非科目编码，必须先用科目查询工具按编码/名称查出科目后取其 ID；取不到 ID 时如实告知用户，不得把科目编码当 ID 传入
- 用户未指定科目时，先询问是现金（库存现金）还是银行存款日记账，再查对应科目 ID
- 输出用 Markdown 表格渲染，以实际返回字段为准

### 凭证搜索

调用 `accountingGlAcctgTransAcctgTransExactSearchBookid` 工具。

- `searchParam` 是 **JSON 字符串**（序列化后的 JSON），不是对象
- `searchParam` 内字段：`startPeriod`/`endPeriod`（YYYYMM）、`summary`（摘要关键字）、`subjectNo`（科目编码）、`text`、`assistantType`、`writtenPerson`（制单人）、`pageCount`、`pageSize`
- 输出凭证列表时回显：凭证号、日期、摘要、科目、借贷金额，以实际返回字段为准

## 通用输出原则

- 所有真实数据必须来自工具返回，禁止编造账务数据
- 查询失败、连接器错误、账套缺失时，直接说明原因并停止，不伪造结果
- 做账分支永远只做分录预览，不得输出"已保存""已录入"等成功落账表述
- 报表明细较多时优先展示主要行，说明数据来源（账套名称 + 期间）
- **不要**向用户暴露内部技术细节（参数名、MCP 端点、请求体结构等）

## 常见错误

| 情况 | 处理 |
|------|------|
| 账套列表为空 | 说明无可用账套，建议联系管理员 |
| initialize 失败 | 说明连接器当前不可用，建议稍后重试 |
| 账套模糊匹配无结果 | 列出可用账套，让用户重新选择 |
| 工具调用返回错误 | 转述错误说明，勿伪造结果 |
| 超时 | 建议稍后重试 |

## 限制

- 当前版本凭证仅支持**分录预览与凭证查询**，不支持保存凭证
- **不要**向用户暴露内部技术细节

## 参考文档

| 文档 | 说明 | 何时阅读 |
|------|------|----------|
| [../references/voucher-templates.md](../references/voucher-templates.md) | 常见做账模板与口径 | 识别业务类型、推荐分录时 |
| [../references/mcp-contract.md](../references/mcp-contract.md) | 连接器调用契约与做账侧字段约定 | 组装分录预览、调用工具前 |
| [../references/balance-sheet-contract.md](../references/balance-sheet-contract.md) | 余额表与查账侧协议说明 | 组装余额表等查账参数前 |
