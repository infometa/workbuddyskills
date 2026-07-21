# Crash 命令速查与分析技巧

以下命令用法均来自 `crash -h <command>` 官方 help 手册，确保准确可靠。

## 常用 crash 命令速查

### bt — 回溯（backtrace）

| 命令 | 用途 |
|------|------|
| `bt` | 显示当前上下文的内核栈回溯 |
| `bt -a` | 显示每个 CPU 上活跃任务的栈回溯（仅适用于 crash dump） |
| `bt -p` | 仅显示 panic 任务的栈回溯（仅适用于 crash dump） |
| `bt -f` | 显示每个栈帧中的完整栈数据（用于确定传递给函数的参数） |
| `bt -F` | 类似 `-f`，但会对栈数据进行符号化显示；`-FF` 显示 slab cache 对象名和地址 |
| `bt -l` | 显示每个栈回溯文本位置的源文件名和行号 |
| `bt -t` | 从最后已知栈位置到栈顶显示所有文本符号（回溯失败时有用） |
| `bt -T` | 从 task_struct/thread_info 上方到栈顶显示所有文本符号 |
| `bt -r` | 显示原始栈数据（包含 task_union 结构的两个页面的内存转储） |
| `bt -e` | 在栈中搜索可能的内核态和用户态异常帧 |
| `bt -E` | 在 IRQ 栈和异常栈中搜索可能的异常帧（x86_64） |
| `bt -v` | 检查所有任务的内核栈是否存在栈溢出 |
| `bt -c <cpu>` | 显示指定 CPU 上活跃任务的栈回溯，支持格式 "3"、"1,8,9"、"1-23" |
| `bt -g` | 显示目标任务所在线程组中所有线程的栈回溯 |
| `bt -o` | 以老式 backtrace 格式输出 |
| `bt -s` | 显示每个栈帧的起始地址，可与 `-x`/`-d` 配合设置格式 |
| `bt -I <ip>` | 使用指定的指令指针地址开始回溯 |
| `bt -S <sp>` | 使用指定的栈指针地址开始回溯 |
| `bt -R <ref>` | 在栈回溯中搜索指定的引用 |
| `bt <pid>` | 显示指定 PID 进程的栈回溯 |
| `bt <task>` | 显示指定 task_struct 地址的任务的栈回溯 |

### ps — 进程状态信息

| 命令 | 用途 |
|------|------|
| `ps` | 显示所有进程的状态信息（PID、PPID、CPU、TASK、状态、%MEM、VSZ、RSS、COMM） |
| `ps <pid>` | 显示指定 PID 的进程信息 |
| `ps <command>` | 显示指定命令名的进程信息 |
| `ps -k` | 仅显示内核线程 |
| `ps -u` | 仅显示用户任务 |
| `ps -G` | 仅显示每个线程组的线程组 leader |
| `ps -s` | 将 TASK 列替换为 KSTACKP（内核栈指针）列 |
| `ps -p` | 显示每个进程的父/子关系树 |
| `ps -c` | 显示每个进程的子进程列表 |
| `ps -t` | 显示每个进程最近一次运行的 CPU 时间 |
| `ps -l` | 显示进程最后运行的时间戳值（纳秒级 `last_run`/`timestamp` 值） |
| `ps -m` | 类似 `-l`，但将时间戳转换为距今的天/时/分/秒/毫秒格式 |
| `ps -l -C <cpu>` | 按指定 CPU 显示进程时间戳数据 |
| `ps -m -C <cpu>` | 按指定 CPU 显示进程距今运行时间 |
| `ps -a` | 显示进程的命令行参数和环境变量 |
| `ps -g` | 按线程组显示任务 |
| `ps -r` | 显示进程的资源限制 |
| `ps -S` | 显示各进程状态的统计计数 |
| `ps -A` | 显示进程的 cgroup 信息 |
| `ps -H` | 显示进程的调度信息 |
| `ps -y <policy>` | 按调度策略过滤（NORMAL/FIFO/RR/BATCH/IDLE/DEADLINE） |

**进程状态标识**：RU(运行)、IN(可中断睡眠)、UN(不可中断睡眠/D状态)、ZO(僵尸)、ST(停止)、TR(跟踪)、DE(死亡)、SW(交换)、WA(唤醒中)、PA(暂停)、ID(空闲)、NE(新建)

### foreach — 对多个任务执行命令

