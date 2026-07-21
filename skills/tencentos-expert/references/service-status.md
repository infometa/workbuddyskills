---
name: service-status
description: 检查和管理 systemd 服务状态，包括服务启动失败排查、状态查询、 日志查看、开机自启配置、服务依赖分析、自定义 service 编写、 资源占用查看、systemd timer 定时任务管理等。
description_zh: systemd 服务状态管理与故障排查
description_en: Systemd service management and failure troubleshooting
version: 1.0.0
---

# 服务状态管理

帮助检查和管理 systemd 服务状态，包括服务启动失败排查、服务状态查询、日志查看、开机自启配置、服务依赖分析、自定义 service 编写等。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看状态、查看日志、查看配置），**不自动执行服务启停和配置变更操作**。
> 
> 启动、停止、重启服务以及修改 service 文件等操作仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**"服务起不来"类**（最常见）：
- "nginx 启动不了"、"mysql 起不来"、"服务启动失败了"
- "systemctl start 失败"、"启动报错"、"服务起不来了"
- "启动了但马上就停了"、"start 之后 status 还是 inactive"
- "报错 failed to start"、"Job xxx failed"
- "Unit not found"、"找不到这个服务"

**"服务挂了"类**（服务异常退出）：
- "服务突然挂了"、"进程不见了"、"服务崩了"
- "服务自动重启了"、"服务运行一会就挂"
- "OOM 被杀了"、"killed by signal"
- "服务状态是 failed"、"activating 卡住了"
- "服务反复重启"、"频繁 restart"

**"查看服务状态"类**：
- "怎么看服务有没有在运行"、"服务是什么状态"
- "查看服务状态"、"检查一下 nginx 有没有启动"
- "哪些服务在跑"、"运行了哪些服务"
- "开机启动了哪些服务"、"enabled 的服务有哪些"
- "failed 的服务有哪些"、"有没有报错的服务"

**"服务日志"类**：
- "怎么看服务日志"、"启动报什么错"
- "journalctl 怎么用"、"日志在哪里看"
- "看一下最近的错误日志"、"查看 nginx 的日志"
- "服务为什么挂了，看下日志"、"tail -f 服务日志"
- "日志太多了怎么过滤"、"只看错误日志"

**"开机自启动"类**：
- "怎么设置开机自启"、"怎么让服务开机自动启动"
- "怎么关闭开机启动"、"不想让这个服务开机启动"
- "哪些服务是开机自启的"、"怎么查看 enable 了哪些"
- "服务 enable 了但没自启"、"开机自启不生效"

**"服务依赖"类**：
- "服务启动顺序不对"、"依赖的服务没起来"
- "A 服务要等 B 服务先起"、"服务之间的依赖关系"
- "怎么查看服务的依赖"、"这个服务依赖什么"
- "被依赖的服务挂了影响其他的吗"

**"自定义服务"类**：
- "怎么写 systemd service 文件"、"怎么把脚本变成服务"
- "服务配置文件怎么写"、"service unit 的格式"
- "怎么修改服务的启动参数"、"ExecStart 怎么配"
- "怎么让服务崩了自动重启"、"Restart=always 怎么配"

**"资源占用"类**：
- "这个服务占了多少内存"、"服务 CPU 占用高"
- "服务资源限制怎么设置"、"怎么限制服务的内存"
- "cgroup 怎么看"、"systemd-cgtop 怎么用"

**"定时任务/Timer"类**：
- "systemd timer 怎么用"、"怎么设置定时任务"
- "crontab 和 timer 有什么区别"
- "查看有哪些定时任务"、"timer 没触发怎么回事"

## 诊断步骤

以下命令可由 AI 自动执行，用于诊断服务状态问题。

### 步骤 1：查看服务当前状态

```bash
# 查看指定服务的详细状态
systemctl status 服务名

# 查看服务状态（简洁版）
systemctl is-active 服务名

# 查看服务是否开机自启
systemctl is-enabled 服务名

# 查看服务是否存在
systemctl list-unit-files | grep 服务名

# 查看服务的完整属性
systemctl show 服务名
```

