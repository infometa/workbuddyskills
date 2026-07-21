# 火焰图使用指南

> 这份指南面向想用火焰图排查性能问题的真实用户，不假设你熟悉 perf 工具链，手把手带你从安装到看懂结果。

---

## 一、什么时候该用火焰图？

火焰图解决的核心问题是：**"CPU 的时间都花在哪了？"**

下面这些情况，火焰图能快速给你答案：

| 你遇到的现象 | 火焰图能帮你做什么 |
|---|---|
| 服务 CPU 跑满，但不知道热点在哪 | 直接看哪个函数最宽，就是瓶颈 |
| 程序跑慢了，优化不知道从哪下手 | 找出占比最大的调用路径 |
| 进程频繁卡住（D 状态） | 找出阻塞在哪个内核调用（task-state 分析器）|
| 想验证优化效果 | 优化前后各生成一张，对比宽度变化 |

**不适合的场景：**
- 想看某次请求的耗时（用链路追踪）
- 想知道某个函数被调用了多少次（用 uprobe 计数）

---

## 二、安装配置

### 第一步：安装 perf-prof

优先从包管理器安装，省时省力：

```bash
# 检查是否已安装
which perf-prof && perf-prof --version
```

如果没有，用 yum 安装：

```bash
yum install -y perf-prof
```

yum 源里没有的话，从源码编译（需要几分钟）：

```bash
git clone https://gitee.com/OpenCloudOS/perf-prof.git
cd perf-prof
yum install -y xz-devel elfutils-libelf-devel libunwind-devel python3-devel
make
cp perf-prof /usr/local/bin/
```

### 第二步：安装 flamegraph.pl

参考 [FlameGraph 工具安装指南](flamegraph-install.md) 完成安装。

### 第三步：验证安装

```bash
perf-prof --version   # 应输出版本号，如 perf-prof 1.4
flamegraph.pl --help  # 应输出帮助信息
```

两条命令都有输出，就可以开始了。

---

## 三、生成你的第一张火焰图

### 最简单的场景：整机 CPU 热点

```bash
# 采样 30 秒，生成折叠栈文件
timeout 30 perf-prof profile -F 997 -g --flame-graph cpu.folded

# 转成 SVG
flamegraph.pl cpu.folded > cpu.svg
```

然后把 `cpu.svg` 下载到本地，用浏览器打开。

> **采样频率说明**：`-F 997` 表示每秒采样 997 次。用 997 而不是 1000，是为了避免和系统定时器同频产生采样偏差（伪共振）。生产环境可以调低到 `-F 99` 降低开销。

### 只看特定进程

```bash
# 先找到进程 PID
pgrep nginx  # 或 ps aux | grep 你的进程名

# 采样该进程
timeout 30 perf-prof profile -F 997 -p <PID> -g --flame-graph nginx.folded
flamegraph.pl nginx.folded > nginx.svg
```

### 只看内核态热点（过滤用户代码）

```bash
timeout 30 perf-prof profile -F 997 --exclude-user -g --flame-graph kernel.folded
flamegraph.pl kernel.folded > kernel.svg
```

---

## 四、如何看懂火焰图

拿到 SVG 用浏览器打开后，你会看到类似这样的画面：

```
┌─────────────────────────────────────────────────────────────┐
│                         main                                │  ← 栈底（程序入口）
│──────────────┬──────────────────────────────────────────────│
│   malloc     │              process_request                 │
│──────────────│──────────────┬──────────────────────────────│
│              │  parse_json  │       send_response           │
│              │──────────────│──────┬────────────────────────│
│              │              │write │   compress_data        │  ← 栈顶（实际执行的函数）
└─────────────────────────────────────────────────────────────┘
  越宽 = 采样越多 = CPU时间越长
```

**三个读图规律：**

1. **找"平顶山"** ——顶部宽、上面没有子调用的函数，就是真正消耗 CPU 的热点。`compress_data` 宽且是顶层，说明压缩逻辑是瓶颈。

2. **看宽度，不看高度** ——高度只代表调用栈的深浅，跟性能无关。宽度才代表 CPU 占用比例。

3. **点击可以放大** ——点击某个函数块，画面会以该函数为根重新渲染，方便查看细节。按 Reset Zoom 回到全图。

**常见内容解读：**

| 看到这个 | 说明 |
|---|---|
| `[unknown]` 帧很宽 | 缺少符号信息，需要安装 debuginfo 包 |
| `__do_softirq` 宽 | 软中断处理开销大 |
| `copy_to_user` / `copy_from_user` 宽 | 内核用户态数据拷贝多，考虑零拷贝方案 |
| `schedule` / `__schedule` 宽 | 进程频繁调度，CPU 上下文切换开销大 |
| `selinux_file_permission` 宽 | SELinux 安全检查开销高，可评估策略 |
| `mutex_lock` / `spin_lock` 宽 | 锁竞争严重 |

