---
name: zhihuishu-unified-skill
description: 智慧树教学中心，聚合课程与班级、教学计划、教学观测、学情分析、作业、考试、成绩与考勤、课堂报告与回放、话题通知、分组教学、OBE、题库与试卷、资源库与学习资源的读写能力
description_zh: 智慧树教学中心，聚合课程与班级、教学计划、教学观测、学情分析、作业、考试、成绩与考勤、课堂报告与回放、话题通知、分组教学、OBE、题库与试卷、资源库与学习资源的读写能力
description_en: Zhihuishu Teaching Center aggregating read and write capabilities for courses and classes, teaching plans, teaching observation, learning analysis, homework, exams, scores and attendance, classroom reports and replays, topics and notices, group teaching, OBE, question banks and papers, resource libraries, and study resources.
version: "2.1.0"
author: "智慧树"
---

# 智慧树·教学中心

一个入口聚合 12 个教学专家域的查询与操作能力，按用户意图路由到对应 Tool。

## 能力边界

- Tool 分为查询与写操作两类：`readOnlyHint=true` 为查询、检索与分析；其余为会改变教学数据的写操作。
- 写操作必须先展示目标对象与关键变更，并取得用户明确确认后再执行；用户未确认时只做查询与方案说明。
- 删除、打回、发布、批量导入等操作要说明影响范围；不可恢复的操作还要说明无法撤销。
- 批量写操作必须逐条列出对象，不使用「若干」「全部」等模糊范围，不默认全选。
- 管理入口链接类 Tool 只返回页面链接，不执行页面内操作；页面内的批量处理引导用户跳转完成。
- 身份、学校、助手、Token 由服务端解析，任何 Tool 都不接收这些字段。
- 课程、班级、题目等技术 ID 只用于 Tool 串联，不向用户展示，对用户展示名称。
- 只处理用户真实提出的意图，不主动扩展模块，不批量预取数据。

## 统一前置流程

1. 用 `search_courses` 定位课程。用户未指定学期时不传 `term`，查询全部学期；指定学期时先用 `query_terms` 换算为学期编号再传入。
2. 多个课程候选必须展示名称与学期并等待用户选择，不默认取第一项。
3. 课程确定后仍缺少学期时，用 `query_terms` 展示可选学期并等待选择；向用户只展示学期名称，不展示裸编号。
4. 模块需要班级时，用该模块的班级类 Tool 查询：教学观测用 `query_observation_classes`，训练题库用 `query_training_question_bank_classes`，成绩用 `query_score_students`，分组用 `search_classes`，通用班级与学生用 `search_classes`，班级人员用 `query_students`；多候选同样等待用户选择。
5. 同一轮内后续 Tool 复用已确认的课程、学期、班级，不重复前置；服务端会再次校验归属。
6. 前置查询失败或为空时立即停止并说明，不自动更换课程或学期重试。

## 写操作确认规范

1. 先查询再写入：用查询 Tool 取得真实对象和当前值，展示给用户确认后才调用写操作 Tool。
2. 有预览能力的先预览：`preview_class_student_import`、`preview_score_setting_import`、`analyze_obe_syllabus`、`prepare_question_import`、`query_similar_questions` 的返回必须先给用户确认，再执行对应的导入、保存或删除。
3. 参数以用户确认为准：不擅自补全、不静默修改题量、分值、班级范围或时间。
4. 部分失败按成功与失败分组汇报，未确认的对象不重试；写操作以服务端回查结果为最终状态。
5. 用户只要求「看看」「准备一下」时不执行写操作，只返回查询结果或操作方案。

## Tool 路由

章节按 12 个专家域组织：课程管理、资源库、成绩管理、题库管理、OBE 管理、教学观测、学情分析、学习资源、教学活动、作业管理、考试管理、小组教学。

### 学期、课程与班级

