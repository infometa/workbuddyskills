## 上传银行文件（明细：Excel；回单：PDF）

```shell
zijizhang-cli bank upload_bank_file --uid='<uid>' --file='<file>' --file_type='<file_type>' --bank_account_number_id='<id>' --billing_cycle='<billing_cycle>'
```

### 参数说明

| 参数                    | 类型     | 必填 | 说明 |
|:----------------------|:--------|:---|:---|
| uid                   | string  | ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |
| file                  | string  | ✅  | 银行文件路径；`file_type=明细` 仅支持 `.xls/.xlsx`，`file_type=回单` 仅支持 `.pdf` |
| file_type             | string  | ✅  | 文件类型：`明细` 或 `回单` |
| bank_account_number_id| int     | ✅  | 银行账户 id（来自 `bank_account_number_list` 返回的账号 id） |
| billing_cycle         | string  | ✅  | 回单文件所属月份，格式 `YYYY-MM-DD`（如 `2026-03-01`） |

### 使用示例

```shell
zijizhang-cli bank upload_bank_file --file='/path/to/bank.pdf' --file_type='回单' --bank_account_number_id=123 --billing_cycle='2026-03-01'
```

上传明细（Excel）示例：

```shell
zijizhang-cli bank upload_bank_file --file='/path/to/detail.xlsx' --file_type='明细' --bank_account_number_id=123 --billing_cycle='2026-03-01'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据（以服务端返回为准） |

