# 连接器调用契约与做账侧字段约定

本文件定义 finance-bookkeep-query 连接器的调用方式、工具入参约定，以及做账（分录预览）侧的字段契约。

## 调用机制

本连接器为 **Streamable HTTP MCP** 服务（端点 `https://mcphub.chanapp.chanjet.com/203/mcp`），通过 WorkBuddy MCP Connector 接入。

调用流程：

1. 调用 `获取账套列表` 获取用户可用账套
2. 根据用户指定或默认策略选定账套
3. 调用 `initialize` 传入选定账套建立会话
4. 在会话上下文中调用具体业务工具

会话建立后，后续业务工具调用在该会话上下文中执行，无需在每次调用中重复传入 bookid。

## 连接器能力边界

本连接器只有**只读查询**工具和做账预览所需的科目信息，没有：

- 保存凭证 / 凭证初始化：无法录入或保存凭证
- 租户详情：无法查账套纳税性质、会计准则
- 授权检查：授权状态由网关保证；连接器调用报错即视为不可用

因此：

- 做账分支降级为**分录预览**，输出中必须明确"未录入凭证"
- 分录预览不再回显纳税性质、会计准则（无数据来源）

## 工具与入参速查

| 工具 | 说明 | 关键业务参数 |
|------|------|--------------|
| `获取账套列表` | 获取可用账套 | 无 |
| `initialize` | 根据账套建立会话 | 账套标识 |
| `accountingGlBalanceRptBookid` | 余额表 | `period`（YYYYMM-YYYYMM）、`type`、`startGlAccountCode`/`endGlAccountCode` 或 `glAccountCode`（互斥） |
| `accountingGlGlaccountOpenSearchInitBalanceListBookid` | 科目查询 | `code`、`name`、`searchText` |
| `accountingFinGetNewBalanceSheetBookid` | 资产负债表 | `period`（YYYYMM）、`isReorg` |
| `accountingFinGetOldIncomeStatementBookid` | 利润表 | `period`、`isQuarter`、`enableNewEdition` |
| `accountingGlCashFlowBookid` | 现金流量表 | `period`、`isQuarter` |
| `accountingGlSubsidiaryLedgeQueryPagingBookid` | 明细账 | `queryType`、`startGlAccountCode`/`endGlAccountCode`、`startPeriod`/`endPeriod`、`pageCount`、`pageSize` |
| `accountingAcctgpltCashJournalListBookid` | 日记账 | `period`（YYYYMM）、`glAccountId`（科目 ID，非编码） |
| `accountingGlAcctgTransAcctgTransExactSearchBookid` | 凭证搜索 | `searchParam`（JSON 字符串） |

注意：

- 各工具的具体参数名与类型以 MCP 服务实际返回的 schema 为准
- `searchParam` 必须传序列化后的 JSON 字符串，字段包括：`period`、`subjectNo`、`text`、`assistantType`、`summary`、`writtenPerson`、`startPeriod`、`endPeriod`、`pageCount`、`pageSize`

## 做账（分录预览）契约

### 预览组装来源

- 业务模板：`references/voucher-templates.md`
- 默认科目底表：`references/subject.csv`
- 科目存在性核对：`accountingGlGlaccountOpenSearchInitBalanceListBookid`（可选）

### 分录字段约定（用于预览展示）

每条分录行包含：

- `comments`：摘要（同一张凭证各行默认同一摘要）
- `glAccount.code`：科目编码，来自 `subject.csv` 命中项
- `glAccount.isLeafNode`：来自底表 `isLeaf`
- `glAccount.drCrDirection`：借方 `1`，贷方 `-1`，以底表方向为准
- `basePostedDr` / `basePostedCr`：借方金额 / 贷方金额，未发生方填 `0`，借贷必须平衡

### 预览规则

- 默认科目未命中：停止并说明，不猜测科目
- 命中非末级科目：标注"需下钻到末级科目"，不猜测末级编码；可用科目查询工具尝试查下级
- 预览输出末尾固定说明：当前为分录预览、未录入凭证、连接器不支持保存凭证
- 严禁输出"已保存""已录入"等落账表述

### 期间与摘要

- 用户给定期间则按用户期间展示；未给期间时先取当前系统时间（Bash `date`），禁止凭记忆猜测
- 摘要是用户语义的提取字段，写入每条分录行的 `comments`，不是顶层字段
