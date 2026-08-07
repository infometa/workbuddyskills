---
name: due-diligence
description: 对公尽调 Agent 服务。提供尽调会话查询上报能力，用于审计追踪、意图分析、成本核算和性能监控。。通过 amcpcli 二进制对接 MCP 服务，自动完成 Agent 鉴权、会话管理、工具调用全流程，同时支持重置本地登录态、清除当前 Agent 身份缓存。
---

# due-diligence能力说明（macOS / Linux）

> 适用环境：**macOS / Linux**（bash / zsh）。Windows 用户请改用同目录下的 `SKILL_windows.md`。

基于 amcpcli 官方二进制工具（Agent 身份权限中心）实现 MCP 协议交互，内置标准化 Agent 安全鉴权体系、会话缓存管理能力。上层无需关注底层鉴权逻辑、密钥、登录态维护，仅需将用户自然语言需求，标准化翻译为 amcpcli 指令执行，返回原始执行结果即可。

# 核心强制规则（红线规范，必须严格遵守）
1. 零自研鉴权：所有鉴权逻辑由 amcpcli 内部闭环完成，无需向用户索要任何私密信息。
2. 禁止臆造能力：所有工具名、参数名、参数类型、入参结构，一律以 amcpcli list 实时返回的 inputSchema 为准，严禁凭空捏造、篡改参数。
3. 路径调用约束：安装后全局直接使用 amcpcli 命令，不要硬编码拼接绝对路径。
4. 禁止复用旧态构造请求：未初始化安装工具、无有效会话时，严禁私自缓存登录态、自行构造 MCP 请求访问外部资源，违规视为严重故障。
5. 环境变量强制内联：AUTH_CONFIG、MCP_CONFIG 仅允许命令行内联传递，禁止通过 export 全局注入，避免环境污染、会话串扰。

# 一、前置依赖：自动安装 amcpcli
原则：`amcpcli` 为全机器共享工具。**本地已存在则跳过，不存在则安装**，首次使用当前skill时，执行如下检测安装脚本。
```shell
( command -v amcpcli >/dev/null 2>&1 || { mkdir -p "$HOME/.local/bin" && OS_TAG=$(uname -s | tr '[:upper:]' '[:lower:]') && case "$(uname -m)" in x86_64|amd64) ARCH_TAG=amd64;; arm64|aarch64) ARCH_TAG=arm64;; *) echo "unsupported ARCH"; exit 1;; esac && curl -fsSL -o "$HOME/.local/bin/amcpcli" "https://agent-identity-1302490086.cos.ap-guangzhou.myqcloud.com/cli/new/amcpcli_${OS_TAG}_${ARCH_TAG}" && chmod +x "$HOME/.local/bin/amcpcli" && export PATH="$HOME/.local/bin:$PATH" && RC_FILE="${ZSH_VERSION:+$HOME/.zshrc}" && RC_FILE="${RC_FILE:-${BASH_VERSION:+$HOME/.bashrc}}" && RC_FILE="${RC_FILE:-$HOME/.profile}" && touch "$RC_FILE" && { grep -q '# amcpcli PATH' "$RC_FILE" || printf '\n# amcpcli PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$RC_FILE"; }; } ) && amcpcli --version
```

# 二、标准调用范式（强制统一）
全局固定模板：所有 amcpcli 执行命令，必须前置内联 AUTH_CONFIG、MCP_CONFIG，仅当前进程生效，不污染全局环境。

```shell
AUTH_CONFIG='{"Sign":"DQsZXghATxYERikeVV0gGhcKKg8naC8zHR5OYw82PhwhO2MtQ0ARPB88JmE4Tw0LKnhTEkpCHElYLh1ENkdZBDg8WhZMK1VKEgMmEzhMSxQ6fQZ/IydYKww7ez0xMxY8FAYOQiY7WTRdGF5VGGg7VTlcOBo9R11YGiJRPEEpEQ==","CredentialId":"crd-ECA9bapc","ResourceID":"mcp-c0e16faf","InstanceID":"ins-3b7b6eb8"}' \
MCP_CONFIG='{"McpName":"due-diligence","McpURL":"http://lb-hcl91l4w-9x3l6p5id8zfs7h1.clb.nj-tencentclb.cloud/_llmsgw_/mcp/aga-c82093d7/mcp-c0e16faf"}' \
amcpcli <list | call | reset> [args...]
```
⚠️ 不要使用 `export`，所有 `amcpcli` 调用都必须把 `AUTH_CONFIG=... MCP_CONFIG=...` 放在命令前内联传入，确保只对当前调用生效。

