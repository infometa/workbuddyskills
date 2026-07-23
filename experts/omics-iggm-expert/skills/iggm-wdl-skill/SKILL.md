---
name: iggm-wdl-skill
description:
  "腾讯健康组学平台(Omics) - IgGM-WDL 公共应用专用运行助手（独立应用，AppType=WDL）。IgGM (Immunoglobulin Generative Model) 是 TencentAI4S 研发的抗体/纳米抗体生成式基础大模型（ICLR 2025 收录，AIntibody 抗体设计竞赛前三名），通过统一框架针对给定抗原同时生成抗体序列与结构，支持抗体/纳米抗体从头设计、CDR 重设计与亲和力成熟。仅服务于 IgGM-WDL 这一个公共应用的导入与运行；其他应用请改用 omics-task-skill。触发词：IgGM, iggm, IGGM, IgGM-WDL, iggm-wdl, IgGM WDL, IgGM(WDL), IgGM 的 WDL 版, Immunoglobulin Generative Model, 免疫球蛋白生成模型, 抗体生成模型, 抗体生成式大模型, TencentAI4S 抗体模型, 腾讯 AI for Science 抗体, ICLR 2025 抗体, AIntibody, 抗体设计, 抗体从头设计, de novo 抗体设计, 抗体生成, 抗体序列设计, 抗体结构设计, 抗体序列+结构, 抗体序列与结构同时生成, 抗体序列结构联合生成, 纳米抗体, 纳米抗体设计, nanobody, nanobody 设计, CDR 设计, CDR 重设计, CDR redesign, CDR-H3 设计, 抗原特异性抗体, 针对抗原设计抗体, 抗原结合抗体, 给定抗原生成抗体, 亲和力成熟, affinity maturation, 抗体亲和力优化, 跑 IgGM-WDL, 跑 iggm-wdl, 跑 IgGM 的 WDL 版, 用 IgGM-WDL 做抗体设计, 用 IgGM-WDL 生成抗体"
---

# IgGM-WDL Skill (v1.0 · 单应用收窄版)

> 本 SKILL 是 `omics-task-skill` 的**单应用收窄版**：仅服务于 `IgGM-WDL` 这一个公共应用。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅运行 IgGM-WDL 这一个 AppId**；任何越界都视为越权。

---

## 应用锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段              | 值                                     |
| ----------------- | -------------------------------------- |
| **应用名称**      | `IgGM-WDL`                             |
| **AppId（锁定）** | `a9c8cb12-0a16-43f0-ab07-96ec5b41cc71` |
| **应用类型**      | `WDL`                                  |
| **分组类型**      | `STANDALONE_APP`（独立应用）           |
| **标签**          | AI 模型                                |

**应用简介**：IgGM（Immunoglobulin Generative Model）是腾讯 AI Lab 姚建华团队联合复旦大学应天雷、上海交通大学赵沛霖、
中国科学院大学高兴宇团队发布的**抗体设计通用基础模型**（ICLR 2025）。
通过大规模免疫组库数据训练，IgGM 可针对给定抗原**同时生成抗体序列与结构**，
支持抗体 / 纳米抗体的从头设计、CDR 重设计与亲和力成熟。
模型由三个核心组件构成：用于提取序列特征的预训练语言模型、用于识别相关特征的特征学习模块、用于联合生成序列与结构的扩散模块。

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用以下 **6 条** CLI 一级命令的**收窄子集**：

```
login   whoami   config   run   status   debug
```

> 注意：`omics list public-apps` / `omics list apps` **均禁用**——本 SKILL 已锁定单一 AppId，
> 既不需要让用户在公共应用列表里挑，也不需要查项目内其它应用。

### 🚫 严令禁止

1. **严禁运行除 IgGM-WDL 之外的任何应用**：
   - 禁止使用 `omics run --wdl <path>`（**用户本地 WDL** —— 注意区分：本 SKILL 跑的 IgGM-WDL 是**公共应用**，不是用户的本地 WDL 文件）
   - 禁止使用 `omics run --app <ApplicationId>`（项目内已有应用）
   - 禁止使用 `omics run --public-app <其它 AppId>`（其它公共应用）
   - **唯一允许**的 run 形态：`omics run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 ...`
