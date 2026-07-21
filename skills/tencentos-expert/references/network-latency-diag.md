# 延迟排查

> 本文件包含网络延迟的完整诊断流程。公共部分（安全原则、前置检查、阈值表）请参见 SKILL.md。
>
> **排查思路**：按网络收发包全流程逐层分析——问诊定向 → 环境预检 → RTT 基线与路径分析 → 传输层综合分析（NIC 硬件/中断合并 → TCP 拥塞/Pacing → 内核参数/Nagle/缓冲区）→ 队列与软中断分析（Qdisc → softirq/ksoftirqd → GRO → ARP 解析）→ nettrace 协议栈延迟与 RTT 分析 → 应用层分析（Socket Backlog → 进程调度 → 系统调用）
>
> **设计依据**：基于 Linux 内核网络收发包全流程（DMA/PCIe 传输 → 硬中断/中断合并 → softirq/NAPI → GRO → 协议栈 → 传输层 → Socket → 应用层）中各环节可能产生延迟的热点，逐一覆盖诊断。

---

## Phase 0：问诊与分析模型选择

> **⚠️ 必须在执行任何诊断命令之前完成此阶段。** AI 需要通过结构化问诊收集关键上下文，然后根据问诊结果选择最匹配的分析模型，确定诊断路径。

### 必要信息清单

| 编号 | 信息项 | 说明 | 获取策略 |
|------|-------|------|---------|
| Q1 | **对端 IP / 域名** | 延迟的目标地址 | 用户未提供则**必须询问**；直接影响 ping/mtr/nettrace 等所有命令的目标参数 |
| Q2 | **网卡 / bond 名称** | 流量出口接口 | 通过 `ip route get <对端IP>` 自动推断；单网卡场景直接使用，多网卡/bond 场景向用户确认 |
| Q3 | **问题频率** | 偶发 / 持续 / 特定时段 | 用户未明确则**必须询问**；直接决定分析模型选择 |
| Q4 | **问题时间规律** | 高峰期？最近才出现？ | Q3=="持续"且用户未提及时间信息时**条件追问**；直接影响 M-3/M-4 模型选择 |
| Q5 | **业务协议与端口** | TCP/UDP？端口号？ | 用户提到具体业务时追问；用于 nettrace/tcpdump 的过滤参数 |
| Q6 | **已做过的排查** | 用户已尝试的操作 | 可选，避免重复劳动 |

### 智能问诊规则

```
WHEN 用户 prompt 中已包含对端 IP:
  → 跳过 Q1，直接使用

WHEN `ip route get` 推断结果明确（单一出口网卡，非 bond/非多 NIC）:
  → Q2 直接使用推断结果，无需确认，在诊断上下文摘要中展示
WHEN `ip route get` 推断结果涉及 bond/多网卡/结果不明确:
  → Q2 向用户确认

WHEN 用户 prompt 中提到 "偶发"/"偶现"/"有时候"/"随机":
  → Q3 已知 = 偶发，跳过 Q3

WHEN 用户 prompt 中提到 "一直"/"持续"/"稳定偏高"/"必现":
  → Q3 已知 = 持续，跳过 Q3

WHEN Q3 == "持续" AND 用户未提及时间信息（未出现 "最近"/"刚开始"/"高峰期"/"某个时段"）:
  → 追问 Q4："延迟是一直存在还是最近才出现的？有没有特定时段更明显？"
  → 目的: 区分 M-1（纯持续）和 M-3（时段型）/ M-4（新发型）

WHEN 用户 prompt 中提到 "最近"/"刚开始"/"升级后"/"配置后"/"重启后":
  → Q4 已知 = 新发，自动关联 M-4 模型，跳过 Q4

WHEN 用户 prompt 中提到 "高峰期"/"白天"/"工作时间"/"某个时段":
  → Q4 已知 = 时段型，自动关联 M-3 模型，跳过 Q4

WHEN 用户提到了具体业务（如 "访问 MySQL 慢"/"API 响应慢"）:
  → 追问 Q5（端口），并自动推断协议

WHEN 缺失的必要信息 ≤ 2 项:
  → 合并为一次提问（避免多轮追问增加用户负担）

WHEN 缺失的必要信息 > 2 项:
  → 分两次提问，先问最关键的 Q1 + Q3
```

### 分析模型选择

根据问诊收集到的**问题频率**（核心分类维度），选择不同的分析模型：

| 模型编号 | 问题模式 | 分析策略 | 核心工具 | 推荐路径 |
|---------|---------|---------|---------|---------|
| **M-1: 持续型延迟** | 延迟一直偏高、稳定复现 | 快速定位 → 逐层排查 | ping/mtr/ss/sysctl | Module 1 → Module 2 → Module 3 → Module 4 → Module 6 |
| **M-2: 偶发型延迟** | 偶尔出现延迟尖刺、随机抖动 | 抓现场 → 关联分析 | nettrace --latency + 监控脚本 | Module 1 → Module 5(nettrace 优先) → 根据结果定向 |
| **M-3: 时段型延迟** | 特定时间段延迟增高 | 基线对比 → 资源竞争分析 | 监控脚本 + 分时段采集 | Module 1 → Module 2(对比基线) → Module 3(带宽) |
| **M-4: 新发型延迟** | 配置变更/升级后突然出现 | 变更溯源 → 差异对比 | sysctl diff + tc check + dmesg | Module 1 → Step 3.3(内核参数优先) → dmesg 分析 |

**模型选择逻辑**：

