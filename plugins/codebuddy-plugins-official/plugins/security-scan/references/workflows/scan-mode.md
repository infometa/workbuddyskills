# 扫描模式索引

> 引用方：commands/project.md、commands/diff.md、references/workflows/initialization.md、references/workflows/verification.md
>
> 本文件是 Fast / Light / Deep 三种扫描模式的**入口与对比表**。具体执行细节按当前 `scanMode` 选一份独立文件 Read，不要全部加载。

---

## 按模式跳转（必读）

| scanMode | 仅需 Read 的文件 |
|---|---|
| `fast` | `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-fast.md` + 本索引 |
| `light` | `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-light.md` + 本索引 |
| `deep` | `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode-deep.md` + 本索引 |

> 注：本索引仅含跨模式的对比表与共享交互逻辑（约 3 KB），加载代价极低；具体阶段执行细节都在三份独立文件里。

---

## 模式选择交互

> 完整交互流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md > init-步骤2: 模式选择`

若用户通过 `--scan-level fast`、`--scan-level light` 或 `--scan-level deep` 指定了扫描模式，则**直接采用**该模式，跳过交互。否则弹出交互让用户选择"极速扫描（Fast）"、"快速扫描（Light）"或"深度扫描（Deep）"。

> 模式选择在权限配置（init-步骤1）之后、环境准备（init-步骤3/4）之前执行。后续步骤按需准备：Fast/Light 跳过 LSP，Deep 才做 LSP 探活+安装。

记录 `scanMode = "fast" | "light" | "deep"`。

---

## 阶段 0: 初始化差异

> 完整初始化流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`

| 维度 | Fast | Light | Deep |
|------|------|-------|------|
| 权限检查与配置（init-步骤1） | 检查 + 自动修复 | 同 Fast | 同 Fast |
| 模式选择（init-步骤2） | 交互选择 | 同 Fast | 同 Fast |
| tree-sitter（init-步骤3） | **整体跳过** | **整体跳过** | 检测 + 自动安装 |
| LSP 探活与安装（init-步骤4） | **整体跳过** | **整体跳过** | 探活 + 自动安装二进制 + 二次探活 |
| 环境就绪确认（init-步骤5） | 直接输出就绪信息（无 pendingActions） | 同 Fast | 可能包含 LSP / tree-sitter 降级提示（不阻塞，自动降级继续） |

---

## 阶段 1 / 2: 探索与扫描差异

所有扫描模式在阶段 1 必须执行**产品形态分析**，但**禁止调用脚本做产品形态判定**（不得调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type`）。由当前 Agent 基于仓库结构、入口点、依赖/Manifest、核心代码语义直接判断，并产出 `$batch_dir/project-type.json`。结论限定为 `客户端` / `AI agent` / `web` / `数据库` / `未知`；机器码限定为 `client` / `ai_agent` / `web` / `database` / `unknown`。必须将真实文件证据写入 `product_shape_evidence_chain.evidence[]`，每条证据包含 `path`、`line` 或 `lines`、`snippet`、`reason`，并透传到 HTML / JSON。证据不足或冲突时必须输出 `未知`。

按 scanMode 跳转到对应文件的"阶段 1: 探索"和"阶段 2: 扫描"小节：

- Fast：`scan-mode-fast.md > 阶段 1: 探索` 与 `> 阶段 2: 扫描 + 内联验证（纪律化）`
- Light：`scan-mode-light.md > 阶段 1: 探索` 与 `> 阶段 2: 扫描（编排器内联扫描）`
- Deep：`scan-mode-deep.md > 阶段 1: 探索` 与 `> 阶段 2: 扫描（三 Agent 并行）`

---

## 阶段 3: 验证差异

> 完整验证流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/verification.md`

