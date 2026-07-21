# 验证流程

> 引用方：commands/project.md（阶段3）、commands/diff.md（阶段3）

定义 Fast（极速扫描）、Light（快速扫描）和 Deep（深度扫描）的验证策略差异。

---

## Fast 模式: 无独立验证阶段（内联 + bypass 兜底）

Fast 模式**默认跳过独立的阶段 3 verifier Agent**，但在 bypass 路径上保留确定性脚本兜底（`run_pre_check` + Critical/High Fast+ 校验）。验证分四层：

1. **阶段 2 LLM 内联**：Read Sink 上下文时同时完成 Source 可达性三判 + 代码存在性校验 + 防御检查（详见 `scan-mode-fast.md > 阶段 2: 扫描 + 内联验证（纪律化）`），打标 `verificationStatus: "inline-verified" | "inline-dismissed"`。
2. **bypass 路径前置 pre-check 兜底**：`merge_findings.py merge-verify` 检测到 `scan_mode == "fast"` 且既无 `pre-check-results.json` 也无分片时，自动调用 `verifier.run_pre_check(batch_dir)`：
   - 复用 Deep 模式确定性校验逻辑：文件存在性、行号范围、代码片段模糊匹配（60% token 覆盖）
   - 产物 `pre-check-results.json` 由 bypass 流程原有加载逻辑自然应用
   - 不通过的 finding 打 `_removed`，从 `merged-verified.json` 里剔除；代码片段不匹配仅降级不删除
3. **Critical/High Fast+ 确定性校验**：`SECURITY_SCAN_FAST_V2 != 0` 时，bypass 路径对 Critical/High 运行 `chain-verify → challenge`，不启动 verifier Agent；结果用于设置 `verificationStatus` / `challengeVerdict`，并对 dismissed / downgraded / unverified 结果降置信度和标记人工审核。
4. **置信度上限 90**。

**回滚开关**：`SECURITY_SCAN_FAST_V2=0` 可禁用 bypass pre-check 与 Fast+ 确定性校验兜底，回到纯 LLM 内联校验模式。

**设计理由**：
- LLM 幻觉行号 / 片段在 Fast 模式没有 verifier Agent 去兜底，直接污染 `merged-verified.json`
- `run_pre_check` 是纯文件 I/O，无 LLM 调用，毫秒级开销，不影响 Fast 5–7 min 目标
- 复用 bypass 现有加载逻辑，零重复代码

---

## Light 模式: 轻量验证

仅验证严重（Critical）和高危（High）风险：

1. **代码存在性校验**：Glob + Read 验证文件/行号/代码片段是否匹配
2. **基础防御检查**：Grep 搜索 Sink 周围的防御模式
3. 对通过校验的 finding，基于代码上下文评估置信度（上限 90）
4. **§4 严重级别合规校验（确定性，强制）**：`merge-verify` 在 Light bypass 路径调用 `verifier.apply_severity_compliance()`（纯函数，仅依赖 taxonomy.severity_default + finding 字段，不依赖 index.db），对越级 finding 强制收敛——越级无 `severityRationale` 回落基线、有理由也最多 +1 档封顶、线索级不得升至 high/critical。**目的：避免越级噪声直接进报告打扰用户。** 该校验与 Deep/Fast 的 challenge 第 4.5 步共用同一份收敛逻辑（`verifier.correct_one_severity`），三模式级别契约完全一致。

---

## Deep 模式: 确定性脚本 + LLM verifier 混合验证

> **设计原则**：能用脚本确定性验证的用脚本（pre-check、chain-verify、challenge、score、quality），需要 LLM 推理能力的由 verifier Agent 执行（攻击链深度验证、对抗审查）。

### Stage 1: 代码存在性校验 + 分级（脚本）

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" pre-check --batch-dir "$batch_dir"
```

输出：
- `pre-check-results.json`：分级结果
- `filtered-findings.json`：待验证的 findings

### Stage 2: 攻击链索引验证（脚本）

利用 `project-index.db` 对每个 finding 的攻击链进行确定性验证。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" chain-verify --batch-dir "$batch_dir"
```

输出：`chain-verify-results.json`

验证维度：
- Source 验证（endpoints / ast_functions）
- Sink 验证（sinks 表）
- 路径可达性验证（call_graph BFS）
- 防御交叉验证（defenses 表）

