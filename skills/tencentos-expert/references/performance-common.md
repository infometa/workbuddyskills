# 共享 Prompt 片段：性能分析通用指令

## 性能分析前置检查

在开始性能分析之前，请确认以下事项：

### 1. 工具可用性检查

```bash
# 检查 perf 工具
which perf && perf --version

# 检查 bpftrace（如果需要）
which bpftrace && bpftrace --version

# 检查 strace
which strace && strace -V

# 检查 sysstat 工具集
which sar && sar -V
```

### 2. 权限检查

```bash
# 检查 perf_event_paranoid 设置
cat /proc/sys/kernel/perf_event_paranoid
# 建议值: -1 或 0（允许非 root 用户使用 perf）

# 检查 kptr_restrict 设置
cat /proc/sys/kernel/kptr_restrict
# 建议值: 0（允许查看内核符号地址）
```

### 3. 符号表检查

```bash
# 检查内核符号表
ls -la /proc/kallsyms

# 检查 debuginfo 包
rpm -qa | grep debuginfo
```

## 性能数据采集注意事项

1. **采集时间**：根据问题复现周期选择合适的采集时长
2. **采集频率**：平衡数据精度和系统开销
3. **目标进程**：明确要分析的进程或系统范围
4. **数据存储**：确保有足够的磁盘空间存储采集数据

## 结果分析框架

```
=== 性能分析报告 ===

分析目标: [进程名/PID/系统整体]
分析时间: [开始时间] - [结束时间]
采集时长: [X 秒/分钟]

--- 关键指标 ---
CPU 使用率: X%
内存使用: X GB
I/O 等待: X%

--- 热点分析 ---
Top 5 热点函数:
1. function_name (X%)
2. ...

--- 问题定位 ---
发现问题: 
1. ...

--- 优化建议 ---
1. ...
```
