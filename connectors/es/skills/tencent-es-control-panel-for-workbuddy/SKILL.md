---
name: tencent-es-control-panel
description: 用于用户要求对腾讯云 ES（Elasticsearch Service）集群执行变更时 —— 扩容 / 加节点、磁盘扩容、集群重启、节点重启、重启 Kibana、开关 Kibana 公网或内网访问、管理 Kibana 访问白名单 / 黑名单、Kibana 报「很抱歉，你没有权限访问」或 403、查看变更进度、询问「什么时候需要扩容 / 扩多少合适 / 容量还能撑多久」，以及 tencent-es-diagnose 给出诊断结论后需要落地执行变更时。不用于根因分析与问题诊断。
---

# 腾讯云 ES 集群变更执行 Skill

> ⚠️ 本 Skill 执行**真实变更**，MCP tool **一调即下发，无 dry-run**。只读诊断与根因分析请用 `tencent-es-diagnose`。

全部取数与变更通过 **MCP tools** 完成，外加 2 个零云 API 调用的本地脚本。

## ⚠️ 安全铁律

1. **变更前必须二次确认**：展示完整 tool 名 + 全部参数 + 影响，获得用户明确确认。**没有脚本层兜底，Agent 是唯一防线**
2. **变更前必调 `DescribeInstances`** 确认 `Status=1`（正常）
3. **不执行缩容**（减节点 / 降配规格 / 缩磁盘），不执行删除集群、版本降级
4. **不做根因分析** —— CPU 高 / JVM 高 / 延迟高 / Red 的排查归 `tencent-es-diagnose`
5. **禁止输出密钥**。鉴权由连接器在宿主层完成，Skill 层不存在 SecretId/SecretKey
6. **禁止绕行**：MCP tools 不可用或能力缺失时，**不得**改用 `tccli` / `curl` 云 API / 自写签名脚本
7. **服务端前置检查被阻断时如实转述**，不重试、不换参数硬闯

## ⚠️ 强制执行规则

- 执行任何变更前必须 `use_skill("tencent-es-control-panel")` 加载本文档
- 用户回复「确认 / 是 / 执行」等确认词时，**必须重新加载本文档**再执行
- **禁止凭记忆或推测 tool 名与参数** —— 必须从 reference 文档核对

## 鉴权模型

鉴权由 MCP 连接器在宿主层完成，本 Skill **不接触任何密钥**，无需环境变量。

**前置检查**：若 MCP tools 不可用（未加载 / 调用报连接错误），提示用户在连接器管理页面配置并连接。

> ℹ️ 所需 CAM 权限：`es:Describe*`、`es:UpdateInstance`、`es:RestartInstance`、`es:RestartNodes`、`es:RestartKibana`、`monitor:GetMonitorData`。出现 `AuthFailure` 时让用户联系管理员确认授权。

## MCP Tool 索引

> 🔴 **REQUIRED**：本表**仅为索引，不含完整参数**。调用任何 tool 前，**必须**先读 [`references/mcp-tools-reference.md`](references/mcp-tools-reference.md) 的对应章节，确认参数语义与服务端强制前置检查。**禁止**仅凭本表调用。

### 变更类（写操作，必须二次确认）

