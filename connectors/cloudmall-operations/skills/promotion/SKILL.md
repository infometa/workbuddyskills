---
name: promotion
display_name: 云MALL促销
display_name_en: CloudMall Promotions
description: 以商品销售转化为主的促销活动（满减/满折/满赠/秒杀/预售/直降/口令购/拼团/周期购/N件Y元）的创建审核与状态管理，优惠券模板及发券/退券/延期/解锁/停用、平台券码批次、赠品库、日历主题、活动库存。满减/券模板/平台券码批次属本域；品牌方兑换码互动领奖、弹窗/CPS分销/导购属营销域；商品售价/实物库存属商品域，订单结算属交易域。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths; execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.5.15
author: 云MALL
---

# 云MALL促销域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。写操作的前置条件/幂等键/状态约束在对应契约锚点内，本表不重复。

## 业务目的定位（本域是什么）

本域通过优惠、折扣、限时和拼团等机制提高商品销售转化。营销域管理分销、导购、弹窗及互动领奖等场景。业务目的辅助判断，最终按明确的业务对象和操作选域；新客券、发券和赠品也可能属于本域，不凭“送/领/拉新”等单个词切域。

## 路由前先识别业务对象

以用户明确的对象和操作选域，名称与信号词只作线索：满减、券模板、券实例、平台生成券码批次属于本域；分销佣金、导购、弹窗、互动领奖属于营销域。“每单满减”“新人礼包券模板”不因“每单/新人礼包”切域。兑换码按下方消歧约定判断；对象仍不明确时再澄清。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **促销商品文件解析**（上传商品清单、解析/校验活动商品 Excel 或 CSV，含“先解析，不创建”） | activity-query.md → ops.promotion.import.parse 锚点 → 按运行时文件通道提交实际附件并调用解析。文件预览与逐项商品查询不能替代解析；成功/错误行以真实返回为准。解析不落库，用户仅要求解析或取消后，不继续创建/导入；需要提交时再进入写操作路径 |
| **简单查询**（查活动/查券/查模板/查批次/查赠品/查主题/查统计/查日志） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ 业务名 — capability-id` 锚点 → 直接调用查询执行器。具体对象先查数据再解释：券当前运行态查 coupon.detail / coupon.library；给定订单金额的局部预检用 coupon.check，并结合运行态；叠加类型规则查 stackable-rules，两个具体活动还需各自详情中的 stackableExclusions，不以类型规则代替实例配置 |
| **写操作**（创建/编辑/提审/审核/暂停/停用/删除/发券/退券/延期/作废/归组等） | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应场景文件（审核链=`promotion-review.md`；活动=`promotion-activity.md`；券体系=`promotion-coupon.md`；赠品/日历/库存=`promotion-support.md`）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值） | `references/domains/promotion-enums.md`（状态机/枚举字典）→ 契约文件锚点 |
| **概念咨询/异常排查**（规则怎么算/子类型差异/实体口径/互斥） | `references/domains/promotion-concepts.md`（实体/23 种子类型/四层互斥/规则结构/业务规则）→ 契约文件锚点 |
| **特殊活动结构**（周期购/拼团/预售/买赠的嵌套配置） | `references/apis/promotion/specialty.md`（随 `activity-action.md` 的 create / `pending-action.md` 的 update 使用） |
| **创建/复制/编辑/改期/提审的字段联动** | 必须读取 `references/apis/promotion/form-validation.md`，按当前模式检查整组日期、价格和范围；特殊活动同时读取 specialty，不能仅凭单字段参数表提交 |

## 能力路由表（唯一索引）

> 所有 capability 前缀为 `ops.promotion.`（下表省略前缀）；契约文件均在 `references/apis/promotion/` 下。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器 / mall.query）

| 契约文件 | capabilities |
|---|---|
| `activity-query.md` | activity.search 分页 · activity.detail 详情 · activity.goods-search 商品分页 · activity.goods-all 商品全量（编辑/复制基线） · activity.logs 日志 · activity.stats 统计 · stackable-rules 叠加互斥 · passcode.check 口令占用 · import.parse 商品 Excel 解析（纯解析无落库） |
| `pending-query.md` | pending.detail 草稿详情（含 version） · pending.check-logs 审核历史 |
| `coupon-template-query.md` | coupon-template.search · coupon-template.detail · coupon-template.stats · coupon-template.logs · coupon-template.share-capability 分享能力 |
| `coupon-runtime-query.md` | coupon.report 报表 · coupon.detail 详情 · coupon.library 会员券库 · coupon.check 核销预检 |
| `gift-pool-query.md` | gift-pool.search · gift-pool.sku-details · gift-pool.reference-count 引用数 |
| `calendar-query.md` | calendar.view 日历 · theme.detail 主题详情 · theme.eligible-targets · theme.eligible-activities |
| `stock-query.md` | stock.items 库存分页 |
| `overview.md` | home.summary 首页汇总 · groupon.stats · groupon.stats-batch 拼团统计 |
| `coupon-code-query.md` | coupon-code.batches · coupon-code.batch-detail · coupon-code.templates · coupon-code.batch-codes · coupon-code.codes-search · coupon-code.batch-codes-search |

### 写能力（Capability 写操作执行器 / mall.action）

| 契约文件 | capabilities |
|---|---|
| `activity-action.md` | activity.create 创建草稿 · activity.check 审核合一 · activity.pause · activity.resume · activity.stop 停用🔴 · activity.delete 删除🔴 |
| `pending-action.md` | pending.update 编辑 · pending.submit 提审 · pending.withdraw 撤回 · pending.approve 通过 · pending.reject 驳回🔴 · pending.delete 删草稿🔴 · pending.start-edit 变更重审 |
| `coupon-template-action.md` | coupon-template.create · coupon-template.update · coupon-template.submit · coupon-template.check · coupon-template.stop 停用🔴 · coupon-template.pause · coupon-template.resume · coupon-template.delete 删除🔴 · coupon-template.share-qrcode · coupon-template.share-short-link |
| `coupon-runtime-action.md`（资金面高危区） | coupon.send 发券🔴 · coupon.stop 停用🔴 · coupon.cancel 退券🔴 · coupon.delay 延期🔴 · coupon.unlock 解锁🔴 |
| `coupon-code-action.md` | coupon-code.batch-create 创建批次🔴 · coupon-code.batch-activate 生效🔴 · coupon-code.batch-void 批次作废🔴 · coupon-code.code-void 单码作废🔴 |
| `gift-pool-action.md` | gift-pool.batch-add 批量添加 · gift-pool.remove 移除🔴 · gift-pool.remove-by-spu🔴 |
| `calendar-action.md` | theme.create · theme.update · theme.workcopy · theme.delete · theme.assign-activity · theme.unassign-activity（乐观锁契约见锚点） |
| `stock-action.md` | stock.increase 增库存🔴 |
| `specialty.md` | 特殊活动配置结构参考（周期购/拼团/预售/买赠/extJson/operationValue），非独立能力 |
| `form-validation.md` | 创建/编辑/提审的时间、价格与范围联动参考，非独立能力 |

### 未开放（不调用，只整理需求）

| 模块 | 原因 |
|---|---|
| 促销工具启用/停用开关及创建权限查询 | 当前能力索引未提供对应读取能力；home.summary 只返回进行中活动数量，数量为0或大于0都不能证明工具开关或创建权限。无法核验时直接说明边界，不以活动统计代答 |
| 券数据看板（领取/使用/成本/成交）及CSV导出 | 当前catalog没有report/coupon看板端点；已开放coupon.report仅按模板统计券量与使用率，不能替代成交看板 |
| 券模板领用记录（claim-records）、券订单明细导出、兑换码制卡导出 | 端点要求额外端侧操作权限标识参与券种级鉴权（能力链不提供该入参 → 必然 400）；明文码属敏感资产，不经开放能力流转；待后端改造后评估 |
| 计算引擎索引/券投影重建、拼团事件重放/发件箱健康 | 运维面操作，不属运营开放能力 |
| 重复入口（pending/create、PUT /admin/promotion/{id}） | 与主入口同一实现（前者 bizType 参数无法经能力链传递），已按主入口开放 |
| 供应商/内部回调（Internal/OpenGateway） | 非平台运营面 |

## 通用约定（护栏）

| 项 | 约定 |
|----|------|
| **调用方式** | 只能调用能力路由表中列出的 capability：查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`。入参形态以**当前运行时的工具说明为准**（如 `capabilityId` 键名；写操作按运行时要求附审批理由）；`summary` 一句话说明意图。**不得猜测或编造未登记的 capability** |
| **入参字段名** | 以契约参数表为准，**大小写敏感**（如 `afterSaleNo` 不是 `aftersaleSn`）；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工） |
| **身份与授权** | 身份由连接授权绑定；查询需 `mall.query`、写操作需 `mall.action`，且受当前账号实时业务权限限制，权限拒绝时停止。不询问、不传入租户/账号/Token/服务名/路径/权限码；门店/会员/标签等业务参数必须来自用户或查询结果 |
| **ID 序列化** | 雪花 ID（promotionId/pendingId/templateId/couponId/batchId/themeId/giftPoolId/skuId 等）一律**十进制字符串**，严禁 Number。memberId 为字符串会员 ID |
| **⚠️ 金额单位** | 本域**金额单位分（整数）**：rules 金额门槛/金额优惠值、deductAmount、orderAmount、useCondition。折扣为千分比整数（850=8.5 折）。券实例 `amount` 沿用模板摘要：`couponType=2` 为折扣千分比（100=1折），不能除以100当元；金额券为分；兑换券/全免运费券不能凭该摘要推导兑换商品价格或实际优惠额。`coupon.check.discountAmount` 原样回传该摘要，仍不是实际结算金额。与商品域"元"的约定不同，禁止混用。**例外（元单位）**：①周期购 `periodBuyGoodsConfig.activityPrice`（元，两位小数，服务端转分）；②赠品池 productPrice 沿用商品域元单位——当前版本该字段不返回，若恢复则按元两位小数；③商品清单解析 `import.parse.successItems[].originalPrice`（元，沿用商品原价，展示时不再除以100） |
| **时间格式与时区** | startTime/endTime/preheatStartTime/领券时间窗/expireStart/expireEnd/operatedAt 为**毫秒时间戳**；useExpireDuration 为**秒**；createdTime/checkTime/activatedAt/voidedAt 为 `yyyy-MM-dd HH:mm:ss`。毫秒时间戳是绝对时刻，换算/展示优先用用户指定时区，其次用已确认的业务时区，并标注所用时区；不能依赖执行环境默认时区。需要转日期或计算时长时，使用确定性日期计算，显式指定时区，覆盖本次实际展示的每个值（相同值可去重批量计算）；展示的每个换算值须来自计算结果，不能仅算少数行后推填其余行。没有计算能力或个别值无法可靠换算时，已换算值照常展示，未换算值保留原始值并说明，不估算时分秒。无时区的服务端日期字符串原样展示，跨时区换算前先确认来源时区。两者都未确定时，查询仍可执行，原样展示时间值并说明尚未换算；按自然日构造区间前须确认时区 |
| **分页** | `pageSize ≤ 100`（活动商品 goods-search 例外 ≤200）；建议 20 起步；上游因响应超预算拒绝时缩小范围重试 |
| **响应解读** | 外层结构、成功标志、错误码与 traceId 位置以当前运行时工具说明为准；解包后的业务字段按目标能力契约读取，不假设固定信封。回执不代替未返回的对象状态，错误不等于空列表 |
| **同名活动消歧** | 用户只说“活动”且未明确类型时，本域无匹配还需读取营销域契约，查询 CPS 活动奖励（`ops.marketing.cps-activity.search`，name）、互动活动（`ops.marketing.interactive-activity.search`，keyword）、活动推广（`ops.marketing.cps-promotion.search`，activityName）。用户已明确券模板等对象时，先查该对象，不因名称跨域；无结果只说明已查范围内无匹配，不据此断言全域不存在。查询失败、权限拒绝均不算无结果 |
| **兑换码二义性** | 平台生成优惠券码、制卡或明确券码批次→本域；品牌方提供码、用户输入参与互动领奖→营销域 exchange-code。仅说“兑换码活动”无法定域，目的不明再澄清；互动奖品引用券模板不改变活动归属。明文导出是否开放见能力边界 |
| **错误恢复** | 错误分类名称以当前运行时契约为准：认证失效→重新连接；授权范围不足→确认授权；业务权限拒绝→停止、不换工具绕行；参数错误→按契约修正；上游失败/超时→查询可稍后重试或缩小条件。**写失败可能已生效**，按下行核验，不能当无数据 |
| **写操作语义** | 单次提交，不自动重试。写失败/超时结果未知时先查对象状态；确认未生效且参数无误才至多重试一次，仍失败交用户决策。幂等能力（发券 requestId/增库存 batchOperationId/兑换码 createRequestId）重试保持同键同参，禁止换新键掩盖未知结果 |
| **审核链纪律** | 活动与券模板不存在"直接创建"——一律走「创建草稿 → 提审 → 审核」链。编辑/提审带内容必传 `version`（来自草稿详情）；驳回原因必填且具体可行动，**禁止 AI 编造审核结论与驳回原因** |
| **写操作确认** | 除下方资金面高危操作的专项确认外，用户明确要求操作且关键字段、完整对象清单齐全，即可作为业务确认，无需为相同内容机械追加询问。执行前核对对象并说明实际影响，仍遵循当前运行时审批；参数缺失、对象歧义或影响超出原指令时补问。用户取消后停止写入及后台重试。需采用业务默认值、同名多条、发现新的关联影响（如赠品引用>0）、版本冲突或导入部分失败时，说明后确认处置；状态前置不符时停止，不以确认绕过。**「定向/发放」语义边界**：建定向人群券或配置定向发放仅授权创建模板和设置人群，不包含实际发券；人群圈选或标签绑定不构成发放授权。实际发券前须按下方专项规则确认券模板、会员清单及每人数量，未确认时只做配置并汇报 |
| **布尔值** | 传 `true`/`false`；枚举严格按 `promotion-enums.md` 字典大小写（`MYJ`/`MJ_COUPON` 大写、tab 值小写、赠品池组合状态小写下划线如 in_use/available——off_shelf/out_of_stock 当前实现不可达） |

