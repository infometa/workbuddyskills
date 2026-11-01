---
name: marketing
display_name: 云MALL营销
display_name_en: CloudMall Marketing
description: 营销域技能包：CPS 分销（活动奖励/活动推广/商品与爆品推广/结算/佣金缺失排查/分销员申请/分组等级/佣金率与定向佣金/提现打款/分销规则）、导购（主档调店/客户归属公共池/目标计划/提成/业绩看板/推广任务/话术/素材）、首页弹窗审核链、互动营销活动（九宫格/大转盘/签到/兑换码等八类、奖品模板、实物发货；分销员等级=本域非会员等级）、协议（隐私政策等9类）。本域定位：拉新/留存/扩品牌（分销拉人/互动拉客/弹窗曝光/协议信任），非卖货转化。防混淆：满减/券模板/券实例/平台生成券码批次/秒杀/拼团→促销域；品牌方兑换码输入领奖的互动活动→本域；分销/导购/弹窗/互动/协议→本域；商品价格库存→商品域；**推广追踪单/渠道追踪（追踪单停用、渠道配置、会员行为）→商户域**——本域仅有 CPS 推广商品与导购推广任务。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths; execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.3.10
author: 云MALL
---

# 云MALL营销域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方模块路由表定位契约文件，capability 级选择在**契约文件头部**的「能力索引」行（含语义与 🔴 风险标记）。写操作的前置条件/幂等键/状态约束在对应契约锚点内。
> **域边界**：满减/满折/秒杀/折扣/**优惠券（券模板/券实例/平台生成券码批次）**/赠品/预售/拼团属**促销技能包**（已建成，勿越界）——运营口语的"活动/优惠"多数指促销；本域只收 **CPS 分销（分佣/佣金/分销员/提现）、导购（归属/目标/提成/业绩/任务/话术/素材）、首页弹窗、互动营销活动、协议**。商品价格与仓库库存属商品域；会员资产（积分/余额）属会员域；门店主档与门店分组属商户域；订单查询属交易域。命中这些意图时说明超出营销技能范围。
> **业务目的定位**：本域的业务本质是**拉新、留存、扩大品牌**——让更多人成为分销员/导购、让用户参与活动领奖品、让用户看到品牌内容。**不是让商品更便宜**（降价/优惠/限时/拼团促下单是促销域）。运营说"搞个活动"时，语境是"送/领/参与/邀请/签到/抽奖/成为分销员"→归本域；语境是"打折/便宜/满减/拼团买"→归促销域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查状态/列表/详情/账户/统计/日志/看板） | 模块路由表 → 定位契约文件 → 文件头「能力索引」选 capability → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作** | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应场景文件（见下表）→ 契约锚点 → 按风险档位确认后调用；action 契约头部均指引「先读 query 现值再全量提交」 |
| **客诉排查**（分销佣金缺失/订单没算佣金） | `references/flows/cps-diagnosis-flow.md`（诊断决策树，只读优先）→ 契约锚点 |
| **概念咨询/异常排查**（查状态含义/操作前置/枚举值） | `references/domains/marketing-enums.md`（状态机/枚举字典）→ 契约锚点 |
| **概念咨询/异常排查**（规则怎么算/实体口径/优先级/互斥） | `references/domains/` 概念文件：CPS=`cps-concepts.md`；导购=`guide-concepts.md`；弹窗/互动/奖品/协议/跨模块=`marketing-concepts.md` |
| **导出/导入** | `references/flows/marketing-support-flow.md` + `export-task.md`（任务轮询）；`*.export` 契约在各 `*-query.md`、`*.import` 在各 `*-action.md` |

写操作按业务族路由：

| 业务族 | 流程文件 |
|-------|---------|
| CPS 活动奖励/活动推广 | `cps-activity-flow.md` |
| CPS 结算明细/商品推广 | `cps-settle-flow.md` |
| CPS 分销员/申请/分组等级/佣金率 | `cps-distributor-flow.md` |
| CPS 提现（资金面最高危） | `cps-withdraw-flow.md` |
| 导购主档/客户归属/等级绑定 | `guide-flow.md` |
| 导购目标/提成/业绩 | `guide-incentive-flow.md` |
| 导购推广任务/话术/素材 | `guide-content-flow.md` |
| 弹窗审核链 | `popup-review-flow.md` |
| 互动活动 | `interactive-activity-flow.md` |
| 协议/导入导出 | `marketing-support-flow.md` |

