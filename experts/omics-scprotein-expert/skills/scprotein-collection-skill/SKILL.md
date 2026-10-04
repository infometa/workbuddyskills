---
name: scprotein-collection-skill
description: "scPROTEIN 基于图神经网络，对单细胞蛋白组数据去批次效应降噪、不确定性估计、生成 embedding 与细胞类型表征，含 stage1/stage2 两子应用。"
triggers: [图神经网络, scPROTEIN Collection (Nextflow), scprotein collection (nextflow), scprotein-collection-(nextflow), scprotein_collection_(nextflow), scproteincollection(nextflow), 单细胞与多组学基础模型, 跑 scPROTEIN Collection (Nextflow), run scprotein collection (nextflow)]
platform: 腾讯健康组学平台(Omics)
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app, collection]
version: 1.0.0
---

# scPROTEIN Collection (Nextflow) Skill (v1.0.0 · 单合集收窄版)

> **平台归属**：腾讯健康组学平台(Omics) 公共应用合集专用 SKILL。
> 本 SKILL 是 `omics-task-skill` 的**单合集收窄版**：仅服务于 `scPROTEIN Collection (Nextflow)` (NEXTFLOW) 这一个公共应用合集。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅运行 scPROTEIN Collection (Nextflow) 合集下的子应用**；任何越界都视为越权。
>
> ⚠️ **子应用 AppId 已在生成时硬编码到本 SKILL 中**（见下方子应用清单）。
> 运行时无需再执行 `list public-apps --parent-app` 展开操作，直接根据用户输入匹配子应用。

---

## 合集锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段                   | 值                                     |
| ---------------------- | -------------------------------------- |
| **合集名称**           | `scPROTEIN Collection (Nextflow)`                     |
| **合集 AppId（锁定）** | `5c63718b-d24f-4a9f-9838-4177185f414a`                       |
| **应用类型**           | `NEXTFLOW`                     |
| **分组类型**           | `APP_COLLECTION`（合集，含多个子应用） |
| **子应用数量**         | 2 个（见下方清单）      |

**应用简介**：scPROTEIN 基于图神经网络，对单细胞蛋白组数据去批次效应降噪、不确定性估计、生成 embedding 与细胞类型表征。
> ⚠️ 合集（`APP_COLLECTION`）本身**不能直接 `omics run`**——必须先展开找到具体子应用 AppId，
> 再用子应用 AppId 跑。这是平台规则；本 SKILL 流程已内化此约束。

---

## 子应用清单（**硬编码 · 禁止运行时修改**）

> 以下子应用信息在 SKILL 生成时由平台 API 获取并写死。
> 如合集新增/删除子应用，需重新生成本 SKILL。

| 序号 | 子应用名称 | 类型 | AppId（硬编码） | NF 版本候选 | 简介 |
| ---- | ---------- | ---- | --------------- | ----------- | ---- |
| 1 | `scPROTEIN_stage1` | `NEXTFLOW` | `bfa72f47-c230-41eb-806f-973fe00a8cda` | v24.04.3 | scPROTEIN stage1 |
| 2 | `scPROTEIN_stage2` | `NEXTFLOW` | `58a00e72-116b-4bd1-bfee-ee22763f21e5` | v24.04.3 | scPROTEIN stage2 |

---

## 能力边界

> ⚠️ **触发时必须强制读取** `references/cli-whitelist.md`（完整命令白名单与 Flag 约束）和 `references/skill-template.md`（越界响应模板 §2.3）。

本 SKILL 仅服务于 `scPROTEIN Collection (Nextflow)` 合集（AppId: `5c63718b-d24f-4a9f-9838-4177185f414a`）。
允许调用的命令（完整 Flag 约束见 **[references/cli-whitelist.md §2](references/cli-whitelist.md)**）：

```
version / login / whoami
config show / config set / config clear
list region / list project / list env / list cos-bucket
list apps --type <selectedAppType>   # 仅用于导入前同名检查
run --public-app <子应用AppId> --public-app-name <name> [--nf-version] [--input] [--name]
    ⚠️ --public-app 必须来自下方硬编码子应用清单，不可使用合集 AppId
status / debug
```

