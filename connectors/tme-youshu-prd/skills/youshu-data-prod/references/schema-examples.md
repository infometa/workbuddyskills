# 平铺参数示例

工具名称以运行时列表为准。以下月份仅是格式示例，使用时根据用户请求换算。

## 部门单月收入

工具：queryDepartmentIncome
```json
{"startMonth":"2026-09","endMonth":"2026-09"}
```

## 指定平台的歌曲资料

工具：batchQueryTrackBasicInfo
```json
{"platformType":"TME","platformIds":[123456],"pageNo":1,"pageSize":10}
```

## 本月歌曲支出 Top100

工具：querySongExpense；以下月份需替换为实际本月。
```json
{"startMonth":"2026-10","endMonth":"2026-10","sortField":"AMOUNT","sortDirection":"DESC","limit":100}
```

## 近七天付款流水

工具：pageQueryExpenseFlow
```json
{"paymentTimeRangePreset":"RECENT_7_NATURAL_DAYS","pageNo":1,"pageSize":10}
```

## 按平台分组的认领事件

工具：pageQueryClaimedInSongs
```json
{"songIds":[{"platformType":"TME","platformIds":[123456]}],"eventTimeRangePreset":"RECENT_7_NATURAL_DAYS","pageNo":1,"pageSize":10}
```

## 姓名解析的第一步

工具：conditionList；该工具没有姓名筛选字段，需要在返回的授权人员列表中匹配。
```json
{"statDimension":"PERSON"}
```

只有唯一匹配时，才把 conditionId 填入 queryPersonPerformance.personId。

## 歌曲运营来源及快照筛选

工具：pageQuerySongOperationDataForMcp。示例为北京时间2026-10-20一天，使用时替换为用户实际日期；不以该日期重定义快照筛选期。
```json
{"startDate":1792425600000,"endDate":1792425600000,"metricRangeField":"JS_PLAY_CNT","metricMinValue":10000,"metricSortField":"SRCH_JS_PLAY_CNT_DIFF","metricSortDirection":"DESC","pageNo":1,"pageSize":10}
```

结果只展示歌曲ID和每日播放来源，不能展示筛选/排序指标的具体数值。
