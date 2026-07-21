# memory-leak 使用手册

Linux 用户态内存泄漏诊断工具，通过对进程内存多次采样，计算 RSS/PSS 增长速率，判定是否存在内存泄漏，并预测 OOM 触发时间.

**依赖**: bash、python3、ps（系统自带）。可选 bcc-tools 启用 eBPF 调用栈追踪.

---

## 快速开始

```bash
# 全局扫描：找出哪个进程在泄漏
bash scripts/collect_memory_leak.sh

# 监控指定进程名
bash scripts/collect_memory_leak.sh -n java

# 监控指定 PID，加长采样时间（更准确）
bash scripts/collect_memory_leak.sh -p 1234 -c 10 -i 30

# 查看结果
cat /tmp/memory-leak-<timestamp>/summary.json
```

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p <pid>` | 目标进程 PID，优先于 `-n` | (空) |
| `-n <name>` | 目标进程名，模糊匹配（如 java、nginx） | (空) |
| `-c <count>` | 采样次数（建议 ≥ 3） | 6 |
| `-i <interval>` | 采样间隔秒数 | 10 |
| `-t <top_n>` | 全局扫描显示 Top N 进程 | 5 |
| `-o <log_dir>` | 日志输出目录 | `/tmp/memory-leak-<timestamp>` |
| `-j <task_id>` | 任务 ID，写入 summary.json | 自动生成 |
| `-h` | 显示帮助 | — |

**监控模式**：
- 指定 `-p` 或 `-n` → 单进程监控
- 两者均不指定 → 全局扫描，找出增长最快的 Top N 进程

**实际监控时长** = `(count - 1) × interval` 秒

---

## 核心诊断功能

| 功能 | 说明 |
|------|------|
| **单进程监控** | 指定 PID 或进程名，多次采样目标进程内存 |
| **全局扫描** | 自动扫描全机所有进程，找出 RSS 增长最快的 Top N |
| **RSS/PSS 双轨采集** | 读取 `/proc/<pid>/status`（RSS）+ `smaps_rollup`（PSS），PSS 排除共享内存更准确 |
| **增长速率计算** | 计算 KB/min 和 %/min，基于多次时序采样 |
| **泄漏判定** | 四级结论：`leak_confirmed`（>2%/min）/ `leak_suspected`（1~2%/min）/ `normal` / `insufficient_data` |
| **单调性分析** | 检测 RSS 是否严格单调递增（无回落），单调递增将判定升级一级 |
| **增长趋势分析** | 二阶导数判断趋势：`accelerating`（加速）/ `decelerating`（减速）/ `linear`（匀速） |
| **OOM 时间预测** | 基于 `MemAvailable / growth_rate` 预测可用内存耗尽时间，含 Swap 说明 |

---

## 辅助检测

| 功能 | 说明 |
|------|------|
| **文件描述符泄漏** | 统计 `/proc/<pid>/fd` 数量，> 5000 告警 |
| **内核 slab 泄漏** | 读取 `/proc/meminfo` 中 `SUnreclaim`，> 500MB 告警 |
| **dmesg OOM 历史** | 检查是否已有 OOM 事件发生 |
| **进程中途退出检测** | 监控期间进程消失时保留已采集数据并输出初步分析 |
| **多进程同步增长告警** | 全局模式下 >2 个进程增量超 50MB 时，提示可能是共享库泄漏 |
| **新进程/消失进程追踪** | 全局模式下记录监控期间出现和消失的进程 |

---

## eBPF 增强（可选）

若系统安装了 bcc-tools，脚本会**自动**并行启动 `memleak`，追踪未释放内存的调用栈，不额外增加总耗时.

```bash
# TencentOS 2 / CentOS 7
yum install -y bcc-tools
# TencentOS 3/4 / CentOS 8+
dnf install -y bcc-tools
# Ubuntu / Debian
apt-get install -y bpfcc-tools
```

eBPF 调用栈示例输出：
```
62915790 bytes in 30 allocations from stack
    PyObject_Malloc+0x158 [libpython3.12.so.1.0]
```

---

## 输出结构

```
<log_dir>/
├── summary.json           # 结构化诊断结果（主要读取此文件）
└── raw/
    ├── config.json        # 本次运行配置
    ├── sample_N.json      # 每次采样快照（RSS/PSS/VmAnon/fd_count）
    ├── meminfo_N.log      # 每次采样时的全局内存状态
    ├── meminfo_baseline.log
    ├── memleak_stack.log  # eBPF 调用栈（若已采集）
    ├── slabinfo.log       # 内核 slab 快照
    └── dmesg_oom.log      # OOM 历史日志
```

### summary.json 示例

```json
{
  "leak_verdict": "leak_confirmed",
  "growth": {
    "rss_start_kb": 63156,
    "rss_end_kb": 114636,
    "rss_delta_kb": 51480,
    "growth_rate_kb_per_min": 61776.0,
    "growth_pct_per_min": 97.81,
    "is_monotonic": true,
    "trend": "linear",
    "rss_series_kb": [63156, 73452, 83748, 94044, 104340, 114636]
  },
  "oom_prediction": {
    "available_mem_kb": 26501784,
    "eta_minutes": 429.0,
    "eta_human": "约 7.1 小时",
    "note": "线性外推，实际受内核回收、业务波动影响，仅供参考"
  },
  "fd_count": 3,
  "ebpf_stacks": "PyObject_Malloc+0x158 [libpython3.12.so.1.0]",
  "key_findings": [
    "进程 python3 (PID 1530395) RSS 增长 50.3MB/1min，速率 97.81%/min，判定: 确认泄漏",
    "RSS 6 次采样持续单调递增，无回落，泄漏特征明显",
    "按当前增速，预计 约 7.1 小时 后可用内存耗尽"
  ]
}
```

---

## 常用场景

```bash
# 场景 1：不知道哪个进程在泄漏，全局扫一遍
bash scripts/collect_memory_leak.sh -o /tmp/result

# 场景 2：Java 服务内存一直在涨，监控 5 分钟
bash scripts/collect_memory_leak.sh -n java -c 10 -i 30 -o /tmp/java_leak

# 场景 3：已知 PID，快速确认（30s）
bash scripts/collect_memory_leak.sh -p 12345 -c 4 -i 10

# 场景 4：定时任务周期采样，输出到固定目录
bash scripts/collect_memory_leak.sh -n myapp \
  -c 6 -i 10 \
  -o /var/log/memleak/$(date +%Y%m%d_%H%M) \
  -j "cron_$(date +%Y%m%d_%H%M)"
```

---

## 功能边界

- **不支持内核模块泄漏精确定位**：只能检测 `SUnreclaim` 异常，需配合 `slabtop` 手动分析
- **不自动触发 Java heap dump**：只输出建议命令，需用户手动执行 `jmap`
- **不修改任何系统配置、不 kill 进程**：只读诊断
- **eBPF 调用栈依赖符号表**：stripped 二进制只显示 `[unknown]`
- **OOM 预测为线性外推**：实际受内核回收、业务波动影响，仅供参考
