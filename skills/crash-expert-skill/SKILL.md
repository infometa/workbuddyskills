---
name: crash-expert-skill
description: "Linux kernel vmcore/coredump analysis expert skill. Use when users need to analyze Linux kernel crash dumps (vmcore), investigate kernel panic causes, or debug kernel deadlocks, hung tasks, soft/hard lockups, BUG_ON, null pointer dereferences, OOM, or other kernel crash scenarios. Integrates with AiCrasher MCP tool for automated crash debugging across 7 analysis phases."
description_zh: "Linux 内核 vmcore 分析专家，诊断 panic/死锁/OOM 根因"
description_en: "Linux kernel vmcore expert for panic, deadlock, and OOM diagnosis"
version: 1.0.0
allowed-tools: Read,Bash,Grep
---

# Crash Expert — Linux 内核 vmcore 分析专家

本技能提供 Linux 内核 vmcore 深度分析的完整工作流，结合 AiCrasher MCP 工具实现自动化 crash 调试。

## 完整流程总览（共 7 个阶段）

| 阶段 | 名称 | 核心动作 | 产出/检查点 | 是否必须 |
|------|------|---------|------------|---------|
| **阶段零** | 前置环境检查 | 检查 crash 命令、安装 aicrasher、注册 MCP Server、验证 MCP 可调用 | MCP 可用 | ✅ 必须 |
| **阶段一** | 初始化与基线收集 | `analyze_crash` 创建 session → 收集 sys/bt/log | session_id 已获取 | ✅ 必须 |
| **阶段二** | 识别 Panic 类型 | 根据基线判断 crash 类型 | 明确 panic 类型 | ✅ 必须 |
| **阶段三** | 深入分析 | 根据类型执行对应分析命令 | 证据链完整，根因定位，**并明确根因分类** | ✅ 必须 |
| **阶段四** | 查找社区 fix commit 及 bug issue | 搜索上游 git 仓库或 web 搜索修复补丁，搜索社区 bug/issue 报告，**若用户提供了发行版 git 仓库则检查新版本是否已修复并定位修复 tag** | fix commit 列表 + 相关 bug issue + 发行版修复状态 | ⚡ **条件执行** |
| **阶段五** | 缓解措施分析 | 评估业务优化和内核参数调整 | 可行性建议 | ✅ 必须 |
| **阶段六** | 输出分析报告 | 获取 TIME → Markdown → 脚本生成 HTML 报告 | `.md` + `.html` 报告 | ✅ 必须 |
| **阶段七** | 关闭 session | `close_crash_session` 释放资源 | session 已关闭 | ✅ 必须 |

**⚠️ 常见遗漏提醒：**
- 🚫 **禁止在阶段三完成后就停止**——必须继续执行阶段五至阶段七
- 🚫 **禁止跳过阶段六的报告生成**——分析结论必须写入文件
- 🚫 **禁止忘记阶段七关闭 session**

**🔴🔴🔴 阶段切换铁律（防止长对话中遗忘 skill 要求）：**
- **每个阶段开始前，必须重新读取该阶段对应的详细步骤文件**（如进入阶段四前必须读取 `references/phases/phase4_community_fix.md`，进入阶段六前必须读取 `references/phases/phase6_report.md`）
- **不得凭记忆执行**——长对话中早期加载的指令会被逐渐稀释，必须在关键节点主动回读
- 每个阶段完成后，对照该阶段的产出/检查点确认是否满足要求后再进入下一阶段

---

## 阶段零：前置环境检查

**在执行任何 vmcore 分析之前，必须先确认 AiCrasher MCP Server 已安装并注册。**

👉 **必须完整读取详细步骤文件：[`references/phases/phase0_setup.md`](references/phases/phase0_setup.md)，按步骤 0.0~0.6 逐一执行。**

> **🔴 首次注册须知：** MCP Server 的发现和连接发生在**会话启动时**。如果 aicrasher 是在当前会话中首次注册的，当前会话无法热加载，**必须提示用户退出并重新启动会话**（`codebuddy` / `claude` / `openclaw`），新会话会自动连接已注册的 MCP Server。详见 `phase0_setup.md` 步骤 0.4 后的说明。

---

## MCP 工具使用铁律

👉 **进入阶段一前，必须完整读取：[`references/phases/mcp_tools_rules.md`](references/phases/mcp_tools_rules.md)**

**核心铁律摘要（详情见上述文件）：**
1. **必须使用 MCP 工具**，禁止 `execute_command` 直接调用 crash、禁止 Python 底层 API 绕过。只能用 session 内已注册的 MCP 工具直接调用；禁止通过 Bash 调用 CLI 的 `mcp` 子命令
2. **超时/失败时重试**，不得降级为脚本方式
3. **分析过程中禁止中途关闭会话**，只有阶段六完成后才能在阶段七关闭

