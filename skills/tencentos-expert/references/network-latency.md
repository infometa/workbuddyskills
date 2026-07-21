---
name: network-latency
description: Diagnose network packet loss and latency issues by analyzing NIC hardware, driver, protocol stack, and application layers
description_zh: 排查网络丢包和延迟问题，从网卡硬件到协议栈逐层分析定位
description_en: Diagnose network packet loss and latency issues by analyzing NIC hardware, driver, protocol stack, and application layers
version: 2.0.0
---

# 网络丢包与延迟排查

帮助排查网络丢包和延迟问题，从 TCP/IP 协议栈底层到上层逐层分析。
丢包排查覆盖网卡硬件层、网卡驱动层、协议栈层的丢包检测与定位，支持使用 nettrace 进行报文生命周期跟踪、智能故障诊断和丢包监控。
延迟排查覆盖 RTT 异常、网络抖动、逐跳延迟定位、TCP 拥塞窗口分析、带宽瓶颈、nettrace 协议栈延迟分析与 RTT 统计、应用层延迟定位、队列延迟等场景。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看统计、查看配置、查看计数），**不自动执行以下高危操作**：
> 
> - 不自动修改网卡 Ring Buffer 大小（ethtool -G）
> - 不自动修改网卡协商参数（ethtool -s / ethtool -r）
> - 不自动修改网卡流控配置（ethtool -A）
> - 不自动修改内核网络参数（sysctl -w）
> - 不自动修改中断亲和性配置
> - 不自动执行 tcpdump 长时间抓包（避免磁盘写满）
> - 不自动修改 TCP 拥塞算法（sysctl tcp_congestion_control）
> - 不自动修改 qdisc/tc 队列配置（tc qdisc change/replace）
> - 不自动修改中断合并参数（ethtool -C）
> - 不自动执行 iperf3 带宽测试（占用带宽）
>
> 以上操作仅作为参考提供给用户，由用户自行判断和手动执行。

## 诊断前置检查（强制）

> **🚨 无论是丢包排查还是延迟排查，在执行任何 ping、mtr 等诊断命令之前，必须先执行以下检查，排除人为的 tc netem 流量控制注入。违反此规则会导致严重误判。**

```bash
# 【强制第一步】检查是否存在人为注入的 netem 规则
tc -s qdisc show 2>/dev/null | grep -v "noqueue"
lsmod | grep -E "ifb|sch_netem" 2>/dev/null
tc qdisc show dev eth0 ingress 2>/dev/null
tc filter show dev eth0 parent ffff: 2>/dev/null
```

**如果输出中出现 `qdisc netem`（在任何设备上，包括 ifb0）或 `lsmod` 显示 `sch_netem`/`ifb` 模块已加载**：
- → **立即停止后续诊断**，直接向用户报告：当前系统存在通过 tc netem 人为注入的丢包/延迟/抖动，指出具体参数
- → 给出清除命令供用户参考：`tc qdisc del dev ifb0 root; tc qdisc del dev eth0 handle ffff: ingress`
- → 用户确认清除后再重新开始诊断

**如果未发现 netem 规则** → 根据问题类型，通过下方「诊断路由规则」选择加载对应的诊断文件。

## 适用场景

### 用户可能的问题表述

**"网络丢包"类**（最常见）：
- "网络丢包严重"、"丢包率很高"、"为什么丢包"
- "ping 丢包"、"丢包怎么排查"、"丢包原因是什么"
- "服务器丢包"、"内网丢包"、"packet loss"
- "数据包丢了"、"收不到包"、"包被丢了"

**"网卡丢包/错误"类**：
- "网卡有 error"、"网卡有 drop"、"ethtool 看到丢包"
- "rx errors 很多"、"rx dropped 在增长"、"rx overrun"
- "ifconfig 看到错误计数"、"ip -s link 有丢包"
- "网卡 ring buffer 满了"、"fifo error"
- "CRC 校验错误"、"网线有问题吗"

**"网卡协商/配置"类**：
- "网卡速率不对"、"协商到了百兆"、"应该是万兆但只有千兆"
- "duplex 不对"、"半双工"、"自协商失败"
- "网卡流控"、"pause 帧"、"flow control"
- "MTU 不匹配"、"巨帧"、"jumbo frame"

**"驱动层丢包"类**：
- "softnet backlog 满了"、"netdev_max_backlog"
- "软中断丢包"、"IRQ 丢包"、"中断不均衡"
- "某个核软中断特别高"、"单核 si% 很高"
- "irqbalance 没生效"、"中断亲和性"
- "softnet_stat 有丢包"、"napi"

