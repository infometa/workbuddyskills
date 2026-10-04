> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# policy-calculate（终端策略计算·核心）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。policy-calculate = 终端策略计算核心。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（按 mid 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（工单："策略不生效/没下发"）

policy-calculate = **终端策略计算核心**。按 mid 计算终端应下发的策略：校验 license→合并策略项(账号/账号组/设备/设备组多维度)→授权过滤。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/policy-calculate/policy-calculate.log` |
| 错误 | `.../policy-calculate/error_policy-calculate.log` |
| fatal | `.../policy-calculate/fatal_policy-calculate.log` |

### 串联查询字段：mid（贯穿，配 tenantId/accountId）、policyId、item_id。

---

## 一、功能逻辑：按 mid 计算策略→校验 license→多维度合并策略项→授权过滤→下发。UpdatePolicy 变更通知刷缓存。

---

## 二、故障场景库

### 场景 A：策略不下发（license 问题，高频）
**② 大概原因**：license 过期/无效→策略被过滤。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：策略项缺失不生效
**② 大概原因**：策略项未同步到缓存/本地。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：控制台改了终端没更新
**② 大概原因**：变更通知参数非法→缓存不刷新。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> ⚠ 策略不下发先看 `get license failed`（授权不足会导致策略不算）。终端管控/软件管控的各 module 开关都经本服务→config-query 下发。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **policy**（策略主表）：`id`、`name`、`status`、`priority`、`policy_type`、`policy_sub_type`、`time_effect_type`、`time_start`、`time_end`、`itime`、`utime`
- **policy_item**（策略项，具体开关）：`id`、`name`、`business_id`、`template_id`、`type`、`version`、`data`(JSONB具体配置)
- **policy_template**（策略模板）：`id`、`policy_id`、`ostype`、`domain_id`
- **policy_template_to_{account, account_group, account_virtual_group, device, device_virtual_group, group}**（下发范围关系）：`template_id`、对应实体id、`type`、`time_effect_type`、`time_start`、`time_end`
- **policy_version**（策略版本）、**accounts**/**account_groups**/**devices**/**groups**（读，算生效范围）
> 策略生效范围计算核心。“策略不下发”先看 `get license failed`；具体开关在 policy_item.data(JSONB)。