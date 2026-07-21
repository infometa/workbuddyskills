---
description: 全项目代码安全审计。支持 fast（极速扫描）、light（快速扫描）和 deep（深度扫描）三种模式，支持 --auto 无人值守自动化。
argument-hint: "[file_path...] [--scan-level fast|light|deep] [--focus high] [--auto] [--background|--bg] [--include *.py,*.js] [--exclude node_modules,dist] [--output-root <dir>]"
allowed-tools: Bash, Read, Glob, Write, Grep, Task, Edit, MultiEdit, LSP, WebSearch, AskUserQuestion
---

# 全项目安全审计

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

当指定 `--background`（简写 `--bg`）参数时，把整条扫描流程交给后台 Agent 执行，**主对话立即释放**，用户可继续其他工作。完成后由后台 Agent 通过消息回流摘要。

> **运行机制**：`Task(subagent_type: bg-scan, run_in_background: true)` 会让框架自动创建临时 team（主对话为 team lead，bg-scan 为 teammate），跑完自动销毁。bg-scan 是**独立上下文的全新 Agent，不继承主对话历史**，因此它需要的所有信息必须由主对话在 prompt 中显式注入（见下方第 3 步参数）。扫描过程的几十个 turn 全部在 bg-scan 自己的上下文中进行，**不污染主对话**；进入主对话的只有最后一条回流摘要。完整机制说明见 `agents/bg-scan.md > 运行机制`。

**适用范围（本期仅 Fast）**：

- `--background` **仅支持 `--scan-level fast`**。Fast 模式本就全内联、无子 Agent、无人值守，最适合整体后台化。
- 命中 `--background` 但 `scanMode == light` 或 `deep` 时：提示「后台模式当前仅支持 Fast，light/deep 请走前台执行」，并询问用户是改用 fast 还是转前台。
- `--background` 隐含 `--auto` 语义（无人值守、绝不自动修复）。

**主对话职责（前置 + 调度，不执行扫描）**：

1. **前置交互（必须在主对话完成，后台 Agent 无法交互）**：
   - init-步骤1 权限白名单确认（`AskUserQuestion`，`--auto` 时自动配置）
   - init-步骤2 模式选择：若未显式 `--scan-level fast`，交互确认为 fast（后台仅支持 fast）
2. **生成工作目录**（沿用「阶段1: 探索 > 初始化工作目录」的命名规范）：

   ```bash
   audit_batch_id="project-fast-$(date +%Y%m%d%H%M%S)"
   scan_output_root="${outputRoot:-.codebuddy/security-scan/runs}"
   batch_dir="${scan_output_root}/${audit_batch_id}"
   mkdir -p "$batch_dir/agents"
   python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))" > "$batch_dir/.audit_start_time"
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" begin-session \
     --batch-dir "$batch_dir" --run-id "$audit_batch_id" --mode fast \
     --scan-command project --project-path "$(pwd)"
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" init --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)"
   ```

   > 工作目录与 DB 初始化放在主对话，是为了让后台 Agent 接手时环境已就绪，且 `begin-session` 锁先建好避免并发污染。
3. **启动后台 Agent 并立即返回**：

   ```
   Task(
     subagent_type: bg-scan,
     run_in_background: true,
     max_turns: 50,
     mode: bypassPermissions,
     prompt:
       在独立上下文执行 Fast 模式安全扫描全流程，完成后用 SendMessage 回流摘要给 main。
       [CODEBUDDY_PLUGIN_ROOT] <已解析的绝对路径>
       [batch_dir] <batch_dir>
       [audit_batch_id] <audit_batch_id>
       [scanMode] fast
       [include] <include 参数，可空>
       [exclude] <exclude 参数，可空>
       [permissionReady] true
   )
   ```

   > `mode: bypassPermissions` 与 Deep 模式启动扫描 Agent 一致——后台 Agent 无法响应权限询问，必须预先授权，否则会卡死。

