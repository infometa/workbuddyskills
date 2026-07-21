---
description: Git diff 增量安全审计。支持 fast（极速扫描）、light（快速扫描）和 deep（深度扫描）三种模式。
argument-hint: "[--commit <hash|base..head>] [--scan-level fast|light|deep] [--mode staged|unstaged|all] [--auto] [--background|--bg] [--output-root <dir>]"
allowed-tools: Bash, Read, Glob, Write, Grep, Task, Edit, MultiEdit, LSP, WebSearch, AskUserQuestion
---

# Git Diff 增量安全审计

> **语言约束（强制）**
>
> 所有面向用户的输出使用**简体中文**，具体覆盖：
> - 对话文本、任务摘要、CLI 日志打印
> - 写入 findings JSON 中会被 HTML 报告渲染的**字段值**：`title`、`description`、`attackScenario`、`recommendation`
> - `riskType`：必须使用 `risk-type-taxonomy.yaml` 中的标准中文 `name`（如 "SQL 注入"、"命令注入"、"SSRF"），**不得**自创复合描述（如 ~~"密钥管理 / 硬编码敏感信息"~~）、**不得**添加括号补充说明（如 ~~"服务端请求伪造 (SSRF)"~~）。taxonomy 中未收录的类型，使用简短中文名（≤8字），不含斜杠/括号/分隔符。
>
> **保持英文/原样**：JSON **字段名**、`id`、`filePath`、`cwe` 代号、`codeSnippet` 中的源代码原文。
>
> 禁止使用 emoji。
>
> **自动校验与修复**：`generate_report.py` 默认带 `--enforce-language zh` 校验，若 findings 文本字段中文占比不足阈值（默认 30%），脚本以**退出码 2** 终止并写出 `language-violations.json`。此时 MANDATORY-1 需按"语言校验失败回流"流程自动改写违规 findings 为中文后重跑（见 MANDATORY-1）。

硬约束：
- 必须在 git 仓库中运行
- 文件列表来自 git diff，无需文件枚举
- 关联文件总数上限 = changedCodeFiles x 3

---

## 自动模式（--auto）

当指定 `--auto` 参数时，进入无人值守模式，跳过所有用户交互：

| 交互点 | 正常模式 | --auto 模式 |
|--------|---------|------------|
| 权限白名单确认（init-步骤1） | AskUserQuestion | 自动执行配置/更新 |
| 模式选择（init-步骤2） | AskUserQuestion | 使用 `--scan-level` 参数（默认 light） |
| 环境就绪确认（init-步骤5） | **直接降级继续扫描**（不再弹出询问） | 行为同正常模式：自动降级继续 |
| 高风险未验证确认 | Deep 正常模式可 AskUserQuestion；**Light/Fast 跳过，直接继续** | 跳过，直接继续 |
| 修复交互 | Deep 正常模式可 AskUserQuestion；**Light/Fast 跳过修复，直接进入报告生成** | **跳过修复**，直接进入报告生成 |
| 下一步操作 | Deep 正常模式可 AskUserQuestion；**Light/Fast 跳过，自动结束** | 跳过，自动结束 |

Light/Fast 模式尾段固定流水线：报告生成 → 门禁评估 → 门禁通知 → 输出摘要 → 自动结束；不得弹出“生成 HTML 详细报告 / 结束审计”等下一步选择。

`--auto` 模式下的完整流水线：
1. 初始化（跳过交互）→ 2. 探索 → 3. 扫描 → 4. 验证 → 5. 报告生成 → 6. 上报 → 7. 门禁评估 → 8. 门禁通知 → 自动结束

**安全红线**：`--auto`、Light、Fast 模式**绝不**执行自动修复（不修改用户代码）。

---

## 后台模式（--background）

当指定 `--background`（简写 `--bg`）参数时，把整条增量扫描流程交给后台 Agent 执行，**主对话立即释放**。完成后由后台 Agent 通过消息回流摘要。

> **运行机制**：`Task(subagent_type: bg-scan, run_in_background: true)` 会让框架自动创建临时 team（主对话为 team lead，bg-scan 为 teammate），跑完自动销毁。bg-scan 是**独立上下文的全新 Agent，不继承主对话历史**，所需信息全部由主对话在 prompt 中显式注入。扫描过程的几十个 turn 全在 bg-scan 自己的上下文中进行，**不污染主对话**。完整机制见 `agents/bg-scan.md > 运行机制`。

**适用范围（本期仅 Fast）**：

