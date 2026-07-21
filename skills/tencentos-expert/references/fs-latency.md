---
name: fs-latency
description: 系统性分析 Linux 文件系统 I/O 延迟问题，从 VFS → Page Cache → 文件系统（ext4/xfs）逐层定位性能瓶颈根因。 支持t-ops os_stat纳秒级内核函数追踪和 strace/perf/proc 传统工具双轨诊断方案。 涵盖 14 类已知文件 IO 瓶颈模式的自动识别：page cache miss、atime 写放大、fsync 慢、 文件碎片化、挂载参数错误、dentry/inode 缓存不足、fd/inode 耗尽、ext4 回写风暴、 大目录 lookup 慢、mmap 缺页率高、文件系统锁竞争、XFS 日志瓶颈、内核函数热点等。
description_zh: 文件系统 I/O 延迟分析
description_en: File system I/O latency analysis
version: 1.0.0
---

# 文件 IO 性能分析

> 系统性分析 Linux 文件系统 I/O 延迟问题，从 VFS → Page Cache → 文件系统（ext4/xfs）逐层定位性能瓶颈根因。

## 概述

当用户反馈"文件读写慢"、"open/read/write/close 延迟高"、"fsync 卡顿"、"page cache 命中率低"、"文件系统锁竞争"、"dentry/inode 缓存问题"、"VFS 层延迟"、"ext4/xfs 文件操作慢"、"atime 写放大"、"脏页回写"等问题时，按照以下流程进行系统性排查。

### 适用场景

- 应用反馈文件读写慢 / read/write 系统调用延迟高
- 数据库 WAL/fsync 延迟大
- page cache 命中率低
- 文件系统锁竞争（多线程并发操作同一文件/目录）
- VFS 层性能瓶颈（路径查找慢、inode 锁竞争）
- ext4/xfs 文件操作卡顿
- dentry/inode 缓存问题
- atime 写放大
- 脏页回写风暴

### 分析范围

**覆盖**：VFS 层 → 文件系统层（ext4/xfs）→ Page Cache 层

**不涉及**：块设备层（blktrace/blkparse/btt/iostat 等块 IO 工具属于 block-io-latency 技能范畴）

### 分层诊断模型

```
用户感知：read() 耗时 50ms
            │
  ┌─────────┼──────────────────────────┐
  │         ▼                          │
  │  VFS 层耗时 2ms                    │
  │  （路径查找、权限检查、inode 锁）    │
  │         │                          │
  │         ▼                          │
  │  Page Cache 层                      │
  │  ├── cache hit: 200ns  ← 命中      │
  │  └── cache miss: 48ms  ← 未命中    │
  │         │                          │
  │         ▼                          │
  │  ext4/xfs 层耗时 1ms              │
  │  （extent 查找、元数据读取）         │
  └────────────────────────────────────┘
```

## 前置条件

### 权限要求

- 需要 root 权限（部分命令需要访问 /proc、/sys）

### 工具检查

```bash
# === 必需工具 ===
which df mount findmnt dmesg awk cat

# === 推荐工具：t-ops—— 内核函数级追踪 ===
which t-ops && t-ops -v
# 安装方式（TencentOS）:
# yum install tencentos-tools -y

# 检查内核模块
lsmod | grep os_aware
ls /usr/lib/tencentos-tools/ops/os_stat/os_stat_user/os_aware_$(uname -r).ko* 2>/dev/null

# 检查 cflow（os_stat 生成函数调用树需要）
which cflow || yum install cflow -y

# === 可选工具（降级方案）===
which strace && strace -V
which perf && perf --version
which iostat && iostat -V
which iotop pidstat 2>/dev/null
```

**双轨工具策略**：优先使用t-ops（纳秒级精度、<1% 开销、自动展开调用树），t-ops不可用时自动降级到 strace + perf + /proc 传统方案。

### os_aware.ko 兼容性处理（重要，新机器必做）

`ops-run` 脚本在执行 `os_stat` 前会根据 `uname -r` 截取内核版本号来查找预编译的 `.ko.xz` 文件。但某些内核版本（如 `5.4.241-24.0017.23`）的版本号格式与 `ops-run` 中硬编码的截取规则不匹配（它期望类似 `5.4.241-1-tlinux4-0017` 的格式），导致找不到 `.ko.xz` 文件，进入编译分支后因 `change.py` 的符号替换问题（`->` 被替换为 `bb`）而编译失败。

**症状**：执行 `t-ops latency os_stat -fg 1 ...` 时输出大量编译错误（含 `error: expected ...` 和 `change.py` 相关日志），或提示 `need rmmod os_aware` 后退出。

**解决方案**：在执行 os_stat 前，运行兼容性修复脚本。优先使用符号链接方案（方案 A）；如果目录下没有任何可用的 `os_aware.ko` 或 `.ko.xz`，则自动从内核源码编译（方案 B）。

