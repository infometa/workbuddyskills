## 获取社保申报历史记录列表

```shell
zijizhang-cli social_security social_security_history_list --uid='<uid>' --current='<current>'
```

### 参数说明

| 参数      | 类型  | 必填 | 说明 |
|:--------|:------|:---|:---|
| uid     | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |
| current | int   | ❌  | 页码，默认 1 |

### 使用示例

```shell
zijizhang-cli social_security social_security_history_list --current=1

zijizhang-cli social_security social_security_history_list --uid='<uid>' --current=2
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据 |

data 参数说明（以服务端返回为准）

| 参数     | 类型   | 说明 |
|:--------|:------|:---|
| uid     | string| 当前查询所属的 uid |
| current | int   | 当前页码 |
| history_list   | list  | 历史列表 |

items 元素参数说明

| 参数           | 类型     | 说明 |
|:--------------|:--------|:---|
| reporting_period | string  | 所属期 |
| state | string | 申报状态（如：已申报｜未申报｜未知） |
| total_user | int | 申报人数 |
| jnjsze | string | 缴纳基数总额 |
| yjzje | string | 应缴总额 |
