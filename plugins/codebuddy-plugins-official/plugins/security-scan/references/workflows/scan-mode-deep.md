# Deep 扫描模式（深度扫描）

> 引用方：commands/project.md、commands/diff.md
>
> **当 `scanMode == "deep"` 时，仅 Read 本文件 + `scan-mode.md`（索引/对比）即可，无需加载 scan-mode-fast.md / scan-mode-light.md。**

Deep = 全语义索引深度扫描。编排器写入索引 DB → indexer Agent 构建语义索引 → 三 Agent 并行扫描 → 五层混合验证。置信度上限 100。

---

## 阶段 0: 初始化

> 完整初始化流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`

Deep 模式在初始化阶段的差异：
- 权限检查与配置（init-步骤1）：检查 + 自动修复
- 模式选择（init-步骤2）：交互选择
- tree-sitter（init-步骤3）：检测 + 自动安装
- LSP 探活与安装（init-步骤4）：探活 + 自动安装二进制 + 二次探活
- 环境就绪确认（init-步骤5）：可能包含 LSP / tree-sitter 降级提示（不阻塞，自动降级继续）

---

## 阶段 1: 探索

先执行 Light 模式的基础探索，然后将探索结果写入索引数据库，最后启动 indexer Agent 从 indexer-步骤2 开始构建语义索引。

### 1.1 编排器写入索引数据库（脚本化 indexer-步骤1 前置）

基础探索完成后，编排器通过脚本批量执行 indexer-步骤1 的确定性工作，并将结果写入 `project-index.db`：

```bash
# 1. 初始化索引数据库
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" init --batch-dir "$batch_dir"

# 2. 检测项目框架（确定性）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" detect-framework --project-path .

# 2.5. 产品形态分析（所有扫描模式必须执行，禁止脚本判定）
# 不调用 agent_classifier.py 或 orchestration_helper.py detect-project-type。
# 由当前 Agent 直接分析仓库结构、入口点、依赖/Manifest 与核心代码语义。
# 结论只能是：客户端 / AI agent / web / 数据库 / 未知。
# 写入 $batch_dir/project-type.json，并在 product_shape_evidence_chain.evidence[] 中保留真实 path、line/lines、snippet、reason。

# 3. 写入项目元数据 + 文件清单（编排器已有的枚举结果）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" write --batch-dir "$batch_dir" --data '{
  "phase": "phase1",
  "meta": {
    "framework": "{framework}",
    "file_count": "{fileCount}",
    "total_lines": "{totalLines}",
    "language": "{primaryLanguage}"
  },
  "table": "files",
  "rows": [{fileRows}]
}'

# 4. 脚本化 Sink grep（替代手动 Grep 循环）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-sinks \
  --batch-dir "$batch_dir" \
  --patterns-file "${CODEBUDDY_PLUGIN_ROOT}/resource/scan-data/sink-patterns.yaml" \
  --project-path .

# 5. 脚本化入口点检测
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-entries \
  --batch-dir "$batch_dir" \
  --project-path .

# 6. 脚本化攻击面检测
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-attack-surface \
  --batch-dir "$batch_dir" \
  --project-path .

# 7. 脚本化防御检测（基础）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-defenses \
  --batch-dir "$batch_dir" \
  --project-path .

# 8. 脚本化敏感信息检测
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-secrets \
  --batch-dir "$batch_dir" \
  --project-path .

# 9. 写入框架隐式行为（编排器探索阶段检测到的）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" write --batch-dir "$batch_dir" --data '{
  "phase": "phase1",
  "table": "framework_behaviors",
  "rows": [{behaviorRows}]
}'

