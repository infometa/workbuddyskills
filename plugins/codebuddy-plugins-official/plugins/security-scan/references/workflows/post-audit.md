# 审计后工作流

> 引用方：commands/project.md（阶段4）、commands/diff.md（阶段4）

---

## Fast 早退路径（v3.2 / 方案 F'）

> 仅 Fast 模式相关。Light / Deep 不受影响。

Fast 模式在阶段 1 / 阶段 2 的空场景下会标注 `early_exit_reason`，进入**早退路径**。重要约束：

**早退 ≠ 跳步**。以下 MANDATORY 步骤**仍必须全部执行**，只是输入/输出为空：

1. **MANDATORY-1 报告生成**：`generate_report.py` 对空 findings 有早退兜底（v3.2），自动注入最小占位 result，不再报"未找到审计结果"。HTML 报告顶部会展示蓝色 `early-exit-banner`，中文原因标签 + `skip_detail` 详细说明。
2. **MANDATORY-2 门禁评估**：0 风险自动 pass（`gateStatus: "pass"`）
3. **MANDATORY-3 门禁通知**：pass 状态下自动跳过通知发送
4. **上报**：Stop Hook 的 `report_upload_hook.py` 仍正常上报，让平台知道扫描完成

### 四种早退原因（early_exit_reason）

| reason | 场景 | 触发位置 | 中文标签 |
|--------|------|---------|---------|
| `no_sinks` | 阶段 1 整仓脚本预筛后无任何 Sink | commands/project.md 阶段 1 早退门 | "阶段 1 未检测到任何 Sink（可攻击点）" |
| `no_sinks_in_diff` | diff 场景下变更文件 ∩ Sink = 0 | commands/diff.md 1.3a.1 早退门 | "变更范围内无可攻击的 Sink（diff-scope）" |
| `no_findings` | 阶段 2 LLM 扫描后 light-inline.json findings=[] | `merge_findings.py` Fast bypass 自动标注 | "阶段 2 扫描后无可报告的风险" |
| `no_scannable_files` | 变更文件均为文档/配置（无代码） | commands 层 `hasCodeChanges=false` 快速通道 | "变更文件无可扫描的代码 / 配置 / 依赖" |

### Metadata 透传链路

```
batch-plan.json.early_exit_reason
    ↓（merge-verify Fast bypass 路径）
merged-verified.json.metadata.early_exit_reason
    ↓（summary 生成时同步）
summary.json.early_exit_reason
    ↓（generate_report 读取）
report.html 顶部 early-exit-banner
```

merge_findings.py 规则：
- batch-plan 已含 `early_exit_reason` → 透传（阶段 1 就标注的优先）
- 否则 Fast 模式且 `final_count == 0` → 自动标注 `no_findings`

### 回滚开关

- `SECURITY_SCAN_EARLY_EXIT=0`：编排器层不执行早退门检查，强制走全流程（调试用）
- `git revert`：恢复 v3.2 前的行为

---

## 报告生成

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/generate_report.py" --input "$batch_dir" --audit-batch-id "$audit_batch_id" --format html --output "$batch_dir"/security-scan-report.html
```

> `generate_report.py` 也支持直接输出 JSON（默认 stdout），以及仅传 `--audit-batch-id` 自动定位审计目录；编排器场景建议继续固定输出到 `security-scan-report.html`。

---

## 长期记忆同步

> memory-sync 会同步：项目指纹、扫描历史、Sink、防御、**项目结构快照**（文件列表+技术栈+入口点）。
> 下次扫描可通过 `--preset cached-structure` 查询复用。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" memory-sync --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)" --scan-mode "$scanMode"

# findings-file 选择：
#   - Light 模式：读 merged-scan.json（历史既有行为）
#   - Fast 模式：读 merged-verified.json（merge-verify bypass 产物，与 Deep 一致）
#   - Deep 模式：读 merged-verified.json
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" update-findings --batch-dir "$batch_dir" --batch-id "$audit_batch_id" --project-path "$(pwd)" --findings-file "$batch_dir"/$([ "$scanMode" = "light" ] && echo "merged-scan.json" || echo "merged-verified.json")
```

---

## 报告上报（Stop Hook 自动执行）

报告上报由 Stop Hook (`report_upload_hook.py`) 在 Agent 停止时自动执行，**编排中无需手动调用**。
Hook 仅通过 `CODEBUDDY_SERVICE_PROXY_URL` 服务代理通道上报，由网关注入认证信息；若未注入该环境变量，上报直接失败（不再回退）。

验证文件：`report-payload.json`（上报数据）、`report-sent.json`（状态标记）。

