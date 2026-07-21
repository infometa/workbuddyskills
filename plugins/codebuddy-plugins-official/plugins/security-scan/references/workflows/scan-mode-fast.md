# Fast 扫描模式（极速扫描）

> 引用方：commands/project.md、commands/diff.md
>
> **当 `scanMode == "fast"` 时，仅 Read 本文件 + `scan-mode.md`（索引/对比）即可，无需加载 scan-mode-light.md / scan-mode-deep.md。**

Fast 模式 = Light 的检查逻辑 + 严格执行纪律。目标平均耗时 5 分钟（vs Light 22 分钟）。

---

## Fast 模式硬性约束（必读）

> 此章节定义 Fast 模式相对于 Light 的执行纪律，基于对 Light 实际会话的耗时瓶颈分析（平均耗时 22 分钟 → Fast 目标 5 分钟）。

Fast = **Light + 纪律**。检查逻辑与 Light 完全相同，但执行方式受以下约束：

**A. 并行化（必须）**
- 阶段 1 的 Grep/Glob（技术栈、Sink、凭证）必须同一 message 内并行发起，最多 4 个并行工具调用
- 阶段 2 多文件 Read 必须同一 message 内并行发起，N 个文件 = 一批并行 Read

**B. 禁用轮询等待（必须）**
- ❌ 禁止 `sleep N && ls` 循环检查产物
- ❌ Fast 流程**内部**禁止再 fork 任何扫描子 Agent（vuln-scan / logic-scan 等），project 和 diff 的扫描判定均走当前上下文内联执行，守住内联验证合并与 5 分钟纪律
- ✅ **例外**：允许由**主对话**把整条 Fast 流程作为单个后台 Agent 调度（`--background`，见 commands/project.md「后台模式」），该后台 Agent 内部仍遵守本约束（不再 fork 子 Agent、保持内联）。机制为 `Task(subagent_type=bg-scan, run_in_background=true)` + `SendMessage` 回流

**C. 扫描+验证合并（必须）**
- 阶段 2 产 finding 时同时完成代码存在性校验，打标 `verificationStatus: "inline-verified"`
- 阶段 3 完全跳过

**D. 字段 schema 约束（必须）**
- 规范字段：`riskType` / `filePath` / `lineNumber` / `severity` / `riskConfidence` / `verificationStatus`
- `riskType` 必须使用 `risk-type-taxonomy.yaml` 中的标准中文 `name`（如 "SQL 注入"、"SSRF"），禁止复合描述（如 "A / B"）或括号补充（如 "X (Y)"）
- 即使写错，`scripts/merge_findings.py` 的 `normalize_finding_schema` 会兜底映射常见漂移（finding_type / file_path / line / riskLevel / confidence 等）

**E. 裁剪范围**
- 阶段 1 保留脚本化攻击面/入口预筛，但跳过 LLM 重复翻页扫描
- 阶段 3 不启动 verifier Agent；`merge-verify` bypass 路径会前置跑 `run_pre_check`，并对 Critical/High 运行确定性 Fast+ 校验（`SECURITY_SCAN_FAST_V2=0` 可关闭）

**F. 前置脚本化预筛（必须）**
- 阶段 1 必须在 LLM 任何 Grep 之前运行 `pattern_grep.py` 六条预筛命令，把 Sink / 防御 / 凭证 / 入口 / 攻击面 / 云资源访问流写入 `project-index.db`：
  1. `grep-sinks` — 通用 Sink 表
  2. `grep-defenses` — 防御模式表
  3. `grep-secrets` — 凭证/密钥/危险配置
  4. `grep-entries` — 入口点检测
  5. `grep-attack-surface` — 攻击面（上传/WebSocket/Cron/MQ/RPC/GraphQL）
  6. `grep-cloud-resource-flow` — CAM/COS sink ±15 行窗口三元组（`cloud_resource_flow` 表）
- 阶段 2 必须通过 `index_db.py query --preset sinks-top-per-file --limit 3`（+ `defenses-for-file` 为每个文件拉本地与全局防御）消费预筛产物；每文件 Top-K 裁剪，避免同文件同类型 Sink 触发 LLM 重复判定
- 阶段 2 还须额外消费 `--preset cloud-resource-orphans` 输出（`has_controllable=1 AND has_branch_sts=0 AND has_resource_scope=0`），驱动**第 4 判**（CAM/COS STS 分支级鉴权缺失），见下文约束 H
- 阶段 2 同时消费 `--preset auth-element-incomplete-candidates` 输出（`is_auth_element_incomplete=1`），驱动**第 5 判**（认证要素缺失），见下文约束 H
- diff 模式下脚本仍跑整仓；阶段 2 用 `changedCodeFiles` 列表过滤；project 模式直接使用整仓 Sink

