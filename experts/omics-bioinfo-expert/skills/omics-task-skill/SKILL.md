---
name: omics-task-skill
description: "组学平台 CLI 通用操作助手，完成登录配置、列应用、发起 WDL/Nextflow 任务、查询状态、debug 排查。"
---

# Omics Task Skill (v4.2)

> 通过 `omics-platform-cli` 操作腾讯健康组学平台。所有命令拼接走 `scripts/omics_cli.py`，
> 统一参数与输出格式。**SKILL 的能力范围严格遵循 CONTRACT.md 白名单；任何越界都视为越权。**

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用 CONTRACT.md 白名单内的命令：

```
login   whoami   config(show/set/clear)   list(*)   run   status   debug   quota   cos(upload/ls)
```

### 严令禁止

1. **严禁编造其他命令**——`app list` / `app list-public` / `app templates` / `app file *` / `import` 等已废弃，调用必失败。
2. **严禁直接调用 omics 后端 HTTP API**（CommonAppService / RunService 等）、SQL、文件系统写入等任何旁路通道。
3. **严禁"导入公共应用"作为独立动作执行**——导入是 `run --public-app` 的内部步骤，必须随 run 一起发生。
4. **form B 必须显式传 `--app-type WDL` 或 `--app-type NEXTFLOW`**，不可省略。
5. **form D 禁止使用 `--update`**——form D 每次自动新建应用，CLI 运行时会强制拒绝。
6. **form D 不需要任何本地 COS 工具**——服务端直接从 COS 读源码，SKILL 不要引导用户安装 coscli/mc/aws 等第三方工具。`omics cos upload` 是官方内置上传命令，不依赖任何第三方工具。
7. **C 端体验用户每次 `omics run` 前必须强制执行配额检查**——在进入二次确认前先调 `omics quota`，配额为 0 时禁止继续，不受用户指令影响。
8. **`omics cos upload` / `omics cos ls` 由 CLI 内置实现**——无需安装任何第三方工具，通过预签名 PUT URL 直接上传，SKILL 可安全引导用户使用。

### run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须按 §4.2 模板完成二次确认：

1. 拼出完整命令字符串（含所有 flag）
2. 输出参数摘要表（形态 / 应用 / 项目 / 环境 / 输入 / NF 版本 / output-dir 等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复（y / yes / 确认 / 继续 / 是 / 执行 / OK）才调用
5. 用户拒绝（n / no / 取消）→ 终止；模糊回复（嗯 / 好 / 可以）→ 再次明确询问
6. 用户追加修改 → 回到 1 重拼

### 其他命令的确认要求

| 命令 | 是否需要确认 |
|------|-------------|
| `whoami` / `status` / `debug` / `list *` / `config show` / `quota` / `cos ls` | 免确认（只读 / 本地操作） |
| `run` | **必须二次确认** |
| `login` | SKILL 主动调用，无需额外确认 |
| `config set` | 每次写入前向用户展示最终配置摘要，确认后执行 |
| `config clear` | 需一次用户确认（破坏性操作） |
| `cos upload` | 展示上传文件列表 + 目标路径，确认后执行 |

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义 | SKILL 处理 |
|--------|------|-----------|
| `0` | 成功 | 解析 stdout |
| `1` | 业务错误 | 把 stderr 转述给用户；配置缺失时进入 Step 2 |
| `2` | 鉴权失败 | 进入 Step 1（SKILL 主动调用 `omics login`） |
| `FileNotFoundError` | CLI 未安装 | 进入 Step -1（安装引导） |

---

## Step -1：CLI 存在性检查（最先执行）

> **强制读取**：[references/omics-cli-setup.md §Step -1 和 §A](references/omics-cli-setup.md)
>
> 进入本步骤前，必须先使用 Read 工具读取上述文档对应章节，然后按文档流程执行。

任何业务命令之前，SKILL 必须先确认本机已安装 `omics-platform-cli`：

```bash
python3 scripts/omics_cli.py version
```

- exit 0 → CLI 已就绪，进入 Step 0
- `FileNotFoundError` / `command not found` / stderr 出现"未找到 'omics' 命令" → CLI 未安装，进入安装引导

**安装引导（按 references/omics-cli-setup.md §A 执行）**：

使用 `AskUserQuestion` 工具询问安装方式（自动安装 / 手动安装），按用户选择执行对应路径。安装完成后使用完整路径验证：

```bash
~/.local/bin/omics version   # macOS / Linux
```

---

## Step 0：鉴权与配置双重预检（每次启动必做）

> **强制读取**：[references/omics-cli-setup.md §D](references/omics-cli-setup.md)
>
> 进入本步骤前，必须先使用 Read 工具读取上述文档对应章节，然后按文档流程执行。

### Step 0.1：whoami

```bash
python3 scripts/omics_cli.py whoami
```

- exit 0 → 解析用户类型（B 端 / C 端）→ 进入 Step 0.2
- exit 2 → 进入 Step 1（Login）

### Step 0.2：config show

```bash
python3 scripts/omics_cli.py config show -o json
```

- exit 0 + 所有字段非空（Region / ProjectId / EnvironmentId / CosBucketName）→ 全部就绪，复述配置摘要后：
  - B 端用户 → 直接进入业务流程
  - C 端用户 → 进入 Step 0.3 配额首检
  > 当前配置：地域 `{Region}`，项目 `{ProjectName}（{ProjectId}）`，环境 `{EnvironmentName}（{EnvironmentId}）`，COS 桶 `{CosBucketName}`。
- exit 1 或字段有空值 → 进入 Step 2（配置引导）

### Step 0.3：C 端体验用户配额首检（仅 C 端）

> **触发条件**：Step 0.2 配置验证通过且用户类型为 C 端体验用户。
>
> **强制读取**：[references/omics-cli-setup.md §D-Step 0.3](references/omics-cli-setup.md)
>
> 每次 SKILL 启动，登录+配置就绪后必须执行一次。不得跳过，不受用户指令影响。

