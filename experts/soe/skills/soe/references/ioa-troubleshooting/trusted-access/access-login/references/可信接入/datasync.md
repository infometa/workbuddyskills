> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# datasync（身份源数据采集中转）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。datasync = 身份源数据采集与中转层（落中间库 iamuser/iamorganization/iamgroup）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字，按 IdentifySourceId 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位 + 同步链路（重要）

datasync = **身份源数据采集与中转层**（采集段）。对接 30+ 第三方目录源（钉钉/飞书/企微/AD/SCIM/华润/中核等），拉取/接收源数据规整为组织/用户/组落**中间库**(iamuser/iamorganization/iamgroup)，再通知 account-sync 拿货入正式表。

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/datasync/datasync.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/datasync/error_datasync.log` |

> ⚠️ **无 fatal 日志文件**（模板只到 error 级别）。

### 串联查询字段

`IdentifySourceId`/`sourceId`（最核心）、`tenant_id`、`user_id`、`request_id`；中间库表 `iamuser`/`iamorganization`/`iamgroup`；下游 topic `IOA_MINIIAM`；Push 型失败留档表 `iam_push_fail_log`(SourceID/DataType/RawMsg/LogTime)。

---

## 一、功能逻辑（正常怎么工作）

拉取/接收各身份源(ldap/dingtalk/wecom/lark/scim/authing 等)数据 → 规整为组织/用户/组落中间库 iamuser/iamorganization/iamgroup → 完成后 `NotifyIOASyncSuccess` 向 topic `IOA_MINIIAM` 重试 3 次发消息（下游 account-sync 消费）。另提供 SCIM API 对外接收推送。

---

## 二、故障场景库

### 场景 A：即时同步任务整体失败
**① 功能逻辑**：HandleInstantSyncTask 拉源→写中间库。
**② 大概原因**：查身份源配置失败 / 拉源全量数据失败 / 组织用户组入中间库失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：通知下游失败（account-sync 收不到）
**① 功能逻辑**：完成后发 IOA_MINIIAM 通知。
**② 大概原因**：NSQ 发送失败（重试 3 次仍失）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：同步周期配置非法
**② 大概原因**：cron 表达式错。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 D：Push 型源推送处理失败
**① 功能逻辑**：Push 型源（企微/钉钉推送）失败留档。
**③ 排障方式**：查表 `iam_push_fail_log`（SourceID/DataType/RawMsg/LogTime）；SCIM/source 层错误看对应 source 日志。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

铁律：
1. 只引用本库真实关键字/路径不编造；无 fatal，只看 info+error。
2. **"账号同步不生效"先查 datasync(采集段)，再查 account-sync(入库段)**，共同串联 tenant_id。
3. 串联用 **IdentifySourceId**（核心）；通知下游断点看 `publish topic failed, topic:IOA_MINIIAM`。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **account_group_config**（身份源同步配置）：`id`、`name`、`parent_id`、`aduser`、`adserv`、`addn`、`importtype`(身份源类型)、`source`、`cron`(JSON定时)、`itime`、`utime`
> datasync 从 AD/LDAP/钉钉/飞书/企微 拉数据入中间库、发消息给 account-sync 落正式表(accounts/account_groups)。身份源连接参数看 account_group_config。datasync 本身无 fatal。