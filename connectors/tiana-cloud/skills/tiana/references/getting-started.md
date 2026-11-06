# 开始使用

在 Agent 实际执行命令的环境检查 `tiana version`。本技能要求 CLI 1.0.4 或更新正式版，具备分步登录、sqlite、git、web、file、list-template/init-template 和 version check。CLI 不存在时执行下面的 npm 安装并重新核验；已有版本过低时按更新流程取得用户确认后升级，再执行资源操作。不要仅凭同名命令存在跳过版本核验。

最低版本核验独立于更新提醒：0.x、预发行版、dev 或无法核实的版本不满足本技能基线。即使 `should_notify=false` 或更新检查不可用，也不能据此跳过最低版本要求；先完成已获授权的升级，尚未获授权时说明需要升级，暂缓依赖新版 CLI 的资源操作。CLI 与 Skills 独立编号，`--skills-version` 仍传实际加载的 Skills 版本。

最低版本升级已获授权但更新检查不可用时，可安装已发布基线 `npm install -g @tianacloud/cli@1.0.4 --registry=https://registry.npmjs.org/`，随后核验 `tiana version`；下载失败则报告实际错误，不继续资源操作。

## 安装

CLI 主包和适合当前系统的原生平台包都由 npm registry 提供。需要 Node.js 20+，使用 Tiana Git 还需要原生 Git。安装不运行下载二进制的 postinstall：

```sh
npm install -g @tianacloud/cli@latest --registry=https://registry.npmjs.org/
```

该包提供 `tiana` 和 `git-remote-tiana`，npm optionalDependencies 选择当前平台原生包；保持 optional 依赖启用，`--ignore-scripts` 也可以正常安装。缺少平台包时按实际错误修复安装，不能只凭命令入口存在宣称成功。Windows PowerShell 使用 `npm.cmd`，详情见 [Windows 安装](windows-install.md)和 [Git helper 排查](windows-git-helper.md)。

安装 Skills 使用 Node.js 22.20+：

```sh
npx --yes @tianacloud/agent-skills@latest install --agent codex
```

其他客户端按自己的安装目录使用 `install --dir PATH`，或不传目标运行客户端选择流程。四个 Skills 来自 npm 包内目录，安装后是持久文件副本。导入 Skill 与安装 CLI 是两步。

核验安装后直接执行 `tiana status`，按实际结果继续任务或恢复登录。用户同时要求创建应用时，完成安装和登录后继续原始需求。当前会话可以读取新安装的 SKILL.md 及其引用文件；宿主必须重载才可使用时，明确提示重载，并保留应用需求及本次环境选择。安装失败时报告实际阶段；没有执行过的登录、资源创建或发布仍然未知。

## 更新

四个入口共享会话内的更新检查记录：CLI 满足最低版本后，仅本会话首次使用 Tiana 技能时执行 `tiana version check --skills-version VERSION --json`；VERSION 来自本次加载的 Skill metadata.version。调用前在会话上下文中记录已尝试，返回后保留检查结果及用户的升级选择；失败或不可用也计为已尝试。后续轮次、重复加载和跨技能调用直接复用记录，不再自动检查；上下文压缩或任务交接时保留该记录，新会话重新检查。结果是直接 JSON，包含 should_notify、check_status 和 updates。

仅在 should_notify 为 true 时简短告诉用户 updates 中当前版本和新版本，并询问是否升级。不要因 updates 非空却 should_notify=false 再次提醒。CLI 保存两个包各自的检查尝试时间和共同的提醒时间，滚动 24 小时最多提醒一次；已核实 CLI 满足最低版本时，断网、更新状态不可写或待检查包版本未知不阻断任务。

当前 CLI 已满足最低版本时，用户选择稍后升级仍继续原任务；确认后才安装所选包的实际更新版本：CLI 使用 `npm install -g @tianacloud/cli@VERSION --registry=https://registry.npmjs.org/`；Skills 使用 `npx --yes @tianacloud/agent-skills@VERSION install --agent CLIENT`，或复用原来的 `--dir PATH`。VERSION 从检查结果取得，CLIENT/目录对应当前宿主的实际安装目标。

CLI 升级后核验 `tiana version` 和所需帮助；Skills 安装后检查四份 SKILL.md 的 metadata.version，并让宿主重载或开始新会话。当前会话已经加载的旧指令仍按旧版本处理，不把磁盘替换当作已重载。升级失败保留实际错误，不中途改动应用资源或凭据来修复。

## 环境与地址

未设置 `TIANA_API_ORIGIN` 时，CLI 默认连接 online：`https://console.tianacloud.com`，使用系统公有 CA；已保存的 staging 账号不会改变默认环境。外围启动器已设置变量时继承其选择。

用户在当前任务明确指定 origin（包括把 `export TIANA_API_ORIGIN=...` 写在请求中）时，将该值传入本任务后续每次 CLI、原生 Git 和相关子进程调用。优先使用执行器的环境参数；执行器只有 shell 时，在同一次调用中设置变量并执行命令。每次工具调用都可能启动新进程，安装时执行一次 export 不会影响后续调用。任务恢复时继续使用用户已选 origin；没有用户的新选择时不要自行切换。环境选择只属于当前任务，不写入技能目录、应用源码或用户启动文件。

例如用户明确选择 staging 后，每次 POSIX shell 调用都携带环境，包括安装后的独立调用：

```sh
export TIANA_API_ORIGIN=https://console.tianacloud-staging.net
tiana status
```

后续 `git push` 也在其所在的工具调用中设置相同变量，让 `git-remote-tiana` 继承。PowerShell 使用 `$env:TIANA_API_ORIGIN`，同样需在每次独立调用中传递。

staging CLI 自动加载内置公共根证书，无需另设 CA 文件；开发者须已接入 staging VPN/DNS，并为浏览器一次性安装 staging CA。证书来源、指纹和安装步骤见 [CLI staging 信任说明](https://github.com/tianacloud/cli/blob/main/docs/staging-ca.md)。证书故障按实际提示处理，不能关闭验证或切到另一个环境。

WorkBuddy Connector 由自身命令环境固定 online，其安装、登录及业务命令沿用该环境。

Console/管理 API、用户 Web 地址、数据库 Endpoint 各有用途：全部取实际 CLI/服务回执，不猜域名或把管理地址作为数据库连接地址。应用地址使用回执中的 application_url，Git URL 使用用户 Git 实例的 Endpoint。

## 对话中的登录

1. 执行 `tiana login --start --no-open --json`。
2. 向用户展示 data.verification_uri，等待用户打开并批准。status=pending、退出码 3 表示等待授权。
3. 用户授权后 `tiana login --resume --json`；只有 status=succeeded 且 data.logged_in=true 才继续。仍等待时保留同一链接和 data.retry_after，不连续 start。
4. 链接失效后再 start。CLI 保存账号会话，不需要读取凭据文件。

普通终端也可执行 `tiana login`。用量接口失败不代表退出登录；命令与恢复见 [CLI 指引](cloud-cli.md)。


配套修复后的 CLI 在缺少 pending 时返回 `NO_PENDING_AUTH`、`pending_auth:false`，不据此否定当前登录；用 `tiana status --json` 单独核实。`logged_in` 仅在本次已确认登录成功时为 true，其他登录结果可能省略；省略 `pending_auth` 表示无法确认 pending 是否仍在，保存/网络失败后不能假定授权已丢失。按错误 code/message/next_action 处理目录、锁、过期或拒绝，不机械重复 start。先通过 `--help` 核实当前安装版本的新 JSON 能力。
