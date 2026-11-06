# 歌曲运营与播放来源

使用 `pageQuerySongOperationDataForMcp`，不调用旧版 `pageQuerySongOperationData`。查询仅使用 生产环境 连接器及当前授权范围。

## 输入与统计口径

- `startDate`、`endDate` 必填，为13位毫秒时间戳，按北京时间自然日包含首尾、最多31天，仅限定每日播放来源。用户未给时间且不能从上下文确定时先补齐。
- 按 `tmeTrackId` 精确选歌，或 `songName`、`singerName` 包含匹配；批量中央歌曲ID使用成组的 `platformType=TME`、`platformIds`。不要将基础资料的 `trackName` 传给此工具。
- `metricRangeField` 配合 `metricMinValue`/`metricMaxValue`，上下界包含边界，一次只选一个指标；`metricSortField` 配合 `metricSortDirection=ASC/DESC`，方向默认DESC。服务端先筛选、排序再分页，`pageNo`从1开始，`pageSize`最大20。
- 指标枚举：`JS_PLAY_CNT`、`JS_PLAY_CNT_DIFF`、`SRCH_JS_PLAY_CNT`、`SRCH_JS_PLAY_CNT_DIFF`、`SETTLEMENT_PEAK_DAILY_PLAY_COUNT`、`SETTLEMENT_PEAK_DAILY_PLAY_DATE`、`OPERATION_PEAK_DAILY_PLAY_COUNT`、`OPERATION_PEAK_DAILY_PLAY_DATE`、`HOT_INDEX`、`PLAY_INDEX`、`PAY_USER_PLAY_INDEX`、`PAY_DRIVE_INDEX`。日期指标范围传毫秒时间戳。
- 结算量、差值和指数按最近完整日快照，峰值按历史累计值；改变趋势日期不会改变这些筛选/排序指标的统计期。用户要求历史某日排行或区间总量排行时，不能用此快照排行替代。
- 其他继承条件只按实时Schema及现有业务支持填写，不因Java父类存在某字段就承诺有效；具体字段不支持时说明限制。

## 输出与分析

分页项只含 `key`、中央歌曲ID `tmeTrackId`、`qmPlaySources`、`kgPlaySources`。来源数组按日期排列，`date`为北京时间零点毫秒时间戳；`sources`含平台、来源名称、播放量和占比，按实际字段与单位展示。

不返回歌曲名、歌手、结算量、指数、峰值或其趋势；需要歌名时以中央ID查 `batchQueryTrackBasicInfo(platformType=TME, platformIds=...)`，不把中央ID当基础资料的SaaS `trackId`。不可相加来源量、跨工具拼接或反复试探阈值来重建受限指标。

总数以分页 `totalCount` 为准，不能只取首页就称为全曲库。来源为空可能是缺少数据或下游降级，不解释成零播放；不要对缺失日期自行补0。仅依据真实返回且获授权的数据分析，导出能力与范围按当前平台及工具契约执行。
