---
name: sched-latency
description: Analyze process scheduling latency using perf-prof or perf to locate scheduling performance bottlenecks
description_zh: 分析进程的调度延迟（唤醒延迟和抢占延迟），定位调度层面的性能瓶颈
description_en: Analyze process scheduling latency including wake-up delay and preemption delay to locate scheduling performance bottlenecks
version: 1.0.0
---

# 进程调度延迟分析

你是 TencentOS 系统运维专家，擅长使用 perf-prof、perf 等工具分析进程的调度延迟，定位调度性能瓶颈。

## 任务目标

分析指定进程的调度延迟（scheduling latency），包括唤醒延迟（wake-up delay）和抢占延迟（preemption delay），输出延迟分布统计（p50/p95/p99/max），帮助用户定位调度层面的性能瓶颈。

## 工具优先级

按以下优先级选择分析工具：
1. **perf-prof rundelay**（推荐）：专用调度延迟分析器，自动配置 sched 事件和 key 关联，内存中实时处理，开销低，支持延迟分布、按线程统计、阈值过滤、详细跟踪等高级功能
2. **perf-prof task-state**（辅助）：进程状态分布分析，可定位 RD（调度延迟）状态占比
3. **perf sched**（降级）：Linux 内核自带调度分析工具
4. **无兜底方案**：perf-prof 和 perf 都不可用时，直接报错终止，告知用户必须安装其中之一

## 执行步骤

### 步骤 1：确认目标进程和延迟阈值

#### 1.1 确认目标进程

确认用户要分析的目标进程，获取进程 PID：

```bash
# 通过进程名查找 PID
ps aux | grep <进程名>
# 或
pgrep -f <进程名>
```

确认进程存在且正在运行后，记录 PID 用于后续分析。

#### 1.2 确定延迟阈值

延迟阈值决定了 `--than` 过滤参数和监控脚本的抓取粒度，**必须在开始分析前确定**。

**优先从用户描述中提取**：仔细阅读用户的 prompt，从中提取延迟相关的时间信息。常见的表达方式：

| 用户描述示例 | 提取的阈值 |
|------------|-----------|
| "任务经常超时 10ms" | `10ms` |
| "偶尔卡顿 100 毫秒" | `100ms` |
| "响应时间偶现 50ms 毛刺" | `50ms` |
| "SLA 要求延迟不超过 5ms" | `5ms` |
| "抖动到 200us 以上" | `200us` |

如果用户的描述中包含了具体的延迟时间数值，**直接使用该值作为阈值**，无需再询问。例如用户说"某任务经常超时 10ms，分析下调度延迟"，则阈值直接使用 `10ms`。

**用户未提供具体时间时**：根据目标进程的类型和特征，给出几个合理的选项供用户选择。判断依据：

| 进程类型 | 典型场景 | 推荐阈值选项 |
|---------|---------|-------------|
| 低延迟交易/金融 | 量化交易、高频交易系统 | 100us, 500us, 1ms |
| 实时音视频 | 直播推流、视频会议、游戏服务器 | 1ms, 5ms, 10ms |
| Web 服务/RPC | nginx、java 微服务、gRPC | 5ms, 10ms, 50ms |
| 数据库 | MySQL、Redis、MongoDB | 5ms, 10ms, 50ms |
| 批处理/大数据 | Spark、Hadoop、离线计算 | 10ms, 50ms, 100ms |
| 不确定/通用 | 其他进程 | 5ms, 10ms, 50ms |

向用户展示选项时的格式：

> 请选择调度延迟的关注阈值（超过此值的延迟事件会被详细记录，包括调用栈）：
> 1. **5ms** — 适合对延迟敏感的在线服务
> 2. **10ms** — 适合一般 Web 服务和数据库
> 3. **50ms** — 适合批处理任务或初步排查
>
> 您也可以输入自定义值（如 1ms、100us 等）。

将确定的阈值记为 `<THRESHOLD>`，后续所有步骤的 `--than` 参数和监控脚本均使用此值。

#### 1.3 判断分析模式

根据用户的 prompt 意图，判断走**实时分析**还是**直接部署长期监控**：

| 用户意图特征 | 判断 | 走向 |
|------------|------|------|
| 明确要求部署监控脚本（如"部署监控"、"生成监控脚本"、"挂个后台脚本抓"） | **直接部署** | → 步骤 2 → 步骤 5 |
| 描述问题难以复现（如"很难复现"、"偶尔才出现"、"上周出现过一次"） | **直接部署** | → 步骤 2 → 步骤 5 |
| 要求分析调度延迟（如"分析 nginx 的调度延迟"、"看看是不是调度慢"） | **实时分析** | → 步骤 2 → 步骤 3 → 步骤 4（可能再到步骤 5） |
| 提供了监控日志要求分析（如"帮我分析这个 summary.log"） | **分析已有日志** | → 直接跳到步骤 5.4（分析监控结果） |
| 意图不明确 | **默认实时分析** | → 步骤 2 → 步骤 3 → 步骤 4 |

