---
name: kdump-check
description: 检查和排查 kdump（内核崩溃转储）相关问题，包括 kdump 服务未启动、 crashkernel 参数配置、vmcore 未生成、vmcore 存储路径配置、 远程转储、kdump 测试验证、vmcore 分析准备等。
description_zh: kdump 内核崩溃转储配置与故障排查
description_en: Kdump kernel crash dump configuration and troubleshooting
version: 1.0.0
---

# kdump 配置与故障排查

帮助检查和排查 kdump（内核崩溃转储）相关问题，包括 kdump 服务未启动、crashkernel 参数配置、vmcore 未生成、vmcore 存储路径配置、远程转储、kdump 测试验证、vmcore 分析准备等。

## 安全原则

> ⚠️ **重要**：AI 只执行查询/诊断命令（查看状态、查看配置、检查日志），**不自动执行以下高危操作**：
> 
> - 不自动触发内核 panic（echo c > /proc/sysrq-trigger）
> - 不自动修改 grub/内核启动参数
> - 不自动修改 kdump.conf 配置
> - 不自动重启 kdump 服务
> - 不自动安装/卸载软件包
>
> 以上操作仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**"kdump 服务没起来"类**（最常见）：
- "kdump 没有启动"、"kdump 是 inactive 的"、"kdump 服务不 active"
- "systemctl status kdump 报错"、"kdump 起不来"
- "kexec-tools 没装"、"kdump 服务不存在"
- "kdump 启动失败"、"loaded but not active"
- "dracut 报错"、"kdump initramfs 生成失败"

**"配了 kdump 但没生成 vmcore"类**（极高频）：
- "机器重启了但没有 vmcore"、"crash 了但是没 dump"
- "vmcore 在哪"、"/var/crash 是空的"
- "没有 crashkernel 参数"、"vmcore 不完整"
- "磁盘空间不够没写 vmcore"、"dump 写到一半断了"
- "panic 了但是没触发 kdump"、"softlockup 没生成 vmcore"
- "生成了 vmcore 但是很小，像是不完整的"

**"crashkernel 参数"类**：
- "crashkernel 应该配多少"、"crashkernel 参数怎么加"
- "grub 里怎么配 crashkernel"、"内核启动参数"
- "大内存机器 crashkernel 要多少"、"512M 够不够"
- "crashkernel 参数改了不生效"、"重启后参数丢了"
- "crashkernel=auto 是什么意思"

**"kdump 配置"类**：
- "kdump.conf 怎么配"、"vmcore 存到哪"
- "怎么改 vmcore 路径"、"怎么存到其他目录"
- "core_collector 怎么配"、"makedumpfile 参数"
- "dump_level 什么意思"、"压缩等级怎么调"
- "kdump 只保留最近几个 vmcore"

**"kdump 转储到远程"类**：
- "vmcore 怎么存到 NFS"、"vmcore 传到远程服务器"
- "kdump ssh 转储"、"网络 dump"
- "远程转储配不通"、"NFS 挂载失败 dump 也失败了"

**"测试 kdump 是否生效"类**：
- "怎么测试 kdump 有没有配好"、"sysrq-trigger"
- "怎么手动触发 panic"、"怎么验证 kdump 能正常工作"
- "触发 crash 但是没生成 vmcore"

**"vmcore 分析准备"类**：
- "vmcore 怎么分析"、"crash 工具怎么用"
- "debuginfo 包怎么装"、"kernel-debuginfo 在哪下"
- "vmlinux 在哪"、"crash 打不开 vmcore"

**"crashkernel 内存预留"类**：
- "kdump 启动报内存不够"、"Cannot allocate memory"
- "crashkernel 预留太小"、"kdump 内核加载失败"
- "kexec load 失败"、"内存预留不够"

**"kdump 兼容性"类**：
- "UEFI 下 kdump 不工作"、"secure boot 影响 kdump"
- "kexec 加载失败"、"新内核 kdump 不支持"
- "虚拟机里 kdump 能用吗"、"容器里能配 kdump 吗"

## 诊断步骤

以下命令可由 AI 自动执行，用于诊断 kdump 问题。

### 步骤 1：检查 kdump 服务状态

```bash
# 查看 kdump 服务状态
systemctl status kdump

# 查看 kdump 是否 active
systemctl is-active kdump

# 查看 kdump 是否开机自启
systemctl is-enabled kdump

# 查看 kexec-tools 是否安装
rpm -q kexec-tools 2>/dev/null || dpkg -l kexec-tools 2>/dev/null

# 查看 kdump 相关包版本
rpm -qa | grep -E "kexec-tools|kdump|makedumpfile" 2>/dev/null
```

