# 场景分析：Soft Lockup / Hard Lockup

### 必须执行的分析命令

```
# 第一步：全局 CPU 状态扫描（最高优先级！）
run_crash_commands: ["bt -a", "runq"]

# 第二步：全局状态分类统计（在分析 panic CPU 之前必须完成！）
# 统计有多少 CPU 卡在相同/相似的调用栈中
run_crash_commands: [
  "bt -a | grep -c 'native_flush_tlb_multi'",
  "bt -a | grep -c 'smp_call_function_many_cond'",
  "bt -a | grep -c 'native_queued_spin_lock_slowpath'",
  "bt -a | grep -c '_raw_spin_lock'",
  "bt -a | grep -c 'handle_softirqs'",
  "bt -a | grep -c 'call_function'",
  "bt -a | grep -c 'reschedule_interrupt'"
]

```

### 必须注意的点
- **必须理解内核Soft Lockup / Hard Lockup 实现的工作原理，并非只有死锁会导致内核Lockup**
- **必须理解内核调度优先级，包括进程优先级/软中断优先级/硬中断优先级**
- **触发panic时的堆栈是panic瞬间的，无法完全代表lockup watchdog时间周期内的真实状态，需要结合vmcore信息综合分析，包括多个cpu的堆栈分析**
- **性能问题引起的Soft Lockup / Hard Lockup，在推导出结论时你需要结合内核的调度和优先级机制确认正确性**

### ⚠️ 关键分析原则：先全局后局部，避免锚定偏差

**在 Soft Lockup / Hard Lockup 场景中，panic CPU 的调用栈只是"表象"，不一定是"根因"。必须遵循以下分析顺序：**

1. **第一步（最高优先级）：全局 CPU 状态分类**
   - 用 `foreach bt | grep -c '<关键函数>'` 统计所有 CPU 的状态分布
   - **重点关注：有多少 CPU 卡在 `native_flush_tlb_multi` / `smp_call_function_many_cond`**
   - **重点关注：有多少 CPU 卡在同一个 spinlock**
   - **重点关注：有多少 CPU 的 `call_single_queue` 有未处理的 CSD**

2. **第二步：确认因果方向**
   - 如果 panic CPU 在 softirq/hardirq 中，先检查**它是否是"受害者"而非"肇事者"**
   - **切忌把"panic CPU 正在做的事"直接等同于"导致 lockup 的原因"**

3. **第三步：才是深入 panic CPU 的局部分析**
   - **结合全局信息综合分析确认"panic CPU 正在做的事"是刚好panic时发生还是确实是"panic cpu 正在做的情"导致watchdog超时


### 排查方向（全部需要逐一排查并找证据）

#### 0. 全局 CPU 状态分析（必须最先执行）
- **统计所有 CPU 的调用栈分类**，识别是否存在大量 CPU 卡在同一位置的"群体现象"
- 如果发现大量 CPU 卡在 `smp_call_function_many_cond`（TLB flush / IPI 等待），这比 panic CPU 本身的行为更重要
- 如果发现大量 CPU 卡在同一个锁上，优先分析锁的持有者
- **高 CPU 数量的虚拟机（128+核）上，TLB flush 连锁阻塞是高频问题，必须优先排查**
- 检查 panic CPU 和卡住的 CPU 的 `call_single_queue` 中是否有未处理的 CSD

#### 1. TLB Flush / IPI 连锁阻塞（大规格机器高优先级）
- **特征**：多个 CPU 卡在 `native_flush_tlb_multi` → `smp_call_function_many_cond`，busy-wait 中断关闭（cli）
- **检查步骤**：
  1. `foreach bt | grep -c 'native_flush_tlb_multi'` — 统计受影响 CPU 数量
  2. `foreach bt | grep -B1 'smp_call_function_many_cond' | grep 'exception RIP'` — 确认全部卡在同一位置
  3. 检查 panic CPU 的 `call_single_queue` 是否有未处理的 `flush_tlb_func` CSD
  4. `rd <csd_addr> 4` — 验证 CSD 的 flag（0x11=locked）和 func（flush_tlb_func）
  5. 分析为什么 panic CPU 无法处理 IPI：在 softirq 中？关中断？vCPU 被 preempt？
- **因果链典型模式**：
  - CPU A 在 softirq 中处理包（中断开着），但 IPI 交付延迟（KVM 虚拟化）
  - CPU B/C/D... 发 TLB flush IPI 给 CPU A，在 `smp_call_function_many_cond` 中**关中断自旋等待**
  - 更多 CPU 也需要 TLB flush，目标包括已经卡住的 B/C/D...
  - **连锁反应**：越来越多 CPU 被困在关中断的 busy-wait 中
  - 最终系统大面积卡死，panic CPU 的 watchdog 超时
- **注意**：这种情况下 panic CPU 的调用栈（如 `net_rx_action`）只是"碰巧在做的事"，不是根因

#### 2. 内核死锁
- 从 vmcore 证明是否因死锁导致
- 如果是等待spinlock需要根据vmcore对应内核版本spinlock机制检查锁结构成员信息确认是有进程持有锁
- 找到锁的持有者和等待者，分析代码逻辑

#### 3. 锁竞争繁忙
- 区分死锁与锁竞争激烈
- 检查spinlock自旋锁的等待情况

#### 4. 长时间占用 CPU 的逻辑
- 检查长时间没有发生调度切换的cpu上的堆栈是否存在耗时很长的代码循环逻辑
- 从vmcore的调度信息以及cpu调用栈和代码逻辑验证

