---
name: ziniao-shared
version: 1.2.0
description: "紫鸟 CLI 共享基础：连接器登录态、ZClaw 客户端与 Bridge 就绪、统一 apiKey 认证、错误处理、输出格式和安全规则。当用户通过 WorkBuddy 操作紫鸟、启动紫鸟客户端、登录 ZClaw 或排查认证/Bridge 问题时触发。"
author: "Ziniao"
metadata:
  requires:
    bins: ["ziniao-cli"]
---

# ziniao-cli 共享规则

本技能指导你如何通过 ziniao-cli 操作紫鸟开放平台资源和控制紫鸟浏览器，以及有哪些注意事项。

## 登录

WorkBuddy 连接这个连接器之后，API Key 已经保存在本机。不要运行 `ziniao-cli config init`，也不要运行 `ziniao-cli workbuddy login` 再创建一次应用。

命令返回未登录、API Key 无效或缺失时，请用户在 WorkBuddy 里重新连接。

连接器登录在浏览器里用开放平台账号完成，不要求本机紫鸟客户端已经登录。店铺浏览器操作仍然需要本机客户端。

`ziniao-cli zclaw login` 只登录浏览器会话，和连接器保存的 API Key 不是同一件事。`ziniao-cli login` 不是有效命令。

### Boss 与成员账号

登录完成时服务端返回 `isBoss` 标识，决定账号权限范围：

| 账号类型 | 服务端 API | ZClaw Bridge（本地浏览器） |
|---------|-----------|--------------------------|
| Boss | ✓ 全部可用 | ✓ 全部可用 |
| 成员 | ✗ 不可用（返回 auth 错误） | ✓ 全部可用 |

服务端 API 权限仅 Boss 账号可申请和调用。成员账号不能开通这些权限点；所有通过 `api` 命令或服务端快捷命令（account/staff/department/role/device）的请求会被拦截并提示"需要 Boss 权限"。

### 检查配置

```bash
ziniao-cli config show   # 查看当前配置（含 profile 名称）
ziniao-cli config list   # 列出所有 profile
ziniao-cli doctor         # 自检（配置、apiKey、Skills、客户端、本地 Bridge）
```

## ZClaw 客户端与 Bridge 就绪

ZClaw 本地浏览器操作依赖紫鸟客户端和本地 Bridge。本次任务首次执行店铺或页面命令前，先运行以下命令检查环境：

### 登录命令硬约束

本节所有“登录”“自动登录”“先登录”都只表示逐字执行 `ziniao-cli zclaw login`。不存在可替代的 `ziniao-cli login`，也不得省略 `zclaw`。在输出或执行登录步骤前先核对完整命令。

```bash
ziniao-cli doctor
```

判断本地浏览器操作（`store` / `page` / `zclaw`）能否继续时，只看与本地环境相关的明细，不要看最后的「全部检查通过 / 部分检查未通过」：

- **需要通过：** 配置文件、API Key 有效（含终端绑定）、客户端已启动并已登录、客户端账号与当前 profile 一致、ZClaw Bridge 连通。
- **不拦截：** Skills 未安装或有新版本（仅提醒）。

上述本地项通过后，直接执行原店铺或页面命令。一次任务内本地环境未变化时，不要为每个后续命令重复检查。

当 `doctor` 的客户端明细明确显示“紫鸟客户端已启动，但尚未登录”或 `[CLIENT_LOGGED_OUT]`，且 Bridge 已连通、没有 API Key、终端绑定或账号不一致错误时，这已经是确定的未登录状态。未登录恢复命令固定且只能是 `ziniao-cli zclaw login`；`ziniao-cli login` 不是有效命令，不得缩写或替换。必须在任何 `store`、`page` 业务命令之前按以下顺序执行：

```bash
ziniao-cli zclaw login
ziniao-cli doctor
# 仅当本地浏览器相关明细通过时，执行一次原业务命令
```

禁止先调用 `store list`、`store resolve`、`store open` 或 `page` 命令来再次探测登录状态，即使 `doctor` 退出码为 0 或 Bridge 显示正常也不例外。登录失败或复查仍未通过时立即停止并报告实际错误。

