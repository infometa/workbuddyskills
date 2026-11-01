## 获取代办列表（我的代办/本月进度）

```shell
zijizhang-cli todo get_todo_list --uid='<uid>'
```

### 参数说明

| 参数  | 类型     | 必填 | 说明                                                                                            |
|:----|:-------|:---|:----------------------------------------------------------------------------------------------|
| uid | string | ❌  | 公司唯一标识，可以不指定；不指定时使用当前已切换在用的 `uid`，参见 `zijizhang-cli account get_cpy_list` 中 `active=true` |

### 使用示例

```shell
zijizhang-cli todo get_todo_list
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | dict   | 数据，当 code=200 时返回       |

data 参数说明

| 参数        | 类型   | 说明     |
|:----------|:------|:--------|
| uid  | string | 当前设置所属的 `uid` |
| todo_list | list  | 代办项列表 |
| year | string | 当前记账期的年 |
| month | string | 当前记账期的月 |

todo_list 元素参数说明（以服务端返回为准）

| 参数      | 类型     | 说明 |
|:--------|:--------|:---|
| code    | string  | 代办编码（例：EMPLOYEE/PAYROLL/BANK/SALES/INCOME 等） |
| name    | string  | 代办名称 |
| desc    | string  | 描述 |
| state   | int     | 完成状态（1 已完成 / 0 未完成） |
| blocking| int     | 是否阻塞（0 不阻塞 / 1 阻塞） |
| tips    | string  | 提示（依赖项等） |
