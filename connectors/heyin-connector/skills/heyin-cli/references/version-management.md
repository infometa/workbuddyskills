# 版本管理

## 安装

### WorkBuddy 中的安装顺序

先检查实际命令 `heyincli`（Windows 为 `heyincli.cmd`）的路径、`-v` 和 `--help`。已可用且版本满足要求时直接复用；技能名 `heyin-cli` 不是命令名。

找不到命令时，优先通过 `heyin-connector` 连接器的宿主连接入口完成初始化；没有直接操作入口时引导用户在连接器界面完成，不臆造工具或命令。等待初始化结束后，在连接器提供的执行环境中验证命令。连接器使用宿主管理的运行环境和安装位置，普通终端 PATH 中找不到命令不代表初始化失败，不写死托管安装路径，也不要求先在系统中安装 Node.js。

只有连接器初始化明确失败，或确认连接器不可用，且命令仍不可用时，才进入下方现有安装流程。等待中或工具超时不能作为失败依据，不并行启动两种安装；用户明确取消时停止。非 WorkBuddy 环境直接使用下方流程。

无论通过哪种方式安装，都应验证实际命令路径、版本和帮助，再按本技能“授权”流程检查登录态；连接器已经完成授权时直接复用，不重新登录。

### 现有安装流程（独立环境或连接器失败后）

需要 Node.js 22.20.0 或以上版本，支持 Windows、macOS 和 Linux。在独立 AI 工具中，一条命令安装 CLI 与配套技能：

```sh
npx @heyinkeji/cli@latest install
```

按向导选择目标 AI 工具；再次执行同一命令可同步更新 CLI 与配套技能。普通 `npm install -g @heyinkeji/cli@latest` 只更新 CLI，不安装或更新技能。

非交互环境必须同时提供 `--agent` 和 `--yes`（或 `-y`）；`--agent` 可重复传入。按用户指定的工具选择安装目标，例如：

```sh
npx @heyinkeji/cli@latest install --agent codex --agent claude-code --yes
```

支持的工具为 `codex`、`claude-code`、`cursor`、`codebuddy`、`gemini-cli`、`opencode`、`workbuddy`。CLI 安装到 npm 全局目录，配套技能安装到所选工具的用户级目录；自定义或已修改的同名技能不会被覆盖。`--yes` 仅确认安装，不代表同意登录授权。交互安装后会询问是否启动授权；非交互安装后按本技能“授权”流程先查状态，已登录直接复用，需要时只启动一次登录并等待完成后复查。完整参数可通过 `npx @heyinkeji/cli@latest install --help` 查看。

WorkBuddy 由宿主加载连接器中的技能，并通过初始化、认证和环境配置管理 CLI。

安装完成后检查版本与帮助：

```sh
heyincli -v
heyincli --help
```

Windows 可使用 `heyincli.cmd -v` 和 `heyincli.cmd --help`。本技能以 CLI 1.0.0 为已核实的兼容基线，使用时需要 CLI 1.0.0 或以上版本；技能清单与 WorkBuddy 连接器采用相同的版本要求。

## 查看与更新版本

`heyincli -v` 显示当前 CLI 版本，不需要登录。更新到最新发布版本后，再次检查：

```sh
npm install -g @heyinkeji/cli@latest
heyincli -v
```

独立 AI 工具需要同步技能时，执行 `npx @heyinkeji/cli@latest install`；WorkBuddy 配套技能通过更新连接器获得。

若终端提示找不到命令，确认安装成功并重新打开终端，再执行版本检查。

## 强制更新

如果 CLI 调用服务端后失败退出，标准错误中的 API 错误包含 `code 4001010011`，表示服务端要求更新客户端。CLI 不会在标准输出中返回该业务错误信封。必须先更新 CLI，再按下述核实步骤决定是否重新执行原指令；不得继续使用旧版本重试或跳过更新。

```sh
npm install -g @heyinkeji/cli@latest
heyincli -v
```

确认安装成功，且当前版本满足服务端要求后，使用原参数重新执行用户已授权的指令。若更新失败或最新发布版本仍不满足要求，停止执行并向用户说明原因。对于写入指令，若此前执行结果不明确，更新后先查询实际状态，避免重复提交。

## 卸载

用户要求卸载时，说明卸载范围后执行：

```sh
npx @heyinkeji/cli@latest uninstall
```

交互模式会要求确认；用户已明确授权以下完整卸载范围时，可使用 `--yes`（或 `-y`），非交互环境必须提供：

```sh
npx @heyinkeji/cli@latest uninstall --yes
```

卸载按以下顺序执行：

1. 调用服务端 API 删除本地保存的全部 Token 对应的远端令牌，并清理本地副本；令牌立即失效，可能影响其他使用它们的工具。
2. 执行 `auth logout`，撤销 OAuth 授权并清理登录凭据。
3. 删除 `~/.heyin/config.json`。
4. 清理全部支持工具中的当前技能源清单中的官方合因技能，包括修改过的官方同名技能；不支持通过 `--agent` 限定卸载目标。
5. 卸载 npm 全局 `@heyinkeji/cli` 命令行。

任一步失败都会停止后续步骤，已完成的删除不回滚；根据错误修复后再执行，结果不明时先核实。未安装项跳过，其他技能、`~/.heyin/.env`、npm 缓存和手动安装的 CLI 保留。参数说明见 `npx @heyinkeji/cli@latest uninstall --help`。

`install` 和 `uninstall` 由 npm 入口提供，直接下载的 Go 二进制不包含这两个命令。
