# 场景分析指南

本文档包含各种 vmcore 场景的详细分析流程和排查方向。

---

## 场景一：Hung Task Watchdog

### 必须执行的分析命令

```
# 基础排查
run_crash_commands: ["bt -a", "ps -m", "ps | grep ' UN '", "log | grep -i hung", "log | grep 'blocked for more than'"]

# 锁相关
run_crash_commands: ["foreach UN bt",  "files <hung_task_pid>"]

# 进程D状态持续时长分析
run_crash_command: "ps -l | grep ' UN '"  （检查D状态进程最后一次运行的时间戳）
run_crash_command: "log | grep panic"  （检查机器panic瞬间的时间戳）
```

### 排查方向（全部需要逐一排查并找证据）

#### 1. 确认是否真正长时间 D 状态
- 进程短暂 D 状态可能不是问题
- **必须找到证据证明有进程持续 D 住超过 10 秒**
- 使用 `ps -l` 或 `task_struct`查看D状态最久的进程最近一次运行的时间戳跟`log | grep panic`获取panic时的时间戳对比验证

#### 2. 内核死锁
- 找到 hung 进程在等待的锁
- 找到**持有锁的 CPU 上的进程**
- **结合 vmcore 和源码从代码逻辑上找到不释放锁的原因**
- 常用命令：`bt <pid>`、检查 `mutex`/`rwsem`/`spinlock` 的 owner 字段,检查锁等待队列情况

#### 3. 锁竞争繁忙
- 区分死锁与锁竞争激烈
- 检查**持有锁的 CPU 上的进程**已经持续D住超过多长时间，排除是panic前刚好获取到锁的情况

#### 4. 内存耗尽（条件触发，非必须）
- **前置条件判断**：先通过 `bt -a` 全局堆栈检查是否有 CPU 处于内存回收相关代码路径（如 `__alloc_pages_slowpath`、`try_to_free_pages`、`shrink_node`、`shrink_lruvec`、`do_try_to_free_pages`、`__perform_reclaim`、`__alloc_pages_direct_reclaim`、`oom_kill_process`、`out_of_memory`、`mem_cgroup_out_of_memory`、`compact_zone`、`kswapd`、`kcompactd` 等）。**如果全局堆栈中没有任何 CPU 处于上述内存回收代码路径，则跳过本项内存状态检查**
- 如果全局堆栈有 CPU 卡在内存回收上，需要重点排查是否内存紧张导致系统卡慢
- 排查是否存在内存碎片原因导致机器hung住
- 列出内存占用分布信息
- **如果确认内存紧张是导致 hung 的原因，分析报告中必须列出以下各项内存使用量明细**：
  - 总内存 / 已用内存 / 空闲内存
  - **Slab 内存**（可回收 SReclaimable + 不可回收 SUnreclaim，必要时用 `kmem -s` 列出 top slab 占用）
  - **匿名内存**（AnonPages / Active(anon) / Inactive(anon)）
  - **共享内存**（Shmem，包含 tmpfs / devtmpfs / shared mmap）
  - **Dirty Pages**（NR_FILE_DIRTY / Dirty）
  - **Page Cache**（Cached / Active(file) / Inactive(file)），重点区分 clean cache 与 dirty cache 的比例
  - PageTables / KernelStack / Bounce / Unevictable 等其他显著占用项
  - 各 zone 的 free pages 与 min/low/high watermark 对比
- **需要分析列出cache内存组成占比**，重点关注 clean cache 与 dirty cache 的比例
- **如果存在较多 clean cache，必须谨慎分析**——clean cache 理论上可以被快速回收，大量 clean cache 存在时系统仍然卡在内存回收路径是不寻常的，需要从以下方面深入排查并给出明确解释：
  - 是否是高阶（order≥1）内存分配失败导致的 compaction 卡住，而非真正的内存不足（clean cache 多但碎片化严重）
  - 是否存在 memcg 限制导致 cgroup 内部内存不足，但全局 clean cache 属于其他 cgroup 无法被回收
  - 是否存在大量 page 被 pin/mlock/unevictable 标记，虽统计为 cache 但实际不可回收
  - 是否是回收路径本身的锁竞争或代码逻辑缺陷导致回收效率低下
  - **如果无法从 vmcore 中找到 clean cache 不能被有效回收的合理解释，应质疑"内存耗尽"是否真的是根因**，转而排查其他可能性（如锁竞争、IO 阻塞等）
- **注意**：一般内存耗尽会触发 OOM Kill 而非 hung，需要从 vmcore 和代码逻辑分析证明确实是内存耗尽引起

