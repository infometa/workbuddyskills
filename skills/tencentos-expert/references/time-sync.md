---
name: time-sync
description: 检查和管理系统时间同步，包括 chronyd/ntpd 状态排查、NTP 源配置、 时间偏移诊断、时区管理、硬件时钟（RTC/hwclock）、makestep 配置、 闰秒处理、内网 NTP 服务器搭建、虚拟机/容器时间同步等。
description_zh: 系统时间同步与 NTP/Chronyd 管理
description_en: System time synchronization and NTP/Chronyd management
version: 1.0.0
---

# 时间同步与 NTP/Chronyd 管理

帮助检查和管理系统时间同步，包括 chronyd/ntpd 状态排查、NTP 源配置、时间偏移诊断、时区管理、硬件时钟、闰秒处理、内网 NTP 搭建等。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看时间状态、同步偏移、NTP 源、配置信息），**不自动执行时间修改、配置变更和服务重启操作**。
> 
> 修改系统时间（`date -s`/`timedatectl set-time`）、修改 NTP 配置、重启 chronyd/ntpd 等操作仅作为参考提供给用户，由用户自行判断和手动执行。
> 
> **修改系统时间可能导致**：数据库事务异常、日志时间戳混乱、证书验证失败、Kerberos 认证中断、cron 定时任务错乱、分布式系统数据不一致。

## 适用场景

### 用户可能的问题表述

**"系统时间不对"类**（最常见）：
- "系统时间不对"、"服务器时间差了好几分钟"、"时间偏了"
- "时间慢了"、"时间快了"、"跟标准时间差多少"
- "date 看到的时间不对"、"时间不准"、"时间漂移"
- "机器时间和实际时间不一样"、"时间差了几秒"
- "业务日志时间不对"、"数据库时间不对"

**"时间同步不了"类**（高频故障）：
- "时间同步不上"、"NTP 同步失败"、"时间同步报错"
- "chronyd 不工作"、"ntpd 同步不了"、"NTP 超时"
- "时间一直偏"、"同步了但时间还是不对"
- "No sources"、"Not synchronized"、"Leap status: not synchronised"
- "chronyc tracking 显示异常"、"ntpstat 报错"

**"查看时间同步状态"类**：
- "时间同步了没"、"NTP 状态怎么看"、"时间同步状态"
- "chronyc sources"、"chronyc tracking"、"ntpq -p"
- "同步偏移多少"、"同步精度"、"时间抖动"
- "timedatectl 怎么看"、"NTP synchronized 是什么意思"

**"怎么配 NTP"类**（配置需求）：
- "怎么配时间同步"、"NTP 服务器怎么设"、"chrony 配置"
- "时间同步到哪个服务器"、"NTP 源怎么改"
- "添加 NTP 服务器"、"server 行怎么写"
- "pool.ntp.org"、"ntp.tencent.com"、"时间源"
- "iburst 是什么意思"、"prefer 是什么意思"

**"时区问题"类**：
- "时区不对"、"怎么改时区"、"时区设成北京时间"
- "UTC 和 CST 差 8 小时"、"时区是 UTC 怎么改"
- "timedatectl 怎么用"、"Asia/Shanghai"
- "TZ 环境变量"、"/etc/localtime"
- "所有时区列表"、"查看当前时区"

**"NTP 和 Chronyd 区别"类**：
- "ntpd 和 chronyd 哪个好"、"用 ntpd 还是 chronyd"
- "怎么从 ntpd 切到 chronyd"、"ntpd 过时了吗"
- "TencentOS 2 和 TencentOS 3 时间同步区别"

**"硬件时钟"类**：
- "hwclock 怎么用"、"硬件时钟和系统时间不一致"
- "BIOS 时间不对"、"RTC 时间"
- "hwclock --systohc"、"系统时间写入硬件时钟"

**"闰秒/时间跳变"类**：
- "闰秒怎么处理"、"时间突然跳了"、"时间回退"
- "slew 和 step 区别"、"makestep"
- "时间跳变对业务的影响"、"leapsectz"

**"内网时间同步"类**：
- "内网怎么同步时间"、"搭建 NTP 服务器"
- "没有外网怎么同步时间"、"本地时间服务器"
- "当 NTP 服务器给其他机器同步"

