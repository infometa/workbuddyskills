# CLI 命令白名单（omics-common-app-skill）

> **权威来源**：本文档列出 omics-common-app-skill 生态中**允许调用**的全部 CLI 命令。
> 未在本文档中出现的命令，一律不得调用。

---

## §1 元 SKILL 可用命令（生成流程）

> 适用：omics-common-app-skill 元 SKILL 执行"查询公共应用 → 生成专用 SKILL"的完整流程。

| 命令 | 允许的子动作 / Flag | 用途 |
|------|-------------------|------|
| `omics version` | — | CLI 存在性检查 |
| `omics login` | — | SKILL 主动触发浏览器 OAuth 授权（`whoami` exit 2 时） |
| `omics whoami` | — | 鉴权预检 + 判断用户类型（B端 / C端） |
| `omics config show` | `[-o json]` | 检查当前配置是否完整 |
| `omics config set` | `-r <region> -p <projectId> -e <envId> -b <bucket>` | 写入配置（四参数必须全由 list 命令查询后用户选定） |
| `omics config clear` | — | 清除本地配置 |
| `omics list region` | `[-o json]` | B端配置：查询可用地域列表 |
| `omics list project` | `[-o json]` | B端/C端配置：查询用户项目列表 |
| `omics list env` | `[--region <region>] [-o json]` | B端配置：查询环境列表 |
| `omics list cos-bucket` | `[-o json]` | B端配置：查询当前环境绑定的 COS 桶 |
| `omics list public-apps` | `[-o json] [--tag] [--keyword] [--type] [--parent-app]` | 查询公共应用列表；`--parent-app` 用于生成合集 SKILL 前展开子应用 |
| `omics quota` | `[-o json]` | **仅供参考**：元 SKILL 不直接调用，此命令由生成的子 SKILL 在 Step 0.3 使用（C端专用，见 §2） |

---

## §2 产物 SKILL 可用命令（运行时）

> 适用：omics-common-app-skill 生成的所有专用 SKILL（独立应用模式 + 合集模式）。

| 命令 | 允许的子动作 / Flag | 用途 |
|------|-------------------|------|
| `omics version` | — | CLI 存在性检查 |
| `omics login` | — | SKILL 主动触发浏览器 OAuth 授权（`whoami` exit 2 时） |
| `omics whoami` | — | 鉴权预检 + 判断用户类型 |
| `omics config show` | `[-o json]` | 检查当前配置是否完整 |
| `omics config set` | `-r <region> -p <projectId> -e <envId> -b <bucket>` | 写入配置 |
| `omics config clear` | — | 清除本地配置 |
| `omics list region` | `[-o json]` | 配置阶段：查询地域 |
| `omics list project` | `[-o json]` | 配置阶段：查询项目 |
| `omics list env` | `[--region <region>] [-o json]` | 配置阶段：查询环境 |
| `omics list cos-bucket` | `[-o json]` | 配置阶段：查询 COS 桶 |
| `omics list apps` | `--type <AppType> [-o json]` | 导入前同名检查（`--type` 必填） |
| `omics run` | `--public-app <AppId> [--public-app-name <name>] --app-type <WDL|NEXTFLOW> [--nf-version <ver>] [--input <path>] [--template <InputTemplateId>] [--name <runName>] [-o json]` | 运行公共应用（AppId 在 SKILL 中硬编码，不可替换；AppType 在 SKILL 中硬编码，由 wrapper 自动填入） |
| `omics status` | `[<rgId>] [-o json]` | 查询任务状态 |
| `omics debug` | `<rgId> [-o json]` / `--run <uuid> [-o json]` / `--run <uuid> --job <jobId>` | 异步任务失败取证 |
| `omics quota` | `[-o json]` | **C端专用**：每次 Step 0 通过后查询体验配额（RemainDays + TodayRemainingRuns），根据结果展示话术或阻断流程（详见 omics-cli-setup.md §D-Step 0.3） |

> **`omics run` 说明**：
> - `--public-app` 的值在 SKILL 生成时硬编码写死，运行时不可替换
> - `--app-type` **必传**，值在 SKILL 生成时硬编码写死（来自公共应用的 AppType），由 wrapper 自动填入，无需用户填写
> - 合集模式：`--public-app` 必须来自 SKILL 内硬编码的子应用清单，`--public-app-name` 必传，`--app-type` 来自子应用清单的 `selectedAppType`
> - `--nf-version` 仅 NEXTFLOW 类型时必传，候选值来自硬编码清单的 `NextflowVersions[]`
> - 未传 `--input` 且未传 `--template` 时，CLI 按优先级自动选取运行参数模板：优先选 Name == `input.json_{Region}` 的模板（Region 来自当前 config，如 `ap-guangzhou`）；无命中取第一条；无模板时 fail，需用户通过 `--input` 显式提供运行参数
> - `--input` 与 `--template` 互斥

---

## §3 变更流程

若需新增或修改允许的命令/Flag，同步更新：
1. 本文档（`cli-whitelist.md`）
2. `../SKILL.md`（元 SKILL 能力边界章节）
3. `../CONTRACT.md`（边界契约）
4. `skill_generation_spec.md`（如涉及生成器参数）
