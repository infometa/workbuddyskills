# nettrace 网络诊断工具

> 本文件为 AI 执行网络丢包与延迟排查时提供 nettrace 工具的使用参考。涵盖工具概述、安装方法、各诊断模式的命令用法与输出解读、AI 执行约束及版本兼容性。

---

## 一、概述

nettrace 是基于 eBPF 的集**网络报文跟踪**、**网络故障诊断**、**网络异常监控**于一体的网络工具集。

### 核心能力

| 能力 | 说明 |
|------|------|
| 报文生命周期跟踪 | 跟踪报文在内核协议栈中的完整路径（从网卡驱动到用户态 socket） |
| 丢包监控 | 监控系统中的所有丢包事件，显示 70+ 种丢包原因（skb drop reason） |
| 智能故障诊断 | 自动分析报文异常，给出 INFO/WARN/ERROR 级别提示和修复建议 |
| 协议栈延迟分析 | 测量报文在协议栈各环节的处理耗时 |
| TCP RTT 分析 | 统计和分析 TCP 连接的 RTT 分布 |

### 项目地址

- 源码仓库：`https://gitee.com/OpenCloudOS/nettrace.git`
- 适用内核：Linux 4.x ~ 6.x（不同版本编译方式不同，详见安装章节）

### 与传统工具对比

| 特性 | nettrace | perf kfree_skb | dropwatch | tcpdump |
|------|----------|----------------|-----------|---------|
| 丢包原因（drop reason） | ✅ 70+ 种 | ❌ 仅调用栈 | ❌ 仅函数地址 | ❌ |
| 智能故障诊断 | ✅ 自动分析 | ❌ | ❌ | ❌ |
| 报文生命周期跟踪 | ✅ 完整路径 | ❌ 仅丢包点 | ❌ | ❌ 仅网卡层 |
| 协议栈延迟分析 | ✅ 各环节耗时 | ❌ | ❌ | ❌ |
| RTT 分析 | ✅ 分布统计 | ❌ | ❌ | ❌ |
| NAT 场景跟踪 | ✅ 地址变更后仍持续跟踪 | ❌ | ❌ | 部分 |
| iptables/nftables 适配 | ✅ 显示经过的表和链 | ❌ | ❌ | ❌ |

---

## 二、安装

### 2.1 检查是否已安装

```bash
which nettrace && nettrace -V
```

### 2.2 包管理器安装（优先）

OpenCloudOS/TencentOS 系统可直接在线安装：

```bash
# TencentOS 2
sudo yum install -y nettrace

# TencentOS 3/4
sudo dnf install -y nettrace
```

安装后验证：
```bash
which nettrace && nettrace -V
```

### 2.3 源码编译安装

包管理器安装失败时，使用源码编译：

**a. 下载源码**
```bash
git clone https://gitee.com/OpenCloudOS/nettrace.git
cd nettrace
```

**b. 安装编译依赖**
```bash
# TencentOS 2
sudo yum install -y python3-yaml elfutils-devel elfutils-devel-static libbpf-devel libbpf-static kernel-headers kernel-devel clang llvm bpftool

# TencentOS 3/4
sudo dnf install -y python3-yaml elfutils-devel elfutils-devel-static libbpf-devel libbpf-static kernel-headers kernel-devel clang llvm bpftool
```

**c. 判断内核是否支持 BTF**
```bash
ls /sys/kernel/btf/vmlinux 2>/dev/null && echo "BTF supported" || echo "BTF not supported"
```

**d. 编译**
```bash
# 支持 BTF 的内核（内核版本 >= 5.3，且 CONFIG_DEBUG_INFO_BTF=y）
make all

# 不支持 BTF 的内核（内核版本 < 5.3）
make NO_BTF=1 all

# 低版本内核（<= 4.15）的兼容模式
make COMPAT=1 all
```

**e. 安装到系统 PATH**
```bash
# 安装到 /usr/local/bin（需要 root 权限）
sudo cp nettrace /usr/local/bin/nettrace
sudo chmod +x /usr/local/bin/nettrace
which nettrace && nettrace -V
```

备选方案（无 root 权限）：
```bash
mkdir -p ~/bin
cp nettrace ~/bin/nettrace
chmod +x ~/bin/nettrace
export PATH="$HOME/bin:$PATH"
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
which nettrace && nettrace -V
```

---

## 三、丢包监控（--drop）

替代 dropwatch，监控系统中的所有丢包事件。

### 基本用法

```bash
# 监控系统丢包（显示丢包原因）
sudo timeout <N> nettrace --drop

# 监控丢包并打印内核调用栈
sudo timeout <N> nettrace --drop --drop-stack
```

