# CLI / SKILL 边界契约（IgGM(WDL) 单应用收窄版 v1.0.0)

> 本文档定义 omics-platform-cli 与 `iggm-wdl-skill` 之间不可违反的能力边界。
> CR 与日常巡检按本文档执行。

---

## 1. 唯一合法出口：7 命令白名单 + 单应用锁定

iggm-wdl-skill 通过 wrapper（`scripts/omics_cli.py`）调用 CLI；wrapper 在 argparse 层物理上注册 7 条一级命令，
但本 SKILL **只允许**调用以下子集：

| #   | 命令                              | 子动作                                 | 写/读        | SKILL 是否可主动调                                                                                |
| --- | --------------------------------- | -------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------- |
| 1   | `omics login`                     | —                                      | 写 token     | ❌ 引导用户在本机执行（OAuth 浏览器回调）                                                          |
| 2   | `omics whoami`                    | —                                      | 读           | ✅                                                                                                 |
| 3   | `omics config`                    | `show` / `clear`                       | 读 / 删本地  | ✅ show / clear；❌ set 由用户本机执行                                                             |
| 4   | `omics list public-apps`          | `--parent-app (禁用)` | read           | ❌ 整体禁用                                                                    |
| 5   | `omics list apps`                 | —                                      | read           | ✅ **仅限"导入前同名检查"用途**                                                                    |
| 6   | `omics run`                       | —                                      | 写远端任务   | ✅ **必须先二次确认；`--public-app` `--public-app` 固定为 `b65d7070-6e8a-4a57-914d-dbbb9dd9b286`**                    |
| 7   | `omics status`                    | —                                      | read           | ✅                                                                                                 |
| 8   | `omics debug`                     | `<rgId>` / `--run` / `--run + --job`   | read           | ✅                                                                                                 |

> 应用 AppId（锁定）：`b65d7070-6e8a-4a57-914d-dbbb9dd9b286`

---

## 2. 严令禁止的反例

| 反例                                                                                          | 违反原则                                                            |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| SKILL 调 `omics run --wdl <path>`（form A）                                                   | 越界——本 SKILL 只能跑 IgGM(WDL)                              |
| SKILL 调 `omics run --app <ApplicationId>`（form C）                                          | 越界——引导用户去 `omics-task-skill`                                  |
| SKILL 调 `omics run --public-app <非本应用 AppId>` | 越界——必须使用锁定的 AppId                                                               |
| SKILL 直调 `requests.post("https://omics.../...", ...)`                                       | 直调后端 API → 绕开审计                                              |
| SKILL 自己 `subprocess.run(["curl", ...])` 拼 HTTP 调用                                       | 同上                                                                |
| SKILL 用 `omics run` 但不向用户列摘要+完整命令、不询问 y/N，直接发起                           | 跳过二次确认                                                        |
| SKILL 自己挑NF 版本 不让用户决策                                             | 替用户做选型决策                                                    |
| SKILL 看到同名应用直接加 `-1` / `-cli` / 时间戳后缀绕过冲突                                   | 命名属用户治理空间，不可代决策                                       |
| SKILL 看到 OOMKilled 直接改 memory + 自动重跑                                                 | 替用户做症状判断 + auto-chain                                        |
| SKILL 建议/提示用户「直接用 CLI 绕过 SKILL 限制跑其他应用」或提供 CLI 绕行选项供用户选择         | 违反边界约束——唯一合法出口是引导使用 `omics-task-skill`              |
| SKILL 在同名检查发现项目已有应用时直接拒绝（不提供重命名循环）                                   | 违反导入流程——同名时应引导重命名后重新检查，循环直到名称唯一再导入     |
| SKILL 在非孤儿场景下（如用户明确要求时）用 `--app` 复用项目已有应用运行                           | 违反能力边界——`--app` 复用仅允许在"已通过同名检查→`omics run`命令接口报错→冲突∉快照(孤儿)"这一唯一场景 |
| SKILL 在运行参数含 outdir 时未主动提醒用户查看结果目录                                           | 违反用户体验守则——含 outdir 时必须在任务完成后主动提醒用户查看输出目录               |
| SKILL 接受用户给的另一个 PublicAppId 并替换硬编码值                                         | AppId 是本 SKILL 身份的一部分，不可被参数化                          |

---

## 3. 关键时序

### 3.1 run 前置确认 时序

```
用户："跑 IgGM(WDL)" / "做 XX 分析"
        │
        ▼
SKILL 拼: run --public-app b65d7070-6e8a-4a57-914d-dbbb9dd9b286
        │
        ▼
输出参数摘要表 + 完整命令 → 询问 y/N
        │
        ▼
收到肯定答复 → cli.execute(...)
```

