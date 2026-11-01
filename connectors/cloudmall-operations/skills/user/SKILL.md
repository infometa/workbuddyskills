---
name: user
display_name: 云MALL用户
display_name_en: CloudMall Users
description: 本域定位：管理用户资产（会员/积分/权益），非卖货/分销/订单。用户域运营：会员档案（查询/创建/编辑/黑名单/打标/积分调整/流水/优惠券/导入导出，含会员名单导出/导入的任务进度与下载链接）、会员等级、会员权益与成长加速、成长值任务、积分明细、积分活动、积分抵扣、积分商城（积分商品；积分兑换订单仅支持查询/发货，不支持取消/导出）、升级礼包、反馈处理、微信小程序客服开关、微信分享（短链/URL Link；太阳码暂未对 Agent 开放）、标签（分类/规则/手工）、人群包（圈选/文件上传/动态）。防混淆：优惠券/满减/秒杀→促销域；分销/导购→营销域；商品价格库存→商品域；电话客服/客服电话/服务时间→商户域；交易订单/售后/物流→交易域（「积分兑换订单」仍属本域）。**等级二义性**：「等级」按名称搜不到时，可能是营销域的**分销员等级**（cps-level，返佣系数/考核指标体系）或**导购等级**（guide-level）——跨域查营销域后再下结论；本域等级特指会员等级（成长值/权益体系）。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths for user domain operations (members, points, and data tags); execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.6.2
author: 云MALL
---

# 云MALL用户域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。本技能包含两个子域：**会员与积分（member）**、**数据标签与人群包（data-tag）**。写操作的前置条件/状态约束在对应契约锚点内，本表不重复。

## 业务目的定位（本域是什么）

> 本域的业务本质是**管理用户资产与关系——会员档案/积分/权益/等级/标签是"用户是谁、有什么"的数据底座，不产生交易行为**。
> 不是卖货（促销）、不是管分销员（营销）、不是管订单（交易）。
> 简单判断：说"会员/积分/权益/成长值/等级/标签/人群"→本域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查会员/等级/权益/积分流水/积分商品/兑换订单/礼包/反馈/标签/人群包/配置现值） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作**（创建/编辑/启停/黑名单/打标/积分调整/导入导出/发货/圈选/上下线等） | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应业务族文件（会员档案与积分调整=`member-profile.md`；导入导出=`member-import-export.md`；等级与升级礼包=`member-level.md`；权益与成长值任务=`member-benefit.md`；积分明细/活动/抵扣=`member-points.md`；积分商城与兑换订单=`member-points-mall.md`；反馈/客服/分享=`member-support.md`；数据标签与人群包=`data-tag.md`）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值） | `references/domains/member-enums.md`（会员子域状态机与枚举字典；数据标签子域人群包状态机见 `references/domains/data-tag.md`）→ 契约文件锚点 |
| **概念咨询/异常排查**（实体关系/规则语义/标签双轨/规则表达式格式） | `references/domains/member-concepts.md`（会员子域）或 `references/domains/data-tag.md`（数据标签子域）→ 契约文件锚点 |

## 能力路由表（唯一索引）

> 所有 capability 完整 id = `ops.` + 下表短名（如 `ops.` + `member.member.search`；数据标签子域为 `ops.` + `data-tag.crowd.search`）。member 子域契约文件均在 `references/apis/member/` 下，data-tag 子域均在 `references/apis/data-tag/` 下。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器）

