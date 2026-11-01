## 获取某个月份个税申报概览信息

```shell
zijizhang-cli tax month_gs_report_info <year> <month> --uid='<uid>'
```

### 参数说明

| 参数   | 类型   | 必填 | 说明 |
|:------|:------|:---|:---|
| year  | int   | ✅  | 年份，如 2026 |
| month | int   | ✅  | 月份(1-12)，如 3 |
| uid   | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 使用示例

```shell
zijizhang-cli tax month_gs_report_info 2026 3

zijizhang-cli tax month_gs_report_info 2026 3 --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 数据详见下表 |

**data 字段说明**

| 参数               | 类型   | 说明 |
|:-----------------|:------|:---|
| uid              | string | 公司唯一标识uid |
| reporting_period | string | 申报期，格式 `YYYY-MM` |
| state            | string | 当前申报状态，取值见下表 |

**state 取值说明**

| state 值 | 说明 |
|:--------|:---|
| `待确认个税税额` | 需要确认个税税额，可调用 `agree_gs_tax_rate` 或 `disagree_gs_tax_rate` |
| `银行余额不足`  | 银行余额不足，无法缴款 |
| `线下缴款`    | 需要线下缴款 |
| `缴款中`     | 缴款任务处理中，等待结果 |
| `未知`      | 其他状态 |
