---
name: resume-ai-help
display_name: 简历 AI 帮你写
display_name_en: Resume AI Help Write
description: 用于直接改写、润色或优化简历内容。当用户要求「优化简历」「改写简历」「润色简历」「帮我写简历」「生成优化版简历」「把这段经历写得更好」，或上传整份简历并要求产出修改后的版本时触发。支持复现简历「AI 帮你写」两阶段追问与优化交互；整份优化固定生成 HTML 和 PDF，单字段优化只返回该字段。仅负责内容创作和改写，不执行整份简历诊断、问题清单或 6 维评分；用户仅要求分析问题、评审或打分时，改用 resume-diagnosis。
description_zh: 用于直接改写、润色或优化简历内容。当用户要求「优化简历」「改写简历」「润色简历」「帮我写简历」「生成优化版简历」「把这段经历写得更好」，或上传整份简历并要求产出修改后的版本时触发。支持复现简历「AI 帮你写」两阶段追问与优化交互；整份优化固定生成 HTML 和 PDF，单字段优化只返回该字段。仅负责内容创作和改写，不执行整份简历诊断、问题清单或 6 维评分；用户仅要求分析问题、评审或打分时，改用 resume-diagnosis。
description_en: Use when the user asks to directly rewrite, polish, optimize, or create resume content, including requests such as "optimize my resume", "rewrite my resume", "polish this experience", "help write my resume", or generating a revised version from an uploaded resume. It supports the two-stage ask-and-optimize interaction. Full-resume optimization must produce HTML and PDF, while single-field optimization returns only the revised field. This skill creates or rewrites content but does not perform comprehensive diagnosis, issue reporting, or six-dimension scoring. If the user only asks for analysis, review, feedback, or scoring, use resume-diagnosis instead.
category: 15-Education
version: 2.0.1
author: wangtengfei
agent_created: true
---

# 简历 AI 帮你写

面向学员端完成简历内容优化。只使用用户提供的简历，以及 gaodun-job MCP 下发的静态 Prompt、模块配置和 HTML 模板；不读取后端源码，不调用简历业务接口，不落库。

## 核心契约

每一步都必须满足进入条件后才能执行，并产生明确产物后才能进入下一步。岗位确认是硬门禁，岗位值不是绝对必填：缺少意向岗位时询问一次；用户给出岗位则定向优化，用户明确不填或要求通用优化则记录跳过并继续。不得把岗位问题混入字段追问。

## 路由与分支

| 用户请求 | 进入条件 | 路径 | 产物 |
|---|---|---|---|
| 只优化一段或一个字段 | 已提供待优化原文 | 单字段优化 | 优化后的字段文本 |
| 优化已上传的整份简历 | 已提供完整附件或全文 | 整份优化 | 本地 HTML + PDF；失败时降级为已完成内容 |
| 只排版，不改内容 | 已提供整份简历 | 仅排版 | 本地 HTML |
| 诊断、评分、问题报告 | 请求重点是评价而非改写 | 改用 `resume-diagnosis` | 由对应 skill 决定 |
| 面试练习 | 请求重点是模拟面试或刷题 | 改用 `interview-brush` | 由对应 skill 决定 |

用户已提供整份简历并泛化要求“优化简历”时，直接走整份优化；不再询问范围、模板或输出格式。只有用户明确限定字段时才缩小范围。

## 意向岗位确认门禁

### 何时进入

- 单字段或整份内容优化：必须执行岗位确认。
- 仅排版：不执行岗位确认，直接解析和渲染。
- 简历已有明确 `position`：视为已确认，不重复询问。

### 决策分支与产物