- `--background` **仅支持 `--scan-level fast`**。命中 `--background` 但 scanMode 为 light/deep 时：提示「后台模式当前仅支持 Fast，light/deep 请走前台执行」，询问用户改用 fast 还是转前台。
- `--background` 隐含 `--auto` 语义（无人值守、绝不自动修复）。

**主对话职责（前置 + 调度，不执行扫描）**：

1. **前置交互**（必须在主对话完成，后台 Agent 无法交互）：权限白名单确认（`--auto` 时自动配置）、模式确认为 fast。
2. **解析变更文件列表**：按下方「阶段1 > 获取 git diff 文件列表」的规则解析 `--commit` / `--mode`，得到 `changedFiles`（含分类）。**这一步必须在主对话完成**——因为 bg-scan 独立上下文不知道命令行参数,变更范围必须由主对话算好传入。空文件列表则直接走「空文件列表快速退出」,不启动后台 Agent。
3. **生成工作目录**（diff 命名规范）：

   ```bash
   audit_batch_id="diff-fast-$(date +%Y%m%d%H%M%S)"
   scan_output_root="${outputRoot:-.codebuddy/security-scan/runs}"
   batch_dir="${scan_output_root}/${audit_batch_id}"
   mkdir -p "$batch_dir/agents"
   python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))" > "$batch_dir/.audit_start_time"
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" begin-session \
     --batch-dir "$batch_dir" --run-id "$audit_batch_id" --mode fast \
     --scan-command diff --project-path "$(pwd)"
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" init --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)"
   ```

4. **启动后台 Agent 并立即返回**：

   ```
   Task(
     subagent_type: bg-scan,
     run_in_background: true,
     max_turns: 50,
     mode: bypassPermissions,
     prompt:
       在独立上下文执行 Fast 模式增量安全扫描全流程，完成后用 SendMessage 回流摘要给 main。
       [CODEBUDDY_PLUGIN_ROOT] <已解析的绝对路径>
       [batch_dir] <batch_dir>
       [audit_batch_id] <audit_batch_id>
       [scanMode] fast
       [scope] diff
       [scanCommand] diff
       [changedCodeFiles] <逗号分隔的变更代码文件列表>
       [permissionReady] true
   )
   ```

5. **打印提示并结束本轮**（不空等、不轮询）：

   > 已在后台启动 Fast 增量安全扫描（批次 `{audit_batch_id}`，task_id `{task_id}`）。扫描完成后会自动回流摘要。

**完成回流**：后台 Agent 跑完后 `SendMessage(recipient: "main")` 回流。主对话下次活跃时自动收到。

---

## 编排器核心原则

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/contracts/orchestrator-contract.md`（仅在执行到编排调度时 Read，不提前加载）

---

## Fast 模式硬性约束（仅当 `scanMode == "fast"` 时生效）

Fast 模式 = Light 的执行纪律化版本。检查逻辑完全复用 Light（LLM 做扫描和验证），但**必须遵守 8 项硬性约束**。

> **完整约束 + 执行细节** Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-fast.md > Fast 模式硬性约束（必读）`（仅在 `scanMode == "fast"` 时 Read，不提前加载）

**速记**（详细说明见上述 Ref）：

- **A. 并行化**：阶段 1 Grep/Glob、阶段 2 多变更文件 Read 必须同 message 并行（≤4 并发），禁止串行。
- **B. 禁等待**：禁 `sleep N && ls`；本期禁启任何后台 Agent（**不启动 light-scan Agent**），统一走主窗口内联执行。
- **C. 扫描+验证合并**：阶段 2 产 finding 时同时校验代码存在性，打 `verificationStatus`，阶段 3 跳过。
- **D. 字段 schema**：`riskType` / `filePath` / `lineNumber` / `severity` / `riskConfidence`（≤90） / `verificationStatus`；`riskType` 用 taxonomy 标准中文 name，禁复合描述。
- **E. 裁剪**：阶段 1 跳 LLM 重复翻页扫描，阶段 3 跳 verifier Agent（保留 `merge-verify` bypass + Fast+ 校验）。
- **F. 前置脚本预筛**：阶段 1 LLM Grep 之前必须先跑 `pattern_grep.py` 五条命令；阶段 2 通过 `index_db.py query --preset sinks-top-per-file --limit 3` 与 `changedCodeFiles` 求交集消费预筛产物。
- **G. Source 可达性三判**：阶段 2 产 finding 之前对每个 Sink 完成 isReachableFromSource / isUndefended / isAttackerReachable 三判，任一不通过即 dismiss。文件级批量 prompt 见 Ref。

---

