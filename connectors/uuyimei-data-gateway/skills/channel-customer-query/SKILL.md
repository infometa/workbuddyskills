---
name: channel-customer-query
description: 当用户询问渠道客户相关问题时使用——查客户档案明细、顾问名下客户、某渠道/地域/时间段的客户数量、客户建档信息、是否添加顾问企微、客户微信/企微聊天记录与对话统计、言迹录音文本（语音转写）、「到院/接诊」记录（姓名、接诊顾问、新老客、接诊年龄、是否二次、接待时间、医助描述、客户意向、未成交处理、科室、二级分诊、主诊医生；2026-09-20 裁剪，主诉/成交等字段已下线），「正式客户档案」（到院成交后客户：私域一二三级分类、用户组及别名、五科归属医生、会员卡类型、专家特助、渠道建档人、职业/体型/婚姻/生日），「客户RFM指标」（客户价值星级/总评分、首次消费/首次到院/最近到院、保留周期、消费次数、转介绍人数与金额、等级积分），以及「新客线索」（线索来源、一/二/三级渠道、姓名、电话、派单时间、线索备注）、「线索查询/线索提交记录」（转诊平台提交客户资料原始记录，含老客/新客/未建档，派单方式如巨量本地推/巨量飞鱼/小红书/美团等、咨询内容、处理状态）、「回访计划」记录（回访名称、上报时间、实际执行时间、任务等级、姓名、回访目的、拨打结果、回访方式、回访反馈；2026-09-20 裁剪，执行人/是否到场等跟踪字段已下线）、「客户投诉」（投诉类型/等级/日期/来源/描述/处理结果/状态/类别，正式+临时客户都支持）、「电话黑名单」（某号码是否在黑名单、拉黑原因/类别/时间，电话脱敏）、「客户需求」（一级/二级类别、主销售线索、解决/刚需状态、地区/时间/担心问题、解决人与周期）。数据经 crm-data-gateway MCP 工具查询，敏感字段自动脱敏，权限由服务端按岗位控制。
version: "1.11.0"
author: "CRM 数据网关"
display_name: "渠道客户信息查询"
display_name_en: "Channel Customer Query"
description_zh: "查询渠道客户档案、正式客户档案（私域分类/用户组/归属医生/会员卡/专家特助/渠道建档人）、客户RFM指标（价值星级/消费/转介绍/保留周期）、数量统计、企微聊天记录、到院/接诊记录、新客线索、线索提交记录（转诊平台提交客户资料）与回访计划（名称/时间/任务等级/目的/结果/方式/反馈）；支持按地域/顾问/渠道/时间/成交状态等维度过滤，敏感字段脱敏，权限服务端强制。"
description_en: "Query channel customer profiles, formal customer profiles (private-domain categories, user groups, section doctors, membership, expert assistant, channel builder), customer RFM metrics (value grade, spend, referrals, lifespan), counts, WeCom chat records, visit/reception records, revisit plans (name/times/grade/purpose/result/feedback, trimmed 2026-09-20), new-customer leads and lead submission records (referral-platform submitted customer data) via the crm-data-gateway MCP tools, with server-enforced permissions and field masking."
visibility: "public"
---

# 渠道客户信息查询

## 这个 Skill 做什么

通过 `crm-data-gateway` MCP 连接器查询「渠道客户」业务数据：客户档案明细、数量统计、企微聊天记录、**正式客户档案**（到院成交后客户：私域一二三级分类、用户组及别名、五科归属医生、会员卡类型、专家特助、渠道建档人）、**客户RFM指标**（客户价值星级/总评分、首次消费/首次到院/最近到院、保留周期、消费次数、转介绍人数与金额、等级积分）、**渠道客户到院/接诊记录**（接诊顾问、新老客、接待时间、医助描述、客户意向、未成交处理、科室、二级分诊、主诊医生等——2026-09-20 已裁剪为精简视角）、**新客线索**（线索来源、一/二/三级渠道、派单时间、备注——2026-09-20 已裁剪为精简档案视角）、**线索提交记录**（转诊平台提交客户资料原始记录，含老客/新客/未建档，即一般说的「线索查询」），以及**渠道客户回访计划**（回访名称/上报/实际执行时间、任务等级、目的、拨打结果、方式、反馈——2026-09-20 裁剪为精简视角）、**客户投诉**、**电话黑名单**与**客户需求**（类别/刚需/解决状态/解决周期）。

**一切查询都必须走 MCP 工具**，不要直连数据库、不要读本地文件、更不要用训练知识编造客户数据。

**核心原则**：权限、审计、脱敏都在网关服务端强制执行。你只需把自然语言正确翻译成工具调用；查不到或被拒就如实转述，绝不换字段绕过权限。

## 前置自检

- 不确定当前身份/权限时，先调 `get_my_profile`（岗位、权限点、数据范围）或 `list_available_datasets`（可查数据集与可过滤字段）。
- 用户问题超出「渠道客户」范围（如项目营收、成本、其他员工数据）时，本 skill 覆盖不到，直接说明。

## 工具速查