**输出解读**：
- `active (exited)`：kdump 正常工作（exited 是正常的，因为它加载完 crash kernel 后就退出了）
- `inactive (dead)`：kdump 未启动，crash kernel 未加载
- `failed`：kdump 启动失败，需要看日志
- `enabled`：开机自启已开启
- `disabled`：开机自启未开启
- `not-found`：kexec-tools 未安装

### 步骤 2：检查 crashkernel 内核参数

```bash
# 查看当前内核启动参数中的 crashkernel 配置
cat /proc/cmdline | tr ' ' '\n' | grep -i crashkernel

# 完整查看内核启动参数
cat /proc/cmdline

# 查看 crashkernel 预留内存是否成功
dmesg | grep -i "crashkernel\|crash kernel\|reserved" | head -20

# 查看内核预留内存信息
cat /proc/iomem | grep -i "crash kernel"

# 查看系统总内存
free -h | head -2

# 查看 grub 配置中的 crashkernel
grep -i crashkernel /etc/default/grub 2>/dev/null
grep -i crashkernel /boot/grub2/grub.cfg 2>/dev/null | head -5
grep -i crashkernel /boot/grub/grub.cfg 2>/dev/null | head -5
# TencentOS 4 使用 grubby
grubby --info=DEFAULT 2>/dev/null | grep -i crashkernel
```

**输出解读**：
- `crashkernel=auto`：自动预留（TencentOS 3 默认）
- `crashkernel=256M`：固定预留 256MB
- `crashkernel=512M`：固定预留 512MB
- 如果 `/proc/cmdline` 中没有 `crashkernel` → kdump 肯定不工作
- 如果 `/proc/iomem` 中没有 `Crash kernel` → 内存预留失败

### 步骤 3：检查 kdump 配置文件

```bash
# 查看 kdump 主配置文件
cat /etc/kdump.conf

# 过滤掉注释看有效配置
grep -v '^#' /etc/kdump.conf | grep -v '^$'

# 查看 vmcore 保存路径配置
grep -E "^path|^ext4|^xfs|^nfs|^ssh|^raw" /etc/kdump.conf

# 查看 core_collector 配置（makedumpfile 参数）
grep "^core_collector" /etc/kdump.conf

# 查看 kdump 默认保存路径（如果 kdump.conf 中没配 path）
# 默认: /var/crash/
echo "默认路径: /var/crash/"
ls -la /var/crash/ 2>/dev/null

# 查看 kdump sysconfig 配置
cat /etc/sysconfig/kdump 2>/dev/null | grep -v '^#' | grep -v '^$'

# TencentOS 4 额外配置
cat /etc/kdump/kdump.conf 2>/dev/null | grep -v '^#' | grep -v '^$'
```

**kdump.conf 关键配置说明**：
- `path /var/crash`：vmcore 保存路径
- `core_collector makedumpfile -l --message-level 7 -d 31`：dump 收集器及参数
- `ext4 /dev/vda1`：指定 dump 到某个分区
- `nfs server:/export/crash`：NFS 远程转储
- `ssh user@server`：SSH 远程转储
- `default reboot`：dump 失败后的动作（reboot/halt/poweroff/shell）
- `dracut_args --install "/bin/xxx"`：额外的 dracut 参数

### 步骤 4：检查 vmcore 是否存在

```bash
# 查看 vmcore 保存目录
ls -lah /var/crash/ 2>/dev/null

# 递归查看所有 vmcore 文件
find /var/crash/ -name "vmcore*" -o -name "dmesg*" 2>/dev/null | head -20

# 查看最近的 vmcore
ls -lhrt /var/crash/*/vmcore 2>/dev/null | tail -5

# 查看 vmcore 文件大小
du -sh /var/crash/*/ 2>/dev/null | tail -10

# 查看 /var/crash 所在分区的空间
df -h /var/crash/

# 查看最近的 vmcore-dmesg（不需要 crash 工具就能看）
LATEST_CRASH=$(ls -td /var/crash/*/ 2>/dev/null | head -1)
if [[ -n "$LATEST_CRASH" ]]; then
    echo "最近的 crash 目录: $LATEST_CRASH"
    ls -la "$LATEST_CRASH"
    echo "--- vmcore-dmesg.txt 最后 50 行 ---"
    tail -50 "${LATEST_CRASH}/vmcore-dmesg.txt" 2>/dev/null
fi
```

### 步骤 5：检查 kdump 启动日志（排查启动失败）

```bash
# 查看 kdump 服务日志
journalctl -u kdump -n 50 --no-pager

# 查看 kdump 最近一次启动的日志
journalctl -u kdump -b --no-pager

# 查看 kdump 错误日志
journalctl -u kdump -p err --no-pager

# 查看 kexec 相关内核日志
dmesg | grep -i "kexec\|kdump\|crash" | tail -20

# 查看 kdump initramfs 是否存在
ls -la /boot/initramfs-*kdump.img 2>/dev/null
ls -la /boot/initrd-*kdump 2>/dev/null

# 查看 kdump initramfs 的生成时间和大小
stat /boot/initramfs-$(uname -r)kdump.img 2>/dev/null
```

