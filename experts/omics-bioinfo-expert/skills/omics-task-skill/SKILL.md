---
name: omics-task-skill
description:
  "腾讯健康组学平台(Omics) CLI 通用操作助手。通过 omics-platform-cli 完成：登录与配置、列公共应用与项目应用、发起 WDL / Nextflow 任务（本地 WDL、公共应用、项目内应用、COS 上的 NF 四种形态）、查询任务批次和子任务状态、debug 异步失败排查。本技能为通用入口，当用户明确指定专用应用（scBERT / IgGM / tFold / CD-GPT / ORI / scPROTEIN 等）时，请改用对应的专用 SKILL。触发词：Omics, omics, 组学平台, 健康组学, 腾讯健康组学, omics cli, omics-platform-cli, omics-cli, 跑 WDL, 跑 wdl, 跑 Nextflow, 跑 NF, 跑 nf, 跑流水线, 跑任务, 跑批次, 发起任务, 启动任务, 提交任务, 跑公共应用, 跑项目应用, 跑本地 WDL, 跑 COS 上的 NF, 列公共应用, 列项目应用, 列应用版本, 列参数模板, list public-apps, list apps, list versions, list templates, omics list, omics run, omics status, omics debug, 查任务进度, 查批次状态, 任务状态, 批次状态, RunGroup, rg-xxx, debug 任务, 任务失败排查, 看 stderr, 看为啥挂了, 钻取 plan-xxx, WGS, RNA-seq, sentieon, cromwell, 生信流程"
---

# Omics Task Skill (v2.0)

> 通过 `omics-platform-cli` 操作腾讯健康组学平台。所有命令拼接走 `scripts/omics_cli.py`，
> 统一参数与输出格式。**SKILL 的能力范围严格等于 CLI 7 条白名单命令；任何越界都视为越权。**

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用以下 **7 条** CLI 一级命令：

```
login   whoami   config   list   run   status   debug
```

### 🚫 严令禁止

1. **严禁编造其他命令**——例如 `app list` / `app list-public` / `app templates` / `app file *` /
   `project list` / `import` 等都已废弃，调用必失败。
2. **严禁直接调用 omics 后端 HTTP API**（CommonAppService._ / RunService._ / ImportApplication 等）、
   SQL、文件系统写入等任何旁路通道。
3. **严禁通过组合现有命令"模拟"出白名单外的语义**——例如不能把"导入公共应用"作为独立动作执行；
   导入是 `omics run --public-app` 的内部步骤，必须随 run 一起发生。
4. **`omics login` / `omics config set` 由用户在本机终端执行**，SKILL 永远不主动调（OAuth 浏览器
   回调 + 交互式输入只能在用户本机完成）。

### ✅ run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须按 §4.2 模板完成二次确认：

1. 拼出完整命令字符串（含所有 flag）
2. 输出参数摘要表（应用 / 项目 / 环境 / 输入 / NF 版本等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复（y / yes / 确认 / 继续 / 是 / 执行 / OK）才调用
5. 用户拒绝（n / no / 取消）→ 终止；模糊回复（嗯 / 好 / 可以）→ 再次明确询问
6. 用户追加修改 → 回到 1 重拼

### ✅ 其他命令的确认要求

| 命令                                                             | 是否需要确认              |
| ---------------------------------------------------------------- | ------------------------- |
| `whoami` / `status` / `debug` / `list *` / `config show / clear` | 免确认（只读 / 本地操作） |
| `run`                                                            | **必须**                  |
| `login` / `config set`                                           | 不调，引导用户本机执行    |

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义     | SKILL 处理                                                                                  |
| ------ | -------- | ------------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                                 |
| `1`    | 业务错误 | 把 stderr 转述给用户。如果是"未配置"错误，按下文 Step 2 引导用户去本机跑 `omics config set` |
| `2`    | 鉴权失败 | 按下文 Step 1 引导用户去本机跑 `omics login`，不要循环重试                                  |

stderr 中以 `❌` 开头的行为可读错误描述，可直接转述。

> 另外：`scripts/omics_cli.py` 启动时若在 `PATH` 与 `OMICS_CLI_PATH` 都找不到 `omics` 可执行文件，
> 会以 `FileNotFoundError` 退出（非 0/1/2 业务退出码），SKILL 必须按下文 **Step −1** 引导用户安装 CLI，
> **不要**自动尝试下载、不要 `pip/brew/curl` 替用户装。

---

## Step −1：CLI 存在性检查（**最先执行**）

任何业务命令之前，SKILL 必须先确认本机已安装 `omics-platform-cli`。
最简单的方式是直接尝试 `omics whoami` / `omics version`：

- 如果 `python3 scripts/omics_cli.py whoami` / `omics whoami` 抛出 `FileNotFoundError`、
  shell 提示 `command not found: omics`、Windows 提示 `'omics' 不是内部或外部命令`，
  或者 stderr 出现 `未找到 'omics' 命令` —— 都视为 **CLI 未安装**。
- 命中以上任一情况，立即给用户下面这段话并**终止流程**，等待用户安装完成回执：

> 检测到本机尚未安装 `omics-platform-cli`，无法继续。
>
> 请前往下载页，按页面提供的安装脚本和使用指南完成安装：
> https://cnb.cool/tencenthealthcareomics/omics-platform-cli
>
> 安装完成后回到我这里告诉我「已安装 / done」，我会验一次 `omics version` 再继续。

**强约束**：

- **绝不**在 SKILL 端用 `curl` / `wget` / `brew` / `pip` / `npm` 等任何方式自动下载或安装 CLI；
  也**不要**自行编写解压、加 PATH、导 `OMICS_CLI_PATH` 之类的操作步骤——下载页已提供官方的安装脚本和使用指南，按页面执行即可。
- **绝不**继续调用任何 `python3 scripts/omics_cli.py ...` 命令（CLI 不存在时这些命令必失败）。
- 用户回执「已安装」后，重新跑一次 `omics version` 确认通过后才进入 Step 0；
  若仍失败，仅需再次把下载页链接给用户，让其参照页面指南排查，不要替用户猜路径。

---

## Step 0：鉴权与配置双重检查（每次启动必做）

任何业务命令前必须先验证两个条件：

```
┌──────────────────────────┬──────────────────────────────┐
│ 检查项                   │ 命令 / 期望                  │
├──────────────────────────┼──────────────────────────────┤
│ 已登录                   │ omics whoami → exit 0        │
│ 已配置 region/proj/env   │ omics config show -o json    │
│                          │ → exit 0 且字段都不为空      │
└──────────────────────────┴──────────────────────────────┘
```

### Step 0.1：whoami

```bash
python3 scripts/omics_cli.py whoami
```

退出码 0 → 进入 Step 0.2；退出码 2 → 跳到 Step 1（登录引导）。

### Step 0.2：config show

```bash
python3 scripts/omics_cli.py config show -o json
```

判定：

- **退出码 0 + JSON 字段齐全**（Region/ProjectId/EnvironmentId 都不为空）→ 进入业务流程，
  **复述当前配置给用户**：
  > 当前配置：地域 `ap-guangzhou`，项目 `prj-xxx (xxx)`，环境 `env-yyy (yyy)`，COS Bucket `my-bucket`。如需切换请告诉我。
- **退出码 1（文件不存在 / 字段缺失）** → 跳到 Step 2（配置引导）。

---

## Step 1：登录引导（鉴权失败时使用）

**SKILL 不要自己调 `omics login`。** 一旦 `whoami` 返回退出码 2 或任何业务命令报"鉴权失败 / session 过期 / 401"，立即给用户下面这段话（按需润色）：

> 检测到当前会话的登录状态已失效或不存在。
>
> 请在你**本机的终端**中执行下面这条命令完成授权：
>
> ```bash
> omics login
> ```
>
> 完成后回到我这里告诉我「已登录」，我会继续后续操作。

**强约束**：

- 不要在 SKILL 端启动 `omics login` 子进程
- 不要循环 `whoami` 等待用户登录
- 不要给用户复制授权 URL 让其在远程粘贴（OAuth 回调地址 `localhost:18000` 必须落到用户本机的 CLI 进程上）

收到用户「已登录 / done」类肯定答复后，重新跑一次 `omics whoami` 确认 → exit 0 才进入 Step 0.2。

---

## Step 2：配置引导（config 缺失或字段不全时使用）

**SKILL 不要自己调 `omics config set`。** 它是**交互式**命令，会逐项提示输入 region/projectId/environmentId/bucketName，
SKILL 跑在远程 agent 里无法替用户输入；同时 SKILL 也不应猜测或编造这三个 ID。

一旦 `omics config show` 返回退出码 1，立即给用户下面这段话：

> 检测到本地尚未完成 region / projectId / environmentId 的配置。
>
> 请在你**本机的终端**中执行下面这条命令完成配置：
>
> ```bash
> omics config set
> ```
>
> CLI 会依次提示输入 **Region → ProjectId → EnvironmentId → COS BucketName**。
> COS BucketName 为**必填项**，CLI 会调用 DescribeAssociatedCosBuckets 校验该桶是否属于当前环境且地域匹配。
>
> 完成后回到我这里告诉我「已配置」，我会继续后续操作。

收到用户「已配置 / done」类肯定答复后，重新跑一次 `omics config show -o json` 确认 → exit 0 + 字段齐全才进入业务流程。

