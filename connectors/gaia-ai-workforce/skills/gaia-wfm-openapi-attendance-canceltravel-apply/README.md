# gaia-wfm-openapi-attendance-canceltravel-apply

处理当前登录用户的非 LA 销出差申请、修改、撤回，并按日期范围查询可销出的出差记录。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人销出差；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getCancelTravelApplyAccess、getTravelRecordForCancelTravel、applyCancelTravelForm、modifyCancelTravelApply、cancelCancelTravelApply。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取销出差权限 | `gaia YA ATD_FORM_APPLY getCancelTravelApplyAccess` | read | `gaia YA ATD_FORM_APPLY getCancelTravelApplyAccess --help` |
| 查询可销出的出差记录 | `gaia YA ATD_FORM_APPLY getTravelRecordForCancelTravel` | read | `gaia YA ATD_FORM_APPLY getTravelRecordForCancelTravel --help` |
| 申请销出差 | `gaia YA ATD_FORM_APPLY applyCancelTravelForm` | write | `gaia YA ATD_FORM_APPLY applyCancelTravelForm --help` |
| 修改销出差 | `gaia YA ATD_FORM_APPLY modifyCancelTravelApply` | write | `gaia YA ATD_FORM_APPLY modifyCancelTravelApply --help` |
| 撤回销出差 | `gaia YA ATD_FORM_APPLY cancelCancelTravelApply` | destructive | `gaia YA ATD_FORM_APPLY cancelCancelTravelApply --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
