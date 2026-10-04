> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# config-query（策略配置查询代理）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。config-query = 策略配置查询代理（按 mid 查策略版本）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（⚠️配置/日志特殊）

config-query = **策略配置查询代理**。按 mid 查策略版本 QueryPolicyVerByMid（终端据此判断是否需更新策略）。

> ⚠️ **配置用 trpc_go_cvm.yaml（无 .template）**。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/config-query/config-query.log` |
| fatal | ⚠️ **在 devices 目录**：`.../logs/devices/fatal_config-query.log` |

> ⚠️ **仅 info+fatal，无独立 error 日志；fatal 在 devices 目录**。

### 串联查询字段：Mid(核心)、Gid、TenantId。

---

## 一、功能逻辑：按 mid/gid 查策略与版本（QueryPolicyByMid/ByGid/VerByMid）。

---

## 二、故障场景库

### 场景 A：策略版本查失败（终端不拉新策略）
**② 大概原因**：缓存/DB 异常。
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

- **config_set**（配置集）：`set_id`、`templet_id`、`name`、`data`、`pdata`、`ostype`、`time_start`、`time_end`、`itime`、`utime`
- **config_set_mid**（按 mid 下发）：同 config_set 加 `mid`
- **config_templet** / **config_business_set** / **config_group_strategy**（配置模板/业务集/分组策略）
- **policy_query_info** / **policy_version**（策略查询/版本）、**devices**/**groups**（读）、**device_job**
> 按 mid 看实际下发配置：config_set_mid；终端拉到的配置 = policy-calculate 算出的结果落 config_set。