---

## 核心分析原则（必须严格遵守）

### 1. 先全局后局部，避免锚定偏差（最重要！）
- **Panic CPU 的调用栈只是"快照"，不等于"根因"**
- Soft Lockup / Hard Lockup / RCU Stall 场景中，**必须先用 `bt -a | grep -c '<关键函数>'` 统计全局状态**
- 切忌把"panic CPU 正在做的事"直接等同于"导致 lockup 的原因"

### 2. 证据驱动，杜绝臆断
- 推测触发原因时必须结合代码逻辑验证
- 推测已合入修复 patch 时，必须查看过代码或 changelog 后才能下结论
- 每个结论需有 vmcore 中的具体数据支撑
- 🔴 **建议"回合补丁"或"升级内核"前，必须先验证当前内核是否已包含该功能**：先查源码确认功能/参数是否存在，再通过反汇编或结构体偏移确认编译后的二进制是否包含该逻辑。禁止未经验证就建议回合

### 3. 局部变量查找策略
- 优先从堆栈（stack frame）中查找，不要简单从寄存器取值
- 找出的变量地址需严谨校验（交叉验证地址范围、类型大小、相邻变量合理性）

### 4. 禁止过早下结论
- 确保构建完整自洽的分析结论后，再进行修复探索
- 看到 panic CPU 调用栈后不要立刻锚定方向，先完成全局扫描

### 5. 主动思考，不限于已知场景
- 下文列出的场景仅供参考，要主动思考其他可能性

### 6. 🔴 内核参数/sysctl 查找策略：源码优先，禁止仅依赖 sym 搜索
- **`sym` 命令只能搜索全局符号（全局变量、函数名）**，无法找到结构体字段。大量内核 sysctl 参数（如 IPVS 的 `net.ipv4.vs.*`、netfilter 的参数等）是存储在 per-netns 结构体字段中的，不是独立的全局变量
- **正确的查找流程（必须按序执行）：**
  1. **先查源码**：用 `grep -rn "<参数名>" <内核源码目录>` 在源码中搜索参数定义，确认是否存在、在哪个结构体中、是哪个 sysctl procname
  2. **查结构体定义**：找到参数所在的结构体（如 `netns_ipvs`、`netns_sysctl`），确认字段名和偏移量
  3. **反汇编验证**：对相关函数执行 `dis <function>`，确认编译后的二进制中是否包含该参数的条件判断逻辑，从反汇编中获取结构体字段的实际偏移量
  4. **通过偏移量读取运行时值**：获取结构体实例指针，加上偏移量，用 `rd` 或 `p/d *(int *)<addr>` 读取实际值
- **典型易错场景：**
  - IPVS sysctl（`net.ipv4.vs.*`）→ 存储在 `struct netns_ipvs` 字段中，通过 inline 函数访问
  - 网络命名空间 sysctl（`net.ipv4.conf.*`、`net.core.*`）→ 存储在 per-netns 结构体中
  - 内核模块的 sysctl → 模块的调试符号可能未加载，`sym` 搜索不到
- **禁止行为**：仅用 `sym -q <参数名>` 搜索不到就断言"参数不存在"。必须结合源码和反汇编交叉验证

### 7. 🔴 单位换算必须交叉验证，禁止臆断单位
- **`crash ps` 输出的 VSZ 和 RSS 单位是 KB（千字节），不是 pages**
- 换算公式：`RSS(GB) = RSS(KB) / 1024 / 1024`
- **绝对禁止**将 KB 值当成 pages 后乘以 4KB（4096）——这个错误会导致内存数据虚高 4 倍
- **交叉验证方法**：用 `mm->total_vm`（单位：pages）× 4096 / 1024 = VSZ（KB），两者必须一致
- **多线程 RSS 重复计数**：使用 `ps -G`（线程组 leader）避免同一进程的多个线程被重复统计
- **合理性检查**：Top N 进程 RSS 合计不得超过物理内存总量（`kmem -i`），如果超出说明单位搞错或存在重复计数

---

## 阶段一：初始化与基线收集

1. **获取 TIME 变量**（全程复用，阶段六禁止重新获取）：
   ```bash
   TIME=$(date '+%Y%m%d_%H%M') && echo "TIME=$TIME"
   ```
