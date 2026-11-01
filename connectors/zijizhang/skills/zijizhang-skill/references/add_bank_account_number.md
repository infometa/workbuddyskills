## 添加银行账号

```shell
zijizhang-cli bank add_bank_account_number --uid='<uid>' --bank_id='<bank_id>' --bank_number='<bank_number>'
```

### 参数说明

| 参数         | 类型     | 必填 | 说明 |
|:------------|:--------|:---|:---|
| uid         | string  | ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |
| bank_id     | int     | ✅  | 银行 id（来自 `support_bank_list` 返回的银行 id） |
| bank_number | string  | ✅  | 银行账号 |

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据（以服务端返回为准） |