| 命令 | 用途 |
|------|------|
| `foreach bt` | 对所有任务执行 bt 命令 |
| `foreach UN bt` | 对所有 UN（不可中断睡眠/D状态）进程执行 bt 命令 |
| `foreach RU bt` | 对所有运行态进程执行 bt |
| `foreach active bt` | 对每个 CPU 上的活跃线程执行 bt |
| `foreach kernel bt` | 对所有内核线程执行 bt |
| `foreach user bt` | 对所有用户线程执行 bt |
| `foreach <name> bt` | 对指定进程名的所有任务执行 bt |
| `foreach files` | 对所有任务执行 files 命令 |
| `foreach vm` | 对所有任务执行 vm 命令 |
| `foreach task` | 对所有任务执行 task 命令 |
| `foreach net` | 对所有任务执行 net 命令 |
| `foreach ps` | 对所有任务执行 ps 命令 |
| `foreach sig` | 对所有任务执行 sig 命令 |

**注意**：`foreach` 支持可选 flag 传递给子命令，如 `foreach UN bt -l`（对所有 D 状态进程显示带行号的回溯）

### kmem — 内核内存

| 命令 | 用途 |
|------|------|
| `kmem -i` | 显示通用内存使用信息摘要 |
| `kmem -f` | 显示系统空闲内存头信息，并校验 page count 等于 nr_free_pages |
| `kmem -F` | 同 `-f`，但同时转储链接到该头的所有页面 |
| `kmem -z` | 显示各 zone 的内存统计 |
| `kmem -s` | 显示 slab 缓存信息 |
| `kmem -S [slab]` | 搜索指定 slab 缓存信息，带 `=cpu` 可限定 CPU |
| `kmem -v` | 显示由 vmalloc() 分配的映射虚拟内存区域 |
| `kmem -V` | 显示 vm_stat/vm_zone_stat/vm_node_stat 表和 vm_event_states 计数器 |
| `kmem -n` | 显示内存节点、内存 section、内存 block 的数据和状态 |
| `kmem -o` | 显示每个 CPU 的 offset 值（用于 per-cpu 符号地址转换） |
| `kmem -h` | 显示 hugepage hstate 数组条目（hugepage 大小、总数、空闲数） |
| `kmem -p` | 显示系统 mem_map[] 数组中每个 page 结构的基本信息 |
| `kmem -g [flags]` | 翻译 page 结构的 flags 字段内容为可读的 PAGE-FLAG 名 |
| `kmem <addr>` | 查询指定地址的归属（所属 page、slab、kmalloc 信息等） |
| `kmem -P <addr>` | 以指定地址作为物理地址或 page 结构地址进行查询 |

### irq — 中断数据

| 命令 | 用途 |
|------|------|
| `irq` | 显示所有 IRQ 的描述符数据（irq_desc、irqaction、名称） |
| `irq <index>` | 显示指定 IRQ 号的详细数据 |
| `irq -u` | 仅显示正在使用的 IRQ 数据 |
| `irq -d` | 显示 intel 中断描述符表（IDT）条目 |
| `irq -b` | 显示软中断（bottom half / softirq）数据 |
| `irq -a` | 显示使用中的 IRQ 的 CPU 亲和性掩码 |
| `irq -s` | 显示内核中断统计（类似 /proc/interrupts，包含每个 CPU 的中断计数） |
| `irq -s -c <cpu>` | 仅显示指定 CPU 的中断统计，CPU 格式："1,3,5"、"1-3"、"all" |

### dis — 反汇编

| 命令 | 用途 |
|------|------|
| `dis <symbol>` | 反汇编整个函数（如果不指定 count） |
| `dis <addr> [count]` | 从指定地址反汇编 count 条指令（默认 1 条） |
| `dis -l <symbol>` | 反汇编时同时显示源代码行号信息 |
| `dis -r <addr>` | 反向显示：从函数起始位置到指定地址的所有指令 |
| `dis -f <addr>` | 正向显示：从指定地址到函数结尾的所有指令 |
| `dis -s <symbol/addr>` | 显示关联的源代码文件名、行号和源码清单（如主机上有源码） |
| `dis -x <symbol>` | 以十六进制格式输出 |
| `dis -d <symbol>` | 以十进制格式输出 |
| `dis -u <addr>` | 指定地址为用户空间虚拟地址 |

### rd — 读取内存

