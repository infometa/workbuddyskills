# 软中断/硬中断不均衡排查

## 概述

中断不均衡是指系统中各CPU处理的中断数量差异显著，导致部分CPU负载过高，影响整体性能。本技能提供系统化的排查流程，从发现不均衡到定位根因。

### 常见症状

- 部分CPU的 `si`（软中断）或 `hi`（硬中断）占比显著高于其他CPU
- 网络收发性能不稳定，部分网卡队列负载集中
- `ksoftirqd/N` 线程在某些CPU上CPU占用高
- 系统整体吞吐未达预期，但部分CPU已满载

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
   参考 [FlameGraph 工具安装指南](flamegraph-install.md) 进行安装和验证。

## 排查流程总览

```
第一步：初步诊断（系统工具确认问题）
  │
  ▼
第二步：中断分布统计（定量确认不均衡）
  │  ├── 2.1 硬中断分布 → perf stat / perf record + perf script + awk
  │  ├── 2.2 软中断分布 → perf stat / perf record + perf script + awk
  │  └── 2.3 按CPU×中断类型交叉统计
  │
  ▼
第三步：时间维度突发检测（定位时间窗口）
  │  └── perf stat -I（周期性计数）
  │
  ▼
第四步：延迟影响分析（量化不均衡的影响）
  │  └── perf record + perf script + 脚本计算延迟
  │
  ▼
第五步：热点定位（找到根因代码路径）
  │  └── perf record + FlameGraph 火焰图
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

使用 perf 精确统计中断在各CPU上的分布。

### 2.1 硬中断分布统计

**方法A：使用 perf stat 按CPU统计硬中断总数**
```bash
# 按CPU分别统计硬中断次数（每秒输出）
perf stat -e irq:irq_handler_entry -a -A -I 1000
```
输出示例：
```
#  time    CPU    counts unit events
 1.000     CPU0   12345      irq:irq_handler_entry
 1.000     CPU1    8901      irq:irq_handler_entry
 1.000     CPU2     234      irq:irq_handler_entry
```
**解读**：各CPU的硬中断计数差异反映了不均衡程度。

**方法B：使用 perf record + perf script 按中断号×CPU交叉统计**
```bash
# 采集硬中断事件（10秒）
perf record -e irq:irq_handler_entry -a -o irq.data -- sleep 10

# 按CPU和中断号交叉统计
perf script -i irq.data | awk '{
    # 提取CPU号和irq号
    for(i=1;i<=NF;i++) {
        if($i ~ /^\[/) cpu=$i
        if($i ~ /^irq=/) irq=$i
        if($i ~ /^name=/) name=$i
    }
    key=cpu" "irq" "name
    count[key]++
}
END {
    for(k in count) print count[k], k
}' | sort -rn | head -30
```

**方法C：使用 perf script 查看每个中断的详细信息**
```bash
# 直接查看原始事件
perf script -i irq.data | head -50
```

### 2.2 软中断分布统计

**方法A：使用 perf stat 按CPU统计软中断总数**
```bash
# 按CPU分别统计软中断次数（每秒输出）
perf stat -e irq:softirq_entry -a -A -I 1000
```

**方法B：按CPU×软中断类型交叉统计**
```bash
# 采集软中断事件（10秒）
perf record -e irq:softirq_entry -a -o softirq.data -- sleep 10

# 按CPU和向量号统计
perf script -i softirq.data | awk '{
    for(i=1;i<=NF;i++) {
        if($i ~ /^\[/) cpu=$i
        if($i ~ /^vec=/) vec=$i
    }
    key=cpu" "vec
    count[key]++
}
END {
    for(k in count) print count[k], k
}' | sort -rn
```

**方法C：只统计网络相关软中断**
```bash
# 采集NET_TX(vec=1)和NET_RX(vec=3)
perf record -e irq:softirq_entry --filter 'vec == 1 || vec == 3' -a -o net_softirq.data -- sleep 10

# 按CPU和类型统计
perf script -i net_softirq.data | awk '{
    for(i=1;i<=NF;i++) {
        if($i ~ /^\[/) cpu=$i
        if($i ~ /^vec=/) vec=$i
    }
    key=cpu" "vec
    count[key]++
}
END {
    for(k in count) print count[k], k
}' | sort -rn
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

使用 perf stat 的周期性输出观察中断的时间分布，发现突发和波动。

### 3.1 硬中断时间分布

```bash
# 各CPU硬中断计数（每秒输出，按CPU分别统计）
perf stat -e irq:irq_handler_entry -a -A -I 1000

# 更短间隔（500ms），观察突发
perf stat -e irq:irq_handler_entry -a -A -I 500

# 只观察特定CPU
perf stat -e irq:irq_handler_entry -C 0-7 -A -I 1000
```
输出示例：
```
#  time    CPU    counts unit events
 1.000     CPU0    655      irq:irq_handler_entry
 1.000     CPU1     62      irq:irq_handler_entry
 2.000     CPU0    670      irq:irq_handler_entry
 2.000     CPU1     58      irq:irq_handler_entry
```
**解读**：CPU0每秒约660次硬中断，CPU1仅约60次，差距约10倍。