**常见启动失败原因**：
- `No memory reserved for crash kernel`：没有 crashkernel 参数
- `Cannot open /boot/initramfs-xxxkdump.img`：kdump initramfs 不存在
- `Not enough memory`：预留内存不足
- `kexec: load failed`：crash kernel 加载失败
- `dracut: FAILED`：kdump initramfs 生成失败

### 步骤 6：检查 kdump 转储能力

```bash
# 检查 kexec 是否已加载 crash kernel
cat /sys/kernel/kexec_crash_loaded
# 1 = 已加载（正常）
# 0 = 未加载（异常，即使 kdump 服务是 active）

# 查看 crash kernel 大小
cat /sys/kernel/kexec_crash_size

# 查看 sysrq 是否启用（用于测试触发 panic）
cat /proc/sys/kernel/sysrq

# 查看 panic 相关内核参数
sysctl kernel.panic 2>/dev/null
sysctl kernel.panic_on_oops 2>/dev/null
sysctl kernel.softlockup_panic 2>/dev/null
sysctl kernel.hung_task_panic 2>/dev/null
sysctl kernel.unknown_nmi_panic 2>/dev/null

# 查看 NMI watchdog 状态
cat /proc/sys/kernel/nmi_watchdog 2>/dev/null

# 检查 makedumpfile 是否可用
which makedumpfile 2>/dev/null && makedumpfile --help 2>&1 | head -3
```

**panic 相关参数说明**：
- `kernel.panic = 0`：panic 后不自动重启（0 表示挂起）
- `kernel.panic = 10`：panic 后 10 秒自动重启
- `kernel.panic_on_oops = 1`：oops 时也触发 panic（建议开启，这样 oops 也能生成 vmcore）
- `kernel.softlockup_panic = 1`：softlockup 时触发 panic
- `kernel.hung_task_panic = 1`：hung_task 超时触发 panic
- `kernel.sysrq = 1`：启用所有 sysrq 功能（用于手动触发 panic 测试）

### 步骤 7：检查磁盘空间是否足够存 vmcore

```bash
# vmcore 大小估算（约等于已用物理内存，压缩后约 1/4 ~ 1/2）
echo "=== 内存使用情况 ==="
free -h

# /var/crash 分区的可用空间
echo "=== /var/crash 磁盘空间 ==="
df -h /var/crash/ 2>/dev/null || df -h /var/

# 估算 vmcore 大小
MEM_USED_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_TOTAL_MB=$((MEM_USED_KB / 1024))
echo "总内存: ${MEM_TOTAL_MB}MB"
echo "预估 vmcore 最大: ${MEM_TOTAL_MB}MB（未压缩）"
echo "预估 vmcore 压缩后: $((MEM_TOTAL_MB / 4))MB ~ $((MEM_TOTAL_MB / 2))MB"

# 查看 makedumpfile dump_level 对大小的影响
echo ""
echo "=== dump_level 对比 ==="
echo "dump_level 0: 完整内存（最大）"
echo "dump_level 1: 排除 zero pages"
echo "dump_level 31: 排除 zero/cache/private/free pages（最小，推荐）"

# 查看现有 vmcore 占用的空间
echo ""
echo "=== 现有 vmcore 占用 ==="
du -sh /var/crash/*/ 2>/dev/null || echo "无历史 vmcore"
```

### 步骤 8：检查 kernel-debuginfo（vmcore 分析准备）

```bash
# 查看当前内核版本
uname -r

# 查看是否安装了 debuginfo
rpm -qa | grep kernel-debuginfo 2>/dev/null

# 查看 crash 工具是否安装
which crash 2>/dev/null && crash --version 2>/dev/null | head -1

# 查看 vmlinux 是否存在
ls -la /usr/lib/debug/lib/modules/$(uname -r)/vmlinux 2>/dev/null

# 查看 debuginfo 仓库是否配置
grep -r "debuginfo" /etc/yum.repos.d/ 2>/dev/null | head -5

# 查看可用的 debuginfo 包
yum list available kernel-debuginfo 2>/dev/null | head -5
dnf list available kernel-debuginfo 2>/dev/null | head -5
```

### 步骤 9：检查历史 crash 记录

```bash
# 查看最近的系统意外重启记录
last -x reboot | head -10

# 查看最近的关机/crash 记录
last -x shutdown | head -10

# 查看内核日志中的 panic/oops 记录
journalctl -k -b -1 --no-pager 2>/dev/null | grep -i "panic\|oops\|bug\|rip\|call trace" | head -20

# 查看上次启动的日志（如果是 crash 后重启）
journalctl -b -1 --no-pager 2>/dev/null | tail -50

# 查看 abrt 记录（如果安装了 abrt）
ls -la /var/spool/abrt/ 2>/dev/null

# 查看 mcelog（硬件错误）
cat /var/log/mcelog 2>/dev/null | tail -20
```

