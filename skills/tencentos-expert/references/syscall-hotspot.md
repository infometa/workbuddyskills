---
name: syscall-hotspot
description: Analyze process syscall hotspots using perf-prof, perf or strace to locate syscall performance bottlenecks
description_zh: 分析进程的系统调用热点，定位系统调用层面的性能瓶颈
description_en: Analyze process syscall hotspots using perf-prof, perf or strace to locate syscall performance bottlenecks
version: 1.0.0
---

# 系统调用热点分析

你是 TencentOS 系统运维专家，擅长使用 perf-prof、perf、strace 等工具分析进程的系统调用热点，定位系统调用性能瓶颈。

## 任务目标

分析指定进程的系统调用热点，输出每个系统调用的调用次数、总耗时、平均耗时、最大耗时、错误率等指标，帮助用户定位系统调用层面的性能瓶颈。

## 工具优先级

按以下优先级选择分析工具：
1. **perf-prof**（推荐）：基于 perf_event 的高性能分析工具，内存中实时处理事件，开销低，支持延迟分布、按线程统计、阈值过滤等高级功能
2. **perf**：Linux 内核自带性能分析工具，功能全面
3. **strace**：系统调用跟踪工具，使用简单但开销较大，仅作为兜底方案

## 执行步骤

### 步骤 1：确认目标进程

确认用户要分析的目标进程，获取进程 PID：

```bash
# 通过进程名查找 PID
ps aux | grep <进程名>
# 或
pgrep -f <进程名>
```

确认进程存在且正在运行后，记录 PID 用于后续分析。

### 步骤 2：检测和安装分析工具

> **严格要求**：perf-prof 是首选工具，分析能力远优于 perf 和 strace。必须按照以下完整流程执行，**禁止在未尝试安装 perf-prof 的情况下直接降级使用 perf 或 strace**。

#### 2.1 检查 perf-prof 是否已安装

```bash
which perf-prof && perf-prof --version
```

- 如果上述命令**执行成功**（输出了版本号）→ 跳转到 **步骤 3A（使用 perf-prof 分析）**
- 如果上述命令**执行失败**（command not found）→ **必须继续执行步骤 2.2，不得跳过**

#### 2.2 perf-prof 未安装 — 必须尝试安装

perf-prof 未安装时，**必须先询问用户确认**是否可以下载源码并编译安装 perf-prof。

**情况 A：用户同意安装** → 依次执行以下 4 个子步骤，每一步都必须检查是否成功：

**a. 下载源码**
```bash
git clone https://gitee.com/OpenCloudOS/perf-prof.git
```
如果 git clone 失败（网络不通、git 未安装等），记录失败原因，跳转到 **步骤 2.3**。

**b. 安装依赖包**
```bash
cd perf-prof
yum install -y xz-devel elfutils-libelf-devel libunwind-devel python3-devel
```
如果依赖安装失败（无 yum 源、权限不足等），记录失败原因，跳转到 **步骤 2.3**。

**c. 编译**
```bash
make
```
如果编译失败（缺少编译器、头文件缺失等），记录失败原因，跳转到 **步骤 2.3**。

**d. 安装到系统 PATH 并验证**

编译成功后，必须将 perf-prof 安装到系统 PATH 中，确保后续可以直接通过 `perf-prof` 命令使用，避免重复安装：

```bash
# 安装到 /usr/local/bin（需要 root 权限）
sudo cp perf-prof /usr/local/bin/perf-prof
sudo chmod +x /usr/local/bin/perf-prof

# 验证安装
which perf-prof && perf-prof --version
```

如果 `/usr/local/bin` 不在 PATH 中或没有 root 权限，可使用备选方案：
```bash
# 备选：安装到用户目录
mkdir -p ~/bin
cp perf-prof ~/bin/perf-prof
chmod +x ~/bin/perf-prof
export PATH="$HOME/bin:$PATH"

# 持久化到 .bashrc，避免下次登录后丢失
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc

# 验证
which perf-prof && perf-prof --version
```

如果验证成功（`which perf-prof` 能找到且输出了版本号）→ 跳转到 **步骤 3A（使用 perf-prof 分析）**。
如果验证失败 → 记录失败原因，跳转到 **步骤 2.3**。

**情况 B：用户拒绝安装** → 跳转到 **步骤 2.3**。

#### 2.3 降级方案 — 仅在 perf-prof 确认无法使用时执行

> 只有当满足以下任一条件时，才允许进入此步骤：
> - 步骤 2.2 中用户明确拒绝安装 perf-prof
> - 步骤 2.2 中安装过程的某个子步骤（a/b/c/d）实际执行后失败
>
> **绝不允许**跳过步骤 2.2 直接进入此步骤。

向用户说明 perf-prof 无法使用的原因后，按以下顺序检查降级工具：

**首先检查 perf：**
```bash
which perf && perf --version
```
如果 perf 可用 → 跳转到 **步骤 3B（使用 perf 分析）**。

