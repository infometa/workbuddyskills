# CLI / SKILL 边界契约（v5.1）

> 本文档定义 omics-platform-cli 与 omics-task-skill 之间不可违反的能力边界。
> CR 与日常巡检按本文档执行。

---

## 1. 唯一合法出口：7 命令白名单

SKILL 通过 wrapper（`scripts/omics_cli.py`）调用 CLI；wrapper 在 argparse 层物理上只注册以下 7 条一级命令：

| # | 命令 | 子动作 | 写/读 | SKILL 是否可主动调 |
|---|---|---|---|---|
| 1 | `omics login` | — | 写 token | ❌ 引导用户在本机执行（OAuth 浏览器回调） |
| 2 | `omics whoami` | — | 读 | ✅ |
| 3 | `omics config` | `show` / `clear`（**不暴露 `set`**） | 读 / 删本地 | ✅ show / clear；❌ set 由用户本机执行 |
| 4 | `omics list` | `public-apps` / `apps` | 读 | ✅ |
| 5 | `omics run` | —（v5：四形态 A/B/C/D + 版本管理 `--version`） | 写远端任务 | ✅ **必须先二次确认** |
| 6 | `omics status` | — | 读 | ✅ |
| 7 | `omics debug` | `<rgId>` / `--run` / `--run + --job` | 读 | ✅ |

> CLI 自身还有 `version` 工具命令，不属业务白名单但允许调用。

### v5.1 新增 flag 汇总（挂在 omics run 下）

| flag | 适用形态 | 必填性 | 说明 |
|---|---|---|---|
| `--nf <cos-path>` | D（COS NF） | form D 必填 | COS 上的 NF 应用路径，格式 `cos://bucket-name/prefix/`；用户需先通过 COS 工具上传 |
| `--cos-tool <tool>` | D（COS NF） | 可选 | 指定 COS 同步工具：auto(默认) / coscli / mc / aws / coscmd / python_cos；auto 模式全未检测到时引导安装 coscli |
| `--nf-version` | B / C(NF) / D | form B(NF) 必填（版本从应用 `NextflowVersion[]` 获取）；form C(运行NF应用) 必填（版本从应用信息 `NextflowVersion` 字段获取，不用默认列表）；form D 必填（版本从默认候选列表 22.10.7/23.10.1/23.10.3/24.04.3/25.10.2 选取） | NF 引擎版本号 |
| `--version <VerId>` | C / A / D | 可选 | 指定目标 ApplicationVersionId 运行 |
| `--input <path>` | C(NF) | form C 运行 NF 应用时必填 | 运行参数 JSON（NF 无 Validate baseline，必须显式提供） |

---

## 2. 严令禁止的反例

| 反例 | 违反原则 |
|---|---|
| SKILL 直调 `requests.post("https://omics.../CommonAppService.DescribeCommonApp", ...)` | 直调后端 API → 绕开命令审计 |
| SKILL 自己 `subprocess.run(["curl", ...])` 拼 HTTP 调用 | 同上 |
| SKILL 用 `omics run --wdl` 但不向用户列摘要+完整命令、不询问 y/N，直接发起 | 跳过二次确认 |
| SKILL 拼出 `omics app ...` / `omics project list` / `omics import ...` | 编造已废弃命令 |
| SKILL 自动给同名应用加 `-1` / `-cli` / 时间戳后缀绕过冲突 | 命名属用户治理空间，不可代决策 |
| SKILL 看到 OOMKilled 直接改 WDL 的 memory + 自动重跑 | 替用户做症状判断 + auto-chain |
| 用户说"导入这个公共应用"，SKILL 单独执行导入步骤（不随 run 一起发生） | "导入"不是独立动作，必须随 run 内化执行 |
| 用户说"列出应用 X 的参数模板"，SKILL 拼旧的 `omics app templates --app X` | 命令已废除，模板已内化到 run |

---

## 3. run 前置确认时序

```
SKILL 拼 run 命令 (build_run)
        │
        ▼
┌────────────────────────────────┐
│ 输出参数摘要表 + 完整命令字符串 │
│ 询问用户：是否执行？(y / N)    │
└──────────┬─────────────────────┘
           │
   ┌───────┴────────┐
   │                │
   ▼                ▼
[肯定答复]      [否定答复 / 修改 / 模糊]
y/yes/确认/      ─→ [否定]：终止，等用户进一步指示
继续/OK/是/      ─→ [修改]：解析意图 → 重拼 → 重走确认
执行             ─→ [模糊]：再次明确询问 y/N
   │
   ▼
cli.execute(...)
   │
   ▼
解析 RunGroupId / 处理 PARAM_MERGE_FAILED / 鉴权失败转步骤 1/2 引导
```

**确认模板**：参考 `SKILL.md` §4.2 form A / form C / form B 三个版本。

**关键约束**：

1. SKILL 输出的命令字符串必须**完整等同于** `cli.execute` 真正调用的命令，不可"展示一个命令实际跑另一个"
2. 摘要表必须列出对用户决策重要的字段：形态 / 应用 / 项目 / 环境 / 输入 / NF 版本 / `--update` 复用应用 ID
3. 用户只回"嗯/好/可以/试试"等模糊回复时，**不视作肯定**，必须再问一次

---

## 4. CLI 端的契约义务

CLI 端为支撑 SKILL 边界设计提供以下保障：

