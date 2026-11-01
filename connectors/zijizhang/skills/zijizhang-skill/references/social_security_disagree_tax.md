## 不同意社保税额/费率（驳回金额）

```shell
zijizhang-cli social_security social_security_disagree_tax <year> <month> --uid='<uid>'
```

### 参数说明

| 参数   | 类型   | 必填 | 说明 |
|:------|:------|:---|:---|
| year  | int   | ✅  | 年份，如 2026 |
| month | int   | ✅  | 月份(1-12)，如 3 |
| uid   | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 使用示例

```shell
zijizhang-cli social_security social_security_disagree_tax 2026 3
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据（以服务端返回为准） |