**输出解读**：
- `active (running)`：服务正在运行
- `inactive (dead)`：服务未运行
- `failed`：服务启动失败或异常退出
- `activating (start)`：服务正在启动中
- `activating (auto-restart)`：服务正在自动重启
- `enabled`：开机自启已开启
- `disabled`：开机自启未开启
- `static`：服务不能单独启用，通常作为其他服务的依赖
- `masked`：服务被屏蔽，无法启动

### 步骤 2：查看服务日志（排查启动失败）

```bash
# 查看服务最近的日志（最常用）
journalctl -u 服务名 -n 50 --no-pager

# 查看服务最近一次启动的日志
journalctl -u 服务名 -b --no-pager | tail -100

# 只看错误级别日志
journalctl -u 服务名 -p err --no-pager -n 30

# 查看服务今天的日志
journalctl -u 服务名 --since today --no-pager | tail -50

# 查看服务最近 10 分钟的日志
journalctl -u 服务名 --since "10 min ago" --no-pager

# 实时跟踪服务日志（排查运行时问题）
journalctl -u 服务名 -f

# 查看内核日志（排查 OOM 等系统级问题）
journalctl -k --no-pager | grep -i -E "oom|kill|out of memory" | tail -20

# 查看上次启动失败的完整日志
journalctl -u 服务名 --no-pager -o verbose | tail -100
```

**常见错误日志关键词**：
- `Failed to start`：服务启动失败
- `Main process exited, code=exited, status=1`：主进程异常退出（退出码 1）
- `Killed`/`OOM`：被 OOM Killer 杀死
- `code=killed, signal=SEGV`：段错误（程序 bug）
- `code=killed, signal=ABRT`：程序异常中断
- `Binding to ... failed: Address already in use`：端口被占用
- `Permission denied`：权限不足
- `No such file or directory`：文件/路径不存在
- `timeout`：启动超时

### 步骤 3：查看所有服务的运行状态

```bash
# 查看所有运行中的服务
systemctl list-units --type=service --state=running --no-pager

# 查看所有失败的服务（重要！）
systemctl list-units --type=service --state=failed --no-pager

# 查看所有已加载的服务
systemctl list-units --type=service --no-pager

# 查看所有开机自启的服务
systemctl list-unit-files --type=service --state=enabled --no-pager

# 查看服务数量统计
echo "运行中: $(systemctl list-units --type=service --state=running --no-pager | grep -c '\.service')"
echo "已失败: $(systemctl list-units --type=service --state=failed --no-pager | grep -c '\.service')"
echo "开机自启: $(systemctl list-unit-files --type=service --state=enabled --no-pager | grep -c '\.service')"
```

### 步骤 4：查看服务配置文件

```bash
# 查看 service unit 文件位置
systemctl show -p FragmentPath 服务名

# 查看 service unit 文件内容
systemctl cat 服务名

# 查看所有覆盖配置（override/drop-in）
systemd-delta --type=overridden 2>/dev/null | grep 服务名

# 查看服务的 override 配置
cat /etc/systemd/system/服务名.service.d/*.conf 2>/dev/null

# 查看服务的关键配置属性
systemctl show 服务名 -p ExecStart,ExecReload,Restart,RestartSec,LimitNOFILE,LimitNPROC,MemoryMax --no-pager
```

**Unit 文件关键字段**：
- `ExecStart`：启动命令
- `ExecReload`：重载命令
- `WorkingDirectory`：工作目录
- `User`/`Group`：运行用户/组
- `Restart`：重启策略（no/always/on-failure/on-abnormal）
- `RestartSec`：重启间隔
- `Type`：服务类型（simple/forking/oneshot/notify）
- `LimitNOFILE`：文件描述符限制
- `MemoryMax`/`MemoryHigh`：内存限制

### 步骤 5：查看服务依赖关系

