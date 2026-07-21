---
name: system-log
description: 分析系统日志，快速定位问题，包括 journalctl/dmesg/syslog 查看、错误日志过滤、按时间查询日志、OOM/kill 日志分析、内核硬件错误、 日志轮转与清理、审计与安全日志、日志配置管理等。
description_zh: 系统日志分析与问题定位
description_en: System log analysis and troubleshooting
version: 1.0.0
---

# 系统日志排查

帮助分析系统日志，快速定位问题，包括 journalctl/dmesg/syslog 查看、错误日志过滤、按时间查询日志、OOM/kill 日志分析、内核硬件错误、日志轮转与清理、审计与安全日志、日志配置管理等。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看日志、过滤日志、分析日志），**不自动执行以下高危操作**：
> 
> - 不自动删除或清空日志文件
> - 不自动修改 rsyslog/journald/logrotate 配置
> - 不自动重启 rsyslog/journald 服务
> - 不自动修改审计规则
> - 不自动清空 journal 日志
>
> 以上操作仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**"查看系统日志"类**（最基础）：
- "怎么看系统日志"、"日志在哪里"、"syslog 在哪"
- "/var/log/messages 在哪"、"journalctl 怎么用"
- "系统日志怎么查"、"哪里有日志"
- "帮我看看日志"、"查一下系统日志"
- "日志文件列表"、"/var/log 下有什么"

**"系统报错了"类**（最常见）：
- "系统报什么错"、"有没有错误日志"、"最近有报错吗"
- "看看有没有 error"、"系统有没有异常"
- "为什么系统不正常"、"查一下有没有报错"
- "日志里有没有 warning"、"critical 错误"
- "系统异常排查"、"看下有什么错"

**"日志占空间太大"类**（高频）：
- "/var/log 占了好几个 G"、"日志文件太大了"
- "journal 占了多少空间"、"日志怎么清理"
- "logrotate 没生效"、"日志没有轮转"
- "syslog 文件越来越大"、"日志不滚动了"
- "messages 文件好几个 G"、"日志把磁盘撑满了"
- "怎么限制日志大小"、"journal 太大了"

**"内核日志/dmesg"类**：
- "dmesg 有什么报错"、"内核日志怎么看"
- "硬件错误日志"、"MCE 错误"、"内存 ECC 错误"
- "磁盘 IO 错误"、"ext4 错误"、"XFS 错误"
- "网卡报错"、"EDAC 错误"、"硬件故障"
- "dmesg 里有 error"、"内核 warning"

**"按时间查日志"类**：
- "看今天的日志"、"昨天什么时间出的问题"
- "某个时间段的日志"、"日志时间过滤"
- "几点到几点的日志"、"从什么时候开始出的问题"
- "上次重启之后的日志"、"本次启动的日志"
- "最近一小时的日志"、"最近 10 分钟的错误"

**"OOM / kill 日志"类**：
- "进程被 kill 了看日志"、"OOM 日志"
- "什么时候被 OOM 杀的"、"谁触发的 OOM"
- "oom-killer 日志"、"内存不足杀进程"
- "进程突然消失了"、"进程被系统杀了"
- "cgroup OOM"、"memory cgroup 限制"

**"审计与安全日志"类**：
- "谁登录了系统"、"登录日志"、"ssh 登录记录"
- "有没有被入侵"、"安全日志"、"audit 日志"
- "登录失败记录"、"暴力破解"、"failed password"
- "lastlog"、"wtmp"、"btmp"
- "su/sudo 记录"、"谁 sudo 了"、"提权记录"

**"日志配置"类**：
- "rsyslog 怎么配置"、"日志发到远程"
- "journald 配置"、"journal 持久化"
- "日志级别怎么调"、"logrotate 怎么配"
- "日志保留多少天"、"日志轮转策略"
- "syslog 转发"、"集中化日志"

**"启动日志"类**：
- "系统启动日志"、"上次启动有报错吗"
- "boot 日志"、"开机日志"
- "启动慢看日志"、"启动报错"
- "上一次为什么重启"、"异常重启日志"

**"应用/服务日志"类**：
- "nginx 日志在哪"、"mysql 日志"、"应用日志在哪"
- "应用日志怎么看"、"日志实时跟踪"
- "docker 容器日志"、"pod 日志"
- "cron 日志"、"定时任务日志"

## 诊断步骤

以下命令可由 AI 自动执行，用于查看和分析系统日志。

### 步骤 1：日志系统概览

```bash
# 查看日志相关服务状态
systemctl is-active rsyslog 2>/dev/null; systemctl is-active systemd-journald

# 查看 /var/log 目录结构和大小
du -sh /var/log/ 2>/dev/null
ls -lhS /var/log/ 2>/dev/null | head -20

# 查看 journal 占用空间
journalctl --disk-usage 2>/dev/null

# 查看日志系统配置概要
echo "--- rsyslog ---"
rpm -q rsyslog 2>/dev/null || dpkg -l rsyslog 2>/dev/null | grep "^ii"
echo "--- journald ---"
grep -v "^#" /etc/systemd/journald.conf 2>/dev/null | grep -v "^$"

# 查看有多少次启动记录
journalctl --list-boots --no-pager 2>/dev/null | wc -l
```