| 工具 | 数据桶 | 用途 |
|------|--------|------|
| `get_my_profile` | 登录即可 | 我是谁、数据桶、组织范围 |
| `list_available_datasets` | 登录即可 | 可查数据集与可过滤字段清单 |
| `query_channel_customers` | `company` | 渠道客户档案明细（列表，分页，字段脱敏） |
| `query_channel_customer_count` | `company` | 渠道客户数量统计（只返回 count） |
| `query_formal_customers` | `company` | 正式客户档案明细（到院成交后客户，列表，分页，姓名/电话脱敏） |
| `query_formal_customer_count` | `company` | 正式客户数量统计（按客户ID去重，只返回 count） |
| `query_customer_rfm` | `company` | 客户RFM指标明细（每客户一行的价值快照：星级/评分/消费/转介绍，姓名/电话脱敏） |
| `query_customer_rfm_count` | `company` | 客户RFM指标数量统计（按客户ID去重，只返回 count） |
| `query_channel_customer_chats` | `company` | 某客户的企微聊天记录 |
| `query_wechat_dialogue` | `company` | 微信对话（个人微信/云客：绑定 + 对话统计） |
| `query_wechat_dialogue_count` | `company` | 微信对话条数统计（只返回 count） |
| `query_wecom_dialogue` | `company` | 企微对话（企业微信：绑定 + 对话统计） |
| `query_wecom_dialogue_count` | `company` | 企微对话条数统计（只返回 count） |
| `query_yanji_asr` | `company` | 言迹录音文本（语音转写 ASR） |
| `query_yanji_asr_count` | `company` | 言迹录音条数统计（只返回 count） |
| `query_channel_customer_visit` | `company` | 到院/接诊明细（15 字段：顾问/新老客/时间/医助描述/意向/未成交处理/科室/分诊/医生，分页，姓名脱敏） |
| `query_channel_customer_visit_count` | `company` | 到院/接诊记录数量统计（只返回 count） |
| `query_channel_leads` | `company` | 新客线索明细（来源/一二级三级渠道/姓名/电话/派单时间/备注，列表，分页，字段脱敏） |
| `query_channel_lead_count` | `company` | 新客线索数量统计（只返回 count） |
| `query_lead_submit` | `company` | 线索提交记录明细（转诊平台提交客户资料，含老客/新客/未建档，字段脱敏） |
| `query_lead_submit_count` | `company` | 线索提交记录数量统计（只返回 count） |
| `query_complaints` | `company` | 客户投诉明细（类型/等级/日期/来源/描述/处理结果/状态/类别，正式+临时客户，按投诉日期倒序） |
| `query_complaint_count` | `company` | 客户投诉条数统计（只返回 count） |
| `query_blacklist` | `company` | 电话黑名单（电话🔒、拉黑类别/原因/时间） |
| `query_blacklist_count` | `company` | 黑名单记录数统计（只返回 count） |
| `query_customer_requests` | `company` | 客户需求明细（类别/主销售线索/解决/刚需状态/担心问题/解决人/周期，默认创建近30天） |
| `query_customer_request_count` | `company` | 客户需求条数统计（只返回 count） |
| `query_channel_customer_revisit` | `company` | 回访计划明细（名称/上报/实际执行时间/任务等级/目的/拨打结果/方式/反馈，列表，分页，姓名脱敏） |
| `query_channel_customer_revisit_count` | `company` | 回访计划数量统计（只返回 count） |
> **业绩数字化大盘全家（25 个工具：8 数据集 ×2 + 8 聚合 + 1 整屏打包）自 2026-09-20 起默认隐藏**，MCP 端不再暴露、
> 列表里看不到属正常。代码与配置保留，需要恢复时联系管理员在网关 `.env` 设 `EXPOSE_PERFORMANCE_TOOLS=true` 重启。
> 用户问业绩/员工/客户基础资料类问题时，如实告知该能力暂时关闭，**不要尝试调用这些工具名**。

参数：

- `query_channel_customers(filters, limit=100, offset=0)` — `filters` 是 `[{"field","op","value"}]` 数组；`limit` 单次最多 1000。
- `query_channel_customer_count(filters)` — `filters` 同上，只返回 `data.count`。
- `query_formal_customers(filters, limit=100, offset=0)` — 正式客户档案明细，`filters` 白名单见下「正式客户可过滤字段」；`limit` 单次最多 1000。
- `query_formal_customer_count(filters)` — 正式客户总数（按客户ID去重），只返回 `data.count`。
- `query_customer_rfm(filters, limit=100, offset=0)` — 客户RFM指标明细，`filters` 白名单见下「客户RFM指标可过滤字段」；`limit` 单次最多 1000。
- `query_customer_rfm_count(filters)` — RFM 客户总数（按客户ID去重），只返回 `data.count`。
- `query_channel_customer_chats(phone | temp_id, cus_type=2, begintime, endtime, limit=100)` — `phone` 与 `temp_id` 二选一；`cus_type` 2=临时客户（默认）、1=正式客户。
- `query_wechat_dialogue(filters, limit=100, offset=0)` — 微信对话（个人微信/云客）绑定与对话统计，`filters` 白名单见下「微信/企微对话可过滤字段」；`limit` 单次最多 1000。
- `query_wechat_dialogue_count(filters)` — 微信对话条数统计，只返回 `data.count`。
- `query_wecom_dialogue(filters, limit=100, offset=0)` — 企微对话（企业微信）绑定与对话统计，`filters` 同上。
- `query_wecom_dialogue_count(filters)` — 企微对话条数统计，只返回 `data.count`。
- `query_yanji_asr(filters, limit=100, offset=0)` — 言迹录音文本（语音转写 ASR），`filters` 白名单见下「微信/企微对话 · 言迹录音可过滤字段」；`limit` 单次最多 1000。
- `query_yanji_asr_count(filters)` — 言迹录音条数统计，只返回 `data.count`。
- `query_channel_customer_visit(filters, limit=100, offset=0)` — 到院/接诊明细，`filters` 白名单见下「到院/接诊可过滤字段」；`limit` 单次最多 1000。
- `query_channel_customer_visit_count(filters)` — 到院/接诊总数，只返回 `data.count`。
- `query_channel_leads(filters, limit=100, offset=0)` — 新客线索明细，`filters` 白名单见下「新客线索可过滤字段」；`limit` 单次最多 1000。
- `query_channel_lead_count(filters)` — 新客线索总数，只返回 `data.count`。
- `query_lead_submit(filters, limit=100, offset=0)` — 线索提交记录明细，`filters` 白名单见下「线索提交记录可过滤字段」；`limit` 单次最多 1000。
- `query_lead_submit_count(filters)` — 线索提交记录总数，只返回 `data.count`。
- `query_channel_customer_revisit(filters, limit=100, offset=0)` — 回访明细，`filters` 白名单见下「回访可过滤字段」；`limit` 单次最多 1000。
- `query_channel_customer_revisit_count(filters)` — 回访总数，只返回 `data.count`。
- `query_complaints(filters, limit=100, offset=0)` — 投诉明细，白名单见下「投诉/黑名单可过滤字段」；按投诉日期倒序。
- `query_complaint_count(filters)` — 投诉条数，只返回 `data.count`。
- `query_blacklist(filters, limit=100, offset=0)` — 电话黑名单明细；`query_blacklist_count(filters)` — 记录数。
- `query_customer_requests(filters, limit=100, offset=0)` — 客户需求明细，白名单见下「投诉/黑名单/需求可过滤字段」；默认创建近 30 天。
- `query_customer_request_count(filters)` — 客户需求条数，只返回 `data.count`。

