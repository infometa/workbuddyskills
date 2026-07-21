# Crash MCP 工具使用铁律

## 可用的 MCP 工具

| 工具名称 | 用途 |
|---------|------|
| `analyze_crash` | 一键创建会话并收集基线（sys, bt, log），**分析的入口点**。`cmd_log_path` 必须指定为 `<vmcore_dir>/crash_cmd_log_TIME.jsonl` |
| `create_crash_session` | 单独创建会话。同样需指定 `cmd_log_path` |
| `run_crash_command` | 执行单条 crash CLI 命令（优先使用） |
| `run_crash_commands` | 批量执行多条命令（输出多时慎用，相似命令一次执行时用此工具） |
| `collect_baseline` | 收集基线（sys, bt, log \| tail -n 100） |
| `export_command_log` | 导出命令日志到 JSONL（报告生成前确认日志完整性） |
| `close_crash_session` | 关闭并清理会话 |
| `search_knowledge_base` | 搜索本地知识库和 Red Hat KB |
| `list_sessions` | 列出所有活跃会话 |

## 铁律一：必须使用 MCP 工具，禁止脚本方式

**🔴 绝对禁止：**
- 🚫 使用 `execute_command` 直接运行 `crash` 命令
- 🚫 编写 crash 脚本文件然后通过 `execute_command` 执行
- 🚫 通过 shell 管道/重定向/echo 绕过 MCP
- 🚫 通过 Python 底层 API（import `CrashSessionManager`）绕过 MCP
- 🚫 在 MCP Server 未注册/未连接时开始分析
- 🚫 **通过 Bash 调用 CLI 的 `mcp` 子命令来调用 MCP 工具**（如 `codebuddy mcp call ...`、`claude mcp call ...`——这些 CLI 的 `mcp` 子命令仅用于管理 MCP Server 配置，**没有 `call` 命令**）

**✅ 唯一合法方式：** 通过 session 内已注册的 MCP 工具直接调用。工具调用链：`analyze_crash`/`create_crash_session` → `run_crash_command`/`run_crash_commands` → `close_crash_session`

## 铁律二：超时/失败时重试，不得降级

### 通用重试策略

1. 重试同一命令
2. 拆分复杂命令为更小的子命令（如 `bt -a` 拆为逐 CPU 的 `bt <pid>`）
3. 会话异常时重建会话
4. MCP Server 不可用时**回到阶段零步骤 0.0-0.6 修复环境**
5. 🔴 **绝对不能降级为脚本方式**

### 会话创建超时处理（`analyze_crash` / `create_crash_session`）

MCP Server 内部通过 `crash_timeout_seconds` 配置 crash 进程的命令超时（默认 300 秒，环境变量 `CRASH_TIMEOUT_SECONDS` 可调）。超时可能来自两个层面：

- **crash 内部超时**（错误信息含 `Timed out waiting for crash prompt`）：crash 进程在 `crash_timeout_seconds` 内未完成加载。通过环境变量 `CRASH_TIMEOUT_SECONDS` 递增调大后重试。
- **MCP 网关超时**（错误信息含 `timeout` 或连接中断，但不含上述 crash 内部信息）：IDE/mcporter 的 MCP 调用超时（默认通常 60 秒）比 `crash_timeout_seconds` 更短。此时 crash 进程**很可能仍在后台正常加载 vmcore**。

---

#### 🔴 MCP 网关超时专用策略（最常见场景，必须严格按以下顺序执行）

**核心原则：网关超时 ≠ crash 失败！crash 进程很可能在后台正常加载。不要盲目重试或杀进程，而是等待并检查。**

**第 1 步：立即检查后台 crash 进程是否仍在运行**

🔴 **必须使用当前分析的 vmcore 完整路径进行精确匹配**，避免多个 crash 会话并行分析不同 vmcore 时误判/误杀其他进程。

```bash
# 将 <VMCORE_PATH> 替换为当前分析的 vmcore 完整绝对路径
# 例如: /data/vmcore-2026-03-28/vmcore
ps aux | grep "crash.*<VMCORE_PATH>" | grep -v grep
```

> **为什么不用通配符 `crash.*(vmcore|vmlinux|dump)`？**
> 通配符会匹配所有 crash 进程，当有多个 vmcore 在同时分析时，会错误地认为"进程还在"或误杀其他分析的进程。使用完整 vmcore 路径可以精确定位到当前分析对应的那一个 crash 进程。

- 如果 crash 进程存在（状态为 D/Ds+ 表示在 IO 等待加载，R/S 表示已加载完成或在处理中）→ **进入第 2 步**
- 如果 crash 进程不存在 → **跳到"无后台进程的重试策略"**

