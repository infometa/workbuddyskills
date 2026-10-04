> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# device-info（设备信息上报接收·写入侧）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。device-info = 接收客户端各类信息上报按 cmd 分发落库（写入侧）。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式（按 mid/cmd 串联） ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

device-info = **设备信息上报接收·写入侧**。接收客户端各类上报（终端扫描/磁盘/共享文件夹/CPU内存/域信息/安装卸载权限状态等），按 cmd 分发落库。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志（info） | `/data/services/pcmgr_enterprise/logs/device-info/device-info.log` |
| 告警日志 | `/data/services/pcmgr_enterprise/logs/device-info/device-info-warn.log` |
| 错误日志 | `/data/services/pcmgr_enterprise/logs/device-info/error_device-info.log` |
| fatal | `.../device-info/fatal_device-info.log` |

### 串联查询字段

`mid`、`cmd`（如 7263=权限上报/7007=卸载状态/install report=安装状态）、`guid`。

---

## 一、功能逻辑

MQ/长连接收到各类上报 → 入口 `on data mid = ... cmd = ...` 按 cmd 分发到各 handler 落库。

---

## 二、故障场景库

### 场景 A：上报信息未落库/处理失败
**② 大概原因**：某 cmd 处理失败（报文解析/DB 写）。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

> ⚠️ 各 cmd 处理器未逐一展开统一错误码表，按 mid+cmd 定位后看具体 handler 报错。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

- **devices**（终端主表）：`mid`、`guid`、`name`、`username`、`group_id`、`ip`、`status`、`online_status`、`version`、`ostype`、`itime`、`utime`
- **device_info**（终端详情宽表 150+列）：`mid`、`computername`、`os`/`osversion`、`compliance_inspect_status`(合规)、`firewall_status`、`vulcount`/`vul_scan_time`(漏洞)、`riskcount`/`risk_scan_time`(风险)、`itime`、`utime`
- **device_ops_info** / **hardware_changes**（硬件变更） / **software_status** / **data_client_tav_update**(病毒库版本) / **data_client_version_update**(终端版本)
> 按 mid 串联。写入侧服务；查询看 device-query 页。