未列出的命令一律不得调用。如需运行本合集以外的应用，请使用 `omics-task-skill`。

### run 前置确认（必经）

`omics run` 执行前必须：
1. 展示完整命令 + 参数摘要（合集/子应用/导入名/NF版本/项目环境）
2. 询问用户确认（y / 确认 / 继续），收到明确肯定才执行
3. 模糊回复 → 再次询问；用户修改参数 → 重拼命令 → 重走确认

---

## 退出码 & 鉴权失败处理

| 退出码 | 含义     | SKILL 处理                                                                              |
| ------ | -------- | --------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                             |
| `1`    | 业务错误 | 把 stderr 转述给用户；如果是"未配置"错误，引导用户去本机跑 `omics config set`           |
| `2`    | 鉴权失败 | 引导用户去本机跑 `omics login`，不要循环重试                                          |

---

## Step −1：CLI 存在性检查

> 📖 完整流程（含三平台自动安装方案）参见：
> **[references/omics-cli-setup.md § Step -1 & §A](references/omics-cli-setup.md)**

```bash
python3 scripts/omics_cli.py version
```

| 结果 | 处理 |
|------|------|
| exit 0 | CLI 已安装，继续 Step 0 |
| `FileNotFoundError` / `command not found` | 提供手动安装链接或 SKILL 自动安装，详见 [omics-cli-setup.md §A](references/omics-cli-setup.md) |

---

## Step 0：鉴权与配置双重检查

> 📖 详细流程参见：**[references/omics-cli-setup.md §D](references/omics-cli-setup.md)**

### Step 0.1：whoami
```bash
python3 scripts/omics_cli.py whoami
```
退出码 0 → 解析用户类型（`Role == "trial_user"` → C端；其他 → B端），继续 Step 0.2；退出码 2 → Step 1。

### Step 0.2：config show
```bash
python3 scripts/omics_cli.py config show -o json
```
- 退出码 0 + JSON 字段齐全（Region / ProjectId / EnvironmentId / CosBucketName 均非空）→ 复述当前配置给用户，进入 Step 0.3（C端）或直接进入业务流程（B端）
- 退出码 1 或任一字段为空 → Step 2（配置引导）

### Step 0.3：体验配额首检（⚠️ **仅 C端用户，登录/配置就绪后必执行，不可跳过**）

> **触发条件**：Step 0.2 通过 **且** 用户类型为 C端体验用户（`Role == "trial_user"`）。
> **强制性**：不可跳过，不受用户指令影响。此为会话内第一次配额检查（首检）。

```bash
python3 scripts/omics_cli.py quota -o json
```

解析 `RemainDays`（剩余体验天数）和 `TodayRemainingRuns`（今日剩余运行次数），**按以下四档执行**：

| 场景 | 条件 | 行为 |
|------|------|------|
| 已到期 | `RemainDays == 0` | **阻断** — 展示到期提示后终止，不进入业务流程 |
| 今日次数耗尽 | `TodayRemainingRuns == 0` 且 `RemainDays > 0` | **阻断** — 展示次数用完提示后终止，不进入业务流程 |
| 临近到期 | `RemainDays <= 3` 且 `RemainDays > 0` 且 `TodayRemainingRuns > 0` | **提示后继续** — 展示临近到期提示，直接进入业务流程 |
| 正常体验 | `RemainDays > 3` 且 `TodayRemainingRuns > 0` | **简短提示后继续** — 一行配额信息，直接进入业务流程 |

**话术模板（四档，必须完整执行）**：

**场景一（已到期）— 阻断**：
```
⏰ 温馨提示：您的免费体验已到期，将无法继续运行任务，历史结果仍可查看。
   您可开通组学平台正式版，体验更多功能。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
🌐 了解平台 → https://cloud.tencent.com/product/omics
```

**场景二（今日次数耗尽）— 阻断**：
```
⏰ 温馨提示：今日免费体验运行已用完，明日 00:00 重置。
   您可开通组学平台正式版，享受无限制运行。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
```

