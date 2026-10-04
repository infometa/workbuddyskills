# 公共应用运行流程规范

> 本文档定义 omics-common-app-skill **所生成的专用 SKILL** 在执行运行任务时的标准流程规范。
> 包含独立应用模式和合集模式的完整流程，以及各阶段的交互模板和守则。
>
> **相关文档**：
> - CLI 命令白名单与 run Flag 约束：[cli-whitelist.md](cli-whitelist.md)
> - SKILL 框架模板（包含能力边界声明）：[skill-template.md](skill-template.md)
> - 鉴权与配置流程（Step -1/0/1/2）：[omics-cli-setup.md](omics-cli-setup.md)

---

## §1 流程概览

### 1.1 独立应用模式（模式 B）

```
Step -1  CLI 存在性检查
Step 0   鉴权 + 配置检查（whoami + config show）
         └─ Step 0.3  体验配额首检（仅 C端，登录/配置就绪后必执行，见 omics-cli-setup.md §D-Step 0.3）
Step 1   登录（whoami exit 2 时）
Step 2   配置引导（config show 缺字段时）
Step 3   导入前同名检查（list apps，必须通过）
Step 4   运行前二次确认
Step 4.5 运行前配额检查（⚠️ 仅 C端，强制执行，见 §3.3b）
Step 5   执行运行（omics run --public-app <AppId>）
Step 6   查询任务状态（omics status）
```

### 1.2 合集模式（模式 A）

```
Step -1  CLI 存在性检查
Step 0   鉴权 + 配置检查（whoami + config show）
         └─ Step 0.3  体验配额首检（仅 C端，登录/配置就绪后必执行，见 omics-cli-setup.md §D-Step 0.3）
Step 1   登录（whoami exit 2 时）
Step 2   配置引导（config show 缺字段时）
Step 3   子应用选择（从硬编码清单展示/推荐，禁止调用 list public-apps）
Step 4   导入前同名检查（list apps，必须通过）
Step 5   运行前二次确认
Step 5.5 运行前配额检查（⚠️ 仅 C端，强制执行，见 §3.3b）
Step 6   执行运行（omics run --public-app <子应用AppId>）
Step 7   查询任务状态（omics status）
```

> ⚠️ **鉴权与配置流程（Step -1/0/1/2）所有生成的 SKILL 共用同一规范**，详细步骤见 [omics-cli-setup.md](omics-cli-setup.md)，生成的 SKILL 中必须引用，不得各自复制粘贴安装流程。

---

## §2 退出码处理（通用）

| 退出码 | 含义 | 处理方式 |
|--------|------|---------|
| `0` | 成功 | 解析 stdout |
| `1` | 业务错误 | 转述 stderr；配置缺失时引导走 Step 2 |
| `2` | 鉴权失败 | SKILL 直接调用 `omics login`，浏览器自动打开授权页；不循环重试 |

---

## §3 核心流程规范

### 3.1 子应用选择（合集模式 Step 3）

> 仅适用于合集模式（模式 A）

生成的合集 SKILL **必须从硬编码子应用清单**展示和匹配子应用，**禁止调用 `list public-apps`**。

**选择逻辑**：

```
读取 SKILL 中硬编码的子应用清单
         ↓
根据用户输入（功能描述/关键词/应用名）推荐匹配的子应用
         ↓
精确匹配（唯一）→ 向用户展示并确认
多个候选       → 列出让用户选择
无匹配         → 展示完整清单，引导用户选择
         ↓
记录字段：
  <selectedAppId>     ← 来自硬编码清单（⚠️ 不得使用合集 AppId）
  <selectedAppName>   ← 来自硬编码清单
  <selectedAppType>   ← 来自硬编码清单（⚠️ 不得使用合集的 AppType）
  <selectedNfVersion> ← 仅 selectedAppType=="NEXTFLOW" 时，从清单 NextflowVersions 让用户选
```

