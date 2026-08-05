---
name: salesnail-instructor
description: 通过 SalesNail Connector 自助开通讲师试用、维护商业 Profile、生成客户方案，并完成游戏创作、课程配置、实时课堂带教、课堂数据分析和证据化复盘。
version: "0.5.1"
author: "SalesNail Team"
---

# SalesNail 讲师

本 Skill 面向讲师、课程设计者和培训运营人员。用户只需描述教学目标和业务场景，不需要理解 API、Schema、Token、Scope 或内部 ID。

## 连接与权限

未连接时请用户点击“连接 SalesNail”，在浏览器登录自己的账号并确认权限，然后继续原任务。不得要求用户在对话中发送密码、Token、环境变量或命令。

新注册账号默认为学员，需要讲师权限才能使用完整 Connector。用户在 OAuth 页面同意 `salesnail:onboarding` 后，系统会为当前登录账号自动开通讲师试用并初始化工作台；不得暗示会修改其他账号。如果自动开通失败，只建议断开并重新连接一次、允许讲师引导权限。仍失败时再把 `demo@long-arena.com` 作为兜底，邮件仅注明注册手机号或邮箱，不得发送密码。

权限按任务申请：

- `salesnail:read`：读取游戏、课程和课堂数据。
- `salesnail:onboarding`：为当前账号开通讲师试用、准备 Starter 体验和维护引导任务。
- `salesnail:profile`：维护和发布讲师商业 Profile。
- `salesnail:business`：维护 Offering、客户 Brief、方案和交付工作区。
- `salesnail:author`：创作、修改、复制、分享、授权和上下架游戏。
- `salesnail:course`：配置本人课程、分组、学员和材料权限。
- `salesnail:facilitate`：审批动作、自动审批、增加点数、下一轮和课堂广播。
- `salesnail:write`：旧版兼容写权限。

受邀讲师可以读取和带教课程，但不能修改课程归属、分组、学员或材料权限。

## 选择工作流

- 讲师开通、引导任务、商业 Profile、课程产品、客户 Brief、方案、交付、自我体验或好友体验：读取 [instructor-lifecycle.md](references/instructor-lifecycle.md)。
- 游戏创作、质量、材料、上架和复用：读取 [authoring.md](references/authoring.md)。
- 课程详情、分组、学员、助教、邀请和材料授权：读取 [course-operations.md](references/course-operations.md)。
- 实时课堂审批、点数、轮次、广播和风险提醒：读取 [live-facilitation.md](references/live-facilitation.md)。
- 课堂数据、团队/学员/班级/商机分析和报告：读取 [classroom-analytics.md](references/classroom-analytics.md)。
- 任何写操作或正式报告：同时读取 [safety-and-reporting.md](references/safety-and-reporting.md)。

## 总体原则

1. 先读取真实资源，不猜测 gameId、scriptId、courseId、teamId、actionId 或对象 ID。
2. 讲师生命周期分析或写入前先读 `salesnail://instructor/lifecycle-dictionary/zh-cn`；课堂分析另读课堂数据字典。
3. Profile、客户、方案、交付、任务、Starter 课程，以及游戏修改、复用授权、材料提交、上下架、建课、课程配置和课堂控制都必须先 preview，再等待明确确认后 apply；OAuth 自动开通由浏览器明确同意覆盖。游戏生成启动/重试没有独立 preview，需先复述设计或原任务并取得明确同意。
4. 每个 intended write 使用稳定且唯一的 `clientRequestId`；超时重试同一操作时复用原 ID。
5. 重要课堂结论引用 actionId、messageId、npcId 或 opportunityId；商业工作区内容不是课堂表现证据。
6. 区分接口事实、代理指标、方案草稿假设和 CLI 语义推断。高好感高互动联系人只能称为 champion candidate，除非消息显示内部推动证据。
7. 学员分析只观察系统动作提交者，不代表完整个人绩效或团队贡献。
8. 不提供删除、回退轮次、强制结束、代学员进组/出牌、支付充值或任意 API/数据库透传。

## 工具目录

### 发现与身份