```bash
python3 scripts/omics_cli.py quota -o json
```

按返回字段 `remain_days` 和 `run_remain_limit` 判断：

| 场景 | 条件 | 行为 |
|------|------|------|
| 试用期已到期 | `remain_days == 0` | **阻断**：展示到期提示 + 开通链接，终止流程 |
| 今日次数已用完 | `run_remain_limit == 0` 且 `remain_days > 0` | **阻断**：展示用完提示，终止流程 |
| 临近到期 | `remain_days <= 3` 且 `run_remain_limit > 0` | **提示**：展示剩余天数和次数，继续流程 |
| 正常 | `remain_days > 3` 且 `run_remain_limit > 0` | 简短展示剩余次数，继续流程 |

详细话术见 [references/omics-cli-setup.md §D-Step 0.3](references/omics-cli-setup.md)。

---

## Step 1：登录授权（鉴权失败时）

> **强制读取**：[references/omics-cli-setup.md §B](references/omics-cli-setup.md)
>
> 进入本步骤前，必须先使用 Read 工具读取上述文档对应章节，然后按文档流程执行。

SKILL **主动调用** `omics login`，拉起浏览器完成授权：

```bash
python3 scripts/omics_cli.py login
```

提示用户：
```
已为您打开浏览器登录授权页，请在浏览器中点击「确认授权」完成登录。
授权完成后系统将自动继续。（等待中...最长 120 秒）
```

登录完成后轮询验证（最多 3 次，间隔 2s）：

```bash
python3 scripts/omics_cli.py whoami
```

- exit 0 → 登录成功，解析用户类型（B 端 / C 端）→ 进入 Step 0.2
- exit 2 仍未登录 → 3 次后提示用户确认浏览器是否已授权，可回复「重试」重新发起

**注意**：`omics login` 会打开本地浏览器，仅适用于用户本机场景。远程/容器/SSH 环境无法接收 localhost 回调，告知用户在有浏览器的本地机器执行。

---

## Step 2：配置引导（config 缺失或字段不全时）

> **强制读取**：[references/omics-cli-setup.md §C](references/omics-cli-setup.md)
>
> 进入本步骤前，必须先使用 Read 工具读取上述文档对应章节，然后按文档流程执行。
> B 端用户 → §C-B；C 端用户 → §C-C

按 `whoami` 输出的用户类型分流：

| 用户类型 | 识别条件 | 配置流程 |
|---------|---------|---------|
| **C 端体验用户** | `Role == "trial_user"` 且 `Capabilities` 含 `"misc:trial"` | §C-C：静默配置，地域固定 ap-guangzhou，环境固定 `env-b65ys9kj`，桶固定 `trial-user-1323714374`，项目取第一条 |
| **B 端正式用户** | 其他情况 | §C-B：完整引导（地域→项目→环境→COS桶，全程 AskUserQuestion 选项卡） |

**所有选择环节必须使用 `AskUserQuestion` 工具**，禁止纯文字让用户输入命令或编号。

配置完成后向用户确认摘要并继续业务流程（C 端随后执行 Step 0.3 配额首检）。

---

## 命令意图映射表（v7 · 完整命令边界）

| 用户说 | CLI 命令 | 场景 |
|--------|---------|------|
| 「我没装 CLI」| → 进入 Step -1（安装引导） | Step -1 |
| 「我登录了吗 / 当前账号是谁」| `omics whoami` | Step 0.1 |
| 「没登录 / session 过期」| → SKILL 主动调 `omics login` | Step 1 |
| 「现在是哪个项目和环境」| `omics config show -o json` | Step 0.2 |
| 「配置项目/切环境」| → SKILL 引导完整配置流程（Step 2） | Step 2 |
| 「清掉本地配置」| `omics config clear` | — |
| 「我的配额还剩多少」（C 端）| `omics quota -o json` | — |
| 「有哪些地域可选」| `omics list region -o json` | Step 2 |
| 「有哪些项目」| `omics list project -o json` | Step 2 |
| 「有哪些运行环境」| `omics list env --region <r> -o json` | Step 2 |
| 「有哪些 COS 桶可选」| `omics list cos-bucket -o json` | Step 2 |
| 「有哪些缓存卷」| `omics list volume -o json` | run 前 |
| 「平台有哪些公共应用」| `omics list public-apps [-o json]` | §3.1 |
| 「按 WGS 分类看公共应用」| `omics list public-apps --tag WGS -o json` | §3.1 |
| 「展开这个公共应用合集」| `omics list public-apps --parent-app <合集AppId> -o json` | §3.1.1 |
| 「项目里有哪些应用」| `omics list apps [-o json]` | §3.2 |
| 「这个应用有哪些版本」| `omics list versions --app <appId> -o json` | §3.4 |
| 「这个应用有哪些运行参数模板」| `omics list templates --app <appId> -o json` | §3.5 |
| 「跑这个本地 WDL」（B端）| `omics run --wdl <p> --name <n> [--input <p>] [--output-dir <cos>]` | §4.A（B端可用，C端不支持） |
| 「改了 WDL 再跑一次」（B端）| `omics run --wdl <p> --name <n> --update <appId> [--release-name <v>]` | §4.A（B端可用，C端不支持） |
| 「跑公共应用 X，命名为 Y」| `omics run --public-app <AppId> --public-app-name Y --app-type WDL\|NEXTFLOW` | §4.B |
| 「跑我项目里那个应用」| `omics run --app <ApplicationId> [--version <v>] [--template <t>]` | §4.C |
| 「用 COS 上的 NF 跑任务」（B端）| `omics run --nf <cos-path> --name <n> --nf-version <v>` | §4.D（B端可用，C端不支持） |
| 「看任务进度」| `omics status -o json` | §5 |
| 「rg-xxx 跑完了吗」| `omics status <rgId> -o json` | §5 |
| 「rg-xxx 哪些子任务挂了」| `omics debug <rgId> -o json` | §6.1 |
| 「这个失败子任务为啥挂的」| `omics debug --run <runUuid> -o json` | §6.2 |
| 「钻下 plan-xxx 的 stderr」| `omics debug --run <runUuid> --job <jobId> -o json` | §6.3 |
| 「帮我把本地文件上传到 COS」| `omics cos upload <local-path> [--prefix <prefix>]` | §7.1 |
| 「看 COS 上有哪些文件」| `omics cos ls [--prefix <prefix>] [-r]` | §7.2 |

