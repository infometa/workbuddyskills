## 获取支持的银行列表

```shell
zijizhang-cli bank support_bank_list
```

### 参数说明

无

### 使用示例

```shell
zijizhang-cli bank support_bank_list
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | list    | 银行列表 |

data 元素参数说明（以服务端返回为准）

| 参数       | 类型     | 说明 |
|:----------|:--------|:---|
| id        | int     | 银行 id |
| bank_name | string  | 银行名称 |

补充说明：

- 常用于 `add_bank_account_number` / `del_bank_account_number`