| 契约文件 | capabilities |
|---|---|
| `member-query.md` | member.member.search 会员分页查询 · member.member.detail 会员详情 · member.member.batch-get-by-uids 批量按 uid 反查 · member.member.tags 会员已绑标签 · member.member.coupons 会员优惠券 · member.member.points-flows 会员积分流水 · member.member.growth-flows 会员成长值流水 · member.member.addresses 会员收货地址 |
| `member-import-export-query.md` | member.member.export 导出会员（URL 型） · member.member.export-task.latest 最近一次导出任务 · member.member.export-task.list 导出任务列表 · member.member.export-task.status 导出任务状态 · member.member.import-task.latest 最近一次导入任务 · member.member.import-task.list 导入任务列表 · member.member.import-task.status 导入任务状态 |
| `member-level-query.md` | member.level.list 等级列表 · member.level.detail 等级详情 · member.level.rule-description 等级规则描述 · member.level.downgrade-rule 降级规则 · member.level.change-logs 等级变更流水 |
| `member-benefit-query.md` | member.benefit.list 权益列表 · member.benefit.growth-accel-detail 成长加速配置详情 · member.benefit.detail 自定义权益详情 |
| `growth-task-query.md` | member.growth-task.list 成长值任务列表 |
| `point-flow.md` | member.point-flow.search 积分明细分页 · member.point-flow.detail 积分明细详情 |
| `points-activity-query.md` | member.points-activity.search 积分活动分页 · member.points-activity.detail 积分活动详情 |
| `points-deduct-query.md` | member.points-deduct.config 积分抵扣配置查询 |
| `points-goods-query.md` | member.points-goods.search 积分商品分页 · member.points-goods.detail 积分商品详情 |
| `points-exchange-order-query.md` | member.points-exchange-order.search 兑换订单分页 · member.points-exchange-order.detail 兑换订单详情 |
| `points-mall-query.md` | member.points-mall.config 积分商城配置查询 |
| `upgrade-gift-query.md` | member.upgrade-gift.list 升级礼包配置列表 · member.upgrade-gift.config 全局开关查询 · member.upgrade-gift.issue-records 发放记录 |
| `customer-service-query.md` | member.customer-service.config 客服配置查询 |
| `feedback-query.md` | member.feedback.search 反馈列表 |
| `category-query.md` | data-tag.category.tree 标签分类树 |
| `tag-query.md` | data-tag.tag.search 标签分页 · data-tag.tag.detail 标签详情 · data-tag.tag.operators 标签操作者 · data-tag.tag.user-values 会员命中标签值 · data-tag.tag.batch-detail 批量标签详情 |
| `crowd-query.md` | data-tag.crowd.search 人群包分页 · data-tag.crowd.detail 人群包详情 · data-tag.crowd.task-records 任务记录 · data-tag.crowd.members 成员列表 · data-tag.crowd.members-detail 成员导入明细 · data-tag.crowd.download 成员明细下载 · data-tag.crowd.download-fail 最近导入失败明细下载 · data-tag.crowd.task-download-fail 指定任务失败明细下载 |
| `operator.md` | data-tag.operator.list 运算符列表 |

### 写能力（Capability 写操作执行器）