#### 5. IO 压力导致
- **必须从 vmcore 证明 IO 队列确实存在大量 IO 长时间积压**
- 找出 IO 等待队列里**等待时间最长的请求**，计算截止到 panic 时已等待的时长
- **关键验证**：区分请求是"长时间未响应"还是"panic 前瞬间刚发送出去"
  - 例如：NFS 请求可能只是 panic 前一瞬间刚发送，并非长时间未响应
  - 需要通过时间戳对比验证
- 确定是哪个盘、是读 IO 还是写 IO
- 验证是否因内存不足引起的 IO 压力

#### 6. 存储问题
- 如果某个 IO 请求长时间无响应，结合内核 IO 下发原理找证据
- 确认具体是哪个存储（云盘/NFS/其他）存在问题
- 给出明确的存储排查建议

#### 7. cgroup的cpu throttle问题
- 需要排查是否因为进程所在的cgroup的cpu quota设置太小导致进程因为获取不到锁导致持有锁时长过长
- 需要从vmcore找证据证明没有发生死锁，而是因为持有锁的进程存在严重的调度延时引起持有锁时间过长

#### 8. 虚拟化环境
这部分无相关mcp可用时可以不做真正的检查，但对于逻辑推到存在该可能性导致的，可以列出来推理依据

- 如果是虚拟机，分析是否可能是虚拟化层面或者宿主机问题
- 检查 vCPU 是否存在无响应情况,结合代码逻辑以及当前cpu进程的调用栈以及cpu 运行队列情况等因素综合排查
- 通过vmcore分析如果怀疑是虚拟化或者宿主机问题应该给出明确建议进一步排查虚拟化和宿主机

#### 9. 内核 Bug
- 尝试从社区找到修复 commit
- 给出可行的规避措施（内核调优或业务层面调优）
- 如果是内核调优，给出具体调整内核配置的命令以及调整对应参数含义
- **⚠️ 建议调整参数前，必须先从 vmcore 读取当前值，以"当前值→建议值"对比呈现，当前值已等于建议值时不输出该建议**
- 如果是业务层面调优，**给出触发问题的具体进程**

#### 10. 非内核 Bug
- 给出可行的规避措施（内核调优或业务层面调优）
- 如果是内核调优，给出具体调整内核配置的命令以及调整对应参数含义
- **⚠️ 建议调整参数前，必须先从 vmcore 读取当前值，以"当前值→建议值"对比呈现，当前值已等于建议值时不输出该建议**
- 如果是业务层面调优，**给出触发问题的具体进程**，以及业务如何调整的具体建议

#### ⚠️ Hung Task 场景 `hung_task_panic` 参数处理规则
- **如果从 vmcore 读取到 `hung_task_panic` 当前值已经为 1**：无需额外提醒或建议修改，维持现状即可
- **如果从 vmcore 读取到 `hung_task_panic` 当前值为 0**：**禁止**在分析报告中建议开启 `kernel.hung_task_panic=1`，不得主动推荐该配置
- **仅当用户主动询问是否可以开启 `hung_task_panic`** 时，才进行回复，且必须明确说明风险：该参数会在 hung task 检测触发时直接 panic 导致系统重启，而单个进程有时进入 D 状态时并不会直接影响业务运行，开启后可能因单个进程的短暂 D 状态引发整个系统意外重启
---

## 场景二：Soft Lockup / Hard Lockup

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

---

## 场景三：BUG_ON / NULL 指针 / 异常地址访问

### 必须执行的分析命令

```
run_crash_commands: ["bt -l", "bt -f", "dis -l <fault_function>", "log | grep -i bug", "log | grep -i rip"]

# 检查故障地址
run_crash_commands: ["vm <pid>", "kmem <fault_address>", "rd <stack_area> <length>"]
```

### 排查方向

#### 1. 定位故障代码
- 从 `bt -l` 获取源码行号
- 使用 `dis -l` 反汇编故障函数
- 排查是否是第三方内核模块导致
- 排查是否存在病毒模块
- 结合源码分析触发条件

#### 2. 区分硬件问题与软件问题
- 检查是否有 MCE（Machine Check Exception）记录
- 检查内存错误信息：`log | grep -i mce`、`log | grep -i hardware`
- 如果是硬件问题给出硬件排查建议

#### 3. 内核代码问题
- 分析触发 BUG_ON 的条件在代码中如何被满足
- 尝试从社区找出相关修复 commit
- 使用 `search_knowledge_base` 搜索已知问题

---

## 场景四：SysRq 触发 / virsh dump

### 分析步骤

1. 确认是否因机器宕机无响应而触发的 SysRq/virsh dump
2. 如果是无响应，按照以下优先级分析：
   - 检查是否存在 soft/hard lockup（参考场景二）
   - 检查是否存在 hung task（参考场景一）
   - 检查内存状态
   - 检查各 CPU 上的进程状态：`bt -a`、`runq`
