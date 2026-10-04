> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# device-open-api（设备开放 API）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。device-open-api = 设备对外开放 API（明细导出/匹配/定时任务）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

device-open-api = **设备开放 API**。设备明细导出、按账号/多分组匹配、组织架构映射；定时任务 TimerDeviceUpload/TimerCheckDuplicateMid。依赖极多下游。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/device-open-api/device-open-api.log` |
| 错误 | `.../device-open-api/error_device-open-api.log` |
| fatal | `.../device-open-api/fatal_device-open-api.log` |

### 串联查询字段：`mid`、分组 id、账号 id、`tenantId`。

---

## 一、功能逻辑：对外提供设备明细导出/匹配 API，并跑 TimerDeviceUpload/TimerCheckDuplicateMid 定时任务。

---

## 二、故障场景库

### 场景 A：设备明细导出/查询失败
**② 大概原因**：入参问题或 SQL/下游异常。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> ⚠️ 错误码表在 devicedetail/error.go，本页未展开。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> device-open-api 是设备开放API，本身不持表，读写同 device 主链。
> 设备真源：**devices** / **device_info**（见 device-query 页）。