---
name: tsec-risk
description: Tsec 安全中心风险查询与处理指南。当用户查询安全风险、风险类型、修复指引，或需要发起延期/误报/加白/转单时使用。
---

# Tsec 安全中心使用指南

## 核心原则

1. 凡是「查我的 XX」，**必须先调用 `get_current_user` 获取服务端认证的真实身份**，再以其作为 filter_value 查询，不要从其他来源推断用户 RTX 名。
2. 查询结果中存在未处理（risk_status=0）风险时，收集 `_risk_type` 去重后调用 `GetRepairGuide`，连同风险列表一起输出。
3. 延期（DelayApply）、误报（MisreportApply）、加白（WhiteApply）、转单（TransferApply）均为**写操作**：第一次调用 `confirmed=False` 只拿预览，向用户复述预览并获得明确同意后，才能以相同参数 `confirmed=True` 执行。
4. 0 条结果直接如实回复"无数据"，不要擅自扩大查询范围（可能越权展示）。

## 工具速查

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `get_current_user` | 获取当前登录身份 | 无参数 |
| `LookupRiskType` | 风险类型模糊匹配 | keyword（中文/英文均可） |
| `LookupBG` | BG 事业群名称匹配 | keyword（如 wxg、csig） |
| `GetUserOrgInfo` | 用户 OA 组织架构 | staff_name（RTX 名） |
| `SelectRiskList` | 风险列表查询 | filter_type（rtx/org_name）、filter_value、risk_status、risk_level、count_only、sort_order |
| `SelectRiskStatusChangeRecord` | 风险状态变更时间线 | risk_uuid + risk_type |
| `GetRepairGuide` | 修复指引 | risk_type（精确标识，可传列表） |
| `DelayApply` | 延期申请（写） | risk_type + risk_uuid_list + confirmed |
| `MisreportApply` | 误报反馈（写） | risk_type + risk_uuid_list + confirmed |
| `WhiteApply` | 加白申请（写） | risk_type + risk_uuid_list + confirmed |
| `TransferApply` | 转单申请（写） | risk_type + risk_uuid_list + confirmed |

## 典型查询模式

- 「查我的风险」→ `get_current_user` 拿 staff_name → `SelectRiskList(filter_type="rtx", filter_value=<staff_name>)`
- 「查 XX 部门的风险」→ 用 `LookupBG` 补全 BG 全称 → `SelectRiskList(filter_type="org_name", filter_value=["/BG全称/..."])`
- 「按类型统计」→ `SelectRiskList(count_only=true)`
- 用户提到风险类型时，先用 `LookupRiskType` 校验该类型是否已开启，只有返回的 risk_type 才能传给 SelectRiskList
- 用户要"最近的风险"时传 `sort_order="desc"`

## 输出要求

- 风险列表以表格呈现：等级、风险名称、实例、IP、地域、状态、修复期限。
- 修复期限已过的风险要明确标注超期。
- 高危风险如有敏感数据、非常规操作人（如外包账号）记录，需单独提示。
