---
name: tencentos-expert
description: "TencentOS Server 全栈运维诊断，根据用户的自然语言描述，自动识别需要的能力接口，查询能力实现，使用具体能力解决客户问题。覆盖磁盘空间/分区/文件系统/LVM/健康检测、网络连通性/丢包/延迟排查、CPU火焰图/系统调用热点/调度延迟/中断均衡/文件IO延迟/进程IO追踪分析、内存泄漏/OOM诊断、系统日志/服务管理/时间同步/软件包/软件源管理、kdump配置与故障排查、等保三级安全基线检查与加固、CVE漏洞查询、产品文档实时查询。共24项能力，渐进式按需加载。触发词：磁盘满、磁盘空间、分区、格式化、挂载、fstab、LVM、扩容、SMART、坏块、ping不通、端口不通、DNS、丢包、延迟、网络慢、RTT、火焰图、CPU热点、perf、系统调用、调度延迟、中断不均衡、软中断、文件IO慢、fsync慢、page cache、IO延迟、进程IO、iotop、内存泄漏、OOM、进程被杀、内存不足、日志、journalctl、dmesg、服务启动失败、systemctl、时间不对、NTP、chrony、时区、yum源、dnf、pip源、npm源、软件包版本、安全更新、CVE、kdump、vmcore、crashkernel、等保、安全加固、安全基线、TencentOS文档、版本信息、CentOS迁移。"
description_zh: "TencentOS 服务器运维诊断助手，排查磁盘/网络/CPU/内存/安全问题"
description_en: "TencentOS Server ops assistant for disk, network, CPU, memory & security diagnostics"
version: 2.0.1
---

# TencentOS Server 全栈运维诊断

覆盖 24 项运维能力，按需加载，不撑爆上下文。

## 工作流程

### Step 0: 安装依赖工具（首次执行）

当触发本 skill 时，**首先执行以下命令安装所有诊断工具依赖**（无论成功或失败，都继续执行后续步骤）：

```bash
# 性能分析工具
dnf install -y perf-prof perf bpftrace sysstat || true
# 网络诊断工具
dnf install -y tcpdump nettrace mtr ethtool iperf3 dropwatch || true
# 存储诊断工具
dnf install -y smartmontools nvme-cli fio blktrace iotop || true
# 内存与调试工具
dnf install -y valgrind bcc-tools gdb crash || true
# 系统调用与进程追踪
dnf install -y strace lsof cflow || true
# 系统服务工具
dnf install -y kexec-tools chrony || true
```

> **说明**：
> - 使用 `|| true` 确保即使部分包安装失败也不中断流程
> - 安装完成后继续执行 Step 1

### Step 1: 理解用户意图

分析用户的自然语言请求，从下方 **能力索引表** 中匹配 1~3 个最相关的模块。

**匹配策略**：
1. 先根据关键词缩小到大类（如"磁盘满" → 磁盘与存储）
2. 再在子模块中定位具体能力（如"磁盘满" → `disk-space`）
3. 如果用户意图模糊，选择最可能的模块并在诊断中确认

### Step 2: 加载模块详细文档

找到目标模块后，**必须先读取对应的 references/ 文件**，获取完整的诊断步骤和命令参考。

**加载方式**：
```
Read: references/<module-id>.md
```

例如用户问"磁盘空间不足"：
```
Read: references/disk-space.md
```

### Step 3: 执行诊断

按照模块文档中的诊断步骤执行。遵循以下通用原则：

#### 安全原则

> ⚠️ AI 只执行诊断命令（查看、分析），**不自动执行任何破坏性操作**。
>
> 涉及数据变更的操作（格式化、删除、重启服务、修改配置等）仅作为参考提供给用户，由用户自行判断和手动执行。

#### 通用信息收集（首次连接时执行一次）

```bash
uname -r && cat /etc/os-release | head -3
uptime && free -h
df -h | head -10
```

#### TencentOS 版本差异速查

| 操作 | TencentOS 2 | TencentOS 3/4 |
|------|-------------|---------------|
| 包管理器 | `yum` | `dnf`（`yum` 为别名） |
| 默认防火墙 | iptables | firewalld |
| 网络管理 | network-scripts | NetworkManager |
| NTP 服务 | ntpd | chronyd |
| 连接查看 | netstat | ss |
| 日志轮转 | cron 触发 | systemd timer |
| cgroup | v1 | v1(TS3) / v2(TS4) |
| 性能工具安装 | `yum install` | `dnf install` |