### 操作风险档位（写操作前必读）

| 档位 | 操作 | 说明 |
|------|------|------|
| 🔴 资金面高危（**先发确认卡、获用户确认后才可调用** + 执行后回读） | 发券（send）、退券（cancel）、券停用（stop）、兑换码批次创建/生效/作废、单码作废 | 直接影响用户资产。**发券（send）执行前必须已存在一张用户已回答的确认卡**（内容含券模板名/面额、会员 ID 清单、每人数量）；没有该确认卡就调用 send 属于违规——「定向人群/定向发放/批量发券」类指令不构成隐式确认，先发卡等用户答 |
| 🔴 不可逆（执行前确认完整对象清单） | 活动删除、pending 删除（物理删除）、券模板删除、移除赠品（单记录 / 按 SPU） | 删除后不可恢复 |
| 🔴 商业影响（确认数值/清单 + 执行后回读） | 活动停用（提前结束）、券模板停用、活动库存增加、券延期、券解锁、审核驳回 | 影响面大或公开可见 |
| 🟡 可逆写（执行 + 核验结果 + 说明） | 创建草稿、编辑草稿、提审、撤回、审核通过、发起变更重审（start-edit，仅生成变更草稿快照）、活动暂停/恢复、券模板暂停/恢复、赠品批量添加、主题创建/编辑/删除/归组/移出、太阳码/短链生成 | 可撤销或低影响 |
| 🟢 只读 | 全部 search/detail/logs/stats/calendar/report/check 类能力 | 可直接调用 |