# 10. 标记 phase1 完成（触发增量扫描启动）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" write --batch-dir "$batch_dir" --data '{"phase":"phase1","phase_status":"completed"}'
```

> **脚本化优势**：步骤 4-8 由 `pattern_grep.py` 确定性执行（无 LLM 参与），结果直接写入 DB。
> 编排器无需手动构造 Grep 命令、解析输出、拼装 JSON、写入 DB，减少 5-8 个 LLM turns。

### 1.2 启动 indexer Agent（从 indexer-步骤2 开始）

```
Task(indexer):
  prompt:
    构建项目语义索引（SQLite 数据库）。
    [batch-dir] "$batch_dir"
    [lspStatus] {lspStatus}
    [db-tool] ${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py
    [ts-parser] ${CODEBUDDY_PLUGIN_ROOT}/scripts/ts_parser.py
    [memory-hints] {memory_hints_json}
    [structureCache] {structureCache_json}
    [scan-mode] deep
    {scope == "diff" ? "[scope] diff\n[changed-files] {changedCodeFiles}\n[related-files-limit] {limit}" : ""}
  max_turns: 30
  mode: bypassPermissions
```

indexer Agent 启动后检测到 indexer-步骤1 已由编排器完成（`phases.phase1 == "completed"`），自动跳过 indexer-步骤1，从 indexer-步骤2 开始执行：
- **indexer-步骤2**（AST 精化，双引擎）：tree-sitter 引导安装 + 批量解析持久化（persist）+ Sink AST 验证；结果缓存到 SQLite（ast_functions、ast_calls、ast_refined_sinks 等），后续阶段通过 cached-query 复用
- **indexer-步骤3**（LSP 语义精化）：端点精化、Sink 调用追踪、调用图构建、防御映射

---

## 阶段 2: 扫描（三 Agent 并行）

### 2.0 增量门控：根据 phase 状态渐进式启动扫描 Agent

扫描 Agent 依赖 indexer 产出的语义索引数据。编排器通过脚本检查 phase 状态，**渐进式启动** Agent：

```bash
# 脚本化门控检查（替代手动 SQL 查询和 if/else 判断）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" should-launch-agent \
  --batch-dir "$batch_dir" \
  --agent vuln-scan
# 返回: {"action": "launch|wait|already_run", "reason": "...", ...}
```

**Phase 与 Agent 启动对应关系**：

| Phase 完成 | 可启动的 Agent | 数据可用性 |
|-----------|---------------|----------|
| phase1 | vuln-scan, red-team | 有 coarse sink，但无 AST/LSP |
| phase1_5 | 触发已启动 agent 的 re-run | 有 AST 数据（精确行号+函数范围） |
| phase2 | logic-scan | endpoints/call_graph/defenses 可用 |
| phase2 | 触发所有 agent final re-run | LSP 数据完整，traceMethod=LSP |

**Re-run 机制**：

```bash
# 检查是否需要 re-run（检测 phase 更新）
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" should-rerun-agent \
  --batch-dir "$batch_dir" \
  --agent vuln-scan
# 返回: {"action": "rerun|no_action|skip", "reason": "New data available: phase1 → phase1_5", "instruction": "rm agents/vuln-scan.json && relaunch"}
```

Re-run 时删除 agent 输出文件，让 agent 重新查询最新 DB 数据。每个 agent 最多 re-run 2 次。

**增量扫描时序**：

```
时间轴
│ phase1 完成
├─→ 启动 vuln-scan-v1 (phase1 sink)
├─→ 启动 red-team-v1 (phase1 数据)
│
│ phase1_5 完成
├─→ 检查 should-rerun-agent vuln-scan → rerun
├─→ 检查 should-rerun-agent red-team → rerun
├─→ vuln-scan-v2 (AST 数据)
├─→ red-team-v2 (AST 数据)
│
│ phase2 完成
├─→ 启动 logic-scan (endpoints 可用)
├─→ 检查 should-rerun-agent vuln-scan → rerun
├─→ 检查 should-rerun-agent red-team → rerun
├─→ vuln-scan-v3 (LSP 完整数据)
├─→ red-team-v3 (LSP 完整数据)
│
│ 所有 agent 完成
└─→ 启动验证流程
```

> **重要**：logic-scan 的 `min_phase` 为 `phase2`（依赖 endpoints 表），不在 phase1 时启动。
> vuln-scan 和 red-team 可在 phase1 启动，但产出的 findings 置信度上限为 90（Grep+Read fallback）。
> phase2 后的 final re-run 使 findings 获得 LSP 数据支持，置信度上限提升至 100。

### 2.0a 进度监控

编排器通过脚本监控整体进度：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/orchestration_helper.py" summarize-progress \
  --batch-dir "$batch_dir"
# 返回: {"progress": "5/8", "progress_pct": 63, "next_actions": [...], ...}
```

`next_actions` 字段给出下一步操作建议（launch_agent / rerun_agent / start_verification / wait）。

### 2.1 启动扫描 Agent（增量启动）

根据 2.0 的门控结果，分阶段启动 Agent。每个 Agent 在输出中记录 `metadata.index_phase`，供 re-run 判断使用：

```
Task(vuln-scan):
  prompt:
    执行 Source→Sink 数据流追踪漏洞审计（C1 注入类）。
    [batch-dir] "$batch_dir"
    [scan-mode] deep
    [db-tool] ${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py
    [输出文件] agents/vuln-scan.json
    [index-phase] {current_phase}  # phase1 | phase1_5 | phase2
  max_turns: 25
  mode: bypassPermissions

Task(logic-scan):  # 仅在 phase2 完成后启动
  prompt:
    执行认证授权（C3）+ 业务逻辑（C7）安全审计。
    [batch-dir] "$batch_dir"
    [scan-mode] deep
    [db-tool] ${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py
    [输出文件] agents/logic-scan.json
    [index-phase] {current_phase}
  max_turns: 25
  mode: bypassPermissions

Task(red-team):
  prompt:
    以红队视角执行 3 核心猎杀问题深度审计（Q1 自造轮子、Q2 异常路径、Q3 信任穿越）。
    [batch-dir] "$batch_dir"
    [scan-mode] deep
    [db-tool] ${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py
    [输出文件] agents/red-team.json
    [index-phase] {current_phase}
  max_turns: 25
  mode: bypassPermissions
```

> **Agent 输出 metadata 要求**：每个 Agent 必须在 JSON 输出中包含 `metadata.index_phase` 字段：
> ```json
> {
>   "metadata": {
>     "index_phase": "phase1",  // 运行时的 phase 状态
>     "rerun_count": 0          // re-run 次数
>   },
>   "findings": [...]
> }
> ```
> 此字段使 `should-rerun-agent` 脚本能判断是否有新数据可用。

### 2.2 等待期间前置工作 + 流式处理

启动 Agent 后，编排器执行前置工作（不空等）：

1. **导出 indexer findings**（密钥/配置/CVE 检测结果）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query --batch-dir "$batch_dir" --preset indexer-findings
```

2. **加载框架知识文件**（按技术栈）

3. **等待扫描 Agent 完成**：编排器通过检查 `"$batch_dir"/agents/` 目录下各 Agent 的 JSON 产物是否落盘来判断完成状态。

### 2.3 续扫处理

对 `status: "partial"` 且有 `pendingSinks`/`pendingEndpoints` 的 Agent：
- vuln-scan：启动续扫实例（max_turns: 15），仅处理 `pendingSinks`
- logic-scan：启动续扫实例（max_turns: 12），仅处理 `pendingEndpoints`

### 2.4 合并扫描结果

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
  --batch-dir "$batch_dir" \
  --extra-agents indexer-findings,vuln-scan,logic-scan,red-team
```

### 2.5 WebSearch 情报增强（Deep 模式专属）

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/orchestration.md > WebSearch 情报增强`（完整场景、预算控制和降级策略见该节）

跳过条件：无 `webSearchCandidate: true` 的 CVE 条目且无 `auditDimension: "C7.7"` 的条目。

---

## 阶段 3: 验证

验证全部 findings，5 层混合验证（脚本 3 层 + verifier Agent + 脚本评分 2 层），置信度上限 100。

> 完整验证流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/verification.md`

执行链路概要：
- **Stage 1-3（确定性脚本验证）**：pre-check（文件/行号/代码片段校验）→ chain-verify（调用链可达性）→ challenge（对抗审查）
- **Stage 4（verifier Agent 深度验证）**：分片执行 verifier-vuln / verifier-logic / verifier-redteam
- **Stage 4 子项 redteam-replay-forge**（CAM/COS sink，且 finding `riskType == "认证要素缺失"`）：
  1. 取 sink 所在签名函数的合法测试样本（time + key + path），通过工具脚本对其计算签名 S
  2. 构造重放请求：保留同一 (time, key, path) 与签名 S，但替换 `X-COS-CI-ARGS` / `X-Cos-Owner-Uin` 中的 `ownerUin` / `sub_uin` / `ownerAppid` / `Host` 为另一租户的值
  3. 静态推演服务端校验路径（直接读 `verifySign` / `checkSign` / `MD5Hex` 等签名校验函数的入参表，确认其入参中**不**含被替换字段）
  4. 若推演确认替换字段不参与签名校验 → finding 升级为 `severity: critical`，并在 `reasonBrief` 写入「跨租户可达：sign verified with forged tenant identity」；若签名材料确实包含被替换字段 → 维持 high 或 dismiss
  - 验证不要求实际发起 HTTP 请求；仅静态推演 string-to-sign 组合即可（无侧信任）
- **Stage 5（脚本评分）**：score → quality 评估
- 最后通过 `merge_findings.py merge-verify` 汇总，生成 `finding-*.json` + `summary.json`

---

## 阶段 4: 修复

| 维度 | Deep |
|------|------|
| 自动修复 | 完整支持（confidence >= 90 可自动修复） |
| 报告生成输入 | `finding-*.json` + `summary.json`（由 `merge-verify` 生成） |
| 修复 finding 来源 | `score-results.json` 或 `agents/verifier-*.json`（完整资格检查） |

---

## 错误处理

1. **indexer 失败**：终止审计，提示用户重试
2. **扫描 Agent 失败**：检查 `agents/{agent-name}.json` 是否有部分产物，有则纳入合并
3. **verifier Agent 失败**：跳过该分片，使用脚本验证结果
4. **确定性脚本失败（score/quality）**：脚本失败不阻断流程，仍可生成报告

产物完整性检查：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/checkpoint_verify.py" verify-artifacts \
  --batch-dir "$batch_dir" \
  --agents vuln-scan,logic-scan,red-team
```

---

## 聚焦模式（`focusMode == "high"` 时生效）

> 聚焦模式完整流程见 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/focus-mode.md`。
> 本节仅列出 Deep 模式下的差异化行为。

### 阶段2扫描：子 Agent 聚焦指令

在启动 vuln-scan / logic-scan / red-team 的 Task prompt 中追加以下聚焦指令：

```
[聚焦模式] scanFocus = "high"
仅产出 severity 为 critical 或 high 的 finding。
对于 medium 级别的类型（SSRF、路径穿越、访问控制缺失、文件上传、信息泄露），
仅在与高危 Sink 位于同一文件或同一调用链时，作为 comboClue 附加输出。
禁止产出独立的 Medium/Low finding。
```

### 阶段3验证：verifier Agent 聚焦挑战模式

启动 verifier Agent 时注入聚焦挑战 prompt。

> **关键约束**：聚焦模式下 verifier Agent **不读取** `chain-verify-results.json` 和
> `challenge-results.json`。verifier 进入纯挑战者角色，按 `agents/verifier.md > 聚焦挑战模式`
> 的信号速查表独立判定。

启动 verifier 实例时在 prompt 中追加：

```
[聚焦模式] 进入挑战模式（refute，非 confirm）。
不读取 chain-verify-results.json 和 challenge-results.json。
按信号速查表独立判定：公网可达？可直接利用？危害过高？
默认立场为怀疑，不确定时降级。
```

### 阶段3末尾：确定性过滤

merge-verify 完成后，**必须**执行：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" focus-filter \
  --batch-dir "$batch_dir"
```

### 阶段4报告：聚焦过滤后产物

使用 focus-filter 后的 `merged-verified.json` 生成报告。