## 模块路由表（模块 → 契约文件）

> 一行一模块；capability 级索引（含语义与 🔴 风险标记）在**各契约文件头部**的「能力索引」行——由 SKILL.md 定位文件后，在文件头选择 capability、读 `## ✅ capability` 锚点。所有 capability 前缀为 `ops.marketing.`。

| 模块 | 业务覆盖 | 契约文件（`references/apis/marketing/` 下） |
|------|---------|------|
| CPS 活动奖励 / 分销规则 | 活动分页/详情/冲突校验；保存/发布/终止；全局分销规则读写 | `cps-activity-query.md` / `cps-activity-action.md` |
| CPS 活动推广 | 爆品推广/平台活动：查询/创建/发布/结束；效果报表与导出 | `cps-promotion-query.md` / `cps-promotion-action.md` |
| CPS 结算明细 | 分销员×活动结算汇总（活动/全局维度）；手动结算；明细导出 | `cps-settle-query.md` / `cps-settle-action.md` |
| CPS 商品推广 | 商品可推广性查询/选品器/批量启停 | `cps-goods-promotion-query.md` / `cps-goods-promotion-action.md` |
| CPS 分销员 | 列表/详情/佣金账户三余额/流水；绑定关系；Excel 导入导出 | `cps-distributor-query.md` / `cps-distributor-action.md` |
| CPS 分销员申请 | 申请列表/审核（通过即建分销员）/申请设置 | `cps-apply-query.md` / `cps-apply-action.md` |
| CPS 分组与等级 | 分销员分组；等级（返佣系数/升降级规则/规则页） | `cps-group-level-query.md` / `cps-group-level-action.md` |
| CPS 佣金率 | 四级佣金率体系（全局/定向/分组）；分销订单导出；订单佣金补算 | `cps-commission-query.md` / `cps-commission-action.md` |
| CPS 提现 | 提现列表/详情/审核日志；审核（触发异步打款）与设置——资金面最高危 | `cps-withdraw-query.md` / `cps-withdraw-action.md` |
| 导购主档 | 导购生命周期（新增/调店/停用/启用/归档）；统计/日志；导入导出 | `guide-query.md` / `guide-action.md` |
| 导购客户 | 客户归属（列表/360 画像/轨迹/转移）；公共池；绑定关系 | `guide-customer-query.md` / `guide-customer-action.md` |
| 导购等级与绑定设置 | 导购等级（≤6 个）；绑定设置四区域 | `guide-level-settings-query.md` / `guide-level-settings-action.md` |
| 导购目标计划 | 目标计划与目标行（填值/按上期填充/导入） | `guide-target-plan-query.md` / `guide-target-plan-action.md` |
| 导购提成 | 提成规则（冲突检测）；明细统计与批量结算 | `guide-commission-query.md` / `guide-commission-action.md` |
| 导购业绩 | 业绩方案（互斥生效）；业绩明细；导购看板 | `guide-performance-query.md` / `guide-performance-action.md` |
| 导购推广任务 | 任务创建/下发/催办/结束；执行记录 | `guide-task-query.md` / `guide-task-action.md` |
| 导购话术 | 话术内容块/分组/置顶；导入导出 | `guide-speech-query.md` / `guide-speech-action.md` |
| 导购素材 | 业务素材/内容素材/素材分组；传播统计；复制记录导出 | `guide-material-query.md` / `guide-material-action.md` |
| 首页弹窗 | 审核链（创建/提审/审核/投放/暂停/下线）；全局策略；效果统计 | `popup-query.md` / `popup-action.md` |
| 互动营销活动 | 八类活动 draft/formal 双版本；查询/编辑/发布/生命周期。**⚠️ 新建撞 code=5006「请选择适用人群」时勿反复重试，立即改走 copy 复制路径（见环境与执行边界「互动活动创建校验」条）** | `interactive-activity-query.md` / `interactive-activity-action.md` / `interactive-activity-lifecycle-action.md` |
| 互动奖品履约 | 实物发货（SENDED 终态）；奖品库存调整（只能增） | `interactive-activity-prize-action.md` |
| 奖品模板 | 积分/优惠券/实物三类模板；启停；图片上传 | `prize-template-query.md` / `prize-template-action.md` |
| 协议管理 | 9 类协议（同类型互斥发布）；插图上传 | `agreement-query.md` / `agreement-action.md` |
| 通用导出任务 | 全部 `*.export` 的任务状态轮询与下载链接 | `export-task.md` |

