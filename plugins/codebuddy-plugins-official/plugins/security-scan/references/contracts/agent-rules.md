# Agent 通用规则

> 引用方：所有 agent

---

## 1. 反幻觉约束

**宁可漏报也不误报**。filePath/riskCode 必须来自工具输出（Grep/Read/Glob/LSP），防御搜索是强制前置步骤。

**必须 Read** 完整合约文件获取具体规则条目（共 5 条硬规则）：
`${CODEBUDDY_PLUGIN_ROOT}/resource/anti-hallucination-rules.yaml`

## 2. 增量写入

**任何已完成的分析结果必须在 3 个工具调用周期内写入磁盘。**

### 写入触发条件（满足任一）

1. 完成一个完整 finding
2. 完成一个 Phase / 子任务
3. 累积未写入数据超过 2000 tokens
4. 连续 10 次工具调用未写入

### 写入方式

> ⚠️ **严格使用 Read/Write 工具操作 Agent JSON 输出文件。禁止使用 `python3 -c` 读写 JSON 文件。**

1. **Read** 工具读取当前输出文件（获取已有 findings + writeCount）
2. 在 LLM 内部合并新 findings 到已有数据
3. **Write** 工具写入完整 JSON（覆盖写入）
4. 确保更新 `meta.status`、`meta.lastCheckpoint`、`meta.writeCount`

**工具选择规则**：
- 读文件 → **Read 工具**（免授权，直接读取文件内容）
- 写文件 → **Write 工具**（白名单已覆盖 `.codebuddy/security-scan/runs/*`）
- 查数据库 → **`index_db.py query`**（preset 或自定义 SQL）
- **禁止**用 `python3 -c` 做文件读写 — 这不是数据处理，是工具层已覆盖的基础操作

### 恢复协议

Agent 启动时检查输出文件：
- 已存在且 `status != "completed"` -> 从 `lastCheckpoint` 继续
- 不存在 -> 从头开始

### 各 Agent 写入节奏

| Agent | 写入时机 |
|-------|---------|
| indexer | indexer-步骤1 完成后批量写入（indexer-1.写入）；indexer-步骤2 每完成一个子步骤增量写入；indexer-步骤3 每完成一个子步骤增量写入 |
| vuln-scan | 第 1 个 finding 后立即写入；之后每完成 1 个追加 |
| logic-scan | 第 1 个 finding 后立即写入；之后每完成 1 个追加 |
| red-team | 第 1 个 finding 后立即写入；之后每完成 1 个追加 |
| verifier | 第 1 个 finding 验证后立即写入；之后每完成 1 个追加 |

### 资源预算

真正的硬约束是 `max_turns`（Task 工具参数），插件层面无法改变。Agent 只需遵循以下简单规则：

1. **立即写入，禁止积攒** — 每完成一个 finding 立即追加写入
2. **预算紧张时保结果** — 感觉快到限制时，停止新探索，写入已完成结果
3. **设置正确的退出状态** — 全部完成 `completed`，未完成 `partial`（含 `earlyTermination`）

LSP 结果复用：同一方法的 incomingCalls/outgoingCalls 结果在本次审计中有效，不重复调用。

收尾模式触发条件（任一）：
1. 输出被截断
2. 当前 turn 数接近 max_turns（剩余 <= 2 turns）

收尾动作：停止新探索 -> 写入已完成结果 -> 设置 status（`completed` 或 `partial`）

### 增量写入实现模板

Agent 使用 `_common.py` 提供的辅助函数完成增量写入。以下为标准流程：

**1. 启动时初始化输出文件**

```python
# Agent 启动后立即执行（步骤0 加载索引之前）
existing, checkpoint = init_agent_output(output_path, 'vuln-scan')
if existing:
    # 续扫模式：从 checkpoint 继续，跳过已完成的 findings
    completed_ids = {f.get('findingId') for f in existing.get('findings', [])}
```

**2. 每完成一个 finding 后立即追加**

```python
# 完成一个 finding 后立即写入（禁止积攒）
finding = { "filePath": "...", "lineNumber": 42, "riskType": "...", "severity": "high", "riskCode": "...", "confidence": 90, "description": "...", "recommendation": "...", "attackChain": {"source": "...", "propagation": [], "sink": "...", "traceMethod": "LSP"}, "traceMethod": "LSP", "sourceAgent": "vuln-scan" }
incremental_write_findings(
    path=output_path,
    new_findings=[finding],
    agent_name='vuln-scan',
    checkpoint='sink-3',      # 当前进度标识
    status='partial',         # 尚未全部完成
)
```

**3. 全部完成后标记 completed**

