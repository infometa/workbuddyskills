---
name: memory-leak
description: 诊断 Linux 用户态内存泄漏问题. 通过对进程 RSS/PSS 进行多次采样，计算内存增长速率，判定是否存在内存泄漏，并预测 OOM 触发时间. 支持指定进程名/PID 单进程监控，也支持全局扫描找出内存增长最快的进程.
description_zh: 内存泄漏诊断（用户态进程 RSS/PSS 多次采样分析）
description_en: Diagnose Linux user-space memory leaks via RSS/PSS sampling and growth rate analysis
version: 1.1.0
---

# 内存泄漏诊断

诊断 Linux 用户态内存泄漏问题，通过对进程内存进行多次采样，计算 RSS/PSS 增长速率，判定是否存在内存泄漏，并预测 OOM 触发时间.

## 安全原则

> ⚠️ **重要**：本 Skill 只执行查询/采集操作（读取 /proc、运行 ps），**不自动执行以下操作**：
>
> - 不自动 kill 或重启任何进程
> - 不自动调整 vm.overcommit_memory 等内核参数
> - 不自动安装 bcc-tools 或其他工具
> - 不自动修改进程的 oom_score_adj
>
> 以上操作仅在报告中作为建议提供，由用户自行判断后手动执行.

---

## 适用场景

### 用户可能的问题表述

**内存泄漏直接表述**：
- "我们的服务内存泄漏了"、"memory leak 怎么排查"
- "进程有内存泄露"、"堆内存一直增长"
- "帮我看看有没有内存泄漏"

**进程内存持续增长**：
- "Java 进程内存一直在涨"、"nginx 内存越来越大"
- "进程内存持续增长，怎么排查"、"RSS 一直在涨"
- "内存占用越来越高，不知道什么原因"
- "内存缓慢增长，怀疑有泄漏"

**内存不释放**：
- "进程内存不释放"、"内存没有归还给系统"
- "进程重启后内存才降下来"、"内存增长后不回落"

**查找泄漏进程**：
- "帮我找出哪个进程在泄漏内存"
- "机器内存一直在减少，找找原因"
- "哪个进程内存增长最快"

---

## 目录结构

```
memory-leak/
├── SKILL.md                              # 本文件
├── skill.yaml                            # 元信息（名称、触发词、依赖等）
├── OWNERS                                # 负责人
├── references/
│   └── memory-leak-indicators.md        # 内存泄漏判定知识库（指标、规则、场景）
├── scripts/
│   ├── collect_memory_leak.sh           # 数据采集入口脚本
│   └── parse_memory_leak.py             # 解析脚本（增长速率计算 + 泄漏判定 + OOM 预测）
└── tests/
    └── test.sh                          # 格式验证与脚本语法测试
```

---

## 前置条件

**可选参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| process_name | string | 否 | (空) | 指定进程名，模糊匹配（如 java、nginx） |
| pid | int | 否 | (空) | 指定 PID，优先于 process_name |
| monitor_count | int | 否 | 6 | 采样次数（建议 ≥ 3） |
| monitor_interval | int | 否 | 10 | 采样间隔（秒） |
| top_n | int | 否 | 5 | 全局扫描时显示 RSS 增长 Top N 进程 |

**监控模式**：
- 指定 `pid` 或 `process_name` → 单进程监控模式
- 两者均不指定 → 全局扫描模式，自动找出 RSS 增长最快的 Top N 进程

**依赖工具**：
- `python3`：解析采样数据（必需）
- `ps`、`cat`：采集进程信息（必需，系统自带）
- `memleak`（bcc-tools）：eBPF 调用栈追踪（可选，需安装）

---

## Workflow

### Step 0：确定监控目标

- **指定 pid**：直接监控该 PID
- **指定 process_name**：用 `ps aux` 查找匹配进程，取 RSS 最大的那个
- **两者都不指定**：全局扫描模式，监控所有 RSS > 1MB 的进程

无需向用户询问，直接执行.

### Step 1：多次采样

以 `monitor_interval` 为间隔，执行 `monitor_count` 次采样：

```bash
# 单进程模式：读取 /proc/<pid>/status 和 smaps_rollup
cat /proc/<pid>/status     # VmRSS、VmAnon、VmPeak、VmSize
cat /proc/<pid>/smaps_rollup  # Pss、Private_Dirty（更准确）
ls /proc/<pid>/fd | wc -l  # 文件描述符数量

# 全局模式：获取所有进程 RSS
ps -eo pid,rss,comm --no-headers | awk '$2 > 1024'
```

同时采集辅助信息（仅一次）：
- `/proc/meminfo`：全局内存状态（供 OOM 预测用）
- `/proc/slabinfo`：内核 slab 内存（检测内核对象泄漏）
- `dmesg | grep -i oom`：确认是否已发生 OOM

