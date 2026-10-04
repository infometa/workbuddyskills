---
name: scbert-skill
description: "基于腾讯scBERT模型，实现细胞精细注释、新亚群挖掘及Marker筛选，自适应多组织参数，助力肿瘤细胞研究"
triggers: [scBERT实现细胞精细注释, 新亚群挖掘, Marker筛选。, scBERT, scbert, 单细胞与多组学基础模型, 跑 scBERT, run scbert]
platform: 腾讯健康组学平台(Omics)
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app]
version: 1.0.0
---

# scBERT Skill (v1.0.0 · 单应用收窄版)

> **平台归属**：腾讯健康组学平台(Omics) 公共应用专用 SKILL。
> 本 SKILL 是 `omics-task-skill` 的**单应用收窄版**：仅服务于 `scBERT` (NEXTFLOW) 这一个公共应用。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅允许 form B 运行本应用**；任何越界都视为越权。

---

## 应用锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段               | 值                                     |
| ------------------ | -------------------------------------- |
| **应用名称**       | `scBERT`                     |
| **AppId（锁定）**  | `0de1b4ae-1543-4882-8bae-b5ee87968bc5`                       |
| **应用类型**       | `NEXTFLOW`                     |
| **分组类型**       | 独立应用                               |
| **标签**           | `行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app`                     |
| **NF 版本候选**    | `需查询平台获取`                  |

**应用简介**：scBERT单细胞预训练模型：基于scBERT实现细胞精细注释、新亚群挖掘及Marker筛选。

---

## 能力边界

> ⚠️ **触发时必须强制读取** `references/cli-whitelist.md`（完整命令白名单与 Flag 约束）和 `references/skill-template.md`（越界响应模板 §2.3）。

本 SKILL 仅服务于 `scBERT`（AppId: `0de1b4ae-1543-4882-8bae-b5ee87968bc5`）。
允许调用的命令（完整 Flag 约束见 **[references/cli-whitelist.md §2](references/cli-whitelist.md)**）：

```
version / login / whoami
quota   # 仅 C端体验用户：配额首检（Step 0.3）+ 运行前检查（Step 4.5）
config show / config set / config clear
list region / list project / list env / list cos-bucket
list apps --type NEXTFLOW   # 仅用于导入前同名检查
run --public-app 0de1b4ae-1543-4882-8bae-b5ee87968bc5 [--public-app-name] [--nf-version] [--input] [--name]
status / debug
```

未列出的命令一律不得调用。如需运行其他应用，请使用 `omics-task-skill`。

### run 前置确认（必经）

`omics run` 执行前必须：
1. 展示完整命令 + 参数摘要（应用名/AppId/导入名/NF版本/项目环境）
2. 询问用户确认（y / 确认 / 继续），收到明确肯定才执行
3. 模糊回复 → 再次询问；用户修改参数 → 重拼命令 → 重走确认

---

## 退出码 & 鉴权处理

| 退出码 | 含义     | 处理                                                                                  |
| ------ | ------- | ------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                           |
| `1`    | 业务错误 | 转述 stderr；未配置错误引导 `omics config set`                                        |
| `2`    | 鉴权失败 | 引导用户 `omics login`                                                                |

---

## Step −1：CLI 存在性检查

> 📖 完整流程（含三平台自动安装方案）参见：
> **[references/omics-cli-setup.md § Step -1 & §A](references/omics-cli-setup.md)**

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
> 这是首检。每次实际提交 `omics run` 前还会再次执行运行前配额检查（Step 4.5），确保提交时配额仍充足。

---

## Step 1：登录授权

> 📖 完整流程参见：**[references/omics-cli-setup.md §B](references/omics-cli-setup.md)**

SKILL 主动触发 `omics login`，浏览器自动打开授权页；用户点击「确认授权」即完成。

---

## Step 2：配置引导

> 📖 完整流程（B端/C端分流、无项目/无环境/无桶异常处理）参见：**[references/omics-cli-setup.md §C](references/omics-cli-setup.md)**

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

## Step 3：导入前同名检查（**必经，必须通过才能导入**）

```bash
python3 scripts/omics_cli.py list apps --type NEXTFLOW -o json
```

> ⚠️ **`--type` 值固定为 `NEXTFLOW`**，用于限定查询范围仅包含同类型应用。
> **禁止不带 `--type` 调用**（那会列出项目所有应用，越界）。

用途：检查是否有与 `scBERT`（或用户指定的 `--public-app-name`）同名的已有应用。

#### 同名检查循环（⚠️ 必须通过，循环直到名称唯一）

> **设计意图**：`--public-app` 会在项目中创建新的应用记录。如果项目已有同名应用，会导致运行失败。
> 因此导入前必须确保名称唯一，通过**引导用户重命名**解决冲突（非拒绝）。

