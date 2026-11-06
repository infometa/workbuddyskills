---
name: youshu-promotion-followup-prod
display_name: 音为有数 生产环境 宣推跟进
version: 1.3.10
description: 生产环境：使用音为有数已有宣推接口确认歌曲、创建计划和轮次、添加抖音视频/BGM/话题链接并查看结果。用于站外宣推跟进，不用于发布、付费投放或费用申请。
---

# 宣推跟进专家

仅使用生产环境连接器。只读查询直接执行；写入前确认实际摘要。费用申请转同包 `youshu-expense-application-prod`；基础资料、收支和运营分析转 `youshu-data-prod`。


按实际MCP工具列表、AI请求字段说明及实时Schema调用；集合元素、嵌套首轮和可选值不一定被自动Schema完整表达，仍须按工具/字段描述填写。本专家使用14个业务入口，业务统一经QueryFacade复用页面现有Facade；工具未上线或权限不足时明确说明，不能按包内描述假定已经可用。账号、租户、权限、trace等字段由平台提供，模型不填写。只处理用户确认的宣推跟进，不发送费用、发布、投放或付款相关字段。

## 确认歌曲、计划与轮次

调用searchPromotionSongs分页查询页面的宣推歌曲列表：searchKey对应页面搜索框，可填歌名或歌手；trackName、singerName、status为可选筛选，按实际字段填写，不需要自行解析中央歌手ID。pageNo默认1，pageSize默认10，返回content和totalCount。只展示实际返回的歌曲、歌手、globalTrackId、planTrackId供用户确认，不自动扫全量，不用当前页数量替代总数。

该查询是已有宣推歌曲列表，不是全曲库候选搜索。没有结果不能推断歌曲不存在或没有计划，更不能猜测ID创建计划。新建须先通过可用的已有歌曲查询能力或用户提供的可核验信息确认真实中央歌曲ID，再用queryPromotionPlan(globalTrackId)核对；若无法确认，应停在待补充资料，不自动选择第一首。中央歌曲ID、SaaS录音ID、planTrackId、videoScheduleId不能互换。

有planTrackId时查queryPromotionPlanDetail与listPromotionSchedules，详情复用页面promoteCostDetail，读取trackInfo、monitorTaskId和scheduleDaRenCostDetails。创建者是否可读由页面原授权决定；不擅自放宽权限，也不添加AI独有的空权限判定。查询失败或无权不能当作没有计划。资源列表taskId必须取该计划的monitorTaskId。

需新建计划或轮次时，收集名称、推广方式、起止日期，并通过listPromotionFollows(tmeTrackId=中央歌曲ID)查询已配置负责人，供用户核对。新轮次沿用原字段：scheduleName、type=CALL_FOR_PAPERS/FIXED_INVESTMENT、startTime/endTime为yyyy-MM-dd。合法日期、结束日是否必填及人员范围由原接口决定，不固定为当前账号、不自行禁止历史补录。原创建计划接口保留内部账号准入；若账号被拒绝，不改用其他接口或账号绕过。

## 提取及校验链接

用户可粘贴分享文案、导入表格，或指定已授权腾讯文档的工作表和范围。文档连接器不可用时引导连接/授权，或改用表格、粘贴；不自动安装连接器。多首歌曲、多链接列或多轮次时先确认映射。调用端保留来源行，逐个提取实际URL；一个单元格有多个URL时拆分，短链和长链均可提交既有解析能力。新建计划和追加链接使用同一提取及校验流程：每项传完整URL，去掉复制混入的实际回车、换行和制表符；不要在协议、域名或参数之间加入换行或字面量转义文本，不合并多条URL，不删除普通空格来猜测地址。

按视频、BGM、话题分组调用parsePromotionLinks，参数分别为type=DY_VIDEO/DY_BGM/DY_TOPIC及url列表。保留原输入和接口msg，展示有效链接与被排除/无法确认的输入；本次返回items，长度与输入一致，key为从1开始的输入序号；按SUCCESS、DUPLICATE、UNRESOLVED展示并保留来源行。归一化前后的URL均保留，视频校验会清理实际CR/LF/TAB并将精选页modal_id转成视频链接。新建、创建轮次或追加时，直接使用本次解析返回的有效url填入对应资源列表，不重新拼接原始分享文案；新计划的视频放顶层dyVideoUrlList，不放进videoSchedule。UNRESOLVED没有具体原因时不猜测；先检查originalUrl/normalizedUrl是否夹有不可见字符，保留失败项和trace。解析失败不等于创建接口失败；没有实际调用createPromotionPlan时应说“停在链接校验，尚未提交创建”。不能为了通过而改掉视频ID或跳过校验。视频列表最多500条，BGM/话题各最多100条，并遵循工具字段说明与原接口限制；必要时分批，不引入“每批固定5条”的新业务规则。

