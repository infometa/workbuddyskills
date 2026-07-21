# 内核 OOM 日志特征库

> 本文件供 AI 在 Step 1（日志解析）和 Step 2（根因判定）时参考。

---

## 一、OOM 日志结构

Linux 内核触发 oom-killer 时，会在 dmesg / syslog 日志中输出一段固定格式的信息，
通常包含以下三个部分：

### 1.1 触发行（OOM 事件入口）

```
<时间戳> kernel: <进程名>: page allocation failure ...
<时间戳> kernel: Out of memory: Kill process <pid> (<name>) score <score> or sacrifice child
<时间戳> kernel: Out of memory (oom_kill_allocating_task) ...   # cgroup OOM 变体
<时间戳> kernel: Memory cgroup out of memory: Kill process ...  # cgroup OOM
```

**关键正则**：
```python
# 标准 OOM 触发
OOM_KILL = r'Out of memory: Kill process (\d+) \((.+?)\) score (\d+)'

# cgroup OOM 触发
OOM_CGROUP = r'Memory cgroup out of memory: Kill process (\d+) \((.+?)\)'

# oom-killer 被调用（早期版本）
OOM_INVOKED = r'oom-killer: gfp_mask=(.+?), order=(\d+)'
```

### 1.2 进程内存快照（Mem-Info 段）

触发行之后紧跟系统内存快照，关键字段：

```
Node 0 DMA free:<X>kB min:<Y>kB low:<Z>kB ...
Node 0 Normal free:<X>kB ...
[ pid ]   uid  tgid total_vm      rss cpu oom_adj oom_score_adj name
[  1234]     0  1234   123456   102400   0      0          1000 java
...
Out of memory: Kill process 1234 (java) score 900 or sacrifice child
Killed process 1234 (java) total-vm:494624kB, anon-rss:409600kB, file-rss:4096kB
```

**关键正则**：
```python
# 进程列表行（[ pid ] uid tgid ... oom_score_adj name）
PROC_LINE = r'\[\s*(\d+)\]\s+\d+\s+\d+\s+\d+\s+(\d+)\s+\d+\s+[-\d]+\s+([-\d]+)\s+(\S+)'
# groups: pid, rss(pages), oom_score_adj, name

# 被杀进程行
KILLED = r'Killed process (\d+) \((.+?)\) total-vm:(\d+)kB, anon-rss:(\d+)kB, file-rss:(\d+)kB'
# groups: pid, name, total_vm_kb, anon_rss_kb, file_rss_kb

# 内存快照摘要行
MEM_FREE = r'Node \d+ \S+ free:(\d+)kB'
MEM_TOTAL = r'MemTotal:\s+(\d+) kB'
```

---

## 二、根因分类树

### 2.1 业务内存泄漏（最常见）

**特征**：
- 指标：内存使用率在 OOM 前呈**线性持续增长** > 20 分钟
- 日志：OOM 前无突发操作，被杀进程 RSS 异常高（超过正常水位的 2x 以上）
- kswapd 长期活跃（`kswapd` 指标持续 > 0）

**置信度规则**：满足以上 2 条 → 置信度 85%；满足 3 条 → 95%

**处置**：
- 立即：重启泄漏进程
- 短期：检查内存分配逻辑，定位泄漏点（heap dump / jmap）
- 长期：添加内存用量告警（阈值 80%），接入 pprof/jvm 监控

---

### 2.2 突发大内存申请

**特征**：
- 指标：内存使用出现**短时跳变**（5 分钟内上升 > 50%）
- 日志：OOM 前系统内存尚充足，OOM 瞬间 RSS 骤增
- 可能伴随大量 `page allocation failure` 日志

**置信度规则**：满足跳变特征 → 置信度 80%

**处置**：
- 立即：限制单次申请量或加 OOM 保护（ulimit / cgroup memory.limit）
- 短期：梳理大内存操作场景（批量读取、大缓存等）

---

### 2.3 cgroup 内存限制过低

**特征**：
- 日志：含 `Memory cgroup out of memory` 而非标准 `Out of memory`
- 系统可用内存（`mem_available`）仍充足（> 20%），但容器/进程组内 OOM
- OOM 发生时 cgroup memory.usage 命中 memory.limit_in_bytes

**置信度规则**：日志包含 `cgroup` 关键词 → 置信度 95%

**处置**：
- 立即：临时调大 cgroup 内存上限
- 短期：评估业务实际内存需求，合理设置 limit

---

### 2.4 Swap 未开启或已耗尽

**特征**：
- `swap_total == 0`（未开启）
- 或 `swap_free` 趋势持续下降至 0（已耗尽）
- `mem_available` 同时趋近 0

**置信度规则**：swap_total == 0 且 mem_available < 5% → 置信度 90%

**处置**：
- 立即：添加 swapfile（临时缓解）
- 长期：扩容内存规格或优化内存占用

---

### 2.5 多进程内存竞争

**特征**：
- 进程列表中有 **3 个以上进程** RSS > 1GB
- 可用内存长期维持低位（< 10%），无单一突出泄漏源

**处置**：
- 评估内存总需求是否超出物理容量
- 按优先级设置 `oom_score_adj`，保护核心进程

---

## 三、字段说明速查

| 字段 | 含义 | 单位/换算 |
|------|------|---------|
| `anon-rss` | 匿名内存（堆/栈），最能反映业务内存用量 | KB，直接读 |
| `file-rss` | 文件映射内存（mmap 文件），可被回收 | KB，直接读 |
| `total-vm` | 虚拟地址空间大小，通常远大于实际 RSS | KB，直接读 |
| `oom_score_adj` | OOM 优先级，越高越先被杀，范围 -1000~1000 | 无单位 |
| RSS in proc list | 进程列表中的 RSS 列，单位为**页** | 页数 × 页大小(KB) = KB |

> **页面大小说明**：x86-64 系统默认页大小为 4KB，ARM64 系统通常为 16KB（部分配置为 64KB）。
> `parse_oom_events.py` 会自动检测当前系统页大小；分析离线日志时可通过 `--page-size` 参数手动指定目标机器的页大小，避免 RSS 换算偏差。
> 注意：`anon-rss`、`file-rss`、`total-vm` 字段已是 KB，**不需要**乘以页大小。
