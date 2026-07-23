---
name: scprotein-collection-skill
description:
  "腾讯健康组学平台(Omics) - scPROTEIN Collection 公共应用合集专用运行助手。scPROTEIN 是腾讯人工智能实验室研发的基于图神经网络架构的深度学习模型，可应用于质谱和抗体路线的单细胞蛋白组数据建模，对 bottom-up 采集的多肽进行 uncertainty 估计、对蛋白组数据降噪以提升数据质量、对最终细胞类型表征有显著提升；本合集（Nextflow，v24.04.3）含 2 个子应用：scPROTEIN_stage1（肽段水平：肽段定量不确定性评估）与 scPROTEIN_stage2（蛋白质水平：生成单细胞 embedding 与细胞类型表征）。仅服务于本合集子应用的导入与运行；其他应用请改用 omics-task-skill。触发词：scPROTEIN, scprotein, sc-PROTEIN, scProtein, SCPROTEIN, sc_protein, scPROTEIN Collection, scprotein collection, scProtein 合集, scPROTEIN_stage1, scPROTEIN_stage2, scPROTEIN Stage1, scPROTEIN Stage2, Stage1, Stage2, stage1, stage2, 阶段一, 阶段二, 第一阶段, 第二阶段, 单细胞蛋白组, 单细胞蛋白质组, 单细胞蛋白组学, single cell proteomics, scProteomics, 蛋白组学, 蛋白质组学, proteomics, 质谱蛋白组, 抗体路线蛋白组, bottom-up 蛋白组, 图神经网络, GNN, graph neural network 蛋白组, 肽段不确定性, 肽段定量不确定性, peptide uncertainty, 多肽 uncertainty 估计, 蛋白质降噪, 蛋白质数据去噪, 蛋白组数据降噪, 提升数据质量, 批次效应校正, batch effect correction, 蛋白组批次效应, 细胞嵌入, cell embedding, 单细胞 embedding, 细胞类型表征, 跑 scPROTEIN, 跑 scprotein, 跑 stage1, 跑 stage2, 跑单细胞蛋白组分析, 跑肽段不确定性评估, 跑蛋白质降噪, 用 scPROTEIN 做细胞嵌入, 用 scPROTEIN 表征细胞类型"
---

# scPROTEIN Collection Skill (v1.0 · 单合集收窄版)

> 本 SKILL 是 `omics-task-skill` 的**单合集收窄版**：仅服务于 `scPROTEIN Collection (Nextflow)` 这一个公共应用合集。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅运行 scPROTEIN Collection 合集下的子应用**；任何越界都视为越权。

---

## 应用锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段                     | 值                                     |
| ------------------------ | -------------------------------------- |
| **合集名称**             | `scPROTEIN Collection (Nextflow)`      |
| **合集 AppId（锁定）**   | `5c63718b-d24f-4a9f-9838-4177185f414a` |
| **PublicAppId**          | `publicapp-nf-scprotein-collection`    |
| **应用类型**             | `NEXTFLOW`                             |
| **分组类型**             | `APP_COLLECTION`（合集，含多个子应用） |
| **标签**                 | AI 模型                                |

**应用简介**：scPROTEIN 是由腾讯人工智能实验室研发的基于图神经网络架构的深度学习模型，
可应用于质谱和抗体路线的单细胞蛋白组数据建模。在统一框架下实现四大功能：

1. **肽段定量不确定性评估**
2. **蛋白质数据去噪**
3. **批次效应校正**
4. **单细胞特异性嵌入编码**

本合集核心子流程：

1. **阶段一（Stage1）** — 从肽段水平数据运行 scPROTEIN，评估不确定性
2. **阶段二（Stage2）** — 以蛋白质水平数据生成细胞 embedding

> ⚠️ 合集（`APP_COLLECTION`）本身**不能直接 `omics run`**——必须先展开找到具体子应用 AppId，再用子应用 AppId 跑。
> 这是平台规则；本 SKILL 流程已内化此约束。

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用以下 **7 条** CLI 一级命令的**收窄子集**：