---

## 命令意图映射表（v4 · 严格对齐 7 命令）

| 用户说                                          | CLI 命令                                                                                                                 | 场景     |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------- |
| 「我没装 CLI / 提示 command not found」         | **告诉用户去 https://cnb.cool/tencenthealthcareomics/omics-platform-cli 下载安装**，SKILL 不调                           | Step −1  |
| 「我登录了吗 / 当前账号是谁」                   | `omics whoami`                                                                                                           | Step 0.1 |
| 「我没登录 / session 过期了」                   | **告诉用户在本机终端跑** `omics login`，SKILL 不调                                                                       | Step 1   |
| 「现在用的是哪个项目和环境」                    | `omics config show -o json`                                                                                              | Step 0.2 |
| 「配下默认项目 / 切到 xx 项目」                 | **告诉用户在本机终端跑** `omics config set`，SKILL 不调                                                                  | Step 2   |
| 「清掉本地配置」                                | `omics config clear`                                                                                                     | —        |
| 「平台有哪些公共应用」「按 WGS 分类看公共应用」 | `omics list public-apps [--tag <T>] [--type WDL\|NEXTFLOW] [--keyword <kw>] -o json`                                     | §3.1     |
| 「展开这个公共应用合集」                        | `omics list public-apps --parent-app <合集AppId> -o json`                                                                | §3.1.1   |
| 「项目里有哪些应用」「我有哪些 WDL 应用」       | `omics list apps [--type WDL\|NEXTFLOW] -o json`                                                                         | §3.2     |
| 「这个应用都有哪些版本」「列出版本」            | `omics list versions --app <appId> [--type RELEASE\|HISTORY] -o json`                                                    | §3.4     |
| 「这个应用有哪些运行参数模板」                  | `omics list templates --app <appId> [--version <verId>] [--with-content] -o json`                                        | §3.5     |
| 「跑这个本地 WDL」+ 路径                        | `omics run --wdl <p> --name <n> [--input <p>]`（CLI 直接尝试用 baseline 跑；缺啥以 PARAM_MERGE_FAILED 报错）             | §4.A     |
| 「校验失败了，我改了 WDL 再跑一次」             | `omics run --wdl <new> --input <p> --name <n> --update <appId> [--release-name <verName>]`                               | §4.A     |
| 「跑公共应用 X，导入后命名为 Y」                | `omics run --public-app <AppId> --public-app-name Y`（CLI 自动取第一个 InputTemplate 作为 override）                     | §4.B     |
| 「跑公共应用 X，但参数我自己改过」              | `omics run --public-app <AppId> --public-app-name Y --input ./run.json`（显式 override 覆盖自动模板）                    | §4.B     |
| 「跑这个 NF 公共应用 X」                        | `omics run --public-app <AppId> --public-app-name Y --nf-version <版本>`（版本从应用 `NextflowVersion[]` 获取）          | §4.B     |
| 「跑我项目里那个应用」                          | `omics run --app <ApplicationId> [--input <p>]`                                                                          | §4.C     |
| 「跑我项目里那个 NF 应用」                      | `omics run --app <ApplicationId> --nf-version <版本> --input <p>`（版本从应用 `NextflowVersion` 字段获取，不用默认列表） | §4.C     |
| 「用 COS 上的 NF 跑任务」+ COS 路径             | `omics run --nf <cos-path> --name <n> --nf-version <版本> [--cos-tool <tool>]`（版本从默认候选列表选取）                 | §4.D     |
| 「看任务进度」「查批次状态」                    | `omics status -o json`                                                                                                   | §5       |
| 「rg-xxx 跑完了吗 / 看子任务」                  | `omics status <rgId> -o json`                                                                                            | §5       |
| 「rg-xxx 哪些子任务挂了」                       | `omics debug <rgId> -o json`                                                                                             | §6.1     |
| 「这个失败子任务到底为啥挂的」                  | `omics debug --run <runUuid> -o json`                                                                                    | §6.2     |
| 「钻下 plan-xxx 这个作业的 stderr」             | `omics debug --run <runUuid> --job <jobId> -o json`                                                                      | §6.3     |

> ❌ 用户说「列出应用模板」「拷一份模板出来」「按文件精准 patch」等：v4 起这些独立动作**已废除**。
> 模板已内化到 `omics run` 内部链路（form B 自动取第一个 InputTemplate）；
> 多文件 WDL 整改改为只走 `omics run --wdl <目录> --update <appId>` 整目录覆盖，
> service 端冲突由 CLI 内部回退处理。

---

## Step 3：查询类（场景 1）

### 3.1 公共应用：`omics list public-apps`（按 AppTag 分组）

```bash
# 默认查询全部公共应用，按 AppTag 分组展示
python3 scripts/omics_cli.py list public-apps -o json

# 按业务标签精确过滤（推荐入口：用户先说"我要跑 WGS 类的"）
python3 scripts/omics_cli.py list public-apps --tag WGS -o json

# 二级类型过滤可叠加在 tag 之上
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
    { "Tag": "WGS", "Count": 3, "Apps": [ {AppId, AppName, AppType, AppGroupType, AppDesc, NextflowVersion, AppTags}, ... ] },
    { "Tag": "RNA-seq", "Count": 2, "Apps": [...] },
    { "Tag": "未分类", "Count": 1, "Apps": [...] }
  ]
}
```

**关键字段**（每个 App）：

- `AppId`：用于 `omics run --public-app <AppId>`
- `AppName` / `AppType` / `AppGroupType` / `AppDesc` / `NextflowVersion[]` / `AppTags[]`

**SKILL 转述给用户的建议形态**：按 Tag 分组列出，每组显示 1~3 个代表应用 + 总数；
让用户挑出感兴趣的 Tag 后再用 `--tag` 过滤拉详细清单。

#### 3.1.1 合集（AppGroupType=APP_COLLECTION）的处理（必读）

返回结果中若 `AppGroupType == "APP_COLLECTION"`：合集是多子应用打包，**不能直接 run**。

提醒话术示例：

> 你选的 `<AppName> (<AppId>)` 是一个**合集**（包含多个子应用），不能直接运行。
> 我可以帮你展开看看里面有哪些子应用，要展开吗？

得到肯定答复后展开：

```bash
python3 scripts/omics_cli.py list public-apps --parent-app <合集AppId> -o json
```

把展开后的子应用清单转述给用户，由用户挑一个具体的子应用 AppId，再走正常 `run --public-app <子应用AppId>` 流程。

> **重要：合集子应用导入路径** > `omics run --public-app <子应用AppId>` 会**直接把子应用 AppId 作为 `CommonAppUuid` 调 `ImportCommonApplication`**，
> 不需要也不应该传合集 AppId。
> service 端 `DescribeCommonApp` 默认强制 `f_parent_app_id=''` 过滤，所以 CLI 单独探测元信息可能查不到子应用——这是正常现象。
> 如果导入失败提示\"AppId 不存在\"，**第一时间核对：传入的是不是合集自身 AppId**？应当传**子应用** AppId。

### 3.2 项目内应用：`omics list apps`

```bash
python3 scripts/omics_cli.py list apps -o json
python3 scripts/omics_cli.py list apps --type WDL -o json
```

固定走 config 项目，**不支持** `-p` 切项目；要切请重新让用户跑 `omics config set`。

JSON 关键字段：`ApplicationId / Name / Type / Entrypoint / VersionCount / CreateTime / NextflowVersion`。

- **NEXTFLOW 类型应用**的 `NextflowVersion` 字段非空，记录该应用使用的 NF 引擎版本；form C 运行 NF 应用时必须从此字段获取版本号，**不要使用默认候选列表**
- WDL 类型应用的 `NextflowVersion` 为空或不存在

**主要使用场景**：

1. 用户想跑 form C（项目内已有应用）时，帮其挑 ApplicationId
2. form B 导入公共应用前的同名预检（参见 §4.4.1）

### 3.4 应用版本列表：`omics list versions`（v6 新增）

```bash
# 列出该应用全部版本（HISTORY + RELEASE，按 sid 倒序）
python3 scripts/omics_cli.py list versions --app app-xxxx -o json

# 仅看正式发布版本
python3 scripts/omics_cli.py list versions --app app-xxxx --type RELEASE -o json
```

**JSON 输出**：

```json
{
  "ApplicationId": "app-xxxx",
  "TotalCount": 5,
  "Versions": [
    { "Type": "RELEASE", "ApplicationVersionId": "ver-yyyy", "Name": "v2.0",
      "Entrypoint": "main.wdl", "CreateTime": "2026-06-01 10:11:12",
      "CreatorName": "alice", ... },
    ...
  ]
}
```

**关键字段**：

- `Type`：`RELEASE`（已发布、有正式名）/ `HISTORY`（每次保存自动生成的快照）
- `ApplicationVersionId`：传给 `omics run --version <Id>` 即可指定该版本运行
- `Name`：仅 RELEASE 有有意义的版本名（如 `v1.0` / `2026-q2-stable`）
- `Entrypoint` / `CreateTime` / `CreatorName`：辅助识别版本来源

**主要使用场景**：

1. **form C 运行 WDL 应用前的版本确认（必经，§4.5 详述）**
2. form A `--update` 触发后，查询本次新生成的版本是否已发布命名
3. 排查"哪个版本最新 / 哪个发布过"等元信息