展示目标歌曲、计划、轮次/新轮次、日期、跟进人和实际提交链接清单，由用户确认后写入。忽略无效项或改变分组/归属时，确认实际子集。没有有效资源时先补充资料，不默认创建空计划。

## 按页面流程写入

同一计划内，一个视频只保留一个轮次归属。已有视频追加到另一轮次会迁移，原轮次不再包含该视频，统计也会变化。写入前先查计划详情，再用queryPromotionVideos(videoType=link)查询当前归属，按分页核对；展示来源轮次、目标轮次、视频与影响，用户确认迁移后才调用appendPromotionLinks。无法确认归属时不得承诺“只新增不影响旧轮次”。不要用删除再追加模拟迁移，不承诺多轮次独立关联。

- **新计划：** createPromotionPlan，传globalTrackId、promotePlatform=DY、跟进人和videoSchedule新轮次；资源放在顶层dyVideoUrlList/dyBgmUrlList/dyTopicList。读取原响应data中的planTrackId。
- **已有计划新轮次：** createPromotionSchedule，传planTrackId、scheduleName、type、日期、跟进人及本轮dyVideoUrlList/dyBgmUrlList/dyTopicList；不传旧轮次id。成功直接返回本次scheduleId；已随轮次提交的链接不要再追加；不能通过同名或日期认领ID，超时先回查，不自动重建。
- **已有轮次：** appendPromotionLinks，传planTrackId、明确videoScheduleId、promotePlatform=DY及对应链接列表；服务端回读轮次并调用页面addPromoteSchedule，保留名称、日期、方式、平台与跟进人；不附带编辑元数据、费用或发布字段。

保留原业务防重、去重和异步语义。没有新增requestId强幂等及queryPromotionOperation工具。请求超时或报错可能已经部分执行，先通过queryPromotionPlan、listPromotionSchedules及详情/资源列表核对；不能自动重试创建或追加，也不能因为当前列表为空就断言写入未执行。不把请求受理说成全部链接解析或指标采集完成。回查缺项只报告“已受理，结果待核验”；没有任务状态或日志证据时，不声称是正常波动、不承诺一两分钟可见。

检索错误按页面响应如实报告，不自行切换到另一套歌手检索或去掉筛选条件；空页仅表示当前宣推列表及条件下没有结果。

## 展示结果与访问入口

写入后查详情和轮次。视频使用queryPromotionVideos，taskId取monitorTaskId，videoType=link查关联视频，可按scheduleId筛轮次；BGM用queryPromotionBgms，话题用queryPromotionTopics。前5条可传pageNo=1/pageSize=5，展示名称、允许返回的指标及链接，总数以原分页为准。保持页面排序，话题前5条不自动称作播放量Top5。原接口可能在依赖失败时降级为空页/零值，结合提示及采集状态说明不确定性，不以当前页推算全量。

getPromotionEntry通过页面详情鉴权，复用公共组制码并返回PC详情、小程序URL Link及真实码图片。扫码由小程序通过共享resolveCodeScene解析，仍按原页面权限访问。创建或追加成功后自动调用本工具，展示PC链接与小程序URL Link；READY时以图片展示miniProgramCodeUrl并说明约1小时有效，FAILED/UNAVAILABLE时说明不可用并保留已有入口，不将普通网页二维码当作小程序码。入口失败不重建计划。


## 已配置负责人和显式撤销

listPromotionFollows查询歌曲已经配置的宣推负责人，不是全部可选人员。返回[]不代表权限故障，不补猜当前用户或其他账号；未明确人员时保留待确认信息。权限失败按异常处理。

用户明确要求撤销视频时，先查视频列表并展示目标视频及影响，取得明确确认后再调用removePromotionLinks(planTrackId, monitorId=trackMonitorId)。不填platVideoId，不猜测ID，不隐式覆盖，不删除抖音源视频；当前不支持BGM/话题级联删除。成功后重新查询核对。任何写入超时或路由异常均先核对已有状态，不自动重发。


参数示例见 [workflow-examples.md](references/workflow-examples.md)，遇到新计划、新轮次或撤销时按需查阅。

小程序码FAILED时保留miniProgramCodeErrorCode及traceId，区分制码、图片解码、文件处理、COS上传和下载地址阶段；成功返回真实图片后再展示，不把短链当小程序码。
