> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# security-open-api（安全域对外 OpenAPI）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。security-open-api = 安全域对外开放 API 入口。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位（⚠️日志命名特殊）

security-open-api = **安全域对外 OpenAPI**。`Run()` 启动服务，含 CSV 导出/URL 生成等能力。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/security-open-api/security-open-api.log` |
| 错误 | ⚠️ **`/data/services/pcmgr_enterprise/logs/security-open-api/err_security-open-api.log`**（前缀是 **err_** 不是 error_） |

> ⚠️ **error 前缀 err_、无 fatal**：崩溃类信息仅在 err_ 与主日志，不要找 fatal_ 文件。

### 串联查询字段：OpenAPI 接口名、导出任务/URL。

---

## 一、功能逻辑：安全域对外 OpenAPI 入口，Run 启动；CSV 导出走 Prepare/WriteToCsv/GenerateURL。

---

## 二、故障场景库

### 场景 A：接口报错/导出失败
**③ 排障方式**：查 `err_security-open-api.log`（注意文件名前缀）；CSV 导出走 Prepare/WriteToCsv/GenerateURL。
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

> security-open-api 本身不持表。盗版检测/正版率走 software-open-api；木马/信誉看 **t_trojan_local**等（见 queryServer 页）。error 文件前缀 err_。