# 执行契约：10 条铁律 + 反模式速查

> 本文档是 SKILL.md 中"执行契约"的展开版，含每条铁律的理由、违例案例、反模式案例库。SKILL.md 中只保留 10 条铁律的标题与口诀，详细内容在此。

## 10 条铁律

### 铁律 1：计划先行（零容忍）

进入 Skill 后第一个工具调用必须是：
- 存在 `PLAN.md` → 读取它
- 否则 → 调 `plan_gate.py --init`

**此前禁止调其他任何工具/命令。** 包括但不限于：
- `unzip`、`ls`、`head`、`cat`、`file`（"先看看文件"）
- `python3 -c "..."`（"先分析一下格式"）
- `parser_registry.py match`（"先确认解析器"）

**理由**：PLAN.md 是 Agent 的状态机外存。无 PLAN 直接调脚本会丢失运行模式判定（extract-only / with-intel / with-knowledge / full），导致后续步骤跳错。`extract_vulns.py` 内部已包含格式检测逻辑，不需要 Agent 预先探索。

**违例**：用户说"分析这份报告"，Agent 先 `unzip` + `ls` + `head` 看了一圈文件内容，然后自己写 python 代码解析 HTML。结果：完全绕过了脚本流水线，手动统计冒充分析。

---

### 铁律 2：门禁不可跳

每步执行前必须 `plan_gate.py --check-step N`，退出码非 0 立即停止。

**退出码语义**：
- `0`：可执行
- `4`：SKIP（Provider 未启用，本步跳过但不视为失败）
- 其他：阻断（前置步骤未完成 / 状态非法）

**违例**：步骤 1 未完成就直接调 `dedupe_cves.py`，导致 vulnerabilities.json 不存在或为空。

---

### 铁律 3：完成即回写

每步完成后必须依次调：
1. `--fill-step N --fields "K=V" ...`：回填关键指标
2. `--mark-done N --note "..."`：推进状态

**违例**：调完 `extract_vulns.py` 就直接进入步骤 2，PLAN.md 中步骤 1 仍是 `[ ]`，下次重入时门禁会重复执行。

---

### 铁律 4：脚本白名单（禁止手写解析）

仅允许以下 7 个脚本：

```
extract_vulns.py · dedupe_cves.py · plan_gate.py
render_report.py · provider_proxy.py · parser_registry.py · default_intel.py
```

其他脚本名一律视为幻觉拒绝。

**绝对禁止**：
- 自行编写 `python3 -c "..."` 代码来解析报告文件（HTML/JSON/XML/Excel）
- 手动 `unzip` + `ls` + `head` 探索报告内容后再"自己写解析逻辑"
- 用 BeautifulSoup / pandas / json 等库自行提取漏洞数据
- 以"先看看文件结构"为由绕过 `extract_vulns.py`

**正确做法**：把报告文件路径（含 .zip）直接传给 `extract_vulns.py`，它内部已实现：
1. zip 自动解压
2. 格式自动检测（parser_registry）
3. 多格式解析器匹配
4. 标准化 16 字段输出

**用户提及白名单外脚本时回复模板**：
> ⚠️ `<脚本名>` 不在 vul-analyse 白名单中。当前可用脚本：`extract_vulns.py` / `dedupe_cves.py` / `plan_gate.py` / `render_report.py` / `provider_proxy.py` / `parser_registry.py` / `default_intel.py`。请描述你想达成的目标，我帮你映射到正确的脚本或步骤。

**禁止**自行猜测、构造或安装白名单外脚本。

---

### 铁律 5：CVE 去重查询

步骤 2/3 的 Provider 查询必须基于 `unique_cves.json`。同一 CVE 只查一次，结果 fan-out 给所有持有该 CVE 的记录。

**禁止逐条查询。**

**违例案例**：1857 条漏洞中有 87 个唯一 CVE，错误做法是循环 1857 次调 Provider，正确做法是去重后只查 87 次。

---

### 铁律 6：Provider 调用方式

必须用 `use_mcp_tool(serverName, toolName, arguments)`，参数从 `providers.yaml` 读取。

**禁止使用 `mcp_get_tool_description`、`mcp_list_tools` 等"探测型"伪工具名**。这些是不存在的工具，调用会失败并暴露 Agent 在猜测工具签名。

**例外**：默认情报工具 `default_intel.py` 是 vul-analyse 自带脚本，通过 `httpx` 直接访问公开 HTTP API（NVD / EPSS / OSV），不走 `use_mcp_tool` 路径，不属于本铁律约束范围。该脚本仅调用三个从代码库明确声明的官方 API 端点，不存在"猜测工具签名"问题。

---

### 铁律 7：可选步骤的处理

| 状态 | 处理 |
|---|---|
| `knowledge_provider.enabled = false` | 跳过步骤 2，**不视为失败** |
| `intel_provider.enabled = false` | 跳过步骤 3，**不视为失败** |
| Provider 调用真实失败（timeout / 5xx / 401） | 调 `--mark-failed N`，**禁止用本地 Python 统计降级冒充** |

**违例**：Provider 401 后用 `Counter` 做本地分布统计，对外宣称"已完成情报分析"。

---