采样结束后调用 `scripts/collect_memory_leak.sh` 自动完成上述过程.

### Step 2：增长速率计算与泄漏判定

调用 `scripts/parse_memory_leak.py` 分析采样数据：

**增长速率计算**：
```
growth_rate_kb_per_min = (rss_last - rss_first) / elapsed_minutes
growth_pct_per_min     = growth_rate_kb_per_min / rss_first × 100
```

**泄漏判定规则**（详见 `references/memory-leak-indicators.md`）：

| 结论 | 条件 |
|------|------|
| `leak_confirmed`（确认泄漏） | growth_pct_per_min > 2% 或（> 1% 且 RSS 单调递增） |
| `leak_suspected`（疑似泄漏） | growth_pct_per_min 1%~2%，或绝对增量 > 50MB 且单调 |
| `normal`（正常波动） | growth_pct_per_min ≤ 1% 且无单调增长 |
| `insufficient_data`（数据不足） | 采样次数 < 2 或监控时长 < 30s |
| `process_disappeared`（进程中途退出） | 监控期间目标进程消失 |

**OOM 预测**：
```
oom_eta_minutes = MemAvailable / growth_rate_kb_per_min
```

**趋势分析**（二阶导数）：
- `accelerating`（加速）→ 泄漏在恶化，需立即处置
- `decelerating`（减速）→ 增长趋稳，可能是业务峰值已过
- `linear`（线性）→ 匀速增长，持续监控

**辅助检查**：
- fd_count > 5000 → 告警：可能存在文件描述符泄漏
- SUnreclaim > 500MB → 告警：内核 slab 对象泄漏

**eBPF 调用栈**（可选）：若 `memleak` 可用且为单进程模式，自动运行 30 秒采集未释放内存的调用栈，精准定位泄漏代码行.

### Step 3：输出诊断报告

严格使用下方报告模板输出，**处置建议必须结合本次采集的具体数值**（如实际进程名、RSS 增量、预测 OOM 时间），不要照抄通用模板文案.

---

## 诊断报告模板

```
## 内存泄漏诊断报告

### 基本信息
- 监控目标: <进程名> (PID <pid>) / 全局扫描
- 监控时长: <elapsed>s（<monitor_count> 次采样，间隔 <monitor_interval>s）
- 数据完整度: <完整 / 部分缺失（说明原因）>

### 诊断结论
**<leak_confirmed / leak_suspected / normal / insufficient_data / process_disappeared>**
（<中文含义>）

### 内存增长详情
| 指标 | 起始值 | 结束值 | 变化量 |
|------|--------|--------|--------|
| RSS  | <start>MB | <end>MB | <delta>MB |
| PSS  | <start>MB | <end>MB | <delta>MB |
- 增长速率: <rate>KB/min（<pct>%/min）
- 增长趋势: <accelerating 加速 / decelerating 减速 / linear 线性 / 波动>
- 单调性: <是 / 否（有回落）>
- 文件描述符: <fd_count>（<正常 / 偏高：超过 5000>）

### OOM 预测
- 当前可用内存: <available>MB
- 按当前增速（线性外推）: <eta_human> 后可用内存耗尽
- 备注: <含 Swap 说明 / 线性外推仅供参考>

### 内存增长 Top <N> 进程（全局扫描模式）
| 进程名 | PID | 起始 RSS(MB) | 结束 RSS(MB) | 增量(MB) |
|--------|-----|-------------|-------------|---------|
| ...    | ... | ...         | ...         | ...     |

### 根因分析
根因类型（从以下四类中选择）:
- **业务堆泄漏**: VmAnon 持续增长，eBPF 有固定 malloc 调用栈
- **文件描述符泄漏**: fd_count 持续增长，RSS 增长相对缓慢
- **内存碎片（非真泄漏）**: RSS 高但重启后恢复正常，无单调递增
- **内核 slab 泄漏**: SUnreclaim 持续增长，用户态进程 RSS 正常

主要依据: <1-2 条核心证据，结合实际数值>
辅助印证: <eBPF 调用栈 / slab 信息 / fd 统计>

### 处置建议

**若为业务堆泄漏（C/C++ 程序）**：
1. **立即**: 确认进程 <name> 当前 RSS(<end>MB) 是否已影响业务，评估是否需要重启
2. **短期**: 使用 Valgrind 或 AddressSanitizer 在测试环境复现；若生产紧急可用 memleak 追踪调用栈
3. **长期**: 代码审查 malloc/free 配对，集成 LeakSanitizer 到 CI

**若为业务堆泄漏（Java 程序）**：
1. **立即**: `jmap -dump:live,format=b,file=/tmp/heap_<pid>.bin <pid>`（保留泄漏现场）
2. **短期**: 用 Eclipse Memory Analyzer (MAT) 分析 heap dump，查找 classloader/listener 泄漏
3. **长期**: 建立 JVM 堆内存监控（使用率 > 80% 告警）

**若为文件描述符泄漏**：
1. **立即**: `lsof -p <pid> | sort | uniq -c | sort -rn | head -20`（查看泄漏的 FD 类型）
2. **短期**: 代码审查 open/close 配对，特别是异常分支和循环体
3. **长期**: 设置 ulimit 限制 fd 上限，集成 fd 监控告警（> 1000 告警）

**若为内存碎片**：
1. **立即**: `gdb -p <pid> -ex "call malloc_trim(0)" -ex detach -ex quit`（归还 glibc 碎片）
2. **短期**: 使用 jemalloc 替换 glibc malloc（`LD_PRELOAD=/usr/lib/libjemalloc.so`）
3. **长期**: 定期重启策略或业务层内存池复用

### eBPF 调用栈摘要（若已采集）
<memleak 输出的未释放内存调用栈，展示前 5 条>
```