### Step 4: 输出结果

按照模块文档中定义的报告格式输出诊断结论和建议。

---

## 能力索引（24 项）

### 磁盘与存储（5 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `disk-space` | 磁盘空间分析与清理 | 磁盘满、空间不足、No space、inode、du、df、日志清理 | `references/disk-space.md` |
| `disk-partition` | 磁盘分区管理 | 分区、fdisk、parted、GPT、MBR、新磁盘 | `references/disk-partition.md` |
| `disk-filesystem` | 文件系统管理 | 格式化、挂载、fstab、fsck、mkfs、ext4、xfs | `references/disk-filesystem.md` |
| `disk-lvm` | LVM 逻辑卷管理 | LVM、扩容、lvextend、pvcreate、快照 | `references/disk-lvm.md` |
| `disk-health` | 磁盘健康检测 | SMART、坏块、磁盘寿命、NVMe、I/O error | `references/disk-health.md` |

### 网络（3 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `network-check` | 网络连通性诊断 | ping不通、端口不通、DNS、防火墙、路由、ssh连不上 | `references/network-check.md` |
| `network-latency` | 网络丢包与延迟 | 丢包、延迟高、RTT、网络慢、重传、ethtool、nettrace、网络抖动、TCP重传、Ring Buffer、softnet、conntrack满、conntrack table full、drop reason、eBPF网络诊断、报文跟踪、协议栈延迟、ping延迟正常但应用慢、传输速度慢、首次连接慢、ARP、拥塞窗口、BDP、TCP缓冲区、Nagle、偶发延迟、持续延迟、时段型延迟、网卡错误、rx dropped、吞吐低 | `references/network-latency.md`（主入口，自动路由到丢包/延迟子文件） |
| — | 丢包排查子文件 | Ring Buffer溢出、softnet backlog溢出、conntrack满、kfree_skb、dropwatch | `references/network-packet-loss.md` |
| — | 延迟排查子文件 | mtr逐跳、TCP拥塞恢复、bufferbloat、队列延迟、softirq积压、GRO、ARP解析延迟 | `references/network-latency-diag.md` |

### 性能分析（7 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `cpu-flamegraph` | CPU 火焰图 | 火焰图、CPU热点、perf-prof profile、调用栈、Java进程CPU高、JVM性能、JIT、进程CPU占用高、nginx热点、D状态、进程阻塞、task-state、dwarf栈回溯、内核态热点、用户态热点、kmalloc调用路径、缺页异常、flamegraph.pl、folded文件、SVG火焰图、优化前后对比、perf-prof安装、FlameGraph安装 | `references/cpu-flamegraph.md` |
| `syscall-hotspot` | 系统调用热点 | 系统调用慢、strace、perf trace、syscall、futex延迟、epoll_wait延迟、系统调用报错、errno、IO系统调用、进程hang住、系统调用频率、系统调用耗时 | `references/syscall-hotspot.md` |
| `sched-latency` | 进程调度延迟 | 调度延迟、rundelay、抢占、唤醒延迟、P99延迟毛刺、cgroup CPU限流、CPU quota、RD状态、NUMA调度、进程响应慢但CPU不高、容器变慢、调度延迟监控 | `references/sched-latency.md` |
| `irq-balance` | 中断均衡排查 | 软中断、硬中断、中断不均、ksoftirqd、RSS哈希不均、NET_RX集中、网络吞吐上不去、网卡队列、RPS、RFS、irqbalance、hrcount、softirqs、中断亲和性、ethtool队列配置 | `references/irq-balance.md` |
| `fs-latency` | 文件系统IO延迟 | 文件IO慢、fsync慢、page cache、ext4慢、t-ops | `references/fs-latency.md` |
| `file-io-trace` | 进程文件IO追踪 | 进程IO高、iowait、IO追踪、fd泄漏 | `references/file-io-trace.md` |
| `oom-killer` | OOM 事件诊断 | OOM、进程被杀、内存不足、oom-killer、cgroup内存限制、Memory cgroup out of memory、page allocation failure、kswapd、Swap耗尽、oom_score_adj、多进程内存竞争 | `references/oom-killer.md` |