---

## 常见问题解答

### Q1: kdump 服务启动失败怎么排查？

```bash
# 1. 检查 kdump 服务状态和错误
systemctl status kdump

# 2. 看详细日志
journalctl -u kdump --no-pager

# 3. 检查 crashkernel 参数
cat /proc/cmdline | tr ' ' '\n' | grep crashkernel

# 4. 检查 crash kernel 是否加载
cat /sys/kernel/kexec_crash_loaded

# 5. 检查 kdump initramfs
ls -la /boot/initramfs-$(uname -r)kdump.img

# 6. 检查 kdump.conf 语法
# TencentOS 3+
kdumpctl showmem 2>/dev/null
```

**常见启动失败原因及解决思路**：

1. **没有 crashkernel 参数**
   - 现象：日志显示 "No memory reserved for crash kernel"
   - 排查：`cat /proc/cmdline | grep crashkernel`
   - 解决（用户操作）：添加 crashkernel 参数并重启

2. **crashkernel 预留内存不足**
   - 现象：日志显示 "Not enough memory" 或 "kexec: load failed"
   - 排查：`cat /sys/kernel/kexec_crash_size`
   - 解决（用户操作）：增大 crashkernel 值

3. **kdump initramfs 不存在或损坏**
   - 现象：日志显示 "Cannot open /boot/initramfs-xxxkdump.img"
   - 排查：`ls -la /boot/initramfs-*kdump*`
   - 解决（用户操作）：`kdumpctl rebuild` 或 `mkdumprd`

4. **kexec-tools 未安装**
   - 现象：`systemctl status kdump` 显示 "not-found"
   - 排查：`rpm -q kexec-tools`
   - 解决（用户操作）：`yum install kexec-tools`

5. **SELinux 阻止**
   - 现象：日志中有 "avc: denied"
   - 排查：`ausearch -m avc -ts recent | grep kdump`
   - 解决（用户操作）：调整 SELinux 策略

### Q2: 机器 crash 了但没有生成 vmcore？

```bash
# 逐项排查清单
echo "=== 1. kdump 服务在 crash 前是否 active ==="
systemctl is-active kdump

echo "=== 2. crash kernel 是否已加载 ==="
cat /sys/kernel/kexec_crash_loaded

echo "=== 3. crashkernel 参数是否存在 ==="
cat /proc/cmdline | tr ' ' '\n' | grep crashkernel

echo "=== 4. vmcore 保存路径和空间 ==="
grep -v '^#' /etc/kdump.conf | grep -v '^$'
df -h /var/crash/ 2>/dev/null

echo "=== 5. 是否真的发生了 panic ==="
# softlockup/hung_task 默认不触发 panic
sysctl kernel.softlockup_panic
sysctl kernel.hung_task_panic
sysctl kernel.panic_on_oops

echo "=== 6. 上次重启记录 ==="
last -x reboot | head -3
```

**没有生成 vmcore 的常见原因**：

1. **kdump 服务未启动** → crash 前 kdump 不是 active 状态
2. **没有 crashkernel 参数** → crash kernel 根本没加载
3. **crash 类型未触发 panic** → softlockup/hung_task 默认不 panic
   - `kernel.softlockup_panic = 0`（默认）→ 不会生成 vmcore
   - `kernel.panic_on_oops = 0`（默认可能是 0）→ oops 不会生成 vmcore
4. **磁盘空间不足** → vmcore 写入中途失败
5. **硬件问题** → NMI 或 MCE 导致 kdump 也无法正常工作
6. **不是 panic 重启** → 可能是掉电、watchdog 重启、手动重启
7. **kdump initramfs 损坏** → 进入 kdump 内核后无法正常初始化

### Q3: crashkernel 参数应该配多少？

```bash
# 查看当前配置和内存
echo "当前 crashkernel: $(cat /proc/cmdline | tr ' ' '\n' | grep crashkernel)"
echo "预留大小: $(cat /sys/kernel/kexec_crash_size 2>/dev/null) bytes"
echo "系统总内存: $(free -h | awk '/Mem:/{print $2}')"
echo "内核版本: $(uname -r)"

# TencentOS 3+ 的推荐值
kdumpctl estimate 2>/dev/null
```

**推荐配置**（不同内存规格）：

| 系统内存 | 推荐 crashkernel | 说明 |
|---------|-----------------|------|
| ≤ 2GB | `crashkernel=128M` | 小内存机器 |
| 2GB ~ 8GB | `crashkernel=256M` | 常规配置 |
| 8GB ~ 64GB | `crashkernel=512M` | 推荐值 |
| 64GB ~ 256GB | `crashkernel=768M` | 大内存机器 |
| > 256GB | `crashkernel=1G` | 超大内存机器 |
| 自动 | `crashkernel=auto` | TencentOS 3 推荐，自动计算 |

