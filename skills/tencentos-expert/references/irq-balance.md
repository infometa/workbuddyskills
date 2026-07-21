---
name: irq-balance
description: 软中断不均衡、硬中断不均衡、部分CPU中断负载高、网络收包不均匀、软中断延迟高、中断亲和性问题、ksoftirqd CPU占用高时触发
description_zh: 使用perf-prof排查软中断/硬中断不均衡问题，覆盖初步诊断→中断分布统计→时间维度突发检测→延迟影响分析→热点定位→根因确认完整流程
description_en: Diagnose soft/hard IRQ imbalance using perf-prof. Covers full workflow from initial diagnosis, IRQ distribution stats, burst detection, latency impact analysis, hotspot profiling, to root cause confirmation.
version: 1.0.0
---

# 软中断/硬中断不均衡排查

## 概述

中断不均衡是指系统中各CPU处理的中断数量差异显著，导致部分CPU负载过高，影响整体性能。本技能提供系统化的排查流程，从发现不均衡到定位根因。

### 常见症状

- 部分CPU的 `si`（软中断）或 `hi`（硬中断）占比显著高于其他CPU
- 网络收发性能不稳定，部分网卡队列负载集中
- `ksoftirqd/N` 线程在某些CPU上CPU占用高
- 系统整体吞吐未达预期，但部分CPU已满载

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

## 排查流程总览

```
第一步：初步诊断（系统工具确认问题）
  │
  ▼
第二步：中断分布统计（定量确认不均衡）
  │  ├── 2.1 硬中断分布 → top / sql
  │  ├── 2.2 软中断分布 → top / sql
  │  └── 2.3 按CPU×中断类型交叉统计 → top / sql
  │
  ▼
第三步：时间维度突发检测（定位时间窗口）
  │  └── hrcount 高精度计数
  │
  ▼
第四步：延迟影响分析（量化不均衡的影响）
  │  └── multi-trace 延迟分析
  │
  ▼
第五步：热点定位（找到根因代码路径）
  │  └── profile 火焰图
  │
  ▼
第六步：根因确认与处置建议
```

## 第一步：初步诊断

使用系统工具确认存在中断不均衡问题。

### 1.1 查看各CPU中断负载

```bash
# 查看各CPU的si/hi占比
mpstat -P ALL 1 5

# 关注字段：
# %irq  - 硬中断占比
# %soft - 软中断占比
# 不均衡特征：某些CPU的%irq或%soft显著高于其他CPU
```

### 1.2 查看中断计数分布

```bash
# 查看各CPU的中断计数
cat /proc/interrupts

# 关注：同一中断号在各CPU上的计数差异
# 网卡中断通常按队列绑定到不同CPU
```

### 1.3 查看软中断计数分布

```bash
# 查看各CPU的软中断计数
cat /proc/softirqs

# 关注：NET_RX、NET_TX、TIMER等在各CPU上的分布
# 不均衡特征：某些CPU的计数远大于其他CPU
```

### 1.4 查看中断亲和性

```bash
# 查看中断亲和性设置
for irq in /proc/irq/*/smp_affinity_list; do
    echo "IRQ $(basename $(dirname $irq)): $(cat $irq)"
done

# 检查irqbalance服务状态
systemctl status irqbalance
```

**判断依据：** 如果确认存在不均衡（某些CPU的中断数或中断CPU占比显著偏高），进入第二步精确分析。

## 第二步：中断分布统计

使用 perf-prof 精确统计中断在各CPU上的分布。

### 2.1 硬中断分布统计

**方法A：使用 top 统计每个中断号的触发次数**
```bash
# 按中断号统计硬中断次数和名称
perf-prof top -e irq:irq_handler_entry//key=irq/comm=name/ -i 1000
```
输出示例：
```
IRQ IRQ_HANDLER_ENTRY NAME
 28              12345 eth0-TxRx-0
 29               8901 eth0-TxRx-1
 30                234 eth0-TxRx-2
```
**解读**：各中断号的计数差异反映了硬中断不均衡程度。

**方法B：使用 top 按CPU×中断号交叉统计**
```bash
# 复合key：高32位为CPU号，低32位为中断号
perf-prof top -e 'irq:irq_handler_entry//key=(_cpu<<32)|irq/printkey=printf("  %03d   %4d",key>>32,(int)key)/comm=name/' -i 1000
```
**解读**：直接看每个CPU上每个中断的触发次数。