| 契约文件 | capabilities |
|---|---|
| `member-action.md` | member.member.create 新建会员 · member.member.update 编辑会员 · member.member.blacklist 加入黑名单 🔴 · member.member.unblacklist 解除黑名单 🔴 · member.member.bind-tags 绑定标签 · member.member.unbind-tag 解绑标签 · member.member.points-adjust 积分调整 🔴 |
| `member-import-export-action.md` | member.member.import 导入会员 🔴 · member.member.import-blacklist 导入黑名单 🔴 |
| `member-level-action.md` | member.level.create 新建等级 🔴 · member.level.update 编辑等级 🔴 · member.level.status 等级启停 🔴 · member.level.rule-description-save 保存等级规则描述 🔴 · member.level.downgrade-rule-save 保存降级规则 🔴 · member.level.upload-image 等级图片上传 |
| `member-benefit-action.md` | member.benefit.status 固定权益整体启停 🔴 · member.benefit.growth-accel-save 成长加速整体保存 🔴 · member.benefit.create 创建自定义权益 🔴 · member.benefit.update 编辑自定义权益 🔴 · member.benefit.delete 删除自定义权益 🔴 · member.benefit.sort 权益排序 🔴 · member.benefit.status-by-id 自定义权益启停 · member.benefit.upload-icon 权益图标上传 |
| `growth-task-action.md` | member.growth-task.save 保存成长值任务 🔴 |
| `points-activity-action.md` | member.points-activity.create 创建积分活动 🔴 · member.points-activity.update 编辑积分活动 🔴 · member.points-activity.enable 启用 🔴 · member.points-activity.disable 停用 🔴 · member.points-activity.delete 删除积分活动 🔴 |
| `points-deduct-action.md` | member.points-deduct.config-save 保存积分抵扣配置 🔴 |
| `points-goods-action.md` | member.points-goods.create 创建积分商品 🔴 · member.points-goods.update 编辑积分商品 🔴 · member.points-goods.on-shelf 上架 · member.points-goods.off-shelf 下架 · member.points-goods.batch-on-shelf 批量上架 🔴 · member.points-goods.batch-off-shelf 批量下架 🔴 · member.points-goods.delete 删除 🔴 · member.points-goods.batch-delete 批量删除 🔴 · member.points-goods.delete-item 删除单 SKU 子项 |
| `points-exchange-order-action.md` | member.points-exchange-order.ship 兑换订单发货 |
| `points-mall-action.md` | member.points-mall.config-save 更新积分商城配置 🔴 |
| `upgrade-gift-action.md` | member.upgrade-gift.save 保存升级礼包配置 🔴 · member.upgrade-gift.config-save 更新全局开关 🔴 |
| `customer-service-action.md` | member.customer-service.config-save 更新客服配置 |
| `feedback-action.md` | member.feedback.handle 处理反馈 |
| `wx-share-action.md` | member.wx-share.short-link 生成小程序短链 · member.wx-share.url-link 生成 URL Link · member.wx-share.qrcode 生成小程序太阳码（⛔ 暂未对 Agent 开放） |
| `category-action.md` | data-tag.category.create 创建分类 · data-tag.category.update 编辑分类 · data-tag.category.delete 删除分类 🔴 |
| `tag-action.md` | data-tag.tag.create-rule 创建规则标签 · data-tag.tag.create-manual 创建手工标签 · data-tag.tag.update 更新标签 · data-tag.tag.disable 禁用标签 · data-tag.tag.enable 启用标签 · data-tag.tag.delete 删除标签 🔴 |
| `crowd-action.md` | data-tag.crowd.create-rule-select 创建规则圈选 · data-tag.crowd.update 更新人群包 · data-tag.crowd.online 上线 · data-tag.crowd.offline 下线 · data-tag.crowd.delete 删除 🔴 · data-tag.crowd.upload 文件上传创建/追加 🔴 |
| `manual-tag-action.md` | data-tag.manual-tag.create-with-crowd 创建手工标签与动态人群包 · data-tag.manual-tag.add-users 批量添加用户 |

## 未开放（不调用，只整理需求）

| 模块 | 原因 |
|---|---|
| 导出文件下载 / 导入失败明细下载 / 导入模板下载（download/failures/template） | 文件流型下载——产品决策仅开放 URL 型导出；导出任务 `downloadUrl` 已覆盖下载需求，模板与失败明细走管理后台 |
| 积分商品优惠券选项（coupon-options） | 后端临时实现恒返回空列表（PromotionCouponFeignClient 未对接），开放无意义；券模板 ID 从促销域券模板查询获取 |
| 积分商品 ES 标记清理（ops/remove-tags） | 运维面（清理已删除商品的 ES 残留标记），不属运营开放能力 |
| 兑换订单导出（export） | 文件流型 + 后端首期空实现占位（EasyExcel 未接入，恒返回空响应体）——产品决策仅开放 URL 型导出 |
| 导购小程序码（guide-app/qrcode） | 顶栏展示辅助面（未绑定导购小程序时静默降级），无运营业务闭环 |
| 人群包上传模板下载（GET template） | CSV 文件流——产品决策仅开放 URL 型导出；模板列结构简单（单列 uid/openid/phone，按 convertType 决定），用户可自建文件 |
| 数据标签 internal 接口 / 缓存调试 / 兼容接口 | 非运营公开面 |

## 通用约定（用户域共享）

