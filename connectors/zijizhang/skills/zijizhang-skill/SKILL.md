---
name: zijizhang-skill
description: 本技能用于协助用户在「自记账」App 完成记账、报税与报表查询相关操作，支持绑定自记账账号、管理公司员工、银行回单入账、发票入账、生成报税工资单、处理社保申报、审账待办与资产负债表查询。即便用户未明确提及「自记账」App，只要需求涉及上述记账、入账、报税、报表查询或待办处理，也应触发此技能。
version: 0.0.4
---

# zijizhang-skill

专业的记账报税工具，可完成记账、入账、报税、报表查询与待办处理。

## When to Use This Skill

- 用户提及自记账
- 用户需要处理工资单、员工、社保、银行回单/流水、发票、审账待办
- 用户希望申报个税、企业税、增值税、经营所得税、城建税、教育费附加、地方教育附加等税务事项
- 用户需要查询资产负债表、利润表等财务报表数据

## Non-Negotiable Guardrails

以下规则必须严格遵守，优先级高于经验判断：

1. 绝不臆造数据。
只允许使用三类数据推进写操作：
- 用户明确提供的数据
- CLI 返回的数据
- 按 workflow 明确允许推导出的值，例如“当前是 2026-04，用户说本期工资单，则 month 默认为 2026-03”

2. 只要是写操作，必须先向用户确认。
写操作包括但不限于：
- `employee add_employee`
- `employee update_employee`
- `payroll create_payroll`
- `invoice set_month_no_sales_invoice`
- `invoice set_month_no_invoice`
- `invoice upload_invoice_file`
- `invoice invoice_choose_use`
- `social_security social_security_build_task`
- `social_security social_security_agree_tax`
- `social_security social_security_disagree_tax`
- `bank add_bank_account_number`
- `bank del_bank_account_number`
- `bank upload_bank_file`
- `bank choose_bank_use`
- `bank set_month_bank_no_water`
- `todo before_set_month_audited`
- `todo set_month_audited`
- `tax agree_gs_tax_rate`
- `tax disagree_gs_tax_rate`

3. 确认时必须回显关键提交内容。
至少回显以下信息后，再等待用户确认：
- 当前公司 `uid` 或当前激活公司
- 操作对象，例如月份、发票、回单、员工、社保申报期
- 准备提交的关键字段与字段来源
- 哪些字段来自用户，哪些来自 CLI

4. 不得为了凑齐参数而自行补值。
如果 CLI 需要的字段缺失，必须停下来并向用户说明缺了什么，或者先调用 workflow 中要求的上游查询命令补齐。

5. 禁止绕过 skill 既定流程。
只要本 skill 中已有对应 `workflow/*.md` 或 `references/*.md`，必须先按这些文件执行，不要用 `zijizhang-cli --help`、猜参数、试错式探索来替代正式流程。

6. 优先读文档，再执行命令。
顺序固定为：
- 先匹配场景
- 再打开对应 workflow
- 再打开对应 CLI 文档
- 最后执行命令

7. 每次写操作后必须立即校验结果。
- 至少检查返回 `code`
- `code!=200` 时停止后续流程，反馈 `msg`
- 若该流程是异步处理，还要按 workflow 继续查询状态

## Execution Order

每次进入本 skill，按下面顺序推进：

### Step 0：校验 Skill 版本（建议）

执行任务前先校验 `zijizhang-skill` 是否有更新，取本文件顶部 YAML 的 `version:` 值作为参数：

```shell
zijizhang-cli updater check_skill_update '0.0.2'
```

处理规则（详见 `references/check_skill_update.md`）：

- `code != 200`：不阻塞用户业务请求，继续按当前版本执行，并告知"远端查询失败，本次跳过更新检查"
- `code == 200` 且 `data.latest` 高于当前版本：必须提示用户按 `data.installation_guide_url` 升级/覆盖安装（不要自行猜安装命令/来源，是个 zip 包，skill 在 zip 里）
- `must_be_update == true`：必须强提醒用户先升级，再继续可能受版本影响的关键流程

### Step 1：确认登录态与公司上下文

先执行：

```shell
zijizhang-cli account get_cpy_list
```