## 初始化

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`（仅在执行初始化时 Read，不提前加载）

按共享初始化流程依次执行 init-步骤0~5。

**参数解析约定**：
- `--scan-level fast|light|deep`：解析后记录为编排器变量 `scanMode`，未指定时通过 init-步骤2 交互选择
- `--background` / `--bg`：后台模式标志。命中时**不进入**下方常规编排流程，改走「后台模式（--background）」章节定义的前置 + 调度路径（仅支持 fast）。隐含 `--auto` 语义
- `--output-root <dir>`：自定义扫描产物的批次根目录，解析后记录为编排器变量 `outputRoot`。未指定时为默认值 `.codebuddy/security-scan/runs`。编排器仍在该根目录下自动拼接 `/{audit_batch_id}` 子目录，保留批次隔离。支持相对路径（相对当前工作目录）或绝对路径
- `--commit <arg>`：解析后记录为编排器变量 `COMMIT_ARG`（未指定时为空字符串），供后续 `fix_detector.py` 复用 git diff 范围
- `--mode <arg>`：解析后记录为编排器变量 `MODE_ARG`（未指定时为空字符串），供后续 `fix_detector.py` 复用 diff 模式

> **init-步骤0 必须最先执行**，且必须使用以下命令解析插件根目录，**禁止**用 `find`、`ls` 等方式手动搜索：

```bash
python3 -c "
import json, sys; from pathlib import Path
try:
  home = Path.home()
  s = json.loads((home/'.codebuddy'/'settings.json').read_text())
  km = json.loads((home/'.codebuddy'/'plugins'/'known_marketplaces.json').read_text())
  mid = [k.split('@',1)[1] for k,v in s.get('enabledPlugins',{}).items() if v and k.startswith('security-scan@')]
  if not mid: raise KeyError('not in enabledPlugins')
  loc = km[mid[0]]['installLocation']
  src = next((p['source'] for p in km[mid[0]].get('manifest',{}).get('plugins',[]) if p.get('name')=='security-scan'), './plugins/security-scan')
  root = str((Path(loc)/src).resolve())
  assert (Path(root)/'.codebuddy-plugin'/'plugin.json').exists()
  print(root)
except Exception as e:
  print('FALLBACK:' + str(e), file=sys.stderr); sys.exit(1)
"
```

将输出记录为 `CODEBUDDY_PLUGIN_ROOT`。后续所有 Bash 调用插件脚本前必须 `export CODEBUDDY_PLUGIN_ROOT="<路径>"`。
若 exit 1，Read `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md > 方法二` 执行 Glob 兜底。

diff 模式差异：模式选择交互中的时间预估为 Light 约 1-3 分钟，Deep 约 5-15 分钟。

输出初始化摘要：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段0: 初始化摘要`

---

## 阶段1: 探索

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段1: 探索`

### 探索阶段：初始化 + 获取变更

```bash
audit_batch_id="diff-${scanMode}-$(date +%Y%m%d%H%M%S)"
scan_output_root="${outputRoot:-.codebuddy/security-scan/runs}"
batch_dir="${scan_output_root}/${audit_batch_id}"
export SECURITY_SCAN_BATCH_DIR="$batch_dir"
mkdir -p "$batch_dir/agents"
# 写入审计开始时间（跨平台：用 Python 输出 ISO 8601，避免依赖 GNU date -Iseconds，兼容 macOS / Linux / Windows）
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))" > "$batch_dir/.audit_start_time"

# 开启扫描会话锁（防止上次扫描的陈旧 finding 污染本次结果）
# 详见 project.md 同段说明
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" begin-session \
  --batch-dir "$batch_dir" \
  --run-id "$audit_batch_id" \
  --mode "$scanMode" \
  --scan-command diff \
  --project-path "$(pwd)"
```

初始化 SQLite 索引数据库：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" init --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)"
```

产品形态分析（所有扫描模式必须执行，禁止脚本判定）：

