> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# data-edr-scan（EDR 检测扫描引擎·核心）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。data-edr-scan = EDR 检测扫描引擎（检测→告警→事件图合并→响应）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（按 incident_id/EventUUID/TaskSeq 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（EDR 核心检测）

data-edr-scan = **EDR 检测扫描引擎**。从 pipe 通道批量消费客户端上报→CmdHandler 循环检测→产告警→按租户合并事件图(IncidentGraph)→alertAfterRespond 匹配响应规则并调 task-server 下发处置任务。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/data-edr-scan/data-edr-scan.log` |
| 错误 | `.../data-edr-scan/error_data-edr-scan.log` |

> ⚠️ **无 fatal**。

### 串联查询字段（EDR 告警链）

`incident_id`(Incident.Id)、`EventUUID`/`EventOldUUID`(告警 uuid)、`TaskSeq`(响应任务 seq)、TenantId、Mid。

---

## 一、功能逻辑：pipe 批量消费→CmdHandler process/processBytesData 检测→产告警→按租户合并事件图→alertAfterRespond 匹配响应规则→调 task-server 下发处置。

---

## 二、故障场景库

### 场景 A：检测批处理报错/告警丢失
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。


### 场景 C：响应任务未下发/处置不生效
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

> 来源：代码实锤(ioa-backend/internal/pkg/edr/database, sqlx `db:` 标签)。⭐ **EDR 是独立 PG(pg-edr)+ES，多租户，几乎每张表带 tenant_id**，与主库隔离。**只用下列表名，禁止编造。**

- **edr_incident**（安全事件/告警聚合，核心）：`id`、`tenant_id`、`uuid`、`incident_name`、`risk_level`、`judge_level`、`survey_status`、`first_time`/`last_time`、`event_total`/`terminal_total`/`user_total`、`create_time`/`update_time`
- **edr_event**（原始安全事件）：`id`、`tenant_id`、`incident_id`(→edr_incident.id)、`mid`、`terminal_name`、`account_id`/`ioa_account`、`event_name`、`policy_id`/`policy_name`、`rule_id`/`rule_name`、`risk_level`、`disposal_status`、`occur_time`、`create_time`
- **edr_policy** / **edr_rule** / **edr_white_policy**（策略/规则/白名单）、**edr_evidence**（证据）、**edr_terminal**（终端）
> 告警链按 `incident_id`/`incident_uuid`/`mid` 串联；多租户查询必带 `tenant_id`。