**"业务影响排查"类**：
- "Kerberos 认证失败时间偏差"、"证书时间错误"
- "分布式系统时间不同步"、"数据库主从时间不一致"
- "日志时间戳混乱"、"cron 定时任务时间不对"

## 诊断步骤

以下命令可由 AI 自动执行，用于诊断时间同步问题。

### 步骤 1：系统时间概览

```bash
# 查看当前系统时间（最常用）
date
date -u    # UTC 时间
date +"%Y-%m-%d %H:%M:%S %Z %:z"    # 格式化输出含时区

# timedatectl 综合信息（推荐）
timedatectl status

# 查看 UNIX 时间戳
date +%s
```

**timedatectl 输出解读**：

| 字段 | 含义 | 正常值 |
|------|------|--------|
| `Local time` | 本地时间 | 与实际时间一致 |
| `Universal time` | UTC 时间 | Local - 时区偏移 |
| `RTC time` | 硬件时钟时间 | 与 UTC 接近 |
| `Time zone` | 时区 | 如 `Asia/Shanghai (CST, +0800)` |
| `NTP enabled` / `Network time on` | NTP 是否启用 | `yes` |
| `NTP synchronized` | 是否已同步 | `yes` |
| `RTC in local TZ` | RTC 是否用本地时区 | `no`（推荐） |

### 步骤 2：检查时间同步服务状态

```bash
# 检查 chronyd 状态（TencentOS 3/4 默认）
systemctl status chronyd

# 检查 ntpd 状态（TencentOS 2 默认）
systemctl status ntpd

# 检查哪个在运行
systemctl is-active chronyd 2>/dev/null && echo "chronyd 运行中" || echo "chronyd 未运行"
systemctl is-active ntpd 2>/dev/null && echo "ntpd 运行中" || echo "ntpd 未运行"

# 检查是否开机自启
systemctl is-enabled chronyd 2>/dev/null
systemctl is-enabled ntpd 2>/dev/null

# 检查服务是否安装
rpm -q chrony 2>/dev/null
rpm -q ntp 2>/dev/null
```

### 步骤 3：Chrony 详细诊断（推荐）

```bash
# 查看同步状态概览（最重要的命令）
chronyc tracking

# 查看 NTP 源列表和状态
chronyc sources -v

# 查看 NTP 源统计信息
chronyc sourcestats -v

# 查看 chrony 活动信息
chronyc activity

# 查看 chrony 选择的 NTP 源
chronyc -n sources | head -20

# 查看 NTP 客户端访问记录（如果当 NTP 服务器）
chronyc clients 2>/dev/null | head -20
```

**chronyc tracking 输出解读**：

| 字段 | 含义 | 关注点 |
|------|------|--------|
| `Reference ID` | 当前同步源 | 不应为 `00000000` |
| `Stratum` | 层级 | 1-3 表示直接/近距离同步，>10 异常 |
| `Ref time` | 上次同步时间 | 不应太久远 |
| `System time` | 系统时间偏移 | 越接近 0 越好 |
| `Last offset` | 上次同步偏移量 | 正常 <1ms |
| `RMS offset` | 偏移均方根 | 正常 <10ms |
| `Frequency` | 频率偏差（ppm） | 正常 <10 ppm |
| `Residual freq` | 残余频率偏差 | 越小越好 |
| `Skew` | 频率估计误差 | 越小越好 |
| `Root delay` | 根延迟 | 网络延迟相关 |
| `Root dispersion` | 根分散度 | 越小越好 |
| `Leap status` | 闰秒状态 | `Normal` 为正常 |

**chronyc sources 输出解读**：

| 标志位 | 含义 |
|--------|------|
| `^` | 服务器 |
| `=` | 对等节点 |
| `#` | 本地时钟 |
| `*` | 当前同步源（最佳） |
| `+` | 可选的良好源 |
| `-` | 被排除的源 |
| `?` | 连接已丢失 |
| `x` | 被标记为假的 |
| `~` | 变化太大 |

### 步骤 4：NTPd 详细诊断（传统方式）

```bash
# 查看 NTP peer 状态
ntpq -p

# 查看 NTP 同步状态
ntpstat 2>/dev/null

# 查看 NTP 关联详情
ntpq -c associations

# 查看 ntpd 系统变量
ntpq -c "rv 0"

# 查看 NTP 同步偏移
ntpq -c "rv 0 offset,sys_jitter,clk_jitter,frequency"
```

**ntpq -p 输出解读**：