**关键信息**：
- `rsyslog` 负责传统 syslog 日志（`/var/log/messages`、`/var/log/secure` 等）
- `systemd-journald` 负责 journal 二进制日志（通过 `journalctl` 查看）
- 两者通常并行运行，journal 会转发给 rsyslog

### 步骤 2：查看系统日志（journalctl — 最常用）

```bash
# 查看最近的系统日志（最常用）
journalctl -n 50 --no-pager

# 查看本次启动的日志
journalctl -b --no-pager | tail -100

# 查看上一次启动的日志（排查重启原因）
journalctl -b -1 --no-pager | tail -100

# 只看错误级别及以上日志（最快发现问题）
journalctl -p err --no-pager -n 50

# 只看警告级别及以上
journalctl -p warning --no-pager -n 50

# 查看紧急/致命错误
journalctl -p emerg..crit --no-pager -n 30

# 查看今天的错误日志
journalctl --since today -p err --no-pager

# 查看最近 1 小时的日志
journalctl --since "1 hour ago" --no-pager | tail -50

# 查看指定时间段的日志
journalctl --since "2024-01-15 10:00:00" --until "2024-01-15 12:00:00" --no-pager | tail -100

# 按 JSON 格式输出（方便程序解析）
journalctl -p err -n 10 -o json-pretty --no-pager
```

**日志级别说明**：
| 级别 | 数值 | 含义 | 示例 |
|------|------|------|------|
| emerg | 0 | 系统不可用 | 内核 panic |
| alert | 1 | 必须立即处理 | 核心系统故障 |
| crit | 2 | 严重错误 | 硬件故障、磁盘损坏 |
| err | 3 | 一般错误 | 服务启动失败、IO 错误 |
| warning | 4 | 警告 | 磁盘空间低、配置异常 |
| notice | 5 | 正常但值得注意 | 服务启停、用户登录 |
| info | 6 | 信息 | 常规运行信息 |
| debug | 7 | 调试 | 详细调试信息 |

### 步骤 3：查看传统 syslog 日志文件

```bash
# 查看系统主日志（最近 50 行）
tail -50 /var/log/messages 2>/dev/null || tail -50 /var/log/syslog 2>/dev/null

# 查看安全/认证日志
tail -50 /var/log/secure 2>/dev/null || tail -50 /var/log/auth.log 2>/dev/null

# 查看内核日志
tail -50 /var/log/kern.log 2>/dev/null

# 查看 cron 日志
tail -30 /var/log/cron 2>/dev/null

# 查看 mail 日志
tail -30 /var/log/maillog 2>/dev/null || tail -30 /var/log/mail.log 2>/dev/null

# 查看启动日志
cat /var/log/boot.log 2>/dev/null | tail -30

# 过滤关键字
grep -i "error\|fail\|critical\|panic" /var/log/messages 2>/dev/null | tail -30
grep -i "error\|fail\|critical\|panic" /var/log/syslog 2>/dev/null | tail -30

# 按时间查找（某个时间段内的日志）
awk '/Jan 15 10:00/,/Jan 15 12:00/' /var/log/messages 2>/dev/null | tail -50
```

**常用日志文件说明**：
| 文件 | 内容 | 对应 journalctl |
|------|------|-----------------|
| `/var/log/messages` | 系统主日志（TencentOS） | `journalctl` |
| `/var/log/syslog` | 系统主日志（Ubuntu/Debian） | `journalctl` |
| `/var/log/secure` | 认证/安全日志（TencentOS） | `journalctl -u sshd` |
| `/var/log/auth.log` | 认证/安全日志（Ubuntu/Debian） | `journalctl -u sshd` |
| `/var/log/kern.log` | 内核日志 | `journalctl -k` |
| `/var/log/cron` | 定时任务日志 | `journalctl -u crond` |
| `/var/log/boot.log` | 启动日志 | `journalctl -b` |
| `/var/log/dmesg` | 内核启动时环形缓冲区 | `dmesg` |
| `/var/log/wtmp` | 登录记录（二进制） | `last` |
| `/var/log/btmp` | 登录失败记录（二进制） | `lastb` |
| `/var/log/lastlog` | 最后登录记录（二进制） | `lastlog` |
| `/var/log/audit/audit.log` | 审计日志 | `ausearch` |

### 步骤 4：查看内核日志（dmesg）

