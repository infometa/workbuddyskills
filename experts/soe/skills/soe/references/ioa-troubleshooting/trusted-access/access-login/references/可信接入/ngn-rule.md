> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# ngn-rule（访问控制规则判定）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。ngn-rule = iOA 零信任访问控制的规则引擎。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

流程：参数校验（Uid/UrlId/Url/OsType/DeviceId 均非空）→ 取设备数据 → control.Exec 执行规则匹配 → 命中则回填 HitRule/Action/RuleId/RuleName/RuleAppGroup/RuleNetworkArea/RuleDeviceCompliance/RuleAccessDate/RuleAccessTime。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/ngn-rule/ngn-rule.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/ngn-rule/error_ngn-rule.log` |

> ⚠️ ngn-rule **只有 info + error 两档，无 fatal 日志**（与其他服务不同）。

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

`RequestId`、`tenantId`(缺省 on-premise)、`Uid`、`UrlId`、`Url`、`AppMd5`、`DeviceId`、`OsType`、返回 `RuleId/RuleName/Action`、`StackTrace`(SvrIp)。

> 本服务有两条**竖线分隔的结构化日志行**，是最好用的串联锚点：
> - 入参：`[CheckNgnRule]|req|<requestId>|<tenantId>|<uid>|<urlId>|<osType>|<appMd5>|<deviceId>|<deviceSecurity>`
> - 结果：`[CheckNgnRule]|res|<requestId>|<tenantId>|<uid>|<urlId>|<code>|<hitRule>|<ruleId>|<ruleName>|<action>`

---

## 一、功能逻辑（正常怎么工作）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 二、故障场景库

### 场景 A：访问被规则拦截 / 规则命中异常

**① 功能逻辑**：control.Exec 逐条匹配访问控制规则，命中返回动作（可能是拒绝/限制）。
**② 大概原因**：命中了某条访问控制规则（拒绝/限制），或规则执行内部错。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：规则检查失败（参数非法 / 内部错）

**① 功能逻辑**：入口校验必填字段；control.Exec 执行规则。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

命中场景后固定四段：**【功能逻辑】【大概原因】【排障方式】【排不出来给技术人员的信息】。

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. 串联查询优先用两条竖线结构化行（`[CheckNgnRule]|req|` / `|res|`），按 RequestId+Uid 定位。
3. ngn-rule **无 fatal 日志**，只查 info + error 两个文件。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> 访问控制规则的策略真源在 **policy** 及资源授权 **resource_to_accounts**（见 ngn-query 页）。