2. **创建会话并收集基线**：使用 `analyze_crash`，`cmd_log_path` 设为 `<vmcore_dir>/crash_cmd_log_${TIME}.jsonl`
3. **解读基线信息**：`sys`（内核版本、运行时长、panic 原因）、`bt`（panic CPU 调用栈）、`log | tail -n 100`（最后的内核日志）
4. **定位内核源码路径**（后续阶段三反汇编对照、grep 源码等操作直接复用此路径）：
   - 默认使用 vmcore 文件所在目录里匹配版本的内核代码
   - 若存在匹配的 kernel-debuginfo-common 包，解压作为源码包
   - 若用户提供 git 仓库路径（默认当前目录），检查 tag 是否匹配内核版本
   - 若无对应内核代码，尝试查找反汇编中列出的代码目录
5. **记录用户提供的内核代码 git 仓库路径**（阶段四复用）：
   - 如果用户在分析请求中提供了 vmcore 内核版本对应的内核代码 git 仓库路径，记录为 `DISTRO_GIT_REPO` 变量，阶段四将用它检查新版本是否已修复
   - 如果用户未提供 git 仓库，则 `DISTRO_GIT_REPO` 为空，阶段四跳过仓库修复检查

---

## 阶段二：识别 Panic 类型

| 类型 | 典型特征 |
|------|---------|
| **Hung Task** | `khungtaskd`、"blocked for more than" |
| **Soft Lockup** | "BUG: soft lockup"、`watchdog` |
| **Hard Lockup** | "NMI watchdog: Watchdog detected hard LOCKUP" |
| **BUG_ON** | "kernel BUG at" |
| **NULL 指针** | "unable to handle kernel NULL pointer dereference" |
| **异常地址** | "unable to handle kernel paging request"、"general protection fault" |
| **OOM 内存耗尽** | "Out of memory and no killable processes"、"System is deadlocked on memory" |
| **SysRq 触发** | "SysRq : Trigger a crashdump" |
| **virsh dump** | 无明显 panic 信息 |

---

## 阶段三：深入分析

👉 **根据阶段二识别的 Panic 类型，只读取对应的场景分析文件（不要全部读取）：**

| Panic 类型 | 读取文件 |
|------------|---------|
| **Hung Task** | [`references/reference/scenario_hung_task.md`](references/reference/scenario_hung_task.md) |
| **Soft Lockup / Hard Lockup** | [`references/reference/scenario_lockup.md`](references/reference/scenario_lockup.md) |
| **BUG_ON / NULL 指针 / 异常地址** | [`references/reference/scenario_bug_null_ptr.md`](references/reference/scenario_bug_null_ptr.md) |
| **OOM 内存耗尽** | [`references/reference/scenario_oom_deadlock.md`](references/reference/scenario_oom_deadlock.md) |
| **SysRq 触发 / virsh dump** | [`references/reference/scenario_sysrq_virsh.md`](references/reference/scenario_sysrq_virsh.md)（可能需要追加读取 lockup 或 hung task 场景文件） |

👉 **分析过程中需要参考命令用法时，读取：[`references/reference/crash_commands.md`](references/reference/crash_commands.md)**

### 🔴 阶段三输出要求：根因分类判定

**阶段三分析完成后，必须明确给出根因分类判定，决定后续流程走向：**

| 根因分类 | 判定标准 | 后续流程 |
|----------|---------|---------|
| **内核缺陷** | 根因涉及内核代码 bug（如空指针解引用、竞态条件、逻辑错误、内核/内核模块内存泄漏等） | → 阶段四（查找社区 fix commit 及 bug issue）→ 阶段五 → 阶段六 → 阶段七 |
| **非内核缺陷** | 根因为业务配置问题、用户态程序行为、运维操作失误等（如 oom_score_adj 误配、用户进程内存泄漏、cgroup 配置不当、业务触发 SysRq 等） | → **跳过阶段四**，直接进入 阶段五 → 阶段六 → 阶段七 |

**判定原则：**
- 如果根因明确不涉及内核代码缺陷，**不要浪费时间去搜索社区内核修复 commit**
- 如果判定存疑（无法确定是否为内核 bug），仍然执行阶段四以排除内核侧问题

---

## 阶段四：查找社区 fix commit 及 bug issue（条件执行）

**⚡ 前置条件：仅当阶段三根因分类判定为"内核缺陷"或"存疑"时才执行此阶段。**

**如果阶段三已明确根因为非内核缺陷（如业务配置问题、用户态程序行为等），直接跳过此阶段，进入阶段五。若原因可能为内核缺陷不可跳过。**

👉 **必须完整读取详细步骤：[`references/phases/phase4_community_fix.md`](references/phases/phase4_community_fix.md)**