| 意图 | Tool | 类型 |
|---|---|---|
| 查询或换算学期 | `query_terms` | 查询 |
| 定位授课课程 | `search_courses` | 查询 |
| 课程基本信息 | `get_course_basic_info` | 查询 |
| 课程详情（授课课程） | `get_course_teaching_detail` | 查询 |
| 检索归档课程 / 共享课 | `list_archived_courses` / `list_shared_courses` | 查询 |
| 课程概况 | `get_course_overview` | 查询 |
| 查询班级与学生 | `search_classes` | 查询 |
| 查询班级人员 | `query_students` | 查询 |
| 课程标签 / 学生标签 | `list_course_tags` / `query_student_tags` | 查询 |
| 检索学校 / 学校学生 | `search_schools` / `search_school_students` | 查询 |
| 预览学生名单导入 | `preview_class_student_import` | 查询 |
| 生成学生导入模板 | `generate_class_import_template` | 查询 |
| 导出班级学生名单（返回可下载文件信息） | `export_class_students` | 查询 |
| 班级群列表 / 成员 / 消息 | `list_class_groups` / `list_class_group_members` / `list_class_group_messages` | 查询 |
| 教学团队成员 | `query_teaching_team_members` | 查询 |
| 课程 / 班级 / 教学团队管理入口链接 | `get_course_manage_link` / `get_class_manage_link` / `get_teaching_team_manage_link` | 查询 |
| 创建课程 | `create_course` | 写操作 |
| 编辑课程基本信息 | `edit_course` | 写操作 |
| 更新课程基本信息 | `update_course_info` | 写操作 |
| 创建班级 | `create_class` | 写操作 |
| 添加班级学生 | `add_class_student` | 写操作 |
| 模板批量导入班级学生 | `import_class_students_from_template` | 写操作 |
| 执行学生名单导入（需先预览取得任务ID） | `execute_class_student_import` | 写操作 |
| 审核入班申请 | `audit_enrollment_applications` | 写操作 |
| 删除待激活学生 | `delete_pending_students` | 写操作 |
| 创建 / 设置 / 删除课程标签 | `create_course_tag` / `assign_student_tags` / `delete_course_tag` | 写操作 |
| 学生调班 | `transfer_student` | 写操作 |
| 学生退班 | `quit_student` | 写操作 |
| 发送班级群消息 | `send_class_group_message` | 写操作 |
| 发布班级群公告 | `publish_class_group_announcement` | 写操作 |

### 教学计划

| 意图 | Tool | 类型 |
|---|---|---|
| 教学计划结构 | `query_teaching_plan_structure` | 查询 |
| 教学计划关联活动 | `query_teaching_plan_activities` | 查询 |
| 教学计划编辑入口链接 | `get_teaching_plan_edit_link` | 查询 |
| 批量写入教学计划草稿 | `write_teaching_plan_draft` | 写操作 |
| 附件生成教学计划 | `generate_teaching_plan_from_file` | 写操作 |

教学计划的单点增删改优先走 `get_teaching_plan_edit_link` 返回的页面；`write_teaching_plan_draft` 仅在用户已确认完整三级结构后整批写入。

### 教学观测（学情 / 教学双视角）

前置：用 `query_observation_classes` 查询观测班级；用户未明确视角时先询问学情、教学或双视角，「教学概况」「全面观测」「整体数据」默认双视角。

学情数据：

| 意图 | Tool | 类型 |
|---|---|---|
| 查询观测班级 | `query_observation_classes` | 查询 |
| 学习进度（完成率） | `query_learning_progress` | 查询 |
| 学习进度详情 | `query_learning_progress_detail` | 查询 |
| 学习排行榜 | `query_learning_rankings` | 查询 |
| 教学活动完成情况 | `query_teaching_activity` | 查询 |
| 总成绩与等级分布 | `query_total_scores` | 查询 |
| 学习趋势 | `query_learning_trend` | 查询 |
| 知识点掌握 | `query_knowledge_mastery` | 查询 |
| 学习预警 | `query_learning_warnings` | 查询 |
| 课堂互动明细 | `query_learning_lesson_interactions` | 查询 |
| 话题讨论统计 | `query_learning_topic_discussion` | 查询 |
| 作业统计与明细 | `query_learning_homework` | 查询 |
| 考试统计与明细 | `query_learning_exams` | 查询 |
| 能力阶梯达成 / 能力训练 | `query_ability_ladder` / `query_ability_training` | 查询 |
| 智能体教学情况 | `query_agent_teaching` | 查询 |
| 智能体问答概览 | `query_agent_qa_overview` | 查询 |
| 智能体问题类型分布 | `query_agent_qa_question_types` | 查询 |
| 智能体问答趋势 | `query_agent_qa_trend` | 查询 |
| 学生最近提问 | `query_student_questions` | 查询 |
| 学生不满意回答 | `query_dissatisfied_answers` | 查询 |
| 学情综合评价 | `query_learning_evaluation` | 查询 |

