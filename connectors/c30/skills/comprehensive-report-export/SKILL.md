---
name: comprehensive-report-export
display_name: 生成综合报告 Excel
display_name_en: Generate Comprehensive Report Excel
description: 当用户需要 iClass30 考试的综合报告、成绩汇总 Excel 或系统同版式导出（得分、赋分或两份）时，先确认统计口径，再按授权生成并给出下载链接。
description_zh: 按授权生成系统同版式综合报告 Excel，含总分分布、班级各科均分、分数段、名次段与成绩单，支持得分与赋分双模板。
description_en: Generate the system-layout comprehensive report workbook for an authorized exam, in raw-score, converted-score or both variants, and return a download link.
version: 2.1.0
author: iClass30
---

# 生成综合报告 Excel

使用 `c30` 连接器的 `generate_exam_report` 工具。它连接正式系统，数据和账号均属于生产环境。 用户要求“把这次考试的综合报告导出来”“按系统那张表生成 Excel”“得分和赋分各要一份”时使用本技能。首次使用由 WorkBuddy 打开浏览器登录并同意授权，不要让用户在对话中提供密码或令牌。

## 产出内容

工作簿包含五张工作表，版式与考试系统下载件一致：总分分布（分数段分布与累计分布两块）、班级各科均分、班级各科分数段（先年级各学科分档，再按学科列班级）、班级各科名次段（总分块在前，各学科块在后）、成绩单（按年级排名升序，含学生与各科分数及排名）。

- 分档与占比、名次段截断、“缺考”与“--”规则沿用系统统计结果：占比分母是该范围的实考人数，学科满分不同导致档数不同时按最宽学科对齐，不足的档位显示“--”。
- `scoreType=score` 为得分版（卷面分与系统排名），`rule` 为赋分版（换算分与换算排名），默认 `both` 一次生成两份。
- 赋分版只包含 `ruleEnabled=true` 的学科；未启用赋分、无权限或无统计的口径逐项出现在 `unavailable` 中，不得补零分或虚构。

## 流程

1. `get_current_user` 核对账号与学校；需要切校时用 `list_schools` + `select_school`（切校会清空已选考试）。
2. 确认考试：`list_learning_reports` 查已发布报告，或沿用已选考试；有歧义时让用户确认 ID。
3. `get_exam_report_config` 核对口径。includesTotalScore=false时说明总分表组不会输出；convertedAvailable=false时按message解释未启用赋分、缺少统计或权限限制，不能一律归因于未配置。subjects[].classes按学科给出班级及任课教师，不能把不同学科班级范围合并用于取数。
4. 调用 `generate_exam_report`，按用户要求传 `scoreType`；用户没有明确时保持默认 `both`。
5. 用 `reports[]` 的 `fileName`、`sheetCount`、`studentRows`、`expiresAt` 说明生成了什么、覆盖多少学生、链接何时失效，并把 `downloadUrl` 原样给出。`unavailable` 与 `message` 如实转述。

## 参数与返回

| 工具 | 参数 | 返回 |
| --- | --- | --- |
| `generate_exam_report` | 可选 `examId`: int；可选 `scoreType`: string，`score` / `rule` / `both`（默认 `both`） | `exam`、`reports[]`（`reportId`、`scoreKind`、`fileName`、`downloadUrl`、`expiresAt`、`sheetCount`、`studentRows`）、`unavailable[]`、`message` |

## 下载链接安全

`downloadUrl` 是持有即可重复下载的授权凭据，只在当前对话给出。expiresAt 表示文件留存截止时间，授权到期或撤销可能让链接更早失效。用 `get_generation_status(jobId=reportId, type=report)` 核对文件，无需重复生成。

成绩单包含学生姓名、学号与分数等个人信息，使用范围不超出该账号授权的班级与学科；跨校、跨班引用或超出权限汇总前先说明限制。

## 边界

生成只读取系统统计并产出文件，不修改业务数据。未配置存储时说明限制，不绕过工具取数。用户只要数字时用 `query_exam_report`；当前栏目为得分口径，不能解释为赋分。

## 错误恢复

提示“请先选择考试”时先查询并 `select_exam`；提示登录失效时在 WorkBuddy 重新连接授权；报“该考试尚未完成成绩统计”时说明需等系统统计完成，不猜测结果；生成失败可稍后重试，反复失败时记录 `unavailable` 与 `message` 供排查，不更换账号规避权限。