**方法C：使用 sql 灵活查询**
```bash
# 按CPU统计硬中断总数
perf-prof sql -e irq:irq_handler_entry -i 1000 \
  --query 'SELECT _cpu, COUNT(*) as count FROM irq_handler_entry GROUP BY _cpu ORDER BY count DESC'

# 按CPU×中断名交叉统计
perf-prof sql -e irq:irq_handler_entry -i 1000 \
  --query 'SELECT _cpu, name, COUNT(*) as count FROM irq_handler_entry GROUP BY _cpu, name ORDER BY count DESC'
```

### 2.2 软中断分布统计

**方法A：使用 top 按CPU×软中断类型统计**
```bash
# 复合key：高32位为CPU号，低32位为软中断向量号
perf-prof top -e 'irq:softirq_entry//key=(_cpu<<32)|vec/printkey=printf("  %03d      %d",key>>32,(int)key)/' -i 1000
```
输出示例：
```
(_CPU<<32)|VEC SOFTIRQ_ENTRY
    000      1          5678    # CPU0 NET_TX
    000      3          1234    # CPU0 NET_RX
    001      3           123    # CPU1 NET_RX
```
**解读**：对比同一软中断向量在不同CPU上的计数差异。

**方法B：使用 sql 按软中断名称统计**
```bash
# 按CPU和软中断名称统计
perf-prof sql -e irq:softirq_entry -i 1000 \
  --query "SELECT _cpu, symbolic('vec', vec) as name, COUNT(*) as count FROM softirq_entry GROUP BY _cpu, vec ORDER BY vec, _cpu"
```
输出示例：
```
_cpu | name     | count
-----|----------|------
0    | HI       | 12
1    | HI       | 5
0    | NET_TX   | 5678
1    | NET_TX   | 234
0    | NET_RX   | 8901
1    | NET_RX   | 567
```

**方法C：只统计网络相关软中断**
```bash
# NET_TX=1, NET_RX=3
perf-prof sql -e 'irq:softirq_entry/vec==1 || vec==3/' -i 1000 \
  --query "SELECT _cpu, symbolic('vec', vec) as name, COUNT(*) as count FROM softirq_entry GROUP BY _cpu, vec ORDER BY vec, _cpu"
```

### 2.3 软中断向量号速查

| vec | 名称 | 说明 |
|-----|------|------|
| 0 | HI | 高优先级tasklet |
| 1 | TIMER | 定时器 |
| 2 | NET_TX | 网络发送 |
| 3 | NET_RX | 网络接收 |
| 4 | BLOCK | 块设备 |
| 5 | IRQ_POLL | IRQ轮询 |
| 6 | TASKLET | 普通tasklet |
| 7 | SCHED | 调度器 |
| 8 | HRTIMER | 高精度定时器 |
| 9 | RCU | RCU回调 |

## 第三步：时间维度突发检测

使用 hrcount 以毫秒级粒度观察中断的时间分布，发现突发和波动。

### 3.1 硬中断时间分布

```bash
# 各CPU硬中断计数（50ms粒度，每秒输出）
perf-prof hrcount -e irq:irq_handler_entry -C 0-7 --period 50ms -i 1000 --perins
```
输出示例：
```
[000] irq:irq_handler_entry 120|135|128|142|130| total 655
[001] irq:irq_handler_entry  12| 15| 10| 14| 11| total  62
```
**解读**：CPU0每50ms约130次硬中断，CPU1仅约12次，差距约10倍。

### 3.2 软中断时间分布

```bash
# 各CPU软中断计数（50ms粒度）
perf-prof hrcount -e irq:softirq_entry -C 0-7 --period 50ms -i 1000 --perins

# 只看网络收包软中断（NET_RX=3）
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 50ms -i 1000 --perins

# 只看网络发包软中断（NET_TX=1）
perf-prof hrcount -e 'irq:softirq_entry/vec==1/' -C 0-7 --period 50ms -i 1000 --perins
```

### 3.3 对比硬中断和软中断

```bash
# 同时观察硬中断和软中断（使用别名区分）
perf-prof hrcount -e 'irq:irq_handler_entry//alias=hard/,irq:softirq_entry//alias=soft/' \
    -C 0-7 --period 50ms -i 1000 --perins
```

