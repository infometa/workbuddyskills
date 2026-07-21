---
name: network-check
description: 诊断网络连通性问题，包括 ping 不通、端口不通、DNS 解析失败、 网络延迟高、丢包、防火墙拦截、路由异常、网卡故障等各类网络故障。 支持从基础连通性到高级网络诊断的完整排查流程。
description_zh: 网络连通性诊断与故障排查
description_en: Network connectivity diagnostics and troubleshooting
version: 1.0.0
---

# 网络连通性排查

帮助诊断网络连通性问题，包括 ping 不通、端口不通、DNS 解析失败、网络延迟高、丢包、防火墙拦截、路由异常等各类网络故障。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看、分析），**不自动执行网络配置变更操作**。
> 
> 修改网络配置（如修改 IP、修改路由、修改防火墙规则等）仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**"上不了网"类**（最常见）：
- "网不通了"、"ping 不了"、"网络突然不行了"
- "服务器连不上"、"断网了"、"连不上互联网"
- "上不了网怎么办"、"网络不通帮我看看"
- "ssh 连不上了"、"刚还好好的突然就不通了"

**端口连不上类**：
- "为什么访问不了我的网站"、"nginx 启动了但访问不了"
- "端口不通"、"telnet 连不上"、"curl 超时"
- "服务部署了但外面连不上"、"3306 端口不通"
- "端口被拦了"、"端口开了但访问不了"

**DNS 解析失败类**：
- "域名解析不了"、"nslookup 失败"
- "ping IP 通但 ping 域名不通"、"DNS 不工作了"
- "解析到了错误的 IP"、"域名解析很慢"
- "resolv.conf 配置有问题吗"

**网络延迟/丢包类**：
- "网络很卡"、"延迟高"、"丢包严重"
- "ssh 很卡"、"传文件很慢"、"下载速度慢"
- "ping 延迟几百毫秒"、"丢包率很高"
- "网络时好时坏"、"网络抖动"

**网卡/IP 配置类**：
- "看不到 IP 地址"、"网卡没启动"
- "IP 地址变了"、"DHCP 获取不到地址"
- "多个 IP 怎么看"、"网卡 down 了"
- "eth0 不见了"、"ifconfig 看不到网卡"

**路由问题类**：
- "路由不对"、"网关不通"、"默认路由没了"
- "traceroute 卡住了"、"出不了公网"
- "能 ping 内网但出不了外网"、"路由表怎么看"
- "多网卡路由冲突"、"策略路由不生效"

**防火墙/安全组类**：
- "端口被防火墙拦了"、"iptables 规则不对"
- "firewalld 拦截了"、"安全组没放行"
- "怎么查看防火墙规则"、"怎么看端口有没有放行"
- "nftables 规则怎么查"

**连接状态/端口占用类**：
- "端口被占用了"、"哪个进程在用 80 端口"
- "TIME_WAIT 太多"、"连接数太多了"
- "ESTABLISHED 连接怎么这么多"
- "查看网络连接状态"

## 诊断步骤

以下命令可由 AI 自动执行，用于诊断网络问题。

### 步骤 1：检查网络接口状态

```bash
# 查看所有网络接口及 IP 地址
ip addr show

# 简洁查看 IP 地址
ip -brief addr show

# 查看网卡链路状态（UP/DOWN）
ip link show

# 查看网卡详细信息（速率、双工等）
ethtool eth0 2>/dev/null | grep -E "Speed|Duplex|Link detected"

# 查看网卡流量统计（是否有大量错误/丢弃）
ip -s link show eth0
```

**输出解读**：
- `state UP`：网卡已启用
- `state DOWN`：网卡未启动或线缆未连接
- `NO-CARRIER`：物理链路未连接
- `inet x.x.x.x/xx`：已分配 IP 地址
- 没有 `inet` 行：未获取到 IP

### 步骤 2：测试基础连通性（Ping）

```bash
# 测试网关是否可达（先获取默认网关）
ip route show default
ping -c 4 -W 3 $(ip route show default | awk '/default/ {print $3}' | head -1)

# 测试外网连通性
ping -c 4 -W 3 8.8.8.8
ping -c 4 -W 3 114.114.114.114

# 测试域名连通性（同时验证 DNS）
ping -c 4 -W 3 www.baidu.com

# 指定源 IP ping（多网卡场景）
ping -c 4 -I eth0 8.8.8.8
```

**输出解读**：
- `0% packet loss`：网络正常
- `100% packet loss`：完全不通
- `time=xxx ms`：延迟值（局域网 <1ms，同城 <10ms，跨区域 <50ms 为正常）
- `Destination Host Unreachable`：目标不可达，通常是路由或网关问题
- `Request timeout`：超时，可能是防火墙拦截或网络拥塞

