---
name: dd-financial-analysis
display_name: AI尽调·财务分析专家
display_name_en: AI Due Diligence · Financial Analysis
description: 面向中国境内银行对公信贷经理的财务分析能力。存在可用 Finance Run 时执行有界的 AIDD Runtime 候选生成；没有 Run 时执行独立、可追溯的财务专项报告流程。凡产出财务专项报告，一律同时交付 Markdown 与 DOCX 两种格式。数值计算必须由确定性脚本完成，缺失资料不得推测或补造。
description_zh: 银行对公信贷财务分析：三表解读、比率计算、同业对标与专项报告生成（MD + Word 双格式）。
description_en: Financial analysis for corporate banking credit — statement interpretation, ratio calculation, peer benchmarking and dedicated report generation (Markdown + Word).
category: finance
version: 1.3.0
author: 腾讯金融云
permissions: [sandbox, file-read-write]
requires_sandbox: true
---

## 打开 embed 页面（重要）

需要通过 `present_files` 打开业务页面时，**不要自己拼 URL**，按下面两步调用：

```
调用工具：create_embed_code
参数 path：/embed/workspace/{projectId}/finance

调用工具：present_files
参数 url：<上一步 create_embed_code 返回的 url>
```

- `path` 只写**站内相对路径**（以 `/embed/` 开头），`{projectId}` 替换为真实项目 ID；**站点域名由服务端决定，禁止自行拼接**。
- `create_embed_code` 返回 `{ url, code, expiresIn }`，**只用返回的 `url`**，不要拿 `code` 自己拼。
- 登录码**一次性且约 60 秒过期**：每打开一次页面就重新调用一次 `create_embed_code`，**禁止复用上次的 url**（复用会因登录码已失效而回退到手动登录）。

# 对公信贷财务分析

AIDD_FINANCE_RUNTIME_CONTRACT_VERSION=4

先路由，后执行。两个分支互斥，禁止把另一分支的工作附加到当前任务。

> **贯穿两个分支的硬规则**：只要本次任务要产出「财务专项报告」，就必须走本文「公共收尾：生成财务专项报告（MD + DOCX）」一节，**Markdown 与 DOCX 同步交付，缺一不可**。该节与路由无关，两个分支都适用。

## 前置：准备计算脚本

> **只有「独立财务专项报告」分支需要脚本。** AIDD execution Runtime 分支自 v1.2.0 起
> 全部数值由后端产出并经 `get_finance_agent_context` 的 `calculation.result` 下发，
> 该分支**不运行 `bootstrap.py`，也不运行任何计算脚本**。
>
> 例外：Runtime 分支若被要求产出专项报告，「公共收尾」节的 DOCX 渲染可以用 `md_to_docx.py`；
> 该脚本不可用时按公共收尾节的规定自行生成 DOCX，**不得因此跳过 DOCX**。

确定性计算脚本不随 Skill 包分发。**独立报告分支在第一次执行脚本前**，必须先运行引导脚本取得脚本目录：

```bash
python3 /workspace/.codebuddy/skills/dd-financial-analysis/scripts/bootstrap.py
```

返回 `{"ok": true, "scripts_dir": "...", "cached": ...}`。后续文档中的 `<scripts_dir>` 一律替换为返回的 `scripts_dir`，例如 `python3 <scripts_dir>/calculate.py`。

- 同一会话内只需运行一次；已缓存时返回 `cached: true`，可直接复用
- 返回 `{"ok": false, ...}` 时按 `error` 原样报告失败并停止，不得改用手算或估算替代脚本计算

脚本职责：

- `calculate.py`：三表标准化与全部指标、勾稽、异动、对标的权威计算
- `tables.py`：把计算结果转为报告可直接引用的 Markdown 表格与数值事实（独立专项报告用）
- `verify.py`：把报告正文声称的数字与权威重算逐项比对（交付前闸口）
- `peer_benchmark.py`：同业对标的行业分位数计算，由**后端**调用。可比公司原始科目由独立取数 Runtime 通过 MCP `web_search` 联网获取后交给本脚本计算 mean/median/P25/P50/P75。Runtime 分析分支不调用，只消费 baseline 中已注入的基准
- `md_to_docx.py`：把定稿报告 Markdown 渲染成专业排版 DOCX（**首选**渲染方式，内部复用 `word_report.py` 的排版能力）。脚本不可用时按「公共收尾」节自行生成 DOCX，绝不跳过
- `render.py` / `word_report.py` / `preflight_narrative.py`：后端受控 narrative 路径专用，独立专项报告流程不直接调用（`word_report.py` 仅作为 `md_to_docx.py` 的排版依赖被间接使用）

## 页面展示（present_files）

进入本流程时，调用 `present_files` 工具打开财务分析页面：