**场景三（临近到期）— 提示后继续**：
```
⏰ 温馨提示：您的免费体验即将到期（剩余 {RemainDays} 天）。
   到期后将无法继续运行任务，历史结果仍可查看。
   您可开通组学平台正式版，体验更多功能。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb

📊 今日剩余运行次数：{TodayRemainingRuns} 次
```

**场景四（正常体验）— 简短提示后继续**：
```
📊 免费体验版配额：今日剩余 {TodayRemainingRuns} 次 · 剩余 {RemainDays} 天
```

> ⚠️ **守则**：阻断时展示话术后立即终止，不进入任何业务逻辑；继续时无需等待用户确认，直接进入下一步。
> 这是首检。每次实际提交 `omics run` 前还会再次执行运行前配额检查（Step 5.5），确保提交时配额仍充足。

---

## Step 1：登录授权

> 📖 完整流程参见：**[references/omics-cli-setup.md §B](references/omics-cli-setup.md)**

SKILL **主动触发**：

```bash
python3 scripts/omics_cli.py login
```

- CLI 启动 `localhost:18000`，**自动打开浏览器**到 OAuth 授权页
- 用户点击「确认授权」完成，无需命令行操作
- 最长等待 120s；完成后轮询 `whoami` 确认登录状态（最多 3 次）

---

## Step 2：配置引导

> 📖 完整流程（B端/C端分流、无项目/无环境/无桶异常处理）参见：
> **[references/omics-cli-setup.md §C](references/omics-cli-setup.md)**

| 用户类型 | 流程 |
|---------|------|
| 🟢 B端正式用户 | `list region` → 选地域 → 并行 `list project`+`list env` → 选项目+环境 → 临时写入 → `list cos-bucket` → 选桶 → 正式 `config set` |
| 🔵 C端体验用户 | 地域固定 `ap-guangzhou`，项目自动取第一条，环境/桶使用共享池占位符 |

**B端用户异常分支（⚠️ 引导语强制使用，不得改写/替换/省略引导 URL）**：
- **无可用项目**（`list project` 返回空）→ 提示用户前往组学平台创建项目后回复「已就绪」：
  > 👉 https://omics.qq.com/platform/project/list
- **无可用环境**（`list env` 返回空）→ 提示用户前往控制台创建环境后回复「已就绪」：
  > 👉 https://console.cloud.tencent.com/omics/env/env-list
- **无绑定存储桶**（`list cos-bucket` 返回空）→ 提示用户前往控制台为当前环境绑定 COS 桶后回复「已绑定」：
  > 👉 https://console.cloud.tencent.com/omics/env/env-list（详见 [omics-cli-setup.md §C-B-no-bucket](references/omics-cli-setup.md)）

---

## Step 3：子应用选择（**从硬编码清单中匹配，无需展开**）

> ⚠️ **无需调用 `list public-apps`**——子应用 AppId 已在生成时写死，直接从本 SKILL 清单中选择。

### 3.1 根据用户输入匹配子应用

根据用户在对话中提到的信息（应用名、编号、功能描述等），从上方**子应用清单**中匹配最合适的子应用：

**匹配规则（优先级从高到低）**：
1. **精确编号**：用户直接说"选 2"/ "第三个"/ "编号 2" → 按序号直接选
2. **精确名称**：用户提到的名称与 AppName 完全匹配（大小写不敏感）
3. **部分名称/关键词**：用户提到的关键词包含在 AppName 中
4. **功能描述**：根据用户描述的功能需求，推断最匹配的子应用

**匹配结果处理**：
- **唯一匹配** → 向用户展示匹配结果并询问确认
- **多个匹配** → 列出候选项，让用户选择
- **无匹配** → 展示完整子应用清单，引导用户选择

### 3.2 展示子应用清单（无匹配时或首次使用时）

若无法自动匹配，或用户要求查看完整列表：

> scPROTEIN Collection (Nextflow) 包含以下子应用，请选择一个：
>
  1. **scPROTEIN_stage1** (`NEXTFLOW` · NF版本: v24.04.3) — scPROTEIN stage1
  2. **scPROTEIN_stage2** (`NEXTFLOW` · NF版本: v24.04.3) — scPROTEIN stage2
>
> 请输入编号或应用名称进行选择。

### 3.3 记录字段

用户确认后记录：