```python
# 最后一个 finding 写入时设置 status='completed'
incremental_write_findings(
    path=output_path,
    new_findings=[last_finding],
    agent_name='vuln-scan',
    checkpoint='done',
    status='completed',
)
```

**关键要求：**
- `write_json_file()` 使用 temp + rename 原子操作，中途崩溃不会损坏文件
- 并发读取者始终看到完整有效的 JSON
- Agent 超时后，已写入的 findings 会被 merge_findings.py 正常处理

## 3. 攻击链合约

所有 finding 必须包含 `attackChain`：

```json
{
  "source": "entry point or user input",
  "propagation": ["intermediate call 1", "call 2"],
  "sink": "dangerous operation",
  "traceMethod": "LSP | Grep+Read | unknown"
}
```

## 4. 严重级别规则

四级：**Critical(严重) > High(高危) > Medium(中危) > Low(低危)**。

### 4.0 判定逻辑（权威定义 / 必须严格遵守）

> 所有 agent 输出 `severity` 时**必须**严格按下表判定；验证环节由确定性脚本（`verifier.py challenge`）对照本定义校验合规性。
>
> 定级由**两个维度共同决定**：①**危害维度**（造成什么后果）②**外部可控性维度**（攻击者能否、以及多容易让恶意输入到达触发点 / Sink）。**两轴取严（就低）**：最终级别不得超过外部可控性维度允许的上限；两轴结论冲突时，取更低的一级。

| 级别 | ① 危害维度 | ② 外部可控性维度（封顶轴） |
|------|----------|----------|
| **严重 Critical** | 可直接造成入侵、以及可直接获取大量敏感信息的漏洞 | **可直接远程**：无需任何前置条件，外部 / 公网输入直达触发点（如未认证入口的参数 / body / URL 直入危险操作） |
| **高危 High** | 可直接造成入侵、可直接获取大量敏感信息、造成权限提升、造成资金损失的逻辑漏洞 | **可直接远程，或经其他方式可外部可控**：需认证 / 特定上下文 / 二阶（先落库再触发）/ 跨组件 / 诱导用户等前置条件后，外部输入仍可到达触发点 |
| **中危 Medium** | 有助于造成入侵和数据泄漏的漏洞、凭据泄漏、配置不当 | **经其他方式可外部可控，或本身外部不可控但可被纳入攻击链**（贡献性） |
| **低危 Low** | 无法直接利用、属于线索级别的问题 | **外部不可控**：source 完全由内部产生（常量 / 配置 / 随机 / 系统值），攻击者无任何途径影响触发点 |

**分水岭口诀（用于消歧）：**
- **Critical ↔ High**：差异在「**远程 + 直接**」与「**可控性是否需要前置条件**」。无需任何前置条件即可远程直接 RCE / 直接远程拖库 → **Critical**；需要认证 / 特定上下文 / 本地条件方可直接利用，或仅经其他方式（间接）外部可控 → **High**。
- **High ↔ Medium**：差异在「**能否直接造成危害**」且「**是否仍具外部可控性**」。本身即可直接入侵 / 直接拖库 / 直接提权 / 直接造成资金损失，且外部（含间接方式）可控 → **High**；本身不可直接利用、仅**有助于**（贡献于）入侵或数据泄漏、或仅是凭据泄漏 / 配置不当 → **Medium**。
- **Medium ↔ Low**：差异在「**是否外部可控 / 是否可利用**」。外部不可控但仍可被纳入攻击链发挥作用 → **Medium**；**外部完全不可控**且仅是线索 / 辅助信息、无法纳入任何攻击链 → **Low**。

**外部可控性封顶（强约束，覆盖危害维度的拔高冲动）：**
- source 完全内部产生、攻击者无任何途径影响触发点 → **封顶 Low**，任何危害描述都不得拔高。
- 仅在需要极强前置、或仅间接外部可控、且危害为贡献性 → **封顶 Medium**。
- 需前置条件（认证 / 上下文 / 二阶 / 跨组件等）方可外部可控 → **封顶 High**，不得标 Critical。
- 仅当**可直接远程**（无任何前置条件）→ 方可达 **Critical**。

**外部可控性的工件化证据 —— 攻击请求（PoC）可得性（落地判据）：**

「能否为该 finding 构造出一个具体、可复现的攻击请求 / 触发工件（PoC）」是外部可控性最强、最工件化的证据。每个 finding **应产出 `poc` 字段**（结构见 `output-schemas.md > poc 字段结构`），并据此做封顶校准：

