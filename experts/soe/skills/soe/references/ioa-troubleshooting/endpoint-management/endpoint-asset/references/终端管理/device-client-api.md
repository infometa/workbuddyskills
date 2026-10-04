> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# device-client-api（设备端 HTTP API）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。device-client-api = 面向客户端的终端管理 HTTP API 入口（gin）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

device-client-api = **设备端 HTTP API 网关**（gin）。面向客户端的终端管理(terminal_manage) API 入口。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/device-client-api/device-client-api.log` |
| 错误 | `.../device-client-api/error_device-client-api.log` |
| fatal | `.../device-client-api/fatal_device-client-api.log` |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 一、功能逻辑：gin HTTP 服务，面向客户端提供 terminal_manage 类 API。

---

## 二、故障场景库

### 场景 A：终端管理 API 报错
**② 大概原因**：业务处理异常（logic/terminal_manage）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> ⚠️ 业务在 logic/terminal_manage，本页未深入，具体错误码需看该目录。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> device-client-api 是设备端 HTTP API，主要转发/读取，本身不直接持表。
> 设备真源在 **devices** / **device_info** 表（见 device-query 页）。