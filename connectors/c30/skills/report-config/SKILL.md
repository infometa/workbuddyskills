---
name: report-config
display_name: 获取报告统计口径
display_name_en: Read Report Statistics Config
description: 当用户询问 iClass30 考试的分数段怎么分、名次段档位、一分五率阈值、满分、赋分是否启用或可访问班级与任课教师时，读取该考试报告的统计口径再回答。
description_zh: 读取考试的分数段步长、名次段档位、五率阈值、学科满分与赋分启用情况、可访问班级及教师。
description_en: Read score-band steps, rank bands, five-rate thresholds, subject full marks, converted-score availability and permitted classes for an exam report.
version: 2.1.0
author: iClass30
---

# 获取报告统计口径

使用 `c30` 连接器的 `get_exam_report_config` 工具。它连接正式系统，数据和账号均属于生产环境。 首次使用由 WorkBuddy 打开浏览器登录并同意授权；不要让用户把密码、SSO 票据或令牌发到对话中。

回答“这次考试分数段是按多少分一档”“赋分开了没有”“优秀率及格线是多少”“哪些班哪些老师能看”这类问题时使用本技能。它是生成综合报告前的口径确认步骤，也单独用于解释系统统计结果。

## 流程

1. 调用 `get_current_user` 核对账号与当前学校；学校为空或用户指定其他学校时，先用 `list_schools` 再用 `select_school`。
2. 确认考试：用 `list_learning_reports` 查询已发布报告，或沿用当前连接已选考试（`get_selected_exam` 可核对）。名称有歧义时列出候选让用户确认，不能猜 ID。
3. 调用 `get_exam_report_config`（可省略 `examId` 使用已选考试）。
4. 按返回值解释，不自行设定分档或阈值：
   - `subjects[]`：`subjectId`、`subjectName`、`fullScore`（得分满分）、`ruleFullScore`（赋分满分）、`ruleEnabled`（该学科是否启用赋分）及该学科的 `classes[]`。有总分权限时首项为 `subjectId="all"` 的总分。
   - `segmentStep`：分数段步长（分）。总分满分不低于 230 分时系统按 20 分一档，首档吸收不足一档的余量，标签形如 `(750,740]`；满分以下按同一档距向下切到 `(20,0]`。
   - `rankBands[]`：名次段档位，`start=-1` 表示“第 `end` 名”，其余为 `[start,end]` 闭区间；生成报告时累计到覆盖全年级人数的档位后结束。
   - `rateThresholds[]`：各学科（含总分）的一分五率阈值，`startPercent`/`endPercent` 是满分的百分比；高分率、优秀率、优良率、及格率、不及格率、低分率的名称与阈值沿用系统配置，缺省时使用系统默认。
   - `classes[]`：当前账号在该考试中可访问的班级及班主任/任课教师显示名。
   - `includesTotalScore`：false 表示账号不具备该考试全部学科权限，总分表组不可输出。
   - `convertedAvailable` 与 `convertedSubjectIds`：赋分版综合报告可包含的学科。
5. `message` 非空时如实转述（例如未配置赋分、口径缺失）。字段缺失就说明缺失，不得编造分档、阈值或教师姓名。

## 参数与返回

| 工具 | 参数 | 返回 |
| --- | --- | --- |
| `get_exam_report_config` | 可选 `examId`: int，省略时使用当前已选考试 | `exam`、`subjects`、`classes`、`includesTotalScore`、`segmentStep`、`rankBands`、`rateThresholds`、`convertedAvailable`、`convertedSubjectIds`、`message` |

配置查询只读元数据、配置和授权汇总，不读取学生成绩；统计未完成时仍返回配置，并通过 message 说明生成限制。ruleEnabled 表示配置已启用赋分，convertedAvailable 表示已有可输出的授权统计，两者不能混用。配置与报告查询统一用 subjectId=all 表示总分，具体学科直接使用返回的 subjectId。缺失教师姓名不得猜测；修改配置须在考试系统中操作。

## 示例

用户：“这份成绩表按多少分一档？政治的优秀线是多少？”

先确认考试，再调用 `get_exam_report_config`，用返回的 `segmentStep` 与 `rateThresholds` 回答；同时说明总分档首列是满分人数、其余档为区间 `(start,end]`，占比分母是该范围实考人数。

## 错误恢复

未授权或登录失效时让用户在 WorkBuddy 重新连接；提示“请先选择考试”时先查询并 `select_exam`；报告未发布或无权限时按 `message` 与 `unavailable` 说明，不更换账号或旁路查询。