| `poc.available` / `reachability` | 外部可控性结论 | severity 上限 |
|------|------|------|
| `available=yes` 且 `remote-direct`（无任何前置、公网输入直达 Sink） | 可直接远程 | 可达 **Critical** |
| `available=yes/conditional` 且 `remote-conditional`（需认证 / 上下文 / 二阶 / 跨组件 / 诱导等前置） | 经其他方式可外部可控 | 封顶 **High** |
| `available=conditional` 且仅 `local-only` / 间接 | 间接可控 | 封顶 **Medium** |
| `available=no`（无法构造出任何攻击请求 / 触发工件） | 实质外部不可控 | **封顶 Medium（中危）**，并置 `humanReviewRequired: true` |

> **造不出攻击请求 → 封顶中危**：扫描期构造不出可复现 PoC，不等于绝对不可控（索引可能不全），故采取保守口径——**封顶 Medium 并标人工复核**，而非直接归零 Low。`available=no` 时必须在 `poc.notObtainableReason` 写明造不出的原因。
> 非 HTTP 工件（Intent/IPC/deeplink/MQ/RPC/反序列化载荷/CLI）均为合法 PoC 形态，不得因「非 Web」而误判 `available=no`。
> 豁免：供应链类（malicious-package / vulnerable-dependency / typosquatting）、凭据/配置存在性类（hardcoded-secret / AKSK 泄漏 / public-bucket / iam-overprivilege）按存在性定级，不受 PoC 封顶约束。

### 4.1 各级别典型场景（映射到 risk-type-taxonomy.yaml）

#### Critical（严重）— 可直接远程入侵 / 可直接远程获取大量敏感信息
- 无认证直接 RCE：命令注入、代码执行、反序列化、JNDI 注入、SSTI、表达式注入、用户输入直入代码执行
- 沙箱 / 容器逃逸（直接获得宿主控制权）
- 已知恶意 / 投毒依赖包（malicious-package）
- 在野被积极利用的 CVE（存在公开 PoC，列入 CISA KEV）
- 无认证即可远程拖库 / 批量导出全量敏感数据（如公网零鉴权的 SQL 注入直接 dump 整库）

#### High（高危）— 可直接入侵 / 可直接获取大量敏感信息 / 权限提升 / 资金损失逻辑
- SQL 注入 / NoSQL 注入（可导致大量数据泄漏）
- 认证绕过（auth-bypass，可直接获取未授权访问）
- 直接造成权限提升的漏洞（垂直越权拿到管理员权限、提权到高权角色）
- 直接造成资金损失的业务 / 支付逻辑漏洞（价格篡改、退款滥用、余额溢出）
- 腾讯云 AKSK / 可直接调云 API 的生产密钥泄漏
- 面向用户的 COS / 数据万象对象操作接口：用户可控 `key/fileName/path/prefix` 等对象 Key，且未配置 STS 临时凭证或按前缀收敛的临时策略
- 可 RCE 的调试端点暴露（如 Flask Debugger、Node.js Debug 端口、Jolokia）
- 可导致大量内存数据泄漏的端点（如 heapdump）

#### Medium（中危）— 有助于入侵 / 数据泄漏（贡献性）、凭据泄漏、配置不当
- SSRF、路径穿越、XXE、XSS、CSRF、IDOR、文件上传（需上下文或链式利用）
- LDAP 注入、访问控制缺陷、明文密码、JWT 问题
- 凭据泄漏：硬编码凭证 / 后门（hardcoded-secret）、模型 / API 密钥泄漏（非可直接调云 API 的生产密钥）
- 各类端点暴露（Actuator、pprof、phpinfo 等）
- DoS 类（ReDoS、XML 炸弹、Zip 炸弹）
- 前端安全问题（PostMessage、CORS 反射、WebSocket 劫持）
- 敏感数据日志泄露、依赖混淆
- 配置不当：一般云安全配置问题（CAM/IAM 策略过宽、COS/S3 公开存储桶、云函数无认证；用户可控 COS/万象对象 Key 且缺 STS 按 High 处理）

#### Low（低危）— 无法直接利用 / 线索级
- 信息泄露（版本号 / 路径 / 堆栈，无敏感数据）、不安全配置（DEBUG=True、autoindex）
- 弱加密、弱密码哈希、弱随机数、缺少安全头
- CSV 注入、审计缺失、暴力破解防护缺失、会话固定、Cookie 属性缺失
- Swagger/GraphQL 暴露、CSRF 禁用、CORS 配置问题
- 日志注入、缺少锁定文件

### 4.2 确定性升级 / 降级规则（脚本强制执行）

1. **基线优先**：每个 riskType 以 `risk-type-taxonomy.yaml` 中对应 slug 的 `severity_default` 为基线，不得凭直觉打分。
2. **越级需理由且最多 +1 档**：仅当存在**直接、具体、已验证**的攻击路径时，才允许在 `severity_default` 基础上**最多上调 1 档**，且必须在 `severityRationale` 字段写出具体证据。
   - 越级且无 `severityRationale` → 强制回落到 `severity_default`。
   - 越级超过 +1 档（即便有 `severityRationale`）→ 上限收敛到 `severity_default + 1`。
