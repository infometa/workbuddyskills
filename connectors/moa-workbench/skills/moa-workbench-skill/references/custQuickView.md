# 客户速查场景

用于销售在通话后快速掌握客户情况：**定位客户**（客户名/联系人姓名/手机号/微信）、**查看客户全景**（资料、跟进人、标签、联系方式、跟进与通话记录等），需要继续联系时**经用户确认创建回访提醒**。

## 场景工具

参数结构以工具 schema 为准，本文档不写死字段。

| 工具 | 用途 |
|---|---|
| searchCustomer | 按客户名称或联系人（姓名/手机号/微信）搜索客户，最多返回前 100 条 |
| getCustomerFollowRecords | 按客户 ID 查跟进记录（沟通/通话+外勤两类合并，时间倒序，支持按跟进记录时间范围过滤） |
| getCustomerSalesChances | 按客户 ID 查商机列表（阶段历史/金额/跟进人/赢单输单状态） |
| getCustomerOrders | 按客户 ID 查销售订单列表（状态/金额/回款退款汇总，权限范围内） |
| getOrderReceivePayments | 按订单 ID 查回款与退款明细列表（金额/回款方式/状态/退款原因/图片附件） |
| getOrderContracts | 按订单 ID 查合同列表（标题/编号/起止时间/自定义属性/图片附件） |
| getCustomerReminds | 按客户 ID 查回访提醒（未完成/已失效两组，未完成含逾期标记） |
| createRemind | 创建回访提醒（关联客户，指定提醒时间与重复规则） |
| whoami | 查询当前登录用户的简要信息（pid/did/姓名），用于确认当前登录身份 |

## 工作流

### 1. 定位客户

调用 searchCustomer：

- name 与联系人条件（contactName/mobile/wechat）至少提供一个，且联系人条件至多提供一个（底层同为联系人搜索字段）。
- 最多返回前 100 条，无分页；**命中多条时必须向用户展示候选并确认唯一客户后再继续**。
- 返回完整客户信息：创建时间（即客户来源时间）、跟进人、标签、联系人、自定义属性等，可直接用于向用户汇报客户情况。

### 2. 查询客户全景并汇报

定位到唯一客户后，按用户关注点调用对应查询工具（均传 custmid）：

- **getCustomerFollowRecords**：返回该客户跟进记录（沟通/通话记录与外勤记录两类合并，时间倒序，合计取前 9999 条）；支持 timeStart/timeEnd（GMT 毫秒时间戳）按跟进记录时间范围过滤，不传则不限；source=talk 为沟通/通话记录，crdid 非零为电销通话记录（含通话状态/方向与 AI 外呼标记，关联商机见 scid），source=legwork 为外勤记录（含签到/签退位置与目标地址距离）；仅单一来源有效的字段不适用时省略（如外勤记录无通话字段）；跟进内容在 content（纯语音外勤为占位文本）；图片在 pictures、附件在 atts、语音在 voices（均带下载链接，获取失败时为空不影响主体数据）；自定义表单在 forms（value 已解析，选项类已映射为选项文本；值为空（未填写或解析异常）的表单项整项不返回）。
- **getCustomerSalesChances**：返回该客户全部商机（内部自动分批拉全）；列表含当前阶段编号与阶段历史（名称/占比/进出时间）；阶段 5=赢单、6=输单，其余为自定义阶段（名称见 stepInfos）；图片在 pictures、附件在 atts（带下载链接，获取失败时为空不影响主体数据）。
- **getCustomerOrders**：返回该客户全部订单（内部自动分批拉全）；订单状态含语义描述（statusDesc）；回款/退款为汇总金额与笔数；商品明细在 products（含单价/数量/折扣/金额），折扣为百分率（85=八五折）；订单属性在 myProps（含自定义字段与备注/收货信息等系统属性，value 已解析为可读值）；附件在 atts（含图片，带下载链接，链接获取失败时为空不影响主体数据）。
- **getOrderReceivePayments**：用户关注回款/退款明细时，先用 getCustomerOrders 拿到订单再按 orderId 查（orderId 取自 getCustomerOrders 返回，不要臆造）；返回该订单全部回款与退款（内部自动分批拉全）；回款在 receivePayments（含回款方式/确认信息），退款在 refunds（含退款原因）；金额均为单笔金额；状态含语义描述（statusDesc：待确认/已确认/已驳回/已作废/未设置审批人）；图片在 pictures、附件在 atts（带下载链接，获取失败时为空不影响主体数据）。
- **getOrderContracts**：用户关注合同信息时按 orderId 查（orderId 取自 getCustomerOrders 返回，不要臆造）；返回该订单全部合同（create_time 倒序）；开启的自定义属性在 properties（value 已解析为可读值，与订单属性同口径）；图片在 pictures、附件在 atts（带下载链接，获取失败时为空不影响主体数据）。
- **getCustomerReminds**：返回该客户全部提醒（内部自动分批拉全）；reminds 为未完成提醒（overdue=true 表示已逾期），invalidReminds 为已失效提醒。
- 客户 ID（custmid）与订单 ID（orderId）一律取自工具返回，不要臆造；无数据时返回空列表属正常。
- 汇报内容根据用户关注点裁剪，不要把全部字段罗列给用户。

### 3. 创建回访提醒（经确认）

调用 createRemind：

- 关联 customerIds（取自 searchCustomer 返回的 custmid，不要臆造）；awokePids/awokeGids 不指定时默认提醒当前登录用户。
- 创建前先查 getCustomerReminds，避免与既有未完成提醒重复；提醒内容、提醒时间（remindTime，GMT 毫秒时间戳）必须来自用户；重复规则未指定时默认"不重复"（repeatType=1）。
- 成功响应含提醒 id 与 nextScheduleTime，单独回报给用户。

## 常见异常

| 现象 | 处理方式 |
|---|---|
| 401 / 未授权 | 提示用户重新发起扫码授权（AGENT 会自动打开授权页） |
| 搜索命中多条客户 | 展示候选列表让用户确认唯一客户，不要自行猜测 |

## 注意事项

- 一切客户 ID（custmid）、订单 ID（orderId）来自工具返回，不要臆造。
- 汇报按用户关注点裁剪，避免罗列全部字段。