### 未开放（不调用，只整理需求）

| 模块 | 未开放项 | 原因 |
|---|---|---|
| 导入模板下载（全模块） | 分销员/导购/话术/目标计划的导入模板 Excel 文件流 | 二进制文件下载超出工具返回契约；模板列结构以运营端页面下载为准 |
| CPS 结算明细 | 活动数据明细（订单维度） | 后端无对应端点（前端调用必然失败），订单数据走交易域 |
| CPS 提现 | 提现列表导出 | 前端有入口但**后端无对应端点实现**（前后端契约缺口），需后端补齐 |
| 导购客户 | 客户消费记录明细 | 本期后端未注册路由（前端空态），消费概要走客户 360 画像 |
| 导购话术 | 批量操作旧入口（batch-operate 后端已废弃） | 仅剩导出场景兼容，改分组/删除用 batch-update-group / batch-delete，导出走 guide.speech.export；**Catalog 未登记该入口** |
| 导购素材 | 素材文件上传 | 素材创建链路未纳入能力化范围；素材引用已上传地址 |
| 弹窗 | 统计导出（Excel 文件流） | 服务端导出实现仍为 TODO（返回空文件）；选项类接口（券/活动页/标签/门店选项）为前端 mock 或复用其它域接口，无独立端点 |
| 互动活动 | C 端参与/抽奖/签到等运行时接口（Internal/App 侧）、玩法运行时数据（邀请/助力明细） | 面向 C 端运行时，不属运营端能力面；统计已并入数据监控 |

---

## 通用约定（护栏）

