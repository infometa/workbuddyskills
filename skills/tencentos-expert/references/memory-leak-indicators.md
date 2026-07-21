# 内存泄漏判定指标与知识库

本文件为 `parse_memory_leak.py` 提供判定规则和背景知识，供 AI 分析时参考.

---

## 一、关键指标说明

### 进程级指标（来源: `/proc/<pid>/status`）

| 指标 | 说明 | 泄漏信号 |
|------|------|---------|
| `VmRSS` | 当前物理内存驻留大小（含共享页） | 持续增长且不回落 |
| `VmAnon` | 匿名内存（堆+栈，纯私有） | 持续增长是堆泄漏的核心信号 |
| `VmPeak` | 历史 RSS 峰值 | `VmPeak >> VmRSS` 说明曾泄漏后被回收；`VmPeak ≈ VmRSS` 说明从未回落 |
| `VmSize` | 虚拟地址空间大小 | 远大于 VmRSS 说明有大量虚拟映射未实际使用（不一定是泄漏） |

### 进程级指标（来源: `/proc/<pid>/smaps_rollup` 或 `smaps`）

| 指标 | 说明 | 泄漏信号 |
|------|------|---------|
| `Pss` | 按比例分摊共享页后的实际内存占用 | 比 VmRSS 更准确，持续增长即异常 |
| `Private_Dirty` | 私有脏页（已写入且不共享） | 堆泄漏时此值持续增长 |
| `Heap` | 堆段大小（smaps 中 `[heap]` 项的 Size） | 持续增长说明 malloc arena 在扩张 |

### 全局内存指标（来源: `/proc/meminfo`）

| 指标 | 说明 | 泄漏信号 |
|------|------|---------|
| `AnonPages` | 全局匿名内存总量 | 与目标进程 VmAnon 趋势吻合时确认泄漏归属 |
| `Slab` | 内核 slab 缓存总量 | 持续增长且 `SReclaimable` 不增长，说明内核对象泄漏 |
| `SUnreclaim` | 不可回收 slab | 持续增长是内核泄漏的强信号 |
| `Committed_AS` | 已承诺虚拟内存 | 远超物理内存时，任何 malloc 失败都可能触发 OOM |
| `MemAvailable` | 当前可用内存（内核估算） | 与 OOM 预测直接相关 |

---

## 二、泄漏判定规则

### 规则 1：增长速率判定（主规则）

```
growth_rate = (rss_last - rss_first) / elapsed_minutes

verdict:
  > 5%/min  → leak_confirmed（确认泄漏）
  1%~5%/min → leak_suspected（疑似泄漏）
  ≤ 1%/min  → normal（正常波动）
```

**注意**: 增长速率需结合绝对增量判断:
- 速率 3%/min 但绝对增量只有 1MB → 可能是正常启动期波动，降级为 normal
- 速率 0.5%/min 但绝对增量超过 500MB/h → 应升级为 suspected

### 规则 2：单调性判定（辅助规则）

若所有采样点的 RSS 均单调递增（无任何回落），则置信度 +1 级:
- `normal` → `leak_suspected`
- `leak_suspected` → `leak_confirmed`

若 RSS 有明显回落（下降超过 5%），则置信度 -1 级.

### 规则 3：文件描述符泄漏

若目标进程 `fd_count > 1000`，追加告警:
```
"文件描述符数量异常: <fd_count>（> 1000），可能存在 fd 泄漏"
```

### 规则 4：内核 slab 泄漏

若 `/proc/meminfo` 中 `SUnreclaim > 500MB`，追加告警:
```
"内核不可回收 slab 内存过高: <SUnreclaim>MB，可能存在内核对象泄漏，建议检查 /proc/slabinfo"
```

---

## 三、OOM 预测算法

```
available_kb = MemAvailable（来自 /proc/meminfo，采集最后一次）
growth_rate_kb_per_min = rss 增长速率（KB/min）

if growth_rate_kb_per_min > 0:
    eta_minutes = available_kb / growth_rate_kb_per_min
    eta_human = 友好格式（分钟/小时/天）
else:
    eta_minutes = null（内存未增长，无法预测）
```

**免责说明**: OOM 预测基于线性外推，仅供参考，实际受 swap、内存碎片、其他进程竞争等因素影响.

---

## 四、eBPF 调用栈解读

当 `memleak` 工具可用时，输出格式为:

```
[12:00:01] Top 10 stacks with outstanding allocations:
    <未释放字节数> bytes in <分配次数> allocations from stack:
        malloc+0x...
        myapp!allocate_buffer+0x...
        myapp!process_request+0x...
```

关键字段:
- 未释放字节数持续增长的栈 → 泄漏根因
- `malloc` / `calloc` / `realloc` 之上的调用帧 → 业务代码位置

---

## 五、常见泄漏场景

| 场景 | 信号 | 处置建议 |
|------|------|---------|
| **业务堆泄漏（C/C++）** | VmAnon 持续增长，eBPF 有固定调用栈 | 代码审查 malloc/free 对，使用 Valgrind 复现 |
| **Java/JVM 内存泄漏** | RSS 增长但 JVM GC 日志无 Full GC；或 Full GC 后内存不回落 | 使用 jmap -histo 分析堆对象，查找 classloader/listener 泄漏 |
| **内存碎片（非泄漏）** | VmRSS 高但进程逻辑内存使用合理 | 使用 jemalloc/tcmalloc 替换 glibc malloc，或通过 malloc_trim() 归还碎片 |
| **文件描述符泄漏** | fd_count 持续增长，RSS 正常 | `lsof -p <pid>` 查看泄漏的文件类型，审查 close() 调用 |
| **内核 slab 泄漏** | SUnreclaim 增长，用户态进程 RSS 正常 | `slabtop` 定位增长最快的 slab 类型，联系内核团队 |