如需手动调试上报，可执行：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/report_upload.py" --input "$batch_dir" --audit-batch-id "$audit_batch_id"
```

---

## 门禁评估

报告生成完成后执行门禁评估。评估结果不阻塞流程。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/gate_evaluator.py" evaluate --batch-dir "$batch_dir" --project-root "$(pwd)"
```

验证文件：`gate-result.json`（门禁评估结果）。评估失败不阻塞流程。

### 门禁通知

门禁评估完成后，如果配置了通知渠道（用户级 `~/.codebuddy/security-scan/config.json` 或项目级 `.codebuddy/security-scan/config.json`），静默发送通知。通知失败不阻塞流程。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/gate_reminder.py" notify --batch-dir "$batch_dir" --source "$notifySource" --project-root "$(pwd)"
```

`--source` 取值规则：
- `scan` — 用户手动执行 `/security-scan:diff` 或 `/security-scan:project`
- `hook-auto` — git hook 被动触发的自动扫描（`--auto` 模式）
- `push` — git push 前触发

编排器在初始化时根据是否有 `--auto` 参数决定 `notifySource`：有 `--auto` 时 `notifySource="hook-auto"`，否则 `notifySource="scan"`。

> 通知渠道通过 `/security-scan:setup` 命令配置。未配置时跳过。

---

## 审计摘要模板

```
**代码安全审查完成！**

发现 **{total_issues}** 个问题：**{critical_count}** 严重 / **{high_count}** 高危 / **{medium_count}** 中危 / **{low_count}** 低危
{scope_line}

**严重/高危漏洞：**
1. **[{severity}]**[{riskType}] {filePath}:{lineNumber} -- 置信度 **{confidence}**
...

**审计结果文件：**
   finding-sql-injection.json -- 漏洞安全审计 -- SQL 注入（2 个风险）
  ...

**HTML 报告已生成**：`.codebuddy/security-scan/runs/{batch}/security-scan-report.html`（耗时 **{elapsed_time}**）

**安全门禁：{gate_status}**
{gate_violations_summary}
```

规则：
- 严重/高危列表最多 10 条，超出显示 `... 及其他 {n} 个严重/高危漏洞`
- 无严重/高危时省略该部分
- 耗时格式：`{M} 分 {S} 秒`（不足 1 分钟仅显示秒数）
- 批次 ID、agent 数量仅记录在 `summary.json` 中

审查范围行：
- **project（deep）**: `审查范围：**{total_files}** 个文件`
- **project（light）**: `审查范围：**{total_files}** 个文件（**快速扫描**）`
- **project（fast）**: `审查范围：**{total_files}** 个文件（**极速扫描**）`
- **diff**: `变更文件：**{changed_files}** 个`

门禁状态行（读取 `gate-result.json`）：
- `gateStatus` 为 `pass` 时：`**安全门禁：通过**`
- `gateStatus` 为 `warn` 时：`**安全门禁：告警** — {violations 列表逗号分隔}`
- `gateStatus` 为 `soft-block` 时：`**安全门禁：未通过** — {violations 列表逗号分隔}`
- `gate-result.json` 不存在时省略门禁状态行

---

## 高风险未验证发现确认（可选）

当存在 `verificationStatus: "unverified"` 且 `severity: "critical"/"high"` 的 finding 时触发：

> **Light/Fast/`--auto` 模式**：跳过此交互，直接继续后续流程。未验证的高危漏洞信息会记录在报告中供后续人工复核。

Deep 正常模式下弹出交互：

```
AskUserQuestion:
  question: "本次审计发现 **{n}** 个高危/严重漏洞未能完整验证（置信度 < **90**）。建议人工复核："
  options:
    - label: "查看详情"
      description: "显示未验证的高危漏洞详细信息和无法验证的原因"
    - label: "已知悉，继续"
      description: "跳过，进入下一步操作选择"
```

---

## 用户交互：下一步操作

> **Light/Fast/`--auto` 模式**：跳过此交互，**绝不执行自动修复**，输出 HTML 报告路径和审计摘要后自动结束。不得弹出“生成 HTML 详细报告 / 结束审计”等下一步选择。

**存在高置信度（>= 90）漏洞时**（仅 Deep 正常模式）：

```
AskUserQuestion:
  question: "审计完成，请选择下一步操作："
  options:
    - label: "自动修复高置信度漏洞"
      description: "自动修复置信度 >= 90 的漏洞"
    - label: "预览报告"
    - label: "修复 + 预览报告"
    - label: "结束审计"
