# 丢包排查 — 常见问题、操作参考与命令速查

> 本文件是 `packet-loss.md` 的补充参考，包含常见问题解答、操作参考和命令速查表。
> 公共阈值请参见 `SKILL.md`，核心诊断流程请参见 `packet-loss.md`。

---

## 常见问题解答

### Q1: 怎么快速判断丢包发生在哪一层？

按以下顺序排查，可以快速定位丢包层级：

```bash
# 1. 先看网卡硬件层是否有丢包（参数从诊断上下文获取）
ethtool -S <诊断上下文.网卡> 2>/dev/null | grep -iE "error|drop|miss|fifo|crc" | grep -v ": 0$"

# 2. 再看驱动/接口层（参数从诊断上下文获取）
ip -s link show <诊断上下文.网卡> | grep -A 2 "RX:"

# 3. 看 softnet 层
cat /proc/net/softnet_stat

# 4. 看协议栈层
netstat -s | grep -iE "error|drop|retrans|overflow|fail" | head -20
```

**判断逻辑**：
- `ethtool -S` 有错误计数 → 网卡硬件层问题（Ring Buffer、协商、CRC 等）
- `ip -s link` 的 dropped/overrun 非零 → 驱动层问题
- `softnet_stat` 第二列非零 → softnet backlog 溢出
- `netstat -s` 有大量重传/错误 → 协议栈层问题

### Q2: softnet_stat 怎么读？

```bash
cat /proc/net/softnet_stat
# 输出示例：
# 00035720 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
# 000268c4 00000000 00000002 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
```

每行代表一个 CPU（第一行是 CPU0），每列含义：
- **第1列**：该 CPU 处理的总包数
- **第2列**：因 `netdev_max_backlog` 溢出丢弃的包数（**非零 = 丢包**）
- **第3列**：`time_squeeze` 次数，软中断 CPU 时间不足（**持续增长 = 需增大 netdev_budget**）
- 值均为十六进制

### Q3: 重传率多少算异常？

```bash
# 计算重传率
cat /proc/net/snmp | grep "^Tcp:" | awk 'NR==2{printf "重传段: %s\n发送段: %s\n重传率: %.4f%%\n", $13, $12, $13/$12*100}'
```

**参考标准**（**参见 SKILL.md 公共阈值参考表**）：
- 重传率 < 0.1%：正常
- 重传率 0.1% ~ 1%：轻微丢包，需关注
- 重传率 > 1%：严重丢包，需立即处理

### Q4: conntrack 满了怎么确认？

```bash
# 查看当前连接跟踪数和最大值
sysctl net.netfilter.nf_conntrack_count
sysctl net.netfilter.nf_conntrack_max

# 查看是否有 conntrack 丢包日志
dmesg | grep -i "nf_conntrack: table full" | tail -5
```

如果 `nf_conntrack_count` 接近或等于 `nf_conntrack_max`，新连接会被丢弃。dmesg 中会有 `nf_conntrack: table full, dropping packet` 日志。

### Q5: perf 跟踪 kfree_skb 没有输出怎么办？

> 💡 **推荐使用 nettrace 替代 perf 跟踪 kfree_skb**：`nettrace --drop` 可直接监控丢包并显示丢包原因，`nettrace --diag` 可自动诊断网络故障并给出修复建议。详见 `references/nettrace.md`。

```bash
# 推荐：使用 nettrace 监控丢包（<N> 为用户指定的监控秒数）
sudo timeout <N> nettrace --drop

# 如果 nettrace 不可用，检查 perf 工具是否可用
which perf && perf --version

# 检查 tracepoint 是否存在
ls /sys/kernel/debug/tracing/events/skb/kfree_skb 2>/dev/null

# 检查 perf_event_paranoid 设置
cat /proc/sys/kernel/perf_event_paranoid
# 值为 -1 或 0 才允许非 root 用户使用；值为 2 需要 root 权限
```

如果 tracepoint 不存在，可能是内核未编译 `CONFIG_TRACEPOINTS` 或版本过低。如果权限不足，需要以 root 身份执行或调整 `perf_event_paranoid`。

### Q6: 怎么区分是本机丢包还是网络链路丢包？

```bash
# 方法1：对比本机接口统计和对端统计（参数从诊断上下文获取）
# 本机发送计数
ip -s link show <诊断上下文.网卡> | grep -A 2 "TX:"
# 对端接收计数（需要在对端执行）
# ip -s link show <网卡> | grep -A 2 "RX:"

# 方法2：使用 mtr 逐跳分析（参数从诊断上下文获取）
mtr -r -c 50 -n <诊断上下文.目标IP> 2>/dev/null

# 方法3：源端和目的端同时 tcpdump 抓包对比
```

**判断逻辑**：
- 本机 TX 正常但对端 RX 少 → 网络链路丢包
- 本机 RX 的 dropped/errors 非零 → 本机接收端丢包
- mtr 中某一跳开始出现丢包 → 该跳的网络设备问题
- mtr 中只有最后一跳丢包 → 对端可能屏蔽了 ICMP

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及系统配置变更，AI 不会自动执行！**
>
> 请用户根据诊断结果，自行判断是否需要执行以下操作。

