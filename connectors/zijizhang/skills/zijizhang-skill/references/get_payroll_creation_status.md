## 获取工资单创建状态

```shell
zijizhang-cli payroll get_payroll_creation_status '<month>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型     | 必填 | 说明                                                                                            |
|:------|:-------|:---|:----------------------------------------------------------------------------------------------|
| month | string | ✅  | 工资单月份，如 2026-04                                                                               |
| uid   | string | ❌  | 公司唯一标识，可以不指定，如果不指定会用默认使用终端激活在用的`uid`，参见 `zijizhang-cli account get_cpy_list` 状态为 `true` 的公司 |

### 使用示例

#### 获取当前公司 2026年4月 的创建状态

```shell
zijizhang-cli payroll get_payroll_creation_status 2026-04
```

#### 获取指定公司 2026年4月 的创建状态

```shell
zijizhang-cli payroll get_payroll_creation_status 2026-04 --uid='xxxx'
```

### 返回参数

| 参数   | 类型     | 说明                         |
|:-----|:-------|:---------------------------|
| code | int    | 状态码，`200` 表示可以创建工资单，其他代表失败 |
| msg  | string | 提示信息，失败时为不能创建的原因           |
| data | dict   | 数据字典，当code=200时返回          |

data 参数说明

| 参数              | 类型     | 说明                                          |
|:----------------|:-------|:--------------------------------------------|
| uid             | string | 当前查询所属的`uid`                                |
| year            | int    | 查询的年份                                       |
| month           | int    | 查询的月份                                       |
| already_exist   | bool   | 代表所查月份工资单是否存在                               |
| is_time_allowed | bool   | 所查月份的工资单是否支持创建，正常来说只能创建当期申报月份的工资单，一般为当期上一个月 |
| has_ryxx        | bool   | 是否已经存在员工记录，创建工资单的前提需要有员工信息                  |

### 返回例子

```json
{
    "code": 200,
    "msg": "",
    "data": {
        "already_exist": false,
        "is_time_allowed": true,
        "has_ryxx": true,
        "uid": "123451c07f47435e12a34111",
        "year": 2026,
        "month": 4
    }
}
```