## 可过滤字段（白名单，紧凑版）

`filters` 里 `field` 只能填以下 11 个之一（完整目录与字段含义见 `references/fields.md`；2026-09-18 字段裁剪后，录入员/跟进人/创建人/是否加顾问企微/渠道分类/深度平台/私域分类/美容院/职业/预估开发金额/会员卡类别等过滤项已移除）：

- 地域：`province` / `city` / `region`
- 归属人：`consultear`(顾问) / `useraccount`(工号)
- 客户：`name`(姓名)
- 渠道：`fchanneltwoname`(三级渠道名) / `ftype`(用户组)
- 其它：`cfintent`(意向度)
- 时间：`tempcomdate`(建档时间) / `fcreatetime1`(创建时间，仅过滤用、不返回)

`op` 支持：`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`(默认包含匹配 `%value%`)、`in`(传列表)、`is_null`(传 0/1)。

## 正式客户可过滤字段（白名单，紧凑版）

`query_formal_customers` / `query_formal_customer_count` 的 `filters` 里 `field` 只能填以下 23 个之一（完整目录见 `references/fields.md`「正式客户数据集」章节）：

- 关联键：`cusid`(客户ID) / `consultorid`(顾问ID) / `tempcusid`(临时客户ID)
- 客户：`cusname`(姓名，敏感) / `cfhandset`(电话，敏感) / `cussex`(性别) / `cusage`(年龄) / `birthday`(生日) / `fbodysize`(体型：直接传中文「偏胖/中等/偏瘦」，服务端解析 CRM 字典 1/2/3) / `ismarry`(婚姻)
- 地域：`provincename`(省份) / `city`(县市) / `regionname`(区域)
- 职业：`workname`
- 私域分类：`cusmanagelevel1name` / `cusmanagelevel2name` / `cusmanagelevel3name`(一/二/三级)
- 人员：`consultant`(顾问姓名) / `beauname`(专家特助) / `tempconsultor`(渠道建档人，即渠道时的渠道顾问)
- 分组：`ftypename`(用户组) / `fgroupname`(用户组别名)
- 会员：`cardtype`(会员卡类型，无卡返回'非会员')

**归属医生 `secdoc1-5`（整形/皮肤/口腔/无创/中医）随行返回、不可作过滤条件**（传入会 INVALID_PARAMS）；要按归属医生筛，先查列表再在结果里本地过滤。**无默认时间窗**（档案数据）。返回 28 个字段：3 个关联键原值 + 姓名/电话(SHA256 脱敏) + 23 个档案字段。

## 客户RFM指标可过滤字段（白名单，紧凑版）

`query_customer_rfm` / `query_customer_rfm_count` 的 `filters` 里 `field` 只能填以下 21 个之一（完整目录见 `references/fields.md`「客户RFM指标数据集」章节）：

- 关联键：`fcustid`(客户ID)
- 客户：`cfname`(姓名，敏感) / `cfhandset`(电话，敏感)
- 价值：`fcustoverallgrade`(价值星级 1-5) / `fcustoverallvalue`(价值总评分)
- 时间：`firstchargedate`(首次消费日) / `fqbillfirstdate`(首次到院) / `fqbilllastdate`(最近到院)
- 活跃：`fqbilllastdays`(距最近到院间隔天数) / `fqbilllastdaysvalue`(间隔分值 1-5) / `fqbilllastdaysstr`(最近到院标签，同间隔分值)
- 保留：`flifespan`(顾客保留周期，天) / `flifespanvalue`(保留周期分值 1-5) / `fqbillcnt`(总消费次数)
- 转介绍：`freferralnumber`(转介绍人数) / `freferralnumbervalue`(转介绍分值 1-5) / `freferralnumberstr`(转介绍积极度标签，同转介绍分值)
- 消费：`fmttlamt`(等级积分=累计消费金额) / `fmttlamtvalue`(总消费能力分值 1-5) / `fmttlamtstr`(总消费能力标签，同分值) / `freferralamt`(转介绍客户消费金额)

⚠️ 三个「标签/str」列（`fqbilllastdaysstr` / `freferralnumberstr` / `fmttlamtstr`）**就是对应分值列的别名，值是 1-5 的数字**，不是中文标签——别编造「积极/沉睡」之类的文字映射，直接把数字转述给用户即可。日期列传字符串（如 `"2026-01-01"`）会自动转日期绑定。**无默认时间窗**（快照数据）。返回 19 个字段：`fcustid` 原值 + 姓名/电话(SHA256 脱敏) + 16 个 RFM 指标。

## 到院/接诊可过滤字段（白名单，紧凑版）

`query_channel_customer_visit` / `query_channel_customer_visit_count` 的 `filters` 里 `field` 只能填以下 **15 个**之一（2026-09-20 字段裁剪 32→15，完整目录见 `references/fields.md`）：