```bash
# 查看服务的依赖（它需要什么）
systemctl list-dependencies 服务名 --no-pager

# 查看谁依赖这个服务（反向依赖）
systemctl list-dependencies 服务名 --reverse --no-pager

# 查看服务的启动顺序依赖
systemctl show 服务名 -p After,Before,Requires,Wants,Conflicts --no-pager

# 查看服务的实际启动顺序
systemd-analyze critical-chain 服务名 2>/dev/null

# 查看所有服务的启动耗时
systemd-analyze blame --no-pager | head -20
```

**依赖关键字段**：
- `Requires`：强依赖，依赖的服务挂了自己也会停
- `Wants`：弱依赖，依赖的服务挂了不影响自己
- `After`：启动顺序，在指定服务之后启动
- `Before`：启动顺序，在指定服务之前启动
- `Conflicts`：冲突关系，不能同时运行

### 步骤 6：查看服务资源占用

```bash
# 查看服务的 cgroup 资源信息
systemctl status 服务名 | grep -E "Memory:|CPU:|Tasks:"

# 查看服务的详细资源使用
systemctl show 服务名 -p MemoryCurrent,CPUUsageNSec,TasksCurrent --no-pager

# 查看所有服务的资源占用排行
systemd-cgtop -b -n 1 2>/dev/null | head -20

# 查看服务主进程的资源占用
PID=$(systemctl show 服务名 -p MainPID --value)
if [[ "$PID" != "0" && -n "$PID" ]]; then
    ps -p "$PID" -o pid,ppid,user,%cpu,%mem,rss,vsz,comm --no-headers
fi

# 查看服务的资源限制配置
systemctl show 服务名 -p LimitNOFILE,LimitNPROC,MemoryMax,MemoryHigh,CPUQuota --no-pager
```

### 步骤 7：查看 systemd Timer（定时任务）

```bash
# 查看所有定时器
systemctl list-timers --all --no-pager

# 查看指定 timer 的状态
systemctl status 定时器名.timer

# 查看 timer 的配置
systemctl cat 定时器名.timer

# 查看 timer 关联的 service
systemctl cat 定时器名.service

# 查看 timer 的下次触发时间
systemctl show 定时器名.timer -p NextElapseUSecRealtime,LastTriggerUSec --no-pager
```

### 步骤 8：启动排查与系统级诊断

```bash
# 查看系统启动总耗时
systemd-analyze time 2>/dev/null

# 查看启动最慢的服务
systemd-analyze blame --no-pager | head -15

# 查看启动关键链
systemd-analyze critical-chain --no-pager 2>/dev/null

# 验证 unit 文件语法
systemd-analyze verify /etc/systemd/system/服务名.service 2>&1

# 查看 systemd 的版本
systemctl --version | head -1

# 查看系统运行级别
systemctl get-default

# 查看最近的系统启动记录
journalctl --list-boots --no-pager | tail -5

# 检查是否有 coredump
coredumpctl list 2>/dev/null | tail -10
```

---

## 常见问题解答

### Q1: 服务启动失败怎么排查？

```bash
# 1. 先看状态和错误提示
systemctl status 服务名

# 2. 看详细日志
journalctl -u 服务名 -n 50 --no-pager

# 3. 检查配置文件
systemctl cat 服务名

# 4. 检查端口是否被占用（如果服务需要监听端口）
ss -tlnp | grep :端口号

# 5. 检查文件/目录权限
ls -la /path/to/service/binary
ls -la /path/to/config

# 6. 手动运行启动命令试试
# 先看 ExecStart 是什么
systemctl show 服务名 -p ExecStart --no-pager
```

**常见启动失败原因及解决思路**：
1. **端口被占用** → `ss -tlnp | grep :端口` 找到占用进程
2. **配置文件错误** → 查看日志中的具体报错行
3. **权限不足** → 检查 `User=` 配置和文件权限
4. **文件不存在** → 检查 `ExecStart` 中的可执行文件路径
5. **依赖未就绪** → 检查 `After=` 和 `Requires=` 依赖
6. **资源不足** → 检查 OOM 日志或 `LimitNOFILE` 配置