> **"直接部署"模式说明**：跳过步骤 3（实时分析）和步骤 4（分析报告），在步骤 2 中只需确认 perf-prof 可用（长期监控依赖 perf-prof，不支持 perf 降级），然后直接进入步骤 5。

将判断结果记为 `<MODE>`（`实时分析` / `直接部署` / `分析日志`），后续步骤据此分流。

### 步骤 2：检测和安装分析工具

> **严格要求**：perf-prof 是首选工具，调度延迟分析能力远优于 perf。必须按照以下完整流程执行，**禁止在未尝试安装 perf-prof 的情况下直接降级使用 perf**。

#### 2.1 检查 perf-prof 是否已安装

```bash
which perf-prof && perf-prof --version
```

- 如果上述命令**执行成功**（输出了版本号）：
  - `<MODE>` 为"直接部署" → 跳转到 **步骤 5（生成长期监控脚本）**
  - 其他模式 → 跳转到 **步骤 3A（使用 perf-prof 分析）**
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

如果验证成功（`which perf-prof` 能找到且输出了版本号）：
- `<MODE>` 为"直接部署" → 跳转到 **步骤 5**
- 其他模式 → 跳转到 **步骤 3A（使用 perf-prof 分析）**

如果验证失败 → 记录失败原因，跳转到 **步骤 2.3**。

**情况 B：用户拒绝安装** → 跳转到 **步骤 2.3**。

#### 2.3 降级方案 — 仅在 perf-prof 确认无法使用时执行

> 只有当满足以下任一条件时，才允许进入此步骤：
> - 步骤 2.2 中用户明确拒绝安装 perf-prof
> - 步骤 2.2 中安装过程的某个子步骤（a/b/c/d）实际执行后失败
>
> **绝不允许**跳过步骤 2.2 直接进入此步骤。

**如果 `<MODE>` 为"直接部署"**：perf-prof 不可用则长期监控无法部署，**直接报错终止**：

> ⛔ 长期监控脚本依赖 perf-prof，perf 不支持长期监控模式。请安装 perf-prof 后重试：
> `git clone https://gitee.com/OpenCloudOS/perf-prof.git && cd perf-prof && make`

**如果 `<MODE>` 为"实时分析"**：向用户说明 perf-prof 无法使用的原因后，降级到 perf：

```bash
which perf && perf --version
```
如果 perf 可用 → 跳转到 **步骤 3B（使用 perf 分析）**。

#### 2.4 所有工具均不可用 — 直接报错终止

perf-prof 和 perf 都不可用时，**直接报错终止**，告知用户：

> ⛔ 调度延迟分析必须依赖 perf-prof 或 perf 工具，无替代方案。
>
> 请安装以下工具之一后重试：
> - **perf-prof**（推荐）：`git clone https://gitee.com/OpenCloudOS/perf-prof.git && cd perf-prof && make`
> - **perf**：`yum install -y perf` 或 `dnf install -y perf`

**不提供任何兜底分析方案，直接终止流程。**

### 步骤 3A：使用 perf-prof 分析（推荐）

perf-prof 的 rundelay 分析器是 multi-trace 的特化版本，预配置了 `sched:sched_wakeup`/`sched:sched_wakeup_new` 和 `sched:sched_switch` 事件，专用于分析调度延迟。需要 root 权限。

#### 3A.1 基础统计 — 了解调度延迟整体分布

```bash
# 统计目标进程的调度延迟（每秒输出一次）
perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000
```

输出格式：
```
          rundelay                calls        total(us)      min(us)      p50(us)      p95(us)      p99(us)      max(us)
------------------------- ------------ ---------------- ------------ ------------ ------------ ------------ ------------
wake-up delay                     1234         5678.901        0.123        2.345       15.678       45.123      120.456
preemption delay                   567         1234.567        0.234        1.567        8.901       25.678       80.123
```

字段说明：
| 字段 | 说明 |
|------|------|
| rundelay | 延迟类型：wake-up delay（唤醒延迟）或 preemption delay（抢占延迟） |
| calls | 发生次数 |
| total(us) | 总延迟时间（微秒） |
| min(us) | 最小延迟 |
| p50(us) | 50 分位延迟（中位数） |
| p95(us) | 95 分位延迟 |
| p99(us) | 99 分位延迟 |
| max(us) | 最大延迟 |