- 时间：`cfreceptiontime`(接待时间)
- 关联键：`fid`(接诊ID) / `cusid`(正式客户ID) / `tempid`(临时客户ID)
- 客户：`cusname`(姓名，审计脱敏)
- 接诊属性：`fisnewcustomer`(新老客) / `fisrecsecond`(是否二次) / `cfsamplingtype`(接诊年龄) / `fsection`(科室，编码 1整形/2皮肤/3口腔/4无创/5中医) / `twoname`(二级分诊，like)
- 人员：`consultator`(接诊顾问) / `doctor`(主诊医生)
- 文本/计算：`fcuredesc`(医助描述，like) / `fintention`(客户意向) / `isdeal`(未成交处理，1=有登记 0=无)

`op` 语义与上节完全一致（`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`、`in`、`is_null`）。`fisnewcustomer` / `fisrecsecond` / `isdeal` 等标志位用字符串 `"1"` / `"0"` 比较。⚠️ 原「主诉/是否成交 ischarge/渠道/企微/会员/协诊开单导诊人员/首咨重咨/状态/分诊时间」等 17 个过滤项与 80 个返回字段已下线，传入会 INVALID_PARAMS；`fsection` 是编码列，按编码过滤、原样转述（别编科室名）。**返回 15 个字段**：3 关联键原值 + 姓名(SHA256) + 11 个业务字段。**无渠道豁免**：不传时间一律自动限定接待时间近 30 天。

## 新客线索可过滤字段（白名单，紧凑版）

`query_channel_leads` / `query_channel_lead_count` 的 `filters` 里 `field` 只能填以下 **8 个**之一（2026-09-20 字段裁剪，完整目录见 `references/fields.md`）：

- 时间：`fsubmittimestr`(派单时间)
- 渠道：`fchannelname`(三级渠道名) / `fchannel1name`(一级渠道名) / `fchannel2name`(二级渠道名)
- 客户：`fcusname`(姓名，审计脱敏) / `fmobile`(电话，审计脱敏)
- 线索：`submittype`(线索来源，`'1'`=API/二维码合并值、`'3'`=CRM 等)
- 关联键：`ftempcusid`(渠道客户ID，原值)

`op` 语义与上节一致。**返回 10 个字段**：`fid`(线索ID)/`ftempcusid`(渠道客户ID) + `submittype`(来源) + 一/二/三级渠道中文名 + `fcusname`/`fmobile`(SHA256) + `fsubmittimestr`(派单时间) + `fremark`(线索备注)。原「是否来院/处理状态/线索等级/分值/分诊/人员/地域/企微/产品」等跟踪字段已下线——需要它们请改用 `query_lead_submit`（全类型提交记录，含处理状态/派单方式等更全字段）。

## 线索提交记录可过滤字段（白名单，紧凑版）

`query_lead_submit` / `query_lead_submit_count` 的 `filters` 里 `field` 只能填以下 32 个之一（完整目录见 `references/fields.md`）：

- 时间：`fcreatetimestr`(创建/提交时间) / `fsubmittimestr`(派单时间) / `fallocatetimestr`(分诊时间) / `fdepthtimestr`(深度标记时间)
- 渠道：`fchannelname`(转诊三级渠道名) / `fchannel1name`(一级) / `fchannel2name`(二级) / `fchannel`(三级渠道ID)
- 客户：`fcusname`(姓名，审计脱敏) / `fmobile`(手机号，审计脱敏) / `fmoble2`(辅助号码，审计脱敏) / `fgender`(性别) / `fage`(年龄) / `funitname`(单位名称)
- 线索：`ftype`(1老客 2新客 3未建档) / `fstatue`(1未处理 2已处理) / `submittype`(派单方式：1API 2二维码 3CRM 4巨量本地推 5巨量飞鱼 6小红书私信 7云晰 8小红书小程序 9商城小程序 10优居营客 11快商通 12美团) / `fdepth`(是否深度，1是0否)
- ID：`fcusid`(正式客户) / `ftempcusid`(临时客户) / `fthirdpartycusid`(第三方客户) / `fsourceid`(源ID，巨量有值) / `org_id`(医院组织)
- 人员：`fassignpername`(派单人) / `fallocatepername`(分诊人) / `ffollowername`(跟进人) / `fdepthusername`(深度标记人) / `fcreateperson`(第三方派单人)
- 地域：`provincename`(省) / `cityname`(城市/地址)
- 产品：`pty1name`(分诊产品一级) / `pty2name`(分诊产品二级)

`op` 语义与上节一致。枚举/标志位字段（`ftype`/`fstatue`/`submittype`/`fdepth`）用字符串比较（如 `"1"`）。

## 回访可过滤字段（白名单，紧凑版）

`query_channel_customer_revisit` / `query_channel_customer_revisit_count` 查**回访计划**，`filters` 里 `field` 只能填以下 **12 个**之一（2026-09-20 字段裁剪，完整目录见 `references/fields.md`）：

- 时间：`revisittime`(实际执行时间) / `createtime`(上报时间)
- 任务：`fretvname`(回访名称，like) / `jobgrade`(任务等级 1-5) / `purpose`(回访目的，like) / `doresult`(拨打结果) / `frevisitway`(回访方式) / `ffeedbackname`(回访反馈，like)
- 客户：`cusname`(姓名，审计脱敏)
- 关联键：`fid`(回访记录ID) / `tempcusid`(渠道客户ID，→渠道客户档案/聊天记录) / `cusid`(同 tempcusid)

