## 确认收到的发票已全部录入完成（完成进项/收到的发票代办）

```shell
zijizhang-cli invoice check_invoice_over --uid='<uid>' '<year>' '<month>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                            |
|:------|:-------|:---|:----------------------------------------------------------------------------------------------|
| year  | int    | ✅  | 年份，如 2026                                                                                    |
| month | int    | ✅  | 月份(1-12)，如 3                                                                                  |
| uid   | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |

### 使用示例

#### 确认当前公司 2026 年 3 月收到的发票已全部录入完成

```shell
zijizhang-cli invoice check_invoice_over 2026 3
```

#### 确认 uid=xxxx 的 2026 年 3 月收到的发票已全部录入完成

```shell
zijizhang-cli invoice check_invoice_over --uid='xxxx' 2026 3
```

### 返回参数

| 参数   | 类型     | 说明                    |
|:-----|:-------|:----------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string | 提示信息，失败时为异常信息         |
| data | dict   | 结果数据，当 code=200 时返回   |

data 参数说明

| 参数    | 类型     | 说明           |
|:------|:-------|:-------------|
| uid   | string | 当前设置所属的 `uid` |
| year  | int    | 年份           |
| month | int    | 月份           |

