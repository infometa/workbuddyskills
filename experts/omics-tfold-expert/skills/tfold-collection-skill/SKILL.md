---
name: tfold-collection-skill
description: "腾讯健康组学平台(Omics) - tFold Collection (Nextflow) 公共应用合集专用运行助手。腾讯自研抗体/纳米抗体与抗原复合体结构预测深度学习模型仅服务于本合集子应用的导入与运行；其他公共应用、本地 WDL、COS 上的 NF、项目内已有应用请改用 omics-task-skill。 触发词：tFold Collection (Nextflow), tfold collection (nextflow), tfold-collection-(nextflow), tfold_collection_(nextflow), tfoldcollection(nextflow), AI 模型, ai 模型, 蛋白质结构预测, 原复合体结构预测深度学习模型, 预测深度学习模型, 跑 tFold Collection (Nextflow), run tfold collection (nextflow), 合集"
platform: 腾讯健康组学平台(Omics)
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app, collection]
version: 1.0.0
---

# tFold Collection (Nextflow) Skill (v1.0.0 · 单合集收窄版)

> **平台归属**：腾讯健康组学平台(Omics) 公共应用合集专用 SKILL。
> 本 SKILL 是 `omics-task-skill` 的**单合集收窄版**：仅服务于 `tFold Collection (Nextflow)` (NEXTFLOW) 这一个公共应用合集。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅运行 tFold Collection (Nextflow) 合集下的子应用**；任何越界都视为越权。

---

## 应用锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段                   | 值                                     |
| ---------------------- | -------------------------------------- |
| **合集名称**           | `tFold Collection (Nextflow)`                     |
| **合集 AppId（锁定）** | `807fc9ae-6197-43c0-a7a8-993c09ec1ee2`                       |
| **PublicAppId**        | `publicapp-nextflow-tfold-collection` |
| **应用类型**           | `NEXTFLOW`                     |
| **分组类型**           | `APP_COLLECTION`（合集，含多个子应用） |
| **标签**               | `行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app, collection`                     |

**应用简介**：腾讯自研抗体/纳米抗体与抗原复合体结构预测深度学习模型。
> ⚠️ 合集（`APP_COLLECTION`）本身**不能直接 `omics run`**——必须先展开找到具体子应用 AppId，
> 再用子应用 AppId 跑。这是平台规则；本 SKILL 流程已内化此约束。

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用以下 **7 条** CLI 一级命令的**收窄子集**：

```
login   whoami   config   list   run   status   debug
```

> 注意：`omics list public-apps` 仅允许以 `--parent-app 807fc9ae-6197-43c0-a7a8-993c09ec1ee2` 形态调用，
> 用于展开本合集的子应用清单；**禁止不带 `--parent-app` 调用**（那会列出全平台所有公共应用，越界）。
>
> `omics list apps` 整体禁用，但**仅允许在导入前同名检查这一处**调用。

### 🚫 严令禁止

1. **严禁运行除 tFold Collection (Nextflow) 之外的任何应用**：
   - 禁止使用 `omics run --wdl <path>`（本地 WDL）
   - 禁止使用 `omics run --app <ApplicationId>`（项目内已有应用）
   - 禁止使用 `omics run --public-app <非本合集子应用 AppId>`
   - 禁止使用 `omics run --public-app 807fc9ae-6197-43c0-a7a8-993c09ec1ee2`（合集本身不可直接 run）
   - **唯一允许**的 run 形态：`omics run --public-app <tFold Collection (Nextflow) 合集展开后的子应用 AppId> ...`
2. **严禁不带 `--parent-app` 调 `list public-apps`**
3. **严禁让用户提供合集 AppId / PublicAppId**——合集 AppId 已硬编码
4. **严禁编造其他命令**——废弃命令调用必失败
5. **严禁直接调用后端 HTTP API、SQL 等旁路通道**
6. **严禁通过组合命令模拟白名单外语义**
7. **`omics login` / `omics config set` 由用户在本机终端执行**
8. **严禁建议/提示用户「直接用 CLI 绕过 SKILL 跑」**——当用户要求运行非本合集应用时，唯一合法响应是引导使用 `omics-task-skill`，不得提供任何形式的 CLI 绕行方案

