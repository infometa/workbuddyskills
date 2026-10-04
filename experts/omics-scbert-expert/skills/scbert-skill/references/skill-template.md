# 公共应用 / 合集 SKILL 框架模板

> 本文档是 `generate_app_skill.py` 生成专用 SKILL 时的**结构契约**。
> 分为三节：
> - **§1 frontmatter 字段规范**：每个字段的取值逻辑（description / triggers 等）
> - **§2 能力边界通用声明**：所有生成的 SKILL 必须包含的能力边界说明
> - **§3 SKILL.md 骨架模板**：生成器填充的完整结构
>
> **CLI 命令白名单与 run Flag 约束**：见 [cli-whitelist.md §2](cli-whitelist.md)
> **运行流程规范**：见 [run-flow-spec.md](run-flow-spec.md)

---

## §1 frontmatter 字段规范

### 1.1 `name` 字段

**格式**：`{sanitized_app_name}-skill`（全英文，不含中文字符）

#### 命名规则（强制）

| 规则 | 适用范围 | 说明 |
|------|---------|------|
| 目录名必须全英文 | 仅限文件夹名 | 不允许使用中文字符 |
| `name` 格式 | 仅限 YAML frontmatter 的 `name` 字段 | `{目录名}-skill` |
| 描述内容保持原名 | description、标题、正文、应用简介 | **必须保持公共应用本身的中文名称，不得翻译** |

#### 自动派生算法（`sanitize_name()`）

从 `AppName` 按以下顺序处理：

| 步骤 | 操作 | 示例 |
|------|------|------|
| ① 全部小写 | `ESMFold2` → `esmfold2` | |
| ② 去除括号及括号内内容 | `(Nextflow)` → 去掉 | `ESMFold2 Collection (Nextflow)` → `ESMFold2 Collection ` |
| ③ 空格/连字符/下划线/点号 → `-` | `CD-GPT Collection` → `cd-gpt-collection` | |
| ④ 去除其他特殊字符（`/` `(` `)` `&` 等） | `snps/indels` → `snpsindels` | |
| ⑤ 合并连续连字符，去除首尾连字符 | `--` → `-` | |
| ⑥ 加 `-skill` 后缀 | `fastp` → `fastp-skill` | |

**中文 AppName 处理**：包含中文时先翻译为英文再执行上述步骤（参考翻译规则：保留技术缩写，功能描述译为英文，版本修饰语简化）。

**派生示例**：

| AppName | 自动派生 name |
|---------|-------------|
| `CD-GPT Collection (Nextflow)` | `cd-gpt-collection-skill` |
| `fastp` | `fastp-skill` |
| `IgGM(WDL)` | `iggm-skill` |
| `boltz结构预测-WDL` | `boltz-structure-prediction-wdl-skill` |
| `抗体研发-IgGM-Boltz-MSA版-WDL` | `iggm-boltz-msa-wdl-skill` |

**用户自定义 name**：用户可输入 `name: xxx` 覆盖自动派生值。生成器自动补充 `-skill` 后缀；若包含中文字符，提示用户修改。

#### 输出目录同名检查（必检）

```
if 存在("{output_dir}/{skill_name}"):
  → 报错终止，提示用户检查是否已有同名 SKILL，或使用 --skill-name 指定不同名称
  → 不允许自动覆盖（除非传入 --overwrite 参数）
else:
  → 继续创建目录和文件
```

---

### 1.2 `description` 字段

**取值优先级（必须按顺序）**：

```
首选：--skill-intro 参数（表格「SKILL简介」列对应行的原始文本）
  → 完整原样写入，不做任何修改
  → 不得编造、不得删减、不得改写

兜底（--skill-intro 为空时）：AppDesc 自动生成
  → 调用 _condense_description() 智能总结 + 固定前缀格式
  → 输出告警提示用户补充表格数据
```