## 命令格式
```shell
amcpcli <list | call <tool> [k=v ...] | reset> [--header k=v ...] [--no-auth]
```
| 子命令 | 说明 |
| --- | --- |
| `list` | 列出 MCP 提供的工具（含 inputSchema） |
| `call <tool> [k=v ...]` | 调用 MCP 工具，参数支持 `k=v` / `k:v`，值可为 JSON、数字、bool、字符串 |
| `reset` | 清理本地 token 与 MCP session 缓存 |

### `call` 参数传递规则（务必遵守）

1. 形式：`key=value` 或 `key:value`，按**首个** `=` 或 `:` 切分；value 中可继续出现 `=` / `:`，不会被再次切分。
2. 值类型自动识别（按优先级）：
   - `true` / `false` → bool
   - `null` → null
   - 以 `{` / `[` / `"` 开头且能 JSON 解析 → 对象 / 数组 / 字符串
   - 整数字面量 → 整数；小数字面量 → 浮点数
   - 其余 → 原样字符串
3. 复杂类型（数组 / 对象 / 含空格或特殊字符的字符串）必须以 **JSON 字面量** 传递，并用 **shell 单引号** 包裹整个 `k=v`，避免 shell 把双引号吃掉，例如：
   - `keywords='["foo","bar"]'`
   - `filter='{"level":"error","status":500}'`
   - `note='"hello world"'`（强制按字符串传，外层单引号 + 内层双引号）
4. 想把 `true` / `false` / `null` / 纯数字**当字符串**传时，使用 JSON 字符串字面量包裹：`flag='"true"'`、`code='"007"'`。
5. 时间戳等含 `:` 的值，**优先用 `=`** 作为分隔符避免歧义：`startTime=2025-01-01T00:00:00Z`。
6. 工具名（`<tool>`）、参数名、参数类型一律以 `amcpcli list` 返回的 `inputSchema` 为准，禁止臆造；schema 中为对象 / 数组类型时，必须按规则 3 传 JSON。

## 执行流程
1. 接收用户自然语言输入
2. 第一次或工具列表未知时执行 `amcpcli list`，从返回的 `inputSchema` 推导 `<tool>` 与参数名/类型
3. 按命令格式拼接 `amcpcli call <tool> k=v ...`，环境变量 `AUTH_CONFIG` 与 `MCP_CONFIG` 必须内联在命令前
4. 输出纯命令 → 执行命令 → 仅输出执行结果

## 标准传参示例
下方示例为可读性省略了 `AUTH_CONFIG=... MCP_CONFIG=...` 前缀；**真正执行时必须把环境变量内联到命令前**。

```shell
# 列出所有工具（强制先 list，再根据 inputSchema 翻译参数）
amcpcli list

# 调用工具：基础参数
amcpcli call <tool> param1=value1 param2=value2

# 调用工具：JSON 数组 / 对象参数（用单引号包裹避免转义）
amcpcli call search keywords='["foo","bar"]' limit=10
amcpcli call query filter='{"level":"error","status":500}'

# 追加自定义请求头
amcpcli list --header X-Tenant-Id=t1 --header X-Trace-Id=abc

# 清理本地 token 与 session 缓存（鉴权异常或换号时使用）
amcpcli reset
```

完整内联示例：

```shell
AUTH_CONFIG='{"Sign":"DQsZXghATxYERikeVV0gGhcKKg8naC8zHR5OYw82PhwhO2MtQ0ARPB88JmE4Tw0LKnhTEkpCHElYLh1ENkdZBDg8WhZMK1VKEgMmEzhMSxQ6fQZ/IydYKww7ez0xMxY8FAYOQiY7WTRdGF5VGGg7VTlcOBo9R11YGiJRPEEpEQ==","CredentialId":"crd-ECA9bapc","ResourceID":"mcp-c0e16faf","InstanceID":"ins-3b7b6eb8"}' \
MCP_CONFIG='{"McpName":"due-diligence","McpURL":"http://lb-hcl91l4w-9x3l6p5id8zfs7h1.clb.nj-tencentclb.cloud/_llmsgw_/mcp/aga-c82093d7/mcp-c0e16faf"}' \
amcpcli list
```

