# 基础资料、合同扩展筛选及部门切换

## 歌曲基础资料 batchQueryTrackBasicInfo

保留原筛选和3天有效的audioUrl/lyricUrl，新增返回中央 `tmeTrackId`，SaaS `trackId` 含义不变。用于费用或宣推的中央ID必须取真实tmeTrackId，不用SaaS ID替代。

`orderField` 与 `orderType=ASC/DESC` 同传。支持JS_PLAY_CNT、JS_PLAY_CNT_DIFF、SRCH_JS_PLAY_CNT、SRCH_JS_PLAY_CNT_DIFF、SETTLEMENT_PEAK_DAILY_PLAY_COUNT、SETTLEMENT_PEAK_DAILY_PLAY_DATE、HOT_INDEX、PLAY_INDEX、PAY_USER_PLAY_INDEX、PAY_DRIVE_INDEX，兼容YESTERDAY_HOT_INDEX；不排序时按发行时间倒序。显式排序缺失值末尾，同值按歌曲ID倒序。

范围字段：jsPlayCntMin/Max、srchJsPlayCntMin/Max为非负整数次数；hotIndexMin/Max、playIndexMin/Max、payUserPlayIndexMin/Max、payDriveIndexMin/Max为非负原始指数。可单边、含边界，多组按且组合，不按“万”传原始值。日指标取最近完整日快照，差值较前日，峰值取历史结算口径；筛选、排序在分页之前完成。仍不返回这些受限指标值，不通过反复试探阈值反推。

## 合同筛选

采买、宣推合同均支持signingTimeMin/Max、authorizationStartTimeMin/Max、authorizationEndTimeMin/Max，分别表示签约、授权开始、授权结束的13位毫秒时间戳。可单边且含边界，自然日转换为北京时间当天起止，不把开始/结束筛选自动解释成授权期重叠。

purchaseType支持SINGLE_PURCHASE、FRAMEWORK_AGREEMENT、历史SINGER_BUY或其返回的中文描述；不要自创宣推方式字段名。

采买合同：oneTimeFeeMin/Max、advancePaymentMin/Max为非负元字符串、最多两位小数；sharingRatioMin/Max为0～100百分比数值字符串，不带%且不再乘100。

宣推合同：totalFeeMin/Max、cooperationFeeMin/Max、serviceFeeMin/Max、taxFeeMin/Max、promotionAudioFeeMin/Max均为非负元字符串、最多两位小数。所有范围可单边、含边界，最小不大于最大，全部非空条件按且组合，在分页与总数统计前生效。未记录金额为空字符串，真实零为0.00；未记录签约时间为0，不把缺失当业务零值。

## 绩效部门

queryDepartmentPerformance、queryPersonPerformance、queryDepartmentPerformanceRanking、queryPersonPerformanceRanking使用departmentId。省略时沿用当前切换部门；指定部门只缩小已有绩效权限范围，不扩大数据权限。指定人员查询要求人员直接属于该部门，不自动包含子部门。收支类仍使用depId，不能跨工具照搬字段。

## 类型展示口径

歌曲版权授权形式使用重点、普通及当前实际返回的首发、无版权等类别；筛选编码以工具 Schema 为准。采买/宣推合同的资产类型中，历史代理细分类在用户展示时归为代理，自有和永久代理保留其本来含义。仅规范结构化类型标签，不修改合同名称、歌曲名称、原始文件或合法筛选值；不能据此声称原始接口响应已被全局替换。
