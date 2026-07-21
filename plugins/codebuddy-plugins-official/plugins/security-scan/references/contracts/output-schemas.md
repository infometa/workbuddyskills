# 输出合约

> 引用方：所有 agent、commands/

---

## 风险发现 JSON 格式

按风险类型拆分，每种类型一个文件：`finding-{risk-type-slug}.json`。

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/resource/risk-type-taxonomy.yaml`（标准类型映射）

```json
{
  "metadata": {
    "fileName": "src/dao/UserDao.java",
    "timestamp": "ISO 8601",
    "auditBatchId": "{command}-{mode}-{timestamp}"
  },
  "summary": {
    "totalIssues": 2,
    "criticalRisk": 0, "highRisk": 1, "mediumRisk": 1, "lowRisk": 0
  },
  "findings": [
    {
      "findingId": "PL20260623201219-000",
      "filePath": "src/dao/UserDao.java",
      "lineNumber": 45,
      "riskType": "SQL 注入",
      "severity": "critical",
      "riskCode": "String sql = \"SELECT * FROM users WHERE id = \" + userId;",
      "confidence": 95,
      "description": "...",
      "recommendation": "...",
      "fixedCode": "...",
      "attackChain": {
        "source": "...",
        "propagation": ["..."],
        "sink": "...",
        "traceMethod": "LSP"
      },
      "traceMethod": "LSP",
      "sourceAgent": "vuln-scan",
      "verificationStatus": "verified",
      "auditedBy": ["vuln-scan", "verifier"]
    }
  ]
}
```

---

## Agent 输出必需字段

每个 agent 输出必须包含：
- `agent`: agent 名称
- `status`: completed / partial / failed
- `findings[]`: 发现列表
- `writeCount`: 写入次数
- `lastCheckpoint`: 最后检查点
- `_integrity`: { expectedFindingsCount, actualFindingsCount, allPhasesCompleted, lastWriteTimestamp }

### findings[] 中每个 finding 的字段规范

**统一字段命名：所有字段一律 camelCase，禁止 PascalCase 别名。** 下游脚本（merge_findings.py / verifier.py / generate_report.py）严格按以下字段名解析；任何旧字段（`FilePath`、`RiskType`、`RiskLevel`、`RiskCode`、`RiskConfidence`、`RiskDetail`、`Suggestions`、`FixedCode`、`riskLevel`、`riskConfidence`、`codeSnippet`、`exploitScenario`、`fixSuggestion`、`callPath` 等）一律拒绝并 fail-fast 报错。

**使用扁平字段，禁止嵌套 `location` 对象。**

#### 必填核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| findingId | string | 唯一风险编号，由 merge 阶段确定性生成，格式 `{前缀}-{NNN}`（如 `PL20260623201219-000`）；前缀按批次目录名 `{命令}-{模式}-{时间戳}` 推导：命令 project→P / diff→D，模式 light→L / deep→D / fast→F，序号从 000 起递增。Agent 产出时可留空 |
| filePath | string | 源文件相对路径（从项目根目录起） |
| lineNumber | int | 风险代码行号（单行号，非范围） |
| riskType | string | 风险类型：使用 `risk-type-taxonomy.yaml` 中的标准中文 `name`（如 "SQL 注入"）。禁止复合描述（如 "A / B"）和括号补充（如 "X (Y)"） |
| severity | string | 严重级别：critical / high / medium / low |
| riskCode | string | 风险代码片段（必须来自 Read 输出） |
| confidence | int | 置信度 0-100 |
| description | string | 风险描述（含 rationale / impact / 攻击叙事；logic-scan 的 exploitScenario 内容并入此字段） |
| recommendation | string | 修复建议（logic-scan 的 fixSuggestion 内容并入此字段） |
| attackChain | object | `{ source, propagation[], sink, traceMethod }`（logic-scan 的 callPath 并入此字段，见 agent-rules.md 第 3 节） |
| verificationStatus | string | unverified / verified / falsified（merge/verifier 阶段补齐） |
| sourceAgent | string | vuln-scan / logic-scan / red-team / verifier |
| traceMethod | string | LSP / Grep+Read / unknown |

#### 可选扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| fixedCode | string | 修复后代码 |
| severityRationale | string | 严重级别判定理由 |
| evidence | object/array | 证据片段、外部依据 |
| cwe | string | CWE 编号 |
| endpoint | string | HTTP/RPC 端点（logic-scan 常用） |
| missingDefenses | array | 缺失的防御措施 |
| auditDimension | string | 审计维度：C1-C10 |
| affectedFiles | array | 同 riskType 跨文件聚合 |
| auditedBy | array | 经手 agent 列表 |
| mergedId | string | 合并后的 ID |
| humanReviewRequired | bool | 是否需人工复核 |
| discoveryMethod | string | 发现路径 |
| riskTypeCN | string | 中文 riskType（备用） |
| poc | object | 攻击请求（PoC）可得性判定，见下方「poc 字段结构」。是外部可控性轴的工件化证据，直接驱动 severity 封顶 |
| comboClue | object | 组合攻击线索。聚焦模式（`focusMode=="high"`）时，若高危 finding 附近存在可组合达成高危场景的线索 Sink，挂载此字段。见下方「comboClue 字段结构」 |
| _focusExcludeReasons | array | 聚焦模式确定性过滤排除原因列表（内部字段，由 `verifier.py focus-filter` 写入）。仅出现在 `focus-excluded.json` 的 finding 中 |

#### poc 字段结构（攻击请求可得性）

用于回答「能否为该 finding 构造出一个具体、可复现的攻击请求 / 触发工件」。**造不出 PoC → severity 封顶 Medium（中危），并置 `humanReviewRequired: true`**（见 agent-rules.md §4.2）。

```jsonc
"poc": {
  "available": "yes | conditional | no",       // 能否构造出攻击请求；no→封顶 Medium
  "entryType": "http | intent | ipc | deeplink | mq | rpc | cli | deserialize | file | none",
  "reachability": "remote-direct | remote-conditional | local-only | none",
  "request": "POST /api/order?id=1 HTTP/1.1\nCookie: ...\n\n{\"price\":-1}", // 可复现工件：HTTP 请求 / Intent / IPC 调用 / MQ 消息 / 反序列化载荷等；可为多步序列
  "preconditions": ["需登录任意普通账号", "需诱导受害者点击"],         // 触发所需前置条件
  "evidenceRefs": ["endpoints: ctrl/Order.java:42 auth_type=none", "call_graph: A→B→sink"],
  "notObtainableReason": "sink 仅被内部定时任务调用，无任何外部入口可达"  // available=no 时必填
}
```

字段约定：
- **非 HTTP 入口同样合法**：客户端（Intent/IPC/deeplink）、后台（mq/rpc）、反序列化载荷、CLI 等均为有效 `entryType`，按其形态填 `request`，不得因「非 HTTP」而误判 `available=no`。
- `reachability` 与 `available` 的对应：`remote-direct`→`yes`（无前置直达）；`remote-conditional`→`yes/conditional`（需认证/上下文/二阶等前置）；`local-only`/间接→`conditional`；`none`→`no`。
- 供应链 / 凭据存在性类（malicious-package、vulnerable-dependency、hardcoded-secret、public-bucket、iam-overprivilege 等）**豁免** PoC 封顶：按存在性定级，`available` 可填 `conditional` 且不触发降级。

#### comboClue 字段结构（组合攻击线索）

聚焦模式下，当高危 finding 的同一文件/调用链上存在可组合达成高危场景的线索 Sink 时挂载。

```jsonc
"comboClue": {
  "clueType": "ssrf",                              // 线索风险类型 slug
  "clueLabel": "SSRF 指向内网服务",                  // 线索中文标签
  "clueFile": "internal/HttpClient.java",           // 线索所在文件
  "clueLine": 84,                                   // 线索行号
  "relation": "same-file | same-chain | same-endpoint",  // 与主 finding 的关系
  "comboScenario": "SSRF 可达内网 IMDS + 硬编码 AK/SK → 云资源接管"  // 组合攻击场景描述
}
```

> 组合线索不作为独立 finding 输出，而是挂载在高危 finding 的 `comboClue` 字段中。
> 线索类型定义见 `resource/high-focus-sinks.yaml > combo_clue_types`。

**禁止使用的格式**（会被 fail-fast 拦截）：
```json
// 错误：嵌套 location 对象
{ "location": { "file": "...", "startLine": 88 } }