观察 **至少 10 个周期** 的输出后，根据结果判断下一步走向：

| 3A.1 观察结果 | 判断 | 下一步 |
|--------------|------|--------|
| max 多次超过 `<THRESHOLD>` | **当前可复现** | → 3A.2 逐步深入分析 |
| p99 偏高但 max 偶尔才超过 `<THRESHOLD>` | **低频可复现** | → 3A.2 逐步深入，同时考虑步骤 5（长期监控） |
| max 从未超过 `<THRESHOLD>` | **当前未超阈值** | → 直接跳到 **步骤 4**（会建议部署长期监控） |

#### 3A.2 按线程统计 — 定位具体线程

> **以下 3A.2 ~ 3A.5 为渐进式深入分析**，不要一次性全部执行。每完成一步后判断是否已获得足够信息来定位问题，如果是则直接跳到步骤 4 出报告。典型路径：
> - 轻度问题：3A.1 → 3A.2 → 步骤 4
> - 中度问题：3A.1 → 3A.2 → 3A.3 → 3A.6 → 步骤 4
> - 严重/需定位根因：3A.1 → 3A.2 → 3A.3 → 3A.4 → 3A.5 → 3A.6 → 步骤 4

```bash
# 加上 --perins 按线程维度统计
perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000 --perins
```

输出格式增加 thread 和 comm 列，可以定位是哪个线程调度延迟最严重。

#### 3A.3 阈值过滤 — 聚焦慢调度

使用步骤 1.2 中确定的延迟阈值 `<THRESHOLD>` 过滤延迟较高的调度事件：

```bash
# 只统计延迟超过阈值的调度事件
perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000 --perins --than <THRESHOLD>
```

例如用户描述"任务经常超时 10ms"，则使用 `--than 10ms`。

#### 3A.4 详细跟踪 — 分析延迟期间的中间事件

当发现延迟毛刺时，使用 `--detail=samecpu` 查看延迟区间内同一 CPU 上的中间事件，定位延迟原因：

```bash
# 查看超过阈值的调度延迟，并显示期间的中间事件
perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000 --than <THRESHOLD> --detail=samecpu
```

中间事件可以揭示：
- 是否有其他高优先级进程抢占了 CPU
- 是否有中断处理占用了 CPU
- 目标进程被哪个进程让出 CPU

#### 3A.5 调用栈采集 — 定位唤醒源和切出原因

```bash
# 采集调度延迟时的调用栈（wakeup 端 + switch 端）
perf-prof rundelay -e 'sched:sched_wakeup*/stack/,sched:sched_switch//stack/' \
    -e 'sched:sched_switch//stack/' -p <PID> -i 1000 --than <THRESHOLD>
```

两端调用栈的分析：
- **wakeup 端调用栈（唤醒源）**：是谁（哪个进程、哪个代码路径）唤醒了目标进程
- **第一个 -e 的 switch 端调用栈（被切出时）**：目标进程被切出时正在执行的代码路径，判断是自愿睡眠（futex_wait/ep_poll）还是被抢占（__cond_resched/preempt_schedule）
- **第二个 -e 的 switch 端调用栈（被切入时）**：目标进程被重新调度运行时的上下文

#### 3A.6 辅助分析：task-state — 查看进程状态分布

```bash
# 统计进程在各状态的时间分布（每秒输出一次）
perf-prof task-state -p <PID> -i 1000 -S
```

输出中各状态含义：
| 状态 | 说明 |
|------|------|
| R | Running — 正在 CPU 上运行 |
| RD | Runnable Delay — 可运行但等待 CPU（调度延迟） |
| S | Sleeping — 自愿睡眠（等待 I/O、锁等） |
| D | Disk Sleep — 不可中断睡眠（通常为磁盘 I/O） |

重点关注 **RD 状态占比**：
- RD 占比高 → 调度延迟严重，CPU 资源不足或调度策略不当
- S 占比高 → 进程大部分时间在等待，可能是 I/O 或锁瓶颈
- R 占比高 → CPU 密集型，调度延迟不是主要问题

#### 3A.7 高频场景优化

如果目标进程调度事件频率很高，可能出现事件丢失（stderr 输出 `lost xx events on`），需增大缓冲区：

```bash
# 增大 ringbuffer 到 256 页
perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000 -m 256
```

### 步骤 3B：使用 perf 分析

#### 3B.1 使用 perf sched record 采集调度数据

```bash
# 采集目标进程的调度事件，持续 30 秒，-g 采集调用栈
perf sched record -g -p <PID> -- sleep 30
```

> 注意：`-g` 参数会采集调度切换时的调用栈，用于后续分析延迟原因。perf sched record 会采集系统级的调度事件（不仅是目标进程），数据量较大。采集时长建议 30 秒，不宜过长。

