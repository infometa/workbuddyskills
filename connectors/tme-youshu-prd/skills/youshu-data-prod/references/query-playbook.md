# 常见问题调用示例

这些示例帮助选择工具和填写业务参数。实际调用时以 WorkBuddy 当前工具 Schema 为准，月份与日期要根据用户提问换算，不要照抄示例文字。只传提问所需的字段。

## 曲库与合同

| 用户提问 | 调用与参数 | 回答时注意 |
| --- | --- | --- |
| “查《某歌曲》的发行信息和词曲作者” | `batchQueryTrackBasicInfo`，按 `trackName` 包含匹配；若用户给的是外部平台歌曲 ID，成组传 `platformType`、`platformIds`。 | 同名歌曲可能有多个版本，展示匹配项供用户辨认，不自行认定第一条就是目标。发行、上线、创建日期筛选使用 `yyyy-MM-dd`。 |
| “这首歌对应哪些采买合同号” | `pageQueryTrackPurchaseContractInfo`，已知中央曲库歌曲 ID 时传 `trackId`，否则用歌名、歌手等条件缩小范围。 | 返回的是词、曲、表演者、录音录像合同号；若要授权、预付款、分成等合同条款，再查 `pageQueryPurchaseContractInfo`。 |
| “找合同编号为 XXX 的采买合同” | `pageQueryPurchaseContractInfo`，传 `contractNo`。 | 合同编号为包含匹配，结果可能不止一份；保留作品清单和合同主体上下文。 |
| “这份宣推合同花了多少钱” | `pageQueryPromotionContractInfo`，按 `contractNo` 或 `contractName` 查。 | 报告合同总费用、合作费或服务费等对应字段；这些是合同金额，不是歌曲实际宣推成本或投放效果。 |

## 收支和付款流水

| 用户提问 | 调用与参数 | 回答时注意 |
| --- | --- | --- |
| “我部门上个月收入是多少” | `queryDepartmentIncome`，`startMonth` 与 `endMonth` 都设为上个月的 `yyyy-MM`；通常省略 `depId`。 | 结果按部门-月份列出正式、预估及合计金额；有预估时说明。此工具不是实时流水。 |
| “我部门今年各月支出” | `queryDepartmentExpense`，填当年首月到用户要求的末月；如果只问年度汇总，需要在完整的月度结果上求和并说明计算范围。 | 不把缺少的月份自动当作零。指定 `sortField` 后可选 `sortDirection`，省略时默认 DESC；只传方向则不合法。 |
| “本月支出最多的 100 首歌” | `querySongExpense`，`startMonth=endMonth=本月`，`sortField=AMOUNT`、`sortDirection=DESC`、`limit=100`。 | 返回按歌曲-月份行排序后的前 100 条；当前月数据可能尚不完整。 |
| “某首歌近三个月收入及环比” | `querySongIncome`，传 `songId` 或歌名，指定完整的起止月份；`monthOverMonthDiff` 是当前月减上月的金额差。 | `songId` 是中央曲库歌曲 ID；一个月一行，多个同名歌曲需区分。`limit` 若截断结果，不能据此声称覆盖全部月份或歌曲。 |
| “近七天有哪些付款流水” | `pageQueryExpenseFlow`，只传 `paymentTimeRangePreset=RECENT_7_NATURAL_DAYS` 和所需筛选、分页参数。 | 这是含当天的七个北京时间自然日。不要再传 `paymentStartTime`、`paymentEndTime`；需要完整清单时依 `totalCount` 翻页。 |
| “某日到某日的付款流水” | `pageQueryExpenseFlow`，将用户给出的北京时间日期转成成对的 `paymentStartTime`、`paymentEndTime` 毫秒时间戳。 | 不同时传时间预设；金额、收款户名、付款主体和合同名使用各自筛选字段。 |

## 业绩与组织

| 用户提问 | 调用与参数 | 回答时注意 |
| --- | --- | --- |
| “我的部门业绩怎样” | `queryDepartmentPerformance`，通常省略 `depId`；用户要求新歌或 AI 歌曲时分别设置 `songRange`、`aiSongType`。 | 这是部门自身的固定统计期指标，不是部门排行，也不支持任意自定义日期范围。 |
| “张三的业绩” | 先用 `conditionList` 且 `statDimension=PERSON` 查 `conditionId`；确认匹配人员后，以该 ID 调 `queryPersonPerformance` 的 `personId`。 | 若有同名人员，先请用户区分，不把姓名直接放进 `personId`。付费份额空字符串代表不可见。 |
| “下级部门的业绩排名” | `queryDepartmentPerformanceRanking`；只查直接下级用 `viewLevel=ONLY_CHILD_DEP`，全部后代用 `ALL_CHILD_DEP`。 | 不包含目标部门自身。返回的名次和顺序以服务端为准。 |
| “我部门人员业绩排名” | `queryPersonPerformanceRanking`；`viewLevel=ONLY_CHILD_DEP` 代表目标部门自身及直接下级范围。 | 与部门排行的包含范围不同；人员排行包含目标部门自身人员。不要重排或重新编号。 |
| “查某个部门 ID” | `getDepartmentInfoTree`。 | `selected=true` 是当前所在部门；`boolHasDepAuth` 表示该节点数据权限，二者不是同一含义。不要从树根或第一项猜当前部门。 |

