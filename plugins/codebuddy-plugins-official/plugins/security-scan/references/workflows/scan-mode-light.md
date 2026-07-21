# Light 扫描模式（快速扫描）

> 引用方：commands/project.md、commands/diff.md
>
> **当 `scanMode == "light"` 时，仅 Read 本文件 + `scan-mode.md`（索引/对比）即可，无需加载 scan-mode-fast.md / scan-mode-deep.md。**

Light = 标准轻量扫描。编排器主窗口内联完成扫描与轻量验证，置信度上限 90。

---

## 阶段 0: 初始化

> 完整初始化流程：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md`

Light 模式与 Fast 在初始化阶段完全相同：
- 权限检查与配置（init-步骤1）：检查 + 自动修复
- 模式选择（init-步骤2）：交互选择
- tree-sitter（init-步骤3）：**整体跳过**
- LSP 探活与安装（init-步骤4）：**整体跳过**
- 环境就绪确认（init-步骤5）：直接输出就绪信息（无 pendingActions）

---

## 阶段 1: 探索

编排器内快速完成基础探索（Grep/Glob，不启动 Agent）：

1. 文件枚举 + 技术栈识别
2. Sink 粗定位、凭证/密钥检测、配置基线、CVE 扫描

> 与 Fast 模式的差异：Light 不调用 `pattern_grep.py` 前置脚本预筛，也不做文件内批量三判；沿用既有 LLM Grep/Glob + Read 流程。
>
> 重要：Light 下 `sink-patterns.yaml` / `pattern_grep.py` 中的 `SINK_SEVERITY` 不会自动生效。Light 应先按代码语义识别是否存在云产品对象操作、CAM 鉴权或 CI 内部转发链路；只有语义相关时，才进入下列 COS/万象 STS 专项确认。

### 腾讯云 COS/万象 STS 语义触发检查（Light 条件执行）

Light 不对所有项目强制检查 STS。仅当基础探索或代码语义满足任一条件时执行专项确认：
- 存在 COS/CI/CAM 相关模块、配置或域名（如 `cam_auth`、`pic_process`、`qcloud`、`myqcloud`、`tencentci`）
- 当前分析的入口/调用链涉及对象上传、下载、删除、持久化处理、图片处理或 coscgi→万象转发
- 代码中出现 CAM 鉴权构造、内部签名、临时凭证或对象 Key 语义

高信号确认探针（语义相关后才 Grep；任一命中再 Read 上下文）：
- `logic\.cam\.sigAndAuth|ModeOnlyAuth|q-token|HTTP_X_CI_SECURITY_TOKEN|HTTP_X_COS_SECURITY_TOKEN`
- `X-CI-SIGN|GenerateCiKey`
- `putObject|uploadFile|sliceUploadFile|deleteObject|getObject|getSignedUrl|ciProcess|ImageProcess|imageMogr2`

上下文证据探针（仅用于命中文件的二次判断，不单独报风险）：
- `ownerUin|ownerAppid|CIArgs|user_info|coscgi|CosCgi|CI_S3_|pic_process`
- `key|fileName|filename|filePath|path|prefix|objectKey`

命中高信号探针后 Read 命中文件上下文，按下述**四问**判定 `COS/万象 STS 鉴权缺失`。若当前扫描上下文已进入 COS/CI/CAM 语义场景，不得只依赖 `sinks-by-severity` 是否返回该类 Sink；若语义不相关，则不执行本专项。

> **CAM/COS Sink 五问（Light 内联判定，对应 `sts_authorization_check` + `auth_element_completeness_check` 共享信号库）**
> 1. **isCloudResourceSink**：是否命中 `cos_object_op` / `ci_internal_forward` / `cam_sig_auth` 三类 sink 之一？
> 2. **isControllableDescriptor**：sink ±15 行窗口内是否同时出现 `controllable_signals.param_names`（key/fileName/path/prefix/...）与 `source_markers`（HTTP_/REQUEST_/req./@RequestParam/...）？
> 3. **isBranchStsMissing**：sink 所在 if/switch 分支内是否**缺失** `sts_signals.defense_keywords`（q-token/AssumeRole/x-cos-security-token/sessionToken/...）？仅在函数其它分支出现 STS 关键字**不足以反驳**当前分支的缺失。
> 4. **isResourceScopeMissing**：窗口内是否**缺失** `sts_signals.resource_scope_patterns`（`qcs::cos:.*:prefix/...` 或按 `uid/uin/tenant/business` 收敛）？同文件出现 `defense_config_families`（`cam_tmp_token_auth.` / `sts.` / `tmp_token.` ...）只能视为辅助参考，不能替代分支级判定。
> 5. **isAuthElementIncomplete**：sink 所在分支是否触发「签名材料缺失身份/资源字段」？需同时满足：(a) 分支或窗口内出现 `auth_element_signals.signature_func_keywords`（CalcSign/HmacSha256/MD5Hex/verifySign/...）；(b) 窗口内 `required_identity_fields`（ownerUin/sub_uin/ownerAppid/Host/bucket/region）与 `request_header_sources`（X-COS-CI-ARGS / base64_decode / ParseFromArray / getHeader / ...）共现；(c) 分支内**未**出现 `auth_element_signals.defense_keywords` 或 `signed_material_keywords` 与身份字段共现。三条同时满足 → yes。
>
> 第 1-4 问全 yes → 输出 `riskType: "COS/万象 STS 鉴权缺失"`；第 5 问 yes（无论 3/4 结果） → 额外输出 `riskType: "认证要素缺失"`，`sourceAgent: "light-inline"`，`riskConfidence` 上限 90。两条 finding 在同位置 ±5 行内时，由 §1.5.5 dedup 规则收敛（保留 `auth-element-incomplete`，因其严重程度通常高于 STS 缺失）。任一前 4 问为 no 且第 5 问也 no（窗口内确认存在 STS 防御 + 签名材料完整）→ 不报。

---

## 阶段 1.5: 业务场景识别与策略选择（Light 专属）

> Light 专属阶段。Fast / Deep 不消费 `scenarios` / `lightScenarioRules` 字段；
> 当 `scenarios == ["web"]` 时本阶段 NO-OP，与旧版本 Light 行为一致。

### 1.5.1 触发场景检测

Light 的产品形态结论来自阶段 1 的 Agent 直接分析，**不得**在本阶段调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type` 重新判定。