| CLI 义务 | 实现位置 |
|---|---|
| `--public-app-name` 缺失 + 合集子应用 → 主动报错而非建空名应用 | `cmd/run.go` 形态 B 兜底逻辑 |
| `--nf-version` 缺失 + NEXTFLOW 公共应用（form B） → `MISSING_NF_VERSION` 含候选列表 | `cmd/run.go` |
| `--nf-version` 缺失 + 运行 NF 应用（form C） → `MISSING_NF_VERSION_RUN`（SKILL 应从应用信息的 `NextflowVersion` 字段获取版本，不要使用默认列表） | `cmd/run.go` form C 分支 |
| `--input` 缺失 + 运行 NF 应用（form C） → `MISSING_INPUT_NF_RUN` 含示例命令 | `cmd/run.go` form C 分支 |
| 无可用 COS 同步工具（form D，auto 模式全未检测到） → 引导安装 coscli | `cmd/run.go` resolveCosTool → verifyCosTool / verifyPythonCos |
| COS 路径格式无效（form D） → `INVALID_COS_PATH` | `cmd/run.go` prepareCosNf |
| 参数合并失败 → `PARAM_MERGE_FAILED` 结构化报错（含 Specs/Report/PartialSkeleton/Hint） | `cmd/run.go` |
| form C 运行前打印可用版本清单（table 模式）+ 支持 --version 指定版本运行 | `cmd/run.go` printAvailableVersions + pipeline TargetVersionId |
| form D COS NF 同步+上传 + 版本回显（多工具 syncFromCos + SaveApplicationFiles 返回 NewApplicationVersionId）；**--nf-version 必填**（从默认候选列表选取）；**--cos-tool 可选（默认 auto）** | `cmd/run.go` prepareCosNf + syncFromCos + resolveCosTool |
| `omics list public-apps` 按 AppTag 客户端分组（多 Tag 重复展示，去重 TotalApps） | `cmd/list_public_apps.go` |
| `omics debug` 三段式只取证不做症状匹配 | `cmd/debug.go` |
| `omics status` / `omics list apps` 固定走 config 项目，不支持 `-p` | `cmd/status.go` / `cmd/list_apps.go` |
| 鉴权失败统一退出码 2，业务错误退出码 1 | `internal/cliexit/` |
| Debug 重跑 = 重新调用 RunApplication（非独立 RetryRuns 接口） | `--app + [--version] + --input <fixed.json>` |

---

## 5. CR 检查项

| 检查项 | 通过标准 |
|---|---|
| SKILL 新增的 builder 是否只调白名单命令 | `grep -E "build_(login\|whoami\|config_show\|config_clear\|list_public_apps\|list_apps\|run\|status\|debug\|version)" scripts/omics_cli.py` 应覆盖全部对外 builder |
| wrapper argparse 顶层是否只注册 7 + version | `subparsers.add_parser` 调用的命令名只能在 {login, whoami, version, config, list, run, status, debug} |
| SKILL 是否引入 HTTP 客户端 | `grep -nE "import (requests\|http\|httpx\|urllib)" skills/omics-task-skill/` 应为空 |
| SKILL 是否使用 `subprocess` 调非 omics 命令 | `grep -n "subprocess" scripts/omics_cli.py` 仅在 `cli.execute` 内部调 omics 二进制 |
| run 前置确认是否在 SKILL.md / wrapper 中明文要求 | SKILL.md "能力边界"章节 + §4.2 模板存在 |

---

## 6. 例外条款

如确实出现下面这些情况，请走"先讨论后改契约"流程，不要在不通告的情况下绕开：

- **新增能力**（例如希望加 `omics list runs --tag` 之类）：先在 CLI 加命令 + 文档，再在 SKILL 加 builder + SKILL.md 章节，**不允许 SKILL 抢跑**
- **临时调试**：通过 wrapper 的 `--cli-path` 指向自定义 CLI 二进制，不要在 SKILL 内绕过 wrapper 直跑 binary
- **数据探测**（如确实需要直查某个未暴露的元数据）：作为 CLI 内部辅助实现，不对外暴露用户命令

---

## 7. 修订历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v5.2 | 2026-06-10 | form D `--nf-version` 改为必填（从默认候选列表选取）；form C 运行 NF 版本来源改为应用信息 `NextflowVersion` 字段（不再使用默认候选列表）；form B NF 版本来源明确为应用 `NextflowVersion[]` |
| v5.1 | 2026-06-09 | form D `--nf-version` 改为可选；form C 运行 NF 必须指定 `--nf-version`+`--input`；COS 同步工具多策略（`--cos-tool`：auto/coscli/mc/aws/coscmd/python_cos）；未安装任何工具时引导安装 coscli |
| v5 | 2026-06-09 | 版本管理（--version 选择/回溯运行）；形态 D（COS NF --nf cos-path）；Debug 重跑模式（修正参数重新走 RunApplication）；coscli COS 同步集成 |
| v4 | 2026-06-01 | 锁定 7 命令白名单；废除 `app *` 命令族；新增 `list public-apps / apps`；强化 run 前置确认 |
| v3 | 2026-05-29 | baseline + override 合并模式；form B 自动模板路径 |
| v2 | 2026-04 | OAuth 登录；config 强制校验；status 固定走 config |

---

> 文档拥有者：组学平台 CLI / SKILL 联合维护
> 关联：[SKILL.md](SKILL.md) / [references/cli_commands.md](references/cli_commands.md)