### 3.5 应用运行参数模板列表：`omics list templates`（v6.1 新增）

```bash
# 列出该应用的全部参数模板（默认列全部版本下的模板）
python3 scripts/omics_cli.py list templates --app app-xxxx -o json

# 仅看指定应用版本下的模板
python3 scripts/omics_cli.py list templates --app app-xxxx --version ver-yyyy -o json

# 附带每个模板的 Content（多一次接口调用，列表大时慎用）
python3 scripts/omics_cli.py list templates --app app-xxxx --with-content -o json
```

**JSON 输出**：

```json
{
  "ApplicationId": "app-xxxx",
  "VersionFilter": "",
  "TotalCount": 3,
  "Templates": [
    {
      "InputTemplateId": "tmpl-aaaa",
      "Name": "default",
      "Description": "默认参数模板",
      "ApplicationVersionId": "0",
      "Creator": "alice",
      "Content": "{ \"foo\": \"bar\" }",
      "ContentValid": true
    },
    ...
  ]
}
```

**关键字段**：

- `InputTemplateId`：传给 `omics run --template <Id>` 即可使用该模板的内容作为运行参数 override
- `Name` / `Description`：辅助用户识别用途
- `ApplicationVersionId`：该模板绑定的版本号（"0" 表示未发布版本下的通用模板）
- `Content` / `ContentValid`（仅 `--with-content` 时返回）：**ContentValid=false 表示该模板不可用**（Content 为空 / 不是合法 JSON），SKILL 必须从候选清单中剔除

**主要使用场景（v6.1 强制流程）**：

1. **form B / form C 运行前的模板拍板**：详见 §4.5
2. 用户问"这个应用预设了哪些参数模板"
3. 排查"为什么模板内容运行报错"——加 `--with-content` 看实际 JSON

### 3.3 应用的运行参数：合并模式（v3 起统一 · v4 边界继承）

> **核心理念**：CLI 不再有"参数清单 / JSON 骨架模式"，也不再有用户层的 `app templates` 命令。
> 任何形态下 `omics run` 都会**直接进入流水线**，内部按 `final = baseline + override` 合并参数 JSON，
> 校验通过则发起任务，校验失败则**结构化报错**告诉 SKILL 缺哪些 key、要什么类型，
> 由 SKILL 引导用户补值后通过 `--input` 传回 override 重跑。

```text
                ValidateApplication.Inputs[].Default
                          │
                          ▼
               ┌──────────────────────┐
               │  baseline (map)      │   ← WDL 中显式声明的默认值
               └──────────┬───────────┘
                          │ Merge（浅覆盖）
               ┌──────────▼───────────┐
               │  override (map)      │   ← form B：自动 InputTemplate
               │                      │     form A/C：用户 --input 本地 JSON
               │                      │     都没传：override 为空
               └──────────┬───────────┘
                          ▼
               ┌──────────────────────┐
               │  finalParsed         │
               │  ├─ 必填全有值？ ✅ → RunApplication.Input
               │  └─ 缺失 / 类型错？❌ → PARAM_MERGE_FAILED
               └──────────────────────┘
```

**对 SKILL 的含义**：

| 场景                                                                       | SKILL 行为                                                                                                                                              |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `omics run` 直接 exit 0 + 输出 RunGroupId                                  | 一切顺利，转述结果给用户即可                                                                                                                            |
| stderr 出现 `❌ 参数模板校验失败` 或 JSON 输出 `Error: PARAM_MERGE_FAILED` | 解析其中的 `Report.MissingRequired / TypeErrors / ExtraFields`，把缺失字段及类型告诉用户；用户给值后 SKILL 写入本地 `run.json` 再 `--input <path>` 重跑 |

**JSON 报错的关键字段**（`-o json` 时）：

- `Error`：固定为 `"PARAM_MERGE_FAILED"`
- `ApplicationId` / `WorkflowName`：定位上下文
- `Specs[]`：每项 `{ Name, Optional, TypeName, Default }`
- `Baseline` / `UserOverride` / `FinalParsed`：合并各阶段快照
- `Report.MissingRequired[]` / `EmptyRequired[]` / `ExtraFields[]` / `TypeErrors[]`
- `PartialSkeleton`：CLI 已拼好的"可保存即用"的 JSON
- `Hint[]`：CLI 给的下一步重跑命令模板

**典型话术**：

> 跑这次任务时 CLI 已经把 WDL 的默认值和模板拼好，但还有 N 个必填项缺值：
>
> - `<workflow>.input_bam`：File（必填）
> - `<workflow>.sample_id`：String（必填）
>
> 请把这些值告诉我，或者直接给我一份本地 JSON 路径，我帮你按 `--input` 传回去重跑。

---

## Step 4：运行类（场景 2，统一入口）

`omics run` 是**唯一运行入口**，按互斥四选一分流（v5 新增形态 D）：

| flag                    | 形态              | 必备                                                                                                                                                                                                                         |
| ----------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--wdl <path>`          | A：本地 WDL       | `--name <n>`                                                                                                                                                                                                                 |
| `--nf <cos-path>`       | D：COS 上的 NF    | `--name <n>`；cos-path 格式：`cos://bucket-name/prefix/`；`--nf-version` **必填**（从默认候选列表 `22.10.7` / `23.10.1` / `23.10.3` / `24.04.3` / `25.10.2` 中选取）；`--cos-tool <tool>` 可选（默认 auto 自动检测可用工具） |
| `--public-app <AppId>`  | B：公共应用       | **合集子应用必传 `--public-app-name <newName>`**；独立公共应用可省                                                                                                                                                           |
| `--app <ApplicationId>` | C：项目内已有应用 | —                                                                                                                                                                                                                            |

**版本管理 flag（v5 新增，全形态可用）**：

| flag                | 说明                               | 典型场景                                     |
| ------------------- | ---------------------------------- | -------------------------------------------- |
| `--version <VerId>` | 指定目标 ApplicationVersionId 运行 | form C 运行历史版本；form A/D 回溯已保存版本 |

> **形态 D COS NF 说明（v5.1 更新）**：
>
> - 用户需**先将 Nextflow 管道文件上传到 COS**（可通过 coscli / mc / aws 等任意工具），再通过 `--nf cos://bucket/prefix/` 指定路径运行
> - CLI 内部自动从 COS 同步文件到本地临时目录，再通过 SaveApplicationFiles 上传到平台
> - `--nf-version` **必填**（用户必须从默认候选列表 `22.10.7` / `23.10.1` / `23.10.3` / `24.04.3` / `25.10.2` 中选取一个版本；SKILL 不要替用户随便选）
> - `--cos-tool <tool>` **可选**，支持：`auto`（默认，自动检测）| `coscli` | `mc` | `aws` | `coscmd` | `python_cos`（内置降级）
> - 跳过 ValidateApplication 步骤（NF 无服务端校验）
> - 每次保存自动生成新版本，可通过 `--app + --version` 回溯
> - 前置依赖：至少安装一种 COS 同步工具；未安装任何工具时 CLI 会引导用户安装 coscli
>
> **★ 形态 C 运行 NF 应用额外要求（v5.1 更新）★**：
>
> - 当通过 `--app <appId>` 运行的应用类型为 NEXTFLOW 时：
>   - **必须** 通过 `--nf-version` 指定引擎版本，**版本来源为该应用自身的信息**（`list apps` 输出中该应用的 `NextflowVersion` 字段），**不要使用默认候选列表**
>   - **必须** 通过 `--input` 提供运行参数 JSON（NF 无 ValidateApplication baseline，无法自动生成默认值）

> **公共应用导入命名规则**：
> service 端 `ImportCommonApplication` 直接把 `CommonAppNewName` 作为新建应用的 Name，留空建出空字符串名应用。
> CLI 已加兜底：未传 `--public-app-name` 时尝试从公共应用列表读取原名作为命名。
> 但 service 端 `DescribeCommonApp` 默认 `f_parent_app_id=''` 过滤，**合集子应用查不到元信息** → CLI 此时**直接报错**，要求 SKILL 显式传 `--public-app-name`。

### 4.1 完整流程（每次必走）

#### 4.1.A 形态 A（本地 WDL）/ 4.1.D 形态 D（COS NF）/ 4.1.C 形态 C（项目内应用）

1. **首次新建（form A/D 不带 --update / form C 第一次见这个应用）**：
   - 先按 §4.5 走"版本+模板拍板"流程（form A 首次新建无版本可选，form C 强制；form D 首次新建无版本但需挑 NF 引擎版本）；