| 标记 | 含义 |
|------|------|
| `*` | 当前同步源 |
| `+` | 候选源 |
| `-` | 被淘汰的源 |
| `x` | 被标记为假的源 |
| `.` | 被评估为太差 |
| 无标记 | 被拒绝/不可达 |

| 列 | 含义 |
|----|------|
| `remote` | NTP 服务器地址 |
| `refid` | 参考时钟 ID |
| `st` | 层级（stratum） |
| `when` | 上次查询时间（秒） |
| `poll` | 查询间隔（秒） |
| `reach` | 可达性（八进制，377=全部可达） |
| `delay` | 往返延迟（ms） |
| `offset` | 偏移量（ms） |
| `jitter` | 抖动（ms） |

### 步骤 5：时区检查

```bash
# 查看当前时区
timedatectl show --property=Timezone --value 2>/dev/null || \
    timedatectl | grep "Time zone"

# 查看 /etc/localtime 链接
ls -la /etc/localtime

# 查看 TZ 环境变量
echo "TZ=${TZ:-未设置}"

# 列出所有可用时区（搜索）
timedatectl list-timezones | grep -i "shanghai\|beijing\|asia"

# 查看 /etc/timezone（部分系统）
cat /etc/timezone 2>/dev/null
```

**常见时区对照**：

| 时区标识 | 说明 | UTC 偏移 |
|----------|------|----------|
| `Asia/Shanghai` | 中国标准时间（CST） | UTC+8 |
| `Asia/Hong_Kong` | 香港时间（HKT） | UTC+8 |
| `Asia/Tokyo` | 日本标准时间（JST） | UTC+9 |
| `Asia/Singapore` | 新加坡时间（SGT） | UTC+8 |
| `America/New_York` | 美国东部时间（EST/EDT） | UTC-5/-4 |
| `America/Los_Angeles` | 美国太平洋时间（PST/PDT） | UTC-8/-7 |
| `Europe/London` | 格林威治时间（GMT/BST） | UTC+0/+1 |
| `UTC` | 协调世界时 | UTC+0 |

### 步骤 6：NTP 配置检查

```bash
# 查看 chrony 配置文件
cat /etc/chrony.conf 2>/dev/null

# 查看 chrony 有效配置（去掉注释和空行）
grep -v '^#' /etc/chrony.conf 2>/dev/null | grep -v '^$'

# 查看 ntpd 配置文件
cat /etc/ntp.conf 2>/dev/null

# 查看 ntpd 有效配置
grep -v '^#' /etc/ntp.conf 2>/dev/null | grep -v '^$'

# 查看配置中的 NTP 服务器列表
grep -E "^(server|pool|peer)" /etc/chrony.conf 2>/dev/null
grep -E "^(server|pool|peer)" /etc/ntp.conf 2>/dev/null

# 查看 chrony 密钥文件（是否存在）
ls -la /etc/chrony.keys 2>/dev/null

# 查看 chrony drift 文件
cat /var/lib/chrony/drift 2>/dev/null
```

**chrony.conf 关键参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `server` | 指定 NTP 服务器 | `server ntp.tencent.com iburst` |
| `pool` | 指定 NTP 服务器池 | `pool pool.ntp.org iburst` |
| `peer` | 对等同步节点 | `peer 10.0.0.2` |
| `iburst` | 初次同步快速发送 4 个包 | 加快首次同步 |
| `prefer` | 首选服务器 | 优先使用此源 |
| `makestep` | 允许时间跳变 | `makestep 1.0 3`（前 3 次允许跳 >1s） |
| `rtcsync` | 定期同步到 RTC | 保持硬件时钟准确 |
| `driftfile` | 频率漂移文件 | 记录时钟频率偏差 |
| `allow` | 允许哪些客户端同步 | `allow 10.0.0.0/8` |
| `deny` | 拒绝哪些客户端 | `deny all` |
| `local` | 本地时钟作为源 | `local stratum 10`（当 NTP 服务器用） |
| `stratumweight` | 层级权重 | 影响源选择 |
| `logdir` | 日志目录 | `/var/log/chrony` |
| `maxdistance` | 最大允许距离 | 默认 3 秒 |
| `minsources` | 最少可用源数 | 默认 1 |
| `leapsectz` | 闰秒时区文件 | `leapsectz right/UTC` |

### 步骤 7：硬件时钟（RTC）检查

