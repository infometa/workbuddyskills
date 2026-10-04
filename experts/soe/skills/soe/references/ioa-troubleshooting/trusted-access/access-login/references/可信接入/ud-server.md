> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# ud-server（定制客户用户目录实时增量接入）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。ud-server = 面向定制客户（国航 AICAF / 中核 CNNC）的用户目录实时增量同步服务（RocketMQ）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字，按 source_id 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

ud-server = **定制客户用户目录实时增量同步**（仅 Master 节点跑）。监听 `identify_sources` 表变化，为对应源启停 RocketMQ 消费者接收增量，处理后经 MQ topic `IOA_MINIIAM` 通知 IOA（下游由 account-sync 消费）。

**客户类型分流**：AICAF（国航）/ CNNC（中核，:org_user 走 org+user、:group 走 app config）。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/ud-server/ud-server.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/ud-server/error_ud-server.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/ud-server/fatal_ud-server.log` |

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

`source_id`（身份源ID）、`tenant_id`、`mid`/`user_id`、RocketMQ `topic`、下游 `IOA_MINIIAM` topic。日志前缀：消费者管理 `[Monitor]`、国航 `[AICAF]`、中核通知 `[Notify]`。

> ⚠️ 仅 Master 节点跑（CHECK_MASTER_STATUS）。

---

## 一、功能逻辑（正常怎么工作）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 二、故障场景库

### 场景 A：定制客户用户/组织不同步（消费者未启动/停掉）
**① 功能逻辑**：Monitor 按 identify_sources 配置动态启停 RocketMQ 消费者。
**② 大概原因**：identify_sources 配置无效；MQ 地址/topic 为空或错；源 type 不识别。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：AICAF（国航）消息解析/落库失败
**① 功能逻辑**：解析 pkgOps/pkgObj/pkgData → IAM_ORG/IAM_USER upsert/del。
**② 大概原因**：pkgData 非数组、operation 非法、DB 写失败、字段映射配错。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。


### 场景 D：中核（CNNC）通知未触发
**① 功能逻辑**：中核 group 按 notify_interval 检查版本变化后推同步结果。
**② 大概原因**：版本未变 / 时间未到 interval / 用户组织数为 0。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

命中场景后固定四段：**【功能逻辑】【大概原因】【排障方式】【排不出来给技术人员的信息】**。

铁律：
1. 只引用本库真实关键字/路径不编造；未收录的告知需升级研发。
2. **本服务仅面向国航 AICAF/中核 CNNC 定制客户**，非定制客户的目录同步看 datasync/account-sync。
3. 串联用 **source_id**；先分清 [Monitor]/[AICAF]/[Notify] 三段。
4. 仅 Master 节点跑，排障先确认节点角色。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
