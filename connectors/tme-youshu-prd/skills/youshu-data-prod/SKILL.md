---
name: youshu-data-prod
display_name: 音为有数 生产环境 数据查询
display_name_en: 音为有数 Data Query
description: Use the Production (PROD) environment to answer authorized music catalog, contract, finance, performance, singer, catalog-event and song play-source questions through the youshu MCP tools.
description_zh: 生产环境：通过 youshu 查询有权限访问的歌曲、合同、收支、业绩、歌手指标和曲库事件。
description_en: Query authorized music catalog, contract, finance, performance, singer, and catalog-event data with youshu.
version: 1.3.10
author: youshu
---

# 音为有数数据查询

当用户询问歌曲、合同、收支、付款流水、部门与人员业绩、运营指标、曲库事件，或希望跟进宣推、办理费用资料时，使用音为有数。先按意图选择下面一条路径，不要求用户先选择“专家”：

| 用户目的 | 处理路径 |
| --- | --- |
| 查询、比较和分析授权业务数据 | 本技能及 @references/tool-routing.md、@references/query-playbook.md |
| 为歌曲创建宣推计划或轮次、追加抖音资源、查看跟进结果 | 同包 `youshu-promotion-followup-prod` |
| 查询开户银行、支行 | 同包 `youshu-expense-application-prod` 的银行查询规则；`queryFeeBanks` 两级均必填keyword，先level=1查银行，再按需携带已选bankName以level=2查支行；无需先确定费用类型或准备申请资料 |
| 申请费用、导入合同或整理费用资料 | 同包 `youshu-expense-application-prod`；先明确费用类型 |

本技能仅使用 生产环境 对应连接器。沿用已确认的歌曲和业务上下文，但切换环境、歌曲、轮次或从查询转为写入时重新核对目标；不把其他环境的 ID、文件引用或授权带入本环境。按需加载相应参考，不要求加载全部专家。源码包含20项查询、14项宣推跟进、2项上传及合同导入、9项费用候选与草稿入口（含公共银行字典）；具体可用能力以当前连接器工具列表、实时 Schema 和业务权限为准，不自行拼接 OpenAPI 路径。文档中的方法名用于识别工具；实际名称带前缀时使用运行时名称。

平铺 JSON 示例见 @references/schema-examples.md。

## WorkBuddy 调用方式

直接调用 MCP 当前列出的工具；参考 Agent 的 `skill_load`、`search_apis`、`invoke_api`、`ui_renderer` 和 COS 卡片流程不属于本连接器调用步骤。参数是平铺 JSON 对象，不包在 `request` 或 `req` 下。只传业务参数，账号、租户、权限、thread/run、trace 字段由接入平台处理，用户或模型不得填写。