### Q2: 服务运行一会就挂了怎么办？

```bash
# 1. 查看服务退出码和信号
systemctl show 服务名 -p ExecMainStatus,ExecMainCode --no-pager

# 2. 查看最近几次启动的日志
journalctl -u 服务名 --no-pager | tail -100

# 3. 是否被 OOM Killer 杀死
journalctl -k --no-pager | grep -i "oom\|killed process" | tail -10
dmesg | grep -i "oom\|killed process" | tail -10

# 4. 查看服务重启次数
systemctl show 服务名 -p NRestarts --no-pager

# 5. 检查 coredump
coredumpctl list 2>/dev/null | grep 服务名 | tail -5
```

**判断逻辑**：
- 退出码 137 / signal=KILL → 通常是 OOM 被杀
- 退出码 139 / signal=SEGV → 段错误（程序 bug）
- 退出码 1 → 程序内部错误，看日志
- 退出码 2 → 通常是参数错误或配置问题
- 退出码 126 → 命令不可执行（权限）
- 退出码 127 → 命令未找到（路径问题）

### Q3: 怎么设置服务开机自启？

```bash
# 查看当前是否开机自启
systemctl is-enabled 服务名

# 查看所有开机自启的服务
systemctl list-unit-files --type=service --state=enabled --no-pager
```

> **设置方法**（需用户手动执行）：
> ```bash
> # 开启开机自启
> systemctl enable 服务名
> 
> # 开启并立即启动
> systemctl enable --now 服务名
> 
> # 关闭开机自启
> systemctl disable 服务名
> ```

### Q4: 怎么把自己的脚本变成 systemd 服务？

需要编写一个 `.service` 文件。以下是模板：

```ini
# /etc/systemd/system/my-app.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/my-app
ExecStart=/opt/my-app/start.sh
ExecStop=/bin/kill -SIGTERM $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Type 选项说明**：
- `simple`：默认值，`ExecStart` 启动的进程就是主进程
- `forking`：传统 daemon 模式，进程 fork 后父进程退出
- `oneshot`：一次性任务，运行完就结束
- `notify`：服务启动完成后通过 sd_notify 通知 systemd
- `exec`：类似 simple，但 systemd 等 exec() 成功后才认为启动完

> **创建步骤**（需用户手动执行）：
> ```bash
> # 1. 创建 service 文件
> vim /etc/systemd/system/my-app.service
> 
> # 2. 重新加载 systemd 配置
> systemctl daemon-reload
> 
> # 3. 启动并设置开机自启
> systemctl enable --now my-app
> 
> # 4. 检查状态
> systemctl status my-app
> ```

### Q5: 服务反复重启（restart loop）怎么办？

```bash
# 1. 查看重启次数
systemctl show 服务名 -p NRestarts --no-pager

# 2. 查看重启策略
systemctl show 服务名 -p Restart,RestartSec,StartLimitBurst,StartLimitIntervalUSec --no-pager

# 3. 查看详细的启动/退出日志
journalctl -u 服务名 --no-pager | grep -E "Started|Stopped|Failed|Main process exited" | tail -20

# 4. 看每次重启的退出原因
journalctl -u 服务名 -p err --no-pager | tail -30
```

**常见原因**：
- 配置错误导致进程立即退出 → 修复配置
- 端口冲突导致反复起不来 → 释放端口
- OOM 反复被杀 → 增加内存或调整限制
- `StartLimitBurst` 达到上限后会停止尝试 → `systemctl reset-failed` 后重试

### Q6: 怎么查看服务占了多少资源？

```bash
# 方法 1: systemctl status 看摘要信息
systemctl status 服务名 | grep -E "Memory:|CPU:|Tasks:"

# 方法 2: systemctl show 看精确数值
systemctl show 服务名 -p MemoryCurrent,CPUUsageNSec,TasksCurrent --no-pager

