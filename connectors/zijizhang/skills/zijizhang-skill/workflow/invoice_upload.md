# INVOICE 上传文件工作流（同步返回状态）

当流程涉及 `upload_invoice_file` 上传发票文件时，上传接口会同步返回文件处理结果：

- `data.file_state`：`成功`｜`拒绝`
- `data.file_state_desc`：处理结果描述
  - 若为 `拒绝`：为拒绝原因
  - 若为 `成功`：为该文件内发票数据当前状态描述（如：正在财务审核中等待处理｜已成功入账｜需要您选择用途）

每次上传完成后，先向用户提示该文件的处理结果，然后可继续上传下一个文件。

写操作保护：

- 上传前必须先向用户确认要上传的文件路径列表
- 只允许上传用户明确提供的本地文件
- 不能自己猜文件、替用户挑文件，或把不确定来源的文件提交到系统

## Step 1：上传（仅 `pdf/ofd`；可连续上传多个文件）

逐个文件回显给用户确认后，再执行：

```shell
zijizhang-cli invoice upload_invoice_file --uid='<uid>' --file='<发票文件路径>'
```

期望结果（成功分支）：

- `code=200` 且 `data.file_state=成功`：向用户提示 `data.file_state_desc`，然后进入 Step 2 继续上传下一份文件
- `code=200` 且 `data.file_state=拒绝`：向用户提示“被拒绝”与 `data.file_state_desc`（拒绝原因），然后进入 Step 2 继续上传下一份文件

失败分支：

- 若 `code!=200`：停止推进，向用户反馈 `msg`，并请用户确认是否更换文件（仅支持 `.pdf/.ofd`）

## Step 2：继续上传下一个文件（循环）

- 对剩余待上传文件，重复 Step 1
- 若用户还要追加上传新文件：必须先让用户明确提供新文件路径，再继续执行 Step 1

## Step 3：确认已上传完全部文件后，触发代办逻辑

- 必须先让用户确认：“已上传完全部发票文件/不再继续上传”
- 用户确认后，执行查看代办列表（用于触发后续“选择用途/入账”等代办处理）：

```shell
zijizhang-cli todo get_todo_list --uid='<uid>'
```

## Step 4（可选）：查看已上传文件记录

```shell
zijizhang-cli invoice invoice_file_list --uid='<uid>' --current=1
```

说明：

- `invoice_file_list` 的 `data.items[].status` 会从“处理中/解析中/待处理”等状态，变化为“成功/已处理/失败/被拒绝”等终态（以服务端返回为准）
- ⚠️ 被 `拒绝` 的文件不会出现在 `invoice_file_list` 中；拒绝原因以 `upload_invoice_file` 返回的 `data.file_state_desc` 为准