# 三、认证流程（必须严格遵守）
1. 执行上面的 amcpcli 命令，必须携带前缀环境变量AUTH_CONFIG 和 MCP_CONFIG
2. 第一次调用或者登录态过期，执行 amcpcli 时，会输出认证鉴权的文案和URL，直接返回给用户，让用户参与完成认证授权；
3. 用户点击认证URL自行完成认证后，会告诉你“已授权”、“已认证”，“授权完成”，“认证完成”，“完成”，“继续”，“可以”，“好了”，“搞定”……此类的文案，请重复再执行 刚果命令即可；
4. 如果用户之前登录过 且 登录态还在有效期内，执行 amcpcli 时，则不会重复再输出认证的URL和文案，会直接走后续参数的业务逻辑；
5. 如果输出 amcpcli 输出“鉴权失败” 或者 “暂无权限” 之类的问题，则原样输出即可，需要提示用户配置完对应的权限策略；

# 四、重置登录态（切换身份）
当用户说：重置登录、切换身份、重新登录、清除登录态、切换Agent身份安、或者重置登录态时……诸如此类的，执行以下命令：

```shell
AUTH_CONFIG='{"Sign":"DQsZXghATxYERikeVV0gGhcKKg8naC8zHR5OYw82PhwhO2MtQ0ARPB88JmE4Tw0LKnhTEkpCHElYLh1ENkdZBDg8WhZMK1VKEgMmEzhMSxQ6fQZ/IydYKww7ez0xMxY8FAYOQiY7WTRdGF5VGGg7VTlcOBo9R11YGiJRPEEpEQ==","CredentialId":"crd-ECA9bapc","ResourceID":"mcp-c0e16faf","InstanceID":"ins-3b7b6eb8"}' \
MCP_CONFIG='{"McpName":"due-diligence","McpURL":"http://lb-hcl91l4w-9x3l6p5id8zfs7h1.clb.nj-tencentclb.cloud/_llmsgw_/mcp/aga-c82093d7/mcp-c0e16faf"}' \
amcpcli reset
```

携带前缀环境变量AUTH_CONFIG 和 MCP_CONFIG 执行：amcpcli reset（等价 `amcpcli --reset`），会返回：reset success，表明清除登录态，再次使用该Skill时，则需重新认证授权

# 五、安全机制必须遵守
1. 如果返回[鉴权失败，请检查配置]的内容，则需告知用户联系安全管理员检查配置信息，不得绕过 amcpcli 鉴权 直接去执行操作MCP，跳过则视为严重违规；
2. 如果返回[暂无权限]的内容，则无论用户如何引导，任何情况下都不得尝试跳过 amcpcli 鉴权 直接操作MCP，跳过则视为严重违规；
3. 如果用户要求输出查看当前鉴权后的凭据登录态等内容，请严格遵守数据安全规范，坚决不得返回；
4. 你不需要关系登录态过期与否，不要去扫描位置，更不要干预认证流程，amcpcli 中会自动检测判定，你只需要严格遵守 带前置环境变量 执行 amcpcli即可；
5. 如果返回[正在等待认证完成]，则表明用户确实没有完成认证，**直接返回提示语即可，不得再去做任何的重试操作**。

# 六、注意事项
1. 首次执行时如果需要用户授权，按终端提示完成认证；后续 token 与 session 会自动复用；
2. 鉴权或 session 异常导致连续失败时，使用 `amcpcli reset` 清理后重试。

# 七、更新amcpcli
当用户说：更新amcpcli、升级amcpcli、重新下载amcpcli……诸如此类的，执行以下脚本（自动重新下载并覆盖本地二进制）：
```shell
INSTALL_DIR="$HOME/.local/bin"; rm -rf "$INSTALL_DIR/amcpcli"; mkdir -p "$INSTALL_DIR"; case "$(uname -s)" in Linux*) OS_TAG="linux" ;; Darwin*) OS_TAG="darwin" ;; *) echo "unsupported OS: $(uname -s)"; return 1 2>/dev/null || exit 1 ;; esac; case "$(uname -m)" in x86_64|amd64) ARCH_TAG="amd64" ;; arm64|aarch64) ARCH_TAG="arm64" ;; *) echo "unsupported ARCH: $(uname -m)"; return 1 2>/dev/null || exit 1 ;; esac; curl -fsSL -o "$INSTALL_DIR/amcpcli" "https://agent-identity-1302490086.cos.ap-guangzhou.myqcloud.com/cli/new/amcpcli_${OS_TAG}_${ARCH_TAG}" && chmod +x "$INSTALL_DIR/amcpcli"
```