- `<selectedAppId>` → 来自上方子应用清单的 AppId，**不得使用合集本身的 AppId（5c63718b-d24f-4a9f-9838-4177185f414a）**
- `<selectedAppName>` → 来自上方子应用清单的 AppName
- `<selectedAppType>` → 来自上方子应用清单的 AppType（**不得使用合集的 AppType NEXTFLOW**）
- `<selectedNfVersion>` → 当 `<selectedAppType> == "NEXTFLOW"` 时，从子应用清单的 `NextflowVersions[]` 中让用户挑；否则**不传此参数**

---

## Step 4：运行前准备（**必经**）

### 4.1 导入前同名检查（**必须才能导入**）

```bash
python3 scripts/omics_cli.py list apps --type <selectedAppType> -o json
```

> ⚠️ **`--type` 值必须来自子应用清单中 `<selectedAppType>`**。
> **禁止使用合集本身的 AppType（NEXTFLOW）**。
> **禁止不带 `--type` 调用**。

用途：检查是否有与 `<selectedAppName>`（或用户指定的 `--public-app-name`）同名的已有应用。

#### 同名检查循环（⚠️ 必须通过，循环直到名称唯一）

> **设计意图**：`--public-app` 会在项目中创建新的应用记录。如果项目已有同名应用，会导致运行失败。
> 因此导入前必须确保名称唯一，通过**引导用户重命名**解决冲突（非拒绝）。

查找 `Name == <selectedAppName>`（或用户提供的自定义名）：

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | ✅ 通过检查，用当前名称作为 `--public-app-name` 继续下一步                                                  |
| **≥ 1 条命中** | **必须停下来**，展示冲突信息 + 引导用户为待导入应用指定新名称；用户输入新名字后**重新执行同名检查**（循环） |

##### 同名检查交互模板

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

##### 同名检查守则

- **必须先记录快照再做同名判断**——快照是后续孤儿复用的判定基准
- **必须循环直到名称唯一**——不允许跳过同名检查直接 run
- **不得自动生成名称替代用户选择**
- **不得删除/修改项目已有应用**——只做读操作 + 引导重命名

### 4.2 确认运行参数

根据子应用清单和用户选择，确认以下参数：

| 参数 | 来源 | 说明 |
|------|------|------|
| `--public-app` | `<selectedAppId>`（来自硬编码清单） | 必须来自本 SKILL 子应用清单 |
| `--public-app-name` | 用户指定 / 默认 `<selectedAppName>` | 导入到项目时的应用名 |
| `--nf-version` | `<selectedNfVersion>` | 仅当 selectedAppType=="NEXTFLOW" 时必传 |
| `--input` | 可选 | 用户自定义参数 JSON |

---

## Step 5：运行（仅形态 B · 公共应用）

根据子应用清单中硬编码的 `<selectedAppType>` 区分构造入参：

**WDL 类型**（`selectedAppType == "WDL"`）：

```bash
omics run --public-app <selectedAppId> \\
          --public-app-name <importedName> \\
          --app-type <selectedAppType> \\
          [--input <path>] \\
          [--name <runName>] \\
          -o json
```

**NEXTFLOW 类型**（`selectedAppType == "NEXTFLOW"`）：

```bash
omics run --public-app <selectedAppId> \\
          --public-app-name <importedName> \\
          --app-type <selectedAppType> \\
          --nf-version <selectedNfVersion> \\
          [--input <path>] \\
          [--name <runName>] \\
          -o json
```

> **入参构造规则（基于硬编码 AppType）**：
> - `<selectedAppId>` 来自本 SKILL 子应用清单，**不得使用合集本身的 AppId（5c63718b-d24f-4a9f-9838-4177185f414a）**
> - `<selectedAppType>` 来自本 SKILL 子应用清单，**不得使用合集本身的 AppType（NEXTFLOW）**；通过 `--app-type` 传给 CLI
> - `--nf-version`：**NEXTFLOW 类型必传**；WDL 类型不传（CLI 会忽略该参数）
> - `--app-type`：**必传**，值来自硬编码子应用清单的 `selectedAppType`，由 SKILL 内部构造命令时自动填入

### 5.1 运行参数模板（InputTemplate 自动填充）

