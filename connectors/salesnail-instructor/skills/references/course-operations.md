# 课程配置与授权
## 课程工作台

先调用 `salesnail_get_course_workspace`。它返回课程角色、分组、学员、组长、进组链接、口令、助教邀请链接、受邀讲师、材料权限和自动审批状态。

不要自己拼接链接，也不要通过猜测 ID 修改分组或学员。

## 配置操作

课程所有讲师可通过 `salesnail_preview_course_setup_patch` 预览：

- update_course：名称、时间、公司、描述、人数、组数和课程模式字段。
- add_group / edit_group。
- move_learner。
- set_leader。
- remove_invited_teacher。
- set_team_material_access。
- set_learner_material_access。

受邀讲师不能执行这些配置。分组删除不开放。邀请助教时向用户提供 workspace 返回的助教链接，由对方用自己的账号加入。

用户确认后调用 `salesnail_apply_course_setup_patch`，并以返回的最新 workspace 为准。