### 3.2 软中断时间分布

```bash
# 各CPU软中断计数（每秒输出）
perf stat -e irq:softirq_entry -a -A -I 1000

# 只看网络收包软中断（NET_RX=3）
perf stat -e irq:softirq_entry --filter 'vec == 3' -a -A -I 1000

# 只看网络发包软中断（NET_TX=1）
perf stat -e irq:softirq_entry --filter 'vec == 1' -a -A -I 1000
```

### 3.3 对比硬中断和软中断

```bash
# 同时观察硬中断和软中断
perf stat -e irq:irq_handler_entry -e irq:softirq_entry -a -A -I 1000
```

### 3.4 更高精度分析

```bash
# 100ms间隔，观察更细粒度的波动
perf stat -e irq:softirq_entry --filter 'vec == 3' -a -A -I 100

# 注意：perf stat -I 的最小间隔一般为 100ms
# 如需更高精度（毫秒/微秒级），需要使用 perf record + perf script 后处理
```

**毫秒级精度方案（使用 perf record 后处理）：**
```bash
# 采集带时间戳的原始事件
perf record -e irq:softirq_entry --filter 'vec == 3' -a -o softirq_ts.data -- sleep 10

# 按50ms时间窗口统计各CPU的事件数
perf script -i softirq_ts.data -F cpu,time | awk '{
    cpu=$1; t=$2
    # 按50ms窗口分组
    window=int(t*1000/50)*50
    key=cpu" "window
    count[key]++
}
END {
    for(k in count) print k, count[k]
}' | sort -k2 -n
```

## 第四步：延迟影响分析

使用 perf record 采集软中断的 entry/exit 事件，通过 perf script 后处理计算延迟。

### 4.1 软中断处理延迟（按CPU统计）

```bash
# 采集软中断entry和exit事件
perf record -e irq:softirq_entry -e irq:softirq_exit -a -o softirq_lat.data -- sleep 10

# 计算每次软中断的处理延迟（按CPU统计）
perf script -i softirq_lat.data -F cpu,time,event,trace | awk '
/softirq_entry/ {
    cpu=$1; t=$2
    entry[cpu]=t
}
/softirq_exit/ {
    cpu=$1; t=$2
    if(entry[cpu] > 0) {
        lat = (t - entry[cpu]) * 1000000  # 转换为微秒
        count[cpu]++
        total[cpu] += lat
        if(lat > max[cpu]) max[cpu] = lat
        if(min[cpu] == 0 || lat < min[cpu]) min[cpu] = lat
        entry[cpu] = 0
    }
}
END {
    printf "%-5s %8s %12s %12s %12s\n", "CPU", "calls", "avg(us)", "min(us)", "max(us)"
    printf "%-5s %8s %12s %12s %12s\n", "-----", "--------", "------------", "------------", "------------"
    for(cpu in count) {
        avg = total[cpu] / count[cpu]
        printf "%-5s %8d %12.3f %12.3f %12.3f\n", cpu, count[cpu], avg, min[cpu], max[cpu]
    }
}'
```
**解读**：对比各CPU的软中断处理次数和延迟（avg/min/max），确认不均衡影响。

### 4.2 按软中断类型分析延迟

```bash
# 只分析NET_RX软中断延迟
perf record -e irq:softirq_entry --filter 'vec == 3' \
            -e irq:softirq_exit --filter 'vec == 3' \
            -a -o netrx_lat.data -- sleep 10

# 使用同样的awk脚本计算延迟
perf script -i netrx_lat.data -F cpu,time,event,trace | awk '
/softirq_entry/ { cpu=$1; entry[cpu]=$2 }
/softirq_exit/ {
    cpu=$1
    if(entry[cpu] > 0) {
        lat = ($2 - entry[cpu]) * 1000000
        count[cpu]++; total[cpu] += lat
        if(lat > max[cpu]) max[cpu] = lat
        if(min[cpu] == 0 || lat < min[cpu]) min[cpu] = lat
        entry[cpu] = 0
    }
}
END {
    printf "%-5s %8s %12s %12s %12s\n", "CPU", "calls", "avg(us)", "min(us)", "max(us)"
    for(cpu in count) printf "%-5s %8d %12.3f %12.3f %12.3f\n", cpu, count[cpu], total[cpu]/count[cpu], min[cpu], max[cpu]
}'
```

### 4.3 大延迟事件详细查看