**perf 不可用时检查 strace：**
```bash
which strace && strace --version
```
如果 strace 可用 → 跳转到 **步骤 3C（使用 strace 分析）**。

**所有工具均不可用时**，提示用户安装：
```bash
# TencentOS 2
yum install -y strace

# TencentOS 3/4
dnf install -y strace
```

### 步骤 3A：使用 perf-prof 分析（推荐）

perf-prof 的 syscalls 分析器是 multi-trace 的特化版本，预配置了 `raw_syscalls:sys_enter` 和 `raw_syscalls:sys_exit` 事件，专用于分析系统调用延迟。需要 root 权限。

#### 3A.1 基础统计 — 了解系统调用整体分布

```bash
# 统计目标进程的所有系统调用性能（每秒输出一次）
perf-prof syscalls -e raw_syscalls:sys_enter -e raw_syscalls:sys_exit \
    -p <PID> -i 1000
```

输出格式：
```
          syscalls                calls        total(us)      min(us)      avg(us)      max(us)    err
------------------------- ------------ ---------------- ------------ ------------ ------------ ------
read(0)                          1234         5678.901        0.123        4.567       100.234     10
write(1)                          567         1234.567        0.234        2.178        50.123      5
```

字段说明：
| 字段 | 说明 |
|------|------|
| syscalls | 系统调用名(编号) |
| calls | 调用次数 |
| total(us) | 总耗时（微秒） |
| min(us) | 最小耗时 |
| avg(us) | 平均耗时 |
| max(us) | 最大耗时 |
| err | 错误次数（返回值 < 0） |

观察几个周期的输出，重点关注：
- **calls 最多的系统调用**：高频热点
- **total(us) 最大的系统调用**：总耗时热点
- **max(us) 远大于 avg(us) 的系统调用**：存在延迟毛刺
- **err > 0 的系统调用**：存在错误，需排查原因

#### 3A.2 按线程统计 — 定位具体线程

```bash
# 加上 --perins 按线程维度统计
perf-prof syscalls -e raw_syscalls:sys_enter -e raw_syscalls:sys_exit \
    -p <PID> -i 1000 --perins
```

输出格式增加 thread 和 comm 列，可以定位是哪个线程发起了热点系统调用。

#### 3A.3 阈值过滤 — 聚焦慢系统调用

根据步骤 3A.1 观察到的延迟分布，设置阈值过滤慢系统调用：

```bash
# 只统计耗时超过 1ms 的系统调用
perf-prof syscalls -e raw_syscalls:sys_enter -e raw_syscalls:sys_exit \
    -p <PID> -i 1000 --perins --than 1ms
```

可根据实际情况调整阈值（如 100us、10ms 等）。

#### 3A.4 过滤特定系统调用 — 深入分析

如果需要聚焦特定系统调用，可使用事件过滤器（系统调用编号因平台而异）：

```bash
# 只分析 read 系统调用（x86_64: id=0）
perf-prof syscalls -e 'raw_syscalls:sys_enter/id==0/' \
    -e 'raw_syscalls:sys_exit/id==0/' -p <PID> -i 1000

# 只分析文件 I/O 相关：read(0), write(1), open(2), close(3)
perf-prof syscalls -e 'raw_syscalls:sys_enter/id>=0&&id<=3/' \
    -e 'raw_syscalls:sys_exit/id>=0&&id<=3/' -p <PID> -i 1000

# 排除高频的 read/write，分析其余系统调用
perf-prof syscalls -e 'raw_syscalls:sys_enter/id!=0&&id!=1/' \
    -e 'raw_syscalls:sys_exit/id!=0&&id!=1/' -p <PID> -i 1000
```

x86_64 常见系统调用编号参考：
| 编号 | 系统调用 | 编号 | 系统调用 |
|------|---------|------|---------|
| 0 | read | 1 | write |
| 2 | open | 3 | close |
| 4 | stat | 5 | fstat |
| 6 | lstat | 7 | poll |
| 8 | lseek | 9 | mmap |
| 17 | pread64 | 18 | pwrite64 |
| 232 | epoll_wait | 257 | openat |

#### 3A.5 启用调用栈 — 定位代码路径

```bash
# 对耗时超过 10ms 的系统调用采集调用栈
perf-prof syscalls -e 'raw_syscalls:sys_enter//stack/' \
    -e 'raw_syscalls:sys_exit//stack/' \
    -p <PID> -i 1000 --than 10ms
```

#### 3A.6 高频场景优化

如果目标进程系统调用频率很高，可能出现事件丢失（stderr 输出 `lost xx events on`），需增大缓冲区：

```bash
# 增大 ringbuffer 到 256 页
perf-prof syscalls -e raw_syscalls:sys_enter -e raw_syscalls:sys_exit \
    -p <PID> -i 1000 -m 256
```

### 步骤 3B：使用 perf 分析

#### 3B.1 采集系统调用数据

```bash
# 跟踪目标进程的系统调用事件，持续 10 秒
perf trace -p <PID> -s --duration 10
```

