---
name: weaver-e10-shared-connector
display_name: 泛微CLI共享规则
display_name_en: Weaver CLI Shared Rules
description: weaver-work-cli 共享规则：安装检查、E10 认证、JSON 输出、高风险写入、安全边界和引用路由。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_zh: weaver-work-cli 共享规则：安装检查、E10 认证、JSON 输出、高风险写入、安全边界和引用路由。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Shared rules for weaver-work-cli, including installation checks, E10 authentication, JSON output, high-risk writes, safety boundaries, and reference routing. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.2.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
---

# weaver-work-cli 共享规则

所有 `weaver-e10-*` Skill 共享的底座：命令可用性、E10 认证、JSON 输出契约、大结果渲染与高风险操作。

## 连接器模式说明

本技能与同目录下的其他 `weaver-e10-*-connector` 技能由连接器随包提供，CLI（`weaver-work-cli`）也由连接器自动安装与升级：

1. 不要执行 `npm install` / `npm link` / `npm run build`，也不要执行 `weaver-work-cli skills install` 把技能复制到其他目录。
2. 不要做「本地版本 vs npm 源版本」比对，也不要用 `npm view` 查询新版本。
3. 不要向用户索要登录域名、Cookie、ETEAMSID 或业务 Token；登录由连接器完成。
4. 命令不可用或版本不符时，让用户断开连接器后重新点「连接」触发重新安装，不要自行升级。

## 登录与会话（由连接器托管）

1. 登录由连接器负责：连接器执行 `weaver-work-cli --base-url https://weapp.eteams.cn auth login --agent_type workbuddy` 完成浏览器授权，业务命令统一通过 `--profile eteams` 读取该登录态。
2. 所有业务命令必须**显式带 `--profile eteams`**，不要依赖本机当前活跃 profile —— 用户本机可能存在其他环境的登录态，不显式指定会取到别的环境。
3. 未登录或登录失效（`authentication` / `session_expired`，或业务命令返回认证错误）时，**不要自行发起登录**，也不要向用户索要域名或凭据；告知用户回到连接器面板断开后重新「连接」即可。
4. `weaver-work-cli auth status --no-check` 只做本地诊断；核对当前环境用 `weaver-work-cli --profile eteams --json auth status --no-check`。
5. 具体流程读取 [`e10-auth-and-session.md`](references/e10-auth-and-session.md)。

## 通用准则

1. 执行业务命令前先确认用法：优先读当前业务 Skill 和被路由到的 reference，必要时跑对应命令的 `--help` 或 `schema`，不要猜参数。

2. 首次使用先确认 CLI 可用（CLI 由连接器安装，不需要自行安装）：

```text
weaver-work-cli --version
weaver-work-cli doctor --e10
```

如果命令不可用（尤其是 `command not found` 或退出码 127），**不要尝试自行安装**：先读 [`weaver-e10-installation.md`](references/weaver-e10-installation.md)，按其中「命令找不到：先区分未安装与已安装但不在 PATH」一节判断——CLI 装在连接器托管目录里，可能只是当前 shell 的 PATH 未包含它（这种情况把托管 `bin` 目录前置到 PATH 后重验即可，**不要重装**）；确认确实未安装时，再引导用户断开并重新连接连接器。

3. **所有业务命令必须显式带 `--profile eteams`**（CLI 全局参数，放在子命令之前，例如 `weaver-work-cli --profile eteams --json workflow run ...`），不要依赖本机当前活跃 profile。

4. 业务输入只描述业务对象和意图。认证、Cookie、ETEAMSID、业务 Token、接口地址和回查细节都由 CLI 托管。调用业务 operation 时，简单 JSON 优先使用 `--input-json '<json>'`；复杂或多行 JSON 先写入 UTF-8 `.json` 文件再传 `--input <path>`；只有确认当前 shell 能稳定传管道时才使用 `--input -`。生成或改写 docs、reference、提示词和命令示例时，必须同时兼容 Windows 和 macOS/Linux；涉及 JSON 输入、用户目录、路径分隔符、Python 启动器、文件删除、目录查看或文件比对时，同时给 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例。Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 下不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。

