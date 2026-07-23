# CLI / SKILL 边界契约（scBERT 单应用收窄版）

> 本文档定义 omics-platform-cli 与 scbert-skill 之间不可违反的能力边界。
> CR 与日常巡检按本文档执行。

---

## 1. 唯一合法出口：6 命令白名单 + 单应用锁定

scbert-skill 通过 wrapper（`scripts/omics_cli.py`）调用 CLI；wrapper 在 argparse 层物理上注册 7 条一级命令，
但本 SKILL **只允许**调用以下子集：

| #   | 命令                              | 子动作                                | 写/读        | SKILL 是否可主动调                                                            |
| --- | --------------------------------- | ------------------------------------- | ------------ | ----------------------------------------------------------------------------- |
| 1   | `omics login`                     | —                                     | 写 token     | ❌ 引导用户在本机执行（OAuth 浏览器回调）                                      |
| 2   | `omics whoami`                    | —                                     | 读           | ✅                                                                             |
| 3   | `omics config`                    | `show` / `clear`                      | 读 / 删本地  | ✅ show / clear；❌ set 由用户本机执行                                         |
| 4   | `omics list apps`                 | —                                     | 读           | ✅ **仅限"导入前同名检查"用途**                                                |
| 5   | `omics run`                       | —                                     | 写远端任务   | ✅ **必须先二次确认；AppId 必须等于 `0de1b4ae-1543-4882-8bae-b5ee87968bc5`** |
| 6   | `omics status`                    | —                                     | 读           | ✅                                                                             |
| 7   | `omics debug`                     | `<rgId>` / `--run` / `--run + --job`  | 读           | ✅                                                                             |

> ❌ **本 SKILL 禁用**：`omics list public-apps`（不需要让用户挑应用）。

---

## 2. 严令禁止的反例

| 反例                                                                            | 违反原则                                                       |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| SKILL 调 `omics run --wdl <path>`（form A）                                     | 越界——本 SKILL 只能跑 scBERT 这一个公共应用                     |
| SKILL 调 `omics run --app <ApplicationId>`（form C）                            | 越界——同上；引导用户去 `omics-task-skill`                       |
| SKILL 调 `omics run --public-app <非锁定 AppId>`                                | 越界——AppId 已硬编码为 `0de1b4ae-1543-4882-8bae-b5ee87968bc5`   |
| SKILL 调 `omics list public-apps` 列其它应用                                    | 本 SKILL 只服务一个应用，不应让用户挑                           |
| SKILL 用 `list apps` 的结果让用户"复用某个 app-xxx 直接跑"                      | 越界——应引导用户去 `omics-task-skill`                            |
| SKILL 直调 `requests.post("https://omics.../...", ...)`                         | 直调后端 API → 绕开命令审计                                     |
| SKILL 自己 `subprocess.run(["curl", ...])` 拼 HTTP 调用                         | 同上                                                           |
| SKILL 用 `omics run` 但不向用户列摘要+完整命令、不询问 y/N，直接发起             | 跳过二次确认                                                   |
| SKILL 看到同名应用直接加 `-1` / `-cli` / 时间戳后缀绕过冲突                     | 命名属用户治理空间，不可代决策                                  |
| SKILL 看到 OOMKilled 直接改 nextflow config 的 memory + 自动重跑                | 替用户做症状判断 + auto-chain                                   |
| SKILL 接受用户给的"另一个 AppId"并替换硬编码值                                  | AppId 是本 SKILL 身份的一部分，不可被参数化                     |

---

## 3. run 前置确认时序

```
SKILL 拼 run 命令 (build_run, public_app="0de1b4ae-1543-4882-8bae-b5ee87968bc5")
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
继续/OK/是/      ─→ [修改]：解析意图 → 重拼 → 重走确认（AppId 不可改）
执行             ─→ [模糊]：再次明确询问 y/N
   │
   ▼
cli.execute(...)
   │
   ▼
解析 RunGroupId / 处理 PARAM_MERGE_FAILED / 鉴权失败转 Step 1/2 引导
```

**确认模板**：参考 `SKILL.md` §4.2。