# 方法 3: 看主进程的资源占用
PID=$(systemctl show 服务名 -p MainPID --value)
ps -p "$PID" -o pid,%cpu,%mem,rss,vsz,comm --no-headers 2>/dev/null

# 方法 4: cgroup top 整体排行
systemd-cgtop -b -n 1 2>/dev/null | head -15
```

### Q7: systemd timer 和 crontab 有什么区别？

```bash
# 查看系统中所有 timer
systemctl list-timers --all --no-pager

# 查看所有 crontab
crontab -l 2>/dev/null
ls /etc/cron.d/ 2>/dev/null
cat /etc/crontab 2>/dev/null
```

**区别说明**：
| 特性 | crontab | systemd timer |
|------|---------|---------------|
| 日志 | 需要配置 | 自动记录到 journal |
| 依赖管理 | 无 | 支持 After/Requires |
| 资源限制 | 无 | 支持 cgroup 限制 |
| 随机延迟 | 无 | 支持 RandomizedDelaySec |
| 精度 | 分钟级 | 微秒级 |
| 错过的任务 | 不补执行 | 支持 Persistent=true 补执行 |

### Q8: 怎么查看服务的启动耗时？

```bash
# 查看系统启动总耗时
systemd-analyze time 2>/dev/null

# 查看最慢的服务
systemd-analyze blame --no-pager | head -20

# 查看服务启动的关键路径
systemd-analyze critical-chain 服务名 2>/dev/null
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及服务状态变更，AI 不会自动执行！**
> 
> 请用户根据诊断结果，自行判断是否需要执行以下操作。

### 1. 启动/停止/重启服务

```bash
# 启动服务
systemctl start 服务名

# 停止服务
systemctl stop 服务名

# 重启服务
systemctl restart 服务名

# 重载配置（不中断服务）
systemctl reload 服务名

# 先尝试 reload，失败再 restart
systemctl reload-or-restart 服务名
```

### 2. 设置/取消开机自启

```bash
# 开机自启
systemctl enable 服务名

# 开机自启并立即启动
systemctl enable --now 服务名

# 取消开机自启
systemctl disable 服务名

# 彻底屏蔽服务（无法被启动，包括依赖拉起）
systemctl mask 服务名

# 解除屏蔽
systemctl unmask 服务名
```

### 3. 修改服务配置（推荐 override 方式）

```bash
# 使用 override（推荐，不修改原始文件）
systemctl edit 服务名

# 这会创建 /etc/systemd/system/服务名.service.d/override.conf
# 示例内容：
# [Service]
# Restart=always
# RestartSec=5
# LimitNOFILE=65535

# 修改后重新加载
systemctl daemon-reload
systemctl restart 服务名
```

### 4. 清除失败状态

```bash
# 清除指定服务的失败状态
systemctl reset-failed 服务名

# 清除所有服务的失败状态
systemctl reset-failed
```

### 5. 创建 systemd timer 定时任务

```bash
# 创建 service 文件 /etc/systemd/system/my-task.service
cat > /etc/systemd/system/my-task.service << 'EOF'
[Unit]
Description=My Periodic Task

[Service]
Type=oneshot
ExecStart=/path/to/script.sh
EOF

# 创建 timer 文件 /etc/systemd/system/my-task.timer
cat > /etc/systemd/system/my-task.timer << 'EOF'
[Unit]
Description=Run my task periodically

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 启用
systemctl daemon-reload
systemctl enable --now my-task.timer
```

**OnCalendar 时间格式**：
- `*-*-* 02:00:00`：每天凌晨 2 点
- `Mon *-*-* 09:00:00`：每周一上午 9 点
- `*-*-01 00:00:00`：每月 1 日
- `*:0/15`：每 15 分钟
- `hourly`/`daily`/`weekly`/`monthly`

### 6. 设置服务资源限制

