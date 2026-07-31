---
name: iggm-wdl-skill
description: "腾讯健康组学平台(Omics) - IgGM(WDL) 公共应用专用运行助手。IgGM 是一个用于抗体设计的生成式基础模型，支持抗体CDR区域设计、全链设计和人源化设计等任务仅服务于本应用的导入与运行；其他公共应用、本地 WDL、COS 上的 NF、项目内已有应用请改用 omics-task-skill。 触发词：IgGM(WDL), iggm(wdl), AI 模型, ai 模型, 蛋白质与抗体设计, 一个用于抗体设计的生成式基础模型, 设计的生成式基础模型, IgGM, 全链设计和人源化设计等任务, 设计和人源化设计等任务, CDR, 跑 IgGM(WDL), run iggm(wdl), 应用"
platform: 腾讯健康组学平台(Omics)
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app]
version: 1.0.0
---

# IgGM(WDL) Skill (v1.0.0 · 单应用收窄版)

> **平台归属**：腾讯健康组学平台(Omics) 公共应用专用 SKILL。
> 本 SKILL 是 `omics-task-skill` 的**单应用收窄版**：仅服务于 `IgGM(WDL)` (WDL) 这一个公共应用。
> 所有命令拼接走 `scripts/omics_cli.py`，统一参数与输出格式。
> **能力范围严格 = `omics-platform-cli` 7 命令 ∩ 仅允许 form B 运行本应用**；任何越界都视为越权。

---

## 应用锁定参数（**SKILL 内部硬编码，禁止覆盖**）

| 字段               | 值                                     |
| ------------------ | -------------------------------------- |
| **应用名称**       | `IgGM(WDL)`                     |
| **AppId（锁定）**  | `b65d7070-6e8a-4a57-914d-dbbb9dd9b286`                       |
| **PublicAppId**    | `publicapp-wdl-iggm` |
| **应用类型**       | `WDL`                     |
| **分组类型**       | 独立应用                               |
| **标签**           | `行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app`                     |

**应用简介**：IgGM 是一个用于抗体设计的生成式基础模型，支持抗体CDR区域设计、全链设计和人源化设计等任务。

---

## 能力边界（不可违反 · 最高优先级）

本 SKILL 只能调用以下 **7 条** CLI 一级命令的**收窄子集**：

```
login   whoami   config   list apps   run   status   debug
```

> 注意：`omics list public-apps` 整体禁用——本 SKILL 服务的是固定单一应用，不需要让用户在全平台里挑。
> `omics list apps` 仅允许在导入前同名检查时调用。

### 🚫 严令禁止

1. **严禁运行除 IgGM(WDL) 之外的任何应用**：
   - 禁止 `omics run --wdl <path>`（本地 WDL）
   - 禁止 `omics run --app <ApplicationId>`（项目内已有应用）
   - 禁止 `omics run --public-app <非本应用 AppId>`
   - **唯一允许**的 run 形态：`omics run --public-app b65d7070-6e8a-4a57-914d-dbbb9dd9b286 ...`
2. **严禁调 `list public-apps`**——不需要
3. **严禁编造其他命令**
4. **严禁直接调用后端 HTTP API、SQL 等旁路通道**
5. **`omics login` / `omics config set` 由用户在本机终端执行**
6. **严禁建议/提示用户「直接用 CLI 绕过 SKILL 跑」**——当用户要求运行非本应用时，唯一合法响应是引导使用 `omics-task-skill`，不得提供任何形式的 CLI 绕行方案

### ✅ run 前置确认（必经）

同合集模式：拼完整命令 → 输出摘要表 → 询问 y/N → 收到肯定答复才执行。

### ✅ 其他命令确认要求

同合集模式。

---

## 退出码 & 鉴权处理

| 退出码 | 含义     | 处理                                                                                  |
| ------ | ------- | ------------------------------------------------------------------------------------- |
| `0`    | 成功     | 解析 stdout                                                                           |
| `1`    | 业务错误 | 转述 stderr；未配置错误引导 `omics config set`                                        |
| `2`    | 鉴权失败 | 引导用户 `omics login`                                                                |