3. **线索级不得拔高**：弱加密 / 弱密码哈希 / 弱随机 / 信息泄露等 `severity_default = low` 的「线索级」类型，最高只能到 Medium（low + 1），**任何理由都不得升到 High/Critical**。
4. **下调无需理由**：本 finding 实际不可达 / 防御有效 / 仅死代码 / **外部不可控**（source 完全内部产生、攻击者无任何途径影响触发点）时，必须下调。
5. **外部可控性封顶（两轴取严）**：在 §4.0 危害维度判定出级别后，必须用外部可控性维度做封顶校准——外部不可控封顶 Low、仅间接 / 极强前置封顶 Medium、需前置条件方可外部可控封顶 High、仅可直接远程方可达 Critical。两轴冲突时取更低一级。
6. **攻击请求（PoC）可得性封顶（脚本强制，§4.0 工件化判据）**：当 finding 的 `poc.available == "no"`（构造不出任何可复现攻击请求 / 触发工件）时，severity **封顶 Medium（中危）**，超出部分一律收敛到 Medium，并置 `humanReviewRequired: true`；`verifier.py challenge` 对此做确定性收敛（`poc_not_obtainable` 降级记录）。豁免类型（供应链 / 凭据·配置存在性类）不触发本封顶。

**禁止**：不得仅因「理论上可能」或「最坏情况下」就提升到 Critical/High。必须基于实际攻击链的可达性、外部可控性和直接危害共同判定。

## 5. LSP 降级规则

> 完整降级策略和错误处理表：Ref `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md > LSP 降级规则`。

摘要：S1/S2 Sink 必须至少尝试 1 次 LSP；失败仅该 Sink 回退；`lspStatus: "unavailable"` 时全部使用 Grep+Read。

## 6. Read 规范

- 禁止全文件 Read，必须用 `offset` + `limit`
- Sink/finding 上下文：目标行号 +-30 行
- 同文件最多 Read 3 次
- 大文件(>500行)先用 LSP documentSymbol 定位

## 7. 反隧道视野

- 同一 riskType 多文件出现 -> 合并为 1 个 finding + `affectedFiles[]`
- 单一维度不超过总预算 40%

## 8. Bash 使用规则

### 单行命令强制约束

**所有 Bash 命令必须为单行格式，禁止在命令中插入换行符。** 多行命令会导致权限白名单通配符匹配失败，触发不必要的手动授权弹窗。

常见场景：
- `wc -l` 后跟多个文件路径 → 所有路径写在同一行，用空格分隔
- `sqlite3` 后跟 SQL 语句 → SQL 压缩为单行（去除换行和多余空格）
- `python3 -c "..."` 内联脚本 → 代码写在同一行，用 `;` 分隔语句

> **数据库查询优先使用 `index_db.py query`**（`--preset`/`--sql`），覆盖绝大多数场景。仅当 preset 无法满足需求时才用 `python3 -c` 内联 SQLite，且必须为**单行格式**（用 `;` 分隔语句）。

### 允许/禁止列表

- **允许**：调用插件 Python 脚本（`python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/{script_name}" {subcommand} {args}`）
- **允许**：带 export 前缀的 Python 脚本调用（`export CODEBUDDY_PLUGIN_ROOT=... && python3 ...`）
- **允许**：内联 Python 数据处理（`python3 -c "..."`，**仅限**SQLite 查询、数据转换等轻量操作）
- **允许**：Git 只读操作（`git ls-files`/`diff`/`log`/`status`/`rev-parse`）
- **允许**：目录列表查看（`ls`）、回显验证（`echo`）
- **允许**：延时等待（`sleep N && ...`，用于等待上游 Agent 完成后执行查询/检查）
- **禁止**：用 `python3 -c` 读写文件（**必须用 Read/Write 工具**，免授权且更高效）
- **禁止**：`bash grep`/`find`/`cat` 做安全分析（必须使用工具层 Grep/Read/Glob）
- **禁止**：`pip install`/`brew install`/`npm install` 等包管理器命令（由 `ts_parser.py setup` 内部处理）
- **禁止**：内联 Python 中执行网络请求、修改项目源代码、安装包或执行危险子进程
- **禁止**：使用 `for`/`while` 等 Shell 循环
- **禁止**：在 Bash 命令中插入换行符（所有命令必须为单行）

## 9. 通用注意事项

- 不执行攻击，不修改项目源文件
- 所有文件路径和行号必须来自工具输出
- 排除测试数据和示例
- 每完成一个阶段必须立即写入，禁止积攒
