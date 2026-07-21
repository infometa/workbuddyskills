# 场景分析：Hung Task Watchdog

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
- **🔴 每条参数建议必须通过因果有效性验证**：论证修改该参数能从原理上解决或缓解根因，且在当前系统配置下不会引入新问题。无法通过验证的建议不得出现在报告中
- 如果是业务层面调优，**给出触发问题的具体进程**

#### 10. 非内核 Bug
- 给出可行的规避措施（内核调优或业务层面调优）
- 如果是内核调优，给出具体调整内核配置的命令以及调整对应参数含义
- **⚠️ 建议调整参数前，必须先从 vmcore 读取当前值，以"当前值→建议值"对比呈现，当前值已等于建议值时不输出该建议**
- **🔴 每条参数建议必须通过因果有效性验证**：论证修改该参数能从原理上解决或缓解根因，且在当前系统配置下不会引入新问题。**如果根因是业务配置问题且不存在有效的内核参数可调整，则不需要给出内核参数建议——宁缺毋滥**
- 如果是业务层面调优，**给出触发问题的具体进程**，以及业务如何调整的具体建议

#### ⚠️ Hung Task 场景 `hung_task_panic` 参数处理规则
- **如果从 vmcore 读取到 `hung_task_panic` 当前值已经为 1**：无需额外提醒或建议修改，维持现状即可
- **如果从 vmcore 读取到 `hung_task_panic` 当前值为 0**：**禁止**在分析报告中建议开启 `kernel.hung_task_panic=1`，不得主动推荐该配置
- **仅当用户主动询问是否可以开启 `hung_task_panic`** 时，才进行回复，且必须明确说明风险：该参数会在 hung task 检测触发时直接 panic 导致系统重启，而单个进程有时进入 D 状态时并不会直接影响业务运行，开启后可能因单个进程的短暂 D 状态引发整个系统意外重启