`op` 语义与上节一致。⚠️ 三点注意：①原「执行人/执行部门/是否到场/是否有效/回访状态/渠道」等**跟踪字段已下线**，传入会 INVALID_PARAMS——「某人回访了多少次」类问题不再支持，如实告知；②`doresult`(1-6)/`frevisitway`(1-8) 是编码列，文字字典不在库，**按编码原样返回，别编造「有效/无人接听」之类的标签**；③无渠道豁免，不传时间一律自动限定实际执行时间近 30 天。返回 12 个字段：3 关联键原值 + `fretvname`/`createtime`(上报)/`revisittime`(实际执行)/`jobgrade`/`purpose`/`doresult`/`frevisitway`/`ffeedbackname` + `cusname`(SHA256)。

## 微信/企微对话 · 言迹录音可过滤字段（白名单）

`query_wechat_dialogue` / `_count`、`query_wecom_dialogue` / `_count` 与 `query_yanji_asr` / `_count` 的 `filters` 里 `field` 只能填以下 3 个之一：

- `phone`(手机号，精确匹配)
- `cus_id`(正式客户 ID)
- `name`(客户姓名，支持 like 模糊匹配)

`op` 语义与其它数据集一致（`=`、`!=`、`>`、`<`、`>=`、`<=`、`like`、`in`、`is_null`）。`phone`/`cus_id` 建议用 `=`，`name` 用 `like`。**无默认时间过滤**（仅按租户/组织范围兜底）；计数按绑定条数 `COUNT(*)`。

## 投诉/黑名单/需求可过滤字段（白名单，紧凑版）

**客户投诉** `query_complaints` / `query_complaint_count`（15 个过滤字段；2026-09-20 底表已授权、全量实测通过，人口=挂正式/临时档案的 15,914 条）：

- 关联键：`fid`(投诉ID) / `fcusid`(正式客户) / `ftempcusid`(渠道客户) / `fcustype`(1=已注册 2=渠道临时)
- 客户：`fcusname`(姓名，敏感) / `fcftelephone`(电话，敏感)
- 投诉：`ftypename`(投诉类型，like) / `flevelname`(等级) / `fcomplainttime`(投诉日期，范围) / `fcometype`(来源，编码) / `fdescription`(描述，like) / `fstatus`(状态 1=处理中 2=已关闭) / `fcategory`(投诉类别)
- 处理：`fresults`(处理结果，like)

**电话黑名单** `query_blacklist` / `query_blacklist_count`（5 个过滤字段）：

- `fid` / `ftelphone`(电话：**过滤传明文精确值**，返回值是 SHA256 无法回推；row_count>0 即「在黑名单」) / `fblacktype`(类别编码 1-4) / `fremark`(拉黑原因，like) / `fcreatetime`(拉黑时间，范围)

**客户需求** `query_customer_requests` / `query_customer_request_count`（14 个过滤字段；一客户多需求，服务端固定剔软删，**默认创建时间近 30 天**，显式传 `faddtime`/`fresolvetime` 可豁免）：

- 关联键：`fid`(需求ID) / `cfcusid`(正式客户) / `ftempcusid`(渠道客户)
- 类别：`firsttypename`(一级类别,like) / `secondtypename`(二级类别,like)
- 状态：`fisprimary`(主销售线索 '1'=主需求) / `cfflag`(解决状态 0未解决/1解决) / `cfrequeststate`(刚需 0非/1是)
- 问题：`cfcityquestion`(地区 1本市/2本省/3外省) / `cftimequestion`(时间 1都有/2周内无/3其它)
- 时间/人员/周期：`faddtime`(创建,范围) / `fresolvetime`(解决,范围) / `resolvername`(解决人,like) / `resolvedays`(解决周期天，数值比较如 {"op":">","value":30})

编码列含义即上面括号内枚举；担心问题 `cfworryquestion1/2`（枚举 0-4）仅随行返回，字典在 CRM 配置、别编含义。类别名源值可能带首尾空格，like 用短词更稳。

⚠️ 通用纪律：`fcometype`/`fstatus`/`fblacktype` 是编码列（文字字典在 CRM 应用层），按编码原样转述、别编造含义；`fremark`/`fdescription`/`fresults` 自由文本可能内嵌姓名电话——**转述只概括原因，禁止复述身份信息**。投诉/黑名单无默认时间窗，需求默认创建近 30 天。

## 核心规则（必须遵守）