| 命令 | 用途 |
|------|------|
| `rd <addr> [count]` | 读取内核虚拟地址的内存（默认按 long 大小，十六进制+ASCII） |
| `rd -8 <addr> <count>` | 以 8 位（字节）为单位显示 |
| `rd -16 <addr> <count>` | 以 16 位为单位显示 |
| `rd -32 <addr> <count>` | 以 32 位为单位显示（32位机器默认） |
| `rd -64 <addr> <count>` | 以 64 位为单位显示（64位机器默认） |
| `rd -d <addr> <count>` | 以有符号十进制格式显示 |
| `rd -D <addr> <count>` | 以无符号十进制格式显示 |
| `rd -s <addr> <count>` | 对内存内容进行符号化显示（地址映射到函数名） |
| `rd -S <addr> <count>` | 符号化显示，额外标注 slab cache 对象名 |
| `rd -a <addr>` | 以 ASCII 字符显示（到首个不可打印字符停止） |
| `rd -p <addr> <count>` | 指定地址为物理地址 |
| `rd -x <addr> <count>` | 不显示行尾的 ASCII 翻译 |
| `rd -o <offs> <addr> <count>` | 从起始地址偏移 offs 字节开始读取 |
| `rd -e <end_addr> <addr>` | 读取到指定结束地址 |
| `rd -r <file> <addr> <count>` | 将原始数据转储到指定文件（count 为字节数） |
| `rd -R <addr> <count>` | 逆序显示内存 |
| `rd -N <addr> <count>` | 以网络字节序显示（仅 16/32 位值有效） |

### struct — 结构体内容

| 命令 | 用途 |
|------|------|
| `struct <type>` | 显示结构体定义和大小 |
| `struct <type> <addr>` | 在指定地址以格式化方式显示结构体内容 |
| `struct <type>.member` | 仅显示指定成员的偏移和定义 |
| `struct <type>.member <addr>` | 显示指定地址结构体的特定成员值 |
| `struct <type> -o` | 显示结构体定义并包含各成员偏移量 |
| `struct <type> -o <addr>` | 带成员虚拟地址的格式化显示 |
| `struct <type> <addr> <count>` | 连续显示 count 个结构体（数组形式） |
| `struct <type> <addr>:a` | 显示所有 CPU 的 per-cpu 数据 |
| `struct <type> -x <addr>` | 以十六进制格式输出 |
| `struct <type> -d <addr>` | 以十进制格式输出 |
| `struct <type> -p <addr>` | 如果成员是指针，解引用显示目标数据 |
| `struct <type> -l <offset> <addr>` | 指定嵌入 list_head 的偏移量 |

**快捷方式**：如果结构体名不与 crash 命令冲突，可以省略 `struct` 关键字，如 `task_struct <addr>`

### union — 联合体内容

| 命令 | 用途 |
|------|------|
| `union <type>` | 显示联合体定义和大小 |
| `union <type> <addr>` | 在指定地址以格式化方式显示联合体内容 |

用法与 `struct` 命令基本相同，详见 `crash -h union`。

### sym — 符号翻译

| 命令 | 用途 |
|------|------|
| `sym <addr>` | 将虚拟地址翻译为符号名+偏移（如有）；同时显示符号类型和源文件行号 |
| `sym <name>` | 将符号名翻译为虚拟地址 |
| `sym -l` | 转储所有符号及其值 |
| `sym -M` | 转储当前所有模块符号 |
| `sym -m <module>` | 转储指定模块的符号 |
| `sym -p <symbol>` | 显示目标符号及前一个符号 |
| `sym -n <symbol>` | 显示目标符号及下一个符号 |
| `sym -q <string>` | 搜索所有包含指定字符串的符号 |

### whatis — 搜索符号表获取类型信息

| 命令 | 用途 |
|------|------|
| `whatis <struct/union/typedef>` | 显示结构体/联合体/typedef 的定义和大小 |
| `whatis -o <struct>` | 显示结构体定义并包含各成员偏移量 |
| `whatis <symbol>` | 显示内核符号的数据类型（如函数签名） |
| `whatis -r <size>` | 搜索指定大小的所有结构体 |
| `whatis -r <low-high>` | 搜索指定大小范围的结构体 |
| `whatis -m <member>` | 搜索包含指定类型成员（或指向指定类型的指针）的结构体 |

### p — 打印表达式值