```bash
# 使用 override 方式设置资源限制
systemctl edit 服务名

# 内容示例：
# [Service]
# MemoryMax=512M
# MemoryHigh=400M
# CPUQuota=50%
# LimitNOFILE=65535
# LimitNPROC=4096
# TasksMax=512

systemctl daemon-reload
systemctl restart 服务名
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看服务状态 | `systemctl status 服务名` |
| 判断是否运行 | `systemctl is-active 服务名` |
| 判断是否自启 | `systemctl is-enabled 服务名` |
| 查看服务日志 | `journalctl -u 服务名 -n 50 --no-pager` |
| 只看错误日志 | `journalctl -u 服务名 -p err --no-pager` |
| 实时跟踪日志 | `journalctl -u 服务名 -f` |
| 查看运行中的服务 | `systemctl list-units --type=service --state=running` |
| 查看失败的服务 | `systemctl list-units --type=service --state=failed` |
| 查看自启服务 | `systemctl list-unit-files --type=service --state=enabled` |
| 查看 unit 文件 | `systemctl cat 服务名` |
| 查看服务属性 | `systemctl show 服务名` |
| 查看依赖关系 | `systemctl list-dependencies 服务名` |
| 查看反向依赖 | `systemctl list-dependencies 服务名 --reverse` |
| 查看资源占用 | `systemctl status 服务名 \| grep Memory` |
| 查看启动耗时 | `systemd-analyze blame` |
| 查看 cgroup 排行 | `systemd-cgtop -b -n 1` |
| 查看定时器 | `systemctl list-timers --all` |
| 查看 OOM 记录 | `journalctl -k \| grep -i oom` |
| 查看 coredump | `coredumpctl list` |
| 验证 unit 语法 | `systemd-analyze verify /path/to/unit` |

---

## 快速排查流程图

```
服务起不来？
├── 服务存在吗？ → systemctl list-unit-files | grep 服务名
│   └── 不存在 → unit 文件未创建或路径不对
├── 服务什么状态？ → systemctl status 服务名
│   ├── inactive → 从未启动，尝试手动启动看报错
│   ├── failed → 看日志 journalctl -u 服务名
│   ├── activating → 启动中/卡住，可能是依赖或超时
│   └── masked → 被屏蔽了，需要 unmask
├── 日志说什么？ → journalctl -u 服务名 -n 50
│   ├── Address in use → 端口被占用
│   ├── Permission denied → 权限不足
│   ├── No such file → 文件路径错误
│   └── OOM/Killed → 内存不足
└── 端口被占了？ → ss -tlnp | grep :端口

服务总是挂？
├── 退出码是什么？ → systemctl show 服务名 -p ExecMainStatus
│   ├── 137 → OOM 被杀
│   ├── 139 → 段错误
│   └── 1/2 → 程序错误，看日志
├── 有 coredump 吗？ → coredumpctl list | grep 服务名
├── 重启了多少次？ → systemctl show 服务名 -p NRestarts
└── Restart 策略？ → systemctl show 服务名 -p Restart,RestartSec
```

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|-------------|-------------|-------------|
| init 系统 | systemd (v219) | systemd (v239) | systemd (v252+) |
| cgroup 版本 | cgroup v1 | cgroup v1 | cgroup v2 |
| 资源控制 | 基础 | 完善 | 完善 + PSI |
| journal 日志 | 基础 | 完善 | 完善 + 压缩 |
| timer 精度 | 基础 | 完善 | 完善 |
| socket activation | 支持 | 支持 | 支持 |
| portable services | 不支持 | 部分支持 | 支持 |

> **注意**：
> - TencentOS 2 的 systemd 版本较老，部分新特性（如 `MemoryMax`、`CPUQuota`）可能不可用，需用 `MemoryLimit` 替代
> - TencentOS 4 使用 cgroup v2，资源管理更精细，支持 `MemoryHigh`、`MemoryMax`、`CPUWeight` 等
> - 所有版本均支持 `systemctl`、`journalctl` 基础操作

## 相关技能

- **process-management**：进程管理与排查
- **log-analysis**：日志分析与过滤
- **cgroup-resource**：cgroup 资源管理
- **boot-troubleshoot**：系统启动故障排查
