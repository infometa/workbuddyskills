# gaia-wfm-openapi-attendance-cancelpunch-apply

处理当前登录用户的非 LA 撤销补卡申请、修改、撤回，并查询审批中的撤销补卡单和可选补卡记录。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人撤销补卡；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getCancelPunchApplyAccess、getCancelPunchApplyAvailableRecords、applyCancelPunchForm、modifyCancelPunchApply、cancelCancelPunchApply。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取撤销补卡权限 | `gaia YA ATD_FORM_APPLY getCancelPunchApplyAccess` | read | `gaia YA ATD_FORM_APPLY getCancelPunchApplyAccess --help` |
| 查询可撤销补卡记录 | `gaia YA ATD_FORM_APPLY getCancelPunchApplyAvailableRecords` | read | `gaia YA ATD_FORM_APPLY getCancelPunchApplyAvailableRecords --help` |
| 申请撤销补卡 | `gaia YA ATD_FORM_APPLY applyCancelPunchForm` | write | `gaia YA ATD_FORM_APPLY applyCancelPunchForm --help` |
| 修改撤销补卡 | `gaia YA ATD_FORM_APPLY modifyCancelPunchApply` | write | `gaia YA ATD_FORM_APPLY modifyCancelPunchApply --help` |
| 撤回撤销补卡 | `gaia YA ATD_FORM_APPLY cancelCancelPunchApply` | destructive | `gaia YA ATD_FORM_APPLY cancelCancelPunchApply --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
