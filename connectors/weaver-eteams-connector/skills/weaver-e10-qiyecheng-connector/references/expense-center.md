# 费用中心（报销 / 借款 / 预付核销）

## 何时使用

三个查询共用 `SumAmountByAiVo`，**body 可为空**（默认当前登录人）。每个意图只选一个接口，不要自动切换近义接口。

| 用户意图 | operation |
|---|---|
| 「我/某人某时间段报销了多少」「这笔报销流程报销了多少钱」 | `fna.expense.reimbursed.sum` |
| 「还有多少借款没还」「各状态借款金额/笔数」 | `fna.expense.loan.sum` |
| 「预付核销进度」「未到账多少」 | `fna.expense.prepay.writeoff.sum` |

## 输入要点

- `employeeId`/`workflowId`/`requestId` 都是数字 ID（借款接口只认数字，字符串会静默返回空 data）；用户给姓名/流程名时先请其提供数字 ID。
- `startDate`/`endDate` 格式 `YYYY-MM-DD`，必须成对提供；**日期口径不同**：报销按明细费用日期、借款按流程创建时间、预付核销按核销记录创建时间。
- 人员口径差异：报销按明细归属人、预付核销按预付单创建人匹配。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.expense.reimbursed.sum --input-json '{"employeeId":12345,"startDate":"2026-01-01","endDate":"2026-08-31"}'
weaver-work-cli --profile eteams --json fna run fna.expense.loan.sum --input-json '{"requestId":1304980982180151297}'
weaver-work-cli --profile eteams --json fna run fna.expense.prepay.writeoff.sum --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.expense.reimbursed.sum --input-json '{"employeeId":12345,"startDate":"2026-01-01","endDate":"2026-08-31"}'
weaver-work-cli --profile eteams --json fna run fna.expense.loan.sum --input-json '{"requestId":1304980982180151297}'
weaver-work-cli --profile eteams --json fna run fna.expense.prepay.writeoff.sum --input-json '{}'
```

## 输出处理

- 报销：`data.amount`（元）；无数据返回 `0.0`。
- 借款：`data.segments` 为 `{dhk,hkz,yhk,jk}` 四段 `{amount,count,costType}`；`segments:null` 表示暂无借款记录；以 key 判断状态，不依赖 costType 文案（可能是文案或状态码）。
- 预付核销：`paymentAmount`/`writeOffing`/`writeOffed`/`noArrivedAmount`（未到账 = 预付 − 已到账 − 已核销），无数据兜底 0。

## 注意（口径与缺陷）

- **借款查询实现缺陷**：`getSumLoanAmountByAi` 只统计首条借款记录（for 循环内 return），对外汇报注明「可能仅反映首条记录口径，待开发修复」，不作权威结论。
- **借款瞬时空响应**：首次/冷启动偶发 `code:200` 但整个 `data` 缺失，CLI 已自动重试最多 2 次；若仍为空按「暂无借款记录」处理并提示可稍后重试，不要误判为确定无记录。
- 报销无数据是 `0.0`、借款无数据是 `null`、预付核销兜底 `0`，三者空值语义不同。

## 失败处理

`code!=200`/`success!=true` → 停止并向用户说明查询失败，建议稍后重试或联系管理员；不自行拼装其它接口路径重试。