1. **数数量用 count，不要用列表数**：问「多少个/多少条」→ `query_channel_customer_count`。列表接口的 `meta.row_count` 受 `limit` 封顶会失真。
2. **查聊天先拿 fid**：先 `query_channel_customers(filters=[{"field":"name","op":"like","value":"<客户名>"}])` 拿 `fid`，再 `query_channel_customer_chats(temp_id=<fid>)`；无需明文手机号。
3. **默认时间限制**：`query_channel_customers` / `count` 在用户没给时间、也没按单渠道限定时，会自动加「建档近 30 天」。返回的 `meta.default_time_filter_applied` 会标注是否命中。
4. **按天过滤写法**：表达「某一天」用 `tempcomdate >= 当天 00:00:00` 且 `< 次日 00:00:00`。
5. **脱敏**：姓名/手机号返回 SHA256 脱敏值；`fid` 是内部关联键、按原值返回。不要承诺返回明文手机号/姓名。
6. **权限被拒**：返回 `PERMISSION_DENIED` 时，按 error 里的 `missing_bucket` / `hint` 转告用户「请联系管理员开通该数据桶」，不要试图换字段绕过。
7. **查不到聊天是常见情况**：大概率是①该客户未加顾问企微，②所属组织未接入聊天系统（聊天接口 HTTP 400）。工具会在 `data.note` 给提示，如实转述，不要静默说「无数据」。
8. **到院/接诊数数量用 visit_count**：问「某顾问/医生/科室/时间段接待了多少条到院」→ `query_channel_customer_visit_count`，不要用列表工具数。计数按接诊 ID 去重（`COUNT(DISTINCT fid)`），比列表 `row_count` 准确。⚠️ 2026-09-20 裁剪后不支持按渠道/主诉/成交统计，如实告知。
9. **到院/接诊默认时间限制**：`query_channel_customer_visit` / `_count` 在用户没给时间时，自动加「接待时间近 30 天」（渠道豁免已随渠道字段下线）。返回的 `meta.default_time_filter_applied` 标注是否命中。
10. **新客线索数数量用 lead_count**：问「某渠道/顾问/时间段有多少条新客线索」→ `query_channel_lead_count`，不要用列表工具数。计数按线索 ID 去重（`COUNT(DISTINCT fid)`）。
11. **新客线索默认时间限制**：`query_channel_leads` / `_count` 在用户没给时间、也没按渠道（`fchannelname`/`fchannel1name`/`fchannel2name` 任一）限定时，自动加「派单时间近 30 天」。返回的 `meta.default_time_filter_applied` 标注是否命中。
12. **回访数数量用 revisit_count**：问「某时间段/某目的/某任务等级有多少条回访计划」→ `query_channel_customer_revisit_count`，不要用列表工具数。计数按回访记录 ID 去重（`COUNT(DISTINCT fid)`）。⚠️ 2026-09-20 裁剪后**不支持**按执行人/部门/是否有效等跟踪维度统计，如实告知。
13. **回访默认时间限制**：`query_channel_customer_revisit` / `_count` 在用户没给时间时，自动加「实际执行时间（revisittime）近 30 天」（无渠道豁免）。返回的 `meta.default_time_filter_applied` 标注是否命中。
14. **微信/企微对话统计按手机号/客户ID/姓名直查**：`query_wechat_dialogue`（个人微信/云客）与 `query_wecom_dialogue`（企业微信）直接按 `phone`/`cus_id`/`name` 过滤，返回「绑定 + 员工/客户对话数 + 最后对话时间」，无需先拿 fid。这是**对话统计**（对话数/时间），不是聊天内容；要查聊天内容仍走 `query_channel_customer_chats`。
15. **言迹录音文本按手机号/客户ID/姓名直查**：`query_yanji_asr` 返回「录音文本 ftext + 员工 + 时长 + 创建时间 + 接诊ID」，`ftext` 是整段语音转写文本（可能几十到上千字）。同样直接按 `phone`/`cus_id`/`name` 过滤，无需先拿 fid。
16. **线索提交记录数数量用 lead_submit_count**：问「某渠道/派单方式/时间段提交了多少条线索」→ `query_lead_submit_count`，不要用列表工具数。计数按线索记录 ID 去重（`COUNT(DISTINCT fid)`）。
17. **线索提交记录默认时间限制**：`query_lead_submit` / `_count` 在用户没给时间、也没按具体渠道（`fchannelname`）限定时，自动加「创建时间近 30 天」。返回的 `meta.default_time_filter_applied` 标注是否命中。
18. **两个「线索」工具的分工**：问「线索查询/提交记录/派单方式来源（巨量/飞鱼/小红书/美团等）/老客线索/咨询内容/未处理线索/处理状态」→ `query_lead_submit`（全类型原始提交记录，字段更全）；问「新客线索 来源/渠道（一二三级）/派单时间/备注」→ `query_channel_leads`（限新客/未建档，2026-09-20 裁剪后只返回精简档案视角，**不含**是否来院/加企微/线索等级等跟踪指标——别再承诺这些）。拿不准就按用户原话里的关键词选，或两个都查后合并说明。
19. **渠道客户 vs 正式客户的分工**：问「渠道客户/临时客户/建档/意向度/回访/渠道来源」→ `query_channel_customers`（到院前临时档案）；问「正式客户/成交客户/私域分类/用户组别名/归属医生/会员卡类型/专家特助/渠道建档人」→ `query_formal_customers`（到院成交后档案）。正式客户数量用 `query_formal_customer_count`（按客户ID去重）。
20. **正式客户归属医生只能本地过滤**：`secdoc1-5`（整形/皮肤/口腔/无创/中医归属医生）随行返回但不在过滤白名单里；用户要「某医生名下的正式客户」时，用其它可过滤字段收敛后在结果里按 secdoc 列本地筛选，并把该限制如实告知。
21. **正式客户链路键**：`cusid`(原值) → 微信/企微对话 `cus_id`、业绩大盘 `customer_id`；`tempcusid`(原值) → 聊天记录 `temp_id`；`consultorid`(原值) → 业绩大盘 `rec_consultant_id`。`cfhandset` 已脱敏，对话工具的 `phone` 过滤需明文，链路请改用 `cus_id`/`temp_id`。正式客户 count 用非选择性前导通配 like（如 `fgroupname like '%组%'`）会很慢，计数尽量用等值或 `in` 精确过滤。
22. **RFM vs 正式客户的分工**：问「档案属性」（私域分类/用户组/归属医生/会员卡/专家特助/渠道建档人）→ `query_formal_customers`；问「消费行为/价值指标」（价值星级/评分、最近到院距今、保留周期、消费次数、转介绍人数/金额、等级积分）→ `query_customer_rfm`。RFM 每客户一行，计数用 `query_customer_rfm_count`（按客户ID去重）。链路键 `fcustid`(原值) = 正式客户 `cusid` = 对话 `cus_id` = 业绩大盘 `customer_id`。三个「标签/str」列是分值(1-5)的数字别名，转述时别编文字标签。
23. **投诉与黑名单**：问「客户投诉过吗/投诉处理情况」→ `query_complaints`（正式+临时客户都支持，`fcustype` 区分）；问「某号码是否被拉黑/拉黑原因」→ `query_blacklist`（电话过滤传明文，返回哈希）。投诉来源 fcometype（0=院内/3=平台）与状态 fstatus 是编码列，按编码转述别编含义；无档案关联的投诉（约 1,300 条）不在接口人口内。自由文本备注可能内嵌身份信息，转述只概括、不复述。
24. **客户需求**：问「客户的需求/刚需/未解决/解决周期/主销售线索」→ `query_customer_requests`（计数用 `_count`）。编码列按白名单注释里的枚举转述；「担心问题」暂只有 0-4 编码值。大表默认限创建近 30 天，问「全部/历史所有需求」时显式传宽松的 `faddtime >=` 范围豁免。