#### 3B.2 查看调度延迟统计

```bash
# 输出调度延迟汇总，按最大延迟排序
perf sched latency --sort max
```

输出示例：
```
  Task                  |   Runtime ms  | Switches | Avg delay ms | Max delay ms |
  ----------------------|---------------|----------|--------------|--------------|
  nginx:12345           |    500.123    |    1234  |    2.345     |   50.678     |
  nginx:12346           |    300.456    |     567  |    1.234     |   25.345     |
```

字段说明：
| 字段 | 说明 |
|------|------|
| Task | 进程名:PID |
| Runtime ms | 实际运行时间 |
| Switches | 上下文切换次数 |
| Avg delay ms | 平均调度延迟 |
| Max delay ms | 最大调度延迟 |

**判断下一步**：检查目标进程的 Max delay 是否超过 `<THRESHOLD>`：
- 超过 → 继续 3B.3 深入分析具体事件
- 未超过 → 跳到步骤 4

#### 3B.3 查看调度时间线 — 定位超阈值事件

当 3B.2 发现超阈值延迟时，**必须**使用 `perf sched timehist` 定位具体的延迟事件及其调用栈：

```bash
# 输出详细的调度时间线，-g 显示调用栈，过滤目标进程的超阈值事件
perf sched timehist -g | grep -B20 <进程名> | head -200
```

从输出中找到 `wait time` 超过 `<THRESHOLD>` 的行，记录其**时间戳、CPU、wait time**，并重点分析紧跟其后的**调用栈**：

- 调用栈显示的是进程被**切出（sched_switch）时的代码路径**
- 如果栈顶是 `schedule()` ← `do_nanosleep()` / `futex_wait()` 等 → 进程是自愿睡眠，延迟原因是唤醒后等待 CPU
- 如果栈顶是 `schedule()` ← `__cond_resched()` 等 → 进程被抢占

#### 3B.4 分析超阈值事件的上下文 — 从调用栈定位延迟原因

找到超阈值事件后，**必须**结合调用栈和 CPU 上下文分析延迟根因：

**第一步：分析目标进程的调用栈**

从 3B.3 中获取的调用栈，判断进程被切出的原因：

| 调用栈特征 | 切出原因 | 延迟类型 |
|-----------|---------|---------|
| `schedule()` ← `futex_wait()` | 等待锁/条件变量 | 唤醒延迟（被唤醒后等 CPU） |
| `schedule()` ← `ep_poll()` / `do_select()` | 等待 I/O 事件 | 唤醒延迟 |
| `schedule()` ← `do_nanosleep()` / `hrtimer_nanosleep()` | 主动 sleep | 唤醒延迟 |
| `schedule()` ← `__cond_resched()` | 被内核抢占 | 抢占延迟 |
| `schedule()` ← `preempt_schedule_common()` | 被高优先级进程抢占 | 抢占延迟 |

**第二步：分析延迟期间 CPU 上的其他进程**

```bash
# 查看该时间段附近同一 CPU 上的所有调度事件和调用栈
perf sched timehist -g -C <CPU> | grep -A20 "<时间戳前缀>" | head -100
```

从上下文中分析延迟期间**谁占了 CPU**：
- 查看目标进程等待期间，同 CPU 上运行的其他进程及其调用栈
- 如果某个进程长时间占用 CPU（runtime 大） → 该进程是延迟的直接原因
- 如果有大量中断处理（`irq_handler_entry` 相关栈） → 中断处理时间过长

#### 3B.5 查看调度统计摘要

```bash
# 查看 CPU 利用率和调度统计
perf sched map
```

### 步骤 4：分析决策与报告

本步骤是整个分析流程的**决策汇聚点**。根据前序步骤的采集结果，判断走向并输出对应内容。

#### 4.1 判断分析结论

根据步骤 3A 或 3B 采集到的数据，对照阈值参考表做出判断：

| 情况 | 判定条件 | 操作 |
|------|---------|------|
| **A. 问题已定位** | 采集期间多次复现超阈值延迟，且通过调用栈/中间事件定位了根因 | → 4.2 输出完整分析报告 + 4.3 询问是否部署长期监控 |
| **B. 有延迟但根因不明** | 采集期间偶现超阈值延迟，但频率太低或调用栈信息不足以定位根因 | → 4.2 输出初步报告 + 4.3 询问是否部署长期监控 |
| **C. 当前未超过阈值** | 采集期间延迟未超过 `<THRESHOLD>`（无论整体水平高低） | → 4.2 输出当前状态报告 + 4.3 询问是否部署长期监控 |