### 内存（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `memory-leak` | 内存泄漏诊断 | 内存泄漏、RSS增长、内存不释放、memleak、VmRSS持续增长、VmAnon增长、Private_Dirty、Pss、SUnreclaim、内核slab泄漏、文件描述符泄漏、fd_count增长、内存碎片、Java堆泄漏、jmap、OOM预测 | `references/memory-leak.md` |

### 系统管理（5 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `system-log` | 系统日志分析 | 日志、journalctl、dmesg、报错、日志清理 | `references/system-log.md` |
| `service-status` | 服务状态管理 | 服务起不来、systemctl、启动失败、开机自启 | `references/service-status.md` |
| `time-sync` | 时间同步管理 | 时间不对、NTP、chrony、时区、时间同步 | `references/time-sync.md` |
| `package-version` | 软件包版本管理 | 软件版本、安全更新、升级、rpm、dnf | `references/package-version.md` |
| `repo-source` | 软件源配置 | yum源、dnf源、pip源、npm源、换源、镜像 | `references/repo-source.md` |

### 安全（2 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `security-baseline` | 等保三级安全加固 | 等保、安全加固、安全基线、GB/T 22239、身份鉴别、访问控制、安全审计、入侵防范、SELinux加固、SSH加固、密码策略、账户管理、防火墙配置、check模式、harden模式、R1高风险、安全检查 | `references/security-baseline.md` |
| `tencentos-cve-query` | CVE 漏洞查询 | CVE、漏洞、安全公告、TSSA、OCSA、OpenCloudOS安全公告、批量CVE查询、TS2漏洞、TS3漏洞、TS4漏洞、OC7漏洞、OC8漏洞、OC9漏洞 | `references/tencentos-cve-query.md` |

### 故障恢复（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `kdump-check` | kdump 配置与排查 | kdump、vmcore、crashkernel、panic、crash | `references/kdump-check.md` |

### 产品文档（1 项）

| 模块 ID | 能力 | 匹配关键词 | 文档路径 |
|---------|------|-----------|----------|
| `tencentos-docs` | 产品文档实时查询 | TencentOS版本、维护周期、CentOS迁移、产品特性 | `references/tencentos-docs.md` |

---

## 文档路径映射（完整）

| 模块 ID | references/ 路径 | scripts/ 路径 |
|---------|-----------------|---------------|
| disk-space | `references/disk-space.md` | — |
| disk-partition | `references/disk-partition.md` | — |
| disk-filesystem | `references/disk-filesystem.md` | — |
| disk-lvm | `references/disk-lvm.md` | — |
| disk-health | `references/disk-health.md` | — |
| network-check | `references/network-check.md` | — |
| network-latency | `references/network-latency.md` + `references/network-packet-loss.md` + `references/network-latency-diag.md` + `references/network-nettrace.md` + `references/network-faq-latency.md` + `references/network-faq-packet-loss.md` | `scripts/network-latency-monitor.sh` |
| cpu-flamegraph | `references/cpu-flamegraph.md` + `references/cpu-flamegraph-perf.md` + `references/flamegraph-install.md` | — |
| syscall-hotspot | `references/syscall-hotspot.md` | — |
| sched-latency | `references/sched-latency.md` | `scripts/sched-latency-monitor.sh` |
| irq-balance | `references/irq-balance.md` + `references/irq-balance-perf.md` | — |
| fs-latency | `references/fs-latency.md` | `scripts/fs-latency-collect.sh`, `scripts/install-deps.sh` |
| file-io-trace | `references/file-io-trace.md` | `scripts/file-io-trace.sh` |
| oom-killer | `references/oom-killer.md` + `references/oom-kernel-patterns.md` + `references/oom-metrics-guide.md` | `scripts/collect_and_analyze.sh`, `scripts/parse_oom_events.py` |
| memory-leak | `references/memory-leak.md` + `references/memory-leak-indicators.md` | `scripts/collect_memory_leak.sh`, `scripts/parse_memory_leak.py` |
| system-log | `references/system-log.md` | — |
| service-status | `references/service-status.md` | — |
| time-sync | `references/time-sync.md` | — |
| package-version | `references/package-version.md` | — |
| repo-source | `references/repo-source.md` | — |
| security-baseline | `references/security-baseline.md` + `references/security-checklist.md` | `scripts/tos_security_harden.sh` |
| tencentos-cve-query | `references/tencentos-cve-query.md` | `scripts/cve_xml_server.py`, `scripts/opencloudos_api_server.py`, `scripts/requirements.txt` |
| kdump-check | `references/kdump-check.md` | — |
| tencentos-docs | `references/tencentos-docs.md` | — |