// 错误：PascalCase 旧字段
{ "FilePath": "...", "LineNumber": 88, "RiskLevel": "high" }

// 正确：扁平 camelCase 字段
{ "filePath": "...", "lineNumber": 88, "severity": "high" }
```

> `normalize_finding()` 不再提供任何 alias / fallback。Agent 必须严格输出上表 camelCase 字段；任何遗漏或别名会在 `merge_findings.py` 的 `validate_finding_schema()` 处直接拒绝并指出问题来源。

---

## 输出目录结构

```
.codebuddy/security-scan/runs/{batch}/
  project-index.db              # 语义索引（SQLite）
  agents/
    indexer.json
    vuln-scan.json              # Deep 模式（vuln-scan Agent 产出）
    logic-scan.json             # Deep 模式（logic-scan Agent 产出）
    red-team.json               # Deep 模式（red-team Agent 产出）
    verifier-vuln.json          # Deep 模式（verifier 分片产出）
    verifier-logic.json         # Deep 模式（verifier 分片产出）
    verifier-redteam.json       # Deep 模式（verifier 分片产出）
    light-inline.json           # Light 模式
    remediation.json
  pre-check-results.json        # verifier.py pre-check 产出
  filtered-findings.json        # grade_verifiable findings
  filtered-findings-vuln.json   # verifier.py split 产出（vuln-scan findings）
  filtered-findings-logic.json  # verifier.py split 产出（logic-scan findings）
  filtered-findings-redteam.json # verifier.py split 产出（red-team findings）
  chain-verify-results.json     # verifier.py chain-verify 产出（攻击链索引验证）
  challenge-results.json        # verifier.py challenge 产出（确定性对抗审查）
  score-results.json            # verifier.py score 产出（确定性置信度评分）
  quality-assessment.json       # verifier.py quality 产出（确定性质量评估）
  stage1-context.json
  merged-scan.json
  merged-verified.json          # Deep 模式
  finding-{slug}.json
  summary.json
  security-scan-report.html
```

---

## summary.json

```json
{
  "batchId": "...",
  "command": "project | diff",
  "scanMode": "fast | light | deep",
  "totalFindings": 0,
  "criticalRisk": 0, "highRisk": 0, "mediumRisk": 0, "lowRisk": 0,
  "executionMetrics": {
    "lspStatus": "available | unavailable | skipped",
    "totalDuration": "120s"
  }
}
```