```
login   whoami   config   list   run   status   debug
```

> 注意：`omics list public-apps` 仅允许以 `--parent-app 5c63718b-d24f-4a9f-9838-4177185f414a` 形态调用，
> 用于展开本合集的子应用清单；**禁止不带 `--parent-app` 调用**（那会列出全平台所有公共应用，越界）。
>
> `omics list apps` 整体禁用，但**仅允许在导入前同名检查这一处**调用。

### 🚫 严令禁止

1. **严禁运行除 scPROTEIN Collection 之外的任何应用**：
   - 禁止使用 `omics run --wdl <path>`（本地 WDL）
   - 禁止使用 `omics run --app <ApplicationId>`（项目内已有应用）
   - 禁止使用 `omics run --public-app <非本合集子应用 AppId>`
   - 禁止使用 `omics run --public-app 5c63718b-d24f-4a9f-9838-4177185f414a`（合集本身不可直接 run）
   - **唯一允许**的 run 形态：`omics run --public-app <scPROTEIN 合集展开后的子应用 AppId> ...`
2. **严禁不带 `--parent-app` 调 `list public-apps`**——本 SKILL 不需要让用户在全平台公共应用里挑。
3. **严禁让用户提供合集 AppId / PublicAppId**——合集 AppId 已硬编码，用户提供其它 ID 一律拒绝。
4. **严禁编造其他命令**——例如 `app list` / `app templates` / `import` 等都已废弃，调用必失败。
5. **严禁直接调用 omics 后端 HTTP API**（CommonAppService.\* / RunService.\* / ImportApplication 等）、
   SQL、文件系统写入等任何旁路通道。
6. **严禁通过组合现有命令"模拟"出白名单外的语义**——例如不能把"导入公共应用"作为独立动作执行；
   导入是 `omics run --public-app` 的内部步骤，必须随 run 一起发生。
7. **`omics login` / `omics config set` 由用户在本机终端执行**，SKILL 永远不主动调（OAuth 浏览器
   回调 + 交互式输入只能在用户本机完成）。

### ✅ run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须按 §5.2 模板完成二次确认：

1. 拼出完整命令字符串（含所有 flag），AppId 必须来自本合集的子应用展开结果
2. 输出参数摘要表（合集 / 选定子应用 / 项目 / 环境 / 输入 / NF 版本等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复（y / yes / 确认 / 继续 / 是 / 执行 / OK）才调用
5. 用户拒绝（n / no / 取消）→ 终止；模糊回复（嗯 / 好 / 可以）→ 再次明确询问
6. 用户追加修改 → 回到 1 重拼

### ✅ 其他命令的确认要求

| 命令                                                                              | 是否需要确认              |
| --------------------------------------------------------------------------------- | ------------------------- |
| `whoami` / `status` / `debug` / `config show / clear` / `list public-apps --parent-app ...` / `list apps`（同名检查） | 免确认（只读 / 本地操作） |
| `run`                                                                             | **必须**                  |
| `login` / `config set`                                                            | 不调，引导用户本机执行    |

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义     | SKILL 处理                                                                                 |
| ------ | -------- | ------------------------------------------------------------------------------------------ |
| `0`    | 成功     | 解析 stdout                                                                                |
| `1`    | 业务错误 | 把 stderr 转述给用户。如果是"未配置"错误，按 Step 2 引导用户去本机跑 `omics config set`    |
| `2`    | 鉴权失败 | 按 Step 1 引导用户去本机跑 `omics login`，不要循环重试                                     |

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

## 命令意图映射表（scPROTEIN Collection 收窄版）