```bash
# 查看硬件时钟时间
hwclock --show 2>/dev/null || hwclock -r 2>/dev/null

# 对比系统时间和硬件时钟
echo "系统时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "硬件时钟: $(hwclock --utc --show 2>/dev/null)"

# 查看 RTC 是否用本地时区
timedatectl | grep "RTC in local TZ"

# 查看 /etc/adjtime
cat /etc/adjtime 2>/dev/null
```

**hwclock 说明**：
- 系统时间（system clock）：操作系统维护，掉电丢失
- 硬件时钟（RTC/CMOS clock）：主板电池维持，独立于 OS
- 系统启动时从 RTC 读取初始时间，运行中由 NTP 维护系统时间
- `rtcsync`（chrony）或 `11 minute mode`（ntpd）定期将系统时间写回 RTC

### 步骤 8：时间同步故障排查

```bash
# 检查网络连通性（能否访问 NTP 服务器）
# 获取配置的 NTP 服务器
ntp_servers=$(grep -E "^(server|pool)" /etc/chrony.conf 2>/dev/null | awk '{print $2}')
if [[ -z "$ntp_servers" ]]; then
    ntp_servers=$(grep -E "^(server|pool)" /etc/ntp.conf 2>/dev/null | awk '{print $2}')
fi
echo "配置的 NTP 服务器: $ntp_servers"

# 检查 UDP 123 端口是否可达
for srv in $ntp_servers; do
    echo -n "测试 $srv:123 ... "
    timeout 3 bash -c "echo > /dev/udp/$srv/123" 2>/dev/null && echo "可达" || echo "不可达"
done

# 检查防火墙是否放行 UDP 123
iptables -L -n 2>/dev/null | grep -i "123\|ntp"
firewall-cmd --list-all 2>/dev/null | grep -i "ntp\|123"

# 检查 chronyd 日志
journalctl -u chronyd -n 30 --no-pager 2>/dev/null
journalctl -u ntpd -n 30 --no-pager 2>/dev/null

# 检查系统日志中的时间同步相关错误
journalctl --no-pager -n 50 | grep -i -E "chrony|ntp|time|clock" | tail -20

# 手动测试 NTP 同步（只测试不改时间）
chronyd -Q "server ntp.tencent.com iburst" 2>&1 || true
```

**常见同步失败原因**：

| 症状 | 可能原因 | 排查方向 |
|------|----------|----------|
| `No sources` | NTP 服务器不可达 | 检查网络/防火墙/DNS |
| `Not synchronised` | 未完成同步 | 等待或检查 NTP 源 |
| `Stratum 0` / `16` | 源不可用 | NTP 服务器自身未同步 |
| `reach=0` (ntpq) | 完全不可达 | 网络/防火墙问题 |
| 偏移量很大 | 时间差异过大 | 需要 `makestep` 或手动校时 |
| `502 chronyd is not running` | 服务未启动 | `systemctl start chronyd` |
| `Connection refused` | 服务端口未监听 | 检查服务状态和配置 |

### 步骤 9：时间偏移精确测量

```bash
# 使用 chronyc 查看精确偏移
chronyc tracking | grep -E "System time|Last offset|RMS offset"

# 使用 ntpdate 测量偏移（不修改时间）
ntpdate -q ntp.tencent.com 2>/dev/null || \
    chronyd -Q "server ntp.tencent.com iburst" 2>&1

# 使用 sntp 查询（如果可用）
sntp ntp.tencent.com 2>/dev/null

# 查看时间偏移历史（chrony 日志）
cat /var/log/chrony/tracking.log 2>/dev/null | tail -20

# 多源偏移对比
for srv in ntp.tencent.com ntp1.aliyun.com time.windows.com; do
    echo -n "$srv: "
    chronyd -Q "server $srv iburst" 2>&1 | grep "offset" || echo "不可达"
done
```

### 步骤 10：NTP 安全与认证检查

```bash
# 查看 NTP 认证配置
grep -E "^(keyfile|authselectmode|key)" /etc/chrony.conf 2>/dev/null
grep -E "^(keys|trustedkey|requestkey|controlkey)" /etc/ntp.conf 2>/dev/null

# 查看 NTP 访问控制
grep -E "^(allow|deny|cmdallow|cmddeny)" /etc/chrony.conf 2>/dev/null
grep -E "^(restrict)" /etc/ntp.conf 2>/dev/null

# 查看 chronyd 监听端口
ss -ulnp | grep chronyd
ss -ulnp | grep ntpd

# 查看是否开放了 NTP 服务端口给外部
ss -ulnp | grep ":123 "
```

