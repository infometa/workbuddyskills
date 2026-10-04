> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# chart-stat / data-stat-ex（图表统计/数据统计扩展）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。本页含 chart-stat(图表统计)与 data-stat-ex(数据统计扩展)两个相似服务。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、chart-stat（图表统计）

- **功能**：图表/看板统计服务，主备(CHECK_MASTER_STATUS)，按 SERVICE_NAME 区分。
- **日志**：`chart-stat/chart-stat.log`+`error_chart-stat.log`（⚠️无 fatal）。
- **故障**：统计数据不更新→优先确认主备角色(备机不执行统计)与数据源。串联字段 SERVICE_NAME。

---

## 一、data-stat-ex（数据统计扩展）

- **功能**：扩展数据统计服务(在线设备数等)，主备。
- **日志**：`data-stat-ex/data-stat-ex.log`+`error_data-stat-ex.log`（⚠️无 fatal）。
- **故障**：统计缺失→确认主备角色与依赖数据源。串联字段 服务名(主备键)。

---

## 二、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> 来源：代码实锤(chart_stat/src、data_stat)。库：pcmgr_enterprise（推断）。**只用下列表名。**
- **account_login_info**（登录统计）、**device_info**（设备统计）、**compliance_inspect_status**（合规状态）
- **chart_stat_online_users**、**log_stat_compliance_inspect_*_main**、**log_stat_process_violation_main**、**log_stat_service_violation_main**（各类统计主表）
> 图表/数据统计；统计主表 log_stat_*_main。