> 表内及契约中的“确认”按通用约定解释，完整原指令可确认；新增影响须补问，运行时审批仍执行。

> ⚠️ 赠品移除（remove/remove-by-spu）为 🔴：服务端**不校验引用数**，引用 >0 也会删除；引用计数仅覆盖部分状态下的商品行，0不能排除暂停活动或草稿引用。执行前按gift-pool契约查引用、核对关联影响并与用户确认——与 gift-pool-action.md 契约口径一致。

**字段确认红线（禁止 AI 编造）**：优惠规则（门槛/优惠值/折扣）、审核结论与驳回原因、发券对象与数量、库存增量、延期天数、兑换码数量——必须由用户明确给出。

### 写后核验与结果表述

核验用于确认实际保存内容或最终状态。创建成功、配置核对完成和正式生效是三个结论，分别按已有证据表述；后续查询失败不能改称创建接口失败。

| 场景 | 核验方式 |
|---|---|
| 普通同步草稿创建/编辑 | 若目标契约明确返回服务端保存后的完整快照，且包含对象ID、草稿状态、版本和本次修改的全部字段，可用该快照核对，不机械追加同一查询。入参回显或仅返回成功/ID不满足此条件：查 pending.detail 核对规则、日期和范围；字段缺失不补猜。当前本域草稿写契约均未声明该完整持久化快照，默认查 pending.detail |
| 提审/撤回/审核/暂停/恢复/删除等状态转换 | 按目标契约查询最终状态。草稿期查 pending；审核通过后 pending 删除，普通活动查正式详情，券模板按正式 templateId 来源链查询；审核驳回后 pending 保留，查 pending.detail 核对 checkStatus=3；删除核验业务上的已删除/不存在，查询失败不等于不存在 |
| 其他同步配置写（主题创建/编辑/归组、赠品添加等） | 按目标契约用对应详情/搜索核对本次配置。保存视图可以说明其实际返回的保存结果，不冒充独立查询；部分失败逐项说明，缺失结果不补猜 |
| 发券/退券/券停用/延期/解锁及商业影响操作 | 保留目标契约要求的执行后回读，核对对象、状态或增量；完整写回执不自动免除该要求。库存增加的内部回读例外按下方处理 |
| 异步处理、超时或网络失败 | 按契约查询/轮询原对象，区分已完成、处理中与结果未知；预算耗尽报告最后状态。保持原幂等键，未核实结果前不重复写入 |
| 物料生成 | 核对真实返回的物料格式和内容，不为没有详情查询的物料编造查询能力 |

