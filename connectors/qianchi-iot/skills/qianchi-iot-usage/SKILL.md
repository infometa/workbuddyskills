---
name: qianchi-iot-usage
description: 指导 AI 正确调用千尺物联连接器的 35 个工具（30 个只读 + 5 个写/危险），查询水卡、设备、订单流水、故障知识库与经营报表，并安全执行开卡、充值、扣款、挂失、设备参数下发。包含分页与数据范围口径、日期语义三分类、排序白名单、工具依赖链、大结果集处理、写操作确认规则和异常恢复方式。当用户询问水卡余额、消费/充值记录、设备状态与故障码、退款、扣款、下级经销商、经营报表或统计趋势，或要求开卡/充值/扣款/挂失/改设备参数时使用。
---

# 千尺物联连接器使用指南

## 一、能力边界与风险分级

本连接器共 **35 个工具：30 个只读（`read`）+ 5 个写/危险**。

| 等级 | 工具 | 行为要求 |
|---|---|---|
| `read`（30 个） | 其余全部查询工具 | 直接调用，无需确认 |
| `write`（1 个） | `update_card_use_status`（挂失/恢复卡） | **必须先取得用户明确同意** |
| `dangerous`（4 个） | `create_card`（开卡）、`recharge_card`（充值）、`draw_money`（扣款）、`save_equipment_params`（设备参数下发） | **必须先取得用户明确同意**，并复述金额/对象 |

写操作确认规则见 §六，务必遵守。

> 只读工具里唯一的例外说明：`search_device_faq` 会给知识库条目累加命中次数（`HitCount`），那是语料统计副作用，不进卡表/订单表/设备表，**按 `read` 处理、不需要确认**。

如果用户要的是连接器**没有**的能力（删卡、改密码、改价目表、导出文件等），明确告知不具备，不要用查询工具变通实现。

## 二、认证与前置条件

- 连接时用户需填写 **Token 秘钥**（见 `token-schema.json` 表单，字段键 `SERVICE_TOKEN`）。
- 所有工具调用都以该账号的身份与数据权限执行，**返回范围受账号自身权限限制**（层级越界查不到数据是正常现象，不是接口坏了）。
- 鉴权失败时不要反复重试：说明 Token 可能已失效（例如后台密码修改后需重新生成），引导用户在连接器设置里更新 Token 后重连。

## 三、通用约定（务必遵守）

### 1. 分页与「总数」：`page` + `size`，总数看 `count`

- `page` 从 **1** 开始，`size` 默认 **20**。
- 成功返回体结构：
  ```json
  { "success": true, "count": 128, "data": [ ... ] }
  ```
  - **`count` 是符合条件的总条数**，不是本页条数；
  - **`data` 只是当前页的数组**（某些工具还会附带额外字段，如 `create_card` 的 `appliedDefaultEndDate`、`search_device_faq` 未命中时的 `note`，要读出来转告用户）。

> ⚠️ **最容易出错的点**：绝不能把 `data.length` 当作总数回答用户。用户问「一共有多少张卡」时必须读 `count`。反之，`data.length` 恰好等于 `size` 说明还有下一页。

### 2. 大结果集处理

- `size` **不要超过 50**。单条会员卡记录有 50 多个字段，`size=100` 时返回体可达 100KB+，过大的返回体会被宿主截断并落盘。
- 要「有多少条」：取 `size=1` 读 `count` 即可。
- 要全量明细：缩小 `size` 并逐页 `page` 循环处理。
- `get_equipment_params` 的 `size` 由网关固定为 50，需用 `page` 翻页取全。

### 3. 数据范围：`scope` 一律默认 `1`

带 `scope` 的工具（订单类全部、`get_equipment_list`、`get_warn_status`、`get_company_childs`、`get_equipment_consume_report` 之外的层级类），语义统一为：

| 值 | 含义 |
|---|---|
| `1`（**所有工具的默认值**） | 只含**直接挂在自己名下**的数据（直属） |
| `0` | 含下级经销商整棵子树（即隔了一层的下级） |

> ⚠️ **不要主动传 `0`**：Level1 账号传 0 会把二级经销商名下的单/设备一起算进来，属越级取数，业务上不允许。只有用户明确说「连下级的下级一起看」时才传 0。
> Level3/4/5 账号传 1 与 0 结果相同（其下已无经销商层）。
> 回答时**必须说明口径**（是否含下级），否则用户会把数字理解错。