```
IF 问题模式 == "偶发":
  → 选择 M-2，提示用户："偶发型延迟最有效的方式是抓现场，建议优先使用 nettrace 实时监控"
  → 推荐路径: Module 1 → Module 5 → (根据 nettrace 结果) → Module 2/3/4

IF 问题模式 == "持续" OR "必现":
  → 选择 M-1，按标准顺序推进
  → 推荐路径: Module 1 → Module 2 → Module 3 → Module 4 → Module 5 → Module 6

IF 问题模式 == "特定时段":
  → 选择 M-3，先采集基线对比数据
  → 推荐路径: Module 1 → Module 2(对比正常/异常时段) → Module 3(带宽)

IF 问题模式 == "新发" AND (用户提到配置变更/升级/内核更新):
  → 选择 M-4，优先检查变更内容
  → 推荐路径: Module 1 → Step 3.3 → dmesg/journal 变更分析
```

### 诊断上下文摘要

问诊结束后，AI 内部生成诊断上下文摘要，**后续所有步骤的命令参数从此摘要中取值**：

```markdown
> **📋 诊断上下文**
> - 目标: <对端IP> (<协议>:<端口>)
> - 出口网卡: <网卡名> (via `ip route get` 推断)
> - 问题模式: <偶发/持续/时段/新发>，<补充描述>
> - 业务: <业务类型>
> - 链路类型: <同机房/同城跨机房/跨地域/跨国>（推断 RTT 基线 < Xms）
> - 分析模型: <M-1/M-2/M-3/M-4>
```

**链路类型自动推断规则**（无需额外询问用户）：

```
WHEN 对端IP为内网IP（10.x.x.x / 172.16-31.x.x / 192.168.x.x）:
  → 初步推断为"同机房"或"同VPC"

链路类型在 Module 2 的 RTT 基线测量后自动修正：
  WHEN ping RTT avg < 1ms   → 推断为"同机房"
  WHEN ping RTT avg 1~5ms   → 推断为"同城跨机房"
  WHEN ping RTT avg 5~50ms  → 推断为"跨地域"
  WHEN ping RTT avg > 100ms → 推断为"跨国"
```

**命令参数绑定规则**（替代硬编码 8.8.8.8/eth0）：

```
所有 ping 命令:   ping -c N <诊断上下文.目标IP>
所有 mtr 命令:    mtr -rwzbc N <诊断上下文.目标IP>
所有 ethtool:     ethtool <诊断上下文.网卡>
所有 tcpdump:     tcpdump -i <诊断上下文.网卡> host <诊断上下文.目标IP>
所有 nettrace:    nettrace --daddr <诊断上下文.目标IP> [--dport <诊断上下文.端口>]
所有 ss 过滤:     ss -i -t dst <诊断上下文.目标IP>
所有 tc/ip link:  tc -s qdisc show dev <诊断上下文.网卡>
```

---

## 症状速查表

> 根据典型症状快速选择分析模型和起始 Module，避免盲目全流程执行。

| 症状特征 | 分析模型 | 推荐起始 Module | 关键命令 |
|---------|---------|----------------|---------|
| 延迟稳定偏高，无抖动 | M-1 持续型 | Module 2 → Module 3 | `ping -c 100`、`mtr -rwzbc 100` |
| 延迟波动大，mdev 高 | M-2 偶发型 | Module 2 → Module 4 | `ping -c 100`、`tc -s qdisc show` |
| 偶发延迟尖刺 | M-2 偶发型 | Module 1 → Module 5 | `nettrace --latency`、`tcpdump` |
| TCP 连接慢，但 ping 正常 | M-1 持续型 | Module 3 → Module 6 | `ss -tin`、`strace` |
| 大文件传输慢 | M-1 持续型 | Module 3（带宽+BDP） | `ethtool`、`ss -tin`、BDP 计算 |
| 新内核/新配置后延迟增加 | M-4 新发型 | Module 1 → Step 3.3 | `sysctl -a \| grep tcp`、`dmesg` |
| 特定时段延迟增高（如工作时间） | M-3 时段型 | Module 2(对比基线) | 监控脚本分时段采集 + `sar` |
| 到特定目标延迟高，到其他目标正常 | M-1 持续型 | Module 2(mtr逐跳) | `mtr -rwzbc 100 <目标IP>` |
| 延迟偶尔飙升伴随 CPU softirq 高 | M-2 偶发型 | Module 4（softirq） | `cat /proc/net/softnet_stat`、`mpstat` |
| 小包延迟高、大包正常 | M-1 持续型 | Step 3.3（Nagle） | `ss -tin`、`sysctl tcp_nodelay` |
| 首次连接慢、后续正常 | M-1 持续型 | Module 4（ARP） | `ip neigh show`、`nettrace --drop` |

---

## 阈值参考表

> **参见 SKILL.md 公共阈值参考表**（本表保留延迟域特有的阈值）

| 指标 | 正常 | 告警 | 严重 | 说明 |
|-----|------|------|------|------|
| RTT 抖动率（mdev/avg）| < 10% | 10% ~ 30% | > 30% | 高抖动通常指向队列/中断合并问题 |
| BDP 窗口匹配率 | > 80% | 50% ~ 80% | < 50% | TCP 窗口 / BDP |
| 中断合并延迟（rx-usecs）| < 50μs | 50 ~ 250μs | > 250μs | ethtool -c 查看 |
| softirq 处理延迟 | < 2ms | 2 ~ 10ms | > 10ms | ksoftirqd 被调度说明 > 2ms |
| ARP 解析时间 | < 5ms | 5 ~ 50ms | > 50ms | 首次通信时增加的额外延迟 |