---

## Step −1：CLI 存在性检查

同合集模式。

---

## Step 0：鉴权与配置双重检查

同合集模式（Step 0.1 whoami → Step 0.2 config show）。

---

## Step 1：登录引导

同合集模式。

---

## Step 2：配置引导

同合集模式。

---

## Step 3：导入前同名检查 + 快照记录（**必经**，必须才能导入）

进入 `omics run` 之前，先在 config 项目里检查是否已存在同名应用。

```bash
python3 scripts/omics_cli.py list apps -o json
```

| 用途 | 说明 |
|------|------|
| **快照记录（先执行）** | **必须**先将返回的全部 `ApplicationId` 存储为「预存应用快照」，用于后续 **`omics run` 命令接口报错**时判定孤儿应用来源 |
| **同名检查（后执行）** | 检查是否有与 `IgGM(WDL)`（或用户指定的 `--public-app-name`）同名的已有应用 |

### 3.1 同名检查循环（⚠️ 必须通过，循环直到名称唯一）

> **设计意图**：`--public-app` 会在项目中创建新的应用记录。如果项目已有同名应用，会导致运行失败。
> 因此导入前必须确保名称唯一，通过**引导用户重命名**解决冲突（非拒绝）。

查找 `Name == IgGM(WDL)`（或用户提供的自定义名）：

| 命中情况       | SKILL 行为                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| **0 条命中**   | ✅ 通过检查，用当前名称作为 `--public-app-name` 继续下一步                                                  |
| **≥ 1 条命中** | **必须停下来**，展示冲突信息 + 引导用户为待导入应用指定新名称；用户输入新名字后**重新执行同名检查**（循环） |

#### 同名检查交互模板

```
────────────────────────────────────
同名检查：IgGM(WDL)（独立应用）
────────────────────────────────────

待导入名称: {candidateName}
检查结果: ⚠️ 发现同名应用

项目中已存在的同名应用:
  名称: {ConflictingAppName}
  AppId: {ConflictingApplicationId}

请为即将导入的 IgGM(WDL) 指定一个不同的名称（将用作 --public-app-name）：
• 输入新名称，如 IgGM(WDL)_v2、my_IgGM(WDL)
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

## Step 4：运行（仅形态 B · 固定公共应用）

```bash
omics run --public-app b65d7070-6e8a-4a57-914d-dbbb9dd9b286 \\
          --public-app-name <importedName>\
          {[--nf-version <version>] if APP_TYPE == "NEXTFLOW" else ''} \\
          [--input <path>] \\
          [--name <runName>] \\
          -o json
```

> - `--public-app` 值**固定**为 `b65d7070-6e8a-4a57-914d-dbbb9dd9b286`，不接受替换。
> - `--public-app-name` 可由用户自定义，默认用 `IgGM(WDL)`。

> - `--input` 仅在用户明确要求自定义参数时传入。
> - **`--nf-version` 仅当本应用 AppType 为 NEXTFLOW 时传入**（AppType 来自公共应用元数据）。

### 4.1 运行参数模板（InputTemplate 自动填充）

1. **默认行为**：未传 `--input` 参数时，CLI 自动取该应用的第一个 InputTemplate 作为 baseline
2. **用户覆盖**：传入 `--input` 参数时，自定义值覆盖对应字段；未覆盖字段保持默认值
3. **模板来源**：InputTemplate 数据来自公共应用注册时的模板定义

### 4.2 完整流程

1. Step 0 鉴权 + 配置检查
2. Step 3 导入前同名检查
3. 用户确认参数 / 自定义输入
4. 二次确认（按 §4.3 模板）
5. 执行

### 4.3 二次确认模板

```
即将运行任务，请确认：
  ┌────────────────────────────────────────────┐
  │ 形态      : 公共应用（form B，自动模板）    │
  │ 应用      : IgGM(WDL)               │
  │ AppId     : b65d7070-6e8a-4a57-914d-dbbb9dd9b286                 │
  │ AppType   : WDL                │
  │ {'NF 版本   : <version>' if APP_TYPE == 'NEXTFLOW' else ''}│
  │ 导入后命名: <importedName>                  │
  │ 项目/环境  : ← config                       │
  └────────────────────────────────────────────┘