- **Fast**：**不启动独立 verifier Agent**。阶段 2 已在产出 finding 时内联完成代码存在性校验（`verificationStatus: inline-verified`）。`merge_findings.py` 自动走 `scan_mode == "fast"` 的 bypass 分支，并在 `SECURITY_SCAN_FAST_V2 != 0` 时对 Critical/High 运行 `pre-check → chain-verify → challenge` 的确定性 Fast+ 校验；校验结果用于降置信度和标记人工审核。置信度上限 90。详见 `scan-mode-fast.md > 阶段 3: 验证`。
- **Light**：仅验证 Critical + High，编排器内联验证（代码存在性 + 基础防御检查），置信度上限 90。详见 `scan-mode-light.md > 阶段 3: 验证`。
- **Deep**：验证全部 findings，5 层混合验证（脚本 3 层 + verifier Agent + 脚本评分 2 层），置信度上限 100。详见 `scan-mode-deep.md > 阶段 3: 验证`。

---

## 阶段 4: 修复差异

| 维度 | Fast | Light | Deep |
|------|------|------|------|
| 自动修复 | 跳过 | 跳过（不修改用户代码；不弹修复确认） | 完整支持（confidence >= 90 可自动修复） |
| 报告生成输入 | `merged-scan.json`（fallback） | `merged-scan.json`（无 `finding-*.json`，`generate_report.py` 自动 fallback） | `finding-*.json` + `summary.json`（由 `merge-verify` 生成） |
| 修复 finding 来源 | 不消费 | 不消费；尾段直接报告收尾 | `score-results.json` 或 `agents/verifier-*.json`（完整资格检查） |

---

## 错误处理

各模式具体错误处理详见对应文件的"错误处理"小节：
- Fast：`scan-mode-fast.md > 错误处理`
- Light：`scan-mode-light.md > 错误处理`
- Deep：`scan-mode-deep.md > 错误处理`

通用兜底：
1. 基础探索失败 → 终止审计，提示用户重试
2. 编排器内联分析异常 → 基于已有 indexer findings 继续生成报告（Fast / Light 兜底；Deep 兜底见各 Agent 部分产物处理）
3. 字段漂移 → `normalize_finding_schema` 自动兜底，不阻断流程

---

## 模式对比

| 维度 | Fast（极速扫描） | Light（快速扫描） | Deep（深度扫描） |
|------|-----------------|------------------|-----------------|
| 定位 | Light + 执行纪律（并行 Read / 禁 sleep / 禁后台 Agent） | 标准轻量扫描 | 全语义索引深度扫描 |
| 探索 | 基础探索（Grep/Glob 强制并行，瘦身版） | 基础探索（Grep/Glob） | 基础探索 + 编排器写入索引 DB + indexer 语义索引（indexer-步骤2 AST + indexer-步骤3 LSP） |
| tree-sitter 检测与安装 | 跳过 | 跳过 | 检测 + 自动安装 |
| LSP | 跳过 | 跳过 | 探活 + 语义追踪 |
| AST 精化 | 跳过 | 跳过 | indexer-步骤2 双引擎，结果持久化到 SQLite |
| 扫描 | 编排器内联 + 内联校验合并 | 编排器内联 | vuln-scan + logic-scan + red-team 并行 |
| 验证 | 阶段 3 完全跳过（阶段 2 内联已完成） | 轻量验证 | 脚本验证（pre-check → chain-verify → challenge）+ verifier Agent + 脚本评分（score → quality） |
| 后台 Agent | 本期禁用（避免 sleep 轮询） | 允许（diff 启 light-scan） | 必须（三 Agent 并行）|
| WebSearch 情报增强 | 无 | 无 | 有（CVE 实时验证 + 0day 情报感知） |
| 置信度上限 | 90 | 90 | 100 |
| 自动修复 | 跳过 | 跳过 | 完整支持 |
| 预期耗时 | 3-12 分钟 | 5-58 分钟（抖动大） | 15-60 分钟 |
| 典型场景 | Git Hook / IDE 自动扫描 / CI 轻量门禁 | 日常快速自检 | 正式安全审计 / 发版前门禁 |