| 情况 | 动作 | 产物 / 状态 | 下一步 |
|---|---|---|---|
| 有一个明确岗位 | 直接采用 | `position=<岗位>`、`positionConfirmed=true` | 准备优化资源 |
| 没有岗位 | 单独询问一次目标岗位并停止 | 等待用户输入 | 收到答复后重新判定 |
| 用户明确不填或要求通用优化 | 接受跳过，不再追问 | `position=""`、`positionConfirmed=true`；Prompt 中岗位变量由脚本填“无” | 准备优化资源 |
| 只有岗位名称、没有 JD | 按岗位名称定向，不索要 JD | `position=<岗位>` | 准备优化资源 |
| 用户要求按具体 JD 匹配但未提供 JD | 询问 JD 并停止 | 等待 JD | 收到后继续；不得臆测 JD 要求 |
| 多个意向岗位且未指定主岗位 | 请用户选一个主岗位，或明确选择通用优化 | 等待选择 | 不得把冲突岗位要求混入同一版本 |

整份流程的机器门禁：`init` 返回 `positionMissing=true` 时，必须先完成上表分支；有岗位执行 `set-position --position '<目标岗位>'`，明确跳过执行 `set-position --skip`。在此之前 `next` 必须拒绝推进。

单字段流程没有 runner 状态文件，但门禁语义相同：确认结果写入 `fields.json.position`；用户明确跳过时写空值，由脚本统一填“无”。

## 不可违背的执行断言

- 用户上传整份简历并泛化要求优化时，默认且立即执行整份优化并生成 HTML + PDF；整份简历优化的最终交付物固定为 HTML 和 PDF，并自动进入 Phase 5（即本文“汇总/渲染”步骤）。禁止询问“希望怎么优化”，不得提供“整份重写 / 诊断 / 重点字段”选项，也不得推荐或切换到 `resume-diagnosis`。
- 禁止询问或提供 Word / PDF / HTML 输出格式选择；默认模板固定为 `default`。
- `--resume-type` 只使用 CLI 枚举键，例如 `havingInternshipExperience`；禁止数字别名，也不得让用户选择 `resumeType`。
- 每个优化字段无条件走两阶段，第一个动作恒为追问 Prompt；问题产生后用户可全部跳过，但展示追问后必须结束当前回复。不得把“用户尚未回答”解释为“全部跳过”。
- 整份简历必须使用 `scripts/full_resume_runner.py`，禁止由模型自行维护循环下标。优化结果逐条累计到 `overrides.json`；仍有未处理项目，runner 会禁止提前生成 HTML。没有需要优化的字段时直接进入渲染。
- 用户明确跳过追问时执行 `skip-questions --state runner-state.json --confirmed-by-user`。优化响应通过 `complete --state runner-state.json --response-file optimization-response.json` 传递 LLM 原始 JSON；禁止用 `complete --resume`。

## 全局约束

1. Prompt、模板和模块配置默认只通过一次 `resume_resource_bundle_get` 获取；旧的 `resume_prompt_get`、`resume_module_config_get`、`resume_template_get` 仅用于整任务兜底，不得读取后端工程作为运行依赖。
2. MCP 只接收资源查询参数。简历正文、追问答案、优化结果和个人信息不得传给 MCP。
3. MCP 返回值原样保存为 UTF-8 JSON，再交给 `scripts/materialize_resources.py`；不得手工拆 JSON、复制 Prompt 或改写 HTML。
4. 简历解析只用 `scripts/resume_parse.py`；整份编排只用 `scripts/full_resume_runner.py`；HTML 只用 `scripts/render_resume_html.py`；HTML 转 PDF 只用 `scripts/html_to_pdf.py`。
5. 多行 JSON、简历正文和问答通过文件传递，不放进 shell 参数。模型原始响应只用 `scripts/save_response.py` 从 stdin 落盘，禁止 shell `>` 重定向或临时脚本转写。
6. 每个进入优化的字段必须先执行追问 Prompt。返回 3 个问题时，展示后停止；只有用户回答或明确跳过才能继续。返回 `questions: []` 时不打扰用户，直接优化。
7. 空变量和跳过答案由脚本填“无”，不得编造用户信息。
8. 追问结果必须是 3 个非空问题或零问题，不允许残缺；优化结果必须含非空 `resume`。解析失败只允许修复一次并再校验一次。

## 流程总览