**数据源**：[企微表格 BB08J2](https://doc.weixin.qq.com/sheet/e3_AF4Aw3hJAGICNW7MMsqSCSp2xuHZE_a?tab=BB08J2)「SKILL slug」→「SKILL简介」列

> ⚠️ 严禁在 SKILL简介非空时使用 AppDesc 覆盖或改写 description。

---

### 1.3 `triggers` 字段

**格式**：YAML 列表，独立字段，禁止拼接到 `description` 字段末尾。

```yaml
triggers: [触发词1, 触发词2, ...]
```

**触发词来源（按优先级）**：

#### Priority 0：功能场景短语（最高优先级）

**数据源**：AppDesc（一句话概述）

从 AppDesc 中提取"这个应用能做什么"的功能场景词，覆盖 6 种模式：

| 模式 | 提取目标 | 示例 |
|------|---------|------|
| **A: 显式功能声明** | `支撑/支持/用于/适用于` 后接短语 | 药物靶点发现、疗效评估 |
| **B: 能力描述** | `可/能够` 后接动词短语 | 识别变异位点 |
| **C: 基于/面向** | `基于/面向` 后接短语 | 基于深度学习的蛋白质结构预测 |
| **D: 适合/专为** | `适合/专为` 后接短语 | 适合大规模基因组重测序数据分析 |
| **E: 冒号枚举** | 冒号后内容再拆分 | — |
| **F: 定义式（兜底）** | `是...(模型\|工具\|系统)` 的核心功能 | 蛋白质结构预测 |

后处理：并列短语按 `、/及/和` 拆分；过滤停用词；长度限制 4-18 字。

#### Priority 1：应用名变体

AppName 全名、缩写、常见拼写变体（如 `ESMFold2`、`esmfold2`、`ESMFold 2`）

#### Priority 2：标签词（过滤后）

AppTags 中英文名，过滤泛化标签黑名单：
```
AI 模型, AI, 模型, 工具, 平台, 系统, 流程, 未分类, 合集, 应用, 软件
```

#### Priority 3：行动短语

`跑 {AppName}`、`用 {AppName}`、`运行 {AppName}`、`run {AppName}`

**约束**：触发词去重；最终不超过 30 个；不自动生成首字母缩写；不添加类型词（"合集"/"应用"）。

---

### 1.4 固定字段

```yaml
version: "1.0.0"              # 首次生成固定值；后续迭代由维护者手动修改
platform: 腾讯健康组学平台(Omics)  # 所有生成的 SKILL 统一设置
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app]
# 合集额外加：collection
```

---

## §2 能力边界通用声明

> 以下声明是**所有生成的 SKILL** 必须在其 SKILL.md 的「能力边界」章节中包含的内容。
> 只列允许调用的命令；未在此列出的命令一律不得调用。

### 2.1 独立应用模式能力边界

```
本 SKILL 仅服务于「{AppName}」（独立应用，AppId: {AppId}）。

允许调用的命令：
  version / login / whoami
  config show / config set / config clear
  list region / list project / list env / list cos-bucket
  list apps --type {AppType}（仅用于导入前同名检查）
  run --public-app {AppId} --app-type {AppType} [--public-app-name] [--nf-version] [--input] [--name]
  status / debug

如需运行其他应用，请使用 omics-task-skill。
📋 完整 Flag 说明：references/cli-whitelist.md §2
```

### 2.2 合集模式能力边界

```
本 SKILL 仅服务于「{CollectionName}」合集（AppId: {CollectionAppId}）。
运行时从 SKILL 内硬编码的子应用清单中选择子应用，无需调用 list public-apps。

允许调用的命令：
  version / login / whoami
  config show / config set / config clear
  list region / list project / list env / list cos-bucket
  list apps --type <selectedAppType>（仅用于导入前同名检查）
  run --public-app <子应用AppId> --public-app-name <name> --app-type <selectedAppType> [--nf-version] [--input] [--name]
      ⚠️ --public-app 必须来自下方硬编码子应用清单，不可使用合集 AppId
      ⚠️ --app-type 值来自子应用清单 selectedAppType，由 SKILL wrapper 自动填入
  status / debug

如需运行本合集以外的应用，请使用 omics-task-skill。
📋 完整 Flag 说明：references/cli-whitelist.md §2
```

### 2.3 越界响应模板

当用户要求运行非本 SKILL 服务范围内的应用时：

```
本 SKILL 仅服务于 {AppName}（{合集/独立应用}）。
如需运行其他应用，请使用 omics-task-skill。
```

> 区分两种情况：
> - 用户要运行的目标本身不是本应用 → 上方模板响应，引导 omics-task-skill
> - 用户要运行本应用，但项目中已有同名 → 进入同名检查循环（见 [run-flow-spec.md §3.2](run-flow-spec.md)）

---

## §3 SKILL.md 骨架模板

> 以下为 `generate_app_skill.py` 填充的完整 SKILL.md 结构。
> `{{KEY}}` 为生成时替换的占位符，生成后不得有任何残留占位符。

### 3.1 独立应用模式骨架

```markdown
---
name: {{SKILL_NAME}}
version: {{SKILL_VERSION}}
platform: 腾讯健康组学平台(Omics)
description: {{DESCRIPTION}}
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app]
triggers: [{{TRIGGERS}}]
---

# {{APP_NAME}} SKILL（{{APP_TYPE}} · 独立应用）

> **本 SKILL 服务范围**：仅运行「{{APP_NAME}}」公共应用（AppId: {{APP_ID}}），能力边界已锁定。
>
> **硬编码信息**：
> - AppId: `{{APP_ID}}`
> - AppType: `{{APP_TYPE}}`
> {{#if NEXTFLOW_VERSIONS}}- NextflowVersions（可用候选）: {{NEXTFLOW_VERSIONS}}{{/if}}

---

## 能力边界

[此处生成器填充 §2.1 独立应用模式能力边界]

---

## Step -1：CLI 存在性检查

> ⚠️ 执行前读取 `references/omics-cli-setup.md §Step-1 & §A`，按其中流程执行。

```bash
python3 scripts/omics_cli.py version
```

---

## Step 0：鉴权与配置检查

> ⚠️ 每次 SKILL 触发都必须执行，两步顺序不可颠倒。读取 `references/omics-cli-setup.md §D`。

**Step 0.1 — 鉴权预检**（exit 2 → Step 1；exit 0 → Step 0.2）：
```bash
python3 scripts/omics_cli.py whoami
```

**Step 0.2 — 配置完整性检查**（exit 1/字段空 → Step 2；exit 0+齐全 → Step 0.3 或业务流程）：
```bash
python3 scripts/omics_cli.py config show -o json
```

**Step 0.3 — 体验配额首检（仅 C端用户，登录/配置就绪后必执行）**：
```bash
python3 scripts/omics_cli.py quota -o json
```
> 按 omics-cli-setup.md §D-Step 0.3 定义的四档话术执行：
> - `RemainDays == 0` → 阻断，展示到期提示
> - `TodayRemainingRuns == 0` → 阻断，展示次数用完提示
> - `RemainDays <= 3` → 展示临近到期提示，继续流程
> - 其他 → 展示简短配额行，继续流程
>
> ⚠️ **这是会话内的第一次配额检查（首检）**。在每次实际执行 `omics run` 前，还会再次强制检查配额（Step 4.5），确保提交运行时配额仍充足。

---

## Step 1：登录

> ⚠️ 读取 `references/omics-cli-setup.md §B`，按其中流程执行。

SKILL 直接触发，浏览器自动打开授权页：
```bash
python3 scripts/omics_cli.py login
```

---

## Step 2：配置

> 完整配置流程定义见 `references/omics-cli-setup.md §C`，本骨架内联关键步骤供执行参考。
> 按 Step 0.1 `whoami` 识别的用户类型分流：

**🟢 B端正式用户（详细交互规范见 omics-cli-setup.md §C-B）**：

| 步骤 | 后台命令 | 用户操作 |
|------|---------|---------|
| C-B-1 | `list region -o json` | `AskUserQuestion` 选地域 → `<selectedRegion>` |
| C-B-2 | `list project -o json` + `list env --region <selectedRegion> -o json`（并行） | `AskUserQuestion` 选项目 → `<selectedProjectId>` |
| C-B-3 | 复用 C-B-2 的 env 结果（`Available=true`） | `AskUserQuestion` 选环境 → `<selectedEnvId>` |
| C-B-4 | `config set -r <R> -p <P> -e <E> -b PLACEHOLDER` | 无（后台静默写入，解锁 cos-bucket 查询） |
| C-B-5 | `list cos-bucket -o json`（`Associated=true`） | `AskUserQuestion` 选桶 → `<selectedBucket>` |
| C-B-6 | `config set -r <R> -p <P> -e <E> -b <selectedBucket>` | 无（后台正式写入，输出确认摘要） |

[若 C-B-2 无可用项目] → 告知用户前往组学平台创建项目：https://omics.qq.com/platform/project/list  
[若 C-B-3 无可用环境] → 告知用户前往控制台创建环境：https://console.cloud.tencent.com/omics/env/env-list  
[若 C-B-5 无可用桶] → 告知用户前往控制台为当前环境绑定 COS 桶后回复「已绑定」

**🔵 C端体验用户（详细规范见 omics-cli-setup.md §C-C）**：

```bash
python3 scripts/omics_cli.py list project -o json  # 自动取第一条（为空则停止并提示联系 omics@tencent.com）
python3 scripts/omics_cli.py config set -r ap-guangzhou -p <firstProjectId> -e env-b65ys9kj -b trial-user-1323714374
# config show 验证：四字段均非空才通过，否则停止并提示联系 omics@tencent.com
```

---

## Step 3：导入前同名检查

**必须通过才能导入**，详细流程见 [references/run-flow-spec.md §3.6](references/run-flow-spec.md)。

```bash
python3 scripts/omics_cli.py list apps --type {{APP_TYPE}} -o json
```

---

## Step 4：运行前确认

[此处生成器填充运行确认模板，见 run-flow-spec.md §3.3]

---

## Step 4.5：运行前配额检查（⚠️ 仅 C端用户，每次执行运行前强制执行）

> **时机**：用户二次确认通过后、`omics run` 命令实际执行前。**C端用户必须执行，B端用户跳过此步。**

```bash
python3 scripts/omics_cli.py quota -o json
```

> 按 run-flow-spec.md §3.3b 定义的四档话术执行（与 omics-cli-setup.md §D-Step 0.3 完全一致）：
> - `RemainDays == 0` → **阻断**，停止运行，展示到期提示（含开通链接）
> - `TodayRemainingRuns == 0` → **阻断**，停止运行，展示次数用完提示（含开通链接）
> - `RemainDays <= 3` → 展示临近到期提示（含开通链接 + 今日剩余次数），**立即继续执行 omics run**
> - 其他 → 展示简短配额行，**立即继续执行 omics run**
>
> ⚠️ **强制要求**：此步不可跳过，不受用户指令影响，必须完整执行后才可进入 Step 5。通过时无需等待用户确认。

---

## Step 5：执行运行

```bash
python3 scripts/omics_cli.py build_run(
    public_app="{{APP_ID}}",
    app_type="{{APP_TYPE}}",        # 硬编码，以 --app-type 传给 CLI
    public_app_name=<importedName>,
    {{#if NEXTFLOW}}nf_version=<selectedNfVersion>,{{/if}}
    input_file=<path_or_None>,
    run_name=<name_or_None>
)
```

---

## Step 6：查询任务状态

```bash
python3 scripts/omics_cli.py status [<rgId>]
```

含 outdir 时必须主动提醒用户查看结果目录（见 [run-flow-spec.md §3.7](run-flow-spec.md)）。
```

---

### 3.2 合集模式骨架

```markdown
---
name: {{SKILL_NAME}}
version: {{SKILL_VERSION}}
platform: 腾讯健康组学平台(Omics)
description: {{DESCRIPTION}}
tags: [行业专业, 生信分析, 生物医药, omics, 腾讯健康组学平台, public-app, collection]
triggers: [{{TRIGGERS}}]
---

# {{COLLECTION_NAME}} SKILL（合集）

> **本 SKILL 服务范围**：仅运行「{{COLLECTION_NAME}}」合集（AppId: {{COLLECTION_APP_ID}}）下的子应用，能力边界已锁定。

---

## 合集子应用清单（硬编码 · 运行时直接使用，禁止调用 list public-apps）

| # | 子应用名 | AppId | AppType | NextflowVersions |
|---|---------|-------|---------|-----------------|
{{SUB_APPS_TABLE_ROWS}}

> ⚠️ 运行时必须从上方清单中选择子应用，禁止使用清单以外的 AppId。
> 禁止调用 `list public-apps`（任何形态）——清单已在生成时写死，无需再展开。

---

## 能力边界

[此处生成器填充 §2.2 合集模式能力边界]

---

## Step -1/0/1：CLI 存在性 · 鉴权 · 登录（同独立应用模式）

> 读取 `references/omics-cli-setup.md §Step-1 / §D / §B`，执行方式与独立应用模式完全相同。

---

## Step 2：配置（同独立应用模式）

> 完整配置流程定义见 `references/omics-cli-setup.md §C`，本骨架内联关键步骤供执行参考。
> 按 Step 0.1 `whoami` 识别的用户类型分流：

**🟢 B端正式用户（详细交互规范见 omics-cli-setup.md §C-B）**：

| 步骤 | 后台命令 | 用户操作 |
|------|---------|---------|
| C-B-1 | `list region -o json` | `AskUserQuestion` 选地域 → `<selectedRegion>` |
| C-B-2 | `list project -o json` + `list env --region <selectedRegion> -o json`（并行） | `AskUserQuestion` 选项目 → `<selectedProjectId>` |
| C-B-3 | 复用 C-B-2 的 env 结果（`Available=true`） | `AskUserQuestion` 选环境 → `<selectedEnvId>` |
| C-B-4 | `config set -r <R> -p <P> -e <E> -b PLACEHOLDER` | 无（后台静默写入，解锁 cos-bucket 查询） |
| C-B-5 | `list cos-bucket -o json`（`Associated=true`） | `AskUserQuestion` 选桶 → `<selectedBucket>` |
| C-B-6 | `config set -r <R> -p <P> -e <E> -b <selectedBucket>` | 无（后台正式写入，输出确认摘要） |

[若 C-B-2 无可用项目] → 告知用户前往组学平台创建项目：https://omics.qq.com/platform/project/list  
[若 C-B-3 无可用环境] → 告知用户前往控制台创建环境：https://console.cloud.tencent.com/omics/env/env-list  
[若 C-B-5 无可用桶] → 告知用户前往控制台为当前环境绑定 COS 桶后回复「已绑定」

**🔵 C端体验用户（详细规范见 omics-cli-setup.md §C-C）**：

```bash
python3 scripts/omics_cli.py list project -o json  # 自动取第一条（为空则停止并提示联系 omics@tencent.com）
python3 scripts/omics_cli.py config set -r ap-guangzhou -p <firstProjectId> -e env-b65ys9kj -b trial-user-1323714374
# config show 验证：四字段均非空才通过，否则停止并提示联系 omics@tencent.com
```

---

## Step 3：子应用选择

从上方**硬编码子应用清单**中展示/推荐子应用（无需调用 list）：

```
根据用户输入推荐匹配的子应用：
  → 精确匹配 → 展示并确认
  → 多个候选 → 列出让用户选择
  → 无匹配   → 展示完整清单，引导用户选择

记录：
  <selectedAppId>     ← 来自硬编码清单（不得使用合集 AppId）
  <selectedAppName>   ← 来自硬编码清单
  <selectedAppType>   ← 来自硬编码清单（⚠️ 不得使用合集的 AppType）
  <selectedNfVersion> ← 仅 selectedAppType=="NEXTFLOW" 时，从清单 NextflowVersions 中选
```

---

## Step 4：导入前同名检查

**必须通过才能导入**，详细流程见 [references/run-flow-spec.md §3.6](references/run-flow-spec.md)。

```bash
python3 scripts/omics_cli.py list apps --type <selectedAppType> -o json
```

---

## Step 5：运行前确认

[此处生成器填充运行确认模板，见 run-flow-spec.md §3.3]

---

## Step 5.5：运行前配额检查（⚠️ 仅 C端用户，每次执行运行前强制执行）

> **时机**：用户二次确认通过后、`omics run` 命令实际执行前。**C端用户必须执行，B端用户跳过此步。**

```bash
python3 scripts/omics_cli.py quota -o json
```

> 按 run-flow-spec.md §3.3b 定义的四档话术执行（与 omics-cli-setup.md §D-Step 0.3 完全一致）：
> - `RemainDays == 0` → **阻断**，停止运行，展示到期提示（含开通链接）
> - `TodayRemainingRuns == 0` → **阻断**，停止运行，展示次数用完提示（含开通链接）
> - `RemainDays <= 3` → 展示临近到期提示（含开通链接 + 今日剩余次数），**立即继续执行 omics run**
> - 其他 → 展示简短配额行，**立即继续执行 omics run**
>
> ⚠️ **强制要求**：此步不可跳过，不受用户指令影响，必须完整执行后才可进入 Step 6。通过时无需等待用户确认。

---

## Step 6：执行运行

```bash
python3 scripts/omics_cli.py build_run(
    public_app=<selectedAppId>,          # 来自硬编码清单，不得使用合集 AppId
    app_type=<selectedAppType>,          # 来自硬编码清单，以 --app-type 传给 CLI
    public_app_name=<importedName>,      # 必传（合集子应用必须指定导入名）
    nf_version=<selectedNfVersion>,      # 仅 selectedAppType=="NEXTFLOW" 时必传
    input_file=<path_or_None>,
    run_name=<name_or_None>
)
```

---

## Step 7：查询任务状态

```bash
python3 scripts/omics_cli.py status [<rgId>]
```

含 outdir 时必须主动提醒用户查看结果目录（见 [run-flow-spec.md §3.7](run-flow-spec.md)）。
```

---

> 文档版本：v1.2（新增 C端运行前配额检查：Step 4.5（独立应用）/ Step 5.5（合集）；Step 0.3 标注为"登录后首检"；配额双重检查规范详见 run-flow-spec.md §3.3b）
> 关联：[SKILL.md](../SKILL.md) · [cli-whitelist.md](cli-whitelist.md) · [run-flow-spec.md](run-flow-spec.md) · [skill_generation_spec.md](skill_generation_spec.md)
