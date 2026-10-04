# 预算查询

## 何时使用

用户问「事前申请单预算还剩多少」「某 requestId 的预算/报销情况」→ 事前申请单预算详情；问「预算执行报表」「某模板/部门/期间预算执行情况」→ 预算执行报表。两者都是只读查询，无写副作用。

## 事前申请单预算详情（fna.budget.application.detail）

### 输入要点

- `requestId` 必填：事前申请单 ID（数字），用户只给申请名称/事由时先向其索要 requestId，不要自行拼 ID 解析接口。
- 预算口径：预算总额 = 已报销 + 报销中 + 剩余可用 + 已释放；若不等，提示数据可能未刷新或存在并发在途变更。

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.budget.application.detail --input-json '{"requestId":"1001"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.budget.application.detail --input-json '{"requestId":"1001"}'
```

### 输出处理

返回归一化对象：`requestId`/`requestName`/`createPerson`/`createTime` + `budget{totalAmount,reimbursedFee,reimbursingFee,remainingBudget,releasedBudgetAmount,isDisplay}`；`meta.rawForm` 为原始 WeaForm。汇报时展示申请名称、发起时间、预算总额与剩余可用预算即可，不必粘贴整份表单。

## 预算执行报表（fna.budget.execute.list）

### 输入要点

- `current`/`pageSize` 必填（正整数）；`templateId` 预算模板 ID，为空只返回表头（正常行为，不是错误）。
- `formDatas`（可选）：维度/期间筛选。**嵌套陷阱**：每个 value 是「单元素数组包裹同名 key 数组」的二层嵌套；`periodName` 传金额列名 `budget_amount1`~`budget_amount12`（对应 1~12 月）；维度成员传 `[{"dimenMem1":[{"id":"...","name":"..."}]}]`，维度 key 由模板 `corrColumn` 决定，不要臆造。
- `type`：`and`/`or`；`ignoreReportPower` 仅内部/管理员场景，默认不传。

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.budget.execute.list --input-json '{"current":1,"pageSize":100,"templateId":"1192927724873392129","formDatas":{"periodName":[{"periodName":["budget_amount1"]}]}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.budget.execute.list --input-json '{"current":1,"pageSize":100,"templateId":"1192927724873392129","formDatas":{"periodName":[{"periodName":["budget_amount1"]}]}}'
```

### 输出处理

返回 `{total,current,pageSize,hasMore,periodFlag,columns,rows,totals}`。汇总问题（预算总额/已报销/剩余可用/执行率）优先读 `totals` 中 `budget_sumAmount` 前缀的合计字段（字符串，转数值、比率去 `%`）；明细看 `rows`。

### 注意

- `templateId` 为空仅返回表头，需提示用户传入正确的模板 ID。
- 字段列与维度 key 因模板而异，本 Skill 不臆造，必要时请用户提供模板维度配置。

## 失败处理

`code!=200`/`status!=true` → 停止并按错误 envelope 汇报，不切换到其它近义接口重试。
