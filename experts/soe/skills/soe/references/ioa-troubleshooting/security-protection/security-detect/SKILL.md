---
name: security-detect
description: Use when the user reports EDR detection or alert problems, virus database or vulnerability update failures, real-time protection issues, offline update packages, DLP interception or approval problems, UEBA anomalies, or phishing defense questions.
---

# 安全检测能力

本能力覆盖终端安全域与数据安全域：EDR、病毒库/漏洞库更新、实时防护、离线数据包、安全数据查询、DLP、文件服务与 UEBA。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：EDR 告警缺失/异常、病毒库与漏洞库更新失败、实时防护不生效、离线环境数据更新、DLP 未拦截/误拦截、DLP 审批与取证、UEBA 异常、防钓鱼。
- **排除**：终端设备不可见转 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`；策略下发导致防护配置未生效转 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md`；告警后台与任务转 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。

## 意图分诊

| 现象 | 优先路径 |
|---|---|
| EDR 无告警/告警异常 | 共同底座 → EDR 检测链路 |
| 病毒库/漏洞库更新失败 | 版本与更新链路 |
| 实时防护未生效 | 底座 + 策略 + 版本链路 |
| 离线环境无法更新 | 离线数据包链路 |
| DLP 未拦截/误拦截 | 共同底座 → DLP 引擎与策略链路 |
| DLP 审批/取证异常 | DLP 审批、签名与文件链路 |
| 行为异常、风险账号 | UEBA 链路 |

## 工作流程

### 共同底座优先

1. 先核实终端模块健康度、授权、策略计算与配置下发，排除底座问题再拆具体检测链路。
2. “没有告警”不等于“没有威胁”，也不等于“没有检测”；先区分未检测、未上报、未展示。
3. 大范围异常先怀疑平台侧，单终端异常先怀疑终端侧。

### EDR 链路

1. 只读核实检测对象服务、日志代理与开放接口状态，按“检测 → 日志转发 → 告警展示”逐段定位。
2. 结合时间段与事件类型核对，不直接断言漏检。

### 更新链路

1. 区分在线与离线更新路径，先确认版本服务器与更新任务状态。
2. 失败时定位下载、导入、替换任一阶段，不先建议手动改配置。

### DLP 链路

1. 先确认策略对象、通道（外发方式）与引擎状态，再判断“策略未配、未命中、已命中未拦截”。
2. 误拦截场景按规则命中记录反向定位规则与对象范围，不先建议全局放行。
3. 涉及审批、签名与文件取证的异常分别按对应服务文档核实。

### UEBA 链路

1. 只读核实 ETL 与数据链路，结合时间段判断数据延迟或任务异常。
2. 行为异常的解释必须限定在已有证据内，不推断动机。

## 服务文档路由

路径以顶层 Skill 目录为基准，按需读取：

- EDR 与检测：`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/edr-object-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/edr-log-proxy.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/edr-tix-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/edr-open-api.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/data-edr-scan.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/device-phish.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/security-open-api.md`
- 版本与更新：`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/tavUpdate.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/vulUpdate.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/dataUpdate.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/version-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/queryServer.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/nvd-server.md`
- 离线数据包：`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/importDataPkg.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/offline-update.md`
- UEBA：`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/ueba-etl.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/ueba-open-api.md`
- DLP 核心：`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-security-engine.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-conn.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-dispatch.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-alarm.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-open-api.md`
- DLP 审批、签名与文件：`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-approval-api.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-sign.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-tool.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/file-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/file-open-api.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/object-server.md`、`references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/sync-file.md`

未命中时先读 `references/ioa-troubleshooting/security-protection/security-detect/references/终端安全/edr-object-server.md` 或 `references/ioa-troubleshooting/security-protection/security-detect/references/数据安全/dlp-server.md` 建立链路，再按异常点加载具体服务文档。

## 跨能力联动

- 检测链路异常伴随告警/任务后台异常 → 追加 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。
- 策略未下发导致防护或 DLP 未生效 → 追加 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md`。
- 终端模块异常 → 追加 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`。
- 共享串联字段：租户、`mid`、策略/任务标识、事件时间、事件类型；跨域证据对齐后再合并结论。

## 输出验收

- 先声明共同底座结论，再给出检测/更新/DLP 具体链路中的失败阶段。
- 区分“未检测、未上报、未展示、未命中、未拦截”，无证据不归因。
- 不输出样本哈希、文件路径、涉密内容或策略细节。
- 四段式完整，一次作答自收敛。