> **注意**：
> - `crashkernel=auto` 在 TencentOS 3/4 上推荐使用，会根据内存自动计算
> - `crashkernel=auto` 在内存 < 2GB 时可能不会预留（因此小内存机器建议手动指定）
> - 如果系统加载了很多内核模块或驱动，可能需要更多预留内存
> - TencentOS 2 上 `crashkernel=auto` 的最小内存要求是 2GB

### Q4: 如何测试 kdump 是否工作？

```bash
# 预检查（AI 可自动执行）
echo "=== kdump 测试预检 ==="
echo "1. kdump 服务: $(systemctl is-active kdump)"
echo "2. crash kernel 加载: $(cat /sys/kernel/kexec_crash_loaded)"
echo "3. crashkernel 参数: $(cat /proc/cmdline | tr ' ' '\n' | grep crashkernel)"
echo "4. sysrq 开关: $(cat /proc/sys/kernel/sysrq)"
echo "5. /var/crash 空间: $(df -h /var/crash/ 2>/dev/null | tail -1 | awk '{print $4}') 可用"
echo ""

# 检查所有条件
if [[ "$(systemctl is-active kdump)" == "active" ]] && \
   [[ "$(cat /sys/kernel/kexec_crash_loaded)" == "1" ]] && \
   [[ $(cat /proc/sys/kernel/sysrq) -ge 1 ]]; then
    echo "✓ 所有条件满足，可以进行 kdump 测试"
else
    echo "✗ 有条件不满足，请先修复"
fi
```

> ⚠️ **触发 panic 测试**（需用户手动执行，会导致系统立即 crash 并重启！）：
> ```bash
> # 确认要触发（这会导致系统立即崩溃！）
> echo 1 > /proc/sys/kernel/sysrq
> echo c > /proc/sysrq-trigger
> 
> # 重启后检查 vmcore
> ls -la /var/crash/
> ```
>
> **重要提醒**：
> - 执行 `echo c > /proc/sysrq-trigger` 会立即触发内核 panic！
> - 系统会完全不可用，直到 kdump 完成转储并重启
> - 请在业务低峰期、维护窗口内执行
> - 确保有 IPMI/BMC/VNC 等带外管理途径

### Q5: kdump.conf 常用配置怎么写？

```bash
# 查看当前有效配置
grep -v '^#' /etc/kdump.conf | grep -v '^$'

# 查看 kdump.conf 示例
cat /etc/kdump.conf
```

**常用配置模板**：

```ini
# --- 本地存储（最简单） ---
path /var/crash
core_collector makedumpfile -l --message-level 7 -d 31

# --- NFS 远程存储 ---
nfs 192.168.1.100:/export/crash
path /var/crash
core_collector makedumpfile -l --message-level 7 -d 31

# --- SSH 远程存储 ---
ssh user@192.168.1.100
path /var/crash
sshkey /root/.ssh/kdump_id_rsa
core_collector makedumpfile -l --message-level 7 -d 31

# --- dump 失败后的动作 ---
default reboot         # 失败后重启（推荐）
#default halt          # 失败后停机
#default poweroff      # 失败后关机
#default shell         # 失败后进入 shell（调试用）

# --- 指定 dump 目标分区 ---
#ext4 /dev/vda1
#xfs /dev/vdb1
#path /var/crash

# --- fence 相关（集群环境） ---
#fence_kdump_args -p 7410 -f auto -i 0
#fence_kdump_nodes node1 node2
```

**core_collector makedumpfile 参数说明**：
- `-l`：使用 lzo 压缩（推荐，速度快）
- `-c`：使用 zlib 压缩（压缩率高但慢）
- `-p`：使用 snappy 压缩
- `-d 31`：dump level（31 = 排除 zero/cache/private/free pages，最小最快）
- `-d 0`：完整 dump（最大最慢，调试需要完整 dump 时用）
- `--message-level 7`：输出详细进度信息

### Q6: vmcore 怎么分析？需要什么准备？

```bash
# 1. 确认 crash 工具是否安装
which crash && crash --version | head -1

# 2. 确认 kernel-debuginfo 是否安装
rpm -qa | grep kernel-debuginfo

# 3. 查看 vmlinux 路径
ls -la /usr/lib/debug/lib/modules/$(uname -r)/vmlinux 2>/dev/null

# 4. 找到 vmcore 文件
LATEST=$(ls -td /var/crash/*/ 2>/dev/null | head -1)
echo "最新 vmcore: ${LATEST}vmcore"
ls -lh "${LATEST}vmcore" 2>/dev/null

# 5. 查看 vmcore-dmesg（不需要 crash 工具）
cat "${LATEST}vmcore-dmesg.txt" 2>/dev/null | tail -100
```

