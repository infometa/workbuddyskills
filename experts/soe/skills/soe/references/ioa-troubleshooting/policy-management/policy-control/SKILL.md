---
name: policy-control
description: Use when the user reports policy delivery or calculation failures, endpoint controls not taking effect, process, peripheral or access control issues, or software distribution, installation, or uninstallation problems.
---

# 策略管控能力

本能力覆盖终端管控域与软件管控域：策略计算、策略下发、策略适配与上报、进程控制、外设与访问控制（ACL）、合规基线、软件分发与静默安装。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：策略下发显示成功但终端未生效、策略计算或适配异常、进程/外设/文件/网络管控问题、ACL 不生效、软件下发/安装/卸载问题。
- **排除**：终端设备不可见或未注册转 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`；实时防护或 DLP 拦截转 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`；控制台、任务引擎后台故障转 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。

## 意图分诊

| 现象 | 优先路径 |
|---|---|
| 策略未生效 | 计算 → 下发 → 终端执行逐段排查 |
| 进程、外设、文件/网络访问、水印、系统加固或防火墙未生效 | 策略计算与 ACL 链路 |
| 策略下发失败或报错 | 策略适配与上报链路 |
| 软件下发成功但未安装 | 任务 → 下载代理 → 静默安装 → 上报链路 |
| 软件卸载异常 | 软件任务链路 |

## 工作流程

### 策略未生效

1. 确认授权包含目标策略能力，再确认策略对象是否包含目标终端与用户（分组、组织架构）；授权不足时策略可能不会进入有效计算，授权细节由平台运维能力只读核实。
2. 只读核实策略计算结果、下发记录与终端执行状态，按“授权 → 计算 → 下发 → 执行 → 上报”定位第一个失败点。
3. 多终端一致失败先怀疑平台侧或策略配置，单终端失败先怀疑终端侧。
4. 覆盖/优先级冲突时给出核对路径，不直接建议删除策略。

### 软件下发未安装

1. 区分“任务已创建、下载成功、安装执行、结果上报、控制台展示”五个阶段；“下发成功”只说明某阶段完成，不代表安装完成。
2. 按任务 → 下载代理 → 终端静默安装 → 结果上报逐段只读核实。
3. 安装失败原因分技术类（权限、冲突、防护拦截）与任务类（参数、时间窗、对象范围）分别收敛。

### 通用顺序

先确认对象归属与阶段状态，再只读比对记录；任何变更（重发、重新下发、卸载重装）都必须先经只读证据确认并说明影响后等待批准。

## 服务文档路由

路径以顶层 Skill 目录为基准，按需读取：

- 策略计算与适配：`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/policy-calculate.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/policy-adapter.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/config-query.md`
- 策略上报与接口：`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/policy-report.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/policy-open-api.md`
- 进程、外设、文件/网络访问、水印、系统加固与防火墙等管控：`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/process-acl.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/acl-strategy.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/acl-info.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/acl-report.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/acl-open-api.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/location.md`
- 软件下载与静默安装：`references/ioa-troubleshooting/policy-management/policy-control/references/软件管控/download-proxy-server.md`、`references/ioa-troubleshooting/policy-management/policy-control/references/软件管控/client-extra.md`

未命中时先读 `references/ioa-troubleshooting/policy-management/policy-control/references/终端管控/policy-calculate.md` 或 `references/ioa-troubleshooting/policy-management/policy-control/references/软件管控/download-proxy-server.md` 建立链路，再按异常点加载具体服务文档。

## 跨能力联动

- 软件任务异常与后台任务引擎相关 → 追加 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`（任务、告警）。
- 实际已安装但软件清单未识别 → 追加 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`。
- 终端执行阶段被防护拦截 → 追加 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`。
- 共享串联字段：租户、分组、`mid`、策略/任务标识、时间窗；跨域证据对齐后再合并结论。

## 输出验收

- 明确策略链路（计算/下发/执行/上报）或软件链路（任务/下载/安装/上报）中的失败阶段。
- 说明“下发成功”与“终端已生效/已安装”的区别。
- 只读检查优先；变更类建议必须说明影响并等待批准。
- 四段式完整，不泄露策略内容或任务敏感标识。