4. **打印提示并结束本轮**（不空等、不轮询）：

   > 已在后台启动 Fast 安全扫描（批次 `{audit_batch_id}`，task_id `{task_id}`）。扫描完成后会自动回流摘要，期间你可以继续其他工作。

**完成回流**：后台 Agent 跑完后通过 `SendMessage(recipient: "main")` 回流（成功含 Critical/High/Medium/Low 统计、门禁结果、报告路径；失败含原因与 batch_dir）。主对话下次活跃时自动收到，无需主动轮询；如需主动查看可用 `TaskOutput` 查 task_id。

**与现有 Hook 的关系**：审计报告上报仍由 Stop Hook（`report_upload_hook.py`）在会话结束时自动完成，后台 Agent 产物落在标准 batch_dir，Hook 照常发现并上报，无需改动。

---

## 编排器核心原则

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/contracts/orchestrator-contract.md`（仅在执行到编排调度时 Read，不提前加载）

---

## Fast 模式硬性约束（仅当 `scanMode == "fast"` 时生效）

Fast 模式 = Light 的执行纪律化版本。检查逻辑完全复用 Light（LLM 做扫描和验证），但**必须遵守 8 项硬性约束**。

> **完整约束 + 执行细节** Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-fast.md > Fast 模式硬性约束（必读）`（仅在 `scanMode == "fast"` 时 Read，不提前加载）

**速记**（详细说明见上述 Ref）：

- **A. 并行化**：阶段 1 Grep/Glob、阶段 2 多文件 Read 必须同 message 并行（≤4 并发），禁止串行。
- **B. 禁等待**：禁 `sleep N && ls`；本期禁启任何后台 Agent，project / diff 一律走主窗口内联执行。
- **C. 扫描+验证合并**：阶段 2 产 finding 时同时校验代码存在性，打 `verificationStatus`，阶段 3 跳过。
- **D. 字段 schema**：`riskType` / `filePath` / `lineNumber` / `severity` / `riskConfidence`（≤90） / `verificationStatus`；`riskType` 用 taxonomy 标准中文 name，禁复合描述。
- **E. 裁剪**：阶段 1 跳 LLM 重复翻页扫描，阶段 3 跳 verifier Agent（保留 `merge-verify` bypass + Fast+ 校验）。
- **F. 前置脚本预筛**：阶段 1 LLM Grep 之前必须先跑 `pattern_grep.py grep-sinks/grep-defenses/grep-secrets/grep-entries/grep-attack-surface` 五条命令；阶段 2 通过 `index_db.py query --preset sinks-top-per-file --limit 3` 消费预筛产物。
- **G. Source 可达性三判**：阶段 2 产 finding 之前对每个 Sink 完成 isReachableFromSource / isUndefended / isAttackerReachable 三判，任一不通过即 dismiss。文件级批量 prompt 见 Ref。

---


## 聚焦模式（--focus high）

> 当 `focusMode == "high"` 时生效。完整流程 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/focus-mode.md`（仅在 `focusMode == "high"` 时 Read，不提前加载）

聚焦模式仅关注可直接远程造成命令执行(RCE)和大量信息泄漏的高危风险，以及组合漏洞线索。

**适用约束**：
- 仅 `project` + `light` / `deep`。`fast` 已默认聚焦高危，自动忽略
- 阶段1探索不变（需全量索引发现组合线索）
- 阶段2扫描：Light 仅分析 S1+S2 Sink；Deep 子 Agent 注入聚焦指令
- 阶段3验证：Deep 下 verifier Agent 进入无上下文挑战模式（不读扫描推理，信号速查表匹配）
- 阶段3末尾：**必须**执行 `verifier.py focus-filter` 确定性过滤
- 阶段4报告：仅输出 critical+high finding

确定性过滤由 `verifier.py focus-filter` 纯函数执行，不依赖 LLM，5 条硬规则确保聚焦准确。

---


## 初始化

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`（仅在执行初始化时 Read，不提前加载）

按共享初始化流程依次执行 init-步骤0~5（**插件根目录解析**、权限、模式选择、tree-sitter、LSP、环境确认）。

