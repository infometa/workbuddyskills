## 标记某个月份无销项/开出的发票

```shell
zijizhang-cli invoice set_month_no_sales_invoice '<year>' '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                            |
|:------|:-------|:---|:----------------------------------------------------------------------------------------------|
| year  | int    | ✅  | 年份，如 2026                                                                                    |
| month | int    | ✅  | 月份(1-12)，如 3                                                                                  |
| uid   | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |

### 使用示例

#### 标记当前公司 2026 年 3 月无销项发票

```shell
zijizhang-cli invoice set_month_no_sales_invoice 2026 3
```

#### 标记 uid=xxxx 的 2026 年 3 月无销项发票

```shell
zijizhang-cli invoice set_month_no_sales_invoice 2026 3 --uid='xxxx'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 结果数据，当 code=200 时返回     |

data 参数说明

| 参数   | 类型     | 说明                                |
|:-----|:-------|:----------------------------------|
| uid  | string | 当前查询所属的`uid`                      |

### 返回例子

#### 设置成功

```json
{
    "code": 200,
    "msg": "设置成功",
    "data": {
        "uid": "123451c07f47435e12a34111",
    }
}
```

#### 设置失败

```json
{
    "code": 500,
    "msg": "该月份已经录入了发票｜该月份还没到可以设置无发票的时间",
    "data": {}
}
```