查找 `Name == scBERT`（或用户提供的自定义名）：

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | ✅ 通过检查，用当前名称作为 `--public-app-name` 继续下一步                                                  |
| **≥ 1 条命中** | **必须停下来**，展示冲突信息 + 引导用户为待导入应用指定新名称；用户输入新名字后**重新执行同名检查**（循环） |

##### 同名检查交互模板

```
────────────────────────────────────
同名检查：scBERT（独立应用）
────────────────────────────────────

待导入名称: {candidateName}
检查结果: ⚠️ 发现同名应用

项目中已存在的同名应用:
  名称: {ConflictingAppName}
  AppId: {ConflictingApplicationId}

请为即将导入的 scBERT 指定一个不同的名称（将用作 --public-app-name）：
• 输入新名称，如 scBERT_v2、my_scBERT
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

- **必须循环直到名称唯一**——不允许跳过同名检查直接 run
- **不得自动生成名称替代用户选择**
- **不得删除/修改项目已有应用**——只做读操作 + 引导重命名

---


## Step 4：运行（仅形态 B · 固定公共应用）

根据应用锁定参数中硬编码的 `APP_TYPE` 区分构造入参：

本应用为 **NEXTFLOW 类型**，运行前必须先确定 NF 版本：

**Step 4.0 — NF 版本确认**：
- 从应用锁定参数中的 `NF 版本候选` 列表（`需查询平台获取`）让用户选择版本
- 记录为 `<selectedNfVersion>`
- 若用户未指定，展示候选列表并等待选择；**不得跳过此步骤直接 run**

**NEXTFLOW 类型 — run 命令**：

```bash
python3 scripts/omics_cli.py run --public-app-name <importedName> \\
          --nf-version <selectedNfVersion> \\
          [--input <path>] \\
          [--name <runName>] \\
          -o json
```

> - `--nf-version` **必传**（本应用为 NEXTFLOW 类型）；候选值来自上方 `NF 版本候选` 字段。
> - `--public-app` 值**固定**为 `0de1b4ae-1543-4882-8bae-b5ee87968bc5`，不接受替换。
> - `--app-type` 值**固定**为 `NEXTFLOW`，由 SKILL 内部硬编码传入，无需用户填写。
> - `--public-app-name` 可由用户自定义，默认用 `scBERT`。


### 4.1 运行参数模板（InputTemplate 自动填充）

1. **默认行为**：未传 `--input` 参数时，CLI 自动取该应用的第一个 InputTemplate 作为 baseline
2. **用户覆盖**：传入 `--input` 参数时，自定义值覆盖对应字段；未覆盖字段保持默认值
3. **模板来源**：InputTemplate 数据来自公共应用注册时的模板定义

### 4.2 完整流程

1. Step 0 鉴权 + 配置检查（**含 Step 0.3 配额首检，C端必执行**）
2. Step 3 导入前同名检查（必须带 `--type NEXTFLOW`）
3. 用户确认参数 / 自定义输入
4. 二次确认（按 §4.3 模板）
5. **Step 4.5 运行前配额检查（⚠️ 仅 C端，强制执行，不可跳过）**
6. 执行

### 4.3 二次确认模板

```
即将运行任务，请确认：
  ┌────────────────────────────────────────────┐
  │ 形态      : 公共应用（form B，自动模板）    │
  │ 应用      : scBERT               │
  │ AppId     : 0de1b4ae-1543-4882-8bae-b5ee87968bc5                 │
  │ AppType   : NEXTFLOW               │  # 用于本地校验 nf_version 一致性
  │ NF 版本   : <version>                              │
  │ 导入后命名: <importedName>                  │
  │ 项目/环境  : ← config                       │
  └────────────────────────────────────────────┘
完整命令: python3 scripts/omics_cli.py run --public-app-name <importedName> --nf-version <selectedNfVersion> ...