---

## 诊断步骤

以下命令可由 AI 自动执行，用于诊断延迟问题。所有命令中的目标 IP、网卡名等参数**从 Phase 0 的诊断上下文中取值**，不使用硬编码默认值。

### Module 1：环境预检

> **⚠️ 必须首先执行此步骤**：排除 tc netem 人为注入，并收集系统基本信息。如果在丢包排查的 Step 1.1 中已经检查过且确认无 netem 规则，可以跳过 tc 检查部分。

#### Step 1.1: 排除人为流量控制（tc netem）

```bash
# 查看所有设备上的 qdisc（包括 ifb、veth 等虚拟设备）
tc -s qdisc show 2>/dev/null | grep -v "noqueue"

# 检查是否加载了 ifb/netem 内核模块
lsmod | grep -E "ifb|sch_netem" 2>/dev/null

# 检查出口网卡上是否有 ingress qdisc + filter 重定向（参数从诊断上下文获取）
tc qdisc show dev <诊断上下文.网卡> ingress 2>/dev/null
tc filter show dev <诊断上下文.网卡> parent ffff: 2>/dev/null
```

判断规则和处理方式同丢包排查 Step 1.1。如果发现 netem 规则，直接报告为人为注入。

#### Step 1.2: 收集系统基本信息

```bash
# 系统和内核版本
uname -r
cat /etc/os-release | grep -E "^NAME=|^VERSION="

# 推断出口网卡（如 Phase 0 未确定）（参数从诊断上下文获取）
ip route get <诊断上下文.目标IP> 2>/dev/null | head -1

# 检查 IOMMU 是否开启（IOMMU 可能引入 DMA 映射额外延迟）
# 在虚拟化环境或使用 VFIO 直通时，IOMMU 开启会增加每次 DMA 映射的开销
dmesg 2>/dev/null | grep -i "iommu" | head -5
cat /proc/cmdline 2>/dev/null | grep -oE "(intel_iommu|amd_iommu)=[^ ]+"

# 检查最近的内核网络相关日志（用于 M-4 新发型延迟）
dmesg -T 2>/dev/null | grep -iE "link|nic|eth|drop|error|timeout|reset" | tail -10
```

**判断规则**：
- 如果 IOMMU 开启（`intel_iommu=on` 或 `amd_iommu=on`）且环境为虚拟机/容器直通场景，记录为潜在延迟因素
- 如果 dmesg 中有网卡 link down/up、driver reset 等异常，标记为可能的延迟根因

---

### Module 2：RTT 基线与路径分析

> 合并"确认延迟现象"和"逐跳分析"为一步。通过 ping 建立 RTT 基线，通过 mtr 定位延迟发生在哪一跳。

#### Step 2.1: RTT 基线测量

```bash
# 基础延迟测试（测网关，评估本机出口延迟）
ping -c 20 -i 0.2 $(ip route show default | awk '/default/ {print $3}' | head -1) 2>/dev/null

# 测试到目标的基础延迟（参数从诊断上下文获取）
ping -c 50 -i 0.2 <诊断上下文.目标IP>

# 延迟统计分布（参数从诊断上下文获取）
ping -c 100 -i 0.1 <诊断上下文.目标IP> 2>/dev/null | tail -3
```

**ping 统计行解读**（`min/avg/max/mdev`）：
- `min`：最小延迟，代表网络空闲时的最优路径延迟
- `avg`：平均延迟，**核心关注指标**，对照阈值参考表中对应链路类型判断
- `max`：最大延迟，如果 max 远大于 avg，说明有延迟尖刺
- `mdev`：标准差（mean deviation），**衡量抖动的关键指标**。mdev/avg > 10% 告警，> 30% 严重

**延迟参考基线**（**参见 SKILL.md 公共阈值参考表**）：
- 同机房/同 VPC：< 1ms
- 同城跨机房：< 5ms
- 跨地域（如北京-上海）：10~50ms
- 跨国（如中国-美国西海岸）：150~200ms

#### Step 2.2: 逐跳路径分析

```bash
# 使用 mtr 进行逐跳分析（推荐，综合了 traceroute 和 ping）（参数从诊断上下文获取）
mtr -r -c 50 -n <诊断上下文.目标IP> 2>/dev/null

# 使用 mtr 的 TCP 模式（某些环境 ICMP 被过滤）（参数从诊断上下文获取）
mtr -r -c 50 -n -T -P 443 <诊断上下文.目标IP> 2>/dev/null

# 如果没有 mtr，使用 traceroute（参数从诊断上下文获取）
traceroute -n -w 3 <诊断上下文.目标IP> 2>/dev/null
```

**mtr 各列含义**：
- `Loss%`：该跳的丢包率。中间跳 Loss% 非零但后续跳正常，通常是路由器限速 ICMP 导致，不代表真正丢包
- `Avg`：平均延迟。观察 **Avg 列的增量**：某一跳 Avg 突然大幅增加（如从 5ms 跳到 50ms），该跳是延迟瓶颈
- `StDev`：标准差（抖动指标）。某跳 StDev 很大，说明该段网络不稳定

**⚠️ mtr 丢包率的关键判断规则（避免误判）**：