2. **严禁编造其他命令**——例如 `app list` / `app templates` / `import` 等都已废弃，调用必失败。
3. **严禁直接调用 omics 后端 HTTP API**（CommonAppService.\* / RunService.\* / ImportApplication 等）、
   SQL、文件系统写入等任何旁路通道。
4. **严禁通过组合现有命令"模拟"出白名单外的语义**——例如不能把"导入公共应用"作为独立动作执行；
   导入是 `omics run --public-app` 的内部步骤，必须随 run 一起发生。
5. **`omics login` / `omics config set` 由用户在本机终端执行**，SKILL 永远不主动调（OAuth 浏览器
   回调 + 交互式输入只能在用户本机完成）。
6. **严禁让用户提供 AppId / PublicAppId / CommonAppUuid**——AppId 已硬编码，用户提供其它 ID 一律拒绝。
7. **严禁传入 `--nf-version`** —— IgGM-WDL 是 **WDL 类型**，不是 NEXTFLOW；CLI 会忽略并提示。

### ✅ run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须按 §4.2 模板完成二次确认：

1. 拼出完整命令字符串（含所有 flag），AppId 必须是上方锁定值
2. 输出参数摘要表（应用 / 项目 / 环境 / 输入 / 类型等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复（y / yes / 确认 / 继续 / 是 / 执行 / OK）才调用
5. 用户拒绝（n / no / 取消）→ 终止；模糊回复（嗯 / 好 / 可以）→ 再次明确询问
6. 用户追加修改 → 回到 1 重拼

### ✅ 其他命令的确认要求

| 命令                                                  | 是否需要确认              |
| ----------------------------------------------------- | ------------------------- |
| `whoami` / `status` / `debug` / `config show / clear` | 免确认（只读 / 本地操作） |
| `run`                                                 | **必须**                  |
| `login` / `config set`                                | 不调，引导用户本机执行    |

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义     | SKILL 处理                                                                              |
| ------ | -------- | --------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                             |
| `1`    | 业务错误 | 把 stderr 转述给用户。如果是"未配置"错误，按 Step 2 引导用户去本机跑 `omics config set` |
| `2`    | 鉴权失败 | 按 Step 1 引导用户去本机跑 `omics login`，不要循环重试                                  |

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

**SKILL 不要自己调 `omics login`。** 一旦 `whoami` 返回退出码 2 或任何业务命令报"鉴权失败 / session 过期 / 401"，立即给用户下面这段话：

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
> COS BucketName 为**必填项**。
>
> 完成后回到我这里告诉我「已配置」，我会继续后续操作。

收到用户「已配置 / done」类肯定答复后，重新跑一次 `omics config show -o json` 确认 → exit 0 + 字段齐全才进入业务流程。

---

## 命令意图映射表（IgGM-WDL 收窄版）

| 用户说                                        | CLI 命令                                                                                         | 场景     |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------- |
| 「我没装 CLI / 提示 command not found」       | **告诉用户去 https://cnb.cool/tencenthealthcareomics/omics-platform-cli 下载安装**，SKILL 不调   | Step −1  |
| 「我登录了吗 / 当前账号是谁」                 | `omics whoami`                                                                                   | Step 0.1 |
| 「我没登录 / session 过期了」                 | **告诉用户在本机终端跑** `omics login`，SKILL 不调                                               | Step 1   |
| 「现在用的是哪个项目和环境」                  | `omics config show -o json`                                                                      | Step 0.2 |
| 「配下默认项目 / 切到 xx 项目」               | **告诉用户在本机终端跑** `omics config set`，SKILL 不调                                          | Step 2   |
| 「清掉本地配置」                              | `omics config clear`                                                                             | —        |
| 「跑 IgGM」「做抗体设计」「针对抗原生成抗体」 | `omics run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 [--public-app-name <name>] -o json` | §4       |
| 「跑 IgGM-WDL，参数我自己改过」               | 上面命令 + `--input <path>` 显式覆盖自动模板                                                     | §4       |
| 「看任务进度」「查批次状态」                  | `omics status -o json`                                                                           | §5       |
| 「rg-xxx 跑完了吗 / 看子任务」                | `omics status <rgId> -o json`                                                                    | §5       |
| 「rg-xxx 哪些子任务挂了」                     | `omics debug <rgId> -o json`                                                                     | §6.1     |
| 「这个失败子任务到底为啥挂的」                | `omics debug --run <runUuid> -o json`                                                            | §6.2     |
| 「钻下 plan-xxx 这个作业的 stderr」           | `omics debug --run <runUuid> --job <jobId> -o json`                                              | §6.3     |
| 「列下平台公共应用」「跑别的应用」            | ❌ **拒绝**——本 SKILL 仅服务 IgGM-WDL；建议用户改用 `omics-task-skill`                           | —        |