输入字段：
- `project_type` / `product_shape`：只能是 `客户端` / `AI agent` / `web` / `数据库` / `未知`
- `project_type_code`：只能是 `client` / `ai_agent` / `web` / `database` / `unknown`
- `product_shape_decision` / `product_shape_evidence_chain`：产品形态判定说明、依据与真实文件证据链

场景检测由 Agent 基于产品形态、技术栈和实际攻击面语义内联判断，不写成产品形态结论：
- `AI agent` 且 evidence 同时证明 LLM 能力与工具/编排能力 → 可启用 `ai_agent_app` 场景
- `web` 且存在 HTTP/Web 入口 → 使用 baseline `web` 场景
- `客户端` 且存在端侧 WebView/IPC/导出组件/证书校验等攻击面 → 可启用客户端相关问答集
- `数据库` 仅表示产品形态，不等于自动存在 SQL 注入；仍需按真实入口与 Sink 判断

输出新增字段：
- `scenarios`：按置信度降序的场景列表（最多 3 项），可能取值
  `web` / `cloud_native_service` / `ai_agent_app` / `sandbox_runtime` / `business_payment` / `mixed`
- `scenarioConfidence`：每个场景的置信度（0-100）
- `auditStrategy.knowledge_files`：场景触发的知识 yaml 列表
- `auditStrategy.lightScenarioRules[]`：每场景的问答集 + per-file finding 上限 + per-scenario 文件预算

仅当 `scenarios` 含 `web` 以外的场景时，按下文 1.5.3~1.5.6 加载对应问答集；
任一 yaml `Read` 失败 → 跳过该场景，写 `agents/light-inline.json > _scenarioErrors[]`，**不中断扫描**。