**硬编码清单展示模板**：

```
「{CollectionName}」合集包含以下子应用，请选择要运行的子应用：

  # │ 子应用名                │ 类型      │ 简介
  ──┼────────────────────────┼──────────┼────────
  1 │ {SubAppName1}          │ {Type1}  │ {Desc1}
  2 │ {SubAppName2}          │ {Type2}  │ {Desc2}
  ...

请输入编号或子应用名：
```

---

### 3.2 导入前同名检查循环（两种模式通用，必经）

> **设计意图**：`--public-app` 会在项目中创建新的应用记录。
> 若项目已有同名应用会导致 DUPLICATE_APP_NAME 错误，因此必须在导入前确保名称唯一。
> 通过**重命名引导**而非拒绝解决冲突。

#### 检查流程

```
执行检查：
  omics list apps --type <AppType> -o json
         ↓
检查待导入名称是否与已有应用的 ApplicationName 重名
         ↓
        ┌───────────────────────────┐
        │                           │
    无同名 ✓                    有同名 ✗
        │                           │
        ▼                           ▼
   通过检查                  展示冲突信息
   继续导入流程               引导用户重命名
                              用户输入新名称
                              重新执行同名检查
                              ↑（循环直到唯一）
```

#### 同名检查交互模板

```
────────────────────────────────────────
同名检查：{AppName}（{合集子应用 / 独立应用}）
────────────────────────────────────────

待导入名称: {candidateName}
检查结果: ⚠️ 发现同名应用

项目中已存在的同名应用:
  名称: {ConflictingAppName}
  AppId: {ConflictingApplicationId}
  类型: {ConflictingAppType}

请为即将导入的 {AppName} 指定一个不同的名称（将用作 --public-app-name）：
• 输入新名称，如 {AppName}_v2、my_{AppName}
• 或输入「取消」终止本次操作
>
```

#### 用户响应处理

| 用户输入 | 行为 |
|---------|------|
| 输入新名称 | 用新名称重新执行同名检查（回到流程入口） |
| 新名称仍同名 | 再次展示冲突信息，继续引导重命名 |
| 新名称无同名 | ✅ 通过检查，使用该名称作为 `--public-app-name` 继续 |
| 「取消」/「终止」 | 终止本次运行操作（不删除/修改任何项目已有应用） |

#### 同名检查守则

- **必须循环直到名称唯一**——不允许跳过同名检查直接 run
- **引导重命名时提供冲突信息**——让用户知道和谁冲突，便于决策
- **不得自动生成名称替代用户选择**——必须由用户显式指定新名称
- **不得删除/修改项目已有应用**——只做读操作（list apps）+ 引导用户重命名待导入的应用
- **取消时不执行任何写操作**——安全退出，不影响项目状态

---

### 3.3 运行前二次确认模板（两种模式通用）

```
即将运行任务，请确认：
┌──────────────────────────────────────────────────────┐
│ 形态      : 公共应用（form B）                        │
│ 应用      : {AppName}                   ← 合集时为子应用名  │
│ AppId     : {AppId}                     ← 合集时为子应用 AppId │
│ 来源合集  : {CollectionName}（{CollectionAppId}）     │  ← 仅合集模式
│ 应用类型  : {AppType}                   ← 合集时为子应用 AppType │
│ 导入后命名: {importedName}                            │
│ NF 版本   : {nfVersion}                              │  ← 仅 NEXTFLOW 类型
│ 项目/环境 : ← config                                 │
└──────────────────────────────────────────────────────┘
完整命令: omics run --public-app {AppId} --public-app-name {importedName} --app-type {AppType} ...

确认无误请回复「确认 / y / 继续」
```

---

### 3.3b 运行前配额检查（⚠️ 仅 C端用户，每次 omics run 前强制执行）