教学数据：

| 意图 | Tool | 类型 |
|---|---|---|
| 教学统计概览 | `query_teaching_stats_overview` | 查询 |
| 作业考试发布与完成率 | `query_teaching_homework_exam_stats` | 查询 |
| 课堂互动发布情况 | `query_teaching_lesson_interactions` | 查询 |
| 话题讨论发布情况 | `query_teaching_topic_discussion` | 查询 |
| 课程图谱统计 | `query_course_graph` | 查询 |
| AI 应用与智能体统计 | `query_teaching_agent_ai_stats` | 查询 |

路由规则：

- 泛问「智能体问答情况」时组合调用 `query_agent_qa_overview`、`query_agent_qa_question_types`、`query_agent_qa_trend`；只问热词、类型或趋势时只调用对应 Tool。
- 「学生最近都在问什么」只用 `query_student_questions`；「哪些回答被点踩」只用 `query_dissatisfied_answers`，不与其他模块组合。
- 学情视角的课堂互动用 `query_learning_lesson_interactions`，教学视角用 `query_teaching_lesson_interactions`；话题讨论同理按视角区分。

### 学习分析

| 意图 | Tool | 类型 |
|---|---|---|
| 作业深入分析 | `analyze_homework` | 查询 |
| 考试学情分析 | `analyze_exam_learning` | 查询 |
| 查询作业 | `search_homeworks` | 查询 |
| 查询考试 | `search_exams` | 查询 |
| 训练题库学情 | `query_training_question_bank_learning` | 查询 |
| 训练题库班级 | `query_training_question_bank_classes` | 查询 |
| 训练题库数据概览 | `query_training_question_bank_statistics` | 查询 |
| 训练题库题目列表 | `query_training_question_bank_questions` | 查询 |
| 训练题库详情 | `query_training_question_bank_detail` | 查询 |

学习分析中的观测类 Tool 与「教学观测」共用，见上表；同一轮内不要重复调用。

### 作业管理

前置：先确认课程、学期和作业；涉及学生时再用 `query_homework_completion` 取得真实名单。

| 意图 | Tool | 类型 |
|---|---|---|
| 作业详情与完成情况 | `query_homework_completion` | 查询 |
| 作业交流与回复 | `query_homework_discussions` | 查询 |
| 作业学情 | `query_homework_learning` | 查询 |
| 作业查重报告 / 查重智能体 | `query_homework_similarity` / `query_homework_similarity_agents` | 查询 |
| 作业重做申请 | `query_homework_redo_requests` | 查询 |
| 按时间筛选作业 | `filter_homeworks_by_time` | 查询 |
| 作业批阅入口链接 | `get_homework_review_link` | 查询 |
| 创建作业草稿 | `create_homework` | 写操作 |
| 试卷直绑创建并发布作业 | `create_homework_from_paper` | 写操作 |
| 发布作业 | `publish_homework` | 写操作 |
| 编辑作业 | `edit_homework` | 写操作 |
| 催交作业 | `urge_homework_students` | 写操作 |
| 打回学生作业 | `return_homework_submissions` | 写操作 |
| 审批作业重做申请 | `approve_homework_redo_requests` | 写操作 |
| 发布作业成绩 | `publish_homework_scores` | 写操作 |
| 回复作业讨论 | `reply_homework_discussion` | 写操作 |
| 保存作业模版 | `save_homework_template` | 写操作 |
| 使用模版创建作业 | `create_homework_from_template` | 写操作 |
| 高级导出作业数据 | `export_homework_data` | 写操作 |

作业的创建与发布是两步：`create_homework` 生成草稿后，用户确认再 `publish_homework`；`create_homework_from_paper` 与 `create_homework_from_template` 创建后直接发布，调用前必须确认。批阅与评语录入在页面完成。

### 考试管理

前置：先确认课程、学期和考试；涉及学生时再用 `query_exam_completion` 取得真实名单。

