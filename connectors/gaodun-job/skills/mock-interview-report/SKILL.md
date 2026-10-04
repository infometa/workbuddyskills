---
name: mock-interview-report
display_name: 模拟面试报告
display_name_en: Mock Interview Report
description: 模拟面试抽题与评估报告生成，支持按岗位生成结构化面试间。通过 mcp 工具 draw_questions 按岗位（如「银行销售岗位」「公务员/省考/山东」）一次性抽取最多 3 道面试题，一次性展示题目并收集用户全部回答后，生成单题评分与面试辅导建议，并聚合并输出 HTML 分析报告。当用户要求「生成面试间」「结构化面试」「模拟面试」「抽面试题」「面试题分析报告」「评估我的面试回答」「面试辅导建议」，或要求针对某岗位（如银行销售）生成模拟面试并给出辅导建议时使用。
description_zh: 模拟面试抽题与评估报告生成，支持按岗位生成结构化面试间。通过 mcp 工具 draw_questions 按岗位（如「银行销售岗位」「公务员/省考/山东」）一次性抽取最多 3 道面试题，一次性展示题目并收集用户全部回答后，生成单题评分与面试辅导建议，并聚合并输出 HTML 分析报告。当用户要求「生成面试间」「结构化面试」「模拟面试」「抽面试题」「面试题分析报告」「评估我的面试回答」「面试辅导建议」，或要求针对某岗位（如银行销售）生成模拟面试并给出辅导建议时使用。
description_en: Generates mock-interview question-drawing and evaluation reports, supporting structured-interview-room generation by job position. Uses the draw_questions MCP tool to draw up to 3 interview questions at once for a given position (e.g. "bank sales", "civil servant/shandong"), presents all questions together and collects the user's full answers, then produces per-question scores and interview coaching advice, and aggregates the results into an HTML analysis report. Use when the user asks to generate an interview room, run a structured mock interview, draw interview questions, get an interview-question analysis report, evaluate their interview answers, or get coaching advice for a specific position such as bank sales.
category: 15-Education
version: 1.0.1
author: 上海高顿教育科技有限公司
---

# Mock Interview Report（模拟面试抽题与评估报告）

## Overview

完整走一遍「抽题 -> 作答 -> 评估 -> 报告」流程，报告逻辑与线上面试评估实现保持一致，不绑定真实用户/面试信息：

1. 抽题：**由 mcp 工具 `draw_questions` 执行**——工具内部组装请求、解析岗位、拼接维度并返回标准化题目 JSON。本 skill 不直接调用抽题接口，也不依赖真实用户/面试信息。
2. 评估：对每道已作答题目执行两个相互独立的评估——面试建议、单题评分，各自失败互不影响。
3. 报告：按每题分数、维度聚合、总分、总评生成报告，并按得分比例升序排序展示。

所有输出格式、分数计算、排序规则必须与 `references/report-logic.md` 完全一致，不得自行发明格式（如用 `#` 切分单题评分——线上解析并不是这样）。

## 输出红线：内部 ID 绝不外泄（最高优先级）

`draw_questions` 返回与评估过程中存在大量**内部 ID**（`jobId`、`projectId`、`industryId`、`promptIds`、`questionId`、`groupId`、`bizId`、`dimensionIds`、`filter_question_ids` 等）。它们只用于内部逻辑：选 prompt 变体、合并维度、防重复抽题、确认归属。**这些原始 ID 严禁出现在任何面向用户的内容中**——聊天中的题目列表、评估中间过程、最终 HTML 报告一概不允许，一条都不行。

- **抽题后展示题目**：考核维度只显示**维度名称**（`dimensionNames`），不显示 `dimensionIds`；题号用展示序号（第 1/2/3 题），不用 `questionId`/`groupId`。
- **单题评分 / 面试建议 / 总评**：内部按 ID 路由 prompt，对外输出只含文字评分与建议，不展示 `promptIds` 等变体标识。
- **最终报告**：只包含题干、题型名称、维度名称、分数、建议、总评等可读文本，报告内不得出现任何内部数字 ID。

判据：凡用户能看到的东西，出现 `questionId` / `dimensionId` / `jobId` / `projectId` 等原始数字 ID 即为违规，一律替换为对应的可读名称或直接去掉。若确实没有可读名称（如维度库未命中），用通用占位名（如「维度N」）代替，绝不输出原始 id。

## 前置检查（必读）

开始流程前依次检查：