---

## Step 3：查询类（只读）

### 3.1 公共应用：`omics list public-apps`（按 AppTag 分组）

```bash
# 默认查全部，按 AppTag 分组
python3 scripts/omics_cli.py list public-apps -o json

# 按业务标签精确过滤
python3 scripts/omics_cli.py list public-apps --tag WGS -o json

# 二级类型过滤叠加在 tag 之上
python3 scripts/omics_cli.py list public-apps --tag RNA-seq --type NEXTFLOW -o json

# 关键词搜索
python3 scripts/omics_cli.py list public-apps --keyword sentieon -o json
```

**JSON 顶层结构**：

```json
{
  "Tags": ["WGS", "RNA-seq", "未分类"],
  "TotalApps": 6,
  "Groups": [
    { "Tag": "WGS", "Count": 3, "Apps": [{"AppId", "AppName", "AppType", "AppGroupType", "AppDesc", "NextflowVersion", "AppTags"}, ...] }
  ]
}
```

**关键字段**：
- `AppId`：用于 `omics run --public-app <AppId>`
- `AppType`：`WDL` / `NEXTFLOW`（form B 必须用此值填 `--app-type`）
- `AppGroupType`：`APP_COLLECTION` 表示合集，**不能直接 run**（见 §3.1.1）
- `NextflowVersion[]`：NEXTFLOW 应用的引擎候选版本；**B端** form B 时让用户从此列表选取；**C端** 运行参数由 CLI 自动获取，无需用户指定

#### 3.1.1 合集（AppGroupType=APP_COLLECTION）的处理（必读）

返回结果中若 `AppGroupType == "APP_COLLECTION"`：

> 你选的 `<AppName>（<AppId>）` 是一个**合集**（包含多个子应用），不能直接运行。
> 我可以帮你展开看看里面有哪些子应用，要展开吗？

展开后：

```bash
python3 scripts/omics_cli.py list public-apps --parent-app <合集AppId> -o json
```

由用户挑一个子应用 AppId，再走 `run --public-app <子应用AppId>` 流程。

### 3.2 项目内应用：`omics list apps`

```bash
python3 scripts/omics_cli.py list apps -o json
python3 scripts/omics_cli.py list apps --type WDL -o json
```

固定走 config 项目，**不支持** `-p` 切项目。

JSON 关键字段：`ApplicationId / Name / Type / Entrypoint / VersionCount / CreateTime / NextflowVersion`

- **NEXTFLOW 类型应用**的 `NextflowVersion` 字段：**B端** form C 运行 NF 应用时必须从此字段获取版本号；**C端** 运行参数由 CLI 自动获取，无需用户指定版本
- WDL 类型应用的 `NextflowVersion` 为空

### 3.3 应用版本列表：`omics list versions`

```bash
python3 scripts/omics_cli.py list versions --app app-xxxx -o json
python3 scripts/omics_cli.py list versions --app app-xxxx --type RELEASE -o json
```

**JSON 关键字段**：
- `Type`：`RELEASE`（已发布）/ `HISTORY`（保存快照）
- `ApplicationVersionId`：传给 `omics run --version <Id>` 指定该版本运行（**B端专用**；C端无需指定版本）
- `Name`：仅 RELEASE 有有意义的版本名

### 3.4 应用运行参数模板列表：`omics list templates`

```bash
python3 scripts/omics_cli.py list templates --app app-xxxx -o json
python3 scripts/omics_cli.py list templates --app app-xxxx --version <verId> --with-content -o json
```

**JSON 关键字段**：
- `InputTemplateId`：传给 `omics run --template <Id>`（**B端专用**；C端由 CLI 自动获取运行参数，无需使用模板）
- `ContentValid`：`false` 表示模板不可用，必须从候选清单剔除

### 3.5 参数合并模式（统一）

所有形态下 `omics run` 内部按 `final = baseline + override` 合并参数：

```text
baseline（WDL Default 值）
    + override（用户 --input JSON / --template 服务端模板 / form B 自动取第一个模板）
    = finalParsed
        ├── 必填全有值 ✅ → RunApplication.Input
        └── 缺失/类型错 ❌ → PARAM_MERGE_FAILED（结构化报错）
```

> **C端说明**：C端 form B / form C 运行时，CLI 内部通过 `GetRunApplicationTrialUserConfig` 自动获取运行参数，SKILL 不向用户询问任何运行参数，直接拼最简命令发起运行。

**PARAM_MERGE_FAILED 关键字段**（`-o json` 时，仅 B端场景）：
- `Report.MissingRequired[]` / `TypeErrors[]` / `ExtraFields[]`
- `PartialSkeleton`：CLI 已拼好的"可保存即用"JSON
- `Hint[]`：下一步重跑命令模板

**典型话术**（B端）：
> 还有 N 个必填项缺值：
> - `<workflow>.input_bam`：File（必填）
> - `<workflow>.sample_id`：String（必填）
>
> 请把这些值告诉我，或给我一份本地 JSON 路径，我帮你通过 `--input` 传回去重跑。

---

## Step 4：运行类（统一入口）

### 4.0 运行形态与用户类型权限矩阵

`omics run` 支持四种互斥形态，B端/C端可用范围不同：

