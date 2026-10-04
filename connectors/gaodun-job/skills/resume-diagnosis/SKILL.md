---
name: resume-diagnosis
display_name: 简历诊断
display_name_en: Resume Diagnosis
description: 用于诊断、评审或评分整份简历。当用户要求「诊断简历」「简历有什么问题」「看看简历哪里要改」「简历打分」「评审简历」「resume review」，或上传 PDF/DOCX 并要求分析问题、给出评分或修改建议时触发。输出 3 类诊断（NO_DATA / NO_FILL / DESCRIPTION_SUGGEST）和 6 维评分（简历完整度 / 经历描述 / 学习能力 / 专业能力 / 创新领导力 / 职场能力），诊断与评分规则及配置见 `references/`，全程由确定性脚本 + 一次批量 LLM 推理完成。仅诊断、评分和提出建议，不直接重写整份简历或生成优化版；用户明确要求改写、润色、优化内容或生成新版简历时，改用 resume-ai-help。
description_zh: 用于诊断、评审或评分整份简历。当用户要求「诊断简历」「简历有什么问题」「看看简历哪里要改」「简历打分」「评审简历」，或上传 PDF/DOCX 并要求分析问题、给出评分或修改建议时触发。输出 3 类诊断（NO_DATA / NO_FILL / DESCRIPTION_SUGGEST）和 6 维评分（简历完整度 / 经历描述 / 学习能力 / 专业能力 / 创新领导力 / 职场能力），诊断与评分规则及配置见 `references/`，全程由确定性脚本 + 一次批量 LLM 推理完成。仅诊断、评分和提出建议，不直接重写整份简历或生成优化版；用户明确要求改写、润色、优化内容或生成新版简历时，改用 resume-ai-help。
description_en: Use when the user asks to diagnose, review, evaluate, or score a complete resume, including requests such as "resume diagnosis", "what is wrong with my resume", "review my resume", "resume score", or feedback on an uploaded PDF/DOCX. It produces 3 diagnosis categories (NO_DATA / NO_FILL / DESCRIPTION_SUGGEST) and 6 scoring dimensions (completeness / experience descriptions / learning ability / professional ability / innovation and leadership / workplace ability) from its own bundled rules and configuration. This skill analyzes, scores, and recommends changes but does not rewrite the full resume or generate an optimized version. If the user explicitly asks to rewrite, polish, optimize, or produce a revised resume, use resume-ai-help instead.
category: 15-Education
version: 2.0.2
author: niemingjie
---

# 简历诊断 Skill (Resume Diagnosis)

## Overview

本 skill 对整份简历输出**诊断**与**评分**：

- **诊断（3 类问题）**：`NO_DATA` / `NO_FILL` / `DESCRIPTION_SUGGEST`；
- **评分（6 维分数）**：简历完整度 / 经历描述 / 学习能力 / 专业能力 / 创新领导力 / 职场能力；
- **报告输出**：一份 HTML 诊断报告（`score` / `beatPercent` / `reportDetails`）。

全部规则、配置与 Prompt 原文已落盘到 `references/`；确定性逻辑由 `scripts/resume_pipeline.py` 代码化执行，模型只承担填值与一次批量 LLM 推理。

**性能设计（2026-08-17 提速重构，v2.0）**：模型在整条流水线里只做**两件事、两次推理**——①填值（把原文抄进模板）；②一次性批量 LLM 推理（诊断 + 评分合并成单次）。其余（解析/清洗/评分/报告装配/HTML 渲染/校验）全部由脚本确定性执行。因此：

- 文本提取**不限定文件类型**：默认由模型用 Read 工具直接读取原文；仅当 AI 读不了（如旧版 `.doc` 二进制）时，才用 `extract-text` 兜底。`scripts/resume_pipeline.py prepare` 一次完成「照片检测 + 生成填写模板」，替代原先多次 Bash 往返；
- `scripts/resume_pipeline.py emit-llm-tasks` 把 `suggestTargets` + 评分输入组装成**单份任务单**，每份诊断 Prompt 从 `references/diagnose-prompts.json` 按需逐字注入（不再让模型整份加载 25KB 的 md）；原本逐字段独立 LLM 调用的 (prompt, 值) 二元组逐字不变、互不影响，判定结果与逐条调用**等价**，只是串行 → 批量；
- `scripts/orchestrate.py` 合并「(finalize) → 注入 LLM 结果 → build-report → 渲染 HTML → 校验」为一次调用。

## 触发场景（When to use this skill）