2. **二次确认**（必经，模板见 §4.2，包含运行版本和模板信息）；
3. **直接尝试发起**：
   ```bash
   omics run --wdl ... --name ...                                        # A：仅靠 baseline
   omics run --wdl ... --input /tmp/run.json --name ... --update <appId> # A：用户 override
   omics run --nf cos://my-bucket/nf-apps/my-pipe/ --name my-nf-run --nf-version 24.04.3   # D：COS NF（--nf-version 必填，auto 检测 COS 工具）
   omics run --nf cos://my-bucket/nf-apps/my-pipe/ --name my-nf-run --nf-version 23.10.1 --cos-tool mc  # D：显式使用 MinIO Client
   omics run --app <ApplicationId> --version <VerId> --template <TemplateId>             # C：WDL 选定版本+模板（v6.1 推荐）
   omics run --app <ApplicationId> --version <VerId> --input /tmp/run.json               # C：WDL 选定版本+本地 JSON
   omics run --app <ApplicationId> --nf-version <版本> --version <VerId> --template <TemplateId>  # C：NF 应用（必带 --nf-version）
   ```
   **A/D 形态首次失败后必须带 `--update`**：CLI 已经为你创建了空白应用并上传了文件；这次直接复用，否则会重复建空壳。
   **D 形态前置条件**：用户需先通过 COS 工具（coscli/mc/aws 等）将 NF 文件上传到 COS，再指定 `--nf` COS 路径运行。未安装任何工具时 CLI 会引导安装 coscli。**`--nf-version` 必填**，用户须从默认候选列表（22.10.7/23.10.1/23.10.3/24.04.3/25.10.2）中选取。
   **C 形态运行前必经**：`list versions` + `list templates` 让用户拍板（详见 §4.5）。
4. **若 CLI 报 `PARAM_MERGE_FAILED`**：按 §3.3 解析报告，转述给用户、收齐参数，写入 `/tmp/run.json` 后用相同命令加 `--input /tmp/run.json` 重跑。
5. **若 CLI 报 `INVALID_INPUT_TEMPLATE`**（指定的 `--template` 拉取失败/Content 为空/非 JSON）：回到 list templates 让用户重选，或改用 `--input <path>`。
6. **若 CLI 报其它流水线错误**（Validate / 环境 / 卷）：按 §4.3 / §4.6 处置。

#### 4.1.B 形态 B（公共应用，模板拍板路径）

1. **形态 B 必须先做合集检查**（§3.1.1）；
2. **决定 `--public-app-name`**（按 §4.4 决策表）；
3. **导入前同名预检**（§4.4.1）；
4. **首次 run 完成导入**（CLI 自动 ImportCommonApplication，但**不传 `--template`**）：

   ```bash
   omics run --public-app <AppId> [--public-app-name <name>] [--name <runName>] -o json
   ```

   - 若运行成功 → 转述结果即可
   - 若 PARAM_MERGE_FAILED 或失败需要换模板 → 进入第 5 步

5. **拿到导入后的 ApplicationId 后，按 §4.5 走"版本+模板拍板"**：
   ```bash
   omics list versions  --app <import-app-id> -o json
   omics list templates --app <import-app-id> --with-content -o json
   ```
   把候选版本和候选模板呈现给用户拍板（按 §4.5 决策树）。
6. **拍板后用 form C 重发**：
   ```bash
   omics run --app <import-app-id> [--version <Ver>] --template <TemplateId> -o json
   # 或：用户改用本地 JSON
   omics run --app <import-app-id> [--version <Ver>] --input ./run.json -o json
   ```
7. **NF 公共应用额外要求**：必传 `--nf-version`（来源 §4.4 决策表）。

> **简化路径（兼容旧版）**：若用户只想"开箱即跑"且不在意模板/版本选取，可直接 `run --public-app <AppId>`，CLI 仍会兜底用第一个 InputTemplate 跑——但这条路径会被新版 SKILL 主动避免，因为它跳过了用户拍板。

### 4.2 二次确认（**必经**）

向用户汇总后等"确认/继续/OK/y"再执行。

#### form A / form C 模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 本地 WDL (form A) / 项目内应用 (C)  │
  │ 应用        : <Name (Id)>                         │
  │ 项目        : <ProjectId (Name, Region)>  ← config│
  │ 环境        : <EnvironmentId (Name)>      ← config│
  │ 运行版本    : <VersionId (Type/Name)> ← form C 必显示│
  │ 发布命名    : <release-name 或 "不发布(HISTORY)"> ← form A --update 时显示│
  │ 运行参数    : 模板 <TemplateId (Name)> ← form C 拍板的 InputTemplate│
  │              或 本地 JSON <path>                  │
  │              或 仅 baseline（无 override）         │
  │ NF 版本     : <从应用信息获取 / —（WDL 应用无需）> │
  │ 关键参数摘要:                                      │
  │   - sample_id   = NA12878                         │
  │   - input_bam   = cos://bucket/sample.bam         │
  │   - reference   = hg38                            │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --app app-xxxx --version ver-aaaaaaaa \
            --template tmpl-aaaa --name wgs-2026q2 -o json

确认无误请回复「确认 / 继续 / y」；如需修改请告诉我改什么。
```

#### form D 模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : COS Nextflow (form D)               │
  │ COS 路径    : cos://my-bucket/nf-apps/my-pipe/    │
  │ 应用名      : <name>                              │
  │ NF 版本     : 24.04.3（从默认候选列表选取）        │
  │ COS 工具    : auto（自动检测）                     │
  │ 项目        : <ProjectId (Name, Region)>  ← config│
  │ 环境        : <EnvironmentId (Name)>      ← config│
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --nf cos://my-bucket/nf-apps/my-pipe/ \
            --name my-nf-run --nf-version 24.04.3 -o json

确认无误请回复「确认 / 继续 / y」；如需修改请告诉我改什么。
```

#### form B 模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用 (form B，自动模板)         │
  │ 公共应用    : Sentieon-Germline (cm-aaa-bbb)     │
  │ AppType     : WDL                                │
  │ 导入后命名  : my-sentieon                        │
  │ 项目        : prj-yyy (..., ap-guangzhou) ← config│
  │ 环境        : env-zzz (...)               ← config│
  │ 参数模板    : 自动取该应用第一个 InputTemplate    │
  │ NF 版本     : —（WDL 应用无需）/ <版本>（从应用 NextflowVersion[] 选取）│
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --public-app cm-aaa-bbb --public-app-name my-sentieon \
            --name run-1 -o json

确认无误请回复「确认 / 继续 / y」；如需自定义参数请告诉我（可改走 --input 模式）。
```

#### 用户回复识别

| 用户回复                                                        | SKILL 行为                                 |
| --------------------------------------------------------------- | ------------------------------------------ |
| `y` / `yes` / `确认` / `继续` / `OK` / `是` / `执行` / `开始跑` | 调用 `cli.execute(...)`                    |
| `n` / `no` / `取消` / `等等` / `先别`                           | 终止流程，等待用户进一步指示               |
| 任何含修改意图的句子（"改下 X" / "把 Y 换成 Z"）                | 解析修改意图 → 重拼命令 → 重走确认         |
| 模糊回复（"嗯" / "好" / "可以" / "试试")                        | ⚠️ 不算肯定 → 再次明确询问"是否执行 y/N？" |

### 4.3 形态 A/D 的整改重试（场景 2.1.1 / 2.5）

形态 A（本地 WDL）和形态 D（COS NF）任意一步失败都会**保留 `--update <appId>` 复用**那个空白应用，不重复 CreateApplication。

#### 4.3.0 形态 D COS NF 特有失败处理

| 失败位置                                   | CLI 报错关键字                      | 用户要修的                                                        | 重跑命令                                                            |
| ------------------------------------------ | ----------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| 无可用 COS 同步工具（auto 模式全未检测到） | `本机未检测到可用的 COS 同步工具`   | 安装 coscli（推荐）或配置其他 COS 工具                            | 安装后重新执行当前命令；或用 `--cos-tool <已安装的工具名>` 显式指定 |
| COS 路径格式无效                           | `INVALID_COS_PATH`                  | 修正为 `cos://bucket-name/prefix/` 格式                           | 同上，`--nf` 换值                                                   |
| COS 同步文件失败                           | 工具相关错误（cosli/mc/aws/coscmd） | 检查所用工具的配置 / COS 路径是否存在                             | 同上；可尝试 `--cos-tool auto` 切换工具                             |
| NF 文件语法/配置错误                       | SaveApplicationFiles 运行时错误     | 修改 NF 文件后重新上传到 COS，再重跑                              | `run --nf <new-cos-path> --name <n> --update <appId>`               |
| 缺少 `--nf-version`                        | `MISSING_NF_VERSION_COS`            | 从默认候选列表（22.10.7/23.10.1/23.10.3/24.04.3/25.10.2）选取版本 | `run --nf <cos-path> --name <n> --nf-version <版本>`                |
| NF 引擎版本不存在/不兼容                   | service 端返回无效版本错误          | 从默认候选列表中另选一个有效 NF 版本                              | `run --nf <cos-path> --name <n> --nf-version <新版本>`              |

> **注意**：form D（`--nf` 新建）**必须**传 `--nf-version`，用户需从默认候选列表（22.10.7/23.10.1/23.10.3/24.04.3/25.10.2）中选取。

#### 4.3.0.1 形态 C 运行 NF 应用特有失败处理（v5.1 新增）

| 失败位置                | CLI 报错关键字           | 用户要修的                                                        | 重跑命令                                                                   |
| ----------------------- | ------------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 缺少 `--nf-version`     | `MISSING_NF_VERSION_RUN` | 从该应用信息中的 `NextflowVersion` 字段获取版本，不要使用默认列表 | `run --app <appId> --nf-version <从应用信息获取的版本> --input ./run.json` |
| 缺少 `--input` 参数模板 | `MISSING_INPUT_NF_RUN`   | 准备一份运行参数 JSON 文件                                        | `run --app <appId> --nf-version <ver> --input ./run.json`                  |

#### 4.3.1 失败位置矩阵（按流水线先后）

