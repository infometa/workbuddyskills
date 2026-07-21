---
name: file-io-trace
description: 追踪和分析进程的文件 I/O 操作，包括查看进程打开的文件及 I/O 统计、追踪文件 I/O 系统调用、分析 I/O 吞吐量与频率、定位 I/O 密集操作、排查 I/O 延迟高的问题、块设备层 I/O 延迟分析等。
description_zh: 追踪和分析进程的文件 I/O 操作，包括查看进程打开的文件及 I/O 统计、追踪文件 I/O 系统调用、分析 I/O 吞吐量与频率、定位 I/O 密集操作、排查 I/O 延迟高的问题、块设备层 I/O 延迟分析等。
description_en: Trace and analyze process file I/O operations, including viewing open files and I/O statistics, tracing file I/O system calls, analyzing I/O throughput and frequency, locating I/O intensive operations, troubleshooting high I/O latency, and block device layer I/O latency analysis.
version: 1.0.0
---

# 进程文件 I/O 追踪

帮助追踪和分析进程的文件 I/O 操作，包括系统 IO 概览、进程 IO 定位、文件描述符分析、IO 系统调用追踪、IO 延迟分析等。

## 安全原则

> ⚠️ AI 只执行查询/诊断命令，**不自动执行**：kill 进程、修改内核参数（IO 调度器/预读等）、修改挂载选项、blktrace 长时间采集、修改安全设置。这些操作仅作为建议提供给用户手动执行。

## 适用场景

- 进程 IO 高 / iowait 高 / 磁盘繁忙
- 进程读写了哪些文件 / fd 泄漏
- 追踪文件 IO 系统调用
- IO 延迟高 / await 高
- IO 吞吐分析

## 诊断策略：分层递进

采用**先概览再深入**的策略，根据概览结果决定是否需要进一步分析，避免不必要的命令执行。

```
第 1 层：一键采集概览（必做）→ 脚本一次调用获取系统 IO + 进程 IO 全貌
第 2 层：针对性深入（按需）→ 根据第 1 层结果，对特定进程做 lsof/strace
第 3 层：高级追踪（按需）→ blktrace / bpftrace / perf（仅在延迟问题明确时）
```

### 第 1 层：一键采集概览（必做）

使用内置脚本一次性采集系统 IO 概览和进程 IO 排名。脚本路径相对于 skill 的 `scripts/` 目录。

**场景 A：用户未指定 PID（系统整体 IO 分析）**

```bash
# 将 scripts/file-io-trace.sh 上传到目标服务器后执行
bash file-io-trace.sh
```

脚本会输出：系统基本信息、磁盘设备和调度器、iostat 采样、dirty page 状态、进程 IO TOP 15、IO 延迟详情、块设备队列参数。

**场景 B：用户指定了 PID**

```bash
bash file-io-trace.sh <PID> [采集秒数]
```

脚本会额外输出：进程基本信息、`/proc/<PID>/io` 统计、fd 数量和使用率、lsof 文件列表、strace IO 系统调用统计。

> 脚本位于本 skill 的 `scripts/file-io-trace.sh`，需先上传至目标服务器再执行。

**分析脚本输出后的决策**：

| 脚本输出现象 | 结论 | 下一步 |
|-------------|------|--------|
| %util < 5%，iowait ≈ 0，无高 IO 进程 | IO 正常，无瓶颈 | 直接输出结论，结束 |
| %util > 70% 或 await 异常高 | 磁盘繁忙或延迟高 | 进入第 2 层定位进程 |
| 找到高 IO 进程但用户未指定 PID | 需要深入分析该进程 | 用场景 B 重新采集该 PID |
| strace 显示大量小 IO 或高错误率 | 应用 IO 模式问题 | 进入第 2 层详细追踪 |
| fd 使用率 > 80% | 可能存在 fd 泄漏 | 进入第 2 层 fd 分析 |

### 第 2 层：针对性深入（按需）

仅在第 1 层发现问题时执行。根据问题类型选择对应命令：

**2a. 进程 IO 详细追踪（strace）**

```bash
# 统计模式（推荐，开销小）
timeout 5 strace -p <PID> -e trace=open,openat,read,write,close,pread64,pwrite64 -c 2>&1

# 详细模式（看具体文件和耗时）
timeout 5 strace -p <PID> -e trace=read,write,pread64,pwrite64 -T -tt -y -s 64 2>&1 | tail -30
```

