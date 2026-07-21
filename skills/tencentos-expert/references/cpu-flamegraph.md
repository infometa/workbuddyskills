---
name: cpu-flamegraph
description: 需要生成火焰图、分析火焰图、CPU热点可视化、调用栈分布分析、性能瓶颈定位可视化需求时触发
description_zh: 使用perf-prof生成和分析火焰图，覆盖数据采集、格式转换（flamegraph.pl）、结果解读完整工作流，支持profile/trace/task-state分析器
description_en: Generate and analyze flame graphs using perf-prof. Covers full workflow of data collection, format conversion (flamegraph.pl), and result interpretation. Supports profile, trace, and task-state profilers.
version: 1.0.0
---

# 火焰图生成与分析

## 概述

火焰图（Flame Graph）是一种将调用栈采样数据可视化的工具，能够直观展示程序在各个函数上花费的时间。本技能基于 perf-prof 工具，提供火焰图的完整工作流：数据采集、格式转换和结果分析。

### 前置条件

1. **perf-prof 已安装**：
   ```bash
   which perf-prof && perf-prof --version
   ```
   如果未安装，优先从 yum 源安装：
   ```bash
   yum install -y perf-prof
   ```
   如果 yum 源中没有，则从源码编译安装：
   ```bash
   git clone https://github.com/OpenCloudOS/perf-prof.git || git clone https://gitee.com/OpenCloudOS/perf-prof.git
   cd perf-prof
   yum install -y xz-devel elfutils-libelf-devel libunwind-devel python3-devel
   make
   ```
   **如果 perf-prof 无法安装**，可以使用 perf 原生命令作为替代方案，但需先确保 FlameGraph 工具集已安装（参考 [FlameGraph 工具安装指南](references/flamegraph-install.md)），详见 [perf 替代方案](references/perf.md)。

2. **flamegraph.pl 已安装**（用于将折叠栈转换为 SVG）：
   参考 [FlameGraph 工具安装指南](references/flamegraph-install.md) 进行安装和验证。

## 火焰图工作流

### 三阶段流程

```
阶段1: 数据采集          阶段2: 格式转换           阶段3: 可视化与分析
perf-prof [profiler]  →  折叠栈文件(.folded)   →  flamegraph.pl → SVG
  --flame-graph file       comm;func1;func2 N       交互式火焰图
```

### 第一步：确定分析场景，选择分析器

根据要分析的问题类型选择对应的分析器：

```
火焰图分析场景
├── CPU热点分析 → profile
│   适用：CPU使用率高、定位热点函数、内核态/用户态CPU消耗
├── 事件调用栈分析 → trace
│   适用：特定事件（调度、内存分配、IO等）的调用路径可视化
└── 进程状态分析 → task-state
    适用：进程D状态、S状态的原因分析，阻塞路径定位
```

### 第二步：查看分析器帮助

```bash
perf-prof <profiler> -h
```

### 第三步：采集数据生成折叠栈

#### 3.1 profile - CPU热点火焰图

profile 通过定期采样CPU执行状态，记录调用栈，生成折叠栈文件。

**基本用法：**
```bash
perf-prof profile -F <freq> -g --flame-graph <file> [选项] [-- workload]
```

**关键选项：**
| 选项 | 说明 | 推荐值 |
|------|------|--------|
| `-F, --freq <n>` | 采样频率(Hz) **[必需]** | 99-999，推荐 997 |
| `-g, --call-graph` | 启用调用栈记录 **[必需]** | 始终启用 |
| `--flame-graph <file>` | 折叠栈输出文件 **[必需]** | 如 `cpu.folded` |
| `-p, --pids` | 监控指定进程 | 按需 |
| `-C, --cpus` | 监控指定CPU | 按需 |
| `-m, --mmap-pages` | ringbuffer大小 | 高频采样时增大 |
| `--than <n>` | 百分比阈值，过滤低占比函数 | 按需 |
| `-i, --interval <ms>` | 周期性输出间隔 | 配合 `--flame-graph ""` |
| `--user-callchain[=dwarf[,size]]` | 用户态调用栈，`no-`前缀排除。`=dwarf` 启用DWARF栈回溯 | 按需 |
| `--kernel-callchain` | 内核态调用栈，`no-`前缀排除 | 按需 |