| 形态 | 触发 flag | B端正式用户 | C端体验用户 | 说明 |
|------|---------|:---------:|:---------:|------|
| **A** | `--wdl <path>` | ✅ | ❌ | 需本地 WDL 文件 + 写应用权限，C端账号无此权限 |
| **B** | `--public-app <AppId>` | ✅ | ✅ | 导入平台公共应用并运行 |
| **C** | `--app <ApplicationId>` | ✅ | ✅ | 运行项目内已有应用；C端仅能使用 form B 导入后产生的应用 |
| **D** | `--nf <cos-path>` | ✅ | ❌ | 需自行上传 NF 源码 + 写应用权限，C端账号无此权限 |

**C端用户触发 form A / form D 时（SKILL 层提前拦截，不调 CLI）**：

```
当前是体验版用户，本地 WDL（form A）/ COS Nextflow（form D）暂不支持。

体验版支持以下运行方式：
  • 运行平台公共应用（form B）：omics run --public-app <AppId>
  • 运行已导入的项目应用（form C）：omics run --app <ApplicationId>

如需了解可用的公共应用，我可以帮您查询：omics list public-apps
```

**C端用户 form C 背景说明**：C端账号无法在组学平台自行新建应用，`omics list apps` 返回的项目内应用均来源于之前通过 form B 导入的公共应用。如果列表为空，需先通过 form B 导入一个公共应用。

`omics run` 是**唯一运行入口**，按互斥四选一分流：

| flag | 形态 | 必备 |
|------|------|------|
| `--wdl <path>` | A：本地 WDL | `--name <n>`；可选 `--output-dir <cos://bucket/path>` |
| `--nf <cos-path>` | D：COS 上的 NF | `--name <n>`；`--nf-version` **必填**；**文件须预先通过 `omics cos upload` 上传（CLI 内置，无需第三方工具）**；cos-path 格式 `cos://bucket/prefix/`；服务端直接读 COS 源码 |
| `--public-app <AppId>` | B：公共应用 | `--app-type WDL\|NEXTFLOW` **必传**；合集子应用必传 `--public-app-name`；NEXTFLOW 必传 `--nf-version` |
| `--app <ApplicationId>` | C：项目内已有应用 | 可选 `--version` / `--template` / `--input` |

**NF 高级选项（NEXTFLOW 应用）**：

| flag | 说明 |
|------|------|
| `--nf-resume` | 断点续跑（跳过已成功步骤） |
| `--nf-config <path>` | 自定义 Nextflow config 文件路径 |
| `--nf-profile <name>` | Nextflow profile 名称（多个逗号分隔） |
| `--nf-report` | 生成 workflow execution report（HTML 格式，4 个报告） |
| `--volume-id <id>` | 指定非默认缓存卷（可通过 `list volume` 查询） |

**WDL 运行选项**：

| flag | 说明 |
|------|------|
| `--output-dir <cos://bucket/path>` | 指定结果输出目录（COS 路径）；传入后任务成功需引导用户查看（§5.结果引导） |

**版本管理 flag（全形态可用）**：

| flag | 说明 | 典型场景 |
|------|------|---------|
| `--version <VerId>` | 指定目标 ApplicationVersionId | form C 运行历史版本 |
| `--release-name <name>` | form A + `--update`：把新 HISTORY 版本发布为 RELEASE | 保存稳定版本 |
| `--release-desc <desc>` | 配合 `--release-name` 的版本描述 | — |

**形态 D（COS NF）说明**：

> - 用户须**先将 NF 文件上传到 COS**（通过 `omics cos upload`，CLI 内置实现，无需第三方工具，见 §7.1）
> - 指定 `--nf cos://bucket/prefix/` 后，CLI 把 CosSource（bucket + uri）传给服务端，**服务端直接从 COS 路径读取源码**，无需客户端下载或二次上传
> - `--nf-version` **必填**（从候选列表 `22.10.7` / `23.10.1` / `23.10.3` / `24.04.3` / `25.10.2` 中选取）
> - `--update` 与 `--nf` **互斥**，CLI 运行时强制拒绝；如需运行已有 NF 应用，改用 form C：`--app <appId>`
> - `--main` 可选（默认 `main.nf`）

### 4.1 完整流程（每次必走）

#### C 端用户 run 前强制配额检查

> ⚠️ C 端体验用户每次发起 `omics run` 前（进入二次确认之前），必须额外执行一次配额检查：
>
> ```bash
> python3 scripts/omics_cli.py quota -o json
> ```
>
> - `run_remain_limit == 0` → **禁止继续**，展示用完提示，不进入二次确认
> - `run_remain_limit > 0` → 继续进入二次确认
>
> 此检查不可被用户指令跳过。适用于 form B 和 form C（C端可用的全部运行形态）。

#### 4.1.A 形态 A（本地 WDL）· **B端可用 · C端不支持**

> ⚠️ **C端体验用户不可用**。检测到 C端用户请求此形态时，SKILL 直接给出提示（见 §4.0），不调用 CLI。

1. 首次新建：直接进入二次确认（§4.2）→ 发起
2. 失败后整改重试：必带 `--update <appId>`（复用上次创建的应用）
3. 若 `PARAM_MERGE_FAILED` → 收齐参数写 `run.json`，加 `--input` 重跑
4. 若需命名版本：加 `--release-name <v>` + `--release-desc <d>`

```bash
# 首次跑
python3 scripts/omics_cli.py run --wdl ./pipeline/ --name wgs-run1 -o json
# 带自定义输出目录
python3 scripts/omics_cli.py run --wdl ./pipeline/ --name wgs-run1 --output-dir cos://my-bucket/results/ -o json
# 整改重试
python3 scripts/omics_cli.py run --wdl ./fixed_pipeline/ --input ./run.json --name wgs-run1 --update app-xxxx -o json
# 整改重试 + 发布命名版本
python3 scripts/omics_cli.py run --wdl ./fixed_pipeline/ --input ./run.json --name wgs-run1 --update app-xxxx --release-name v1.1 -o json
```

#### 4.1.D 形态 D（COS NF）· **B端可用 · C端不支持**