> **重要**：短时间采集（通常 10-90 秒）的结果不具备统计充分性，无论哪种情况，都**必须在报告末尾执行步骤 4.3 询问用户是否需要部署长期监控**。

#### 4.2 输出分析报告

根据使用的分析工具（perf-prof 或 perf），选择对应的报告模板输出。

**使用 perf-prof 分析时的报告模板**（步骤 3A）：

（见下方"结果输出格式"章节的完整模板）

**使用 perf 分析时的报告模板**（步骤 3B）：

（见下方"结果输出格式"章节的 perf sched 报告模板）

#### 4.3 询问是否部署长期监控

> **强制要求**：输出分析报告后，**必须紧接着向用户提问**，明确询问是否需要部署长期监控脚本。不能只在报告中"提一下建议"就结束，**必须以提问形式等待用户回答**。

在分析报告输出完毕后，**必须**向用户提出以下问题：

> 调度延迟问题通常为偶现，短时间采集（几十秒到几分钟）的结果不具备统计充分性。如果该问题为偶现问题，建议部署后台监控脚本持续运行数天，等待问题复现时自动记录详细信息（包括调用栈），以便精确定位根因。
>
> **是否需要我为您部署调度延迟长期监控脚本？**

如果用户同意 → 继续执行 **步骤 5**。
如果用户拒绝 → 流程结束。

### 步骤 5：生成长期监控脚本（偶现问题场景）

> **适用场景**：调度延迟往往是偶现问题，短时间（如 10 秒）采集几乎不可能抓到现场。对于这类偶现问题，应为用户生成一个后台监控脚本，持续运行数天来捕获延迟毛刺。
>
> **前置条件**：此步骤仅在 perf-prof 可用时执行。perf-prof 的 rundelay 实时处理模式开销极低，适合长期部署。

#### 5.1 确认监控参数

目标进程和延迟阈值已在步骤 1 中确定，此处需要确定**监控时长**。

##### 监控时长确定

**优先从用户描述中提取**：

| 用户描述示例 | 提取的时长 |
|------------|-----------|
| "部署 3 天的监控" | 3 天 |
| "先跑一天看看" | 1 天 |
| "监控一周" | 7 天 |
| "这个问题每隔几小时出一次" | 1 天（复现周期短，1 天足够抓到多次） |
| "上周出现过一次" | 7 天（复现周期长，需要更长监控窗口） |

如果用户描述中包含了具体时长或可推断复现频率，**直接使用**，无需询问。

**用户未提供时**：根据步骤 4.1 的判断结果给出推荐选项，让用户选择：

| 步骤 4.1 判断 | 推荐选项（推荐项加粗） | 理由 |
|--------------|----------------------|------|
| B（有延迟但根因不明） | **1 天（推荐）**、3 天、7 天 | 问题已偶现过，1 天大概率抓到足够样本 |
| C（当前未复现） | 1 天、**3 天（推荐）**、7 天 | 问题未复现，需要更长窗口等待 |

向用户展示选项时的格式：

> 请选择监控时长：
> 1. **1 天** — 问题复现频率较高时适用
> 2. **3 天（推荐）** — 覆盖率和运维负担之间的平衡
> 3. **7 天** — 低频偶现问题，最大化捕获窗口
>
> 您也可以输入自定义天数。

将确定的时长记为 `<DURATION>`，后续脚本使用此值。

##### 参数汇总

| 参数 | 值 | 来源 |
|------|------|------|
| 目标进程 | PID + 进程名 | 步骤 1.1 |
| 延迟阈值 | `<THRESHOLD>` | 步骤 1.2 |
| 监控时长 | `<DURATION>` 天 | 本步骤（自动决定或从 prompt 提取） |
| 日志目录 | /var/log/sched-latency-monitor | 默认值 |

#### 5.2 验证 perf-prof 命令正确性

> **严格要求**：在生成监控脚本之前，**必须先短时间试跑 perf-prof 命令**，确认命令语法正确、事件可用、能正常产生输出。只有验证通过的命令才能写入最终的监控脚本。**禁止跳过验证直接输出脚本。**

##### 5.2.1 试跑统计摘要命令（通道 1）

用目标进程的 PID 短时间运行（3 秒），验证基础统计命令是否正常工作：

```bash
# 试跑 3 秒，检查命令是否能正常输出
timeout 3 perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch \
    -e sched:sched_switch -p <PID> -i 1000 --perins -m 256
```

**验证标准**：
- ✅ 命令正常退出（exit code 0 或被 timeout 终止返回 124），且 stdout 有统计输出 → 通过
- ❌ 命令报错（如 `invalid event`、`Permission denied`、`No such process`） → 需诊断修复