**eBPF 过滤选项（采样前过滤，高效）：**
| 选项 | 说明 |
|------|------|
| `--exclude-user` | 只分析内核态热点 |
| `--exclude-kernel` | 只分析用户态热点 |
| `--exclude-guest` / `-G` | Host/Guest 隔离分析 |
| `--irqs_disabled` | 只采样中断关闭的代码段 |
| `--tif_need_resched` | 只采样需要调度但未调度的代码段 |
| `--exclude_pid <pid>` | 排除指定进程 |
| `--nr_running_min <n>` | 按 runqueue 最小长度过滤 |
| `--nr_running_max <n>` | 按 runqueue 最大长度过滤 |
| `--sched_policy <n>` | 按调度策略过滤（0:NORMAL, 1:FIFO, 2:RR, 3:BATCH, 5:IDLE, 6:DEADLINE） |
| `--prio <prio[-prio],...>` | 按优先级范围过滤（0-139） |

**示例：**
```bash
# 整个系统CPU火焰图（60秒）
timeout 60 perf-prof profile -F 997 -g --flame-graph cpu.folded

# 特定进程CPU火焰图
timeout 30 perf-prof profile -F 997 -p <pid> -g --flame-graph proc.folded

# 特定CPU火焰图
timeout 60 perf-prof profile -F 997 -C 0-3 -g --flame-graph cpus.folded

# 只看内核态热点
timeout 60 perf-prof profile -F 997 --exclude-user -g --flame-graph kernel.folded

# 只看用户态热点
timeout 60 perf-prof profile -F 997 --exclude-kernel -g --flame-graph user.folded

# 只采样中断关闭代码段
perf-prof profile -F 997 --irqs_disabled -g --flame-graph irqoff.folded

# 只采样 runqueue >= 3 的 CPU
perf-prof profile -F 997 --nr_running_min 3 -g --flame-graph busy.folded

# 只采样实时优先级进程（0-99）
perf-prof profile -F 997 --prio 0-99 -g --flame-graph rt.folded

# 只采样 RR 调度策略进程
perf-prof profile -F 997 --sched_policy 2 -g --flame-graph rr.folded

# 采样延迟调度的代码
perf-prof profile -F 997 --tif_need_resched -g --flame-graph sched_delay.folded

# Host/Guest 隔离分析
perf-prof profile -F 997 --exclude-guest -g --flame-graph host.folded
perf-prof profile -F 997 -G -g --flame-graph guest.folded

# 高频采样（需增大ringbuffer）
perf-prof profile -F 4000 -g -m 64 --flame-graph high_freq.folded

# 生产环境低开销
timeout 300 perf-prof profile -F 99 -g --flame-graph production.folded

# 周期性火焰图（每5秒输出一次）
perf-prof profile -F 997 -g --flame-graph "" -i 5000
```

#### 3.2 trace - 事件调用栈火焰图

trace 跟踪系统事件并记录调用栈，支持 tracepoint、kprobe、uprobe 等事件源。

**基本用法：**
```bash
perf-prof trace -e EVENT[,...] -g --flame-graph <file> [选项]
```

**关键选项：**
| 选项 | 说明 |
|------|------|
| `-e, --event <EVENT,...>` | 事件选择器 **[必需]** |
| `-g, --call-graph` | 启用调用栈记录 **[必需]** |
| `--flame-graph <file>` | 折叠栈输出文件 **[必需]** |
| `-i, --interval <ms>` | 周期性输出间隔 |
| `--order` | 按时间戳排序事件 |
| `-N, --exit-N <N>` | 采集N个事件后退出 |
| `-m, --mmap-pages` | ringbuffer大小 |
| `--user-callchain[=dwarf[,size]]` | 用户态调用栈，`no-`前缀排除。`=dwarf` 启用DWARF栈回溯 |
| `--kernel-callchain` | 内核态调用栈，`no-`前缀排除 |

**事件源类型：**
```
tracepoint:  sys:name[/filter/ATTR/.../]          # 如 sched:sched_wakeup
kprobe:      kprobe:func[/filter/ATTR/.../]       # 内核函数探针
kretprobe:   kretprobe:func[/filter/ATTR/.../]    # 内核函数返回探针
uprobe:      uprobe:func@"file"[/filter/ATTR/.../]   # 用户态函数探针
uretprobe:   uretprobe:func@"file"[/filter/ATTR/.../] # 用户态函数返回探针
profiler:    profiler[/option/ATTR/.../]           # 嵌入其他分析器
```

**事件属性（在 `/` 分隔符中配置）：**
| 属性 | 说明 |
|------|------|
| `stack` | 为指定事件打开调用栈 |
| `max-stack=int` | 指定堆栈深度（默认127） |
| `alias=str` | 事件别名 |
| `cpus=cpu[-cpu]` | 指定CPU范围 |
| `exec=EXPR` | 执行表达式 |

