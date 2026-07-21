# OOM 诊断内存指标参考

> 本文件供 AI 在根因判定时参考，通过本地系统命令采集内存指标辅助分析。
> 所有命令均为标准 Linux 工具，无需额外安装。

---

## 一、时间窗口建议

以 OOM 事件触发时间为 `T`：

| 目的 | 建议窗口 |
|------|---------|
| 趋势分析（是否缓慢增长） | `T - 30min` ~ `T + 5min` |
| 突发定位（是否瞬间跳变） | `T - 10min` ~ `T + 5min` |
| 恢复确认（是否已恢复） | `T - 5min` ~ `T + 30min` |

---

## 二、当前内存状态快照

```bash
# 总体内存使用（available 列 = 真实可用内存）
free -h

# 详细内存信息
grep -E "MemTotal|MemAvailable|MemFree|Buffers|^Cached|SwapTotal|SwapFree|Slab" /proc/meminfo

# 内存占用最高的进程（Top 15）
ps aux --sort=-%rss | head -16

# 查看各进程 RSS 详情
ps -eo pid,comm,rss,vsz,oom_score_adj --sort=-rss | head -20
```

---

## 三、Swap 状态检查

```bash
# Swap 分区信息（是否启用、已用量）
cat /proc/swaps

# Swap 启用详情（含优先级）
swapon --show

# 检查 swappiness（内核使用 Swap 的积极性，60 为默认值）
cat /proc/sys/vm/swappiness
```

> **判断规则**：`/proc/swaps` 为空或 `SwapTotal == 0` → 未启用 Swap；`SwapFree == 0` → Swap 已耗尽。

---

## 四、内存压力趋势

```bash
# vmstat：每 5 秒采样一次，共 12 次（约 1 分钟）
# 关注 free(空闲)、si/so(swap in/out)、b(阻塞进程数)
vmstat 5 12

# sar 历史内存数据（需已安装 sysstat）
# 查看当天内存趋势
sar -r 1 | grep -A 999 "kbmemfree"

# 查看指定时间段（如 14:00 ~ 15:00）
sar -r -s 14:00:00 -e 15:00:00

# dmesg：查看内核内存相关事件（含 kswapd 活跃情况）
dmesg -T | grep -E "kswapd|page allocation|oom|Killed" | tail -30
```

---

## 五、cgroup 内存限制检查

```bash
# 查看是否有进程触发 cgroup OOM（日志中搜索）
grep "Memory cgroup out of memory" /var/log/messages /var/log/syslog 2>/dev/null

# 列出所有 cgroup 的内存限制（cgroup v1）
find /sys/fs/cgroup/memory -name "memory.limit_in_bytes" 2>/dev/null | while read f; do
    limit=$(cat "$f")
    # 过滤掉未设限制（值极大）的 cgroup
    [ "$limit" -lt 9223372036854775807 ] && echo "$limit bytes: $f"
done

# cgroup v2：列出内存限制
find /sys/fs/cgroup -name "memory.max" 2>/dev/null | while read f; do
    limit=$(cat "$f")
    [ "$limit" != "max" ] && echo "$limit: $f"
done
```

---

## 六、快速诊断命令组合

### 场景 A：怀疑内存泄漏（进程持续增长）

```bash
# 1. 确认被杀进程历史 RSS（从日志中提取）
grep "Killed process" /var/log/messages | tail -10

# 2. 查看同类进程当前内存
ps aux | grep <进程名> | awk '{print $6, $11}'

# 3. 检查是否有内存持续增长趋势
sar -r 1 60 | awk '{print $1, $2, $3}'  # 时间, kbmemfree, kbmemused
```

### 场景 B：怀疑突发大内存申请

```bash
# 查看 OOM 前后的系统内存快照（从日志提取 Node free 值）
grep "Node.*free:" /var/log/messages | grep -B5 -A5 "Out of memory"

# 检查是否有大量 page allocation failure
grep "page allocation failure" /var/log/messages | tail -20
```

### 场景 C：确认 cgroup 限制

```bash
# 确认触发类型
grep -E "Memory cgroup out of memory|Out of memory" /var/log/messages | tail -5

# 查看对应 cgroup 的限制（从日志中的 task_memcg 路径获取 cgroup 路径）
# 例：task_memcg=/system.slice/docker-xxx.scope
cat /sys/fs/cgroup/memory/system.slice/docker-xxx.scope/memory.limit_in_bytes
```

### 场景 D：确认 Swap 未开启/耗尽

```bash
free -h | grep Swap
cat /proc/swaps
# SwapTotal 为 0 → 未开启；SwapFree 为 0 → 已耗尽
```
