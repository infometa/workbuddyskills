> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# dlp-open-api（DLP 对外 API）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。dlp-open-api = DLP 能力对外 HTTP API。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

dlp-open-api = **DLP 对外 API**。含 dlp-security / dlp-flyback(外发回捞) / dlp-analysis / dlp-file-record-config 等子模块。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/dlp-open-api/dlp-open-api.log` |
| 错误 | `.../dlp-open-api/error_dlp-open-api.log` |
| fatal | `.../dlp-open-api/fatal_dlp-open-api.log` |

### 串联查询字段：RequestId、tenant_id、PolicyId/RuleId。

---

## 一、功能逻辑：DLP 能力对外 HTTP API，多子模块(security/flyback/analysis/file-record-config)。

---

## 二、故障场景库

### 场景 A：接口报错
**③ 排障方式**：在 `error_dlp-open-api.log` 按对应子模块 controller/service 的 Errorf 定位；按子路由定位。
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

> dlp-open-api 本身不持表，读写 DLP 主链。
> 数据分级/数据地图：**dlp_data_level**/**dlp_data_category**；告警：**dlp_alarm**（见 dlp-alarm/dlp-server 页）。