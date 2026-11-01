## 获取员工列表

```shell
zijizhang-cli employee get_employee_list --uid='<uid>' --keyword='<keyword>'
```

### 参数说明

| 参数      | 类型     | 必填 | 说明                                                                                            |
|:--------|:-------|:---|:----------------------------------------------------------------------------------------------|
| uid     | string | ❌  | 公司唯一标识，可以不指定，如果不指定会用默认使用终端激活在用的`uid`，参见 `zijizhang-cli account get_cpy_list` 状态为 `true` 的公司 |
| keyword | string | ❌  | 搜索关键字，姓名或者证件号码都可以，支持模糊查找                                                                      |

### 使用示例

#### 获取当前公司所有员工列表

```shell
zijizhang-cli employee get_employee_list
```

#### 获取账号下 uid=xxxx 的员工列表

```shell
zijizhang-cli employee get_employee_list --uid='xxxx'
```

#### 获取姓名为 夏天 的员工列表

```shell
zijizhang-cli employee get_employee_list --keyword='夏天'
```

#### 获取账号下 uid=xxxx 且姓名为 夏天 的员工列表

```shell
zijizhang-cli employee get_employee_list --uid='xxxx' --keyword='夏天'
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | list   | 当前账号下的公司列表，当code=200时返回 |

data 参数说明

| 参数   | 类型     | 说明                                |
|:-----|:-------|:----------------------------------|
| uid  | string | 当前查询所属的`uid`                      |
| ryxx | list   | 员工列表                              |

ryxx 参数说明

| 参数   | 类型     | 说明                                            |
|:-----|:-------|:----------------------------------------------|
| id   | string | 员工唯一标识                                        |
| xm   | string | 姓名                                            |
| zjlx | int    | 证件类型，`1` 代表居民身份证                              |
| zjhm | string | 证件号码                                          |
| xb   | int    | 性别，`1`: 男，`2`: 女，`0`: 未知                      |
| rzlx | int    | 任职受雇从业类型，`1`: 雇员 `2`: 劳务兼职 `3`: 实习学生（全日制学历教育） |
| sjhm | string | 手机号码                                          |
| rzrq | string | 入职日期，格式 `yyyy-mm-dd`，如 2020-02-03             |
| jbgz | float  | 基本工资（元）                                       |
| csrq | string | 出生日期，格式 `yyyy-mm-dd`，如 2020-02-03             |
| gjdq | int    | 国家地区，`1` 代表中国                                 |

### 返回例子

#### 获取成功

```json
{
    "code": 200,
    "msg": "",
    "data": {
        "uid": "123451c07f47435e12a34111",
        "ryxx": [
            {
                "id": "123451cf6277f5fc0c5addaa",
                "xm": "夏天",
                "zjlx": 1,
                "zjhm": "440000200202111111",
                "xb": 1,
                "rzlx": 1,
                "sjhm": "18888888888",
                "rzrq": "2023-04-17",
                "jbgz": 0,
                "csrq": "2002-02-11",
                "gjdq": 1
            }
        ]
    }
}
```

#### 关键字搜索，没有相关结果的情况

```json
{
    "code": 200,
    "msg": "共搜索出0名符合要求的员工",
    "data": {
        "uid": "123451c07f47435e12a34111",
        "cnt": 0,
        "ryxx": []
    }
}
```