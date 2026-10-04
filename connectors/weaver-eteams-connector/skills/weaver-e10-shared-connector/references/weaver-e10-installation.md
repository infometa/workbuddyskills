# 安装与可用性检查（连接器模式）

## 什么时候读取

命令不可用、版本不确定、怀疑安装不完整，或需要向用户解释「为什么不用自己装 CLI」时读取本文件。

## 检查命令

```text
weaver-work-cli --version
weaver-work-cli doctor --e10
weaver-work-cli --profile eteams --json auth status --no-check
```

`--version` 返回 CLI 版本，`doctor --e10` 检查 Node 环境与 E10 登录文件；两者都通过、且 `auth status` 显示 `loggedIn=true`，才说明连接器环境完整可用。

## 命令找不到（退出码 127）：先区分「未安装」与「已安装但不在 PATH」

`weaver-work-cli --version` 报 `command not found` 或退出码 127 时，**不要直接判定为未安装**。连接器把 CLI 装在托管前缀下（macOS/Linux：`~/.workbuddy/binaries/node/cli-connector-packages/`，可执行文件在其 `bin/`），若该 `bin` 目录不在当前 shell 的 PATH 中，就会表现为「找不到命令」。按顺序处理：

1. 先确认托管目录里有没有 `weaver-work-cli`：

macOS/Linux（bash/zsh）：

```bash
ls "$HOME/.workbuddy/binaries/node/cli-connector-packages/bin" | grep -i weaver
```

Windows PowerShell：

```powershell
Get-ChildItem "$env:USERPROFILE\.workbuddy\binaries\node\cli-connector-packages\bin" -Filter "weaver-work-cli*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
```

2. 若找得到，把该 `bin` 目录前置到 PATH 后重验，**不要安装**：

macOS/Linux（bash/zsh）：

```bash
export PATH="$HOME/.workbuddy/binaries/node/cli-connector-packages/bin:$PATH"
weaver-work-cli --version
```

Windows PowerShell：

```powershell
$env:Path = "$env:USERPROFILE\.workbuddy\binaries\node\cli-connector-packages\bin;$env:Path"
weaver-work-cli --version
```

3. 前置后仍不可用，或托管目录里根本没有 `weaver-work-cli`，才判定为「未安装」：**不要执行 `npm install`**，让用户断开连接器后重新点「连接」，由连接器重跑安装（见下一节）。沙箱/容器里若 PATH 前置仍失败，按 [`non-interactive-environment.md`](non-interactive-environment.md) 收尾：记录退出码与耗时并反馈。

## 谁负责安装

| 事项 | 由谁完成 |
| --- | --- |
| 安装 / 升级 `weaver-work-cli` | 连接器（`cli.json` 的 `init`，Node 运行时也由连接器托管） |
| 把技能放进 Agent 环境 | 连接器（随包加载，无需安装动作） |
| 登录 E10 与登录态持久化 | 连接器（`auth` 命令 + 轮询 `status`） |

CLI 的全局安装目录被 WorkBuddy 重定向到其托管目录（macOS/Linux：`~/.workbuddy/binaries/node/cli-connector-packages/`），不会污染用户系统的全局 npm 环境，也不会依赖用户的 `~/.npmrc`。

## Agent 应当做什么

1. **先确认命令可用**，再执行业务动作。

2. **命令不可用时不要自行安装**：不要执行 `npm install -g weaver-work-cli`、`npm install`、`npm run build`、`npm link`，也不要执行 `weaver-work-cli skills install`。直接告知用户：

> 当前连接器的 CLI 未就绪，请回到连接器面板断开连接后重新点「连接」，连接器会自动完成安装。

3. **不要把技能复制到其他目录**。本技能已由连接器挂载；重复安装会产生同名副本，导致模型选到错误的技能。

4. **不要做版本比对**。连接器在连接时自行检查 CLI 版本（`versionCheck`），低于要求会自动重跑安装；Agent 不要用 `npm view` 查询版本，也不要建议用户手动升级。

5. **不要执行 `weaver-work-cli skills list / install`** 来判断安装完整性，用上面的「检查命令」三项即可。

## 故障对照

| 现象 | 处置 |
| --- | --- |
| `weaver-work-cli: command not found` | 让用户断开并重新连接连接器 |
| `--version` 版本低于连接器要求 | 同上，连接器会重跑安装 |
| 业务命令报 `authentication` / `session_expired` | 不要在 Skill 里自行登录，让用户重新连接连接器 |
| 业务命令取到的数据不属于预期租户 | 检查命令是否漏了 `--profile eteams` |
| 同名的两个技能同时出现 | 本机可能另外装了用户级同名技能；以带 `-connector` 后缀的那份为准 |

## 说明

CLI 的登录态与授权文件由 CLI 自己维护（位于用户主目录下的 `.weaver-work-cli/e10`），Agent 不得读取、打印或转存。