```
调用工具：create_embed_code
参数 path：/embed/workspace/{projectId}/finance

调用工具：present_files
参数 url：<上一步 create_embed_code 返回的 url>
```

- **每次进入流程都调用**：`{projectId}` 替换为真实项目 ID；即使对话记录中已打开过该页面，每次执行本 Skill 时仍调用 `present_files` 尝试打开
- 必须真实调用工具，不得只输出 URL 文本或请求用户提供网址
- `present_files` 只做展示，Agent 不从页面读取任何数据

## 强制路由

判据是「**本项目是否存在可用的 Finance Run**」，而不是上下文里有没有 `turnId`。

> **变更说明（v1.1.0）**：旧版要求上下文同时含 `runId`+`attemptId`+`turnId` 才走 Runtime 分支。
> 但 `turnId` 现在由 `begin_finance_turn` 在本 Skill 内部产生 —— 进入 Skill 时必然还没有，
> 按旧判据会永远误路由到独立报告分支。

### 1. AIDD execution Runtime（P0-P5 候选分析）

**先判定**：上下文已给出 `runId`，或调 `get_finance_run(projectId)` / `get_finance_workflow_context(projectId)`
能取到状态可继续的 Run（非 `failed`/已归档）时 → 必须完整读取并且只执行
[runtime-execution.md](runtime-execution.md)。

`attemptId` 与 `turnId` 由 `get_finance_agent_context` / `begin_finance_turn` 在该文档的流程中获取，
**不是进入本分支的前置条件**。

该分支具有最高优先级，即使用户消息中同时出现"报告""完整分析"或"Word"也不改变路由。该分支：

- **候选生成过程本身不产出专项报告**，不调用 `render.py`，不走后端受控 narrative 路径。
- ⚠️ 但**若用户要求生成「财务专项报告」**：先按本文档完成 Runtime 候选提交，再转入
  「公共收尾：生成财务专项报告（MD + DOCX）」节完成交付。该节**必须产出 MD + DOCX 两种格式**，
  数值只能取自 `get_finance_agent_context` 的 `calculation.result`。
  **不允许只保存 Markdown**——漏传 `docxCosKey` 前端就没有 Word，等于交付不完整。
- **不运行任何计算脚本，也不自行计算数值**：数字只能取自 `get_finance_agent_context` 的
  `calculation.result`（后端 `calculate.py` 的权威产出）。
- 不做公开研究，不联网，不查行业或可比公司（`researchMode` 允许时才可用只读 `web_search`）。
- 不穷举附注，不重复抽取 `get_finance_agent_context` 已返回的 `baseline.data` 中的事实。
- 不读取 `standalone-report.md`、`output-spec.md`、`analysis-logic.md` 或 `knowledge/public-source-policy.md`
  （「公共收尾」节已自包含全部报告交付步骤，不需要读这些子文档）。
- **材料、基线与计算结果只能通过 MCP 获取**（`get_finance_agent_context` → `get_finance_run_material`），
  不读写 `/workspace` 下的任何财务文件；只调用 Runtime 文档与「公共收尾」节明确列出的工具。

### 2. 独立财务专项报告

**仅当本项目没有可用 Finance Run**（未发起过核验，或用户明确要求脱离 Run 独立出一份报告）时，
必须完整读取并执行 [standalone-report.md](standalone-report.md)。

若用户要求的是「基于已有财务分析结果生成报告」，那属于 `dd-report` Skill 的职责，不走本分支。

该分支与其他专项报告（画像/经营/行业）架构对齐：**章节结构必须取自报告模板库，正文由 LLM 在该骨架内撰写完整 Markdown，全部数值与表格由确定性脚本产出**。

- **材料只能通过 MCP 获取**：进件材料不会预先注入沙箱，必须走 `get_intake_files(projectId)` → `get_intake_file_content(projectId, fileId)` 拿后端已解析好的 Markdown（与经营/画像/行业分析同一条工具链）。扫 `/workspace`、`/root`、`/tmp` 找不到文件**不等于**没有材料，不得据此判定"材料未注入"并终止。
- **章节骨架只能来自模板库**：必须先调 `search_templates("财务分析报告模板")` → `get_report_template(templateId)`，标题/顺序/层级逐字照用 `chapterOutline`，逐章遵循 `chapterList[].content`。**禁止自行拟定或精简大纲**；模板库确实没有可用模板时，须经 `ask_user_question` 用户确认后才可使用兜底结构。
- 表格与可引用数值由 `tables.py` 生成，正文只能整段引用其表格、只能从 `facts[key].display` 复制数字。
- 交付前**两道闸口都要过**：`verify.py` 数字逐项回算校验 + 章节完整性自检（定稿标题与模板 `chapterOutline` 逐条比对）。任一不通过不得调用 `save_finance_report`。
- 两道闸口通过后，按「公共收尾：生成财务专项报告（MD + DOCX）」节交付（对应 `standalone-report.md` 第 11 节）。
- 本分支**不调用 `render.py`**（`render.py` 仅服务于后端受控 narrative 路径）。

