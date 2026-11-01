## 获取可切换的公司列表

```shell
zijizhang-cli account get_cpy_list
```

### 使用示例

```shell
zijizhang-cli account get_cpy_list
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | list   | 当前账号下的公司列表，当code=200时返回 |

data 参数说明

| 参数       | 类型     | 说明                    |
|:---------|:-------|:----------------------|
| uid      | string | 公司唯一标识                |
| cpy_name | string | 公司名称                  |
| tax_no   | string | 公司税号                  |
| active   | bool   | 状态，`true` 代表 当前终端激活在用 |
| pending_todo_cnt | int\|null | 未完成代办数量（通过 `todo get_todo_list` 统计；查询失败时为 null） |

### 返回例子

#### 成功，当已经登录的情况

```json
{
    "code": 200,
    "msg": "一共2个公司，当前正使用uid=123451c07f47435e12a34111",
    "data": [
        {
            "uid": "123451c07f47435e12a34111",
            "cpy_name": "珠海xx科技有限公司",
            "tax_no": "12345400AACEBAA111",
            "active": true,
            "pending_todo_cnt": 2
        },
        {
            "uid": "123459238f5dd2934f6cd111",
            "cpy_name": "清远xxx服装店",
            "tax_no": "",
            "active": false,
            "pending_todo_cnt": 0
        }
    ]
}
```

### 失败，当未登录的情况

```json
{
    "code": 400,
    "msg": "没有可切换的公司列表"
}
```
