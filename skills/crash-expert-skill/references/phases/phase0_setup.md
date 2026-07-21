# 阶段零：前置环境检查（详细步骤）

**步骤 0.0~0.5 是强制性的顺序流程，必须逐步执行，不得跳过任何步骤。只有全部步骤通过后才能进入阶段一。**

**🚫 绝对禁止的行为：**
- 🚫 **禁止在检测到 `NOT_INSTALLED` 或 `NOT_REGISTERED` 后跳过安装/注册步骤，直接用 Python 底层 API（如 `CrashSessionManager`）或自编脚本替代 MCP 工具**
- 🚫 **禁止因为 MCP 调用失败就放弃 MCP，转而使用 `execute_command` + Python 脚本绕过**
- 🚫 **禁止在步骤 0.0-0.5 未全部通过的情况下开始 vmcore 分析**

## 步骤 0.0：检测系统 `crash` 命令是否可用

```bash
which crash >/dev/null 2>&1 && echo "CRASH_INSTALLED" || echo "CRASH_NOT_INSTALLED"
```

**如果输出 `CRASH_NOT_INSTALLED`，自动安装：**

```bash
if command -v yum >/dev/null 2>&1; then
    yum install crash -y
elif command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install crash -y
else
    echo "ERROR: 无法识别包管理器，请手动安装 crash 工具"
    exit 1
fi
```

安装后必须重新验证 `crash` 命令可用，仍失败则停止。

## 步骤 0.1：检测 aicrasher MCP 包是否已安装

```bash
python3 -c "import aicrasher; print('OK')" 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"
```

## 步骤 0.2：如果未安装，自动执行安装

```bash
SKILL_DIR="<本 skill 文件所在目录的绝对路径>"
if [[ -f "$SKILL_DIR/.project_root" ]]; then
    PROJECT_ROOT=$(cat "$SKILL_DIR/.project_root")
else
    PROJECT_ROOT="$SKILL_DIR"
fi
cd "$PROJECT_ROOT" && pip3 install -e ".[cli]"
```

🔴 安装后必须重新执行步骤 0.1 验证安装成功。

## 步骤 0.3：检测 MCP Server 是否已注册

```bash
if command -v codebuddy >/dev/null 2>&1; then
    codebuddy mcp list 2>/dev/null | grep -q "aicrasher" && echo "REGISTERED" || echo "NOT_REGISTERED"
elif command -v claude >/dev/null 2>&1; then
    claude mcp list 2>/dev/null | grep -q "aicrasher" && echo "REGISTERED" || echo "NOT_REGISTERED"
elif command -v mcporter >/dev/null 2>&1; then
    mcporter list 2>/dev/null | grep -q "aicrasher" && echo "REGISTERED" || echo "NOT_REGISTERED"
else
    echo "NO_CLI_FOUND"
fi
```

## 步骤 0.4：如果未注册，自动注册 MCP Server

🔴🔴🔴 这一步是强制性的，不是可选的！

```bash
if command -v codebuddy >/dev/null 2>&1; then
    codebuddy mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server
elif command -v claude >/dev/null 2>&1; then
    claude mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server
elif command -v mcporter >/dev/null 2>&1; then
    mcporter config add aicrasher --stdio "python3 -m aicrasher.mcp_server" --scope home
fi
```

> **各工具注册命令速查：**
> - **CodeBuddy**: `codebuddy mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server`
> - **Claude Code**: `claude mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server`
> - **OpenClaw (mcporter)**: `mcporter config add aicrasher --stdio "python3 -m aicrasher.mcp_server" --scope home`

> **⚠️ OpenClaw 环境关键注意事项：`lifecycle` 必须设为 `keep-alive`**
>
> aicrasher 是有状态的 MCP Server——session 需要跨多次 tool call 存活。mcporter 默认 ephemeral 模式会导致 session 丢失。
> 如 CLI 注册失败，直接编辑 `~/.mcporter/mcporter.json` 添加：
> ```json
> { "mcpServers": { "aicrasher": { "command": "python3", "args": ["-m", "aicrasher.mcp_server"], "lifecycle": "keep-alive" } } }
> ```
> 配置修改后执行 `openclaw gateway restart` 使配置生效。

🔴 注册后必须重新执行步骤 0.3 验证注册成功。最多重试 3 次。