仅当 `doctor` 的客户端检查明确显示“紫鸟客户端未启动或本地服务未就绪”时，才可尝试启动客户端。调用前按**当前 Shell**选择一种命令检查 `ziniao` 是否可解析，不得把某一种检测命令用于所有平台，也不得依次执行多种检测命令：

| 当前 Shell | 命令检测 |
|------------|----------|
| Windows PowerShell | `Get-Command ziniao -ErrorAction SilentlyContinue` |
| Windows CMD | `where.exe ziniao` |
| macOS/Linux Bash、Zsh、sh，或 Windows Git Bash | `command -v ziniao` |

若当前 Shell 找不到 `ziniao`，不得调用或重试 `ziniao start`。macOS 例外：如果 `/Applications/ziniao.app` 存在，可执行一次 `open -a "/Applications/ziniao.app"` 启动桌面客户端，然后重新运行 `ziniao-cli doctor`；不得把 `open` 当作 Bridge 就绪证明。其他平台提示用户手动启动紫鸟客户端，用户完成后重新运行 `ziniao-cli doctor`。只有找到 `ziniao` 命令时，才执行一次：

```bash
ziniao start
ziniao-cli doctor
```

`ziniao start` 只用于启动或唤起单实例紫鸟客户端，不能修复 API Key、终端绑定、账号不一致或登录会话问题。Bridge 可能在客户端启动后才就绪；启动后可短间隔重新运行 `doctor`，总等待时间最多 30 秒。若 `ziniao start` 返回 Windows 错误 1113 或其他启动错误，或命令成功返回但 macOS 上 `doctor` 仍明确显示客户端未启动，可在 `/Applications/ziniao.app` 存在时额外执行一次 `open -a "/Applications/ziniao.app"`，随后重新运行 `doctor`；不得再次重试 `ziniao start`。仍未通过则报告启动错误和 doctor 明细后停止。

如果 `doctor` 报告 `127.0.0.1:9481` 无法连接，先把它视为“诊断未确定”，不得直接说紫鸟未启动，也不得直接建议升级客户端。当前任务运行在受限沙箱时，必须先用系统权限/绕过沙箱做一次只读复查（至少重新运行 `ziniao-cli doctor`；必要时直接探测 `http://127.0.0.1:9481/`）。按复查结果分流：

- 系统权限下 Bridge 可连接并返回 `Ziniao user is not logged in` 或 HTTP 401：Bridge 和客户端实际在运行，执行一次 `ziniao-cli zclaw login`，再用同一权限复查 `doctor`，通过后执行原业务命令。
- 系统权限下 Bridge 可连接且返回其他明确错误：报告该原始错误，不得改写成“客户端未启动”。
- 系统权限下仍无法连接：再检查客户端进程/监听端口；只有确认 Bridge 进程不存在、端口未监听或启动失败时，才进入 `ziniao start` 流程。
- 仅 API Key 校验失败：单独报告 API Key 问题，不得据此推断本地客户端或 Bridge 未启动。

如果 Bridge 暂时不可连接，可在完成上述系统权限复查后短间隔重试 `doctor`，总等待时间最多 30 秒。不要把启动或登录当作状态探测；只有证据明确支持时才启动或登录。

独立的运行中会话失效分支：如果此前 `doctor` 明细已经通过，但原始 `store`、`page` 或其他 ZClaw 本地命令随后明确返回 `Ziniao user is not logged in`，下一条命令必须逐字为：

```bash
ziniao-cli zclaw login
```

这里同样只能使用完整命令 `ziniao-cli zclaw login`，不得写成不存在的 `ziniao-cli login`。登录成功后，使用相同参数只重试刚才失败的原命令一次；不要为了这次恢复额外执行 `doctor`。不得在尚未尝试 `zclaw login` 前要求用户手工登录。

若 `zclaw login` 失败，直接报告其实际错误。API Key 无效或被拒绝、终端未绑定、账号不一致，或 Bridge 不可连接时，必须立即停止，禁止重复登录、重复发送店铺请求，或笼统要求用户“先登录客户端”。只有原始错误不是该精确未登录错误、或登录命令本身无法恢复时，才按对应原因要求用户处理前置条件。