### 1.5.2 场景 → 规则集映射

| 场景 | 加载知识 yaml | Light 问答集 | 备注 |
|---|---|---|---|
| `web` | （无新增） | （走既有 Sink 优先级） | baseline，沿用现有路径 |
| `cloud_native_service` | `tencent-cloud-security.yaml` | 1.5.5 四问（IMDS / IAM 通配 / 公开桶 / STS 临时密钥策略过宽） | 与现有 COS/万象 STS 四问 dedup |
| `ai_agent_app` | `ai-agent-security.yaml` | 1.5.3 四问 | per-file ≤ 2 finding |
| `sandbox_runtime` | `sandbox-escape-patterns.yaml` | 1.5.4 五问 | per-file ≤ 2 finding |
| `business_payment` | `payment-logic-rules.yaml` | 1.5.6 三问 | per-file ≤ 1 finding |

### 1.5.3 AI Agent 四问（场景 `ai_agent_app`）

> 引用：`resource/knowledge/ai-agent-security.yaml`

按文件维度执行（命中 `tool_execution_signals.registration_patterns` 或 `prompt_injection_signals.prompt_construction` 的文件）：

1. **isToolBoundToAgent**：当前文件是否注册了工具集合到 Agent（命中 `tools=[` / `@tool` / `bind_tools(` / `AgentExecutor(` / `create_react_agent`）？
2. **isLLMOutputUnconstrained**：LLM 输出是否未走 pydantic / jsonschema / StructuredOutputParser / safe_eval / `output_parser.parse`？
3. **isToolDangerous**：注册的工具名是否命中 `dangerous_tool_names`（shell_exec/run_python/sql_execute/http_get/fs_write/...）？
4. **isOutputSinkUnsafe**：LLM 输出是否进入 `agent_output_sink_signals.dangerous_sinks`（exec/eval/innerHTML/`cursor.execute(f"")` / `db.query(\``）？

判定矩阵（以二元组 `(isToolBoundToAgent, isLLMOutputUnconstrained, isToolDangerous, isOutputSinkUnsafe)` 表示，命中即输出）：

| isToolBoundToAgent | isToolDangerous | 缺 `allowed_tools` / `HumanInputRun` | → 输出 |
|---|---|---|---|
| yes | yes | yes | `riskType: "工具执行无约束"`（severity critical） |
| yes | yes | no（已防御） | 不报 |
| yes | no | — | 视 isLLMOutputUnconstrained 与 isOutputSinkUnsafe |
| isLLMOutputUnconstrained=yes & isOutputSinkUnsafe=yes | — | — | `riskType: "Agent 输出未校验"`（severity high） |
| `prompt_construction` 命中 + 不可信 source 命中 + 缺 `defense_keywords` | — | — | `riskType: "提示词注入"`（severity high） |
| `mcp_trust_signals.untrusted_server` 命中 + 缺 `defense_keywords` | — | — | `riskType: "MCP 服务信任失控"`（severity high） |
| `system_prompt_leak_signals.hardcoded_secret_in_prompt` 命中 | — | — | `riskType: "模型凭证泄露"`（severity high） |

`sourceAgent: "light-inline"`（diff 模式 `light-scan`），`riskConfidence` 上限 90。每文件至多 2 个 finding，超出标 `analysisDepth: queued`。

### 1.5.4 沙箱五问（场景 `sandbox_runtime`）

> 引用：`resource/knowledge/sandbox-escape-patterns.yaml`

针对命中 `nodejs_vm_signals.vm_apis` / `python_sandbox_signals.exec_apis` / `container_runtime_signals` / `seccomp_signals` / `wasi_signals` 的文件执行：