### 过滤选项

```bash
# 按协议过滤
sudo timeout <N> nettrace --drop -p tcp
sudo timeout <N> nettrace --drop -p icmp

# 按地址/端口过滤
sudo timeout <N> nettrace --drop --daddr <目标IP>
sudo timeout <N> nettrace --drop --port <端口>

# 限制输出速率（生产环境推荐）
sudo timeout <N> nettrace --drop --rate-limit 100
```

### 输出解读

每行显示一个丢包事件，包含协议、源/目的地址端口、丢包原因（reason）和丢包位置（内核函数）。

**常见丢包原因（drop reason）**：

| reason | 含义 |
|--------|------|
| `NOT_SPECIFIED` | 未指定具体原因（低版本内核或特定路径） |
| `NO_SOCKET` | 目标端口无监听 |
| `NETFILTER_DROP` | 被防火墙规则丢弃 |
| `TCP_INVALID_SEQUENCE` | TCP 序列号无效 |
| `TCP_CLOSE` | TCP 连接已关闭 |
| `SKB_DROP_REASON_FULL` | 队列/缓冲区满 |

> 更多丢包原因可通过 `man dropreason` 查看，内核支持 70+ 种丢包原因枚举。

---

## 四、故障诊断模式（--diag）

跟踪报文完整生命周期并自动分析异常，给出修复建议。

### 基本用法

```bash
# 诊断模式 - 跟踪指定报文并自动分析
sudo timeout <N> nettrace --diag -p icmp --saddr <源IP>
sudo timeout <N> nettrace --diag -p tcp --daddr <目标IP> --dport <端口>

# 只显示异常报文（过滤正常报文）
sudo timeout <N> nettrace --diag --diag-quiet

# 持续诊断（默认发现异常后会退出，加 --diag-keep 持续跟踪）
sudo timeout <N> nettrace --diag --diag-keep --diag-quiet

# 诊断 + 显示 netfilter 钩子函数（定位防火墙丢包）
sudo timeout <N> nettrace --diag --saddr <源IP> --hooks

# 显示详细信息（进程、网口、CPU 等）
sudo timeout <N> nettrace --diag --detail --saddr <源IP>
```

### 输出解读

诊断模式提供三种级别提示：

| 级别 | 含义 | 示例 |
|------|------|------|
| `INFO` | 正常信息提示 | 经过了某个 iptables 链 |
| `WARN` | 警告信息，需关注 | 发生了 NAT 地址转换 |
| `ERROR` | 异常信息，报文发生了问题 | 被防火墙丢弃、端口未监听 |

**诊断结果**（`ANALYSIS RESULT`）会列出所有异常事件，并给出 `fix advice`（修复建议）。

**关键特性**：
- 支持 iptables-legacy 和 iptables-nft 的完美适配，能够显示报文经过的 iptables 表和链
- 结合 `--hooks` 参数可以打印出 netfilter HOOK 上所有的钩子函数，深入分析第三方模块导致的丢包

---

## 五、报文生命周期跟踪（默认模式）

跟踪报文在内核协议栈中的完整路径。

### 基本用法

```bash
# 跟踪 ICMP 报文的完整内核路径
sudo timeout <N> nettrace -p icmp --saddr <源IP>

# 跟踪 TCP 报文
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --dport <端口>

# 显示详细信息（进程、网口、CPU）
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --dport <端口> --detail

# 以时间格式打印时间戳
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --dport <端口> --date

# 限制跟踪报文个数（会自动退出，无需 timeout）
sudo nettrace -p icmp --saddr <源IP> -c 5

# 打印指定函数的内核调用栈
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --trace-stack kfree_skb
```

### 输出解读

- 每行显示报文经过的内核函数和时间戳
- `kfree_skb`：报文被内核丢弃（非正常释放路径）
- `consume_skb`：报文正常消费释放
- 通过观察报文的内核路径，可以精确定位丢包发生在协议栈的哪个环节
- 支持 NAT 场景：报文地址被 NAT 修改后仍会持续跟踪

---

## 六、协议栈延迟分析

### 6.1 基本延迟分析

```bash
# 显示报文在协议栈各环节的处理延迟
sudo timeout <N> nettrace -p icmp --latency-show --saddr <源IP>

# 显示 TCP 报文的延迟信息
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --dport <端口> --latency-show

# 过滤处理时长超过 1ms 的报文（单位 us）
sudo timeout <N> nettrace -p tcp --daddr <目标IP> --dport <端口> --min-latency 1000

# 高效延迟分析模式（性能开销小，适合大流量场景）
sudo timeout <N> nettrace -p tcp --latency --daddr <目标IP> --dport <端口> --min-latency 1000

# 延迟分布统计（每秒刷新）
sudo timeout <N> nettrace -p tcp --latency --latency-summary --daddr <目标IP> --dport <端口>
```

