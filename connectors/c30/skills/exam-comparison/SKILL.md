---
name: exam-comparison
display_name: 多场考试对比
display_name_en: Compare Multiple Exams
description: 当用户需要在 iClass30 比较 2 至 10 场考试、分析共同学生进退或固定群体趋势，并且只要对话里的即时数字时，核对已发布报告和学科班级权限，再调用考试对比工具；要整套可离线网页请改用 learning-portal。
description_zh: 基于共同有效学生的得分率对比多场考试，说明百分点变化和样本覆盖率；网页版整套交付走 learning-portal。
description_en: Compare multiple exams using common valid students, score rates, percentage-point changes and sample coverage; use learning-portal for a full offline site.
version: 2.1.0
author: iClass30
---

# 多场考试对比

使用 `c30` 的 `compare_exams` 工具。先在 WorkBuddy 完成浏览器登录授权，再通过 `list_learning_reports` 确定已发布考试，用 `get_exam_report_options` 获取可访问学科和班级。

## 什么时候不该用本技能

用户要求网页、门户、图表名单或执行表时使用 `learning-portal`。两者共用有效成绩与共同学生算法，但门户年级趋势额外使用80%参测规模筛选；本工具使用全部可分析考试，按 includedExamIds、excludedExams 和 comparisonScope 解释范围差异。本工具最多10场，只返回对话中的数字。

同一轮回答里不要既给 `compare_exams` 的数字又给门户的数字，两套来源同一指标一旦对不上就无法解释。

## 参数

| 参数 | 类型与要求 |
| --- | --- |
| `examIds` | 必填 int[]，2–10 个用户明确指定或已确认的不同考试 ID；不能用名称代替 ID |
| `subjectId` | 必填 string，所有考试均包含且有访问权限的具体学科 ID；不支持 `all` |
| `classId` | 可选 string；指定时该班级必须在每场考试中可访问且有统计；省略时使用各场允许访问的班级成绩 |

考试须来自同一学校和年级。服务按考试日期排序，对比不会改变当前已选考试。只纳入已完成统计且有效的成绩，排除缺失成绩、非有效类型和零满分记录；原始零分仍是有效成绩。

## 执行与解释

先核对当前学校，未选校或需要切校时使用 `list_schools` 和 `select_school`。考试对比只能使用当前学校的考试；切校后重新查找考试，不混用其他学校的 ID。

1. 先列出考试名称、日期和 ID；名称或时间范围有歧义时让用户确认。明确指定的考试范围直接采用，不能自行替换为其他考试。
2. 确认具体学科及班级范围，再调用 `compare_exams`。
3. `exams` 描述各场有效人数、排除人数、均分、平均得分率和分布。各场整体人数可能不同，不能直接把整体均分变化解释为同一批学生的进退。
4. `adjacentComparisons` 与 `overallComparison` 描述共同有效学生。报告共同学生人数、前后平均得分率、`changePercentagePoints`、提高或下降至少 5 个百分点的人数，以及前后样本覆盖率。
5. `fixedCohortCount` 与 `fixedCohortTrend` 使用全部可分析考试的有效学生交集。固定群体为 0 时，明确不能据此判断趋势。
6. 同时说明 `excludedExams` 和 `message` 中的数据限制。没有共同学生或指标为 null 时说明不可比，不把 null 改成 0。

返回的平均得分率、分布占比和覆盖率是比例；`changePercentagePoints` 是百分点。不同满分通过每个学生的得分/满分进行换算后再平均；不能用总均分除以某个统一满分替代。附加分可能使得分率超过 1，沿用工具结果。

比较结果仅描述这些考试及可访问学生的表现。试卷难度、考试内容、参测群体和班级变化都会影响结果，不能直接声称变化就是教学增值或教学效果的因果证明。

## 示例

用户：“对比我班最近三场数学考试，看看学生进退。”

查询该范围的已发布报告，按日期匹配三场考试，确认实际学科和班级 ID，然后调用 `compare_exams`。回答依次说明各场样本、相邻考试共同学生的百分点变化、首末对比、三场固定群体趋势和覆盖率限制。所有统计数字使用工具实际返回的数据。

## 错误恢复

输入不足 2 场、超过 10 场、重复 ID 或 `subjectId=all` 时更正参数。学校、年级、学科或班级范围不一致时重新查询选项并缩小到允许对比的范围，不擅自跨校或替换学科。重复学生数据等一致性错误按工具提示报告，请用户检查考试系统；不要自行去重以得到看似正常的结果。登录失效时在 WorkBuddy 重新授权，超时或服务不可用时稍后重试。