| 用户说                                                       | CLI 命令                                                                                         | 场景     |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ | -------- |
| 「我没装 CLI / 提示 command not found」                      | **告诉用户去 https://cnb.cool/tencenthealthcareomics/omics-platform-cli 下载安装**，SKILL 不调   | Step −1  |
| 「我登录了吗 / 当前账号是谁」                                | `omics whoami`                                                                                   | Step 0.1 |
| 「我没登录 / session 过期了」                                | **告诉用户在本机终端跑** `omics login`，SKILL 不调                                               | Step 1   |
| 「现在用的是哪个项目和环境」                                 | `omics config show -o json`                                                                      | Step 0.2 |
| 「配下默认项目 / 切到 xx 项目」                              | **告诉用户在本机终端跑** `omics config set`，SKILL 不调                                          | Step 2   |
| 「清掉本地配置」                                             | `omics config clear`                                                                             | —        |
| 「跑 scPROTEIN」「做单细胞蛋白组分析」「跑 Stage1 / Stage2」 | 先 §3 展开子应用清单 → 用户挑子应用 → §4 同名检查 → §5 run                                       | §3~5     |
| 「scPROTEIN 里有哪些子流程」                                 | `omics list public-apps --parent-app 5c63718b-d24f-4a9f-9838-4177185f414a -o json`               | §3       |
| 「跑 scPROTEIN 的某子应用，参数我自己改过」                  | `omics run --public-app <子应用AppId> --public-app-name <name> --nf-version <ver> --input <p>`   | §5       |
| 「看任务进度」「查批次状态」                                 | `omics status -o json`                                                                           | §6       |
| 「rg-xxx 跑完了吗 / 看子任务」                               | `omics status <rgId> -o json`                                                                    | §6       |
| 「rg-xxx 哪些子任务挂了」                                    | `omics debug <rgId> -o json`                                                                     | §7.1     |
| 「这个失败子任务到底为啥挂的」                               | `omics debug --run <runUuid> -o json`                                                            | §7.2     |
| 「钻下 plan-xxx 这个作业的 stderr」                          | `omics debug --run <runUuid> --job <jobId> -o json`                                              | §7.3     |
| 「列下平台公共应用」「跑别的应用」                           | ❌ **拒绝**——本 SKILL 仅服务 scPROTEIN Collection；建议用户改用 `omics-task-skill`                | —        |

> ❌ 用户说「跑本地 WDL」「跑别的公共应用 X」「跑项目里那个 app-xxx」「跑 scPROTEIN 合集本身不挑子应用」：
> 本 SKILL **必须拒绝**，引导用户：
> 「我只能帮你跑 scPROTEIN Collection 下的某一个具体子应用；如需运行其他应用，请使用 `omics-task-skill`。」

---

## Step 3：展开本合集子应用（**必经**第一步）

合集（`APP_COLLECTION`）本身不可直接 `omics run`，必须先展开找到具体子应用。

```bash
python3 scripts/omics_cli.py list public-apps \
  --parent-app 5c63718b-d24f-4a9f-9838-4177185f414a -o json
```

> ⚠️ `--parent-app` 值**固定**为 scPROTEIN Collection 的 AppId，不接受替换。

**JSON 关键字段**（每个子应用）：

- `AppId`：用于 `omics run --public-app <子应用AppId>`
- `AppName`：用于 `--public-app-name` 兜底（合集子应用必须显式传名，否则 CLI 报错）
- `AppType`：**必须从返回值的该子应用 AppType 字段获取**，不可硬编码；
  用于决定是否传 `--nf-version`（NEXTFLOW 类型必传，其他类型不需要）
- `AppDesc`：简要描述
- `NextflowVersion[]`：候选 NF 版本列表（必须从中挑一个）
- `AppTags[]`

### 3.1 转述给用户

> scPROTEIN Collection 包含以下子应用，请挑一个具体的子流程：
>
> ① **<AppName 1>** (`<AppId 1>`) — <AppDesc 简要> · NF 版本候选: <NextflowVersion[0]>, ...
> ② **<AppName 2>** (`<AppId 2>`) — <AppDesc 简要> · NF 版本候选: ...
> ...
>
> 你想跑哪一个？（请直接告诉我编号或 AppName；常见选择为 Stage1 / Stage2）

**约束**：

- SKILL **不要替用户随便选**——必须让用户明确指定子应用
- 用户回复模糊（如"都行"/"随便"）→ 再次明确询问
- 用户指定的子应用 AppId 必须**严格来自上面 JSON 的 `Apps[].AppId`**，不接受用户自填的其它 AppId