| 意图 | Tool | 类型 |
|---|---|---|
| 考试完成情况 | `query_exam_completion` | 查询 |
| 考试题库题目 | `search_exam_questions` | 查询 |
| 考试监考异常 | `query_exam_invigilation` | 查询 |
| 考试批阅智能体 | `query_exam_marking_agents` | 查询 |
| 补考学生 | `query_makeup_exam_students` | 查询 |
| 考试批阅入口链接 | `get_exam_review_link` | 查询 |
| 创建并发布考试 | `create_exam` | 写操作 |
| 试卷直绑创建并发布考试 | `create_exam_from_paper` | 写操作 |
| 编辑考试 | `edit_exam` | 写操作 |
| 发布考试成绩 | `publish_exam_scores` | 写操作 |
| 催交考试 | `urge_exam_submissions` | 写操作 |
| 全部打回考试 | `return_exam_submissions` | 写操作 |
| 公布试卷及答案 | `publish_exam_answers` | 写操作 |
| 创建补考草稿 | `prepare_makeup_exam` | 写操作 |
| 保存补考配置 | `finalize_makeup_exam` | 写操作 |
| 高级导出考试数据 | `export_exam_data` | 写操作 |

补考按「`prepare_makeup_exam` 创建草稿 → 查询并确认学生 → `finalize_makeup_exam` 保存配置」执行，草稿不会自动发布。批阅与评语录入在页面完成。

### 成绩与考勤

前置：成绩权重、成绩分布、线下成绩与考勤先确认课程、学期和班级。

| 意图 | Tool | 类型 |
|---|---|---|
| 多维成绩 | `query_grade_scores` | 查询 |
| 查询成绩班级学生 | `query_score_students` | 查询 |
| 总成绩分布 | `query_score_distribution` | 查询 |
| 成绩权重配置 | `query_score_setting` | 查询 |
| 成绩权重设置入口链接 | `query_score_setting_link` | 查询 |
| 预览成绩权重导入 | `preview_score_setting_import` | 查询 |
| 成绩导出任务 | `query_score_exports` | 查询 |
| 线下成绩活动 | `query_offline_score_activities` | 查询 |
| 线下成绩导入结果 | `query_offline_score_import` | 查询 |
| 线下考勤记录 | `query_attendance_records` | 查询 |
| 班级考勤名单 | `query_class_students` | 查询 |
| 生成成绩权重模板 | `generate_score_setting_template` | 写操作 |
| 保存成绩权重导入 | `save_score_setting_import` | 写操作 |
| 发起成绩导出 | `start_score_export` | 写操作 |
| 新增线下成绩 | `create_offline_score` | 写操作 |
| 修改线下成绩 | `update_offline_score` | 写操作 |
| 删除线下成绩 | `delete_offline_score` | 写操作 |
| 导入线下成绩 | `import_offline_scores` | 写操作 |
| 新增线下考勤 | `create_attendance` | 写操作 |
| 整体重录线下考勤 | `update_attendance` | 写操作 |
| 修改学生考勤状态 | `change_attendance_sign` | 写操作 |
| 删除整次线下考勤 | `delete_attendance` | 写操作 |

成绩权重的页面设置为推荐方式；Excel 导入按「`generate_score_setting_template` → 用户填写 → `preview_score_setting_import` → `save_score_setting_import`」执行。考勤写入前必须展示全班名单与默认出勤状态。

### 课堂报告与回放

| 意图 | Tool | 类型 |
|---|---|---|
| 查询课堂课次 | `search_classroom_lessons` | 查询 |
| 课堂核心数据 | `query_classroom_core_report` | 查询 |
| 课堂核心回顾 | `query_classroom_review` | 查询 |
| 随堂互动 | `query_classroom_interactions` | 查询 |
| 随堂测验详情 | `query_classroom_quiz_report` | 查询 |
| 课堂人员概况 | `query_classroom_people_report` | 查询 |
| 查询课堂回放 | `search_classroom_replays` | 查询 |
| 查询回放申请 | `query_replay_applications` | 查询 |
| 回放查看入口链接 | `get_replay_view_link` | 查询 |
| 发布课堂回放 | `publish_classroom_replays` | 写操作 |
| 同步课堂回放至资源库 | `sync_classroom_replays_to_library` | 写操作 |
| 重命名课堂回放 | `rename_classroom_replay` | 写操作 |
| 同意回放申请 | `approve_replay_applications` | 写操作 |
| 拒绝回放申请 | `reject_replay_applications` | 写操作 |

同步回放至资源库不会发布给学生；发布与申请审批都需要先展示课程、学期、回放或申请详情并确认，拒绝时必须提供给申请学生看的理由。

### 话题与通知