---

## 常见问题解答

### Q1: 系统时间不对，怎么快速诊断？

**快速排查三步走**：

```bash
# 第一步：看当前时间和同步状态
timedatectl status

# 第二步：看 NTP 源状态
chronyc sources -v 2>/dev/null || ntpq -p 2>/dev/null

# 第三步：看时间偏移量
chronyc tracking 2>/dev/null | grep -E "System time|Last offset"
```

**判断逻辑**：
- `NTP synchronized: no` → NTP 同步未开启或失败，查步骤 2/8
- 没有 `*` 标记的源 → 没有成功同步的 NTP 源，查步骤 3/8
- 偏移量很大（>1s） → 需要手动校时或调整 `makestep`
- 时区不对 → 查步骤 5

### Q2: chronyd 和 ntpd 有什么区别？该用哪个？

| 对比项 | chronyd | ntpd |
|--------|---------|------|
| **推荐度** | ⭐⭐⭐ 推荐 | ⭐ 传统 |
| **同步速度** | 快（数秒~数分钟） | 慢（可能需要数分钟~数小时） |
| **虚拟机支持** | 优秀（适应时钟抖动） | 一般 |
| **网络中断恢复** | 快速恢复 | 恢复慢 |
| **间歇性连接** | 支持良好 | 不支持 |
| **内存占用** | 更小 | 较大 |
| **初次同步** | 支持 `makestep`（快速跳变） | 需要 `ntpdate` 先校时 |
| **精度** | 微秒级 | 微秒级 |
| **默认随发行版** | TencentOS 3+ | TencentOS 2 |
| **配置文件** | `/etc/chrony.conf` | `/etc/ntp.conf` |
| **管理命令** | `chronyc` | `ntpq`/`ntpdc` |

> **结论**：在 TencentOS 3/4 上使用 `chronyd`，TencentOS 2 上使用 `ntpd`。新部署一律推荐 `chronyd`。

### Q3: 时间同步失败怎么排查？

**排查流程**：

```
时间同步失败？
├── 1. 服务是否运行？
│   ├── systemctl is-active chronyd → inactive → 启动服务
│   └── 运行中 → 继续排查
├── 2. NTP 源是否可达？
│   ├── chronyc sources → 无 * 或 + 标记
│   ├── 检查网络: ping NTP服务器
│   ├── 检查防火墙: UDP 123 是否放行
│   └── 检查 DNS: 能否解析 NTP 服务器名
├── 3. 时间偏差是否过大？
│   ├── 偏差 > makestep 阈值 → 手动校时
│   └── 偏差不大 → 等待自动同步
└── 4. 配置是否正确？
    ├── 检查 /etc/chrony.conf 中 server/pool 行
    └── 检查是否有拼写错误或不可用的 NTP 地址
```

### Q4: 怎么改时区？

```bash
# 查看当前时区
timedatectl | grep "Time zone"

# 列出可用时区
timedatectl list-timezones | grep Asia

# 设置时区为北京时间（参考命令，需手动执行）
# timedatectl set-timezone Asia/Shanghai

# 验证
date
```

> **注意**：改时区不会改变 UTC 时间，只改变本地时间的显示。已存储的时间戳（如日志中的 UTC 时间）不受影响。

### Q5: 时间偏移多少算正常？

| 偏移量 | 评估 | 说明 |
|--------|------|------|
| < 1 ms | 优秀 | 局域网或高质量 NTP 源 |
| 1-10 ms | 良好 | 公网 NTP 正常水平 |
| 10-100 ms | 可接受 | 远距离或负载较高的 NTP 源 |
| 100 ms - 1 s | 需关注 | 可能影响部分应用 |
| > 1 s | 异常 | 需要立即排查和修复 |
| > 128 ms | 注意 | 可能导致 Kerberos 认证失败（默认容差 5 分钟） |

**业务影响参考**：
- **数据库主从复制**：偏差 >1s 可能影响，>10s 可能中断
- **Kerberos 认证**：默认容差 5 分钟，超过则认证失败
- **TLS 证书验证**：偏差超过证书有效期范围会失败
- **分布式事务**：偏差 >100ms 可能导致事务排序异常
- **日志分析**：偏差 >1s 影响多服务器日志关联

