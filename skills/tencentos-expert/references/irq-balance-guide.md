# 中断不均衡排查指南

> 这份指南面向遇到 CPU 软/硬中断负载不均衡问题的运维和开发人员，语言通俗，手把手带你从发现问题到定位根因。

---

## 一、什么时候需要排查中断不均衡？

中断不均衡的本质是：**本来该由多个 CPU 分担的中断处理，却集中压在一两个 CPU 上**，导致这些 CPU 成为瓶颈，整体性能上不去。

出现以下现象时，优先考虑中断不均衡：

| 你看到的现象 | 可能的中断不均衡原因 |
|---|---|
| `top` 里某个 CPU 的 `si`（软中断）持续偏高，其他 CPU 空闲 | 软中断集中，未分散 |
| 网络吞吐量上不去，但系统整体 CPU 还有余量 | NET_RX 软中断集中在少数 CPU |
| `ksoftirqd/0` 等线程 CPU 占用高 | 软中断处理压力集中 |
| 网络延迟抖动，偶发高延迟 | 软中断队列积压导致处理延迟 |
| `/proc/softirqs` 里某个 CPU 的 NET_RX 数字远大于其他 CPU | NET_RX 分布不均 |

**快速确认：**

```bash
# 看各 CPU 的软中断/硬中断占比
mpstat -P ALL 1 3

# 看软中断各类型在各 CPU 上的累计分布
cat /proc/softirqs
```

如果 `mpstat` 里某些 CPU 的 `%soft` 或 `%irq` 显著高于其他 CPU，或者 `softirqs` 里某个 CPU 的 `NET_RX` 远高于其他 CPU，就需要开始排查了。

---

## 二、安装配置

### 第一步：安装 perf-prof

```bash
# 检查是否已安装
which perf-prof && perf-prof --version
```

没有的话，用 yum 安装：

```bash
yum install -y perf-prof
```

yum 源里没有的话，从源码编译：

```bash
git clone https://gitee.com/OpenCloudOS/perf-prof.git
cd perf-prof
yum install -y xz-devel elfutils-libelf-devel libunwind-devel python3-devel
make
cp perf-prof /usr/local/bin/
```

### 第二步：安装 flamegraph.pl（热点定位阶段需要）

参考 [FlameGraph 工具安装指南](flamegraph-install.md) 完成安装。

### 第三步：验证

```bash
perf-prof --version    # 输出版本号即可，如 perf-prof 1.4
flamegraph.pl --help   # 输出帮助信息即可
```

---

## 三、排查流程全览

排查分六步，按顺序来，每步都有明确的"继续往下"或"找到了"的判断标准：

```
第一步：初步诊断（系统工具，30秒定性）
  ↓
第二步：精确统计（perf-prof，定量确认哪个 CPU 集中）
  ↓
第三步：时间维度分析（是持续问题还是突发？）
  ↓
第四步：延迟量化（不均衡对业务延迟的实际影响）
  ↓
第五步：热点定位（集中的 CPU 在做什么？）
  ↓
第六步：根因确认
```

---

## 四、分步排查详解

### 第一步：初步诊断

**看 CPU 中断负载分布：**

```bash
mpstat -P ALL 1 5
```

重点看 `%irq`（硬中断）和 `%soft`（软中断）列。正常情况下各 CPU 数值应该相近；如果某个 CPU 明显偏高，说明存在不均衡。

**看软中断类型分布：**

```bash
cat /proc/softirqs
```

对比各 CPU 的 `NET_RX`、`NET_TX`、`TIMER` 等数字。如果某个 CPU 的 `NET_RX` 是其他 CPU 的好几倍，网络收包软中断集中是主要问题。

**看硬中断绑定：**

```bash
cat /proc/interrupts
```

找到你的网卡（如 `eth0`、`virtio0`）对应的中断行，看各 CPU 上的计数是否均衡。

**看 irqbalance 是否在运行：**

```bash
systemctl status irqbalance
```

如果服务是 `inactive`（未运行），中断分配完全静态，需要手动配置亲和性或启动 irqbalance。

---

### 第二步：精确统计中断分布