> **安装分析工具**（需用户手动执行）：
> ```bash
> # 安装 crash 工具
> yum install crash
> 
> # 安装 kernel-debuginfo（需要和 vmcore 对应的内核版本）
> # 方法 1: 从 debuginfo 仓库安装
> debuginfo-install kernel-$(uname -r)
> 
> # 方法 2: 手动下载安装
> yum install kernel-debuginfo-$(uname -r) kernel-debuginfo-common-$(uname -r)
> 
> # 打开 vmcore
> crash /usr/lib/debug/lib/modules/$(uname -r)/vmlinux /var/crash/xxx/vmcore
> ```

### Q7: 怎么把 vmcore 转储到远程服务器？

```bash
# 检查当前远程转储配置
grep -E "^nfs|^ssh|^sshkey" /etc/kdump.conf

# 检查网络配置（kdump 环境需要网络）
grep -E "^kdump_pre|^kdump_post|^extra_modules|^net" /etc/kdump.conf
grep "^dracut_args" /etc/kdump.conf
```

> **配置 NFS 远程转储**（需用户手动执行）：
> ```bash
> # 编辑 kdump.conf
> # 添加:
> nfs 192.168.1.100:/export/crash
> path /var/crash
> 
> # 确保 NFS 可以挂载
> mount -t nfs 192.168.1.100:/export/crash /mnt/test
> 
> # 重建 kdump initramfs 并重启服务
> kdumpctl rebuild
> systemctl restart kdump
> ```

> **配置 SSH 远程转储**（需用户手动执行）：
> ```bash
> # 1. 生成专用密钥（无密码）
> ssh-keygen -t rsa -f /root/.ssh/kdump_id_rsa -N ""
> 
> # 2. 分发公钥
> ssh-copy-id -i /root/.ssh/kdump_id_rsa.pub user@remote-server
> 
> # 3. 编辑 kdump.conf
> ssh user@remote-server
> sshkey /root/.ssh/kdump_id_rsa
> path /var/crash
> 
> # 4. 重建并重启
> kdumpctl rebuild
> systemctl restart kdump
> ```

### Q8: softlockup/hung_task 时为什么没有 vmcore？

```bash
# 查看当前 panic 触发条件配置
echo "=== panic 触发条件 ==="
echo "panic_on_oops: $(sysctl -n kernel.panic_on_oops)"
echo "softlockup_panic: $(sysctl -n kernel.softlockup_panic)"
echo "hung_task_panic: $(sysctl -n kernel.hung_task_panic)"
echo "unknown_nmi_panic: $(sysctl -n kernel.unknown_nmi_panic 2>/dev/null || echo 'N/A')"
echo "panic_on_warn: $(sysctl -n kernel.panic_on_warn 2>/dev/null || echo 'N/A')"
echo ""

# softlockup 相关配置
echo "=== softlockup 配置 ==="
echo "softlockup_all_cpu_backtrace: $(sysctl -n kernel.softlockup_all_cpu_backtrace 2>/dev/null || echo 'N/A')"
echo "watchdog_thresh: $(sysctl -n kernel.watchdog_thresh 2>/dev/null || echo 'N/A')"
echo ""

# hung_task 相关配置
echo "=== hung_task 配置 ==="
echo "hung_task_timeout_secs: $(sysctl -n kernel.hung_task_timeout_secs 2>/dev/null || echo 'N/A')"
echo "hung_task_check_count: $(sysctl -n kernel.hung_task_check_count 2>/dev/null || echo 'N/A')"
```

**关键说明**：
- 默认情况下，softlockup 和 hung_task **不会触发 panic**，所以不会生成 vmcore
- 需要设置 `kernel.softlockup_panic=1` 和 `kernel.hung_task_panic=1` 才会在对应事件发生时触发 panic
- 同样，oops 默认也可能不触发 panic，需要 `kernel.panic_on_oops=1`

> **开启 panic 触发**（需用户手动执行）：
> ```bash
> # 临时生效
> sysctl -w kernel.softlockup_panic=1
> sysctl -w kernel.hung_task_panic=1
> sysctl -w kernel.panic_on_oops=1
> 
> # 永久生效
> cat >> /etc/sysctl.d/99-kdump-panic.conf << 'EOF'
> kernel.softlockup_panic = 1
> kernel.hung_task_panic = 1
> kernel.panic_on_oops = 1
> kernel.panic = 10
> EOF
> sysctl -p /etc/sysctl.d/99-kdump-panic.conf
> ```

### Q9: 如何只保留最近几个 vmcore？

```bash
# 查看现有 vmcore 占用的空间
echo "=== 现有 vmcore ==="
ls -lhd /var/crash/*/ 2>/dev/null
echo ""
du -sh /var/crash/*/ 2>/dev/null
echo ""
echo "总占用: $(du -sh /var/crash/ 2>/dev/null | awk '{print $1}')"
```