### ✅ run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须完成二次确认：

1. 拼出完整命令字符串（含所有 flag），AppId 必须来自本合集的子应用展开结果
2. 输出参数摘要表（合集 / 选定子应用 / 项目 / 环境 / 输入 / NF 版本等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复才调用
5. 用户拒绝 → 终止；模糊回复 → 再次明确询问
6. 用户追加修改 → 重拼命令 → 重走确认

### ✅ 其他命令确认要求

| 命令                                                                                                                  | 是否需要确认              |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `whoami` / `status` / `debug` / `config show / clear` / `list public-apps --parent-app ...` / `list apps`（同名检查） | 免确认（只读 / 本地操作） |
| `run`                                                                                                                 | **必须**                  |
| `login` / `config set`                                                                                                | 不调，引导用户本机执行    |

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义     | SKILL 处理                                                                              |
| ------ | -------- | --------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                             |
| `1`    | 业务错误 | 把 stderr 转述给用户；如果是"未配置"错误，引导用户去本机跑 `omics config set`           |
| `2`    | 鉴权失败 | 引导用户去本机跑 `omics login`，不要循环重试                                          |

---

## Step −1：CLI 存在性检查

任何业务命令之前，先确认本机已安装 `omics-platform-cli`：

```bash
python3 scripts/omics_cli.py whoami
```

若抛出 `FileNotFoundError` / shell 提示 `command not found: omics` → 视为 CLI 未安装：

> 检测到本机尚未安装 `omics-platform-cli`，无法继续。
>
> 请前往下载页安装：
> https://cnb.cool/tencenthealthcareomics/omics-platform-cli
>
> 安装完成后告诉我「已安装」，我会验证后继续。

---

## Step 0：鉴权与配置双重检查

### Step 0.1：whoami
```bash
python3 scripts/omics_cli.py whoami
```
退出码 0 → Step 0.2；退出码 2 → Step 1。

### Step 0.2：config show
```bash
python3 scripts/omics_cli.py config show -o json
```
- 退出码 0 + JSON 字段齐全 → 进入业务流程，复述当前配置给用户
- 退出码 1 → Step 2（配置引导）

---

## Step 1：登录引导

检测到会话失效时：

> 请在你**本机的终端**中执行：`omics login`
>
> 完成后告诉我「已登录」。

不调 login 子进程，不循环 whoami，不复制授权 URL。

---

## Step 2：配置引导

> 请在你**本机的终端**中执行：`omics config set`
>
> 完成后告诉我「已配置」。

---

## Step 3：展开本合集子应用（**必经第一步**）

```bash
python3 scripts/omics_cli.py list public-apps \\
  --parent-app 807fc9ae-6197-43c0-a7a8-993c09ec1ee2 -o json
```

> ⚠️ `--parent-app` 值**固定**为 tFold Collection (Nextflow) 的 AppId，不接受替换。

### 3.1 转述给用户

