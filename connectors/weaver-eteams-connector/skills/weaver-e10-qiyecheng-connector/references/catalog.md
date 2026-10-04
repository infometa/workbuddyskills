# FNA 齐业成费控接口目录

对应 `weaver-work-cli fna` 的 13 个 operation，覆盖源资料四大模块 11 个接口（预算 2 / 费用中心 3 / 借款管理 3 / 发票核销 3，其中提醒还款与催票拆为 prepare/apply 两个操作）。完整接口路径与认证由 weaver-work-cli 托管，Agent 只写业务 JSON。

## 一、预算查询（budget，2 个）

| 用户意图 | operation | 说明 |
|---|---|---|
| 「这个事前申请单预算还剩多少」「某 requestId 的预算情况」 | `fna.budget.application.detail` | GET 详情，requestId 必填，返回预算总额/已报销/报销中/剩余可用/已释放 |
| 「预算执行报表」「某模板/部门/期间预算执行情况」 | `fna.budget.execute.list` | POST 报表，current/pageSize 必填，templateId 为空仅返回表头 |

- 均为公开 AI 接口（`publicPermission=true`），只读无写副作用。
- 预算执行报表期间筛选 `periodName` 传**金额列名**（`budget_amount1`~`budget_amount12`），维度 key（`dimenMem1` 等）随模板 `corrColumn` 变化；`formDatas` 每个 value 是「单元素数组包裹同名 key 数组」的二层嵌套，拼错层级会筛选失效而不是报错。
- 汇总口径优先读响应 `totals`（customParameters）中 `budget_sumAmount` 前缀字段，金额/比率为字符串。

## 二、费用中心（expense，3 个）

| 用户意图 | operation |
|---|---|
| 「我/某人报销了多少」「某时间段报销金额合计」 | `fna.expense.reimbursed.sum` |
| 「还有多少借款没还」「各状态借款金额/笔数」 | `fna.expense.loan.sum` |
| 「预付核销进度」「未到账多少」 | `fna.expense.prepay.writeoff.sum` |

- 共用 `SumAmountByAiVo`（employeeId/startDate/endDate/workflowId/requestId），**body 可为空**，不传按当前登录人。
- 报销口径：明细状态 `status=1`（审批完成）的 `reimburse_amount` 合计 = 已报销金额；无数据返回 `0.0`。
- ⚠️ 借款接口缺陷：仅统计首条借款记录（对外汇报注明）；且首次/冷启动可能瞬时空响应（缺 data 键），CLI 自动重试最多 2 次。
- 借款接口 requestId 等必须传数字；预付核销接口日期按核销记录创建时间、employeeId 匹配预付单创建人。

## 三、借款管理（loan，管理员）

| 用户意图 | operation | 风险 |
|---|---|---|
| 「全公司待还款/还款中多少钱」 | `fna.loan.main.page` | read |
| 「列出借款单」「谁还欠多少」 | `fna.loan.main.list` | read |
| 「提醒某人/批量提醒还款」 | `fna.loan.remind.repay.prepare` / `.apply` | **write** |

- `mainPageList` 必填 `current`/`pageSize`/`menuCode`/`permissionSetCode`（示例 `fesx_fna_borrowingManagement`，需与环境核对）。
- 数据流：`fna.loan.main.list` 返回 `rows`（displayData 行，含 id/workflowId/jkrPersonName/dhkAmount）→ 原样回传 `fna.loan.remind.repay.prepare` → 用户确认 → `apply`。
- 金额：`data` 原始精度、`displayData` 已格式化；`createTime` 在 displayData 为 `yyyy-MM-dd HH:mm:ss`。

## 四、发票核销财务（invoice-writeoff，财务/管理员）

| 用户意图 | operation | 风险 |
|---|---|---|
| 「发票核销未核销/核销中多少」 | `fna.invoice.writeoff.summary` | read |
| 「列出发票核销单」「谁还有多少没核销」 | `fna.invoice.writeoff.list` | read |
| 「催票/批量催票」 | `fna.invoice.writeoff.callticket.prepare` / `.apply` | **write** |

- `invoiceStatus` 过滤：`unWritten`/`unarrivedTicket`/`dealing`/`callTicket`；`menuCode`/`permissionSetCode` 示例 `inv_write_off_financial(.default)`。
- 数据流：`fna.invoice.writeoff.list` 返回行 `requestId`（= `id`）→ 组装 `requestids` 传给 `callticket.prepare` → 用户确认 → `apply`。

## 通用约定

- 失败时按错误 envelope 的 `type/subtype` 处理：`confirmation.required` 缺确认；`partial.write_uncertain` 不确定结果立即停止并回查，禁止自动重试。
- 无记录时输出 `total=0`/空 `rows` 或 `segments:null`，提示「暂无记录」，不得伪造成功。
- 全部金额字段单位为元。