> **设计意图**：Step 0.3 首检在登录/配置就绪后执行，但用户可能在同一会话内多次运行任务，两次运行之间可能已消耗今日配额。因此，在每次实际提交 `omics run` 前必须再次检查，确保提交时配额仍充足。

#### 执行规则

- **触发条件**：用户类型为 C端（`whoami` 返回 `Role == "trial_user"`）
- **时机**：运行前二次确认（§3.3）通过后，`omics run` 命令执行前
- **强制性**：不可跳过，不受用户指令（如"直接跑""跳过检查"）影响

```bash
python3 scripts/omics_cli.py quota -o json
```

#### 话术（与 omics-cli-setup.md §D-Step 0.3 完全一致，四档均保留）

**场景一：已到期（`RemainDays == 0`）→ 阻断，停止运行**

```
⏰ 温馨提示：您的免费体验已到期，将无法继续运行任务，历史结果仍可查看。
   您可开通组学平台正式版，体验更多功能。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
🌐 了解平台 → https://cloud.tencent.com/product/omics
```

> ⚠️ 阻断：展示以上话术后立即终止，不提交 `omics run`。

**场景二：今日次数已用完（`TodayRemainingRuns == 0` 且 `RemainDays > 0`）→ 阻断，停止运行**

```
⏰ 温馨提示：今日免费体验运行已用完，明日 00:00 重置。
   您可开通组学平台正式版，享受无限制运行。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
```

> ⚠️ 阻断：展示以上话术后立即终止，不提交 `omics run`。

**场景三：临近到期（`RemainDays <= 3` 且 `RemainDays > 0` 且 `TodayRemainingRuns > 0`）→ 提示，继续运行**

```
⏰ 温馨提示：您的免费体验即将到期（剩余 {RemainDays} 天）。
   到期后将无法继续运行任务，历史结果仍可查看。
   您可开通组学平台正式版，体验更多功能。

📋 立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb

📊 今日剩余运行次数：{TodayRemainingRuns} 次
```

> 展示以上话术后**立即执行** `omics run`，无需等待用户确认。

**场景四：正常体验（`RemainDays > 3` 且 `TodayRemainingRuns > 0`）→ 简短提示，继续运行**

```
📊 免费体验版配额：今日剩余 {TodayRemainingRuns} 次 · 剩余 {RemainDays} 天
```

> 展示一行后**立即执行** `omics run`，无需等待用户确认。

#### 守则

- ✅ **阻断时**：展示话术后停止流程，不提交 `omics run`
- ✅ **通过时**（场景三/四）：展示话术/配额行后**立即**提交，不等待用户确认
- ❌ **不可跳过**：C端用户每次 run 前此步必须执行
- ❌ **不可让用户绕过**：即使用户明确说"我知道了直接跑"，仍须先执行检查

---

### 3.4 执行运行（两种模式通用）

**wrapper 调用**：

```python
# 独立应用模式
cli.build_run(
    public_app="{APP_ID}",               # 硬编码值
    app_type="{APP_TYPE}",               # 硬编码值，以 --app-type 传给 CLI
    public_app_name=importedName,        # 可为 None（独立应用时 CLI 自动兜底）
    nf_version=nfVersion,                # 仅 APP_TYPE=="NEXTFLOW" 时必传
    input_file=inputPath,
    run_name=runName
)

# 合集模式
cli.build_run(
    public_app=selectedAppId,            # 来自硬编码清单（子应用 AppId）
    app_type=selectedAppType,            # 来自硬编码清单，以 --app-type 传给 CLI
    public_app_name=importedName,        # 必传（合集子应用必须指定导入名）
    nf_version=selectedNfVersion,        # 仅 selectedAppType=="NEXTFLOW" 时必传
    input_file=inputPath,
    run_name=runName
)
```

**run 报错处理**：当 `omics run` 报错（CLI 非零退出码 / API 返回错误码）时，SKILL **直接透传 CLI 输出给用户**，不做任何额外处理。

**InputTemplate 自动填充**：