```bash
# 导出原始事件，手动查看大延迟
perf script -i softirq_lat.data -F cpu,time,event,trace | awk '
/softirq_entry/ { cpu=$1; entry_time[cpu]=$2; entry_line[cpu]=$0 }
/softirq_exit/ {
    cpu=$1
    if(entry_time[cpu] > 0) {
        lat = ($2 - entry_time[cpu]) * 1000000
        if(lat > 50) {  # 阈值：50微秒
            print "LATENCY:", lat, "us"
            print "  ENTRY:", entry_line[cpu]
            print "  EXIT: ", $0
            print ""
        }
        entry_time[cpu] = 0
    }
}'
```

### 4.4 硬中断处理延迟

```bash
# 采集硬中断entry和exit事件
perf record -e irq:irq_handler_entry -e irq:irq_handler_exit -a -o hirq_lat.data -- sleep 10

# 计算延迟（按CPU统计）
perf script -i hirq_lat.data -F cpu,time,event,trace | awk '
/irq_handler_entry/ { cpu=$1; entry[cpu]=$2 }
/irq_handler_exit/ {
    cpu=$1
    if(entry[cpu] > 0) {
        lat = ($2 - entry[cpu]) * 1000000
        count[cpu]++; total[cpu] += lat
        if(lat > max[cpu]) max[cpu] = lat
        if(min[cpu] == 0 || lat < min[cpu]) min[cpu] = lat
        entry[cpu] = 0
    }
}
END {
    printf "%-5s %8s %12s %12s %12s\n", "CPU", "calls", "avg(us)", "min(us)", "max(us)"
    for(cpu in count) printf "%-5s %8d %12.3f %12.3f %12.3f\n", cpu, count[cpu], total[cpu]/count[cpu], min[cpu], max[cpu]
}'
```

## 第五步：热点定位

使用 perf record 采样负载高的CPU上的热点代码路径，生成火焰图。

### 5.1 采样高负载CPU的热点

```bash
# 采样特定CPU（选择中断负载高的CPU）
perf record -F 997 -g -C <high_irq_cpu> -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > irq_cpu.folded
flamegraph.pl irq_cpu.folded > irq_cpu.svg
```

### 5.2 只采样内核态热点（软中断在内核态执行）

```bash
# 采样所有CPU的内核态热点
perf record -F 997 -g --exclude-user -a -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > kernel.folded
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
perf record -F 997 -g -p <ksoftirqd_pid> -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > ksoftirqd.folded
flamegraph.pl ksoftirqd.folded > ksoftirqd.svg
```

### 5.4 软中断调用栈火焰图

```bash
# 直接跟踪软中断entry事件的调用栈
perf record -e irq:softirq_entry -g -a -m 64 -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > softirq.folded
flamegraph.pl --title "Softirq Entry Call Stacks" softirq.folded > softirq.svg

# 只跟踪NET_RX软中断
perf record -e irq:softirq_entry --filter 'vec == 3' -g -a -m 64 -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl > netrx.folded
flamegraph.pl --title "NET_RX Softirq" netrx.folded > netrx.svg
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
perf stat -e irq:softirq_entry -a -A -I 1000

# 3. 按软中断类型分别统计（采集10秒后分析）
perf record -e irq:softirq_entry -a -o softirq.data -- sleep 10
perf script -i softirq.data | awk '{for(i=1;i<=NF;i++){if($i~/^\[/)cpu=$i;if($i~/^vec=/)vec=$i} count[cpu" "vec]++} END{for(k in count) print count[k],k}' | sort -rn

# 4. 延迟对比（采集10秒后分析）
perf record -e irq:softirq_entry -e irq:softirq_exit -a -o lat.data -- sleep 10
perf script -i lat.data -F cpu,time,event | awk '/entry/{cpu=$1;e[cpu]=$2}/exit/{if(e[$1]>0){l=($2-e[$1])*1e6;c[$1]++;t[$1]+=l;if(l>m[$1])m[$1]=l;e[$1]=0}}END{for(k in c)printf "CPU%-3s calls=%-6d avg=%.1fus max=%.1fus\n",k,c[k],t[k]/c[k],m[k]}'

# 5. 热点火焰图（采样30秒）
perf record -F 997 -g -C <high_cpu> --exclude-user -o perf.data -- sleep 30
perf script -i perf.data | stackcollapse-perf.pl | flamegraph.pl > hotcpu.svg
```

## 严格约束

- 生成火焰图必须使用 `-g` 选项启用调用栈记录
- 高频事件需要增大 `-m` 参数避免数据丢失
- tracepoint 过滤器使用 `--filter` 选项
- `perf record` 多次采集需用 `-o` 指定不同文件名避免覆盖
- `perf stat -I` 的最小间隔一般为 100ms，更高精度需要 perf record + 后处理
- 需要 root 权限或 `kernel.perf_event_paranoid` 设置为 -1

## 相关资源

- [perf wiki](https://perf.wiki.kernel.org/)
- [FlameGraph 工具集](https://github.com/brendangregg/FlameGraph)
- [irqbalance](https://github.com/Irqbalance/irqbalance)