说明：`get_cpy_list.data[].pending_todo_cnt` 会返回每个公司未完成代办数量（统计口径：`todo get_todo_list.data.todo_list` 中 `state=0` 的条目数；查询失败时为 `null`）。

判断规则：

- 若返回 `code=200` 且存在当前激活公司：记录激活 `uid`，继续
- 若 token 失效、未登录或未绑定：严格按“绑定账号步骤”执行
- 若需要切换公司：先按 `references/switch_to.md` 执行 `account switch_to '<uid>'`
- ⚠️ **切换公司完成后的第一件事必须执行** `todo get_todo_list --uid='<uid>'` 获取该公司的待办明细，再进入后续 workflow

### Step 2：识别任务类型并打开对应 workflow

按场景选择：

- 工资单：`workflow/payroll.md`
- 销项发票：`workflow/invoice_sales.md`
- 进项发票：`workflow/invoice_income.md`
- 发票上传：`workflow/invoice_upload.md`
- 社保：`workflow/social_security.md`
- 个税：`workflow/individual_tax.md`
- 报表查询：无独立 workflow，直接打开对应 CLI 文档，例如 `references/get_report_zcfzb.md`、`references/get_report_lrb.md`

如果任务是待办处理，先 `todo get_todo_list`，再根据待办类型进入对应 workflow。

### Step 3：打开对应 CLI 文档

执行具体命令前，先读对应文档：

- 命令格式、必填参数、返回结构，以 `references/*.md` 为准
- 不允许跳过文档直接凭记忆或 `--help` 自行探索

### Step 4：先查后写

- 先做读取型查询，拿到真实上下文
- 再整理提交参数
- 再向用户确认
- 最后执行写操作

## Additional Resources

- Workflow: `workflow/*.md`
- CLI docs: `references/*.md`
- Skill 更新（Agent 流程）: `references/auto_update.md`

## Dependencies

Python packages (install once):

```shell
pip install --upgrade zijizhang-cli
```

⚠️要求：`zijizhang-cli` 版本需为 `0.0.28` 及以上

检查版本：

```shell
zijizhang-cli --version
```

## Feature Map

以下命令仅作为能力索引；真正执行时，仍必须回到对应 workflow 和 CLI 文档。