1. **默认行为**：未传 `--input` 且未传 `--template` 时，CLI 按以下优先级自动选取运行参数模板：
   - **优先**：模板 `Name` 等于 `input.json_{Region}`（前缀 `input.json_` 精确匹配，region 部分不区分大小写，Region 来自 `config show` 的当前配置，如 `ap-guangzhou`）
   - **兜底**：无命中时取模板列表第一条
   - **无模板**：模板列表为空时回落到参数清单模式（pipeline 用纯 baseline 跑；若必填参数无 Default 值则在 ValidateDetailed 阶段精准报错，引导用户通过 `--input <local.json>` 提供参数）
2. **用户覆盖**：传入 `--input` 或 `--template` 时，自定义值覆盖对应字段；未覆盖字段保持默认值；`--input` 与 `--template` 互斥
3. **模板来源**：InputTemplate 数据来自公共应用注册时的模板定义，绑定在导入后的项目内 ApplicationId 维度上

---

### 3.5 任务状态查询

```bash
python3 scripts/omics_cli.py status [<rgId>]
```

- 无 `<rgId>`：查询最近一次运行的状态
- 有 `<rgId>`：查询指定批次的状态

**状态轮询建议**：

| 任务类型 | 建议策略 |
|---------|---------|
| 同步任务 | `omics run` 返回后检查 exit code，再调用 `status` 确认 |
| 异步任务 | 提交后告知用户 runGroupId，引导使用 `status <rgId>` 查询 |

**失败取证**（任务 FAILED 时）：

```bash
python3 scripts/omics_cli.py debug <rgId>          # 批次级别
python3 scripts/omics_cli.py debug <rgId> --run    # 子任务级别
python3 scripts/omics_cli.py debug <rgId> --run --job  # Job 级别
```

---

### 3.6 结果目录提醒规范（outdir 场景）

> **触发条件**：运行参数中包含 `outdir` 字段（来自 `--input` 参数、InputTemplate 默认值、或用户指定）

#### 提醒时机

| 任务类型 | 提醒时机 |
|---------|---------|
| 同步任务 | `omics run` 命令返回后立即提醒（无论 exit code） |
| 异步任务 | `omics status` 查询到终态（SUCCESS / FAILED）后提醒 |

#### 提醒模板

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 运行结果目录提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

任务已完成，运行结果已输出至：
  {outdir 完整路径}

请前往该目录查看输出文件。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 守则

- ✅ **必须提醒**：每次含 outdir 的任务完成后都必须执行
- ✅ **路径完整**：提醒时展示 outdir 的完整绝对或相对路径
- ✅ **时机准确**：同步任务在 run 返回后；异步任务在 status 查到终态后
- ❌ **不得省略**：不得因为任务失败而省略 outdir 提醒
- ❌ **不得延迟**：不得将提醒推迟到后续对话轮次
- ❌ **不得假设**：不得假设用户已经知道结果位置而不提醒

---

## §4 越界场景处理（两种模式通用）

当用户要求运行**非本 SKILL 职责范围内**的应用时，按以下流程处理：

```
判断用户意图：
  ↓
  A. 用户要运行本公共应用/合集中的应用，但项目有同名冲突
     → 进入 §3.2 同名检查循环（引导重命名，不拒绝）
  
  B. 用户要运行的目标本身不是本公共应用/合集（如其他公共应用、项目已有应用等）
     → 按越界拒绝模板响应（见 skill-template.md §2.3）
     → 引导使用 omics-task-skill
```

---

> 文档版本：v1.1（新增 §3.3b 运行前配额检查；§1 流程概览更新 Step 4.5/5.5；Step 0.3 标注为"首检"）
> 关联：[SKILL.md](../SKILL.md) · [cli-whitelist.md](cli-whitelist.md) · [skill-template.md](skill-template.md) · [omics-cli-setup.md](omics-cli-setup.md)
