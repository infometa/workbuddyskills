---
name: moka-compensation-admin
display_name: Moka 薪酬管理
display_name_en: Moka Compensation Admin
description: 面向薪酬负责人与薪酬管理角色的薪酬数据查询（薪酬敏感数据，普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器按场景查询工资单、薪资档案、定调薪、发薪核算与预警、社保等薪酬列表，以及薪酬填报活动、任务与在线填报明细。当用户以薪酬管理视角核对发薪数据或跟进填报进度时使用。
description_zh: 面向薪酬负责人与薪酬管理角色的薪酬数据查询（薪酬敏感数据，普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器按场景查询工资单、薪资档案、定调薪、成本分摊与代发、发薪核算与核算预警、社保等薪酬列表，以及薪酬填报活动、活动下任务与在线填报明细。当用户问「工资单发送状态」「入职未定薪的人」「停止发薪名单」「填报活动进展」等薪酬管理问题时使用。
description_en: Compensation data queries for compensation owners and payroll admin roles (compensation-sensitive data; regular employee accounts lack the required permissions). Uses the Moka Connector available on the current platform to query payroll lists by scene (payslips, salary archives, salary setting and adjustment, cost apportionment and agent pay, payroll calculation and warnings, social insurance) plus salary submission activities, their tasks, and online submission details. Use it for admin questions like payslip delivery status, employees without salary set after onboarding, stopped-pay lists, or submission activity progress.
category: productivity
version: 1.0.0
author: Moka
---

# Moka 薪酬管理

以薪酬负责人视角查询薪酬列表与填报进度，全部只读、薪酬敏感。只编排以下两个工具：

- `mcp__moka__search_salary_data_list`
- `mcp__moka__get_salary_submission_activities`

## 选择工具

薪酬列表查询用 `mcp__moka__search_salary_data_list`：按业务场景（scene）取数，场景覆盖：

- 工资与档案：工资单列表、薪资档案、定薪管理、调薪管理。
- 成本与代发：成本分摊结果、代发记录详情。
- 发薪核算：全部发薪、停止发薪。
- 核算预警：入职未定薪、离职未停薪、同一天入离职、法人公司缺失、人员报送失败、末次发薪与离职日期不匹配、起薪与入职日期不匹配、在途审批。
- 社保：未匹配参保方案人员、不参保人员。

适用于「这批工资单的发送状态」「入职未定薪的人员名单」「本月停止发薪的人有哪些」等问题。

薪酬填报用 `mcp__moka__get_salary_submission_activities`：只读查询当前账号可见的薪酬填报数据，覆盖：

- 填报活动列表（可按名称关键词、月份、创建人、活动状态筛选）与活动详情。
- 按活动名称消歧：名称不唯一时先消歧，只有唯一命中才可直接使用。
- 活动下的任务列表与任务详情（填报金额、流程状态、是否超出填报范围）。
- 在线填报明细预览（已剔除敏感列的表头与当前页明细）。

适用于「有哪些薪酬填报活动」「这个活动的任务都提交了吗」「预览填报名单」等问题。

易混辨析：「薪酬列表」是既有薪酬数据的盘点视角，「填报活动」是按月组织的数据收集流程视角；跟进某次填报的进度用后者，核对发薪与档案数据用前者。

非薪酬的人事列表（花名册、合同、异动等）、员工本人查自己的工资单，以及薪酬数据的修改或提交，不要用本技能的工具。这些问题应由当前可用的其他 Moka 工具处理。

## 调用规范

1. 使用 Moka 连接器提供的工具（本技能内的工具名即实际注册名）；连接器未安装或未连接时如实告知用户，不改用其他来源。
2. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源；各场景与查询动作的确切取值以工具实时 description 为准。
3. 只传用户明确给出的条件，不自行扩展月份、人员或状态筛选。
4. `mcp__moka__search_salary_data_list` 是两段式查询：
   - 第一段 `action="schema"`：取该场景的字段目录、筛选协议、枚举候选与 `schemaHash`。
   - 第二段 `action="query"`：执行查询，`schemaHash` 原样回传。
   - 普通字段构造筛选前先展开字段详情与枚举候选，筛选值形状以字段协议为准，禁止猜测候选值。
   - 只知道业务词时用关键词消歧，只有唯一精确匹配的建议筛选才可直接使用。
5. `mcp__moka__get_salary_submission_activities` 的句柄链：
   - 活动名称不唯一时先用名称消歧动作，多候选时把候选交给用户选择，禁止替用户挑选。
   - `activityId` 来自活动列表或唯一消歧结果，`taskId` 来自任务列表，均不得猜测。
   - 查活动详情、任务列表、填报明细都要先有 `activityId`。
6. 月份用 YYYY-MM；相对时间（「这个月」「上月」）先按用户所在时区换算成绝对月份再调用，回答里说明实际查询的月份。
7. 结果按页返回，只汇报实际取到的范围；需要完整名单就继续翻页，有下一页标记时递增页码。

## 结果与权限

- 薪酬数据敏感：仅具备薪酬管理权限的账号可用，结果只在当前账号权限范围内返回；无权限时工具会明确提示，如实转述，不要绕行。
- 空结果一律按「未返回数据」处理：可能是条件过严或范围内确实没有记录，不得反推为无权限，也不要断言「确实没有」。
- 工具返回的 notices 与 message 如实转达，先读 notices 与单位再组织回答。
- 填报明细已剔除敏感列，下载链接不会返回；结果仅供权限范围内只读核对，不要向用户许诺提供被剔除的内容。
- 填报任务的流程状态以返回的中文说明为准转述，不要按数字状态值自行解释。
- 金额字段为 null 表示未返回该口径，不要按 0 转述。

## 安全边界

- 回答时不要主动扩散薪酬数值：按用户问题的最小范围呈现，不把与问题无关的员工薪酬带进回答，也不把某位员工的薪酬转述给无关的人。
- 不向用户展示访问令牌、内部标识符或原始技术响应；活动与任务的标识句柄只用于串联工具，不出现在回答里。
- 不虚构工具未返回的字段；电话、证件、头像等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 全部只读：不支持导出、配置、编辑或提交任何薪酬数据；用户要改数据时引导其在 Moka 页面操作。
