# fh CLI 安装、认证与配置（references/cli-connection.md）

> 加载时机：首次使用 / `fh` 不存在 / doctor 失败 / 401（退出码 3）/ 需要换环境时加载。
> 本文档取代旧 MCP 版的 `mcp-connection.md`（本 skill 不依赖宿主 MCP 能力）。

## 1. 安装

**WorkBuddy 连接器**由 `cli.json` 声明 `runtime.type: node`：点连接时宿主准备 Node，对
`https://crm.feiheair.com/download/fh-cli-0.1.4.tgz` 执行 `npm install -g`，随后 auth/status/unAuth 直接跑 `fh` / `fh.cmd`。
凭据仍在 `~/.fh/`，与安装目录分开。以下为人肉/开发场景的手工安装（Bun 编译的单文件）。

Windows 与 WSL 是**两个独立环境**，需要各装一份（Windows 用 `fh-*-win-x64.exe`，WSL 用 `fh-*-linux-x64`）。

若 `fh version` 已成功，跳过本节。否则用官方安装脚本（相对 **fh-cli 工程目录**，不要 `cd` 到任何作者机器上的盘符路径）：

```powershell
# Windows PowerShell（一键：装到 %LOCALAPPDATA%\fh 并写入用户 PATH）
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
# 装完【新开一个 PowerShell 窗口】再试 fh version（旧窗口不刷新 PATH）
```

```bash
# WSL / Linux（一键：装到 ~/.local/bin 并写入 ~/.profile 的 PATH）
bash scripts/install.sh
# 新开终端，或先 source ~/.profile
```

也可把发布包 `dist/` 下的单文件二进制拷入任意 PATH 目录。不要从作者仓库绝对路径构建。

手工安装与排障细节见 fh-cli 工程的 `docs/使用说明.md` §2。

## 2. 认证

凭据只由 fh CLI 自己保管（对齐飞书 `lark-cli` / 同程程心 `tc-chengxin`）。
文件在 `~/.fh/` 下，**文件名**以本 skill `config.json` 的 `credentialsFile` 为准
（生产默认 `credentials`；开发/测试打包盖成 `fh-travel-dev-credentials` /
`fh-travel-test-credentials`）。查询由 `mcp_proxy.py` 自动带 `--credentials-file`；
WorkBuddy 连接器的 login/status/logout 由 `cli.json` 带同一旗标。人手敲
`fh auth login` 时必须带同一旗标，否则会写到默认 `credentials`。

| 来源 | 场景 |
|---|---|
| `~/.fh/<credentialsFile>`（`fh auth login` 写入，0600） | WorkBuddy「连接器」走 cli.json 的 auth；人肉/开发直接跑下面的命令 |
| 无 → 退出码 3 | 按下列命令登录 |

运行时只读上述文件。过期由 `fh auth refresh` 写回同一文件。

```bash
fh --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth status
fh --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth login
fh --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth login --manual  # 8081 被占时粘贴回调地址
fh --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth logout
```

安全红线：token 永不进 argv、stdout、日志、结果文件；CLI 不会索要/回显密码与验证码。
token 失效（401）时 CLI 自动用 refresh_token 静默刷新重试一次；仍失败才报退出码 3。
refresh token 约 60 天，access token 约 1 小时。快过期时 CLI 静默刷新，不必让用户再次登录。

Windows 上入口是本 skill 目录里的 `auth-status.cmd`、`auth-login.cmd`。macOS / Linux 是同目录的 `sh auth-status.sh`、`sh auth-login.sh`。都由助手执行。脚本用 `node` 跑同目录 `cli/cli.js`（JavaScript，不是 exe），打开系统默认浏览器并等待本机回调。不必先有 PATH 上的 `fh`。
`auth-login.cmd` 或 `sh auth-login.sh` 必须在当前对话前台跑完，不要放到后台。用户只在弹出的系统默认浏览器中完成图形码和短信，然后关闭页面回到对话。
登录由脚本打开系统默认浏览器。不要把授权地址发到对话里点击，也不要用宿主内置浏览器。
桌面浏览器未弹出时：不要贴链接；助手可改跑 `auth-login.cmd --manual` / `sh auth-login.sh --manual`，或排查本机默认浏览器。
登录命令结束后（含非 0 退出码）：先跑 `auth-status.cmd` / `sh auth-status.sh`。stderr 已出现「登录成功」，或 status 显示已有有效凭据时，不要重复登录。
不要要求用户寻找本 skill 的安装目录，也不要要求用户自己双击或手敲这些文件。
`--manual` 用于端口占用或桌面浏览器未弹出时的兜底，不作为平时路径。