**延迟分析模式对比**：

| 模式 | 参数 | 说明 | 适用场景 |
|------|------|------|----------|
| 详细延迟 | `--latency-show` | 显示每个内核函数的耗时 | 精确定位延迟环节 |
| 高效延迟 | `--latency` | 只跟踪总耗时，性能开销小 | 大流量场景 |
| 延迟分布 | `--latency-summary` | 显示延迟分布直方图（us 粒度） | 分析延迟分布特征 |
| 延迟过滤 | `--min-latency <us>` | 只显示超过阈值的报文 | 过滤正常报文 |

### 6.2 分阶段延迟分析

精确定位协议栈中哪个环节引入了延迟：

```bash
# 收包阶段：报文放到收包队列 -> 用户取走的延迟（用户态程序收包不及时）
sudo timeout <N> nettrace -p tcp --latency \
    -t tcp_queue_rcv,tcp_data_queue_ofo \
    --trace-matcher tcp_queue_rcv,tcp_data_queue_ofo \
    --latency-free --min-latency 1000

# 收包阶段：网卡驱动收包 -> 放到套接口收包队列的延迟（CPU 处理延迟）
sudo timeout <N> nettrace -p tcp --latency \
    -t __netif_receive_skb_core,tcp_queue_rcv,tcp_data_queue_ofo \
    --trace-matcher __netif_receive_skb_core \
    --trace-free tcp_queue_rcv,tcp_data_queue_ofo --min-latency 1000

# 发包阶段：报文放到发送队列 -> 开始发送的延迟（nagle 算法引发的聚合延迟）
sudo timeout <N> nettrace -p tcp --latency \
    -t skb_entail,tcp_skb_entail,__tcp_transmit_skb,__tcp_retransmit_skb \
    --trace-matcher skb_entail,tcp_skb_entail \
    --trace-free __tcp_transmit_skb,__tcp_retransmit_skb --min-latency 1000

# 发包阶段：传输层到网卡驱动层的延迟（qdisc 排队延迟）
sudo timeout <N> nettrace -p tcp --latency \
    -t __ip_queue_xmit,dev_hard_start_xmit \
    --trace-matcher __ip_queue_xmit \
    --trace-free dev_hard_start_xmit --min-latency 1000
```

**各阶段延迟含义**：

| 阶段 | 跟踪函数 | 高延迟原因 |
|------|----------|-----------|
| 收包队列 → 用户读取 | `tcp_queue_rcv` → 用户 `recv()` | 应用层处理慢，recv() 不及时 |
| 网卡驱动 → 收包队列 | `__netif_receive_skb_core` → `tcp_queue_rcv` | CPU 软中断处理延迟 |
| 发送队列 → 开始发送 | `skb_entail` → `__tcp_transmit_skb` | Nagle 算法聚合等待 |
| 传输层 → 网卡驱动 | `__ip_queue_xmit` → `dev_hard_start_xmit` | qdisc 排队延迟 |

---

## 七、TCP RTT 分析

### 基本用法

```bash
# RTT 分布统计（每秒刷新）
sudo timeout <N> nettrace --rtt

# 查看每个报文的 RTT 详情
sudo timeout <N> nettrace --rtt-detail

# 过滤 srtt 超过 10ms 的连接
sudo timeout <N> nettrace --sock -t tcp_ack_update_rtt --filter-srtt 10

# 过滤特定目标的 RTT
sudo timeout <N> nettrace --rtt-detail --daddr <目标IP>
```

### 输出解读

| 字段 | 含义 |
|------|------|
| `rtt` | 经过平滑处理的 RTT（smoothed RTT） |
| `rtt_min` | 本次发送报文被确认过程中的实际 RTT |
| RTT 直方图 | `--rtt` 模式下显示 ms 粒度的分布图 |

结合 `--filter-srtt` 可以监控系统中超过一定阈值的 RTT，快速发现延迟异常的连接。

---

## 八、参数速查表

### 通用过滤参数

| 参数 | 说明 |
|------|------|
| `-p <proto>` | 协议过滤：tcp、udp、icmp |
| `--saddr <IP>` | 源 IP 地址过滤 |
| `--daddr <IP>` | 目的 IP 地址过滤 |
| `--sport <port>` | 源端口过滤 |
| `--dport <port>` | 目的端口过滤 |
| `--port <port>` | 匹配源端口或目的端口 |
| `-c <count>` | 限制跟踪报文个数（达到后自动退出） |