**G. Source 可达性 + CAM/COS 五判（必须）**
- LLM 在阶段 2 产出 finding 之前，必须对每个候选 Sink 回答五个判定题；任一关键判定（1/2/3）不通过即 `verificationStatus: "inline-dismissed"`，不产出 finding：
  1. **isReachableFromSource**：Sink 的关键参数是否可由外部输入（HTTP 参数、DTO 字段、路径变量、Cookie、Header、上传文件、MQ 消息、外部 API 返回）到达？
  2. **isUndefended**：基于 `defenses-for-file` 查询 + Sink 前后 30 行上下文，是否缺少有效防御（参数化查询、白名单、强类型、Bean Validation、Spring Security 注解）？
  3. **isAttackerReachable**：Sink 所在函数是否存在一条通往入口点（Controller / @RestController / HttpServlet / @MessageMapping / @KafkaListener / @Scheduled）的调用链？
  4. **isBranchStsMissing**（仅 CAM/COS 类 Sink，从 `cloud-resource-orphans` preset 流入；非云资源 Sink 直接置为 `n/a`）：sink 所在 if/switch 分支内是否**缺失** `sts_signals.defense_keywords` 与 `resource_scope_patterns`？同函数其它分支出现 STS 关键字、或 `defense_config_families` 仅在文件其它位置出现，**不能反驳**当前分支的缺失。
  5. **isAuthElementIncomplete**（仅 CAM/COS 类 Sink，从 `auth-element-incomplete-candidates` preset 流入；非云资源 Sink 直接置为 `n/a`）：sink 所在分支是否同时满足「签名函数命中 + 身份字段事后消费 + 分支无防御」？等价于该 sink 在 `auth-element-incomplete-candidates` preset 中且分支内未出现 `signed_material_keywords ∩ required_identity_fields` 共现。
- **禁止只凭 Sink 关键字命中直接产出 finding**；五判完整 prompt 与决策表见下文 `阶段 2: 扫描 + 内联验证`。

---

## 阶段 0: 初始化

> 完整初始化流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`

Fast 模式在初始化阶段的差异：
- 权限检查与配置（init-步骤1）：检查 + 自动修复
- 模式选择（init-步骤2）：交互选择
- tree-sitter（init-步骤3）：**整体跳过**
- LSP 探活与安装（init-步骤4）：**整体跳过**
- 环境就绪确认（init-步骤5）：直接输出就绪信息（无 pendingActions）

---

## 阶段 1: 探索

编排器内快速完成基础探索，**严格遵守 Fast 硬性约束 A + G**：所有 Grep/Glob 并行发起，且 LLM Grep 之前必须先跑脚本预筛（五条 `pattern_grep.py`）。

执行顺序：

1. `index_db.py init`（初始化 DB）
2. **产品形态分析（所有扫描模式必须执行，禁止脚本判定）**：
   - 不调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type`。
   - 由当前 Agent 直接分析文件结构、入口点、依赖/Manifest 与核心代码语义。
   - 结论只能是 `客户端` / `AI agent` / `web` / `数据库` / `未知`；机器码只能是 `client` / `ai_agent` / `web` / `database` / `unknown`。
   - 产物：`$batch_dir/project-type.json`，必须包含 `product_shape_decision` 与 `product_shape_evidence_chain.evidence[]`。每条 evidence 必须有真实 `path`、`line` 或 `lines`、`snippet`、`reason`；证据不足或冲突时输出 `未知`。