1. **默认行为**：未传 `--input` 参数时，CLI 自动取该子应用的第一个 InputTemplate 作为 baseline
2. **用户覆盖**：传入 `--input` 参数时，自定义值覆盖对应字段；未覆盖字段保持默认值
3. **模板来源**：InputTemplate 数据来自公共应用注册时的模板定义

### 5.2 完整流程

1. Step 0 鉴权 + 配置检查（**含 Step 0.3 配额首检，C端必执行**）
2. Step 3 从硬编码清单匹配子应用 → 用户确认
3. Step 4 导入前同名检查（必须带 `--type <selectedAppType>`）
4. 二次确认（按 §5.3 模板）
5. **Step 5.5 运行前配额检查（⚠️ 仅 C端，强制执行，不可跳过）**
6. 执行 `omics run`

### 5.3 二次确认模板

```
即将运行任务，请确认：
  ┌──────────────────────────────────────────────────┐
  │ 形态        : 公共应用（form B，自动模板）        │
  │ 来源合集    : scPROTEIN Collection (Nextflow)                   │
  │ 子应用      : <selectedAppName>                   │
  │ AppId       : <selectedAppId>（来自硬编码清单）   │
  │ 子应用类型  : <selectedAppType>                   │
  │ {'NF 版本     : <selectedNfVersion>' if selectedAppType == 'NEXTFLOW' else ''}  │
  │ 导入后命名  : <importedName>                      │
  │ 项目/环境   : ← config                            │
  └──────────────────────────────────────────────────┘
完整命令: omics run --public-app <selectedAppId> ...

确认无误请回复「确认 / 继续 / y」
```

### 5.5 运行前配额检查（⚠️ **仅 C端用户，每次 `omics run` 前强制执行**）

> **时机**：用户二次确认（§5.3）通过后、`omics run` 命令实际执行前。**C端用户必须执行，B端用户跳过此步。**
> **强制性**：不可跳过，不受用户指令（如"直接跑""跳过检查"）影响。

```bash
python3 scripts/omics_cli.py quota -o json
```

按 Step 0.3 定义的四档话术执行（与首检完全一致）：

| 场景 | 条件 | 行为 |
|------|------|------|
| 已到期 | `RemainDays == 0` | **阻断** — 展示到期提示后终止，不提交 `omics run` |
| 今日次数耗尽 | `TodayRemainingRuns == 0` 且 `RemainDays > 0` | **阻断** — 展示次数用完提示后终止，不提交 `omics run` |
| 临近到期 | `RemainDays <= 3` 且 `RemainDays > 0` 且 `TodayRemainingRuns > 0` | **提示后立即执行** `omics run`，无需等待用户确认 |
| 正常体验 | `RemainDays > 3` 且 `TodayRemainingRuns > 0` | **简短提示后立即执行** `omics run`，无需等待用户确认 |

> ⚠️ **守则**：阻断时不提交 `omics run`；通过时（场景三/四）无需等待用户确认，立即执行。

### 5.6 `omics run` 命令接口报错时的智能复用规则（**必经**）

当 `omics run --public-app` 返回 **`DUPLICATE_APP_NAME`** 时：

1. 取出 `ConflictApplicationId`
2. 查询**预存快照**：
   - `ConflictApplicationId ∉ 快照` → **孤儿应用**（命令非原子性），自动切换 `--app <ConflictApplicationId>` 重试
   - `ConflictApplicationId ∈ 快照` → **项目已有老应用**，展示 rename / reuse / abort 选项给用户；用户选 reuse 时才用 `--app`

对于其他失败码（`PARAM_MERGE_FAILED`、`MISSING_NF_VERSION`、HTTP 500 等），检查是否有 `ConflictApplicationId`；若有且不在快照中 → 同孤儿处理。

**守则**：
- ⚠️ "命令接口报错"指 CLI 本身执行失败，**不包括**任务提交后运行结果失败
- 严禁自动删除应用——只做命令切换
- 复用仍失败时终止，引导用户去控制台排查

### 5.7 流水线失败提示