> **清理旧 vmcore 和设置自动清理**（需用户手动执行）：
> ```bash
> # 手动清理旧的 vmcore（保留最近 3 个）
> cd /var/crash
> ls -td */ | tail -n +4 | xargs rm -rf
> 
> # 设置 cron 自动清理（保留最近 5 个，每天检查）
> cat > /etc/cron.daily/kdump-cleanup << 'SCRIPT'
> #!/bin/bash
> CRASH_DIR="/var/crash"
> KEEP=5
> cd "$CRASH_DIR" 2>/dev/null || exit 0
> ls -td */ 2>/dev/null | tail -n +$((KEEP+1)) | xargs rm -rf 2>/dev/null
> SCRIPT
> chmod +x /etc/cron.daily/kdump-cleanup
> ```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及系统关键配置变更，AI 不会自动执行！**
> 
> 请用户根据诊断结果，自行判断是否需要执行以下操作。

### 1. 安装 kdump 相关包

```bash
# TencentOS 2/3 (yum)
yum install kexec-tools

# TencentOS 4 (dnf)
dnf install kexec-tools

# 安装 crash 分析工具
yum install crash
yum install kernel-debuginfo-$(uname -r)
```

### 2. 配置 crashkernel 参数

```bash
# 方法 1: 使用 grubby（推荐，TencentOS 3/4）
grubby --update-kernel=ALL --args="crashkernel=512M"

# 方法 2: 修改 /etc/default/grub
# 在 GRUB_CMDLINE_LINUX 中添加 crashkernel=512M
vim /etc/default/grub
# 然后重新生成 grub 配置
grub2-mkconfig -o /boot/grub2/grub.cfg

# 方法 3: TencentOS 2
# 编辑 /etc/default/grub，在 GRUB_CMDLINE_LINUX 中添加
# crashkernel=auto 或 crashkernel=256M
grub2-mkconfig -o /boot/grub2/grub.cfg

# 重启生效
reboot
```

### 3. 启用 kdump 服务

```bash
# 设置开机自启并启动
systemctl enable --now kdump

# 检查是否成功
systemctl status kdump
cat /sys/kernel/kexec_crash_loaded
```

### 4. 重建 kdump initramfs

```bash
# 修改 kdump.conf 后需要重建
kdumpctl rebuild
# 或
mkdumprd -f /boot/initramfs-$(uname -r)kdump.img

# 重启 kdump 服务
systemctl restart kdump
```

### 5. 配置 panic 触发条件

```bash
# 创建 sysctl 配置
cat > /etc/sysctl.d/99-kdump-panic.conf << 'EOF'
# oops 时触发 panic（建议开启）
kernel.panic_on_oops = 1
# softlockup 时触发 panic
kernel.softlockup_panic = 1
# hung_task 超时时触发 panic
kernel.hung_task_panic = 1
# panic 后 10 秒自动重启
kernel.panic = 10
# 启用 sysrq（用于测试）
kernel.sysrq = 1
EOF

sysctl -p /etc/sysctl.d/99-kdump-panic.conf
```

### 6. 触发 panic 测试

```bash
# ⚠️ 这会导致系统立即崩溃并重启！仅在维护窗口执行！
echo 1 > /proc/sys/kernel/sysrq
sync    # 先同步文件系统
echo c > /proc/sysrq-trigger

# 重启后检查
ls -la /var/crash/
systemctl status kdump
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看 kdump 状态 | `systemctl status kdump` |
| 查看是否 active | `systemctl is-active kdump` |
| 查看是否自启 | `systemctl is-enabled kdump` |
| 查看 crash kernel 是否加载 | `cat /sys/kernel/kexec_crash_loaded` |
| 查看 crashkernel 参数 | `cat /proc/cmdline \| grep crashkernel` |
| 查看 crash kernel 大小 | `cat /sys/kernel/kexec_crash_size` |
| 查看 crashkernel 预留 | `cat /proc/iomem \| grep "Crash kernel"` |
| 查看 kdump 配置 | `grep -v '^#' /etc/kdump.conf \| grep -v '^$'` |
| 查看 kdump 日志 | `journalctl -u kdump --no-pager` |
| 查看 kdump initramfs | `ls -la /boot/initramfs-*kdump*` |
| 查看 vmcore 目录 | `ls -la /var/crash/` |
| 查看最近的 vmcore | `ls -lhrt /var/crash/*/vmcore \| tail -5` |
| 查看 vmcore-dmesg | `cat /var/crash/最新目录/vmcore-dmesg.txt` |
| 查看 vmcore 大小 | `du -sh /var/crash/*/` |
| 查看 /var/crash 空间 | `df -h /var/crash/` |
| 查看 panic 参数 | `sysctl kernel.panic kernel.panic_on_oops` |
| 查看 softlockup 配置 | `sysctl kernel.softlockup_panic` |
| 查看 hung_task 配置 | `sysctl kernel.hung_task_panic` |
| 查看 sysrq 状态 | `cat /proc/sys/kernel/sysrq` |
| 查看 kexec-tools 版本 | `rpm -q kexec-tools` |
| 查看 crash 工具 | `crash --version` |
| 查看 debuginfo | `rpm -qa \| grep kernel-debuginfo` |
| 查看重启记录 | `last -x reboot \| head -10` |
| 估算 vmcore 大小 | `kdumpctl estimate` (TencentOS 3+) |

---

## 快速排查流程图

```
kdump 服务没起来？
├── kexec-tools 安装了吗？ → rpm -q kexec-tools
│   └── 没装 → yum install kexec-tools
├── crashkernel 参数配了吗？ → cat /proc/cmdline | grep crashkernel
│   └── 没配 → 添加 crashkernel 参数并重启
├── crash kernel 加载了吗？ → cat /sys/kernel/kexec_crash_loaded
│   ├── 0 → 预留内存不够或参数错误
│   └── 1 → 正常，检查其他问题
├── kdump initramfs 存在吗？ → ls /boot/initramfs-*kdump*
│   └── 不存在 → kdumpctl rebuild
└── 日志怎么说？ → journalctl -u kdump