**核心要求摘要：**
- **4.1 查找上游社区 fix commit**：搜索上游 git 仓库或在线搜索修复补丁
- **4.2 搜索社区 bug/issue 报告**：搜索 kernel.org Bugzilla、LKML、Red Hat Bugzilla 等
- **4.3 🔴 检查发行版仓库是否已修复**（当 `DISTRO_GIT_REPO` 非空时必须执行）：在用户提供的发行版 git 仓库中搜索修复 commit，通过 `git tag --contains` 确定哪个 tag 版本首次包含修复，并通过代码对比验证修复确实生效。这一步直接决定用户是"升级到发行版新版本"还是"自行反向移植"

---

## 阶段五：缓解措施分析

👉 **必须完整读取详细步骤：[`references/phases/phase5_mitigation.md`](references/phases/phase5_mitigation.md)**

**核心要求：**
- 🔴 **第一步：触发条件分析**——基于阶段三根因，梳理 bug 的完整触发条件链（应用行为、内核机制、并发条件、系统状态、配置条件），**具体到应用/业务层面**说清楚什么操作导致这条代码路径被执行
- 🔴 **第二步：业务侧规避建议**——评估是否可以从业务侧（停用触发组件、调整使用模式、降低触发频率、隔离影响）规避问题
- 🔴 **第三步：内核参数调整建议**——每条参数建议必须先通过"因果有效性验证"，不满足的不得出现在报告中
- 如果根因为业务配置问题且无内核参数可调整来解决，则不给出内核参数建议（宁缺毋滥）
- 建议调整参数前必须先从 vmcore 读取当前值，以"当前值→建议值"对比呈现

---

## 阶段六：输出分析报告

分析报告需要**用中文**输出，保存为**html格式**，文件名按照**crash_report_TIME.html**格式命名，TIME为本地当前时间,精确到分钟，分析报告保存在vmcore文件所在目录。

### 🚨 🚨 🚨  报告生成方式（最高优先级强制要求 — 使用脚本生成，禁止直接输出 HTML）

**必须使用 [`crash_report_generator.py`](scripts/crash_report_generator.py) 脚本生成报告（Markdown + 命令引用方案）。**

👉 **必须完整读取详细步骤：[`references/phases/phase6_report.md`](references/phases/phase6_report.md)**

**核心要求摘要：**
- **复用阶段一已获取的 TIME 变量**（禁止重新获取），全程复用于文件名
- **必须使用 `crash_report_generator.py` 脚本生成**，禁止直接手写 HTML
- 流程：确认 TIME → 撰写 Markdown → 写入 `crash_report_TIME.md` → 调用脚本生成 `crash_report_TIME.html`（`-l` 参数指向 `crash_cmd_log_TIME.jsonl`）
- 使用 `@cmd[]` 引用 crash 命令输出，避免在 Markdown 中重复粘贴

---

## 阶段七：关闭 session（必须执行）

🔴 阶段六完毕后，调用 `close_crash_session` 关闭会话，释放 crash 进程资源。

- 只有执行完此步骤才算完成一次完整的 vmcore 分析
- 用户明确要求保留 session 时可跳过

---

## 重要提醒

1. **永远不要在没有充分证据的情况下给出结论**
2. **永远不要给出跟分析结论不相关的缓解参数**，而是给出下一步排查建议
3. **建议调整参数前必须先确认当前值**（参见阶段五）
4. **🔴 每条内核参数建议都必须通过因果有效性验证**（参见阶段五"强制前置步骤一"）：必须论证"改这个参数"→"为什么能解决当前问题"的完整因果链，以及在当前系统配置下不会引入新问题。**如果分析结论为"非内核缺陷（业务配置问题）"，且从原理上没有任何内核参数调整能解决此问题，则报告中不需要给出任何内核参数调整建议——宁缺毋滥，不给无效建议**
5. **描述问题触发方式时区分"系统默认触发"和"进程主动请求触发"**
6. **分析完成后必须执行阶段七关闭会话**
7. **遇到不确定的情况，执行更多 crash 命令获取信息，而非猜测**
8. **所有工具调用通过 MCP 协议执行**：先 `mcp_get_tool_description`（传入 `toolRequests: [["aicrasher", "<工具名>"]]`）获取参数，再 `mcp_call_tool`（传入 `serverName: "aicrasher"`, `toolName: "<工具名>"`, `arguments: "{...}"`）执行
9. **MCP 工具/会话/报告生成的铁律**：严格遵守，禁止降级为脚本方式


## 工具说明

本技能使用以下工具：

- **Read**: 读取项目文件和配置