| 意图 | Tool | 类型 |
|---|---|---|
| 检索课程话题 | `search_topics` | 查询 |
| 分析课程讨论区 | `analyze_topics` | 查询 |
| 话题词云 | `query_topic_word_cloud` | 查询 |
| 话题管理入口链接 | `get_topic_manage_link` | 查询 |
| 查询通知 | `search_notices` | 查询 |
| 分析通知 | `analyze_notices` | 查询 |
| 通知阅读详情 | `query_notice_read_detail` | 查询 |
| 通知管理入口链接 | `get_notice_manage_link` | 查询 |

话题与通知的创建、编辑、删除在管理入口页面完成，本入口只提供检索、分析与入口链接。

### 分组方案与小组作业

前置：先确认课程、学期和分组方案。

| 意图 | Tool | 类型 |
|---|---|---|
| 分组方案列表 | `query_group_plans` | 查询 |
| 分组方案详情 | `query_group_plan_detail` | 查询 |
| 小组成员 | `query_group_members` | 查询 |
| 未进组学生 | `query_ungrouped_students` | 查询 |
| 小组作业 | `query_group_homeworks` | 查询 |
| 创建分组方案 | `create_group_plan` | 写操作 |
| 编辑分组方案 | `edit_group_plan` | 写操作 |
| 删除分组方案 | `delete_group_plan` | 写操作 |
| 加入或调整小组成员 | `assign_group_students` | 写操作 |
| 移出小组成员 | `remove_group_student` | 写操作 |
| 重命名小组 | `rename_plan_group` | 写操作 |
| 删除小组 | `delete_plan_group` | 写操作 |
| 设置小组组长 | `set_group_leader` | 写操作 |
| 创建小组作业草稿 | `create_group_homework` | 写操作 |
| 编辑小组作业 | `edit_group_homework` | 写操作 |
| 发布小组作业 | `publish_group_homework` | 写操作 |
| 删除小组作业 | `delete_group_homework` | 写操作 |

小组作业保存后必须另行确认是否发布；删除方案会连带删除小组与成员关系，删除小组不会删除作业。

### OBE

| 意图 | Tool | 类型 |
|---|---|---|
| 课程目标 / 毕业要求 | `query_obe_course_objectives` / `query_obe_graduation_requirements` | 查询 |
| 课程目标达成度 | `query_obe_objective_achievement` | 查询 |
| 学生 OBE 达成度 | `query_obe_student_achievement` | 查询 |
| 识别教学大纲 OBE 配置 | `analyze_obe_syllabus` | 查询 |
| OBE 配置管理入口链接 | `get_obe_management_link` | 查询 |
| 批量保存毕业要求 | `save_obe_requirements` | 写操作 |
| 批量保存课程目标 | `save_obe_objectives` | 写操作 |

保存课程目标时权重之和必须为 100；`analyze_obe_syllabus` 只返回预览，用户确认后才调用保存 Tool。已有目标、毕业要求的修改与关联在管理入口页面完成。

### 题目与题库

| 意图 | Tool | 类型 |
|---|---|---|
| 定位课程题库文件夹 | `locate_question_folder` | 查询 |
| 题库列表 | `list_question_banks` | 查询 |
| 题库知识点 / 标签 | `list_question_knowledge_points` / `list_question_labels` | 查询 |
| 筛选查询题目 | `search_questions` | 查询 |
| 查询相似题目 | `query_similar_questions` | 查询 |
| AI 出题选项 | `query_question_generation_options` | 查询 |
| 题库管理入口链接 | `get_question_manage_link` | 查询 |
| 创建单道题目 | `create_question` | 写操作 |
| 批量创建题目 | `create_questions_batch` | 写操作 |
| 删除已确认的相似题目 | `delete_similar_questions` | 写操作 |
| AI 生成题目并入库 | `generate_questions` | 写操作 |
| 识别文件中的题目 | `prepare_question_import` | 写操作 |
| 导入已确认的识别题目 | `import_recognized_questions` | 写操作 |
| 提交题目导出任务 | `export_questions` | 写操作 |

创建题目首次调用 `skipSimilarity=false`；返回相似待确认时先让用户确认，再改为 `true` 重试。`delete_similar_questions` 只删除最新查重结果中用户明确选择的题目，不支持无 ID 全选。文件导题按「`prepare_question_import` 识别 → 用户选题 → `import_recognized_questions` 导入」执行。

### 试卷

