> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# importDataPkg（离线数据包导入）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。importDataPkg = 离线数据包导入。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

importDataPkg = **离线数据包导入**。主循环收到导入触发后执行 doImport 完成离线数据包导入（接 dataUpdate 的 notifyImportDataPkg）。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/importDataPkg/importDataPkg.log` |
| 错误 | `.../importDataPkg/error_importDataPkg.log` |
| fatal | `.../importDataPkg/fatal_importDataPkg.log` |

### 串联查询字段：businessName、importType、数据包路径。

---

## 一、功能逻辑：主循环收到导入触发→doImport 执行导入。

---

## 二、故障场景库

### 场景 A：导入不执行/失败
**② 大概原因**：doImport 返回 false / 数据包缺失。
**③ 排障方式**：在 `error_importDataPkg.log` 看 doImport 内部报错+触发点；核对数据包路径与 dataUpdate 的通知（notifyImportDataPkg 是否发出）。
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

> importDataPkg 离线数据包导入，主要处理数据包文件，**无业务主表**（写入同 dataUpdate 的 datapkg/config_set）。