只有 `doctor` 显示配置、API Key、ZClaw Bridge 连通、客户端已登录且账号与当前 profile 一致时，才继续浏览器操作。Skills 版本提醒不作为拦截条件：

- 店铺窗口操作使用 `ziniao-store` Skill。
- 页面浏览器自动化使用 `ziniao-page` Skill。
- 查询可用 Bridge 工具使用 `ziniao-cli zclaw tools`；仅在没有快捷命令或用户明确要求调试原始工具时，才使用 `ziniao-cli zclaw invoke <tool>`。

| 现象 | 处理 |
|------|------|
| 店铺或页面命令提示客户端未登录 | 启动并登录紫鸟客户端后再重试该命令。这不影响连接器登录；连接器登录在浏览器里完成。 |
| `doctor` 的 ZClaw Bridge 检查提示 ziniao 进程正在运行但无法连接，或要求关闭「多开工作台」 | 不要执行 `ziniao start` 或 `zclaw login`。提示用户到紫鸟客户端「本地设置」-「偏好设置」关闭「多开工作台」，完成后重新运行 `doctor`。 |
| `doctor` 提示客户端未启动或本地服务未就绪 | 按当前 Shell 使用 PowerShell `Get-Command`、CMD `where.exe` 或 POSIX/Git Bash `command -v` 检测；找到命令才执行一次 `ziniao start`。若 macOS 上 `ziniao start` 失败或执行后仍未启动，且存在 `/Applications/ziniao.app`，可再执行一次 `open -a "/Applications/ziniao.app"`，随后重新运行 `doctor`；若 macOS 找不到命令但应用存在，也直接使用一次 `open`；其他情况提示用户手动启动。 |
| `doctor` 明确显示客户端已启动但未登录，且 Bridge 已连通 | 直接执行一次 `ziniao-cli zclaw login`，不得先发店铺或页面命令探测；登录后重新运行 `doctor`，本地浏览器相关明细通过后才执行原业务命令。 |
| `127.0.0.1:9481` 暂不可连接 | 先绕过沙箱用系统权限只读复查 `doctor`，必要时直接探测 Bridge；按返回体区分“未登录”、其他 Bridge 错误和真正未监听。未完成系统权限复查前，不得直接提示客户端未启动。 |
| `ziniao start` 返回 Windows 错误 1113 或其他启动错误 | 不重试启动；立即重新运行一次 `doctor`，明细通过则继续，否则同时报告启动错误和 doctor 明细后停止。 |
| `zclaw login` 提示无法连接 ZClaw Bridge | 不把登录当作启动探测；回到 `doctor` 判断 9481 不可连接的具体原因。 |
| API Key 无效或未配置 | 请用户在 WorkBuddy 里重新连接。不要运行 `config init` 或 `workbuddy login`。 |
| 初始化后 ZClaw 仍提示 API Key 认证失败 | 前往 https://open.ziniao.com 的用户应用「终端管理」，绑定当前终端识别码（在紫鸟浏览器设置中查看），然后重新执行 `ziniao-cli zclaw login` 和 `ziniao-cli doctor`。 |
| `doctor` 提示客户端登录用户与当前 profile 不一致 | 明确说明当前 profile 与客户端登录账号及其不一致，询问用户是否切换到当前 profile 对应账号并继续原请求；不要只要求用户手工切换。用户确认后按既有登录流程继续。 |

### 多账号切换

支持多个账号配置（profile），通过 `config use` 切换：

```bash
# 列出所有 profile
ziniao-cli config list
# * zhangsan
#   staging

# 切换到指定 profile
ziniao-cli config use staging

# 重命名 profile
ziniao-cli config rename staging production
```

连接成功后，profile 使用账号用户名命名。

### 退出登录

不要在任务里删除 profile，也不要运行 `config remove`。用户要退出时，让他在 WorkBuddy 里断开这个连接器。

## 认证

