> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# device-register（设备注册）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。device-register = 设备注册服务（处理客户端 6001 注册、分配/找回 mid、供 conn-sc 鉴权）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字，按 mid/guid 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（工单高频）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/device-register/device-register.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/device-register/error_device-register.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/device-register/fatal_device-register.log` |

### 串联查询字段

`mid`、`guid`、`MachineGuid`、`tenantId`；conn-sc 侧用 `req.Mid`+`caller`。

---

## 一、功能逻辑（正常怎么工作）

客户端发 6001 注册请求 → 校验 GUID/OS 类型 → mid 找回主链路（Step① 机器码 hash 找回、Step② MachineGuid 找回，都 miss 才新建 mid）→ 写库。对外 QueryDeviceRegister 供 conn-sc 鉴权：返回设备注册态（UNREGISTER=无记录/BLOCKED=封禁）。mid 找回受配置 `MidRecoveryCfgOpen` 控制。

---

## 二、故障场景库

### 场景 A：设备注册失败
**② 大概原因**：GUID 为空(RetCode 10) / 无效 OS 类型或租户初始化失败(100) / DB 执行失败(50)。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：conn-sc 说设备未授权/未注册
**① 功能逻辑**：conn-sc 鉴权时调 QueryDeviceRegister 查 mid 注册态。
**② 大概原因**：该 mid 无注册记录(UNREGISTER)或被封禁(BLOCKED)。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：重装后变成新设备（mid 找回失效）
**② 大概原因**：mid 找回两条链路（机器码 hash、MachineGuid）都 miss，或找回配置 `MidRecoveryCfgOpen` 未开。
**③ 排障方式**：看 mid 找回主链路日志（Step①/Step②）与 `LastMid`；注意 `mid_dual_recovery_conflict`（WARN，双钥匙找回冲突，仅告警）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. 串联用 mid/guid/MachineGuid；"conn-sc 说未授权"回本服务查 QueryDeviceRegister。
3. "重装变新设备"看 mid 找回两条链路 + MidRecoveryCfgOpen。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
- **devices**（注册写入终端主表，按 mid/guid）（字段见 device-query 页）
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
