# gaia-wfm-openapi-attendance-exception-apply

处理当前登录用户的非 LA 考勤异常申诉申请、修改、撤回，并查询可用异常类型与原因。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人异常申诉；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getExceptionAppealAccess、getExceptionAppealTypeAndReason、applyExceptionAppeal、modifyExceptionAppeal、cancelExceptionAppeal。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查异常申诉权限 | `gaia YA ATD_FORM_APPLY getExceptionAppealAccess` | read | `gaia YA ATD_FORM_APPLY getExceptionAppealAccess --help` |
| 查询异常类型和原因 | `gaia YA ATD_FORM_APPLY getExceptionAppealTypeAndReason` | read | `gaia YA ATD_FORM_APPLY getExceptionAppealTypeAndReason --help` |
| 申请异常申诉 | `gaia YA ATD_FORM_APPLY applyExceptionAppeal` | write | `gaia YA ATD_FORM_APPLY applyExceptionAppeal --help` |
| 修改异常申诉 | `gaia YA ATD_FORM_APPLY modifyExceptionAppeal` | write | `gaia YA ATD_FORM_APPLY modifyExceptionAppeal --help` |
| 撤回异常申诉 | `gaia YA ATD_FORM_APPLY cancelExceptionAppeal` | destructive | `gaia YA ATD_FORM_APPLY cancelExceptionAppeal --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