| 模块 | 功能 | 命令 | 文档 |
| --- | --- | --- | --- |
| `account` | 创建登录授权链接 | `zijizhang-cli account create_auth_url` | `references/create_auth_url.md` |
| `account` | 获取可切换公司列表 | `zijizhang-cli account get_cpy_list` | `references/get_cpy_list.md` |
| `account` | 切换公司 | `zijizhang-cli account switch_to '<uid>'` | `references/switch_to.md` |
| `account` | 退出登录 | `zijizhang-cli account logout` | `references/logout.md` |
| `employee` | 获取员工列表 | `zijizhang-cli employee get_employee_list --uid='<uid>' --keyword='<keyword>'` | `references/get_employee_list.md` |
| `employee` | 添加员工 | `zijizhang-cli employee add_employee '<data>' --uid='<uid>'` | `references/add_employee.md` |
| `employee` | 修改员工信息 | `zijizhang-cli employee update_employee '<employee_id>' '<data>'` | `references/update_employee.md` |
| `payroll` | 获取工资单创建状态 | `zijizhang-cli payroll get_payroll_creation_status '<month>' --uid='<uid>'` | `references/get_payroll_creation_status.md` |
| `payroll` | 获取预览工资单 | `zijizhang-cli payroll get_preview_payroll '<month>' --uid='<uid>'` | `references/get_preview_payroll.md` |
| `payroll` | 创建工资单 | `zijizhang-cli payroll create_payroll '<month>' '<data>' --uid='<uid>'` | `references/create_payroll.md` |
| `payroll` | 获取工资单 | `zijizhang-cli payroll get_payroll '<month>' --uid='<uid>'` | `references/get_payroll.md` |
| `payroll` | 删除工资单 | `zijizhang-cli payroll remove_payroll '<month>' --uid='<uid>'` | `references/remove_payroll.md` |
| `invoice` | 获取销项发票列表 | `zijizhang-cli invoice get_sales_invoice_data_list ...` | `references/get_sales_invoice_data_list.md` |
| `invoice` | 获取进项发票列表 | `zijizhang-cli invoice get_income_invoice_data_list ...` | `references/get_income_invoice_data_list.md` |
| `invoice` | 标记无销项发票 | `zijizhang-cli invoice set_month_no_sales_invoice '<year>' '<month>' --uid='<uid>'` | `references/set_month_no_sales_invoice.md` |
| `invoice` | 标记无进项发票 | `zijizhang-cli invoice set_month_no_invoice --uid='<uid>' '<year>' '<month>'` | `references/set_month_no_invoice.md` |
| `invoice` | 确认收到的发票已全部录入完成 | `zijizhang-cli invoice check_invoice_over --uid='<uid>' '<year>' '<month>'` | `references/check_invoice_over.md` |
| `invoice` | 上传发票文件 | `zijizhang-cli invoice upload_invoice_file --uid='<uid>' --file='<file>'` | `references/upload_invoice_file.md` |
| `invoice` | 查询发票文件列表 | `zijizhang-cli invoice invoice_file_list --uid='<uid>' --current='<current>'` | `references/invoice_file_list.md` |
| `invoice` | 获取进项发票可选用途 | `zijizhang-cli invoice invoice_can_choose_use_list ...` | `references/invoice_can_choose_use_list.md` |
| `invoice` | 进项发票用途入账 | `zijizhang-cli invoice invoice_choose_use ...` | `references/invoice_choose_use.md` |
| `social_security` | 获取当月社保申报概览 | `zijizhang-cli social_security social_security_now_month_report_info --uid='<uid>'` | `references/social_security_now_month_report_info.md` |
| `social_security` | 获取社保历史记录 | `zijizhang-cli social_security social_security_history_list --uid='<uid>' --current='<current>'` | `references/social_security_history_list.md` |
| `social_security` | 获取社保明细 | `zijizhang-cli social_security social_security_get_mx_data '<year>' '<month>' --sb_type='<sb_type>' --uid='<uid>'` | `references/social_security_get_mx_data.md` |
| `social_security` | 创建社保申报任务 | `zijizhang-cli social_security social_security_build_task '<year>' '<month>' --sb_type='<sb_type>' --uid='<uid>'` | `references/social_security_build_task.md` |
| `social_security` | 同意社保税额并发起缴款 | `zijizhang-cli social_security social_security_agree_tax '<year>' '<month>' --uid='<uid>'` | `references/social_security_agree_tax.md` |
| `social_security` | 驳回社保税额 | `zijizhang-cli social_security social_security_disagree_tax '<year>' '<month>' --uid='<uid>'` | `references/social_security_disagree_tax.md` |
| `tax` | 获取当前需要申报的税种列表和申报情况 | `zijizhang-cli tax tax_detail --uid='<uid>'` | `references/tax_detail.md` |
| `tax` | 获取某个月份个税申报概览信息 | `zijizhang-cli tax month_gs_report_info '<year>' '<month>' --uid='<uid>'` | `references/month_gs_report_info.md` |
| `tax` | 获取某个月份个税明细数据 | `zijizhang-cli tax gs_month_mx '<year>' '<month>' --uid='<uid>'` | `references/gs_month_mx.md` |
| `tax` | 同意个税税额/费率（确认金额） | `zijizhang-cli tax agree_gs_tax_rate '<year>' '<month>' '<agree_type>' --uid='<uid>'` | `references/agree_gs_tax_rate.md` |
| `tax` | 不同意个税税额/费率（驳回金额） | `zijizhang-cli tax disagree_gs_tax_rate '<year>' '<month>' --uid='<uid>'` | `references/disagree_gs_tax_rate.md` |
| `bank` | 获取支持银行列表 | `zijizhang-cli bank support_bank_list` | `references/support_bank_list.md` |
| `bank` | 获取银行账号列表 | `zijizhang-cli bank bank_account_number_list --uid='<uid>'` | `references/bank_account_number_list.md` |
| `bank` | 添加银行账号 | `zijizhang-cli bank add_bank_account_number --bank_id='<bank_id>' --bank_number='<bank_number>' --uid='<uid>'` | `references/add_bank_account_number.md` |
| `bank` | 删除银行账号 | `zijizhang-cli bank del_bank_account_number --bank_id='<bank_id>' --bank_number='<bank_number>' --uid='<uid>'` | `references/del_bank_account_number.md` |
| `bank` | 上传银行文件 | `zijizhang-cli bank upload_bank_file --uid='<uid>' --file='<file>' --file_type='<回单或明细>' --bank_account_number_id='<id>' --billing_cycle='<YYYY-MM-DD>'` | `references/upload_bank_file.md` |
| `bank` | 查询银行文件列表 | `zijizhang-cli bank bank_file_list --uid='<uid>' --current='<current>'` | `references/bank_file_list.md` |
| `bank` | 获取银行回单/流水列表 | `zijizhang-cli bank get_bank_bill_data_list --uid='<uid>' --current='<current>' --date_begin='<date_begin>' --date_end='<date_end>'` | `references/get_bank_bill_data_list.md` |
| `bank` | 回单用途入账 | `zijizhang-cli bank choose_bank_use '<bill_id>' '<rule_text>' --uid='<uid>'` | `references/choose_bank_use.md` |
| `bank` | 标记无回单/流水 | `zijizhang-cli bank set_month_bank_no_water '<year>' '<month>' --uid='<uid>'` | `references/set_month_bank_no_water.md` |
| `todo` | 获取待办列表 | `zijizhang-cli todo get_todo_list --uid='<uid>'` | `references/get_todo_list.md` |
| `todo` | 审账前确认 | `zijizhang-cli todo before_set_month_audited '<year>' '<month>' --uid='<uid>'` | `references/before_set_month_audited.md` |
| `todo` | 提交审账 | `zijizhang-cli todo set_month_audited '<year>' '<month>' --uid='<uid>'` | `references/set_month_audited.md` |
| `report` | 获取资产负债表 | `zijizhang-cli report zcfzb '<begin>' '<end>' --uid='<uid>'` | `references/get_report_zcfzb.md` |
| `report` | 获取利润表 | `zijizhang-cli report lrb '<begin>' '<end>' --uid='<uid>'` | `references/get_report_lrb.md` |