### 认证模型

ziniao-cli 使用**统一 apiKey**（Bearer Token），一个 Key 同时用于：

| 用途 | 地址 | 说明 |
|------|------|------|
| 服务端 API | `sbappstoreapi.ziniao.com` | 部门/员工/账号/设备等业务接口 |
| 本地 ZClaw Bridge | `127.0.0.1:9481` | 紫鸟浏览器店铺/页面操控 |

**没有** OAuth、token 刷新、双身份（user/bot）等复杂机制。apiKey 是静态凭证，不过期。

### ISV 应用权限点

调用服务端 API 前，需在紫鸟开放平台为应用开通对应的权限点。这些权限仅 Boss 账号可申请和调用。以下是各模块所需的权限点：

| 模块 | 权限点 | 覆盖接口 |
|------|--------|---------|
| 部门员工 | ERP-部门与员工接口 | 部门 CRUD + 员工查询/新增/修改/启禁用（9 个） |
| 部门员工 | ERP-用户的部门变更 | 员工调岗（1 个） |
| 角色权限 | ERP-角色列表查询 | 角色列表 + 用户角色列表（2 个） |
| 角色权限 | ERP-角色详情 | 角色详情（1 个） |
| 角色权限 | ERP-权限列表 | 权限项列表（1 个） |
| 角色权限 | ERP-角色添加、修改权限 | 添加/修改/调整角色（3 个） |
| 设备管理 | ERP-设备查询 | 设备列表 + 历史绑定记录（2 个） |
| 设备管理 | ERP-设备套餐列表查询权限 | 套餐列表（1 个） |
| 设备管理 | ERP-设备绑定权限 | 绑定设备（1 个） |
| 设备管理 | ERP-解绑设备 | 解绑设备（1 个） |
| 设备管理 | ERP-开关自动续费 | 自动续费开关（1 个） |
| 设备管理 | ERP-设备购买与续费权限 | 购买 + 续费（2 个） |
| 设备管理 | ERP-添加自有设备（新） | 添加自有设备（1 个） |
| 设备管理 | ERP-修改自有设备信息（新） | 修改自有设备（1 个） |
| 设备管理 | ERP-查询已购设备价格接口 | 已购设备价格（1 个） |
| 账号管理 | ERP-账号查看权限 | 账号列表/授权查询/用户账号列表/授权用户列表（4 个） |
| 账号管理 | ERP-创建与删除账号权限 | 创建 + 删除账号（2 个） |
| 账号管理 | ERP-编辑账号基础信息 | 编辑账号信息（1 个） |
| 账号管理 | ERP-账号授权权限 | 授权新增 + 授权删除（2 个） |
| 账号管理 | ERP-清除账号授权 | 清除全部授权（1 个） |
| 账号管理 | ERP-清除账号缓存 | 清除缓存（1 个） |
| 账号管理 | ERP-标签列表 | 企业标签列表（1 个） |
| 账号管理 | ERP-查询某用户有权限的账号列表 | 用户有权限的账号（1 个） |
| 账号管理 | ERP-获取附加网站信息 | 附加网站信息（1 个） |
| 账号管理 | 账号标签管理权限 | 标签 CRUD + 绑定/解绑/替换/清空/移除（9 个） |
| 访问策略 | ERP-网页访问权限 | 访问规则/网页/网页分组全部操作（22 个） |

