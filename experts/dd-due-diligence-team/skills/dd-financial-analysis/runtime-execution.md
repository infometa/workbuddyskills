# AIDD 财务 execution Runtime

本文适用于**本项目存在可用 Finance Run** 的 P0-P5 候选分析场景（路由判据见 SKILL.md「强制路由」）。
`attemptId` 与 `turnId` 由下方流程中的 `get_finance_agent_context` / `begin_finance_turn` 获取，
不需要在进入本文前就已具备。目标是在硬超时前形成可冻结、可校验、可同步的最小候选；不是生成一份独立财务报告。

> **v1.2.0 起本分支的候选生成不需要沙箱、不需要计算脚本**：不要运行 `bootstrap.py`，不要运行 `calculate.py`，
> 不要在 `/workspace` 下读写任何财务文件。全部输入经 MCP 获取，全部产出经 MCP 提交。
>
> **本文的约束只覆盖「候选生成与提交」**。turn 提交完成后，若用户还要求生成财务专项报告，
> 转入 `SKILL.md`「公共收尾：生成财务专项报告（MD + DOCX）」节，该节允许写沙箱、允许生成 DOCX。

## 绝对禁止

- 候选生成与提交过程中禁止调用 `render.py`、禁止写入工作空间 reports 或工作空间 work。
  （turn 提交完成后执行「公共收尾」节生成专项报告 DOCX 不受此限，但仍禁止调用 `render.py`。）
- **禁止自行计算任何财务数值**。比率、勾稽、期间变化、同业差异一律引用
  `get_finance_agent_context` 返回的 `calculation.result`。手算、估算、心算的数字一律视为伪造。
- 本 turn 内禁止联网、公开研究、行业检索、可比公司检索或重新下载年报。
  - 约束理由是**时间盒与可冻结性**，不是「系统不允许联网」。
  - 同业对标所需的行业基准由后端独立取数后注入 baseline，本 turn 只消费，不得自己检索或编造。
  - baseline 里没有 `benchmark` 时，P4 直接标 `limited` 并写明「行业基准未就绪」，不做数值对标。
- 禁止逐页阅读整份年报、穷举所有附注、追求非阻断性的账龄、借款、受限资金或分红细节。
- 禁止访问另一个 Run/Attempt。
- 禁止直接发布 P0-P5、benchmark、snapshot 或把候选称为数据库权威结果。

## 执行流程（MCP）

财务分析轮**只支持 MCP 流程**：

1. `get_finance_agent_context({ runId })` —— 取得 Run 绑定、材料清单、`baseVersions`、
   **`baseline.data`（内联的完整基线 JSON）** 与 **`calculation`（后端权威计算结果）**。
2. `begin_finance_turn({ runId, kind, query, idempotencyKey })` —— 开启本轮，
   返回 `turnId` 与 `turnSecret`。**`turnSecret` 只返回一次，必须留存至提交。**
3. 只有某个字段 proposal 确实需要原文证据时，才调用
   `get_finance_run_material({ runId, runMaterialId })` 取该材料的 `markdown` 正文；
   **不得遍历全部材料**（那是材料预处理轮的职责，且会挤占时间盒）。
4. 形成候选后调用一次
   `submit_finance_turn({ runId, turnId, turnSecret, submission })`。

不得在 MCP 提交失败后改用正文 JSON 假装成功。

## 权威边界：谁产出什么

| 内容 | 产出方 |
| --- | --- |
| `state/baseline.json` | **后端**（`baseline.data`，你只读） |
| `calculation/financial-input-*.json`、`calculation/financial-result-*.json` | **后端**（`calculation.result`，你只读） |
| `stages/p*.json` 中的 `calculationSummary` / `changes` / `comparisons` / `signals` | **后端回填**（你传什么都会被覆盖） |
| `state/proposed.json` | **你**（内联在 `candidate.proposed`） |
| 各阶段的语义 `data`、`sourceRefs`、`limitations` | **你**（内联在 `candidate.stages[Pn]`） |
| `stages/p*.md` 叙述 | **你**（内联在 `candidate.stages[Pn].markdown`） |

这条边界是硬约束：**你根本没有提交数值的通道**。因此不要为「让数字对上」花任何时间，
把预算全部投到事实抽取、来源定位和定性判断上。

### baseline 与 calculation 的使用

