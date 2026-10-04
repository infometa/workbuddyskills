> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# account-sync（账号同步任务执行器）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。account-sync = 账户同步任务执行器（将身份源数据落入 IOA 正式账号表）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字，按 TaskId/tenant_id 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位 + 同步链路（重要）

account-sync = **账号同步任务执行器**（入库段）。按 ImportType 分发到各外部身份源适配器（AD/openldap、企微、IAM、SCIM 等），从源端拉组织/账户**落入 IOA 正式账号表**。

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> **"账号没同步过来"分两段判断**：先查 datasync（采集段）→再查 account-sync（入库段），共同串联 tenant_id。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/account-sync/account-sync.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/account-sync/error_account-sync.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/account-sync/fatal_account-sync.log` |

### 串联查询字段

`TaskId`、`source`(ImportType)、`tenant_id`(默认 on-premise)、`user_id`、`IdentifySourceId`、`request_id`；上游 topic `IOA_MINIIAM`。

---

## 一、功能逻辑（正常怎么工作）

两条入口：① tRPC `SubmitAccountSyncTask` 手动提交同步任务；② `MiniIamConsumer` 消费 datasync 发的 `IOA_MINIIAM`，为身份源目录创建 scimex 类型任务投入 taskChan。RunSyncJob 按 source%100 算 accountImportType（miniIAM +10000），按适配器类型分支拉源端组织/账户落正式表，分全量/增量。

---

## 二、故障场景库

### 场景 A：同步任务提交/执行失败
**① 功能逻辑**：SubmitAccountSyncTask 校验 ImportType 并投任务。
**② 大概原因**：不支持的同步类型 / 任务正在运行中(同组织不允许并发) / 任务数超限。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：AD/LDAP 拉取失败
**② 大概原因**：域控不通/账密错/baseDN 错 / DN 解析失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：MiniIAM 消息消费失败（datasync→account-sync 断点）
**① 功能逻辑**：MiniIamConsumer 消费 IOA_MINIIAM 后建 scimex 任务。
**② 大概原因**：消息解析失败 / 账号配置缺失 / 建任务失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 D：同步执行但无数据
**② 大概原因**：源端 Orgmap/Staffmap 为空。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. **"账号同步不生效"必分两段查**：datasync(采集段)→account-sync(入库段)，共同串联 tenant_id。
3. 串联用 TaskId/source/tenant_id；MiniIAM 链路断点用 IdentifySourceId 回查 datasync。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **accounts**（同步落地的账号正式表）：`id`、`user_id`、`user_name`、`group_id`、`source`(来源)、`status`、`itime`、`utime`
- **account_groups**（同步落地的组织分组）：`id`、`name`、`parent_id`、`source`、`itime`、`utime`
- **security_groups** / **security_group_account_relation**（安全组及关联）
- **account_organization_sync** / **security_organization_sync**（组织同步记录）
> 账号同步链：datasync采集入中间库 → account-sync 消费写入 accounts/account_groups 正式表。账号“变少/消失”对比 source 与同步记录。