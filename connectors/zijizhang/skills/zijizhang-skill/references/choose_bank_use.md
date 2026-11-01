## 回单选择用途/入账

```shell
zijizhang-cli bank choose_bank_use '<bill_id>' '<rule_text>' --uid='<uid>'
```

### 参数说明

| 参数       | 类型     | 必填 | 说明                                                                                            |
|:---------|:--------|:---|:----------------------------------------------------------------------------------------------|
| bill_id       | int     | ✅  | 回单单据 id（来自 `get_bank_bill_data_list.data.bill_list[].id`）                                   |
| rule_text| string  | ✅  | 用途文本（建议从 `bill_list[].use_list` 中选择一个）                                                       |
| uid      | string  | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |

### 使用示例

```shell
zijizhang-cli bank choose_bank_use '123456' '货款'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据（可能为空对象）              |