| 失败位置                                    | CLI 报错关键字                                         | 用户要修的                           | 重跑命令                                                                |
| ------------------------------------------- | ------------------------------------------------------ | ------------------------------------ | ----------------------------------------------------------------------- |
| ValidateApplication 不通过（WDL 语法/语义） | `WDL Validate 未通过` + `Position`/`Message`           | 本地 WDL                             | `run --wdl <new> --input <p> --name <n> --update <appId>`               |
| 多文件 WDL 中某子文件错                     | 同上，错误指向 import 语句                             | 改对应 .wdl 文件                     | 同上                                                                    |
| 参数模板校验失败                            | `参数模板校验失败：必填缺失 / 类型不匹配 / 未声明字段` | 本地 JSON                            | `run --wdl <p> --input <new.json> --name <n> --update <appId>`          |
| NF 文件保存失败                             | `上传 NF 文件失败` / `Result=CONFLICT`                 | 修改后重新上传到 COS 或本地修复      | 同上（form D 用 `--nf <cos-path> --nf-version <ver> --update <appId>`） |
| WDL 和 JSON 同时有问题                      | 先报 Validate，再报参数                                | **先修 WDL**，再修 JSON              | 一次只解决一类，每次都带 `--update`                                     |
| 环境/默认卷问题                             | `环境 X 不可用` / `环境 X 下未绑定默认缓存卷`          | 重新 `omics config set` 或控制台配卷 | 修复后整条命令重跑                                                      |

> 重要：**SKILL 不要把多个修复合并成一次**。CLI 是流水线式中止——上一关没过，下一关的错根本看不到。每次失败 → 让用户改一项 → 重跑一次。

#### 4.3.2 整改循环（推荐话术框架）

```
❌ 第 N 次运行失败：<错误关键字>
错误位置: <Position 或字段路径>
错误内容: <原文转述>

整改指引：
  • 如果是 WDL 语法/语义 问题 → 修改本地 .wdl 文件（多文件 WDL 通常错在某个被 import 的子文件，按 Position 找）
  • 如果是参数 JSON 问题 → 修改本地 run.json
  • 如果是环境/卷问题 → 重新 omics config set 或在控制台配置默认 Volume
  • 如果是 CONFLICT → 通常 CLI 已内部回退处理；若反复失败说明应用被并发修改，请等待后重试或换新名

修复完告诉我，我会用同一个应用 ID（app-xxxx）+ 你的最新文件重跑（CLI 用 --update 复用上次创建的空白应用，不会重复建空壳）。
```

> **v4 边界变化**：用户层不再有 `omics app file list/get/update` 命令。多文件 WDL 整改路径只剩**整目录覆盖**：
> 用户更新本地 WDL/NF 目录后，统一走 `omics run --wdl <整目录> --update <appId>`；service 端 SaveApplicationFiles 的 OriginalHash 校验
> 由 CLI 内部按"先 ListApplicationFiles 再 SaveApplicationFiles"流程自动处理，多次冲突的极端场景由 CLI 报清楚后请用户决策（等并发或重导入）。

### 4.3.5 版本管理（v5/v6 ）

#### 版本选择流程（form C 运行前 · v6 强制）

详见 §4.5。**核心规则**：form C 运行 WDL/NF 应用前必须先 `list versions` 让用户拍板版本，不要替用户默认选最新。

#### form A `--update` 触发的新版本命名（v6 强制）

```
用户："改了 WDL，再跑一次"（已知 app-xxxx 是上次新建的应用）
    ↓
SKILL：
  1) 询问用户："这次更新要不要给新版本起个正式名字（发布为 RELEASE）？"
     - 给出三档建议：
       a) 起个版本名（推荐用于稳定/里程碑代码）
       b) 不起名，作为 HISTORY 草稿（适合迭代中的代码）
       c) 列已有版本作参考：python3 scripts/omics_cli.py list versions --app app-xxxx -o json
  2) 拿到用户答复：
     - 用户给名字（如 v1.1 / 2026q2-fix）→ 加 --release-name <名字> [--release-desc <描述>]
     - 用户说"先存草稿" / "随便" / 没回应 → 不加 --release-name，保持 HISTORY
  3) 二次确认（§4.2）→ 调用 run
```

**版本命名约束**（CLI 已传递服务端校验）：

- 名字在 **(Uin, ApplicationId, ProjectId)** 维度内唯一；重名会 ERROR_DUPLICATE_NAME
- 发布失败不会回滚文件保存——CLI 会在 stderr 给出 `⚠️ 版本已生成，但发布命名失败` 警告，用户可换名重试或直接用返回的 HISTORY VersionId 运行
- 保持 HISTORY 状态时，用户后续仍可通过 `--version <historyVerId>` 指定该版本运行

```bash
# 整改重试 + 起版本名
python3 scripts/omics_cli.py run --wdl ./fixed_pipeline/ \
  --input ./run.json --name wgs-2026q2 \
  --update app-xxxx \
  --release-name v1.1 --release-desc "fix WGS pipeline OOM" \
  -o json

# 整改重试 + 保持 HISTORY 草稿（与 v5 行为一致）
python3 scripts/omics_cli.py run --wdl ./fixed_pipeline/ \
  --input ./run.json --name wgs-2026q2 --update app-xxxx -o json
```

**话术示例**：

> 这次改完 WDL 重跑，CLI 会保存为应用 `app-xxxx` 的一个新版本。要给它起个名字吗？
>
> - 推荐：如果这次改动是个里程碑（比如修了关键 bug 或上线版），给它起个名字（如 `v1.1` / `2026-06-fix-oom`），发布为正式 RELEASE 版，方便日后用 `--version v1.1` 引用
> - 不起名：保持为 HISTORY 草稿（CLI 会回显新生成的 ID，你可以随时通过 `--version <ID>` 指定该版本运行）
>
> 你想怎么处理？

#### 每次保存生成新版本

形态 A/D 中每次 `SaveApplicationFiles` 成功后：

```json
{
  "Result": "SUCCESS",
  "NewApplicationVersionId": "ver-20260609-xxxx"
}
```

- CLI 在结果中回显 `VersionId=ver-xxxx`
- 后续可通过 `--app <appId> --version ver-xxxx` 回溯到任意历史版本运行
- **版本不可变**：已保存的版本内容无法修改，修改只能创建新版本
- v6：传入 `--release-name <name>` 时，CLI 会基于该 HISTORY 版本调用 ReleaseApplicationVersion 服务端再生成一条 RELEASE（sid+1），同时回显发布结果

#### Debug 重跑模式（v5 新增）

当 debug 诊断出**运行设置或参数问题**（非应用代码 bug）时，SKILL 应采用以下"批次重跑"策略：

```
debug 取证完成 → 诊断出参数/设置问题
       │
       ▼
SKILL 构造修正后的输入 JSON（fixed_run.json）
  或修正运行选项（如 NF 配置 / WDL FailureMode）
       │
       ▼
重新发起 omics run（等效"用修复后参数跑同一个应用"，走 RunApplication 流程）：

  # 方式一：form C + 指定原版本（推荐）
  omics run --app <appId> --version <原VerId> --input ./fixed_run.json

  # 方式二：若需要换版本（如升级 WDL 后的新版本）
  omics run --app <appId> --version <新VerId> --input ./fixed_run.json

  （重跑 = 重新走 RunApplication，无需独立 RetryRuns 接口）
```

> **关键原则**：
>
> - Debug 重跑走的是 **`omics run --app`** 形态 C，**重新调用 RunApplication 流程**
> - 不需要独立的 RetryRuns / rerun 命令；修正参数后直接 `--app + --input + [可选 --version]` 即可
> - 若原问题是**应用代码/WDL/NF 逻辑 bug**，应引导用户走 form A/D 的 `--update` 整改路径
> - 仅当问题是**运行参数错误**时才直接用修正后的 `--input` 重跑

### 4.4 形态 B：公共应用（场景 2.2）

**`--public-app-name` 决策规则**：

| 情形                                                     | --public-app-name          | 来源                                                                   |
| -------------------------------------------------------- | -------------------------- | ---------------------------------------------------------------------- |
| 用户明确指定了导入名（如「叫 my-sentieon」）             | **必传**                   | 用户原话                                                               |
| 独立公共应用，用户没指定名                               | **先做同名检查（§4.4.1）** | 检查通过后走 CLI 原名兜底，否则要求用户给新名 / 确认复用               |
| **合集子应用**（来自 `--parent-app` 展开），用户没指定名 | **必传 + 同名检查**        | 从 `list public-apps --parent-app` JSON 结果中读出该子应用的 `AppName` |

**`--nf-version` 决策规则**：

| 情形                              | --nf-version                                                                                                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| WDL 公共应用（form B）            | **不传**；传了 CLI 会忽略并提示                                                                                                                                                |
| **NEXTFLOW 公共应用**（form B）   | **必传**；不传 CLI 会报 `MISSING_NF_VERSION` 并列出候选版本。版本来源：`list public-apps` 输出中该应用的 `NextflowVersion[]`，SKILL 让用户在候选列表里挑一个，不要替用户随便选 |
| **NEXTFLOW 项目内应用**（form C） | **必传**；版本来源：`list apps` 输出中该应用的 `NextflowVersion` 字段，**不要使用默认候选列表**                                                                                |
| **COS NF**（form D）              | **必传**；版本来源：默认候选列表（`22.10.7` / `23.10.1` / `23.10.3` / `24.04.3` / `25.10.2`），SKILL 让用户选取，不要替用户随便选                                              |

