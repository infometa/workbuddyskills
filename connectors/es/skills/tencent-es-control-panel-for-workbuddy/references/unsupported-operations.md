# 暂不支持的操作（Unsupported Operations）

> 本文档列出当前 MCP tools **尚未提供对应 tool** 的 4 项变更能力：**规格升配、ES 内核版本升级、节点开机/关机、维护时间窗口设置**。
>
> 🔴 **本文档是「无 tool 能力」应答框架与控制台路径的唯一权威来源（SSOT）**。处理这 4 类请求前必须读完本文档。
>
> **处理原则**：`做完能做的只读校验` → `明确告知不支持` → `引导控制台` → `绝不绕行`。
>
> 🔄 **本文档是临时状态记录**。待 MCP 侧新增对应 tool 后，应将相应条目从本文档移除，并迁入 SKILL.md 的「已支持」路由表和正常变更流程。

## 通用应答框架（四类请求统一适用）

**不要简单一句「不支持」了事**，必须让这次对话仍然有产出：

```
① 先做能做的只读校验，把有价值的信息先给到用户
② 明确说明「该变更操作当前无 MCP tool 支持」—— 不含糊、不承诺、不给时间表
③ 给出精确的控制台操作路径
④ 把只读校验结论整理成「操作前检查清单」交给用户
⑤ 主动提出后续可帮忙的事（如「操作完成后帮你核对新配置与监控变化」）
```

### 通用应答模板

```
我先帮你做了 <操作名> 前的评估：

<只读校验结论：当前配置 / 监控判读 / 推荐目标值 / 备份与健康状态>

⛔ <操作名>当前没有 MCP tool 支持，我无法直接执行。
   请在腾讯云控制台操作：
   <控制台路径，见下方各节>

📋 操作前检查清单：
  ✅ <已通过的校验项>
  ⚠️ <需要注意的风险项>
  □  <待用户确认的事项>

需要我在操作完成后帮你核对结果吗？
```

## ⛔ 禁止的绕行方式（全部适用）

| 绕行方式 | 为什么禁止 |
|---------|----------|
| 用 `tccli es UpdateInstance ...` 子进程调用 | 绕过 MCP 服务端强制安全前置检查，等于放弃全部保护 |
| 用 `curl` 直接请求 `es.tencentcloudapi.com` | 同上；且需要密钥，违反「Skill 不接触密钥」原则 |
| 自写 TC3-HMAC-SHA256 签名脚本 | 同上，Skill 层不存在也不应引入任何凭证处理代码 |
| 拿 `UpdateInstanceNodeNum` / `UpdateInstanceDiskSize` 去「凑」规格升配 | 这两个 tool 服务端硬约束**不支持**改 `NodeType`，凑不出来，只会报错 |
| 用 `RestartNodes` 模拟节点关机 | 语义完全不同（重启 ≠ 关机），会造成用户预期错位 |

> 🚨 用户催促「你就帮我调一下嘛」时，**依然不绕行**。正确回应是解释绕行会跳过服务端的安全前置检查（如「集群不存在 0 副本索引」这类保护），风险由用户独自承担，并再次给出控制台路径。

---

## 1. 规格升配（纵向扩容 / 加 CPU / 加内存）

**MCP 现状**：❌ 无对应 tool。`UpdateInstanceNodeNum` / `UpdateInstanceDiskSize` 的能力边界均明确**不支持修改节点规格（NodeType）**。

**控制台路径**：ES 控制台 → 集群列表 → 点击集群 ID → 「节点配置」→「调整配置」→ 选择目标规格

### 可做的只读校验

```
① DescribeInstances(Fields=["InstanceId","InstanceName","Status","HealthStatus",
                            "NodeType","NodeNum","NodeInfoList","DiskType"])
   → 拿到当前规格
② 若用户是因 CPU / 内存高而想升配：
   GetMonitorData(MetricName="CpuUsageMax" / "JvmMemUsageMax", Period=3600, 最近 7 天)
   → 交 forecast_calc.py 判偶发 vs 持续（口径见 capacity-forecast-rules.md）
   → 偶发打高时应先告知「升配无效，建议先做根因分析」，这比引导控制台更有价值
③ 按 capacity-planning-guide.md「CPU/内存升配规格选择」表给出推荐目标规格
④ DescribeClusterSnapshot 确认有近期成功快照
```

### 本节特有的告知要点

**必须告知用户控制台上的升配方式二选一：**

- **蓝绿重启（推荐）**：业务无感知，读写不中断，约 40~60 分钟，临时需双倍节点资源
- **原地升配**：约 20~30 分钟，节点逐个重启期间副本数减少，有短暂抖动

> 生产环境 / 高可用要求 / 数据量大 → 建议选蓝绿重启。
> 💡 内存升配后 JVM 堆自动增至节点内存的 50%，无需手动配置。

### 未来接入要点

若 MCP 后续提供 `UpdateInstanceNodeType`（或类似）tool，接入时需：

- 在 SKILL.md 恢复「**升配方式必询问**（蓝绿 / 原地）」的强制规则
- 加「不降配」校验：目标规格的 `CPU × 内存` 必须大于当前值
- 保留「不切换机型系列」原则（切机型会导致数据搬迁）
- 磁盘类型必须保持不变

---

## 2. ES 内核版本升级

**MCP 现状**：❌ 无写 tool。但有只读 `DescribeUpgrade` 可查可升级版本。

**控制台路径**：ES 控制台 → 集群列表 → 点击集群 ID → 「集群配置」→「版本升级」

> 💡 **注意区分**：`RestartInstance(UpgradeKernel=true)` 升级的是**内核 patch 版本**（小版本补丁），**不是** ES 大版本升级（如 7.10.1 → 7.14.2）。不要拿它替代版本升级。