`get_company_childs` 另有一处后端特例：当前账号是 Level3 时后端会忽略 `scope`，总是返回直属两层。

### 4. 日期与金额

- 日期参数格式 `yyyy-MM-dd`（统计类还可能是 `yyyy-MM` / `yyyy`，见下）。用户说「上个月」「最近 7 天」时，先换算成具体日期区间再传参。
- 金额为数字、单位**元**，展示加 `¥`。充值/扣款金额**最多两位小数**（后端最小单位是分），超过会被拒。
- 时间戳为 ISO 8601 带时区（如 `2026-09-19T17:11:56.487+08:00`）。
- **`0001-01-01T08:00:00+08:00` 表示该字段未设置**（常见于未绑定的卡），不要当「公元 1 年」解读或展示。

⚠️ **上界日期语义按接口分三类，不要统一处理**：

| 类别 | 接口 | 上界语义 | 实操口径 |
|---|---|---|---|
| **订单类**（右开） | `get_water_order`、`get_recharge_order`、`get_draw_money_order` 及三个 `*_history` | `支付时间 < endDate` | **要查到今天，`endDate` 必须填「明天」** |
| **卡/设备/退款类**（闭区间，网关已补 23:59:59） | `get_card_list` 的建卡与到期日、`get_equipment_list` 的装机日、`get_refund` | `列 <= endDate 23:59:59` | 正常填当天即可，含当天整天 |
| **报表类**（闭区间） | `get_recharge_report`、`get_consume_report`、`get_equipment_consume_report` | `Date <= endDate` | 报表按天存、无时分秒，正常填当天即可 |

统计类接口（`get_year_month_day_stats`、`get_recharge_chart`、`get_consume_chart`、`get_equipment_consume_desc`）的 `startDate` 格式**必须与 `dateType` 对齐**：`0`→`yyyy-MM-dd`、`1`→`yyyy-MM`、`2`→`yyyy`。格式错了后端不做解析、会静默拼出废日期区间，**只会拿到全 0 结果**，不会报错。

### 5. 筛选方式：模糊 vs 精确

- `searchKey` 是**模糊**匹配，但**各工具覆盖的字段不同**，以工具描述为准。典型：`get_card_list` 只匹配「持卡人手机号/姓名、开户人手机号/姓名」四个字段（**不匹配卡号**）；`get_water_order` 的 `searchKey` 走「单号精确」语义（见下条）；`get_refund` 的 `searchKey` 是覆盖面最广的一个（系统单号/订单号/手机号/卡号/姓名）。
- 名为 `cardCode`、`equipmentCode`、`orderId`、`mobile`、`outTradeNo` 的参数为**精确**匹配。`mobile` 是精确等值，号码差一位就查不到，模糊找人要用 `searchKey`。
- ⚠️ **订单类工具（`get_water_order` / `get_recharge_order` / `get_draw_money_order` 及各 `*_history`）的 `searchKey` 必须与 `searchKeyType` 成对传**：`searchKeyType` 取 1=订单号、2=系统单号（`W`/`R`/`D`+日期数字）、3=第三方支付单号。后端只有在 `searchKeyType>0` 时才使用 `searchKey`，**否则静默忽略它并返回全部记录**（不报错）。想按卡号查请改用 `cardCode`。
- 拿不到结果时，优先放宽条件（日期区间 / `searchKey` / `scope` / 换 `*_history`），而不是直接回复「没有数据」。

### 6. 排序：只能按白名单，两类接口不支持

- `sortBy` 的合法值即各工具描述里列出的白名单字符串（后端视图里真实存在的列）。传白名单外的字段会被网关直接拒绝，**不要凭猜测字段名**。
- `sortDir` 取 `ASC`/`DESC`，默认 `ASC`，只在给了 `sortBy` 时生效。
- 常用排序：查余额最多/最少用 `get_card_list` 的 `TotalAmount`；查快到期用 `EndDate`；查大额单用订单类的 `TotalFee`；看哪台机器卖得好用 `get_equipment_consume_report` 的 `TotalPrice` + `DESC`。
- ⚠️ **三个 `*_history` 归档接口不支持自定义排序**（读的是 Mongo 归档，后端不看 `Sorts`）；`get_recharge_coupons` 固定按后台排序号倒序。
- ⚠️ 「在线/离线」**不能拿来排序**（视图里没有这一列）。要看离线设备请传 `isOnline=false`。