### 1. 增大 Ring Buffer

```bash
# 查看当前值和最大值（参数从诊断上下文获取）
ethtool -g <诊断上下文.网卡>

# 增大 Ring Buffer（根据硬件最大值调整）（参数从诊断上下文获取）
ethtool -G <诊断上下文.网卡> rx 4096 tx 4096
```

### 2. 修复网卡协商问题

```bash
# 重新自协商（参数从诊断上下文获取）
ethtool -r <诊断上下文.网卡>

# 如果上游不支持自协商，强制设置速率和双工（参数从诊断上下文获取）
ethtool -s <诊断上下文.网卡> speed 10000 duplex full autoneg off
```

### 3. 关闭网卡流控

```bash
# 关闭自协商流控（参数从诊断上下文获取）
ethtool -A <诊断上下文.网卡> autoneg off

# 关闭发送方向流控（参数从诊断上下文获取）
ethtool -A <诊断上下文.网卡> tx off

# 关闭接收方向流控（参数从诊断上下文获取）
ethtool -A <诊断上下文.网卡> rx off
```

### 4. 调整内核网络参数

```bash
# 增大 softnet backlog 队列长度（默认 1000）
sysctl -w net.core.netdev_max_backlog=10000

# 增大 NAPI poll 预算（默认 300）
sysctl -w net.core.netdev_budget=600

# 增大 conntrack 最大值
sysctl -w net.netfilter.nf_conntrack_max=262144

# 永久生效
echo "net.core.netdev_max_backlog = 10000" >> /etc/sysctl.conf
echo "net.core.netdev_budget = 600" >> /etc/sysctl.conf
sysctl -p
```

### 5. 调整中断亲和性

```bash
# 查看网卡中断号（参数从诊断上下文获取）
grep <诊断上下文.网卡> /proc/interrupts | awk '{print $1}' | tr -d ':'

# 手动设置中断亲和性（将中断绑定到指定 CPU）
echo <cpu_mask> > /proc/irq/<irq_num>/smp_affinity

# 或使用 irqbalance 自动均衡
systemctl restart irqbalance
```

### 6. 调整 MTU

```bash
# 查看当前 MTU（参数从诊断上下文获取）
ip link show <诊断上下文.网卡> | grep mtu

# 调整 MTU（需要两端和中间设备都支持）（参数从诊断上下文获取）
ip link set <诊断上下文.网卡> mtu 9000  # 开启巨帧
ip link set <诊断上下文.网卡> mtu 1500  # 标准以太网
```

### 7. tcpdump 抓包

```bash
# 基本抓包（限制包数防止磁盘写满）（参数从诊断上下文获取）
tcpdump -i <诊断上下文.网卡> host <诊断上下文.目标IP> and port <端口> -c 10000 -w /tmp/capture.pcap

# 注意：磁盘空间充足时可增大 -c 值，或使用 -C 按大小轮转
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看接口错误统计 | `ip -s link show <网卡>` |
| 查看网卡详细计数 | `ethtool -S <网卡>` |
| 查看非零错误计数 | `ethtool -S <网卡> \| grep -iE "error\|drop" \| grep -v ": 0$"` |
| 查看 Ring Buffer 大小 | `ethtool -g <网卡>` |
| 查看网卡协商状态 | `ethtool <网卡>` |
| 查看网卡流控配置 | `ethtool -a <网卡>` |
| 查看光模块状态 | `ethtool -m <网卡>` |
| 查看 softnet 统计 | `cat /proc/net/softnet_stat` |
| 查看 CPU 软中断 | `mpstat -P ALL 1 3` |
| 查看中断分布 | `grep <网卡> /proc/interrupts` |
| 查看协议栈统计 | `netstat -s` 或 `cat /proc/net/snmp` |
| 查看扩展 TCP 统计 | `cat /proc/net/netstat` |
| 查看丢包统计 | `cat /proc/net/dropstat` |
| 查看 conntrack 使用率 | `sysctl net.netfilter.nf_conntrack_count` |
| 跟踪丢包路径 | `perf record -e skb:kfree_skb -g -a -- sleep 10` |
| 监控丢包 | `dropwatch -l kas` |
| **nettrace 丢包监控** | **`timeout <N> nettrace --drop`** |
| **nettrace 丢包监控+调用栈** | **`timeout <N> nettrace --drop --drop-stack`** |
| **nettrace 故障诊断** | **`timeout <N> nettrace --diag --diag-quiet`** |
| **nettrace 报文跟踪** | **`timeout <N> nettrace -p tcp --daddr <IP> --dport <端口>`** |
| **nettrace 诊断+防火墙** | **`timeout <N> nettrace --diag --hooks --saddr <IP>`** |
| 计算重传率 | `cat /proc/net/snmp \| grep "^Tcp:"` |
| 网络抓包 | `tcpdump -i <网卡> host <IP> -c 1000 -w /tmp/cap.pcap` |