---

## 常见问题排查

### 监控时长不足，结论为 insufficient_data

增加采样次数或间隔：

```bash
bash scripts/collect_memory_leak.sh -n java -c 10 -i 30
```

### 进程在监控期间退出

`collect_memory_leak.sh` 会自动检测进程消失并停止采样. 若采集到 ≥ 2 次数据，仍可输出初步结论.

### 内存增长但非业务泄漏（内存碎片）

表现：RSS 高但进程逻辑内存使用合理，重启后 RSS 下降. 处理方式：
```bash
# 使用 malloc_trim 归还碎片（C/C++ 程序）
gdb -p <pid> -ex "call malloc_trim(0)" -ex detach -ex quit

# 或配置 jemalloc/tcmalloc 替换 glibc malloc
```

### 找不到 memleak 工具

```bash
# TencentOS 2
yum install -y bcc-tools
# TencentOS 3/4
dnf install -y bcc-tools

# 确认工具位置
ls /usr/share/bcc/tools/memleak
```

### Java 进程内存泄漏排查

RSS 增长但 JVM GC 正常时，检查堆外内存：
```bash
# 查看 JVM 堆使用（需 jdk 工具）
jmap -heap <pid>

# 查看堆对象分布（最多 20 种）
jmap -histo <pid> | head -25

# 查看 GC 日志
jstat -gcutil <pid> 5000 10
```

### 结论为 insufficient_data 是什么原因？

两种可能：
1. **采样次数不足**（< 2 次）：增加 `monitor_count`
2. **监控时长不足**（< 30 秒）：增加 `monitor_interval`

```bash
# 至少采样 3 次，每次间隔 20 秒（总时长 60s）
bash scripts/collect_memory_leak.sh -n java -c 3 -i 20
```

### 内存波动和真实泄漏怎么区分？

| 特征 | 正常波动 | 真实泄漏 |
|------|---------|---------|
| RSS 变化形态 | 锯齿状，有明显回落 | 楼梯状，只增不落 |
| 重启后表现 | 与重启前一致 | 重启后 RSS 恢复正常 |
| 单调性 | 否 | 是（多次采样均递增） |
| GC/缓存行为 | 可解释 | 无法解释的持续增长 |

判断方法：增加 `monitor_count` 到 10+，观察 RSS 序列是否严格单调递增.

### PSS 和 RSS 哪个更准确？

- **RSS**（Resident Set Size）：包含共享内存页，多进程共享库会被重复计算，偏高
- **PSS**（Proportional Set Size）：按比例分摊共享页，更真实反映进程实际占用

本 Skill 主要用 RSS 做趋势判定（速度快），PSS 作为辅助参考. 若 RSS 判定为 normal 但 PSS 持续增长，说明存在共享内存泄漏.

### 全局模式多个进程都在增长怎么处理？

全局模式检测到多个进程 RSS 增长时，说明可能是：
1. 系统整体内存压力（非单一进程泄漏）
2. 共享库泄漏（多进程使用同一共享库）

建议逐一切换为单进程模式确认：
```bash
# 对全局扫描中增长最快的进程逐一确认
bash scripts/collect_memory_leak.sh -p <pid1> -c 6
bash scripts/collect_memory_leak.sh -p <pid2> -c 6
```

---

## 相关技能

- **oom-killer**：OOM 事件已发生后的根因分析（本 Skill 为事前预防）
- **memory-analysis**：系统整体内存状态快照（OOM 次数、大页、Swap）
- **system-log**：查看内核日志中的内存相关报错