上述调用约定不限制 WorkBuddy 宿主的原生交互式提问能力。费用申请需要补充资料或选择候选时，交接费用专家并遵循其[弹窗优先规则](../youshu-expense-application-prod/SKILL.md#提问与候选选择弹窗优先)，使用当前实际可用的 `AskUserQuestion` 等原生工具；不把原 Agent 的 `ui_renderer` 当作弹窗前置条件。

使用实际运行时间按北京时间解析相对时间，不照抄示例月份。“我部门”通常省略部门ID，无需先查部门树；用户点名其他部门时才解析部门；月度收支传 `depId`，绩效传 `departmentId`。只给人员姓名时先查 `conditionList(statDimension=PERSON)`，使用唯一匹配项的 `conditionId`。

工具 Schema 的分页上限是服务端能力；日常明细从 `pageSize=10` 开始。完整查询最多取 1000 条，超过时说明限制并请用户缩小范围，不把部分结果作为完整统计或全量导出。服务端歌曲月收支 Top N 可使用 `limit=N`（最多 1000），不可把它改成客户端先取 10 行再排序。服务端非分页业绩排行保留原始名次。公共银行字典 `queryFeeBanks` 按非空白keyword分级查询，无分页或数量参数，不能传空对象或查全量。level=1查银行；选定完整bankName后才按需以level=2及支行keyword查询；展示实际匹配项。

## 每次查询的步骤

1. **确定业务对象和粒度。** 先分清歌曲基础资料、歌曲月度收支、部门月度收支、付款流水、合同、业绩、歌手运营指标或曲库事件。尤其分清“部门自身业绩”和“下级部门排行”，“歌曲采买合同号”和“完整合同”，“歌手运营”和“歌曲运营”。
2. **补齐必要条件。** 从用户话语提取名称或 ID、时间范围、部门、歌曲范围、排序和结果数量。仅在缺少的条件会改变业务含义或工具要求必填时询问；能由明确的“上月”“最近七天”等表达确定时直接换算。姓名不能当作人员 ID，必要时先查 `conditionList`；部门不明确但需要指定部门ID 时可用 `getDepartmentInfoTree`。
3. **按 Schema 构造最小请求。** 使用工具实际暴露的字段名、枚举和类型。不要同时传互斥条件；传排序方向时必须同时传排序字段；月度收支只传排序字段时方向默认 DESC。无需填与问题无关的条件。一次查询只选足够回答问题的工具，确需跨工具补充时分别说明各工具的业务口径。
4. **核对响应，再作答。** 检查结果是否分页、是否截断、是否含预估或不可见指标，保留服务端排序和排名。说明实际查询范围、时间、单位和结果条数；只有完整取回后才称“全部”或基于全量计算统计。空结果、无权限、接口失败和超时要分别表述。

## 可直接复用的常见问题

- “查询部门业绩排行”：当前部门，`songRange=ALL`、`aiSongType=ALL`、`viewLevel=ALL_CHILD_DEP`，调用部门排行。
- “查询人员业绩排行”：同样三个分类参数，调用人员排行；包含当前部门自身人员。
- “近7天支出记录”：用付款时间预设，查询总数及最近 20 条（两页、每页 10），明确仅展示最近 20 条。
- “近7天认领入库／被认领／下架”：使用各自固定状态工具及事件时间预设，三种业务方向不可互换。
- “本月支出最多100首歌曲”：当前部门、本月，`sortField=AMOUNT`、`sortDirection=DESC`、`limit=100`；单月行数与歌曲数对应。
- “查询我的部门收入”未给时间时，只问需要查询哪个月份或范围。参考 Agent 的默认月份由专用预设计划决定，本连接包未取得该计划，不猜测时间。

歌曲运营使用 `pageQuerySongOperationDataForMcp`：可按指标区间和服务端排序选歌，返回歌曲 ID 与 QQ 音乐、酷狗音乐每日播放来源。结算量、指数和峰值只用于筛选/排序，不返回其数值或趋势；详见 @references/song-operation.md。不要照搬原 Agent 预设中要求这些受限输出字段的步骤。

## 常见选择

| 用户表达 | 选用工具 | 关键理由 |
| --- | --- | --- |
| “查这首歌的发行信息、作者、供应商” | `batchQueryTrackBasicInfo` | 查录音库歌曲资料，不是收入或运营数据。 |
| “这首歌有哪些采买合同号” | `pageQueryTrackPurchaseContractInfo` | 返回歌曲关联的词、曲、表演者、录音录像合同号。 |
| “看采买合同授权、预付款、分成” | `pageQueryPurchaseContractInfo` | 返回完整采买合同与作品清单。 |
| “看宣推合同费用” | `pageQueryPromotionContractInfo` | 仅为合同费用，不能解释为歌曲宣推实际成本。 |
| “上月我部门收入/支出” | `queryDepartmentIncome` / `queryDepartmentExpense` | 单部门逐月汇总。 |
| “本月支出最多的 100 首歌” | `querySongExpense` | 按歌曲-月份行在服务端排序后截取。 |
| “最近七天付款流水” | `pageQueryExpenseFlow` | 付款记录，按付款时间倒序。 |
| “张三的业绩” | `conditionList` → `queryPersonPerformance` | 先把姓名解析为绩效人员 ID。 |
| “下级部门谁排名靠前” | `queryDepartmentPerformanceRanking` | 下级部门排行不包含查询部门自身。 |
| “歌手近七天的运营指标” | `pageQuerySingerOperationData` | 歌手级周期指标，非歌曲逐日运营。 |
| “最近认领入库/被别人认领/已下架的歌” | 对应的三个曲库事件工具 | 事件状态由专用工具固定。 |

## 参数和结果口径

- **ID：** `batchQueryTrackBasicInfo.trackId` 是 SaaS 曲库歌曲 ID；歌曲采买合同查询的 `trackId`、歌曲月度收支中的 `songId` 是中央曲库歌曲 ID；歌手运营的 `singerId` 是中央曲库歌手 ID。不能只因数字相同就跨 ID 体系套用。外部平台歌曲 ID 要按工具 Schema 提供平台类型及 ID 列表。
- **主体：** 歌曲基础资料的 `issuingSubject` 是发行主体，`displayBrandName` 是厂牌，不能当成用户本次费用申请的付款主体。为费用申请查询歌曲或交接费用专家时，保留用户已指定的付款主体及适用行/歌曲；只补充歌曲资料，已指定付款主体的名称/ID 由费用专家通过 `queryFeePaymentSubjects` 核实，不能被歌曲查询结果覆盖。宣推对私未指定主体时，费用专家可省略 `ourSubjectId` 交后端按发行厂牌关联的我方公司主体补全，失败后再补选；数据专家不猜测或自行映射主体 ID。
- **展示口径：** 歌曲版权授权形式使用“重点 / 普通”等当前业务名称，首发、无版权等其他真实类型照实保留，不强行压成两类；沿用实时 Schema 中的编码。采买和宣推合同的 `assetType` 中，自有、代理、永久代理按各自口径展示，其余历史代理细分类对外归为“代理”。只规范类型标签，不全文替换合同名、歌曲名或合同正文，不改业务 ID、筛选编码和上传文件。未知类型先说明待核实，不猜分类。
- **时间：** 部门/歌曲月度收支的 `startMonth`、`endMonth` 为 `yyyy-MM`，查询单月时两者相同。歌曲资料的发行、上线、创建日期筛选为 `yyyy-MM-dd`。付款流水和曲库事件的明确日期范围使用成对的 13 位毫秒时间戳，按北京时间理解自然日；“近七天”优先使用各工具的 `RECENT_7_NATURAL_DAYS` 预设，勿同时传起止时间。
- **分页与截断：** 分页接口从 `pageNo=1` 开始，按 Schema 的 `pageSize` 上限请求。歌曲月度收支的 `limit` 限制**歌曲-月份行**，不是去重后的歌曲数。分页总数以 `totalCount` 为准；只读取部分页时不得宣称总结果已全部展示。
- **金额与指标：** 合同、收支和流水金额按返回契约以元解释，不把空字符串当零。月度收入/支出可能包含预估值；应提示估算口径。业绩付费份额为空字符串表示不可见，不是 0%；歌手结算指标还要看可见性标记，标记为 `false` 时默认数值 0 不代表真实业务值。
- **统计范围：** 部门/人员业绩工具返回固定的年度、最近完整月、昨日、本月累计或近 30 天指标，不接收任意自定义日期。歌手 `YESTERDAY` 是单日值，其余周期是对应周期日均值；返回的 `date` 是数据更新日期，不是统计周期起止日。

## 能力边界与回答

- **完整歌曲运营指标**和旧版 `batchQueryTrackPromoteInfo` 未注册。当前可用的歌曲播放来源、宣推计划及资源查询各有独立契约，不能承诺返回旧接口的所有效果字段或推广成本排行。不能把宣推合同、歌手指标或播放来源加总冒充受限的歌曲结算量、指数、峰值，也不通过多个阈值试探反推具体数值。
- 工具只返回当前可访问范围内的数据。若请求对象不在结果中，不据此断言全局不存在；如有 `totalCount`，区分“本页无数据”和“整个查询为空”。
- 默认用简洁文字或表格给出结论、关键数值、筛选条件和必要限制。不要暴露内部工具调用、认证字段或错误堆栈。用户明确要求文件时，仅能基于已取得、获授权且完整的数据使用 WorkBuddy 的文件能力；未生成文件时不要宣称已导出。

## 新增流程的衔接

- 用户查询后说“把这些链接加到这首歌”，将已确认的歌曲候选交给宣推专家，再确认计划与轮次；查询成功不代表用户已确认写入。
- 用户说“申请这笔推广费用”，转费用专家，区分有合同对公、无合同对私和备用金；宣推资源入库不产生费用单。
- 歌曲基本资料可返回 `audioUrl`、`lyricUrl`、`coverUrl`；音频和歌词有效期3天，空值表示没有对应文件，过期时重新查询。按昨日热度排序使用 `orderField=YESTERDAY_HOT_INDEX`、`orderType=DESC`；当前基础资料也支持运营快照指标排序和六组范围筛选，使用其独立字段；详见 @references/extended-filters.md。
- 合同查询已支持签约/授权时间、采买方式及金额区间筛选，必须使用对应工具的字段；详见 @references/extended-filters.md。
- 绩效工具切换部门使用 `departmentId`，不是月度收支工具的 `depId`。指定部门只在已有权限范围内筛选，个人业绩要求该人员直接属于指定部门；无权限不换身份或扩大范围。
