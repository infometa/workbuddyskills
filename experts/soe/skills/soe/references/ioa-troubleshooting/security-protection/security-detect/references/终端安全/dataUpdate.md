> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# dataUpdate（数据包更新分发）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。dataUpdate = 数据包更新分发。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（⚠️目录名差异）

dataUpdate = **数据包更新分发**。⚠️ **app 目录名 `dataUpdate`，但配置/日志目录名为 `data-update`**。doUpdate 按各业务更新开关/自定义更新时间判定，触发数据包更新并 notifyImportDataPkg 通知导入。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/data-update/data-update.log` |
| 错误 | `.../data-update/error_data-update.log` |
| fatal | `.../data-update/fatal_data-update.log` |

### 串联查询字段：businessName、importType、forceUpdate、更新类型 nUpdateType。

---

## 一、功能逻辑：Run 启动→doUpdate 按业务更新开关/自定义更新时间判定→触发数据包更新→notifyImportDataPkg 通知导入。

---

## 二、故障场景库

### 场景 A：数据包不更新/不分发
**② 大概原因**：业务更新开关关闭或更新时间未到。
**③ 排障方式**：查 `data-update.log` 的 setBusinessUpdateSwitch 与 matchUserDefineUpdateTime；核对更新策略配置。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：通知导入失败
**③ 排障方式**：查 `notifyImportDataPkg`；联查 importDataPkg 服务是否收到通知。
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

> 来源：代码实锤(data_update/src)。**只用下列表名。**
- **config_set**（配置集）、**datapkg**（数据包）、**system_config**
> 数据包更新分发；app目录 vs data-update 配置目录要区分。