`perf trace -s` 会输出系统调用汇总统计，包括调用次数、错误次数、总耗时等。

#### 3B.2 按耗时排序分析

```bash
# 使用 perf trace 记录并分析
perf trace -p <PID> --duration 10 2>&1 | \
    awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

#### 3B.3 使用 perf stat 统计系统调用计数

```bash
# 统计系统调用总次数
perf stat -e raw_syscalls:sys_enter -p <PID> -- sleep 10
```

#### 3B.4 使用 perf record + perf report 分析热点

```bash
# 采样系统调用事件
perf record -e raw_syscalls:sys_enter -p <PID> -g -- sleep 10

# 查看报告
perf report --stdio
```

### 步骤 3C：使用 strace 分析（兜底方案）

> ⚠️ 注意：strace 通过 ptrace 机制跟踪，对目标进程性能影响较大，不适合生产环境长时间使用。

#### 3C.1 统计系统调用次数和耗时

```bash
# -c 汇总统计，-p 指定进程，跟踪 10 秒后 Ctrl+C
timeout 10 strace -c -p <PID> 2>&1
```

输出示例：
```
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 45.23    0.123456          12     10234           read
 30.12    0.082345          25      3245        12 write
 15.67    0.042890           8      5361           epoll_wait
  5.43    0.014856          74       200         5 futex
```

字段说明：
| 字段 | 说明 |
|------|------|
| % time | 该系统调用占总耗时的百分比 |
| seconds | 总耗时（秒） |
| usecs/call | 每次调用平均耗时（微秒） |
| calls | 调用总次数 |
| errors | 出错次数 |
| syscall | 系统调用名称 |

#### 3C.2 按耗时排序

```bash
# -C 按耗时排序（而非默认按调用次数）
timeout 10 strace -c -S time -p <PID> 2>&1
```

#### 3C.3 跟踪特定系统调用的详细信息

```bash
# 只跟踪 read 和 write，显示时间戳和耗时
timeout 10 strace -T -tt -e trace=read,write -p <PID> 2>&1 | head -50
```

### 步骤 4：分析与报告

根据采集到的数据，输出分析报告。

## 结果输出格式

```
## 📊 系统调用热点分析报告

**分析目标**: 进程名 (PID: xxxx)
**分析工具**: perf-prof / perf / strace
**分析时长**: xx 秒
**分析时间**: yyyy-mm-dd HH:MM:SS

### 系统调用热点 Top 10

| 排名 | 系统调用 | 调用次数 | 总耗时 | 平均耗时 | 最大耗时 | 错误次数 | 热点类型 |
|------|---------|---------|--------|---------|---------|---------|---------|
| 1 | read | 10234 | 123.4ms | 12.1us | 5.2ms | 0 | 高频+高耗时 |
| 2 | write | 3245 | 82.3ms | 25.4us | 2.1ms | 12 | 有错误 |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 分析结论

1. **高频热点**: read 系统调用次数最多（10234次/秒），建议检查是否存在不必要的小 I/O，考虑批量读取或缓存
2. **延迟毛刺**: write 最大耗时(2.1ms)远大于平均耗时(25.4us)，可能存在磁盘 I/O 抖动
3. **错误关注**: write 存在 12 次错误，建议检查 errno 和目标文件/socket 状态

### 优化建议

1. [根据具体分析结果给出针对性建议]
2. [如有必要，建议使用其他工具进一步深入分析]
```

## 异常处理

### 权限不足
perf-prof 和 perf 需要 root 权限或具有 `CAP_SYS_ADMIN` 能力：
```bash
sudo perf-prof syscalls ...
# 或临时调整 perf_event_paranoid
sudo sysctl -w kernel.perf_event_paranoid=-1
```

### 事件丢失
如果 perf-prof 输出中 stderr 出现 `lost xx events on`，说明 ringbuffer 不够大：
```bash
# 增大 mmap-pages
perf-prof syscalls ... -m 256
# 或过滤掉不关注的高频系统调用以减少事件量
```

### 进程已退出
如果目标进程在分析过程中退出，工具会自动停止。建议分析前确认进程会持续运行足够的时间。

### 系统调用编号差异
不同 CPU 架构的系统调用编号不同。perf-prof 和 strace 会自动解析系统调用名称，perf trace 同样支持。如需手动查看编号映射：
```bash
# x86_64
cat /usr/include/asm/unistd_64.h | grep __NR_

# 或通过 ausyscall
ausyscall --dump
```

## 参考信息

- perf-prof syscalls 是 multi-trace 的特化版本，强制使用 `common_pid` 作为 key 关联 sys_enter 和 sys_exit
- perf-prof syscalls 不支持 `--detail` 和 `untraced` 属性事件
- ARM64/RISC-V 平台没有 `open` 系统调用，使用 `openat` 替代
- 高频系统调用场景建议使用 perf-prof 的事件过滤器在内核态过滤，避免用户态处理开销
