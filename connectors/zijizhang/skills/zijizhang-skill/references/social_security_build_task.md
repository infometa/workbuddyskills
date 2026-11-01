## 创建社保申报任务

```shell
zijizhang-cli social_security social_security_build_task <year> <month> --sb_type='<sb_type>' --uid='<uid>'
```

### 参数说明

| 参数    | 类型   | 必填 | 说明 |
|:-------|:------|:---|:---|
| year   | int   | ✅  | 年份，如 2026 |
| month  | int   | ✅  | 月份(1-12)，如 3 |
| sb_type| string| ❌  | 社保类型：`normal` 或 `last_month`（默认 `normal`） |
| uid    | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 使用示例

```shell
zijizhang-cli social_security social_security_build_task 2026 3

zijizhang-cli social_security social_security_build_task 2026 3 --sb_type=normal
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据（以服务端返回为准） |
