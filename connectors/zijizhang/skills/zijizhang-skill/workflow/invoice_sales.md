# SALES（销项/开出的发票）工作流

目标：判断本记账期是否存在销项发票，并在“确认无销项发票”时做标记。

写操作保护：

- `set_month_no_sales_invoice` 属于写操作，执行前必须向用户回显 `year`、`month`、`uid` 与“无销项发票”的确认依据
- 若用户表示“本期有开票”，不能为了完成待办而直接标记“无销项发票”

## Step 1：查询本期销项发票

```shell
zijizhang-cli invoice get_sales_invoice_data_list --uid='<uid>' --invoice_date_begin='<本期开始>' --invoice_date_end='<本期结束>' --current=1
```

分页说明：

- 返回中包含 `data.current`、`data.page_size`、`data.total`、`data.invoice_list`
- 若 `data.total > len(data.invoice_list)`，必须继续用 `--current=2,3...` 拉取后续页，直到覆盖全部发票后再做“是否存在发票”的判断（避免只查到第 1 页导致漏判）

期望结果：

- `code=200`
- 从 `data.total` 或 `data.invoice_list` 判断是否存在发票（以返回为准）

分支规则：

- 若存在销项发票：提示用户“系统将在每月 1 号后自动获取并录入”（无需继续做“无销项发票”标记）
- 若不存在销项发票：继续 Step 2

## Step 2：向用户确认是否确实无销项发票

- 若用户确认“本期没有开出发票”：执行 Step 3
- 若用户确认“本期有开出发票”：提示系统自动录入；如用户坚持要上传文件，仅支持 `pdf/ofd`，按 `workflow/invoice_upload.md` 上传即可（`code=200` 可继续上传；上传完再用 `invoice_file_list` 查看处理状态）

## Step 3：标记本月无销项发票

只有在下面两个条件同时满足时才可执行：

- 本期查询结果确实未查到销项发票
- 用户明确确认“本期没有开出发票”

```shell
zijizhang-cli invoice set_month_no_sales_invoice '<year>' '<month>' --uid='<uid>'
```

期望结果：

- `code=200`

失败分支：

- `code!=200`：停止推进，向用户反馈 `msg`