#### 5. cgroup的cpu throttle问题
- 需要排查是否因为进程所在的cgroup的cpu quota设置太小导致进程因为调度延时引发持有锁时长过长
- 需要从vmcore找证据证明没有发生死锁，而是因为持有锁的进程存在严重的调度延时引起持有锁时间过长

#### 6. 中断风暴问题
- 中断风暴(设备风暴或者IPI风暴)也会导致lockup watchdog 超时
- 从vmcore 找出可能是什么中断风暴导致的lockup watchdog超时
- 如果是IPI风暴需要结合多个cpu堆栈和per cpu积压的待处理IPI中断队列(比如call_single_queue)里的信息确认是什么IPI风暴
- watchdog触发panic的延时远超过watchdog配置的超时时间时需要重点看看hrtimer是否也存在被延时执行
- softirq软中断的优先级低于硬中断，hrtimer采用硬中断实现时，softirq软中断不会导致hrtimer被执行存在延时

#### 7. IPI 中断响应问题
- 找到相关 IPI 请求发送给了哪个/哪些 CPU
- 确认目标 CPU 是否存在未处理的 IPI
- 确认目标CPU存在未处理IPI时需要**分析未处理IPI的原因**
- 结合vmcore信息确认目标cpu是否是因为IPI风暴导致处理IPI不及时
- **必须结合上下文再检查是否还有其他CPU存在未处理的IPI**
- 对每个目标CPU，结合其中断状态和堆栈进一步分析

#### 8. 内存状态检查（条件触发，非必须）
- **前置条件判断**：在完成 `bt -a` 全局堆栈扫描后，检查是否有任一 CPU 处于内存回收相关的代码路径（如 `__alloc_pages_slowpath`、`try_to_free_pages`、`shrink_node`、`shrink_lruvec`、`do_try_to_free_pages`、`__perform_reclaim`、`__alloc_pages_direct_reclaim`、`oom_kill_process`、`out_of_memory`、`mem_cgroup_out_of_memory`、`compact_zone`、`kswapd`、`kcompactd` 等）
- **如果全局堆栈中没有任何 CPU 处于上述内存回收代码路径，则跳过内存状态检查**，直接进入下一排查方向
- **如果有 CPU 处于内存回收路径**，则执行以下检查：
  - `kmem -i` 或 `kmem -V` 获取内存使用概况
  - 检查各 zone 的 free pages 与 watermark 关系
  - 分析是否因内存紧张触发大量回收/压缩，进而导致 lockup
  - **如果确认内存紧张是导致 lockup 的原因，分析报告中必须列出以下各项内存使用量明细**：
    - 总内存 / 已用内存 / 空闲内存
    - **Slab 内存**（SReclaimable + SUnreclaim，必要时用 `kmem -s` 列出 top slab 占用）
    - **匿名内存**（AnonPages / Active(anon) / Inactive(anon)）
    - **共享内存**（Shmem，含 tmpfs / devtmpfs / shared mmap）
    - **Dirty Pages**（NR_FILE_DIRTY / Dirty）
    - **Page Cache**（Cached / Active(file) / Inactive(file)），区分 clean cache 与 dirty cache 比例
    - PageTables / KernelStack / Unevictable 等其他显著占用项
    - 各 zone 的 free pages 与 min/low/high watermark 对比
  - **如果存在较多 clean cache，必须谨慎分析**——clean cache 理论上可快速回收，大量 clean cache 存在时仍卡在回收路径是不寻常的，需排查：高阶分配碎片化、memcg 隔离限制、page 被 pin/mlock/unevictable、回收路径锁竞争等。**如果无法解释 clean cache 不能被有效回收，应质疑"内存不足"是否为真正根因**

#### 9. 内核 Bug 或规避措施
- 尝试从社区找到修复 commit
- 给出可行的规避优化措施，不限于内核参数调优或业务层面的调优
- 如果是内核调优，给出具体调整内核配置的命令以及调整对应参数含义
- **⚠️ 建议调整参数前，必须先从 vmcore 读取当前值，以"当前值→建议值"对比呈现，当前值已等于建议值时不输出该建议**
- **🔴 每条参数建议必须通过因果有效性验证**：论证修改该参数能从原理上解决或缓解根因，且在当前系统配置下不会引入新问题。无法通过验证的建议不得出现在报告中。**如果根因非内核参数可调，则不需要给出内核参数建议**
- 业务层面调优需给出**触发问题的具体进程**，以及业务是如何触发的，应该如何优化或者规避
- **⚠️ 描述触发方式时必须区分"系统默认行为"与"进程主动请求"**（如 THP madvise 模式下是进程主动请求，不是系统自动触发）

#### 10. 虚拟机 vCPU 问题
这部分无相关mcp可用时可以不做真正的检查，但对于从vmcore分析推测跟虚拟化相关，需要列出推理依据
- **vCPU 长时间不工作会导致子机内核出现soft/hard lockup**
- **vCPU退出到宿主机后长时间未返回导致子机对应cpu出现无响应引起soft/hard lockup**
- 单次VM EXIT正常情况下不会耗时很长，如果从vmcore分析出现单次VM EXIT耗时超秒级时需要严谨分析是否虚拟化问题
- 如果怀疑子机因为某些短时间的风暴事件触发的虚拟化瓶颈，应该严谨确认在Panic前10秒平均每秒产生的异常事件是否确实较多
- 检查cpu当前运行进程是idle进程且未关闭中断，但是cpu运行队列有待调度的进程较长时间未得到调度运行需要关注是否虚拟化问题
- 检查TSC偏移或者某些cpu的时钟计数是否长时间未更新等