### 7. 水卡的两种卡号

| 卡型 | 标识 | 形态 |
|---|---|---|
| 实体卡 | `CardCode` | 8 位卡面编号，形如 `4496DE2F` |
| 电子卡 | `MemberCardId` | 纯数字，**新建卡已是 9 位**，形如 `100000004` |

- `get_card_by_code` 按长度判断电子卡，**9 位新编号会回「此卡不存在」**。这种卡请改用 `get_card_list` 传 `memberCardId`。
- 订单里的 `cardCode` 参数对应后端 `AccountCode1`，存的是「有卡面编号就存编号、没有就存 `MemberCardId`」——两种都要能传，等值匹配、大小写不敏感，但**前后带空格查不到**。

### 8. 响应结构

- 成功：`{"success":true,"count":N,"data":...}`
- 后端失败：`{"success":false,"code":"...","error":"..."}`
- 网关参数拒绝：`{"success":false,"code":"-1","error":"..."}`（参数格式不合法、排序字段不在白名单、必填缺失等）

**两种情况都要按「这次查询没成功」处理**：如实转述 `error`，不要当成空结果向用户报「没有数据」。

## 四、工具清单

### 4.1 账号与组织（3 个只读）

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_company` | 当前登录经销商自身信息（名称、编码、级别、联系方式）。**无参数**，适合开场确认账号与层级 | — |
| `get_company_childs` | 下级经销商/子单位列表（分区与小区两层） | `parentCode`（36 位 Guid，留空=自己）、`scope`（默认 1）。⚠️ 后端**只认这两个参数**，不支持关键字搜索/分页/排序；要按名称找人请用 `get_below_agent` |
| `get_below_agent` | 下级代理商列表（Level1~3 经销商） | `searchKey`（匹配单位名/联系人/联系电话）、`parentCode`、`level`（0/1/2/3，0=不限）、`sortBy`、`sortDir`、`page`、`size` |

> `get_company_childs` 与 `get_below_agent` 语义相近：前者是「下级单位（分区/小区）」，后者是「经销商/代理商」。用户说「下级」时先各查一次或询问澄清，不要主观二选一。
> ⚠️ `get_company_childs` 不支持模糊搜索——传 `searchKey` 这类参数不生效，别以为查空了。

### 4.2 水卡查询（3 个只读）

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_card_list` | 会员卡列表与余额、状态、有效期 | `searchKey`（手机/姓名模糊，**不含卡号**）、`cardCode`（精确）、`memberCardId`（查 9 位电子卡用这个）、`mobile`（精确）、`equipmentCode`、`cardType`（0不限/1金额卡/2计次卡）、`useStatus`（0不限/1正常/2挂失/3已到期）、`totalAmountBelow`（余额或次数「小于此值」）、`createStartDate`/`createEndDate`、`validStartDate`/`validEndDate`、`sortBy`、`sortDir`、`page`、`size` |
| `get_card_by_code` | 按卡号精确查单张卡详情 | `cardCode`（**必填**；8 位实体卡或不足 8 位的老电子卡号） |
| `get_card_coupons` | 某张卡持有的优惠券/时效套餐 | `memberCardId`（**必填**，先由 `get_card_list` 取得） |

补充说明：
- `totalAmountBelow` 单独用时**会混两种口径**（金额卡比卡内总额、计次卡比剩余次数）。问金额请配 `cardType=1`，问次数请配 `cardType=2`。
- `useStatus=3`（已到期）是后端按「有效期早于当前时间」推导的，不是存的列值。
- `validEndDate` 填「今天+30 天」就是查一个月内到期的卡。

### 4.3 水卡写操作（4 个：1 write + 3 dangerous）