| Tool | 能力 | 参数与前置检查 |
|------|------|--------------|
| `UpdateInstanceNodeNum` | 节点数量扩容（横向） | [§3](references/mcp-tools-reference.md#3-updateinstancenodenum节点数量扩容-) |
| `UpdateInstanceDiskSize` | 磁盘扩容 | [§4](references/mcp-tools-reference.md#4-updateinstancedisksize磁盘扩容-) |
| `RestartInstance` | 集群重启（**仅滚动，要求 green**） | [§5](references/mcp-tools-reference.md#5-restartinstance集群滚动重启-) |
| `RestartNodes` | 节点重启 | [§6](references/mcp-tools-reference.md#6-restartnodes节点重启-) |
| `RestartKibana` | Kibana 重启 | [§7](references/mcp-tools-reference.md#7-restartkibanakibana-重启-) |
| `UpdateEsAcl` | Kibana 访问白 / 黑名单 | [§8](references/mcp-tools-reference.md#8-updateesaclkibana-访问白黑名单-) |
| `UpdateKibanaPublicAccess` | Kibana 公网访问开关 | [§9](references/mcp-tools-reference.md#9-updatekibanapublicaccesskibana-公网访问开关-) |
| `UpdateKibanaPrivateAccess` | Kibana 内网访问开关 | [§10](references/mcp-tools-reference.md#10-updatekibanaprivateaccesskibana-内网访问开关-) |

### 只读类（变更前置查询 / 进度跟踪 / 容量预测）

| Tool | 典型用途 | 参数 |
|------|---------|------|
| `DescribeInstances` | **每次变更前必调**，查状态与当前配置 | [§1](references/mcp-tools-reference.md#1-describeinstances集群概览-) |
| `GetMonitorData` | 容量预测取数 | [§2](references/mcp-tools-reference.md#2-getmonitordata监控取数-) |
| `DescribeInstanceOperations` | 变更提交后跟踪进度 | [§11](references/mcp-tools-reference.md#11-describeinstanceoperations变更进度-) |
| `DescribeClusterDiskRange` | 磁盘扩容可行性校验 | [§12](references/mcp-tools-reference.md#12-describeclusterdiskrange磁盘上下限-) |
| `DescribeUpgrade` | 版本升级只读校验 | [§13](references/mcp-tools-reference.md#13-describeupgrade可升级版本-) |
| `DescribeViews` | 节点资源快照 / 查节点名 | [§14](references/mcp-tools-reference.md#14-describeviews集群视图-) |
| `DescribeInstancePluginList` | 升级前插件兼容性核对 | [§15](references/mcp-tools-reference.md#15-describeinstancepluginlist插件列表-) |
| `DescribeClusterSnapshot` | 高风险变更前确认有备份 | [§16](references/mcp-tools-reference.md#16-describeclustersnapshot快照备份-) |
| `DescribeEsInstanceEventLists` / `DescribeEventDataDetail` / `DescribeEventInfoList` | 变更前确认无进行中的硬件异常 / 智能运维事件 | [§17](references/mcp-tools-reference.md#17-事件中心三件套-) |

### 本地脚本（2 个，均零云 API 调用）

| 脚本 | 功能 | 详细参数 |
|------|------|---------|
| `scripts/detect_my_ip.py` | 按集群地域智能探测**本机公网 IP** | [§18](references/mcp-tools-reference.md#18-detect_my_ippy本机公网-ip-探测-) |
| `scripts/forecast_calc.py` | 容量预测**确定性数值计算** | [§19](references/mcp-tools-reference.md#19-forecast_calcpy容量预测计算-) |

> ⚠️ **容量预测必须走 `forecast_calc.py`，禁止 Agent 自行心算**。线性回归需对上百数据点求 Σxy/Σx²，LLM 计算不可靠且**算错不会报错**，只会给出看似合理的错误天数。
> ⚠️ **「加我的 IP / 本机 IP」必须走 `detect_my_ip.py`，禁止 Agent 自行 curl 探测**。原因见 [§18](references/mcp-tools-reference.md#18-detect_my_ippy本机公网-ip-探测-)。

## 执行顺序（MANDATORY，禁止跳步骤）

```
DescribeInstances 查状态 → 读当前值算目标值 → 展示完整 tool 调用与影响
  → 用户明确确认 → 调用变更 tool → DescribeInstances 回读 + DescribeInstanceOperations 跟踪
```

> 🔴 **REQUIRED**：完整流程图、分场景步骤详解、确认话术模板、异常处理，**执行变更前必读** [`workflow.md`](workflow.md)。

## 三条最高频陷阱

**① 扩容类参数是目标值，不是增量。** 用户说「扩 2 个节点」时**禁止**直接传 `NodeNum=2` —— 在 3 节点集群上会被服务端判定为缩容而阻断。必须先 `DescribeInstances` 读当前值再相加。磁盘同理：`DiskSize` 是目标**单节点**容量，不是增量、不是集群总容量。
→ 换算与区间校验步骤见 [mcp-tools-reference §3](references/mcp-tools-reference.md#3-updateinstancenodenum节点数量扩容-) / [§4](references/mcp-tools-reference.md#4-updateinstancedisksize磁盘扩容-)，**必读**。

**② 集群重启仅支持滚动，且强制要求 health = green。** `RestartMode` 与 `ForceRestart` 在服务端已硬编码，**不提供全量 / 强制重启**。因此**不要询问用户「滚动还是全量」**。yellow / red 时不要尝试绕行，改为建议先用 `tencent-es-diagnose` 定位未分配分片，或引导控制台。
→ 标准应答话术见 [mcp-tools-reference §5](references/mcp-tools-reference.md#5-restartinstance集群滚动重启-)。

**③ `UpdateEsAcl` 是全量覆盖语义。** 白名单与黑名单**必须同时回传**，未传的一侧视为清空。必须先 `DescribeInstances(Fields=["EsAcl"])` 读出双列表再增量修改。
→ 安全约束（拒绝 `0.0.0.0` / `/0` 掩码等）与完整流程见 [mcp-tools-reference §8](references/mcp-tools-reference.md#8-updateesaclkibana-访问白黑名单-)，**必读**。

## 用户意图路由表

### ✅ MCP 已支持

| 用户描述 | Tool | 关键提示 |
|---------|------|----------|
| 扩容 / 加节点（热节点）| `UpdateInstanceNodeNum` | `Type=hotData`，`NodeNum`=**目标总数** |
| 扩容冷节点 / 主节点 / 协调节点 / ML 节点 | `UpdateInstanceNodeNum` | `Type=warmData\|dedicatedMaster\|dedicatedCoordinating\|dedicatedMl` |
| 扩磁盘 | `UpdateInstanceDiskSize` | `DiskSize`=**目标单节点 GB**；先 `DescribeClusterDiskRange` 校验 |
| 不知道扩多少 / 什么时候扩 / 还能撑多久 | `GetMonitorData` → `forecast_calc.py` → 扩容 tool | `Period=3600`，7~14 天；口径见 [capacity-forecast-rules.md](references/capacity-forecast-rules.md) |
| 重启集群 | `RestartInstance` | 告知仅滚动、需 green |
| 重启集群并升级内核 patch | `RestartInstance` | `UpgradeKernel=true`，须明确告知会升 patch |
| 重启节点（已知节点名）| `RestartNodes` | 节点名原样传入，长数字串也是节点名 |
| 重启 Kibana / Kibana 卡死打不开 / 白屏 | `RestartKibana` | 仅 `InstanceId` |
| **Kibana「很抱歉，你没有权限访问」/ 403 / 加本机 IP** | `detect_my_ip.py` → `UpdateEsAcl` | **必须**先跑脚本探测；**不是**重启 Kibana |
| 查看 / 添加 / 移除 白名单 / 黑名单 | `DescribeInstances(Fields=["EsAcl"])` → `UpdateEsAcl` | 双列表**必须同时回传** |
| 开启 / 关闭 Kibana 公网访问 | `UpdateKibanaPublicAccess` | `OPEN` 时必须提示公网暴露风险 |
| 开启 / 关闭 Kibana 内网访问 | `UpdateKibanaPrivateAccess` | 关闭前确认用户不是仅依赖内网 |
| 查看变更进度 / 跟踪 | `DescribeInstanceOperations` | **必须限定** `StartTime`/`EndTime` |
| 查看集群列表 / 集群状态 | `DescribeInstances` | 变更场景**必须显式传 `Fields`** |
| 查看集群 / 节点资源快照 | `DescribeViews` | 变更前后对比 |
| 查看快照备份 | `DescribeClusterSnapshot` | 高风险变更前确认有备份 |
| 查看已装插件 | `DescribeInstancePluginList` | 升级前兼容性核对 |
| 查看硬件异常 / 变更 / 智能运维事件 | `DescribeEsInstanceEventLists` → `DescribeEventDataDetail` | 变更前确认无进行中事件 |

### ⛔ MCP 暂不支持（只读校验 + 明确告知 + 控制台引导）

| 用户描述 | 可做的只读校验 |
|---------|--------------|
| 升配 / 提升规格 / 加 CPU / 加内存 | `DescribeInstances` 查当前规格 + `GetMonitorData` 判偶发/持续 + 按 [规格选择表](references/capacity-planning-guide.md) 给推荐目标规格 |
| ES 内核版本升级 | `DescribeUpgrade` 列可升级版本 + `DescribeInstancePluginList` 核对插件 + `DescribeClusterSnapshot` 确认备份 |
| 节点开机 / 关机 | `DescribeInstances` / `DescribeViews` 查节点状态（**先澄清是否其实只想重启**）|
| 设置维护时间窗口 | `DescribeInstances` 查当前维护时间字段 |

> 🔴 **REQUIRED**：处理以上 4 类请求前，**必读** [`references/unsupported-operations.md`](references/unsupported-operations.md) 获取应答框架、控制台路径与禁止的绕行方式。**禁止**简单一句「不支持」了事。
> 🔄 待 MCP 侧新增对应 tool 后，将条目迁入「已支持」并接入变更流程。建议每次大版本升级前重新核对一次可用 tool 列表。

## 能力边界

- ❌ 不执行缩容（减节点 / 降配规格 / 缩磁盘）、删除集群、版本降级
- ❌ 不做根因分析、不做集群健康监控与批量巡检打分（均属 `tencent-es-diagnose`）
- ❌ 不执行 ES 数据面写操作（`_reroute`、`_close`、解除只读锁等）
- ⚠️ 集群重启仅支持滚动且要求 green；全量 / 强制重启需走控制台
- ⚠️ 容量预测基于趋势外推，仅供参考

### Skill 协作关系

```
tencent-es-diagnose（诊断 / 根因分析 / 监控巡检 / 数据面只读）
    │ 结论：需要升配 / 扩容 / 重启
    ▼
tencent-es-control-panel（变更执行 / 容量预测）  ← 本 Skill
    │ 用户确认后
    ▼
调用变更类 MCP tool → DescribeInstanceOperations 跟踪进度
```

> 两个 Skill 共用同一套 MCP tools。诊断类只读取数（`Ces*` 数据面、日志、打分）交给 `tencent-es-diagnose`，本 Skill 只做「变更前置校验 + 变更 + 进度跟踪」。

## Anti-Patterns

❌ **把增量当目标值传给 `UpdateInstanceNodeNum` / `UpdateInstanceDiskSize`** → 最高频错误，会被服务端判定为缩容而阻断。必须先读当前值再相加
❌ **未获得用户确认就调用变更 tool** → 无脚本层兜底、无 dry-run，一调即真，Agent 是唯一防线
❌ **MCP tools 不可用时改用 `tccli` / `curl` 云 API / 自写签名脚本绕行** → 绕过了服务端强制安全前置检查，等于放弃全部保护
❌ **向白名单添加 `0.0.0.0` / `0.0.0.0/0` / `::/0` / `*` / 任何 `/0` 掩码 CIDR** → 等同于关闭白名单限制，服务端不一定拦，**本 Skill 层必须硬性拒绝**
❌ **「加本机 IP / 我的 IP」时 Agent 自行用 `curl` / `api.ipify.org` / `ifconfig.me` 探测** → 绕过按地域选路。国内集群走代理时会拿到代理出口 IP，加进白名单后 tool 返回成功但 **Kibana 依旧 403**，且极难排查。仅当用户**明确指定具体 IP** 时才跳过探测
❌ **对未实际看到的 tool 返回做猜测性描述** → 进度与结果必须基于真实返回，禁止凭空推测
❌ **把 403「没有权限访问」当成 Kibana 故障去重启** → 重启解决不了白名单问题

## References

**🔴 以下文档为强制阅读项，不是「延伸阅读」：**

| 文档 | 何时**必读** |
|------|------------|
| [`references/mcp-tools-reference.md`](references/mcp-tools-reference.md) | **调用任何 tool 前** —— 完整参数、服务端前置检查、错误码、脚本用法。本 Skill 中 tool 参数的**唯一权威来源** |
| [`workflow.md`](workflow.md) | **执行任何变更前** —— 流程图、分场景步骤、确认话术模板、异常处理 |
| [`references/capacity-forecast-rules.md`](references/capacity-forecast-rules.md) | **做容量预测前** —— 取数口径、阈值、算法、推荐分流、报告模板。阈值与算法的**唯一权威来源** |
| [`references/capacity-planning-guide.md`](references/capacity-planning-guide.md) | **需要给规格升配建议时** —— 操作优先级、规格选择表、最佳实践 |
| [`references/unsupported-operations.md`](references/unsupported-operations.md) | **用户请求上述 4 项无 tool 能力时** —— 应答框架、控制台路径、禁止的绕行方式 |