> ❌ 用户说「跑本地 WDL」「跑别的公共应用 X」「跑项目里那个 app-xxx」：本 SKILL **必须拒绝**，
> 引导用户：「我只能帮你跑 IgGM-WDL；如需运行其他应用，请使用 `omics-task-skill`。」

---

## Step 3：导入前同名检查（**必经**）

IgGM-WDL 进入 `omics run --public-app ...` 之前，SKILL 必须先在 config 项目里检查是否已存在同名应用，避免：

- service 端 `CreateApplication` 因 Name 唯一约束直接报错；
- SKILL 自动加后缀（如 `IgGM-WDL-1`、`IgGM-WDL-cli`）替用户决策，污染应用列表。

### 检查方法（**例外允许的 list apps 调用**）

> 本 SKILL 整体禁用 `omics list apps`，但**仅允许在导入前同名检查这一处**调用，
> 其结果**只能用于"是否已有 IgGM-WDL 同名应用"的二选一判断**，**禁止用于让用户挑别的应用运行**。

```bash
python3 scripts/omics_cli.py list apps -o json
```

在返回 JSON 的 `Applications[]` 中查找 `Name == "IgGM-WDL"`（或用户提供的自定义 candidateName）：

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | 不传 `--public-app-name` 走 CLI 原名兜底；或按用户指定的新名传入                                            |
| **≥ 1 条命中** | **必须停下来**，把命中条目的 `ApplicationId / Name / Type / VersionCount / CreateTime` 列给用户，二选一询问 |

### 命中同名时的话术

> 项目里已经存在一个叫 `IgGM-WDL` 的应用：
>
> - ApplicationId：`app-xxxx`
> - Type：WDL，版本数：3，创建时间：2026-05-20 10:11
>
> 我不会自动改名，请你二选一：
>
> **A. 重命名后导入（推荐）**：给一个新的导入名，比如 `IgGM-WDL-v2` / `IgGM-WDL-2026q2`
> → 我会用你给的新名字重新导入这个公共应用并运行。
>
> **B. 终止本次运行**：本 SKILL 仅服务于公共应用 IgGM-WDL 的导入与运行；
> 如需直接复用项目里已有的 `app-xxxx` 应用，请使用 `omics-task-skill`（form C：`omics run --app app-xxxx`）。
>
> 你选哪个？或者直接告诉我新名字。

> **强约束**：
>
> - SKILL **不要**自动给候选名加 `-1` / `-2` / `-cli` / 时间戳之类的后缀。命名是用户的项目治理空间，必须由用户拍板。
> - 如果用户在本 SKILL 内选 B（复用已有应用），**必须拒绝**——本 SKILL 不能调 `omics run --app <已有 AppId>`，请引导用户去 `omics-task-skill`。

---

## Step 4：运行（仅形态 B · 公共应用 · 自动模板路径）

`omics run` 在本 SKILL 中**只接受**以下命令骨架：

```bash
omics run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
          [--public-app-name <importedName>] \
          [--input <path>] \
          [--name <runName>] \
          -o json
```

> - `--public-app` 值**固定**为 IgGM-WDL 的 AppId，不接受替换。
> - **不传 `--nf-version`**（WDL 应用无 NF 版本概念；CLI 会忽略并提示）。
> - `--public-app-name` 按 §3 同名检查决策；独立公共应用允许走 CLI 原名兜底（不传也可）。
> - `--input` 仅在用户明确要求自定义参数时显式传入（覆盖自动 InputTemplate）。

CLI 内部链路：ImportCommonApplication → DescribeInputTemplates → GetInputTemplateFile → baseline+override → RunApplication。

### 4.1 完整流程