**关键约束**：

1. SKILL 输出的命令字符串必须**完整等同于** `cli.execute` 真正调用的命令，不可"展示一个命令实际跑另一个"
2. 摘要表必须列出：应用名 / **锁定的 AppId** / 项目 / 环境 / NF 版本 / 导入命名 / 输入文件路径
3. 用户只回"嗯/好/可以/试试"等模糊回复时，**不视作肯定**，必须再问一次
4. AppId 不出现在用户可修改的字段中

---

## 4. CLI 端的契约义务

CLI 端为支撑 SKILL 边界设计提供以下保障：

| CLI 义务                                                                              | 实现位置                          |
| ------------------------------------------------------------------------------------- | --------------------------------- |
| `--public-app-name` 缺失 + 合集子应用 → 主动报错而非建空名应用                        | `cmd/run.go` 形态 B 兜底逻辑      |
| `--nf-version` 缺失 + NEXTFLOW 公共应用 → `MISSING_NF_VERSION` 含候选列表             | `cmd/run.go`                      |
| 参数合并失败 → `PARAM_MERGE_FAILED` 结构化报错（含 Specs/Report/PartialSkeleton/Hint） | `cmd/run.go`                      |
| `omics debug` 三段式只取证不做症状匹配                                                | `cmd/debug.go`                    |
| `omics status` 固定走 config 项目，不支持 `-p`                                        | `cmd/status.go`                   |
| 鉴权失败统一退出码 2，业务错误退出码 1                                                | `internal/cliexit/`               |

---

## 5. CR 检查项

| 检查项                                                                       | 通过标准                                                                                                                |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| SKILL 在 build_run 时是否硬编码 AppId                                        | 全文搜 `0de1b4ae-1543-4882-8bae-b5ee87968bc5`；不应允许该值被用户参数覆盖                                                |
| SKILL 是否引入 HTTP 客户端                                                   | `grep -nE "import (requests\|http\|httpx\|urllib)" skills/scbert-skill/` 应为空                                          |
| SKILL 是否使用 `subprocess` 调非 omics 命令                                  | `grep -n "subprocess" scripts/omics_cli.py` 仅在 `cli.execute` 内部调 omics 二进制                                       |
| SKILL 是否出现 `--wdl` / `--app` 这类越界 flag                               | `grep -nE "(\\\\-\\\\-wdl\\b\|\\\\-\\\\-app\\b)" skills/scbert-skill/SKILL.md` 仅出现在"严令禁止"和"❌"反例段落           |
| SKILL 是否出现其它 `--public-app` AppId                                      | 全文 `--public-app` 后的 AppId 应只出现 `0de1b4ae-1543-4882-8bae-b5ee87968bc5`                                           |
| run 前置确认是否在 SKILL.md / wrapper 中明文要求                              | SKILL.md "能力边界"章节 + §4.2 模板存在                                                                                   |

---

## 6. 例外条款

如确实出现下面这些情况，请走"先讨论后改契约"流程，不要在不通告的情况下绕开：

- **新增 scBERT 版本**（例如平台升级到 NF v25.x）：先在 SKILL.md 同步 `--nf-version` 默认值，
  并在 CONTRACT 修订历史里记录；**不允许 SKILL 默默切到新版本**
- **AppId 变更**（例如平台重新分配 ID）：本 SKILL 整个失效，必须重新发布版本，CONTRACT 同步更新
- **临时调试**：通过 wrapper 的 `--cli-path` 指向自定义 CLI 二进制，不要在 SKILL 内绕过 wrapper 直跑 binary

---

## 7. 修订历史

| 版本 | 日期       | 变更                                                                                  |
| ---- | ---------- | ------------------------------------------------------------------------------------- |
| v1.0 | 2026-06-03 | 从 omics-task-skill v4 派生；锁定 AppId=`0de1b4ae-...`；仅允许 form B + status + debug |

---

> 文档拥有者：组学平台 CLI / SKILL 联合维护
> 关联：[SKILL.md](SKILL.md) / [references/cli_commands.md](references/cli_commands.md)