| 工具 | 等级 | 用途 | 关键参数 |
|---|---|---|---|
| `update_card_use_status` | `write` | 挂失 / 恢复正常卡 | `memberCardId`、`useStatus`（1=正常，2=挂失） |
| `create_card` | `dangerous` | 开实体会员卡（可同时把金额/次数写进卡） | `cardCode`（**必填**，正好 8 位字母或数字）、`cardType`（默认 1 金额卡，仅明说计次才填 2）、`endDate`（留空=网关补「开卡日 + 10 年」）、`companyCode`（分区，留空=自动解析直属分区）、`rechargeMoney`、`presentMoney`、`name`、`mobile`、`remark`、`address`、`equipmentCode` |
| `recharge_card` | `dangerous` | 会员卡充值 | `cardId`（= `MemberCardId`）、`money`、`giveMoney`（赠送，可选）、`remark` |
| `draw_money` | `dangerous` | 会员卡扣款 | `cardId`、`money`（扣余额；计次卡传 0）、`presentMoney`（扣赠送余额；**计次卡在这里传要扣的次数**）、`remark` |

`create_card` 的分区规则（**最容易卡住的一步**）：
1. 用户话里带了分区名称 → 先调 `get_company_childs`（`parentCode` 留空、`scope` 用默认的 1），把匹配上的分区 `CompanyCode` 填进 `companyCode`，一轮就能开出来。
2. `companyCode` 留空 → 网关在「当前账号的直属下级」里找分区：只有一个就直接用；**有多个时不提交任何数据**，而是返回一份「分区名称 + 编码」清单。这时要把清单**原样列给用户**、等用户选定后再带上 `companyCode` 重新调用。
3. 只允许开到**直接挂在自己名下**的分区。分区可能挂在一级/二级/三级经销商名下，但上级不能跨级开卡。若返回的拒绝文案说该分区不归你，**不要**改用 `scope=0` 再试一次。
4. `endDate` 省略时成功结果里会带 `appliedDefaultEndDate`，**手上没有今天的日期，不要自己推算**，直接把该值转告用户。
5. ⚠️ 开卡即充的钱是**直接改卡表余额、不生成充值订单**的。要给用户留可追溯的充值记录，请开完卡再走 `recharge_card`。

### 4.4 营销配置（1 个只读）

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_recharge_coupons` | 时效套餐（线上营销）配置 | `rechargeTemplateId` 与 `companyCode` **至少填一个**（都不填后端回参数无效）、`searchKey`（匹配套餐名/副标题）、`status`（0禁用/1启用）、`type`（1线下/2全部/3线上）、`couponConType`（1按金额/2按次数）、`cycleType`（0自定义/1每天/2每月）、`page`、`size`。结果固定按后台排序号倒序，不支持自定义排序 |

### 4.5 订单与资金流水（8 个只读）

三个「近期」接口读实时表，三个 `*_history` 读 Mongo 归档（**不含当天**，时间更久、量更大），加 `get_order` 与 `get_refund`。

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_water_order` | 消费记录（打水/售水订单）**近期** | `orderId`、`searchKey`+`searchKeyType`（**必须成对**）、`cardCode`、`equipmentCode`、`payStatus`、`consumeStatus`、`payType`、`startDate`、`endDate`、`scope`、`sortBy`、`sortDir`、`page`、`size` |
| `get_water_order_history` | 消费记录**归档** | 同上，但**不支持排序** |
| `get_recharge_order` | 充值订单**近期** | `orderId`、`searchKey`+`searchKeyType`、`outTradeNo`、`cardCode`、`payType`、`rechargeType`、日期、`scope`、`sortBy`、`sortDir`、`page`、`size` |
| `get_recharge_order_history` | 充值订单**归档** | 同上，但**不支持 `outTradeNo`、不支持排序** |
| `get_draw_money_order` | 扣款订单**近期** | `orderId`、`searchKey`+`searchKeyType`、`cardCode`、日期、`scope`、`sortBy`、`sortDir`、`page`、`size` |
| `get_draw_money_order_history` | 扣款订单**归档** | 同上，但**不支持排序** |
| `get_order` | 按订单号查单个订单详情（实时表与缓存） | `orderId`（**必填**，21 位串，形如 `5sckHPCPp0YTUsEfi3OBg`，**不是** `R`/`W`/`D` 开头的系统单号） |
| `get_refund` | 退款记录 | `orderRefundId`、`orderId`、`searchKey`（**本工具是唯一覆盖面广的模糊搜索**：系统单号/订单号/手机号/卡号/姓名）、`status`、`startDate`、`endDate`、`scope`、`sortBy`、`sortDir`、`page`、`size` |