### 3.2 run 前置确认时序

同 cdgpt-collection-skill CONTRACT.md §3.2。

**确认模板**：参考 `SKILL.md` §4.2。

**关键约束**：
1. SKILL 输出的命令必须**等同于** `cli.execute` 真正调用的命令
2. 摘要表必须列出：应用名 + AppId / 项目 / 环境 / 导入命名
3. 用户模糊回复时**不视作肯定**，必须再问一次

---

## 4. CLI 端的契约义务

| CLI 义务                                                                                  | 实现位置                          |
| ----------------------------------------------------------------------------------------- | --------------------------------- |
| `omics run --public-app <X>` 正确导入并运行公共应用                          | `cmd/ / `cmd/run.go`                         |
| `--public-app-name` 缺失 + 独立应用 → 主动报错/兜底                            | `cmd/run.go`                      |
| `--nf-version` 缺失 + NEXTFLOW 公共应用 → `MISSING_NF_VERSION` 含候选列表                 | `cmd/run.go`                      |
| 参数合并失败 → `PARAM_MERGE_FAILED` 结构化报错                                           | `cmd/run.go`                      |
| `omics debug` 三段式只取证不做症状匹配                                                    | `cmd/debug.go`                    |
| 鉴权失败统一退出码 2，业务错误退出码 1                                                    | `internal/cliexit/`               |
| 生成的 SKILL 默认使用公共应用自带的 InputTemplate，未传 `--input` 时自动取第一个模板作为 baseline              | 模板 + 文档说明                   |
| 生成的 SKILL 在运行参数含 outdir 时，任务完成后必须主动提醒用户查看该目录                        | 模板 + 文档说明                   |

---

## 5. CR 检查项

| 检查项                                                                                        | 通过标准                                                                                                                                                       |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| | SKILL 是否出现 `--wdl` / `--app` 这类越界 flag                                                | 应仅出现在"严令禁止"和"❌"反例段落                                      |
| `omics run --public-app` 入参是否为固定的 `' + c["APP_ID"] + '`                                      | 全文搜索验证                                          |\n
| SKILL 同名检查是否为"重命名循环"而非"直接拒绝"                                               | SKILL.md 的同名检查步骤中应包含：①先记录快照 ②有同名→引导重命名 ③循环直到唯一 ④通过后才继续导入 |
| SKILL 是否正确区分"场景 D（非本应用→拒绝）"与"同名检查（本应用+同名→重命名）"                 | SKILL.md 中应明确：用户要求运行非本公共应用→引导 omics-task-skill；导入本公共应用但项目有同名→引导重命名后继续 |
| SKILL 的孤儿复用是否限定在唯一合法场景                                                           | SKILL.md 中 `--app` 复用必须且只能出现在：已通过同名检查 → `omics run` **命令接口报错** → ConflictApplicationId ∉ 预存快照 |
| SKILL 是否引入 HTTP 客户端                                                                    | `grep -nE "import (requests|http|httpx|urllib)" skills/iggm-wdl-skill/` 应为空                                                                       |
| SKILL 是否使用 subprocess 调非 omics 命令                                                      | grep 仅在 `cli.execute` 内部调 omics 二进制                                                                                                                   |
| run 前置确认是否在 SKILL.md / wrapper 中明文要求                                              | SKILL.md "能力边界"章节 + 确认模板存在                                                                                                                          |
| 生成的 SKILL 是否默认使用公共应用自带的 InputTemplate                                           | SKILL.md 的运行参数章节应说明：未传 `--input` 时 CLI 自动取第一个模板；用户 `--input` 自定义覆盖对应字段                                                                                                                      |
| 生成的 SKILL 是否在含 outdir 时主动提醒用户查看结果目录                                           | SKILL.md 应有明确的 outdir 提醒守则：触发条件（outdir 字段存在）、提醒时机（同步/异步）、提醒模板、禁止省略                                                                                                                      |

---

## 6. 例外条款

如确实出现下面这些情况，请走"先讨论后改契约"流程：
- **应用版本更新**（平台变更）：自动通过，无需改 SKILL
- **AppId 变更**：本 SKILL 整个失效，必须重新发布版本
- **临时调试**：通过 wrapper 的 `--cli-path` 指向自定义 CLI 二进制

---

> 文档拥有者：组学平台 CLI / SKILL 联合维护
> 关联：[SKILL.md](SKILL.md) / [references/cli_commands.md](references/cli_commands.md)