> tFold Collection (Nextflow) 包含以下子应用，请挑一个具体的子流程：
>
> ① **<AppName 1>** (`<AppId 1>`) — <AppDesc> · | **NF 版本候选** | `
> ...
>
> 你想跑哪一个？

### 3.2 记录字段

- `<selectedAppId>` → `--public-app` 入参
- `<selectedAppName>` → `--public-app-name` 默认候选 + 同名检查 candidateName
- `<selectedAppType>` → **从展开结果的 `Apps[].AppType` 获取，不得使用合集的 AppType（NEXTFLOW）**
- `<selectedNfVersion>` → 当 `<selectedAppType> == "NEXTFLOW"` 时，从 `NextflowVersion[]` 中让用户挑；否则**不传此参数**

---

## Step 4：导入前同名检查 + 快照记录（**必经**，必须才能导入）

```bash
python3 scripts/omics_cli.py list apps -o json
```

仅在导入前同名检查时允许调用此命令。

| 用途 | 说明 |
|------|------|
| **快照记录（先执行）** | **必须**先将返回的全部 `ApplicationId` 存储为「预存应用快照」，用于后续 **`omics run` 命令接口报错**时判定孤儿应用来源 |
| **同名检查（后执行）** | 检查是否有与 `<selectedAppName>`（或用户指定的 `--public-app-name`）同名的已有应用 |

### 4.1 同名检查循环（⚠️ 必须通过，循环直到名称唯一）

> **设计意图**：`--public-app` 会在项目中创建新的应用记录。如果项目已有同名应用，会导致运行失败。
> 因此导入前必须确保名称唯一，通过**引导用户重命名**解决冲突（非拒绝）。

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | ✅ 通过检查，用当前名称作为 `--public-app-name` 继续下一步                                                  |
| **≥ 1 条命中** | **必须停下来**，展示冲突信息 + 引导用户为待导入应用指定新名称；用户输入新名字后**重新执行同名检查**（循环） |

#### 同名检查交互模板

```
────────────────────────────────────────
同名检查：<selectedAppName>（本合集子应用）
────────────────────────────────────────

待导入名称: {candidateName}
检查结果: ⚠️ 发现同名应用

项目中已存在的同名应用:
  名称: {ConflictingAppName}
  AppId: {ConflictingApplicationId}

请为即将导入的 <selectedAppName> 指定一个不同的名称（将用作 --public-app-name）：
• 输入新名称，如 <selectedAppName>_v2、my_<selectedAppName>
• 或输入「取消」终止本次操作
>
```

**用户响应处理**：

| 用户输入 | 行为 |
|---------|------|
| 输入新名称 | 用新名称重新执行同名检查（回到检查入口） |
| 新名称仍同名 | 再次展示冲突信息，继续引导重命名 |
| 新名称无同名 | ✅ 通过检查，使用该名称继续 |
| 「取消」/「终止」 | 终止本次运行操作（不删除/修改任何项目已有应用） |

#### 同名检查守则

- **必须先记录快照再做同名判断**
- **必须循环直到名称唯一**——不允许跳过同名检查直接 run
- **不得自动生成名称替代用户选择**
- **不得删除/修改项目已有应用**——只做读操作 + 引导重命名

---

## Step 5：运行（仅形态 B · 公共应用）

```bash
omics run --public-app <selectedAppId> \\
          --public-app-name <importedName> \\
          {'[--nf-version <selectedNfVersion>] \\' if selectedAppType == "NEXTFLOW" else '# NEXTFLOW 类型必填，其他类型不传此参数'} \
          [--input <path>] \\
          [--name <runName>] \\
          -o json
```

### 5.1 运行参数模板（InputTemplate 自动填充）

1. **默认行为**：未传 `--input` 参数时，CLI 自动取该子应用的第一个 InputTemplate 作为 baseline
2. **用户覆盖**：传入 `--input` 参数时，自定义值覆盖对应字段；未覆盖字段保持默认值
3. **模板来源**：InputTemplate 数据来自公共应用注册时的模板定义

### 5.2 完整流程

1. Step 0 鉴权 + 配置检查
2. Step 3 展开合集子应用 → 用户挑
3. Step 4 导入前同名检查
4. 二次确认（按 §5.3 模板）
5. 执行 `omics run`

### 5.3 二次确认模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用（form B，自动模板）        │
  │ 来源合集    : tFold Collection (Nextflow)                   │
  │ 子应用      : <selectedAppName>                   │
  │ AppId       : <selectedAppId>                     │
  │ 子应用类型  : <selectedAppType>                   │  ← 来自展开结果，非合集 AppType
  │ {'NF 版本     : <selectedNfVersion>' if selectedAppType == 'NEXTFLOW' else ''}  │
  │ 导入后命名  : <importedName>                      │
  │ 项目/环境   : ← config                            │
  └──────────────────────────────────────────────────┘
完整命令: omics run --public-app <selectedAppId> ...

确认无误请回复「确认 / 继续 / y」
```