- 用户上传/粘贴简历并请求："帮我诊断"、"简历哪里有问题"、"帮我优化简历"、"简历打分"。
- 用户问"这份简历能过 HR 初筛吗"。
- **不适用**于：纯面试准备、笔试刷题、offer 选择、薪资谈判。

---

## 工作流（Workflow）

### Phase 0：确定 `resumeType`（**不询问、不打断**，从简历内容推断）

| `resumeType` 键名 | 推断条件（按优先级） |
|---|---|
| `havingWorkExperience` | 简历含全职**工作经历**内容 |
| `havingInternshipExperience` | 否则，含**实习经历**内容 |
| `noInternshipExperience` | 否则（无经历或只有校内/实践） |
| `onlineApplication` | **仅当用户明确说"网申"**时使用 |

推断完成后，仅在对话里顺带说明采用了哪种类型（如与用户表述冲突才提醒），不阻塞流程。

> ⚠️ 命令行 `--resume-type` 一律传**键名**，不要传数字（0/1/2/3 会 `KeyError`）。

### Phase 1：解析（AI 读取 + prepare + 模型填值 + 确定性结算）——脚本强制，禁止手算

**第 1 步：读原文 + 生成模板**。

- **文本提取不限定文件类型**：无论 PDF / DOCX / `.doc` / 其他格式，一律先用 Read 工具读取附件原文（AI 提取）；
- 仅当 Read 读不了时（旧版 `.doc` 二进制等），才显式调 `extract-text` 兜底提取文本；
- 纯文本粘贴：直接跳过文件读取；
- 照片检测（idPhoto）由脚本对原始字节判定（魔数 / docx media），与文件类型无关。

```bash
# ① 文本（AI 提取）：模型用 Read 工具读原文，不限定文件类型；
#    Read 读不了时兜底：
#    PYTHONDONTWRITEBYTECODE=1 python scripts/resume_pipeline.py extract-text \
#      --resume-file "<用户上传的文件路径>" --out tmp/resume.txt

# ② 照片检测 + 模板（一次 Bash 调用；有附件时传 --resume-file，纯文本粘贴可省略）
PYTHONDONTWRITEBYTECODE=1 python scripts/resume_pipeline.py prepare \
  --resume-type <resumeType> --resume-file "<用户上传的文件路径>" --out tmp/prepare.json
# 纯文本粘贴时
PYTHONDONTWRITEBYTECODE=1 python scripts/resume_pipeline.py prepare \
  --resume-type <resumeType> --out tmp/prepare.json
```

`tmp/prepare.json` 含：`idPhoto`（脚本已按魔数/媒体判定，含照片填 `<已上传证件照>`，否则 `""`）、`template`（全模块×全字段填写模板）。**文本读取与照片判定都不再需要手工处理。**

**第 2 步：模型填值（模型在解析阶段的唯一职责）**。把 `template` 复制一份并逐字段填值，用 **Write 工具**写成 `tmp/filled.json`（不要用 `python -c json.dump`，Write 工具 UTF-8 无引号污染）：

- 逐字段照抄原文，一个字段都不许跳过；原文没有的字段保持 `""`——空白是合法值，由脚本决定是否记 NO_FILL，**不要编造，也不要因"觉得不可见"而删字段**。
- 经历类模块按原文条数增加 `records` 数组元素（如 8 条校内活动 = 8 个 records 元素），每条字段齐全，缺值留空。
- 时间字段照抄原文（`2023.09` / `2023年9月` / `至今` 均可），归一化由脚本完成。
- 特别注意别漏：基本信息的 `workCity`（期望城市）/`position`（应聘岗位）；实习/工作的 `xxxPostName`/`xxxDepartmentName`；`hobbySpecialityDesc`、`campusActivitiesDesc`、`practicalExperienceDesc` 等描述正文（哪怕很短也是"有值"）；`campusActivities`/`rewardRecords` 虽配置 hidden=true 但原文有内容就必须填（脚本会判 SHOW）。

**第 3 步：确定性结算 + 生成 LLM 任务单（一条 Bash 调用）**：

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/resume_pipeline.py finalize \
  --resume-type <resumeType> --filled tmp/filled.json --out tmp/finalized.json && \
PYTHONDONTWRITEBYTECODE=1 python scripts/resume_pipeline.py emit-llm-tasks \
  --finalized tmp/finalized.json --out tmp/llm_tasks.md
