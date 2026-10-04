---
name: endpoint-asset
description: Use when the user reports endpoint registration or visibility problems, offline or unknown device status, group or profile issues, remote control failures, MDM enrollment, or software inventory and repository questions.
---

# 终端资产能力

本能力覆盖终端管理域与软件运维域：设备注册、设备信息、硬件信息与预警、设备查询、在线状态、分组、位置、远程协助、MDM、软件清单、盗版软件检测/正版率与软件仓库。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：设备不可见、注册失败、设备信息/分组/位置不对、在线状态异常、远控失败或黑屏、MDM 纳管、软件清单与仓库问题。
- **排除**：策略下发与管控效果转 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md`；软件“安装行为”被实时防护拦截转 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`；控制台整体不可用转 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。

## 意图分诊

| 现象 | 优先路径 |
|---|---|
| 控制台看不到某台设备 | 注册与查询链路 |
| 设备信息/分组/位置不对 | 设备信息与分组链路 |
| 硬件信息缺失或硬件预警异常 | 设备信息与硬件上报链路 |
| 设备离线、状态异常 | 模块状态与 `ioagent` 链路 |
| 远控失败、黑屏 | 远控与隧道链路 |
| 无法纳管移动设备 | MDM 链路 |
| 软件清单缺失、仓库分发异常 | 软件清单与仓库链路 |
| 盗版软件检测或正版率统计异常 | 软件清单与开放接口链路 |

## 工作流程

### 设备不可见

1. 先确认设备是否注册：注册链路只读核实，区分“未注册”与“已注册未上报”。
2. 注册成功后依次检查：上报 → 列表展示，逐级比对只读状态。
3. 批量不可见先怀疑平台侧，单台不可见先怀疑终端侧；不先动手注销重装。

### 在线状态异常

1. 结合时间段与最近一次上报，只读核实心跳与模块状态。
2. 区分网络断开、暂停使用（`ioa-pause`）与客户端异常，先排除人为暂停。
3. 不把“控制台看不到”直接等同于“终端离线”。

### 远控失败

1. 先核实设备在线态与分组归属，再查远控链路。
2. 按“请求 → 隧道 → 会话建立 → 画面”逐步定位卡点。
3. 黑屏先看会话是否建立，再看画面通道；不先建议重启客户端。

### 软件清单与仓库

1. 区分软件“记录存在”与“终端实际安装”，先查清单状态再查分发记录。
2. 涉及下发任务转策略管控能力。

### 通用顺序

先只读核实存在性与状态，再定位阶段卡点；每一步写清检查对象、期望结果和下一步分支。

## 服务文档路由

路径以顶层 Skill 目录为基准，按需读取：

- 设备注册与查询：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-register.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-query.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/devices.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-info.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-client-api.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-open-api.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/host-lookup.md`
- 分组、档案与位置：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-group.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-profile.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-location.md`
- 在线状态与暂停：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-module-status.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/ioagent.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/ioa-pause.md`
- 远程协助：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/remote-ctrl-srv.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/remote-desktop.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/remote-turn-srv.md`
- MDM：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/mdm-svr.md`
- 软件清单、盗版软件检测/正版率与仓库：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/软件运维/software.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/软件运维/software-import.md`、`references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/软件运维/software-open-api.md`

未命中时先读 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/终端管理/device-query.md` 或 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/软件运维/software.md` 建立链路，再按异常点加载具体服务文档。

## 跨能力联动

- 远控与隧道异常 → 追加 `references/ioa-troubleshooting/trusted-access/access-login/SKILL.md`（隧道、连接通道）。
- 软件下发成功但未安装 → 追加 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md`（下载代理、任务）。
- 设备批量不可见伴随平台告警 → 追加 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。
- 共享串联字段：租户、`mid`、分组 ID、软件 ID、任务标识、时间段；跨域证据对齐后再合并结论。

## 输出验收

- 给出“注册/上报/展示”或“请求/通道/会话”链路中第一个可能的失败点。
- 区分“未注册、已注册未上报、离线、在线但列表异常”四种状态。
- 四段式完整，不输出真实 `mid`、位置或设备敏感信息。
- 一次作答自收敛，不要求上传客户端原始日志。
