---
name: oom-killer
description: 排查 Linux 主机 OOM（Out of Memory）Killer 事件，通过分析系统日志定位内存不足根因。支持分析本机日志或指定日志文件，提取被杀进程、内存快照、cgroup 信息等关键字段，输出结构化诊断报告。
description_zh: OOM Killer 事件诊断（内核日志解析 + 根因分类 + 处置建议）
description_en: Diagnose Linux OOM Killer events via kernel log parsing, root cause classification, and structured remediation report
version: 0.1.0
---

# Linux OOM 事件诊断

排查 Linux 主机 OOM（Out of Memory）Killer 事件，通过分析系统日志定位内存不足根因，输出结构化诊断报告。

## 适用场景

### 用户可能的问题表述

**OOM 事件**：
- "服务器出现 OOM 了"、"oom killer 触发了"
- "进程被 kill 了"、"内存不足进程被杀"
- "帮我看下 OOM"、"内存溢出怎么排查"

**日志分析**：
- "帮我分析下 /var/log/messages"、"messages 日志里有 OOM"
- "这个日志文件里有没有 OOM"

**内存相关**：
- "内存打满了"、"内存不够用"
- "cgroup 内存限制触发了"

---

## 目录结构

```
oom-killer/
├── SKILL.md                          # 本文件
├── references/
│   ├── kernel-oom-patterns.md        # 内核 OOM 日志特征库 & 根因分类
│   └── metrics-guide.md              # 内存相关监控指标清单（外部参考）
├── scripts/
│   ├── collect_and_analyze.sh        # 入口脚本
│   └── parse_oom_events.py           # OOM 事件解析脚本（日志 → 结构化事件）
└── tests/
    └── test.sh                       # 测试脚本
```

---

## 前置条件

**可选输入**：

- `-f <path>`：日志文件路径（不指定时自动分析本机日志）
- `-o <dir>`：输出目录（不指定时使用当前目录）
- `-t <id>`：任务 ID（不指定时默认 unknown）

**依赖工具**：

- `python3`：解析 OOM 日志

---

## Workflow

### Step 0：确定日志来源

- **用户提供了 `log_file`**：直接使用该路径
- **未提供**：自动检测本机日志，依次查找 `/var/log/messages` → `/var/log/syslog` → `/var/log/kern.log`

无需向用户询问，直接执行。

### Step 1：解析 OOM 事件

调用 `scripts/parse_oom_events.py` 解析日志，提取结构化 OOM 事件：

```bash
python3 skills/oom-killer/scripts/parse_oom_events.py \
  --log-file /path/to/messages \
  --output /tmp/oom_events.json --pretty
```

解析重点参考 `references/kernel-oom-patterns.md` 中的正则模式和字段说明。

**解析结果为空时的处理**：

1. 先检查文件是否真的存在且不为空
2. 扩大文件范围（如 `messages-1`、`messages.1`、`syslog.1` 等归档文件）
3. 直接用关键词搜索确认是否有 OOM 迹象：`oom`、`Killed process`、`Out of memory`

### Step 2：根因判定

结合解析出的 OOM 事件字段，按根因分类树判定（详见 `references/kernel-oom-patterns.md` 第二节）：

```
├── 业务内存泄漏      被杀进程 anon-rss 异常高，无突发操作
├── 突发大内存申请    OOM 前内存尚充足，RSS 骤增
├── cgroup 限制过低   日志含 "Memory cgroup out of memory"
├── Swap 未开启/耗尽  无 Swap 相关行或 Swap 相关日志显示耗尽
└── 多进程内存竞争    top_rss_procs 中 3 个以上进程 RSS > 1GB
```

置信度评估规则参见 `references/kernel-oom-patterns.md` 第二节各类型的"置信度规则"。

### Step 3：输出诊断报告

严格使用下方报告模板输出，不要随意省略章节。**处置建议必须结合本次事件的具体数据填写**（如实际进程名、RSS 数值、cgroup 路径），不要照抄通用模板文案。

---

## 诊断报告模板

```
## OOM 诊断报告

### 基本信息
- 日志文件: <log_file 路径>
- 故障时间: <OOM 触发时间戳>
- 数据完整度: <完整 / 部分缺失（说明原因）>

### 事件摘要
- OOM 触发次数: N 次
- 被 Kill 进程: <进程名> (PID <pid>), anon-rss: <rss>KB
- 触发时 free 内存: <free>KB
- OOM 分数 (oom_score_adj): <score>
- 触发类型: 标准 OOM / cgroup OOM

### 进程内存快照（Top RSS 进程）
| 进程名 | PID | RSS (KB) | oom_score_adj |
|--------|-----|----------|---------------|
| ...    | ... | ...      | ...           |

### 根因判定
<根因类型>（置信度 <XX>%）
- 主要依据: <1-2 条核心证据，结合实际数值>
- 辅助印证: <日志中的其他佐证>

### 处置建议
1. **立即**: <结合实际进程名/数值的临时止血措施>
2. **短期**: <配置/代码层修复>
3. **长期**: <监控/告警/容量规划>

### 补充信息（可选）
如有外部监控数据（内存使用率趋势、Swap 状态等），可在此补充以辅助判断。
```

---

## 常见问题排查

### 日志为空或无 OOM 关键词

```bash
# 检查归档日志（可自动执行）
ls /var/log/messages* /var/log/syslog* /var/log/kern.log* 2>/dev/null

# 快速搜索 OOM 迹象
grep -iE "oom.killer|out of memory|Killed process|Memory cgroup" /var/log/messages
```

### 找到 "Killed process" 但无完整 OOM 块

可能是 cgroup OOM，或被人为 kill：

```bash
# 搜索 cgroup OOM
grep "Memory cgroup out of memory" /var/log/messages

# 搜索人为 kill（signal 9）
grep "signal 9" /var/log/messages
```

### 同一时间窗口出现多次 OOM

- 间隔 < 5 分钟的多次 OOM → 视为同一根因，取第一次为基准
- 间隔 > 30 分钟的多次 OOM → 分别判定根因，报告中分段陈述

