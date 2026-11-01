## 进项发票：选择用途并入账

```shell
zijizhang-cli invoice invoice_choose_use --uid='<uid>' --invoice_id='<invoice_id>' --category='<category>' --is_pay='<is_pay>' --payee='<payee>'
```

### 参数说明

| 参数       | 类型     | 必填 | 说明                                                                                            |
|:---------|:-------|:---|:----------------------------------------------------------------------------------------------|
| uid      | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |
| invoice_id | string    | ✅  | 发票 id |
| category | string | ✅  | 选择的用途/类目（建议从 `invoice_can_choose_use_list.data.items[].id` 里选） |
| is_pay   | string | ✅  | 支付方式（必须为：对公银行支付/员工垫付/老板垫付/现金支付 之一） |
| payee    | string | ❌  | 垫付人/收款人（`is_pay=员工垫付/老板垫付` 时必填；若老板垫付，可直接用 `invoice_can_choose_use_list.data.boss_name`） |

### 使用示例

```shell
zijizhang-cli invoice invoice_choose_use --invoice_id='123456' --category='1216' --is_pay='员工垫付' --payee='张三'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据（可能为空对象）              |

data 参数说明

| 参数   | 类型     | 说明                                |
|:-----|:-------|:----------------------------------|
| uid  | string | 当前查询所属的`uid`                      |

#### 设置成功

```json
{
    "code": 200,
    "msg": "入账成功",
    "data": {
        "uid": "123451c07f47435e12a34111",
    }
}
```

#### 设置失败

```json
{
    "code": 500,
    "msg": "该月份的发票已经不能录入｜匹配不到规则｜该发票已入账了|...",
    "data": {}
}
```
