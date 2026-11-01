---
name: moa-workbench-skill
description: 口袋助理 KDZL 工作台技能 - 扫码 OAuth 授权后，AGENT 可调用客户管理、跟进记录、订单、回款、商机、工作汇报等业务能力工具
version: "1.0.0"
author: "KDZL"
---

# 口袋助理 KDZL 工作台 Skill

本 Skill 提供口袋助理 KDZL 工作台的全部能力：覆盖客户管理、跟进/外勤、订单、回款、商机、提醒、电销、工作汇报等业务域。用户完成扫码 
OAuth 授权后，AGENT 即可按用户意图调用。

## 认证说明

- 采用标准 OAuth 2.1 + PKCE，由 AGENT 自动驱动，无需手动管理凭证。
- 授权方式：浏览器打开授权页后，使用「口袋助理」App 扫描页面上的二维码并确认登录。
- 若工具调用返回 401 / 未授权，提示用户重新发起授权（AGENT 会自动打开授权页）。
- Token 过期后 AGENT 自动使用 refresh_token 续期，无需用户干预。

## 工具总览（按业务域分类）

参数结构以各工具的 schema 为准，本文档不写死字段。

### 通讯录 / 身份（roster）

| 工具           | 用途                                   |
|--------------|--------------------------------------|
| whoami       | 查询当前登录用户简要信息（pid/did/姓名），确认当前身份      |
| findPersons  | 按姓名批量查找通讯录成员（PID/姓名/职位/部门），把姓名转为 pid |
| getAllPerson | 获取通讯录成员（含职位与部门；传 gid 含子部门，不传为全公司）    |
| getAllGroup  | 获取部门 / 组织架构列表                        |

### 客户（customer）

| 工具                         | 用途                                            |
|----------------------------|-----------------------------------------------|
| searchCustomer             | 按客户名或联系人（姓名/手机/微信）搜索客户，最多前 100 条              |
| createCustomer             | 创建客户（需【创建客户】权限）                               |
| editCustomer               | 编辑客户（editFields 局部更新；contacts 增量操作；需【编辑客户】权限） |
| setCustomerLabels          | 全量覆盖客户标签配置树（需管理员 / CRM 权限）                    |
| getCustomerProperties      | 获取客户 / 联系人自定义属性配置                             |
| getCustomerLabels          | 获取客户标签树配置                                     |
| getCustomerFollowLevel     | 获取跟进阶段配置                                      |
| getCustomersByIds          | 按客户 ID 批量获取客户详情                               |
| getLfCustomerList          | 按最后跟进时间获取客户列表                                 |
| getAssignedCustomerList    | 获取已分配客户列表                                     |
| getCreateCustomerList      | 获取我创建的客户列表                                    |
| getAllPubSea               | 获取公海列表                                        |
| getPsCustomerList          | 获取公海客户列表                                      |
| getImportCustomerTpl       | 获取客户导入模板                                      |
| convertImportCustomerData  | 转换导入客户数据（需AGNET提前将Excel 解析为所需格式的数据）           |
| checkImportCustomerSimilar | 导入客户查重                                        |
| batchImportCustomer        | 批量导入客户（需【导入客户】权限）                             |
| batchAllocPsCustomer       | 批量分配公海客户（需【分配客户】权限）                           |

### 跟进 / 外勤（legwork）

| 工具                               | 用途                              |
|----------------------------------|---------------------------------|
| getCustomerFollowRecords         | 按客户 ID 查跟进记录（沟通/通话 + 外勤合并，时间倒序） |
| getFollowRecords                 | 查跟进记录列表                         |
| createCustomerFollowRecord       | 创建跟进记录（需【创建跟进记录】权限）             |
| batchCreateCustomerFollowRecords | 批量创建跟进记录（需【创建跟进记录】权限）           |
| addFollowRecordComment           | 为跟进记录添加评论                       |

### 订单 / 回款 / 合同（order / receivepayment / contract）

| 工具                      | 用途                            |
|-------------------------|-------------------------------|
| getCustomerOrders       | 按客户 ID 查销售订单列表                |
| getOrderList            | 查订单列表                         |
| getOrderRank            | 员工成交排行（需指定 startTime/endTime） |
| getOrderReceivePayments | 按订单 ID 查回款 / 退款明细             |
| getReceivePaymentList   | 查回款列表                         |
| getOrderContracts       | 按订单 ID 查合同列表                  |

### 商机（salesChance）

| 工具                      | 用途           |
|-------------------------|--------------|
| getCustomerSalesChances | 按客户 ID 查商机列表 |
| getSalesChanceList      | 查商机列表        |

### 提醒（schedule）

| 工具                 | 用途                      |
|--------------------|-------------------------|
| createRemind       | 创建回访提醒（关联客户，指定时间与重复规则）  |
| getCustomerReminds | 按客户 ID 查回访提醒（未完成 / 已失效） |

### 电销（phonesale）

| 工具          | 用途     |
|-------------|--------|
| getCallStat | 获取通话统计 |

### 工作汇报（workReport）

| 工具                 | 用途              |
|--------------------|-----------------|
| getWorkReportTemplate | 查工作汇报自定义表单模板 |
| createWorkReport  | 创建工作汇报（正文或自定义表单） |
| getWorkReportList | 查工作汇报列表(含自定义字段/附件) |
| modifyWorkReport  | 修改工作汇报（正文或自定义表单） |

## 场景工作流索引

不同任务参考对应场景文档（含该场景的工具组合、推荐工作流、参数语义与异常处理）：

| 场景    | 用途                                   | 参考文档                              |
|-------|--------------------------------------|-----------------------------------|
| 创建客户  | 搜索既有客户 → 获取公司配置 → 创建/编辑 → 打标签 → 回访提醒 | @references/createCustomer.md     |
| 公海处理  | 导入模板 → 数据解析 → 查重 → 批量导入 → 公海分配       | @references/dealPsCustomer.md     |
| 客户速查  | 通话后定位客户 → 查看全景信息 → 经确认创建回访提醒         | @references/custQuickView.md      |
| 客户分析  | 客户资料 / 跟进 / 订单 / 商机 / 回款多维分析         | @references/custAnalysis.md       |
| 跟进写入  | 创建 / 批量创建客户跟进记录                      | @references/custFollowWrite.md    |
| 跟进质检  | 查跟进记录 → 评价与评论                        | @references/custFollowQuality.md  |
| 高频未成交 | 筛选高频跟进但未成交客户并分析                      | @references/custHighFreqUnsold.md |
| 销售转化  | 销售转化漏斗与趋势分析                          | @references/salesConversion.md    |
| 通话处理量 | 电销通话处理量统计                            | @references/callProcessVolume.md  |
| 销售报告  | 自动生成销售日报 / 周报                        | @references/salesReport.md        |

## 注意事项

- 所有工具调用均要求用户已完成扫码授权；未授权时不要臆造数据。
- 参数结构以工具 schema 为准；不要臆造客户 ID、联系人 ID 等，一切以工具返回为准。
- 写操作均需要用户确认后才能执行，除非用户明确授权。
- 如遇连接超时（默认 30s），提示用户检查网络后重试。