枚举速查：

- `payStatus`：0 未支付，1 已支付，2 已申请退款，3 退款成功，-1 支付失败
- `consumeStatus`：1 未消费，2 成功，3 失败，4 设备忙，5 设备离线，6 设备无响应，7 设备故障，8 消费中
- `payType`：1 微信，2 支付宝，3 余额，4 投币，5 后台充值
- `rechargeType`：1 开卡充值，2 后台充值，3 用户自助充值，4 代客充值，5 兼容卡充值
- `get_refund` 的 `status`：0 待处理，1 已申请退款，2 退款成功，**-1 退款失败**（注意：文档里写的 `3=失败` 是错的，后端枚举 `Failure=-1`）

> **近期 vs 历史**：查「最近/本月」用不带 `history` 的；查「很久以前」、或近期查不到时改用 `*_history`。用户说「这笔订单」但时间不明时，两个都试。
> **典型诊断用法**：「付了钱没出水」= `get_water_order` 传 `payStatus=1` 且 `consumeStatus` 取 3/5/6/7 这几个失败类状态。

### 4.6 设备（5 个只读 + 1 个 dangerous）

| 工具 | 等级 | 用途 | 关键参数 |
|---|---|---|---|
| `get_equipment_list` | read | 售水设备列表（位置、状态、绑定关系） | `searchKey`（匹配设备名称/编号/小区名）、`equipmentCode`、`agreementType`（10售水机/11数码管水控（自动并上 17 液晶水控）/13洗车机/15售液机/16手持机/17液晶水控）、`equipmentTypeId`、`province`/`city`/`area`（需与库里写法一致，如「广东省」）、`companyCode`、`parentCompanyCode`、`createStartDate`/`createEndDate`、`isOnline`、`isWarning`、`scope`、`sortBy`、`sortDir`、`page`、`size` |
| `get_equipment_params` | read | 某台设备的参数配置 | `equipmentCode`（**必填**）、`page`（每页固定 50 条，需翻页取全） |
| `get_warn_status` | read | 设备告警/预警运行状态（水压、水位、TDS、流量计/电磁阀故障等） | `equipmentCode`、`searchKey`（**只匹配设备编号**，不含名称/小区）、`isWarning`、`isOnline`、`scope`、`sortBy`、`sortDir`、`page`、`size` |
| `get_equipment_activity` | read | 指定设备关联的营销活动 | `equipmentRelationId`（**必填**，先由 `get_equipment_list` 取得） |
| `search_device_faq` | read | **设备故障知识库**：屏显故障码含义 + 现场故障排查 + 业务规则问答 | `question`（用户原话，原样传）、`errorCode`（`E-01`/`E01`/`E---001`/`95L` 都认）、`partType`（-1不限/1主板侧/2水控侧）、`top`（1~5，默认 3） |
| `save_equipment_params` | **dangerous** | 批量保存设备参数并**下发到设备** | `equipmentRelationId`、`equipmentCode`、`paramChanges`（JSON 数组字符串 `[{"equipmentParamId":123,"value":"456"}]`，单次 ≤50 条）、`huifuchuchang`（1=保存并下发，0=仅存库不下发） |

补充说明：
- `isOnline` / `isWarning` 的判定口径都是「最后心跳（或告警）距今 30 分钟内」，**不是实时状态**。
- ⚠️ **回答故障码、设备故障、运维排查这类问题前必须先调 `search_device_faq`**，不要凭常识解释故障码——库里的口径由售后维护，猜出来的处置步骤可能让经营者把设备弄坏。未命中时返回体里会带 `note`，要如实告知「暂无标准口径」并引导联系售后/报修，**禁止编造故障码含义或处置步骤**。
- `save_equipment_params` 的依赖链：`get_equipment_list`（取 `EquipmentRelationId` + `EquipmentCode`）→ `get_equipment_params`（取 `EquipmentParamId`）→ 保存。网关会自动校验设备在线，**离线设备直接拒绝**。`huifuchuchang=1` 会经 IoT 真实下发 MQTT 指令，设备立即按新参数运行（如计费参数改了，刷卡扣费金额立刻变）。除非用户明确说「先保存不下发」，否则都用 1。