> ⚠️ **C端体验用户不可用**。检测到 C端用户请求此形态时，SKILL 直接给出提示（见 §4.0），不调用 CLI。

**前置步骤（引导用户操作，见 §7.1）**：

SKILL 引导用户使用 `omics cos upload` 上传 NF 文件到 COS（CLI 内置实现，无需第三方工具）：

```bash
# 用户先把 NF 文件上传到 COS（SKILL 可帮用户执行此步骤，见 §7.1）
omics cos upload ./my-pipeline/ --prefix nf-apps/my-pipeline
```

上传成功后，CLI 会输出完整的 COS 路径，例如 `cos://my-bucket/nf-apps/my-pipeline/`。

**SKILL 调用**：

```bash
# --nf-version 必填；--name 必填
python3 scripts/omics_cli.py run \
  --nf cos://my-bucket/nf-apps/my-pipeline/ \
  --name my-nf-run \
  --nf-version 24.04.3 \
  -o json

# 带可选参数
python3 scripts/omics_cli.py run \
  --nf cos://my-bucket/nf-apps/my-pipeline/ \
  --name my-nf-run \
  --nf-version 24.04.3 \
  --input ./params.json \
  --nf-resume \
  --volume-id vol-xxx \
  -o json
```

**错误处理**：

| 错误码 | 原因 | 处理 |
|--------|------|------|
| `MISSING_NF_VERSION_COS` | 未传 `--nf-version` | 让用户从候选列表（22.10.7/23.10.1/23.10.3/24.04.3/25.10.2）选取 |
| `INVALID_COS_PATH` | COS 路径格式错误 | 修正为 `cos://bucket-name/prefix/` 格式 |
| `DUPLICATE_APP_NAME` | 应用同名冲突 | CLI 输出三选项（§4.4.1），让用户通过 `AskUserQuestion` 拍板 |

#### 4.1.B 形态 B（公共应用）· **B端 + C端均可用**

1. 先做合集检查（§3.1.1）
2. 决定 `--public-app-name`（§4.4 决策表）
3. 导入前同名预检（§4.4.1）
4. **C 端用户**：进入二次确认前先执行配额检查（§4.1 C 端规则）
5. 首次 run：
   - **B端**：CLI 自动取第一个 InputTemplate 作为运行参数基线，SKILL 可让用户通过 `--input` 自定义参数
   - **C端**：CLI 内部通过 `GetRunApplicationTrialUserConfig` 自动获取运行参数，**SKILL 不向用户询问任何运行参数**，直接拼最简命令发起：

```bash
# C端 form B 最简命令（不传 --input / --template / --nf-version，由 CLI 自动获取）
python3 scripts/omics_cli.py run \
  --public-app <AppId> \
  --public-app-name <name> \
  --app-type WDL|NEXTFLOW \
  --name <runName> \
  -o json

# B端 form B（WDL，可选传入自定义参数）
python3 scripts/omics_cli.py run \
  --public-app <AppId> \
  --public-app-name <name> \
  --app-type WDL \
  --name <runName> \
  -o json

# B端 form B（NEXTFLOW，必须从 NextflowVersion[] 选取版本）
python3 scripts/omics_cli.py run \
  --public-app <AppId> \
  --public-app-name <name> \
  --app-type NEXTFLOW \
  --nf-version <从应用NextflowVersion[]选取> \
  --name <runName> \
  -o json
```

6. 若 PARAM_MERGE_FAILED → CLI 自动回滚删除孤儿应用，直接用原 `--public-app <AppId>` 重试（**无需手动清理**）

#### 4.1.C 形态 C（项目内已有应用）· **B端 + C端均可用**

> **C端用户说明**：
> - C端账号无法在组学平台自行新建应用，`omics list apps` 列出的应用均来自之前 form B 导入的公共应用。若列表为空，需先通过 form B 导入公共应用。
> - **C端运行参数由 CLI 内部通过 `GetRunApplicationTrialUserConfig` 自动获取，SKILL 不向用户询问版本、模板或 `--input` 等参数，直接拼最简命令发起**。
> - C端 form C 运行前同样需要执行配额检查（§4.1 C端规则）。

```bash
# C端 form C 最简命令（不传 --version / --template / --input，由 CLI 自动获取）
python3 scripts/omics_cli.py run \
  --app <ApplicationId> \
  --name <runName> \
  -o json

# B端 form C（WDL 应用：拍板版本+模板后运行，见 §4.5）
python3 scripts/omics_cli.py run \
  --app <ApplicationId> \
  --version <VerId> \
  --template <TemplateId> \
  --name <runName> \
  -o json

# B端 form C（NF 应用：--nf-version 从 list apps 的 NextflowVersion 字段取）
python3 scripts/omics_cli.py run \
  --app <ApplicationId> \
  --version <VerId> \
  --nf-version <从应用信息获取> \
  --input ./run.json \
  --name <runName> \
  -o json
```

### 4.2 二次确认（必经）

#### form A / form C 模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 本地 WDL (form A) / 项目内应用 (C)  │
  │ 应用        : <Name (Id)>                         │
  │ 项目        : <ProjectId (Name, Region)>  <- config│
  │ 环境        : <EnvironmentId (Name)>      <- config│
  │ 运行版本    : <VersionId (Type/Name)>             │
  │ 发布命名    : <release-name 或 "不发布(HISTORY)">  │
  │ 运行参数    : 模板 <TemplateId (Name)> / 本地 JSON │
  │ NF 版本     : <从应用信息获取 / WDL 应用无需>      │
  │ 输出目录    : <output-dir 或 "未指定">             │
  │ 关键参数摘要:                                      │
  │   - sample_id = NA12878                           │
  │   - input_bam = cos://bucket/sample.bam           │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --app app-xxxx --version ver-aaaa \
            --template tmpl-aaaa --name run-1 -o json