1. **isUserInputReachable**：用户输入（`request.*` / `req.body` / `ctx.request.body` / cli args）是否到达 `eval`/`exec`/`vm.runInContext`/`new Function`？
2. **isContextWeak**：vm 上下文是否暴露 `this.constructor.constructor` / `process.binding` / `require('child_process')`，或 Python exec 是否能走 `().__class__.__bases__` / `__subclasses__()` 链？
3. **isCapDangerous**（仅容器/k8s yaml）：是否含 `privileged: true` / `CAP_SYS_ADMIN` / `hostPath: "/"` / `docker.sock` / `hostPID` / `hostNetwork`？
4. **isSeccompMissing**：是否 `seccompProfile.type=Unconfined` 或自定义 profile 允许 ptrace/keyctl/userfaultfd/unshare/setns？
5. **isWasiOverPermissive**：WASI 是否 `preopen("./" / "/")` / `inherit_stdio` / `inherit_env`？

输出：
- `(isUserInputReachable, isContextWeak)` 全 yes → `Node VM 上下文绕过` / `Python 沙箱绕过` / `用户输入直入代码执行`（按命中的 vm/exec API 选 slug）
- `isCapDangerous=yes` → `容器逃逸`（severity critical）
- `isSeccompMissing=yes` → `seccomp 策略绕过`（severity high）
- `isWasiOverPermissive=yes` → `WASI 逃逸`（severity high）

存在对应 `defense_keywords`（vm2/isolated-vm/RestrictedPython/`runAsNonRoot: true`/`RuntimeDefault`）→ 不报。`sourceAgent` 同 1.5.3。每文件至多 2 个 finding。

### 1.5.5 云原生四问增量（场景 `cloud_native_service`）

> 引用：`resource/knowledge/tencent-cloud-security.yaml`

在现有 COS/万象 STS 四问之上追加：

1. **isImdsReachable**：SSRF / fetch 路径是否可达 `169.254.169.254` / `metadata.tencentyun.com` / `100.100.100.200`？
2. **isIamWildcard**：CAM/IAM 策略是否 `Action: "*"` 或 `Resource: "*"`，且未限定 condition / principal？
3. **isPublicBucket**：COS/S3/OSS 是否 `public-read` / `public-read-write` / Bucket Policy 允许匿名 ListBucket / GetObject？
4. **isStsPolicyOverprivilege**（对应知识块 `cos_security.sts_temp_policy_overprivilege_check`，`riskType: "COS 临时密钥策略过宽"`，severity high）：服务端**确实在签发 STS 临时密钥**（命中 `sts_issue_signals.policy_build_keywords`：`GetCredential` / `CredentialPolicy` / `CredentialPolicyStatement` / `CredentialOptions` / `AssumeRole` / `GetFederationToken` / `buildResource` / `buildStatement`），但某条 `Effect=allow` 的 Statement 同时满足：
   - **Resource 过宽**：命中 `arbitrary_object_overwrite.wildcard_resource_patterns`（`resource="*"`，或收敛到桶级 `.../{bucket}/*` 而非具体对象 / 用户前缀）；或仅收敛到目录级 `.../{bucket}/目录/*`（命中 `directory_level_overwrite.resource_patterns`，按文档降级为 medium）；
   - **且 Action 含写 / 高危**：命中 `arbitrary_object_overwrite.action_patterns`（PutObject / PostObject / 分块上传），或 `high_risk_action_grant.high_risk_actions`（PutBucketACL / DeleteBucket / PutBucketPolicy 等桶级），或 `full_action_grant.action_patterns`（`action="*"` / `cos:*` → severity critical）；
   - **且用户可控的 Key / 前缀拼入 Resource 前未做通配符过滤与归属收敛**：命中 `sts_issue_signals.user_controlled_key_into_resource`，且分支内未显式拒绝 `*` / `?` / `..`，未把前缀绑定到服务端可信派生的 `<appid>/<userId>/`。
   - 满足 `false_positive_reduction` 任一项（Resource 已收敛到可信用户前缀 + 读类 Action / 带 cos:prefix·ip·短有效期 condition / 仅离线运维固定 Key / Resource 为结尾非 `*` 的具体对象 / test_·example_·tools 目录）→ 不报或降级。