**第 2 步：等待后台 crash 进程加载完成**

🔴 **绝对禁止在此阶段杀掉 crash 进程！** 杀进程会浪费已进行的加载，下次重试又要从头开始。

使用轮询等待进程状态变化（最长等待 5 分钟）：
```bash
# 将 <VMCORE_PATH> 替换为当前分析的 vmcore 完整绝对路径
echo "等待crash进程加载完成..."
for i in $(seq 1 30); do
    sleep 10
    PROC_LINE=$(ps aux | grep "crash.*<VMCORE_PATH>" | grep -v grep)
    if [[ -z "$PROC_LINE" ]]; then
        echo "crash进程已退出（可能加载失败）"
        break
    fi
    STATE=$(echo "$PROC_LINE" | awk '{print $8}')
    PID=$(echo "$PROC_LINE" | awk '{print $2}')
    if [[ "$STATE" != *"D"* ]]; then
        echo "crash进程 PID=$PID 状态: $STATE (已完成IO加载)"
        break
    fi
    echo "[$i/30] crash进程 PID=$PID 状态: $STATE (仍在加载...)"
done
```

**第 3 步：检查会话是否已自动创建成功**

crash 进程加载完成后，MCP Server 内部可能已经成功创建了会话（即使网关调用超时返回了错误）。用 `list_sessions` 检查：

**🔴 必须使用以下精确的调用方式：**
```
第 1 步：调用 mcp_get_tool_description，参数：
  toolRequests: [["aicrasher", "list_sessions"]]

第 2 步：调用 mcp_call_tool，参数：
  serverName: "aicrasher"
  toolName: "list_sessions"
  arguments: "{}"
```
- 如果返回的 sessions 列表**非空** → ✅ **会话已创建成功！** 直接使用该 session_id，跳过重试，继续执行 `collect_baseline` 等后续步骤
- 如果返回的 sessions 列表**为空** → 会话未创建，进入第 4 步

**第 4 步：清理残留进程后重试创建**

此时 crash 进程可能已退出或处于异常状态，需要清理后重试。由于 vmcore 数据已被操作系统缓存到内存（page cache），**重试时加载速度会显著加快**（通常从几分钟缩短到几十秒）：
```bash
# 将 <VMCORE_PATH> 替换为当前分析的 vmcore 完整绝对路径
# 🔴 使用精确路径匹配，避免误杀其他并行分析的 crash 进程
pkill -f "crash.*<VMCORE_PATH>" 2>/dev/null; sleep 2
ps aux | grep "crash.*<VMCORE_PATH>" | grep -v grep | wc -l  # 确认已清理
```
然后调用 `create_crash_session`（而非 `analyze_crash`，缩短单次调用耗时）重新创建会话。

**第 5 步：如果重试仍然网关超时**

重复第 1~3 步。因为 vmcore 已被缓存，这次加载通常只需要几十秒。如果第 3 步 `list_sessions` 仍为空，最多再重复一轮。

**第 6 步：三轮仍然失败 → 报告错误并停止**

告知用户 vmcore 加载超时，建议：
- 检查 vmcore 文件完整性（`file <vmcore_path>`）
- 检查机器磁盘 IO 和可用内存
- 尝试手动运行 `crash <vmlinux> <vmcore>` 验证是否能正常加载

---

#### 无后台进程的重试策略（crash 进程不存在时）

如果第 1 步检查发现没有后台 crash 进程：

1. **直接重试 `create_crash_session`**——可能是瞬时通信抖动
2. **如果之前用的是 `analyze_crash`**：改用 `create_crash_session` + `collect_baseline` 两步调用，缩短单次调用耗时
3. **仍然失败**：检查 MCP Server 状态和日志

---

#### crash 内部超时策略（错误含 `Timed out waiting for crash prompt`）

通过环境变量递增超时后重试：
```bash
export CRASH_TIMEOUT_SECONDS=600  # 从默认 300 递增到 600
```
然后回到阶段零步骤 0.3 重新注册 MCP Server（使环境变量生效），再重试。最多递增两次（300 → 600 → 1200）。仍然失败则报告错误并停止。

## 铁律三：分析过程中禁止中途关闭会话

- 🚫 禁止在分析未完成前调用 `close_crash_session`
- 🚫 禁止在 `run_crash_command` 中执行 `quit`/`q`/`exit`
- 🚫 禁止因"暂时不需要"就关闭会话

**正确的会话生命周期：** 阶段一创建 → 阶段一至六保持存活 → 阶段六报告完成后 → 阶段七关闭