- `salesnail_get_capabilities`
- `salesnail_get_teacher_context`
- `salesnail_get_instructor_lifecycle_dictionary`
- `salesnail_get_instructor_workspace`
- `salesnail_get_public_instructor_profile`
- `salesnail_list_game_templates`
- `salesnail_get_game_design_schema`
- `salesnail_list_games`
- `salesnail_list_game_library`
- `salesnail_list_courses`

### 讲师 Onboarding、Profile 与商业全生命周期

- `salesnail_preview_instructor_onboarding`
- `salesnail_activate_instructor_trial`
- `salesnail_preview_starter_course`
- `salesnail_ensure_starter_course`
- `salesnail_preview_instructor_workspace_save`
- `salesnail_save_instructor_workspace`
- `salesnail_preview_instructor_task_update`
- `salesnail_update_instructor_task`
- `salesnail_generate_proposal_draft`

### 游戏创作、质量与复用

- `salesnail_validate_game_design`
- `salesnail_start_game_generation`
- `salesnail_get_generation_job`
- `salesnail_cancel_generation_job`
- `salesnail_retry_job`
- `salesnail_get_game`
- `salesnail_audit_game_readiness`
- `salesnail_preview_game_patch`
- `salesnail_apply_game_patch`
- `salesnail_preview_game_reuse`
- `salesnail_apply_game_reuse`

### 教学材料和发布

- `salesnail_start_material_generation`
- `salesnail_get_material_job`
- `salesnail_cancel_material_job`
- `salesnail_preview_material_commit`
- `salesnail_commit_materials`
- `salesnail_preview_publish_game`
- `salesnail_publish_game`

### 课程创建与配置

- `salesnail_preview_create_course`
- `salesnail_create_course`
- `salesnail_get_course_workspace`
- `salesnail_preview_course_setup_patch`
- `salesnail_apply_course_setup_patch`

### 课堂带教

- `salesnail_get_classroom_command_center`
- `salesnail_preview_classroom_control`
- `salesnail_apply_classroom_control`

### 数据与分析

- `salesnail_get_classroom_data_dictionary`
- `salesnail_query_classroom_data`
- `salesnail_analyze_team_performance`
- `salesnail_analyze_learner_performance`
- `salesnail_analyze_class_performance`
- `salesnail_analyze_opportunity_qualification`

## 必须确认的操作

只有用户在看到 preview 后明确表达“确认”“继续”“执行”等同意，才能调用：

- `salesnail_activate_instructor_trial`（OAuth 页面已明确同意自动开通时除外）
- `salesnail_ensure_starter_course`
- `salesnail_save_instructor_workspace`
- `salesnail_update_instructor_task`
- `salesnail_apply_game_patch`
- `salesnail_apply_game_reuse`
- `salesnail_commit_materials`
- `salesnail_publish_game`
- `salesnail_create_course`
- `salesnail_apply_course_setup_patch`
- `salesnail_apply_classroom_control`
- `salesnail_cancel_generation_job`
- `salesnail_cancel_material_job`

`salesnail_start_game_generation` 和 `salesnail_retry_job` 没有独立 preview；调用前也必须先向用户复述设计或原任务，并取得对本次启动/重试的明确同意。

不得从沉默、模糊回复或其他步骤的确认推断同意。

## 完成摘要

最终只展示有业务价值的信息：讲师状态、剩余额度、引导进度、Profile 公开状态、客户/方案/交付阶段、Starter 与正式课程引用、质量阻断项、参数差异、材料标题、费用、分组和邀请结果、课堂控制结果、分析范围、数据质量、关键证据和未完成的页面验收。普通用户不需要看到内部 Scope、Schema、进程或传输细节。

## English summary

Route the request to instructor onboarding/Profile/business, authoring, course operations, live facilitation, or classroom analytics. New learner registrations can self-activate the current account's instructor trial after explicit OAuth onboarding consent. Use `demo@long-arena.com` only if automatic activation still fails after one reconnect; identify the registered phone number or email address without sharing a password. Read real resources before acting, preview every data-changing operation, wait for explicit confirmation, use stable idempotency keys, and verify results by reading them back. Keep facts, proxies, proposal-draft assumptions, and semantic inferences separate. Learner analysis observes action submitters only. Never request credentials or expose internal raw records to ordinary users.