```

`finalize` 确定性执行：解析清洗（技能合并/教育前缀/枚举归一化/时间归一化）→ 状态与排序 → 可见字段过滤 → NO_FILL / NO_DATA 判定 → 5 个确定性评分维度。`emit-llm-tasks` 输出**单份任务单**（A 诊断 + B 评分 + 输出协议）。**模型不得自行重算或重跑任何确定性逻辑。**

### Phase 2：单次批量 LLM 推理（诊断 + 评分）

读 `tmp/llm_tasks.md`，**一次推理**完成全部任务，把结果用 Write 工具写成 `tmp/llm.json`：

```json
{"suggestions": [{"moduleCode": "...", "fieldCode": "...", "dataSort": 1, "suggestion": "..."}],
 "score": {"实习经历": 82, "自我评价": 70}}
```

- 判定纪律（任务单头部已固化）：逐条对照 Rules，全部明确满足才判"暂无修改建议"（跳过不写），任何一条存疑/不满足都给建议；与本字段无关给「请认真完善哦～」。
- `dataId` 不需要（build-report 只按 moduleCode+fieldCode 分组、dataSort 排序）。
- 评分按任务单中评分 Prompt 的 OutputFormat，键用其中文模块名原样，无内容模块给 0。

### Phase 3：报告装配 + HTML 交付（一条 Bash 调用）

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/orchestrate.py \
  --resume-id <简历标识> --finalized tmp/finalized.json --llm tmp/llm.json \
  --html-out 简历诊断报告_<resumeId>.html --tmp-dir tmp
```

`orchestrate.py` 完成 build-report（经历描述分折算/求和/beatPercent/描述建议编号/reportDetails 装配）→ 渲染 HTML → 占位符校验，输出到 stdout 的 JSON 摘要（score/beatPercent/模块数/明细数）。成功后自动清理 `tmp/`（**零残留**）；失败时保留 `tmp/` 便于修正 llm.json 重跑。

生成后调用 `present_files` 将 HTML 报告交付给用户。

> 接口外扩展（综合评价/整改计划/求职赛道建议/改写草稿）仅在用户明确要求时追加到 HTML 报告末尾，并标注"以下为扩展分析"（见 diagnose-output-template.md 第 4 节）。

---

## 交付纪律（模型执行）

- 中间文件（prepare/filled/finalized/llm_tasks/llm.json）只放 `tmp/`，成功后由 orchestrate 整体清理，**不残留**。
- 最终**只产出 1 份 HTML 报告文件**（`简历诊断报告_<resumeId>.html`）并用 `present_files` 交付；不输出 markdown/文本版报告。
- 所有 `python scripts/...` 调用前缀 `PYTHONDONTWRITEBYTECODE=1`（避免生成 `__pycache__`）。

---

## 资源说明（简）

| 文件 | 用途 |
|---|---|
| `scripts/resume_pipeline.py` | 确定性流水线：prepare（照片检测+模板）/ extract-text（兜底提取，仅 AI 读不了时用）/ emit-template / finalize / emit-llm-tasks / build-report |
| `scripts/orchestrate.py` | 报告装配 + HTML 渲染 + 校验，一次调用 |
| `references/diagnose-prompts.json` | 12 份诊断 Prompt 原文（执行权威，`emit-llm-tasks` 按需注入） |
| `references/resume-module-config.json` | 模块+字段权威配置（4 种 resumeType 全量 + visibleModuleMap） |
| `references/resume-score-config.json` | 评分权威配置（scoreList / moduleScoreMap / 阶梯表 / diagnosePromptMap / scoreGptConfig） |
| `references/resume-score-prompt.txt` | 经历描述评分 Prompt 原文（promoteId=1640） |
| `references/analysis-resume-rules.md` | 解析与可见性规则（清洗、起止时间、状态赋值、模块 sort、枚举归一化） |
| `references/diagnosis-categories.md` | 3 类诊断判定 + 描述建议文案拼装 |
| `references/scoring-rubric.md` | 6 维评分公式、阶梯表、学历映射 |
| `references/diagnose-prompts.md` | 调用协议 + 判定纪律 + 映射表（Prompt 原文见 JSON） |
| `references/diagnose-output-template.md` | 报告结构、话术模板、排序规则、HTML 占位符清单 |
| `assets/diagnose-report-template.html` | HTML 交付模板（静态占位符 `{{...}}`，无脚本） |

**执行规则/红线、已知 quirk 与排查口径：见 `references/troubleshooting.md`。**

## 局限与免责

- 本 skill 不读取任何线上服务的真实简历数据，所有数据来自用户输入/上传。
- 评分/诊断所需配置已全部落盘；线上配置若变更，需同步 `resume-score-config.json` / `resume-module-config.json` / `diagnose-prompts.json` / `resume-score-prompt.txt`。
- LLM 评分具有主观性；严禁把诊断报告中的"问题清单"直接作为淘汰候选人的依据，仅供优化参考。