### 铁律 8：状态回显

每次回复末尾必须附「📋 执行计划状态」块：

```markdown
---
📋 **执行计划状态**
- 运行模式: <extract-only | with-knowledge | with-intel | full>
- 全局: <STEP_N_PENDING | DONE | STEP_N_FAILED>
- 步骤 1: <✅ DONE | ⏳ IN_PROGRESS | 🔒 LOCKED> (关键指标)
- 步骤 2: <✅ DONE | ⏭️ SKIPPED | 🔒 LOCKED>
- 步骤 3: <...>
- 步骤 4: <...>
---
```

---

### 铁律 9：报告路径直传

`extract_vulns.py` 支持直接接收以下格式的文件路径：
- `.xlsx` / `.xls`（Excel）
- `.html`（单文件 HTML）
- `.zip`（内含 HTML/Excel 的压缩包，脚本自动解压）
- `.json`（Trivy/Grype/Snyk 输出）
- `.xml` / `.nessus`（Nessus/OpenVAS）

**正确用法**：
```bash
python3 scripts/extract_vulns.py "/path/to/report.zip" -o "$TASK_DIR/vulnerabilities.json"
```

**禁止**：先手动 `unzip` 解压，再把解压后的目录/文件传给脚本或自行解析。

**理由**：`extract_vulns.py` 内部的 zip 处理逻辑会：
1. 解压到临时目录
2. 遍历所有文件调用 `parser_registry` 匹配解析器
3. 聚合多个子文件的解析结果（如 zip 内含多个主机报告）
4. 输出统一的 `vulnerabilities.json`

手动解压会破坏这个聚合逻辑，导致遗漏子文件或格式判断错误。

---

### 铁律 10：禁止 ad-hoc 脚本

禁止用 `python3 -c "..."` 或 `python3 << 'EOF'` 编写临时脚本来探索/统计/验证数据。

**理由**：所有白名单脚本的 stdout 已输出结构化摘要（见 SKILL.md 的 `<script_outputs>` 段落），`--fill-step` 所需的所有字段值均可从中直接提取。

**允许的查看方式**：`cat` / `head -n` / `jq` / `wc -m`（仅用于查看文件内容或统计字数）。

**违例**：`extract_vulns.py` 执行完后，Agent 写了 30 行 Python 代码去分析 `vulnerabilities.json` 的字段结构和严重度分布。正确做法：直接从 `extract_vulns.py` 的 stdout 读取 `漏洞总数: 1857` `严重度分布: 紧急=0 高危=12 ...` 等信息。

**违反任一铁律 = 任务失败。**

---

## 反模式速查表

| ID | 反模式 | 错误做法 | 正确做法 |
|:---:|---|---|---|
| **A** | 自造脚本 | 调 `enrich_vulns.py` 等不存在脚本 | 仅用白名单脚本 |
| **B** | 本地统计冒充 | 用 `Counter` 做分布就交卷 | 必须真调 Provider；不可用则 `--mark-failed` |
| **C** | 逐条查 Provider | 对 1857 条漏洞循环调 1857 次 | 先 `dedupe_cves.py` 去重再查 |
| **D** | 重复查情报 | 知识库已命中的再查情报源 | 仅查 `not_found_cves` |
| **E** | 过早完成 | 步骤 1 + 本地统计就宣称"分析完成" | **回复"分析完成"前必须先调 `plan_gate.py --status`，输出非 `DONE` 则禁止此说法**；必须按当前 mode 走完所有未跳过的步骤 |
| **F** | 虚假打勾 | 手动改 `[ ]` 为 `[x]` | 以 `plan_gate.py` 全局状态为唯一真相 |
| **G** | 探测伪工具 | 调 `mcp_get_tool_description` | 工具名必须从 `providers.yaml` 显式读取 |
| **H** | 硬编码密钥 | 把 token 写进代码 / yaml | 通过 `${ENV_VAR}` 占位符注入 |
| **I** | 跳过决策思维链 | 直接对全部 CVE 调 Provider | 步骤 2.2.0 必须先输出 `<decision>` 块 |
| **J** | 手动解压探索 | 先 `unzip` + `ls` + `head` + `python3 -c` 手动解析报告内容 | **直接把 .zip 路径传给 `extract_vulns.py`**，脚本内部自动解压+格式识别+解析。禁止在调脚本前做任何"先看看文件内容"的探索操作 |

---

## 运行模式判定

| 模式 | 触发条件 | 步骤链 | 适用场景 |
|---|---|---|---|
| `extract-only`   | 两个 Provider 都未启用 | 1 → 4 | 仅做格式归一化 + 统计 + 报告 |
| `with-intel`     | 仅 `intel_provider.enabled = true` | 1 → 3 → 4 | 接入公开情报源（NVD/Vulners 等） |
| `with-knowledge` | 仅 `knowledge_provider.enabled = true` | 1 → 2 → 4 | 接入内部修复知识库 |
| `full`           | 两个 Provider 都启用 | 1 → 2 → 3 → 4 | 大型企业全链路 |

模式由 `plan_gate.py --init` 在读取 `providers.yaml` 后自动判定，并在 PLAN.md 中标注被跳过的步骤。