## 常见问题 → 工具调用

| 用户说 | 调用 |
|--------|------|
| 「查石家庄市的渠道客户」 | `query_channel_customers(filters=[{"field":"city","op":"=","value":"石家庄市"}])` |
| 「看顾问张三名下的客户」 | `query_channel_customers(filters=[{"field":"consultear","op":"=","value":"张三"}])` |
| 「陈姣姣 8 月 20 号有多少个客户」 | `query_channel_customer_count(filters=[{"field":"consultear","op":"=","value":"陈姣姣"},{"field":"tempcomdate","op":">=","value":"2026-08-20 00:00:00"},{"field":"tempcomdate","op":"<","value":"2026-08-21 00:00:00"}])` |
| 「最近 30 天建档的客户」 | 不传 filters（自动注入近 30 天） |
| 「百度渠道来的客户」 | `query_channel_customers(filters=[{"field":"fchanneltwoname","op":"like","value":"百度"}])` |
| 「查 13800000000 的聊天记录」 | `query_channel_customer_chats(phone="13800000000")` |
| 「这个客户的聊天记录」（已有 fid） | `query_channel_customer_chats(temp_id="<fid>")` |
| 「查 13812345678 的企微对话」 | `query_wecom_dialogue(filters=[{"field":"phone","op":"=","value":"13812345678"}])` |
| 「查客户张三的微信对话」 | `query_wechat_dialogue(filters=[{"field":"name","op":"like","value":"张三"}])` |
| 「客户 cus_001 企微聊了多少句」 | `query_wecom_dialogue(filters=[{"field":"cus_id","op":"=","value":"cus_001"}])`（看 `fuserchats`/`fcustomerchats`） |
| 「查客户张三的言迹录音」 | `query_yanji_asr(filters=[{"field":"name","op":"like","value":"张三"}])` |
| 「美团渠道来的渠道客户」 | `query_channel_customers(filters=[{"field":"fchanneltwoname","op":"like","value":"美团"}])` |
| 「查顾问陈姣姣名下的正式客户档案」 | `query_formal_customers(filters=[{"field":"consultant","op":"=","value":"陈姣姣"}])` |
| 「现场顾问用户组有多少个正式客户」 | `query_formal_customer_count(filters=[{"field":"fgroupname","op":"=","value":"现场顾问"}])`（计数用等值，别用 like '%…%'） |
| 「拿了银卡的正式客户」 | `query_formal_customers(filters=[{"field":"cardtype","op":"=","value":"银卡"}])`（无卡客户 cardtype='非会员'） |
| 「私域一级分类是XX的正式客户」 | `query_formal_customers(filters=[{"field":"cusmanagelevel1name","op":"=","value":"XX"}])` |
| 「皮肤归属医生是罗玉燕的正式客户」 | `query_formal_customers` 按可过滤字段收敛后，在结果里按 `secdoc2` 本地过滤（归属医生列不可 SQL 过滤，如实告知用户） |
| 「5星价值客户有多少个」 | `query_customer_rfm_count(filters=[{"field":"fcustoverallgrade","op":"=","value":"5"}])` |
| 「转介绍过3人以上的客户」 | `query_customer_rfm(filters=[{"field":"freferralnumber","op":">=","value":3}])` |
| 「最近90天没到院的高价值客户」 | `query_customer_rfm(filters=[{"field":"fqbilllastdays","op":">=","value":90},{"field":"fcustoverallgrade","op":">=","value":"4"}])` |
| 「陈姣姣本月接诊了多少个到院客户」 | `query_channel_customer_visit_count(filters=[{"field":"consultator","op":"=","value":"陈姣姣"}])` |
| 「查最近成交的新客」 | ⚠️ ischarge(成交)已随 2026-09-20 裁剪下线；改用 `isdeal`(未成交处理)`op="="value="1"`+`fisnewcustomer` 近似，如实说明 |
| 「主诉是隆鼻的到院记录」 | ⚠️ 主诉字段已下线；改按 `fcuredesc`(医助描述) like 查询，如实说明限制 |
| 「8 月 20 号到院的客户」 | `query_channel_customer_visit_count(filters=[{"field":"cfreceptiontime","op":">=","value":"2026-08-20 00:00:00"},{"field":"cfreceptiontime","op":"<","value":"2026-08-21 00:00:00"}])` |
| 「百度渠道到院的客户」 | ⚠️ 渠道字段已下线；渠道来源类问题改用 `query_channel_customers`(三级渠道可过滤) 或 `query_channel_leads`，如实说明 |
| 「百度渠道来的新客线索」 | `query_channel_leads(filters=[{"field":"fchannelname","op":"like","value":"百度"}])` |
| 「本月新客线索有多少条」 | `query_channel_lead_count()`（自动限定派单近 30 天） |
| 「还没来院的新客线索」 | ⚠️ 跟踪字段已裁剪下线，改用 `query_lead_submit`（处理状态/全类型），如实告知用户 `query_channel_leads` 不再返回是否来院 |
| 「转诊平台渠道的新客线索」 | `query_channel_leads(filters=[{"field":"fchannel1name","op":"=","value":"转诊平台"}])` |
| 「8 月 20 号派单的新客线索」 | `query_channel_lead_count(filters=[{"field":"fsubmittimestr","op":">=","value":"2026-08-20 00:00:00"},{"field":"fsubmittimestr","op":"<","value":"2026-08-21 00:00:00"}])` |
| 「查巨量飞鱼的线索提交记录」 | `query_lead_submit(filters=[{"field":"submittype","op":"=","value":"5"}])`（4=巨量本地推 5=巨量飞鱼 6=小红书私信 12=美团） |
| 「本月提交了多少条线索」 | `query_lead_submit_count()`（自动限定创建近 30 天） |
| 「还没处理的线索」 | `query_lead_submit(filters=[{"field":"fstatue","op":"=","value":"1"}])` |
| 「老客线索提交记录」 | `query_lead_submit(filters=[{"field":"ftype","op":"=","value":"1"}])`（新客线索精简档案视角用 `query_channel_leads`） |
| 「查 13800000000 提交的线索」 | `query_lead_submit(filters=[{"field":"fmobile","op":"=","value":"13800000000"}])`（返回姓名/手机号为脱敏值） |
| 「陈姣姣本月回访了多少次」 | ⚠️ 跟踪字段已裁剪下线（2026-09-20），不再支持按执行人统计，如实告知并可改问「本月有多少条回访」`query_channel_customer_revisit_count()` |
| 「最近回访无效的」 | ⚠️ 是否有效/到场跟踪字段已下线；可改按 `ffeedbackname`(回访反馈) like 关键词查询，如实说明限制 |
| 「回访目的是术后关怀的」 | `query_channel_customer_revisit(filters=[{"field":"purpose","op":"like","value":"术后"}])` |
| 「任务等级3以上的回访计划」 | `query_channel_customer_revisit_count(filters=[{"field":"jobgrade","op":">=","value":"3"}])` |
| 「13800000000 是否在黑名单」 | `query_blacklist(filters=[{"field":"ftelphone","op":"=","value":"13800000000"}])`（row_count>0 即在名单内） |
| 「最近被拉黑的号码」 | `query_blacklist(filters=[{"field":"fcreatetime","op":">=","value":"2026-09-01"}])` |
| 「未解决的刚需有多少条」 | `query_customer_request_count(filters=[{"field":"cfrequeststate","op":"=","value":"1"},{"field":"cfflag","op":"=","value":"0"}])`（默认限创建近 30 天） |
| 「这个客户的需求都解决了吗」 | `query_customer_requests(filters=[{"field":"cfcusid","op":"=","value":"<客户ID>"}])` |
| 「这个客户有哪些投诉」 | `query_complaints(filters=[{"field":"fcusid","op":"=","value":"<客户ID>"}])`；按临时客户查用 `ftempcusid` |
| 「本月全院预收业绩总额」 | ⚠️ 业绩大盘工具已默认隐藏（2026-09-20），如实告知暂不提供业绩查询 |
| 「查员工李四的信息」 | ⚠️ 同上，员工/客户/会员基础资料工具已随业绩大盘一起隐藏 |