- 不得调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type` 判定产品形态。
- 由当前 Agent 使用 Glob/Grep/Read 等上下文工具，基于仓库文件结构、入口点、依赖/Manifest、核心代码语义直接分析；获取 diff 文件列表后可用变更范围补充证据，但不得替代仓库主形态判断。
- 结论只能是 `客户端` / `AI agent` / `web` / `数据库` / `未知` 之一；机器码只能是 `client` / `ai_agent` / `web` / `database` / `unknown`。
- 必须给出实际举证：至少 1 条真实文件证据，包含 `path`、`line` 或 `lines`、`snippet`、`reason`。只有依赖名、目录名或猜测不足以定类。
- 若证据冲突或不足，结论必须为 `未知`，并说明缺失了哪些关键证据。

判定口径：

| product_shape | project_type_code | 必要证据口径 |
|---|---|---|
| `客户端` | `client` | 移动端/桌面端/小程序/浏览器插件等面向终端用户运行的客户端入口或 Manifest，例如 `AndroidManifest.xml`、`Info.plist`、Electron/Tauri 主进程、小程序 `app.json`/`*.wxml`，并能指向启动入口或端侧能力代码。 |
| `AI agent` | `ai_agent` | 同时存在 LLM/模型调用能力与工具执行/注册/任务编排/记忆/RAG/MCP 等 Agent 行为证据；仅调用 LLM 或仅聊天 UI 不足以定类。 |
| `web` | `web` | 存在 HTTP/Web 入口、路由、Controller、前端页面或全栈框架入口，并能证明该仓库提供 Web/API 服务或浏览器访问界面。 |
| `数据库` | `database` | 仓库本身实现数据库/存储引擎/查询执行/SQL 解析/数据库代理/迁移管控等数据库产品能力；普通业务代码“使用数据库”不算数据库形态。 |
| `未知` | `unknown` | 无法用真实文件证据支撑上述任一形态，或多个形态证据强度相近且无法判断主形态。 |

将分析结论写入 `$batch_dir/project-type.json`，格式如下（字段值替换为实际分析结果）：

```json
{
  "project_type": "web",
  "project_type_code": "web",
  "product_category": "web",
  "product_subtype": "",
  "product_shape": "web",
  "product_shape_decision": "基于真实文件证据判断为 web；未调用产品形态识别脚本。",
  "product_shape_evidence_chain": {
    "conclusion": "web",
    "standard": "Agent 直接分析仓库结构、入口、依赖/Manifest 与核心代码语义；结论限定为客户端/AI agent/web/数据库/未知；必须有真实文件证据。",
    "basis": ["识别到 HTTP 路由入口", "识别到 Web 框架启动文件"],
    "evidence": [
      {"path": "src/app.ts", "line": 12, "snippet": "app.get('/api/health', handler)", "reason": "HTTP 路由入口证明该仓库提供 Web/API 服务"}
    ],
    "competingCandidates": []
  }
}
```

查询长期记忆和项目结构缓存：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset memory-hints --project-path "$(pwd)"

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset cached-structure --project-path "$(pwd)"
```

记录 `structureCache`。diff 模式下结构缓存尤为有价值：有缓存时可直接定位变更文件涉及的入口点和已知 Sink，加速影响范围分析。

获取 git diff 文件列表：

```bash
git diff <base> <head> --name-only --diff-filter=ACMR    # commit range (base..head)
git diff <hash>^ <hash> --name-only --diff-filter=ACMR   # single commit
git diff HEAD --name-only --diff-filter=ACMR              # --mode all (default)
git diff --cached --name-only --diff-filter=ACMR           # --mode staged
git diff --name-only --diff-filter=ACMR                    # --mode unstaged
```

**`--commit` 参数解析规则**：
- `--commit abc1234..def5678` → commit 范围，使用 `git diff abc1234 def5678`
- `--commit abc1234~1..def5678` → 带 `~N` 的范围语法，同上
- `--commit abc1234` → 单个 commit，使用 `git diff abc1234^ abc1234`

**参数自动修正**（防御性校验）：
- `--mode staged` 但 `git diff --cached --name-only` 为空 → 自动修正为 `--commit HEAD`，并向用户说明原因（暂存区已清空，可能是 commit 后触发的被动扫描）
- `--mode all` 但 `git diff HEAD --name-only` 为空 → 自动修正为 `--commit HEAD`，并向用户说明原因

**空文件列表快速退出**：

> **`--auto` 模式**：空文件列表时生成"无变更"空报告并正常结束流程。创建 `batch-plan.json`（`total_files: 0`）、生成空的 `summary.json` 和 `gate-result.json`（`gateStatus: "pass"`），然后自动结束。不弹出任何提示。

正常模式下：

```
**未检测到任何代码变更**，无需执行安全扫描。
请确认：
  - 当前分支是否有未提交的修改（`git status` 查看）
  - 或指定具体 commit：`/security-scan:diff --commit <hash>`
```

**变更文件分类**：
- **代码文件**：`.java`、`.py`、`.go`、`.js`、`.ts` 等
- **依赖文件**：`pom.xml`、`package.json`、`go.mod` 等
- **配置文件**：`application.yml`、`.env` 等
- **运维文件**：`Dockerfile`、`docker-compose.yml` 等

输出任务摘要：