| 意图 | Tool | 类型 |
|---|---|---|
| 查询试卷库 | `list_paper_libraries` | 查询 |
| 查询试卷 | `search_papers` | 查询 |
| 可用组卷题型 | `list_available_paper_question_types` | 查询 |
| 组卷知识点 / 标签 | `list_paper_knowledge_points` / `list_paper_question_labels` | 查询 |
| 试卷查看 / 编辑入口链接 | `get_paper_view_link` / `get_paper_edit_link` | 查询 |
| 试卷库管理入口链接 | `get_paper_library_manage_link` | 查询 |
| 随机组卷 | `create_random_papers` | 写操作 |
| 创建选题试卷 | `create_select_paper` | 写操作 |
| 导出试卷 | `export_papers` | 写操作 |

随机组卷必须先确认完整规则，不静默修改题量、分值或筛选条件；选题组卷创建后由用户在页面逐题挑选。导出任务受理不等于文件已生成。

### 资源库

| 意图 | Tool | 类型 |
|---|---|---|
| 查询个人知识库 | `query_personal_knowledge_bases` | 查询 |
| 搜索个人知识库 | `search_knowledge_resources` | 查询 |
| 搜索资源库文件 | `search_resource_files` | 查询 |
| 定位资源库文件 | `locate_resource_file` | 查询 |
| 跨资源库查找文件 | `search_file_across_libraries` | 查询 |
| 解析资源所在资源库 | `resolve_resource_library` | 查询 |
| 资源库文件夹 / 回收站 | `query_library_folders` / `query_recycle_bin_files` | 查询 |
| 资源下载链接 | `query_resource_download_links` | 查询 |
| 个人 / 团队 / 课程资源库页面链接 | `query_person_library_link` / `query_team_library_link` / `query_course_library_link` | 查询 |
| 我的团队 / 团队资源库资源 | `query_team_list` / `query_team_library_files` | 查询 |
| 添加个人知识块 | `add_personal_knowledge_chunk` | 写操作 |
| 上传知识文件 | `upload_personal_knowledge_file` | 写操作 |
| 结构化知识库文件 | `structure_knowledge_base_files` | 写操作 |
| 上传文件到资源库 | `upload_resource_file` | 写操作 |
| 移动 / 复制资源库文件 | `move_resource_files` / `copy_resource_files` | 写操作 |
| 删除资源库文件到回收站 | `delete_resource_files` | 写操作 |
| 还原回收站文件 | `restore_recycle_bin_files` | 写操作 |
| 永久删除回收站文件 | `delete_recycle_bin_files` | 写操作 |

写入个人知识库前必须展示目标知识库、标题和写入内容；上传文件单文件不超过 50MB，HTTPS 附件先上传再结构化。移动与复制仅限同一课程资源库内；永久删除不可恢复，必须取得用户明确确认。

### 学习资源

前置：先确认课程、学期和资源所属章节。

| 意图 | Tool | 类型 |
|---|---|---|
| 学习资源章节树 | `query_study_resource_tree` | 查询 |
| 搜索学习资源 | `search_study_resources` | 查询 |
| 学习资源配置 | `query_study_resource_detail` | 查询 |
| 学习资源发布班级 | `list_study_resource_classes` | 查询 |
| 学习资源下载链接 | `get_study_resource_download` | 查询 |
| 学习资源详情 / 批量管理 / 分组创建 / 模式切换入口链接 | `get_study_resource_detail_link` / `get_study_resource_batch_manage_link` / `get_study_resource_group_create_link` / `get_study_resource_mode_switch_link` | 查询 |
| 添加学习资源文件 | `add_study_resource_files` | 写操作 |
| 添加学习资源链接 | `add_study_resource_link` | 写操作 |
| 发布学习资源 | `publish_study_resources` | 写操作 |

文件无 ID 但有 HTTPS 附件地址时先上传个人资源库，不能改成链接资源；链接意图只使用 `add_study_resource_link`。发布前会整批重新校验资源归属，并支持立即或逐班定时发布。

## 通用规则

- 管理入口链接类 Tool 只返回链接，不执行页面内操作；页面内的批量操作引导用户跳转完成。
- 模块间相互独立：某个模块无数据或失败时说明该模块不可用，继续其他已选择模块。
- 空结果如实说明「暂无数据」，不编造内容；检索类空结果提示可调整关键词或策略。
- 比例字段按百分数展示，超过两位小数四舍五入保留两位。
- 不向用户展示 Token、nid、route、内部 ID 或原始错误响应。