### 步骤 3：测试 DNS 解析

```bash
# 查看当前 DNS 配置
cat /etc/resolv.conf

# 测试 DNS 解析
nslookup www.baidu.com
dig www.baidu.com +short

# 指定 DNS 服务器测试（排除本机 DNS 配置问题）
nslookup www.baidu.com 8.8.8.8
dig @114.114.114.114 www.baidu.com +short

# 反向解析
dig -x 8.8.8.8 +short

# 查看 DNS 解析耗时
dig www.baidu.com | grep "Query time"

# 检查 /etc/hosts 是否有干扰
grep -v "^#" /etc/hosts | grep -v "^$"

# 检查 nsswitch 配置
grep "hosts:" /etc/nsswitch.conf
```

**常见 DNS 问题**：
- `SERVFAIL`：DNS 服务器故障
- `NXDOMAIN`：域名不存在
- `connection timed out`：DNS 服务器不可达
- 解析结果与预期不符：检查 `/etc/hosts` 是否有覆盖条目

### 步骤 4：测试端口连通性

```bash
# 使用 curl 测试 HTTP/HTTPS 端口（最常用）
curl -v -m 5 http://目标IP:端口/ 2>&1 | head -20
curl -o /dev/null -s -w "HTTP状态码: %{http_code}\n连接耗时: %{time_connect}s\n总耗时: %{time_total}s\n" http://目标IP:端口/

# 使用 ss 查看端口是否在监听
ss -tlnp | grep :80

# 使用 bash 内置测试 TCP 端口（不需要额外工具）
timeout 3 bash -c 'echo > /dev/tcp/目标IP/端口' && echo "端口可达" || echo "端口不可达"

# 使用 nc 测试端口
nc -zv -w 3 目标IP 端口

# 批量测试常用端口
for port in 22 80 443 3306 6379 8080; do
    timeout 2 bash -c "echo > /dev/tcp/目标IP/$port" 2>/dev/null && echo "端口 $port 开放" || echo "端口 $port 关闭"
done
```

**端口不通的常见原因**：
1. 服务未启动（`ss -tlnp` 看不到端口）
2. 服务只监听了 127.0.0.1（需改为 0.0.0.0）
3. 防火墙拦截
4. 安全组未放行（云服务器）

### 步骤 5：检查路由

```bash
# 查看完整路由表
ip route show

# 查看默认路由
ip route show default

# 查看到目标 IP 经过哪条路由
ip route get 8.8.8.8

# 路由追踪（查看经过哪些节点）
traceroute -n -w 3 目标IP 2>/dev/null || tracepath -n 目标IP

# 使用 mtr 交互式路由追踪（更详细的丢包/延迟信息）
mtr -r -c 10 -n 目标IP 2>/dev/null

# 查看策略路由规则
ip rule show
ip route show table all | grep -v "^local"
```

**输出解读**：
- `default via x.x.x.x`：默认网关
- `traceroute` 中 `* * *`：该节点不响应 ICMP 或被过滤
- `traceroute` 某跳后全 `*`：从该点起网络不通
- `mtr` 中 `Loss%` 列：丢包率，>5% 需关注

### 步骤 6：检查防火墙规则

```bash
# 查看 firewalld 状态和规则（TencentOS 3/4）
systemctl status firewalld
firewall-cmd --list-all

# 查看 firewalld 开放的端口
firewall-cmd --list-ports

# 查看 firewalld 允许的服务
firewall-cmd --list-services

# 查看 iptables 规则（所有版本通用）
iptables -L -n -v --line-numbers
iptables -t nat -L -n -v

# 查看 nftables 规则（TencentOS 4）
nft list ruleset 2>/dev/null | head -50

# 检查是否有 REJECT/DROP 规则拦截了目标
iptables -L -n -v | grep -E "DROP|REJECT"
```

**防火墙排查思路**：
1. 先确认防火墙是否开启（`systemctl status firewalld`）
2. 查看是否有 DROP/REJECT 规则命中了目标端口
3. 注意 INPUT/OUTPUT/FORWARD 链的默认策略（policy）

### 步骤 7：检查网络连接状态

```bash
# 查看所有 TCP 连接状态统计
ss -s

# 查看所有监听端口
ss -tlnp

# 查看所有 TCP 连接
ss -tnp

# 查看指定端口的连接
ss -tnp | grep :80

# 统计各连接状态数量
ss -tn | awk '{print $1}' | sort | uniq -c | sort -rn

# 查看 TIME_WAIT 数量
ss -tn state time-wait | wc -l

# 查看 ESTABLISHED 连接数
ss -tn state established | wc -l

# 查看哪个进程占用了指定端口
ss -tlnp | grep :8080
lsof -i :8080 2>/dev/null
```