| 命令 | 用途 |
|------|------|
| `p <expression>` | 将参数传递给 gdb 的 print 命令进行求值 |
| `p <symbol>` | 打印内核符号的值（全局变量等） |
| `p <per_cpu_symbol>` | 显示 per-cpu 变量的数据类型和所有 CPU 的地址 |
| `p <per_cpu_symbol>:<cpu>` | 显示指定 CPU 上 per-cpu 变量的内容 |
| `p <per_cpu_symbol>:a` | 显示所有 CPU 上 per-cpu 变量的内容 |
| `p -x <expression>` | 以十六进制格式输出 |
| `p -d <expression>` | 以十进制格式输出 |

**内置别名**：`px`（强制十六进制）、`pd`（强制十进制）、`hex`（设默认十六进制）、`dec`（设默认十进制）

### log — 内核日志

| 命令 | 用途 |
|------|------|
| `log` | 按时间顺序转储内核 log_buf 内容 |
| `log -T` | 以人类可读的时间戳显示（注意：时间戳可能不准确，来自 local_clock()） |
| `log -t` | 不显示时间戳（仅适用于变长记录格式） |
| `log -m` | 在每条消息前显示日志级别 |
| `log -d` | 显示 dev_printk() 附加的键值对属性字典 |
| `log -a` | 转储尚未拷贝到用户空间 audit 守护进程的内核审计日志 |
| `log -s` | 转储尚未刷新到 log_buf 的 per-CPU printk safe buffer 内容 |

**注意**：log 命令的输出可以通过管道进行过滤，如 `log \| tail -n 100`、`log \| grep -i hung`

### runq — 运行队列

| 命令 | 用途 |
|------|------|
| `runq` | 显示每个 CPU 运行队列上的任务 |
| `runq -t` | 显示每个 CPU 运行队列的时间戳和活跃任务的时间戳 |
| `runq -T` | 显示每个 CPU 相对于最近运行队列时间戳的时间差 |
| `runq -m` | 显示每个 CPU 上活跃任务已运行的时间（天/时/分/秒/毫秒） |
| `runq -g` | 按 task_group 层次化显示任务（含 THROTTLED 状态） |
| `runq -c <cpu>` | 仅显示指定 CPU 的运行队列，CPU 格式："3"、"1,8,9"、"1-23" |

### files — 打开的文件

| 命令 | 用途 |
|------|------|
| `files` | 显示当前上下文的打开文件（ROOT、CWD、每个 fd 的 file/dentry/inode/类型/路径） |
| `files <pid>` | 显示指定 PID 进程的打开文件 |
| `files -d <dentry>` | 给定 dentry 地址，显示其 inode、super block、文件类型和完整路径 |
| `files -p <inode>` | 给定 inode 地址，显示其在 page cache 中的所有页面 |
| `files -c` | 显示每个打开文件的 inode、i_mapping、page cache 页数、文件类型和路径 |
| `files -R <ref>` | 搜索引用（fd 号、文件名、dentry/inode/file 地址） |

### vm — 虚拟内存

| 命令 | 用途 |
|------|------|
| `vm` | 显示当前上下文的 mm_struct 指针、PGD、RSS、TOTAL_VM 及各 vm_area_struct 信息 |
| `vm <pid>` | 显示指定 PID 的虚拟内存信息 |
| `vm -p` | 将每个 VM 区域的虚拟页转换为物理地址（或 swap/文件偏移） |
| `vm -P <vma>` | 仅转换指定 VMA 的页面 |
| `vm -m` | 转储关联的 mm_struct 结构体内容 |
| `vm -v` | 转储所有 vm_area_struct 结构体内容 |
| `vm -M <mm>` | 手动指定 mm_struct 地址（用于 mm 已从 task_struct 移除的退出中任务） |
| `vm -f <vm_flags>` | 翻译 FLAGS（vm_flags）值为可读标志名 |
| `vm -R <ref>` | 搜索引用（地址或文件名） |

### net — 网络

| 命令 | 用途 |
|------|------|
| `net` | 显示网络设备列表（NET_DEVICE、NAME、IP ADDRESS） |
| `net -n [pid]` | 显示指定任务网络命名空间内的网络设备列表 |
| `net -s [pid]` | 显示打开的网络 socket/sock 地址、协议族、类型、源/目的地址和端口 |
| `net -S [pid]` | 同 `-s`，但额外转储 socket 和 sock 结构体的完整内容 |
| `net -a` | 显示 ARP 缓存 |
| `net -N <addr>` | 将十进制/十六进制 IPv4 地址转换为点分十进制表示 |
| `net -R <ref>` | 搜索引用（socket/sock 地址或 fd） |