```bash
# 查看最近的内核日志
dmesg --time-format=iso 2>/dev/null | tail -50
# 或者
dmesg -T 2>/dev/null | tail -50

# 只看错误和警告
dmesg --level=err,warn 2>/dev/null | tail -30
# 或者
dmesg -T 2>/dev/null | grep -i -E "error|warn|fail|bug|panic" | tail -30

# 查看硬件相关错误
dmesg -T 2>/dev/null | grep -i -E "mce|edac|ecc|hardware error|machine check" | tail -20

# 查看磁盘/文件系统错误
dmesg -T 2>/dev/null | grep -i -E "ext4|xfs|I/O error|block|scsi|ata|sd[a-z]" | tail -20

# 查看网卡相关信息
dmesg -T 2>/dev/null | grep -i -E "eth|nic|link up|link down|carrier|net" | tail -20

# 查看内存相关信息
dmesg -T 2>/dev/null | grep -i -E "oom|memory|swap|page allocation failure" | tail -20

# 查看 USB/PCI 设备信息
dmesg -T 2>/dev/null | grep -i -E "usb|pci" | tail -20

# 使用 journalctl 查看内核日志（更可靠，支持持久化）
journalctl -k --no-pager | tail -50
journalctl -k -p err --no-pager | tail -30
```

**常见内核错误关键词**：
| 关键词 | 含义 | 严重程度 |
|--------|------|----------|
| `MCE` / `Machine Check Exception` | CPU/内存硬件错误 | 🔴 严重 |
| `EDAC` / `ECC` | 内存纠错/不可纠正错误 | 🔴 严重 |
| `I/O error` | 磁盘 IO 错误 | 🔴 严重 |
| `ext4/xfs error` | 文件系统错误 | 🔴 严重 |
| `BUG:` / `kernel BUG` | 内核 bug | 🔴 严重 |
| `Oops:` | 内核异常 | 🔴 严重 |
| `page allocation failure` | 内存分配失败 | 🟡 警告 |
| `soft lockup` / `hard lockup` | 内核死锁 | 🔴 严重 |
| `hung_task` | 任务挂起 | 🟡 警告 |
| `NMI watchdog` | 不可屏蔽中断看门狗 | 🔴 严重 |
| `Out of memory` / `oom-killer` | OOM 杀进程 | 🟡 警告 |
| `link down` / `carrier lost` | 网卡链路断开 | 🟡 警告 |

### 步骤 5：OOM（内存不足）日志分析

```bash
# 检查是否有 OOM 事件
journalctl -k --no-pager | grep -i "oom\|out of memory\|killed process" | tail -20

# 或者使用 dmesg
dmesg -T 2>/dev/null | grep -i "oom\|out of memory\|killed process" | tail -20

# 查看 /var/log/messages 中的 OOM
grep -i "oom\|out of memory\|killed process" /var/log/messages 2>/dev/null | tail -20

# 查看被 OOM 杀掉的进程详情
journalctl -k --no-pager | grep -A 5 "oom-killer" | tail -40

# 查看 OOM 评分（哪个进程最容易被杀）
for pid in $(ps -eo pid --no-headers); do
    if [[ -f /proc/$pid/oom_score ]]; then
        score=$(cat /proc/$pid/oom_score 2>/dev/null)
        if [[ -n "$score" && "$score" -gt 100 ]]; then
            name=$(cat /proc/$pid/comm 2>/dev/null)
            echo "PID=$pid  OOM_SCORE=$score  PROCESS=$name"
        fi
    fi
done 2>/dev/null | sort -t= -k4 -rn | head -15

# 查看当前内存使用情况
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree|Committed_AS"

# 查看 cgroup 内存限制（容器/cgroup 内 OOM）
find /sys/fs/cgroup -name "memory.max" -exec sh -c 'echo "$1: $(cat "$1")"' _ {} \; 2>/dev/null | head -10
```

**OOM 日志解读**：
- `Out of memory: Killed process PID (进程名), UID=xxx, total-vm:xxx, anon-rss:xxx`
  - `total-vm`: 进程虚拟内存总量
  - `anon-rss`: 进程实际使用的物理内存
  - `oom_score_adj`: OOM 调整分数（-1000 到 1000，越高越容易被杀）
- `oom-killer: constraint=CONSTRAINT_MEMCG` → cgroup 内存限制触发的 OOM
- `oom-killer: constraint=CONSTRAINT_NONE` → 系统级全局 OOM

### 步骤 6：查看登录与安全日志

```bash
# 查看最近的登录记录
last -n 20

# 查看最近的登录失败记录
lastb -n 20 2>/dev/null

# 查看每个用户最后一次登录
lastlog 2>/dev/null | grep -v "Never"

# 查看 SSH 登录成功记录
journalctl -u sshd --no-pager | grep "Accepted" | tail -20
# 或者
grep "Accepted" /var/log/secure 2>/dev/null | tail -20
grep "Accepted" /var/log/auth.log 2>/dev/null | tail -20

# 查看 SSH 登录失败记录（暴力破解检测）
journalctl -u sshd --no-pager | grep "Failed password" | tail -20
grep "Failed password" /var/log/secure 2>/dev/null | tail -20

# 统计 SSH 登录失败的 IP（排查暴力破解）
journalctl -u sshd --no-pager | grep "Failed password" | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10

# 查看 su/sudo 记录
grep "su:" /var/log/secure 2>/dev/null | tail -15
grep "sudo:" /var/log/secure 2>/dev/null | tail -15
journalctl -t sudo --no-pager | tail -15

# 查看系统重启记录
last -x reboot | head -10
last -x shutdown | head -10

# 查看审计日志概要
ausearch -ts recent 2>/dev/null | tail -30
aureport --summary 2>/dev/null
aureport --login 2>/dev/null | tail -10
```