**"协议栈丢包"类**：
- "netstat -s 看到丢包"、"TCP 重传多"、"重传率高"
- "segments retransmited"、"SYN 重传"
- "conntrack 满了"、"nf_conntrack 丢包"
- "/proc/net/snmp 异常"、"dropstat 有计数"
- "kfree_skb"、"dropwatch 看到丢包"

**"抓包分析"类**：
- "需要抓包看看"、"tcpdump 怎么抓"
- "怎么确认包丢在哪里"、"源端有发但目的端没收到"
- "perf 跟踪丢包"、"skb:kfree_skb"

**"nettrace 报文跟踪与诊断"类**：
- "用 nettrace 跟踪一下"、"nettrace 看看"
- "报文在内核里走到哪了"、"报文路径"、"报文生命周期"
- "nettrace 诊断模式"、"网络故障诊断"、"协议栈跟踪"
- "skb drop reason"、"丢包原因是什么"
- "nettrace --drop"、"nettrace --diag"、"nettrace --latency"
- "网络异常监控"、"丢包监控"

**"网络延迟/RTT 异常"类**：
- "网络延迟高"、"ping 延迟大"、"网络慢"
- "RTT 异常"、"RTT 高"、"响应时间长"
- "网络响应慢"、"连接建立慢"、"三次握手慢"

**"网络抖动/不稳定"类**：
- "网络抖动"、"延迟不稳定"、"jitter 大"
- "网络时好时坏"、"延迟忽高忽低"
- "mdev 很大"、"延迟波动"

**"传输慢/带宽"类**：
- "传输速度慢"、"下载慢"、"上传慢"
- "带宽不够"、"带宽跑不满"、"吞吐低"
- "iperf 测速慢"、"scp 很慢"

**"TCP 拥塞/窗口"类**：
- "拥塞窗口小"、"cwnd 很小"、"TCP 拥塞"
- "窗口缩放"、"接收窗口小"、"发送窗口小"
- "TCP 缓冲区"、"socket buffer"、"BDP"

**"队列延迟"类**：
- "qdisc 延迟"、"tc 队列"、"流量整形延迟"
- "bufferbloat"、"队列积压"、"backlog 延迟"

---

## 诊断路由规则

AI 读取本文件（SKILL.md）后，根据用户问题的关键词判断加载哪个诊断文件：

### 路由判断

| 用户问题匹配关键词 | 加载文件 | 说明 |
|-------------------|---------|------|
| 丢包、drop、packet loss、rx error、rx dropped、Ring Buffer、conntrack 满、ethtool -S 丢包、重传 | `packet-loss.md` | 丢包诊断完整流程 |
| 延迟、RTT、慢、latency、jitter、抖动、拥塞、带宽慢、队列延迟、传输慢 | `latency.md` | 延迟诊断完整流程 |
| 同时涉及丢包和延迟（如"丢包且延迟高"） | 按**主要症状**先加载一个文件，另一个作为辅助参考 | — |

> **📂 文件加载指引**：
> - **丢包排查** → 请读取本文件同目录下的 **`packet-loss.md`** 文件，获取完整的丢包诊断流程（Phase 0 问诊 + Module 1~7 诊断步骤）。
> - **延迟排查** → 请读取本文件同目录下的 **`latency.md`** 文件，获取完整的延迟诊断流程（Phase 0 问诊 + Module 1~6 诊断步骤）。
> - **两个文件都依赖本文件的「安全原则」「诊断前置检查」和「公共阈值参考表」**，请确保先阅读本文件的公共部分。

---

## 公共阈值参考表

> 丢包和延迟诊断流程中的判断规则统一引用此表。各子文件中保留其域特有的阈值。

### 网络基线阈值

| 指标 | 正常 | 告警 | 严重 | 说明 |
|-----|------|------|------|------|
| 同机房 RTT | < 1ms | 1 ~ 5ms | > 5ms | ping -c 100 的 avg |
| 同城跨机房 RTT | < 5ms | 5 ~ 20ms | > 20ms | |
| 跨地域 RTT | < 50ms | 50 ~ 100ms | > 100ms | |
| TCP 重传率 | < 0.1% | 0.1% ~ 1% | > 1% | /proc/net/snmp 统计 |
| 带宽利用率 | < 50% | 50% ~ 70% | > 70% | 实际/标称比值 |
| 丢包率 | 0% | 0.01% ~ 0.1% | > 0.1% | ping 或 ethtool 统计 |

### NIC/驱动层阈值

| 指标 | 正常 | 告警 | 严重 | 说明 |
|-----|------|------|------|------|
| 网卡队列丢包 | 0 | 偶发 | 持续增长 | ethtool -S 的 drop 计数 |
| softnet_stat 丢包 | 0 | 偶发 | 持续增长 | /proc/net/softnet_stat 第二列 |
| conntrack 使用率 | < 70% | 70% ~ 90% | > 90% | nf_conntrack_count / nf_conntrack_max |
| 单核 si% | < 50% | 50% ~ 80% | > 80% | mpstat -P ALL 软中断占比 |

