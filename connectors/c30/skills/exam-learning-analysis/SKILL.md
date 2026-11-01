---
name: exam-learning-analysis
display_name: 考试学情分析
display_name_en: Analyze Exam Learning Reports
description: 当用户需要分析 iClass30 考试成绩、一分五率、薄弱知识点、试题、小分表或报告栏目时，使用已发布报告和授权范围内的学科、班级数据给出结论。
description_zh: 分析考试报告的成绩、知识点、试题及 22 个栏目，明确数据单位和缺失情况。
description_en: Analyze exam scores, knowledge points, questions and 22 report sections within the account's authorized scope.
version: 2.1.0
author: iClass30
---

# 考试学情分析

使用 `c30` 的 MCP 工具。用户先通过 WorkBuddy 的浏览器登录授权；尚未确定报告时，先使用已发布学情查询流程。用户明确给出考试 ID 时，可直接把该 ID 传给分析工具，由服务重新验证发布权限。

## 分析流程

先用 `get_current_user` 核对当前学校。学校为空或用户指定其他学校时，使用 `list_schools` 查询、`select_school` 选择已确认的学校；切校后重新查询考试和选项，不能继续使用原学校的考试 ID。

1. 调用 `get_exam_report_options` 获取该考试已发布且可访问的学科和班级 ID、名称。将用户说的学科、班级与返回值匹配，歧义时再请用户确认。
2. 统一调用 `query_exam_report`：一分五率用 `five_rates`，知识点用 `knowledge_analysis`，试题均分及班级得分率用 `question_averages`。`overview` 是另一套概览指标，`question_analysis` 是大小题年级指标，不能替代上述栏目。
3. 用户指定其他报告栏目时，先调用 `list_exam_report_sections` 获取 `section`、`classRequired`、`supportsTotal` 和 `rateUnits`，再调用 `query_exam_report`。
4. 结论附考试名称、日期、学科、班级或可访问班级范围；引用实际返回的指标和样本。报告仍在阅卷时说明统计可能变化；返回 `message` 或缺失数据时明确说明。

需要题干、选项、答案或解析时调用 `get_exam_questions`。可按有权限的考试与具体学科分页读取；筛选 `questionIds` 时使用返回的真实父题、小题 ID 或学生小分表的 `questionId`，不能根据卷面题号猜测 ID。小题查询保留所属大题及关联小题；`hasQuestions` 仅表示试卷关联题库，缺失详情见 `missingQuestionIds`。不要把 `sortOrder` 或题库默认题号当成卷面题号。

## 工具参数与返回

| 工具 | 参数 | 返回内容 |
| --- | --- | --- |
| `get_exam_report_options` | 可选 `examId`: int；省略时使用已选考试 | `exam`、`subjects`；每学科含 ID、名称和可访问 `classes` |
| `get_exam_questions` | 必填具体 `subjectId`: string；可选 `classId`: string、`examId`: int、`questionIds`: string[1–50]；`page`: int=1、`pageSize`: int=10，1–50 | `papers`、`items`、`hasQuestions`、`hasMore`、`missingQuestionIds`、`message`、`ordering`，保留父子题结构 |
| `list_exam_report_sections` | 无 | 22 个栏目及其 ID、名称、班级要求、总分支持和单位 |
| `query_exam_report` | 必填 `section`: string、`subjectId`: string；可选 `classId`: string、`examId`: int；`page`: int=1、`pageSize`: int=20，1–50 | `exam`、`section`、`subjectId`、`classId`、`data`、分页、`hasMore` 和 `message` |
| `get_exam_report_config` | 可选 `examId`: int；省略时使用已选考试 | 各学科得分/赋分满分、`ruleEnabled`、班级与任课教师、`segmentStep`、`rankBands`、五率阈值、`includesTotalScore`、`convertedAvailable`、`message` |
| `generate_exam_report` | 可选 `examId`: int、`scoreType`: string=both（`score`/`rule`/`both`） | `reports`（`reportId`、`scoreKind`、`fileName`、`downloadUrl`、`expiresAt`、`sheetCount`、`studentRows`）、`unavailable`、`message` |