**安全日志关键事件**：
| 事件 | 日志关键词 | 位置 |
|------|-----------|------|
| SSH 登录成功 | `Accepted password/publickey` | `/var/log/secure` |
| SSH 登录失败 | `Failed password` | `/var/log/secure` |
| SSH 暴力破解 | 大量 `Failed password` 来自同一 IP | `/var/log/secure` |
| su 切换用户 | `su:` | `/var/log/secure` |
| sudo 提权 | `sudo:` | `/var/log/secure` |
| 用户添加/删除 | `useradd`/`userdel` | `/var/log/secure` |
| 密码修改 | `passwd` | `/var/log/secure` |

### 步骤 7：查看启动日志

```bash
# 查看本次启动日志
journalctl -b 0 --no-pager | head -100

# 查看上一次启动的日志（排查上次重启原因）
journalctl -b -1 --no-pager | tail -100

# 查看上次关机/重启前的最后日志
journalctl -b -1 --no-pager | tail -30

# 查看所有启动记录
journalctl --list-boots --no-pager

# 查看启动过程中的错误
journalctl -b -p err --no-pager

# 查看 boot.log
cat /var/log/boot.log 2>/dev/null | tail -30

# 查看启动耗时分析
systemd-analyze time 2>/dev/null
systemd-analyze blame --no-pager | head -15

# 查看系统运行时间
uptime
who -b
```

**判断异常重启**：
- `journalctl --list-boots` 中时间跳跃 → 中间可能有异常重启
- `journalctl -b -1 | tail` 最后一条日志 → 看关机前发生了什么
- `last -x reboot` → 确认重启时间
- 内核 panic → 看上次 boot 末尾是否有 panic/oops 关键字

### 步骤 8：日志空间占用分析

```bash
# 查看 /var/log 目录总大小
du -sh /var/log/

# 查看 /var/log 下各文件/目录大小（按大小排序）
du -sh /var/log/* 2>/dev/null | sort -rh | head -20

# 查看最大的日志文件
find /var/log -type f -size +10M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -15

# 查看 journal 占用空间
journalctl --disk-usage

# 查看 journal 配置的空间限制
grep -v "^#" /etc/systemd/journald.conf 2>/dev/null | grep -v "^$"

# 查看 logrotate 配置
cat /etc/logrotate.conf 2>/dev/null
ls -la /etc/logrotate.d/

# 查看 logrotate 状态文件（最后轮转时间）
cat /var/lib/logrotate/logrotate.status 2>/dev/null | tail -20
cat /var/lib/logrotate.status 2>/dev/null | tail -20

# 查看有没有未被轮转的超大日志
find /var/log -name "*.log" -size +100M -exec ls -lh {} \; 2>/dev/null
find /var/log -name "*.log" -mtime +30 -exec ls -lh {} \; 2>/dev/null | head -10

# 检查 logrotate 是否有错误
logrotate -d /etc/logrotate.conf 2>&1 | grep -i "error\|warning\|skipping" | head -10
```

**日志空间占用常见原因**：
1. **journal 未设置大小限制** → 默认占用 10% 文件系统或 4G
2. **logrotate 没有正常运行** → cron 服务问题或配置错误
3. **应用日志无轮转** → 自定义应用未配置 logrotate
4. **审计日志过大** → audit 规则过多或过于详细
5. **debug 级别日志** → 某服务开了 debug 级别导致日志暴增

### 步骤 9：查看日志配置

```bash
# 查看 rsyslog 主配置
cat /etc/rsyslog.conf 2>/dev/null | grep -v "^#" | grep -v "^$"

# 查看 rsyslog 扩展配置
ls -la /etc/rsyslog.d/ 2>/dev/null
for f in /etc/rsyslog.d/*.conf; do
    echo "=== $f ==="
    grep -v "^#" "$f" 2>/dev/null | grep -v "^$"
done

# 查看 journald 配置
cat /etc/systemd/journald.conf | grep -v "^#" | grep -v "^$"

# 查看 journal 是否持久化
ls -la /var/log/journal/ 2>/dev/null
# 如果目录存在 → 持久化模式
# 如果只有 /run/log/journal → 易失模式（重启丢失）

# 查看 logrotate 主配置
cat /etc/logrotate.conf | grep -v "^#" | grep -v "^$"

# 查看应用的 logrotate 配置
ls /etc/logrotate.d/

# 查看指定应用的 logrotate 配置
cat /etc/logrotate.d/syslog 2>/dev/null
cat /etc/logrotate.d/nginx 2>/dev/null

# 查看 audit 配置
cat /etc/audit/auditd.conf 2>/dev/null | grep -v "^#" | grep -v "^$"
```