| 错误                                      | 处置建议                                                                                                                   |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `PARAM_MERGE_FAILED`                     | 解析缺失字段，引导补值后通过 `--input` 传回重跑                                          |
| `MISSING_NF_VERSION`                      | 让用户从子应用清单中该子应用的 `NextflowVersions[]` 列表挑一个                                                    |
| `公共应用 X 是一个合集` / `AppId 不存在`  | 核对 `--public-app` 是否传成了合集 AppId？合集 AppId（`5c63718b-d24f-4a9f-9838-4177185f414a`）不可作为 run 的 `--public-app` |
| 鉴权失败（exit 2）                        | 引导用户在本机跑 `omics login`                                                                                             |

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
whoami ✓ → config show ✓ → Step 3 匹配子应用 → Step 4 同名检查 → Step 5 二次确认 → 运行

### 场景 B：用户直接说出子应用名
用户说「帮我跑 scPROTEIN Collection (Nextflow) 里的 XXX」→ Step 3 精确匹配 → 确认 → 同名检查 → 运行

### 场景 D：用户说"跑别的应用"
**拒绝 + 唯一引导**：
1. ❌ 严禁以任何形式替用户执行越界命令（包括直接 CLI 调用）
2. ❌ 严禁将「直接 CLI 跑」作为可选项提供给用户
3. ✅ 唯一合法响应：「本 SKILL 只能运行 scPROTEIN Collection (Nextflow) 下的子应用。如需运行其他应用（含项目已有应用），请使用 `omics-task-skill`。」
4. 即使用户明确要求绕过，也必须拒绝并说明原因

> ⚠️ **重要区分**：
> - **场景 D**（此处）：用户要求运行的**目标本身就不是本合集子应用**（如项目已有应用、其他公共应用等）→ **直接拒绝**
> - **§4 同名检查**：用户明确要求**导入并运行本合集子应用**，只是碰巧项目中有同名 → **引导重命名后继续导入**

---

## 高级用法

### §COS 上传流程（本地文件 → COS 路径）

> **适用场景**：当运行参数需要**本地生成的文件**作为输入时（如 AI 生成的蛋白质序列、自定义参考数据等），
> 应用运行容器无法直接读取 agent 本地文件系统，必须先将文件上传到用户绑定的 COS 桶。

#### 触发条件

以下情况**必须**走 COS 上传流程：
1. 用户要求使用 AI 生成的文件（如"生成测试蛋白质序列"、"生成随机 FASTA 文件"等）作为运行参数
2. 参数值是**本地文件路径**（如 `/tmp/protein.fasta`、`./input.txt`）
3. 参数来源是其他 SKILL 的输出文件（如 cdgpt-collection-skill 生成的序列文件）

#### 上传步骤

```
Step C.1: 确认上传需求
  │
  ├─ 识别到参数值为本地文件路径
  └─ 向用户确认："检测到输入参数为本地文件，需要先上传至 COS。目标 COS 路径？（默认: uploads/<filename>）"
      │
      ▼
Step C.2: 执行 COS 上传
  │
  ├─ 命令: omics cos upload --file <localPath> --cos-path <cosPath>
  │
  ├─ 成功 → 解析返回的完整 COS URL（cos://bucket-name/... 或 https://...）
  │
  └─ 失败 → 转述错误信息，引导用户检查：
     · 本地文件是否存在
     · COS 路径格式是否正确
     · 是否已执行 omics config set 配置环境（含 CosBucketName）
      │
      ▼
Step C.3: 替换参数值
  │
  ├─ 将原本地文件路径替换为返回的 COS URL
  └─ 使用新参数值继续 run 流程
```

#### 命令示例

```bash
# 上传单个文件
python3 scripts/omics_cli.py cos upload \
  --file /tmp/generated_protein.fasta \
  --cos-path uploads/protein_sequence.fasta \
  -o json

# 返回示例（成功时）:
# {
#   "CosUrl": "cos://my-bucket-1234567890/uploads/protein_sequence.fasta",
#   "FileSize": 1024,
#   "UploadTime": "2026-08-06T16:00:00+08:00"
# }
```

#### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--file <path>` | ✅ | 本地文件绝对路径或相对路径 |
| `--cos-path <path>` | ✅ | COS 目标路径（相对于用户配置的 CosBucketName）；需用户指定 |
| `-o json` | 否 | 输出格式（默认 table） |