**参数解析约定**：
- `--scan-level fast|light|deep`：解析后记录为编排器变量 `scanMode`，未指定时通过 init-步骤2 交互选择
- `--background` / `--bg`：后台模式标志。命中时**不进入**下方常规编排流程，改走「后台模式（--background）」章节定义的前置 + 调度路径（仅支持 fast）。隐含 `--auto` 语义
- `--output-root <dir>`：自定义扫描产物的批次根目录，解析后记录为编排器变量 `outputRoot`。未指定时为默认值 `.codebuddy/security-scan/runs`。编排器仍在该根目录下自动拼接 `/{audit_batch_id}` 子目录，保留批次隔离。支持相对路径（相对当前工作目录）或绝对路径
- `--focus high`：聚焦模式标志。**仅** `project` 流程 + `light` / `deep` 模式下生效。记录为编排器变量 `focusMode = "high"`。
  - 与 `--scan-level fast` 同时使用：提示「Fast 模式已默认聚焦高危漏洞，无需 --focus high」并忽略该参数，`focusMode` 保持空
  - `--focus high` 隐含自动跳过修复交互和下一步操作选择

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

project 模式无额外差异，完整按 initialization.md 执行。

输出初始化摘要：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段0: 初始化摘要`

---

## 阶段1: 探索

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段1: 探索`

### 探索阶段：初始化工作目录和检测历史扫描记忆

```bash
audit_batch_id="project-${scanMode}-$(date +%Y%m%d%H%M%S)"
scan_output_root="${outputRoot:-.codebuddy/security-scan/runs}"
batch_dir="${scan_output_root}/${audit_batch_id}"
export SECURITY_SCAN_BATCH_DIR="$batch_dir"
mkdir -p "$batch_dir/agents"
# 写入审计开始时间（跨平台：用 Python 输出 ISO 8601，避免依赖 GNU date -Iseconds，兼容 macOS / Linux / Windows）
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))" > "$batch_dir/.audit_start_time"

# 开启扫描会话锁（防止上次扫描的陈旧 finding 污染本次结果）
# - 写入 .scan-session.json 标识本次扫描的起始时间和 runId
# - 主动清理早于本次会话的固定文件名产物（agents/*.json / merged-scan.json /
#   merged-verified.json / finding-*.json / summary.json / gate-result.json 等）
# - 下游 merge / gate / upload 均会按 mtime 校验产物属于本次会话才允许加载
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" begin-session \
  --batch-dir "$batch_dir" \
  --run-id "$audit_batch_id" \
  --mode "$scanMode" \
  --scan-command project \
  --project-path "$(pwd)"
```

初始化 SQLite 索引数据库 + 长期记忆库：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" init --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)"
```

产品形态分析（所有扫描模式必须执行，禁止脚本判定）：

- 不得调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type` 判定产品形态。
- 由当前 Agent 使用 Glob/Grep/Read 等上下文工具，基于文件结构、入口点、依赖/Manifest、核心代码语义直接分析。
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

查询长期记忆（如有历史扫描）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset memory-hints --project-path "$(pwd)"
```

查询项目结构缓存（如有历史扫描的结构快照）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset cached-structure --project-path "$(pwd)"
```

记录 `structureCache`（`cached-structure` 返回的 JSON）。

**缓存复用规则**：
- `structureCache.cached == true` → indexer-1.2 改为增量模式：通过 `content_hash` 比对识别新增/变更/删除的文件，对变更文件重新执行 Sink + 入口点 Grep，技术栈通过标记文件 Glob 校验后决定复用或重检
- `structureCache.cached == false` → 正常执行 indexer-1.2 全量枚举

输出任务摘要：

```
  **[1.1]** 工作目录已初始化：`.codebuddy/security-scan/runs/{audit_batch_id}`
  {hasMemoryHints ? "历史扫描记忆已加载，共 **" + memoryCount + "** 条提示" : "无历史扫描记忆"}
  {structureCache.cached ? "项目结构缓存命中：**" + structureCache.fileCount + "** 个文件，**" + structureCache.entryPointCount + "** 个入口点（将增量更新）" : "无结构缓存，将执行全量枚举"}
```