**strace 关键判断**：
- 高频 read/write + 小 buffer → 建议增大缓冲区
- open/openat 大量 ENOENT 错误 → 频繁打开不存在的文件
- 单次调用 > 100ms → IO 延迟问题

**2b. fd 泄漏排查**

```bash
# 持续观察 fd 变化（60 秒内每 5 秒采样）
for i in $(seq 1 12); do echo "$(date '+%H:%M:%S') fd=$(ls /proc/<PID>/fd 2>/dev/null | wc -l)"; sleep 5; done
```

fd 持续增长不下降 → 存在泄漏。

**2c. iowait 高但找不到进程**

```bash
# 检查内核 IO 线程
ps aux | grep -E "flush|jbd2|kswapd|kworker" | grep -v grep
# 检查 dirty page 回写
cat /proc/meminfo | grep -E "Dirty|Writeback"
cat /proc/vmstat | grep -E "nr_dirty|nr_writeback"
```

常见原因：jbd2（ext4 日志）、kswapd（内存回收）、flush（dirty page 刷写）、进程已退出。

### 第 3 层：高级追踪（按需）

仅在第 2 层无法定位根因时使用。需要 root 权限。

| 工具 | 适用场景 | 命令示例 |
|------|---------|---------|
| blktrace + btt | 块设备层延迟分段分析（D2C=设备慢, I2D=调度拥堵） | `timeout 5 blktrace -d /dev/<DEV> -o /tmp/trace && blkparse -i /tmp/trace -d /tmp/trace.bin && btt -i /tmp/trace.bin` |
| bpftrace | IO 延迟直方图、VFS 层追踪（TencentOS 3/4） | `timeout 5 bpftrace -e 'tracepoint:block:block_rq_issue { @start[args->dev, args->sector] = nsecs; } tracepoint:block:block_rq_complete /@start[args->dev, args->sector]/ { @usecs = hist((nsecs - @start[args->dev, args->sector]) / 1000); delete(@start[args->dev, args->sector]); }'` |
| perf trace | 低开销的 IO 系统调用追踪（生产环境优先） | `timeout 5 perf trace -p <PID> -e read,write,open,openat --duration 100 2>&1 \| tail -30` |

> 注意：blktrace 会产生大量数据，务必限制采集时间并及时清理（`rm -f /tmp/trace.blktrace.* /tmp/trace.bin`）。
> strace 有显著性能影响（2-10x 减速），生产环境优先用 perf trace 或 bpftrace。

## 结果输出格式

### 📊 系统 I/O 概览

| 指标 | 值 | 状态 |
|------|-----|------|
| 系统负载 | xxx | ✅/⚠️/❌ |
| iowait | xxx% | ✅/⚠️/❌ |
| 磁盘利用率(%util) | xxx% | ✅/⚠️/❌ |
| IO 延迟(await) | xxxms | ✅/⚠️/❌ |

### 🔍 I/O 高的进程

列出 IO 排名靠前的进程，包含 PID、进程名、读写字节数。

### ⏱️ I/O 延迟分析（如有异常）

列出各设备的 await/r_await/w_await/%util。

### 💡 诊断结论与建议

根据分析结果给出具体结论和可操作建议。

## 操作参考（仅供用户手动执行）

> 🛑 以下操作 AI 不会自动执行，由用户自行判断。

- **安装工具**：`yum/dnf install -y strace lsof sysstat iotop blktrace perf bpftrace`
- **调整 IO 调度器**：`echo "mq-deadline" > /sys/block/<DEV>/queue/scheduler`（SSD 建议 none/mq-deadline，HDD 建议 bfq/mq-deadline）
- **调整 IO 优先级**：`ionice -c 3 -p <PID>`（设为 idle 类）
- **调整 dirty page**：`sysctl -w vm.dirty_ratio=10 vm.dirty_background_ratio=5`
- **调整预读**：`echo 256 > /sys/block/<DEV>/queue/read_ahead_kb`（顺序读场景增大，随机读减小）

## 相关技能

- **fs-latency**：文件系统延迟分析
- **syscall-hotspot**：系统调用热点分析
- **disk-space**：磁盘空间排查
- **system-log**：系统日志排查