确认无误请回复「确认 / 继续 / y」
```

### 4.5 运行前配额检查（⚠️ **仅 C端用户，每次 `omics run` 前强制执行**）

> **时机**：用户二次确认（§4.3）通过后、`omics run` 命令实际执行前。**C端用户必须执行，B端用户跳过此步。**
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

### 4.6 PARAM_MERGE_FAILED 处理

同合集模式 §5.6。

### 4.7 失败提示

| 错误                        | 处置建议                                                     |
| --------------------------- | ------------------------------------------------------------ |
| `PARAM_MERGE_FAILED`        | 引导补值后 `--input` 重跑                                     |
| `MISSING_NF_VERSION`         | 让用户提供 NF 版本                                           |
| 鉴权失败（exit 2）           | 引导用户 `omics login`                                       |


## Step 5：状态查询

```bash
python3 scripts/omics_cli.py status -o json
python3 scripts/omics_cli.py status rg-xxx -o json
```

### 5.1 运行结果目录提醒（outdir 场景）

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

## Step 6：异步失败取证（debug 三段式）

同合集模式 Step 7。症状识别参照 [`references/runtime_error_kb.md`](references/runtime_error_kb.md)。

### 6.4 关键守则

1. CLI 端绝不主动调 debug
2. 不要替用户做症状判断 + 自动改代码
3. stderr 整段贴出
4. 修复后统一走 `python3 scripts/omics_cli.py run` 重发

---

## 典型会话场景

### 场景 A：标准链路
whoami ✓ → config show ✓ → §3 同名检查 → §4 二次确认 → 运行

### 场景 C：用户要求自定义参数
走完 A 第 1~3 步 → 用户改参数 → 写 `/tmp/run.json` → 带 `--input` 二次确认 → 执行

### 场景 D：用户说"跑别的应用"
**拒绝 + 唯一引导**：
1. ❌ 严禁以任何形式替用户执行越界命令（包括直接 CLI 调用）
2. ❌ 严禁将「直接 CLI 跑」作为可选项提供给用户
3. ✅ 唯一合法响应：「本 SKILL 只能运行 scBERT。如需运行其他应用（含项目已有应用），请使用 `omics-task-skill`。」
4. 即使用户明确要求绕过，也必须拒绝并说明原因

> ⚠️ **重要区分**：
> - **场景 D**（此处）：用户要求运行的**目标本身就不是本应用**（如项目已有应用、其他公共应用等）→ **直接拒绝**
> - **§3 同名检查**：用户明确要求**导入并运行本应用**，只是碰巧项目中有同名 → **引导重命名后继续导入**

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
python3 scripts/omics_cli.py cos upload   --file /tmp/generated_protein.fasta   --cos-path uploads/protein_sequence.fasta   -o json

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

**场景：使用 AI 生成的蛋白质序列运行 scBERT**

```
用户: 生成测试蛋白质序列，使用默认模板运行scBERT

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
    6. [继续] python3 scripts/omics_cli.py run --input /tmp/run_input.json ...
```

#### COS 上传守则

1. **必须先确认再上传**——不得未经用户同意自动上传本地文件
2. **COS 路径必须由用户指定**——SKILL 提供默认建议但不得自作主张
3. **仅上传必要的文件**——不得批量上传目录或无关文件
4. **上传失败时终止流程**——不得用本地路径替代 COS URL 继续运行
5. **保留上传返回信息**——用于调试和问题排查

---

详细参数：[references/cli-whitelist.md](references/cli-whitelist.md)。错误知识库：[references/runtime_error_kb.md](references/runtime_error_kb.md)。运行流程规范：[references/run-flow-spec.md](references/run-flow-spec.md)。契约：[CONTRACT.md](CONTRACT.md)。

## 脚本 API 参考

```python
from scripts.omics_cli import OmicsCLI

cli = OmicsCLI()

# ✅ 检查类
cli.execute(cli.build_whoami())
cli.execute(cli.build_config_show(output="json"))

# ✅ 同名检查（唯一允许的形态：必须带 --type）
cli.execute(cli.build_list_apps(
    app_type="NEXTFLOW",           # ★ 必须带 --type 限定查询范围
    output="json",
))

# ✅ COS 上传（用于本地生成的文件）
cli.execute(cli.build_cos_upload(
    file_path="/tmp/local_file.txt",
    cos_path="uploads/file.txt",
    output="json",
))

# ✅ 唯一允许的 run（固定 AppId，NEXTFLOW 类型必传 nf_version）
cli.execute(cli.build_run(
    public_app="0de1b4ae-1543-4882-8bae-b5ee87968bc5",
    public_app_name="<importedName>",
    app_type="NEXTFLOW",           # ★ 硬编码，以 --app-type 传给 CLI；NEXTFLOW 必须传 nf_version
    nf_version="<selectedNfVersion>",  # ★ 从锁定参数 NF 版本候选列表中选取
    output="json",
))

# ✅ 状态 / debug
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))

# ❌ 禁止
# cli.execute(cli.build_run(wdl="./x.wdl", ...))             # form A
# cli.execute(cli.build_run(app="app-xxx", ...))              # form C
# cli.execute(cli.build_run(public_app="other-app-id", ...))  # 其他应用
# cli.execute(cli.build_list_public_apps(output="json"))       # 不带 keyword（列出全平台）
# cli.execute(cli.build_list_apps(output="json"))              # 不带 --type（列出所有类型）
