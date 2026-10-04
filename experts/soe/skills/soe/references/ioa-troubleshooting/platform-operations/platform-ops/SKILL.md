---
name: platform-ops
description: Use when the user reports console or API failures, permission problems, data domain or cascade issues, license problems, alarm or task anomalies, reports or metrics, performance and disk issues, middleware problems, or network admission backend failures.
---

# 平台运维能力

本能力覆盖基础平台域、运营类域与网络准入域：控制台、Web/Open API、API 插件、数据域、级联、授权、告警、任务、报表指标、日志中心、第三方对接与网络准入后台。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：控制台无法打开/功能报错、API 调用失败、权限问题、数据域与级联、授权到期或异常、告警误报/缺失、任务执行异常、报表与指标、磁盘/性能、日志中心、第三方对接、准入（Portal、RADIUS、计费/审计）后台。
- **排除**：单台终端业务现象转对应终端/接入能力；终端安全告警内容转 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`；账号权限的“业务含义”转 `references/ioa-troubleshooting/trusted-access/access-login/SKILL.md`。

## 意图分诊

| 现象 | 优先路径 |
|---|---|
| 控制台打不开/普遍报错 | Web 服务与 API 链路 |
| API 调用失败 | API 网关、插件与开放接口链路 |
| 权限/数据域/级联 | 数据域与级联链路 |
| 授权异常 | 授权处理链路 |
| 告警异常 | 告警产生、发送与展示链路 |
| 任务异常 | 任务引擎与任务服务链路 |
| 报表/指标/日志 | 统计、指标、日志中心链路 |
| 磁盘/性能告警 | 只读定位增长源，不无证据归因 |
| ES、ETCD、Redis、NSQ、Nginx、PgSQL 异常 | 中间件健康与依赖链路 |
| 第三方对接失败 | 第三方提供方链路 |
| 网络准入异常 | Portal、RADIUS、计费审计链路 |

## 工作流程

### 控制台与 API

1. 先确认影响范围：单用户（权限/账号）还是普遍（服务/网关）。
2. 只读核实 Web 服务、API 网关与插件状态，按“接入 → 鉴权 → 转发 → 结果”定位。
3. 不直接建议重启服务；先给只读证据与最小影响选项。

### 告警与任务

1. 先核对时间段、对象与最近执行记录，区分“任务未跑、跑了没结果、结果未展示”。
2. 告警异常区分“未产生、未发送、未展示”三个阶段。
3. 磁盘与性能告警先只读定位增长源（日志轮转、数据增长、任务积压），再决定行动；不把时间接近的两个告警自动判定为同因。

### 授权

1. 只读核实授权信息、处理服务与到期时间；到期问题只解释影响，不给出绕过手段。
2. 商务与续费相关转 `references/ioa-troubleshooting/consulting/consult-advisor/SKILL.md`。

### 中间件健康

1. 按应用依赖关系分诊 ES、ETCD、Redis、NSQ、Nginx 与 PgSQL；先只读核实进程/实例健康、容量、延迟、连接与主从/集群状态，再关联上层服务现象。
2. 只读核实必须限定时间与节点，不使用全量扫描；没有随包精确服务文档时明确按现场部署工具和版本核实，不补造命令、端口、字段或日志路径。
3. 中间件异常只有在时间、节点、错误记录和上层请求能串联时才判定为故障原因，否则作为候选项并列。

### 网络准入

1. 区分认证阶段、授权阶段与计费审计阶段，按“Portal → RADIUS → 计费/审计”链路只读核实。
2. 涉及准入的终端侧访问现象可追加读取 `references/ioa-troubleshooting/trusted-access/access-login/SKILL.md`。

### 通用顺序

先影响范围，再阶段定位；只读检查为主，变更（重启、清缓存、改配置、删数据）必须说明影响并等待批准。

## 服务文档路由

路径以顶层 Skill 目录为基准，按需读取：

- 控制台与 API：`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/web-api.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/web-open-api.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/api-access-svr.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/api-plugin.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/client-api.md`
- 数据域与级联：`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/data-domain.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/cascade-SrvMgr.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/cascade-open-api.md`
- 告警：`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/alarm-server.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/alarm-producer.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/alarm-sender.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/monitor-alarm.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/alert-open-api.md`
- 任务：`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/task-engine.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/task-server.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/task-open-api.md`
- 授权：`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/license.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/license-process.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/license-open-api.md`
- 报表、指标、日志与数据流：`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/chart-stat.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/metric-query.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/log-center.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/log-report.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/data-report.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/data-route.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/flow-collect.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/event-deliver.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/syncto-es.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/client-quality.md`
- 第三方：`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/thirdparty-set.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/thirdparty-provider.md`
- 网络准入：`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/access_svr.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/portal_svr.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/radius_ctrl_svr.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/inac-accounting.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/inac_auth_log.md`、`references/ioa-troubleshooting/platform-operations/platform-ops/references/网络准入/inac_macs.md`

未命中时先读 `references/ioa-troubleshooting/platform-operations/platform-ops/references/基础平台/web-api.md` 或 `references/ioa-troubleshooting/platform-operations/platform-ops/references/运营类/task-engine.md` 建立链路，再按异常点加载具体服务文档。

## 跨能力联动

- 任务异常导致策略/软件下发问题 → 追加 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md`。
- 准入后台正常但终端访问异常 → 追加 `references/ioa-troubleshooting/trusted-access/access-login/SKILL.md`。
- 告警指向终端安全事件 → 追加 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`。
- 共享串联字段：租户、任务/告警标识、时间段、数据域、对象标识；跨域证据对齐后再合并结论。

## 输出验收

- 区分“服务异常、任务异常、数据延迟、展示异常”四类根因方向。
- 磁盘/性能类问题先给只读定位项，不无证据归因。
- 变更建议必须说明影响、回滚方式并等待批准。
- 四段式完整，不泄露内部 URL、连接串或凭据。