完整命令: omics run --public-app b65d7070-6e8a-4a57-914d-dbbb9dd9b286 ...

确认无误请回复「确认 / 继续 / y」
```

### 4.4 PARAM_MERGE_FAILED 处理

同合集模式 §5.3。

### 4.5 失败提示

| 错误                        | 处置建议                                                     |
| --------------------------- | ------------------------------------------------------------ |
| `PARAM_MERGE_FAILED`        | 引导补值后 `--input` 重跑                                     |
| `MISSING_NF_VERSION`         | 让用户提供 NF 版本                                           |
| 鉴权失败（exit 2）           | 引导用户 `omics login`                                       |

### 4.6 DUPLICATE_APP_NAME 智能复用（**必经**）

同合集模式 §5.5。核心逻辑：

> **前置条件**：此流程**仅在已完成 §3 同名检查循环（名称已确认唯一）并执行 run 后触发**。
> ⚠️ **重要区分**："命令接口报错"指 `omics run` CLI 本身执行失败，**不包括**任务提交成功后运行结果失败。

1. 取出响应中的 `ConflictApplicationId`
2. **查询 Step 3 预存快照**：
   - **在快照中**（项目已有老应用，理论上不应发生）→ 展示 Options 给用户选择
   - **不在快照中**（本次 `omics run` 命令新建的孤儿应用）→ **自动切 `--app <ConflictApplicationId>` 复用** ✅
3. 用复用命令重新发起运行

> ⚠️ **复用边界守则**：
> - ✅ 允许自动复用：**仅限孤儿应用场景**（已通过同名检查 → `omics run` **命令接口报错** → 冲突 ∉ 快照）
> - ❌ 禁止复用：任何其他场景下使用 `--app` 运行项目已有应用
> - ❌ **禁止将"任务运行结果失败"误判为命令接口报错**——后者不涉及孤儿应用

---

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
4. 修复后统一走 `omics run --public-app b65d7070-6e8a-4a57-914d-dbbb9dd9b286` 重发

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
3. ✅ 唯一合法响应：「本 SKILL 只能运行 IgGM(WDL)。如需运行其他应用（含项目已有应用），请使用 `omics-task-skill`。」
4. 即使用户明确要求绕过，也必须拒绝并说明原因

> ⚠️ **重要区分**：
> - **场景 D**（此处）：用户要求运行的**目标本身就不是本应用**（如项目已有应用、其他公共应用等）→ **直接拒绝**
> - **§3 同名检查**：用户明确要求**导入并运行本应用**，只是碰巧项目中有同名 → **引导重命名后继续导入**

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

# ✅ 同名检查
cli.execute(cli.build_list_apps(output="json"))

# ✅ 唯一允许的 run（固定 AppId）
cli.execute(cli.build_run(
    public_app="b65d7070-6e8a-4a57-914d-dbbb9dd9b286",
    public_app_name="<importedName>",
    nf_version="<version>",  # 仅 NEXTFLOW 类型需要
    output="json",
))

# ✅ 状态 / debug
cli.execute(cli.build_status(output="json"))
cli.execute(cli.build_debug(run_group_id="rg-xxx", output="json"))

# ❌ 禁止
# cli.execute(cli.build_run(wdl="./x.wdl", ...))             # form A
# cli.execute(cli.build_run(app="app-xxx", ...))              # form C
# cli.execute(cli.build_run(public_app="other-app-id", ...))  # 其他应用
# cli.execute(cli.build_list_public_apps(output="json"))       # 不需要