### Q6: makestep 配置怎么理解？

`makestep` 是 chrony 最重要的配置之一，控制时间跳变行为：

```
makestep <阈值(秒)> <次数限制>
```

| 配置 | 含义 | 使用场景 |
|------|------|----------|
| `makestep 1.0 3` | 前 3 次更新，偏差 >1s 允许跳变 | **默认推荐** |
| `makestep 1.0 -1` | 任何时候偏差 >1s 都允许跳变 | 虚拟机/容器环境 |
| `makestep 0.1 3` | 前 3 次更新，偏差 >0.1s 允许跳变 | 要求更高精度 |
| 不设 makestep | 只用 slew（渐变），不跳变 | 对时间回退敏感的业务 |

**slew vs step**：
- **step（跳变）**：直接调整时间，快但可能导致时间回退
- **slew（渐变）**：通过调整时钟频率逐渐纠正，慢但不会时间回退
- chrony 默认 slew 速率为 ±100 ppm，每秒最多修正 100 微秒

### Q7: 怎么搭建内网 NTP 服务器？

**架构建议**：

```
外网 NTP 源 (如 ntp.tencent.com)
        │
   ┌────▼────┐
   │ NTP 主  │ (Stratum 2，连接外网)
   └────┬────┘
        │
   ┌────▼────┐
   │ NTP 备  │ (Stratum 2，连接外网)
   └────┬────┘
        │
    内网客户端 (Stratum 3)
```

**服务端 chrony.conf 参考配置**：

```ini
# 上游 NTP 源
server ntp.tencent.com iburst prefer
server ntp1.aliyun.com iburst
server time.windows.com iburst

# 允许内网客户端同步
allow 10.0.0.0/8
allow 172.16.0.0/12
allow 192.168.0.0/16

# 当所有上游不可用时，用本地时钟
local stratum 10

# 快速初始同步
makestep 1.0 3

# 同步到硬件时钟
rtcsync

# 日志
logdir /var/log/chrony
log measurements statistics tracking
```

### Q8: 闰秒怎么处理？

**闰秒简介**：国际标准时间（UTC）偶尔会在 6 月 30 日或 12 月 31 日的最后一秒插入/删除一秒。

**chrony 处理闰秒的方式**：

| 方式 | 配置 | 说明 |
|------|------|------|
| **slew（渐变，推荐）** | `leapsecmode slew` | 在闰秒前后通过调整时钟频率平滑过渡 |
| **step（跳变）** | `leapsecmode step` | 在闰秒时刻直接跳变 1 秒 |
| **系统默认** | `leapsecmode system` | 由内核处理（默认） |
| **时区数据** | `leapsectz right/UTC` | 使用 tzdata 中的闰秒表 |

**检查闰秒状态**：

```bash
# 查看当前闰秒状态
chronyc tracking | grep "Leap status"

# 查看内核闰秒标志
adjtimex --print 2>/dev/null | grep "status"

# 查看 tzdata 中的闰秒信息
cat /usr/share/zoneinfo/leap-seconds.list 2>/dev/null | tail -5
zdump -v /usr/share/zoneinfo/right/UTC 2>/dev/null | tail -5
```

### Q9: 虚拟机/容器时间同步注意事项？

**虚拟机**：
- 虚拟机时钟可能受宿主机影响而抖动
- `chronyd` 比 `ntpd` 更适合虚拟机环境（能更好地适应时钟跳变）
- 建议配置 `makestep 1.0 -1`（始终允许跳变）
- 如果使用 VMware Tools / open-vm-tools，注意其可能自带时间同步，可能与 NTP 冲突

```bash
# 检查是否有虚拟化相关的时间同步工具
systemctl status vmtoolsd 2>/dev/null
systemctl status qemu-guest-agent 2>/dev/null

# 检查 KVM 时钟源
cat /sys/devices/system/clocksource/clocksource0/current_clocksource 2>/dev/null
cat /sys/devices/system/clocksource/clocksource0/available_clocksource 2>/dev/null
```

**容器**：
- 容器与宿主机共享内核时钟，**容器内无法独立修改系统时间**
- 容器内只能修改时区（挂载 `/etc/localtime`）
- 时间同步应在宿主机上配置，容器自动继承
- 如果容器时间不对，检查宿主机时间

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及时间修改和配置变更，AI 不会自动执行！**