## 业绩数字化大盘（已默认隐藏，2026-09-20）

业绩大盘全家（8 个数据集 ×2 + 8 个聚合汇总 + 1 个整屏打包，共 25 个工具）按需求**默认不再暴露**：MCP 端 `list_tools` 与 `list_available_datasets` 均看不到，属预期行为，不要重试或变通。网关代码、XML、权限桶全部保留；恢复方式为网关 `.env` 设 `EXPOSE_PERFORMANCE_TOOLS=true` 重启（详见仓库 README「业绩数字化大盘」一节）。用户问到业绩/员工资料时，回复「该能力暂时关闭，如需恢复请联系管理员」。

## 错误码

`AUTH_FAILED`（apiKey 无效/过期）、`PERMISSION_DENIED`（缺数据桶，按 hint 申请）、`INVALID_PARAMS`（字段/操作符/值不合法）、`QUERY_FAILED`（查询失败，请重试或收敛条件）。

错误信封形如 `{"success":false,"error":{"code":"PERMISSION_DENIED","message":"...","missing_bucket":"company","hint":"请联系管理员在 CRM 中为该账号开通对应数据桶权限"}}`。

## 字段与过滤白名单

完整字段目录（24 个返回字段，含脱敏标注）与 11 个过滤字段的详细含义见 `references/fields.md`；正式客户数据集的字段目录（28 个返回字段、23 个过滤字段）见同文件「正式客户数据集」章节；客户RFM指标数据集的字段目录（19 个返回字段、21 个过滤字段）见同文件「客户RFM指标数据集」章节；到院/接诊数据集的字段目录（2026-09-20 裁剪后 15 个返回字段、15 个过滤字段）、新客线索数据集的字段目录（2026-09-20 裁剪后 10 个返回字段、8 个过滤字段）、线索提交记录数据集的字段目录（37 个返回字段、32 个过滤字段）与回访数据集的字段目录（2026-09-20 裁剪后 12 个返回字段、12 个过滤字段）见同文件对应章节；投诉数据集（15 个返回字段、15 个过滤字段，2026-09-20 已授权实测）与电话黑名单数据集（5 个返回字段、5 个过滤字段）、客户需求数据集（16 个返回字段、14 个过滤字段，2026-09-21 新增）的字段目录见同文件「客户投诉数据集」「电话黑名单数据集」「客户需求数据集」章节。微信/企微对话数据集（微信 5 个返回字段、企微 8 个返回字段，各 3 个过滤字段）与言迹录音文本数据集（7 个返回字段、3 个过滤字段）见同文件「微信 / 企微对话数据集」与「言迹录音文本数据集」章节。渠道客户档案裁剪后一/二/三级渠道只返回服务端解析出的中文名（`bulidtypename`/`fchannelonename`/`fchanneltwoname`），代码列不再返回；一/二级渠道名仅随行返回、不可过滤，三级渠道名可过滤。到院/接诊数据集 2026-09-20 起已无渠道列；新客线索/线索提交等数据集按各自章节为准。