**journald.conf 关键参数**：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `Storage` | auto | 存储模式：volatile(内存)、persistent(磁盘)、auto、none |
| `SystemMaxUse` | 10%/4G | journal 最大占用空间 |
| `SystemKeepFree` | 15% | 保留的空闲空间 |
| `SystemMaxFileSize` | 1/8 of SystemMaxUse | 单个 journal 文件最大大小 |
| `MaxRetentionSec` | 0 (不限制) | 日志最长保留时间 |
| `MaxFileSec` | 1month | 单个文件最长时间跨度 |
| `ForwardToSyslog` | yes | 是否转发给 rsyslog |
| `RateLimitIntervalSec` | 30s | 速率限制时间窗口 |
| `RateLimitBurst` | 10000 | 速率限制阈值 |

### 步骤 10：实时跟踪与高级过滤

```bash
# 实时跟踪系统日志
journalctl -f

# 实时跟踪错误级别日志
journalctl -f -p err

# 实时跟踪指定服务的日志
journalctl -u 服务名 -f

# 实时跟踪内核日志
journalctl -kf

# 多关键字过滤
journalctl --no-pager | grep -i -E "error|fail|critical|panic|oom" | tail -30

# 排除某些噪音日志
journalctl -p err --no-pager | grep -v "audit\|pam_unix\|systemd-logind" | tail -30

# 按进程 PID 查看
journalctl _PID=1234 --no-pager

# 按用户 UID 查看
journalctl _UID=1000 --no-pager | tail -30

# 按可执行文件路径查看
journalctl /usr/sbin/sshd --no-pager | tail -30

# 查看指定 syslog facility
journalctl SYSLOG_FACILITY=4 --no-pager | tail -30  # auth

# 输出到文件（方便离线分析）
journalctl -b -p err --no-pager -o short-iso > /tmp/errors.log 2>/dev/null
```

### 步骤 11：应用与容器日志

```bash
# 常见应用日志位置
ls -la /var/log/nginx/ 2>/dev/null
ls -la /var/log/mysql/ 2>/dev/null || ls -la /var/log/mysqld.log 2>/dev/null
ls -la /var/log/httpd/ 2>/dev/null || ls -la /var/log/apache2/ 2>/dev/null
ls -la /var/log/redis/ 2>/dev/null

# 查看 nginx 错误日志
tail -30 /var/log/nginx/error.log 2>/dev/null

# 查看 mysql 日志
tail -30 /var/log/mysql/error.log 2>/dev/null || tail -30 /var/log/mysqld.log 2>/dev/null

# Docker 容器日志
docker logs --tail 50 容器名 2>/dev/null

# Docker 所有容器的日志大小
find /var/lib/docker/containers -name "*-json.log" -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -10

# 查看 cron 定时任务日志
journalctl -u crond --no-pager | tail -20
grep CRON /var/log/cron 2>/dev/null | tail -20
grep CRON /var/log/syslog 2>/dev/null | tail -20
```

---

## 常见问题解答

### Q1: 系统有没有报错？怎么快速查看？

```bash
# 最快的方式：查看所有 error 级别及以上的日志
journalctl -p err --no-pager -n 50

# 查看本次启动以来的错误
journalctl -b -p err --no-pager

# 查看内核错误
dmesg --level=err,warn 2>/dev/null | tail -20

# 综合检查
echo "=== 系统错误 ==="
journalctl -b -p err --no-pager -n 10
echo ""
echo "=== 内核错误 ==="
dmesg -T 2>/dev/null | grep -i -E "error|fail|bug|panic" | tail -10
echo ""
echo "=== 失败的服务 ==="
systemctl list-units --state=failed --no-pager
```

**排查思路**：
1. 先看 `journalctl -p err` — 有没有错误
2. 看 `dmesg` — 有没有硬件/内核错误
3. 看 `systemctl --failed` — 有没有失败的服务
4. 根据错误信息进一步深入

### Q2: 进程被 OOM Killer 杀了怎么查？

```bash
# 1. 确认是不是 OOM
journalctl -k --no-pager | grep -i "oom\|killed process" | tail -10
dmesg -T 2>/dev/null | grep -i "oom\|killed process" | tail -10

# 2. 查看被杀的是哪个进程
journalctl -k --no-pager | grep "Killed process" | tail -5

# 3. 查看 OOM 时的内存状态
journalctl -k --no-pager | grep -B 20 "Killed process" | grep -E "Mem-Info|Active|Inactive|Free|total" | tail -10

# 4. 查看当前内存状态
free -h
cat /proc/meminfo | head -10

# 5. 查看各进程内存占用
ps aux --sort=-%mem | head -15
```

**被 OOM 杀的进程恢复**：
- 如果是服务 → 配置了 `Restart=on-failure` 会自动恢复
- 增加物理内存或 swap
- 调整 `oom_score_adj` 保护关键进程
- 设置 cgroup 内存限制，让非关键进程先被杀

### Q3: 怎么看某个时间段的日志？

```bash
# 方法 1: journalctl --since / --until（最推荐）
journalctl --since "2024-01-15 10:00:00" --until "2024-01-15 12:00:00" --no-pager | tail -50

# 常用时间格式：
journalctl --since today --no-pager | tail -50
journalctl --since yesterday --until today --no-pager | tail -50
journalctl --since "1 hour ago" --no-pager | tail -50
journalctl --since "30 min ago" --no-pager | tail -50
journalctl --since "2024-01-15" --no-pager | tail -50

# 方法 2: 传统日志文件用 awk 按时间过滤
awk '/Jan 15 10:00/,/Jan 15 12:00/' /var/log/messages | tail -50

# 方法 3: 用 grep 模糊匹配时间
grep "Jan 15 1[0-1]:" /var/log/messages | tail -50
```