### 手动校时

```bash
# 使用 chronyc 强制同步（推荐，需要 chronyd 运行中）
chronyc makestep

# 使用 ntpdate 手动校时（需先停止 ntpd/chronyd）
# systemctl stop chronyd
# ntpdate ntp.tencent.com
# systemctl start chronyd

# 使用 date 命令直接设置时间（不推荐）
# date -s "2026-04-04 12:00:00"

# 使用 timedatectl 设置时间（需先关闭 NTP 同步）
# timedatectl set-ntp false
# timedatectl set-time "2026-04-04 12:00:00"
# timedatectl set-ntp true
```

### 修改时区

```bash
# 设置时区
# timedatectl set-timezone Asia/Shanghai

# 或者通过链接文件
# ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
```

### 安装和启用 chronyd

```bash
# 安装 chrony
# yum install -y chrony    # TencentOS 2
# dnf install -y chrony    # TencentOS 3/4

# 启用并启动
# systemctl enable --now chronyd

# 如果之前用 ntpd，需要先停掉
# systemctl stop ntpd
# systemctl disable ntpd
# systemctl enable --now chronyd
```

### 修改 NTP 服务器配置

```bash
# 编辑 chrony 配置
# vi /etc/chrony.conf

# 示例：修改 NTP 服务器为腾讯 NTP
# server ntp.tencent.com iburst
# server ntp1.tencent.com iburst
# server ntp2.tencent.com iburst

# 修改后重启服务
# systemctl restart chronyd
```

### 硬件时钟同步

```bash
# 将系统时间写入硬件时钟
# hwclock --systohc

# 将硬件时钟写入系统时间
# hwclock --hctosys

# 设置硬件时钟为 UTC（推荐）
# hwclock --systohc --utc
```

### 配置 NTP 服务端（允许其他机器同步）

```bash
# 在 /etc/chrony.conf 中添加：
# allow 10.0.0.0/8

# 重启 chrony
# systemctl restart chronyd

# 开放防火墙 UDP 123 端口
# firewall-cmd --permanent --add-service=ntp
# firewall-cmd --reload
```

---

## 命令速查表

### 基础命令

| 目的 | 命令 |
|------|------|
| 查看系统时间 | `date` |
| 查看详细时间信息 | `timedatectl` |
| 查看 NTP 同步状态 | `timedatectl show -p NTPSynchronized --value` |
| 查看硬件时钟 | `hwclock --show` |

### Chrony 命令

| 目的 | 命令 |
|------|------|
| 查看同步跟踪状态 | `chronyc tracking` |
| 查看 NTP 源 | `chronyc sources -v` |
| 查看 NTP 源统计 | `chronyc sourcestats -v` |
| 查看活动 | `chronyc activity` |
| 查看客户端 | `chronyc clients` |
| 查看服务器日志 | `journalctl -u chronyd -n 30` |
| 查看配置 | `cat /etc/chrony.conf` |

### NTPd 命令

| 目的 | 命令 |
|------|------|
| 查看 peer 状态 | `ntpq -p` |
| 查看同步状态 | `ntpstat` |
| 查看关联 | `ntpq -c associations` |
| 查看偏移量 | `ntpq -c "rv 0 offset"` |
| 查看服务日志 | `journalctl -u ntpd -n 30` |
| 查看配置 | `cat /etc/ntp.conf` |

### 时区命令

| 目的 | 命令 |
|------|------|
| 查看当前时区 | `timedatectl \| grep "Time zone"` |
| 列出时区 | `timedatectl list-timezones` |
| 查看 localtime 链接 | `ls -la /etc/localtime` |

---

## 快速排查流程图

### 系统时间不对？

```
系统时间不对？
├─ 1. timedatectl 查看状态
│  ├─ NTP synchronized: no
│  │  ├─ 服务是否运行？systemctl is-active chronyd
│  │  │  ├─ inactive → 启动 chronyd
│  │  │  └─ active → 查看 NTP 源
│  │  └─ chronyc sources → 有无 * 标记的源？
│  │     ├─ 无 → 检查网络/防火墙/NTP 配置
│  │     └─ 有 → 等待同步或 chronyc makestep
│  └─ NTP synchronized: yes
│     ├─ 偏移量检查 chronyc tracking
│     │  ├─ 偏移量正常 (<100ms) → 时区问题？
│     │  └─ 偏移量大 → 检查 NTP 源质量
│     └─ 时区检查 timedatectl | grep "Time zone"
│        ├─ 时区不对 → timedatectl set-timezone
│        └─ 时区正确 → 检查应用层时间处理
└─ 2. 硬件时钟检查
   └─ hwclock --show vs date
      ├─ 差异大 → hwclock --systohc
      └─ 差异小 → 正常
```

