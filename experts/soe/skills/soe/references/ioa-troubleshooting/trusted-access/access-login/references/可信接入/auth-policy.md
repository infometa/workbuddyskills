> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# auth-policy（账号安全策略）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。auth-policy = iOA 账号安全/认证策略下发服务。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> ⚠️ 职责边界：auth-policy **不做资源级 allow/deny 判定**（那是 ngn-query/ngn-rule 的职责），它只下发账号/认证侧策略。

对外接口：`OnData`（短/长连接 CMD 6627/6628）、`GetUserAccountSecurityPolicy`(RPC)、`GetUserAuthSecurityPolicy`(RPC 终端认证配置)。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/auth-policy/auth-policy.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/auth-policy/error_auth-policy.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/auth-policy/fatal_auth-policy.log` |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

`RequestId`、`Uid`、`GroupId`、`PolicyHash`、CMD(6627/6628)、`mid`。

---

## 一、功能逻辑（正常怎么工作）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 二、故障场景库

### 场景 A：账号安全策略查询失败 / 策略不生效

**① 功能逻辑**：按 uid/groupId 查账号安全策略缓存返回。
**② 大概原因**：uid 为空 / 账号策略缓存未加载（Cache is nil）/ 参数非法 / businessList 为空。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

| 日志关键字 | 代表根因 | 下一步 |
|---|---|---|
| `interauthpolicy.GetAccountSecurityPolicy fail`（CMD 6627） | 账号安全策略查询失败 | 看下面细分 |
| `... AccountSecurityPolicyAccountCache is nil` | 账号策略缓存未加载 | 查策略同步 |
| `Uid is nil.` | 请求缺 uid | 查调用方 |
| `Query auth policy param error` / `GroupId or Uid must be gt than 0` | 参数非法 | 校验 uid/groupId |
| `... BusinessList is nil` | 请求 businessList 空 | 查客户端入参 |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：认证策略查询失败（GetUserAuthSecurityPolicy）

**① 功能逻辑**：返回终端认证配置（PC/Mobile 认证源等）。
**② 大概原因**：内部查询失败 / 按 uid 查失败。
**③ 排障方式**：在 `error_auth-policy.log` 搜 `GetUserAuthSecurityPolicy failed by interreq:%+v` / `GetUserAuthSecurityPolicy Failed by Uid:%d`。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：CMD 报文处理失败（OnData）

**① 功能逻辑**：短/长连接 CMD 6627/6628 取数并解析。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
**③ 排障方式**：在 `error_auth-policy.log` 搜 `OnData, CMD:%d, get Data failed` / `OnData requset, parse param/data ... error`（查 mid/报文格式）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

命中场景后固定四段：**【功能逻辑】【大概原因】【排障方式】【排不出来给技术人员的信息】。

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. 串联查询用 **RequestId + Uid**（辅以 GroupId）。
3. **auth-policy 只管账号/认证策略，不做资源权限判定**——"访问某资源无权限"应转 ngn-query，别在这里找。
4. 策略查询失败的头号根因是缓存未同步（`AccountSecurityPolicyAccountCache is nil`）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **auth_security_policy**（账号安全/认证策略）：`id`、`name`、`group_id`、`priority`、`policy_type`；子表含 `policy_id`+`scope_type`+`account_id`/`account_group_id` 及 `terminal_type`+`auth_state`+`auth_switch`
- **account_groups**（读，策略适用范围）、**policy**（读）
> 账号安全策略（二次认证/登录限制等）看 auth_security_policy。