```
  **[1.1]** 变更获取完成
    变更文件：**{changedFiles}** 个（代码 **{codeFiles}**，配置 **{configFiles}**，依赖 **{depFiles}**，运维 **{opsFiles}**）
```

### 探索阶段：判断是否需要执行完整 diff 流水线

```
hasCodeChanges = true?
  -> true  -> 完整 diff 流水线
  -> false -> 纯配置/依赖变更快速通道（1.3c）
```

### 1.3a 基础探索（hasCodeChanges = true）

**【Fast 模式必须 - 约束 G】前置脚本化预筛**：仅 `scanMode == "fast"` 时执行。在 `audit_batch_id` 建立且 `index_db.py init` 完成后、**任何 LLM Grep 之前**，按顺序跑以下五条命令（同一 Bash 会话）。diff 模式下脚本**仍跑整仓**——以便捕获变更文件调用到的既有文件 Sink / 防御 / 入口 / 攻击面；阶段 2 再用 `changedCodeFiles` 求交集。Light / Deep 模式跳过此步骤，沿用既有探索流程。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-sinks \
  --batch-dir "$batch_dir" \
  --patterns-file "${CODEBUDDY_PLUGIN_ROOT}/resource/scan-data/sink-patterns.yaml" \
  --project-path .

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-defenses \
  --batch-dir "$batch_dir" \
  --project-path .

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-secrets \
  --batch-dir "$batch_dir" \
  --project-path .

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-entries \
  --batch-dir "$batch_dir" \
  --project-path .

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-attack-surface \
  --batch-dir "$batch_dir" \
  --project-path .
```

**检测本次 diff 修复的 Sink**（供 `merge_findings.py` 过滤已修复 finding，避免修复型变更误报为风险）：

> 必须放在脚本预筛之后执行：`fix_detector.py` 的 `defense_added` 分支依赖 `project-index.db` 中的 `sinks` / `defenses` 表。提前执行只能识别删除 Sink，无法识别新增防御修复。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/fix_detector.py" detect \
  --batch-dir "$batch_dir" \
  --project-path . \
  ${COMMIT_ARG:+--commit "$COMMIT_ARG"} \
  ${MODE_ARG:+--mode "$MODE_ARG"}
```

- 产出 `$batch_dir/diff-fixes.json`，列出被本次 diff 移除的 Sink 与新增防御覆盖的 Sink 位置
- `merge_findings.py merge-scan` 阶段会读取此文件，按 `(filePath, lineNumber)` ±3 行容差剔除对应 finding
- `merge_findings.py` 还会额外执行 diff remediation gate：若 finding 自身已声明“此变更已修复/无需额外处理”，则从最终风险列表移除并写入 `$batch_dir/remediated-findings.json`
- `COMMIT_ARG` / `MODE_ARG` 均为空时 `fix_detector` 默认走 `--mode all`（`git diff HEAD`）
- 失败不阻塞流程，仅日志告警；无 diff-fixes.json 时 `merge_findings` 仍保留 remediation gate 兜底

编排器内 LLM 并行补充（单 message，符合约束 A）：
1. **技术栈识别**：Glob + Grep 确认框架
2. **变更文件 Sink 检测**：
   - Fast 模式：不再逐关键字 Grep，改为 `index_db.py query --preset sinks-top-per-file --limit 3` 拉取脚本预筛结果（每文件 Top-3 裁剪），与变更文件列表求交集
   - Light / Deep 模式：沿用既有逻辑，对变更代码文件 Grep Sink 模式
3. **凭证/密钥检测**：
   - Fast 模式：已由脚本写入 `indexer_findings` 表，LLM 仅补充框架特定密钥
   - Light / Deep 模式：沿用既有逻辑，对变更文件 Grep 密钥模式
4. **配置基线检查**：对变更配置文件检查不安全默认值

输出任务摘要：

```
  **[1.3a]** 基础探索完成
    技术栈：**{framework}**
    变更文件 Sink：**{sinkCount}** 个候选 Sink（脚本预筛 ∩ 变更文件）
    凭证检测：**{secretCount}** 个疑似硬编码密钥（脚本预筛）
    配置基线：**{configIssueCount}** 个不安全配置项
```

### 1.3b Deep 模式深度探索（hasCodeChanges = true）

> **仅 Deep 模式执行**。Light 模式跳过，直接进入阶段2。

先执行 1.3a 的基础探索，然后启动 indexer Agent，`[scope] = diff`：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-deep.md > 阶段 1: 探索`

indexer 在 diff 模式下额外执行**影响范围扩展**：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/diff-mode.md > 变更影响范围分析策略`

输出任务摘要：

