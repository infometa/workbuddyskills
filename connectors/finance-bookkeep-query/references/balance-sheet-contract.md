# 余额表与查账侧协议

本文档定义查账侧的账套选择、会话初始化、余额表查询协议，以及各查账工具的输出约定。工具均通过 WorkBuddy MCP Connector（`finance-bookkeep-query`）调用。

## 账套选择与会话初始化

### 获取账套列表

调用 `获取账套列表` 工具查询用户可用账套。

### 确定目标账套

- **用户未指定账套**：取默认账套（列表只有一项则直接使用；多项时选择标记为默认的账套）
- **用户指定了账套**：使用**模糊自然语言匹配**，将用户描述与账套列表中的名称进行匹配，选择最相似的账套
- 若匹配到多个候选且无法确定唯一结果，列出候选项让用户选择
- 若账套列表为空或匹配失败，立即停止

### 初始化会话

使用选定的账套调用 `initialize` 工具建立 MCP 会话。初始化成功后，后续工具调用在该会话上下文中执行。

## 余额表：`accountingGlBalanceRptBookid`

### 业务入参

字段说明：

| 字段 | 含义 | 规则 |
|------|------|------|
| `period` | 会计期间区间 | 必填，格式 `YYYYMM-YYYYMM`；单期间如 `202604` 转成 `202604-202604` |
| `type` | 余额表类型 | 默认 `"0"`（标准）；`1` 数量金额、`2` 外币金额、`3` 外币数量 |
| `startGlAccountCode` | 起始科目编码 | 可选，与 `glAccountCode` 互斥 |
| `endGlAccountCode` | 结束科目编码 | 可选，包含下级科目（如 `1001` 含 `100101`） |
| `glAccountCode` | 单科目编码 | 可选，单科目查询；与起止范围互斥，不能同时传 |

优先级：

- 科目条件：用户显式范围（或单科目） > 默认值 `1001 ~ 5901`
- 期间：用户问题解析结果 > 当前系统年月（用 Bash `date` 获取，禁止凭记忆猜测）
- 用户只给科目名称时，可先用科目查询工具按 `name` 核对编码；仍无法确认时要求用户补充编码

### 出参字段映射

| 字段 | 含义 |
|------|------|
| `glAccountCode` | 科目编码 |
| `glAccountName` | 科目名称 |
| `baseOpeningDrBalance` | 借方期初余额 |
| `baseOpeningCrBalance` | 贷方期初余额 |
| `currentPeriodDrBalance` | 本期借方发生额 |
| `currentPeriodCrBalance` | 本期贷方发生额 |
| `baseEndingDrBalance` | 期末借方余额 |
| `baseEndingCrBalance` | 期末贷方余额 |

出参示例：

```json
[
  {
    "glAccountName": "银行存款",
    "baseOpeningDrBalance": "222000.00",
    "currentPeriodCrBalance": "0.00",
    "baseEndingDrBalance": "222000.00",
    "baseOpeningCrBalance": "0",
    "currentPeriodDrBalance": "0.00",
    "glAccountCode": "1002"
  },
  {
    "glAccountName": "合计",
    "baseOpeningDrBalance": "410495.58",
    "currentPeriodCrBalance": "0.00",
    "baseEndingDrBalance": "410495.58",
    "baseOpeningCrBalance": "410495.58",
    "currentPeriodDrBalance": "0.00",
    "glAccountCode": ""
  }
]
```

### 渲染规则

- 明细用 Markdown 管道表格直接渲染在回复中，禁止生成文件、附件或整表包进代码块
- "小计""合计"行保留原样，不自行重算
- 只要字段存在且值非空（含 `"0"`、`"0.00"`），必须原样展示；仅缺失、`null`、空字符串才显示 `-`
- 输出前自查：原始字段有值而表格显示 `-`，视为格式化错误，必须重排
- 若实际返回字段与上表命名不同，以实际返回为准并在回复中说明

## 科目查询：`accountingGlGlaccountOpenSearchInitBalanceListBookid`

- `code` / `name` / `searchText` 按需单用，用于科目核对、名称转编码、日记账取科目 ID

## 报表（资产负债表 / 利润表 / 现金流量表）

- 资产负债表：`accountingFinGetNewBalanceSheetBookid`，`period`（YYYYMM）、`isReorg`（默认 `"false"`）
- 利润表：`accountingFinGetOldIncomeStatementBookid`，`period`、`isQuarter`（默认 `"false"`）、`enableNewEdition`（默认 `"false"`）
- 现金流量表：`accountingGlCashFlowBookid`，`period`、`isQuarter`（默认 `"false"`）
- 输出结构以实际返回为准，主要项目行用 Markdown 表格渲染，合计行不重算

## 明细账：`accountingGlSubsidiaryLedgeQueryPagingBookid`

- 所有参数必填且均为字符串，未用到的传 `""` 或 `"false"`
- 单科目 `queryType="simple"`（起止编码相同）；范围 `queryType="exact"`
- `startPeriod`/`endPeriod` 单期间 `YYYYMM`；分页 `pageSize` 默认 `"50"`、`pageCount` 从 `"1"` 起

## 日记账：`accountingAcctgpltCashJournalListBookid`

- `period`（YYYYMM）、`glAccountId`
- `glAccountId` 是科目 **ID** 而非编码，先用科目查询工具取 ID；取不到时如实告知，禁止把编码当 ID 传

## 凭证搜索：`accountingGlAcctgTransAcctgTransExactSearchBookid`

- `searchParam`（**JSON 字符串**）
- `searchParam` 内字段：`period`、`subjectNo`、`text`、`assistantType`、`summary`（摘要关键字）、`writtenPerson`（制单人）、`startPeriod`、`endPeriod`、`pageCount`、`pageSize`