### 3.2 记录字段

用户挑定后，SKILL 内部记录：

- `<selectedAppId>`：将作为 `--public-app` 入参（form B）或用于匹配已导入应用（form C 断点恢复）
- `<selectedAppName>`：将作为 `--public-app-name` 默认候选（也是同名检查的 candidateName）
- `<selectedAppType>`：从该子应用的 `AppType` 字段获取（**必须使用返回值，不可硬编码**；
  若为 `NEXTFLOW` 则后续 `--nf-version` 必传，否则不需要）
- `<selectedNfVersion>`：从该子应用的 `NextflowVersion[]` 列表中挑一个（多个时**让用户挑**，不要替选）；
  **仅当 `<selectedAppType> == NEXTFLOW` 时才需要**

---

## Step 4：导入前同名检查（**必经**）

进入 `omics run --public-app ...` 之前，SKILL 必须先在 config 项目里检查是否已存在同名应用，避免：

- service 端 `CreateApplication` 因 Name 唯一约束直接报错；
- SKILL 自动加后缀（如 `<原名>-1`、`<原名>-cli`）替用户决策，污染应用列表。

### 检查方法（**例外允许的 list apps 调用**）

> 本 SKILL 整体禁用 `omics list apps`，但**仅允许在导入前同名检查这一处**调用，
> 其结果**只能用于"是否已有同名应用"的二选一判断**，**禁止用于让用户挑别的应用运行**。

```bash
python3 scripts/omics_cli.py list apps -o json
```

在返回 JSON 的 `Applications[]` 中查找 `Name == <selectedAppName>`（或用户提供的自定义 candidateName）：

| 命中情况       | SKILL 行为                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------ |
| **0 条命中**   | 用 `<selectedAppName>` 作为 `--public-app-name`（合集子应用**必传**），走 form B 导入+运行                      |
| **≥ 1 条命中** | **必须停下来**，把命中条目的 `ApplicationId / Name / Type / VersionCount / CreateTime` 列给用户，三选一询问      |

### 命中同名时的话术

> 项目里已经存在一个叫 `<selectedAppName>` 的应用：
>
> - ApplicationId：`app-xxxx`
> - Type：NEXTFLOW，版本数：3，创建时间：2026-05-20 10:11
>
> 我不会自动改名，请你三选一：
>
> **A. 重命名后导入**：给一个新的导入名，比如 `<selectedAppName>-v2` / `<selectedAppName>-2026q2`
> → 我会用你给的新名字重新导入这个子应用并运行（form B）。
>
> **B. 复用已有应用继续运行（推荐，断点恢复）**：如果这个应用是之前通过本 SKILL 导入的（
> 上次可能导入成功但运行流程意外中断），我可以直接用已有的 `app-xxxx` 继续运行（form C），
> 无需重复导入。
>
> **C. 终止本次运行**：如需直接复用项目里已有的 `app-xxxx` 应用做其他操作，请使用 `omics-task-skill`。
>
> 你选哪个？或者直接告诉我新名字（选项 A）。

> **强约束**：
> - SKILL **不要**自动给候选名加 `-1` / `-2` / `-cli` / 时间戳之类的后缀
> - **选项 B（复用已有应用）仅限断点恢复场景**：即该同名应用是之前通过本 SKILL 的 form B（`--public-app`）导入的，
>   且上次运行流程在导入成功后意外中断。SKILL 内部可用 `omics run --app <已有 ApplicationId>` 继续运行。
>   若用户要求复用**非本 SKILL 导入的**应用（如用户自行创建、其他 SKILL 导入等），**必须拒绝**并引导用户去 `omics-task-skill`

---

## Step 5：运行（form B · 公共应用导入+运行 / form C · 断点恢复复用）

`omics run` 在本 SKILL 中接受以下两种命令骨架：

**form B（首次导入+运行）**：
```bash
omics run --public-app <selectedAppId> \
          --public-app-name <importedName> \
          [--nf-version <selectedNfVersion>] \
          [--input <path>] \
          [--name <runName>] \
          -o json
```

