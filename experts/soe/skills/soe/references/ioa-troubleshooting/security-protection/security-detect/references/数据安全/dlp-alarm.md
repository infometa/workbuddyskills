> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# dlp-alarm（告警聚合）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。dlp-alarm = DLP 告警聚合。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

dlp-alarm = **DLP 告警聚合**。定时聚合 DLP 告警并落库。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/dlp-alarm/dlp-alarm.log` |
| 错误 | `.../dlp-alarm/error_dlp-alarm.log` |
| fatal | `.../dlp-alarm/fatal_dlp-alarm.log` |

### 串联查询字段：tenant_id、content。

---

## 一、功能逻辑：定时 AlarmCache 聚合告警→saveAlarm/tipFileAlarm 落库；OnData 接数据。

---

## 二、故障场景库

### 场景 A：告警缺失/延迟
**② 大概原因**：定时任务异常或 DB 写失败。
**③ 排障方式**：在 `error_dlp-alarm.log` 看 saveAlarm/saveFileAlarm 报错；查定时任务是否执行、DB 写入。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。


---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **dlp_alarm**（DLP告警，排障核心宽表）：`dlp_alarm_id`、`dlp_item_id`、`data_rule_id`、`alarm_name`、`account_id`/`account_name`、`device_name`、`action_type`、`control_channel`/`control_channel_type`（外发渠道）、`data_level`、`category_name`、`begin_time`/`end_time`/`client_report_time`、`content`
- **dlp_alarm_comment** / **dlp_alarm_policy** / **dlp_alarm_policy_scope**（告警批注/策略/范围）
> “该拦没拦/漏检”、外发告警都看 dlp_alarm；按 account_id/device_name + 时间段查。