### 丢包监控参数

| 参数 | 说明 |
|------|------|
| `--drop` | 丢包监控模式 |
| `--drop-stack` | 丢包时打印内核调用栈 |
| `--rate-limit <N>` | 限制输出速率（每秒最多 N 条） |

### 故障诊断参数

| 参数 | 说明 |
|------|------|
| `--diag` | 故障诊断模式 |
| `--diag-quiet` | 只显示异常报文（过滤正常报文） |
| `--diag-keep` | 持续诊断（默认发现异常后退出） |
| `--hooks` | 显示 netfilter 钩子函数 |
| `--detail` | 显示详细信息（进程、网口、CPU） |

### 报文跟踪参数

| 参数 | 说明 |
|------|------|
| `--trace-stack <func>` | 打印指定函数的内核调用栈 |
| `--date` | 以时间格式打印时间戳 |

### 延迟分析参数

| 参数 | 说明 |
|------|------|
| `--latency-show` | 显示每个内核函数间的延迟 |
| `--latency` | 高效延迟分析（仅跟踪总耗时） |
| `--min-latency <us>` | 过滤延迟低于阈值的报文（单位微秒） |
| `--latency-summary` | 显示延迟分布直方图 |
| `--latency-free` | 延迟结束标记 |

### RTT 分析参数

| 参数 | 说明 |
|------|------|
| `--rtt` | RTT 分布统计 |
| `--rtt-detail` | 每个报文的 RTT 详情 |
| `--filter-srtt <ms>` | 过滤 srtt 超过阈值的连接 |

### 高级参数

| 参数 | 说明 |
|------|------|
| `-t <funcs>` | 指定跟踪的内核函数列表 |
| `--trace-matcher <funcs>` | 指定延迟分析的起始函数 |
| `--trace-free <funcs>` | 指定延迟分析的结束函数 |
| `--sock` | socket 级别跟踪模式 |

---

## 九、AI 执行约束

### 流式输出处理

nettrace 的大部分命令是流式输出的（持续监控，不会自动退出），AI 直接执行会导致命令挂住。**必须遵循以下规则**：

1. **先询问用户**需要监控多长时间（如 10 秒、30 秒、60 秒），获取 `<N>` 秒
2. **所有流式命令必须用 `timeout <N>` 包裹**，确保命令在指定时间后自动退出
3. 如果用户没有明确指定时长，**默认使用 30 秒**
4. 已有 `-c` 参数限制报文个数的命令（如 `-c 5`）可以不加 `timeout`，因为它们会自动退出

### IP 地址/端口获取策略

很多命令需要 `--saddr`/`--daddr`/`--dport` 来过滤目标流量。如果用户没有提供：

1. **先用全局监控命令**（如 `nettrace --drop`、`nettrace --diag --diag-quiet`、`nettrace --rtt`）进行初步采集
2. **从全局监控结果中提取信息**：分析输出中频繁出现的 IP 地址和端口
3. **向用户确认**：将发现的可疑 IP/端口反馈给用户，确认后再使用带过滤条件的命令做精确诊断
4. 也可以**直接询问用户**需要分析的目标 IP 和端口

### 权限要求

nettrace 需要 root 权限运行，命令前需加 `sudo`。

---

## 十、版本兼容性

### 各 TencentOS 版本安装方式

| 版本 | 安装方式 | 包管理器 |
|------|---------|---------|
| TencentOS 2 | `yum install nettrace` 或源码编译 | yum |
| TencentOS 3 | `dnf install nettrace` 或源码编译 | dnf |
| TencentOS 4 | `dnf install nettrace` 或源码编译 | dnf |

### BTF 支持情况

| 条件 | 编译方式 |
|------|---------|
| 内核 >= 5.3 且 `CONFIG_DEBUG_INFO_BTF=y` | `make all` |
| 内核 < 5.3（无 BTF） | `make NO_BTF=1 all` |
| 内核 <= 4.15（低版本兼容） | `make COMPAT=1 all` |

判断方法：
```bash
ls /sys/kernel/btf/vmlinux 2>/dev/null && echo "BTF supported" || echo "BTF not supported"
```

### 功能差异

- 高版本内核（>= 5.17）引入了 `kfree_skb_reason`，nettrace `--drop` 可直接显示丢包原因枚举
- nettrace 的 `--drop` 模式可完全替代 dropwatch，且支持更丰富的丢包原因分析
- 支持 iptables-legacy 和 iptables-nft 适配（TencentOS 4 默认使用 nftables）