##### 5.2.2 试跑详细事件命令（通道 2）

验证带调用栈和详细跟踪的命令：

```bash
# 试跑 3 秒，检查带 stack 和 --detail 的命令是否正常工作
timeout 3 perf-prof rundelay -e 'sched:sched_wakeup*/stack/,sched:sched_switch//stack/' \
    -e 'sched:sched_switch//stack/' -p <PID> -i 1000 --perins -m 256 \
    --than <THRESHOLD> --detail=samecpu
```

**验证标准**（同上）：
- ✅ 命令正常退出，无报错 → 通过（注意：如果 3 秒内没有超阈值事件，stdout 可能为空，这是正常的，只要 stderr 无报错即可）
- ❌ 命令报错 → 需诊断修复

##### 5.2.3 验证失败的诊断和修复

如果试跑报错，按以下常见原因逐一排查并修复命令：

| 错误信息 | 原因 | 修复方法 |
|----------|------|----------|
| `Permission denied` / `No permission` | 权限不足 | 加 `sudo` 或 `sysctl -w kernel.perf_event_paranoid=-1` |
| `event not found` / `invalid event` | sched tracepoint 不可用 | `mount -t debugfs none /sys/kernel/debug`，或检查内核是否启用 CONFIG_SCHEDSTATS |
| `No such process` | PID 不存在 | 重新确认目标进程 PID |
| `stack` 属性报错 | perf-prof 版本不支持 | 去掉 `/stack/` 属性，改用 `-g` 参数采集调用栈：`perf-prof rundelay -e sched:sched_wakeup*,sched:sched_switch -e sched:sched_switch -p <PID> -g ...` |
| `--detail` 参数报错 | perf-prof 版本不支持 | 去掉 `--detail=samecpu` 参数 |
| `lost xx events on` | ringbuffer 不足 | 增大 `-m` 值（如 512 或 1024） |

修复后**必须重新执行步骤 5.2.1 和 5.2.2 的试跑**，直到两个命令都验证通过。

> **关键**：最终写入监控脚本的 perf-prof 命令，必须是经过试跑验证通过的那条命令（包括所有修复后的调整），不能与试跑命令有任何差异。

#### 5.3 生成并部署监控脚本

> **前置条件**：步骤 5.2 的两条 perf-prof 命令都已验证通过后，才执行此步骤。

读取脚本模板文件 `scripts/sched-latency-monitor.sh`（位于本 skill 目录下），基于该模板进行定制。

**定制规则**（必须严格执行）：

1. **替换默认参数占位符** — 将脚本顶部"默认参数"区域的占位符替换为实际值：

| 占位符 | 替换为 | 来源 |
|--------|--------|------|
| `<PID>` | 目标进程 PID | 步骤 1.1 |
| `<进程名>` | 目标进程名 | 步骤 1.1 |
| `<天数>` | 监控持续天数 | 步骤 5.1 中确定的 `<DURATION>` |
| `<阈值>` | 延迟阈值（如 10ms） | 步骤 1.2 |

2. **替换 perf-prof 命令** — 将 `start_summary()` 和 `start_detail()` 函数中的 perf-prof 命令替换为步骤 5.2 中**验证通过的命令**，仅将固定的 `-p <PID>` 改为 `-p "$TARGET_PID"`。如果验证时做了修复调整（如去掉 `/stack/`、去掉 `--detail`、改用 `-g` 等），此处必须同步修改。

3. **不修改其他逻辑** — 脚本的参数解析、前置检查、日志轮转、主循环、信号处理等逻辑不做修改。

**写入文件、设置权限、后台启动、验证**，一次性完成：

```bash
# 1. 将定制后的脚本写入文件
cat > /usr/local/bin/sched-latency-monitor.sh << 'SCRIPT_EOF'
... （定制后的完整脚本内容） ...
SCRIPT_EOF

# 2. 设置执行权限
chmod +x /usr/local/bin/sched-latency-monitor.sh

# 3. 后台启动监控
nohup bash /usr/local/bin/sched-latency-monitor.sh \
    > /dev/null 2>&1 &

# 4. 等待脚本初始化完成，验证启动是否成功
sleep 2
```

如果 `/usr/local/bin` 没有写权限，改用 `/tmp/sched-latency-monitor.sh`。

启动后**必须立即验证**：

```bash
# 检查脚本主进程是否存活
cat /var/log/sched-latency-monitor/monitor.pid && \
    kill -0 $(cat /var/log/sched-latency-monitor/monitor.pid) 2>/dev/null && \
    echo "监控脚本运行中" || echo "监控脚本未启动"

# 检查启动日志是否有错误
cat /var/log/sched-latency-monitor/monitor.log
```