确认无误请回复「确认 / 继续 / y」；如需修改请告诉我改什么。
```

#### form D 模板（COS NF）

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : COS Nextflow (form D)               │
  │ COS 路径    : cos://my-bucket/nf-apps/my-pipe/    │
  │ 应用名      : <name>                              │
  │ NF 版本     : 24.04.3                             │
  │ 入口文件    : main.nf（默认）                     │
  │ 运行参数    : <./params.json 或 "无">             │
  │ 项目        : <ProjectId (Name, Region)>  <- config│
  │ 环境        : <EnvironmentId (Name)>      <- config│
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --nf cos://my-bucket/nf-apps/my-pipe/ \
            --name my-nf-run --nf-version 24.04.3 -o json

确认无误请回复「确认 / 继续 / y」；如需修改请告诉我改什么。
```

#### form B 模板（公共应用）

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用 (form B)                   │
  │ 公共应用    : Sentieon-Germline (cm-aaa-bbb)      │
  │ AppType     : WDL                                 │
  │ 导入后命名  : my-sentieon                         │
  │ 项目        : prj-yyy (..., ap-guangzhou) <- config│
  │ 环境        : env-zzz (...)               <- config│
  │ 参数模板    : 自动取该应用第一个 InputTemplate     │
  │ NF 版本     : -- (WDL 应用无需)                   │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --public-app cm-aaa-bbb --public-app-name my-sentieon \
            --app-type WDL --name run-1 -o json

确认无误请回复「确认 / 继续 / y」；如需自定义参数请告诉我。
```

#### 用户回复识别

| 用户回复 | SKILL 行为 |
|---------|-----------|
| `y` / `yes` / `确认` / `继续` / `OK` / `是` / `执行` / `开始跑` | 调用 `cli.execute(...)` |
| `n` / `no` / `取消` / `等等` / `先别` | 终止流程，等待用户进一步指示 |
| 任何含修改意图的句子（"改下 X" / "把 Y 换成 Z"）| 解析修改意图 → 重拼命令 → 重走确认 |
| 模糊回复（"嗯" / "好" / "可以" / "试试"）| **不算肯定** → 再次明确询问"是否执行 y/N？" |

### 4.3 形态 A/D 的整改重试

形态 A 失败会保留 `ApplicationId`，用 `--update <appId>` 复用，不重复 CreateApplication。

#### 4.3.1 失败位置矩阵

| 失败位置 | CLI 报错关键字 | 用户要修的 | 重跑命令 |
|---------|-------------|---------|---------|
| ValidateApplication 不通过（WDL 语法/语义）| `WDL Validate 未通过` | 本地 WDL | `run --wdl <new> --input <p> --name <n> --update <appId>` |
| 参数模板校验失败 | `PARAM_MERGE_FAILED` | 本地 JSON | `run --wdl <p> --input <new.json> --name <n> --update <appId>` |
| 环境/默认卷问题 | `环境 X 不可用` / `未绑定默认缓存卷` | 重新 `omics config set` 或控制台配卷 | 修复后整条命令重跑 |
| COS 路径格式无效（form D）| `INVALID_COS_PATH` | 修正为 `cos://bucket/prefix/` 格式 | 修正后重跑 |
| 缺少 `--nf-version`（form D）| `MISSING_NF_VERSION_COS` | 从候选列表选取版本 | 加 `--nf-version <版本>` 重跑 |
| form C NF 缺 `--nf-version` | `MISSING_NF_VERSION_RUN` | 从应用信息 `NextflowVersion` 字段取版本 | `run --app <appId> --nf-version <ver> --input ./run.json` |
| form C NF 缺 `--input` | `MISSING_INPUT_NF_RUN` | 准备运行参数 JSON | `run --app <appId> --nf-version <ver> --input ./run.json` |

> 重要：**SKILL 不要把多个修复合并成一次**。CLI 是流水线式中止，每次失败 → 让用户改一项 → 重跑一次。

#### 4.3.2 整改循环话术框架

```
第 N 次运行失败：<错误关键字>
错误位置: <Position 或字段路径>
错误内容: <原文转述>

整改指引：
  · WDL 语法/语义问题 → 修改本地 .wdl 文件，按 Position 定位
  · 参数 JSON 问题 → 修改本地 run.json
  · 环境/卷问题 → 重新 omics config set 或在控制台配置默认 Volume
  · form D COS 路径问题 → 修正路径格式

修复完告诉我，我会用同一个应用 ID（app-xxxx）+ 你的最新文件重跑。
```

### 4.4 形态 B：公共应用

**`--public-app-name` 决策规则**：

| 情形 | --public-app-name | 来源 |
|------|------------------|------|
| 用户明确指定了导入名 | **必传** | 用户原话 |
| 独立公共应用，用户没指定名 | **先做同名检查（§4.4.1）** | 检查通过后 CLI 用原名兜底 |
| **合集子应用**，用户没指定名 | **必传 + 同名检查** | `list public-apps --parent-app` 结果中的 `AppName` |

**`--nf-version` 决策规则**：

| 情形 | --nf-version |
|------|-------------|
| WDL 公共应用（form B）| **不传** |
| NEXTFLOW 公共应用（form B）| **必传**；来源：`list public-apps` 结果中该应用的 `NextflowVersion[]`，让用户挑 |
| NEXTFLOW 项目内应用（form C）| **必传**；来源：`list apps` 结果中该应用的 `NextflowVersion` 字段，**不用默认候选列表** |
| COS NF（form D）| **必传**；来源：默认候选列表（22.10.7/23.10.1/23.10.3/24.04.3/25.10.2），让用户选 |

#### 4.4.1 导入前同名检查（必经）

只要将走"用公共应用原名兜底"路径，必须先检查 config 项目里是否已有同名应用：

> CLI 内部在 `run --public-app` 时自动做同名预检，遇到同名会输出结构化 `DUPLICATE_APP_NAME` 错误，包含 `ConflictApplicationId` 和三个选项。

SKILL 遇到此错误时，使用 `AskUserQuestion` 展示三个选项：

