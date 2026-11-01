## 获取某个月份个税明细数据

```shell
zijizhang-cli tax gs_month_mx <year> <month> --uid='<uid>'
```

### 参数说明

| 参数   | 类型   | 必填 | 说明 |
|:------|:------|:---|:---|
| year  | int   | ✅  | 年份，如 2026 |
| month | int   | ✅  | 月份(1-12)，如 3 |
| uid   | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 使用示例

```shell
zijizhang-cli tax gs_month_mx 2026 3

zijizhang-cli tax gs_month_mx 2026 3 --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据详见下表 |

**data 字段说明**

| 参数              | 类型  | 说明 |
|:----------------|:-----|:---|
| uid   | string | 公司唯一标识uid |
| zhuanzhi        | list | 专职（正常工资薪金）人员明细列表 |
| laowu           | list | 劳务（一般劳务报酬所得/其他连续劳务报酬）人员明细列表 |
| quanNianJiangJin| list | 全年一次性奖金人员明细列表 |

**zhuanzhi 列表字段**

| 参数       | 类型   | 说明 |
|:---------|:------|:---|
| month    | int    | 月份 |
| name     | string | 姓名 |
| gsse     | string | 个税税额（元） |
| byyfgz   | string | 本月应发工资（元） |
| mymsed   | string | 每月免税额度（元） |
| bngz     | string | 本年工资（元） |
| bnmsed   | string | 本年免税额度（元） |
| bnzxkc   | string | 本年专项扣除（元） |
| bnzxfjkc | string | 本年专项附加扣除（元） |
| bnxjsgz  | string | 本年需缴税工资（元） |
| sysl     | string | 适用税率，如 `3%` |
| sskcs    | string | 速算扣除数（元） |
| bnyjgs   | string | 本年已缴个税（元） |

**laowu 列表字段**

| 参数       | 类型   | 说明 |
|:---------|:------|:---|
| month    | int    | 月份 |
| name     | string | 姓名 |
| gsse     | string | 个税税额（元） |
| bqlwbc   | string | 本期劳务报酬（元） |
| bqmsed   | string | 本期免税额度（元） |
| bqxjnsgz | string | 本期需缴税工资（元） |
| sysl     | string | 适用税率，如 `20%` |
| sskcs    | string | 速算扣除数（元） |

**quanNianJiangJin 列表字段**

| 参数    | 类型   | 说明 |
|:------|:------|:---|
| month | int    | 月份 |
| name  | string | 姓名 |
| qnjj  | string | 全年奖金（元） |
| gsse  | string | 个税税额（元） |
| sysl  | string | 适用税率 |
| sskcs | string | 速算扣除数（元） |