```
  **[1.3b]** 深度探索完成（indexer Agent）
    语义索引已构建：`project-index.db`
    关联文件：**{relatedFiles}** 个（L1 **{a}**，L2 **{b}**，L3 **{c}**）
    端点：**{endpointCount}** 个 API 端点
    调用图：**{callGraphEdges}** 条调用关系
    防御映射：**{defenseCount}** 个防御点
```

### 1.3c 纯配置/依赖快速通道（hasCodeChanges = false）

```
  **[1.3c]** 探索完成：变更文件 **{n}** 个（均为配置/依赖文件，无代码变更）
  启用**配置快速通道**：仅执行密钥检测 + CVE 扫描 + 配置基线检查
```

编排器内联执行密钥检测 + CVE 扫描 + 配置基线，跳转到阶段4报告生成。

### 探索阶段：条件规则加载

**条件规则加载**：按技术栈和项目类型加载框架安全知识（含 Ghost Bits 条件维度）。
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/orchestration.md > 条件规则加载`

### 探索阶段：探索阶段摘要

输出探索阶段完成摘要（diff 模式）：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段1: 探索 > 阶段完成摘要 > diff 模式`

### 探索阶段：生成扫描计划

生成 `batch-plan.json` 以保障审计元数据完整性（供后续 generate_report.py 使用）。

> **diffRange 一致性**：下方内联脚本 import `fix_detector.derive_diff_range`（diff 范围推导的**唯一真相源**）读取编排器 export 的 `COMMIT_ARG` / `MODE_ARG` 推导 `base`/`head`，写入 `batch-plan.json > diffRange`；import 失败时回退到等价内联逻辑（保证 batch-plan 不中断）。`merge_findings.py` 在 diff-fixes 过滤前会比对该字段与 `diff-fixes.json` 的范围，不一致则跳过过滤（避免过滤对错位置）。因此生成 batch-plan 前**必须**先 `export COMMIT_ARG MODE_ARG`（未指定的传空串）。

```bash
export COMMIT_ARG MODE_ARG
SCAN_MODE="$scanMode" python3 << 'PYTHON_INLINE_SCRIPT'
import json
import os
import sys

batch_dir = os.environ["SECURITY_SCAN_BATCH_DIR"]
project_type_info = {}
project_type_file = os.path.join(batch_dir, "project-type.json")
if os.path.exists(project_type_file):
    try:
        project_type_info = json.loads(open(project_type_file, encoding="utf-8").read())
    except Exception:
        project_type_info = {}

# 推导 diffRange：优先复用 fix_detector.derive_diff_range（唯一真相源），
# import 失败（如 PLUGIN_ROOT 异常）时回退到等价内联逻辑，保证 batch-plan 不中断
commit_arg = (os.environ.get("COMMIT_ARG", "") or "").strip()
mode_arg = (os.environ.get("MODE_ARG", "") or "").strip()
try:
    _plugin_root = os.environ["CODEBUDDY_PLUGIN_ROOT"]
    sys.path.insert(0, os.path.join(_plugin_root, "scripts"))
    from fix_detector import derive_diff_range
    diff_range = derive_diff_range(commit_arg, mode_arg)
except Exception:
    # 回退：与 fix_detector.derive_diff_range 等价（commit_arg/mode_arg 已 strip）
    if commit_arg and ".." in commit_arg:
        _base, _head = commit_arg.split("..", 1)
    elif commit_arg:
        _base, _head = commit_arg + "^", commit_arg
    elif mode_arg == "staged":
        _base, _head = "", "--cached"
    elif mode_arg == "unstaged":
        _base, _head = "", ""
    else:
        _base, _head = "", "HEAD"  # all / 默认
    diff_range = {"base": _base, "head": _head, "mode": mode_arg, "commit": commit_arg}

batch_plan = {
    "total_files": {changedFiles},
    "changed_files": {changedFiles},
    "code_files": {codeFiles},
    "config_files": {configFiles},
    "dep_files": {depFiles},
    "scan_mode": os.environ.get("SCAN_MODE", "unknown"),
    "framework": "{framework}",
    "project_type": project_type_info.get("project_type", "未知"),
    "project_type_code": project_type_info.get("project_type_code", "unknown"),
    "product_category": project_type_info.get("product_category", project_type_info.get("product_shape", "未知")),
    "product_subtype": project_type_info.get("product_subtype", ""),
    "product_shape": project_type_info.get("product_shape", project_type_info.get("project_type", "未知")),
    "product_shape_decision": project_type_info.get("product_shape_decision", ""),
    "product_shape_evidence_chain": project_type_info.get("product_shape_evidence_chain", {}),
    "product_shape_info": project_type_info,
    "scan_timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).astimezone().isoformat(timespec="seconds"),
    "diffRange": diff_range,
    "options": {}
}

batch_plan_file = os.path.join(batch_dir, "batch-plan.json")
with open(batch_plan_file, 'w') as f:
    json.dump(batch_plan, f, ensure_ascii=False, indent=2)

print(f"已生成 {batch_plan_file}")
PYTHON_INLINE_SCRIPT
```