### 探索阶段：基础探索

> 基础探索逻辑的权威定义：`agents/indexer.md > indexer-步骤1`。
> Light 模式由编排器内联执行 indexer-步骤1 逻辑，Deep 模式由 indexer Agent 完整执行（编排器仍先执行基础探索，indexer 在此基础上构建完整语义索引）。

在编排器内按 `agents/indexer.md > indexer-步骤1` 的流程快速完成基础枚举：

- `structureCache.cached == true` → 增量模式（详见 `agents/indexer.md > indexer-1.0a 缓存加速`）
- `structureCache.cached == false` → 全量枚举

基础探索包含：文件枚举 + 技术栈识别、入口点粗定位、Sink 粗定位、凭证/密钥检测、配置基线、CVE 扫描。

**【Fast 模式必须 - 约束 G】前置脚本化预筛**：仅 `scanMode == "fast"` 时执行。在 `audit_batch_id` 建立且 `index_db.py init` 完成后、**任何 LLM Grep 之前**，按顺序跑以下五条命令，把 Sink / 防御 / 凭证 / 入口 / 攻击面确定性写入 `project-index.db`。后续 LLM 从"按 Sink 清单扫描"替代"全文件翻页"。Light / Deep 模式跳过此步骤，沿用既有探索流程。

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

脚本已内置测试/构建产物过滤；结果进入 `sinks` / `defenses` / `indexer_findings` / `files.is_entry` / `attack_surface` 表。Fast 模式下 LLM Grep 仅用于补充脚本未覆盖的框架特定模式；Light / Deep 模式沿用既有探索流程，本章节预筛不影响其行为。

输出任务摘要：

```
  **[1.2]** 基础探索完成
    文件枚举：**{fileCount}** 个源文件，**{totalLines}** 行代码
    技术栈：**{framework}**
    入口点文件：**{entryPointFiles}** 个
    Sink 粗定位：**{sinkCount}** 个候选 Sink
    凭证检测：**{secretCount}** 个疑似硬编码密钥
    配置基线：**{configIssueCount}** 个不安全配置项
    依赖安全：**{cveCount}** 个已知 CVE
```

### 探索阶段：Deep 模式深度探索

> **仅 Deep 模式执行**。Light 模式跳过，直接进入阶段2。
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-deep.md > 阶段 1: 探索`

启动 indexer Agent 构建完整语义索引。

输出任务摘要：

```
  **[1.3]** 深度探索完成（indexer Agent）
    语义索引已构建：`project-index.db`
    端点：**{endpointCount}** 个 API 端点
    调用图：**{callGraphEdges}** 条调用关系
    防御映射：**{defenseCount}** 个防御点
