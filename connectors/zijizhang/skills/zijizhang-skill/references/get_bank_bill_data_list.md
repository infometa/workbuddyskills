## 获取银行回单/流水列表

```shell
zijizhang-cli bank get_bank_bill_data_list --uid='<uid>' --current='<current>' --date_begin='<date_begin>' --date_end='<date_end>'
```

### 参数说明

| 参数        | 类型     | 必填 | 说明                                                                                            |
|:----------|:-------|:---|:----------------------------------------------------------------------------------------------|
| uid       | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |
| current   | int    | ❌  | 页码，默认 1                                                                                      |
| date_begin| string | ❌  | 交易日期开始，格式 `YYYY-MM-DD`（如需使用，需与 `date_end` 同时传）                                                |
| date_end  | string | ❌  | 交易日期结束，格式 `YYYY-MM-DD`（如需使用，需与 `date_begin` 同时传）                                               |

### 使用示例

#### 获取当前公司回单列表，第 1 页

```shell
zijizhang-cli bank get_bank_bill_data_list --current=1
```

#### 获取 2026-03 的回单/流水

```shell
zijizhang-cli bank get_bank_bill_data_list --date_begin='2026-03-01' --date_end='2026-03-31'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当 code=200 时返回       |

data 参数说明

| 参数        | 类型     | 说明 |
|:----------|:-------|:---|
| uid       | string | 查询所属的 `uid` |
| current   | int    | 当前页码 |
| page_size | int    | 每页条数 |
| total     | int    | **服务端总条数**（非当前页条数），用于判断是否还有更多页 |
| bill_list | list   | 当前页回单列表 |

> **分页说明**：`bill_list` 每页返回 `page_size` 条。`total` 为服务端总条数。
> 若需获取全部数据，判断规则为：**当已累计获取的条数 < `total` 时，继续递增 `current` 翻页，直到 `bill_list` 为空或已累计条数 >= `total` 为止**。

bill_list 元素参数说明（以服务端返回为准）

| 参数              | 类型     | 说明 |
|:----------------|:--------|:---|
| id              | int     | 回单 id |
| accounting_date | string | 交易日期（常见为时间戳或 yyyy-mm-dd） |
| money_type      | string     | 金额类型（支出|收入） |
| money           | string     | 交易金额（元） |
| account_name    | string  | 对方户名 |
| account_number  | string  | 对方账号 |
| opening_institution | string | 对方开户行 |
| bank_name       | string  | 我方户名 |
| bank_number     | string  | 我方账号 |
| branch_name     | string  | 我方开户行 |
| status          | string     | 状态（待审核|待确认|已入账） |
| remark          | string  | 备注 |
| summary         | string  | 摘要 |
| use_list        | list    | 可选用途列表（当 status=待确认 时有值，['货款', '无票收入']） |