| 步骤 | 进入条件 | 动作 | 必须产物 | 分支 / 退出条件 |
|---|---|---|---|---|
| 1. 路由 | 收到用户请求 | 按“路由与分支”分类 | `single` / `full` / `layout-only` / 转交目标 | 转交即结束本 skill |
| 2. 岗位确认 | 路径包含内容优化 | 执行岗位确认门禁 | 已确认的岗位值或明确跳过记录 | 未确认则停止等待；仅排版跳过此步 |
| 3. 资源准备 | 路由和岗位状态已确定 | 一次获取并物化对应模式的 MCP 资源包 | 完整资源目录 | 失败则按资源失败语义停止；仅“不支持新工具”可整任务兜底 |
| 4. 输入准备 | 模块配置已物化 | 保存用户内容；整份简历再解析 | `fields.json` 或 `finalized.json` | 解析失败则报告并停止 |
| 5. 字段追问 | 字段原文和追问 Prompt 就绪 | 调模型、保存并解析响应 | 3 个问题或 `questions: []` | 3 问则等待；零问直接优化 |
| 6. 字段优化 | 用户已回答/明确跳过，或追问为零问 | 渲染优化 Prompt、调模型并校验 | 非空 `resume` | 失败可重试、跳过当前字段或停止 |
| 7. 汇总/渲染 | 单字段完成，或整份队列全部结束 | 单字段直接交付；整份累计 overrides 后渲染 HTML 并导出 PDF | 字段文本或 HTML + PDF | HTML 失败则降级交付已完成内容；PDF 失败只降级 PDF |

## 准备 MCP 资源

默认执行“一次 MCP 业务调用 + 一次 Python 执行”。宿主只把完整 tool result 保存为一个 UTF-8 JSON 文件，禁止逐字段复制、拆分或重复启动 Python。详细协议见 [references/pipeline.md](references/pipeline.md)。

### 单字段

1. 进入条件：已确定 `dataFieldCode`，并完成岗位确认。
2. 从 `references/field-config.json` 取得该字段的 `promptOneId/promptTwoId`，调用一次 `resume_resource_bundle_get {"prompt_ids":["<promptOneId>","<promptTwoId>"]}`。
3. 将完整响应保存到资源目录之外的临时 JSON 文件，然后只启动一次 Python：

   ```bash
   python scripts/materialize_resources.py ingest-bundle --mode single \
     --input <bundle-response.json> --out-dir <资源目录> \
     --prompt-ids <promptOneId,promptTwoId>
   ```

### 整份简历

1. 进入条件：用户已提供整份简历；必须在 `resume_parse.py emit-template/finalize` 之前准备资源。
2. 调用一次 `resume_resource_bundle_get {"include_all_prompts":true,"include_module_config":true,"theme":"default"}`。
3. 将完整响应保存到资源目录之外的临时 JSON 文件，然后只启动一次 `ingest-bundle --mode full`。脚本同时校验、转换模板、写 manifest 并事务替换资源目录；成功后不得再单独运行 `verify`。
4. 使用已物化的 `resume-module-config.json` 执行解析，再执行 runner `init`。
5. 若输出 `positionMissing=true`：立即执行岗位确认门禁；未完成前不得调用 `next`。

仅排版调用一次 `resume_resource_bundle_get {"include_module_config":true,"theme":"default"}`，随后执行一次 `ingest-bundle --mode layout`。旧路径诊断可用 `verify`；`--layout-only` 与 `--prompt-ids/--field-config` 互斥。

## 单字段执行

1. 进入条件：岗位已确认，字段类型和原文已确定。输出 `fields.json`，其中包含 `position`。
2. 执行 `aihelp.py render --stage ask`。输出渲染后的追问 `systemPrompt/userContent`。
3. 调当前模型，用 `save_response.py` 保存 `ask-response.json`，再执行 `parse-ask`。
4. 分支：
   - 3 个问题：展示问题并停止；用户回答后输出 `qa.json`。
   - `questions: []`：无需用户输入，直接进入优化。
   - 非法响应：只修复一次；仍非法则停止。
5. 执行 `aihelp.py render --stage opt`，保存 `optimization-response.json`，再执行 `parse-opt`。
6. 完成条件：解析得到非空 `resume`；只交付该字段内容。

## 整份简历编排（本地扩展）