### 可做的只读校验

```
① DescribeUpgrade(InstanceId=id)              → 可升级的大版本、商业特性、子产品
② DescribeInstancePluginList(PluginType=1)    → 用户自装插件（升级失败的常见元凶）
③ DescribeClusterSnapshot(InstanceId=id)      → 确认有近期成功快照
④ DescribeInstances(Fields=["EsVersion","Status","HealthStatus"])
```

### 本节特有的告知要点

```
⚠️ 版本升级不可回滚，快照是唯一退路 —— 无可用快照时必须先建快照
⚠️ 用户自装插件需确认目标版本有对应插件版本，否则升级后插件不可用
□  已完成业务侧兼容性测试（7.x → 7.x 相对平滑，跨大版本到 8.x 有 breaking changes）
□  已通知相关业务方，选择业务低峰期
□  版本只能升不能降，请再次确认目标版本
```

### 未来接入要点

- 强制前置：`DescribeClusterSnapshot` 确认有成功快照，无快照则阻断
- 强制前置：`DescribeUpgrade` 确认目标版本在可升级列表中
- 必须提示：**升级不可回滚**
- 建议前置：`DescribeInstancePluginList` 插件兼容性核对

---

## 3. 节点开机 / 关机

**MCP 现状**：❌ 无对应 tool。MCP 只提供 `RestartNodes`（节点重启）。

**控制台路径**：ES 控制台 → 集群列表 → 点击集群 ID → 「节点信息」→ 选中节点 → 「关机 / 开机」

### ⚠️ 先澄清用户真实意图（高频误判，本节最重要）

用户说「关掉这个节点」时，往往真实意图并不是关机：

| 用户描述 | 真实意图 | 正确处理 |
|---------|---------|---------|
| 「这个节点有问题，重启一下」| 节点重启 | ✅ `RestartNodes` **已支持**，直接走正常流程 |
| 「节点卡住了，恢复一下」| 节点重启 | ✅ `RestartNodes` |
| 「把这个节点摘掉 / 下线」| 缩容 | ⛔ 本 Skill **不执行缩容** |
| 「先关掉再开起来」| 等价于重启 | ✅ 引导用 `RestartNodes` 更安全（无中间不可用窗口）|
| 「确实要关机，暂时不用」| 节点关机 | ⛔ 无 tool → 控制台 |

> 📌 **先问清意图再回答**。大部分场景 `RestartNodes` 就能满足，没必要引导用户去控制台。

### 可做的只读校验

```
① DescribeInstances(Fields=["Status","HealthStatus","NodeInfoList","InstanceName"])
② DescribeViews(InstanceId=id) → 节点列表、角色、节点级资源使用情况
```

### 本节特有的告知要点（确认确实要关机后）

```
⚠️ 关机后该节点上的分片将不可用，集群会自动重路由到副本
⚠️ 请确认集群副本数 ≥ 1
⚠️ Red 集群禁止关机，会加剧数据丢失风险
💡 若目的只是让节点恢复正常，可直接用 RestartNodes（已支持），比「关机再开机」更安全
```

### 未来接入要点

- `stop` 属高风险操作，接入时需强制校验：集群 health 不为 Red、副本数 ≥ 1
- 确认交互应使用比常规变更更强的措辞

---

## 4. 维护时间窗口设置

**MCP 现状**：❌ 无对应 tool。`UpdateInstanceNodeNum` / `UpdateInstanceDiskSize` 均只回填节点配置，不下发维护时间字段。

**控制台路径**：ES 控制台 → 集群列表 → 点击集群 ID → 「集群配置」→「可维护时间段」

### 可做的只读校验

```
DescribeInstances(Fields=["InstanceId","InstanceName","Status","Maintenance"])
→ Maintenance 未精确命中时会退化为关键词子串匹配，可命中
  MaintenanceStartTime / MaintenanceEndTime / MaintenanceTime 等字段
→ 若仍取不到，可退一步传 Fields=["*"] 并只摘取维护时间相关字段展示
```

### 本节特有的告知要点

```
· 选择业务低峰期（通常凌晨 02:00-06:00）
· 时间窗口至少 4 小时，确保有足够时间完成维护
· 避免与定时任务（数据导入、快照备份）冲突
```

---

## 汇总速查

| 能力 | MCP 写 tool | 可用的只读校验 tool | 控制台路径 |
|------|------------|------------------|----------|
| 规格升配 | ❌ | `DescribeInstances`、`GetMonitorData`、`DescribeClusterSnapshot` | 节点配置 → 调整配置 |
| 版本升级 | ❌ | `DescribeUpgrade`、`DescribeInstancePluginList`、`DescribeClusterSnapshot` | 集群配置 → 版本升级 |
| 节点开机 / 关机 | ❌ | `DescribeInstances`、`DescribeViews` | 节点信息 → 关机/开机 |
| 维护时间窗口 | ❌ | `DescribeInstances` | 集群配置 → 可维护时间段 |

## 版本核对建议

可用的 MCP tool 集合会随服务端迭代变化。建议在以下时机重新核对一次当前已加载的 tool 列表：

- 本 Skill 做大版本升级前
- 用户反馈「控制台有这个功能，为什么你不能做」时
- `minWorkbuddyVersion` 提升时

核对后若发现上述 4 项已有对应 tool，请：

1. 从本文档移除相应条目
2. 迁入 SKILL.md「用户意图路由表 → ✅ MCP 已支持」
3. 在 `references/mcp-tools-reference.md` 补充该 tool 的完整参数章节
4. 恢复对应的强制规则（如规格升配的「升配方式必询问」）
5. 更新 `connector-meta.json` 的 `version`