```

### 探索阶段：生成扫描计划

生成 `batch-plan.json` 以保障扫描元数据完整性（供后续 merge_findings.py 和 generate_report.py 使用）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset summary > /tmp/summary_out.json 2>/dev/null

# 提取必要的扫描数据并生成 batch-plan.json
# 若 focusMode 为 "high"，注入环境变量供 batch-plan.json options.focus 使用
SCAN_MODE="$scanMode" SECURITY_SCAN_FOCUS_MODE="${focusMode:-}" python3 << 'PYTHON_INLINE_SCRIPT'
import json
import os

batch_dir = os.environ["SECURITY_SCAN_BATCH_DIR"]
summary_out = json.loads(open("/tmp/summary_out.json").read())
project_type_info = {}
project_type_file = os.path.join(batch_dir, "project-type.json")
if os.path.exists(project_type_file):
    try:
        project_type_info = json.loads(open(project_type_file, encoding="utf-8").read())
    except Exception:
        project_type_info = {}

# 计算源文件总数（从索引数据库或环保存的fileCount）
file_count = summary_out.get("fileCount", 0)
if file_count == 0:
    # Fallback: 从 git ls-files 快速统计
    import subprocess
    try:
        result = subprocess.run(
            "git ls-files --cached --others --exclude-standard | grep -E '\\.(java|kt|kts|py|go|js|ts|jsx|tsx|php|rb|cs|cpp|c|rs|swift|vue)$' | wc -l",
            shell=True, capture_output=True, text=True
        )
        file_count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except:
        file_count = 0

batch_plan = {
    "total_files": file_count,
    "scan_mode": os.environ.get("SCAN_MODE", "unknown"),
    "framework": summary_out.get("framework", "unknown"),
    "project_type": project_type_info.get("project_type", "未知"),
    "project_type_code": project_type_info.get("project_type_code", "unknown"),
    "product_category": project_type_info.get("product_category", project_type_info.get("product_shape", "未知")),
    "product_subtype": project_type_info.get("product_subtype", ""),
    "product_shape": project_type_info.get("product_shape", project_type_info.get("project_type", "未知")),
    "product_shape_decision": project_type_info.get("product_shape_decision", ""),
    "product_shape_evidence_chain": project_type_info.get("product_shape_evidence_chain", {}),
    "product_shape_info": project_type_info,
    "entry_points": summary_out.get("entryPointCount", 0),
    "scan_timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).astimezone().isoformat(timespec="seconds"),
    "options": {"focus": os.environ.get("SECURITY_SCAN_FOCUS_MODE", "")}
}

batch_plan_file = os.path.join(batch_dir, "batch-plan.json")
with open(batch_plan_file, 'w') as f:
    json.dump(batch_plan, f, ensure_ascii=False, indent=2)

print(f"已生成 {batch_plan_file}")
PYTHON_INLINE_SCRIPT
```

### 探索阶段：大仓分片计划

project 命令必须在 `batch-plan.json` 后执行大仓识别；该步骤只生成编排元数据，不改变最终报告格式。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/large_repo_sharder.py" plan \
  --batch-dir "$batch_dir" \
  --project-path "$(pwd)" \
  --scan-mode "$scanMode"