#### 完整场景示例

**场景：使用 AI 生成的蛋白质序列运行 scPROTEIN Collection (Nextflow) 子应用**

```
用户: 生成测试蛋白质序列，使用默认模板运行scPROTEIN Collection (Nextflow)

Agent:
  1. [调用相关SKILL] 生成蛋白质序列到 /tmp/test_protein.fasta
  2. [识别到本地文件] 触发 COS 上传流程
  
  Agent → 用户:
    "已生成测试蛋白质序列：/tmp/test_protein.fasta (2.3KB)
     需要上传至 COS 后才能作为运行参数。
     请指定 COS 目标路径（默认: uploads/test_protein.fasta）："
  
  用户: "uploads/my_test_protein.fasta"
  
  Agent:
    3. [执行] omics cos upload --file /tmp/test_protein.fasta --cos-path uploads/my_test_protein.fasta
    4. [解析返回] CosUrl = "cos://my-bucket/uploads/my_test_protein.fasta"
    5. [构建 input JSON] { "input_file": "cos://my-bucket/uploads/my_test_protein.fasta" }
    6. [继续] omics run --public-app <selectedAppId> --input /tmp/run_input.json ...
```

#### COS 上传守则

1. **必须先确认再上传**——不得未经用户同意自动上传本地文件
2. **COS 路径必须由用户指定**——SKILL 提供默认建议但不得自作主张
3. **仅上传必要的文件**——不得批量上传目录或无关文件
4. **上传失败时终止流程**——不得用本地路径替代 COS URL 继续运行
5. **保留上传返回信息**——用于调试和问题排查

---

错误知识库：[references/runtime_error_kb.md](references/runtime_error_kb.md)。运行流程规范：[references/run-flow-spec.md](references/run-flow-spec.md)。契约：[CONTRACT.md](CONTRACT.md)。

## 脚本 API 参考

```python
from scripts.omics_cli import OmicsCLI

cli = OmicsCLI()

# ✅ 检查类
cli.execute(cli.build_whoami())
cli.execute(cli.build_config_show(output="json"))

# ✅ 同名检查（唯一允许的 list 形态：必须带 --type）
cli.execute(cli.build_list_apps(
    app_type="<selectedAppType>",       # ★ 从子应用清单获取，不得用合集 AppType
    output="json",
))

# ✅ COS 上传（用于本地生成的文件）
cli.execute(cli.build_cos_upload(
    file_path="/tmp/local_file.txt",
    cos_path="uploads/file.txt",
    output="json",
))

# ✅ 唯一允许的 run（AppId 来自硬编码子应用清单，AppType 决定是否传 nf_version）
# WDL 子应用（不传 nf_version）
cli.execute(cli.build_run(
    sub_app_id="<selectedAppId>",       # ★ 来自本 SKILL 子应用清单，不得用合集 AppId
    public_app_name="<importedName>",
    app_type="<selectedAppType>",       # ★ 硬编码，以 --app-type 传给 CLI；WDL 时自动跳过 nf_version 校验
    output="json",
))

# NEXTFLOW 子应用（必须传 nf_version）
cli.execute(cli.build_run(
    sub_app_id="<selectedAppId>",
    public_app_name="<importedName>",
    app_type="NEXTFLOW",               # ★ 硬编码，以 --app-type 传给 CLI；NEXTFLOW 必须传 nf_version，否则抛出 ValueError
    nf_version="<selectedNfVersion>",  # 从子应用清单 NextflowVersions[] 中选取
    output="json",
))

# ✅ 状态 / debug
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))

# ❌ 禁止
# cli.execute(cli.build_list_public_apps(...))                 # 禁止调用（子应用已硬编码）
# cli.execute(cli.build_run(wdl="./x.wdl", ...))             # form A
# cli.execute(cli.build_run(app="app-xxx", ...))              # form C
# cli.execute(cli.build_run(public_app="5c63718b-d24f-4a9f-9838-4177185f414a", ...))      # 合集本身不可 run
# cli.execute(cli.build_list_apps(output="json"))              # 不带 --type（越界）
