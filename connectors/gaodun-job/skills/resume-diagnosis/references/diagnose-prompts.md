# 诊断 Prompt（12 个字段）

> **Prompt 原文（执行权威）**：`references/diagnose-prompts.json`（`{dataFieldCode: {moduleCode, moduleName, promptId, prompt}}`）——`resume_pipeline.py emit-llm-tasks` 从该 JSON 按需逐字注入任务单，**模型不需要读本文件来执行**。本文件只记录调用协议与判定纪律，供排查与同步配置时对照。

---

## 调用协议

**参数组装**：`botId` = 评分配置的 `diagnoseBotId`；`prompt` = `diagnosePromptMap[dataFieldCode]` 对应的 Prompt 原文（按字段取）；`content` = **只传字段原始值**，不拼字段名、不加分隔符。

线上是**每个有值字段各调一次 LLM（多条经历多次调用、共用同一份 Prompt）**；本 skill 由 `emit-llm-tasks` 组装成单次批量任务单——每次调用的 (system prompt, user 消息) 二元组逐字不变、条目间互不影响，判定结果与逐条独立调用等价，只是把 N 次串行推理合并为 1 次（提速关键）。

**LLM 输出格式**（由 Prompt 末尾 OutputFormat + Addition 约束）：

| 情况 | 单次调用的输出 | 处理结果 | 批量任务单对应 |
|---|---|---|---|
| 满足 Rules | 纯文本 `暂无修改建议` | 解析不出 `suggestion` -> 返回 null，**不产生诊断明细** | 该任务**跳过不写**进 suggestions |
| 内容与本字段无关 | JSON `{"suggestion":"请认真完善哦～"}` | 产出 DESCRIPTION_SUGGEST 明细 | 记入 suggestions |
| 不满足 Rules | JSON `{"suggestion":"1. ...\n2. ..."}` | 产出 DESCRIPTION_SUGGEST 明细 | 记入 suggestions |

> ⚠️ **判定纪律（减少与线上 GPT 的判定分歧）**：判"暂无修改建议"前，必须逐条对照 Prompt 中的 Rules，内部列出每条是否明确满足；**只有所有 Rules 都明确满足**才输出"暂无修改建议"，任何一条存疑/不满足都必须给出建议 JSON。线上 GPT 对"量化到位"类描述也常给出进一步建议，过度宽容地判"暂无修改建议"是曾造成明细缺失的真实缺陷。此纪律已固化在 `emit-llm-tasks` 任务单头部。

> 多条明细的"描述建议N："前缀拼装规则见 `diagnosis-categories.md` 类别 3（描述建议文案拼装），由 build-report 代码执行。

## 字段元数据 -> Prompt 映射表（`diagnosePromptMap` 真实 promptId 见 `resume-score-config.json`）

| # | 模块 moduleCode | 字段 dataFieldCode | promptId | 数据源 Prompt 文件 |
|---|---|---|---|---|
| 1 | `internshipExperience` | `internshipExperienceDesc` | 1762 | 简历2.0-诊断-实习经历.txt |
| 2 | `workExperience` | `workExperienceDesc` | 1750 | 简历2.0-诊断-工作经历.txt |
| 3 | `projectExperience` | `projectExperienceDesc` | 1763 | 简历2.0-诊断-项目经历.txt |
| 4 | `practicalExperience` | `practicalExperienceDesc` | 1757 | 简历2.0-诊断-实践经历.txt |
| 5 | `campusActivities` | `campusActivitiesDesc` | 1760 | 简历2.0-诊断-校内工作.txt |
| 6 | `competitionExperience` | `competitionExperienceDesc` | 1758 | 简历2.0-诊断-比赛经历.txt |
| 7 | `trainExperience` | `trainDesc` | 1759 | 简历2.0-诊断-培训经历.txt |
| 8 | `hobbySpeciality` | `hobbySpecialityDesc` | 1761 | 简历2.0-诊断-爱好特长.txt |
| 9 | `selfEvaluation` | `selfEvaluationDesc` | 1764 | 简历2.0-诊断-自我评价.txt |
| 10 | `applicationReason` | `applicationReasonDesc` | 1765 | 简历2.0-诊断-应聘理由.txt |
| 11 | `careerPlanning` | `careerPlanningDesc` | 1766 | 简历2.0-诊断-职业规划.txt |
| 12 | `suitableJob` | `suitableJobDesc` | 1767 | 简历2.0-诊断-适合的工作.txt |

**未启用 Prompt 的描述字段**（`diagnosePromptMap` 不包含，finalize 的 suggestTargets 不会产出）：
- `educationExperienceDesc`（专业课程）- 未配置 prompt
- `rewardRecords` 子模块字段 - 未配置

## 已知原文 quirk（原样保留，不修正）

- **校内工作 prompt**（promptId 1760）绑定的实际是 `campusActivities` 模块；其 Addition 3 笔误为"实践经历"而非"校内活动/工作"——JSON 中按原文保留。
- **爱好特长 prompt**（1761）的 `## Rules：` 使用全角冒号（其余 11 份为半角）——JSON 中按原文保留。
- 评分侧"校内活动评分 key 错配"（GPT 返回"校内工作"匹配不上"校内活动"配置键 -> 永不计分）见 `scoring-rubric.md` / `resume-score-config.json`，由 build-report 代码保留。

## 线上配置同步

任一诊断 Prompt 原文变更时：更新 `references/diagnose-prompts.json` 对应条目的 `prompt` 字段（保持逐字），并在 `resume-score-config.json` 同步 promptId。