#### 4.4.1 导入前同名检查（**必经，禁止 SKILL 自作主张改名**）

只要 SKILL **没有**从用户那里拿到一个明确的 `--public-app-name`（即将走"用公共应用原名兜底"或"用合集子应用 AppName 兜底"路径），**必须先在 config 项目里检查同名应用**，避免：

- service 端 `CreateApplication` 因 Name 唯一约束直接报错；
- SKILL 自动加后缀（如 `xxx-1`、`xxx-cli`）替用户决策，污染应用列表。

**检查步骤**（即将作为 `--public-app-name` 的字符串记为 `<candidateName>`）：

```bash
# 拉项目内全部应用（按需加 --type 缩窄）
python3 scripts/omics_cli.py list apps -o json
```

在返回 JSON 中查找 `Name == <candidateName>` 的条目：

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | 不传 `--public-app-name`（独立应用走 CLI 兜底）/ 传 `<candidateName>`（合集子应用），按原流程发起 import    |
| **≥ 1 条命中** | **必须停下来**，把命中条目的 `ApplicationId / Name / Type / VersionCount / CreateTime` 列给用户，二选一询问 |

**话术模板（命中同名应用时）**：

> 项目里已经存在一个叫 `<candidateName>` 的应用：
>
> - ApplicationId：`app-xxxx`
> - Type：WDL，版本数：3，创建时间：2026-05-20 10:11
>
> 我不会自动改名，请你二选一：
>
> **A. 直接复用这个已存在的同名应用运行**
> → 我会跳过导入，直接用 `omics run --app app-xxxx ...` 发起任务。
> **B. 给一个新的导入名，比如 `<candidateName>-v2` / `my-sentieon-2026q2`**
> → 我会用你给的新名字导入这个公共应用。
>
> 你选哪个？或者直接告诉我新名字。

**用户回复后的执行分支**：

- 选 A（复用同名应用）→ **跳过 import**，直接走 form C：
  ```bash
  python3 scripts/omics_cli.py run --app <命中的 ApplicationId> [--input ...] [--name run-1] -o json
  ```
  ⚠️ 注意：复用前要让用户清楚"这是项目里已有的应用，可能不是最新公共应用版本"——如对版本敏感，建议改用方案 B 重新导入。
- 选 B（给新名）→ 用新名当 `--public-app-name` 重新走 form B 流程；**新名再做一遍同名检查**。
- 用户既不选 A 也不选 B、也不给名 → 不要发起 import，等待用户决策。

> **强约束**：SKILL 在任何情况下都**不要**自动给候选名加 `-1` / `-2` / `-cli` / 时间戳之类的后缀。命名是用户的项目治理空间，必须由用户拍板。

```bash
# 1) 先看 list public-apps 的结果，AppGroupType=APP_COLLECTION → 走 §3.1.1 合集展开

# 2) 决定 candidateName：用户原话 / 公共应用 AppName / 合集子应用 AppName

# 3) 同名检查
python3 scripts/omics_cli.py list apps -o json
#    在 Applications[] 中匹配 Name == candidateName

# 4a) 0 条命中 + 独立公共应用 + 用户没要求改名 → 不传 --public-app-name，CLI 用原名兜底
python3 scripts/omics_cli.py run --public-app cm-xxx --name run-1 -o json

# 4b) 0 条命中 + 用户要求叫 my-sentieon
python3 scripts/omics_cli.py run --public-app cm-xxx \
  --public-app-name my-sentieon --name run-1 -o json

# 4c) 0 条命中 + 合集子应用：先 list public-apps --parent-app 拿到 {AppId, AppName}
python3 scripts/omics_cli.py run --public-app <子应用AppId> \
  --public-app-name "<子应用 AppName>" \
  --name run-1 -o json

# 4d) ≥1 条命中 + 用户选 A（复用） → 走 form C，不再 import
python3 scripts/omics_cli.py run --app <命中的 ApplicationId> --name run-1 -o json

# 4e) ≥1 条命中 + 用户选 B（新名） → 用新名重新走 4b/4c

# 5) 用户要求改参数 → 显式传 --input 覆盖自动模板
python3 scripts/omics_cli.py run --public-app cm-xxx \
  --public-app-name my-sentieon --input ./run.json --name run-1 -o json

# 6) 该应用没有可用 InputTemplate（极少数）→ CLI 仅靠 baseline 跑；
#    若 baseline 不足以覆盖所有必填项，会以 PARAM_MERGE_FAILED 报错；
#    SKILL 按 §3.3 处理后用 `run --app <已导入的 ApplicationId> --input ./run.json` 重跑。
```

### 4.5 form C：项目内已有应用 / 版本与模板拍板（v6.1 强制流程）

**核心原则**（适用于 WDL 与 NF 应用）：

> **运行任何形态都必须由用户先确认"运行哪个版本 + 用哪个运行参数"**。CLI 不允许默认蒙混过关；
> SKILL 必须先 `list versions` + `list templates`，把候选清单原样呈现给用户拍板。

#### 第一步：版本拍板

**WDL 应用（任意 form）**：

```bash
python3 scripts/omics_cli.py list versions --app app-xxxx -o json
```

把 Versions[] 渲染给用户：标注每条 `Type / Name / ApplicationVersionId / CreateTime`；
默认推荐"最新 RELEASE"，候选还含"最新 HISTORY / 指定 ID"，由用户拍板后用 `--version <Id>` 传给 run。

**NF 应用——版本来源因 form 不同**：

| form                    | NF 引擎版本（`--nf-version`）来源                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| **B（公共应用）**       | `list public-apps` 输出中该应用的 `NextflowVersion[]` 字段，从中让用户选一个                        |
| **C（项目内 NF 应用）** | `list apps` 输出中该应用的 `NextflowVersion` 字段（导入时已固化），让用户在该字段提供的版本里选一个 |
| **D（COS 上的 NF）**    | 默认候选列表 `22.10.7 / 23.10.1 / 23.10.3 / 24.04.3 / 25.10.2`，由用户挑一个                        |

> **注意**：NF 应用的"应用版本（ApplicationVersionId）"和"NF 引擎版本（--nf-version）"是两件事；
> 应用版本同样要走 `list versions` 让用户拍板，引擎版本按上表来源选。

#### 第二步：运行参数模板拍板

```bash
# 推荐：拉模板列表（含每条的 Content + ContentValid）
python3 scripts/omics_cli.py list templates --app app-xxxx --with-content -o json
```

**拍板决策树**（SKILL 必走）：

```
list templates 返回 Templates[]
  │
  ├─ 0 条记录                          → 必须让用户提供本地 JSON：
  │                                       run --app <appId> --input ./run.json
  │                                       （NF 应用必须；WDL 应用至少有 baseline，
  │                                        若 baseline 已覆盖必填项也可省略 --input）
  │
  ├─ 多条记录，但全部 ContentValid=false → 同上：模板都不可用，要求 --input
  │
  └─ 至少 1 条 ContentValid=true       → 把候选 Templates 渲染给用户：
                                            (TemplateId / Name / Description / VersionId / Creator)
                                          标注 ContentValid=false 的模板"不可用"，
                                          引导用户从可用模板中拍板一个，再：
                                            run --app <appId> --version <Ver> --template <TemplateId>
                                          用户也可放弃模板改走 --input
```

**话术模板（多个可用模板时）**：

> 应用 `app-xxxx (my-pipeline)` 有 3 个可用运行参数模板：
>
> | TemplateId  | Name        | 说明                     | 绑定版本  |
> | ----------- | ----------- | ------------------------ | --------- |
> | `tmpl-aaaa` | default     | WGS hg38 默认参数        | 0（通用） |
> | `tmpl-bbbb` | hg19-legacy | hg19 旧版参考基因组      | ver-old   |
> | `tmpl-cccc` | mini-test   | 跑 1k reads 的小样本测试 | 0         |
>
> 你想用哪一个？或者直接给我一份本地参数 JSON（我可以帮你按 `--input` 传回去）？

#### 第三步：合并拍板结果发起运行

```bash
# WDL form C：用户选定版本 + 模板
python3 scripts/omics_cli.py run --app app-xxx \
  --version ver-aaaaaaaa --template tmpl-aaaa -o json

# WDL form C：用户选定版本，但模板都不合适 → 改用本地 JSON
python3 scripts/omics_cli.py run --app app-xxx \
  --version ver-aaaaaaaa --input ./run.json -o json

# NF form C：必须 --nf-version + (--template 或 --input)
python3 scripts/omics_cli.py run --app app-xxx \
  --version ver-bbbbbbbb --nf-version 23.10.1 --template tmpl-aaaa -o json
```

> **强约束**：
>
> - **WDL form C 运行前必须先 list versions + list templates**——不要跳过任何一步直接 run，否则用户无法感知"自己跑的是哪个版本 / 哪个模板"
> - **NF 应用同样适用**：需让用户拍板 ApplicationVersionId（应用版本）+ NF 引擎版本（--nf-version 来源因 form 异）+ 模板/输入 JSON
> - **不要替用户随便选**：除非用户明确说"用最新 / 用默认"才能自动选；任何模糊回复都要再次确认
> - **`--template` 与 `--input` 互斥**（CLI 强校验）：模板用服务端的 ID，本地 JSON 用文件路径，同传必报错