### 步骤 8：高级网络诊断

```bash
# 抓包分析（需要 root）
tcpdump -i eth0 -c 20 host 目标IP -nn
tcpdump -i eth0 -c 10 port 80 -nn

# 查看 ARP 缓存（排查局域网问题）
ip neigh show

# 查看网络内核参数
sysctl -a 2>/dev/null | grep -E "net.ipv4.ip_forward|net.ipv4.tcp_tw_reuse|net.core.somaxconn"

# 检查网络错误统计
netstat -i 2>/dev/null || ip -s link show

# 查看网卡队列和中断
cat /proc/interrupts | grep eth0 2>/dev/null
ethtool -S eth0 2>/dev/null | grep -E "error|drop|miss" | grep -v ": 0$"
```

---

## 常见问题解答

### Q1: ping 不通怎么一步步排查？

按顺序检查：

```bash
# 1. 网卡是否 UP，IP 是否正常
ip addr show

# 2. 网关是否可达
ping -c 2 $(ip route show default | awk '/default/ {print $3}' | head -1)

# 3. 外网是否可达
ping -c 2 8.8.8.8

# 4. DNS 是否正常
ping -c 2 www.baidu.com
```

**判断逻辑**：
- 网卡 DOWN → 网卡问题
- 网关不通 → 本机网络配置或物理链路问题
- 网关通、外网不通 → 网关出口或运营商问题
- IP 通、域名不通 → DNS 问题

### Q2: 服务启动了但外部访问不了？

```bash
# 1. 确认服务在监听
ss -tlnp | grep :端口号

# 2. 确认监听地址不是 127.0.0.1
# 如果是 127.0.0.1:80 → 只能本机访问，需改为 0.0.0.0:80

# 3. 确认防火墙放行
firewall-cmd --list-ports

# 4. 本机测试
curl -v http://127.0.0.1:端口号/

# 5. 同网段测试
curl -v http://本机IP:端口号/
```

### Q3: 怎么判断是丢包还是延迟高？

```bash
# 使用 mtr 是最好的方式（综合了 ping 和 traceroute）
mtr -r -c 100 -n 目标IP

# 或者用 ping 大量测试
ping -c 100 目标IP

# 解读：
# - Loss% > 0: 有丢包
# - Avg > 100ms: 延迟偏高
# - StDev 很大: 网络抖动严重（不稳定）
```

### Q4: TIME_WAIT 太多怎么办？

```bash
# 查看 TIME_WAIT 数量
ss -tn state time-wait | wc -l

# 查看当前内核参数
sysctl net.ipv4.tcp_tw_reuse
sysctl net.ipv4.tcp_fin_timeout
sysctl net.ipv4.tcp_max_tw_buckets

# TIME_WAIT 是正常的 TCP 行为，只有数量过大(>10000)才需要关注
```

### Q5: 怎么判断端口是被防火墙拦了还是服务没启动？

```bash
# 在目标机器上：
ss -tlnp | grep :端口号

# 如果有输出 → 服务已在监听，问题在网络/防火墙
# 如果没输出 → 服务没在监听这个端口

# 在目标机器本地测试：
curl -v http://127.0.0.1:端口号/ 2>&1 | head -5
# 如果本地可以 → 外部不通是防火墙/安全组问题
# 如果本地也不行 → 服务本身有问题
```

### Q6: 多网卡环境怎么排查？

```bash
# 查看所有网卡及路由
ip addr show
ip route show

# 查看到目标走哪张网卡
ip route get 目标IP

# 指定网卡 ping
ping -I eth0 -c 4 目标IP
ping -I eth1 -c 4 目标IP

# 查看策略路由
ip rule show
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及网络配置变更，AI 不会自动执行！**
> 
> 请用户根据诊断结果，自行判断是否需要执行以下操作。

### 1. 重启网卡/网络服务

```bash
# 重启单个网卡
ip link set eth0 down
ip link set eth0 up

# 重启网络服务（TencentOS 3/4）
systemctl restart NetworkManager

# 重新获取 DHCP 地址
dhclient -r eth0
dhclient eth0
```

### 2. 配置 DNS

```bash
# 临时修改 DNS
echo "nameserver 114.114.114.114" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf

# 通过 NetworkManager 永久修改（推荐）
nmcli con mod "连接名" ipv4.dns "114.114.114.114 8.8.8.8"
nmcli con up "连接名"
```

### 3. 防火墙放行端口

```bash
# firewalld 放行端口
firewall-cmd --add-port=80/tcp --permanent
firewall-cmd --add-port=443/tcp --permanent
firewall-cmd --reload

# iptables 放行端口
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT
```

### 4. 添加/修改路由

```bash
# 添加默认路由
ip route add default via 网关IP dev eth0

# 添加静态路由
ip route add 10.0.0.0/8 via 网关IP dev eth0

# 删除错误路由
ip route del 10.0.0.0/8
```

### 5. 配置静态 IP

```bash
# 使用 nmcli 配置
nmcli con mod "连接名" ipv4.method manual
nmcli con mod "连接名" ipv4.addresses "192.168.1.100/24"
nmcli con mod "连接名" ipv4.gateway "192.168.1.1"
nmcli con mod "连接名" ipv4.dns "114.114.114.114"
nmcli con up "连接名"
```

### 6. 优化 TCP 参数（高连接数场景）

```bash
# 临时调整
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_fin_timeout=30
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_tw_buckets=50000

# 永久生效
echo "net.ipv4.tcp_tw_reuse = 1" >> /etc/sysctl.conf
echo "net.ipv4.tcp_fin_timeout = 30" >> /etc/sysctl.conf
sysctl -p
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看 IP 地址 | `ip addr show` 或 `ip -brief addr` |
| 查看网卡状态 | `ip link show` |
| 测试 ping 连通性 | `ping -c 4 目标IP` |
| 测试 TCP 端口 | `nc -zv -w 3 IP 端口` 或 `curl -v IP:端口` |
| 查看 DNS 配置 | `cat /etc/resolv.conf` |
| 测试 DNS 解析 | `nslookup 域名` 或 `dig 域名 +short` |
| 查看路由表 | `ip route show` |
| 路由追踪 | `traceroute -n IP` 或 `mtr -r -n IP` |
| 查看到目标走哪条路由 | `ip route get 目标IP` |
| 查看防火墙规则 | `firewall-cmd --list-all` |
| 查看 iptables 规则 | `iptables -L -n -v` |
| 查看监听端口 | `ss -tlnp` |
| 查看所有连接 | `ss -tnp` |
| 查看连接状态统计 | `ss -s` |
| 查看端口占用进程 | `ss -tlnp \| grep :端口` 或 `lsof -i :端口` |
| 查看 TIME_WAIT 数 | `ss -tn state time-wait \| wc -l` |
| 查看 ARP 表 | `ip neigh show` |
| 网络抓包 | `tcpdump -i eth0 host IP -nn` |
| 查看网卡统计 | `ip -s link show eth0` |
| 查看网络内核参数 | `sysctl -a \| grep net.ipv4` |

---

## 快速排查流程图

```
上不了网？
├── 有 IP 吗？ → ip addr show
│   └── 没有 → 网卡/DHCP 问题
├── 网关通吗？ → ping 网关
│   └── 不通 → 网卡/网线/交换机问题
├── 外网通吗？ → ping 8.8.8.8
│   └── 不通 → 路由/网关出口问题
├── DNS 正常吗？ → ping www.baidu.com
│   └── 不通 → DNS 配置问题
└── 特定端口通吗？ → nc -zv IP 端口
    └── 不通 → 防火墙/服务未监听

延迟高/丢包？
├── 哪一跳开始的？ → mtr -r -n 目标IP
├── 全链路丢包？ → 本机网卡/出口问题
└── 某跳开始？ → 中间网络设备问题
```

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|-------------|-------------|-------------|
| 网络管理工具 | network-scripts | NetworkManager | NetworkManager |
| 防火墙 | iptables | firewalld(iptables后端) | firewalld(nftables后端) |
| 网络配置文件 | `/etc/sysconfig/network-scripts/` | NetworkManager + 兼容 ifcfg | NetworkManager(nmcli) |
| 默认网络命令 | ifconfig/route | ip | ip |
| 连接查看 | netstat | ss | ss |

> **注意**：
> - TencentOS 2 的 `ifconfig` 和 `route` 在 TencentOS 3/4 上建议使用 `ip` 命令替代
> - TencentOS 4 的 firewalld 使用 nftables 后端，但 `iptables` 命令仍可用（兼容层）
> - 所有版本的 `ss` 命令用法一致，推荐优先使用 `ss` 代替 `netstat`

## 相关技能

- **firewall-config**：防火墙详细配置与管理
- **dns-config**：DNS 配置与故障排查
- **network-bandwidth**：网络带宽与流量分析
- **tcp-tuning**：TCP 内核参数调优