`baseline.data` 是唯一权威起点。核对其 `schemaVersion=finance-baseline/v1` 以及 Run/Attempt 绑定。优先使用：

- `workingState.p0`
- `workingState.financialInput`
- `workingState.calculationInput`（后端已从 UI 工作态转换成 `calculate.py` 所需的 snake_case 输入）
- `acceptedStages`
- `baseVersions`
- `researchMode` 和材料快照摘要

`calculation` 的形态：

```json
{
  "schemaVersion": "finance-calculation-result/v1",
  "status": "ready",
  "input": { "...": "与 baseline.workingState.calculationInput 相同" },
  "result": { "summary": {}, "statement_changes": {}, "industry_comparisons": {}, "rule_signals": {} },
  "error": null
}
```

`status = "failed"` 时（通常是 P1 年度数据不全），`result` 为 `null`：
此时仍要完成 P0/P1 候选，其余阶段一律标 `limited` 并在 `limitations` 写明
「后端计算未就绪：<error>」，不得用估算值顶替。

不得为了"更完整"重新抽取 baseline 已含的事实。`candidate.proposed` 只能从 baseline 派生，
保留已确认值；只允许用有冻结材料证据的字段 proposal 补 `null`、补来源或报告冲突。

## 有界产出顺序

按 30 分钟硬上限设计的内部时间盒：读取上下文与形成 `proposed` 不超过 3 分钟；
P0-P5 语义候选与叙述累计不超过 12 分钟；可选证据补充最多再用 5 分钟；
最迟第 20 分钟开始组装并提交 submission。达到任一时间盒立即跳过非阻断增强。

### 1. 形成最小 proposed

`candidate.proposed` 的固定形态：

```json
{
  "schemaVersion": "finance-proposed/v1",
  "runId": "<runId>",
  "attemptId": "<attemptId>",
  "baseVersions": {},
  "p0": {},
  "financialInput": {},
  "changeSummary": []
}
```

`baseVersions`、`p0`、`financialInput` 分别**原样复制** `baseline.data` 的对应字段。
没有充分证据时不产生任何变更 —— 这是优先快速路径。

只有存在冻结材料支持的字段 proposal 时，才修改 `p0` / `financialInput` 的对应字段，
并在 `changeSummary` 中记录。后端会用改后的 `proposed` 重建计算输入并复算，
因此**不要**自己推演变更后的数值影响，在叙述里定性说明即可。

### 2. 写 P0-P5 语义候选

`candidate.stages[Pn]` 的固定形态：

```json
{
  "status": "done",
  "data": {},
  "sourceRefs": [],
  "limitations": [],
  "markdown": "# P0 ...\n\n结论……"
}
```

`status` 只允许 `done` 或 `limited`。证据不足但可判断时用 `limited`，不等待额外资料。

各阶段 `data` 的最小字段：

| 阶段 | `data` 最小字段 | 来源 |
| --- | --- | --- |
| P0 | `companyName`, `accountingPeriods`, `statementScope`, `currency`, `sourceUnit`, `reviewItems` | baseline `workingState.p0` |
| P1 | `periods`, `statements`, `sourceRefs`, `reviewItems` | baseline `workingState.calculationInput` |
| P2 | `groups`, `metricGaps` | 你的分组与缺口判断（`calculationSummary` 由后端回填） |
| P3 | `anomalies`, `reviewItems` | 你对 `calculation.result.statement_changes` 的异动定性（`changes` 由后端回填） |
| P4 | `benchmark`, `limitations` | `benchmark` 取自 baseline（`comparisons` 由后端回填） |
| P5 | `profitabilityQuality`, `conclusion`, `limitations` | 你的盈利质量判断与非空结论（`signals` 由后端回填） |

> 后端回填字段即使你一并提交也会被覆盖，但**允许**提交（便于自查）。省略是推荐做法。
> P0 的 `companyName`、P5 的 `conclusion` 必须非空，否则同步会被拒。

`markdown` 必须至少包含对应 `# Pn` 阶段标题和一句非空结论；
其余最多三条关键数值事实与限制，数值只能从 `calculation.result` 摘抄。
不得只写标题、复述整表、裸算数字或展开附注研究。单份 `markdown` 上限 2 MiB。