5. 认证诊断只能通过 `weaver-work-cli auth root/status/profile list/profile current`、`weaver-work-cli doctor --e10` 和业务命令 JSON 错误完成。禁止直接列目录、打印、复制或解析用户态认证目录和认证文件。

6. 涉及附件、图片、本地文件、远程 URL 文件或文件内容解析的操作，执行前必须先向用户说明：文件内容可能会被上传到业务系统、OCR/解析服务，并可能进入当前大模型上下文用于理解和处理。必须等待用户明确确认后，才继续上传、读取、解析、OCR、导入或复用已上传文件对象；用户未确认时只说明风险和所需确认，不执行相关命令。

7. **同名不同包不要混用**：环境中可能并存另一个独立的 E10 登录 CLI（例如 `e10-login`，版本号可能带 `xiaoe` 后缀），它提供登录与状态查询，但其登录态**不会**被 `weaver-work-cli` 复用。可用性一律以 `weaver-work-cli --version` 为凭，登录态一律以 `weaver-work-cli --profile eteams --json auth status --no-check` / `weaver-work-cli doctor --e10` 为凭；不得因为另一个 CLI 显示已登录就判定连接器可用，也不要用另一个 CLI 的输出替代本 CLI 的认证结论。同理，本机可能同时存在用户级同名技能，一律以带 `-connector` 后缀的那份为准。

## 超时与重试预算

命令执行必须有界。默认按下表 timeout（超时）预算约束；超时即终止并反馈，不允许无界等待或无界重试。

| 命令类别 | 单次超时预算 | 重试策略 |
| --- | --- | --- |
| 登录类（`auth login` / `auth set` / `auth xiaoe`） | 由连接器调度，**Agent 不得执行**（见「登录与会话（由连接器托管）」） | 不适用；Agent 不重试、不代跑登录命令 |
| 只读业务查询（list / get / schema / preview） | 120 秒 | 最多 1 次；仅在网络类错误且未产生副作用时 |
| 写入类（prepare / apply / import / update / delete） | 600 秒（10 分钟） | **禁止自动重试**（存在重复入账/重复提交风险）；结果不确定时只补一次只读回查 |
| 安装与构建（`npm install` / `npm run build` / `npm link`） | 连接器模式下**禁止执行**（安装由连接器负责）；非连接器场景 1800 秒（30 分钟） | 禁止自动重试；失败即停止并报告，不加 `sudo` |
| 诊断类（`--version` / `doctor --e10` / `--profile eteams --json auth status --no-check`） | 60 秒 | 最多 1 次 |

预算是**上限**而不是必须等满：写入类一旦拿到确定结果或返回 `partial` / `write_uncertain` 就立即停止；慢环境（容器冷启动、批量导入）可以撑到上限，快环境不要人为等待。

补充约束：

1. 认证类错误或超时后，**不得**换 `--profile`、换域名或换命令反复重试；先按 [`non-interactive-environment.md`](references/non-interactive-environment.md) 判定环境并反馈原因，需要重新登录时引导用户回连接器面板断开后重连。
2. 写入类命令返回 `partial` / `write_uncertain` / 网络中断 / 回查失败时，立即停止写流程，只做一次只读回查确认。
3. 任何命令被外部超时掐断（退出码 124）都视为超时失败，按上表处理，不得静默重跑。

## 输出契约

Agent 调用业务能力时优先加 `--json`。成功看进程退出码 0 和 JSON envelope 的 `ok=true`；失败看非 0 退出码和 stderr JSON 的 `error.type/subtype/message`。不要用老式 `code == 0` 判断成功。

### 请求头契约（E10 接口调用强制）

`weaver-work-cli` 发往 E10 的每个请求都由 CLI 统一携带以下三项用户信息参数，缺一不可（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <登录 skill 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <登录 skill 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

