---
name: access-login
description: Use when the user reports iOA login or authentication failures, account or OU sync problems, or inability to reach intranet business systems after a successful client login.
---

# 接入登录能力

本能力覆盖可信接入域：登录认证、账号同步、账号信息与组织架构、内网访问（SPA、DNS 接管、L3 隧道）、Web 网关、WireGuard 通道与无端接入。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：登录失败/被拒、账号同步异常、账号或组织信息缺失、登录成功但内网不通、特定业务系统无法访问、网关或隧道类现象、无端接入。
- **排除**：网络准入后台和 RADIUS 服务异常转 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`；客户端安装、终端在线状态和远控转 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`；终端实时防护拦截转 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`。

## 意图分诊

先确认对象与范围，再选择路径：

| 现象 | 优先路径 |
|---|---|
| 客户端登录报错、失败、被拒 | 客户端登录与票据链路 |
| 账号缺失、组织架构不对、同步延迟 | 账号同步与信息链路 |
| 全部内网业务都不通 | 共享链路优先：SPA/DNS/隧道，再逐资源 |
| 单个业务系统不通 | 资源授权与网关链路 |
| 登录成功但网络反复断连 | 连接管理、WireGuard 与流量控制链路 |
| 无端接入（浏览器/无客户端） | Web 网关链路 |

## 工作流程

### 登录链路

1. 区分登录阶段：账号密码校验 → 票据申请与换取 → 客户端上线。
2. 只读核实账号状态、同步结果与票据申请/换取记录；把卡住阶段与正常链路对比，定位第一个失败点。
3. 证据优先：账号类问题先查同步链路，不先怀疑客户端。
4. 输出文字流程图，标明可能卡点，按分支给出下一步只读检查。

### 内网访问链路

1. 先确认影响范围：全部资源还是单个资源。
2. 全部不通：按 DNS 接管 → SPA/隧道 → 网关连接检查共享链路；同一租户多设备对比可快速区分环境问题。
3. 单个不通：按资源授权 → 网关路由 → 连接通道检查，再结合访问时段与报错特征收敛。
4. 不做写操作，不要求客户端上传原始日志；后台只读检索遵守公共规范。

### 通用顺序

先公共底座（账号、策略、连接状态），再服务细节；每一步写清“查什么、期望什么、异常下一步”。

## 服务文档路由

只读取与当前现象直接相关的文件，路径以顶层 Skill 目录为基准：

- 登录与票据：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/client-login.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/client-ticket.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/authkeeper.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/auth-policy.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/server-configs.md`
- 账号与组织：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/account-info.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/account-sync.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/account-open-api.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ou-query.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/datasync.md`
- 内网访问与隧道：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-query.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-rule.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-spa.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-spa-misc.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-ticket.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-merge.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-governance-job.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/wg-route-client.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/wg-route-server.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/wireguard-channel.md`
- 连接管理与网关：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/conn-lc.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/conn-mgr.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/conn-sc.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/cluster-route.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/gw-groupcache.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/gw-monitor.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/gw-msg-channel.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/server-flow-control.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ud-server.md`
- Web 网关与无端接入：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/webgw-server.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/webgw-sync.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/webgw-helper.md`、`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/webgw-ngn-helper.md`

无端接入还必须检查权限治理链：`ngn-governance` 负责资源权限判断与缓存治理，`ngn-governance-job` 负责重算/刷新任务。出现资源列表为空、`invalid mid` 或权限缓存疑似未更新时，先只读核实账号/设备标识、资源授权与治理任务结果；当前知识包没有独立 `ngn-governance` 服务文档，不得补造其字段或日志路径。

未命中时先读 `references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-query.md` 或 `references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/client-login.md` 建立链路，再按异常点加载具体服务文档；不得一次加载全部文件。

## 跨能力联动

- 登录后内网不通且伴随告警或后台异常 → 追加 `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md`。
- 账号同步异常但表现为设备信息缺失 → 追加 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md`。
- 终端上防护策略拦截导致访问异常 → 追加 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md`。
- 共享串联字段：租户/账号、组织路径、`mid`、票据或请求标识、时间段；跨能力证据必须通过这些字段对齐，否则按并发问题分别处理。

## 输出验收

- 指明登录/访问链路中第一个可能失败点及对应只读核实步骤。
- 区分账号、策略、通道、网关四类原因，无证据不归因。
- 四段式完整，流程图清晰，不泄露真实地址、票据或账号。
- 一次作答自收敛，不把客户端日志上传作为前置条件。