**form C（断点恢复：复用已导入的应用继续运行）**：
```bash
omics run --app <existingApplicationId> \
          [--input <path>] \
          [--name <runName>] \
          -o json
```
> form C **仅允许在 Step 4 选项 B（断点恢复）场景下使用**，即 `<existingApplicationId>` 来自
> `list apps` 命中结果且该应用是之前通过本 SKILL 的 form B 导入的。

> - `--public-app` 值**必须**来自 §3 展开本合集的 `Apps[].AppId`，不接受其它 AppId。
> - `--nf-version` **仅当 `<selectedAppType> == NEXTFLOW` 时必传**，值**必须**来自该子应用的 `NextflowVersion[]` 候选；CLI 否则报 `MISSING_NF_VERSION`。
> - `--public-app-name` **必须**显式传入（合集子应用没有 CLI 兜底）。
> - `--input` 仅在用户明确要求自定义参数时显式传入（覆盖自动 InputTemplate）。

CLI 内部链路：ImportCommonApplication → DescribeInputTemplates → GetInputTemplateFile → baseline+override → RunApplication。

> ⚠️ **合集子应用的导入路径**：`omics run --public-app <子应用AppId>` 会**直接把子应用 AppId 作为 `CommonAppUuid` 调 `ImportCommonApplication`**，
> 不需要也不应该传合集 AppId。
> service 端 `DescribeCommonApp` 默认强制 `f_parent_app_id=''` 过滤，所以单独探测元信息可能查不到子应用——这是正常现象。
> 如果导入失败提示"AppId 不存在"，第一时间核对：传入的是不是合集自身 AppId？应当传 §3 展开后的**子应用** AppId。

### 5.1 完整流程

1. **Step 0** 鉴权 + 配置双重检查（必经）
2. **Step 3** 展开合集子应用 → 让用户挑（必经）
3. **Step 4** 导入前同名检查（必经）
4. **判断运行形态**：
   - **form B（无同名命中 / 用户选 A 重命名）**：
     a. 决定 `--public-app-name`：用户原话 / `<selectedAppName>` 兜底
     b. 决定 `--nf-version`：**若 `<selectedAppType> == NEXTFLOW`**，让用户从 `NextflowVersion[]` 挑（多个时不要替选）
     c. 二次确认（按 §5.2 模板，形态标注为 form B）
     d. 一步直达运行：
        ```bash
        python3 scripts/omics_cli.py run --public-app <selectedAppId> \
          --public-app-name <name> [--nf-version <ver>] [--name run-1] -o json
        ```
   - **form C（断点恢复：用户选 B 复用已有应用）**：
     a. 从 Step 4 命中结果取 `<existingApplicationId>`
     b. 二次确认（按 §5.2 模板，形态标注为 form C 断点恢复）
     c. 运行已有应用：
        ```bash
        python3 scripts/omics_cli.py run --app <existingApplicationId> \
          [--name run-1] [-o json]
        ```
5. **若 CLI 报 `PARAM_MERGE_FAILED`**：按 §5.4 处理。
6. **如果用户主动要求改参数** → 显式传 `--input` 覆盖自动模板：
   ```bash
   # form B
   python3 scripts/omics_cli.py run --public-app <selectedAppId> \
     --public-app-name <name> [--nf-version <ver>] --input ./run.json -o json
   # form C
   python3 scripts/omics_cli.py run --app <existingApplicationId> --input ./run.json -o json
   ```

### 5.2 二次确认模板（**必经**）

向用户汇总后等"确认/继续/OK/y"再执行。

