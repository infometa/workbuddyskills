# guansd 命令速查

`guansd` 是观思动的本地开发命令行（npm 包 `guansd`，Node.js 20+）。所有命令都接受 `--origin <控制台地址>`
（私有部署用；默认 `https://console.guansd.cn`）。查看类命令支持 `--json`；任何命令后加 `--help` 看参数。
参数写法是 `--名字 值` / `--开关`，不认识的参数会被拒绝并打印该命令的用法。

## 账户级（在任何目录都能运行）

| 命令 | 用途 |
|---|---|
| `guansd whoami [--json]` | 我是谁、在哪个团队、管几个应用；本机有哪些应用凭证；在应用目录里还会报当前目录对应的应用，`--json` 里带 `urls.dev` / `urls.prod` 网址 |
| `guansd apps [--json]` | 名下应用清单：正式版 / 开发版状态、待授权功能、近 7 天活跃人数 |
| `guansd create <名称> [--slug x] [--desc 一句话]` | 创建应用（中文名即可，网址标识自动取拼音；用户成为负责人）；打印下一步的 clone 命令 |
| `guansd clone <org/slug 或 slug> [目录名]` | 克隆应用的 `work` 分支并接好凭证（无需浏览器；会等后台预置完成，最长 90 秒） |
| `guansd login [--device \| --browser]` | 浏览器授权一次，凭据只存本机 `~/.guansd`（0600）。**连接器已代为完成，不要再跑** |
| `guansd logout` | 撤销并清除本机的账户级授权。**连接器的「断开」会调用它，不要自己跑** |
| `guansd setup [--client <name>] [--print]` | 把平台接进本机的编程助手（写 MCP 配置）。WorkBuddy 内不需要 |
| `guansd doctor` | 自检：环境、PATH、登录、平台连通、当前目录 |

## 应用级（在 `guansd clone` 出来的目录里运行，或加 `--app org/slug`）

| 命令 | 用途 |
|---|---|
| `guansd check` | 预检：部署的安全门槛在**已推送**的代码上先跑一遍（秒级）。红了部署必红 |
| `guansd deploy [--no-wait]` | 部署当前目录的应用到开发版，跟踪到 healthy / failed。本地有未推送提交时拒绝；应用被对话任务占用时拒绝（409） |
| `guansd status [deployId]` | 某次部署的状态（缺省为最近一次）；failed 时带 failureReason |
| `guansd runtime [--env dev\|prod]` | 应用此刻是否在跑；开发版还会报密钥是否已配、功能权限是否已授权，以及正式版操作开关 |
| `guansd history [--limit 20]` | 版本历史（开发版 + 正式版），标出正在服务的和可回滚的 |
| `guansd logs [--env dev\|prod] [--since 秒] [--contains 关键词] [--max-bytes N]` | 应用运行日志（跨部署） |
| `guansd open [--prod]` | 在本机浏览器打开开发版 / 正式版网址 |
| `guansd verify "<要验证的主流程>"` | 请平台验收 AI 在开发版的一次性隔离副本上开真浏览器验证；发布前必须 ok，且要实际操作过。开头打印验证 id，然后阻塞到结束（1–4 分钟，没有 `--no-wait`）；被中断后用下一行接着等 |
| `guansd verify --status [id] [--wait]` | 看已经跑过的验证（不带 id 看最近一次；`--wait` 等它结束） |
| `guansd promote` | 发布到正式版（发布的是已验证的那次开发版镜像；202 后自动跟踪；发布后列出仍待授权的功能） |
| `guansd rollback [<deployId>]` | 回滚正式版到历史版本（不带参数列出可选目标；不需要验收） |
| `guansd token [--app org/slug]` | 打印一个当前有效的 access token（给 curl 用；勿写进文件或对话） |

## 管道（不是给人敲的）

| 命令 | 用途 |
|---|---|
| `guansd mcp [--app org/slug \| --account]` | stdio MCP 服务，给编程助手用；在应用目录自动定位到该应用 |
| `guansd git-credential` | git 按凭据助手协议调用它（`guansd clone` 已配置好），不要手动运行 |

## 环境变量

| 变量 | 含义 |
|---|---|
| `GUANSD_ORIGIN` | 平台地址（等价于 `--origin`） |
| `GUANSD_TOKEN` | CI 用：直接用指定的长期令牌，跳过本机凭据 |

## 退出码

0 成功；1 失败（未登录、接口错误、部署失败、验收未通过等，错误原因在 stderr）；2 用法错误。
