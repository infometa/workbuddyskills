> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# server-configs（服务端配置下发）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。server-configs = 给终端下发“应连接哪些服务器地址”的服务。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字，按 mid/servertype 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/server-configs/server-configs.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/server-configs/error_server-configs.log` |
| fatal | `/data/services/pcmgr_enterprise/logs/server-configs/fatal_server-configs.log` |

### 串联查询字段

`RequestId`、`servertype`、客户端 IP、`mid`、`set_id`、`grayscale_strategy_id`；DB 表 `server_address_list`/`grayscale_strategy_list`。

---

## 一、功能逻辑（正常怎么工作）

启动后多后台循环：系统配置更新(60s)、服务器地址更新(60s)、灰度策略更新(2min)。doUpdateServerAddress 靠 CheckDBTableModify("server_address_list") 判变更，变更才重载并双 buffer 热切换。下发时按客户端 IP 落在 [startip,endip] 区间 + mid 命中的灰度策略过滤。

---

## 二、故障场景库

### 场景 A：终端拿不到某类服务器地址
**② 大概原因**：该 ServerType 无 enable 记录 / 客户端 IP 不落在任何 [startip,endip] 区间 / 灰度策略 ID 不匹配 / 行数超 30 被截断。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：配置改了不生效
**② 大概原因**：CheckDBTableModify 未检测到变更（版本/时间戳未更新）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：灰度不生效
**② 大概原因**：策略 status≠1 / strategyType 非1/2 / valuejson 解析失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

铁律：
1. 只引用本库真实关键字/路径不编造；运行时错误关键字未全部逐条定位，先按 error 日志排查。
2. 串联用 servertype+客户端IP+mid；"拿不到地址"先查 IP 区间与灰度匹配。
3. "改了不生效"看是否有 Found modifications / UpData Server Address Suc。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
