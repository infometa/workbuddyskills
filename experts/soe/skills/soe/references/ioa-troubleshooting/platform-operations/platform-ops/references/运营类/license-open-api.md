> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# license-open-api（授权查询/操作 API）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。license-open-api = 授权查询/操作 API。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（按 mid 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

license-open-api = **授权查询/操作 API**。GrantDevicesAuth(手动申请授权)与 RevokeDevicesAuth(手动回收)。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/license-open-api/license-open-api.log` |
| 错误 | `.../license-open-api/error_license-open-api.log` |
| fatal | `.../license-open-api/fatal_license-open-api.log` |

### 串联查询字段：mid、authLicenseDomainId/licenseDomainId、tenantId。

---

## 一、功能逻辑：手动授权 GrantDevicesAuth / 回收 RevokeDevicesAuth，下游调 license-process。

---

## 二、故障场景库

### 场景 A：授权批量失败
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：入参非法/授权域校验不过
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> license-open-api 本身不持表。授权真源：**license**（见 license 页）。