| 项 | 约定 |
|----|------|
| **调用方式** | 只能调用 Layer 3 中标注了 capability 的能力：查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`。输入 `{capability, input, summary}`；`summary` 一句话说明意图。**不得猜测或编造未登记的 capability** |
| **入参字段名** | 以契约参数表为准，**大小写敏感**；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工） |
| **身份与授权** | 身份由连接授权绑定；查询需 `mall.query`、写操作需 `mall.action`，且受当前账号实时业务权限限制（权限不足得 PERMISSION_DENIED）。不询问、不传入租户/账号/Token/服务名/路径/权限码；门店/会员/标签等业务参数必须来自用户或查询结果 |
| **ID 序列化** | 雪花 ID（id/uid/groupId/levelId/planId/detailIds 等）一律**十进制字符串**，严禁 Number。注意四类特殊形态：① CPS 活动奖励与互动活动的 `activityId` 为**业务 ID 字符串**（CPS 为 16 位数字串；互动活动为业务 ID 非数据库主键）；② 分销员/客户 `uid` 为字符串会员 ID；③ 活动推广/商品推广等数字主键出参已序列化为字符串；④ 提现单号 `withdrawNo` 为 **WD 前缀业务单号**（WD+日期+分片+序列，约 22 位字母数字），非纯数字，原样传递 |
| **⚠️ 金额单位** | 本域**金额一律单位元**（两位小数）：奖励金额、佣金/提成金额、提现金额、业绩值、销售额目标、minAmount/maxPerOrder/autoPassThreshold。**佣金率与分成比例为小数比例**（0.1=10%，范围 [0,1]）；**CPS 等级返佣系数为乘数**（1.0000=100% 基准，范围 0..10.00，填 1 表示 1 倍而非 1%）；提成 fixed 规则的 commissionRate 为元金额；cumulative_ladder 阶梯门槛以万元数值录入。与促销域"分"的约定不同，禁止混用 |
| **时间格式** | 时间字段一律 `yyyy-MM-dd HH:mm:ss`；日期字段（joinTime/startDate/endDate/statsDate）为 `yyyy-MM-dd`。例外：互动活动 configInfo 的 activityTimeRule（startTime/endTime/可选 reserveTime）、SIGN.signRule.startTime 与 expireConfig 的 fixTime/fixTimePerDay 为**毫秒时间戳**；cps-activity.search 的 startTimeBegin/End 无显式格式注解，按 ISO `yyyy-MM-dd'T'HH:mm:ss` 传递（非必要不传）；分销规则 followUpValiditySeconds 为秒数（0=永不过期） |
| **分页** | `pageSize ≤ 100`（建议 20 起步）；**例外**：分销员流水 deal-records ≤50；互动活动/中奖记录/奖品模板默认 10。响应超预算返回 UPSTREAM_ERROR 时缩小范围重试 |
| **响应信封** | 成功 `{capability, data, traceId}`，data 为上游原始业务数据；错误 `{errorCode, message, retryable, traceId}` |
| **错误恢复** | `AUTH_REQUIRED`：重新连接；`SCOPE_INSUFFICIENT`：重新确认授权；`PERMISSION_DENIED`：停止该操作不绕行；`INPUT_INVALID`：对照参数表修正；`UPSTREAM_ERROR/UPSTREAM_TIMEOUT`：查询可稍后重试或缩小条件；**写操作禁止立即同参重试**——先回读核对是否已生效，确认未生效且参数无误后至多重试一次，仍失败如实报告由用户决策（写 500 可能已生效，盲目重试有副作用）。**失败不等于无数据** |
| **写操作语义** | `当前运行时的 Capability 写操作执行器` 为纯执行器：单次提交（永不自动重试）原样返回。超时/网络错误结果不确定——**先查对象状态再决定动作，不盲目重复提交**。批量操作多为**逐条执行、部分成功无逐项回执**（弹窗批量下线/删除、商品推广启停、佣金批量），执行后必须回读核验。**空响应仍须回读**：publish/terminate/delete/end/offline 等终态类写操作成功时常返回空 data——"操作成功"不等于"已核验"，仍须回读目标对象确认状态已流转或已删除，再向用户报告结果 |
| **审核链纪律** | 弹窗带完整审核链（创建→提审→审核→投放）；创建/编辑/审核是三种不同角色动作。审核结论与驳回原因必须来自用户明确指示，**禁止 AI 编造**（弹窗 REJECT 的 reason 必填且 ≥10 字）。cps-apply.audit 驳回 auditRemark 必填 |
| **写操作确认** | 只在用户明确要求执行对应操作时调用写能力；创建/编辑须先确认关键字段（奖励金额/佣金率/分成比例/目标值/时间窗/范围）。整表覆盖式接口（cps-rule.save、cps-apply.save-settings、cps-withdraw.save-settings、guide-bind-settings.update、popup.update-global-strategy、save-relative-scenes）**必须先查询现值、原值回传只改需要改的字段** |
| **生命周期纪律** | flows 里的生命周期/流程图是**对象状态机参考，不是单次执行清单**：用户说「建/做/配置」只执行创建与编辑，publish / activate / submit / dispatch 等生效类动作**必须由指令显式触发**——不得因"目标看起来需要生效"而自主补齐后半段；做到指令要求的步骤后停下汇报，可顺带询问是否发布。 |
| **副作用确认（硬门禁）** | 动作会影响**指令对象之外**的数据时，即使指令本身明确，也必须先复述受影响对象并取得确认：协议发布（同类型现行版本自动结束）、业绩方案启用（原生效方案自动停用）、弹窗 EDIT_APPROVE（先应用 popupData）、互动活动发布（C 端立即可见）。**「用户说了发布」不等于「用户确认了副作用」**——受影响对象须点名复述。 |

| **全局生效写确认（硬门禁）** | 全租户/全局生效的配置写，**无论指令参数是否齐全，提交前必须发确认卡复述「现值 → 目标值」并取得明确确认**：全局弹窗策略（popup.update-global-strategy）、绑定设置更新（guide-bind-settings.update）、业绩方案启用（guide-performance-plan.activate）、申请设置保存（cps-apply.save-settings）、提现设置保存（cps-withdraw.save-settings）、分销规则保存（cps-rule.save）、等级规则页保存（cps-level.save-rule-page）。参数齐全只说明「知道改什么」，不等于「已授权改」——此类写影响全部用户/全部后续业务，漏发确认即为执行纪律违规。 |
| **布尔值** | 传 `true`/`false`；枚举严格按 Layer 1 字典大小写——弹窗/互动活动/提现状态全大写（`PENDING_REVIEW`/`RUNNING`/`PENDING_AUDIT`），导购/素材/任务状态小写（`active`/`draft`/`published`），互动活动类型小写中划线（`sudoku-lottery`），CPS 活动状态小写（`draft`/`running`）；整数枚举（cps 状态 0/1/2、协议 0/1/2）勿传字符串 |

### 操作风险档位（写操作前必读）

| 档位 | 操作 | 说明 |
|------|------|------|
| 🔴🔴 提现单审核（核对对象与结论 + 运行时审批 + 执行后复查） | cps-withdraw.audit（PASS 触发异步真实打款；REJECT 回退余额） | 用户对象/结论明确后不另发追问卡重复审批；执行摘要说明单号、分销员、金额、渠道和后果，缺参或指令冲突才澄清；不虚构已确认或已受理 |
| 🔴🔴 其他资金面最高危（逐项复述确认 + 执行后复查） | 提现设置（cps-withdraw.save-settings）、批量标记提成结算（guide-commission-detail.batch-settle）、设全局佣金率（cps-commission.set-global-rate） | 直接决定资金流转，既有字段与全局配置确认纪律不变 |
| 🔴 资金面高危（确认数值来源 + 执行后回读） | 手动结算（cps-settle.manual-settle）、商品定向/分组佣金率写操作与取消定向（cps-commission.*）、CPS 等级创建/启停/批量修改/规则页保存（返佣系数直接放大缩小分佣） | 佣金率/系数变更影响结算 |
| 🔴 不可逆（执行前确认完整对象清单） | CPS 活动终止/删除、活动推广删除（**无状态校验，进行中也能删**）、分销员分组删除、导购归档（终态）、导购等级删除、目标计划删除（级联）/清空目标值、提成规则停用（无启用通道）/删除、业绩方案删除、任务结束、话术删除/批量删除、业务素材批量移除、内容素材删除、素材分组删除、弹窗下线/批量下线（ENDED 终态）/删除/批量删除、互动活动结束/删除、实物发货（SENDED 终态）、协议结束/删除 | 删除/终止/终态后不可恢复 |
| 🔴 商业影响（确认清单 + 执行后回读） | 新建/启停/批量改分销员、申请审核（通过即建分佣主体）与申请设置、分组创建/编辑、客户归属转移/公共池分配/绑定释放、导购停用（必须处置客户）与调店、绑定设置更新（全租户）、按上期填充目标（覆盖式）、业绩方案启用（全局互斥）、任务下发与直接下发创建、内容素材发布/取消发布、弹窗审核、全局弹窗策略、互动活动发布、库存调整（只能增）、协议发布（同类型旧版自动结束） | 影响面大或公开可见/全局生效 |
| 🟡 可逆写（做 + 向用户说明） | 各类草稿创建/编辑（CPS 活动、弹窗、互动活动、内容素材、话术、提成规则、目标计划、协议）、提审、复制、暂停/恢复、取消发布、启停切换、置顶、显示切换、分享计数、催办、单条目标填值/加行/删行、编辑等级/分组/方案/任务、保存分销规则/关联场景/等级配置 | 可撤销或低影响 |
| 🟢 只读 | 全部 search/detail/list/logs/stats/check/report/tree/options/preview/summary/trend 类能力 | 可直接调用 |

**字段确认红线（禁止 AI 编造）**：奖励金额与阶梯、佣金率（全局/定向/分组）、分成比例（之和=1）、返佣系数、提现审核结论与驳回备注、弹窗审核结论与驳回原因（≥10 字）、提现设置金额阈值与积分比例、目标值与填充百分比、互动奖品库存目标值（只能增）、实物发货运单号与物流公司——必须由用户明确给出。

### 调用前完整性检查（强制）

1. 展开读取入参表全部叶子字段；嵌套结构（prizeInfo/configInfo/selectGoods/relatedContent/dispatch/attachment/ruleConfig/templateConfig/scopes/items）继续读取其子表。
2. 区分必填、条件必填（如 overlap-check 的 configInfo 四维度 type、cps-apply.audit 驳回的 auditRemark、弹窗 REJECT 的 reason、coupon 类奖品模板的 bizTemplateId）与可选。
3. 枚举用 Layer 1 字典精确值；注意本域金额单位元、佣金率小数比例、返佣系数乘数、阶梯门槛万元数值。
4. ID 一律十进制字符串；区分业务 ID（CPS/互动活动 activityId）与主键 ID；uid 为字符串会员 ID。
5. 确认对象当前状态（各状态机前置：提现仅 PENDING_AUDIT 可审、弹窗 7 态、互动活动双版本、导购四态、CPS 活动 draft→…），按状态前置调用。
6. **营销 vs 促销防混淆**：券模板/券实例/平台生成券码批次及满减/秒杀/拼团 → 促销技能包；品牌方提供码、输入领奖、兑换码互动活动 → 本域 `exchange-code`（奖品引用优惠券不改变活动归属）；仅说兑换码且目的不清时才澄清。**正向信号优先**：指令或对象名含「分销/佣金/激励/奖励/每单/爆品/分销员/导购/弹窗/互动/签到/抽奖/兑换码活动/品牌方提供码/输入领奖/协议」等本域信号词，或按名称在本域能查到对象时，直接走本域——不要先去促销域试探再折返（"活动"是泛称，本域的 CPS 活动奖励/活动推广/互动活动都是活动）。**找不到 ≠ 不存在**：运营口语说「活动」时，本域就有三种活动——CPS 活动奖励（cps-activity.search，名称模糊搜）、互动活动（interactive-activity.search，keyword）、活动推广（cps-promotion.search，activityName），加上促销域共四类同名可能。按名称/关键词在某一个域搜不到时，**必须把其余三个域都搜一遍再下结论**（全是只读查询，成本极低）；四个域都没有才回答"不存在"。禁止只搜一个域（尤其只搜促销域）就断言对象不存在或要求用户提供 ID。

**跨域同名词消歧（等级/分组/模板/任务/规则——两个以上域存在同名概念，路由前先按下表定位）**：
- **等级**：分销员等级/返佣系数/考核指标/升降级 → 本域 cps-level；导购等级/levelSort → 本域 guide-level；会员等级/成长值/权益/V0-V4/SVIP → 用户域。"XX 的升级门槛/返佣"优先本域，"会员/成长值/权益"优先用户域——某一域找不到时按本表把其他域查一遍。
- **分组**：分销员分组/分组佣金 → 本域 cps-group；素材分组 → 商户域；商品分组 → 商品域。
- **模板**：奖品模板 → 本域 prize-template；优惠券模板/券模板 → 促销域；运费模板/履约模板 → 商户域。
- **任务**：推广任务/下发/催办 → 本域 guide-task；成长值任务 → 用户域。
- **规则**：分销规则/跟单有效期 → 本域 cps-rule；提成规则 → 本域 guide-commission-rule；活动规则/优惠规则 → 促销域。

同时警惕三套结算状态（CPS 活动侧字符串 '0'/unsettled/settled、CPS 明细侧整数 0/1、导购提成侧 pending/settled）不可混用。

---

## 环境与执行边界

- **临时预签名 URL 不可持久化**：CPS 活动/活动推广图片（60 分钟）、内容素材附件（30 分钟）、奖品模板 image（约 60 分钟）、协议富文本图片 src（约 30 分钟）均为带时效临时地址，过期需重查，不要写入任何持久化产物。
- **导购激活走导购端小程序**：运营端无激活端点，pending 状态可能长期存在；导购列表不传 status 会包含已归档记录。
- **提现打款为异步链路**：审核接口返回成功不代表打款成功——必须稍后用列表/详情复查提现状态（微信渠道存在 WAIT_USER_CONFIRM 中间态，需用户确认收款）。
- **批量操作部分成功无回执**：弹窗批量下线/删除、商品推广启停、佣金批量结算等均为逐条执行、失败跳过——执行后必须回读列表/统计核验实际结果。
- **cps-promotion.delete 无状态校验**：进行中的活动推广也能直接物理删除（等于强制下线），执行前务必与用户逐项确认清单。
- **互动活动 EXPIRED 为惰性展示态**：按 status=EXPIRED 筛选中奖记录返回空，超期记录筛 WAITING_CLAIM 再看 expireTime；状态筛选传 PUBLISHED 视为非法（空列表）。
- **整表覆盖式接口纪律**：分销规则/申请设置/提现设置/绑定设置/全局弹窗策略/关联场景均为整体覆盖——先查询现值、原值回传只改需要改的字段；提现设置机密字段留空=保留旧值。
- **缺失字段不等于零、不存在**：目标值为空表示尚未设定；提现详情的条件字段（wxState/failReason/settleTime）仅对应状态下出现；cps-rule.get 未保存过返回 null。
- **图片/物料 URL 需用户直接提供云MALL可访问地址**（建议裸地址）；本域已登记的上传能力仅**协议插图**（agreement.upload-image）与**奖品图片**（prize-template.upload-image）两项，均要求当前运行时提供文件型 capability，本地路径不得放入结构化 input；不把陌生 URL 当可信内部素材。
- **互动活动创建校验（5006 处理协议）**：部分环境对**新建**互动活动启用了「请选择适用人群」必填校验（code=5006），该字段未文档化、换字段组合/复刻已有活动配置/换活动类型**均无法绕过**。处理协议：**create 撞 5006 最多重试 1 次（共 2 次尝试）**，仍失败立即改用 `interactive-activity.copy` 复制一个现有已发布互动活动生成草稿（复制不触发该校验），再用 `interactive-activity.update` 补充名称/时间/奖品等差异配置；若 update 补配置也被拦，如实告知用户 API 路径受限、建议走管理后台，并说明该限制待平台侧补文档——**禁止超过 2 次继续硬试 create**。详见 `interactive-activity-action.md` 的「⚠️ 已知环境限制」段。
- **异步导出闭环**：全部 `*.export` 能力只返回任务 ID，必须配合 `ops.marketing.export.task.get` 轮询（`PENDING`/`PROCESSING` 继续、`COMPLETED` 取 `downloadUrl`、`FAILED` 停止报告）；`downloadUrl` 有时效（约 30 分钟），过时重新发起导出，不持久化、不当稳定链接转述。**导出为非幂等操作**（每次调用创建新导出任务）——超时不要盲目重试，先轮询任务状态确认是否已创建。
- **导出内容含明文 PII**：分销员/导购/结算明细等导出文件含手机号等未脱敏个人信息（与对应查询接口出参同构）——向用户转述导出结果时遵守同查询接口的打码纪律；不把导出内容或 `downloadUrl` 写入任何持久化产物或第三方渠道；交付时提醒用户妥善保管文件。
- **Excel 导入纪律**：导入仅文件型 capability 可执行；导入结果含成功/失败明细，失败行修正后重导，不盲目整批重复提交；导入模板的列结构以运营端页面下载为准（三条导入链路的服务端大小上限未经仓库内配置证实，以网关实际限制为准）。
- **track-order-conf 即分销规则端点**：`/admin/marketing/cps/track-order-conf` 是全局分销规则的读写路径（对应 `cps-rule.get`/`cps-rule.save`，入参为 distributionRelationType/followUpValiditySeconds 等四字段）——旧文档将其误标为「跟踪订单配置 trackingDays/enabled」，以本表为准。
- 写操作超时或网络错误时结果不确定：先查询对象状态（搜索/详情/日志）再向用户说明；本域无幂等键机制，禁止盲目重复提交资金面与不可逆操作。