### 3.4 更高精度分析（微突发检测）

```bash
# 10ms粒度，检测微突发
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-3 --period 10ms -i 1000 --perins

# 1ms粒度（极高精度）
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0 --period 1ms -i 500
```

## 第四步：延迟影响分析

使用 multi-trace 分析中断不均衡对软中断处理延迟的影响。

### 4.1 软中断处理延迟（按CPU统计）

```bash
# 各CPU软中断处理延迟分布
perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 1000 --perins
```
输出示例：
```
CPU         start => end             calls        total(us)      min(us)      p50(us)      p95(us)      p99(us)      max(us)
--- -------------    ------------ -------- ---------------- ------------ ------------ ------------ ------------ ------------
0   softirq_entry => softirq_exit      234          672.741        0.451        1.055        6.840       11.071      138.790
1   softirq_entry => softirq_exit       45           52.123        0.312        0.876        2.100        3.200        5.600
```
**解读**：CPU0的软中断处理次数多且延迟高（max 138us），CPU1次数少延迟低，确认不均衡影响。

### 4.2 按软中断类型分析延迟

```bash
# 只分析NET_RX软中断延迟
perf-prof multi-trace -e 'irq:softirq_entry/vec==3/' -e 'irq:softirq_exit/vec==3/' -i 1000 --perins

# 只分析NET_TX软中断延迟
perf-prof multi-trace -e 'irq:softirq_entry/vec==1/' -e 'irq:softirq_exit/vec==1/' -i 1000 --perins

# 只分析TIMER软中断延迟
perf-prof multi-trace -e 'irq:softirq_entry/vec==1/' -e 'irq:softirq_exit/vec==1/' -i 1000 --perins
```

### 4.3 大延迟深入分析

```bash
# 步骤1：确定阈值（根据4.1的p99值）
perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 1000 --perins --than 50us

# 步骤2：查看大延迟的中间细节
perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 1000 --perins --than 50us --detail=samecpu

# 步骤3：添加调度事件作为辅助信息，还原延迟期间的CPU活动
perf-prof multi-trace \
    -e irq:softirq_entry \
    -e 'irq:softirq_exit,sched:sched_switch//untraced/stack/' \
    -i 1000 --than 50us --detail=samecpu --order
```

### 4.4 硬中断处理延迟

```bash
# 硬中断处理延迟（按CPU统计）
perf-prof multi-trace -e irq:irq_handler_entry -e irq:irq_handler_exit -i 1000 --perins

# 特定中断号的处理延迟
perf-prof multi-trace -e 'irq:irq_handler_entry/irq==28/' -e 'irq:irq_handler_exit/irq==28/' -i 1000 --perins
```

## 第五步：热点定位

使用 profile 采样负载高的CPU上的热点代码路径。

### 5.1 采样高负载CPU的热点

```bash
# 采样特定CPU（选择中断负载高的CPU）
timeout 30 perf-prof profile -F 997 -C <high_irq_cpu> -g --flame-graph irq_cpu.folded
flamegraph.pl irq_cpu.folded > irq_cpu.svg
```

### 5.2 只采样软中断上下文

```bash
# 采样所有CPU的内核态热点
timeout 30 perf-prof profile -F 997 --exclude-user -g --flame-graph kernel.folded
flamegraph.pl kernel.folded > kernel.svg

# 在火焰图中搜索软中断相关函数：
# - __do_softirq
# - net_rx_action (NET_RX)
# - net_tx_action (NET_TX)
# - ksoftirqd
```

### 5.3 采样 ksoftirqd 线程

```bash
# 找到高负载CPU对应的ksoftirqd进程
ps -eo pid,comm,psr | grep ksoftirqd

# 采样特定ksoftirqd
timeout 30 perf-prof profile -F 997 -p <ksoftirqd_pid> -g --flame-graph ksoftirqd.folded
flamegraph.pl ksoftirqd.folded > ksoftirqd.svg
```

### 5.4 中断关闭代码段分析

```bash
# 如果怀疑中断被长时间关闭导致不均衡
timeout 30 perf-prof profile -F 997 --irqs_disabled -g --flame-graph irqoff.folded
flamegraph.pl irqoff.folded > irqoff.svg
```

