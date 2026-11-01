---
name: published-learning-reports
display_name: 查询已发布学情报告
display_name_en: Find Published Learning Reports
description: 当用户需要在 iClass30 查询已发布学情、查找考试或选择当前考试时，先核对登录账号，再从报告中心查找有权限的已发布报告。
description_zh: 查询已向当前账号发布的学情报告，并根据真实考试 ID 选择报告。
description_en: Find learning reports published to the current iClass30 account and select an exam using its returned ID.
version: 2.1.0
author: iClass30
---

# 查询已发布学情报告

使用 `c30` 连接器的 MCP 工具。它连接正式系统，数据和账号均属于正式环境。首次使用由 WorkBuddy 打开浏览器，通过考试系统登录及同意授权。不要要求用户把密码、SSO 票据或令牌发到对话中。

## 查询流程

1. 调用 `get_current_user` 查看已授权用户和当前学校，返回 `id`、`name`、`schoolId`、`schoolName`、`userType`、`adminType`。学校为空或用户要求切校时，先用 `list_schools` 查找可访问学校，再用其返回的 `id` 调用 `select_school`；多个同名学校须确认。切校清空已选考试，学校选择仅属于当前连接，不随网页切校变化。
   `name` 是账号显示姓名，不能据此推断角色或权限；运营账号也可查询所属学校的学情。网页登录换号不会更换连接器账号；账号不对时，在 WorkBuddy 重新授权并在授权页点击「切换登录账号」，重新登录后确认姓名、账号 ID 和身份，再同意连接。返回后重新核对 `id` 和 `name`；若仍返回旧账号，删除旧连接并重新添加。不要用直接浏览器查询代替连接器的账号和权限核对。
2. 用户查询学情时调用 `list_learning_reports`；它查询报告中心中已向当前账号角色发布的报告。不要用考试管理列表可见、考试级发布标记或统计完成状态代替报告发布权限。
3. 从返回的 `reports` 中提取 `exam.id`、`exam.name`、`exam.examTime`、年级、可访问学科及班级。`markingInProgress=true` 时说明报告仍在阅卷，统计可能更新。
4. 报告名称有歧义时列出候选并让用户确认；用户明确指定唯一考试或报告时，可直接使用其 ID 查询。需要保存当前考试时调用 `select_exam`。
5. 后续学情分析先调用 `get_exam_report_options` 读取真实学科和班级 ID。不要从名称猜测 ID；仅使用 `select_school` 切换服务端校验过的学校，不得指定账号或角色来扩大权限。

## 工具参数

用户明确要求“查询并选择考试”时，可在 `list_learning_reports` 加 `selectIfUnique=true`。仅第一页、`hasMore=false` 且完整结果唯一时，服务保存选择并返回 `selectedExamId`，后续查询可省略考试 ID。其他情况根据 `selectionMessage` 让用户确认候选，再调用 `select_exam`；不要把单页唯一当成全部结果唯一。普通查询省略该参数，已有选择不会被改动。`selectedExamId=null` 表示本次未保存选择，可用 `get_selected_exam` 核对当前状态。

| 工具 | 参数及默认值 | 返回内容 |
| --- | --- | --- |
| `get_current_user` | 无 | 已授权用户和学校 |
| `list_schools` | `page`: int=1；`pageSize`: int=20，1–50；可选 `keyword`: string，最多 100 字 | `schools`（每项为 `id`、`name`）、`page`、`pageSize`、`hasMore` |
| `select_school` | 必填 `schoolId`: string，使用学校列表返回的 `id` | 当前学校的 `id`、`name`；切校后需重新查询考试 |
| `list_learning_reports` | `page`: int=1；`pageSize`: int=20，1–50；可选 string：`keyword`、`gradeId`、`subjectId`、`classId`、`schoolYearId`、`campusCode`、`categoryId`；可选 int：`enrollmentYear`；`selectIfUnique`: bool=false | `reports`、`page`、`pageSize`、`hasMore`、`message`、`selectedExamId`、`selectionMessage` |
| `select_exam` | 必填 `examId`: int，使用查询返回的正整数 ID | 当前所选考试的 ID、名称、学校、年级、学科和日期 |
| `get_selected_exam` | 无 | 已选考试；未选择时返回 `selected=false` 和提示 |

`keyword` 最多 100 字。`schoolYearId` 是系统学年 ID，不能使用“2026-2027”等展示名称代替；它与 `enrollmentYear` 互斥。`classId` 支持行政班和分层班，必须来自当前账号可访问的数据。

服务先按上游分页再过滤权限，因此 `reports=[]` 且 `hasMore=true` 时仍可继续下一页。不能用空页直接推断没有已发布报告。遵循用户筛选范围，不返回未授权记录或总数。

`select_exam` 只保存当前 OAuth 连接的考试选择，不修改考试成绩或业务数据。显式向分析工具传 `examId` 不会改变当前选择；`get_selected_exam` 会重新核对权限。

## 示例

用户：“找出最近已发布的期中学情报告。”

先调用 `get_current_user`，再调用：

```json
{"keyword":"期中","page":1,"pageSize":20}
```

该 JSON 是 `list_learning_reports` 的参数。用真实返回的考试名称、日期和 ID 列出候选；选择确认的 ID，再读取学科、班级选项。示例没有预置考试、学校或班级 ID。

## 错误恢复

登录失效或权限错误时，让用户在 WorkBuddy 重新连接并完成浏览器授权。无报告数据时说明当前页或当前范围无数据，按 `hasMore` 决定是否继续。参数错误时更正页码、ID 或互斥筛选项。超时或服务不可用时稍后重试；不要通过更换账号参数、旁路令牌或直接请求数据库绕过工具权限。