### 4.7 报表与统计（10 个只读）

**按天分行的明细报表**（日期闭区间，不含当天实时数据）：

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_recharge_report` | 充值统计报表（每天一条汇总） | `startDate`、`endDate`、`sortBy`（`ZongPrice` 充值总额、`ZengSongZongPrice` 赠送总额、`ZongCount` 笔数、`WeiXinPrice` 线上充值、`DrawRechargeMoney` 扣款金额）、`sortDir`、`page`、`size` |
| `get_consume_report` | 消费统计报表（每天一条汇总） | `startDate`、`endDate`、`sortBy`（`TotalPrice` 消费总额、`TotalCount` 单数、`WaterCardPrice` 刷卡、`CoinPrice` 投币、`WeiXinPrice` 微信、`AliyPrice` 支付宝、`WaterQuantity` 出水量 L）、`sortDir`、`page`、`size` |
| `get_equipment_consume_report` | 按 设备×日期 分行的消费统计 | `searchKey`（设备名称模糊 **OR** 设备编号精确，编号必须完整）、`startDate`、`endDate`、`sortBy`、`sortDir`、`page`、`size` |

**当日实时汇总**（无参数，取自实时统计缓存，只有当天）：

| 工具 | 用途 |
|---|---|
| `get_today_recharges` | 当天充值汇总（总金额/赠送/笔数，按微信、支付宝、开卡、后台、取款等维度细分） |
| `get_today_consumes` | 当天消费汇总（总金额/总笔数，按水卡、投币、会员、微信、支付宝等维度细分） |

**单个周期的汇总与排行**（`dateType` 0=按日 / 1=按月 / 2=按年；`startDate` 格式必须与 `dateType` 对齐）：

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_user_card_stats` | 会员卡概况：总卡数、金额卡/计次卡、电子卡/实体卡、到期卡、挂失卡、有效卡，以及余额/赠送/次数/积分合计 | `projectCode`（小区编码，可选，**仅当前账号为 1~3 级经销商时生效**） |
| `get_year_month_day_stats` | **某一个**年/月/日的充值与消费总额（消费 `TotalXF`、充值 `TotalCZ`、赠送 `TotalZS`、开卡充值 `TotalKKCZ` 等）；所含周期含今天时自动叠加当天实时数据 | `dateType`、`startDate`。**后端忽略 `endDate`** |
| `get_equipment_consume_desc` | **某一个**年/月/日各台设备的消费排行（设备名、编号、金额、笔数），回答「哪台机器卖得最好」 | `dateType`、`startDate`、`projectCode`（可选，本接口**不支持按小区收窄**，后端会忽略） |

**7 桶趋势图**（固定 7 个周期桶，附 `ItemList` 逐期明细，可直接画折线图）：

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `get_recharge_chart` | 充值趋势：总额、线上（微信）充值、赠送总额、线上赠送 | `dateType`（**只支持 0 按日 / 1 按月**）、`startDate`、`endDate` |
| `get_consume_chart` | 消费趋势，按支付方式拆分：刷卡、投币、微信、支付宝、会员扫码 | 同上 |

补充说明：
- ⚠️ **报表数据由后台日任务生成，不含当天**。用户问「今天充值多少」必须走 `get_today_recharges` / `get_today_consumes` / `get_year_month_day_stats`，报表类会返回空集。
- ⚠️ **两个趋势图接口不支持按年**（后端只有按日/按月两个分支，`dateType=2` 会静默返回空 `ItemList` 与全 0 合计）。要某一年的合计请用 `get_year_month_day_stats(dateType=2, startDate=年份)`。
- 趋势图的 `endDate` **不改变桶的数量**（恒为从 `startDate` 起的 7 个桶），它只用来「跳过等于该值的那一格」；想让 7 格完整呈现，就填 `startDate` 之后第 7 个周期。

## 五、典型任务链

有依赖关系的查询必须分两步，**不要凭空编造 ID**：

