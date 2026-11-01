---
name: learning-portal
display_name: 学情门户生成
display_name_en: Generate Learning Portal
description: 当用户需要把多场考试的学情做成可离线打开、能按自己方式微调板块的整套网页（历次对比、班级诊断、一生一案、题目讲评、四周执行表）时，核对考试与学科权限后调用 generate_portal。
description_zh: 按授权生成八页离线学情门户，交付网页而不是对话里的数字表格，并支持用 config.js 微调板块与口径。
description_en: Build an eight-page offline portal (trend, class diagnosis, per-student cases, question review, four-week plan) scoped to the authorized role, customizable through config.js.
version: 2.1.0
author: iClass30
---

# 学情门户生成

使用 `c30` 的 `generate_portal` 与 `get_generation_status` 工具。先完成浏览器登录授权，再用报告列表和选项确认考试、学科与班级。

## 什么时候用门户，什么时候用 compare_exams

用户要的是**看得见的整套交付**——"生成一个网站/网页""给教研组或班主任传阅""把这几场的历次对比做成页面""要图、要名单、要执行表""能自己删板块改口径"——用本技能。

用户只要**对话里的即时数字**——"这三场谁进步了""共同学生涨了几个百分点""固定群体趋势怎么样"——用 `exam-comparison`（`compare_exams`），它 2–10 场直接返回数值，不生成文件。

历次对比位于 `exams.html` 与 `index.html`。共同有效学生、得分率和±5百分点算法共用；门户年级趋势额外筛选参测人数达到最大人数80%的考试，`compare_exams` 使用所有可分析考试。按 `comparisonScope` 核对纳入场次，再解释数字。

## 参数

| 参数 | 类型与要求 |
| --- | --- |
| `examIds` | 必填 int[]，1–20 个用户确认过的不同考试 ID，必须同一年级 |
| `subjectId` | 必填 string，具体学科 ID；不支持 `all`，且每场考试都须已向当前角色发布该学科报告 |
| `background` | bool，默认 true；先返回 jobId，通过状态工具等待完成 |

生成物是八个页面：`index.html` 指挥台（脉搏、增量地图、分层流向、知识图谱、行动纲领、数据缺口）、`exams.html` 考试轴与双场/相邻对比、`classes.html` 班级诊断、`students.html` 分层名册与预警、`student.html` 一生一案、`questions.html` 题目讲评、`question.html` 单题复盘、`plan.html` 四周执行表。学生个案与题目详情按需加载，交付目录约 60–70 个文件。

## 执行与解释

1. 先核对当前学校与角色；未选校时用 `list_schools` 和 `select_school`。
2. 列出候选考试的名称、日期、ID 让用户确认范围，再确认具体学科；不要替用户扩大或替换考试。
3. 调用 `generate_portal(background=true)` 保存 jobId。queued/running 时用 `get_generation_status(jobId, type=portal)` 等待，合理间隔查询。failed/cancelled 时解释 error 和 errorCode，再按修正范围重新提交。role 在权限核验后确定，不能由用户指定以扩大范围。
4. 只有 done 时交付 `indexUrl` 和 `zipUrl`。链接是持有即可重复下载的授权凭据，授权到期或撤销可能早于 expiresAt 失效，只在当前对话给出。门户含学生信息，仅限账号授权范围内使用。
5. 用 `students`、`questions`、`exams`、`files`、`bytes`、`baselineName` 说明这次实际覆盖了什么范围；`message` 与 `Notice` 里的数据限制（未扫描、缺考、题目标签缺失）如实转述，不得编造。
6. 用 `get_generation_status(jobId, type=portal)` 核对有效性。found=false 表示过期、授权失效或不属于当前连接。任务默认处理期限10分钟；服务重启中断的任务超过 processingDeadlineAt 会标为失败，可重新提交。

## 微调与裁剪

生成后用户要改样式、删板块、改分层线或阈值，改的是交付目录里的 `config.js`，刷新即生效，不需要重新生成，也不会碰到 `data/` 里的学生数据：

- `layout` 按页填板块 id 数组——删掉一个 id 整段消失，改顺序就改页面结构；留空 `nav` 时按角色默认导航。
- `filters` 的 `examIds`/`classIds` 全站生效，`hidePending` 控制未完成统计的考试是否进分析。
- `rules.bands` 改四档分层线，`movePp`/`warnPp` 改升降与波动预警判定阈值（百分点）。
- `copy` 改标题、页脚、警示文案、术语解释和各层教学提示。

`role` 由服务端写入，用户要求改 `role` 以看到更多学生时拒绝，并说明范围只由账号权限决定。

## 示例

用户："把这学期四次月考做成一个网页，历次对比要能看趋势，板块我自己删减。"

用 `list_learning_reports` 找出四场同年级月考并确认 ID，用 `get_exam_report_options` 确认学科，调用 `generate_portal`。交付 `indexUrl`，说明历次对比在 `exams.html` 与 `index.html` 的脉搏板块，并告知改 `config.js` 的 `layout` 即可删板块、刷新生效。

## 错误恢复

跨年级、具体学科不合法或某场无权限时不交付部分门户。存储未配置或队列已满时说明限制。只有 authentication_required 才要求重新授权；permission_denied 时核对发布范围。已有 jobId 的请求超时先查状态，queued/running 时等待，done 直接交付，failed/cancelled 再重新提交。