### Q4: 日志太大了怎么清理？

```bash
# 1. 先看哪些日志占空间大
du -sh /var/log/* 2>/dev/null | sort -rh | head -15
journalctl --disk-usage

# 2. 查看 logrotate 是否正常工作
cat /var/lib/logrotate/logrotate.status 2>/dev/null | head -10
systemctl status logrotate.timer 2>/dev/null

# 3. 检查 logrotate 配置
logrotate -d /etc/logrotate.conf 2>&1 | grep -i "error\|warning" | head -10
```

> **清理操作**（需用户手动执行）：
> ```bash
> # 清理 journal 日志（保留最近 7 天）
> journalctl --vacuum-time=7d
> 
> # 清理 journal 日志（限制最大 500MB）
> journalctl --vacuum-size=500M
> 
> # 手动触发 logrotate
> logrotate -f /etc/logrotate.conf
> 
> # 清空指定日志文件（不删除文件，保持 fd）
> > /var/log/messages  # 或 cat /dev/null > /var/log/messages
> 
> # 删除旧的轮转日志
> find /var/log -name "*.gz" -mtime +30 -delete
> find /var/log -name "*.old" -mtime +30 -delete
> ```

### Q5: journal 日志重启后就没了？

```bash
# 检查 journal 存储模式
grep "Storage" /etc/systemd/journald.conf

# 检查是否有持久化目录
ls -la /var/log/journal/ 2>/dev/null

# 检查 /var/log/journal 目录权限
stat /var/log/journal/ 2>/dev/null
```

**如果 journal 不持久化**，原因可能是：
1. `Storage=volatile` → 只存在内存中
2. `Storage=auto`（默认）但 `/var/log/journal/` 目录不存在
3. 目录权限不对

> **开启持久化**（需用户手动执行）：
> ```bash
> # 创建持久化目录
> mkdir -p /var/log/journal
> systemd-tmpfiles --create --prefix /var/log/journal
> 
> # 或修改配置为 persistent
> # 编辑 /etc/systemd/journald.conf：
> # [Journal]
> # Storage=persistent
> 
> # 重启 journald
> systemctl restart systemd-journald
> ```

### Q6: logrotate 没有生效怎么排查？

```bash
# 1. 检查 logrotate timer/cron 是否在运行
systemctl status logrotate.timer 2>/dev/null
systemctl list-timers logrotate* --no-pager 2>/dev/null
cat /etc/cron.daily/logrotate 2>/dev/null

# 2. 检查 logrotate 状态文件
cat /var/lib/logrotate/logrotate.status 2>/dev/null | head -20
cat /var/lib/logrotate.status 2>/dev/null | head -20

# 3. 手动调试运行（只显示不执行）
logrotate -d /etc/logrotate.d/syslog 2>&1

# 4. 检查配置语法
logrotate -d /etc/logrotate.conf 2>&1 | grep -i "error\|warning\|skipping"

# 5. 查看 logrotate 执行日志
journalctl -u logrotate --no-pager | tail -10
grep logrotate /var/log/cron 2>/dev/null | tail -10
```

**logrotate 不生效常见原因**：
1. **cron/timer 没运行** → `systemctl start logrotate.timer` 或检查 crond
2. **配置语法错误** → `logrotate -d` 调试
3. **日志文件路径不匹配** → 检查通配符和实际文件路径
4. **selinux 拦截** → 检查 `ausearch -m avc | grep logrotate`
5. **文件被其他进程持有** → 需要 `copytruncate` 或 postrotate 重启服务

### Q7: 怎么查看有没有被暴力破解 SSH？

```bash
# 1. 检查失败登录次数
journalctl -u sshd --no-pager | grep "Failed password" | wc -l

# 2. 统计失败登录的来源 IP
journalctl -u sshd --no-pager | grep "Failed password" | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -20

# 3. 统计失败登录的目标用户
journalctl -u sshd --no-pager | grep "Failed password" | awk '{for(i=1;i<=NF;i++) if($i=="for") {if($(i+1)=="invalid") print $(i+3); else print $(i+1)}}' | sort | uniq -c | sort -rn | head -20

# 4. 查看最近的失败登录
lastb 2>/dev/null | head -20

# 5. 检查是否有 fail2ban 在运行
systemctl status fail2ban 2>/dev/null
fail2ban-client status 2>/dev/null
```

**暴力破解判断标准**：
- 同一 IP 短时间内大量 `Failed password` → 暴力破解
- 尝试 root/admin 等常见用户名 → 字典攻击
- 来自不同 IP 但时间集中 → 分布式暴力破解

### Q8: dmesg 里有硬件错误怎么判断严重性？

