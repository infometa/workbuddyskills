# 场景分析：OOM 内存耗尽无可杀进程（System is deadlocked on memory）

### 场景特征

内核日志出现以下标志性信息：
```
Out of memory and no killable processes...
Kernel panic - not syncing: System is deadlocked on memory
```

这是内核 OOM Killer 被触发后，扫描所有进程发现**没有任何可以被杀死的进程**来释放内存，导致系统陷入内存死锁并主动 panic。

### 必须执行的分析命令

```
# 第一步：基础信息和 panic 调用栈
run_crash_commands: ["bt", "bt -a", "log | tail -200"]

# 第二步：内存全局状态
run_crash_commands: ["kmem -i", "kmem -V", "kmem -z"]

# 第三步：OOM 相关日志
run_crash_commands: ["log | grep -i 'out of memory'", "log | grep -i 'oom'", "log | grep -i 'killed process'", "log | grep -i 'invoked oom'"]

# 第四步：进程状态
run_crash_commands: ["ps -m", "ps | grep ' UN '", "ps -G"]

# 第五步：Slab 内存详情（如果 Slab 占用显著）
run_crash_command: "kmem -s"

# 第六步：OOM 参数
run_crash_commands: ["sysctl vm.overcommit_memory", "sysctl vm.overcommit_ratio", "sysctl vm.panic_on_oom", "sysctl vm.oom_kill_allocating_task"]
```

### 排查方向（全部需要逐一排查并找证据）

#### 0. 前置判断：是否伴随 hung task 或 lockup

**在进入后续 OOM 专项分析之前，必须先检查系统是否同时存在 hung task 或 lockup 现象。**

- 检查 `log` 中是否存在 "blocked for more than"、"soft lockup"、"hard lockup" 等告警
- 检查 `ps | grep ' UN '` 是否有大量 D 状态进程
- 检查 `bt -a` 中是否有进程卡在内存回收相关路径（如 `shrink_node`、`shrink_slab`、`balance_pgdat`、`__alloc_pages_slowpath`等），或卡在锁等待路径

**如果确认伴随 hung task 或 lockup，按以下方式处理：**

- **存在 hung task**（大量 D 状态进程、"blocked for more than" 告警）：读取 [`reference/scenario_hung_task.md`](reference/scenario_hung_task.md)，按其排查流程分析 D 状态进程的阻塞原因
- **存在 soft lockup 或 hard lockup**：读取 [`reference/scenario_lockup.md`](reference/scenario_lockup.md)，按其排查流程分析 lockup 的根因

**⚠️ 注意区分因果关系**：OOM 和 hung/lockup 可能互为因果——hung/lockup 可能阻塞内存回收导致 OOM，反过来内存紧张也可能引发进程阻塞和 lockup。必须从 vmcore 中分析时间线和调用栈，判断谁是因谁是果。

**如果不存在 hung task 和 lockup 现象，继续以下 OOM 专项排查：**

#### 1. 确认 panic 触发路径

- 从 `bt` 确认 panic 调用栈经过 `out_of_memory` → `__alloc_pages_slowpath` 或类似路径
- 从 `log` 确认在 panic 之前是否有 OOM Killer 尝试杀进程的记录
- 确认是**全局 OOM** 还是 **memcg OOM**（cgroup 内存限制触发）：
  - 全局 OOM：调用链中有 `out_of_memory` 但无 `mem_cgroup_out_of_memory`
  - memcg OOM：调用链中有 `mem_cgroup_out_of_memory`，需要进一步确认是哪个 cgroup 触发

#### 2. 分析为什么没有可杀进程

OOM Killer 认为"没有可杀进程"通常由以下原因之一导致，**必须从 vmcore 找到具体原因**：

- **所有进程的 `oom_score_adj` 设为 -1000**：被标记为 OOM 豁免
  ```
  # 检查进程的 oom_score_adj
  ps -A   # 列出所有进程，逐一检查关键进程的 task_struct 中 signal->oom_score_adj
  ```
- **进程处于不可杀状态**：内核态进程（kthread）和 init 进程（pid=1）默认不可被 OOM Kill
- **memcg 限制场景**：cgroup 内的进程都已退出或都被标记为不可杀，但 cgroup 的 memory.limit_in_bytes 仍然锁住内存
- **所有用户进程已经退出**：系统中只剩内核线程

#### 3. 内存使用明细分析

**必须在报告中列出完整的内存使用分布**：

- 总内存 / 已用内存 / 空闲内存
- **Slab 内存**（SReclaimable + SUnreclaim）
  - 如果 Slab 占比显著，用 `kmem -s` 列出 top 10 占用最大的 slab cache