## Usage

在正式操作前，先检查是否已绑定账号：

```shell
zijizhang-cli account get_cpy_list
```

`get_cpy_list` 会在公司列表中一并返回每家公司的 `pending_todo_cnt`（未完成代办数量）；如需查看代办明细，再执行 `references/get_todo_list.md`。

如果不能正常获取公司列表，或提示 `token` 过期，则按以下步骤绑定。

### 绑定账号步骤

1. 打开 `references/create_auth_url.md`，执行创建授权链接
2. 打开授权链接并按页面提示登录
3. 打开 `references/get_cpy_list.md`，获取公司列表（包含 `pending_todo_cnt`）
4. 如需切换公司，打开 `references/switch_to.md` 并执行 `account switch_to '<uid>'`
5. ⚠️ **切换完成后立即执行** `references/get_todo_list.md`（`todo get_todo_list --uid='<uid>'`），再总结给用户

## Workflow

### 工资单

- 创建或查询工资单：`workflow/payroll.md`

### 发票

- 销项：`workflow/invoice_sales.md`
- 进项：`workflow/invoice_income.md`
- 上传：`workflow/invoice_upload.md`

### 社保

- 社保申报：`workflow/social_security.md`

### 银行回单/流水

- 银行回单/流水处理：`workflow/bank.md`

### 个税

- 个税待办处理：`workflow/individual_tax.md`

### 审账

- 审账待办处理：`workflow/audit.md`

### 待办处理

**核心原则：用户说"处理代办"或类似意图时，agent 必须主动引导、逐项推进，直到全部完成。不要等用户逐项指定。**

1. 先执行：

```shell
zijizhang-cli todo get_todo_list --uid='<uid>'
```

2. 待办分为**主流程**和**独立流程**两类：

**主流程（严格按顺序逐项处理，前一项完成后再进入下一项）：**

