# gaia-wfm-openapi-attendance-cancelleave-apply

处理当前登录用户的非 LA 销假申请、修改、撤回，并按日期范围查询可销假的请假记录。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人销假；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getCancelLeaveAccess、getLeaveRecordForCancelLeave、applyCancelLeaveForm、modifyCancelLeaveApply、cancelCancelLeaveApply。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取销假权限 | `gaia YA ATD_FORM_APPLY getCancelLeaveAccess` | read | `gaia YA ATD_FORM_APPLY getCancelLeaveAccess --help` |
| 查询可销假的请假记录 | `gaia YA ATD_FORM_APPLY getLeaveRecordForCancelLeave` | read | `gaia YA ATD_FORM_APPLY getLeaveRecordForCancelLeave --help` |
| 申请销假 | `gaia YA ATD_FORM_APPLY applyCancelLeaveForm` | write | `gaia YA ATD_FORM_APPLY applyCancelLeaveForm --help` |
| 修改销假 | `gaia YA ATD_FORM_APPLY modifyCancelLeaveApply` | write | `gaia YA ATD_FORM_APPLY modifyCancelLeaveApply --help` |
| 撤回销假 | `gaia YA ATD_FORM_APPLY cancelCancelLeaveApply` | destructive | `gaia YA ATD_FORM_APPLY cancelCancelLeaveApply --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