### NTP 同步失败？

```
NTP 同步失败？
├─ 1. 服务状态
│  ├─ systemctl is-active chronyd → inactive
│  │  └─ 检查日志 journalctl -u chronyd
│  └─ active → 继续
├─ 2. NTP 源检查
│  ├─ chronyc sources → 无源
│  │  └─ 检查 /etc/chrony.conf 是否配了 server/pool
│  ├─ 全部 ? 标记 → 网络不通
│  │  ├─ ping NTP 服务器
│  │  ├─ 检查 DNS 解析
│  │  └─ 检查防火墙 UDP 123
│  └─ 有 + 但无 * → 等待选举或偏差太大
├─ 3. 偏差过大
│  ├─ chronyc tracking → offset 很大
│  └─ makestep 或手动校时
└─ 4. 配置问题
   ├─ server/pool 地址是否可用
   ├─ 是否有语法错误
   └─ systemd-analyze verify
```

---

## 常用 NTP 服务器地址

### 腾讯云

| 地址 | 说明 |
|------|------|
| `ntp.tencent.com` | 腾讯云 NTP（推荐） |
| `ntp1.tencent.com` | 腾讯云 NTP 备选 1 |
| `ntp2.tencent.com` | 腾讯云 NTP 备选 2 |
| `ntp3.tencent.com` | 腾讯云 NTP 备选 3 |
| `ntp4.tencent.com` | 腾讯云 NTP 备选 4 |
| `ntp5.tencent.com` | 腾讯云 NTP 备选 5 |
| `ntpupdate.tencentyun.com` | 腾讯云内网 NTP |
| `time1.tencentyun.com` | 腾讯云内网 NTP 备选 |

### 其他常用

| 地址 | 说明 |
|------|------|
| `ntp.aliyun.com` | 阿里云 NTP |
| `pool.ntp.org` | NTP Pool Project |
| `cn.pool.ntp.org` | 中国 NTP Pool |
| `time.windows.com` | Microsoft NTP |
| `time.google.com` | Google NTP |
| `time.apple.com` | Apple NTP |
| `time.cloudflare.com` | Cloudflare NTP |

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|------|------|------|
| **默认 NTP** | ntpd | chronyd | chronyd |
| **NTP 包** | `ntp` | `chrony` | `chrony` |
| **配置文件** | `/etc/ntp.conf` | `/etc/chrony.conf` | `/etc/chrony.conf` |
| **管理命令** | `ntpq -p` | `chronyc sources` | `chronyc sources` |
| **timedatectl** | 支持 | 支持 | 支持 |
| **时区管理** | `timedatectl` | `timedatectl` | `timedatectl` |
| **默认 NTP 源** | 腾讯云 NTP | 腾讯云 NTP | 腾讯云 NTP |
| **闰秒处理** | 内核处理 | chrony slew | chrony slew |
| **PTP 支持** | 有限 | linuxptp | linuxptp |
| **chrony 版本** | - | 3.x/4.x | 4.x |
| **hwclock** | `hwclock` | `hwclock` | `hwclock` |
| **systemd-timesyncd** | 无 | 可选（通常不用） | 可选 |

### TencentOS 2 注意事项
- 默认安装 `ntp` 包，使用 `ntpd` 服务
- 建议升级到 `chrony`：`yum install chrony && systemctl disable ntpd && systemctl enable --now chronyd`
- `ntpdate` 命令可用于手动校时

### TencentOS 3/4 注意事项
- 默认安装 `chrony`，使用 `chronyd` 服务
- `ntpdate` 可能未安装，可用 `chronyd -q` 替代
- 支持 NTS（Network Time Security，chrony 4.0+）

---

## 相关技能

- [service-status](../service-status/) — 服务状态管理（chronyd/ntpd 服务排查）
- [network-check](../network-check/) — 网络连通性排查（NTP 端口连通性）
- [system-log](../system-log/) — 系统日志排查（NTP 相关日志）