**form B 模板（首次导入+运行）**：
```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用（form B，自动模板）        │
  │ 来源合集    : scPROTEIN Collection                │
  │ 子应用      : <selectedAppName>                   │
  │ AppId       : <selectedAppId>                     │
  │ AppType     : <selectedAppType>                   │
  │ NF 版本     : <selectedNfVersion> （若 NEXTFLOW） │
  │ 导入后命名  : <importedName>                      │
  │ 项目        : prj-yyy (..., ap-guangzhou) ← config│
  │ 环境        : env-zzz (...)               ← config│
  │ 参数模板    : 自动取该应用第一个 InputTemplate    │
  │ 运行名称    : <Name>                              │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --public-app <selectedAppId> \
            --public-app-name <importedName> \
            [--nf-version <selectedNfVersion>] \
            --name run-1 -o json

确认无误请回复「确认 / 继续 / y」；如需自定义参数请告诉我（可改走 --input 模式）。
```

**form C 模板（断点恢复：复用已导入应用）**：
```
即将运行任务，请确认（断点恢复模式）：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 已有应用（form C，断点恢复）        │
  │ 来源合集    : scPROTEIN Collection                │
  │ 子应用      : <selectedAppName>                   │
  │ ApplicationId : <existingApplicationId>           │
  │ 应用名称    : <selectedAppName> （已导入）        │
  │ 项目        : prj-yyy (..., ap-guangzhou) ← config│
  │ 环境        : env-zzz (...)               ← config│
  │ 参数模板    : 使用应用已有配置                    │
  │ 运行名称    : <Name>                              │
  └──────────────────────────────────────────────────┘
完整命令:
  omics run --app <existingApplicationId> \
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
| 用户改口"换一个子应用"                                          | 回到 §3 重新展开 / 让用户重选              |

### 5.3 运行参数：合并模式

> CLI 的 `omics run` 内部按 `final = baseline + override` 合并参数 JSON：
> - `baseline` = WDL/NF 中显式声明的默认值（ValidateApplication.Inputs[].Default）
> - `override` = form B 默认自动取该应用第一个 InputTemplate；用户给 `--input` 时则替换

| 场景                                                                       | SKILL 行为                                                                                                                                              |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `omics run` 直接 exit 0 + 输出 RunGroupId                                  | 一切顺利，转述结果给用户即可                                                                                                                            |
| stderr 出现 `❌ 参数模板校验失败` 或 JSON 输出 `Error: PARAM_MERGE_FAILED` | 解析其中的 `Report.MissingRequired / TypeErrors / ExtraFields`，把缺失字段及类型告诉用户；用户给值后 SKILL 写入本地 `run.json` 再 `--input <path>` 重跑 |

### 5.4 PARAM_MERGE_FAILED 处理

JSON 报错的关键字段：

- `Error`：固定为 `"PARAM_MERGE_FAILED"`
- `ApplicationId` / `WorkflowName`：定位上下文
- `Specs[]`：每项 `{ Name, Optional, TypeName, Default }`
- `Baseline` / `UserOverride` / `FinalParsed`：合并各阶段快照
- `Report.MissingRequired[]` / `EmptyRequired[]` / `ExtraFields[]` / `TypeErrors[]`
- `PartialSkeleton`：CLI 已拼好的"可保存即用"的 JSON
- `Hint[]`：CLI 给的下一步重跑命令模板

**典型话术**：

> 跑这次任务时 CLI 已经把 NF 的默认值和模板拼好，但还有 N 个必填项缺值：
>
> - `<workflow>.peptide_input`：File（Stage1 必填，肽段水平输入）
> - `<workflow>.protein_input`：File（Stage2 必填，蛋白质水平输入）
>
> 请把这些值告诉我，或者直接给我一份本地 JSON 路径，我帮你按 `--input` 传回去重跑。

### 5.5 流水线失败提示

| 错误                                      | 处置建议                                                                                                                |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `参数模板校验失败` / `PARAM_MERGE_FAILED` | 解析 `Report.MissingRequired / TypeErrors`，按 §5.4 引导用户给值后通过 `--input` 传回重跑                              |
| `MISSING_NF_VERSION`                      | 让用户从 §3 展开结果中该子应用的 `NextflowVersion[]` 列表挑一个；不要替选                                              |
| `公共应用 X 是一个合集` / `AppId 不存在`  | 立即核对：`--public-app` 是否传成了合集 AppId 而非子应用 AppId？合集 AppId（`5c63718b-...`）不可作为 run 的 `--public-app` |
| `环境 X 不可用 / 不存在`                  | 提示用户重跑 `config set` 或去控制台检查                                                                                |
| `环境 X 下未绑定默认缓存卷`               | 提示用户去控制台为该环境配置默认 Volume                                                                                 |
| `Result=CONFLICT` 反复出现                | CLI 内部已尝试回退；说明应用被并发修改，提示用户等待或换新名重新导入                                                    |
| 鉴权失败（exit 2）                        | 不重试，引导用户在本机跑 `omics login`                                                                                  |

---

## Step 6：状态查询

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

紧凑总结：`最近 N 个 scPROTEIN 批次：✅ 已完成 X / ❌ 已失败 Y / 🔄 运行中 Z`。

> ⚠️ `omics status` 列出的是**当前项目**所有批次（不限于 scPROTEIN），SKILL 转述时
> 应**优先突出 scPROTEIN 相关批次**，但不强制过滤——这是平台原生能力。

---

## Step 7：异步失败取证（debug 三段式）

**触发条件**：`omics status` 看到子任务 `Status=Failed / Aborted / Error`，或用户问「rg-xxx 为啥挂了」。

**工具**：`omics debug` 三段式（CLI 端只取证，不做规则匹配；症状判断由 SKILL 模型对照
[`references/runtime_error_kb.md`](references/runtime_error_kb.md) 决定）。

### 7.1 段 1：列批次失败子任务

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

### 7.2 段 2：单子任务现场

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

### 7.3 段 3：精确钻取某个 Job

```bash
python3 scripts/omics_cli.py debug --run <runUuid> --job <jobId> -o json
```

输出与段 2 同结构，但 `Calls` / `JobLogs` 都按 `JobId` 过滤。

### 7.4 关键守则

1. **CLI 端绝不主动调 `omics debug`** —— 用户问"为啥挂了"才用
2. **不要替用户做症状判断 + 自动改代码** —— 看到 `OOMKilled` 不要直接改 memory，要先告诉用户"目测内存不足"并询问是否调整
3. **stderr 内容是用户应用代码** —— 转述时**整段贴出来**，不要总结/二次加工
4. **修复后统一走 `omics run` 重发** —— 根据场景选择形态：
   - **form B（首次 / 用户选 A 重命名）**：走 `--public-app` 导入+运行
     ```bash
     omics run --public-app <selectedAppId> \
               --public-app-name <newName> [--nf-version <ver>] --input <fixed.json> -o json
     ```
   - **form C（断点恢复：Step 4 选项 B）**：若该应用已通过本 SKILL 的 form B 导入过，
     可直接用 `--app` 复用，无需重复导入
     ```bash
     omics run --app <existingApplicationId> --input <fixed.json> -o json
     ```
   - ⚠️ **严禁**复用**非本 SKILL 导入的**应用——那会越界，请引导用户去 `omics-task-skill`

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

### 场景 B：跑 scPROTEIN Collection 下的某子应用（标准链路）

1. `whoami` ✓ + `config show` ✓ → 复述当前配置
2. 用户："跑 scPROTEIN Stage1" 或 "做单细胞蛋白组分析"
3. **§3 展开合集**：`list public-apps --parent-app 5c63718b-... -o json` → 把子应用清单转述给用户
4. 用户挑定子应用（例如 `scPROTEIN Stage1`、`scPROTEIN Stage2`）→ 记录 `<selectedAppId>` / `<selectedAppName>` / `<selectedNfVersion>`
5. **§4 同名检查**：`list apps -o json`，匹配 `Name == <selectedAppName>`
   - 0 条命中 → 通过
   - ≥1 条命中 → 停下，请用户选「重命名」或「终止改用 omics-task-skill」
6. **二次确认**（按 §5.2 模板）
7. **一步直达运行**：
   ```bash
   python3 scripts/omics_cli.py run --public-app <selectedAppId> \
     --public-app-name <selectedAppName> --nf-version <selectedNfVersion> --name run-1 -o json
   ```
8. 解析 `RunGroupId` → 提示 `omics status <rgId>`

### 场景 C：用户要求自定义参数

1. 走完场景 B 第 1~5 步
2. 用户："参数我想改 peptide_input 文件路径"（或 protein_input、batch_label 等）
3. 收齐参数 → 写 `/tmp/run.json`
4. 二次确认（命令带 `--input /tmp/run.json`）
5. 执行 `run --public-app <selectedAppId> --input /tmp/run.json`

### 场景 D：用户问"跑别的应用"

1. **拒绝**："本 SKILL 只能帮你运行 scPROTEIN Collection 下的子应用。如需运行其他应用（本地 WDL / 其他公共应用 / 项目内已有应用），
   请使用通用版的 `omics-task-skill`。"
2. 不调任何命令。

### 场景 E：用户说"直接跑 scPROTEIN 合集"不挑子应用

1. **拒绝**：合集（APP_COLLECTION）本身不可直接运行，必须挑一个具体子应用。
2. 回到 §3 展开后让用户挑。

### 场景 F：用户混淆 Stage1 / Stage2

1. 用户："直接跑就好"——不指定阶段
2. **不替选**：明确解释 Stage1（肽段水平：不确定性评估）与 Stage2（蛋白质水平：细胞 embedding）的差异，
   并询问用户应跑哪一个，或两个按顺序跑（如要按顺序，请用户分两次发起，每次单独 run）
3. 等用户明确答复后再回到 §3 / §4 / §5

### 场景 G：业务命令报鉴权失败

1. 任何业务命令 exit 2 → SKILL 不重试
2. **告知用户去本机终端跑** `omics login` → 等用户回执
3. 重新跑原命令一次

---

## 计算资源说明

scPROTEIN Collection 子应用支持 GPU 资源（T4 及以上），可通过用户的 `--input run.json` 内 nextflow config 段配置：

- `process.resourceLabels = ["gpuType":"T4", "gpuCount": "1"]`

> SKILL 不主动替用户决定 GPU 型号与数量；如用户问"用哪个"，告知候选并询问其偏好与数据规模（特别是 Stage2 蛋白质水平 embedding 计算可能需要更高规格 GPU）。

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

# ✅ 唯一允许的 list public-apps 形态：展开本合集
cli.execute(cli.build_list_public_apps(
    parent_app="5c63718b-d24f-4a9f-9838-4177185f414a",
    output="json",
))

# ✅ 仅在导入前同名检查时使用
cli.execute(cli.build_list_apps(output="json"))

# ✅ 唯一允许的 run（AppId 来自上面合集展开后的子应用 AppId）
cli.execute(cli.build_run(
    public_app="<合集展开后的子应用AppId>",
    public_app_name="<importedName>",
    nf_version="<候选 NF 版本>",
    name="run-1",
    output="json",
))

# ✅ 用户自定义参数时
cli.execute(cli.build_run(
    public_app="<合集展开后的子应用AppId>",
    public_app_name="<importedName>",
    nf_version="<候选 NF 版本>",
    input_json="./run.json",
    output="json",
))

# ❌ 禁止：以下任何形态在本 SKILL 中均不允许
# cli.execute(cli.build_run(wdl="./hello.wdl", ...))                                        # form A
# cli.execute(cli.build_run(app="app-xxx", ...))                                            # form C
# cli.execute(cli.build_run(public_app="5c63718b-d24f-4a9f-9838-4177185f414a", ...))         # 合集本身不可 run
# cli.execute(cli.build_run(public_app="cm-other-collection-xxx", ...))                     # 其它合集
# cli.execute(cli.build_list_public_apps(output="json"))                                    # 不带 parent-app 列全平台

# ✅ 状态
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_status(run_group_id="rg-xxx", output="json"))

# ✅ debug 三段式
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))
cli.execute(cli.build_debug(run_uuid="uuid-xxx", output="json"))
cli.execute(cli.build_debug(run_uuid="uuid-xxx", job_id="plan-xxx", output="json"))
```

环境变量 `OMICS_CLI_PATH` 可覆盖 CLI 可执行文件路径。