> **完整脚本见下方「[步骤 0：环境准备](#步骤-0环境准备自动首次执行必做)」中的 os_aware.ko 兼容性修复代码块。**

**方案说明**：

| 方案 | 条件 | 动作 |
|------|------|------|
| A-1 | 已有精确匹配的 `os_aware_$(uname -r).ko.xz` 或 `.ko` | 无需操作 |
| A-2 | 有通用的 `os_aware.ko` | 创建符号链接 |
| A-3 | 有其他版本的 `.ko.xz` | 创建符号链接（可能因内核版本不匹配 insmod 失败） |
| B | 目录下没有任何 ko 文件 | 从 `/usr/src/kernels/$(uname -r)` 编译 `os_aware.ko` |

**关键注意事项**：
- 方案 B 编译需要安装 `kernel-devel`（`yum install kernel-devel-$(uname -r) -y`）
- **`include_link` 必须用 `rm -f include/include`**（第二层符号链接），**绝不能 `rm -rf include`**（会删掉整个头文件目录）
- **vmx.h 兼容性修复**：6.6.0~6.6.103 内核需要用 `#if LINUX_VERSION_CODE >= KERNEL_VERSION(6,6,104)` 包裹 `host_debugctl` 相关函数
- 编译时加 `EXTRA_CFLAGS="-w"` 禁用 warning，`version` 参数与 `ops-run` 一致
- 兼容性问题的根因在 `ops-run` 脚本中的版本号截取逻辑（`${tk4:0:22}`），符号链接 + 编译兜底是通用的解决方式

### os_stat 命令格式（重要：版本差异）

不同版本的 t-ops 调用 os_stat 的命令格式不同：

- **新版格式**：`t-ops latency os_stat -f <func> -fg 1 -de <duration> -o 0`
- **旧版格式**：`t-ops os_stat -f <func> -fg 1 -de <duration> -o 0`（不带 `latency` 子命令）

**已知问题**：
- **v4.2.12**：`t-ops latency os_stat` 的 `ops-run` 脚本会错误地将参数（`-de`、`-ss`、`-la`）解析为 `--de`、`--ss`、`--la`，导致 `unrecognized option` 错误。此版本应使用 `t-ops os_stat`（不带 `latency`）。
- **v4.2.17+**：`t-ops os_stat` 旧格式已移除（报 `command "-f" invalid`），必须使用 `t-ops latency os_stat`。该格式运行时可能输出大量 `open error:-1`，属正常现象，最终仍会输出有效数据。

**建议：在批量追踪脚本开头自动探测可用格式**（优先旧格式，失败再用新格式）：

```bash
# 自动探测 os_stat 命令格式
rmmod os_aware 2>/dev/null; sleep 5
if t-ops os_stat -f vfs_read -fg 1 -de 2 -o 0 2>&1 | grep -q "command.*invalid"; then
    OS_STAT_CMD="t-ops latency os_stat"
    echo "Using: t-ops latency os_stat (v4.2.17+ format)"
else
    OS_STAT_CMD="t-ops os_stat"
    echo "Using: t-ops os_stat (legacy format)"
fi
rmmod os_aware 2>/dev/null; sleep 5
```

---

## 使用步骤

### 步骤 0：环境准备（自动，首次执行必做）

在开始诊断前，必须确保所有依赖工具已安装就绪。**此步骤不可跳过**，缺少 t-ops 时不应直接降级到传统方案，而应先尝试安装。

#### 0.1 一键安装所有依赖（推荐）

本 skill 提供了 `scripts/install-deps.sh` 脚本，**一站式**完成以下工作：
- 安装 tencentos-tools（提供 t-ops）
- 修复 4.2.17+ ops-run 路径 bug（os_stat_user → common/tools-manager 等目录迁移未适配）
- 修复 include 符号链接（根据当前内核版本自动选择正确的 include 目录）
- 修复 vmx.h host_debugctl 兼容问题（6.6.0~6.6.103 内核）
- 修复 5.4.241-24 x86_64 被误判为 ARM 的 bug
- 安装 bcc-tools（biolatency/ext4slower/fileslower 等 eBPF 工具）
- 源码编译安装 cflow（os_stat 热路径分析依赖）

```bash
# 获取 skill 脚本路径（假设当前在 skill 根目录下）
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# 如果是 AI 执行，SKILL_DIR 通常是 skills/fs-latency

# 一键安装所有依赖并修复已知 bug
bash "${SKILL_DIR}/scripts/install-deps.sh" --all
```

> **重要**：必须先执行 `install-deps.sh`，再执行后续步骤。该脚本修复了 tencentos-tools 4.2.17 的多个已知 bug，
> 不修复将导致 `t-ops latency os_stat` 无法运行。脚本幂等可重复执行，已修复的项目不会重复处理。

如果无法执行脚本（例如离线环境），可按以下手动步骤操作：

<details>
<summary>手动安装步骤（仅在脚本不可用时使用）</summary>

```bash
# 0.1.1 安装 t-ops
if ! command -v t-ops &>/dev/null; then
    yum install tencentos-tools -y
fi

# 0.1.2 安装其他工具
command -v iostat &>/dev/null || yum install sysstat -y
command -v cflow &>/dev/null || yum install cflow -y
command -v perf &>/dev/null || yum install perf -y
```

</details>

#### 0.2 探测 os_stat 命令格式

```bash
# 自动探测 os_stat 命令格式（适配不同 t-ops 版本）
# 优先尝试旧格式（t-ops os_stat），4.2.17+ 已移除旧格式会立即报错
if command -v t-ops &>/dev/null; then
    rmmod os_aware 2>/dev/null; sleep 5
    OLD_OUTPUT=$(timeout 10 t-ops os_stat -f vfs_read -fg 1 -de 2 -o 0 2>&1)
    if echo "$OLD_OUTPUT" | grep -q "command.*invalid"; then
        OS_STAT_CMD="t-ops latency os_stat"
        echo "Using: t-ops latency os_stat (v4.2.17+ format)"
    else
        OS_STAT_CMD="t-ops os_stat"
        echo "Using: t-ops os_stat (legacy format)"
    fi
    rmmod os_aware 2>/dev/null; sleep 5
    # 验证选定的命令格式能正常输出数据
    OUTPUT=$(timeout 120 $OS_STAT_CMD -f vfs_read -fg 1 -de 2 -o 0 2>&1)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ] || ! echo "$OUTPUT" | grep -q "=== ave ==="; then
        echo "os_stat 不可用（ko 编译失败或内核不兼容），降级到传统工具"
        OS_STAT_CMD=""
    fi
    rmmod os_aware 2>/dev/null
fi
```

> **注意**：首次执行 os_stat 时，ops-run 会自动编译 os_aware.ko 内核模块（需要 kernel-devel），
> 编译+追踪过程可能需要 30~60 秒，请耐心等待，不要提前中断。

#### 0.3 环境就绪确认

```bash
echo "=== 环境检查汇总 ==="
echo "t-ops:    $(command -v t-ops &>/dev/null && t-ops -v || echo '不可用')"
echo "strace:   $(command -v strace &>/dev/null && strace -V 2>&1 | head -1 || echo '不可用')"
echo "perf:     $(command -v perf &>/dev/null && perf --version || echo '不可用')"
echo "iostat:   $(command -v iostat &>/dev/null && echo '可用' || echo '不可用')"
echo "pidstat:  $(command -v pidstat &>/dev/null && echo '可用' || echo '不可用')"
echo "cflow:    $(command -v cflow &>/dev/null && echo '可用' || echo '不可用')"
echo "===================="
```

**决策逻辑**：
- t-ops 可用且 `OS_STAT_CMD` 非空 → 使用 t-ops 深度追踪（步骤 2A）
- t-ops 不可用、安装失败、或 os_aware.ko 编译失败/内核不兼容（`OS_STAT_CMD` 为空）→ 直接降级到传统工具（步骤 2B）

---

### 步骤 1：基础信息采集（~2 分钟）

并行采集 11 项文件 IO 相关基础数据，建立环境画像。

#### 1.1 系统和内核版本

```bash
uname -r
cat /etc/os-release | head -5
```

#### 1.2 文件系统类型和使用率

```bash
df -hT
df -i   # inode 使用率
```

**分析要点**：
- 使用率超过 **90%** 的文件系统需重点关注（ext4 会触发 `ext4_nonda_switch`，强制关闭延迟分配，写延迟暴增）
- inode 使用率接近 100% 说明小文件过多，无法创建新文件

#### 1.3 挂载参数检查

```bash
findmnt -t ext4,xfs,btrfs -o TARGET,SOURCE,FSTYPE,OPTIONS 2>/dev/null || mount | grep "^/dev"
```

**分析要点**：

| 参数 | 问题 | 建议 |
|------|------|------|
| 缺少 `noatime`/`relatime` | 每次读都更新 atime，导致写放大 | 加 `noatime` 或 `relatime` |
| `data=journal` (ext4) | 数据和元数据都写日志，写放大严重 | 改为 `data=ordered` |
| `sync` | 所有写都同步，极慢 | 改为异步 |
| XFS `logbsize` 过小 | 日志写入瓶颈 | 增大 logbsize |
| `nobarrier`/`barrier=0` | 性能好但断电数据不安全 | 生产环境保持 barrier |

#### 1.4 文件描述符使用情况

```bash
sysctl fs.file-nr fs.file-max fs.nr_open 2>/dev/null
# fs.file-nr: 已分配/未使用/最大值
```

#### 1.5 inode 和 dentry 缓存状态

```bash
sysctl fs.inode-nr fs.dentry-state 2>/dev/null
```

#### 1.6 Page Cache 和内存状态

```bash
cat /proc/meminfo | grep -E "^(MemTotal|MemFree|MemAvailable|Buffers|Cached|Active\(file\)|Inactive\(file\)|Dirty|Writeback|Slab|SReclaimable)"
```

**判断规则**：
- `Active(file)` >> `Inactive(file)` → 命中率高，工作集在缓存中
- `Active(file)` << `Inactive(file)` → 大量一次性读取，命中率可能低
- `Dirty` 持续 > 数百MB → 回写压力大
- `Writeback` 持续 > 0 → 回写跟不上写入速度

#### 1.7 脏页参数

```bash
sysctl vm.dirty_ratio vm.dirty_background_ratio vm.dirty_expire_centisecs vm.dirty_writeback_centisecs vm.vfs_cache_pressure 2>/dev/null
cat /proc/vmstat | grep -E "nr_dirty|nr_writeback|nr_dirtied|nr_written"
```

#### 1.8 文件系统错误日志

```bash
dmesg | grep -i -E "ext4.*(error|warning|corrupt|abort|remount|no space)" | tail -10
dmesg | grep -i -E "xfs.*(error|warning|corrupt|shutdown|log)" | tail -10
dmesg | grep -i -E "I/O error|buffer_io_error|blk_update_request" | tail -10
dmesg | grep -i "remount.*read-only" | tail -5
```

#### 1.9 高文件 IO 进程

```bash
for pid in $(ls /proc/ | grep -E '^[0-9]+$' | head -30); do
  io=$(cat /proc/$pid/io 2>/dev/null)
  if [ -n "$io" ]; then
    syscr=$(echo "$io" | grep syscr | awk '{print $2}')
    syscw=$(echo "$io" | grep syscw | awk '{print $2}')
    if [ "$syscr" -gt 10000 ] || [ "$syscw" -gt 10000 ] 2>/dev/null; then
      comm=$(cat /proc/$pid/comm 2>/dev/null)
      rb=$(echo "$io" | grep read_bytes | awk '{print $2}')
      wb=$(echo "$io" | grep write_bytes | awk '{print $2}')
      echo "PID=$pid ($comm): syscr=$syscr syscw=$syscw read_bytes=$rb write_bytes=$wb"
    fi
  fi
done
```

**分析要点**：
- `syscr` 大但 `read_bytes` 小 → page cache 命中率高
- `syscr` 大且 `read_bytes` 也大 → page cache 命中率低

#### 1.10 文件锁状态

```bash
cat /proc/locks | head -20
```

#### 1.11 ext4 Journal 信息

```bash
# ext4 journal 统计（如有 ext4 文件系统）
cat /proc/fs/jbd2/*/info 2>/dev/null
```

**关键指标**：average commit time（平均 commit 耗时），handles per transaction

### 步骤 2：深度追踪

根据步骤 1 的结果选择追踪方向。

#### 决策树：选择追踪目标

```
用户问题
  ├── "读文件慢" / "read 延迟高"
  │     → 追踪 vfs_read / generic_file_buffered_read / pagecache_get_page
  │
  ├── "写文件慢" / "write 延迟高"
  │     → 追踪 vfs_write / generic_perform_write / ext4_da_write_begin
  │
  ├── "fsync 慢" / "数据库 WAL 慢"
  │     → 追踪 vfs_fsync_range / ext4_sync_file / jbd2_complete_transaction
  │
  ├── "打开文件慢" / "ls/stat 慢"
  │     → 追踪 do_sys_open / path_openat / lookup_open
  │
  ├── "mmap 应用抖动"
  │     → 追踪 filemap_fault
  │
  ├── "创建文件失败"
  │     → 检查 inode 使用率 (df -i), fd 数量 (file-nr)
  │
  └── 描述不明确
        → 全面基础采集 → 根据数据选择深入方向
```

#### 2A：t-ops深度追踪（推荐）

t-ops os_stat可以追踪从 VFS 层到文件系统具体实现的函数调用链，精确到纳秒级。

**两种模式**：
- **单函数模式（`-fg 1`）**：追踪单个内核函数的调用次数和延迟，**无需内核源码**，是日常诊断的主要模式
- **热路径模式（`-fg 0`）**：递归追踪函数的完整子调用树，需要先通过 cflow 从内核源码生成 `func_tree.txt`。此模式一般用于开发者深度调试

```bash
# 单函数模式用法（推荐日常使用）:
# t-ops latency os_stat -f <函数名> -fg 1 -de <追踪时长秒> -o 0
t-ops latency os_stat -f vfs_read -fg 1 -de 5 -o 0

# 热路径模式用法（需要内核源码 + func_tree.txt）:
# t-ops os_stat <内核源码目录> <起始函数> <模式0=热路径> <热点1=首次/0=复用>
t-ops os_stat /data/linux vfs_read 0 1
```

##### os_stat 批量追踪脚本（单函数模式）

执行 os_stat 追踪多个函数时，**每个函数追踪前都必须先 `rmmod os_aware`**，因为 os_stat 需要重新 insmod 来设置新的 ftrace hook。推荐使用以下批量追踪脚本：

**注意**：批量追踪 8 个函数约需 80 秒（每个 5 秒追踪 + 5 秒间隔）。脚本自动后台执行并输出日志到 `/tmp/batch_trace_output.log`，无需手动 nohup。

```bash
#!/bin/bash
LOGFILE="/tmp/batch_trace_output.log"
FUNCS=(vfs_read vfs_write do_sys_open ext4_sync_file generic_perform_write generic_file_buffered_read generic_update_time pagecache_get_page)
DURATION=5

safe_rmmod() {
    rmmod os_aware 2>/dev/null
    sleep 5
    if lsmod | grep -q os_aware; then
        exit 1
    fi
}

do_trace() {
    safe_rmmod
    if timeout 10 t-ops os_stat -f vfs_read -fg 1 -de 2 -o 0 2>&1 | grep -q "command.*invalid"; then
        OS_STAT_CMD="t-ops latency os_stat"
    else
        OS_STAT_CMD="t-ops os_stat"
    fi
    safe_rmmod

    for f in ${FUNCS[@]}; do
        echo "=== Tracing $f ==="
        safe_rmmod
        $OS_STAT_CMD -f $f -fg 1 -de $DURATION -o 0 > /tmp/os_stat_${f}.log 2>&1
        echo "=== Done $f ==="
    done
    safe_rmmod

    echo ""
    for f in ${FUNCS[@]}; do
        echo "========== $f =========="
        grep -E '(ave|max|min|p90|p95|p99|num)' /tmp/os_stat_${f}.log | sed 's/\x1b\[[0-9;]*m//g'
        echo
    done
    echo "ALL_DONE"
}

nohup bash -c "$(declare -f safe_rmmod do_trace); FUNCS=(${FUNCS[*]}); DURATION=$DURATION; do_trace" > "$LOGFILE" 2>&1 &
echo "PID=$! — 日志: $LOGFILE"
echo "查看进度: tail -f $LOGFILE"
echo "等待完成: grep -q ALL_DONE $LOGFILE"
```

##### func_tree.txt 制作方法（热路径模式，高级可选）

热路径模式（`-fg 0`，即 `t-ops os_stat <内核源码目录> <函数> 0 1`）依赖 `func_tree.txt` 文件，该文件记录函数调用关系树。**只需制作一次**，后续复用。

**方式一**：通过 `stat.sh` 跑一遍自动生成

`stat.sh` 是 os_stat 的底层脚本，首次对某个函数执行热路径扫描时（热点参数设 `1`），它会自动调用 cflow 在指定的内核源码目录中生成 `func_tree.txt`。

```bash
# 首次扫描（第4参数=1 表示生成 func_tree.txt），后续复用（设0）
t-ops os_stat /path/to/linux-source vfs_read 0 1
# stat.sh 会在内核源码目录下自动执行 cflow 生成 func_tree_vfs_read.txt
# 后续再追踪同一函数时复用已有的 func_tree.txt：
t-ops os_stat /path/to/linux-source vfs_read 0 0
```

**方式二**：手动执行 cflow 命令直接制作

不依赖 stat.sh，直接用 cflow 分析内核源码生成函数调用树：

```bash
# 参数说明:
#   depth: 调用深度（推荐 5-8）
#   test_func: 目标函数名（如 vfs_read）
#   path: 内核源码子目录（如 /root/linux/fs）
#   $1: 内核源码根目录（如 /root/linux）
# 示例: 分析 vfs_read 的调用树，深度 6
depth=6
test_func=vfs_read
path=/root/linux/fs
cflow -T -d $depth -i _ -m $test_func $path/*.c $path/*.h /root/linux/include/*.h /root/linux/include/*/*.h -o func_tree_vfs_read.txt 2> cflow_err.txt

# 分析 ext4_sync_file
test_func=ext4_sync_file
path=/root/linux/fs/ext4
cflow -T -d 6 -i _ -m $test_func $path/*.c $path/*.h /root/linux/include/*.h /root/linux/include/*/*.h -o func_tree_ext4_sync_file.txt 2> cflow_err.txt
```

**cflow 参数说明**：
- `-T`：生成树形输出
- `-d $depth`：最大递归深度
- `-i _`：忽略以 `_` 开头的内部函数
- `-m $test_func`：指定入口函数

**内核源码来源**：不要求精确匹配 TencentOS 内核，使用同版本号的开源 Linux 内核源码即可（如 linux-5.4.241），大概函数对应即可。能定位到父子函数关系就够了。

**注意**：执行 cflow 前需确认已安装 cflow（`which cflow || yum install cflow -y`），并且内核源码目录下有对应的 `.c` 和 `.h` 文件。

##### VFS 层追踪（通用文件读写路径）

VFS 层是所有文件IO的入口，从这里开始追踪可以看到完整的文件IO调用链。

```bash
# === 读路径追踪 ===
# vfs_read → __vfs_read → new_sync_read → call_read_iter → ext4_file_read_iter/xfs_file_read_iter
t-ops os_stat /data/linux vfs_read 0 1

# === 写路径追踪 ===
# vfs_write → __vfs_write → new_sync_write → call_write_iter → ext4_file_write_iter/xfs_file_write_iter
t-ops os_stat /data/linux vfs_write 0 1

# === 文件打开路径 ===
# do_sys_open → do_filp_open → path_openat → lookup_open → ext4_lookup/xfs_vn_lookup
t-ops os_stat /data/linux do_sys_open 0 1

# === fsync 路径 ===
# vfs_fsync → vfs_fsync_range → ext4_sync_file/xfs_file_fsync
t-ops os_stat /data/linux vfs_fsync_range 0 1

# === 文件 stat 路径 ===
t-ops os_stat /data/linux vfs_statx 0 1
t-ops os_stat /data/linux vfs_getattr 0 1

# === 目录操作路径 ===
t-ops os_stat /data/linux vfs_mkdir 0 1
t-ops os_stat /data/linux vfs_rmdir 0 1
t-ops os_stat /data/linux vfs_unlink 0 1
t-ops os_stat /data/linux vfs_rename 0 1

# === 文件截断路径 ===
t-ops os_stat /data/linux vfs_truncate 0 1

# === readlink 路径 ===
t-ops os_stat /data/linux vfs_readlink 0 1
```

##### Page Cache 层追踪（缓存读写路径）

Page cache 是文件IO性能的关键，追踪 page cache 的命中、分配、回写等路径。

```bash
# === buffered read 路径（page cache 读） ===
# generic_file_buffered_read → pagecache_get_page → (cache hit 或 readpage)
t-ops os_stat /data/linux generic_file_buffered_read 0 1

# === buffered write 路径（page cache 写） ===
# generic_perform_write → pagecache_get_page → a_ops->write_begin → copy_from_user → a_ops->write_end
t-ops os_stat /data/linux generic_perform_write 0 1

# === page cache 查找 ===
t-ops os_stat /data/linux pagecache_get_page 1 0

# === readahead 预读路径 ===
t-ops os_stat /data/linux page_cache_sync_readahead 1 0
t-ops os_stat /data/linux page_cache_async_readahead 1 0

# === filemap_fault（mmap 缺页路径） ===
t-ops os_stat /data/linux filemap_fault 0 1

# === 脏页回写路径 ===
t-ops os_stat /data/linux filemap_fdatawrite_range 0 1
t-ops os_stat /data/linux filemap_write_and_wait_range 0 1

# === page cache 分配 ===
t-ops os_stat /data/linux __page_cache_alloc 1 0
```

##### EXT4 文件系统层追踪

```bash
# === ext4 读路径 ===
# ext4 buffered read: generic_file_read_iter → generic_file_buffered_read
t-ops os_stat /data/linux generic_file_read_iter 0 1

# === ext4 写路径（delayed allocation） ===
# ext4_file_write_iter → __generic_file_write_iter → generic_perform_write
#   → ext4_da_write_begin → ext4_da_write_end
t-ops os_stat /data/linux ext4_da_write_begin 0 1
t-ops os_stat /data/linux ext4_da_write_end 0 1

# === ext4 fsync 路径 ===
# ext4_sync_file → jbd2_complete_transaction → ...
t-ops os_stat /data/linux ext4_sync_file 0 1

# === ext4 extent 映射（文件块分配/碎片化诊断） ===
t-ops os_stat /data/linux ext4_ext_map_blocks 0 1

# === ext4 inode 写入 ===
t-ops os_stat /data/linux ext4_write_inode 0 1

# === ext4 page mkwrite（mmap 写时复制） ===
t-ops os_stat /data/linux ext4_page_mkwrite 0 1

# === ext4 writepages（脏页批量回写） ===
t-ops os_stat /data/linux ext4_bio_write_page 0 1

# === ext4 inline data 操作 ===
t-ops os_stat /data/linux ext4_readpage_inline 1 0
t-ops os_stat /data/linux ext4_try_to_write_inline_data 1 0
```

##### XFS 文件系统层追踪

```bash
# === xfs 读路径 ===
t-ops os_stat /data/linux xfs_file_read_iter 0 1

# === xfs 写路径 ===
t-ops os_stat /data/linux xfs_file_write_iter 0 1
# 更细分：buffered write
t-ops os_stat /data/linux xfs_file_buffered_write 0 1

# === xfs fsync 路径 ===
t-ops os_stat /data/linux xfs_file_fsync 0 1

# === xfs 日志相关 ===
t-ops os_stat /data/linux xfs_log_force 1 0

# === xfs 缓冲区等待（mount/umount 卡住常见原因） ===
t-ops os_stat /data/linux xfs_wait_buftarg 1 0
```

##### atime 写放大追踪

atime 更新是常见的文件IO写放大来源——每次读文件都会触发 inode 写入。

```bash
# 追踪时间戳更新频率和延迟
t-ops os_stat /data/linux generic_update_time 1 0

# 交互式诊断（新版 t-ops）
t-ops interaction io scene_io show_time_update
```

##### 交互式文件IO诊断（新版 t-ops）

如果机器上安装了新版 t-ops（包含 interaction 子命令）：

```bash
# 系统整体性能检查（含文件IO系统调用时延）
t-ops interaction system system_performance 1

# IO 诊断
t-ops interaction io scene_io io_diagnosis

# 文件系统时间戳更新追踪
t-ops interaction io scene_io show_time_update
```

##### os_stat 输出解读

**重要**：`t-ops os_stat` 的输出包含 ANSI color escape codes，直接查看或 grep 结果会有乱码。查看和处理结果时需要清理：
```bash
# 清理 ANSI 转义码
sed 's/\x1b\[[0-9;]*m//g'
# 示例：查看追踪日志
cat /tmp/os_stat_vfs_read.log | sed 's/\x1b\[[0-9;]*m//g'
```

###### `-fg 1` 单函数模式输出格式（日常诊断主要模式）

```
=== ave ===: num:     628, latency:    1594(ns), block latency:   12774(ns), vfs_read
=== max ===: num:      32, latency:    3644(ns), block latency:    3644(ns), vfs_read
=== min ===: num:     190, latency:    1150(ns), block latency:   13432(ns), vfs_read
=== p90 ===: num:     596, latency:    3644(ns), block latency:    3644(ns), vfs_read
=== p95 ===: num:     596, latency:    3644(ns), block latency:    3644(ns), vfs_read
=== p99 ===: num:     596, latency:    3644(ns), block latency:    3644(ns), vfs_read
```

**字段说明：**
- **num**：采样周期内的调用次数（ave 行的 num 为平均每周期调用次数）
- **latency**：函数执行延迟（纳秒），分为 ave/max/min/p90/p95/p99 百分位
- **block latency**：函数内部阻塞等待的延迟（纳秒），如 IO 等待、锁等待等。**block latency >> latency 说明函数存在显著的阻塞行为**（如 `ext4_sync_file` 的 block latency 通常远大于 latency，因为 fsync 需要等待 jbd2 journal commit 和磁盘落盘）

**`-fg 1` 分析要点：**
- **latency ave > 10μs 的函数**：需要关注，可能存在锁等待或 cache miss
- **block latency >> latency**：说明函数内有显著阻塞（IO 等待/锁竞争）
- **num 为 0 且出现 `error:-1`**：os_aware 模块加载失败或 hook 异常，需检查兼容性（参见"os_aware.ko 兼容性处理"和"os_stat 命令格式"章节）
- **出现 `need rmmod os_aware`**：前次追踪的模块未卸载干净，需增加 `rmmod os_aware` 后的等待时间（建议 `sleep 5`）

###### `-fg 0` 热路径模式输出格式（高级调试）

```
# 输出格式:
# real_index: 全局索引, index: 相对索引, level: 调用层级
# num: 调用次数, latency: 平均延迟(ns), total_latency: 总延迟(ns)
# func: 函数名, origin: 原始函数/函数指针实际指向

******real index:  1, index:  1, level: 0, num:: 803038, latency: 3312 ns, total latency: 2659661856 ns, func:vfs_read, origin:vfs_read
******real index:  2, index:  2, level: 1, num:: 803038, latency: 2800 ns, total latency: 2248509400 ns, func:__vfs_read, origin:__vfs_read
******real index:  3, index:  3, level: 2, num:: 350000, latency: 5100 ns, total latency: 1785000000 ns, func:new_sync_read, origin:new_sync_read
******real index:  4, index:  4, level: 3, num:: 350000, latency: 4800 ns, total latency: 1680000000 ns, func:ext4_file_read_iter, origin:ext4_file_read_iter
******real index:  5, index:  5, level: 4, num:: 350000, latency: 4200 ns, total latency: 1470000000 ns, func:generic_file_buffered_read, origin:generic_file_buffered_read
******real index:  6, index:  6, level: 5, num:: 280000, latency: 200 ns, total latency: 56000000 ns, func:pagecache_get_page, origin:pagecache_get_page    ← 80% cache hit
******real index:  7, index:  7, level: 5, num:: 70000, latency: 15000 ns, total latency: 1050000000 ns, func:__do_page_cache_readahead, origin:__do_page_cache_readahead ← 20% miss
```

**`-fg 0` 分析方法**：
1. `level` = 调用深度（0=根函数）
2. 找 `latency` 最高的叶子函数 → 那就是瓶颈点
3. 父函数 `latency` - 子函数 `latency` 之和 = 父函数自身开销（锁、条件判断等）
4. `num` 不同的函数 → 说明有分支（如 cache hit/miss 走不同路径）
5. `origin` 为函数指针的函数 → 如 `file->f_op->read_iter` 实际指向 `ext4_file_read_iter`
6. 子函数 `latency` 之和 << 父函数 `latency` → 时间花在父函数自身逻辑（锁、条件判断等）

#### 2B：传统工具降级方案（t-ops不可用时）

```bash
# === strace：追踪进程的文件IO系统调用 ===
# 统计文件IO系统调用的延迟分布
strace -e trace=open,openat,read,write,close,fsync,fdatasync,stat,fstat,lstat,getdents -c -p <PID> -f 2>&1

# 逐个追踪文件IO系统调用（显示时间戳和耗时）
strace -e trace=open,openat,read,write,close,fsync -T -t -p <PID> 2>&1 | head -100

# 只看慢的文件IO调用（>10ms）
strace -e trace=read,write,fsync -T -p <PID> 2>&1 | awk -F'<|>' '$NF+0 > 0.01'

# === perf：追踪文件系统 tracepoint 事件 ===
# ext4 事件追踪
perf trace -e 'ext4:ext4_da_write_begin,ext4:ext4_da_write_end,ext4:ext4_sync_file_enter,ext4:ext4_sync_file_exit' -a sleep 5

# ext4 完整事件追踪
perf trace -e 'ext4:*' -a sleep 5

# xfs 事件追踪
perf trace -e 'xfs:*' -a sleep 5

# writeback 事件追踪（脏页回写）
perf trace -e 'writeback:*' -a sleep 5

# filemap 事件追踪（page cache）
perf trace -e 'filemap:*' -a sleep 5

# === perf：VFS 函数级热点 ===
# 追踪文件读写的 CPU 热点
perf record -g -e 'probe:vfs_read' -a sleep 10
perf report --sort=symbol

# === /proc/<PID>/io：进程级文件IO统计 ===
# rchar/wchar: 进程读写字节数（含 page cache）
# syscr/syscw: read/write 系统调用次数
# read_bytes/write_bytes: 实际磁盘IO字节数
cat /proc/<PID>/io
# 对比 syscr/syscw vs read_bytes/write_bytes 可判断 page cache 命中率：
# syscr 大但 read_bytes 小 → cache 命中率高
# syscr 大且 read_bytes 也大 → cache 命中率低

# === /proc/<PID>/fdinfo：文件描述符详情 ===
ls -la /proc/<PID>/fd | wc -l   # fd 数量
ls -la /proc/<PID>/fd | head -20  # 打开的文件列表

# === XFS 专用工具 ===
xfs_info /dev/sdX       # 查看 XFS 文件系统参数
xfs_db -r /dev/sdX      # 交互式调试器（只读）
xfs_bmap -v file        # 查看文件块映射（碎片分析）
xfs_fsr /dev/sdX        # 碎片整理

# === EXT4 专用工具 ===
tune2fs -l /dev/sdX     # 查看 ext4 参数
dumpe2fs /dev/sdX 2>/dev/null | grep -E "(Block count|Free blocks|Inode count|Free inodes|Block size|Journal)"
e4defrag -c /mount/point  # 碎片统计（只读）
filefrag filename        # 单文件碎片分析

# === iostat：块设备概览 ===
iostat -x -t 1 10

# === iotop/pidstat：进程级IO ===
iotop -o -b -n 5
pidstat -d 1 5
```

**t-ops vs 传统工具对比**：

| 维度 | t-ops (os_stat) | 传统工具 |
|------|----------------|---------|
| 精度 | 纳秒（内核函数级） | 微秒（系统调用级） |
| 开销 | < 1% | strace 200-500% |
| 调用树展开 | 自动递归 | 手动探测 |
| 函数指针解析 | 自动 | 不支持 |
| 生产可用 | 是 | strace 不适合生产 |

### 步骤 3：分析诊断

根据采集数据，与 14 类已知瓶颈模式比对。

#### 14 类文件 IO 瓶颈模式

| # | 模式名称 | 触发条件 | os_stat 特征 | 传统工具特征 |
|---|---------|----------|-------------|-------------|
| 1 | Page cache miss | 读延迟高 | `pagecache_get_page` num 大但 `__do_page_cache_readahead` latency 高 | `syscr` 大且 `read_bytes` 也大 |
| 2 | atime 写放大 | 读操作触发写 | `generic_update_time` 被频繁调用 | 挂载参数无 noatime |
| 3 | fsync 慢 | 数据库写入卡 | `ext4_sync_file` → `jbd2_complete_transaction` latency 高 | jbd2 info commit time 高 |
| 4 | 文件碎片化 | 顺序读变慢 | `ext4_ext_map_blocks` latency 高 | `filefrag` 显示 extent 数多 |
| 5 | 挂载参数错误 | 写放大/同步慢 | data=journal 下写路径双倍 | `findmnt` 检查 |
| 6 | dentry/inode 缓存不足 | stat/open 慢 | `do_sys_open` → `lookup_open` latency 高 | `dentry-state` 未使用数低 |
| 7 | fd 耗尽 | open 失败 | - | `file-nr` 接近 `file-max` |
| 8 | inode 耗尽 | 创建文件失败 | - | `df -i` 使用率 > 95% |
| 9 | ext4 回写风暴 | 写延迟间歇飙高 | `balance_dirty_pages_ratelimited` latency 高 | 磁盘使用率 > 90%, dirty 页多 |
| 10 | 大目录 lookup 慢 | open/stat 慢 | `path_openat` → `ext4_lookup` latency 高 | 目录下文件数 > 10万 |
| 11 | mmap 缺页率高 | 应用抖动 | `filemap_fault` latency 高且 num 大 | - |
| 12 | 文件系统锁竞争 | 并发操作慢 | 父函数 latency >> 子函数之和（时间花在锁上）| - |
| 13 | XFS 日志瓶颈 | fsync 慢 | `xfs_log_force` latency 高 | `xfs_info` logbsize 小 |
| 14 | 内核函数热点 | 特定操作慢 | 某个函数 latency 占比 > 80% | - |

#### 关键指标告警条件

| 指标 | 含义 | 告警条件 |
|------|------|----------|
| 磁盘使用率 (df -h) | 空间使用 | > 90%（ext4 触发 nonda_switch） |
| inode 使用率 (df -i) | inode 消耗 | > 80% |
| fs.file-nr | fd 使用 | 已分配 > 80% 最大值 |
| Cached (meminfo) | page cache 大小 | 远小于文件工作集 |
| Active(file)/Inactive(file) | 活跃/非活跃比 | Active << Inactive 可能命中率低 |
| Dirty (meminfo) | 脏页大小 | 持续 > 数百MB |
| Writeback (meminfo) | 回写中的页 | 持续 > 0 |
| iostat %util | 设备利用率 | > 80% 表示接近饱和 |
| iostat await | IO 等待时间 | HDD > 20ms, SSD > 5ms |

### 步骤 4：输出诊断报告

```
=== 文件 IO 性能分析报告 ===

状态: [正常/警告/异常]

--- 基础信息 ---
操作系统: TencentOS Server X.X
内核版本: X.X.X
文件系统: /mount (ext4/xfs, rw,relatime,data=ordered)
t-ops: [可用 vX / 不可用（降级到传统工具）]

--- 关键指标 ---
文件描述符: X/Y (已用/最大)
inode 使用率: X%
Page cache: X MB (Active file: Y MB, Inactive file: Z MB)
脏页: X KB (Dirty) / Y KB (Writeback)
磁盘使用率: X%

--- 函数级追踪结果（如有 t-ops）---
追踪入口: vfs_read
  调用次数: X, 平均延迟: X ns
  热点路径: vfs_read → ... → 瓶颈函数(Xns)
  瓶颈函数: func_name, latency: Xns, 占比: X%

--- 发现的问题 ---
1. [严重程度: 高/中/低] 问题描述
2. [严重程度: 高/中/低] 问题描述

--- 优化建议 ---
1. [优先级: 高] [风险: 低] 建议描述
   操作: mount -o remount,noatime /data
2. [优先级: 中] [风险: 中] 建议描述
   操作: sysctl -w vm.dirty_background_ratio=5
```

---

## 典型案例

### 案例 1：read 延迟高（page cache miss）

**现象**：应用 read 系统调用平均延迟 > 5ms
**排查路径**：
1. `strace -e trace=read -T -c -p <PID>` → 确认 read 延迟分布
2. `cat /proc/<PID>/io` → 对比 `syscr` vs `read_bytes`，发现 read_bytes/syscr ≈ 4KB，命中率低
3. `t-ops os_stat /data/linux vfs_read 0 1` → 热点在 `generic_file_buffered_read` → `__do_page_cache_readahead`
4. `cat /proc/meminfo` → page cache 仅占内存 10%
**结论**：page cache 不足导致频繁从磁盘加载
**建议**：减小 `vm.vfs_cache_pressure`（如 50）；检查是否有其他进程竞争内存；应用层增大读缓冲区减少 syscall 次数

### 案例 2：fsync 延迟高（journal commit 慢）

**现象**：数据库 WAL 写入 fsync 平均 50ms
**排查路径**：
1. `strace -e trace=write,fsync -T -p <PID>` → fsync 平均 48ms
2. `t-ops os_stat /data/linux ext4_sync_file 0 1` → 热点在 `jbd2_complete_transaction`
3. 检查挂载参数：`data=journal`
**结论**：data=journal 导致 fsync 写放大
**建议**：改为 `data=ordered`；或使用 O_DIRECT

### 案例 3：atime 导致读操作写放大

**现象**：读多写少的应用，但发现大量 inode 写入
**排查路径**：
1. `t-ops os_stat /data/linux generic_update_time 1 0` → 每次 read 都触发
2. 检查挂载参数：无 noatime/relatime
3. `t-ops os_stat /data/linux vfs_read 0 1` → 大量时间在 `file_accessed` → `generic_update_time`
**结论**：atime 更新导致每次读都触发 inode 写入
**建议**：`mount -o remount,noatime /data`

### 案例 4：大目录下文件操作慢

**现象**：单目录 100 万文件，open 延迟 > 10ms
**排查路径**：
1. `t-ops os_stat /data/linux do_sys_open 0 1` → 热点在 `ext4_lookup`
2. `tune2fs -l /dev/sdX | grep dir_index` → 未启用 dir_index
**结论**：大目录线性扫描查找
**建议**：启用 dir_index；拆分目录层级

### 案例 5：ext4 空间不足触发回写风暴

**现象**：业务写操作不频繁，但文件写延迟间歇性飙高
**排查路径**：
1. `df -h` → 使用率 > 90%
2. `t-ops os_stat /data/linux generic_perform_write 0 1` → 追踪写路径
3. 发现 `balance_dirty_pages_ratelimited` 延迟高 → dirty_ratio 触发同步回写
4. ext4 判断 free clusters < 2 × dirty clusters → `ext4_nonda_switch` 返回 true → 强制回写所有脏数据
**结论**：ext4 空间管理策略触发写回风暴，强制关闭延迟分配
**建议**：紧急清理空间至 80% 以下；增加磁盘容量或调整 `dirty_writeback_centisecs`

## 碎片化检测

```bash
# ext4 碎片化
e4defrag -c /mount/point 2>/dev/null
filefrag <file>  # 单文件碎片

# xfs 碎片化
xfs_db -r -c frag /dev/sdX 2>/dev/null
```

**分析要点**：
- 碎片化指数 > 30% 建议整理
- HDD 影响明显，SSD 影响较小
- 碎片整理在业务低峰期执行

## 深度分析工具（可选）

```bash
# BCC/bpftrace 工具（install-deps.sh --all 已自动创建软链接，可直接调用）
biolatency 10 1          # 块设备 IO 延迟分布
ext4slower 10            # ext4 慢操作 >10ms
fileslower 10            # 所有文件系统慢操作
filetop 5                # 文件级 IO Top

# blktrace 块设备追踪
blktrace -d /dev/sdX -w 10 -o trace_data
blkparse -i trace_data -d trace_data.bin
btt -i trace_data.bin    # Q2C=总延迟, D2C=设备服务时间

# perf 文件系统事件
perf trace -e 'ext4:*' -a sleep 5
perf trace -e 'writeback:*' -a sleep 5
```

## 常见问题

### Q: 如何区分文件系统层延迟和块设备层延迟？

A: 使用 blktrace 的 btt 分析。`Q2C`（总延迟）= 文件系统层 + 块设备层。`D2C` 是纯设备延迟。若 `Q2C - D2C` 很大，瓶颈在文件系统层。

### Q: vm.dirty_ratio 怎么调？

A: 推荐：
- 数据库（低延迟）：`dirty_background_ratio=3`, `dirty_ratio=10`
- 日志写入（高吞吐）：`dirty_background_ratio=10`, `dirty_ratio=30`

### Q: ext4 和 xfs 延迟方面有什么区别？

A: ext4 的 jbd2 在高并发写入时可能成为瓶颈（日志锁争用）。xfs 使用延迟分配和更细粒度的锁，大文件高并发场景通常更好。但 ext4 在小文件和元数据操作上通常更快。

## 注意事项

- **新机器首次执行 os_stat 前必须做兼容性处理**：检查 `os_aware_$(uname -r).ko.xz` 文件是否存在，不存在则创建符号链接指向已有的 `os_aware.ko`（详见"os_aware.ko 兼容性处理"章节）
- **每次追踪新函数前必须 `rmmod os_aware`**：os_stat 需要重新 insmod 来设置 ftrace hook，如果 os_aware 已加载会直接退出或报错。**`rmmod` 后建议 `sleep 5`**，间隔过短可能导致下次追踪报 `need rmmod os_aware` 错误
- **os_stat 命令格式存在版本差异**：v4.2.12 用 `t-ops os_stat`（旧格式），v4.2.17+ 用 `t-ops latency os_stat`（新格式，旧格式已移除）。探测方法：先尝试旧格式，若报 `command.*invalid` 则切新格式。v4.2.17+ 新格式运行时可能输出 `open error:-1`，属正常现象，不影响最终数据
- **os_stat 输出包含 ANSI color escape codes**，查看和 grep 结果时需加 `sed 's/\x1b\[[0-9;]*m//g'` 清理
- **批量追踪脚本已内置后台执行**，8 个函数追踪约需 80 秒，执行后自动 nohup 到后台，日志输出到 `/tmp/batch_trace_output.log`
- `t-ops os_stat` 单函数模式（`-fg 1`）无需内核源码；热路径模式（`-fg 0`）需要 cflow + 内核源码生成 `func_tree.txt`（只需一次，开源同版本源码即可）
- os_stat 的函数指针解析依赖 `func_pointer_table*.c` 中的映射表，不同内核版本使用不同映射
- strace 会显著影响被追踪进程性能（2-5x 减速），生产环境慎用
- perf trace 的 tracepoint 开销较小，适合生产环境
- 优化建议涉及修改时，提醒用户在维护窗口操作
- 先备份再操作；XFS 慎用 `xfs_repair -L`（会丢弃日志）

## 参考资料

- [Linux Storage Stack Diagram](https://www.thomas-krenn.com/en/wiki/Linux_Storage_Stack_Diagram)
- [BCC tools for I/O analysis](https://github.com/iovisor/bcc)
- [ext4 Performance Tuning](https://ext4.wiki.kernel.org/index.php/Ext4_Howto)
- [XFS FAQ](https://xfs.org/index.php/XFS_FAQ)