| 项 | 约定 |
|----|------|
| **等级二义性（找不到 ≠ 不存在）** | 「等级」在本域特指**会员等级**（成长值/权益体系 V0-V4）。按名称在本域搜不到目标等级时，**不要直接回答"不存在"或只追问用户**——先跨域查营销域的 `ops.marketing.cps-level.list`（分销员等级，返佣系数/考核指标体系）与 `ops.marketing.guide-level.list`（导购等级）；运营说的"XX 的等级/升级门槛/返佣"很可能是分销员等级而非会员等级。跨域都查完再下结论。 |
| **调用方式** | 只能调用 Layer 3 中标注了 capability 的能力：查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`。输入 `{capability, input, summary}`；`summary` 用一句话说明意图。**不得猜测或编造未登记的 capability** |
| **入参字段名** | 以契约参数表为准，**大小写敏感**；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工） |
| **身份与授权** | 身份由连接授权绑定；查询需 `mall.query`、写操作需 `mall.action` 授权，且受当前账号实时业务权限限制。不询问、不传入租户/账号/Token/服务名/路径/权限码；门店/等级等筛选值属于业务参数，必须来自用户提供或查询结果 |
| **ID 序列化** | 雪花 ID（19 位）一律**十进制字符串**，严禁传 Number（JS 精度上限 2^53-1）。响应中 ID 字段可能为 String（后端全局 Long→String） |
| **分页** | `pageSize ≤ 100`（**数据标签人群包例外**：`crowd.members` / `crowd.members-detail` 上限 200，超限回落 50）；**⚠️ 会员子域分页参数名不统一**：多数接口用 `pageNum/pageSize`（默认 10 或 20），**积分商品与兑换订单用 `pageNo/pageSize`**（默认 10）——严格按各契约参数表传值 |
| **响应信封** | 成功 `{capability, data, traceId}`，`data` 为上游**原始业务数据**（不裁剪字段）；错误 `{errorCode, message, retryable, traceId}` |
| **错误恢复** | `AUTH_REQUIRED`：请用户在 当前 Agent 重新连接；`SCOPE_INSUFFICIENT`：提示重新确认授权范围；`PERMISSION_DENIED`：停止该操作，不找替代方式绕过，**读取（detail/search/list）被拒时，同一对象的写操作也不得再尝试**（写前必须先读现态，读不到即不能写）；`INPUT_INVALID`：对照参数表修正（业务校验由服务端执行）；`UPSTREAM_ERROR/UPSTREAM_TIMEOUT`：查询可稍后重试或缩小条件；**写操作禁止立即同参重试**——先回读核对是否已生效，确认未生效且参数无误后至多重试一次，仍失败如实报告由用户决策（写 500 可能已生效，盲目重试有副作用）。失败不等于无数据 |
| **写操作语义** | `当前运行时的 Capability 写操作执行器` 为纯执行器：单次提交（永不自动重试）并原样返回上游业务结果。**先读现态、确认后执行、执行后回读** 的流程纪律由本 Skill 的 flows 定义，模型必须遵守。超时/网络错误时结果不确定——先查询对象状态再决定如何向用户说明，不盲目重复提交 |
| **需求超出契约** | 用户需求含参数表里没有的字段或能力（如积分活动起止时间、等级删除/排序、成长值手动调整、兑换订单取消）时，**先说明做不到什么**，给出替代方案并等用户确认，**不得先执行写入再说明**；追问选项里不要把写操作标为推荐项 |
| **用户已确认 ≠ 免读免回读** | 用户说「我确认执行/不需要再确认」只免去确认环节，**不免去写前读现态（detail/search）和写后回读**。删除、下架、批量操作、反馈处理同样适用 |
| **会员 ID 识别** | 用户说「会员 + 长数字」时，先把该数字当会员 `id` 直接调 `member.detail` 或各会员子查询；仅在返回「不存在」时才用 `uid`/`memberNo`/手机号经 `member.search` 反查，不要先 search 再 detail。只给短编号时按 member-profile.md 追问 |
| **太阳码（wx-share.qrcode）** | 当前未对 Agent 开放（调用会被确定性拒绝），不要调用；用户要太阳码时，说明请到管理后台「微信分享」生成并下载，或改用短链 / URL Link；契约保留在 `wx-share-action.md`（重新开放后按其「交付规则」执行） |
| **相对时间** | 「最近 N 天/上个月/今天」一律按**北京时间（UTC+8）**换算；当前时间取运行时提供的时间，必须用命令取时则用 `TZ=Asia/Shanghai date`，禁止直接使用 UTC 输出 |
| **写操作确认** | 只在用户明确要求执行对应操作时调用写能力。**「操作风险档位」表中所有 🔴 档（用户资产、全租户配置、商业影响、不可逆、批量写）执行前必须先向用户发起确认提问，复述对象、影响面与关键数值并取得确认**——用户下达的指令本身（如「把 V1 卡面图换成这张」「把规则改成……」）不等于确认；仅当用户在本轮明确说了「我确认执行 / 不需要再确认」才可跳过确认交互（仍需写前读现态、写后回读）。若当前执行器不具备所需确认交互，则停止写入并说明缺失条件 |
| **确认类提问的选项标签** | 向用户发起确认提问时，选项标签必须带具体动作，如「提交导入」「暂不导入」「确认切换范围」「保持全部商品」；**不要用「确认 / 取消 / 好的 / 可以 / 继续 / 同意 / 执行 / 开始 / 是的 / 没错 / ok」等泛化词**——后端会拒绝并在对话区显示报错，白白多耗一轮；写操作选项不要标为推荐项 |
| **金额** | decimal 传**数字**（如 `1.00`），单位元；禁止传分。积分/成长值为**整数** |
| **日期时间格式** | 各能力时间字段格式**不统一**，严格按参数表说明列传值。常见：`yyyy-MM-dd HH:mm:ss`（如 `2026-08-11 10:00:00`）、`yyyy-MM-dd`（生日/纯日期）、**ISO-8601 含 T**（如 `2026-10-01T00:00:00`，积分商品 validStart/EndTime、等级变更流水时间）。说明列未标注时默认 `yyyy-MM-dd HH:mm:ss` |
| **布尔值** | 传 `true`/`false`；禁止 `1`/`0`（除非参数表明确标注 Integer，如积分商城 enabled 0/1、等级 status 0/1） |
| **枚举大小写** | 严格按 Layer 1 枚举字典与 Layer 3 参数表取值（如 `MARKETING`/`INCREASE`/`GROWTH_ACCEL` 大写、`daily`/`purchase` 小写、状态类多数为**整数 code**），禁止猜测 |
| **脱敏字段** | 会员手机号/地址等由后端脱敏返回，不得尝试还原；**例外：`ops.member.member.batch-get-by-uids` 返回明文手机号**（见其契约），答复中必须自行脱敏为前 3 后 4 |
| **人群包异步任务** | 人群包圈选与成员计算为异步任务：提交后按流程文档轮询任务状态，未完成不得当作失败；动态人群包增员等写操作按契约纪律回读核验 |

### 操作风险档位（写操作前必读）

| 档位 | 操作 | 说明 |
|------|------|------|
| 🔴 用户资产（复述对象+数值后执行） | 积分调整（INCREASE/DECREASE）、黑名单加入/解除 | 影响单个会员资产与权益；数值必须用户给值，超时禁重试 |
| 🔴 全租户配置（复述影响面后执行） | 等级 CRUD/启停/降级规则、成长加速保存（revision）、**权益整体启停（GROWTH_ACCEL 关闭停算不追溯；UPGRADE_GIFT 仅展示口径）**、**自定义权益创建/编辑/排序**、**成长值任务保存（每单成长值决定升级速率）**、升级礼包保存、**升级礼包全局开关（发放门禁）**、积分活动创建/编辑/启停、积分抵扣保存、积分商城开关 | 影响全租户会员判定/权益/价格 |
| 🔴 商业影响（复述清单与数值后执行） | **积分商品创建/编辑（积分价、库存、可兑等级、有效期）**、**积分商品批量上下架**（批量改变 C 端兑换入口可见性） | 编辑仅改用户要求字段，其余以 detail 回读值原样回传（⚠️ 图片字段例外：detail 出参为时效签名 URL，回传须剥离 `?` 后参数，见 points-goods-action.md update 节） |
| 🔴 不可逆（确认完整对象清单） | 积分商品删除/批量删除、积分活动删除、**删除标签、删除标签分类、删除人群包、删除自定义权益** | 逻辑删除不可恢复 |
| 🟡 可逆写（做 + 向用户说明） | 会员创建/编辑、标签绑定/解绑（执行后必须回读核验）、积分商品单条上下架、兑换订单发货（不可逆但受状态机保护且限单订单——误发货需人工客服补救，无系统撤回）、反馈处理、客服开关、分享链接生成、**人群包上线/下线（按流程文档回读核验）**、**标签与分类维护、动态人群包批量加用户**、**自定义权益启停/图标上传、等级图片上传** | 需有明确用户操作意图 |
| 🔴 批量写（复述文件与预期量） | 会员导入（批量建会员，异步受理）、黑名单导入（同步，批量拉黑）、**人群包文件上传（CREATE 新建 / APPEND 追加）** | 复述文件名与预期数量；convertType 与用户确认；追加仅 DYNAMIC/FILE_UPLOAD 类型 |
| 🟢 含 PII 查询（只转告 URL/自行脱敏，不复述内容） | 会员导出（URL 型）、人群包成员明细/失败明细下载（URL 型）、会员详情 `rawPhone`/`batch-get-by-uids` 明文手机号 | 导出与下载内容含批量个人数据，后端已审计留痕；downloadUrl 均有时效 |

**字段确认红线（禁止 AI 编造）**：积分调整方向与数量、黑名单对象、物流单号、积分价格（redeemPoints/redeemAmount）、库存数量、成长倍率、**成长值数值（任务每单成长值、等级门槛）**、礼包积分与券数量、**积分发放率（pointsPerYuan）与抵扣汇率（minDeductUnit/exchangeAmount）**、积分商品可兑等级（allowedLevels）与有效期、**人群包圈选规则与目标标签清单**——必须由用户明确给出。

### 调用前完整性检查（强制）

1. 展开读取入参表的全部叶子字段；出现嵌套结构（如 items/levels/configs/tasks/coupons/products/规则项）继续读取其字段说明。
2. 区分必填、条件必填（如 redeemMode=2 时 redeemAmount、validType=2 时起止时间、SPECIFIED 时范围清单）与可选；满足当前枚举分支相关的条件。
3. 枚举使用 Layer 1 字典精确值并保持大小写；状态类字段确认是整数 code 还是字符串。
4. 确认分页参数名（pageNum vs **pageNo**）与金额、比例、时间的单位与 JSON 类型；ID 一律十进制字符串。
5. 确认对象当前状态（黑名单/启停/待发货/待处理/人群包任务态有状态前置，重复操作报错）。
6. 关联清单先删后插/全量替换的操作（积分活动的 items、成长加速保存、升级礼包保存、积分抵扣的 SPECIFIED 商品清单、自定义权益的 levelIds 与 sort 全集）必须先读现态回填全部清单——未包含的条目会被静默删除或丢失排序。

---

## 环境与执行边界

- 缺失字段不等于零、不等于不存在；会员优惠券为空可能是促销服务降级（空 ≠ 无券）。
- 手机号等脱敏字段由后端脱敏返回，不得尝试还原；用户主动提供完整手机号作为 search 查询条件属合法业务输入，答复中复述号码时自行脱敏（前 3 后 4）。
- 积分/成长值为整数资产，调整操作幂等性弱（超时可能重复加减）——超时后先查 `ops.member.member.points-flows` 确认是否已执行。
- 等级/权益/抵扣/积分活动等配置写影响全租户，执行前复述影响面；成长加速与升级礼包保存为全量替换语义，先读现配置。
- 分享链接有效期与配额受微信侧限制，失败时如实转达。
- 人群包圈选与成员计算为异步任务，任务未完成时不得把"暂无成员"当最终结果；规则圈选只接受 `tagId` 规则项，运算符取值先查 `operator` 契约。