处理前必须阅读 [references/analysis-resume-rules.md](references/analysis-resume-rules.md) 和 [references/pipeline.md](references/pipeline.md)；结构不清楚时再读 [references/resume-schema.md](references/resume-schema.md)。

1. 进入条件：已提供整份简历。提取文本、填充解析模板，并用 `resume_parse.py finalize` 输出 `finalized.json`。
2. 进入条件：解析完成且基础资源已物化。执行 `full_resume_runner.py init`，输出 `runner-state.json`、`requiredPromptIds` 和岗位状态。
3. 进入条件：岗位门禁已解除、所需 Prompt 已物化。重复执行 `next`，只按其返回动作推进：
   - `ask`：调用追问模型；3 问则展示后停止，零问则执行 `no-questions`。
   - 用户回答：保存 `qa.json`，执行 `answers --qa-file qa.json`。
   - 用户明确跳过追问：执行 `skip-questions --confirmed-by-user`；仍进入优化。
   - `optimize`：调用模型，用 `complete --response-file` 保存结果。
   - 字段失败：由用户选择重试、`skip-item --confirmed-by-user` 或停止。
4. 输出：所有结果按 `(moduleCode, dataSort, dataFieldCode)` 逐条累计到 `overrides.json`；不得自行维护循环下标。
5. 只有 `next` 返回 `render_html` 后才能生成 HTML；仍有未处理字段时禁止提前导出。

模型调用或会话中断后，从 `runner-state.json` 继续，不得重新初始化覆盖进度。

## 交付与降级

- 单字段：只返回优化后的字段内容。
- 整份简历：默认同时交付 HTML 和 PDF。HTML 渲染成功后，立即执行一次：

  ```bash
  python scripts/html_to_pdf.py --html <简历.html>
  ```

  输出到 HTML 同目录同名 `.pdf`；脚本返回非零或 PDF 校验失败时，只降级 PDF，仍交付 HTML 并明确说明。
- **编辑事实源**：HTML 是唯一可编辑事实源，PDF 是从 HTML 重新生成的只读产物。用户后续要求修改内容或样式时，一律先改 HTML（或改 `finalized.json`/`overrides.json` 后重新渲染），再用 `html_to_pdf.py` 重新导出 PDF，保证两份产物同步。禁止直接编辑 PDF。
- 模板缺失或转换失败：仍交付已完成的优化内容，并明确 HTML/PDF 未生成。
- 某字段失败：保留已完成结果；等待用户选择重试、跳过该字段或停止。
- 不在日志或 manifest 中保存完整电话、邮箱、简历正文、问答或模型响应。

## 交付结束语

整份优化交付 HTML + PDF 后，固定以以下话术收尾（路径替换为实际产物路径）：

> 优化版简历已生成：
> - HTML：`.../张三的简历.html`（浏览器打开可预览、打印）
> - PDF：`.../张三的简历.pdf`（可直接投递）
>
> 如果想调整内容，直接在对话里告诉我要改哪里，我会改完同步更新 HTML 和 PDF；也可以下载 PDF 自行使用，或在浏览器打开 HTML 后另存/打印。

## 常见错误

| 错误 | 正确处理 |
|---|---|
| 把意向岗位混入某字段的 3 个追问 | 岗位是前置门禁，必须单独询问一次 |
| 把岗位值当成绝对必填 | 用户明确要求通用优化时记录跳过并继续 |
| 没有 JD 就阻塞所有优化 | 只有用户明确要求“按 JD 匹配”时 JD 才是必需输入 |
| 同一版本同时迎合多个冲突岗位 | 先确定主岗位，或选择通用优化 |
| 追问后自动替用户作答 | 展示并停止，等用户回答或明确跳过 |
| runner 尚未返回 `render_html` 就导出 | 继续队列，直到 runner 明确放行 |

只有用户明确要求按具体 JD 匹配时，JD 缺失才构成卡点；其他优化不得因没有 JD 而停住。

## 内部映射边界

后端实现、接口、配置与 PromptId 的来源和影响分析不属于本 Skill，由服务端团队维护；不要把它们加入学员执行流程。
