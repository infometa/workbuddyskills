## 获取当月社保申报概览信息

```shell
zijizhang-cli social_security social_security_now_month_report_info --uid='<uid>'
```

### 参数说明

| 参数  | 类型   | 必填 | 说明 |
|:-----|:------|:---|:---|
| uid  | string| ❌  | 公司唯一标识uid（不传则使用当前已切换在用的 uid） |

### 使用示例

```shell
zijizhang-cli social_security social_security_now_month_report_info

zijizhang-cli social_security social_security_now_month_report_info --uid='<uid>'
```

### 返回参数

| 参数   | 类型     | 说明 |
|:-----|:--------|:---|
| code | int     | 状态码，`200` 代表成功，其他代表失败 |
| msg  | string  | 提示信息，失败时为异常信息 |
| data | dict    | 当月社保申报概览信息（以服务端返回为准） |

data 参数说明（以服务端返回为准）

| 参数     | 类型   | 说明 |
|:--------|:------|:---|
| uid     | string | 当前查询所属的 uid |
| reporting_period | string | 所属期 |
| state | string  | 状态：（未查询社保数据｜预览社保数据并确认申报｜已申报未交款待确认｜申报成功｜需要添加社保参保人｜正在申报中/交款中｜停止申报｜需要修改参保人信息） |