```bash
# 1. 查看 MCE（Machine Check Exception）
dmesg -T 2>/dev/null | grep -i "mce\|machine check" | tail -10

# 2. 查看 EDAC（内存纠错）
dmesg -T 2>/dev/null | grep -i "edac\|ecc" | tail -10
# CE (Corrected Error) → 已纠正，暂时不影响，但频繁出现要更换
# UE (Uncorrected Error) → 未纠正，必须立即处理

# 3. 查看磁盘错误
dmesg -T 2>/dev/null | grep -i "I/O error\|medium error\|sense error" | tail -10
smartctl -H /dev/sda 2>/dev/null  # 需要 smartmontools

# 4. 查看 mcelog（如果安装了）
cat /var/log/mcelog 2>/dev/null | tail -20
mcelog --client 2>/dev/null

# 5. 查看 rasdaemon（TencentOS 3/4）
ras-mc-ctl --errors 2>/dev/null
ras-mc-ctl --summary 2>/dev/null
```

### Q9: 怎么查看 cron 定时任务的执行日志？

```bash
# 方法 1: 查看 cron 日志文件
tail -50 /var/log/cron 2>/dev/null

# 方法 2: journalctl
journalctl -u crond --no-pager | tail -30
journalctl -u cron --no-pager | tail -30  # Ubuntu

# 方法 3: 按用户过滤
grep "用户名" /var/log/cron 2>/dev/null | tail -20

# 查看 crontab 配置
crontab -l 2>/dev/null
ls /etc/cron.d/ 2>/dev/null
cat /etc/crontab 2>/dev/null

# 查看 systemd timer（替代 cron 的定时任务）
systemctl list-timers --all --no-pager
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及日志删除或配置变更，AI 不会自动执行！**
> 
> 请用户根据诊断结果，自行判断是否需要执行以下操作。

### 1. 清理 journal 日志

```bash
# 保留最近 7 天的日志
journalctl --vacuum-time=7d

# 保留最多 500MB
journalctl --vacuum-size=500M

# 保留最多 3 个日志文件
journalctl --vacuum-files=3