**验证结果判断**：
- ✅ monitor.pid 存在、进程存活、monitor.log 显示"调度延迟监控启动" → 部署成功
- ❌ 进程不存在或 monitor.log 有错误 → 检查错误原因，修复后重新部署

部署成功后，**必须一次性向用户输出以下完整信息**：

> ✅ **调度延迟监控脚本已部署并启动**
>
> **监控配置：**
> - 监控进程: <进程名> (PID: <PID>)
> - 延迟阈值: <THRESHOLD>（超过此值的事件会记录调用栈和详细信息）
> - 监控时长: <DURATION> 天（预计 yyyy-mm-dd HH:MM 到期自动停止）
> - 脚本 PID: xxxx
>
> **日志文件：**
> | 文件 | 说明 |
> |------|------|
> | `/var/log/sched-latency-monitor/summary.log` | 每秒统计摘要（按线程维度），用于定位延迟高发时段 |
> | `/var/log/sched-latency-monitor/detail.log` | 超阈值事件详情 + 调用栈 + 同 CPU 中间事件，用于定位根因 |
> | `/var/log/sched-latency-monitor/monitor.log` | 脚本运行日志（确认监控是否正常） |
>
> **日常查看命令：**
> ```bash
> # 查看脚本运行状态
> tail -5 /var/log/sched-latency-monitor/monitor.log
> # 查看最新统计摘要
> tail -20 /var/log/sched-latency-monitor/summary.log
> # 查看捕获到的超阈值延迟事件
> tail -100 /var/log/sched-latency-monitor/detail.log
> ```
>
> **停止监控：**
> ```bash
> kill $(cat /var/log/sched-latency-monitor/monitor.pid)
> ```
>
> **📌 抓取完成后的分析：** 监控到期或手动停止后，您可以再次使用本技能（sched-latency）对采集结果进行分析。只需告诉我日志路径，例如："帮我分析 /var/log/sched-latency-monitor/ 下的调度延迟监控日志"，我会从 summary.log 和 detail.log 中提取延迟高发时段、分析调用栈定位根因，并输出完整的分析报告。

#### 5.4 分析监控结果

当用户收集到监控日志后，可以使用本 skill 对结果进行分析。告知用户：

> 监控日志收集完成后，可以将日志内容提供给我进行分析。我会帮你：
> 1. 从 `summary.log` 中找出延迟高发的时段和线程
> 2. 从 `detail.log` 中分析超阈值延迟的调用栈，定位延迟根因
> 3. 输出完整的分析报告和优化建议

**分析 summary.log — 定位高发时段和线程：**

引导用户提供日志片段，或直接读取日志文件进行分析。summary.log 的格式与 perf-prof rundelay `--perins` 的标准输出一致，包含时间戳和按线程维度的延迟统计。

分析方法：
1. 先用 `tail -100` 查看最近的输出，了解日志的实际格式
2. 根据实际格式，筛选 max 延迟超过阈值的行
3. 统计不同时段的延迟趋势，定位高发时段

```bash
# 第一步：查看日志实际格式
tail -50 /var/log/sched-latency-monitor/summary.log

# 查看 detail.log 中记录的超阈值事件数量
wc -l /var/log/sched-latency-monitor/detail.log
```

**分析 detail.log — 定位延迟根因：**

detail.log 中包含超阈值事件的完整信息：
- 延迟发生的精确时间戳
- 延迟时长
- 唤醒源/抢占源的调用栈
- 同 CPU 上的中间事件（哪些进程在延迟期间占用了 CPU）

根据这些信息，可以定位出调度延迟的具体原因（如：某个内核线程长时间占用 CPU、中断处理时间过长、cgroup CPU 限流等）。

## 结果输出格式

### perf-prof 分析报告模板（步骤 3A）