- **匿名内存**（AnonPages / Active(anon) / Inactive(anon)）
- **共享内存**（Shmem，包含 tmpfs / devtmpfs / shared mmap）
- **Page Cache**（Cached / Active(file) / Inactive(file)），区分 clean cache 与 dirty cache 比例
- **Dirty Pages**（NR_FILE_DIRTY / Dirty）
- PageTables / KernelStack / Bounce / Unevictable / HugePages 等其他显著占用项
- 各 zone 的 free pages 与 min/low/high watermark 对比
- **如果存在 HugePages 预留，必须单独列出**——HugePages 预留会锁定大块内存不参与普通分配

#### 4. 判断内存耗尽的主要消耗方：内核态 vs 用户态

**这是最关键的分析步骤，必须先判断内存主要被谁消耗，再按对应方向深入分析。**

根据第 3 步获取的内存使用明细，将内存消耗分为两大类并计算各自占比：

- **内核态内存**：Slab（SReclaimable + SUnreclaim）+ PageTables + KernelStack + vmalloc + Bounce 等
- **用户态内存**：AnonPages（匿名内存）+ Shmem（共享内存）+ 用户进程的 Page Cache 占用

**根据占比判断主因后，进入对应的子方向：**

##### 4a. 内核态内存占用主导 → 排查内核/内核模块内存泄漏

如果 Slab、PageTables、vmalloc 等内核态内存占总内存比例异常高（如超过 50% 或绝对值远超正常水平）：

- **Slab 泄漏排查**：
  - 用 `kmem -s` 列出所有 slab cache，按占用大小排序，找出 top 10
  - 重点关注异常膨胀的 slab cache（如 `dentry`、`inode_cache`、`radix_tree_node`、`task_struct` 等数量远超正常水平）
  - 确认异常 slab cache 是由内核核心代码还是第三方内核模块分配
  - 使用 `kmem -S <slab_name>` 查看具体 slab cache 的详细信息

- **内核模块排查**：
  - 用 `mod` 或 `lsmod` 列出所有已加载的内核模块
  - 检查是否有第三方/非标准内核模块（如自研驱动、安全模块、监控 agent 的内核模块等）
  - 如果异常 slab cache 的分配调用链指向特定内核模块，重点分析该模块是否存在内存泄漏 bug
  - 使用 `search_knowledge_base` 搜索该模块是否有已知的内存泄漏问题

- **PageTables 异常排查**：
  - 如果 PageTables 占用异常大，检查是否有进程映射了大量碎片化的虚拟内存区域
  - 检查是否与内核的内存管理机制缺陷有关

- **vmalloc 区域排查**：
  - 检查 vmalloc 区域占用是否异常
  - 某些内核模块可能通过 vmalloc 大量分配内存

##### 4b. 用户态内存占用主导 → 列出 top 进程

如果匿名内存（AnonPages）或共享内存（Shmem）占总内存比例高：

- **列出内存占用 top 10 进程**：通过 `ps -m` 或逐进程检查 `task_struct->mm->total_vm` / `rss`，按 RSS 排序列出前 10 名
- **对每个 top 进程需列出**：PID、进程名（comm）、RSS、total_vm
- **共享内存分析**：如果 Shmem 占比显著，检查 tmpfs / devtmpfs 的使用情况，确认是哪些进程创建了大量共享内存段

##### 4c. 内存不可回收释放导致无内存可用

即使内存总量未全部被"泄漏"占用，也可能因大量内存处于不可回收状态而导致 OOM。需从以下方面排查：

- **Unevictable / Mlocked 内存**：
  - 检查 `Unevictable` 和 `Mlocked` 的值，如果占比显著，说明大量内存被 `mlock()` 锁定，内核无法回收
  - 找出哪些进程调用了 `mlock` / `mlockall` 锁定了大量内存（检查进程的 `vm_flags` 中是否有 `VM_LOCKED`）

- **HugePages 预留**：
  - HugePages 一旦预留（`vm.nr_hugepages`）即从系统可用内存中扣除，不参与普通内存分配和回收
  - 检查 HugePages_Total / HugePages_Free / HugePages_Rsvd，如果预留了大量 HugePages 但实际使用很少，则存在内存浪费

- **Slab Unreclaimable 过高**：
  - `SUnreclaim` 为不可回收的 slab 内存，如果占比远高于 `SReclaimable`，说明大量内核对象无法被释放
  - 用 `kmem -s` 找出占用最大的不可回收 slab cache