1. **Step 0** 鉴权 + 配置双重检查（必经）
2. **Step 3** 导入前同名检查（必经）
3. **决定 `--public-app-name`**：用户原话 / 默认走 CLI 原名兜底
4. **二次确认**（按 §4.2 模板）
5. **一步直达运行**：
   ```bash
   python3 scripts/omics_cli.py run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
     [--public-app-name <name>] [--name run-1] -o json
   ```
6. **若 CLI 报 `PARAM_MERGE_FAILED`**：按 §4.4 处理。
7. **如果用户主动要求改参数** → 显式传 `--input` 覆盖自动模板：
   ```bash
   python3 scripts/omics_cli.py run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
     --public-app-name <name> --input ./run.json -o json
   ```

### 4.2 二次确认模板（**必经**）

向用户汇总后等"确认/继续/OK/y"再执行。

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用（form B，自动模板）        │
  │ 公共应用    : IgGM-WDL                            │
  │ AppId       : a9c8cb12-0a16-43f0-ab07-96ec5b41cc71│
  │ AppType     : WDL                                 │
  │ 导入后命名  : IgGM-WDL（或用户指定）               │
  │ 项目        : prj-yyy (..., ap-guangzhou) ← config│
  │ 环境        : env-zzz (...)               ← config│
  │ 参数模板    : 自动取该应用第一个 InputTemplate    │
  │ 运行名称    : <Name>                              │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
            --public-app-name IgGM-WDL \
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

### 4.3 运行参数：合并模式

> CLI 的 `omics run` 内部按 `final = baseline + override` 合并参数 JSON：
>
> - `baseline` = WDL 中显式声明的默认值（ValidateApplication.Inputs[].Default）
> - `override` = form B 默认自动取该应用第一个 InputTemplate；用户给 `--input` 时则替换

| 场景                                                                       | SKILL 行为                                                                                                                                              |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `omics run` 直接 exit 0 + 输出 RunGroupId                                  | 一切顺利，转述结果给用户即可                                                                                                                            |
| stderr 出现 `❌ 参数模板校验失败` 或 JSON 输出 `Error: PARAM_MERGE_FAILED` | 解析其中的 `Report.MissingRequired / TypeErrors / ExtraFields`，把缺失字段及类型告诉用户；用户给值后 SKILL 写入本地 `run.json` 再 `--input <path>` 重跑 |

### 4.4 PARAM_MERGE_FAILED 处理

JSON 报错的关键字段：

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
> - `<workflow>.antigen_pdb`：File（必填，抗原结构）
> - `<workflow>.antigen_chain`：String（必填，抗原链 ID）
> - `<workflow>.design_mode`：String（必填，例如 de_novo / cdr_redesign / affinity_maturation）
>
> 请把这些值告诉我，或者直接给我一份本地 JSON 路径，我帮你按 `--input` 传回去重跑。

### 4.5 流水线失败提示

| 错误                                      | 处置建议                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| `参数模板校验失败` / `PARAM_MERGE_FAILED` | 解析 `Report.MissingRequired / TypeErrors`，按 §4.4 引导用户给值后通过 `--input` 传回重跑 |
| 用户误传 `--nf-version`                   | 提醒用户 IgGM-WDL 是 WDL 类型，无需 NF 版本；CLI 会忽略此参数                             |
| `环境 X 不可用 / 不存在`                  | 提示用户重跑 `config set` 或去控制台检查                                                  |
| `环境 X 下未绑定默认缓存卷`               | 提示用户去控制台为该环境配置默认 Volume                                                   |
| `Result=CONFLICT` 反复出现                | CLI 内部已尝试回退；说明应用被并发修改，提示用户等待或换新名重新导入                      |
| 鉴权失败（exit 2）                        | 不重试，引导用户在本机跑 `omics login`                                                    |

---

## Step 5：状态查询

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

紧凑总结：`最近 N 个 IgGM 批次：✅ 已完成 X / ❌ 已失败 Y / 🔄 运行中 Z`。

> ⚠️ `omics status` 列出的是**当前项目**所有批次（不限于 IgGM），SKILL 转述时
> 应**优先突出 IgGM 相关批次**，但不强制过滤——这是平台原生能力。

---

## Step 6：异步失败取证（debug 三段式）

**触发条件**：`omics status` 看到子任务 `Status=Failed / Aborted / Error`，或用户问「rg-xxx 为啥挂了」。