用 perf-prof 实时观察中断在各 CPU 上的分布，比 `/proc/softirqs` 的累计计数更直观。

**统计各 CPU 的硬中断次数：**

```bash
perf-prof top -e 'irq:irq_handler_entry//key=irq/' -i 3000
```

输出示例（每 3 秒刷新一次）：
```
IRQ  IRQ_HANDLER_ENTRY
 45               73     ← IRQ 45 触发次数远高于其他
 41               12
 43                9
 47                8
```

**实时统计各 CPU 的 NET_RX 软中断（50ms 粒度）：**

```bash
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 50ms -i 3000 --perins
```

输出示例：
```
[CPU] 每50ms计数 → 5个周期依次显示
[000]  0  0  1  0  0  | total  1
[001]  0  1  0  0  1  | total  2
[002]  0  0  0  1  0  | total  1
[003] 16 13 14 15 13  | total 71  ← CPU3 独占，其他 CPU 几乎没有
[004]  0  1  0  0  0  | total  1
[005]  1  0  0  1  0  | total  2
[006]  0  0  1  0  1  | total  2
[007]  1  0  0  0  1  | total  2
```

CPU3 每轮约 14 次，其他 CPU 合计约 2 次，差距约 7 倍——确认不均衡。

---

### 第三步：时间维度分析

判断这是持续性问题还是偶发突发。

**持续观察 1 分钟：**

```bash
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 1000ms -i 60000 --perins
```

- 如果每秒都是某个 CPU 高：**持续性不均衡**，根因是亲和性或 RSS 哈希固定
- 如果偶尔某个 CPU 突然飙升：**突发性不均衡**，可能是流量突发或中断合并参数问题

**高精度微突发检测（10ms 粒度）：**

```bash
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 10ms -i 5000 --perins
```

---

### 第四步：延迟量化

确认不均衡对软中断处理延迟的实际影响。

**各 CPU 软中断处理延迟统计：**

```bash
perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 5000 --perins
```

输出示例：
```
CPU   start => end                calls    p50(us)  p95(us)  p99(us)  max(us)
  0   softirq_entry => softirq_exit  2990    2.1      3.6      4.8      131.0  ← 次数最多，max 最高
  3   softirq_entry => softirq_exit   450    1.0     20.7     25.2       31.1  ← p95 异常高
  6   softirq_entry => softirq_exit   351    0.8      2.8      4.6        6.0  ← 轻载，延迟低
```

CPU3 的 p95 延迟是 CPU6 的 7 倍，说明软中断集中已经影响到延迟了。

**单独分析 NET_RX 延迟：**

```bash
perf-prof multi-trace -e 'irq:softirq_entry/vec==3/' -e 'irq:softirq_exit/vec==3/' -i 5000 --perins
```

---

### 第五步：热点定位

找到中断集中的 CPU 上具体在执行什么代码，为调整方向提供依据。

**对中断负载最高的 CPU 做内核态热点采样：**

```bash
# 假设 CPU3 负载最高
timeout 30 perf-prof profile -F 997 -C 3 --exclude-user -g --flame-graph cpu3_kernel.folded
flamegraph.pl cpu3_kernel.folded > cpu3_kernel.svg
```

下载 SVG 用浏览器打开，搜索以下关键函数：
- `net_rx_action`：NET_RX 软中断的处理函数，宽说明收包压力大
- `__do_softirq`：软中断执行入口
- `ksoftirqd`：软中断内核线程

---

### 第六步：根因确认

根据前几步的结果，对照下表确认根因：

| 观察到的现象 | 根因 |
|---|---|
| 某个 IRQ 硬中断计数远高于其他，且该 IRQ 绑定在单个 CPU | **流量哈希不均**（RSS 哈希固定到某队列）|
| 所有 IRQ 都绑定在同一个 CPU | **IRQ 亲和性配置不当** |
| irqbalance 未运行，中断分布完全静态 | **irqbalance 未启动** |
| 网卡只有 1 个队列，无法分散硬中断 | **网卡队列数不足** |
| NET_RX 集中，IRQ 亲和性正常，RPS 未开启 | **RPS 未配置** |
| 单条大流量连接占满一个队列 | **单流大连接**，RSS 无法分散 |