- **Dirty Pages 无法回写**：
  - 如果 `Dirty` / `Writeback` 值异常高，可能因后端存储故障（磁盘 IO 错误、NFS 不可达等）导致脏页无法回写释放
  - 检查 `log` 中是否有 IO 错误、块设备异常、NFS 超时等相关报错

- **内存碎片化**：
  - 用 `kmem -z` 检查各 zone 的 free pages 分布，如果总空闲内存不少但都是小碎片，高阶（order ≥ 2）分配请求可能失败
  - 检查 `log` 中是否有 `page allocation failure` 且 order > 0 的记录
  - 检查 `/proc/buddyinfo`（通过 log 或 OOM dump 信息中的 buddyinfo 输出）

- **Bounce 内存**：
  - 在使用 DMA 的旧设备场景中，Bounce buffer 可能占用大量低端内存（ZONE_DMA / ZONE_DMA32）

#### 5. memcg 分析（如果是 cgroup 触发的 OOM）

- 确认触发 OOM 的 cgroup 路径
- 检查该 cgroup 的 `memory.limit_in_bytes` 和 `memory.usage_in_bytes`
- 检查该 cgroup 内的进程列表和各进程内存占用
- 检查 `memory.oom_control` 是否被设置为禁止 OOM Kill（`oom_kill_disable=1`）
- **如果 cgroup 设置了 `oom_kill_disable=1`**：这会导致 cgroup 内进程在内存耗尽时被挂起而非被杀死，积累到全局 OOM 时可能无可杀进程

#### 6. OOM 前的系统状态

- 检查 OOM 之前系统日志中是否有内存压力预警信号：
  - 频繁的 page allocation failure
  - kswapd 高负载运行
  - 之前是否已有 OOM Kill 记录（杀了哪些进程、释放了多少内存）
- 检查是否有大量进程处于 D 状态（等待 IO 或内存回收）

#### 7. 规避和优化建议

**🔴 核心原则：建议必须对解决问题有正向作用，禁止给出无效或有害的建议。如果根因是用户态业务配置问题，且不存在可以通过内核参数调整来解决的情况，则不需要给出内核参数调整建议。**

根据第 4 步判断的内存消耗主因，给出对应方向的建议：

- **内核态内存占用主导**：
  - 尽量从内核源码或社区中找到相关的内存泄漏 bug 及修复 commit
  - 如果不是 bug，需说明是什么原因导致内核占用大量内存（如大量文件打开导致 dentry/inode cache 膨胀、大量网络连接导致相关 slab 增长等），分析是否与业务使用姿势相关，如果是则给出具体的业务优化建议
  - 如果涉及第三方内核模块，建议联系模块提供方排查

- **用户态内存占用主导**：
  - 给出内存占用 top 进程列表（第 4b 步的结果），建议业务侧进一步排查这些进程的内存使用是否合理
  - **🔴 不要给出"调整 vm.overcommit_memory"之类的内核参数建议**——用户态进程内存超配是业务配置问题，调整内核的 overcommit 策略不能解决根本问题（严格模式只会让应用无法启动，启发式模式是默认行为本身没有问题）
  - 重点关注：业务内存规划是否合理、是否需要 cgroup 限制、oom_score_adj 配置是否合理、服务重启策略是否合理

---

### 🔴 阶段三结束前：根因分类判定

**完成上述所有排查后，必须对根因进行明确分类，决定是否进入阶段四（查找社区 fix commit 及 bug issue）：**

| 根因分类 | 典型场景 | 是否需要阶段四 |
|----------|---------|---------------|
| **内核缺陷** | 内核/内核模块内存泄漏（Slab 异常增长）、内核回收路径死锁、OOM Killer 逻辑 bug | ✅ 需要——去查找社区修复 commit 和相关 bug issue |
| **非内核缺陷（业务配置）** | 所有进程 `oom_score_adj=-1000` 导致无可杀进程、cgroup `oom_kill_disable=1`、用户态进程内存泄漏、HugePages 预留过多等 | ❌ 不需要——**跳过阶段四**，直接进入阶段五 |
| **存疑** | 无法确定是内核 bug 还是配置问题 | ✅ 需要——执行阶段四以排除内核侧问题 |

**判定原则：**
- 如果根因明确是**业务侧行为或配置导致的 OOM**（如错误的 oom_score_adj 设置、用户进程内存暴涨），这不是内核 bug，搜索社区内核修复 commit 和 bug issue 没有意义
- 只有根因涉及**内核代码本身的缺陷**（如内核内存回收逻辑有 bug、内核模块 slab 泄漏等）才需要进入阶段四