> 如果调用接口返回 `isv.invalid-method`（不存在的方法名），通常是该权限点未开通。前往 [紫鸟开放平台](https://open.ziniao.com) → 应用管理 → 权限管理 中开通。

### 公共参数

每个服务端 API 请求都需要 `companyId`，**CLI 自动注入并强制使用配置值**，无需也不应手动传递。该值在连接成功时自动写入配置；即使 `--data` 中显式传入 `companyId`，CLI 也会用配置值覆盖。

## 两层命令体系

### 第一层：通用 api 命令（覆盖全部 73 个接口）

任何紫鸟服务端 API 都可以通过 `api` 命令调用，无需专门的快捷命令：

```bash
ziniao-cli api <path> [--data '{}'] [--format table] [--jq '.data[]']
ziniao-cli api GET /app/builtin/company
ziniao-cli api /superbrowser/rest/v1/erp/department/list
ziniao-cli api /superbrowser/rest/v1/erp/staff/list --data '{"page":1,"limit":10}' --format table
```

- 默认 POST 方法，支持 GET/POST/PUT/DELETE
- `companyId` 由框架自动注入，并强制覆盖 `--data` 中的同名字段
- `--page-all` 自动翻页（默认最多 10 页，需取全部时配合 `--page-limit 0`）
- `--page-size N` 每页条数（默认 20）
- `--page-limit N` 最大翻页数（默认 10，0 为不限，配合 `--page-all`）
- `--page-delay MS` 翻页间隔毫秒数（默认 200，配合 `--page-all`）
- `--dry-run` 预览请求不执行
- `--jq` 内置 jq 过滤

### 第二层：快捷命令（高频场景优化）

为复杂接口提供命名 flag + 智能默认值：

```bash
ziniao-cli department list --tree
ziniao-cli staff create --username "zhangsan" --name "张三" --password "Pass123!" --role-id 16691047257645
ziniao-cli store list --format table
```

## `account` 与 `store` 的区别

两组命令都涉及"店铺"，但职责和通道完全不同：

| | `account` 命令 | `store` 命令 |
|--|---------------|-------------|
| 通道 | 服务端 API（`sbappstoreapi.ziniao.com`） | 本地 ZClaw Bridge（`127.0.0.1:9481`） |
| 职责 | 店铺账号的 CRUD、授权、标签等**管理操作** | 控制已打开的浏览器实例：列出、打开、关闭 |
| 前置条件 | 只需 apiKey + 网络 | 紫鸟浏览器客户端必须已启动 |
| 典型场景 | 创建店铺、批量授权员工、管理标签 | 打开店铺浏览器 → 导航 → 截图 → 自动化操作 |

**简单记忆：** `account` = 管理后台增删改查，`store` = 控制本地浏览器窗口。

## 命令优先级

AI Agent 调用时按优先级选择：

1. **快捷命令** -- `staff list`、`department create`、`store open` 等（参数简化，体验最好）
2. **通用 api 命令** -- `api <path>` 兜底（任意接口都能调，需要手写 JSON body）
3. **zclaw invoke** -- `zclaw invoke <tool>` 兜底（任意 ZClaw 工具都能调）

### ZClaw 快捷命令硬约束

若某个 ZClaw 工具已有对应快捷命令，**必须只调用快捷命令**，禁止再调用
`ziniao-cli zclaw invoke <tool>`。两者最终都会请求同一个 Bridge 工具；重复调用会重复执行操作。

`zclaw invoke` 仅用于没有快捷命令的 Bridge 工具，或用户明确要求按原始工具名和 JSON 参数调试。

例如 `visit_page` 已由 `page visit` 封装，必须使用 `ziniao-cli page visit ...`。

### 店铺环境结果硬约束

当用户要求店铺浏览器、店铺代理或该店铺登录态下的结果时，结果只能来自该店铺环境。
店铺页面操作失败后，禁止改用公开网页、搜索引擎、其他店铺、服务端 API 或供应来源来“替代”结果；除非用户明确将任务范围改为公开信息检索。

发生 `ERR_SOCKS_CONNECTION_FAILED` 时，保持当前店铺打开，等待 5 秒后以相同参数重试；最多 3 次总尝试。仍失败时，报告该店铺环境暂时无法访问及已尝试次数，并停止该店铺任务；不得声称已取得店铺环境结果。

## 输出格式

所有命令支持 `--format json|table|csv` 和 `--jq` 过滤：

```bash
ziniao-cli staff list --format table
ziniao-cli staff list --jq '.[].name'
ziniao-cli department list --format csv
```

### 输出结构

成功（stdout）：
```json
{"ok": true, "data": ..., "meta": {"count": 10}}
```

失败（stderr）：
```json
{"ok": false, "error": {"type": "gateway|business|auth|validation", "code": 1001, "message": "...", "hint": "..."}}
```

### 错误类型与处理

| 错误类型 | 含义 | AI Agent 应该做什么 |
|---------|------|-------------------|
| `auth` | apiKey 缺失或无效 | 请用户在 WorkBuddy 里重新连接 |
| `gateway` | 网关层错误 (code != "0") | 报告错误，检查网络/apiKey |
| `business` | 业务层错误 (ret != 0) | 报告错误信息，根据 msg 判断原因 |
| `validation` | 参数校验失败 | 检查命令参数是否正确 |
| `network` | 网络不通/Bridge 未启动 | ZClaw 相关：回到 `doctor` 明细路由，只有客户端未启动时才进入启动流程；API 相关：检查网络 |

## 更新检查

ziniao-cli 命令执行后，如果检测到新版本，JSON 输出中会包含 `_notice.update` 字段：

```json
{
  "ok": true,
  "data": ...,
  "_notice": {
    "update": {
      "current": "1.0.0",
      "latest": "1.1.0",
      "message": "ziniao-cli 1.1.0 可用，当前 1.0.0，运行 npm update -g @ziniao-open/cli 更新"
    }
  }
}
```

**当你在输出中看到 `_notice.update` 时：**
1. 先完成用户当前请求
2. 然后将 `message` 字段内容展示给用户，提议帮其更新
3. 若用户同意，执行 `npm update -g @ziniao-open/cli`

更新提示仅通过 stdout JSON 的 `_notice` 字段传递，不会输出到 stderr。可通过环境变量 `ZINIAO_CLI_NO_UPDATE_CHECK=1` 禁用检查。

## 环境兼容说明

### Windows Git Bash 路径转义问题

在 **Git Bash** 中，以 `/` 开头的字符串会被 MSYS 自动转换为 Windows 本地路径（如 `/superbrowser/...` → `C:/Program Files/Git/superbrowser/...`），导致 `api` 命令的路径参数被破坏。

**PowerShell 和 CMD 无此问题。**

**解决方式一（推荐）：写入 `.bashrc` 永久生效**

```bash
echo 'export MSYS_NO_PATHCONV=1' >> ~/.bashrc
source ~/.bashrc
```

**解决方式二：每次命令前加前缀**

```bash
MSYS_NO_PATHCONV=1 ziniao-cli api /superbrowser/rest/v1/erp/store/create \
  --data '{"storeData":[{"name":"新店铺"}]}'
```

## 安全规则

- **API Key 是静态敏感凭证**：不得主动索要完整 Key。不得在回复、终端输出或错误信息中展示完整 Key
- **禁止把完整 API Key 写入命令行参数、用户日常 Shell 历史、脚本、截图、录屏、聊天消息、日志或 Git**。用户已把 Key 发在对话里，不视为 Agent 主动泄露
- 不要向用户索要 API Key，也不要代用户写入 Key。登录失效时请用户在 WorkBuddy 里重新连接
- **写入/删除操作前必须确认用户意图**
- `high-risk-write` 操作（department delete、staff remove）会要求交互式确认，可用 `--yes` 跳过
- 建议先用 `--dry-run` 预览危险请求

## 重要行为规则

- **ZClaw 本地接口必须通过 ziniao-cli 调用**：调用紫鸟浏览器本地接口（store/page/zclaw 命令）时，必须使用本技能体系中的 ziniao-cli 能力，不要使用 ziniao-assistant 技能自行调用 ZClaw Bridge。
- **店铺列表优先使用本地接口**：如果用户要求获取店铺列表，应优先使用 `store list` 快捷命令（走本地 ZClaw Bridge），因为普通成员没有服务端 `account list` 接口权限。成员类型可通过 `ziniao-cli config show` 结果中的 `isBoss` 字段判断。
- **ZClaw 认证失败排查**：连接完成后，如果 ZClaw 接口仍返回 API Key 认证失败，提醒用户前往紫鸟开放平台 https://open.ziniao.com 查看自己的用户应用里「终端管理」是否已绑定当前终端识别码（识别码在紫鸟浏览器设置中查看）。