```
Options:
  1. 取消操作（保留同名应用）
  2. 换一个新名字导入
  3. 使用已有同名应用（ConflictApplicationId）直接跑 form C
```

**SKILL 不可自动加后缀绕过冲突**，命名属用户治理空间。

**form B 孤儿应用自动回滚说明**：

> CLI 在 form B 导入成功但运行失败（如 PARAM_MERGE_FAILED）时，会**自动回滚删除**已导入的孤儿应用。
> SKILL 收到 PARAM_MERGE_FAILED 后，直接告知用户「导入的应用已自动清理，修改参数后可直接重新运行 `omics run --public-app <AppId>`」，无需引导用户手动删除。

### 4.5 版本+模板拍板流程（form C / form B 获取 appId 后）· **仅 B端**

> **C端用户不走此流程**：C端 form B / form C 的运行参数由 CLI 通过 `GetRunApplicationTrialUserConfig` 自动获取，无需版本和模板拍板。

B端 form C 运行 WDL/NF 应用前，必须让用户选择版本和模板：

```
① list versions --app <appId> -o json
   → 展示版本清单给用户（AskUserQuestion）
   → 记录 <selectedVersionId>

② list templates --app <appId> --version <selectedVersionId> --with-content -o json
   → 过滤 ContentValid=true 的模板
   → 展示候选模板给用户（AskUserQuestion）
   → 用户拍板：
     a) 选模板 → build_run(template_id=<TemplateId>)
     b) 用本地 JSON → build_run(input_json=<path>)
     c) 模板全不合适且无 override 需求 → 尝试 build_run（仅靠 baseline）

③ 进入二次确认（§4.2）→ 执行
```

### 4.3.5 版本管理

#### form A `--update` 触发的版本命名

```
用户："改了 WDL，再跑一次"（已知 app-xxxx 是上次创建的应用）
    ↓
SKILL 询问：这次更新要不要给新版本起个正式名字？
  a) 起个版本名（推荐用于稳定/里程碑代码）
  b) 不起名，作为 HISTORY 草稿
    ↓
用户给名字 → 加 --release-name <名> [--release-desc <描述>]
用户说"先存草稿" → 不加 --release-name，保持 HISTORY
    ↓
二次确认（§4.2）→ 调用 run
```

**版本命名约束**：
- 名字在 `(Uin, ApplicationId, ProjectId)` 维度内唯一；重名会 `ERROR_DUPLICATE_NAME`
- 发布失败不会回滚文件保存——CLI 会警告，用户可换名重试

#### Debug 重跑模式

诊断出参数/设置问题后重新发起：

```bash
# 修正参数重跑（走 RunApplication，非独立 RetryRuns 接口）
python3 scripts/omics_cli.py run --app <appId> --version <原VerId> --input ./fixed_run.json
```

若是应用代码/WDL/NF 逻辑 bug → 引导用户走 form A/D 的 `--update` 整改路径。

---

## Step 5：状态查询与结果引导

### 5.1 任务状态查询

```bash
# 列当前 config 项目下全部批次
python3 scripts/omics_cli.py status -o json

# 查指定批次下的子任务
python3 scripts/omics_cli.py status <runGroupId> -o json
```

**RunGroup Status 状态**：`RUNNING` / `SUCCEEDED` / `FAILED` / `CANCELLED`

### 5.2 运行结果引导（统一）

任务 `Status=SUCCEEDED` 后，按以下规则主动引导用户查看结果：

| 条件 | SKILL 行为 |
|------|-----------|
| `omics run` 入参**包含** `--output-dir <cos-path>` | 主动告知用户结果在 `<cos-path>`，提供查看命令和控制台链接 |
| `omics run` 入参**不包含** `--output-dir` | 引导用户前往平台控制台查看任务详情和输出文件 |
| NF 应用启用 `--nf-report` | debug 段 2 输出含 `WithReports`（4 个 HTML 报告 CosSignedUrl），主动告知用户 URL |

**结果引导话术示例**（有 output-dir 时）：

```
任务已成功完成（RunGroupId: rg-xxx）！

结果文件已写入您指定的 COS 路径：
  cos://my-bucket/results/wgs-run1/

查看方式：
  1. 在终端运行：omics cos ls cos://my-bucket/results/wgs-run1/
  2. 或登录组学平台任务详情页：
     https://omics.qq.com/platform/tasks
```

**结果引导话术示例**（无 output-dir 时）：

```
任务已成功完成（RunGroupId: rg-xxx）！

您可以前往组学平台查看任务详情和输出文件：
  https://omics.qq.com/platform/tasks

如需在终端查看 COS 上的输出，可以运行：
  omics cos ls --prefix <任务输出目录前缀>
```

---

## Step 6：debug 异步失败排查

### 6.1 段 1：批次级取证

```bash
python3 scripts/omics_cli.py debug <runGroupId> -o json
```

列出该批次下所有子任务，标出 Failed 的 `RunUuid`。段 1 输出包含 `AppType` 字段，用于后续分流诊断。

### 6.2 段 2：子任务现场

```bash
python3 scripts/omics_cli.py debug --run <runUuid> -o json
# NF 应用额外获取执行报告 URL
python3 scripts/omics_cli.py debug --run <runUuid> --with-reports -o json
```

输出按 `AppType` 分流：

**WDL / WDL_GRAPH 应用**：主战场是 `JobLogs[].Stderr` + `PodEvents`

**NEXTFLOW 应用**：主战场是 `NextflowLog` 末尾（CLI 自动截尾：头 8KB + 尾 56KB），同时参考 `JobLogs[].Stderr`
  - 若 `NextflowLog` 指向具体 task hash（如 `[a1/b2c3d4]`），在 `Calls[]` 里按 `WorkDir` 末段反查具体 `JobId`，再用段 3 钻取

**关键信号**：

- `OOMKilled` → 容器内存不足，引导用户调整 WDL 中的 `runtime.memory`
- `FailedMount` → COS/Volume 挂载失败，检查 COS 桶绑定或 Volume 配置
- `Command exited with ...` → 脚本运行时错误，看 `Stderr` 定位具体行