初始分析写齐 P0-P5。followup 只写实际变化阶段，但 `candidate.proposed` 仍必须完整提交。

### 3. 最后才生成 proposal 与 submission

proposal 只支持 P0/P1 字段级变更，并且必须有当前 Run 的冻结材料证据。每个 proposal 至少包含：

```json
{
  "targetStage": "P1",
  "reason": "材料原文支持补充此前为空的字段",
  "changes": [
    {
      "path": "/periods/0/balanceSheet/accounts_receivable",
      "beforeValue": null,
      "proposedValue": 0,
      "evidenceRefs": [{ "runMaterialId": "<id>", "locator": "页码或表名" }]
    }
  ]
}
```

不覆盖 baseline 非空值；冲突作为限制记录，不生成覆盖 proposal。

## Submission 唯一契约（finance-runtime/v2）

```json
{
  "submissionKind": "initial-analysis",
  "complete": true,
  "requiredFilesVersion": "finance-runtime/v2",
  "candidateDisposition": "artifacts-only-no-authoritative-change",
  "changedStages": ["P0", "P1", "P2", "P3", "P4", "P5"],
  "candidate": {
    "proposed": {
      "schemaVersion": "finance-proposed/v1",
      "runId": "<runId>",
      "attemptId": "<attemptId>",
      "baseVersions": {},
      "p0": {},
      "financialInput": {},
      "changeSummary": []
    },
    "stages": {
      "P0": { "status": "done", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P0 ..." },
      "P1": { "status": "done", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P1 ..." },
      "P2": { "status": "done", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P2 ..." },
      "P3": { "status": "done", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P3 ..." },
      "P4": { "status": "limited", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P4 ..." },
      "P5": { "status": "done", "data": {}, "sourceRefs": [], "limitations": [], "markdown": "# P5 ..." }
    }
  },
  "proposals": []
}
```

`requiredFilesVersion` 必须是 `finance-runtime/v2`；旧的 `finance-runtime/v1`（沙箱路径声明式）后端已拒绝。

`candidateDisposition` 与 `proposals` 只有两种合法组合：

| `proposals` | `candidateDisposition` |
| --- | --- |
| 空数组 | `artifacts-only-no-authoritative-change` |
| 非空数组 | `proposals-attached` |

禁止使用 `review_required`、`done`、`limited` 或其他值作为 `candidateDisposition`。
非空 proposals 的 `changedStages` 必须包含对应的 P0/P1；
空 proposals 仍可声明 P0-P5，表示冻结审计候选，不表示修改权威阶段。

followup 使用 `submissionKind=followup`，只列实际变化的 `changedStages`，
`candidate.stages` 只含这些阶段；`candidate.proposed` 始终必传。

整个 submission 的 JSON 上限 12 MiB，单份 `markdown` 上限 2 MiB。超限会被明确拒绝，
此时精简叙述后重试，不要拆成多次提交。

## 完成条件

提交前逐项检查：

- 所有数值均摘抄自 `calculation.result`，没有任何手算值。
- `candidate.proposed` 的 `baseVersions` / `p0` / `financialInput` 与 baseline 一致（无 proposal 时逐字节一致）。
- 每个声明阶段都有非空 `data`、`markdown`，且 `markdown` 首行是 `# Pn` 标题。
- P0 的 `companyName`、P5 的 `conclusion` 非空。
- disposition 与 proposals 数量严格匹配。
- 以 `submit_finance_turn` 成功返回为 turn 提交完成（须回传 `turnSecret`）。
- 在后端返回同步成功前，只能说"候选已提交/等待同步"，不能声称"分析已同步"或"权威阶段已更新"。
- `researchMode=provided-only` 时提交内容不得含任何外部链接 —— 后端会扫描并拒绝。

## turn 提交之后：是否还要出专项报告

`submit_finance_turn` 成功返回即本文职责结束。此后：

- 用户**没有**要求专项报告 → 直接汇报候选已提交，流程结束。
- 用户**要求**「财务专项报告」/「报告」/「Word」→ 转入 `SKILL.md`「公共收尾：生成财务专项报告（MD + DOCX）」节，
  按该节 6 步交付。数值只能取自本 turn 已获得的 `calculation.result`，不得重算。
  **必须 MD + DOCX 同步交付**，`save_finance_report` 漏传 `docxCosKey` 视为未完成。
