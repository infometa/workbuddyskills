> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# devices（设备核心业务 Web+v2/v3）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。devices = 设备域最重的业务服务（Web 端增删改查+v2/v3 分组计算）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

devices = **设备核心业务**。Web 端设备/分组增删改查、v2/v3 分组计算与设备迁移、设备清理、账号同步、license 校验。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/devices/devices.log` |
| 错误 | `.../devices/error_devices.log` |
| fatal | `.../devices/fatal_devices.log` |

### 串联查询字段：`mid`、分组 id、账号 id、`tenantId`。

---

## 一、功能逻辑：Web 端设备/分组 CRUD；v2/v3 分组计算与设备迁移；设备清理、账号同步、license 校验。

---

## 二、故障场景库

### 场景 A：设备/分组 Web 操作报错
**② 大概原因**：业务校验/DB 异常。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：v3 分组计算/设备迁移异常
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> ⚠️ errcode 包与 logicv2/groupmgr/cachemgr 本页未展开，需深挖。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> 来源：代码实锤(devices/src、backend device-mgr)。库：pcmgr_enterprise（推断）。**只用下列表名，禁止编造。**

- **devices**（终端主表）、**device_info**（详情）（字段见 device-query 页）
- **groups**（终端分组树）：`id`、`parent_id`、`name`、`id_path`、`name_path`、`ostype`
- **group_org** / **group_org_device** / **group_path_list**（终端组织关系）
- **device_move_log**（设备移动日志）、**device_virtual_groups** / **device_virtual_group_to_device**（虚拟分组）
- **accounts**（关联登录账号）、**system_config**
> 终端分组看 groups（注意与 account_groups 组织分组区分）。