## 第六步：根因确认与处置建议

根据前五步收集的数据，确认根因并给出处置建议。

### 常见根因与处置

| 根因 | 特征 | 处置建议 |
|------|------|----------|
| **中断亲和性配置不当** | 多个中断绑定到同一CPU | 调整 `/proc/irq/<N>/smp_affinity` 或配置 irqbalance |
| **RSS/RPS未配置** | 网络软中断集中在单个CPU | 配置网卡RSS队列或开启RPS |
| **irqbalance未运行** | 中断分布完全静态 | 启动 irqbalance 服务 |
| **irqbalance策略不当** | irqbalance运行但分布仍不均 | 调整irqbalance策略或手动绑定 |
| **网卡队列数不足** | 硬中断数少于CPU数 | 增加网卡队列数 `ethtool -L` |
| **单流量大连接** | 单个连接的包量极大 | 考虑aRFS、流量分散、XDP |
| **NAPI轮询集中** | 高流量时NAPI轮询占满单CPU | 调整NAPI权重或使用多队列 |
| **中断合并参数** | 中断合并导致突发 | 调整 `ethtool -C` 参数 |

### 配置调整命令参考

```bash
# 查看/设置中断亲和性
echo <cpu_mask> > /proc/irq/<irq_num>/smp_affinity
cat /proc/irq/<irq_num>/smp_affinity_list

# 查看/设置网卡队列数
ethtool -l <eth_name>                     # 查看队列数
ethtool -L <eth_name> combined <N>        # 设置队列数

# 配置RPS（接收包导向）
echo <cpu_mask> > /sys/class/net/<eth_name>/queues/rx-<N>/rps_cpus

# 配置RFS（接收流导向）
echo <flow_entries> > /proc/sys/net/core/rps_sock_flow_entries
echo <per_queue_entries> > /sys/class/net/<eth_name>/queues/rx-<N>/rps_flow_cnt

# 查看/调整中断合并参数
ethtool -c <eth_name>                     # 查看
ethtool -C <eth_name> rx-usecs <N>        # 设置

# irqbalance管理
systemctl status irqbalance
systemctl restart irqbalance
```

## 快速排查清单

针对紧急场景的快速排查路径：

```bash
# 1. 快速确认不均衡（30秒）
mpstat -P ALL 1 3
cat /proc/softirqs

# 2. 精确统计软中断分布（持续观察）
perf-prof sql -e irq:softirq_entry -i 1000 \
  --query "SELECT _cpu, symbolic('vec', vec) as name, COUNT(*) as count FROM softirq_entry GROUP BY _cpu, vec ORDER BY vec, _cpu"

# 3. 高精度时间分布（持续观察）
perf-prof hrcount -e 'irq:softirq_entry/vec==3/' -C 0-7 --period 50ms -i 1000 --perins

# 4. 延迟对比（持续观察）
perf-prof multi-trace -e irq:softirq_entry -e irq:softirq_exit -i 1000 --perins

# 5. 热点火焰图（采样30秒）
timeout 30 perf-prof profile -F 997 -C <high_cpu> --exclude-user -g --flame-graph hotcpu.folded
flamegraph.pl hotcpu.folded > hotcpu.svg
```

## 严格约束

- 使用新的分析器时，必须先执行 `perf-prof <profiler> -h` 查看帮助
- 事件有过滤器时，`-e` 选项必须使用单引号，避免与bash运算符冲突
- hrcount 只能 Attach 到 CPU（`-C`），不能 Attach 到进程（`-p`）
- multi-trace 跨CPU事件关联需要 `--order` 选项
- top 的 key 只能是 u64 数值，复合key需要位运算组合
- 如果 perf-prof 无法安装，切换到 perf 原生命令方案，参考 [perf 替代方案](references/perf.md)

## 相关资源

- [perf-prof 项目](https://github.com/OpenCloudOS/perf-prof.git)
- [irqbalance](https://github.com/Irqbalance/irqbalance)
- [perf 替代方案](references/perf.md) - 当 perf-prof 无法安装时使用 perf 原生命令
- [示例 Prompt](references/examples.md) - 典型使用场景与触发示例
- [使用指南](references/guide.md) - 面向用户的通俗上手指南，含安装、案例与常见误区