---

## 五、效果说明与案例

### 案例：NET_RX 集中在 CPU3

**问题现象：**

```bash
$ cat /proc/softirqs | grep NET_RX
NET_RX:   9884   12658   7889   55834   10262   14295   11217   14850
          CPU0    CPU1    CPU2    CPU3    CPU4    CPU5    CPU6    CPU7
```

CPU3 的 NET_RX 次数是其他 CPU 平均值的 **4 倍**，占全部 NET_RX 的 41%。

**排查过程：**

1. `mpstat -P ALL 1 3` 确认 CPU3 的 `%soft` 显著偏高
2. `perf-prof top -e 'irq:irq_handler_entry//key=irq/' -i 3000` 发现 IRQ 45（virtio0-input.3）计数是其他队列的 4 倍
3. `perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 50ms -i 3000 --perins` 实时确认 NET_RX 持续集中在 CPU3
4. `perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 5000 --perins` 显示 CPU3 的软中断 p95 延迟（20.7µs）是 CPU6（2.8µs）的 7 倍
5. `perf-prof profile -F 997 -C 3 --exclude-user -g --flame-graph cpu3.folded` 热点火焰图确认 `net_rx_action` 占主导
6. 根因确认：上游流量哈希固定到队列 3，IRQ 亲和性本身正确，RPS 未开启

**perf-prof hrcount 实时观测对比：**

```
修复前（每秒 NET_RX 分布）：
CPU3: ~43次/秒，CPU0-2,4-7: 合计约 8次/秒

修复后（开启 RPS，每秒 NET_RX 分布）：
CPU0:  3次   CPU1:  4次   CPU2:  3次   CPU3: 15次
CPU4:  4次   CPU5:  3次   CPU6: 14次   CPU7:  4次
```

CPU3 从独占 84% 降至约 30%，软中断处理延迟 p95 从 20.7µs 降至约 5µs。

---

## 六、常见误区与 Tips

### ❌ 误区 1：irqbalance 启动了就不会有中断不均衡

**实际情况**：irqbalance 只负责动态调整**硬中断**亲和性，对软中断（如 NET_RX）没有直接控制。即使 irqbalance 运行正常，也可能因为 RSS 哈希不均导致软中断集中。排查时两个层面都要看。

### ❌ 误区 2：网卡有多队列就一定均衡

**实际情况**：多队列只是前提，还需要：
- IRQ 亲和性：每个队列绑定到不同 CPU
- RSS 哈希分布：流量能均匀分配到各队列

如果所有流量来自同一个源 IP，RSS 哈希结果相同，所有包仍会进同一个队列。

### ❌ 误区 3：`/proc/softirqs` 显示均衡就没问题

**实际情况**：`/proc/softirqs` 是**从系统启动以来的累计值**，看起来均衡可能只是历史累积的"均值效应"。当前时刻是否均衡，需要用 `perf-prof hrcount` 实时观测增量。

### 💡 Tip 1：先看增量，再看累计

`/proc/softirqs` 是累计值，判断当前是否均衡要用 hrcount 实时观测：

```bash
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 1000ms -i 5000 --perins
```

### 💡 Tip 2：大延迟时查看中间发生了什么

发现 p99 延迟异常高后，用 `--than` 抓出大延迟事件并还原现场：

```bash
# 抓出超过 50us 的软中断，并显示期间的调度事件
perf-prof multi-trace \
    -e irq:softirq_entry \
    -e 'irq:softirq_exit,sched:sched_switch//untraced/stack/' \
    -i 1000 --than 50us --detail=samecpu --order
```

### 💡 Tip 3：同时对比硬中断和软中断的时间分布

```bash
perf-prof hrcount \
    -e 'irq:irq_handler_entry//alias=hard/,irq:softirq_entry//alias=soft/' \
    -C 0-7 --period 50ms -i 3000 --perins
```

两行对比，可以快速判断是硬中断不均（IRQ 亲和性问题）还是软中断不均（RPS 问题）。

---

## 七、相关资源

- [perf-prof 项目](https://github.com/OpenCloudOS/perf-prof.git)
- [示例 Prompt](examples.md) - 常用触发场景速查