---

## 场景快速导航（按问题现象路由）

当用户描述问题现象而非直接使用关键词时，用下表定位模块：

| 问题现象 | 首选模块 | 备选模块 |
|---------|---------|---------|
| 服务 CPU 跑满，不知道热点在哪 | `cpu-flamegraph` | — |
| Java/Python/Node.js 进程 CPU 高 | `cpu-flamegraph`（加载 guide 中 Java 案例）| — |
| 进程卡住不动，ps 看到 D 状态 | `cpu-flamegraph`（task-state 分析器）| `fs-latency` |
| 某个 CPU 的 %soft 持续偏高，其他 CPU 空闲 | `irq-balance` | — |
| 网络吞吐上不去，但整体 CPU 还有余量 | `irq-balance` | `network-latency` |
| ping 延迟正常，但应用响应慢 | `network-latency`（延迟域 Module 3/6）| `syscall-hotspot` |
| 网络延迟偶尔飙高，平时正常 | `network-latency`（偶发型 M-2）| `sched-latency` |
| TCP 重传率高 | `network-latency`（延迟域）| — |
| 连接跟踪表满，新连接被丢弃 | `network-latency`（丢包域 Module 6）| — |
| 进程响应变慢，但 CPU/内存不高 | `sched-latency` | `syscall-hotspot` |
| 容器 P99 延迟飙高，CPU 使用率正常 | `sched-latency`（cgroup CPU quota）| — |
| 某接口延迟 P99/max 偶发异常高 | `syscall-hotspot`（futex/epoll_wait 毛刺）| `sched-latency` |
| 可用内存持续下降，进程内存不释放 | `memory-leak` | — |
| Java 进程内存高，GC 后不回落 | `memory-leak`（JVM 堆泄漏场景）| `oom-killer` |
| 进程突然被杀，不知道为什么 | `oom-killer` | — |
| cgroup 内容器内 OOM，但宿主机内存充足 | `oom-killer`（cgroup OOM 场景）| — |

---

## 文档完整导航地图

所有 references/ 文件的职责和加载时机，确保每个文件都有明确的到达路径：

### 主诊断文档（直接由能力索引触发）

| 文件 | 职责 | 触发时机 |
|------|------|---------|
| `disk-space.md` | 磁盘空间分析与清理完整流程 | 磁盘满、inode 不足 |
| `disk-partition.md` | 分区创建/管理流程 | 新磁盘、分区扩容 |
| `disk-filesystem.md` | 文件系统格式化/挂载/修复 | mkfs、fsck、fstab 问题 |
| `disk-lvm.md` | LVM 逻辑卷操作 | 扩容、快照、pvresize |
| `disk-health.md` | SMART 检测、坏块扫描 | 磁盘故障预测 |
| `network-check.md` | 连通性逐层排查 | ping 不通、端口不通 |
| `network-latency.md` | 丢包与延迟诊断入口（含路由规则）| 丢包、延迟高 |
| `cpu-flamegraph.md` | 火焰图采样与生成主流程 | CPU 热点、火焰图 |
| `syscall-hotspot.md` | 系统调用采集与分析主流程 | 系统调用慢、strace |
| `sched-latency.md` | 调度延迟采集与分析主流程 | 调度延迟、唤醒延迟 |
| `irq-balance.md` | 中断均衡诊断主流程 | 软中断不均、NET_RX 集中 |
| `fs-latency.md` | 文件系统 IO 延迟诊断 | fsync 慢、ext4 慢 |
| `file-io-trace.md` | 进程 IO 追踪 | 进程 IO 高、fd 泄漏 |
| `oom-killer.md` | OOM 事件分析主流程 | 进程被杀、内存不足 |
| `memory-leak.md` | 内存泄漏诊断主流程 | RSS 增长、内存不释放 |
| `system-log.md` | 系统日志分析 | dmesg 报错、journalctl |
| `service-status.md` | 服务状态与启动排查 | systemctl 失败 |
| `time-sync.md` | 时间同步配置与排查 | 时间不对、NTP |
| `package-version.md` | 软件包版本与更新管理 | 升级、安全更新 |
| `repo-source.md` | 软件源配置与切换 | yum 源、换源 |
| `security-baseline.md` | 等保三级检查与加固主流程 | 等保、安全加固 |
| `tencentos-cve-query.md` | CVE 查询主流程（路由到 MCP 或 Fallback）| CVE、漏洞查询 |
| `kdump-check.md` | kdump 配置与排查 | kdump、vmcore |
| `tencentos-docs.md` | 产品文档查询 | TencentOS 版本、迁移 |