---

## 公共命令速查表

> 完整的命令速查表在各诊断文件中（`packet-loss.md` / `latency.md`）。以下为最常用命令。

| 场景 | 命令 |
|------|------|
| 查看接口错误统计 | `ip -s link show <网卡>` |
| 查看网卡详细计数 | `ethtool -S <网卡>` |
| 查看 Ring Buffer 大小 | `ethtool -g <网卡>` |
| 查看网卡协商状态 | `ethtool <网卡>` |
| 查看 softnet 统计 | `cat /proc/net/softnet_stat` |
| 查看 CPU 软中断 | `mpstat -P ALL 1 3` |
| 查看协议栈统计 | `netstat -s` 或 `cat /proc/net/snmp` |
| 查看 conntrack 使用率 | `sysctl net.netfilter.nf_conntrack_count` |
| TCP 连接详情 | `ss -tin dst <目标IP>` |
| nettrace 丢包监控 | `timeout <N> nettrace --drop` |
| nettrace 故障诊断 | `timeout <N> nettrace --diag --diag-quiet` |
| nettrace 协议栈延迟 | `timeout <N> nettrace --latency-show` |
| 基础延迟测试 | `ping -c 50 -i 0.2 <目标IP>` |
| 逐跳路径分析 | `mtr -r -c 50 -n <目标IP>` |
| 网络抓包 | `tcpdump -i <网卡> host <IP> -c 1000 -w /tmp/cap.pcap` |

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|-------------|-------------|-------------|
| 网卡统计命令 | `ifconfig` / `ip` | `ip`（推荐） | `ip`（推荐） |
| ethtool | 可用 | 可用 | 可用 |
| softnet_stat | 可用 | 可用 | 可用 |
| mpstat | `yum install sysstat` | `dnf install sysstat` | `dnf install sysstat` |
| perf | `yum install perf` | `dnf install perf` | `dnf install perf` |
| tcpdump | `yum install tcpdump` | `dnf install tcpdump` | `dnf install tcpdump` |
| dropwatch | 需手动安装 | `dnf install dropwatch` | `dnf install dropwatch` |
| nettrace | `yum install nettrace` 或源码编译 | `dnf install nettrace` 或源码编译 | `dnf install nettrace` 或源码编译 |
| kfree_skb tracepoint | 可用 | 可用 | 可用（语义可能有变化） |
| conntrack | `iptables` 后端 | `iptables` 后端 | `nftables` 后端 |
| 中断亲和性工具 | 手动配置 | 有系统脚本 | 有系统脚本 |
| mtr | `yum install mtr` | `dnf install mtr` | `dnf install mtr` |
| iperf3 | `yum install iperf3` | `dnf install iperf3` | `dnf install iperf3` |
| tc (iproute2) | 可用 | 可用 | 可用 |
| sar (sysstat) | `yum install sysstat` | `dnf install sysstat` | `dnf install sysstat` |
| bpftrace | 需手动编译 | `dnf install bpftrace` | `dnf install bpftrace` |
| 默认 TCP 拥塞算法 | `cubic` | `cubic` | `cubic`（可切换 `bbr`） |
| 默认 qdisc | `pfifo_fast` | `fq_codel` | `fq_codel` |

> **注意**：
> - TencentOS 2 使用 `yum` 安装工具，TencentOS 3/4 使用 `dnf`
> - TencentOS 3/4 上推荐使用 `ip` 命令替代 `ifconfig`
> - 不同内核版本中 `kfree_skb` 的语义可能有差异，高版本内核引入了 `kfree_skb_reason`，可以直接看到丢包原因枚举
> - nettrace 的安装方式、BTF 兼容性、与传统工具的对比详见 `references/nettrace.md`
> - TencentOS 2 默认 qdisc 为 `pfifo_fast`，TencentOS 3/4 默认为 `fq_codel`（更好的延迟控制）
> - BBR 拥塞算法在 TencentOS 3/4 的内核中已内置，TencentOS 2 需确认内核版本是否支持
> - bpftrace 在 TencentOS 2 上需手动编译安装，TencentOS 3/4 可直接通过包管理器安装
> - 禁止引用 CentOS / RHEL，统一使用 TencentOS 的说法

---

## 相关技能

- **network-check**：网络基础连通性排查（ping 不通、端口不通、DNS、防火墙、路由等基础问题）
- **syscall-hotspot**：系统调用热点分析（如果怀疑是应用层系统调用导致的网络性能问题）
- **sched-latency**：调度延迟分析（如果怀疑是 CPU 调度导致的网络处理延迟）