**工具**：`omics debug` 三段式（CLI 端只取证，不做规则匹配；症状判断由 SKILL 模型对照
[`references/runtime_error_kb.md`](references/runtime_error_kb.md) 决定）。

### 6.1 段 1：列批次失败子任务

```bash
python3 scripts/omics_cli.py debug <runGroupId> -o json
```

输出关键字段：

- `TotalRuns / FailedCount`
- `FailedRunUuids[]`
- `Runs[]`：完整子任务列表

**SKILL 行为**：

1. `FailedCount == 0` → 告诉用户"该批次没有失败子任务，可能是运行中或已成功"
2. `FailedCount == 1` → 直接进入段 2
3. `FailedCount > 1` → 询问用户先看哪一个，或主动取前 1~2 个钻一遍找共性

### 6.2 段 2：单子任务现场

```bash
python3 scripts/omics_cli.py debug --run <runUuid> -o json
```

输出关键字段（详见 `references/cli_commands.md` debug 段）：

- `Status`：顶层 RunMetadata（`RunType / Status / JobId / ErrorMessage / Input / Output / Command`）
- `Calls[]`：cromwell call 元数据
- `JobLogs[]`：CLI 已自动钻取最多 5 个失败 call 的真实 stderr 与 K8s 事件
  - `Stderr` / `StderrTruncated`：实际日志正文（已截尾，头 4KB + 尾 24KB）
  - `PodEvents[]`：保留 `FailedMount`（前端会过滤但 AI 排障必须看）

**症状识别流程**：

1. 优先看 `Status.ErrorMessage`
2. 逐个看 `JobLogs[].Stderr` 末尾
3. 看 `JobLogs[].PodEvents`
4. 对照 `references/runtime_error_kb.md` 决策快速表
5. 都不命中 → 走兜底，把现场原文贴给用户做透明分析

### 6.3 段 3：精确钻取某个 Job

```bash
python3 scripts/omics_cli.py debug --run <runUuid> --job <jobId> -o json
```

输出与段 2 同结构，但 `Calls` / `JobLogs` 都按 `JobId` 过滤。

### 6.4 关键守则

1. **CLI 端绝不主动调 `omics debug`** —— 用户问"为啥挂了"才用
2. **不要替用户做症状判断 + 自动改代码** —— 看到 `OOMKilled` 不要直接改 memory，要先告诉用户"目测内存不足"并询问是否调整
3. **stderr 内容是用户应用代码** —— 转述时**整段贴出来**，不要总结/二次加工
4. **修复后统一走 `omics run` 重发** —— 本 SKILL 的重发**仍然只能走 form B**：
   ```bash
   omics run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
             --public-app-name <newName> --input <fixed.json> -o json
   ```
   ⚠️ 严禁本 SKILL 用 `--app <已导入的 ApplicationId>` 复用——那会越界进入 form C，请引导用户去 `omics-task-skill`。

---

## 典型会话场景

### 场景 A0：用户没装 CLI

1. 任意命令报 `FileNotFoundError` / `command not found: omics` / `未找到 'omics' 命令` →
   **告知用户去 https://cnb.cool/tencenthealthcareomics/omics-platform-cli 下载页按页面安装脚本和使用指南安装**，SKILL 不自动装；
2. 等用户回执「已安装」→ 跑 `omics version` 验证 → 通过后进入场景 A。

### 场景 A：用户首次使用本 SKILL

1. `whoami` → 退出 2 → **告知用户去本机终端跑** `omics login`，等用户回执「已登录」
2. 重新 `whoami` ✓ → 跑 `config show` → 退出 1 → **告知用户去本机终端跑** `omics config set`，等用户回执「已配置」
3. 重新 `config show` ✓ → 进入业务流程

### 场景 B：跑 IgGM-WDL（标准链路）

1. `whoami` ✓ + `config show` ✓ → 复述当前配置
2. 用户："跑 IgGM" 或 "做抗体设计" 或 "针对这个抗原生成抗体"
3. **同名检查（§3）**：执行 `list apps -o json`，匹配 `Name == "IgGM-WDL"`
   - 0 条命中 → 通过
   - ≥1 条命中 → 停下，请用户选「重命名」或「终止改用 omics-task-skill」
