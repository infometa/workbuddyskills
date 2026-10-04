# CLI / SKILL 边界契约（v7.0）

> 本文档定义 omics-platform-cli 与 omics-task-skill 之间不可违反的能力边界。
> CR 与日常巡检按本文档执行。

---

## 1. 唯一合法出口：命令白名单

SKILL 通过 wrapper（`scripts/omics_cli.py`）调用 CLI；wrapper 在 argparse 层物理上只注册以下命令：

| # | 命令 | 子动作 | 写/读 | SKILL 是否可主动调 |
|---|---|---|---|---|
| 1 | `omics login` | — | 写 token | ✅ SKILL 主动调用，拉起浏览器授权（OAuth 浏览器回调需在本机完成） |
| 2 | `omics whoami` | — | 读 | ✅ |
| 3 | `omics config` | `show` / `set` / `clear` | 读 / 写本地 / 删本地 | ✅ show/clear；✅ set **仅在配置引导流程中调用，参数必须来自用户选择** |
| 4 | `omics list` | `region` / `project` / `env` / `cos-bucket` / `volume` | 读 | ✅（配置引导与运行前查询） |
| 5 | `omics list` | `public-apps` / `apps` / `versions` / `templates` | 读 | ✅ |
| 6 | `omics run` | —（form A/B/C/D + 版本管理）| 写远端任务 | ✅ **必须先二次确认** |
| 7 | `omics status` | — | 读 | ✅ |
| 8 | `omics debug` | `<rgId>` / `--run` / `--run + --job` | 读 | ✅ |
| 9 | `omics quota` | — | 读 | ✅（仅 C 端体验用户） |
| 10 | `omics cos` | `upload` / `ls` | 写 COS / 读 COS | ✅ upload 需确认；ls 免确认 |

> CLI 自身还有 `version` / `update` / `uninstall` 工具命令：
> - `version`：允许调用（CLI 存在性检查）
> - `update` / `uninstall`：SKILL 不调用，仅在必要时向用户介绍

### v7.0 白名单变更汇总

| 变更项 | 旧状态 | 新状态 |
|--------|--------|--------|
| `omics cos upload` | 不存在（旧版依赖 coscli/mc 等第三方工具）| ✅ 新增，CLI 内置实现，SKILL 可调用引导用户上传 |
| `omics cos ls` | 不存在 | ✅ 新增，CLI 内置实现，SKILL 可调用浏览 COS 目录 |
| `--cos-tool` flag | 已废弃（CLI 已移除）| ❌ 不存在，禁止使用 |

### form B `--app-type` 强制要求

`omics run --public-app` 时，**必须**显式传入 `--app-type WDL` 或 `--app-type NEXTFLOW`，
不可省略让 CLI 自行猜测（CLI 默认兜底 WDL，但 SKILL 必须明确传入避免歧义）。

### run 前置确认（必经）

SKILL 触发 `omics run ...` 前必须按 §3 模板完成二次确认：

1. 拼出完整命令字符串（含所有 flag）
2. 输出参数摘要表（形态 / 应用 / 项目 / 环境 / 输入 / NF 版本 / output-dir 等关键项）
3. 询问用户："以上命令是否执行？(y / 确认 / 继续)"
4. 仅当收到明确肯定答复（y / yes / 确认 / 继续 / 是 / 执行 / OK）才调用
5. 用户拒绝（n / no / 取消）→ 终止；模糊回复 → 再次明确询问
6. 用户追加修改 → 回到 1 重拼

### C 端用户配额检查（必经）

C 端体验用户触发 `omics run ...` 前，除二次确认外，还需：

1. 每次 SKILL 启动后（Step 0.3）执行一次配额首检
2. **每次 `omics run` 前**再次调用 `omics quota` 检查 `run_remain_limit > 0`
3. `run_remain_limit == 0` → **禁止继续**，展示用完提示，不进入二次确认
4. 此检查不受用户指令影响，不可跳过

---

## 2. 严令禁止的反例

| 反例 | 违反原则 |
|------|---------|
| SKILL 直调 `requests.post("https://omics.../CommonAppService...")` | 直调后端 API → 绕开命令审计 |
| SKILL 自己 `subprocess.run(["curl", ...])` 拼 HTTP 调用 | 同上 |
| SKILL 拼出 `omics run` 但不向用户列摘要+完整命令、不询问 y/N | 跳过二次确认 |
| SKILL 拼出 `omics app ...` / `omics project list` / `omics import ...` | 编造已废弃命令 |
| SKILL 调 `omics config set` 时使用猜测/编造的参数值 | 参数必须来自用户选择（list + AskUserQuestion） |
| SKILL 为 form B 省略 `--app-type` | 默认兜底歧义，必须显式指定 |
| SKILL 对 form D 使用 `--update` | CLI 运行时强制拒绝；form D 每次新建应用 |
| SKILL 运行 form D 前让用户安装 coscli/mc/aws 等本地 COS 工具 | `omics cos upload` 是官方内置命令，CLI 已移除 `--cos-tool`，无需第三方工具 |
| SKILL 自动给同名应用加后缀绕过冲突 | 命名属用户治理空间，不可代决策 |
| SKILL 看到 OOMKilled 直接改 WDL 的 memory + 自动重跑 | 替用户做症状判断 + auto-chain |
| 用户说"导入这个公共应用"，SKILL 单独执行导入步骤 | 导入是 run --public-app 的内部步骤 |
| C 端用户 run 前跳过配额检查 | 违反 C 端配额保护规则，不受用户指令影响 |