### 5.4 PARAM_MERGE_FAILED 处理

解析 `Report.MissingRequired / TypeErrors / ExtraFields`，引导用户补值后 `--input <path>` 重跑。

### 5.5 流水线失败提示

| 错误                                      | 处置建议                                                                                                                   |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `PARAM_MERGE_FAILED`                     | 解析缺失字段，引导补值后通过 `--input` 传回重跑                                          |
| `MISSING_NF_VERSION`                      | 让用户从 §3 展开结果中该子应用的 `NextflowVersion[]` 列表挑一个                                                    |
| `公共应用 X 是一个合集` / `AppId 不存在`  | 核对 `--public-app` 是否传成了合集 AppId？合集 AppId（`807fc9ae-6197-43c0-a7a8-993c09ec1ee2`）不可作为 run 的 `--public-app` |
| 鉴权失败（exit 2）                        | 引导用户在本机跑 `omics login`                                                                                             |

### 5.6 DUPLICATE_APP_NAME 智能复用（**必经**）

`omics run --public-app` 是**非原子操作**：服务端可能在返回错误响应前已创建应用记录。
当 **`omics run` 命令接口报错**（CLI 非零退出码 / API 返回错误码）并返回 `DUPLICATE_APP_NAME` 时，**必须**按以下流程处理。

> **前置条件**：此流程**仅在已完成 §4 同名检查循环（名称已确认唯一）并执行 run 后触发**。
> ⚠️ **重要区分**："命令接口报错"指 `omics run` CLI 本身执行失败，**不包括**任务提交成功后运行结果失败（如流水线执行出错、OOMKilled 等）。

#### 5.6.1 判定孤儿 vs 老应用

取出响应中的 `ConflictApplicationId`，查询 **Step 4 预存快照**：

| ConflictApplicationId ∈ 预存快照? | 判定 | SKILL 行为 |
|---|---|---|
| **Yes** | 项目已有老应用（理论上不应发生，因同名检查已通过） | 展示平台 Options（rename / reuse / abort）给用户选择 |
| **No** | **本次 `omics run` 命令新建的孤儿应用**（命令的非原子性导致先建后报错） | **自动切换为 `--app` 复用模式** ✅ |

#### 5.6.2 自动复用模式（仅限孤儿应用场景）

```
检测到同名孤儿应用（`omics run` 命令执行过程中创建应用记录但命令本身报错），自动复用。
  冲突应用: <ConflictApplicationId>
  原因: 该 AppId 不在 run 命令执行前的预存快照中，判定为本次 run 命令新建的孤儿

  自动切换命令：omics run --app <ConflictApplicationId> ...
```

用 `--app <ConflictApplicationId>` 替代 `--public-app` 重新发起运行。

#### 5.6.3 智能复用守则

- **严禁自动删除应用**——只做命令形态切换
- **严禁跳过快照直接重试**——会导致无法区分新老应用
- **复用仍失败时终止**——引导用户手动检查或联系平台客服
- **快照必须每次重新获取**——不得缓存上一次的结果

> ⚠️ **复用边界守则**：
> - ✅ 允许自动复用：**仅限上述孤儿应用场景**（已通过同名检查 → `omics run` **命令接口报错** → 冲突应用 ∉ 快照）
> - ❌ 禁止复用：任何其他场景下使用 `--app` 运行项目已有应用（包括用户明确要求时）
> - ❌ **禁止将"任务运行结果失败"（如流水线执行出错、OOMKilled）误判为命令接口报错**——后者不涉及孤儿应用，不得触发 `--app` 复用

---

## Step 6：状态查询

```bash
python3 scripts/omics_cli.py status -o json
python3 scripts/omics_cli.py status rg-xxx -o json
```

### 6.1 运行结果目录提醒（outdir 场景）

当运行参数中包含 `outdir`（输出目录）字段时，**必须在任务完成后主动提醒用户查看该目录**。