```

**不存在高置信度漏洞时**（仅 Deep 正常模式）：

提示：`本次审计未发现置信度 >= **90** 的漏洞，无需自动修复。低置信度漏洞建议人工审查。`

> **禁止**在提示中添加「因 Grep+Read 降级模式置信度上限为 89」等错误说明。Grep+Read 的实际置信度上限为 **90**（见 `techniques/confidence-scoring.md > traceMethod 分级上限`）。无高置信度漏洞可能是因为门控条件未全部满足，而非 traceMethod 上限导致。

```
AskUserQuestion:
  question: "请选择下一步操作："
  options:
    - label: "预览报告"
    - label: "结束审计"
```

---

## 内联修复执行

不启动独立 Agent。修复逻辑在编排器上下文内直接执行。

### 修复资格

`ahAction=pass` 且 `confidence>=90` 且 `challengeVerdict` 为 confirmed/escalated。

### 方案生成

1. 提取符合资格的 findings：
   - **Deep 模式**：从 `score-results.json` 提取（含确定性置信度评分），回退到 `agents/verifier-*.json` 或 `agents/verifier.json`
   - **Light 模式**：从 `merged-scan.json` 中 `findings` 数组提取（`confidence >= 90` 的条目视为符合资格，Light 模式无 `challengeVerdict`，跳过该条件检查）
2. 按 `filePath` 分组
3. 对每组：
   - Read Sink 上下文（目标行号 +-20 行）+ Source 文件
   - Grep 项目已有安全组件（sanitizer/validator/encoder）
   - 选择修复层级：Sink 层 > 中间层 > Source 层 > 架构层
   - 生成 `originalCode` 和 `fixedCode`
4. 写入 `agents/remediation.json`（含 `fileGroups` 分组信息）

### 修复执行

#### 修复-步骤1：展示修复候选项与代码对比

按文件分组展示每个待修复漏洞的前后代码对比：

```
**待修复漏洞（{count} 个）：**

─── {filePath} ───

{idx}. **[{severity}]**[{riskType}] 第 **{lineNumber}** 行 -- 置信度 **{confidence}**

修复前：
```{lang}
{originalCode}
```

修复后：
```{lang}
{fixedCode}
```

修复策略：{strategy}

...（同文件其他漏洞）

─── {filePath2} ───
...
```

展示规则：
- 按 `agents/remediation.json` 中 `fileGroups` 分组，同文件漏洞连续展示
- `originalCode` / `fixedCode` 取自 `remediation.json`，带语言标记的代码块
- 漏洞数超过 10 个时仅展示 Top-10（按 severity + confidence 排序），并提示 `... 及其他 {n} 个漏洞`

展示后通过 AskUserQuestion 获取修复方式：

```
AskUserQuestion:
  question: "以上为待修复漏洞的代码对比，请选择修复方式："
  options:
    - label: "全部修复"
      description: "自动修复以上所有漏洞"
    - label: "选择修复"
      description: "逐个确认是否修复"
    - label: "取消"
      description: "放弃修复"
```

"选择修复"模式下，逐个漏洞询问"修复 / 跳过"。

#### 修复-步骤2：执行修复

按 `agents/remediation.json` 中 `fileGroups` 分组执行：
- 同文件多修复点：优先 MultiEdit（行号从大到小），失败降级逐个 Edit
- 单文件单修复点：直接 Edit
- 每个文件修复后立即验证

### MultiEdit 策略

| 同文件修复点数 | 首选工具 | 降级工具 |
|-------------|---------|---------|
| 1 个 | Edit | -- |
| >=2 个 | MultiEdit | 逐个 Edit |

MultiEdit 规范：
1. 行号从大到小排序（避免偏移）
2. 同文件 `additionalImports` 去重合并，作为首个编辑项
3. 重叠区域合并为单个修复块
4. MultiEdit 不可用时自动降级为逐个 Edit

### 修复原则

- 复用优先 -- 使用项目已有安全组件
- 风格一致 -- 匹配项目代码风格
- 最小变更 -- 仅修改必要代码行
- 业务无损 -- 不破坏业务逻辑
- 编译即通 -- 包含所有必要 import
- 可逆安全 -- 复杂修复拆分为独立步骤

### 修复完成摘要

```
**修复完成！**

已修复：**{fixed_count}** 个漏洞
跳过（代码已变更无法自动修复）：**{failed_count}** 个

**修复的漏洞：**
1. **[{severity}]**[{riskType}] {filePath}:{lineNumber} -- {strategy}
...

建议在修复后运行项目测试，并使用 `git diff` 审查变更内容。
```

### 上下文控制

Read 调用使用 `offset` + `limit`，禁止全文件 Read。待修复 findings 超过 10 个时仅修复 Top-10（按 severity + confidence 排序）。

---

## 预览 HTML 报告

HTML 报告已在阶段4自动生成，使用 `open` 命令直接在浏览器中预览：

```bash
open "$batch_dir"/security-scan-report.html
```