---

## 3. run 前置确认时序

```
SKILL 拼 run 命令 (build_run)
        │
        │ [C端用户]
        ├─→ omics quota → run_remain_limit == 0 → 阻断（不进入确认）
        │                run_remain_limit > 0  → 继续
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
y/yes/确认/      → [否定]：终止，等用户进一步指示
继续/OK/是/      → [修改]：解析意图 → 重拼 → 重走确认
执行             → [模糊]：再次明确询问 y/N
   │
   ▼
cli.execute(...)
   │
   ▼
解析 RunGroupId / 处理错误码 / 鉴权失败引导 omics login
```

**关键约束**：

1. SKILL 输出的命令字符串必须**完整等同于** `cli.execute` 真正调用的命令
2. 摘要表必须列出对用户决策重要的字段：形态 / 应用 / 项目 / 环境 / 输入 / NF 版本 / output-dir
3. 用户只回"嗯/好/可以/试试"等模糊回复时，**不视作肯定**，必须再问一次

---

## 4. CLI 端的契约义务

| CLI 义务 | 实现位置 |
|---|---|
| form D `--update` 与 `--nf` 互斥 → 运行时强制报错 | `cmd/run.go` runRun |
| form D `--nf-version` 缺失 → `MISSING_NF_VERSION_COS` 含候选列表 | `cmd/run.go` prepareCosNf |
| form D `--nf` COS 路径格式无效 → `INVALID_COS_PATH` | `cmd/run.go` prepareCosNf |
| form D 服务端直接从 CosSource 读取 NF 源码（无需客户端 SaveApplicationFiles） | `cmd/run.go` prepareCosNf → CreateApplication(CosSource) |
| `--public-app-name` 缺失 + 合集子应用 → 主动报错 | `cmd/run.go` form B 兜底逻辑 |
| `--nf-version` 缺失 + NEXTFLOW 公共应用（form B）→ `MISSING_NF_VERSION` 含候选列表 | `cmd/run.go` |
| `--input` 缺失 + 运行 NF 应用（form C）→ `MISSING_INPUT_NF_RUN` | `cmd/run.go` form C 分支 |
| 参数合并失败 → `PARAM_MERGE_FAILED` 结构化报错（含 Specs/Report/PartialSkeleton/Hint） | `cmd/run.go` |
| form B 导入成功但 run 失败 → 自动回滚删除孤儿应用 | `cmd/run.go` runPipelineWithRollback |
| form C 运行前打印可用版本清单（table 模式）+ 支持 --version 指定版本 | `cmd/run.go` printAvailableVersions |
| `DUPLICATE_APP_NAME` 三选项结构化输出（含 ConflictApplicationId） | `cmd/run.go` duplicateNamePayload |
| `omics list public-apps` 按 AppTag 客户端分组（多 Tag 重复展示，去重 TotalApps） | `cmd/list_public_apps.go` |
| `omics debug` 三段式只取证不做症状匹配；v6 按 WDL/NF 分流采集 | `cmd/debug.go` |
| `omics debug` NF 分支额外采集 NextflowLog（头 8KB + 尾 56KB） | `cmd/debug.go` |
| `omics status` / `omics list apps` 固定走 config 项目，不支持 `-p` | `cmd/status.go` / `cmd/list_apps.go` |
| 鉴权失败统一退出码 2，业务错误退出码 1 | `internal/cliexit/` |
| Debug 重跑 = 重新调用 RunApplication（非独立 RetryRuns 接口） | `--app + [--version] + --input <fixed.json>` |
| `omics quota` 先校验用户为 C 端体验用户，非 C 端直接报错退出 | `cmd/quota.go` |
| `omics cos upload` 通过平台预签名 PUT URL 实现，无需第三方工具，显式桶须校验绑定关系 | `cmd/cos_upload.go` |
| `omics cos ls` 通过平台 API 列出对象，无需第三方工具 | `cmd/cos_ls.go` |
| `--cos-tool` 已移除，CLI 不再支持此选项 | 移除于 v7 重构 |

---

## 5. 结果引导规则