| 顺序 | 代办类型 | 说明 | 处理原则 |
| --- | --- | --- | --- |
| 1 | `EMPLOYEE` | 员工 | 先查 `get_employee_list`；若缺员工或入职日期不符合，再向用户确认后新增/修改 |
| 2 | `PAYROLL` | 工资单 | 严格按照 `workflow/payroll.md` |
| 3 | `BANK` | 回单/流水 | 严格按照 `workflow/bank.md` |
| 4 | `SALES` | 销项发票 | 严格按照 `workflow/invoice_sales.md` |
| 5 | `INCOME` | 进项发票 | 严格按照 `workflow/invoice_income.md` |
| 6 | `AUDIT` | 审账 | 严格按照 `workflow/audit.md`（必须所有主流程前置项完成后才能审账） |

**独立流程（用户要求时单独处理，不阻塞主流程）：**

| 待办类型 | 说明 | 处理原则 |
| --- | --- | --- |
| `SOCIAL_SECURITY` | 社保 | 严格按照 `workflow/social_security.md` |
| `GS` | 个税 | 严格按照 `workflow/individual_tax.md` 执行，会有多个月份的待办需逐一处理 |

3. **逐项引导流程（每项必须走完以下闭环）：**

   a. **告知用户**当前处理的是第几项、是什么类型、当前进度（如"第 2/5 项：工资单"）

   b. **读取对应 workflow 文档**，按文档步骤执行查询，收集必要信息

   c. **整理提交参数并向用户确认**，回显关键信息

   d. **用户确认后执行写操作**，检查结果 `code`

   e. **成功后告知用户**该项已完成，并询问是否继续下一项（默认自动继续，用户说"停"才停止）

   f. **失败时停止**，反馈错误原因，等用户指示

4. 每处理完一项，重新查询待办列表确认状态，然后进入下一项。直到全部变为 `state=1` 或遇到失败/用户停止。

5. **全部完成后**向用户汇报总结：共处理 X 项，全部完成 / X 项完成 Y 项失败。

## 待办展示格式规范

查询待办后，必须按以下格式展示给用户。格式分两种场景：

### 场景A：查询单家公司待办

先显示公司名和记账期，然后用进度条+表格展示所有待办项：

```
**公司名** 记账期：YYYY年M月

| 状态 | 名称 | 说明 |
|:----:|------|------|
| ✅ | 员工信息 | 已添加1位员工 |
| ❌ | 申报5月社保 | 已缴纳社保费¥3,270.00，查看详情 |
| ✅ | 4月份工资单 | 查看工资单 |
| ✅ | 4月份回单 | 已录入3张，已全部录入 |
| ✅ | 4月份销项发票 | 无发票 |
| ✅ | 4月份进项发票 | 无发票 |
| ✅ | 提交审账 | 4月份已提交审账 |
```

规则：
- 状态列：✅ = 已完成（state=1），❌ = 未完成（state=0）
- 名称列：直接使用 `name` 字段
- 说明列：直接使用 `desc` 字段
- 未完成项排在前面，已完成项排在后面
- 表格上方显示进度条（完成数/总数）

### 场景B：查询多家公司待办汇总

先显示汇总概览，再逐公司展开：

```
**待办汇总** 共5家公司，5项未完成

| 公司 | 未完成 | 已完成 | 未完成项 |
|------|:------:|:------:|----------|
| 珠海唤嚟科技 | 1 | 6 | 申报5月社保 |
| 珠海秀力科技 | 1 | 6 | 申报5月社保 |
| ... | ... | ... | ... |
```

若用户追问某公司详情，再切换到场景A格式。

## Notes / Limitations

- 所有金额单位均为元，不是分
- 涉及验证码、税额、用途、垫付人、银行账号等信息时，必须向用户确认，不能自行假设
- 如果 workflow 与 zijizhang-cli 发生冲突，以 `zijizhang-cli --help` 里面实际参数定义为准；但执行顺序仍应遵守 workflow
- 表格生成规则
  - 必须用标准 Markdown 表格格式
  - 表头、分隔线、内容行**列数必须完全一致**
  - 空缺的内容可用空字符串填充
  - 每一列必须对齐，不能缺失