### dev — 设备数据

| 命令 | 用途 |
|------|------|
| `dev` | 显示字符设备和块设备数据 |
| `dev -i` | 显示 I/O 端口使用情况；在 2.4 内核上还显示 I/O 内存使用情况 |
| `dev -p` | 显示 PCI 设备数据 |
| `dev -d` | 显示磁盘 I/O 统计（TOTAL/SYNC/ASYNC/READ/WRITE/DRV 请求数） |
| `dev -D` | 同 `-d`，但过滤掉没有进行中 I/O 请求的磁盘 |
| `dev -V` | 显示 vmcore 中所有设备转储的索引列表（偏移、大小、名称） |
| `dev -v <index>` | 选择并显示指定索引的设备转储数据 |
| `dev -v <index> <file>` | 将设备转储数据导出到文件 |

### mod — 模块信息

| 命令 | 用途 |
|------|------|
| `mod` | 显示当前已加载模块的基本信息（地址、名称、基址、大小、对象文件、KALLSYMS 状态） |
| `mod -s <module> [objfile]` | 从对象文件加载指定模块的符号和调试数据 |
| `mod -d <module>` | 删除指定模块已加载的符号和调试数据 |
| `mod -S [directory]` | 加载所有模块的符号和调试数据 |
| `mod -t` | 显示被标记为"tainted"的模块 |
| `mod -r` | 使用已加载模块来设置符号搜索的根目录 |

### sys — 系统数据

| 命令 | 用途 |
|------|------|
| `sys` | 显示系统基本信息（KERNEL、DUMPFILE、CPUS、DATE、UPTIME、LOAD AVERAGE 等） |
| `sys -c` | 转储 sys_call_table 所有条目（系统调用号、名称、源文件行号） |
| `sys -c <name>` | 搜索包含指定字符串的系统调用 |
| `sys -c <number>` | 显示指定编号的系统调用 |
| `sys config` | 转储内核配置数据（需要 CONFIG_IKCONFIG） |
| `sys -t` | 显示内核 taint 信息（tainted_mask 及各位含义） |
| `sys -i` | 显示 DMI 字符串数据（BIOS 厂商、产品名、序列号等） |

### mount — 挂载的文件系统

| 命令 | 用途 |
|------|------|
| `mount` | 显示当前挂载的文件系统（VFSMOUNT/MOUNT、SUPERBLK、TYPE、DEVNAME、DIRNAME） |
| `mount -f` | 显示每个文件系统中打开的文件（仅 Linux 3.13 之前支持） |
| `mount -i` | 显示每个文件系统关联的脏 inode（仅 Linux 2.6.32 之前支持） |
| `mount -n <pid>` | 显示指定任务命名空间内的挂载文件系统 |
| `mount <dev/dir/dentry/inode/superblock>` | 查找包含指定设备/目录/dentry/inode/superblock 的文件系统 |

### task — task_struct 和 thread_info 内容

| 命令 | 用途 |
|------|------|
| `task` | 转储当前上下文的 task_struct 和 thread_info 结构体的格式化内容 |
| `task <pid>` | 转储指定 PID 的 task_struct 和 thread_info |
| `task <taskp>` | 转储指定 task_struct 地址的内容 |
| `task -R <member[,member]>` | 仅显示指定的 task_struct/thread_info 成员 |
| `task -R <member.member>` | 显示嵌套成员（如 `task -R se.on_rq`） |
| `task -x` | 以十六进制格式输出 |
| `task -d` | 以十进制格式输出 |

### set — 设置进程上下文

| 命令 | 用途 |
|------|------|
| `set` | 显示当前上下文（PID、task 指针、CPU、状态） |
| `set <pid>` | 切换当前上下文到指定 PID 的进程 |
| `set <taskp>` | 切换当前上下文到指定 task_struct 地址的进程 |
| `set -c <cpu>` | 切换到指定 CPU 上的活跃任务（仅 dump 文件） |
| `set -p` | 切换到 panic 任务 |
| `set -a <pid/taskp>` | 将指定进程设为其 CPU 上的活跃任务 |
| `set radix 16` | 设置输出格式为十六进制 |
| `set radix 10` | 设置输出格式为十进制 |
| `set scroll off` | 关闭输出滚动 |
| `set -v` | 显示所有内部 crash 变量的当前状态 |