> **第 4 问与既有「COS/万象 STS 鉴权缺失」四问正交**：既有四问查的是「面向用户的对象操作**根本没走 STS**（缺临时凭证）」；第 4 问查的是「**确实在签发 STS，但下发的临时策略本身过宽**（Resource 通配 + 写/高危 Action）」。二者可在同一项目不同代码点分别命中，互不替代。

判定输出：第 4 问命中 → `riskType: "COS 临时密钥策略过宽"`，`severity` 按上文（桶级通配 + 写 = high；目录级 = medium；`action=*`/`cos:*` = critical），`sourceAgent: "light-inline"`，`riskConfidence` 上限 90。

第 1-3 问每文件至多 1 个 finding，`severity ≤ medium`；第 4 问每文件至多 1 个 finding（severity 不封顶 medium，按命中场景定级）。

**Dedup 规则**（强制）：
- 当同文件同位置 ±5 行内已存在 `cos-sts-missing` finding 时，**不再输出** `iam-overprivilege` / `public-bucket`（避免与既有四问重复）
- `cloud-imds` 与 STS 四问正交，**不 dedup**
- 当同文件同位置 ±5 行内同时存在 `cos-sts-missing` 与 `auth-element-incomplete` 时，**保留 `auth-element-incomplete`**（更高优先级，签名身份/资源未绑定通常蕴含跨租户 IDOR 风险），dismiss `cos-sts-missing`
- **`cos-sts-policy-overprivilege`（第 4 问）与 `cos-sts-missing` 正交，不 dedup**：前者要求「已签发 STS」，后者要求「未签发 STS」，二者互斥，同位置不会同真；若 LLM 误在同位置同时产出两者，保留 `cos-sts-policy-overprivilege`（已确认存在 STS 签发链路，证据更具体）

### 1.5.6 支付三问（场景 `business_payment`）

> 引用：`resource/knowledge/payment-logic-rules.yaml`

1. **isPriceFromClient**：金额/价格是否来自客户端请求未做服务端价格表二次校验？
2. **isIdempotencyKeyMissing**：支付/扣款接口是否缺幂等键（`idempotency_key` / `out_trade_no` 唯一约束）？
3. **isCallbackUnsigned**：异步通知（`notify_url` / 回调）是否缺签名校验或未校验来源 IP？

每文件至多 1 个 finding。`sourceAgent` 同 1.5.3。

### 1.5.7 置信度与硬上限

- `scenarioConfidence ≥ 60` 才入选；同时活跃场景上限 `SCENARIO_MAX_ACTIVE = 3`
- 任一 yaml `Read` 失败 → 降级跳过该场景，写入 `agents/light-inline.json > _scenarioErrors[]`，不中断扫描
- 每场景文件预算 ≤ 50（按场景信号命中文件优先），超出标 `analysisDepth: queued`
- 跨场景同文件命中：每文件总 finding 上限取所有命中场景中的 `max_findings_per_file` 之和，封顶 4

---

## 阶段 2: 扫描（编排器内联扫描）

不启动独立 Agent（diff 模式例外，启用 light-scan Agent；project 模式始终内联）。编排器在主窗口内执行：

### 1. 导出 indexer findings（密钥/配置/CVE）

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset indexer-findings
```

### 2. Sink 风险评估

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset sinks-by-severity --limit 30
```

`index_db` 结果只作为已有索引候选；Light 不依赖 `pattern_grep.py`。若阶段 1 语义触发了 COS/万象 STS 专项确认，则阶段 2 同步消费该确认结果。