---

## 阶段2: 扫描

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段2: 扫描`
>
> 扫描策略按 scanMode 选一份 Read（不要全部加载）：
> - Fast: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-fast.md > 阶段 2: 扫描 + 内联验证（纪律化）`
> - Light: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-light.md > 阶段 2: 扫描（编排器内联扫描）`
> - Deep: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-deep.md > 阶段 2: 扫描（三 Agent 并行）`

按 scanMode 执行对应的扫描策略。diff 模式的 Deep Agent 提示词需附加变更上下文：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/diff-mode.md > Agent 提示词注入模板`

- **Fast 模式**：**不启动任何 Agent**，编排器主窗口内联执行，严格遵守 **"Fast 模式硬性约束"** 章节（并行 Read + 扫描内联校验 + 字段 schema 规范 + **Source 可达性三判（文件内批量）**）。
  - 扫描前先 `index_db.py query --preset sinks-top-per-file --limit 3` 拉取每文件 Top-3 Sink 清单，与 `changedCodeFiles` 求交集；再 `--preset defenses-for-file --filter-file <path>` 为每个命中文件拉防御映射。**按 Sink 清单驱动 + 文件内批量三判**（详见 `scan-mode-fast.md > 阶段 2: 扫描 + 内联验证（纪律化）`）：LLM 同一 message 内 Read 文件 + 对该文件所有 Sink 输出 verdict 数组。
  - 回滚说明：`SECURITY_SCAN_FAST_V2=0` **仅关闭 `merge_findings.py` 的 pre-check 兜底**；Top-K 裁剪和批量三判由 `scan-mode-fast.md` 定义，LLM 执行时不读环境变量。完整回退需 `git revert` 本次 A+B 改动。
  - 置信度上限 90。产出 `agents/light-inline.json`（`sourceAgent: "light-inline"`）。
- **Light 模式**：启动 light-scan Agent（编排器动态生成 Task）。具体流程见 `scan-mode-light.md`。
- **Deep 模式**：三 Agent 并行（vuln-scan + logic-scan + red-team）。

> **Deep 模式关键**：并行启动 vuln-scan + logic-scan + red-team 三个 Agent Task 后，主窗口**不空转等待**——先执行前置工作（导出 indexer findings、加载知识文件），再检查各 Agent 产物是否落盘。详见 `scan-mode-deep.md > 2.2 等待期间前置工作 + 流式处理`。

**漏洞链检测**（diff 模式尤为重要）：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/diff-mode.md > 漏洞链检测重点`

---

## 阶段3: 验证

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段3: 验证`

按 scanMode 执行对应的验证策略。

> **完整流程** Read: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/verification.md`（仅在执行验证阶段时 Read，不提前加载）
>
> - **Fast 模式**：**完全跳过独立阶段 3**。阶段 2 已内联完成代码存在性校验（`verificationStatus: inline-verified`）。直接执行下方 Fast 合并步骤。
> - **Light 模式**：轻量验证，仅代码存在性校验（置信度上限 90）
> - **Deep 模式**：确定性脚本验证（Stage 1-3）→ verifier Agent 深度验证（Stage 4）→ 评分 + 质量评估（Stage 5）→ merge-verify 合并

### Fast 模式合并步骤（MANDATORY）

Fast 模式阶段 2 编排器内联扫描完成后，**必须**调用 merge 脚本将内联产物导入标准管线。不可跳过。

**步骤 3.1：合并 light-inline 产物**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
  --batch-dir "$batch_dir" \
  --extra-agents light-inline
```

验证：`.codebuddy/security-scan/runs/{batch}/merged-scan.json` 已创建。

**步骤 3.2：执行 merge-verify（Fast bypass 模式）**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-verify \
  --batch-dir "$batch_dir"
```

Fast 模式下 merge-verify 会自动检测 `batch-plan.json > scan_mode == "fast"` 并跳过 verifier 产物加载，复用 Light 的 bypass 路径，直接使用 stage2 结果生成 `finding-*.json` 和 `summary.json`。

### Light 模式验证步骤（MANDATORY）