**过滤器语法（内核态执行，高效）：**
- 数值比较：`==`, `!=`, `<`, `<=`, `>`, `>=`, `&`
- 字符串匹配：`==`, `!=`, `~`（通配符）
- 逻辑组合：`&&`, `||`, `()`
- 注意：事件有过滤器时，`-e` 选项必须使用单引号

**示例：**
```bash
# 跟踪高优先级进程唤醒的调用栈
perf-prof trace -e 'sched:sched_wakeup/prio<10/' -g --flame-graph high_prio.folded

# 跟踪内核函数调用栈
perf-prof trace -e 'kprobe:schedule' -g --flame-graph schedule.folded

# 监控大内存分配的调用栈
perf-prof trace -e 'kmem:kmalloc/bytes_alloc>1024/stack/' -g --flame-graph kmalloc.folded -m 128

# 使用通配符匹配多个事件
perf-prof trace -e 'sched:sched_wakeup,sched:sched_switch' -g --flame-graph sched.folded

# 周期性生成火焰图
perf-prof trace -e 'sched:sched_wakeup' -g --flame-graph wakeup.folded -i 5000

# 多层过滤组合
perf-prof trace -e 'sched:sched_wakeup/target_cpu==0 && prio<10/stack/max-stack=16/' -g --flame-graph filtered.folded
```

#### 3.3 task-state - 进程状态火焰图

task-state 跟踪进程状态变化，通过火焰图展示导致进程进入各种状态（D/S/RD等）的调用路径。

**基本用法：**
```bash
perf-prof task-state [-S] [-D] -g --flame-graph <file> [选项]
```

**关键选项：**
| 选项 | 说明 |
|------|------|
| `-g, --call-graph` | 启用调用栈记录 **[必需]** |
| `--flame-graph <file>` | 折叠栈输出文件 **[必需]** |
| `-S, --interruptible` | 监控可中断睡眠状态，`no-`前缀排除 |
| `-D, --uninterruptible` | 监控不可中断睡眠状态 |
| `--than <n>` | 输出超过阈值的事件（单位: s/ms/us/ns） |
| `--filter <comm>` | 按进程名过滤（支持通配符 `*?[]`） |
| `--perins` | 按线程输出统计 |
| `--ptrace` | 跟踪新创建的线程 |
| `--user-callchain[=dwarf[,size]]` | 用户态调用栈，`no-`前缀排除。`=dwarf` 启用DWARF栈回溯 |
| `--kernel-callchain` | 内核态调用栈，`no-`前缀排除 |

**示例：**
```bash
# D状态（IO等待）火焰图
perf-prof task-state -D --than 10ms -g --flame-graph d_state.folded

# 特定进程状态火焰图
perf-prof task-state -p <pid> -g --flame-graph proc_state.folded

# 按进程名过滤
perf-prof task-state --filter 'java*' -D -g --flame-graph java_d.folded

# 同时分析S和D状态
perf-prof task-state -SD --than 5ms -g --flame-graph sleep.folded
```

### 第四步：生成 SVG 火焰图

将折叠栈文件转换为交互式 SVG：

```bash
flamegraph.pl <folded_file> > <output>.svg
```

**常用 flamegraph.pl 选项：**
| 选项 | 说明 |
|------|------|
| `--title <text>` | 设置火焰图标题 |
| `--width <px>` | 设置图片宽度（默认1200） |
| `--height <px>` | 设置每层高度（默认16） |
| `--minwidth <px>` | 最小显示宽度（默认0.1） |
| `--countname <text>` | 计数单位名称（如 "samples"） |
| `--colors <scheme>` | 颜色方案（hot/mem/io/java/...） |
| `--reverse` | 生成倒置火焰图（icicle graph） |
| `--inverted` | 倒置显示 |

**示例：**
```bash
# 基本转换
flamegraph.pl cpu.folded > cpu.svg

# 自定义标题和颜色
flamegraph.pl --title "CPU Flame Graph" --colors hot cpu.folded > cpu.svg

# 生成倒置火焰图
flamegraph.pl --reverse cpu.folded > cpu_icicle.svg
```

### 第五步：分析火焰图

#### 5.1 折叠栈文件格式

**标准格式：**
```
comm;func1;func2;func3 count
```
- `comm`: 进程名
- `func1;func2;func3`: 从栈底到栈顶的调用链，分号分隔
- `count`: 该调用栈的采样次数