**触发条件**：
- `--input` 参数或 InputTemplate 默认值中包含 `outdir` 字段
- 任务执行完成（无论成功或失败）

**提醒时机**：
- **同步任务**：`omics run` 命令返回后立即提醒（无论 exit code）
- **异步任务**：`omics status` 查询到终态（SUCCESS/FAILED）后提醒

**提醒模板**：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 运行结果目录提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

任务已完成，运行结果已输出至：
  {outdir 完整路径}

请前往该目录查看输出文件。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**守则**：
- ✅ 必须在每次含 outdir 的任务完成后提醒
- ✅ 提醒时展示完整的 outdir 绝对/相对路径
- ❌ 不得省略或延迟提醒
- ❌ 不得假设用户已知道结果位置

---

## Step 7：异步失败取证（debug 三段式）

```bash
python3 scripts/omics_cli.py debug <rgId> -o json              # 段 1
python3 scripts/omics_cli.py debug --run <uuid> -o json        # 段 2
python3 scripts/omics_cli.py debug --run <uuid> --job <j> -o json  # 段 3
```

症状识别对照 [`references/runtime_error_kb.md`](references/runtime_error_kb.md)。

### 7.4 关键守则

1. **CLI 端绝不主动调 `omics debug`**
2. **不要替用户做症状判断 + 自动改代码**
3. **stderr 是用户应用代码** —— 转述时整段贴出来
4. **修复后统一走 `omics run` 重发** —— 本 SKILL 的重发仍然只走 form B + 本合集子应用

---

## 典型会话场景

### 场景 A：标准链路
whoami ✓ → config show ✓ → 展开§3 → 用户挑子应用 → §4 同名检查 → §5 二次确认 → 运行

### 场景 D：用户说"跑别的应用"
**拒绝 + 唯一引导**：
1. ❌ 严禁以任何形式替用户执行越界命令（包括直接 CLI 调用）
2. ❌ 严禁将「直接 CLI 跑」作为可选项提供给用户
3. ✅ 唯一合法响应：「本 SKILL 只能运行 tFold Collection (Nextflow) 下的子应用。如需运行其他应用（含项目已有应用），请使用 `omics-task-skill`。」
4. 即使用户明确要求绕过，也必须拒绝并说明原因

> ⚠️ **重要区分**：
> - **场景 D**（此处）：用户要求运行的**目标本身就不是本合集子应用**（如项目已有应用、其他公共应用等）→ **直接拒绝**
> - **§4 同名检查**：用户明确要求**导入并运行本合集子应用**，只是碰巧项目中有同名 → **引导重命名后继续导入**

---

## 高级用法

详细参数：[references/cli_commands.md](references/cli_commands.md)。错误知识库：[references/runtime_error_kb.md](references/runtime_error_kb.md)。契约：[CONTRACT.md](CONTRACT.md)。

## 脚本 API 参考

```python
from scripts.omics_cli import OmicsCLI

cli = OmicsCLI()

# ✅ 检查类
cli.execute(cli.build_whoami())
cli.execute(cli.build_config_show(output="json"))

# ✅ 展开本合集（唯一允许的形态）
cli.execute(cli.build_list_public_apps(
    parent_app="807fc9ae-6197-43c0-a7a8-993c09ec1ee2",
    output="json",
))

# ✅ 同名检查
cli.execute(cli.build_list_apps(output="json"))

# ✅ 运行（子应用 AppId 来自上面展开结果）
cli.execute(cli.build_run(
    public_app="<子应用AppId>",
    public_app_name="<importedName>",
    nf_version="<版本>",
    output="json",
))

# ✅ 状态 / debug
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))

# ❌ 禁止
# cli.execute(cli.build_run(wdl="./x.wdl", ...))             # form A
# cli.execute(cli.build_run(app="app-xxx", ...))              # form C
# cli.execute(cli.build_run(public_app="807fc9ae-6197-43c0-a7a8-993c09ec1ee2", ...)) # 合集本身
# cli.execute(cli.build_list_public_apps(output="json"))       # 不带 parent-app