light-scan Agent 完成后，**必须**调用 merge 脚本将 agent 产物导入标准管线。不可跳过此步骤，否则下游报告、上报、门禁、通知全部失效。

**步骤 3.1：合并 light-scan 产物**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
  --batch-dir "$batch_dir" \
  --extra-agents light-scan
```

验证：`.codebuddy/security-scan/runs/{batch}/merged-scan.json` 已创建且 `totalFindings > 0`。

**步骤 3.2：执行 merge-verify（Light bypass 模式）**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-verify \
  --batch-dir "$batch_dir"
```

Light 模式下 merge-verify 会自动检测 `batch-plan.json > scan_mode == "light"` 并跳过 verifier 产物加载，直接使用 stage2 结果生成 `finding-*.json` 和 `summary.json`。

---

## 阶段4: 修复

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段4: 修复`

### 修复阶段：修复方案生成

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 内联修复执行`

### 修复阶段：报告生成 + 记忆同步 + 门禁评估 + 门禁通知 + 摘要

> 按 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md` 依次执行：报告生成 → 长期记忆同步 → 门禁评估 → 门禁通知 → 审计摘要。
> 以下步骤为**必须执行（MANDATORY）**，不可跳过。即使上游步骤失败或输出为空，下游步骤仍需尝试执行（best effort）。
> **Light/Fast 模式**：执行完 MANDATORY 步骤后直接输出报告路径和审计摘要并结束，禁止再发起“生成 HTML 详细报告 / 结束审计”等用户确认。
> **注意**：审计报告上报由 Stop Hook 自动完成（`report_upload_hook.py`），无需在编排中手动执行。

**记录审计结束时间**（在报告生成前写入，供上报统计耗时）：

```bash
# 跨平台：用 Python 输出 ISO 8601，避免依赖 GNU date -Iseconds，兼容 macOS / Linux / Windows
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))" > "$batch_dir/.audit_end_time"
```

**MANDATORY-1：报告生成**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/generate_report.py" \
  --input "$batch_dir" \
  --audit-batch-id "$audit_batch_id" \
  --format html \
  --output "$batch_dir"/security-scan-report.html
```

> **语言校验失败回流（退出码 == 2）**
>
> 上述命令默认启用 `--enforce-language zh`。若退出码为 2，表示 findings 文本字段中文占比未达阈值（默认 30%），此时**必须**按以下步骤自动修复，**禁止**改用 `--enforce-language none` 绕过：
>
> 1. Read `.codebuddy/security-scan/runs/<batch>/language-violations.json`，获取违规 finding 的 `id`、`filePath`、`lineNumber`、`fields`。
> 2. 定位含这些 finding 的 `.codebuddy/security-scan/runs/<batch>/agents/<agent-name>.json`，对每条违规 finding 改写 `title` / `description` / `riskType` / `attackScenario` / `recommendation` 为简体中文，**保持** `id`、`filePath`、`lineNumber`、`severity`、`riskConfidence`、`codeSnippet`、`cwe` 原样。
> 3. 重跑合并与报告生成（`merge_findings.py merge-scan` → `merge-verify` → `generate_report.py`）。
> 4. 最多重试 2 次。若仍失败，保留 `language-violations.json` 并在最终摘要中提示用户，但不阻塞 MANDATORY-2/3。

**MANDATORY-2：门禁评估**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/gate_evaluator.py" evaluate \
  --batch-dir "$batch_dir" \
  --project-root "$(pwd)"
```

评估失败不阻塞流程。验证 `gate-result.json` 已创建。

**MANDATORY-3：门禁通知**

`--auto` 模式下 `notifySource="hook-auto"`，否则 `notifySource="scan"`。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/gate_reminder.py" notify \
  --batch-dir "$batch_dir" \
  --source "$notifySource" \
  --project-root "$(pwd)"
```

通知失败不阻塞流程。未配置通知渠道时自动跳过。

**Light/Fast/`--auto` 模式**：MANDATORY-1/2/3 执行完成后，输出 HTML 报告路径和审计摘要，**跳过修复交互和下一步操作选择**，自动结束。

**Deep 正常模式**：可继续执行 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 用户交互：下一步操作`。用户选择修复时，按 `post-audit.md > 内联修复执行` 执行；用户选择预览时，使用 `open` 命令打开 HTML 报告。

---

## 错误处理

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode.md > 错误处理`（仅在遇到错误时 Read，不提前加载）

diff 模式额外降级策略：indexer 失败时，基于基础探索结果的变更文件列表仍可用，编排器内联执行轻量扫描作为降级。