### waitq — 等待队列

| 命令 | 用途 |
|------|------|
| `waitq <symbol>` | 显示在指定全局等待队列上阻塞的任务 |
| `waitq <struct.member> <addr>` | 显示在指定结构体的等待队列成员上阻塞的任务 |
| `waitq <addr>` | 显示在指定等待队列地址上阻塞的任务 |

### swap — 交换设备信息

| 命令 | 用途 |
|------|------|
| `swap` | 显示每个配置的交换设备信息（类型、大小、使用量、优先级、文件名） |

### timer — 定时器队列

| 命令 | 用途 |
|------|------|
| `timer` | 按时间顺序显示定时器队列条目（过期时间、TTE、地址、回调函数） |
| `timer -r` | 显示 hrtimer 高精度定时器队列条目 |
| `timer -C <cpu>` | 仅显示指定 CPU 的定时器数据 |

---

## 分析技巧

### 查看 per-cpu 变量

crash 中**没有独立的 `per_cpu` 命令**。查看 per-cpu 变量的正确方式：

```
# 显示 per-cpu 变量的类型和所有 CPU 地址
p irq_stat

# 显示指定 CPU 上的 per-cpu 变量内容
p irq_stat:1

# 显示所有 CPU 上的 per-cpu 变量内容
p irq_stat:a

# 也可以通过 struct 命令加 :a 后缀
struct disk_stats <percpu_addr>:a
```

### 查看锁状态

crash 中**没有独立的 `mutex` 和 `rwlock` 命令**。查看锁状态的正确方式：

```
# 查看 mutex 结构
struct mutex <addr>
# 关注 owner 字段：指向持有锁的 task_struct

# 查看 rwsem（读写信号量）
struct rw_semaphore <addr>
# 关注 owner 和 count 字段

# 查看 spinlock
struct spinlock <addr>
# 或直接查看 raw_spinlock
struct raw_spinlock <addr>

# 死锁检测：跟踪锁持有链
# 1. 从 hung 进程的 bt 找到在等待的锁地址
# 2. struct mutex <lock_addr> 找到 owner
# 3. bt <owner_task> 查看 owner 的调用栈
# 4. 重复以上步骤看是否形成环
```

### 时间计算

```
# 获取当前 jiffies 值
p jiffies

# 获取 HZ 值
p HZ

# 计算时间差
# elapsed_seconds = (current_jiffies - start_jiffies) / HZ
# 注意 jiffies 回绕问题（使用 time_after/time_before 语义）

# 纳秒级时间戳
# 部分 task_struct 成员使用纳秒（如 sched_info、se.exec_start）
# 转换：seconds = nanoseconds / 1000000000
```

### 内存地址校验

- 内核地址空间通常在 `0xffff800000000000` 以上（x86_64，4 级页表）
- 使用 `kmem <addr>` 确认地址有效性和归属（page/slab/kmalloc）
- 使用 `rd` 读取并验证数据内容的合理性
- 通过相邻结构体成员交叉验证地址准确性
- 使用 `sym <addr>` 检查地址是否位于已知符号附近

### 局部变量查找

```
# 1. 使用 bt -f 查看完整栈帧数据
bt -f

# 2. 使用 bt -F 获取符号化的栈帧数据
bt -F

# 3. 对照反汇编代码确认变量在栈上的偏移
dis -l <fault_function>
dis -rl <caller_return_address>

# 4. 通过 rd 读取栈上特定偏移的数据
rd <stack_addr> <count>

# 重要：不要直接信任寄存器中的值，寄存器可能已被后续代码覆盖
# 如果局部变量有压栈，优先从堆栈中查找
```

### IO 分析

```
# 查看磁盘 I/O 统计
dev -d

# 查看有活跃 I/O 的磁盘
dev -D

# 检查 request_queue 中的请求
struct request_queue <addr>

# 检查 IO 请求的时间戳
struct request <addr>
# 关注 start_time 或 io_start_time_ns 字段

# NFS 请求分析
struct rpc_task <addr>
# 关注 tk_start 时间字段
```

### 虚拟化环境分析

```
# 检查内核日志中的虚拟化信息
log | grep -i kvm
log | grep -i hypervisor
log | grep -i vmware
log | grep -i xen

# 检查系统信息（是否为虚拟机）
sys -i

# 检查 steal time（per-cpu）
p steal_time:a

```
