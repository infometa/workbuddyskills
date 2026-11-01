## 获取某个月份社保明细数据

```shell
zijizhang-cli social_security social_security_get_mx_data <year> <month> --sb_type='<sb_type>' --uid='<uid>'
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
zijizhang-cli social_security social_security_get_mx_data 2026 3

zijizhang-cli social_security social_security_get_mx_data 2026 3 --sb_type=last_month
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据（以服务端返回为准） |

data 参数说明（以服务端返回为准）

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| uid     | string| 当前查询所属的 uid |
| reporting_period | string | 所属期，如 `2026-04` |
| state | string | 申报状态，如 `已申报`,`申报中-概览`,`未申报-预览` |
| members | list | 社保明细列表 |

members 元素参数说明

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| xm   | string  | 姓名 |
| zjlx | string  | 证件类型（如：居民身份证） |
| zjhm | string  | 证件号码 |
| wages | string | 工资（金额，单位以服务端为准） |
| dw   | list | 单位缴纳明细（字符串列表；展示文本，如：`基本养老保险：1,600.00`） |
| gr   | list | 个人缴纳明细（字符串列表；展示文本，如：`基本养老保险：800.00`） |

### 返回示例

```json
{
  "msg": "ok",
  "code": 200,
  "data": {
    "uid": "111111",
    "reporting_period": "2026-04",
    "state": "已申报",
    "members": [
      {
        "xm": "张三",
        "zjlx": "居民身份证",
        "zjhm": "11111111111111111",
        "wages": 10000,
        "dw": [
          "基本养老保险：1,600.00",
          "城镇工失业保险：80.00",
          "基本医疗保险（含生育）：600.00",
          "工伤保险：20.00"
        ],
        "gr": [
          "基本养老保险：800.00",
          "城镇工失业保险：20.00",
          "基本医疗保险（含生育）：150.00",
          "工伤保险：0.00"
        ]
      }
    ]
  }
}
```