### 子流程/工具参考文档（由主文档内部导航触发）

| 文件 | 职责 | 触发时机 |
|------|------|---------|
| `network-packet-loss.md` | 丢包域完整诊断流程（Module 1~7）| `network-latency.md` 路由到丢包场景 |
| `network-latency-diag.md` | 延迟域完整诊断流程（Module 1~6）| `network-latency.md` 路由到延迟场景 |
| `network-nettrace.md` | nettrace 工具完整用法参考 | 需要 nettrace 丢包监控/故障诊断/延迟分析时 |
| `network-faq-latency.md` | 延迟域 FAQ + 操作参考 + 命令速查 | 延迟诊断中需要 FAQ 解答或配置参考时 |
| `network-faq-packet-loss.md` | 丢包域 FAQ + 操作参考 + 命令速查 | 丢包诊断中需要 FAQ 解答或配置参考时 |
| `cpu-flamegraph-guide.md` | 火焰图使用指南（含 Java/D状态案例）| 需要用户友好的操作指引，或遇到 Java/D状态场景 |
| `cpu-flamegraph-perf.md` | perf 原生三步生成法（高级用户）| perf-prof 不可用时的降级方案 |
| `cpu-flamegraph-examples.md` | 常用触发场景示例 Prompt | 用户描述的场景不易直接匹配关键词时参考 |
| `flamegraph-install.md` | FlameGraph 工具安装指南 | 用户需要安装 flamegraph.pl 时 |
| `irq-balance-guide.md` | 中断均衡六步排查指南（含案例）| 需要用户友好的操作指引 |
| `irq-balance-perf.md` | perf-prof 中断分析命令参考 | 执行 hrcount/multi-trace/profile 命令时 |
| `irq-balance-examples.md` | 中断均衡场景示例 | 场景匹配参考 |
| `sched-latency-guide.md` | 调度延迟使用指南（含案例）| 需要用户友好的操作指引，或 cgroup 限流场景 |
| `syscall-hotspot-guide.md` | 系统调用分析使用指南（含案例）| 需要用户友好的操作指引，或 epoll/futex 场景 |
| `memory-leak-indicators.md` | 内存泄漏判定指标知识库 | 分析 VmRSS/VmAnon/SUnreclaim 等指标时 |
| `memory-leak-guide.md` | 内存泄漏排查指南 | 需要用户友好的操作指引 |
| `oom-kernel-patterns.md` | OOM 日志特征库与根因分类 | 解析 dmesg OOM 日志时 |
| `oom-metrics-guide.md` | OOM 诊断指标说明 | 分析内存指标与 OOM 关联时 |
| `security-baseline-guide.md` | 等保加固概述（37项/双模式/风险分级）| 用户需了解加固范围或使用方式时 |
| `security-checklist.md` | 安全检查项清单 | check 模式执行时比对参考 |

---

## 重要注意事项

1. **不要一次性加载所有 references/**——只加载用户问题匹配的 1~3 个模块文档
2. **脚本路径替换规则**：文档中出现 `<SKILL_DIR>` 的地方，替换为本 skill 目录的实际绝对路径（即 `SKILL.md` 所在目录）
3. **perf-prof 优先**：性能分析类模块优先使用 perf-prof，不可用时按文档中的降级方案使用 perf 原生命令
4. **索引中找不到匹配时**：可用 Grep 在 references/ 目录中搜索用户描述的关键词
5. **多个模块关联时**：按主要问题加载主模块，相关模块的文档路径在每个模块末尾的"相关技能"中列出