1. **岗位定位**：抽题工具 `draw_questions` 支持定位方式：
   
   - `job_description`（自然语言描述，推荐）：如「银行/柜员」「公务员/省考/山东」。命中后自动确定 jobId/projectId/industryId 及对应 prompt 变体。
   
   用户未指定岗位时，需要引导用户指定岗位抽题。
   **注意（不提供事业单位选项）**：当用户的项目或岗位不明确、需要引导用户明确岗位时，**不要提供「事业单位」项目作为选项**（事业单位 prompt 变体未上线配置、暂用通用版，题库与评估质量不稳定）。可引导用户选择有稳定题库的项目（如公务员、银行、央国企），用户明确要求事业单位时除外。
   **注意（多岗位重名）**：同一项目下不同行业可能有同名岗位（如公务员项目「山东」同时存在于省考行业与选调行业），自然语言解析可能落到错误行业（且该行业题库可能为空）。应尽量用「项目/行业/岗位」三级限定描述（如 `job_description="公务员/省考/山东"`），命中多岗位时提示用户确认。
   **注意（题库为空）**：工具返回 `组题失败，题库无可用题目`（或空题库）表示该岗位在环境内无可用题库。此时不要伪造题目：在**同一项目内**换行业/岗位探测，最多尝试 **3 次**不同 `job_description` 组合，**不要切换项目**；仍为空则告知用户并让其选择：用公考真题手动出题 / 换有题库的项目（如银行）继续 。
2. **Prompt 变体**：直接取自抽题返回的 `meta.promptIds`（`advice`/`generalComment`/`overall`），无需手动查表。已内置线上 prompt 正文（见 references 三个 prompt 文件）：
   
   - 100520929 公务员：advice=2167 / generalComment=893 / overall=2147
   - 1000648 银行：advice=2169 / generalComment=585
   - 100534841 央国企：advice=2169 / generalComment=585
   - 100535479（注：此 projectId 当前不在岗位映射表中）：advice=2177 / generalComment=1874
   - 100523443 事业单位：暂用通用版 2169/585（线上配置未提供，待确认）
   `meta.promptIds.overall` 为 null 时（银行/央国企等），总评按同一输入/输出契约直接生成。若用户提供了更新的 prompt 文本，替换对应「Prompt 正文」区域（输入/输出格式契约已按线上解析代码固化，不得改动）。

## Workflow

### Step 1: 抽题（最多 3 道）

调用 mcp 工具 `draw_questions`。参数均非必填：

| 参数 | 类型 | 说明 |
|---|---|---|
| `job_description` | string | 岗位自然语言描述（如「银行/柜员」「公务员/省考/山东」） |
| `interview_type` | string | 面试类型，默认 `REAL_QUESTION`，枚举 `REAL_QUESTION` |
| `question_configs` | array | 题目配置（顺序即题号顺序）；缺省为岗位特色题/英语题/专业题各一道。每项含 `id`(题号)、`question_type`(整数编码) |
| `dimension_ids` | array<int> | 考核维度 id 集合，缺省空 |
| `filter_question_ids` | array<string> | 需过滤（不再抽取）的题目 id 集合，缺省空 |
| `max_questions` | integer | 最多返回题目数，1~3，默认 3 |

`question_type` 编码：0 岗位特色题 / 1 英语题 / 2 专业题 / 4 行业常规题 / 42 自我介绍题 / 43 主题陈述题 / 44 综合面试题（**不可传 3 个性题——工具不会返回**）。

典型调用（不指定 question_configs，用缺省题型组合，抽 3 道）：

```
draw_questions(job_description="", max_questions=3)
```

返回单对象 JSON：

```
{
  "meta": { "jobId", "projectId", "projectName", "industryId", "jobName",
            "promptIds": {"advice", "generalComment", "overall"} },
  "questions": [{
    "questionNo", "questionId", "groupId", "bizId", "questionStem",
    "questionType"(int), "questionTypeName", "isProbe",
    "dimensionIds"(int[]), "dimensionNames"(中文逗号分隔),
    "assessmentLatitude"(评分标准全文), "evaluation"(维度简介拼接),
    "questionRefer"(array), "examineModule"
  }],
  "note": ""
}
```

- `meta.promptIds` 直接用于 Step 3 的 prompt 变体选择；`meta.projectId` 用于下文校验变体归属。
- 每题的 `assessmentLatitude`/`evaluation`/`dimensionNames` 已由工具按维度配置真实拼接，下游评估直接取用，不得自行重拼。
- 工具行为规则：`interview_type` 不可为 `COMPOSE_QUESTION`；个性题（questionType=3）不会被返回；同一场不会重复出题。
- 工具调用失败或返回空题库时直接报出，并按前置检查 1 的兜底处理：同一项目内最多换 3 次行业/岗位探测、不切换项目，不要伪造题目。

### Step 2: 一次性展示题目并收集回答

将全部题目一次性展示给用户，每题包含：题号（展示序号）、题型名称、题干、考核维度（显示**维度名称**，如「逻辑思维」「岗位认知」——**严禁展示 `dimensionIds` 或任何内部 ID**）。提示用户按题号逐题作答。

- 允许跳过：跳过的题不调用两个评估，单题分数记 0，各考核维度按 0 分参与维度平均（对齐线上缺失记录按 0 计的逻辑），辅导建议留空。

### Step 3: 逐题评估（两步独立，格式契约见 references/report-logic.md）

按 Step 1 返回的 `meta.promptIds` 选择 prompt 变体（见前置检查 2），后续两次评估均使用同一变体。

对每道已作答题目，先按以下固定格式拼接问答文本：

```
问题:{题干}
回答:{用户回答}
```

（本 skill 抽题配置 isProbe=false，无追问段落；追问格式见 report-logic.md 备注即可，不模拟。）