> **🔴🔴🔴 首次注册后必须重启会话！**
>
> MCP Server 的发现和连接发生在**会话启动时**，而非运行时动态加载。如果 aicrasher 是在**当前会话运行中**才首次注册的（即会话开始时 `mcp list` 中没有 `aicrasher`），则：
> - 配置文件虽已更新，但**当前会话不会热加载新注册的 MCP Server**
> - `mcp_get_tool_description` / `mcp_call_tool` 对 `aicrasher` 不可见
> - **必须提示用户退出当前会话并重新启动**（退出后重新运行 `codebuddy` / `claude` / `openclaw`），新会话启动时会自动发现并连接已注册的 MCP Server
>
> **处理流程：**
> 1. 完成步骤 0.4 注册后，执行步骤 0.5 验证注册已写入配置
> 2. **向用户输出明确提示：**
>    ```
>    ⚠️ aicrasher MCP Server 已成功注册，但当前会话无法热加载新注册的 MCP Server。
>    请退出当前会话，重新启动 CodeBuddy / Claude Code / OpenClaw，然后重新执行 vmcore 分析命令。
>    新会话启动后会自动连接 aicrasher MCP Server，无需再次注册。
>    ```
> 3. **停止后续步骤执行**——不要尝试继续步骤 0.6 的 MCP 调用验证（一定会失败）
>
> **如果会话启动时 aicrasher 已经在 `mcp list` 中**（说明是之前的会话已注册过），则无需重启，直接继续步骤 0.5、0.6。

## 步骤 0.5：验证安装完成

```bash
python3 -c "import aicrasher; print('✅ aicrasher 包: OK')"

if command -v codebuddy >/dev/null 2>&1; then
    codebuddy mcp list 2>/dev/null | grep "aicrasher"
elif command -v claude >/dev/null 2>&1; then
    claude mcp list 2>/dev/null | grep "aicrasher"
elif command -v mcporter >/dev/null 2>&1; then
    mcporter list 2>/dev/null | grep "aicrasher"
fi
```

**必须同时满足以下两个条件才能继续：**
1. ✅ aicrasher 包导入成功
2. ✅ MCP server 列表输出中包含 `aicrasher` 且状态正常

> 如果自动安装失败，请手动运行：`bash <skill_dir>/scripts/setup.sh`

## 步骤 0.6：验证 MCP Server 进程能正常工作

🔴 **注册成功 ≠ 进程能正常启动！必须通过实际 MCP 调用验证。**

使用 `list_sessions` 工具进行健康检查（无需参数、不创建资源、最轻量）。

**🔴🔴🔴 必须使用以下精确的调用方式：**

**第 1 步：获取工具描述**
```
调用 mcp_get_tool_description，参数：
  toolRequests: [["aicrasher", "list_sessions"]]
```

**第 2 步：执行工具调用**
```
调用 mcp_call_tool，参数：
  serverName: "aicrasher"
  toolName: "list_sessions"
  arguments: "{}"
```

**预期结果：** 返回 `{"sessions": []}`（空列表，因为还没有创建会话）

**如果调用失败（超时/报错/MCP Server 不可达）：**

**首先判断是否属于"首次注册"场景：**
- 如果 aicrasher 是在当前会话运行过程中才注册的（步骤 0.4 刚执行了注册命令），MCP 调用**一定会失败**，这是正常的——因为当前会话无法热加载新注册的 MCP Server
- 此时**不要重试**，直接提示用户重启会话（参见步骤 0.4 后的说明）

**如果不是首次注册（会话启动时 aicrasher 已在 `mcp list` 中），则按以下步骤排查：**

1. 检查 MCP Server 进程是否已启动：
   ```bash
   ps aux | grep "aicrasher.mcp_server" | grep -v grep
   ```
2. 尝试手动启动验证是否有错误输出：
   ```bash
   python3 -m aicrasher.mcp_server 2>&1 &
   PID=$!
   sleep 2
   kill $PID 2>/dev/null
   ```
3. 如仍失败，回退到步骤 0.2 重新安装，然后重新执行步骤 0.3-0.6
4. 最多重试 3 次
5. 🔴 **无论如何都不能放弃 MCP 转用 Python API 或脚本方式**

**⚠️ 只有 `mcp_call_tool` 调用 `list_sessions` 成功返回后，才能进入阶段一。**
