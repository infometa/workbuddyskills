## 获取银行账号列表

```shell
zijizhang-cli bank bank_account_number_list --uid='<uid>'
```

### 参数说明

| 参数  | 类型     | 必填 | 说明 |
|:----|:--------|:---|:---|
| uid | string  | ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | list    | 银行账号列表 |

data 元素参数说明

| 参数         | 类型     | 说明 |
|:------------|:--------|:---|
| bank_id     | int     | 银行 id |
| bank_name   | string  | 银行名称 |
| bank_number | string  | 银行账号 |