**时间序列格式（周期性输出，`--flame-graph "" -i INT`）：**
```
YYYY-MM-DD;HH:MM:SS;comm;func1;func2;func3 count
```

#### 5.2 火焰图解读方法

**基本解读：**
- **X轴**：函数名按字母排序排列，宽度代表采样占比（不代表时间顺序）
- **Y轴**：调用栈深度，从下到上是调用链（底部是根，顶部是叶子函数）
- **宽度**：函数的采样次数占总采样的比例，越宽说明在CPU上花费时间越多
- **颜色**：通常随机分配，用于区分不同函数

**分析要点：**
1. **找宽顶（plateau）**：顶部宽的函数 = 自身消耗CPU多的函数 = 热点
2. **找宽塔（tower）**：整体宽度大的调用链 = 该路径消耗CPU多
3. **搜索功能**：SVG 支持 Ctrl+F 搜索函数名，匹配项会高亮
4. **缩放功能**：点击某个函数可以放大查看其子调用

**常见模式：**
| 模式 | 含义 | 行动 |
|------|------|------|
| 单一宽顶 | 单个函数是明确热点 | 优化该函数 |
| 多个窄塔 | CPU分散在很多路径 | 可能正常，关注整体架构 |
| 深且宽的栈 | 调用链过深 | 考虑减少调用层级 |
| `[unknown]` 帧 | 缺少符号信息 | 安装 debuginfo 包 |
| 内核栈宽 | 内核态消耗大 | 分析系统调用和内核路径 |

#### 5.3 直接分析折叠栈文件

当无法使用 flamegraph.pl 生成 SVG 时，可以直接分析折叠栈文件：

```bash
# 查看最热的调用栈（前20）
sort -t' ' -k2 -rn <file>.folded | head -20

# 统计某个函数被采样的次数
grep "function_name" <file>.folded | awk '{sum+=$NF} END {print sum}'

# 查看包含某函数的所有调用路径
grep "function_name" <file>.folded | sort -t' ' -k2 -rn

# 统计各进程的采样分布
awk -F';' '{print $1}' <file>.folded | sort | uniq -c | sort -rn
```

## 周期性火焰图（趋势分析）

周期性火焰图可以跟踪热点随时间的变化，适合分析间歇性性能问题。

**使用方法：**
```bash
# --flame-graph "" 表示只生成火焰图（到stdout），-i 指定周期（毫秒）
perf-prof profile -F 997 -g --flame-graph "" -i 5000

# trace 也支持
perf-prof trace -e 'sched:sched_wakeup' -g --flame-graph wakeup.folded -i 5000
```

**输出格式：**
```
YYYY-MM-DD;HH:MM:SS;comm;func1;func2;func3 count
```
时间戳作为调用栈的一部分，可以按时间段分析不同时刻的热点差异。

## 性能优化建议

| 场景 | 建议 |
|------|------|
| 高频采样 | 增大 `-m` 参数（如 `-m 64` 或 `-m 256`） |
| 生产环境 | 降低采样频率（`-F 99`），限制时间（`timeout 300 perf-prof ...`） |
| 事件量大 | 添加过滤器减少数据量 |
| 符号缺失 | 安装 debuginfo 包，使用 `--user-callchain=dwarf` |
| ringbuffer溢出 | 增大 `-m` 参数，或添加过滤器 |

## 严格约束

- 使用新的分析器时，必须先执行 `perf-prof <profiler> -h` 查看帮助
- 生成火焰图必须同时使用 `-g` 和 `--flame-graph` 选项
- 事件有过滤器时，`-e` 选项必须使用单引号，避免与bash运算符冲突
- 事件属性使用表达式时，必须使用括号包含整个表达式部分
- 如果 perf-prof 无法安装，切换到 perf 原生命令方案（需先安装 FlameGraph 工具集，参考 [FlameGraph 工具安装指南](references/flamegraph-install.md)），参考 [perf 替代方案](references/perf.md)

## 相关资源

- [FlameGraph 工具集](https://github.com/brendangregg/FlameGraph)
- [perf-prof 项目](https://github.com/OpenCloudOS/perf-prof.git)
- [perf 替代方案](references/perf.md) - 当 perf-prof 无法安装时使用 perf 原生命令
- [示例 Prompt](references/examples.md) - 典型使用场景与触发示例
- [使用指南](references/guide.md) - 面向用户的通俗上手指南，含安装、案例与常见误区