### 4.6 流水线失败提示（场景 2.3.5）

| 错误                                      | 处置建议                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| `应用 X 无可用版本`                       | 检查应用是否真的有版本，或重新 `omics run` 上传                                           |
| `WDL Validate 未通过`                     | 走 §4.3 整改重试                                                                          |
| `参数模板校验失败` / `PARAM_MERGE_FAILED` | 解析 `Report.MissingRequired / TypeErrors`，按 §3.3 引导用户给值后通过 `--input` 传回重跑 |
| `环境 X 不可用 / 不存在`                  | 提示用户重跑 `config set` 或去控制台检查                                                  |
| `环境 X 下未绑定默认缓存卷`               | 提示用户去控制台为该环境配置默认 Volume                                                   |
| `Result=CONFLICT` 反复出现                | CLI 内部已尝试回退；说明应用被并发修改，提示用户等待或换新名重新导入                      |
| `公共应用 X 是一个合集`                   | 用 `list public-apps --parent-app X` 展开，请用户挑子应用再跑                             |

---

## Step 5：状态查询（场景 3）

```bash
# 列批次（固定走 config 项目）
python3 scripts/omics_cli.py status -o json

# 列子任务
python3 scripts/omics_cli.py status rg-xxx -o json
```

> status 不支持跨项目查询。如需查别的项目，先重新 `omics config set`。

JSON 关键字段：

- 列批次：`RunGroupId / Name / Status / TotalRun / RunStatusCounts / ExecutionTime`
- 列子任务：`RunUuid / RunGroupId / UserDefinedId / Status / ExecutionTime / ErrorMessage`

紧凑总结：`最近 N 个批次：✅ 已完成 X / ❌ 已失败 Y / 🔄 运行中 Z`。

---

## Step 6：异步失败取证（场景 4 · v6 按 AppType 分流）

**触发条件**：`omics status` 看到子任务 `Status=Failed / Aborted / Error`，或用户问「rg-xxx 为啥挂了」之类。

**工具**：`omics debug` 三段式（CLI 端只取证，不做规则匹配；症状判断由 SKILL 模型对照 [`references/runtime_error_kb.md`](references/runtime_error_kb.md) 决定）。

**v6 关键变化**：CLI 按 `AppType` (`WDL` / `NEXTFLOW`) 差异化采集：

- WDL 分支：`Status` + `Calls` + `JobLogs[]`（stderr + PodEvents），不拉 `nextflow.log`，输出清空 `Status.Command/Meta`
- NF 分支：上述 + `NextflowLog`（顶层 `nextflow.log`，头 8KB + 尾 56KB 截尾），输出清空 `Status.Output`

### 6.1 段 1：列批次失败子任务

```bash
python3 scripts/omics_cli.py debug <runGroupId> -o json
```

**输出关键字段**：

- `TotalRuns / FailedCount`
- `FailedRunUuids[]`
- `Runs[]`：完整子任务列表，每项含 **`AppType`**（CLI 用 ApplicationId 反查 list apps 派生）

**SKILL 行为**：

1. `FailedCount == 0` → 告诉用户"该批次没有失败子任务，可能是运行中或已成功"
2. `FailedCount == 1` → 直接进入段 2
3. `FailedCount > 1` → 询问用户先看哪一个，或主动取前 1~2 个钻一遍找共性
4. 若批次内 `AppType` 混合（WDL + NF 都有），按 AppType 分组分别钻取，避免 checklist 串味

### 6.2 段 2：单子任务现场（按 AppType 分流）

```bash
python3 scripts/omics_cli.py debug --run <runUuid> -o json
# 可选 flag：
#   --with-stdout    钻取 Job 时同时拉 stdout（默认仅 stderr）
#   --with-trace     仅 NF；额外拉 execution_trace.txt
#   --with-reports   仅 NF；输出 4 个 HTML 报告 CosSignedUrl（不下载）
```

**输出关键字段**（详见 [`references/cli_commands.md` §8](references/cli_commands.md)）：

- `AppType`：`WDL` / `NEXTFLOW`（必读，决定下面看哪些字段）
- `Status`：顶层 RunMetadata
- `Calls[]` / `JobLogs[]`：失败 call 钻取（CLI 自动钻最多 8 个）
- **NF 专属**：`NextflowLog` / `NextflowLogTruncated` / `NextflowLogError`

**症状识别 checklist（按 AppType 分流）**：

#### WDL 分支

1. 看 `Status.ErrorMessage`（cromwell 抛错）
2. 逐个看 `JobLogs[].Stderr` 末尾（应用代码错）
3. 看 `JobLogs[].PodEvents`（OOMKilled / FailedScheduling / FailedMount / ImagePullBackOff）
4. 配合 `JobLogs[].Runtime`（cpu/memory/docker）判断资源是否合理
5. 对照 `runtime_error_kb.md` §1 / §3 / §4 决策

#### NF 分支

1. **首选** `NextflowLog` 末尾（NF 排障主战场，pipeline 编排级错误几乎都在这）
2. `Status.ErrorMessage`（NF 引擎抛的总结性错信）
3. `JobLogs[].Stderr` 末尾（单 process 内部应用错）
4. `JobLogs[].PodEvents`（与 WDL 共用）
5. 若 `NextflowLog` 提到具体 task hash（如 `[a1/b2c3d4]`） → 在 `Calls[]` 里按 `WorkDir` 末段反查 JobId，再用段 3 钻取
6. 对照 `runtime_error_kb.md` §2 / §3 / §4 决策

任一 checklist 都不命中 → 走兜底（§5），把现场原文贴给用户做透明分析。

### 6.3 段 3：精确钻取某个 Job

```bash
python3 scripts/omics_cli.py debug --run <runUuid> --job <jobId> -o json
```

输出与段 2 同结构，但 `Calls` / `JobLogs` 都按 `JobId` 过滤（NF 顶层 `NextflowLog` 仍输出，便于交叉查阅）。

### 6.4 关键守则（v6）

1. **CLI 端绝不主动调 `omics debug`** —— 用户问"为啥挂了"才用
2. **不要替用户做症状判断 + 自动改代码** —— 看到 `OOMKilled` 不要直接改 memory，要先告诉用户"目测内存不足，要把 memory 从 4G 调到 16G，确认吗"
3. **stderr / NextflowLog 是用户应用现场** —— 转述时**整段贴出来**，不要总结/二次加工
4. **不消费已被 CLI 清空的字段**：WDL 分支不要再读 `Status.Command/Meta`；NF 分支不要再读 `Status.Output`（前端汇总表也确认 NF 无 Output）
5. **多失败子任务时找共性** —— `FailedRunUuids` 里多个 Run 都失败在同一个 `CallName` → 标记"共性失败"，倾向应用 / 参数侧；分散失败 → 倾向环境 / 资源侧
6. **修复后统一走 `omics run` 重发**（按 AppType 分流，详见 `runtime_error_kb.md §7`）：
   - **WDL 代码 bug**：form A `--wdl ... --update <appId>`
   - **NF 代码 bug**：form D `--nf <new-cos-path> --name <n> --nf-version <版本>` **新建**（NF 不支持 --update）
   - **运行参数错**：form C `--app <appId> [--version <Ver>] --input <fixed.json>`
   - 重跑 = 重新调用 RunApplication 流程，无需独立 RetryRuns 接口

### 6.5 典型对话示例

#### 示例 A：WDL OOM

```
用户：rg-aa11bb22 跑挂了，帮我看看

SKILL：
（执行 debug 段 1）
python3 scripts/omics_cli.py debug rg-aa11bb22 -o json
→ TotalRuns=3, FailedCount=2, FailedRunUuids=[uuid-A, uuid-B]，Runs[].AppType=WDL

回应：该批次共 3 个子任务，2 个失败（WDL 应用）。先钻第一个 uuid-A 看看。

（执行 debug 段 2）
python3 scripts/omics_cli.py debug --run uuid-A -o json
→ AppType=WDL
→ JobLogs[0].Status=Failed, ErrorMessage="exited with return code 137"
→ JobLogs[0].PodEvents 含 Reason=OOMKilled
→ JobLogs[0].Runtime: {"cpu":4,"memory":"4G"}

回应（命中 runtime_error_kb §3.1）：
❌ 子任务 uuid-A 因内存不足被 K8s 杀掉（OOMKilled）。
当前 runtime.memory = 4G。建议改 WDL 中的 `runtime { memory: "16G" }`，
再 `omics run --wdl <整目录> --update <appId> --input <p>` 重跑。要继续吗？
```

#### 示例 B：NF process OOM

```
用户：rg-cc33dd44 跑挂了

SKILL：
（执行 debug 段 1）
→ TotalRuns=1, FailedCount=1, Runs[0].AppType=NEXTFLOW

（执行 debug 段 2）
python3 scripts/omics_cli.py debug --run uuid-X -o json
→ AppType=NEXTFLOW, NextflowLogTruncated=true
→ NextflowLog 末尾："Process `call_variants` terminated with code 137"
→ JobLogs[0].PodEvents: Reason=OOMKilled, Count=2
→ JobLogs[0].Runtime: {"cpu":8,"memory":"8G"}

回应（命中 runtime_error_kb §3.1 + §2.1）：
❌ NF process call_variants 内存不足被 K8s 杀掉（OOMKilled）。
当前 process memory = 8G，建议在 nextflow.config 把该 process 调到 32G 后**重新上传 COS**，
再 `omics run --nf <new-cos-path> --name xxx --nf-version 24.04.3` 新建任务（NF 不支持 --update）。要继续吗？
```

