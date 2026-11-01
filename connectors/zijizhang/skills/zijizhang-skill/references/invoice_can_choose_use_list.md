## 进项发票：查询可选用途列表

```shell
zijizhang-cli invoice invoice_can_choose_use_list --uid='<uid>' --goods_name='<goods_name>' --total_tax_price='<total_tax_price>' --total_money='<total_money>'
```

### 参数说明

| 参数            | 类型           | 必填 | 说明                                                                                            |
|:--------------|:-------------|:---|:----------------------------------------------------------------------------------------------|
| uid           | string       | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |
| invoice_id     | string        | ✅  | 发票id,可从 get_income_invoice_data_list.data.invoice_list[].id 中获取                           |

### 使用示例

```shell
zijizhang-cli invoice invoice_can_choose_use_list --invoice='1111111111111111111111'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当 code=200 时返回       |

data 参数说明（以服务端返回为准）

| 参数      | 类型   | 说明 |
|:--------|:------|:---|
| uid  | string | 当前查询所属的`uid`                      |
| items   | list  | 可选用途/类目列表（用于 `invoice_choose_use --category`） |
| is_pay  | list  | 支付方式候选（用于 `invoice_choose_use --is_pay`） |
| boss_name | string | 老板名称（当选择“老板垫付”时可直接作为 payee） |

items 参数说明

| 参数 | 类型 | 说明 |
|:--------|:------|:---|
| id | int | 用途id |
| category_name | string | 用途名称（用于 `invoice_choose_use --category`） |
| notice | string | 提醒 |
