# 字段配置参考（FIELDS_CONFIG）

> 本文件按 finalRole × from_type × type 列出各场景下的实际渲染字段。
> 标记说明：✱=必填，🔀=条件显示，🔧=系统自动填充字段（由系统自动写入，无需用户操作）

## 目录

- [跟进对象类型](#跟进对象类型)
- [国内版 — Sales（销售）](#国内版--sales)
- [国内版 — Owner（售前架构师）](#国内版--owner)
- [国内版 — Subcontracting（分包）](#国内版--subcontracting)
- [海外版 — gw_pd_sa_sg（产研架构师）](#海外版--产研架构师)
- [海外版 — gw_poc_engineer（POC测试）](#海外版--poc测试)
- [海外版 — gw_presales_sa（售前架构师）](#海外版--海外售前架构师)
- [海外版 — gw_dsales（TCI销售）](#海外版--tci销售)
- [必填规则汇总](#必填规则汇总)

---

## 跟进对象类型

| from_type | 含义 | 适用角色 |
|-----------|------|---------|
| 1 | 客户 | Sales / Owner / gw_dsales / gw_presales_sa |
| 2 | 商机 | Sales / Owner / gw_dsales / gw_presales_sa |
| 12 | 线索 | Sales / gw_dsales |
| 10 | 产研商机 | gw_pd_sa_sg / gw_poc_engineer |
| 11 | POC | gw_pd_sa_sg / gw_poc_engineer |
| 13 | 合作伙伴 | Subcontracting |

---

## 国内版 — Sales

### 客户/商机 × 拜访（type=10000）
```
签到打卡(visit_check_ins_id)✱、跟进对象(customer_name)✱、跟进方式(type)✱、
拜访对象(contact_info)✱、腾讯会议号(meeting_code)、会议创建人(meeting_creator)、
沟通内容(conclusion)✱、下一步计划(plan)✱、附件(attachments)、
拜访时间(visit_time)✱、协同跟进人(joint_follow_person)、跟进人(creator)🔧
```

### 客户/商机 × 跟进进展（type=10002）
```
签到打卡(visit_check_ins_id)、跟进对象(customer_name)、跟进方式(type)、
腾讯会议号(meeting_code)、会议创建人(meeting_creator)、
项目当前进展(current_progress)✱、下一步计划(plan)✱、痛点问题(pain_problem)、
项目主要风险点(main_risk)、附件(attachments)、拜访时间(visit_time)✱、
协同跟进人(joint_follow_person)、跟进人(creator)🔧
```

### 线索 × 拜访（type=10000）
```
跟进对象(lead_name)✱、跟进方式(type)✱、签到打卡(visit_check_ins_id)✱、
跟进渠道(follow_channel)、是否继续跟进(continue_follow)✱、
是否已建联(has_established_contact)✱🔀、客户意向(customer_intention)✱🔀、
腾讯会议号(meeting_code)🔀、会议创建人(meeting_creator)🔀、
沟通内容(conclusion)🔀、附件(attachments)🔀、
拜访时间(visit_time)✱、放弃跟进原因(abandon_follow_reason)✱🔀、跟进人(creator)🔧
```

### 线索 × 跟进进展（type=10002）
```
跟进对象(lead_name)✱、跟进方式(type)✱、
跟进渠道(follow_channel)、是否继续跟进(continue_follow)✱、
是否已建联(has_established_contact)✱🔀、客户意向(customer_intention)✱🔀、
腾讯会议号(meeting_code)🔀、会议创建人(meeting_creator)🔀、
项目当前进展(current_progress)🔀、附件(attachments)🔀、
拜访时间(visit_time)✱、放弃跟进原因(abandon_follow_reason)✱🔀、跟进人(creator)🔧
```

> 🔀 线索条件规则：
> - continue_follow=是 → 显示 has_established_contact、customer_intention、conclusion/current_progress、meeting_code、meeting_creator、attachments
> - continue_follow=否 → 显示 abandon_follow_reason
> - ⚠️ 线索下不显示协同跟进人

---

## 国内版 — Owner

### 客户/商机 × 拜访（type=10000）
```
签到打卡(visit_check_ins_id)、跟进对象(customer_name)✱、跟进方式(type)✱、
纪要类型(summary_type)、拜访对象(contact_info)✱、腾讯会议号(meeting_code)、
会议创建人(meeting_creator)、沟通内容(conclusion)✱、下一步计划(plan)、
拜访时间(visit_time)✱、拜访目标(visit_target)、是否达成目标(is_get_target)、
会议地址(meeting_address)、协同跟进人(joint_follow_person)、附件(attachments)、
跟进人(creator)🔧
```

### 客户 × 跟进进展（type=10002）
```
签到打卡(visit_check_ins_id)、跟进对象(customer_name)、跟进方式(type)、
项目当前进展(current_progress)✱、下一步计划(plan)✱、项目主要风险点(main_risk)、
产品卡点(stuck_point)、协同跟进人(joint_follow_person)、附件(attachments)、
拜访时间(visit_time)、跟进人(creator)🔧
```
> ⚠️ Owner 客户×跟进进展无拜访时间字段，拜访时间选填

### 商机 × 跟进进展（type=10002）
```
签到打卡(visit_check_ins_id)、跟进对象(customer_name)、跟进方式(type)、
腾讯会议号(meeting_code)、会议创建人(meeting_creator)、
项目当前进展(current_progress)✱、下一步计划(plan)✱、项目主要风险点(main_risk)、
产品卡点(stuck_point)、协同跟进人(joint_follow_person)、附件(attachments)、
拜访时间(visit_time)、跟进人(creator)🔧、创建时间(create_time)🔧
```
> ⚠️ Owner 商机×跟进进展无拜访时间字段，拜访时间选填

---

## 国内版 — Subcontracting

### 合作伙伴 × 拜访（type=10000，唯一支持模式）
```
跟进对象(subcontractor_partner_name)✱、跟进方式(type)✱、
拜访对象(contact_info)✱、协同跟进人(joint_follow_person)、
沟通内容(conclusion)✱、下一步计划(plan)✱、合作背景(cooperation_background)、
附件(attachments)、拜访时间(visit_time)✱、跟进人(creator)🔧
```

---

## 海外版 — 产研架构师

### 产研商机/POC × 拜访（type=10000）
```
签到打卡(visit_check_ins_id)、跟进对象(product_opp_name/private_poc_name)、跟进方式(type)、
拜访对象(contact_info)✱、协同跟进人(joint_follow_person)✱、
沟通方式(communication_mode)✱、产品跟进类型(product_follow_type)✱、
沟通内容(conclusion)✱、下一步计划(plan)、风险问题(main_risk)、
拜访时间(visit_time)✱、沟通时长h(invest_time)、附件(attachments)、
行销侧是否可见文档(document_visible)、跟进人(creator)🔧、创建时间(create_time)🔧
```

### 产研商机/POC × 跟进进展（type=10002）
```
跟进对象(product_opp_name/private_poc_name)、跟进方式(type)、
产品跟进类型(product_follow_type)✱、项目当前进展(current_progress)✱、
下一步计划(plan)、项目主要风险点(main_risk)、投入时间h(invest_time)、
附件(attachments)、行销侧是否可见文档(document_visible)、拜访时间(visit_time)✱、
跟进人(creator)🔧、创建时间(create_time)🔧
```

---

## 海外版 — POC测试

字段配置与产研架构师完全相同，但 product_follow_type 枚举不同 → 见 ENUMS.md

---

## 海外版 — 海外售前架构师

### 客户/商机 × 拜访（type=10000）
```
签到打卡(visit_check_ins_id)、跟进对象(customer_name)✱、跟进方式(type)✱、
纪要类型(summary_type)、拜访对象(contact_info)✱、沟通内容(conclusion)✱、
下一步计划(plan)、拜访时间(visit_time)、拜访目标(visit_target)、
是否达成目标(is_get_target)、会议地址(meeting_address)、
协同跟进人(joint_follow_person)✱、附件(attachments)、跟进人(creator)🔧
```
> ⚠️ 协同跟进人必填；无腾讯会议号字段

### 客户/商机 × 跟进进展（type=10002）
```
跟进对象(customer_name)、跟进方式(type)、
项目当前进展(current_progress)✱、下一步计划(plan)✱、
项目主要风险点(main_risk)、产品卡点(stuck_point)、
协同跟进人(joint_follow_person)、附件(attachments)、跟进人(creator)🔧
```
> ⚠️ 无拜访时间字段

---

## 海外版 — TCI销售

字段配置与国内版 Sales 完全相同。

---

## 必填规则汇总

### 通用必填规则
```
下一步计划必填 = finalRole 为 Sales 或 type 为 10002 或 finalRole 为 Subcontracting
拜访时间必填 = 非（finalRole 为 Owner 且 type 为 10002）的情况
沟通内容/项目当前进展必填 = 非线索场景（from_type 不为 12）
```

### 各场景必填字段速查

| 场景 | 必填字段 |
|------|---------|
| Sales × 客户/商机 × 拜访 | **visit_check_ins_id**, contact_info, conclusion, plan, visit_time |
| Sales × 客户/商机 × 跟进进展 | current_progress, plan, visit_time |
| Sales × 线索 × 拜访 | **visit_check_ins_id**, continue_follow, visit_time; 是→has_established_contact, customer_intention; 否→abandon_follow_reason |
| Sales × 线索 × 跟进进展 | continue_follow, visit_time; 是→has_established_contact, customer_intention; 否→abandon_follow_reason |
| Owner × 客户/商机 × 拜访 | contact_info, conclusion, visit_time |
| Owner × 客户/商机 × 跟进进展 | current_progress, plan（拜访时间选填） |
| Subcontracting × 合作伙伴 × 拜访 | contact_info, conclusion, plan, visit_time |
| 海外产研/POC × 拜访 | contact_info, joint_follow_person, communication_mode, product_follow_type, conclusion, visit_time |
| 海外产研/POC × 跟进进展 | product_follow_type, current_progress, visit_time |
| 海外售前 × 拜访 | contact_info, conclusion, joint_follow_person |
| 海外售前 × 跟进进展 | current_progress, plan |
