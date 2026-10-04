> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# data-domain（数据管理域权限隔离）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。data-domain = 数据管理域权限隔离。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（⚠️日志路径特殊）

data-domain = **数据管理域权限隔离**。对外 GetAccessIDList(返回用户可访问资源 id 列表)、CheckIDListPrivilege(校验 id 访问权限)；目前资源类型注册了设备组 DeviceGroupType。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | ⚠️ `/data/services/pcmgr_enterprise/public/service/cam-mgr/data-domain/logs/data-domain.log` |

> ⚠️ **路径在 public/service/ 层、仅主日志、无 error/fatal**。

### 串联查询字段：UserId、DataType(DeviceGroupType)。

---

## 一、功能逻辑：GetAccessIDList 返回用户可访问资源 id 列表；CheckIDListPrivilege 校验访问权限。

---

## 二、故障场景库

### 场景 A：用户看不到本应可见的数据
**② 大概原因**：GetAccessIDList 返回列表偏小/为空。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：越权访问被拦
**③ 排障方式**：看 CheckIDListPrivilege 判定；检查资源类型与 domain 配置。
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

> 来源：代码实锤(backend)。**只用下列表名。**
- **am_domain** / **am_module** / **am_role** / **am_role_module**（管理域/模块/角色/角色模块）：`domain_name`、`parent_id`、`role_name`、`module_id`、`role_id`、`readwriteable`
> 数据管理域权限隔离；管理域看 am_domain。日志在 public/service 层。