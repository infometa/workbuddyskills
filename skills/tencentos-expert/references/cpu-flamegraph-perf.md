# 火焰图生成与分析

## 概述

火焰图（Flame Graph）是一种将调用栈采样数据可视化的工具，能够直观展示程序在各个函数上花费的时间。本技能基于 perf 和 FlameGraph 工具集，提供火焰图的完整工作流：数据采集、格式转换和结果分析。

### 前置条件

1. **perf 已安装**：
   ```bash
   which perf && perf --version
   ```
   如果未安装，从 yum 源安装：
   ```bash
   yum install -y perf
   ```

2. **FlameGraph 工具集已安装**（包含 stackcollapse-perf.pl 和 flamegraph.pl）：
   参考 [FlameGraph 工具安装指南](references/flamegraph-install.md) 进行安装和验证。

## 火焰图工作流

### 三阶段流程

```
阶段1: 数据采集               阶段2: 格式转换                         阶段3: 可视化
perf record -g -a         →  perf script | stackcollapse-perf.pl  →  flamegraph.pl → SVG
  生成 perf.data               生成折叠栈文件(.folded)                  交互式火焰图
```

### 标准三步命令

```bash
# 步骤1: 采集数据
perf record -F 997 -g -a -o perf.data -- sleep 60

# 步骤2: 转换为折叠栈
perf script -i perf.data | stackcollapse-perf.pl > cpu.folded

# 步骤3: 生成SVG火焰图
flamegraph.pl cpu.folded > cpu.svg
```

也可以用管道一行完成步骤2和步骤3：
```bash
perf script -i perf.data | stackcollapse-perf.pl | flamegraph.pl > cpu.svg
```

### 第一步：确定分析场景

根据要分析的问题类型选择对应的 perf record 参数：

```
火焰图分析场景
├── CPU热点分析 → perf record -F <freq> -g
│   适用：CPU使用率高、定位热点函数、内核态/用户态CPU消耗
├── 事件调用栈分析 → perf record -e <event> -g
│   适用：特定事件（调度、内存分配、IO等）的调用路径可视化
├── 进程状态分析 → perf record -e sched:sched_switch -g + 后处理
│   适用：进程D状态、S状态的原因分析，阻塞路径定位
└── 事件调用栈分析 → perf record -e <event> -g
    适用：特定事件（调度、内存分配、IO等）的调用路径可视化
```

### 第二步：采集数据生成折叠栈

#### 2.1 CPU热点火焰图

通过定期采样CPU执行状态，记录调用栈，生成火焰图。

**基本用法：**
```bash
perf record -F <freq> -g [选项] -o perf.data -- sleep <seconds>
perf script -i perf.data | stackcollapse-perf.pl > <file>.folded
flamegraph.pl <file>.folded > <file>.svg
```

**关键选项：**
| 选项 | 说明 | 推荐值 |
|------|------|--------|
| `-F <n>` | 采样频率(Hz) **[必需]** | 99-999，推荐 997 |
| `-g` | 启用调用栈记录 **[必需]** | 始终启用 |
| `-a` | 系统级采样（所有CPU） | 默认使用 |
| `-p <pid>` | 监控指定进程 | 按需 |
| `-C <cpus>` | 监控指定CPU | 按需 |
| `-o <file>` | 输出文件 | 默认 perf.data |
| `--call-graph dwarf` | 使用DWARF栈回溯（用户态更准确） | 用户态程序推荐 |
| `--call-graph lbr` | 使用LBR栈回溯（Intel CPU，零开销） | Intel平台推荐 |

**过滤选项：**
| 选项 | 说明 |
|------|------|
| `--exclude-user` | 只采样内核态 |
| `--exclude-kernel` | 只采样用户态 |
| `--exclude-guest` | 排除Guest采样（Host分析） |
| `--exclude-host` | 排除Host采样（Guest分析） |

**示例：**
```bash
# 整个系统CPU火焰图（60秒）
perf record -F 997 -g -a -o perf.data -- sleep 60
perf script -i perf.data | stackcollapse-perf.pl > cpu.folded
flamegraph.pl cpu.folded > cpu.svg

# 特定进程CPU火焰图
perf record -F 997 -g -p <pid> -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > proc.folded
flamegraph.pl proc.folded > proc.svg

# 特定CPU火焰图
perf record -F 997 -g -C 0-3 -o perf.data -- sleep 60
perf script -i perf.data | stackcollapse-perf.pl > cpus.folded
flamegraph.pl cpus.folded > cpus.svg

# 只看内核态热点
perf record -F 997 -g --exclude-user -a -o perf.data -- sleep 60
perf script -i perf.data | stackcollapse-perf.pl > kernel.folded
flamegraph.pl kernel.folded > kernel.svg

# 只看用户态热点
perf record -F 997 -g --exclude-kernel -a -o perf.data -- sleep 60
perf script -i perf.data | stackcollapse-perf.pl > user.folded
flamegraph.pl user.folded > user.svg

# 使用DWARF栈回溯（用户态更准确）
perf record -F 997 --call-graph dwarf -p <pid> -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > dwarf.folded
flamegraph.pl dwarf.folded > dwarf.svg

# Host/Guest 隔离分析
perf record -F 997 -g --exclude-guest -a -o perf.data -- sleep 60
perf script -i perf.data | stackcollapse-perf.pl > host.folded
flamegraph.pl host.folded > host.svg

# 高频采样（需增大mmap缓冲区）
perf record -F 4000 -g -a -m 64 -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > high_freq.folded
flamegraph.pl high_freq.folded > high_freq.svg

# 生产环境低开销
perf record -F 99 -g -a -o perf.data -- sleep 300
perf script -i perf.data | stackcollapse-perf.pl > production.folded
flamegraph.pl production.folded > production.svg

# 一行完成（采集+转换+生成SVG）
perf record -F 997 -g -a -o perf.data -- sleep 60 && perf script -i perf.data | stackcollapse-perf.pl | flamegraph.pl > cpu.svg
```