4. **二次确认**（按 §4.2 模板）
5. **一步直达运行**：
   ```bash
   python3 scripts/omics_cli.py run --public-app a9c8cb12-0a16-43f0-ab07-96ec5b41cc71 \
     --public-app-name <name> --name run-1 -o json
   ```
6. 解析 `RunGroupId` → 提示 `omics status <rgId>`

### 场景 C：用户要求自定义参数

1. 走完场景 B 第 1~3 步
2. 用户："参数我想改 antigen_pdb / design_mode / 输出抗体数量"
3. 收齐参数 → 写 `/tmp/run.json`
4. 二次确认（命令带 `--input /tmp/run.json`）
5. 执行 `run --public-app ... --input /tmp/run.json`

### 场景 D：用户问"跑别的应用"

1. **拒绝**："本 SKILL 只能帮你运行 IgGM-WDL。如需运行其他应用（本地 WDL / 其他公共应用 / 项目内已有应用），
   请使用通用版的 `omics-task-skill`。"
2. 不调任何命令。

### 场景 E：用户混淆"跑本地 WDL"和"跑 IgGM-WDL 公共应用"

1. 注意区分：本 SKILL 的"IgGM-WDL"是**平台公共应用名**（type=WDL），不是用户自己的本地 WDL 文件。
2. 如果用户想"用本地 WDL 跑"——这是 form A（本地 WDL 上传）→ 本 SKILL 拒绝，引导去 `omics-task-skill`。
3. 如果用户想"跑 IgGM-WDL 这个公共应用"——这正是本 SKILL 的服务范围，按场景 B 流程进行。

### 场景 F：业务命令报鉴权失败

1. 任何业务命令 exit 2 → SKILL 不重试
2. **告知用户去本机终端跑** `omics login` → 等用户回执
3. 重新跑原命令一次

---

## 计算资源说明

IgGM-WDL 涉及大型蛋白质结构生成与扩散模型推理，建议使用 GPU 资源（T4 及以上）。
具体资源参数已由公共应用模板定义；如需自定义（例如指定 GPU 数量、内存等），
通过用户的 `--input run.json` 内 WDL `runtime` 段配置：

```
runtime {
  gpuType: "T4"
  gpuCount: 1
  memory: "32 GB"
}
```

> SKILL 不主动替用户决定 GPU 型号与数量；如用户问"用哪个"，告知候选并询问其偏好与抗原大小、设计目标数量。

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

# ✅ 检查类
cli.execute(cli.build_whoami())
cli.execute(cli.build_config_show(output="json"))

# ✅ 仅在导入前同名检查时使用
cli.execute(cli.build_list_apps(output="json"))

# ✅ 唯一允许的 run（AppId 锁定为 IgGM-WDL；WDL 类型不传 nf_version）
cli.execute(cli.build_run(
    public_app="a9c8cb12-0a16-43f0-ab07-96ec5b41cc71",
    public_app_name="IgGM-WDL",
    name="run-1",
    output="json",
))

# ✅ 用户自定义参数时
cli.execute(cli.build_run(
    public_app="a9c8cb12-0a16-43f0-ab07-96ec5b41cc71",
    public_app_name="IgGM-WDL",
    input_json="./run.json",
    output="json",
))

# ❌ 禁止：以下任何形态在本 SKILL 中均不允许
# cli.execute(cli.build_run(wdl="./hello.wdl", ...))                          # form A（用户本地 WDL）
# cli.execute(cli.build_run(app="app-xxx", ...))                              # form C
# cli.execute(cli.build_run(public_app="cm-other-xxx", ...))                  # 其它公共应用
# cli.execute(cli.build_run(public_app="a9c8cb12-...", nf_version="v24...")) # IgGM-WDL 是 WDL，不传 nf_version
# cli.execute(cli.build_list_public_apps(...))                                # 列公共应用（用户不需要挑）

# ✅ 状态
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_status(run_group_id="rg-xxx", output="json"))

# ✅ debug 三段式
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))
cli.execute(cli.build_debug(run_uuid="uuid-xxx", output="json"))
cli.execute(cli.build_debug(run_uuid="uuid-xxx", job_id="plan-xxx", output="json"))
```

环境变量 `OMICS_CLI_PATH` 可覆盖 CLI 可执行文件路径。