- 用户任务或验收明确要求独立查询时仍执行；返回快照或接口内部回读不能冒充另一次独立查询。
- stock.increase 的提交后查询结果可按该契约用于核验；availableCount=0可能是缓存缺失/查询降级，不能仅凭非空认定售罄。缺失/null补查stock.items，同源反复0仍可能未知，不据此换批次增库。任务指定独立查询时仍执行。
- 成功回执只支持其实际承诺的保存结果；只有核对到相应字段或终态才说“已核验”。草稿保存不代表可提审、已审核或可参与交易。

### 调用前完整性检查（强制）

1. 展开读取入参表全部叶子字段；嵌套结构（rules/goodsList/items/stackableExclusions）继续读取其子表。
2. 区分必填、条件必填（如 PASSCODE 必传 passcode、驳回必传 reason、编辑必传 version）与可选。
3. 枚举用 `promotion-enums.md` 字典精确值；金额与折扣按目标字段契约，元单位例外见通用约定。
4. ID 一律十进制字符串；memberId 是字符串。
5. 确认对象当前状态（活动状态机/审核状态/券实例状态/批次状态），按状态前置调用。
6. **pendingId 与正式 ID 不可混用**：编辑/提审/审核用 pendingId；生命周期操作（暂停/停用/删除/报表/分享）用 promotionId/templateId/batchId。
7. 创建/复制/编辑/提审按 `form-validation.md` 检查合并修改后的完整配置；改一个日期须重验关联窗口，草稿保存不代表可提审，不能静默编造日期或改变用户要求保留的发货时刻。