| 条件 | SKILL 行为 |
|------|-----------|
| `omics run` 入参**包含** `--output-dir <cos-path>` | 任务成功后，告知用户结果在 `<cos-path>`，提供 `omics cos ls <cos-path>` 命令和组学平台控制台链接 |
| `omics run` 入参**不包含** `--output-dir` | 引导用户前往组学平台任务详情页：`https://omics.qq.com/platform/tasks` |
| NF 应用启用 `--nf-report` | debug 段 2 输出含 `WithReports`（4 个 HTML 报告 CosSignedUrl），SKILL 主动告知用户 URL |

---

## 6. CR 检查项

| 检查项 | 通过标准 |
|--------|---------|
| SKILL 新增的 builder 是否只调白名单命令 | `grep -E "build_(login\|whoami\|config_show\|config_set\|config_clear\|list_region\|list_project\|list_env\|list_cos_bucket\|list_volume\|list_public_apps\|list_apps\|list_versions\|list_templates\|run\|status\|debug\|quota\|version\|cos_upload\|cos_ls)" scripts/omics_cli.py` 应覆盖全部对外 builder |
| wrapper argparse 顶层是否只注册白名单命令 | `subparsers.add_parser` 调用的命令名只能在 {login, whoami, version, config, list, run, status, debug, quota, cos} |
| SKILL 是否引入 HTTP 客户端 | `grep -nE "import (requests\|http\|httpx\|urllib)" skills/omics-task-skill/` 应为空 |
| SKILL 是否使用 `subprocess` 调非 omics 命令 | `grep -n "subprocess" scripts/omics_cli.py` 仅在 `cli.execute` 内部调 omics 二进制 |
| run 前置确认是否在 SKILL.md / wrapper 中明文要求 | SKILL.md "能力边界"章节 + §4.2 模板存在 |
| config set 调用时是否带全四个参数 | `build_config_set` 调用方必须传入所有 4 个参数 |
| form B 是否显式传入 `--app-type` | `build_run(public_app=..., app_type=...)` 中 app_type 不为 None |
| form D 是否误用 `--update` | `build_run(nf_cos_path=..., update_app_id=...)` 会在 wrapper 层 raise ValueError |
| C 端 run 前是否调了 quota 检查 | SKILL.md §4.1 C 端规则存在且不可跳过 |
| cos upload 是否引导用户安装第三方工具 | 禁止出现 coscli / mc / aws / --cos-tool 字样 |

---

## 7. 例外条款

如确实出现下面这些情况，请走"先讨论后改契约"流程：

- **新增能力**：先在 CLI 加命令 + 文档，再在 SKILL 加 builder + SKILL.md 章节，**不允许 SKILL 抢跑**
- **临时调试**：通过 wrapper 的 `--cli-path` 指向自定义 CLI 二进制
- **数据探测**（如确实需要直查某个未暴露的元数据）：作为 CLI 内部辅助实现，不对外暴露

---

## 8. 修订历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.0 | 2026-08-27 | 新增 `omics cos upload` / `omics cos ls` 白名单（CLI 内置，无需第三方工具）；明确 `--cos-tool` 已从 CLI 移除；新增 C端 run 前配额检查规则（不可跳过）；补充 form B 孤儿应用自动回滚说明；结果引导增加组学平台控制台链接；CR 检查项扩展 cos 相关检查点 |
| v6.0 | 2026-08-21 | `omics login` 改为 SKILL 主动调用；`omics config set` 权限放开（配置引导场景）；list 白名单扩展（region/project/env/cos-bucket/volume）；新增 quota 命令；form D `--update` 明确禁止；form D 主流程更新为服务端直接读 COS 源码（无需本地 COS 工具）；form B `--app-type` 强制要求；新增结果引导规则 |
| v5.2 | 2026-06-10 | form D `--nf-version` 改为必填；form C 运行 NF 版本来源改为应用信息 `NextflowVersion` 字段；form B NF 版本来源明确为应用 `NextflowVersion[]` |
| v5.1 | 2026-06-09 | form D `--nf-version` 改为可选；form C 运行 NF 必须指定 `--nf-version`+`--input`；COS 同步工具多策略（`--cos-tool`）；未安装任何工具时引导安装 coscli |
| v5 | 2026-06-09 | 版本管理（--version）；形态 D（COS NF --nf）；Debug 重跑模式；coscli COS 同步集成 |
| v4 | 2026-06-01 | 锁定 7 命令白名单；废除 `app *` 命令族；新增 `list public-apps / apps`；强化 run 前置确认 |
| v3 | 2026-05-29 | baseline + override 合并模式；form B 自动模板路径 |
| v2 | 2026-04 | OAuth 登录；config 强制校验；status 固定走 config |

---

> 文档拥有者：组学平台 CLI / SKILL 联合维护
> 关联：[SKILL.md](SKILL.md) / [references/cli_commands.md](references/cli_commands.md) / [references/omics-cli-setup.md](references/omics-cli-setup.md)