详细的错误模式知识库见 [references/runtime_error_kb.md](references/runtime_error_kb.md)。

**NF 应用 `--with-reports` 结果展示**：

若用户在 run 时指定了 `--nf-report`，段 2 的 `ReportUrls` 字段含 4 个 HTML 报告的 COS 签名 URL，SKILL 主动展示：

```
NF 执行报告（有效期约 1 小时）：
  - 执行报告：https://... （execution_report.html）
  - 时间线：https://...   （execution_timeline.html）
  - 跟踪：https://...     （execution_trace.txt）
  - DAG 图：https://...   （pipeline_dag.html）
```

### 6.3 段 3：按 JobId 过滤

```bash
python3 scripts/omics_cli.py debug --run <runUuid> --job <jobId> -o json
```

在段 2 的 Calls/JobLogs 中按 JobId 精确过滤，常用于 stderr 被截断时做针对性诊断。

**debug 不做的事（SKILL 不可越界）**：
- 不自动修改 WDL 的 `runtime.memory` / `runtime.disk`
- 不自动重跑（只取证，SKILL 报告诊断给用户，让用户决策修什么）
- 重跑方式见 §4.3.5 Debug 重跑模式

---

## Step 7：COS 文件操作（`omics cos`）

> `omics cos` 是 CLI 内置命令，**无需安装任何第三方工具**（coscli/mc/aws 等），
> 通过平台预签名 PUT URL 实现上传，通过平台 API 实现目录浏览。

### 7.1 上传文件到 COS：`omics cos upload`

```bash
# 上传单文件（使用 config 桶，默认前缀 uploads/）
python3 scripts/omics_cli.py cos upload ./data.fastq

# 上传目录（指定前缀，常用于 form D NF 文件准备）
python3 scripts/omics_cli.py cos upload ./nf-pipeline/ --prefix nf-apps/my-pipeline

# 上传到指定桶
python3 scripts/omics_cli.py cos upload ./sample.vcf --bucket my-bucket-123 --prefix uploads/vcf

# 预览模式（不实际上传，仅列出将上传的文件）
python3 scripts/omics_cli.py cos upload ./data/ --dry-run

# JSON 格式输出（含每个文件的上传结果）
python3 scripts/omics_cli.py cos upload ./data/ -o json
```

**参数说明**：

| flag | 说明 |
|------|------|
| `<local-path>` | 本地文件或目录路径（支持多个，目录自动递归，跳过隐藏文件/.git） |
| `--prefix <prefix>` | COS 对象前缀（默认 `uploads`） |
| `--bucket <name>` | 目标桶（缺省使用 config 配置桶；显式指定时校验是否已绑定到当前环境） |
| `--dry-run` | 预览模式，不实际执行 |
| `-o json` | JSON 格式输出（含每个文件的 LocalPath / COSPath / Error） |

**SKILL 引导上传的标准话术**：

```
即将上传以下内容到 COS：
  本地路径: ./nf-pipeline/
  目标桶: my-bucket-123（来自 config）
  COS 前缀: nf-apps/my-pipeline

确认上传吗？（y / 取消）
```

上传完成后告知用户完整 COS 路径（form D 场景下直接用于 `--nf` 参数）。

### 7.2 浏览 COS 文件：`omics cos ls`

```bash
# 列配置桶根目录
python3 scripts/omics_cli.py cos ls

# 列指定前缀
python3 scripts/omics_cli.py cos ls --prefix nf-apps/

# 递归列出全部内容
python3 scripts/omics_cli.py cos ls --prefix nf-apps/ -r

# 指定桶（根目录）
python3 scripts/omics_cli.py cos ls --bucket my-bucket-123

# cos:// 格式（从路径解析桶和前缀）
python3 scripts/omics_cli.py cos ls cos://my-bucket/data/
```

**参数说明**：

| flag | 说明 |
|------|------|
| `[cos://bucket/prefix]` | 可选位置参数，从 cos:// 路径解析桶和前缀 |
| `--prefix <prefix>` | 指定起始路径前缀 |
| `--bucket <name>` | 指定桶（缺省使用 config 配置桶） |
| `-r` / `--recursive` | 递归展开全部子目录 |
| `-o json` | JSON 格式输出 |

---

## C 端体验用户配额查询

```bash
python3 scripts/omics_cli.py quota -o json
```

返回字段：
- `run_limit`（每日上限）
- `run_remain_limit`（今日剩余）
- `days`（试用总天数）
- `remain_days`（剩余天数）

仅 C 端体验用户可用（CLI 内部先做身份校验，非 C 端直接报错退出）。

---

## 附录

### A. 参考文档

- [references/omics-cli-setup.md](references/omics-cli-setup.md) — CLI 安装/授权/配置共享规范（Step -1/0/1/2 + §C-C 固定值 env-b65ys9kj/trial-user-1323714374 + §D-Step 0.3 配额首检）
- [references/cli_commands.md](references/cli_commands.md) — CLI 命令详细参考（含 omics cos 命令）
- [references/runtime_error_kb.md](references/runtime_error_kb.md) — 运行时错误知识库
- [CONTRACT.md](CONTRACT.md) — CLI / SKILL 边界契约（v7）

### B. 生态定位

```
┌─────────────────────────────────────────────────────────────┐
│ omics-task-skill（本通用 SKILL）                              │
│   职责：支持所有形态（A/B/C/D）+ 完整配置引导 + 结果引导      │
│         + COS 文件操作（上传/浏览）+ C端配额管理              │
│   白名单：见 CONTRACT.md §1                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 专用应用 SKILL（如 fastp-skill / IgGM-skill 等）              │
│   职责：锁定特定公共应用/合集，提供一键运行                   │
│   当用户明确指定这些应用时，请改用对应专用 SKILL              │
└─────────────────────────────────────────────────────────────┘
```
