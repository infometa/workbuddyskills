> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# ngn-query（策略权限判定）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。ngn-query = iOA 零信任"用户对资源有无权限"的判定端。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
- `HasUserStrategyAuth`：判用户对 app/url/service 权限，返回 `RetApp/RetUrl/RetService` 三布尔。
- `GetHashPolicy`：按 uid+osType 查策略 hash。
- `OnData`：短连接 CMD 6622/6623 下发策略内容。

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> 注：实际生效逻辑是 `multi-ou/logic/ngn_query_service_multi_ou.go`（旧 logic 已注释）。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/ngn-query/ngn-query.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/ngn-query/error_ngn-query.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/ngn-query/fatal_ngn-query.log` |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

`RequestId`、`Uid`、`OsType`、`ServiceId`、返回 `RetApp/RetUrl/RetService`、`StackTrace`（含 SvrIps）。

---

## 一、功能逻辑（正常怎么工作）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 二、故障场景库

### 场景 A：用户明明该有权限却被判无权（判权返回 false）

**① 功能逻辑**：ngn-query 按 uid 查缓存策略，serviceId 命中授权集才放行。
**② 大概原因**：该 uid 的策略缓存没同步（Cache is nil）/ serviceId 不在用户授权集 / uid 非法。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

| 日志关键字 | 代表根因 | 下一步 |
|---|---|---|
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
| `校验站点权限失败, 无站点权限` / `获取资源Id失败` | serviceId 不在授权集/非法 | 核对 serviceId 与用户策略配置 |
| `Uid is nil, req:...` | 请求未带 uid | 查调用方入参 |
| `Convert uid(string) to int failed` | uid 非数字 | 查客户端传值 |
| `Check NgnPolicy done. reqUid ... retApp ... retService`（正常收尾） | 含判权结果 | 看三布尔值确认是哪类权限没过 |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：判权调用整体失败

**① 功能逻辑**：HasUserStrategyAuth 逻辑层返回 err。
**② 大概原因**：入参问题或缓存异常。
**③ 排障方式**：在 `error_ngn-query.log` 搜 `NgnQueryServiceImpl logic.HasUserStrategyAuth fail`，看同 RequestId 上下文。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：策略 hash 查询失败（GetHashPolicy）

**① 功能逻辑**：按 uid 查策略 hash（客户端用它判断策略是否要更新）。
**② 大概原因**：参数或缓存问题。
**③ 排障方式**：在 `error_ngn-query.log` 搜 `NgnQueryServiceImpl logic.GetHashPolicy fail` / `QueryPolicyByAccountId failed, uid:%d`。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

命中场景后固定四段：**【功能逻辑】【大概原因】【排障方式】【排不出来给技术人员的信息】。

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. 串联查询用 **RequestId + Uid**（辅以 ServiceId）。
3. **判权 false 的头号根因是策略缓存未同步（Cache is nil）**，先查这个再查授权配置。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。


1. 看服务状态：
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

2. 按账号/设备拉权限判定日志（看为何拒绝/放行）：
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

3. 访问策略/资源授权查主库：
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。


---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **resource_to_accounts**（资源授权关系，核心："没授权"看这里）：`id`、`scope_type`、`account_id`/`account_group_id`/`account_virtual_group_id`、`service_id`、`service_area_id`、`resource_type`、`expire_time`、`extra_info`(JSONB)
- **ngn_service_list**（网关资源/服务）：`id`、`service_name`、`service_address`、`service_port`、`protocol`、`area_id`、`enableflag`、`domain_id`
- **resource_inherit_config**（资源继承）：`inherit_type`、`account_id`/`account_group_id`、`service_id`、`resource_type`、`inherit_switch`、`expire_time`
- **policy**（策略主表，读）：`id`、`name`、`status`、`policy_type`
> 判"某账号能否访问某资源"：查 resource_to_accounts 中该 account_id/account_group_id 对该 service_id 有无授权行，注意 expire_time 未过期。
