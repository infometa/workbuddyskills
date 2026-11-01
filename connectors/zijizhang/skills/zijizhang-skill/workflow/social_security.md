# SOCIAL_SECURITY（社保）工作流

目标：根据本期社保申报状态，决定是否预览并发起申报任务。

写操作保护：

- `social_security_build_task`、`social_security_agree_tax`、`social_security_disagree_tax` 都属于写操作，执行前必须先向用户确认
- 申报期 `year`、`month` 必须来自 `social_security_now_month_report_info` 返回的 `reporting_period`
- `sb_type` 必须来自 workflow 分支选择结果，不能自行猜测

补充说明：

- 若要查询历史社保申报记录，可用 `zijizhang-cli social_security social_security_history_list`
- `history_list` 不包含本期申报情况，本期需用 `now_month_report_info`

## Step 1：查看本期社保申报进度

```shell
zijizhang-cli social_security social_security_now_month_report_info --uid='<uid>'
```

期望结果：

- `code=200`
- 从 `data.reporting_period` 获取申报期（如 `YYYY-MM`），用于后续 `year`/`month` 参数
- 读取 `data.state` 判断下一步

## Step 2：根据 `state` 分支处理

当 `state=预览社保数据并确认申报` 时继续：

- 需要用户确认：按上个月申报 / 本月有新增社保成员 / 已自行申报过

当 `state=已申报未交款待确认` 时继续：

- 先 `zijizhang-cli social_security social_security_get_mx_data <year> <month> --uid='<uid>'` 查看申报概览
- 若用户同意该税额：先回显税额概览、申报期、`uid`，用户确认后再执行 `zijizhang-cli social_security social_security_agree_tax <year> <month> --uid='<uid>'` 发起缴款任务（需等待申报结果）
  - 若失败：直接展示报错信息并停止
- 若用户不同意：先回显税额概览、申报期、`uid`，用户确认后再执行 `zijizhang-cli social_security social_security_disagree_tax <year> <month> --uid='<uid>'`
  - 若成功：撤销申报任务，并回到 `zijizhang-cli social_security social_security_now_month_report_info --uid='<uid>'` 重新走申报流程
  - 若失败：直接展示报错信息并停止

### 分支 A：按上个月申报

1) 预览明细：

```shell
zijizhang-cli social_security social_security_get_mx_data <year> <month> --sb_type=last_month --uid='<uid>'
```

2) 确认预览无误后，发起申报任务：

先向用户回显：

- 申报期
- `sb_type=last_month`
- 明细预览摘要
- `uid`

只有用户明确确认后，才可执行：

```shell
zijizhang-cli social_security social_security_build_task <year> <month> --sb_type=last_month --uid='<uid>'
```

### 分支 B：本月有新增社保成员

1) 预览明细：

```shell
zijizhang-cli social_security social_security_get_mx_data <year> <month> --sb_type=normal --uid='<uid>'
```

2) 确认预览无误后，发起申报任务：

先向用户回显：

- 申报期
- `sb_type=normal`
- 明细预览摘要
- `uid`

只有用户明确确认后，才可执行：

```shell
zijizhang-cli social_security social_security_build_task <year> <month> --sb_type=normal --uid='<uid>'
```

### 分支 C：已自行申报过

- 不处理

## Step 3：其他状态

- 若 `state` 非“预览社保数据并确认申报”，不处理