然后执行两个相互独立的评估（各自独立执行，一个失败不影响另一个）：

1. **面试建议**：使用 `references/prompt-coaching-advice.md` 所选变体的 prompt，替换 `{{$target_job}}`、`{{$evaluation}}`（取自抽题返回的同名字段）、`{{$student_resume}}`、`{{$question_refer}}`（逐条拼为 `参考范例1：xxx\n`）变量（2169/2177 的 `{{$skills}}`/`{{$goals}}`/`{{$rules}}` 见 `references/prompt-skill-map.md` 原样替换，2167 的 `{{$structure}}` 置空）。输出**为 JSON**：`{"你的回答优点在于":"...","不足之处及改进建议":"...","作答范例":"..."}`（支持中文 key，亦可映射英文 key；JSON 不合法时 fallback 为 `回答优点#改进建议#参考作答` 按 `#` 切分三段）。展示时三段分别加固定前缀「你的回答优点在于：」「不足之处及改进建议：」「作答范例：」。
2. **单题评分**：使用 `references/prompt-single-evaluation.md` 所选变体的 prompt，替换 `{{$target_job}}`、`{{$assessment_latitude}}`（取自抽题返回的同名字段；公考 893 为 `{{$evaluation}}`）变量。输出为**每个考核维度一段、段与段之间空行分隔**的三行结构（解析时按 `\n\n` 分段、段首须为数字）：

   ```
   1、维度名：
   分数：16分
   建议：评语内容
   ```

   每个维度满分 20 分。解析规则：维度名=首行 `、`/`.` 之后到 `：` 之间；分数=第二行 `：` 后到最后一个 `分` 之间（无「分」则取到行尾）；建议=第三行 `：` 之后；分数转数字失败记 0。回答跑题（输出含「你的回答与本题无关」）时该题各维度记 0 分。

**本题分数**（百分制）：

```
本题分数 = Σ各维度 floor(维度分 / 20 × 权重)
```

权重等权分配：`floor(100/维度数)`，最后一个维度取 `100 - 其余之和`；先对每个维度单独 floor 再求和。

### Step 4: 聚合报告数据

1. **维度平均分**：跨题按维度合并，同维度多题分数取平均，保留 2 位小数（HALF_UP）。维度评价 = 各题评语按 `第{中文数字}题：{评语}` 逐行拼接（如「第一题：表达清晰…\n第三题：…」）。
2. **维度换算分与权重**：维度平均分先截断取整，换算分 = `floor(平均分 / 20 × 权重)`，权重归一化合计 100（等权分配规则同上，最后一个维度拿余数）。报告展示的维度得分即该换算分（百分制）。
3. **总分**：= Σ权重列表内各维度换算分，超过 100 按 100 封顶。
4. **总评**：使用 `references/prompt-overall-evaluation.md` 的 prompt（公考 2147；其他项目按同一输入/输出契约直接生成），输入为**全部题目的问答内容**（每题题干、回答、考核维度名列表），输出 JSON `{"面试表现总评":"..."}`，取该文字作为总评，不是基于分数计算。
5. **排序**：维度报告按 得分比例（维度换算前平均分/满分）**升序**排列——得分低的维度排前面，与线上展示一致。

### Step 5: 生成 HTML 报告并交付

复制 `assets/report-template.html`，替换以下占位符生成最终报告文件（文件名如 `interview-report.html`）：

- `{{TARGET_JOB}}` / `{{INTERVIEW_TYPE}}` / `{{GENERATED_AT}}`
- `{{TOTAL_SCORE}}` / `{{TOTAL_SCORE_MAX}}`（100）/ `{{INTERVIEW_EVALUATION}}`
- `{{DIMENSION_ROWS}}`：按模板注释中的 `<tr>` 结构生成维度行（含 `{{DIMENSION_PERCENT}}` 进度条宽度），**按得分比例升序**
- `{{ANSWER_RECORDS}}`：按模板注释中的 `qa-item` 结构生成每题记录（题干、题型、用户回答、本题分数、回答优点/改进建议/参考作答，三段带线上前缀文案）

生成后调用 present_files 将 HTML 报告交付给用户。

**报告中不得出现任何内部 ID**（`questionId`/`dimensionId`/`jobId`/`projectId` 等一律不渲染）；模板占位符只填可读字段（维度名、题型名、题干、回答、分数、建议、总评）。

## Resources

- `assets/report-template.html` - HTML 报告模板，覆盖总分、总评、维度报告、回答记录等报告字段
- `references/report-logic.md` - 报告生成与聚合逻辑（问答拼接格式、两类评估的参数与输出契约、每题分数/维度分/总分计算公式、排序规则、简化假设）
- `references/prompt-single-evaluation.md` - 单题评分 prompt（按项目选择变体：893/585/1874，含输入/输出契约）
- `references/prompt-coaching-advice.md` - 面试建议 prompt（按项目选择变体：2167/2169/2177，含输入/输出契约）
- `references/prompt-overall-evaluation.md` - 面试总评 prompt（公考 2147，含输入/输出契约）
- `references/prompt-skill-map.md` - 非公考 advice prompt 的 skills/goals/rules 全局配置
