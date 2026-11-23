# gaia-wfm-openapi-attendance-leave-apply

处理当前登录用户的非 LA 请假申请、修改和撤回，不用于查询请假单或审批他人。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人请假；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getLeaveApplyAccess、getLeaveApplyTypeAndMode、getLeaveApplyReason、leaveFormApply、leaveApplyModify、leaveApplyCancel。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查请假权限 | `gaia YA ATD_FORM_APPLY getLeaveApplyAccess` | read | `gaia YA ATD_FORM_APPLY getLeaveApplyAccess --help` |
| 查询请假类型和模式 | `gaia YA ATD_FORM_APPLY getLeaveApplyTypeAndMode` | read | `gaia YA ATD_FORM_APPLY getLeaveApplyTypeAndMode --help` |
| 查询请假原因 | `gaia YA ATD_FORM_APPLY getLeaveApplyReason` | read | `gaia YA ATD_FORM_APPLY getLeaveApplyReason --help` |
| 申请请假 | `gaia YA ATD_FORM_APPLY leaveFormApply` | write | `gaia YA ATD_FORM_APPLY leaveFormApply --help` |
| 修改请假 | `gaia YA ATD_FORM_APPLY leaveApplyModify` | write | `gaia YA ATD_FORM_APPLY leaveApplyModify --help` |
| 撤回请假 | `gaia YA ATD_FORM_APPLY leaveApplyCancel` | destructive | `gaia YA ATD_FORM_APPLY leaveApplyCancel --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