**快捷操作：**
- `Ctrl+F`：搜索函数名，匹配的函数会高亮，右上角显示总占比
- 点击函数块：放大查看
- 鼠标悬停：显示函数名和占比数字

---

## 五、进阶场景与案例

### 案例 1：Java 进程 CPU 高

Java 用户态栈默认无法回溯，需要加 `=dwarf` 参数：

```bash
timeout 30 perf-prof profile -F 97 -p <java_pid> \
    --user-callchain=dwarf -g --flame-graph java.folded
flamegraph.pl java.folded > java.svg
```

> 注意：dwarf 模式开销更大，采样频率调低到 97 左右，避免影响业务。

### 案例 2：找出阻塞在 D 状态的原因

进程卡住不动，`ps` 看到状态是 `D`（不可中断睡眠），通常是 IO 等待：

```bash
# 采样 D 状态超过 10ms 的调用栈（task-state 分析器）
perf-prof task-state -D --than 10ms -g --flame-graph d_state.folded
flamegraph.pl d_state.folded > d_state.svg
```

在火焰图里搜索 `io_schedule` 或 `submit_bio`，能找到是哪个 IO 操作导致的阻塞。

### 案例 3：验证优化效果

优化前后各生成一张，对比热点函数宽度：

```bash
# 优化前
timeout 30 perf-prof profile -F 997 -p <PID> -g --flame-graph before.folded
flamegraph.pl before.folded > before.svg

# 做优化...

# 优化后
timeout 30 perf-prof profile -F 997 -p <PID> -g --flame-graph after.folded
flamegraph.pl after.folded > after.svg
```

打开两张图对比，热点函数变窄说明优化有效。

### 案例 4：生产环境低开销采样

```bash
# 低频（99Hz）+ 长时间（5分钟）
timeout 300 perf-prof profile -F 99 -g --flame-graph prod.folded
flamegraph.pl prod.folded > prod.svg
```

---

## 六、常见误区与 Tips

### ❌ 误区 1：采样时间越短越好

**实际情况**：采样时间太短（<10秒），样本量不足，火焰图会有很大随机性，某些低频但重要的热点根本采不到。建议至少采样 30 秒，间歇性问题采 5 分钟以上。

### ❌ 误区 2：看到宽的就是性能问题

**实际情况**：有些函数本来就该占用 CPU，比如你的核心业务逻辑。关键是看**你不期望它宽的函数**有没有异常宽，比如锁等待、内核拷贝、SELinux 检查等。

### ❌ 误区 3：`[unknown]` 帧很多说明工具有问题

**实际情况**：`[unknown]` 表示符号解析失败，通常是因为：
- 程序没有 debug 符号（加 `-g` 编译，或安装 `*-debuginfo` 包）
- JIT 编译的代码（Java/Node.js 等需要额外配置）
- 内联优化导致栈帧消失

解决办法：安装对应的 debuginfo 包，或对 Java/Python 等运行时使用专用方法。

### ❌ 误区 4：火焰图里没有热点说明程序没问题

**实际情况**：如果采样期间 CPU 整体利用率很低（进程大部分时间在等 IO 或睡眠），火焰图就会很"矮"，看不出什么。这种情况应该用 `task-state` 分析器分析睡眠原因，而不是 CPU 采样火焰图。

### 💡 Tip 1：用 `--than` 过滤低占比噪音

```bash
# 只看占比超过 5% 的采样
perf-prof profile -F 997 -C 0 --than 5 -g --flame-graph cpu.folded
```

### 💡 Tip 2：直接让 AI 帮你分析折叠栈

拿到 `.folded` 文件后，可以直接把文件内容或 top 行贴给 AI：

```bash
# 提取最热的 20 条调用栈
sort -t' ' -k2 -rn cpu.folded | head -20
```

把输出贴出来，AI 就能帮你解读热点含义和优化方向。

### 💡 Tip 3：ringbuffer 溢出时加 `-m` 参数

采样高频事件时如果看到类似 `lost N events` 的警告，加大 ringbuffer：

```bash
perf-prof profile -F 997 -m 64 -g --flame-graph cpu.folded
```

### 💡 Tip 4：不同颜色方案适合不同场景

```bash
flamegraph.pl --colors hot cpu.folded > cpu.svg    # 默认，红橙色，适合 CPU 热点
```

---

## 七、相关资源

- [perf-prof 项目](https://github.com/OpenCloudOS/perf-prof.git)
- [FlameGraph 工具集](https://github.com/brendangregg/FlameGraph)
- [Brendan Gregg 的火焰图原理文章](https://www.brendangregg.com/flamegraphs.html)
- [示例 Prompt](examples.md) - 常用触发场景速查
