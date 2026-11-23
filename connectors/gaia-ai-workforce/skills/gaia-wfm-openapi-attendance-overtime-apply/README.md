# gaia-wfm-openapi-attendance-overtime-apply

处理当前登录用户的非 LA 加班申请、修改和撤回，并提供权限、类型、原因、班单和结果查询。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人加班；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getOvertimeApplyAccess、getAvailableOvertimeType、getOvertimeApplyReason、getOvertimeRecordByDate、overtimeFormApply、overtimeApplyModify、overtimeApplyCancel。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查加班权限 | `gaia YA ATD_FORM_APPLY getOvertimeApplyAccess` | read | `gaia YA ATD_FORM_APPLY getOvertimeApplyAccess --help` |
| 查询可用加班类型 | `gaia YA ATD_FORM_APPLY getAvailableOvertimeType` | read | `gaia YA ATD_FORM_APPLY getAvailableOvertimeType --help` |
| 查询加班原因 | `gaia YA ATD_FORM_APPLY getOvertimeApplyReason` | read | `gaia YA ATD_FORM_APPLY getOvertimeApplyReason --help` |
| 查询指定日期班单和加班结果 | `gaia YA ATD_FORM_APPLY getOvertimeRecordByDate` | read | `gaia YA ATD_FORM_APPLY getOvertimeRecordByDate --help` |
| 申请加班 | `gaia YA ATD_FORM_APPLY overtimeFormApply` | write | `gaia YA ATD_FORM_APPLY overtimeFormApply --help` |
| 修改加班 | `gaia YA ATD_FORM_APPLY overtimeApplyModify` | write | `gaia YA ATD_FORM_APPLY overtimeApplyModify --help` |
| 撤回加班 | `gaia YA ATD_FORM_APPLY overtimeApplyCancel` | destructive | `gaia YA ATD_FORM_APPLY overtimeApplyCancel --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