## 公共收尾：生成财务专项报告（MD + DOCX）

> 与路由无关，**两个分支都适用**。本节自包含，Runtime 分支执行本节时不需要读取任何子文档。
> 与 `dd-profile-analysis` / `dd-business-analysis` / `dd-industry-analysis` 采用同一套交付范式。

⚠️ **DOCX 不是可选项**。`save_finance_report` 不传 `docxCosKey` 时，前端财务页版本列表的预览/下载按钮会置灰并提示「该版本无 Word」，等于交付不完整。以下 6 步必须全部执行成功。

1. 调用 `get_project_finance_reports(projectId)` 查询已有版本，新版本号 = 已有最大版本号 + 1（无版本则从 v1 开始）
2. 生成报告 Markdown 内容（银行送审报告口吻），内容必须**完整详实**，不是摘要、不是大纲
3. 生成报告 DOCX 文件（在沙箱内生成，确保内容与 MD 一致）：
   - **首选**确定性脚本 `python3 <scripts_dir>/md_to_docx.py --md <报告.md> --out <报告.docx> --title "<企业名称>财务分析报告" [--period ...] [--scope ...]`，返回 `{"ok": true, ...}` 才算成功
   - 脚本不可用时（未运行 `bootstrap.py`、脚本包为旧版、Runtime 分支不带脚本目录等），**改用你选择的方式在沙箱内生成 DOCX**，并在交付说明中注明渲染方式
   - **任何情况下都不得跳过 DOCX**，也不得以"脚本缺失"为由只保存 Markdown
4. 调用 `create_report_upload_url(projectId, fileName: "财务专项报告.docx")` 获取 DOCX 上传地址，返回 `uploadUrl` + `cosKey`
5. 将 DOCX 文件上传到 `uploadUrl`（HTTP PUT，body 为文件**原始字节**，不是 base64、不是 multipart），HTTP 200/204 才算成功
6. 调用 `save_finance_report(projectId, content, versionLabel, docxCosKey)` 保存报告
   - ⚠️ `docxCosKey` 必须传入第 4 步返回的 `cosKey`（不是 `uploadUrl`），否则前端无法下载 DOCX 版本
   - ⚠️ `content` 必须是完整的报告 Markdown，不要只写摘要或大纲

**易错点**：

1. **`docxCosKey` 必须传** `create_report_upload_url` 返回的 `cosKey`（不是 `uploadUrl`），否则前端报告列表没有 Word 预览/下载。
2. **`content` 必须完整**：传完整报告 Markdown，不要只传摘要或章节大纲。
3. **版本号自增**：用 `get_project_finance_reports` 返回的最大版本号 +1；首次从 v1 开始。注意区分 `get_finance_reports`（后端受控报告会话专用、不吃 `projectId`），本节**只用带 `projectId` 的 `get_project_finance_reports`**。
4. **报告保存只能走 `save_finance_report`**：禁止用其他方式（通用报告生成、直接写文件等）保存，否则报告不会出现在财务分析页面的版本列表中。
5. **上传失败不得继续**：PUT 返回非 200/204 时必须排查重试，不能带着失败的上传去调 `save_finance_report`。

**交付确认**：保存成功返回报告版本后才可向用户宣称报告已生成，并说明本次章节数与 **DOCX 是否已可下载**。返回值中 `docxSaved: true` 才算 Word 交付成功。

## 共同边界

- 单位换算、四则运算、比率、期间变化、阈值比较、计数和行业差异只能来自 `calculate.py`（位于 `<scripts_dir>`）；报告表格与可引用数值只能来自 `tables.py`。
- LLM 只负责材料事实抽取、来源定位和定性分析；缺失值写 `null`，只有材料明确披露为零时写 `0`。
- 客户进件值优先；冲突必须披露，不能静默覆盖、平均或猜测。
- 工具、脚本或后端校验失败时准确报告失败，不能声称已完成或已同步。
- 独立专项报告分支的章节结构只能来自报告模板库，不得由 LLM 自拟；未取得模板不得静默兜底。
- **凡产出财务专项报告，必须 MD + DOCX 同步交付**：不论走哪个分支，保存报告一律走「公共收尾」节，`save_finance_report` 必须带 `docxCosKey`。只保存 Markdown 视为未完成交付。
- **报告保存只能走 `save_finance_report`**：禁止用通用报告生成工具或直接写文件的方式保存财务专项报告。
