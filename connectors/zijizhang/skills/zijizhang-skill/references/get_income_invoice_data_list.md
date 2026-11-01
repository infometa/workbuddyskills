## 获取进项/收到的发票列表

```shell
zijizhang-cli invoice get_income_invoice_data_list --uid='<uid>' --current='<current>' --invoice_number='<invoice_number>' --invoice_date_begin='<invoice_date_begin>' --invoice_date_end='<invoice_date_end>'
```

### 参数说明

| 参数               | 类型     | 必填 | 说明                                                                                            |
|:-----------------|:-------|:---|:----------------------------------------------------------------------------------------------|
| uid              | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |
| current          | int    | ❌  | 页码，默认 1                                                                                      |
| invoice_number   | string | ❌  | 发票号码关键字（精确匹配），不传则查询全部                                                                          |
| invoice_date_begin | string | ❌  | 开票日期开始，格式 `YYYY-MM-DD`（如需使用，需与 `invoice_date_end` 同时传）                                          |
| invoice_date_end | string | ❌  | 开票日期结束，格式 `YYYY-MM-DD`（如需使用，需与 `invoice_date_begin` 同时传）                                         |
| status           | string | ❌  | 发票状态（审核中/待确认/已拒绝/已入账），不传则查询全部                                                             |

### 使用示例

#### 获取当前公司进项/收到的发票列表，第1页

```shell
zijizhang-cli invoice get_income_invoice_data_list --current=1
```

#### 获取账号下 uid=xxxx 的进项/收到的发票列表

```shell
zijizhang-cli invoice get_income_invoice_data_list --uid='xxxx'
```

#### 获取开票日期为2026-03-01到2026-03-31的进项/收到的发票列表

```shell
zijizhang-cli invoice get_income_invoice_data_list --invoice_date_begin='2026-03-01' --invoice_date_end='2026-03-31'
```

#### 获取状态为待确认的进项/收到的发票列表

```shell
zijizhang-cli invoice get_income_invoice_data_list --status='待确认'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当 code=200 时返回       |

data 参数说明

| 参数   | 类型     | 说明               |
|:-----|:-------|:-----------------|
| uid  | string | 当前查询所属的 `uid`     |
| current | int | 当前页码 |
| page_size | int | 每页数量（以服务端返回为准） |
| total | int | 符合条件的总发票数 |
| invoice_list | list | 发票列表            |

invoice_list 元素参数说明（以服务端返回为准）

| 参数   | 类型     | 说明                                            |
|:-----|:-------|:----------------------------------------------|
| id | string | 发票 id |
| invoice_number | string | 发票号码 |
| create_invoice_time | string | 开票日期（yyyy-mm-dd） |
| total_tax_price | string | 价税合计（单位：“元”） |
| total_money | string | 不含税金额（单位：“元”） |
| total_rate | string | 税额（单位：“元”） |
| title | string | 发票抬头 |
| buyer_name | string | 购买方名称 |
| buyer_taxpayer_number | string | 购买方纳税人识别号 |
| seller_name | string | 销售方名称 |
| seller_taxpayer_number | string | 销售方纳税人识别号 |
| status | int | 状态（审核中/待确认/已拒绝/已入账） |
| goods_name | string | 货物名称/服务名称（例：*建筑服务*安装服务费） |
| book_time | string | 入账月份（yyyy-mm）|