省略 `examId` 要求当前连接已选考试。`subjectId` 和 `classId` 必须使用选项工具返回的 ID。`all` 表示总分，只有选项工具返回该值且栏目 `supportsTotal=true` 时才能使用；知识点、试题专用分析需要具体学科。

## 报告栏目

下表帮助选择；运行时以 `list_exam_report_sections` 返回的要求为准。

| section | 栏目 | 必须指定班级 | 支持总分 |
| --- | --- | --- | --- |
| `overview` | 学情概览 | 否 | 是 |
| `score_card` | 成绩单 | 是 | 是 |
| `five_rates` | 一分五率 | 否 | 是 |
| `subject_comparison` | 学科对比 | 否 | 否 |
| `student_question_scores` | 学生小分表 | 是 | 否 |
| `question_analysis` | 大小题分析 | 否 | 否 |
| `question_averages` | 试题均分与班级得分率 | 否 | 否 |
| `class_group` | 班内小组分析 | 是 | 是 |
| `class_layered` | 班级分层对比 | 否 | 是 |
| `critical_students` | 临界生分布 | 否 | 是 |
| `top_under` | 优困生分布 | 否 | 是 |
| `online` | 上线分析 | 否 | 是 |
| `grade_distribution` | 等级分布 | 否 | 是 |
| `score_segments` | 成绩分段分析 | 否 | 是 |
| `rank_analysis` | 名次分析 | 否 | 是 |
| `boxplot` | 箱线图 | 否 | 是 |
| `paper_quality` | 命题质量 | 否 | 否 |
| `blueprint` | 双向细目表 | 否 | 否 |
| `question_types` | 题型均分 | 否 | 否 |
| `answer_details` | 作答详情 | 是 | 否 |
| `knowledge_analysis` | 知识点分析 | 否 | 否 |
| `paper_comment` | 试卷讲评 | 是 | 否 |

## 综合报告导出

需要统计口径说明时用 `get_exam_report_config`；需要系统同版式的综合报告 Excel（得分/赋分）时改用 `comprehensive-report-export` 技能，先确认口径再生成。两个工具同样遵守当前账号的学校、学科、班级与报告发布权限，未生成的口径按 `unavailable` 如实说明。

## 指标解释

优先遵循工具返回的 `rateUnits`。得分率通常是 0–1 的比例，五率及部分命题指标是百分数，不能混用。

`query_exam_report` 返回 `scoreType=score`，当前栏目只支持得分口径；赋分需求使用综合报告导出技能。一分五率、知识点和试题均分分别查询 `five_rates`、`knowledge_analysis`、`question_averages` 栏目。

学生小分表的 `type=1/2/3` 分别表示未扫描、缺考、批改不完整，`questions=null` 表示缺失，不代表零分。真实零分要保留；满分为 0 时得分率为 null。不要代填小题分数，不要推算工具未返回的学生答案或其他班级信息。

一分五率的名称和阈值沿用学校系统配置。名次分析的人数数组与返回的 `ranges` 一一对应，不自行假定分段。总分及跨学科查询必须满足返回的授权范围。

## 示例

用户：“分析这次考试我班的薄弱知识点，并给出补练方向。”

读取报告选项并匹配用户指定的学科、班级，使用真实返回的 ID 调用知识点分析；如 `hasMore=true`，根据分析范围继续翻页。按实际低得分率知识点列出考频、满分、均分和班级得分率，再提出针对性补练建议。补练建议是分析推论，应与系统统计事实区分。

用户：“查看学生小分表和名次分析。”

先获取栏目列表，分别用 `student_question_scores` 和 `rank_analysis` 查询；小分表必须传实际班级 ID，名次人数结合返回的分段解释。

## 错误恢复

未选考试时先查报告或明确传 `examId`。参数不合法、学科或班级不在权限范围时，重新读取报告选项并更正。登录失效时在 WorkBuddy 重新授权。空数据、未配置报告和超时均按工具提示说明，不能编造补齐，也不能绕过权限直接查询上游。