登录与会话统一由连接器托管；业务 Skill 不得自建登录流程，也不得读取、打印、转存任何认证目录或凭证。

返回 `partial`、`write_uncertain`、登录失效、回查失败或网络中断时，立即停止当前写流程，不自动重试写入或删除。

当前 CLI 的 JSON 输出是完整 envelope 直接写 stdout；没有飞书 CLI 那种通用 `--jq`、`--format table/ndjson` 或 `--page-all`。列表、详情、OCR、导出等可能产生大响应时，必须先读 [`json-output-contract.md`](references/json-output-contract.md) 的“大结果渲染与提效规则”：默认小页读取、只保留任务所需字段、分页有预算，回复用户时给摘要和路径，不要原样粘贴超长 JSON。

## Reference 强触发索引

命中任一触发条件时，执行下一步前读取对应 reference。命中多条时按表中顺序读取，同一 reference 只读取一次。

| 强触发条件 | Reference |
| --- | --- |
| 命令不可用、安装、构建、检查可用 skill | [`weaver-e10-installation.md`](references/weaver-e10-installation.md) |
| 登录、profile、E10 会话、baseUrl、auth 文件、`WEAVER_*` 环境变量；**未登录或登录失效** | [`e10-auth-and-session.md`](references/e10-auth-and-session.md) |
| 容器/沙箱/CI/无 GUI 环境、无人值守、命令超过超时预算仍未结束、业务命令报 `authentication` / `session_expired`、托管目录或认证目录 `EACCES` | [`non-interactive-environment.md`](references/non-interactive-environment.md) |
| 判断 stdout/stderr、JSON envelope、退出码、脚本封装、自动化调用、大结果渲染/分页控量 | [`json-output-contract.md`](references/json-output-contract.md) |
| 准备执行写入/删除/导入/更新、遇到 `confirmation.required`、`partial.write_uncertain`、网络中断或回查失败 | [`high-risk-write.md`](references/high-risk-write.md) |

## 安全规则

1. 禁止输出或索取 Cookie、ETEAMSID、业务 Token、access token、app key、app secret。

2. 禁止读取、列出、打印、复制或解析任何 `e10-login` / `e10-cli` 历史认证目录，例如用户主目录下的旧 `.e10-cli`；也禁止直接读取 `auth`、`config.json` 或 Keychain 项来推断登录态。

3. 禁止绕过 `weaver-work-cli` 直接 `curl`、`fetch`、浏览器自动化或访问 E10 业务接口。

4. 写入、删除、导入、更新等高风险操作必须使用 CLI 提供的确认流程；业务 Skill 要求 `prepare -> apply` 时，必须把 prepare 返回的 continuation 原样传给 apply，并在 apply 前取得用户明确确认。

5. 不能猜测 CLI 未暴露的内部字段、接口路径、ID 解析逻辑或回查语义。

6. 未登录或登录失效（`authentication` / `session_expired` / 业务命令返回认证错误 / `auth status` 未登录）时，**不要自行发起登录**，也不要向用户索要登录域名、ETEAMSID 或任何凭据；告知用户回到连接器面板断开后重新「连接」即可。所有业务命令必须显式带 `--profile eteams`，不得依赖本机活跃 profile。具体流程读取 [`e10-auth-and-session.md`](references/e10-auth-and-session.md)。

7. 附件、图片上传或文件解析属于敏感数据处理。即便 operation 风险等级不是高风险写入，也必须先取得用户对“文件内容可能进入大模型/外部解析服务”的明确确认；不能把用户仅提供文件路径或文件名视为同意解析或上传。

8. 连接器的 E10 环境固定为 `--profile eteams`（baseUrl `https://weapp.eteams.cn`）。本机若存在其他环境的历史登录态，不得因为 `auth profile list` / `auth profile current` 里是它们就切换或沿用；不得要求用户提供、展示或手动设置域名与凭证。