3. **脚本预筛（约束 G，不经过 LLM，串行跑完）**：
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
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/pattern_grep.py" grep-cloud-resource-flow \
     --batch-dir "$batch_dir" \
     --project-path . \
     --knowledge-file "${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/tencent-cloud-security.yaml"
   ```
   > 也可一键调用 `pattern_grep.py grep-all --patterns-file ... --knowledge-file ...`（v3.5.5+ 已串行包装上述六条命令 + `prescreen-sinks`，同进程内 `_detect_grep_tool` 缓存生效）。
3. **LLM 并行补充（单 message 发起，约束 A）**：
   - 文件枚举 + 技术栈识别（Glob + Grep）
   - 凭证/密钥补充（脚本未覆盖的框架特定密钥）
   - CVE 扫描（读 `indexer-findings` 表）

跳过（瘦身）：
- 攻击面/入口的 LLM 重复扫描（脚本 `grep-entries` / `grep-attack-surface` 已落 DB）
- Sink / 凭证的 LLM 重复定位（脚本已完成）
- 框架级防御基线 LLM 扫描（脚本 `grep-defenses` 已落 DB，阶段 2 按需拉取本地与全局防御）

产物验收：
```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset sinks-by-severity --limit 100
# 预期 rows.count > 0；若为 0，说明脚本未跑或项目无 Sink，停止并排查。
```

---

## 阶段 2: 扫描 + 内联验证（纪律化）

沿用 Light 的内联扫描逻辑（LLM 在主窗口读 Sink 上下文、判断防御、产出 finding），但增加以下约束。

### 1. Sink 清单驱动扫描（约束 G 续）

扫描开始前先拉 DB，使用 **每文件 Top-K** 裁剪策略避免同文件多 Sink 重复判定（默认 k=3）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset sinks-top-per-file --limit 3
```

得到 `{sinks: [...], count: N, k_per_file: 3}`。`sinks` 按 `severity_level` 全局排序、同文件连续，便于 LLM 按文件批量 Read + 批量判定。

- diff 模式下与 `changedCodeFiles` 求交集
- 按 `severity_level ASC`（S1 → S3）处理，前 k 个文件（建议 k 文件 ≤ 30）进入 LLM 判定队列
- **回滚说明**：环境变量 `SECURITY_SCAN_FAST_V2=0` **仅关闭 `merge_findings.py` 的 pre-check 兜底**；Top-K 裁剪和批量四判由本文档定义，LLM 执行时感知不到环境变量。若需完全回退到 Fast P0 基线行为，请 `git revert` 本次 A+B 改动（恢复旧 prompt 和旧 preset 名）

### 2. Source 可达性 + CAM/COS 五判（约束 H，文件内批量）

五判规则覆盖通用 Source→Sink 三判 + 云资源 Sink 第 4 判（CAM/COS 分支级 STS 鉴权缺失）+ 第 5 判（认证要素缺失）。**默认采用文件内批量模式**：LLM Read 一个文件后，对该文件**所有候选 Sink** 一次性输出 verdict 数组，避免同文件 N 个 Sink 触发 N 次 LLM 往返。

**逐字** prompt（文件级批量）：

```
对以下同一文件内的 {N} 个 Sink，逐个执行五判再一次性输出 verdict 数组：
  [文件] {file}
  [Defenses-for-file] {defenses JSON from index_db query}
  [Cloud-resource-orphans] {orphans JSON from index_db query --preset cloud-resource-orphans --filter-file {file}}
  [Auth-element-incomplete-candidates] {candidates JSON from index_db query --preset auth-element-incomplete-candidates --filter-file {file}}
  [Sinks]
    1. line={L1} type={T1} snippet={S1}
    2. line={L2} type={T2} snippet={S2}
    ...

判定 1 (isReachableFromSource)
  Sink 关键参数是否可由外部输入（HTTP 参数、DTO 字段、路径变量、Cookie、Header、上传文件、MQ 消息、外部 API 返回）到达？
    - 字面量 / 配置常量 / 枚举 → "no"
    - 从 HTTP 参数 / DTO / Controller 透传 → "yes"
    - 无法追溯 / 不确定 → "maybe"

判定 2 (isUndefended)
  基于 Defenses-for-file + Sink 前后 30 行上下文，是否缺少有效防御？
    - PreparedStatement / 参数化查询 → "no（已防御）"
    - 白名单 / 强类型 enum / @Pattern @Size / Bean Validation → "no（已防御）"
    - 仅字符串替换（replaceAll(',', '')）/ 黑名单 → "yes（不充分）"
    - 无任何防御 → "yes"

判定 3 (isAttackerReachable)
  Sink 所在函数是否存在一条通往入口点（Controller / @RestController / HttpServlet / @MessageMapping / @KafkaListener / @Scheduled）的调用链？
    - private 工具 + 仅被单元测试调用 → "no"
    - 从 Controller 透传到 Service/DAO → "yes"
    - 未能判断 → "maybe"

判定 4 (isBranchStsMissing)（仅 CAM/COS 类 Sink；非云资源 Sink 直接置 "n/a"）
  Sink 是否出现在 [Cloud-resource-orphans] 列表中？且其所在 if/switch 分支内缺失 sts_signals.defense_keywords 与 resource_scope_patterns？
    - Sink 命中 orphans 且窗口内确认无 q-token / AssumeRole / x-cos-security-token / sessionToken / qcs::cos:.*:prefix/ 等关键字 → "yes"
    - Sink 在 orphans 中但窗口内或同分支已出现上述任一关键字 → "no（分支已防御）"
    - Sink 不属于 cos_object_op / ci_internal_forward / cam_sig_auth 三类 → "n/a"
    注意：同函数其它分支出现 STS 关键字、或 defense_config_families 仅在文件其它位置出现，不能反驳当前分支的缺失。

判定 5 (isAuthElementIncomplete)（仅 CAM/COS 类 Sink；非云资源 Sink 直接置 "n/a"）
  Sink 是否出现在 [Auth-element-incomplete-candidates] 列表中？且其分支内：
    - 命中 signature_func_keywords（CalcSign/HmacSha256/MD5Hex/verifySign/...） 且
    - 同窗口出现 required_identity_fields（ownerUin/sub_uin/ownerAppid/Host/bucket/region）∩ request_header_sources（X-COS-CI-ARGS/base64_decode/ParseFromArray/...） 且
    - 分支内未出现 signed_material_keywords（stringToSign/signSource/...）与身份字段共现？
  → "yes"
  签名材料中确认包含身份/资源字段（stringToSign 与 ownerUin/Host 同分支共现）→ "no（签名材料完整）"
  Sink 不属于 cam_sig_auth / ci_internal_forward 类之一 → "n/a"
  注意：身份字段在签名后用于日志/打点不算违规；只要 string-to-sign 列表中包含即视为已防御。

输出 JSON 数组（每个 Sink 一条，顺序与 Sinks 列表一致）：
  {
    "verdicts": [
      {
        "line": {L1},
        "isReachableFromSource": "yes|maybe|no",
        "isUndefended": "yes|no",
        "isAttackerReachable": "yes|maybe|no",
        "isBranchStsMissing": "yes|no|n/a",
        "isAuthElementIncomplete": "yes|no|n/a",
        "action": "report | downgrade | dismiss",
        "reasonBrief": "<= 30 字中文原因"
      },
      ...
    ]
  }

action 决策表：
  通用 Sink（判定 4 = n/a 且判定 5 = n/a）
    判定 1/2/3 全 yes               → report     → verificationStatus=inline-verified, riskConfidence ≤ 90
    一个 maybe 其它 yes              → downgrade  → verificationStatus=inline-verified, severity 降一级 或 riskConfidence -= 20
    任一 no（含 1/2/3）              → dismiss    → verificationStatus=inline-dismissed
  CAM/COS Sink（判定 4 ∈ {yes, no} 或 判定 5 ∈ {yes, no}）
    1/2/3 全 yes 且判定 4 = yes 且判定 5 = n/a   → report (riskType="COS/万象 STS 鉴权缺失")
    1/2/3 全 yes 且判定 5 = yes（无论判定 4）   → report (riskType="认证要素缺失")
       └─ 判定 4 同时 yes 时，dedup 保留"认证要素缺失"，dismiss STS 缺失（详见 §1.5.5 dedup 规则）
    1/2/3 全 yes 且判定 4 = yes 且判定 5 = no    → report (riskType="COS/万象 STS 鉴权缺失")
    1/2/3 全 yes 且判定 4 = no 且判定 5 = no     → dismiss（两类防御均存在）
    判定 1 = no 或 判定 2 = no 或 判定 3 = no    → dismiss
```

**批量约束**：
- 每个文件一次 prompt，对该文件 N 个 Sink 一并输出
- 多个文件在同一 assistant message 内并行（约束 A，≤4 并发）
- Read 与 verdict 输出合并到单一 message，避免往返开销
- **严禁遗漏**：verdicts 数组长度必须等于 Sinks 列表 N；若 LLM 判断 dismiss 仍需输出 verdict 条目并记录 reason，仅在转写 `light-inline.json` 时过滤

**注意**：本批量四判 prompt 是本文档的**硬性规范**，由 LLM 主动遵循，无环境变量可切换。`SECURITY_SCAN_FAST_V2=0` 仅关闭 pre-check 兜底，不影响此 prompt。若需完全回退到单 Sink 模式，请 `git revert` 本次改动。

### 3. 防御查询脚本化

为每个涉及文件执行：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset defenses-for-file --filter-file <path>
```

结果注入判定 2 的 prompt，减少 LLM 自行 Grep 防御。

### 4. 并行 Read + 批量四判合并（约束 A）

同一 assistant message 内：Read 多个文件（≤ 4 并发）→ 对每个文件的所有 Sink 输出 verdict 数组（文件内批量，见约束 H）。Read 与 verdict 输出合并为单一 message，避免往返开销。仅对 `action=report` / `downgrade` 的 Sink 进入 `light-inline.json`；`dismiss` 的条目只出现在 verdict 日志中。

### 5. 字段 schema 规范

`riskType` / `filePath` / `lineNumber` / `severity` / `riskConfidence`（Fast 上限 90） / `verificationStatus`（即使写错，`merge_findings.py` 的 `normalize_finding_schema` 会兜底）。

**产物**：`agents/light-inline.json`（`sourceAgent: "light-inline"`）

**合并命令**：
```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
  --batch-dir "$batch_dir" \
  --extra-agents indexer-findings,light-inline

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-verify \
  --batch-dir "$batch_dir"
# Fast 模式 merge-verify 会：
#   1) 检测 scan_mode == "fast" 且无 verifier 产出 → 走 bypass 路径
#   2) bypass 路径前置执行 verifier.run_pre_check 兜底
#      - 校验文件存在 / 行号范围 / 代码片段模糊匹配
#      - 不通过的 finding 打 _removed，从 merged-verified.json 中剔除
#      - 代码片段模糊匹配失败不删除，仅降级（扣置信度）
#   3) SECURITY_SCAN_FAST_V2=0 可回滚关闭兜底
```

置信度上限 **90**。

### Source 可达性 + CAM/COS 五判 决策表（速查）

| isReachableFromSource | isUndefended | isAttackerReachable | isBranchStsMissing | isAuthElementIncomplete | action | verificationStatus |
|---|---|---|---|---|---|---|
| yes | yes | yes | n/a | n/a | report | inline-verified |
| yes | yes | yes | yes | n/a | report (riskType=`COS/万象 STS 鉴权缺失`) | inline-verified |
| yes | yes | yes | n/a | yes | report (riskType=`认证要素缺失`) | inline-verified |
| yes | yes | yes | yes | yes | report (riskType=`认证要素缺失`，dedup 掉 STS 缺失) | inline-verified |
| yes | yes | yes | no  | yes | report (riskType=`认证要素缺失`) | inline-verified |
| yes | yes | yes | yes | no  | report (riskType=`COS/万象 STS 鉴权缺失`) | inline-verified |
| maybe | yes | yes | n/a | n/a | downgrade | inline-verified |
| yes | yes | maybe | n/a | n/a | downgrade | inline-verified |
| yes | yes | yes | no  | no  | dismiss（两类防御均存在） | inline-dismissed |
| no  | *   | *   | *   | *   | dismiss | inline-dismissed |
| *   | no  | *   | *   | *   | dismiss | inline-dismissed |
| *   | *   | no  | *   | *   | dismiss | inline-dismissed |

> 当 `isBranchStsMissing=yes` 与 `isAuthElementIncomplete=yes` 同时命中时，`merge_findings.py` dedup 阶段保留 `auth-element-incomplete`（与 light §1.5.5 一致）。

---

## 阶段 3: 验证

**完全跳过独立 verifier Agent**。阶段 2 已在产出 finding 时内联完成代码存在性校验（`verificationStatus: inline-verified`）。

`merge_findings.py` 自动走 `scan_mode == "fast"` 的 bypass 分支，并在 `SECURITY_SCAN_FAST_V2 != 0` 时对 Critical/High 运行 `pre-check → chain-verify → challenge` 的确定性 Fast+ 校验；校验结果用于降置信度和标记人工审核。置信度上限 90。

---

## 阶段 4: 修复

| 维度 | Fast |
|------|------|
| 自动修复 | 同 Light（受限） |
| 报告生成输入 | `merged-scan.json`（fallback） |
| 修复 finding 来源 | 同 Light（`merged-scan.json`，`confidence >= 90`，跳过 `challengeVerdict` 检查） |

---

## 错误处理

1. 基础探索失败 → 终止审计，提示用户重试
2. 编排器内联分析异常 → 基于已有 indexer findings 继续生成报告（同 Light 兜底）
3. 字段漂移 → `normalize_finding_schema` 自动兜底，不阻断流程