| 现象 | 判断 | 原因 |
|------|------|------|
| 中间某跳 Loss% 高，但**后续所有跳 Loss% 正常** | **假丢包，忽略** | 该路由器对 ICMP 限速 |
| 中间某跳 Loss% 高，且**后续所有跳 Loss% 也同样高** | **真丢包** | 该跳确实存在丢包 |
| 只有最后一跳 Loss% 高，中间跳正常 | **可能是对端限速 ICMP** | 用 TCP 模式 mtr 验证 |
| 前几跳全部超时（`???`），后续跳正常 | **前几跳屏蔽了探测包** | 云环境/VPN 网关常见 |

**延迟叠加分析**：

> 当测量到的延迟明显高于同类链路的正常基线时，应拆解延迟的组成部分。

拆解方法：
1. **分别测试多个目标**：对比到网关、到同 VPC 内网 IP、到公网 IP 的延迟，区分"本机出口额外延迟"和"链路固有延迟"
2. **结合 mtr 逐跳分析**：如果第 1 跳就有高延迟，说明本机出口侧有额外开销（可能是 tc netem 注入、VPN 隧道封装、或 qdisc 排队）
3. **计算叠加**：`实测延迟 = 本机出口额外延迟 + 链路固有延迟`

#### Module 2 智能分支