## 歌手指标与曲库事件

| 用户提问 | 调用与参数 | 回答时注意 |
| --- | --- | --- |
| “某歌手近七天播放表现” | `pageQuerySingerOperationData`，传 `singerName` 或 `singerId`，`timeRange=LAST_7_DAY`。 | 近七天值是周期日均值；结算播放、搜播不可见时对应的默认 0 不能当真实值。`date` 是更新日期。 |
| “最近认领入库的歌曲” | `pageQueryClaimedInSongs`，`eventTimeRangePreset=RECENT_7_NATURAL_DAYS`。 | 事件状态固定为 `CLAIM`，不用传 `songStatus`；结果按认领时间倒序。 |
| “我们的歌最近被谁认领了” | `pageQueryClaimedByOthersSongs`，按需传事件时间、歌名或平台分组歌曲 ID。 | `claimBrandName` 是认领方，`claimedBrandName` 是被认领方；二者不可互换。 |
| “最近下架了哪些歌、原因是什么” | `pageQueryUnshelvedSongs`，`eventTimeRangePreset=RECENT_7_NATURAL_DAYS`。 | 固定查询当前已下架歌曲；下架原因缺失时保留空值，不推断原因。 |

## 需要先澄清的情况

- “歌曲表现”可能指收入、支出或歌手运营；若用户的指标或粒度未说明，先问一个能区分工具的问题。每日播放来源使用 MCP 专用歌曲运营工具；它不返回结算量、指数或峰值，不能以歌手数据替代。
- “这首歌”只给模糊名称且匹配到多个版本时，先用歌曲资料或关联结果列出候选，再请用户确认；不要跨工具把不同 ID 类型混用。
- “全部数据”“总金额”“排行”要确认工具是否已返回全量、是否有分页或 `limit` 截断。未取全时说明只覆盖当前页或当前上限。

## 从查询到跟进和费用

| 用户提问 | 处理方式 | 返回边界 |
| --- | --- | --- |
| “昨日搜播增长最高的10首歌” | `pageQuerySongOperationDataForMcp`，`metricSortField=SRCH_JS_PLAY_CNT_DIFF`、`metricSortDirection=DESC`、`pageSize=10`；日期按用户请求转换。 | 保留服务端排序，说明是最近完整日快照选歌；不显示搜播差值数值。 |
| “这些歌最近七天QQ/酷狗的播放来源” | 同一工具，中央歌曲ID用 `platformType=TME`、`platformIds`，日期成对填写、最多31天。 | 按返回日期和来源展示，不反推结算量；名称需另按正确ID体系查基础资料。 |
| “把表中的抖音链接加入这首歌的宣推跟进” | 宣推专家：确认歌曲 → 查计划/轮次 → 分类校验链接 → 确认提交 → 回查资源及入口。 | 不自动新建重复计划，不发费用单；无真实小程序码时给可用链接。 |
| “帮我申请这份合同的版权费用” | 费用专家：确认类型和PDF → 准备上传 → PUT成功 → 合同登记 → 返回归档入口。 | 电脑端核对、归档和费用申请仍由用户完成。 |
| “按达人表生成宣推对私申请” | 费用专家：识别为对私，转换并核对rows、金额及收款信息；用户已指定主体则查询核实并显式传入，未指定则省略ourSubjectId交后端补全，无法补全时再补选。使用符合幂等契约的requestId创建DRAFT。 | 仅回显必要脱敏资料；成功后用返回单号、状态和url引导用户手动提交，不把草稿当审批完成。 |

## 扩展筛选与费用办理

- “结算播放超过1万的歌曲，按搜播增长排前10”：基础资料用 `jsPlayCntMin=10000`、`orderField=SRCH_JS_PLAY_CNT_DIFF`、`orderType=DESC`、`pageNo=1`、`pageSize=10`；结果是基础资料，不包含指标数值。各组范围可同时填写并取交集。
- “签约于某月且预付款1万到5万的采买合同”：采买合同工具使用该月北京时间毫秒边界 `signingTimeMin/Max`、`advancePaymentMin="10000"`、`advancePaymentMax="50000"`，服务端筛选后分页。
- “指定部门的业绩”：解析授权部门后，绩效工具填写 `departmentId`；该字段不等于收支查询的depId，也不能扩大权限。
- 对私/备用金/制作费/报销使用费用专家内的4项创建工具；合同类费用仍导入PDF交接归档。所有费用最终提交、审批和付款均由用户在平台完成。