```
## 📊 进程调度延迟分析报告

**分析目标**: 进程名 (PID: xxxx)
**分析工具**: perf-prof rundelay
**分析时长**: xx 秒
**分析时间**: yyyy-mm-dd HH:MM:SS
**延迟阈值**: <THRESHOLD>

### 调度延迟 Top 线程

| 排名 | 线程 | 唤醒延迟 p50 | 唤醒延迟 p99 | 唤醒延迟 max | 抢占延迟 p50 | 抢占延迟 p99 | 抢占延迟 max |
|------|------|-------------|-------------|-------------|-------------|-------------|-------------|
| 1 | worker:12345 | 0.5ms | 5.2ms | 50.3ms | 0.2ms | 2.1ms | 15.6ms |
| 2 | worker:12346 | 0.3ms | 3.1ms | 25.8ms | 0.1ms | 1.5ms | 10.2ms |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 延迟分布分析

- **唤醒延迟（wake-up delay）**: [描述分布特征]
- **抢占延迟（preemption delay）**: [描述分布特征]
- **RD 状态占比**: xx%（task-state 结果，如已执行 3A.6）

### 延迟严重程度判定

| 指标 | 当前值 | 判定 |
|------|--------|------|
| p50 | x.xxms | 正常/需关注/严重 |
| p99 | x.xxms | 正常/需关注/严重 |
| max | x.xxms | 正常/需关注/严重 |

### 分析结论

1. **主要延迟类型**: [唤醒延迟/抢占延迟] 占主导
2. **延迟毛刺**: [是否存在长尾延迟，原因分析]
3. **CPU 竞争**: [是否存在 CPU 资源不足]
4. **根因定位**: [如有调用栈/中间事件数据，给出具体根因]

### 优化建议

1. [根据具体分析结果给出针对性建议]
2. [如有必要，建议使用其他工具进一步深入分析]
3. [如问题未复现或需更多数据，建议部署长期监控]
```

### perf sched 分析报告模板（步骤 3B）

```
## 📊 进程调度延迟分析报告

**分析目标**: 进程名 (PID: xxxx)
**分析工具**: perf sched
**分析时长**: xx 秒
**分析时间**: yyyy-mm-dd HH:MM:SS

### 调度延迟统计

| 排名 | 线程 | 运行时间 | 上下文切换次数 | 平均延迟 | 最大延迟 |
|------|------|---------|--------------|---------|---------|
| 1 | worker:12345 | 500.1ms | 1234 | 2.3ms | 50.7ms |
| 2 | worker:12346 | 300.5ms | 567 | 1.2ms | 25.3ms |
| ... | ... | ... | ... | ... | ... |

### 分析结论

1. **整体延迟水平**: [基于 Avg delay 和 Max delay 的判断]
2. **延迟毛刺**: [Max delay 远大于 Avg delay 说明存在长尾]
3. **上下文切换频率**: [Switches 数值是否异常]

### 局限性说明

> perf sched 只提供平均延迟和最大延迟，无法区分唤醒延迟和抢占延迟，也无法提供 p50/p95/p99 分位数。如需更精细的分析，建议安装 perf-prof。

### 优化建议

1. [根据具体分析结果给出针对性建议]
2. [建议安装 perf-prof 以获得更精确的延迟分布数据]
```

### 关键阈值参考

| 指标 | 正常 | 需关注 | 严重 |
|------|------|--------|------|
| p50 | <1ms | 1-5ms | >5ms |
| p99 | <10ms | 10-50ms | >50ms |
| max | <50ms | 50-100ms | >100ms |

## 异常处理

### 权限不足
perf-prof 和 perf 需要 root 权限或具有 `CAP_SYS_ADMIN` 能力：
```bash
sudo perf-prof rundelay ...
# 或临时调整 perf_event_paranoid
sudo sysctl -w kernel.perf_event_paranoid=-1
```

### 事件丢失
如果 perf-prof 输出中 stderr 出现 `lost xx events on`，说明 ringbuffer 不够大：
```bash
# 增大 mmap-pages
perf-prof rundelay ... -m 256
```

### 内核版本差异
`sched:sched_switch` 事件的 `prev_state` 字段在 Linux 4.14+ 内核中类型从 `long` 变为 `unsigned int`，perf-prof 会自动适配。如果遇到事件解析异常，请确认内核版本：
```bash
uname -r
```

### 进程已退出
如果目标进程在分析过程中退出，工具会自动停止。建议分析前确认进程会持续运行足够的时间。

### sched tracepoint 不可用
如果 sched 相关 tracepoint 不可用，可能是 debugfs 未挂载：
```bash
# 检查 sched tracepoint
ls /sys/kernel/debug/tracing/events/sched/
# 如果目录不存在，挂载 debugfs
mount -t debugfs none /sys/kernel/debug
```

## 参考信息

- perf-prof rundelay 是 multi-trace 的特化版本，预配置了 sched 事件的 key 关联（基于 PID 匹配唤醒/切换事件对）
- perf-prof task-state 使用 `sched:sched_switch` 和 `sched:sched_wakeup` 事件计算进程在各状态的停留时间
- 唤醒延迟（wake-up delay）：从 `sched_wakeup` 到 `sched_switch`（进程被选中运行）的时间间隔
- 抢占延迟（preemption delay）：从 `sched_switch`（进程被切出，prev_state=R）到下一次 `sched_switch`（进程被切入运行）的时间间隔
- 调度延迟的常见原因：CPU 过载、NUMA 不亲和、cgroup CPU 限制、实时进程抢占、中断处理时间过长