#### 示例 C：NF 参数缺失

```
（执行 debug 段 2）
→ AppType=NEXTFLOW
→ NextflowLog 末尾："ERROR ~ Required parameter `samplesheet` not specified"
→ JobLogs[] 为空（NF 引擎在 process 启动前就挂了）

回应（命中 runtime_error_kb §2.2）：
❌ NF 引擎报参数缺失：Required parameter `samplesheet` not specified。
检查 input JSON 里是否给了 samplesheet 字段；修复后用
`omics run --app <NFappId> --nf-version <版本> --input <fixed.json>` 重跑（form C，复用应用，不必重传 COS）。
```

---

## 典型会话场景

### 场景 A0：用户没装 CLI

1. 任意命令报 `FileNotFoundError` / `command not found: omics` / `未找到 'omics' 命令` →
   **告知用户去 https://cnb.cool/tencenthealthcareomics/omics-platform-cli 下载并安装**，SKILL 不自动装；
2. 等用户回执「已安装」→ 跑 `omics version` 验证 → 通过后进入场景 A。

### 场景 A：用户首次使用

1. `whoami` → 退出 2 → **告知用户去本机终端跑** `omics login`，等用户回执「已登录」
2. 重新 `whoami` ✓ → 跑 `config show` → 退出 1 → **告知用户去本机终端跑** `omics config set`，等用户回执「已配置」
3. 重新 `config show` ✓ → 进入业务流程

### 场景 B：跑公共应用（含合集分流，**默认自动模板**）

1. `whoami` ✓ + `config show` ✓ → 复述当前配置
2. 用户："跑公共应用 sentieon_germline"
3. `list public-apps --keyword sentieon -o json` → 拿候选清单
4. **检查 `AppGroupType`**：
   - 若 `APP_COLLECTION` → 提醒用户这是合集，询问是否展开
     - 同意 → `list public-apps --parent-app <合集AppId> -o json` → 让用户**挑一个具体的子应用 AppId**；记录子应用的 `AppName`
     - 拒绝 → 终止
   - 若不是合集 → 直接用该 AppId（同时记录 `AppName` 备用）
5. **决定 `--public-app-name`**（参考 §4.4 决策表）
6. **导入前同名检查（§4.4.1）**：
   - 执行 `list apps -o json`，匹配 `Name == <candidateName>`
   - 0 条命中 → 通过
   - ≥1 条命中 → 停下，请用户选「复用」或「新名」
7. **二次确认**（按 §4.2 form B 模板）
8. **一步直达运行**：
   ```bash
   run --public-app <选定的 AppId> [--public-app-name <按 §4.4 决策>] [--name run-1] -o json
   ```
9. 解析 `RunGroupId` → 提示 `omics status <rgId>`

### 场景 C：本地 WDL 整改重试

1. `run --wdl ... --name ...`（仅靠 baseline 跑）→ 若必填项不全 CLI 报 `PARAM_MERGE_FAILED`
2. SKILL 把缺失参数列表转述给用户，收齐后写入 `/tmp/run.json`，二次确认后：
   `run --wdl ... --input /tmp/run.json --name ... --update <appId>`
3. 如果是 WDL Validate 失败 → CLI stderr 给出 `app-xxxx` → 转述错误位置/消息
4. 等用户更新 WDL → `run --wdl <new> --input ... --name ... --update <appId>`

### 场景 D：用户想切项目

1. 用户："换到 prj-yyy 项目"
2. SKILL **告知用户去本机终端跑** `omics config set`
3. 等用户回执「已配置」→ `config show -o json` 复述新配置后继续业务

### 场景 E：业务命令报鉴权失败

1. 任何业务命令 exit 2 → SKILL 不重试
2. **告知用户去本机终端跑** `omics login` → 等用户回执
3. 重新跑原命令一次

---

## 高级用法

详细参数与状态枚举：[references/cli_commands.md](references/cli_commands.md)。
症状识别知识库：[references/runtime_error_kb.md](references/runtime_error_kb.md)。
边界契约：[CONTRACT.md](CONTRACT.md)。

## 脚本 API 参考

`scripts/omics_cli.py` 也可作为 Python 模块导入：

```python
from scripts.omics_cli import OmicsCLI

cli = OmicsCLI()

# ✅ 仅做检查类命令；whoami/config show 失败由 SKILL 引导用户去本机执行 login / config set
cli.execute(cli.build_whoami())
cli.execute(cli.build_config_show(output="json"))
cli.execute(cli.build_config_clear())                  # 仅在用户明确要求清配置时

# ❌ 禁止：build_config_set 已从 wrapper 删除；login 也不应由 SKILL 自动执行

# 公共应用（按 Tag 分组）
cli.execute(cli.build_list_public_apps(output="json"))
cli.execute(cli.build_list_public_apps(tag="WGS", output="json"))
cli.execute(cli.build_list_public_apps(tag="RNA-seq", app_type="NEXTFLOW", output="json"))
cli.execute(cli.build_list_public_apps(keyword="sentieon", output="json"))
cli.execute(cli.build_list_public_apps(parent_app="cm-collection-xxx", output="json"))

# 项目内应用（form C 挑 ApplicationId / form B 同名预检）
cli.execute(cli.build_list_apps(app_type="WDL", output="json"))

# v6：列指定应用的版本（form C 运行前必经；form A --update 后可查最新版本）
cli.execute(cli.build_list_versions(app="app-xxxx", output="json"))
cli.execute(cli.build_list_versions(app="app-xxxx", version_type="RELEASE", output="json"))

# v6.1：列指定应用的运行参数模板（form B/C 运行前必经，让用户拍板用哪个）
cli.execute(cli.build_list_templates(app="app-xxxx", output="json"))
cli.execute(cli.build_list_templates(app="app-xxxx", with_content=True, output="json"))

# 唯一 run 入口（四种形态；调用前必须完成二次确认！）
# form A / form C（WDL）：不传 input_json → CLI 仅靠 baseline 跑；缺啥以 PARAM_MERGE_FAILED 报错
cli.execute(cli.build_run(wdl="./hello.wdl", name="hello", output="json"))
cli.execute(cli.build_run(app="app-xxx", output="json"))

# form C + NF 项目内应用：必传 nf_version（版本从应用信息获取）+ input_json
cli.execute(cli.build_run(app="app-xxx", nf_version="23.10.1",
                          input_json="./run.json", output="json"))

# form B：默认自动取第一个 InputTemplate 作为 override
cli.execute(cli.build_run(public_app="cm-xxx", public_app_name="my-app",
                          name="run-1", output="json"))

# form B + NF 公共应用：必传 nf_version（版本从应用 NextflowVersion[] 获取）
cli.execute(cli.build_run(public_app="cm-rnaseq-xxx", public_app_name="my-rnaseq",
                          nf_version="v23.10.1", name="run-1", output="json"))

# form D：COS NF，必传 nf_version（从默认候选列表选取）
cli.execute(cli.build_run(nf_cos_path="cos://my-bucket/nf-apps/my-pipe/",
                          name="my-nf-run", nf_version="24.04.3", output="json"))

# form B 偶发：用户要改参数 → 显式覆盖
cli.execute(cli.build_run(public_app="cm-xxx", public_app_name="my-app",
                          input_json="./run.json", output="json"))

# form A 整改：复用 update_app_id；v6 起可加 release_name 把新版本发布命名
cli.execute(cli.build_run(wdl="./fixed.wdl", input_json="./hello.json",
                          name="hello", update_app_id="app-xxxx"))
cli.execute(cli.build_run(wdl="./fixed.wdl", input_json="./hello.json",
                          name="hello", update_app_id="app-xxxx",
                          release_name="v1.1", release_desc="fix OOM"))

# form C 运行指定版本（v6 强制：先 list versions 让用户拍板）
cli.execute(cli.build_run(app="app-xxxx", target_version="ver-aaaaaaaa",
                          input_json="./run.json", output="json"))

# form C v6.1：用户从 list templates 中拍板了 tmpl-aaaa，再 run（与 input_json 互斥）
cli.execute(cli.build_run(app="app-xxxx", target_version="ver-aaaaaaaa",
                          template_id="tmpl-aaaa", output="json"))

# form B v6.1：导入后改走 form C + 模板拍板（推荐）
# 1) 用 build_run(public_app=..., public_app_name=...) 完成 import + 兜底跑
# 2) 拿到导入后的 app-xxxx 后，再走 list versions / list templates → run --app + --template

# 状态
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_status(run_group_id="rg-xxx", output="json"))

# 异步失败取证（debug 三段式）
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))           # 段 1
cli.execute(cli.build_debug(run_uuid="uuid-xxx", output="json"))             # 段 2
cli.execute(cli.build_debug(run_uuid="uuid-xxx", job_id="plan-xxx",          # 段 3
                            output="json"))
```

环境变量 `OMICS_CLI_PATH` 可覆盖 CLI 可执行文件路径。