1. **查某张卡的优惠券**：`get_card_list`（用卡号/手机号/姓名找到目标卡）→ 取 `MemberCardId` → `get_card_coupons(memberCardId)`
2. **查某台设备的营销活动**：`get_equipment_list`（用设备编号或关键字找到设备）→ 取 `EquipmentRelationId` → `get_equipment_activity(equipmentRelationId)`
3. **查充值套餐**：先确认 `companyCode`（由 `get_company` 或 `get_company_childs` 取得）→ `get_recharge_coupons`
4. **给某张卡充值/扣款**：`get_card_list`（按卡号或手机号找到卡，**顺便确认 `CardType`**）→ 若扣款且是计次卡，次数填到 `presentMoney` → `recharge_card` / `draw_money`
5. **开一张卡**：若用户点了名 → `get_company_childs`（`scope=1`）取分区 `CompanyCode` → `create_card`；若没点名 → 直接 `create_card`，从返回的分区清单里让用户挑
6. **改设备参数**：`get_equipment_list`（取 `EquipmentRelationId`/`EquipmentCode`，并确认在线）→ `get_equipment_params`（取 `EquipmentParamId`）→ `save_equipment_params`

## 六、写操作确认规则（5 个 write/dangerous 工具必读）

调用 `create_card`、`recharge_card`、`draw_money`、`update_card_use_status`、`save_equipment_params` 前，**必须先向用户复述具体对象与参数并取得明确同意**，然后再调用：

| 工具 | 调用前必须复述给用户的内容 |
|---|---|
| `create_card` | 卡面编号、卡类型（金额卡/计次卡）、分区、开卡即充金额与赠送、到期日（未指定时说清楚默认按「开卡日 + 10 年」） |
| `recharge_card` | 卡号 + 持卡人、充值金额、赠送金额 |
| `draw_money` | 卡号 + 持卡人、扣款金额（计次卡则说明扣几次） |
| `update_card_use_status` | 卡号 + 持卡人、目标状态（挂失 / 恢复） |
| `save_equipment_params` | 设备编号 + 名称、要改的参数项与**新旧值对照**、是否立即下发到设备 |

规则细节：

- 目标卡/设备必须先查出来给用户看过（卡号 + 持卡人 + 当前余额；设备编号 + 名称 + 当前参数值），**不要直接用用户口述的编号就下单**。
- 用户没有明确说金额/次数时，**不要自己猜一个数字**，先问清楚。
- 若宿主平台在调用时还会弹出授权/确认卡片，以该卡片上的用户确认为准；此时不必再额外追问一次。
- 写操作成功后，把返回的新状态（如充值后余额、开卡得到的 `MemberCardId`、`appliedDefaultEndDate`）转告用户；**不要声称「已到账」之外没依据的状态**。

## 七、异常处理

| 情况 | 处理方式 |
|---|---|
| 鉴权失败 / 无权限 | 告知用户 Token 可能失效（密码修改后需重新生成），引导重新连接并更新 Token；**不要反复重试** |
| 返回 `success:false` | 读取 `error` 并如实转述，不要编造原因 |
| 网关参数拒绝（`code:"-1"`） | 按 `error` 里说的改参数重试（如排序字段不在白名单、日期格式不对、必填缺失） |
| 空结果 | 依次尝试：放宽日期区间 → 改用 `searchKey` 模糊 → 切换 `scope` → 换用 `*_history`。全部无效才回复「未查到」 |
| `searchKey` 传了却像没生效（返回全部记录） | 订单类接口漏了 `searchKeyType`，补上 1/2/3 重试 |
| 统计结果全是 0 | 先查 `startDate` 格式是否与 `dateType` 对齐；趋势图接口还要确认没传 `dateType=2` |
| 「今天/本月」查不到数据 | 报表类不含当天数据；改用 `get_today_*` / `get_year_month_day_stats` |
| 参数无效（如 `get_recharge_coupons` 没传 `rechargeTemplateId`/`companyCode`） | 补齐必填参数后重试 |
| 返回体被截断/落盘 | 减小 `size` 后分页重取，不要一次性拉全量 |

## 八、回答规范

- 报数字时**说明口径**：数据范围（是否含下级）、时间区间、筛选条件。
- 报总数时用 `count`，并说明这是「符合条件的总条数」而非本页条数。
- 金额统一带 `¥` 与千分位，百分比保留一位小数。
- 数据为空时明确说「未查到」，**不要用 0 或推测值代替**。
- 涉及具体卡号、手机号等个人信息时，在群聊或对外场合注意脱敏。