# 永久限制 journal 大小（修改配置）
# 编辑 /etc/systemd/journald.conf：
# [Journal]
# SystemMaxUse=500M
# SystemMaxFileSize=100M
# MaxRetentionSec=30d
#
# 然后重启：
# systemctl restart systemd-journald
```

### 2. 配置 logrotate（日志轮转）

```bash
# 示例：为自定义应用配置 logrotate
cat > /etc/logrotate.d/myapp << 'EOF'
/var/log/myapp/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        /bin/kill -USR1 $(cat /var/run/myapp.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

# 测试配置
logrotate -d /etc/logrotate.d/myapp

# 手动强制执行
logrotate -f /etc/logrotate.d/myapp
```

**logrotate 常用参数**：
| 参数 | 说明 |
|------|------|
| `daily/weekly/monthly` | 轮转周期 |
| `rotate N` | 保留 N 个归档 |
| `compress` | gzip 压缩归档 |
| `delaycompress` | 延迟压缩（下次轮转时才压缩） |
| `missingok` | 日志文件不存在不报错 |
| `notifempty` | 空文件不轮转 |
| `create MODE OWNER GROUP` | 创建新文件的权限 |
| `copytruncate` | 先复制再清空（适合无法重新打开日志的程序） |
| `sharedscripts` | 多个文件匹配时只运行一次脚本 |
| `size NM` | 按大小轮转（不按时间） |
| `maxsize NM` | 即使未到周期，超过该大小也轮转 |

### 3. 配置 rsyslog 远程转发

```bash
# 编辑 /etc/rsyslog.conf 或 /etc/rsyslog.d/remote.conf

# 转发所有日志到远程服务器（TCP）
# *.* @@远程服务器IP:514

# 转发所有日志到远程服务器（UDP）
# *.* @远程服务器IP:514

# 只转发错误级别以上
# *.err @@远程服务器IP:514

# 重启 rsyslog
# systemctl restart rsyslog
```

### 4. 开启 journal 持久化

```bash
# 创建持久化目录
mkdir -p /var/log/journal
systemd-tmpfiles --create --prefix /var/log/journal

# 或修改配置
# 编辑 /etc/systemd/journald.conf：
# [Journal]
# Storage=persistent

# 重启 journald
# systemctl restart systemd-journald
```

### 5. 配置 journald 速率限制

```bash
# 如果日志被限速丢弃，会看到：
# "Suppressed N messages from ..."
# 
# 修改 /etc/systemd/journald.conf：
# [Journal]
# RateLimitIntervalSec=30s
# RateLimitBurst=10000
# 
# 或完全禁用限速（不推荐）：
# RateLimitIntervalSec=0
# 
# 重启 journald：
# systemctl restart systemd-journald
```

### 6. 清空指定日志文件

```bash
# 清空文件内容（保留文件描述符，推荐）
> /var/log/messages
# 或
cat /dev/null > /var/log/messages

# 注意：不要用 rm 删除正在被写入的日志文件！
# rm 后 rsyslog 仍然往已删除的 fd 写，空间不会释放
# 如果误删了，需要重启 rsyslog：
# systemctl restart rsyslog
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看最近日志 | `journalctl -n 50 --no-pager` |
| 只看错误 | `journalctl -p err --no-pager -n 50` |
| 本次启动日志 | `journalctl -b --no-pager \| tail -100` |
| 上次启动日志 | `journalctl -b -1 --no-pager \| tail -100` |
| 今天的日志 | `journalctl --since today --no-pager` |
| 最近1小时 | `journalctl --since "1 hour ago" --no-pager` |
| 时间段过滤 | `journalctl --since "10:00" --until "12:00"` |
| 指定服务日志 | `journalctl -u 服务名 --no-pager` |
| 内核日志 | `journalctl -k --no-pager` 或 `dmesg -T` |
| 实时跟踪 | `journalctl -f` |
| 查看 OOM | `journalctl -k \| grep -i oom` |
| 登录记录 | `last -n 20` |
| 失败登录 | `lastb -n 20` |
| SSH 失败 | `journalctl -u sshd \| grep "Failed password"` |
| 传统系统日志 | `tail -50 /var/log/messages` |
| 安全日志 | `tail -50 /var/log/secure` |
| cron 日志 | `tail -30 /var/log/cron` |
| journal 空间 | `journalctl --disk-usage` |
| /var/log 大小 | `du -sh /var/log/* \| sort -rh \| head -15` |
| logrotate 状态 | `cat /var/lib/logrotate/logrotate.status` |
| logrotate 调试 | `logrotate -d /etc/logrotate.conf` |
| audit 日志 | `ausearch -ts recent` |
| 启动记录 | `journalctl --list-boots` |
| 重启记录 | `last -x reboot` |
| Docker 日志 | `docker logs --tail 50 容器名` |

---

## 快速排查流程图

```
系统有报错吗？
├── 看系统错误 → journalctl -p err --no-pager -n 50
│   ├── 有错误 → 根据错误信息进一步排查
│   └── 没有 → 看内核错误
├── 看内核错误 → dmesg -T | grep -i "error|fail|bug"
│   ├── 硬件错误（MCE/EDAC） → 硬件故障，需更换
│   ├── 磁盘 IO 错误 → 磁盘故障，检查 SMART
│   ├── 文件系统错误 → 文件系统损坏，需 fsck
│   └── OOM → 内存不足，看 Q2
└── 看失败服务 → systemctl list-units --state=failed

进程被杀了？
├── 是 OOM 吗？ → journalctl -k | grep "oom\|killed process"
│   ├── 是 → 查看哪个进程被杀、当时内存状态
│   └── 不是 → 查看 signal（kill -9?）
├── 查看 coredump → coredumpctl list
└── 查看 audit → ausearch -ts recent | grep 进程名

日志太大了？
├── 哪个最大？ → du -sh /var/log/* | sort -rh | head -10
├── journal 占多少？ → journalctl --disk-usage
├── logrotate 正常吗？ → logrotate -d /etc/logrotate.conf
│   ├── 正常 → 调整轮转策略（保留天数、文件数量）
│   └── 报错 → 修复配置
└── Docker 日志？ → find /var/lib/docker -name "*-json.log" -ls

看不到历史日志？
├── journal 持久化了吗？ → ls /var/log/journal/
│   ├── 有 → 检查 --list-boots 看启动记录
│   └── 没有 → 开启持久化
├── rsyslog 在运行吗？ → systemctl status rsyslog
└── 传统日志存在吗？ → ls -la /var/log/messages
```

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|-------------|-------------|-------------|
| 日志系统 | rsyslog + journald | rsyslog + journald | rsyslog + journald |
| rsyslog 版本 | 8.24.x | 8.2102.x | 8.2310.x+ |
| journald 持久化 | 默认不持久化 | 默认不持久化 | 默认不持久化 |
| logrotate | cron.daily 触发 | systemd timer 触发 | systemd timer 触发 |
| audit 版本 | audit 2.x | audit 3.0.x | audit 3.1.x+ |
| journal 压缩 | 不支持 lz4 | 支持 lz4 | 支持 lz4/zstd |
| 日志文件路径 | `/var/log/messages` | `/var/log/messages` | `/var/log/messages` |
| 安全日志路径 | `/var/log/secure` | `/var/log/secure` | `/var/log/secure` |
| dmesg 时间格式 | `-T` 可用 | `-T`/`--time-format=iso` | `-T`/`--time-format=iso` |

> **注意**：
> - TencentOS 2 的 journalctl 部分高级过滤选项可能不可用（如 `--output=json-seq`）
> - TencentOS 3/4 的 logrotate 由 systemd timer 触发（`logrotate.timer`），不再依赖 cron
> - 所有版本默认 journal 不持久化（`Storage=auto` 且无 `/var/log/journal` 目录），重启后 journal 日志丢失
> - TencentOS 4 的 journald 支持 zstd 压缩，空间利用率更高

## 相关技能

- **service-status**：服务状态管理与排查
- **kdump-check**：kdump 配置与故障排查
- **disk-space**：磁盘空间排查
- **network-check**：网络连通性排查