#### 2.2 事件调用栈火焰图

跟踪系统事件并记录调用栈，支持 tracepoint、kprobe、uprobe 等事件源。

**基本用法：**
```bash
perf record -e <event> -g [选项] -o perf.data -- sleep <seconds>
perf script -i perf.data | stackcollapse-perf.pl > <file>.folded
flamegraph.pl <file>.folded > <file>.svg
```

**关键选项：**
| 选项 | 说明 |
|------|------|
| `-e <event>` | 事件选择器 **[必需]** |
| `-g` | 启用调用栈记录 **[必需]** |
| `-a` | 系统级采样 |
| `--filter '<filter>'` | tracepoint 事件过滤器 |
| `-m <pages>` | mmap缓冲区大小（高频事件增大） |

**事件源类型：**
```
tracepoint:  <subsys>:<event>            # 如 sched:sched_wakeup
kprobe:      kprobe:<func>               # 内核函数探针（需先添加）
uprobe:      uprobe:<func>               # 用户态函数探针（需先添加）
```

**过滤器语法（tracepoint 事件）：**
- 在 `-e` 后使用 `--filter` 指定内核态过滤条件
- 数值比较：`==`, `!=`, `<`, `<=`, `>`, `>=`, `&`
- 字符串匹配：`==`, `!=`, `~`（通配符）
- 逻辑组合：`&&`, `||`

**示例：**
```bash
# 跟踪高优先级进程唤醒的调用栈
perf record -e sched:sched_wakeup --filter 'prio < 10' -g -a -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > high_prio.folded
flamegraph.pl high_prio.folded > high_prio.svg

# 跟踪内核函数调用栈（使用kprobe）
perf probe --add schedule
perf record -e probe:schedule -g -a -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > schedule.folded
flamegraph.pl schedule.folded > schedule.svg
perf probe --del schedule

# 监控大内存分配的调用栈
perf record -e kmem:kmalloc --filter 'bytes_alloc > 1024' -g -a -m 128 -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > kmalloc.folded
flamegraph.pl kmalloc.folded > kmalloc.svg

# 跟踪多个事件
perf record -e sched:sched_wakeup -e sched:sched_switch -g -a -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > sched.folded
flamegraph.pl sched.folded > sched.svg

# 带过滤器的多层组合
perf record -e sched:sched_wakeup --filter 'target_cpu == 0 && prio < 10' -g -C 0 -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > filtered.folded
flamegraph.pl filtered.folded > filtered.svg
```

#### 2.3 进程状态分析火焰图

通过跟踪调度事件，分析导致进程进入各种状态（D/S等）的调用路径。

**基本用法：**
```bash
# 采集调度事件
perf record -e sched:sched_switch -e sched:sched_wakeup -g -a -o perf.data -- sleep 60

# 导出事件数据
perf script -i perf.data > sched_events.txt

# 按 prev_state 筛选特定状态的调用栈并生成火焰图
# D状态（不可中断睡眠/IO等待）：prev_state 包含 D
grep -A 100 'prev_state=D' sched_events.txt | stackcollapse-perf.pl > d_state.folded
flamegraph.pl --title "D-State (Uninterruptible Sleep)" d_state.folded > d_state.svg

# S状态（可中断睡眠）：prev_state 包含 S
grep -A 100 'prev_state=S' sched_events.txt | stackcollapse-perf.pl > s_state.folded
flamegraph.pl --title "S-State (Interruptible Sleep)" s_state.folded > s_state.svg
```

**针对特定进程的状态分析：**
```bash
# 采集特定进程的调度事件
perf record -e sched:sched_switch --filter 'prev_pid == <pid> || next_pid == <pid>' \
    -e sched:sched_wakeup --filter 'pid == <pid>' -g -a -o perf.data -- sleep 60
perf script -i perf.data > proc_sched.txt

# 按进程名过滤
perf record -e sched:sched_switch --filter 'prev_comm ~ "java*"' \
    -e sched:sched_wakeup --filter 'comm ~ "java*"' -g -a -o perf.data -- sleep 60
```