## 环境与执行边界

- 缺失字段不等于零、不存在；**活动/券模板详情不返回商品清单**（只有 `goodsCount` 总数），商品一律用 `activity.goods-search` / `goods-all`；库存元数据不可确认（unlimited=null）时不得当不限量表述。
- **敏感原文不复述**：券实例详情的 `code`（券码明文）、口令购的 `passcode`、口令码校验的 `normalizedCode` 均为未脱敏原值——只在用户明确要求核对时转述，禁止写入标题/备注/报告或导出到对话外。
- **回显字段不等于原入参**：详情的 `audienceType`、主题归组的 `revision`、券模板详情的 `totalStock` 都是服务端派生/计算值，编辑回填时以 pending 草稿快照为基线，不要拿详情回显值直接回传。
- 创建/编辑为**草稿快照**语义：编辑前先读 pending 详情，抽取可编辑请求快照并合并本次修改，按完整快照保存；主要字段缺省可被清空，不按PATCH理解。保留有效未改字段，清理已失效模式字段和已被完整配置替代的已知私有草稿（见specialty）；编辑保存不等于生效，生效以审核通过为界。
- 图片/物料 URL 需用户直接提供云MALL可访问地址；当前 Capability Catalog 未登记上传能力，不把陌生 URL 当可信内部素材。
