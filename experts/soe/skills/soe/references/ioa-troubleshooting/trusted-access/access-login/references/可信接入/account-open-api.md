> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# account-open-api（账号管理 HTTP OpenAPI）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。account-open-api = 控制台/对外的本地账号管理 HTTP OpenAPI。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

account-open-api = **本地账号管理 HTTP OpenAPI**：账号增删改查、批量导入、启停用、重置密码、离职管理、账号组/虚拟组管理、在线/活跃统计。分层 controller(协议转换+参数检查)/service/mapper/dao。路由前缀 `/capi/Assets/Account/*`。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info，含收发请求 debuglog） | `/data/services/pcmgr_enterprise/logs/account-open-api/account-open-api.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/account-open-api/error_account-open-api.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/account-open-api/fatal_account-open-api.log` |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

`RequestId`（CommonHeader，首选）、`UserId`、`AccountId(Id)`、`GroupId`/`GroupIds`、`VirtualGroupIds`、`tenant_id`。

> 配置启用 debuglog：收发请求都会打印（error 非 nil 时打 error 级别），用 RequestId 可拉出一次完整调用。

---

## 一、功能逻辑（正常怎么工作）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 二、故障场景库

### 场景 A：接口返回 InvalidParameter.RequestParam（参数校验不过）
**① 功能逻辑**：handler 先做参数校验。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：创建/修改成功但落库失败
**① 功能逻辑**：校验后调 Dao 层写 DB。
**② 大概原因**：DB 连接异常 / 约束冲突（如 user_id 重复）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：查账号列表查不到（DescribeSimpleLocalAccounts）
**① 功能逻辑**：按 account_ids/group_ids/virtual_group_ids 过滤查询。
**② 大概原因**：三类 id 全空 / QuerySimpleAccountIds 调 ou-query 失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 D：批量导入账号失败
**① 功能逻辑**：ImportLocalAccount 批量校验+落库。
**② 大概原因**：导入行参数不合规 / DB 异常。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

命中场景后固定四段：**【功能逻辑】【大概原因】【排障方式】【排不出来给技术人员的信息】**。

铁律：
1. 只引用本库真实关键字/路径不编造；具体 errorcode 常量未逐一收录，未收录的告知需升级研发。
2. 串联查询首选 **RequestId**（debuglog 会打收发），辅以 UserId/GroupId。
3. 查询类问题常牵连 ou-query，必要时转 ou-query 排查。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