crash 了但没有 vmcore？
├── kdump 在 crash 前是 active 吗？
│   └── 不是 → 说明 kdump 服务就没正常工作
├── crash kernel 已加载？ → cat /sys/kernel/kexec_crash_loaded
│   └── 是 0 → kdump 根本没准备好
├── 是真的 panic 了吗？
│   ├── softlockup → 看 kernel.softlockup_panic 是否 = 1
│   ├── hung_task → 看 kernel.hung_task_panic 是否 = 1
│   ├── oops → 看 kernel.panic_on_oops 是否 = 1
│   └── 可能不是 panic（掉电/watchdog/手动重启）
├── 磁盘空间够吗？ → df -h /var/crash/
│   └── 不够 → 清理空间或改存储路径
└── vmcore 路径对吗？ → grep path /etc/kdump.conf

crashkernel 参数怎么配？
├── 内存 ≤ 2GB → crashkernel=128M
├── 2~8GB → crashkernel=256M
├── 8~64GB → crashkernel=512M（推荐）
├── 64~256GB → crashkernel=768M
├── > 256GB → crashkernel=1G
└── TencentOS 3/4 → crashkernel=auto（推荐）

vmcore 怎么分析？
├── crash 工具装了吗？ → which crash
│   └── 没装 → yum install crash
├── debuginfo 装了吗？ → rpm -qa | grep kernel-debuginfo
│   └── 没装 → debuginfo-install kernel-$(uname -r)
├── vmlinux 在哪？ → ls /usr/lib/debug/lib/modules/$(uname -r)/vmlinux
└── 打开 vmcore → crash vmlinux /var/crash/xxx/vmcore
```

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3 | TencentOS 4 |
|------|-------------|-------------|-------------|
| kexec-tools 版本 | 2.0.15+ | 2.0.20+ | 2.0.25+ |
| kdump 配置文件 | /etc/kdump.conf | /etc/kdump.conf | /etc/kdump.conf |
| crashkernel 默认 | 需手动配置 | crashkernel=auto | crashkernel=auto |
| crashkernel=auto 最小内存 | 2GB | 2GB | 1GB |
| kdumpctl 工具 | 基础 | 完善（rebuild/estimate） | 完善 |
| makedumpfile | 基础 | 完善 | 完善 + zstd 压缩 |
| 远程转储 | NFS/SSH | NFS/SSH | NFS/SSH + 改进 |
| UEFI 支持 | 部分 | 完善 | 完善 |
| grub 工具 | grub2-mkconfig | grubby + grub2-mkconfig | grubby |
| kdump initramfs | mkdumprd | kdumpctl rebuild | kdumpctl rebuild |
| 日志 | /var/log/messages | journalctl -u kdump | journalctl -u kdump |

> **注意**：
> - TencentOS 2 上 `crashkernel=auto` 需要系统内存 ≥ 2GB 才会预留
> - TencentOS 4 的 makedumpfile 支持 zstd 压缩，dump 更快
> - 所有版本都支持本地和 NFS/SSH 远程转储
> - 升级内核后需要确保新内核的 kdump initramfs 已生成（`kdumpctl rebuild`）

## 相关技能

- **service-status**：systemd 服务状态管理
- **system-log**：系统日志分析
- **disk-space**：磁盘空间检查（vmcore 需要足够空间）
- **oom-killer**：OOM 分析（OOM 可能触发 panic）
- **memory-leak**：内存泄漏排查
