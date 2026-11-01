# INCOME（进项/收到的发票）工作流

目标：确保本期收到的发票已录入并完成“用途选择/入账”。

写操作保护：

- `set_month_no_invoice`、`upload_invoice_file`、`invoice_choose_use`、`check_invoice_over` 都属于写操作，执行前必须先向用户确认
- `category` 必须来自 `invoice_can_choose_use_list.data.items` 返回值或用户明确指定
- `is_pay`、`payee` 必须来自用户确认或 CLI 返回的候选信息，不能自行猜测

## Step 1：向用户确认本期是否有收到发票

- 若用户确认“没有收到发票”：可在最后执行 `set_month_no_invoice`（见 Step 5）
- 若用户确认“有收到发票”：继续 Step 2

## Step 2：如需上传发票文件（仅 `pdf/ofd`）

- 仅当用户提供 `pdf/ofd` 文件时才可用 CLI 上传
- 上传按 `workflow/invoice_upload.md` 执行：会同步返回 `data.file_state`（成功/拒绝）与 `data.file_state_desc`（处理结果描述）；提示结果后可继续上传下一个文件
- “选择用途/入账”由代办触发：等用户确认“已上传完全部发票文件”后，再执行 `zijizhang-cli todo get_todo_list` 触发并进入后续处理

## Step 3：查询待确认的进项发票（用于入账）

```shell
zijizhang-cli invoice get_income_invoice_data_list --uid='<uid>' --status='待确认' --current=1
```

分页说明：

- 返回中包含 `data.current`、`data.page_size`、`data.total`、`data.invoice_list`
- 若 `data.total > len(data.invoice_list)`，必须继续用 `--current=2,3...` 拉取后续页，确保本期所有 `status='待确认'` 的发票都被处理（避免只处理第 1 页）

期望结果：

- `code=200`
- 若 `data.invoice_list` 为空：进入 Step 4/Step 5 做最终确认
- 若存在待确认发票：对每张发票执行 Step 3.1 与 Step 3.2

### Step 3.1：查询该发票可选用途列表

```shell
zijizhang-cli invoice invoice_can_choose_use_list --uid='<uid>' --invoice_id='<invoice_id>'
```

期望结果：

- `code=200`
- `data.items` 返回可选用途（以返回为准）

失败分支：

- `code!=200`：停止推进，向用户反馈 `msg` 并请用户确认是否补齐参数/改走 App 处理

### Step 3.2：选择用途并入账

先向用户回显以下内容，再等待确认：

- `invoice_id`
- 发票关键信息，例如发票号码、货物名称、金额、税价合计
- 准备提交的 `category`、`is_pay`、`payee`
- 这些值分别来自哪里

只有用户明确确认后，才可以执行：

```shell
zijizhang-cli invoice invoice_choose_use --uid='<uid>' --invoice_id='<invoice_id>' --category='<category>' --is_pay='<is_pay>' --payee='<payee>'
```

期望结果：

- `code=200`

分支规则：

- 每处理一张后，重新执行一次 Step 3，直到不再存在 `status='待确认'` 的发票

## Step 4：最终确认本期是否已录入收到的发票

```shell
zijizhang-cli invoice get_income_invoice_data_list --uid='<uid>' --invoice_date_begin='<本期开始>' --invoice_date_end='<本期结束>' --current=1
```

分页说明：

- 若 `data.total > len(data.invoice_list)`，必须继续用 `--current=2,3...` 拉取后续页，避免“本期确实有发票但第 1 页为空”的误判

期望结果：

- `code=200`
- 若不存在发票：进入 Step 5
- 若存在发票：
  - 仍需以 `todo get_todo_list` 的 INCOME 代办状态为准
  - 当 **待确认发票已全部处理完**（Step 3 结果为空），但 INCOME 代办仍为未完成（`state=0`）时，必须先向用户确认“本期收到的发票已全部录入完成”，再执行 `check_invoice_over` 完成代办（见下方 Step 4.1）

### Step 4.1：确认本期收到的发票已全部录入完成（完成代办）

触发条件（需同时满足）：

- Step 3 查询 `status='待确认'` 的发票为空（待处理发票已全部处理完）
- Step 4 查询本期发票列表存在发票（说明本期确实有收到发票）
- `zijizhang-cli todo get_todo_list --uid='<uid>'` 中 INCOME 代办仍未完成（`state=0`）

执行前必须向用户确认（写操作保护）：**“本期收到的发票已经全部录入完成，确认要完成该代办吗？”**

用户确认后才可执行：

```shell
zijizhang-cli invoice check_invoice_over --uid='<uid>' '<year>' '<month>'
```

期望结果：

- `code=200`
- 重新执行 `zijizhang-cli todo get_todo_list --uid='<uid>'`，确认 INCOME 代办已变为完成（`state=1`）

## Step 5：标记本月无进项发票（可选）

仅当用户确认“本期确实没有收到发票”时执行：

```shell
zijizhang-cli invoice set_month_no_invoice --uid='<uid>' '<year>' '<month>'
```

期望结果：

- `code=200`

失败分支：

- `code!=200`：停止推进，向用户反馈 `msg`