> **🔀 智能分支 BR-1**：如果 ping RTT avg 在正常范围内，但 mdev/avg > 20%（抖动大），建议直接跳转到 [Module 4: 队列与软中断分析](#module-4队列与软中断分析)。
>
> **原因**：RTT 均值正常但抖动大，说明不是链路固有延迟问题，通常是本机队列排队、中断合并波动、或 softirq 调度不均匀导致。

> **🔀 智能分支 BR-2**：如果 mtr 显示某跳 RTT 突增 > 前一跳 2 倍，标记该跳为外部网络瓶颈，跳过本机传输层分析。
>
> **原因**：中间网络设备是瓶颈，本机侧无法优化，应输出建议并结束。

---

### Module 3：传输层综合分析

> 覆盖从 NIC 硬件层到传输层的完整延迟链：网卡协商/中断合并 → TCP 拥塞控制/Pacing → 内核参数/Nagle/缓冲区。

#### Step 3.1: 网卡带宽与中断合并检查

> **延迟热点覆盖**：NIC 硬件层（PCIe/DMA 传输延迟）、中断合并（ITR/Interrupt Coalescing）。
> 中断合并是 NIC 为减少 CPU 中断负载而将多个包合并为一次中断通知的机制，会引入微秒到毫秒级的额外延迟。

```bash
# 查看网卡协商速率（参数从诊断上下文获取）
ethtool <诊断上下文.网卡> 2>/dev/null | grep -E "Speed|Duplex|Link detected"

# 查看网卡实时流量（使用 sar）（参数从诊断上下文获取）
sar -n DEV 1 5 2>/dev/null | grep -E "^Average|<诊断上下文.网卡>" || echo "sar 不可用，尝试其他方式"

# 使用 /proc/net/dev 计算实时带宽（参数从诊断上下文获取）
cat /proc/net/dev | grep "<诊断上下文.网卡>"

# 查看网卡队列长度（txqueuelen）（参数从诊断上下文获取）
ip link show <诊断上下文.网卡> | grep qlen

# 查看网络接口错误和丢包统计（参数从诊断上下文获取）
ip -s link show <诊断上下文.网卡> | head -20

# ★ 查看中断合并（Interrupt Coalescing）设置（参数从诊断上下文获取）
# rx-usecs/tx-usecs 越大，单次中断聚合的包越多，但延迟越高
ethtool -c <诊断上下文.网卡> 2>/dev/null
```

**带宽利用率计算**：
- 网卡速率 1000Mb/s = 约 125MB/s 的理论最大吞吐
- 如果 `sar -n DEV` 显示 `rxkB/s` 或 `txkB/s` 接近网卡速率的 70% 以上，说明带宽接近饱和（触发 BR-5）
- 带宽饱和会导致排队延迟增加

**中断合并（Interrupt Coalescing）判断**：
- `rx-usecs` > 250：高延迟场景下可能增加明显的收包延迟，参考阈值表
- `adaptive-rx: on`：自适应模式，根据负载动态调整，一般不需要修改
- `adaptive-rx: off` 且 `rx-usecs` > 100：在延迟敏感场景下考虑降低
- **TX 侧**：`tx-usecs` 高会延迟发送完成通知（TX Completion），影响 TCP 拥塞窗口推进速度

**协商问题**：
- 万兆网卡协商到千兆或百兆：带宽降低 10~100 倍
- 半双工（`Duplex: Half`）：收发不能同时进行
- 参考丢包排查 Step 2.2 的协商排查

#### Step 3.2: TCP 拥塞控制与 Pacing 分析

> **延迟热点覆盖**：TCP 拥塞控制（cwnd 限制/重传延迟）、TCP Pacing（发送速率平滑化）。
> TCP Pacing 是 BBR 等算法将突发数据按时间均匀发送的机制，避免突发导致中间设备排队，但可能在某些场景下限制发送速率。

```bash
# 查看 TCP 连接的详细内部信息（拥塞窗口、RTT、重传等）
ss -i -t state established | head -60

# 查看到特定目标的 TCP 连接详细信息（参数从诊断上下文获取）
ss -i -t dst <诊断上下文.目标IP> 2>/dev/null | head -30

# 查看当前使用的 TCP 拥塞算法
sysctl net.ipv4.tcp_congestion_control

# 查看系统可用的拥塞算法
sysctl net.ipv4.tcp_available_congestion_control

# 查看 TCP 重传统计
cat /proc/net/snmp | grep "^Tcp:"

# 查看扩展 TCP 统计（重传、超时、快速重传等）
cat /proc/net/netstat | grep "^TcpExt:"

# ★ 检查 Pacing 状态（BBR 使用 FQ qdisc 实现 pacing）（参数从诊断上下文获取）
# 如果拥塞算法是 bbr，配合 fq qdisc 才能正确 pacing
tc -s qdisc show dev <诊断上下文.网卡> 2>/dev/null | head -5
```

**`ss -i` 关键字段**：
- `rtt:X/Y`：X 是平滑 RTT（微秒或毫秒），Y 是 RTT 变化量。**rtt 远大于 ping 延迟说明有协议栈延迟或排队**
- `cwnd:N`：拥塞窗口大小（MSS 段数）。cwnd 小说明处于慢启动或拥塞恢复阶段
- `retrans:X/Y`：X 是当前未确认的重传段数，Y 是总重传次数。**重传多说明链路丢包导致延迟增加**
- `pacing_rate Xbps`：当前 Pacing 发送速率。如果 pacing_rate 远低于链路带宽，可能是 Pacing 限制了发送速度
- `delivery_rate Xbps`：实际数据交付速率。delivery_rate << pacing_rate 说明网络侧有瓶颈
- `send Xbps`：当前发送速率估算

**TCP Pacing 判断**：
- 拥塞算法为 `bbr` 但 qdisc 不是 `fq`：Pacing 无法正确工作，可能导致突发丢包和延迟
- `pacing_rate` 远低于期望带宽：检查 BBR 是否正确估计了带宽（可能被丢包干扰）
- 重传率 > 1%：每次重传至少增加一个 RTT 的延迟（**参见 SKILL.md 公共阈值参考表**）

**拥塞算法影响**：
- `cubic`：Linux 默认算法，适合大多数场景
- `bbr`：基于带宽和 RTT 估算，在高延迟高丢包链路上表现更好，需配合 `fq` qdisc
- `reno`：早期算法，丢包恢复较慢

#### Step 3.3: TCP 内核参数与缓冲区检查

> **延迟热点覆盖**：Nagle 算法（小包聚合延迟）、TCP 发送缓冲区阻塞、延迟确认（Delayed ACK）、慢启动重启。

```bash
# 查看 TCP 缓冲区配置（min/default/max）
sysctl net.ipv4.tcp_rmem
sysctl net.ipv4.tcp_wmem
sysctl net.core.rmem_max
sysctl net.core.wmem_max

# 查看 TCP 窗口缩放和时间戳
sysctl net.ipv4.tcp_window_scaling
sysctl net.ipv4.tcp_timestamps

# 查看 Nagle 算法和延迟确认相关
# ⚠️ Nagle 算法会聚合小包直到收到前一个包的 ACK 或凑够 MSS，对交互式/低延迟业务有明显影响
sysctl net.ipv4.tcp_slow_start_after_idle

# 查看 TCP 连接超时和重试相关
sysctl net.ipv4.tcp_syn_retries
sysctl net.ipv4.tcp_synack_retries
sysctl net.ipv4.tcp_retries2

# 查看 TCP Keepalive 参数
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_intvl
sysctl net.ipv4.tcp_keepalive_probes
```

**缓冲区与 BDP（Bandwidth-Delay Product）**：
- BDP = 带宽 × RTT，表示链路上"在途"数据量
- 例如：1Gbps 链路、20ms RTT → BDP = 1000Mbps × 0.02s = 20Mbit = 2.5MB
- 如果 `tcp_rmem`/`tcp_wmem` 的 max 值小于 BDP，TCP 吞吐无法达到链路上限
- **发送缓冲区阻塞**：当 `tcp_wmem` 耗尽时，`send()`/`write()` 系统调用会阻塞，导致应用层感知到的延迟增加

**Nagle 算法影响**：
- Nagle 算法（TCP_NODELAY 未设置时默认开启）会将小包聚合，等待前一个包的 ACK 或凑够 MSS 再发送
- 对交互式协议（Redis、MySQL 短查询、HTTP/2 小帧）影响明显，可增加 RTT 量级的延迟
- 应用应通过 `setsockopt(TCP_NODELAY, 1)` 关闭 Nagle，这是应用层设置，内核参数无法全局控制
- **Nagle + Delayed ACK 叠加**：当发送端开启 Nagle 且接收端开启 Delayed ACK（默认 40ms），小包延迟可达 40ms+

**窗口缩放（`tcp_window_scaling`）**：
- 值为 1（开启）：允许 TCP 接收窗口超过 65535 字节，高 BDP 链路必须开启
- 值为 0（关闭）：接收窗口最大 64KB，严重限制高延迟链路性能

**慢启动重启（`tcp_slow_start_after_idle`）**：
- 值为 1（默认）：空闲后重新慢启动，会导致间歇性传输的连接性能下降
- 值为 0：空闲后不重置拥塞窗口，适合有长连接但间歇传输的场景

#### Module 3 智能分支

> **🔀 智能分支 BR-3**：如果 `ss -i` 显示的 TCP RTT ≈ ping RTT（差距 < 15%），建议直接跳转到 [Module 6: 应用层分析](#module-6应用层分析)。
>
> **原因**：传输层没有额外引入延迟，问题在应用层（recv() 慢、处理逻辑耗时等）。

> **🔀 智能分支 BR-4**：如果 TCP RTT >> ping RTT（差距 > 50%），需深入分析 Module 3 各子项 + Module 4 队列分析。
>
> **原因**：传输层（拥塞控制/缓冲区/重传/排队）引入了额外延迟，需要逐项排除。

> **🔀 智能分支 BR-5**：如果带宽利用率 > 70%，聚焦分析 BDP 与窗口配置。
>
> **原因**：带宽饱和是延迟根因，需确认 TCP 窗口/缓冲区能支撑对应的 BDP 需求。

---

### Module 4：队列与软中断分析

> 覆盖 Qdisc 排队延迟、softirq 调度延迟（ksoftirqd 降级）、GRO 聚合等待、ARP/邻居表解析延迟等内核协议栈底层延迟热点。这些是从"NIC 驱动→softirq→协议栈入口"这一段的关键延迟来源。

#### Step 4.1: Qdisc 队列延迟分析

```bash
# 查看所有网络接口的 qdisc 配置和统计（包括 ifb 等虚拟设备）
tc -s qdisc show 2>/dev/null

# 查看指定接口的 qdisc 详细信息（参数从诊断上下文获取）
tc -s qdisc show dev <诊断上下文.网卡> 2>/dev/null

# 查看 tc class 信息（如果有流量整形）（参数从诊断上下文获取）
tc -s class show dev <诊断上下文.网卡> 2>/dev/null

# 查看 tc filter 规则（参数从诊断上下文获取）
tc -s filter show dev <诊断上下文.网卡> 2>/dev/null

# 查看网卡 TX 队列长度（参数从诊断上下文获取）
ip link show <诊断上下文.网卡> | grep qlen
```

**qdisc 统计关键指标**：
- `dropped N`：**被 qdisc 丢弃的包数，非零说明队列满导致丢包和延迟**
- `backlog Xb Yp`：**当前队列积压的字节数和包数，持续非零说明有排队延迟**
- `overlimits N`：超过速率限制的次数

**常见 qdisc 类型与延迟特性**：
- `pfifo_fast`：默认无类队列，FIFO + 简单优先级
- `fq`（Fair Queue）：公平队列，per-flow 排队，配合 BBR 使用支持 TCP Pacing
- `fq_codel`：公平队列 + CoDel 主动队列管理，减少 bufferbloat
- `tbf`（Token Bucket Filter）：令牌桶限速，`dropped` 非零说明限速导致丢包
- `htb`（Hierarchy Token Bucket）：分层令牌桶，复杂限速场景

**排队延迟估算**：
- 如果 `backlog` 显示 100 个包积压，每个包 1500 字节，网卡速率 1Gbps：
- 排队延迟 ≈ 100 × 1500 × 8 / 1,000,000,000 = 1.2ms
- 在低速链路上（如 100Mbps），同样的积压会导致 12ms 延迟

#### Step 4.2: softirq 调度延迟与 ksoftirqd 分析

> **延迟热点覆盖**：softirq 调度延迟、ksoftirqd 降级处理。
> 网络包的协议栈处理在 softirq（NET_RX_SOFTIRQ/NET_TX_SOFTIRQ）中完成。当 softirq 处理时间过长（超过 2ms 或处理包数超过 netdev_budget），内核会将剩余工作交给 ksoftirqd 内核线程以普通进程优先级调度，导致处理延迟从微秒级退化到毫秒级。

```bash
# 查看 softnet_stat（每 CPU 的网络包处理统计）
# 各列含义：processed, dropped, time_squeeze, ...
cat /proc/net/softnet_stat

# 查看 netdev_budget（每次 softirq 最多处理的包数）
sysctl net.core.netdev_budget
sysctl net.core.netdev_budget_usecs

# 查看 netdev backlog 队列上限
sysctl net.core.netdev_max_backlog

# 查看各 CPU 的软中断负载分布
mpstat -P ALL 1 3 2>/dev/null | grep -v "^$"

# 检查 ksoftirqd 是否频繁被调度（ksoftirqd 活跃说明 softirq 处理积压）
ps aux | grep ksoftirqd | grep -v grep

# 查看中断亲和性分布（确认网卡中断是否分散到多个 CPU）（参数从诊断上下文获取）
cat /proc/interrupts | grep -E "eth|ens|<诊断上下文.网卡>" | head -10
```

**softnet_stat 各列解读**：
- **第 1 列（processed）**：该 CPU 处理的总包数
- **第 2 列（dropped）**：因 backlog 队列满而丢弃的包数，非零说明 `netdev_max_backlog` 不够
- **第 3 列（time_squeeze）**：softirq 因超时/超预算而主动让出的次数，**非零说明 softirq 处理时间不够，有延迟风险**

**判断规则**：
- `time_squeeze` 持续增长 → softirq 处理积压，包被延迟处理，考虑增大 `netdev_budget`
- `dropped` 非零 → backlog 队列溢出，增大 `netdev_max_backlog`
- `mpstat` 某核 `%soft` > 30% 而其他核接近 0 → 中断亲和性不均，所有网络处理集中在单核，考虑开启 RSS/RPS
- `ksoftirqd` CPU 占用高 → softirq 已降级为线程处理，网络包处理延迟增加

#### Step 4.3: GRO 聚合与 IP 分片

> **延迟热点覆盖**：GRO（Generic Receive Offload）聚合等待、IP 分片重组延迟。
> GRO 将多个小包合并为大包再交给协议栈处理，减少协议栈处理次数但引入聚合等待延迟。IP 分片重组需要等待所有分片到齐才能交给上层。

```bash
# 查看 GRO 是否开启（参数从诊断上下文获取）
ethtool -k <诊断上下文.网卡> 2>/dev/null | grep "generic-receive-offload"

# 查看 LRO（Large Receive Offload，硬件层面的聚合）（参数从诊断上下文获取）
ethtool -k <诊断上下文.网卡> 2>/dev/null | grep "large-receive-offload"

# 查看 IP 分片统计（分片重组可能引入延迟）
cat /proc/net/snmp | grep "^Ip:"
# 关注 ReasmReqds（重组请求数）和 ReasmFails（重组失败数）
```

**判断规则**：
- GRO 开启是常态，一般不需要关闭。但在延迟极度敏感的场景（如高频交易）中，关闭 GRO 可减少 ~50μs 的聚合等待
- IP 分片重组失败（`ReasmFails` 增长）说明有分片丢失导致超时重组，增加延迟
- 如果 MTU 不匹配导致频繁分片（`FragCreates` 高），考虑调整 MTU 或开启 Path MTU Discovery

#### Step 4.4: ARP/邻居表解析延迟

> **延迟热点覆盖**：ARP 解析延迟、邻居表（Neighbor Table）状态。
> 首次通信时需要通过 ARP 请求解析对端 MAC 地址，未命中 ARP 缓存时会触发 ARP 请求-响应流程，引入额外的 RTT 延迟。在大规模组网中 ARP 表满也可能导致频繁的 ARP 解析。

```bash
# 查看 ARP/邻居表
ip neigh show | head -20

# 查看邻居表中 STALE/FAILED 状态的条目数
ip neigh show | awk '{print $NF}' | sort | uniq -c | sort -rn

# 查看 ARP 表大小限制
sysctl net.ipv4.neigh.default.gc_thresh1
sysctl net.ipv4.neigh.default.gc_thresh2
sysctl net.ipv4.neigh.default.gc_thresh3

# 查看 ARP 缓存超时
sysctl net.ipv4.neigh.default.base_reachable_time_ms
```

**判断规则**：
- 大量 `STALE` 状态条目：ARP 缓存已过期，下次通信需要重新解析（增加 1 个 RTT）
- `FAILED` 状态条目：ARP 解析失败，可能导致首包丢弃或长时间等待
- ARP 条目数接近 `gc_thresh3`：邻居表即将满，新条目可能被拒绝或触发 GC，影响延迟
- 首次连接慢但后续正常 → 典型的 ARP 解析延迟症状

---

### Module 5：nettrace 协议栈延迟与 RTT 分析

> **本模块可在任意步骤后插入使用**，不必等到 Module 5。特别是 M-2（偶发型延迟）模型推荐在 Module 1 之后直接使用 nettrace 抓现场。
>
> nettrace 可一次性定位协议栈各环节的处理耗时（DMA→softirq→协议栈→传输层→socket），是最高效的延迟定位工具。
>
> 如果 nettrace 已安装（参考丢包排查 Step 4.1），可以使用延迟分析功能精确定位协议栈各环节的处理耗时。完整的命令参数说明参见 `references/nettrace.md`。
>
> ⚠️ **AI 执行约束**同丢包排查 Step 4.2（详见 `references/nettrace.md` AI 执行约束章节）：流式命令用 `timeout <N>` 包裹，默认 30 秒。

#### Step 5.1: 协议栈延迟分析

```bash
# 显示报文在协议栈各环节的处理延迟（参数从诊断上下文获取）
sudo timeout <N> nettrace -p tcp --daddr <诊断上下文.目标IP> --dport <诊断上下文.端口> --latency-show

# 过滤处理时长超过 1ms 的报文（单位 us）（参数从诊断上下文获取）
sudo timeout <N> nettrace -p tcp --daddr <诊断上下文.目标IP> --dport <诊断上下文.端口> --min-latency 1000

# 高效延迟分析模式（性能开销小，适合大流量场景）（参数从诊断上下文获取）
sudo timeout <N> nettrace -p tcp --latency --daddr <诊断上下文.目标IP> --dport <诊断上下文.端口> --min-latency 1000

# 延迟分布统计（每秒刷新）（参数从诊断上下文获取）
sudo timeout <N> nettrace -p tcp --latency --latency-summary --daddr <诊断上下文.目标IP> --dport <诊断上下文.端口>
```

**输出解读**：
- `--latency-show` 模式：在每个内核函数后显示 `latency: X.XXXms`，最后显示 `total latency` 总耗时
- `--latency` 模式：高效模式，只跟踪总耗时，性能开销小
- `--latency-summary` 模式：显示延迟分布直方图（us 粒度）

**分阶段延迟分析**：可以使用 `-t`/`--trace-matcher`/`--trace-free` 参数组合精确定位哪个环节引入延迟（收包队列延迟、CPU 处理延迟、Nagle 聚合延迟、qdisc 排队延迟等）。详见 `references/nettrace.md` 协议栈延迟分析章节。

#### Step 5.2: TCP RTT 分析

```bash
# RTT 分布统计（每秒刷新）
sudo timeout <N> nettrace --rtt

# 查看每个报文的 RTT 详情
sudo timeout <N> nettrace --rtt-detail

# 过滤 srtt 超过 10ms 的连接
sudo timeout <N> nettrace --sock -t tcp_ack_update_rtt --filter-srtt 10

# 过滤特定目标的 RTT（参数从诊断上下文获取）
sudo timeout <N> nettrace --rtt-detail --daddr <诊断上下文.目标IP>
```

**输出解读**：`rtt` 为平滑 RTT，`rtt_min` 为实际 RTT。`--rtt` 模式显示 ms 粒度分布直方图，结合 `--filter-srtt` 可监控超阈值 RTT 连接。详见 `references/nettrace.md` RTT 分析章节。

---

### Module 6：应用层分析

> 覆盖从 Socket 到应用进程的延迟链：Socket Backlog 处理延迟、进程唤醒/调度延迟、应用层系统调用阻塞。

#### Step 6.1: Socket 队列与 Backlog 分析

> **延迟热点覆盖**：TCP Socket Backlog 处理延迟、Socket 接收/发送队列积压。
> 当应用通过 `lock_sock()` 持有 socket 锁时（如正在执行 `sendmsg()`），此时到达的数据包会被放入 socket backlog 队列，等待锁释放后再处理。在高并发场景下，backlog 处理延迟可达毫秒级。

```bash
# 查看 socket 接收/发送队列积压
ss -tnp | awk 'NR>1 {if($2>0 || $3>0) print}' | head -20
# 第二列 Recv-Q > 0 说明应用没有及时 recv()；第三列 Send-Q > 0 说明数据在发送缓冲区积压

# 查看到特定目标的 socket 队列状态（参数从诊断上下文获取）
ss -tnp dst <诊断上下文.目标IP> 2>/dev/null

# 查看 LISTEN 状态的 socket 队列（SYN 队列和 Accept 队列）
ss -tlnp | head -20
# Recv-Q > 0（LISTEN 状态）：等待 accept 的连接数，高说明应用 accept 太慢

# 查看 socket backlog 大小限制
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

**Socket 队列积压分析**：
- `Recv-Q > 0`（ESTABLISHED 状态）：数据已到达内核但应用未读取，**应用层处理慢**
- `Send-Q > 0`（ESTABLISHED 状态）：数据已交给内核但未发送完毕，**可能是网络拥塞或对端接收窗口小**
- `Recv-Q > 0`（LISTEN 状态）：等待 accept 的连接数，高说明应用 accept 太慢

#### Step 6.2: 进程调度与唤醒延迟

> **延迟热点覆盖**：Socket 唤醒后进程调度延迟。
> 当数据到达 socket 时，内核通过 `sk_data_ready()` 唤醒等待的进程。但被唤醒的进程需要被调度到 CPU 上运行才能实际处理数据，调度延迟取决于 CPU 负载和调度策略。

```bash
# 查看系统 CPU 负载（判断是否 CPU 繁忙导致调度延迟）
uptime
mpstat -P ALL 1 3 2>/dev/null | tail -20

# 查看进程的 CPU 亲和性
taskset -p <PID> 2>/dev/null

# 查看进程调度策略
chrt -p <PID> 2>/dev/null
```

**判断规则**：
- CPU 负载高（load average > CPU 核数）且应用延迟高 → 进程调度排队导致的延迟
- 网络处理线程被绑定在繁忙的 CPU 核上 → 考虑调整 CPU 亲和性

#### Step 6.3: 应用层系统调用分析

```bash
# 使用 strace 跟踪网络相关系统调用耗时（指定 PID）
# 注意：strace 有性能开销，仅在排查时短暂使用
strace -e trace=network -T -c -p <PID> 2>&1 | head -30

# 查看进程的网络 socket 信息
ls -la /proc/<PID>/fd 2>/dev/null | grep socket | head -10

# 如果有 bpftrace，跟踪 TCP 发送延迟（需要 root）
# 统计 tcp_sendmsg 的耗时分布
bpftrace -e 'kprobe:tcp_sendmsg { @start[tid] = nsecs; } kretprobe:tcp_sendmsg /@start[tid]/ { @usecs = hist((nsecs - @start[tid]) / 1000); delete(@start[tid]); }' 2>/dev/null &
sleep 10 && kill %1 2>/dev/null

# 如果有 perf，跟踪网络相关函数延迟
perf trace -e sendto,recvfrom,connect -p <PID> -T -- sleep 5 2>/dev/null | head -30
```

**区分内核延迟与应用延迟**：
- `ss -i` 的 rtt 正常（接近 ping 值）但应用感知延迟高 → 应用层处理慢
- `ss -i` 的 rtt 远大于 ping 值 → 内核协议栈处理有延迟（队列积压、softirq 延迟）
- `Recv-Q` 持续积压 → 应用 recv() 太慢（CPU 忙或应用逻辑耗时）
- `Send-Q` 持续积压 → 网络侧瓶颈（拥塞、窗口小、带宽不足）

**strace 延迟分析**：
- `sendto` / `send` 耗时高：发送缓冲区满导致阻塞
- `recvfrom` / `recv` 耗时高：等待数据到达（可能是对端慢或网络延迟）
- `connect` 耗时高：TCP 三次握手延迟（网络 RTT + SYN 排队）
- `poll` / `epoll_wait` 耗时高：等待事件就绪，通常是正常的 IO 等待

---

## 常见问题、操作参考、命令速查与流程图

> 📎 FAQ（Q1~Q6）、操作参考（iperf3/拥塞算法/TCP缓冲区/qdisc/中断合并/softirq预算/ARP表）、命令速查表（25 条）和快速排查流程图（Mermaid + 文字版）请参见 **`references/faq-latency.md`**。

## 相关技能

- **network-check**：网络基础连通性排查 | **syscall-hotspot**：系统调用热点分析 | **sched-latency**：调度延迟分析
