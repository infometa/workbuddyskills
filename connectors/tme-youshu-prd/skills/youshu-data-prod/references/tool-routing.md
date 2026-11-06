# 工具选择与参数口径

本表依据 `CompanySaasAiAssistantMcpFacadeImpl` 当前启用的 `@OpenapiMcpTool`。调用时仍以 WorkBuddy 实际列出的工具及实时 Schema 为准。

| 用户要查 | 工具 | 关键区分 |
| --- | --- | --- |
| 歌曲基本资料、发行信息、歌手/作者、供应商 | `batchQueryTrackBasicInfo` | `trackId` 是 SaaS 曲库 ID；其他平台 ID 需成组给 `platformType`、`platformIds`。 |
| 采买合同主体、授权、费用、分成和作品清单 | `pageQueryPurchaseContractInfo` | 查询完整采买合同；合同名、编号、相对方可筛选。 |
| 宣推**合同**的主体、费用、作品清单 | `pageQueryPromotionContractInfo` | 只查合同，不是歌曲宣推状态或成本明细。 |
| 指定歌曲对应的词、曲、表演者、录音录像合同号 | `pageQueryTrackPurchaseContractInfo` | 返回歌曲与合同号，不返回完整合同条款。 |
| 单部门逐月收入 | `queryDepartmentIncome` | `startMonth`、`endMonth` 用 `yyyy-MM`；不传 `depId` 时按当前部门。 |
| 单部门逐月支出 | `queryDepartmentExpense` | 同上，输出是支出口径。 |
| 歌曲逐月收入、金额筛选或环比 | `querySongIncome` | `songId` 是中央曲库歌曲 ID；`limit` 限制歌曲与月份的结果行数。 |
| 歌曲逐月支出、金额筛选或环比 | `querySongExpense` | 同上，输出是支出口径。 |
| 支出付款流水、收款户名、付款主体、付款日期 | `pageQueryExpenseFlow` | 近七天用 `paymentTimeRangePreset=RECENT_7_NATURAL_DAYS`；明确日期用成对的毫秒时间戳，两种方式互斥。 |
| 一个部门自身的年度、上月、昨日业绩与近 30 天趋势 | `queryDepartmentPerformance` | 不是下级部门排行。 |
| 查绩效统计中的人员或部门 ID | `conditionList` | `statDimension` 取 `PERSON` 或 `DEPT`（不使用 TENANT；按实时 Schema 校验）；需要姓名转人员 ID 时先用它。 |
| 单个人员自身业绩 | `queryPersonPerformance` | `personId` 必须是正整数；只有姓名时先查 `conditionList`。 |
| 下级部门业绩排行 | `queryDepartmentPerformanceRanking` | `viewLevel` 可选直接下级或全部后代；不包含查询部门自身。 |
| 部门内人员业绩排行 | `queryPersonPerformanceRanking` | 排序与名次以返回为准；不要自行重排或重新编号。 |
| 当前可访问部门树、选择 `depId` | `getDepartmentInfoTree` | `selected` 标记当前部门，`boolHasDepAuth` 标记部门数据权限，含义不同。 |
| 歌手周期结算播放、搜播和指数 | `pageQuerySingerOperationData` | 歌手级运营数据；`timeRange` 可选昨日、近七日、近一月、近三月。 |
| 我方认领入库的歌曲 | `pageQueryClaimedInSongs` | 固定 `CLAIM` 状态，按认领时间倒序。 |
| 我方歌曲被其他主体认领 | `pageQueryClaimedByOthersSongs` | 固定 `CLAIMED` 状态，返回认领方和被认领方。 |
| 当前已下架歌曲 | `pageQueryUnshelvedSongs` | 固定 `UNSHELF` 状态，返回下架时间、原因和歌曲。 |

## 常见判断

- “这首歌的合同号”选 `pageQueryTrackPurchaseContractInfo`；“采买合同费用/授权”选 `pageQueryPurchaseContractInfo`；“宣推合同服务费/合作费”选 `pageQueryPromotionContractInfo`。
- “我部门业绩”选 `queryDepartmentPerformance`；“下级部门谁更好”选 `queryDepartmentPerformanceRanking`；“部门内哪些人员排名靠前”选 `queryPersonPerformanceRanking`。
- “最近认领入库”选 `pageQueryClaimedInSongs`；“被别的主体认领”选 `pageQueryClaimedByOthersSongs`。
- 若工具描述要求平台及 ID 成组、时间预设与明确时间互斥，缺一时不要发起会导致错误的调用。金额、份额、时间点和估算标记按返回契约解释。

## 新增查询与业务办理

| 用户要做 | 工具或技能 | 关键区分 |
| --- | --- | --- |
| 按结算量、搜播差值、指数或峰值筛选/排序选歌；查看每日来源 | `pageQuerySongOperationDataForMcp` | 仅返回 `tmeTrackId`、`qmPlaySources`、`kgPlaySources`；指标不是返回字段；见 @song-operation.md。 |
| 查询/新建宣推计划、轮次、追加抖音视频、BGM、话题 | `youshu-promotion-followup-prod` | 14项计划及资源入口，确认后写入，不承担付费投放和费用申请。 |
| PDF版权费/宣推对公合同导入，取得核对归档入口 | `youshu-expense-application-prod` | `prepareFileUpload` → 实际COS PUT → `importCopyrightContractFile`。 |
| 查询开户银行、支行 | `queryFeeBanks` / `youshu-expense-application-prod` | 两级keyword均必填；level=1查银行，选定完整bankName后以level=2和支行keyword查支行。公共字典仍需登录，不要求费用、连接器菜单或数据权限；不查全量，key不是支付字段。 |
| 宣推对私、备用金、无合同制作费、报销 | `youshu-expense-application-prod` | 已支持5项候选查询和4项草稿创建；银行资料按费用专家的分场景规则处理，宣推对私保留原文；按费用类型收集、校验、创建DRAFT，返回链接由用户手动提交。 |

歌曲基础资料支持音频/歌词、中央ID、运营快照范围及排序；合同日期/金额扩展筛选已开放，详见 @extended-filters.md。完整歌曲运营指标及旧版宣推效果列表仍未开放。绩效切换部门字段为departmentId，收支字段为depId。