产出字段：`verificationStatus`（verified / partially_verified / unverified）

### Stage 3: 确定性对抗审查（脚本）

对 verified/partially_verified 的 finding 执行自动化对抗审查。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" challenge --batch-dir "$batch_dir"
```

输出：`challenge-results.json`

审查维度：
- 防御有效性挑战：查 defenses 表，匹配 riskType 对应的有效防御类型
- 误报模式检测：测试文件、示例代码排除
- 死代码检测：无入站调用且非端点
- 攻击链完整性挑战：traceMethod == unknown 则降级
- 跨 finding 冲突检查：同一位置不同结论

产出字段：`challengeVerdict`（confirmed / dismissed / downgraded）

### Stage 4: verifier Agent 深度验证（LLM）

按 sourceAgent 拆分 findings 并启动并行 verifier 实例：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" split --batch-dir "$batch_dir"
```

产出：
- `filtered-findings-vuln.json`
- `filtered-findings-logic.json`
- `filtered-findings-redteam.json`

verifier Agent 执行：
1. **攻击链深度验证**：LSP incomingCalls/outgoingCalls 确认入口可达性、数据流完整性、防御有效性、多态性评估
2. **对抗审查**（仅 Critical/High）：红队视角挑战 verified findings，搜索全局防御、扩展上下文、评估攻击可行性

按 sourceAgent 并行启动 verifier 实例：

```
Task(verifier-vuln):
  prompt:
    验证 vuln-scan findings 的攻击链可达性和防御有效性。
    [batch-dir] "$batch_dir"
    [findings-file] filtered-findings-vuln.json
    [输出文件] agents/verifier-vuln.json
  max_turns: 20
  mode: bypassPermissions

Task(verifier-logic):
  prompt:
    验证 logic-scan findings 的攻击链可达性和防御有效性。
    [batch-dir] "$batch_dir"
    [findings-file] filtered-findings-logic.json
    [输出文件] agents/verifier-logic.json
  max_turns: 20
  mode: bypassPermissions

Task(verifier-redteam):
  prompt:
    验证 red-team findings 的攻击链可达性和防御有效性。
    [batch-dir] "$batch_dir"
    [findings-file] filtered-findings-redteam.json
    [输出文件] agents/verifier-redteam.json
  max_turns: 20
  mode: bypassPermissions
```

verifier Agent 会读取 chain-verify 和 challenge 脚本产出，跳过已被脚本确认/淘汰的 findings，聚焦脚本无法处理的深度推理。

### Stage 5: 置信度评分 + 质量评估（脚本）

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" score --batch-dir "$batch_dir"
```

输出：`score-results.json`

> **置信度评分规则**：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/techniques/confidence-scoring.md`
>
> 核心公式（5 行摘要）：
> ```
> 置信度 = 攻击链可达性分(0-40) + 防御措施分(0-30) + 数据源可控性分(0-30)
> traceMethod 上限：LSP=100, Grep+Read=90, unknown=50
> 高置信度门控(>=90)：需 verificationStatus=verified + challengeVerdict=confirmed/escalated + defenseSearchRecord非空
> ```

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" quality --batch-dir "$batch_dir"
```

输出：`quality-assessment.json`

### 最终: 合并验证结果

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-verify --batch-dir "$batch_dir"
```

---

## 验证模式对比

| 维度 | Fast（极速扫描） | Light（快速扫描） | Deep（深度扫描） |
|------|-----------------|------------------|-----------------|
| 验证范围 | 所有 finding（扫描时内联） | Critical + High | 全部 findings |
| 验证方式 | 阶段 2 内联（无独立阶段 3） | 编排器内联验证 | 脚本确定性验证（3 层）+ LLM verifier Agent（深度验证）+ 脚本评分（2 层） |
| 置信度上限 | 90 | 90 | 100 |
| 攻击链索引验证 | 无 | 无 | 有（利用 project-index.db） |
| LLM 深度验证 | 无 | 无 | 有（verifier Agent 按 sourceAgent 并行分片） |
| 对抗审查 | 无 | 无 | 脚本确定性审查 + LLM 对抗审查 |
| §4 级别合规校验（确定性） | 有（bypass challenge 兜底，Critical/High） | 有（apply_severity_compliance 纯函数兜底，全量） | 有（challenge 第 4.5 步，全量） |
| 质量评估 | 无 | 无 | 有 |
