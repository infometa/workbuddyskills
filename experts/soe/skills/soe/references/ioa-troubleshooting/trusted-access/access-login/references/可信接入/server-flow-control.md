> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# server-flow-control（服务端流控/策略）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。server-flow-control = 接入服务端流控与接入服务器列表/策略 HTTP 服务。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（日志文件+关键字） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

server-flow-control = **接入服务端流控/策略**（HTTP）。按部署角色分工：**总控**主动生成策略(60s)，**二级/ingress** 从总控拉(300s)。总控地址取自 PlatformConfig.MasterControlServer。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/server-flow-control/server-flow-control.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/server-flow-control/error_server-flow-control.log` |

> ⚠️ **无独立 fatal**（只 info+error）。

### 串联查询字段

`RequestId`、部署 tags(ingress/gateway)、`MasterControlServer`、`localServerIP`、rootServers/cacheServers。

---

## 一、功能逻辑（正常怎么工作）

启动判部署角色(IsRootIngress/IsNoLocalDatabase)→起三协程：生成本地策略/同步策略服务器/ingress上报(6h)。总控 watchDBVersionChanged 60s 生成；二级 remoteGenFlowControlPolicy 300s 从总控拉。接入服务器列表经 API 返回。SaaS 模式跳过本地策略生成。

---

## 二、故障场景库

### 场景 A（高频）：masterAddr is empty，二级/ingress 拿不到策略或上报失败
**② 大概原因**：PlatformConfig.MasterControlServer 未配置或为空。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 B：ingress 上报总控失败
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

### 场景 C：策略始终不更新（总控侧）
**② 大概原因**：DB 版本未变 / 本机不是总控（带 gateway tag 会被排除）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

铁律：
1. 只引用本库真实关键字/路径不编造；无 fatal，只看 info+error。
2. **masterAddr is empty 是本服务高频根因**，先查平台 MasterControlServer 配置与部署角色。
3. 串联用部署角色+RequestId。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。