找不到 `node` 或 `cli/cli.js` 时：技能目录就是包含本文件的那一层（与 `SKILL.md` 并列），`cli/cli.js` 在其下。Windows 跑同目录 `auth-status.cmd` / `auth-login.cmd`；macOS / Linux 跑同目录 `sh auth-status.sh` / `sh auth-login.sh`。读 stderr。退出码 3 表示未登录；`node` 不是内部命令或 `command not found` 才是没有 Node。不要全盘搜索，不要让用户自己找文件夹，不要为了得到 `fh` 去 `npm install -g`。登录进程前台等到退出，最长约 5 分钟。

## 3. 环境自检

```bash
fh --base-url https://travel.feiheair.com/api/portal --credentials-file credentials doctor
```

输出逐项 ✔/✘：runtime / config / registry / credentials / endpoint(mcp) / endpoint(rest)。
REST 通道未部署在默认（mcp）模式下只是提示、不算失败。全部关键项通过时 rc=0。

## 4. 配置（四层：flag > env > profile 文件 > 默认）

```bash
fh config list                                   # 生效值 + 每项来源标注
fh profile add uat --base-url https://uat.feiheair.com/api/portal
fh profile use uat
fh config set defaults.timeout 120
fh config set defaults.transport auto            # 切换传输通道（见 §5）
```

| 环境变量 | 作用 |
|---|---|
| `FH_TRAVEL_BASE_URL` | 覆盖服务端 baseUrl |
| `FH_TRAVEL_PROFILE` | 覆盖默认 profile |
| `FH_TRAVEL_TIMEOUT` | 单请求超时秒数 |
| `FH_TRAVEL_TRANSPORT` | `mcp`/`rest`/`auto` |

注意 `baseUrl` 是 portal 基址（不含 `/mcp`），CLI 自动拼接各端点。

## 5. 传输通道

| 模式 | 说明 |
|---|---|
| `mcp`（默认） | 走服务端 MCP 端点（协议细节全封装在 CLI 内，宿主无需任何 MCP 能力） |
| `rest` | 纯 HTTP `POST {baseUrl}/cli/v1/call` + Bearer，需服务端部署 CliGatewayController |
| `auto` | REST 优先，未部署（404）时整进程自动回退 MCP |

两通道后端是同一份业务实现与安全策略（同一批 `@Tool`、同一身份闸门、同一出参打码），
信封与退出码完全一致；信封 `via` 字段标明实际通道。

## 6. 常见问题

| 症状 | 处理 |
|---|---|
| `fh: command not found` | 按 §1 安装；Windows 装完必须**新开终端** |
| 401 反复 / rc=3 | 先 `auth-status`；确认无效后再重新登录 |
| 登录命令 rc≠0，但曾出现「登录成功」 | 先 `auth-status`；有有效凭据则不要重复登录（可能是进程收尾异常） |
| `MCP_OAUTH_1006`（注册） | 回调地址不在白名单：用默认 `http://localhost:8081/callback` |
| 注册 429 | 单 IP 单日限 20 次：`fh auth use-token` 导入现成 token 或次日再试 |
| 端口 8081 被占 | `fh auth login --manual`（无需监听端口） |
| 授权页跳不到登录页，报 `CM_500 网络异常`，地址栏 URL 在 `?response_type=code` 后被截断 | 0.1.0 已知 bug：cmd 把授权 URL 在第一个 `&` 处截断；升级到 0.1.1，旧版用 `--manual` 手动复制完整 URL |
| 服务端 5xx / 超时 | rc=4，CLI 已自动重试 1 次；再失败如实告知用户稍后再试 |
| 更多 | fh-cli 工程 `docs/使用说明.md` §12 排障手册 |