对 S1（critical 优先级）Sink 执行轻量分析；已语义触发并命中的云产品鉴权类 Sink（如 `COS/万象 STS 鉴权缺失`）在 Light 中按高优先级处理：
- Read Sink 所在代码上下文（+/-20 行）
- 检查是否存在直接防御（参数化查询、白名单、编码、STS 临时凭证、按用户/业务前缀收敛的临时策略等）
- COS/万象对象操作若接收用户补充的 `key/fileName/path/prefix` 等对象 Key，且上下文没有 `AssumeRole/GetFederationToken/qcloud-cos-sts/sessionToken/x-cos-security-token`，输出 `riskType: "COS/万象 STS 鉴权缺失"`
- coscgi→万象内部转发若仅有 `X-CI-SIGN/GenerateCiKey` 内部签名 + `uin/ownerUin/ownerAppid` 账号鉴权，未在当前处理分支传递 `q-token/sessionToken`，同样输出该风险
- 产出 finding（`sourceAgent: "light-inline"`，`confidence` 上限 90）

### 3. 合并结果

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/merge_findings.py" merge-scan \
  --batch-dir "$batch_dir" \
  --extra-agents indexer-findings,light-inline
```

> **diff 模式 Light 扫描注意**：diff 命令的 Light 模式启动 `light-scan` Agent（而非 project 的 `light-inline` 内联），合并时必须指定 `--extra-agents light-scan`。merge-scan 脚本也有兼容兜底：即使编排器遗漏 `--extra-agents`，脚本会自动发现 `agents/light-scan.json` 并加载。

---

## 阶段 3: 验证

仅验证 Critical + High，编排器内联验证（代码存在性 + 基础防御检查），置信度上限 90。

> 完整验证策略：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/verification.md`

---

## 阶段 4: 报告与收尾

| 维度 | Light |
|------|------|
| 自动修复 | **跳过**（不修改用户代码；不弹修复确认） |
| 报告生成输入 | `merged-scan.json`（无 `finding-*.json`，`generate_report.py` 自动 fallback） |
| 修复 finding 来源 | 不消费；Light 尾段不执行自动修复 |
| 下一步操作 | **跳过**；必须直接生成 HTML 报告、执行门禁评估/通知、输出报告路径与审计摘要后结束 |

Light 模式禁止在尾段询问“生成 HTML 详细报告 / 结束审计”或“预览报告 / 结束审计”。报告生成是必做步骤，不是用户选项。

---

## 错误处理

1. 基础探索失败 → 终止审计，提示用户重试
2. 编排器内联分析异常 → 基于已有 indexer findings 继续生成报告

---

## 聚焦模式（`focusMode == "high"` 时生效）

> 聚焦模式完整流程见 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/focus-mode.md`。
> 本节仅列出 Light 模式下的差异化行为。

### 阶段2扫描：Sink 过滤

聚焦模式下，阶段2仅分析 S1(critical) + S2(high) 级别的 Sink：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset sinks-by-severity --limit 30
```

编排器在拿到结果后，**手动过滤**仅保留 `severity_level 1`（S1）和 `severity_level 2`（S2）的 Sink，
跳过 S3/S4。

聚焦模式下 LLM 内联扫描：
- **仅分析 S1/S2 级别的 Sink**
- 对每个高危 Sink，检查 ±30 行上下文是否存在组合线索 Sink
  （按 `high-focus-sinks.yaml > combo_clue_types` 匹配：SSRF/路径穿越/访问控制缺失/文件上传/信息泄露）
- 若存在组合线索，在高危 finding 追加 `comboClue` 字段

### 阶段3验证：信号匹配三问

编排器内联验证时，对每个 Critical/High finding 按 `focus-mode.md > 信号速查表` 回答三问：
1. 公网可达？（Grep 入口注解/IP白名单/来源校验/触发方式）
2. 可直接利用？（Grep 认证/鉴权/CSRF/MFA）
3. 危害过高？（Grep DB权限/容器限制/命令范围/数据范围）

任一信号命中导致降级 → severity 降级。不确定 → 降级 medium → 由后续 focus-filter 排除。

### 阶段3末尾：确定性过滤

merge-verify 完成后，**必须**执行：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" focus-filter \
  --batch-dir "$batch_dir"
```

### 阶段4报告：聚焦过滤后产物

使用 focus-filter 后的 `merged-verified.json` 生成报告。`summary.json` 中 `mediumRisk` / `lowRisk` 为 0，
新增 `focusFiltered` 字段记录排除数量。