```

判定规则由脚本内置：源文件数、总行数、Sink 数、monorepo 标志任一超过阈值即写出 `shard-plan.json` 且 `largeRepo=true`。若 `largeRepo=false`，后续按原 project 流程继续。若 `largeRepo=true`，后续阶段进入"大仓分片分支"：分别扫描 `shards/<shard-id>/`，最后回到父级批次合并成一份报告。

分片产物约定：

```text
$batch_dir/shard-plan.json
$batch_dir/shards/shard-001/batch-plan.json
$batch_dir/shards/shard-001/shard-status.json
$batch_dir/shards/shard-001/agents/*.json
```

### 探索阶段：探索阶段摘要

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset summary
```

**条件规则加载**：按技术栈加载框架安全知识。
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/orchestration.md > 条件规则加载`

输出探索阶段完成摘要（project 模式）：
> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段1: 探索 > 阶段完成摘要 > project 模式`

---

## 阶段2: 扫描

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段2: 扫描`
>
> 扫描策略按 scanMode 选一份 Read（不要全部加载）：
> - Fast: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-fast.md > 阶段 2: 扫描 + 内联验证（纪律化）`
> - Light: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-light.md > 阶段 2: 扫描（编排器内联扫描）`
> - Deep: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-deep.md > 阶段 2: 扫描（三 Agent 并行）`

按 scanMode 执行对应的扫描策略：
- **Fast 模式**：编排器内联（与 Light 相同路径），但受 **"Fast 模式硬性约束"** 章节约束（并行 Read + 扫描内联校验 + 字段 schema 规范 + **Source 可达性三判（文件内批量）**）。
  - 扫描前先通过 `index_db.py query --preset sinks-top-per-file --limit 3` 拉取每文件 Top-3 Sink 清单（按 severity_level ASC，优先 S1/S2）；对每个涉及文件用 `--preset defenses-for-file --filter-file <path>` 拉防御映射。**按 Sink 清单驱动 + 文件内批量三判**（详见 `scan-mode-fast.md > 阶段 2: 扫描 + 内联验证（纪律化）`）：LLM 同一 message 内 Read 文件 + 对该文件所有 Sink 输出 verdict 数组。
  - 回滚说明：`SECURITY_SCAN_FAST_V2=0` **仅关闭 `merge_findings.py` 的 pre-check 兜底**；Top-K 裁剪和批量三判由 `scan-mode-fast.md` 定义，LLM 执行时不读环境变量。完整回退需 `git revert` 本次 A+B 改动。
  - 置信度上限 90。
- **Light 模式**：编排器内联扫描，置信度上限 90。具体流程见 `scan-mode-light.md`。
- **Deep 模式**：三 Agent 并行（vuln-scan + logic-scan + red-team）。

> **Deep 模式关键**：并行启动 vuln-scan + logic-scan + red-team 三个 Agent。启动后主窗口**不空转等待**——先执行前置工作（导出 indexer findings、加载知识文件），再检查各 Agent 产物是否落盘。详见 `scan-mode-deep.md > 2.2 等待期间前置工作 + 流式处理`。

### 大仓分片分支（仅 `shard-plan.json > largeRepo == true`）

若 `shard-plan.json` 中 `largeRepo=true`，阶段 2 不再一次性扫描全仓，改为遍历 `shards[]`。每个 shard 独立运行当前 `scanMode` 的扫描策略，但扫描范围必须限制为该 shard 的 `includeGlobs`，并附加 `sharedContext`。

执行纪律：

1. 每个 shard 使用独立 `shard_dir="$batch_dir/shards/<shard-id>"`，不得把子扫描 agent 产物写入父级 `agents/`。
2. 启动 shard 前标记 `running`；完成标记 `completed`；失败标记 `failed` 后继续下一个 shard，不得中断父流程。
3. shard 内扫描仍遵守 Fast/Light/Deep 原有规则；Deep shard 内仍是 `vuln-scan + logic-scan + red-team` 三 Agent。
4. 若用户重跑同一批次，跳过 `shard-status=completed` 的 shard，仅续扫 `pending/failed` shard。

状态更新命令：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/large_repo_sharder.py" status \
  --batch-dir "$batch_dir" \
  --shard-id "$shard_id" \
  --status running
```

shard 扫描上下文变量：

```bash
parent_batch_dir="$batch_dir"
shard_dir="$batch_dir/shards/$shard_id"
export SECURITY_SCAN_PARENT_BATCH_DIR="$parent_batch_dir"
export SECURITY_SCAN_BATCH_DIR="$shard_dir"
# include 参数来自 shard-plan.json 的 includeGlobs；扫描 Agent 只能读取这些路径及 sharedContext。
```

---

## 阶段3: 验证

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段3: 验证`

按 scanMode 执行对应的验证策略。

> **完整流程** Read: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/verification.md`（仅在执行验证阶段时 Read，不提前加载）
>
> - **Fast 模式**：**完全跳过独立阶段 3**。阶段 2 已内联完成代码存在性校验（`verificationStatus: inline-verified`），置信度上限 90。
> - **Light 模式**：轻量验证，仅代码存在性校验（置信度上限 90）
> - **Deep 模式**：确定性脚本验证（Stage 1-3）→ verifier Agent 深度验证（Stage 4）→ 评分 + 质量评估（Stage 5）→ merge-verify 合并

### 大仓分片验证与全局合并（MANDATORY when `largeRepo=true`）

若 `shard-plan.json > largeRepo == true`，阶段 3 在每个 completed shard 内先执行当前 `scanMode` 对应的原有验证/合并流程，然后回到父级批次执行跨分片关联和最终合并。

**步骤 3.S1：逐 shard 验证与合并**

对每个 `shard-status=completed` 的 shard：

- Fast shard：在 `shard_dir` 执行 `merge-scan --extra-agents light-inline` → `merge-verify`。
- Light shard：在 `shard_dir` 执行 `merge-scan --extra-agents light-scan` → `merge-verify`。
- Deep shard：在 `shard_dir` 按 `verification.md` 完整执行确定性验证、verifier Agent、评分、质量评估、`merge-verify`。

失败 shard 记录为 `failed` 并继续，最终报告展示 `failedShards`，不得因单 shard 失败导致父级无报告。

**步骤 3.S2：生成跨分片关联候选**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/large_repo_sharder.py" correlate \
  --batch-dir "$batch_dir" \
  --project-path "$(pwd)"
```

生成 `$batch_dir/cross-shard-correlation.json`。该文件只是候选，不等同 confirmed findings。

**步骤 3.S3：跨目录关联风险复核**

若 `cross-shard-correlation.json > candidateCount > 0`，启动 `cross-shard-scan` Agent，输入父级 `batch_dir`，输出必须写入：

```text
$batch_dir/agents/cross-shard-scan.json
```

该 Agent 只复核候选链路，不全仓重扫；输出 findings 必须使用规范 camelCase schema。

**步骤 3.S4：父级统一合并**

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-shards \
  --batch-dir "$batch_dir"
```

`merge-shards` 会收集 `shards/*/merged-verified.json`、父级 `agents/cross-shard-scan.json`，去重后写出父级 `merged-scan.json`、`merged-verified.json`、`finding-*.json` 和 `summary.json`。完成后直接进入阶段4的报告/门禁流程；不要再对父级批次执行普通 `merge-verify`。

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

Fast 模式下 merge-verify 会自动检测 `batch-plan.json > scan_mode == "fast"` 并跳过 verifier 产物加载，复用 Light 的 bypass 路径，直接使用 stage2 结果生成 `merged-verified.json` 和 `summary.json`。

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

Light 模式下 merge-verify 会自动检测 `batch-plan.json > scan_mode == "light"` 并跳过 verifier 产物加载，直接使用 stage2 结果生成 `merged-verified.json` 和 `summary.json`。

---

## 阶段4: 修复

> 进度与摘要格式 Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 进度与摘要输出 > 阶段4: 修复`