### 第三步：生成 SVG 火焰图

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

**stackcollapse-perf.pl 常用选项：**
| 选项 | 说明 |
|------|------|
| `--pid` | 在进程名后附加PID |
| `--tid` | 在进程名后附加TID |
| `--inline` | 展开内联函数 |
| `--kernel` | 只保留内核栈帧 |
| `--jit` | 支持JIT符号（Java等） |

**示例：**
```bash
# 基本转换
flamegraph.pl cpu.folded > cpu.svg

# 自定义标题和颜色
flamegraph.pl --title "CPU Flame Graph" --colors hot cpu.folded > cpu.svg

# 生成倒置火焰图
flamegraph.pl --reverse cpu.folded > cpu_icicle.svg

# 附加PID信息
perf script -i perf.data | stackcollapse-perf.pl --pid > cpu.folded
```

### 第四步：分析火焰图

#### 4.1 折叠栈文件格式

**标准格式：**
```
comm;func1;func2;func3 count
```
- `comm`: 进程名
- `func1;func2;func3`: 从栈底到栈顶的调用链，分号分隔
- `count`: 该调用栈的采样次数

#### 4.2 火焰图解读方法

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

#### 4.3 直接分析折叠栈文件

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

#### 4.4 使用 perf report 交互分析

除火焰图外，还可以使用 perf report 直接分析 perf.data：

```bash
# 交互式查看热点
perf report -i perf.data

# 按调用链展开
perf report -i perf.data --call-graph=graph

# 文本模式输出（非交互）
perf report -i perf.data --stdio

# 按进程汇总
perf report -i perf.data --sort comm
```

## 周期性火焰图（趋势分析）

周期性火焰图可以跟踪热点随时间的变化，适合分析间歇性性能问题。

perf 不支持直接周期性生成折叠栈，需要通过脚本循环实现：

```bash
#!/bin/bash
# periodic_flamegraph.sh - 周期性生成火焰图
INTERVAL=${1:-5}    # 每次采样间隔（秒），默认5秒
COUNT=${2:-12}      # 采样次数，默认12次
FREQ=${3:-997}      # 采样频率

for i in $(seq 1 $COUNT); do
    ts=$(date +%Y%m%d_%H%M%S)
    perf record -F $FREQ -g -a -o perf_${ts}.data -- sleep $INTERVAL
    perf script -i perf_${ts}.data | stackcollapse-perf.pl > flame_${ts}.folded
    flamegraph.pl --title "Flame Graph ${ts}" flame_${ts}.folded > flame_${ts}.svg
    rm -f perf_${ts}.data
    echo "Generated flame_${ts}.svg"
done
```

使用方法：
```bash
# 每5秒采样一次，共12次（1分钟）
bash periodic_flamegraph.sh 5 12 997

# 每10秒采样一次，共6次
bash periodic_flamegraph.sh 10 6 997
```

## Differential Flame Graph（差分火焰图）

比较两个时间点或场景的火焰图差异，定位性能变化：

```bash
# 采集基准数据
perf record -F 997 -g -a -o perf_before.data -- sleep 60
perf script -i perf_before.data | stackcollapse-perf.pl > before.folded

# 采集对比数据
perf record -F 997 -g -a -o perf_after.data -- sleep 60
perf script -i perf_after.data | stackcollapse-perf.pl > after.folded

# 生成差分火焰图
difffolded.pl before.folded after.folded | flamegraph.pl > diff.svg
```

## 性能优化建议

| 场景 | 建议 |
|------|------|
| 高频采样 | 增大 `-m` 参数（如 `-m 64`） |
| 生产环境 | 降低采样频率（`-F 99`），限制时间（`-- sleep 300`） |
| 事件量大 | 添加 `--filter` 过滤器减少数据量 |
| 符号缺失 | 安装 debuginfo 包，使用 `--call-graph dwarf` |
| 用户态栈不完整 | 使用 `--call-graph dwarf` 或 `--call-graph lbr` |
| perf.data过大 | 减少采样时间或频率，或使用 `-m` 控制缓冲区 |
| Java/JIT符号 | 使用 `perf-map-agent` 生成符号映射，`stackcollapse-perf.pl --jit` |

## 严格约束

- 生成火焰图必须使用 `-g` 选项启用调用栈记录
- 高频事件需要增大 `-m` 参数避免数据丢失
- tracepoint 过滤器使用 `--filter` 选项，注意引号转义
- `perf record` 默认输出到 `perf.data`，多次采集需用 `-o` 指定不同文件名避免覆盖
- 需要 root 权限或 `kernel.perf_event_paranoid` 设置为 -1

## 相关资源

- [FlameGraph 工具集](https://github.com/brendangregg/FlameGraph)
- [FlameGraph 工具安装指南](references/flamegraph-install.md)
- [perf wiki](https://perf.wiki.kernel.org/)
- [Brendan Gregg's Flame Graph 页面](https://www.brendangregg.com/flamegraphs.html)