### 修复阶段：修复方案生成

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md > 内联修复执行`

### 修复阶段：报告生成 + 记忆同步 + 门禁评估 + 门禁通知 + 摘要

> 按 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/post-audit.md` 依次执行：报告生成 → 长期记忆同步 → 门禁评估 → 门禁通知 → 审计摘要。
> **注意**：审计报告上报由 Stop Hook 自动完成（`report_upload_hook.py`），无需在编排中手动执行。
> 以下步骤为**必须执行（MANDATORY）**，不可跳过。
> **Light/Fast 模式**：执行完 MANDATORY 步骤后直接输出报告路径和审计摘要并结束，禁止再发起“生成 HTML 详细报告 / 结束审计”等用户确认。

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
> 1. Read `.codebuddy/security-scan/runs/<batch>/language-violations.json`，获取违规 finding 的 `id`、`filePath`、`lineNumber`、`fields`（需要改写的字段名）。
> 2. 定位含这些 finding 的 `.codebuddy/security-scan/runs/<batch>/agents/<agent-name>.json`（可通过 grep finding id 快速定位），对每条违规 finding 改写 `title` / `description` / `riskType` / `attackScenario` / `recommendation` 为简体中文，**保持** `id`、`filePath`、`lineNumber`、`severity`、`riskConfidence`、`codeSnippet`、`cwe` 原样。
> 3. 重跑合并与报告生成：
>    ```bash
>    python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
>      --batch-dir "$batch_dir"
>    python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-verify \
>      --batch-dir "$batch_dir"
>    python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/generate_report.py" \
>      --input "$batch_dir" \
>      --audit-batch-id "$audit_batch_id" \
>      --format html \
>      --output "$batch_dir"/security-scan-report.html
>    ```
> 4. 最多重试 2 次。若仍失败，保留 `language-violations.json` 并在最终摘要中提示用户存在未完成翻译项，但不阻塞后续 MANDATORY-2/3。

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
